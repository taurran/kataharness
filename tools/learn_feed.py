"""learn_feed.py — the second-brain LEARN-feed emitter (second-brain-loop SB-L1..SB-L4).

The **write-side** engine of the learn→store→recall loop: it parses grill decision
ledgers (and DECISIONS bullets), renders **one wiki-synthesis page per RESOLVED
entry** (the ``protocol/engram.md`` "Wiki-synthesis output schema", verbatim), and
emits the pages under the operator-supplied feed dir with an append-only session
log. Recall (``tools/recall.py``) is the read side; this module never reads the
feed back and never decides anything (zero CONSULT — the structural guarantee).

Grammar (SB-L1, freeze-gate F-1 — corpus-verified)
---------------------------------------------------
**Heading entries** ``### {anchor} — {title}`` (H2..H6 — never H1, so a ledger's own
``# GRILL-LEDGER — <spec>`` title is not miscounted as an open entry; LFB-2/BL-M24)
where ``{anchor}`` is any ledger token
(``MM-1``, ``IP-A``, ``R-1``, ``GB1``, ``D7`` …) — a token carries a digit or a
dash segment, so prose headings ("Self-resolved defaults", "DECISION TREE") and
range headings ("R-14..R-21") are NOT entries. Status vocabulary on the heading
line: ``· LOCKED`` / ``· RESOLVED`` / ``— RESOLVED`` (case-insensitive), TOLERANT
of trailing text after the status token (``— RESOLVED 2026-07-04``,
``— RESOLVED core + …``). ``· open`` or NO status ⇒ open — parsed but NOT emitted
(only explicitly-resolved entries are decision-pattern signal); the caller counts
them as ``parsed_open_skipped``. Bold-field bullets under a heading are
tolerant (any subset of Question/Provenance/Options/Decision/Rationale/Edges).

**Bullet entries** (BL-X12 (a)/(b)/(d) — the 2026-08 house style):
``- **{anchor} · {title}.** body …`` at TOP level, harvested ONLY from regions no
heading entry owns (a heading entry's own bullets remain its fields/body — the
heading grammar above is untouched). The bold anchor span may WRAP across
physical lines (``.planning/specs/ux-rework`` UX-28/UX-32 wrap; the single-line
regex dropped them silently). The anchor is the first ``·``/``—``-separated
segment's leading anchor token, so the stable short key (``UX-28``, ``AC-11``,
``BBM-12``) is what namespaces the page — never the whole title.

**Bullet-entry status is FAIL-CLOSED TO OPEN** (BL-X12 (c), D136): resolved ONLY
when the title or the entry's lead line carries a provable decided marker
(:data:`_BULLET_DECIDED_RE` — ``LOCKED`` / ``RULED`` / ``RULING(S)`` /
``RESOLVED``, derived from the real ux-rework · backlog-burn-mode · agent-cadre
ledgers), and NEVER when it carries an explicit open marker
(:data:`_BULLET_OPEN_RE` — ``OPEN QUESTION``), which WINS over any decided marker.
Anything unclassifiable is open. Two deliberate narrowings, both erring open:
bare ``ACCEPTED`` is NOT decided vocabulary here (the real context-autonomy
``R-5 … — ACCEPTED`` means *the assessment was accepted, the work is still owed*
— already pinned open by the heading grammar; promoting it in the bullet grammar
would emit an undecided branch as a ruling), and an entry that merely MENTIONS an
open question — UX-28's *"closes the UX-5 open question"* — parses open even
though it is a ruling. Losing signal is recoverable; emitting an undecided branch
into the vault as a decision is the harm this parser exists to refuse.

Page contract (SB-L2 — engram.md wiki-synthesis schema, verbatim)
-----------------------------------------------------------------
Frontmatter ``produced-by: loop`` · ``source:`` (raw artifact path(s)) · ``date:``
(entry/ledger date when present, else the injected ``now``'s date) · ``scope:`` ·
sorted namespaced ``tags:`` (``kata/synthesis/decision-pattern`` +
``kata/decision-pattern/<coding|research|workflow>`` from the run kind) ·
``redactions: N`` only when N>0. Body: Question / Options considered / Decision /
Rationale / Edges sections (present fields only), then the entry's remaining prose
under ``## Detail`` — the body is rendered **in addition to** the fields, never
instead of them (LFB-1; the ``elif`` that dropped it was DEF-2). When NO field
parses, that same body renders under ``## Decision`` (the field-less MM
``· LOCKED`` form). ``[[wikilinks]]`` to the raw artifact. One page = one pattern.
LF line endings.

Determinism (SB-L3 — Doctrine laws 2/3/5/6/7)
----------------------------------------------
Deterministic filename
``decision-patterns/<project-slug>--<source-slug>--<anchor-slug>.md`` (project
from the REQUIRED ``--project`` arg — no cwd inference, F-5). The **source-slug**
namespaces the page by its originating artifact so anchors that restart per
source do not collide: for a ``--ledger`` file it is the ledger's PARENT
directory name when that parent is not the shared ``.planning`` root
(``.planning/specs/statusline-decouple/GRILL-LEDGER.md`` → ``statusline-decouple``),
else the file stem; for ``--decisions`` it is the literal ``decisions``. Every
segment is lowercased + filesystem-safe (:func:`_slug`). *Naming-contract note:*
pages emitted under the earlier un-namespaced ``<project>--<anchor>.md`` scheme
become ORPHANS the emitter never touches again (the produced-by guardrail is
unchanged; idempotency is per-filename, so re-emits under the new scheme write
fresh pages beside — not over — the orphans). Sorted
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
``-----BEGIN…PRIVATE KEY``, ``password/token/secret[:=]<value>`` classes, plus the
RS-M7 extension: vendor key shapes, JWTs, credentialed connection strings, ``Bearer``
values and the generic ``api_key``/``client_secret``/``access_key`` labels) →
``[REDACTED:<class>]``, counted per page (frontmatter ``redactions: N``) and in
the emit report. Redaction NEVER blocks emit HERE (the conscious re-scope of engram
C3's fail-closed gate for the loop feed — recorded in the DESIGN + D151).

``redact`` is also **THE one scrub** the trust-model close reaches from its two named
points (``kata_close.redact_at_commit_act`` / ``redact_at_snapshot_edge``, RS-M7). The
blocking posture is the CALLER's, not this function's: the learn feed never blocks, and
the commit act fails closed on any detected class. One table, two policies — and the
table is the only place a class is ever defined.

Security posture (exec-safety.md)
---------------------------------
stdlib-only; no subprocess, no eval/exec, no shell. Writes land ONLY under the
two independently ``..``-guarded supplied paths — the feed dir and the named log
path (the log is NEVER derived from the feed dir, F-2); page relpaths are
``..``-guarded and must be relative. Reads are tolerant (mirrors
``recall._read_text``); the ``..`` caller-bug raises ``ValueError`` (CWE-23).

Route guard (BL-X12 (c) — D136 fail-closed, never a silent misclassification)
------------------------------------------------------------------------------
:func:`grill_ledger_marker` names why a file is a GRILL LEDGER (a ``spec:``
frontmatter key, or a ``GRILL-LEDGER`` filename). :func:`main` REFUSES such a
file on the ``--decisions`` route — exit 2 with the ``--ledger`` route named in
the message — because ``parse_decisions_bullets`` marks every bullet resolved by
DECISIONS.md's own contract, which is exactly right there and would emit a
ledger's OPEN questions into the vault as decided rulings. The guard lives at the
ROUTE layer; the pure parser keeps its contract and its hardcoded status.

Public surfaces (cite-able by name per protocol/reuse-claims.md)
----------------------------------------------------------------
parse_grill_ledger      — ledger parser: heading entries + fail-closed bullet entries
parse_decisions_bullets — ``- **anchor — title.** body`` parser (recall family)
grill_ledger_marker     — "is this a grill ledger?" reason string (route guard)
_source_slug            — source-artifact → filename namespace slug (collision guard)
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
from pathlib import Path, PurePosixPath

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
#
# H2..H6 ONLY (BL-M24 / LFB-2). Every ledger's own H1 title is `# GRILL-LEDGER —
# <spec>`, and the literal `GRILL-LEDGER` matches _ANCHOR_RE, so an `^#{1,6}`
# grammar parsed the document title itself as a status-less (⇒ open) entry — the
# phantom `parsed_open_skipped=1` every emit has reported forever. Ledger entries
# are `###` by house style; no real entry is ever an H1.
_HEADING_LINE_RE = re.compile(r"^#{2,6}\s+(?P<rest>.+?)\s*$")
# Record TERMINATOR for parse_decisions_bullets — a different job from the entry
# grammar above, so it deliberately still matches H1..H6: a `# Heading` in a
# DECISIONS file ends the open record rather than being vacuumed into its body.
# (Narrowing this one too would have been a silent behavior change to an
# unrelated parser.)
_RECORD_END_HEADING_RE = re.compile(r"^#{1,6}\s+.+?\s*$")
_ANCHOR_RE = re.compile(
    r"^(?P<anchor>[A-Z]+(?:-[A-Za-z0-9]+)+|[A-Z]+[0-9][A-Za-z0-9]*)(?=[\s(·—:]|$)"
)
# Status vocabulary: `· LOCKED` / `· RESOLVED` / `— RESOLVED` (case-insensitive),
# tolerant of trailing text after the token; `· open` is the explicit open marker.
_STATUS_RE = re.compile(r"[·—]\s*(?P<status>locked|resolved|open)\b", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

# Record OPENER for DECISIONS: `- **D1 — title.** body` (recall._BULLET_RE family).
# It matches the START of a top-level record and does NOT require the closing `**`
# on the same physical line — the wrap is handled by :class:`_BoldSpan` below.
# The `- ` literal prefix is the prior `_BULLET_RE`'s verbatim (deliberately NOT
# the ledger opener's tolerant `-\s+`): this route's record-start contract is
# unchanged, only its ability to see past a line break is added.
_DECISIONS_BULLET_OPEN_RE = re.compile(r"^- \*\*(?P<rest>.*)$")

# --- Bullet ENTRIES in a grill ledger (BL-X12) ------------------------------
# A TOP-LEVEL `- **…**` bullet only (leading whitespace ⇒ a sub-bullet of the
# record above, never an entry of its own). The opening line is matched alone so
# the bold span can be accumulated across physical lines: the 2026-08 house style
# wraps long anchor spans, and a single-line regex drops those entries SILENTLY
# (UX-28 + UX-32, 2 of 33 in the real ux-rework ledger).
_LEDGER_BULLET_OPEN_RE = re.compile(r"^-\s+\*\*(?P<rest>.*)$")
# Bound the wrap search: an unterminated `**` is malformed markdown, not an entry.
_MAX_BOLD_SPAN_LINES = 10
# Anchor partition inside the bold span. The 2026-08 ledgers separate with ` · `;
# the older DECISIONS style separates with ` — `. Splitting on BOTH is what keeps
# the page key the stable short anchor (`UX-28`) instead of a whole title
# (`UX-1 · Launcher mechanism`, the BL-X12 (d) unstable key).
_BULLET_ANCHOR_SEP_RE = re.compile(r"\s+[·—]\s+")
# Bullet-entry status vocabulary (BL-X12 (c)) — CLOSED, and fail-closed to open.
# Derived by reading the real bullet-form ledgers: ux-rework (`… is LOCKED.`,
# `(locked 2026-08-16)`, `Transcript color ruling`, `Ruling: keep BOTH …`),
# backlog-burn-mode (`The fork is RULED`, `operator ruling … BINDING NOW`) and
# agent-cadre. The open marker WINS over any decided marker — an undecided entry
# emitted as decided is the exact harm BL-X12 filed.
_BULLET_OPEN_RE = re.compile(r"\bopen\s+questions?\b", re.IGNORECASE)
_BULLET_DECIDED_RE = re.compile(r"\b(?:locked|ruled|rulings?|resolved)\b", re.IGNORECASE)

# Route guard (BL-X12 (c) / D136): a file carrying either mark is a GRILL LEDGER
# and is REFUSED by the `--decisions` route. `spec:` is the frontmatter key every
# ledger in `.planning/specs/*/` carries and DECISIONS.md does not.
_GRILL_LEDGER_NAME_RE = re.compile(r"grill[-_ ]?ledger", re.IGNORECASE)
_LEDGER_FM_KEY = "spec"
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
# The entry BODY's section title (LFB-1). It is rendered ALONGSIDE any parsed
# fields, never instead of them: `Detail` when fields are also present (the body
# is the surrounding reasoning), `Decision` when none parsed (the field-less MM
# `· LOCKED` form, where the body IS the recorded resolution).
_BODY_TITLE_WITH_FIELDS = "Detail"
_BODY_TITLE_ALONE = "Decision"

# SB-L4 redaction classes — fixed apply order, bounded patterns (linear scan; no
# nested/chained quantifiers — ReDoS-safe by construction).
#
# ONE SCRUB, TWO CALL POINTS (RS-M7 / DESIGN §8 S4).  This table is THE class table: the
# trust-model close reaches it through `kata_close.redact_at_commit_act` (committed run
# provenance, at the branch-close commit act — never at mint, which is what closes the
# TOCTOU window) and `kata_close.redact_at_snapshot_edge` (cursor/trail content at the
# snapshot-or-push edge).  Neither point owns a pattern of its own, deliberately: a second
# table is how two scrubs drift apart and one of them quietly stops covering a class.
#
# The extension below (rows 7-14) was added by that task.  Every row keeps the original
# construction rules — bounded quantifiers, no nesting, linear scan — and the apply order
# of the first six rows is UNCHANGED, so an existing page's counts do not move except
# where a genuinely new class matches.
#
# Redaction is DETECTION, and the honesty label travels with the table: a clean result
# means no class HERE matched, never that no secret is present.  Undetected content is a
# stated residual (trust-model DESIGN §11).
_REDACTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github-pat", re.compile(r"github_pat_[A-Za-z0-9_]+")),
    ("private-key", re.compile(r"-----BEGIN[A-Z ]{0,40}PRIVATE KEY-----")),
    ("password", re.compile(r"\bpassword\s*[:=]\s*\S+", re.IGNORECASE)),
    ("token", re.compile(r"\btoken\s*[:=]\s*\S+", re.IGNORECASE)),
    ("secret", re.compile(r"\bsecret\s*[:=]\s*\S+", re.IGNORECASE)),
    # --- RS-M7 extension (trust-model close-machinery) ---
    # Ordered most-specific-first: a vendor-shaped literal is recognised as ITS class
    # before the generic `<label>: <value>` rows below can claim it, so the recorded
    # class name stays useful in the refusal message.
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_-]{16,128}")),
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9]{20,64}\b")),
    ("google-api-key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("slack-token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,120}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,300}\.[A-Za-z0-9_-]{8,300}\.[A-Za-z0-9_-]{8,300}")),
    # A URL carrying inline credentials — `scheme://user:pass@host`.  Bounded on every
    # segment; the `@` terminator is what keeps it from running away over a line.
    ("connection-string", re.compile(r"\b[a-z][a-z0-9+.-]{1,20}://[^\s:/@]{1,64}:[^\s@/]{1,64}@")),
    ("bearer", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,512}", re.IGNORECASE)),
    # The generic labelled-credential rows, mirroring the original three in shape.
    ("api-key", re.compile(r"\bapi[_-]?key\s*[:=]\s*\S+", re.IGNORECASE)),
    ("credential", re.compile(r"\b(?:passwd|pwd|client[_-]?secret|access[_-]?key)\s*[:=]\s*\S+",
                              re.IGNORECASE)),
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


def _source_slug(source: str | Path) -> str:
    """Filename namespace slug for a page, derived from its source artifact path.

    The emitted page is ``<project>--<source-slug>--<anchor>.md``; the source-slug
    prevents cross-source filename collisions (every spec GRILL-LEDGER restarts
    anchors at ``D1`` and DECISIONS.md uses ``D``-anchors globally — without a
    namespace a ``--decisions`` backfill would clobber a prior ledger's page). The
    slug is the source file's PARENT directory name — the natural per-spec
    namespace (``.planning/specs/statusline-decouple/GRILL-LEDGER.md`` →
    ``statusline-decouple``) — falling back to the file STEM when the parent is the
    shared ``.planning`` root (or absent). Lowercased + filesystem-safe via
    :func:`_slug`. Determinism Doctrine: same input path ⇒ same slug
    (``PurePosixPath`` on a forward-slashed path — OS-independent).
    """
    p = PurePosixPath(str(source).replace("\\", "/"))
    parent = p.parent.name
    base = p.stem if (not parent or parent == ".planning") else parent
    return _slug(base)


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

class _BoldSpan:
    """Accumulator for a ``**…**`` bold anchor span that WRAPS across lines.

    Both bullet routes need it and for the same reason: the 2026-08 house style
    wraps long anchor spans, and a regex that requires the closing ``**`` on the
    opening physical line drops those records **silently** — no note, no count.
    That cost the ledger route UX-28/UX-32 (BL-X12 (b), fixed) and it still cost
    the DECISIONS route D168/D172/D173 (3 of 177) until this class was shared.

    Construct with the text following the opening ``**``, then :meth:`feed` each
    following physical line until it returns the closed ``(span, tail)`` pair or
    :attr:`abandoned` goes True. Pure — no I/O, no clock, no module state.
    """

    __slots__ = ("lines", "abandoned")

    def __init__(self, head: str) -> None:
        self.lines: list[str] = [head]
        self.abandoned = False

    def feed(self, line: str) -> tuple[str, str] | None:
        """Consume one physical line.

        Returns ``(span, tail)`` when the closing ``**`` is found — ``span`` is
        the re-joined bold text (each physical line stripped, joined by a single
        space, so a wrap never fuses two words) and ``tail`` is the rest of that
        line, i.e. the record's lead body text. Returns ``None`` while the span
        is still open; sets :attr:`abandoned` when the
        :data:`_MAX_BOLD_SPAN_LINES` bound is exceeded (an unterminated ``**``
        is malformed markdown, not a record).
        """
        head, sep, tail = line.partition("**")
        if sep:
            self.lines.append(head)
            return " ".join(s.strip() for s in self.lines), tail
        if len(self.lines) >= _MAX_BOLD_SPAN_LINES:
            self.abandoned = True
            return None
        self.lines.append(line)
        return None


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


def _bullet_status(title: str, body: str) -> str:
    """Classify a BULLET entry — fail-closed to ``"open"`` (BL-X12 (c), D136).

    Scans the title and the entry's LEAD line (its first non-empty body line —
    the house style puts the ruling verb there: *"Ruling: keep BOTH …"*). An
    explicit open marker WINS; a decided marker resolves; anything else is open.
    Pure, no clock, no state.
    """
    lead = next((ln for ln in body.splitlines() if ln.strip()), "")
    probe = f"{title}\n{lead}"
    if _BULLET_OPEN_RE.search(probe):
        return "open"  # an explicit OPEN QUESTION is never a decision pattern
    return "resolved" if _BULLET_DECIDED_RE.search(probe) else "open"


def _parse_bullet_entry(span: str, fm_date: str | None) -> dict | None:
    """Parse a bullet's (possibly re-joined multi-line) bold span → entry skeleton.

    ``None`` when the span carries no anchor token — a bold lead-in such as
    ``- **Refined (operator, 2026-08-16):**`` is prose, not an entry. Status is
    left ``"open"`` here and finalized by :func:`_bullet_status` once the body is
    assembled (the lead line is part of the evidence). Pure.
    """
    span = span.strip()
    first = _BULLET_ANCHOR_SEP_RE.split(span)[0]
    a = _ANCHOR_RE.match(first)
    if not a:
        return None
    # Everything after the anchor TOKEN stays in the title verbatim (the split
    # bounds the anchor candidate; it never discards text).
    title = span[a.end():].strip().lstrip("·—-").strip().rstrip(".").strip()
    return {
        "anchor": a.group("anchor"),
        "title": title,
        "status": "open",  # provisional — fail-closed default (BL-X12 (c))
        "date": _first_date(title) or fm_date,
        "fields": {},
        "body": "",
    }


def _heading_entry_mask(lines: list[str], fm_date: str | None) -> list[bool]:
    """Mark every line OWNED by a heading entry (its heading line included).

    Bullet entries are harvested only from the unmarked regions, so the SB-L1
    heading grammar — including how a heading entry swallows its own bullets as
    fields/body — is behaviorally untouched by the BL-X12 bullet grammar.
    """
    mask = [False] * len(lines)
    owned = False
    for i, line in enumerate(lines):
        h = _HEADING_LINE_RE.match(line)
        if h:
            owned = _parse_heading_entry(h.group("rest"), fm_date) is not None
        mask[i] = owned
    return mask


def _parse_ledger_bullets(
    lines: list[str], mask: list[bool], fm_date: str | None
) -> list[dict]:
    """Parse top-level ``- **anchor · title.** body`` ledger entries (BL-X12).

    Runs only over lines no heading entry owns. Handles the multi-line bold span
    (BL-X12 (b)) and ends a record on the next top-level bullet, any heading, a
    heading-entry region, or a blank line followed by non-indented content — the
    same record shape :func:`parse_decisions_bullets` uses. Pure.
    """
    entries: list[dict] = []
    span: _BoldSpan | None = None  # an unterminated `**…` span in progress
    current: dict | None = None
    body: list[str] = []
    pending_blank = False

    def _flush() -> None:
        nonlocal current, body, pending_blank
        if current is not None:
            current["body"] = "\n".join(ln.rstrip() for ln in body).strip()
            current["status"] = _bullet_status(current["title"], current["body"])
            entries.append(current)
        current, body, pending_blank = None, [], False

    def _open(bold: str, tail: str) -> None:
        nonlocal current, body, pending_blank, span
        span = None
        current = _parse_bullet_entry(bold, fm_date)
        body = [tail.strip()] if tail.strip() else []
        pending_blank = False

    for i, line in enumerate(lines):
        if mask[i]:  # a heading entry owns this line — it is not bullet territory
            _flush()
            span = None
            continue
        if span is not None:  # accumulating a wrapped bold anchor span
            closed = span.feed(line)
            if closed is not None:
                _open(*closed)
            elif span.abandoned:
                span = None  # unterminated bold ⇒ malformed, not an entry
            continue
        m = _LEDGER_BULLET_OPEN_RE.match(line)
        if m:
            _flush()
            head, sep, tail = m.group("rest").partition("**")
            if sep:
                _open(head, tail)
            else:
                span = _BoldSpan(head)  # the span wraps onto the following line(s)
            continue
        if current is None:
            continue  # prose between entries
        if _RECORD_END_HEADING_RE.match(line):
            _flush()
            continue
        if not line.strip():
            pending_blank = True
            continue
        if pending_blank and not line[:1].isspace():
            _flush()  # blank + non-indented ⇒ new paragraph; the line is outside
            continue
        if pending_blank:  # blank + indented ⇒ an internal blank within the record
            body.append("")
            pending_blank = False
        body.append(line)
    _flush()
    return entries


def parse_grill_ledger(text: str | None) -> list[dict]:
    """Parse a grill decision ledger's entries (SB-L1 grammar + BL-X12 bullets).

    Returns ALL parsed entries — resolved AND open — as dicts
    ``{anchor, title, status, date, fields, body}``; the caller filters
    ``status == "resolved"`` for emission and counts the rest as
    ``parsed_open_skipped``.

    Two grammars, appended in a fixed order — every SB-L1 **heading** entry
    (unchanged), THEN the 2026-08 house-style **bullet** entries (BL-X12)
    harvested from the regions no heading entry owns; each group is in document
    order (page filenames are keyed and sorted downstream, so the concatenation
    order is presentational only). The file literally named ``GRILL-LEDGER.md``
    used to be invisible to this function. Bullet status is fail-closed to open
    (:func:`_bullet_status`); heading status keeps its own closed vocabulary.
    Pure.
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

    entries += _parse_ledger_bullets(lines, _heading_entry_mask(lines, fm_date), fm_date)
    return entries


