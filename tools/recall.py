"""recall.py — the Recall read-CONTRACT (recall/v1) + the files-only default adapter.

Recall is the **read-side** of a second brain: it SURFACES prior knowledge so the
``kata-initiate`` grill/mirror can weigh it. Recall is **READ-ONLY** — it never
writes, never decides, never gates, never mutates a skill/protocol/tool, and never
touches ``INTENT.md`` (PINNED). The decider (``kata-reason``) and the write/distill
half (the β LEARN feed, D74) are OUT of scope. See
``.planning/specs/second-brain-learning/PLAN-recall.md`` (Slice R1).

The contract vs the adapter (the load-bearing separation)
---------------------------------------------------------
* **The CONTRACT** = ``recall_payload_schema()`` (the single source of truth for the
  payload shape) + the selection/staleness/read-only rules. It validates **SHAPE
  (required keys + types) ONLY** — it **NEVER** closes a source/backend vocabulary.
* **The files-only adapter** = ``recall_from_paths(...)`` + the per-source parsers:
  the default backend that serves the contract from six on-disk artifacts, plus an
  optional config-gated SEVENTH source — the second-brain synthesis feed dir
  (``feed_dir``, SB-L5): ``parse_synthesis_pages`` reads ``*.md`` synthesis pages
  (sorted recursive walk) as ``source="second-brain"`` candidates. Unconfigured
  (``feed_dir=None``) the adapter behaves byte-identically to the six-source form.

B1 — OPEN adapter-supplied labels (pinned IN the schema)
--------------------------------------------------------
``RecallRecord.source``, ``provenance.backend`` and ``provenance.produced_by`` are
**OPEN, adapter-supplied strings** — type-checked (must be ``str``), **NEVER**
enum-checked. The files-only values (``"lessons"`` / ``"files-only"`` / ``"repo"``)
are *that adapter's* labels, not the contract's closed set. An external
Obsidian/kiban/kagami adapter MUST be able to build a payload with
``source="obsidian-note"`` / ``backend="obsidian"`` / ``produced_by="kiban"`` and
have it validate — otherwise it would have to re-contract. This is the deliberate
*opposite* of ``validation_misses.miss_schema()``'s closed ``severity`` /
``what_caught_it`` enums: Recall mirrors only that module's single-source-of-truth
*schema-function* pattern, NOT its closed-enum enforcement.

N1 — selection is a hard token-overlap predicate
-------------------------------------------------
A ``RecallRecord`` passes ONLY if its tags+title+excerpt tokens overlap the query
terms (> 0 overlap). Recency only **RANKS among the passers** — a zero-overlap-but-
recent record is **EXCLUDED**. Recurrences **bypass** selection (always surfaced).
**NO embeddings / NO RAG** (case-insensitive token overlap only).

N3 — RecurrenceRecord projects out raw evidence
-----------------------------------------------
``recurrence_detect.actionable_recurrences`` returns each cluster WITH ``evidence``
(the raw miss dicts, incl. ``what_conformance_missed`` text). The adapter PROJECTS
these out — a RecurrenceRecord keeps ONLY the 7 contract fields. Raw miss text never
reaches the payload or the brief (secret-hygiene + altitude).

Security posture (exec-safety.md)
---------------------------------
PURE — no subprocess, no eval, no exec, no shell; no write surface (returns a dict).
Path reads are ``..``-guarded (CWE-23) via ``_guard_path`` (mirrors
``validation_misses._guard_path``); I/O failure is tolerant (returns ``[]`` /
partial, never raises into the caller — mirrors ``read_misses``). Reuses the pure
``recurrence_detect.detect_from_paths`` by name (no re-clustering). Assertable by
the source scan in ``test_recall.py`` (no exec sink, no embedding/vector import).

Public surfaces (cite-able by name per protocol/reuse-claims.md)
----------------------------------------------------------------
recall_payload_schema  — THE CONTRACT: single source of truth (shape, vocab-OPEN)
validate_payload       — shape validator for the contract (keys + types, OPEN labels)
match_score            — token-overlap + recency component (pure; no embeddings)
token_overlap          — the case-insensitive token-overlap set (the N1 predicate)
select_records         — overlap>0 GATE, then recency RANKS the passers (N1)
parse_lessons / parse_decisions / parse_intent / parse_understand — source parsers
parse_synthesis_pages  — the optional 7th source: second-brain feed dir (SB-L5)
build_payload          — assemble a contract-shaped payload
recall_from_paths      — the files-only default adapter entry point
_guard_path            — ``..`` traversal guard (CWE-23)
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path

import recurrence_detect

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Contract constants (single source of truth)
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "recall/v1"
DEFAULT_BACKEND = "files-only"

# Documented query kinds (type-checked str; NOT a hard enum here).
_QUERY_KINDS: tuple[str, ...] = ("project", "research", "version-up")

# RecallRecord field set (the 9 contract fields).
_RECORD_FIELDS: tuple[str, ...] = (
    "id", "source", "source_path", "title", "excerpt",
    "tags", "match_score", "provenance", "stale",
)
_RECORD_ALL_FIELDS: frozenset[str] = frozenset(_RECORD_FIELDS)

# RecurrenceRecord field set — EXACTLY these 7 (raw `evidence` projected OUT, N3).
_RECURRENCE_FIELDS: tuple[str, ...] = (
    "key", "responsible_skill", "failure_class", "distinct_runs",
    "severity_tier", "off_vocabulary", "open",
)

# Staleness threshold (decision #4 — a date-based HINT only, NEVER a filter).
_STALE_DAYS = 365
# Recency scale — keeps the recency component in (0, 1) so token-overlap always
# DOMINATES match_score (recency only ranks/breaks ties, never out-weighs overlap).
_RECENCY_SCALE = 10_000_000

# Bullet shape for LESSONS-LEARNED / DECISIONS: `- **L7 — title.** body`.
_BULLET_RE = re.compile(r"^- \*\*(?P<anchor>.+?)\*\*\s*(?P<body>.*)$", re.MULTILINE)
_HEADING_RE = re.compile(r"^#{1,6}\s+(?P<name>.+?)\s*$")
_LIST_RE = re.compile(r"^\s*[-*]\s+(?P<item>.+?)\s*$")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
# Synthesis-page title: the FIRST `# ` (h1) heading (SB-L5); fallback = file stem.
_H1_RE = re.compile(r"^#\s+(?P<name>.+?)\s*$", re.MULTILINE)
# Excerpt bound for synthesis pages — short, description-level (existing excerpt norms).
_EXCERPT_MAX = 240


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23) — mirrors validation_misses._guard_path
# ---------------------------------------------------------------------------

def _guard_path(raw: str | Path) -> Path:
    """Reject paths containing a ``..`` traversal component (CWE-23). Does NOT resolve.

    Only the ``..`` caller-bug raises here; other I/O failures are handled non-fatally
    by the readers (return ``""`` / ``[]``). Mirrors ``validation_misses._guard_path``.

    Raises:
        ValueError: if ``raw`` contains a ``..`` path component.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"recall: refusing path with '..' traversal: {raw!r}"
        )
    return p


