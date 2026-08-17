"""kata_dispatch.py — the SEAM engine + cross-model worker dispatch.

**The seam (trust-model DESIGN §1): every agent launch is a code act.**  The seam section
at the bottom of this module is the engine door — ``run_start`` / ``mint`` / ``capture`` /
``phase`` / ``deny`` plus the dispatch-record lifecycle.  "Module layout is a build detail;
the **surface is contract**" (DESIGN §1.3), which is why the seam extends this file rather
than opening a new one.  Every function there is engine code under the Determinism
Doctrine (D172): clocks and entropy are injectable, folds are pure, side effects happen
only after a fold completes, and committed JSON is ``sort_keys=True``.

The historical N1/N2/N3 cross-model dispatch chain is unchanged and documented below.

--------------------------------------------------------------------------- the seam

run_start(kata_dir, ...)              -> dict   new-vs-resume, rotation, reaping, marker,
                                                probes, and the §6.4 declaration
mint(*, governs, role, ...)           -> dict   the governor ladder (§1.4) + the dispatch
                                                record (§1.5) + the SPAWN cursor line
claim_record(kata_dir, record_id)     -> dict   the ATOMIC single-use claim (os.rename)
validate_record(record, ...)          -> dict   the SEMANTIC re-validation the hook runs
capture(envelope, record_id, ...)     -> dict   the ONE verdict parser + VERDICT/DOWN line
phase(kata_dir, msg, ...)             -> line   the §2.6 closed phase vocabulary
deny(kata_dir, reason, ...)           -> line   a DENY line naming the legal path

--------------------------------------------------------------------------- the N-chain

kata_dispatch.py — cross-model worker dispatch (N1 brief + N2 adapters + N3 result).

The multi-model loop routes a ROLE to a platform/model (kata_roles) and dispatches a
worker on that platform over the shared filesystem (DESIGN multi-model-orchestration):

  build_brief()  ->  the cross-model task-contract dict (N1; persisted as BRIEF.json by the caller)
  dispatch()     ->  runs the platform's headless CLI in a worktree (N2)
  normalize()    ->  the per-role result payload (N3); build_result() wraps it in the envelope
                     a caller persists as RESULT.json

These functions RETURN dicts; they do not themselves write BRIEF.json / RESULT.json (the
orchestrator owns persistence). `"fallback"` status covers the LD7 host-fallback path;
dispatch is wired into kata-orchestrate (Slice A of the multi-model layer build).

The CLI launch is behind an **injectable runner** so the whole chain is testable with a
stub CLI (no live host). The default runner shells out for real (gated on the CLI being
installed + confirmed). Per-platform CLI flags are point-in-time (RESEARCH §0/§6) — the
install confirm-probe is the standing guard; pin/verify at build.

Public API
----------
build_brief(task_id, role, platform, *, model, objective, result_path, plan_path, ...) -> dict  # N1
codex_command(brief, worktree) -> list[str]                                            # N2 (codex adapter)
dispatch(brief, worktree, runner=None, timeout=600) -> dict                            # N2 -> N3
normalize(role, raw_text) -> dict                                                      # N3 per-role payload
build_result(task_id, role, platform, model, status, payload, raw="") -> dict          # N3 envelope
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess  # noqa: S404 — used only by the default real runner; tests inject a stub
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

import yaml

import intent_scaffold as _intent
import kata_board as _kb
import kata_trail as _trail
from kata_restore import assert_frozen
from kata_roles import ROLE_GROUPS

_SANDBOX = frozenset({"read-only", "write"})
_STATUS = frozenset({"completed", "failed", "timeout", "fallback"})


# --------------------------------------------------------------------------- N1
def build_brief(
    task_id: str,
    role: str,
    platform: str,
    *,
    model: str,
    objective: str,
    result_path: str,
    plan_path: str | Path,
    inputs: list[str] | None = None,
    owned_files: list[str] | None = None,
    sandbox: str = "read-only",
    acceptance: str = "",
    output_contract: str | None = None,
) -> dict:
    """Build the cross-model task-brief (N1). Pure; validates role + sandbox.

    BL-F01 chokepoint: ``plan_path`` is a REQUIRED keyword-only argument, no default.
    Before this, nothing between a plan and a dispatched worker ever checked whether the
    plan was actually frozen — ``build_brief`` never even received the plan path. This
    call is now that chokepoint: it refuses (raises, via ``kata_restore.assert_frozen``)
    to build a brief against a plan whose ``status:`` is not ``frozen``, and it refuses
    BEFORE any other validation so no brief can be built for a caller who provides a bad
    plan_path along with an otherwise-valid role/objective/etc.

    ``plan_path`` deliberately has NO default. An optional gate that a caller can simply
    forget to pass is a silent-permissive default (D136) — exactly the "warn" posture
    rejected for this feature (operator: "we don't want a model making assumptions and
    just executing because it sees warn as a soft status"). Making it required means
    every existing caller (all of them tests today — build_brief has no non-test caller
    yet) had to be updated to pass a real plan_path; that migration is the cost of not
    having a bypassable gate.
    """
    assert_frozen(plan_path)
    if role not in ROLE_GROUPS:
        raise ValueError(f"kata_dispatch: unknown role {role!r}")
    if sandbox not in _SANDBOX:
        raise ValueError(f"kata_dispatch: sandbox must be one of {sorted(_SANDBOX)}, got {sandbox!r}")
    if not objective or not result_path:
        raise ValueError("kata_dispatch: objective and result_path are required")
    # Absolute under EITHER OS convention (Windows treats a leading "/" as drive-relative, not absolute),
    # or containing "..", is rejected — resultPath must stay inside the worktree.
    if (PurePosixPath(result_path).is_absolute() or PureWindowsPath(result_path).is_absolute()
            or any(part == ".." for part in Path(result_path).parts)):
        raise ValueError(f"kata_dispatch: resultPath must be worktree-relative, no '..': {result_path!r}")
    return {
        "taskId": task_id,
        "role": role,
        "platform": platform,
        "model": model,
        "objective": objective,
        "inputs": inputs or [],
        "boundaries": {"ownedFiles": owned_files or [], "sandbox": sandbox},
        "outputContract": output_contract or role,
        "resultPath": result_path,
        "acceptanceCriteria": acceptance,
    }


def _brief_prompt(brief: dict, capture: str = "emit") -> str:
    """The prompt handed to the worker: objective + inputs + boundaries + the result contract.

    ``capture="emit"`` (codex/default): the result is captured by the adapter's ``-o`` flag from
    the worker's FINAL message — the worker emits and does NOT write the result file itself.
    ``capture="write"`` (kiro): kiro has no ``-o`` capture (DESIGN §4 N2); the prompt instructs
    the worker to write the result JSON to ``resultPath`` directly.  ``_subprocess_runner`` reads
    ``resultPath`` after the run in both cases, so both paths converge at the same read point.
    """
    parts = [brief["objective"]]
    if brief.get("inputs"):
        parts.append("Inputs: " + ", ".join(brief["inputs"]))
    owned = brief.get("boundaries", {}).get("ownedFiles") or []
    if owned:
        parts.append("You may only modify: " + ", ".join(owned))
    parts.append(f"Acceptance: {brief['acceptanceCriteria']}")
    parts.append(f"Output contract: a single JSON object for role '{brief['role']}' ({brief['outputContract']}).")
    if capture == "write":
        parts.append(f"Write that JSON object to the file `{brief['resultPath']}`.")
    else:
        parts.append("Emit that JSON object as your FINAL message — it is captured automatically; do not write files.")
    return "\n".join(parts)


# --------------------------------------------------------------------------- N2
def codex_command(brief: dict, worktree: str) -> list[str]:
    """Build the `codex exec` command for a brief (the codex dispatch adapter).

    Uses ``-o <resultPath>`` to capture the worker's final JSON message to the result file;
    the prompt instructs the worker to emit JSON for its role. (A real per-role JSON-Schema
    file could later be passed to ``--output-schema`` for hard constraint — NOT the result
    path itself; passing the output path as the schema was a latent bug, fixed here.)
    """
    sandbox = "workspace-write" if brief["boundaries"]["sandbox"] == "write" else "read-only"
    return [
        "codex", "exec",
        "--skip-git-repo-check",
        "--cd", str(worktree),
        "--sandbox", sandbox,
        "--model", brief["model"],
        "-o", brief["resultPath"],
        _brief_prompt(brief, capture="emit"),
    ]


def kiro_command(brief: dict, worktree: str) -> list[str]:
    """Build the ``kiro-cli chat`` command for a brief (the kiro dispatch adapter).

    Launches kiro in headless mode with the assigned role as the agent.  Because kiro has no
    ``-o`` capture flag (DESIGN §4 N2), ``_brief_prompt`` is called with ``capture="write"``
    so the prompt instructs the worker to write the result JSON to ``resultPath`` itself.
    ``_subprocess_runner`` then reads ``resultPath`` after the run — the same read point as
    the codex path, so both adapters converge at N3 normalize.

    Command shape (DESIGN §4 N2, June-2026 point-in-time snapshot — RESEARCH §0/§6):
        kiro-cli chat --no-interactive --agent <role> <prompt>
    ⚠ Pin/verify these flags at build; the N5 confirm-probe is the standing guard against
    stale flag names between kiro-cli releases.
    """
    return [
        "kiro-cli", "chat",
        "--no-interactive",
        "--agent", brief["role"],
        _brief_prompt(brief, capture="write"),
    ]


# adapter registry: platform -> command builder. Claude uses the in-process Agent path
# (no external CLI) and is handled by the orchestrator, not here.
_COMMAND_BUILDERS = {"codex": codex_command, "kiro": kiro_command}


def _safe_result_path(result_path: str, cwd: str) -> Path:
    """Resolve ``result_path`` strictly UNDER ``cwd`` (CWE-23). Reject ``..`` and any escape.

    Mirrors the ``_safe_abs`` ``..``-guard the rest of the codebase applies (kata_install /
    kata_settings) — the result file must live inside the worker's worktree, never outside it.
    """
    if any(part == ".." for part in Path(result_path).parts):
        raise ValueError(f"kata_dispatch: refusing resultPath with '..' traversal: {result_path!r}")
    base = Path(cwd).resolve()
    rp = (base / result_path).resolve()
    if base != rp and base not in rp.parents:
        raise ValueError(f"kata_dispatch: resultPath escapes the worktree: {result_path!r}")
    return rp


_STDERR_TAIL_CHARS = 4000
_STDERR_TRUNCATION_MARKER = f"[stderr truncated to last {_STDERR_TAIL_CHARS} chars]\n"


def _stderr_tail(stderr) -> str:
    """Deterministic tail cap for worker stderr carried into RESULT envelopes.

    The ONE dispatch-side choke point (injected runners cannot bypass it): keeps the LAST
    ``_STDERR_TAIL_CHARS`` chars — provider error text (rate-limit/quota/auth) arrives at the
    END of stderr — prepending a literal marker only when clipped. Accepts ``bytes``
    (``TimeoutExpired.stderr`` is bytes on some platforms) and decodes tolerantly.
    Pure function of its input (Determinism Doctrine).
    """
    if stderr is None:
        return ""
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    if len(stderr) > _STDERR_TAIL_CHARS:
        return _STDERR_TRUNCATION_MARKER + stderr[-_STDERR_TAIL_CHARS:]
    return stderr


def _subprocess_runner(cmd: list[str], cwd: str, result_path: str, timeout: int):
    """Default real runner: shell out, then read the worker's result file. Gated on the CLI existing."""
    rp = _safe_result_path(result_path, cwd)
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)  # noqa: S603
    result_text = rp.read_text(encoding="utf-8") if rp.exists() else ""
    return proc.returncode, proc.stdout, proc.stderr, result_text