def parse_decisions_bullets(text: str | None) -> list[dict]:
    """Parse ``- **anchor — title.** body`` bullets (recall's ``_BULLET_RE`` family).

    Every DECISIONS bullet is a decided decision ⇒ ``status="resolved"`` (the F-10
    backfill path — volume accepted, not capped). Entry date = the file's
    frontmatter ``date:`` (never mined from bullet prose).

    DECISIONS records WRAP over multiple physical lines: a record's body is the
    text after the ``**…**`` bold anchor PLUS every following continuation line
    (indented wraps, indented sub-bullets, or plain wrapped prose) up to — but not
    including — the next ``- **`` bullet, a ``#`` heading, or a blank line followed
    by non-indented content (a new paragraph / an HTML ``<!-- … -->`` section
    separator ends the record). Capturing only the first physical line
    (the prior ``_BULLET_RE.finditer``) truncated wrapped records mid-sentence.
    Redaction runs over the FULL assembled body downstream in :func:`render_page`.

    The **bold anchor span itself** may also wrap (BL-X12 (b) residue, 2026-08-16):
    the record-start regex required the closing ``**`` on the opening physical
    line, so a record whose anchor+title runs past the wrap column was not seen as
    a record at all — its text was silently vacuumed into the PRECEDING record's
    body. On the real ``.planning/DECISIONS.md`` that dropped D168, D172 and D173
    (3 of 177) with no note and no count, and the grill-close command routes that
    exact file through this exact route. :class:`_BoldSpan` — the same accumulator
    the ledger route already used — now spans the break here too.

    Everything else about this route's contract is DELIBERATELY unchanged: the
    ``- `` literal record-start prefix, the record terminators, and
    ``status="resolved"`` (correct by DECISIONS.md's own contract; a grill ledger
    reaching this parser is refused upstream by :func:`grill_ledger_marker`).
    Pure.
    """
    src = text or ""
    meta, _ = _parse_frontmatter(src)
    fm_date = _first_date(meta.get("date"))

    entries: list[dict] = []
    current_raw: str | None = None  # the `**…**` bold span of the open record
    span: _BoldSpan | None = None   # an unterminated `**…` span in progress
    body: list[str] = []
    pending_blank = False

    def _flush() -> None:
        nonlocal current_raw
        if current_raw is None:
            return
        raw = current_raw.strip().rstrip(".").strip()
        if raw:
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
                "body": "\n".join(body).strip(),
            })
        current_raw = None

    def _open(bold: str, tail: str) -> None:
        nonlocal current_raw, body, pending_blank, span
        span = None
        current_raw = bold
        body = [tail]
        pending_blank = False

    for line in src.splitlines():
        if span is not None:  # accumulating a wrapped bold anchor span
            closed = span.feed(line)
            if closed is not None:
                bold, tail = closed
                _open(bold, tail.lstrip())  # `**` … `**` then the lead body text
            elif span.abandoned:
                span = None  # unterminated bold ⇒ malformed, not a record
            continue
        m = _DECISIONS_BULLET_OPEN_RE.match(line)
        if m:  # a new top-level `- **…` record starts here
            _flush()
            pending_blank = False
            head, sep, tail = m.group("rest").partition("**")
            if sep:
                _open(head, tail.lstrip())
            else:
                span = _BoldSpan(head)  # the span wraps onto the following line(s)
            continue
        if current_raw is None:
            continue  # content before the first bullet (frontmatter, intro prose)
        if _RECORD_END_HEADING_RE.match(line):  # any `#`..`######` heading ends the record
            _flush()
            pending_blank = False
            continue
        if not line.strip():  # defer: a blank may be internal OR a separator
            pending_blank = True
            continue
        if pending_blank and not line[:1].isspace():
            _flush()  # blank + non-indented ⇒ new paragraph; the line is outside
            pending_blank = False
            continue
        if pending_blank:  # blank + indented ⇒ an internal blank within the record
            body.append("")
            pending_blank = False
        body.append(line)
    _flush()
    return entries


