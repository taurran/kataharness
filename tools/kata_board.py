"""kata_board.py — the CURSOR engine: single emitter, canonical parser, pure fold.

The run's one log IS the **cursor** (DESIGN §2.1 — Trust Model): a run-header block
plus an append-only sequence of typed lines.  This module is the single writer and
the single canonical parser of that grammar, plus the pure folds computed over it.
Stdlib only; no sub-process calls; no side-effects at import time.

The CONCEPT is the cursor; the FILE is still ``board.md`` this wave — the
board→cursor heritage rename rides a later task (PLAN W4 ``coordinate-skills-migration``).
``CURSOR_FILENAME`` exists so that rename is one edit.

Grammar (transcribed from DESIGN §2.2, not re-derived)::

    cursor        ::= run-header line*
    run-header    ::= "RUN " run-id NL
                      ( "prev-run: "     run-id  NL )?
                      ( "parent-run: "   run-id  NL )?
                      ( "prev-segment: " path    NL )?
    run-id        ::= "run-" utc-compact "-" hex+
    line          ::= utc FS seq-field FS agent-id FS type FS task-id FS msg NL
    FS            ::= " | "
    seq-field     ::= seq ( "~" parent-seq )?
    seq           ::= digit+
    type          ::= worker-type | orch-type | seam-type
    worker-type   ::= "CLAIM" | "DONE" | "BLOCK" | "ESCALATE" | "NOTE" | "PROGRESS"
    orch-type     ::= "DECISION"
    seam-type     ::= "PHASE" | "VERDICT" | "SPAWN" | "DOWN" | "DENY"
    msg           ::= one-line-text ( " payload=" path )?

The old 5-field grammar parses NOWHERE: a legacy line is a parse REFUSAL
(``CursorParseError``), never a silent skip.

Writer rules (DESIGN §2.3 / L3 — LESSONS-LEARNED):
  WORKERS       append CLAIM / DONE / BLOCK / ESCALATE / NOTE / PROGRESS
  ORCHESTRATOR  appends DECISION, and calls write_state / update_task
  THE SEAM      appends PHASE / VERDICT / SPAWN / DOWN / DENY (never a worker)

Workers MUST NOT call write_state or update_task; no writer may bypass this module
to write the cursor file directly.  This separation is the fix for the shared-state
corruption documented in L3.

Determinism Doctrine: every fold here is PURE — no clock, no filesystem, no
environment — and side effects happen only AFTER a fold completes (law 6/7).
Randomness mints identity only (law 9): ``mint_run_id`` is the sole entropy sink and
every derived computation is reproducible given the id.  Ordering of record is
``(runId, seq, file-position)`` with an explicit total-order tie-break (law 10);
**wall-clock is never load-bearing**.  Committed JSON is ``sort_keys=True`` (law 5).

Security note (from PLAN S1a threat model): kata_dir is operator-supplied; it
is sanitised by _safe_path before any filesystem sink is reached (CWE-23 guard).
Payload pointers are guarded the same way, on both write and parse.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Grammar constants
# ---------------------------------------------------------------------------

#: The cursor file's name inside .kata/.  The CONCEPT is the cursor; the FILE keeps
#: its board heritage until the rename wave.
CURSOR_FILENAME = "board.md"

#: Directory (relative to the kata dir) holding pointed-to JSON payloads.
PAYLOAD_DIRNAME = "payloads"

#: Field separator — exactly one space, pipe, one space (DESIGN §2.2 ``FS``).
FS = " | "

#: The token that introduces a payload pointer inside ``msg``.
PAYLOAD_TOKEN = " payload="

#: Worker-authored types.
WORKER_TYPES: frozenset[str] = frozenset(
    {"CLAIM", "DONE", "BLOCK", "ESCALATE", "NOTE", "PROGRESS"}
)
#: Orchestrator-authored types.
ORCH_TYPES: frozenset[str] = frozenset({"DECISION"})
#: Seam-authored types (engine mint/capture paths + the hook) — never worker-authored.
SEAM_TYPES: frozenset[str] = frozenset({"PHASE", "VERDICT", "SPAWN", "DOWN", "DENY"})
#: The closed TYPE enumeration.
CURSOR_TYPES: frozenset[str] = WORKER_TYPES | ORCH_TYPES | SEAM_TYPES

#: Types for which a ``payload=`` pointer is REQUIRED (DESIGN §2.2).
PAYLOAD_REQUIRED_TYPES: frozenset[str] = frozenset({"VERDICT"})

#: Required fields of a VERDICT payload (DESIGN §2.2 / TM-C4).
VERDICT_PAYLOAD_FIELDS: tuple[str, ...] = (
    "verdict",
    "evidencePointers",
    "judgeDispatchSeq",
    "runId",
)

#: ``run-`` + utc-compact + ``-`` + hex.  Sortable (the compact stamp leads), humane.
RUN_ID_RE = re.compile(r"\Arun-\d{8}T\d{6}Z-[0-9a-f]+\Z")

#: ``seq`` or ``seq~parent-seq``.
_SEQ_FIELD_RE = re.compile(r"\A(\d+)(?:~(\d+))?\Z")

#: Header pointer keys, in BNF emission order.
_HEADER_KEYS: tuple[str, ...] = ("prev-run", "parent-run", "prev-segment")

_RUN_PREFIX = "RUN "

_UTC_COMPACT = "%Y%m%dT%H%M%SZ"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class CursorError(Exception):
    """Base class for every cursor grammar violation."""


class CursorParseError(CursorError):
    """A cursor line/header could not be parsed.  A refusal, never a skip."""


class CursorGrammarError(CursorError):
    """A write was refused because it would not satisfy the grammar."""


# ---------------------------------------------------------------------------
# Path guard
# ---------------------------------------------------------------------------


def _safe_path(raw: str | Path) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied path, then resolve.

    Blocks any ``..`` segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree, while still allowing the
    absolute and nested-relative paths the maintainer legitimately targets.
    Sanitizes the tainted input at the boundary before any filesystem sink.

    Mirrors the identical guard in gate_emit._safe_path (keep them in sync).

    Single-writer rule: WORKERS call append_event/append_progress only.
    ONLY the orchestrator calls write_state/update_task.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"kata_board: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


def _guard_pointer(raw: str, *, what: str) -> str:
    """Guard a cursor-embedded pointer (payload / prev-segment).

    A pointer is a **kata-dir-relative** POSIX path: no absolute paths, no drive
    letters, no ``..`` segments, no whitespace (whitespace would break the
    ``" payload="`` suffix grammar), no field separator.  Raises on violation so a
    crafted pointer can never reach a filesystem sink.
    """
    if not raw:
        raise CursorGrammarError(f"kata_board: empty {what} pointer")
    if any(ch.isspace() for ch in raw):
        raise CursorGrammarError(
            f"kata_board: {what} pointer must not contain whitespace: {raw!r}"
        )
    if "|" in raw:
        raise CursorGrammarError(
            f"kata_board: {what} pointer must not contain '|': {raw!r}"
        )
    p = Path(raw)
    if p.is_absolute() or p.drive or raw.startswith(("/", "\\")):
        raise CursorGrammarError(
            f"kata_board: {what} pointer must be kata-dir-relative: {raw!r}"
        )
    if any(part == ".." for part in p.parts):
        raise CursorGrammarError(
            f"kata_board: refusing {what} pointer with '..' traversal: {raw!r}"
        )
    return raw


def _guard_field(value: str, *, what: str) -> str:
    """Guard a single non-msg field: non-empty, one line, no pipe."""
    if not isinstance(value, str) or not value.strip():
        raise CursorGrammarError(f"kata_board: {what} must be a non-empty string")
    if "\n" in value or "\r" in value:
        raise CursorGrammarError(f"kata_board: {what} must not contain a newline")
    if "|" in value:
        raise CursorGrammarError(
            f"kata_board: {what} must not contain '|' (field separator): {value!r}"
        )
    return value.strip()


# ---------------------------------------------------------------------------
# Run identity
# ---------------------------------------------------------------------------


def mint_run_id(*, now: datetime | None = None, entropy: str | None = None) -> str:
    """Mint a run id: ``run-<utc-compact>-<hex>`` (DESIGN §2.2 / TM-C2).

    Determinism Doctrine law 9 — **randomness mints identity only**.  The hex suffix
    is the sole entropy sink in this module; nothing downstream derives a decision
    from it.  Both inputs are injectable so a test pins exact bytes.
    """
    stamp = (now or datetime.now(UTC)).astimezone(UTC).strftime(_UTC_COMPACT)
    suffix = entropy if entropy is not None else secrets.token_hex(4)
    run_id = f"run-{stamp}-{suffix}"
    return validate_run_id(run_id)


def validate_run_id(run_id: str) -> str:
    """Return *run_id* if it satisfies the run-id grammar; raise otherwise."""
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        raise CursorGrammarError(
            f"kata_board: not a run-id (expected run-<utc-compact>-<hex>): {run_id!r}"
        )
    return run_id


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunHeader:
    """The run-header block.

    ``prev_run`` walks history (iteration: re-loop / loop-back); ``parent_run`` walks
    the tree (child runs, roll-up folds).  ``prev_segment`` is RESERVED — parsed and
    round-tripped, with no segmenting machinery built (DESIGN §2.2).
    """

    run_id: str
    prev_run: str | None = None
    parent_run: str | None = None
    prev_segment: str | None = None


@dataclass(frozen=True)
class CursorLine:
    """One parsed cursor line.

    ``pos`` is the line's file position (0-based over parsed lines).  It is the
    third element of the ordering key: duplicate worker seqs are LEGAL and are
    ordered by file position (DESIGN §2.2).
    """

    utc: str
    seq: int
    agent: str
    type: str
    task: str
    msg: str
    parent_seq: int | None = None
    payload: str | None = None
    pos: int = 0


@dataclass(frozen=True)
class Cursor:
    """A parsed cursor: its header plus its lines, in file order."""

    header: RunHeader
    lines: tuple[CursorLine, ...] = ()

    @property
    def run_id(self) -> str:
        return self.header.run_id


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_header(header: RunHeader) -> str:
    """Render a run-header block (trailing newline included)."""
    validate_run_id(header.run_id)
    out = [f"{_RUN_PREFIX}{header.run_id}"]
    if header.prev_run is not None:
        out.append(f"prev-run: {validate_run_id(header.prev_run)}")
    if header.parent_run is not None:
        out.append(f"parent-run: {validate_run_id(header.parent_run)}")
    if header.prev_segment is not None:
        out.append(
            f"prev-segment: {_guard_pointer(header.prev_segment, what='prev-segment')}"
        )
    return "\n".join(out) + "\n"


def format_line(
    *,
    utc: str,
    seq: int,
    agent: str,
    type: str,  # noqa: A002  (shadowing built-in intentional — matches protocol)
    task: str,
    msg: str,
    parent_seq: int | None = None,
    payload: str | None = None,
) -> str:
    """Render one cursor line (trailing newline included).

    Refuses anything the grammar forbids: an unknown TYPE, a negative seq, a field
    carrying the separator, a msg carrying the reserved ``" payload="`` token, an
    unguarded payload pointer, and a VERDICT without a payload.
    """
    if type not in CURSOR_TYPES:
        raise CursorGrammarError(
            f"kata_board: unknown TYPE {type!r}; legal: {sorted(CURSOR_TYPES)}"
        )
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
        raise CursorGrammarError(f"kata_board: seq must be a non-negative int: {seq!r}")
    if parent_seq is not None and (
        not isinstance(parent_seq, int) or isinstance(parent_seq, bool) or parent_seq < 0
    ):
        raise CursorGrammarError(
            f"kata_board: parent-seq must be a non-negative int: {parent_seq!r}"
        )

    utc = _guard_field(utc, what="utc")
    _parse_utc(utc)
    agent = _guard_field(agent, what="agent-id")
    task = _guard_field(task, what="task-id")

    if not isinstance(msg, str) or not msg.strip():
        raise CursorGrammarError("kata_board: msg must be a non-empty string")
    if "\n" in msg or "\r" in msg:
        raise CursorGrammarError("kata_board: msg must not contain a newline")
    if PAYLOAD_TOKEN in msg:
        raise CursorGrammarError(
            f"kata_board: msg must not contain the reserved token {PAYLOAD_TOKEN!r}; "
            "pass payload= explicitly"
        )
    msg = msg.strip()

    if payload is None and type in PAYLOAD_REQUIRED_TYPES:
        raise CursorGrammarError(
            f"kata_board: TYPE {type} REQUIRES a payload pointer (DESIGN §2.2)"
        )
    if payload is not None:
        payload = _guard_pointer(payload, what="payload")
        msg = f"{msg}{PAYLOAD_TOKEN}{payload}"

    seq_field = f"{seq}~{parent_seq}" if parent_seq is not None else f"{seq}"
    return FS.join([utc, seq_field, agent, type, task, msg]) + "\n"


# ---------------------------------------------------------------------------
# Parsing — a failure is a REFUSAL, never a skip
# ---------------------------------------------------------------------------


def _parse_utc(value: str) -> datetime:
    """Validate the utc field.  Recorded for humans; NEVER load-bearing for order."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CursorParseError(
            f"kata_board: utc field is not ISO-8601: {value!r}"
        ) from exc


