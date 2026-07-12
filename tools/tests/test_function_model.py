"""test_function_model.py — TDD suite for tools/function_model.py (Slice S2).

Strategy: default-FAIL (tests written before implementation; green only after
function_model.py is present and correct).  No external I/O except the
mutation-proof tests which spawn a subprocess via prove_non_vacuous.

Coverage map
------------
Round-trip:        test_emit_load_round_trip, test_emit_load_identity
Schema:            test_function_model_schema_has_required_keys
Validate — happy:  test_validate_valid_fm_returns_no_errors
Validate — sad:    test_validate_missing_field_*,
                   test_validate_confidence_out_of_range_*,
                   test_validate_bad_derivation_source,
                   test_validate_non_list_preconditions,
                   test_validate_non_list_postconditions,
                   test_validate_assertion_fails_ast_allowlist
_safe_eval happy:  test_safe_eval_simple_comparison,
                   test_safe_eval_arithmetic,
                   test_safe_eval_bool_ops,
                   test_safe_eval_builtin_call
_safe_eval reject: test_safe_eval_raises_on_dunder_escape,
                   test_safe_eval_raises_on_import_call,
                   test_safe_eval_raises_on_attribute_access,
                   test_safe_eval_raises_on_open_call,
                   test_safe_eval_raises_on_unknown_name
evaluate_spec:     test_evaluate_spec_ok_true_on_matching_behavior,
                   test_evaluate_spec_false_on_violated_precondition,
                   test_evaluate_spec_false_on_violated_postcondition,
                   test_evaluate_spec_records_error_on_bad_assertion
Mutation proofs:   test_mutation_proof_violation_guard,
                   test_mutation_proof_ast_allowlist_reject
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _valid_fm() -> dict:
    """Return a minimal schema-valid function_model dict."""
    return {
        "module": "tools/footprint.py",
        "intent_summary": "Add two integers and return their sum.",
        "preconditions": ["isinstance(a, int)", "isinstance(b, int)"],
        "postconditions": ["result == a + b"],
        "behavioral_examples": [{"inputs": {"a": 1, "b": 2}, "expected": 3}],
        "derivation_sources": ["graph", "types"],
        "confidence": 0.85,
    }


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class TestSchema:
    def test_function_model_schema_has_required_keys(self):
        import function_model as fm
        schema = fm.function_model_schema()
        assert isinstance(schema, dict)
        required = schema.get("required", [])
        for field in (
            "module", "intent_summary", "preconditions", "postconditions",
            "behavioral_examples", "derivation_sources", "confidence",
        ):
            assert field in required, f"Schema missing required field: {field!r}"

    def test_schema_allowed_derivation_sources(self):
        import function_model as fm
        schema = fm.function_model_schema()
        props = schema["properties"]
        src_enum = props["derivation_sources"]["items"]["enum"]
        expected = {"graph", "docs", "types", "commit-history", "callers", "contract-inference"}
        assert set(src_enum) == expected


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_emit_load_round_trip(self, tmp_path):
        """emit_function_model + load_function_model are inverses (identity)."""
        import function_model as fm
        data = _valid_fm()
        dest = tmp_path / "fm.json"
        fm.emit_function_model(data, dest)
        loaded = fm.load_function_model(dest)
        assert loaded == data

    def test_emit_creates_valid_json(self, tmp_path):
        """Emitted file is valid JSON."""
        import function_model as fm
        dest = tmp_path / "fm.json"
        fm.emit_function_model(_valid_fm(), dest)
        text = dest.read_text(encoding="utf-8")
        parsed = json.loads(text)
        assert parsed["module"] == "tools/footprint.py"

    def test_emit_creates_parent_dirs(self, tmp_path):
        """emit_function_model creates intermediate directories."""
        import function_model as fm
        dest = tmp_path / "deep" / "nested" / "fm.json"
        fm.emit_function_model(_valid_fm(), dest)
        assert dest.exists()

    def test_load_identity(self, tmp_path):
        """Loaded data is byte-for-byte structurally equal to what was emitted."""
        import function_model as fm
        data = _valid_fm()
        dest = tmp_path / "fm.json"
        fm.emit_function_model(data, dest)
        assert fm.load_function_model(dest) == data


# ---------------------------------------------------------------------------
# validate_function_model — happy path
# ---------------------------------------------------------------------------

class TestValidateHappy:
    def test_validate_valid_fm_returns_no_errors(self):
        import function_model as fm
        errors = fm.validate_function_model(_valid_fm())
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_validate_zero_confidence_valid(self):
        import function_model as fm
        data = _valid_fm()
        data["confidence"] = 0.0
        assert fm.validate_function_model(data) == []

    def test_validate_one_confidence_valid(self):
        import function_model as fm
        data = _valid_fm()
        data["confidence"] = 1.0
        assert fm.validate_function_model(data) == []

    def test_validate_all_derivation_sources(self):
        import function_model as fm
        data = _valid_fm()
        data["derivation_sources"] = [
            "graph", "docs", "types", "commit-history", "callers", "contract-inference"
        ]
        assert fm.validate_function_model(data) == []


# ---------------------------------------------------------------------------
# validate_function_model — missing fields
# ---------------------------------------------------------------------------

class TestValidateMissingFields:
    @pytest.mark.parametrize("field", [
        "module",
        "intent_summary",
        "preconditions",
        "postconditions",
        "behavioral_examples",
        "derivation_sources",
        "confidence",
    ])
    def test_validate_missing_field(self, field):
        import function_model as fm
        data = _valid_fm()
        del data[field]
        errors = fm.validate_function_model(data)
        assert errors, f"Expected error for missing {field!r}, got none"
        assert any(field in e for e in errors), (
            f"Error message does not mention {field!r}: {errors}"
        )


# ---------------------------------------------------------------------------
# validate_function_model — confidence
# ---------------------------------------------------------------------------

class TestValidateConfidence:
    @pytest.mark.parametrize("bad_conf", [-0.001, 1.001, -1.0, 2.0, float("inf")])
    def test_validate_confidence_out_of_range(self, bad_conf):
        import function_model as fm
        data = _valid_fm()
        data["confidence"] = bad_conf
        errors = fm.validate_function_model(data)
        assert errors, f"Expected error for confidence={bad_conf}, got none"
        assert any("confidence" in e for e in errors)

    def test_validate_confidence_non_numeric(self):
        import function_model as fm
        data = _valid_fm()
        data["confidence"] = "high"
        errors = fm.validate_function_model(data)
        assert errors
        assert any("confidence" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_function_model — derivation_sources
# ---------------------------------------------------------------------------

class TestValidateDerivationSources:
    @pytest.mark.parametrize("bad_source", [
        "unknown",
        "llm",
        "heuristic",
        "magic",
    ])
    def test_validate_bad_derivation_source(self, bad_source):
        import function_model as fm
        data = _valid_fm()
        data["derivation_sources"] = [bad_source]
        errors = fm.validate_function_model(data)
        assert errors, f"Expected error for derivation_source {bad_source!r}"
        assert any("derivation_sources" in e for e in errors)

    def test_validate_non_list_derivation_sources(self):
        import function_model as fm
        data = _valid_fm()
        data["derivation_sources"] = "graph"  # string instead of list
        errors = fm.validate_function_model(data)
        assert errors
        assert any("derivation_sources" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_function_model — assertion fields (type + AST)
# ---------------------------------------------------------------------------

class TestValidateAssertionFields:
    def test_validate_non_list_preconditions(self):
        import function_model as fm
        data = _valid_fm()
        data["preconditions"] = "isinstance(a, int)"  # string, not list
        errors = fm.validate_function_model(data)
        assert errors
        assert any("preconditions" in e for e in errors)

    def test_validate_non_list_postconditions(self):
        import function_model as fm
        data = _valid_fm()
        data["postconditions"] = "result > 0"  # string, not list
        errors = fm.validate_function_model(data)
        assert errors
        assert any("postconditions" in e for e in errors)

    def test_validate_assertion_fails_ast_allowlist_attribute(self):
        """Assertion with Attribute access must be rejected at validate time."""
        import function_model as fm
        data = _valid_fm()
        data["preconditions"] = ["a.__class__.__bases__"]
        errors = fm.validate_function_model(data)
        assert errors, "Expected AST-allowlist error for Attribute access, got none"
        assert any("AST allowlist" in e or "preconditions" in e for e in errors)

    def test_validate_assertion_fails_ast_allowlist_import(self):
        """Assertion using __import__ must be rejected."""
        import function_model as fm
        data = _valid_fm()
        data["postconditions"] = ["__import__('os')"]
        errors = fm.validate_function_model(data)
        assert errors, "Expected AST-allowlist error for __import__ call"
        assert any("postconditions" in e for e in errors)

    def test_validate_assertion_fails_ast_allowlist_lambda(self):
        """Assertion using lambda must be rejected."""
        import function_model as fm
        data = _valid_fm()
        data["preconditions"] = ["(lambda x: x)(a)"]
        errors = fm.validate_function_model(data)
        assert errors, "Expected AST-allowlist error for lambda"

    def test_validate_assertion_fails_ast_allowlist_comprehension(self):
        """Assertion using list comprehension must be rejected."""
        import function_model as fm
        data = _valid_fm()
        data["preconditions"] = ["[x for x in a]"]
        errors = fm.validate_function_model(data)
        assert errors, "Expected AST-allowlist error for comprehension"


# ---------------------------------------------------------------------------
# _safe_eval — happy path
# ---------------------------------------------------------------------------

class TestSafeEvalHappy:
    def test_safe_eval_simple_comparison_true(self):
        import function_model as fm
        assert fm._safe_eval("a == 1", {"a": 1}) is True

    def test_safe_eval_simple_comparison_false(self):
        import function_model as fm
        assert fm._safe_eval("a == 1", {"a": 2}) is False

    def test_safe_eval_arithmetic(self):
        import function_model as fm
        # result == a + b
        assert fm._safe_eval("result == a + b", {"a": 3, "b": 4, "result": 7}) is True
        assert fm._safe_eval("result == a + b", {"a": 3, "b": 4, "result": 8}) is False

    def test_safe_eval_bool_ops_and(self):
        import function_model as fm
        assert fm._safe_eval("a > 0 and b > 0", {"a": 1, "b": 2}) is True
        assert fm._safe_eval("a > 0 and b > 0", {"a": -1, "b": 2}) is False

    def test_safe_eval_bool_ops_or(self):
        import function_model as fm
        assert fm._safe_eval("a > 0 or b > 0", {"a": -1, "b": 2}) is True
        assert fm._safe_eval("a > 0 or b > 0", {"a": -1, "b": -1}) is False

    def test_safe_eval_not(self):
        import function_model as fm
        assert fm._safe_eval("not a", {"a": False}) is True
        assert fm._safe_eval("not a", {"a": True}) is False

    def test_safe_eval_builtin_len(self):
        import function_model as fm
        assert fm._safe_eval("len(items) > 0", {"items": [1, 2, 3]}) is True
        assert fm._safe_eval("len(items) > 0", {"items": []}) is False

    def test_safe_eval_builtin_min_max(self):
        import function_model as fm
        assert fm._safe_eval("result == min(a, b)", {"a": 3, "b": 5, "result": 3}) is True

    def test_safe_eval_constant(self):
        import function_model as fm
        assert fm._safe_eval("True", {}) is True
        assert fm._safe_eval("False", {}) is False

    def test_safe_eval_chained_comparison(self):
        import function_model as fm
        assert fm._safe_eval("0 <= confidence <= 1", {"confidence": 0.5}) is True
        assert fm._safe_eval("0 <= confidence <= 1", {"confidence": 1.5}) is False

    def test_safe_eval_in_operator(self):
        import function_model as fm
        assert fm._safe_eval("result in items", {"result": 2, "items": [1, 2, 3]}) is True
        assert fm._safe_eval("result in items", {"result": 9, "items": [1, 2, 3]}) is False

    def test_safe_eval_list_literal(self):
        import function_model as fm
        assert fm._safe_eval("result in [1, 2, 3]", {"result": 2}) is True

    def test_safe_eval_subscript(self):
        import function_model as fm
        assert fm._safe_eval("items[0] == 1", {"items": [1, 2, 3]}) is True


# ---------------------------------------------------------------------------
# _safe_eval — security rejections (MUST raise ValueError)
# ---------------------------------------------------------------------------

class TestSafeEvalRejects:
    def test_safe_eval_raises_on_dunder_escape(self):
        """().__class__.__bases__ is a known sandbox escape — must raise ValueError."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("().__class__.__bases__", {})

    def test_safe_eval_raises_on_import_call(self):
        """__import__('os') must raise ValueError — not in safe-symbol table."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("__import__('os')", {})

    def test_safe_eval_raises_on_attribute_access(self):
        """obj.attr must raise ValueError — Attribute nodes are rejected."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("obj.attr", {"obj": object()})

    def test_safe_eval_raises_on_open_call(self):
        """open('x') must raise ValueError — open not in safe-symbol table."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("open('x')", {})

    def test_safe_eval_raises_on_unknown_name(self):
        """A Name not in names or safe-table must raise ValueError."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("nonexistent_var", {})

    def test_safe_eval_raises_on_lambda(self):
        """Lambda in assertion must raise ValueError."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("(lambda x: x)(a)", {"a": 1})

    def test_safe_eval_raises_on_comprehension(self):
        """List comprehension in assertion must raise ValueError."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("[x for x in items]", {"items": [1, 2]})

    def test_safe_eval_raises_on_walrus(self):
        """Walrus operator in assertion must raise ValueError."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("(x := 1) == 1", {})

    def test_safe_eval_raises_on_nested_attribute(self):
        """Nested attribute chain must raise ValueError."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("os.path.join", {})

    def test_safe_eval_raises_on_exec_call(self):
        """exec not in safe-symbol table — must raise ValueError."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("exec('import os')", {})


class TestSafeEvalResourceGuards:
    """D98 finding: the evaluator must not hang/OOM on a structurally-valid but
    resource-exhausting assertion (range iteration, huge Pow, oversized AST)."""

    def test_range_removed_from_safe_table(self):
        """`range` is the unbounded-iteration footgun — must NOT be callable."""
        import function_model as fm
        assert "range" not in fm._SAFE_SYMBOLS
        with pytest.raises(ValueError):
            fm._safe_eval("sum(range(99999)) > 0", {})

    def test_pow_rejected_entirely(self):
        """`**` is removed entirely — even a small Pow raises (boolean assertions
        never need exponentiation; this kills the chained-Pow explosion vector)."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("2 ** 3 == 8", {})

    def test_chained_pow_rejected(self):
        """D98 re-confirm: chained Pow (14 nodes, each exponent ≤ cap) must NOT
        hang — it is rejected outright via the no-`**` rule, fast."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("(((10**1000)**1000)**1000) > 0", {})

    def test_huge_lshift_rejected(self):
        """A huge `<<` shift (the remaining integer-build vector) is capped."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("(1 << 100000) > 0", {})

    def test_oversized_assertion_rejected(self):
        """An assertion exceeding the AST node cap must raise."""
        import function_model as fm
        big = " + ".join(["1"] * 500) + " > 0"
        with pytest.raises(ValueError):
            fm._safe_eval(big, {})

    def test_dict_unpacking_rejected(self):
        """`{**d}` (None key) must raise — it would otherwise eval to {None: d}."""
        import function_model as fm
        with pytest.raises(ValueError):
            fm._safe_eval("{**d} == {}", {"d": {}})

    def test_bounded_sum_over_literal_still_works(self):
        """The fix must not break legitimate bounded aggregation over a literal."""
        import function_model as fm
        assert fm._safe_eval("sum([1, 2, 3]) == 6", {}) is True