# ---------------------------------------------------------------------------
# Route guard (BL-X12 (c) / D136 — fail-closed, never a silent misclassification)
# ---------------------------------------------------------------------------

def grill_ledger_marker(path: str | Path, text: str | None) -> str | None:
    """Name why ``path``/``text`` is a GRILL LEDGER, or ``None`` if it is not.

    Two independent marks, either sufficient: a ``spec:`` frontmatter key (every
    ledger under ``.planning/specs/*/`` carries one; ``.planning/DECISIONS.md``
    does not), or a ``GRILL-LEDGER`` filename. Used by :func:`main` to REFUSE a
    ledger on the ``--decisions`` route — that route's parser marks every bullet
    resolved by DECISIONS.md's contract, so routing a ledger through it emits the
    ledger's OPEN questions into the vault as decided rulings (BL-X12 (c), the
    live defect). The guard lives here at the route layer, never inside the pure
    parser, whose hardcoded status is correct for the file it is contracted to.
    Pure — no I/O; the caller supplies the already-read text.
    """
    name = PurePosixPath(str(path).replace("\\", "/")).name
    if _GRILL_LEDGER_NAME_RE.search(name):
        return f"filename {name!r} names it a grill ledger"
    meta, _ = _parse_frontmatter(text or "")
    if _LEDGER_FM_KEY in meta:
        return f"frontmatter carries a {_LEDGER_FM_KEY!r} key ({meta[_LEDGER_FM_KEY]!r})"
    return None


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
    source_slug: str | None = None,
) -> tuple[str, str]:
    """Render ONE resolved entry into a wiki-synthesis page (SB-L2, verbatim).

    Pure — no I/O, no clock (``now`` is injected; used only when the entry
    carries no date). Hard-fails (``ValueError``) on unusable INPUT to this
    decision code: unknown ``kind``/``scope``, empty ``project``, missing anchor —
    never a silent permissive default.

    Args:
        source_slug: explicit filename namespace (the ``--decisions`` path pins the
            literal ``"decisions"``). When ``None`` (the ``--ledger`` path) it is
            derived from the source path via :func:`_source_slug`.

    Returns:
        ``(relpath, content)`` — relpath is the deterministic
        ``decision-patterns/<project-slug>--<source-slug>--<anchor-slug>.md``
        (SB-L3); content is the full page, LF-only, frontmatter ``redactions: N``
        present only when the SB-L4 scrub hit (redaction marks, never blocks).
        Body sections: the present parsed fields in :data:`_SECTION_ORDER`, THEN
        the entry body under ``## Detail`` (LFB-1 — additive, never a substitute);
        with no fields parsed the body renders under ``## Decision`` instead, and
        with no body neither extra section is emitted.
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
    # Filename namespace (collision guard): explicit slug (the --decisions literal
    # "decisions") or derived from the source artifact path (the --ledger path).
    src_slug = _slug(source_slug) if source_slug is not None else _source_slug(sources[0])

    title = str(entry.get("title") or "").strip()
    fields = entry.get("fields") or {}
    body_text = str(entry.get("body") or "").strip()

    # --- body (one page = one pattern; wikilinks to the raw artifact) ---
    lines: list[str] = [f"# {anchor} — {title}" if title else f"# {anchor}", ""]
    lines += ["**Source:** " + " · ".join(f"[[{s}]]" for s in sources), ""]
    present = [k for k in _SECTION_ORDER if str(fields.get(k) or "").strip()]
    for k in present:
        lines += [f"## {_SECTION_TITLES[k]}", "", str(fields[k]).strip(), ""]
    if body_text:
        # LFB-1: the body renders IN ADDITION to the fields, never INSTEAD of them.
        # The prior `elif` discarded the body whenever ANY field parsed, and the
        # house style — a bold field prefix followed by indented sub-bullets and
        # `**Rejected — …**` bullets — reliably parses *some* field while leaving
        # the substance in the body, so the dropping branch was the one that fired
        # (68 of 218 entries / 46,427 characters across 22 ledgers; DEF-2).
        #
        # Which heading the body takes depends on what it IS:
        #   fields present ⇒ the body is the surrounding reasoning → `## Detail`.
        #   no fields      ⇒ the body IS the recorded resolution (the field-less
        #                    MM `· LOCKED` form) → the canonical `## Decision`.
        #                    This path is load-bearing and unchanged.
        lines += [f"## {_BODY_TITLE_WITH_FIELDS if present else _BODY_TITLE_ALONE}", "",
                  body_text, ""]
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

    relpath = f"{_FEED_SUBDIR}/{_slug(project)}--{src_slug}--{_slug(anchor)}.md"
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
                notes.append(f"{ledger}: 0 entries (no heading or bullet entry parsed)")
            for e in entries:
                if e["status"] != "resolved":
                    continue  # open/no-status entries are NOT decision-pattern signal
                relpath, content = render_page(
                    e, project=args.project, source_path=str(ledger),
                    scope=args.scope, kind=args.kind, now=now,
                )
                pages[relpath] = (relpath, content)
        if args.decisions:
            decisions_text = _read_text(args.decisions)
            # D136 fail-closed route guard (BL-X12 (c)): a grill ledger is REFUSED
            # here rather than silently emitted as all-resolved decisions.
            marker = grill_ledger_marker(args.decisions, decisions_text)
            if marker:
                raise ValueError(
                    f"refusing --decisions {args.decisions}: {marker}. "
                    "A grill ledger goes through the --ledger route: --decisions marks "
                    "EVERY bullet resolved (correct for DECISIONS.md, whose bullets are all "
                    "decided), so a ledger routed here emits its OPEN QUESTIONS into the "
                    "vault as decided rulings."
                )
            for e in parse_decisions_bullets(decisions_text):
                relpath, content = render_page(
                    e, project=args.project, source_path=str(args.decisions),
                    scope=args.scope, kind=args.kind, now=now,
                    source_slug="decisions",  # F-10 backfill namespace (defect 1)
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
