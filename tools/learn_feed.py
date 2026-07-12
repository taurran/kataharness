"""learn_feed.py — the second-brain LEARN-feed emitter (second-brain-loop SB-L1..SB-L4).

The **write-side** engine of the learn→store→recall loop: it parses grill decision
ledgers (and DECISIONS bullets), renders **one wiki-synthesis page per RESOLVED
entry** (the ``protocol/engram.md`` "Wiki-synthesis output schema", verbatim), and
emits the pages under the operator-supplied feed dir with an append-only session
log. Recall (``tools/recall.py``) is the read side; this module never reads the
feed back and never decides anything (zero CONSULT — the structural guarantee).

Grammar (SB-L1, freeze-gate F-1 — corpus-verified)
---------------------------------------------------
Heading entries ``### {anchor} — {title}`` where ``{anchor}`` is any ledger token
(``MM-1``, ``IP-A``, ``R-1``, ``GB1``, ``D7`` …) — a token carries a digit or a
dash segment, so prose headings ("Self-resolved defaults", "DECISION TREE") and
range headings ("R-14..R-21") are NOT entries. Status vocabulary on the heading
line: ``· LOCKED`` / ``· RESOLVED`` / ``— RESOLVED`` (case-insensitive), TOLERANT
of trailing text after the status token (``— RESOLVED 2026-07-04``,
``— RESOLVED core + …``). ``· open`` or NO status ⇒ open — parsed but NOT emitted
(only explicitly-resolved entries are decision-pattern signal); the caller counts
them as ``parsed_open_skipped``. Bullet-only ledgers parse to ZERO entries —
honest scope, surfaced by the CLI. Bold-field bullets under a heading are
tolerant (any subset of Question/Provenance/Options/Decision/Rationale/Edges).

Page contract (SB-L2 — engram.md wiki-synthesis schema, verbatim)
-----------------------------------------------------------------
Frontmatter ``produced-by: loop`` · ``source:`` (raw artifact path(s)) · ``date:``
(entry/ledger date when present, else the injected ``now``'s date) · ``scope:`` ·
sorted namespaced ``tags:`` (``kata/synthesis/decision-pattern`` +
``kata/decision-pattern/<coding|research|workflow>`` from the run kind) ·
``redactions: N`` only when N>0. Body: Question / Options considered / Decision /
Rationale / Edges sections (present fields only) with ``[[wikilinks]]`` to the
raw artifact. One page = one pattern. LF line endings.

Determinism (SB-L3 — Doctrine laws 2/3/5/6/7)
----------------------------------------------
Deterministic filename ``decision-patterns/<project-slug>--<anchor-slug>.md``
(project from the REQUIRED ``--project`` arg — no cwd inference, F-5); sorted
tags; pages processed in sorted relpath order; **injectable ``now``** — the wall
clock is minted ONLY in :func:`main` (law 7); idempotent emit — the identity
comparison **scrubs the ``date:`` frontmatter line** before comparing (law 6:
never byte-compare a wall-clock stamp), so identical-content-different-day ⇒
skip; changed content ⇒ overwrite. Zero-page emit appends NO log line (the log
records actual writes only — F-2). No randomness anywhere.

Overwrite guardrail (engram C5 carve-out)
------------------------------------------
Loop-emitted pages are REGENERABLE DERIVED VIEWS of the durable raw ledger, so
rewriting one loses nothing. Hand-curated pages stay protected: :func:`emit`
**refuses, fail-closed,** to overwrite any existing page whose frontmatter
``produced-by`` is not ``loop`` (missing/unparseable frontmatter included). The
refusal is checked for EVERY target in a pre-scan BEFORE anything is written
(all-or-nothing — no partial session behind a raised refusal).

Redaction (SB-L4 — G4/D151 operator-directed light touch)
----------------------------------------------------------
Deterministic pattern scrub (AWS ``AKIA[0-9A-Z]{16}``, ``github_pat_…``,
``-----BEGIN…PRIVATE KEY``, ``password/token/secret[:=]<value>`` classes) →
``[REDACTED:<class>]``, counted per page (frontmatter ``redactions: N``) and in
the emit report. Redaction NEVER blocks emit (the conscious re-scope of engram
C3's fail-closed gate for the loop feed — recorded in the DESIGN + D151).

Security posture (exec-safety.md)
---------------------------------
stdlib-only; no subprocess, no eval/exec, no shell. Writes land ONLY under the
two independently ``..``-guarded supplied paths — the feed dir and the named log
path (the log is NEVER derived from the feed dir, F-2); page relpaths are
``..``-guarded and must be relative. Reads are tolerant (mirrors
``recall._read_text``); the ``..`` caller-bug raises ``ValueError`` (CWE-23).

Public surfaces (cite-able by name per protocol/reuse-claims.md)
----------------------------------------------------------------
parse_grill_ledger      — heading-entry parser (anchor/status/date/fields/body)
parse_decisions_bullets — ``- **anchor — title.** body`` parser (recall family)
render_page             — one resolved entry → (relpath, page content)
redact                  — the SB-L4 deterministic scrub → (text, counts-by-class)
emit                    — atomic feed writes + session log → the emit report
main                    — the CLI shell (the ONLY place the wall clock is minted)
_guard_path             — ``..`` traversal guard (CWE-23; mirrors recall)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Contract constants (single source of truth)
# ---------------------------------------------------------------------------

# Run kind → decision-pattern tag leaf (SB-L2: project→coding, research→research,
# version-up/debug→workflow).
_KIND_TAG: dict[str, str] = {
    "project": "coding",
    "research": "research",
    "version-up": "workflow",
    "debug": "workflow",
}
_SCOPES: tuple[str, ...] = ("project", "universal")
_SYNTH_TAG = "kata/synthesis/decision-pattern"
_FEED_SUBDIR = "decision-patterns"

# Heading-entry grammar (SB-L1 / F-1). An anchor TOKEN carries a digit or a dash
# segment (MM-1, IP-A, R-1, GB1, D7, D151) — prose headings and ranges
# ("R-14..R-21": '.' fails the boundary lookahead) are not entries.
_HEADING_LINE_RE = re.compile(r"^#{1,6}\s+(?P<rest>.+?)\s*$")
_ANCHOR_RE = re.compile(
    r"^(?P<anchor>[A-Z]+(?:-[A-Za-z0-9]+)+|[A-Z]+[0-9][A-Za-z0-9]*)(?=[\s(·—:]|$)"
)
# Status vocabulary: `· LOCKED` / `· RESOLVED` / `— RESOLVED` (case-insensitive),
# tolerant of trailing text after the token; `· open` is the explicit open marker.
_STATUS_RE = re.compile(r"[·—]\s*(?P<status>locked|resolved|open)\b", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

# Bullet shape for DECISIONS: `- **D1 — title.** body` (recall._BULLET_RE family).
_BULLET_RE = re.compile(r"^- \*\*(?P<anchor>.+?)\*\*\s*(?P<body>.*)$", re.MULTILINE)
# Bold-field bullets under a heading entry: `- **Question:** …`.
_FIELD_RE = re.compile(r"^\s*-\s+\*\*(?P<name>[^:*]+):\*\*\s*(?P<value>.*)$")
_PLAIN_BULLET_RE = re.compile(r"^\s*[-*]\s+")
_FM_LINE_RE = re.compile(r"^(?P<key>[A-Za-z][\w-]*):\s*(?P<value>.*)$")
_DATE_LINE_RE = re.compile(r"^date:.*$", re.MULTILINE)

# Tolerant bold-field names → canonical field keys (prefix match, lowercased):
# "Options considered" → options, "Edges/scenarios" → edges. Any subset accepted;
# unknown names (e.g. "Doc-baked") fall through to the entry body.
_FIELD_PREFIXES: tuple[tuple[str, str], ...] = (
    ("question", "question"),
    ("provenance", "provenance"),
    ("options", "options"),
    ("decision", "decision"),
    ("rationale", "rationale"),
    ("edges", "edges"),
)
# Rendered sections (SB-L2 order): Provenance is parsed/tolerated but NOT a section.
_SECTION_ORDER: tuple[str, ...] = ("question", "options", "decision", "rationale", "edges")
_SECTION_TITLES: dict[str, str] = {
    "question": "Question",
    "options": "Options considered",
    "decision": "Decision",
    "rationale": "Rationale",
    "edges": "Edges",
}

# SB-L4 redaction classes — fixed apply order, bounded patterns (linear scan; no
# nested/chained quantifiers — ReDoS-safe by construction).
_REDACTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github-pat", re.compile(r"github_pat_[A-Za-z0-9_]+")),
    ("private-key", re.compile(r"-----BEGIN[A-Z ]{0,40}PRIVATE KEY-----")),
    ("password", re.compile(r"\bpassword\s*[:=]\s*\S+", re.IGNORECASE)),
    ("token", re.compile(r"\btoken\s*[:=]\s*\S+", re.IGNORECASE)),
    ("secret", re.compile(r"\bsecret\s*[:=]\s*\S+", re.IGNORECASE)),
)


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23) — mirrors recall._guard_path
# ---------------------------------------------------------------------------

def _guard_path(raw: str | Path) -> Path:
    """Reject paths containing a ``..`` traversal component (CWE-23). Does NOT resolve.

    Only the ``..`` caller-bug raises here; other I/O failures are handled
    non-fatally by the readers. Mirrors ``recall._guard_path``.

    Raises:
        ValueError: if ``raw`` contains a ``..`` path component.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"learn-feed: refusing path with '..' traversal: {raw!r}")
    return p