# ---------------------------------------------------------------------------
# Tolerant text/date helpers (pure)
# ---------------------------------------------------------------------------

def _read_text(path: str | Path) -> str:
    """Read a file's text; ``..``-guarded, tolerant ('' on any I/O failure)."""
    p = _guard_path(path)
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""  # absent/unreadable ⇒ contributes nothing, never crashes


def _coerce_text(arg: str | Path | None) -> str:
    """Accept either inline text or a path; return the text (tolerant).

    A ``Path`` is read. A ``str`` containing a newline is treated as inline text;
    otherwise it is treated as a path if it exists, else as inline text. ``None`` ⇒ ''.
    """
    if arg is None:
        return ""
    if isinstance(arg, Path):
        return _read_text(arg)
    if isinstance(arg, str):
        if "\n" in arg:
            return arg
        try:
            p = _guard_path(arg)
            if p.exists():
                return _read_text(arg)
        except (ValueError, OSError):
            pass
        return arg
    return ""


def _exists(path: str | Path | None) -> bool:
    """True iff ``path`` names an existing file (tolerant — never raises)."""
    if path is None:
        return False
    try:
        return Path(str(path)).exists()
    except (OSError, ValueError, TypeError):
        return False


def _spath(path: str | Path | None) -> str | None:
    """The on-disk source path as a str (or None)."""
    return None if path is None else str(path)


