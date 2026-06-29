"""test_usage_meter.py — TDD suite for tools/usage_meter.py (S1, kata-loop-benchmark).

Strategy: default-FAIL (tests written before implementation; green only after
usage_meter.py is present and correct). Pure tests (no I/O except tmp_path
writes) plus mutation-proof tests that spawn a real subprocess via
mutation_run.prove_non_vacuous.

The engine is PURE — no subprocess, no eval/exec. Injectable clock for
wallClockS (elapsed is passed in; no real wall-clock calls in tests).
tokensIn/Out/costUSD are honestly nullable (host-dependent capture).

Coverage map
------------
usage_schema:
    TestSchema::test_required_fields_present
    TestSchema::test_nullable_token_fields_in_schema
    TestSchema::test_wall_clock_and_tool_calls_always_present
    TestSchema::test_schema_description_carries_honesty_note

build_usage:
    TestBuildUsage::test_all_fields_present_in_entry
    TestBuildUsage::test_nullable_tokens_in_allowed
    TestBuildUsage::test_nullable_tokens_out_allowed
    TestBuildUsage::test_nullable_cost_usd_allowed
    TestBuildUsage::test_all_nullable_fields_none_simultaneously
    TestBuildUsage::test_label_and_model_carried
    TestBuildUsage::test_wall_clock_coerced_to_float
    TestBuildUsage::test_tool_calls_present
    TestBuildUsage::test_defaults_for_optional_counters
    TestBuildUsage::test_invalid_label_raises_type_error
    TestBuildUsage::test_invalid_wall_clock_raises_type_error

cost_from_rate_table:
    TestCostFromRateTable::test_basic_cost_computation
    TestCostFromRateTable::test_null_tokens_in_returns_none
    TestCostFromRateTable::test_null_tokens_out_returns_none
    TestCostFromRateTable::test_model_not_in_table_returns_none
    TestCostFromRateTable::test_multi_model_priced_independently

write_usage / load_usage:
    TestWriteLoad::test_write_creates_parent_directories
    TestWriteLoad::test_round_trip_preserves_all_fields
    TestWriteLoad::test_round_trip_nullable_fields_preserved
    TestWriteLoad::test_write_guard_rejects_traversal

exec-safety:
    TestExecSafety::test_no_subprocess_import
    TestExecSafety::test_no_eval
    TestExecSafety::test_no_exec
    TestExecSafety::test_no_shell_true

Mutation proofs (spawn real subprocess via prove_non_vacuous):
    TestMutationProof::test_mutation_guard_raise            (a)
    TestMutationProof::test_mutation_tokens_in_field        (b)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# usage_schema
# ---------------------------------------------------------------------------


class TestSchema:
    def test_required_fields_present(self):
        """The schema required list covers all always-present fields."""
        import usage_meter as um
        schema = um.usage_schema()
        required = schema["required"]
        for field in ("label", "model", "wallClockS", "toolCalls",
                      "escalations", "thrashIters", "subagentDispatches"):
            assert field in required, f"{field!r} missing from schema required"

    def test_nullable_token_fields_in_schema(self):
        """tokensIn, tokensOut, costUSD are defined in properties (nullable)."""
        import usage_meter as um
        props = um.usage_schema()["properties"]
        for field in ("tokensIn", "tokensOut", "costUSD"):
            assert field in props, f"{field!r} missing from schema properties"
            ftype = props[field]["type"]
            # Must allow null — either ["...", "null"] or equivalent
            if isinstance(ftype, list):
                assert "null" in ftype, f"{field!r} must allow null in schema"

    def test_wall_clock_and_tool_calls_always_present(self):
        """wallClockS and toolCalls are required (not nullable) in the schema."""
        import usage_meter as um
        schema = um.usage_schema()
        required = schema["required"]
        assert "wallClockS" in required
        assert "toolCalls" in required
        props = schema["properties"]
        # wallClockS: type is "number" (not a list with null)
        wc_type = props["wallClockS"]["type"]
        assert wc_type == "number" or (isinstance(wc_type, list) and "null" not in wc_type)
        # toolCalls: type is "integer" (not a list with null)
        tc_type = props["toolCalls"]["type"]
        assert tc_type == "integer" or (isinstance(tc_type, list) and "null" not in tc_type)

    def test_schema_description_carries_honesty_note(self):
        """The schema description records the host-dependent / nullable honesty note."""
        import usage_meter as um
        desc = um.usage_schema()["description"].lower()
        assert "null" in desc or "nullable" in desc
        assert "host" in desc


# ---------------------------------------------------------------------------
# build_usage
# ---------------------------------------------------------------------------


class TestBuildUsage:
    def test_all_fields_present_in_entry(self):
        """build_usage returns an entry with every schema field present."""
        import usage_meter as um
        entry = um.build_usage(
            label="baseline",
            model="claude-sonnet-4-6",
            wall_clock_s=12.5,
            tool_calls=7,
            tokens_in=1000,
            tokens_out=300,
            cost_usd=0.0042,
            escalations=1,
            thrash_iters=2,
            subagent_dispatches=0,
        )
        for field in (
            "label", "model", "tokensIn", "tokensOut", "costUSD",
            "wallClockS", "toolCalls", "escalations", "thrashIters",
            "subagentDispatches",
        ):
            assert field in entry, f"{field!r} missing from build_usage output"

    def test_nullable_tokens_in_allowed(self):
        """tokensIn=None is accepted and preserved (host-dependent capture)."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm-a", model="m1", wall_clock_s=5.0, tool_calls=3,
            tokens_in=None,
        )
        assert entry["tokensIn"] is None

    def test_nullable_tokens_out_allowed(self):
        """tokensOut=None is accepted and preserved."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm-a", model="m1", wall_clock_s=5.0, tool_calls=3,
            tokens_out=None,
        )
        assert entry["tokensOut"] is None

    def test_nullable_cost_usd_allowed(self):
        """costUSD=None is accepted and preserved."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm-a", model="m1", wall_clock_s=5.0, tool_calls=3,
            cost_usd=None,
        )
        assert entry["costUSD"] is None

    def test_all_nullable_fields_none_simultaneously(self):
        """All three nullable fields can be None at the same time (no tokens surfaced)."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm-a", model="m1", wall_clock_s=5.0, tool_calls=3,
            tokens_in=None, tokens_out=None, cost_usd=None,
        )
        assert entry["tokensIn"] is None
        assert entry["tokensOut"] is None
        assert entry["costUSD"] is None

    def test_label_and_model_carried(self):
        """label and model are carried through unchanged."""
        import usage_meter as um
        entry = um.build_usage(
            label="my-arm", model="claude-opus-4-5", wall_clock_s=1.0, tool_calls=0,
        )
        assert entry["label"] == "my-arm"
        assert entry["model"] == "claude-opus-4-5"

    def test_wall_clock_coerced_to_float(self):
        """wallClockS is stored as a float (injectable clock: pass elapsed directly)."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm", model="m", wall_clock_s=10, tool_calls=1,
        )
        assert isinstance(entry["wallClockS"], float)
        assert entry["wallClockS"] == 10.0

    def test_tool_calls_present(self):
        """toolCalls is always present and equals the passed value."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm", model="m", wall_clock_s=3.0, tool_calls=42,
        )
        assert entry["toolCalls"] == 42

    def test_defaults_for_optional_counters(self):
        """escalations, thrashIters, subagentDispatches default to 0."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm", model="m", wall_clock_s=1.0, tool_calls=0,
        )
        assert entry["escalations"] == 0
        assert entry["thrashIters"] == 0
        assert entry["subagentDispatches"] == 0

    def test_invalid_label_raises_type_error(self):
        """Passing a non-str label raises TypeError."""
        import usage_meter as um
        import pytest
        with pytest.raises(TypeError):
            um.build_usage(label=123, model="m", wall_clock_s=1.0, tool_calls=0)

    def test_invalid_wall_clock_raises_type_error(self):
        """Passing a non-numeric wall_clock_s raises TypeError."""
        import usage_meter as um
        import pytest
        with pytest.raises(TypeError):
            um.build_usage(label="arm", model="m", wall_clock_s="fast", tool_calls=0)

    # -- D98: non-negativity guard (Axis-C gaming vector) --------------------

    def test_negative_cost_usd_raises_value_error(self):
        """Negative cost_usd is rejected with ValueError (gaming vector guard)."""
        import usage_meter as um
        import pytest
        with pytest.raises(ValueError, match="cost_usd"):
            um.build_usage(
                label="arm", model="m", wall_clock_s=1.0, tool_calls=0,
                cost_usd=-5.0,
            )

    def test_negative_wall_clock_s_raises_value_error(self):
        """Negative wall_clock_s is rejected with ValueError."""
        import usage_meter as um
        import pytest
        with pytest.raises(ValueError, match="wall_clock_s"):
            um.build_usage(
                label="arm", model="m", wall_clock_s=-1.0, tool_calls=0,
            )

    def test_negative_tokens_in_raises_value_error(self):
        """Negative tokens_in is rejected with ValueError."""
        import usage_meter as um
        import pytest
        with pytest.raises(ValueError, match="tokens_in"):
            um.build_usage(
                label="arm", model="m", wall_clock_s=1.0, tool_calls=0,
                tokens_in=-1,
            )

    def test_negative_tool_calls_raises_value_error(self):
        """Negative tool_calls is rejected with ValueError."""
        import usage_meter as um
        import pytest
        with pytest.raises(ValueError, match="tool_calls"):
            um.build_usage(
                label="arm", model="m", wall_clock_s=1.0, tool_calls=-3,
            )

    def test_zero_cost_usd_allowed(self):
        """cost_usd=0 is at the boundary and must NOT raise (zero is valid)."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm", model="m", wall_clock_s=1.0, tool_calls=0,
            cost_usd=0.0,
        )
        assert entry["costUSD"] == 0.0

    def test_zero_wall_clock_s_allowed(self):
        """wall_clock_s=0 is at the boundary and must NOT raise."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm", model="m", wall_clock_s=0.0, tool_calls=0,
        )
        assert entry["wallClockS"] == 0.0

    def test_none_cost_usd_not_rejected_by_negcheck(self):
        """cost_usd=None is still accepted (nullable — not subject to negcheck)."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm", model="m", wall_clock_s=1.0, tool_calls=0,
            cost_usd=None,
        )
        assert entry["costUSD"] is None

    def test_none_tokens_in_not_rejected_by_negcheck(self):
        """tokens_in=None is still accepted (nullable — not subject to negcheck)."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm", model="m", wall_clock_s=1.0, tool_calls=0,
            tokens_in=None,
        )
        assert entry["tokensIn"] is None


