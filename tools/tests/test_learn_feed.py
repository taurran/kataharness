"""test_learn_feed.py — TDD suite for tools/learn_feed.py (second-brain-loop SB-L1..SB-L4).

Strategy: default-FAIL, written to the FROZEN second-brain-loop DESIGN. Pure except
tmp_path writes. Fixtures are VERBATIM excerpts of the two real grill ledgers
(multi-model-orchestration `### MM-n … · LOCKED` form; context-autonomy
`### R-n (…) title — RESOLVED <trailing>` forms — the freeze-gate re-gate LOW
obligation pin), plus the canonical DECISION-LEDGER.md bold-field shape.

Coverage map
------------
SB-L1 parse:   heading grammar (anchor vocab MM-1/IP-A/R-1/GB1/D7); status vocab
               `· LOCKED` / `· RESOLVED` / `— RESOLVED` case-insensitive, TOLERANT of
               trailing text; the vocabulary is CLOSED — other status-shaped tails the
               real ledgers use (`— NO OPERATOR ACTION`, `— ACCEPTED`, `— RECORDED …`)
               ⇒ open; `· open`/no-status ⇒ open, NOT emitted; bold-field bullets
               tolerant (any subset); parse_decisions_bullets (recall _BULLET_RE family).
BL-X12:        bullet-form ledger entries — multi-line bold anchor spans (the UX-28/
               UX-32 silent drop), ` · `/` — ` anchor partition ⇒ stable short keys,
               FAIL-CLOSED status (decided markers only; `OPEN QUESTION` wins; bare
               `ACCEPTED` stays open); heading entries provably undisturbed; the
               `--decisions` ROUTE GUARD refusing grill-ledger-marked files (D136);
               and the challenger's live reproduction against the real ux-rework
               ledger pinned as a regression.
SB-L2 render:  relpath `decision-patterns/<project-slug>--<source-slug>--<anchor-slug>.md`;
               frontmatter produced-by/source/date/scope/sorted tags (+redactions
               only when >0); kind→tag map; body sections present-fields-only with
               [[wikilinks]]; LF-only.
SB-L3 emit:    atomic temp+rename; date-scrubbed idempotency (identical-otherwise ⇒
               skip); changed ⇒ overwrite; produced-by ≠ loop ⇒ fail-closed refuse
               (incl. missing frontmatter; all-or-nothing pre-scan); zero-page emit ⇒
               NO log line; one log line per writing session; both paths `..`-guarded
               INDEPENDENTLY.
SB-L4 redact:  AKIA / github_pat_ / PRIVATE KEY / password|token|secret[:=] classes ⇒
               [REDACTED:<class>], counted, NEVER blocks emit.
CLI:           --project REQUIRED; --json report to stdout sort_keys=True; human
               summary to stderr; open entries counted as parsed_open_skipped.
Determinism:   wall clock minted ONLY in main() (law 7); stdlib-only; no randomness;
               no exec sinks.
"""

from __future__ import annotations

import ast
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

import learn_feed

_SOURCE = Path(__file__).resolve().parent.parent / "learn_feed.py"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_MM_LEDGER = _REPO_ROOT / ".planning" / "specs" / "multi-model-orchestration" / "GRILL-LEDGER.md"
_CA_LEDGER = _REPO_ROOT / ".planning" / "specs" / "context-autonomy" / "GRILL-LEDGER.md"

NOW = datetime(2026, 7, 12, 8, 0, 0, tzinfo=UTC)

# ---------------------------------------------------------------------------
# Fixtures — VERBATIM excerpts of the real ledgers
# ---------------------------------------------------------------------------

# .planning/specs/multi-model-orchestration/GRILL-LEDGER.md (the `· LOCKED` form).
MM_EXCERPT = """\
## Resolved branches (LOCKED ledger)

### MM-1 — Five role groups; evaluator is a distinct lightweight inline scorer · LOCKED
- coder = `execute/` (kata-tdd). validator = adversarial cluster (red-team + anti-slop + grounding). researcher =
  `plan/kata-research`. orchestrator = `coordinate/` (plan-guardian).
- Boundary: evaluator = conformance/scoring; validator = adversarial.

### MM-2 — Every role routable to any platform; coder stays a single agent · LOCKED
- Any role → any platform/model (incl. coder on non-Claude).
"""

# .planning/specs/context-autonomy/GRILL-LEDGER.md heading forms (freeze-gate
# re-gate LOW obligation: status token TOLERANT of trailing text).
#
# R-5 is VERBATIM from the real ledger (`:138`) and carries the `— ACCEPTED`
# status-shaped tail. It is the classification obligation the real-ledger floor
# pins CANNOT carry (a floor over `resolved` can only red on a resolved entry
# going open, never on an open one being promoted), so it lives here, on a
# fixture, where a vocabulary change that swallows `accepted` reds immediately.
CA_EXCERPT = """\
### R-1 (CA-1c) Threshold policy — RESOLVED 2026-07-04
Operator: 70% default, "fine no matter how much it really is," surfaced as a configurable
recommendation at configuration; default stands.

### R-3 (CA-7a) Fable gate — RESOLVED core + NEW above-anchor concept; one sub-Q open
Option A confirmed (decline => pin anchor opus + hard-stop advising /model switch).

### R-4 (statusline discovery) — NO OPERATOR ACTION; design mandate stands
Operator's own statusline works and stays untouched.

### R-5 (CA-11) Installer fix — ACCEPTED
Fix shared-base-dir install gap; enumerate + freeze the "5 frozen engine fns" list in DESIGN first.

### R-6 (NEW — handoff taxonomy) Operator-requested assessment: "clean handoff management for
manual, self, and agent handoffs — assess what needs clarifying." Assessment below.

### R-12 (CA-6a) Preflight strictness — RECORDED PENDING VETO (asked twice, unanswered)
Intent-keyed: walk-away-configured run.
"""

# Canonical DECISION-LEDGER.md per-entry shape (bold-field bullets).
CANONICAL_ENTRY = """\
### D7 — Escalation timeout default  ·  LOCKED
- **Question:** what timeout for worker escalations?
- **Provenance:** spec §4 left it open.
- **Options considered:** A (30m, chosen) · B (60m) — one line of trade-off each.
- **Decision:** 30 minutes, config-overridable,
  applied at dispatch.
- **Rationale:** matches the liveness deadline.
- **Edges/scenarios:** clock skew ⇒ monotonic timer.
- **Doc-baked:** glossary term added.
"""

BULLET_ONLY = """\
# Decisions

- **D1 — The plan does not drift.** Orchestrator = plan-guardian (owns frozen plan, task assignment).
- **D2 — One-shot = no plan churn.** Deep plan → execute → eval → targeted fix vs the same plan.
"""


def _entry(**over) -> dict:
    base = {
        "anchor": "MM-1",
        "title": "Five role groups",
        "status": "resolved",
        "date": None,
        "fields": {},
        "body": "Decision body.",
    }
    base.update(over)
    return base


def _render(entry=None, **kw):
    kw.setdefault("project", "KataHarness")
    kw.setdefault("source_path", ".planning/specs/x/GRILL-LEDGER.md")
    kw.setdefault("scope", "project")
    kw.setdefault("kind", "project")
    kw.setdefault("now", NOW)
    return learn_feed.render_page(entry if entry is not None else _entry(), **kw)


# ---------------------------------------------------------------------------
# SB-L1 — parse_grill_ledger: heading grammar + status vocabulary
# ---------------------------------------------------------------------------

def test_parse_mm_locked_headings():
    """Real MM form: `### MM-n — title · LOCKED` ⇒ resolved entries."""
    entries = learn_feed.parse_grill_ledger(MM_EXCERPT)
    assert [e["anchor"] for e in entries] == ["MM-1", "MM-2"]
    assert all(e["status"] == "resolved" for e in entries)
    assert entries[0]["title"] == "Five role groups; evaluator is a distinct lightweight inline scorer"
    assert "coder = `execute/`" in entries[0]["body"]


def test_parse_context_autonomy_real_forms():
    """The pinned freeze-gate obligation: real context-autonomy heading forms.

    `— RESOLVED 2026-07-04` and `— RESOLVED core + …` (trailing text after the
    status token) ⇒ resolved; `— NO OPERATOR ACTION` / `— ACCEPTED` /
    `— RECORDED PENDING VETO` / no status ⇒ open.

    The negative half is the load-bearing half: the status vocabulary is
    CLOSED (`locked`/`resolved`/`open`). Every other `— <WORD>` tail the real
    ledgers use is an editorial note, NOT a resolution, and must classify open
    — otherwise `learn_feed` emits an unresolved branch as a decision pattern.
    """
    entries = {e["anchor"]: e for e in learn_feed.parse_grill_ledger(CA_EXCERPT)}
    assert entries["R-1"]["status"] == "resolved"
    assert entries["R-1"]["date"] == "2026-07-04"  # trailing entry date captured
    assert entries["R-3"]["status"] == "resolved"  # trailing text after RESOLVED
    assert entries["R-4"]["status"] == "open"
    assert entries["R-5"]["status"] == "open"      # ACCEPTED is NOT in the vocabulary
    assert entries["R-6"]["status"] == "open"      # no status token at all
    assert entries["R-12"]["status"] == "open"     # RECORDED is NOT in the vocabulary


def test_parse_status_case_insensitive():
    text = "### D1 — a thing · locked\nbody\n\n### D2 — other — resolved\nbody\n"
    entries = learn_feed.parse_grill_ledger(text)
    assert [e["status"] for e in entries] == ["resolved", "resolved"]


def test_parse_explicit_open_status():
    entries = learn_feed.parse_grill_ledger("### D3 — pending call · open\nbody\n")
    assert entries[0]["status"] == "open"