# ---------------------------------------------------------------------------
# evaluate_spec
# ---------------------------------------------------------------------------

class TestEvaluateSpec:
    def _add_fm(self) -> dict:
        """A function_model for ``result == a + b`` (integer addition)."""
        return {
            "module": "tools/math_utils.py",
            "intent_summary": "Add two integers.",
            "preconditions": ["isinstance(a, int)", "isinstance(b, int)"],
            "postconditions": ["result == a + b"],
            "behavioral_examples": [],
            "derivation_sources": ["types"],
            "confidence": 0.9,
        }

    def test_evaluate_spec_ok_true_on_matching_behavior(self):
        """evaluate_spec returns ok:True when all pre/post hold."""
        import function_model as fm
        result = fm.evaluate_spec(
            self._add_fm(),
            {"inputs": {"a": 3, "b": 4}, "result": 7},
        )
        assert result["ok"] is True
        assert result["violations"] == []

    def test_evaluate_spec_false_on_violated_precondition(self):
        """evaluate_spec returns ok:False when a precondition fails."""
        import function_model as fm
        # Pass a float for 'a' — violates isinstance(a, int)
        result = fm.evaluate_spec(
            self._add_fm(),
            {"inputs": {"a": 3.5, "b": 4}, "result": 7.5},
        )
        assert result["ok"] is False
        assert any("isinstance(a, int)" in v for v in result["violations"]), (
            f"Expected 'isinstance(a, int)' in violations; got {result['violations']}"
        )

    def test_evaluate_spec_false_on_violated_postcondition(self):
        """evaluate_spec returns ok:False when a postcondition fails (injected deviation)."""
        import function_model as fm
        # Correct inputs but wrong result (e.g. off-by-one bug)
        result = fm.evaluate_spec(
            self._add_fm(),
            {"inputs": {"a": 3, "b": 4}, "result": 8},  # should be 7
        )
        assert result["ok"] is False
        assert any("result == a + b" in v for v in result["violations"]), (
            f"Expected 'result == a + b' in violations; got {result['violations']}"
        )

    def test_evaluate_spec_records_error_on_bad_assertion(self):
        """An assertion that raises during evaluation is recorded, not propagated."""
        import function_model as fm
        bad_fm = {
            **self._add_fm(),
            "postconditions": ["result == a + b", "nonexistent_var"],
        }
        result = fm.evaluate_spec(
            bad_fm,
            {"inputs": {"a": 3, "b": 4}, "result": 7},
        )
        assert result["ok"] is False
        assert any("nonexistent_var" in v for v in result["violations"]), (
            f"Expected error-annotated violation for bad assertion; got {result['violations']}"
        )

    def test_evaluate_spec_multiple_violations(self):
        """All failing assertions are collected, not just the first."""
        import function_model as fm
        strict_fm = {
            **self._add_fm(),
            "postconditions": ["result == a + b", "result > 100"],
        }
        # result=8 → both postconditions fail: 8 != 7 AND 8 <= 100
        result = fm.evaluate_spec(
            strict_fm,
            {"inputs": {"a": 3, "b": 4}, "result": 8},
        )
        assert result["ok"] is False
        assert len(result["violations"]) >= 2

    def test_evaluate_spec_empty_assertions(self):
        """FM with no pre/postconditions always passes."""
        import function_model as fm
        empty_fm = {
            **self._add_fm(),
            "preconditions": [],
            "postconditions": [],
        }
        result = fm.evaluate_spec(empty_fm, {"inputs": {"a": 1}, "result": 1})
        assert result["ok"] is True
        assert result["violations"] == []