# ---------------------------------------------------------------------------
# Tolerant text helpers (pure)
# ---------------------------------------------------------------------------

def _read_text(path: str | Path) -> str:
    """Read a file's text; ``..``-guarded, tolerant ('' on any I/O failure)."""
    p = _guard_path(path)
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""  # absent/unreadable ⇒ contributes nothing, never crashes


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split simple ``key: value`` YAML frontmatter from the body — stdlib-only.

    Tolerant: no frontmatter / malformed ⇒ ``({}, text)``. Only flat scalar lines
    are read (all this module needs: ``produced-by`` / ``date`` / ``redactions``).
    """
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        m = _FM_LINE_RE.match(line)
        if m:
            meta[m.group("key")] = m.group("value").strip()
    return meta, parts[2]


def _first_date(value: object) -> str | None:
    """The first ``YYYY-MM-DD`` in ``value``, or None."""
    if not value:
        return None
    m = _DATE_RE.search(str(value))
    return m.group(1) if m else None


def _slug(text: str) -> str:
    """Stable slug for filenames (mirrors recall._slug — survives edits)."""
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return s or "item"


def _field_key(name: str) -> str | None:
    """Map a tolerant bold-field name to its canonical key (None = not a field)."""
    normalized = name.strip().lower()
    for prefix, key in _FIELD_PREFIXES:
        if normalized.startswith(prefix):
            return key
    return None


# ---------------------------------------------------------------------------
# SB-L1 — parsers
# ---------------------------------------------------------------------------

def _parse_heading_entry(rest: str, fm_date: str | None) -> dict | None:
    """Parse one heading's text into an entry skeleton (None = not a ledger entry)."""
    a = _ANCHOR_RE.match(rest)
    if not a:
        return None
    tail = rest[a.end():]
    s = _STATUS_RE.search(tail)
    if s:
        status = "resolved" if s.group("status").lower() in ("locked", "resolved") else "open"
        title_part = tail[: s.start()]
    else:
        status = "open"  # explicit policy: no status ⇒ open, NOT emitted
        title_part = tail
    title = title_part.strip().strip("·—-").strip()
    return {
        "anchor": a.group("anchor"),
        "title": title,
        "status": status,
        # entry date = first date on the heading line (e.g. `— RESOLVED 2026-07-04`),
        # else the ledger frontmatter date, else None (render falls back to `now`).
        "date": _first_date(tail) or fm_date,
        "fields": {},
        "body": "",
    }


