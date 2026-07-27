"""kata_handoff_break.py — the SESSION BREAK notice KataHarness prints at a handoff.

The formal, visible end-of-session artifact. It exists because the session boundary is the
one place the harness *cannot* act for the operator: no agent can trigger ``/clear`` or
``/compact``, and no agent can start a successor session. The boundary is therefore a
**handoff to a human**, and it deserves an official form rather than a paragraph of prose
the model may or may not remember to write.

What this closes
----------------
``adapters/claude/hooks/kata-precompact.py`` NUDGES the model to write a handoff; the
``SessionStart`` hook mechanically injects a pointer to ``.planning/HANDOFF.md``. So the
*read* half of session refresh is code and the *write* half was a suggestion. This module
gives the operator-facing half a deterministic owner (KH-T01).

Prescriptive by design
----------------------
It tells the operator to run **/clear**, not ``/compact``, and says why: compaction keeps a
lossy summary of a window that is about to be superseded by a written handoff, and that
summary is a slop source — the successor inherits a paraphrase of decisions *and* the
authoritative record, with no marker for which is which. A clear start plus a durable
handoff has exactly one source of truth.

Design notes
------------
- Pure + stdlib-only, mirroring ``kata_banner``/``kata_statusline``: trivially testable.
- **Deterministic**: same inputs ⇒ same bytes. No clock, no environment reads, no I/O.
  Any timestamp is passed IN by the caller (DETERMINISM-DOCTRINE law 7).
- Brand + rule glyph + width match ``kata_banner`` exactly, so the break reads as the same
  system that printed the loop-init banner.

Public API
----------
render_break(*, handoff_path, branch, head, master, gates, owed=(), next_step=None,
             stamp=None, width=None) -> str
render_reentry(*, handoff_path, repo_root=None) -> str  — the copy/paste block
"""

from __future__ import annotations

import unicodedata

BRAND = "KATAHARNESS 改善型"
_WIDTH = 74
_RULE = "━"
_THIN = "─"

#: The successor-session orientation, kept deliberately SHORT.
#: A large, detailed, prescriptive handoff makes a large orientation redundant — the
#: orientation's only job is to point at the handoff and forbid acting before reading it.
_REENTRY_TEMPLATE = """\
Resume the KataHarness run. Do these in order, and do not act before step 3 completes.

1. Read `{handoff}` in full. It is the authoritative state — it carries the decisions
   themselves, not pointers to them.
2. Verify its §0 GROUND TRUTH block yourself before trusting anything in it: tree clean,
   `git stash list` EMPTY (stop if not), the recorded master SHA, and the gauntlet via
   `cd tools && uv run python scripts/gauntlet.py` — NOT the venv python directly, which
   produces a false red on two integration tests offline.
3. Read §3 DECISIONS MADE and treat them as settled. Do not re-litigate them.
4. Then read §5 NEXT STEP and continue from there.

If §0 does not verify, STOP and report the mismatch instead of proceeding."""


