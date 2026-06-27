"""drift_gate.py — §5 behavioral drift-gate engine (v1).

Enforces the behavioral drift contract for P2b gated fix-application: every
test that was GREEN in the BEFORE run must stay GREEN in the AFTER run.  Any
green→RED transition outside the Allowed Exception List (AEL) = BLOCK.
Characterization snapshots must be byte-identical (nondeterminism scrubbed)
EXCEPT entries on the AEL.

§5 v1 LIMITATION — honest scope statement
------------------------------------------
This engine enforces BEHAVIORAL drift only.  The structural / public-surface
invariance layer (public-API diff = ∅ + AST-edit-script) is a FAST-FOLLOW,
NOT v1.  Do NOT claim "structure preserved" on the basis of this engine's v1
verdict alone.  The named seam ``structural_drift_verdict`` (below) marks the
fast-follow boundary; it does not enforce anything in v1.

Security posture
----------------
PURE — no subprocess, no eval, no exec.  This engine consumes test-result data
as plain dicts/strings and returns verdicts.  Operator test runs go through the
existing registered operator sink ``run_result.run_gate``; this engine never
spawns one.  Assertable by source scan (see test_drift_gate.py::TestExecSafety).

Public surfaces (cite-able by name per protocol/reuse-claims.md)
----------------------------------------------------------------
DEFAULT_SCRUB_PATTERNS          — tunable nondeterminism-scrub pattern list
structural_drift_verdict        — §5 v1 FAST-FOLLOW seam (NOT IMPLEMENTED)
parse_test_outcomes             — pure parse of verbose test-runner output
classify_transitions            — per-test transition classification
validate_allowed_exceptions     — AEL integrity gate (load-bearing safety control)
drift_verdict                   — §5 behavioral gate (composes the above)
scrub_nondeterminism            — scrub timestamps/hex/tmp/uuids before compare
snapshots_match                 — byte-compare after scrubbing
characterization_snapshot_verdict — snapshots byte-identical except AEL
defer_record                    — can't-fix-without-drift → DEFER record
emit_deferrals                  — write deferred records to JSON
build_drift_report              — per-finding drift proof dict
emit_drift_report               — write drift proof to .kata/drift/<id>.json
drift_schema                    — JSON schema for a drift report (single source of truth)
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Union


# ---------------------------------------------------------------------------
# §5 v1 FAST-FOLLOW SEAM — structural_drift_verdict (NOT IMPLEMENTED IN v1)
# ---------------------------------------------------------------------------
# The structural / public-surface invariance layer (public-API diff = ∅ +
# AST-edit-script) is a FAST-FOLLOW, NOT v1.  The function below is a
# clearly-named, non-executing stub that marks the seam.  It does NOT enforce
# structural drift; it raises NotImplementedError if called so callers get an
# explicit signal rather than a silent mis-verdict.
#
# When the fast-follow lands: implement the body, remove the raise, add tests,
# and update the docstring.  The name and signature are stable (cite-able).


def structural_drift_verdict(*args: object, **kwargs: object) -> dict:
    """§5 v1 LIMITATION — structural-drift enforcement is NOT IMPLEMENTED in v1.

    The structural / public-surface invariance layer (public-API diff = ∅ plus
    AST-edit-script = body-updates-only) is a FAST-FOLLOW.  This named seam
    does NOT enforce structural drift in v1.  Behavioral drift only is enforced
    by ``drift_verdict``.

    Full structural enforcement (public-API diff + AST-edit-script comparison)
    arrives with the fast-follow.  Do NOT claim "structure preserved" on the
    basis of v1 behavioral drift enforcement alone.

    Raises:
        NotImplementedError: always — this seam is not implemented in v1.
    """
    raise NotImplementedError(
        "structural_drift_verdict is a §5 v1 FAST-FOLLOW seam and is NOT "
        "implemented in v1.  Use drift_verdict for behavioral drift enforcement. "
        "Full structural enforcement (public-API diff = ∅ + AST-edit-script) "
        "arrives with the fast-follow.  Do not claim 'structure preserved' on "
        "the basis of v1 behavioral enforcement alone."
    )


# ---------------------------------------------------------------------------
# Nondeterminism-scrub patterns (TUNABLE — calibratable without re-freeze)
# ---------------------------------------------------------------------------

DEFAULT_SCRUB_PATTERNS: list[str] = [
    # ISO 8601 timestamps (with optional fractional seconds and timezone offset)
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?",
    # UUIDs (8-4-4-4-12 hex)
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
    # Object-repr memory addresses ONLY — the Python "<... at 0x...>" form.
    # NARROW ON PURPOSE: a BARE 0x... hex literal is NOT scrubbed, so real hex
    # values (flags, hashes, opcodes) are never masked.  (F2 defense-in-depth.)
    r"at 0x[0-9a-fA-F]+",
    # Epoch timestamps ONLY when contextually LABELED (a 10–13 digit run
    # immediately preceded by a time label).  NARROW ON PURPOSE: a bare 10–13
    # digit integer is NOT scrubbed, so real numeric values (balances, counts,
    # ids) are never masked.  Scoped (?i:...) flag — global (?i) mid-alternation
    # is a regex error on Python ≥3.11.  (F2 defense-in-depth.)
    r"(?i:timestamp|epoch|ts|time)[\"'\s:=]+\d{10,13}",
    # POSIX /tmp/ paths
    r"/tmp/[^\s]+",
    # Windows %TEMP% / AppData\Local\Temp paths
    r"[A-Za-z]:\\[^\\]+\\AppData\\Local\\Temp\\[^\s]+",
]

# Internal compiled regex built from DEFAULT_SCRUB_PATTERNS
_DEFAULT_SCRUB_RE = re.compile("|".join(DEFAULT_SCRUB_PATTERNS))

# Regex for parsing pytest verbose output lines:
# Matches: "<test_id> PASSED/FAILED  [ nn%]"
# test_id = path/to/file.py::TestClass::test_method (one or more :: segments)
_OUTCOME_LINE_RE = re.compile(
    r"^([\w][\w./\\-]*(?:::[\w\[\].,=+-]+)+)\s+(PASSED|FAILED)",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_test_outcomes(output_text: str) -> dict[str, str]:
    """Parse captured verbose test-runner output into a per-test outcome map.

    Consumes the text output of a pytest --verbose run and returns a dict
    mapping each test ID to ``"green"`` (PASSED) or ``"red"`` (FAILED).

    Pure string parsing only — no subprocess, no eval, no exec.  The *running*
    is done by the caller via the existing ``run_result.run_gate`` operator sink.

    Args:
        output_text: Combined stdout from a pytest --verbose run.

    Returns:
        ``{test_id: "green"|"red"}`` for each PASSED/FAILED line found.
        Tests that appear neither as PASSED nor FAILED are not included.
    """
    outcomes: dict[str, str] = {}
    for match in _OUTCOME_LINE_RE.finditer(output_text):
        test_id = match.group(1)
        status = match.group(2)
        outcomes[test_id] = "green" if status == "PASSED" else "red"
    return outcomes


def classify_transitions(
    before: dict[str, str],
    after: dict[str, str],
) -> dict[str, str]:
    """Classify per-test transitions between before-run and after-run outcomes.

    Args:
        before: ``{test_id: "green"|"red"}`` from the pre-fix run.
        after:  ``{test_id: "green"|"red"}`` from the post-fix run.

    Returns:
        ``{test_id: transition_class}`` where transition_class is one of:
        ``"green->green"`` / ``"green->red"`` / ``"red->green"`` / ``"red->red"``
        / ``"added"`` (only in after) / ``"removed"`` (only in before).
    """
    all_ids = set(before) | set(after)
    transitions: dict[str, str] = {}
    for tid in all_ids:
        if tid not in before:
            transitions[tid] = "added"
        elif tid not in after:
            transitions[tid] = "removed"
        else:
            b, a = before[tid], after[tid]
            if b == "green" and a == "green":
                transitions[tid] = "green->green"
            elif b == "green" and a == "red":
                transitions[tid] = "green->red"
            elif b == "red" and a == "green":
                transitions[tid] = "red->green"
            else:
                transitions[tid] = "red->red"
    return transitions


def validate_allowed_exceptions(
    allowed: list[str],
    before: dict[str, str],
) -> dict:
    """AEL integrity gate — the load-bearing safety control.

    Validates every entry in the Allowed Exception List (AEL) against the
    before-run outcomes.  An AEL entry is valid ONLY IF the test is:
      - present in ``before`` (known test), AND
      - RED in ``before`` (a genuinely failing test nominated to flip GREEN).

    An entry that is GREEN in ``before`` (or absent from ``before``) is
    REJECTED.  A green test can never be authorized to regress — if such an
    entry were accepted, a regression could be whitelisted.  The engine never
    infers or enlarges the AEL from after-results.

    Args:
        allowed: AEL — list of test IDs (trusted input from the fix manifest).
        before:  Before-run outcome map ``{test_id: "green"|"red"}``.

    Returns:
        ``{"valid": bool, "rejected": list[str]}``.
        ``valid`` is True only if ``rejected`` is empty.
    """
    rejected: list[str] = []
    for entry in allowed:
        if entry not in before or before[entry] != "red":
            rejected.append(entry)
    valid = len(rejected) == 0
    return {"valid": valid, "rejected": rejected}


def drift_verdict(
    before: dict[str, str],
    after: dict[str, str],
    *,
    allowed_exceptions: list[str],
) -> dict:
    """§5 behavioral drift gate — the core decision engine.

    Enforces the P2b behavioral drift contract:
      1. ``validate_allowed_exceptions`` first — invalid AEL ⇒ BLOCK immediately.
      2. Any ``green->red`` transition outside the AEL ⇒ BLOCK.
      3. Every AEL test must flip ``red->green`` — a still-RED nominee ⇒ BLOCK
         (the fix did not land, or a different test was nominated by mistake).
      4. PASS only when all baseline-green tests stayed green AND every AEL test
         flipped red→green.

    The engine NEVER infers the AEL from after-results and NEVER enlarges it.

    Args:
        before:             Before-run outcome map ``{test_id: "green"|"red"}``.
        after:              After-run outcome map ``{test_id: "green"|"red"}``.
        allowed_exceptions: AEL — trusted list of test IDs allowed to flip
                            red→green (from the orchestrator-owned fix manifest).

    Returns:
        ``{"verdict": "PASS"|"BLOCK", "blocking": list[str],
           "flipped": list[str], "reason": str}``.
    """
    blocking: list[str] = []
    reasons: list[str] = []

    # Step 1 — AEL integrity: reject any green-in-before or unknown entry
    ael_check = validate_allowed_exceptions(allowed_exceptions, before)
    if not ael_check["valid"]:
        blocking.extend(ael_check["rejected"])
        reasons.append(
            f"AEL rejected entries (green-in-before or unknown): {ael_check['rejected']}"
        )
        return {
            "verdict": "BLOCK",
            "blocking": blocking,
            "flipped": [],
            "reason": "; ".join(reasons),
        }

    # Step 2 — classify transitions and find unallowed green→red regressions
    transitions = classify_transitions(before, after)
    ael_set = set(allowed_exceptions)

    for tid, transition in transitions.items():
        if transition == "green->red":
            if tid not in ael_set:
                blocking.append(tid)
                reasons.append(f"unallowed green→red regression: {tid}")

    # Step 2b — fail-closed: every baseline-GREEN test must still be PRESENT in
    # `after`.  A green-in-before test that VANISHED (deleted/renamed, or a
    # pytest ERROR / collection-failure that parse_test_outcomes does not
    # capture as FAILED) is absent from `after` and would otherwise classify as
    # "removed" and slip through the green→red check — silently violating §5's
    # "every baseline-green test stays green".  Require set(before-green) ⊆
    # set(after); a vanished baseline-green test BLOCKS.  (A green-in-before test
    # can never be a valid AEL entry — the AEL must be red-in-before — so this
    # never conflicts with the AEL rules.)
    for gtid, status in before.items():
        if status == "green" and gtid not in after:
            blocking.append(gtid)
            reasons.append(f"baseline-green test vanished from after-run: {gtid}")

    # Step 3 — every AEL test must flip red→green (fix must have landed)
    flipped: list[str] = []
    for tid in allowed_exceptions:
        t = transitions.get(tid, "removed")
        if t == "red->green":
            flipped.append(tid)
        else:
            blocking.append(tid)
            reasons.append(f"AEL test did not flip red→green ({t!r}): {tid}")

    if blocking:
        return {
            "verdict": "BLOCK",
            "blocking": blocking,
            "flipped": flipped,
            "reason": "; ".join(reasons),
        }

    return {
        "verdict": "PASS",
        "blocking": [],
        "flipped": flipped,
        "reason": (
            "All baseline-green tests stayed green; "
            "all AEL tests flipped red→green."
        ),
    }


# ---------------------------------------------------------------------------
# Snapshot comparison
# ---------------------------------------------------------------------------


def scrub_nondeterminism(
    text: str,
    *,
    patterns: list[str] = DEFAULT_SCRUB_PATTERNS,
) -> str:
    """Scrub nondeterministic elements from *text* before byte-comparison.

    Replaces genuinely-nondeterministic spans (ISO-8601 datetimes, UUIDs,
    object-repr memory addresses, labeled epoch timestamps, temp paths) with a
    stable placeholder so that two snapshots that differ only in nondeterministic
    noise are considered equal.

    The default patterns are DELIBERATELY NARROW to their nondeterminism intent
    so they do NOT mask real value changes (F2 defense-in-depth):
      - only the Python object-repr ``at 0x...`` address form is scrubbed — a
        BARE ``0x...`` hex literal (a flag/hash/opcode) is left intact;
      - only a CONTEXTUALLY-LABELED epoch (``timestamp:``/``epoch:``/``ts:``/
        ``time:`` + 10–13 digits) is scrubbed — a bare large integer (a balance,
        count, or id) is left intact.
    A greedy ``0x[0-9a-fA-F]+`` / bare ``\\d{10,13}`` would make two genuinely
    different values compare equal, masking a real regression.

    The ``patterns`` list is TUNABLE per project — callers may extend or replace
    it without a re-freeze (DESIGN §5 / calibration note).

    Args:
        text:     The snapshot string to scrub.
        patterns: List of regex patterns to replace with ``"<scrubbed>"``.
                  Defaults to ``DEFAULT_SCRUB_PATTERNS``.

    Returns:
        The scrubbed string with all matched spans replaced by ``"<scrubbed>"``.
    """
    if patterns is DEFAULT_SCRUB_PATTERNS:
        compiled = _DEFAULT_SCRUB_RE
    elif not patterns:
        return text  # nothing to scrub
    else:
        compiled = re.compile("|".join(patterns))
    return compiled.sub("<scrubbed>", text)


def snapshots_match(
    before_snap: str,
    after_snap: str,
    *,
    scrub: bool = True,
) -> bool:
    """Byte-compare two snapshots, optionally scrubbing nondeterminism first.

    Args:
        before_snap: Snapshot text from the before-run.
        after_snap:  Snapshot text from the after-run.
        scrub:       If True (default), apply ``scrub_nondeterminism`` before
                     comparing so that timestamp/UUID/address noise is ignored.

    Returns:
        True if the snapshots are byte-identical after optional scrubbing.
    """
    if scrub:
        return scrub_nondeterminism(before_snap) == scrub_nondeterminism(after_snap)
    return before_snap == after_snap


def characterization_snapshot_verdict(
    before_snaps: dict[str, str],
    after_snaps: dict[str, str],
    allowed_exceptions: list[str],
) -> dict:
    """Check characterization snapshots: byte-identical (scrubbed) EXCEPT the AEL.

    For each snapshot key NOT in the AEL, the before and after snapshot must be
    byte-identical (after nondeterminism scrubbing).  AEL entries are exempt —
    the nominated test's snapshot is expected to change when the bug is fixed.

    Args:
        before_snaps:       ``{snapshot_key: text}`` from the before-run.
        after_snaps:        ``{snapshot_key: text}`` from the after-run.
        allowed_exceptions: AEL — snapshot keys exempt from the comparison.

    Returns:
        ``{"verdict": "PASS"|"BLOCK", "changed_outside_ael": list[str]}``.
    """
    ael_set = set(allowed_exceptions)
    changed_outside_ael: list[str] = []

    all_keys = set(before_snaps) | set(after_snaps)
    for key in all_keys:
        if key in ael_set:
            continue  # AEL entries are exempt from snapshot comparison
        before_snap = before_snaps.get(key, "")
        after_snap = after_snaps.get(key, "")
        if not snapshots_match(before_snap, after_snap):
            changed_outside_ael.append(key)

    if changed_outside_ael:
        return {
            "verdict": "BLOCK",
            "changed_outside_ael": sorted(changed_outside_ael),
        }
    return {
        "verdict": "PASS",
        "changed_outside_ael": [],
    }


# ---------------------------------------------------------------------------
# Deferred-fix records (LD9/DG-12)
# ---------------------------------------------------------------------------


def defer_record(finding: dict, reason: str) -> dict:
    """Build a can't-fix-without-drift → DEFER record for a single finding.

    Records a finding that cannot be fixed without causing behavioral drift.
    These records are written to ``.kata/deviations/deferred.json`` by
    ``emit_deferrals`` and consumed by the LD12 closeout report in P3.

    Args:
        finding: The finding dict (from findings.json, ``route=="auto-fix-eligible"``).
        reason:  Human-readable explanation of why the fix was deferred.

    Returns:
        A dict with keys: ``finding_id``, ``finding``, ``reason``, ``utc``.
    """
    finding_id = finding.get("id") or finding.get("locus") or "unknown"
    return {
        "finding_id": str(finding_id),
        "finding": finding,
        "reason": reason,
        "utc": datetime.now(tz=timezone.utc).isoformat(),
    }


def emit_deferrals(
    records: list[dict],
    path: Union[str, Path],
) -> None:
    """Write deferred-fix records as JSON to *path*.

    Creates parent directories if absent.  Overwrites any existing file.
    The output file is consumed by the LD12 closeout confidence report (P3)
    and is distinct from the P3 recommendations report.

    Args:
        records: List of dicts produced by ``defer_record``.
        path:    Destination path (e.g. ``.kata/deviations/deferred.json``).
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(records, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Drift report (per-finding proof → .kata/drift/<id>.json)
# ---------------------------------------------------------------------------


def drift_schema() -> dict:
    """Return the JSON schema for a drift report (single source of truth).

    All drift reports produced by ``build_drift_report`` / ``emit_drift_report``
    conform to this schema.  It is the canonical reference for the LD12 closeout
    report and for downstream consumers in P3.

    Returns:
        A JSON Schema (draft 2020-12) dict describing a drift report.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "DriftReport",
        "description": (
            "Per-finding behavioral drift proof produced by drift_gate.py (§5 v1). "
            "NOTE: §5 v1 LIMITATION — behavioral drift only; structural enforcement "
            "(public-API diff = ∅ + AST-edit-script) is a FAST-FOLLOW, NOT v1."
        ),
        "type": "object",
        "required": ["finding_id", "behavioral", "snapshot", "verdict", "utc"],
        "properties": {
            "finding_id": {
                "type": "string",
                "description": "ID of the finding this drift proof corresponds to.",
            },
            "behavioral": {
                "type": "object",
                "required": ["verdict", "blocking", "flipped", "reason"],
                "properties": {
                    "verdict": {
                        "type": "string",
                        "enum": ["PASS", "BLOCK"],
                        "description": "Behavioral drift verdict.",
                    },
                    "blocking": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Test IDs that caused a BLOCK verdict.",
                    },
                    "flipped": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "AEL test IDs that successfully flipped red→green.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Human-readable explanation of the verdict.",
                    },
                },
            },
            "snapshot": {
                "type": "object",
                "required": ["verdict", "changed_outside_ael"],
                "properties": {
                    "verdict": {
                        "type": "string",
                        "enum": ["PASS", "BLOCK"],
                        "description": "Snapshot drift verdict.",
                    },
                    "changed_outside_ael": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Snapshot keys that changed outside the AEL.",
                    },
                },
            },
            "verdict": {
                "type": "string",
                "enum": ["PASS", "BLOCK"],
                "description": "Overall drift verdict (PASS iff both behavioral and snapshot are PASS).",
            },
            "utc": {
                "type": "string",
                "description": "ISO-8601 UTC timestamp when this report was produced.",
            },
        },
        "additionalProperties": False,
    }


def build_drift_report(
    finding: dict,
    behavioral: dict,
    snapshot: dict,
) -> dict:
    """Build a per-finding drift proof dict from the gate sub-verdicts.

    The overall verdict is PASS iff both ``behavioral["verdict"]`` and
    ``snapshot["verdict"]`` are ``"PASS"``.

    NOTE: §5 v1 LIMITATION — this report covers behavioral drift only.
    Structural enforcement (public-API diff = ∅ + AST-edit-script) is a
    FAST-FOLLOW and is NOT reflected here.  Do not claim "structure preserved"
    on the basis of this report alone.

    Args:
        finding:    The finding dict (provides the ``finding_id``).
        behavioral: Verdict dict from ``drift_verdict``.
        snapshot:   Verdict dict from ``characterization_snapshot_verdict``.

    Returns:
        A drift report dict conforming to ``drift_schema()``.
    """
    overall = (
        "PASS"
        if behavioral["verdict"] == "PASS" and snapshot["verdict"] == "PASS"
        else "BLOCK"
    )
    finding_id = finding.get("id") or finding.get("locus") or "unknown"
    return {
        "finding_id": str(finding_id),
        "behavioral": behavioral,
        "snapshot": snapshot,
        "verdict": overall,
        "utc": datetime.now(tz=timezone.utc).isoformat(),
    }


def emit_drift_report(
    report: dict,
    path: Union[str, Path],
) -> None:
    """Write a drift report as JSON to *path*.

    Creates parent directories if absent (e.g. ``.kata/drift/``).  Overwrites
    any existing file.  The report feeds the LD12 regression proof in P3.

    Args:
        report: Dict produced by ``build_drift_report``.
        path:   Destination path (e.g. ``.kata/drift/<finding_id>.json``).
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2), encoding="utf-8")
