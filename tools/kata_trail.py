"""kata_trail.py — durable-cursor helper (restore-hardening B1 + trust-model TM-C3/C4).

Snapshots the run's cursor file (``.kata/board.md`` today; the board→cursor rename
rides a later wave) — and, for run-scoped snapshots, its pointed-to payload files
under ``.kata/payloads/`` — to an orphan git ref via git PLUMBING only.  The call
chain is:

    git hash-object -w <file>            # write blob(s) to object store
    git mktree  (stdin: mode type sha TAB name)   # build tree(s) (no index touch)
    git commit-tree <tree> [-p <prior>]  # build commit (no index touch)
    git update-ref <ref> <commit>        # atomically point the ref

Invariants (DESIGN §2 B1 / D133; trust-model DESIGN §2.5):
- NEVER touches the working tree or the real index.
- NEVER writes to refs/heads/* or the integration ref.
- NEVER pushes.  There is no push path in this module at all — ``cursor.pushTrail``
  is READ here (:func:`read_push_trail`) but the OFFER and the act belong to
  closeout, later.  Default is never-push.
- Commits ONLY the cursor file (+ its run's payload files) — never state.json,
  never source files.
- On a busy ``<ref>.lock``: retry ONCE, then return a skip sentinel.
- When the cursor file is absent: return a skip sentinel immediately.
- On any subprocess or OS error: return a skip sentinel (never raise to the caller).

Ref layout
----------
``refs/kata/trail``
    The LEGACY ref — unchanged, byte-for-byte, for backward compatibility.  Written
    ONLY by :func:`snapshot_board` (the PreCompact hook's entry point).  Run-scoped
    snapshots never touch it.

``refs/kata/trails/<runId>``
    The PER-RUN ref (RS-L3: per-arm cursors get per-arm durability, so fan-out
    snapshots never contend on one ref).

    **DEVIATION, forced by git — recorded honestly.**  DESIGN §2.5 specifies
    ``refs/kata/trail/<runId>``.  That is not constructible while the legacy ref
    exists: git's ref namespace forbids a directory/file conflict, so
    ``refs/kata/trail`` (a ref) and ``refs/kata/trail/<runId>`` (implying a
    directory of that name) cannot coexist —::

        fatal: update_ref failed for ref 'refs/kata/trail/run-123': cannot lock ref
        'refs/kata/trail/run-123': 'refs/kata/trail' exists; cannot create
        'refs/kata/trail/run-123'

    Both DESIGN intents (per-run namespacing AND an unchanged legacy ref) survive
    under the pluralised segment ``refs/kata/trails/<runId>``, which also keeps a
    clean enumerable prefix for fan-out roll-up.  The namespace segment is the only
    thing that moved.

Public API
----------
snapshot_board(repo_root=".") -> dict
    LEGACY, unchanged contract.  Snapshots the cursor file alone to
    ``refs/kata/trail``.  ``{"committed": sha}`` | ``{"skipped": reason}``.
snapshot_cursor(repo_root=".", *, run_id, cursor_path=None) -> dict
    Run-scoped snapshot: cursor file + its payloads → ``refs/kata/trails/<runId>``.
should_snapshot(line_type) -> bool
snapshot_on_append(line_type, *, run_id, ...) -> dict | None
    The CADENCE surface the W3 seam calls after every cursor append.  Fires on
    PHASE and VERDICT only; returns a cursor-appendable RECORD (including the skip
    case), or ``None`` when the appended type is not a trigger.
snapshot_record(result, *, run_id, trigger) -> dict
push_receipt_record(*, run_id, ref, commit, remote) -> dict
format_record_line(record) -> str
derive_resilience(records, *, push_trail_configured=False) -> dict
read_push_trail(config) -> bool

Nothing in this module raises out of the durability path.  The pure helpers
(:func:`derive_resilience`, :func:`read_push_trail`, :func:`run_trail_ref`,
:func:`snapshot_record`, :func:`format_record_line`) do no I/O; the two config /
identity guards fail CLOSED with ``ValueError`` on a malformed present value,
matching the ``kata_config`` / ``kata_models`` house style.
"""

from __future__ import annotations

import datetime
import re
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: The legacy orphan ref.  UNCHANGED for BC — written only by snapshot_board().
_TRAIL_REF = "refs/kata/trail"

