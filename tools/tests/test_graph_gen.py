"""test_graph_gen.py — TDD for graph_gen.build_graph.

Tests run against in-memory fixture files written to tmp_path.
Schema required fields are validated per protocol/graph.md.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

FIXTURE_A = """\
import fixture_b

def greet(name):
    return f"hello {name}"

class Greeter:
    def greet(self, name):
        return greet(name)
"""

# Same-name function defined twice — collision ordinal test
FIXTURE_B = """\
def process(data):
    return data

def process(data, extra):
    return (data, extra)
"""

# Extra file with import of fixture_a (for cross-file import edge)
FIXTURE_C = """\
from fixture_a import greet

def run():
    return greet("world")
"""


def write_fixtures(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Write the three fixture .py files into tmp_path and return their paths."""
    a = tmp_path / "fixture_a.py"
    b = tmp_path / "fixture_b.py"
    c = tmp_path / "fixture_c.py"
    a.write_text(FIXTURE_A, encoding="utf-8")
    b.write_text(FIXTURE_B, encoding="utf-8")
    c.write_text(FIXTURE_C, encoding="utf-8")
    return a, b, c


# ---------------------------------------------------------------------------
# Schema validator (inline — mirrors protocol/graph.md required fields)
# ---------------------------------------------------------------------------

FILE_NODE_REQUIRED = {"id", "kind", "path", "hash", "rank"}
SYMBOL_NODE_REQUIRED = {"id", "kind", "path", "name", "symKind", "span", "rank"}
EDGE_REQUIRED = {"src", "dst", "kind", "weight"}
VALID_SYM_KINDS = {"function", "class", "method", "interface", "type", "constant", "other"}
VALID_EDGE_KINDS = {"def", "ref", "call", "import"}


def validate_graph(graph: dict) -> list[str]:
    """Return a list of schema violations; empty list == valid."""
    errors: list[str] = []
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    meta = graph.get("meta", {})

    # meta
    for mf in ("backend", "repoHash", "generatedAt"):
        if mf not in meta:
            errors.append(f"meta missing field: {mf}")

    node_ids: set[str] = set()
    for i, node in enumerate(nodes):
        nid = node.get("id", f"<node[{i}] no id>")
        node_ids.add(nid)
        kind = node.get("kind")
        if kind == "file":
            for f in FILE_NODE_REQUIRED:
                if f not in node:
                    errors.append(f"file node {nid!r} missing required field: {f}")
            if not isinstance(node.get("rank"), (int, float)):
                errors.append(f"file node {nid!r} rank must be float")
        elif kind == "symbol":
            for f in SYMBOL_NODE_REQUIRED:
                if f not in node:
                    errors.append(f"symbol node {nid!r} missing required field: {f}")
            sym_kind = node.get("symKind")
            if sym_kind not in VALID_SYM_KINDS:
                errors.append(f"symbol node {nid!r} invalid symKind: {sym_kind!r}")
            span = node.get("span")
            if not (isinstance(span, list) and len(span) == 2):
                errors.append(f"symbol node {nid!r} span must be [start, end]")
            else:
                s, e = span
                if not (isinstance(s, int) and isinstance(e, int) and s >= 1 and e >= s):
                    errors.append(f"symbol node {nid!r} span {span} must be 1-indexed inclusive")
            if not isinstance(node.get("rank"), (int, float)):
                errors.append(f"symbol node {nid!r} rank must be float")
        else:
            errors.append(f"node {nid!r} has invalid kind: {kind!r}")

    for j, edge in enumerate(edges):
        for f in EDGE_REQUIRED:
            if f not in edge:
                errors.append(f"edge[{j}] missing required field: {f}")
        if edge.get("kind") not in VALID_EDGE_KINDS:
            errors.append(f"edge[{j}] invalid kind: {edge.get('kind')!r}")
        if not isinstance(edge.get("weight"), (int, float)):
            errors.append(f"edge[{j}] weight must be float")

    return errors


# ---------------------------------------------------------------------------
# Tests — written first (RED before implementation)
# ---------------------------------------------------------------------------


def test_import_available():
    """graph_gen module can be imported."""
    import graph_gen  # noqa: F401


def test_build_graph_returns_dict(tmp_path):
    """build_graph returns a dict with nodes/edges/meta keys."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    assert isinstance(g, dict)
    assert "nodes" in g
    assert "edges" in g
    assert "meta" in g


def test_file_nodes_exist(tmp_path):
    """A file node exists for each discovered .py file."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    file_nodes = {n["path"]: n for n in g["nodes"] if n["kind"] == "file"}
    paths = set(file_nodes.keys())
    # All three fixture files should appear (repo-relative, forward-slash)
    assert any("fixture_a" in p for p in paths), f"fixture_a missing from {paths}"
    assert any("fixture_b" in p for p in paths), f"fixture_b missing from {paths}"
    assert any("fixture_c" in p for p in paths), f"fixture_c missing from {paths}"