def parse_line(raw: str, *, pos: int = 0) -> CursorLine:
    """Parse one cursor line into a :class:`CursorLine`.

    A legacy 5-field board line raises :class:`CursorParseError` naming the
    migration — the old grammar parses NOWHERE (DESIGN §2.2).
    """
    line = raw.strip()
    if not line:
        raise CursorParseError("kata_board: blank line is not a cursor line")

    parts = line.split(FS, 5)
    if len(parts) != 6:
        raise CursorParseError(
            f"kata_board: expected 6 ' | '-separated fields, got {len(parts)}: {line!r}"
            + (
                "  — this is the LEGACY 5-field board grammar, which parses nowhere "
                "after the cursor migration (DESIGN §2.2); re-emit it through "
                "kata_board.append_event."
                if len(parts) == 5
                else ""
            )
        )

    utc, seq_field, agent, type_, task, msg = parts
    _parse_utc(utc)

    m = _SEQ_FIELD_RE.match(seq_field)
    if not m:
        raise CursorParseError(
            f"kata_board: bad seq field {seq_field!r} (expected 'seq' or "
            f"'seq~parent-seq', digits only) in: {line!r}"
            + (
                "  — a 5-field legacy line whose msg contained ' | ' presents as 6 "
                "fields; it is refused here, never mis-parsed."
                if not seq_field.replace("~", "").isdigit()
                else ""
            )
        )
    seq = int(m.group(1))
    parent_seq = int(m.group(2)) if m.group(2) is not None else None

    if type_ not in CURSOR_TYPES:
        raise CursorParseError(
            f"kata_board: unknown TYPE {type_!r} in: {line!r}; "
            f"legal: {sorted(CURSOR_TYPES)}"
        )
    if not agent.strip() or not task.strip():
        raise CursorParseError(f"kata_board: empty agent-id/task-id in: {line!r}")

    payload: str | None = None
    if PAYLOAD_TOKEN in msg:
        msg, _, payload = msg.rpartition(PAYLOAD_TOKEN)
        try:  # on the READ path every refusal is a CursorParseError, so a fail-soft
            payload = _guard_pointer(payload.strip(), what="payload")
        except CursorGrammarError as exc:  # consumer catches exactly one class
            raise CursorParseError(f"{exc} in: {line!r}") from exc
    msg = msg.strip()
    if not msg:
        raise CursorParseError(f"kata_board: empty msg in: {line!r}")
    if payload is None and type_ in PAYLOAD_REQUIRED_TYPES:
        raise CursorParseError(
            f"kata_board: TYPE {type_} REQUIRES a payload pointer, none found in: {line!r}"
        )

    return CursorLine(
        utc=utc.strip(),
        seq=seq,
        agent=agent.strip(),
        type=type_,
        task=task.strip(),
        msg=msg,
        parent_seq=parent_seq,
        payload=payload,
        pos=pos,
    )


