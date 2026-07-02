"""Tests for kata_restore.py — restore read (restore-hardening WAVE B2).

TDD discipline: written FIRST (red→green). Every test creates a real temporary
git repo via subprocess; no mocking of git internals.  No network access required.

Coverage
--------
(a) re-dispatch set is PLAN-minus-integration, NOT board-derived.
(b) early-wave crash ("no fewer"): T1/T2/T3 all CLAIM to the board, nothing
    integrated, tier-3 wiped → ALL of T1/T2/T3 re-dispatched (none silently dropped).
(c) reconcile ("no more"): task with an integration commit (Kata-Task trailer) is
    NOT re-dispatched even if the stale board shows CLAIM-without-DONE.
(d) finished-but-not-integrated: board DONE but NO integration commit → IS
    re-dispatched (tier-2 AUTHORITATIVE for DONE).
(e) C2 cleanup: dead worker's task/<id> branch + worktree registration cleared so
    a fresh worktree add -b task/<id> succeeds (no "already exists" collision).
(f) resume does NOT rotate the board (no .kata/board.<utc>.archive.md created).
(FIX-1a) parse_plan_tasks reads ownership: frontmatter even when headings use
    colon separators or are missing.
(FIX-1b) parse_plan_tasks raises ValueError when PLAN has no frontmatter task
    structure — never returns an empty set silently.
(FIX-2) collect_integrated_tasks bounds the scan to this run (after plan-freeze);
    prior-run Kata-Task trailers for reused task-ids are excluded.
(fold_board_parity) fold_board reproduces the canonical K3 result: earliest CLAIM
    and latest DONE per task, with correct in_flight / completed classification.
"""

from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

import kata_restore
import kata_trail


# ---------------------------------------------------------------------------
# Shared git helpers
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=check,
    )


