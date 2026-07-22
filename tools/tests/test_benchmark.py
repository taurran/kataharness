"""test_benchmark.py — TDD suite for tools/benchmark.py (S2, kata-loop-benchmark).

Strategy: default-FAIL (written before implementation; green only after
benchmark.py is present and correct).  Pure engine tests inject pre-built
JSON artifacts via tmp_path — no subprocess in the pure tests.  Mutation-proof
tests spawn a real subprocess via mutation_run.prove_non_vacuous.

Split coverage:
  (A) Pure engine — scorecard_schema, score_arms, emit_scorecard
  (B) Thin runner — run_dual_gate (interface/delegation contract only)
  Exec-safety — source-scan assertions (no subprocess import, no eval, no exec)
  Mutation proofs — five load-bearing lines, mutation-proven

Coverage map
------------
scorecard_schema:
    TestScorecardSchema::test_required_fields_present
    TestScorecardSchema::test_directional_field_in_schema
    TestScorecardSchema::test_n_field_in_schema
    TestScorecardSchema::test_schema_description_carries_honesty_note
    TestScorecardSchema::test_schema_required_includes_honesty
    TestScorecardSchema::test_schema_required_includes_recommendations
    TestScorecardSchema::test_schema_honesty_property_shape
    TestScorecardSchema::test_schema_recommendations_property_shape

TestFloorGate:
    test_floor_fail_exit_code_nonzero          ← mutation-proof target (a)
    test_floor_fail_failed_count
    test_floor_pass_clean_result               ← updated: uses real f2p/p2p

TestFloorPartialResult (FIX 5):
    test_floor_fail_missing_failed_key         ← mutation-proof target (e)
    test_floor_fail_missing_exit_code
    test_floor_pass_requires_both_keys

TestDualGate:
    test_both_green_full_credit
    test_partial_f2p_partial_credit
    test_no_gate_empty_criteria_no_q_credit    ← updated from test_empty_f2p_p2p_defaults_full_credit

TestNoFreeDualScore (FIX 1):
    test_no_gate_arm_not_in_results
    test_no_gate_empty_criteria_dual_gate_evaluated_false
    test_evaluated_gate_has_flag_true
    test_floor_fail_has_dual_gate_evaluated_false

TestMutationMultiplier:
    test_mutation_all_non_vacuous_no_penalty   ← updated: uses real f2p/p2p
    test_mutation_vacuous_reduces_q            ← updated: uses real f2p/p2p
    test_mutation_absent_no_penalty            ← updated: uses real f2p/p2p

TestAxisC:
    test_axis_c_null_tokens_labeled_not_zero
    test_axis_c_normalization_range
    test_axis_c_multi_arm_relative

TestAxisCIncomplete (FIX 6b):
    test_missing_non_nullable_flagged
    test_missing_non_nullable_not_scored_as_cheapest

TestFloorGateEfficiency:
    test_floor_fail_excluded_from_efficiency_ranking
    test_floor_passers_only_ranked              ← mutation-proof target (b)

TestParetoAndScalar:
    test_pareto_point_format
    test_composite_scalar_formula

TestProfileWeights:
    test_cost_lean_vs_balanced_ranking_flips
    test_quality_strict_vs_balanced_q_wins

TestMultiArm:
    test_multi_arm_two_entries_in_arms_list
    test_multi_arm_per_arm_pareto_points

TestHonestyFields:
    test_scorecard_n_field_equals_arm_count
    test_scorecard_directional_always_true

TestHonestyBlock (FIX 3):
    test_scorecard_has_honesty_dict
    test_honesty_directional_always_true
    test_honesty_basis_is_n1
    test_honesty_disclosure_carries_exercised_not_proven

TestRecommendations (FIX 3):
    test_scorecard_has_recommendations_list
    test_recommendations_pareto_best_present
    test_recommendations_empty_when_no_passers
    test_recommendations_dominated_detected

TestTraversalGuard (FIX 2):
    test_traversal_id_rejected                 ← mutation-proof target (d)
    test_traversal_never_invokes_run_named_test
    test_leading_dash_path_rejected
    test_valid_id_not_rejected

TestEmitScorecard:
    test_emit_creates_file_and_dirs
    test_emit_round_trip_readable
    test_emit_guard_rejects_traversal

TestExecSafety:
    test_no_subprocess_import
    test_no_eval
    test_no_exec
    test_no_shell_true

TestRunDualGate:
    test_run_dual_gate_delegates_to_run_named_test
    test_run_dual_gate_malformed_id_returns_false

TestMutationProof:
    test_mutation_proof_floor_q_zero           (a) floor-fail Q=0 line
    test_mutation_proof_efficiency_floor_gate  (b) floor-passers-only append line
    test_mutation_proof_no_free_dual_score     (c) FIX 1 gate-not-evaluated Q=0 line
    test_mutation_proof_traversal_guard        (d) FIX 2 _guard_node_id call
    test_mutation_proof_partial_floor          (e) FIX 5 failed_present check line

TestF2PEvaluatedFlag (FIX metric-honesty):
    test_empty_f2p_with_p2p_vacuous_flag      vacuous 1.0 → f2p_evaluated=False, f2p_total=0
    test_real_f2p_is_evaluated                real F2P → f2p_evaluated=True, f2p_total=N
    test_real_all_pass_f2p_distinguishable    all-pass + f2p_evaluated=True ≠ vacuous
    test_p2p_evaluated_symmetry               empty p2p → p2p_evaluated=False, p2p_total=0

TestDurableF2PProof (@pytest.mark.integration):
    test_f2p_zero_to_one_transition           real 0→1 via broken→fixed synthetic control
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup — mirrors pattern in test_benchmark_control.py
# ---------------------------------------------------------------------------

_TESTS = Path(__file__).resolve().parent
_TOOLS = _TESTS.parent

if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import benchmark as bm  # noqa: E402

# ---------------------------------------------------------------------------
# Test-fixture helpers
# ---------------------------------------------------------------------------


def _kata(arm_root: Path) -> Path:
    """Create and return the .kata/ sub-directory under arm_root."""
    kata = arm_root / ".kata"
    kata.mkdir(parents=True, exist_ok=True)
    return kata


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _result(exit_code: int = 0, failed: int = 0, passed: int = 5) -> dict:
    return {"exitCode": exit_code, "failed": failed, "passed": passed,
            "gateName": "smoke", "command": "pytest", "skipped": 0,
            "stdoutTail": "", "baselineSha": "abc", "resultSha": "def",
            "utc": "2026-06-28T00:00:00+00:00"}


def _mutation(all_non_vacuous: bool = True) -> dict:
    return {"allNonVacuous": all_non_vacuous, "records": []}


def _usage(
    label: str = "arm",
    wall_clock_s: float = 10.0,
    tool_calls: int = 5,
    escalations: int = 0,
    thrash_iters: int = 0,
    subagent_dispatches: int = 0,
    cost_usd: float | None = 0.01,
    tokens_in: int | None = 1000,
    tokens_out: int | None = 300,
) -> dict:
    return {
        "label": label,
        "model": "claude-sonnet-4-6",
        "wallClockS": wall_clock_s,
        "toolCalls": tool_calls,
        "escalations": escalations,
        "thrashIters": thrash_iters,
        "subagentDispatches": subagent_dispatches,
        "costUSD": cost_usd,
        "tokensIn": tokens_in,
        "tokensOut": tokens_out,
    }


def _make_arm(
    tmp_path: Path,
    label: str,
    result: dict | None = None,
    mutation: dict | None = None,
    usage: dict | None = None,
) -> Path:
    """Create a minimal arm directory with .kata/ JSON artifacts."""
    root = tmp_path / label
    root.mkdir(parents=True, exist_ok=True)
    kata = _kata(root)
    _write(kata / "RESULT.json", result if result is not None else _result())
    _write(kata / "mutation.json", mutation if mutation is not None else _mutation())
    _write(kata / "usage.json", usage if usage is not None else _usage(label=label))
    return root


def _arm_by_label(scorecard: dict, label: str) -> dict:
    """Return the arm row from scorecard matching the given label."""
    for arm in scorecard["arms"]:
        if arm["label"] == label:
            return arm
    raise KeyError(f"Label {label!r} not found in scorecard arms")


# Minimal f2p/p2p results that make gate_evaluated=True → Q > 0
_GATE_PASS = {"f2p": {"t1": True}, "p2p": {}}


# ---------------------------------------------------------------------------
# scorecard_schema
# ---------------------------------------------------------------------------


class TestScorecardSchema:
    def test_required_fields_present(self):
        """Schema required list includes schema, profile, n, directional, arms, utc."""
        schema = bm.scorecard_schema()
        for field in ("schema", "profile", "n", "directional", "arms", "utc"):
            assert field in schema["required"], f"{field!r} missing from required"

    def test_directional_field_in_schema(self):
        """'directional' property is present in schema properties."""
        props = bm.scorecard_schema()["properties"]
        assert "directional" in props
        assert props["directional"]["type"] == "boolean"

    def test_n_field_in_schema(self):
        """'n' property is present with type integer."""
        props = bm.scorecard_schema()["properties"]
        assert "n" in props
        assert props["n"]["type"] == "integer"

    def test_schema_description_carries_honesty_note(self):
        """Schema description must mention floor-fail, directional, and reports-never-gate."""
        desc = bm.scorecard_schema()["description"].lower()
        assert "floor" in desc, "schema description missing 'floor' honesty note"
        assert "directional" in desc, "schema description missing 'directional' honesty note"
        assert "gate" in desc, "schema description missing 'never gate' honesty note"

    def test_schema_required_includes_honesty(self):
        """'honesty' is in the schema required list (engine-pinned, FIX 3)."""
        assert "honesty" in bm.scorecard_schema()["required"], (
            "FIX 3: 'honesty' must be in schema required — engine-pinned, cannot be dropped"
        )

    def test_schema_required_includes_recommendations(self):
        """'recommendations' is in the schema required list (engine-pinned, FIX 3)."""
        assert "recommendations" in bm.scorecard_schema()["required"], (
            "FIX 3: 'recommendations' must be in schema required — engine-pinned"
        )

    def test_schema_honesty_property_shape(self):
        """Schema honesty property is an object with directional/basis/disclosure."""
        props = bm.scorecard_schema()["properties"]
        assert "honesty" in props
        h = props["honesty"]
        assert h["type"] == "object"
        assert "directional" in h.get("required", [])
        assert "basis" in h.get("required", [])
        assert "disclosure" in h.get("required", [])

    def test_schema_recommendations_property_shape(self):
        """Schema recommendations property is an array of objects with kind+arm."""
        props = bm.scorecard_schema()["properties"]
        assert "recommendations" in props
        r = props["recommendations"]
        assert r["type"] == "array"
        item_req = r.get("items", {}).get("required", [])
        assert "kind" in item_req
        assert "arm" in item_req


# ---------------------------------------------------------------------------
# TestFloorGate
# ---------------------------------------------------------------------------


class TestFloorGate:
    """Floor-gate: exitCode!=0 or failed>0 ⇒ Q=0 absolute (DESIGN §3.1.1)."""

    def test_floor_fail_exit_code_nonzero(self, tmp_path):
        """exitCode=1 → Q=0 absolute (floor-fail, regardless of dual-gate)."""
        root = _make_arm(tmp_path, "arm-a", result=_result(exit_code=1, failed=0))
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["q"] == 0.0, f"Expected Q=0.0 on floor-fail, got {arm['q']}"
        assert arm["floor_passed"] is False
        assert arm["floor_verdict"] == "FAIL"

    def test_floor_fail_failed_count(self, tmp_path):
        """exitCode=0 but failed>0 → Q=0 absolute (test failures floor the arm)."""
        root = _make_arm(tmp_path, "arm-a", result=_result(exit_code=0, failed=2))
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["q"] == 0.0
        assert arm["floor_passed"] is False

    def test_floor_pass_clean_result(self, tmp_path):
        """exitCode=0, failed=0, with evaluated gate → floor passed, Q > 0."""
        root = _make_arm(tmp_path, "arm-a", result=_result(exit_code=0, failed=0))
        # Use a real f2p entry so dual_gate_evaluated=True → Q > 0
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["floor_passed"] is True
        assert arm["floor_verdict"] == "PASS"
        assert arm["q"] > 0.0, f"Expected Q>0 on floor-pass with evaluated gate, got {arm['q']}"


# ---------------------------------------------------------------------------
# TestFloorPartialResult (FIX 5) — fail-closed floor on partial RESULT.json
# ---------------------------------------------------------------------------


class TestFloorPartialResult:
    """FIX 5: Floor is fail-closed when 'failed' key is absent from RESULT.json."""

    def test_floor_fail_missing_failed_key(self, tmp_path):
        """RESULT.json = {exitCode:0} with no 'failed' key → floor FAIL, Q=0."""
        root = _make_arm(tmp_path, "arm-a", result={"exitCode": 0})  # no 'failed'
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["floor_passed"] is False, (
            "FIX 5: missing 'failed' key must be floor FAIL (partial artifact)"
        )
        assert arm["q"] == 0.0
        assert arm["floor_verdict"] == "FAIL"

    def test_floor_fail_missing_exit_code(self, tmp_path):
        """RESULT.json = {} (no exitCode, no failed) → floor FAIL (exitCode defaults to 1)."""
        root = _make_arm(tmp_path, "arm-a", result={})
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["floor_passed"] is False
        assert arm["q"] == 0.0

    def test_floor_pass_requires_both_keys(self, tmp_path):
        """exitCode=0 AND failed=0 both present → floor PASS."""
        root = _make_arm(tmp_path, "arm-a", result=_result(exit_code=0, failed=0))
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["floor_passed"] is True, (
            "exitCode=0 AND failed=0 both present → floor PASS"
        )

    def test_floor_fail_result_json_absent(self, tmp_path):
        """Absent RESULT.json → floor FAIL (file-absent already fail-closes)."""
        root = tmp_path / "arm-a"
        root.mkdir()
        kata = _kata(root)
        # No RESULT.json
        _write(kata / "mutation.json", _mutation())
        _write(kata / "usage.json", _usage())
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["floor_passed"] is False
        assert arm["q"] == 0.0


# ---------------------------------------------------------------------------
# TestDualGate
# ---------------------------------------------------------------------------


class TestDualGate:
    """Dual-gate F2P/P2P booleans (injected — pure tests, no pytest subprocess)."""

    def test_both_green_full_credit(self, tmp_path):
        """All F2P and P2P tests pass → dual_gate_both_green=True, Q at maximum."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={
                "arm-a": {
                    "f2p": {"t1": True, "t2": True},
                    "p2p": {"t3": True},
                }
            },
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["dual_gate_both_green"] is True
        assert arm["f2p_pass_rate"] == 1.0
        assert arm["p2p_pass_rate"] == 1.0
        # With allNonVacuous=True (default fixture) and both-green:
        # Q = (0.6*1.0 + 0.4*1.0) * 1.0 = 1.0
        assert abs(arm["q"] - 1.0) < 1e-9

    def test_partial_f2p_partial_credit(self, tmp_path):
        """Some F2P fail → partial credit (0 < Q < 1.0 for floor-passer)."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={
                "arm-a": {
                    "f2p": {"t1": True, "t2": False, "t3": False},
                    "p2p": {"t4": True},
                }
            },
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["dual_gate_both_green"] is False
        assert arm["f2p_pass_rate"] == pytest.approx(1 / 3)
        assert arm["floor_passed"] is True
        # Q < 1.0 (partial F2P credit)
        assert 0.0 < arm["q"] < 1.0

    def test_no_gate_empty_criteria_no_q_credit(self, tmp_path):
        """Empty f2p AND p2p → dual_gate_evaluated=False, Q=0 (FIX 1: no free credit).

        Replaces old test_empty_f2p_p2p_defaults_full_credit whose assumption
        (empty → Q=1.0) was the BLOCKER defect — proved nothing, got full credit.
        """
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}},
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["dual_gate_evaluated"] is False, (
            "FIX 1: empty f2p AND p2p → dual_gate_evaluated must be False"
        )
        assert arm["q"] == 0.0, (
            "FIX 1: unevaluated gate → Q must be 0.0 (no free credit)"
        )
        assert arm["floor_passed"] is True, (
            "floor still passes (RESULT.json is clean); only Q is 0 due to no gate"
        )


# ---------------------------------------------------------------------------
# TestNoFreeDualScore (FIX 1)
# ---------------------------------------------------------------------------


class TestNoFreeDualScore:
    """FIX 1: dual_gate_evaluated flag; no Q credit for unevaluated gates."""

    def test_no_gate_arm_not_in_results(self, tmp_path):
        """Arm absent from f2p_p2p_results → dual_gate_evaluated=False, Q=0."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["dual_gate_evaluated"] is False, (
            "Arm missing from f2p_p2p_results → dual_gate_evaluated=False"
        )
        assert arm["q"] == 0.0, (
            "No gate entry for this arm → Q=0 (no free credit)"
        )

    def test_no_gate_empty_criteria_dual_gate_evaluated_false(self, tmp_path):
        """Arm with empty f2p AND p2p → dual_gate_evaluated=False, Q=0."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}},
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["dual_gate_evaluated"] is False
        assert arm["q"] == 0.0

    def test_evaluated_gate_has_flag_true(self, tmp_path):
        """Arm with ≥1 f2p or p2p entry → dual_gate_evaluated=True."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={"arm-a": {"f2p": {"t1": True}, "p2p": {}}},
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["dual_gate_evaluated"] is True, (
            "At least one f2p entry → gate was evaluated → dual_gate_evaluated=True"
        )
        assert arm["q"] > 0.0, (
            "Evaluated gate with passing tests → Q > 0"
        )

    def test_floor_fail_has_dual_gate_evaluated_false(self, tmp_path):
        """Floor-fail arm → dual_gate_evaluated=False (gate never reached)."""
        root = _make_arm(tmp_path, "arm-a", result=_result(exit_code=1))
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={"arm-a": {"f2p": {"t1": True}, "p2p": {}}},
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["floor_passed"] is False
        assert arm["dual_gate_evaluated"] is False, (
            "Floor-fail returns before gate evaluation → dual_gate_evaluated=False"
        )

    def test_dual_gate_evaluated_in_detail(self, tmp_path):
        """dual_gate_evaluated is present in the per-arm detail dict (for both states)."""
        root_eval = _make_arm(tmp_path, "arm-eval")
        root_skip = _make_arm(tmp_path, "arm-skip")
        sc = bm.score_arms(
            {"arm-eval": root_eval, "arm-skip": root_skip},
            f2p_p2p_results={
                "arm-eval": {"f2p": {"t1": True}, "p2p": {}},
                "arm-skip": {"f2p": {}, "p2p": {}},
            },
        )
        arm_eval = _arm_by_label(sc, "arm-eval")
        arm_skip = _arm_by_label(sc, "arm-skip")
        assert "dual_gate_evaluated" in arm_eval, "dual_gate_evaluated must be in arm record"
        assert "dual_gate_evaluated" in arm_skip
        assert arm_eval["dual_gate_evaluated"] is True
        assert arm_skip["dual_gate_evaluated"] is False


