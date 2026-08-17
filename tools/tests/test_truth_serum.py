"""Tests for truth_serum.py — Truth Serum v1's blocking detectors B1, B3, B5.

Detectors ATTEST and NARROW; judges judge.

Coverage
--------
(1)  B1: each of the five DESIGN §3.1 syntactic families blocks in a fixture repo.
(2)  B1: a ``DEF-*`` reference on the offending line suppresses each family (D3b).
(3)  B1: the three explicit mechanical suppressors (``__init__.py`` / abstract method /
     protocol handler) suppress, and are code predicates rather than judgment.
(4)  B1 (E3): a suspected-legitimacy class NEVER suppresses — the finding still BLOCKS
     and additionally routes to the signal channel.
(5)  Anti-vacuity companions (TM-D3): B1 refuses on a zero-function scan / an absent /
     unreadable / internally-inconsistent / STALE graph; B3 refuses on an empty
     modified-file set and on an unreadable member; B5 refuses on an unreadable
     artifact and reports a zero-candidate artifact AS zero-candidate.
(6)  B3: TBD/FIXME/XXX block; a same-line ``DEF-*`` or issue ref suppresses.
(7)  B3: the DEF-9 boundary is REAL, not prose — a fictional ``DEF-9999`` is suppressed,
     pinning the stated limit rather than implying ledger validation that does not exist.
(8)  B5: existence is checked (missing file, line past EOF, unresolved wikilink, ``..``
     traversal); "support" is never claimed.
(9)  The TM-D2 humility line is verbatim in every public docstring AND in every report
     string, and is not overridable.
(10) Determinism (D172): same inputs => same bytes, over a re-run and a re-parse.
(11) Exec safety: no subprocess / eval / exec anywhere in the module (AST-asserted).
(12) The path-guard family invariant is verified here (the registry row itself is a
     conductor integration act, not a builder self-paste).
(13) Stated limits are PINNED BY TESTS THAT DEMONSTRATE THE MISS, never prosed away.
(14) D-26: the DetectorReport invariants are enforced at the boundary, not promised.

No network, no subprocess, no mutation of the repo.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

import graph_gen
import truth_serum as ts

TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = TOOLS_DIR / "truth_serum.py"

# A pinned clock so every fixture graph is byte-stable (DETERMINISM-DOCTRINE law 7).
_PINNED_CLOCK = "2020-01-01T00:00:00+00:00"


# ---------------------------------------------------------------------------
# Fixture-repo helpers
# ---------------------------------------------------------------------------

def _write(root: Path, rel: str, text: str) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return rel


def _case_dir(tmp_path: Path, *parts: str) -> Path:
    """A per-parametrised-case fixture dir with a STABLE name.

    ``hash()`` on a str is PYTHONHASHSEED-dependent (Determinism Doctrine law 3); a
    detector suite that exists to enforce that doctrine does not get to break it in its
    own fixtures, even for a directory name.
    """
    digest = hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()[:12]
    root = tmp_path / f"repo_{digest}"
    root.mkdir()
    return root


def _build_graph(root: Path) -> dict:
    """Build kata.graph.json over the fixture repo, exactly as the harness would."""
    files = sorted(p for p in root.rglob("*.py"))
    return graph_gen.build_graph(root, files=files, generated_at=_PINNED_CLOCK)


def _b1(root: Path, rels: list[str], graph: dict | None = None) -> ts.DetectorReport:
    return ts.scan_stub_bodies(root, graph if graph is not None else _build_graph(root), rels)


# The five DESIGN §3.1 families, as source bodies. Each maps family -> (source, symbol).
_FAMILY_SOURCES: dict[str, str] = {
    ts.FAMILY_PASS_ONLY: "def f_pass():\n    pass\n",
    ts.FAMILY_TODO_COMMENT_ONLY: "def f_todo():\n    # TODO: wire this up\n    pass\n",
    ts.FAMILY_RAISE_NOTIMPLEMENTED: "def f_raise():\n    raise NotImplementedError\n",
    ts.FAMILY_LOG_ONLY: "import logging\n\n\ndef f_log():\n    logging.info('called')\n",
    ts.FAMILY_HARDCODED_EMPTY_RETURN: "def f_ret():\n    return []\n",
}


# ===========================================================================
# (1) + the declared evidence node
# ===========================================================================

def test_stub_body_without_def_ref_blocks(tmp_path: Path) -> None:
    """DECLARED EVIDENCE NODE. A stub body with no DEF-* reference BLOCKS.

    All five DESIGN §3.1 syntactic families are exercised, each in its own fixture
    repo, so a family that silently stopped matching cannot hide behind its siblings.
    """
    assert set(_FAMILY_SOURCES) == set(ts.STUB_FAMILIES), (
        "this test must exercise exactly the five DESIGN families"
    )
    for family, source in sorted(_FAMILY_SOURCES.items()):
        root = tmp_path / f"repo_{family}"
        root.mkdir()
        rel = _write(root, "mod.py", source)
        report = _b1(root, [rel])
        assert report.verdict == ts.VERDICT_BLOCK, f"{family}: {report.summary()}"
        assert report.blocking is True
        assert report.certifies is False
        assert [f.family for f in report.findings] == [family]
        assert report.findings[0].path == "mod.py"
        assert report.candidates_scanned >= 1
        assert ts.HUMILITY_LINE in report.summary()


def test_a_real_implementation_passes(tmp_path: Path) -> None:
    """The detector is not a rubber stamp in the other direction either."""
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "mod.py", "def add(a, b):\n    total = a + b\n    return total\n")
    report = _b1(root, [rel])
    assert report.verdict == ts.VERDICT_PASS
    assert report.certifies is True
    assert report.findings == ()
    assert report.candidates_scanned == 1


# ===========================================================================
# (2) D3b same-line suppression
# ===========================================================================

def test_def_ref_on_the_offending_line_suppresses_every_family(tmp_path: Path) -> None:
    annotated = {
        ts.FAMILY_PASS_ONLY: "def f_pass():\n    pass  # DEF-42 — lands in W7\n",
        ts.FAMILY_TODO_COMMENT_ONLY: "def f_todo():\n    # TODO(DEF-42): wire this up\n    pass\n",
        ts.FAMILY_RAISE_NOTIMPLEMENTED: "def f_raise():\n    raise NotImplementedError  # DEF-42\n",
        ts.FAMILY_LOG_ONLY: "import logging\n\n\ndef f_log():\n    logging.info('x')  # DEF-42\n",
        ts.FAMILY_HARDCODED_EMPTY_RETURN: "def f_ret():\n    return []  # DEF-42\n",
    }
    assert set(annotated) == set(ts.STUB_FAMILIES)
    for family, source in sorted(annotated.items()):
        root = tmp_path / f"ok_{family}"
        root.mkdir()
        rel = _write(root, "mod.py", source)
        report = _b1(root, [rel])
        assert report.verdict == ts.VERDICT_PASS, f"{family}: {report.summary()}"
        assert report.findings == ()


def test_def_ref_on_a_neighbouring_line_does_not_suppress(tmp_path: Path) -> None:
    """The rule is SAME-line. A nearby promise is one refactor from being an orphan."""
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "mod.py", "# DEF-42 — this function is a stub\ndef f():\n    pass\n")
    report = _b1(root, [rel])
    assert report.verdict == ts.VERDICT_BLOCK
    assert report.findings[0].family == ts.FAMILY_PASS_ONLY


# ===========================================================================
# (3) the three explicit mechanical suppressors
# ===========================================================================

@pytest.mark.parametrize(
    "rel,source",
    [
        ("pkg/__init__.py", "def f():\n    pass\n"),
        ("mod.py", "import abc\n\n\nclass C(abc.ABC):\n    @abc.abstractmethod\n    def f(self):\n        pass\n"),
        ("mod.py", "from abc import ABC\n\n\nclass C(ABC):\n    def f(self):\n        pass\n"),
        ("mod.py", "class C(metaclass=ABCMeta):\n    def f(self):\n        pass\n"),
        ("mod.py", "from typing import Protocol\n\n\nclass P(Protocol):\n    def handle(self):\n        pass\n"),
        ("mod.py", "from typing import Protocol\n\n\nclass P(Protocol[int]):\n    def handle(self):\n        pass\n"),
    ],
)
def test_explicit_mechanical_suppressors_suppress(tmp_path: Path, rel: str, source: str) -> None:
    root = _case_dir(tmp_path, rel, source)
    _write(root, rel, source)
    report = _b1(root, [rel])
    assert report.verdict == ts.VERDICT_PASS, report.summary()
    assert report.findings == ()


def test_suppressor_set_is_exactly_three_explicit_classes() -> None:
    """E3: the suppressor set is pinned. Growing it is an ESCALATION, not an edit."""
    assert ts.SUPPRESSOR_CLASSES == ("init-module", "abstract-method", "protocol-handler")
    # The predicates are code, not judgment: each is a literal-name comparison living in
    # a named function, so a reviewer can read the whole suppression surface in one place.
    src = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert {"_suppressor_for", "_class_suppressor"} <= names


def test_a_non_suppressed_class_still_blocks(tmp_path: Path) -> None:
    """A plain class's empty method is NOT legitimately-empty by default."""
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "mod.py", "class C:\n    def f(self):\n        pass\n")
    report = _b1(root, [rel])
    assert report.verdict == ts.VERDICT_BLOCK
    assert report.findings[0].symbol == "f"


