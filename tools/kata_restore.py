"""kata_restore.py — restore read (restore-hardening WAVE B2).

Implements the five-step restore flow from DESIGN §2 B3:

1. detect_lost_run      — tier-3 cache absent/stale AND refs/kata/trail present.
2. read_board_from_trail + fold_board — read the durable board from the orphan ref;
   fold to a frontier view with the canonical concurrency reduce (protocol/board.md).
3. compute_redispatch_set — re-dispatch set = frozen PLAN tasks MINUS tasks with an
   integration commit (mapped via the Kata-Task: trailer in each integration commit).
   The folded board CORROBORATES in-flight ownership but NEVER gates the set.
4. cleanup_stale_task   — git worktree prune + delete the stale task/<id> branch so
   a fresh re-dispatch cannot collide.  Half-written artifacts are discarded.
5. restore (top-level)  — orchestrates steps 1–4 and writes the board back to
   .kata/board.md WITHOUT rotation (no archive file).

STDLIB + subprocess(git) + yaml (pyyaml, a tools dependency); no validate_skills.

Invariants (DESIGN §2 B3 / §0 C2 / §0 L1):
- Re-dispatch set = PLAN-derived, never board-derived.
- Board corroborates, never gates.
- Tier-2 (integration history) is AUTHORITATIVE for DONE.
- Cleanup discards half-written artifacts; never re-attaches.
- Resume never rotates the board.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Union

import yaml


# ---------------------------------------------------------------------------
# Ref constant (mirrors kata_trail.py)
# ---------------------------------------------------------------------------

_TRAIL_REF = "refs/kata/trail"


# ---------------------------------------------------------------------------
# Step 1 — detect a lost run
# ---------------------------------------------------------------------------


def detect_lost_run(repo_root: str = ".") -> dict[str, Any]:
    """Detect whether a lost-run condition is present.

    A lost run is defined as: tier-3 cache (.kata/board.md) absent or stale
    AND refs/kata/trail is present (there is a durable board to restore from).

    Returns
    -------
    dict
        ``{"lost": True,  "reason": "board-absent-trail-present"}``  — lost run.
        ``{"lost": False, "reason": "no-trail"}``                     — no trail; cannot restore.
        ``{"lost": False, "reason": "board-present"}``                — board exists; normal run.
    """
    root = Path(repo_root).resolve()
    board_path = root / ".kata" / "board.md"

    # Check refs/kata/trail
    trail_present = _ref_exists(root, _TRAIL_REF)

    if not trail_present:
        return {"lost": False, "reason": "no-trail"}

    if not board_path.exists() or board_path.stat().st_size == 0:
        return {"lost": True, "reason": "board-absent-trail-present"}

    return {"lost": False, "reason": "board-present"}


def _ref_exists(root: Path, ref: str) -> bool:
    """Return True when the given git ref resolves successfully."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=str(root),
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


# ---------------------------------------------------------------------------
# Step 2 — read the durable board and fold to a frontier view
# ---------------------------------------------------------------------------