def _infer_spath(src, source_path: str | None) -> str | None:
    """Infer the on-disk source path from a Path/path-like ``src`` when not given."""
    if source_path is not None:
        return source_path
    if isinstance(src, Path):
        return str(src)
    if isinstance(src, str) and "\n" not in src:
        try:
            if _guard_path(src).exists():
                return src
        except (ValueError, OSError):
            pass
    return None


def _tokenize(text: str) -> set[str]:
    """Case-insensitive token set (alphanumeric runs of length >= 2)."""
    return {t for t in _TOKEN_RE.findall(str(text).lower()) if len(t) >= 2}


def _slug(text: str) -> str:
    """Stable anchor slug for the record id (NOT line numbers — survives edits)."""
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return s or "item"


def _coerce_date_str(date) -> str | None:
    """Normalise a frontmatter date (str / datetime.date / None) to a str or None."""
    if date is None:
        return None
    if isinstance(date, str):
        return date.strip() or None
    return str(date)


def _parse_date(date_str: str | None):
    """Parse the leading ``YYYY-MM-DD`` of a date string; None if unparseable."""
    if not date_str or not isinstance(date_str, str):
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=UTC).date()
    except ValueError:
        return None


def _is_stale(date_str: str | None) -> bool:
    """A date-based HINT only (decision #4). Unknown/unparseable ⇒ not stale."""
    d = _parse_date(date_str)
    if d is None:
        return False
    return (datetime.now(UTC).date() - d).days > _STALE_DAYS


def _recency_component(date_str: str | None) -> float:
    """Recency boost in (0, 1) — monotonic in date, always < any 1-token overlap.

    More-recent records get a larger value; an unknown date contributes 0.0.
    """
    d = _parse_date(date_str)
    if d is None:
        return 0.0
    ordinal = d.toordinal()
    return ordinal / (ordinal + _RECENCY_SCALE)


def _record_date(record: dict, key: str = "date") -> str | None:
    """The record's date — top-level ``key`` if set, else ``provenance.date``."""
    if not isinstance(record, dict):
        return None
    if record.get(key):
        return record[key]
    prov = record.get("provenance")
    if isinstance(prov, dict):
        return prov.get("date")
    return None


def _date_sort_key(date_str: str | None) -> str:
    """Sortable key for recency ranking (newest first); unknown sorts last."""
    return date_str or ""