def parse_header(text: str) -> tuple[RunHeader, int]:
    """Parse the run-header block.

    Returns ``(header, consumed)`` where *consumed* is the number of raw text lines
    the header occupied (leading blank lines included).  Pointer keys may appear in
    any order; each may appear at most once.
    """
    raw_lines = text.splitlines()
    i = 0
    while i < len(raw_lines) and not raw_lines[i].strip():
        i += 1
    if i >= len(raw_lines):
        raise CursorParseError(
            "kata_board: cursor has no run-header block; a cursor is "
            "'run-header line*' (DESIGN §2.2) — call start_run() first"
        )
    first = raw_lines[i].strip()
    if not first.startswith(_RUN_PREFIX):
        raise CursorParseError(
            f"kata_board: cursor must open with 'RUN <run-id>', got: {first!r}"
        )
    try:  # read path: one refusal class (see parse_line)
        run_id = validate_run_id(first[len(_RUN_PREFIX) :].strip())
    except CursorGrammarError as exc:
        raise CursorParseError(str(exc)) from exc
    i += 1

    pointers: dict[str, str] = {}
    while i < len(raw_lines):
        candidate = raw_lines[i].strip()
        key = next((k for k in _HEADER_KEYS if candidate.startswith(f"{k}: ")), None)
        if key is None:
            break
        if key in pointers:
            raise CursorParseError(
                f"kata_board: duplicate run-header key {key!r}"
            )
        value = candidate[len(key) + 2 :].strip()
        try:  # read path: one refusal class (see parse_line)
            pointers[key] = (
                _guard_pointer(value, what="prev-segment")
                if key == "prev-segment"
                else validate_run_id(value)
            )
        except CursorGrammarError as exc:
            raise CursorParseError(f"{exc} (run-header key {key!r})") from exc
        i += 1

    return (
        RunHeader(
            run_id=run_id,
            prev_run=pointers.get("prev-run"),
            parent_run=pointers.get("parent-run"),
            prev_segment=pointers.get("prev-segment"),
        ),
        i,
    )