#: Per-run ref prefix (RS-L3).  Pluralised segment — see the module docstring's
#: recorded deviation: git forbids refs/kata/trail AND refs/kata/trail/<runId>.
RUN_TRAIL_REF_PREFIX = "refs/kata/trails/"

#: The cursor file, relative to the repo root.  The board→cursor file RENAME rides
#: a later wave; this module consumes the cursor as an OPAQUE path (contract-only
#: coupling to the cursor-grammar owner — nothing here parses cursor lines).
DEFAULT_CURSOR_RELPATH = (".kata", "board.md")

#: Payload directory convention (DESIGN §2.2): .kata/payloads/<runId>-<seq>.json.
PAYLOAD_DIRNAME = "payloads"

#: Snapshot cadence trigger set (DESIGN §2.5 / TM-C3): every PHASE and VERDICT
#: append fires a snapshot.  No other line type does.
SNAPSHOT_TRIGGER_TYPES = frozenset({"PHASE", "VERDICT"})

#: Cursor-appendable record kinds produced by this module.
RECORD_KIND_SNAPSHOT = "trail-snapshot"
RECORD_KIND_PUSH_RECEIPT = "trail-push-receipt"

#: Derived resilience levels (DESIGN §2.5) — DERIVED from recorded fact, never
#: asserted, and never read off the config flag.
RESILIENCE_FULL = "full"
RESILIENCE_LOCAL = "local"
RESILIENCE_DEGRADED = "degraded"

#: Guardian scale terms (DESIGN §6.2) — the ONLY user-facing trust vocabulary.
#: Display strings are the §6.2 table cells VERBATIM (no builder invention).
RESILIENCE_GUARDIAN: dict[str, str] = {
    RESILIENCE_FULL: "Verified",
    RESILIENCE_LOCAL: "Partially verified",
    RESILIENCE_DEGRADED: "Honor-system",
}
RESILIENCE_DISPLAY: dict[str, str] = {
    RESILIENCE_FULL: (
        "Verified (full: push receipt recorded on the cursor, never the config flag)"
    ),
    RESILIENCE_LOCAL: "Partially verified (local)",
    RESILIENCE_DEGRADED: "Honor-system (degraded/skips detected)",
}

#: The kata.config key that carries the operator's remembered push preference.
#: Nested form: {"cursor": {"pushTrail": true}}.  Default (absent) = never push.
CONFIG_KEY_PUSH_TRAIL = "cursor.pushTrail"

# Q-16 (2026-07-12 health review): every git subprocess call carries this timeout so a
# stale index.lock or a credential prompt in a hostile target repo can never stall the
# snapshot forever.  The durability path is FAIL-SOFT — a timeout returns a skip
# sentinel (never raises to a compaction caller), exactly like every other git error.
_GIT_TIMEOUT_S = 60

# --- guards (every one of these feeds a git argv element or a tree entry name) ---

#: runId grammar guard (DESIGN §2.2: run-<utc-compact>-<hex>).  Deliberately
#: stricter than git's ref rules: alphanumeric segments joined by single hyphens.
#: No slash, dot, whitespace, control char, or leading/trailing hyphen can survive,
#: so a runId can never traverse the ref namespace or inject a tree entry.
_RUN_ID_RE = re.compile(r"run-[0-9A-Za-z]+(?:-[0-9A-Za-z]+)*\Z")

#: Cursor file basename guard — becomes a tree entry name.
_CURSOR_NAME_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]{0,63}\.md\Z")

#: Control characters + ANSI-range bytes stripped from any rendered record text
#: (DESIGN §6.3: a cursor line must never be able to repaint a fake receipt).
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")

#: A 40-char lowercase hex git SHA — used to validate a push receipt before it is
#: allowed to raise the derived resilience level to "full" (fail-closed).
_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess:
    """Run a git plumbing command and raise CalledProcessError on non-zero exit.

    shell=False is enforced by passing a fixed argv list.  Never accepts
    untrusted strings in the command position.  A ``_GIT_TIMEOUT_S`` timeout (Q-16)
    raises ``subprocess.TimeoutExpired``, which the snapshot entry points map to a
    skip sentinel (fail-soft — never raised to the caller).
    """
    return subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
        timeout=_GIT_TIMEOUT_S,
    )