def test_parse_anchor_token_vocabulary():
    """Anchor = any ledger token: MM-1, IP-A, R-1, GB1, D7."""
    text = "\n\n".join(
        f"### {a} — some branch title · LOCKED\n- body"
        for a in ("MM-1", "IP-A", "R-1", "GB1", "D7")
    )
    entries = learn_feed.parse_grill_ledger(text)
    assert [e["anchor"] for e in entries] == ["MM-1", "IP-A", "R-1", "GB1", "D7"]


def test_parse_non_anchor_headings_ignored():
    """Prose headings and range headings are NOT entries (no false resolutions)."""
    text = (
        "## Resolved branches (LOCKED ledger)\n"
        "### Self-resolved defaults (TUNABLE, freeze-gate attacks numbers)\n"
        "- Gauge staleness: 300s.\n"
        "### R-14..R-21 — Convergence-gate HOLD branches folded (gate v1, 8 findings)\n"
        "- R-14 (gate#1): host compaction.\n"
    )
    assert learn_feed.parse_grill_ledger(text) == []


def test_parse_bullet_only_ledger_parses_fail_closed():
    """BL-X12 (a): bullet-form ledgers parse — and classify fail-closed to open.

    SUPERSEDES the pre-BL-X12 pin `== []` ("honest scope"). Zero entries was the
    defect, not the contract: the file literally named GRILL-LEDGER.md was
    invisible to the `--ledger` route. These two bullets carry no decided marker,
    so they parse OPEN and still emit nothing — the honesty is now in the STATUS,
    not in the blindness.
    """
    entries = learn_feed.parse_grill_ledger(BULLET_ONLY)
    assert [e["anchor"] for e in entries] == ["D1", "D2"]
    assert {e["status"] for e in entries} == {"open"}


def test_parse_empty_and_none():
    assert learn_feed.parse_grill_ledger("") == []
    assert learn_feed.parse_grill_ledger(None) == []


def test_parse_bold_fields_full_set():
    """Canonical bold-field bullets are captured (Doc-baked is NOT a page field)."""
    (entry,) = learn_feed.parse_grill_ledger(CANONICAL_ENTRY)
    assert entry["status"] == "resolved"
    assert entry["fields"]["question"] == "what timeout for worker escalations?"
    assert entry["fields"]["provenance"].startswith("spec")
    assert entry["fields"]["options"].startswith("A (30m, chosen)")
    # multi-line field value folded
    assert entry["fields"]["decision"] == "30 minutes, config-overridable, applied at dispatch."
    assert entry["fields"]["rationale"] == "matches the liveness deadline."
    assert entry["fields"]["edges"] == "clock skew ⇒ monotonic timer."
    assert "doc-baked" not in entry["fields"]


def test_parse_bold_fields_any_subset():
    text = "### D9 — engram gating · LOCKED\n- **Decision:** stay gated off.\n"
    (entry,) = learn_feed.parse_grill_ledger(text)
    assert entry["fields"] == {"decision": "stay gated off."}


def test_parse_frontmatter_date_fallback():
    text = "---\ndate: 2026-06-26\n---\n### D1 — a call · LOCKED\n- body\n"
    (entry,) = learn_feed.parse_grill_ledger(text)
    assert entry["date"] == "2026-06-26"


# ---------------------------------------------------------------------------
# SB-L1 — parse_decisions_bullets (recall _BULLET_RE family)
# ---------------------------------------------------------------------------

def test_parse_decisions_bullets_shape():
    entries = learn_feed.parse_decisions_bullets(BULLET_ONLY)
    assert [e["anchor"] for e in entries] == ["D1", "D2"]
    assert entries[0]["title"] == "The plan does not drift"
    assert entries[0]["status"] == "resolved"
    assert entries[0]["body"].startswith("Orchestrator = plan-guardian")


def test_parse_decisions_bullets_frontmatter_date():
    text = "---\ndate: 2026-05-01\n---\n- **D5 — AGENTS.md is canonical.** Cross-tool standard.\n"
    (entry,) = learn_feed.parse_decisions_bullets(text)
    assert entry["date"] == "2026-05-01"


def test_parse_decisions_bullets_empty():
    assert learn_feed.parse_decisions_bullets("") == []
    assert learn_feed.parse_decisions_bullets(None) == []


# ---------------------------------------------------------------------------
# DEFECT 2 — wrapped multi-line DECISIONS records are not truncated
# ---------------------------------------------------------------------------
# Real DECISIONS.md records wrap over multiple physical lines (2-space indented
# continuations, indented sub-bullets), are separated by blank + `<!-- … -->`
# section comments, and interleave `###` sub-headings. The prior `_BULLET_RE`
# finditer captured ONLY the first physical line → 70/95 backfilled pages
# truncated mid-sentence.

WRAPPED_DECISIONS = """\
---
date: 2026-06-01
---

# Decisions

- **D1 — The plan does not drift.** Orchestrator = plan-guardian (owns frozen plan, task assignment,
  file-ownership, gating); peers execute + communicate, never re-plan; unknowns escalate. *Why:* drift
  is the enemy of one-shot.
- **D2 — Second record.** Body line one
  continues onto line two.

<!-- a section separator comment, NOT part of D2 -->
- **D3 — Ladder.** Four rungs:
  (1) default → go.
  (2) add modules.

### sprint-cadence (a sub-heading, NOT part of D3)
- **D4 — After the heading.** Fresh record body.
"""


def test_decisions_bullet_body_not_truncated():
    """Defect 2: the FULL wrapped body is folded in, not just the first line."""
    entries = {e["anchor"]: e for e in learn_feed.parse_decisions_bullets(WRAPPED_DECISIONS)}
    d1 = entries["D1"]["body"]
    assert d1.startswith("Orchestrator = plan-guardian")
    assert "file-ownership, gating" in d1   # 2nd physical line captured
    assert "enemy of one-shot" in d1        # 3rd physical line captured


def test_decisions_blank_then_comment_terminates_record():
    """A blank line followed by non-indented content (an HTML section comment)
    ends the record — the comment is NOT vacuumed into the body."""
    entries = {e["anchor"]: e for e in learn_feed.parse_decisions_bullets(WRAPPED_DECISIONS)}
    d2 = entries["D2"]["body"]
    assert "continues onto line two." in d2
    assert "section separator comment" not in d2


def test_decisions_indented_subbullets_captured():
    entries = {e["anchor"]: e for e in learn_feed.parse_decisions_bullets(WRAPPED_DECISIONS)}
    d3 = entries["D3"]["body"]
    assert "(1) default → go." in d3
    assert "(2) add modules." in d3
    assert "sprint-cadence" not in d3       # a `###` heading ends the record


def test_decisions_heading_terminates_and_next_record_starts():
    entries = {e["anchor"]: e for e in learn_feed.parse_decisions_bullets(WRAPPED_DECISIONS)}
    assert entries["D4"]["body"] == "Fresh record body."


def test_decisions_full_body_redacted():
    """SB-L4 redaction runs over the FULL multi-line body, not just line 1."""
    text = "- **D9 — leak.** first line ok\n  password: hunter2 on a wrapped line\n"
    (entry,) = learn_feed.parse_decisions_bullets(text)
    assert "hunter2" in entry["body"]       # captured into the body...
    _, content = _render(entry)
    assert "hunter2" not in content         # ...and scrubbed at render
    assert "[REDACTED:password]" in content


# ---------------------------------------------------------------------------
# BL-X12 (b) RESIDUE — a wrapped bold ANCHOR SPAN on the --decisions route
# ---------------------------------------------------------------------------
# BL-X12's sub-defect (b) was closed on the --ledger side only. The record-start
# regex here still required the closing `**` on the OPENING physical line, so a
# record whose anchor+title ran past the wrap column was not seen as a record at
# all — its text was silently vacuumed into the PRECEDING record's body. Two
# wrongs, one cause: a record vanishes AND its neighbour is corrupted with the
# missing text, with no note and no count anywhere in the report.
#
# On the real `.planning/DECISIONS.md` at fix time that was D168, D172 and D173
# (3 of 177) — and the grill-close command routes that exact file through this
# exact flag (`skills/plan/kata-grill/RUBRIC.md:218`). The bodies of D167 and
# D171 shrank 7289→3877 and 4320→1581 characters when the fix excised the
# swallowed text back into its own records.

WRAPPED_ANCHOR_DECISIONS = """\
---
date: 2026-08-16
---

- **D167 — a record whose bold span closes on its own line.** Body of the
  PRECEDING record, which must not absorb its neighbour.
- **D168 — a title long enough that the bold anchor span wraps past the
  column, closing only on the CONTINUATION line.** 2026-08-01. The real body
  starts here and wraps too.
- **D169 — back to a single-line span.** Short body.
"""


def test_decisions_wrapped_anchor_span_is_a_record():
    """(b) residue: a record whose bold span wraps is parsed, not swallowed."""
    entries = {e["anchor"]: e for e in
               learn_feed.parse_decisions_bullets(WRAPPED_ANCHOR_DECISIONS)}
    assert set(entries) == {"D167", "D168", "D169"}, (
        "a wrapped bold anchor span is being dropped again"
    )
    # the span is re-joined with a single space — a wrap never fuses two words
    # and never leaks a newline into the title
    assert entries["D168"]["title"] == (
        "a title long enough that the bold anchor span wraps past the "
        "column, closing only on the CONTINUATION line"
    )
    # the record's own body starts after the CLOSING `**`, not before it
    assert entries["D168"]["body"].startswith("2026-08-01.")
    assert "starts here and wraps too" in entries["D168"]["body"]


def test_decisions_wrapped_anchor_does_not_corrupt_the_previous_record():
    """The other half of the same defect: the neighbour is not left holding the text."""
    entries = {e["anchor"]: e for e in
               learn_feed.parse_decisions_bullets(WRAPPED_ANCHOR_DECISIONS)}
    d167 = entries["D167"]["body"]
    assert d167.endswith("must not absorb its neighbour.")
    assert "D168" not in d167
    assert "CONTINUATION" not in d167


