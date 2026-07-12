"""test_gauntlet_script.py — D158: honest-exit gauntlet helper (tools/scripts/gauntlet.py).

Kills the pipe-eats-the-failure class (`pytest -q | tail && git commit`): every gate's
exit code is recorded and the script exits with the FIRST non-zero gate exit code.

These tests exercise ONLY the pure parts (gate construction, env stripping, exit-code
selection, summary rendering, flag parsing) via the injectable runner seam.  The real
gauntlet is NEVER invoked from here — gate 1 is `uv run pytest`, which would recurse
the suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import gauntlet  # noqa: E402

# ---------------------------------------------------------------------------
# Gate construction (argv is a fixed list — never a shell string)
# ---------------------------------------------------------------------------


def test_build_gates_canonical_order_and_argv():
    gates = gauntlet.build_gates()
    assert [g.name for g in gates] == [
        "pytest-unit",
        "pytest-integration",
        "ruff",
        "validate-skills",
    ]
    assert gates[0].argv == ("uv", "run", "pytest", "-m", "not integration", "-q")
    assert gates[1].argv == ("uv", "run", "pytest", "-m", "integration", "-q")
    assert gates[2].argv == ("uvx", "ruff", "check", ".")
    assert gates[3].argv == ("uv", "run", "python", "validate_skills.py")
    for g in gates:
        assert isinstance(g.argv, tuple), "argv must be structured, never a shell string"
        assert all(isinstance(part, str) for part in g.argv)


def test_build_gates_default_nothing_skipped():
    assert [g.skipped for g in gauntlet.build_gates()] == [False, False, False, False]


def test_build_gates_skip_integration_marks_only_integration():
    gates = gauntlet.build_gates(skip_integration=True)
    assert [g.skipped for g in gates] == [False, True, False, False]


# ---------------------------------------------------------------------------
# Gate env — Doctrine law 8: strip PYTEST_ADDOPTS
# ---------------------------------------------------------------------------


def test_gate_env_strips_pytest_addopts_keeps_rest():
    base = {"PYTEST_ADDOPTS": "-x --lf", "PATH": "/bin", "KEEP": "1"}
    env = gauntlet.gate_env(base)
    assert "PYTEST_ADDOPTS" not in env
    assert env["PATH"] == "/bin"
    assert env["KEEP"] == "1"
    # pure: the input mapping is not mutated
    assert base["PYTEST_ADDOPTS"] == "-x --lf"


def test_gate_env_noop_when_absent():
    assert gauntlet.gate_env({"A": "b"}) == {"A": "b"}


# ---------------------------------------------------------------------------
# run_gauntlet — orchestration via the injectable runner
# ---------------------------------------------------------------------------


def _runner_returning(codes: dict[str, int]):
    calls: list[str] = []

    def runner(gate, cwd, env):
        calls.append(gate.name)
        return codes[gate.name]

    return runner, calls


def test_all_pass_exit_zero_all_gates_run():
    gates = gauntlet.build_gates()
    runner, calls = _runner_returning({g.name: 0 for g in gates})
    out: list[str] = []
    code = gauntlet.run_gauntlet(gates, runner, echo=out.append)
    assert code == 0
    assert calls == ["pytest-unit", "pytest-integration", "ruff", "validate-skills"]


def test_exit_is_first_nonzero_and_default_runs_all():
    """Default is run-all-then-report: a mid-gauntlet failure does not stop later
    gates, and the exit code is the FIRST non-zero (not the last)."""
    gates = gauntlet.build_gates()
    runner, calls = _runner_returning(
        {"pytest-unit": 0, "pytest-integration": 3, "ruff": 5, "validate-skills": 0}
    )
    out: list[str] = []
    code = gauntlet.run_gauntlet(gates, runner, echo=out.append)
    assert code == 3, "exit code must be the FIRST non-zero gate exit code"
    assert calls == ["pytest-unit", "pytest-integration", "ruff", "validate-skills"]


def test_fail_fast_stops_at_first_failure():
    gates = gauntlet.build_gates()
    runner, calls = _runner_returning(
        {"pytest-unit": 0, "pytest-integration": 2, "ruff": 0, "validate-skills": 0}
    )
    out: list[str] = []
    code = gauntlet.run_gauntlet(gates, runner, fail_fast=True, echo=out.append)
    assert code == 2
    assert calls == ["pytest-unit", "pytest-integration"], "fail-fast must stop the gauntlet"
    summary = out[-1]
    assert "NOT-RUN" in summary
    assert summary.count("NOT-RUN") == 2  # ruff + validate-skills never ran


def test_skipped_gate_never_runs_and_does_not_affect_exit():
    gates = gauntlet.build_gates(skip_integration=True)
    runner, calls = _runner_returning({"pytest-unit": 0, "ruff": 0, "validate-skills": 0})
    out: list[str] = []
    code = gauntlet.run_gauntlet(gates, runner, echo=out.append)
    assert code == 0, "SKIPPED gates must not affect the exit code"
    assert "pytest-integration" not in calls
    assert "SKIPPED" in out[-1]


def test_runner_receives_env_with_addopts_stripped():
    gates = gauntlet.build_gates()
    seen_envs: list[dict] = []

    def runner(gate, cwd, env):
        seen_envs.append(env)
        return 0

    gauntlet.run_gauntlet(
        gates, runner, env={"PYTEST_ADDOPTS": "-x", "KEEP": "1"}, echo=lambda s: None
    )
    for env in seen_envs:
        assert "PYTEST_ADDOPTS" not in env
        assert env["KEEP"] == "1"


def test_runner_receives_tools_dir_cwd_by_default():
    gates = gauntlet.build_gates()[:1]
    seen: list[Path] = []

    def runner(gate, cwd, env):
        seen.append(cwd)
        return 0

    gauntlet.run_gauntlet(gates, runner, env={}, echo=lambda s: None)
    assert seen == [gauntlet.TOOLS_DIR]
    assert gauntlet.TOOLS_DIR.name == "tools"


# ---------------------------------------------------------------------------
# Summary rendering — deterministic: fixed column order, no timestamps
# ---------------------------------------------------------------------------


def test_render_summary_exact_bytes():
    results = [
        ("pytest-unit", 0, "PASS"),
        ("pytest-integration", None, "SKIPPED"),
        ("ruff", 1, "FAIL"),
        ("validate-skills", None, "NOT-RUN"),
    ]
    expected = (
        "\n"
        "gauntlet summary:\n"
        "  gate                 exit  status\n"
        "  pytest-unit             0  PASS\n"
        "  pytest-integration      -  SKIPPED\n"
        "  ruff                    1  FAIL\n"
        "  validate-skills         -  NOT-RUN"
    )
    assert gauntlet.render_summary(results) == expected


def test_render_summary_deterministic_across_calls():
    results = [("a-gate", 0, "PASS"), ("b-gate", 7, "FAIL")]
    assert gauntlet.render_summary(results) == gauntlet.render_summary(results)


def test_summary_has_no_timestamp():
    """No wall-clock content in the summary (Determinism Doctrine law 6)."""
    out: list[str] = []
    gates = gauntlet.build_gates()
    runner, _ = _runner_returning({g.name: 0 for g in gates})
    gauntlet.run_gauntlet(gates, runner, echo=out.append)
    summary = out[-1]
    import re

    assert not re.search(r"\d{4}-\d{2}-\d{2}|\d{2}:\d{2}", summary)


# ---------------------------------------------------------------------------
# Flag parsing + thin main wiring
# ---------------------------------------------------------------------------


def test_parse_args_defaults():
    args = gauntlet.parse_args([])
    assert args.skip_integration is False
    assert args.fail_fast is False


def test_parse_args_skip_integration():
    assert gauntlet.parse_args(["--skip-integration"]).skip_integration is True


def test_parse_args_skip_slow_is_alias_of_skip_integration():
    assert gauntlet.parse_args(["--skip-slow"]).skip_integration is True


def test_parse_args_fail_fast():
    assert gauntlet.parse_args(["--fail-fast"]).fail_fast is True


def test_main_wires_flags_into_run(monkeypatch):
    captured: dict = {}

    def fake_run(gates, runner=gauntlet.default_runner, *, fail_fast=False, **kwargs):
        captured["gates"] = gates
        captured["fail_fast"] = fail_fast
        return 42

    monkeypatch.setattr(gauntlet, "run_gauntlet", fake_run)
    code = gauntlet.main(["--skip-slow", "--fail-fast"])
    assert code == 42
    assert captured["fail_fast"] is True
    assert [g.skipped for g in captured["gates"]] == [False, True, False, False]


# ---------------------------------------------------------------------------
# default_runner — list argv, no shell=True, streams through (no capture)
# ---------------------------------------------------------------------------


def test_default_runner_list_argv_no_shell_no_capture(monkeypatch):
    recorded: dict = {}

    class FakeProc:
        returncode = 7

    def fake_run(argv, **kwargs):
        recorded["argv"] = argv
        recorded["kwargs"] = kwargs
        return FakeProc()

    monkeypatch.setattr(gauntlet.subprocess, "run", fake_run)
    gate = gauntlet.Gate("demo", ("uvx", "ruff", "check", "."))
    code = gauntlet.default_runner(gate, Path("."), {"A": "b"})
    assert code == 7
    assert recorded["argv"] == ["uvx", "ruff", "check", "."]
    kwargs = recorded["kwargs"]
    assert not kwargs.get("shell", False), "never shell=True"
    for capture_kw in ("capture_output", "stdout", "stderr"):
        assert capture_kw not in kwargs, "output must stream through unmodified"
    assert kwargs["env"] == {"A": "b"}
