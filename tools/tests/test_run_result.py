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


# ---------------------------------------------------------------------------
# run_gate — Q-4 timeout (a hung gate must go RED, never hang; D136)
# ---------------------------------------------------------------------------


def test_run_gate_timeout_returns_failure_shaped_result(monkeypatch):
    """Q-4: subprocess.TimeoutExpired → (output-with-note, nonzero exit), never a raise."""
    import subprocess

    def hung_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd="pytest -q", timeout=kwargs.get("timeout"), output="partial gate output"
        )

    monkeypatch.setattr(run_result.subprocess, "run", hung_run)

    output, exit_code = run_result.run_gate("pytest -q", timeout=0.01)
    assert exit_code == 124, "timeout must map to a NONZERO exit code (gate red)"
    assert "[kata] gate runner timeout after 0.01s" in output
    assert "partial gate output" in output, "partial output captured before the hang is preserved"


def test_run_gate_timeout_result_feeds_build_result_as_failure(monkeypatch):
    """The timeout tuple composes into build_result as a failed (exitCode != 0) gate."""
    import subprocess

    monkeypatch.setattr(
        run_result.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(
            subprocess.TimeoutExpired(cmd="c", timeout=k.get("timeout"))
        ),
    )

    output, exit_code = run_result.run_gate("c", timeout=1.0)
    result = run_result.build_result(
        gate_name="smoke",
        command="c",
        output=output,
        exit_code=exit_code,
        baseline_sha="a",
        result_sha="b",
        utc="2026-01-01T00:00:00+00:00",
    )
    assert result["exitCode"] != 0
    assert "[kata] gate runner timeout" in result["stdoutTail"]


def test_run_gate_forwards_default_timeout_600(monkeypatch):
    """The default 600s timeout is forwarded to subprocess.run (bounded, overridable)."""
    seen: dict = {}

    class _Proc:
        stdout = "1 passed"
        returncode = 0

    def spy_run(*args, **kwargs):
        seen.update(kwargs)
        return _Proc()

    monkeypatch.setattr(run_result.subprocess, "run", spy_run)

    output, exit_code = run_result.run_gate("pytest -q")
    assert (output, exit_code) == ("1 passed", 0)
    assert seen.get("timeout") == 600.0, (
        "Q-4: run_gate must bound the subprocess with a 600s default timeout"
    )


# ---------------------------------------------------------------------------
# evidence_is_current — pure identity gate (D136 fail-closed)
# ---------------------------------------------------------------------------


def test_stale_result_sha_does_not_pass_identity():
    """The live-repo scenario: a green RESULT.json whose resultSha is stale
    (differs from the SHA actually being credited) does NOT read as current."""
    result = _make_result(exit_code=0, result_sha="159fc9b")
    ok, reason = run_result.evidence_is_current(result, "aaaaaaa0000000000000000000000000000000")
    assert ok is False
    assert reason == "stale-evidence"


def test_matching_sha_passes_identity():
    """Matching SHAs (same length) with a passing suite read as current — no
    false positive from the identity gate itself."""
    result = _make_result(exit_code=0, result_sha="abc1234")
    ok, reason = run_result.evidence_is_current(result, "abc1234")
    assert ok is True
    assert reason == ""


def test_short_vs_long_sha_forms_of_same_commit_match():
    """A 7-char resultSha and the SAME commit's 40-char HEAD form must match
    (git's short/long form mismatch, tolerated case-insensitively)."""
    result = _make_result(exit_code=0, result_sha="AbC1234")
    long_sha = "abc1234def5678900000000000000000000000"
    ok, reason = run_result.evidence_is_current(result, long_sha)
    assert ok is True
    assert reason == ""


def test_six_char_prefix_is_not_treated_as_a_match():
    """A 6-char (or shorter) prefix is rejected outright, never matched —
    below git's own short-SHA floor, a 'match' would be coincidental."""
    result = _make_result(exit_code=0, result_sha="abc123")
    ok, reason = run_result.evidence_is_current(result, "abc123def4567890000000000000000000000000")
    assert ok is False
    assert reason == "evidence-missing-sha"