# ---------------------------------------------------------------------------
# cost_from_rate_table
# ---------------------------------------------------------------------------


_SAMPLE_RATE_TABLE = {
    "claude-sonnet-4-6": {"input": 3e-6, "output": 15e-6},
    "claude-opus-4-5": {"input": 15e-6, "output": 75e-6},
}


class TestCostFromRateTable:
    def test_basic_cost_computation(self):
        """cost = tokens_in * input_rate + tokens_out * output_rate."""
        import usage_meter as um
        cost = um.cost_from_rate_table(1000, 300, "claude-sonnet-4-6", _SAMPLE_RATE_TABLE)
        expected = 1000 * 3e-6 + 300 * 15e-6
        assert cost is not None
        assert abs(cost - expected) < 1e-10

    def test_null_tokens_in_returns_none(self):
        """tokens_in=None → returns None (host did not surface token count)."""
        import usage_meter as um
        result = um.cost_from_rate_table(None, 300, "claude-sonnet-4-6", _SAMPLE_RATE_TABLE)
        assert result is None

    def test_null_tokens_out_returns_none(self):
        """tokens_out=None → returns None."""
        import usage_meter as um
        result = um.cost_from_rate_table(1000, None, "claude-sonnet-4-6", _SAMPLE_RATE_TABLE)
        assert result is None

    def test_model_not_in_table_returns_none(self):
        """model absent from rate_table → returns None."""
        import usage_meter as um
        result = um.cost_from_rate_table(1000, 300, "unknown-model", _SAMPLE_RATE_TABLE)
        assert result is None

    def test_multi_model_priced_independently(self):
        """Each model is priced from its own rate entry (multi-model arms)."""
        import usage_meter as um
        cost_sonnet = um.cost_from_rate_table(
            1000, 300, "claude-sonnet-4-6", _SAMPLE_RATE_TABLE
        )
        cost_opus = um.cost_from_rate_table(
            1000, 300, "claude-opus-4-5", _SAMPLE_RATE_TABLE
        )
        assert cost_sonnet is not None
        assert cost_opus is not None
        # Opus is more expensive per token — its cost must be strictly higher
        assert cost_opus > cost_sonnet


