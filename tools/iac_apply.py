"""iac_apply.py — IaC live-apply (Tier 2) PREVIEW/APPROVE/PLAN-CAPTURE engine.

THE HIGHEST-STAKES MODULE IN THE PROJECT. A live cloud apply destroys real,
non-git-reversible infrastructure. This module builds + unit-tests the **pure
preview/approve/capture machinery** and **STOPS at the creds wall**: the actual
cloud EXECUTION (``terraform apply`` / ``aws cloudformation execute-change-set``)
is the DEFERRED, n=0-live seam (``run_apply`` → ``NotImplementedError``).

Security posture (the defining safety property)
-----------------------------------------------
PURE — this module spawns **no** cloud-mutating process. It never imports the
subprocess module, and contains no ``eval``/``exec`` and never enables the
shell-true subprocess mode (the builders describe ``shell=False`` only). It
consumes a **provided** plan / change-set artifact (exactly as Tier-1
``iac_detect.scan_tf_plan`` operates on a provided ``plan_json``) plus the
approval / grant artifacts as plain bytes/dicts, and returns argv ``list[str]``s,
hashes, verdict dicts, and schema dicts. Assertable by source scan (see
``test_iac_apply.py::TestExecSafety``, mirroring ``drift_gate.TestExecSafety``).

The four argv builders are pure functions returning a ``list[str]`` where
``argv[0]`` is the program and the plan/stack/change-set identifier is a
positional/flag-valued DATA element — never the program, never shell-interpolated.
``shell=False`` is the only mode they describe; they never emit a shell string.
Every operator-supplied value that enters an argv is ``fullmatch``-anchored
against an explicit grammar and ``..``-guarded (CWE-23) BEFORE it enters the
list; a leading ``-`` is rejected (flag injection); ``--`` end-of-options is
inserted before positional data. The builders NEVER emit ``-auto-approve`` and
have NO ``-target`` parameter (FORBIDDEN in v1 — bypasses lifecycle guards).

Public surfaces (cite-able by name per protocol/reuse-claims.md)
----------------------------------------------------------------
build_tf_plan_argv               — pure structured argv: terraform plan
build_tf_apply_argv              — pure structured argv: terraform apply (saved plan)
build_cfn_create_changeset_argv  — pure structured argv: aws cfn create-change-set
build_cfn_execute_changeset_argv — pure structured argv: aws cfn execute-change-set
plan_hash                        — SHA-256 of the exact apply-consumed bytes
canonical_cfn_plan_bytes         — deterministic bytes of a FULL describe-change-set
load_approval                    — read the committable approval artifact (None if absent)
approval_verdict                 — APPROVED iff approvedPlanHash == computed_plan_hash
capability_gate_verdict          — the self-binding typed stateful-destroy gate
apply_state                      — the apply state-machine resolver
iac_apply_schema                 — single source of truth for .kata/iac-apply.json
build_iac_apply_artifact         — build the sibling runtime artifact
emit_iac_apply / load_iac_apply  — write/read the sibling runtime artifact
build_capability_grant           — typed grant shape {hash, addresses, token}
build_approval_artifact          — committable approval artifact shape
build_apply_audit_record         — one append-only audit row (actor/time/rationale)
run_apply                        — THE DEFERRED EXECUTION SEAM (raises NotImplementedError)

Reuse (verify-before-reuse, cited surfaces)
-------------------------------------------
- iac_detect.scan_tf_plan / scan_cfn_changeset (+ the ``stateful`` boolean) — the
  stateful classification the capability-gate keys off.
- kata_preflight H2 inline ``hashlib.sha256(...)`` + ``_load_approved_hash`` +
  ``_DEFAULT_FREEZE_APPROVAL_FILENAME`` pattern + ``_validate_field_value`` /
  ``_validate_package`` / ``_safe_abs`` (the argv validators + CWE-23 guard).
- drift_gate.structural_drift_verdict (the NotImplementedError seam shape) +
  drift_gate.drift_schema (schema-as-source-of-truth).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Schema / artifact constants
# ---------------------------------------------------------------------------

_SCHEMA_VERSION = 1

#: Sibling RUNTIME artifact (machine-written; gitignored under .kata/).
_DEFAULT_IAC_APPLY_ARTIFACT_RELPATH = ".kata/iac-apply.json"

#: Committable APPROVAL artifact (human-authored; repo root, separate from the
#: runtime artifact — tamper-resistance, mirrors kata_preflight's
#: kata.freeze-approval.json / _DEFAULT_FREEZE_APPROVAL_FILENAME H2 pattern).
_DEFAULT_IAC_APPLY_APPROVAL_FILENAME = "kata.iac-apply-approval.json"

# ---------------------------------------------------------------------------
# approval_verdict sub-states
# ---------------------------------------------------------------------------

_APPROVED = "APPROVED"

# ---------------------------------------------------------------------------
# capability_gate_verdict states
# ---------------------------------------------------------------------------

_CAP_NOT_REQUIRED = "NOT_REQUIRED"
_CAP_REQUIRED = "CAPABILITY_REQUIRED"
_CAP_CLEARED = "CAPABILITY_CLEARED"

# Sentinel for a stateful entry whose address/logicalId is empty — can never be
# a member of an operator-authored authorized set, so containment fails closed.
_UNKNOWN_ADDR = "<unknown-stateful-address>"

# ---------------------------------------------------------------------------
# apply_state terminal vocabulary (judgment call #4 — LOCKED)
# ---------------------------------------------------------------------------

_PENDING_PLAN = "PENDING_PLAN"
_PLAN_CAPTURED = "PLAN_CAPTURED"
_APPROVAL_INVALIDATED = "APPROVAL_INVALIDATED"
_CAPABILITY_REQUIRED = "CAPABILITY_REQUIRED"
_DRIFT_ABORT = "DRIFT_ABORT"
_CREDS_ABSENT = "CREDS_ABSENT"
_READY_DEFERRED = "READY_DEFERRED"
_BLOCKED = "BLOCKED"

_APPLY_STATES = (
    _PENDING_PLAN,
    _PLAN_CAPTURED,
    _APPROVAL_INVALIDATED,
    _CAPABILITY_REQUIRED,
    _DRIFT_ABORT,
    _CREDS_ABSENT,
    _READY_DEFERRED,
    _BLOCKED,
)

# ---------------------------------------------------------------------------
# Identifier grammars (anti-injection — mirror kata_preflight validators)
# ---------------------------------------------------------------------------

# Path-like identifier (plan-file path, var-file path, template path, chdir):
# forward-slash segments of safe chars only. Forbids ``:`` (no drive/scheme),
# whitespace, ``;``, ``|``. ``..`` and a leading ``-`` are rejected separately.
_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")

# CloudFormation stack-name / change-set-name grammar: must start with a letter,
# alphanumeric + hyphen, up to 128 chars. STRICTER than the ARN grammar — it
# forbids ``:`` and ``/``, so a change-set ARN is REJECTED here (distinct grammars).
_CFN_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]{0,127}$")

# DEDICATED change-set ARN grammar (permits ``:`` and ``/`` that the other
# grammars forbid). Distinct from + stricter than the stack-name grammar.
_CFN_CHANGESET_ARN_RE = re.compile(
    r"^arn:aws:cloudformation:[a-z0-9-]+:\d{12}:changeSet/"
    r"[A-Za-z0-9][A-Za-z0-9-]{0,127}/[0-9a-f-]{36}$"
)

_CFN_CHANGE_SET_TYPES = frozenset({"UPDATE", "CREATE"})


def _safe_abs(raw: str | Path) -> Path:
    """Reject ``..`` traversal (CWE-23) then resolve to an absolute path.

    Mirrors ``kata_preflight._safe_abs`` / ``iac_detect._safe_abs``.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"iac_apply: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


