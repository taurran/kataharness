"""Tests for kata_dash_model.py — pure board+state parser -> dashboard ViewModel.

TDD discipline: tests written FIRST, before kata_dash_model.py existed.
All tests are PURE — no I/O, no rich, deterministic.

Coverage:
- parse_board: well-formed multi-line, malformed lines skipped, order preserved
- status_to_percent: EACH exact mapping value
- build_view_model: tasks rows, gate, driftEscalations, phase derivation, wave, events truncation
- waiting path (state=None + empty board → waiting True; with data → waiting False)
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Import checks
# ---------------------------------------------------------------------------


def test_kata_dash_model_importable():
    """Module must be importable without side-effects."""
    import kata_dash_model  # noqa: F401


def test_no_rich_import():
    """kata_dash_model must NOT import rich (it is the pure layer)."""
    import importlib
    import sys

    # Reload to ensure fresh state
    if "kata_dash_model" in sys.modules:
        del sys.modules["kata_dash_model"]

    # Check the module's source does not import rich
    import inspect

    import kata_dash_model as m
    source = inspect.getsource(m)
    assert "import rich" not in source, "kata_dash_model must not import rich"


# ---------------------------------------------------------------------------
# BoardEvent dataclass
# ---------------------------------------------------------------------------


def test_board_event_fields():
    """BoardEvent must have utc, agent, type, task, msg fields."""
    from kata_dash_model import BoardEvent

    ev = BoardEvent(
        utc="2026-06-21T10:00:00Z",
        agent="DASH-model",
        type="CLAIM",
        task="T1",
        msg="starting task",
    )
    assert ev.utc == "2026-06-21T10:00:00Z"
    assert ev.agent == "DASH-model"
    assert ev.type == "CLAIM"
    assert ev.task == "T1"
    assert ev.msg == "starting task"


# ---------------------------------------------------------------------------
# parse_board
# ---------------------------------------------------------------------------

WELL_FORMED_BOARD = """\
2026-06-21T10:00:00Z | DASH-model | CLAIM | T1 | starting task
2026-06-21T10:01:00Z | DASH-render | CLAIM | T2 | starting render
2026-06-21T10:05:00Z | DASH-model | DONE | T1 | verify passed
"""


def test_parse_board_well_formed_returns_all_events():
    """parse_board must return one BoardEvent per well-formed line."""
    from kata_dash_model import parse_board

    events = parse_board(WELL_FORMED_BOARD)
    assert len(events) == 3


def test_parse_board_preserves_order():
    """parse_board must preserve line order (most recent last)."""
    from kata_dash_model import parse_board

    events = parse_board(WELL_FORMED_BOARD)
    assert events[0].agent == "DASH-model"
    assert events[0].type == "CLAIM"
    assert events[1].agent == "DASH-render"
    assert events[2].type == "DONE"


def test_parse_board_correct_fields():
    """parse_board must correctly split all 5 fields."""
    from kata_dash_model import parse_board

    events = parse_board(WELL_FORMED_BOARD)
    e = events[0]
    assert e.utc == "2026-06-21T10:00:00Z"
    assert e.agent == "DASH-model"
    assert e.type == "CLAIM"
    assert e.task == "T1"
    assert e.msg == "starting task"


def test_parse_board_skips_blank_lines():
    """parse_board must skip blank lines without error."""
    from kata_dash_model import parse_board

    text = "\n\n2026-06-21T10:00:00Z | DASH-model | CLAIM | T1 | msg\n\n"
    events = parse_board(text)
    assert len(events) == 1


def test_parse_board_skips_malformed_fewer_than_5_fields():
    """parse_board must skip lines with fewer than 5 pipe-delimited fields."""
    from kata_dash_model import parse_board

    malformed = """\
