"""validation_report.py — pure findings engine for kata-validate (Slice 1).

Deterministic, mutation-proof assembly of the kata-validate validation report.
Provides the Finding schema, severity mapping, markdown table renderer, JSON
round-trip I/O, and the known-bad tripwire corpus guard.

PURE — stdlib only, no subprocess, no eval, no exec, no shell, no network.
``..``-guarded path writes (CWE-23, mirrors grounding_gate._safe_path and
kata_board._safe_path).

Public surfaces (cite-able by name per protocol/reuse-claims.md)
----------------------------------------------------------------
finding_schema         — JSON schema for a single Finding (single source of truth)
report_schema          — JSON schema for a Report{passed, findings[]}
finding_id             — stable join key (matches debug_report.finding_id precedent)
severity_of            — SARIF band mapping (behavior_changing => error)
render_table           — severity-ranked markdown table; explicit N/A rows (R4 guard)
emit_findings          — write .kata/validation/findings.json (``..``-guarded)
load_findings          — read the round-trip JSON back
compute_passed         — default-FAIL verdict (error/HOLD => False, N/A/info => not-fail)
tripwire_corpus        — load the known-bad fixture findings
assert_tripwire_flagged — raise ValueError when findings show no error (leniency guard)

Security posture
----------------
PURE — no subprocess, no eval, no exec, no shell.  This engine consumes and
writes JSON via json.load / json.dumps.  Path writes use _safe_path() to block
``..`` traversal (CWE-23) before any filesystem sink is reached.
Assertable by source scan (see test_validation_report.py::TestExecSafety).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23) — mirrors grounding_gate._safe_path / kata_board._safe_path
# ---------------------------------------------------------------------------


def _safe_path(raw: Union[str, Path]) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied path, then resolve.

    Blocks any ``..`` segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree, while still allowing the
    absolute and nested-relative paths the operator legitimately targets.
    Sanitizes tainted input at the boundary before any filesystem sink.

    Mirrors the identical guard in grounding_gate._safe_path and
    kata_board._safe_path (keep them in sync).
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"validation_report: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


# ---------------------------------------------------------------------------
# Finding schema (single source of truth)
# ---------------------------------------------------------------------------


def finding_schema() -> dict:
    """Return the JSON schema for a single Finding (single source of truth).

    Severity follows SARIF (error / warning / info).
    ``behavior_changing: True`` mandates severity == "error" (DESIGN §6 band rule:
    "fixing it changes behavior => error").
    ``hold: True`` causes compute_passed to fail regardless of severity.

    Returns:
        A JSON Schema dict (draft 2020-12) describing a Finding.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Finding",
        "description": (
            "A single validation finding produced by the kata-validate mini-loop. "
            "severity follows SARIF (error/warning/info). "
            "behavior_changing: True => severity MUST be error "
            "(fixing it changes behavior — DESIGN §6 band rule). "
            "hold: True => compute_passed returns False regardless of severity."
        ),
        "type": "object",
        "required": ["severity", "leg", "message"],
        "properties": {
            "id": {
                "type": ["string", "null"],
                "description": "Stable caller-assigned id (preferred join key for finding_id).",
            },
            "severity": {
                "type": "string",
                "enum": ["error", "warning", "info"],
                "description": "SARIF severity band.",
            },
            "leg": {
                "type": "string",
                "description": "Validator leg: grounding | review | slop | score | na.",
            },
            "location": {
                "type": ["string", "null"],
                "description": "File:line or other location reference (fallback join key).",
            },
            "message": {
                "type": "string",
                "description": "One-line human-readable message (the table cell content).",
            },
            "rule": {
                "type": ["string", "null"],
                "description": "Rule or heuristic name (e.g. 'slop/G2-vague-filler').",
            },
            "suggested_fix": {
                "type": ["string", "null"],
                "description": "Optional suggested fix (human-gated; writer applies on approval).",
            },
            "behavior_changing": {
                "type": "boolean",
                "default": False,
                "description": (
                    "True if fixing this finding changes observable behavior. "
                    "When True, severity_of() MUST return 'error'."
                ),
            },
            "hold": {
                "type": "boolean",
                "default": False,
                "description": (
                    "True if this finding is a HOLD (DESIGN §10-2). "
                    "compute_passed returns False when any finding has hold=True, "
                    "regardless of severity."
                ),
            },
        },
        "additionalProperties": True,
    }