def parse_cursor(text: str) -> Cursor:
    """Parse a whole cursor.  Any unparseable line is a REFUSAL, never a skip."""
    header, consumed = parse_header(text)
    lines: list[CursorLine] = []
    for raw in text.splitlines()[consumed:]:
        if not raw.strip():
            continue
        lines.append(parse_line(raw, pos=len(lines)))
    return Cursor(header=header, lines=tuple(lines))


def next_seq(cursor: Cursor | str) -> int:
    """Return ``(observed max) + 1`` — the seq the next appending writer stamps.

    Concurrent worker appends may race; **duplicate worker seqs are legal** and are
    ordered by file position (DESIGN §2.2).  Seam-authored lines come from the single
    seam writer and are therefore unique, which is why lineage references always
    target seam-authored seqs.
    """
    if isinstance(cursor, str):
        cursor = parse_cursor(cursor)
    return max((ln.seq for ln in cursor.lines), default=0) + 1


# ---------------------------------------------------------------------------
# Ordering of record + the pure folds
# ---------------------------------------------------------------------------


def order_key(run_id: str, line: CursorLine) -> tuple[str, int, int]:
    """The ordering key of record: ``(runId, seq, file-position)``.

    **Wall-clock is never load-bearing** — it is recorded for humans only.  The
    file-position tail is the explicit total-order tie-break duplicate worker seqs
    require (Determinism Doctrine law 10).
    """
    return (run_id, line.seq, line.pos)