2026-06-21T10:00:00Z | DASH-model | CLAIM | T1 | valid line
this line has no pipes at all
2026-06-21T10:00:00Z | only | three | fields
2026-06-21T10:01:00Z | DASH-model | NOTE | T2 | another valid
"""
    events = parse_board(malformed)
    assert len(events) == 2
    assert events[0].msg == "valid line"
    assert events[1].msg == "another valid"


def test_parse_board_strips_whitespace_from_fields():
    """parse_board must strip leading/trailing whitespace from each field."""
    from kata_dash_model import parse_board

    text = "  2026-06-21T10:00:00Z  |  DASH-model  |  CLAIM  |  T1  |  the message  \n"
    events = parse_board(text)
    assert len(events) == 1
    e = events[0]
    assert e.utc == "2026-06-21T10:00:00Z"
    assert e.agent == "DASH-model"
    assert e.task == "T1"
    assert e.msg == "the message"


def test_parse_board_empty_string_returns_empty_list():
    """parse_board must return [] for an empty string."""
    from kata_dash_model import parse_board

    assert parse_board("") == []


def test_parse_board_msg_may_contain_pipes():
    """parse_board must handle msg field that contains pipe chars (split on first 4 pipes only)."""
    from kata_dash_model import parse_board

    # 5th field is the msg; if msg itself has pipes that's ok — we split by maxsplit=4
    text = "2026-06-21T10:00:00Z | DASH-model | NOTE | T1 | msg with | extra pipe\n"
    events = parse_board(text)
    assert len(events) == 1
    assert "extra pipe" in events[0].msg


# ---------------------------------------------------------------------------
# status_to_percent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status,expected", [
    ("assigned", 5),
    ("in-progress", 50),
    ("blocked", 50),
    ("done", 90),
    ("gated", 95),
    ("integrated", 100),
    ("unknown-status", 0),
    ("", 0),
    ("ASSIGNED", 0),  # case-sensitive; unknown → 0
])
def test_status_to_percent_exact_mapping(status, expected):
    """status_to_percent must return exact values per the frozen contract."""
    from kata_dash_model import status_to_percent

    assert status_to_percent(status) == expected, (
        f"status_to_percent({status!r}) expected {expected}, got {status_to_percent(status)}"
    )


# ---------------------------------------------------------------------------
# TaskRow dataclass
# ---------------------------------------------------------------------------


def test_task_row_fields():
    """TaskRow must have id, label, status, percent, active, blocked, done fields."""
    from kata_dash_model import TaskRow

    row = TaskRow(
        id="T1",
        label="T1",
        status="in-progress",
        percent=50,
        active=True,
        blocked=False,
        done=False,
    )
    assert row.id == "T1"
    assert row.label == "T1"
    assert row.status == "in-progress"
    assert row.percent == 50
    assert row.active is True
    assert row.blocked is False
    assert row.done is False


# ---------------------------------------------------------------------------
# ViewModel dataclass
# ---------------------------------------------------------------------------


def test_view_model_fields():
    """ViewModel must have all fields defined in the frozen contract."""
    from kata_dash_model import TaskRow, ViewModel

    vm = ViewModel(
        spec="test-spec",
        wave="1/?",
        phase="EXECUTE",
        gate="tests: 112/0/0",
        tasks=[],
        driftEscalations=(0, 0),
        events=[],
        waiting=False,
        updatedUtc="2026-06-21T10:00:00Z",
    )
    assert vm.spec == "test-spec"
    assert vm.wave == "1/?"
    assert vm.phase == "EXECUTE"
    assert vm.gate == "tests: 112/0/0"
    assert vm.tasks == []
    assert vm.driftEscalations == (0, 0)
    assert vm.events == []
    assert vm.waiting is False
    assert vm.updatedUtc == "2026-06-21T10:00:00Z"


# ---------------------------------------------------------------------------
# build_view_model — fixture state dict
# ---------------------------------------------------------------------------

FIXTURE_STATE = {
    "plan": ".planning/phases/phase4/plan.md",
    "forkPoint": "abc123",
    "integrationBranch": "dash/integration",
    "wavesDone": ["wave1"],
    "tasks": {
        "DASH-model": "done",
        "DASH-render": "in-progress",
        "DASH-blocked": "blocked",
        "DASH-integrated": "integrated",
    },
    "gate": {"tests": "112/0/0", "build": "ok", "security": "0"},
    "driftLedger": {"unauthorizedDeviations": 2, "escalations": 1, "interventions": 0},
    "updatedUtc": "2026-06-21T12:00:00Z",
}

FIXTURE_BOARD = """\
2026-06-21T10:00:00Z | DASH-model | CLAIM | DASH-model | starting model task
2026-06-21T10:01:00Z | DASH-render | CLAIM | DASH-render | starting render task
2026-06-21T10:05:00Z | DASH-model | DONE | DASH-model | verify passed
2026-06-21T10:06:00Z | orchestrator | DECISION | DASH-blocked | unblocked
2026-06-21T10:07:00Z | DASH-render | NOTE | DASH-render | progress note
2026-06-21T10:08:00Z | DASH-blocked | BLOCK | DASH-blocked | dependency missing
2026-06-21T10:09:00Z | DASH-integrated | DONE | DASH-integrated | done and integrated
"""


def test_build_view_model_returns_view_model():
    """build_view_model must return a ViewModel instance."""
    from kata_dash_model import ViewModel, build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    assert isinstance(vm, ViewModel)


def test_build_view_model_tasks_count():
    """build_view_model must produce one TaskRow per task in state['tasks']."""
    from kata_dash_model import build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    assert len(vm.tasks) == 4


def test_build_view_model_task_ids():
    """build_view_model tasks must have correct ids from state keys."""
    from kata_dash_model import build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    ids = {t.id for t in vm.tasks}
    assert ids == {"DASH-model", "DASH-render", "DASH-blocked", "DASH-integrated"}


def test_build_view_model_task_label_equals_id_v1():
    """In v1, task label must equal task id."""
    from kata_dash_model import build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    for t in vm.tasks:
        assert t.label == t.id


def test_build_view_model_task_percent_correct():
    """build_view_model must map status to percent correctly for each task."""
    from kata_dash_model import build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    by_id = {t.id: t for t in vm.tasks}

    assert by_id["DASH-model"].percent == 90       # done → 90
    assert by_id["DASH-render"].percent == 50      # in-progress → 50
    assert by_id["DASH-blocked"].percent == 50     # blocked → 50
    assert by_id["DASH-integrated"].percent == 100 # integrated → 100


def test_build_view_model_task_active_flag():
    """active must be True only for in-progress tasks."""
    from kata_dash_model import build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    by_id = {t.id: t for t in vm.tasks}

    assert by_id["DASH-render"].active is True
    assert by_id["DASH-model"].active is False
    assert by_id["DASH-blocked"].active is False
    assert by_id["DASH-integrated"].active is False


def test_build_view_model_task_blocked_flag():
    """blocked must be True only for blocked tasks."""
    from kata_dash_model import build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    by_id = {t.id: t for t in vm.tasks}

    assert by_id["DASH-blocked"].blocked is True
    assert by_id["DASH-model"].blocked is False
    assert by_id["DASH-render"].blocked is False
    assert by_id["DASH-integrated"].blocked is False


def test_build_view_model_task_done_flag():
    """done must be True for tasks in done/gated/integrated statuses."""
    from kata_dash_model import build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    by_id = {t.id: t for t in vm.tasks}

    assert by_id["DASH-model"].done is True        # done → done
    assert by_id["DASH-integrated"].done is True   # integrated → done
    assert by_id["DASH-render"].done is False
    assert by_id["DASH-blocked"].done is False


def test_build_view_model_gate_stringified():
    """gate must be a non-None string derived from state['gate']."""
    from kata_dash_model import build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    assert vm.gate is not None
    assert isinstance(vm.gate, str)
    # Must include the tests value
    assert "112/0/0" in vm.gate


def test_build_view_model_drift_escalations():
    """driftEscalations must be (unauthorizedDeviations, escalations) from driftLedger."""
    from kata_dash_model import build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    assert vm.driftEscalations == (2, 1)


def test_build_view_model_updated_utc():
    """updatedUtc must come from state['updatedUtc']."""
    from kata_dash_model import build_view_model

    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    assert vm.updatedUtc == "2026-06-21T12:00:00Z"


# ---------------------------------------------------------------------------
# Phase derivation
# ---------------------------------------------------------------------------


def test_phase_execute_when_tasks_present_not_all_integrated():
    """Phase must be EXECUTE when tasks exist and not all are integrated."""
    from kata_dash_model import build_view_model

    # FIXTURE_STATE has mixed tasks (in-progress, done, blocked, integrated) — not all integrated
    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    assert vm.phase == "EXECUTE"


def test_phase_evaluate_when_all_integrated_and_gate_present():
    """Phase must be EVALUATE when all tasks are integrated and gate is present."""
    from kata_dash_model import build_view_model

    state = {
        "wavesDone": ["wave1"],
        "tasks": {"T1": "integrated", "T2": "integrated"},
        "gate": {"tests": "112/0/0"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T12:00:00Z",
    }
    vm = build_view_model("", state)
    assert vm.phase == "EVALUATE"


def test_phase_execute_default_when_no_tasks():
    """Phase must default to EXECUTE when state has no tasks."""
    from kata_dash_model import build_view_model

    state = {
        "wavesDone": [],
        "tasks": {},
        "gate": None,
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T12:00:00Z",
    }
    vm = build_view_model("", state)
    assert vm.phase == "EXECUTE"


def test_phase_execute_when_all_integrated_but_no_gate():
    """Phase must be EXECUTE (not EVALUATE) when all integrated but gate is absent/None."""
    from kata_dash_model import build_view_model

    state = {
        "wavesDone": ["wave1"],
        "tasks": {"T1": "integrated"},
        "gate": None,
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T12:00:00Z",
    }
    vm = build_view_model("", state)
    assert vm.phase == "EXECUTE"


# ---------------------------------------------------------------------------
# Wave field
# ---------------------------------------------------------------------------


def test_wave_reflects_waves_done_count():
    """wave must reflect the number of completed waves from wavesDone."""
    from kata_dash_model import build_view_model

    state = {**FIXTURE_STATE, "wavesDone": ["wave1", "wave2"]}
    vm = build_view_model("", state)
    # wave must contain "2" (the count)
    assert "2" in vm.wave


def test_wave_none_when_waves_done_absent():
    """wave must be None or a reasonable fallback when wavesDone is absent."""
    from kata_dash_model import build_view_model

    state = {k: v for k, v in FIXTURE_STATE.items() if k != "wavesDone"}
    vm = build_view_model("", state)
    # Acceptable: None or "0/?" or similar — just must not crash
    # The spec says wave:str|None so None is fine
    assert vm.wave is None or isinstance(vm.wave, str)


# ---------------------------------------------------------------------------
# Events truncation
# ---------------------------------------------------------------------------


def test_events_are_last_6_board_lines():
    """events must contain at most the last 6 formatted board lines."""
    from kata_dash_model import build_view_model

    # 7 lines in FIXTURE_BOARD
    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    assert len(vm.events) == 6


def test_events_formatted_as_agent_type_task_msg():
    """events must be formatted as 'agent TYPE task: msg'."""
    from kata_dash_model import build_view_model

    board = "2026-06-21T10:00:00Z | my-agent | CLAIM | T1 | hello world\n"
    vm = build_view_model(board, FIXTURE_STATE)
    # Find the event matching our line
    matching = [e for e in vm.events if "my-agent" in e]
    assert len(matching) == 1
    ev = matching[0]
    assert "my-agent" in ev
    assert "CLAIM" in ev
    assert "T1" in ev
    assert "hello world" in ev


def test_events_most_recent_last():
    """events list must be ordered most-recent-last (chronological)."""
    from kata_dash_model import build_view_model

    # FIXTURE_BOARD ends with DASH-integrated DONE
    vm = build_view_model(FIXTURE_BOARD, FIXTURE_STATE)
    # Last event must mention DASH-integrated or DONE
    last = vm.events[-1]
    assert "DASH-integrated" in last or "DONE" in last


def test_events_fewer_than_6_when_board_has_fewer():
    """events must have fewer entries when board has fewer than 6 lines."""
    from kata_dash_model import build_view_model

    board = "2026-06-21T10:00:00Z | a | CLAIM | T1 | msg1\n2026-06-21T10:01:00Z | b | DONE | T2 | msg2\n"
    vm = build_view_model(board, FIXTURE_STATE)
    assert len(vm.events) == 2


# ---------------------------------------------------------------------------
# waiting path
# ---------------------------------------------------------------------------


def test_waiting_true_when_state_none_and_board_empty():
    """waiting must be True when state is None AND board is empty."""
    from kata_dash_model import build_view_model

    vm = build_view_model("", None)
    assert vm.waiting is True


def test_waiting_false_when_state_present():
    """waiting must be False when state is provided."""
    from kata_dash_model import build_view_model

    vm = build_view_model("", FIXTURE_STATE)
    assert vm.waiting is False


def test_waiting_false_when_board_has_events_but_no_state():
    """waiting must be False when board has events even if state is None."""
    from kata_dash_model import build_view_model

    board = "2026-06-21T10:00:00Z | agent | CLAIM | T1 | starting\n"
    vm = build_view_model(board, None)
    assert vm.waiting is False


def test_waiting_view_model_has_sensible_defaults_when_no_data():
    """When waiting=True, ViewModel must not crash and have safe field values."""
    from kata_dash_model import build_view_model

    vm = build_view_model("", None)
    assert vm.tasks == []
    assert vm.events == []
    assert vm.driftEscalations == (0, 0)
    assert vm.phase == "EXECUTE"  # default


# ---------------------------------------------------------------------------
# build_view_model with no drift ledger (missing keys)
# ---------------------------------------------------------------------------


def test_build_view_model_missing_drift_ledger_defaults_to_zeros():
    """driftEscalations must default to (0, 0) when driftLedger is absent."""
    from kata_dash_model import build_view_model

    state = {
        "wavesDone": [],
        "tasks": {"T1": "in-progress"},
        "gate": None,
        "updatedUtc": "2026-06-21T12:00:00Z",
        # No driftLedger key
    }
    vm = build_view_model("", state)
    assert vm.driftEscalations == (0, 0)


def test_build_view_model_gate_none_when_state_gate_absent():
    """gate must be None when state has no 'gate' key or gate is None."""
    from kata_dash_model import build_view_model

    state = {
        "wavesDone": [],
        "tasks": {},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T12:00:00Z",
    }
    vm = build_view_model("", state)
    assert vm.gate is None


def test_build_view_model_gated_tasks_are_done():
    """Tasks with status 'gated' must have done=True."""
    from kata_dash_model import build_view_model

    state = {
        "wavesDone": [],
        "tasks": {"T1": "gated"},
        "gate": None,
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T12:00:00Z",
    }
    vm = build_view_model("", state)
    assert vm.tasks[0].done is True
    assert vm.tasks[0].percent == 95


# ---------------------------------------------------------------------------
# S1b: PROGRESS heartbeat parsing + smooth-bar mapping
# ---------------------------------------------------------------------------

PROGRESS_BOARD = """\
2026-06-21T10:00:00Z | worker-A | CLAIM | T1 | starting
2026-06-21T10:01:00Z | worker-A | PROGRESS | T1 | 1/5 reading spec
2026-06-21T10:02:00Z | worker-A | PROGRESS | T1 | 2/5 writing code
2026-06-21T10:03:00Z | worker-A | PROGRESS | T1 | 3/5 writing tests
2026-06-21T10:04:00Z | worker-B | CLAIM | T2 | starting T2
2026-06-21T10:05:00Z | worker-B | PROGRESS | T2 | 2/4 half done
"""


def test_parse_board_includes_progress_lines():
    """parse_board must parse PROGRESS type lines as BoardEvents."""
    from kata_dash_model import parse_board

    events = parse_board(PROGRESS_BOARD)
    progress_events = [e for e in events if e.type == "PROGRESS"]
    assert len(progress_events) == 4


def test_parse_board_progress_event_fields():
    """PROGRESS event must have correct fields including msg with step/n label."""
    from kata_dash_model import parse_board

    events = parse_board(PROGRESS_BOARD)
    progress_events = [e for e in events if e.type == "PROGRESS" and e.task == "T1"]
    # Last PROGRESS for T1 is 3/5 writing tests
    last = progress_events[-1]
    assert last.agent == "worker-A"
    assert last.type == "PROGRESS"
    assert last.task == "T1"
    assert last.msg == "3/5 writing tests"


def test_task_row_has_progress_label_field():
    """TaskRow must have a progressLabel field."""
    from kata_dash_model import TaskRow

    row = TaskRow(
        id="T1",
        label="T1",
        status="in-progress",
        percent=60,
        active=True,
        blocked=False,
        done=False,
        progressLabel="writing tests",
    )
    assert row.progressLabel == "writing tests"


def test_task_row_progress_label_empty_by_default():
    """TaskRow.progressLabel must default to empty string."""
    from kata_dash_model import TaskRow

    row = TaskRow(
        id="T1",
        label="T1",
        status="in-progress",
        percent=50,
        active=True,
        blocked=False,
        done=False,
    )
    assert row.progressLabel == ""


def test_heartbeat_3_of_5_yields_60_percent():
    """An in-progress task with latest PROGRESS 3/5 must get percent=60."""
    from kata_dash_model import build_view_model

    board = """\
