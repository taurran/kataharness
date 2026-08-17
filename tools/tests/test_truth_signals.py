"""Tests for truth_signals.py — Truth Serum v1's SEMI layer (S1, S2, S3).

Standing humility (TM-D2, verbatim): *"the judgment+human layers found all of these; the
automated mechanical gates found none."* Detectors ATTEST and NARROW; judges judge.

Three obligations from the frozen acceptance, and every test here serves one of them:

1. **T6–T11 corpus fixtures produce the known-orphan findings.** ``test_orphan_corpus_
   calibration_t6_t11`` is the declared evidence node. It runs the REAL ``graph_gen.build_graph``
   over ``tests/fixtures/orphan-corpus`` — no mocked graph — so the calibration is against the
   graph's actual behaviour, defects included.
2. **Each stated limit has a test DEMONSTRATING the miss.** The five ``test_limit_*`` tests below
   assert the WRONG answer S1 gives, one per verbatim limit. Honest limits pinned, not prosed: if
   a future change fixed a limit, its test fails and the prose must be corrected with it.
3. **Signals never return a blocking verdict type.** Pinned four ways — the enum sets are
   disjoint, ``build_row`` refuses to mint one, ``assert_non_blocking`` raises on one, and every
   row produced from the real corpus is checked.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import graph_gen
import truth_signals as ts

CORPUS = Path(__file__).parent / "fixtures" / "orphan-corpus"

# Pinned clock: build_graph stamps meta.generatedAt, and a wall-clock stamp would make the
# byte-stability assertion below vacuous (Determinism Doctrine law 7 / DET-14).
_PINNED_CLOCK = "2026-01-01T00:00:00+00:00"


@pytest.fixture(scope="module")
def graph() -> dict:
    return graph_gen.build_graph(CORPUS, generated_at=_PINNED_CLOCK)


def _subjects(rows, row_class: str) -> set[str]:
    return {r["subject"] for r in rows if r["class"] == row_class}


# =============================================================================
# 1. THE EVIDENCE NODE — T6–T11 calibration
# =============================================================================

#: Ground truth transcribed from the trust ledger (.planning/specs/trust-model/ASSESSMENT.md
#: §1, the six FACADE rows). Each entry: the ledger row, and the corpus symbols that mirror the
#: live orphan it names.
KNOWN_ORPHANS: dict[str, tuple[str, ...]] = {
    # T6 — "Nothing builds from a draft (D169)": assert_frozen inside build_brief, zero
    # production callers. The only caller is same-file, and graph_gen emits no self-file edge.
    "T6": ("t6_dispatch.py::assert_frozen", "t6_dispatch.py::build_brief"),
    # T7 — "Host-only roles never route off-host": resolve_roles has zero callers; the
    # preflight that should call it exists and never does.
    "T7": ("t7_roles.py::resolve_roles",),
    # T8 — "The contract gate ran": producer-only, zero ever written.
    "T8": ("t8_contract_gate.py::write_contract_gate",),
    # T9 — "Runs are accounted (telemetry)": engine with zero callers.
    "T9": ("t9_telemetry.py::build_ledger_row", "t9_telemetry.py::record_dispatch"),
    # T10 — "Runs survive interruption": detect_lost_run / restore / fold_board, zero callers.
    "T10": (
        "t10_restore.py::detect_lost_run",
        "t10_restore.py::fold_board",
        "t10_restore.py::restore_run",
    ),
    # T11 — "Research claims are grounded": TEST-ONLY callers. The tests-path filter is the
    # whole reason this row is visible as a facade rather than as wired machinery.
    "T11": ("t11_grounding.py::build_verdict", "t11_grounding.py::grounding_verdict"),
}

#: Genuinely wired symbols. A detector that flags these is vacuous, so the calibration asserts
#: their ABSENCE as hard as it asserts the orphans' presence.
NEGATIVE_CONTROLS: tuple[str, ...] = (
    # Called from wired_pipeline.py (non-test) AND from tests/ — the test caller must neither
    # create nor destroy wiring.
    "wired_helper.py::helper_wired",
    # T7's would-be caller: alive, and that is what makes "it never calls resolve_roles" a
    # finding about resolve_roles rather than about dead code.
    "t7_preflight.py::run_preflight",
)


def test_orphan_corpus_calibration_t6_t11(graph):
    """EVIDENCE NODE. Every T6–T11 known orphan is found; every wired control is not.

    Runs the real graph builder over the real corpus. Ground truth is the trust ledger's six
    FACADE rows, mirrored shape-for-shape in tests/fixtures/orphan-corpus/.
    """
    rows = ts.unwired_symbols(graph)
    found = _subjects(rows, "unwired-symbol")

    missed: list[str] = []
    for ledger_row, symbols in KNOWN_ORPHANS.items():
        for symbol in symbols:
            if symbol not in found:
                missed.append(f"{ledger_row}: {symbol}")
    assert not missed, f"known orphans NOT reported by S1: {missed}"

    false_positives = [c for c in NEGATIVE_CONTROLS if c in found]
    assert not false_positives, f"wired symbols wrongly reported unwired: {false_positives}"

    # The scan-coverage row is the positive half of the anti-vacuity companion: proof the
    # scan covered real input rather than certifying an empty set.
    coverage = [r for r in rows if r["class"] == "scan-coverage"]
    assert len(coverage) == 1
    assert coverage[0]["verdict"] == "CLEAR"
    assert "scanned" in coverage[0]["detail"]

    # And it never blocks.
    assert all(r["blocking"] is False for r in rows)


def test_t11_is_an_orphan_only_because_of_the_tests_path_filter(graph):
    """Without the filter, T11's engine looks wired: it has callers — all of them tests."""
    with_filter = _subjects(ts.unwired_symbols(graph), "unwired-symbol")
    without_filter = _subjects(ts.unwired_symbols(graph, test_path_parts=()), "unwired-symbol")

    for symbol in KNOWN_ORPHANS["T11"]:
        assert symbol in with_filter
        assert symbol not in without_filter

    # The control keeps its non-test caller either way — the filter subtracts test callers,
    # it does not invent orphans.
    assert "wired_helper.py::helper_wired" not in with_filter
    assert "wired_helper.py::helper_wired" not in without_filter


