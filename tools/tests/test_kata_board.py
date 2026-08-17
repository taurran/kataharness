"""Tests for kata_board.py — the CURSOR engine (emitter + parser + pure fold).

TDD discipline: all tests use tmp_path; pure stdlib; no real kata run required.

Coverage
--------
- run-id grammar: mint/validate, randomness mints identity only
- run-header block: RUN + prev-run / parent-run / prev-segment (RESERVED) round-trip
- every line TYPE (worker / orchestrator / seam) round-trips write -> parse
- ``seq~parent-seq`` dispatch-lineage stamps parse
- seq assignment is (observed max)+1; duplicate worker seqs are LEGAL and ordered
  by file position
- ordering of record = (runId, seq, pos) + parent fold-order; wall-clock never
  load-bearing
- payload pointers: written under .kata/payloads/<runId>-<seq>.json, REQUIRED for
  VERDICT, schema-checked, traversal-guarded (CWE-23)
- the LEGACY 5-field grammar is a parse REFUSAL, never a silent skip
- the fold is PURE: no side effect, deterministic, and emit writes only after it
  completes
- write_state / update_task (orchestrator-only) unchanged
- _safe_path rejects a kata_dir containing ".."
"""

from __future__ import annotations

import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import under test
# ---------------------------------------------------------------------------
import kata_board

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AGENT = "S1a-worker"
TASK = "T1"
RUN_A = "run-20260816T101500Z-a1b2c3d4"
RUN_B = "run-20260816T111500Z-beef0001"
RUN_C = "run-20260816T121500Z-c0ffee02"
FIXED_NOW = datetime(2026, 8, 16, 10, 15, 0, tzinfo=UTC)


def _cursor_lines(kata_dir: Path) -> list[str]:
    """Return non-empty, non-header lines from the cursor file."""
    text = (kata_dir / kata_board.CURSOR_FILENAME).read_text(encoding="utf-8")
    _header, consumed = kata_board.parse_header(text)
    return [ln for ln in text.splitlines()[consumed:] if ln.strip()]


def _fresh(tmp_path: Path, name: str = "kata", **kw) -> Path:
    """Create a kata dir with a started run and return it."""
    kata_dir = tmp_path / name
    kata_dir.mkdir(parents=True, exist_ok=True)
    kw.setdefault("run_id", RUN_A)
    kata_board.start_run(kata_dir, **kw)
    return kata_dir


# ---------------------------------------------------------------------------
# _safe_path
# ---------------------------------------------------------------------------


def test_safe_path_rejects_dotdot_traversal(tmp_path):
    """A kata_dir containing '..' must raise ValueError."""
    with pytest.raises(ValueError):
        kata_board._safe_path(str(tmp_path / ".." / "escape"))


def test_safe_path_accepts_normal_path(tmp_path):
    """A normal nested path (no '..') must resolve without error."""
    result = kata_board._safe_path(str(tmp_path / "sub" / "dir"))
    assert isinstance(result, Path)
    assert ".." not in result.parts


# ---------------------------------------------------------------------------
# Run identity — run-id ::= "run-" utc-compact "-" hex+
# ---------------------------------------------------------------------------


def test_mint_run_id_matches_grammar():
    """A minted id must satisfy run-<utc-compact>-<hex>."""
    run_id = kata_board.mint_run_id(now=FIXED_NOW, entropy="deadbeef")
    assert run_id == "run-20260816T101500Z-deadbeef"
    assert kata_board.RUN_ID_RE.match(run_id)


def test_mint_run_id_is_sortable_by_time():
    """Ids sort chronologically because the compact utc stamp leads."""
    early = kata_board.mint_run_id(now=datetime(2026, 1, 1, tzinfo=UTC), entropy="ffff")
    late = kata_board.mint_run_id(now=datetime(2026, 6, 1, tzinfo=UTC), entropy="0000")
    assert early < late


def test_mint_run_id_randomness_mints_identity_only():
    """Two mints at the same instant differ only in the entropy suffix (doctrine law 9)."""
    a = kata_board.mint_run_id(now=FIXED_NOW)
    b = kata_board.mint_run_id(now=FIXED_NOW)
    assert a != b
    assert a.rsplit("-", 1)[0] == b.rsplit("-", 1)[0]


@pytest.mark.parametrize(
    "bad",
    ["run-2026-08-16-abcd", "run-20260816T101500Z-XYZ", "20260816T101500Z-abcd", "", "runid"],
)
def test_validate_run_id_refuses_malformed(bad):
    """A malformed run id is refused, never coerced."""
    with pytest.raises(kata_board.CursorGrammarError):
        kata_board.validate_run_id(bad)


# ---------------------------------------------------------------------------
# The run-header block
# ---------------------------------------------------------------------------


def test_start_run_writes_run_header(tmp_path):
    """start_run must write 'RUN <run-id>' as the first line."""
    kata_dir = _fresh(tmp_path)
    text = (kata_dir / kata_board.CURSOR_FILENAME).read_text(encoding="utf-8")
    assert text.splitlines()[0] == f"RUN {RUN_A}"


def test_header_round_trips_all_pointers(tmp_path):
    """prev-run / parent-run / prev-segment must round-trip write -> parse."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()
    kata_board.start_run(
        kata_dir,
        run_id=RUN_B,
        prev_run=RUN_A,
        parent_run=RUN_A,
        prev_segment="segments/board.20260816T090000Z.archive.md",
    )
    header = kata_board.read_cursor(kata_dir).header
    assert header.run_id == RUN_B
    assert header.prev_run == RUN_A
    assert header.parent_run == RUN_A
    assert header.prev_segment == "segments/board.20260816T090000Z.archive.md"


def test_prev_segment_is_reserved_only(tmp_path):
    """prev-segment is parsed and round-tripped; NO segmenting machinery exists."""
    kata_dir = _fresh(tmp_path, run_id=RUN_B, prev_segment="segments/prior.md")
    header = kata_board.read_cursor(kata_dir).header
    assert header.prev_segment == "segments/prior.md"
    assert not hasattr(kata_board, "segment_cursor"), (
        "prev-segment is RESERVED this wave — no segmenting machinery may exist"
    )


def test_header_refuses_duplicate_pointer_key():
    """A duplicated header key is a refusal."""
    text = f"RUN {RUN_A}\nprev-run: {RUN_B}\nprev-run: {RUN_B}\n"
    with pytest.raises(kata_board.CursorParseError):
        kata_board.parse_header(text)


def test_header_keys_must_be_in_bnf_order():
    """The reader is as strict as the writer: one header, one serialization."""
    permuted = f"RUN {RUN_A}\nparent-run: {RUN_B}\nprev-run: {RUN_B}\n"
    with pytest.raises(kata_board.CursorParseError) as exc:
        kata_board.parse_header(permuted)
    assert "out of BNF order" in str(exc.value)

    canonical = f"RUN {RUN_A}\nprev-run: {RUN_B}\nparent-run: {RUN_B}\n"
    header, _consumed = kata_board.parse_header(canonical)
    assert kata_board.format_header(header) == canonical


def test_emitted_header_key_order_matches_the_bnf():
    """Every emitted header is already in the order the reader demands."""
    header = kata_board.RunHeader(
        run_id=RUN_A,
        prev_run=RUN_B,
        parent_run=RUN_B,
        prev_segment="segments/prior.md",
    )
    keys = [ln.split(":")[0] for ln in kata_board.format_header(header).splitlines()[1:]]
    assert keys == list(kata_board._HEADER_KEYS)


def test_cursor_without_header_is_refused():
    """A cursor is 'run-header line*' — a headerless body is a refusal."""
    with pytest.raises(kata_board.CursorParseError):
        kata_board.parse_cursor(
            "2026-08-16T10:15:00+00:00 | 1 | a | NOTE | T1 | hi\n"
        )


def test_append_without_started_run_is_refused(tmp_path):
    """append_event never mints identity — the seam mints runId at run start."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()
    with pytest.raises(kata_board.CursorGrammarError):
        kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "no header yet")


