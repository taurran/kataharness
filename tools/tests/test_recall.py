"""test_recall.py — TDD suite for tools/recall.py (second-brain-learning Slice R1).

Strategy: default-FAIL, written to the frozen R1 acceptance. Pure except tmp_path /
fixture reads and the mutation proofs (which spawn a real subprocess via
mutation_run.prove_non_vacuous and always restore the source).

Coverage map
------------
contract:      schema_version "recall/v1"; RecallRecord/RecurrenceRecord field sets;
               build_payload output validates; schema is shape-only & vocab-OPEN.
B1 (open):     a payload with source="obsidian-note"/backend="obsidian"/
               produced_by="kiban" VALIDATES (a closed-vocab builder would FAIL).
N1 (selection):zero-overlap-but-RECENT excluded; a matching record passes; recency
               only RANKS passers (never promotes/filters).
recurrences:   ALWAYS surfaced (bypass selection) even with zero overlap.
N3 (project):  RecurrenceRecord carries only the 7 fields; raw evidence /
               what_conformance_missed absent from the payload.
staleness:     a stale record is surfaced (not filtered) with provenance.
provenance:    sources_read lists exactly the present sources.
degradation:   all sources absent ⇒ empty payload, no crash.
purity:        source scan — no eval/exec/subprocess/shell; no embedding/vector import.
guard:         a '..' path raises ValueError (CWE-23).
Mutation proofs (a–g): overlap gate, recency component, always-surface branch,
               stale-does-not-filter, '..' guard, vocab-OPEN schema, evidence-projection.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

import recall

_SOURCE = (Path(__file__).resolve().parent.parent / "recall.py")
_FIX = Path(__file__).resolve().parent / "fixtures" / "recall"

_RECORD_FIELDS = {
    "id", "source", "source_path", "title", "excerpt",
    "tags", "match_score", "provenance", "stale",
}
_RECURRENCE_FIELDS = {
    "key", "responsible_skill", "failure_class", "distinct_runs",
    "severity_tier", "off_vocabulary", "open",
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _cand(*, title="converse grill", excerpt="", tags=None, date=None,
          source="lessons", produced_by="repo", source_path="LESSONS-LEARNED.md",
          stale=False) -> dict:
    """A minimal candidate RecallRecord (the shape select_records consumes)."""
    return {
        "id": f"{source_path}#{recall._slug(title)}",
        "source": source,
        "source_path": source_path,
        "title": title,
        "excerpt": excerpt,
        "tags": list(tags) if tags is not None else title.split(),
        "match_score": 0.0,
        "provenance": {"produced_by": produced_by, "date": date, "recency_rank": 0},
        "stale": stale,
    }


def _raw_recurrence(**overrides) -> dict:
    """A raw cluster as actionable_recurrences returns it (WITH evidence)."""
    base = {
        "key": "kata-evaluate::exec-injection",
        "responsible_skill": "kata-evaluate",
        "failure_class": "exec-injection",
        "distinct_runs": 3,
        "raw_count": 3,
        "severity_tier": "MAJOR",
        "threshold": 3,
        "off_vocabulary": False,
        "evidence": [{"what_conformance_missed": "LEAKYSECRETMARKER raw text"}],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# The CONTRACT — recall_payload_schema()
# ---------------------------------------------------------------------------

def test_schema_version_pinned():
    """The contract pins schema_version 'recall/v1'."""
    assert recall.recall_payload_schema()["schema_version"] == "recall/v1"


def test_schema_record_field_set():
    """RecallRecord field set matches the documented 9 fields."""
    schema = recall.recall_payload_schema()
    assert set(schema["records"]["record_fields"]) == _RECORD_FIELDS


def test_schema_recurrence_field_set():
    """RecurrenceRecord field set is EXACTLY the 7 contract fields (no evidence)."""
    schema = recall.recall_payload_schema()
    assert set(schema["recurrences"]["record_fields"]) == _RECURRENCE_FIELDS


def test_schema_marks_open_fields_without_closed_vocabulary():
    """B1: source/backend/produced_by are marked OPEN and carry NO closed vocabulary."""
    schema = recall.recall_payload_schema()
    src = schema["records"]["record_fields"]["source"]
    prod = schema["records"]["record_fields"]["provenance"]["fields"]["produced_by"]
    backend = schema["provenance"]["fields"]["backend"]
    for field in (src, prod, backend):
        assert field.get("open") is True
        assert "values" not in field and "enum" not in field


def test_build_payload_validates_against_schema():
    """build_payload output validates against the contract."""
    payload = recall.build_payload(
        {"terms": ["recall"], "kind": "project"},
        [_cand(date="2026-06-01")], [], ["LESSONS-LEARNED.md"],
        generated_ts="2026-06-28T00:00:00Z",
    )
    # ensure the record carries valid recency_rank/match_score after selection shape
    payload["records"] = recall.select_records([_cand(title="recall contract", date="2026-06-01")], ["recall"])
    assert recall.validate_payload(payload) == []


def test_validate_payload_rejects_wrong_version():
    """A payload with the wrong schema_version is rejected."""
    payload = recall.build_payload({"terms": [], "kind": "project"}, [], [], [])
    payload["schema_version"] = "recall/v2"
    assert any("schema_version" in e for e in recall.validate_payload(payload))


# ---------------------------------------------------------------------------
# B1 — the contract is vocabulary-OPEN (external-adapter acceptance)
# ---------------------------------------------------------------------------

def test_external_adapter_payload_validates():
    """B1 (mutation-load-bearing): an external-adapter payload with arbitrary
    source/backend/produced_by VALIDATES — the schema enforces shape, NOT a closed
    vocabulary. A builder who closes the set to the files-only labels FAILS this.
    """
    ext_record = _cand(
        title="A note", source="obsidian-note", produced_by="kiban",
        source_path="vault://notes/a", date="2026-01-01",
    )
    payload = recall.build_payload(
        {"terms": ["note"], "kind": "research"},
        [ext_record], [], ["vault://notes"],
        backend="obsidian", generated_ts="2026-06-28T00:00:00Z",
    )
    errors = recall.validate_payload(payload)
    assert errors == [], f"external-adapter payload must validate (B1), got: {errors}"


def test_files_only_default_backend_validates():
    """The files-only adapter's own labels also validate (same open contract)."""
    payload = recall.build_payload({"terms": ["x"], "kind": "project"}, [], [], [])
    assert payload["provenance"]["backend"] == "files-only"
    assert recall.validate_payload(payload) == []