def test_import_level_leg_finds_the_unimported_modules(graph):
    """The import-level half: product files no non-test file imports."""
    found = _subjects(ts.unimported_modules(graph), "unimported-module")
    for module in ("t6_dispatch.py", "t8_contract_gate.py", "t9_telemetry.py",
                   "t10_restore.py", "t11_grounding.py", "t7_roles.py"):
        assert module in found, f"{module} has no non-test importer and was not reported"
    # wired_helper.py is imported by wired_pipeline.py (non-test) → not reported.
    assert "wired_helper.py" not in found
    assert "t7_preflight.py" not in found


def test_import_level_leg_catches_what_bare_name_matching_hid(graph):
    """The two S1 legs are not redundant.

    ``limit_bare_name_a.shared_name`` escapes the symbol leg (bare-name matching credits it
    with a call it never received), but nothing imports its module, so the import leg reports
    it. Stated so the legs' complementarity is a fact and not an assumption.
    """
    symbol_leg = _subjects(ts.unwired_symbols(graph), "unwired-symbol")
    import_leg = _subjects(ts.unimported_modules(graph), "unimported-module")
    assert "limit_bare_name_a.py::shared_name" not in symbol_leg
    assert "limit_bare_name_a.py" in import_leg


def test_s1_signals_composes_both_legs(graph):
    combined = ts.s1_signals(graph)
    assert _subjects(combined, "unwired-symbol")
    assert _subjects(combined, "unimported-module")
    assert all(r["detector"] == "S1" for r in combined)


# =============================================================================
# 2. THE FIVE HONEST LIMITS — each demonstrated, not prosed
# =============================================================================

def test_s1_honest_limits_are_carried_verbatim_on_every_row(graph):
    """The DESIGN §3.1 wording travels with the finding, not only in a docstring."""
    assert ts.S1_HONEST_LIMITS == (
        "call-only edges",
        "bare-name matching",
        "fabricated `src` attribution",
        "dynamic imports invisible",
        "entry points outside the graph look dead",
    )
    for row in ts.s1_signals(graph):
        assert set(row["limits"]) == set(ts.S1_HONEST_LIMITS)


