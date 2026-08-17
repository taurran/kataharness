"""test_kata_dash_demo.py — TDD tests for kata_dash_demo replay driver.

Tests use --once mode into tmp_path to avoid real-time sleeps.
Validates:
- --once writes board.md and state.json to the specified kata-dir
- board.md contains PROGRESS lines
- PROGRESS heartbeats are monotonically increasing within a task
- state.json is valid JSON with expected shape
- The ..  guard rejects path traversal
- No real sleeps are tested (only --once mode)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import check
# ---------------------------------------------------------------------------


def test_kata_dash_demo_importable():
    """kata_dash_demo must be importable without side-effects."""
    import kata_dash_demo  # noqa: F401


def test_kata_dash_demo_uses_kata_board():
    """Post-integration: the demo writes telemetry via the shared kata_board emitter
    (single source of truth — the same producer the dashboard consumes)."""
    import inspect
    import sys

    if "kata_dash_demo" in sys.modules:
        del sys.modules["kata_dash_demo"]

    import kata_dash_demo as m

    source = inspect.getsource(m)
    assert "import kata_board" in source, (
        "kata_dash_demo should delegate telemetry writes to kata_board after integration"
    )


# ---------------------------------------------------------------------------
# --once mode: files are written
# ---------------------------------------------------------------------------


def test_once_writes_board_md(tmp_path):
    """--once must write a board.md file to --kata-dir."""
    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_file = kata_dir / "board.md"
    assert board_file.exists(), "board.md must exist after --once run"
    content = board_file.read_text(encoding="utf-8")
    assert content.strip(), "board.md must not be empty"


def test_once_writes_state_json(tmp_path):
    """--once must write a state.json file to --kata-dir."""
    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    state_file = kata_dir / "state.json"
    assert state_file.exists(), "state.json must exist after --once run"


def test_state_json_is_valid_json(tmp_path):
    """state.json must be parseable valid JSON."""
    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    state_file = kata_dir / "state.json"
    raw = state_file.read_text(encoding="utf-8")
    try:
        state = json.loads(raw)
    except json.JSONDecodeError as exc:
        pytest.fail(f"state.json is not valid JSON: {exc}\nContent: {raw[:200]}")
    assert isinstance(state, dict), "state.json top level must be a dict"


def test_state_json_has_tasks_key(tmp_path):
    """state.json must have a 'tasks' key."""
    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    state = json.loads((kata_dir / "state.json").read_text(encoding="utf-8"))
    assert "tasks" in state, "state.json must have 'tasks' key"
    assert isinstance(state["tasks"], dict), "'tasks' must be a dict"


def test_state_json_has_updated_utc(tmp_path):
    """state.json must have an 'updatedUtc' key."""
    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    state = json.loads((kata_dir / "state.json").read_text(encoding="utf-8"))
    assert "updatedUtc" in state, "state.json must have 'updatedUtc'"
    assert isinstance(state["updatedUtc"], str)


# ---------------------------------------------------------------------------
# board.md format validation
# ---------------------------------------------------------------------------


def _parse_board_lines(board_text: str):
    """Parse cursor lines into list of dicts via the ONE canonical parser.

    Delegates to ``kata_board.parse_cursor`` rather than hand-indexing fields —
    a second parser in a test is still a second source of truth, and hand-indexing
    is exactly what silently mis-read the migrated grammar.  Any grammar violation
    (including a LEGACY 5-field line) PROPAGATES as ``CursorParseError``: this
    helper never skips, so a demo that emitted a bad cursor fails loudly.
    """
    import kata_board

    return [
        {
            "utc": ln.utc,
            "seq": ln.seq,
            "agent": ln.agent,
            "type": ln.type,
            "task": ln.task,
            "msg": ln.msg,
        }
        for ln in kata_board.parse_cursor(board_text).lines
    ]


def test_board_opens_with_a_run_header(tmp_path):
    """The demo must mint the run via kata_board.start_run — the ONE legal path.

    A cursor is ``run-header line*`` (DESIGN §2.2); without the header the first
    append is refused, which is precisely how the grammar migration broke the demo.
    """
    import kata_board

    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_text = (kata_dir / "board.md").read_text(encoding="utf-8")
    assert board_text.startswith("RUN run-"), (
        f"cursor must open with a run-header block, got: {board_text[:60]!r}"
    )
    cursor = kata_board.parse_cursor(board_text)
    kata_board.validate_run_id(cursor.run_id)


def test_board_lines_are_canonical_cursor_lines(tmp_path):
    """Every non-header, non-blank cursor line must satisfy the 6-field grammar."""
    import kata_board

    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_text = (kata_dir / "board.md").read_text(encoding="utf-8")
    _header, consumed = kata_board.parse_header(board_text)
    non_blank = [l for l in board_text.splitlines()[consumed:] if l.strip()]
    parsed = _parse_board_lines(board_text)
    assert len(parsed) == len(non_blank), (
        f"All non-blank lines must be canonical cursor lines. "
        f"Non-blank: {len(non_blank)}, parsed: {len(parsed)}"
    )
    assert parsed, "demo must emit at least one cursor line"


def test_demo_board_rejects_the_legacy_grammar(tmp_path):
    """Proof the migration happened: a LEGACY 5-field line is REFUSED, not parsed.

    If this helper still accepted the old grammar the migration would be
    unverified — a legacy fixture that passes proves nothing changed.
    """
    import kata_board

    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_text = (kata_dir / "board.md").read_text(encoding="utf-8")
    legacy = board_text + "2026-06-21T10:00:00Z | worker-S1a | CLAIM | S1a-emitter | legacy\n"
    with pytest.raises(kata_board.CursorParseError, match="LEGACY 5-field"):
        _parse_board_lines(legacy)


def test_board_contains_claim_lines(tmp_path):
    """board.md must contain at least one CLAIM line."""
    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_text = (kata_dir / "board.md").read_text(encoding="utf-8")
    lines = _parse_board_lines(board_text)
    claim_lines = [l for l in lines if l["type"] == "CLAIM"]
    assert len(claim_lines) >= 1, "board.md must contain at least one CLAIM line"


def test_board_contains_progress_lines(tmp_path):
    """board.md must contain PROGRESS heartbeat lines."""
    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_text = (kata_dir / "board.md").read_text(encoding="utf-8")
    lines = _parse_board_lines(board_text)
    progress_lines = [l for l in lines if l["type"] == "PROGRESS"]
    assert len(progress_lines) >= 1, "board.md must contain PROGRESS heartbeat lines"


def test_progress_lines_have_step_fraction_format(tmp_path):
    """PROGRESS msg must match '<step>/<n> <label>' format."""
    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_text = (kata_dir / "board.md").read_text(encoding="utf-8")
    lines = _parse_board_lines(board_text)
    progress_lines = [l for l in lines if l["type"] == "PROGRESS"]

    for line in progress_lines:
        msg = line["msg"]
        parts = msg.split(" ", maxsplit=1)
        fraction = parts[0]
        assert "/" in fraction, (
            f"PROGRESS msg must start with 'step/n', got: {msg!r}"
        )
        step_str, n_str = fraction.split("/", maxsplit=1)
        try:
            step = int(step_str)
            n = int(n_str)
        except ValueError:
            pytest.fail(f"PROGRESS fraction not integers: {fraction!r} in msg {msg!r}")
        assert n > 0, f"n must be positive, got {n} in msg {msg!r}"
        assert 0 <= step <= n * 2, f"step {step} unreasonably large vs n {n}"


def test_progress_heartbeats_monotonic_within_task(tmp_path):
    """PROGRESS step must be non-decreasing within each task's sequence."""
    import kata_dash_demo

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_text = (kata_dir / "board.md").read_text(encoding="utf-8")
    lines = _parse_board_lines(board_text)
    progress_lines = [l for l in lines if l["type"] == "PROGRESS"]

    # Group by task, check monotonic
    from collections import defaultdict
    by_task: dict[str, list[int]] = defaultdict(list)
    for line in progress_lines:
        msg = line["msg"]
        fraction = msg.split(" ", maxsplit=1)[0]
        if "/" not in fraction:
            continue
        step_str, _ = fraction.split("/", maxsplit=1)
        try:
            step = int(step_str)
        except ValueError:
            continue
        by_task[line["task"]].append(step)

    for task_id, steps in by_task.items():
        for i in range(len(steps) - 1):
            assert steps[i] <= steps[i + 1], (
                f"Task {task_id!r} steps not monotonic: {steps}"
            )