def _is_lock_error(exc: subprocess.CalledProcessError, root: Path, ref: str) -> bool:
    """Return True when a git error looks like ref-lock contention.

    Two signals are checked for robustness across platforms and git versions:
    1. The stderr from git mentions "lock" (standard across git builds).
    2. Fallback: the lock file itself exists on disk (belt-and-suspenders for
       Windows environments where git error messages may differ).
    """
    if "lock" in (exc.stderr or "").lower():
        return True
    # Fallback: check the canonical lock-file path for this ref
    parts = ref.split("/")
    lock_path = root.joinpath(".git", *parts[:-1], parts[-1] + ".lock")
    return lock_path.exists()


def _tree_sort_key(entry: tuple[str, str, str, str]) -> str:
    """Canonical git tree ordering key: tree names sort as if suffixed with '/'.

    Determinism Doctrine: the entry order is computed, never left to filesystem
    iteration order.  ``git mktree`` normalises order itself, but sorting here
    makes the constructed stdin byte-identical run to run.
    """
    _mode, obj_type, _sha, name = entry
    return name + "/" if obj_type == "tree" else name


def _mktree(entries: list[tuple[str, str, str, str]], *, root: Path) -> str:
    """Build a tree object from ``(mode, type, sha, name)`` entries; return its SHA.

    ``git mktree`` reads ls-tree format from stdin; it does NOT touch the real
    index (unlike git update-index / git write-tree, which would require a temp
    GIT_INDEX_FILE to be side-effect-free).

    IMPORTANT: pass bytes (not text=True) to avoid Windows CRLF translation in
    subprocess stdin, which would make git mktree see "board.md\\r" as the
    filename and corrupt the tree entry.

    Every ``name`` reaching here has already passed a character guard
    (``_CURSOR_NAME_RE`` / the per-run payload pattern), so no entry can contain a
    TAB or newline and break the record framing.
    """
    lines = "".join(
        f"{mode} {obj_type} {sha}\t{name}\n"
        for mode, obj_type, sha, name in sorted(entries, key=_tree_sort_key)
    )
    result = subprocess.run(
        ["git", "mktree"],
        input=lines.encode("latin-1"),
        cwd=str(root),
        capture_output=True,
        check=True,
        timeout=_GIT_TIMEOUT_S,  # Q-16: a hung mktree ⇒ skip sentinel (fail-soft)
    )
    return result.stdout.strip().decode("ascii")


def _hash_object(path: Path, *, root: Path) -> str:
    """Write ``path`` to the object store and return its blob SHA."""
    return _run(["git", "hash-object", "-w", str(path)], cwd=root).stdout.strip()


def _resolve_cursor_path(root: Path, cursor_path: str | Path | None) -> Path:
    """Resolve the cursor file path and confine it to the repo root.

    The cursor is consumed as an OPAQUE path (the contract boundary with the
    cursor-grammar owner — nothing here parses its lines).  A caller-supplied path
    is still confined: it must resolve inside ``root`` and its basename must pass
    ``_CURSOR_NAME_RE``, because that basename becomes a git tree entry name.
    """
    if cursor_path is None:
        return root.joinpath(*DEFAULT_CURSOR_RELPATH)
    candidate = Path(cursor_path)
    resolved = candidate if candidate.is_absolute() else root / candidate
    resolved = resolved.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"cursor_path must resolve inside the repo root, got {resolved!s}"
        ) from exc
    if not _CURSOR_NAME_RE.fullmatch(resolved.name):
        raise ValueError(f"cursor file name is not tree-safe: {resolved.name!r}")
    return resolved


def _collect_payloads(root: Path, run_id: str) -> list[Path]:
    """Return this run's payload files under ``.kata/payloads/``, sorted by name.

    "Pointed-to payloads" (DESIGN §2.5) are resolved by the ``<runId>-<seq>.json``
    FILENAME CONVENTION (DESIGN §2.2), NOT by parsing the cursor.  That is the
    deliberate contract boundary: this module never reads cursor grammar, so a
    grammar change can never break durability.  The convention is a superset of
    the strictly-pointed-to set within a single run, which is the safe direction —
    an unreferenced payload of this run gets snapshotted; a payload of ANOTHER run
    never does.

    Symlinks are excluded: ``git hash-object`` would follow them, so a symlinked
    payload could pull arbitrary out-of-repo content into the snapshot.
    """
    payload_dir = root / DEFAULT_CURSOR_RELPATH[0] / PAYLOAD_DIRNAME
    if not payload_dir.is_dir():
        return []
    pattern = re.compile(rf"{re.escape(run_id)}-\d+\.json\Z")
    found = [
        entry
        for entry in payload_dir.iterdir()
        if pattern.fullmatch(entry.name)
        and not entry.is_symlink()
        and entry.is_file()
    ]
    return sorted(found, key=lambda p: p.name)


