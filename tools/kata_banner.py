"""kata_banner.py — the loop-init readout KataHarness prints at the start of every run.

A deterministic, few-line banner so the operator sees — every time a loop runs — that
it is KataHarness executing, and a brief summary of WHAT it is executing. Rendered by a
tool (not LLM-improvised) so the format is byte-identical every run (consistency, D18).

The conductor (`kata-loop`) emits the full banner at loop init and a one-line compact
banner on loop-back. Pure + stdlib-only (mirrors `kata_statusline.py`), so it is trivially
testable and reusable by adapters/hooks.

Public API
----------
render_banner(*, goal, run_shape=None, mode=None, grill=None, delivery=None,
              tasks=None, slices=None, gate="default-FAIL", drift=0, compact=False) -> str
"""

from __future__ import annotations

import unicodedata

BRAND = "KATAHARNESS 改善型"
_WIDTH = 60  # box rule width in display columns
_RULE = "━"
_DOT = " · "
_VALIDATION_MARKER = "Running KataHarness validation loop…"

# Hokusai-derived closeout-report palette (modules/closeout/resources/BRAND.md), adapted for a
# dark terminal: use the accent tones that read on dark (ochre arrow, warm border, mid-blue, paper),
# not the dark Prussian ink (which is the report's light-bg foreground).
_PALETTE = {
    "ochre": (181, 137, 75),   # #B5894B — the kaizen rising-arrow accent → the brand mark
    "border": (205, 190, 155),  # #CDBE9B — card border/divider → the box frame
    "blue": (46, 99, 137),     # #2E6389 — mid-blue → labels
    "paper": (233, 223, 200),  # #E9DFC8 — aged paper → values
    "muted": (117, 106, 82),   # #756A52 — metadata/taglines → "· executing"
    "rust": (166, 83, 43),     # #A6532B — error/backout (reserved)
}
_RESET = "\x1b[0m"


def _dwidth(s: str) -> int:
    """Display width in terminal columns (CJK wide/fullwidth glyphs count as 2)."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def _paint(text: str, role: str, *, bold: bool = False, enabled: bool = False) -> str:
    """Wrap ``text`` in a 24-bit ANSI color from the report palette (no-op when disabled)."""
    if not enabled or not text:
        return text
    r, g, b = _PALETTE[role]
    return (("\x1b[1m" if bold else "") + f"\x1b[38;2;{r};{g};{b}m") + text + _RESET


def _join(parts: list[str]) -> str:
    return _DOT.join(p for p in parts if p)


def render_banner(
    *,
    goal: str,
    run_shape: str | None = None,
    mode: str | None = None,
    grill: str | None = None,
    delivery: str | None = None,
    tasks: int | None = None,
    slices: int | None = None,
    gate: str = "default-FAIL",
    drift: int = 0,
    compact: bool = False,
    color: bool = False,
) -> str:
    """Render the loop-init banner (boxed) or the compact loop-back line.

    Only the fields you pass appear — missing run/plan fields are omitted, so the banner
    renders cleanly before a plan exists (e.g. at initiate) and fills in once it does.
    ``color=True`` paints it in the closeout-report palette via 24-bit ANSI.
    """
    goal = (goal or "").strip() or "(goal pending)"

    if compact:
        tail = f" · {tasks} tasks" if tasks is not None else ""
        return (
            _paint("↻ ", "ochre", enabled=color)
            + _paint(BRAND, "ochre", bold=True, enabled=color)
            + _paint(f" · loop-back — {goal}{tail}", "muted", enabled=color)
        )

    run_line = _join([run_shape, mode, (f"grill {grill}" if grill else None), delivery])
    plan_line = _join([
        (f"{tasks} tasks" if tasks is not None else None),
        (f"{slices} slices" if slices is not None else None),
        (f"gate {gate}" if gate else None),
        (f"drift {drift}" if drift is not None else None),
    ])

    # Top rule: brand mark (ochre) + tagline (muted) + frame filler (border), sized on the PLAIN text.
    plain_header = f"{_RULE}{_RULE} {BRAND} · executing "
    fill = max(0, _WIDTH - _dwidth(plain_header))
    top = (
        _paint(f"{_RULE}{_RULE} ", "border", enabled=color)
        + _paint(BRAND, "ochre", bold=True, enabled=color)
        + _paint(" · executing ", "muted", enabled=color)
        + _paint(_RULE * fill, "border", enabled=color)
    )
    bottom = _paint(_RULE * _WIDTH, "border", enabled=color)

    def _row(name: str, value: str) -> str:
        return f" {_paint(name.ljust(11), 'blue', enabled=color)} {_paint(value, 'paper', enabled=color)}"

    rows = []
    if run_line:
        rows.append(_row("run-shape", run_line))
    rows.append(_row("goal", goal))
    if plan_line:
        rows.append(_row("plan", plan_line))

    return "\n".join([top, *rows, bottom])


def render_validation_banner(*, color: bool = False) -> str:
    """Render the deterministic validation-loop init banner.

    Emitted once at the start of every kata-validate run so the operator sees —
    immediately — that KataHarness is running the validation mini-loop.
    Byte-identical for identical inputs (deterministic). ``color=True`` paints
    the closeout-report palette via 24-bit ANSI (same palette as ``render_banner``).
    """
    plain_header = f"{_RULE}{_RULE} {BRAND} · validation "
    fill = max(0, _WIDTH - _dwidth(plain_header))
    top = (
        _paint(f"{_RULE}{_RULE} ", "border", enabled=color)
        + _paint(BRAND, "ochre", bold=True, enabled=color)
        + _paint(" · validation ", "muted", enabled=color)
        + _paint(_RULE * fill, "border", enabled=color)
    )
    bottom = _paint(_RULE * _WIDTH, "border", enabled=color)
    body = " " + _paint(_VALIDATION_MARKER, "paper", enabled=color)
    return "\n".join([top, body, bottom])


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    import argparse
    import os
    import sys

    # The banner uses box-drawing + CJK glyphs; force UTF-8 so a cp1252 console doesn't choke.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    p = argparse.ArgumentParser(prog="kata_banner", description="Render the KataHarness loop-init banner.")
    p.add_argument("--validation", action="store_true", help="render the validation-loop init banner instead")
    p.add_argument("--goal", default=None)
    p.add_argument("--run-shape")
    p.add_argument("--mode")
    p.add_argument("--grill")
    p.add_argument("--delivery")
    p.add_argument("--tasks", type=int)
    p.add_argument("--slices", type=int)
    p.add_argument("--gate", default="default-FAIL")
    p.add_argument("--drift", type=int, default=0)
    p.add_argument("--compact", action="store_true")
    p.add_argument("--color", dest="color", action="store_true", default=None, help="force the report palette (ANSI)")
    p.add_argument("--no-color", dest="color", action="store_false", help="plain text, no ANSI")
    a = p.parse_args(argv)

    # Resolve color: explicit flag wins; else auto (a TTY and NO_COLOR unset — no-color.org).
    color = a.color
    if color is None:
        color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

    if a.validation:
        print(render_validation_banner(color=color))
        return 0

    if not a.goal:
        p.error("--goal is required unless --validation is used")

    print(render_banner(
        goal=a.goal, run_shape=a.run_shape, mode=a.mode, grill=a.grill, delivery=a.delivery,
        tasks=a.tasks, slices=a.slices, gate=a.gate, drift=a.drift, compact=a.compact, color=color,
    ))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