def report_schema() -> dict:
    """Return the JSON schema for a Report{passed, findings[]} (single source of truth).

    ``passed`` defaults False (default-FAIL invariant, DESIGN §2/§10-2).
    ``findings[]`` is the severity-ranked list rendered by the writer (DESIGN §6).

    Returns:
        A JSON Schema dict (draft 2020-12) describing a Report.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Report",
        "description": (
            "Validation mini-loop report. passed defaults False (default-FAIL, "
            "DESIGN §2/§10-2). findings[] is the severity-ranked list. "
            "passed becomes True ONLY when every dispatched critic returns clean "
            "AND the tripwire fired correctly (compute_passed with tripwire_ok=True)."
        ),
        "type": "object",
        "required": ["passed", "findings"],
        "properties": {
            "passed": {
                "type": "boolean",
                "default": False,
                "description": "Default False. True only when every leg clears and tripwire_ok.",
            },
            "findings": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Severity-ranked list of Finding dicts.",
            },
            "utc": {
                "type": "string",
                "description": "ISO-8601 UTC timestamp when the report was built.",
            },
        },
        "additionalProperties": True,
    }


# ---------------------------------------------------------------------------
# finding_id — stable join key (matches debug_report.finding_id precedent)
# ---------------------------------------------------------------------------


def finding_id(finding: dict) -> str:
    """Derive the canonical join key for a finding.

    Algorithm: ``id`` → ``locus``/``location`` fallback → ``"unknown"``.
    Matches the ``debug_report.finding_id`` precedent exactly
    (``finding.get("id") or finding.get("locus") or "unknown"``) with the
    addition of ``location`` as a fallback — the validation_report Finding shape
    uses ``location`` rather than ``locus``.  NO hashing.

    Encoding this once and reusing it ensures every artifact join (findings →
    .kata/validation/findings.json) uses the same key and cannot silently mis-join.

    Args:
        finding: A Finding dict.

    Returns:
        The finding's canonical join key as a string.
    """
    return str(
        finding.get("id")
        or finding.get("locus")
        or finding.get("location")
        or "unknown"
    )


# ---------------------------------------------------------------------------
# severity_of — SARIF band mapping
# ---------------------------------------------------------------------------

# Band normalization map (all-lowercase keys; severity_of normalizes input before lookup)
_BAND_MAP: dict[str, str] = {
    # SARIF pass-through
    "error": "error",
    "warning": "warning",
    "info": "info",
    # GATE-VERDICT tokens — LOCKED §10-2 / kata-slop-check L2: these are gate verdicts,
    # NOT generic SARIF severity levels, so as severity TOKENS they MUST fail (error band).
    # SLOP-DETECTED ⇒ NEEDS_WORK regardless of critical/major/minor (severity informs
    # remediation priority, not gate status). REJECT/ESCALATE/HOLD likewise fail.
    "blocker": "error",
    "critical": "error",
    "reject": "error",
    "escalate": "error",
    "fail": "error",
    "slop-detected": "error",
    "needs_work": "error",
    "needs-work": "error",
    "hold": "error",
    # generic SARIF severity LEVELS (defensible warning/info; the conductor stamps
    # hold:true on normal-band slop findings so they fail via the hold path)
    "warn": "warning",
    "major": "warning",
    "caution": "warning",
    # info-band synonyms
    "minor": "info",
    "note": "info",
    "na": "info",
    "n/a": "info",
}


def severity_of(finding: dict) -> str:
    """Map a finding to a SARIF severity band.

    Band rule (DESIGN §6): ``behavior_changing: True`` → ``"error"``
    (fixing it changes observable behavior).  Overrides any other field.

    Then: maps BLOCKER/MAJOR/MINOR + slop critical/major/minor to
    error/warning/info.  If the ``severity`` field is already a SARIF value,
    it passes through unchanged.  Defaults to ``"info"`` for unknown bands.

    Args:
        finding: A Finding dict (may contain severity, band, behavior_changing).

    Returns:
        One of ``"error"``, ``"warning"``, or ``"info"``.
    """
    # behavior_changing => error, always (no override possible)
    if finding.get("behavior_changing"):
        return "error"
    raw = finding.get("severity") or finding.get("band") or "info"
    return _BAND_MAP.get(str(raw).strip().lower(), "info")


# ---------------------------------------------------------------------------
# render_table — severity-ranked markdown table with explicit N/A rows
# ---------------------------------------------------------------------------

_SEVERITY_ORDER: dict[str, int] = {"error": 0, "warning": 1, "info": 2}


def render_table(findings: list[dict], na_legs: list[str]) -> str:
    """Render a severity-ranked markdown table of findings.

    One row per finding, ordered: severity-first (error → warning → info),
    then by stable ``finding_id()`` within each severity band.

    R4 render guard (DESIGN §6, LOCKED): each leg in ``na_legs`` receives an
    explicit ``info`` row ("N/A — no plan to conform to" for the ``score`` leg;
    "N/A — leg not selected" for all others).  ``render_table`` NEVER silently
    omits a leg — a skipped conformance leg can NEVER read as a clean PASS.

    NO HTML in output.

    Args:
        findings: List of Finding dicts (from validation runs).
        na_legs:  List of leg names that were N/A / skipped (not run).
                  The caller decides which legs are N/A; typically the ``score``
                  leg when no plan was supplied (DESIGN §4d).

    Returns:
        Markdown table string (header + separator + one data row per finding/N/A).
    """
    # Build explicit N/A rows for each skipped leg (R4 guard)
    na_rows: list[dict] = []
    for leg in na_legs:
        msg = (
            "N/A — no plan to conform to"
            if leg == "score"
            else "N/A — leg not selected"
        )
        na_rows.append(
            {
                "id": f"na-{leg}",
                "severity": "info",
                "leg": leg,
                "location": None,
                "message": msg,
                "rule": "na-guard",
                "behavior_changing": False,
                "hold": False,
            }
        )

    all_rows: list[dict] = list(findings) + na_rows

    def _sort_key(f: dict) -> tuple[int, str]:
        sev = severity_of(f)
        return (_SEVERITY_ORDER.get(sev, 99), finding_id(f))

    sorted_rows = sorted(all_rows, key=_sort_key)

    lines: list[str] = [
        "| severity | finding_id | location | message |",
        "|---|---|---|---|",
    ]
    for f in sorted_rows:
        sev = severity_of(f)
        fid = finding_id(f)
        loc = str(f.get("location") or "—")
        # Escape pipe characters in message to preserve markdown table structure
        msg = str(f.get("message") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {sev} | {fid} | {loc} | {msg} |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# emit_findings / load_findings — JSON round-trip (.kata/validation/findings.json)
# ---------------------------------------------------------------------------


def emit_findings(path: Union[str, Path], report: dict) -> None:
    """Write the validation report to *path* as JSON.

    Intended for ``.kata/validation/findings.json`` — the machine source of
    truth (the markdown table is a view of it, DESIGN §6).

    Path write uses ``_safe_path()`` to block ``..`` traversal (CWE-23,
    mirrors grounding_gate.write_grounding and kata_board.write_state).
    Creates parent directories if absent.  Overwrites any existing file.

    Args:
        path:   Destination path (e.g. ``.kata/validation/findings.json``).
        report: Dict produced by the conductor (must conform to report_schema()).
    """
    dest = _safe_path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def load_findings(path: Union[str, Path]) -> dict:
    """Load a validation report dict from *path* (round-trip with emit_findings).

    Args:
        path: Path to a JSON file previously written by ``emit_findings``.

    Returns:
        The parsed report dict.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# compute_passed — default-FAIL verdict
