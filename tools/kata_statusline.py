"""kata_statusline.py — agnostic one-line statusline projection for KataHarness.

Pure core: stdlib only, no 'rich', no tool-specific dependencies.
Reuses kata_dash_model.build_view_model (lazy import) for the ViewModel.

Public API:
    render_statusline(view_model) -> str
        Project a ViewModel to the FROZEN one-line format (PLAN-s1.5.md § Task S1.5a).
    build_statusline(kata_dir) -> str
        Read <kata_dir>/board.md + state.json, build ViewModel, return render_statusline().
    statusline_from_event(stdin_text: str) -> str
        Parse the Claude statusLine stdin JSON, find cwd, call build_statusline().
        Fail-soft: ANY exception -> return "".
    write_bridge(temp_dir, payload_dict) -> Path | None
        Write the kata superset context-usage bridge file (CA-L1/CA-L2) from the
        SAME statusLine stdin JSON. Fail-soft observability write (never raises).

Security: build_statusline() applies a _safe_path() .. guard (CWE-23, mirrors kata_dash).
write_bridge() applies a session_id filename-safety guard (CWE-22/CWE-23).
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Union


# ---------------------------------------------------------------------------
# Internal path-traversal guard (CWE-23 — mirror kata_dash._safe_path)
# ---------------------------------------------------------------------------


def _safe_path(raw: Union[str, Path]) -> Path:
    """Reject any path containing '..' segments, then resolve.

    Consistent with kata_dash._safe_path and gate_emit._safe_path.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"kata_statusline: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


# ---------------------------------------------------------------------------
# Internal 8-wide block-char bar helper (do NOT import kata_dash or rich)
# ---------------------------------------------------------------------------


def _bar8(pct: int) -> str:
    """Return an 8-wide block-char progress bar.

    filled = clamp(round(pct / 100 * 8), 0, 8)
    Filled: ▰   Empty: ▱
    """
    filled = max(0, min(8, round(pct / 100 * 8)))
    return "▰" * filled + "▱" * (8 - filled)


# ---------------------------------------------------------------------------
# render_statusline — FROZEN format (PLAN-s1.5.md § LOCKED decisions)
# ---------------------------------------------------------------------------

_SEP = " │ "  # U+2502 BOX DRAWINGS LIGHT VERTICAL


def render_statusline(view_model) -> str:  # duck-typed, no rich
    """Project a ViewModel to the FROZEN one-line statusline string.

    Frozen format (PLAN-s1.5.md):
        waiting → "KATAHARNESS 改善型 │ ⏳ idle — no active run"
        else    → "KATAHARNESS 改善型 │ <phase> │ <bar> <pct>% │ <done>/<total> tasks │ gate <gate|–> │ drift <d>"

    view_model is duck-typed (SimpleNamespace or real ViewModel):
        .waiting  .phase  .tasks (iterable with .percent and .done)
        .gate     .driftEscalations (tuple[int, int])

    The bar is 8-wide ▰▱; pct = round(mean(task.percent)) or 0 if no tasks.
    """
    if view_model.waiting:
        return "KATAHARNESS 改善型" + _SEP + "⏳ idle — no active run"

    phase: str = view_model.phase
    tasks = list(view_model.tasks)
    total: int = len(tasks)

    if total:
        pct: int = round(sum(t.percent for t in tasks) / total)
    else:
        pct = 0

    done: int = sum(1 for t in tasks if t.done)
    bar: str = _bar8(pct)
    gate: str = view_model.gate or "–"
    d: int = view_model.driftEscalations[0]

    return (
        "KATAHARNESS 改善型"
        + _SEP + phase
        + _SEP + f"{bar} {pct}%"
        + _SEP + f"{done}/{total} tasks"
        + _SEP + f"gate {gate}"
        + _SEP + f"drift {d}"
    )


# ---------------------------------------------------------------------------
# build_statusline — read .kata/, build ViewModel, render
# ---------------------------------------------------------------------------


def build_statusline(kata_dir: Union[str, Path]) -> str:
    """Read <kata_dir>/board.md + state.json and return the one-line statusline.

    Applies a .. guard on kata_dir (CWE-23).
    Absent or bad files are treated as empty/None (mirrors kata_dash patterns).
    Lazy-imports kata_dash_model so this module is importable in test contexts
    where kata_dash_model may not be installed.
    """
    # Security: reject path traversal
    safe_dir = _safe_path(kata_dir)

    board_file = safe_dir / "board.md"
    state_file = safe_dir / "state.json"

    # Read board text (empty string if absent/unreadable)
    board_text: str = ""
    if board_file.exists():
        try:
            board_text = board_file.read_text(encoding="utf-8")
        except OSError:
            pass

    # Read state dict (None if absent/unreadable/bad JSON)
    state: dict | None = None
    if state_file.exists():
        try:
            raw = state_file.read_text(encoding="utf-8")
            state = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            pass

    # Lazy import so importing kata_statusline in tests never hard-fails
    import kata_dash_model  # type: ignore[import]

    vm = kata_dash_model.build_view_model(board_text, state)
    return render_statusline(vm)


# ---------------------------------------------------------------------------
# write_bridge — kata superset context-usage bridge writer (CA-L1 / CA-L2)
# ---------------------------------------------------------------------------

#: session_id is interpolated into the bridge filename; accept only a safe
#: charset (UUIDs are `[0-9a-fA-F-]`). Combined with an explicit ".." reject
#: below, this blocks path traversal / separator injection (CWE-22/CWE-23).
_SAFE_SESSION_ID = re.compile(r"\A[A-Za-z0-9._-]+\Z")


