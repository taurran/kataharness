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

# Freeze/Float M1-P1 durable trailers (git-durable, survive the .kata/ wipe on the
# canonical lost-run).  Written by the P2 supersede path; parsed here.
#   Kata-Invalidated: <task-id>            — a re-opened integrated dependent (M1-L3/F5)
#   Kata-Supersede:   <contractId>@<hash>  — an authorized contract surface change (M1-L3/L8)
_KATA_INVALIDATED_RE = re.compile(r"^\s*Kata-Invalidated\s*:\s*(\S+)\s*$", re.IGNORECASE)
# Loose prefix — used ONLY to detect a malformed invalidation trailer (looks like the
# key but fails the strict single-token match) so it is surfaced, never silently
# swallowed into an under-dispatch.  `\s*` before the colon: a key-whitespace
# variant (`Kata-Invalidated : T1`) previously missed BOTH regexes and vanished
# silently — the exact under-dispatch class this detector exists for (adval P1-F1).
_KATA_INVALIDATED_PREFIX_RE = re.compile(r"^\s*Kata-Invalidated\s*:", re.IGNORECASE)
_KATA_SUPERSEDE_RE = re.compile(
    r"^\s*Kata-Supersede\s*:\s*([A-Za-z0-9._-]+)@([0-9a-fA-F]{8,64})\s*$", re.IGNORECASE
)
# Malformed-supersede detector (adval P1-F4): a line that looks like the key but
# fails the strict `<id>@<8-64 hex>` match must be surfaced — an invisible
# supersede would let the P2 coverage audit pass vacuously (M1-L9).
_KATA_SUPERSEDE_PREFIX_RE = re.compile(r"^\s*Kata-Supersede\s*:", re.IGNORECASE)
# NOTE the deliberate asymmetry: `Kata-Task:` stays STRICT with no tolerant
# colon-spacing — tolerating a sloppy Kata-Task would move a task INTO the
# integrated set (toward under-dispatch); missing it merely re-dispatches
# (over-dispatch, the safe direction, D134/D135).

# Frontmatter fence pattern — matches the opening --- and its closing ---
_FM_RE = re.compile(r"^---[ \t]*\n(.*?)\n---", re.DOTALL)


def parse_plan_tasks(plan_path: Union[str, Path]) -> set[str]:
    """Parse task-ids from a frozen PLAN.md's YAML frontmatter.

    The YAML frontmatter ``ownership:``, ``waves:``, ``depends_on:``, and
    ``builds_against:`` (Freeze/Float M1-L2) keys are AUTHORITATIVE for the
    complete task-id set.  The four maps cover every per-task key the orchestrator
    reads (RUBRIC.md / kata-orchestrate precondition 2).
    Heading-based scraping is NOT used — it was a drift-prone second source of truth
    that silently dropped tasks with colon separators or non-standard hash levels.

    Returns
    -------
    set[str]
        Union of task-ids from ``ownership:`` keys, ``depends_on:`` keys,
        ``builds_against:`` keys, and task-ids in ``waves:`` value lists.

    Raises
    ------
    ValueError
        When the PLAN has no YAML frontmatter, the frontmatter is not valid YAML,
        or the frontmatter contains no ownership/waves/depends_on/builds_against task structure.
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
            "ownership/waves/depends_on/builds_against frontmatter; refusing to under-dispatch. "
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
            "ownership/waves/depends_on/builds_against frontmatter; refusing to under-dispatch. "
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

    # Keys of builds_against: dict (Freeze/Float M1-P1 / M1-L2 — contract-edge
    # dependents).  A contract-only dependent may appear ONLY under builds_against in
    # some plan shapes; unioning its keys guarantees it is never dropped from the
    # restore re-dispatch set.  Absent / not-a-dict ⇒ no-op (BC — no builds_against
    # edge exists in any run today).
    builds_against = fm.get("builds_against") or {}
    if isinstance(builds_against, dict):
        task_ids.update(str(k) for k in builds_against.keys())

    if not task_ids:
        raise ValueError(
            "kata_restore: cannot determine the run's task set — frozen PLAN has no "
            "ownership/waves/depends_on/builds_against frontmatter; refusing to under-dispatch. "
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

    Notes
    -----
    Delegates to :func:`collect_integrated_tasks_ex` and returns its ``["tasks"]`` —
    byte-identical behaviour and NOTE prints (BC, P0.1 U2); the structured degraded
    signal is available via the ``_ex`` variant.
    """
    return collect_integrated_tasks_ex(repo_root, integration_branch, plan_path)["tasks"]