def _now_ts() -> str:
    """ISO8601 generation timestamp (UTC)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter (``--- ... ---``) from the body; tolerant ({}, text)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        import yaml  # noqa: PLC0415 — lazy; pure parse, no exec
        meta = yaml.safe_load(parts[1]) or {}
    except Exception:  # noqa: BLE001 — malformed frontmatter must never crash a read
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, parts[2]


# ---------------------------------------------------------------------------
# THE CONTRACT — recall_payload_schema() (single source of truth)
# ---------------------------------------------------------------------------

def recall_payload_schema() -> dict:
    """Return the Recall payload schema — the single source of truth (recall/v1).

    SHAPE-only: it lists the required keys + their types. It deliberately does NOT
    close a vocabulary for ``RecallRecord.source`` / ``provenance.backend`` /
    ``provenance.produced_by`` — those are OPEN, adapter-supplied strings (B1),
    marked ``"open": True`` and carrying NO ``"values"``/``"enum"`` set. Mirrors the
    single-source-of-truth *pattern* of ``validation_misses.miss_schema()`` while
    doing the OPPOSITE of its closed-enum enforcement for these three fields.
    """
    return {
        # Top-level version is the literal pinned string (the contract version).
        "schema_version": SCHEMA_VERSION,
        "query": {
            "type": "dict",
            "fields": {
                "terms": {"type": "list[str]", "description": "Query/goal/CONTEXT terms."},
                "kind": {
                    "type": "str",
                    "values": list(_QUERY_KINDS),
                    "description": "project | research | version-up (type-checked str).",
                },
            },
        },
        "records": {
            "type": "list[RecallRecord]",
            "record_fields": {
                "id": {"type": "str", "description": "Stable id = source_path + anchor/slug (NOT line numbers)."},
                # B1 — OPEN adapter-supplied label: type-checked str, NEVER enum-checked.
                "source": {"type": "str", "open": True, "description": "OPEN adapter label (files-only: lessons|decisions|prior-intent|understand-map)."},
                "source_path": {"type": "str", "description": "On-disk artifact path."},
                "title": {"type": "str", "description": "The surfaced item's anchor/name."},
                "excerpt": {"type": "str", "description": "Short description-level snippet (no code payloads)."},
                "tags": {"type": "list[str]", "description": "Matched tags/keywords."},
                "match_score": {"type": "float", "description": "Token-overlap + recency component."},
                "provenance": {
                    "type": "dict",
                    "fields": {
                        # B1 — OPEN adapter-supplied label.
                        "produced_by": {"type": "str", "open": True, "description": "OPEN adapter label (files-only: repo|kata-understand)."},
                        "date": {"type": "str|null", "description": "Source date, or null."},
                        "recency_rank": {"type": "int", "description": "Rank among passers (0 = newest)."},
                    },
                },
                "stale": {"type": "bool", "description": "Date-based HINT only — NEVER a filter."},
            },
        },
        "recurrences": {
            "type": "list[RecurrenceRecord]",
            "record_fields": {
                "key": {"type": "str"},
                "responsible_skill": {"type": "str"},
                "failure_class": {"type": "str"},
                "distinct_runs": {"type": "int"},
                "severity_tier": {"type": "str"},
                "off_vocabulary": {"type": "bool"},
                "open": {"type": "bool", "description": "Always True (the actionable/open subset)."},
            },
        },
        "provenance": {
            "type": "dict",
            "fields": {
                # B1 — OPEN adapter-supplied label (files-only default).
                "backend": {"type": "str", "open": True, "description": "OPEN adapter backend label (default 'files-only')."},
                "sources_read": {"type": "list[str]", "description": "Exactly the sources present on disk."},
                "generated_ts": {"type": "str", "description": "ISO8601 generation timestamp."},
            },
        },
    }


# ---------------------------------------------------------------------------
# Contract validator — SHAPE only (keys + types); vocabulary OPEN (B1)
# ---------------------------------------------------------------------------

def _is_str_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_record(rec: dict, i: int) -> list[str]:
    """Validate one RecallRecord — SHAPE only (keys + types). `source` stays OPEN."""
    errors: list[str] = []
    if not isinstance(rec, dict):
        return [f"records[{i}] must be a dict"]

    extra = set(rec.keys()) - _RECORD_ALL_FIELDS
    if extra:
        errors.append(f"records[{i}] extra keys not allowed: {sorted(extra)}")

    for field in ("id", "source_path", "title", "excerpt"):
        if not isinstance(rec.get(field), str):
            errors.append(f"records[{i}].{field} must be str")

    # B1: `source` is an OPEN adapter-supplied label — type-checked (str), NEVER
    # enum-checked. (Removing this line orphans the append → import error → the
    # external-adapter test goes red: it is the open-acceptance line for `source`.)
    if not isinstance(rec.get("source"), str):
        errors.append(f"records[{i}].source must be str (OPEN adapter label)")

    if not _is_str_list(rec.get("tags")):
        errors.append(f"records[{i}].tags must be list[str]")
    if not _is_number(rec.get("match_score")):
        errors.append(f"records[{i}].match_score must be a number")
    if not isinstance(rec.get("stale"), bool):
        errors.append(f"records[{i}].stale must be bool")

    prov = rec.get("provenance")
    if not isinstance(prov, dict):
        errors.append(f"records[{i}].provenance must be a dict")
    else:
        # B1: `produced_by` is an OPEN adapter-supplied label — type-checked str only.
        if not isinstance(prov.get("produced_by"), str):
            errors.append(f"records[{i}].provenance.produced_by must be str (OPEN label)")
        date = prov.get("date")
        if not (date is None or isinstance(date, str)):
            errors.append(f"records[{i}].provenance.date must be str or null")
        if not _is_int(prov.get("recency_rank")):
            errors.append(f"records[{i}].provenance.recency_rank must be int")
    return errors


def _validate_recurrence(rec: dict, i: int) -> list[str]:
    """Validate one RecurrenceRecord — EXACTLY the 7 fields (raw evidence rejected)."""
    errors: list[str] = []
    if not isinstance(rec, dict):
        return [f"recurrences[{i}] must be a dict"]

    extra = set(rec.keys()) - set(_RECURRENCE_FIELDS)
    if extra:
        errors.append(
            f"recurrences[{i}] extra keys (raw evidence must be projected out, N3): {sorted(extra)}"
        )
    missing = set(_RECURRENCE_FIELDS) - set(rec.keys())
    if missing:
        errors.append(f"recurrences[{i}] missing keys: {sorted(missing)}")

    for field in ("key", "responsible_skill", "failure_class", "severity_tier"):
        if not isinstance(rec.get(field), str):
            errors.append(f"recurrences[{i}].{field} must be str")
    if not _is_int(rec.get("distinct_runs")):
        errors.append(f"recurrences[{i}].distinct_runs must be int")
    if not isinstance(rec.get("off_vocabulary"), bool):
        errors.append(f"recurrences[{i}].off_vocabulary must be bool")
    if not isinstance(rec.get("open"), bool):
        errors.append(f"recurrences[{i}].open must be bool")
    return errors


def validate_payload(payload: dict) -> list[str]:
    """Validate a payload against ``recall_payload_schema()`` — SHAPE only.

    Returns a list of error strings ([] = valid). Enforces required keys + types
    and the EXACT RecurrenceRecord field set (so raw ``evidence`` is rejected, N3).
    Does NOT enforce a closed vocabulary for ``source`` / ``backend`` /
    ``produced_by`` (B1) — those are type-checked (str), never value-checked.
    """
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["payload must be a dict"]

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")

    query = payload.get("query")
    if not isinstance(query, dict):
        errors.append("query must be a dict")
    else:
        if not _is_str_list(query.get("terms")):
            errors.append("query.terms must be list[str]")
        if not isinstance(query.get("kind"), str):
            errors.append("query.kind must be str")

    records = payload.get("records")
    if not isinstance(records, list):
        errors.append("records must be a list")
    else:
        for i, rec in enumerate(records):
            errors.extend(_validate_record(rec, i))

    recurrences = payload.get("recurrences")
    if not isinstance(recurrences, list):
        errors.append("recurrences must be a list")
    else:
        for i, rec in enumerate(recurrences):
            errors.extend(_validate_recurrence(rec, i))

    prov = payload.get("provenance")
    if not isinstance(prov, dict):
        errors.append("provenance must be a dict")
    else:
        # B1: `backend` is an OPEN adapter-supplied label — type-checked str only.
        if not isinstance(prov.get("backend"), str):
            errors.append("provenance.backend must be str (OPEN adapter label)")
        if not _is_str_list(prov.get("sources_read")):
            errors.append("provenance.sources_read must be list[str]")
        if not isinstance(prov.get("generated_ts"), str):
            errors.append("provenance.generated_ts must be str")
    return errors


# ---------------------------------------------------------------------------
# Selection (N1) — token-overlap GATE; recency only RANKS the passers
# ---------------------------------------------------------------------------

def _record_tokens(record: dict) -> set[str]:
    """Tokens from a record's tags + title + excerpt (the selection surface)."""
    parts: list[str] = list(record.get("tags", []) or [])
    parts.append(str(record.get("title", "") or ""))
    parts.append(str(record.get("excerpt", "") or ""))
    return _tokenize(" ".join(str(p) for p in parts))