# ---------------------------------------------------------------------------


def compute_passed(
    findings: list[dict],
    tripwire_ok: bool = True,
) -> bool:
    """Return True only when the validation run is fully clean.

    Default-FAIL (DESIGN §2/§10-2): starts False; returns True ONLY when:
    - ``tripwire_ok`` is True (the tripwire self-check passed),
    - no finding has severity ``"error"`` (or maps to "error" via severity_of),
    - no finding has ``hold: True``.

    N/A / ``info`` rows do NOT trip this — an explicit N/A row for the ``score``
    leg is informational only and never counts as a failure.

    Args:
        findings:    List of Finding dicts from the validation run.
        tripwire_ok: True if the tripwire self-check confirmed the validator
                     can catch known-bad content (DESIGN §7-i, §10-2).
                     Default True (caller passes False when tripwire failed).

    Returns:
        True if all conditions clear; False otherwise.
    """
    if not tripwire_ok:
        return False
    for f in findings:
        if not isinstance(f, dict):
            continue
        if severity_of(f) == "error":
            return False
        if f.get("hold"):
            return False
    return True


# ---------------------------------------------------------------------------
# Tripwire corpus — known-bad fixture guard (DESIGN §7-i)
# ---------------------------------------------------------------------------

_TRIPWIRE_DIR: Path = (
    Path(__file__).resolve().parent
    / "tests"
    / "fixtures"
    / "validation_tripwire"
)


