"""test_recurrence_detect.py — TDD suite for tools/recurrence_detect.py (T2 Slice S1).

Strategy: default-FAIL (tests written to the frozen S1 acceptance). All tests are
pure except tmp_path writes and the mutation proofs (which spawn a real subprocess
via mutation_run.prove_non_vacuous and always restore the source).

Coverage map
------------
distinct_run_counts:
    distinct run_id counting (2 share run_id → 1; 2 distinct → 2), ts-fallback,
    mixed run_id/ts.
cluster_severity_tier:
    BLOCKER short-circuit, MAJOR, MINOR.
actionable_recurrences:
    distinct-run control (3 rows/1 run_id → NOT actionable; 3 distinct → actionable),
    legacy ts-fallback (3 rows/1 ts → NOT; 3 distinct ts → actionable),
    severity short-circuit (BLOCKER@2 actionable; MAJOR@2 not),
    handled-skip (proposed/guarded excluded), off-vocabulary flag, result shape.
read_handled / append_handled / validate_handled / handled_schema:
    append-only, ValueError on '..'/malformed, False on I/O failure, tolerant read.
detect_from_paths:
    reads both files + returns actionable; absent files ⇒ [].
exec-safety:
    source scan — no eval/exec/subprocess/shell; ast-parseable.
Mutation proofs (spawn subprocess via prove_non_vacuous):
    (a1) distinct-run identity add, (a2) run_id→ts fallback,
    (b) severity-aware threshold selection, (c) handled-aware skip,
    (d) >= threshold comparison, (e) the '..' guard in append_handled.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest


_SOURCE = (Path(__file__).resolve().parent.parent / "recurrence_detect.py")


# ---------------------------------------------------------------------------
# Synthetic fixture builders
# ---------------------------------------------------------------------------

def _miss(skill="kata-evaluate", cls="exec-injection", severity="MAJOR",
          ts="2026-06-27T00:00:00Z", **overrides) -> dict:
    """Build a minimal miss dict the engine reads (skill/class/severity/ts/run_id)."""
    base = {
        "responsible_skill": skill,
        "failure_class": cls,
        "severity": severity,
        "ts": ts,
    }
    base.update(overrides)
    return base


def _handled(skill="kata-evaluate", cls="exec-injection", status="proposed",
             **overrides) -> dict:
    """Build a valid handled-sidecar record."""
    base = {
        "ts": "2026-06-27T00:00:00Z",
        "key": f"{skill}::{cls}",
        "responsible_skill": skill,
        "failure_class": cls,
        "status": status,
        "proposal_ref": f".planning/specs/recurrence-hardening/PROPOSAL-{cls}.md",
        "guard_ref": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# distinct_run_counts
# ---------------------------------------------------------------------------

def test_distinct_run_counts_shared_run_id_counts_one():
    """Two misses sharing a run_id count as ONE run."""
    import recurrence_detect as rd

    misses = [
        _miss(run_id="run-A", ts="2026-01-01T00:00:00Z"),
        _miss(run_id="run-A", ts="2026-01-02T00:00:00Z"),
    ]
    counts = rd.distinct_run_counts(misses)
    assert counts["kata-evaluate::exec-injection"] == 1


def test_distinct_run_counts_distinct_run_id_counts_two():
    """Two misses with distinct run_id count as TWO runs."""
    import recurrence_detect as rd

    misses = [
        _miss(run_id="run-A", ts="2026-01-01T00:00:00Z"),
        _miss(run_id="run-B", ts="2026-01-01T00:00:00Z"),  # same ts, different run
    ]
    counts = rd.distinct_run_counts(misses)
    assert counts["kata-evaluate::exec-injection"] == 2


def test_distinct_run_counts_ts_fallback_for_legacy():
    """Entries with no run_id fall back to ts for run identity."""
    import recurrence_detect as rd

    misses = [
        _miss(ts="2026-01-01T00:00:00Z"),  # no run_id
        _miss(ts="2026-01-02T00:00:00Z"),  # no run_id, distinct ts
        _miss(ts="2026-01-02T00:00:00Z"),  # no run_id, duplicate ts
    ]
    counts = rd.distinct_run_counts(misses)
    assert counts["kata-evaluate::exec-injection"] == 2  # two distinct ts


def test_distinct_run_counts_not_raw_rows():
    """The count is distinct identities, NOT the raw row count."""
    import recurrence_detect as rd

    misses = [_miss(run_id="run-A") for _ in range(5)]  # 5 rows, 1 run
    counts = rd.distinct_run_counts(misses)
    assert counts["kata-evaluate::exec-injection"] == 1


def test_distinct_run_counts_blank_run_id_falls_back_to_ts():
    """A blank ('') run_id is ABSENT → identity falls back to ts (distinct ts → distinct runs)."""
    import recurrence_detect as rd

    misses = [
        _miss(run_id="", ts="2026-01-01T00:00:00Z"),
        _miss(run_id="", ts="2026-01-02T00:00:00Z"),
        _miss(run_id="", ts="2026-01-03T00:00:00Z"),
    ]
    counts = rd.distinct_run_counts(misses)
    assert counts["kata-evaluate::exec-injection"] == 3  # 3 distinct ts, NOT 1


def test_distinct_run_counts_whitespace_run_id_falls_back_to_ts():
    """A whitespace run_id behaves the same as blank → falls back to ts."""
    import recurrence_detect as rd

    misses = [
        _miss(run_id="   ", ts="2026-01-01T00:00:00Z"),
        _miss(run_id="\t", ts="2026-01-02T00:00:00Z"),
    ]
    counts = rd.distinct_run_counts(misses)
    assert counts["kata-evaluate::exec-injection"] == 2


def test_distinct_run_counts_real_run_id_takes_precedence_over_ts():
    """Regression: a real non-empty run_id still takes precedence over a shared ts."""
    import recurrence_detect as rd

    # 3 distinct run_ids that happen to share one ts → 3 distinct runs (not 1).
    misses = [_miss(run_id=f"run-{i}", ts="2026-01-01T00:00:00Z") for i in range(3)]
    counts = rd.distinct_run_counts(misses)
    assert counts["kata-evaluate::exec-injection"] == 3


# ---------------------------------------------------------------------------
# cluster_severity_tier
# ---------------------------------------------------------------------------

def test_severity_tier_blocker_short_circuit():
    """Any BLOCKER entry → tier BLOCKER."""
    import recurrence_detect as rd

    entries = [_miss(severity="MINOR"), _miss(severity="BLOCKER"), _miss(severity="MAJOR")]
    assert rd.cluster_severity_tier(entries) == "BLOCKER"


def test_severity_tier_major_when_no_blocker():
    """MAJOR present, no BLOCKER → tier MAJOR."""
    import recurrence_detect as rd

    entries = [_miss(severity="MINOR"), _miss(severity="MAJOR")]
    assert rd.cluster_severity_tier(entries) == "MAJOR"


def test_severity_tier_minor_default():
    """Only MINOR → tier MINOR."""
    import recurrence_detect as rd

    entries = [_miss(severity="MINOR")]
    assert rd.cluster_severity_tier(entries) == "MINOR"


# ---------------------------------------------------------------------------
# actionable_recurrences — distinct-run control
# ---------------------------------------------------------------------------

def test_three_distinct_run_id_actionable():
    """3 rows / 3 distinct run_id (MAJOR) → actionable at default threshold 3."""
    import recurrence_detect as rd

    misses = [_miss(run_id=f"run-{i}") for i in range(3)]
    result = rd.actionable_recurrences(misses, [])
    assert len(result) == 1
    assert result[0]["key"] == "kata-evaluate::exec-injection"
    assert result[0]["distinct_runs"] == 3
    assert result[0]["raw_count"] == 3


def test_three_rows_one_distinct_run_id_not_actionable():
    """3 rows but 1 distinct run_id → distinct_runs 1 < 3 → NOT actionable."""
    import recurrence_detect as rd

    misses = [_miss(run_id="run-same") for _ in range(3)]
    result = rd.actionable_recurrences(misses, [])
    assert result == []


def test_legacy_three_distinct_ts_actionable():
    """3 legacy rows (no run_id) with 3 distinct ts → actionable via ts-fallback."""
    import recurrence_detect as rd

    misses = [_miss(ts=f"2026-01-0{i}T00:00:00Z") for i in range(1, 4)]
    result = rd.actionable_recurrences(misses, [])
    assert len(result) == 1
    assert result[0]["distinct_runs"] == 3


def test_legacy_three_rows_one_distinct_ts_not_actionable():
    """3 legacy rows (no run_id) sharing 1 ts → distinct 1 < 3 → NOT actionable."""
    import recurrence_detect as rd

    misses = [_miss(ts="2026-01-01T00:00:00Z") for _ in range(3)]
    result = rd.actionable_recurrences(misses, [])
    assert result == []


def test_threshold_comparison_exact():
    """distinct_runs == threshold is actionable (>= is inclusive)."""
    import recurrence_detect as rd

    misses = [_miss(run_id=f"run-{i}") for i in range(3)]  # exactly 3
    result = rd.actionable_recurrences(misses, [], default_threshold=3)
    assert len(result) == 1


def test_blank_run_id_distinct_ts_actionable():
    """Silent-suppression guard: 3 misses all run_id='' but 3 distinct ts → ACTIONABLE.

    Under the old (None-only) fallback, '' is non-None → all collapse to 1 distinct
    run → the cluster would NEVER trip (fail-open silent suppression). The
    blank-guard makes the engine fail HONEST: blank run_id falls back to ts.
    """
    import recurrence_detect as rd

    misses = [_miss(run_id="", ts=f"2026-01-0{i}T00:00:00Z") for i in range(1, 4)]
    result = rd.actionable_recurrences(misses, [])
    assert len(result) == 1, "blank run_id must fall back to ts, not suppress the cluster"
    assert result[0]["distinct_runs"] == 3


def test_blank_run_id_shared_ts_not_actionable():
    """3 misses all run_id='' AND sharing one ts → 1 distinct run → NOT actionable."""
    import recurrence_detect as rd

    misses = [_miss(run_id="", ts="2026-01-01T00:00:00Z") for _ in range(3)]
    result = rd.actionable_recurrences(misses, [])
    assert result == []


def test_whitespace_run_id_distinct_ts_actionable():
    """A whitespace run_id behaves as blank: falls back to ts (3 distinct ts → actionable)."""
    import recurrence_detect as rd

    misses = [_miss(run_id="   ", ts=f"2026-01-0{i}T00:00:00Z") for i in range(1, 4)]
    result = rd.actionable_recurrences(misses, [])
    assert len(result) == 1
    assert result[0]["distinct_runs"] == 3


def test_real_run_id_precedence_three_rows_shared_ts_actionable():
    """Regression: 3 distinct real run_ids sharing one ts → 3 distinct runs → actionable."""
    import recurrence_detect as rd

    misses = [_miss(run_id=f"run-{i}", ts="2026-01-01T00:00:00Z") for i in range(3)]
    result = rd.actionable_recurrences(misses, [])
    assert len(result) == 1
    assert result[0]["distinct_runs"] == 3


# ---------------------------------------------------------------------------
# actionable_recurrences — severity short-circuit
# ---------------------------------------------------------------------------

def test_blocker_actionable_at_two_distinct_runs():
    """A BLOCKER cluster with 2 distinct runs IS actionable (threshold 2)."""
    import recurrence_detect as rd

    misses = [_miss(severity="BLOCKER", run_id=f"run-{i}") for i in range(2)]
    result = rd.actionable_recurrences(misses, [])
    assert len(result) == 1
    assert result[0]["severity_tier"] == "BLOCKER"
    assert result[0]["threshold"] == 2
    assert result[0]["distinct_runs"] == 2


def test_major_not_actionable_at_two_distinct_runs():
    """A MAJOR cluster with 2 distinct runs is NOT actionable (threshold 3)."""
    import recurrence_detect as rd

    misses = [_miss(severity="MAJOR", run_id=f"run-{i}") for i in range(2)]
    result = rd.actionable_recurrences(misses, [])
    assert result == []


# ---------------------------------------------------------------------------
# actionable_recurrences — handled-skip
# ---------------------------------------------------------------------------

def test_handled_proposed_cluster_excluded():
    """An over-threshold cluster with a 'proposed' marker is NOT returned."""
    import recurrence_detect as rd

    misses = [_miss(run_id=f"run-{i}") for i in range(3)]
    handled = [_handled(status="proposed")]
    result = rd.actionable_recurrences(misses, handled)
    assert result == [], "proposed cluster must be skipped (no re-proposal)"


def test_handled_guarded_cluster_excluded():
    """An over-threshold cluster with a 'guarded' marker is NOT returned."""
    import recurrence_detect as rd

    misses = [_miss(run_id=f"run-{i}") for i in range(3)]
    handled = [_handled(status="guarded", guard_ref="protocol/exec-safety.md")]
    result = rd.actionable_recurrences(misses, handled)
    assert result == []


def test_unhandled_other_cluster_still_actionable():
    """A handled marker for one cluster does not suppress a different cluster."""
    import recurrence_detect as rd

    misses = [_miss(skill="kata-review", cls="dos-vector", run_id=f"run-{i}") for i in range(3)]
    handled = [_handled(skill="kata-evaluate", cls="exec-injection")]  # different key
    result = rd.actionable_recurrences(misses, handled)
    assert len(result) == 1
    assert result[0]["key"] == "kata-review::dos-vector"


# ---------------------------------------------------------------------------
# actionable_recurrences — off-vocabulary flag + shape
# ---------------------------------------------------------------------------

def test_off_vocabulary_flagged_not_dropped():
    """An over-threshold off-enum class is RETURNED with off_vocabulary True."""
    import recurrence_detect as rd

    misses = [_miss(cls="rce-unchecked", run_id=f"run-{i}") for i in range(3)]
    result = rd.actionable_recurrences(misses, [])
    assert len(result) == 1, "off-vocab cluster must be flagged, never dropped"
    assert result[0]["off_vocabulary"] is True


def test_known_vocabulary_not_flagged():
    """An over-threshold curated class has off_vocabulary False."""
    import recurrence_detect as rd

    misses = [_miss(cls="exec-injection", run_id=f"run-{i}") for i in range(3)]
    result = rd.actionable_recurrences(misses, [])
    assert result[0]["off_vocabulary"] is False


def test_actionable_result_shape():
    """Each result dict carries the full documented key set."""
    import recurrence_detect as rd

    misses = [_miss(run_id=f"run-{i}") for i in range(3)]
    result = rd.actionable_recurrences(misses, [])
    assert set(result[0].keys()) == {
        "key", "responsible_skill", "failure_class", "distinct_runs",
        "raw_count", "severity_tier", "threshold", "off_vocabulary", "evidence",
    }


def test_empty_misses_returns_empty():
    """No misses → no actionable recurrences."""
    import recurrence_detect as rd

    assert rd.actionable_recurrences([], []) == []


# ---------------------------------------------------------------------------
# handled_schema / validate_handled
# ---------------------------------------------------------------------------

def test_handled_schema_fields_and_status_enum():
    """handled_schema lists the record fields and publishes the status enum."""
    import recurrence_detect as rd

    schema = rd.handled_schema()
    assert set(schema.keys()) == {
        "ts", "key", "responsible_skill", "failure_class",
        "status", "proposal_ref", "guard_ref",
    }
    assert schema["status"]["enum"] == ["guarded", "proposed"]


def test_validate_handled_valid_record():
    """A well-formed handled record returns no errors."""
    import recurrence_detect as rd

    assert rd.validate_handled(_handled()) == []


def test_validate_handled_extra_key_rejected():
    """An extra key is rejected (additionalProperties: false)."""
    import recurrence_detect as rd

    rec = _handled()
    rec["sneaky"] = "nope"
    errors = rd.validate_handled(rec)
    assert any("extra" in e for e in errors)


def test_validate_handled_missing_field_rejected():
    """A missing required field is rejected."""
    import recurrence_detect as rd

    rec = _handled()
    del rec["proposal_ref"]
    errors = rd.validate_handled(rec)
    assert any("proposal_ref" in e for e in errors)


def test_validate_handled_bad_status_rejected():
    """An off-enum status value is rejected."""
    import recurrence_detect as rd

    errors = rd.validate_handled(_handled(status="bogus"))
    assert any("status" in e for e in errors)


def test_validate_handled_guard_ref_nullable_and_typed():
    """guard_ref accepts str/None/missing, rejects non-str."""
    import recurrence_detect as rd

    assert rd.validate_handled(_handled(guard_ref="x.md")) == []
    assert rd.validate_handled(_handled(guard_ref=None)) == []
    rec = _handled()
    del rec["guard_ref"]
    assert rd.validate_handled(rec) == []
    errors = rd.validate_handled(_handled(guard_ref=42))
    assert any("guard_ref" in e for e in errors)


# ---------------------------------------------------------------------------
# append_handled — append-only + error contract
# ---------------------------------------------------------------------------

def test_append_handled_creates_and_is_append_only(tmp_path):
    """Two appends → two lines; the first line is preserved intact."""
    import recurrence_detect as rd

    target = tmp_path / "sub" / "recurrence-handled.jsonl"
    assert rd.append_handled(_handled(cls="exec-injection"), target) is True
    assert rd.append_handled(_handled(cls="dos-vector"), target) is True
    lines = target.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["failure_class"] == "exec-injection"
    assert json.loads(lines[1])["failure_class"] == "dos-vector"


def test_append_handled_raises_on_dotdot(tmp_path):
    """append_handled raises ValueError on a '..' path segment (CWE-23)."""
    import recurrence_detect as rd

    traversal = tmp_path / ".." / "evil.jsonl"
    with pytest.raises(ValueError, match=r"\.\."):
        rd.append_handled(_handled(), traversal)


def test_append_handled_raises_on_malformed(tmp_path):
    """append_handled raises ValueError when the record fails validation."""
    import recurrence_detect as rd

    with pytest.raises(ValueError):
        rd.append_handled(_handled(status="not-a-status"), tmp_path / "h.jsonl")


def test_append_handled_returns_false_on_io_failure(tmp_path):
    """append_handled returns False (does NOT raise) when the target is a directory."""
    import recurrence_detect as rd

    dir_path = tmp_path / "a_dir"
    dir_path.mkdir()
    assert rd.append_handled(_handled(), dir_path) is False


def test_append_handled_nul_path_returns_false():
    """A pathological path (embedded NUL) is a non-fatal write failure, not a raise."""
    import recurrence_detect as rd

    assert rd.append_handled(_handled(), "bad\x00path.jsonl") is False


# ---------------------------------------------------------------------------
# read_handled
# ---------------------------------------------------------------------------

def test_read_handled_absent_returns_empty(tmp_path):
    """read_handled returns [] for a non-existent file."""
    import recurrence_detect as rd

    assert rd.read_handled(tmp_path / "nope.jsonl") == []


def test_read_handled_tolerates_malformed(tmp_path):
    """A malformed line is skipped; valid records are returned."""
    import recurrence_detect as rd

    target = tmp_path / "h.jsonl"
    target.write_text("not json {{{\n" + json.dumps(_handled()) + "\n", encoding="utf-8")
    result = rd.read_handled(target)
    assert len(result) == 1
    assert result[0]["status"] == "proposed"


def test_read_handled_round_trips_appended(tmp_path):
    """Records written by append_handled are read back faithfully."""
    import recurrence_detect as rd

    target = tmp_path / "h.jsonl"
    rec = _handled()
    rd.append_handled(rec, target)
    assert rd.read_handled(target) == [rec]


# ---------------------------------------------------------------------------
# detect_from_paths
# ---------------------------------------------------------------------------

def test_detect_from_paths_reads_and_detects(tmp_path):
    """detect_from_paths reads manifest + sidecar and returns actionable clusters."""
    import recurrence_detect as rd

    manifest = tmp_path / "validation-misses.jsonl"
    handled = tmp_path / "recurrence-handled.jsonl"
    misses = [_miss(run_id=f"run-{i}") for i in range(3)]
    manifest.write_text(
        "".join(json.dumps(m) + "\n" for m in misses), encoding="utf-8"
    )
    result = rd.detect_from_paths(manifest, handled)  # handled absent ⇒ []
    assert len(result) == 1
    assert result[0]["key"] == "kata-evaluate::exec-injection"


def test_detect_from_paths_handled_suppresses(tmp_path):
    """A proposed marker in the sidecar suppresses the cluster via detect_from_paths."""
    import recurrence_detect as rd

    manifest = tmp_path / "validation-misses.jsonl"
    handled = tmp_path / "recurrence-handled.jsonl"
    misses = [_miss(run_id=f"run-{i}") for i in range(3)]
    manifest.write_text("".join(json.dumps(m) + "\n" for m in misses), encoding="utf-8")
    handled.write_text(json.dumps(_handled(status="proposed")) + "\n", encoding="utf-8")
    assert rd.detect_from_paths(manifest, handled) == []


def test_detect_from_paths_absent_files_empty(tmp_path):
    """Both files absent ⇒ [] (no crash)."""
    import recurrence_detect as rd

    assert rd.detect_from_paths(tmp_path / "a.jsonl", tmp_path / "b.jsonl") == []


# ---------------------------------------------------------------------------
# exec-safety — recurrence_detect.py is pure (no exec sink introduced)
# ---------------------------------------------------------------------------

class TestExecSafety:
    """Source-scan assertions: recurrence_detect.py introduces no execution sink."""

    def _source(self) -> str:
        return _SOURCE.read_text(encoding="utf-8")

    def test_no_eval(self):
        hits = [m.group() for m in re.finditer(r"\beval\s*\(", self._source())]
        assert not hits, f"eval() found in recurrence_detect.py: {hits}"

    def test_no_exec(self):
        hits = [m.group() for m in re.finditer(r"\bexec\s*\(", self._source())]
        assert not hits, f"exec() found in recurrence_detect.py: {hits}"

    def test_no_subprocess_import(self):
        hits = [
            m.group() for m in re.finditer(
                r"^\s*(?:import|from)\s+subprocess\b", self._source(), re.MULTILINE
            )
        ]
        assert not hits, f"subprocess import found in recurrence_detect.py: {hits}"

    def test_no_shell_true(self):
        assert "shell=True" not in self._source(), "shell=True found in recurrence_detect.py"

    def test_ast_parseable(self):
        ast.parse(self._source())


# ---------------------------------------------------------------------------
# Mutation non-vacuity proofs (spawn real subprocess via prove_non_vacuous)
# ---------------------------------------------------------------------------

def _tools_dir() -> str:
    return str(Path(__file__).parent.parent.resolve())


def _src() -> str:
    return str(_SOURCE.resolve())


def _cmd(test_name: str) -> str:
    return (
        f'cd /d "{_tools_dir()}" && uv run pytest '
        f"tests/test_recurrence_detect.py::{test_name} -q"
    )


def test_mutation_proof_distinct_run_identity():
    """(a1) Removing the distinct-identity accumulation breaks distinct-run counting.

    Asserted line (exact, 8-space indent):
        '        clusters.setdefault(key, set()).add(identity)'
    Removed → distinct_run_counts returns {} → no cluster reaches threshold →
    test_three_distinct_run_id_actionable goes red.
    """
    import mutation_run

    asserted_line = "        clusters.setdefault(key, set()).add(identity)"
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_three_distinct_run_id_actionable")
    )
    assert verdict["nonVacuous"] is True, f"distinct-run identity not load-bearing: {verdict}"


def test_mutation_proof_run_id_ts_fallback():
    """(a2) Removing the run_id→ts fallback breaks legacy ts-based counting.

    Asserted line (exact, 12-space indent):
        '            identity = m.get(fallback_key)'
    Removed → orphaned `else:` body → IndentationError on import →
    test_legacy_three_distinct_ts_actionable goes red.
    """
    import mutation_run

    asserted_line = "            identity = m.get(fallback_key)"
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_legacy_three_distinct_ts_actionable")
    )
    assert verdict["nonVacuous"] is True, f"run_id→ts fallback not load-bearing: {verdict}"


def test_mutation_proof_blank_run_id_guard():
    """(a3) Removing the blank/whitespace run_id guard re-opens the silent-suppression.

    Asserted line (exact, 8-space indent):
        '        if isinstance(rid, str) and rid.strip():'
    Removed → orphaned `identity = rid` body → IndentationError on import →
    test_blank_run_id_distinct_ts_actionable goes red. (Proves the blank-guard
    line is load-bearing: without it, a blank run_id is non-None and collapses a
    cluster to one run, suppressing detection.)
    """
    import mutation_run

    asserted_line = "        if isinstance(rid, str) and rid.strip():"
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_blank_run_id_distinct_ts_actionable")
    )
    assert verdict["nonVacuous"] is True, f"blank run_id guard not load-bearing: {verdict}"


def test_mutation_proof_severity_threshold_selection():
    """(b) Removing the severity-aware threshold selection breaks the BLOCKER@2 path.

    Asserted line (exact, 8-space indent):
        '        threshold = blocker_threshold if tier == "BLOCKER" else default_threshold'
    Removed → `threshold` undefined → NameError when compared →
    test_blocker_actionable_at_two_distinct_runs goes red.
    """
    import mutation_run

    asserted_line = (
        '        threshold = blocker_threshold if tier == "BLOCKER" else default_threshold'
    )
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_blocker_actionable_at_two_distinct_runs")
    )
    assert verdict["nonVacuous"] is True, f"severity threshold not load-bearing: {verdict}"


def test_mutation_proof_handled_skip():
    """(c) Removing the handled-aware skip guard makes a proposed cluster re-surface.

    Asserted line (exact, 8-space indent):
        '        if key in handled_keys:'
    Removed → orphaned `continue` → IndentationError on import →
    test_handled_proposed_cluster_excluded goes red.
    """
    import mutation_run

    asserted_line = "        if key in handled_keys:"
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_handled_proposed_cluster_excluded")
    )
    assert verdict["nonVacuous"] is True, f"handled-skip not load-bearing: {verdict}"


def test_mutation_proof_threshold_comparison():
    """(d) Removing the >= threshold comparison breaks actionability.

    Asserted line (exact, 8-space indent):
        '        if distinct_runs >= threshold:'
    Removed → orphaned results.append block → IndentationError on import →
    test_threshold_comparison_exact goes red.
    """
    import mutation_run

    asserted_line = "        if distinct_runs >= threshold:"
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_threshold_comparison_exact")
    )
    assert verdict["nonVacuous"] is True, f">= threshold comparison not load-bearing: {verdict}"


def test_mutation_proof_dotdot_guard():
    """(e) Removing the '..' guard in append_handled's _guard_path defeats CWE-23.

    Asserted line (exact, 4-space indent):
        '    if any(part == ".." for part in p.parts):'
    Removed → orphaned raise → IndentationError on import →
    test_append_handled_raises_on_dotdot goes red.
    """
    import mutation_run

    asserted_line = '    if any(part == ".." for part in p.parts):'
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_append_handled_raises_on_dotdot")
    )
    assert verdict["nonVacuous"] is True, f"'..' guard not load-bearing: {verdict}"