def collect_integrated_tasks_ex(
    repo_root: str,
    integration_branch: str,
    plan_path: Union[str, Path, None] = None,
) -> dict[str, Any]:
    """Like :func:`collect_integrated_tasks`, but returns a structured degraded signal.

    Returns
    -------
    dict
        ``{"tasks": set[str], "degraded": bool, "reasons": list[str]}`` — ``degraded``
        is true iff ``reasons`` is non-empty (P0.1 U2 / delta-gate).  Reasons aggregate
        the widened ``_scan_integration_commit_bodies`` signal (``"integration-scan-
        unbounded"``), the ``lines is None`` git-error reason
        (``"integration-history-unreadable"``, MED-2 — the MOST degraded path, which
        today prints no NOTE), and the malformed-Kata-Invalidated / phantom-id NOTE
        sites (their verbatim prints stay).  ``collect_integrated_tasks`` returns this
        dict's ``["tasks"]`` unchanged (BC).
    """
    lines, reasons = _scan_integration_commit_bodies(repo_root, integration_branch, plan_path)
    reasons = list(reasons)
    if lines is None:
        # Git error: the MOST degraded path (integration history unreadable). Today it
        # prints no NOTE; the structured reason closes that false-clean gap (MED-2).
        # collect stays over-dispatch-SAFE (empty set ⇒ redispatch everything); only
        # parse_supersede_trailers RAISES on this path (out of the #16 fold).
        reasons.append("integration-history-unreadable")
        return {"tasks": set(), "degraded": True, "reasons": reasons}

    integrated: set[str] = set()
    invalidated: set[str] = set()
    for line in lines:
        mt = _KATA_TASK_RE.match(line)
        if mt:
            integrated.add(mt.group(1))
            continue
        mi = _KATA_INVALIDATED_RE.match(line)
        if mi:
            invalidated.add(mi.group(1))
        elif _KATA_INVALIDATED_PREFIX_RE.match(line):
            # A line that LOOKS like an invalidation trailer but fails the strict
            # single-token match cannot be subtracted (its task-id is unrecoverable) —
            # so the task stays "integrated" and would NOT be re-dispatched, the one
            # under-dispatch vector on this path.  Surface it loudly rather than
            # swallow it silently.  The AUTHORITATIVE fail-closed handling of a
            # malformed invalidation record is the P2 final-gate re-derivation
            # (DESIGN M1-L9); this restore subtract is a best-effort corroborator.
            print(
                "NOTE: kata_restore: malformed Kata-Invalidated trailer "
                f"{line.strip()!r} — cannot subtract (task-id unrecoverable); the P2 "
                "final gate is the fail-closed authority. Resolve manually if this run "
                "under-dispatches.",
                flush=True,
            )
            reasons.append("malformed-invalidated-trailer")

    # Corroboration (adval P1-F2): an invalidation id that never matched ANY
    # integration trailer is the under-dispatch signature — a typo'd/garbled id
    # (`T1,T2`, case-variant `t1`) subtracts nothing while the REAL task stays
    # "integrated".  Surface it loudly; the P2 final gate is the fail-closed
    # authority (M1-L9), this restore subtract is a best-effort corroborator.
    phantom = invalidated - integrated
    if phantom:
        print(
            "NOTE: kata_restore: Kata-Invalidated id(s) with no matching Kata-Task "
            f"integration trailer: {sorted(phantom)!r} — a typo'd/case-variant id "
            "subtracts nothing and the real task would NOT re-dispatch. Verify "
            "against the frozen PLAN's task-ids; the P2 final gate is the "
            "fail-closed authority. Resolve manually if this run under-dispatches.",
            flush=True,
        )
        reasons.append("phantom-invalidation-id")

    # Set-based subtract (Freeze/Float M1-P1, D138): OVER-DISPATCH-SAFE.  A task
    # integrated → invalidated → re-integrated bears BOTH trailers and is subtracted
    # (⇒ redundantly re-dispatched — the SAFE direction, D134/D135).  A run with no
    # Kata-Invalidated: trailer returns the byte-identical integrated set (BC).
    return {"tasks": integrated - invalidated, "degraded": bool(reasons), "reasons": reasons}


