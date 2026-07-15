"""kata_crew.py — the pure, agnostic crew/roster renderer (subagent-monitor S1).

The kata statusline gains a stylized subagent/crew tracker in the D162 dim theme: a chip per
LIVE worker showing role · model · dispatch-time reasoning-effort · liveness (▰ fresh heartbeat /
▱ stale). The host statusline payload carries ZERO subagent info (GRILL D3), so crew truth comes
from a conductor-written **dispatch roster** at ``.kata/dispatch.json`` — single-writer (the
conductor), one entry per dispatch, closed at the task gate. This module is the portable core:
stdlib-only, no adapter dependency, Determinism-Doctrine-conformant, so codex/kiro bindings can
re-skin the SAME renderer later (D1 — the alignment carve-out).

Determinism (docs/DETERMINISM-DOCTRINE.md):
- **Law 7 (injectable clocks):** every decision that reads a clock takes ``now`` — ``liveness``
  and ``render_crew`` require it (no default); the write helpers accept ``now=None`` and stamp
  ``datetime.now(UTC)`` ONLY as a persisted log stamp (never a compared value).
- **Laws 2/3/10 (sorted iteration, explicit tie-break):** ``render_crew`` orders open entries by
  ``dispatchedAt`` then ``taskId`` — a total order, stated not implied.
- **Law 5 (sort_keys on committed JSON):** the roster is serialized ``sort_keys=True``.
- Atomic writes via ``fs_atomic.atomic_write_text`` (the D159 reader-corruption fix).

Posture split (mirrors kata_settings):
- **Writes fail-CLOSED** — ``write_roster_entry`` / ``close_roster_entry`` refuse to overwrite a
  corrupt/non-dict existing roster (``ValueError``; the file is left byte-unchanged — the
  ``record_accepted_defaults`` never-clobber posture).
- **Reads fail-SOFT** — ``read_roster`` degrades an absent/corrupt/non-dict file to ``{}`` so a
  statusline tick NEVER raises (the ``read_settings`` lenient-read side).

Honesty limit (GRILL D4): a subagent's live "thinking" state is unobservable from outside the
host and is NEVER rendered — the dispatch-time effort tier + heartbeat liveness are the truthful
substitutes.

Public API
----------
write_roster_entry(kata_dir, task_id, *, role, model, effort, now=None) -> Path
close_roster_entry(kata_dir, task_id, *, now=None) -> Path
read_roster(kata_dir) -> dict                                    # fail-soft ⇒ {} on any trouble
liveness(entry, board_text, task_id, *, now, deadline_minutes) -> bool   # NEVER raises on board
render_crew(roster, board_text, *, now, deadline_minutes=10) -> str      # the chip run ("" empty)
render_model_chip(payload) -> str                                # dim shortname ("" absent/bad)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fs_atomic import atomic_write_text

#: Roster schema version (`.kata/dispatch.json` top-level ``v``).
ROSTER_VERSION = 1

#: Roster file basename inside the ``.kata/`` dir.
_ROSTER_FILENAME = "dispatch.json"

#: Valid dispatch-time reasoning-effort tiers (GRILL D4 — the truthful substitute for "thinking").
_EFFORTS = frozenset({"L", "M", "H"})

# --- Dim theme (mirror statusline_chain._ANSI_DIM/_ANSI_RESET — same bytes ⇒ theme matches) ---
_ANSI_DIM = "\x1b[2m"
_ANSI_RESET = "\x1b[0m"

#: Crew marker prefix + chip glyphs (the pinned D5 layout — byte-exact).
_CREW_MARKER = "⚒ "
_CHIP_SEP = " "
_DOT = "·"
_LIVE_MARK = "▰"
_STALE_MARK = "▱"

#: Truncate the chip run at this many chips, then append ` +N` (DESIGN D5).
_MAX_CHIPS = 3


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _roster_path(kata_dir: str | Path) -> Path:
    """The roster file path: ``<kata_dir>/dispatch.json``."""
    return Path(kata_dir) / _ROSTER_FILENAME


def _strict_load(path: Path) -> dict:
    """Fail-CLOSED load for the write path: ``{}`` when absent, ``ValueError`` when corrupt/non-dict.

    Mirrors ``kata_settings._load_existing`` (the C-4 never-clobber posture): a writer about to
    overwrite must never destroy state it cannot understand. Deliberately NOT ``read_roster``
    (which is lenient for the render path).
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"kata_crew: refusing to overwrite unparseable roster file: {path}"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(
            f"kata_crew: refusing to overwrite unparseable roster file (not an object): {path}"
        )
    return data