def dispatch(brief: dict, worktree: str, runner=None, timeout: int = 600) -> dict:
    """Dispatch a worker for ``brief`` in ``worktree``; return a normalized RESULT envelope (N2→N3).

    ``runner(cmd, cwd, result_path, timeout) -> (exit_code, stdout, stderr, result_text)`` is
    injectable (a stub in tests; the real subprocess runner by default). The worker's stderr is
    carried — tail-capped via ``_stderr_tail`` — into the payload of every FAILURE envelope
    (exit≠0 / timeout / unparseable result) so the provider error signal survives dispatch;
    the ``completed`` envelope is byte-unchanged and ``raw`` keeps stdout-only semantics.
    """
    platform = brief["platform"]
    builder = _COMMAND_BUILDERS.get(platform)
    if builder is None:
        # No adapter for this platform → fail gracefully (LD7 surfaces it / host-fallback),
        # never crash the loop. (A confirmed-but-undispatchable platform must not raise.)
        return build_result(
            brief["taskId"], brief["role"], platform, brief.get("model"), "failed",
            {"error": f"no dispatch adapter for platform {platform!r}"}, raw="",
        )
    cmd = builder(brief, worktree)
    runner = runner or _subprocess_runner

    try:
        exit_code, stdout, stderr, result_text = runner(cmd, worktree, brief["resultPath"], timeout)
    except subprocess.TimeoutExpired as exc:
        # Captured-so-far stderr rides the timeout envelope — a quota-hung worker's last words.
        payload: dict = {}
        tail = _stderr_tail(getattr(exc, "stderr", None))
        if tail:
            payload["stderr"] = tail
        return build_result(brief["taskId"], brief["role"], platform, brief["model"], "timeout", payload, raw="")

    stderr_tail = _stderr_tail(stderr)
    if exit_code != 0:
        payload = {"error": f"worker exited {exit_code}"}
        if stderr_tail:
            payload["stderr"] = stderr_tail
        return build_result(
            brief["taskId"], brief["role"], platform, brief["model"], "failed",
            payload, raw=stdout,
        )
    try:
        payload = normalize(brief["role"], result_text)
    except (ValueError, TypeError, AttributeError, json.JSONDecodeError) as e:
        payload = {"error": f"unparseable result: {e}"}
        if stderr_tail:
            payload["stderr"] = stderr_tail
        return build_result(
            brief["taskId"], brief["role"], platform, brief["model"], "failed",
            payload, raw=result_text,
        )
    return build_result(brief["taskId"], brief["role"], platform, brief["model"], "completed", payload, raw=stdout)


# --------------------------------------------------------------------------- N3
def build_result(task_id, role, platform, model, status: str, payload: dict, raw: str = "") -> dict:
    """Build the RESULT envelope (N3). ``status`` = the DISPATCH OUTCOME (not the verdict)."""
    if status not in _STATUS:
        raise ValueError(f"kata_dispatch: status must be one of {sorted(_STATUS)}, got {status!r}")
    return {
        "taskId": task_id, "role": role, "platform": platform, "model": model,
        "status": status, "payload": payload, "raw": raw,
    }


def normalize(role: str, raw_text: str) -> dict:
    """Map a worker's raw JSON output to the ROLE's payload shape (N3). Raises on a missing verdict.

    The verdict lives in the payload (distinct from the envelope ``status``):
    - validator      -> {verdict: "ship"|"hold", findings: [...]}
    - evaluator      -> {score: 0.0-1.0, decision: "accept"|"send-back"|"reroll", reason}
    - researcher     -> {claim, source, confidence, groundsToPlan}
    - coder          -> {resultJson?, diffPath?}  (the gate RESULT.json is produced separately)
    - design-author  -> {designPath, verdict: "ready"|"needs-rework", deviations: [...]}
                        (DESIGN §4.3, dispatch-authoring spec — designPath/verdict REQUIRED)
    - plan-author    -> {planPath,   verdict: "ready"|"needs-rework", deviations: [...]}
                        (DESIGN §4.3, dispatch-authoring spec — planPath/verdict REQUIRED)
    """
    if not raw_text.strip():
        raise ValueError(f"empty worker result for role {role!r} (default-FAIL)")
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        raise ValueError(f"worker result must be a JSON object, got {type(data).__name__}")
    if role == "validator":
        verdict = data.get("verdict")
        if verdict not in {"ship", "hold"}:
            raise ValueError(f"validator result missing verdict ship|hold (got {verdict!r})")
        return {"verdict": verdict, "findings": data.get("findings", [])}
    if role == "evaluator":
        decision = data.get("decision")
        if decision not in {"accept", "send-back", "reroll"}:
            raise ValueError(f"evaluator result missing decision accept|send-back|reroll (got {decision!r})")
        score = data.get("score")
        if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0):
            raise ValueError(f"evaluator score must be a number in [0.0, 1.0] (got {score!r})")
        return {"score": score, "decision": decision, "reason": data.get("reason", "")}
    if role == "researcher":
        if not (data.get("claim") or data.get("groundsToPlan")):
            raise ValueError("researcher result missing both claim and groundsToPlan (default-FAIL)")
        claim = data.get("claim")
        source = data.get("source")
        # Q-13: an ungrounded claim is not a finding.  Mirror escalation.build_finding's
        # source-required rule (D136 fail-closed): when a claim is asserted, its citation
        # is mandatory and must be a non-empty string.  Without this a cross-model
        # researcher result with a claim but no source silently flowed in as completed.
        # (The confidence/groundsToPlan enum from build_finding is NOT replicated here:
        # this role's schema uses a numeric confidence and free-text groundsToPlan.)
        if claim and not (isinstance(source, str) and source.strip()):
            raise ValueError(
                "researcher result has an ungrounded claim: 'source' citation is required "
                "and must be a non-empty string (default-FAIL)"
            )
        return {
            "claim": claim, "source": source,
            "confidence": data.get("confidence"), "groundsToPlan": data.get("groundsToPlan"),
        }
    if role == "design-author":
        design_path = data.get("designPath")
        if not isinstance(design_path, str) or not design_path.strip():
            raise ValueError(f"design-author result missing designPath (got {design_path!r})")
        verdict = data.get("verdict")
        if verdict not in {"ready", "needs-rework"}:
            raise ValueError(f"design-author result missing verdict ready|needs-rework (got {verdict!r})")
        return {"designPath": design_path, "verdict": verdict, "deviations": data.get("deviations", [])}
    if role == "plan-author":
        plan_path = data.get("planPath")
        if not isinstance(plan_path, str) or not plan_path.strip():
            raise ValueError(f"plan-author result missing planPath (got {plan_path!r})")
        verdict = data.get("verdict")
        if verdict not in {"ready", "needs-rework"}:
            raise ValueError(f"plan-author result missing verdict ready|needs-rework (got {verdict!r})")
        return {"planPath": plan_path, "verdict": verdict, "deviations": data.get("deviations", [])}
    # coder / orchestrator: pass through the worker's reported object, but reject an empty one
    if not data:
        raise ValueError(f"empty payload for role {role!r} (default-FAIL)")
    return data


# ===========================================================================
# THE SEAM — every agent launch is a code act (trust-model DESIGN §1)
# ===========================================================================
#
# Transcribed from the gated DESIGN, never re-derived.  Section anchors are cited
# inline; a behaviour here without an anchor is drift.
#
# Determinism Doctrine (D172): `now` and `entropy` are injectable everywhere they
# are consumed, no fold reads the clock, side effects follow the fold, and
# wall-clock is NEVER load-bearing for a decision (the `mintedUtc` window is
# defense-in-depth only — RS-M12).

#: The agent-id the seam stamps on the lines it authors (DESIGN §2.3 writer classes).
SEAM_AGENT = "seam"

#: Dispatch records live under ``<kata_dir>/dispatch/`` — tier-3, the cursor chain
#: entry being the durable half (DESIGN §1.5 / R-L4).
DISPATCH_DIRNAME = "dispatch"
#: Claimed records are renamed into this subdirectory and RETAINED (R3-M1).
CONSUMED_DIRNAME = "consumed"
#: Orphans (a record with no matching cursor lineage) are reaped here, never deleted.
REAPED_DIRNAME = "reaped"
#: The seam-init run marker the W8 deny hook reads for scope (DESIGN §8 RS-L5).
RUN_MARKER_FILENAME = "run-marker.json"

#: The closed governor vocabulary (DESIGN §1.4).  Unknown governor ⇒ refuse to mint.
GOVERNORS: frozenset[str] = frozenset({"plan", "ledger", "intent", "initiation"})

#: The closed four-value grill-ledger status enum (DESIGN §1.4, R2-H1).
LEDGER_STATUSES: tuple[str, ...] = ("draft", "converged", "frozen", "absorbed")

#: Ordering over ledger statuses (DESIGN §1.4): ``draft < converged``, and ``frozen``
#: satisfies anything ``converged`` satisfies.  ``absorbed`` is deliberately ABSENT —
#: it never satisfies a mint, it ROUTES it (pass-1 SHIP residual 2, R3-M3, E6).
_LEDGER_RANK: dict[str, int] = {"draft": 1, "converged": 2, "frozen": 3}

#: Guardian grade of each governor rung (DESIGN §1.4 table, §6.2 vocabulary).
GOVERNOR_GRADE: dict[str, str] = {
    "plan": "Verified",
    "ledger": "Verified",
    "intent": "Verified",
    "initiation": "Honor-system",
}

#: Role classes for the per-role minimum-state table (DESIGN §1.4).
_ROLE_CLASS: dict[str, str] = {
    # "Plan-executing roles — coder, task-scoped judges, anything dispatched against a plan task"
    "coder": "plan-executing",
    "validator": "plan-executing",
    "evaluator": "plan-executing",
    "orchestrator": "plan-executing",
    "reviewer": "plan-executing",
    "slop": "plan-executing",
    "inline-eval": "plan-executing",
    "critic": "plan-executing",
    "challenger": "plan-executing",
    "grounding": "plan-executing",
    # "design-author / plan-author"
    "design-author": "authoring",
    "plan-author": "authoring",
    # "Grill-phase researchers / advisor / convergence reviewers"
    "researcher": "grill-phase",
    "advisor": "grill-phase",
}

#: The ledger rung's minimum state, BY ROLE CLASS (DESIGN §1.4 rows 2 and 4).  A role
#: class absent from this map has NO ledger-governed rung and is refused there —
#: fail-closed, because an unlisted row is an unruled one.
_LEDGER_MINIMUM: dict[str, str] = {"authoring": "converged", "grill-phase": "draft"}

#: The phase vocabulary — a CLOSED enum (DESIGN §2.6).
PHASES: frozenset[str] = frozenset({
    "INITIATION", "GRILL", "AUTHORING", "FREEZE", "EXECUTION",
    "FINAL-GATE", "CLOSEOUT", "LOOP-BACK",
})
#: Phases the initiation governor rung reads as "open" (DESIGN §1.4, pass-2 low 13).
INITIATION_PHASES: frozenset[str] = frozenset({"INITIATION", "AUTHORING"})
#: EXECUTION is the one parameterized phase: ``EXECUTION (wave=<n>)`` (DESIGN §2.6).
_WAVE_PARAM = "wave"

#: PHASE msg verbs (DESIGN §2.6): ``open <PHASE> [k=v…] | close <PHASE> [k=v…] | run-closed [k=v…]``.
_PHASE_VERBS: frozenset[str] = frozenset({"open", "close"})
_RUN_CLOSED = "run-closed"
_KV_RE = re.compile(r"\A([A-Za-z][A-Za-z0-9_.-]*)=([^\s|]+)\Z")

#: Guardian scale values, VERBATIM from the DESIGN §6.2 table.  No builder invention:
#: a value not in these sets cannot be rendered into a declaration.
ENFORCEMENT_INTERCEPTING = "Verified (intercepting)"
ENFORCEMENT_BASH_LEG = "Partially verified (bash-leg)"
ENFORCEMENT_DORMANT = "Dormant (pre-activation)"
ENFORCEMENT_DETECTION_ONLY = "Honor-system (detection-only host)"
ENFORCEMENT_VALUES: frozenset[str] = frozenset({
    ENFORCEMENT_INTERCEPTING, ENFORCEMENT_BASH_LEG, ENFORCEMENT_DORMANT, ENFORCEMENT_DETECTION_ONLY,
})
CAPTURE_POST_EDGE = "Verified (post-edge)"
CAPTURE_ENGINE_BY_CONDUCTOR = "Honor-system (engine-by-conductor)"
CAPTURE_VALUES: frozenset[str] = frozenset({CAPTURE_POST_EDGE, CAPTURE_ENGINE_BY_CONDUCTOR})