def token_overlap(record: dict, query_terms) -> set[str]:
    """The case-insensitive token-overlap set between the record and query terms.

    This is the N1 selection PREDICATE: a record passes ``select_records`` iff this
    set is non-empty. No embeddings / no RAG — plain token-set intersection.
    """
    q_tokens: set[str] = set()
    for term in query_terms or []:
        q_tokens |= _tokenize(str(term))
    return _record_tokens(record) & q_tokens


def match_score(record: dict, query_terms) -> float:
    """Token-overlap COUNT + a recency component (pure; no embeddings).

    The overlap count dominates; the recency component lives in (0, 1) so it only
    ranks/breaks ties among records that already share an overlap count.
    """
    overlap = len(token_overlap(record, query_terms))
    recency = _recency_component(_record_date(record, "date"))
    return float(overlap) + recency


def select_records(candidates, query_terms, *, recency_key: str = "date") -> list[dict]:
    """Select RecallRecords: GATE on token-overlap > 0, then recency RANKS passers.

    N1 (the load-bearing rule): a candidate with ZERO token overlap is EXCLUDED — no
    matter how recent (recency never promotes a non-match in). Recency only **ranks
    among the passers** (sets ``provenance.recency_rank`` and boosts ``match_score``)
    and **never filters a passer out**. A stale-but-overlapping record stays in.
    """
    passers: list[dict] = []
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        if not token_overlap(cand, query_terms):
            continue  # N1: zero token-overlap → EXCLUDED (recency cannot promote it in)
        passers.append(cand)

    # Recency RANKS among passers (newest first) — it never filters/promotes.
    passers.sort(key=lambda r: _date_sort_key(_record_date(r, recency_key)), reverse=True)
    for rank, cand in enumerate(passers):
        prov = cand.setdefault("provenance", {})
        prov["recency_rank"] = rank
        cand["match_score"] = match_score(cand, query_terms)

    # Final order: match_score desc (overlap dominates; recency breaks ties).
    passers.sort(key=lambda r: r["match_score"], reverse=True)
    return passers


