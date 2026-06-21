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

Security: build_statusline() applies a _safe_path() .. guard (CWE-23, mirrors kata_dash).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union


# ---------------------------------------------------------------------------
# Internal path-traversal guard (CWE-23 — mirror kata_dash._safe_path)
# ---------------------------------------------------------------------------


def _safe_path(raw: Union[str, Path]) -> Path:
    """Reject any path containing '..' segments, then resolve.

    Consistent with kata_dash._safe_path and gate_emit._safe_path.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise SystemExit(
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

        cwd: str = data.get("cwd") or (
            data.get("workspace", {}).get("current_dir") or ""
        )
        if not cwd:
            return ""

        kata_dir = Path(cwd) / ".kata"
        if not kata_dir.exists():
            return ""

        return build_statusline(kata_dir)

    except Exception:  # noqa: BLE001  (fail-soft: never crash Claude's statusline)
        return ""
