"""debug_report.py — LD12 debug-run closeout report-assembly engine (P3, Slice A).

Pure, deterministic, mutation-proof ASSEMBLY of the LD12 closeout confidence
report DATA MODEL from the real P1/P2 artifact shapes.  It builds:

  1. a per-module confidence map (assessed / low_confidence / skipped),
  2. one deviation -> fix -> pinning-test traceable row per finding,
  3. the regression + security proof rollup (drift PASS/BLOCK + suite-green +
     mutation non-vacuous + the REAL Snyk before/after verdicts),
  4. the carried-through (skill-authored) recommendations + offered follow-ons.

It TRANSCRIBES the artifacts' own (already-honest) verdicts and labels; it
confers none.  It neither asserts structure-preservation nor re-derives
confidence.  The skill (kata-debrief) adds the plain-language honesty wording.

LD12 honesty integrity (engine-pinned, mutation-covered)
--------------------------------------------------------
* Behavioral-only.  ``build_proof_rollup`` carries the behavioral-only
  limitation flag (sourced from ``drift_gate.drift_schema()``'s own
  description).  The report NEVER claims "structure preserved" on the basis of
  the v1 behavioral drift gate.
* Heuristic confidence.  ``build_confidence_map`` tags every entry
  ``heuristic: true`` and uses the LD5 ``low_cap`` (sourced from
  ``deviation.DEFAULT_THRESHOLDS``) to classify force-LOW / sparse modules as
  ``low_confidence``; modules with no FM are ``skipped`` — never silently
  "assessed".  No calibration is implied.
* n=0 live.  ``debug_report_schema()``'s description states that Debug Mode has
  never run end-to-end on a real repository (seeded-fixture proof only).
* Real Snyk, not fabricated.  ``build_proof_rollup`` rolls up the REAL
  before/after Snyk verdicts that Slice W persists to ``.kata/snyk/<id>.json``
  (RESULT.json carries no Snyk field).  A fix with no obtainable before-scan is
  rolled up ``available: false`` — never as "clean".

Security posture
----------------
PURE — no subprocess, no eval, no exec, no shell.  This engine consumes JSON
artifacts via ``json.load`` / plain-dict assembly and writes JSON.  It spawns no
subprocess and calls no ``eval``/``exec``.  Assertable by source scan (see
test_debug_report.py::TestExecSafety).  It registers no new execution sink.

Public surfaces (cite-able by name per protocol/reuse-claims.md)
---------------------------------------------------------------
debug_report_schema    — JSON schema (single source of truth) for the LD12 report
snyk_report_schema     — JSON schema (single source of truth) for .kata/snyk/<id>.json
finding_id             — the SAME join-key derivation as drift_gate.defer_record
build_confidence_map   — per-module assessed / low_confidence / skipped map
build_deviation_table  — one deviation -> fix -> pinning-test row per finding
build_proof_rollup     — regression + security proof (drift + suite + mutation + Snyk)
build_debug_report     — compose the full LD12 data model
emit_debug_report      — write the report to .kata/debug/closeout.json
load_debug_report      — read the report back
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

import deviation

# ---------------------------------------------------------------------------
# LD5 low_cap — single source of truth is deviation.DEFAULT_THRESHOLDS
# ---------------------------------------------------------------------------
# An FM whose heuristic confidence is at or below this cap is force-LOW / sparse
# equivalent and renders as ``low_confidence`` (never silently "assessed").
_LOW_CAP: float = deviation.DEFAULT_THRESHOLDS["low_cap"]


# ---------------------------------------------------------------------------
# §5 / LD5 / n=0 honesty note strings (fixed; carried into the schema + model)
# ---------------------------------------------------------------------------

_BEHAVIORAL_ONLY_NOTE: str = (
    "§5 v1 LIMITATION: this report rolls up BEHAVIORAL drift only "
    "(baseline-green stays green; characterization snapshots stable except the "
    "AEL). The structural / public-surface invariance layer (public-API "
    "diff = ∅ + AST-edit-script) is a FAST-FOLLOW, NOT v1. This report says "
    "'behavior preserved (behavioral drift gate)'; it NEVER claims "
    "'structure preserved' on the basis of the v1 gate."
)

_CONFIDENCE_HEURISTIC_NOTE: str = (
    "LD5 v1: the per-module confidence map is a HEURISTIC "
    "(C = w1·MSAS + w2·(1−entropy) + w3·StructuralPrior, force-LOW for sparse "
    "signal) — it is uncalibrated and not verbalized. The map is labeled "
    "'heuristic (v1, uncalibrated)'; force-LOW / sparse modules render as "
    "low_confidence and modules with no function model render as skipped."
)

_LIVE_RUN_NOTE: str = (
    "n=0 live: Debug Mode has NEVER run end-to-end on a real repository. This "
    "report is proven on seeded fixtures only; no real-repo run is implied or "
    "claimed."
)

# The behavioral-only limitation is sourced from drift_gate's own schema note,
# resolved lazily (kept here verbatim so the engine carries it without a hard
# import dependency at module load for the schema text).
_LIMITATION_SOURCE: str = "drift_gate.drift_schema"


# ---------------------------------------------------------------------------
# finding_id — the SINGLE join-key derivation (identical to drift_gate)
# ---------------------------------------------------------------------------


def finding_id(finding: dict) -> str:
    """Derive the canonical join key for a finding (the SAME rule everywhere).

    Identical to ``drift_gate.defer_record`` / ``drift_gate.build_drift_report``:
    ``finding.get("id") or finding.get("locus") or "unknown"``.  Encoding this
    once and reusing it for every artifact join (findings -> .kata/drift ->
    .kata/fix_manifest -> .kata/snyk) means the deviation table can never
    silently mis-join on a divergent key (MINOR 2).

    Args:
        finding: A finding dict (from findings.json).

    Returns:
        The finding's join key as a string.
    """
    return str(finding.get("id") or finding.get("locus") or "unknown")


# ---------------------------------------------------------------------------
# JSON schemas (single source of truth)
# ---------------------------------------------------------------------------


def debug_report_schema() -> dict:
    """Return the JSON schema for the LD12 closeout report (single source of truth).

    The ``description`` carries the fixed §5 behavioral-only, LD5
    heuristic-confidence, and n=0-live honesty notes verbatim, so the honesty is
    pinned at the schema and cannot be silently dropped.

    Returns:
        A JSON Schema (draft 2020-12) dict describing the LD12 report.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "DebugCloseoutReport",
        "description": (
            "LD12 debug-run closeout confidence report data model produced by "
            "debug_report.py (P3). It TRANSCRIBES the P1/P2 artifacts' own "
            "verdicts and labels; it confers none. HONESTY (engine-pinned): "
            + _BEHAVIORAL_ONLY_NOTE
            + " "
            + _CONFIDENCE_HEURISTIC_NOTE
            + " "
            + _LIVE_RUN_NOTE
        ),
        "type": "object",
        "required": [
            "confidence_map",
            "deviation_table",
            "proof_rollup",
            "recommendations",
            "offered_followups",
            "honesty",
            "utc",
        ],
        "properties": {
            "confidence_map": {
                "type": "object",
                "description": (
                    "Per-module classification: assessed / low_confidence / "
                    "skipped. Every entry tagged heuristic:true (LD5 v1)."
                ),
            },
            "deviation_table": {
                "type": "array",
                "items": {"type": "object"},
                "description": (
                    "One deviation -> fix -> pinning-test row per finding "
                    "(DESIGN §6)."
                ),
            },
            "proof_rollup": {
                "type": "object",
                "description": (
                    "Regression + security proof: drift PASS/BLOCK, suite-green, "
                    "mutation non-vacuous, and the REAL Snyk before/after."
                ),
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "object"},
                "description": (
                    "LD3 recommendations list (skill-authored; carried through "
                    "unchanged)."
                ),
            },
            "offered_followups": {
                "type": "object",
                "description": (
                    "Offered follow-on version-up / sprint handoff "
                    "(skill-authored; carried through unchanged)."
                ),
            },
            "honesty": {
                "type": "object",
                "required": [
                    "behavioral_only",
                    "confidence_heuristic",
                    "live_run",
                ],
                "properties": {
                    "behavioral_only": {"type": "boolean"},
                    "confidence_heuristic": {"type": "boolean"},
                    "live_run": {"type": "boolean"},
                },
                "description": (
                    "The three pinned honesty flags: behavioral-only drift, "
                    "heuristic (uncalibrated) confidence, and n=0 live run."
                ),
            },
            "utc": {
                "type": "string",
                "description": "ISO-8601 UTC timestamp when the report was built.",
            },
        },
        "additionalProperties": True,
    }