# ===========================================================================
# (4) E3 — residual legitimacy routes to the signal channel, never suppresses
# ===========================================================================

def test_overload_stub_blocks_and_routes_to_the_signal_channel(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(
        root, "mod.py",
        "from typing import overload\n\n\n@overload\ndef f(a: int) -> int:\n    pass\n",
    )
    report = _b1(root, [rel])
    # It BLOCKS — the suspected legitimacy did NOT silently suppress it.
    assert report.verdict == ts.VERDICT_BLOCK
    assert len(report.findings) == 1
    # AND it signals, so a judge decides with the fact in hand.
    assert [s.family for s in report.signals] == ["overload-decorated"]
    assert "signal(s) routed to the signal channel" in report.summary()


def test_unresolvable_class_base_blocks_and_signals(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "mod.py", "class C(make_base()):\n    def f(self):\n        pass\n")
    report = _b1(root, [rel])
    assert report.verdict == ts.VERDICT_BLOCK
    assert [s.family for s in report.signals] == ["unresolvable-class-base"]


def test_signal_classes_are_disjoint_from_suppressor_classes() -> None:
    assert not set(ts.SIGNAL_CLASSES) & set(ts.SUPPRESSOR_CLASSES)


# ===========================================================================
# (5) the anti-vacuity companions — the second declared evidence node
# ===========================================================================

def test_zero_input_refuses_to_certify(tmp_path: Path) -> None:
    """DECLARED EVIDENCE NODE. Every detector REFUSES over its vacuous input (TM-D3).

    Absence of a precondition is never rendered as a pass. Each of the three detectors
    is driven to its own zero-input condition and each must return REFUSE with a
    populated reason — and none may report ``certifies``.
    """
    root = tmp_path / "repo"
    root.mkdir()

    # B1 over a file with zero functions: nothing was examined, so nothing is certified.
    rel = _write(root, "mod.py", "CONSTANT = 1\n")
    b1 = ts.scan_stub_bodies(root, _build_graph(root), [rel])
    assert b1.verdict == ts.VERDICT_REFUSE
    assert "zero functions" in (b1.refusal_reason or "")

    # B1 with no graph at all: absence is a refusal, not a pass.
    b1_nograph = ts.scan_stub_bodies(root, None, [rel])
    assert b1_nograph.verdict == ts.VERDICT_REFUSE
    assert "absent" in (b1_nograph.refusal_reason or "")

    # B3 over an empty modified-file set: nothing scanned => nothing certified.
    b3 = ts.scan_debt_markers(root, [])
    assert b3.verdict == ts.VERDICT_REFUSE
    assert "EMPTY" in (b3.refusal_reason or "")

    # B5 over an artifact it cannot read: refuses to certify a file it never saw.
    b5 = ts.resolve_citations(root, "does-not-exist.md")
    assert b5.verdict == ts.VERDICT_REFUSE
    assert "could not be read" in (b5.refusal_reason or "")

    for report in (b1, b1_nograph, b3, b5):
        assert report.blocking is True
        assert report.certifies is False
        assert report.findings == ()
        assert report.refusal_reason
        assert ts.HUMILITY_LINE in report.summary()


def test_b1_refuses_a_stale_graph(tmp_path: Path) -> None:
    """A graph that no longer matches the file on disk cannot certify that file."""
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "mod.py", "def f():\n    return 1\n")
    graph = _build_graph(root)
    (root / rel).write_text("def f():\n    pass\n", encoding="utf-8")  # edit AFTER the graph
    report = ts.scan_stub_bodies(root, graph, [rel])
    assert report.verdict == ts.VERDICT_REFUSE
    assert "STALE" in (report.refusal_reason or "")