def parse_grill_ledger(text: str | None) -> list[dict]:
    """Parse a grill decision ledger's heading entries (SB-L1 grammar).

    Returns ALL parsed entries — resolved AND open — as dicts
    ``{anchor, title, status, date, fields, body}``; the caller filters
    ``status == "resolved"`` for emission and counts the rest as
    ``parsed_open_skipped``. Bullet-only ledgers ⇒ ``[]`` (honest scope). Pure.
    """
    lines = (text or "").splitlines()
    meta, _ = _parse_frontmatter(text or "")
    fm_date = _first_date(meta.get("date"))

    entries: list[dict] = []
    current: dict | None = None
    body: list[str] = []
    fields: dict[str, str] = {}
    active_field: str | None = None

    def _flush() -> None:
        nonlocal current, body, fields, active_field
        if current is not None:
            current["fields"] = dict(fields)
            current["body"] = "\n".join(ln.rstrip() for ln in body).strip()
            entries.append(current)
        current, body, fields, active_field = None, [], {}, None

    for line in lines:
        h = _HEADING_LINE_RE.match(line)
        if h:
            _flush()
            current = _parse_heading_entry(h.group("rest"), fm_date)
            continue
        if current is None:
            continue  # content under a non-entry heading is ignored
        f = _FIELD_RE.match(line)
        if f:
            key = _field_key(f.group("name"))
            if key:
                active_field = key
                fields[key] = f.group("value").strip()
            else:
                active_field = None  # unknown bold field (e.g. Doc-baked) → body
                body.append(line)
            continue
        if _PLAIN_BULLET_RE.match(line):
            active_field = None
            body.append(line)
            continue
        if not line.strip():
            active_field = None
            body.append(line)
            continue
        if active_field:  # wrapped continuation of the current bold field
            fields[active_field] = f"{fields[active_field]} {line.strip()}".strip()
        else:
            body.append(line)
    _flush()
    return entries