# ---------------------------------------------------------------------------
# Files-only adapter — per-source parsers → candidate RecallRecords
# ---------------------------------------------------------------------------

def _make_record(*, source, source_path, title, excerpt, date, produced_by, extra_tag_text="") -> dict:
    """Build one candidate RecallRecord with provenance + date + tags + stale hint."""
    date_str = _coerce_date_str(date)
    tags = sorted(_tokenize(f"{title} {extra_tag_text}"))
    return {
        "id": f"{source_path or '<text>'}#{_slug(title)}",
        "source": source,
        "source_path": source_path or "<text>",
        "title": title,
        "excerpt": excerpt,
        "tags": tags,
        "match_score": 0.0,
        "provenance": {
            "produced_by": produced_by,
            "date": date_str,
            "recency_rank": 0,
        },
        "stale": _is_stale(date_str),
    }


def _parse_bullets(text: str, *, source: str, source_path: str | None, date, produced_by: str) -> list[dict]:
    """Parse ``- **anchor — title.** body`` bullets into candidate RecallRecords."""
    meta, _ = _parse_frontmatter(text)
    fm_date = date if date is not None else meta.get("date")
    records: list[dict] = []
    for m in _BULLET_RE.finditer(text):
        anchor = m.group("anchor").strip().rstrip(".").strip()
        excerpt = m.group("body").strip()
        if not anchor:
            continue
        records.append(_make_record(
            source=source, source_path=source_path, title=anchor, excerpt=excerpt,
            date=fm_date, produced_by=produced_by, extra_tag_text=f"{anchor} {excerpt}",
        ))
    return records


def parse_lessons(src, *, source_path: str | None = None, date=None) -> list[dict]:
    """Parse ``.planning/LESSONS-LEARNED.md`` bullets → RecallRecords (source='lessons')."""
    return _parse_bullets(
        _coerce_text(src), source="lessons", source_path=_infer_spath(src, source_path),
        date=date, produced_by="repo",
    )


def parse_decisions(src, *, source_path: str | None = None, date=None) -> list[dict]:
    """Parse ``.planning/DECISIONS.md`` bullets → RecallRecords (source='decisions')."""
    return _parse_bullets(
        _coerce_text(src), source="decisions", source_path=_infer_spath(src, source_path),
        date=date, produced_by="repo",
    )


def parse_intent(src, *, source_path: str | None = None, date=None) -> list[dict]:
    """Parse a prior ``INTENT.md`` frontmatter (goal/fixes/features/tags) → RecallRecords.

    READ-ONLY: parses a *prior* intent for recall context only. Recall never writes
    INTENT (source='prior-intent').
    """
    text = _coerce_text(src)
    source_path = _infer_spath(src, source_path)
    meta, _ = _parse_frontmatter(text)
    if not meta:
        return []
    fm_date = date if date is not None else meta.get("date")
    base_tags = meta.get("tags") or []
    tag_text = " ".join(str(t) for t in base_tags) if isinstance(base_tags, list) else str(base_tags)
    records: list[dict] = []

    goal = meta.get("goal")
    if isinstance(goal, str) and goal.strip():
        records.append(_make_record(
            source="prior-intent", source_path=source_path, title="goal",
            excerpt=goal.strip(), date=fm_date, produced_by="repo",
            extra_tag_text=f"{goal} {tag_text}",
        ))
    for field in ("fixes", "features"):
        vals = meta.get(field)
        if isinstance(vals, list):
            for item in vals:
                if isinstance(item, str) and item.strip():
                    records.append(_make_record(
                        source="prior-intent", source_path=source_path,
                        title=f"{field}: {item.strip()[:40]}", excerpt=item.strip(),
                        date=fm_date, produced_by="repo",
                        extra_tag_text=f"{item} {tag_text}",
                    ))
    return records


