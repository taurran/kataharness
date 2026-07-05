"""adapters/claude/hooks/kata-precompact.py — PreCompact hook for KataHarness.

Thin trigger that commits ``.kata/board.md`` to ``refs/kata/trail`` before
Claude auto-compacts the context window.  Invoked by Claude Code's
PreCompact hook entry in settings.snippet.json (see adapters/claude/README.md).

Contract (DESIGN §2 B2, L4, D133):
- Calls kata_trail.snapshot_board(repo_root) — git plumbing only.
  Never touches the working tree or index, never pushes, never writes a branch.
- Inherits kata_trail's fail-soft robustness: no-op on absent board,
  retry-once-then-skip on a busy ref-lock.
- NEVER raises to the caller.  NEVER hangs.  Always exits 0.
- If the snapshot succeeds (result["committed"]), emits a JSON line on stdout
  with a ``custom_instructions`` key nudging the resumed turn to run
  kata-handoff.  Durable safety NEVER depends on that nudge — the mechanical
  commit to refs/kata/trail is the guarantee.
- If the snapshot is skipped (no board, busy lock, etc.) the hook exits
  silently and cleanly; compaction proceeds unaffected.

ASSUMPTION — flagged for live-proof #2 (see README.md §Assumptions):
  Claude Code's ``PreCompact`` hook is a synchronous shell command invoked
  before context compaction with a usable time budget.  If this assumption
  does not hold, Gap 2/3 still close via B1's integration-cadence call site
  in kata-orchestrate; only the compaction-window floor of Gap 1 is affected.

Usage:
    This script is invoked by Claude Code via the hook entry in
    adapters/claude/settings.snippet.json.  It can also be called directly
    for testing:

        python adapters/claude/hooks/kata-precompact.py

    It resolves the repo root from its own __file__ path (three levels up
    from adapters/claude/hooks/), so it works regardless of cwd.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _handoff_status_suffix(repo_root: Path) -> str:
    """CA-L17 ADDITIVE surface: describe ``.planning/HANDOFF.md`` existence + mtime.

    Observe-only and pure stdlib. Returns a leading-space suffix to append to the
    existing custom_instructions nudge (so the resumed turn also learns about the
    durable handoff), or a rebuild pointer when no handoff exists. NEVER block-shaped
    (no ``decision``, no exit code) — the hook must never block compaction (G2: blocking
    near the limit is dangerous). Fail-soft: an OS error yields an empty suffix.
    """
    handoff = repo_root / ".planning" / "HANDOFF.md"
    try:
        if handoff.is_file():
            mtime = datetime.fromtimestamp(handoff.stat().st_mtime, tz=timezone.utc)
            return (
                " HANDOFF.md present (.planning/HANDOFF.md, modified "
                f"{mtime.isoformat()}); on resume, apply the handoff staleness rule — "
                "demote it if any board DONE/DECISION line is newer than its git commit."
            )
    except OSError:
        return ""
    return (
        " No .planning/HANDOFF.md found; on resume, rebuild context via a "
        "kata-orient full 3-tier rebuild."
    )


def _main() -> None:
    """Snapshot the board and (if successful) emit a custom_instructions nudge."""
    # ------------------------------------------------------------------ #
    # Locate repo root: this file lives at adapters/claude/hooks/
    #   parents[0] = adapters/claude/hooks/
    #   parents[1] = adapters/claude/
    #   parents[2] = adapters/
    #   parents[3] = repo root
    # ------------------------------------------------------------------ #
    repo_root = Path(__file__).resolve().parents[3]

    # ------------------------------------------------------------------ #
    # Add tools/ to sys.path so kata_trail can be imported without install
    # ------------------------------------------------------------------ #
    tools_dir = repo_root / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))

    import kata_trail  # noqa: PLC0415  (deferred import — path must be set first)

    result = kata_trail.snapshot_board(str(repo_root))

    # ------------------------------------------------------------------ #
    # Optional nudge: if snapshot committed, tell the resumed turn to run
    # kata-handoff.  Safety NEVER depends on this nudge (L4).
    # ------------------------------------------------------------------ #
    if "committed" in result:
        sha_short = result["committed"][:8]
        nudge = (
            "KataHarness trail checkpoint saved before compaction "
            f"(refs/kata/trail → {sha_short}). "
            "First action after resuming: invoke the kata-handoff skill "
            "to restore context from the just-committed board snapshot."
        )
        # CA-L17: additively surface HANDOFF.md existence/freshness in the SAME nudge.
        # Observe-only; never block-shaped. The board-snapshot leg above is unchanged.
        nudge += _handoff_status_suffix(repo_root)
        # Output a single JSON line; Claude Code reads this as custom_instructions
        # for the post-compaction resumed turn.
        print(json.dumps({"custom_instructions": nudge}))
    # else: skipped (no board, busy lock, etc.) — exit silently


if __name__ == "__main__":
    try:
        _main()
    except Exception:  # noqa: BLE001  (fail-soft: never block or crash compaction)
        pass
