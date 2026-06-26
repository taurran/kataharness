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


def _dwidth(s: str) -> int:
    """Display width in terminal columns (CJK wide/fullwidth glyphs count as 2)."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


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
) -> str:
    """Render the loop-init banner (boxed) or the compact loop-back line.

    Only the fields you pass appear — missing run/plan fields are omitted, so the banner
    renders cleanly before a plan exists (e.g. at initiate) and fills in once it does.
    """
    goal = (goal or "").strip() or "(goal pending)"

    if compact:
        tail = f" · {tasks} tasks" if tasks is not None else ""
        return f"↻ {BRAND} · loop-back — {goal}{tail}"

    run_line = _join([run_shape, mode, (f"grill {grill}" if grill else None), delivery])
    plan_line = _join([
        (f"{tasks} tasks" if tasks is not None else None),
        (f"{slices} slices" if slices is not None else None),
        (f"gate {gate}" if gate else None),
        (f"drift {drift}" if drift is not None else None),
    ])

    header = f"{_RULE}{_RULE} {BRAND} · executing "
    top = header + _RULE * max(0, _WIDTH - _dwidth(header))
    bottom = _RULE * _WIDTH

    rows = []
    if run_line:
        rows.append(f" run-shape   {run_line}")
    rows.append(f" goal        {goal}")
    if plan_line:
        rows.append(f" plan        {plan_line}")

    return "\n".join([top, *rows, bottom])


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    import argparse
    import sys

    # The banner uses box-drawing + CJK glyphs; force UTF-8 so a cp1252 console doesn't choke.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    p = argparse.ArgumentParser(prog="kata_banner", description="Render the KataHarness loop-init banner.")
    p.add_argument("--goal", required=True)
    p.add_argument("--run-shape")
    p.add_argument("--mode")
    p.add_argument("--grill")
    p.add_argument("--delivery")
    p.add_argument("--tasks", type=int)
    p.add_argument("--slices", type=int)
    p.add_argument("--gate", default="default-FAIL")
    p.add_argument("--drift", type=int, default=0)
    p.add_argument("--compact", action="store_true")
    a = p.parse_args(argv)
    print(render_banner(
        goal=a.goal, run_shape=a.run_shape, mode=a.mode, grill=a.grill, delivery=a.delivery,
        tasks=a.tasks, slices=a.slices, gate=a.gate, drift=a.drift, compact=a.compact,
    ))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