def test_limit_call_only_edges_misses_a_value_reference(graph):
    """LIMIT 1 — "call-only edges". Demonstrates the FALSE POSITIVE.

    ``limit_call_only_consumer.register_handlers`` imports ``used_as_value`` and hands it on as
    a value. graph_gen's ``_extract_refs`` walks ``call`` expressions only, so the reference is
    invisible and a genuinely-used symbol is reported unwired.
    """
    assert "limit_call_only.py::used_as_value" in _subjects(
        ts.unwired_symbols(graph), "unwired-symbol"
    )
    # Proof the reference really is there in the source S1 just scanned.
    source = (CORPUS / "limit_call_only_consumer.py").read_text(encoding="utf-8")
    assert "used_as_value" in source
    assert "used_as_value(" not in source  # referenced, never called


def test_limit_bare_name_matching_credits_the_wrong_symbol(graph):
    """LIMIT 2 — "bare-name matching". Demonstrates BOTH error directions.

    ``limit_bare_name_caller`` imports and calls ``limit_bare_name_b.shared_name``. Call targets
    resolve by bare NAME to the first sorted candidate, so the edge lands on
    ``limit_bare_name_a`` instead: the genuine orphan is hidden (false negative — the direction
    that actually lets a facade through) and the real target is reported unwired (false
    positive).
    """
    found = _subjects(ts.unwired_symbols(graph), "unwired-symbol")
    assert "limit_bare_name_a.py::shared_name" not in found, "false negative not reproduced"
    assert "limit_bare_name_b.py::shared_name" in found, "false positive not reproduced"

    edges = {(e["src"], e["dst"]) for e in graph["edges"] if e["kind"] == "ref"}
    assert ("limit_bare_name_caller.py::call_b", "limit_bare_name_a.py::shared_name") in edges
    assert ("limit_bare_name_caller.py::call_b", "limit_bare_name_b.py::shared_name") not in edges


def test_limit_fabricated_src_attribution_names_the_wrong_caller(graph):
    """LIMIT 3 — "fabricated `src` attribution".

    ``zzz_actual_caller`` calls ``imported_target``. ``_extract_refs`` attributes the edge to the
    calling FILE's alphabetically-first symbol, so the provenance S1 reports names
    ``aaa_innocent`` — a function that calls nothing. The file is right; the symbol is invented.
    """
    provenance = ts.reference_provenance(graph)
    attributed = provenance["limit_fabricated_target.py::imported_target"]
    assert attributed == ["limit_fabricated_src.py::aaa_innocent"]
    assert "limit_fabricated_src.py::zzz_actual_caller" not in attributed

    source = (CORPUS / "limit_fabricated_src.py").read_text(encoding="utf-8")
    assert "def zzz_actual_caller():\n    return imported_target()" in source


def test_limit_dynamic_imports_are_invisible(graph):
    """LIMIT 4 — "dynamic imports invisible". Demonstrates the FALSE POSITIVE.

    ``call_dynamically`` reaches ``dynamic_only`` through ``importlib.import_module`` +
    ``getattr``. Neither an import edge (the module name is a string) nor a ref edge (the call
    node's function is ``getattr``) exists, so a live symbol AND its module are both reported
    dead. Same residual ``contract_edges.edge_honesty`` already documents (adval P0-F9).
    """
    assert "limit_dynamic_target.py::dynamic_only" in _subjects(
        ts.unwired_symbols(graph), "unwired-symbol"
    )
    assert "limit_dynamic_target.py" in _subjects(
        ts.unimported_modules(graph), "unimported-module"
    )
    import_edges = {(e["src"], e["dst"]) for e in graph["edges"] if e["kind"] == "import"}
    assert ("limit_dynamic_caller.py", "limit_dynamic_target.py") not in import_edges


def test_limit_out_of_graph_entry_points_look_dead(graph):
    """LIMIT 5 — "entry points outside the graph look dead".

    ``run_pipeline`` is the corpus's entry point, invoked from ``entrypoints/run.sh``. graph_gen
    globs ``*.py``, so the shell caller is not a node at all and the entry point is reported
    unwired — while the symbols it wires are correctly CLEAR.
    """
    found = _subjects(ts.unwired_symbols(graph), "unwired-symbol")
    assert "wired_pipeline.py::run_pipeline" in found, "false positive not reproduced"
    # The wiring it performs is nonetheless seen — this limit costs the entry point, not its callees.
    assert "wired_helper.py::helper_wired" not in found
    assert "t7_preflight.py::run_preflight" not in found

    entry = CORPUS / "entrypoints" / "run.sh"
    assert entry.is_file()
    assert "run_pipeline" in entry.read_text(encoding="utf-8")
    assert entry.suffix != ".py"  # which is exactly why the graph cannot see it