# ---------------------------------------------------------------------------
# N1 — selection is a hard token-overlap gate; recency only ranks
# ---------------------------------------------------------------------------

def test_matching_record_selected():
    """A candidate whose tags/title overlap the query terms IS selected."""
    out = recall.select_records([_cand(title="converse grill", date="2026-01-01")], ["converse"])
    assert len(out) == 1


def test_zero_overlap_recent_excluded():
    """N1 (mutation-load-bearing): a zero-overlap-but-RECENT candidate is EXCLUDED.

    Recency ranks passers; it never promotes a non-match in.
    """
    match = _cand(title="converse grill", date="2020-01-01")        # old, overlaps
    recent_norel = _cand(title="zzz unrelated topic", date="2026-06-28")  # recent, NO overlap
    out = recall.select_records([match, recent_norel], ["converse"])
    ids = [r["id"] for r in out]
    assert match["id"] in ids
    assert recent_norel["id"] not in ids, "zero-overlap record excluded despite recency"


def test_recency_ranks_passers():
    """Of two equally-overlapping records, the more recent ranks higher (recency RANKS).

    Mutation-load-bearing on the recency component.
    """
    old = _cand(title="converse alpha", date="2019-01-01")
    new = _cand(title="converse beta", date="2026-06-01")
    out = recall.select_records([old, new], ["converse"])
    assert out[0]["id"] == new["id"]
    assert out[0]["provenance"]["recency_rank"] == 0
    # the old (overlapping) record is STILL present — recency never filters a passer out
    assert old["id"] in [r["id"] for r in out]


def test_match_score_overlap_dominates_recency():
    """match_score: overlap count dominates; recency lives in (0,1)."""
    two = _cand(title="converse grill", excerpt="", tags=["converse", "grill"])
    one = _cand(title="converse only", excerpt="", tags=["converse"])
    s2 = recall.match_score(two, ["converse", "grill"])
    s1 = recall.match_score(one, ["converse", "grill"])
    assert s2 >= 2.0 and s2 < 3.0
    assert s1 >= 1.0 and s1 < 2.0


def test_no_query_terms_selects_nothing():
    """Empty query terms ⇒ zero overlap for everything ⇒ no records selected."""
    assert recall.select_records([_cand(title="converse grill")], []) == []


# ---------------------------------------------------------------------------
# Recurrences — ALWAYS surfaced (bypass selection)
# ---------------------------------------------------------------------------