# ---------------------------------------------------------------------------
# write_usage / load_usage round-trip
# ---------------------------------------------------------------------------


class TestWriteLoad:
    def _full_entry(self):
        import usage_meter as um
        return um.build_usage(
            label="baseline",
            model="claude-sonnet-4-6",
            wall_clock_s=8.3,
            tool_calls=5,
            tokens_in=2000,
            tokens_out=600,
            cost_usd=0.015,
            escalations=0,
            thrash_iters=1,
            subagent_dispatches=2,
        )

    def test_write_creates_parent_directories(self, tmp_path):
        """write_usage creates .kata/ parent dirs if absent."""
        import usage_meter as um
        dest = tmp_path / ".kata" / "usage.json"
        assert not dest.parent.exists()
        um.write_usage(dest, self._full_entry())
        assert dest.exists()

    def test_round_trip_preserves_all_fields(self, tmp_path):
        """write then load_usage returns a dict with every field intact."""
        import usage_meter as um
        entry = self._full_entry()
        dest = tmp_path / ".kata" / "usage.json"
        um.write_usage(dest, entry)
        loaded = um.load_usage(dest)
        for field in entry:
            assert field in loaded, f"{field!r} missing after round-trip"
            assert loaded[field] == entry[field], f"{field!r} mismatch after round-trip"

    def test_round_trip_nullable_fields_preserved(self, tmp_path):
        """write/load preserves None (JSON null) for nullable token fields."""
        import usage_meter as um
        entry = um.build_usage(
            label="arm", model="m", wall_clock_s=1.0, tool_calls=0,
            tokens_in=None, tokens_out=None, cost_usd=None,
        )
        dest = tmp_path / ".kata" / "usage.json"
        um.write_usage(dest, entry)
        loaded = um.load_usage(dest)
        assert loaded["tokensIn"] is None
        assert loaded["tokensOut"] is None
        assert loaded["costUSD"] is None

    def test_write_guard_rejects_traversal(self, tmp_path):
        """write_usage raises ValueError when path contains '..' traversal (CWE-23)."""
        import usage_meter as um
        import pytest
        bad_path = tmp_path / ".." / "evil" / "usage.json"
        with pytest.raises(ValueError, match=r"\.\."):
            um.write_usage(bad_path, self._full_entry())


