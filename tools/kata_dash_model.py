"""kata_dash_model.py — pure board+state parser -> dashboard ViewModel.

No I/O beyond accepting strings/dicts.
No 'rich' import (this is the pure layer; rendering lives in kata_dash.py).

Public API:
    BoardEvent          dataclass: utc, agent, type, task, msg
    TaskRow             dataclass: id, label, status, percent, active, blocked, done
    ViewModel           dataclass: spec, wave, phase, gate, tasks, driftEscalations,
                                   events, waiting, updatedUtc
    parse_board(text)           -> list[BoardEvent]
    status_to_percent(status)   -> int
    build_view_model(board_text, state, spec=None) -> ViewModel

Wave field convention:
    wave = str(len(wavesDone)) + "/?" when wavesDone is present and non-empty,
           "0/?" when wavesDone is present but empty,
           None when wavesDone key is absent from state.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class BoardEvent:
    """A single parsed line from .kata/board.md."""

    utc: str
    agent: str
    type: str
    task: str
    msg: str


@dataclass
class TaskRow:
    """Render-ready row derived from a single state["tasks"] entry."""

    id: str
    label: str
    status: str
    percent: int
    active: bool
    blocked: bool
    done: bool
    progressLabel: str = field(default="")


@dataclass
class ViewModel:
    """Fully render-ready snapshot consumed by the rich render layer.

    Fields per the frozen contract in PLAN.md § "Frozen contract — the ViewModel".
    """

    spec: str | None
    wave: str | None
    phase: str                        # one of the 6 ribbon phases
    gate: str | None
    tasks: list[TaskRow]
    driftEscalations: tuple[int, int]
    events: list[str]                 # last N formatted board lines, most-recent-last
    waiting: bool                     # True iff no live run data
    updatedUtc: str | None


# ---------------------------------------------------------------------------
# parse_board
# ---------------------------------------------------------------------------

_MAX_EVENTS = 6  # number of recent board events to surface in the ViewModel


def parse_board(text: str) -> list[BoardEvent]:
    """Parse .kata/board.md text into an ordered list of BoardEvent.

    Format per protocol/board.md:
        <ISO-8601-UTC> | <agent-id> | <TYPE> | <task-id> | <one-line message>

    Tolerant: blank lines and lines with fewer than 5 pipe-delimited fields are
    silently skipped.  Order is preserved (top-of-file first → most recent last).
    The msg field is everything after the 4th pipe, so it may itself contain pipes.
    """
    events: list[BoardEvent] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("|", maxsplit=4)
        if len(parts) < 5:
            continue
        utc, agent, typ, task, msg = (p.strip() for p in parts)
        events.append(BoardEvent(utc=utc, agent=agent, type=typ, task=task, msg=msg))
    return events


# ---------------------------------------------------------------------------
# status_to_percent
# ---------------------------------------------------------------------------

_STATUS_PERCENT: dict[str, int] = {
    "assigned": 5,
    "in-progress": 50,
    "blocked": 50,
    "done": 90,
    "gated": 95,
    "integrated": 100,
}

_DONE_STATUSES: frozenset[str] = frozenset({"done", "gated", "integrated"})


def status_to_percent(status: str) -> int:
    """Map a task status string to a stepped progress percent.

    Exact mapping (frozen contract):
        assigned   →   5
        in-progress → 50
        blocked    →  50
        done       →  90
        gated      →  95
        integrated → 100
        <unknown>  →   0
    """
    return _STATUS_PERCENT.get(status, 0)


# ---------------------------------------------------------------------------
# PROGRESS heartbeat helpers
# ---------------------------------------------------------------------------


def _parse_progress_msg(msg: str) -> tuple[int, int, str] | None:
    """Parse a PROGRESS msg in the form '<step>/<n> <label>'.

    Returns (step, n, label) on success, or None if the format doesn't match.
    The label may be empty if nothing follows the fraction.
    """
    # Expected format: "3/5 writing tests" or "3/5" (no label)
    parts = msg.split(" ", maxsplit=1)
    fraction = parts[0]
    label = parts[1].strip() if len(parts) > 1 else ""
    if "/" not in fraction:
        return None
    step_str, n_str = fraction.split("/", maxsplit=1)
    try:
        step = int(step_str.strip())
        n = int(n_str.strip())
    except ValueError:
        return None
    if n <= 0:
        return None
    return (step, n, label)


def _latest_progress_per_task(events: list[BoardEvent]) -> dict[str, tuple[int, int, str]]:
    """Scan board events and return the latest PROGRESS heartbeat per task.

    Returns a mapping of task_id -> (step, n, label) for each task that has at
    least one valid PROGRESS event.  Only the LAST valid PROGRESS per task is kept.
    """
    result: dict[str, tuple[int, int, str]] = {}
    for ev in events:
        if ev.type != "PROGRESS":
            continue
        parsed = _parse_progress_msg(ev.msg)
        if parsed is None:
            continue
        result[ev.task] = parsed  # overwrite with the most recent valid one
    return result


# ---------------------------------------------------------------------------
# build_view_model
# ---------------------------------------------------------------------------


def _format_event(ev: BoardEvent) -> str:
    """Format a BoardEvent as 'agent TYPE task: msg'."""
    return f"{ev.agent} {ev.type} {ev.task}: {ev.msg}"


def _derive_gate_str(gate_raw: object) -> str | None:
    """Stringify the gate value compactly, or return None if absent/None."""
    if gate_raw is None:
        return None
    if isinstance(gate_raw, dict):
        # Compact: "tests: 112/0/0 · build: ok · security: 0"
        parts = [f"{k}: {v}" for k, v in gate_raw.items()]
        return " · ".join(parts)
    return str(gate_raw)


def _derive_wave(waves_done: list | None) -> str | None:
    """Derive the wave display string.

    Returns:
        "N/?" where N = len(wavesDone), or None if wavesDone key was absent.
    """
    if waves_done is None:
        return None
    return f"{len(waves_done)}/?"


def _derive_phase(tasks: dict[str, str], gate_raw: object) -> str:
    """Derive the current loop phase from task statuses and gate.

    Rules (per PLAN locked design):
        - No tasks present                         → "EXECUTE" (default)
        - Tasks present, not all integrated        → "EXECUTE"
        - All tasks integrated AND gate present    → "EVALUATE"
        - All tasks integrated but no gate         → "EXECUTE"
    """
    if not tasks:
        return "EXECUTE"
    all_integrated = all(s == "integrated" for s in tasks.values())
    if all_integrated and gate_raw:
        return "EVALUATE"
    return "EXECUTE"


def build_view_model(
    board_text: str,
    state: dict | None,
    spec: str | None = None,
) -> ViewModel:
    """Build a render-ready ViewModel from raw board text and state dict.

    Args:
        board_text: full contents of .kata/board.md (may be empty string).
        state:      parsed .kata/state.json as a dict, or None if absent.
        spec:       optional spec path/label override (falls back to state["plan"]).

    Returns:
        ViewModel with all fields populated.

    waiting semantics:
        True iff state is None AND parse_board(board_text) is empty —
        i.e. there is genuinely no live run data.
    """
    events_parsed = parse_board(board_text)

    # ----- waiting check ---------------------------------------------------
    waiting = state is None and len(events_parsed) == 0

    # ----- defaults when no state ------------------------------------------
    if state is None:
        formatted_events = [_format_event(e) for e in events_parsed[-_MAX_EVENTS:]]
        return ViewModel(
            spec=spec,
            wave=None,
            phase="EXECUTE",
            gate=None,
            tasks=[],
            driftEscalations=(0, 0),
            events=formatted_events,
            waiting=waiting,
            updatedUtc=None,
        )

    # ----- tasks -----------------------------------------------------------
    tasks_raw: dict[str, str] = state.get("tasks") or {}

    # Build per-task heartbeat map from board events
    latest_progress = _latest_progress_per_task(events_parsed)

    task_rows: list[TaskRow] = []
    for task_id, status in tasks_raw.items():
        # Smooth-bar: in-progress + valid PROGRESS heartbeat → compute percent
        # Other statuses always use stepped value (frozen contract)
        heartbeat = latest_progress.get(task_id)
        if status == "in-progress" and heartbeat is not None:
            step, n, label = heartbeat
            pct = max(0, min(100, round(step / n * 100)))
            progress_label = label
        else:
            pct = status_to_percent(status)
            progress_label = ""

        task_rows.append(TaskRow(
            id=task_id,
            label=task_id,           # v1: label = id
            status=status,
            percent=pct,
            active=(status == "in-progress"),
            blocked=(status == "blocked"),
            done=(status in _DONE_STATUSES),
            progressLabel=progress_label,
        ))

    # ----- gate ------------------------------------------------------------
    gate_raw = state.get("gate")
    gate_str = _derive_gate_str(gate_raw)

    # ----- drift + escalations --------------------------------------------
    drift_ledger: dict = state.get("driftLedger") or {}
    drift_escalations: tuple[int, int] = (
        drift_ledger.get("unauthorizedDeviations", 0),
        drift_ledger.get("escalations", 0),
    )

    # ----- wave ------------------------------------------------------------
    waves_done_raw = state.get("wavesDone")   # None if key absent, [] if empty
    wave = _derive_wave(waves_done_raw)

    # ----- phase -----------------------------------------------------------
    phase = _derive_phase(tasks_raw, gate_raw)

    # ----- events (last _MAX_EVENTS, most-recent-last) --------------------
    formatted_events = [_format_event(e) for e in events_parsed[-_MAX_EVENTS:]]

    # ----- spec ------------------------------------------------------------
    resolved_spec = spec or state.get("plan")

    return ViewModel(
        spec=resolved_spec,
        wave=wave,
        phase=phase,
        gate=gate_str,
        tasks=task_rows,
        driftEscalations=drift_escalations,
        events=formatted_events,
        waiting=False,
        updatedUtc=state.get("updatedUtc"),
    )