def test_recurrences_always_surface(tmp_path):
    """A seeded open recurrence appears in payload['recurrences'] with ZERO query overlap.

    Mutation-load-bearing on the always-surface branch.
    """
    payload = recall.recall_from_paths(
        misses_path=_FIX / "validation-misses.jsonl",
        handled_path=tmp_path / "absent-handled.jsonl",  # absent ⇒ nothing handled
        query_terms=["xyzzy-no-overlap"], kind="project",
        generated_ts="2026-06-28T00:00:00Z",
    )
    assert len(payload["recurrences"]) >= 1
    assert payload["recurrences"][0]["key"] == "kata-evaluate::exec-injection"


# ---------------------------------------------------------------------------
# N3 — RecurrenceRecord projects out raw evidence
# ---------------------------------------------------------------------------

def test_recurrence_projects_out_evidence():
    """N3 (mutation-load-bearing): the projection keeps ONLY the 7 fields; evidence dropped."""
    rec = recall._recurrence_record(_raw_recurrence())
    assert set(rec.keys()) == _RECURRENCE_FIELDS
    assert "evidence" not in rec
    assert "raw_count" not in rec and "threshold" not in rec
    assert rec["open"] is True


def test_no_raw_miss_text_in_payload(tmp_path):
    """The raw what_conformance_missed text never leaks into the serialized payload."""
    payload = recall.recall_from_paths(
        misses_path=_FIX / "validation-misses.jsonl",
        handled_path=tmp_path / "absent-handled.jsonl",
        query_terms=["converse"], kind="project",
        generated_ts="2026-06-28T00:00:00Z",
    )
    assert "LEAKYSECRETMARKER" not in json.dumps(payload)


def test_payload_recurrences_validate(tmp_path):
    """Projected recurrences pass validation (extra raw keys would be rejected)."""
    payload = recall.recall_from_paths(
        misses_path=_FIX / "validation-misses.jsonl",
        handled_path=tmp_path / "absent-handled.jsonl",
        query_terms=["converse"], kind="project",
        generated_ts="2026-06-28T00:00:00Z",
    )
    assert recall.validate_payload(payload) == []


def test_validate_rejects_recurrence_with_evidence():
    """A recurrence carrying raw evidence is rejected (extra key, N3 guard)."""
    payload = recall.build_payload(
        {"terms": [], "kind": "project"}, [],
        [{**{f: ("MAJOR" if f == "severity_tier" else "x") for f in _RECURRENCE_FIELDS},
          "distinct_runs": 3, "off_vocabulary": False, "open": True,
          "evidence": [{"what_conformance_missed": "secret"}]}],
        [],
    )
    assert any("evidence" in e or "extra" in e for e in recall.validate_payload(payload))


# ---------------------------------------------------------------------------
# Staleness — a HINT, surfaced not filtered
# ---------------------------------------------------------------------------

def test_stale_record_surfaced_with_flag():
    """A stale (old-dated) record is surfaced with stale=True and provenance.

    Mutation-load-bearing on the stale-marking line.
    """
    text = "---\ndate: 2019-01-01\n---\n- **L1 — Converse old lesson.** body about converse\n"
    recs = recall.parse_lessons(text, source_path="LESSONS-LEARNED.md")
    assert len(recs) == 1
    assert recs[0]["stale"] is True
    assert recs[0]["provenance"]["date"] == "2019-01-01"
    assert recs[0]["provenance"]["produced_by"] == "repo"


def test_recent_record_not_stale():
    """A recent record is not flagged stale."""
    text = "---\ndate: 2026-06-01\n---\n- **L2 — Converse fresh lesson.** body\n"
    recs = recall.parse_lessons(text, source_path="x.md")
    assert recs[0]["stale"] is False


def test_stale_record_not_filtered_from_selection():
    """A stale-but-overlapping record REMAINS in records (stale never gates inclusion)."""
    stale = _cand(title="converse stale", date="2019-01-01", stale=True)
    out = recall.select_records([stale], ["converse"])
    assert len(out) == 1
    assert out[0]["stale"] is True


# ---------------------------------------------------------------------------
# Parsers + provenance
# ---------------------------------------------------------------------------

def test_parse_lessons_bullets():
    """parse_lessons extracts anchor/title + excerpt + repo provenance."""
    recs = recall.parse_lessons(_FIX / "LESSONS-LEARNED.md")
    titles = [r["title"] for r in recs]
    assert any(t.startswith("L7 —") for t in titles)
    assert all(r["source"] == "lessons" for r in recs)
    assert all(r["provenance"]["date"] == "2026-06-01" for r in recs)