def run_fold_order(cursors: Sequence[Cursor]) -> tuple[str, ...]:
    """Return run ids in **parent fold-order**: parents before their children.

    Roots (and runs whose ``parent-run:`` names a cursor not supplied) sort by run
    id — which is chronological, because a run id leads with its utc-compact stamp.
    A ``parent-run:`` cycle is a fail-loud refusal, never a silent drop.  Pure.
    """
    by_id: dict[str, Cursor] = {}
    for c in cursors:
        if c.run_id in by_id:
            raise CursorParseError(f"kata_board: duplicate cursor for run {c.run_id}")
        by_id[c.run_id] = c

    children: dict[str, list[str]] = {rid: [] for rid in by_id}
    roots: list[str] = []
    for rid, c in by_id.items():
        parent = c.header.parent_run
        if parent and parent in by_id and parent != rid:
            children[parent].append(rid)
        else:
            roots.append(rid)

    ordered: list[str] = []

    def walk(rid: str, stack: frozenset[str]) -> None:
        if rid in stack:
            raise CursorParseError(
                f"kata_board: parent-run cycle through {rid!r}"
            )
        ordered.append(rid)
        for child in sorted(children[rid]):
            walk(child, stack | {rid})

    for root in sorted(roots):
        walk(root, frozenset())

    if len(ordered) != len(by_id):
        missing = sorted(set(by_id) - set(ordered))
        raise CursorParseError(
            f"kata_board: parent-run cycle leaves runs unreachable: {missing}"
        )
    return tuple(ordered)


def fold_order(cursors: Sequence[Cursor]) -> tuple[tuple[str, CursorLine], ...]:
    """Every line across every supplied cursor in order of record.

    ``(runId, seq) + parent fold-order``: runs walk the ``parent-run:`` tree
    (parents first), lines within a run sort by ``(seq, file-position)``.  Pure.
    """
    by_id = {c.run_id: c for c in cursors}
    out: list[tuple[str, CursorLine]] = []
    for rid in run_fold_order(cursors):
        for line in sorted(by_id[rid].lines, key=lambda ln: (ln.seq, ln.pos)):
            out.append((rid, line))
    return tuple(out)


def fold_concurrency(cursors: Sequence[Cursor]) -> dict:
    """Fold cursors into the concurrency-evidence model.  **PURE** — no I/O, no clock.

    Cross-cursor ``(runId, seq)`` fold: per run, a task's in-flight span runs from its
    EARLIEST ``CLAIM`` seq to its LATEST ``DONE`` seq (a re-dispatched task keeps its
    full span — a naive last-write CLAIM would erase a real overlap and undercount
    concurrency).  The sweep is over **seq space**, not wall-clock, so the historic
    clock-trust caveat no longer applies: cross-host skew cannot change the answer.
    At an equal seq an END is processed before a START, so a hand-off is never
    inflated into an overlap.

    ``fold is pure; side effects only after fold completes`` (DESIGN §2.8) — the
    writing sibling is :func:`emit_concurrency`.
    """
    cursors = list(cursors)
    by_id = {c.run_id: c for c in cursors}
    runs = run_fold_order(cursors)

    workers: dict[str, dict] = {}
    overlaps: list[dict] = []
    max_in_flight = 0

    for rid in runs:
        starts: dict[str, int] = {}
        ends: dict[str, int] = {}
        owner: dict[str, str] = {}
        utc_start: dict[str, str] = {}
        utc_end: dict[str, str] = {}

        for line in sorted(by_id[rid].lines, key=lambda ln: (ln.seq, ln.pos)):
            if line.type == "CLAIM":
                if line.task not in starts or line.seq < starts[line.task]:
                    starts[line.task] = line.seq
                    utc_start[line.task] = line.utc
                owner.setdefault(line.task, line.agent)
            elif line.type == "DONE":
                if line.task not in ends or line.seq > ends[line.task]:
                    ends[line.task] = line.seq
                    utc_end[line.task] = line.utc

        spans: list[tuple[int, int, str]] = []
        for task in sorted(starts):
            if task not in ends:
                continue  # still in-flight / unterminated — not countable evidence
            start, end = starts[task], ends[task]
            if end < start:
                raise CursorParseError(
                    f"kata_board: task {task!r} on run {rid} DONEs at seq {end} before "
                    f"its earliest CLAIM at seq {start} — the cursor is out of order; "
                    "a corrupt span is a refusal, never a silent skip"
                )
            workers[f"{rid}#{task}"] = {
                "agent": owner[task],
                "endSeq": end,
                "runId": rid,
                "spanSeqs": end - start,
                "startSeq": start,
                "task": task,
                "utcEnd": utc_end[task],
                "utcStart": utc_start[task],
            }
            spans.append((start, end, task))

        # Sweep the seq endpoints for max concurrent in-flight + overlap windows (>=2).
        # Priority 0 = END, 1 = START, so at an equal seq an end is processed first and a
        # hand-off never inflates into an overlap.  Task id is the total-order tie-break.
        events = sorted(
            [(s, 1, t, +1) for s, _e, t in spans] + [(e, 0, t, -1) for _s, e, t in spans]
        )
        active = 0
        win_start: int | None = None
        for seq, _priority, _task, delta in events:
            prev = active
            active += delta
            if prev < 2 <= active:
                win_start = seq
            if prev >= 2 > active and win_start is not None:
                overlaps.append({"fromSeq": win_start, "runId": rid, "toSeq": seq})
                win_start = None
            max_in_flight = max(max_in_flight, active)

    return {
        "genuinelyParallel": max_in_flight >= 2,
        "maxInFlight": max_in_flight,
        "ordering": "(runId, seq, file-position) + parent fold-order; wall-clock never load-bearing",
        "overlaps": overlaps,
        "runs": list(runs),
        "source": (
            "cursor CLAIM/DONE seq spans (cross-cursor (runId, seq) fold); "
            "utc fields are informational only"
        ),
        "workerCount": len(workers),
        "workers": workers,
    }