def test_missing_result_sha_fails_closed():
    """resultSha absent from RESULT.json fails closed, never treated as a pass."""
    result = _make_result(exit_code=0)
    del result["resultSha"]
    ok, reason = run_result.evidence_is_current(result, "abc1234")
    assert ok is False
    assert reason == "evidence-missing-sha"


def test_empty_result_sha_fails_closed():
    """An empty-string resultSha is treated the same as missing."""
    result = _make_result(exit_code=0, result_sha="")
    ok, reason = run_result.evidence_is_current(result, "abc1234")
    assert ok is False
    assert reason == "evidence-missing-sha"


def test_none_result_json_is_no_evidence():
    """result_json=None (RESULT.json absent/unreadable) fails closed as no-evidence."""
    ok, reason = run_result.evidence_is_current(None, "abc1234")
    assert ok is False
    assert reason == "no-evidence"


def test_expected_sha_none_fails_closed():
    """expected_sha=None (D136 case) must NOT silently pass — the caller could
    not establish what SHA is being credited, so evidence can't be current."""
    result = _make_result(exit_code=0, result_sha="abc1234")
    ok, reason = run_result.evidence_is_current(result, None)
    assert ok is False
    assert reason == "unknown-expected-sha"


def test_expected_sha_empty_string_fails_closed():
    """expected_sha='' is treated the same as None."""
    result = _make_result(exit_code=0, result_sha="abc1234")
    ok, reason = run_result.evidence_is_current(result, "")
    assert ok is False
    assert reason == "unknown-expected-sha"


def test_evidence_is_current_is_pure_and_repeatable():
    """Determinism: same inputs -> same output, repeatable, no I/O/clock/subprocess."""
    result = _make_result(exit_code=0, result_sha="abc1234")
    results = {run_result.evidence_is_current(result, "abc1234def") for _ in range(5)}
    assert results == {(True, "")}

    stale_result = _make_result(exit_code=0, result_sha="0000000")
    stale_results = {
        run_result.evidence_is_current(stale_result, "abc1234def") for _ in range(5)
    }
    assert stale_results == {(False, "stale-evidence")}


# ---------------------------------------------------------------------------
# resolve_head_sha — the identity gate's subprocess sink (registered:
# protocol/exec-safety.md). Lives here (run_result.py is ALREADY a registered
# sink module via run_gate) rather than in benchmark.py, which must stay
# subprocess-free (test_benchmark.py::TestExecSafety::test_no_subprocess_import,
# a frozen invariant).
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_resolve_head_sha_resolves_via_git_rev_parse():
    """resolve_head_sha runs `git rev-parse HEAD` against the given root and
    returns the SAME SHA a direct `git rev-parse HEAD` reports for THIS repo —
    proves the sink is wired to real git, not a stub."""
    import subprocess as _subprocess
    real = _subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert run_result.resolve_head_sha(_REPO_ROOT) == real


def test_resolve_head_sha_returns_none_for_non_git_directory(tmp_path):
    """resolve_head_sha returns None (never raises) for a directory that is
    not inside a git repository."""
    non_repo = tmp_path / "not-a-repo"
    non_repo.mkdir()
    assert run_result.resolve_head_sha(non_repo) is None


def test_resolve_head_sha_returns_none_on_timeout(monkeypatch):
    """A hung git call fails closed (None), never hangs, never raises through."""
    import subprocess as _subprocess

    def _timeout(*args, **kwargs):
        raise _subprocess.TimeoutExpired(cmd="git", timeout=30)

    monkeypatch.setattr(run_result.subprocess, "run", _timeout)
    assert run_result.resolve_head_sha("/some/path") is None


def test_resolve_head_sha_returns_none_on_nonzero_exit(monkeypatch):
    """A non-zero git exit (e.g. detached/corrupt repo) fails closed (None),
    even when stdout carries SOMETHING non-empty (e.g. a partial/garbage
    line) — the exit code must gate the result, not just an empty-string check."""
    class _Proc:
        returncode = 128
        stdout = "fatal: not a git repository (or any of the parent directories): .git\n"

    monkeypatch.setattr(run_result.subprocess, "run", lambda *a, **k: _Proc())
    assert run_result.resolve_head_sha("/some/path") is None
