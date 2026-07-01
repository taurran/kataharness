"""kata_trail.py — durable-board helper (restore-hardening B1).

Snapshots ``.kata/board.md`` to the orphan ref ``refs/kata/trail`` via git
PLUMBING only.  The call chain is:

    git hash-object -w <board>          # write blob to object store
    git mktree  (stdin: mode blob sha TAB board.md)  # build tree (no index touch)
    git commit-tree <tree> [-p <prior>] # build commit (no index touch)
    git update-ref refs/kata/trail <commit>          # atomically point the ref

Invariants (DESIGN §2 B1 / D133):
- NEVER touches the working tree or the real index.
- NEVER writes to refs/heads/* or the integration ref.
- NEVER pushes.
- Commits ONLY board.md (not state.json, not source files).
- On a busy ``refs/kata/trail.lock``: retry ONCE, then return a skip sentinel.
- When board.md is absent: return a skip sentinel immediately.
- On any subprocess or OS error: return a skip sentinel (never raise to the caller).

Public API
----------
snapshot_board(repo_root=".") -> dict
    On success:  {"committed": "<40-char-sha>"}
    On skip:     {"skipped": "<human-readable-reason>"}
    Never raises.
"""

from __future__ import annotations

import datetime
import subprocess
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TRAIL_REF = "refs/kata/trail"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess:
    """Run a git plumbing command and raise CalledProcessError on non-zero exit.

    shell=False is enforced by passing a fixed argv list.  Never accepts
    untrusted strings in the command position.
    """
    return subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )


def _is_lock_error(exc: subprocess.CalledProcessError, root: Path) -> bool:
    """Return True when a git error looks like ref-lock contention.

    Two signals are checked for robustness across platforms and git versions:
    1. The stderr from git mentions "lock" (standard across git builds).
    2. Fallback: the lock file itself exists on disk (belt-and-suspenders for
       Windows environments where git error messages may differ).
    """
    if "lock" in exc.stderr.lower():
        return True
    # Fallback: check the canonical lock-file path for this ref
    lock_path = root / ".git" / "refs" / "kata" / "trail.lock"
    return lock_path.exists()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def snapshot_board(repo_root: str = ".") -> dict[str, Any]:
    """Snapshot ``.kata/board.md`` to ``refs/kata/trail`` via git plumbing only.

    Parameters
    ----------
    repo_root:
        Root of the git repository (the directory that contains ``.git/``).
        Defaults to the current working directory.

    Returns
    -------
    dict
        ``{"committed": "<sha>"}`` on success.
        ``{"skipped": "<reason>"}`` on any non-fatal condition (absent board,
        busy lock, or subprocess/OS error).

    This function never raises.  The durability path must never crash a run.
    """
    try:
        root = Path(repo_root).resolve()
        board_path = root / ".kata" / "board.md"

        # ------------------------------------------------------------------ #
        # Guard: no-op when board.md is absent (fired outside a run)
        # ------------------------------------------------------------------ #
        if not board_path.exists():
            return {"skipped": "no-board"}

        # ------------------------------------------------------------------ #
        # Step 1 — write the board blob to the object store
        # git hash-object -w <file> writes the blob and prints the SHA.
        # Does NOT touch the index or working tree.
        # ------------------------------------------------------------------ #
        blob_result = _run(
            ["git", "hash-object", "-w", str(board_path)],
            cwd=root,
        )
        blob_sha = blob_result.stdout.strip()

        # ------------------------------------------------------------------ #
        # Step 2 — build a tree containing only board.md
        # git mktree reads ls-tree format from stdin; it does NOT touch the
        # real index (unlike git update-index / git write-tree which would
        # require a temp GIT_INDEX_FILE to be side-effect-free).
        # Input format: "<mode> blob <sha>\t<filename>\n"
        #
        # IMPORTANT: pass bytes (not text=True) to avoid Windows CRLF
        # translation in subprocess stdin, which would make git mktree see
        # "board.md\r" as the filename and corrupt the tree entry.
        # ------------------------------------------------------------------ #
        mktree_input_bytes = f"100644 blob {blob_sha}\tboard.md\n".encode("latin-1")
        tree_result = subprocess.run(
            ["git", "mktree"],
            input=mktree_input_bytes,
            cwd=str(root),
            capture_output=True,
            check=True,
        )
        if tree_result.returncode != 0:
            raise subprocess.CalledProcessError(
                tree_result.returncode, ["git", "mktree"],
                tree_result.stdout, tree_result.stderr,
            )
        tree_sha = tree_result.stdout.strip().decode("ascii")

        # ------------------------------------------------------------------ #
        # Step 3 — build a commit object
        # Chain onto the prior trail ref if it exists (creates history).
        # git commit-tree does NOT touch the index or working tree.
        # ------------------------------------------------------------------ #
        now_utc = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        commit_args = [
            "git",
            "commit-tree",
            tree_sha,
            "-m",
            f"kata-trail {now_utc}",
        ]
        try:
            prior_result = _run(
                ["git", "rev-parse", "--verify", _TRAIL_REF],
                cwd=root,
            )
            commit_args += ["-p", prior_result.stdout.strip()]
        except subprocess.CalledProcessError:
            pass  # No prior ref — this is the first snapshot (orphan commit)

        commit_result = _run(commit_args, cwd=root)
        commit_sha = commit_result.stdout.strip()

        # ------------------------------------------------------------------ #
        # Step 4 — atomically advance refs/kata/trail
        # Retry ONCE on a busy lock (D133 robustness invariant).
        # On a second lock failure: return skip (never raise).
        # On a non-lock error from update-ref: fall through to the outer handler.
        # ------------------------------------------------------------------ #
        for attempt in range(2):  # attempt 0 = first try; attempt 1 = retry
            try:
                _run(
                    ["git", "update-ref", _TRAIL_REF, commit_sha],
                    cwd=root,
                )
                return {"committed": commit_sha}
            except subprocess.CalledProcessError as exc:
                if _is_lock_error(exc, root):
                    if attempt == 0:
                        continue  # retry once
                    # Second lock failure — skip rather than raise
                    return {"skipped": "ref-lock"}
                # Non-lock subprocess error: fall through to outer handler
                raise

        # Unreachable (the loop always returns), but satisfies type checkers
        return {"skipped": "ref-lock"}  # pragma: no cover

    except subprocess.CalledProcessError as exc:
        # Any git plumbing error other than a handled lock failure
        return {"skipped": f"git-error: {exc.returncode} {exc.stderr.strip()!r}"}
    except OSError as exc:
        return {"skipped": f"os-error: {exc}"}
    except Exception as exc:  # noqa: BLE001
        # Belt-and-suspenders: the durability path must NEVER propagate
        return {"skipped": f"unexpected: {type(exc).__name__}: {exc}"}
