"""kata_telemetry.py — Freeze/Float M4-P0 measurement substrate (record, don't act).

P0 telemetry records signal vectors and builds the calibration substrate. It
computes NO risk score, NO threshold, NO triggers, NO ladder, NO kills (all P1).
This module is the code-bearing leg of M4-P0: the checkpoint-trailer parser, the
task-branch scanner, the evidence digest, the config load-guard, the slack
substrate, the per-task/per-run record builders, and the ``emit-trailer`` CLI the
worker uses to author its checkpoint trailer.

Fail-closed vs fail-soft (D136 / M4-L10):
- Functions that PARSE an external artifact to feed a decision or a record are
  **fail-closed**: absent/unparseable input RAISES :class:`TelemetryError`, never a
  permissive default (a swallowed error would vacuously pass the calibration audit
  — the exact defect this substrate exists to prevent).
- Telemetry WRITES are **fail-soft** (observability): a write failure returns a
  ``{"skipped": "<reason>"}`` sentinel (the ``kata_trail`` shape) for the caller to
  surface as a board NOTE, never gating a task.

Execution surface (``protocol/exec-safety.md``): every git call is
``subprocess.run`` with a fixed argv list and ``shell=False``; no third-party
imports; ``core.quotepath=off`` + ``--no-renames`` pin the path-listing calls so a
staged deletion is visible and the digest is deterministic across operator configs;
``log.showSignature=false`` pins the log/show family so signed commits cannot
inject ``gpg:`` lines into parsed stdout (DET-03 — the pins live in one place,
:func:`_run_git`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import footprint
from kata_advisor import ADVISOR_OUTCOMES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TRAILER_KEY = "Kata-Checkpoint:"
_VALID_MODES: frozenset[str] = frozenset({"off", "telemetry", "on"})
_SHA256_HEX_LEN = 64

# Ledger schema v2 (P0.1, additive). Producer vocabulary for a gate-rejection's
# failure kind — the orchestrator classifies from the gate evidence (D33), never the
# worker. ``unclassified`` is READER-side only (see :func:`failure_kinds_of`) and is
# NEVER a producible value: an unknown/missing kind at BUILD time is a producer bug and
# RAISES.
FAILURE_KINDS: frozenset[str] = frozenset(
    {
        "test-regression",
        "lane-drift",
        "spec-misread",
        "integration-conflict",
        "packaging",
        "security",
        "other",
    }
)

# Ledger row versions the reader parses. An ABSENT ``v`` reads as v1 (the pre-schema
# committed shape); a PRESENT-but-unknown version RAISES (fail-closed, D136). Schema
# history: v1 (pre-schema) → v2 (perTask/failureKinds/degraded, P0.1) → v3 (parentTokens
# per-phase, CA-L40; verdictByTier/tierEvents ride v3 as ADDITIVE OPTIONAL keys —
# AT-L20 / M4 Amendment #6: NO v4 is minted, a v4 row would RAISE in every deployed
# v0.2.1 reader mid-scan). Every bump is additive, no backfill (the D142 precedent).
_KNOWN_LEDGER_VERSIONS: frozenset[int] = frozenset({1, 2, 3})

# Adaptive-tiering calibration (AT-L20 / M4 Amendment #6 item 3). Producer vocabulary
# for the ``verdictByTier`` key grammar ``"<verdict>×<tier>"`` (the × separator matching
# the ``firstPassAcceptanceByClassTier`` ``"<class>×<tier>"`` convention). ``continue``/
# ``correct``/``reroll`` are the inline-evaluator ladder verdicts; ``overturned`` is the
# convention token for a SCREEN verdict overturned at re-adjudication (AT-L9): standing
# verdicts are counted under their DECIDING tier, an overturned screen verdict under
# ``"overturned×<screen-tier>"``. An unknown/malformed key at BUILD time is a producer
# bug and RAISES (the FAILURE_KINDS precedent).
VERDICT_TOKENS: frozenset[str] = frozenset({"continue", "correct", "reroll", "overturned"})

# The ``"<verdict>×<tier>"`` separator (U+00D7, the firstPassAcceptanceByClassTier char).
_VERDICT_TIER_SEP = "×"

# The exact five string keys of a ``tierEvents`` entry (AT-L7's adaptive-move audit
# trail): missing/extra/non-str keys RAISE at build (fail-closed, D136).
_TIER_EVENT_KEYS: frozenset[str] = frozenset({"at", "dispatch", "from", "to", "reason"})

# Advisor-consult run-ledger key (advisor-executor, DESIGN §3.9 — additive,
# presence-discriminated; the verdictByTier/tierEvents precedent). The row's ``advisor``
# value carries EXACTLY these five keys; a per-consult row carries EXACTLY {id, outcome}.
# The outcome vocabulary is the single-source-of-truth EV-1 enum imported from
# :mod:`kata_advisor` (never re-listed here — the two layers must agree). ``None`` is a
# LEGAL pending outcome (§3.9 explicit-null honesty). Absent ⇒ the key is OMITTED (the
# pre-feature row shape is byte-preserved); present-but-malformed RAISES at build.
_ADVISOR_LEDGER_KEYS: frozenset[str] = frozenset(
    {"consults", "byEvent", "budgetUsed", "budgetCap", "lapses"}
)
_ADVISOR_CONSULT_KEYS: frozenset[str] = frozenset({"id", "outcome"})

# Below this many total costly-verdict samples, :func:`overturn_rate` returns ``None``
# (the class_median not-yet-meaningful discipline, A1-Q3 / AT-L18's min_samples=5).
_OVERTURN_MIN_SAMPLES = 5


class TelemetryError(Exception):
    """Fail-closed telemetry error (D136).

    Raised by every parse/derive path on absent or malformed input. The
    orchestrator's documented response is STOP + escalate / treat-as-triggered +
    surface — never a silent permissive default.
    """


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_int(value: Any) -> bool:
    """Return True iff *value* is a real int (bool is rejected — it subclasses int)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _normalize(path: str) -> str:
    """Normalize path separators to forward slashes (Windows-safe)."""
    return path.replace("\\", "/")