2026-06-21T10:00:00Z | worker-A | CLAIM | T1 | starting
2026-06-21T10:01:00Z | worker-A | PROGRESS | T1 | 3/5 writing tests
"""
    state = {
        "tasks": {"T1": "in-progress"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T10:00:00Z",
    }
    vm = build_view_model(board, state)
    t1 = vm.tasks[0]
    assert t1.percent == 60


def test_heartbeat_percent_uses_latest_progress_event():
    """When multiple PROGRESS lines exist, the last one wins."""
    from kata_dash_model import build_view_model

    board = """\
2026-06-21T10:00:00Z | worker-A | CLAIM | T1 | starting
2026-06-21T10:01:00Z | worker-A | PROGRESS | T1 | 1/5 reading spec
2026-06-21T10:02:00Z | worker-A | PROGRESS | T1 | 2/5 writing code
2026-06-21T10:03:00Z | worker-A | PROGRESS | T1 | 3/5 writing tests
"""
    state = {
        "tasks": {"T1": "in-progress"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T10:00:00Z",
    }
    vm = build_view_model(board, state)
    t1 = vm.tasks[0]
    assert t1.percent == 60  # 3/5 * 100 = 60


def test_heartbeat_progress_label_set_from_latest():
    """progressLabel must come from the label part of the latest PROGRESS msg."""
    from kata_dash_model import build_view_model

    board = """\