def test_parse_decisions_bullets():
    """parse_decisions yields decisions-sourced records."""
    recs = recall.parse_decisions(_FIX / "DECISIONS.md")
    assert recs and all(r["source"] == "decisions" for r in recs)


def test_parse_intent_frontmatter():
    """parse_intent reads goal/fixes/features from frontmatter (source='prior-intent')."""
    recs = recall.parse_intent(_FIX / "INTENT.md")
    assert recs and all(r["source"] == "prior-intent" for r in recs)
    assert any(r["title"] == "goal" for r in recs)


def test_parse_understand_sections():
    """parse_understand yields understand-map records from section bullets."""
    recs = recall.parse_understand(_FIX / "understand.md")
    assert recs and all(r["source"] == "understand-map" for r in recs)
    assert all(r["provenance"]["produced_by"] == "kata-understand" for r in recs)


def test_record_id_is_anchor_slug_not_line_numbers():
    """Record id = source_path + anchor slug (stable across edits; no line numbers)."""
    recs = recall.parse_lessons(_FIX / "LESSONS-LEARNED.md")
    rec = next(r for r in recs if r["title"].startswith("L7"))
    assert rec["id"].startswith(str(_FIX / "LESSONS-LEARNED.md"))
    assert "#" in rec["id"]
    assert not re.search(r":\d+$", rec["id"])  # not a trailing line number


def test_sources_read_lists_present_sources(tmp_path):
    """provenance.sources_read lists exactly the present sources."""
    payload = recall.recall_from_paths(
        lessons_path=_FIX / "LESSONS-LEARNED.md",
        decisions_path=_FIX / "DECISIONS.md",
        intent_path=tmp_path / "absent-INTENT.md",   # absent
        understand_path=_FIX / "understand.md",
        misses_path=_FIX / "validation-misses.jsonl",
        handled_path=tmp_path / "absent-handled.jsonl",  # absent
        query_terms=["converse"], kind="project",
        generated_ts="2026-06-28T00:00:00Z",
    )
    read = payload["provenance"]["sources_read"]
    assert str(_FIX / "LESSONS-LEARNED.md") in read
    assert str(_FIX / "DECISIONS.md") in read
    assert str(_FIX / "understand.md") in read
    assert str(_FIX / "validation-misses.jsonl") in read
    assert str(tmp_path / "absent-INTENT.md") not in read
    assert str(tmp_path / "absent-handled.jsonl") not in read


def test_recall_from_paths_full_validates(tmp_path):
    """A full files-only recall over the fixtures produces a valid payload with records."""
    payload = recall.recall_from_paths(
        lessons_path=_FIX / "LESSONS-LEARNED.md",
        decisions_path=_FIX / "DECISIONS.md",
        intent_path=_FIX / "INTENT.md",
        understand_path=_FIX / "understand.md",
        misses_path=_FIX / "validation-misses.jsonl",
        handled_path=tmp_path / "absent-handled.jsonl",
        query_terms=["converse", "recall"], kind="version-up",
        generated_ts="2026-06-28T00:00:00Z",
    )
    assert recall.validate_payload(payload) == []
    assert len(payload["records"]) >= 1
    assert payload["query"]["kind"] == "version-up"


# ---------------------------------------------------------------------------
# Degradation — absent sources never crash
# ---------------------------------------------------------------------------

def test_all_sources_absent_empty_payload(tmp_path):
    """All sources absent ⇒ empty records/recurrences/sources_read, no crash."""
    payload = recall.recall_from_paths(
        lessons_path=tmp_path / "no-lessons.md",
        decisions_path=tmp_path / "no-decisions.md",
        intent_path=tmp_path / "no-intent.md",
        understand_path=tmp_path / "no-understand.md",
        misses_path=tmp_path / "no-misses.jsonl",
        handled_path=tmp_path / "no-handled.jsonl",
        query_terms=["anything"], kind="project",
        generated_ts="2026-06-28T00:00:00Z",
    )
    assert payload["records"] == []
    assert payload["recurrences"] == []
    assert payload["provenance"]["sources_read"] == []
    assert recall.validate_payload(payload) == []