def _snapshot(
    root: Path,
    *,
    ref: str,
    cursor_file: Path,
    payloads: list[Path],
) -> dict[str, Any]:
    """Core snapshot: build the tree, commit it, advance ``ref``.  Never raises.

    Returns ``{"committed": sha, "ref": ref, "payloads": n}`` or
    ``{"skipped": reason, "ref": ref, "payloads": n}``.
    """
    payload_count = len(payloads)
    try:
        if not cursor_file.exists():
            return {"skipped": "no-board", "ref": ref, "payloads": 0}

        # -- Step 1: blobs -------------------------------------------------- #
        entries: list[tuple[str, str, str, str]] = [
            ("100644", "blob", _hash_object(cursor_file, root=root), cursor_file.name)
        ]

        # -- Step 2: the payloads subtree (TM-C4 "durable at the moment they
        #    exist" — the snapshot is the mechanism that makes that true) ----- #
        if payloads:
            payload_entries = [
                ("100644", "blob", _hash_object(p, root=root), p.name) for p in payloads
            ]
            payload_tree = _mktree(payload_entries, root=root)
            entries.append(("040000", "tree", payload_tree, PAYLOAD_DIRNAME))

        tree_sha = _mktree(entries, root=root)

        # -- Step 3: the commit (chains onto this ref's own prior tip) ------- #
        now_utc = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        commit_args = ["git", "commit-tree", tree_sha, "-m", f"kata-trail {now_utc}"]
        try:
            prior = _run(["git", "rev-parse", "--verify", ref], cwd=root)
            commit_args += ["-p", prior.stdout.strip()]
        except subprocess.CalledProcessError:
            pass  # No prior ref — this is the first snapshot (orphan commit)

        commit_sha = _run(commit_args, cwd=root).stdout.strip()

        # -- Step 4: advance the ref, retry ONCE on a busy lock (D133) ------- #
        for attempt in range(2):  # attempt 0 = first try; attempt 1 = retry
            try:
                _run(["git", "update-ref", ref, commit_sha], cwd=root)
                return {
                    "committed": commit_sha,
                    "ref": ref,
                    "payloads": payload_count,
                }
            except subprocess.CalledProcessError as exc:
                if _is_lock_error(exc, root, ref):
                    if attempt == 0:
                        continue  # retry once
                    return {"skipped": "ref-lock", "ref": ref, "payloads": payload_count}
                raise  # Non-lock subprocess error: fall through to outer handler

        return {  # pragma: no cover - loop always returns
            "skipped": "ref-lock",
            "ref": ref,
            "payloads": payload_count,
        }

    except subprocess.TimeoutExpired as exc:
        # Q-16: a git call exceeded _GIT_TIMEOUT_S (stale lock / credential prompt in a
        # hostile target). Fail-soft — skip, never raise to the compaction caller.
        return {
            "skipped": f"git-timeout: {exc.timeout}s",
            "ref": ref,
            "payloads": payload_count,
        }
    except subprocess.CalledProcessError as exc:
        return {
            "skipped": f"git-error: {exc.returncode} {(exc.stderr or '').strip()!r}",
            "ref": ref,
            "payloads": payload_count,
        }
    except OSError as exc:
        return {"skipped": f"os-error: {exc}", "ref": ref, "payloads": payload_count}
    except Exception as exc:  # noqa: BLE001
        # Belt-and-suspenders: the durability path must NEVER propagate
        return {
            "skipped": f"unexpected: {type(exc).__name__}: {exc}",
            "ref": ref,
            "payloads": payload_count,
        }


# ---------------------------------------------------------------------------
# Public API — identity
# ---------------------------------------------------------------------------