# ---------------------------------------------------------------------------
# Mutation proofs (non-vacuous — prove load-bearing lines actually bite)
# ---------------------------------------------------------------------------

class TestMutationProof:
    """Mutation proofs via mutation_run.prove_non_vacuous.

    Each test removes one load-bearing line from function_model.py, runs a
    targeted pytest command, and asserts the test went red.  The file is
    restored unconditionally by prove_non_vacuous (try/finally).
    """

    def _fm_source(self) -> str:
        return str(_TOOLS / "function_model.py")

    def _test_cmd(self, test_name: str) -> str:
        return (
            f'cd "{_TOOLS}" && '
            f'{sys.executable} -m pytest '
            f'"tests/test_function_model.py::{test_name}" -q'
        )

    def test_mutation_proof_violation_guard(self):
        """Prove the violation-detection guard in evaluate_spec bites.

        Target line: ``                violations.append(pre)``
        (the append in the 'if not ok_pre:' branch of evaluate_spec).

        Without this line, a failing precondition is silently ignored and
        evaluate_spec returns ok:True → test_evaluate_spec_false_on_violated_precondition
        goes red.
        """
        import mutation_run

        source = self._fm_source()
        asserted_line = "                violations.append(pre)"
        test_cmd = self._test_cmd(
            "TestEvaluateSpec::test_evaluate_spec_false_on_violated_precondition"
        )
        verdict = mutation_run.prove_non_vacuous(source, asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make the precondition-violation test go red — "
            "violations.append(pre) guard is not biting"
        )
        assert verdict["nonVacuous"], (
            "Test must be non-vacuous: it must catch removal of violations.append(pre)"
        )

    def test_mutation_proof_ast_allowlist_reject(self):
        """Prove the AST-allowlist Attribute-reject branch in _walk_verify bites.

        Target line: ``        raise ValueError("Attribute access rejected in assertion")``
        (the raise in the isinstance(node, ast.Attribute) branch of _walk_verify).

        Without this raise, Attribute access is not caught by _walk_verify, so
        test_safe_eval_raises_on_attribute_access goes red.
        """
        import mutation_run

        source = self._fm_source()
        asserted_line = '        raise ValueError("Attribute access rejected in assertion")'
        test_cmd = self._test_cmd(
            "TestSafeEvalRejects::test_safe_eval_raises_on_attribute_access"
        )
        verdict = mutation_run.prove_non_vacuous(source, asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make the attribute-access test go red — "
            "AST Attribute reject branch is not biting"
        )
        assert verdict["nonVacuous"], (
            "Test must be non-vacuous: it must catch removal of the Attribute raise"
        )


