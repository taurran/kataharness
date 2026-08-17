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

import kata_board
import kata_restore
import kata_trail

# ---------------------------------------------------------------------------
# Cursor fixtures — built through the canonical EMITTER, never hand-typed
# ---------------------------------------------------------------------------
# DESIGN §2.2: the legacy 5-field grammar parses NOWHERE after the migration, so a
# legacy board fixture that still folded would prove the migration never happened.
# Every board fixture below therefore goes through kata_board.format_header /
# format_line.  Legacy strings survive ONLY inside the refusal tests.

_RUN_ID = "run-20240101T100000Z-beef0003"

#: A LEGACY 5-field CLAIM line — kept only to be REFUSED.
LEGACY_LINE = "2024-01-01T10:00:00+00:00 | worker-1 | CLAIM | T1 | starting T1"


def _cursor(*rows: tuple[str, str, str, str, str], run_id: str = _RUN_ID) -> str:
    """Build a cursor from ``(utc, agent, TYPE, task, msg)`` rows; seq stamped 1..N."""
    header = kata_board.format_header(kata_board.RunHeader(run_id=run_id))
    return header + "".join(
        kata_board.format_line(
            utc=utc, seq=i, agent=agent, type=typ, task=task, msg=msg
        )
        for i, (utc, agent, typ, task, msg) in enumerate(rows, start=1)
    )


def _claim(utc: str, agent: str, task: str, msg: str = "starting") -> tuple[str, str, str, str, str]:
    return (utc, agent, "CLAIM", task, msg)


def _done(utc: str, agent: str, task: str, msg: str = "verify passed") -> tuple[str, str, str, str, str]:
    return (utc, agent, "DONE", task, msg)


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


def _branch_names(repo: Path) -> set[str]:
    """Return the set of local branch names (strips the '* <current>' marker)."""
    out = _git(["branch", "--list"], repo).stdout
    names: set[str] = set()
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("* "):
            line = line[2:]
        names.add(line.strip())
    return names