# ---------------------------------------------------------------------------
# Cursor file I/O
# ---------------------------------------------------------------------------


def cursor_path(kata_dir: str | Path) -> Path:
    """Absolute path of the run's cursor file inside *kata_dir*."""
    return _safe_path(kata_dir) / CURSOR_FILENAME


def read_cursor(kata_dir: str | Path) -> Cursor:
    """Read and parse ``<kata_dir>/board.md``.  Raises if absent or malformed."""
    path = cursor_path(kata_dir)
    if not path.exists():
        raise CursorGrammarError(
            f"kata_board: no cursor at {path} — call start_run() first "
            "(the seam mints the runId at run start)"
        )
    return parse_cursor(path.read_text(encoding="utf-8"))


def start_run(
    kata_dir: str | Path,
    *,
    run_id: str | None = None,
    prev_run: str | None = None,
    parent_run: str | None = None,
    prev_segment: str | None = None,
    now: datetime | None = None,
    entropy: str | None = None,
) -> RunHeader:
    """Rotate any pre-existing cursor, then write this run's header block.

    The run-isolation duty (see ``protocol/board.md``): a pre-existing cursor is
    moved to ``board.<utc-compact>.archive.md`` before the header is written, so the
    live cursor carries only the current run's events and prior-run CLAIM/DONE pairs
    cannot contaminate the fold.

    New-run vs resume discrimination, orphan reaping, and the run-marker write belong
    to the seam's ``run_start()`` (DESIGN §1.3/§2.4, PLAN wave 3); this is the
    grammar primitive that seam act calls.
    """
    kata = _safe_path(kata_dir)
    kata.mkdir(parents=True, exist_ok=True)
    path = kata / CURSOR_FILENAME

    if path.exists() and path.read_text(encoding="utf-8").strip():
        stamp = (now or datetime.now(UTC)).astimezone(UTC).strftime(_UTC_COMPACT)
        archive = kata / f"{Path(CURSOR_FILENAME).stem}.{stamp}.archive.md"
        n = 1
        while archive.exists():  # never clobber an archive; deterministic suffix
            archive = kata / f"{Path(CURSOR_FILENAME).stem}.{stamp}.{n}.archive.md"
            n += 1
        os.replace(path, archive)

    header = RunHeader(
        run_id=validate_run_id(run_id) if run_id else mint_run_id(now=now, entropy=entropy),
        prev_run=prev_run,
        parent_run=parent_run,
        prev_segment=prev_segment,
    )
    path.write_text(format_header(header), encoding="utf-8")
    return header


# ---------------------------------------------------------------------------
# Payloads (worker + seam)
# ---------------------------------------------------------------------------


def payload_pointer(run_id: str, seq: int) -> str:
    """The kata-dir-relative pointer written into a line: ``payloads/<runId>-<seq>.json``.

    The file therefore lives at ``.kata/payloads/<runId>-<seq>.json`` (DESIGN §2.2).
    The pointer is stored kata-dir-relative so it resolves from the cursor's own
    location — surviving archive rotation and worktree moves.
    """
    validate_run_id(run_id)
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
        raise CursorGrammarError(f"kata_board: seq must be a non-negative int: {seq!r}")
    return f"{PAYLOAD_DIRNAME}/{run_id}-{seq}.json"


