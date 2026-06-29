"""test_debug_report.py — TDD suite for tools/debug_report.py (Slice A, Phase P3).

Strategy: default-FAIL (tests written before implementation; green only after
debug_report.py is present and correct).  Pure tests (no I/O except fixture
loads and tmp_path writes) plus mutation-proof tests that spawn a real
subprocess via mutation_run.prove_non_vacuous.

The engine is PURE data assembly — it transcribes the P1/P2 artifacts' own
verdicts/labels and confers none.  These tests pin the LD12 honesty surfaces at
the engine (§5 behavioral-only, LD5 heuristic confidence, n=0 live, real Snyk)
so they cannot be silently regressed.

Coverage map
------------
debug_report_schema / snyk_report_schema:
    TestSchemas::test_debug_report_schema_honesty_strings
    TestSchemas::test_debug_report_schema_required_keys
    TestSchemas::test_snyk_report_schema_shape

finding_id:
    TestFindingId::test_id_preferred
    TestFindingId::test_locus_when_no_id
    TestFindingId::test_unknown_when_neither
    TestFindingId::test_identical_to_drift_gate_defer_record

build_confidence_map:
    TestConfidenceMap::test_high_fm_assessed
    TestConfidenceMap::test_force_low_is_low_confidence
    TestConfidenceMap::test_sparse_is_low_confidence
    TestConfidenceMap::test_graph_module_no_fm_skipped
    TestConfidenceMap::test_every_entry_heuristic_true
    TestConfidenceMap::test_missing_confidence_low_confidence

build_deviation_table:
    TestDeviationTable::test_auto_fix_pass_applied
    TestDeviationTable::test_block_deferred_row
    TestDeviationTable::test_research_defer_human_no_fix_claim
    TestDeviationTable::test_locus_only_join_complete

build_proof_rollup:
    TestProofRollup::test_drift_counts
    TestProofRollup::test_suite_green
    TestProofRollup::test_all_non_vacuous
    TestProofRollup::test_snyk_clean_zero_new_findings
    TestProofRollup::test_snyk_with_finding_counts
    TestProofRollup::test_snyk_unavailable_not_clean
    TestProofRollup::test_behavioral_only_flag

build_debug_report / emit / load:
    TestBuildAndRoundTrip::test_carries_recommendations_unchanged
    TestBuildAndRoundTrip::test_carries_offered_followups_unchanged
    TestBuildAndRoundTrip::test_round_trip_schema_valid

exec-safety:
    TestExecSafety::test_no_eval
    TestExecSafety::test_no_exec
    TestExecSafety::test_no_subprocess_import
    TestExecSafety::test_no_shell_true
    TestExecSafety::test_pure_ast_parseable

Mutation proofs (spawn real subprocess via prove_non_vacuous):
    TestMutationProof::test_mutation_low_confidence_branch        (a)
    TestMutationProof::test_mutation_applied_join_branch          (b)
    TestMutationProof::test_mutation_behavioral_only_flag         (c)
    TestMutationProof::test_mutation_snyk_unavailable_branch      (d)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent.parent
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "debug_report"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _load_json(rel: str):
    return json.loads((_FIXTURES / rel).read_text(encoding="utf-8"))


def _function_models() -> list[dict]:
    return [
        _load_json("function_models/mod_a_high.json"),
        _load_json("function_models/mod_b_low.json"),
        _load_json("function_models/mod_c_sparse.json"),
    ]


def _graph_modules() -> list[str]:
    # mod_d has no FM -> skipped
    return ["src/mod_a.py", "src/mod_b.py", "src/mod_c.py", "src/mod_d.py"]


def _findings() -> list[dict]:
    return _load_json("findings.json")


def _drift_reports() -> list[dict]:
    return [_load_json("drift/A_pass.json"), _load_json("drift/B_block.json")]


def _fix_manifests() -> list[dict]:
    return [_load_json("fix_manifest/A.json")]


def _deferrals() -> list[dict]:
    return _load_json("deferred.json")


def _result_json() -> dict:
    return _load_json("RESULT.json")


def _mutation_json() -> dict:
    return _load_json("mutation.json")


def _snyk_clean() -> dict:
    return _load_json("snyk/A_clean.json")


def _snyk_withfinding() -> dict:
    return _load_json("snyk/B_withfinding.json")


def _snyk_unavailable() -> dict:
    return _load_json("snyk/C_unavailable.json")


def _snyk_masking() -> dict:
    # Regression-masking attack: stored newFindings:0 but after-before = +5.
    return _load_json("snyk/D_masking.json")


# Stable finding_id of the locus-only auto-fix-eligible finding (finding A)
_LOCUS_ONLY_ID = "src/mod_a.py::compute"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TestSchemas:
    def test_debug_report_schema_honesty_strings(self):
        """The schema description carries all three §5/LD5/n=0 honesty strings."""
        import debug_report as dr
        desc = dr.debug_report_schema()["description"].lower()
        # §5 behavioral-only
        assert "behavioral" in desc
        assert "structure preserved" in desc
        assert "fast-follow" in desc
        # LD5 heuristic confidence (uncalibrated)
        assert "heuristic" in desc
        assert "uncalibrated" in desc
        # n=0 live
        assert "n=0 live" in desc
        assert "never run end-to-end" in desc

    def test_debug_report_schema_required_keys(self):
        import debug_report as dr
        schema = dr.debug_report_schema()
        for key in (
            "confidence_map",
            "deviation_table",
            "proof_rollup",
            "recommendations",
            "offered_followups",
            "honesty",
            "utc",
        ):
            assert key in schema["required"], f"{key!r} missing from required"

    def test_snyk_report_schema_shape(self):
        """snyk_report_schema is the single source of truth for .kata/snyk/<id>.json."""
        import debug_report as dr
        schema = dr.snyk_report_schema()
        for key in ("finding_id", "before", "after", "newFindings", "available"):
            assert key in schema["required"], f"{key!r} missing from required"
        before = schema["properties"]["before"]
        assert "verdict" in before["properties"]
        assert "findingCount" in before["properties"]
        after = schema["properties"]["after"]
        assert "verdict" in after["properties"]
        assert "findingCount" in after["properties"]


# ---------------------------------------------------------------------------
# finding_id — identical to drift_gate.defer_record derivation
# ---------------------------------------------------------------------------


class TestFindingId:
    def test_id_preferred(self):
        import debug_report as dr
        assert dr.finding_id({"id": "X", "locus": "Y"}) == "X"

    def test_locus_when_no_id(self):
        import debug_report as dr
        assert dr.finding_id({"locus": "Y"}) == "Y"

    def test_unknown_when_neither(self):
        import debug_report as dr
        assert dr.finding_id({}) == "unknown"

    def test_identical_to_drift_gate_defer_record(self):
        """The helper derives the key identically to drift_gate.defer_record."""
        import debug_report as dr
        import drift_gate as dg
        for finding in (
            {"id": "F1", "locus": "loc"},
            {"locus": "only-locus"},
            {},
        ):
            record = dg.defer_record(finding, "reason")
            assert dr.finding_id(finding) == record["finding_id"]


# ---------------------------------------------------------------------------
# build_confidence_map
# ---------------------------------------------------------------------------


class TestConfidenceMap:
    def test_high_fm_assessed(self):
        import debug_report as dr
        cmap = dr.build_confidence_map(_function_models(), graph_modules=_graph_modules())
        assert cmap["src/mod_a.py"]["classification"] == "assessed"

    def test_force_low_is_low_confidence(self):
        """The force-LOW FM (confidence <= low_cap) -> low_confidence."""
        import debug_report as dr
        cmap = dr.build_confidence_map(_function_models(), graph_modules=_graph_modules())
        assert cmap["src/mod_b.py"]["classification"] == "low_confidence"

    def test_sparse_is_low_confidence(self):
        """The sparse FM (confidence just under low_cap) -> low_confidence."""
        import debug_report as dr
        cmap = dr.build_confidence_map(_function_models(), graph_modules=_graph_modules())
        assert cmap["src/mod_c.py"]["classification"] == "low_confidence"

    def test_graph_module_no_fm_skipped(self):
        """A graph module with no FM -> skipped (never silently 'assessed')."""
        import debug_report as dr
        cmap = dr.build_confidence_map(_function_models(), graph_modules=_graph_modules())
        assert cmap["src/mod_d.py"]["classification"] == "skipped"

    def test_every_entry_heuristic_true(self):
        """Every entry is tagged heuristic:true (LD5 v1, uncalibrated)."""
        import debug_report as dr
        cmap = dr.build_confidence_map(_function_models(), graph_modules=_graph_modules())
        assert cmap, "confidence map must not be empty"
        for module, entry in cmap.items():
            assert entry["heuristic"] is True, f"{module} not tagged heuristic"

    def test_missing_confidence_low_confidence(self):
        """An FM with no confidence value is treated as low_confidence (fail-honest)."""
        import debug_report as dr
        fm = {"module": "src/none.py"}
        cmap = dr.build_confidence_map([fm])
        assert cmap["src/none.py"]["classification"] == "low_confidence"

    def test_non_numeric_confidence_low_confidence(self):
        """MINOR 3: a non-numeric confidence ('high') must NOT crash — low_confidence."""
        import debug_report as dr
        cmap = dr.build_confidence_map([{"module": "src/m.py", "confidence": "high"}])
        assert cmap["src/m.py"]["classification"] == "low_confidence"

    def test_bool_confidence_low_confidence(self):
        """MINOR 3: a bool confidence is NOT a number → low_confidence (no <= crash)."""
        import debug_report as dr
        cmap = dr.build_confidence_map([{"module": "src/b.py", "confidence": True}])
        assert cmap["src/b.py"]["classification"] == "low_confidence"

    def test_malformed_function_model_skipped(self):
        """MINOR 4: a non-dict FM entry is skipped; good entries still process."""
        import debug_report as dr
        cmap = dr.build_confidence_map([None, "junk", {"module": "src/ok.py", "confidence": 0.9}])
        assert cmap["src/ok.py"]["classification"] == "assessed"
        assert len(cmap) == 1


# ---------------------------------------------------------------------------
# build_deviation_table
# ---------------------------------------------------------------------------


def _row_by_id(table: list[dict], fid: str) -> dict:
    for row in table:
        if row["finding_id"] == fid:
            return row
    raise AssertionError(f"no row for finding_id {fid!r} in table")


class TestDeviationTable:
    def _table(self) -> list[dict]:
        import debug_report as dr
        return dr.build_deviation_table(
            _findings(), _drift_reports(), _fix_manifests(), _deferrals()
        )

    def test_auto_fix_pass_applied(self):
        """The auto-fix-eligible + PASS finding row: applied:true + flipped + char files."""
        row = _row_by_id(self._table(), _LOCUS_ONLY_ID)
        assert row["route"] == "auto-fix-eligible"
        assert row["applied"] is True
        assert row["drift_verdict"] == "PASS"
        assert "tests/characterization/mod_a_char.py::test_compute_pins" in row["pinning_tests"]
        assert "tests/characterization/mod_a_char.py" in row["characterization_files"]

    def test_block_deferred_row(self):
        """The BLOCK/deferred finding row: applied:false + the deferral reason."""
        row = _row_by_id(self._table(), "F-BLOCK")
        assert row["applied"] is False
        assert row["drift_verdict"] == "BLOCK"
        assert row["deferred"] is True
        assert "cannot fix without behavioral drift" in row["reason"]

    def test_research_defer_human_no_fix_claim(self):
        """research / defer / human findings appear with route and NO applied-fix claim."""
        table = self._table()
        for fid, route in (
            ("F-RESEARCH", "research"),
            ("F-DEFER", "defer"),
            ("F-HUMAN", "human"),
        ):
            row = _row_by_id(table, fid)
            assert row["route"] == route
            assert row["applied"] is False, f"{fid} must not claim an applied fix"
            assert row["pinning_tests"] == []
            assert row["characterization_files"] == []

    def test_locus_only_join_complete(self):
        """MINOR 2: a finding with ONLY locus joins to drift+fix keyed by that locus."""
        # finding A has no "id" — only "locus" == _LOCUS_ONLY_ID
        finding_a = _findings()[0]
        assert "id" not in finding_a
        assert finding_a["locus"] == _LOCUS_ONLY_ID
        row = _row_by_id(self._table(), _LOCUS_ONLY_ID)
        # complete join: drift verdict, pinning tests, and char files all present
        assert row["drift_verdict"] == "PASS"
        assert row["pinning_tests"], "locus-only join missed the drift proof"
        assert row["characterization_files"], "locus-only join missed the fix manifest"

    def test_route_gated_research_not_applied(self):
        """MAJOR 2(a): a research finding with a PASS drift keyed to its id is NOT applied.

        applied is gated on the finding's OWN route being auto-fix-eligible — a
        research finding must never render as a proven applied fix.
        """
        import debug_report as dr
        findings = [{"id": "R1", "route": "research"}]
        drift = [{
            "finding_id": "R1",
            "verdict": "PASS",
            "behavioral": {"verdict": "PASS", "flipped": ["t::pins"]},
        }]
        fix = [{"finding_id": "R1", "characterization_files": ["tests/char_r1.py"]}]
        row = _row_by_id(dr.build_deviation_table(findings, drift, fix, []), "R1")
        assert row["route"] == "research"
        assert row["applied"] is False, "research finding must not claim an applied fix"
        assert row["pinning_tests"] == []
        assert row["characterization_files"] == []

    def test_duplicate_finding_id_no_cross_attribution(self):
        """MAJOR 2(b): two findings deriving the same id are ambiguous — no cross-join.

        An auto-fix-eligible and a research finding both lacking id+locus both
        derive "unknown"; a single PASS drift keyed "unknown" must NOT be
        attributed to either (which would let the research finding render applied,
        or cross-attribute the auto-fix finding's proof).
        """
        import debug_report as dr
        findings = [
            {"route": "auto-fix-eligible", "module": "src/a.py"},
            {"route": "research", "module": "src/b.py"},
        ]
        drift = [{
            "finding_id": "unknown",
            "verdict": "PASS",
            "behavioral": {"verdict": "PASS", "flipped": ["t::pins"]},
        }]
        table = dr.build_deviation_table(findings, drift, [], [])
        assert len(table) == 2
        for row in table:
            assert row["finding_id"] == "unknown"
            assert row["ambiguous"] is True
            assert row["applied"] is False, "ambiguous id must not attach a proof"
            assert row["pinning_tests"] == []
            assert row["drift_verdict"] is None

    def test_malformed_finding_skipped(self):
        """MINOR 4: a non-dict finding is skipped; good findings still process."""
        import debug_report as dr
        findings = [None, "junk", {"id": "G1", "route": "research"}]
        table = dr.build_deviation_table(findings, [], [], [])
        assert len(table) == 1
        assert table[0]["finding_id"] == "G1"


# ---------------------------------------------------------------------------
# build_proof_rollup
# ---------------------------------------------------------------------------


class TestProofRollup:
    def _rollup(self, snyk_reports=None) -> dict:
        import debug_report as dr
        if snyk_reports is None:
            snyk_reports = [_snyk_clean(), _snyk_withfinding()]
        return dr.build_proof_rollup(
            _drift_reports(), _result_json(), _mutation_json(), snyk_reports
        )

    def test_drift_counts(self):
        rollup = self._rollup()
        assert rollup["drift"]["pass"] == 1
        assert rollup["drift"]["block"] == 1

    def test_suite_green(self):
        rollup = self._rollup()
        assert rollup["suite_green"] is True

    def test_all_non_vacuous(self):
        rollup = self._rollup()
        assert rollup["allNonVacuous"] is True

    def test_snyk_clean_zero_new_findings(self):
        """The clean Snyk artifact rolls up newFindings:0."""
        rollup = self._rollup(snyk_reports=[_snyk_clean()])
        assert rollup["snyk"]["newFindings"] == 0
        assert rollup["snyk"]["clean"] is True

    def test_snyk_with_finding_counts(self):
        """The with-finding Snyk artifact rolls up newFindings >= 1."""
        rollup = self._rollup(snyk_reports=[_snyk_clean(), _snyk_withfinding()])
        assert rollup["snyk"]["newFindings"] >= 1

    def test_snyk_unavailable_not_clean(self):
        """An available:false artifact rolls up as unavailable, NEVER as clean."""
        rollup = self._rollup(snyk_reports=[_snyk_unavailable()])
        assert "F-NOSCAN" in rollup["snyk"]["unavailable"]
        assert rollup["snyk"]["clean"] is False
        assert rollup["snyk"]["available"] is False

    def test_behavioral_only_flag(self):
        """The behavioral-only limitation flag is present and True."""
        rollup = self._rollup()
        assert rollup["behavioral_only"] is True

    def test_snyk_regression_not_masked(self):
        """MAJOR 1: a too-low stored newFindings can NOT mask a real +5 regression.

        Input: before.findingCount 0, after.findingCount 5, stored newFindings 0,
        available. The engine RECOMPUTEs newFindings = max(stored, after-before)
        so the rollup is NOT clean and newFindings >= 5.
        """
        rollup = self._rollup(snyk_reports=[_snyk_masking()])
        assert rollup["snyk"]["newFindings"] >= 5, "regression masked by stored newFindings"
        assert rollup["snyk"]["clean"] is False

    def test_snyk_missing_count_not_clean(self):
        """MAJOR 1 fail-honest: an available report missing a findingCount is NOT clean."""
        rollup = self._rollup(snyk_reports=[{
            "finding_id": "F-NOCOUNT",
            "before": {"verdict": "clean"},
            "after": {"verdict": "clean"},
            "newFindings": 0,
            "available": True,
        }])
        assert "F-NOCOUNT" in rollup["snyk"]["countMissing"]
        assert rollup["snyk"]["clean"] is False

    def test_snyk_malformed_report_skipped(self):
        """MINOR 4: a non-dict snyk report is skipped; good ones still roll up."""
        rollup = self._rollup(snyk_reports=["junk", None, _snyk_clean()])
        assert rollup["snyk"]["reportCount"] == 1
        assert rollup["snyk"]["newFindings"] == 0

    def test_snyk_negative_new_findings_floor(self):
        """Floor effective_new at 0 when counts absent and newFindings is negative (ad-val).

        A malformed/adversarial record with newFindings:-50 and no before/after
        findingCounts must NOT drive the aggregate newFindings total negative.
        The floor must clamp effective_new to >= 0 on the counts-absent path.
        The honesty invariant is preserved: count_missing => counts_ok=False =>
        snyk_clean=False.  The floor only fixes the advisory integer; it never
        flips clean to True.
        """
        import debug_report as dr
        snyk_negative = {
            "finding_id": "F-NEGATIVE",
            "before": {"verdict": "clean"},
            "after": {"verdict": "clean"},
            "newFindings": -50,
            "available": True,
        }
        rollup = dr.build_proof_rollup(
            _drift_reports(), _result_json(), _mutation_json(), [snyk_negative]
        )
        # Per-record effective_new must be clamped to >= 0.
        per = next(r for r in rollup["snyk"]["per_fix"] if r["finding_id"] == "F-NEGATIVE")
        assert per["newFindings"] >= 0, "per-record effective_new driven negative by -50 input"
        # Aggregate total must also be >= 0.
        assert rollup["snyk"]["newFindings"] >= 0, "aggregate newFindings driven negative"
        # Honesty invariant: counts absent => countMissing => NOT clean.
        assert "F-NEGATIVE" in rollup["snyk"]["countMissing"]
        assert rollup["snyk"]["clean"] is False


# ---------------------------------------------------------------------------
# build_debug_report / emit / load
# ---------------------------------------------------------------------------


class TestBuildAndRoundTrip:
    def _report(self):
        import debug_report as dr
        cmap = dr.build_confidence_map(_function_models(), graph_modules=_graph_modules())
        table = dr.build_deviation_table(
            _findings(), _drift_reports(), _fix_manifests(), _deferrals()
        )
        rollup = dr.build_proof_rollup(
            _drift_reports(), _result_json(), _mutation_json(),
            [_snyk_clean(), _snyk_withfinding()],
        )
        recs = [{"title": "Add input validation", "source": "research"}]
        followups = {"version_up": True, "sprint": "debug-followup-1"}
        return dr.build_debug_report(
            cmap, table, rollup, recommendations=recs, offered_followups=followups
        )

    def test_carries_recommendations_unchanged(self):
        report = self._report()
        assert report["recommendations"] == [
            {"title": "Add input validation", "source": "research"}
        ]

    def test_carries_offered_followups_unchanged(self):
        report = self._report()
        assert report["offered_followups"] == {
            "version_up": True,
            "sprint": "debug-followup-1",
        }

    def test_round_trip_schema_valid(self, tmp_path):
        import debug_report as dr
        report = self._report()
        dest = tmp_path / ".kata" / "debug" / "closeout.json"
        assert not dest.parent.exists()
        dr.emit_debug_report(report, dest)
        assert dest.exists()
        loaded = dr.load_debug_report(dest)
        schema = dr.debug_report_schema()
        for key in schema["required"]:
            assert key in loaded, f"schema-required key {key!r} missing after round-trip"
        assert loaded["honesty"]["behavioral_only"] is True
        assert loaded["honesty"]["confidence_heuristic"] is True
        assert loaded["honesty"]["live_run"] is False


# ---------------------------------------------------------------------------
# exec-safety: no eval / exec / subprocess / shell in debug_report.py
# ---------------------------------------------------------------------------


class TestExecSafety:
    """Source-scan assertions: debug_report.py is pure — no exec sink introduced."""

    def _source(self) -> str:
        return (_TOOLS / "debug_report.py").read_text(encoding="utf-8")

    def test_no_eval(self):
        import re
        hits = [m.group() for m in re.finditer(r"\beval\s*\(", self._source())]
        assert not hits, f"eval() call found in debug_report.py: {hits}"

    def test_no_exec(self):
        import re
        hits = [m.group() for m in re.finditer(r"\bexec\s*\(", self._source())]
        assert not hits, f"exec() call found in debug_report.py: {hits}"

    def test_no_subprocess_import(self):
        import re
        hits = [
            m.group()
            for m in re.finditer(
                r"^\s*(?:import|from)\s+subprocess\b", self._source(), re.MULTILINE
            )
        ]
        assert not hits, f"subprocess import found in debug_report.py: {hits}"

    def test_no_shell_true(self):
        assert "shell=True" not in self._source(), "shell=True found in debug_report.py"

    def test_pure_ast_parseable(self):
        import ast
        ast.parse(self._source())


# ---------------------------------------------------------------------------
# Mutation non-vacuity proofs (spawn real subprocess via prove_non_vacuous)
# ---------------------------------------------------------------------------


class TestMutationProof:
    """Mutation-proof tests for the four named load-bearing branches.

    Each test removes exactly one load-bearing line from debug_report.py using
    mutation_run.prove_non_vacuous and verifies the corresponding guard test
    goes red (testWentRed:True, nonVacuous:True).  Each target line has a sibling
    statement in its block, so removal keeps the module syntactically valid — the
    failure is from the targeted behavior change, NOT a syntax error (proving the
    test is non-vacuous, not vacuously-red).

    prove_non_vacuous always restores the source file afterward (try/finally), so
    these tests are self-healing even on failure.
    """

    def _source(self) -> str:
        return str(_TOOLS / "debug_report.py")

    def _test_cmd(self, test_spec: str) -> str:
        return (
            f'cd /d "{_TOOLS}" && '
            f"{sys.executable} -m pytest "
            f'"tests/test_debug_report.py::{test_spec}" -q --tb=no'
        )

    def test_mutation_low_confidence_branch(self):
        """(a) The low_confidence-vs-skipped classification branch is load-bearing."""
        import mutation_run
        asserted_line = '            entry["classification"] = "low_confidence"'
        cmd = self._test_cmd("TestConfidenceMap::test_force_low_is_low_confidence")
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing the low_confidence classification must make "
            "test_force_low_is_low_confidence go red"
        )
        assert verdict["nonVacuous"], (
            "test_force_low_is_low_confidence must catch removal of the "
            "low_confidence classification"
        )

    def test_mutation_applied_join_branch(self):
        """(b) The applied-vs-deferred join branch is load-bearing."""
        import mutation_run
        asserted_line = '            row["applied"] = True'
        cmd = self._test_cmd("TestDeviationTable::test_auto_fix_pass_applied")
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing row['applied'] = True must make test_auto_fix_pass_applied go red"
        )
        assert verdict["nonVacuous"], (
            "test_auto_fix_pass_applied must catch removal of the applied join"
        )

    def test_mutation_behavioral_only_flag(self):
        """(c) The honesty-flag (behavioral-only) propagation is load-bearing."""
        import mutation_run
        asserted_line = '    rollup["behavioral_only"] = True'
        cmd = self._test_cmd("TestProofRollup::test_behavioral_only_flag")
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing the behavioral_only flag must make test_behavioral_only_flag go red"
        )
        assert verdict["nonVacuous"], (
            "test_behavioral_only_flag must catch removal of the behavioral-only flag"
        )

    def test_mutation_snyk_unavailable_branch(self):
        """(d) The Snyk available:false -> honest-unavailable branch is load-bearing."""
        import mutation_run
        asserted_line = "            unavailable.append(rid)"
        cmd = self._test_cmd("TestProofRollup::test_snyk_unavailable_not_clean")
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing unavailable.append(rid) must make "
            "test_snyk_unavailable_not_clean go red"
        )
        assert verdict["nonVacuous"], (
            "test_snyk_unavailable_not_clean must catch removal of the "
            "unavailable roll-up"
        )

    def test_mutation_snyk_recompute_branch(self):
        """(e) MAJOR 1: the Snyk newFindings RECOMPUTE branch is load-bearing.

        Removing ``effective_new = max(stored_new, derived)`` leaves the stored
        (too-low) value in place, so the +5 masking input rolls up newFindings 0
        / clean — the regression-masking guard test goes red.
        """
        import mutation_run
        asserted_line = "            effective_new = max(stored_new, derived)"
        cmd = self._test_cmd("TestProofRollup::test_snyk_regression_not_masked")
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing the newFindings recompute must make "
            "test_snyk_regression_not_masked go red"
        )
        assert verdict["nonVacuous"], (
            "test_snyk_regression_not_masked must catch removal of the "
            "newFindings recompute (regression-masking defense)"
        )

    def test_mutation_snyk_negative_floor(self):
        """(f) The effective_new >= 0 floor on ALL paths is load-bearing (ad-val).

        Removing the floor line allows a negative effective_new (-50) to pass
        through on the counts-absent branch, driving the aggregate newFindings
        total negative — the guard test goes red.
        """
        import mutation_run
        asserted_line = "        effective_new = max(0, effective_new)"
        cmd = self._test_cmd("TestProofRollup::test_snyk_negative_new_findings_floor")
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing the effective_new >= 0 floor must make "
            "test_snyk_negative_new_findings_floor go red"
        )
        assert verdict["nonVacuous"], (
            "test_snyk_negative_new_findings_floor must catch removal of the "
            "effective_new floor (negative newFindings ad-val defense)"
        )