# ---------------------------------------------------------------------------
# D98 validate/evaluate hardening (schema drift + robustness)
# ---------------------------------------------------------------------------

class TestValidateD98Fixes:
    def _valid(self) -> dict:
        return {
            "module": "m", "intent_summary": "s",
            "preconditions": [], "postconditions": [],
            "behavioral_examples": [], "derivation_sources": ["graph"],
            "confidence": 0.5,
        }

    def test_confidence_bool_rejected(self):
        """confidence: True must be rejected (isinstance(True, int) is True)."""
        import function_model as fm
        bad = self._valid(); bad["confidence"] = True
        assert any("confidence" in e for e in fm.validate_function_model(bad))

    def test_extra_keys_rejected(self):
        """additionalProperties: False — an unexpected key is a validation error."""
        import function_model as fm
        bad = self._valid(); bad["junk"] = 1
        assert any("Unexpected field" in e for e in fm.validate_function_model(bad))

    def test_valid_fm_still_passes(self):
        import function_model as fm
        assert fm.validate_function_model(self._valid()) == []


class TestEvaluateSpecMalformedCall:
    def _add_fm(self) -> dict:
        return {
            "module": "add", "intent_summary": "result == a + b",
            "preconditions": [], "postconditions": ["result == a + b"],
            "behavioral_examples": [], "derivation_sources": ["graph"],
            "confidence": 0.9,
        }

    def test_missing_keys_returns_structured_not_keyerror(self):
        """A malformed call record must return ok:False, not raise KeyError."""
        import function_model as fm
        out = fm.evaluate_spec(self._add_fm(), {})  # no inputs/result
        assert out["ok"] is False and out["violations"]

    def test_non_dict_inputs_returns_structured(self):
        import function_model as fm
        out = fm.evaluate_spec(self._add_fm(), {"inputs": "nope", "result": 1})
        assert out["ok"] is False


