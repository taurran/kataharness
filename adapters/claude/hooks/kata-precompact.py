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

    The TARGET repo root comes from the PreCompact stdin payload's ``cwd``
    (falling back to the process cwd) — the session's repo, NOT the harness
    home. Only ``tools/`` (for the kata_trail import) resolves from this
    file's own path, since the engine ships with the harness clone.
    (2026-07-12 health review F1: the previous __file__-derived repo root
    snapshotted ~/.kata-home instead of the session repo, silently no-oping
    the Gap-1 guarantee in every installed deployment.)
"""

from __future__ import annotations

import json
import os
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


def _resolve_repo_root(payload: object) -> Path:
    """Resolve the SESSION repo root from the hook payload ``cwd``, else the process cwd.

    Mirrors kata-sessionstart.py's ``_resolve_base``. The board being snapshotted
    lives in the session's target repo — never in the harness home (F1).
    """
    if isinstance(payload, dict):
        cwd = payload.get("cwd")
        if isinstance(cwd, str) and cwd:
            return Path(cwd)
    return Path(os.getcwd())


def _main() -> None:
    """Snapshot the board and (if successful) emit a custom_instructions nudge."""
    # ------------------------------------------------------------------ #
    # The TARGET repo root comes from the PreCompact payload (session cwd);
    # the harness home (this file's tree) hosts only the engine import.
    # ------------------------------------------------------------------ #
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace") if not sys.stdin.closed else ""
    payload = json.loads(raw) if raw.strip() else {}
    repo_root = _resolve_repo_root(payload)

    # ------------------------------------------------------------------ #
    # Add the HARNESS's tools/ to sys.path so kata_trail imports without
    # install: this file lives at <harness>/adapters/claude/hooks/.
    # ------------------------------------------------------------------ #
    tools_dir = Path(__file__).resolve().parents[3] / "tools"
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
    except Exception as exc:  # noqa: BLE001  (fail-soft: never block or crash compaction)
        # One breadcrumb so a permanently-broken install is distinguishable from
        # "no kata run active" (F8). stderr only; still exit 0, never block.
        try:
            print(f"[kata-precompact] fail-soft: {type(exc).__name__}: {exc}", file=sys.stderr)
        except Exception:  # noqa: BLE001
            pass