def _now_utc() -> str:
    """Return the current UTC time as an ISO-8601 ``...Z`` string."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_git(
    repo_root: str, args: list[str], *, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a git command against *repo_root* with a fixed argv and ``shell=False``.

    ``core.quotepath=off`` is pinned so unicode paths are emitted verbatim (not
    octal-escaped) — the digest and lane-drift sets must be byte-stable across
    operator git configs. ``log.showSignature=false`` is pinned (DET-03) so a
    signed commit under an operator ``log.showSignature=true`` cannot inject
    ``gpg:`` lines into parsed log/show stdout — :func:`scan_checkpoints` parses
    ``%P%n%B`` positionally and a gpg preamble would misparse ``%P`` (the parent
    line). Both pins are load-bearing for digest stability. On a git or OS error
    (when *check*), the failure is wrapped in :class:`TelemetryError` (D139 —
    never a silent ``[]`` on git failure).

    Args:
        repo_root: Directory the git command runs in (the worker's worktree root).
        args: Git sub-command argv (without the leading ``git``).
        check: Raise on non-zero exit (default True).

    Returns:
        The completed process.

    Raises:
        TelemetryError: On a git or OS error when *check* is True.
    """
    try:
        return subprocess.run(
            ["git", "-c", "core.quotepath=off", "-c", "log.showSignature=false", *args],
            cwd=str(Path(repo_root).resolve()),
            capture_output=True,
            text=True,
            check=check,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        stderr = getattr(exc, "stderr", "") or ""
        raise TelemetryError(
            f"kata_telemetry: git {' '.join(args)} failed in {repo_root!r} "
            f"(D139 fail-closed, never []): {stderr.strip() or exc}"
        ) from exc


def _trailer_values(body: str) -> list[str]:
    """Return the JSON payloads of every ``Kata-Checkpoint:`` line in *body*."""
    values: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(_TRAILER_KEY):
            values.append(stripped[len(_TRAILER_KEY):].strip())
    return values


def _validate_record(record: Any) -> None:
    """Validate a checkpoint record against schema v1 (fail-closed).

    Required: ``v == 1``; ``i`` int >= 0; ``verify.exit`` int. Optional nullable:
    ``verify.owned`` (int — the OWNED-FILE-scoped verify exit, Amendment #5/C-1),
    ``verify.passed/failed/skipped`` (ints), ``lint`` (int), ``evidence`` (sha256
    hex). Unknown keys tolerated (forward-compatible / additive).

    Raises:
        TelemetryError: On any schema violation.
    """
    if not isinstance(record, dict):
        raise TelemetryError("checkpoint record must be a JSON object")
    if record.get("v") != 1:
        raise TelemetryError(f"checkpoint record schema: v must == 1 (got {record.get('v')!r})")
    i = record.get("i")
    if not _is_int(i) or i < 0:
        raise TelemetryError(f"checkpoint record schema: i must be an int >= 0 (got {i!r})")
    verify = record.get("verify")
    if not isinstance(verify, dict):
        raise TelemetryError("checkpoint record schema: verify must be an object")
    if not _is_int(verify.get("exit")):
        raise TelemetryError(
            f"checkpoint record schema: verify.exit must be an int (got {verify.get('exit')!r})"
        )
    for key in ("passed", "failed", "skipped", "owned"):
        if key in verify and verify[key] is not None and not _is_int(verify[key]):
            raise TelemetryError(f"checkpoint record schema: verify.{key} must be int or null")
    if "lint" in record and record["lint"] is not None and not _is_int(record["lint"]):
        raise TelemetryError("checkpoint record schema: lint must be int or null")
    evidence = record.get("evidence")
    if "evidence" in record and evidence is not None:
        if not isinstance(evidence, str) or len(evidence) != _SHA256_HEX_LEN or any(
            c not in "0123456789abcdefABCDEF" for c in evidence
        ):
            raise TelemetryError("checkpoint record schema: evidence must be a sha256 hex string")


# ---------------------------------------------------------------------------
# 1. parse_checkpoint_trailer
# ---------------------------------------------------------------------------


def parse_checkpoint_trailer(body: str) -> dict | None:
    """Extract the single ``Kata-Checkpoint:`` trailer from one commit-message *body*.

    Args:
        body: The full commit-message body (subject + trailers).

    Returns:
        The parsed record dict, or ``None`` when the body carries no trailer (a
        plain commit — NOT malformed).

    Raises:
        TelemetryError: On more than one trailer (ambiguous evidence — never
            first/last-wins, v2-MED-5), a JSON parse failure, or a schema violation.
    """
    values = _trailer_values(body)
    if not values:
        return None
    if len(values) > 1:
        raise TelemetryError(
            f"parse_checkpoint_trailer: {len(values)} Kata-Checkpoint trailers on one "
            "commit — ambiguous evidence, never first/last-wins (v2-MED-5). Escalate."
        )
    try:
        record = json.loads(values[0])
    except (json.JSONDecodeError, ValueError) as exc:
        raise TelemetryError(
            f"parse_checkpoint_trailer: Kata-Checkpoint JSON parse failure ({exc}). Escalate."
        ) from exc
    _validate_record(record)
    return record


# ---------------------------------------------------------------------------
# 2. scan_checkpoints
# ---------------------------------------------------------------------------


def scan_checkpoints(repo_root: str, branch: str, integration_ref: str) -> list[dict]:
    """Return the task branch's own checkpoint commits, oldest-first.

    Walks ``git rev-list --reverse <branch> ^<integration_ref>`` (two-dot LOG
    semantics — no merge-base ambiguity for a log walk), then per commit reads
    ``git show -s --format=%P%n%B``. A MERGE commit (>1 parent) carrying a trailer
    RAISES (the chunk diff is undefined on a multi-parent commit, v2-MED-5); a
    trailer-free merge is skipped, not an error. A non-merge commit yields
    ``{"sha": <sha>, "record": <dict|None>}`` via :func:`parse_checkpoint_trailer`.

    Args:
        repo_root: The worker's worktree root.
        branch: The task branch/ref to walk.
        integration_ref: The dispatch-base ref excluded from the walk.

    Returns:
        Oldest-first list of ``{"sha", "record"}`` dicts (the caller derives
        streaks from order).

    Raises:
        TelemetryError: On any git error (D139), or a trailer on a merge commit.
    """
    out = _run_git(repo_root, ["rev-list", "--reverse", branch, f"^{integration_ref}"]).stdout
    shas = [s for s in out.split() if s]
    results: list[dict] = []
    for sha in shas:
        show = _run_git(repo_root, ["show", "-s", "--format=%P%n%B", sha]).stdout
        first, _, body = show.partition("\n")
        parents = first.split()
        if len(parents) > 1:  # merge commit
            if _trailer_values(body):
                raise TelemetryError(
                    f"scan_checkpoints: merge commit {sha} carries a Kata-Checkpoint "
                    "trailer — 'the chunk diff' is undefined on a multi-parent commit "
                    "(v2-MED-5). Escalate."
                )
            continue  # trailer-free merge — skipped, not an error
        results.append({"sha": sha, "record": parse_checkpoint_trailer(body)})
    return results


# ---------------------------------------------------------------------------
# 3. evidence_digest / evidence_entries
# ---------------------------------------------------------------------------


def _ls_files_staged(repo_root: str, paths: list[str]) -> dict[str, str]:
    """Return ``{path: blob-sha}`` for staged (indexed) entries among *paths*.

    Parses ``git ls-files -s`` — the ``<mode> <blob-sha> <stage>\\t<path>`` form.
    The BLOB SHA column is the invariant (ls-files carries stage numbers,
    ls-tree carries object types — only the blob sha is common to both modes).
    """
    out = _run_git(repo_root, ["ls-files", "-s", "--", *paths]).stdout
    staged: dict[str, str] = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        meta, _, path = line.partition("\t")
        cols = meta.split()
        if len(cols) >= 2:
            staged[_normalize(path)] = cols[1]  # <mode> <blob-sha> <stage>
    return staged


def _ls_tree_blobs(repo_root: str, treeish: str, paths: list[str]) -> dict[str, str]:
    """Return ``{path: blob-sha}`` for blob entries under *treeish* among *paths*.

    Parses ``git ls-tree -r`` — the ``<mode> <type> <sha>\\t<path>`` form; only
    ``blob`` rows are kept (the blob sha is the digest invariant).
    """
    out = _run_git(repo_root, ["ls-tree", "-r", treeish, "--", *paths]).stdout
    blobs: dict[str, str] = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        meta, _, path = line.partition("\t")
        cols = meta.split()
        if len(cols) >= 3 and cols[1] == "blob":  # <mode> blob <sha>
            blobs[_normalize(path)] = cols[2]
    return blobs


def _tracked_in_head(repo_root: str, path: str) -> bool:
    """Return True iff *path* is tracked in HEAD (a staged deletion is detectable)."""
    proc = _run_git(repo_root, ["ls-tree", "HEAD", "--", path], check=False)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def _commit_parents(repo_root: str, commit: str) -> list[str]:
    """Return the parent SHAs of *commit* (empty for a root commit)."""
    out = _run_git(repo_root, ["show", "-s", "--format=%P", commit]).stdout
    return [p for p in out.split() if p]


def evidence_entries(repo_root: str, paths: list[str], *, commit: str | None) -> list[str]:
    """Return the sorted ``"<path>:<blob-sha|ABSENT>"`` entries for the digest.

    Worker/stamp mode (``commit=None``): staged blob hashes via ``git ls-files -s``
    (the index IS the future commit's tree for those paths). A path absent from the
    index but tracked in HEAD ⇒ ``"<path>:ABSENT"`` (a staged deletion, detectable);
    never-tracked and not-staged ⇒ RAISE (unresolvable, never hashed-as-missing).

    Verify/gate mode (``commit=<sha>``): the same entries from ``git ls-tree <sha>``.
    A path absent from ``<sha>``'s tree ⇒ check the parent tree ``<sha>^``:
    present-in-parent ⇒ ``"<path>:ABSENT"`` (deleted by this chunk — round-trips the
    stamp entry); absent-from-both ⇒ RAISE. A ROOT commit treats the parent tree as
    EMPTY ⇒ the never-existed RAISE (gate v2 F9 — the right error class), not a
    generic git error. Values are identical across modes by the git object model.

    Args:
        repo_root: The worker's worktree root.
        paths: The chunk's changed paths (any separator).
        commit: ``None`` for stamp mode; a commit SHA for verify mode.

    Returns:
        The sorted entry list.

    Raises:
        TelemetryError: On empty *paths* (a digest over nothing is a vacuous pin,
            the D131 0-of-0 lesson), or an unresolvable path.
    """
    norm_paths = [_normalize(p) for p in paths]
    if not norm_paths:
        raise TelemetryError(
            "evidence_entries: empty path list — a digest over nothing is a vacuous "
            "pin (the D131 0-of-0 lesson). Stage the chunk before digesting."
        )
    entries: list[str] = []
    if commit is None:
        staged = _ls_files_staged(repo_root, norm_paths)
        for path in norm_paths:
            if path in staged:
                entries.append(f"{path}:{staged[path]}")
            elif _tracked_in_head(repo_root, path):
                entries.append(f"{path}:ABSENT")
            else:
                raise TelemetryError(
                    f"evidence_entries: path {path!r} is neither staged nor tracked in "
                    "HEAD — unresolvable, never hashed-as-missing (A1-Q2 fail-closed). "
                    "Escalate."
                )
    else:
        in_tree = _ls_tree_blobs(repo_root, commit, norm_paths)
        parents = _commit_parents(repo_root, commit)
        in_parent: dict[str, str] | None = None
        for path in norm_paths:
            if path in in_tree:
                entries.append(f"{path}:{in_tree[path]}")
                continue
            if not parents:  # root commit — parent tree is EMPTY
                raise TelemetryError(
                    f"evidence_entries: path {path!r} absent from root commit {commit} "
                    "(empty parent tree) — the path never existed (gate v2 F9). Escalate."
                )
            if in_parent is None:
                in_parent = _ls_tree_blobs(repo_root, f"{commit}^", norm_paths)
            if path in in_parent:
                entries.append(f"{path}:ABSENT")
            else:
                raise TelemetryError(
                    f"evidence_entries: path {path!r} absent from both commit {commit} "
                    "and its parent — the path never existed (unresolvable, mirrors "
                    "stamp mode). Escalate."
                )
    return sorted(entries)


def evidence_digest(repo_root: str, paths: list[str], *, commit: str | None) -> str:
    """Return the sha256 over the sorted ``"<path>:<blob-sha>"`` entries.

    See :func:`evidence_entries` for the stamp/verify mode semantics; identical
    values across modes by the git object model.

    Raises:
        TelemetryError: On empty *paths* or an unresolvable path.
    """
    entries = evidence_entries(repo_root, paths, commit=commit)
    # DET-10 (DETERMINISM-DOCTRINE law 4 — length-prefix every multi-item digest):
    # netstring-frame each entry (``f"{len(b)}:"`` + bytes — the exact
    # benchmark_control.content_hash / contract_edges._netstring_hash in-repo
    # pattern) before hashing. A bare "\n".join is frame-ambiguous: a git-legal
    # newline in a filename lets two different (path, blob) partitions stream the
    # same bytes and collide (the D98 collision lesson). This is a digest-SCHEMA
    # change — the value differs from the pre-DET-10 bare-join digest. No committed
    # artifact/test pins the old literal (round-trip tests assert stamp==verify,
    # preserved: both modes hash the identical entry list). The entry contract is
    # unversioned, so there is no schema counter to bump.
    h = hashlib.sha256()
    for entry in entries:
        b = entry.encode("utf-8")
        h.update(f"{len(b)}:".encode("ascii"))
        h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 4. validate_inline_eval
# ---------------------------------------------------------------------------


def validate_inline_eval(value: Any) -> str:
    """Return the validated ``inlineEval`` mode (the config load-guard's mechanical leg).

    Args:
        value: The raw ``kata.config.inlineEval`` value (or ``None`` when absent).

    Returns:
        ``"off"`` when *value* is ``None`` (absent ⇒ off, the BC fail-safe); the
        value itself when it is exactly ``"off"``/``"telemetry"``/``"on"``.

    Raises:
        TelemetryError: On any case-variant, wrong type, or unknown string — the
            orchestrator's response is STOP + escalate (D45/GB12), never a silent "off".
    """
    if value is None:
        return "off"
    if isinstance(value, str) and value in _VALID_MODES:
        return value
    raise TelemetryError(
        f"validate_inline_eval: {value!r} is not a valid inlineEval mode "
        "(off|telemetry|on) — STOP + escalate, never a silent 'off' (D45/GB12/MED-9a)."
    )


# ---------------------------------------------------------------------------
# 5. Slack substrate (scheduler-computed; P0 records, P1 scores)
# ---------------------------------------------------------------------------


def parse_progress_events(board_text: str, task_id: str) -> list[dict]:
    """Return ``{ts, done, owned}`` events from *task_id*'s ``PROGRESS`` board lines.

    The board line format is
    ``<ts> | <agent> | <TYPE> | <task-id> | <msg>`` and a PROGRESS ``msg`` opens with
    ``<done>/<owned> <label>`` (F3). Other tasks' lines and non-PROGRESS types are
    ignored (the board legitimately holds them). A corrupted line that no longer
    splits into 5 fields is UNATTRIBUTABLE (its task-id field is unreadable) and is
    skipped — the board-snippet skip precedent (gate v1 LOW-12). The board format is
    UNTOUCHED.

    Args:
        board_text: The full ``.kata/board.md`` text.
        task_id: The task whose PROGRESS lines to extract.

    Returns:
        In-order list of ``{"ts", "done", "owned"}`` events.

    Raises:
        TelemetryError: On a malformed ``done/owned`` on an attributable PROGRESS
            line for THIS task (never skip-and-average an attributable signal).
    """
    events: list[dict] = []
    for raw in board_text.splitlines():
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 5:
            continue  # unattributable — fail-safe skip (LOW-12)
        ts, _agent, typ, task, msg = parts[:5]
        if typ != "PROGRESS" or task != task_id:
            continue
        tokens = msg.split()
        token = tokens[0] if tokens else ""
        frac = token.split("/")
        if len(frac) != 2:
            raise TelemetryError(
                f"parse_progress_events: malformed done/owned {token!r} on a PROGRESS "
                f"line for {task_id!r} — never skip an attributable this-task signal "
                "(A1-Q3). Escalate."
            )
        try:
            done = int(frac[0])
            owned = int(frac[1])
        except ValueError as exc:
            raise TelemetryError(
                f"parse_progress_events: non-integer done/owned {token!r} for "
                f"{task_id!r}. Escalate. ({exc})"
            ) from exc
        events.append({"ts": ts, "done": done, "owned": owned})
    return events


def read_ledger(path: str | Path) -> list[dict]:
    """Return the parsed row objects from the committed telemetry ledger.

    Row-lines are one JSON object per line (after the markdown header block); a
    line that begins with ``{`` is a row and is parsed. A malformed row RAISES
    (never skip-and-average, MED-9b). A MISSING file RAISES, always: A1-Q3's
    documented fail-safe is the ``telemetryLedger`` SETTING being absent (in which
    case ``read_ledger`` is never called); a configured-but-dangling path is a
    present-but-broken pointer ⇒ GB12/D45 raise (there is no ``missing_ok`` param).

    **Version tolerance (schema v3, CA-L40):** a row with an ABSENT ``v`` reads as v1
    (the pre-schema committed shape); a PRESENT ``v`` in :data:`_KNOWN_LEDGER_VERSIONS`
    (``{1, 2, 3}``) parses; a PRESENT-but-unknown version RAISES (fail-closed — a future
    schema this reader cannot interpret must never be silently mis-parsed, D136). v1/v2
    rows read byte-unchanged (no backfill); use :func:`parent_tokens_of` for the additive
    v3 ``parentTokens`` field, which degrades to ``{}`` on any pre-v3 row.

    Args:
        path: The ledger file path.

    Returns:
        List of row dicts.

    Raises:
        TelemetryError: On a missing file, a malformed row, or an unknown row version.
    """
    p = Path(path)
    if not p.exists():
        raise TelemetryError(
            f"read_ledger: ledger file {str(path)!r} is absent — a configured-but-"
            "dangling telemetryLedger is a broken pointer, not a fall-through "
            "(gate v1 MED-9/D45). Escalate."
        )
    rows: list[dict] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue  # header/prose line
        try:
            record = json.loads(stripped)
        except (json.JSONDecodeError, ValueError) as exc:
            raise TelemetryError(
                f"read_ledger: malformed ledger row {stripped[:80]!r} — never "
                f"skip-and-average (MED-9b). Escalate. ({exc})"
            ) from exc
        version = record.get("v") if isinstance(record, dict) else None
        if version is not None and version not in _KNOWN_LEDGER_VERSIONS:
            raise TelemetryError(
                f"read_ledger: unknown ledger row version {version!r} — known versions "
                f"are {sorted(_KNOWN_LEDGER_VERSIONS)}; an absent v reads as v1 but a "
                "PRESENT unknown version RAISES (fail-closed, D136). Escalate."
            )
        rows.append(record)
    return rows


def failure_kinds_of(row: dict) -> list[dict]:
    """Return the ledger *row*'s failure-kind classification (reader accessor, v1/v2).

    A schema-v2 row carries an explicit ``failureKinds`` list (built by
    :func:`build_ledger_row`, each entry ``{taskId, kind, at}``) and it is returned
    verbatim. A v1 row — or a v2 row where the field is absent — has no producer
    classification; this maps it to the reader-side sentinel
    ``[{"kind": "unclassified"}]`` ONLY when the row records at least one gate
    rejection (there was something to classify), and to ``[]`` otherwise (an
    unclassified sentinel is NEVER fabricated where no failure occurred). The
    discriminator is field PRESENCE, not the version number, so an additive v2 row
    without the field degrades identically to a v1 row. ``unclassified`` is
    reader-side only and is never a producible :data:`FAILURE_KINDS` value.

    Args:
        row: A ledger row dict (from :func:`read_ledger`).

    Returns:
        The list of ``{taskId, kind, at}`` classification entries for a v2 row, or
        the ``unclassified``/empty reader-side mapping for a v1/absent-field row.
    """
    if "failureKinds" in row:
        return list(row["failureKinds"])
    if row.get("gateRejections", 0) > 0:
        return [{"kind": "unclassified"}]
    return []


def parent_tokens_of(row: dict) -> dict:
    """Return the ledger *row*'s per-phase parent-context readings (reader accessor, v3).

    A schema-v3 row carries an explicit ``parentTokens`` map (built by
    :func:`build_ledger_row`, ``{"<phase>": int|null}``); it is returned verbatim with
    its EXPLICIT NULLS PRESERVED — a null is honest absence (a reading never taken) and
    must never be coerced to zero (CA-L40). A v1/v2 row — or any row where the field is
    absent — has no producer readings and maps to ``{}`` (no backfill). The
    discriminator is field PRESENCE, not the version number, so an additive row without
    the field degrades identically regardless of ``v`` (the :func:`failure_kinds_of`
    pattern).

    Named consumers (future calibration, §8 — not built here): the CA-L16 gap formula's
    worst-observed-boundary-burn term; CA-L4's ``est_wave_burn`` replacement; OP-3's
    telemetry-derived gap.

    Args:
        row: A ledger row dict (from :func:`read_ledger`).

    Returns:
        The ``{"<phase>": int|null}`` readings for a v3 row (nulls preserved), or ``{}``
        for a v1/v2/absent-field row.
    """
    if "parentTokens" in row:
        return dict(row["parentTokens"])
    return {}


def verdict_by_tier_of(row: dict) -> dict:
    """Return the ledger *row*'s verdict×tier calibration counts (reader accessor, AT-L20).

    ABSENT-HONEST on absence, FAIL-CLOSED on presence: an additive-v3 row carrying
    ``verdictByTier`` (built by :func:`build_ledger_row`) has the map returned after
    the same fail-closed validation the builder applies — a PRESENT-but-malformed
    value RAISES (the :func:`read_ledger` row-validation posture: a corrupt row is
    never skipped or coerced, MED-9b/D136). A pre-amendment row — any v1/v2/v3 row
    where the key is absent — maps to ``{}`` (nothing is ever fabricated). The
    discriminator is field PRESENCE, not the version number — exactly how
    :func:`failure_kinds_of` / :func:`parent_tokens_of` degrade on an absent field.

    Key convention (documented at :data:`VERDICT_TOKENS` and pinned by the builder):
    STANDING verdicts are counted under their DECIDING tier; an overturned screen
    verdict is counted under ``"overturned×<screen-tier>"`` (AT-L9 re-adjudication).

    Args:
        row: A ledger row dict (from :func:`read_ledger`).

    Returns:
        The validated ``{"<verdict>×<tier>": count}`` map, or ``{}`` when absent.

    Raises:
        TelemetryError: On a present-but-malformed ``verdictByTier`` value.
    """
    if "verdictByTier" not in row:
        return {}
    return _validate_verdict_by_tier(row["verdictByTier"], where="verdict_by_tier_of")


def tier_events_of(row: dict) -> list:
    """Return the ledger *row*'s adaptive-move audit trail (reader accessor, AT-L20).

    ABSENT-HONEST on absence (``[]`` — the :func:`failure_kinds_of` /
    :func:`parent_tokens_of` presence-discriminated degrade), FAIL-CLOSED on
    presence: a PRESENT-but-malformed ``tierEvents`` RAISES (the
    :func:`verdict_by_tier_of` posture — a corrupt row is never skipped).

    Args:
        row: A ledger row dict (from :func:`read_ledger`).

    Returns:
        The validated ``[{at, dispatch, from, to, reason}]`` list, or ``[]`` when
        absent.

    Raises:
        TelemetryError: On a present-but-malformed ``tierEvents`` value.
    """
    if "tierEvents" not in row:
        return []
    return _validate_tier_events(row["tierEvents"], where="tier_events_of")


def verdict_by_tier_totals(rows: list[dict], *, include_calibration: bool = False) -> dict:
    """Sum the ``verdictByTier`` maps across ledger *rows* (the calibration aggregate).

    **Calibration rows (``"calibration": true``) are EXCLUDED by default** — exactly
    the :func:`class_median` F6 discipline and for the same reasons: toy calibration
    verdict counts must never bias the real τ/verdict calibration input. Pass
    ``include_calibration=True`` to fold them in (e.g. when auditing the calibration
    runs themselves). Rows without the key contribute nothing (absent-honest via
    :func:`verdict_by_tier_of`); a row with a PRESENT-but-malformed map RAISES —
    never skip-and-average (MED-9b).

    Args:
        rows: Ledger rows (from :func:`read_ledger`).
        include_calibration: Include ``calibration: true`` rows (default False).

    Returns:
        The summed ``{"<verdict>×<tier>": total}`` map (``{}`` when no row carries
        the key).

    Raises:
        TelemetryError: On any row's present-but-malformed ``verdictByTier``.
    """
    totals: dict[str, int] = {}
    for row in rows:
        if not include_calibration and row.get("calibration") is True:
            continue  # calibration rows never bias the totals (the F6 discipline)
        for key, count in verdict_by_tier_of(row).items():
            totals[key] = totals.get(key, 0) + count
    return totals


def overturn_rate(
    rows: list[dict], *, tier: str | None = None, include_calibration: bool = False
) -> float | None:
    """Return the screen-verdict overturn rate — the first-class calibration metric.

    **The mechanical definition (the key convention pinned by the builder):**
    ``verdictByTier`` counts STANDING verdicts under their DECIDING tier and each
    overturned SCREEN verdict under ``"overturned×<screen-tier>"`` (AT-L9: a
    would-be ``correct``/``reroll`` screen verdict is re-adjudicated one rung up;
    the higher evaluator's verdict stands). The rate is therefore::

        overturned_total / (overturned_total + standing correct+reroll total)

    — of all costly (``correct``/``reroll``/``overturned``) verdicts recorded, the
    fraction that were screen verdicts overturned at re-adjudication vs verdicts
    that stood. ``continue`` verdicts are NEVER samples (the green path is never
    re-adjudicated, M4-L1). With *tier* given, only keys whose tier component
    matches count: overturned screens AT that tier plus standing verdicts DECIDED
    at that tier.

    Fewer than 5 total samples (``_OVERTURN_MIN_SAMPLES``) ⇒ ``None`` — the
    :func:`class_median` not-yet-meaningful discipline (A1-Q3): a rate over noise
    is never manufactured. Calibration rows are excluded by default (the
    :func:`verdict_by_tier_totals` / F6 discipline).

    Args:
        rows: Ledger rows (from :func:`read_ledger`).
        tier: Restrict to one tier's keys (``None`` ⇒ all tiers).
        include_calibration: Include ``calibration: true`` rows (default False).

    Returns:
        The overturn rate in ``[0.0, 1.0]``, or ``None`` below 5 total samples.

    Raises:
        TelemetryError: On any row's present-but-malformed ``verdictByTier``.
    """
    totals = verdict_by_tier_totals(rows, include_calibration=include_calibration)
    overturned = 0
    samples = 0
    for key, count in totals.items():
        verdict, _, key_tier = key.partition(_VERDICT_TIER_SEP)
        if tier is not None and key_tier != tier:
            continue
        if verdict == "overturned":
            overturned += count
            samples += count
        elif verdict in ("correct", "reroll"):
            samples += count
        # "continue" is never a sample — the green path is never re-adjudicated.
    if samples < _OVERTURN_MIN_SAMPLES:
        return None  # not-yet-meaningful (the class_median discipline, A1-Q3)
    return overturned / samples


def class_median(rows: list[dict], task_class: str, min_samples: int = 5) -> float | None:
    """Return the median per-task duration for *task_class*, or ``None`` if too few.

    Samples are drawn from each row's ``taskDurationsByClass[task_class]``.
    **Calibration rows (``"calibration": true``) are EXCLUDED** (gate v2 F6 — toy
    calibration durations must never bias the real class median). Fewer than
    *min_samples* samples ⇒ ``None`` (the documented fall-through, A1-Q3).

    Args:
        rows: Ledger rows (from :func:`read_ledger`).
        task_class: The class to aggregate (e.g. ``"code"``).
        min_samples: The minimum sample count below which ``None`` is returned.

    Returns:
        The median duration (float), or ``None`` when ``< min_samples`` samples.
    """
    samples: list[float] = []
    for row in rows:
        if row.get("calibration") is True:
            continue  # calibration rows never bias the real median (F6)
        durations = row.get("taskDurationsByClass", {})
        samples.extend(durations.get(task_class, []))
    if len(samples) < min_samples:
        return None
    return float(statistics.median(samples))


def resolve_estimate(
    median: float | None, frontmatter_estimate: Any
) -> tuple[float | None, str]:
    """Resolve the slack estimate by precedence: ledger-median → frontmatter → absent.

    Args:
        median: The ledger class median (or ``None`` when unavailable).
        frontmatter_estimate: The optional per-task ``estimate:`` (minutes).

    Returns:
        ``(estimate, source)`` — source is ``"ledger"``, ``"frontmatter"``, or
        ``"absent"`` (with ``estimate`` ``None``).

    Raises:
        TelemetryError: When *frontmatter_estimate* is present but non-numeric (the
            runtime backstop; freeze-time validation is T3 prose, A1-Q3).
    """
    if median is not None:
        return (float(median), "ledger")
    if frontmatter_estimate is not None:
        if isinstance(frontmatter_estimate, bool) or not isinstance(
            frontmatter_estimate, (int, float)
        ):
            raise TelemetryError(
                f"resolve_estimate: frontmatter estimate {frontmatter_estimate!r} is "
                "non-numeric — the runtime fail-closed backstop (A1-Q3). Escalate."
            )
        return (float(frontmatter_estimate), "frontmatter")
    return (None, "absent")


def _parse_iso(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp (accepting a trailing ``Z``); RAISE on failure."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError) as exc:
        raise TelemetryError(
            f"slack_ratio: unparseable timestamp {ts!r} — fail-closed (D136). "
            f"Escalate. ({exc})"
        ) from exc


def slack_ratio(
    events: list[dict], estimate_min: float | None, now_utc: datetime
) -> float | None:
    """Return the progress-normalized slack ratio, or ``None`` when it is absent.

    The ratio is ``elapsed / (estimate × done/owned)`` using the earliest event's
    timestamp as task start and the latest event's ``done/owned`` as progress.
    ``estimate is None`` OR ``done == 0`` (the mandated ``0/1`` early-heartbeat form)
    ⇒ ``None`` — the formula must never manufacture an early trigger against a
    healthy early worker (v2-MED-6 / zero-progress guard).

    KNOWN CAVEAT (L19 sweep LOW-8): PROGRESS events SPAN reroll attempts — elapsed
    runs from attempt 1's first event while a fresh attempt's ``done/owned``
    restarts, so recorded slack across a reroll is inflated/polluted. Harmless for
    P1 code-class triggering (slack alone cannot cross τ), but calibration
    consumers of recorded slack should exclude rerolled tasks until P2 re-scopes
    slack per attempt.

    Args:
        events: ``{ts, done, owned}`` events (from :func:`parse_progress_events`).
        estimate_min: The resolved estimate in minutes (or ``None``).
        now_utc: The current time (tz-aware) used to compute elapsed.

    Returns:
        The slack ratio (float), or ``None`` when the term is absent.

    Raises:
        TelemetryError: On non-monotonic or unparseable timestamps.
    """
    if estimate_min is None:
        return None
    times = [_parse_iso(e["ts"]) for e in events]
    for idx in range(1, len(times)):
        if times[idx] < times[idx - 1]:
            raise TelemetryError(
                "slack_ratio: non-monotonic PROGRESS timestamps — ambiguous elapsed, "
                "fail-closed (D136). Escalate."
            )
    if not events:
        return None
    last = events[-1]
    done, owned = last["done"], last["owned"]
    if done == 0 or owned == 0:
        return None
    fraction = done / owned
    elapsed_min = (now_utc - times[0]).total_seconds() / 60.0
    denominator = estimate_min * fraction
    if denominator == 0:
        return None
    return elapsed_min / denominator


# ---------------------------------------------------------------------------
# 6. Records + ledger rows
# ---------------------------------------------------------------------------


def build_task_telemetry(
    *,
    task_id: str,
    task_class: str,
    tier: str,
    effective_mode: str,
    checkpoints: list[dict],
    gate_verdict: str,
    fix_cycles: int,
    wall_clock_s: float,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    utc: str | None = None,
) -> dict:
    """Build the per-task telemetry record (schema v1).

    ``firstTripIndex`` and ``ladderEvents`` are SCHEMA'd now but always
    ``null``/``[]`` in P0 (no triggers exist). Token counts are nullable per the
    ``usage_meter`` honesty (the host may not surface them). Each entry in
    *checkpoints* is expected to carry
    ``{i, sha, verifyExit, verifyPassed, verifyFailed, verifySkipped, lint,
    evidence, laneDrift, slack}`` — the verify COUNTS the trailer already parses
    (gate v1 MED-10; M4-L6's pass/fail/delta signal needs them).

    Args:
        task_id: The task id.
        task_class: The task's detected class (e.g. ``"code"``).
        tier: The resolved model tier the task ran at.
        effective_mode: The task's effective ``inlineEval`` mode.
        checkpoints: The per-checkpoint entry dicts.
        gate_verdict: The task's final gate verdict.
        fix_cycles: The task's fix-cycle count.
        wall_clock_s: The task's wall-clock duration in seconds.
        tokens_in: Input token count, or ``None`` where unsurfaced.
        tokens_out: Output token count, or ``None`` where unsurfaced.
        utc: The record timestamp (defaults to now).

    Returns:
        The schema-v1 per-task telemetry record.
    """
    return {
        "v": 1,
        "taskId": task_id,
        "class": task_class,
        "tier": tier,
        "effectiveMode": effective_mode,
        "chunkCount": len(checkpoints),
        "checkpoints": list(checkpoints),
        "firstTripIndex": None,
        "ladderEvents": [],
        "gateVerdict": gate_verdict,
        "fixCycles": fix_cycles,
        "wallClockS": wall_clock_s,
        "tokensIn": tokens_in,
        "tokensOut": tokens_out,
        "utc": utc or _now_utc(),
    }


def write_task_telemetry(kata_dir: str | Path, record: dict) -> dict:
    """Write *record* to ``<kata_dir>/telemetry/<taskId>.json`` (fail-soft).

    Telemetry is observability, not a gate: an ``OSError`` is caught and returned as
    a ``{"skipped": "<reason>"}`` sentinel (the exact ``kata_trail`` shape, gate v1
    LOW-15) for the caller to surface as a board NOTE — the write never gates a task.

    Args:
        kata_dir: The run's ``.kata/`` directory.
        record: The per-task telemetry record (must carry ``taskId``).

    Returns:
        ``{"written": "<path>"}`` on success, or ``{"skipped": "<reason>"}`` on
        an OS error.
    """
    try:
        telemetry_dir = Path(kata_dir) / "telemetry"
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        path = telemetry_dir / f"{record['taskId']}.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return {"written": str(path)}
    except OSError as exc:
        return {"skipped": f"os-error: {exc}"}


def checkpoint_changed_files(repo_root: str, sha: str) -> list[str]:
    """Return the files a single checkpoint commit changed (sorted, normalized).

    Uses ``git show --no-renames --name-only --format=`` (with ``core.quotepath=off``
    via :func:`_run_git`) — the same rename/quotepath pins as the CLI default so a
    renamed path surfaces as delete+add and the set is config-independent. Merge
    commits never reach here (excluded in :func:`scan_checkpoints`). The per-checkpoint
    lane drift is then ``footprint.partition(changed, ownership)["out_of_footprint"]``
    (REUSES footprint — no reimplementation).

    Args:
        repo_root: The worker's worktree root.
        sha: The single (non-merge) commit SHA.

    Returns:
        The sorted, forward-slash-normalized changed-file list.

    Raises:
        TelemetryError: On any git error (D139).
    """
    out = _run_git(repo_root, ["show", "--no-renames", "--name-only", "--format=", sha]).stdout
    return sorted({_normalize(line) for line in out.splitlines() if line.strip()})


def checkpoint_lane_drift(
    repo_root: str, sha: str, ownership: list[str]
) -> list[str]:
    """Return the out-of-footprint files a checkpoint changed (REUSES footprint).

    Args:
        repo_root: The worker's worktree root.
        sha: The checkpoint commit SHA.
        ownership: The task's declared footprint (paths / directory prefixes).

    Returns:
        The out-of-footprint (lane-drift) file list.
    """
    changed = checkpoint_changed_files(repo_root, sha)
    return footprint.partition(changed, ownership)["out_of_footprint"]


_LEDGER_ROW_DEFAULTS: dict[str, Any] = {
    "tasks": 0,
    "checkpoints": 0,
    "zeroCheckpointTasks": 0,
    "firstPassAcceptanceByClassTier": {},
    "streaksByClass": {},
    "fixCycles": 0,
    "gateRejections": 0,
    "taskDurationsByClass": {},
    "wallClockS": None,
    "tokensIn": None,
    "tokensOut": None,
    "effectiveModes": {},
}


def _normalize_per_task(raw: Any) -> dict:
    """Normalize the v2 ``perTask`` cost map to ``{taskId: {tokensIn, tokensOut, wallClockS}}``.

    Every entry is forced to the three-key shape with EXPLICIT nulls where the host
    surfaced nothing — the usage_meter honesty (a null token count is recorded, never
    fabricated). An absent / empty map ⇒ ``{}``.
    """
    result: dict[str, dict] = {}
    for task_id, cost in (raw or {}).items():
        cost = cost or {}
        result[str(task_id)] = {
            "tokensIn": cost.get("tokensIn"),
            "tokensOut": cost.get("tokensOut"),
            "wallClockS": cost.get("wallClockS"),
        }
    return result


def _validate_failure_kinds(raw: Any) -> list[dict]:
    """Validate + normalize the v2 ``failureKinds`` list (producer-side, fail-closed).

    Each entry must carry a ``kind`` in :data:`FAILURE_KINDS`; an unknown OR missing
    ``kind`` at BUILD time is a producer bug and RAISES :class:`TelemetryError`
    (``unclassified`` is reader-side only, never producible — see
    :func:`failure_kinds_of`). ``taskId`` and ``at`` (ISO-UTC, caller-supplied) pass
    through. An absent / empty list ⇒ ``[]``.

    Raises:
        TelemetryError: On a non-object entry or an unknown/missing ``kind``.
    """
    out: list[dict] = []
    for entry in raw or []:
        if not isinstance(entry, dict):
            raise TelemetryError(
                "build_ledger_row: failureKinds entry must be a JSON object "
                f"(got {entry!r}). Escalate."
            )
        kind = entry.get("kind")
        if kind not in FAILURE_KINDS:
            raise TelemetryError(
                f"build_ledger_row: failureKinds kind {kind!r} not in the producer "
                f"vocabulary {sorted(FAILURE_KINDS)} — an unknown/missing kind at build "
                "time is a producer bug (unclassified is reader-side only, never "
                "producible). Escalate."
            )
        out.append({"taskId": entry.get("taskId"), "kind": kind, "at": entry.get("at")})
    return out


def _validate_degraded(raw: Any) -> list[dict]:
    """Validate the ``degraded`` list ``[{scope, reason}]`` (producer-side, fail-closed).

    Previously an unvalidated passthrough — the one v2 list beside the fail-closed
    siblings :func:`_validate_failure_kinds` / :func:`_validate_verdict_by_tier`
    (quota-resilience G-10 brought it into the family). Each entry must be a dict with
    exactly the keys ``scope`` and ``reason``, both non-empty strings. ``scope`` stays
    an OPEN string (no enum — BC with existing ``"premium"`` / task-scoped producers;
    this run adds scope ``"provider"`` with reasons ``quota-exhausted`` /
    ``rate-limited`` / ``auth``). An absent / empty list ⇒ ``[]``.

    Raises:
        TelemetryError: On a non-object entry, extra/missing keys, or a non-string /
            empty ``scope``/``reason`` (a malformed degraded record at build time is a
            producer bug — the ``_validate_failure_kinds`` posture).
    """
    out: list[dict] = []
    for entry in raw or []:
        if not isinstance(entry, dict):
            raise TelemetryError(
                f"build_ledger_row: degraded entry must be a JSON object (got {entry!r}). Escalate."
            )
        if set(entry) != {"scope", "reason"}:
            raise TelemetryError(
                "build_ledger_row: degraded entry must carry exactly {scope, reason} "
                f"(got keys {sorted(entry)}). Escalate."
            )
        scope, reason = entry["scope"], entry["reason"]
        for name, value in (("scope", scope), ("reason", reason)):
            if not isinstance(value, str) or not value.strip():
                raise TelemetryError(
                    f"build_ledger_row: degraded {name} must be a non-empty string "
                    f"(got {value!r}). Escalate."
                )
        out.append({"scope": scope, "reason": reason})
    return out


def _normalize_parent_tokens(raw: Any) -> dict:
    """Normalize the v3 ``parentTokens`` per-phase map to ``{"<phase>": int|None}``.

    Each value is an honest parent-context token reading OR an EXPLICIT null where no
    reading was taken — never zero (a zero would falsely assert an empty parent
    context; CA-L40: "Nulls are honest absence, never zero"). A ``None`` is preserved
    as ``None``; the caller's numeric reading passes through untouched (mirrors
    :func:`_normalize_per_task` — the producer is trusted for the value, the shape is
    enforced here). An absent / empty map ⇒ ``{}`` (no backfill; old rows read as v1/v2).
    """
    result: dict[str, Any] = {}
    for phase, tokens in (raw or {}).items():
        result[str(phase)] = tokens
    return result


def _validate_verdict_by_tier(raw: Any, *, where: str) -> dict:
    """Validate the additive-v3 ``verdictByTier`` map (fail-closed, both sides).

    Key grammar (AT-L20 / Amendment #6 item 3): every key is exactly
    ``"<verdict>×<tier>"`` — one ``×`` separator (the ``firstPassAcceptanceByClassTier``
    convention), verdict in :data:`VERDICT_TOKENS` (``overturned`` IS legal — the
    overturned-screen-verdict convention key), tier a non-empty string; every value a
    non-negative real int (bool rejected). A malformed map RAISES wherever it is seen:
    at BUILD it is a producer bug (the :func:`_validate_failure_kinds` precedent), at
    READ it is a corrupt row (the :func:`read_ledger` row-validation posture) — never
    skipped, never coerced (D136). A PRESENT ``None`` is malformed, never read as
    absent (absence is key OMISSION, enforced by the callers).

    Args:
        raw: The raw ``verdictByTier`` value.
        where: The raising context (``"build_ledger_row"`` / ``"verdict_by_tier_of"``).

    Returns:
        The validated ``{"<verdict>×<tier>": count}`` dict (a fresh copy).

    Raises:
        TelemetryError: On a non-dict value, a malformed key, an unknown verdict
            token, or a negative/non-int count.
    """
    if not isinstance(raw, dict):
        raise TelemetryError(
            f"{where}: verdictByTier must be a JSON object of "
            f'"<verdict>{_VERDICT_TIER_SEP}<tier>" counts (got {raw!r}) — a present '
            "null/wrong type is malformed, never absent (D136 fail-closed). Escalate."
        )
    out: dict[str, int] = {}
    for key, count in raw.items():
        parts = key.split(_VERDICT_TIER_SEP) if isinstance(key, str) else []
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise TelemetryError(
                f"{where}: verdictByTier key {key!r} is not of the exact "
                f'"<verdict>{_VERDICT_TIER_SEP}<tier>" shape (one {_VERDICT_TIER_SEP} '
                "separator, non-empty verdict and tier — the "
                "firstPassAcceptanceByClassTier convention). Escalate."
            )
        verdict, tier = parts
        if verdict not in VERDICT_TOKENS:
            raise TelemetryError(
                f"{where}: verdictByTier verdict token {verdict!r} not in the producer "
                f"vocabulary {sorted(VERDICT_TOKENS)} (key {key!r}) — an unknown token "
                "is a producer bug (the FAILURE_KINDS precedent). Escalate."
            )
        if not _is_int(count) or count < 0:
            raise TelemetryError(
                f"{where}: verdictByTier count for {key!r} must be a non-negative int "
                f"(got {count!r}) — a count is a tally, never coerced (D136). Escalate."
            )
        out[key] = count
    return out


def _validate_tier_events(raw: Any, *, where: str) -> list[dict]:
    """Validate the additive-v3 ``tierEvents`` list (fail-closed, both sides).

    Each entry (AT-L7's adaptive-move audit record) must carry EXACTLY the five
    string keys ``{at, dispatch, from, to, reason}`` — a missing key, an extra key,
    or a non-string value RAISES (build: producer bug; read: corrupt row — the
    :func:`_validate_verdict_by_tier` posture). ``at`` is checked as a string only
    (ISO-8601-ish by contract; no timestamp parse here). A PRESENT ``None``/non-list
    is malformed, never read as absent.

    Args:
        raw: The raw ``tierEvents`` value.
        where: The raising context.

    Returns:
        The validated entry list (fresh five-key dicts, fixed key order).

    Raises:
        TelemetryError: On a non-list value, a non-object entry, missing/extra
            keys, or a non-string value.
    """
    if not isinstance(raw, list):
        raise TelemetryError(
            f"{where}: tierEvents must be a JSON array of "
            "{at, dispatch, from, to, reason} objects (got "
            f"{raw!r}) — a present null/wrong type is malformed, never absent "
            "(D136 fail-closed). Escalate."
        )
    out: list[dict] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise TelemetryError(
                f"{where}: tierEvents entry must be a JSON object (got {entry!r}). "
                "Escalate."
            )
        if set(entry.keys()) != _TIER_EVENT_KEYS:
            raise TelemetryError(
                f"{where}: tierEvents entry keys {sorted(entry.keys())!r} must be "
                f"EXACTLY {sorted(_TIER_EVENT_KEYS)} — missing/extra keys are a "
                "producer bug (AT-L20 additive contract). Escalate."
            )
        for key in _TIER_EVENT_KEYS:
            if not isinstance(entry[key], str):
                raise TelemetryError(
                    f"{where}: tierEvents entry value for {key!r} must be a string "
                    f"(got {entry[key]!r}). Escalate."
                )
        out.append(
            {
                "at": entry["at"],
                "dispatch": entry["dispatch"],
                "from": entry["from"],
                "to": entry["to"],
                "reason": entry["reason"],
            }
        )
    return out


def _validate_advisor_ledger(raw: Any, *, where: str) -> dict:
    """Validate the additive advisor run-ledger value (fail-closed, both sides).

    The advisor-executor rollup source (DESIGN §3.9), built by
    ``kata_advisor.ledger_fragment``. Shape: EXACTLY the five keys
    :data:`_ADVISOR_LEDGER_KEYS` — ``consults`` (a list of ``{id, outcome}`` rows;
    ``id`` a non-empty string, ``outcome`` in :data:`ADVISOR_OUTCOMES` or ``None`` for a
    pending pairing), ``byEvent`` (``{event: n}`` non-negative-int tally), ``budgetUsed``
    / ``budgetCap`` (non-negative ints), and ``lapses`` (a ``list[str]``). A missing/
    extra key, a wrong type, a negative/non-int count, or an unknown outcome RAISES (the
    ``verdictByTier``/``failureKinds`` producer-bug precedent); a PRESENT ``None``/
    non-object is malformed, never read as absent.

    Args:
        raw: The raw ``advisor`` value.
        where: The raising context.

    Returns:
        The validated ``advisor`` value (fresh, fixed key order).

    Raises:
        TelemetryError: On any shape/type/vocabulary violation.
    """
    if not isinstance(raw, dict):
        raise TelemetryError(
            f"{where}: advisor must be a JSON object with keys "
            f"{sorted(_ADVISOR_LEDGER_KEYS)} (got {raw!r}) — a present null/wrong type is "
            "malformed, never absent (D136 fail-closed). Escalate."
        )
    if set(raw.keys()) != _ADVISOR_LEDGER_KEYS:
        raise TelemetryError(
            f"{where}: advisor keys {sorted(raw.keys())!r} must be EXACTLY "
            f"{sorted(_ADVISOR_LEDGER_KEYS)} — missing/extra keys are a producer bug "
            "(the tierEvents additive contract). Escalate."
        )
    for key in ("budgetUsed", "budgetCap"):
        if not _is_int(raw[key]) or raw[key] < 0:
            raise TelemetryError(
                f"{where}: advisor.{key} must be a non-negative int (got {raw[key]!r}) — "
                "a count is a tally, never coerced (D136). Escalate."
            )
    if not isinstance(raw["byEvent"], dict):
        raise TelemetryError(
            f"{where}: advisor.byEvent must be an object (got {raw['byEvent']!r}). Escalate."
        )
    by_event: dict[str, int] = {}
    for event, count in raw["byEvent"].items():
        if not isinstance(event, str) or not event:
            raise TelemetryError(
                f"{where}: advisor.byEvent key {event!r} must be a non-empty string. Escalate."
            )
        if not _is_int(count) or count < 0:
            raise TelemetryError(
                f"{where}: advisor.byEvent count for {event!r} must be a non-negative int "
                f"(got {count!r}) — a count is a tally, never coerced (D136). Escalate."
            )
        by_event[event] = count
    if not isinstance(raw["lapses"], list) or not all(isinstance(x, str) for x in raw["lapses"]):
        raise TelemetryError(
            f"{where}: advisor.lapses must be a list of strings (got {raw['lapses']!r}). Escalate."
        )
    if not isinstance(raw["consults"], list):
        raise TelemetryError(
            f"{where}: advisor.consults must be a JSON array of {{id, outcome}} objects "
            f"(got {raw['consults']!r}). Escalate."
        )
    consults: list[dict] = []
    for entry in raw["consults"]:
        if not isinstance(entry, dict) or set(entry.keys()) != _ADVISOR_CONSULT_KEYS:
            raise TelemetryError(
                f"{where}: advisor.consults entry keys must be EXACTLY "
                f"{sorted(_ADVISOR_CONSULT_KEYS)} (got {entry!r}). Escalate."
            )
        if not isinstance(entry["id"], str) or not entry["id"]:
            raise TelemetryError(
                f"{where}: advisor.consults id must be a non-empty string (got "
                f"{entry['id']!r}). Escalate."
            )
        outcome = entry["outcome"]
        if outcome is not None and outcome not in ADVISOR_OUTCOMES:
            raise TelemetryError(
                f"{where}: advisor.consults outcome {outcome!r} not in the EV-1 enum "
                f"{sorted(ADVISOR_OUTCOMES)} (or null for pending) — an unknown outcome is "
                "a producer bug (D136). Escalate."
            )
        consults.append({"id": entry["id"], "outcome": outcome})
    return {
        "consults": consults,
        "byEvent": by_event,
        "budgetUsed": raw["budgetUsed"],
        "budgetCap": raw["budgetCap"],
        "lapses": list(raw["lapses"]),
    }


def build_ledger_row(run_summary: dict) -> str:
    """Build the one-line JSON ledger row (schema v3, additive over v2/v1) from a run summary.

    ``firstPassAcceptanceByClassTier`` is keyed ``"<class>×<tier>"`` (gate v1
    MED-10; M4-L10/L7's acceptance-per-(class×tier) routing report needs the keys,
    not a bare rate). ``zeroCheckpointTasks`` is the LOW-12 tell. A truthy
    ``calibration`` in *run_summary* is carried through as ``"calibration": true``
    (gate v2 F6/F8 — :func:`class_median` then EXCLUDES the row).

    **Schema v2 (P0.1, additive):** ``perTask`` (``{taskId: {tokensIn, tokensOut,
    wallClockS}}``, explicit nulls, never fabricated), ``failureKinds``
    (``[{taskId, kind, at}]``, an unknown/missing ``kind`` RAISES at build time), and
    ``degraded`` (``[{scope, reason}]``).

    **Schema v3 (CA-L40, additive):** the row carries ``v: 3`` plus ``parentTokens``
    (``{"<phase>": int|null}``) — per-phase parent-context token readings, explicit
    nulls for honest absence (never zero). Named future consumers (calibration, §8 —
    NOT built here): the CA-L16 gap formula's worst-observed-boundary-burn term;
    CA-L4's ``est_wave_burn`` replacement; OP-3's telemetry-derived gap.

    Every earlier-schema field is retained; a caller passing no new data gets ``{}`` /
    ``[]`` / ``[]`` / ``{}`` defaults (no backfill — old rows read as v1/v2, §4 row 12).

    **AT-L20 / M4 Amendment #6 item 3 (adaptive-tiering, additive — the row STAYS
    ``v: 3``, NO v4 is minted):** two OPTIONAL, presence-discriminated keys —
    ``verdictByTier`` (``{"<verdict>×<tier>": n}``; verdict in :data:`VERDICT_TOKENS`;
    standing verdicts counted under their DECIDING tier, an overturned screen verdict
    under ``"overturned×<screen-tier>"`` — the τ/verdict calibration input C-3 named)
    and ``tierEvents`` (``[{at, dispatch, from, to, reason}]`` — the adaptive-move
    audit trail). PRESENT ⇒ validated fail-closed (an unknown verdict token, malformed
    key shape, negative/non-int count, or a wrong-shaped event entry RAISES at build —
    the ``failureKinds`` producer-bug precedent); ABSENT ⇒ the key is OMITTED from the
    row entirely (never null — the pre-amendment v3 row shape is byte-preserved).

    **Advisor-executor (DESIGN §3.9, additive — the row STAYS ``v: 3``):** one further
    OPTIONAL, presence-discriminated ``advisor`` key (``kata_advisor.ledger_fragment``'s
    ``{consults, byEvent, budgetUsed, budgetCap, lapses}`` after-action rollup). PRESENT
    ⇒ validated fail-closed (:func:`_validate_advisor_ledger` — bad shape, negative
    counts, or an unknown EV-1 outcome RAISE; a ``None`` per-consult outcome is a LEGAL
    pending pairing); ABSENT ⇒ OMITTED, the pre-feature row byte-preserved.

    Args:
        run_summary: The run-summary dict (``runId``/``target`` + the metrics).

    Returns:
        A single-line JSON string (append-ready; no embedded newline).

    Raises:
        TelemetryError: On a ``failureKinds`` entry with an unknown/missing ``kind``,
            or a present-but-malformed ``verdictByTier`` / ``tierEvents``.
    """
    row: dict[str, Any] = {
        "v": 3,
        "utc": run_summary.get("utc") or _now_utc(),
        "runId": run_summary.get("runId"),
        "target": run_summary.get("target"),
    }
    for key, default in _LEDGER_ROW_DEFAULTS.items():
        row[key] = run_summary.get(key, default)
    row["perTask"] = _normalize_per_task(run_summary.get("perTask"))
    row["failureKinds"] = _validate_failure_kinds(run_summary.get("failureKinds"))
    row["degraded"] = _validate_degraded(run_summary.get("degraded"))
    row["parentTokens"] = _normalize_parent_tokens(run_summary.get("parentTokens"))
    # AT-L20 additive keys: PRESENCE-discriminated (absent ⇒ omitted, never null);
    # present ⇒ fail-closed validation (a present None is malformed, not absent).
    if "verdictByTier" in run_summary:
        row["verdictByTier"] = _validate_verdict_by_tier(
            run_summary["verdictByTier"], where="build_ledger_row"
        )
    if "tierEvents" in run_summary:
        row["tierEvents"] = _validate_tier_events(
            run_summary["tierEvents"], where="build_ledger_row"
        )
    # Advisor-executor additive key (DESIGN §3.9): PRESENCE-discriminated (absent ⇒
    # omitted, the pre-feature row byte-preserved; present ⇒ fail-closed validation —
    # a present None is malformed, not absent).
    if "advisor" in run_summary:
        row["advisor"] = _validate_advisor_ledger(
            run_summary["advisor"], where="build_ledger_row"
        )
    if run_summary.get("calibration"):
        row["calibration"] = True
    # DET-08: sort_keys pins the serialized byte order — pass-through maps
    # (streaksByClass, taskDurationsByClass, effectiveModes, …) would otherwise
    # leak PRODUCER dict-insertion order into the committed calibration ledger
    # (two byte-different rows for the same run summary). Safe: every reader
    # (read_ledger + the *_of accessors + class_median) is key-based, never
    # position- or byte-based.
    return json.dumps(row, separators=(",", ":"), sort_keys=True)


def append_ledger_row(path: str | Path, row: str) -> None:
    """Append a one-line ledger *row* to the committed ledger at *path* (append-only).

    Never creates the file: the ledger is a committed, header-carrying artifact (T4
    creates it). Appending to a MISSING file RAISES (M4-L10/M1-L3 — the durability
    promise is kept or loudly deferred, never quietly recreated).

    Args:
        path: The ledger file path.
        row: The one-line JSON row (from :func:`build_ledger_row`).

    Raises:
        TelemetryError: When the ledger file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise TelemetryError(
            f"append_ledger_row: ledger {str(path)!r} does not exist — the ledger is a "
            "committed, header-carrying artifact created at closeout (T4); append never "
            "creates it (M4-L10/M1-L3). Create it first. Escalate."
        )
    with p.open("a", encoding="utf-8") as fh:
        fh.write(row.rstrip("\n") + "\n")


# ---------------------------------------------------------------------------
# 7. CLI (worker tooling) — emit-trailer
# ---------------------------------------------------------------------------


def _emit_trailer(
    *,
    repo_root: str,
    index: int,
    verify_exit: int,
    passed: int | None,
    failed: int | None,
    skipped: int | None,
    lint: int | None,
    paths: list[str] | None,
    owned_exit: int | None = None,
) -> str:
    """Build the complete single-line ``Kata-Checkpoint:`` trailer (staged mode).

    When *paths* is ``None`` the staged paths are resolved via
    ``git -c core.quotepath=off diff --cached --name-only --no-renames`` against
    *repo_root* (gate v1 MED-5 + gate v2 F3 — ``ls-files -s`` emits nothing for a
    staged deletion, and rename detection is ``diff.renames``-config-dependent;
    ``--no-renames`` + quotepath pin a deterministic, deletion-visible set). An empty
    staging area maps to a worker-facing stage-first error (gate v2 F10).

    Raises:
        TelemetryError: On an empty staging area or an unresolvable path.
    """
    if paths is None:
        out = _run_git(
            repo_root, ["diff", "--cached", "--name-only", "--no-renames"]
        ).stdout
        resolved = [line.strip() for line in out.splitlines() if line.strip()]
    else:
        resolved = list(paths)
    if not resolved:
        raise TelemetryError(
            "nothing staged — stage the chunk before emitting the checkpoint trailer "
            "(gate v2 F10; the stage → emit → commit ordering mandate)."
        )
    digest = evidence_digest(repo_root, resolved, commit=None)
    verify: dict[str, Any] = {"exit": verify_exit}
    if owned_exit is not None:
        verify["owned"] = owned_exit
    if passed is not None:
        verify["passed"] = passed
    if failed is not None:
        verify["failed"] = failed
    if skipped is not None:
        verify["skipped"] = skipped
    trailer: dict[str, Any] = {"v": 1, "i": index, "verify": verify}
    if lint is not None:
        trailer["lint"] = lint
    trailer["evidence"] = digest
    return f"{_TRAILER_KEY} " + json.dumps(trailer, separators=(",", ":"))


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build the ``kata_telemetry`` CLI argument parser."""
    parser = argparse.ArgumentParser(prog="kata_telemetry")
    sub = parser.add_subparsers(dest="command", required=True)
    emit = sub.add_parser(
        "emit-trailer",
        help="compute the staged-mode evidence digest and print the checkpoint trailer",
    )
    emit.add_argument("--repo-root", required=True, help="the worker's worktree root")
    emit.add_argument("--index", type=int, required=True, help="the checkpoint index i")
    emit.add_argument("--verify-exit", type=int, required=True, help="the verify exit code")
    emit.add_argument(
        "--owned-exit", type=int, default=None,
        help="the OWNED-FILE-scoped verify exit code (Amendment #5/C-1; optional)",
    )
    emit.add_argument("--passed", type=int, default=None)
    emit.add_argument("--failed", type=int, default=None)
    emit.add_argument("--skipped", type=int, default=None)
    emit.add_argument("--lint", type=int, default=None)
    emit.add_argument("--paths", nargs="*", default=None, help="explicit chunk paths")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry: ``python -m kata_telemetry emit-trailer ...``.

    Prints exactly one line starting ``Kata-Checkpoint: `` to stdout on success.
    A :class:`TelemetryError` (empty staging, unresolvable path) prints the
    worker-facing message to stderr and returns 1; a missing required ``--repo-root``
    is an argparse usage error (exit 2).

    Args:
        argv: The argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code (0 success, 1 telemetry error).
    """
    args = _build_arg_parser().parse_args(argv)
    if args.command == "emit-trailer":
        try:
            line = _emit_trailer(
                repo_root=args.repo_root,
                index=args.index,
                verify_exit=args.verify_exit,
                owned_exit=args.owned_exit,
                passed=args.passed,
                failed=args.failed,
                skipped=args.skipped,
                lint=args.lint,
                paths=args.paths,
            )
        except TelemetryError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(line)
        return 0
    return 2  # pragma: no cover — argparse enforces a subcommand


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