# =============================================================================
# 3. SIGNALS NEVER RETURN A BLOCKING VERDICT TYPE
# =============================================================================

def test_signal_and_blocking_verdict_sets_are_disjoint():
    assert ts.SIGNAL_VERDICTS & ts.BLOCKING_VERDICTS == frozenset()


def test_signals_never_return_a_blocking_verdict_type(graph):
    """Every row from every detector, over real input, on the signal enum and non-blocking."""
    rows = (
        ts.s1_signals(graph)
        + ts.prose_claim_signals(
            (CORPUS / "prose" / "claims.md").read_text(encoding="utf-8"),
            source="prose/claims.md",
            repo_root=CORPUS,
        )
        + ts.label_propagation_signals(
            (CORPUS / "labels" / "unlabelled-closeout.md").read_text(encoding="utf-8"),
            artifact="labels/unlabelled-closeout.md",
            required_labels=["modeled", "n=1-directional"],
        )
    )
    assert rows
    for row in rows:
        assert row["blocking"] is False
        assert row["verdict"] in ts.SIGNAL_VERDICTS
        assert row["verdict"] not in ts.BLOCKING_VERDICTS


@pytest.mark.parametrize("verdict", sorted(ts.BLOCKING_VERDICTS))
def test_build_row_refuses_to_mint_a_blocking_verdict(verdict):
    with pytest.raises(ValueError, match="not a signal verdict"):
        ts.build_row(
            detector="S1", row_class="unwired-symbol", verdict=verdict,
            subject="x", detail="y",
        )


def test_assert_non_blocking_raises_on_a_blocking_verdict():
    row = ts.build_row(detector="S1", row_class="c", verdict="SIGNAL", subject="s", detail="d")
    row["verdict"] = "BLOCK"
    with pytest.raises(ValueError, match="blocking verdict type"):
        ts.assert_non_blocking([row])


def test_assert_non_blocking_raises_on_a_blocking_flag():
    row = ts.build_row(detector="S1", row_class="c", verdict="SIGNAL", subject="s", detail="d")
    row["blocking"] = True
    with pytest.raises(ValueError, match="marked blocking"):
        ts.assert_non_blocking([row])


def test_unattested_is_a_refusal_to_certify_not_a_refusal_to_gate():
    """The anti-vacuity companion for a SIGNAL detector cannot be a gate refusal."""
    assert "UNATTESTED" in ts.SIGNAL_VERDICTS
    assert "UNATTESTED" not in ts.BLOCKING_VERDICTS
    rows = ts.unwired_symbols({})
    assert rows[0]["verdict"] == "UNATTESTED"
    assert rows[0]["blocking"] is False


# =============================================================================
# 4. ANTI-VACUITY COMPANIONS (TM-D3)
# =============================================================================

@pytest.mark.parametrize("bad_graph, reason", [
    (None, "no graph artifact supplied"),
    ("not-a-graph", "no graph artifact supplied"),
    ({"meta": {"repoHash": "abc"}}, "no nodes/edges lists"),
    ({"nodes": [], "edges": []}, "no meta.repoHash"),
    ({"nodes": [], "edges": [], "meta": {}}, "no meta.repoHash"),
])
def test_s1_refuses_to_certify_an_absent_or_stale_graph(bad_graph, reason):
    for detector in (ts.unwired_symbols, ts.unimported_modules):
        rows = detector(bad_graph)
        assert len(rows) == 1
        assert rows[0]["verdict"] == "UNATTESTED"
        assert rows[0]["class"] == "anti-vacuity"
        assert reason in rows[0]["detail"]


def test_s1_refuses_a_zero_symbol_scan():
    empty = {"nodes": [], "edges": [], "meta": {"repoHash": "deadbeef"}}
    rows = ts.unwired_symbols(empty)
    assert rows[0]["verdict"] == "UNATTESTED"
    assert "zero product symbols" in rows[0]["detail"]


def test_s1_refuses_a_zero_file_scan():
    empty = {"nodes": [], "edges": [], "meta": {"repoHash": "deadbeef"}}
    rows = ts.unimported_modules(empty)
    assert rows[0]["verdict"] == "UNATTESTED"
    assert "zero product files" in rows[0]["detail"]