def _make_git_repo(tmp_path: Path) -> Path:
    """Initialize a minimal git repo with one commit and .gitignore excluding .kata/."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], repo)
    _git(["config", "user.email", "test@kata.local"], repo)
    _git(["config", "user.name", "Kata Test"], repo)
    (repo / ".gitignore").write_text(".kata/\n", encoding="utf-8")
    _git(["add", ".gitignore"], repo)
    _git(["commit", "-m", "init"], repo)
    return repo


def _make_plan(repo: Path, task_ids: list[str]) -> Path:
    """Write a minimal PLAN.md with ownership: frontmatter + H4 headings.

    The frontmatter ``ownership:`` map is the authoritative task-id source
    (as required by kata-orchestrate precondition 2 and RUBRIC.md).  H4 headings
    are included for documentation but are NOT the parse target.
    """
    plan_dir = repo / ".planning"
    plan_dir.mkdir(exist_ok=True)

    # Build ownership map (each task owns an empty file list)
    ownership_str = "\n".join(f"  {tid}: []" for tid in task_ids)

    content = (
        f"---\nownership:\n{ownership_str}\n---\n\n"
        "# Test Plan\n\n"
    )
    for tid in task_ids:
        # Standard em-dash heading — present for documentation but not parsed
        content += f"#### {tid} — task description for {tid}\n\n"

    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text(content, encoding="utf-8")
    return plan_path


def _commit_plan(repo: Path) -> None:
    """Stage and commit all unstaged changes (plan file etc.)."""
    _git(["add", "."], repo)
    _git(["commit", "-m", "add plan"], repo)


def _add_integration_commit(repo: Path, branch: str, task_id: str) -> None:
    """Add an integration commit with Kata-Task trailer on the given branch."""
    _git(["checkout", branch], repo)
    artifact = repo / f"integrated_{task_id}.txt"
    artifact.write_text(f"integrated {task_id}\n", encoding="utf-8")
    _git(["add", artifact.name], repo)
    _git(
        ["commit", "-m", f"feat: integrate {task_id}\n\nKata-Task: {task_id}"],
        repo,
    )


def _write_board_and_snapshot(repo: Path, board_content: str) -> str:
    """Write board.md to .kata/ and snapshot it to refs/kata/trail.

    Returns the commit SHA from the snapshot.
    """
    kata_dir = repo / ".kata"
    kata_dir.mkdir(exist_ok=True)
    (kata_dir / "board.md").write_text(board_content, encoding="utf-8")
    result = kata_trail.snapshot_board(str(repo))
    assert "committed" in result, f"snapshot_board failed: {result}"
    return result["committed"]


def _delete_tier3(repo: Path) -> None:
    """Delete .kata/board.md to simulate a tier-3 wipe (lost session)."""
    board = repo / ".kata" / "board.md"
    if board.exists():
        board.unlink()


# ---------------------------------------------------------------------------
# Test (a) — re-dispatch set is PLAN-minus-integration, NOT board-derived
# ---------------------------------------------------------------------------


def test_redispatch_set_is_plan_minus_integration(tmp_path):
    """PLAN has T1, T2, T3.  Integration branch has T1 integrated.
    Board has T1 CLAIM-without-DONE (stale).  Tier-3 wiped.

    Re-dispatch set must be {T2, T3}.
    T1 has an integration commit → NOT re-dispatched (tier-2 wins over board CLAIM).
    Board is CORROBORATING only — it never limits the re-dispatch set.
    """
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1", "T2", "T3"])
    _commit_plan(repo)

    _git(["checkout", "-b", "integration"], repo)
    _add_integration_commit(repo, "integration", "T1")

    # Board shows T1 CLAIM-without-DONE (stale snapshot from before crash)
    board = "2024-01-01T10:00:00+00:00 | worker-1 | CLAIM | T1 | starting T1\n"
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)

    result = kata_restore.restore(
        repo_root=str(repo),
        plan_path=str(plan_path),
        integration_branch="integration",
    )

    redispatch = result["redispatch"]
    assert "T1" not in redispatch, (
        "T1 has an integration commit; tier-2 is authoritative — "
        "T1 must NOT be re-dispatched even though board shows CLAIM"
    )
    assert "T2" in redispatch, "T2 has no integration commit; must be re-dispatched"
    assert "T3" in redispatch, "T3 has no integration commit; must be re-dispatched"


# ---------------------------------------------------------------------------
# Test (b) — early-wave crash ("no fewer")
# ---------------------------------------------------------------------------


def test_early_wave_crash_no_fewer(tmp_path):
    """Wide first wave: T1/T2/T3 all CLAIM to the board, nothing integrated,
    tier-3 wiped.  Restore → ALL of T1/T2/T3 in re-dispatch set (none dropped).

    This is the critical "no fewer" proof: if re-dispatch were gated on board
    CLAIMs, a crash before any board write would silently drop tasks.  The
    PLAN-derived set contains all three regardless of board completeness.
    """
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1", "T2", "T3"])
    _commit_plan(repo)

    _git(["checkout", "-b", "integration"], repo)
    # No integration commits — wide first wave, nothing finished.

    board = (
        "2024-01-01T10:00:00+00:00 | worker-1 | CLAIM | T1 | starting T1\n"
        "2024-01-01T10:00:01+00:00 | worker-2 | CLAIM | T2 | starting T2\n"
        "2024-01-01T10:00:02+00:00 | worker-3 | CLAIM | T3 | starting T3\n"
    )
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)  # crash simulation

    result = kata_restore.restore(
        repo_root=str(repo),
        plan_path=str(plan_path),
        integration_branch="integration",
    )

    redispatch = result["redispatch"]
    assert "T1" in redispatch, "T1 must be re-dispatched (no integration commit)"
    assert "T2" in redispatch, "T2 must be re-dispatched (no integration commit)"
    assert "T3" in redispatch, "T3 must be re-dispatched (no integration commit)"
    assert len(redispatch) == 3, (
        f"All 3 PLAN tasks must be re-dispatched; got: {redispatch!r}"
    )


# ---------------------------------------------------------------------------
# Test (c) — reconcile ("no more")
# ---------------------------------------------------------------------------


def test_reconcile_no_more(tmp_path):
    """T1 has an integration commit but the stale board shows CLAIM-without-DONE.
    After restore, T1 must NOT be in the re-dispatch set (tier-2 wins).

    Scenario: T1 was integrated after the last trail snapshot (the snapshot was
    taken mid-work when T1 was in-flight); the trail board is stale — it shows
    T1 as in-flight.  Tier-2 sees the integration commit and marks T1 done.
    """
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1", "T2"])
    _commit_plan(repo)

    _git(["checkout", "-b", "integration"], repo)
    _add_integration_commit(repo, "integration", "T1")

    # Stale board: T1 CLAIM-without-DONE (snapshot pre-dates the integration commit)
    board = "2024-01-01T10:00:00+00:00 | worker-1 | CLAIM | T1 | starting T1\n"
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)

    result = kata_restore.restore(
        repo_root=str(repo),
        plan_path=str(plan_path),
        integration_branch="integration",
    )

    redispatch = result["redispatch"]
    assert "T1" not in redispatch, (
        "T1 has an integration commit; tier-2 is authoritative — "
        "must NOT be re-dispatched even with stale CLAIM-without-DONE on board"
    )
    assert "T2" in redispatch, "T2 has no integration commit; must be re-dispatched"


# ---------------------------------------------------------------------------
# Test (d) — finished-but-not-integrated IS re-dispatched
# ---------------------------------------------------------------------------


def test_done_but_not_integrated_is_redispatched(tmp_path):
    """T1 has CLAIM+DONE on the board but NO integration commit.
    T1 must be in the re-dispatch set.

    Scenario: the worker finished T1 and posted DONE, but the session died
    before the orchestrator could run the merge gate.  The board shows DONE
    but tier-2 has no integration commit, so tier-2 wins: T1 is not done.
    """
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1", "T2"])
    _commit_plan(repo)

    _git(["checkout", "-b", "integration"], repo)
    # No integration commit for T1.

    board = (
        "2024-01-01T10:00:00+00:00 | worker-1 | CLAIM | T1 | starting T1\n"
        "2024-01-01T10:30:00+00:00 | worker-1 | DONE | T1 | tests green\n"
    )
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)

    result = kata_restore.restore(
        repo_root=str(repo),
        plan_path=str(plan_path),
        integration_branch="integration",
    )

    redispatch = result["redispatch"]
    assert "T1" in redispatch, (
        "T1 has board DONE but no integration commit; "
        "tier-2 is authoritative for DONE — T1 must be re-dispatched"
    )


# ---------------------------------------------------------------------------
# Test (e) — C2 cleanup clears stale branch + worktree registration
# ---------------------------------------------------------------------------


def test_c2_cleanup_clears_stale_branch_and_worktree(tmp_path):
    """After a dead worker leaves a task/T1 branch + stale worktree registration,
    cleanup_stale_task makes a fresh 'git worktree add -b task/T1' succeed.

    Setup:
    1. Create task/T1 branch (dead worker's WIP branch).
    2. Register a worktree at a path that will be deleted (stale registration).
    3. Delete the worktree path (simulating session death).
    4. Run cleanup_stale_task(repo_root, "T1").
    5. Verify fresh worktree add -b task/T1 succeeds (no "already exists" collision).
    """
    repo = _make_git_repo(tmp_path)

    # Dead worker created task/T1 branch with WIP work.
    _git(["checkout", "-b", "task/T1"], repo)
    (repo / "task_T1_wip.txt").write_text("WIP\n", encoding="utf-8")
    _git(["add", "task_T1_wip.txt"], repo)
    _git(["commit", "-m", "wip: T1 in progress"], repo)
    _git(["checkout", "master"], repo)

    # Simulate a live (then dead) worktree: add it, then delete the path.
    dead_wt_path = tmp_path / "dead_worktree_T1"
    _git(["worktree", "add", str(dead_wt_path), "task/T1"], repo)
    shutil.rmtree(str(dead_wt_path))  # session death — path gone, .git/worktrees/* remains

    # Before cleanup: task/T1 branch exists.
    br_before = _git(["branch", "--list", "task/T1"], repo)
    assert "task/T1" in br_before.stdout, "task/T1 branch should exist before cleanup"

    # C2 cleanup
    kata_restore.cleanup_stale_task(repo_root=str(repo), task_id="T1")

    # After cleanup: a fresh worktree add -b task/T1 must succeed.
    fresh_wt = tmp_path / "fresh_worktree_T1"
    add_result = _git(
        ["worktree", "add", str(fresh_wt), "-b", "task/T1", "master"],
        repo,
        check=False,
    )
    assert add_result.returncode == 0, (
        f"After cleanup, 'git worktree add -b task/T1' must succeed.\n"
        f"stderr: {add_result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Test (f) — resume does NOT rotate the board
# ---------------------------------------------------------------------------


def test_resume_does_not_rotate_board(tmp_path):
    """restore() must NOT rotate the board.

    kata-orchestrate rotates .kata/board.md to .kata/board.<utc>.archive.md at
    run-start to keep concurrency evidence per-run.  A *resume* must skip that
    rotation: rotating would archive the recovered CLAIM/DONE lines and empty
    the live board, defeating the purpose of the restore.

    Verify:
    - No .kata/board.*.archive.md files are created.
    - .kata/board.md is restored (contains the trail board content).
    """
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1"])
    _commit_plan(repo)

    _git(["checkout", "-b", "integration"], repo)

    board_content = (
        "2024-01-01T10:00:00+00:00 | worker-1 | CLAIM | T1 | starting T1\n"
    )
    _write_board_and_snapshot(repo, board_content)
    _delete_tier3(repo)

    kata_restore.restore(
        repo_root=str(repo),
        plan_path=str(plan_path),
        integration_branch="integration",
    )

    kata_dir = repo / ".kata"
    archives = list(kata_dir.glob("board.*.archive.md"))
    assert len(archives) == 0, (
        f"restore() must NOT rotate the board; found archive files: {archives}"
    )

    # Board must be restored from the trail
    board_file = kata_dir / "board.md"
    assert board_file.exists(), ".kata/board.md must be restored after restore()"
    restored = board_file.read_text(encoding="utf-8")
    assert "CLAIM" in restored and "T1" in restored, (
        f"Restored board must contain the trail content; got: {restored!r}"
    )


# ---------------------------------------------------------------------------
# Test FIX-1a — parse_plan_tasks reads ownership: frontmatter (not headings)
# ---------------------------------------------------------------------------


def test_parse_plan_tasks_reads_frontmatter_not_headings(tmp_path):
    """FIX-1a: ownership: frontmatter is authoritative even when headings use
    colon separators (which the old _TASK_ID_RE regex silently dropped).

    The plan has ownership: {T1, T2, T3} in frontmatter.  The H4 headings
    use a colon separator (#### T1: description) which the old regex did NOT
    match (it required em/en/hyphen dash).  parse_plan_tasks must return
    {T1, T2, T3} from the frontmatter — not a partial set from the headings.
    """
    plan_dir = tmp_path / "specs" / "demo"
    plan_dir.mkdir(parents=True)

    # Frontmatter has T1, T2, T3.  Headings use colon (not a dash separator).
    content = (
        "---\n"
        "ownership:\n"
        "  T1: []\n"
        "  T2: [src/foo.py]\n"
        "  T3: [src/bar.py]\n"
        "---\n\n"
        "# Plan with colon-headings\n\n"
        "#### T1: implement foo\n\n"
        "#### T2: implement bar\n\n"
        "#### T3: write tests\n\n"
    )
    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text(content, encoding="utf-8")

    result = kata_restore.parse_plan_tasks(plan_path)

    assert "T1" in result, "T1 must be parsed from ownership: frontmatter"
    assert "T2" in result, "T2 must be parsed from ownership: frontmatter"
    assert "T3" in result, "T3 must be parsed from ownership: frontmatter"
    assert len(result) == 3, (
        f"Exactly 3 tasks expected from frontmatter; got: {result!r}"
    )


def test_parse_plan_tasks_reads_frontmatter_with_missing_headings(tmp_path):
    """FIX-1a (variant): ownership: frontmatter tasks are returned even when
    no matching H4 headings exist at all (heading-scraping fallback is absent).
    """
    plan_dir = tmp_path / "specs" / "demo"
    plan_dir.mkdir(parents=True)

    # Frontmatter only — no H4 headings in the document body
    content = (
        "---\n"
        "ownership:\n"
        "  A1: []\n"
        "  A2: []\n"
        "---\n\n"
        "# Plan (no task headings below)\n\n"
        "Some prose only.\n"
    )
    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text(content, encoding="utf-8")

    result = kata_restore.parse_plan_tasks(plan_path)

    assert result == {"A1", "A2"}, (
        f"Tasks must come from frontmatter ownership: only; got: {result!r}"
    )


# ---------------------------------------------------------------------------
# Test FIX-1b — parse_plan_tasks raises when no frontmatter task structure
# ---------------------------------------------------------------------------


def test_parse_plan_tasks_raises_on_missing_frontmatter(tmp_path):
    """FIX-1b: PLAN with NO YAML frontmatter → parse_plan_tasks raises ValueError.

    The old code would fall back to heading scraping and return a partial set
    (or empty set), causing silent under-dispatch.  The fix hard-fails instead.
    """
    plan_dir = tmp_path / "specs" / "demo"
    plan_dir.mkdir(parents=True)

    # No frontmatter — only headings (the old heading-scraping format)
    content = (
        "# Heading-Only Plan\n\n"
        "#### T1 — task one\n\n"
        "#### T2 — task two\n\n"
    )
    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="refusing to under-dispatch"):
        kata_restore.parse_plan_tasks(plan_path)


def test_parse_plan_tasks_raises_on_frontmatter_without_task_keys(tmp_path):
    """FIX-1b (variant): PLAN with frontmatter but no ownership/waves/depends_on
    keys → parse_plan_tasks raises ValueError (empty task set is not acceptable).
    """
    plan_dir = tmp_path / "specs" / "demo"
    plan_dir.mkdir(parents=True)

    content = (
        "---\n"
        "title: A plan with no task structure\n"
        "status: FROZEN\n"
        "---\n\n"
        "#### T1 — this task has no frontmatter entry\n\n"
    )
    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="refusing to under-dispatch"):
        kata_restore.parse_plan_tasks(plan_path)


def test_parse_plan_tasks_raises_on_unreadable_plan(tmp_path):
    """R-1: a provided-but-unreadable plan_path (missing/moved file) must RAISE,
    not fall through to an empty task set."""
    missing = tmp_path / "specs" / "gone" / "PLAN.md"
    with pytest.raises(ValueError, match="cannot read frozen PLAN"):
        kata_restore.parse_plan_tasks(missing)


def test_restore_raises_on_unreadable_plan_no_silent_underdispatch(tmp_path):
    """R-1 (end-to-end): a lost-run restore() with an unreadable plan_path must
    hard-fail — NEVER return lost_run=True with an empty re-dispatch set."""
    repo = _make_git_repo(tmp_path)
    _make_plan(repo, ["T1", "T2"])
    _commit_plan(repo)
    _git(["checkout", "-b", "integration"], repo)

    board = "2024-01-01T10:00:00+00:00 | worker-1 | CLAIM | T1 | starting T1\n"
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)  # lost-run condition

    with pytest.raises(ValueError, match="cannot read frozen PLAN"):
        kata_restore.restore(
            repo_root=str(repo),
            plan_path=str(repo / "specs" / "does-not-exist" / "PLAN.md"),
            integration_branch="integration",
        )


# ---------------------------------------------------------------------------
# Test FIX-2 — collect_integrated_tasks bounded to this run (fork-point)
# ---------------------------------------------------------------------------


def test_collect_integrated_tasks_bounded_by_plan_freeze(tmp_path):
    """FIX-2: prior-run Kata-Task: B1 trailer (before plan-freeze) is excluded
    by the fork-point bound; only this run's T2 integration is found.

    Topology (linear, all on integration branch):
        init → prior_B1_commit → plan_freeze_commit → this_run_T2_commit

    The fork-point = plan_freeze_commit (last commit touching PLAN.md).
    Bounded scan = plan_freeze..integration → contains only T2.
    B1 is an ancestor of the fork-point → excluded.

    A full restore() call then proves B1 IS re-dispatched (the prior-run trailer
    no longer causes under-dispatch on a re-entrant / version-up run).
    """
    repo = _make_git_repo(tmp_path)

    # Put everything on integration branch (linear history)
    _git(["checkout", "-b", "integration"], repo)

    # Prior-run: integrate B1 (before this run's PLAN is frozen)
    prior_artifact = repo / "prior_b1.txt"
    prior_artifact.write_text("prior run B1 done\n", encoding="utf-8")
    _git(["add", "prior_b1.txt"], repo)
    _git(["commit", "-m", "feat: prior-run integrate B1\n\nKata-Task: B1"], repo)

    # Freeze the PLAN for the current run — this commit is the fork-point.
    # Current run's PLAN has B1 and T2 as its task-ids (B1 is a reused short label).
    plan_path = _make_plan(repo, ["B1", "T2"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN for current run"], repo)

    # This run integrates only T2 (not B1)
    t2_artifact = repo / "integrated_t2.txt"
    t2_artifact.write_text("integrated T2\n", encoding="utf-8")
    _git(["add", "integrated_t2.txt"], repo)
    _git(["commit", "-m", "feat: integrate T2\n\nKata-Task: T2"], repo)

    # --- Verify collect_integrated_tasks (bounded scan) ---
    integrated = kata_restore.collect_integrated_tasks(
        repo_root=str(repo),
        integration_branch="integration",
        plan_path=str(plan_path),
    )
    assert "T2" in integrated, "T2 was integrated in this run; must be in integrated set"
    assert "B1" not in integrated, (
        "B1 was integrated in a prior run (before the plan-freeze commit); "
        "bounded scan must exclude it — prior-run trailers must not affect this run"
    )

    # --- Verify full restore() re-dispatches B1 (not under-dispatched) ---
    board = (
        "2024-01-01T10:00:00+00:00 | worker-1 | CLAIM | B1 | starting B1\n"
        "2024-01-01T10:00:01+00:00 | worker-2 | CLAIM | T2 | starting T2\n"
    )
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)

    result = kata_restore.restore(
        repo_root=str(repo),
        plan_path=str(plan_path),
        integration_branch="integration",
    )

    assert result["lost_run"] is True
    redispatch = result["redispatch"]
    assert "B1" in redispatch, (
        "B1 is in the current PLAN but was NOT integrated in this run; "
        "must be re-dispatched — proves the prior-run trailer no longer "
        "causes silent under-dispatch"
    )
    assert "T2" not in redispatch, (
        "T2 was integrated in this run (Kata-Task: T2 after plan-freeze); "
        "must NOT be re-dispatched"
    )


# ---------------------------------------------------------------------------
# Test fold_board_parity — canonical K3 reduce: earliest CLAIM, latest DONE
# ---------------------------------------------------------------------------


def test_fold_board_parity_canonical_reduce():
    """fold_board reproduces the documented K3 canonical reduce result.

    Canonical rule (protocol/board.md K3):
    - earliest CLAIM per task = true in-flight start (survives re-dispatch spans)
    - latest DONE per task = true in-flight end
    - in_flight = tasks with a CLAIM but no DONE
    - completed = tasks with both a CLAIM and a DONE

    A small fixture exercises all four invariants to guard against drift from
    the canonical snippet (K3 — single source of truth).
    """
    board = (
        # T1: two CLAIMs (re-dispatched), two DONEs — earliest/latest must be selected
        "2024-01-01T10:00:00+00:00 | worker-1 | CLAIM | T1 | first dispatch\n"
        "2024-01-01T10:05:00+00:00 | worker-2 | CLAIM | T1 | re-dispatched claim\n"
        "2024-01-01T10:10:00+00:00 | worker-1 | DONE  | T1 | first done attempt\n"
        "2024-01-01T10:15:00+00:00 | worker-2 | DONE  | T1 | latest done\n"
        # T2: only CLAIM, no DONE → in_flight
        "2024-01-01T09:00:00+00:00 | worker-3 | CLAIM | T2 | only claim\n"
        # Corrupted/non-ISO row — must be silently skipped (never abort)
        "not-a-timestamp | worker-x | CLAIM | T3 | bad row\n"
    )

    frontier = kata_restore.fold_board(board)

    # T1: earliest CLAIM = 10:00 (not 10:05)
    assert frontier["starts"]["T1"] == datetime.fromisoformat(
        "2024-01-01T10:00:00+00:00"
    ), "earliest CLAIM must be 10:00 (K3 canonical reduce)"

    # T1: latest DONE = 10:15 (not 10:10)
    assert frontier["ends"]["T1"] == datetime.fromisoformat(
        "2024-01-01T10:15:00+00:00"
    ), "latest DONE must be 10:15 (K3 canonical reduce)"

    # T1: owner = worker-1 (owner of the first/earliest CLAIM)
    assert frontier["owners"]["T1"] == "worker-1", (
        "owner must be agent of the earliest CLAIM"
    )

    # T1: CLAIM + DONE → completed; NOT in_flight
    assert "T1" in frontier["completed"], "T1 has CLAIM+DONE → completed"
    assert "T1" not in frontier["in_flight"], "T1 has DONE → not in_flight"

    # T2: CLAIM with no DONE → in_flight; NOT completed
    assert "T2" in frontier["in_flight"], "T2 has only CLAIM → in_flight"
    assert "T2" not in frontier["completed"], "T2 has no DONE → not completed"

    # T3: corrupted row skipped — must not appear in frontier
    assert "T3" not in frontier["starts"], "corrupted row must be silently skipped"
    assert "T3" not in frontier["in_flight"]


# ---------------------------------------------------------------------------
# Freeze/Float M1-P1 — durable trailer substrate (builds_against union +
# Kata-Invalidated subtract + Kata-Supersede parser).  Additive/BC.
# ---------------------------------------------------------------------------

def _make_plan_with_builds_against(
    repo: Path, ownership_ids: list[str], builds_against: dict[str, list[str]]
) -> Path:
    """PLAN whose frontmatter has ownership: + builds_against: (M1-L2 union target)."""
    plan_dir = repo / ".planning"
    plan_dir.mkdir(exist_ok=True)
    own = "\n".join(f"  {t}: []" for t in ownership_ids)
    ba = "\n".join(
        f"  {t}:\n" + "\n".join(f"    - {e}" for e in edges)
        for t, edges in builds_against.items()
    )
    content = f"---\nownership:\n{own}\nbuilds_against:\n{ba}\n---\n\n# Plan\n"
    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text(content, encoding="utf-8")
    return plan_path


def _add_invalidation_commit(repo: Path, branch: str, task_id: str) -> None:
    """Add a re-open commit carrying a Kata-Invalidated: trailer (M1-L3/F5)."""
    _git(["checkout", branch], repo)
    art = repo / f"invalidated_{task_id}.txt"
    art.write_text(f"reopened {task_id}\n", encoding="utf-8")
    _git(["add", art.name], repo)
    _git(["commit", "-m", f"chore: re-open {task_id}\n\nKata-Invalidated: {task_id}"], repo)


def _add_supersede_commit(repo: Path, branch: str, cid: str, new_hash: str) -> None:
    """Add a commit carrying a Kata-Supersede: <id>@<hash> trailer (M1-L3/L8)."""
    _git(["checkout", branch], repo)
    art = repo / f"supersede_{cid}_{new_hash}.txt"
    art.write_text("surface change\n", encoding="utf-8")
    _git(["add", art.name], repo)
    _git(["commit", "-m", f"chore: supersede {cid}\n\nKata-Supersede: {cid}@{new_hash}"], repo)


# --- Slice A: parse_plan_tasks unions builds_against keys ----------------------

def test_parse_plan_tasks_unions_builds_against(tmp_path):
    # A contract-only dependent (D1) appears ONLY under builds_against — it must be in
    # the task set or restore silently drops it (M1-L2).  Mutation: drop the union
    # block → D1 missing → this test goes red.
    repo = _make_git_repo(tmp_path)
    plan = _make_plan_with_builds_against(repo, ["P1"], {"D1": ["C1@abcd1234"]})
    ids = kata_restore.parse_plan_tasks(plan)
    assert ids == {"P1", "D1"}


def test_parse_plan_tasks_no_builds_against_is_bc(tmp_path):
    # BC: a PLAN with no builds_against yields exactly the ownership keys (unchanged).
    repo = _make_git_repo(tmp_path)
    plan = _make_plan(repo, ["A1", "A2"])
    assert kata_restore.parse_plan_tasks(plan) == {"A1", "A2"}


# --- Slice B: collect_integrated_tasks subtracts Kata-Invalidated --------------

def test_collect_integrated_subtracts_invalidated(tmp_path):
    # T1 integrated then invalidated (crash mid-invalidation) → NOT in integrated set
    # (⇒ re-dispatched).  T2 (untouched) stays.  Mutation: `return integrated` instead
    # of `integrated - invalidated` → T1 present → this test goes red.
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1", "T2"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_integration_commit(repo, "integration", "T1")
    _add_integration_commit(repo, "integration", "T2")
    _add_invalidation_commit(repo, "integration", "T1")

    integrated = kata_restore.collect_integrated_tasks(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    assert "T2" in integrated
    assert "T1" not in integrated, "invalidated integrated task must be subtracted"


def test_collect_integrated_no_invalidated_is_bc(tmp_path):
    # BC: with no Kata-Invalidated trailer, the integrated set is the pre-P1 result.
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1", "T2"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_integration_commit(repo, "integration", "T1")
    integrated = kata_restore.collect_integrated_tasks(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    assert integrated == {"T1"}


def test_restore_redispatches_invalidated_integrated_task(tmp_path):
    # Crash mid-invalidation: T1 has BOTH Kata-Task: and Kata-Invalidated: → restore
    # must re-dispatch it (the durable trailer survives the .kata/ wipe).  T2 stays done.
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1", "T2"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_integration_commit(repo, "integration", "T1")
    _add_integration_commit(repo, "integration", "T2")
    _add_invalidation_commit(repo, "integration", "T1")

    board = (
        "2024-01-01T10:00:00+00:00 | worker-1 | CLAIM | T1 | starting T1\n"
        "2024-01-01T10:00:01+00:00 | worker-2 | CLAIM | T2 | starting T2\n"
    )
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)

    result = kata_restore.restore(
        repo_root=str(repo), plan_path=str(plan), integration_branch="integration"
    )
    assert result["lost_run"] is True
    assert "T1" in result["redispatch"], "invalidated integrated task must be re-opened"
    assert "T2" not in result["redispatch"], "T2 integrated, not invalidated → done"


def test_collect_integrated_surfaces_malformed_invalidated(tmp_path, capsys):
    # A malformed Kata-Invalidated trailer (multi-token, task-id unrecoverable) cannot
    # be subtracted → the task stays integrated (the documented LOW under-dispatch
    # vector; P2's final gate is the fail-closed authority per DESIGN M1-L9).  It must
    # be SURFACED, never silently swallowed.
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_integration_commit(repo, "integration", "T1")
    # Malformed: strict regex requires a lone token; "T1 oops extra" has spaces.
    art = repo / "bad_inv.txt"
    art.write_text("x\n", encoding="utf-8")
    _git(["add", art.name], repo)
    _git(["commit", "-m", "chore: bad reopen\n\nKata-Invalidated: T1 oops extra"], repo)

    integrated = kata_restore.collect_integrated_tasks(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    assert "T1" in integrated, "malformed trailer cannot subtract — task stays (documented)"
    out = capsys.readouterr().out
    assert "malformed Kata-Invalidated" in out, "malformed trailer must be surfaced, not silent"


# --- Slice C: parse_supersede_trailers (provided in P1, consumed by P2) --------

def test_parse_supersede_trailers_basic(tmp_path):
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_supersede_commit(repo, "integration", "C1", "abcd1234ef")
    out = kata_restore.parse_supersede_trailers(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    assert out == {"C1": "abcd1234ef"}


def test_parse_supersede_trailers_lowercases_hash(tmp_path):
    # Hash normalized to lowercase to match contract_edges._EDGE_RE's lowercase-hex pin.
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_supersede_commit(repo, "integration", "C1", "ABCD1234")
    out = kata_restore.parse_supersede_trailers(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    assert out == {"C1": "abcd1234"}


def test_parse_supersede_trailers_most_recent_wins(tmp_path):
    # Two supersedes of C1; git log is newest-first, so the most-recent hash wins.
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_supersede_commit(repo, "integration", "C1", "11111111")
    _add_supersede_commit(repo, "integration", "C1", "22222222")
    out = kata_restore.parse_supersede_trailers(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    assert out == {"C1": "22222222"}


def test_parse_supersede_trailers_empty_when_none(tmp_path):
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_integration_commit(repo, "integration", "T1")
    out = kata_restore.parse_supersede_trailers(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    assert out == {}


# --- Adval fold (2026-07-02): P1-F1..F4, F8 -------------------------------------

def _invalidation_body_commit(repo: Path, branch: str, body: str, tag: str) -> None:
    """Commit an arbitrary trailer body onto the integration branch."""
    _git(["checkout", branch], repo)
    art = repo / f"body_{tag}.txt"
    art.write_text("x\n", encoding="utf-8")
    _git(["add", art.name], repo)
    _git(["commit", "-m", body], repo)


def test_collect_integrated_space_before_colon_is_surfaced(tmp_path, capsys):
    # P1-F1: `Kata-Invalidated : T1` (key-whitespace variant) previously missed BOTH
    # regexes and vanished SILENTLY (under-dispatch, no NOTE). It must now either
    # subtract (tolerant strict match — over-dispatch-safe) or be loudly surfaced.
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_integration_commit(repo, "integration", "T1")
    _invalidation_body_commit(
        repo, "integration", "chore: re-open T1\n\nKata-Invalidated : T1", "sp"
    )
    integrated = kata_restore.collect_integrated_tasks(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    out = capsys.readouterr().out
    assert "T1" not in integrated or "Kata-Invalidated" in out, (
        "a whitespace-variant invalidation trailer must never vanish silently"
    )
    # with the tolerant strict regex the subtract itself happens (safe direction)
    assert "T1" not in integrated


def test_collect_integrated_notes_phantom_invalidation_id(tmp_path, capsys):
    # P1-F2: an invalidation id that never matched ANY integration trailer (typo /
    # case-variant / comma-joined) is the under-dispatch signature — loud NOTE.
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_integration_commit(repo, "integration", "T1")
    _add_invalidation_commit(repo, "integration", "t1")  # case-variant: matches nothing
    integrated = kata_restore.collect_integrated_tasks(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    out = capsys.readouterr().out
    assert integrated == {"T1"}  # the subtract itself finds no match (verbatim ids)
    assert "no matching Kata-Task" in out and "'t1'" in out


def test_parse_supersede_trailers_raises_on_git_error(tmp_path):
    # P1-F3 (HIGH): a git error must RAISE, never return {} — to the P2 gate {}
    # means "no supersede this run" and would vacuously PASS the coverage audit
    # (D136/M1-L9 silent-permissive default).
    repo = _make_git_repo(tmp_path)  # no 'integration' branch exists
    with pytest.raises(ValueError, match="refusing to report"):
        kata_restore.parse_supersede_trailers(
            repo_root=str(repo), integration_branch="integration"
        )


def test_parse_supersede_trailers_surfaces_malformed(tmp_path, capsys):
    # P1-F4: a malformed supersede (bad hash length / non-hex) must be surfaced,
    # never silently invisible to the P2 coverage audit.
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _invalidation_body_commit(
        repo, "integration", "chore: supersede\n\nKata-Supersede: C1@dead", "short"
    )
    got = kata_restore.parse_supersede_trailers(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    out = capsys.readouterr().out
    assert got == {}
    assert "malformed Kata-Supersede" in out


def test_parse_plan_tasks_builds_against_only_plan(tmp_path):
    # F8(5): a PLAN whose ONLY task source is builds_against passes the
    # not-empty gate (no spurious refusing-to-under-dispatch raise).
    repo = _make_git_repo(tmp_path)
    plan_dir = repo / ".planning"
    plan_dir.mkdir(exist_ok=True)
    plan = plan_dir / "PLAN.md"
    plan.write_text(
        "---\nbuilds_against:\n  D1:\n    - C1@abcd1234\n---\n\n# Plan\n",
        encoding="utf-8",
    )
    assert kata_restore.parse_plan_tasks(plan) == {"D1"}


def test_parse_plan_tasks_scalar_builds_against_is_bc_noop(tmp_path):
    # F8(6): builds_against present but not a dict ⇒ no-op union (BC), and the
    # remaining maps still provide the task set.
    repo = _make_git_repo(tmp_path)
    plan_dir = repo / ".planning"
    plan_dir.mkdir(exist_ok=True)
    plan = plan_dir / "PLAN.md"
    plan.write_text(
        "---\nownership:\n  A1: []\nbuilds_against: nonsense\n---\n\n# Plan\n",
        encoding="utf-8",
    )
    assert kata_restore.parse_plan_tasks(plan) == {"A1"}


def test_fold_board_ignores_progress_lines():
    # F8(7): a PROGRESS heartbeat line (F3) must never enter starts/ends/owners —
    # the board reduce is CLAIM/DONE only (corroboration stays uncorrupted).
    board = (
        "2026-07-02T10:00:00 | w1 | CLAIM | T1 | starting\n"
        "2026-07-02T10:05:00 | w1 | PROGRESS | T1 | 1/3 modules\n"
        "2026-07-02T10:06:00 | w2 | PROGRESS | T9 | 2/2 modules\n"
    )
    folded = kata_restore.fold_board(board)
    assert set(folded["starts"]) == {"T1"}
    assert folded["ends"] == {}
    assert "T9" not in folded["owners"]
    assert folded["in_flight"] == frozenset({"T1"})