# ---------------------------------------------------------------------------
# exec-safety: no subprocess, no eval, no exec, no shell=True
# ---------------------------------------------------------------------------


class TestExecSafety:
    """Source-scan assertions: usage_meter.py is pure — no exec sink introduced."""

    def _source(self) -> str:
        return (_TOOLS / "usage_meter.py").read_text(encoding="utf-8")

    def test_no_subprocess_import(self):
        import re
        hits = [
            m.group()
            for m in re.finditer(
                r"^\s*(?:import|from)\s+subprocess\b", self._source(), re.MULTILINE
            )
        ]
        assert not hits, f"subprocess import found in usage_meter.py: {hits}"

    def test_no_eval(self):
        import re
        hits = [m.group() for m in re.finditer(r"\beval\s*\(", self._source())]
        assert not hits, f"eval() call found in usage_meter.py: {hits}"

    def test_no_exec(self):
        import re
        hits = [m.group() for m in re.finditer(r"\bexec\s*\(", self._source())]
        assert not hits, f"exec() call found in usage_meter.py: {hits}"

    def test_no_shell_true(self):
        assert "shell=True" not in self._source(), "shell=True found in usage_meter.py"


# ---------------------------------------------------------------------------
# Mutation non-vacuity proofs (spawn real subprocess via prove_non_vacuous)
# ---------------------------------------------------------------------------