def parse_decisions_bullets(text: str | None) -> list[dict]:
    """Parse ``- **anchor — title.** body`` bullets (recall's ``_BULLET_RE`` family).

    Every DECISIONS bullet is a decided decision ⇒ ``status="resolved"`` (the F-10
    backfill path — volume accepted, not capped). Entry date = the file's
    frontmatter ``date:`` (never mined from bullet prose). Pure.
    """
    src = text or ""
    meta, _ = _parse_frontmatter(src)
    fm_date = _first_date(meta.get("date"))
    entries: list[dict] = []
    for m in _BULLET_RE.finditer(src):
        raw = m.group("anchor").strip().rstrip(".").strip()
        if not raw:
            continue
        anchor, dash, title = raw.partition("—")
        anchor = anchor.strip()
        title = title.strip() if dash else ""
        if not anchor:
            anchor, title = raw, ""
        entries.append({
            "anchor": anchor,
            "title": title or raw,
            "status": "resolved",
            "date": fm_date,
            "fields": {},
            "body": m.group("body").strip(),
        })
    return entries


# ---------------------------------------------------------------------------
# SB-L4 — redaction (deterministic scrub; never blocks)
# ---------------------------------------------------------------------------

def redact(text: str) -> tuple[str, dict[str, int]]:
    """Scrub secret-pattern matches → ``[REDACTED:<class>]`` (SB-L4, G4/D151).

    Deterministic: fixed class order, plain ``re.subn``. Returns the scrubbed
    text + counts per class ({} when clean). NEVER raises / NEVER blocks emit.
    """
    counts: dict[str, int] = {}
    for cls, pattern in _REDACTION_PATTERNS:
        text, n = pattern.subn(f"[REDACTED:{cls}]", text)
        if n:
            counts[cls] = counts.get(cls, 0) + n
    return text, counts