def test_file_nodes_have_required_fields(tmp_path):
    """File nodes carry id, kind, path, hash, rank."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    file_nodes = [n for n in g["nodes"] if n["kind"] == "file"]
    assert file_nodes, "no file nodes found"
    for n in file_nodes:
        for field in FILE_NODE_REQUIRED:
            assert field in n, f"file node {n.get('id')!r} missing {field!r}"
        assert isinstance(n["rank"], float), f"rank must be float in {n['id']!r}"
        assert n["hash"], f"hash must be non-empty in {n['id']!r}"


def test_function_symbol_node(tmp_path):
    """Top-level function_definition becomes a symbol node with symKind=function."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    sym_ids = {n["id"]: n for n in g["nodes"] if n["kind"] == "symbol"}

    # fixture_a.py has top-level function 'greet'
    greet_node = next(
        (n for n in sym_ids.values() if "fixture_a" in n["path"] and n["name"] == "greet"),
        None,
    )
    assert greet_node is not None, f"greet symbol not found; symbols: {list(sym_ids)}"
    assert greet_node["symKind"] == "function"
    # span is 1-indexed inclusive: greet is defined at line 3 in fixture_a
    start, end = greet_node["span"]
    assert start >= 1
    assert end >= start


def test_class_symbol_node(tmp_path):
    """Class definition becomes a symbol node with symKind=class."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    sym_nodes = [n for n in g["nodes"] if n["kind"] == "symbol"]
    class_nodes = [n for n in sym_nodes if n.get("symKind") == "class"]
    assert class_nodes, "no class symbol nodes found"
    names = [n["name"] for n in class_nodes]
    assert "Greeter" in names, f"Greeter class not found; class nodes: {names}"


def test_method_symbol_node(tmp_path):
    """Method inside a class becomes a symbol node with symKind=method."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    sym_nodes = [n for n in g["nodes"] if n["kind"] == "symbol"]
    method_nodes = [n for n in sym_nodes if n.get("symKind") == "method"]
    assert method_nodes, "no method symbol nodes found"
    names = [n["name"] for n in method_nodes]
    # fixture_a's Greeter.greet should be a method
    assert "greet" in names, f"greet method not found; method nodes: {names}"


def test_span_is_1indexed_inclusive(tmp_path):
    """Symbol span values are 1-indexed (start >= 1) and inclusive (end >= start)."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    sym_nodes = [n for n in g["nodes"] if n["kind"] == "symbol"]
    assert sym_nodes, "no symbol nodes found"
    for n in sym_nodes:
        span = n["span"]
        assert isinstance(span, list) and len(span) == 2, f"bad span in {n['id']!r}"
        s, e = span
        assert s >= 1, f"span start must be >= 1 in {n['id']!r}, got {s}"
        assert e >= s, f"span end must be >= start in {n['id']!r}, got span={span}"


def test_same_name_collision_ordinals(tmp_path):
    """Same-name function defined twice gets ids ::name and ::name~1."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    sym_nodes = [n for n in g["nodes"] if n["kind"] == "symbol"]
    b_syms = [n for n in sym_nodes if "fixture_b" in n["path"] and n["name"] == "process"]
    ids = {n["id"] for n in b_syms}
    assert len(b_syms) == 2, f"expected 2 'process' symbols in fixture_b, got {len(b_syms)}: {ids}"
    # One should have no suffix, one should have ~1
    suffixes = set()
    for n in b_syms:
        tail = n["id"].split("::")[-1]  # e.g. "process" or "process~1"
        suffixes.add(tail)
    assert "process" in suffixes, f"first collision should have no suffix; ids={ids}"
    assert "process~1" in suffixes, f"second collision should have ~1 suffix; ids={ids}"


def test_def_edges_file_to_symbol(tmp_path):
    """Every symbol has a 'def' edge from its file node."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    def_edges = {(e["src"], e["dst"]) for e in g["edges"] if e["kind"] == "def"}
    sym_nodes = [n for n in g["nodes"] if n["kind"] == "symbol"]
    assert sym_nodes, "no symbol nodes"
    for sym in sym_nodes:
        file_id = next(
            n["id"] for n in g["nodes"]
            if n["kind"] == "file" and n["path"] == sym["path"]
        )
        assert (file_id, sym["id"]) in def_edges, (
            f"missing def edge {file_id!r} -> {sym['id']!r}"
        )


def test_import_edge_file_to_file(tmp_path):
    """An import between two fixture files produces a file→file import edge."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    import_edges = [(e["src"], e["dst"]) for e in g["edges"] if e["kind"] == "import"]
    # fixture_a imports fixture_b; fixture_c imports fixture_a
    file_nodes = {n["path"]: n["id"] for n in g["nodes"] if n["kind"] == "file"}

    # At least one cross-file import edge must exist
    assert import_edges, f"no import edges found; edges: {[e['kind'] for e in g['edges']]}"

    # Check that the import edge endpoints are file node ids
    file_ids = set(file_nodes.values())
    for src, dst in import_edges:
        assert src in file_ids, f"import edge src {src!r} is not a file node id"
        assert dst in file_ids, f"import edge dst {dst!r} is not a file node id"