#: The W8 deny/capture hook.  Named here because seam init must PROBE for it; the hook
#: itself is built by PLAN wave 8 (`hook-activation`) and is absent today.
HOOK_RELPATH = ("adapters", "claude", "hooks", "kata-seam-guard.py")
HOOK_FILENAME = "kata-seam-guard.py"
#: Optional `kata.config` expectation read by the TM-H2 consistency check.  Absent ⇒ no
#: expectation declared ⇒ no drift (the registry row for this key rides W8/W7 per D-17's
#: G6 precedent — this module only READS it).
CONFIG_KEY_SEAM_GUARD = "hooks.seamGuard"

#: MINT→LAUNCH window, seconds.  **Defense-in-depth ONLY** (DESIGN §1.5 step 4, RS-M12):
#: the atomic single-use claim is THE replay control.  Nothing refuses on this value.
MINT_LAUNCH_WINDOW_S = 3600

#: Absorbed-routing hop cap (see :func:`resolve_absorbed_ledger`).
ABSORBED_MAX_HOPS = 4

#: A ledger path token inside a free-prose `status:` line.  Deliberately narrow: the
#: token must END in ``LEDGER.md`` (the corpus's ledger filename shape), so ordinary
#: prose in a status line cannot masquerade as a routing target.
_LEDGER_TOKEN_RE = re.compile(r"[A-Za-z0-9_.\-/]*LEDGER\.md")

_FM_RE = re.compile(r"^---[ \t]*\n(.*?)\n---", re.DOTALL)


# --------------------------------------------------------------------------- errors


class SeamError(Exception):
    """Base class for every seam refusal."""


class MintRefused(SeamError):
    """The engine refuses to mint — DESIGN §1.8 park semantics apply.

    There is **no legal path** past this refusal: the caller ESCALATEs
    ``human-required``, and an unattended run PARKS the task.  The exception names
    the park path so the caller never has to derive it (TM-B5).
    """

    def __init__(self, message: str, *, park_path: str | Path | None = None,
                 task_id: str | None = None, deny_class: bool = False) -> None:
        self.park_path = str(park_path) if park_path is not None else None
        self.task_id = task_id
        self.escalation_kind = "human-required"
        self.deny_class = deny_class
        if self.park_path:
            message = (
                f"{message}  No legal path: ESCALATE kind='human-required'; an unattended "
                f"run PARKS the task at {self.park_path}."
            )
        super().__init__(message)


class AbsorbedRoutingAmbiguous(MintRefused):
    """An `absorbed` ledger's routing target could not be resolved unambiguously (E6)."""


class RecordClaimRefused(SeamError):
    """A dispatch record could not be claimed: already consumed, absent, or lost a race."""


class CaptureRefused(SeamError):
    """The capture edge refuses — the absent-records refusal path (DESIGN §5.3).

    Raised when the record is missing OR when the envelope's line 1 carries no
    parseable verdict.  There is deliberately **no body-scan fallback** (pass-2 low 14).
    """


class PhaseRefused(SeamError):
    """A PHASE act violated the closed vocabulary, the msg grammar, or terminality."""


# --------------------------------------------------------------------------- guards


def _safe_kata_dir(raw: str | Path) -> Path:
    """Reject ``..`` traversal in an operator-supplied kata dir, then resolve (CWE-23).

    Mirrors ``kata_board._safe_path`` / ``escalation._safe_kata_dir`` (keep in sync —
    the repo's path-guard family, whose membership test pins every copy).
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"kata_dispatch: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


def _utc(now: datetime | None) -> str:
    """The recorded UTC stamp.  Injectable; never load-bearing for any decision."""
    return (now or datetime.now(UTC)).astimezone(UTC).isoformat()


def _frontmatter(path: Path, *, what: str) -> dict:
    """Read a markdown file's YAML frontmatter as a dict, or raise.  Fail-closed."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"kata_dispatch: cannot read {what} at {path!s} ({exc}) — refusing to assume "
            "a status. Resolve manually."
        ) from exc
    match = _FM_RE.match(content)
    if not match:
        raise ValueError(
            f"kata_dispatch: {what} at {path!s} has no YAML frontmatter — cannot determine "
            "its status. Resolve manually."
        )
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ValueError(
            f"kata_dispatch: {what} frontmatter at {path!s} is not valid YAML — {exc}. "
            "Resolve manually."
        ) from exc
    if not isinstance(fm, dict):
        raise ValueError(
            f"kata_dispatch: {what} frontmatter at {path!s} is not a mapping — cannot "
            "determine its status. Resolve manually."
        )
    return fm


# --------------------------------------------------------------------------- §1.4 ledger rung


def ledger_status(ledger_path: str | Path) -> str:
    """Return a grill ledger's normalized status from its frontmatter ``status:`` field.

    The `ledger` governor rung's predicate (DESIGN §1.4, R2-H1).  The posture is copied
    from ``kata_restore.plan_status`` / ``intent_scaffold.intent_status`` deliberately —
    three governor rungs that read a ``status:`` field must not disagree about what that
    field means:

    - key absent, or present but empty/whitespace-only ⇒ ``"absent"``.  NOT satisfying.
      (15 of the 29 live ledgers are in exactly this state — evidence/ledger-status-table.md.)
    - otherwise the value is split on whitespace and the **first word** is taken,
      case-folded (BL-F01's first-word parse rule); trailing prose is ignored, because a
      status carrying a trailing note is a real authoring shape — the live corpus's
      ``status: absorbed — 2026-08-16, operator-ruled: …`` is the canonical example.
    - first word in ``draft | converged | frozen | absorbed`` ⇒ that lowercase token.
    - any other first word ⇒ RAISES.  Never coerced to a default in either direction.

    Returns
    -------
    str
        One of ``"draft"``, ``"converged"``, ``"frozen"``, ``"absorbed"``, ``"absent"``.
    """
    path = Path(ledger_path)
    fm = _frontmatter(path, what="ledger")
    raw = fm.get("status")
    if raw is None:
        return "absent"
    raw_str = str(raw).strip()
    if not raw_str:
        return "absent"
    first_word = raw_str.split()[0].casefold()
    if first_word in LEDGER_STATUSES:
        return first_word
    raise ValueError(
        f"kata_dispatch: ledger at {path!s} has an unrecognized status {raw_str!r} (first "
        f"word {first_word!r} is not one of {list(LEDGER_STATUSES)}) — refusing to coerce "
        "to a default. Resolve manually."
    )


def ledger_satisfies(status: str, minimum: str) -> bool:
    """True iff *status* satisfies a rung requiring at least *minimum* (DESIGN §1.4).

    ``draft < converged``; ``frozen`` satisfies anything ``converged`` satisfies.
    ``absorbed`` and ``absent`` satisfy NOTHING — ``absorbed`` routes (see
    :func:`resolve_absorbed_ledger`), ``absent`` is simply unmet.
    """
    if status not in _LEDGER_RANK or minimum not in _LEDGER_RANK:
        return False
    return _LEDGER_RANK[status] >= _LEDGER_RANK[minimum]


def _absorbed_target(ledger: Path) -> Path:
    """Resolve ONE hop of `absorbed` routing.  Ambiguity ⇒ refuse (E6).

    **The resolution rule, in full** (DESIGN §1.4 leaves the mechanism to the build;
    conductor ruling R2 in ``evidence/ledger-status-table.md`` requires either a
    parseable field or a documented prose rule):

    1. **Preferred, unambiguous:** a frontmatter key ``absorbed-into: <path>``.  When
       present it wins outright and no prose is read.
    2. **Prose fallback** (what the LIVE corpus has — `dispatch-seam`'s status line names
       ``../trust-model/GRILL-LEDGER.md`` in prose): every token in the ``status:`` value
       matching ``[A-Za-z0-9_.\\-/]*LEDGER.md`` is collected.  **Exactly one distinct
       token must be found**; zero or two-or-more ⇒ refuse.
    3. The token is guarded: it must not be absolute, must carry no drive letter and no
       backslash, and must resolve — relative to the ledger's own directory — to an
       EXISTING file that stays inside the ledger's parent directory's parent (the
       specs root).  Sibling-spec routing only; anything wider ⇒ refuse.

    Every refusal is a :class:`AbsorbedRoutingAmbiguous` ⇒ park.  The rule never guesses.
    """
    fm = _frontmatter(ledger, what="ledger")
    declared = fm.get("absorbed-into")
    if declared is not None and str(declared).strip():
        token = str(declared).strip()
        source = "absorbed-into frontmatter key"
    else:
        raw_status = str(fm.get("status") or "")
        found = []
        for match in _LEDGER_TOKEN_RE.findall(raw_status):
            if match and match not in found:
                found.append(match)
        if not found:
            raise AbsorbedRoutingAmbiguous(
                f"kata_dispatch: ledger at {ledger!s} is 'absorbed' but names no routing "
                "target: neither an 'absorbed-into:' frontmatter key nor exactly one "
                "'*LEDGER.md' token in its status prose. Refusing to guess the absorbing "
                "ledger.",
            )
        if len(found) > 1:
            raise AbsorbedRoutingAmbiguous(
                f"kata_dispatch: ledger at {ledger!s} is 'absorbed' and its status prose "
                f"names {len(found)} candidate ledgers {found} — ambiguous. Add an "
                "'absorbed-into:' frontmatter key naming the one absorbing ledger.",
            )
        token = found[0]
        source = "status-line prose token"

    if "\\" in token or Path(token).is_absolute() or Path(token).drive or token.startswith("/"):
        raise AbsorbedRoutingAmbiguous(
            f"kata_dispatch: ledger at {ledger!s} routes to {token!r} ({source}), which is "
            "not a ledger-relative POSIX path. Refusing to follow it.",
        )
    target = (ledger.parent / token).resolve()
    boundary = ledger.parent.parent.resolve()
    if boundary != target and boundary not in target.parents:
        raise AbsorbedRoutingAmbiguous(
            f"kata_dispatch: ledger at {ledger!s} routes to {token!r} ({source}), which "
            f"escapes the specs root {boundary!s}. Sibling-spec routing only.",
        )
    if not target.is_file():
        raise AbsorbedRoutingAmbiguous(
            f"kata_dispatch: ledger at {ledger!s} routes to {token!r} ({source}), which "
            f"does not exist at {target!s}. Refusing to mint against a phantom ledger.",
        )
    return target


def resolve_absorbed_ledger(ledger_path: str | Path) -> Path:
    """Follow `absorbed` routing to the absorbing ledger (DESIGN §1.4, E6).

    ``absorbed`` **never satisfies a mint and never hard-fails as unknown — it ROUTES
    the mint to the absorbing ledger.**  A non-absorbed ledger is returned unchanged, so
    this is safe to call unconditionally.  A routing chain is followed to at most
    ``ABSORBED_MAX_HOPS``; a cycle or an over-long chain is a refusal, never a loop.
    """
    current = Path(ledger_path).resolve()
    seen: list[Path] = []
    for _hop in range(ABSORBED_MAX_HOPS):
        if ledger_status(current) != "absorbed":
            return current
        seen.append(current)
        target = _absorbed_target(current)
        if target in seen:
            raise AbsorbedRoutingAmbiguous(
                f"kata_dispatch: absorbed-routing cycle through {target!s} "
                f"(chain: {[str(p) for p in seen]}). Refusing to mint.",
            )
        current = target
    raise AbsorbedRoutingAmbiguous(
        f"kata_dispatch: absorbed-routing chain from {ledger_path!s} exceeds "
        f"{ABSORBED_MAX_HOPS} hops (chain: {[str(p) for p in seen]}). Refusing to mint.",
    )