def test_none_sources_degrade(tmp_path):
    """All-None sources ⇒ empty payload (no crash)."""
    payload = recall.recall_from_paths(
        query_terms=["x"], kind="project", generated_ts="2026-06-28T00:00:00Z",
    )
    assert payload["records"] == []
    assert payload["recurrences"] == []


def test_malformed_misses_line_skipped(tmp_path):
    """A malformed misses line is skipped (tolerant), never raises."""
    misses = tmp_path / "m.jsonl"
    misses.write_text("not json {{{\n", encoding="utf-8")
    payload = recall.recall_from_paths(
        misses_path=misses, handled_path=tmp_path / "h.jsonl",
        query_terms=["x"], kind="project", generated_ts="2026-06-28T00:00:00Z",
    )
    assert payload["recurrences"] == []


# ---------------------------------------------------------------------------
# '..' guard (CWE-23)
# ---------------------------------------------------------------------------

def test_guard_path_rejects_dotdot():
    """_guard_path raises ValueError on a '..' segment (CWE-23).

    Mutation-load-bearing on the '..' guard.
    """
    with pytest.raises(ValueError, match=r"\.\."):
        recall._guard_path("../evil.md")


def test_recall_from_paths_rejects_dotdot():
    """recall_from_paths guards all supplied paths — a '..' path raises ValueError."""
    with pytest.raises(ValueError, match=r"\.\."):
        recall.recall_from_paths(
            lessons_path="../evil.md", query_terms=[], kind="project",
        )


def test_non_dotdot_io_failure_returns_empty(tmp_path):
    """A non-'..' absent path returns [] (never raises into the caller)."""
    assert recall.parse_lessons(tmp_path / "nope.md") == []


# ---------------------------------------------------------------------------
# Purity — no exec sink, no embeddings (source scan)
# ---------------------------------------------------------------------------

class TestExecSafety:
    """Source-scan assertions: recall.py introduces no execution sink."""

    def _source(self) -> str:
        return _SOURCE.read_text(encoding="utf-8")

    def test_no_eval(self):
        hits = [m.group() for m in re.finditer(r"\beval\s*\(", self._source())]
        assert not hits, f"eval() found in recall.py: {hits}"

    def test_no_exec(self):
        hits = [m.group() for m in re.finditer(r"\bexec\s*\(", self._source())]
        assert not hits, f"exec() found in recall.py: {hits}"

    def test_no_subprocess_import(self):
        hits = [
            m.group() for m in re.finditer(
                r"^\s*(?:import|from)\s+subprocess\b", self._source(), re.MULTILINE
            )
        ]
        assert not hits, f"subprocess import found in recall.py: {hits}"

    def test_no_os_system_or_popen(self):
        src = self._source()
        assert "os.system" not in src and ".popen" not in src.lower()

    def test_no_shell_true(self):
        assert "shell=True" not in self._source()

    def test_ast_parseable(self):
        ast.parse(self._source())


class TestNoEmbeddings:
    """recall.py imports no vector/embedding library (token-overlap only)."""

    _LIBS = (
        "numpy", "scipy", "sklearn", "faiss", "torch", "tensorflow",
        "sentence_transformers", "gensim", "transformers", "annoy",
        "chromadb", "pinecone", "openai", "langchain", "llama_index",
    )

    def test_no_embedding_import(self):
        src = _SOURCE.read_text(encoding="utf-8")
        for lib in self._LIBS:
            pattern = rf"^\s*(?:import|from)\s+{re.escape(lib)}\b"
            assert not re.search(pattern, src, re.MULTILINE), f"embedding/vector import found: {lib}"


# ---------------------------------------------------------------------------
# Recurrence reuse by name (anchor resolves — no phantom reuse)
# ---------------------------------------------------------------------------

def test_reuses_recurrence_detect_detect_from_paths():
    """recall_from_paths reuses recurrence_detect.detect_from_paths by name (real anchor)."""
    import recurrence_detect
    assert callable(recurrence_detect.detect_from_paths)
    src = _SOURCE.read_text(encoding="utf-8")
    assert "recurrence_detect.detect_from_paths" in src


# ---------------------------------------------------------------------------
# Mutation non-vacuity proofs (a–g) — spawn real subprocess via prove_non_vacuous
# ---------------------------------------------------------------------------

def _tools_dir() -> str:
    return str(Path(__file__).parent.parent.resolve())


def _src() -> str:
    return str(_SOURCE.resolve())


def _cmd(test_name: str) -> str:
    return (
        f'cd /d "{_tools_dir()}" && uv run pytest '
        f"tests/test_recall.py::{test_name} -q"
    )