def test_decisions_unterminated_bold_is_not_a_record():
    """Fail-closed, mirroring the ledger route: unterminated `**` is malformed."""
    text = "- **D1 — closes here.** body\n" + "- **D2 never closes\n" + "  x\n" * 20
    anchors = [e["anchor"] for e in learn_feed.parse_decisions_bullets(text)]
    assert anchors == ["D1"]


_DECISIONS_FILE = _REPO_ROOT / ".planning" / "DECISIONS.md"
# Recorded at fix time (2026-08-16) against the real file: 177 top-level `- **`
# openers, of which these three wrapped their bold span and were dropped. The
# count invariant below is FLOOR-SAFE by construction — both sides are derived
# from the file, so a living DECISIONS.md that grows stays green; only a record
# going MISSING between the raw scan and the parser reds it.
_DECISIONS_WRAPPED_AT_FIX = ("D168", "D172", "D173")


@pytest.mark.skipif(not _DECISIONS_FILE.exists(), reason="real DECISIONS.md not present")
def test_real_decisions_file_loses_no_top_level_bullet():
    """The real-file reproduction: every top-level `- **` bullet becomes a record.

    Before the fix this was 174 parsed against 177 present — three records gone
    with no note, on the file the grill-close command actually routes here.
    """
    text = _DECISIONS_FILE.read_text(encoding="utf-8")
    openers = [ln for ln in text.splitlines() if ln.startswith("- **")]
    entries = learn_feed.parse_decisions_bullets(text)
    assert len(entries) == len(openers), (
        f"parsed {len(entries)} records from {len(openers)} top-level bullets — "
        f"{len(openers) - len(entries)} silently dropped"
    )
    anchors = {e["anchor"] for e in entries}
    for anchor in _DECISIONS_WRAPPED_AT_FIX:
        assert anchor in anchors, f"{anchor} is dropped again (wrapped bold span)"
    # every anchor is a stable short key, never a whole wrapped title
    assert all("\n" not in a for a in anchors)


# ---------------------------------------------------------------------------
# DEFECT 1 — source-namespaced filenames (no cross-source anchor collision)
# ---------------------------------------------------------------------------
# Every spec GRILL-LEDGER restarts anchors at D1 and DECISIONS.md uses D-anchors
# globally, so the prior `<project>--<anchor>.md` scheme let a --decisions
# backfill CLOBBER a prior ledger's page. New scheme:
# `<project>--<source-slug>--<anchor>.md`.

def test_source_slug_spec_dir():
    assert learn_feed._source_slug(
        ".planning/specs/statusline-decouple/GRILL-LEDGER.md"
    ) == "statusline-decouple"


def test_source_slug_backslash_path():
    assert learn_feed._source_slug(
        ".planning\\specs\\context-autonomy\\GRILL-LEDGER.md"
    ) == "context-autonomy"


def test_source_slug_planning_root_falls_back_to_stem():
    """A file directly under `.planning` uses the file STEM, not the shared dir name."""
    assert learn_feed._source_slug(".planning/DECISIONS.md") == "decisions"


def test_render_relpath_is_source_namespaced():
    relpath, _ = _render(source_path=".planning/specs/statusline-decouple/GRILL-LEDGER.md")
    assert relpath == "decision-patterns/kataharness--statusline-decouple--mm-1.md"


def test_render_relpath_explicit_source_slug():
    """The --decisions path pins the literal `decisions` source-slug."""
    relpath, _ = _render(source_path=".planning/DECISIONS.md", source_slug="decisions")
    assert relpath == "decision-patterns/kataharness--decisions--mm-1.md"


def test_render_no_cross_source_collision():
    """Two DIFFERENT sources with the SAME anchor D1 ⇒ DISTINCT filenames (defect 1)."""
    rp_a, _ = _render(_entry(anchor="D1"), source_path=".planning/specs/aa/GRILL-LEDGER.md")
    rp_b, _ = _render(
        _entry(anchor="D1"), source_path=".planning/DECISIONS.md", source_slug="decisions"
    )
    assert rp_a != rp_b
    assert rp_a.endswith("kataharness--aa--d1.md")
    assert rp_b.endswith("kataharness--decisions--d1.md")


# ---------------------------------------------------------------------------
# SB-L2 / SB-L3 — render_page
# ---------------------------------------------------------------------------

def test_render_relpath_deterministic():
    relpath, _ = _render()
    # default fixture source `.planning/specs/x/GRILL-LEDGER.md` ⇒ source-slug `x`
    assert relpath == "decision-patterns/kataharness--x--mm-1.md"


def test_render_frontmatter_contract():
    _, content = _render()
    assert content.startswith("---\n")
    assert "produced-by: loop\n" in content
    assert "source: .planning/specs/x/GRILL-LEDGER.md\n" in content
    assert "scope: project\n" in content
    assert "  - kata/decision-pattern/coding\n" in content
    assert "  - kata/synthesis/decision-pattern\n" in content
    # sorted tags: decision-pattern/coding sorts before synthesis/decision-pattern
    assert content.index("kata/decision-pattern/coding") < content.index("kata/synthesis/decision-pattern")


def test_render_date_entry_date_wins_else_now():
    _, with_date = _render(_entry(date="2026-07-04"))
    assert "date: 2026-07-04\n" in with_date
    _, without = _render(_entry(date=None))
    assert "date: 2026-07-12\n" in without  # NOW's date — injected clock, not wall clock


def test_render_kind_tag_map():
    for kind, tag in (
        ("project", "coding"),
        ("research", "research"),
        ("version-up", "workflow"),
        ("debug", "workflow"),
    ):
        _, content = _render(kind=kind)
        assert f"  - kata/decision-pattern/{tag}\n" in content


def test_render_unknown_kind_raises():
    with pytest.raises(ValueError):
        _render(kind="banana")


def test_render_bad_scope_raises():
    with pytest.raises(ValueError):
        _render(scope="global")


def test_render_missing_project_raises():
    with pytest.raises(ValueError):
        _render(project="")


def test_render_sections_present_fields_only():
    entry = _entry(fields={"question": "Which grammar?", "decision": "Headings only."}, body="")
    _, content = _render(entry)
    assert "## Question\n" in content
    assert "## Decision\n" in content
    assert "## Options considered" not in content
    assert "## Rationale" not in content
    assert "## Edges" not in content
    assert content.index("## Question") < content.index("## Decision")


def test_render_body_fallback_when_no_fields():
    """A field-less resolved entry (the MM form) still yields one-page-one-pattern."""
    _, content = _render(_entry(fields={}, body="The recorded resolution text."))
    assert "## Decision\n" in content
    assert "The recorded resolution text." in content


# ---------------------------------------------------------------------------
# DEFECT DEF-2 / LFB-1 — the body renders IN ADDITION to the fields, never instead
# ---------------------------------------------------------------------------
# `render_page` used `elif body_text:`, so ANY parsed field discarded the body.
# The house ledger style — a bold `- **Decision:**` prefix followed by indented
# sub-bullets and `- **Rejected — …**` bullets — reliably parses *some* field
# while leaving the substance in the body, so the dropping branch was the one
# that fired: 68 of 218 entries / 46,427 characters across 22 ledgers.

# A real-shaped house-style entry (verbatim shape of
# .planning/specs/ungated-protocol-files/GRILL-LEDGER.md UPF-4): bold field
# prefixes whose value wraps, interleaved with `**Rejected — …**` bullets whose
# names are NOT in _FIELD_PREFIXES and therefore land in the body.
HOUSE_STYLE_ENTRY = """\
### UPF-4 — Pin board.md's run-isolation MUST · LOCKED

- **Decision:** the pinned clause covers the run-isolation invariant — the board must
  contain only the current run's events.
- **Rejected — pin the sentence verbatim including truncation:** would make a permission
  that contradicts `D135` *harder to remove than to keep*.
- **Rejected — delete "(or truncate it)" first:** a behavior change to a live contract
  smuggled inside a guarding change.
- **Rationale:** truncation destroys the prior run's board.
- **Follow-up filed, NOT built here:** should `(or truncate it)` be removed?
- **Provenance:** `board.md:45-50` · operator ruling 2026-08-03.
"""


def test_render_fields_and_body_both_rendered():
    """LFB-1 (a): fields present AND body present ⇒ BOTH, body under `## Detail`."""
    entry = _entry(
        fields={"decision": "Use headings.", "rationale": "Cheapest to parse."},
        body="- **Rejected — bullets:** ambiguous under wrapping.",
    )
    _, content = _render(entry)
    # the field sections are rendered exactly as before
    assert "## Decision\n" in content
    assert "Use headings." in content
    assert "## Rationale\n" in content
    assert "Cheapest to parse." in content
    # ...AND the body is no longer discarded
    assert "## Detail\n" in content
    assert "Rejected — bullets" in content
    # fields first, body last (SB-L2 section order preserved)
    assert content.index("## Decision") < content.index("## Detail")
    assert content.index("## Rationale") < content.index("## Detail")


def test_render_no_detail_section_when_body_empty():
    """LFB-1 (b): fields only ⇒ NO empty `## Detail` section is emitted."""
    entry = _entry(fields={"question": "Which grammar?", "decision": "Headings."}, body="")
    _, content = _render(entry)
    assert "## Detail" not in content
    entry_ws = _entry(fields={"decision": "Headings."}, body="   \n\n  ")
    _, content_ws = _render(entry_ws)
    assert "## Detail" not in content_ws


def test_render_body_only_still_uses_decision_heading():
    """LFB-1 (c) REGRESSION GUARD: no fields ⇒ the body stays under `## Decision`.

    The field-less MM `· LOCKED` form is load-bearing for other ledgers; it must
    NOT be relabelled to `## Detail` by the additive-body fix.
    """
    _, content = _render(_entry(fields={}, body="The recorded resolution text."))
    assert "## Decision\n" in content
    assert "The recorded resolution text." in content
    assert "## Detail" not in content


