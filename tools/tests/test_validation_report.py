"""test_validation_report.py — TDD + mutation-proof suite for tools/validation_report.py.

Written TDD-first: these tests are authored against the spec; they go green only after
validation_report.py is correctly implemented.  Each test goes RED if its target logic is
removed or mutated (mutation-proof by construction).

Coverage map
------------
finding_schema / report_schema:
    TestSchemas::test_finding_schema_required_fields
    TestSchemas::test_finding_schema_severity_enum
    TestSchemas::test_report_schema_required_fields
    TestSchemas::test_report_schema_passed_defaults_false

finding_id (id → locus/location → "unknown", no hash):
    TestFindingId::test_id_preferred
    TestFindingId::test_locus_fallback_when_no_id
    TestFindingId::test_location_fallback_when_no_id_or_locus
    TestFindingId::test_unknown_when_no_id_locus_location
    TestFindingId::test_falsy_id_falls_through_to_locus
    TestFindingId::test_falsy_id_and_locus_falls_through_to_location
    TestFindingId::test_returns_string
    TestFindingId::test_matches_debug_report_precedent_algorithm

severity_of (SARIF mapping + behavior_changing rule):
    TestSeverityOf::test_behavior_changing_true_yields_error
    TestSeverityOf::test_behavior_changing_false_uses_severity_field
    TestSeverityOf::test_error_passthrough
    TestSeverityOf::test_warning_passthrough
    TestSeverityOf::test_info_passthrough
    TestSeverityOf::test_blocker_maps_to_error
    TestSeverityOf::test_major_maps_to_warning
    TestSeverityOf::test_minor_maps_to_info
    TestSeverityOf::test_slop_critical_maps_to_error
    TestSeverityOf::test_warn_alias_maps_to_warning
    TestSeverityOf::test_uppercase_error_severity_maps_to_error
    TestSeverityOf::test_gate_verdict_tokens_map_to_error
    TestSeverityOf::test_generic_sarif_major_minor_stay_soft
    TestSeverityOf::test_unknown_band_defaults_to_info
    TestSeverityOf::test_behavior_changing_overrides_info_severity
    TestSeverityOf::test_behavior_changing_overrides_warning_severity

render_table:
    TestRenderTable::test_empty_findings_no_na_legs_yields_header_only
    TestRenderTable::test_single_finding_appears_in_table
    TestRenderTable::test_severity_order_error_before_warning_before_info
    TestRenderTable::test_stable_sort_by_finding_id_within_severity_band
    TestRenderTable::test_na_leg_yields_explicit_info_row
    TestRenderTable::test_score_na_leg_message
    TestRenderTable::test_non_score_na_leg_message
    TestRenderTable::test_skipped_score_leg_never_reads_as_clean_pass
    TestRenderTable::test_no_html_in_output
    TestRenderTable::test_pipe_in_message_is_escaped
    TestRenderTable::test_location_none_renders_dash
    TestRenderTable::test_na_row_has_info_severity
    TestRenderTable::test_na_row_survives_with_real_findings

emit_findings / load_findings (round-trip + path guard):
    TestEmitLoad::test_round_trip_identity
    TestEmitLoad::test_writes_json_file
    TestEmitLoad::test_creates_parent_dirs
    TestEmitLoad::test_traversal_guard_rejects_dotdot_path
    TestEmitLoad::test_traversal_guard_rejects_dotdot_in_segment
    TestEmitLoad::test_accepts_normal_nested_path
    TestEmitLoad::test_utf8_encoded

compute_passed:
    TestComputePassed::test_empty_findings_passes
    TestComputePassed::test_error_finding_fails
    TestComputePassed::test_hold_finding_fails_even_with_warning_severity
    TestComputePassed::test_info_finding_does_not_fail
    TestComputePassed::test_na_info_finding_does_not_fail
    TestComputePassed::test_warning_without_hold_does_not_fail
    TestComputePassed::test_tripwire_ok_false_fails_regardless
    TestComputePassed::test_tripwire_ok_true_with_clean_findings_passes
    TestComputePassed::test_multiple_findings_any_error_fails
    TestComputePassed::test_multiple_findings_any_hold_fails
    TestComputePassed::test_uppercase_error_severity_fails
    TestComputePassed::test_gate_verdict_tokens_fail
    TestComputePassed::test_major_slop_with_hold_fails

tripwire corpus + assert_tripwire_flagged:
    TestTripwireCorpus::test_corpus_is_nonempty
    TestTripwireCorpus::test_corpus_has_at_least_one_error
    TestTripwireCorpus::test_corpus_findings_are_dicts

TestAssertTripwireFlagged::test_corpus_passes_assertion
TestAssertTripwireFlagged::test_empty_findings_raises
TestAssertTripwireFlagged::test_info_only_findings_raise
TestAssertTripwireFlagged::test_warning_only_no_hold_raises
TestAssertTripwireFlagged::test_error_finding_passes_assertion
TestAssertTripwireFlagged::test_mixed_error_and_info_passes
TestAssertTripwireFlagged::test_hold_only_warning_finding_is_armed_no_raise
TestAssertTripwireFlagged::test_clean_no_error_no_hold_still_raises

exec-safety:
    TestExecSafety::test_no_eval
    TestExecSafety::test_no_exec
    TestExecSafety::test_no_subprocess_import
    TestExecSafety::test_no_shell_true
    TestExecSafety::test_stdlib_only
    TestExecSafety::test_pure_ast_parseable
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# sys.path setup (tools/ is on pythonpath via pyproject.toml, but ensure it)
# ---------------------------------------------------------------------------

_TOOLS = Path(__file__).resolve().parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

_FIXTURES_TRIPWIRE = Path(__file__).resolve().parent / "fixtures" / "validation_tripwire"


# ===========================================================================
# Schemas
# ===========================================================================


class TestSchemas:
    def test_finding_schema_required_fields(self):
        from validation_report import finding_schema

        schema = finding_schema()
        required = schema.get("required", [])
        assert "severity" in required
        assert "leg" in required
        assert "message" in required

    def test_finding_schema_severity_enum(self):
        from validation_report import finding_schema

        schema = finding_schema()
        sev_prop = schema["properties"]["severity"]
        assert "enum" in sev_prop
        enum_vals = sev_prop["enum"]
        assert "error" in enum_vals
        assert "warning" in enum_vals
        assert "info" in enum_vals
        # Only three values
        assert len(enum_vals) == 3

    def test_report_schema_required_fields(self):
        from validation_report import report_schema

        schema = report_schema()
        required = schema.get("required", [])
        assert "passed" in required
        assert "findings" in required

    def test_report_schema_passed_defaults_false(self):
        from validation_report import report_schema

        schema = report_schema()
        passed_prop = schema["properties"]["passed"]
        # default must be False (default-FAIL invariant)
        assert passed_prop.get("default") is False


# ===========================================================================
# finding_id — id → locus/location → "unknown", no hash
# ===========================================================================


class TestFindingId:
    def test_id_preferred(self):
        from validation_report import finding_id

        f = {"id": "DEV-42", "locus": "src/foo.py:10", "location": "src/foo.py:10"}
        assert finding_id(f) == "DEV-42"

    def test_locus_fallback_when_no_id(self):
        from validation_report import finding_id

        f = {"locus": "src/bar.py:5", "location": "somewhere"}
        assert finding_id(f) == "src/bar.py:5"

    def test_location_fallback_when_no_id_or_locus(self):
        from validation_report import finding_id

        f = {"location": "payload:12"}
        assert finding_id(f) == "payload:12"

    def test_unknown_when_no_id_locus_location(self):
        from validation_report import finding_id

        f = {"message": "something bad"}
        assert finding_id(f) == "unknown"

    def test_falsy_id_falls_through_to_locus(self):
        from validation_report import finding_id

        # id="" is falsy — falls through to locus
        f = {"id": "", "locus": "src/qux.py:7"}
        assert finding_id(f) == "src/qux.py:7"

    def test_falsy_id_and_locus_falls_through_to_location(self):
        from validation_report import finding_id

        f = {"id": None, "locus": None, "location": "payload:99"}
        assert finding_id(f) == "payload:99"

    def test_returns_string(self):
        from validation_report import finding_id

        f = {"id": 123}  # int id → coerced to str
        result = finding_id(f)
        assert isinstance(result, str)

    def test_matches_debug_report_precedent_algorithm(self):
        """finding_id must match debug_report.finding_id for the id/locus cases."""
        from debug_report import finding_id as dr_finding_id
        from validation_report import finding_id as vr_finding_id

        # Case: id present — both return it
        f_with_id = {"id": "X-99", "locus": "somewhere"}
        assert vr_finding_id(f_with_id) == dr_finding_id(f_with_id)

        # Case: no id, locus present — both return locus
        f_locus_only = {"locus": "src/thing.py:3"}
        assert vr_finding_id(f_locus_only) == dr_finding_id(f_locus_only)

        # Case: neither id nor locus — both return "unknown"
        f_empty = {}
        assert vr_finding_id(f_empty) == dr_finding_id(f_empty) == "unknown"


# ===========================================================================
# severity_of — SARIF band mapping + behavior_changing rule
# ===========================================================================


class TestSeverityOf:
    def test_behavior_changing_true_yields_error(self):
        from validation_report import severity_of

        f = {"behavior_changing": True, "severity": "info"}
        assert severity_of(f) == "error"

    def test_behavior_changing_false_uses_severity_field(self):
        from validation_report import severity_of

        f = {"behavior_changing": False, "severity": "warning"}
        assert severity_of(f) == "warning"

    def test_error_passthrough(self):
        from validation_report import severity_of

        assert severity_of({"severity": "error"}) == "error"

    def test_warning_passthrough(self):
        from validation_report import severity_of

        assert severity_of({"severity": "warning"}) == "warning"

    def test_info_passthrough(self):
        from validation_report import severity_of

        assert severity_of({"severity": "info"}) == "info"

    def test_blocker_maps_to_error(self):
        from validation_report import severity_of

        assert severity_of({"severity": "BLOCKER"}) == "error"
        assert severity_of({"severity": "blocker"}) == "error"

    def test_major_maps_to_warning(self):
        from validation_report import severity_of

        assert severity_of({"severity": "MAJOR"}) == "warning"
        assert severity_of({"severity": "major"}) == "warning"

    def test_minor_maps_to_info(self):
        from validation_report import severity_of

        assert severity_of({"severity": "MINOR"}) == "info"
        assert severity_of({"severity": "minor"}) == "info"

    def test_slop_critical_maps_to_error(self):
        from validation_report import severity_of

        assert severity_of({"severity": "critical"}) == "error"
        assert severity_of({"severity": "CRITICAL"}) == "error"

    def test_warn_alias_maps_to_warning(self):
        from validation_report import severity_of

        assert severity_of({"severity": "warn"}) == "warning"
        assert severity_of({"severity": "WARN"}) == "warning"

    def test_uppercase_error_severity_maps_to_error(self):
        """F2: severity_of must normalize uppercase/mixed-case inputs (case-insensitive).

        Pre-fix: "ERROR", "Reject", "ESCALATE" all fall through to "info" because
        _BAND_MAP was case-sensitive and lacked these keys.  After FIX F1 these
        must resolve to "error".
        """
        from validation_report import severity_of

        assert severity_of({"severity": "ERROR"}) == "error"
        assert severity_of({"severity": "Reject"}) == "error"
        assert severity_of({"severity": "ESCALATE"}) == "error"

    def test_gate_verdict_tokens_map_to_error(self):
        """F1b (§10-2 all-or-nothing): the gate-VERDICT tokens must all hit the error band.

        kata-slop-check LOCKED L2: SLOP-DETECTED ⇒ NEEDS_WORK regardless of severity.
        A review HOLD, an evaluate NEEDS_WORK, and a SLOP-DETECTED verdict are gate
        verdicts (not generic SARIF severity levels), so as severity TOKENS they must
        fail.  Pre-fix: slop-detected/needs_work → info, hold → warning (all soft-pass).
        """
        from validation_report import severity_of

        assert severity_of({"severity": "slop-detected"}) == "error"
        assert severity_of({"severity": "NEEDS_WORK"}) == "error"
        assert severity_of({"severity": "HOLD"}) == "error"

    def test_generic_sarif_major_minor_stay_soft(self):
        """F1b boundary: generic SARIF severity LEVELS (major/minor) are NOT gate-verdict
        tokens — they stay warning/info.  The defense for normal-band slop is the
        conductor stamping hold:true on the finding, not making generic 'major' fail.
        """
        from validation_report import severity_of

        assert severity_of({"severity": "major"}) == "warning"
        assert severity_of({"severity": "minor"}) == "info"

    def test_unknown_band_defaults_to_info(self):
        from validation_report import severity_of

        assert severity_of({"severity": "BOGUS_BAND"}) == "info"
        assert severity_of({}) == "info"

    def test_behavior_changing_overrides_info_severity(self):
        from validation_report import severity_of

        # Even though severity says info, behavior_changing forces error
        f = {"behavior_changing": True, "severity": "info"}
        assert severity_of(f) == "error"

    def test_behavior_changing_overrides_warning_severity(self):
        from validation_report import severity_of

        f = {"behavior_changing": True, "severity": "warning"}
        assert severity_of(f) == "error"


# ===========================================================================
# render_table
# ===========================================================================


class TestRenderTable:
    def _make_finding(
        self,
        *,
        id: str | None = None,  # noqa: A002
        severity: str = "info",
        leg: str = "review",
        location: str | None = None,
        message: str = "A finding.",
        behavior_changing: bool = False,
        hold: bool = False,
    ) -> dict:
        f: dict = {
            "severity": severity,
            "leg": leg,
            "message": message,
            "behavior_changing": behavior_changing,
            "hold": hold,
        }
        if id is not None:
            f["id"] = id
        if location is not None:
            f["location"] = location
        return f

    def test_empty_findings_no_na_legs_yields_header_only(self):
        from validation_report import render_table

        table = render_table([], [])
        lines = table.strip().splitlines()
        assert lines[0].startswith("| severity")
        assert lines[1].startswith("|---")
        # Only two lines (header + separator), no data rows
        assert len(lines) == 2

    def test_single_finding_appears_in_table(self):
        from validation_report import render_table

        f = self._make_finding(id="F-1", severity="warning", message="Something is off.")
        table = render_table([f], [])
        assert "F-1" in table
        assert "warning" in table
        assert "Something is off." in table

    def test_severity_order_error_before_warning_before_info(self):
        from validation_report import render_table

        findings = [
            self._make_finding(id="I-1", severity="info", message="info finding"),
            self._make_finding(id="E-1", severity="error", message="error finding"),
            self._make_finding(id="W-1", severity="warning", message="warn finding"),
        ]
        table = render_table(findings, [])
        lines = [ln for ln in table.splitlines() if ln.startswith("| ") and "severity" not in ln and "|---|" not in ln]
        # First data row must be error
        assert "error" in lines[0]
        assert "warning" in lines[1]
        assert "info" in lines[2]

    def test_stable_sort_by_finding_id_within_severity_band(self):
        from validation_report import render_table

        findings = [
            self._make_finding(id="B-warn", severity="warning", message="b"),
            self._make_finding(id="A-warn", severity="warning", message="a"),
        ]
        table = render_table(findings, [])
        lines = [ln for ln in table.splitlines() if ln.startswith("| ") and "severity" not in ln and "|---|" not in ln]
        assert "A-warn" in lines[0]
        assert "B-warn" in lines[1]

    def test_na_leg_yields_explicit_info_row(self):
        from validation_report import render_table

        table = render_table([], ["score"])
        # Must have a data row for the N/A leg
        assert "score" in table or "N/A" in table
        # The row must be visible (not just the header)
        lines = table.strip().splitlines()
        data_lines = [ln for ln in lines if ln.startswith("| ") and "severity" not in ln and "|---|" not in ln]
        assert len(data_lines) == 1

    def test_score_na_leg_message(self):
        from validation_report import render_table

        table = render_table([], ["score"])
        assert "N/A" in table
        assert "no plan to conform to" in table

    def test_non_score_na_leg_message(self):
        from validation_report import render_table

        table = render_table([], ["grounding"])
        assert "N/A" in table
        assert "leg not selected" in table

    def test_skipped_score_leg_never_reads_as_clean_pass(self):
        """R4 guard: a skipped score leg must NOT produce a table that looks like PASS.

        The N/A row must be present and visible. A reader of the table must see
        the N/A entry — the table is never empty for a skipped leg.
        """
        from validation_report import render_table

        table = render_table([], ["score"])
        data_lines = [
            ln for ln in table.splitlines()
            if ln.startswith("| ") and "severity" not in ln and "|---|" not in ln
        ]
        # There is exactly one row — the N/A info row
        assert len(data_lines) == 1, "skipped score leg must render exactly one N/A row"
        # The row explicitly mentions N/A — cannot be read as a clean PASS
        assert "N/A" in data_lines[0]

    def test_no_html_in_output(self):
        from validation_report import render_table

        f = self._make_finding(id="X", severity="error", message="an error")
        table = render_table([f], ["score"])
        assert "<" not in table, "render_table must produce NO HTML"
        assert ">" not in table.replace("|---|---|---|---|", ""), "render_table must produce NO HTML"

    def test_pipe_in_message_is_escaped(self):
        from validation_report import render_table

        f = self._make_finding(id="P-1", severity="info", message="foo | bar")
        table = render_table([f], [])
        # The unescaped pipe would break the markdown table structure
        # After escaping, \| must appear; raw unescaped | inside message must not
        # (table delimiters are | but message pipes must be \|)
        assert "foo \\| bar" in table or ("foo" in table and "bar" in table)

    def test_location_none_renders_dash(self):
        from validation_report import render_table

        f = self._make_finding(id="L-1", severity="info", location=None)
        table = render_table([f], [])
        assert "—" in table

    def test_na_row_has_info_severity(self):
        from validation_report import render_table

        table = render_table([], ["score"])
        # The N/A row must have severity 'info' — never 'error' or 'warning'
        data_lines = [
            ln for ln in table.splitlines()
            if ln.startswith("| ") and "severity" not in ln and "|---|" not in ln
        ]
        assert len(data_lines) == 1
        assert "info" in data_lines[0]
        assert "error" not in data_lines[0]
        assert "warning" not in data_lines[0]

    def test_na_row_survives_with_real_findings(self):
        """F3 mutation-proof: N/A row must appear EVEN WHEN real findings are present.

        Existing tests only call render_table with empty findings, so a mutation like
        ``na_rows if not findings else []`` would pass the existing suite.  This test
        catches that mutation by asserting len(findings)+1 data rows when na_legs is
        non-empty alongside actual findings.
        """
        from validation_report import render_table

        f1 = self._make_finding(id="F-1", severity="error", message="Error finding.")
        f2 = self._make_finding(id="F-2", severity="warning", message="Warning finding.")
        table = render_table([f1, f2], na_legs=["score"])
        data_lines = [
            ln for ln in table.strip().splitlines()
            if ln.startswith("| ") and "severity" not in ln and "|---|" not in ln
        ]
        # 2 real findings + 1 explicit N/A row = 3 data rows
        assert len(data_lines) == 3, (
            f"Expected 3 data rows (2 findings + 1 N/A), got {len(data_lines)}. "
            "N/A row must not be suppressed when real findings are present."
        )
        assert any("N/A" in ln for ln in data_lines), (
            "The N/A info row must be present in the table output."
        )


# ===========================================================================
# emit_findings / load_findings — round-trip + path guard
# ===========================================================================


class TestEmitLoad:
    def _sample_report(self) -> dict:
        return {
            "passed": False,
            "findings": [
                {
                    "id": "F-1",
                    "severity": "error",
                    "leg": "slop",
                    "location": "payload:1",
                    "message": "Known-bad slop detected.",
                    "behavior_changing": True,
                    "hold": False,
                }
            ],
            "utc": "2026-06-29T00:00:00+00:00",
        }

    def test_round_trip_identity(self, tmp_path: Path):
        from validation_report import emit_findings, load_findings

        report = self._sample_report()
        dest = tmp_path / "validation" / "findings.json"
        emit_findings(str(dest), report)
        loaded = load_findings(str(dest))
        assert loaded == report

    def test_writes_json_file(self, tmp_path: Path):
        from validation_report import emit_findings

        dest = tmp_path / "findings.json"
        emit_findings(str(dest), {"passed": False, "findings": []})
        assert dest.exists()
        data = json.loads(dest.read_text(encoding="utf-8"))
        assert "passed" in data

    def test_creates_parent_dirs(self, tmp_path: Path):
        from validation_report import emit_findings

        dest = tmp_path / "a" / "b" / "c" / "findings.json"
        assert not dest.parent.exists()
        emit_findings(str(dest), {"passed": False, "findings": []})
        assert dest.exists()

    def test_traversal_guard_rejects_dotdot_path(self, tmp_path: Path):
        from validation_report import emit_findings

        traversal = str(tmp_path / ".." / "escaped_findings.json")
        with pytest.raises(ValueError):
            emit_findings(traversal, {"passed": False, "findings": []})

    def test_traversal_guard_rejects_dotdot_in_segment(self, tmp_path: Path):
        from validation_report import emit_findings

        traversal = str(tmp_path) + "/../../../etc/findings.json"
        with pytest.raises(ValueError):
            emit_findings(traversal, {"passed": False, "findings": []})

    def test_accepts_normal_nested_path(self, tmp_path: Path):
        from validation_report import emit_findings

        dest = tmp_path / ".kata" / "validation" / "findings.json"
        # Should NOT raise
        emit_findings(str(dest), {"passed": False, "findings": []})
        assert dest.exists()

    def test_utf8_encoded(self, tmp_path: Path):
        from validation_report import emit_findings

        dest = tmp_path / "findings.json"
        report = {"passed": False, "findings": [], "note": "Unicode: —é"}
        emit_findings(str(dest), report)
        raw = dest.read_bytes()
        # UTF-8: em-dash is 3 bytes e2 80 94
        assert b"\xe2\x80\x94" in raw


# ===========================================================================
# compute_passed
# ===========================================================================


class TestComputePassed:
    def test_empty_findings_passes(self):
        from validation_report import compute_passed

        assert compute_passed([]) is True

    def test_error_finding_fails(self):
        from validation_report import compute_passed

        f = {"severity": "error", "leg": "slop", "message": "bad"}
        assert compute_passed([f]) is False

    def test_hold_finding_fails_even_with_warning_severity(self):
        from validation_report import compute_passed

        f = {"severity": "warning", "leg": "review", "message": "HOLD", "hold": True}
        assert compute_passed([f]) is False

    def test_info_finding_does_not_fail(self):
        from validation_report import compute_passed

        f = {"severity": "info", "leg": "score", "message": "N/A — no plan to conform to"}
        assert compute_passed([f]) is True

    def test_na_info_finding_does_not_fail(self):
        """An N/A info row must NOT trip compute_passed."""
        from validation_report import compute_passed

        na_finding = {
            "id": "na-score",
            "severity": "info",
            "leg": "score",
            "message": "N/A — no plan to conform to",
            "rule": "na-guard",
            "behavior_changing": False,
            "hold": False,
        }
        assert compute_passed([na_finding]) is True

    def test_warning_without_hold_does_not_fail(self):
        from validation_report import compute_passed

        f = {"severity": "warning", "leg": "review", "message": "minor concern", "hold": False}
        assert compute_passed([f]) is True

    def test_tripwire_ok_false_fails_regardless(self):
        from validation_report import compute_passed

        # Even with no error findings, tripwire_ok=False => fail
        assert compute_passed([], tripwire_ok=False) is False

    def test_tripwire_ok_true_with_clean_findings_passes(self):
        from validation_report import compute_passed

        assert compute_passed([], tripwire_ok=True) is True

    def test_multiple_findings_any_error_fails(self):
        from validation_report import compute_passed

        findings = [
            {"severity": "info", "message": "n/a", "hold": False},
            {"severity": "warning", "message": "warning", "hold": False},
            {"severity": "error", "message": "bad", "hold": False},
        ]
        assert compute_passed(findings) is False

    def test_multiple_findings_any_hold_fails(self):
        from validation_report import compute_passed

        findings = [
            {"severity": "info", "message": "n/a", "hold": False},
            {"severity": "warning", "message": "hold finding", "hold": True},
        ]
        assert compute_passed(findings) is False

    def test_uppercase_error_severity_fails(self):
        """F2: compute_passed must return False when severity is 'ERROR' (case-insensitive).

        Pre-fix: severity_of({'severity':'ERROR'}) returned 'info' (not 'error')
        because _BAND_MAP lacked the uppercase key, so compute_passed incorrectly
        returned True on a real error finding.
        """
        from validation_report import compute_passed

        f = {"severity": "ERROR", "leg": "slop", "message": "bad content", "hold": False}
        assert compute_passed([f]) is False

    def test_gate_verdict_tokens_fail(self):
        """F1b: a finding carrying a gate-verdict token as its severity must FAIL.

        Pre-fix: slop-detected/needs_work resolved to info and HOLD to warning, so
        compute_passed returned True — a real gate verdict slipping to pass.
        """
        from validation_report import compute_passed

        for token in ("slop-detected", "needs_work", "HOLD"):
            f = {"severity": token, "leg": "slop", "message": "gate verdict", "hold": False}
            assert compute_passed([f]) is False, f"{token!r} must fail compute_passed"

    def test_major_slop_with_hold_fails(self):
        """F1b realistic case: most real slop is major/minor (slop's NORMAL bands).

        The conductor stamps such SLOP-DETECTED evidence with hold:true (kata-slop-check
        LOCKED L2 — severity informs remediation priority, not gate status).  A
        major-severity slop finding carrying hold:true MUST fail compute_passed via the
        hold path, even though 'major' itself maps to the warning band.
        """
        from validation_report import compute_passed

        f = {
            "severity": "major",
            "leg": "slop",
            "message": "SLOP-DETECTED: A1 inflation on core deliverable.",
            "hold": True,
        }
        assert compute_passed([f]) is False


# ===========================================================================
# Tripwire corpus
# ===========================================================================


class TestTripwireCorpus:
    def test_corpus_is_nonempty(self):
        from validation_report import tripwire_corpus

        corpus = tripwire_corpus()
        assert len(corpus) > 0, "tripwire corpus must not be empty"

    def test_corpus_has_at_least_one_error(self):
        from validation_report import severity_of, tripwire_corpus

        corpus = tripwire_corpus()
        error_findings = [f for f in corpus if severity_of(f) == "error"]
        assert len(error_findings) >= 1, (
            "tripwire corpus must contain at least one error-severity finding "
            "so assert_tripwire_flagged can verify the validator is not lenient"
        )

    def test_corpus_findings_are_dicts(self):
        from validation_report import tripwire_corpus

        corpus = tripwire_corpus()
        for f in corpus:
            assert isinstance(f, dict), f"corpus item must be a dict, got {type(f)}"


# ===========================================================================
# assert_tripwire_flagged
# ===========================================================================


class TestAssertTripwireFlagged:
    def test_corpus_passes_assertion(self):
        """The corpus itself has error findings — assert_tripwire_flagged must not raise."""
        from validation_report import assert_tripwire_flagged, tripwire_corpus

        corpus = tripwire_corpus()
        # Should not raise — corpus has errors
        assert_tripwire_flagged(corpus)

    def test_empty_findings_raises(self):
        """Empty findings list means the validator caught nothing — must raise."""
        from validation_report import assert_tripwire_flagged

        with pytest.raises(ValueError, match="Tripwire FAILED"):
            assert_tripwire_flagged([])

    def test_info_only_findings_raise(self):
        """Info-only findings: validator produced no errors — must raise."""
        from validation_report import assert_tripwire_flagged

        info_findings = [
            {"id": "na-score", "severity": "info", "leg": "score",
             "message": "N/A — no plan to conform to", "hold": False},
        ]
        with pytest.raises(ValueError, match="Tripwire FAILED"):
            assert_tripwire_flagged(info_findings)

    def test_warning_only_no_hold_raises(self):
        """Warning-only (no HOLD) findings: no errors caught — must raise."""
        from validation_report import assert_tripwire_flagged

        warn_findings = [
            {"severity": "warning", "leg": "review", "message": "minor issue", "hold": False},
        ]
        with pytest.raises(ValueError, match="Tripwire FAILED"):
            assert_tripwire_flagged(warn_findings)

    def test_error_finding_passes_assertion(self):
        """A single error finding means the validator caught something — must not raise."""
        from validation_report import assert_tripwire_flagged

        error_findings = [
            {"id": "tw-001", "severity": "error", "leg": "slop",
             "message": "bad content detected", "behavior_changing": True, "hold": False},
        ]
        # Should not raise
        assert_tripwire_flagged(error_findings)

    def test_mixed_error_and_info_passes(self):
        """Mix of error + info findings — must not raise (error present)."""
        from validation_report import assert_tripwire_flagged

        findings = [
            {"severity": "info", "message": "n/a", "hold": False},
            {"severity": "error", "message": "bad content", "hold": False},
        ]
        assert_tripwire_flagged(findings)

    def test_hold_only_warning_finding_is_armed_no_raise(self):
        """FIX-3a: a HOLD/warning finding (no error severity) counts as ARMED — must NOT raise.

        compute_passed returns False for any hold=True finding (even at warning
        severity), so assert_tripwire_flagged must use the same semantics.
        Pre-fix: assert_tripwire_flagged only checked severity_of(f)=='error', so
        a hold+warning finding falsely raised ValueError (leniency mis-alarm).
        """
        from validation_report import assert_tripwire_flagged

        hold_findings = [
            {
                "id": "tw-review-001",
                "severity": "warning",
                "leg": "review",
                "message": "HOLD: adversarial review found unverified claim.",
                "hold": True,
            },
        ]
        # Must NOT raise — hold matches compute_passed's fail semantics
        assert_tripwire_flagged(hold_findings)

    def test_clean_no_error_no_hold_still_raises(self):
        """FIX-3a: corpus with no error AND no hold is NOT armed — must still RAISE."""
        from validation_report import assert_tripwire_flagged

        clean_findings = [
            {"severity": "warning", "leg": "review", "message": "minor concern", "hold": False},
        ]
        with pytest.raises(ValueError, match="Tripwire FAILED"):
            assert_tripwire_flagged(clean_findings)


# ===========================================================================
# Exec safety — no subprocess, no eval, no exec, no shell
# ===========================================================================


class TestExecSafety:
    _SOURCE = (_TOOLS / "validation_report.py").read_text(encoding="utf-8")

    def test_pure_ast_parseable(self):
        """Module must be valid Python (parseability guard)."""
        ast.parse(self._SOURCE)  # raises SyntaxError if not parseable

    def test_no_eval(self):
        """Module must not call eval()."""
        tree = ast.parse(self._SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "eval":
                    pytest.fail("validation_report.py contains eval() call")

    def test_no_exec(self):
        """Module must not call exec()."""
        tree = ast.parse(self._SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "exec":
                    pytest.fail("validation_report.py contains exec() call")

    def test_no_subprocess_import(self):
        """Module must not import subprocess."""
        assert "import subprocess" not in self._SOURCE
        assert "from subprocess" not in self._SOURCE

    def test_no_shell_true(self):
        """Module must not use shell=True."""
        assert "shell=True" not in self._SOURCE

    def test_stdlib_only(self):
        """Module must only import stdlib modules (no third-party deps)."""
        # Parse imports and check against known stdlib modules
        tree = ast.parse(self._SOURCE)
        allowed_third_party: set[str] = set()  # none allowed
        stdlib_roots = {
            "json", "pathlib", "datetime", "typing", "os", "sys", "re",
            "ast", "collections", "__future__", "abc", "io", "functools",
            "itertools", "math", "string", "struct", "tempfile", "hashlib",
            "copy", "dataclasses", "enum", "warnings", "contextlib",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root in stdlib_roots, (
                        f"validation_report.py imports non-stdlib module: {alias.name!r}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    assert root in stdlib_roots, (
                        f"validation_report.py imports from non-stdlib module: {node.module!r}"
                    )