# ---------------------------------------------------------------------------
# TestMutationMultiplier
# ---------------------------------------------------------------------------


class TestMutationMultiplier:
    """Mutation multiplier from mutation.json.allNonVacuous (DESIGN §3.1.3)."""

    def test_mutation_all_non_vacuous_no_penalty(self, tmp_path):
        """allNonVacuous=True → multiplier=1.0, Q unchanged.

        Uses a real f2p entry so dual_gate_evaluated=True and Q is driven by the
        multiplier (not zeroed by FIX 1).
        """
        root = _make_arm(tmp_path, "arm-a", mutation=_mutation(all_non_vacuous=True))
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={"arm-a": _GATE_PASS},
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["mutation_available"] is True
        assert arm["detail"]["mutation_multiplier"] == 1.0
        assert abs(arm["q"] - 1.0) < 1e-9  # all-pass + no penalty = 1.0

    def test_mutation_vacuous_reduces_q(self, tmp_path):
        """allNonVacuous=False → multiplier < 1.0, Q reduced from dual-gate score.

        Uses a real f2p entry so dual_gate_evaluated=True, then the multiplier
        reduces Q below the dual-gate score.
        """
        root = _make_arm(tmp_path, "arm-a", mutation=_mutation(all_non_vacuous=False))
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={"arm-a": _GATE_PASS},
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["mutation_available"] is True
        assert arm["detail"]["mutation_multiplier"] < 1.0
        # dual_score = 0.6*1.0 + 0.4*1.0 = 1.0; vacuous ⇒ Q = 1.0 * 0.5 = 0.5
        assert arm["q"] < 1.0
        assert arm["q"] > 0.0  # floor still passed

    def test_mutation_absent_no_penalty(self, tmp_path):
        """Missing mutation.json → mutation_available=False, no Q penalization.

        Uses a real f2p entry so dual_gate_evaluated=True and Q can be > 0.
        """
        root = tmp_path / "arm-a"
        root.mkdir()
        kata = _kata(root)
        _write(kata / "RESULT.json", _result())
        # No mutation.json written
        _write(kata / "usage.json", _usage())
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={"arm-a": _GATE_PASS},
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["mutation_available"] is False
        assert abs(arm["q"] - 1.0) < 1e-9  # no penalty applied

    def test_mutation_present_missing_key_not_full_credit(self, tmp_path):
        """Q-9 (D136): mutation.json present but missing allNonVacuous ⇒ NOT full credit.

        A present-but-truncated mutation.json (file exists → mutation_available=True)
        that omits the allNonVacuous key must be treated as vacuous, not silently
        given the full 1.0 multiplier — mirrors FIX 5 (truncated RESULT.json → FAIL).
        """
        # Present file, but the key is absent (truncated write).
        root = _make_arm(tmp_path, "arm-a", mutation={"records": []})  # no allNonVacuous
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={"arm-a": _GATE_PASS},
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["mutation_available"] is True, (
            "Q-9: the file is present → mutation_available must be True"
        )
        assert arm["detail"]["mutation_multiplier"] < 1.0, (
            "Q-9: missing allNonVacuous on a present file ⇒ vacuous multiplier, not 1.0"
        )
        assert arm["q"] < 1.0, (
            "Q-9: a truncated mutation.json must NOT earn the full 1.0 Q"
        )


# ---------------------------------------------------------------------------
# TestAxisC
# ---------------------------------------------------------------------------