def _load_workers_for_write(path: Path) -> dict:
    """Return the existing ``workers`` map for a write, fail-closed on structural corruption.

    A present-but-non-dict ``workers`` is structural corruption we cannot safely merge into —
    fail-closed (never clobber), same class as an unparseable file.
    """
    data = _strict_load(path)  # fail-closed on unparseable / non-dict top level
    workers = data.get("workers")
    if workers is None:
        return {}
    if not isinstance(workers, dict):
        raise ValueError(
            f"kata_crew: refusing to overwrite roster with non-object 'workers': {path}"
        )
    return workers


def _iso(now: datetime) -> str:
    """ISO-8601 stamp for a persisted timestamp (matches the board / kata_version stamp form)."""
    return now.isoformat()


def _write_roster(path: Path, workers: dict) -> None:
    """Atomically write the roster (sort_keys=True, law 5; trailing newline; parent mkdir)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = {"v": ROSTER_VERSION, "workers": workers}
    atomic_write_text(path, json.dumps(out, indent=2, sort_keys=True) + "\n")


def _parse_iso(value: object) -> datetime | None:
    """Parse an ISO-8601 string to a tz-AWARE datetime (assume UTC if naive); ``None`` on failure.

    Never raises — used by both the liveness board parse (must survive garbage) and the entry
    ``dispatchedAt`` read.
    """
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.strip())
    except (ValueError, TypeError):
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _latest_board_heartbeat(board_text: object, task_id: str) -> datetime | None:
    """The latest CLAIM/PROGRESS self-stamp for ``task_id``, or ``None``.

    Own LENIENT parse of the board line grammar ``<ts> | <agent> | <TYPE> | <task> | <msg>``
    (protocol/board.md): an unparseable line is SKIPPED — this NEVER raises on malformed
    ``board_text`` (freeze-gate F3). Deliberately does NOT reuse ``kata_telemetry.parse_progress_events``
    (that raises by design — it is a gate parser; this is a statusline tick).
    """
    if not isinstance(board_text, str):
        return None
    latest: datetime | None = None
    for raw in board_text.splitlines():
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 5:
            continue
        ts, _agent, typ, task, _msg = parts[:5]
        if typ not in ("CLAIM", "PROGRESS"):
            continue
        if task != str(task_id):
            continue
        when = _parse_iso(ts)
        if when is None:
            continue
        if latest is None or when > latest:
            latest = when
    return latest


# --------------------------------------------------------------------------- #
# Roster API — the conductor's single-writer surface
# --------------------------------------------------------------------------- #
def write_roster_entry(
    kata_dir: str | Path,
    task_id: str,
    *,
    role: str,
    model: str,
    effort: str,
    now: datetime | None = None,
) -> Path:
    """Write (or replace) the roster entry for ``task_id`` — atomic, fail-closed on corruption.

    Single-writer contract: only the conductor calls this (GRILL D3). ``effort`` must be one of
    ``L``/``M``/``H``. A corrupt/non-dict existing roster ⇒ ``ValueError`` and the file is left
    byte-unchanged (never-clobber). ``now=None`` stamps ``datetime.now(UTC)`` (a persisted log
    stamp only — never a compared value, law 7).
    """
    if not task_id or not str(task_id).strip():
        raise ValueError("kata_crew: task_id is required")
    if effort not in _EFFORTS:
        raise ValueError(f"kata_crew: effort must be one of {sorted(_EFFORTS)}, got {effort!r}")
    stamp = _iso(now if now is not None else datetime.now(UTC))
    path = _roster_path(kata_dir)
    workers = _load_workers_for_write(path)  # fail-closed on corrupt/non-dict
    workers[str(task_id)] = {
        "role": role,
        "model": model,
        "effort": effort,
        "dispatchedAt": stamp,
        "closedAt": None,
    }
    _write_roster(path, workers)
    return path


def close_roster_entry(
    kata_dir: str | Path,
    task_id: str,
    *,
    now: datetime | None = None,
) -> Path:
    """Close the roster entry for ``task_id`` (set ``closedAt``) — atomic, fail-closed on corruption.

    A missing entry (or absent file) is a harmless no-op (no write). A corrupt/non-dict existing
    roster ⇒ ``ValueError``, file byte-unchanged (never-clobber). ``now=None`` stamps
    ``datetime.now(UTC)``.
    """
    path = _roster_path(kata_dir)
    workers = _load_workers_for_write(path)  # fail-closed on corrupt/non-dict
    entry = workers.get(str(task_id))
    if not isinstance(entry, dict):
        return path  # nothing to close — no-op, no write
    entry["closedAt"] = _iso(now if now is not None else datetime.now(UTC))
    _write_roster(path, workers)
    return path


def read_roster(kata_dir: str | Path) -> dict:
    """Read the roster fail-SOFT: absent/corrupt/non-dict ⇒ ``{}`` (a statusline tick never raises).

    The lenient-read side (mirrors ``kata_settings.read_settings``). Returns the full roster dict
    (``{"v": .., "workers": {..}}``) on success; ``{}`` otherwise.
    """
    path = _roster_path(kata_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


# --------------------------------------------------------------------------- #
# Liveness — display-only, NEVER gates (GRILL D3)
# --------------------------------------------------------------------------- #
def liveness(
    entry: dict,
    board_text: object,
    task_id: str,
    *,
    now: datetime,
    deadline_minutes: float,
) -> bool:
    """Return whether the worker is FRESH: display-only, NEVER gates (GRILL D3).

    Fresh IFF the MAX of the entry's ``dispatchedAt`` and the task's latest board CLAIM/PROGRESS
    self-stamp is within ``deadline_minutes`` of ``now`` (the board corroborates — a fresh
    heartbeat rescues a stale ``dispatchedAt``; absent board ⇒ ``dispatchedAt`` alone). NEVER
    raises on malformed ``board_text`` — unparseable lines are skipped (freeze-gate F3). When no
    anchor timestamp is parseable at all, the worker is treated as STALE (cannot confirm ⇒ hollow,
    never a fabricated ▰).
    """
    dispatched = _parse_iso(entry.get("dispatchedAt")) if isinstance(entry, dict) else None
    board = _latest_board_heartbeat(board_text, task_id)
    stamps = [s for s in (dispatched, board) if s is not None]
    if not stamps:
        return False  # no parseable anchor ⇒ stale (never fabricate freshness)
    last = max(stamps)
    now_utc = now if now.tzinfo is not None else now.replace(tzinfo=UTC)
    return (now_utc - last) <= timedelta(minutes=deadline_minutes)


# --------------------------------------------------------------------------- #
# Rendering — the pinned D5 chip run
# --------------------------------------------------------------------------- #
def _role_letter(role: object) -> str:
    """First letter of the role, uppercased (C/V/R/O/E per the roles vocabulary); ``?`` if empty."""
    text = str(role) if role else ""
    return text[0].upper() if text else "?"


def _chip(entry: dict, live: bool) -> str:
    """One chip: ``<RoleLetter>·<model>·<effort><liveness>`` (model rendered VERBATIM)."""
    role_letter = _role_letter(entry.get("role"))
    model = str(entry.get("model") or "")
    effort = str(entry.get("effort") or "")
    mark = _LIVE_MARK if live else _STALE_MARK
    return f"{role_letter}{_DOT}{model}{_DOT}{effort}{mark}"


def render_crew(
    roster: object,
    board_text: object,
    *,
    now: datetime,
    deadline_minutes: float = 10,
) -> str:
    """Render the dim crew chip run, or ``""`` when there is nothing to show (the slot vanishes).

    Open entries only (``closedAt`` null), sorted by ``dispatchedAt`` then ``taskId`` (law 10),
    truncated at :data:`_MAX_CHIPS` chips + ` +N`. Robust to a non-dict roster / malformed
    entries (EV-1 — never blank or crash the whole segment from bad crew data). ``deadline_minutes``
    is the render-time staleness window (default 10; the caller may pass ``livenessDeadline``).
    """
    workers = roster.get("workers") if isinstance(roster, dict) else None
    if not isinstance(workers, dict):
        return ""

    open_items: list[tuple[str, dict]] = []
    for task_id, entry in workers.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("closedAt") is not None:
            continue
        open_items.append((str(task_id), entry))
    if not open_items:
        return ""

    # Total order: dispatchedAt then taskId (laws 2/3/10 — explicit tie-break, never sort-stability).
    open_items.sort(key=lambda kv: (str(kv[1].get("dispatchedAt") or ""), kv[0]))

    chips = [
        _chip(entry, liveness(entry, board_text, task_id, now=now, deadline_minutes=deadline_minutes))
        for task_id, entry in open_items
    ]
    total = len(chips)
    body = _CHIP_SEP.join(chips[:_MAX_CHIPS])
    if total > _MAX_CHIPS:
        body += f" +{total - _MAX_CHIPS}"
    return f"{_ANSI_DIM}{_CREW_MARKER}{body}{_ANSI_RESET}"


def render_model_chip(payload: object) -> str:
    """Return the dim main-session model shortname chip, or ``""`` when absent/malformed (EV-1).

    Shortname = the lowercased FIRST token of ``payload.model.display_name`` (e.g. "Fable 5" →
    ``fable``). Any missing/non-string/blank field ⇒ ``""`` (today's exact segment, no model chip).
    """
    if not isinstance(payload, dict):
        return ""
    model = payload.get("model")
    if not isinstance(model, dict):
        return ""
    display_name = model.get("display_name")
    if not isinstance(display_name, str) or not display_name.strip():
        return ""
    short = display_name.strip().split()[0].lower()
    return f"{_ANSI_DIM}{short}{_ANSI_RESET}"