# --------------------------------------------------------------------------- #
# F1 (2026-07-12 health review): sequence-repetition DoS guard in _safe_eval
# --------------------------------------------------------------------------- #
class TestSequenceRepetitionGuard:
    """`[0]*N` / `"a"*N` allocate memory proportional to N (not node count) --
    the same DoS class as `**`/`<<`. _safe_eval must reject a large seq*int
    repeat rather than execute it. Mutation-proof: deleting the Mult cap in
    _eval_node lets these allocate and the raise-assertions go RED."""

    def _fm(self, postcondition: str) -> dict:
        return {
            "module": "tools/x.py",
            "intent_summary": "seq-repeat probe",
            "preconditions": [],
            "postconditions": [postcondition],
            "behavioral_examples": [],
            "derivation_sources": ["types"],
            "confidence": 0.5,
        }

    def test_list_repetition_over_cap_recorded_as_violation(self):
        import function_model as fm
        res = fm.evaluate_spec(self._fm("len([0] * 9999999999) >= 0"), {"inputs": {}, "result": 0})
        # The cap raises during eval; evaluate_spec records it, never allocates 10^10.
        assert res["ok"] is False
        assert any("resource-exhaustion" in v or "Sequence repetition" in v
                   for v in res["violations"]), res["violations"]

    def test_str_repetition_over_cap_recorded_as_violation(self):
        import function_model as fm
        res = fm.evaluate_spec(self._fm('len("a" * 9999999999) >= 0'), {"inputs": {}, "result": 0})
        assert res["ok"] is False
        assert any("resource-exhaustion" in v or "Sequence repetition" in v
                   for v in res["violations"]), res["violations"]

    def test_small_repetition_still_allowed(self):
        import function_model as fm
        res = fm.evaluate_spec(self._fm("len([0] * 3) == 3"), {"inputs": {}, "result": 0})
        assert res["ok"] is True, res

    def test_chained_repetition_over_cap_rejected(self):
        """adval DEFECT-1: `[0]*1000*1000` keeps every COUNT under the cap while the
        product explodes. The guard must bound the RESULT length, not the count —
        this is RED against the count-only guard (which never fired on the chain)."""
        import function_model as fm
        res = fm.evaluate_spec(
            self._fm("len([0] * 1000 * 1000) >= 0"), {"inputs": {}, "result": 0}
        )
        assert res["ok"] is False
        assert any("resource-exhaustion" in v or "Sequence repetition" in v
                   for v in res["violations"]), res["violations"]

    def test_chained_str_repetition_over_cap_rejected(self):
        """The same chained bypass via str repetition is rejected."""
        import function_model as fm
        res = fm.evaluate_spec(
            self._fm('len("a" * 1000 * 1000) >= 0'), {"inputs": {}, "result": 0}
        )
        assert res["ok"] is False