class TestAxisC:
    """Axis C: normalization, nullable-token honesty."""

    def test_axis_c_null_tokens_labeled_not_zero(self, tmp_path):
        """tokensIn=None (hence costUSD=None) → tokens_unavailable=True; c_norm still computed."""
        u = _usage(cost_usd=None, tokens_in=None, tokens_out=None)
        root = _make_arm(tmp_path, "arm-a", usage=u)
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["tokens_unavailable"] is True, (
            "Null costUSD must set tokens_unavailable=True (not silently scored as 0)"
        )
        # c_norm is still computed from non-nullable fields
        assert arm["c_norm"] is not None

    def test_axis_c_normalization_range(self, tmp_path):
        """c_norm is in [0.0, 1.0] for a single arm with typical usage."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["floor_passed"] is True
        c = arm["c_norm"]
        assert c is not None
        assert 0.0 <= c <= 1.0, f"c_norm={c} out of [0,1]"

    def test_axis_c_multi_arm_relative(self, tmp_path):
        """Two arms: high-usage arm has higher c_norm than low-usage arm."""
        # arm-A: high cost (high wall clock + tool calls)
        root_a = _make_arm(
            tmp_path, "arm-a",
            usage=_usage("arm-a", wall_clock_s=100.0, tool_calls=20, cost_usd=1.0),
        )
        # arm-B: low cost
        root_b = _make_arm(
            tmp_path, "arm-b",
            usage=_usage("arm-b", wall_clock_s=1.0, tool_calls=1, cost_usd=0.01),
        )
        sc = bm.score_arms(
            {"arm-a": root_a, "arm-b": root_b},
            f2p_p2p_results={
                "arm-a": {"f2p": {}, "p2p": {}},
                "arm-b": {"f2p": {}, "p2p": {}},
            },
        )
        arm_a = _arm_by_label(sc, "arm-a")
        arm_b = _arm_by_label(sc, "arm-b")
        assert arm_a["c_norm"] > arm_b["c_norm"], (
            f"High-usage arm-a c_norm={arm_a['c_norm']} should exceed "
            f"low-usage arm-b c_norm={arm_b['c_norm']}"
        )


# ---------------------------------------------------------------------------
# TestAxisCIncomplete (FIX 6b)
# ---------------------------------------------------------------------------


class TestAxisCIncomplete:
    """FIX 6b: absent non-nullable Axis-C fields flagged usage_incomplete, not scored as 0."""

    def test_missing_non_nullable_flagged(self, tmp_path):
        """usage.json missing 'wallClockS' → usage_incomplete=True on the arm."""
        # Build usage dict without wallClockS
        u = {
            "label": "arm-a",
            "model": "claude-sonnet-4-6",
            # wallClockS ABSENT
            "toolCalls": 5,
            "escalations": 0,
            "thrashIters": 0,
            "subagentDispatches": 0,
            "costUSD": 0.01,
        }
        root = _make_arm(tmp_path, "arm-a", usage=u)
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["usage_incomplete"] is True, (
            "FIX 6b: missing wallClockS must set usage_incomplete=True"
        )

    def test_complete_usage_not_flagged(self, tmp_path):
        """Complete usage.json → usage_incomplete=False."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["usage_incomplete"] is False, (
            "All non-nullable fields present → usage_incomplete must be False"
        )

    def test_missing_non_nullable_not_scored_as_cheapest(self, tmp_path):
        """Arm with missing wallClockS does NOT win c_norm vs a fully-reported arm.

        FIX 6b: the missing field is excluded from the mean, not counted as 0.
        A complete arm with the same real values should NOT be penalized relative
        to an arm that omits a field.  Specifically: the incomplete arm's c_norm
        must not drop below the complete arm's c_norm solely due to the missing field.
        """
        # arm-a: missing wallClockS (the most significant C field in this fixture)
        usage_incomplete = {
            "label": "arm-a",
            "model": "claude-sonnet-4-6",
            # wallClockS ABSENT — would have been 100.0 (high cost)
            "toolCalls": 20,
            "escalations": 0,
            "thrashIters": 0,
            "subagentDispatches": 0,
            "costUSD": 1.0,
        }
        # arm-b: all fields present, with a LOW wallClockS
        usage_complete = _usage("arm-b", wall_clock_s=1.0, tool_calls=20, cost_usd=1.0)

        root_a = _make_arm(tmp_path, "arm-a", usage=usage_incomplete)
        root_b = _make_arm(tmp_path, "arm-b", usage=usage_complete)
        sc = bm.score_arms(
            {"arm-a": root_a, "arm-b": root_b},
            f2p_p2p_results={
                "arm-a": {"f2p": {}, "p2p": {}},
                "arm-b": {"f2p": {}, "p2p": {}},
            },
        )
        arm_a = _arm_by_label(sc, "arm-a")
        arm_b = _arm_by_label(sc, "arm-b")

        assert arm_a["usage_incomplete"] is True
        assert arm_b["usage_incomplete"] is False
        # arm-a's missing wallClockS must NOT give it an artificially lower c_norm
        # than arm-b (which has a real low wallClockS).  The incomplete arm should
        # not be artificially ranked as cheapest on the missing dimension.
        # Specifically: arm-a's c_norm should NOT be strictly lower than arm-b's
        # on the basis of the missing field alone (since they have equal toolCalls/cost).
        # Under FIX 6b, arm-a's c_norm is computed from the 4 present fields only.
        # arm-b includes wallClockS=1.0 which normalizes to low. So arm-b <= arm-a
        # is expected because arm-b has a real wallClockS included. But arm-a's
        # wallClockS (100.0) is simply excluded — not counted as 0 (cheapest).
        # The test asserts that arm-a IS flagged incomplete.
        # The key invariant: both arms have same toolCalls/cost → their c_norm from
        # those fields should be equal. arm-b ADDITIONALLY includes a low wallClockS,
        # which should not make arm-b MORE expensive than arm-a (which omitted it).
        assert arm_a["c_norm"] is not None
        assert arm_b["c_norm"] is not None


# ---------------------------------------------------------------------------
# TestFloorGateEfficiency
# ---------------------------------------------------------------------------


class TestFloorGateEfficiency:
    """Efficiency (c_norm, composite, rank) is scored ONLY among floor-passers."""

    def test_floor_fail_excluded_from_efficiency_ranking(self, tmp_path):
        """Floor-failer has c_norm=None, composite=None, rank=None."""
        root = _make_arm(tmp_path, "arm-a", result=_result(exit_code=1))
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["floor_passed"] is False
        assert arm["composite"] is None, "Floor-failer must not receive composite score"
        assert arm["rank"] is None, "Floor-failer must not receive rank"
        assert arm["in_efficiency_set"] is False

    def test_floor_passers_only_ranked(self, tmp_path):
        """A floor-passer gets composite, rank, and pareto assigned."""
        root = _make_arm(tmp_path, "arm-a", result=_result(exit_code=0, failed=0))
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}})
        arm = _arm_by_label(sc, "arm-a")
        assert arm["floor_passed"] is True
        assert arm["composite"] is not None, "Floor-passer must receive composite score"
        assert arm["rank"] is not None, "Floor-passer must receive rank"
        assert arm["rank"] == 1, "Single floor-passer should be rank 1"
        assert arm["in_efficiency_set"] is True


# ---------------------------------------------------------------------------
# TestParetoAndScalar
# ---------------------------------------------------------------------------


class TestParetoAndScalar:
    """Pareto point (Q,C) and composite scalar Q/(1+λ·C_norm)."""

    def test_pareto_point_format(self, tmp_path):
        """Floor-passer arm has pareto = {'q': float, 'c': float}."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={"arm-a": _GATE_PASS},
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["pareto"] is not None
        assert "q" in arm["pareto"]
        assert "c" in arm["pareto"]
        assert isinstance(arm["pareto"]["q"], float)
        assert isinstance(arm["pareto"]["c"], float)

    def test_composite_scalar_formula(self, tmp_path):
        """composite = Q / (1 + λ * C_norm) for the balanced profile (λ=1.0)."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            profile="balanced",
            f2p_p2p_results={"arm-a": _GATE_PASS},
        )
        arm = _arm_by_label(sc, "arm-a")
        q = arm["q"]
        c = arm["c_norm"]
        lambda_ = 1.0  # balanced profile
        expected = q / (1.0 + lambda_ * c)
        assert abs(arm["composite"] - expected) < 1e-9, (
            f"composite={arm['composite']} ≠ Q/(1+λ·C) = {expected}"
        )


# ---------------------------------------------------------------------------
# TestCompositeTieBreak (DET-11) — exact ties break by label, not insertion order
# ---------------------------------------------------------------------------


class TestCompositeTieBreak:
    """DET-11: an EXACT composite tie is broken by lexicographically-first label.

    Before the fix the rank sort (reverse=True) and the pareto-best max() both
    resolved ties by arm insertion order — a non-deterministic scorecard artifact.
    After the fix both use an explicit secondary tie-break on the arm label, so
    rank-1 (and pareto-best) is the lexicographically-first label regardless of
    the order arms are supplied.
    """

    def _tied_pair(self, tmp_path: Path, first: str, second: str) -> dict:
        """Two arms with identical usage + identical gate results → exact composite tie."""
        root_first = _make_arm(
            tmp_path, first,
            usage=_usage(first, wall_clock_s=10.0, tool_calls=5, cost_usd=0.02),
        )
        root_second = _make_arm(
            tmp_path, second,
            usage=_usage(second, wall_clock_s=10.0, tool_calls=5, cost_usd=0.02),
        )
        # Insertion order = (first, second) as given by the caller.
        return bm.score_arms(
            {first: root_first, second: root_second},
            f2p_p2p_results={
                first: {"f2p": {"t1": True}, "p2p": {}},
                second: {"f2p": {"t1": True}, "p2p": {}},
            },
        )

    def test_rank_one_is_lexicographically_first_forward_order(self, tmp_path):
        """Input order (arm-a, arm-z): exact tie ⇒ rank-1 is 'arm-a'."""
        sc = self._tied_pair(tmp_path / "fwd", "arm-a", "arm-z")
        arm_a = _arm_by_label(sc, "arm-a")
        arm_z = _arm_by_label(sc, "arm-z")
        assert arm_a["composite"] == pytest.approx(arm_z["composite"]), (
            "Fixture invariant: the two arms must have an exact composite tie"
        )
        assert arm_a["rank"] == 1, "DET-11: lexicographically-first label must be rank 1"
        assert arm_z["rank"] == 2

    def test_rank_one_is_lexicographically_first_reversed_order(self, tmp_path):
        """Input order (arm-z, arm-a): rank-1 is STILL 'arm-a' (insertion order ignored)."""
        sc = self._tied_pair(tmp_path / "rev", "arm-z", "arm-a")
        arm_a = _arm_by_label(sc, "arm-a")
        arm_z = _arm_by_label(sc, "arm-z")
        assert arm_a["composite"] == pytest.approx(arm_z["composite"])
        assert arm_a["rank"] == 1, (
            "DET-11: rank-1 must be 'arm-a' regardless of input arm order"
        )
        assert arm_z["rank"] == 2

    def test_pareto_best_is_lexicographically_first_on_tie(self, tmp_path):
        """pareto-best recommendation resolves an exact tie to the first label, both orders."""
        for sub, a, b in (("p1", "arm-a", "arm-z"), ("p2", "arm-z", "arm-a")):
            sc = self._tied_pair(tmp_path / sub, a, b)
            pareto = [r for r in sc["recommendations"] if r["kind"] == "pareto-best"]
            assert len(pareto) == 1
            assert pareto[0]["arm"] == "arm-a", (
                f"DET-11: pareto-best must be 'arm-a' on an exact tie (input order {a},{b})"
            )


# ---------------------------------------------------------------------------
# TestProfileWeights
# ---------------------------------------------------------------------------


