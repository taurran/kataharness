"""kata_steer.py — the operator->agent steering channel reader (pure stdlib).

Mid-run direction without a restart. The orchestrator calls this at every wave/task
boundary (a deterministic cadence) to (a) detect a graceful STOP request and (b) read
any active operator directives from ``STEERING.md``. This is the engine behind
``protocol/steering.md``; before it existed, ``STEERING.md`` claimed "the harness reads
this on a cadence" with no implementation (2026-07-12 health review F-3 — the facade the
Prime Directives exist to prevent).

Design (deterministic, fail-closed on the STOP side, fail-soft on the read side):

- **STOP is a file-presence kill-switch.** ``AGENT_STOP`` (a file at ``<kata_dir>/AGENT_STOP``
  OR a ``## AGENT_STOP`` sentinel line in ``STEERING.md``) requests a **graceful halt at the
  next boundary** — never a mid-task blind kill (board.md's "never a blind kill" rule). The
  orchestrator parks in-flight work, writes a handoff, and stops. ``stop_requested`` is
  fail-CLOSED on ambiguity is not appropriate here (a missing file is the normal state), so it
  returns False only when it can positively confirm no sentinel; any *unreadable* STEERING.md
  with the marker byte present is treated as a stop (safe direction: halting is never harmful).

- **Directives are the "## Active directives" section** of STEERING.md: every non-empty,
  non-comment line under that heading and above the next ``##`` heading is an active directive.
  The reader is fail-soft (an absent/malformed file yields no directives — steering is additive,
  never run-fatal).

The orchestrator, after acting on a directive, moves it under "## Consumed / delivered" (a prose
edit it already owns); this module only READS — it never rewrites STEERING.md (single-writer
discipline; the operator and the orchestrator own that file, not the engine).
"""

from __future__ import annotations

from pathlib import Path

_STOP_FILENAME = "AGENT_STOP"
_STOP_SENTINEL = "## AGENT_STOP"
_ACTIVE_HEADING = "## Active directives"


def _is_placeholder(stripped: str) -> bool:
    """True for the ``_(none active …)_`` template placeholder — NOT a real directive.

    Tight match (adval finding #3): an italic-parenthetical whose inner text opens with
    "none". A real directive that merely happens to start with "(none-blocking)…" is NOT a
    placeholder — directives are normally ``- `` bullets, and only the shipped italic
    ``_( … )_`` placeholder is skipped.
    """
    if stripped.startswith("_(") and stripped.endswith(")_"):
        inner = stripped[2:-2].strip().lower()
        return inner.startswith("none")
    return False


def _safe_path(raw: str | Path) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied path, then resolve.

    Mirrors the canonical guard (kata_board._safe_path). The path-guard family's
    ONE enforced invariant — every member rejects a ``..`` component with
    ValueError — is pinned by ``tests/test_path_guard_family.py`` (behavioral,
    not textual identity).
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"kata_steer: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


def stop_requested(kata_dir: str | Path, steering_path: str | Path | None = None) -> bool:
    """Return True if a graceful-stop was requested (AGENT_STOP file OR STEERING sentinel).

    Checked by the orchestrator at every boundary. A True result means: finish nothing new,
    park in-flight tasks, write the handoff, and stop cleanly at this boundary. The check is
    deliberately biased toward halting — an unreadable STEERING.md whose bytes contain the
    sentinel marker still counts as a stop (halting is the safe direction; the operator asked).
    """
    kata = _safe_path(kata_dir)
    if (kata / _STOP_FILENAME).exists():
        return True
    sp = Path(steering_path) if steering_path is not None else (kata.parent / "STEERING.md")
    try:
        text = sp.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return False  # no readable steering file ⇒ no sentinel-based stop
    return any(line.strip() == _STOP_SENTINEL for line in text.splitlines())


def read_active_directives(steering_path: str | Path) -> list[str]:
    """Return the list of active operator directives (fail-soft: [] on absent/malformed).

    Directives are the non-empty, non-placeholder, non-``##``-heading lines under the
    "## Active directives" heading, up to the next ``##`` heading. Deterministic: source
    order preserved, no dedupe, no reordering.
    """
    try:
        text = Path(steering_path).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return []

    directives: list[str] = []
    in_section = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            in_section = stripped == _ACTIVE_HEADING
            continue
        if not in_section:
            continue
        if not stripped:
            continue
        if _is_placeholder(stripped):
            continue
        directives.append(stripped)
    return directives


def has_active_steering(steering_path: str | Path) -> bool:
    """Convenience: True iff there is at least one active directive."""
    return bool(read_active_directives(steering_path))