def parse_understand(src, *, source_path: str | None = None, date=None) -> list[dict]:
    """Parse ``.kata/understand.md`` sections (Changed/Added/Open questions) → RecallRecords.

    Each list item under a heading becomes a candidate (source='understand-map',
    produced_by='kata-understand').
    """
    text = _coerce_text(src)
    source_path = _infer_spath(src, source_path)
    meta, _ = _parse_frontmatter(text)
    fm_date = date if date is not None else meta.get("date")
    records: list[dict] = []
    current = "understand-map"
    for line in text.splitlines():
        h = _HEADING_RE.match(line)
        if h:
            current = h.group("name").strip()
            continue
        b = _LIST_RE.match(line)
        if b:
            item = b.group("item").strip()
            if not item:
                continue
            records.append(_make_record(
                source="understand-map", source_path=source_path,
                title=f"{current}: {item[:50]}", excerpt=item, date=fm_date,
                produced_by="kata-understand", extra_tag_text=f"{current} {item}",
            ))
    return records


def _first_paragraph(body: str) -> str:
    """The first non-heading body paragraph, bounded to ``_EXCERPT_MAX`` chars.

    Heading lines and leading blanks are skipped; the paragraph ends at the next
    blank line or heading. Pure text handling — no I/O.
    """
    para: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or _HEADING_RE.match(stripped):
            if para:
                break
            continue
        para.append(stripped)
    return " ".join(para)[:_EXCERPT_MAX]


def _parse_synthesis_page(page: Path) -> dict | None:
    """Parse ONE second-brain synthesis page → a RecallRecord, or None.

    Tolerant: ANY per-page failure (unreadable, undecodable, malformed) ⇒ ``None``
    — the page is skipped and the walk continues; never raises into the caller.
    ``produced_by`` = the frontmatter ``produced-by`` value (kept verbatim, e.g.
    'loop'); absent ⇒ 'unknown'. Title = first ``# `` heading, else the file stem.
    """
    try:
        text = page.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(text)
        raw_produced = meta.get("produced-by")
        produced_by = str(raw_produced) if raw_produced is not None else "unknown"
        m = _H1_RE.search(body)
        title = m.group("name").strip() if m else page.stem
        raw_tags = meta.get("tags") or []
        if isinstance(raw_tags, list):
            tag_text = " ".join(str(t) for t in raw_tags)
        else:
            tag_text = str(raw_tags)
        return _make_record(
            source="second-brain", source_path=str(page), title=title,
            excerpt=_first_paragraph(body), date=meta.get("date"),
            produced_by=produced_by, extra_tag_text=tag_text,
        )
    except Exception:  # noqa: BLE001 — a malformed page is skipped, never raises (SB-L5)
        return None


def parse_synthesis_pages(feed_dir) -> list[dict]:
    """Parse second-brain synthesis pages under ``feed_dir`` → RecallRecords (SB-L5).

    The optional, config-gated 7th recall source: a SORTED recursive walk
    (``sorted(rglob("*.md"))`` — Determinism Doctrine law 2) of the LEARN-feed dir.
    Each page yields one candidate with ``source="second-brain"`` and frontmatter
    provenance (``produced-by`` / ``date`` / ``tags``). READ-ONLY and tolerant:
    ``feed_dir=None`` or an absent/unreadable dir ⇒ ``[]``; a malformed page is
    skipped; a ``..`` component raises ``ValueError`` (CWE-23, ``_guard_path``).
    """
    if feed_dir is None:
        return []
    root = _guard_path(feed_dir)
    try:
        pages = sorted(root.rglob("*.md"))
    except OSError:
        return []  # unreadable feed dir ⇒ contributes nothing, never crashes
    records: list[dict] = []
    for page in pages:
        rec = _parse_synthesis_page(page)
        if rec is not None:
            records.append(rec)
    return records


# ---------------------------------------------------------------------------
# RecurrenceRecord projection (N3 — drop raw evidence)
# ---------------------------------------------------------------------------

