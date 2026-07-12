import mutation_check


def test_mutation_verdict_nonvacuous_when_baseline_passed_mutated_failed():
    """green before, red after mutation → non-vacuous proof."""
    result = mutation_check.mutation_verdict(True, False)
    assert result["testWentRed"] is True
    assert result["nonVacuous"] is True


def test_mutation_verdict_vacuous_when_both_passed():
    """test still passes after mutation → vacuous (no bite)."""
    result = mutation_check.mutation_verdict(True, True)
    assert result["testWentRed"] is False
    assert result["nonVacuous"] is False


def test_mutation_verdict_nonvacuous_false_when_baseline_failed():
    """baseline already failed → can't claim non-vacuity."""
    result = mutation_check.mutation_verdict(False, False)
    assert result["testWentRed"] is False
    assert result["nonVacuous"] is False


def test_apply_line_removal_removes_first_occurrence():
    """Removes the first exact occurrence of target_line from source."""
    result = mutation_check.apply_line_removal("a\nB\nc\n", "B")
    assert "B" not in result
    assert "a" in result
    assert "c" in result


def test_apply_line_removal_raises_for_absent_line():
    """Raises ValueError if target_line is not present in source."""
    try:
        mutation_check.apply_line_removal("a\nB\nc\n", "Z")
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# FIX A1 BC tests — cwd kwarg added to run_named_test (BC: default None)
# ---------------------------------------------------------------------------


def test_run_named_test_accepts_cwd_kwarg():
    """run_named_test accepts cwd kwarg without error; cwd is forwarded to subprocess (FIX A1)."""
    from unittest.mock import MagicMock, patch

    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = mutation_check.run_named_test(
            "tests/test_foo.py", "test_bar", cwd="/tmp/clone"
        )
    assert result is True
    call_kwargs = mock_run.call_args[1]
    assert call_kwargs.get("cwd") == "/tmp/clone", (
        "FIX A1: cwd kwarg must be forwarded to subprocess.run"
    )


def test_run_named_test_cwd_none_is_bc_default():
    """run_named_test with cwd=None passes cwd=None to subprocess (BC, FIX A1)."""
    from unittest.mock import MagicMock, patch

    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        mutation_check.run_named_test("tests/test_foo.py", "test_bar")

    call_kwargs = mock_run.call_args[1]
    assert call_kwargs.get("cwd") is None, (
        "BC: cwd=None → subprocess.run must receive cwd=None (unchanged behavior)"
    )


# ---------------------------------------------------------------------------
# Q-4 timeout tests — a hung pytest subprocess must go RED, never hang (D136)
# ---------------------------------------------------------------------------


def test_run_named_test_timeout_returns_false(capsys):
    """Q-4: subprocess.TimeoutExpired → False (failure-shaped), never an unhandled raise."""
    import subprocess
    from unittest.mock import patch

    boom = subprocess.TimeoutExpired(cmd="uv run pytest", timeout=0.01)
    with patch("subprocess.run", side_effect=boom):
        result = mutation_check.run_named_test(
            "tests/test_foo.py", "test_bar", timeout=0.01
        )
    assert result is False, "a timed-out gate run must be a FAILURE verdict (gate red)"
    captured = capsys.readouterr()
    assert "[kata] gate runner timeout" in captured.err


def test_run_named_test_forwards_default_timeout_600():
    """The default 600s timeout is forwarded to subprocess.run (bounded, overridable)."""
    from unittest.mock import MagicMock, patch

    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        mutation_check.run_named_test("tests/test_foo.py", "test_bar")

    call_kwargs = mock_run.call_args[1]
    assert call_kwargs.get("timeout") == 600.0, (
        "Q-4: run_named_test must bound the subprocess with a 600s default timeout"
    )


def test_run_named_test_env_is_sanitized(monkeypatch, tmp_path):
    """DET-09: run_named_test strips PYTEST_ADDOPTS + disables plugin autoload."""
    import mutation_check

    monkeypatch.setenv("PYTEST_ADDOPTS", "-x")
    seen: dict = {}

    class _Ok:
        returncode = 0

    def spy_run(*args, **kwargs):
        seen.update(kwargs)
        return _Ok()

    monkeypatch.setattr(mutation_check.subprocess, "run", spy_run)
    mutation_check.run_named_test(str(tmp_path / "t.py"), "test_x")
    env = seen.get("env") or {}
    assert "PYTEST_ADDOPTS" not in env
    assert env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"


def test_run_named_test_sanitized_env_composes_with_cwd_pythonpath(monkeypatch, tmp_path):
    """The cwd PYTHONPATH prepend composes on top of the sanitized env (DET-09)."""
    import os as _os

    import mutation_check

    seen: dict = {}

    class _Ok:
        returncode = 0

    def spy_run(*args, **kwargs):
        seen.update(kwargs)
        return _Ok()

    monkeypatch.setattr(mutation_check.subprocess, "run", spy_run)
    mutation_check.run_named_test(str(tmp_path / "t.py"), "test_x", cwd=str(tmp_path))
    env = seen.get("env") or {}
    assert env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    assert str(tmp_path) in env.get("PYTHONPATH", "")