def test_s1_symbols_defined_only_in_tests_are_not_product_surface(graph):
    """A test helper is not an orphan. Flagging every one would drown the signal."""
    found = _subjects(ts.unwired_symbols(graph), "unwired-symbol")
    assert not [s for s in found if s.startswith("tests/")]


@pytest.mark.parametrize("text", [None, "", "   \n\t "])
def test_s2_refuses_an_empty_artifact(text):
    rows = ts.prose_claim_signals(text, source="x.md", repo_root=CORPUS)
    assert rows[0]["verdict"] == "UNATTESTED"
    assert "empty or could not be read" in rows[0]["detail"]


def test_s2_refuses_a_missing_citation_root(tmp_path):
    rows = ts.prose_claim_signals(
        "this reuses `a.py:1`", source="x.md", repo_root=tmp_path / "nope",
    )
    assert rows[0]["verdict"] == "UNATTESTED"
    assert "does not exist" in rows[0]["detail"]


def test_s2_reports_zero_candidate_as_zero_candidate():
    """Never "all citations resolve" over a document with no claims."""
    text = (CORPUS / "prose" / "no-claims.md").read_text(encoding="utf-8")
    rows = ts.prose_claim_signals(text, source="prose/no-claims.md", repo_root=CORPUS)
    assert len(rows) == 1
    assert rows[0]["class"] == "scan-coverage"
    assert rows[0]["verdict"] == "CLEAR"
    assert "zero-candidate" in rows[0]["detail"]


@pytest.mark.parametrize("text", [None, "", "  "])
def test_s3_refuses_an_empty_artifact(text):
    rows = ts.label_propagation_signals(text, artifact="a.md", required_labels=["modeled"])
    assert rows[0]["verdict"] == "UNATTESTED"


@pytest.mark.parametrize("labels", [[], ["", "  "]])
def test_s3_refuses_an_empty_label_set(labels):
    rows = ts.label_propagation_signals("some text", artifact="a.md", required_labels=labels)
    assert rows[0]["verdict"] == "UNATTESTED"
    assert "badge registry" in rows[0]["detail"]


# =============================================================================
# 5. S2 — prose-claim narrowing
# =============================================================================

def test_s2_narrows_the_corpus_claims_exactly():
    text = (CORPUS / "prose" / "claims.md").read_text(encoding="utf-8")
    rows = ts.prose_claim_signals(text, source="prose/claims.md", repo_root=CORPUS)
    by_class: dict[str, list[dict]] = {}
    for row in rows:
        by_class.setdefault(row["class"], []).append(row)

    assert len(by_class["phantom-reuse-claim"]) == 2
    assert len(by_class["unresolved-citation"]) == 2
    assert len(by_class["resolved-citation"]) == 2

    unresolved = {p for r in by_class["unresolved-citation"] for p in r["provenance"]}
    assert unresolved == {"phantom_module.py:42", "t8_contract_gate.py:9999"}

    assert all(r["verdict"] == "SIGNAL" for r in by_class["phantom-reuse-claim"])
    assert all(r["verdict"] == "SIGNAL" for r in by_class["unresolved-citation"])
    assert all(r["verdict"] == "CLEAR" for r in by_class["resolved-citation"])


def test_s2_trigger_phrases_are_the_reuse_claims_contract_set():
    """Transcribed from protocol/reuse-claims.md's verbatim LD3 guard text."""
    guard = (Path(__file__).parents[2] / "protocol" / "reuse-claims.md").read_text(encoding="utf-8")
    for phrase in ("reuses", "composes", "via the existing", "already writes", "already exists"):
        assert phrase in guard, f"trigger {phrase!r} is not in the guard's contract text"
        assert phrase in ts.REUSE_TRIGGER_PHRASES


@pytest.mark.parametrize("claim", [
    "This reuses the existing writer.",
    "This composes the existing engine.",
    "Built via the existing resolver.",
    "The orchestrator already writes the row.",
    "This already exists in the tree.",
    "The engine already has that field.",
])
def test_s2_flags_every_trigger_form_without_a_citation(claim):
    rows = ts.prose_claim_signals(claim, source="x.md", repo_root=CORPUS)
    assert [r["class"] for r in rows] == ["phantom-reuse-claim"]