def _reject_dangerous(value: object, field_name: str) -> str:
    """Universal anti-injection rejects, shared by every identifier grammar.

    Rejects: non-string / empty, leading ``-`` (flag injection), ``..`` (CWE-23),
    ``://`` (URL/scheme), whitespace, ``;`` and ``|`` (shell metacharacters).
    Mirrors ``kata_preflight._validate_package`` universal checks.
    """
    if not isinstance(value, str) or not value:
        raise ValueError(f"Field {field_name!r} must be a non-empty string: {value!r}")
    if value.startswith("-"):
        raise ValueError(
            f"Field {field_name!r} starts with '-' (flag injection risk): {value!r}"
        )
    if ".." in value:
        raise ValueError(
            f"Field {field_name!r} contains '..' (path traversal rejected): {value!r}"
        )
    if "://" in value:
        raise ValueError(
            f"Field {field_name!r} contains '://' (URL/scheme rejected): {value!r}"
        )
    if any(ch.isspace() for ch in value):
        raise ValueError(
            f"Field {field_name!r} contains whitespace (rejected): {value!r}"
        )
    for bad in (";", "|"):
        if bad in value:
            raise ValueError(
                f"Field {field_name!r} contains {bad!r} (shell metacharacter rejected): {value!r}"
            )
    return value