2026-06-21T10:00:00Z | worker-A | CLAIM | T1 | starting
2026-06-21T10:01:00Z | worker-A | PROGRESS | T1 | 1/5 reading spec
2026-06-21T10:02:00Z | worker-A | PROGRESS | T1 | 3/5 writing tests
"""
    state = {
        "tasks": {"T1": "in-progress"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T10:00:00Z",
    }
    vm = build_view_model(board, state)
    t1 = vm.tasks[0]
    assert t1.progressLabel == "writing tests"


def test_no_heartbeat_falls_back_to_stepped_percent():
    """Without a PROGRESS heartbeat, in-progress uses status_to_percent (50)."""
    from kata_dash_model import build_view_model

    board = "2026-06-21T10:00:00Z | worker-A | CLAIM | T1 | starting\n"
    state = {
        "tasks": {"T1": "in-progress"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T10:00:00Z",
    }
    vm = build_view_model(board, state)
    t1 = vm.tasks[0]
    assert t1.percent == 50  # stepped fallback


def test_no_heartbeat_progress_label_is_empty():
    """Without a PROGRESS heartbeat, progressLabel must be empty string."""
    from kata_dash_model import build_view_model

    board = "2026-06-21T10:00:00Z | worker-A | CLAIM | T1 | starting\n"
    state = {
        "tasks": {"T1": "in-progress"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T10:00:00Z",
    }
    vm = build_view_model(board, state)
    t1 = vm.tasks[0]
    assert t1.progressLabel == ""


def test_heartbeat_clamp_over_100():
    """Heartbeat percent must be clamped to 100 even if step > n (defensive)."""
    from kata_dash_model import build_view_model

    board = "2026-06-21T10:00:00Z | worker-A | PROGRESS | T1 | 6/5 over limit\n"
    state = {
        "tasks": {"T1": "in-progress"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T10:00:00Z",
    }
    vm = build_view_model(board, state)
    t1 = vm.tasks[0]
    assert t1.percent == 100


def test_heartbeat_clamp_below_0():
    """Heartbeat percent must be clamped to 0 if round gives negative (e.g. 0/5)."""
    from kata_dash_model import build_view_model

    board = "2026-06-21T10:00:00Z | worker-A | PROGRESS | T1 | 0/5 just started\n"
    state = {
        "tasks": {"T1": "in-progress"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T10:00:00Z",
    }
    vm = build_view_model(board, state)
    t1 = vm.tasks[0]
    assert t1.percent == 0


def test_heartbeat_only_applies_to_in_progress_tasks():
    """PROGRESS heartbeats must NOT override percent for done/gated/assigned tasks."""
    from kata_dash_model import build_view_model

    board = """\
