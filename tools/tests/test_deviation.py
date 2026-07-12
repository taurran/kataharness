"""test_deviation.py — TDD suite for tools/deviation.py (Slice D1, Phase P2a).

Strategy: default-FAIL (tests written before implementation; green only after
deviation.py is present and correct).  Mutation proof tests use
mutation_run.prove_non_vacuous and spawn a real subprocess (no runner injection).
All other tests are pure (no I/O except fixture loads and tmp_path writes).

Coverage map
------------
tally_self_consistency:
    test_passes_with_2_of_3
    test_fails_with_1_of_3
    test_empty_votes_passes_false
    test_agree_count_correct
    test_total_count_correct
    test_custom_k_min_accepts_all
    test_custom_k_min_rejects_partial

self_consistency_entropy:
    test_perfect_consensus_entropy_zero (all True)
    test_perfect_dissent_entropy_zero (all False)
    test_max_disagreement_entropy_one (50/50)
    test_majority_agreement_entropy_below_one
    test_empty_votes_entropy_zero

corroboration_gate:
    test_corroborated_with_co_located
    test_not_corroborated_llm_only
    test_route_none_when_corroborated
    test_route_human_when_not_corroborated
    test_wrong_module_not_co_located
    test_wrong_locus_not_co_located
    test_multiple_corroborators_one_matches
    test_co_located_list_populated

compute_confidence:
    test_exact_numeric_default_weights
    test_clamped_above_one
    test_clamped_below_zero
    test_weight_override_changes_score
    test_full_signal_high_confidence

apply_force_low:
    test_sparse_caps_confidence_to_low_cap
    test_non_sparse_unchanged
    test_sparse_already_below_cap_unchanged
    test_sparse_custom_cap

route_finding:
    test_high_confidence_auto_fix_eligible
    test_low_confidence_defer
    test_mid_confidence_research
    test_exactly_tau_high_auto_fix_eligible
    test_exactly_tau_low_defer
    test_threshold_override_rerouts

run_funnel (end-to-end):
    test_true_positive_fixture_routes_auto_fix_eligible
    test_false_positive_fixture_routes_human
    test_sc_failure_routes_defer
    test_refuted_routes_human
    test_funnel_stop_sc_failure
    test_funnel_stop_corroboration
    test_funnel_stop_refuted
    test_funnel_stop_none_on_completion
    test_sparse_signal_caps_route

findings_schema:
    test_schema_has_required_keys
    test_schema_route_enum

emit_findings / load_findings:
    test_emit_load_round_trip_empty
    test_emit_load_round_trip_one_finding
    test_emit_creates_parent_dirs

exec-safety:
    test_no_eval_in_deviation_py
    test_no_exec_in_deviation_py
    test_no_subprocess_in_deviation_py
    test_no_shell_call_in_deviation_py

Mutation proofs (spawn real subprocess via prove_non_vacuous):
    TestMutationProof::test_mutation_proof_corroboration_gate_co_location
    TestMutationProof::test_mutation_proof_routing_threshold_boundary
    TestMutationProof::test_mutation_proof_k_min_boundary
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parent.parent
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "deviation"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _load_fixture(name: str) -> dict:
    """Load a seeded fixture dict from the deviation fixtures directory."""
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# tally_self_consistency
# ---------------------------------------------------------------------------

class TestTallySelfConsistency:
    def test_passes_with_2_of_3(self):
        """2/3 agreement satisfies default k_min=2 → passes:True."""
        import deviation as dev
        result = dev.tally_self_consistency([True, True, False])
        assert result["passes"] is True

    def test_fails_with_1_of_3(self):
        """1/3 agreement does NOT satisfy default k_min=2 → passes:False."""
        import deviation as dev
        result = dev.tally_self_consistency([True, False, False])
        assert result["passes"] is False

    def test_empty_votes_passes_false(self):
        """Empty vote list → fail-closed → passes:False."""
        import deviation as dev
        result = dev.tally_self_consistency([])
        assert result["passes"] is False

    def test_agree_count_correct(self):
        """agree field must count True values correctly."""
        import deviation as dev
        result = dev.tally_self_consistency([True, False, True, True])
        assert result["agree"] == 3

    def test_total_count_correct(self):
        """total field must equal len(votes)."""
        import deviation as dev
        result = dev.tally_self_consistency([True, False, True])
        assert result["total"] == 3

    def test_custom_k_min_accepts_all(self):
        """k_min=3 with 3/3 → passes:True."""
        import deviation as dev
        result = dev.tally_self_consistency([True, True, True], k_min=3)
        assert result["passes"] is True

    def test_custom_k_min_rejects_partial(self):
        """k_min=3 with 2/3 → passes:False."""
        import deviation as dev
        result = dev.tally_self_consistency([True, True, False], k_min=3)
        assert result["passes"] is False

    def test_all_false_passes_false(self):
        """All False → agree=0 → passes:False regardless of k_min."""
        import deviation as dev
        result = dev.tally_self_consistency([False, False, False])
        assert result["passes"] is False
        assert result["agree"] == 0

    def test_all_true_passes_true(self):
        """All True → agree=3 ≥ k_min=2 → passes:True."""
        import deviation as dev
        result = dev.tally_self_consistency([True, True, True])
        assert result["passes"] is True
        assert result["agree"] == 3


# ---------------------------------------------------------------------------
# self_consistency_entropy
# ---------------------------------------------------------------------------

class TestSelfConsistencyEntropy:
    def test_perfect_consensus_all_true_entropy_zero(self):
        """All agree (p=1) → entropy = 0.0."""
        import deviation as dev
        assert dev.self_consistency_entropy([True, True, True]) == pytest.approx(0.0)

    def test_perfect_dissent_all_false_entropy_zero(self):
        """All disagree (p=0) → entropy = 0.0."""
        import deviation as dev
        assert dev.self_consistency_entropy([False, False, False]) == pytest.approx(0.0)

    def test_max_disagreement_50_50_entropy_one(self):
        """50/50 split → max binary entropy = 1.0."""
        import deviation as dev
        assert dev.self_consistency_entropy([True, False]) == pytest.approx(1.0)

    def test_majority_agreement_entropy_below_one(self):
        """2/3 agreement → H(2/3) ≈ 0.918, i.e. in (0, 1)."""
        import deviation as dev
        h = dev.self_consistency_entropy([True, True, False])
        assert 0.0 < h < 1.0

    def test_empty_votes_entropy_zero(self):
        """Empty list → 0.0 (fail-safe)."""
        import deviation as dev
        assert dev.self_consistency_entropy([]) == pytest.approx(0.0)

    def test_entropy_in_unit_interval(self):
        """Entropy is always in [0, 1] for any vote list."""
        import deviation as dev
        for votes in [[], [True], [False], [True, False], [True, True, False]]:
            h = dev.self_consistency_entropy(votes)
            assert 0.0 <= h <= 1.0, f"entropy={h} out of [0,1] for votes={votes}"


# ---------------------------------------------------------------------------
# corroboration_gate
# ---------------------------------------------------------------------------

class TestCorroborationGate:
    def _finding(self) -> dict:
        return {"module": "tools/example.py", "locus": "add_numbers"}

    def _corroborator(self, module: str = "tools/example.py", locus: str = "add_numbers") -> dict:
        return {"module": module, "locus": locus, "source": "test", "signal": "FAIL"}

    def test_corroborated_with_co_located(self):
        """≥1 co-located corroborator → corroborated:True."""
        import deviation as dev
        result = dev.corroboration_gate(self._finding(), [self._corroborator()])
        assert result["corroborated"] is True

    def test_not_corroborated_llm_only(self):
        """Zero corroborators (LLM-only) → corroborated:False."""
        import deviation as dev
        result = dev.corroboration_gate(self._finding(), [])
        assert result["corroborated"] is False

    def test_route_none_when_corroborated(self):
        """Corroborated finding → route:None (downstream routing decides)."""
        import deviation as dev
        result = dev.corroboration_gate(self._finding(), [self._corroborator()])
        assert result["route"] is None

    def test_route_human_when_not_corroborated(self):
        """LLM-only finding → route:'human' (NEVER auto-fix-eligible)."""
        import deviation as dev
        result = dev.corroboration_gate(self._finding(), [])
        assert result["route"] == "human"

    def test_wrong_module_not_co_located(self):
        """Corroborator on a different module → NOT co-located → LLM-only."""
        import deviation as dev
        other = self._corroborator(module="tools/other.py")
        result = dev.corroboration_gate(self._finding(), [other])
        assert result["corroborated"] is False
        assert result["route"] == "human"

    def test_wrong_locus_not_co_located(self):
        """Corroborator at a different locus → NOT co-located → LLM-only."""
        import deviation as dev
        other = self._corroborator(locus="subtract_numbers")
        result = dev.corroboration_gate(self._finding(), [other])
        assert result["corroborated"] is False
        assert result["route"] == "human"

    def test_multiple_corroborators_one_matches(self):
        """Multiple corroborators; one matches → corroborated:True."""
        import deviation as dev
        corroborators = [
            self._corroborator(module="tools/other.py"),
            self._corroborator(),   # matches
            self._corroborator(locus="subtract"),
        ]
        result = dev.corroboration_gate(self._finding(), corroborators)
        assert result["corroborated"] is True

    def test_co_located_list_populated(self):
        """co_located list contains exactly the matching corroborators."""
        import deviation as dev
        match = self._corroborator()
        non_match = self._corroborator(locus="other")
        result = dev.corroboration_gate(self._finding(), [non_match, match])
        assert len(result["co_located"]) == 1
        assert result["co_located"][0] is match


# ---------------------------------------------------------------------------
# compute_confidence
# ---------------------------------------------------------------------------

class TestComputeConfidence:
    def test_exact_numeric_default_weights(self):
        """Exact numeric check against the default-weights formula."""
        import deviation as dev
        # msas=0.8, sc_entropy=0.0 (perfect consensus), structural_prior=0.6
        # C = 0.40*0.8 + 0.35*(1-0.0) + 0.25*0.6 = 0.32 + 0.35 + 0.15 = 0.82
        result = dev.compute_confidence(0.8, 0.0, 0.6)
        assert result == pytest.approx(0.82, abs=1e-9)

    def test_clamped_above_one(self):
        """Formula > 1 is clamped to 1.0."""
        import deviation as dev
        result = dev.compute_confidence(1.0, 0.0, 1.0)
        assert result == pytest.approx(1.0)

    def test_clamped_below_zero(self):
        """Negative formula result (unusual weights) is clamped to 0.0."""
        import deviation as dev
        # Force a negative result with custom weights
        result = dev.compute_confidence(
            0.0, 1.0, 0.0,
            weights={"w1": 0.0, "w2": -1.0, "w3": 0.0},
        )
        assert result == pytest.approx(0.0)

    def test_weight_override_changes_score_deterministically(self):
        """Custom weights produce a deterministically different score from defaults."""
        import deviation as dev
        default_score = dev.compute_confidence(0.5, 0.3, 0.5)
        custom_score = dev.compute_confidence(
            0.5, 0.3, 0.5,
            weights={"w1": 0.10, "w2": 0.80, "w3": 0.10},
        )
        assert default_score != pytest.approx(custom_score)

    def test_full_signal_maximum_confidence(self):
        """msas=1, entropy=0, prior=1 → C = w1+w2+w3 (clamped to 1 with default weights)."""
        import deviation as dev
        result = dev.compute_confidence(1.0, 0.0, 1.0)
        expected = min(1.0, dev.DEFAULT_WEIGHTS["w1"] + dev.DEFAULT_WEIGHTS["w2"] + dev.DEFAULT_WEIGHTS["w3"])
        assert result == pytest.approx(expected)

    def test_zero_signal_minimum_confidence(self):
        """msas=0, entropy=1, prior=0 → C = 0 (w2*(1-1) contributes 0)."""
        import deviation as dev
        result = dev.compute_confidence(0.0, 1.0, 0.0)
        assert result == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# apply_force_low
# ---------------------------------------------------------------------------

class TestApplyForceLow:
    def test_sparse_caps_confidence_to_low_cap(self):
        """Sparse module: confidence > low_cap is capped to low_cap."""
        import deviation as dev
        capped = dev.apply_force_low(0.9, sparse_signal=True)
        assert capped == pytest.approx(dev.DEFAULT_THRESHOLDS["low_cap"])

    def test_non_sparse_unchanged(self):
        """Non-sparse module: confidence is returned unchanged."""
        import deviation as dev
        assert dev.apply_force_low(0.9, sparse_signal=False) == pytest.approx(0.9)

    def test_sparse_already_below_cap_unchanged(self):
        """Sparse module but confidence already ≤ low_cap → no change."""
        import deviation as dev
        low = dev.DEFAULT_THRESHOLDS["low_cap"] - 0.01
        result = dev.apply_force_low(low, sparse_signal=True)
        assert result == pytest.approx(low)

    def test_sparse_custom_cap(self):
        """Custom low_cap overrides the default."""
        import deviation as dev
        result = dev.apply_force_low(0.8, sparse_signal=True, low_cap=0.2)
        assert result == pytest.approx(0.2)

    def test_non_sparse_custom_cap_ignored(self):
        """Custom low_cap is irrelevant when sparse_signal=False."""
        import deviation as dev
        result = dev.apply_force_low(0.8, sparse_signal=False, low_cap=0.1)
        assert result == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# route_finding
# ---------------------------------------------------------------------------

class TestRouteFinding:
    def test_high_confidence_auto_fix_eligible(self):
        """Confidence ≥ tau_high → 'auto-fix-eligible'."""
        import deviation as dev
        tau_high = dev.DEFAULT_THRESHOLDS["tau_high"]
        assert dev.route_finding(tau_high + 0.05) == "auto-fix-eligible"

    def test_low_confidence_defer(self):
        """Confidence ≤ tau_low → 'defer'."""
        import deviation as dev
        tau_low = dev.DEFAULT_THRESHOLDS["tau_low"]
        assert dev.route_finding(tau_low - 0.05) == "defer"

    def test_mid_confidence_research(self):
        """tau_low < confidence < tau_high → 'research'."""
        import deviation as dev
        tau_high = dev.DEFAULT_THRESHOLDS["tau_high"]
        tau_low = dev.DEFAULT_THRESHOLDS["tau_low"]
        mid = (tau_high + tau_low) / 2
        assert dev.route_finding(mid) == "research"

    def test_exactly_tau_high_auto_fix_eligible(self):
        """Exactly at tau_high boundary → 'auto-fix-eligible' (inclusive)."""
        import deviation as dev
        tau_high = dev.DEFAULT_THRESHOLDS["tau_high"]
        assert dev.route_finding(tau_high) == "auto-fix-eligible"

    def test_exactly_tau_low_defer(self):
        """Exactly at tau_low boundary → 'defer' (inclusive)."""
        import deviation as dev
        tau_low = dev.DEFAULT_THRESHOLDS["tau_low"]
        assert dev.route_finding(tau_low) == "defer"

    def test_threshold_override_rerouts_deterministically(self):
        """Custom thresholds re-route the same confidence deterministically."""
        import deviation as dev
        # With a very high tau_high, a normally auto-fix-eligible score → research
        custom = {**dev.DEFAULT_THRESHOLDS, "tau_high": 0.999}
        result = dev.route_finding(0.9, thresholds=custom)
        assert result == "research"

    def test_all_three_bands_covered(self):
        """Each of the three bands is reachable with default thresholds."""
        import deviation as dev
        tau_high = dev.DEFAULT_THRESHOLDS["tau_high"]
        tau_low = dev.DEFAULT_THRESHOLDS["tau_low"]
        mid = (tau_high + tau_low) / 2
        assert dev.route_finding(1.0) == "auto-fix-eligible"
        assert dev.route_finding(mid) == "research"
        assert dev.route_finding(0.0) == "defer"


# ---------------------------------------------------------------------------
# run_funnel — end-to-end composition
# ---------------------------------------------------------------------------

class TestRunFunnel:
    def test_true_positive_fixture_routes_auto_fix_eligible(self):
        """True-positive fixture: ≥1 corroborator + ≥2/3 SC + not refuted → auto-fix-eligible."""
        import deviation as dev
        finding = _load_fixture("true_positive.json")
        result = dev.run_funnel(finding)
        assert result["route"] == "auto-fix-eligible", (
            f"True-positive fixture must reach auto-fix-eligible, got {result['route']!r}. "
            f"Full verdict: {result}"
        )
        assert result["funnel_stop"] is None

    def test_false_positive_fixture_routes_human(self):
        """False-positive (LLM-only, no corroborator) → filtered at corroboration gate → 'human'."""
        import deviation as dev
        finding = _load_fixture("false_positive.json")
        result = dev.run_funnel(finding)
        assert result["route"] == "human", (
            f"False-positive (LLM-only) must be filtered to 'human' at corroboration gate, "
            f"got {result['route']!r}. Full verdict: {result}"
        )
        assert result["funnel_stop"] == "corroboration_gate"

    def test_false_positive_never_auto_fix_eligible(self):
        """Extra guard: false-positive must NEVER reach auto-fix-eligible."""
        import deviation as dev
        finding = _load_fixture("false_positive.json")
        result = dev.run_funnel(finding)
        assert result["route"] != "auto-fix-eligible", (
            "HARD gate violation: LLM-only false-positive reached auto-fix-eligible"
        )

    def test_sc_failure_routes_defer(self):
        """Self-consistency failure (1/3) → funnel stops early → 'defer'."""
        import deviation as dev
        finding = {
            "module": "tools/example.py",
            "locus": "add",
            "votes": [True, False, False],
            "corroborators": [{"module": "tools/example.py", "locus": "add", "source": "test"}],
            "refuted": False,
            "msas": 0.8,
            "structural_prior": 0.8,
            "sparse_signal": False,
        }
        result = dev.run_funnel(finding)
        assert result["route"] == "defer"
        assert result["funnel_stop"] == "self_consistency"

    def test_refuted_routes_human(self):
        """Refuted finding (contested) → 'human'."""
        import deviation as dev
        finding = {
            "module": "tools/example.py",
            "locus": "add",
            "votes": [True, True, True],
            "corroborators": [{"module": "tools/example.py", "locus": "add", "source": "test"}],
            "refuted": True,
            "msas": 0.9,
            "structural_prior": 0.8,
            "sparse_signal": False,
        }
        result = dev.run_funnel(finding)
        assert result["route"] == "human"
        assert result["funnel_stop"] == "refuted"

    def test_funnel_stop_none_on_completion(self):
        """A finding that completes the full funnel has funnel_stop=None."""
        import deviation as dev
        finding = _load_fixture("true_positive.json")
        result = dev.run_funnel(finding)
        assert result["funnel_stop"] is None

    def test_sparse_signal_caps_route(self):
        """Sparse-signal module is capped via force-LOW; cannot route auto-fix-eligible."""
        import deviation as dev
        low_cap = dev.DEFAULT_THRESHOLDS["low_cap"]
        tau_high = dev.DEFAULT_THRESHOLDS["tau_high"]
        assert low_cap < tau_high, "Fixture invariant: low_cap must be below tau_high"
        finding = {
            "module": "tools/example.py",
            "locus": "add",
            "votes": [True, True, True],
            "corroborators": [{"module": "tools/example.py", "locus": "add", "source": "test"}],
            "refuted": False,
            "msas": 1.0,
            "structural_prior": 1.0,
            "sparse_signal": True,   # force-LOW applies
        }
        result = dev.run_funnel(finding)
        assert result["route"] != "auto-fix-eligible", (
            "Sparse-signal module must not reach auto-fix-eligible via force-LOW"
        )
        assert result["confidence"] is not None
        assert result["confidence"] <= low_cap

    def test_result_has_all_required_keys(self):
        """run_funnel result always contains all schema-required keys."""
        import deviation as dev
        finding = _load_fixture("true_positive.json")
        result = dev.run_funnel(finding)
        for key in ("module", "locus", "sc_tally", "corroboration", "refuted",
                    "confidence", "sparse_signal", "route", "funnel_stop"):
            assert key in result, f"Missing key {key!r} in funnel result"


# ---------------------------------------------------------------------------
# findings_schema
# ---------------------------------------------------------------------------

class TestFindingsSchema:
    def test_schema_has_required_keys(self):
        """findings_schema() returns a dict with the schema-required keys."""
        import deviation as dev
        schema = dev.findings_schema()
        assert isinstance(schema, dict)
        assert "required" in schema
        for key in ("module", "locus", "sc_tally", "route"):
            assert key in schema["required"], f"Key {key!r} missing from schema required"

    def test_schema_route_enum(self):
        """findings_schema() route property includes all four routing values."""
        import deviation as dev
        schema = dev.findings_schema()
        route_enum = schema["properties"]["route"]["enum"]
        for expected in ("auto-fix-eligible", "research", "defer", "human"):
            assert expected in route_enum, f"{expected!r} missing from route enum"

    def test_schema_type_is_object(self):
        """findings_schema type must be 'object'."""
        import deviation as dev
        assert dev.findings_schema()["type"] == "object"


# ---------------------------------------------------------------------------
# emit_findings / load_findings — JSON round-trip
# ---------------------------------------------------------------------------

class TestEmitLoadRoundTrip:
    def test_emit_load_round_trip_empty(self, tmp_path):
        """Empty findings list round-trips without loss."""
        import deviation as dev
        dest = tmp_path / "findings.json"
        dev.emit_findings([], dest)
        loaded = dev.load_findings(dest)
        assert loaded == []

    def test_emit_load_round_trip_one_finding(self, tmp_path):
        """A single routed finding dict round-trips identically."""
        import deviation as dev
        finding = _load_fixture("true_positive.json")
        verdict = dev.run_funnel(finding)
        dest = tmp_path / "findings.json"
        dev.emit_findings([verdict], dest)
        loaded = dev.load_findings(dest)
        assert len(loaded) == 1
        assert loaded[0] == verdict

    def test_emit_load_round_trip_multiple_findings(self, tmp_path):
        """Multiple findings round-trip in order without loss."""
        import deviation as dev
        tp = dev.run_funnel(_load_fixture("true_positive.json"))
        fp = dev.run_funnel(_load_fixture("false_positive.json"))
        dest = tmp_path / "findings.json"
        dev.emit_findings([tp, fp], dest)
        loaded = dev.load_findings(dest)
        assert len(loaded) == 2
        assert loaded[0] == tp
        assert loaded[1] == fp

    def test_emit_creates_parent_dirs(self, tmp_path):
        """emit_findings creates missing parent directories."""
        import deviation as dev
        dest = tmp_path / "kata" / "deviations" / "findings.json"
        assert not dest.parent.exists()
        dev.emit_findings([], dest)
        assert dest.exists()

    def test_schema_valid_after_round_trip(self, tmp_path):
        """A round-tripped finding has all schema-required keys."""
        import deviation as dev
        finding = _load_fixture("true_positive.json")
        verdict = dev.run_funnel(finding)
        dest = tmp_path / "findings.json"
        dev.emit_findings([verdict], dest)
        loaded = dev.load_findings(dest)
        schema = dev.findings_schema()
        for key in schema["required"]:
            assert key in loaded[0], f"Schema-required key {key!r} missing after round-trip"


# ---------------------------------------------------------------------------
# exec-safety: no eval / exec / subprocess / shell in deviation.py
# ---------------------------------------------------------------------------

class TestExecSafety:
    """Source-scan assertions required by PLAN D1 acceptance + DESIGN exec-safety posture."""

    def _source(self) -> str:
        return (_TOOLS / "deviation.py").read_text(encoding="utf-8")

    def test_no_eval_in_deviation_py(self):
        """deviation.py must not contain eval() calls."""
        src = self._source()
        # Exclude the docstring reference (e.g. 'no eval') by checking for callable form
        import re
        hits = [m.group() for m in re.finditer(r'\beval\s*\(', src)]
        assert not hits, f"eval() call found in deviation.py: {hits}"

    def test_no_exec_in_deviation_py(self):
        """deviation.py must not contain exec() calls."""
        src = self._source()
        import re
        hits = [m.group() for m in re.finditer(r'\bexec\s*\(', src)]
        assert not hits, f"exec() call found in deviation.py: {hits}"

    def test_no_subprocess_import_in_deviation_py(self):
        """deviation.py must not import subprocess (no 'import subprocess' statement)."""
        src = self._source()
        import re
        # Match actual import statements, not docstring mentions
        hits = [m.group() for m in re.finditer(r'^\s*(?:import|from)\s+subprocess\b', src, re.MULTILINE)]
        assert not hits, f"subprocess import found in deviation.py: {hits}"

    def test_no_shell_true_in_deviation_py(self):
        """deviation.py must not pass shell=True (belt-and-suspenders)."""
        src = self._source()
        assert "shell=True" not in src, "shell=True found in deviation.py"

    def test_deviation_py_is_pure_ast_parseable(self):
        """deviation.py must be syntactically valid Python (ast.parse passes)."""
        import ast
        src = self._source()
        # Raises SyntaxError if invalid — surfaces immediately
        ast.parse(src)


# ---------------------------------------------------------------------------
# M-1 regression — null module/locus must not spuriously corroborate
# ---------------------------------------------------------------------------

class TestCoLocatesNullSafety:
    """M-1: _co_locates must be fail-closed for null module/locus on either side.

    Before the fix, None == None → True, so a vague LLM-only finding with null
    locus/module could spuriously corroborate and reach auto-fix-eligible.
    After the fix, both sides must be non-null.
    """

    def test_both_null_locus_does_not_corroborate(self):
        """Finding + corroborator both have null locus → fail-closed → not corroborated."""
        import deviation as dev
        finding = {"module": "tools/x.py", "locus": None}
        corroborator = {"module": "tools/x.py", "locus": None, "source": "test"}
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is False
        assert result["route"] == "human"

    def test_both_null_module_does_not_corroborate(self):
        """Finding + corroborator both have null module → fail-closed → not corroborated."""
        import deviation as dev
        finding = {"module": None, "locus": "add_numbers"}
        corroborator = {"module": None, "locus": "add_numbers", "source": "test"}
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is False
        assert result["route"] == "human"

    def test_both_null_module_and_locus_does_not_corroborate(self):
        """Finding + corroborator both fully null → fail-closed → not corroborated."""
        import deviation as dev
        finding = {"module": None, "locus": None}
        corroborator = {"module": None, "locus": None, "source": "test"}
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is False
        assert result["route"] == "human"

    def test_null_locus_finding_real_locus_corroborator_does_not_corroborate(self):
        """Finding with null locus vs corroborator with real locus → not co-located."""
        import deviation as dev
        finding = {"module": "tools/x.py", "locus": None}
        corroborator = {"module": "tools/x.py", "locus": "add", "source": "test"}
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is False

    def test_non_null_both_sides_still_corroborates(self):
        """Positive control: non-null matching module+locus still corroborates."""
        import deviation as dev
        finding = {"module": "tools/x.py", "locus": "add"}
        corroborator = {"module": "tools/x.py", "locus": "add", "source": "test"}
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is True

    def test_both_empty_locus_does_not_corroborate(self):
        """L-3: finding + corroborator both have empty-string locus → fail-closed.

        ``"" == ""`` is True under plain equality; the truthiness guard rejects it.
        """
        import deviation as dev
        finding = {"module": "tools/x.py", "locus": ""}
        corroborator = {"module": "tools/x.py", "locus": "", "source": "test"}
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is False
        assert result["route"] == "human"

    def test_both_empty_module_does_not_corroborate(self):
        """L-3: finding + corroborator both have empty-string module → fail-closed."""
        import deviation as dev
        finding = {"module": "", "locus": "add"}
        corroborator = {"module": "", "locus": "add", "source": "test"}
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is False
        assert result["route"] == "human"

    def test_both_empty_module_and_locus_does_not_corroborate(self):
        """L-3: finding + corroborator both fully empty-string → fail-closed."""
        import deviation as dev
        finding = {"module": "", "locus": ""}
        corroborator = {"module": "", "locus": "", "source": "test"}
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is False
        assert result["route"] == "human"


# ---------------------------------------------------------------------------
# M-2 regression — corroborator objectivity must be enforced in code
# ---------------------------------------------------------------------------

class TestCorroboratorObjectivity:
    """M-2: corroborators without an objective source must be silently ignored.

    Before the fix, the gate relied on kata-deviate discipline: it accepted any
    dict as a corroborator.  After the fix, only sources in _OBJECTIVE_SOURCES
    count; unknown/absent sources are IGNORED (fail-closed).
    """

    def test_llm_restated_source_does_not_corroborate(self):
        """Corroborator source='llm-restated' (non-allowlisted) → not corroborated."""
        import deviation as dev
        finding = {"module": "tools/x.py", "locus": "add"}
        corroborator = {"module": "tools/x.py", "locus": "add", "source": "llm-restated"}
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is False
        assert result["route"] == "human"

    def test_missing_source_does_not_corroborate(self):
        """Corroborator with no 'source' key → fail-closed → not corroborated."""
        import deviation as dev
        finding = {"module": "tools/x.py", "locus": "add"}
        corroborator = {"module": "tools/x.py", "locus": "add"}  # no source key
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is False
        assert result["route"] == "human"

    def test_snyk_objective_source_corroborates(self):
        """Corroborator source='snyk' co-located → corroborated:True."""
        import deviation as dev
        finding = {"module": "tools/x.py", "locus": "add"}
        corroborator = {"module": "tools/x.py", "locus": "add", "source": "snyk"}
        result = dev.corroboration_gate(finding, [corroborator])
        assert result["corroborated"] is True
        assert result["route"] is None

    def test_all_objective_sources_accepted(self):
        """Each source in _OBJECTIVE_SOURCES is accepted when co-located."""
        import deviation as dev
        finding = {"module": "tools/x.py", "locus": "add"}
        for src in sorted(dev._OBJECTIVE_SOURCES):
            corroborator = {"module": "tools/x.py", "locus": "add", "source": src}
            result = dev.corroboration_gate(finding, [corroborator])
            assert result["corroborated"] is True, (
                f"source={src!r} is in _OBJECTIVE_SOURCES but was not accepted"
            )

    def test_unknown_source_among_valid_ignored_individually(self):
        """Two corroborators: one unknown source, one valid source → only the valid one counts."""
        import deviation as dev
        finding = {"module": "tools/x.py", "locus": "add"}
        bad = {"module": "tools/x.py", "locus": "add", "source": "llm-restated"}
        good = {"module": "tools/x.py", "locus": "add", "source": "test"}
        result = dev.corroboration_gate(finding, [bad, good])
        assert result["corroborated"] is True  # good one saves it
        assert len(result["co_located"]) == 1
        assert result["co_located"][0] is good

    def test_only_unknown_sources_routes_human(self):
        """All corroborators have unknown sources → none count → routes human."""
        import deviation as dev
        finding = {"module": "tools/x.py", "locus": "add"}
        corroborators = [
            {"module": "tools/x.py", "locus": "add", "source": "llm-restated"},
            {"module": "tools/x.py", "locus": "add", "source": "llm"},
            {"module": "tools/x.py", "locus": "add"},
        ]
        result = dev.corroboration_gate(finding, corroborators)
        assert result["corroborated"] is False
        assert result["route"] == "human"

    def test_run_funnel_non_objective_corroborator_routes_human(self):
        """run_funnel: finding with only a non-objective corroborator routes human (never auto-fix)."""
        import deviation as dev
        finding = {
            "module": "tools/x.py",
            "locus": "add",
            "votes": [True, True, True],
            "corroborators": [
                {"module": "tools/x.py", "locus": "add", "source": "llm-restated"}
            ],
            "refuted": False,
            "msas": 0.95,
            "structural_prior": 0.95,
            "sparse_signal": False,
        }
        result = dev.run_funnel(finding)
        assert result["route"] == "human"
        assert result["funnel_stop"] == "corroboration_gate"
        assert result["route"] != "auto-fix-eligible"


# ---------------------------------------------------------------------------
# L-1 regression — present-but-null corroborators/votes must not crash
# ---------------------------------------------------------------------------

class TestRunFunnelNullCoerce:
    """L-1: finding.get("corroborators") or [] guards against None (not KeyError).

    Before the fix, a JSON finding with ``corroborators: null`` (Python None)
    would cause a TypeError inside corroboration_gate when iterating.
    """

    def test_null_corroborators_does_not_crash(self):
        """finding with corroborators=null degrades gracefully to route='human'."""
        import deviation as dev
        finding = {
            "module": "tools/x.py",
            "locus": "add",
            "votes": [True, True, True],
            "corroborators": None,          # present-but-null
            "refuted": False,
            "msas": 0.9,
            "structural_prior": 0.8,
            "sparse_signal": False,
        }
        # Must not raise TypeError
        result = dev.run_funnel(finding)
        # null corroborators → treated as [] → no corroboration → human
        assert result["route"] == "human"
        assert result["funnel_stop"] == "corroboration_gate"

    def test_null_votes_does_not_crash(self):
        """finding with votes=null degrades gracefully to route='defer'."""
        import deviation as dev
        finding = {
            "module": "tools/x.py",
            "locus": "add",
            "votes": None,                  # present-but-null
            "corroborators": [{"module": "tools/x.py", "locus": "add", "source": "test"}],
            "refuted": False,
            "msas": 0.9,
            "structural_prior": 0.8,
            "sparse_signal": False,
        }
        # Must not raise TypeError
        result = dev.run_funnel(finding)
        # null votes → [] → tally fails (0 < k_min=2) → defer
        assert result["route"] == "defer"
        assert result["funnel_stop"] == "self_consistency"

    def test_null_both_does_not_crash(self):
        """finding with both votes=null and corroborators=null degrades to 'defer'."""
        import deviation as dev
        finding = {
            "module": "tools/x.py",
            "locus": "add",
            "votes": None,
            "corroborators": None,
            "refuted": False,
            "msas": 0.0,
            "structural_prior": 0.0,
            "sparse_signal": False,
        }
        result = dev.run_funnel(finding)
        # votes=null → [] → SC fails first → defer
        assert result["route"] == "defer"
        assert result["funnel_stop"] == "self_consistency"


# ---------------------------------------------------------------------------
# Q-6 regression — run_funnel hard-requires refuted + sparse_signal (D136)
# ---------------------------------------------------------------------------

class TestRunFunnelRequiredKeys:
    """Q-6: `refuted` and `sparse_signal` are docstring-contract keys.

    Before the fix, ``finding.get("refuted", False)`` and
    ``finding.get("sparse_signal", False)`` defaulted an ABSENT key to the
    PERMISSIVE branch (not-refuted / not-sparse → auto-fix-eligible-eligible).
    After the fix, an absent key hard-fails (D136 — no silent permissive default).
    """

    def _base(self) -> dict:
        return {
            "module": "tools/x.py",
            "locus": "add",
            "votes": [True, True, True],
            "corroborators": [{"module": "tools/x.py", "locus": "add", "source": "test"}],
            "refuted": False,
            "msas": 0.9,
            "structural_prior": 0.8,
            "sparse_signal": False,
        }

    def test_missing_refuted_raises(self):
        """Finding missing 'refuted' ⇒ ValueError (not permissive not-refuted)."""
        import deviation as dev
        finding = self._base()
        del finding["refuted"]
        with pytest.raises(ValueError, match=r"refuted"):
            dev.run_funnel(finding)

    def test_missing_sparse_signal_raises(self):
        """Finding missing 'sparse_signal' ⇒ ValueError (not permissive not-sparse)."""
        import deviation as dev
        finding = self._base()
        del finding["sparse_signal"]
        with pytest.raises(ValueError, match=r"sparse_signal"):
            dev.run_funnel(finding)

    def test_both_present_still_runs(self):
        """Positive control: both keys present ⇒ funnel runs to completion."""
        import deviation as dev
        result = dev.run_funnel(self._base())
        assert result["funnel_stop"] is None
        assert result["route"] == "auto-fix-eligible"


# ---------------------------------------------------------------------------
# Mutation proofs — prove load-bearing lines actually bite
# ---------------------------------------------------------------------------

class TestMutationProof:
    """Mutation non-vacuous proofs via mutation_run.prove_non_vacuous.

    Each test removes one load-bearing line from deviation.py, runs a targeted
    pytest command, and asserts the test went red.  prove_non_vacuous restores
    the file unconditionally (try/finally) — the source is byte-identical after
    each call.

    Three targets per PLAN D1 acceptance:
    (a) corroboration co-location branch
    (b) routing-threshold boundary branch
    (c) k_min ≥2/3 self-consistency boundary
    """

    def _deviation_source(self) -> str:
        return str(_TOOLS / "deviation.py")

    def _test_cmd(self, test_spec: str) -> str:
        """Build a pytest command targeting a specific test in test_deviation.py."""
        return (
            f'cd /d "{_TOOLS}" && '
            f'{sys.executable} -m pytest '
            f'"tests/test_deviation.py::{test_spec}" -q --tb=no'
        )

    def test_mutation_proof_corroboration_gate_co_location(self):
        """(a) Prove the co-location append in corroboration_gate is load-bearing.

        Target line (exact, 12-space indent):
            ``            co_located.append(c)``

        When removed: co_located never accumulates any entries → corroborated is
        always False → test_corroborated_with_co_located expects True but gets False
        → test goes red.
        """
        import mutation_run

        source = self._deviation_source()
        asserted_line = "            co_located.append(c)"
        test_cmd = self._test_cmd(
            "TestCorroborationGate::test_corroborated_with_co_located"
        )
        verdict = mutation_run.prove_non_vacuous(source, asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make the co-location test go red — "
            "co_located.append(c) is not load-bearing (corroboration gate is not biting)"
        )
        assert verdict["nonVacuous"], (
            "Test must be non-vacuous: it must catch removal of co_located.append(c)"
        )

    def test_mutation_proof_routing_threshold_boundary(self):
        """(b) Prove the auto-fix-eligible return in route_finding is load-bearing.

        Target line (exact, 8-space indent):
            ``        return "auto-fix-eligible"``

        When removed: high-confidence findings fall through to the research check
        → route_finding(tau_high) → 'research' instead of 'auto-fix-eligible'
        → test_exactly_tau_high_auto_fix_eligible goes red.
        """
        import mutation_run

        source = self._deviation_source()
        asserted_line = '        return "auto-fix-eligible"'
        test_cmd = self._test_cmd(
            "TestRouteFinding::test_exactly_tau_high_auto_fix_eligible"
        )
        verdict = mutation_run.prove_non_vacuous(source, asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make the routing boundary test go red — "
            'return "auto-fix-eligible" is not load-bearing (routing threshold is not biting)'
        )
        assert verdict["nonVacuous"], (
            'Test must be non-vacuous: it must catch removal of return "auto-fix-eligible"'
        )

    def test_mutation_proof_k_min_boundary(self):
        """(c) Prove the k_min ≥2/3 boundary in tally_self_consistency is load-bearing.

        Target line (exact, 4-space indent):
            ``    passes = agree >= k_min``

        When removed: ``passes`` is undefined → NameError at the return statement
        → test_passes_with_2_of_3 raises an error (goes red).
        """
        import mutation_run

        source = self._deviation_source()
        asserted_line = "    passes = agree >= k_min"
        test_cmd = self._test_cmd(
            "TestTallySelfConsistency::test_passes_with_2_of_3"
        )
        verdict = mutation_run.prove_non_vacuous(source, asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make the k_min boundary test go red — "
            "passes = agree >= k_min is not load-bearing (k_min gate is not biting)"
        )
        assert verdict["nonVacuous"], (
            "Test must be non-vacuous: it must catch removal of passes = agree >= k_min"
        )