def test_b1_refuses_a_file_absent_from_the_graph(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    covered = _write(root, "covered.py", "def f():\n    return 1\n")
    graph = _build_graph(root)
    uncovered = _write(root, "uncovered.py", "def g():\n    pass\n")
    report = ts.scan_stub_bodies(root, graph, [covered, uncovered])
    assert report.verdict == ts.VERDICT_REFUSE
    assert "absent from the graph" in (report.refusal_reason or "")


def test_b1_refuses_an_internally_inconsistent_graph(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "mod.py", "def f():\n    pass\n")
    graph = _build_graph(root)
    graph["meta"]["repoHash"] = "0" * 64  # tampered
    report = ts.scan_stub_bodies(root, graph, [rel])
    assert report.verdict == ts.VERDICT_REFUSE
    assert "repoHash" in (report.refusal_reason or "")


def test_b1_refuses_an_unreadable_graph_artifact(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "mod.py", "def f():\n    pass\n")
    bad = root / "kata.graph.json"
    bad.write_text("{not json", encoding="utf-8")
    report = ts.scan_stub_bodies(root, bad, [rel])
    assert report.verdict == ts.VERDICT_REFUSE
    assert "not valid JSON" in (report.refusal_reason or "")


def test_b1_refuses_an_unparseable_source_file(tmp_path: Path) -> None:
    """A file the AST cannot read is a refusal, never a silent skip."""
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "mod.py", "def f():\n    pass\n")
    graph = _build_graph(root)
    # Corrupt the source AND re-point the graph hash so the staleness gate is not the
    # thing under test here — the parse failure is.
    broken = "def f(:\n    pass\n"
    # write_bytes, not write_text: on Windows write_text translates \n -> \r\n, which
    # would trip the STALE gate instead of the parse gate this test is aiming at.
    (root / rel).write_bytes(broken.encode("utf-8"))
    for node in graph["nodes"]:
        if node.get("path") == rel:
            node["hash"] = graph_gen._bytes_hash(broken.encode("utf-8"))
    graph["meta"]["repoHash"] = graph_gen._repo_hash(
        {n["path"]: n["hash"] for n in graph["nodes"] if n["kind"] == "file"}
    )
    report = ts.scan_stub_bodies(root, graph, [rel])
    assert report.verdict == ts.VERDICT_REFUSE
    assert "does not parse" in (report.refusal_reason or "")


