"""Tests for run_result.py — gate RESULT emitter.

Run from the tools/ directory:
    uv run pytest tests/test_run_result.py -q
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import run_result


REQUIRED_KEYS = {
    "gateName",
    "command",
    "exitCode",
    "passed",
    "failed",
    "skipped",
    "stdoutTail",
    "baselineSha",
    "resultSha",
    "utc",
}


def _make_result(**overrides) -> dict:
    """Return a build_result call with sensible defaults."""
    kwargs = dict(
        gate_name="smoke",
        command="pytest tests/ -q",
        output="40 passed in 0.2s",
        exit_code=0,
        baseline_sha="abc1234",
        result_sha="def5678",
        utc="2026-01-01T00:00:00+00:00",
    )
    kwargs.update(overrides)
    return run_result.build_result(**kwargs)


# ---------------------------------------------------------------------------
# Key presence
# ---------------------------------------------------------------------------


def test_all_required_keys_present():
    result = _make_result()
    missing = REQUIRED_KEYS - result.keys()
    assert missing == set(), f"Missing keys: {missing}"


def test_no_unexpected_keys():
    result = _make_result()
    extra = result.keys() - REQUIRED_KEYS
    assert extra == set(), f"Unexpected extra keys: {extra}"


# ---------------------------------------------------------------------------
# Parsing — single-line pytest summary
# ---------------------------------------------------------------------------


def test_40_passed_parses_correctly():
    result = _make_result(output="40 passed in 0.2s", exit_code=0)
    assert result["passed"] == 40
    assert result["failed"] == 0
    assert result["skipped"] == 0
    assert result["exitCode"] == 0


def test_2_failed_38_passed_parses_correctly():
    result = _make_result(output="38 passed, 2 failed in 1.0s", exit_code=1)
    assert result["failed"] == 2
    assert result["passed"] == 38
    assert result["skipped"] == 0
    assert result["exitCode"] == 1


def test_skipped_parsed():
    result = _make_result(output="5 passed, 1 skipped in 0.5s", exit_code=0)
    assert result["passed"] == 5
    assert result["skipped"] == 1
    assert result["failed"] == 0


def test_all_three_counts_parsed():
    result = _make_result(output="10 passed, 3 failed, 2 skipped in 2.1s", exit_code=1)
    assert result["passed"] == 10
    assert result["failed"] == 3
    assert result["skipped"] == 2


def test_no_counts_in_output_defaults_to_zero():
    result = _make_result(output="no summary line here", exit_code=0)
    assert result["passed"] == 0
    assert result["failed"] == 0
    assert result["skipped"] == 0


# ---------------------------------------------------------------------------
# stdoutTail
# ---------------------------------------------------------------------------


def test_stdout_tail_short_output():
    short = "hello world"
    result = _make_result(output=short)
    assert result["stdoutTail"] == short


def test_stdout_tail_truncated_to_2000():
    long_output = "x" * 5000
    result = _make_result(output=long_output)
    assert len(result["stdoutTail"]) <= 2000
    assert result["stdoutTail"] == long_output[-2000:]


# ---------------------------------------------------------------------------
# sha passthrough
# ---------------------------------------------------------------------------


def test_shas_passed_through():
    result = _make_result(baseline_sha="aaaaaa", result_sha="bbbbbb")
    assert result["baselineSha"] == "aaaaaa"
    assert result["resultSha"] == "bbbbbb"


# ---------------------------------------------------------------------------
# utc — injectable for determinism
# ---------------------------------------------------------------------------


def test_utc_injectable():
    fixed = "2026-06-19T12:34:56+00:00"
    result = _make_result(utc=fixed)
    assert result["utc"] == fixed


def test_utc_defaults_to_now_when_none():
    """When utc=None, build_result must fill in a valid ISO-8601 UTC string."""
    result = run_result.build_result(
        gate_name="g",
        command="c",
        output="",
        exit_code=0,
        baseline_sha="x",
        result_sha="y",
        utc=None,
    )
    # Must parse as a valid datetime
    parsed = datetime.fromisoformat(result["utc"])
    assert parsed.tzinfo is not None


# ---------------------------------------------------------------------------
# write_result round-trip
# ---------------------------------------------------------------------------


def test_write_result_round_trips():
    result = _make_result()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "RESULT.json"
        run_result.write_result(result, path)
        loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded == result


def test_write_result_is_indented():
    result = _make_result()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "RESULT.json"
        run_result.write_result(result, path)
        raw = path.read_text(encoding="utf-8")
    # indent=2 means lines start with spaces for nested keys
    assert "\n  " in raw


def test_write_result_accepts_str_path():
    result = _make_result()
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "RESULT.json")
        run_result.write_result(result, path)
        loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    assert loaded == result