def payload_path(kata_dir: str | Path, pointer: str) -> Path:
    """Resolve a guarded payload pointer against *kata_dir*."""
    return _safe_path(kata_dir) / _guard_pointer(pointer, what="payload")


def validate_verdict_payload(payload: dict) -> dict:
    """Validate a VERDICT payload against ``{verdict, evidencePointers[], judgeDispatchSeq, runId}``."""
    if not isinstance(payload, dict):
        raise CursorGrammarError("kata_board: VERDICT payload must be an object")
    missing = [f for f in VERDICT_PAYLOAD_FIELDS if f not in payload]
    if missing:
        raise CursorGrammarError(
            f"kata_board: VERDICT payload missing required field(s): {missing}"
        )
    if not isinstance(payload["verdict"], str) or not payload["verdict"].strip():
        raise CursorGrammarError("kata_board: VERDICT payload 'verdict' must be a non-empty string")
    pointers = payload["evidencePointers"]
    if not isinstance(pointers, list) or not all(isinstance(p, str) for p in pointers):
        raise CursorGrammarError(
            "kata_board: VERDICT payload 'evidencePointers' must be a list of strings"
        )
    judge_seq = payload["judgeDispatchSeq"]
    if not isinstance(judge_seq, int) or isinstance(judge_seq, bool) or judge_seq < 0:
        raise CursorGrammarError(
            "kata_board: VERDICT payload 'judgeDispatchSeq' must be a non-negative int"
        )
    validate_run_id(payload["runId"])
    return payload


def write_payload(kata_dir: str | Path, pointer: str, payload: dict) -> Path:
    """Atomically write a pointed-to JSON payload.  ``sort_keys=True`` (doctrine law 5)."""
    target = payload_path(kata_dir, pointer)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return target


# ---------------------------------------------------------------------------
# Appenders (worker-safe; the seam uses the same primitive for its own TYPEs)
# ---------------------------------------------------------------------------


def append_event(
    kata_dir: str | Path,
    agent: str,
    type: str,  # noqa: A002  (shadowing built-in intentional — matches protocol)
    task: str,
    msg: str,
    *,
    parent_seq: int | None = None,
    payload: str | None = None,
    seq: int | None = None,
    now: datetime | None = None,
) -> CursorLine:
    """Append one cursor line to ``<kata_dir>/board.md``.

    Strictly append-only: existing lines are never modified or deleted (audit-trail
    invariant).  The cursor must already carry a run-header block — this function
    never mints identity, because ``runId`` is minted by ONE seam act at run start
    (DESIGN §2.4); an implicit second minting path is the silent-permissive class.

    Line format (``protocol/board.md``)::

        <utc> | <seq>[~<parent-seq>] | <agent> | <TYPE> | <task> | <msg>[ payload=<path>]

    Single-writer rule: WORKERS call this function (and append_progress).
    ONLY the orchestrator calls write_state/update_task.  PHASE/VERDICT/SPAWN/DOWN/DENY
    are seam-authored — a worker never appends them (DESIGN §2.3).

    Parameters
    ----------
    kata_dir:
        Root directory of the running kata (.kata/).  Must not contain '..'.
    agent:
        Agent identifier string (e.g. ``"S1a-worker"``).
    type:
        Cursor TYPE token (must be in ``CURSOR_TYPES``).
    task:
        Task identifier (e.g. ``"T1"``).
    msg:
        One-line message.  No newline, and no bare ``" payload="`` token.
    parent_seq:
        Dispatch-lineage stamp — the seq of the SPAWN line this line descends from.
    payload:
        Kata-dir-relative pointer to a JSON payload.  REQUIRED for ``VERDICT``.
    seq:
        Override the stamped seq.  Default ``(observed max) + 1``.
    now:
        Injectable clock for the recorded (non-load-bearing) utc stamp.

    Returns
    -------
    CursorLine
        The line as appended — its ``seq`` is what the writer stamped.
    """
    kata = _safe_path(kata_dir)
    cursor = read_cursor(kata)
    stamped = next_seq(cursor) if seq is None else seq
    utc_now = (now or datetime.now(UTC)).astimezone(UTC).isoformat()

    rendered = format_line(
        utc=utc_now,
        seq=stamped,
        agent=agent,
        type=type,
        task=task,
        msg=msg,
        parent_seq=parent_seq,
        payload=payload,
    )
    with (kata / CURSOR_FILENAME).open("a", encoding="utf-8") as fh:
        fh.write(rendered)
    return parse_line(rendered, pos=len(cursor.lines))


