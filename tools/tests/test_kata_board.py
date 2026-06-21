"""Tests for kata_board.py — the single emitter for coordination files.

TDD discipline: written FIRST (red→green). All tests use tmp_path; pure stdlib;
no real kata run required.

Coverage
--------
- append_event creates board.md and writes a well-formed 5-field line
- append_progress produces TYPE=PROGRESS with msg "<step>/<n> <label>"
- multiple appends are strictly append-only (prior lines preserved, order kept)
- write_state round-trips JSON correctly
- write_state is atomic (no leftover temp file after a successful write)
- update_task changes one task's status, preserves others, and sets updatedUtc
- _safe_path rejects a kata_dir containing ".." (raises SystemExit)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Import under test
# ---------------------------------------------------------------------------

import kata_board


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AGENT = "S1a-worker"
TASK = "T1"


def _board_lines(kata_dir: Path) -> list[str]:
    """Return non-empty lines from board.md."""
    board = kata_dir / "board.md"
    return [ln for ln in board.read_text(encoding="utf-8").splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# _safe_path
# ---------------------------------------------------------------------------


def test_safe_path_rejects_dotdot_traversal(tmp_path):
    """A kata_dir containing '..' must raise SystemExit."""
    with pytest.raises(SystemExit):
        kata_board._safe_path(str(tmp_path / ".." / "escape"))


def test_safe_path_accepts_normal_path(tmp_path):
    """A normal nested path (no '..') must resolve without error."""
    result = kata_board._safe_path(str(tmp_path / "sub" / "dir"))
    assert isinstance(result, Path)
    assert ".." not in result.parts


# ---------------------------------------------------------------------------
# append_event
# ---------------------------------------------------------------------------


def test_append_event_creates_board_md(tmp_path):
    """append_event must create board.md if it does not exist."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()
    assert not (kata_dir / "board.md").exists()

    kata_board.append_event(kata_dir, AGENT, "CLAIM", TASK, "starting task")

    assert (kata_dir / "board.md").exists()


def test_append_event_writes_five_field_line(tmp_path):
    """Each appended line must split into exactly 5 fields on ' | '."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    kata_board.append_event(kata_dir, AGENT, "CLAIM", TASK, "starting task")

    lines = _board_lines(kata_dir)
    assert len(lines) == 1
    parts = lines[0].split(" | ")
    assert len(parts) == 5, f"Expected 5 fields, got {len(parts)}: {parts}"


def test_append_event_correct_type_field(tmp_path):
    """The TYPE field (index 2) must match the supplied type."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    kata_board.append_event(kata_dir, AGENT, "DONE", TASK, "tests passed")

    parts = _board_lines(kata_dir)[0].split(" | ")
    assert parts[2] == "DONE"


def test_append_event_correct_agent_field(tmp_path):
    """The agent field (index 1) must match the supplied agent."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    kata_board.append_event(kata_dir, "my-agent", "NOTE", TASK, "hi")

    parts = _board_lines(kata_dir)[0].split(" | ")
    assert parts[1] == "my-agent"


def test_append_event_correct_task_field(tmp_path):
    """The task field (index 3) must match the supplied task."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    kata_board.append_event(kata_dir, AGENT, "NOTE", "T99", "some note")

    parts = _board_lines(kata_dir)[0].split(" | ")
    assert parts[3] == "T99"


def test_append_event_correct_msg_field(tmp_path):
    """The message field (index 4) must match the supplied message."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "hello world")

    parts = _board_lines(kata_dir)[0].split(" | ")
    assert parts[4] == "hello world"


def test_append_event_timestamp_is_iso8601_utc(tmp_path):
    """The timestamp field (index 0) must look like an ISO-8601 UTC string."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    kata_board.append_event(kata_dir, AGENT, "CLAIM", TASK, "go")

    ts = _board_lines(kata_dir)[0].split(" | ")[0]
    # Must end with +00:00 or Z and contain T (basic ISO-8601 UTC check)
    assert "T" in ts
    assert ts.endswith("+00:00") or ts.endswith("Z"), f"Not UTC: {ts!r}"


# ---------------------------------------------------------------------------
# append-only: multiple appends preserve order and prior lines
# ---------------------------------------------------------------------------


def test_multiple_appends_are_append_only(tmp_path):
    """Prior lines must survive after a second append (never rewritten)."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    kata_board.append_event(kata_dir, AGENT, "CLAIM", "T1", "first")
    first_line = _board_lines(kata_dir)[0]

    kata_board.append_event(kata_dir, AGENT, "DONE", "T1", "second")
    lines = _board_lines(kata_dir)

    assert len(lines) == 2
    assert lines[0] == first_line, "First line must be unchanged after second append"


def test_multiple_appends_preserve_order(tmp_path):
    """Lines must appear in the order they were written."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    types = ["CLAIM", "NOTE", "DONE"]
    for t in types:
        kata_board.append_event(kata_dir, AGENT, t, TASK, f"msg-{t}")

    lines = _board_lines(kata_dir)
    assert len(lines) == 3
    for i, t in enumerate(types):
        assert lines[i].split(" | ")[2] == t, f"Line {i} type mismatch"


# ---------------------------------------------------------------------------
# append_progress
# ---------------------------------------------------------------------------