def test_render_neither_fields_nor_body_emits_no_section():
    """LFB-1 (d): neither ⇒ unchanged — no Decision, no Detail."""
    _, content = _render(_entry(fields={}, body=""))
    assert "## Decision" not in content
    assert "## Detail" not in content
    assert "# MM-1 — Five role groups" in content  # the page itself still renders


def test_house_style_entry_round_trips_with_substance_intact():
    """LFB-4 (e): a REAL-shaped entry keeps every rejected-alternative bullet.

    Before the fix this page rendered the two parsed fields and silently dropped
    all four body bullets — the whole "why we rejected the alternative" record.
    """
    (entry,) = learn_feed.parse_grill_ledger(HOUSE_STYLE_ENTRY)
    assert entry["status"] == "resolved"
    # the bold-prefix fields still parse exactly as before
    assert entry["fields"]["decision"].startswith("the pinned clause")
    assert entry["fields"]["rationale"] == "truncation destroys the prior run's board."
    # ...and the unknown-name bullets are in the body, where the parser puts them
    assert "Rejected — pin the sentence verbatim" in entry["body"]

    # `**Provenance:**` parses to a field but is deliberately NOT a page section
    # (_SECTION_ORDER omits it) — unchanged pre-existing behavior, asserted here so
    # the omission stays a decision rather than becoming a second silent drop.
    assert entry["fields"]["provenance"].startswith("`board.md:45-50`")
    assert "provenance" not in learn_feed._SECTION_ORDER

    _, content = _render(entry)
    assert "## Decision\n" in content and "## Rationale\n" in content
    assert "## Detail\n" in content
    for substance in (
        "harder to remove than to keep",
        "smuggled inside a guarding change",
        "should `(or truncate it)` be removed?",
    ):
        assert substance in content, f"lost from the rendered page: {substance!r}"


# ---------------------------------------------------------------------------
# BL-M24 / LFB-2 — the heading grammar no longer counts a document H1
# ---------------------------------------------------------------------------

def test_heading_grammar_ignores_document_h1():
    """LFB-4 (d): `# GRILL-LEDGER — <spec>` is a title, not an open entry.

    `GRILL-LEDGER` matches `_ANCHOR_RE`, so the old `^#{1,6}` grammar parsed every
    ledger's own H1 as a status-less (⇒ open) entry — the phantom "1 item skipped"
    on every emit. 11 of the 22 repo ledgers were miscounted this way.
    """
    text = (
        "# GRILL-LEDGER — session-lifecycle\n"
        "\n"
        "Intro prose under the title.\n"
        "\n"
        "### SL-1 — a real entry · LOCKED\n"
        "- **Decision:** the real one.\n"
    )
    entries = learn_feed.parse_grill_ledger(text)
    assert [e["anchor"] for e in entries] == ["SL-1"]
    assert not any(e["anchor"] == "GRILL-LEDGER" for e in entries)
    assert sum(1 for e in entries if e["status"] != "resolved") == 0  # no phantom skip


def test_heading_regex_requires_at_least_h2():
    assert learn_feed._HEADING_LINE_RE.match("# GRILL-LEDGER — x") is None
    assert learn_feed._HEADING_LINE_RE.match("## Resolved branches") is not None
    assert learn_feed._HEADING_LINE_RE.match("###### deep") is not None


def test_decisions_record_terminator_still_matches_h1():
    """The DECISIONS record terminator is a SEPARATE regex and still ends on H1.

    Narrowing it alongside the entry grammar would silently vacuum a mid-file
    `# Heading` into the preceding record's body.
    """
    text = (
        "- **D1 — first.** body line\n"
        "# A new H1 section\n"
        "- **D2 — second.** other body\n"
    )
    entries = {e["anchor"]: e for e in learn_feed.parse_decisions_bullets(text)}
    assert entries["D1"]["body"] == "body line"
    assert "A new H1 section" not in entries["D1"]["body"]
    assert entries["D2"]["body"] == "other body"


def test_real_ledgers_lose_no_entry_bodies():
    """LFB-4 proof, pinned as a test: ZERO dropped bodies across every real ledger.

    Mirrors `render_page`'s real condition (fields nested under `entry["fields"]`;
    a drop is `body_text and present`). Against the pre-fix renderer this same
    scan reported 68 dropped entries / 46,427 characters over 22 ledgers.
    """
    specs = _REPO_ROOT / ".planning" / "specs"
    ledgers = sorted(specs.glob("*/GRILL-LEDGER.md"), key=lambda p: p.as_posix())
    if not ledgers:
        pytest.skip("no real ledgers present")
    dropped = []
    scanned = 0
    for led in ledgers:
        for e in learn_feed.parse_grill_ledger(led.read_text(encoding="utf-8")):
            fields = e.get("fields") or {}
            present = [k for k in learn_feed._SECTION_ORDER if str(fields.get(k) or "").strip()]
            body = str(e.get("body") or "").strip()
            if not (body and present):
                continue  # not the DEF-2 shape
            scanned += 1
            _, content = _render(e, source_path=led.as_posix())
            # the drop was structural: the body got no section at all
            if "## Detail\n" not in content:
                dropped.append(f"{led.parent.name}:{e['anchor']}")
    assert scanned > 0, "the DEF-2 shape vanished from the corpus — probe is no longer meaningful"
    assert dropped == [], f"{len(dropped)} entries still lose their body: {dropped[:5]}"


def test_real_ledgers_have_no_phantom_h1_entry():
    """BL-M24 proof: no ledger's own H1 title is parsed as an entry any more."""
    specs = _REPO_ROOT / ".planning" / "specs"
    ledgers = sorted(specs.glob("*/GRILL-LEDGER.md"), key=lambda p: p.as_posix())
    if not ledgers:
        pytest.skip("no real ledgers present")
    phantoms = [
        f"{led.parent.name}:{e['anchor']}"
        for led in ledgers
        for e in learn_feed.parse_grill_ledger(led.read_text(encoding="utf-8"))
        if e["anchor"] == "GRILL-LEDGER"
    ]
    assert phantoms == []


def test_render_wikilink_to_raw_artifact():
    _, content = _render()
    assert "[[.planning/specs/x/GRILL-LEDGER.md]]" in content


def test_render_backslash_source_normalized():
    _, content = _render(source_path=".planning\\specs\\x\\GRILL-LEDGER.md")
    assert "[[.planning/specs/x/GRILL-LEDGER.md]]" in content
    assert "\\" not in content


def test_render_lf_only():
    _, content = _render()
    assert "\r" not in content
    assert content.endswith("\n")


def test_render_no_redactions_key_when_zero():
    _, content = _render()
    assert "redactions:" not in content


# ---------------------------------------------------------------------------
# BL-X12 — bullet-form grill ledgers: an OPEN QUESTION never emits as a decision
# ---------------------------------------------------------------------------
# The stack's only live wrong-output defect, four sub-defects, all reproduced by
# the challenger against `.planning/specs/ux-rework/GRILL-LEDGER.md`:
#   (a) the --ledger route returned ZERO entries for bullet-form ledgers;
#   (b) entries whose bold anchor span WRAPS were silently dropped (UX-28/UX-32);
#   (c) the --decisions route hardcodes resolved ⇒ `UX-5 · OPEN QUESTION` emitted
#       into the vault as a decided decision pattern;
#   (d) anchors partitioned on em-dash only ⇒ `UX-1 · Launcher mechanism` as the
#       page key instead of the stable `UX-1`.
# The fixture below mirrors the REAL ledger's shapes: `·`-separated anchor spans,
# spans that wrap across a physical line, a verbatim OPEN QUESTION entry, and the
# `(locked …)` / `Ruling: …` decided forms the real ux-rework · backlog-burn-mode
# · agent-cadre ledgers use.

UX_BULLET_LEDGER = """\
---
spec: ux-rework
status: draft
opened: 2026-08-15
---

# GRILL LEDGER — launcher + UX rework (BL-N06 / BL-N07)

**What this is:** operator rulings from the 2026-08-15 visual design session.

## Operator rulings (2026-08-15)

- **UX-4 · Command copy that survived a real confusion:** `/kata-loop` = *"full cycle: build →
  closeout → improve again"*; `/kata-start` = *"single run: plan and build once, then stop."*

- **UX-5 · OPEN QUESTION (feed to the full grill):** should the LOOP be the only door — "single
  run" becoming a choice inside the guided flow — so users never face two entry commands?

- **UX-12 · The phase-break block is LOCKED.** Structure top-to-bottom, all exactly **64
  columns** (64 is the system-wide measure, shared with the launch banner).

## Full-grill rulings (2026-08-16, the freeze grill)

- **UX-28 · Entry hierarchy — the wrapper commands are the PREFERRED door (operator, 2026-08-16;
  closes the UX-5 open question).** Ruling: keep BOTH in-session commands (`/kata-loop` +
  `/kata-start`, UX-4 copy) — but the preferred manner of execution is the **wrapper shell
  commands**.

- **UX-31 · Wrapper build scope — ALL THREE hosts in one pass (operator, 2026-08-16;
  supersedes the Claude-first sequencing).** RULED: assessed and built together.

- **UX-32 · The launch preload is an OPEN SEAM; third-party packs are placeholders (operator,
  2026-08-16).** The wrapper's environment provisioning is designed as a **pluggable ingestion
  seam** — which packs load is configuration, never hard-wired.
"""


def _ux_bullet_entries() -> dict[str, dict]:
    return {e["anchor"]: e for e in learn_feed.parse_grill_ledger(UX_BULLET_LEDGER)}