def _validate_path(value: object, field_name: str) -> str:
    """Validate a path-like argv identifier (fullmatch grammar + ``..``-guard)."""
    v = _reject_dangerous(value, field_name)
    if not _PATH_RE.fullmatch(v):
        raise ValueError(
            f"Field {field_name!r} fails path grammar {_PATH_RE.pattern!r}: {v!r}"
        )
    return v


def _validate_cfn_name(value: object, field_name: str) -> str:
    """Validate a CFN stack-name / change-set-name (rejects an ARN by design)."""
    v = _reject_dangerous(value, field_name)
    if not _CFN_NAME_RE.fullmatch(v):
        raise ValueError(
            f"Field {field_name!r} fails CFN name grammar {_CFN_NAME_RE.pattern!r}: {v!r}"
        )
    return v


def _validate_change_set_id(value: object) -> str:
    """Validate the immutable change-set ARN against its DEDICATED grammar."""
    v = _reject_dangerous(value, "change_set_id")
    if not _CFN_CHANGESET_ARN_RE.fullmatch(v):
        raise ValueError(
            "Field 'change_set_id' is not a well-formed CloudFormation change-set "
            f"ARN ({_CFN_CHANGESET_ARN_RE.pattern!r}): {v!r}"
        )
    return v


# ---------------------------------------------------------------------------
# Argv builders — pure, shell=False, structured DATA, no -target/-auto-approve
# ---------------------------------------------------------------------------

def build_tf_plan_argv(
    *,
    chdir: str | None = None,
    out_path: str,
    var_files: Sequence[str] = (),
) -> list[str]:
    """Build the ``terraform plan`` argv (pure; ``shell=False`` semantics).

    Produces e.g.::

        ["terraform", "-chdir", <dir>, "plan", "-input=false", "-lock=true",
         "-out", <out_path>, "-var-file", <vf>, ...]

    ``out_path`` / ``var_files`` / ``chdir`` are grammar-validated + ``..``-guarded.
    There is NO ``-target`` parameter (FORBIDDEN in v1). The plan/var-file
    identifiers are flag-VALUES, never the program, never shell-interpolated.

    Raises:
        ValueError: if any identifier fails validation.
    """
    argv: list[str] = ["terraform"]
    if chdir is not None:
        _validate_path(chdir, "chdir")
        argv += ["-chdir", chdir]
    argv += ["plan", "-input=false", "-lock=true"]
    _validate_path(out_path, "out_path")
    argv += ["-out", out_path]
    for vf in var_files:
        _validate_path(vf, "var_file")
        argv += ["-var-file", vf]
    return argv