def test_meta_backend(tmp_path):
    """meta.backend == 'tree-sitter'."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    assert g["meta"]["backend"] == "tree-sitter"


def test_meta_required_fields(tmp_path):
    """meta has backend, repoHash, generatedAt."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    meta = g["meta"]
    assert "backend" in meta
    assert "repoHash" in meta
    assert "generatedAt" in meta
    assert meta["repoHash"], "repoHash must be non-empty"
    assert meta["generatedAt"], "generatedAt must be non-empty"


def test_full_schema_validation(tmp_path):
    """Full schema validator reports zero errors on graph output."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    errors = validate_graph(g)
    assert not errors, "Schema violations:\n" + "\n".join(errors)


def test_incremental_reuse(tmp_path):
    """Passing a previous graph reuses unchanged file nodes."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g1 = build_graph(tmp_path)
    # Build again with prev — must produce valid graph
    g2 = build_graph(tmp_path, prev=g1)
    errors = validate_graph(g2)
    assert not errors, "Schema violations on incremental build:\n" + "\n".join(errors)
    # Same node count (no file changed)
    assert len(g2["nodes"]) == len(g1["nodes"]), "incremental build changed node count despite no file changes"


def test_incremental_detects_change(tmp_path):
    """Incremental rebuild picks up a changed file."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g1 = build_graph(tmp_path)
    # Mutate fixture_b
    b = tmp_path / "fixture_b.py"
    b.write_text(FIXTURE_B + "\ndef new_func(): pass\n", encoding="utf-8")
    g2 = build_graph(tmp_path, prev=g1)
    errors = validate_graph(g2)
    assert not errors, "Schema violations after mutation:\n" + "\n".join(errors)
    # new_func should appear
    sym_ids = {n["id"] for n in g2["nodes"] if n["kind"] == "symbol"}
    assert any("new_func" in sid for sid in sym_ids), (
        f"new_func not found after incremental rebuild; symbols: {sym_ids}"
    )


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23)
# ---------------------------------------------------------------------------


def test_safe_path_rejects_dotdot_traversal():
    """_safe_path must raise ValueError for any path containing '..'."""
    from graph_gen import _safe_path

    with pytest.raises(ValueError, match="refusing path with '\\.\\.'" ):
        _safe_path("../../etc/passwd")


def test_safe_path_rejects_dotdot_in_middle():
    """_safe_path must reject '..' even when embedded mid-path."""
    from graph_gen import _safe_path

    with pytest.raises(ValueError):
        _safe_path("valid/../../escape")


def test_safe_path_accepts_normal_path(tmp_path):
    """_safe_path must resolve a clean path without raising."""
    from graph_gen import _safe_path
    from pathlib import Path

    result = _safe_path(str(tmp_path / "sub" / "dir"))
    assert isinstance(result, Path)

def test_skips_venv_pycache(tmp_path):
    """build_graph skips .venv and __pycache__ directories."""
    write_fixtures(tmp_path)
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "skip_me.py").write_text("def should_not_appear(): pass", encoding="utf-8")
    cache_dir = tmp_path / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "also_skip.py").write_text("def also_not(): pass", encoding="utf-8")

    from graph_gen import build_graph

    g = build_graph(tmp_path)
    paths = {n["path"] for n in g["nodes"]}
    assert not any(".venv" in p for p in paths), f".venv paths leaked into graph: {paths}"
    assert not any("__pycache__" in p for p in paths), f"__pycache__ paths leaked into graph: {paths}"


def test_cli_produces_valid_json(tmp_path):
    """CLI --root --out writes valid kata.graph.json."""
    write_fixtures(tmp_path)
    out = tmp_path / "out.json"
    result = subprocess.run(
        [sys.executable, "-m", "graph_gen", "--root", str(tmp_path), "--out", str(out)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),  # tools/ dir
    )
    assert result.returncode == 0, f"CLI failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    assert out.exists(), "CLI did not create output file"
    g = json.loads(out.read_text(encoding="utf-8"))
    errors = validate_graph(g)
    assert not errors, "CLI output schema violations:\n" + "\n".join(errors)


def test_no_call_edges(tmp_path):
    """call edges are oracle-only and must NOT appear in tree-sitter floor output."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    call_edges = [e for e in g["edges"] if e["kind"] == "call"]
    assert not call_edges, f"unexpected call edges (oracle-only): {call_edges}"


def test_pagerank_nonzero(tmp_path):
    """PageRank values are non-negative floats; at least one node has rank > 0."""
    write_fixtures(tmp_path)
    from graph_gen import build_graph

    g = build_graph(tmp_path)
    ranks = [n["rank"] for n in g["nodes"]]
    assert all(isinstance(r, float) for r in ranks), "not all ranks are float"
    assert any(r > 0 for r in ranks), "all ranks are 0 — PageRank not computed"