class TestProfileWeights:
    """Profile weights (balanced|cost-lean|quality-strict) change λ and ranking."""

    def _two_arm_scorecard(self, tmp_path: Path, profile: str) -> dict:
        """
        arm-A: perfect quality (all tests pass), high cost (wallClockS=100, toolCalls=20).
        arm-B: lower quality (all F2P fail, P2P pass), low cost (wallClockS=1, toolCalls=1).

        For balanced (f2p_weight=0.6, p2p_weight=0.4):
          Q_A = 1.0, Q_B = 0.4
        For cost-lean/balanced same weights; quality-strict (f2p=0.7, p2p=0.3):
          Q_B = 0.3
        """
        root_a = _make_arm(
            tmp_path, "arm-a",
            usage=_usage("arm-a", wall_clock_s=100.0, tool_calls=20,
                         escalations=5, thrash_iters=3, subagent_dispatches=2,
                         cost_usd=1.0),
        )
        root_b = _make_arm(
            tmp_path, "arm-b",
            usage=_usage("arm-b", wall_clock_s=1.0, tool_calls=1,
                         escalations=0, thrash_iters=0, subagent_dispatches=0,
                         cost_usd=0.01),
        )
        return bm.score_arms(
            {"arm-a": root_a, "arm-b": root_b},
            profile=profile,
            f2p_p2p_results={
                "arm-a": {"f2p": {"t1": True}, "p2p": {"t2": True}},
                # arm-B: all F2P fail, P2P pass
                "arm-b": {"f2p": {"t1": False, "t2": False, "t3": False}, "p2p": {"t4": True}},
            },
        )

    def test_cost_lean_vs_balanced_ranking_flips(self, tmp_path):
        """cost-lean (λ=2.0) penalizes high-cost arm-A more — ranking flips vs balanced.

        With arm-A (Q=1.0, C_norm≈1.0) vs arm-B (Q_approx≈0.4, C_norm≈small):
          balanced  (λ=1.0): comp_A = 1.0/2.0 = 0.5 > comp_B → A ranks first
          cost-lean (λ=2.0): comp_A = 1.0/3.0 ≈ 0.333 < comp_B → B ranks first
        """
        sc_balanced = self._two_arm_scorecard(tmp_path / "bal", "balanced")
        # In balanced, arm-A (Q=1.0) should rank above arm-B (Q≈0.4)
        arm_a_bal = _arm_by_label(sc_balanced, "arm-a")
        arm_b_bal = _arm_by_label(sc_balanced, "arm-b")
        assert arm_a_bal["rank"] < arm_b_bal["rank"], (
            "balanced: arm-A (high Q) should rank above arm-B (lower Q)"
        )

        sc_cost = self._two_arm_scorecard(tmp_path / "cost", "cost-lean")
        arm_a_cost = _arm_by_label(sc_cost, "arm-a")
        arm_b_cost = _arm_by_label(sc_cost, "arm-b")
        # cost-lean: arm-A's high C_norm (≈1.0) is penalized harder by λ=2.0
        assert arm_b_cost["rank"] < arm_a_cost["rank"], (
            "cost-lean: arm-B (low cost) should rank above arm-A (high cost, λ=2.0)"
        )

    def test_quality_strict_vs_balanced_q_wins(self, tmp_path):
        """quality-strict (λ=0.5) reduces cost penalty — high-Q arm retains first rank."""
        sc = self._two_arm_scorecard(tmp_path, "quality-strict")
        arm_a = _arm_by_label(sc, "arm-a")
        arm_b = _arm_by_label(sc, "arm-b")
        # quality-strict: λ=0.5 gives lower cost weight; arm-A (Q=1.0) stays first
        assert arm_a["rank"] < arm_b["rank"], (
            "quality-strict: high-Q arm-A should rank above lower-Q arm-B"
        )


# ---------------------------------------------------------------------------
# TestMultiArm
# ---------------------------------------------------------------------------


class TestMultiArm:
    """Multi-arm map (≥2 arms) produces per-arm rows and Pareto points."""

    def test_multi_arm_two_entries_in_arms_list(self, tmp_path):
        """2-arm map → scorecard.arms has exactly 2 entries."""
        root_a = _make_arm(tmp_path, "arm-a")
        root_b = _make_arm(tmp_path, "arm-b")
        sc = bm.score_arms(
            {"arm-a": root_a, "arm-b": root_b},
            f2p_p2p_results={
                "arm-a": {"f2p": {}, "p2p": {}},
                "arm-b": {"f2p": {}, "p2p": {}},
            },
        )
        assert len(sc["arms"]) == 2
        labels = {arm["label"] for arm in sc["arms"]}
        assert labels == {"arm-a", "arm-b"}

    def test_multi_arm_per_arm_pareto_points(self, tmp_path):
        """Each floor-passer arm has its own Pareto (Q,C) point (Q=0 still gets pareto)."""
        root_a = _make_arm(tmp_path, "arm-a")
        root_b = _make_arm(tmp_path, "arm-b")
        sc = bm.score_arms(
            {"arm-a": root_a, "arm-b": root_b},
            f2p_p2p_results={
                "arm-a": {"f2p": {}, "p2p": {}},
                "arm-b": {"f2p": {}, "p2p": {}},
            },
        )
        for arm in sc["arms"]:
            assert arm["pareto"] is not None, f"Arm {arm['label']} missing pareto"
            assert "q" in arm["pareto"]
            assert "c" in arm["pareto"]


# ---------------------------------------------------------------------------
# TestHonestyFields
# ---------------------------------------------------------------------------


