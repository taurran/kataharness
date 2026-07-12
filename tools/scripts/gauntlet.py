"""gauntlet.py — honest-exit gate runner (D158).

Kills the pipe-eats-the-failure class (never again ``pytest -q | tail && git commit``):
every gate's exit code is recorded, the run ends with a deterministic summary table,
and the process exits with the FIRST non-zero gate exit code — a truncated pipe can no
longer swallow a red suite.

Gates, in canonical order, run from ``tools/``:

    1. pytest-unit          uv run pytest -m "not integration" -q
    2. pytest-integration   uv run pytest -m integration -q
    3. ruff                 uvx ruff check .
    4. validate-skills      uv run python validate_skills.py

Flags:
    --skip-integration   skip gate 2 (SKIPPED in the summary, never affects exit code)
    --skip-slow          alias of --skip-integration
    --fail-fast          stop at the first failure (default is run-all-then-report so
                         the operator sees the whole picture)

Design (testable-pure core + thin main):
    ``run_gauntlet(gates, runner=...) -> int`` is pure orchestration with an
    injectable runner and echo; ``default_runner`` is the only subprocess touchpoint.
    Gate output streams through UNMODIFIED — no capture, no truncation.  The summary
    table has a fixed column order and no timestamps (Determinism Doctrine law 6).
    Gate subprocesses run with ``PYTEST_ADDOPTS`` stripped (Doctrine law 8) and a
    fixed argv list, never ``shell=True`` (protocol/exec-safety.md posture: this is
    an operator-domain maintainer script; no external input reaches any argv).

Usage (from anywhere; the script pins its own cwd to tools/):
    uv run python scripts/gauntlet.py [--skip-integration] [--fail-fast]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]

# Fixed status vocabulary — the summary table is byte-deterministic.
PASS = "PASS"
FAIL = "FAIL"
SKIPPED = "SKIPPED"
NOT_RUN = "NOT-RUN"

# One summary row: (gate name, exit code or None, status).
Result = tuple[str, int | None, str]


@dataclass(frozen=True)
class Gate:
    """One gauntlet gate: a name and a fixed argv (never a shell string)."""

    name: str
    argv: tuple[str, ...]
    skipped: bool = False


def build_gates(skip_integration: bool = False) -> list[Gate]:
    """The four gates in canonical order; *skip_integration* marks gate 2 SKIPPED."""
    return [
        Gate("pytest-unit", ("uv", "run", "pytest", "-m", "not integration", "-q")),
        Gate(
            "pytest-integration",
            ("uv", "run", "pytest", "-m", "integration", "-q"),
            skipped=skip_integration,
        ),
        Gate("ruff", ("uvx", "ruff", "check", ".")),
        Gate("validate-skills", ("uv", "run", "python", "validate_skills.py")),
    ]


def gate_env(base_env: Mapping[str, str]) -> dict[str, str]:
    """Declared gate-subprocess environment: strip ``PYTEST_ADDOPTS`` (Doctrine law 8).

    Pure — returns a new dict; *base_env* is never mutated.
    """
    env = dict(base_env)
    env.pop("PYTEST_ADDOPTS", None)
    return env


def default_runner(gate: Gate, cwd: Path, env: dict[str, str]) -> int:
    """Run one gate via a fixed argv list; stream output through unmodified.

    No ``shell=True``, no capture/truncation — stdout/stderr inherit the parent's
    streams so the operator sees everything the gate prints.
    """
    proc = subprocess.run(list(gate.argv), cwd=str(cwd), env=env)
    return proc.returncode


def render_summary(results: Sequence[Result]) -> str:
    """Deterministic summary table: one line per gate — name, exit code, status.

    Fixed column order, fixed widths, no timestamps (Determinism Doctrine law 6).
    ``exit code`` renders as ``-`` for SKIPPED / NOT-RUN rows.
    """
    lines = ["", "gauntlet summary:", "  gate                 exit  status"]
    for name, code, status in results:
        code_str = "-" if code is None else str(code)
        lines.append(f"  {name:<20} {code_str:>4}  {status}")
    return "\n".join(lines)


def run_gauntlet(
    gates: Sequence[Gate],
    runner: Callable[[Gate, Path, dict[str, str]], int] = default_runner,
    *,
    fail_fast: bool = False,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    echo: Callable[[str], None] = print,
) -> int:
    """Run *gates* in order; return the FIRST non-zero gate exit code (0 = all green).

    Default is run-all-then-report so the operator sees the whole picture;
    ``fail_fast=True`` stops at the first failure and marks unrun gates NOT-RUN.
    SKIPPED gates never execute and never affect the exit code.
    """
    run_cwd = TOOLS_DIR if cwd is None else cwd
    run_env = gate_env(os.environ if env is None else env)
    results: list[Result] = []
    stopped = False
    for gate in gates:
        if gate.skipped:
            results.append((gate.name, None, SKIPPED))
            continue
        if stopped:
            results.append((gate.name, None, NOT_RUN))
            continue
        echo(f"gauntlet: running {gate.name}: {' '.join(gate.argv)}")
        code = runner(gate, run_cwd, run_env)
        results.append((gate.name, code, PASS if code == 0 else FAIL))
        if fail_fast and code != 0:
            stopped = True
    echo(render_summary(results))
    return next((code for _, code, _ in results if code not in (None, 0)), 0)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse gauntlet flags (``--skip-slow`` is an alias of ``--skip-integration``)."""
    parser = argparse.ArgumentParser(
        prog="gauntlet",
        description="Honest-exit gate runner: pytest (unit + integration), ruff, "
        "validate_skills — exits with the FIRST non-zero gate exit code.",
    )
    parser.add_argument(
        "--skip-integration",
        "--skip-slow",
        dest="skip_integration",
        action="store_true",
        help="skip the integration-test gate (--skip-slow is an alias)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="stop at the first failing gate (default: run all, then report)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Thin entry point: parse flags, build gates, run the gauntlet."""
    args = parse_args(argv)
    gates = build_gates(skip_integration=args.skip_integration)
    return run_gauntlet(gates, fail_fast=args.fail_fast)


if __name__ == "__main__":
    sys.exit(main())
