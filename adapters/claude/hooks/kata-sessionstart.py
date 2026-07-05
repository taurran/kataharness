"""adapters/claude/hooks/kata-sessionstart.py — SessionStart re-anchor hook (CA-L18).

On a post-compaction (``source == "compact"``) or respawned (``source == "resume"``)
SessionStart, this hook injects a re-anchor instruction into the fresh model context via
``hookSpecificOutput.additionalContext`` (GROUNDING-CLAUDE.md G2 — CONFIRMED mechanism).

Contract (DESIGN CA-L18; protocol/handoff.md:7):
- The re-anchor instruction points at the newest ``.planning/HANDOFF.md`` (the canonical
  durable handoff path — NOT the brief's "SELFHANDOFF.md"; SR-9). Orientation tiers
  consume it 1:1.
- The instruction carries the CA-L19 staleness rule pointer (defined in protocol/handoff.md
  + kata-orient; this hook only references it) and the kata-orient 3-tier rebuild.
- Absent ``.planning/HANDOFF.md`` ⇒ the injected context says so and points at a kata-orient
  full 3-tier rebuild (degradation §4 row 8).
- The matcher set (which SessionStart sources fire this hook) lives in the settings snippet;
  this hook additionally guards on ``source`` so a non-anchor source (startup/clear) is a
  clean no-op.
- FAIL-SOFT: any exception ⇒ silent exit 0. A hook must NEVER break the user's session
  (mirrors adapters/claude/hooks/kata-precompact.py). Never raises, never hangs.

The hook reads the SessionStart stdin JSON (fields ``source`` and ``cwd``). ``cwd`` is the
session's working directory (the target repo) and is used only to tailor the present/absent
HANDOFF.md wording — the injected instruction itself references the relative
``.planning/HANDOFF.md`` path, resolved by the resumed agent in its own cwd.

Usage:
    Invoked by Claude Code via the SessionStart hook entry in
    adapters/claude/settings.snippet.json. Also callable directly for testing:

        python adapters/claude/hooks/kata-sessionstart.py < event.json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# SessionStart sources that re-anchor a session (G2 matcher set). A respawned
# ("resume") session re-anchors identically to a post-compaction one.
_ANCHOR_SOURCES = frozenset({"compact", "resume"})

_HANDOFF_REL = Path(".planning") / "HANDOFF.md"


def _should_anchor(source: object) -> bool:
    """True only for the compact/resume SessionStart sources (defence-in-depth guard)."""
    return isinstance(source, str) and source in _ANCHOR_SOURCES


def _resolve_base(payload: object) -> Path:
    """Resolve the session's working dir from the payload ``cwd``, else the process cwd."""
    if isinstance(payload, dict):
        cwd = payload.get("cwd")
        if isinstance(cwd, str) and cwd:
            return Path(cwd)
    return Path(os.getcwd())


def _build_context(*, handoff_exists: bool) -> str:
    """The additionalContext re-anchor instruction (CA-L18), tailored to HANDOFF presence."""
    if handoff_exists:
        return (
            "KataHarness re-anchor (post-compaction / resumed session): before doing "
            "anything else, re-anchor on the newest `.planning/HANDOFF.md` — read it in the "
            "Read-in order it prescribes and confirm the green numbers. Then apply the handoff "
            "staleness rule (protocol/handoff.md): if any board DONE/DECISION line is newer "
            "than the HANDOFF.md git commit, the handoff is demoted from sole-anchor to "
            "context-input and the kata-orient 3-tier rebuild is authoritative. Rebuild full "
            "context via kata-orient (3-tier). Orientation tiers consume it 1:1."
        )
    return (
        "KataHarness re-anchor (post-compaction / resumed session): no `.planning/HANDOFF.md` "
        "was found in this repo — there is no durable handoff to anchor on. Before doing "
        "anything else, rebuild full context via a kata-orient full 3-tier rebuild."
    )


def _main() -> None:
    """Read the SessionStart event and, for anchor sources, inject the re-anchor context."""
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    source = payload.get("source") if isinstance(payload, dict) else None
    if not _should_anchor(source):
        return  # startup/clear (or unknown) — clean no-op, no injection

    base = _resolve_base(payload)
    handoff_exists = (base / _HANDOFF_REL).is_file()
    context = _build_context(handoff_exists=handoff_exists)

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                }
            }
        )
    )


if __name__ == "__main__":
    try:
        _main()
    except Exception:  # noqa: BLE001  (fail-soft: never break the user's session)
        pass