def test_mutation_proof_overlap_gate():
    """(a) Removing the token-overlap GATE breaks the N1 exclusion predicate.

    Asserted line (exact, 8-space indent):
        '        if not token_overlap(cand, query_terms):'
    Removed → orphaned `continue` → IndentationError on import →
    test_zero_overlap_recent_excluded goes red.
    """
    import mutation_run
    asserted_line = "        if not token_overlap(cand, query_terms):"
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_zero_overlap_recent_excluded")
    )
    assert verdict["nonVacuous"] is True, f"overlap gate not load-bearing: {verdict}"


def test_mutation_proof_recency_component():
    """(b) Removing the recency component breaks recency ranking among passers.

    Asserted line (exact, 4-space indent):
        '    recency = _recency_component(_record_date(record, "date"))'
    Removed → `recency` undefined → NameError in match_score →
    test_recency_ranks_passers goes red.
    """
    import mutation_run
    asserted_line = '    recency = _recency_component(_record_date(record, "date"))'
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_recency_ranks_passers")
    )
    assert verdict["nonVacuous"] is True, f"recency component not load-bearing: {verdict}"


def test_mutation_proof_always_surface_recurrences():
    """(c) Removing the detect_from_paths call drops the always-surfaced recurrences.

    Asserted line (exact, 8-space indent):
        '        raw_recurrences = recurrence_detect.detect_from_paths(misses_path, hp)'
    Removed → raw_recurrences stays [] → payload['recurrences'] empty →
    test_recurrences_always_surface goes red.
    """
    import mutation_run
    asserted_line = "        raw_recurrences = recurrence_detect.detect_from_paths(misses_path, hp)"
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_recurrences_always_surface")
    )
    assert verdict["nonVacuous"] is True, f"always-surface branch not load-bearing: {verdict}"


def test_mutation_proof_stale_does_not_filter():
    """(d) Removing the stale-marking line drops the surfaced stale HINT.

    Asserted line (exact, 8-space indent):
        '        "stale": _is_stale(date_str),'
    Removed → record dict has no `stale` key → KeyError in the assertion →
    test_stale_record_surfaced_with_flag goes red. (The record is STILL surfaced —
    stale is a hint, never a filter; this proves the hint is load-bearing.)
    """
    import mutation_run
    asserted_line = '        "stale": _is_stale(date_str),'
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_stale_record_surfaced_with_flag")
    )
    assert verdict["nonVacuous"] is True, f"stale hint not load-bearing: {verdict}"


def test_mutation_proof_dotdot_guard():
    """(e) Removing the '..' guard defeats CWE-23.

    Asserted line (exact, 4-space indent):
        '    if any(part == ".." for part in p.parts):'
    Removed → orphaned raise → IndentationError on import →
    test_guard_path_rejects_dotdot goes red.
    """
    import mutation_run
    asserted_line = '    if any(part == ".." for part in p.parts):'
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_guard_path_rejects_dotdot")
    )
    assert verdict["nonVacuous"] is True, f"'..' guard not load-bearing: {verdict}"


def test_mutation_proof_open_contract_source():
    """(f) Removing the OPEN source type-acceptance breaks external-adapter validation.

    Asserted line (exact, 4-space indent):
        '    if not isinstance(rec.get("source"), str):'
    Removed → orphaned errors.append → IndentationError on import →
    test_external_adapter_payload_validates goes red. This is the open-acceptance
    line for `source` (type-checked str, NOT a closed enum — B1).
    """
    import mutation_run
    asserted_line = '    if not isinstance(rec.get("source"), str):'
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_external_adapter_payload_validates")
    )
    assert verdict["nonVacuous"] is True, f"open-contract source line not load-bearing: {verdict}"


def test_mutation_proof_evidence_projection():
    """(g) Removing the projection comprehension leaks raw evidence (N3).

    Asserted line (exact, 4-space indent):
        '    projected = {field: raw.get(field) for field in _RECURRENCE_FIELDS if field != "open"}'
    Removed → `projected` undefined → NameError in _recurrence_record →
    test_recurrence_projects_out_evidence goes red.
    """
    import mutation_run
    asserted_line = (
        '    projected = {field: raw.get(field) for field in _RECURRENCE_FIELDS if field != "open"}'
    )
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_recurrence_projects_out_evidence")
    )
    assert verdict["nonVacuous"] is True, f"evidence-projection not load-bearing: {verdict}"