def read_board_from_trail(repo_root: str = ".") -> str:
    """Read board.md from refs/kata/trail via git cat-file.

    Returns
    -------
    str
        The raw board content as stored in the orphan ref.

    Raises
    ------
    subprocess.CalledProcessError
        When refs/kata/trail or board.md is absent in the ref.
    """
    root = Path(repo_root).resolve()
    result = subprocess.run(
        ["git", "cat-file", "-p", f"{_TRAIL_REF}:board.md"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


# canonical reduce — keep in lockstep with protocol/board.md (K3)
def fold_board(board_content: str) -> dict[str, Any]:
    """Fold the board to a frontier view using the canonical concurrency reduce.

    Implements the canonical snippet from ``protocol/board.md`` (K3 — single
    source of truth for the concurrency reduce logic).  Pure function — no
    filesystem access.

    The reduce pairs the earliest CLAIM (true in-flight start) and the latest
    DONE (true in-flight end) per task, exactly as the canonical snippet does,
    to correctly span re-dispatched tasks.  Non-ISO / corrupted rows are skipped
    (never raise).

    Returns
    -------
    dict
        ``{
            "starts":    {task_id: datetime},   # earliest CLAIM per task
            "ends":      {task_id: datetime},   # latest DONE per task
            "owners":    {task_id: str},         # agent of first CLAIM per task
            "in_flight": frozenset[str],         # CLAIM but no DONE (corroborating)
            "completed": frozenset[str],         # both CLAIM and DONE (corroborating)
        }``

    The board CORROBORATES in-flight ownership but NEVER gates the re-dispatch
    set (DESIGN §2 B3 step 3 / Gap-table row 3).
    """
    starts: dict[str, datetime] = {}
    ends:   dict[str, datetime] = {}
    owner:  dict[str, str]      = {}

    for raw in board_content.splitlines():
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 5:
            continue
        ts, agent, typ, task, _msg = parts[:5]
        try:
            when = datetime.fromisoformat(ts)
        except ValueError:
            continue  # non-ISO / corrupted row — skip, never abort

        if typ == "CLAIM":
            if task not in starts or when < starts[task]:
                starts[task] = when          # earliest CLAIM = true in-flight start
            owner.setdefault(task, agent)
        elif typ == "DONE":
            if task not in ends or when > ends[task]:
                ends[task] = when            # latest DONE = true in-flight end

    in_flight  = frozenset(t for t in starts if t not in ends)
    completed  = frozenset(t for t in starts if t in ends)

    return {
        "starts":    starts,
        "ends":      ends,
        "owners":    owner,
        "in_flight": in_flight,
        "completed": completed,
    }


# ---------------------------------------------------------------------------
# Step 3 — compute the re-dispatch set (PLAN-derived, tier-2 authoritative)
# ---------------------------------------------------------------------------

# Conventional-commit trailer that marks an integration commit.
# Written by kata-orchestrate step 5.  Case-insensitive for robustness.
_KATA_TASK_RE = re.compile(r"^\s*Kata-Task:\s*(\S+)\s*$", re.IGNORECASE)

# Frontmatter fence pattern — matches the opening --- and its closing ---
_FM_RE = re.compile(r"^---[ \t]*\n(.*?)\n---", re.DOTALL)


def parse_plan_tasks(plan_path: Union[str, Path]) -> set[str]:
    """Parse task-ids from a frozen PLAN.md's YAML frontmatter.

    The YAML frontmatter ``ownership:``, ``waves:``, and ``depends_on:`` keys are
    AUTHORITATIVE for the complete task-id set.  The three maps cover every
    per-task key the orchestrator reads (RUBRIC.md / kata-orchestrate precondition 2).
    Heading-based scraping is NOT used — it was a drift-prone second source of truth
    that silently dropped tasks with colon separators or non-standard hash levels.

    Returns
    -------
    set[str]
        Union of task-ids from ``ownership:`` keys, ``depends_on:`` keys, and
        task-ids in ``waves:`` value lists.

    Raises
    ------
    ValueError
        When the PLAN has no YAML frontmatter, the frontmatter is not valid YAML,
        or the frontmatter contains no ownership/waves/depends_on task structure.
        Never returns an empty or partial set silently — a silent empty set is the
        under-dispatch bug this function is designed to prevent.
    """
    path = Path(plan_path)
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        # A provided-but-unreadable PLAN (missing/moved/permission) must hard-fail the
        # SAME as bad frontmatter — never fall through to an empty task set (the silent
        # under-dispatch bug this function exists to prevent).
        raise ValueError(
            f"kata_restore: cannot read frozen PLAN at {path!s} ({exc}) — "
            f"refusing to under-dispatch. Resolve manually."
        ) from exc

    fm_match = _FM_RE.match(content)
    if not fm_match:
        raise ValueError(
            "kata_restore: cannot determine the run's task set — frozen PLAN has no "
            "ownership/waves/depends_on frontmatter; refusing to under-dispatch. "
            "Resolve manually."
        )

    try:
        fm = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ValueError(
            f"kata_restore: PLAN frontmatter is not valid YAML — {exc}; "
            "refusing to under-dispatch. Resolve manually."
        ) from exc

    if not isinstance(fm, dict):
        raise ValueError(
            "kata_restore: cannot determine the run's task set — frozen PLAN has no "
            "ownership/waves/depends_on frontmatter; refusing to under-dispatch. "
            "Resolve manually."
        )

    task_ids: set[str] = set()

    # Keys of ownership: dict (primary authoritative source — the orchestrator reads this)
    ownership = fm.get("ownership") or {}
    if isinstance(ownership, dict):
        task_ids.update(str(k) for k in ownership.keys())

    # Keys of depends_on: dict (per-task dependency map the orchestrator reads)
    depends_on = fm.get("depends_on") or {}
    if isinstance(depends_on, dict):
        task_ids.update(str(k) for k in depends_on.keys())

    # Task-ids appearing in waves: values (wave → [task-ids] the orchestrator reads)
    waves = fm.get("waves") or {}
    if isinstance(waves, dict):
        for wave_tasks in waves.values():
            if isinstance(wave_tasks, list):
                task_ids.update(str(t) for t in wave_tasks)

    if not task_ids:
        raise ValueError(
            "kata_restore: cannot determine the run's task set — frozen PLAN has no "
            "ownership/waves/depends_on frontmatter; refusing to under-dispatch. "
            "Resolve manually."
        )

    return task_ids


def collect_integrated_tasks(
    repo_root: str,
    integration_branch: str,
    plan_path: Union[str, Path, None] = None,
) -> set[str]:
    """Scan integration-branch commits for ``Kata-Task:`` trailers.

    Maps each integration commit → task-id via the conventional-commit trailer
    written by kata-orchestrate step 5.  Tier-2 (integration history) is
    AUTHORITATIVE for DONE (DESIGN §2 B3 step 3).

    When ``plan_path`` is provided the scan is **bounded** to commits AFTER the
    plan-freeze commit (the most recent commit reachable from the integration
    branch that touched ``plan_path``).  This prevents prior-run trailers for
    reused short task-ids (T1, B1, …) from marking this run's tasks as integrated.

    If the fork-point cannot be resolved (``plan_path`` not found in integration
    history), the scan falls back to the full unbounded history but logs a loud
    NOTE to stdout so the caller can detect the degraded mode.

    Parameters
    ----------
    repo_root:
        Root of the git repository.
    integration_branch:
        Branch holding durable integration commits.
    plan_path:
        Path to the frozen PLAN.md (used to resolve the fork-point).  When
        ``None``, the full history is scanned without bounding.

    Returns
    -------
    set[str]
        Task-ids that have a durable integration commit on the branch (within
        this run's window when ``plan_path`` is provided).  Returns an empty set
        when the branch doesn't exist, has no commits, or on any git error.
    """
    root = Path(repo_root).resolve()

    # ------------------------------------------------------------------
    # Resolve fork-point: most recent commit reachable from integration_branch
    # that touched plan_path.  That commit was made before this run started
    # (PLAN is frozen+committed before build), so anything after it is this run.
    # ------------------------------------------------------------------
    fork_point: Union[str, None] = None
    if plan_path is not None:
        plan_abs = Path(plan_path).resolve()
        # Use a path relative to the repo root when possible — more portable.
        try:
            plan_spec = str(plan_abs.relative_to(root))
        except ValueError:
            plan_spec = str(plan_abs)

        try:
            fp_result = subprocess.run(
                [
                    "git", "log", "-1", "--format=%H",
                    integration_branch, "--", plan_spec,
                ],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=True,
            )
            sha = fp_result.stdout.strip()
            if sha:
                fork_point = sha
        except (subprocess.CalledProcessError, OSError):
            pass

    if fork_point is not None:
        # Bounded scan: only THIS run's integration commits (after plan-freeze).
        # Prior-run trailers live on ancestors of fork_point → correctly excluded.
        # `--` at end = end-of-options / no path filter (defense-in-depth).
        git_cmd = [
            "git", "log", f"{fork_point}..{integration_branch}",
            "--format=%B", "--",
        ]
    else:
        # Unbounded fallback — log a loud NOTE so the degraded mode is visible.
        if plan_path is not None:
            print(
                "NOTE: kata_restore: could not resolve plan fork-point from "
                f"'{plan_path}' in '{integration_branch}' history; "
                "integration scan is UNBOUNDED — prior-run trailers may cause "
                "under-dispatch. Resolve manually.",
                flush=True,
            )
        # `--` at end = end-of-options / no path filter (defense-in-depth).
        git_cmd = [
            "git", "log", "--format=%B", integration_branch, "--",
        ]

    try:
        result = subprocess.run(
            git_cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return set()

    task_ids: set[str] = set()
    for line in result.stdout.splitlines():
        m = _KATA_TASK_RE.match(line)
        if m:
            task_ids.add(m.group(1))
    return task_ids


def compute_redispatch_set(
    plan_task_ids: set[str],
    integrated_task_ids: set[str],
) -> set[str]:
    """Return the re-dispatch set: PLAN tasks MINUS tasks with integration commits.

    The board frontier CORROBORATES ownership but NEVER limits this set
    (DESIGN §2 B3 step 3 / §0 C2):

    - Gating on board CLAIMs would silently drop early-wave tasks a crash
      never durably recorded (e.g. a wide first wave that crashed before any
      board write).
    - The PLAN + integration history are the only ALWAYS-durable sources.

    Parameters
    ----------
    plan_task_ids:
        All task-ids from the frozen PLAN (parsed by ``parse_plan_tasks``).
    integrated_task_ids:
        Task-ids present as integration commits (from ``collect_integrated_tasks``).

    Returns
    -------
    set[str]
        ``plan_task_ids - integrated_task_ids``
    """
    return plan_task_ids - integrated_task_ids


# ---------------------------------------------------------------------------
# Step 4 — C2 cleanup (stale branch + worktree metadata)
# ---------------------------------------------------------------------------


def cleanup_stale_task(repo_root: str, task_id: str) -> None:
    """Clean up a dead worker's stale worktree registration and branch.

    Steps (DESIGN §2 B3 step 4 / §0 C2):
    1. ``git worktree prune`` — removes stale ``.git/worktrees/<name>`` metadata
       for any worktree whose path no longer exists.
    2. ``git branch -D -- task/<task_id>`` — force-deletes the dead worker's branch
       so a fresh ``worktree add -b task/<task_id>`` never collides.  The ``--``
       end-of-options guard prevents the branch name from being parsed as a flag.

    Half-written worktree artifacts are discarded, not reused.  Both steps are
    best-effort: failures are silently swallowed so restore can continue.

    Parameters
    ----------
    repo_root:
        Root of the git repository (the directory that contains ``.git/``).
    task_id:
        The task identifier (e.g. ``"T1"``).  The branch ``task/<task_id>``
        is deleted if it exists.
    """
    root = Path(repo_root).resolve()

    # 1. Prune stale worktree metadata (.git/worktrees/<name>/ for missing paths)
    try:
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=str(root),
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        pass  # prune failure is non-fatal

    # 2. Force-delete the dead worker's task branch.
    # `--` end-of-options guard: prevents task/<id> from being parsed as a flag.
    branch = f"task/{task_id}"
    try:
        subprocess.run(
            ["git", "branch", "-D", "--", branch],
            cwd=str(root),
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        pass  # branch may not exist; non-fatal


# ---------------------------------------------------------------------------
# Top-level restore (orchestrates all five steps)
# ---------------------------------------------------------------------------


def restore(
    repo_root: str = ".",
    plan_path: Union[str, None] = None,
    integration_branch: str = "integration",
) -> dict[str, Any]:
    """Full restore flow (DESIGN §2 B3, the five steps).

    Steps
    -----
    1. Detect lost run (tier-3 absent/stale, refs/kata/trail present).
    2. Read board.md from orphan ref; fold to frontier with the canonical
       concurrency reduce (``fold_board``).
    3. Re-dispatch set = frozen PLAN tasks MINUS tasks with integration
       commits.  The folded board CORROBORATES, never gates.
    4. C2 cleanup for each re-dispatch task: ``git worktree prune`` +
       delete stale ``task/<id>`` branch.
    5. Write the board back to ``.kata/board.md`` WITHOUT rotation
       (no ``.kata/board.<utc>.archive.md`` created).

    Parameters
    ----------
    repo_root:
        Root of the git repository.
    plan_path:
        Path to the frozen PLAN.md.  Required for re-dispatch computation.
        The caller resolves this to ``.planning/specs/<name>/PLAN.md`` (the
        run's frozen PLAN under the spec directory) — ``integration_branch``
        defaults to ``"integration"``.
        If ``None``, plan_tasks is empty and re-dispatch set = empty.
    integration_branch:
        The branch holding durable integration commits (kata-orchestrate step 5).
        Defaults to ``"integration"``.

    Returns
    -------
    dict
        ``{
            "lost_run":       bool,
            "redispatch":     set[str],   # task-ids to re-dispatch (PLAN-derived)
            "plan_tasks":     set[str],   # all plan task-ids
            "integrated":     set[str],   # task-ids with integration commits
            "board_frontier": dict,       # folded board (corroborating only)
            "board_content":  str,        # raw board text from trail
        }``

    Raises
    ------
    ValueError
        When ``plan_path`` is provided but the PLAN has no frontmatter or no
        ownership/waves/depends_on task structure.  Propagated from
        ``parse_plan_tasks`` — silently swallowing it would cause under-dispatch.
    """
    _empty: dict[str, Any] = {
        "lost_run":       False,
        "redispatch":     set(),
        "plan_tasks":     set(),
        "integrated":     set(),
        "board_frontier": {},
        "board_content":  "",
    }

    # Step 1 — detect lost run
    detection = detect_lost_run(repo_root)
    if not detection["lost"]:
        return _empty

    # Step 2 — read board from the orphan ref; fold to frontier
    try:
        board_content = read_board_from_trail(repo_root)
    except Exception:  # noqa: BLE001
        board_content = ""

    frontier = fold_board(board_content)

    # Step 3 — re-dispatch set (PLAN-derived; board corroborates, never gates)
    plan_tasks: set[str] = set()
    if plan_path is not None:
        # A provided PLAN that cannot be read OR parsed MUST hard-fail — silently
        # returning an empty plan_tasks produces an empty redispatch set, the
        # under-dispatch bug this module exists to prevent. parse_plan_tasks raises
        # ValueError for EVERY failure mode (missing/unreadable file, no frontmatter,
        # invalid YAML, no task maps); let it — and any unexpected error — propagate.
        plan_tasks = parse_plan_tasks(plan_path)

    integrated = collect_integrated_tasks(repo_root, integration_branch, plan_path=plan_path)
    redispatch = compute_redispatch_set(plan_tasks, integrated)

    # Step 4 — C2 cleanup for each task to be re-dispatched
    for task_id in redispatch:
        cleanup_stale_task(repo_root, task_id)

    # Step 5 — restore board to .kata/board.md WITHOUT rotation
    # (no .kata/board.<utc>.archive.md created — see DESIGN §2 B3 step 5)
    if board_content:
        root = Path(repo_root).resolve()
        kata_dir = root / ".kata"
        kata_dir.mkdir(parents=True, exist_ok=True)
        (kata_dir / "board.md").write_text(board_content, encoding="utf-8")

    return {
        "lost_run":       True,
        "redispatch":     redispatch,
        "plan_tasks":     plan_tasks,
        "integrated":     integrated,
        "board_frontier": frontier,
        "board_content":  board_content,
    }