def snyk_report_schema() -> dict:
    """Return the JSON schema for a per-fix Snyk artifact (single source of truth).

    This is the shape of ``.kata/snyk/<finding_id>.json`` — the artifact Slice W
    writes (the fix loop's existing Snyk MCP call) and this engine reads.  The
    shape is owned HERE (Slice A); W writes conforming JSON; A reads it.

    Shape::

        {finding_id, before: {verdict, findingCount},
                     after:  {verdict, findingCount},
         newFindings, available, utc}

    where ``newFindings = max(0, after.findingCount − before.findingCount)`` and
    ``available: false`` records honestly that a meaningful before-scan was not
    obtainable for this fix (no fabrication).

    Returns:
        A JSON Schema (draft 2020-12) dict describing the Snyk artifact.
    """
    state = {
        "type": "object",
        "required": ["verdict", "findingCount"],
        "properties": {
            "verdict": {
                "type": "string",
                "description": "The Snyk MCP verdict for this state.",
            },
            "findingCount": {
                "type": "integer",
                "description": "Number of Snyk findings for this state.",
            },
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "SnykFixReport",
        "description": (
            "Per-fix Snyk before/after verdict persisted to "
            ".kata/snyk/<finding_id>.json by Slice W (the fix loop's existing "
            "Snyk MCP call). The REAL before/after states of the pre-fix and "
            "fixed worktree. available:false records honestly that a meaningful "
            "before-scan was not obtainable (no fabrication)."
        ),
        "type": "object",
        "required": ["finding_id", "before", "after", "newFindings", "available"],
        "properties": {
            "finding_id": {
                "type": "string",
                "description": (
                    "The finding this Snyk proof corresponds to (same "
                    "finding_id derivation as everywhere else)."
                ),
            },
            "before": state,
            "after": state,
            "newFindings": {
                "type": "integer",
                "minimum": 0,
                "description": "max(0, after.findingCount − before.findingCount).",
            },
            "available": {
                "type": "boolean",
                "description": (
                    "False iff a meaningful before-scan was not obtainable for "
                    "this fix (honest; never fabricated)."
                ),
            },
            "utc": {
                "type": "string",
                "description": "ISO-8601 UTC timestamp of the Snyk scans.",
            },
        },
        "additionalProperties": True,
    }


# ---------------------------------------------------------------------------
# Confidence map (assessed / low_confidence / skipped)
# ---------------------------------------------------------------------------


def build_confidence_map(
    function_models: list[dict],
    *,
    graph_modules: Union[list[str], None] = None,
) -> dict:
    """Classify each module as assessed / low_confidence / skipped (LD5 v1 heuristic).

    Honest rules:
      * an FM whose ``confidence`` is at or below the LD5 ``low_cap`` (force-LOW /
        sparse-signal equivalent), or whose confidence is missing, =>
        ``low_confidence``;
      * a ``graph_modules`` entry with no FM => ``skipped``;
      * otherwise => ``assessed``.

    Every entry is tagged ``"heuristic": True`` (LD5 v1, uncalibrated) — the map
    NEVER implies calibration.

    Args:
        function_models: List of function_model dicts (``module`` + ``confidence``;
                         conforms to ``function_model.function_model_schema()``).
        graph_modules:   Optional module inventory (e.g. the graph node set). Any
                         module here with no FM is classified ``skipped``.

    Returns:
        ``{module: {"classification", "confidence", "heuristic", ...}}``.
    """
    fm_by_module: dict = {}
    for fm in function_models or []:
        # MINOR 4: skip a malformed (non-dict) record — fail honest, don't crash.
        if not isinstance(fm, dict):
            continue
        fm_by_module[fm.get("module")] = fm

    cmap: dict = {}
    for module, fm in fm_by_module.items():
        confidence = fm.get("confidence")
        # MINOR 3: a missing OR non-numeric confidence is fail-honest low_confidence
        # (a bool is NOT a number here).  Short-circuit so the <= compare is only
        # reached for a genuine number — never a TypeError on a str/None.
        is_number = isinstance(confidence, (int, float)) and not isinstance(confidence, bool)
        entry = {
            "classification": "assessed",
            "confidence": confidence,
            "heuristic": True,
        }
        if not is_number or confidence <= _LOW_CAP:
            entry["classification"] = "low_confidence"
            entry["forced_low"] = True
        cmap[module] = entry

    for module in graph_modules or []:
        if module not in fm_by_module:
            cmap[module] = {
                "classification": "skipped",
                "confidence": None,
                "heuristic": True,
            }

    return cmap


# ---------------------------------------------------------------------------
# Deviation -> fix -> pinning-test table
# ---------------------------------------------------------------------------


def _index_by_finding_id(records: Union[list, None]) -> dict:
    """Index artifact records by their stored ``finding_id`` field.

    The drift report / fix manifest / deferral records each carry a
    ``finding_id`` field that was itself derived upstream by the SAME
    ``finding.get("id") or finding.get("locus")`` rule (drift_gate), so indexing
    by that stored field joins correctly against ``finding_id(finding)``.
    """
    idx: dict = {}
    for rec in records or []:
        # MINOR 4: skip a malformed (non-dict) artifact record — fail honest.
        if not isinstance(rec, dict):
            continue
        key = str(rec.get("finding_id") or "unknown")
        idx[key] = rec
    return idx


def build_deviation_table(
    findings: list[dict],
    drift_reports: Union[list[dict], None],
    fix_manifests: Union[list[dict], None],
    deferrals: Union[list[dict], None],
) -> list[dict]:
    """Build one deviation -> fix -> pinning-test row per finding (DESIGN §6).

    Joins each finding to its drift proof (``verdict`` + ``flipped`` AEL ids =
    the pinning tests), its fix manifest (``characterization_files`` = the
    left-behind suite), and its deferral record (``applied`` vs ``deferred`` +
    ``reason``).  Every join uses ``finding_id(finding)`` so a locus-only finding
    still joins to the artifacts keyed by that locus (no silent miss).

    Args:
        findings:      Routed findings (from ``deviation.load_findings``).
        drift_reports: ``.kata/drift/<id>.json`` dicts (``drift_gate.drift_schema``).
        fix_manifests: ``.kata/fix_manifest/<id>.json`` dicts (kata-characterize).
        deferrals:     ``deferred.json`` records (``drift_gate.defer_record``).

    Returns:
        A list of row dicts, one per finding.
    """
    drift_idx = _index_by_finding_id(drift_reports)
    fix_idx = _index_by_finding_id(fix_manifests)
    defer_idx = _index_by_finding_id(deferrals)

    # MINOR 4: drop malformed (non-dict) findings up front — fail honest.
    valid_findings = [f for f in (findings or []) if isinstance(f, dict)]

    # MAJOR 2: count how many findings derive each finding_id.  A finding_id that
    # is shared by >1 finding (e.g. two findings both lacking id+locus → "unknown")
    # is AMBIGUOUS: attaching the single drift/fix/deferral record keyed on that id
    # to either row would be a guess and could cross-attribute one finding's proof
    # to another.  Such rows get NO artifact join (applied stays false).
    fid_counts: dict = {}
    for finding in valid_findings:
        key = finding_id(finding)
        fid_counts[key] = fid_counts.get(key, 0) + 1

    table: list[dict] = []
    for finding in valid_findings:
        fid = finding_id(finding)
        ambiguous = fid_counts.get(fid, 0) > 1
        # No cross-join for ambiguous ids — refuse to guess which finding owns the proof.
        drift = None if ambiguous else drift_idx.get(fid)
        fix = None if ambiguous else fix_idx.get(fid)
        deferred = None if ambiguous else defer_idx.get(fid)

        route = finding.get("route")
        # MAJOR 2: fix-evidence (the applied-fix CLAIM) is gated on the finding's
        # OWN route being auto-fix-eligible.  A research/defer/human finding must
        # NEVER render as a proven applied fix, even if a drift proof is keyed to
        # its id.  pinning_tests / characterization_files / applied are all gated.
        is_auto_fix = route == "auto-fix-eligible"
        behavioral = (drift or {}).get("behavioral") or {}
        pinning_tests = list(behavioral.get("flipped") or []) if is_auto_fix else []
        characterization_files = (
            list((fix or {}).get("characterization_files") or []) if is_auto_fix else []
        )

        row = {
            "finding_id": fid,
            "module": finding.get("module"),
            "locus": finding.get("locus"),
            "route": route,
            "drift_verdict": (drift or {}).get("verdict") if is_auto_fix else None,
            "pinning_tests": pinning_tests,
            "characterization_files": characterization_files,
            "applied": False,
            "deferred": deferred is not None,
            "reason": (deferred or {}).get("reason"),
            "ambiguous": ambiguous,
        }
        if is_auto_fix and drift is not None and drift.get("verdict") == "PASS":
            row["applied"] = True
            row["fix_proven"] = True
        table.append(row)

    return table


# ---------------------------------------------------------------------------
# Regression + security proof rollup
# ---------------------------------------------------------------------------


def _as_count(value: object) -> Union[int, None]:
    """Return *value* as a non-bool int, else None (missing/malformed count)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _snyk_rollup(snyk_reports: Union[list[dict], None]) -> dict:
    """Roll up the REAL Snyk before/after verdicts (honest about unavailability).

    A report with ``available: false`` is rolled up as unavailable — never as
    "clean".  ``newFindings`` is summed only over AVAILABLE reports.

    MAJOR 1 (regression-masking defense): the stored ``newFindings`` field is
    NOT trusted.  ``snyk_report_schema()`` DEFINES
    ``newFindings = max(0, after.findingCount − before.findingCount)``, so when a
    report is available and both findingCounts are present we RECOMPUTE the
    derived value and use ``effective_new = max(stored, derived)``.  A stored
    value LOWER than the derived value can never lower the result — a real
    regression can never be masked by a too-low (or fabricated) prose
    ``newFindings``.  An available report with a MISSING/malformed count fails
    honest: it is recorded in ``countMissing`` and the rollup is NOT clean.
    """
    new_findings = 0
    unavailable: list[str] = []
    count_missing: list[str] = []
    per_fix: list[dict] = []
    valid = [r for r in (snyk_reports or []) if isinstance(r, dict)]  # MINOR 4
    for rec in valid:
        rid = str(rec.get("finding_id") or "unknown")
        available = bool(rec.get("available", False))

        before = rec.get("before") if isinstance(rec.get("before"), dict) else {}
        after = rec.get("after") if isinstance(rec.get("after"), dict) else {}
        before_count = _as_count(before.get("findingCount"))
        after_count = _as_count(after.get("findingCount"))
        stored_new = _as_count(rec.get("newFindings")) or 0
        counts_present = before_count is not None and after_count is not None

        # Default to the stored value; recompute + take the max when we can, so a
        # too-low stored value can never mask a real regression (MAJOR 1).
        effective_new = stored_new
        derived = None
        if counts_present:
            derived = max(0, after_count - before_count)
            effective_new = max(stored_new, derived)

        per_fix.append(
            {
                "finding_id": rid,
                "before": rec.get("before"),
                "after": rec.get("after"),
                "newFindings": effective_new,
                "available": available,
            }
        )
        if not available:
            unavailable.append(rid)
            continue
        if not counts_present:
            count_missing.append(rid)
        new_findings += effective_new

    all_available = len(unavailable) == 0
    counts_ok = len(count_missing) == 0
    # Clean ONLY when every report is available, every count is present, and no
    # new findings were introduced — fail honest on any gap.
    snyk_clean = all_available and counts_ok and new_findings == 0
    return {
        "newFindings": new_findings,
        "available": all_available,
        "unavailable": unavailable,
        "countMissing": count_missing,
        "clean": snyk_clean,
        "per_fix": per_fix,
        "reportCount": len(valid),
    }


def build_proof_rollup(
    drift_reports: Union[list[dict], None],
    result_json: dict,
    mutation_json: dict,
    snyk_reports: Union[list[dict], None],
) -> dict:
    """Roll up the LD12 regression + security proof.

    Composes: drift PASS/BLOCK counts; suite-green from ``RESULT.json``
    (exit code 0 and no failures); ``allNonVacuous`` from ``mutation.json``; and
    the REAL Snyk before/after verdicts + ``newFindings`` from
    ``.kata/snyk/*.json`` (NOT a RESULT.json Snyk field — RESULT.json carries
    none).  An ``available:false`` Snyk artifact is rolled up honestly as
    unavailable, never as "clean".  Carries the behavioral-only limitation flag.

    Args:
        drift_reports: ``.kata/drift/<id>.json`` dicts.
        result_json:   The parsed ``RESULT.json`` (``run_result.build_result``).
        mutation_json: The parsed ``mutation.json`` (``gate_emit`` payload).
        snyk_reports:  ``.kata/snyk/<id>.json`` dicts (Slice W; this engine's shape).

    Returns:
        The proof rollup dict.
    """
    drift_pass = 0
    drift_block = 0
    for rep in drift_reports or []:
        if not isinstance(rep, dict):  # MINOR 4: skip malformed record
            continue
        if rep.get("verdict") == "PASS":
            drift_pass += 1
        elif rep.get("verdict") == "BLOCK":
            drift_block += 1

    result = result_json or {}
    suite_green = result.get("exitCode") == 0 and result.get("failed", 0) == 0

    mutation = mutation_json or {}
    all_non_vacuous = bool(mutation.get("allNonVacuous"))

    rollup = {
        "drift": {
            "pass": drift_pass,
            "block": drift_block,
            "total": drift_pass + drift_block,
        },
        "suite_green": suite_green,
        "allNonVacuous": all_non_vacuous,
        "snyk": _snyk_rollup(snyk_reports),
        "behavioral_only": False,
        "behavioral_only_note": _BEHAVIORAL_ONLY_NOTE,
    }
    # §5 v1 honesty pin: the drift proofs rolled up here are BEHAVIORAL-only
    # (sourced from drift_gate.drift_schema()'s own limitation note). Never
    # claim "structure preserved" on the basis of this rollup.
    rollup["behavioral_only"] = True
    rollup["limitation_source"] = _LIMITATION_SOURCE
    return rollup


# ---------------------------------------------------------------------------
# Compose the full LD12 data model
# ---------------------------------------------------------------------------


def build_debug_report(
    confidence_map: dict,
    deviation_table: list[dict],
    proof_rollup: dict,
    *,
    recommendations: list[dict],
    offered_followups: dict,
) -> dict:
    """Compose the full LD12 report data model conforming to ``debug_report_schema()``.

    ``recommendations`` (LD3) and ``offered_followups`` are SKILL-authored inputs
    that the engine carries through UNCHANGED — the engine authors neither.

    Args:
        confidence_map:    From ``build_confidence_map``.
        deviation_table:   From ``build_deviation_table``.
        proof_rollup:      From ``build_proof_rollup``.
        recommendations:   Skill-authored LD3 recommendations list.
        offered_followups: Skill-authored offered version-up / sprint handoff.

    Returns:
        The full report dict.
    """
    return {
        "schema": "debug_report/v1",
        "confidence_map": confidence_map,
        "deviation_table": deviation_table,
        "proof_rollup": proof_rollup,
        "recommendations": recommendations,
        "offered_followups": offered_followups,
        "honesty": {
            "behavioral_only": True,
            "confidence_heuristic": True,
            "live_run": False,
            "behavioral_only_note": _BEHAVIORAL_ONLY_NOTE,
            "confidence_heuristic_note": _CONFIDENCE_HEURISTIC_NOTE,
            "live_run_note": _LIVE_RUN_NOTE,
        },
        "utc": datetime.now(tz=timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# I/O — emit / load the report (.kata/debug/closeout.json)
# ---------------------------------------------------------------------------


def emit_debug_report(report: dict, path: Union[str, Path]) -> None:
    """Write the LD12 report as JSON to *path* (e.g. ``.kata/debug/closeout.json``).

    Creates parent directories if absent.  Overwrites any existing file.

    Args:
        report: Dict produced by ``build_debug_report``.
        path:   Destination path.
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def load_debug_report(path: Union[str, Path]) -> dict:
    """Load an LD12 report dict from *path*.

    Args:
        path: Path to a JSON file previously written by ``emit_debug_report``.

    Returns:
        The parsed report dict.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))