def _is_number(value: Any) -> bool:
    """Return True iff *value* is a real int/float (bool rejected — subclasses int).

    Mirrors kata_gauge._is_number so the bridge this writer produces round-trips
    through kata_gauge.read_bridge's numeric guards.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def write_bridge(temp_dir: Union[str, Path], payload_dict: Any) -> Union[Path, None]:
    """Write the kata superset context-usage bridge file (CA-L1 / CA-L2).

    Writes ``<temp_dir>/kata-ctx-<session_id>.json`` with the CA-L2 superset schema
    verbatim: ``{session_id, remaining_percentage, used_pct, timestamp, total_tokens}``.
    ``timestamp`` is Unix epoch seconds now (GROUNDING G3); ``used_pct`` is
    ``100 - remaining_percentage``. The write is **atomic** (temp file in the same
    directory + :func:`os.replace`) so a reader (kata_gauge.read_bridge) never sees a
    partial file (CA-L1).

    The superset is **additive/BC with the gsd 4-field schema**
    (``{session_id, remaining_percentage, used_pct, timestamp}``); ``total_tokens`` is
    free because the wrapper receives the same statusline stdin (GROUNDING G3 —
    ``context_window.remaining_percentage`` + ``context_window.total_tokens`` confirmed).
    When ``total_tokens`` is absent/non-numeric the field is written as JSON ``null`` and
    the reader degrades to percentage-only triggering (CA-L2 degrade).

    Returns:
        The final bridge :class:`~pathlib.Path` on success, or ``None`` when nothing was
        written. Missing ``context_window`` in *payload_dict*, a missing/non-numeric
        ``remaining_percentage``, or a missing/unsafe ``session_id`` ⇒ ``None``, no file
        (a statusline event without gauge data is a legitimate host state — the READ
        side's absent-leg handles it; never a crash).

    Fail-soft (statusline contract — never crash the host statusline): ANY exception,
    including a write :class:`OSError`, is swallowed and yields ``None``. This is the
    documented observability-write exception to the D136 fail-closed posture, matching
    ``write_task_telemetry``'s fail-soft class.
    """
    try:
        if not isinstance(payload_dict, dict):
            return None

        session_id = payload_dict.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return None
        # filename-safety guard (CWE-22/CWE-23): session_id is interpolated into
        # the temp filename — reject '..' and any non-safe character. Defense in
        # depth even though the host session_id is trusted.
        if ".." in session_id or not _SAFE_SESSION_ID.match(session_id):
            return None

        context_window = payload_dict.get("context_window")
        if not isinstance(context_window, dict):
            return None

        remaining = context_window.get("remaining_percentage")
        if not _is_number(remaining):
            return None

        total_tokens = context_window.get("total_tokens")
        total_val = int(total_tokens) if _is_number(total_tokens) else None

        payload = {
            "session_id": session_id,
            "remaining_percentage": remaining,
            "used_pct": 100 - remaining,
            "timestamp": int(time.time()),
            "total_tokens": total_val,
        }

        temp_dir_path = Path(temp_dir)
        final_path = temp_dir_path / f"kata-ctx-{session_id}.json"

        # Atomic temp+rename (CA-L1): a sibling temp in the SAME directory, then
        # os.replace (atomic on one filesystem). The reader watches for the FINAL
        # name, which only ever appears whole via os.replace.
        fd, tmp_name = tempfile.mkstemp(
            dir=str(temp_dir_path), prefix="kata-ctx-", suffix=".json.tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
            os.replace(tmp_name, final_path)
        except OSError:
            # write/rename failed — clean up the orphan temp, never crash the host.
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            return None
        return final_path

    except Exception:  # noqa: BLE001 — fail-soft observability write (never raise to host)
        return None


# ---------------------------------------------------------------------------
# statusline_from_event — Claude statusLine adapter entry point
# ---------------------------------------------------------------------------


def statusline_from_event(stdin_text: str) -> str:
    """Parse the Claude statusLine stdin JSON and return the one-line statusline.

    The Claude statusLine command receives a JSON object on stdin.  The relevant
    field is 'cwd' (fallback: workspace.current_dir).  If no cwd is found, or
    <cwd>/.kata/ does not exist, return "" (invisible outside a kata run).

    Fail-soft: ANY exception in the entire body returns "".

    Spec: PLAN-s1.5.md § Task S1.5a / RESEARCH-s1.5.md § Claude stdin contract.
    """
    try:
        if not stdin_text:
            return ""

        data = json.loads(stdin_text)
        if not isinstance(data, dict):
            return ""

        # CA-L1/CA-L2: write the kata superset bridge from the SAME stdin JSON,
        # BEFORE the render path — the bridge must NOT depend on a kata cwd (a
        # non-kata cwd still writes the gauge). write_bridge is fail-soft (never
        # raises), so it cannot alter the rendered line.
        write_bridge(tempfile.gettempdir(), data)

        cwd: str = data.get("cwd") or (
            data.get("workspace", {}).get("current_dir") or ""
        )
        if not cwd:
            return ""

        kata_dir = Path(cwd) / ".kata"
        if not kata_dir.exists():
            return ""

        return build_statusline(kata_dir)

    except (Exception, SystemExit):  # noqa: BLE001
        # fail-soft: never crash Claude's statusline. The shared _safe_path ..
        # guard now raises ValueError (subclass of Exception, so caught above).
        # SystemExit is retained for defense-in-depth — any traversal cwd must
        # degrade to a blank line, not exit(1) — aligns fail-soft with fail-secure.
        return ""
