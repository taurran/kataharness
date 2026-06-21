"""kata_dash.py — KataHarness rich live dashboard (DASH-render slice).

Renders the ViewModel produced by kata_dash_model into a rich TUI panel.
This file owns ALL rich/display logic; the pure model lives in kata_dash_model.

Architecture:
- Pure render helpers (render_bar, spinner_frame, render_row_text, render_ribbon)
  — no I/O, fully unit-tested with SimpleNamespace duck-typed stand-ins.
- build_frame(view_model, tick) -> rich.console.RenderableType
  — composes helpers into a rich Panel.
- _safe_path / main() — CLI tail-loop (NOT unit-tested, thin glue).

Security note (from PLAN.md threat model): --kata-dir is operator-supplied;
reuse _safe_path ..  guard (CWE-23 defence-in-depth, consistent with gate_emit).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ---------------------------------------------------------------------------
# Pure render helpers — no I/O, duck-typed inputs, fully unit-testable
# ---------------------------------------------------------------------------

_SPINNER_FRAMES = ("⠹", "⠼", "⠧", "⠿")
_RIBBON_PHASES = ("GRILL", "FREEZE", "EXECUTE", "EVALUATE", "HANDOFF", "IMPROVE")


def render_bar(percent: int, width: int = 20) -> str:
    """Return a block-char progress bar string of exactly `width` characters.

    Filled chars: ▰  Empty chars: ▱
    filled = round(percent / 100 * width)
    """
    filled = round(percent / 100 * width)
    filled = max(0, min(width, filled))  # clamp to [0, width]
    return "▰" * filled + "▱" * (width - filled)


def spinner_frame(tick: int) -> str:
    """Return the braille spinner char for the given tick (cycles every 4)."""
    return _SPINNER_FRAMES[tick % 4]


def render_row_text(task, tick: int) -> str:
    """Render one task row as a plain string.

    Format: ▸ <label>  <bar>  <pct>%  <glyph> <status> [<progressLabel>]

    task is duck-typed (SimpleNamespace or real TaskRow):
      .label, .percent, .done, .blocked, .active, .status
      .progressLabel  (optional; shown when non-empty)
    Glyph priority: done → ✓ ; blocked → ✗ ; active → spinner ; else ·
    """
    bar = render_bar(task.percent, width=20)

    if task.done:
        glyph = "✓"
    elif task.blocked:
        glyph = "✗"
    elif task.active:
        glyph = spinner_frame(tick)
    else:
        glyph = "·"

    # progressLabel is optional; only present on TaskRow from S1b+
    progress_label = getattr(task, "progressLabel", "")
    status_text = f"{glyph} {task.status}"
    if progress_label:
        status_text = f"{status_text}  {progress_label}"

    return f"▸ {task.label}  {bar}  {task.percent}%  {status_text}"


def render_ribbon(phase: str) -> str:
    """Return the loop-phase ribbon with the active phase highlighted.

    Format: GRILL ▸ FREEZE ▸ ◉EXECUTE ▸ EVALUATE ▸ HANDOFF ▸ IMPROVE
    Active phase is prefixed with ◉ and surrounded by square brackets
    to make it visibly distinct: [◉EXECUTE]
    """
    parts = []
    for p in _RIBBON_PHASES:
        if p == phase:
            parts.append(f"[◉{p}]")
        else:
            parts.append(p)
    return " ▸ ".join(parts)


# ---------------------------------------------------------------------------
# rich frame builder
# ---------------------------------------------------------------------------

def build_frame(view_model, tick: int) -> RenderableType:
    """Compose a rich Panel from the ViewModel (duck-typed).

    view_model fields (attribute access):
      spec, wave, phase, gate, tasks, driftEscalations, events, waiting, updatedUtc

    If view_model.waiting is True, return a calm "waiting" Panel.
    Otherwise return the full dashboard Panel.
    """
    # ---- waiting path ----
    if view_model.waiting:
        return Panel(
            Text("⏳ waiting for an orchestrated run…", justify="center"),
            title="KATAHARNESS 改善型",
            border_style="dim",
        )

    # ---- header ----
    spec = view_model.spec or "—"
    wave = view_model.wave or "—"
    gate = view_model.gate or "—"
    header_title = f"KATAHARNESS 改善型  ·  {spec}  ·  wave {wave}  ·  {gate}"

    # ---- task table ----
    task_table = Table.grid(padding=(0, 1))
    task_table.add_column(no_wrap=True)

    for task in view_model.tasks:
        row_text = render_row_text(task, tick)
        task_table.add_row(row_text)

    # ---- ribbon ----
    ribbon_text = render_ribbon(view_model.phase)

    # ---- footer ----
    drift, escalations = view_model.driftEscalations
    events_str = "  ".join(view_model.events[-3:]) if view_model.events else "—"
    footer_text = (
        f"board ▸ {events_str}\n"
        f"drift {drift}  ·  escalations {escalations}"
    )

    # ---- body: tasks + ribbon + footer ----
    body = Table.grid()
    body.add_column()
    body.add_row(task_table)
    body.add_row(Text(""))
    body.add_row(Text(ribbon_text, justify="center"))
    body.add_row(Text(""))
    body.add_row(Text(footer_text, style="dim"))

    return Panel(body, title=header_title, border_style="blue")


# ---------------------------------------------------------------------------
# Security: path-traversal guard (CWE-23, consistent with gate_emit._safe_path)
# ---------------------------------------------------------------------------

def _safe_path(raw: str) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied CLI path, then resolve.

    Blocks any '..' segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree.  Consistent with gate_emit.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise SystemExit(f"kata_dash: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


# ---------------------------------------------------------------------------
# CLI tail-loop (thin glue — NOT unit-tested, only integration-smoked)
# kata_dash_model import is LAZY here so importing kata_dash for tests never fails
# ---------------------------------------------------------------------------

def main(argv: Optional[list] = None) -> None:
    """CLI entry-point: tail .kata/board.md + .kata/state.json and render live."""
    parser = argparse.ArgumentParser(
        prog="kata_dash",
        description="KataHarness live dashboard — tail .kata/ and render in a side terminal.",
    )
    parser.add_argument(
        "--kata-dir",
        default=".kata",
        metavar="DIR",
        help="Path to the .kata/ directory (default: .kata)",
    )
    parser.add_argument(
        "--refresh",
        type=float,
        default=0.15,
        metavar="SEC",
        help="Refresh interval in seconds (default: 0.15)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Render a single frame and exit (no live loop)",
    )
    args = parser.parse_args(argv)

    # Lazy import: keeps kata_dash importable in test contexts where
    # kata_dash_model does not exist.
    import kata_dash_model  # type: ignore[import]
    from rich.live import Live

    # The dashboard renders Unicode glyphs (改善型 kanji, braille spinners, block bars). On a
    # non-UTF-8 Windows stdout (piped/redirected, or a cp1252 console) rich's encode
    # would crash. Force UTF-8 with errors="replace" so glyphs degrade, never crash;
    # and disable the legacy-windows renderer so a single code path drives output.
    from rich.console import Console
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError, OSError):
        pass
    console = Console(legacy_windows=False)

    kata_dir = _safe_path(args.kata_dir)
    board_file = kata_dir / "board.md"
    state_file = kata_dir / "state.json"

    def _read_sources():
        board_text = ""
        state = None

        if board_file.exists():
            try:
                board_text = board_file.read_text(encoding="utf-8")
            except OSError:
                pass

        if state_file.exists():
            try:
                raw = state_file.read_text(encoding="utf-8")
                state = json.loads(raw)
            except (OSError, json.JSONDecodeError):
                pass

        return board_text, state

    if args.once:
        # Single render and exit
        board_text, state = _read_sources()
        view_model = kata_dash_model.build_view_model(board_text, state)
        frame = build_frame(view_model, tick=0)
        console.print(frame)
        return

    # Live tail loop
    tick = 0
    with Live(console=console, refresh_per_second=int(1 / args.refresh) if args.refresh > 0 else 7) as live:
        while True:
            board_text, state = _read_sources()
            view_model = kata_dash_model.build_view_model(board_text, state)
            frame = build_frame(view_model, tick=tick)
            live.update(frame)
            tick += 1
            time.sleep(args.refresh)


if __name__ == "__main__":
    main()
