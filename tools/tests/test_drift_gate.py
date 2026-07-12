"""test_drift_gate.py — TDD suite for tools/drift_gate.py (Slice F1, Phase P2b).

Strategy: default-FAIL (tests written before implementation; green only after
drift_gate.py is present and correct).  Mutation-proof tests use
mutation_run.prove_non_vacuous and spawn a real subprocess.  All other tests
are pure (no I/O except fixture loads and tmp_path writes).

Coverage map
------------
parse_test_outcomes:
    TestParseTestOutcomes::test_passed_lines_parsed_as_green
    TestParseTestOutcomes::test_failed_lines_parsed_as_red
    TestParseTestOutcomes::test_mixed_output_correct_map
    TestParseTestOutcomes::test_summary_failed_lines_not_double_counted
    TestParseTestOutcomes::test_empty_output_returns_empty_dict

classify_transitions:
    TestClassifyTransitions::test_green_green
    TestClassifyTransitions::test_green_red
    TestClassifyTransitions::test_red_green
    TestClassifyTransitions::test_red_red
    TestClassifyTransitions::test_added
    TestClassifyTransitions::test_removed
    TestClassifyTransitions::test_all_classes_present

validate_allowed_exceptions:
    TestValidateAllowedExceptions::test_empty_ael_is_valid
    TestValidateAllowedExceptions::test_red_in_before_is_valid
    TestValidateAllowedExceptions::test_green_in_before_is_rejected
    TestValidateAllowedExceptions::test_unknown_entry_is_rejected
    TestValidateAllowedExceptions::test_valid_false_when_any_rejected
    TestValidateAllowedExceptions::test_rejected_list_populated
    TestValidateAllowedExceptions::test_mixed_valid_and_invalid

drift_verdict:
    TestDriftVerdict::test_blocks_injected_regression (seeded fixture)
    TestDriftVerdict::test_passes_nominated_fix (seeded fixture)
    TestDriftVerdict::test_ael_green_in_before_blocks
    TestDriftVerdict::test_ael_unknown_entry_blocks
    TestDriftVerdict::test_ael_still_red_blocks
    TestDriftVerdict::test_no_ael_all_green_passes
    TestDriftVerdict::test_multiple_regressions_all_in_blocking
    TestDriftVerdict::test_ael_valid_afl_test_passes
    TestDriftVerdict::test_red_red_does_not_block

empty-baseline guard (finding Q-1, 2026-07-12 health review):
    TestEmptyBaselineGuard::test_empty_before_empty_ael_blocks
    TestEmptyBaselineGuard::test_empty_before_empty_after_empty_ael_blocks
    TestEmptyBaselineGuard::test_empty_before_nonempty_ael_blocks_as_empty_baseline

deterministic ordering (finding DET-07):
    TestDeterministicOrdering::test_classify_transitions_keys_sorted
    TestDeterministicOrdering::test_drift_verdict_insertion_order_invariant

scrub_nondeterminism / snapshots_match:
    TestScrubAndSnapshots::test_scrubs_iso_timestamp
    TestScrubAndSnapshots::test_scrubs_uuid
    TestScrubAndSnapshots::test_scrubs_hex_address
    TestScrubAndSnapshots::test_nondeterministic_snapshots_match
    TestScrubAndSnapshots::test_real_divergence_does_not_match
    TestScrubAndSnapshots::test_no_scrub_flag_respects_raw_bytes
    TestScrubAndSnapshots::test_custom_patterns_used_when_provided

characterization_snapshot_verdict:
    TestSnapshotVerdict::test_identical_snapshots_pass
    TestSnapshotVerdict::test_snapshot_changed_outside_ael_blocks
    TestSnapshotVerdict::test_snapshot_changed_inside_ael_passes
    TestSnapshotVerdict::test_nondeterministic_snapshots_pass
    TestSnapshotVerdict::test_empty_snaps_pass

defer_record / emit_deferrals:
    TestDeferrals::test_defer_record_has_required_keys
    TestDeferrals::test_defer_record_finding_id_from_locus
    TestDeferrals::test_emit_deferrals_round_trip
    TestDeferrals::test_emit_deferrals_creates_parent_dirs

build_drift_report / emit_drift_report / drift_schema:
    TestDriftReport::test_schema_required_keys
    TestDriftReport::test_schema_verdict_enum
    TestDriftReport::test_build_drift_report_pass_when_both_pass
    TestDriftReport::test_build_drift_report_block_when_behavioral_blocks
    TestDriftReport::test_build_drift_report_block_when_snapshot_blocks
    TestDriftReport::test_emit_drift_report_round_trip
    TestDriftReport::test_emit_drift_report_creates_parent_dirs

structural_drift_verdict seam:
    TestStructuralDriftVerdictSeam::test_raises_not_implemented
    TestStructuralDriftVerdictSeam::test_docstring_states_limitation

exec-safety:
    TestExecSafety::test_no_eval_in_drift_gate_py
    TestExecSafety::test_no_exec_in_drift_gate_py
    TestExecSafety::test_no_subprocess_import_in_drift_gate_py
    TestExecSafety::test_no_shell_true_in_drift_gate_py
    TestExecSafety::test_drift_gate_py_is_pure_ast_parseable

Mutation proofs (spawn real subprocess via prove_non_vacuous):
    TestMutationProof::test_mutation_proof_green_red_block_branch
    TestMutationProof::test_mutation_proof_ael_green_in_before_rejection
    TestMutationProof::test_mutation_proof_ael_must_flip_red_to_green
    TestMutationProof::test_mutation_proof_snapshot_changed_outside_ael
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parent.parent
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "drift_gate"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _load_json(name: str) -> dict:
    """Load a seeded JSON fixture from the drift_gate fixtures directory."""
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def _load_text(name: str) -> str:
    """Load a seeded text fixture from the drift_gate fixtures directory."""
    return (_FIXTURES / name).read_text(encoding="utf-8")


def _before_outcomes() -> dict[str, str]:
    """Load and strip _comment from the before_outcomes fixture."""
    d = _load_json("before_outcomes.json")
    return {k: v for k, v in d.items() if not k.startswith("_")}


def _after_regression() -> dict[str, str]:
    """Load and strip _comment from the after_outcomes_regression fixture."""
    d = _load_json("after_outcomes_regression.json")
    return {k: v for k, v in d.items() if not k.startswith("_")}


def _after_fix() -> dict[str, str]:
    """Load and strip _comment from the after_outcomes_fix fixture."""
    d = _load_json("after_outcomes_fix.json")
    return {k: v for k, v in d.items() if not k.startswith("_")}


# AEL constant — the test nominated as the buggy test being fixed
_AEL_TEST = "tests/test_example.py::test_nominated_buggy"


# ---------------------------------------------------------------------------
# parse_test_outcomes
# ---------------------------------------------------------------------------


class TestParseTestOutcomes:
    def test_passed_lines_parsed_as_green(self):
        """A PASSED line produces a 'green' entry in the outcome map."""
        import drift_gate as dg
        output = "tests/test_foo.py::test_bar PASSED                      [ 50%]\n"
        result = dg.parse_test_outcomes(output)
        assert result.get("tests/test_foo.py::test_bar") == "green"

    def test_failed_lines_parsed_as_red(self):
        """A FAILED line produces a 'red' entry in the outcome map."""
        import drift_gate as dg
        output = "tests/test_foo.py::test_baz FAILED                      [100%]\n"
        result = dg.parse_test_outcomes(output)
        assert result.get("tests/test_foo.py::test_baz") == "red"

    def test_mixed_output_correct_map(self):
        """The seeded parse_output_sample.txt maps the three tests correctly."""
        import drift_gate as dg
        output = _load_text("parse_output_sample.txt")
        result = dg.parse_test_outcomes(output)
        assert result.get("tests/test_example.py::test_feature_a") == "green"
        assert result.get("tests/test_example.py::test_feature_b") == "green"
        assert result.get("tests/test_example.py::test_nominated_buggy") == "red"

    def test_summary_failed_lines_not_double_counted(self):
        """Lines starting with 'FAILED tests/...' (summary) must not be double-counted."""
        import drift_gate as dg
        output = _load_text("parse_output_sample.txt")
        result = dg.parse_test_outcomes(output)
        # test_nominated_buggy should appear exactly once (as "red"), not twice
        assert list(result.values()).count("red") == 1

    def test_empty_output_returns_empty_dict(self):
        """Empty string produces an empty outcome map."""
        import drift_gate as dg
        assert dg.parse_test_outcomes("") == {}


# ---------------------------------------------------------------------------
# classify_transitions
# ---------------------------------------------------------------------------


class TestClassifyTransitions:
    def test_green_green(self):
        """Green in both before and after → green->green."""
        import drift_gate as dg
        result = dg.classify_transitions({"t": "green"}, {"t": "green"})
        assert result["t"] == "green->green"

    def test_green_red(self):
        """Green before, red after → green->red."""
        import drift_gate as dg
        result = dg.classify_transitions({"t": "green"}, {"t": "red"})
        assert result["t"] == "green->red"

    def test_red_green(self):
        """Red before, green after → red->green."""
        import drift_gate as dg
        result = dg.classify_transitions({"t": "red"}, {"t": "green"})
        assert result["t"] == "red->green"

    def test_red_red(self):
        """Red in both → red->red."""
        import drift_gate as dg
        result = dg.classify_transitions({"t": "red"}, {"t": "red"})
        assert result["t"] == "red->red"

    def test_added(self):
        """Test only in after → added."""
        import drift_gate as dg
        result = dg.classify_transitions({}, {"t": "green"})
        assert result["t"] == "added"

    def test_removed(self):
        """Test only in before → removed."""
        import drift_gate as dg
        result = dg.classify_transitions({"t": "green"}, {})
        assert result["t"] == "removed"

    def test_all_classes_present(self):
        """All six transition classes appear in the fixture set."""
        import drift_gate as dg
        before = {
            "t_gg": "green",
            "t_gr": "green",
            "t_rg": "red",
            "t_rr": "red",
            "t_rm": "green",
        }
        after = {
            "t_gg": "green",
            "t_gr": "red",
            "t_rg": "green",
            "t_rr": "red",
            "t_ad": "green",
        }
        result = dg.classify_transitions(before, after)
        assert result["t_gg"] == "green->green"
        assert result["t_gr"] == "green->red"
        assert result["t_rg"] == "red->green"
        assert result["t_rr"] == "red->red"
        assert result["t_rm"] == "removed"
        assert result["t_ad"] == "added"


# ---------------------------------------------------------------------------
# validate_allowed_exceptions
# ---------------------------------------------------------------------------


class TestValidateAllowedExceptions:
    def test_empty_ael_is_valid(self):
        """Empty AEL with any before map → valid:True, rejected:[]."""
        import drift_gate as dg
        result = dg.validate_allowed_exceptions([], {"t": "green"})
        assert result["valid"] is True
        assert result["rejected"] == []

    def test_red_in_before_is_valid(self):
        """AEL entry that is RED in before → accepted."""
        import drift_gate as dg
        result = dg.validate_allowed_exceptions(["t"], {"t": "red"})
        assert result["valid"] is True
        assert result["rejected"] == []

    def test_green_in_before_is_rejected(self):
        """AEL entry that is GREEN in before → REJECTED (cannot authorize a green test to regress)."""
        import drift_gate as dg
        result = dg.validate_allowed_exceptions(["t"], {"t": "green"})
        assert result["valid"] is False
        assert "t" in result["rejected"]

    def test_unknown_entry_is_rejected(self):
        """AEL entry not present in before (unknown test) → REJECTED."""
        import drift_gate as dg
        result = dg.validate_allowed_exceptions(["unknown_test"], {})
        assert result["valid"] is False
        assert "unknown_test" in result["rejected"]

    def test_valid_false_when_any_rejected(self):
        """valid:False whenever rejected is non-empty."""
        import drift_gate as dg
        result = dg.validate_allowed_exceptions(["green_t", "red_t"], {"green_t": "green", "red_t": "red"})
        assert result["valid"] is False
        assert "green_t" in result["rejected"]
        assert "red_t" not in result["rejected"]

    def test_rejected_list_populated(self):
        """rejected list contains exactly the rejected entries."""
        import drift_gate as dg
        result = dg.validate_allowed_exceptions(["g1", "g2"], {"g1": "green", "g2": "green"})
        assert set(result["rejected"]) == {"g1", "g2"}

    def test_mixed_valid_and_invalid(self):
        """Mix of valid (red) and invalid (green/unknown) entries."""
        import drift_gate as dg
        allowed = ["red_test", "green_test", "unknown_test"]
        before = {"red_test": "red", "green_test": "green"}
        result = dg.validate_allowed_exceptions(allowed, before)
        assert result["valid"] is False
        assert "red_test" not in result["rejected"]
        assert "green_test" in result["rejected"]
        assert "unknown_test" in result["rejected"]


# ---------------------------------------------------------------------------
# drift_verdict
# ---------------------------------------------------------------------------


class TestDriftVerdict:
    """Core behavioral gate tests — use seeded fixtures for the main BLOCK/PASS cases."""

    def test_blocks_injected_regression(self):
        """Seeded fixture (a): a previously-GREEN test goes RED → verdict BLOCK.

        test_feature_a was green in before; the regression fixture sets it to red.
        Empty AEL (the regression is unrelated, not nominated).
        Expected: BLOCK with test_feature_a in blocking.
        """
        import drift_gate as dg
        before = _before_outcomes()
        after = _after_regression()
        result = dg.drift_verdict(before, after, allowed_exceptions=[])
        assert result["verdict"] == "BLOCK", (
            f"Expected BLOCK for injected regression; got {result['verdict']!r}. "
            f"Full result: {result}"
        )
        assert "tests/test_example.py::test_feature_a" in result["blocking"], (
            f"test_feature_a (the regressed test) must be in blocking; got {result['blocking']}"
        )

    def test_passes_nominated_fix(self):
        """Seeded fixture (b): AEL test flips RED→GREEN, all other greens stay green → PASS.

        AEL = [test_nominated_buggy]. test_nominated_buggy was RED in before, GREEN in after.
        test_feature_a and test_feature_b were and remain GREEN.
        Expected: PASS with test_nominated_buggy in flipped.
        """
        import drift_gate as dg
        before = _before_outcomes()
        after = _after_fix()
        result = dg.drift_verdict(before, after, allowed_exceptions=[_AEL_TEST])
        assert result["verdict"] == "PASS", (
            f"Expected PASS for nominated fix; got {result['verdict']!r}. "
            f"Full result: {result}"
        )
        assert _AEL_TEST in result["flipped"], (
            f"AEL test must be in flipped; got {result['flipped']}"
        )
        assert result["blocking"] == []

    def test_ael_green_in_before_blocks(self):
        """AEL entry that was GREEN in before → validate_allowed_exceptions rejects → BLOCK.

        A fix worker cannot authorize a green test to regress — this is the
        load-bearing AEL integrity guard.
        """
        import drift_gate as dg
        before = {"t_green": "green", "t_buggy": "red"}
        after = {"t_green": "green", "t_buggy": "green"}
        # Trying to put the green test on the AEL — must be rejected
        result = dg.drift_verdict(before, after, allowed_exceptions=["t_green"])
        assert result["verdict"] == "BLOCK", (
            "AEL entry GREEN-in-before must cause BLOCK; the integrity guard must bite"
        )
        assert "t_green" in result["blocking"]

    def test_ael_unknown_entry_blocks(self):
        """AEL entry not in before (unknown) → validate_allowed_exceptions rejects → BLOCK."""
        import drift_gate as dg
        before = {"t_a": "green"}
        after = {"t_a": "green"}
        result = dg.drift_verdict(before, after, allowed_exceptions=["completely_unknown_test"])
        assert result["verdict"] == "BLOCK"
        assert "completely_unknown_test" in result["blocking"]

    def test_ael_still_red_blocks(self):
        """AEL test stays RED after the fix → fix did not land → BLOCK.

        The AEL test is valid (was red in before), but it did not flip to green.
        This means the fix was not applied or did not take effect.
        """
        import drift_gate as dg
        before = {"t_buggy": "red", "t_stable": "green"}
        # After: t_buggy is STILL red (fix did not land)
        after = {"t_buggy": "red", "t_stable": "green"}
        result = dg.drift_verdict(before, after, allowed_exceptions=["t_buggy"])
        assert result["verdict"] == "BLOCK", (
            "AEL test still RED after fix → fix did not land → must BLOCK"
        )
        assert "t_buggy" in result["blocking"]

    def test_no_ael_all_green_passes(self):
        """No AEL, all green tests stay green → PASS (clean run)."""
        import drift_gate as dg
        before = {"t_a": "green", "t_b": "green"}
        after = {"t_a": "green", "t_b": "green"}
        result = dg.drift_verdict(before, after, allowed_exceptions=[])
        assert result["verdict"] == "PASS"
        assert result["blocking"] == []
        assert result["flipped"] == []

    def test_multiple_regressions_all_in_blocking(self):
        """Multiple green→red regressions (no AEL) → all appear in blocking list."""
        import drift_gate as dg
        before = {"t_a": "green", "t_b": "green", "t_c": "green"}
        after = {"t_a": "red", "t_b": "red", "t_c": "green"}
        result = dg.drift_verdict(before, after, allowed_exceptions=[])
        assert result["verdict"] == "BLOCK"
        assert "t_a" in result["blocking"]
        assert "t_b" in result["blocking"]
        assert "t_c" not in result["blocking"]

    def test_ael_valid_afl_test_passes(self):
        """AEL test is valid (red-in-before) and flips green → PASS."""
        import drift_gate as dg
        before = {"t_buggy": "red", "t_stable": "green"}
        after = {"t_buggy": "green", "t_stable": "green"}
        result = dg.drift_verdict(before, after, allowed_exceptions=["t_buggy"])
        assert result["verdict"] == "PASS"
        assert "t_buggy" in result["flipped"]
        assert result["blocking"] == []

    def test_red_red_does_not_block(self):
        """A test that was red in before and stays red does not cause a BLOCK."""
        import drift_gate as dg
        before = {"t_red": "red", "t_green": "green"}
        after = {"t_red": "red", "t_green": "green"}
        result = dg.drift_verdict(before, after, allowed_exceptions=[])
        # red→red is not a regression; AEL is empty → no AEL tests expected to flip
        assert result["verdict"] == "PASS"
        assert result["blocking"] == []

    # --- F1: fail-closed on vanished baseline-green tests ------------------

    def test_green_in_before_absent_from_after_blocks(self):
        """F1: a baseline-GREEN test that VANISHED from after → BLOCK (fail-closed).

        A green-in-before test that is deleted/renamed disappears from `after`.
        Under the old fail-open behavior it classified as "removed" and slipped
        through the gate, violating §5's "every baseline-green test stays green."
        It must BLOCK.
        """
        import drift_gate as dg
        before = {"t_a": "green", "t_b": "green"}
        after = {"t_a": "green"}  # t_b vanished entirely
        result = dg.drift_verdict(before, after, allowed_exceptions=[])
        assert result["verdict"] == "BLOCK", (
            f"A vanished baseline-green test must BLOCK; got {result}"
        )
        assert "t_b" in result["blocking"], (
            f"The vanished test t_b must be in blocking; got {result['blocking']}"
        )

    def test_green_in_before_errored_not_parsed_blocks(self):
        """F1: a baseline-GREEN test that ERRORed (absent from parsed outcomes) → BLOCK.

        parse_test_outcomes only captures PASSED/FAILED. A pytest ERROR or
        collection-failure leaves the test ABSENT from `after` (not "red").
        Such a test must NOT silently pass the behavioral gate.
        """
        import drift_gate as dg
        before = {"t_a": "green", "t_errored": "green"}
        # t_errored errored at collection → not present in parsed after-outcomes
        after = {"t_a": "green"}
        result = dg.drift_verdict(before, after, allowed_exceptions=[])
        assert result["verdict"] == "BLOCK", (
            f"A baseline-green test that errored (absent from after) must BLOCK; got {result}"
        )
        assert "t_errored" in result["blocking"]

    def test_red_in_before_absent_from_after_does_not_block_on_vanish_rule(self):
        """F1 boundary: a RED-in-before test vanishing is not a baseline-green concern.

        The fail-closed rule targets baseline-GREEN tests only. A red-in-before
        test absent from after is not flagged by the vanish rule (it was never a
        green baseline to protect). With an empty AEL → PASS.
        """
        import drift_gate as dg
        before = {"t_red": "red", "t_green": "green"}
        after = {"t_green": "green"}  # t_red (red-in-before) vanished
        result = dg.drift_verdict(before, after, allowed_exceptions=[])
        assert result["verdict"] == "PASS", (
            f"A vanished red-in-before test must not trip the green-vanish rule; got {result}"
        )
        assert result["blocking"] == []


# ---------------------------------------------------------------------------
# Q-1: empty-baseline guard (2026-07-12 health review)
# ---------------------------------------------------------------------------


class TestEmptyBaselineGuard:
    """Q-1: an EMPTY before map must never produce a vacuous PASS.

    parse_test_outcomes returns {} on unparseable runner output; without the
    Step 0 guard, drift_verdict({}, after, allowed_exceptions=[]) sailed
    through every check and returned PASS having certified NOTHING.  The guard
    must BLOCK with reason ``empty-baseline`` (mirroring the module's existing
    BLOCK-verdict idiom, not an exception).  Each test here asserts on that
    specific reason token, so deleting the guard makes these tests go red
    (the fall-through result is PASS with a different reason) — the guard is
    mutation-proven by construction.
    """

    def test_empty_before_empty_ael_blocks(self):
        """Q-1 core: empty before + empty AEL + non-empty after → BLOCK, not vacuous PASS."""
        import drift_gate as dg
        result = dg.drift_verdict({}, {"t_a": "green"}, allowed_exceptions=[])
        assert result["verdict"] == "BLOCK", (
            f"An empty baseline must BLOCK (vacuous-PASS defect Q-1); got {result}"
        )
        assert "empty-baseline" in result["reason"], (
            f"BLOCK reason must carry the 'empty-baseline' token; got {result['reason']!r}"
        )

    def test_empty_before_empty_after_empty_ael_blocks(self):
        """Q-1 exact scenario: BOTH runs unparseable ({} / {}) → BLOCK, never PASS."""
        import drift_gate as dg
        result = dg.drift_verdict({}, {}, allowed_exceptions=[])
        assert result["verdict"] == "BLOCK", (
            f"Two empty outcome maps certify nothing and must BLOCK; got {result}"
        )
        assert "empty-baseline" in result["reason"]
        assert result["flipped"] == []

    def test_empty_before_nonempty_ael_blocks_as_empty_baseline(self):
        """Empty before + NON-empty AEL → still BLOCK, with the empty-baseline reason.

        Decision (documented in drift_verdict Step 0): an empty baseline with a
        non-empty AEL is never legitimate — an AEL entry is valid only if it is
        RED-in-before, which is impossible against an empty baseline.  The
        guard fires FIRST so the reason names the true root cause (missing/
        unparseable baseline) rather than a misleading AEL-rejection.
        """
        import drift_gate as dg
        result = dg.drift_verdict(
            {}, {"t_buggy": "green"}, allowed_exceptions=["t_buggy"]
        )
        assert result["verdict"] == "BLOCK"
        assert "empty-baseline" in result["reason"], (
            "The empty-baseline guard must fire before the AEL integrity check "
            f"so the root cause is named; got {result['reason']!r}"
        )


# ---------------------------------------------------------------------------
# DET-07: deterministic ordering of transitions / blocking / reason
# ---------------------------------------------------------------------------


class TestDeterministicOrdering:
    """DET-07: verdict artifacts must be byte-stable across hash seeds / insertion order.

    classify_transitions previously iterated ``set(before) | set(after)``
    (PYTHONHASHSEED-ordered), so drift_verdict's blocking[] and concatenated
    reason — persisted into durable drift reports — were byte-unstable.  Both
    must now be deterministic (sorted iteration, mirroring
    characterization_snapshot_verdict).
    """

    def test_classify_transitions_keys_sorted(self):
        """classify_transitions returns keys in sorted order regardless of insertion order."""
        import drift_gate as dg
        # Build inputs in deliberately reversed insertion order
        ids = [f"tests/test_m.py::test_{c}" for c in "zyxwvutsrq"]
        before = {tid: "green" for tid in ids}
        after = {tid: "green" for tid in reversed(ids)}
        result = dg.classify_transitions(before, after)
        assert list(result) == sorted(result), (
            f"Transition keys must be sorted for determinism; got {list(result)}"
        )

    def test_drift_verdict_insertion_order_invariant(self):
        """Two calls with inputs built in different insertion orders → identical output.

        Covers both blocking sources: unallowed green→red regressions (Step 2)
        and vanished baseline-green tests (Step 2b).  The full result dicts —
        including blocking order and the concatenated reason string — must be
        byte-identical, and each blocking segment must be in sorted order.
        """
        import drift_gate as dg
        regressed = [f"t_reg_{c}" for c in "gcaebdfh"]      # green→red in after
        vanished = [f"t_gone_{c}" for c in "dcba"]          # green, absent from after
        stable = [f"t_ok_{i}" for i in range(8)]            # green→green

        def build(order: int) -> tuple[dict[str, str], dict[str, str]]:
            all_before = [(tid, "green") for tid in regressed + vanished + stable]
            all_after = [
                (tid, "red" if tid in regressed else "green")
                for tid in regressed + stable
            ]
            if order:  # reversed insertion order for the second call
                all_before = list(reversed(all_before))
                all_after = list(reversed(all_after))
            return dict(all_before), dict(all_after)

        before1, after1 = build(0)
        before2, after2 = build(1)
        result1 = dg.drift_verdict(before1, after1, allowed_exceptions=[])
        result2 = dg.drift_verdict(before2, after2, allowed_exceptions=[])

        assert result1 == result2, (
            "drift_verdict must be insertion-order invariant (DET-07); "
            f"got\n{result1}\nvs\n{result2}"
        )
        assert result1["verdict"] == "BLOCK"
        # Each blocking segment (Step 2 regressions, then Step 2b vanishes)
        # must itself be in sorted order — not just stable-by-accident.
        assert result1["blocking"] == sorted(regressed) + sorted(vanished), (
            f"blocking must be deterministically sorted per segment; got {result1['blocking']}"
        )


# ---------------------------------------------------------------------------
# scrub_nondeterminism / snapshots_match
# ---------------------------------------------------------------------------


class TestScrubAndSnapshots:
    def test_scrubs_iso_timestamp(self):
        """ISO 8601 timestamps are replaced by the placeholder."""
        import drift_gate as dg
        scrubbed = dg.scrub_nondeterminism("computed_at: 2024-01-15T10:30:00Z")
        assert "2024-01-15T10:30:00Z" not in scrubbed
        assert "<scrubbed>" in scrubbed

    def test_scrubs_uuid(self):
        """UUIDs (8-4-4-4-12) are replaced by the placeholder."""
        import drift_gate as dg
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        scrubbed = dg.scrub_nondeterminism(f"session_id: {uuid}")
        assert uuid not in scrubbed
        assert "<scrubbed>" in scrubbed

    def test_scrubs_hex_address(self):
        """Object-repr memory addresses ('<... at 0x...>') are replaced (F2: narrow form).

        Only the Python object-repr ``at 0x...`` form is scrubbed — a BARE hex
        literal is deliberately NOT scrubbed (see TestNarrowScrub) so real hex
        values are not masked.
        """
        import drift_gate as dg
        scrubbed = dg.scrub_nondeterminism("memory_ref: <Foo object at 0x7f8a9b3c4d5e>")
        assert "0x7f8a9b3c4d5e" not in scrubbed
        assert "<scrubbed>" in scrubbed

    def test_nondeterministic_snapshots_match(self):
        """snap_before.txt and snap_after_nondeterministic.txt match after scrub.

        Both have the same stable content but different timestamps, UUIDs, and
        hex addresses.  snapshots_match must return True.
        """
        import drift_gate as dg
        before = _load_text("snap_before.txt")
        after = _load_text("snap_after_nondeterministic.txt")
        assert dg.snapshots_match(before, after), (
            "Snapshots differing only in nondeterministic noise must match after scrub"
        )

    def test_real_divergence_does_not_match(self):
        """snap_before.txt and snap_after_divergent.txt do NOT match (real content change)."""
        import drift_gate as dg
        before = _load_text("snap_before.txt")
        after = _load_text("snap_after_divergent.txt")
        assert not dg.snapshots_match(before, after), (
            "Snapshots with genuinely different stable content must NOT match"
        )

    def test_no_scrub_flag_respects_raw_bytes(self):
        """scrub=False does a raw byte-compare, so nondeterministic snapshots differ."""
        import drift_gate as dg
        before = _load_text("snap_before.txt")
        after = _load_text("snap_after_nondeterministic.txt")
        # The two fixture files differ in timestamps/UUIDs → raw compare must fail
        assert not dg.snapshots_match(before, after, scrub=False)

    def test_custom_patterns_used_when_provided(self):
        """Custom patterns list overrides DEFAULT_SCRUB_PATTERNS."""
        import drift_gate as dg
        text = "CUSTOM_NONCE: abc123"
        # With no matching pattern: nothing is scrubbed
        result_no_pattern = dg.scrub_nondeterminism(text, patterns=[])
        assert result_no_pattern == text
        # With a custom pattern: the nonce is scrubbed
        result_with_pattern = dg.scrub_nondeterminism(text, patterns=[r"abc123"])
        assert "abc123" not in result_with_pattern
        assert "<scrubbed>" in result_with_pattern


# ---------------------------------------------------------------------------
# F2: scrub patterns are deliberately NARROW — real values must not be masked
# ---------------------------------------------------------------------------


class TestNarrowScrub:
    """The default scrub patterns target genuine NONDETERMINISM only.

    A greedy ``0x[0-9a-fA-F]+`` or bare ``\\d{10,13}`` masks real value changes
    (a hex flag, a balance) so two genuinely different snapshots compare equal —
    a regression-masking defect. The patterns must be narrowed to their actual
    nondeterminism intent.
    """

    # --- genuine nondeterminism IS still scrubbed (match → True) ----------

    def test_object_repr_address_is_scrubbed(self):
        """An object-repr '<... at 0x...>' address (nondeterministic) is scrubbed."""
        import drift_gate as dg
        before = "ref: <Foo object at 0x7f8a9b3c4d5e>"
        after = "ref: <Foo object at 0x1a2b3c4d5e6f>"
        assert dg.snapshots_match(before, after), (
            "Object-repr addresses are nondeterministic and must still be scrubbed"
        )

    def test_iso_timestamp_is_scrubbed(self):
        """An ISO-8601 datetime (nondeterministic) is scrubbed."""
        import drift_gate as dg
        before = "computed_at: 2024-01-15T10:30:00Z"
        after = "computed_at: 2026-06-27T14:55:30Z"
        assert dg.snapshots_match(before, after)

    def test_labeled_epoch_is_scrubbed(self):
        """A LABELED epoch (timestamp/epoch/ts/time: <digits>) is scrubbed."""
        import drift_gate as dg
        before = "timestamp: 1700000000"
        after = "timestamp: 1800000000"
        assert dg.snapshots_match(before, after), (
            "A contextually-labeled epoch is nondeterministic and must be scrubbed"
        )

    # --- real values are NO LONGER masked (match → False / verdict BLOCK) --

    def test_real_integer_value_change_not_masked(self):
        """F2: a genuine 10–13 digit value change (a balance) is NO LONGER masked."""
        import drift_gate as dg
        before = "balance: 1000000000"
        after = "balance: 2000000000"
        assert not dg.snapshots_match(before, after), (
            "A bare large integer is a real value, NOT nondeterminism — it must "
            "not be scrubbed, so genuinely different balances must NOT match"
        )

    def test_standalone_hex_flag_change_not_masked(self):
        """F2: a non-address hex literal change is NO LONGER masked."""
        import drift_gate as dg
        before = "flag: 0xdeadbeef"
        after = "flag: 0xcafef00d"
        assert not dg.snapshots_match(before, after), (
            "A bare hex literal (not an object-repr address) is a real value — "
            "it must not be scrubbed, so different flags must NOT match"
        )

    def test_real_value_change_blocks_via_snapshot_verdict(self):
        """F2 end-to-end: a real value change outside the AEL → BLOCK."""
        import drift_gate as dg
        before = {"t": "balance: 1000000000\n"}
        after = {"t": "balance: 2000000000\n"}
        result = dg.characterization_snapshot_verdict(before, after, [])
        assert result["verdict"] == "BLOCK"
        assert "t" in result["changed_outside_ael"]


# ---------------------------------------------------------------------------
# characterization_snapshot_verdict
# ---------------------------------------------------------------------------


class TestSnapshotVerdict:
    def test_identical_snapshots_pass(self):
        """Identical before/after snapshots → PASS."""
        import drift_gate as dg
        snaps = {"t_a": "output: 42\n", "t_b": "output: hello\n"}
        result = dg.characterization_snapshot_verdict(snaps, snaps, [])
        assert result["verdict"] == "PASS"
        assert result["changed_outside_ael"] == []

    def test_snapshot_changed_outside_ael_blocks(self):
        """A snapshot that changed outside the AEL → BLOCK.

        This is the seeded-fixture acceptance: an unexpected change outside the
        authorized exception list must BLOCK.
        """
        import drift_gate as dg
        before = {"t_stable": "output: 42\n", "t_ael": "output: buggy\n"}
        after = {"t_stable": "output: CHANGED\n", "t_ael": "output: fixed\n"}
        # t_ael is on the AEL (exempt), but t_stable changed unexpectedly → BLOCK
        result = dg.characterization_snapshot_verdict(before, after, ["t_ael"])
        assert result["verdict"] == "BLOCK", (
            "A snapshot change outside the AEL must cause BLOCK"
        )
        assert "t_stable" in result["changed_outside_ael"]
        assert "t_ael" not in result["changed_outside_ael"]

    def test_snapshot_changed_inside_ael_passes(self):
        """A snapshot that changed BUT is in the AEL → PASS (the fix is expected)."""
        import drift_gate as dg
        before = {"t_ael": "output: buggy\n"}
        after = {"t_ael": "output: fixed\n"}
        result = dg.characterization_snapshot_verdict(before, after, ["t_ael"])
        assert result["verdict"] == "PASS"
        assert result["changed_outside_ael"] == []

    def test_nondeterministic_snapshots_pass(self):
        """Snapshots differing only in nondeterministic noise → PASS."""
        import drift_gate as dg
        before = _load_text("snap_before.txt")
        after = _load_text("snap_after_nondeterministic.txt")
        before_snaps = {"t_stable": before}
        after_snaps = {"t_stable": after}
        result = dg.characterization_snapshot_verdict(before_snaps, after_snaps, [])
        assert result["verdict"] == "PASS"

    def test_empty_snaps_pass(self):
        """Empty before and after snapshots → PASS."""
        import drift_gate as dg
        result = dg.characterization_snapshot_verdict({}, {}, [])
        assert result["verdict"] == "PASS"
        assert result["changed_outside_ael"] == []


# ---------------------------------------------------------------------------
# defer_record / emit_deferrals
# ---------------------------------------------------------------------------


class TestDeferrals:
    def test_defer_record_has_required_keys(self):
        """defer_record returns a dict with required keys."""
        import drift_gate as dg
        finding = {"locus": "add_numbers", "module": "tools/example.py"}
        record = dg.defer_record(finding, "cannot fix without changing behavior")
        for key in ("finding_id", "finding", "reason", "utc"):
            assert key in record, f"Missing required key {key!r} in defer_record output"

    def test_defer_record_finding_id_from_locus(self):
        """defer_record derives finding_id from the 'locus' key when 'id' is absent."""
        import drift_gate as dg
        finding = {"locus": "my_function"}
        record = dg.defer_record(finding, "reason")
        assert record["finding_id"] == "my_function"

    def test_emit_deferrals_round_trip(self, tmp_path):
        """emit_deferrals writes JSON that round-trips to the original records."""
        import drift_gate as dg
        finding = {"locus": "buggy_fn", "module": "src/mod.py"}
        record = dg.defer_record(finding, "behavioral change required")
        dest = tmp_path / "deferred.json"
        dg.emit_deferrals([record], dest)
        loaded = json.loads(dest.read_text(encoding="utf-8"))
        assert isinstance(loaded, list)
        assert len(loaded) == 1
        assert loaded[0]["finding_id"] == record["finding_id"]
        assert loaded[0]["reason"] == "behavioral change required"

    def test_emit_deferrals_creates_parent_dirs(self, tmp_path):
        """emit_deferrals creates missing parent directories."""
        import drift_gate as dg
        dest = tmp_path / "kata" / "deviations" / "deferred.json"
        assert not dest.parent.exists()
        dg.emit_deferrals([], dest)
        assert dest.exists()


# ---------------------------------------------------------------------------
# build_drift_report / emit_drift_report / drift_schema
# ---------------------------------------------------------------------------


class TestDriftReport:
    def _behavioral_pass(self) -> dict:
        return {"verdict": "PASS", "blocking": [], "flipped": ["t_buggy"], "reason": "ok"}

    def _behavioral_block(self) -> dict:
        return {"verdict": "BLOCK", "blocking": ["t_a"], "flipped": [], "reason": "regression"}

    def _snapshot_pass(self) -> dict:
        return {"verdict": "PASS", "changed_outside_ael": []}

    def _snapshot_block(self) -> dict:
        return {"verdict": "BLOCK", "changed_outside_ael": ["t_stable"]}

    def test_schema_required_keys(self):
        """drift_schema() returns a dict with all schema-required keys."""
        import drift_gate as dg
        schema = dg.drift_schema()
        assert isinstance(schema, dict)
        assert "required" in schema
        for key in ("finding_id", "behavioral", "snapshot", "verdict", "utc"):
            assert key in schema["required"], f"Key {key!r} missing from schema required"

    def test_schema_verdict_enum(self):
        """drift_schema() verdict property includes PASS and BLOCK."""
        import drift_gate as dg
        schema = dg.drift_schema()
        verdict_enum = schema["properties"]["verdict"]["enum"]
        assert "PASS" in verdict_enum
        assert "BLOCK" in verdict_enum

    def test_build_drift_report_pass_when_both_pass(self):
        """build_drift_report returns verdict:PASS when both sub-verdicts are PASS."""
        import drift_gate as dg
        finding = {"locus": "my_fn"}
        report = dg.build_drift_report(finding, self._behavioral_pass(), self._snapshot_pass())
        assert report["verdict"] == "PASS"
        assert report["finding_id"] == "my_fn"
        for key in ("finding_id", "behavioral", "snapshot", "verdict", "utc"):
            assert key in report

    def test_build_drift_report_block_when_behavioral_blocks(self):
        """build_drift_report returns verdict:BLOCK when behavioral verdict is BLOCK."""
        import drift_gate as dg
        finding = {"locus": "my_fn"}
        report = dg.build_drift_report(finding, self._behavioral_block(), self._snapshot_pass())
        assert report["verdict"] == "BLOCK"

    def test_build_drift_report_block_when_snapshot_blocks(self):
        """build_drift_report returns verdict:BLOCK when snapshot verdict is BLOCK."""
        import drift_gate as dg
        finding = {"locus": "my_fn"}
        report = dg.build_drift_report(finding, self._behavioral_pass(), self._snapshot_block())
        assert report["verdict"] == "BLOCK"

    def test_emit_drift_report_round_trip(self, tmp_path):
        """emit_drift_report writes JSON that round-trips correctly."""
        import drift_gate as dg
        finding = {"locus": "add_numbers"}
        report = dg.build_drift_report(finding, self._behavioral_pass(), self._snapshot_pass())
        dest = tmp_path / "report.json"
        dg.emit_drift_report(report, dest)
        loaded = json.loads(dest.read_text(encoding="utf-8"))
        assert loaded["verdict"] == "PASS"
        assert loaded["finding_id"] == "add_numbers"
        schema = dg.drift_schema()
        for key in schema["required"]:
            assert key in loaded, f"Schema-required key {key!r} missing from loaded report"

    def test_emit_drift_report_creates_parent_dirs(self, tmp_path):
        """emit_drift_report creates .kata/drift/ parent directories."""
        import drift_gate as dg
        finding = {"locus": "add_numbers"}
        report = dg.build_drift_report(finding, self._behavioral_pass(), self._snapshot_pass())
        dest = tmp_path / ".kata" / "drift" / "finding_001.json"
        assert not dest.parent.exists()
        dg.emit_drift_report(report, dest)
        assert dest.exists()


# ---------------------------------------------------------------------------
# structural_drift_verdict seam
# ---------------------------------------------------------------------------


class TestStructuralDriftVerdictSeam:
    def test_raises_not_implemented(self):
        """structural_drift_verdict must raise NotImplementedError in v1.

        This is the §5 v1 fast-follow seam — it is a named, non-executing stub.
        Callers get an explicit signal (NotImplementedError) rather than a
        silent mis-verdict.
        """
        import drift_gate as dg
        with pytest.raises(NotImplementedError):
            dg.structural_drift_verdict()

    def test_docstring_states_limitation(self):
        """structural_drift_verdict docstring must mention the §5 v1 LIMITATION."""
        import drift_gate as dg
        doc = dg.structural_drift_verdict.__doc__ or ""
        assert "v1" in doc.lower() or "limitation" in doc.lower(), (
            "structural_drift_verdict docstring must state the §5 v1 LIMITATION "
            "so callers understand this seam is not implemented"
        )


# ---------------------------------------------------------------------------
# exec-safety: no eval / exec / subprocess / shell in drift_gate.py
# ---------------------------------------------------------------------------


class TestExecSafety:
    """Source-scan assertions: drift_gate.py is pure — no exec sink introduced."""

    def _source(self) -> str:
        return (_TOOLS / "drift_gate.py").read_text(encoding="utf-8")

    def test_no_eval_in_drift_gate_py(self):
        """drift_gate.py must not contain eval() calls (assertable by source scan)."""
        import re
        src = self._source()
        hits = [m.group() for m in re.finditer(r"\beval\s*\(", src)]
        assert not hits, f"eval() call found in drift_gate.py: {hits}"

    def test_no_exec_in_drift_gate_py(self):
        """drift_gate.py must not contain exec() calls."""
        import re
        src = self._source()
        hits = [m.group() for m in re.finditer(r"\bexec\s*\(", src)]
        assert not hits, f"exec() call found in drift_gate.py: {hits}"

    def test_no_subprocess_import_in_drift_gate_py(self):
        """drift_gate.py must not import subprocess."""
        import re
        src = self._source()
        hits = [
            m.group()
            for m in re.finditer(
                r"^\s*(?:import|from)\s+subprocess\b", src, re.MULTILINE
            )
        ]
        assert not hits, f"subprocess import found in drift_gate.py: {hits}"

    def test_no_shell_true_in_drift_gate_py(self):
        """drift_gate.py must not pass shell=True."""
        src = self._source()
        assert "shell=True" not in src, "shell=True found in drift_gate.py"

    def test_drift_gate_py_is_pure_ast_parseable(self):
        """drift_gate.py must be syntactically valid Python."""
        import ast
        ast.parse(self._source())


# ---------------------------------------------------------------------------
# Mutation non-vacuity proofs (spawn real subprocess via prove_non_vacuous)
# ---------------------------------------------------------------------------


class TestMutationProof:
    """Mutation-proof tests for the five load-bearing lines in drift_gate.py.

    Per PLAN F1 acceptance: the green→RED BLOCK branch, the AEL green-in-before
    rejection, the AEL must-flip red→green check, and the snapshot-changed-
    outside-AEL BLOCK must all be mutation-covered (non-vacuous).  D98 F1
    defense-in-depth adds a fifth: the vanished-baseline-green BLOCK branch.

    Each test removes exactly one load-bearing line from drift_gate.py using
    mutation_run.prove_non_vacuous and verifies that the corresponding guard
    test goes red (testWentRed:True, nonVacuous:True).

    mutation_run.prove_non_vacuous always restores the source file afterward
    (try/finally guarantee), so these tests are self-healing even on failure.
    """

    def _source(self) -> str:
        return str(_TOOLS / "drift_gate.py")

    def _test_cmd(self, test_spec: str) -> str:
        """Build a pytest command targeting a specific test in test_drift_gate.py."""
        return (
            f'cd /d "{_TOOLS}" && '
            f"{sys.executable} -m pytest "
            f'"tests/test_drift_gate.py::{test_spec}" -q --tb=no'
        )

    def test_mutation_proof_green_red_block_branch(self):
        """(b) Prove the green→red BLOCK branch in drift_verdict is load-bearing.

        Target line (exact, 16-space indent — 4 levels in):
            ``                blocking.append(tid)``
        This line is inside:
            for tid, transition in transitions.items():
                if transition == "green->red":
                    if tid not in ael_set:
                        blocking.append(tid)   ← target

        When removed: green→red regressions outside the AEL are never added to
        blocking → drift_verdict returns PASS instead of BLOCK → the regression
        guard test goes red.
        """
        import mutation_run

        asserted_line = "                blocking.append(tid)"
        test_cmd = self._test_cmd(
            "TestDriftVerdict::test_blocks_injected_regression"
        )
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make test_blocks_injected_regression go red — "
            "the green→red blocking.append(tid) at 16 spaces is not load-bearing"
        )
        assert verdict["nonVacuous"], (
            "test_blocks_injected_regression must catch removal of the "
            "green→red blocking.append(tid) branch"
        )

    def test_mutation_proof_ael_green_in_before_rejection(self):
        """(a) Prove the AEL green-in-before rejection in validate_allowed_exceptions is load-bearing.

        Target line (exact, 12-space indent — 3 levels in):
            ``            rejected.append(entry)``
        This line is inside:
            for entry in allowed:
                if entry not in before or before[entry] != "red":
                    rejected.append(entry)   ← target

        When removed: green-in-before AEL entries are never added to rejected →
        validate_allowed_exceptions returns valid:True for green entries →
        drift_verdict does not block → the guard test goes red.
        """
        import mutation_run

        asserted_line = "            rejected.append(entry)"
        test_cmd = self._test_cmd(
            "TestValidateAllowedExceptions::test_green_in_before_is_rejected"
        )
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make test_green_in_before_is_rejected go red — "
            "rejected.append(entry) is not load-bearing (AEL integrity guard is not biting)"
        )
        assert verdict["nonVacuous"], (
            "test_green_in_before_is_rejected must catch removal of rejected.append(entry)"
        )

    def test_mutation_proof_ael_must_flip_red_to_green(self):
        """(c) Prove the AEL must-flip red→green check in drift_verdict is load-bearing.

        Target line (exact, 12-space indent — 3 levels in):
            ``            blocking.append(tid)``
        This line is inside:
            for tid in allowed_exceptions:
                t = transitions.get(tid, "removed")
                if t == "red->green":
                    flipped.append(tid)
                else:
                    blocking.append(tid)   ← target

        When removed: AEL tests that stay RED after the fix are never added to
        blocking → drift_verdict returns PASS instead of BLOCK → the guard test
        goes red.
        """
        import mutation_run

        asserted_line = "            blocking.append(tid)"
        test_cmd = self._test_cmd(
            "TestDriftVerdict::test_ael_still_red_blocks"
        )
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make test_ael_still_red_blocks go red — "
            "the AEL blocking.append(tid) at 12 spaces is not load-bearing"
        )
        assert verdict["nonVacuous"], (
            "test_ael_still_red_blocks must catch removal of the AEL blocking.append(tid)"
        )

    def test_mutation_proof_snapshot_changed_outside_ael(self):
        """(d) Prove the snapshot-changed-outside-AEL BLOCK is load-bearing.

        Target line (exact, 12-space indent — 3 levels in):
            ``            changed_outside_ael.append(key)``
        This line is inside:
            for key in all_keys:
                if key in ael_set:
                    continue
                ...
                if not snapshots_match(before_snap, after_snap):
                    changed_outside_ael.append(key)   ← target

        When removed: changed snapshots outside the AEL are never recorded →
        characterization_snapshot_verdict returns PASS instead of BLOCK →
        the guard test goes red.
        """
        import mutation_run

        asserted_line = "            changed_outside_ael.append(key)"
        test_cmd = self._test_cmd(
            "TestSnapshotVerdict::test_snapshot_changed_outside_ael_blocks"
        )
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make test_snapshot_changed_outside_ael_blocks go red — "
            "changed_outside_ael.append(key) is not load-bearing"
        )
        assert verdict["nonVacuous"], (
            "test_snapshot_changed_outside_ael_blocks must catch removal of "
            "changed_outside_ael.append(key)"
        )

    def test_mutation_proof_vanished_baseline_green_block(self):
        """(e) F1: Prove the vanished-baseline-green BLOCK branch is load-bearing.

        Target line (exact, 12-space indent — 3 levels in):
            ``            blocking.append(gtid)``
        This line is inside:
            for gtid, status in before.items():
                if status == "green" and gtid not in after:
                    blocking.append(gtid)   ← target

        When removed: a baseline-green test that vanished from after is never
        added to blocking → drift_verdict returns PASS instead of BLOCK (the
        fail-open defect) → the F1 regression guard goes red.  Distinct line text
        (``gtid``) keeps it unique from the 12-space AEL ``blocking.append(tid)``.
        """
        import mutation_run

        asserted_line = "            blocking.append(gtid)"
        test_cmd = self._test_cmd(
            "TestDriftVerdict::test_green_in_before_absent_from_after_blocks"
        )
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make test_green_in_before_absent_from_after_blocks go red — "
            "the vanished-baseline-green blocking.append(gtid) is not load-bearing"
        )
        assert verdict["nonVacuous"], (
            "test_green_in_before_absent_from_after_blocks must catch removal of "
            "blocking.append(gtid)"
        )


# --- DET-12 fold (2026-07-12 health review): temp-path scrub + id normalization ---

def test_scrub_var_folders_macos_temp_path():
    r"""DET-12: macOS per-user temp dirs (/var/folders/... — the TMPDIR default) must
    scrub like /tmp and Windows AppData\Local\Temp, or an AEL snapshot authored on
    macOS carries a machine-specific temp path that never byte-matches."""
    import drift_gate as dg
    text = "tmp=/var/folders/xy/9zk_h/T/pytest-of-user/pytest-3/test0 end"
    scrubbed = dg.scrub_nondeterminism(text)
    assert "/var/folders/" not in scrubbed
    assert "<scrubbed>" in scrubbed


def test_parse_test_outcomes_normalizes_backslash_node_id():
    r"""DET-12: pytest emits the OS-native path separator, so a Windows run's
    ``tests\x.py::t`` names the SAME test as a Linux ``tests/x.py::t``. The parser
    normalizes the separator to '/' so the AEL / transition set-compare matches."""
    import drift_gate as dg
    out = dg.parse_test_outcomes(r"tests\pkg\x.py::TestA::t_one PASSED [100%]")
    assert out == {"tests/pkg/x.py::TestA::t_one": "green"}


def test_parse_test_outcomes_windows_and_posix_ids_match():
    """The Windows-authored id and the POSIX-run id map to the SAME normalized key."""
    import drift_gate as dg
    win = dg.parse_test_outcomes(r"tests\x.py::t FAILED [ 50%]")
    posix = dg.parse_test_outcomes("tests/x.py::t FAILED [ 50%]")
    assert win == posix == {"tests/x.py::t": "red"}