def build_tf_apply_argv(*, chdir: str | None = None, plan_file: str) -> list[str]:
    """Build the ``terraform apply`` argv applying the EXACT saved plan file.

    Produces e.g.::

        ["terraform", "-chdir", <dir>, "apply", "-input=false", "-lock=true",
         "--", <plan_file>]

    The approved saved plan file IS the authorization (the Atlantis discipline):
    NEVER ``-auto-approve``, never a freeform target. ``--`` end-of-options is
    inserted before the positional ``plan_file`` DATA element. ``plan_file`` /
    ``chdir`` are grammar-validated + ``..``-guarded.

    Raises:
        ValueError: if any identifier fails validation.
    """
    argv: list[str] = ["terraform"]
    if chdir is not None:
        _validate_path(chdir, "chdir")
        argv += ["-chdir", chdir]
    _validate_path(plan_file, "plan_file")
    argv += ["apply", "-input=false", "-lock=true", "--", plan_file]
    return argv


def build_cfn_create_changeset_argv(
    *,
    stack_name: str,
    change_set_name: str,
    template_path: str,
    change_set_type: str = "UPDATE",
) -> list[str]:
    """Build the ``aws cloudformation create-change-set`` argv (pure).

    Produces e.g.::

        ["aws", "cloudformation", "create-change-set",
         "--stack-name", <name>, "--change-set-name", <name>,
         "--template-body", "file://"+<path>, "--change-set-type", <UPDATE|CREATE>]

    All identifiers are grammar-validated; ``template_path`` is ``..``-guarded and
    then prefixed with ``file://`` (the path itself contains no ``://``).

    Raises:
        ValueError: if any identifier fails validation, or ``change_set_type`` is
                    not one of ``UPDATE`` / ``CREATE``.
    """
    _validate_cfn_name(stack_name, "stack_name")
    _validate_cfn_name(change_set_name, "change_set_name")
    _validate_path(template_path, "template_path")
    if change_set_type not in _CFN_CHANGE_SET_TYPES:
        raise ValueError(
            f"change_set_type {change_set_type!r} not in {sorted(_CFN_CHANGE_SET_TYPES)!r}"
        )
    return [
        "aws", "cloudformation", "create-change-set",
        "--stack-name", stack_name,
        "--change-set-name", change_set_name,
        "--template-body", "file://" + template_path,
        "--change-set-type", change_set_type,
    ]


def build_cfn_execute_changeset_argv(*, stack_name: str, change_set_id: str) -> list[str]:
    """Build the ``aws cloudformation execute-change-set`` argv (pure).

    Produces::

        ["aws", "cloudformation", "execute-change-set",
         "--stack-name", <name>, "--change-set-name", <change_set_id>]

    The immutable ``change_set_id`` (ARN) is the binding subject for CFN and is
    validated against its OWN dedicated ARN grammar (permits ``:``/``/``).
    ``stack_name`` is validated against the stricter stack-name grammar.

    Raises:
        ValueError: if ``stack_name`` or ``change_set_id`` fails validation.
    """
    _validate_cfn_name(stack_name, "stack_name")
    _validate_change_set_id(change_set_id)
    return [
        "aws", "cloudformation", "execute-change-set",
        "--stack-name", stack_name,
        "--change-set-name", change_set_id,
    ]


# ---------------------------------------------------------------------------
# Plan hash (H2 — bind approval to the SHA-256 of the exact apply-consumed bytes)
# ---------------------------------------------------------------------------

def plan_hash(plan_bytes: bytes) -> str:
    """SHA-256 (hex) of the exact bytes that will be consumed at apply.

    Mirrors the inline ``hashlib.sha256(manifest_bytes)`` H2 block in
    ``kata_preflight.run_preflight``.

    Binding-input asymmetry (judgment call #1 — LOCKED):
      - **Terraform**: pass the binary ``tfplan`` file bytes (the exact bytes
        ``terraform apply`` consumes).
      - **CloudFormation**: pass the bytes of the FULL ``describe-change-set``
        response (use ``canonical_cfn_plan_bytes``) — the full response embeds
        ``ChangeSetId`` / ``StackId`` / ``StackName``, so the ARN + target stack
        fall WITHIN the hashed bytes and an approval cannot be replayed against a
        different change-set or a different stack.

    Raises:
        TypeError: if ``plan_bytes`` is not bytes-like.
    """
    if not isinstance(plan_bytes, (bytes, bytearray)):
        raise TypeError(
            f"plan_hash requires bytes-like apply-consumed input, got {type(plan_bytes).__name__!r}"
        )
    return hashlib.sha256(bytes(plan_bytes)).hexdigest()