def test_s2_accepts_a_citation_on_the_adjacent_line():
    """Paragraph wrap must not turn a cited claim into a phantom one."""
    text = "this reuses the writer at\n`t8_contract_gate.py:8` which exists.\n"
    rows = ts.prose_claim_signals(text, source="x.md", repo_root=CORPUS)
    assert [r["class"] for r in rows] == ["resolved-citation"]


def test_s2_existence_is_not_support_the_d5_case():
    """OBSERVATIONS D-5: an anchor can RESOLVE and still be fabricated.

    ``kata-validate/SKILL.md:276``'s ``:13`` anchor pointed at a real line that had never, in
    any of the file's nine revisions, contained the quoted sentence — authoring-time
    fabrication, not drift. S2 reports the corpus's equivalent as resolved, and says in the row
    that resolution attests existence only.
    """
    text = "this reuses the lost-run detector at `t10_restore.py:1`.\n"
    rows = ts.prose_claim_signals(text, source="x.md", repo_root=CORPUS)
    assert rows[0]["class"] == "resolved-citation"
    assert rows[0]["verdict"] == "CLEAR"
    assert "support stays judgment" in rows[0]["detail"]
    assert any("existence is not support" in lim for lim in rows[0]["limits"])
    # The cited line genuinely does not support the claim.
    line_1 = (CORPUS / "t10_restore.py").read_text(encoding="utf-8").splitlines()[0]
    assert "detect_lost_run" not in line_1


def test_resolve_citation_existence_semantics():
    assert ts.resolve_citation("t8_contract_gate.py", 1, CORPUS) is True
    assert ts.resolve_citation("t8_contract_gate.py", 9999, CORPUS) is False
    assert ts.resolve_citation("t8_contract_gate.py", 0, CORPUS) is False
    assert ts.resolve_citation("no_such_file.py", 1, CORPUS) is False
    assert ts.resolve_citation("prose", 1, CORPUS) is False  # a directory is not a citation


def test_resolve_citation_refuses_to_escape_the_root():
    """CWE-23: a citation must never resolve outside the supplied root."""
    assert ts.resolve_citation("../../truth_signals.py", 1, CORPUS) is False
    assert ts.resolve_citation(str(Path(__file__).resolve()), 1, CORPUS) is False


def test_s2_resolver_is_injectable_for_the_scheduled_b5_swap():
    """B5's resolver is the sibling Loop-A task's and is UNMERGED at this base commit.

    The composition is declared SCHEDULED, and the seam is proven here: a caller-supplied
    resolver fully determines resolution, so swapping to B5 is a call-site change.
    """
    calls: list[tuple[str, int]] = []

    def always_resolves(path: str, line: int, _root) -> bool:
        calls.append((path, line))
        return True

    text = "this reuses `phantom_module.py:42`\n"
    rows = ts.prose_claim_signals(
        text, source="x.md", repo_root=CORPUS, resolver=always_resolves,
    )
    assert calls == [("phantom_module.py", 42)]
    assert rows[0]["class"] == "resolved-citation"
    # …and the default resolver disagrees, so the parameter is really load-bearing.
    assert ts.prose_claim_signals(text, source="x.md", repo_root=CORPUS)[0]["class"] == (
        "unresolved-citation"
    )


def test_s2_ignores_a_colon_number_that_is_not_a_file_reference():
    """Prose like "`file:line`" or "note:12" must not be mistaken for a citation."""
    rows = ts.prose_claim_signals(
        "this reuses the engine; no `file:line` is cited, see note:12\n",
        source="x.md", repo_root=CORPUS,
    )
    assert [r["class"] for r in rows] == ["phantom-reuse-claim"]


# =============================================================================
# 6. S3 — honesty-label propagation
# =============================================================================

_LABELS = ("modeled", "n=1-directional", "unproven leg")


def test_s3_reports_every_required_label_present():
    text = (CORPUS / "labels" / "labelled-closeout.md").read_text(encoding="utf-8")
    rows = ts.label_propagation_signals(text, artifact="labels/labelled-closeout.md",
                                        required_labels=_LABELS)
    assert len(rows) == 3
    assert all(r["class"] == "label-present" and r["verdict"] == "CLEAR" for r in rows)


def test_s3_signals_every_stripped_label():
    text = (CORPUS / "labels" / "unlabelled-closeout.md").read_text(encoding="utf-8")
    rows = ts.label_propagation_signals(text, artifact="labels/unlabelled-closeout.md",
                                        required_labels=_LABELS)
    assert len(rows) == 3
    assert all(r["class"] == "label-absent" and r["verdict"] == "SIGNAL" for r in rows)