def test_bullet_ledger_parses_every_entry():
    """(a)+(b): the bullet-form ledger is no longer invisible, and nothing is dropped."""
    entries = _ux_bullet_entries()
    assert set(entries) == {"UX-4", "UX-5", "UX-12", "UX-28", "UX-31", "UX-32"}


def test_bullet_wrapped_anchor_span_not_dropped():
    """(b): UX-28/UX-31/UX-32 wrap their bold span across a physical line.

    The single-line `_BULLET_RE` never matched these, so they vanished from the
    feed with no note, no count, no error — the silent-drop half of BL-X12.
    """
    entries = _ux_bullet_entries()
    for anchor in ("UX-28", "UX-31", "UX-32"):
        assert anchor in entries, f"{anchor}'s wrapped bold span was dropped again"
    # the wrap is re-joined into ONE title, not truncated at the line break
    assert "closes the UX-5 open question" in entries["UX-28"]["title"]
    assert entries["UX-32"]["title"].endswith("(operator, 2026-08-16)")


def test_bullet_anchor_is_the_stable_short_key():
    """(d): anchors partition on ` · ` as well as ` — ` ⇒ `UX-4`, never `UX-4 · Command copy`."""
    entries = _ux_bullet_entries()
    assert all("·" not in a and " " not in a for a in entries)
    assert entries["UX-4"]["title"].startswith("Command copy that survived")
    # the em-dash form still partitions (UX-28's title keeps its own em-dash text)
    assert entries["UX-28"]["title"].startswith("Entry hierarchy — the wrapper commands")


def test_bullet_open_question_parses_open():
    """(c) THE LIVE DEFECT: a verbatim `OPEN QUESTION` entry is OPEN, never resolved."""
    assert _ux_bullet_entries()["UX-5"]["status"] == "open"


def test_bullet_decided_markers_resolve():
    """Provable decided markers — and ONLY those — resolve (LOCKED / RULED / RULING)."""
    entries = _ux_bullet_entries()
    assert entries["UX-12"]["status"] == "resolved"   # `is LOCKED.` in the title
    assert entries["UX-31"]["status"] == "resolved"   # `RULED:` in the LEAD, wrapped span


def test_bullet_unclassifiable_fails_closed_to_open():
    """FAIL-CLOSED: no marker ⇒ open. Emitting an undecided entry as decided is the harm."""
    entries = _ux_bullet_entries()
    assert entries["UX-4"]["status"] == "open"    # plain ruling prose, no marker
    assert entries["UX-32"]["status"] == "open"   # `OPEN SEAM`, no decided marker


def test_bullet_mentioning_an_open_question_stays_open():
    """The accepted, DOCUMENTED cost of open-marker precedence, pinned so it is not a surprise.

    UX-28 IS a ruling (`Ruling: keep BOTH …` in its lead) — but its own title says
    it *"closes the UX-5 open question"*, so the open marker fires and it parses
    OPEN. That direction is the safe one: a decided entry held open loses signal
    the ledger still holds; an undecided entry emitted as decided writes a lie
    into the second brain. When in doubt, open (BL-X12).
    """
    entries = _ux_bullet_entries()
    assert "open question" in entries["UX-28"]["title"]
    assert entries["UX-28"]["status"] == "open"


def test_bullet_open_marker_beats_a_decided_marker():
    """Precedence pin: an explicit open marker WINS, whatever else the entry says."""
    text = (
        "- **ZZ-1 · OPEN QUESTION — the ruling is LOCKED for everything else.** "
        "RESOLVED elsewhere; this branch is not.\n"
    )
    (entry,) = learn_feed.parse_grill_ledger(text)
    assert entry["status"] == "open"


def test_bullet_status_vocabulary_is_closed():
    """`ACCEPTED` is NOT decided vocabulary — it means *assessment accepted, work owed*.

    Pinned deliberately: the real context-autonomy `R-5 … — ACCEPTED` is already
    held OPEN by the heading grammar (`_CA_OPEN_AT_FREEZE`), and a bullet grammar
    that swallowed the word would promote an unresolved branch into the vault.
    """
    for tail in ("— ACCEPTED.", "· PENDING VETO.", "— RECORDED, still argued.", "· NOTED."):
        (entry,) = learn_feed.parse_grill_ledger(f"- **ZZ-9 {tail}** body prose.\n")
        assert entry["status"] == "open", f"{tail!r} must not read as decided"


def test_bullet_entries_never_disturb_heading_entries():
    """The SB-L1 heading grammar is untouched: a heading entry keeps its own bullets.

    A heading entry's `- **Decision:** …` field bullets must stay fields — they may
    never ALSO be harvested as bullet entries (that would double-count and re-key
    the page).
    """
    entries = learn_feed.parse_grill_ledger(CANONICAL_ENTRY)
    assert [e["anchor"] for e in entries] == ["D7"]
    assert entries[0]["fields"]["decision"].startswith("30 minutes")


def test_bullet_entries_harvested_after_a_non_entry_heading():
    """Mixed file: prose headings own nothing, so their bullets ARE entries."""
    text = (
        "### MM-1 — a locked branch · LOCKED\n"
        "- **Decision:** stay the course.\n"
        "\n"
        "## Operator rulings (a prose heading — owns nothing)\n"
        "\n"
        "- **BBM-13 · Naming is LOCKED.** Documentation says \"Backlog Burn\".\n"
    )
    entries = {e["anchor"]: e for e in learn_feed.parse_grill_ledger(text)}
    assert set(entries) == {"MM-1", "BBM-13"}
    assert entries["MM-1"]["fields"] == {"decision": "stay the course."}
    assert entries["BBM-13"]["status"] == "resolved"


def test_bullet_bold_lead_in_is_not_an_entry():
    """A bold lead-in with no anchor token is prose, not an entry (no phantom pages)."""
    text = (
        "- **Refined (operator, 2026-08-16):** section headers speak PLAIN language.\n"
        "- **What this is:** operator rulings, LOCKED.\n"
    )
    assert learn_feed.parse_grill_ledger(text) == []


def test_bullet_unterminated_bold_span_is_not_an_entry():
    """Fail-closed on malformed markdown: an unclosed `**` never becomes an entry."""
    text = "- **UX-77 · a span that never closes\n" + "  more prose\n" * 12
    assert learn_feed.parse_grill_ledger(text) == []


def test_bullet_entry_date_from_title_else_frontmatter():
    """Determinism: entry date is mined from the title, else frontmatter — never a clock."""
    entries = _ux_bullet_entries()
    assert entries["UX-28"]["date"] == "2026-08-16"
    assert entries["UX-4"]["date"] is None  # no date in title, no `date:` frontmatter


def test_bullet_ledger_is_deterministic():
    """Doctrine law 2/3: same bytes in ⇒ same entries out, every time."""
    assert learn_feed.parse_grill_ledger(UX_BULLET_LEDGER) == learn_feed.parse_grill_ledger(
        UX_BULLET_LEDGER
    )


# ---------------------------------------------------------------------------
# BL-X12 — the route guard (D136 fail-closed; the parser stays unchanged)
# ---------------------------------------------------------------------------

def test_decisions_parser_semantics_unchanged():
    """PIN: `parse_decisions_bullets` still hardcodes resolved — correct for DECISIONS.md.

    The fix is a ROUTE guard, not a status vocabulary in this parser: by
    DECISIONS.md's own contract every bullet in it IS a decided decision. This
    test exists so a future "fix" that adds a status vocabulary here reds.
    """
    entries = learn_feed.parse_decisions_bullets(
        "- **D1 — an open question we never resolved.** still argued.\n"
    )
    assert [e["status"] for e in entries] == ["resolved"]


def test_grill_ledger_marker_detects_spec_frontmatter():
    reason = learn_feed.grill_ledger_marker("notes/rulings.md", UX_BULLET_LEDGER)
    assert reason and "spec" in reason


def test_grill_ledger_marker_detects_filename():
    reason = learn_feed.grill_ledger_marker(
        ".planning/specs/x/GRILL-LEDGER.md", "- **D1 — no frontmatter.** body.\n"
    )
    assert reason and "grill ledger" in reason


def test_grill_ledger_marker_passes_a_real_decisions_file():
    """DECISIONS.md — no `spec:` key, no ledger filename — is NOT refused."""
    assert learn_feed.grill_ledger_marker("C:\\repo\\.planning\\DECISIONS.md", BULLET_ONLY) is None


