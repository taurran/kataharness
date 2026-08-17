"""kata_restore.py — restore read (restore-hardening WAVE B2).

Implements the five-step restore flow from DESIGN §2 B3:

1. detect_lost_run      — tier-3 cache absent/stale AND refs/kata/trail present.
2. read_board_from_trail + fold_board — read the durable board from the orphan ref;
   fold to a frontier view with the canonical concurrency reduce (protocol/board.md).
3. compute_redispatch_set — re-dispatch set = frozen PLAN tasks MINUS tasks with an
   integration commit (mapped via the Kata-Task: trailer in each integration commit).
   The folded board CORROBORATES in-flight ownership but NEVER gates the set.
4. cleanup_stale_task   — git worktree prune + SALVAGE-RENAME the stale
   task/<id> branch (never force-delete) so a fresh re-dispatch cannot collide
   while the dead worker's commits stay recoverable under kata-salvage/<id>-<sha>.
5. restore (top-level)  — orchestrates steps 1–4 and writes the board back to
   .kata/board.md WITHOUT rotation (no archive file).

STDLIB + subprocess(git) + yaml (pyyaml, a tools dependency); no validate_skills.

Invariants (DESIGN §2 B3 / §0 C2 / §0 L1):
- Re-dispatch set = PLAN-derived, never board-derived.
- Board corroborates, never gates.
- Tier-2 (integration history) is AUTHORITATIVE for DONE.
- Cleanup discards a dead worker's WORKTREE path (worktree prune) but NEVER
  destroys the task branch itself — it is salvage-renamed, never re-attached.
- A DEGRADED scan (integration history unreadable / board unreadable / etc.)
  performs NO cleanup at all — the fail-SAFE direction for re-dispatch
  (assume nothing is done ⇒ redispatch everything) is the fail-DANGEROUS
  direction for cleanup, so step 4 is skipped whole-cloth whenever
  ``degraded`` is true and the skipped task-ids are reported back via
  ``cleanup_skipped``.
- Resume never rotates the board.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# The ONE canonical cursor parser (protocol/board.md / DESIGN §2.2).  ``fold_board``
# owns no grammar of its own — a second parser is a second source of truth.
import kata_board

# ---------------------------------------------------------------------------
# Ref constant (mirrors kata_trail.py)
# ---------------------------------------------------------------------------

_TRAIL_REF = "refs/kata/trail"

# Q-16 (2026-07-12 health review): every git subprocess call carries this timeout so a
# stale index.lock or a credential prompt in a hostile target repo can never stall the
# restore read forever.  A timeout maps to each call site's EXISTING failure/degraded
# path (never a success-shaped result) — subprocess.TimeoutExpired is NOT a subclass of
# CalledProcessError/OSError, so it is added explicitly to each except set.
_GIT_TIMEOUT_S = 60


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
            timeout=_GIT_TIMEOUT_S,  # Q-16: a hung rev-parse ⇒ ref treated as absent
        )
        return True
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
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
    subprocess.TimeoutExpired
        When the git read exceeds ``_GIT_TIMEOUT_S`` (Q-16).  ``restore`` maps this to
        the board-unreadable degraded path, never a silent success.
    """
    root = Path(repo_root).resolve()
    result = subprocess.run(
        ["git", "cat-file", "-p", f"{_TRAIL_REF}:board.md"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=True,
        timeout=_GIT_TIMEOUT_S,  # Q-16: a hung read ⇒ restore() degrades (board-unreadable)
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
    to correctly span re-dispatched tasks.  **Fold semantics are unchanged by the
    cursor migration** — only the parser moved.

    Parsing delegates to :func:`kata_board.parse_cursor`, the ONE canonical parser
    (DESIGN §2.2).  This function no longer hand-rolls the line grammar and no
    longer skips corrupted rows:

    - **Absence** (empty / whitespace-only ``board_content`` — e.g. the Q-14
      board-unreadable fail-soft in :func:`restore`) folds to an EMPTY frontier.
    - **Refusal** (any line the grammar rejects — above all a LEGACY 5-field line,
      which parses NOWHERE after the migration) raises
      :class:`kata_board.CursorParseError`.  A silently skipped row is an invisible
      hole in the audit trail, which is the class the cursor contract removes.
      :func:`restore` catches the refusal and RECORDS it as a degraded reason
      (``board-unparseable``) — never a silent drop.

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

    Raises
    ------
    kata_board.CursorParseError
        When *board_content* is non-empty and does not satisfy the cursor grammar.

    The board CORROBORATES in-flight ownership but NEVER gates the re-dispatch
    set (DESIGN §2 B3 step 3 / Gap-table row 3).
    """
    starts: dict[str, datetime] = {}
    ends:   dict[str, datetime] = {}
    owner:  dict[str, str]      = {}

    lines = (
        kata_board.parse_cursor(board_content).lines
        if board_content and board_content.strip()
        else ()
    )

    for line in lines:
        # utc is grammar-validated by parse_cursor; it stays the fold's selector here
        # so the frontier's semantics are byte-identical to the pre-migration reduce.
        when = datetime.fromisoformat(line.utc.replace("Z", "+00:00"))
        task, agent, typ = line.task, line.agent, line.type

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


def parse_plan_tasks(plan_path: str | Path) -> set[str]:
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


# ---------------------------------------------------------------------------
# BL-F01 — freeze becomes a recorded, checked state (not convention-only prose)
# ---------------------------------------------------------------------------
#
# Plan frontmatter already carries a free-prose `status:` field. These two functions are
# the ONE place that field is read and judged: `plan_status` normalizes it to a closed
# enum, `assert_frozen` is the chokepoint callers (kata_dispatch.build_brief) use to
# refuse to proceed against a plan that is not frozen. Deliberately independent of
# `parse_plan_tasks` above — it has its own pinned error-message contract (tests match on
# "refusing to under-dispatch" / "cannot determine the run's task set") that must not
# shift as a side effect of this addition.

_KNOWN_PLAN_STATUSES = frozenset({"draft", "frozen"})


def plan_status(plan_path: str | Path) -> str:
    """Return a PLAN.md's normalized freeze status from its frontmatter ``status:`` field.

    Fail-closed semantics (D45/GB12 + D136 — no silent-permissive default):

    - ``status:`` key absent, or present but empty/whitespace-only ⇒ returns ``"absent"``.
      This is NOT frozen — an absent field is never coerced to a "frozen" default.
    - Otherwise the value is split on whitespace and the FIRST WORD is taken, case-folded;
      trailing prose after that word is ignored. This is the chosen parse rule (see
      module tests) — it lets an authored value like
      ``status: DRAFT — awaiting freeze-gate (some parenthetical note)`` parse as
      ``"draft"`` instead of hard-failing on the trailing prose. The alternative rule
      (the value must be EXACTLY the token) was rejected because "draft with a trailing
      note" is a real authoring shape, not garbage, and a plan carrying it must not be
      indistinguishable from a corrupt one.
    - First word is ``"draft"`` or ``"frozen"`` ⇒ that lowercase token is returned.
    - Any other first word (typo, unrelated free prose) ⇒ RAISES. Never coerced to a
      default in either direction — an unrecognized status must not silently pass as
      frozen NOR silently pass as draft; it is a data problem to resolve by hand.

    Returns
    -------
    str
        One of ``"draft"``, ``"frozen"``, or ``"absent"``.

    Raises
    ------
    ValueError
        Unreadable file, missing/invalid YAML frontmatter, or a ``status:`` first word
        that is neither "draft" nor "frozen".
    """
    path = Path(plan_path)
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"kata_restore: cannot read PLAN at {path!s} ({exc}) — refusing to assume a "
            "status. Resolve manually."
        ) from exc

    fm_match = _FM_RE.match(content)
    if not fm_match:
        raise ValueError(
            f"kata_restore: PLAN at {path!s} has no YAML frontmatter — cannot determine "
            "its status. Resolve manually."
        )

    try:
        fm = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ValueError(
            f"kata_restore: PLAN frontmatter at {path!s} is not valid YAML — {exc}. "
            "Resolve manually."
        ) from exc

    if not isinstance(fm, dict):
        raise ValueError(
            f"kata_restore: PLAN frontmatter at {path!s} is not a mapping — cannot "
            "determine its status. Resolve manually."
        )

    raw = fm.get("status")
    if raw is None:
        return "absent"
    raw_str = str(raw).strip()
    if not raw_str:
        return "absent"

    first_word = raw_str.split()[0].casefold()
    if first_word in _KNOWN_PLAN_STATUSES:
        return first_word

    raise ValueError(
        f"kata_restore: PLAN at {path!s} has an unrecognized status {raw_str!r} (first "
        f"word {first_word!r} is neither 'draft' nor 'frozen') — refusing to coerce to a "
        "default. Resolve manually."
    )


def assert_frozen(plan_path: str | Path) -> None:
    """Raise unless the PLAN at ``plan_path`` is frozen (BL-F01 dispatch chokepoint).

    The single call a dispatcher-facing gate makes (``kata_dispatch.build_brief``).
    Fail-closed: an absent status, a "draft" status, and any condition :func:`plan_status`
    itself raises on (unreadable/garbled/unrecognized) all end here as a raise — there is
    no code path that lets a non-frozen or unparseable plan pass silently.
    """
    status = plan_status(plan_path)
    if status != "frozen":
        raise ValueError(
            f"kata_restore: PLAN at {plan_path!s} is not frozen (status={status!r}) — "
            "refusing to dispatch against it. Resolve manually."
        )


def collect_integrated_tasks(
    repo_root: str,
    integration_branch: str,
    plan_path: str | Path | None = None,
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
    plan_path: str | Path | None = None,
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
    plan_path: str | Path | None = None,
) -> tuple[list[str] | None, list[str]]:
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
    fork_point: str | None = None
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
                timeout=_GIT_TIMEOUT_S,  # Q-16: a hung fork-point ⇒ unbounded fallback (degraded)
            )
            sha = fp_result.stdout.strip()
            if sha:
                fork_point = sha
        except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
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
            timeout=_GIT_TIMEOUT_S,  # Q-16: a hung scan ⇒ None (integration-history-unreadable)
        )
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return None, reasons

    return result.stdout.splitlines(), reasons


def parse_supersede_trailers(
    repo_root: str,
    integration_branch: str,
    plan_path: str | Path | None = None,
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
    """Clean up a dead worker's stale worktree registration and SALVAGE its branch.

    Steps (DESIGN §2 B3 step 4 / §0 C2):
    1. ``git worktree prune`` — removes stale ``.git/worktrees/<name>`` metadata
       for any worktree whose path no longer exists.
    2. Salvage-rename the dead worker's branch — ``git branch -m -- task/<task_id>
       kata-salvage/<task_id>-<short-sha>`` — so a fresh ``worktree add -b
       task/<task_id>`` never collides on the name, WITHOUT destroying the dead
       worker's commits.  ``<short-sha>`` is the branch's own tip commit
       (``git rev-parse --short``) — a pure function of repo state (never a
       clock/random/counter, Determinism Doctrine law 7), so calling this twice on
       identical state always produces the same salvage name.  The ``--``
       end-of-options guard on the rename prevents either branch name from being
       parsed as a flag.

       This NEVER force-deletes: a ``git branch -D`` here would permanently
       destroy unmerged work the instant this function runs, which is the
       fail-dangerous direction cleanup must never take (see ``restore()``'s
       degraded-scan skip, which additionally refuses to even call this function
       when the re-dispatch set is not verified-safe).

    Half-written worktree artifacts are discarded from their PATH (worktree
    prune); the task branch itself is preserved, never destroyed.  Both steps are
    best-effort: failures are silently swallowed so restore can continue.  If the
    ``task/<task_id>`` branch does not exist, or the salvage name already exists
    (idempotent re-run on the same tip SHA — already salvaged), this is a no-op.

    Parameters
    ----------
    repo_root:
        Root of the git repository (the directory that contains ``.git/``).
    task_id:
        The task identifier (e.g. ``"T1"``).  The branch ``task/<task_id>``
        is salvage-renamed if it exists.
    """
    root = Path(repo_root).resolve()

    # 1. Prune stale worktree metadata (.git/worktrees/<name>/ for missing paths)
    try:
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=str(root),
            capture_output=True,
            check=True,
            timeout=_GIT_TIMEOUT_S,  # Q-16: a hung prune ⇒ best-effort skip (non-fatal)
        )
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        pass  # prune failure is non-fatal

    # 2. Salvage-rename the dead worker's task branch — never force-delete.
    branch = f"task/{task_id}"
    try:
        # No `--` guard here: `git rev-parse --short -- <rev>` treats the rev as a
        # pathspec after `--` and fails ("Needed a single revision") — verified
        # empirically. Safe without it: `branch` always carries the `task/` prefix,
        # so it can never be misparsed as a flag.
        sha_result = subprocess.run(
            ["git", "rev-parse", "--short", branch],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
            timeout=_GIT_TIMEOUT_S,  # Q-16: a hung rev-parse ⇒ best-effort skip (non-fatal)
        )
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return  # branch does not exist (or is unreadable) — no-op, exactly as before

    short_sha = sha_result.stdout.strip()
    if not short_sha:
        return  # defensive: no-op on an unexpected empty rev-parse result

    salvage_branch = f"kata-salvage/{task_id}-{short_sha}"

    # `--` end-of-options guard: prevents either branch name from being parsed
    # as a flag.
    try:
        subprocess.run(
            ["git", "branch", "-m", "--", branch, salvage_branch],
            cwd=str(root),
            capture_output=True,
            check=True,
            timeout=_GIT_TIMEOUT_S,  # Q-16: a hung rename ⇒ best-effort skip (non-fatal)
        )
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        # Covers: branch vanished between rev-parse and rename, and the idempotent
        # re-run case where kata-salvage/<id>-<sha> already exists (same tip SHA ⇒
        # already salvaged) — both are treated as an already-clean no-op.
        pass


# ---------------------------------------------------------------------------
# Top-level restore (orchestrates all five steps)
# ---------------------------------------------------------------------------


def restore(
    repo_root: str = ".",
    plan_path: str | None = None,
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
       salvage-rename the stale ``task/<id>`` branch (never delete).  Skipped
       ENTIRELY when the scan is degraded — see ``degraded`` below.
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
            "cleanup_skipped":  list[str],  # redispatch task-ids whose C2 cleanup was
                                             # skipped because the scan was degraded
        }``

    The ``degraded``/``degraded_reasons``/``cleanup_skipped`` keys are ADDITIVE
    (dict-BC) and are present on BOTH paths — the non-lost-run ``_empty`` early
    return carries ``degraded=False`` + ``degraded_reasons=[]`` +
    ``cleanup_skipped=[]`` (LOW-5, the stable dict contract).

    Fail-closed cleanup (this hardening pass): when ``degraded`` is true, step 4
    is skipped WHOLE-CLOTH — no branch in the re-dispatch set is touched, even by
    the now-non-destructive salvage rename — because a degraded scan means the
    re-dispatch set is only a SAFE over-approximation (over-dispatch-safe), not a
    verified set of tasks this restore may act on.  The skipped task-ids are
    reported in ``cleanup_skipped`` and a loud NOTE is printed.

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
        "cleanup_skipped":  [],
    }

    # Step 1 — detect lost run
    detection = detect_lost_run(repo_root)
    if not detection["lost"]:
        return _empty

    # Step 2 — read board from the orphan ref; fold to frontier
    # Q-14: the orphan-trail board read is fail-soft (board "corroborates, never gates",
    # so an empty frontier keeps the re-dispatch DIRECTION safe), but the loss must be
    # VISIBLE to a programmatic caller — a silent "" here previously set no degraded
    # signal.  Record board-unreadable so degraded/degraded_reasons carry it below.
    board_unreadable = False
    try:
        board_content = read_board_from_trail(repo_root)
    except Exception:  # noqa: BLE001
        board_content = ""
        board_unreadable = True

    # The cursor migration (DESIGN §2.2) makes an ill-formed board a REFUSAL, not a
    # silent row-skip.  restore()'s degraded-mode contract is tolerate-and-continue —
    # the board corroborates and never gates, so an empty frontier keeps the
    # re-dispatch DIRECTION safe (over-dispatch) — but the refusal is RECORDED in
    # degraded_reasons, exactly like the Q-14 board-unreadable loss, so it is never a
    # silent drop.  Note the raw board_content is still returned and written back
    # (step 5), so nothing recovered from the trail is destroyed by the refusal.
    board_unparseable = False
    try:
        frontier = fold_board(board_content)
    except kata_board.CursorError:
        frontier = fold_board("")
        board_unparseable = True

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

    # Aggregate the degraded signal: the integration-scan reasons PLUS the Q-14
    # board-unreadable loss (set above).  Both are ADDITIVE to the return contract.
    degraded_reasons = list(integrated_ex["reasons"])
    degraded = bool(integrated_ex["degraded"])
    if board_unreadable:
        degraded_reasons.append("board-unreadable")
        degraded = True
    if board_unparseable:
        degraded_reasons.append("board-unparseable")
        degraded = True

    # Step 4 — C2 cleanup for each task to be re-dispatched.
    # Fail closed on a degraded scan: the re-dispatch set direction is safe
    # (over-dispatch), but it is NOT a verified set this restore may act on — a
    # degraded scan means "assume nothing is done" for dispatch, and that same
    # assumption must NOT be extended into "so touch every one of those branches"
    # for cleanup.  Skip step 4 whole-cloth and report what was skipped.
    cleanup_skipped: list[str] = []
    if degraded:
        cleanup_skipped = sorted(redispatch)
        print(
            "NOTE: kata_restore: degraded scan "
            f"({', '.join(degraded_reasons) or 'unknown reason'}) — skipping C2 "
            f"cleanup for {len(cleanup_skipped)} task branch(es): "
            f"{cleanup_skipped!r}. No branch state was touched; resolve the "
            "degraded condition manually before re-dispatching.",
            flush=True,
        )
    else:
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
        "degraded":         degraded,
        "degraded_reasons": degraded_reasons,
        "cleanup_skipped":  cleanup_skipped,
    }