def test_start_run_rotates_a_pre_existing_cursor(tmp_path):
    """Run isolation: a pre-existing cursor is archived, never folded into this run."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "CLAIM", TASK, "old run")
    kata_board.start_run(kata_dir, run_id=RUN_B, now=FIXED_NOW)

    archives = sorted(kata_dir.glob("board.*.archive.md"))
    assert len(archives) == 1, f"expected one archive, got {archives}"
    assert RUN_A in archives[0].read_text(encoding="utf-8")
    assert kata_board.read_cursor(kata_dir).run_id == RUN_B
    assert _cursor_lines(kata_dir) == [], "the new run's cursor must start empty"


# ---------------------------------------------------------------------------
# Rotation concurrency — the archive name is ELECTED, never scanned-then-taken
# ---------------------------------------------------------------------------


def test_rotations_at_an_identical_stamp_get_distinct_archives(tmp_path):
    """Same utc stamp, two rotations: distinct archive names, both contents kept.

    The collision suffix is what the naming contract promises; this pins that it still
    holds when the stamp cannot disambiguate.
    """
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "content-of-run-zero")
    kata_board.start_run(kata_dir, run_id=RUN_B, now=FIXED_NOW)
    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "content-of-run-one")
    kata_board.start_run(kata_dir, run_id=RUN_C, now=FIXED_NOW)

    archives = sorted(kata_dir.glob("board.*.archive.md"))
    assert len(archives) == 2, f"expected two distinct archives, got {archives}"
    blob = "\n".join(a.read_text(encoding="utf-8") for a in archives)
    assert "content-of-run-zero" in blob
    assert "content-of-run-one" in blob


def test_reserved_archive_name_is_exclusive(tmp_path):
    """The reservation is an atomic exclusive create: the second call cannot get it."""
    kata_dir = _fresh(tmp_path)
    token = kata_board.archive_token(RUN_B)
    first = kata_board._reserve_archive_path(kata_dir, "20260816T101500Z", token)
    second = kata_board._reserve_archive_path(kata_dir, "20260816T101500Z", token)

    assert first != second, "a reserved name must never be handed out twice"
    assert first.exists() and second.exists()
    assert first.name == "board.20260816T101500Z.beef0001.archive.md"
    assert second.name == "board.20260816T101500Z.beef0001.1.archive.md"


def test_an_archive_name_is_unreachable_by_any_other_run(tmp_path):
    """THE NAME-COLLISION PIN for CI run 32006013216 (windows-latest, round 7).

    Exclusive create makes a name un-shareable only while the file EXISTS — and
    ``os.replace`` onto a reservation momentarily frees it. Measured raw-OS on this
    host: a concurrent ``O_CREAT|O_EXCL`` stole the destination of a live ``os.replace``
    1 time in 20 000. Two racers then own ONE archive path, and each one's own cleanup
    wrecks the other: one unlinks it, leaving the other reading ENOENT off the archive
    it had just filled; one re-creates it as a placeholder, leaving the other reading 0
    bytes where it had moved 121. Both refusals appear verbatim in the CI log.

    This models that window exactly — free the name mid-flight, then let a DIFFERENT run
    reserve — and pins the cure at the level where it is structural rather than narrow:
    a run's archive names are unreachable by any other run, so the window has nothing
    left to lose. Pre-fix the two runs land on the identical path.
    """
    kata_dir = _fresh(tmp_path)
    stamp = "20260816T101500Z"
    mine = kata_board._reserve_archive_path(kata_dir, stamp, kata_board.archive_token(RUN_B))

    # The measured window: os.replace has momentarily freed the destination name.
    mine.unlink()
    theirs = kata_board._reserve_archive_path(kata_dir, stamp, kata_board.archive_token(RUN_C))

    assert theirs != mine, (
        "another run reserved this run's archive path — the exact double ownership "
        f"that produced round 7's ENOENT and 0-byte refusals ({mine.name})"
    )
    assert kata_board.archive_token(RUN_B) in mine.name
    assert kata_board.archive_token(RUN_C) in theirs.name


def test_a_blank_cursor_read_never_deletes_a_live_cursor(tmp_path, monkeypatch):
    """THE ELECTION PIN: the blank-cursor branch must not destroy somebody's cursor.

    ``start_run``'s blank branch used to unlink whatever sat at ``board.md`` on the
    reasoning that "no data is involved". There is a real window in which that is false
    — between a winner's archive-move and its publish, a racer reads the cursor as
    ABSENT — and by the time the racer reaches the branch the winner has published a
    COMPLETE cursor, which the racer then deletes and replaces with its own header.
    Pre-fix that is measurable and deterministic: the winner's cursor does not survive
    and the round ends with TWO runs each believing they own the cursor — the D-25
    election violation, reappearing at the one path the exclusive claim does not guard.

    Forced here with no thread timing: the racer is handed ``b""`` while the winner
    completes an entire ``start_run`` underneath it.
    """
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "winner-content")
    real_read = kata_board._read_cursor_bytes

    def read_as_absent(path):
        real_read(path)
        monkeypatch.setattr(kata_board, "_read_cursor_bytes", real_read)
        kata_board.start_run(kata_dir, run_id=RUN_C, now=FIXED_NOW)  # the winner
        return b""  # ...but this racer is still holding the pre-winner observation

    monkeypatch.setattr(kata_board, "_read_cursor_bytes", read_as_absent)

    with pytest.raises(kata_board.CursorGrammarError) as exc:
        kata_board.start_run(kata_dir, run_id=RUN_B, now=FIXED_NOW)
    assert "nothing was discarded" in str(exc.value)

    assert kata_board.read_cursor(kata_dir).run_id == RUN_C, (
        "the winner's live cursor must survive a racer's blank-cursor read"
    )


def test_a_genuinely_blank_cursor_is_still_cleared(tmp_path):
    """The blank branch still does its job: a crash-left empty cursor cannot wedge runs.

    The guard above must not be bought by leaving stale empty files behind — an empty
    ``board.md`` holds the NAME the exclusive claim needs.
    """
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()
    (kata_dir / kata_board.CURSOR_FILENAME).write_bytes(b"   \n")

    header = kata_board.start_run(kata_dir, run_id=RUN_B, now=FIXED_NOW)

    assert header.run_id == RUN_B
    assert kata_board.read_cursor(kata_dir).run_id == RUN_B
    assert not list(kata_dir.glob("board.*.archive.md")), (
        "a blank cursor holds no history worth archiving"
    )


def test_forced_interleaving_rotation_refuses_and_loses_nothing(tmp_path, monkeypatch):
    """DETERMINISTIC pin (no thread timing): drive a competing rotation at the exact
    race point via the test seam, and prove the loser refuses loudly while leaving the
    directory exactly as it found it — the winner's cursor still live, the original
    content archived once.

    **This is the falsifying pin for the reported defect.** Replaying this exact
    interleaving against the pre-fix name selection (scan for a free name, then
    ``os.replace`` onto it) was measured on this host: the original content was
    CLOBBERED (marker survives = False) and nothing was raised. Both assertions below
    therefore fail on the old algorithm and pass on the new one.
    """
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "original-content-marker")

    def _competing_rotation(_reserved_path):
        # Disarm before recursing so the nested rotation runs cleanly.
        monkeypatch.setattr(kata_board, "_ROTATE_RACE_HOOK", None)
        kata_board.start_run(kata_dir, run_id=RUN_C, now=FIXED_NOW)

    monkeypatch.setattr(kata_board, "_ROTATE_RACE_HOOK", _competing_rotation)

    with pytest.raises(kata_board.CursorGrammarError) as exc:
        kata_board.start_run(kata_dir, run_id=RUN_B, now=FIXED_NOW)
    assert "nothing was discarded" in str(exc.value)

    # The winner (the competing rotation) still owns a LIVE cursor: a refusal must not
    # leave the run without one.
    assert kata_board.read_cursor(kata_dir).run_id == RUN_C

    archives = sorted(kata_dir.glob("board.*.archive.md"))
    assert len(archives) == 1, f"exactly the winner's archive should remain: {archives}"
    assert "original-content-marker" in archives[0].read_text(encoding="utf-8"), (
        "the pre-fix TOCTOU clobbered exactly this content"
    )


# ---------------------------------------------------------------------------
# Rotation LIVENESS — transient Windows contention must cost a retry, not the run
#
# The falsified claim (CI run 32003837572 @ b880810, windows-latest leg): "progress is
# guaranteed by construction … wins can never be empty".  It is not.  Every rotation in
# a round can be refused because ``os.replace`` — the move of the cursor onto its
# reserved archive name — answers PermissionError on Windows whenever ANY other handle
# holds the cursor open: CPython opens files without ``FILE_SHARE_DELETE``, and
# ``MoveFileEx`` needs DELETE access on the source.  Measured raw-OS on this host (no
# kata code): a held read handle ⇒ winerror 32 (ERROR_SHARING_VIOLATION) on the source,
# a held handle on the reservation ⇒ winerror 5 (ERROR_ACCESS_DENIED) on the
# destination, and in BOTH cases the identical rename succeeds the instant the handle
# closes.  Transient, therefore retryable; and every racer in ``start_run`` holds
# exactly such a handle inside ``_read_cursor_bytes``, as does any AV/indexer scanning
# the file the round just appended to.
# ---------------------------------------------------------------------------


class _SharingViolation(PermissionError):
    """A PermissionError carrying ``winerror`` on EVERY platform.

    The defect is Windows-only, but the retry policy is not: pinning it only under
    ``os.name == "nt"`` would leave the whole loop unexercised on the ubuntu leg — the
    exact asymmetry that let the D-27 POSIX strand hide.  A subclass attribute shadows
    ``OSError.winerror`` (which is absent on POSIX and read-only on Windows), so the
    shape reaching the code under test is byte-identical to the real thing.  The REAL
    OS error is pinned separately, by the Windows-only held-handle test below.
    """

    winerror = 32


class _FlakyReplace:
    """Stand-in for ``kata_board.os`` whose ``replace`` fails the first *failures*
    times — but ONLY for the cursor→archive move, so publication is untouched.
    """

    def __init__(self, failures: int, exc: type[OSError] = _SharingViolation) -> None:
        self._left = failures
        self._exc = exc
        self.calls = 0

    def __getattr__(self, name: str):  # everything else is the real os module
        return getattr(os, name)

    def replace(self, src, dst):
        if not str(dst).endswith(".archive.md"):
            return os.replace(src, dst)
        self.calls += 1
        if self._left > 0:
            self._left -= 1
            raise self._exc(13, "the process cannot access the file (injected)")
        return os.replace(src, dst)


def test_transient_contention_at_the_rotation_window_is_retried_not_refused(
    tmp_path, monkeypatch
):
    """THE LIVENESS PIN for CI run 32003837572. Deterministic; no thread timing.

    Pre-fix this raises ``CursorGrammarError`` on the FIRST sharing violation and the
    rotation is lost — which, when every racer in a round loses it at once, is exactly
    the observed "every rotation failed — no progress".  Post-fix the bounded retry
    absorbs the transient window and the rotation completes with its guarantees intact:
    the original content is archived exactly once and the new run owns a live cursor.
    """
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "content-that-must-survive")
    flaky = _FlakyReplace(failures=3)
    monkeypatch.setattr(kata_board, "os", flaky)

    header = kata_board.start_run(kata_dir, run_id=RUN_B, now=FIXED_NOW)

    assert header.run_id == RUN_B
    assert flaky.calls == 4, "3 refusals absorbed, the 4th attempt is the one that moved"
    archives = sorted(kata_dir.glob("board.*.archive.md"))
    assert len(archives) == 1, f"one rotation, one archive: {archives}"
    assert "content-that-must-survive" in archives[0].read_text(encoding="utf-8")
    assert kata_board.read_cursor(kata_dir).run_id == RUN_B


def test_rotation_retries_are_bounded_and_exhaustion_still_refuses_loudly(
    tmp_path, monkeypatch
):
    """The retry is a BOUNDED absorber, never a fail-open and never an open loop.

    Contention that outlasts the budget is still a first-class refusal: the run is
    denied, the live cursor survives untouched, no phantom archive is left behind, and
    the message names both the OS error and the budget it exhausted.
    """
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "never-rotated")
    flaky = _FlakyReplace(failures=10_000)  # contention that never lifts
    monkeypatch.setattr(kata_board, "os", flaky)

    with pytest.raises(kata_board.CursorGrammarError) as exc:
        kata_board.start_run(kata_dir, run_id=RUN_B, now=FIXED_NOW)

    assert flaky.calls == len(kata_board._ROTATE_RETRY_BACKOFF) + 1, (
        "the retry must be bounded by the declared backoff schedule"
    )
    assert "attempts" in str(exc.value), f"the refusal must name the budget: {exc.value}"
    assert kata_board.read_cursor(kata_dir).run_id == RUN_A, "the cursor must survive"
    assert "never-rotated" in (kata_dir / kata_board.CURSOR_FILENAME).read_text(
        encoding="utf-8"
    )
    assert not list(kata_dir.glob("board.*.archive.md")), "no phantom archive"


def test_a_permission_error_without_a_windows_errno_is_never_retried(
    tmp_path, monkeypatch
):
    """The retried class is NARROW: only the two measured Windows contention errnos.

    A POSIX ``EACCES`` — a genuinely broken ACL — carries no ``winerror``, so it must
    refuse on the first attempt rather than burn the budget pretending a permission
    problem might heal itself.
    """
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "content")
    flaky = _FlakyReplace(failures=1, exc=PermissionError)
    monkeypatch.setattr(kata_board, "os", flaky)

    with pytest.raises(kata_board.CursorGrammarError):
        kata_board.start_run(kata_dir, run_id=RUN_B, now=FIXED_NOW)

    assert flaky.calls == 1, "a non-contention PermissionError must not be retried"


@pytest.mark.skipif(os.name != "nt", reason="held handles only block rename on Windows")
def test_a_real_held_cursor_handle_costs_a_retry_not_the_rotation(tmp_path, monkeypatch):
    """The same pin driven by the REAL OS error, not an injected one (Windows only).

    A genuine read handle is held open across the first rotation attempt — precisely
    what a peer racer inside ``_read_cursor_bytes`` holds, and what an AV/indexer holds
    over a file just written — and released before the second.  Pre-fix the first
    ``PermissionError`` (winerror 32) ends the rotation; post-fix the retry rides it out.
    The interleaving is forced through the rotation race seam, so nothing here depends
    on thread scheduling.
    """
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "held-handle-marker")
    board = kata_dir / kata_board.CURSOR_FILENAME
    holder: list = []

    def _hold_then_release(_reserved_path):
        # Called before EVERY attempt: hold the cursor open for the first, let go for
        # the second — the shortest honest model of transient contention.
        if holder:
            holder.pop().close()
        else:
            holder.append(board.open("rb"))

    monkeypatch.setattr(kata_board, "_ROTATE_RACE_HOOK", _hold_then_release)
    try:
        header = kata_board.start_run(kata_dir, run_id=RUN_B, now=FIXED_NOW)
    finally:
        for fh in holder:
            fh.close()

    assert header.run_id == RUN_B
    archives = sorted(kata_dir.glob("board.*.archive.md"))
    assert len(archives) == 1
    assert "held-handle-marker" in archives[0].read_text(encoding="utf-8")
    assert kata_board.read_cursor(kata_dir).run_id == RUN_B


def test_concurrent_rotations_never_clobber_an_archive(tmp_path):
    """G11 in-process race: N rounds of real threads contending on one cursor.

    Invariants per round: the round's unique marker survives in EXACTLY one archive, at
    least one rotation succeeds, every failure is a loud CursorError, and the live
    cursor still parses.

    **What this test falsifies, measured rather than assumed.** Against the pre-fix
    algorithm on this host the marker invariant held in 25/25 rounds (a barrier start
    makes losers hit a missing cursor rather than a completed one, so the byte-level
    clobber does not reproduce here) — but raw ``FileNotFoundError`` and
    ``PermissionError`` escaped in every configuration, which the loud-refusal assertion
    catches. The clobber itself is pinned deterministically by the forced-interleaving
    test above.

    **POSIX (CI run 31989512531, ubuntu leg — the pending proof for this revision).**
    The ubuntu leg failed here on "no progress" with
    ``CursorParseError: cursor has no run-header block``. That message can only come from
    ``parse_header``, which ``start_run`` never calls — so it was a READER landing in a
    window where ``board.md`` existed with no header. The window was real and in
    PRODUCTION code, not in this test: the cursor was published by creating it with
    ``O_CREAT|O_EXCL`` and writing afterwards (both in the header write and in the
    refusal's restore path), so the file existed at zero bytes in between. Windows hides
    that window behind sharing violations; POSIX has no such serialization. The cure is
    in the code — :func:`kata_board._publish_cursor` now publishes complete-or-absent and
    claims the name exclusively — so the assertions below stay unconditional on both
    platforms rather than being framed per-platform.

    **Progress — the honest statement, after CI falsified the previous one.** This
    docstring used to claim progress was "guaranteed by construction … ``wins`` can never
    be empty", on the reasoning that publication elects the winner. CI run 32003837572
    (windows-latest, ``b880810``) refuted it with ``round 8: every rotation failed — no
    progress``: before a racer can publish it must ARCHIVE, and on Windows the archiving
    rename is vetoable by any concurrently held handle — including the ones every OTHER
    racer holds inside ``_read_cursor_bytes``. Nothing elected a winner because nobody
    got that far. What is structural is success-or-typed-refusal; progress is now made
    the ordinary outcome by riding out that window with a bounded retry
    (``kata_board._move_cursor_onto_reservation``, pinned deterministically above). The
    assertion below therefore tests a real property with a real failure mode: a
    no-progress round means contention that outlasted the whole budget, which is worth
    a red build — so it carries the refusals with it, and the next red run reads as a
    diagnosis rather than an archaeology dig.
    """
    rounds, workers = 25, 4

    for r in range(rounds):
        kata_dir = tmp_path / f"round{r}"
        kata_dir.mkdir()
        kata_board.start_run(kata_dir, run_id=RUN_A)
        marker = f"unique-marker-round-{r}"
        kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, marker)

        refusals: list[BaseException] = []
        unexpected: list[BaseException] = []
        wins: list[str] = []
        gate = threading.Barrier(workers)

        def rotate(i: int) -> None:
            gate.wait()  # release all threads into the race together
            try:
                header = kata_board.start_run(
                    kata_dir, run_id=f"run-20260816T20{i:04d}Z-{i:08x}"
                )
                wins.append(header.run_id)
            except kata_board.CursorError as exc:  # loud, expected under contention
                refusals.append(exc)
            except BaseException as exc:  # noqa: BLE001 — the point is to catch anything
                unexpected.append(exc)

        threads = [threading.Thread(target=rotate, args=(i,)) for i in range(workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        assert not any(t.is_alive() for t in threads), f"round {r}: a rotation hung"

        assert not unexpected, f"round {r}: non-CursorError escaped: {unexpected!r}"
        assert wins, (
            f"round {r}: every rotation failed — no progress. The refusals name the "
            f"syscall that lost, which is the whole diagnosis: "
            + " || ".join(str(e) for e in refusals)
        )

        archives = list(kata_dir.glob("board.*.archive.md"))
        hits = [a for a in archives if marker in a.read_text(encoding="utf-8")]
        assert len(hits) == 1, (
            f"round {r}: marker found in {len(hits)} archives (expected exactly 1) — "
            f"archives={[a.name for a in archives]}, refusals={len(refusals)}"
        )

        # Whatever the interleaving, the surviving cursor is still a valid cursor.
        assert kata_board.read_cursor(kata_dir).header.run_id


def test_live_cursor_is_never_observable_without_a_run_header(tmp_path):
    """THE POSIX PIN — the property CI run 31989512531 (ubuntu leg) falsified.

    A concurrent reader samples ``board.md`` throughout a contended rotation. Absent is
    legal (there is a real window between archiving the old cursor and publishing the
    new header), but **existing-and-headerless is not**: that is the stranded cursor a
    reader turns into ``CursorParseError: cursor has no run-header block``, which is
    exactly what the ubuntu leg reported. Pre-fix, the cursor was created with
    ``O_CREAT|O_EXCL`` and written afterwards — a genuine zero-byte window, in
    production code, in both the header write and the refusal's restore path. Windows
    masks it behind sharing violations; POSIX does not.

    Deliberately split from the race test above, and deliberately NOT asserting
    progress: on Windows a hot reader holding the cursor open makes ``os.replace`` fail
    with a sharing violation, so every rotation in a round can legitimately end in a
    typed refusal. That satisfies the contract (success-or-typed-refusal) but would make
    a progress assertion here a lie about what is being tested. Strand-freedom and the
    refusal class stay unconditional on both platforms.
    """
    rounds, workers = 12, 3

    for r in range(rounds):
        kata_dir = tmp_path / f"round{r}"
        kata_dir.mkdir()
        kata_board.start_run(kata_dir, run_id=RUN_A)
        kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, f"content-{r}")

        board = kata_dir / kata_board.CURSOR_FILENAME
        strands: list[bytes] = []
        unexpected: list[BaseException] = []
        stop = threading.Event()
        gate = threading.Barrier(workers)

        def observe() -> None:
            while not stop.is_set():
                try:
                    data = board.read_bytes()
                except OSError:
                    continue  # absent or momentarily unreadable — both legal
                if not data or not data.startswith(b"RUN "):
                    strands.append(data)

        def rotate(i: int) -> None:
            gate.wait()
            try:
                kata_board.start_run(kata_dir, run_id=f"run-20260816T21{i:04d}Z-{i:08x}")
            except kata_board.CursorError:
                pass  # typed refusal is a legal outcome — see the docstring
            except BaseException as exc:  # noqa: BLE001
                unexpected.append(exc)

        watcher = threading.Thread(target=observe, daemon=True)
        watcher.start()
        threads = [threading.Thread(target=rotate, args=(i,)) for i in range(workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        stop.set()
        watcher.join(timeout=30)

        assert not unexpected, f"round {r}: non-CursorError escaped: {unexpected!r}"
        assert not strands, (
            f"round {r}: the live cursor was observable without a run-header "
            f"{len(strands)}x (first sample: {strands[0]!r}) — this is the stranded "
            "cursor the ubuntu leg's CursorParseError was reading"
        )


# ---------------------------------------------------------------------------
# The line grammar — round trip over EVERY type
# ---------------------------------------------------------------------------


def test_cursor_grammar_roundtrip(tmp_path):
    """DECLARED EVIDENCE (PLAN cursor-grammar): every element of the cursor grammar
    round-trips write -> parse — header pointers, every TYPE, the lineage stamp, and
    the payload pointer."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()
    kata_board.start_run(
        kata_dir,
        run_id=RUN_B,
        prev_run=RUN_A,
        parent_run=RUN_A,
        prev_segment="segments/prior.md",
    )

    # Every worker + orchestrator + seam TYPE, plus a lineage-stamped line.
    kata_board.append_event(kata_dir, "seam", "SPAWN", TASK, "dispatch worker")
    spawn_seq = kata_board.read_cursor(kata_dir).lines[-1].seq
    for type_ in sorted(kata_board.WORKER_TYPES | kata_board.ORCH_TYPES):
        kata_board.append_event(
            kata_dir, AGENT, type_, TASK, f"msg-{type_}", parent_seq=spawn_seq
        )
    for type_ in ("PHASE", "DOWN", "DENY"):
        kata_board.append_event(kata_dir, "seam", type_, TASK, f"msg-{type_}")
    kata_board.append_verdict(
        kata_dir,
        "seam",
        TASK,
        "judge returned",
        {
            "verdict": "PASS",
            "evidencePointers": ["artifact:protocol/cursor.md"],
            "judgeDispatchSeq": spawn_seq,
            "runId": RUN_B,
        },
    )

    cursor = kata_board.read_cursor(kata_dir)

    # Header round-trip.
    assert cursor.header == kata_board.RunHeader(
        run_id=RUN_B,
        prev_run=RUN_A,
        parent_run=RUN_A,
        prev_segment="segments/prior.md",
    )

    # Every TYPE in the closed enumeration appears and parsed back as itself.
    seen = {ln.type for ln in cursor.lines}
    assert seen == kata_board.CURSOR_TYPES

    # Lineage stamps survive the round trip.
    stamped = [ln for ln in cursor.lines if ln.parent_seq is not None]
    assert len(stamped) == len(kata_board.WORKER_TYPES | kata_board.ORCH_TYPES)
    assert all(ln.parent_seq == spawn_seq for ln in stamped)

    # The VERDICT payload pointer resolves to the written JSON.
    verdict = next(ln for ln in cursor.lines if ln.type == "VERDICT")
    assert verdict.payload == f"payloads/{RUN_B}-{verdict.seq}.json"
    payload_file = kata_board.payload_path(kata_dir, verdict.payload)
    assert payload_file.parent == kata_dir / "payloads"
    assert json.loads(payload_file.read_text(encoding="utf-8"))["verdict"] == "PASS"

    # Re-render each parsed line and confirm byte-identical output (true round trip).
    raw = _cursor_lines(kata_dir)
    for line, rendered in zip(cursor.lines, raw, strict=True):
        assert (
            kata_board.format_line(
                utc=line.utc,
                seq=line.seq,
                agent=line.agent,
                type=line.type,
                task=line.task,
                msg=line.msg,
                parent_seq=line.parent_seq,
                payload=line.payload,
            ).rstrip("\n")
            == rendered
        )


def test_line_has_six_fields(tmp_path):
    """Each appended line must split into exactly 6 fields on ' | '."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "CLAIM", TASK, "starting task")

    parts = _cursor_lines(kata_dir)[0].split(" | ")
    assert len(parts) == 6, f"Expected 6 fields, got {len(parts)}: {parts}"


def test_line_field_positions(tmp_path):
    """utc | seq | agent | TYPE | task | msg — in that order (DESIGN §2.2 BNF)."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, "my-agent", "DONE", "T99", "tests passed")

    utc, seq, agent, type_, task, msg = _cursor_lines(kata_dir)[0].split(" | ")
    assert "T" in utc and (utc.endswith("+00:00") or utc.endswith("Z"))
    assert seq == "1"
    assert agent == "my-agent"
    assert type_ == "DONE"
    assert task == "T99"
    assert msg == "tests passed"


def test_unknown_type_is_refused(tmp_path):
    """The TYPE enumeration is closed."""
    kata_dir = _fresh(tmp_path)
    with pytest.raises(kata_board.CursorGrammarError):
        kata_board.append_event(kata_dir, AGENT, "SHIPIT", TASK, "nope")


def test_seam_worker_orch_type_partition():
    """The three writer classes partition the TYPE enumeration (DESIGN §2.3)."""
    assert kata_board.WORKER_TYPES & kata_board.SEAM_TYPES == frozenset()
    assert kata_board.WORKER_TYPES & kata_board.ORCH_TYPES == frozenset()
    assert kata_board.ORCH_TYPES & kata_board.SEAM_TYPES == frozenset()
    assert kata_board.SEAM_TYPES == frozenset(
        {"PHASE", "VERDICT", "SPAWN", "DOWN", "DENY"}
    )
    assert kata_board.WORKER_TYPES == frozenset(
        {"CLAIM", "DONE", "BLOCK", "ESCALATE", "NOTE", "PROGRESS"}
    )
    assert kata_board.ORCH_TYPES == frozenset({"DECISION"})


def test_field_carrying_separator_is_refused(tmp_path):
    """A pipe in agent/task would forge a field boundary — refused at the writer."""
    kata_dir = _fresh(tmp_path)
    with pytest.raises(kata_board.CursorGrammarError):
        kata_board.append_event(kata_dir, "ag|ent", "NOTE", TASK, "hi")
    with pytest.raises(kata_board.CursorGrammarError):
        kata_board.append_event(kata_dir, AGENT, "NOTE", "T|1", "hi")


def test_msg_may_contain_a_pipe(tmp_path):
    """msg is the tail field, so an embedded pipe is legal and survives parsing."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "a | b | c")
    assert kata_board.read_cursor(kata_dir).lines[0].msg == "a | b | c"


def test_msg_with_bare_payload_token_is_refused(tmp_path):
    """A msg may not smuggle the reserved ' payload=' token."""
    kata_dir = _fresh(tmp_path)
    with pytest.raises(kata_board.CursorGrammarError):
        kata_board.append_event(
            kata_dir, AGENT, "NOTE", TASK, "see payload=payloads/evil.json"
        )


# ---------------------------------------------------------------------------
# The LEGACY 5-field grammar parses NOWHERE
# ---------------------------------------------------------------------------


def test_legacy_five_field_line_is_refused():
    """The old grammar (protocol/cursor.md:9 pre-migration) is a parse REFUSAL."""
    legacy = "2026-08-16T10:15:00+00:00 | S1a-worker | CLAIM | T1 | starting task"
    with pytest.raises(kata_board.CursorParseError) as exc:
        kata_board.parse_line(legacy)
    assert "LEGACY" in str(exc.value)


def test_legacy_line_is_refused_not_skipped():
    """A legacy line inside an otherwise valid cursor aborts the parse — never skipped."""
    text = (
        f"RUN {RUN_A}\n"
        "2026-08-16T10:15:00+00:00 | 1 | w | CLAIM | T1 | ok\n"
        "2026-08-16T10:16:00+00:00 | w | DONE | T1 | legacy row\n"
    )
    with pytest.raises(kata_board.CursorParseError):
        kata_board.parse_cursor(text)


def test_legacy_line_whose_msg_has_a_pipe_is_still_refused():
    """A 5-field legacy line with a piped msg presents as 6 fields — refused via seq."""
    legacy = "2026-08-16T10:15:00+00:00 | w | NOTE | T1 | left | right"
    with pytest.raises(kata_board.CursorParseError):
        kata_board.parse_line(legacy)


def test_non_iso_utc_is_refused():
    """A malformed utc field RAISES — never skip-and-continue."""
    with pytest.raises(kata_board.CursorParseError):
        kata_board.parse_line("not-a-date | 1 | w | NOTE | T1 | hi")


# ---------------------------------------------------------------------------
# Seq assignment + ordering of record
# ---------------------------------------------------------------------------


def test_seq_is_observed_max_plus_one(tmp_path):
    """The appending writer stamps (observed max)+1."""
    kata_dir = _fresh(tmp_path)
    for expected in (1, 2, 3):
        line = kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, f"n{expected}")
        assert line.seq == expected
    assert kata_board.next_seq(kata_board.read_cursor(kata_dir)) == 4


def test_duplicate_worker_seqs_are_legal_and_ordered_by_file_position(tmp_path):
    """Concurrent worker appends may race; duplicate seqs order by file position."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, "w1", "CLAIM", "TA", "first", seq=7)
    kata_board.append_event(kata_dir, "w2", "CLAIM", "TB", "second", seq=7)

    cursor = kata_board.read_cursor(kata_dir)
    assert [ln.seq for ln in cursor.lines] == [7, 7]
    assert [ln.pos for ln in cursor.lines] == [0, 1]

    keys = [kata_board.order_key(cursor.run_id, ln) for ln in cursor.lines]
    assert keys == sorted(keys)
    assert keys[0] < keys[1], "file position is the tie-break for a duplicate seq"


def test_wall_clock_is_never_load_bearing(tmp_path):
    """Order of record ignores utc entirely: a later seq with an EARLIER clock still wins."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(
        kata_dir, AGENT, "NOTE", TASK, "seq1", now=datetime(2030, 1, 1, tzinfo=UTC)
    )
    kata_board.append_event(
        kata_dir, AGENT, "NOTE", TASK, "seq2", now=datetime(2020, 1, 1, tzinfo=UTC)
    )

    cursor = kata_board.read_cursor(kata_dir)
    ordered = kata_board.fold_order([cursor])
    assert [ln.msg for _rid, ln in ordered] == ["seq1", "seq2"]
    assert ordered[0][1].utc > ordered[1][1].utc, "clock disagrees; seq is the record"


def test_fold_order_walks_parent_run_tree(tmp_path):
    """Ordering of record = (runId, seq) + PARENT FOLD-ORDER: parents before children."""
    parent = _fresh(tmp_path, "parent", run_id=RUN_B)
    child_id = "run-20260816T090000Z-0000aaaa"  # sorts BEFORE the parent by run id
    child = _fresh(tmp_path, "child", run_id=child_id, parent_run=RUN_B)

    kata_board.append_event(parent, "seam", "SPAWN", "TA", "spawn arm")
    kata_board.append_event(child, "w", "CLAIM", "TA", "arm working")

    cursors = [
        kata_board.read_cursor(child),
        kata_board.read_cursor(parent),
    ]
    assert kata_board.run_fold_order(cursors) == (RUN_B, child_id)
    assert [rid for rid, _ln in kata_board.fold_order(cursors)] == [RUN_B, child_id]


def test_parent_run_cycle_is_refused(tmp_path):
    """A parent-run cycle is fail-loud, never a silent drop."""
    a = _fresh(tmp_path, "a", run_id=RUN_A, parent_run=RUN_B)
    b = _fresh(tmp_path, "b", run_id=RUN_B, parent_run=RUN_A)
    with pytest.raises(kata_board.CursorParseError):
        kata_board.run_fold_order([kata_board.read_cursor(a), kata_board.read_cursor(b)])


def test_parent_run_self_cycle_is_refused(tmp_path):
    """A 1-cycle IS a cycle: a run naming ITSELF as parent must never fold as a root.

    The contract's refusal is unconditional; exempting the self-edge would accept the
    shortest cycle while refusing every longer one.
    """
    selfie = _fresh(tmp_path, "selfie", run_id=RUN_A, parent_run=RUN_A)
    cursor = kata_board.read_cursor(selfie)
    assert cursor.header.parent_run == RUN_A  # the header itself round-trips

    with pytest.raises(kata_board.CursorParseError) as exc:
        kata_board.run_fold_order([cursor])
    assert "cycle" in str(exc.value)

    # The refusal must hold through every fold that stacks on run_fold_order.
    with pytest.raises(kata_board.CursorParseError):
        kata_board.fold_order([cursor])
    with pytest.raises(kata_board.CursorParseError):
        kata_board.fold_concurrency([cursor])
    with pytest.raises(kata_board.CursorParseError):
        kata_board.emit_concurrency(selfie)
    assert not (selfie / "concurrency.json").exists()


def test_parent_run_self_cycle_is_refused_alongside_healthy_runs(tmp_path):
    """The self-cycle is refused even when other runs in the fold are well-formed."""
    healthy = _fresh(tmp_path, "healthy", run_id=RUN_B)
    selfie = _fresh(tmp_path, "selfie", run_id=RUN_A, parent_run=RUN_A)
    with pytest.raises(kata_board.CursorParseError):
        kata_board.run_fold_order(
            [kata_board.read_cursor(healthy), kata_board.read_cursor(selfie)]
        )


# ---------------------------------------------------------------------------
# Lineage stamps
# ---------------------------------------------------------------------------


def test_lineage_stamp_round_trips(tmp_path):
    """seq~parent-seq parses into seq + parent_seq."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, "seam", "SPAWN", TASK, "dispatch")
    kata_board.append_event(kata_dir, AGENT, "CLAIM", TASK, "claimed", parent_seq=1)

    raw = _cursor_lines(kata_dir)[1]
    assert raw.split(" | ")[1] == "2~1"

    line = kata_board.read_cursor(kata_dir).lines[1]
    assert (line.seq, line.parent_seq) == (2, 1)


def test_lineage_stamp_must_be_digits():
    """A non-numeric lineage stamp is a refusal."""
    with pytest.raises(kata_board.CursorParseError):
        kata_board.parse_line("2026-08-16T10:15:00+00:00 | 2~abc | w | NOTE | T1 | hi")


# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------


def test_verdict_without_payload_is_refused(tmp_path):
    """VERDICT REQUIRES a pointed-to payload — writing one without is refused."""
    kata_dir = _fresh(tmp_path)
    with pytest.raises(kata_board.CursorGrammarError):
        kata_board.append_event(kata_dir, "seam", "VERDICT", TASK, "PASS")


def test_verdict_without_payload_is_refused_on_parse():
    """A hand-written VERDICT line missing its payload pointer is refused on read."""
    with pytest.raises(kata_board.CursorParseError):
        kata_board.parse_line("2026-08-16T10:15:00+00:00 | 4 | seam | VERDICT | T1 | PASS")


def test_payload_pointer_convention():
    """Payloads live under .kata/payloads/<runId>-<seq>.json (DESIGN §2.2)."""
    assert kata_board.payload_pointer(RUN_A, 12) == f"payloads/{RUN_A}-12.json"


def test_verdict_payload_schema_is_enforced(tmp_path):
    """{verdict, evidencePointers[], judgeDispatchSeq, runId} — all four required."""
    kata_dir = _fresh(tmp_path)
    with pytest.raises(kata_board.CursorGrammarError):
        kata_board.append_verdict(
            kata_dir, "seam", TASK, "PASS", {"verdict": "PASS", "runId": RUN_A}
        )
    with pytest.raises(kata_board.CursorGrammarError):
        kata_board.append_verdict(
            kata_dir,
            "seam",
            TASK,
            "PASS",
            {
                "verdict": "PASS",
                "evidencePointers": "not-a-list",
                "judgeDispatchSeq": 1,
                "runId": RUN_A,
            },
        )


def test_payload_is_written_before_the_line(tmp_path):
    """The pointer is never dangling: the payload file exists once the line does."""
    kata_dir = _fresh(tmp_path)
    line = kata_board.append_verdict(
        kata_dir,
        "seam",
        TASK,
        "judged",
        {
            "verdict": "NEEDS_WORK",
            "evidencePointers": [],
            "judgeDispatchSeq": 0,
            "runId": RUN_A,
        },
    )
    assert kata_board.payload_path(kata_dir, line.payload).exists()


@pytest.mark.parametrize(
    "evil",
    ["../../etc/passwd", "/etc/passwd", "payloads/../../out.json", "payloads/a b.json"],
)
def test_payload_pointer_traversal_is_refused(evil):
    """CWE-23: a crafted payload pointer never reaches a filesystem sink."""
    with pytest.raises(kata_board.CursorGrammarError):
        kata_board._guard_pointer(evil, what="payload")


def test_double_payload_token_is_refused_on_parse():
    """Write/read symmetry: format_line can never emit two payload tokens, so parsing
    a hand-crafted double-token line into a re-emittable msg is refused."""
    with pytest.raises(kata_board.CursorParseError) as exc:
        kata_board.parse_line(
            "2026-08-16T10:15:00+00:00 | 4 | seam | VERDICT | T1 | "
            "PASS payload=payloads/a.json payload=payloads/b.json"
        )
    assert "at most one payload pointer" in str(exc.value)


def test_no_line_survives_a_round_trip_it_could_not_have_been_written_as(tmp_path):
    """Every parseable line re-renders byte-identically — the symmetry the two folds buy."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "NOTE", TASK, "plain")
    kata_board.append_verdict(
        kata_dir,
        "seam",
        TASK,
        "judged",
        {
            "verdict": "PASS",
            "evidencePointers": [],
            "judgeDispatchSeq": 1,
            "runId": RUN_A,
        },
    )
    for line, raw in zip(
        kata_board.read_cursor(kata_dir).lines, _cursor_lines(kata_dir), strict=True
    ):
        assert (
            kata_board.format_line(
                utc=line.utc,
                seq=line.seq,
                agent=line.agent,
                type=line.type,
                task=line.task,
                msg=line.msg,
                parent_seq=line.parent_seq,
                payload=line.payload,
            ).rstrip("\n")
            == raw
        )


def test_payload_traversal_is_refused_on_parse():
    """A traversal pointer inside a cursor line is refused at parse time too — and as a
    CursorParseError, so a fail-soft consumer catches exactly one class on the read path."""
    with pytest.raises(kata_board.CursorParseError):
        kata_board.parse_line(
            "2026-08-16T10:15:00+00:00 | 4 | seam | VERDICT | T1 | "
            "PASS payload=../../secrets.json"
        )


# ---------------------------------------------------------------------------
# Append-only invariant
# ---------------------------------------------------------------------------


def test_multiple_appends_are_append_only(tmp_path):
    """Prior lines must survive after a second append (never rewritten)."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, AGENT, "CLAIM", "T1", "first")
    first_line = _cursor_lines(kata_dir)[0]

    kata_board.append_event(kata_dir, AGENT, "DONE", "T1", "second")
    lines = _cursor_lines(kata_dir)

    assert len(lines) == 2
    assert lines[0] == first_line, "First line must be unchanged after second append"


def test_multiple_appends_preserve_order(tmp_path):
    """Lines must appear in the order they were written."""
    kata_dir = _fresh(tmp_path)
    types = ["CLAIM", "NOTE", "DONE"]
    for t in types:
        kata_board.append_event(kata_dir, AGENT, t, TASK, f"msg-{t}")

    cursor = kata_board.read_cursor(kata_dir)
    assert [ln.type for ln in cursor.lines] == types


# ---------------------------------------------------------------------------
# append_progress
# ---------------------------------------------------------------------------


def test_append_progress_type_and_msg(tmp_path):
    """append_progress must emit TYPE=PROGRESS with msg '<step>/<n> <label>'."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_progress(kata_dir, AGENT, TASK, 3, 5, "writing tests")

    line = kata_board.read_cursor(kata_dir).lines[0]
    assert line.type == "PROGRESS"
    assert line.msg == "3/5 writing tests"


def test_append_progress_six_fields(tmp_path):
    """append_progress lines obey the same 6-field grammar."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_progress(kata_dir, AGENT, TASK, 1, 4, "init")
    assert len(_cursor_lines(kata_dir)[0].split(" | ")) == 6


def test_progress_is_excluded_from_concurrency_evidence(tmp_path):
    """PROGRESS is a liveness heartbeat, never concurrency evidence."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_progress(kata_dir, AGENT, TASK, 1, 4, "init")
    model = kata_board.fold_concurrency([kata_board.read_cursor(kata_dir)])
    assert model["workerCount"] == 0
    assert model["maxInFlight"] == 0


# ---------------------------------------------------------------------------
# The fold — pure, cross-cursor, (runId, seq)
# ---------------------------------------------------------------------------


def _two_overlapping_workers(kata_dir: Path) -> None:
    kata_board.append_event(kata_dir, "w1", "CLAIM", "TA", "start A")
    kata_board.append_event(kata_dir, "w2", "CLAIM", "TB", "start B")
    kata_board.append_event(kata_dir, "w1", "DONE", "TA", "end A")
    kata_board.append_event(kata_dir, "w2", "DONE", "TB", "end B")


def test_fold_detects_overlap_in_seq_space(tmp_path):
    """maxInFlight/genuinelyParallel are computed on seq spans, not on clocks."""
    kata_dir = _fresh(tmp_path)
    _two_overlapping_workers(kata_dir)

    model = kata_board.fold_concurrency([kata_board.read_cursor(kata_dir)])
    assert model["maxInFlight"] == 2
    assert model["genuinelyParallel"] is True
    assert model["workerCount"] == 2
    assert model["workers"][f"{RUN_A}#TA"]["startSeq"] == 1
    assert model["workers"][f"{RUN_A}#TA"]["endSeq"] == 3
    assert model["overlaps"] == [{"fromSeq": 2, "runId": RUN_A, "toSeq": 3}]


def test_fold_sequential_run_is_not_a_failure(tmp_path):
    """A single-worker run legitimately reports maxInFlight 1 (K6 — evidence, not a gate)."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, "w1", "CLAIM", "TA", "start")
    kata_board.append_event(kata_dir, "w1", "DONE", "TA", "end")

    model = kata_board.fold_concurrency([kata_board.read_cursor(kata_dir)])
    assert model["maxInFlight"] == 1
    assert model["genuinelyParallel"] is False


def test_fold_keeps_the_full_span_of_a_redispatched_task(tmp_path):
    """Earliest CLAIM / latest DONE — a naive last-write CLAIM would erase a real overlap."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, "w1", "CLAIM", "TA", "attempt 1")
    kata_board.append_event(kata_dir, "w1", "DONE", "TA", "attempt 1 done")
    kata_board.append_event(kata_dir, "w1", "CLAIM", "TA", "re-dispatch")
    kata_board.append_event(kata_dir, "w1", "DONE", "TA", "re-dispatch done")

    span = kata_board.fold_concurrency([kata_board.read_cursor(kata_dir)])["workers"][
        f"{RUN_A}#TA"
    ]
    assert (span["startSeq"], span["endSeq"]) == (1, 4)


def test_fold_is_cross_cursor(tmp_path):
    """The fold spans multiple cursors, keyed by (runId, seq)."""
    parent = _fresh(tmp_path, "parent", run_id=RUN_B)
    child_id = "run-20260816T120000Z-cccc1111"
    child = _fresh(tmp_path, "child", run_id=child_id, parent_run=RUN_B)
    _two_overlapping_workers(parent)
    kata_board.append_event(child, "arm", "CLAIM", "TC", "arm start")
    kata_board.append_event(child, "arm", "DONE", "TC", "arm end")

    model = kata_board.fold_concurrency(
        [kata_board.read_cursor(child), kata_board.read_cursor(parent)]
    )
    assert model["runs"] == [RUN_B, child_id]
    assert model["workerCount"] == 3
    assert set(model["workers"]) == {
        f"{RUN_B}#TA",
        f"{RUN_B}#TB",
        f"{child_id}#TC",
    }


def test_fold_is_pure_no_side_effects(tmp_path):
    """fold is pure; side effects only after fold completes (DESIGN §2.8)."""
    kata_dir = _fresh(tmp_path)
    _two_overlapping_workers(kata_dir)
    cursor = kata_board.read_cursor(kata_dir)

    before = sorted(p.name for p in kata_dir.iterdir())
    kata_board.fold_concurrency([cursor])
    kata_board.fold_order([cursor])
    kata_board.run_fold_order([cursor])
    after = sorted(p.name for p in kata_dir.iterdir())

    assert before == after, "a fold must not touch the filesystem"


def test_fold_is_deterministic(tmp_path):
    """Same input ⇒ same bytes (no clock, no set-iteration order)."""
    kata_dir = _fresh(tmp_path)
    _two_overlapping_workers(kata_dir)
    cursor = kata_board.read_cursor(kata_dir)

    first = json.dumps(kata_board.fold_concurrency([cursor]), sort_keys=True)
    second = json.dumps(kata_board.fold_concurrency([cursor]), sort_keys=True)
    assert first == second


def test_emit_writes_only_after_the_fold_completes(tmp_path):
    """A refusing fold produces NO artifact — the side effect follows the fold."""
    kata_dir = _fresh(tmp_path)
    kata_board.append_event(kata_dir, "w1", "DONE", "TA", "done at seq 1")
    kata_board.append_event(kata_dir, "w1", "CLAIM", "TA", "claim at seq 2")

    with pytest.raises(kata_board.CursorParseError):
        kata_board.emit_concurrency(kata_dir)
    assert not (kata_dir / "concurrency.json").exists()


def test_emit_concurrency_writes_the_artifact(tmp_path):
    """emit_concurrency writes .kata/concurrency.json with the K5-shaped model."""
    kata_dir = _fresh(tmp_path)
    _two_overlapping_workers(kata_dir)

    model = kata_board.emit_concurrency(kata_dir)
    written = json.loads((kata_dir / "concurrency.json").read_text(encoding="utf-8"))
    assert written == model
    for key in ("maxInFlight", "genuinelyParallel", "workerCount", "workers",
                "overlaps", "runs", "ordering", "source"):
        assert key in written


# ---------------------------------------------------------------------------
# write_state
# ---------------------------------------------------------------------------


def test_write_state_creates_state_json(tmp_path):
    """write_state must create state.json in kata_dir."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {"plan": "test.md", "tasks": {}, "updatedUtc": "2026-01-01T00:00:00+00:00"}
    kata_board.write_state(kata_dir, state)

    assert (kata_dir / "state.json").exists()


def test_write_state_round_trips_json(tmp_path):
    """write_state must produce valid JSON that round-trips exactly."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {
        "plan": "phase/plan.md",
        "tasks": {"T1": "gated", "T2": "in-progress"},
        "gate": {"tests": "10/0/0"},
        "updatedUtc": "2026-06-21T00:00:00+00:00",
    }
    kata_board.write_state(kata_dir, state)

    loaded = json.loads((kata_dir / "state.json").read_text(encoding="utf-8"))
    assert loaded == state


def test_write_state_no_leftover_temp_file(tmp_path):
    """write_state must leave no .tmp file after a successful write (atomic replace)."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {"tasks": {}, "updatedUtc": "2026-06-21T00:00:00+00:00"}
    kata_board.write_state(kata_dir, state)

    tmp_files = list(kata_dir.glob("*.tmp"))
    assert tmp_files == [], f"Leftover temp files: {tmp_files}"


def test_write_state_overwrites_previous(tmp_path):
    """write_state must overwrite (not append) the prior state.json."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state1 = {"tasks": {"T1": "assigned"}, "updatedUtc": "2026-06-21T00:00:00+00:00"}
    kata_board.write_state(kata_dir, state1)

    state2 = {"tasks": {"T1": "gated"}, "updatedUtc": "2026-06-21T01:00:00+00:00"}
    kata_board.write_state(kata_dir, state2)

    loaded = json.loads((kata_dir / "state.json").read_text(encoding="utf-8"))
    assert loaded == state2


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------


def test_update_task_changes_one_task(tmp_path):
    """update_task must change exactly the targeted task's status."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {
        "tasks": {"T1": "assigned", "T2": "in-progress", "T3": "gated"},
        "updatedUtc": "2026-06-21T00:00:00+00:00",
    }
    result = kata_board.update_task(kata_dir, state, "T2", "done")

    assert result["tasks"]["T2"] == "done"