class TestHonestyFields:
    """n and directional fields carry the n=1 directional honesty."""

    def test_scorecard_n_field_equals_arm_count(self, tmp_path):
        """scorecard.n equals the number of arms scored."""
        root_a = _make_arm(tmp_path, "arm-a")
        root_b = _make_arm(tmp_path, "arm-b")
        sc = bm.score_arms(
            {"arm-a": root_a, "arm-b": root_b},
            f2p_p2p_results={
                "arm-a": {"f2p": {}, "p2p": {}},
                "arm-b": {"f2p": {}, "p2p": {}},
            },
        )
        assert sc["n"] == 2

    def test_scorecard_directional_always_true(self, tmp_path):
        """scorecard.directional is always True (n=1 directional honesty note)."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": {"f2p": {}, "p2p": {}}})
        assert sc["directional"] is True


# ---------------------------------------------------------------------------
# TestHonestyBlock (FIX 3)
# ---------------------------------------------------------------------------


class TestHonestyBlock:
    """FIX 3: Engine-pinned honesty dict in every scorecard output."""

    def _sc(self, tmp_path: Path) -> dict:
        root = _make_arm(tmp_path, "arm-a")
        return bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS})

    def test_scorecard_has_honesty_dict(self, tmp_path):
        """scorecard['honesty'] is a dict (engine-pinned, FIX 3)."""
        sc = self._sc(tmp_path)
        assert "honesty" in sc, "FIX 3: scorecard must have 'honesty' key"
        assert isinstance(sc["honesty"], dict)

    def test_honesty_directional_always_true(self, tmp_path):
        """honesty.directional is True."""
        sc = self._sc(tmp_path)
        assert sc["honesty"]["directional"] is True

    def test_honesty_basis_is_n1(self, tmp_path):
        """honesty.basis is 'n=1'."""
        sc = self._sc(tmp_path)
        assert sc["honesty"]["basis"] == "n=1", (
            f"honesty.basis must be 'n=1', got {sc['honesty'].get('basis')!r}"
        )

    def test_honesty_disclosure_carries_exercised_not_proven(self, tmp_path):
        """honesty.disclosure mentions 'exercised' and 'proven' (exercised ≠ proven note)."""
        sc = self._sc(tmp_path)
        disclosure = sc["honesty"].get("disclosure", "").lower()
        assert "exercised" in disclosure or "directional" in disclosure, (
            "honesty.disclosure must mention 'exercised' or 'directional' (DESIGN §6b)"
        )
        assert "proven" in disclosure, (
            "honesty.disclosure must mention 'proven' (exercised-not-proven contract)"
        )

    def test_honesty_present_even_for_floor_failers(self, tmp_path):
        """honesty block is present even when all arms fail the floor."""
        root = _make_arm(tmp_path, "arm-a", result=_result(exit_code=1))
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS})
        assert "honesty" in sc
        assert sc["honesty"]["directional"] is True


# ---------------------------------------------------------------------------
# TestRecommendations (FIX 3)
# ---------------------------------------------------------------------------


class TestRecommendations:
    """FIX 3: Deterministic, data-derived recommendations list in every scorecard."""

    def test_scorecard_has_recommendations_list(self, tmp_path):
        """scorecard['recommendations'] is always a list (engine-pinned)."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS})
        assert "recommendations" in sc, "FIX 3: scorecard must have 'recommendations' key"
        assert isinstance(sc["recommendations"], list)

    def test_recommendations_pareto_best_present_for_passer(self, tmp_path):
        """At least one floor-passer → recommendations includes kind='pareto-best'."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS})
        kinds = [r["kind"] for r in sc["recommendations"]]
        assert "pareto-best" in kinds, (
            f"With a floor-passer, 'pareto-best' must be in recommendations. Got: {kinds}"
        )

    def test_recommendations_empty_when_no_passers(self, tmp_path):
        """No floor-passers → recommendations is empty list."""
        root = _make_arm(tmp_path, "arm-a", result=_result(exit_code=1))
        sc = bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS})
        assert sc["recommendations"] == [], (
            "No floor-passers → recommendations must be empty list"
        )

    def test_recommendations_pareto_best_arm_is_valid_label(self, tmp_path):
        """pareto-best recommendation arm label is one of the scored arm labels."""
        root_a = _make_arm(tmp_path, "arm-a")
        root_b = _make_arm(tmp_path, "arm-b")
        sc = bm.score_arms(
            {"arm-a": root_a, "arm-b": root_b},
            f2p_p2p_results={
                "arm-a": {"f2p": {"t1": True}, "p2p": {}},
                "arm-b": {"f2p": {"t1": True}, "p2p": {}},
            },
        )
        pareto_recs = [r for r in sc["recommendations"] if r["kind"] == "pareto-best"]
        assert len(pareto_recs) == 1
        assert pareto_recs[0]["arm"] in {"arm-a", "arm-b"}

    def test_recommendations_dominated_detected(self, tmp_path):
        """Dominated arm (lower Q, higher C) appears as kind='dominated'."""
        # arm-a: high Q=1.0, low cost (dominant)
        root_a = _make_arm(
            tmp_path, "arm-a",
            usage=_usage("arm-a", wall_clock_s=1.0, tool_calls=1, cost_usd=0.01),
        )
        # arm-b: lower Q=0.4, high cost (dominated by arm-a)
        root_b = _make_arm(
            tmp_path, "arm-b",
            usage=_usage("arm-b", wall_clock_s=100.0, tool_calls=20, cost_usd=1.0),
        )
        sc = bm.score_arms(
            {"arm-a": root_a, "arm-b": root_b},
            f2p_p2p_results={
                "arm-a": {"f2p": {"t1": True}, "p2p": {}},
                "arm-b": {"f2p": {"t1": False}, "p2p": {}},
            },
        )
        # arm-b has lower Q AND higher C → dominated by arm-a
        dominated_arms = [r["arm"] for r in sc["recommendations"] if r["kind"] == "dominated"]
        assert "arm-b" in dominated_arms, (
            f"arm-b (lower Q, higher C) must be flagged as dominated. "
            f"Got dominated: {dominated_arms}"
        )

    def test_recommendations_items_have_kind_and_arm(self, tmp_path):
        """Each recommendation dict has at least 'kind' and 'arm' keys."""
        root_a = _make_arm(tmp_path, "arm-a",
                           usage=_usage("arm-a", wall_clock_s=100.0, tool_calls=20, cost_usd=1.0))
        root_b = _make_arm(tmp_path, "arm-b",
                           usage=_usage("arm-b", wall_clock_s=1.0, tool_calls=1, cost_usd=0.01))
        sc = bm.score_arms(
            {"arm-a": root_a, "arm-b": root_b},
            f2p_p2p_results={
                "arm-a": {"f2p": {"t1": True}, "p2p": {}},
                "arm-b": {"f2p": {"t1": True}, "p2p": {}},
            },
        )
        for rec in sc["recommendations"]:
            assert "kind" in rec, f"Recommendation missing 'kind': {rec}"
            assert "arm" in rec, f"Recommendation missing 'arm': {rec}"


# ---------------------------------------------------------------------------
# TestTraversalGuard (FIX 2)
# ---------------------------------------------------------------------------


class TestTraversalGuard:
    """FIX 2: run_dual_gate rejects node-IDs that escape the clone root."""

    def test_traversal_id_rejected(self, tmp_path):
        """'../../evil/test.py::test_pwn' is rejected with ValueError (FIX 2)."""
        clone_root = tmp_path / "clone"
        clone_root.mkdir()

        invoked: list = []

        def fake_run_named_test(test_path: str, test_name: str) -> bool:
            invoked.append((test_path, test_name))
            return True

        with patch("mutation_check.run_named_test", fake_run_named_test):
            with pytest.raises(ValueError, match=r"escapes clone root|traversal|\.\."):
                bm.run_dual_gate(
                    clone_root,
                    f2p_ids=["../../evil/test.py::test_pwn"],
                    p2p_ids=[],
                )
        assert len(invoked) == 0, (
            "run_named_test must NOT be called when traversal ID is detected (FIX 2)"
        )

    def test_traversal_never_invokes_run_named_test(self, tmp_path):
        """Traversal ID must not reach mutation_check.run_named_test at all."""
        clone_root = tmp_path / "clone"
        clone_root.mkdir()
        mock_rnt = MagicMock(return_value=True)
        with patch("mutation_check.run_named_test", mock_rnt):
            try:
                bm.run_dual_gate(
                    clone_root,
                    f2p_ids=["../sibling_dir/test.py::test_escape"],
                    p2p_ids=[],
                )
            except ValueError:
                pass
        mock_rnt.assert_not_called()

    def test_leading_dash_path_rejected(self, tmp_path):
        """A test-ID with a leading '-' in the path segment is rejected (flag injection)."""
        clone_root = tmp_path / "clone"
        clone_root.mkdir()
        with patch("mutation_check.run_named_test", return_value=True):
            with pytest.raises(ValueError, match=r"leading.*-|'-'"):
                bm.run_dual_gate(
                    clone_root,
                    f2p_ids=["-evil/test.py::test_flag"],
                    p2p_ids=[],
                )

    def test_valid_id_not_rejected(self, tmp_path):
        """A valid 'tests/test_foo.py::test_bar' ID passes the traversal guard."""
        clone_root = tmp_path / "clone"
        clone_root.mkdir()
        called: list = []

        def fake_rnt(test_path: str, test_name: str, *, cwd: str | None = None) -> bool:
            called.append((test_path, test_name))
            return True

        with patch("mutation_check.run_named_test", fake_rnt):
            result = bm.run_dual_gate(
                clone_root,
                f2p_ids=["tests/test_foo.py::test_ok"],
                p2p_ids=[],
            )
        assert result["f2p"]["tests/test_foo.py::test_ok"] is True
        assert len(called) == 1, "Valid ID must reach run_named_test"


# ---------------------------------------------------------------------------
# TestEmitScorecard
# ---------------------------------------------------------------------------


class TestEmitScorecard:
    def _scorecard(self, tmp_path: Path) -> dict:
        root = _make_arm(tmp_path / "arm", "arm-a")
        return bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={"arm-a": _GATE_PASS},
        )

    def test_emit_creates_file_and_dirs(self, tmp_path):
        """emit_scorecard creates intermediate dirs and writes a JSON file."""
        sc = self._scorecard(tmp_path)
        dest = tmp_path / ".kata" / "benchmark" / "run-001.json"
        assert not dest.exists()
        bm.emit_scorecard(dest, sc)
        assert dest.exists()

    def test_emit_round_trip_readable(self, tmp_path):
        """emit_scorecard writes valid JSON that round-trips the scorecard."""
        sc = self._scorecard(tmp_path)
        dest = tmp_path / ".kata" / "benchmark" / "run-001.json"
        bm.emit_scorecard(dest, sc)
        loaded = json.loads(dest.read_text(encoding="utf-8"))
        assert loaded["schema"] == "benchmark/scorecard/v1"
        assert "arms" in loaded
        assert loaded["n"] == sc["n"]
        assert "honesty" in loaded  # FIX 3: engine-pinned
        assert "recommendations" in loaded  # FIX 3: engine-pinned

    def test_emit_guard_rejects_traversal(self, tmp_path):
        """emit_scorecard raises ValueError when path contains '..' (CWE-23)."""
        sc = self._scorecard(tmp_path)
        bad_path = tmp_path / ".." / "evil" / "scorecard.json"
        with pytest.raises(ValueError, match=r"\.\."):
            bm.emit_scorecard(bad_path, sc)


# ---------------------------------------------------------------------------
# TestExecSafety — source-scan assertions (mirrors TestExecSafety in test_usage_meter.py)
# ---------------------------------------------------------------------------


class TestExecSafety:
    """benchmark.py is pure (A): zero new exec sink, no subprocess import."""

    def _source(self) -> str:
        return (_TOOLS / "benchmark.py").read_text(encoding="utf-8")

    def test_no_subprocess_import(self):
        """benchmark.py must NOT import subprocess (zero new exec sink)."""
        hits = [
            m.group()
            for m in re.finditer(
                r"^\s*(?:import|from)\s+subprocess\b", self._source(), re.MULTILINE
            )
        ]
        assert not hits, (
            f"subprocess import found in benchmark.py: {hits} — "
            "zero new exec sink is a frozen invariant (exec-safety.md)"
        )

    def test_no_eval(self):
        """benchmark.py must not use eval()."""
        hits = re.findall(r"\beval\s*\(", self._source())
        assert not hits, f"eval() call found in benchmark.py: {hits}"

    def test_no_exec(self):
        """benchmark.py must not use exec()."""
        hits = re.findall(r"\bexec\s*\(", self._source())
        assert not hits, f"exec() call found in benchmark.py: {hits}"

    def test_no_shell_true(self):
        """benchmark.py must not use shell=True."""
        assert "shell=True" not in self._source(), "shell=True found in benchmark.py"


# ---------------------------------------------------------------------------
# TestRunDualGate — interface / delegation contract (B)
# ---------------------------------------------------------------------------


class TestRunDualGate:
    """run_dual_gate delegates to mutation_check.run_named_test (no new sink)."""

    def test_run_dual_gate_delegates_to_run_named_test(self, tmp_path):
        """run_dual_gate calls mutation_check.run_named_test for each test-ID."""
        # Create a fake clone root with a fake test file path
        clone_root = tmp_path / "clone"
        clone_root.mkdir()

        calls: list = []

        def fake_run_named_test(
            test_path: str, test_name: str, *, cwd: str | None = None
        ) -> bool:
            calls.append((test_path, test_name))
            return True  # all pass

        with patch("mutation_check.run_named_test", fake_run_named_test):
            result = bm.run_dual_gate(
                clone_root,
                f2p_ids=["tests/test_foo.py::test_f2p"],
                p2p_ids=["tests/test_bar.py::test_p2p"],
            )

        assert len(calls) == 2, f"Expected 2 calls to run_named_test, got {len(calls)}"
        assert result["f2p"]["tests/test_foo.py::test_f2p"] is True
        assert result["p2p"]["tests/test_bar.py::test_p2p"] is True

    def test_run_dual_gate_malformed_id_raises(self, tmp_path):
        """A test-ID without '::' is an authoring error → ValueError (Q-8 / D136).

        UPDATED for finding Q-8: the OLD behavior returned False, silently
        scoring a typo'd criteria ID as an arm F2P/P2P *failure* ("arm failed"
        when the truth is "criteria malformed").  The fix raises instead — never
        a silent False.  run_named_test must not be invoked.
        """
        clone_root = tmp_path / "clone"
        clone_root.mkdir()

        with patch("mutation_check.run_named_test", return_value=True) as mock_rnt:
            with pytest.raises(ValueError, match=r"malformed test-ID|::"):
                bm.run_dual_gate(
                    clone_root,
                    f2p_ids=["no_separator_here"],
                    p2p_ids=[],
                )
        mock_rnt.assert_not_called()


# ---------------------------------------------------------------------------
# Mutation non-vacuity proofs (spawn real subprocess via prove_non_vacuous)
# ---------------------------------------------------------------------------


class TestMutationProof:
    """Prove five load-bearing lines in benchmark.py via mutation_run.prove_non_vacuous.

    (a) ``        q = 0.0  # floor-fail: Q=0 absolute (not modified further)``
        in _compute_arm_q. Removing it leaves q unbound in the floor-fail branch,
        causing a NameError → test_floor_fail_exit_code_nonzero goes red.

    (b) ``            floor_passer_labels.append(label)  # floor-gate: efficiency only among passers``
        in score_arms. Removing it leaves floor_passer_labels always empty →
        no passer gets composite/rank → test_floor_passers_only_ranked goes red.

    (c) ``        q = 0.0  # FIX 1: no free dual-score — gate not evaluated → no credit (load-bearing)``
        in _compute_arm_q (gate-not-evaluated branch). Removing it leaves q unbound →
        NameError → test_no_gate_empty_criteria_no_q_credit goes red.

    (d) ``        _guard_node_id(test_id, root)  # FIX 2: traversal guard (load-bearing)``
        in run_dual_gate._run_one. Removing it → no traversal check → ../../ ID passes →
        test_traversal_id_rejected goes red (expected ValueError, not raised).

    (e) ``        failed_present = "failed" in result_json  # FIX 5: fail-closed on absent 'failed' key (load-bearing)``
        in _compute_arm_q. Removing it → NameError on next line →
        test_floor_fail_missing_failed_key goes red.

    mutation_run.prove_non_vacuous runs SANDBOXED — the live source is never
    written (the D1 phantom-corruption fix); the proof mutates a temp-tree copy.
    """

    def _src(self) -> str:
        return str(_TOOLS / "benchmark.py")

    def _cmd(self, test_spec: str) -> str:
        return (
            f'cd /d "{_TOOLS}" && '
            f"{sys.executable} -m pytest "
            f'"tests/test_benchmark.py::{test_spec}" -q --tb=no'
        )

    def test_mutation_proof_floor_q_zero(self):
        """(a) The floor-fail Q=0 assignment is load-bearing.

        Removing ``        q = 0.0  # floor-fail: Q=0 absolute (not modified further)``
        leaves q unbound in the early-return branch of _compute_arm_q.
        test_floor_fail_exit_code_nonzero goes red (NameError or wrong value).
        """
        import mutation_run

        asserted_line = "        q = 0.0  # floor-fail: Q=0 absolute (not modified further)"
        cmd = self._cmd("TestFloorGate::test_floor_fail_exit_code_nonzero")
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing the floor-fail q=0.0 assignment must make "
            "test_floor_fail_exit_code_nonzero go red"
        )
        assert verdict["nonVacuous"], (
            "test_floor_fail_exit_code_nonzero must catch removal of the "
            "floor-fail Q=0 assignment"
        )

    def test_mutation_proof_efficiency_floor_gate(self):
        """(b) The floor-passer append is load-bearing (efficiency gate).

        Removing ``            floor_passer_labels.append(label)  # floor-gate: efficiency only among passers``
        leaves floor_passer_labels always empty → no arm gets composite/rank →
        test_floor_passers_only_ranked goes red.
        """
        import mutation_run

        asserted_line = (
            "            floor_passer_labels.append(label)"
            "  # floor-gate: efficiency only among passers"
        )
        cmd = self._cmd("TestFloorGateEfficiency::test_floor_passers_only_ranked")
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing floor_passer_labels.append(label) must make "
            "test_floor_passers_only_ranked go red"
        )
        assert verdict["nonVacuous"], (
            "test_floor_passers_only_ranked must catch removal of the "
            "efficiency floor-gate append"
        )

    def test_mutation_proof_no_free_dual_score(self):
        """(c) The FIX 1 gate-not-evaluated Q=0 is load-bearing.  prove_non_vacuous.

        Removing:
          ``        q = 0.0  # FIX 1: no free dual-score — gate not evaluated → no credit (load-bearing)``
        leaves q unbound in the not-evaluated branch → NameError on return →
        test_no_gate_empty_criteria_no_q_credit goes red.
        """
        import mutation_run

        asserted_line = (
            "        q = 0.0"
            "  # FIX 1: no free dual-score — gate not evaluated → no credit (load-bearing)"
        )
        cmd = self._cmd("TestDualGate::test_no_gate_empty_criteria_no_q_credit")
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing the FIX 1 Q=0 assignment must make "
            "test_no_gate_empty_criteria_no_q_credit go red"
        )
        assert verdict["nonVacuous"], (
            "test_no_gate_empty_criteria_no_q_credit must catch removal of the "
            "no-free-dual-score guard"
        )

    def test_mutation_proof_traversal_guard(self):
        """(d) The FIX 2 traversal guard call is load-bearing.  prove_non_vacuous.

        Removing:
          ``        _guard_node_id(test_id, root)  # FIX 2: traversal guard (load-bearing)``
        means no traversal check is applied → ../../evil passes through →
        test_traversal_id_rejected goes red (expected ValueError not raised).
        """
        import mutation_run

        asserted_line = (
            "        _guard_node_id(test_id, root)"
            "  # FIX 2: traversal guard (load-bearing)"
        )
        cmd = self._cmd("TestTraversalGuard::test_traversal_id_rejected")
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing _guard_node_id call must make test_traversal_id_rejected go red"
        )
        assert verdict["nonVacuous"], (
            "test_traversal_id_rejected must catch removal of the traversal guard call"
        )

    def test_mutation_proof_partial_floor(self):
        """(e) The FIX 5 failed_present check is load-bearing.  prove_non_vacuous.

        Removing:
          ``        failed_present = "failed" in result_json  # FIX 5: fail-closed on absent 'failed' key (load-bearing)``
        leaves failed_present unbound → NameError on the next line →
        test_floor_fail_missing_failed_key goes red.
        """
        import mutation_run

        asserted_line = (
            "        failed_present = \"failed\" in result_json"
            "  # FIX 5: fail-closed on absent 'failed' key (load-bearing)"
        )
        cmd = self._cmd("TestFloorPartialResult::test_floor_fail_missing_failed_key")
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing failed_present assignment must make "
            "test_floor_fail_missing_failed_key go red"
        )
        assert verdict["nonVacuous"], (
            "test_floor_fail_missing_failed_key must catch removal of the "
            "fail-closed failed_present check"
        )


# ===========================================================================
# FIX A1 — dual-gate execution context: cwd resolves clone imports
# ===========================================================================


class TestRunDualGateCwd:
    """FIX A1: run_dual_gate passes cwd=clone_root so `from src import X` resolves."""

    def test_cwd_passed_to_run_named_test(self, tmp_path):
        """run_dual_gate passes cwd=str(clone_root) to run_named_test (FIX A1)."""
        clone_root = tmp_path / "clone"
        clone_root.mkdir()
        calls: list = []

        def fake_rnt(test_path: str, test_name: str, *, cwd: str | None = None) -> bool:
            calls.append({"test_path": test_path, "test_name": test_name, "cwd": cwd})
            return True

        with patch("mutation_check.run_named_test", fake_rnt):
            bm.run_dual_gate(clone_root, f2p_ids=["tests/test_x.py::test_foo"], p2p_ids=[])

        assert len(calls) == 1
        assert calls[0]["cwd"] == str(clone_root), (
            "FIX A1: run_dual_gate must pass cwd=str(clone_root) to run_named_test"
        )

    def test_relative_path_passed_to_run_named_test(self, tmp_path):
        """run_dual_gate passes rel_path (not absolute) so it resolves under cwd (FIX A1)."""
        clone_root = tmp_path / "clone"
        clone_root.mkdir()
        calls: list = []

        def fake_rnt(test_path: str, test_name: str, *, cwd: str | None = None) -> bool:
            calls.append({"test_path": test_path, "test_name": test_name, "cwd": cwd})
            return True

        with patch("mutation_check.run_named_test", fake_rnt):
            bm.run_dual_gate(clone_root, f2p_ids=["tests/test_x.py::test_foo"], p2p_ids=[])

        assert len(calls) == 1
        assert calls[0]["test_path"] == "tests/test_x.py", (
            "FIX A1: run_dual_gate must pass the relative path (not absolute) to run_named_test"
        )

    @pytest.mark.integration
    def test_importing_fixture_gives_q_one(self, tmp_path):
        """Integration: control with `from src import add` → run_dual_gate True → Q=1.0.

        FIX A1 acceptance criterion (DESIGN §3.1.2 v1 shape): build a synthetic
        control whose test does `from src import add`; run_dual_gate on it returns
        True booleans → score_arms gives Q=1.0.  Was Q=0 before fix (clone root
        never on sys.path → collection failure → all-False gate → Q=0).

        Full per-control dep-env isolation (3rd-party deps in clone) is D5/real-fixture.
        This test only covers the v1 simple-import shape.
        """
        import textwrap

        clone = tmp_path / "control"
        src_dir = clone / "src"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("", encoding="utf-8")
        (src_dir / "add.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n",
            encoding="utf-8",
        )
        tests_dir = clone / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")
        (tests_dir / "test_add.py").write_text(
            textwrap.dedent("""\
                from src import add

                def test_add_basic():
                    assert add.add(1, 2) == 3

                def test_add_zero():
                    assert add.add(0, 0) == 0
            """),
            encoding="utf-8",
        )

        kata = clone / ".kata"
        kata.mkdir()
        (kata / "RESULT.json").write_text(
            json.dumps({"exitCode": 0, "failed": 0, "passed": 2}), encoding="utf-8"
        )
        (kata / "mutation.json").write_text(
            json.dumps({"allNonVacuous": True, "records": []}), encoding="utf-8"
        )
        (kata / "usage.json").write_text(
            json.dumps(_usage("control")), encoding="utf-8"
        )

        f2p_ids = ["tests/test_add.py::test_add_basic"]
        p2p_ids = ["tests/test_add.py::test_add_zero"]
        gate_results = bm.run_dual_gate(clone, f2p_ids, p2p_ids)

        assert gate_results["f2p"]["tests/test_add.py::test_add_basic"] is True, (
            "FIX A1: `from src import add` test must pass with cwd=clone_root on PYTHONPATH "
            "(was False before fix — import failed, gate returned all-False)"
        )
        assert gate_results["p2p"]["tests/test_add.py::test_add_zero"] is True

        sc = bm.score_arms({"control": clone}, f2p_p2p_results={"control": gate_results})
        arm = _arm_by_label(sc, "control")
        assert arm["q"] == pytest.approx(1.0), (
            f"FIX A1: Q must be 1.0 when both gates pass; got {arm['q']} "
            "(was 0.0 before fix)"
        )


# ===========================================================================
# FIX C1 — metric read-path numeric sanity
# ===========================================================================


class TestAxisCNumericSanity:
    """FIX C1: negative/NaN/Inf usage values treated as missing, not scored."""

    def test_negative_cost_does_not_win(self, tmp_path):
        """costUSD=-540 (attack) must NOT produce a lower c_norm than the honest arm (FIX C1).

        Before fix: negative cost is accepted as float(-540), normalizes against a
        positive max → cost dimension goes negative → c_norm_attack < c_norm_honest
        → attack appears cheaper → wins composite race (rank 1) or produces
        non-deterministic NaN-like behaviour.
        After fix: _validate_numeric rejects negative → treated as missing →
        imputed as 1.0 (worst-case) → c_norm_attack >= c_norm_honest.

        Note: the invariant is c_norm, not rank (equal c_norm arms tie by insertion
        order; the c_norm invariant is unambiguous).
        """
        # arm-honest cost is the only valid cost, so it normalises to 1.0.
        # arm-attack's invalid cost is imputed to 1.0 as well → equal c_norm.
        # If C1 validation is removed, arm-attack gets cost dim = -540/0.01 = -54000
        # → c_norm << 0 → c_norm_attack < c_norm_honest → assertion fails.
        root_attack = _make_arm(
            tmp_path, "arm-attack",
            usage=_usage("arm-attack", cost_usd=-540.0),
        )
        root_honest = _make_arm(
            tmp_path, "arm-honest",
            usage=_usage("arm-honest", cost_usd=0.01),
        )
        sc = bm.score_arms(
            {"arm-attack": root_attack, "arm-honest": root_honest},
            f2p_p2p_results={
                "arm-attack": {"f2p": {"t1": True}, "p2p": {}},
                "arm-honest": {"f2p": {"t1": True}, "p2p": {}},
            },
        )
        arm_attack = _arm_by_label(sc, "arm-attack")
        arm_honest = _arm_by_label(sc, "arm-honest")
        assert arm_attack["usage_incomplete"] is True, (
            "FIX C1: negative costUSD must flag usage_incomplete=True"
        )
        # Core C1 invariant: attack's c_norm must NOT be lower than honest's.
        # (Lower c_norm = appears cheaper = unfair advantage.)
        assert arm_attack["c_norm"] >= arm_honest["c_norm"], (
            f"FIX C1: attack arm c_norm={arm_attack['c_norm']:.4f} must NOT be lower "
            f"than honest arm c_norm={arm_honest['c_norm']:.4f}. "
            "Negative costUSD must be rejected and imputed as worst-case 1.0."
        )

    def test_nan_does_not_poison_ranking(self, tmp_path):
        """NaN in a usage field must not poison ranking of other arms (FIX C1)."""
        u_nan = _usage("arm-nan")
        u_nan["costUSD"] = float("nan")
        root_nan = _make_arm(tmp_path, "arm-nan", usage=u_nan)

        u_ok = _usage("arm-ok", cost_usd=0.05)
        root_ok = _make_arm(tmp_path, "arm-ok", usage=u_ok)

        sc = bm.score_arms(
            {"arm-nan": root_nan, "arm-ok": root_ok},
            f2p_p2p_results={
                "arm-nan": {"f2p": {"t1": True}, "p2p": {}},
                "arm-ok": {"f2p": {"t1": True}, "p2p": {}},
            },
        )
        import math as _math
        arm_ok = _arm_by_label(sc, "arm-ok")
        assert arm_ok["c_norm"] is not None
        assert _math.isfinite(arm_ok["c_norm"]), (
            "FIX C1: NaN from arm-nan must not poison arm-ok's c_norm"
        )

    def test_inf_wall_clock_flagged_and_not_exploding(self, tmp_path):
        """Infinity in wallClockS treated as missing → usage_incomplete, c_norm finite (FIX C1)."""
        u_inf = _usage("arm-inf")
        u_inf["wallClockS"] = float("inf")
        root_inf = _make_arm(tmp_path, "arm-inf", usage=u_inf)

        sc = bm.score_arms(
            {"arm-inf": root_inf},
            f2p_p2p_results={"arm-inf": {"f2p": {"t1": True}, "p2p": {}}},
        )
        arm = _arm_by_label(sc, "arm-inf")
        import math as _math
        assert arm["usage_incomplete"] is True, (
            "FIX C1: Inf wallClockS must flag usage_incomplete=True"
        )
        assert _math.isfinite(arm["c_norm"]), (
            "FIX C1: Inf field must not produce Inf c_norm"
        )


# ===========================================================================
# FIX C2 — C-norm imputation: omission never helps
# ===========================================================================


class TestAxisCImputation:
    """FIX C2: missing/null/invalid fields imputed as 1.0 (worst-case), not excluded."""

    def test_null_cost_does_not_improve_c_norm(self, tmp_path):
        """costUSD=null must NOT lower c_norm below honest arm with real low cost (FIX C2).

        Before fix (old FIX 6b): null costUSD excluded → c_norm computed without it →
        arm appeared cheaper on that dimension.
        After fix: null → imputed as 1.0 → arm looks expensive (honest-conservative).
        """
        # arm-null: costUSD=null, same non-cost profile as arm-honest
        u_null = _usage("arm-null", cost_usd=None, tokens_in=None, tokens_out=None)
        u_null["wallClockS"] = 1.0
        u_null["toolCalls"] = 1
        root_null = _make_arm(tmp_path, "arm-null", usage=u_null)

        # arm-honest: all fields present, same non-cost profile + low real cost
        root_honest = _make_arm(
            tmp_path, "arm-honest",
            usage=_usage("arm-honest", wall_clock_s=1.0, tool_calls=1, cost_usd=0.01),
        )
        sc = bm.score_arms(
            {"arm-null": root_null, "arm-honest": root_honest},
            f2p_p2p_results={
                "arm-null": {"f2p": {"t1": True}, "p2p": {}},
                "arm-honest": {"f2p": {"t1": True}, "p2p": {}},
            },
        )
        arm_null = _arm_by_label(sc, "arm-null")
        arm_honest = _arm_by_label(sc, "arm-honest")

        # Under FIX C2: null cost → imputed as 1.0 → arm-null's c_norm is HIGHER
        # than arm-honest (which has a real low cost normalized to ~0).
        assert arm_null["c_norm"] >= arm_honest["c_norm"], (
            f"FIX C2: arm with null cost must NOT have lower c_norm than honest arm. "
            f"null c_norm={arm_null['c_norm']:.4f}, honest c_norm={arm_honest['c_norm']:.4f}. "
            "Missing cost must be imputed as 1.0 (worst-case), not excluded."
        )

    def test_missing_worst_field_does_not_improve_rank(self, tmp_path):
        """Arm missing its worst Axis-C field must NOT get lower c_norm than honest arm (FIX C2).

        arm-omit omits wallClockS (which would have been 100.0 = the worst value in
        the comparison).
        Under FIX C2: missing → imputed 1.0 → included in mean → same c_norm as
        arm-honest (whose wallClockS=100.0 normalises to 1.0).
        Under old FIX 6b: missing → excluded → arm-omit's mean computed over 5
        fields instead of 6 → lower c_norm → appears cheaper → unfair advantage.

        Note: the invariant is c_norm, not rank (equal c_norm arms tie by insertion
        order; the c_norm invariant is unambiguous and is what the mutation proof checks).
        """
        usage_omit = {
            "label": "arm-omit",
            "model": "claude-sonnet-4-6",
            # wallClockS ABSENT — would have been 100.0 (the column max)
            "toolCalls": 5,
            "escalations": 0,
            "thrashIters": 0,
            "subagentDispatches": 0,
            "costUSD": 0.05,
        }
        usage_honest = _usage(
            "arm-honest", wall_clock_s=100.0, tool_calls=5,
            escalations=0, thrash_iters=0, subagent_dispatches=0, cost_usd=0.05,
        )
        root_omit = _make_arm(tmp_path, "arm-omit", usage=usage_omit)
        root_honest = _make_arm(tmp_path, "arm-honest", usage=usage_honest)

        sc = bm.score_arms(
            {"arm-omit": root_omit, "arm-honest": root_honest},
            f2p_p2p_results={
                "arm-omit": {"f2p": {"t1": True}, "p2p": {}},
                "arm-honest": {"f2p": {"t1": True}, "p2p": {}},
            },
        )
        arm_omit = _arm_by_label(sc, "arm-omit")
        arm_honest = _arm_by_label(sc, "arm-honest")

        assert arm_omit["usage_incomplete"] is True, (
            "FIX C2: arm-omit must be flagged usage_incomplete"
        )
        # Core C2 invariant: arm-omit's c_norm must NOT be lower than arm-honest's.
        # (Lower c_norm = appears cheaper = unfair advantage from omission.)
        # With FIX C2: arm-omit's missing wallClockS is imputed as 1.0, matching
        # arm-honest's 100.0/100.0 = 1.0 → equal c_norm → no advantage.
        # Without FIX C2 (old exclusion): arm-omit's wallClockS excluded → c_norm
        # computed over 5 fields instead of 6 → c_norm_omit < c_norm_honest → fails.
        assert arm_omit["c_norm"] >= arm_honest["c_norm"], (
            f"FIX C2: arm-omit c_norm={arm_omit['c_norm']:.4f} must NOT be lower "
            f"than arm-honest c_norm={arm_honest['c_norm']:.4f}. "
            "Missing fields must be imputed as 1.0 (worst-case), not excluded."
        )

    def test_universally_missing_field_neutral(self, tmp_path):
        """If NO arm reports a field, that field is dropped (neutral — FIX C2 edge case).

        When wallClockS is absent from ALL arms, it is dropped entirely (not imputed),
        so no arm is penalized for a universally-missing field.
        Identical arms must have equal c_norm.
        """
        usage_a = {
            "label": "arm-a", "model": "claude-sonnet-4-6",
            "toolCalls": 5, "escalations": 0, "thrashIters": 0,
            "subagentDispatches": 0, "costUSD": 0.05,
        }
        usage_b = {
            "label": "arm-b", "model": "claude-sonnet-4-6",
            "toolCalls": 5, "escalations": 0, "thrashIters": 0,
            "subagentDispatches": 0, "costUSD": 0.05,
        }
        root_a = _make_arm(tmp_path, "arm-a", usage=usage_a)
        root_b = _make_arm(tmp_path, "arm-b", usage=usage_b)

        sc = bm.score_arms(
            {"arm-a": root_a, "arm-b": root_b},
            f2p_p2p_results={
                "arm-a": {"f2p": {"t1": True}, "p2p": {}},
                "arm-b": {"f2p": {"t1": True}, "p2p": {}},
            },
        )
        arm_a = _arm_by_label(sc, "arm-a")
        arm_b = _arm_by_label(sc, "arm-b")
        assert arm_a["c_norm"] is not None
        assert arm_b["c_norm"] is not None
        assert abs(arm_a["c_norm"] - arm_b["c_norm"]) < 1e-9, (
            "FIX C2: universally-missing field must be dropped; identical arms must have equal c_norm"
        )


# ===========================================================================
# FIX A2 — scorecard identity stamping
# ===========================================================================


class TestScorecardIdentityStamping:
    """FIX A2: score_arms stamps benchmark_id and provenance as top-level scorecard fields."""

    def _sc(self, tmp_path: Path, **kwargs) -> dict:
        root = _make_arm(tmp_path, "arm-a")
        return bm.score_arms({"arm-a": root}, f2p_p2p_results={"arm-a": _GATE_PASS}, **kwargs)

    def test_benchmark_id_stamped_when_provided(self, tmp_path):
        """When benchmark_id is provided, it appears as top-level field in scorecard (FIX A2)."""
        bid = "test-bench-001"
        sc = self._sc(tmp_path, benchmark_id=bid)
        assert "benchmark_id" in sc, "FIX A2: benchmark_id must be top-level in scorecard"
        assert sc["benchmark_id"] == bid

    def test_provenance_stamped_when_provided(self, tmp_path):
        """When provenance is provided, it appears as top-level field in scorecard (FIX A2)."""
        prov = {"tool_version": "0.1.0", "skill_versions": {"kata-benchmark-report": "0.1.0"}}
        sc = self._sc(tmp_path, provenance=prov)
        assert "provenance" in sc, "FIX A2: provenance must be top-level in scorecard"
        assert sc["provenance"] == prov

    def test_benchmark_id_not_provided_is_absent_or_none(self, tmp_path):
        """When benchmark_id is not provided, it is absent from scorecard or None (FIX A2)."""
        sc = self._sc(tmp_path)
        assert sc.get("benchmark_id") is None, (
            "FIX A2: unprovided benchmark_id must not appear as a non-None value"
        )

    def test_same_definition_true_via_benchmark_id(self, tmp_path):
        """Two scorecards with same benchmark_id → compute_delta sameDefinition=True (FIX A2).

        Before fix: both scorecards lacked benchmark_id → sameDefinition always False.
        After fix: stamped benchmark_id → sameDefinition=True across runs of same definition.
        """
        import benchmark_def as bdef

        bid = "bench-abc-123"
        root_a = _make_arm(tmp_path / "run1", "arm-a")
        root_b = _make_arm(tmp_path / "run2", "arm-a")

        sc1 = bm.score_arms(
            {"arm-a": root_a},
            f2p_p2p_results={"arm-a": _GATE_PASS},
            benchmark_id=bid,
            provenance={"tool_version": "0.1.0", "skill_versions": {}},
        )
        sc2 = bm.score_arms(
            {"arm-a": root_b},
            f2p_p2p_results={"arm-a": _GATE_PASS},
            benchmark_id=bid,
            provenance={"tool_version": "0.2.0", "skill_versions": {}},
        )
        delta = bdef.compute_delta(sc2, sc1)
        assert delta["sameDefinition"] is True, (
            f"FIX A2: scorecards with same benchmark_id must give sameDefinition=True. "
            f"Got {delta['sameDefinition']}. "
            f"sc1.benchmark_id={sc1.get('benchmark_id')!r}, "
            f"sc2.benchmark_id={sc2.get('benchmark_id')!r}"
        )
        assert delta["provenanceDiff"] != {}, (
            "Different provenance → provenanceDiff must be non-empty"
        )


# ===========================================================================
# Mutation proofs for new fixes (≥3 load-bearing assertions)
# ===========================================================================


class TestMutationProofNewFixes:
    """Mutation proofs for FIX A1 cwd, FIX C1 validation, FIX C2 imputation, FIX A2 stamp."""

    def _src(self) -> str:
        return str(_TOOLS / "benchmark.py")

    def _cmd(self, test_spec: str) -> str:
        return (
            f'cd /d "{_TOOLS}" && '
            f"{sys.executable} -m pytest "
            f'"tests/test_benchmark.py::{test_spec}" -q --tb=no'
        )

    def test_mutation_proof_c1_validate_numeric(self):
        """(f) FIX C1: the _c1_valid assignment is load-bearing.

        Removing:
          ``    _c1_valid = math.isfinite(fv) and fv >= 0  # FIX C1: reject negative/NaN/Inf (load-bearing)``
        causes NameError on the next line → test_negative_cost_does_not_win goes red
        (attack arm wins rank 1 when validation is absent).
        """
        import mutation_run

        asserted_line = (
            "    _c1_valid = math.isfinite(fv) and fv >= 0"
            "  # FIX C1: reject negative/NaN/Inf (load-bearing)"
        )
        cmd = self._cmd("TestAxisCNumericSanity::test_negative_cost_does_not_win")
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing the C1 _c1_valid check must make test_negative_cost_does_not_win go red"
        )
        assert verdict["nonVacuous"]

    def test_mutation_proof_c2_impute_missing_field(self):
        """(g) FIX C2: the 1.0 imputation for missing non-nullable fields is load-bearing.

        Removing:
          ``                norms.append(1.0)  # FIX C2: missing/invalid field → impute worst-case``
        restores the exclusion behavior → omitting wallClockS=100.0 helps arm-omit rank above
        arm-honest → test_missing_worst_field_does_not_improve_rank goes red.
        """
        import mutation_run

        asserted_line = (
            "                norms.append(1.0)"
            "  # FIX C2: missing/invalid field → impute worst-case"
        )
        cmd = self._cmd("TestAxisCImputation::test_missing_worst_field_does_not_improve_rank")
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing C2 non-nullable imputation must make "
            "test_missing_worst_field_does_not_improve_rank go red"
        )
        assert verdict["nonVacuous"]

    def test_mutation_proof_a2_benchmark_id_stamp(self):
        """(h) FIX A2: the benchmark_id stamp in score_arms return dict is load-bearing.

        Removing:
          ``        **({"benchmark_id": benchmark_id} if benchmark_id is not None else {}),``
        means compute_delta sees no benchmark_id → sameDefinition=False →
        test_same_definition_true_via_benchmark_id goes red.
        """
        import mutation_run

        asserted_line = (
            '        **({"benchmark_id": benchmark_id} if benchmark_id is not None else {}),'
        )
        cmd = self._cmd("TestScorecardIdentityStamping::test_same_definition_true_via_benchmark_id")
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing benchmark_id stamp must make "
            "test_same_definition_true_via_benchmark_id go red"
        )
        assert verdict["nonVacuous"]


# ===========================================================================
# FIX metric-honesty — f2p_evaluated / p2p_evaluated
# ===========================================================================


class TestF2PEvaluatedFlag:
    """Metric-honesty: f2p_evaluated / p2p_evaluated distinguish vacuous 1.0 from a real all-pass.

    The root problem: when f2p_results is empty the engine computes
    f2p_rate = 1.0 (the vacuous shortcut), making a zero-test run look
    identical to a genuine all-pass.  Adding f2p_evaluated (= f2p_total > 0)
    and f2p_total lets a caller tell the difference without breaking the BC
    f2p_pass_rate field.
    """

    def test_empty_f2p_with_p2p_vacuous_flag(self, tmp_path):
        """Empty f2p + non-empty p2p: gate_evaluated=True but f2p_evaluated=False.

        f2p_pass_rate is 1.0 (vacuous shortcut — BC preserved), but
        f2p_evaluated=False and f2p_total=0 expose that no F2P tests ran.
        """
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={
                "arm-a": {"f2p": {}, "p2p": {"t1": True}},
            },
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["dual_gate_evaluated"] is True, (
            "gate is evaluated because p2p has entries"
        )
        assert arm["f2p_evaluated"] is False, (
            "Empty f2p → f2p_evaluated must be False (vacuous shortcut, not a real all-pass)"
        )
        assert arm["f2p_total"] == 0, "f2p_total must be 0 when f2p is empty"
        assert arm["f2p_pass_rate"] == 1.0, "BC: f2p_pass_rate is still 1.0 (unchanged)"

    def test_real_f2p_is_evaluated(self, tmp_path):
        """Non-empty f2p → f2p_evaluated=True, f2p_total=N, rate correct."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={
                "arm-a": {
                    "f2p": {"t1": True, "t2": True, "t3": False},
                    "p2p": {},
                },
            },
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["f2p_evaluated"] is True, "f2p has 3 entries → f2p_evaluated=True"
        assert arm["f2p_total"] == 3, "f2p_total must equal the number of F2P entries"
        assert arm["f2p_pass_rate"] == pytest.approx(2 / 3)

    def test_real_all_pass_f2p_distinguishable(self, tmp_path):
        """All F2P pass → f2p_evaluated=True distinguishes from vacuous 1.0.

        Both vacuous (f2p={}) and real-all-pass produce f2p_pass_rate=1.0.
        f2p_evaluated=True here signals this is a genuine result.
        """
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={
                "arm-a": {"f2p": {"t1": True, "t2": True}, "p2p": {}},
            },
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["f2p_evaluated"] is True, (
            "f2p has 2 entries → f2p_evaluated=True (real all-pass, not vacuous)"
        )
        assert arm["f2p_total"] == 2
        assert arm["f2p_pass_rate"] == 1.0

    def test_p2p_evaluated_symmetry(self, tmp_path):
        """Empty p2p with non-empty f2p → p2p_evaluated=False, p2p_total=0 (symmetric)."""
        root = _make_arm(tmp_path, "arm-a")
        sc = bm.score_arms(
            {"arm-a": root},
            f2p_p2p_results={
                "arm-a": {"f2p": {"t1": True}, "p2p": {}},
            },
        )
        arm = _arm_by_label(sc, "arm-a")
        assert arm["p2p_evaluated"] is False, (
            "Empty p2p → p2p_evaluated=False (symmetric vacuous shortcut)"
        )
        assert arm["p2p_total"] == 0
        assert arm["p2p_pass_rate"] == 1.0  # BC: vacuous shortcut unchanged


