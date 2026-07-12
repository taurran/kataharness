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
               trailing text; `· open`/no-status ⇒ open, NOT emitted; bullet-only
               ledgers ⇒ zero entries; bold-field bullets tolerant (any subset);
               parse_decisions_bullets (recall _BULLET_RE family).
SB-L2 render:  relpath `decision-patterns/<project-slug>--<anchor-slug>.md`;
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
CA_EXCERPT = """\
### R-1 (CA-1c) Threshold policy — RESOLVED 2026-07-04
Operator: 70% default, "fine no matter how much it really is," surfaced as a configurable
recommendation at configuration; default stands.

### R-3 (CA-7a) Fable gate — RESOLVED core + NEW above-anchor concept; one sub-Q open
Option A confirmed (decline => pin anchor opus + hard-stop advising /model switch).

### R-4 (statusline discovery) — NO OPERATOR ACTION; design mandate stands
Operator's own statusline works and stays untouched.

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
    status token) ⇒ resolved; `— NO OPERATOR ACTION` / `— RECORDED PENDING VETO` /
    no status ⇒ open.
    """
    entries = {e["anchor"]: e for e in learn_feed.parse_grill_ledger(CA_EXCERPT)}
    assert entries["R-1"]["status"] == "resolved"
    assert entries["R-1"]["date"] == "2026-07-04"  # trailing entry date captured
    assert entries["R-3"]["status"] == "resolved"  # trailing text after RESOLVED
    assert entries["R-4"]["status"] == "open"
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


def test_parse_bullet_only_ledger_zero_entries():
    """Bullet-form ledgers (no ### entries) parse to ZERO entries — honest scope."""
    assert learn_feed.parse_grill_ledger(BULLET_ONLY) == []


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
# SB-L2 / SB-L3 — render_page
# ---------------------------------------------------------------------------

def test_render_relpath_deterministic():
    relpath, _ = _render()
    assert relpath == "decision-patterns/kataharness--mm-1.md"


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
    assert (feed / "decision-patterns" / "kataharness--mm-1.md").exists()
    assert (feed / "decision-patterns" / "kataharness--mm-2.md").exists()


def test_emit_written_lf_only(tmp_path):
    feed, logp = _feed(tmp_path)
    learn_feed.emit(feed, [_render()], log_path=logp, now=NOW)
    raw = (feed / "decision-patterns" / "kataharness--mm-1.md").read_bytes()
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
    assert dst.endswith("kataharness--mm-1.md")
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
    on_disk = (feed / "decision-patterns" / "kataharness--mm-1.md").read_text(encoding="utf-8")
    assert "date: 2026-07-11\n" in on_disk


def test_emit_changed_content_overwrites(tmp_path):
    feed, logp = _feed(tmp_path)
    learn_feed.emit(feed, [_render(_entry(body="old text"))], log_path=logp, now=NOW)
    report = learn_feed.emit(feed, [_render(_entry(body="new text"))], log_path=logp, now=NOW)
    assert report["written"] == 1
    on_disk = (feed / "decision-patterns" / "kataharness--mm-1.md").read_text(encoding="utf-8")
    assert "new text" in on_disk


def test_emit_refuses_foreign_produced_by(tmp_path):
    """C5 carve-out guard: produced-by ≠ loop ⇒ fail-closed refuse, file untouched."""
    feed, logp = _feed(tmp_path)
    target = feed / "decision-patterns" / "kataharness--mm-1.md"
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
    target = feed / "decision-patterns" / "kataharness--mm-1.md"
    target.parent.mkdir(parents=True)
    target.write_text("no frontmatter here\n", encoding="utf-8")
    with pytest.raises(ValueError):
        learn_feed.emit(feed, [_render()], log_path=logp, now=NOW)
    assert target.read_text(encoding="utf-8") == "no frontmatter here\n"


def test_emit_refusal_is_all_or_nothing(tmp_path):
    """The pre-scan refuses BEFORE any page is written (no partial session)."""
    feed, logp = _feed(tmp_path)
    conflict = feed / "decision-patterns" / "kataharness--zz-9.md"
    conflict.parent.mkdir(parents=True)
    conflict.write_text("---\nproduced-by: agent\n---\nbody\n", encoding="utf-8")
    pages = [_render(_entry(anchor="AA-1")), _render(_entry(anchor="ZZ-9"))]
    with pytest.raises(ValueError):
        learn_feed.emit(feed, pages, log_path=logp, now=NOW)
    # the innocent page (sorted FIRST) was NOT written either
    assert not (feed / "decision-patterns" / "kataharness--aa-1.md").exists()


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
    ledger = tmp_path / "GRILL-LEDGER.md"
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
    page = feed / "decision-patterns" / "demo--d1.md"
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
    assert (feed / "decision-patterns" / "demo--d1.md").exists()
    assert (feed / "decision-patterns" / "demo--d2.md").exists()


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


def test_cli_bullet_only_ledger_reported(tmp_path, capsys):
    ledger, feed, logp = _cli_args(tmp_path, ledger_text=BULLET_ONLY)
    rc = learn_feed.main([
        "--ledger", str(ledger), "--feed-dir", str(feed), "--log-path", str(logp),
        "--project", "demo", "--kind", "project", "--json",
    ])
    assert rc == 0
    out, err = capsys.readouterr()
    assert json.loads(out)["written"] == 0
    assert "0 heading entries" in err  # honest-scope note


# ---------------------------------------------------------------------------
# Real-ledger integration (the actual files, when present in the repo)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _MM_LEDGER.exists(), reason="real MM ledger not present")
def test_real_mm_ledger_all_eleven_locked():
    entries = learn_feed.parse_grill_ledger(_MM_LEDGER.read_text(encoding="utf-8"))
    resolved = [e["anchor"] for e in entries if e["status"] == "resolved"]
    assert resolved == [f"MM-{n}" for n in range(1, 12)]


@pytest.mark.skipif(not _CA_LEDGER.exists(), reason="real context-autonomy ledger not present")
def test_real_context_autonomy_ledger_statuses():
    entries = learn_feed.parse_grill_ledger(_CA_LEDGER.read_text(encoding="utf-8"))
    by_status = {}
    for e in entries:
        by_status.setdefault(e["status"], set()).add(e["anchor"])
    assert by_status.get("resolved") == {
        "R-1", "R-2", "R-3", "R-7", "R-8", "R-9", "R-10", "R-11", "R-13",
    }
    assert by_status.get("open") == {"R-4", "R-5", "R-6", "R-12", "R-43"}
    dates = {e["anchor"]: e["date"] for e in entries}
    assert dates["R-1"] == "2026-07-04"


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