def test_cli_decisions_route_refuses_a_grill_ledger(tmp_path, capsys):
    """(c) at the route layer: the misclassification is REFUSED, never silent (D136)."""
    spec_dir = tmp_path / "ux-rework"
    spec_dir.mkdir()
    ledger = spec_dir / "GRILL-LEDGER.md"
    ledger.write_text(UX_BULLET_LEDGER, encoding="utf-8")
    feed = tmp_path / "feed"
    rc = learn_feed.main([
        "--decisions", str(ledger), "--feed-dir", str(feed),
        "--log-path", str(tmp_path / "log.md"), "--project", "demo", "--kind", "project",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--ledger" in err          # the message NAMES the correct route
    assert "OPEN QUESTIONS" in err    # ...and why this matters
    assert not feed.exists()          # all-or-nothing: nothing was emitted


def test_cli_decisions_route_refuses_spec_frontmatter_under_any_name(tmp_path, capsys):
    """The frontmatter mark stands alone — a renamed ledger is refused just the same."""
    target = tmp_path / "rulings.md"
    target.write_text(UX_BULLET_LEDGER, encoding="utf-8")
    rc = learn_feed.main([
        "--decisions", str(target), "--feed-dir", str(tmp_path / "feed"),
        "--log-path", str(tmp_path / "log.md"), "--project", "demo", "--kind", "project",
    ])
    assert rc == 2
    assert "--ledger" in capsys.readouterr().err


def test_cli_ledger_route_emits_only_the_decided_entries(tmp_path, capsys):
    """End-to-end: the same ledger through --ledger emits decided entries ONLY."""
    ledger, feed, logp = _cli_args(tmp_path, ledger_text=UX_BULLET_LEDGER)
    rc = learn_feed.main([
        "--ledger", str(ledger), "--feed-dir", str(feed), "--log-path", str(logp),
        "--project", "demo", "--kind", "project", "--json",
    ])
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["written"] == 2              # UX-12 · UX-31
    assert report["parsed_open_skipped"] == 4  # UX-4 · UX-5 · UX-28 · UX-32
    pages = sorted(p.name for p in (feed / "decision-patterns").iterdir())
    assert pages == ["demo--demo-spec--ux-12.md", "demo--demo-spec--ux-31.md"]
    # (d): the page key is the stable short anchor, not a whole title
    assert not (feed / "decision-patterns" / "demo--demo-spec--ux-5.md").exists()


# ---------------------------------------------------------------------------
# BL-X12 — the challenger's LIVE reproduction, pinned as a regression
# ---------------------------------------------------------------------------

_UX_LEDGER = _REPO_ROOT / ".planning" / "specs" / "ux-rework" / "GRILL-LEDGER.md"
# Recorded at fix time (2026-08-16) against the real file: 33 bullet entries, of
# which 9 carry a provable decided marker. FLOORS, not pins — the ledger is a
# LIVING file and a later grill may add entries or resolve open ones.
_UX_ANCHORS_AT_FIX = {f"UX-{n}" for n in range(1, 34)}
_UX_OPEN_AT_FIX = {"UX-5", "UX-32"}


@pytest.mark.skipif(not _UX_LEDGER.exists(), reason="real ux-rework ledger not present")
def test_real_ux_ledger_open_question_is_not_a_decision():
    """The challenger's reproduction, verbatim: run the emitter's parser at the real file.

    Before the fix: `--ledger` returned 0 entries, and `--decisions` returned 31
    of 33 (UX-28 + UX-32 silently dropped) with ALL 31 marked resolved — including
    the entry titled `UX-5 · OPEN QUESTION (feed to the full grill)`.
    """
    entries = learn_feed.parse_grill_ledger(_UX_LEDGER.read_text(encoding="utf-8"))
    by_anchor = {e["anchor"]: e for e in entries}
    # (a) the ledger is visible at all; (b) nothing is dropped
    assert set(by_anchor) >= _UX_ANCHORS_AT_FIX, (
        f"lost anchors: {sorted(_UX_ANCHORS_AT_FIX - set(by_anchor))}"
    )
    for anchor in ("UX-28", "UX-32"):
        assert anchor in by_anchor, f"{anchor} is dropped again (wrapped bold span)"
    # (c) the live defect: the OPEN QUESTION is open, and NOTHING titled
    # "OPEN QUESTION" is anywhere in the resolved set
    assert by_anchor["UX-5"]["status"] == "open"
    resolved = [e for e in entries if e["status"] == "resolved"]
    assert not [e for e in resolved if "OPEN QUESTION" in e["title"].upper()], (
        "an OPEN QUESTION is being emitted as a decision pattern again"
    )
    # open-side floor (one-directional floors above cannot catch a promotion)
    still_open = {e["anchor"] for e in entries if e["status"] == "open"}
    assert still_open >= _UX_OPEN_AT_FIX, (
        f"promoted un-decided entries: {sorted(_UX_OPEN_AT_FIX - still_open)}"
    )
    # (d) every page key is the stable short anchor
    assert all(" " not in a and "·" not in a for a in by_anchor)
    # and the honest split is real on both sides — not vacuously all-open
    assert resolved, "no entry resolves at all — the marker set has stopped matching"


@pytest.mark.skipif(not _UX_LEDGER.exists(), reason="real ux-rework ledger not present")
def test_real_ux_ledger_is_refused_by_the_decisions_route(tmp_path, capsys):
    """The route the challenger actually ran is now closed at the door."""
    rc = learn_feed.main([
        "--decisions", _UX_LEDGER.as_posix(), "--feed-dir", str(tmp_path / "feed"),
        "--log-path", str(tmp_path / "log.md"), "--project", "KataHarness",
        "--kind", "project",
    ])
    assert rc == 2
    assert "--ledger" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# SB-L4 — redaction (deterministic scrub; never blocks)
# ---------------------------------------------------------------------------

def test_redact_all_classes():
    text = (
        "key AKIAABCDEFGHIJKLMNOP and github_pat_11ABCDEF_x9 and\n"
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "password: hunter2 token=abc123 secret: s3cr3t"
    )
    scrubbed, counts = learn_feed.redact(text)
    assert "AKIAABCDEFGHIJKLMNOP" not in scrubbed
    assert "github_pat_11ABCDEF_x9" not in scrubbed
    assert "PRIVATE KEY" not in scrubbed
    assert "hunter2" not in scrubbed and "abc123" not in scrubbed and "s3cr3t" not in scrubbed
    assert "[REDACTED:aws-key]" in scrubbed
    assert "[REDACTED:github-pat]" in scrubbed
    assert "[REDACTED:private-key]" in scrubbed
    assert "[REDACTED:password]" in scrubbed
    assert "[REDACTED:token]" in scrubbed
    assert "[REDACTED:secret]" in scrubbed
    assert sum(counts.values()) == 6


def test_redact_clean_text_untouched():
    text = "trigger = 0.70 × prime frame; total_tokens counted; secret-hygiene note."
    scrubbed, counts = learn_feed.redact(text)
    assert scrubbed == text
    assert counts == {}


# ----- RS-M7: the class-table EXTENSION (trust-model close-machinery) -----
#
# One scrub, two call points.  These tests bind the CLASSES; the two call points and
# their (different) blocking postures are tested in tests/test_kata_close.py.

@pytest.mark.parametrize("cls,sample,secret", [
    ("anthropic-key", "use sk-ant-api03-AbCdEf0123456789xyz now", "sk-ant-api03-AbCdEf0123456789xyz"),
    ("openai-key", "OPENAI sk-abcdefghijklmnopqrstuvwx here", "sk-abcdefghijklmnopqrstuvwx"),
    ("google-api-key", "AIzaSyA1234567890abcdefghijklmnopqrstuv x", "AIzaSyA1234567890abcdefghijklmnopqrstuv"),
    ("slack-token", "xoxb-1234567890-abcdefghij done", "xoxb-1234567890-abcdefghij"),
    ("jwt", "auth eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NX0.dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1g end",
     "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NX0.dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1g"),
    ("connection-string", "postgres://svc:hunter2@db.internal/x", "postgres://svc:hunter2@"),
    ("bearer", "Authorization: Bearer abcdefghijklmnop.qrst", "Bearer abcdefghijklmnop.qrst"),
    ("api-key", "api_key = ABCDEFGHIJ", "ABCDEFGHIJ"),
    ("credential", "client_secret: zzz-9999-yyy", "zzz-9999-yyy"),
])
def test_redact_extension_classes(cls, sample, secret):
    """Each RS-M7 class is detected, named, and its value removed."""
    scrubbed, counts = learn_feed.redact(sample)
    assert secret not in scrubbed, f"{cls}: the value survived the scrub"
    assert f"[REDACTED:{cls}]" in scrubbed, f"{cls}: wrong class name recorded"
    assert counts.get(cls, 0) >= 1


def test_redact_extension_preserves_the_original_six_apply_order():
    """BC: the first six classes keep their names, order, and counts (rows 1-6 unmoved)."""
    names = [cls for cls, _ in learn_feed._REDACTION_PATTERNS]
    assert names[:6] == [
        "aws-key", "github-pat", "private-key", "password", "token", "secret"
    ]
    text = "AKIAABCDEFGHIJKLMNOP password: hunter2 token=abc123 secret: s3cr3t"
    _, counts = learn_feed.redact(text)
    assert counts == {"aws-key": 1, "password": 1, "token": 1, "secret": 1}


def test_redact_extension_is_deterministic_same_input_same_bytes():
    """Doctrine: the scrub is a fixed-order pass; two runs produce identical bytes."""
    text = "sk-ant-api03-AAAAAAAAAAAAAAAAAA and api_key = QQQQQQQQQQ and Bearer aaaaaaaaaaaa.bb"
    first = learn_feed.redact(text)
    second = learn_feed.redact(text)
    assert first == second


def test_redact_extension_does_not_fire_on_ordinary_prose():
    """Over-firing is a real cost: a scrub that eats normal text trains people to ignore it."""
    text = (
        "The api key registry is documented in protocol/config.md; the bearer of the "
        "token contract is the seam. See https://example.com/docs and sk-ip the rest."
    )
    scrubbed, counts = learn_feed.redact(text)
    assert counts == {}
    assert scrubbed == text


def test_redact_never_raises_on_pathological_input():
    """ReDoS-safety by construction: bounded quantifiers, linear scan, no nesting."""
    text = ("a" * 20000) + " Bearer " + ("b" * 20000) + " sk-" + ("c" * 20000)
    scrubbed, counts = learn_feed.redact(text)
    assert isinstance(scrubbed, str) and isinstance(counts, dict)


def test_render_redacts_and_marks_never_blocks():
    """SB-L4: the page is still emitted, scrubbed, with frontmatter redactions: N."""
    entry = _entry(body="the value was password: hunter2 in the log")
    relpath, content = _render(entry)
    assert relpath.endswith(".md")           # page produced — redaction never blocks
    assert "hunter2" not in content
    assert "[REDACTED:password]" in content
    assert "redactions: 1\n" in content      # counted in page frontmatter


# ---------------------------------------------------------------------------
# SB-L1/SB-L3 — emit: atomic writes, idempotency, refuse-overwrite, guards, log
# ---------------------------------------------------------------------------

def _feed(tmp_path):
    return tmp_path / "feed", tmp_path / "logs" / "log.md"


def test_emit_writes_pages_and_report(tmp_path):
    feed, logp = _feed(tmp_path)
    pages = [_render(_entry(anchor=a)) for a in ("MM-1", "MM-2")]
    report = learn_feed.emit(feed, pages, log_path=logp, now=NOW)
    assert report == {"written": 2, "skipped_identical": 0, "redactions": 0, "parsed_open_skipped": 0}
    assert (feed / "decision-patterns" / "kataharness--x--mm-1.md").exists()
    assert (feed / "decision-patterns" / "kataharness--x--mm-2.md").exists()


def test_emit_written_lf_only(tmp_path):
    feed, logp = _feed(tmp_path)
    learn_feed.emit(feed, [_render()], log_path=logp, now=NOW)
    raw = (feed / "decision-patterns" / "kataharness--x--mm-1.md").read_bytes()
    assert b"\r" not in raw


def test_emit_atomic_temp_rename(tmp_path, monkeypatch):
    """Mutation proof: the write mechanism IS temp+os.replace in the target dir."""
    feed, logp = _feed(tmp_path)
    calls = []
    real_replace = os.replace

    def spy(src, dst):
        calls.append((str(src), str(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(learn_feed.os, "replace", spy)
    learn_feed.emit(feed, [_render()], log_path=logp, now=NOW)
    assert len(calls) == 1
    src, dst = calls[0]
    assert src != dst
    assert dst.endswith("kataharness--x--mm-1.md")
    assert Path(src).parent == Path(dst).parent  # sibling temp — same-filesystem rename
    # no orphan temp files left behind
    leftovers = [p for p in (feed / "decision-patterns").iterdir() if not p.name.endswith(".md")]
    assert leftovers == []


def test_emit_idempotent_date_scrubbed(tmp_path):
    """Law 6: identical-content-different-day ⇒ SKIP (date: line scrubbed pre-compare)."""
    feed, logp = _feed(tmp_path)
    day1 = datetime(2026, 7, 11, tzinfo=UTC)
    day2 = datetime(2026, 7, 12, tzinfo=UTC)
    page1 = _render(_entry(date=None), now=day1)
    page2 = _render(_entry(date=None), now=day2)
    assert page1[1] != page2[1]  # only the date: line differs
    r1 = learn_feed.emit(feed, [page1], log_path=logp, now=day1)
    r2 = learn_feed.emit(feed, [page2], log_path=logp, now=day2)
    assert (r1["written"], r1["skipped_identical"]) == (1, 0)
    assert (r2["written"], r2["skipped_identical"]) == (0, 1)
    # the original file is untouched (still day1's date)
    on_disk = (feed / "decision-patterns" / "kataharness--x--mm-1.md").read_text(encoding="utf-8")
    assert "date: 2026-07-11\n" in on_disk


def test_emit_changed_content_overwrites(tmp_path):
    feed, logp = _feed(tmp_path)
    learn_feed.emit(feed, [_render(_entry(body="old text"))], log_path=logp, now=NOW)
    report = learn_feed.emit(feed, [_render(_entry(body="new text"))], log_path=logp, now=NOW)
    assert report["written"] == 1
    on_disk = (feed / "decision-patterns" / "kataharness--x--mm-1.md").read_text(encoding="utf-8")
    assert "new text" in on_disk


def test_emit_refuses_foreign_produced_by(tmp_path):
    """C5 carve-out guard: produced-by ≠ loop ⇒ fail-closed refuse, file untouched."""
    feed, logp = _feed(tmp_path)
    target = feed / "decision-patterns" / "kataharness--x--mm-1.md"
    target.parent.mkdir(parents=True)
    hand_curated = "---\nproduced-by: wiki\n---\n\n# curated\n"
    target.write_text(hand_curated, encoding="utf-8")
    with pytest.raises(ValueError):
        learn_feed.emit(feed, [_render()], log_path=logp, now=NOW)
    assert target.read_text(encoding="utf-8") == hand_curated
    assert not logp.exists()  # nothing written ⇒ no log line


def test_emit_refuses_missing_frontmatter(tmp_path):
    """Fail-closed includes missing/absent frontmatter (unknown provenance)."""
    feed, logp = _feed(tmp_path)
    target = feed / "decision-patterns" / "kataharness--x--mm-1.md"
    target.parent.mkdir(parents=True)
    target.write_text("no frontmatter here\n", encoding="utf-8")
    with pytest.raises(ValueError):
        learn_feed.emit(feed, [_render()], log_path=logp, now=NOW)
    assert target.read_text(encoding="utf-8") == "no frontmatter here\n"


def test_emit_refusal_is_all_or_nothing(tmp_path):
    """The pre-scan refuses BEFORE any page is written (no partial session)."""
    feed, logp = _feed(tmp_path)
    conflict = feed / "decision-patterns" / "kataharness--x--zz-9.md"
    conflict.parent.mkdir(parents=True)
    conflict.write_text("---\nproduced-by: agent\n---\nbody\n", encoding="utf-8")
    pages = [_render(_entry(anchor="AA-1")), _render(_entry(anchor="ZZ-9"))]
    with pytest.raises(ValueError):
        learn_feed.emit(feed, pages, log_path=logp, now=NOW)
    # the innocent page (sorted FIRST) was NOT written either
    assert not (feed / "decision-patterns" / "kataharness--x--aa-1.md").exists()


def test_emit_overwrites_own_loop_pages(tmp_path):
    """produced-by: loop pages are regenerable derived views — overwrite allowed."""
    feed, logp = _feed(tmp_path)
    learn_feed.emit(feed, [_render(_entry(body="v1"))], log_path=logp, now=NOW)
    report = learn_feed.emit(feed, [_render(_entry(body="v2"))], log_path=logp, now=NOW)
    assert report["written"] == 1


def test_emit_guards_feed_dir_dotdot(tmp_path):
    with pytest.raises(ValueError):
        learn_feed.emit(tmp_path / ".." / "evil", [], log_path=tmp_path / "log.md", now=NOW)


def test_emit_guards_log_path_dotdot_independently(tmp_path):
    """The log path is guarded AS SUPPLIED — independent of a clean feed dir (F-2)."""
    with pytest.raises(ValueError):
        learn_feed.emit(tmp_path / "feed", [], log_path=tmp_path / ".." / "evil.md", now=NOW)


def test_emit_guards_page_relpath_dotdot(tmp_path):
    feed, logp = _feed(tmp_path)
    with pytest.raises(ValueError):
        learn_feed.emit(feed, [("../escape.md", "x\n")], log_path=logp, now=NOW)


def test_emit_zero_pages_no_log_line(tmp_path):
    """Zero-page emit appends NO log line (the log records actual writes only, F-2)."""
    feed, logp = _feed(tmp_path)
    report = learn_feed.emit(feed, [], log_path=logp, now=NOW)
    assert report["written"] == 0
    assert not logp.exists()


def test_emit_all_skipped_no_log_line(tmp_path):
    feed, logp = _feed(tmp_path)
    page = _render()
    learn_feed.emit(feed, [page], log_path=logp, now=NOW)
    first_log = logp.read_text(encoding="utf-8")
    learn_feed.emit(feed, [page], log_path=logp, now=NOW)  # identical ⇒ written=0
    assert logp.read_text(encoding="utf-8") == first_log   # no second line


def test_emit_log_line_once_per_writing_session(tmp_path):
    feed, logp = _feed(tmp_path)
    pages = [_render(_entry(anchor=a)) for a in ("MM-1", "MM-2", "MM-3")]
    report = learn_feed.emit(feed, pages, log_path=logp, now=NOW, parsed_open_skipped=2)
    text = logp.read_text(encoding="utf-8")
    assert text.count("\n") == 1                # ONE line per emit session
    assert "written=3" in text
    assert "parsed_open_skipped=2" in text
    assert "2026-07-12" in text                 # injected now, not wall clock
    assert report["parsed_open_skipped"] == 2


def test_emit_report_sums_page_redactions(tmp_path):
    feed, logp = _feed(tmp_path)
    page = _render(_entry(body="password: hunter2 and token=abc"))
    report = learn_feed.emit(feed, [page], log_path=logp, now=NOW)
    assert report["redactions"] == 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CLI_LEDGER = """\
### D1 — pick the parser — RESOLVED 2026-07-01
- **Question:** which grammar?
- **Decision:** heading entries only.

### D2 — cache policy · open
- still being argued.
"""


def _cli_args(tmp_path, ledger_text=CLI_LEDGER):
    # Nest under a named spec dir so the source-slug is deterministic (`demo-spec`).
    spec_dir = tmp_path / "demo-spec"
    spec_dir.mkdir()
    ledger = spec_dir / "GRILL-LEDGER.md"
    ledger.write_text(ledger_text, encoding="utf-8")
    feed = tmp_path / "feed"
    logp = tmp_path / "wiki" / "log.md"
    return ledger, feed, logp


def test_cli_end_to_end(tmp_path, capsys):
    ledger, feed, logp = _cli_args(tmp_path)
    rc = learn_feed.main([
        "--ledger", str(ledger), "--feed-dir", str(feed), "--log-path", str(logp),
        "--project", "demo", "--kind", "project", "--json",
    ])
    assert rc == 0
    out, err = capsys.readouterr()
    report = json.loads(out)
    assert report["written"] == 1
    assert report["parsed_open_skipped"] == 1  # D2 (· open) NOT emitted, counted
    assert "learn-feed:" in err                # human summary on stderr
    page = feed / "decision-patterns" / "demo--demo-spec--d1.md"
    assert page.exists()
    content = page.read_text(encoding="utf-8")
    assert "produced-by: loop" in content
    assert "kata/decision-pattern/coding" in content
    assert logp.read_text(encoding="utf-8").count("\n") == 1


def test_cli_json_sort_keys(tmp_path, capsys):
    ledger, feed, logp = _cli_args(tmp_path)
    rc = learn_feed.main([
        "--ledger", str(ledger), "--feed-dir", str(feed), "--log-path", str(logp),
        "--project", "demo", "--kind", "project", "--json",
    ])
    assert rc == 0
    out, _ = capsys.readouterr()
    keys = list(json.loads(out).keys())
    assert keys == sorted(keys)  # sort_keys=True on the stdout report


def test_cli_decisions_backfill(tmp_path, capsys):
    decisions = tmp_path / "DECISIONS.md"
    decisions.write_text(BULLET_ONLY, encoding="utf-8")
    feed = tmp_path / "feed"
    logp = tmp_path / "log.md"
    rc = learn_feed.main([
        "--decisions", str(decisions), "--feed-dir", str(feed), "--log-path", str(logp),
        "--project", "demo", "--kind", "project", "--json",
    ])
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["written"] == 2  # F-10: backfill volume accepted, not capped
    # --decisions pins the literal `decisions` source-slug (defect 1)
    assert (feed / "decision-patterns" / "demo--decisions--d1.md").exists()
    assert (feed / "decision-patterns" / "demo--decisions--d2.md").exists()


def test_cli_requires_project(tmp_path):
    ledger, feed, logp = _cli_args(tmp_path)
    with pytest.raises(SystemExit):
        learn_feed.main([
            "--ledger", str(ledger), "--feed-dir", str(feed), "--log-path", str(logp),
            "--kind", "project",
        ])


def test_cli_requires_an_input(tmp_path):
    feed = tmp_path / "feed"
    with pytest.raises(SystemExit):
        learn_feed.main([
            "--feed-dir", str(feed), "--log-path", str(tmp_path / "log.md"),
            "--project", "demo", "--kind", "project",
        ])


def test_cli_dotdot_path_is_error_exit(tmp_path, capsys):
    ledger, feed, logp = _cli_args(tmp_path)
    rc = learn_feed.main([
        "--ledger", str(ledger), "--feed-dir", str(tmp_path / ".." / "evil"),
        "--log-path", str(logp), "--project", "demo", "--kind", "project",
    ])
    assert rc == 2
    assert "learn-feed:" in capsys.readouterr().err


def test_cli_bullet_only_ledger_parsed_but_not_emitted(tmp_path, capsys):
    """BL-X12 (a): the bullets are SEEN (counted open) and still emit nothing.

    Pre-BL-X12 this asserted the `0 heading entries` note — the CLI's honest
    report of a blindness that is now fixed. The entries parse; neither carries a
    decided marker; both land in `parsed_open_skipped`.
    """
    ledger, feed, logp = _cli_args(tmp_path, ledger_text=BULLET_ONLY)
    rc = learn_feed.main([
        "--ledger", str(ledger), "--feed-dir", str(feed), "--log-path", str(logp),
        "--project", "demo", "--kind", "project", "--json",
    ])
    assert rc == 0
    out, err = capsys.readouterr()
    report = json.loads(out)
    assert report["written"] == 0
    assert report["parsed_open_skipped"] == 2
    assert "0 entries" not in err  # the blind-scope note no longer applies


def test_cli_truly_empty_ledger_still_noted(tmp_path, capsys):
    """The honest-scope note survives for a ledger with NO parseable entry at all."""
    ledger, feed, logp = _cli_args(tmp_path, ledger_text="# Notes\n\nprose only.\n")
    rc = learn_feed.main([
        "--ledger", str(ledger), "--feed-dir", str(feed), "--log-path", str(logp),
        "--project", "demo", "--kind", "project", "--json",
    ])
    assert rc == 0
    assert "0 entries" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Real-ledger integration (the actual files, when present in the repo)
# ---------------------------------------------------------------------------

# The two real ledgers are LIVING files: a grill can append a new anchor, and an
# `· open` entry can later be resolved. Both are legitimate change, so these
# integration probes assert FLOORS over the historically-recorded anchors rather
# than exact pins (BL-X05; same shape as the semver floor in
# test_validate_prime_directives.py). What CANNOT legitimately change: a recorded
# anchor disappearing, a resolved entry reverting to open, an anchor landing in
# two statuses, or a status outside the parser's two-value vocabulary.
_MM_LOCKED_AT_FREEZE = {f"MM-{n}" for n in range(1, 12)}
_CA_RESOLVED_AT_FREEZE = {"R-1", "R-2", "R-3", "R-7", "R-8", "R-9", "R-10", "R-11", "R-13"}
# The status-shaped-but-NOT-resolved headings: `R-5 (CA-11) Installer fix — ACCEPTED`
# and `R-43 — Delta-gate v6 fold (grill CLOSED after this entry)`. Neither word is in
# the parser's vocabulary, and neither may drift into it.
_CA_OPEN_AT_FREEZE = {"R-5", "R-43"}
_CA_KNOWN_AT_FREEZE = _CA_RESOLVED_AT_FREEZE | _CA_OPEN_AT_FREEZE | {"R-4", "R-6", "R-12"}
_STATUS_VOCABULARY = {"resolved", "open"}


@pytest.mark.skipif(not _MM_LEDGER.exists(), reason="real MM ledger not present")
def test_real_mm_ledger_locked_entries_stay_resolved():
    entries = learn_feed.parse_grill_ledger(_MM_LEDGER.read_text(encoding="utf-8"))
    resolved = {e["anchor"] for e in entries if e["status"] == "resolved"}
    # FLOOR: the eleven `· LOCKED` branches must all still parse as resolved. A
    # twelfth MM entry is growth, not a regression, so it must not red this.
    assert resolved >= _MM_LOCKED_AT_FREEZE, (
        f"MM ledger lost locked entries: {sorted(_MM_LOCKED_AT_FREEZE - resolved)}"
    )
    # Parser sanity, regenerable: every parsed anchor is a real anchor TOKEN. (Pre
    # BL-X12 this pinned `startswith("MM-")`; the ledger's `- **N1 · …**` build-slice
    # bullets now parse too — as OPEN — so the token grammar is the honest invariant.
    # The resolved floor above is what protects the MM-n branches.)
    assert entries and all(learn_feed._ANCHOR_RE.match(e["anchor"]) for e in entries)
    assert resolved <= {e["anchor"] for e in entries if e["anchor"].startswith("MM-")}


@pytest.mark.skipif(not _CA_LEDGER.exists(), reason="real context-autonomy ledger not present")
def test_real_context_autonomy_ledger_statuses():
    entries = learn_feed.parse_grill_ledger(_CA_LEDGER.read_text(encoding="utf-8"))
    by_status: dict[str, set[str]] = {}
    for e in entries:
        by_status.setdefault(e["status"], set()).add(e["anchor"])
    resolved = by_status.get("resolved", set())
    still_open = by_status.get("open", set())
    assert set(by_status) <= _STATUS_VOCABULARY, f"unknown status parsed: {set(by_status)}"
    # FLOOR: everything resolved at freeze stays resolved (resolution is one-way)...
    assert resolved >= _CA_RESOLVED_AT_FREEZE, (
        f"CA ledger lost resolved entries: {sorted(_CA_RESOLVED_AT_FREEZE - resolved)}"
    )
    # ...and no recorded anchor may vanish, whichever bucket it now sits in.
    # (`· open` ⇒ open classification itself is pinned on fixtures above.)
    assert (resolved | still_open) >= _CA_KNOWN_AT_FREEZE, (
        f"CA ledger lost anchors: {sorted(_CA_KNOWN_AT_FREEZE - (resolved | still_open))}"
    )
    # ...but the floor above is one-directional by construction, so it cannot catch
    # a parser change that promotes an OPEN entry. These two are the ledger's
    # unresolved-but-status-shaped headings (`R-5 … — ACCEPTED`, `R-43 — … (grill
    # CLOSED after this entry)`); a vocabulary widening that swallows either word
    # would emit an unresolved branch as a decision pattern. Pinned as an
    # open-side floor — new open anchors are growth and must not red this.
    assert still_open >= _CA_OPEN_AT_FREEZE, (
        f"CA ledger promoted un-resolved entries: {sorted(_CA_OPEN_AT_FREEZE - still_open)}"
    )
    assert not (resolved & still_open), "an anchor cannot be both resolved and open"
    dates = {e["anchor"]: e["date"] for e in entries}
    assert dates["R-1"] == "2026-07-04"  # a recorded date is history, not living state


# ---------------------------------------------------------------------------
# Determinism laws + purity (source/AST scans)
# ---------------------------------------------------------------------------

def test_wall_clock_minted_only_in_main():
    """Law 7: no datetime.now() inside decision logic — only the CLI shell."""
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    offenders = []
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if func.name == "main":
            continue
        for node in ast.walk(func):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "now"
            ):
                offenders.append(func.name)
    assert offenders == []


def test_stdlib_only_imports():
    """SB-L1: stdlib-only — no yaml, no third-party, anywhere (incl. lazy imports)."""
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    allowed = {
        "__future__", "argparse", "json", "os", "re", "sys",
        "tempfile", "datetime", "pathlib",
    }
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    assert mods <= allowed, f"non-stdlib/forbidden imports: {sorted(mods - allowed)}"


def test_no_exec_sinks_no_randomness():
    """AST scan: no subprocess/random/uuid imports; no eval/exec/os.system calls."""
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    banned_mods = {"subprocess", "random", "uuid", "secrets"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not {a.name.split(".")[0] for a in node.names} & banned_mods
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_mods
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                assert f.id not in ("eval", "exec", "compile"), f"exec sink: {f.id}"
            if isinstance(f, ast.Attribute):
                assert f.attr != "system", "os.system call found"


def test_guard_path_rejects_dotdot_component():
    with pytest.raises(ValueError):
        learn_feed._guard_path("a/../b")
    # a plain relative or absolute path without '..' passes
    assert learn_feed._guard_path("feed/dir") == Path("feed/dir")