# --------------------------------------------------------------------------- §2.6 phase reads


def parse_phase_msg(msg: str) -> dict:
    """Parse a PHASE msg against the closed grammar (DESIGN §2.6).

    Grammar, enforced exactly::

        open <PHASE> [k=v …] | close <PHASE> [k=v …] | run-closed [k=v …]

    ``EXECUTION`` is the one parameterized phase and REQUIRES ``wave=<digits>``.

    Returns ``{"verb", "phase", "params", "key"}`` where ``key`` is the identity a
    close must match an open on (``EXECUTION(wave=2)`` for waves, the phase name
    otherwise).  Anything else raises :class:`PhaseRefused`.
    """
    if not isinstance(msg, str) or not msg.strip():
        raise PhaseRefused("kata_dispatch: PHASE msg must be a non-empty string")
    tokens = msg.split()
    verb = tokens[0]
    if verb == _RUN_CLOSED:
        phase, rest = None, tokens[1:]
    elif verb in _PHASE_VERBS:
        if len(tokens) < 2:
            raise PhaseRefused(
                f"kata_dispatch: PHASE msg {msg!r} is '{verb}' with no phase; the grammar is "
                f"'open <PHASE> [k=v…]' | 'close <PHASE> [k=v…]' | '{_RUN_CLOSED} [k=v…]'"
            )
        phase, rest = tokens[1], tokens[2:]
        if phase not in PHASES:
            raise PhaseRefused(
                f"kata_dispatch: unknown phase {phase!r}; the vocabulary is CLOSED: "
                f"{sorted(PHASES)} (DESIGN §2.6)"
            )
    else:
        raise PhaseRefused(
            f"kata_dispatch: PHASE msg {msg!r} does not start with a legal verb; the grammar "
            f"is 'open <PHASE> [k=v…]' | 'close <PHASE> [k=v…]' | '{_RUN_CLOSED} [k=v…]'"
        )

    params: dict[str, str] = {}
    for token in rest:
        match = _KV_RE.match(token)
        if not match:
            raise PhaseRefused(
                f"kata_dispatch: PHASE msg {msg!r} carries {token!r}, which is not a 'k=v' "
                "parameter (key: letter then word chars/.-; value: no whitespace, no '|')"
            )
        if match.group(1) in params:
            raise PhaseRefused(f"kata_dispatch: PHASE msg {msg!r} repeats parameter {match.group(1)!r}")
        params[match.group(1)] = match.group(2)

    if phase == "EXECUTION":
        wave = params.get(_WAVE_PARAM)
        if wave is None or not wave.isdigit():
            raise PhaseRefused(
                f"kata_dispatch: EXECUTION is parameterized and REQUIRES 'wave=<n>' with a "
                f"numeric n (DESIGN §2.6); got {msg!r}"
            )
    key = f"EXECUTION(wave={params[_WAVE_PARAM]})" if phase == "EXECUTION" else phase
    return {"verb": verb, "phase": phase, "params": params, "key": key}


def phase_state(cursor: _kb.Cursor) -> dict:
    """Fold the cursor's PHASE lines into ``{"open": [...], "closed": [...], "runClosed": bool}``.

    PURE (Determinism Doctrine law 6): no clock, no filesystem.  A PHASE line that does
    not parse is a REFUSAL, never a skip — the cursor's own posture.
    """
    open_keys: list[str] = []
    closed_keys: list[str] = []
    run_closed = False
    for line in sorted(cursor.lines, key=lambda ln: (ln.seq, ln.pos)):
        if line.type != "PHASE":
            continue
        parsed = parse_phase_msg(line.msg)
        if parsed["verb"] == _RUN_CLOSED:
            run_closed = True
            continue
        key = parsed["key"]
        if parsed["verb"] == "open":
            open_keys.append(key)
        else:
            if key in open_keys:
                open_keys.remove(key)
            closed_keys.append(key)
    return {"open": open_keys, "closed": closed_keys, "runClosed": run_closed}


def is_run_closed(cursor: _kb.Cursor) -> bool:
    """True once the terminal ``run-closed`` PHASE line exists (DESIGN §2.6, R4 residual 3)."""
    return phase_state(cursor)["runClosed"]


def _spawn_fields(msg: str) -> dict:
    """Parse the ``k=v`` fields the seam writes into a SPAWN msg.  PURE."""
    fields: dict[str, str] = {}
    for token in msg.split():
        match = _KV_RE.match(token)
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def recorded_governors(cursor: _kb.Cursor) -> list[dict]:
    """Every governor recorded on the cursor's SPAWN lines, in order of record.  PURE."""
    out: list[dict] = []
    for line in sorted(cursor.lines, key=lambda ln: (ln.seq, ln.pos)):
        if line.type != "SPAWN":
            continue
        fields = _spawn_fields(line.msg)
        if "governs" in fields:
            out.append({"seq": line.seq, "governs": fields["governs"], "state": fields.get("state")})
    return out


def has_stronger_governor(cursor: _kb.Cursor) -> dict | None:
    """Return the first recorded ``plan:frozen`` / ``ledger:converged+`` mint, else None.

    The RS-H3 rung-exclusivity predicate: initiation-governed minting is REFUSED once
    the live run records a stronger governor.  PURE.
    """
    for entry in recorded_governors(cursor):
        if entry["governs"] == "plan" and entry["state"] == "frozen":
            return entry
        if entry["governs"] == "ledger" and ledger_satisfies(entry["state"] or "", "converged"):
            return entry
    return None


# --------------------------------------------------------------------------- §1.4 the ladder


def _park_path(kata_dir: Path, task_id: str | None) -> Path:
    """The async-park destination named by a refusal (TM-B5, the existing park pattern)."""
    return kata_dir / "escalations" / f"{task_id or 'unknown-task'}.json"


def check_governor(
    *,
    governs: str,
    role: str,
    kata_dir: str | Path,
    plan_path: str | Path | None = None,
    ledger_path: str | Path | None = None,
    intent_path: str | Path | None = None,
    priming_prompt_hash: str | None = None,
    cursor: _kb.Cursor | None = None,
    task_id: str | None = None,
) -> dict:
    """Validate the governor rung for ``(governs, role)``; return the governed-artifact ref.

    The per-role minimum states are EXACTLY the DESIGN §1.4 table:

    ========================================  ==========================  ==============
    Role class                                Governor : minimum           Guardian grade
    ========================================  ==========================  ==============
    plan-executing (coder, task-scoped judges) ``plan : frozen``           Verified
    design/plan-author WITH a grill ledger     ``ledger : converged``      Verified
    design/plan-author with NO ledger          ``initiation``              Honor-system
    grill-phase researchers / advisor          ``ledger : present(draft)`` Verified
    bootstrap / harness-entry runs             ``intent : frozen``         Verified
    initiation-phase mints                     ``initiation``              Honor-system
    ========================================  ==========================  ==============

    ``plan`` and ``intent`` are role-agnostic rungs (the table's rows say "anything
    dispatched against a plan task" and "runs that ENTERED via initiation/kata-loop").
    ``ledger`` is role-class-scoped: a role class with no ledger row is REFUSED there.

    Raises :class:`MintRefused` (naming the park path) on an unknown governor, a role
    with no such rung, or an unmet state.
    """
    kata = _safe_kata_dir(kata_dir)
    park = _park_path(kata, task_id)

    def refuse(message: str, *, deny_class: bool = False, cls: type[MintRefused] = MintRefused) -> MintRefused:
        return cls(message, park_path=park, task_id=task_id, deny_class=deny_class)

    if role not in ROLE_GROUPS:
        raise refuse(f"kata_dispatch: unknown role {role!r} (valid: {sorted(ROLE_GROUPS)}).")
    if governs not in GOVERNORS:
        raise refuse(
            f"kata_dispatch: unknown governor {governs!r}; the vocabulary is CLOSED: "
            f"{sorted(GOVERNORS)} (DESIGN §1.4)."
        )

    grade = GOVERNOR_GRADE[governs]

    if governs == "plan":
        if plan_path is None:
            raise refuse("kata_dispatch: governs='plan' requires plan_path.")
        try:
            assert_frozen(plan_path)  # unchanged, exactly as D169 rules
        except ValueError as exc:
            raise refuse(f"kata_dispatch: plan rung unmet — {exc}") from exc
        return {"governs": "plan", "ref": str(plan_path), "state": "frozen", "grade": grade}

    if governs == "intent":
        if intent_path is None:
            raise refuse("kata_dispatch: governs='intent' requires intent_path.")
        try:
            status = _intent.intent_status(intent_path)
        except ValueError as exc:
            raise refuse(f"kata_dispatch: intent rung unmet — {exc}") from exc
        if status != "frozen":
            raise refuse(
                f"kata_dispatch: intent rung unmet — INTENT at {intent_path!s} is "
                f"status={status!r}, not 'frozen'."
            )
        return {"governs": "intent", "ref": str(intent_path), "state": "frozen", "grade": grade}

    if governs == "ledger":
        if ledger_path is None:
            raise refuse("kata_dispatch: governs='ledger' requires ledger_path.")
        role_class = _ROLE_CLASS.get(role)
        minimum = _LEDGER_MINIMUM.get(role_class or "")
        if minimum is None:
            raise refuse(
                f"kata_dispatch: role {role!r} (class {role_class!r}) has no ledger-governed "
                f"rung in the DESIGN §1.4 table; ledger rungs exist for role classes "
                f"{sorted(_LEDGER_MINIMUM)}. Use the rung its row names."
            )
        # `absorbed` ROUTES the mint to the absorbing ledger (E6) — never satisfies,
        # never hard-fails as unknown.  Ambiguity inside the routing is a park.
        resolved = resolve_absorbed_ledger(ledger_path)
        try:
            status = ledger_status(resolved)
        except ValueError as exc:
            raise refuse(f"kata_dispatch: ledger rung unmet — {exc}") from exc
        if not ledger_satisfies(status, minimum):
            raise refuse(
                f"kata_dispatch: ledger rung unmet — ledger at {resolved!s} is "
                f"status={status!r}; role {role!r} requires at least {minimum!r}."
            )
        ref: dict = {"governs": "ledger", "ref": str(resolved), "state": status, "grade": grade}
        if Path(resolved) != Path(ledger_path).resolve():
            ref["routedFrom"] = str(Path(ledger_path).resolve())
        return ref

    # governs == "initiation" — the weakest rung, declared Honor-system (R3-H2/R4-H1).
    if not (isinstance(priming_prompt_hash, str) and priming_prompt_hash.strip()):
        raise refuse(
            "kata_dispatch: governs='initiation' requires priming_prompt_hash — the rung's "
            "provenance (DESIGN §1.4, R4-H1)."
        )
    if cursor is None:
        raise refuse(
            "kata_dispatch: governs='initiation' reads the LIVE cursor for an open "
            "INITIATION/AUTHORING phase; no cursor was supplied. Call run_start() first."
        )
    state = phase_state(cursor)
    stronger = has_stronger_governor(cursor)
    if stronger is not None:
        raise refuse(
            f"kata_dispatch: initiation-rung exclusivity (RS-H3) — this run already records a "
            f"stronger governor at seq {stronger['seq']} ({stronger['governs']}:"
            f"{stronger['state']}). Mint under that governor instead.",
            deny_class=True,
        )
    if not any(key in INITIATION_PHASES for key in state["open"]):
        closed = [k for k in state["closed"] if k in INITIATION_PHASES]
        detail = (
            f"the {closed} phase(s) already CLOSED on this run"
            if closed
            else "no INITIATION or AUTHORING phase is open on this run"
        )
        raise refuse(
            f"kata_dispatch: initiation rung unmet — {detail}. The predicate reads an OPEN "
            "INITIATION or AUTHORING phase event on the live cursor (DESIGN §1.4).",
            deny_class=True,
        )
    return {
        "governs": "initiation",
        "ref": f"priming-prompt:{priming_prompt_hash}",
        "state": "open",
        "grade": grade,
    }