def tripwire_corpus() -> list[dict]:
    """Return the list of known-bad fixture findings from the tripwire directory.

    Loads all ``.json`` files from ``tools/tests/fixtures/validation_tripwire/``.
    Each file is a single Finding dict or a list of Finding dicts.  Filesystem
    coupling is minimal and explicit — no glob recursion, no dynamic discovery.

    The corpus defines what "bad" looks like: the validator MUST produce at least
    one error-severity finding when run against these known-bad payloads.

    Returns:
        List of Finding dicts representing the known-bad corpus.
    """
    findings: list[dict] = []
    if not _TRIPWIRE_DIR.exists():
        return findings
    for p in sorted(_TRIPWIRE_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list):
                findings.extend([f for f in data if isinstance(f, dict)])
            elif isinstance(data, dict):
                findings.append(data)
        except (json.JSONDecodeError, OSError):
            pass
    return findings


def assert_tripwire_flagged(findings: list[dict]) -> None:
    """Assert that the validator produced at least one error on the known-bad corpus.

    DESIGN §7-i: the conductor runs the validators against the known-bad corpus
    (``tripwire_corpus()``) first.  If the validator ever produces no error-severity
    findings, it is broken — it silently passes known-bad content (leniency failure).

    Raises ``ValueError`` when:
    - ``findings`` contains no error-severity finding, OR
    - the tripwire corpus itself is empty (the guard is unconfigured).

    A clean tripwire MUST trigger a breakthrough-alert to the human
    (``protocol/narration.md:69-92``) — never a silent pass.

    Args:
        findings: Finding dicts produced by a validation run over the corpus
                  (or the corpus findings themselves for unit-test purposes).

    Raises:
        ValueError: If the validator shows leniency (no error found) or the corpus
                    is unconfigured (empty).
    """
    corpus = tripwire_corpus()
    if not corpus:
        raise ValueError(
            "assert_tripwire_flagged: tripwire corpus is empty — "
            "cannot assert the validator caught known-bad content. "
            "Add at least one error-severity finding to "
            "tools/tests/fixtures/validation_tripwire/."
        )
    has_error = any(
        severity_of(f) == "error" or bool(f.get("hold"))
        for f in findings
        if isinstance(f, dict)
    )
    if not has_error:
        raise ValueError(
            "Tripwire FAILED: the validator produced no error-severity findings "
            "on the known-bad corpus. The validator may be silently passing "
            "everything (leniency failure — DESIGN §7-i). "
            "STOP and issue a breakthrough-alert to the human."
        )