def append_progress(
    kata_dir: str | Path,
    agent: str,
    task: str,
    step: int,
    n: int,
    label: str,
    *,
    parent_seq: int | None = None,
    now: datetime | None = None,
) -> CursorLine:
    """Append a PROGRESS heartbeat line to ``<kata_dir>/board.md``.

    Convenience wrapper around append_event with type=``"PROGRESS"`` and
    msg formatted as ``"<step>/<n> <label>"`` (e.g. ``"3/5 writing tests"``).

    PROGRESS lines are the MANDATED worker liveness heartbeat (Milestone-1 F3;
    see protocol/board.md) — read by the dashboard and the orchestrator's
    liveness monitor, excluded from coordination and concurrency evidence.
    They are IGNORED by coordination logic (DECISION/BLOCK/ESCALATE invariants
    are unchanged).

    Single-writer rule: WORKERS call this function (and append_event).
    ONLY the orchestrator calls write_state/update_task.
    """
    return append_event(
        kata_dir,
        agent,
        "PROGRESS",
        task,
        f"{step}/{n} {label}",
        parent_seq=parent_seq,
        now=now,
    )


def append_verdict(
    kata_dir: str | Path,
    agent: str,
    task: str,
    msg: str,
    payload: dict,
    *,
    parent_seq: int | None = None,
    now: datetime | None = None,
) -> CursorLine:
    """Append a seam-authored VERDICT line together with its REQUIRED JSON payload.

    Writes the payload FIRST (so the pointer is never dangling), then the line.
    Seam-authored: this is ``capture()``'s cursor act (DESIGN §1.3/§2.3), never a
    worker's.
    """
    kata = _safe_path(kata_dir)
    cursor = read_cursor(kata)
    stamped = next_seq(cursor)
    validate_verdict_payload(payload)
    pointer = payload_pointer(cursor.run_id, stamped)
    write_payload(kata, pointer, payload)
    return append_event(
        kata,
        agent,
        "VERDICT",
        task,
        msg,
        parent_seq=parent_seq,
        payload=pointer,
        seq=stamped,
        now=now,
    )


def emit_concurrency(
    kata_dir: str | Path,
    *,
    extra_cursor_paths: Iterable[str | Path] = (),
) -> dict:
    """Fold the run's cursor(s) and write ``<kata_dir>/concurrency.json``.

    The canonical emitter behind ``protocol/board.md``'s concurrency-evidence
    section.  Reads, then folds PURELY, then — and only then — writes: if the fold
    refuses, no artifact is produced.
    """
    kata = _safe_path(kata_dir)
    cursors = [read_cursor(kata)]
    for extra in sorted(str(p) for p in extra_cursor_paths):
        cursors.append(parse_cursor(_safe_path(extra).read_text(encoding="utf-8")))

    model = fold_concurrency(cursors)  # pure; raises before any side effect

    (kata / "concurrency.json").write_text(
        json.dumps(model, indent=2, sort_keys=True), encoding="utf-8"
    )
    return model


# ---------------------------------------------------------------------------
# State helpers (orchestrator-only)
# ---------------------------------------------------------------------------


def write_state(kata_dir: str | Path, state: dict) -> None:
    """Atomically write state.json to <kata_dir>/state.json.

    Uses write-to-temp + os.replace so a concurrent reader never observes a
    half-written file (POSIX atomic rename; also atomic on Windows via
    os.replace which maps to MoveFileExW with MOVEFILE_REPLACE_EXISTING).

    Single-writer rule: ONLY the orchestrator calls this function.
    WORKERS must NEVER call write_state or update_task — they append to the cursor.

    Parameters
    ----------
    kata_dir:
        Root directory of the running kata (.kata/).  Must not contain '..'.
    state:
        Full state dict to persist.  Must be JSON-serialisable.
    """
    kata_dir = _safe_path(kata_dir)
    kata_dir.mkdir(parents=True, exist_ok=True)  # first write of a run creates .kata/
    state_path = kata_dir / "state.json"

    # Write to a sibling temp file, then atomically replace.
    fd, tmp_path = tempfile.mkstemp(dir=kata_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
        os.replace(tmp_path, state_path)
    except Exception:
        # Clean up the temp file on failure so we never leave orphans.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def update_task(
    kata_dir: str | Path,
    state: dict,
    task: str,
    status: str,
) -> dict:
    """Set state["tasks"][task] = status, refresh updatedUtc, and write_state.

    Mutates *state* in place, writes atomically, and returns the mutated dict.

    Single-writer rule: ONLY the orchestrator calls this function.
    WORKERS must NEVER call write_state or update_task — they append to the cursor.

    Parameters
    ----------
    kata_dir:
        Root directory of the running kata (.kata/).  Must not contain '..'.
    state:
        Current state dict (will be mutated in place).
    task:
        Task identifier key within ``state["tasks"]``.
    status:
        New status string (e.g. ``"in-progress"``, ``"done"``, ``"gated"``).

    Returns
    -------
    dict
        The mutated state dict (same object as the *state* parameter).
    """
    state.setdefault("tasks", {})[task] = status
    state["updatedUtc"] = datetime.now(UTC).isoformat()
    write_state(kata_dir, state)
    return state