def test_b3_refuses_an_unreadable_member_of_its_input_set(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "ok.md", "clean\n")
    report = ts.scan_debt_markers(root, ["ok.md", "gone.md"])
    assert report.verdict == ts.VERDICT_REFUSE
    assert "unreadable" in (report.refusal_reason or "")


def test_b5_reports_zero_candidates_as_zero_candidates(tmp_path: Path) -> None:
    """A zero-candidate artifact is NEVER rendered as 'all citations resolve'."""
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "artifact.md", "Prose with no citations at all.\n")
    report = ts.resolve_citations(root, rel)
    assert report.verdict == ts.VERDICT_ZERO_CANDIDATE
    assert report.candidates_scanned == 0
    assert report.blocking is False
    # The load-bearing half: a zero-candidate report does NOT certify.
    assert report.certifies is False
    assert "ZERO candidates" in report.summary()
    assert "all resolve" in report.summary()  # named only to be denied


# ===========================================================================
# (6) + (7) B3 — the same-line rule, and the DEF-9 boundary
# ===========================================================================

@pytest.mark.parametrize("marker", ["TBD", "FIXME", "XXX"])
def test_debt_marker_without_def_ref_blocks(tmp_path: Path, marker: str) -> None:
    root = tmp_path / f"repo{marker}"
    root.mkdir()
    rel = _write(root, "notes.md", f"line one\nsome {marker} left behind\nline three\n")
    report = ts.scan_debt_markers(root, [rel])
    assert report.verdict == ts.VERDICT_BLOCK
    assert len(report.findings) == 1
    assert report.findings[0].line == 2
    assert report.findings[0].family == f"debt-marker:{marker}"