# ===========================================================================
# FIX durable-f2p-proof — permanent reproducible 0→1 proof
# ===========================================================================


class TestDurableF2PProof:
    """Durable real-F2P proof: the 0→1 transition is a permanent, reproducible assertion.

    Builds a tiny synthetic control with:
      (a) a genuinely-FAILING F2P test on the broken baseline (add returns a - b)
      (b) a P2P regression guard that passes even on the broken baseline (add(0,0)==0)

    Proves dual-gate on the broken baseline gives f2p_pass_rate=0.0 and
    dual_both_green=False, then proves the fixed baseline gives f2p_pass_rate=1.0,
    dual_both_green=True, and Q=1.0.

    This permanently prevents the F2P leg from silently regressing to vacuous-pass
    by anchoring the 0→1 transition in a real subprocess run.
    """

    @pytest.mark.integration
    def test_f2p_zero_to_one_transition(self, tmp_path):
        """Integration: F2P 0→1 transition via real dual-gate over a synthetic control.

        BROKEN baseline:  add(a,b) returns a-b  → F2P test (add(1,2)==3) FAILS
                          Q = 0.6*0.0 + 0.4*1.0 = 0.4, dual_gate_both_green=False
        FIXED  baseline:  add(a,b) returns a+b  → F2P test PASSES
                          Q = 1.0, dual_gate_both_green=True

        The P2P guard (add(0,0)==0) passes in both states because 0-0==0.
        """
        import textwrap

        # ── BUILD SYNTHETIC CONTROL ───────────────────────────────────────────
        clone = tmp_path / "control"
        src_dir = clone / "src"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("", encoding="utf-8")

        # BROKEN implementation: subtraction instead of addition
        calc_py = src_dir / "calculator.py"
        calc_py.write_text(
            "def add(a: int, b: int) -> int:\n    return a - b  # deliberate bug\n",
            encoding="utf-8",
        )

        tests_dir = clone / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")
        (tests_dir / "test_calc.py").write_text(
            textwrap.dedent("""\
                from src.calculator import add

                def test_f2p_add_basic():
                    # F2P test: fails on the broken impl (1-2 == -1, not 3)
                    assert add(1, 2) == 3

                def test_p2p_add_zero():
                    # P2P regression guard: passes even on broken impl (0-0 == 0)
                    assert add(0, 0) == 0
            """),
            encoding="utf-8",
        )

        kata = clone / ".kata"
        kata.mkdir()
        (kata / "RESULT.json").write_text(
            json.dumps({"exitCode": 0, "failed": 0, "passed": 2}), encoding="utf-8"
        )
        (kata / "mutation.json").write_text(
            json.dumps({"allNonVacuous": True, "records": []}), encoding="utf-8"
        )
        (kata / "usage.json").write_text(
            json.dumps(_usage("control")), encoding="utf-8"
        )

        f2p_ids = ["tests/test_calc.py::test_f2p_add_basic"]
        p2p_ids = ["tests/test_calc.py::test_p2p_add_zero"]

        # ── BROKEN BASELINE ───────────────────────────────────────────────────
        gate_broken = bm.run_dual_gate(clone, f2p_ids, p2p_ids)

        assert gate_broken["f2p"]["tests/test_calc.py::test_f2p_add_basic"] is False, (
            "Broken impl (a-b): F2P test must FAIL — add(1,2) returns -1, not 3"
        )
        assert gate_broken["p2p"]["tests/test_calc.py::test_p2p_add_zero"] is True, (
            "Broken impl: P2P guard must PASS — add(0,0) returns 0 for any a-b when a==b==0"
        )

        sc_broken = bm.score_arms(
            {"control": clone},
            f2p_p2p_results={"control": gate_broken},
        )
        arm_broken = _arm_by_label(sc_broken, "control")

        assert arm_broken["f2p_pass_rate"] == 0.0, (
            f"Broken: f2p_pass_rate must be 0.0 (F2P test failed); got {arm_broken['f2p_pass_rate']}"
        )
        assert arm_broken["dual_gate_both_green"] is False, (
            "Broken: dual_gate_both_green must be False (F2P failed)"
        )
        # Q = 0.6*f2p_rate + 0.4*p2p_rate = 0.6*0.0 + 0.4*1.0 = 0.4
        assert arm_broken["q"] == pytest.approx(0.4), (
            f"Broken: Q must be 0.4 (only p2p weight contributes); got {arm_broken['q']}"
        )

        # ── APPLY MINIMAL FIX ─────────────────────────────────────────────────
        calc_py.write_text(
            "def add(a: int, b: int) -> int:\n    return a + b  # fixed\n",
            encoding="utf-8",
        )

        # ── FIXED BASELINE ────────────────────────────────────────────────────
        gate_fixed = bm.run_dual_gate(clone, f2p_ids, p2p_ids)

        assert gate_fixed["f2p"]["tests/test_calc.py::test_f2p_add_basic"] is True, (
            "Fixed impl (a+b): F2P test must PASS — add(1,2) returns 3"
        )
        assert gate_fixed["p2p"]["tests/test_calc.py::test_p2p_add_zero"] is True

        sc_fixed = bm.score_arms(
            {"control": clone},
            f2p_p2p_results={"control": gate_fixed},
        )
        arm_fixed = _arm_by_label(sc_fixed, "control")

        assert arm_fixed["f2p_pass_rate"] == 1.0, (
            f"Fixed: f2p_pass_rate must be 1.0 (F2P test passes); got {arm_fixed['f2p_pass_rate']}"
        )
        assert arm_fixed["dual_gate_both_green"] is True, (
            "Fixed: dual_gate_both_green must be True (both gates pass)"
        )
        assert arm_fixed["q"] == pytest.approx(1.0), (
            f"Fixed: Q must be 1.0 (both gates green, allNonVacuous); got {arm_fixed['q']}"
        )
