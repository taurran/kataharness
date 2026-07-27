"""kata_handoff_break.py — the SESSION BREAK notice KataHarness prints at a handoff.

The session boundary is the one place the harness cannot act for the operator: no agent can
trigger ``/clear`` or ``/compact``, or start a successor session. So the boundary is a
handoff to a human, and it gets an official form rather than prose the model may or may not
remember to write.

What this closes: ``kata-precompact.py`` NUDGES the model to write a handoff, while the
``SessionStart`` hook mechanically injects a pointer to it. The read half was code; the
write half was a suggestion. This gives the operator-facing half a deterministic owner
(KH-T01).

Terse by design. The re-entry block carries CONCRETE commands and their expected values so
the successor verifies rather than trusts; everything else is one line or omitted.

Deterministic: no clock, no environment reads, no I/O. Any timestamp is passed in by the
caller (DETERMINISM-DOCTRINE law 7). Brand/rule/width match ``kata_banner``.

Public API
----------
render_break(*, handoff_path, repo, branch, head, master, gates, owed=(), next_step=None,
             stamp=None, width=None) -> str
render_reentry(*, handoff_path, repo, branch, master) -> str
"""

from __future__ import annotations

import unicodedata

BRAND = "KATAHARNESS 改善型"
_WIDTH = 74
_RULE = "━"

#: The successor-session orientation. Deliberately short: a large, prescriptive handoff
#: makes a large orientation redundant. Its jobs are to name the authoritative artifact,
#: give the verification commands WITH their expected values, and forbid acting on a mismatch.
_REENTRY_TEMPLATE = """\
cd {repo}

Read {handoff} in full — it is the authoritative state.

Verify before acting. STOP and report on any mismatch:
  git status --porcelain                          -> empty
  git stash list                                  -> empty
  git rev-parse --short origin/master             -> {master}
  git rev-parse --abbrev-ref HEAD                 -> {branch}
  cd tools && uv run python scripts/gauntlet.py   -> 4/4 PASS
  (use `uv run` — the .venv python false-reds 2 integration tests offline)

§3 DECISIONS are settled; do not re-litigate. Continue from §5 NEXT STEP."""


def _dwidth(s: str) -> int:
    """Display width in terminal columns (CJK wide/fullwidth glyphs count as 2)."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def _center(text: str, width: int) -> str:
    pad = width - _dwidth(text)
    return (" " * (pad // 2) + text) if pad > 0 else text


def _bullet(label: str, value: str) -> str:
    return f"  {label:<10}{value}"


def render_reentry(*, handoff_path: str, repo: str, branch: str, master: str) -> str:
    """Return the copy/paste block for the successor session — this IS the orientation."""
    return _REENTRY_TEMPLATE.format(
        handoff=handoff_path, repo=repo, branch=branch, master=master)


def render_break(
    *,
    handoff_path: str,
    repo: str,
    branch: str,
    head: str,
    master: str,
    gates: str,
    owed: tuple[str, ...] = (),
    next_step: str | None = None,
    stamp: str | None = None,
    width: int | None = None,
) -> str:
    """Render the SESSION BREAK notice. Reads nothing; byte-stable for given inputs."""
    w = width or _WIDTH
    rule = _RULE * w
    out: list[str] = [rule, _center(f"{BRAND}  ·  SESSION BREAK", w), rule, ""]

    out.append(_bullet("handoff", handoff_path))
    out.append(_bullet("branch", f"{branch} @ {head}"))
    out.append(_bullet("master", master))
    out.append(_bullet("gates", gates))
    if stamp:
        out.append(_bullet("written", stamp))
    out.append("")
    out.append("  ▶ RUN /clear — not /compact, which keeps a lossy summary of a window")
    out.append("                 this handoff already replaces.")
    out.append("")
    out.append(rule)
    out.append("  PASTE INTO THE NEW SESSION")
    out.append(rule)
    out.append("")
    out.append(render_reentry(
        handoff_path=handoff_path, repo=repo, branch=branch, master=master))
    out.append("")

    if owed:
        out.append(rule)
        out.append("  OWED TO YOU")
        out.append(rule)
        out.extend(f"  · {item}" for item in owed)
        out.append("")

    if next_step:
        out.append(f"  NEXT: {next_step}")
        out.append("")

    out.append(rule)
    return "\n".join(out)


def _main(argv: list[str] | None = None) -> int:
    """CLI so the conductor emits the break instead of re-authoring it in prose.

    Windows: the notice renders `━` and `改善型`. On a cp1252 console or redirected stdout
    this would crash, so stdout is reconfigured to UTF-8 with ``errors="replace"`` — glyphs
    degrade, the break still prints. Same mitigation `kata_dash` uses, same reason.
    """
    import argparse
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError, OSError):
        pass

    p = argparse.ArgumentParser(description="Emit the KataHarness SESSION BREAK notice.")
    p.add_argument("--handoff", default=".planning/HANDOFF.md")
    p.add_argument("--repo", required=True)
    p.add_argument("--branch", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--master", required=True)
    p.add_argument("--gates", required=True)
    p.add_argument("--owed", action="append", default=[])
    p.add_argument("--next-step", default=None)
    p.add_argument("--stamp", default=None, help="Display-only; never derived here (law 7).")
    a = p.parse_args(argv)

    print(render_break(
        handoff_path=a.handoff, repo=a.repo, branch=a.branch, head=a.head,
        master=a.master, gates=a.gates, owed=tuple(a.owed),
        next_step=a.next_step, stamp=a.stamp,
    ))
    return 0


if __name__ == "__main__":  # pragma: no cover - thin CLI wrapper
    raise SystemExit(_main())