def test_board_parseable_by_kata_dash_model(tmp_path):
    """board.md written by demo must be parseable by kata_dash_model.parse_board."""
    import kata_dash_demo
    import kata_dash_model

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_text = (kata_dir / "board.md").read_text(encoding="utf-8")
    events = kata_dash_model.parse_board(board_text)
    assert len(events) >= 1, "parse_board must extract at least one event from demo board"

    # Should have at least one PROGRESS event
    progress = [e for e in events if e.type == "PROGRESS"]
    assert len(progress) >= 1, "parse_board must find at least one PROGRESS event"


def test_state_json_parseable_by_build_view_model(tmp_path):
    """state.json + board.md must produce a valid ViewModel via build_view_model."""
    import kata_dash_demo
    import kata_dash_model

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_text = (kata_dir / "board.md").read_text(encoding="utf-8")
    state = json.loads((kata_dir / "state.json").read_text(encoding="utf-8"))

    # Must not raise
    vm = kata_dash_model.build_view_model(board_text, state)
    assert isinstance(vm, kata_dash_model.ViewModel)
    assert not vm.waiting


# ---------------------------------------------------------------------------
# --steps argument
# ---------------------------------------------------------------------------


def test_steps_argument_accepted(tmp_path):
    """--steps N must be accepted and produce valid output."""
    import kata_dash_demo

    kata_dir = tmp_path / ".kata2"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once", "--steps", "3"])

    assert (kata_dir / "board.md").exists()
    assert (kata_dir / "state.json").exists()


# ---------------------------------------------------------------------------
# _safe_path: path traversal guard
# ---------------------------------------------------------------------------


def test_safe_path_rejects_dotdot():
    """Demo must refuse a --kata-dir containing '..' segments."""
    import kata_dash_demo

    with pytest.raises(ValueError):
        kata_dash_demo.main(["--kata-dir", "../escape", "--once"])


# ---------------------------------------------------------------------------
# Smoke: demo output + dashboard render together
# ---------------------------------------------------------------------------


def test_demo_plus_dashboard_renders_without_error(tmp_path):
    """Running demo --once then kata_dash --once on the same dir must not crash."""
    import kata_dash
    import kata_dash_demo
    import kata_dash_model

    kata_dir = tmp_path / ".kata"
    kata_dash_demo.main(["--kata-dir", str(kata_dir), "--once"])

    board_text = (kata_dir / "board.md").read_text(encoding="utf-8")
    state = json.loads((kata_dir / "state.json").read_text(encoding="utf-8"))

    vm = kata_dash_model.build_view_model(board_text, state)
    try:
        frame = kata_dash.build_frame(vm, tick=0)
    except Exception as exc:
        pytest.fail(f"build_frame raised after demo --once: {exc}")
    assert frame is not None
