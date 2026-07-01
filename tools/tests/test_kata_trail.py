"""Tests for kata_trail.py — durable board helper (B1, restore-hardening WAVE B1).

TDD discipline: written FIRST (red→green). Every test creates a real temporary git
repo via subprocess; no mocking of git internals. No network access required.

Coverage
--------
1. Helper writes a single-file commit to refs/kata/trail; git cat-file returns board
   content; repo index + working tree are CLEAN afterward (git status --porcelain empty).
2. No-op when .kata/board.md is absent (returns skip sentinel, no ref created, no raise).
3. A second snapshot creates a new commit parented on the prior refs/kata/trail
   (history chains — two successive calls produce a parent→child commit pair).
4. The helper NEVER creates/moves a branch and NEVER pushes (refs/heads/* unchanged;
   refs/kata/trail is NOT in refs/heads/).
5. Robustness: simulate a busy refs/kata/trail.lock (create the lock file) →
   retry-once-then-skip, no raise.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import kata_trail  # module under test (must be importable after kata_trail.py is created)


# ---------------------------------------------------------------------------
# Internal git helpers for test setup + verification
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command in the given directory; returns CompletedProcess."""
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=check,
    )


def _make_git_repo(tmp_path: Path) -> Path:
    """Initialize a minimal git repo with one commit and .gitignore excluding .kata/.

    The .kata/ dir is gitignored (mirrors the real KataHarness project, .gitignore:9).
    After this function returns, ``git status --porcelain`` is empty.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], repo)
    _git(["config", "user.email", "test@kata.local"], repo)
    _git(["config", "user.name", "Kata Test"], repo)
    # .kata/ is gitignored so status stays clean during tests
    (repo / ".gitignore").write_text(".kata/\n", encoding="utf-8")
    _git(["add", ".gitignore"], repo)
    _git(["commit", "-m", "init"], repo)
    return repo


def _branch_refs(repo: Path) -> frozenset[str]:
    """Return the frozenset of all refs/heads/* in the repo."""
    result = _git(["for-each-ref", "--format=%(refname)", "refs/heads/"], repo)
    return frozenset(result.stdout.strip().splitlines())


# ---------------------------------------------------------------------------
# Test 1 — single-file commit + clean status
# ---------------------------------------------------------------------------


def test_snapshot_writes_board_to_trail_ref_and_status_clean(tmp_path):
    """Helper writes board.md to refs/kata/trail; git status stays clean after.

    Verifies:
    - Return value has key "committed" with a 40-char hex SHA.
    - git cat-file -p refs/kata/trail:board.md returns the original board content.
    - git status --porcelain is empty (index + working tree untouched).
    """
    repo = _make_git_repo(tmp_path)
    kata_dir = repo / ".kata"
    kata_dir.mkdir()
    board_content = "CLAIM | worker-1 | CLAIM | T1 | starting task\n"
    (kata_dir / "board.md").write_text(board_content, encoding="utf-8")

    result = kata_trail.snapshot_board(str(repo))

    # Must return a committed SHA
    assert "committed" in result, f"Expected 'committed' key, got: {result}"
    sha = result["committed"]
    assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha), (
        f"Not a valid git SHA: {sha!r}"
    )

    # Board content must be readable from the trail ref
    cat = _git(["cat-file", "-p", "refs/kata/trail:board.md"], repo)
    assert cat.stdout == board_content, (
        f"Board content mismatch.\nExpected: {board_content!r}\nGot: {cat.stdout!r}"
    )

    # Working tree + index must be untouched (status porcelain is empty)
    status = _git(["status", "--porcelain"], repo)
    assert status.stdout.strip() == "", (
        f"Expected clean status, got: {status.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Test 2 — no-op when .kata/board.md is absent
# ---------------------------------------------------------------------------


def test_snapshot_noop_when_board_absent(tmp_path):
    """No-op + skip sentinel when .kata/board.md does not exist; no ref created.

    Verifies:
    - Return value has key "skipped" containing "no-board".
    - refs/kata/trail does not exist after the call.
    - No exception raised.
    """
    repo = _make_git_repo(tmp_path)
    # Deliberately do NOT create .kata/ or .kata/board.md

    result = kata_trail.snapshot_board(str(repo))

    assert "skipped" in result, f"Expected 'skipped' key, got: {result}"
    assert "no-board" in result["skipped"], (
        f"Expected 'no-board' in skipped reason, got: {result['skipped']!r}"
    )

    # refs/kata/trail must not have been created
    verify = _git(["rev-parse", "--verify", "refs/kata/trail"], repo, check=False)
    assert verify.returncode != 0, (
        "refs/kata/trail should not exist when board.md is absent"
    )


# ---------------------------------------------------------------------------
# Test 3 — history chains (second snapshot parents on the first)
# ---------------------------------------------------------------------------


def test_second_snapshot_parents_on_first(tmp_path):
    """Two successive snapshots produce a parent→child commit chain on refs/kata/trail.

    Verifies:
    - First and second commits have different SHAs.
    - The second commit's parent SHA equals the first commit's SHA.
    """
    repo = _make_git_repo(tmp_path)
    kata_dir = repo / ".kata"
    kata_dir.mkdir()

    # First snapshot
    (kata_dir / "board.md").write_text("snapshot 1\n", encoding="utf-8")
    r1 = kata_trail.snapshot_board(str(repo))
    assert "committed" in r1, f"First snapshot failed: {r1}"
    sha1 = r1["committed"]

    # Second snapshot with different content
    (kata_dir / "board.md").write_text("snapshot 2\n", encoding="utf-8")
    r2 = kata_trail.snapshot_board(str(repo))
    assert "committed" in r2, f"Second snapshot failed: {r2}"
    sha2 = r2["committed"]

    assert sha1 != sha2, "First and second snapshots must produce distinct commits"

    # sha2's parent must be sha1
    parent = _git(["log", "--format=%P", "-1", sha2], repo)
    assert parent.stdout.strip() == sha1, (
        f"Second commit's parent should be {sha1!r}, "
        f"but got {parent.stdout.strip()!r}"
    )


# ---------------------------------------------------------------------------
# Test 4 — never touches branches, never pushes
# ---------------------------------------------------------------------------


def test_snapshot_never_touches_branches_or_pushes(tmp_path):
    """Helper must not create or move any branch, and must not interact with remotes.

    Verifies:
    - refs/heads/* is unchanged after the call.
    - refs/kata/trail exists (the orphan ref) but is NOT in refs/heads/*.
    - No remote is configured (belt-and-suspenders: no remote = no accidental push).
    """
    repo = _make_git_repo(tmp_path)
    kata_dir = repo / ".kata"
    kata_dir.mkdir()
    (kata_dir / "board.md").write_text("DONE | worker-2 | DONE | T2 | integrated\n", encoding="utf-8")

    branches_before = _branch_refs(repo)

    result = kata_trail.snapshot_board(str(repo))
    assert "committed" in result, f"Expected committed, got: {result}"

    branches_after = _branch_refs(repo)
    assert branches_before == branches_after, (
        f"Branch refs changed!\nBefore: {branches_before}\nAfter: {branches_after}"
    )

    # The orphan ref exists but is not a branch
    trail_verify = _git(["rev-parse", "--verify", "refs/kata/trail"], repo, check=False)
    assert trail_verify.returncode == 0, "refs/kata/trail should exist after snapshot"
    assert "refs/kata/trail" not in branches_after, (
        "refs/kata/trail must NOT appear in refs/heads/*"
    )

    # No remote configured (no accidental push possible)
    remotes = _git(["remote"], repo)
    assert remotes.stdout.strip() == "", (
        f"Test repo should have no remotes, got: {remotes.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Test 5 — busy lock → retry-once-then-skip, no raise
# ---------------------------------------------------------------------------


def test_snapshot_skips_gracefully_on_busy_lock(tmp_path):
    """Simulate refs/kata/trail.lock busy → retry-once-then-skip, no exception raised.

    Setup: board.md is present and valid; the lock file is pre-created so git
    update-ref cannot acquire the lock on either attempt.

    Verifies:
    - Return value has key "skipped" (no raise).
    - refs/kata/trail does NOT exist after (update-ref never succeeded).
    - The lock file is still present (the helper did not delete it).
    """
    repo = _make_git_repo(tmp_path)
    kata_dir = repo / ".kata"
    kata_dir.mkdir()
    (kata_dir / "board.md").write_text("board content for lock test\n", encoding="utf-8")

    # Pre-create the lock file so git update-ref cannot acquire it
    lock_dir = repo / ".git" / "refs" / "kata"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = lock_dir / "trail.lock"
    lock_file.write_text("held by another process\n", encoding="utf-8")

    # Must not raise
    result = kata_trail.snapshot_board(str(repo))

    assert "skipped" in result, (
        f"Expected 'skipped' on busy lock, got: {result}"
    )

    # The ref must not have been set (update-ref never succeeded)
    verify = _git(["rev-parse", "--verify", "refs/kata/trail"], repo, check=False)
    assert verify.returncode != 0, (
        "refs/kata/trail should not exist when lock prevented update-ref"
    )

    # Lock file still in place (helper must not clean it up)
    assert lock_file.exists(), "Lock file should still exist; helper must not remove it"