@pytest.mark.parametrize(
    "line",
    [
        "some FIXME left behind  <!-- DEF-42 -->",
        "some FIXME left behind (GH-17)",
        "some FIXME left behind (#17)",
        "some FIXME left behind https://example.invalid/o/r/issues/17",
    ],
)
def test_same_line_formal_follow_up_suppresses(tmp_path: Path, line: str) -> None:
    root = _case_dir(tmp_path, line)
    rel = _write(root, "notes.md", f"{line}\n")
    report = ts.scan_debt_markers(root, [rel])
    assert report.verdict == ts.VERDICT_PASS, report.summary()


def test_follow_up_on_the_next_line_does_not_suppress(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "notes.md", "some FIXME left behind\ntracked by DEF-42\n")
    report = ts.scan_debt_markers(root, [rel])
    assert report.verdict == ts.VERDICT_BLOCK
    assert report.findings[0].line == 1


def test_b3_does_not_match_todo_or_lowercase(tmp_path: Path) -> None:
    """Stated limit, pinned: the marker set is TBD/FIXME/XXX, uppercase, word-bounded."""
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "notes.md", "a TODO here\na fixme here\nPREFIXMEANS nothing\n")
    report = ts.scan_debt_markers(root, [rel])
    assert report.verdict == ts.VERDICT_PASS


def test_b3_def9_boundary_is_real_a_fictional_def_id_is_suppressed(tmp_path: Path) -> None:
    """DEF-9 boundary, DEMONSTRATED rather than prosed.

    B3 covers the same-line BLOCKER rule and is NOT an entry-schema parse: it does not
    check that the cited DEF id exists in the ledger. This test pins that limit so the
    docstring cannot quietly start reading as ledger validation.
    """
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, ".planning/DEFERRED.md", "## DEF-1 — a real entry · OPEN (2026-08-17)\n")
    rel = _write(root, "notes.md", "some FIXME here  <!-- DEF-9999 -->\n")
    report = ts.scan_debt_markers(root, [rel])
    assert report.verdict == ts.VERDICT_PASS
    assert "deferral entry-schema parse" in (ts.scan_debt_markers.__doc__ or "")
    assert "DEF-9" in (ts.scan_debt_markers.__doc__ or "")


# ===========================================================================
# (8) B5 — existence is MECH, support is judgment
# ===========================================================================

def test_b5_resolves_real_citations(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "src/mod.py", "a = 1\nb = 2\nc = 3\n")
    _write(root, "docs/DESIGN.md", "design\n")
    rel = _write(root, "artifact.md", "See src/mod.py:2 and [[DESIGN]] and [[docs/DESIGN.md]].\n")
    report = ts.resolve_citations(root, rel)
    assert report.verdict == ts.VERDICT_PASS, report.summary()
    assert report.candidates_scanned == 3


@pytest.mark.parametrize(
    "body,expect_family",
    [
        ("See src/missing.py:2 here.\n", "file-line-citation"),
        ("See src/mod.py:99 here.\n", "file-line-citation"),
        ("See src/../../etc/shadow.conf:1 here.\n", "file-line-citation"),
        ("See [[NoSuchDoc]] here.\n", "wikilink-citation"),
    ],
)
def test_b5_blocks_an_unresolvable_citation(tmp_path: Path, body: str, expect_family: str) -> None:
    root = _case_dir(tmp_path, body)
    _write(root, "src/mod.py", "a = 1\nb = 2\nc = 3\n")
    rel = _write(root, "artifact.md", body)
    report = ts.resolve_citations(root, rel)
    assert report.verdict == ts.VERDICT_BLOCK, report.summary()
    assert report.findings[0].family == expect_family