def _make_task_branch(repo: Path, task_id: str) -> None:
    """Create a live task/<task_id> branch with one WIP commit, off master."""
    _git(["checkout", "master"], repo)
    _git(["checkout", "-b", f"task/{task_id}"], repo)
    wip = repo / f"{task_id}_wip.txt"
    wip.write_text(f"WIP {task_id}\n", encoding="utf-8")
    _git(["add", wip.name], repo)
    _git(["commit", "-m", f"wip: {task_id} in progress"], repo)
    _git(["checkout", "master"], repo)


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
    board = _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"))
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

    board = _cursor(
        _claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"),
        _claim("2024-01-01T10:00:01+00:00", "worker-2", "T2", "starting T2"),
        _claim("2024-01-01T10:00:02+00:00", "worker-3", "T3", "starting T3"),
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
    board = _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"))
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

    board = _cursor(
        _claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"),
        _done("2024-01-01T10:30:00+00:00", "worker-1", "T1", "tests green"),
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

    board_content = _cursor(
        _claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"),
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

    board = _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"))
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
    board = _cursor(
        _claim("2024-01-01T10:00:00+00:00", "worker-1", "B1", "starting B1"),
        _claim("2024-01-01T10:00:01+00:00", "worker-2", "T2", "starting T2"),
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

    Canonical rule (protocol/cursor.md K3):
    - earliest CLAIM per task = true in-flight start (survives re-dispatch spans)
    - latest DONE per task = true in-flight end
    - in_flight = tasks with a CLAIM but no DONE
    - completed = tasks with both a CLAIM and a DONE

    A small fixture exercises all four invariants to guard against drift from
    the canonical snippet (K3 — single source of truth).  Fold semantics are
    UNCHANGED by the cursor migration; only the parser moved (DESIGN §2.2).
    """
    board = _cursor(
        # T1: two CLAIMs (re-dispatched), two DONEs — earliest/latest must be selected
        _claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "first dispatch"),
        _claim("2024-01-01T10:05:00+00:00", "worker-2", "T1", "re-dispatched claim"),
        _done("2024-01-01T10:10:00+00:00", "worker-1", "T1", "first done attempt"),
        _done("2024-01-01T10:15:00+00:00", "worker-2", "T1", "latest done"),
        # T2: only CLAIM, no DONE → in_flight
        _claim("2024-01-01T09:00:00+00:00", "worker-3", "T2", "only claim"),
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


def test_fold_board_refuses_a_corrupted_row_instead_of_skipping_it():
    """A non-ISO / corrupted row is now a REFUSAL, not a silent skip (DESIGN §2.2).

    This REPLACES the pre-migration behaviour ("corrupted row must be silently
    skipped").  A silently skipped row is an invisible hole in the audit trail —
    the class the cursor contract exists to remove.
    """
    board = (
        _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "ok"))
        + "not-a-timestamp | 2 | worker-x | CLAIM | T3 | bad row\n"
    )
    with pytest.raises(kata_board.CursorParseError, match="not ISO-8601"):
        kata_restore.fold_board(board)


def test_fold_board_refuses_a_legacy_5_field_line():
    """MIGRATION PROOF: the LEGACY grammar parses NOWHERE, including here."""
    board = _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "ok")) + LEGACY_LINE + "\n"
    with pytest.raises(kata_board.CursorParseError, match="LEGACY 5-field"):
        kata_restore.fold_board(board)


def test_fold_board_refuses_a_headerless_cursor():
    """A cursor is ``run-header line*``; a headerless board has no run identity."""
    headerless = kata_board.format_line(
        utc="2024-01-01T10:00:00+00:00",
        seq=1,
        agent="worker-1",
        type="CLAIM",
        task="T1",
        msg="ok",
    )
    with pytest.raises(kata_board.CursorParseError, match="must open with 'RUN"):
        kata_restore.fold_board(headerless)


def test_fold_board_empty_content_is_absence_not_refusal():
    """The Q-14 board-unreadable fail-soft passes "" — that folds to an EMPTY frontier."""
    for empty in ("", "   ", "\n\n"):
        frontier = kata_restore.fold_board(empty)
        assert frontier["starts"] == {}
        assert frontier["ends"] == {}
        assert frontier["owners"] == {}
        assert frontier["in_flight"] == frozenset()
        assert frontier["completed"] == frozenset()


def test_fold_board_does_not_misread_seq_as_agent():
    """MIGRATION PROOF: owners come from the AGENT field, never from ``seq``.

    The pre-migration hand-rolled split read the new grammar's ``seq`` as the
    agent — so every owner would have been the string ``"1"``, silently.
    """
    board = _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "ok"))
    frontier = kata_restore.fold_board(board)
    assert frontier["owners"]["T1"] == "worker-1"
    assert "T1" in frontier["in_flight"]


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

    board = _cursor(
        _claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"),
        _claim("2024-01-01T10:00:01+00:00", "worker-2", "T2", "starting T2"),
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
    board = _cursor(
        ("2026-07-02T10:00:00", "w1", "CLAIM", "T1", "starting"),
        ("2026-07-02T10:05:00", "w1", "PROGRESS", "T1", "1/3 modules"),
        ("2026-07-02T10:06:00", "w2", "PROGRESS", "T9", "2/2 modules"),
    )
    folded = kata_restore.fold_board(board)
    assert set(folded["starts"]) == {"T1"}
    assert folded["ends"] == {}
    assert "T9" not in folded["owners"]
    assert folded["in_flight"] == frozenset({"T1"})


# ---------------------------------------------------------------------------
# P0.1 U2 — structured degraded signal (collect_integrated_tasks_ex + restore keys)
# ---------------------------------------------------------------------------


def test_collect_ex_bounded_not_degraded(tmp_path):
    """Bounded scan (fork-point resolves) ⇒ degraded False, reasons empty."""
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1", "T2"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_integration_commit(repo, "integration", "T1")

    ex = kata_restore.collect_integrated_tasks_ex(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    assert ex["tasks"] == {"T1"}
    assert ex["degraded"] is False
    assert ex["reasons"] == []


def test_collect_ex_unbounded_fallback_degraded(tmp_path, capsys):
    """Unbounded fallback (fork-point unresolvable) ⇒ degraded True + reason.

    MUTATION PROOF anchor (degraded-flag guard): dropping the
    ``reasons.append("integration-scan-unbounded")`` in
    ``_scan_integration_commit_bodies`` makes this test go RED (degraded False).
    """
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    _add_integration_commit(repo, "integration", "T1")
    # PLAN exists on disk but is NEVER committed to integration → the fork-point
    # (last commit touching the plan path) is unresolvable → unbounded fallback.
    plan = _make_plan(repo, ["T1"])

    ex = kata_restore.collect_integrated_tasks_ex(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    assert ex["tasks"] == {"T1"}
    assert ex["degraded"] is True
    assert "integration-scan-unbounded" in ex["reasons"]
    # the verbatim NOTE print still fires at its current site (BC)
    assert "integration scan is UNBOUNDED" in capsys.readouterr().out


def test_collect_ex_git_error_integration_history_unreadable(tmp_path):
    """Git error (lines is None) ⇒ empty set + 'integration-history-unreadable' (MED-2)."""
    repo = _make_git_repo(tmp_path)  # no 'integration' branch exists
    ex = kata_restore.collect_integrated_tasks_ex(
        repo_root=str(repo), integration_branch="integration", plan_path=None
    )
    assert ex["tasks"] == set()
    assert ex["degraded"] is True
    assert ex["reasons"] == ["integration-history-unreadable"]


def test_collect_delegation_is_byte_identical(tmp_path):
    """collect_integrated_tasks returns exactly collect_integrated_tasks_ex()['tasks']."""
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)
    plan = _make_plan(repo, ["T1", "T2"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN"], repo)
    _add_integration_commit(repo, "integration", "T1")
    _add_integration_commit(repo, "integration", "T2")

    plain = kata_restore.collect_integrated_tasks(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    ex = kata_restore.collect_integrated_tasks_ex(
        repo_root=str(repo), integration_branch="integration", plan_path=str(plan)
    )
    assert plain == ex["tasks"] == {"T1", "T2"}


def test_restore_carries_degraded_keys_on_empty_path(tmp_path):
    """LOW-5: the non-lost-run _empty early return carries degraded=False + []."""
    repo = _make_git_repo(tmp_path)  # no refs/kata/trail ⇒ not a lost run
    result = kata_restore.restore(repo_root=str(repo))
    assert result["lost_run"] is False
    assert result["degraded"] is False
    assert result["degraded_reasons"] == []


def test_restore_carries_degraded_keys_on_lost_run(tmp_path):
    """restore() carries the additive degraded keys on the lost-run path too."""
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1", "T2"])
    _commit_plan(repo)
    _git(["checkout", "-b", "integration"], repo)
    _add_integration_commit(repo, "integration", "T1")

    board = _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"))
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)

    result = kata_restore.restore(
        repo_root=str(repo),
        plan_path=str(plan_path),
        integration_branch="integration",
    )
    assert result["lost_run"] is True
    assert "degraded" in result and "degraded_reasons" in result
    assert isinstance(result["degraded"], bool)
    assert isinstance(result["degraded_reasons"], list)


def test_collect_integrated_checkpoint_trailers_are_inert(tmp_path):
    """L19 sweep LOW-6 (M4 seam pin): worker Kata-Checkpoint trailer bodies, made
    reachable in the integration scan by a --no-ff merge, must NOT enter the
    integrated set (they match neither the strict Kata-Task regex nor the loose
    prefix detectors) and must NOT be surfaced as malformed.

    Topology: plan-freeze on integration -> worker branch with a checkpoint
    commit (Kata-Checkpoint trailer, per the M4-P0 cadence) -> --no-ff merge
    carrying the Kata-Task trailer (the orchestrator's integration commit).
    """
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "integration"], repo)

    plan_path = _make_plan(repo, ["T1", "T2"])
    _git(["add", "."], repo)
    _git(["commit", "-m", "chore: freeze PLAN for current run"], repo)

    # Worker task branch: one M4 checkpoint commit (worker-authored trailer body).
    _git(["checkout", "-b", "task/T1"], repo)
    (repo / "t1_module.txt").write_text("module 1\n", encoding="utf-8")
    _git(["add", "t1_module.txt"], repo)
    _git(
        [
            "commit",
            "-m",
            "feat: t1 module 1\n\n"
            'Kata-Checkpoint: {"v":1,"i":0,"verify":{"exit":0,"passed":3,'
            '"failed":0},"evidence":"deadbeef"}',
        ],
        repo,
    )

    # Orchestrator integrates via --no-ff merge (checkpoint body now reachable
    # in the fork..integration %B walk).
    _git(["checkout", "integration"], repo)
    _git(["merge", "--no-ff", "task/T1", "-m", "feat: integrate T1\n\nKata-Task: T1"], repo)

    integrated = kata_restore.collect_integrated_tasks(
        repo_root=str(repo),
        integration_branch="integration",
        plan_path=str(plan_path),
    )
    # ONLY T1 (from the orchestrator's Kata-Task trailer). The worker's
    # Kata-Checkpoint body contributed nothing: no phantom ids, no malformed
    # surfacing, no under-dispatch of T2.
    assert integrated == {"T1"}

    ex = kata_restore.collect_integrated_tasks_ex(
        repo_root=str(repo),
        integration_branch="integration",
        plan_path=str(plan_path),
    )
    assert ex["tasks"] == {"T1"}
    assert ex["degraded"] is False


# ---------------------------------------------------------------------------
# DET-02 / DET-03 (2026-07-12 health review) — git-config pins on parsed stdout
# ---------------------------------------------------------------------------


def _pin_present(cmd: list[str], setting: str) -> bool:
    """True iff ``-c <setting>`` appears in *cmd* (the pinned-argv shape)."""
    return any(cmd[i] == "-c" and cmd[i + 1] == setting for i in range(len(cmd) - 1))


def test_scan_commit_bodies_argv_pins_bounded(tmp_path, monkeypatch):
    """DET-02: the fork-point `git log -1 -- <plan>` must pin log.follow=false
    (single-pathspec shape activates operator log.follow=true → an OLDER
    fork point → prior-run trailers ingested → under-dispatch) plus
    log.showSignature=false / core.quotepath=off. DET-03: the bounded %B scan
    must pin log.showSignature=false (gpg: lines pollute the parsed body stream)."""
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if "-1" in cmd:  # fork-point resolution
            return subprocess.CompletedProcess(cmd, 0, stdout="abc123\n", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(kata_restore.subprocess, "run", fake_run)
    lines, reasons = kata_restore._scan_integration_commit_bodies(
        str(tmp_path), "integration", tmp_path / "PLAN.md"
    )
    assert lines == [] and reasons == []

    assert len(calls) == 2, "expected exactly fork-point + bounded-scan git calls"
    fork_cmd, scan_cmd = calls
    assert _pin_present(fork_cmd, "log.follow=false")
    assert _pin_present(fork_cmd, "log.showSignature=false")
    assert _pin_present(fork_cmd, "core.quotepath=off")
    assert _pin_present(scan_cmd, "log.showSignature=false")
    assert _pin_present(scan_cmd, "core.quotepath=off")


def test_scan_commit_bodies_argv_pins_unbounded_fallback(tmp_path, monkeypatch, capsys):
    """DET-03: the unbounded-fallback %B scan (fork-point unresolvable) carries
    the same showSignature/quotepath pins as the bounded scan."""
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(kata_restore.subprocess, "run", fake_run)
    lines, reasons = kata_restore._scan_integration_commit_bodies(
        str(tmp_path), "integration", tmp_path / "PLAN.md"
    )
    assert lines == []
    assert "integration-scan-unbounded" in reasons  # the degraded path was taken

    scan_cmd = calls[-1]
    assert _pin_present(scan_cmd, "log.showSignature=false")
    assert _pin_present(scan_cmd, "core.quotepath=off")


# ---------------------------------------------------------------------------
# Q-16 (2026-07-12 health review) — git subprocess timeouts fail closed/degraded
# ---------------------------------------------------------------------------


def _raise_timeout(*_a, **_k):
    raise subprocess.TimeoutExpired(cmd=["git"], timeout=kata_restore._GIT_TIMEOUT_S)


def test_ref_exists_timeout_returns_false(tmp_path, monkeypatch):
    """Q-16: a hung `git rev-parse` ⇒ _ref_exists returns False (never hangs), so
    detect_lost_run treats the trail as absent — never a success-shaped True."""
    monkeypatch.setattr(kata_restore.subprocess, "run", _raise_timeout)
    assert kata_restore._ref_exists(Path(tmp_path), kata_restore._TRAIL_REF) is False


def test_scan_forkpoint_timeout_falls_back_unbounded(tmp_path, monkeypatch, capsys):
    """Q-16: a hung fork-point resolution ⇒ the module's existing degraded path
    (unbounded fallback, over-dispatch-safe) — NOT a hang, NOT a wrong fork bound."""
    def fake_run(cmd, **kwargs):
        if "-1" in cmd:  # fork-point resolution hangs
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=kata_restore._GIT_TIMEOUT_S)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(kata_restore.subprocess, "run", fake_run)
    lines, reasons = kata_restore._scan_integration_commit_bodies(
        str(tmp_path), "integration", tmp_path / "PLAN.md"
    )
    assert lines == []
    assert "integration-scan-unbounded" in reasons  # degraded, never a wrong bound


def test_scan_main_scan_timeout_history_unreadable(tmp_path, monkeypatch):
    """Q-16: a hung bounded %B scan ⇒ (None, reasons) ⇒ collect_ex reports the MOST
    degraded path (empty set + integration-history-unreadable), never a success set."""
    def fake_run(cmd, **kwargs):
        if "-1" in cmd:  # fork-point resolves
            return subprocess.CompletedProcess(cmd, 0, stdout="abc123\n", stderr="")
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=kata_restore._GIT_TIMEOUT_S)

    monkeypatch.setattr(kata_restore.subprocess, "run", fake_run)
    ex = kata_restore.collect_integrated_tasks_ex(
        str(tmp_path), "integration", plan_path=tmp_path / "PLAN.md"
    )
    assert ex["tasks"] == set()
    assert ex["degraded"] is True
    assert ex["reasons"] == ["integration-history-unreadable"]


def test_read_board_from_trail_timeout_raises(tmp_path, monkeypatch):
    """Q-16: a hung `git cat-file` read RAISES TimeoutExpired (never returns a
    success-shaped empty board); restore()'s fail-soft handler maps it to degraded."""
    monkeypatch.setattr(kata_restore.subprocess, "run", _raise_timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        kata_restore.read_board_from_trail(str(tmp_path))


def test_cleanup_stale_task_timeout_is_swallowed(tmp_path, monkeypatch):
    """Q-16: a hung worktree-prune / branch-delete during cleanup is best-effort —
    swallowed so restore continues (never raises to the caller, never hangs)."""
    monkeypatch.setattr(kata_restore.subprocess, "run", _raise_timeout)
    kata_restore.cleanup_stale_task(str(tmp_path), "T1")  # must not raise


# ---------------------------------------------------------------------------
# Q-14 (2026-07-12 health review) — board-unreadable degraded signal
# ---------------------------------------------------------------------------


def test_restore_board_unreadable_sets_degraded(tmp_path, monkeypatch):
    """Q-14: when the orphan-trail board read raises, restore() must set degraded=True
    and append 'board-unreadable' (never a silent empty frontier) and still COMPLETE.

    MUTATION PROOF: dropping the ``board_unreadable`` branch in restore() makes this
    test go RED (degraded False / reason absent) while direction stays safe."""
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1", "T2"])
    _commit_plan(repo)
    _git(["checkout", "-b", "integration"], repo)
    _add_integration_commit(repo, "integration", "T1")

    board = _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"))
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)  # lost-run condition

    # Board read raises (a Q-16 timeout or a corrupt ref) — restore must degrade, not
    # crash, and must not silently drop the loss.
    def _boom(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd=["git", "cat-file"], timeout=60)

    monkeypatch.setattr(kata_restore, "read_board_from_trail", _boom)

    result = kata_restore.restore(
        repo_root=str(repo), plan_path=str(plan_path), integration_branch="integration"
    )
    assert result["lost_run"] is True
    assert result["degraded"] is True
    assert "board-unreadable" in result["degraded_reasons"]
    # Board corroborates but never gates: the re-dispatch set is still
    # PLAN-minus-integration despite the empty frontier.
    assert "T2" in result["redispatch"] and "T1" not in result["redispatch"]
    assert result["board_content"] == ""


def test_restore_board_unparseable_sets_degraded(tmp_path):
    """The cursor migration's refusal is RECORDED at restore(), never a silent drop.

    A LEGACY 5-field board recovered from the trail no longer folds (DESIGN §2.2).
    restore()'s degraded-mode contract is tolerate-and-continue — the board
    corroborates and never gates — but the loss must be VISIBLE, exactly like the
    Q-14 board-unreadable loss.

    MUTATION PROOF: dropping the ``board_unparseable`` branch in restore() makes this
    test go RED (degraded False / reason absent) while direction stays safe.
    """
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1", "T2"])
    _commit_plan(repo)
    _git(["checkout", "-b", "integration"], repo)
    _add_integration_commit(repo, "integration", "T1")

    _write_board_and_snapshot(repo, LEGACY_LINE + "\n")
    _delete_tier3(repo)  # lost-run condition

    result = kata_restore.restore(
        repo_root=str(repo), plan_path=str(plan_path), integration_branch="integration"
    )
    assert result["lost_run"] is True
    assert result["degraded"] is True
    assert "board-unparseable" in result["degraded_reasons"]
    # Empty frontier, but the raw recovered content is NOT destroyed.
    assert result["board_frontier"]["starts"] == {}
    assert "CLAIM" in result["board_content"]
    # Board corroborates but never gates: direction stays PLAN-minus-integration.
    assert "T2" in result["redispatch"] and "T1" not in result["redispatch"]


def test_restore_new_grammar_board_is_not_degraded(tmp_path):
    """Control for the test above: a NEW-grammar cursor folds cleanly, no refusal."""
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1", "T2"])
    _commit_plan(repo)
    _git(["checkout", "-b", "integration"], repo)
    _add_integration_commit(repo, "integration", "T1")

    _write_board_and_snapshot(
        repo, _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"))
    )
    _delete_tier3(repo)

    result = kata_restore.restore(
        repo_root=str(repo), plan_path=str(plan_path), integration_branch="integration"
    )
    assert "board-unparseable" not in result["degraded_reasons"]
    assert result["board_frontier"]["owners"] == {"T1": "worker-1"}


# ---------------------------------------------------------------------------
# Session-lifecycle hardening (grill/session-lifecycle) — fail-closed cleanup
# on a degraded scan (A) + salvage-rename instead of force-delete (B).
# ---------------------------------------------------------------------------


def test_degraded_scan_skips_cleanup_no_branch_mutation(tmp_path):
    """(A) Case 1: a degraded scan (missing integration branch) must perform NO
    destructive/mutating action on any task/* branch.  Live task branches
    survive untouched and cleanup_skipped reports exactly what was skipped.

    Before the fix, `degraded` was computed but never consulted at the step-4
    call site — cleanup_stale_task ran for every re-dispatch task regardless
    of degraded, and (pre-fix) cleanup_stale_task force-deleted the branch via
    `git branch -D`.  On a repo where 'integration' never exists, EVERY plan
    task lands in the re-dispatch set (empty integrated set), so every
    task/<id> branch used to be destroyed.
    """
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1", "T2", "T3"])
    _commit_plan(repo)

    # Live task branches for T1, T2, T3 — simulate in-flight worker WIP.
    # Deliberately no 'integration' branch is ever created — this forces the
    # git-error / integration-history-unreadable degraded path.
    for tid in ["T1", "T2", "T3"]:
        _make_task_branch(repo, tid)

    board = _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"))
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)

    result = kata_restore.restore(
        repo_root=str(repo),
        plan_path=str(plan_path),
        integration_branch="integration",  # never created ⇒ degraded scan
    )

    assert result["degraded"] is True
    assert "integration-history-unreadable" in result["degraded_reasons"]

    branches = _branch_names(repo)
    for tid in ["T1", "T2", "T3"]:
        assert f"task/{tid}" in branches, (
            f"task/{tid} must survive a degraded scan untouched; branches: {branches!r}"
        )
    assert not any(b.startswith("kata-salvage/") for b in branches), (
        "no salvage rename should occur either — cleanup is skipped whole-cloth "
        "on a degraded scan, not just the destructive half of it"
    )
    assert set(result["cleanup_skipped"]) == {"T1", "T2", "T3"}


def test_bl_m21_default_integration_branch_missing_survives(tmp_path):
    """(A) Case 2 — the end-to-end BL-M21 scenario from the defect report:
    restore() called with the DEFAULT integration_branch ('integration'),
    which does not exist in this repo.  Live task/* branches must survive.
    """
    repo = _make_git_repo(tmp_path)
    plan_path = _make_plan(repo, ["T1", "T2"])
    _commit_plan(repo)

    # No 'integration' branch created at all — this repo never had one.
    for tid in ["T1", "T2"]:
        _make_task_branch(repo, tid)

    board = _cursor(_claim("2024-01-01T10:00:00+00:00", "worker-1", "T1", "starting T1"))
    _write_board_and_snapshot(repo, board)
    _delete_tier3(repo)

    # integration_branch NOT passed — exercises the "integration" default.
    result = kata_restore.restore(repo_root=str(repo), plan_path=str(plan_path))

    assert result["lost_run"] is True
    assert result["degraded"] is True

    branches = _branch_names(repo)
    assert "task/T1" in branches and "task/T2" in branches, (
        f"default integration_branch='integration' missing must not force-delete "
        f"live task branches; branches: {branches!r}"
    )
    assert set(result["cleanup_skipped"]) == {"T1", "T2"}


def test_cleanup_salvage_preserves_commit(tmp_path):
    """(B) Case 4: the original task/<id> tip commit stays reachable from the
    salvage branch after cleanup_stale_task renames the name away.
    """
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "task/T1"], repo)
    (repo / "wip.txt").write_text("wip\n", encoding="utf-8")
    _git(["add", "wip.txt"], repo)
    _git(["commit", "-m", "wip: T1"], repo)
    tip_sha = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    _git(["checkout", "master"], repo)

    kata_restore.cleanup_stale_task(repo_root=str(repo), task_id="T1")

    branches = _branch_names(repo)
    assert "task/T1" not in branches, "task/T1 name must be freed by cleanup"
    salvage = {b for b in branches if b.startswith("kata-salvage/T1-")}
    assert len(salvage) == 1, f"expected exactly one salvage branch; got: {salvage!r}"
    salvage_name = next(iter(salvage))

    log_out = _git(["log", salvage_name, "--format=%H"], repo).stdout.splitlines()
    assert tip_sha in log_out, (
        f"original tip commit {tip_sha} must be reachable from {salvage_name} "
        f"(commit is preserved, not destroyed); log: {log_out!r}"
    )


def test_cleanup_stale_task_idempotent_second_call_is_noop(tmp_path):
    """(B) Case 5: running cleanup_stale_task twice on the same task_id is a
    no-op the second time (branch already salvaged / gone) and never raises.
    """
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "task/T1"], repo)
    (repo / "wip.txt").write_text("wip\n", encoding="utf-8")
    _git(["add", "wip.txt"], repo)
    _git(["commit", "-m", "wip: T1"], repo)
    _git(["checkout", "master"], repo)

    kata_restore.cleanup_stale_task(repo_root=str(repo), task_id="T1")  # 1st call
    after_first = _branch_names(repo)
    assert "task/T1" not in after_first
    assert len({b for b in after_first if b.startswith("kata-salvage/T1-")}) == 1

    kata_restore.cleanup_stale_task(repo_root=str(repo), task_id="T1")  # 2nd call — must not raise
    after_second = _branch_names(repo)
    assert after_second == after_first, (
        "a second cleanup_stale_task call on an already-salvaged task must be a "
        f"pure no-op; branches before={after_first!r} after={after_second!r}"
    )


def test_cleanup_stale_task_salvage_name_is_deterministic(tmp_path):
    """(B) Case 6: the salvage branch name is a pure function of (task_id, tip
    SHA) — Determinism Doctrine law 7 (no clock/random/counter).  Calling
    cleanup_stale_task twice on identical inputs (same task_id, same tip
    commit) must compute the exact same salvage name both times.

    If naming were non-deterministic (e.g. a timestamp or random suffix
    baked into the name), recreating task/T1 at the SAME commit and salvaging
    again would produce a SECOND, differently-named salvage branch instead of
    deterministically colliding with the first (which is treated as
    already-salvaged, per the idempotency contract).
    """
    repo = _make_git_repo(tmp_path)
    _git(["checkout", "-b", "task/T1"], repo)
    (repo / "wip.txt").write_text("wip\n", encoding="utf-8")
    _git(["add", "wip.txt"], repo)
    _git(["commit", "-m", "wip: T1"], repo)
    tip_sha = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    _git(["checkout", "master"], repo)

    kata_restore.cleanup_stale_task(repo_root=str(repo), task_id="T1")
    first_salvage = {b for b in _branch_names(repo) if b.startswith("kata-salvage/T1-")}
    assert len(first_salvage) == 1
    name1 = next(iter(first_salvage))

    # Recreate task/T1 at the EXACT SAME commit (identical task_id + tip sha).
    _git(["branch", "task/T1", tip_sha], repo)
    kata_restore.cleanup_stale_task(repo_root=str(repo), task_id="T1")  # must not raise

    second_salvage = {b for b in _branch_names(repo) if b.startswith("kata-salvage/T1-")}
    assert second_salvage == {name1}, (
        "identical (task_id, tip sha) inputs must always compute the SAME "
        f"salvage name; got {second_salvage!r}, expected {{{name1!r}}}"
    )


# ---------------------------------------------------------------------------
# BL-F01 — plan_status / assert_frozen: freeze becomes a recorded, checked state
# ---------------------------------------------------------------------------
#
# Parse rule under test (see kata_restore.plan_status docstring): the `status:` value is
# split on whitespace and the FIRST WORD is taken, case-folded. This is what lets the real
# `.planning/specs/dispatch-authoring/PLAN.md` value at the time BL-F01 was written —
# `status: DRAFT — awaiting freeze-gate (...)` — parse as "draft" rather than raising. The
# alternative rule (value must be exactly the token) was rejected because it would hard-fail
# on that live authoring shape; see test_plan_status_live_draft_value_with_trailing_prose_parses_as_draft.


def _write_plan_with_status(tmp_path, status_line):
    """A minimal PLAN.md whose frontmatter contains exactly the given `status:` line(s)."""
    plan_dir = tmp_path / "specs" / "demo"
    plan_dir.mkdir(parents=True)
    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text(f"---\ntitle: t\n{status_line}\n---\n\n# Plan\n", encoding="utf-8")
    return plan_path


def test_plan_status_absent_is_not_frozen(tmp_path):
    """No `status:` key at all ⇒ "absent", never a silent "frozen" default (D45/GB12/D136)."""
    plan_dir = tmp_path / "specs" / "demo"
    plan_dir.mkdir(parents=True)
    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text("---\ntitle: t\n---\n\n# Plan\n", encoding="utf-8")

    assert kata_restore.plan_status(plan_path) == "absent"
    with pytest.raises(ValueError, match="not frozen"):
        kata_restore.assert_frozen(plan_path)


def test_plan_status_unknown_value_raises(tmp_path):
    """A garbled/unrecognized status must RAISE — never coerce to a default."""
    plan_path = _write_plan_with_status(tmp_path, "status: banana")
    with pytest.raises(ValueError, match="unrecognized status"):
        kata_restore.plan_status(plan_path)
    with pytest.raises(ValueError, match="unrecognized status"):
        kata_restore.assert_frozen(plan_path)


def test_plan_status_draft_is_not_frozen(tmp_path):
    plan_path = _write_plan_with_status(tmp_path, "status: draft")
    assert kata_restore.plan_status(plan_path) == "draft"
    with pytest.raises(ValueError, match="not frozen"):
        kata_restore.assert_frozen(plan_path)


def test_plan_status_frozen_is_frozen(tmp_path):
    plan_path = _write_plan_with_status(tmp_path, "status: frozen")
    assert kata_restore.plan_status(plan_path) == "frozen"
    kata_restore.assert_frozen(plan_path)  # must NOT raise


def test_plan_status_is_case_insensitive(tmp_path):
    frozen_upper = _write_plan_with_status(tmp_path / "a", "status: FROZEN")
    assert kata_restore.plan_status(frozen_upper) == "frozen"

    draft_mixed = _write_plan_with_status(tmp_path / "b", "status: DrAfT")
    assert kata_restore.plan_status(draft_mixed) == "draft"


def test_plan_status_live_draft_value_with_trailing_prose_parses_as_draft(tmp_path):
    """Pins the chosen parse rule against the EXACT historical value carried by
    `.planning/specs/dispatch-authoring/PLAN.md` when BL-F01 was assessed:

        status: DRAFT — awaiting freeze-gate (conductor applies protocol/authored-artifact-gate.md, defined in
          this build's own DESIGN.md, to this very PLAN before freezing it)

    That file's `status:` is being set to `frozen` as part of this same change (the work it
    describes shipped), so this test freezes the historical value as a fixture instead of
    reading the live file — it must keep parsing as "draft", not raise, under the
    first-word rule.
    """
    plan_path = _write_plan_with_status(
        tmp_path,
        "status: DRAFT — awaiting freeze-gate (conductor applies protocol/authored-artifact-gate.md, defined in\n"
        "  this build's own DESIGN.md, to this very PLAN before freezing it)",
    )
    assert kata_restore.plan_status(plan_path) == "draft"
    with pytest.raises(ValueError, match="not frozen"):
        kata_restore.assert_frozen(plan_path)


# ---------------------------------------------------------------------------
# TM-F1 / R-M9 — the per-task `evidence:` declaration (trust-model wave 2)
#
# `parse_plan_tasks` gains a keyword-only `check_evidence` flag (default OFF, so every
# existing caller's contract is untouched) and a companion `parse_plan_evidence` that
# CARRIES the map.  DESIGN §5.1: no plan item freezes without its completion-evidence
# declaration; DESIGN §3.5: the declaration grammar is closed to three forms.
# ---------------------------------------------------------------------------

import evidence_grammar

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TRUST_MODEL_PLAN = _REPO_ROOT / ".planning" / "specs" / "trust-model" / "PLAN.md"


def _write_plan_with_evidence(tmp_path: Path, evidence_block: str) -> Path:
    plan_dir = tmp_path / "specs" / "demo"
    plan_dir.mkdir(parents=True)
    content = (
        "---\n"
        "status: frozen\n"
        "ownership:\n"
        "  T1: [src/a.py]\n"
        "  T2: [src/b.py]\n"
        f"{evidence_block}"
        "---\n\n"
        "# Demo plan\n"
    )
    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text(content, encoding="utf-8")
    return plan_path


def test_parse_plan_tasks_default_ignores_evidence_backcompat(tmp_path):
    """BC: the pre-TM-F1 contract is unchanged — no evidence: map, no complaint.

    Every existing caller (kata_restore.restore's own step 3, and any orchestrator
    reading the task set) calls this positionally with no keyword.  If the check were
    on by default, every plan authored before the rule would stop parsing.
    """
    plan_path = _write_plan_with_evidence(tmp_path, "")
    assert kata_restore.parse_plan_tasks(plan_path) == {"T1", "T2"}


def test_parse_plan_tasks_check_evidence_accepts_a_declared_plan(tmp_path):
    plan_path = _write_plan_with_evidence(
        tmp_path,
        "evidence:\n"
        '  T1: ["artifact:src/a.py"]\n'
        '  T2: ["test:tests/test_b.py::test_b"]\n',
    )
    assert kata_restore.parse_plan_tasks(plan_path, check_evidence=True) == {"T1", "T2"}


def test_parse_plan_tasks_check_evidence_fails_a_task_with_no_declaration(tmp_path):
    """A PLAN with a task missing `evidence:` FAILS the extended check (TM-F1)."""
    plan_path = _write_plan_with_evidence(
        tmp_path, "evidence:\n  T1: [\"artifact:src/a.py\"]\n"
    )
    with pytest.raises(evidence_grammar.EvidenceGrammarError, match="T2"):
        kata_restore.parse_plan_tasks(plan_path, check_evidence=True)


def test_parse_plan_tasks_check_evidence_fails_an_absent_evidence_map(tmp_path):
    plan_path = _write_plan_with_evidence(tmp_path, "")
    with pytest.raises(evidence_grammar.EvidenceGrammarError, match="no per-task"):
        kata_restore.parse_plan_tasks(plan_path, check_evidence=True)


@pytest.mark.parametrize(
    "declaration",
    [
        "uv run pytest tests/test_b.py",   # freeform command string
        "test:../../etc/test_x.py::test_y",  # CWE-23 traversal
        "artifact:../../../etc/passwd",      # CWE-23 traversal
        "probe:not-registered-anywhere",     # unregistered probe
    ],
)
def test_parse_plan_tasks_check_evidence_fails_a_grammar_invalid_declaration(
    tmp_path, declaration
):
    plan_path = _write_plan_with_evidence(
        tmp_path,
        "evidence:\n"
        '  T1: ["artifact:src/a.py"]\n'
        f'  T2: ["{declaration}"]\n',
    )
    with pytest.raises(evidence_grammar.EvidenceGrammarError):
        kata_restore.parse_plan_tasks(plan_path, check_evidence=True)


def test_evidence_grammar_error_is_a_valueerror_for_existing_callers(tmp_path):
    """Fail-closed callers that catch ValueError keep catching this one."""
    plan_path = _write_plan_with_evidence(tmp_path, "evidence:\n  T1: [\"make test\"]\n")
    with pytest.raises(ValueError):
        kata_restore.parse_plan_tasks(plan_path, check_evidence=True)


def test_parse_plan_evidence_carries_the_map(tmp_path):
    plan_path = _write_plan_with_evidence(
        tmp_path,
        "evidence:\n"
        '  T1: ["artifact:src/a.py"]\n'
        '  T2: ["test:tests/test_b.py::test_b", "probe:gauntlet"]\n',
    )
    carried = kata_restore.parse_plan_evidence(plan_path)
    assert list(carried) == ["T1", "T2"]
    assert [d.form for d in carried["T2"]] == ["test", "probe"]
    assert carried["T1"][0].value == "src/a.py"


def test_parse_plan_evidence_raises_the_same_frontmatter_messages(tmp_path):
    """The evidence reader shares `parse_plan_tasks`' frontmatter failure contract."""
    plan_dir = tmp_path / "specs" / "demo"
    plan_dir.mkdir(parents=True)
    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text("# no frontmatter here\n", encoding="utf-8")
    with pytest.raises(ValueError, match="refusing to under-dispatch"):
        kata_restore.parse_plan_evidence(plan_path)
    with pytest.raises(ValueError, match="cannot read frozen PLAN"):
        kata_restore.parse_plan_evidence(plan_dir / "ABSENT.md")


# --- The reflexive TM-F1 acceptance ----------------------------------------


def test_this_burns_own_frozen_plan_passes_the_evidence_check():
    """REFLEXIVE TM-F1: the first PLAN authored under the rule validates under the rule.

    Run against the REAL frozen plan on disk, not a fixture — a machinery that only ever
    sees its own fixtures is exactly the vacuity this burn exists to end.  If this fails,
    either the plan is undeclared or the grammar is wrong; both are loud.
    """
    assert _TRUST_MODEL_PLAN.is_file(), f"missing frozen PLAN: {_TRUST_MODEL_PLAN}"
    carried = kata_restore.parse_plan_evidence(_TRUST_MODEL_PLAN)
    task_ids = kata_restore.parse_plan_tasks(_TRUST_MODEL_PLAN)
    assert set(carried) == task_ids, "every frozen task carries a declaration"
    assert carried, "the frozen plan declares evidence"
    forms = {d.form for decls in carried.values() for d in decls}
    assert forms <= {"artifact", "test", "probe"}
    # All three forms are exercised by the real plan — the grammar is not a
    # two-thirds-dead surface pinned by a one-form corpus.
    assert forms == {"artifact", "test", "probe"}


def test_this_burns_own_frozen_plan_passes_via_the_extended_parse_plan_tasks():
    assert kata_restore.parse_plan_tasks(
        _TRUST_MODEL_PLAN, check_evidence=True
    ) == kata_restore.parse_plan_tasks(_TRUST_MODEL_PLAN)


def test_every_frozen_plan_test_declaration_compiles_to_the_design_argv():
    """Every `test:` node in the real plan compiles to the pinned DESIGN §3.5 argv."""
    carried = kata_restore.parse_plan_evidence(_TRUST_MODEL_PLAN)
    seen = 0
    for decls in carried.values():
        for decl in decls:
            if decl.form != "test":
                continue
            compiled = evidence_grammar.compile_declaration(decl, repo_root=_REPO_ROOT)
            assert compiled.argv == ("python", "-m", "pytest", decl.value)
            seen += 1
    assert seen > 0, "the frozen plan declares at least one test: node"