def run_trail_ref(run_id: str) -> str:
    """Return the per-run trail ref for ``run_id``.

    Args:
        run_id: A DESIGN §2.2 run identifier (``run-<utc-compact>-<hex>``).

    Returns:
        ``refs/kata/trails/<runId>``.

    Raises:
        ValueError: ``run_id`` does not match the run-identity grammar.  This
            guard is load-bearing: the result becomes a git argv element, so a
            malformed id is refused rather than escaped.
    """
    if not isinstance(run_id, str) or not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError(
            f"run_id must match the run-identity grammar 'run-<alnum>[-<alnum>…]', "
            f"got {run_id!r}"
        )
    return RUN_TRAIL_REF_PREFIX + run_id


# ---------------------------------------------------------------------------
# Public API — snapshots
# ---------------------------------------------------------------------------


def snapshot_board(repo_root: str = ".") -> dict[str, Any]:
    """Snapshot the cursor file to the LEGACY ``refs/kata/trail`` — unchanged (BC).

    This is the pre-existing entry point (the PreCompact hook calls it).  Its
    contract is byte-for-byte what it was: cursor file ONLY (no payloads), legacy
    ref ONLY.  Run-scoped snapshots use :func:`snapshot_cursor` and never touch
    this ref.

    Parameters
    ----------
    repo_root:
        Root of the git repository (the directory that contains ``.git/``).
        Defaults to the current working directory.

    Returns
    -------
    dict
        ``{"committed": "<sha>"}`` on success (plus informational ``ref`` /
        ``payloads`` keys).  ``{"skipped": "<reason>"}`` on any non-fatal
        condition (absent cursor, busy lock, or subprocess/OS error).

    This function never raises.  The durability path must never crash a run.
    """
    try:
        root = Path(repo_root).resolve()
        cursor_file = root.joinpath(*DEFAULT_CURSOR_RELPATH)
    except OSError as exc:
        return {"skipped": f"os-error: {exc}", "ref": _TRAIL_REF, "payloads": 0}
    return _snapshot(root, ref=_TRAIL_REF, cursor_file=cursor_file, payloads=[])


def snapshot_cursor(
    repo_root: str = ".",
    *,
    run_id: str,
    cursor_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run-scoped snapshot: cursor file + this run's payloads → per-run trail ref.

    Implements DESIGN §2.5's content extension (TM-C3 cadence + TM-C4 durability:
    the snapshot is the mechanism that makes "durable at the moment they exist"
    true) and RS-L3's per-run refs.  The legacy ref is NOT touched.

    Parameters
    ----------
    repo_root:
        Root of the git repository.
    run_id:
        The run identity (keyword-only, required — there is no "current run"
        fallback; run membership is never inferred).
    cursor_path:
        Optional override for the cursor file, consumed as an OPAQUE path.  Must
        resolve inside ``repo_root``.  Defaults to ``.kata/board.md``.

    Returns
    -------
    dict
        ``{"committed": sha, "ref": ..., "payloads": n}`` or
        ``{"skipped": reason, "ref": ..., "payloads": n}``.  Never raises.
    """
    try:
        ref = run_trail_ref(run_id)
    except ValueError as exc:
        return {"skipped": f"bad-run-id: {exc}", "ref": None, "payloads": 0}
    try:
        root = Path(repo_root).resolve()
        cursor_file = _resolve_cursor_path(root, cursor_path)
        payloads = _collect_payloads(root, run_id)
    except ValueError as exc:
        return {"skipped": f"bad-cursor-path: {exc}", "ref": ref, "payloads": 0}
    except OSError as exc:
        return {"skipped": f"os-error: {exc}", "ref": ref, "payloads": 0}
    return _snapshot(root, ref=ref, cursor_file=cursor_file, payloads=payloads)


# ---------------------------------------------------------------------------
# Public API — the cadence surface (the W3 seam's call site)
# ---------------------------------------------------------------------------


def should_snapshot(line_type: str) -> bool:
    """True when appending ``line_type`` must fire a trail snapshot (DESIGN §2.5)."""
    return line_type in SNAPSHOT_TRIGGER_TYPES


def snapshot_on_append(
    line_type: str,
    *,
    run_id: str,
    repo_root: str = ".",
    cursor_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Fire the snapshot cadence for a just-appended cursor line.

    **This is the surface the W3 seam calls.**  DESIGN §2.5: the cadence fires on
    every PHASE and VERDICT append — mid-gate resume without re-running the gate.

    Boundary, stated honestly: this function performs the snapshot and RETURNS a
    cursor-appendable record (including the skip case — the skip sentinel becomes
    a RECORDED event, R-M4).  It does NOT append that record to the cursor: the
    append is a seam act, wired in W3 by the cursor's single seam writer.  Nothing
    here writes to the cursor.

    Parameters
    ----------
    line_type:
        The TYPE of the line that was just appended.
    run_id:
        The run identity (keyword-only, required).
    repo_root, cursor_path:
        As :func:`snapshot_cursor`.

    Returns
    -------
    dict | None
        ``None`` when ``line_type`` is not a cadence trigger (nothing fired,
        nothing to record).  Otherwise the record from :func:`snapshot_record`.
    """
    if not should_snapshot(line_type):
        return None
    result = snapshot_cursor(repo_root, run_id=run_id, cursor_path=cursor_path)
    return snapshot_record(result, run_id=run_id, trigger=line_type)