def test_b5_ignores_urls_and_non_path_colon_prose(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(
        root, "artifact.md",
        "See https://example.invalid/a/b.py:12 and DESIGN §3.1: the rule, at 10:30.\n",
    )
    report = ts.resolve_citations(root, rel)
    assert report.verdict == ts.VERDICT_ZERO_CANDIDATE, report.summary()


def test_b5_claims_existence_never_support() -> None:
    """The honest limit is in the contract, and the API has no 'supports' surface."""
    doc = ts.resolve_citations.__doc__ or ""
    assert "Existence is MECH; support is judgment." in doc.replace("\n    ", " ")
    assert not [n for n in dir(ts) if "support" in n.lower()]


# ===========================================================================
# (9) the TM-D2 humility line
# ===========================================================================

def test_humility_line_is_verbatim_and_everywhere() -> None:
    assert ts.HUMILITY_LINE == "Detectors ATTEST and NARROW; judges judge."
    src = MODULE_PATH.read_text(encoding="utf-8")
    module_doc = ast.get_docstring(ast.parse(src)) or ""
    assert ts.HUMILITY_LINE in module_doc
    for fn in (ts.scan_stub_bodies, ts.scan_debt_markers, ts.resolve_citations,
               ts.run_blocking_detectors):
        assert ts.HUMILITY_LINE in (fn.__doc__ or "").replace("\n    ", " "), fn.__name__
    for cls in (ts.Finding, ts.DetectorReport, ts.TruthSerumError):
        assert ts.HUMILITY_LINE in (cls.__doc__ or "").replace("\n    ", " "), cls.__name__


def test_humility_line_is_not_overridable() -> None:
    with pytest.raises(ts.TruthSerumError):
        ts.DetectorReport(detector="B1", verdict=ts.VERDICT_PASS, humility="detectors judge")


def test_every_report_string_carries_the_humility_line(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "mod.py", "def f():\n    pass\n")
    art = _write(root, "artifact.md", "See mod.py:1.\n")
    reports = ts.run_blocking_detectors(root, _build_graph(root), [rel], [art])
    assert set(reports) == {"B1", "B3", "B5:artifact.md"}
    for key, report in sorted(reports.items()):
        assert report.humility == ts.HUMILITY_LINE, key
        assert ts.HUMILITY_LINE in report.summary(), key
        assert ts.HUMILITY_LINE in report.to_json(), key


# ===========================================================================
# (10) determinism — same inputs => same bytes (D172)
# ===========================================================================

def test_determinism_same_inputs_same_bytes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    rels = [
        _write(root, "a.py", "def f():\n    pass\n\n\ndef g():\n    raise NotImplementedError\n"),
        _write(root, "b.py", "def h():\n    return {}\n"),
        _write(root, "notes.md", "a FIXME here\nanother XXX there\n"),
    ]
    art = _write(root, "artifact.md", "See a.py:1 and b.py:99 and [[nope]].\n")
    graph = _build_graph(root)

    first = {k: v.to_json() for k, v in ts.run_blocking_detectors(root, graph, rels, [art]).items()}
    second = {k: v.to_json() for k, v in ts.run_blocking_detectors(root, graph, rels, [art]).items()}
    assert first == second
    # And stable against re-reading the graph from disk rather than from memory.
    graph_path = root / "kata.graph.json"
    graph_path.write_text(json.dumps(graph, sort_keys=True), encoding="utf-8")
    third = {k: v.to_json()
             for k, v in ts.run_blocking_detectors(root, graph_path, rels, [art]).items()}
    assert first == third
    # Findings are in an explicit total order, not filesystem order.
    b1 = ts.scan_stub_bodies(root, graph, list(reversed(rels)))
    assert [f.sort_key() for f in b1.findings] == sorted(f.sort_key() for f in b1.findings)


def test_report_json_is_sort_keyed(tmp_path: Path) -> None:
    report = ts.DetectorReport(detector="B3", verdict=ts.VERDICT_REFUSE, refusal_reason="x")
    payload = report.to_json()
    assert json.loads(payload)["verdict"] == ts.VERDICT_REFUSE
    assert payload == json.dumps(json.loads(payload), sort_keys=True, ensure_ascii=False, indent=2)


# ===========================================================================
# (11) exec safety — asserted, not asserted-about
# ===========================================================================

def test_no_exec_sinks_anywhere_in_module() -> None:
    """The module spawns no subprocess and calls no eval/exec, BY CONTRACT.

    Asserted mechanically (the evidence_grammar / drift_gate precedent) so the claim in
    the module docstring — and the consequent absence of a protocol/exec-safety.md sink
    row — cannot rot into a stale comment.
    """
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    banned_modules = {"subprocess", "os", "shutil", "socket", "pty", "multiprocessing"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_modules, alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_modules, node.module
        elif isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else None
            assert name not in ("eval", "exec", "compile", "__import__"), name


# ===========================================================================
# (12) the path-guard family invariant (registry row = conductor integration act)
# ===========================================================================

def test_guard_path_rejects_traversal() -> None:
    with pytest.raises(ValueError):
        ts._guard_path("../evil/x")


def test_guard_path_accepts_a_clean_relative_path() -> None:
    ts._guard_path(".kata/sub/thing")


def test_modified_file_set_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        ts.scan_debt_markers(tmp_path, ["../../etc/passwd"])


def test_a_single_path_is_not_silently_treated_as_an_iterable(tmp_path: Path) -> None:
    """'abc.py' iterated character-by-character would be a silent, wrong scan."""
    with pytest.raises(ts.TruthSerumError):
        ts.scan_debt_markers(tmp_path, "notes.md")
    with pytest.raises(ts.TruthSerumError):
        ts.run_blocking_detectors(tmp_path, None, [], "artifact.md")


# ===========================================================================
# (13) stated limits, pinned by tests that DEMONSTRATE the miss
# ===========================================================================

def test_ellipsis_only_body_is_a_stated_miss(tmp_path: Path) -> None:
    """STATED LIMIT: `...`-only bodies are not in the v1 five-family set.

    This test exists to make the miss visible and versioned rather than to pretend it
    away. If a future wave adds the family, this test flips — deliberately, in a diff.
    """
    root = tmp_path / "repo"
    root.mkdir()
    rel = _write(root, "mod.py", "def f():\n    ...\n")
    report = _b1(root, [rel])
    assert report.verdict == ts.VERDICT_PASS
    assert "(Ellipsis) -only body is **not** in the v1 family set" in (ts.__doc__ or "")


def test_non_python_modified_files_are_reported_not_dropped(tmp_path: Path) -> None:
    """STATED LIMIT: B1 is Python-only, and says so in the report rather than vanishing."""
    root = tmp_path / "repo"
    root.mkdir()
    py = _write(root, "mod.py", "def f():\n    pass\n")
    md = _write(root, "notes.md", "prose\n")
    report = _b1(root, [py, md])
    assert report.verdict == ts.VERDICT_BLOCK
    assert report.files_scanned == ("mod.py",)
    assert any("notes.md" in n and "NOT scanned" in n for n in report.notes)


# ===========================================================================
# (14) D-26 — the promised invariants are enforced at the boundary
# ===========================================================================

@pytest.mark.parametrize(
    "kwargs",
    [
        {"detector": "B1", "verdict": "MAYBE"},
        {"detector": "B1", "verdict": ts.VERDICT_REFUSE},                       # reason missing
        {"detector": "B1", "verdict": ts.VERDICT_PASS, "refusal_reason": "why"},  # reason w/o REFUSE
        {"detector": "B1", "verdict": ts.VERDICT_BLOCK},                        # no findings
        {"detector": "B1", "verdict": ts.VERDICT_ZERO_CANDIDATE, "candidates_scanned": 3},
    ],
)
def test_detector_report_enforces_its_own_contract(kwargs: dict) -> None:
    with pytest.raises(ts.TruthSerumError):
        ts.DetectorReport(**kwargs)


def test_pass_is_impossible_with_findings() -> None:
    finding = ts.Finding(detector="B1", path="mod.py", line=1, family="pass-only", message="x")
    with pytest.raises(ts.TruthSerumError):
        ts.DetectorReport(detector="B1", verdict=ts.VERDICT_PASS, findings=(finding,),
                          candidates_scanned=1)


def test_only_pass_certifies() -> None:
    finding = ts.Finding(detector="B1", path="m.py", line=1, family="pass-only", message="x")
    cases = {
        ts.VERDICT_PASS: ts.DetectorReport(detector="B1", verdict=ts.VERDICT_PASS, candidates_scanned=1),
        ts.VERDICT_BLOCK: ts.DetectorReport(detector="B1", verdict=ts.VERDICT_BLOCK,
                                            findings=(finding,), candidates_scanned=1),
        ts.VERDICT_REFUSE: ts.DetectorReport(detector="B1", verdict=ts.VERDICT_REFUSE,
                                             refusal_reason="nothing to scan"),
        ts.VERDICT_ZERO_CANDIDATE: ts.DetectorReport(detector="B1",
                                                     verdict=ts.VERDICT_ZERO_CANDIDATE),
    }
    assert [v for v, r in sorted(cases.items()) if r.certifies] == [ts.VERDICT_PASS]
    assert sorted(v for v, r in cases.items() if r.blocking) == sorted(ts.BLOCKING_VERDICTS)