def canonical_cfn_plan_bytes(describe_change_set: dict) -> bytes:
    """Deterministic bytes of a FULL ``describe-change-set`` response for hashing.

    Serializes the WHOLE response (NOT just the ``Changes`` array) with sorted
    keys so the hash is stable and ``ChangeSetId`` / ``StackId`` / ``StackName``
    are inside the hashed bytes (replay-resistance — judgment call #1).

    Raises:
        TypeError: if ``describe_change_set`` is not a dict.
    """
    if not isinstance(describe_change_set, dict):
        raise TypeError(
            f"canonical_cfn_plan_bytes requires the full describe-change-set dict, "
            f"got {type(describe_change_set).__name__!r}"
        )
    return json.dumps(describe_change_set, sort_keys=True, separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------------------
# Approval artifact load + approval_verdict (H2 mismatch -> never collapse to pass)
# ---------------------------------------------------------------------------

def load_approval(path: str | Path) -> dict | None:
    """Read the committable approval artifact; ``None`` if absent/malformed.

    Mirrors ``kata_preflight._load_approved_hash`` (the freeze artifact lives at
    a distinct, committable path — not co-located with the runtime artifact).
    """
    p = _safe_abs(path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def approval_verdict(*, computed_plan_hash: str, approval: dict | None) -> dict:
    """Plan-approval verdict — ``APPROVED`` iff approvedPlanHash == computed_plan_hash.

    Returns ``{"state", "reason"}``:
      - ``PENDING_PLAN``         — no approval artifact present (awaiting approval).
      - ``BLOCKED``              — approval/hash malformed (fail-closed).
      - ``APPROVED``             — approvedPlanHash == the freshly-computed hash.
      - ``APPROVAL_INVALIDATED`` — mismatch (re-plan / plan change invalidated it).

    NEVER collapses a mismatch to a pass (mirrors kata_preflight H2
    mismatch -> blocked). Mutation target (a): the equality on ``matched`` below.
    """
    if not isinstance(approval, dict) or not approval:
        return {"state": _PENDING_PLAN, "reason": "no approval artifact present"}
    approved = approval.get("approvedPlanHash")
    if not isinstance(approved, str) or not approved:
        return {"state": _BLOCKED, "reason": "approval is missing a valid 'approvedPlanHash'"}
    if not isinstance(computed_plan_hash, str) or not computed_plan_hash:
        return {"state": _BLOCKED, "reason": "no computed plan hash to bind the approval to"}
    matched = approved == computed_plan_hash
    if matched:
        return {"state": _APPROVED, "reason": "approvedPlanHash matches the computed plan hash"}
    return {
        "state": _APPROVAL_INVALIDATED,
        "reason": "approvedPlanHash != computed plan hash — re-plan invalidated the approval",
    }


# ---------------------------------------------------------------------------
# Capability gate — the self-binding typed stateful-destroy gate
# ---------------------------------------------------------------------------

def _stateful_destroy_addresses(destructive: Iterable[dict] | None) -> set[str]:
    """Collect the stateful destroy/replace address set from iac_detect scans.

    Keys off the ``stateful: True`` entries emitted by
    ``iac_detect.scan_tf_plan`` (``address``) / ``scan_cfn_changeset``
    (``logicalId``). An empty/absent address on a stateful entry maps to a
    sentinel that can never be authorized (fail-closed).

    Mutation target (e): the ``stateful: True`` filter feed (the ``addrs.add``).

    Raises:
        ValueError: if any entry is not a dict (fail-closed, mirrors iac_detect).
    """
    addrs: set[str] = set()
    for entry in destructive or []:
        if not isinstance(entry, dict):
            raise ValueError(
                f"capability gate: destructive entry must be a dict, got {type(entry).__name__!r}"
            )
        if entry.get("stateful") is True:
            addr = entry.get("address") or entry.get("logicalId") or _UNKNOWN_ADDR
            addrs.add(addr)
    return addrs


def capability_gate_verdict(
    *,
    computed_plan_hash: str,
    destructive: list[dict],
    grant: dict | None,
) -> dict:
    """The typed, self-binding stateful-destroy capability-gate.

    Distinct from plan approval. A destroy/replace on an ``iac_detect``-stateful
    resource clears ONLY when ALL THREE hold:
      (i)   ``grant["approvedPlanHash"] == computed_plan_hash`` — SELF-BINDING; a
            grant bound to a DIFFERENT (stale/prior) plan never authorizes.
      (ii)  ``grant["authorizedStatefulAddresses"]`` ⊇ the stateful-destroy set.
      (iii) a typed ``grant["confirmedToken"]`` is present.
    ``grant=None`` / empty set / missing token / mismatched hash → fail-closed
    ``CAPABILITY_REQUIRED``. A plan approval ALONE never authorizes a stateful
    destroy.

    Returns ``{"state", "reason", "statefulAddresses", "missing"}`` where
    ``state`` is ``NOT_REQUIRED`` / ``CAPABILITY_REQUIRED`` / ``CAPABILITY_CLEARED``.

    Mutation targets: (b) the ``authorizedStatefulAddresses`` containment;
    (c) the self-binding ``approvedPlanHash`` equality.
    """
    stateful = _stateful_destroy_addresses(destructive)
    addrs = sorted(stateful)
    if not stateful:
        return {
            "state": _CAP_NOT_REQUIRED,
            "reason": "no stateful destroy/replace in the plan — typed grant not required",
            "statefulAddresses": [],
            "missing": [],
        }

    g = grant if isinstance(grant, dict) else {}
    missing: list[str] = []
    reasons: list[str] = []

    # (i) SELF-BINDING hash equality — a stale/replayed grant must NOT authorize.
    if not (isinstance(computed_plan_hash, str) and computed_plan_hash
            and g.get("approvedPlanHash") == computed_plan_hash):
        missing.append("approvedPlanHash")
        reasons.append("grant.approvedPlanHash != computed_plan_hash (self-binding: stale/replayed grant rejected)")

    # (ii) containment — EVERY stateful destroy address must be authorized.
    authorized = g.get("authorizedStatefulAddresses")
    authorized_set = set(authorized) if isinstance(authorized, list) else set()
    if not (stateful <= authorized_set):
        missing.append("authorizedStatefulAddresses")
        reasons.append("authorizedStatefulAddresses does not cover the full stateful-destroy set")

    # (iii) typed confirmation token distinct from a bare plan approval.
    if not g.get("confirmedToken"):
        missing.append("confirmedToken")
        reasons.append("confirmedToken is absent")

    if missing:
        return {
            "state": _CAP_REQUIRED,
            "reason": "; ".join(reasons),
            "statefulAddresses": addrs,
            "missing": missing,
        }
    return {
        "state": _CAP_CLEARED,
        "reason": "all three capability conditions satisfied (self-binding hash, containment, token)",
        "statefulAddresses": addrs,
        "missing": [],
    }


# ---------------------------------------------------------------------------
# apply_state — the state-machine resolver
# ---------------------------------------------------------------------------

def apply_state(
    *,
    computed_plan_hash: str,
    approval: dict | None,
    destructive: list[dict],
    grant: dict | None,
    drift_detected: bool,
    creds_present: bool,
) -> str:
    """Compose the apply state-machine over approval + capability + drift + creds.

    Returns one of the terminal vocabulary (judgment call #4):
    ``PENDING_PLAN`` · ``PLAN_CAPTURED`` · ``APPROVAL_INVALIDATED`` ·
    ``CAPABILITY_REQUIRED`` · ``DRIFT_ABORT`` · ``CREDS_ABSENT`` ·
    ``READY_DEFERRED`` · ``BLOCKED``.

    Precedence (fail-closed safety first):
      1. ``drift_detected`` → ``DRIFT_ABORT`` (real infra != state; never proceed,
         regardless of approval/grant). Mutation target (d).
      2. no computed plan hash → ``PENDING_PLAN``.
      3. approval sub-verdict: absent → ``PLAN_CAPTURED``; malformed → ``BLOCKED``;
         mismatch → ``APPROVAL_INVALIDATED``.
      4. approved + stateful destroy without a cleared grant → ``CAPABILITY_REQUIRED``.
      5. approved + capability cleared but no creds → ``CREDS_ABSENT`` (honest park).
      6. all gates pass → ``READY_DEFERRED`` — the terminal success state hands to
         the DEFERRED ``run_apply`` seam; it does NOT execute an apply.
    """
    if drift_detected:
        return _DRIFT_ABORT
    if not isinstance(computed_plan_hash, str) or not computed_plan_hash:
        return _PENDING_PLAN

    av = approval_verdict(computed_plan_hash=computed_plan_hash, approval=approval)
    if av["state"] == _PENDING_PLAN:
        return _PLAN_CAPTURED
    if av["state"] == _BLOCKED:
        return _BLOCKED
    if av["state"] == _APPROVAL_INVALIDATED:
        return _APPROVAL_INVALIDATED

    # approval is APPROVED — now the typed capability-gate over the destructive set.
    cg = capability_gate_verdict(
        computed_plan_hash=computed_plan_hash, destructive=destructive, grant=grant
    )
    if cg["state"] == _CAP_REQUIRED:
        return _CAPABILITY_REQUIRED

    if not creds_present:
        return _CREDS_ABSENT
    return _READY_DEFERRED


# ---------------------------------------------------------------------------
# Sibling runtime artifact (.kata/iac-apply.json) — schema + build + emit/load
# ---------------------------------------------------------------------------

def iac_apply_schema() -> dict:
    """JSON schema (single source of truth) for the sibling ``.kata/iac-apply.json``.

    The sibling runtime artifact is DISTINCT from Tier-1's ``.kata/iac.json`` (it
    is NOT an extension — extending iac.json would perturb the D111 fail-closed
    re-classification). Mirrors ``drift_gate.drift_schema``.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "IacApplyArtifact",
        "description": (
            "Tier-2 IaC apply-lifecycle runtime artifact (.kata/iac-apply.json): "
            "captured plan ref + plan hash + apply state + append-only audit. "
            "Creds-gated lifecycle; the apply EXECUTION is the DEFERRED run_apply seam."
        ),
        "type": "object",
        "required": [
            "schemaVersion", "kind", "capturedPlanRef", "planHash",
            "state", "destructive", "audit", "generatedAt",
        ],
        "properties": {
            "schemaVersion": {"type": "integer"},
            "kind": {
                "type": "string",
                "enum": ["terraform", "cloudformation"],
                "description": "The IaC kind this apply lifecycle covers.",
            },
            "capturedPlanRef": {
                "type": "string",
                "description": "Reference to the captured plan/change-set (path or ARN).",
            },
            "planHash": {
                "type": "string",
                "description": "SHA-256 of the exact apply-consumed bytes (plan_hash).",
            },
            "state": {
                "type": "string",
                "enum": list(_APPLY_STATES),
                "description": "Terminal apply-state-machine state (apply_state).",
            },
            "destructive": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Destructive resource changes (iac_detect scan entries).",
            },
            "audit": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Append-only apply-audit records (build_apply_audit_record).",
            },
            "generatedAt": {
                "type": "string",
                "description": "ISO-8601 UTC timestamp when the artifact was written.",
            },
        },
        "additionalProperties": False,
    }


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def build_iac_apply_artifact(
    *,
    kind: str,
    captured_plan_ref: str,
    plan_hash: str,
    state: str,
    destructive: Sequence[dict] = (),
    audit: Sequence[dict] = (),
) -> dict:
    """Build the sibling runtime artifact dict conforming to ``iac_apply_schema``."""
    return {
        "schemaVersion": _SCHEMA_VERSION,
        "kind": kind,
        "capturedPlanRef": captured_plan_ref,
        "planHash": plan_hash,
        "state": state,
        "destructive": list(destructive),
        "audit": list(audit),
        "generatedAt": _now_iso(),
    }


def emit_iac_apply(artifact: dict, path: str | Path) -> None:
    """Write the sibling runtime artifact as JSON (creates parent dirs)."""
    dest = _safe_abs(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(artifact, indent=2), encoding="utf-8")


def load_iac_apply(path: str | Path) -> dict | None:
    """Read the sibling runtime artifact; ``None`` if absent/malformed."""
    p = _safe_abs(path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


# ---------------------------------------------------------------------------
# Committable approval / grant artifact shapes (mirror kata.freeze-approval.json)
# ---------------------------------------------------------------------------

def build_capability_grant(
    *,
    approved_plan_hash: str,
    authorized_stateful_addresses: Sequence[str],
    confirmed_token: str,
) -> dict:
    """Build the typed stateful-destroy grant shape (judgment call #3).

    ``{approvedPlanHash, authorizedStatefulAddresses:[...], confirmedToken}`` — the
    grant carries its OWN ``approvedPlanHash`` so ``capability_gate_verdict`` is
    self-binding (it re-checks the hash itself, not trusting artifact co-location).
    """
    return {
        "approvedPlanHash": approved_plan_hash,
        "authorizedStatefulAddresses": list(authorized_stateful_addresses),
        "confirmedToken": confirmed_token,
    }


def build_approval_artifact(*, approved_plan_hash: str, grant: dict | None = None) -> dict:
    """Build the committable approval artifact (``kata.iac-apply-approval.json``).

    Human-authored: the approved plan hash plus the optional typed
    stateful-destroy grant. Lives at a distinct committable path from the
    machine-written runtime artifact (tamper-resistance, mirrors kata_preflight H2).
    """
    artifact: dict = {
        "schemaVersion": _SCHEMA_VERSION,
        "approvedPlanHash": approved_plan_hash,
    }
    if grant is not None:
        artifact["grant"] = grant
    return artifact


# ---------------------------------------------------------------------------
# Append-only apply-audit record (actor/time/rationale — SOC2/ISO substrate)
# ---------------------------------------------------------------------------

def build_apply_audit_record(
    *,
    task_id: str,
    kind: str,
    plan_hash: str,
    state: str,
    actor: str,
    ts: str,
    rationale: str,
) -> dict:
    """Build one append-only apply-audit row.

    Append-only-shaped (actor/time/rationale) — reuses the escalation/board
    audit substrate; the orchestrator appends these rows, never mutates them.
    """
    return {
        "taskId": task_id,
        "kind": kind,
        "planHash": plan_hash,
        "state": state,
        "actor": actor,
        "ts": ts,
        "rationale": rationale,
    }


# ---------------------------------------------------------------------------
# THE DEFERRED EXECUTION SEAM — the creds wall (mirrors structural_drift_verdict)
# ---------------------------------------------------------------------------

_RUN_APPLY_MSG = (
    "iac_apply.run_apply is the DEFERRED cloud-execution seam and is NOT "
    "implemented (n=0-live, creds-gated). Live execution (terraform apply / "
    "aws cloudformation execute-change-set) requires authenticated cloud access "
    "AND a present+matching approval artifact AND a present capability grant — "
    "and even then this seam never mutates cloud infra by construction. The pure "
    "engine never spawns a cloud-mutating process. Live execution is a separate, "
    "n=0-live, creds-gated build with its own grill/DESIGN."
)


def run_apply(*args: object, **kwargs: object) -> dict:
    """THE DEFERRED EXECUTION SEAM — the creds wall. Raises ALWAYS.

    n=0-live / creds-gated LIMITATION: this is the single cloud-mutating function
    and it is NOT implemented in this half (mirrors
    ``drift_gate.structural_drift_verdict``). It is reachable only behind a
    present+matching approval artifact AND a present capability grant AND present
    creds, and even then raises ``NotImplementedError`` — it cannot mutate cloud
    infra by construction. This module never imports the subprocess module on any
    path; the engine never executes a cloud mutation.

    Raises:
        NotImplementedError: always — the execution seam is DEFERRED (creds wall).
    """
    raise NotImplementedError(_RUN_APPLY_MSG)