def _scan_integration_commit_bodies(
    repo_root: str,
    integration_branch: str,
    plan_path: Union[str, Path, None] = None,
) -> "tuple[list[str] | None, list[str]]":
    """Return ``(lines, degraded_reasons)`` for THIS run's integration commits.

    The shared bounded scan behind ``collect_integrated_tasks`` (Kata-Task /
    Kata-Invalidated) and ``parse_supersede_trailers`` (Kata-Supersede).  Resolves the
    fork-point from ``plan_path`` (the most recent integration commit that touched the
    frozen PLAN) and bounds ``git log --format=%B`` to commits AFTER it; falls back to
    the full history with a loud NOTE when the fork-point can't be resolved (mirrors
    the prior collect_integrated_tasks behaviour byte-for-byte).

    Return contract (P0.1 U2 / delta-gate HIGH-1 — the named seam):
    - ``lines``: the commit-body lines, or ``None`` on a git
      ``CalledProcessError``/``OSError`` (the MOST degraded path — callers fail safe).
    - ``degraded_reasons``: a structured signal ADDITIVE to the verbatim NOTE prints
      (which stay at their current sites).  The unbounded fallback (fork-point
      unresolvable with a ``plan_path`` provided) appends ``"integration-scan-
      unbounded"``.  The ``lines is None`` git-error reason
      (``"integration-history-unreadable"``, MED-2) is appended by
      :func:`collect_integrated_tasks_ex`, since ``parse_supersede_trailers`` RAISES on
      that path instead (deliberately OUT of the #16 fold).
    """
    reasons: list[str] = []
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

        # Determinism pins (DET-02/DET-03, DETERMINISM-DOCTRINE law 1/5): the
        # single-pathspec shape activates an operator `log.follow=true`, which
        # follows renames to an OLDER commit — a wrong fork point silently
        # ingests prior-run trailers (under-dispatch); `log.showSignature=false`
        # keeps gpg: lines out of the parsed %H stdout; `core.quotepath=off`
        # for path-output symmetry with the other pinned calls.
        try:
            fp_result = subprocess.run(
                [
                    "git",
                    "-c", "log.follow=false",
                    "-c", "log.showSignature=false",
                    "-c", "core.quotepath=off",
                    "log", "-1", "--format=%H",
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
        # `log.showSignature=false` (DET-03): a signed commit under an operator
        # `log.showSignature=true` injects gpg: lines into the parsed %B stream;
        # `core.quotepath=off` for symmetry with the other pinned calls.
        git_cmd = [
            "git",
            "-c", "log.showSignature=false",
            "-c", "core.quotepath=off",
            "log", f"{fork_point}..{integration_branch}",
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
            # Structured degraded signal ADDITIVE to the NOTE (P0.1 U2). Only when a
            # plan_path was provided — an unbounded scan with no plan_path is BY DESIGN
            # (no NOTE, not degraded).
            reasons.append("integration-scan-unbounded")
        # `--` at end = end-of-options / no path filter (defense-in-depth).
        # Same DET-03 pins as the bounded scan (parsed %B stream).
        git_cmd = [
            "git",
            "-c", "log.showSignature=false",
            "-c", "core.quotepath=off",
            "log", "--format=%B", integration_branch, "--",
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
        return None, reasons

    return result.stdout.splitlines(), reasons


def parse_supersede_trailers(
    repo_root: str,
    integration_branch: str,
    plan_path: Union[str, Path, None] = None,
) -> dict[str, str]:
    """Parse ``Kata-Supersede: <contractId>@<newSurfaceHash>`` trailers → ``{id: hash}``.

    Provided in M1-P1; CONSUMED by the P2 final-gate independent re-derivation (with
    ``contract_edges.invalidation_set`` + ``Kata-Invalidated:`` coverage).  The hash is
    normalized to **lowercase** to match ``contract_edges._EDGE_RE``'s lowercase-hex
    pin — a case mismatch would silently fail the P2 re-derivation.  Contract IDS are
    NOT case-normalized (two ids differing only by case are distinct per the edge
    grammar) — the P2 gate must cross-check every trailer id against the pinned
    contract-id set, or a typo'd/case-variant supersede is vacuously "fully covered"
    (adval P1-F5/P0-F11).  ``git log`` is newest-first **for the linear, append-only
    integration history this system produces**, so the FIRST occurrence per id (the
    most-recent supersede) wins (a future caller running this against a merge-laden
    branch would need an explicit ``--date-order``); within a SINGLE commit body the
    first (topmost) line wins (adval P1-F6).  No trailer ⇒ ``{}`` (BC).

    Fail-closed (adval P1-F3, D136/M1-L9): a git error RAISES ``ValueError`` instead
    of returning ``{}`` — to the P2 gate, ``{}`` means "no supersede this run" and a
    git failure returning it would vacuously PASS the coverage audit (the silent
    permissive default this family of code must never produce).  Contrast
    ``collect_integrated_tasks``, where the same helper failure maps to an EMPTY
    integrated set ⇒ redispatch-everything ⇒ over-dispatch-SAFE.  A malformed-looking
    supersede line (key matches, grammar doesn't) is surfaced with a loud NOTE
    (adval P1-F4) — the M1-L8 surface-drift check is the backstop that catches the
    unauthorized change itself.
    """
    lines, _reasons = _scan_integration_commit_bodies(repo_root, integration_branch, plan_path)
    if lines is None:
        raise ValueError(
            "kata_restore: cannot read integration history for Kata-Supersede "
            f"trailers (branch {integration_branch!r}) — refusing to report 'no "
            "supersede' on unreadable input (M1-L9/D136); the P2 coverage audit "
            "must not vacuously pass. Resolve manually."
        )
    out: dict[str, str] = {}
    for line in lines:
        m = _KATA_SUPERSEDE_RE.match(line)
        if m:
            cid = m.group(1)
            if cid not in out:  # newest-first ⇒ keep the most-recent supersede per id
                out[cid] = m.group(2).lower()
        elif _KATA_SUPERSEDE_PREFIX_RE.match(line):
            print(
                "NOTE: kata_restore: malformed Kata-Supersede trailer "
                f"{line.strip()!r} — expected '<contractId>@<8-64 hex>'; this "
                "supersede is INVISIBLE to the coverage audit. The M1-L8 "
                "surface-drift check is the backstop for the unauthorized change "
                "itself. Resolve manually.",
                flush=True,
            )
    return out


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
            "degraded":         bool,       # true iff a degraded-scan reason fired (P0.1 U2)
            "degraded_reasons": list[str],  # aggregated reasons (empty on a clean scan)
        }``

    The ``degraded``/``degraded_reasons`` keys are ADDITIVE (dict-BC) and are present
    on BOTH paths — the non-lost-run ``_empty`` early return carries
    ``degraded=False`` + ``degraded_reasons=[]`` (LOW-5, the stable dict contract).

    Raises
    ------
    ValueError
        When ``plan_path`` is provided but the PLAN has no frontmatter or no
        ownership/waves/depends_on/builds_against task structure.  Propagated from
        ``parse_plan_tasks`` — silently swallowing it would cause under-dispatch.
    """
    _empty: dict[str, Any] = {
        "lost_run":         False,
        "redispatch":       set(),
        "plan_tasks":       set(),
        "integrated":       set(),
        "board_frontier":   {},
        "board_content":    "",
        "degraded":         False,
        "degraded_reasons": [],
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

    integrated_ex = collect_integrated_tasks_ex(
        repo_root, integration_branch, plan_path=plan_path
    )
    integrated = integrated_ex["tasks"]
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
        "lost_run":         True,
        "redispatch":       redispatch,
        "plan_tasks":       plan_tasks,
        "integrated":       integrated,
        "board_frontier":   frontier,
        "board_content":    board_content,
        "degraded":         integrated_ex["degraded"],
        "degraded_reasons": integrated_ex["reasons"],
    }