def test_s3_normalizes_emphasis_and_reflow_like_the_clause_pin():
    """Bolding and line-wrapping a label must not read as deletion (the clause-pin semantics)."""
    rows = ts.label_propagation_signals(
        "the score is **modeled**, and the run is\nn=1-directional overall.\n",
        artifact="a.md", required_labels=["modeled", "n=1-directional"],
    )
    assert all(r["class"] == "label-present" for r in rows)


def test_s3_carries_the_kh_t02_forgeability_limit_on_every_row():
    rows = ts.label_propagation_signals("modeled", artifact="a.md", required_labels=["modeled"])
    assert any("forgeable (KH-T02)" in lim for lim in rows[0]["limits"])
    assert any("badge registry" in lim for lim in rows[0]["limits"])


def test_s3_presence_is_forgeable_the_inverted_artifact_still_reads_present():
    """KH-T02, demonstrated: an artifact stating the OPPOSITE keeps its label and passes.

    This is the limit, pinned. It is why S3 is a SIGNAL and never a block.
    """
    inverted = "This run is n=1-directional, which is why the result generalizes to all repos.\n"
    rows = ts.label_propagation_signals(inverted, artifact="a.md",
                                        required_labels=["n=1-directional"])
    assert rows[0]["class"] == "label-present"
    assert rows[0]["verdict"] == "CLEAR"


# =============================================================================
# 7. THE FACT-TABLE ROW SHAPE + DETERMINISM
# =============================================================================

_ROW_KEYS = {"blocking", "class", "detail", "detector", "humility", "limits", "provenance",
             "schema", "subject", "verdict"}


def test_every_row_has_the_fact_table_shape(graph):
    for row in ts.s1_signals(graph):
        assert set(row) == _ROW_KEYS
        assert row["schema"] == ts.ROW_SCHEMA
        assert row["humility"] == ts.HUMILITY_RULE
        assert isinstance(row["limits"], list) and row["limits"] == sorted(row["limits"])
        assert isinstance(row["provenance"], list)


def test_row_schema_is_marked_provisional():
    """The durable emitter is the grounding agent's (DESIGN §4). This is the producer contract."""
    assert ts.ROW_SCHEMA.endswith("/v1-provisional")


def test_humility_line_is_carried_verbatim():
    assert ts.HUMILITY_LINE == (
        "the judgment+human layers found all of these; "
        "the automated mechanical gates found none"
    )
    assert ts.HUMILITY_RULE == "Detectors ATTEST and NARROW; judges judge."
    assert ts.fact_table([])["humility"] == ts.HUMILITY_LINE


def test_fact_table_is_deterministic_and_sorted(graph):
    rows = ts.s1_signals(graph)
    first = ts.render_fact_table(rows)
    second = ts.render_fact_table(list(reversed(rows)))
    assert first == second, "row order leaked into the artifact (Determinism Doctrine law 3)"

    parsed = json.loads(first)
    keys = [(r["detector"], r["class"], r["subject"], r["detail"]) for r in parsed["rows"]]
    assert keys == sorted(keys)
    assert parsed["tier"] == "SIGNAL"


def test_rebuilding_the_graph_reproduces_the_same_bytes():
    """Same corpus in ⇒ same fact table out, on a freshly built graph."""
    a = graph_gen.build_graph(CORPUS, generated_at=_PINNED_CLOCK)
    b = graph_gen.build_graph(CORPUS, generated_at=_PINNED_CLOCK)
    assert ts.render_fact_table(ts.s1_signals(a)) == ts.render_fact_table(ts.s1_signals(b))


def test_fact_table_rejects_a_blocking_row():
    row = ts.build_row(detector="S1", row_class="c", verdict="SIGNAL", subject="s", detail="d")
    row["verdict"] = "REFUSE"
    with pytest.raises(ValueError):
        ts.fact_table([row])


def test_is_test_path_uses_path_components_not_substrings():
    assert ts.is_test_path("tests/foo.py") is True
    assert ts.is_test_path("pkg/test/foo.py") is True
    assert ts.is_test_path("tools/tests/fixtures/a.py") is True
    assert ts.is_test_path("contest/foo.py") is False
    assert ts.is_test_path("latest.py") is False