2026-06-21T10:00:00Z | worker-A | PROGRESS | T1 | 3/5 late progress
2026-06-21T10:01:00Z | worker-A | DONE | T1 | verify passed
"""
    state = {
        "tasks": {"T1": "done"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T10:00:00Z",
    }
    vm = build_view_model(board, state)
    t1 = vm.tasks[0]
    assert t1.percent == 90  # done → stepped, not heartbeat


def test_heartbeat_per_task_isolated():
    """Each task uses its own latest PROGRESS, not another task's."""
    from kata_dash_model import build_view_model

    board = """\
2026-06-21T10:00:00Z | worker-A | PROGRESS | T1 | 3/5 writing tests
2026-06-21T10:01:00Z | worker-B | PROGRESS | T2 | 2/4 half done
"""
    state = {
        "tasks": {"T1": "in-progress", "T2": "in-progress"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T10:00:00Z",
    }
    vm = build_view_model(board, state)
    by_id = {t.id: t for t in vm.tasks}
    assert by_id["T1"].percent == 60   # 3/5 * 100
    assert by_id["T2"].percent == 50   # 2/4 * 100


def test_heartbeat_malformed_msg_falls_back_to_stepped():
    """A PROGRESS line with non-parseable msg must fall back to stepped percent."""
    from kata_dash_model import build_view_model

    board = "2026-06-21T10:00:00Z | worker-A | PROGRESS | T1 | not a fraction\n"
    state = {
        "tasks": {"T1": "in-progress"},
        "driftLedger": {"unauthorizedDeviations": 0, "escalations": 0},
        "updatedUtc": "2026-06-21T10:00:00Z",
    }
    vm = build_view_model(board, state)
    t1 = vm.tasks[0]
    assert t1.percent == 50  # fallback to stepped