def test_update_task_preserves_other_tasks(tmp_path):
    """update_task must not alter tasks other than the target."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {
        "tasks": {"T1": "assigned", "T2": "in-progress", "T3": "gated"},
        "updatedUtc": "2026-06-21T00:00:00+00:00",
    }
    result = kata_board.update_task(kata_dir, state, "T2", "done")

    assert result["tasks"]["T1"] == "assigned"
    assert result["tasks"]["T3"] == "gated"


def test_update_task_sets_updated_utc(tmp_path):
    """update_task must refresh updatedUtc to a current timestamp."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    old_ts = "2020-01-01T00:00:00+00:00"
    state = {"tasks": {"T1": "assigned"}, "updatedUtc": old_ts}
    result = kata_board.update_task(kata_dir, state, "T1", "in-progress")

    assert result["updatedUtc"] != old_ts
    assert "T" in result["updatedUtc"]  # still looks like ISO-8601


def test_update_task_persists_to_disk(tmp_path):
    """update_task must persist the new state to state.json."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {"tasks": {"T1": "assigned"}, "updatedUtc": "2026-06-21T00:00:00+00:00"}
    kata_board.update_task(kata_dir, state, "T1", "done")

    loaded = json.loads((kata_dir / "state.json").read_text(encoding="utf-8"))
    assert loaded["tasks"]["T1"] == "done"


def test_update_task_returns_mutated_state(tmp_path):
    """update_task must return the full (mutated) state dict."""
    kata_dir = tmp_path / "kata"
    kata_dir.mkdir()

    state = {"tasks": {"T1": "assigned"}, "updatedUtc": "2026-06-21T00:00:00+00:00"}
    result = kata_board.update_task(kata_dir, state, "T1", "gated")

    assert isinstance(result, dict)
    assert "tasks" in result
    assert result["tasks"]["T1"] == "gated"


def test_emitter_creates_kata_dir_if_absent(tmp_path):
    """Integration robustness: start_run creates .kata/ (the orchestrator should not
    have to pre-create it); the first state write creates it too."""
    fresh = tmp_path / "newrun" / ".kata"  # does NOT exist yet
    assert not fresh.exists()
    kata_board.start_run(fresh, run_id=RUN_A)
    kata_board.append_event(fresh, "orch", "DECISION", "-", "first event")
    assert (fresh / kata_board.CURSOR_FILENAME).exists()
    kata_board.write_state(fresh, {"tasks": {}, "updatedUtc": "t"})
    assert (fresh / "state.json").exists()