# --------------------------------------------------------------------------- §1.5 records


def dispatch_dir(kata_dir: str | Path) -> Path:
    """``<kata_dir>/dispatch/`` — the pending-record registry (DESIGN §1.5)."""
    return _safe_kata_dir(kata_dir) / DISPATCH_DIRNAME


def record_id(run_id: str, seq: int) -> str:
    """The record's identity: ``<runId>-<seq>`` (DESIGN §1.5)."""
    _kb.validate_run_id(run_id)
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
        raise ValueError(f"kata_dispatch: seq must be a non-negative int: {seq!r}")
    return f"{run_id}-{seq}"


def _guard_record_id(raw: str) -> str:
    """A record id is ``run-<utc>-<hex>-<seq>``; anything else never reaches a path."""
    if not isinstance(raw, str) or not re.fullmatch(r"run-\d{8}T\d{6}Z-[0-9a-f]+-\d+", raw):
        raise RecordClaimRefused(
            f"kata_dispatch: not a dispatch-record id (expected '<runId>-<seq>'): {raw!r}"
        )
    return raw


def record_path(kata_dir: str | Path, rid: str, *, consumed: bool = False) -> Path:
    """Path of a pending (or consumed) dispatch record."""
    base = dispatch_dir(kata_dir)
    if consumed:
        base = base / CONSUMED_DIRNAME
    return base / f"{_guard_record_id(rid)}.json"