class TestMutationProof:
    """Mutation-proof tests for two named load-bearing lines in usage_meter.py.

    Each test removes exactly one load-bearing line using
    mutation_run.prove_non_vacuous and verifies the corresponding guard test
    goes red (testWentRed:True, nonVacuous:True).  The target lines each have a
    sibling statement in their block, so removal keeps usage_meter.py
    syntactically valid — the failure is behavioral, not a syntax error.
    """

    def _source(self) -> str:
        return str(_TOOLS / "usage_meter.py")

    def _test_cmd(self, test_spec: str) -> str:
        return (
            f'cd /d "{_TOOLS}" && '
            f"{sys.executable} -m pytest "
            f'"tests/test_usage_meter.py::{test_spec}" -q --tb=no'
        )

    def test_mutation_guard_raise(self):
        """(a) The CWE-23 raise in _guard_path is load-bearing.

        Removing 'raise ValueError(msg)' leaves the guard silent — the traversal
        check returns the path without raising, so test_write_guard_rejects_traversal
        goes red (the with pytest.raises block is never triggered).
        """
        import mutation_run
        asserted_line = "        raise ValueError(msg)"
        cmd = self._test_cmd("TestWriteLoad::test_write_guard_rejects_traversal")
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing raise ValueError(msg) must make "
            "test_write_guard_rejects_traversal go red"
        )
        assert verdict["nonVacuous"], (
            "test_write_guard_rejects_traversal must catch removal of the "
            "CWE-23 traversal guard raise"
        )

    def test_mutation_tokens_in_field(self):
        """(b) The 'tokensIn': tokens_in dict entry in build_usage is load-bearing.

        Removing '\"tokensIn\": tokens_in,' from the return dict causes
        test_nullable_tokens_in_allowed to go red (KeyError on entry['tokensIn']).
        """
        import mutation_run
        asserted_line = '        "tokensIn": tokens_in,'
        cmd = self._test_cmd("TestBuildUsage::test_nullable_tokens_in_allowed")
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing '\"tokensIn\": tokens_in,' must make "
            "test_nullable_tokens_in_allowed go red"
        )
        assert verdict["nonVacuous"], (
            "test_nullable_tokens_in_allowed must catch removal of the "
            "tokensIn field from build_usage output"
        )

    def test_mutation_prove_non_vacuous_negative_guard(self):  # noqa: D102
        """(c) The D98 non-negativity raise for cost_usd is load-bearing.

        Removing the 'raise ValueError(...)' line for cost_usd from build_usage
        leaves the guard silent — a negative cost_usd passes through — so
        test_negative_cost_usd_raises_value_error goes red.
        """
        import mutation_run
        asserted_line = (
            "            f\"usage_meter: cost_usd must be >= 0, got {cost_usd!r}\""
        )
        cmd = self._test_cmd(
            "TestBuildUsage::test_negative_cost_usd_raises_value_error"
        )
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, cmd)
        assert verdict["testWentRed"], (
            "Removing the cost_usd negcheck raise must make "
            "test_negative_cost_usd_raises_value_error go red"
        )
        assert verdict["nonVacuous"], (
            "test_negative_cost_usd_raises_value_error must catch removal of "
            "the D98 non-negativity guard raise for cost_usd"
        )
