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
6. Q-16: a hung git call fails soft to a skip sentinel.

Trust-model wave 2 (cursor-durability, TM-C3/C4 · RS-L3 · R-M4 · R3-M5) adds:
7.  Snapshot CONTENT — a run-scoped snapshot carries the cursor file AND its
    pointed-to payload files (the PLAN's declared evidence test).
8.  Per-run trail refs, with the LEGACY ref provably untouched (BC).
9.  Snapshot CADENCE — PHASE/VERDICT fire; nothing else does.
10. The skip sentinel surfaced as a RECORDED, renderable event.
11. The resilience DERIVATION as a pure fold, including the load-bearing
    receipt-not-flag rule.
12. The `cursor.pushTrail` config reader (default never-push, fail-closed).
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


# ---------------------------------------------------------------------------
# Test 6 — Q-16 (2026-07-12 health review): git timeout is fail-soft (skip)
# ---------------------------------------------------------------------------


def test_snapshot_skips_on_git_timeout(tmp_path, monkeypatch):
    """Q-16: a hung git call (stale lock / credential prompt in a hostile target)
    must fail-soft to a skip sentinel — never a raise to the compaction caller and
    never a hang."""
    repo = _make_git_repo(tmp_path)
    kata_dir = repo / ".kata"
    kata_dir.mkdir()
    (kata_dir / "board.md").write_text("board content\n", encoding="utf-8")

    def _raise_timeout(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd=["git"], timeout=kata_trail._GIT_TIMEOUT_S)

    monkeypatch.setattr(kata_trail.subprocess, "run", _raise_timeout)

    result = kata_trail.snapshot_board(str(repo))
    assert "skipped" in result, f"timeout must fail-soft to a skip sentinel, got: {result}"
    assert "timeout" in result["skipped"]


# ===========================================================================
# Trust-model wave 2 — cursor durability (TM-C3/C4 · RS-L3 · R-M4 · R3-M5)
# ===========================================================================

RUN_A = "run-20260816T101500Z-a1b2c3"
RUN_B = "run-20260816T101501Z-d4e5f6"


def _seed_cursor(repo: Path, text: str = "RUN seeded\n") -> Path:
    """Create .kata/ and write the cursor file, returning its path."""
    kata_dir = repo / ".kata"
    kata_dir.mkdir(exist_ok=True)
    cursor = kata_dir / "board.md"
    cursor.write_text(text, encoding="utf-8")
    return cursor


def _seed_payload(repo: Path, run_id: str, seq: int, body: str) -> Path:
    """Write .kata/payloads/<runId>-<seq>.json (the DESIGN §2.2 convention)."""
    payload_dir = repo / ".kata" / "payloads"
    payload_dir.mkdir(parents=True, exist_ok=True)
    path = payload_dir / f"{run_id}-{seq}.json"
    path.write_text(body, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Test 7 — snapshot content: cursor + pointed-to payloads
#          (PLAN frontmatter declares THIS test as the task's evidence)
# ---------------------------------------------------------------------------


def test_snapshot_carries_cursor_and_payloads(tmp_path):
    """A VERDICT append's snapshot contains the cursor AND its payload file.

    This is TM-C4's "durable at the moment they exist" made true: the payload
    pointed to by the VERDICT line is inside the snapshot tree, not merely on
    the (tier-3, gitignored) disk cache.
    """
    repo = _make_git_repo(tmp_path)
    payload_body = '{"verdict":"PASS","evidencePointers":[],"judgeDispatchSeq":11,"runId":"%s"}\n' % RUN_A
    _seed_payload(repo, RUN_A, 12, payload_body)
    _seed_cursor(
        repo,
        f"RUN {RUN_A}\n"
        f"2026-08-16T10:15:00Z | 12 | seam | VERDICT | T1 | gate PASS "
        f"payload=.kata/payloads/{RUN_A}-12.json\n",
    )

    record = kata_trail.snapshot_on_append("VERDICT", run_id=RUN_A, repo_root=str(repo))

    assert record is not None, "a VERDICT append must fire the snapshot cadence"
    assert record["outcome"] == "committed", f"snapshot failed: {record}"
    ref = kata_trail.run_trail_ref(RUN_A)

    # The cursor file is in the snapshot
    listing = _git(["ls-tree", "-r", "--name-only", ref], repo).stdout.split()
    assert "board.md" in listing, f"cursor missing from snapshot tree: {listing}"

    # The payload is in the snapshot, with its exact content
    payload_entry = f"payloads/{RUN_A}-12.json"
    assert payload_entry in listing, f"payload missing from snapshot tree: {listing}"
    cat = _git(["cat-file", "-p", f"{ref}:{payload_entry}"], repo)
    assert cat.stdout == payload_body, (
        f"payload content mismatch.\nExpected: {payload_body!r}\nGot: {cat.stdout!r}"
    )
    assert record["payloads"] == 1, record

    # And the durability path still never dirties the repo
    status = _git(["status", "--porcelain"], repo)
    assert status.stdout.strip() == "", f"Expected clean status, got: {status.stdout!r}"


def test_snapshot_excludes_other_runs_payloads(tmp_path):
    """Run membership is honored: run A's snapshot never carries run B's payload."""
    repo = _make_git_repo(tmp_path)
    _seed_cursor(repo)
    _seed_payload(repo, RUN_A, 1, '{"a":1}\n')
    _seed_payload(repo, RUN_B, 1, '{"b":1}\n')
    # A non-conforming file in the same dir must also be ignored
    (repo / ".kata" / "payloads" / "scratch.json").write_text("{}\n", encoding="utf-8")

    result = kata_trail.snapshot_cursor(str(repo), run_id=RUN_A)

    assert "committed" in result, result
    listing = _git(
        ["ls-tree", "-r", "--name-only", kata_trail.run_trail_ref(RUN_A)], repo
    ).stdout.split()
    assert f"payloads/{RUN_A}-1.json" in listing
    assert f"payloads/{RUN_B}-1.json" not in listing
    assert "payloads/scratch.json" not in listing


# ---------------------------------------------------------------------------
# Test 8 — per-run refs (RS-L3), legacy ref untouched (BC)
# ---------------------------------------------------------------------------


def test_per_run_ref_created_and_legacy_ref_untouched(tmp_path):
    """A run-scoped snapshot creates refs/kata/trails/<runId> and never moves
    the legacy refs/kata/trail (BC — the PreCompact hook still owns that ref)."""
    repo = _make_git_repo(tmp_path)
    _seed_cursor(repo, "legacy content\n")

    # Establish the legacy ref via the legacy entry point
    legacy = kata_trail.snapshot_board(str(repo))
    assert "committed" in legacy, legacy
    legacy_sha_before = _git(["rev-parse", "refs/kata/trail"], repo).stdout.strip()

    # Now take a run-scoped snapshot with DIFFERENT content
    _seed_cursor(repo, "run-scoped content\n")
    result = kata_trail.snapshot_cursor(str(repo), run_id=RUN_A)
    assert "committed" in result, result
    assert result["ref"] == "refs/kata/trails/" + RUN_A

    # The per-run ref exists and holds the new content
    run_ref = kata_trail.run_trail_ref(RUN_A)
    assert _git(["rev-parse", "--verify", run_ref], repo, check=False).returncode == 0
    assert _git(["cat-file", "-p", f"{run_ref}:board.md"], repo).stdout == (
        "run-scoped content\n"
    )

    # The legacy ref did NOT move, and still holds the legacy content
    legacy_sha_after = _git(["rev-parse", "refs/kata/trail"], repo).stdout.strip()
    assert legacy_sha_after == legacy_sha_before, (
        "the legacy refs/kata/trail must be untouched by run-scoped snapshots"
    )
    assert _git(["cat-file", "-p", "refs/kata/trail:board.md"], repo).stdout == (
        "legacy content\n"
    )

    # Still no branch touched, still no remote
    assert _git(["remote"], repo).stdout.strip() == ""
    assert run_ref not in _branch_refs(repo)


def test_per_run_refs_are_isolated_and_chain_independently(tmp_path):
    """Two runs get two distinct refs; each chains on its OWN prior tip (no
    fan-out contention — the RS-L3 point)."""
    repo = _make_git_repo(tmp_path)
    _seed_cursor(repo, "a1\n")
    a1 = kata_trail.snapshot_cursor(str(repo), run_id=RUN_A)["committed"]
    _seed_cursor(repo, "b1\n")
    b1 = kata_trail.snapshot_cursor(str(repo), run_id=RUN_B)["committed"]
    _seed_cursor(repo, "a2\n")
    a2 = kata_trail.snapshot_cursor(str(repo), run_id=RUN_A)["committed"]

    assert len({a1, b1, a2}) == 3

    refs = _git(
        ["for-each-ref", "--format=%(refname)", "refs/kata/"], repo
    ).stdout.split()
    assert sorted(refs) == sorted(
        ["refs/kata/trails/" + RUN_A, "refs/kata/trails/" + RUN_B]
    ), refs

    # run A's second snapshot parents on run A's first — NOT on run B's
    parent = _git(["log", "--format=%P", "-1", a2], repo).stdout.strip()
    assert parent == a1, f"expected parent {a1}, got {parent}"


def test_run_trail_ref_refuses_a_malformed_run_id(tmp_path):
    """A runId reaches a git argv element, so the grammar guard is fail-closed —
    and the fail-soft snapshot path turns the refusal into a skip sentinel."""
    for bad in ["run-../../evil", "run-a b", "runX-1", "run-", "refs/heads/master", ""]:
        with pytest.raises(ValueError):
            kata_trail.run_trail_ref(bad)

    repo = _make_git_repo(tmp_path)
    _seed_cursor(repo)
    result = kata_trail.snapshot_cursor(str(repo), run_id="run-../../evil")
    assert "skipped" in result and "bad-run-id" in result["skipped"], result
    assert _git(["for-each-ref", "refs/kata/"], repo).stdout.strip() == ""


def test_cursor_path_outside_the_repo_is_refused(tmp_path):
    """The cursor is consumed as an opaque path but is still confined to the repo."""
    repo = _make_git_repo(tmp_path)
    _seed_cursor(repo)
    outsider = tmp_path / "outside.md"
    outsider.write_text("not yours\n", encoding="utf-8")

    result = kata_trail.snapshot_cursor(
        str(repo), run_id=RUN_A, cursor_path=str(outsider)
    )
    assert "skipped" in result and "bad-cursor-path" in result["skipped"], result


# ---------------------------------------------------------------------------
# Test 9 — cadence: PHASE and VERDICT only
# ---------------------------------------------------------------------------


def test_cadence_fires_only_on_phase_and_verdict(tmp_path):
    """DESIGN §2.5: the cadence fires on every PHASE and VERDICT append — and on
    nothing else (a NOTE/CLAIM/PROGRESS stream must not snapshot per line)."""
    repo = _make_git_repo(tmp_path)
    _seed_cursor(repo)

    for fires in ("PHASE", "VERDICT"):
        assert kata_trail.should_snapshot(fires) is True
        record = kata_trail.snapshot_on_append(fires, run_id=RUN_A, repo_root=str(repo))
        assert record is not None and record["outcome"] == "committed", record
        assert record["trigger"] == fires

    for quiet in ("CLAIM", "DONE", "NOTE", "PROGRESS", "SPAWN", "DECISION", "DOWN", "DENY"):
        assert kata_trail.should_snapshot(quiet) is False
        assert (
            kata_trail.snapshot_on_append(quiet, run_id=RUN_A, repo_root=str(repo))
            is None
        ), f"{quiet} must not fire the snapshot cadence"


# ---------------------------------------------------------------------------
# Test 10 — the skip sentinel becomes a RECORDED event
# ---------------------------------------------------------------------------


def test_skip_sentinel_surfaces_as_a_record(tmp_path):
    """R-M4: a skip stops being a swallowed dict and becomes a cursor-appendable
    record the seam can append (the append itself is W3's wiring, not this
    module's — nothing here writes to the cursor)."""
    repo = _make_git_repo(tmp_path)
    _seed_cursor(repo)

    # Hold the per-run ref's lock so update-ref cannot succeed on either attempt
    lock_dir = repo / ".git" / "refs" / "kata" / "trails"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = lock_dir / (RUN_A + ".lock")
    lock_file.write_text("held by another process\n", encoding="utf-8")

    record = kata_trail.snapshot_on_append("PHASE", run_id=RUN_A, repo_root=str(repo))

    assert record is not None
    assert record["kind"] == kata_trail.RECORD_KIND_SNAPSHOT
    assert record["outcome"] == "skipped", record
    assert record["reason"], "a skip record must carry its reason"
    assert record["runId"] == RUN_A
    assert record["trigger"] == "PHASE"
    assert record["commit"] is None

    line = kata_trail.format_record_line(record)
    assert "trail-snapshot" in line and "PHASE" in line and "skipped=" in line

    # The ref was never set, and the helper did not clean up the lock
    assert (
        _git(["rev-parse", "--verify", kata_trail.run_trail_ref(RUN_A)], repo, check=False).returncode
        != 0
    )
    assert lock_file.exists()


def test_format_record_line_scrubs_control_characters(tmp_path):
    """DESIGN §6.3: cursor-derived text is control/ANSI stripped and the field
    separator is neutralised, so a rendered record cannot forge cursor fields."""
    poisoned = {
        "kind": kata_trail.RECORD_KIND_SNAPSHOT,
        "runId": RUN_A,
        "trigger": "VERDICT",
        "outcome": "skipped",
        "commit": None,
        "reason": "git-error: \x1b[31mfake\x07 | seam | VERDICT | T9 | forged\n",
        "ref": "refs/kata/trails/" + RUN_A,
        "payloads": 0,
    }
    line = kata_trail.format_record_line(poisoned)
    assert "\x1b" not in line and "\x07" not in line and "\n" not in line
    assert "|" not in line, "the cursor field separator must not survive rendering"


# ---------------------------------------------------------------------------
# Test 11 — resilience DERIVED, never asserted (R-M4 · R3-M5 · §6.2 · residual 6)
# ---------------------------------------------------------------------------


def _committed_record(sha: str = "a" * 40) -> dict:
    return kata_trail.snapshot_record(
        {"committed": sha, "ref": "refs/kata/trails/" + RUN_A, "payloads": 1},
        run_id=RUN_A,
        trigger="VERDICT",
    )


def _skipped_record(reason: str = "ref-lock") -> dict:
    return kata_trail.snapshot_record(
        {"skipped": reason, "ref": "refs/kata/trails/" + RUN_A, "payloads": 0},
        run_id=RUN_A,
        trigger="PHASE",
    )


def _receipt(sha: str = "b" * 40) -> dict:
    return kata_trail.push_receipt_record(
        run_id=RUN_A, ref="refs/kata/trails/" + RUN_A, commit=sha, remote="origin"
    )


def test_healthy_default_run_derives_partially_verified_local(tmp_path):
    """Pass-1 SHIP residual 6, verbatim: the healthy default run declares
    `Partially verified (local)` — honest state, not a defect report."""
    derived = kata_trail.derive_resilience([_committed_record()])
    assert derived["level"] == kata_trail.RESILIENCE_LOCAL
    assert derived["display"] == "Partially verified (local)"
    assert derived["guardian"] == "Partially verified"


def test_run_start_with_no_records_is_local_not_degraded():
    """At run start nothing has been snapshotted yet. `degraded` is reserved for
    an OBSERVED skip; an empty record set must not read as a defect report."""
    derived = kata_trail.derive_resilience([])
    assert derived["level"] == kata_trail.RESILIENCE_LOCAL
    assert derived["display"] == "Partially verified (local)"
    assert derived["basis"] == {
        "snapshots": 0,
        "skips": 0,
        "pushReceipts": 0,
        "pushConfigured": False,
    }


def test_config_flag_without_a_receipt_still_derives_local():
    """THE load-bearing rule (DESIGN §2.5/§6.2): "full" requires a push RECEIPT
    recorded on the cursor — NEVER the config flag. A run with pushTrail set and
    no receipt is `local`, and the flag appears only as informational basis."""
    derived = kata_trail.derive_resilience(
        [_committed_record()], push_trail_configured=True
    )
    assert derived["level"] == kata_trail.RESILIENCE_LOCAL, (
        "a set cursor.pushTrail flag must NEVER raise the derived level to full"
    )
    assert derived["display"] == "Partially verified (local)"
    assert derived["basis"]["pushConfigured"] is True
    assert derived["basis"]["pushReceipts"] == 0


def test_push_receipt_derives_full():
    """A valid receipt — and only a receipt — derives `full`."""
    derived = kata_trail.derive_resilience([_committed_record(), _receipt()])
    assert derived["level"] == kata_trail.RESILIENCE_FULL
    assert derived["guardian"] == "Verified"
    assert derived["display"].startswith("Verified (full:")
    assert derived["basis"]["pushReceipts"] == 1


def test_malformed_receipt_never_raises_the_level():
    """Fail-closed: a receipt without a real 40-hex commit SHA is not evidence,
    so it cannot buy `full` (the §6.3 glyph-mimicry concern, one layer up)."""
    for bad in [
        {"kind": kata_trail.RECORD_KIND_PUSH_RECEIPT, "ref": "r", "commit": "nope"},
        {"kind": kata_trail.RECORD_KIND_PUSH_RECEIPT, "ref": "r", "commit": None},
        {"kind": kata_trail.RECORD_KIND_PUSH_RECEIPT, "commit": "c" * 40},
    ]:
        derived = kata_trail.derive_resilience([_committed_record(), bad])
        assert derived["level"] == kata_trail.RESILIENCE_LOCAL, bad


def test_a_recorded_skip_derives_degraded_even_with_a_receipt():
    """Skips dominate: a gap in the snapshot record is a gap in what survived."""
    derived = kata_trail.derive_resilience(
        [_committed_record(), _skipped_record(), _receipt()],
        push_trail_configured=True,
    )
    assert derived["level"] == kata_trail.RESILIENCE_DEGRADED
    assert derived["guardian"] == "Honor-system"
    assert derived["display"] == "Honor-system (degraded/skips detected)"
    assert derived["basis"] == {
        "snapshots": 1,
        "skips": 1,
        "pushReceipts": 1,
        "pushConfigured": True,
    }


def test_derivation_is_a_pure_fold_over_the_whole_record_stream():
    """The fold ignores unrelated cursor records, so the seam can pass the whole
    stream; and it never touches disk (pure — no repo needed anywhere above)."""
    stream = [
        {"kind": "escalation", "msg": "unrelated"},
        "not-a-dict",
        {"no": "kind"},
        _committed_record(),
    ]
    derived = kata_trail.derive_resilience(stream)
    assert derived["level"] == kata_trail.RESILIENCE_LOCAL
    assert derived["basis"]["snapshots"] == 1


# ---------------------------------------------------------------------------
# Test 12 — the cursor.pushTrail config key: default never-push, fail-closed
# ---------------------------------------------------------------------------


def test_read_push_trail_defaults_to_never_push():
    """Default never-push (BC): absent config, absent block, absent key ⇒ False."""
    assert kata_trail.read_push_trail(None) is False
    assert kata_trail.read_push_trail({}) is False
    assert kata_trail.read_push_trail({"cursor": {}}) is False
    assert kata_trail.read_push_trail({"mode": "standard"}) is False


def test_read_push_trail_reads_an_explicit_preference():
    assert kata_trail.read_push_trail({"cursor": {"pushTrail": True}}) is True
    assert kata_trail.read_push_trail({"cursor": {"pushTrail": False}}) is False


def test_read_push_trail_fails_closed_on_a_malformed_value():
    """A present-but-broken value is never silently coerced to a default
    (the kata_config.validate_core_config house rule)."""
    for bad in [
        {"cursor": "yes"},
        {"cursor": {"pushTrail": "true"}},
        {"cursor": {"pushTrail": 1}},
        {"cursor": {"pushTrail": None}},
    ]:
        with pytest.raises(ValueError):
            kata_trail.read_push_trail(bad)
    with pytest.raises(ValueError):
        kata_trail.read_push_trail(["not", "a", "dict"])


def test_no_push_path_exists_in_the_module(tmp_path):
    """"do not build any push-by-default path" — asserted structurally: the
    module's source contains no git push invocation at all, and a snapshot taken
    with the flag set still performs exactly the same local-only act."""
    source = Path(kata_trail.__file__).read_text(encoding="utf-8")
    assert '"push"' not in source and "'push'" not in source, (
        "kata_trail must contain no git push argv element"
    )

    repo = _make_git_repo(tmp_path)
    _seed_cursor(repo)
    assert kata_trail.read_push_trail({"cursor": {"pushTrail": True}}) is True
    record = kata_trail.snapshot_on_append("PHASE", run_id=RUN_A, repo_root=str(repo))
    assert record["outcome"] == "committed"
    assert _git(["remote"], repo).stdout.strip() == "", "no remote was ever configured"
    assert kata_trail.derive_resilience([record], push_trail_configured=True)[
        "level"
    ] == kata_trail.RESILIENCE_LOCAL