def _write_json_atomic(target: Path, payload: dict) -> Path:
    """Write JSON via temp + ``os.replace``.  ``sort_keys=True`` (doctrine law 5)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return target


def brief_hash(brief: dict | str) -> str:
    """The record's ``briefHash``: sha256 over the brief's canonical JSON (or raw text).

    Canonical = ``sort_keys=True``, compact separators — so the same brief hashes the
    same on every machine (doctrine law 5).
    """
    if isinstance(brief, str):
        data = brief.encode("utf-8")
    else:
        data = json.dumps(brief, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _resolve_role_routing(
    role: str,
    *,
    platform: str | None,
    model: str | None,
    effort: str | None,
    roles_block: dict | None,
    confirmed_platforms: list[str] | None,
    host_platform: str,
    anchor: str | None,
    family: str | None,
) -> dict:
    """Resolve platform/model/effort for *role*, wiring ``kata_roles.resolve_roles``.

    Explicit arguments win; otherwise the config's ``roles`` block is resolved through
    the existing fail-closed resolver (unknown role / unconfirmed platform ⇒ raise), so
    the seam mint is the call site that resolver never had (SURFACE-MAP: "zero callers").
    """
    entry: dict = {}
    if roles_block is not None:
        from kata_roles import resolve_roles  # local import keeps the N-chain import list stable

        entry = resolve_roles(
            roles_block, confirmed_platforms, host_platform, anchor=anchor, family=family
        ).get(role, {})
    return {
        "platform": platform or entry.get("platform") or host_platform,
        "model": model if model is not None else entry.get("model"),
        "effort": effort if effort is not None else entry.get("effort"),
    }


def mint(
    *,
    governs: str,
    role: str,
    task_id: str,
    kata_dir: str | Path,
    plan_path: str | Path | None = None,
    ledger_path: str | Path | None = None,
    intent_path: str | Path | None = None,
    priming_prompt_hash: str | None = None,
    brief: dict | str | None = None,
    brief_digest: str | None = None,
    platform: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    roles_block: dict | None = None,
    confirmed_platforms: list[str] | None = None,
    host_platform: str = "claude",
    anchor: str | None = None,
    family: str | None = None,
    agent: str = SEAM_AGENT,
    parent_seq: int | None = None,
    now: datetime | None = None,
) -> dict:
    """Mint a dispatch record + the seam-authored SPAWN cursor line (DESIGN §1.3/§1.4/§1.5).

    ``governs`` is **required, keyword-only, with no default** — an omittable governor is
    the D136 silent-permissive class (R3-M4, inheriting BL-F01's rule verbatim).

    Order of acts, deliberately: validate the governor ⇒ resolve routing ⇒ write the
    PENDING record ⇒ append the SPAWN line.  The record lands first so a SPAWN line can
    never point at a missing record; a crash between the two leaves an orphan record with
    no cursor lineage, which is exactly what ``run_start``'s reaping pass detects
    (DESIGN §1.5 step 5).

    Returns the record dict plus ``recordId`` / ``recordPath`` / ``spawnSeq``.

    Raises
    ------
    MintRefused
        Unknown governor, unknown role, unmet governor state, no live cursor, or a
        closed run.  The exception names the park path (TM-B5): there is no legal path
        past a refuse-to-mint, so the caller ESCALATEs ``human-required`` and an
        unattended run parks the task.
    """
    kata = _safe_kata_dir(kata_dir)
    park = _park_path(kata, task_id)

    try:
        cursor = _kb.read_cursor(kata)
    except _kb.CursorError as exc:
        raise MintRefused(
            f"kata_dispatch: no readable cursor at {kata!s} ({exc}) — the seam mints only "
            "against a live run. Call run_start() first.",
            park_path=park, task_id=task_id,
        ) from exc

    if is_run_closed(cursor):
        raise MintRefused(
            f"kata_dispatch: run {cursor.run_id} is CLOSED (a terminal 'run-closed' PHASE "
            "line is recorded); nothing is legal on this cursor after it. Start a new run "
            "(run_start) or a loop-back.",
            park_path=park, task_id=task_id,
        )

    try:
        governed = check_governor(
            governs=governs, role=role, kata_dir=kata, plan_path=plan_path,
            ledger_path=ledger_path, intent_path=intent_path,
            priming_prompt_hash=priming_prompt_hash, cursor=cursor, task_id=task_id,
        )
    except MintRefused as exc:
        # DESIGN §1.8: every denial is a cursor DENY event.  Best-effort — a cursor that
        # cannot be written is not allowed to swallow the refusal itself.
        try:
            deny(
                kata, str(exc), legal_path=_legal_path_for(governs, role), task=task_id,
                agent=agent, now=now,
            )
        except SeamError:
            pass
        raise

    routing = _resolve_role_routing(
        role, platform=platform, model=model, effort=effort, roles_block=roles_block,
        confirmed_platforms=confirmed_platforms, host_platform=host_platform,
        anchor=anchor, family=family,
    )

    if brief_digest is None:
        if brief is None:
            raise MintRefused(
                "kata_dispatch: mint requires either brief= (hashed here) or brief_digest= "
                "— briefHash is a REQUIRED record field (DESIGN §1.5).",
                park_path=park, task_id=task_id,
            )
        brief_digest = brief_hash(brief)

    seq = _kb.next_seq(cursor)
    rid = record_id(cursor.run_id, seq)
    record = {
        # DESIGN §1.5 field list — all required unless marked.
        "runId": cursor.run_id,
        "taskId": task_id,
        "role": role,
        "platform": routing["platform"],
        "model": routing["model"],
        "effort": routing["effort"],
        "governs": governed["governs"],
        "governedRef": governed["ref"],
        "governedState": governed["state"],
        "governorGrade": governed["grade"],
        "briefHash": brief_digest,
        "mintedUtc": _utc(now),
        "seq": seq,
        # RESERVED for BL-N20 (our-own-agent-definition), unpopulated in v1 — the slot
        # exists so the field is not invented later at a different name.
        "agentDef": None,
        "recordId": rid,
        "schema": 1,
    }
    if "routedFrom" in governed:
        record["governedRoutedFrom"] = governed["routedFrom"]

    path = _write_json_atomic(record_path(kata, rid), record)

    msg = (
        f"mint role={role} governs={governed['governs']} state={governed['state']} "
        f"platform={record['platform']} model={record['model'] or 'inherit'} "
        f"grade={governed['grade']} record={rid}"
    )
    line = _kb.append_event(
        kata, agent, "SPAWN", task_id, msg, parent_seq=parent_seq, seq=seq, now=now
    )

    return {**record, "recordPath": str(path), "spawnSeq": line.seq}


def _legal_path_for(governs: str, role: str) -> str:
    """The legal path a DENY message names (DESIGN §1.8) — never a bare refusal."""
    if governs == "plan":
        return "freeze the PLAN (D169 freeze act), then mint again with governs='plan'"
    if governs == "ledger":
        return (
            "converge the grill ledger (the grill-close act writes status: converged), or "
            "mint under the rung this role's DESIGN §1.4 row names"
        )
    if governs == "intent":
        return "freeze INTENT.md (write_intent(..., freeze=True) at Phase 6), then mint again"
    if governs == "initiation":
        return (
            "open an INITIATION or AUTHORING phase on the live cursor and supply the "
            "priming-prompt hash — or, once a stronger governor is recorded, mint under it"
        )
    return f"mint through kata_dispatch.mint() with a governor in {sorted(GOVERNORS)}"


def claim_record(kata_dir: str | Path, rid: str) -> dict:
    """**The atomic single-use claim** — ``os.rename`` into ``consumed/`` (DESIGN §1.5, RS-H2).

    Consumption is an atomic claim, not a check-then-act: the record file is renamed
    into ``<kata_dir>/dispatch/consumed/``.  Two racing claimants both target the same
    SOURCE, so exactly one rename can succeed; every loser's rename fails and its
    validation fails with it ⇒ deny.  **Parallel-dispatch order-independence is ACHIEVED
    BY the claim, never assumed**, and ``fs_atomic``'s replace-only primitive is
    explicitly NOT the mechanism (a replace would let the loser silently overwrite the
    winner's claim — the exact opposite of single-use).

    Mark-consumed-and-RETAIN: the claimed record stays on disk under ``consumed/`` for
    lineage; only PRE-hook re-validation fails on it (R3-M1).

    Raises
    ------
    RecordClaimRefused
        Already consumed (naming the re-mint path — the retry-race message of pass-2
        low 11), never minted, or lost the race.
    """
    kata = _safe_kata_dir(kata_dir)
    pending = record_path(kata, rid)
    consumed = record_path(kata, rid, consumed=True)
    consumed.parent.mkdir(parents=True, exist_ok=True)

    try:
        os.rename(pending, consumed)
    except OSError as exc:
        # Loser of the race, a replay, or a record that never existed.  All three are the
        # same refusal, and the message names the ONE legal path out of the retry race.
        if consumed.exists():
            raise RecordClaimRefused(
                f"kata_dispatch: dispatch record {rid!r} is already CONSUMED — a record is "
                "single-use (the atomic claim is the replay control). A legitimate retry "
                "racing its own consumed record must RE-MINT: call kata_dispatch.mint() "
                "again and launch against the new record; never reuse a consumed one."
            ) from exc
        raise RecordClaimRefused(
            f"kata_dispatch: no pending dispatch record {rid!r} at {pending!s} ({exc}) — "
            "a launch without a minted record is denied; mint via kata_dispatch.mint()."
        ) from exc

    try:
        return json.loads(consumed.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecordClaimRefused(
            f"kata_dispatch: dispatch record {rid!r} was claimed but is unreadable ({exc}) — "
            "the claim stands (single-use); re-mint to dispatch."
        ) from exc


def validate_record(
    record: dict,
    *,
    kata_dir: str | Path,
    expected_brief_hash: str | None = None,
    expected_role: str | None = None,
    plan_path: str | Path | None = None,
    ledger_path: str | Path | None = None,
    intent_path: str | Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Re-run the engine validations against a record — **semantic, not existence** (TM-B4).

    A stale or hand-copied record from an earlier dispatch fails here, which is what
    keeps the T-04 staleness class dead.  Checks, in order:

    1. the record's ``runId`` is the LIVE run's,
    2. a SPAWN line at the record's ``seq`` exists on the cursor and names this record
       (the cursor-lineage check — a fabricated record has no matching lineage, S1),
    3. the role is in the closed enum (and matches ``expected_role`` when supplied),
    4. the governor state is STILL met (the predicate is re-run, not remembered),
    5. ``briefHash`` matches when the caller supplies the brief's digest.

    The ``mintedUtc`` window is reported (``expired`` / ``ageSeconds``) and is
    **advisory only** — DESIGN §1.5 step 4 / RS-M12: the atomic single-use claim is THE
    replay control, and wall-clock is never load-bearing.  Nothing here refuses on age.

    Returns a report dict; raises :class:`SeamError` on any hard failure.
    """
    kata = _safe_kata_dir(kata_dir)
    cursor = _kb.read_cursor(kata)

    if record.get("runId") != cursor.run_id:
        raise SeamError(
            f"kata_dispatch: record runId {record.get('runId')!r} is not the live run "
            f"{cursor.run_id!r} — a record from another run never validates (run-membership law)."
        )
    seq = record.get("seq")
    rid = record.get("recordId") or (record_id(cursor.run_id, seq) if isinstance(seq, int) else None)
    lineage = [
        ln for ln in cursor.lines
        if ln.type == "SPAWN" and ln.seq == seq and _spawn_fields(ln.msg).get("record") == rid
    ]
    if not lineage:
        raise SeamError(
            f"kata_dispatch: record {rid!r} has NO matching SPAWN line at seq {seq!r} on the "
            "live cursor — a record without cursor lineage is not a minted record."
        )
    role = record.get("role")
    if role not in ROLE_GROUPS:
        raise SeamError(f"kata_dispatch: record carries unknown role {role!r}.")
    if expected_role is not None and role != expected_role:
        raise SeamError(
            f"kata_dispatch: record role {role!r} does not match the launched role "
            f"{expected_role!r} — a record is bound to the dispatch it was minted for."
        )
    governed = check_governor(
        governs=record.get("governs", ""), role=role, kata_dir=kata,
        plan_path=plan_path if plan_path is not None else record.get("governedRef"),
        ledger_path=ledger_path if ledger_path is not None else record.get("governedRef"),
        intent_path=intent_path if intent_path is not None else record.get("governedRef"),
        priming_prompt_hash=str(record.get("governedRef", "")).removeprefix("priming-prompt:"),
        cursor=cursor, task_id=record.get("taskId"),
    )
    if expected_brief_hash is not None and record.get("briefHash") != expected_brief_hash:
        raise SeamError(
            "kata_dispatch: briefHash mismatch — the launched brief is not the brief this "
            "record was minted for (a hand-copied record fails exactly here)."
        )

    age = None
    try:
        minted = datetime.fromisoformat(str(record.get("mintedUtc")))
        age = ((now or datetime.now(UTC)).astimezone(UTC) - minted.astimezone(UTC)).total_seconds()
    except (TypeError, ValueError):
        age = None
    return {
        "ok": True,
        "recordId": rid,
        "runId": cursor.run_id,
        "governed": governed,
        "ageSeconds": age,
        # Advisory ONLY.  Never a refusal input (RS-M12).
        "expired": bool(age is not None and age > MINT_LAUNCH_WINDOW_S),
        "expiryIsAdvisory": True,
    }


def claim_and_validate(kata_dir: str | Path, rid: str, **kwargs) -> dict:
    """The pre-hook's one call: atomic claim, then the semantic re-validation (§1.5).

    Wired for the W8 hook; callable today by the conductor-invoked leg.  The claim
    happens FIRST so a losing racer is denied before any validation work.
    """
    record = claim_record(kata_dir, rid)
    report = validate_record(record, kata_dir=kata_dir, **kwargs)
    return {"record": record, "validation": report}


# --------------------------------------------------------------------------- cursor acts


#: Control characters + ANSI-range bytes (DESIGN §6.3 rendering law — the same class
#: ``kata_trail._CTRL_RE`` strips; kept local so this module owns its own guard).
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def _sanitize_msg(text: str) -> str:
    """Make arbitrary text safe as a cursor ``msg`` (DESIGN §6.3, applied at the writer).

    Three neutralisations, all deterministic: control/ANSI-range characters are stripped
    (a cursor line must never be able to repaint a fake receipt), the field separator
    ``|`` becomes ``/`` so a value cannot forge extra cursor fields, and the reserved
    ``" payload="`` token — which ``kata_board.format_line`` refuses outright — becomes
    ``" payload_"`` so a hostile refusal reason cannot turn a record into a crash.
    """
    return _CTRL_RE.sub("", str(text)).replace("|", "/").replace(_kb.PAYLOAD_TOKEN, " payload_")


def _fire_cadence(
    kata: Path,
    line_type: str,
    *,
    run_id: str,
    task: str,
    agent: str,
    repo_root: str | Path = ".",
    cursor_path: str | Path | None = None,
    now: datetime | None = None,
) -> dict | None:
    """Fire the trail snapshot cadence and RECORD its outcome on the cursor (D-17, R-M4).

    DESIGN §2.5: the cadence fires on every PHASE and VERDICT append — this is the call
    site that makes "durable at the moment they exist" live rather than test-only.
    ``kata_trail.snapshot_on_append`` performs the snapshot and returns a
    cursor-appendable record **including the skip case**; appending it is the seam's act,
    and this is that act.

    Compile decision (recorded — the DESIGN names no TYPE for a durability record): the
    record lands as a **seam-authored NOTE line carrying the record JSON as its payload**.
    The five seam TYPEs are each defined for something else (PHASE's msg grammar is
    closed; VERDICT is a judge verdict; DOWN is a child terminal; DENY is a refusal), and
    inventing a sixth would break the closed TYPE enum the W2 grammar pins.  NOTE is the
    grammar's free-form line and the agent field marks the seam as its writer.  A NOTE is
    not a cadence trigger, so recording a snapshot can never recurse.
    """
    record = _trail.snapshot_on_append(
        line_type, run_id=run_id, repo_root=str(repo_root), cursor_path=cursor_path
    )
    if record is None:
        return None
    cursor = _kb.read_cursor(kata)
    seq = _kb.next_seq(cursor)
    pointer = _kb.payload_pointer(run_id, seq)
    _kb.write_payload(kata, pointer, record)
    _kb.append_event(
        kata, agent, "NOTE", task, _sanitize_msg(_trail.format_record_line(record)),
        payload=pointer, seq=seq, now=now,
    )
    return record


def read_trail_records(kata_dir: str | Path) -> list[dict]:
    """Every durability record recorded on the cursor, in order.  Feeds ``derive_resilience``.

    Reads the payload JSON behind seam-authored NOTE lines and keeps the ones whose
    ``kind`` is a ``kata_trail`` record kind — so the declared resilience level is a
    **fold over recorded fact**, exactly as R-M4 requires, and never an assertion.
    """
    kata = _safe_kata_dir(kata_dir)
    try:
        cursor = _kb.read_cursor(kata)
    except _kb.CursorError:
        return []
    kinds = {_trail.RECORD_KIND_SNAPSHOT, _trail.RECORD_KIND_PUSH_RECEIPT}
    out: list[dict] = []
    for line in sorted(cursor.lines, key=lambda ln: (ln.seq, ln.pos)):
        if line.type != "NOTE" or not line.payload:
            continue
        try:
            data = json.loads(_kb.payload_path(kata, line.payload).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and data.get("kind") in kinds:
            out.append(data)
    return out


def phase(
    kata_dir: str | Path,
    msg: str,
    *,
    task: str = "run",
    agent: str = SEAM_AGENT,
    repo_root: str | Path = ".",
    cursor_path: str | Path | None = None,
    parent_seq: int | None = None,
    now: datetime | None = None,
) -> dict:
    """Append a seam-authored PHASE line (DESIGN §1.3, §2.3, §2.6) and fire the cadence.

    The msg grammar is ENFORCED (``open <PHASE> [k=v…] | close <PHASE> [k=v…] |
    run-closed [k=v…]``) over the closed phase vocabulary.  Additionally:

    * ``run-closed`` is **terminal** — nothing is legal on the cursor after it, and it
      may be written exactly once (DESIGN §2.6, R4 residual 3).  ``run_start``'s resume
      test reads it.
    * a ``close`` must match an open phase, and an ``open`` of an already-open phase is
      refused — a phase model that cannot be violated is what makes the initiation rung's
      predicate meaningful.
    * re-opening a CLOSED phase is a **recorded DENY-class event**; re-opening INITIATION
      on a run that already records a stronger governor is the RS-H3 case by name.

    Returns ``{"line", "phase", "snapshot"}`` — ``snapshot`` is the durability record the
    cadence produced (``committed`` or ``skipped``), both of which are recorded.
    """
    kata = _safe_kata_dir(kata_dir)
    cursor = _kb.read_cursor(kata)
    parsed = parse_phase_msg(msg)
    state = phase_state(cursor)

    def refuse(message: str, *, legal: str) -> PhaseRefused:
        try:
            if not state["runClosed"]:
                deny(kata, message, legal_path=legal, task=task, agent=agent, now=now)
        except SeamError:
            pass
        return PhaseRefused(f"{message}  Legal path: {legal}")

    if state["runClosed"]:
        raise PhaseRefused(
            f"kata_dispatch: run {cursor.run_id} is CLOSED — the terminal 'run-closed' PHASE "
            "line is recorded and NOTHING is legal on this cursor after it (DESIGN §2.6). "
            "Legal path: start a new run (run_start) or a loop-back."
        )

    if parsed["verb"] == _RUN_CLOSED:
        if state["open"]:
            raise refuse(
                f"kata_dispatch: refusing 'run-closed' while phases are still open: "
                f"{state['open']}.",
                legal="close every open phase first, then write the terminal run-closed line",
            )
    elif parsed["verb"] == "open":
        if parsed["key"] in state["open"]:
            raise refuse(
                f"kata_dispatch: phase {parsed['key']} is already OPEN on this run.",
                legal=f"close {parsed['key']} before opening it again",
            )
        if parsed["key"] in state["closed"]:
            stronger = has_stronger_governor(cursor)
            detail = (
                f" This run records a stronger governor ({stronger['governs']}:"
                f"{stronger['state']} at seq {stronger['seq']}) — re-opening "
                f"{parsed['key']} on it is the RS-H3 DENY-class event."
                if stronger and parsed["key"] in INITIATION_PHASES else ""
            )
            raise refuse(
                f"kata_dispatch: phase {parsed['key']} is already CLOSED on this run; "
                f"re-opening a closed phase is a DENY-class event.{detail}",
                legal="record a LOOP-BACK phase and start a new run, or open the phase the "
                      "run's position actually calls for",
            )
    elif parsed["key"] not in state["open"]:
        raise refuse(
            f"kata_dispatch: cannot close phase {parsed['key']} — it is not open on this run "
            f"(open: {state['open']}).",
            legal="open the phase before closing it",
        )

    line = _kb.append_event(
        kata, agent, "PHASE", task, msg, parent_seq=parent_seq, now=now
    )
    snapshot = _fire_cadence(
        kata, "PHASE", run_id=cursor.run_id, task=task, agent=agent,
        repo_root=repo_root, cursor_path=cursor_path, now=now,
    )
    return {"line": line, "phase": parsed, "snapshot": snapshot}


def deny(
    kata_dir: str | Path,
    reason: str,
    *,
    legal_path: str,
    task: str = "run",
    agent: str = SEAM_AGENT,
    parent_seq: int | None = None,
    now: datetime | None = None,
) -> _kb.CursorLine:
    """Append the seam/hook-authored DENY line, **naming the legal path** (DESIGN §1.8).

    "A record-less launch is DENIED by the hook with a message naming the legal path" —
    denial forces the legal path and needs no human, which is what makes it BBM-11
    compatible.  Every denial is a cursor DENY event; the presentation layer shows it.

    Refuses to write after the terminal ``run-closed`` line (§2.6 terminality).
    """
    kata = _safe_kata_dir(kata_dir)
    cursor = _kb.read_cursor(kata)
    if is_run_closed(cursor):
        raise SeamError(
            f"kata_dispatch: run {cursor.run_id} is CLOSED — no DENY line can be appended "
            "after the terminal 'run-closed' PHASE line."
        )
    msg = _sanitize_msg(f"deny {reason}").strip()
    msg = f"{msg} ;; legal path: {_sanitize_msg(legal_path).strip()}"
    return _kb.append_event(kata, agent, "DENY", task, msg, parent_seq=parent_seq, now=now)


def retry_race_deny_message(rid: str) -> str:
    """The pass-2-low-11 message: a retry racing its own consumed record names the re-mint.

    Exposed as a constant-shaped function so the W8 hook and the engine deny with the
    SAME words — "a denial caused by a legitimate retry racing its own consumed record
    names the re-mint path in the deny message".
    """
    return (
        f"dispatch record {rid} is already consumed (records are single-use — the atomic "
        "claim is the replay control); this is a legitimate retry racing its own record"
    )


RETRY_RACE_LEGAL_PATH = (
    "re-mint via kata_dispatch.mint() and relaunch against the NEW record; never reuse a "
    "consumed record"
)


# --------------------------------------------------------------------------- §1.6 capture


#: The ONE verdict line: ``VERDICT: <ENUM>``.  Strict — anchored, single space, and a
#: token shape that cannot swallow prose.  The per-judge enum table is enumerated at the
#: judge-contract-rewrite wave (R4 residual 4); pass ``allowed=`` to bind it here.
_VERDICT_LINE_RE = re.compile(r"VERDICT: ([A-Za-z][A-Za-z0-9_-]*)")


def _envelope_text(envelope) -> str:
    """Extract the tool-result ENVELOPE's text.  Never reaches into the body's structure."""
    if envelope is None:
        return ""
    if isinstance(envelope, str):
        return envelope
    if isinstance(envelope, dict):
        for key in ("text", "content", "result", "raw"):
            value = envelope.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, list) and value and isinstance(value[0], dict):
                first = value[0].get("text")
                if isinstance(first, str):
                    return first
        return ""
    return str(envelope)


def parse_verdict(envelope, *, allowed: frozenset[str] | set[str] | None = None) -> str | None:
    """**The ONE verdict parser, two callers** (DESIGN §1.6) — post-hook and engine capture.

    Strict ``fullmatch`` on **line 1 of the tool-result ENVELOPE**.  The body is NEVER
    scanned, so repo content, advice payloads, and diff hunks cannot forge a verdict: a
    ``VERDICT: PASS`` sitting on line 2, inside a code fence, or anywhere in the body
    returns ``None`` here, exactly like an envelope with no verdict at all.

    ``allowed`` binds the per-judge closed enum when the caller has one (that table is
    enumerated at the judge-contract-rewrite wave, R4 residual 4); a verdict outside it
    is a no-match, never a coercion.

    Returns the verdict token, or ``None``.  **No-match is the caller's refusal path
    (§5.3) — there is deliberately no body-scan fallback** (pass-2 low 14).
    """
    text = _envelope_text(envelope)
    if not text:
        return None
    line_one = text.split("\n", 1)[0].rstrip()
    match = _VERDICT_LINE_RE.fullmatch(line_one)
    if not match:
        return None
    verdict = match.group(1)
    if allowed is not None and verdict not in allowed:
        return None
    return verdict


def capture(
    envelope,
    rid: str,
    *,
    kata_dir: str | Path,
    kind: str = "verdict",
    task: str | None = None,
    evidence_pointers: list[str] | tuple[str, ...] = (),
    allowed: frozenset[str] | set[str] | None = None,
    reason: str | None = None,
    child_run_id: str | None = None,
    agent: str = SEAM_AGENT,
    repo_root: str | Path = ".",
    cursor_path: str | Path | None = None,
    now: datetime | None = None,
    source: str = "engine-by-conductor",
) -> dict:
    """Capture a judge/arm return envelope: parse the verdict, write the cursor record.

    Two line kinds (DESIGN §1.3): ``kind="verdict"`` writes the seam-authored VERDICT
    line + its REQUIRED payload (judges); ``kind="down"`` writes the parent-seam-authored
    DOWN line for a child run reaching a terminal state (§2.3 — children never write the
    parent's log).  Both go through the ONE parser: an arm returns a verdict-first
    envelope exactly like a judge does.

    The conductor-invoked leg is **declared Honor-system** (RS-M5): its input is
    conductor-supplied, and the returned ``grade`` says so.  A hook-invoked capture
    passes ``source="post-edge"``.

    After the append, the DESIGN §2.5 cadence fires and its outcome is recorded on the
    cursor (D-17) — this is where "durable at the moment they exist" becomes live.

    Raises
    ------
    CaptureRefused
        The record is absent, or line 1 carries no parseable verdict.  Both land on the
        absent-records refusal path (§5.3) — never a body scan.
    """
    if kind not in {"verdict", "down"}:
        raise ValueError(f"kata_dispatch: capture kind must be 'verdict' or 'down', got {kind!r}")
    kata = _safe_kata_dir(kata_dir)
    try:
        _guard_record_id(rid)
    except RecordClaimRefused as exc:
        raise CaptureRefused(f"{exc}  (DESIGN §5.3 absent-records refusal)") from exc

    record = None
    for candidate in (record_path(kata, rid, consumed=True), record_path(kata, rid)):
        if candidate.is_file():
            try:
                record = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CaptureRefused(
                    f"kata_dispatch: dispatch record {rid!r} is unreadable ({exc}) — the close "
                    "refuses on absent records (DESIGN §5.3); re-run the dispatch."
                ) from exc
            break
    if record is None:
        raise CaptureRefused(
            f"kata_dispatch: no dispatch record {rid!r} under {dispatch_dir(kata)!s} — a "
            "verdict without its minted record is an ABSENT RECORD, and the close refuses "
            "on absent records (DESIGN §5.3). Re-dispatch through mint()."
        )

    verdict = parse_verdict(envelope, allowed=allowed)
    if verdict is None:
        raise CaptureRefused(
            f"kata_dispatch: no parseable verdict on LINE 1 of the return envelope for record "
            f"{rid!r} (expected 'VERDICT: <ENUM>'"
            + (f", one of {sorted(allowed)}" if allowed else "")
            + "). The body is NEVER scanned — a body-embedded verdict is not a verdict "
            "(pass-2 low 14). This is the absent-records refusal path (DESIGN §5.3)."
        )

    grade = CAPTURE_POST_EDGE if source == "post-edge" else CAPTURE_ENGINE_BY_CONDUCTOR
    task_id = task or record.get("taskId") or "run"
    cursor = _kb.read_cursor(kata)
    payload = {
        # kata_board.validate_verdict_payload's four REQUIRED fields, plus provenance.
        "verdict": verdict,
        "evidencePointers": list(evidence_pointers),
        "judgeDispatchSeq": record["seq"],
        "runId": cursor.run_id,
        "recordId": rid,
        "role": record.get("role"),
        "taskId": record.get("taskId"),
        "capturedUtc": _utc(now),
        "captureGrade": grade,
        "captureSource": source,
    }
    if reason:
        payload["reason"] = reason
    if child_run_id:
        payload["childRunId"] = _kb.validate_run_id(child_run_id)

    if kind == "verdict":
        msg = f"verdict={verdict} role={record.get('role')} record={rid} capture={source}"
        line = _kb.append_verdict(
            kata, agent, task_id, msg, payload, parent_seq=record["seq"], now=now
        )
    else:
        payload["kind"] = "child-run-terminal"
        seq = _kb.next_seq(cursor)
        pointer = _kb.payload_pointer(cursor.run_id, seq)
        _kb.write_payload(kata, pointer, payload)
        msg = (
            f"down verdict={verdict} child={child_run_id or 'unknown'} record={rid} "
            f"reason={(reason or 'terminal').split()[0]}"
        )
        line = _kb.append_event(
            kata, agent, "DOWN", task_id, msg, parent_seq=record["seq"], payload=pointer,
            seq=seq, now=now,
        )

    snapshot = _fire_cadence(
        kata, line.type, run_id=cursor.run_id, task=task_id, agent=agent,
        repo_root=repo_root, cursor_path=cursor_path, now=now,
    )
    return {
        "verdict": verdict,
        "line": line,
        "payload": payload,
        "grade": grade,
        "snapshot": snapshot,
        "record": record,
    }


# --------------------------------------------------------------------------- §1.7 probes


def hook_path(repo_root: str | Path = ".") -> Path:
    """Where the W8 deny/capture hook lives once ``hook-activation`` lands."""
    return Path(repo_root).resolve().joinpath(*HOOK_RELPATH)


def hook_fingerprint(
    repo_root: str | Path = ".",
    *,
    expected_digest: str | None = None,
    path: str | Path | None = None,
) -> dict:
    """Probe the hook's integrity — **probed, never presumed** (DESIGN §8 S3, RS-H4).

    Honest pre-activation behaviour: the hook does not exist until PLAN wave 8, so this
    returns ``{"installed": False, "digest": None, "matches": None, "result": "no-result"}``
    and the enforcement declaration falls to **Dormant**.  This is a real probe returning
    an honest result, not a stub: point it at a hook file and it fingerprints it.

    ``matches`` is tri-state on purpose — ``None`` means "nothing to compare", which is
    NOT the same as False, and neither may ever read as enforcement.
    """
    target = Path(path).resolve() if path is not None else hook_path(repo_root)
    if not target.is_file():
        return {
            "installed": False, "path": str(target), "digest": None, "matches": None,
            "expectedDigest": expected_digest, "result": "no-result",
            "reason": "no hook installed (the deny/capture hook lands in PLAN wave 8, hook-activation)",
        }
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return {
        "installed": True, "path": str(target), "digest": digest,
        "expectedDigest": expected_digest,
        "matches": None if expected_digest is None else digest == expected_digest,
        "result": "fingerprinted",
    }


def deny_tripwire_probe(prober=None) -> dict:
    """Run the live deny-tripwire — a self-test dispatch that MUST be denied (RS-H4).

    ``prober() -> bool | dict`` is injectable: W8 wires the real self-test dispatch; a
    test injects a stub.  With no prober (today) the honest answer is **no result**, and
    ``derive_enforcement`` maps that to ``Dormant (pre-activation)`` — never inheriting a
    prior declaration (pass-2 high 2).  File presence proves nothing: a mid-session
    install reads present-but-inactive and a neutered hook reads present-and-green, which
    is exactly why the tripwire and the fingerprint are **jointly necessary**.
    """
    if prober is None:
        return {
            "result": "no-result", "denied": None,
            "reason": "no deny-tripwire prober wired (the hook lands in PLAN wave 8, hook-activation)",
        }
    try:
        outcome = prober()
    except Exception as exc:  # noqa: BLE001 — a crashing probe is a NO-RESULT, never a pass
        return {"result": "no-result", "denied": None, "reason": f"probe raised: {exc}"}
    if isinstance(outcome, dict):
        denied = outcome.get("denied")
        return {
            "result": "probed" if isinstance(denied, bool) else "no-result",
            "denied": denied if isinstance(denied, bool) else None,
            "reason": outcome.get("reason"),
        }
    if isinstance(outcome, bool):
        return {"result": "probed", "denied": outcome, "reason": None}
    return {"result": "no-result", "denied": None, "reason": f"probe returned {type(outcome).__name__}"}


def derive_enforcement(
    fingerprint: dict | None,
    tripwire: dict | None,
    *,
    bash_leg: bool = False,
    host_intercepts: bool = True,
) -> str:
    """DERIVE the enforcement Guardian grade from the probes (DESIGN §1.7 / §6.2 table).

    Never asserted, never inherited.  The rules, exactly:

    * host with no interception primitive ⇒ ``Honor-system (detection-only host)``;
    * tripwire returned no result, or was not denied ⇒ ``Dormant (pre-activation)``;
    * tripwire denied but the fingerprint does not match ⇒ ``Dormant`` (the script
      tripwire and the registration digest are **jointly necessary**);
    * both green, Bash leg only ⇒ ``Partially verified (bash-leg)``;
    * both green on the Agent-tool leg ⇒ ``Verified (intercepting)``.
    """
    if not host_intercepts:
        return ENFORCEMENT_DETECTION_ONLY
    tripwire = tripwire or {}
    if tripwire.get("result") != "probed" or tripwire.get("denied") is not True:
        return ENFORCEMENT_DORMANT
    if not (fingerprint or {}).get("matches"):
        return ENFORCEMENT_DORMANT
    return ENFORCEMENT_BASH_LEG if bash_leg else ENFORCEMENT_INTERCEPTING


def derive_capture(capture_edge_probe: dict | None = None) -> str:
    """DERIVE the capture-edge Guardian grade (DESIGN §1.7 / §6.2).

    A PostToolUse-class capture edge that probed green ⇒ ``Verified (post-edge)``.
    Anything else — including today's no-hook state — degrades to the legal engine path:
    ``Honor-system (engine-by-conductor)``.  Hookless capture is a DEGRADE, never a
    failure: the run closes by doing the legal act (R2-H3).
    """
    probe = capture_edge_probe or {}
    if probe.get("result") == "probed" and probe.get("captured") is True:
        return CAPTURE_POST_EDGE
    return CAPTURE_ENGINE_BY_CONDUCTOR


def _settings_hook_entry(settings: dict | None, filename: str) -> dict | None:
    """Find the host-settings entry registering *filename*, if any.  PURE."""
    if not isinstance(settings, dict):
        return None
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return None
    for entries in hooks.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for hook in entry.get("hooks", []) if isinstance(entry.get("hooks"), list) else []:
                command = hook.get("command") if isinstance(hook, dict) else None
                if isinstance(command, str) and filename in command:
                    return {"command": command, "digest": hook.get("digest")}
    return None


def config_settings_consistency(
    config: dict | None,
    settings: dict | None,
    *,
    fingerprint: dict | None = None,
    filename: str = HOOK_FILENAME,
) -> dict:
    """The TM-H2 config-vs-settings consistency check.  PURE fold over two dicts.

    "Settings drift is detected at seam init."  Four drift classes, each named:

    * ``settings-registers-absent-hook`` — settings point at a script that is not there;
    * ``hook-present-but-unregistered`` — the script exists but nothing invokes it;
    * ``hook-digest-mismatch`` — settings recorded a digest at install that no longer
      matches the file (the ``/adapters/claude/`` substring is identification, never
      verification — RS-M10);
    * ``config-declares-unregistered-hook`` — ``hooks.seamGuard`` is declared true in
      ``kata.config`` but no settings entry registers it.

    Both absent (today) is CONSISTENT — pre-activation is a state, not a defect.
    """
    fingerprint = fingerprint or {}
    entry = _settings_hook_entry(settings, filename)
    installed = bool(fingerprint.get("installed"))
    declared = bool(((config or {}).get("hooks") or {}).get("seamGuard")) if isinstance(config, dict) else False

    drift: list[str] = []
    if entry and not installed:
        drift.append("settings-registers-absent-hook")
    if installed and not entry:
        drift.append("hook-present-but-unregistered")
    if entry and entry.get("digest") and fingerprint.get("digest") and entry["digest"] != fingerprint["digest"]:
        drift.append("hook-digest-mismatch")
    if declared and not entry:
        drift.append("config-declares-unregistered-hook")
    return {
        "consistent": not drift,
        "drift": drift,
        "settingsRegistered": bool(entry),
        "hookInstalled": installed,
        "configDeclares": declared,
        "configKey": CONFIG_KEY_SEAM_GUARD,
    }


# --------------------------------------------------------------------------- §6.4 declaration


def format_run_start_declaration(*, enforcement: str, capture: str, resilience: str) -> str:
    """The MINIMAL run-start declaration that ships in the seam wave (DESIGN §6.4, R2-M1).

    Three plain-text lines — enforcement, capture, resilience — every value a Guardian
    term with its mode word **in parentheses only**, taken VERBATIM from the §6.2 table.
    A value outside those tables is refused: "no builder invention" is enforced here, not
    merely stated.  The full UX-grammar box lands in the presentation wave.
    """
    if enforcement not in ENFORCEMENT_VALUES:
        raise ValueError(
            f"kata_dispatch: enforcement value {enforcement!r} is not in the DESIGN §6.2 table "
            f"{sorted(ENFORCEMENT_VALUES)} — the Guardian scale is the ONLY trust vocabulary."
        )
    if capture not in CAPTURE_VALUES:
        raise ValueError(
            f"kata_dispatch: capture value {capture!r} is not in the DESIGN §6.2 table "
            f"{sorted(CAPTURE_VALUES)}."
        )
    if resilience not in set(_trail.RESILIENCE_DISPLAY.values()):
        raise ValueError(
            f"kata_dispatch: resilience value {resilience!r} is not in the DESIGN §6.2 table "
            f"{sorted(_trail.RESILIENCE_DISPLAY.values())}."
        )
    return (
        f"enforcement: {enforcement}\n"
        f"capture: {capture}\n"
        f"resilience: {resilience}"
    )


# --------------------------------------------------------------------------- §2.4 run_start


def run_marker_path(kata_dir: str | Path) -> Path:
    """``<kata_dir>/run-marker.json`` — the scope marker the W8 deny hook reads (RS-L5)."""
    return _safe_kata_dir(kata_dir) / RUN_MARKER_FILENAME


def read_run_marker(kata_dir: str | Path) -> dict | None:
    """Read the run marker, or ``None`` when absent/unreadable (the hook's scope read)."""
    try:
        return json.loads(run_marker_path(kata_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _has_spawn(cursor: _kb.Cursor, seq, rid) -> bool:
    """True iff a SPAWN line at *seq* names record *rid*.  PURE."""
    return any(
        ln.type == "SPAWN" and ln.seq == seq and _spawn_fields(ln.msg).get("record") == rid
        for ln in cursor.lines
    )


def _reap_orphans(kata: Path, cursor: _kb.Cursor | None) -> list[dict]:
    """Reap pending records with no matching cursor lineage (DESIGN §1.5 step 5, R2-M3).

    Registry enumeration, exactly as the DESIGN names it: every pending record under
    ``dispatch/`` whose ``(runId, seq)`` has no SPAWN line on the LIVE cursor is an
    orphan — a crash between the record write and the cursor append, or a record whose
    run has since been rotated away.  Orphans are MOVED to ``reaped/``, never deleted:
    lineage is evidence.
    """
    base = dispatch_dir(kata)
    if not base.is_dir():
        return []
    reaped: list[dict] = []
    for path in sorted(base.glob("*.json")):
        reason = None
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            record, reason = None, f"unreadable-record: {exc}"
        if reason is None:
            if cursor is None:
                reason = "no live cursor"
            elif record.get("runId") != cursor.run_id:
                reason = f"record runId {record.get('runId')} is not the live run {cursor.run_id}"
            elif not _has_spawn(cursor, record.get("seq"), record.get("recordId") or path.stem):
                reason = f"no SPAWN lineage at seq {record.get('seq')}"
        if reason is None:
            continue
        target = base / REAPED_DIRNAME / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(path, target)
        reaped.append({"recordId": path.stem, "reason": reason, "reapedTo": str(target)})
    return reaped


def run_start(
    kata_dir: str | Path,
    *,
    repo_root: str | Path = ".",
    force_new: bool = False,
    prev_run: str | None = None,
    parent_run: str | None = None,
    prev_segment: str | None = None,
    config: dict | None = None,
    settings: dict | None = None,
    expected_hook_digest: str | None = None,
    tripwire_prober=None,
    capture_edge_probe: dict | None = None,
    bash_leg: bool = False,
    host_intercepts: bool = True,
    now: datetime | None = None,
    entropy: str | None = None,
) -> dict:
    """Seam init: new-vs-resume, rotation, reaping, marker, probes, declaration (§1.3/§2.4).

    **New-run vs resume discrimination, mechanically** (R3-H1):

    * no live cursor, **or** the live cursor's run is CLOSED ⇒ NEW: rotate the cursor and
      mint a fresh ``runId`` (``kata_board.start_run``, which owns the atomic rotation);
    * a live cursor with an UNCLOSED run ⇒ RESUME: **ADOPT** the header's runId, reap
      orphan records, continue.  A resumed session NEVER re-mints, which is what keeps
      pre-crash gate artifacts valid evidence under the exact-runId rule;
    * ``force_new=True`` is the re-loop / loop-back case: those ALWAYS mint.

    **Torn rotation** (DESIGN §8 edge list): rotation is an atomic sequence (archive
    rename, then header write).  A cursor file that exists but carries no parseable
    header is a torn rotation and is REFUSED here, loudly — recovering it by guessing
    would fabricate run identity.  A zero-byte cursor is the benign half of the same
    tear: it is reported as ``tornRotation`` and the run starts fresh over it.

    The declaration (§6.4) is DERIVED from the probes, never asserted.  Pre-W8 the honest
    values are ``Dormant (pre-activation)`` / ``Honor-system (engine-by-conductor)`` /
    ``Partially verified (local)``.

    Returns a dict carrying ``runId``, ``mode``, ``rotated``, ``reaped``, ``hook``,
    ``tripwire``, ``enforcement``, ``capture``, ``resilience``, ``consistency``,
    ``tornRotation`` and the rendered ``declaration``.
    """
    kata = _safe_kata_dir(kata_dir)
    kata.mkdir(parents=True, exist_ok=True)
    cursor_file = _kb.cursor_path(kata)

    live: _kb.Cursor | None = None
    torn: str | None = None
    if cursor_file.exists():
        text = cursor_file.read_text(encoding="utf-8")
        if not text.strip():
            torn = "empty-cursor: a rotation archived the previous cursor but wrote no header"
        else:
            try:
                live = _kb.parse_cursor(text)
            except _kb.CursorError as exc:
                raise SeamError(
                    f"kata_dispatch: TORN ROTATION or corrupt cursor at {cursor_file!s} — "
                    f"{exc}. Rotation is an atomic sequence (archive rename, then header "
                    "write); a cursor with no parseable header cannot be recovered without "
                    "fabricating run identity. Move it aside by hand (the archives are "
                    "beside it) and re-run run_start()."
                ) from exc

    mode = "resume" if (live is not None and not force_new and not is_run_closed(live)) else "new"

    if mode == "new":
        header = _kb.start_run(
            kata,
            prev_run=prev_run if prev_run is not None else (live.run_id if live else None),
            parent_run=parent_run,
            prev_segment=prev_segment,
            now=now,
            entropy=entropy,
        )
        cursor = _kb.read_cursor(kata)
        rotated = live is not None
    else:
        header = live.header  # type: ignore[union-attr]
        cursor = live  # type: ignore[assignment]
        rotated = False

    reaped = _reap_orphans(kata, cursor)

    _write_json_atomic(run_marker_path(kata), {
        "schema": 1,
        "runId": header.run_id,
        "kataDir": str(kata),
        "mode": mode,
        "startedUtc": _utc(now),
    })

    fingerprint = hook_fingerprint(repo_root, expected_digest=expected_hook_digest)
    tripwire = deny_tripwire_probe(tripwire_prober)
    enforcement = derive_enforcement(
        fingerprint, tripwire, bash_leg=bash_leg, host_intercepts=host_intercepts
    )
    capture_grade = derive_capture(capture_edge_probe)
    consistency = config_settings_consistency(config, settings, fingerprint=fingerprint)
    resilience = _trail.derive_resilience(
        read_trail_records(kata), push_trail_configured=_trail.read_push_trail(config)
    )

    return {
        "runId": header.run_id,
        "mode": mode,
        "rotated": rotated,
        "adopted": mode == "resume",
        "prevRun": header.prev_run,
        "parentRun": header.parent_run,
        "reaped": reaped,
        "runMarker": str(run_marker_path(kata)),
        "tornRotation": torn,
        "hook": fingerprint,
        "tripwire": tripwire,
        "enforcement": enforcement,
        "capture": capture_grade,
        "resilience": resilience,
        "consistency": consistency,
        "declaration": format_run_start_declaration(
            enforcement=enforcement, capture=capture_grade, resilience=resilience["display"]
        ),
    }