def _recurrence_record(raw: dict) -> dict:
    """Project an ``actionable_recurrences`` cluster down to the 7 contract fields.

    N3: the raw ``evidence`` (full miss dicts incl. ``what_conformance_missed`` text),
    ``raw_count`` and ``threshold`` are PROJECTED OUT — never carried into the
    payload/brief. ``open`` is always True (the detector returns only the
    actionable/over-threshold-and-unhandled = open subset).
    """
    projected = {field: raw.get(field) for field in _RECURRENCE_FIELDS if field != "open"}
    projected["open"] = True
    return projected


# ---------------------------------------------------------------------------
# build_payload + the files-only default adapter entry point
# ---------------------------------------------------------------------------

def build_payload(query, records, recurrences, sources_read, *, backend: str = DEFAULT_BACKEND, generated_ts: str | None = None) -> dict:
    """Assemble a contract-shaped payload (validates against ``recall_payload_schema()``).

    ``query`` may be a ``{terms, kind}`` dict or a bare terms list. ``backend`` is an
    OPEN adapter-supplied label (default 'files-only'; an external adapter passes its
    own, e.g. 'obsidian', and the result still validates — B1).
    """
    if isinstance(query, dict):
        q = {"terms": list(query.get("terms", []) or []), "kind": query.get("kind")}
    else:
        q = {"terms": list(query or []), "kind": None}
    return {
        "schema_version": SCHEMA_VERSION,
        "query": q,
        "records": list(records or []),
        "recurrences": list(recurrences or []),
        "provenance": {
            "backend": backend,
            "sources_read": list(sources_read or []),
            "generated_ts": generated_ts or _now_ts(),
        },
    }


def recall_from_paths(
    *,
    lessons_path=None,
    decisions_path=None,
    intent_path=None,
    understand_path=None,
    misses_path=None,
    handled_path=None,
    query_terms,
    kind,
    generated_ts: str | None = None,
    feed_dir=None,
) -> dict:
    """The files-only default adapter — read six sources, return a contract payload.

    Tolerant reads of the six on-disk sources; selection (N1 overlap gate + recency
    rank) over the parsed records; ALWAYS surfaces open validation-miss recurrences
    via ``recurrence_detect.detect_from_paths`` (reused by name — no re-clustering),
    projected to RecurrenceRecords (N3). Pure: no exec, no write. Absent sources
    contribute ``[]`` and never crash; a ``..`` path raises ``ValueError`` (CWE-23).

    ``feed_dir`` (SB-L5) is the optional, config-gated 7th source: the second-brain
    LEARN-feed dir, read via ``parse_synthesis_pages`` into the SAME candidate pool
    BEFORE selection (the N1 gate + recency rank apply unchanged). ``feed_dir=None``
    (the default) ⇒ byte-identical behavior to the six-source form (BC1).
    """
    # CWE-23 — guard all supplied paths at the adapter boundary (.. ⇒ ValueError).
    for p in (lessons_path, decisions_path, intent_path, understand_path, misses_path, handled_path, feed_dir):
        if p is not None:
            _guard_path(p)

    candidate_records: list[dict] = []
    candidate_records.extend(parse_lessons(lessons_path, source_path=_spath(lessons_path)))
    candidate_records.extend(parse_decisions(decisions_path, source_path=_spath(decisions_path)))
    candidate_records.extend(parse_intent(intent_path, source_path=_spath(intent_path)))
    candidate_records.extend(parse_understand(understand_path, source_path=_spath(understand_path)))
    # SB-L5 — feed pages join the ORDINARY pool before selection (None ⇒ []).
    candidate_records.extend(parse_synthesis_pages(feed_dir))

    records = select_records(candidate_records, query_terms)

    # ALWAYS surface open recurrences (bypass selection). Reuse the BUILT detector.
    raw_recurrences: list[dict] = []
    if misses_path is not None:
        hp = handled_path if handled_path is not None else Path(str(misses_path)).parent / "recurrence-handled.jsonl"
        raw_recurrences = recurrence_detect.detect_from_paths(misses_path, hp)
    recurrences = [_recurrence_record(r) for r in raw_recurrences]

    # sources_read = exactly the sources present on disk (tolerant; incl. feed_dir).
    sources_read = [
        str(p)
        for p in (lessons_path, decisions_path, intent_path, understand_path, misses_path, handled_path, feed_dir)
        if p is not None and _exists(p)
    ]

    return build_payload(
        {"terms": list(query_terms or []), "kind": kind},
        records, recurrences, sources_read, generated_ts=generated_ts,
    )