def test_append_progress_type_is_progress(tmp_path):
    """append_progress must emit TYPE=PROGRESS."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    kata_board.append_progress(kata_dir, AGENT, TASK, 3, 5, "writing tests")

    parts = _board_lines(kata_dir)[0].split(" | ")
    assert parts[2] == "PROGRESS"


def test_append_progress_msg_format(tmp_path):
    """append_progress msg must be '<step>/<n> <label>'."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    kata_board.append_progress(kata_dir, AGENT, TASK, 3, 5, "writing tests")

    parts = _board_lines(kata_dir)[0].split(" | ")
    assert parts[4] == "3/5 writing tests"


def test_append_progress_five_fields(tmp_path):
    """append_progress line must still have exactly 5 fields."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    kata_board.append_progress(kata_dir, AGENT, TASK, 1, 4, "init")

    parts = _board_lines(kata_dir)[0].split(" | ")
    assert len(parts) == 5


# ---------------------------------------------------------------------------
# write_state
# ---------------------------------------------------------------------------


def test_write_state_creates_state_json(tmp_path):
    """write_state must create state.json in kata_dir."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {"plan": "test.md", "tasks": {}, "updatedUtc": "2026-01-01T00:00:00+00:00"}
    kata_board.write_state(kata_dir, state)

    assert (kata_dir / "state.json").exists()


def test_write_state_round_trips_json(tmp_path):
    """write_state must produce valid JSON that round-trips exactly."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {
        "plan": "phase/plan.md",
        "tasks": {"T1": "gated", "T2": "in-progress"},
        "gate": {"tests": "10/0/0"},
        "updatedUtc": "2026-06-21T00:00:00+00:00",
    }
    kata_board.write_state(kata_dir, state)

    loaded = json.loads((kata_dir / "state.json").read_text(encoding="utf-8"))
    assert loaded == state


def test_write_state_no_leftover_temp_file(tmp_path):
    """write_state must leave no .tmp file after a successful write (atomic replace)."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {"tasks": {}, "updatedUtc": "2026-06-21T00:00:00+00:00"}
    kata_board.write_state(kata_dir, state)

    tmp_files = list(kata_dir.glob("*.tmp"))
    assert tmp_files == [], f"Leftover temp files: {tmp_files}"


def test_write_state_overwrites_previous(tmp_path):
    """write_state must overwrite (not append) the prior state.json."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state1 = {"tasks": {"T1": "assigned"}, "updatedUtc": "2026-06-21T00:00:00+00:00"}
    kata_board.write_state(kata_dir, state1)

    state2 = {"tasks": {"T1": "gated"}, "updatedUtc": "2026-06-21T01:00:00+00:00"}
    kata_board.write_state(kata_dir, state2)

    loaded = json.loads((kata_dir / "state.json").read_text(encoding="utf-8"))
    assert loaded == state2


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------


def test_update_task_changes_one_task(tmp_path):
    """update_task must change exactly the targeted task's status."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {
        "tasks": {"T1": "assigned", "T2": "in-progress", "T3": "gated"},
        "updatedUtc": "2026-06-21T00:00:00+00:00",
    }
    result = kata_board.update_task(kata_dir, state, "T2", "done")

    assert result["tasks"]["T2"] == "done"


def test_update_task_preserves_other_tasks(tmp_path):
    """update_task must not alter tasks other than the target."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {
        "tasks": {"T1": "assigned", "T2": "in-progress", "T3": "gated"},
        "updatedUtc": "2026-06-21T00:00:00+00:00",
    }
    result = kata_board.update_task(kata_dir, state, "T2", "done")

    assert result["tasks"]["T1"] == "assigned"
    assert result["tasks"]["T3"] == "gated"


def test_update_task_sets_updated_utc(tmp_path):
    """update_task must refresh updatedUtc to a current timestamp."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    old_ts = "2020-01-01T00:00:00+00:00"
    state = {"tasks": {"T1": "assigned"}, "updatedUtc": old_ts}
    result = kata_board.update_task(kata_dir, state, "T1", "in-progress")

    assert result["updatedUtc"] != old_ts
    assert "T" in result["updatedUtc"]  # still looks like ISO-8601


def test_update_task_persists_to_disk(tmp_path):
    """update_task must persist the new state to state.json."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {"tasks": {"T1": "assigned"}, "updatedUtc": "2026-06-21T00:00:00+00:00"}
    kata_board.update_task(kata_dir, state, "T1", "done")

    loaded = json.loads((kata_dir / "state.json").read_text(encoding="utf-8"))
    assert loaded["tasks"]["T1"] == "done"


def test_update_task_returns_mutated_state(tmp_path):
    """update_task must return the full (mutated) state dict."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {"tasks": {"T1": "assigned"}, "updatedUtc": "2026-06-21T00:00:00+00:00"}
    result = kata_board.update_task(kata_dir, state, "T1", "gated")

    assert isinstance(result, dict)
    assert "tasks" in result
    assert result["tasks"]["T1"] == "gated"


def test_emitter_creates_kata_dir_if_absent(tmp_path):
    """Integration robustness: the first event/state write of a run creates .kata/
    (the orchestrator should not have to pre-create it)."""
    import kata_board as kb
    fresh = tmp_path / "newrun" / ".kata"  # does NOT exist yet
    assert not fresh.exists()
    kb.append_event(fresh, "orch", "DECISION", "-", "first event")
    assert (fresh / "board.md").exists()
    kb.write_state(fresh, {"tasks": {}, "updatedUtc": "t"})
    assert (fresh / "state.json").exists()