def snapshot_record(
    result: dict[str, Any], *, run_id: str, trigger: str
) -> dict[str, Any]:
    """Turn a snapshot result into the cursor-appendable RECORD shape (R-M4).

    The skip sentinel stops being a silently-swallowed dict and becomes a recorded
    fact, so the declared resilience level is a fold over recorded fact rather than
    an assertion.  ``derive_resilience`` consumes exactly this shape.
    """
    committed = result.get("committed")
    return {
        "kind": RECORD_KIND_SNAPSHOT,
        "runId": run_id,
        "trigger": trigger,
        "outcome": "committed" if committed else "skipped",
        "commit": committed,
        "reason": None if committed else result.get("skipped"),
        "ref": result.get("ref"),
        "payloads": result.get("payloads", 0),
    }


def push_receipt_record(
    *, run_id: str, ref: str, commit: str, remote: str
) -> dict[str, Any]:
    """Build the push-receipt record shape — the ONLY thing that can derive "full".

    No push path exists in this module and none is built here: ``cursor.pushTrail``
    defaults to never-push and the OFFER belongs to closeout (DESIGN §2.5).  This
    constructor exists so that when closeout does perform a push, the receipt it
    records on the cursor has one canonical shape that :func:`derive_resilience`
    recognises.  A receipt whose ``commit`` is not a 40-char hex SHA is ignored by
    the derivation (fail-closed — an unverifiable receipt never raises the level).
    """
    return {
        "kind": RECORD_KIND_PUSH_RECEIPT,
        "runId": run_id,
        "ref": ref,
        "commit": commit,
        "remote": remote,
    }


def format_record_line(record: dict[str, Any]) -> str:
    """Render a record as a one-line cursor ``msg`` — control-character-scrubbed.

    DESIGN §6.3 rendering law: all cursor-derived text is control-character/ANSI
    stripped so a line can never repaint a fake receipt.  The field separator
    ``" | "`` is also neutralised (``|`` → ``/``) so a rendered value cannot forge
    extra cursor fields.
    """
    kind = record.get("kind")
    if kind == RECORD_KIND_PUSH_RECEIPT:
        parts = [
            RECORD_KIND_PUSH_RECEIPT,
            f"ref={record.get('ref')}",
            f"remote={record.get('remote')}",
            f"commit={record.get('commit')}",
        ]
    else:
        parts = [str(kind), str(record.get("trigger"))]
        if record.get("outcome") == "committed":
            parts.append(f"committed={record.get('commit')}")
        else:
            parts.append(f"skipped={record.get('reason')}")
        parts += [f"ref={record.get('ref')}", f"payloads={record.get('payloads')}"]
    return _scrub(" ".join(parts))


def _scrub(text: str) -> str:
    """Strip control/ANSI-range characters and neutralise the cursor separator."""
    return _CTRL_RE.sub("", str(text)).replace("|", "/")


# ---------------------------------------------------------------------------
# Public API — the derivation (pure fold over recorded facts)
# ---------------------------------------------------------------------------


