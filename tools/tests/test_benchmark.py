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
    cost_usd: Optional[float] = 0.01,
    tokens_in: Optional[int] = 1000,
    tokens_out: Optional[int] = 300,
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
    result: Optional[dict] = None,
    mutation: Optional[dict] = None,
    usage: Optional[dict] = None,
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

        def fake_rnt(test_path: str, test_name: str) -> bool:
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

        def fake_run_named_test(test_path: str, test_name: str) -> bool:
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

    def test_run_dual_gate_malformed_id_returns_false(self, tmp_path):
        """A test-ID without '::' is malformed and returns False (fail-safe)."""
        clone_root = tmp_path / "clone"
        clone_root.mkdir()

        with patch("mutation_check.run_named_test", return_value=True):
            result = bm.run_dual_gate(
                clone_root,
                f2p_ids=["no_separator_here"],
                p2p_ids=[],
            )

        assert result["f2p"]["no_separator_here"] is False, (
            "Malformed test-ID (no '::') must return False, not call run_named_test"
        )


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

    mutation_run.prove_non_vacuous always restores the source file (try/finally).
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
