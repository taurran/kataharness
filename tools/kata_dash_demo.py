"""kata_dash_demo.py — KataHarness dashboard replay/animation driver.

Simulates a believable 2-worker run (CLAIM → PROGRESS heartbeats → DONE → gated)
and writes board.md + state.json each tick so the operator can watch
kata_dash.py animate live in a side terminal.

Usage:
    # Terminal 1 — drive the demo
    uv run python kata_dash_demo.py --kata-dir .kata [--speed 1.0] [--steps 5]

    # Terminal 2 — watch it animate
    COLUMNS=120 uv run python kata_dash.py --kata-dir .kata

    # Self-check (write a single mid-run frame and exit):
    uv run python kata_dash_demo.py --kata-dir /tmp/s1demo --once

Security note (from PLAN.md threat model): --kata-dir is operator-supplied;
reuses _safe_path ..  guard (CWE-23 defence-in-depth, consistent with kata_dash).

Telemetry is written via the shared `kata_board` emitter (the single source of truth
the real harness uses), so the demo exercises the same producer the dashboard consumes.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import kata_board

# ---------------------------------------------------------------------------
# Security: path-traversal guard (mirrors kata_dash._safe_path)
# ---------------------------------------------------------------------------


def _safe_path(raw: str) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied CLI path, then resolve.

    Blocks any '..' segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise SystemExit(f"kata_dash_demo: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


# ---------------------------------------------------------------------------
# Low-level write helpers (write the frozen format directly, no kata_board)
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_board_line(
    board_file: Path,
    agent: str,
    typ: str,
    task: str,
    msg: str,
) -> None:
    """Append one protocol/board.md line via the shared kata_board emitter."""
    kata_board.append_event(board_file.parent, agent, typ, task, msg)


def _write_state(state_file: Path, state: dict) -> None:
    """Atomically write state.json via the shared kata_board emitter (single-writer)."""
    kata_board.write_state(state_file.parent, state)


# ---------------------------------------------------------------------------
# Scenario: 2-worker simulated run
# ---------------------------------------------------------------------------

_WORKERS = [
    {
        "agent": "worker-S1a",
        "task": "S1a-emitter",
        "steps": [
            "reading spec",
            "writing board helpers",
            "writing write_state",
            "writing tests",
            "verify passing",
        ],
    },
    {
        "agent": "worker-S1b",
        "task": "S1b-dashboard",
        "steps": [
            "reading model",
            "parsing PROGRESS lines",
            "smooth-bar mapping",
            "updating render title",
            "writing demo driver",
        ],
    },
]

_GATE_TASK = "S1c-gate"
_GATE_AGENT = "orchestrator"


def _build_initial_state(workers: list[dict]) -> dict:
    """Build an initial state.json dict with all tasks in 'assigned' status."""
    tasks = {w["task"]: "assigned" for w in workers}
    tasks[_GATE_TASK] = "assigned"
    return {
        "plan": ".planning/specs/loop-hardening/PLAN-s1.md",
        "forkPoint": "abc1234",
        "integrationBranch": "s1/integration",
        "wavesDone": [],
        "tasks": tasks,
        "gate": None,
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0, "interventions": 0},
        "updatedUtc": _utc_now(),
    }


def _run_demo(
    kata_dir: Path,
    n_steps: int,
    speed: float,
    once: bool,
) -> int:
    """Simulate a 2-worker run, writing board.md + state.json each tick.

    Returns the total number of ticks written.
    """
    kata_dir.mkdir(parents=True, exist_ok=True)
    board_file = kata_dir / "board.md"
    state_file = kata_dir / "state.json"

    # Clear previous run artifacts
    if board_file.exists():
        board_file.unlink()

    workers = [
        {
            "agent": w["agent"],
            "task": w["task"],
            "steps": w["steps"][:n_steps],
        }
        for w in _WORKERS
    ]

    state = _build_initial_state(workers)
    _write_state(state_file, state)

    tick_count = 0
    delay = 0.4 * speed  # seconds between ticks; skipped in --once mode

    # Phase 1: CLAIM both tasks
    for w in workers:
        _append_board_line(board_file, w["agent"], "CLAIM", w["task"], "starting assigned task")
        state["tasks"][w["task"]] = "in-progress"
        state["updatedUtc"] = _utc_now()
        _write_state(state_file, state)
        tick_count += 1
        if not once:
            time.sleep(delay)

    if once:
        # Write a mid-run snapshot: emit step 1 of each worker's progress and stop
        for w in workers:
            label = w["steps"][0] if w["steps"] else "starting"
            _append_board_line(
                board_file, w["agent"], "PROGRESS", w["task"],
                f"1/{max(1, len(w['steps']))} {label}",
            )
            tick_count += 1
        state["updatedUtc"] = _utc_now()
        _write_state(state_file, state)
        return tick_count

    # Phase 2: Interleaved PROGRESS heartbeats (step climbing 1..n)
    total_steps = max(len(w["steps"]) for w in workers)
    for step_idx in range(total_steps):
        for w in workers:
            steps_list = w["steps"]
            if step_idx >= len(steps_list):
                continue
            step_num = step_idx + 1
            n = len(steps_list)
            label = steps_list[step_idx]
            _append_board_line(
                board_file, w["agent"], "PROGRESS", w["task"],
                f"{step_num}/{n} {label}",
            )
            state["updatedUtc"] = _utc_now()
            _write_state(state_file, state)
            tick_count += 1
            time.sleep(delay)

    # Phase 3: DONE for each worker
    for w in workers:
        _append_board_line(board_file, w["agent"], "DONE", w["task"], "verify passed")
        state["tasks"][w["task"]] = "done"
        state["updatedUtc"] = _utc_now()
        _write_state(state_file, state)
        tick_count += 1
        time.sleep(delay)

    # Phase 4: Gate integration
    _append_board_line(board_file, _GATE_AGENT, "DECISION", _GATE_TASK, "all tasks verified — gating")
    for w in workers:
        state["tasks"][w["task"]] = "gated"
    state["tasks"][_GATE_TASK] = "gated"
    state["gate"] = {"tests": "205+/0/0", "build": "ok", "security": "0"}
    state["wavesDone"] = ["wave1"]
    state["updatedUtc"] = _utc_now()
    _write_state(state_file, state)
    tick_count += 1
    time.sleep(delay)

    return tick_count


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: Optional[list] = None) -> None:
    """CLI entry-point for the KataHarness dashboard replay/demo driver."""
    parser = argparse.ArgumentParser(
        prog="kata_dash_demo",
        description=(
            "KataHarness dashboard replay driver — simulate a 2-worker run so you can\n"
            "watch kata_dash.py animate live in a side terminal."
        ),
    )
    parser.add_argument(
        "--kata-dir",
        default=".kata",
        metavar="DIR",
        help="Path to the .kata/ directory to write (default: .kata)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        metavar="FACTOR",
        help="Speed multiplier — smaller is faster (default: 1.0, ~0.4s per tick)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=5,
        metavar="N",
        help="Number of PROGRESS steps per worker (default: 5)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Write a single mid-run frame of board+state and exit (no live loop or sleeps)",
    )
    args = parser.parse_args(argv)

    kata_dir = _safe_path(args.kata_dir)

    n_ticks = _run_demo(
        kata_dir=kata_dir,
        n_steps=args.steps,
        speed=args.speed,
        once=args.once,
    )

    print(f"demo wrote {n_ticks} ticks to {kata_dir}")


if __name__ == "__main__":
    main()