def derive_resilience(
    records: Iterable[dict[str, Any]],
    *,
    push_trail_configured: bool = False,
) -> dict[str, Any]:
    """DERIVE the run's resilience level from recorded facts (DESIGN §2.5, R-M4).

    A PURE fold — no I/O, no git, no config lookup.  The rules, exactly:

    * **degraded** — at least one recorded snapshot SKIP.  Skips dominate: a run
      with a push receipt and a skip is still degraded, because a gap in the
      snapshot record is a gap in what was preserved.
    * **full** — no skips AND at least one VALID push receipt recorded on the
      cursor.  ``push_trail_configured`` can NEVER produce this level; only a
      receipt can.  A receipt missing a 40-hex ``commit`` is not valid and is
      ignored (fail-closed).
    * **local** — everything else, including a run with NO records yet.  This is
      the healthy default: at run start nothing has been snapshotted, and the
      honest declaration is ``Partially verified (local)`` — honest state, not a
      defect report (pass-1 SHIP residual 6).  ``degraded`` is reserved for an
      OBSERVED skip.

    Args:
        records: Cursor records (any iterable of dicts).  Unrecognised kinds are
            ignored, so the whole cursor record stream can be passed in.
        push_trail_configured: The ``cursor.pushTrail`` config flag, accepted for
            call-site convenience and ECHOED in ``basis`` for display only.  It is
            structurally excluded from the level computation — the "never the
            config flag" rule of DESIGN §6.2 is enforced here, not merely stated.

    Returns:
        ``{"level", "guardian", "mode", "display", "basis"}`` where ``display`` is
        the DESIGN §6.2 Guardian-scale cell verbatim.
    """
    committed = skipped = receipts = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        kind = record.get("kind")
        if kind == RECORD_KIND_SNAPSHOT:
            if record.get("outcome") == "committed":
                committed += 1
            elif record.get("outcome") == "skipped":
                skipped += 1
        elif kind == RECORD_KIND_PUSH_RECEIPT:
            commit = record.get("commit")
            if isinstance(commit, str) and _SHA_RE.fullmatch(commit) and record.get("ref"):
                receipts += 1

    if skipped:
        level = RESILIENCE_DEGRADED
    elif receipts:
        level = RESILIENCE_FULL
    else:
        level = RESILIENCE_LOCAL

    return {
        "level": level,
        "guardian": RESILIENCE_GUARDIAN[level],
        "mode": level,
        "display": RESILIENCE_DISPLAY[level],
        "basis": {
            "snapshots": committed,
            "skips": skipped,
            "pushReceipts": receipts,
            # Informational ONLY — never an input to `level` above.
            "pushConfigured": bool(push_trail_configured),
        },
    }


# ---------------------------------------------------------------------------
# Public API — the config key
# ---------------------------------------------------------------------------


def read_push_trail(config: dict | None) -> bool:
    """Read ``cursor.pushTrail`` from a parsed ``kata.config``.

    Semantics (DESIGN §2.5): **default never-push.**  Absent config, absent
    ``cursor`` block, or absent ``pushTrail`` key all mean ``False`` — today's
    behaviour, byte-for-byte (BC).  The flag is a REMEMBERED PREFERENCE for the
    offer closeout will later present at the human push gate; it authorises
    nothing on its own and no code path in this module pushes.

    Critically, this value is NOT an input to :func:`derive_resilience`'s level —
    "full" requires a push RECEIPT recorded on the cursor, never this flag.

    Args:
        config: The parsed ``kata.config`` object, or ``None``.

    Returns:
        The remembered preference; ``False`` when unset.

    Raises:
        ValueError: A PRESENT-but-malformed value (non-dict ``cursor`` block or a
            non-boolean ``pushTrail``).  Fail-closed, matching the
            ``kata_config.validate_core_config`` house rule that a
            present-but-broken value is never silently coerced to a default.
    """
    if config is None:
        return False
    if not isinstance(config, dict):
        raise ValueError(f"kata.config must be a dict, got {type(config).__name__}")
    cursor = config.get("cursor")
    if cursor is None:
        return False
    if not isinstance(cursor, dict):
        raise ValueError(
            f"kata.config.cursor must be a dict, got {type(cursor).__name__}"
        )
    if "pushTrail" not in cursor:
        return False
    value = cursor["pushTrail"]
    if not isinstance(value, bool):
        raise ValueError(
            f"{CONFIG_KEY_PUSH_TRAIL} must be a bool when present, got {value!r}"
        )
    return value