# ---------------------------------------------------------------------------
# SB-L2 / SB-L3 — render_page
# ---------------------------------------------------------------------------

def render_page(
    entry: dict,
    *,
    project: str,
    source_path: str | Path | list,
    scope: str,
    kind: str,
    now: datetime,
) -> tuple[str, str]:
    """Render ONE resolved entry into a wiki-synthesis page (SB-L2, verbatim).

    Pure — no I/O, no clock (``now`` is injected; used only when the entry
    carries no date). Hard-fails (``ValueError``) on unusable INPUT to this
    decision code: unknown ``kind``/``scope``, empty ``project``, missing anchor —
    never a silent permissive default.

    Returns:
        ``(relpath, content)`` — relpath is the deterministic
        ``decision-patterns/<project-slug>--<anchor-slug>.md`` (SB-L3); content
        is the full page, LF-only, frontmatter ``redactions: N`` present only
        when the SB-L4 scrub hit (redaction marks, never blocks).
    """
    if kind not in _KIND_TAG:
        raise ValueError(f"learn-feed: unknown kind {kind!r} (expected one of {sorted(_KIND_TAG)})")
    if scope not in _SCOPES:
        raise ValueError(f"learn-feed: unknown scope {scope!r} (expected one of {list(_SCOPES)})")
    if not str(project or "").strip():
        raise ValueError("learn-feed: --project is required (F-5 — no cwd inference)")
    anchor = str(entry.get("anchor") or "").strip()
    if not anchor:
        raise ValueError("learn-feed: entry has no anchor")

    if isinstance(source_path, (str, Path)):
        sources = [str(source_path)]
    else:
        sources = sorted(str(s) for s in source_path)
    sources = [s.replace("\\", "/") for s in sources]
    if not sources:
        raise ValueError("learn-feed: source_path is required")

    title = str(entry.get("title") or "").strip()
    fields = entry.get("fields") or {}
    body_text = str(entry.get("body") or "").strip()

    # --- body (one page = one pattern; wikilinks to the raw artifact) ---
    lines: list[str] = [f"# {anchor} — {title}" if title else f"# {anchor}", ""]
    lines += ["**Source:** " + " · ".join(f"[[{s}]]" for s in sources), ""]
    present = [k for k in _SECTION_ORDER if str(fields.get(k) or "").strip()]
    if present:
        for k in present:
            lines += [f"## {_SECTION_TITLES[k]}", "", str(fields[k]).strip(), ""]
    elif body_text:
        # Field-less ledgers (e.g. the MM `· LOCKED` form): the entry body IS the
        # recorded resolution — rendered under the canonical Decision section.
        lines += ["## Decision", "", body_text, ""]
    body = "\n".join(lines).rstrip("\n") + "\n"
    body, red_counts = redact(body)
    n_redactions = sum(red_counts.values())

    date_str = entry.get("date") or now.date().isoformat()
    tags = sorted((_SYNTH_TAG, f"kata/decision-pattern/{_KIND_TAG[kind]}"))

    fm: list[str] = ["---", "produced-by: loop"]
    if len(sources) == 1:
        fm.append(f"source: {sources[0]}")
    else:
        fm.append("source:")
        fm += [f"  - {s}" for s in sources]
    fm += [f"date: {date_str}", f"scope: {scope}", "tags:"]
    fm += [f"  - {t}" for t in tags]
    if n_redactions > 0:
        fm.append(f"redactions: {n_redactions}")
    fm.append("---")

    relpath = f"{_FEED_SUBDIR}/{_slug(project)}--{_slug(anchor)}.md"
    return relpath, "\n".join(fm) + "\n\n" + body