def _dwidth(s: str) -> int:
    """Display width in terminal columns (CJK wide/fullwidth glyphs count as 2)."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def _center(text: str, width: int) -> str:
    pad = width - _dwidth(text)
    if pad <= 0:
        return text
    left = pad // 2
    return " " * left + text


def _bullet(label: str, value: str) -> str:
    return f"  {label:<14}{value}"


def render_reentry(*, handoff_path: str, repo_root: str | None = None) -> str:
    """Return the copy/paste block the operator pastes into the successor session.

    This IS the agent orientation. It stays short on purpose: when the handoff is large,
    detailed and prescriptive, a long orientation duplicates it and burns tokens twice.
    Its only jobs are to name the authoritative artifact, forbid acting before reading it,
    and require the ground-truth check.
    """
    block = _REENTRY_TEMPLATE.format(handoff=handoff_path)
    if repo_root:
        block = f"Working directory: {repo_root}\n\n{block}"
    return block


def render_break(
    *,
    handoff_path: str,
    branch: str,
    head: str,
    master: str,
    gates: str,
    owed: tuple[str, ...] = (),
    next_step: str | None = None,
    stamp: str | None = None,
    width: int | None = None,
) -> str:
    """Render the full SESSION BREAK notice.

    Every field is supplied by the caller — this function reads nothing and computes no
    time, so its output is byte-stable for a given set of inputs.
    """
    w = width or _WIDTH
    rule = _RULE * w
    thin = _THIN * w
    out: list[str] = []

    out.append(rule)
    out.append(_center(f"{BRAND}  ·  SESSION BREAK", w))
    out.append(rule)
    out.append("")
    out.append("  The run is PAUSED at a session boundary.")
    out.append("  KataHarness cannot cross this boundary for you — no agent can trigger")
    out.append("  /clear or /compact, or start a successor session. This step is yours.")
    out.append("")
    out.append(thin)
    out.append("  STATE — committed and pushed")
    out.append(thin)
    out.append(_bullet("handoff", handoff_path))
    out.append(_bullet("branch", f"{branch} @ {head}"))
    out.append(_bullet("master", master))
    out.append(_bullet("gates", gates))
    if stamp:
        out.append(_bullet("written", stamp))
    out.append("")
    out.append(thin)
    out.append("  REQUIRED ACTION — run /clear   (NOT /compact)")
    out.append(thin)
    out.append("  /clear  starts a genuinely fresh window. The handoff above is the single")
    out.append("          source of truth, and the SessionStart hook points the successor")
    out.append("          at it automatically.")
    out.append("")
    out.append("  /compact keeps a LOSSY SUMMARY of a window the handoff already supersedes.")
    out.append("          The successor then inherits a paraphrase of the decisions AND the")
    out.append("          authoritative record, with nothing marking which is which. That is")
    out.append("          a slop source. Prefer /clear whenever a written handoff exists.")
    out.append("")
    out.append(thin)
    out.append("  THEN PASTE THIS INTO THE NEW SESSION")
    out.append(thin)
    out.append("")
    for line in render_reentry(handoff_path=handoff_path).splitlines():
        out.append(f"  {line}" if line else "")
    out.append("")

    if owed:
        out.append(thin)
        out.append("  OWED TO YOU — carried across the break")
        out.append(thin)
        for item in owed:
            out.append(f"  · {item}")
        out.append("")

    if next_step:
        out.append(thin)
        out.append("  NEXT STEP")
        out.append(thin)
        out.append(f"  {next_step}")
        out.append("")

    out.append(rule)
    return "\n".join(out)


def _main(argv: list[str] | None = None) -> int:
    """CLI so the conductor can emit the break without re-authoring it in prose.

    Windows note: the notice renders `━` rules and the `改善型` brand mark. On a cp1252
    console or a redirected stdout, encoding would crash. Force UTF-8 with
    ``errors="replace"`` so glyphs DEGRADE rather than the break failing to print — the
    same mitigation `kata_dash` uses, for the same reason. A break notice that crashes at
    the boundary is worse than one with substituted characters.
    """
    import argparse
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError, OSError):
        pass

    p = argparse.ArgumentParser(description="Emit the KataHarness SESSION BREAK notice.")
    p.add_argument("--handoff", default=".planning/HANDOFF.md")
    p.add_argument("--branch", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--master", required=True)
    p.add_argument("--gates", required=True)
    p.add_argument("--owed", action="append", default=[])
    p.add_argument("--next-step", default=None)
    p.add_argument("--stamp", default=None, help="Display-only; never derived here (law 7).")
    a = p.parse_args(argv)

    print(render_break(
        handoff_path=a.handoff, branch=a.branch, head=a.head, master=a.master,
        gates=a.gates, owed=tuple(a.owed), next_step=a.next_step, stamp=a.stamp,
    ))
    return 0


if __name__ == "__main__":  # pragma: no cover - thin CLI wrapper
    raise SystemExit(_main())
