"""kata_board.py — single emitter for KataHarness coordination files.

Provides pure file-I/O helpers (stdlib only) for writing the append-only
coordination board and the single-writer run state.  No imports outside the
standard library; no sub-process calls; no side-effects at import time.

Single-writer rule (L3 — LESSONS-LEARNED):
  WORKERS call only:   append_event / append_progress
  ORCHESTRATOR calls:  write_state  / update_task

Workers MUST NOT call write_state or update_task; the orchestrator MUST NOT
bypass this module to write board.md directly.  This separation is the fix for
the shared-state corruption documented in L3.

Security note (from PLAN S1a threat model): kata_dir is operator-supplied; it
is sanitised by _safe_path before any filesystem sink is reached (CWE-23 guard).
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path guard
# ---------------------------------------------------------------------------


def _safe_path(raw: str | Path) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied path, then resolve.

    Blocks any ``..`` segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree, while still allowing the
    absolute and nested-relative paths the maintainer legitimately targets.
    Sanitizes the tainted input at the boundary before any filesystem sink.

    Mirrors the identical guard in gate_emit._safe_path (keep them in sync).

    Single-writer rule: WORKERS call append_event/append_progress only.
    ONLY the orchestrator calls write_state/update_task.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"kata_board: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


# ---------------------------------------------------------------------------
# Board helpers (worker-safe)
# ---------------------------------------------------------------------------


def append_event(
    kata_dir: str | Path,
    agent: str,
    type: str,  # noqa: A002  (shadowing built-in intentional — matches protocol)
    task: str,
    msg: str,
) -> None:
    """Append one coordination event line to <kata_dir>/board.md.

    Creates board.md if it does not exist.  Strictly append-only: existing
    lines are never modified or deleted (audit-trail invariant).

    Line format (protocol/board.md):
        <ISO-8601-UTC> | <agent> | <TYPE> | <task> | <msg>

    Single-writer rule: WORKERS call this function (and append_progress).
    ONLY the orchestrator calls write_state/update_task.

    Parameters
    ----------
    kata_dir:
        Root directory of the running kata (.kata/).  Must not contain '..'.
    agent:
        Agent identifier string (e.g. ``"S1a-worker"``).
    type:
        Board TYPE token (e.g. ``"CLAIM"``, ``"DONE"``, ``"PROGRESS"``).
    task:
        Task identifier (e.g. ``"T1"``).
    msg:
        One-line human-readable message.  Must not contain a bare newline.
    """
    kata_dir = _safe_path(kata_dir)
    kata_dir.mkdir(parents=True, exist_ok=True)  # first event of a run creates .kata/
    utc_now = datetime.now(UTC).isoformat()
    line = f"{utc_now} | {agent} | {type} | {task} | {msg}\n"

    board_path = kata_dir / "board.md"
    with board_path.open("a", encoding="utf-8") as fh:
        fh.write(line)


def append_progress(
    kata_dir: str | Path,
    agent: str,
    task: str,
    step: int,
    n: int,
    label: str,
) -> None:
    """Append a PROGRESS heartbeat line to <kata_dir>/board.md.

    Convenience wrapper around append_event with type=``"PROGRESS"`` and
    msg formatted as ``"<step>/<n> <label>"`` (e.g. ``"3/5 writing tests"``).

    PROGRESS lines are the MANDATED worker liveness heartbeat (Milestone-1 F3;
    see protocol/board.md) — read by the dashboard and the orchestrator's
    liveness monitor, excluded from coordination and concurrency evidence.
    They are IGNORED by coordination logic (DECISION/BLOCK/ESCALATE invariants
    are unchanged).

    Single-writer rule: WORKERS call this function (and append_event).
    ONLY the orchestrator calls write_state/update_task.

    Parameters
    ----------
    kata_dir:
        Root directory of the running kata (.kata/).  Must not contain '..'.
    agent:
        Agent identifier string.
    task:
        Task identifier (e.g. ``"T1"``).
    step:
        Current step number (1-based, or 0-based — caller's choice).
    n:
        Total number of steps.
    label:
        Short human-readable label for the current step (e.g. ``"writing tests"``).
    """
    msg = f"{step}/{n} {label}"
    append_event(kata_dir, agent, "PROGRESS", task, msg)


# ---------------------------------------------------------------------------
# State helpers (orchestrator-only)
# ---------------------------------------------------------------------------


def write_state(kata_dir: str | Path, state: dict) -> None:
    """Atomically write state.json to <kata_dir>/state.json.

    Uses write-to-temp + os.replace so a concurrent reader never observes a
    half-written file (POSIX atomic rename; also atomic on Windows via
    os.replace which maps to MoveFileExW with MOVEFILE_REPLACE_EXISTING).

    Single-writer rule: ONLY the orchestrator calls this function.
    WORKERS must NEVER call write_state or update_task — they append to board.md.

    Parameters
    ----------
    kata_dir:
        Root directory of the running kata (.kata/).  Must not contain '..'.
    state:
        Full state dict to persist.  Must be JSON-serialisable.
    """
    kata_dir = _safe_path(kata_dir)
    kata_dir.mkdir(parents=True, exist_ok=True)  # first write of a run creates .kata/
    state_path = kata_dir / "state.json"

    # Write to a sibling temp file, then atomically replace.
    fd, tmp_path = tempfile.mkstemp(dir=kata_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
        os.replace(tmp_path, state_path)
    except Exception:
        # Clean up the temp file on failure so we never leave orphans.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def update_task(
    kata_dir: str | Path,
    state: dict,
    task: str,
    status: str,
) -> dict:
    """Set state["tasks"][task] = status, refresh updatedUtc, and write_state.

    Mutates *state* in place, writes atomically, and returns the mutated dict.

    Single-writer rule: ONLY the orchestrator calls this function.
    WORKERS must NEVER call write_state or update_task — they append to board.md.

    Parameters
    ----------
    kata_dir:
        Root directory of the running kata (.kata/).  Must not contain '..'.
    state:
        Current state dict (will be mutated in place).
    task:
        Task identifier key within ``state["tasks"]``.
    status:
        New status string (e.g. ``"in-progress"``, ``"done"``, ``"gated"``).

    Returns
    -------
    dict
        The mutated state dict (same object as the *state* parameter).
    """
    state.setdefault("tasks", {})[task] = status
    state["updatedUtc"] = datetime.now(UTC).isoformat()
    write_state(kata_dir, state)
    return state