# ---------------------------------------------------------------------------
# SB-L3 — emit (atomic writes; date-scrubbed idempotency; fail-closed guardrail)
# ---------------------------------------------------------------------------

def _scrub_date_line(text: str) -> str:
    """Neutralize the frontmatter ``date:`` line for identity comparison (law 6)."""
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    return "---".join((parts[0], _DATE_LINE_RE.sub("date: <scrubbed>", parts[1]), parts[2]))


def _page_redaction_count(content: str) -> int:
    """The page's frontmatter ``redactions:`` count (0 when absent/unparseable)."""
    meta, _ = _parse_frontmatter(content)
    try:
        return int(meta.get("redactions", 0) or 0)
    except (TypeError, ValueError):
        return 0


def emit(
    feed_dir: str | Path,
    pages: list[tuple[str, str]],
    *,
    log_path: str | Path,
    now: datetime,
    parsed_open_skipped: int = 0,
) -> dict:
    """Write rendered pages under ``feed_dir`` + append ONE session log line.

    Writes land ONLY under the two independently ``..``-guarded supplied paths
    (the log path is guarded AS SUPPLIED, never derived from the feed dir — F-2).
    Per-page writes are atomic temp+rename (the ``write_bridge`` convention).
    Identity comparison scrubs the ``date:`` frontmatter line first (law 6), so
    identical-otherwise ⇒ ``skipped_identical``. A pre-scan REFUSES, fail-closed
    and all-or-nothing, when ANY target page's frontmatter ``produced-by`` is not
    ``loop`` (missing/unreadable frontmatter included) — hand-curated pages are
    never touched (engram C5 carve-out). The log line is appended ONLY when
    ``written > 0`` (zero-page emit = no log line).

    Args:
        feed_dir: the LEARN-feed root (``engram.learnFeed.dir``).
        pages: ``(relpath, content)`` tuples from :func:`render_page`.
        log_path: the wiki log file to append the session line to.
        now: injected clock — stamps the log line only (law 7).
        parsed_open_skipped: parse-stage count of open/no-status entries, carried
            into the report + log line by the caller.

    Returns:
        ``{written, skipped_identical, redactions, parsed_open_skipped}``.

    Raises:
        ValueError: ``..`` in either supplied path or any page relpath (CWE-23);
            absolute page relpath; produced-by refusal (fail-closed).
    """
    feed_root = _guard_path(feed_dir)
    log_p = _guard_path(log_path)  # independent guard — NEVER derived from feed_root

    ordered = sorted(pages, key=lambda p: str(p[0]))  # law 2/3: sorted at the boundary
    for relpath, _content in ordered:
        rp = Path(str(relpath))
        if rp.is_absolute() or any(part == ".." for part in rp.parts):
            raise ValueError(f"learn-feed: refusing page relpath {relpath!r}")

    # Fail-closed pre-scan (all-or-nothing): never touch a non-loop page, and
    # never write ANY page of a session that contains a refusal.
    existing_texts: dict[str, str] = {}
    for relpath, _content in ordered:
        target = feed_root / str(relpath)
        if not target.exists():
            continue
        try:
            existing = target.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(
                f"learn-feed: cannot verify produced-by of {target} (fail-closed): {exc}"
            ) from exc
        meta, _ = _parse_frontmatter(existing)
        if meta.get("produced-by") != "loop":
            raise ValueError(
                f"learn-feed: refusing to overwrite non-loop page {target} "
                f"(produced-by={meta.get('produced-by')!r}; hand-curated pages are never touched)"
            )
        existing_texts[str(relpath)] = existing

    written = 0
    skipped_identical = 0
    redactions = 0
    for relpath, content in ordered:
        redactions += _page_redaction_count(content)
        existing = existing_texts.get(str(relpath))
        if existing is not None and _scrub_date_line(existing) == _scrub_date_line(content):
            skipped_identical += 1
            continue
        target = feed_root / str(relpath)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Atomic temp+rename (write_bridge convention): sibling temp in the SAME
        # directory, then os.replace — a reader never sees a partial page.
        fd, tmp_name = tempfile.mkstemp(
            dir=str(target.parent), prefix=".learn-feed-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
            os.replace(tmp_name, target)
        except OSError:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        written += 1

    if written > 0:  # F-2: the log records actual writes only
        log_p.parent.mkdir(parents=True, exist_ok=True)
        line = (
            f"- {now.date().isoformat()} learn-feed emit: written={written} "
            f"skipped_identical={skipped_identical} redactions={redactions} "
            f"parsed_open_skipped={parsed_open_skipped}\n"
        )
        with open(log_p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line)

    return {
        "written": written,
        "skipped_identical": skipped_identical,
        "redactions": redactions,
        "parsed_open_skipped": parsed_open_skipped,
    }


# ---------------------------------------------------------------------------
# CLI shell — the ONLY place the wall clock is minted (law 7)
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="learn_feed.py",
        description=(
            "Emit second-brain wiki-synthesis pages from grill decision ledgers "
            "(second-brain-loop SB-L1..SB-L4). JSON report to stdout with --json; "
            "human summary to stderr."
        ),
    )
    p.add_argument("--ledger", action="append", default=[], metavar="PATH",
                   help="a GRILL-LEDGER.md (repeatable)")
    p.add_argument("--decisions", default=None, metavar="PATH",
                   help="a DECISIONS.md bullet file (F-10 backfill)")
    p.add_argument("--feed-dir", required=True, help="the LEARN-feed root dir")
    p.add_argument("--log-path", required=True,
                   help="the wiki log file (independent of --feed-dir)")
    p.add_argument("--project", required=True,
                   help="target repo/project slug (REQUIRED — F-5, no cwd inference)")
    p.add_argument("--kind", required=True, choices=sorted(_KIND_TAG),
                   help="run kind (maps to the decision-pattern tag)")
    p.add_argument("--scope", default="project", choices=list(_SCOPES))
    p.add_argument("--json", action="store_true",
                   help="print the emit report as JSON (sort_keys) on stdout")
    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success, 2 on a guard/refusal error."""
    args = _build_parser().parse_args(argv)
    if not args.ledger and not args.decisions:
        _build_parser().error("at least one of --ledger/--decisions is required")
    now = datetime.now(UTC)  # the ONLY wall-clock mint (Doctrine law 7)

    try:
        pages: dict[str, tuple[str, str]] = {}
        parsed_open_skipped = 0
        notes: list[str] = []
        for ledger in args.ledger:
            entries = parse_grill_ledger(_read_text(ledger))
            parsed_open_skipped += sum(1 for e in entries if e["status"] != "resolved")
            if not entries:
                notes.append(f"{ledger}: 0 heading entries (bullet-only or empty ledger)")
            for e in entries:
                if e["status"] != "resolved":
                    continue  # open/no-status entries are NOT decision-pattern signal
                relpath, content = render_page(
                    e, project=args.project, source_path=str(ledger),
                    scope=args.scope, kind=args.kind, now=now,
                )
                pages[relpath] = (relpath, content)
        if args.decisions:
            for e in parse_decisions_bullets(_read_text(args.decisions)):
                relpath, content = render_page(
                    e, project=args.project, source_path=str(args.decisions),
                    scope=args.scope, kind=args.kind, now=now,
                )
                pages[relpath] = (relpath, content)
        report = emit(
            args.feed_dir, [pages[k] for k in sorted(pages)],
            log_path=args.log_path, now=now, parsed_open_skipped=parsed_open_skipped,
        )
    except ValueError as exc:
        print(f"learn-feed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, sort_keys=True))
    print(
        "learn-feed: written={written} skipped_identical={skipped_identical} "
        "redactions={redactions} parsed_open_skipped={parsed_open_skipped}".format(**report),
        file=sys.stderr,
    )
    for note in notes:
        print(f"learn-feed: note: {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
