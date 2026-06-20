"""graph_gen.py — tree-sitter floor generator for kata.graph.json.

Produces a structural graph of a Python codebase per protocol/graph.md.
Symbol types: function, class, method.
Edges: def (file→symbol), import (file→file, best-effort), ref (symbol→symbol, best-effort).
call edges are oracle-only — NOT emitted here.

Public API
----------
build_graph(root, files=None, prev=None) -> dict
    Walk root for *.py files, parse with tree-sitter, return kata.graph.json dict.

CLI
---
python -m graph_gen --root <path> --out <path>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tree_sitter_python as tsp
from tree_sitter import Language, Parser

# ---------------------------------------------------------------------------
# tree-sitter setup
# ---------------------------------------------------------------------------

_PY_LANG = Language(tsp.language())
_PARSER = Parser(_PY_LANG)

# ---------------------------------------------------------------------------
# Directories to skip during file discovery
# ---------------------------------------------------------------------------

_SKIP_DIRS = {".venv", "__pycache__", ".git", "node_modules"}


def _is_under_skip_dir(path: Path, root: Path) -> bool:
    """Return True if any path component is in _SKIP_DIRS or starts with '_kata_'."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    for part in rel.parts[:-1]:  # check directory parts, not filename
        if part in _SKIP_DIRS or part.startswith("_kata_"):
            return True
    return False


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def _file_hash(path: Path) -> str:
    """SHA-1 hex digest of file contents."""
    return hashlib.sha1(path.read_bytes()).hexdigest()


def _bytes_hash(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _repo_hash(file_hashes: dict[str, str]) -> str:
    """Stable hash of all file hashes (sorted by path)."""
    combined = "|".join(f"{k}:{v}" for k, v in sorted(file_hashes.items()))
    return hashlib.sha1(combined.encode()).hexdigest()


# ---------------------------------------------------------------------------
# tree-sitter AST helpers
# ---------------------------------------------------------------------------

def _node_text(node: Any) -> str:
    """Decode tree-sitter node text bytes to str."""
    return node.text.decode("utf-8", errors="replace")


def _name_of(node: Any) -> str | None:
    """Extract the name identifier from a function/class definition node."""
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return _node_text(name_node)
    return None


def _span_of(node: Any) -> list[int]:
    """Return [startLine, endLine] 1-indexed inclusive from a tree-sitter node."""
    start_row, _ = node.start_point
    end_row, _ = node.end_point
    return [start_row + 1, end_row + 1]


def _is_inside_class(node: Any) -> bool:
    """Return True if this node is directly inside a class_definition body."""
    parent = node.parent
    # Walk up: function_definition -> block -> class_definition
    # tree-sitter: class_definition > block > function_definition
    if parent is None:
        return False
    if parent.type == "block":
        grandparent = parent.parent
        if grandparent is not None and grandparent.type == "class_definition":
            return True
    return False


def _extract_symbols(source_bytes: bytes, rel_path: str) -> list[dict]:
    """Parse source with tree-sitter and return a list of raw symbol dicts.

    Symbol dict keys: name, symKind, span, signature
    Does NOT assign id, hash, rank (caller does that).
    """
    tree = _PARSER.parse(source_bytes)
    symbols: list[dict] = []
    _walk_for_symbols(tree.root_node, rel_path, symbols)
    return symbols


def _walk_for_symbols(
    node: Any,
    rel_path: str,
    out: list[dict],
) -> None:
    """Recursively walk tree-sitter nodes collecting function/class definitions."""
    if node.type in ("function_definition", "async_function_definition"):
        name = _name_of(node)
        if name:
            sym_kind = "method" if _is_inside_class(node) else "function"
            span = _span_of(node)
            sig = _signature_of(node)
            out.append({"name": name, "symKind": sym_kind, "span": span, "signature": sig})
        # Still recurse: nested classes/functions inside function bodies
        for child in node.children:
            _walk_for_symbols(child, rel_path, out)
        return  # don't double-append by falling through

    if node.type == "class_definition":
        name = _name_of(node)
        if name:
            span = _span_of(node)
            out.append({"name": name, "symKind": "class", "span": span, "signature": None})
        # Recurse into class body to capture methods
        for child in node.children:
            _walk_for_symbols(child, rel_path, out)
        return

    for child in node.children:
        _walk_for_symbols(child, rel_path, out)


def _signature_of(func_node: Any) -> str | None:
    """Best-effort function signature (def line text)."""
    params = func_node.child_by_field_name("parameters")
    name = func_node.child_by_field_name("name")
    if name and params:
        return f"def {_node_text(name)}{_node_text(params)}"
    return None


def _assign_collision_ids(symbols: list[dict], rel_path: str) -> list[dict]:
    """Assign ids with def-order ordinal for same-name collisions.

    First occurrence: <path>::<name>
    Second occurrence: <path>::<name>~1
    Third: ~2, etc.
    """
    name_count: dict[str, int] = {}
    result = []
    for sym in symbols:
        name = sym["name"]
        count = name_count.get(name, 0)
        if count == 0:
            sym_id = f"{rel_path}::{name}"
        else:
            sym_id = f"{rel_path}::{name}~{count}"
        name_count[name] = count + 1
        result.append({**sym, "id": sym_id})
    return result


# ---------------------------------------------------------------------------
# Import resolution (best-effort)
# ---------------------------------------------------------------------------

def _extract_imports(source_bytes: bytes, rel_path: str, all_rel_paths: set[str]) -> list[tuple[str, str]]:
    """Return list of (src_rel_path, dst_rel_path) file→file import edges.

    Handles:
      import foo
      import foo.bar
      from foo import bar
      from foo.bar import baz
    Resolves module name → repo-relative path if the corresponding .py file exists.
    """
    tree = _PARSER.parse(source_bytes)
    edges = []
    src_dir = str(Path(rel_path).parent)

    def _collect_imports(node: Any) -> None:
        if node.type == "import_statement":
            # import foo, import foo.bar
            for child in node.children:
                if child.type in ("dotted_name", "aliased_import"):
                    mod_text = _node_text(child.children[0] if child.type == "aliased_import" else child)
                    dst = _resolve_module(mod_text, src_dir, all_rel_paths)
                    if dst:
                        edges.append((rel_path, dst))
        elif node.type == "import_from_statement":
            # from foo import bar
            mod_node = node.child_by_field_name("module_name")
            if mod_node:
                mod_text = _node_text(mod_node)
                dst = _resolve_module(mod_text, src_dir, all_rel_paths)
                if dst:
                    edges.append((rel_path, dst))
        for child in node.children:
            _collect_imports(child)

    _collect_imports(tree.root_node)
    return edges


def _module_to_path(module_name: str, src_dir: str) -> list[str]:
    """Convert dotted module name to candidate repo-relative .py paths."""
    parts = module_name.split(".")
    # Relative: try src_dir / module.py and src_dir / module/__init__.py
    if src_dir and src_dir != ".":
        rel_candidates = [
            (src_dir + "/" + "/".join(parts) + ".py").lstrip("/"),
            (src_dir + "/" + "/".join(parts) + "/__init__.py").lstrip("/"),
        ]
    else:
        rel_candidates = []
    # Absolute from repo root
    abs_candidates = [
        "/".join(parts) + ".py",
        "/".join(parts) + "/__init__.py",
    ]
    return rel_candidates + abs_candidates


def _resolve_module(module_name: str, src_dir: str, all_rel_paths: set[str]) -> str | None:
    """Try to find a matching repo-relative path for a module name."""
    for candidate in _module_to_path(module_name, src_dir):
        if candidate in all_rel_paths:
            return candidate
    return None


# ---------------------------------------------------------------------------
# Ref edges (best-effort: call-sites resolved to known symbol ids)
# ---------------------------------------------------------------------------

def _extract_refs(
    source_bytes: bytes,
    rel_path: str,
    symbol_id_by_name: dict[str, list[str]],
    file_symbol_ids: set[str],
) -> list[tuple[str, str]]:
    """Return (src_symbol_id, dst_symbol_id) ref edges for calls from this file's symbols.

    Best-effort: if a call target name matches a known symbol AND the caller is a
    known symbol in this file, emit a ref edge.
    """
    tree = _PARSER.parse(source_bytes)
    # Map span start line → symbol id for this file
    edges: list[tuple[str, str]] = []

    # Find all call expressions in the file
    calls: list[str] = []

    def _collect_calls(node: Any) -> None:
        if node.type == "call":
            func_node = node.child_by_field_name("function")
            if func_node is not None:
                if func_node.type == "identifier":
                    calls.append(_node_text(func_node))
                elif func_node.type == "attribute":
                    # method call: obj.method(...)
                    attr = func_node.child_by_field_name("attribute")
                    if attr:
                        calls.append(_node_text(attr))
        for child in node.children:
            _collect_calls(child)

    _collect_calls(tree.root_node)

    # For each call name, find matching symbol ids in other files (not this file's own symbols)
    for call_name in calls:
        candidates = symbol_id_by_name.get(call_name, [])
        for candidate_id in candidates:
            if candidate_id not in file_symbol_ids:
                # Pick any symbol in this file as the source (best-effort: use the first)
                if file_symbol_ids:
                    src_id = next(iter(sorted(file_symbol_ids)))
                    edges.append((src_id, candidate_id))
                    break  # one edge per call name per file is enough for best-effort

    return edges


# ---------------------------------------------------------------------------
# PageRank (pure-python power iteration)
# ---------------------------------------------------------------------------

def _pagerank(node_ids: list[str], edges: list[dict], damping: float = 0.85, iterations: int = 20) -> dict[str, float]:
    """Compute uniform PageRank via power iteration.

    Returns dict {node_id: rank_float}.
    """
    n = len(node_ids)
    if n == 0:
        return {}

    idx = {nid: i for i, nid in enumerate(node_ids)}
    rank = [1.0 / n] * n

    # Build adjacency: out_edges[i] = list of j
    out_edges: list[list[int]] = [[] for _ in range(n)]
    in_edges: list[list[int]] = [[] for _ in range(n)]

    for edge in edges:
        src = edge["src"]
        dst = edge["dst"]
        si = idx.get(src)
        di = idx.get(dst)
        if si is not None and di is not None:
            out_edges[si].append(di)
            in_edges[di].append(si)

    out_degree = [len(out_edges[i]) for i in range(n)]

    for _ in range(iterations):
        new_rank = [(1.0 - damping) / n] * n
        for i in range(n):
            for j in in_edges[i]:
                if out_degree[j] > 0:
                    new_rank[i] += damping * rank[j] / out_degree[j]
                else:
                    # dangling node: distribute equally
                    new_rank[i] += damping * rank[j] / n
        rank = new_rank

    return {node_ids[i]: float(rank[i]) for i in range(n)}


# ---------------------------------------------------------------------------
# Core build_graph
# ---------------------------------------------------------------------------

def build_graph(
    root: str | Path,
    files: list[str | Path] | None = None,
    prev: dict | None = None,
) -> dict:
    """Build (or incrementally update) kata.graph.json.

    Parameters
    ----------
    root:  Repo root directory.
    files: Optional explicit list of .py file paths to include (still filtered by skip dirs).
    prev:  Previously-built graph dict. If provided, reuse nodes/edges for files whose
           content hash is unchanged; re-parse only changed files.

    Returns
    -------
    dict matching protocol/graph.md schema.
    """
    root = Path(root).resolve()

    # 1. Discover files
    if files is not None:
        py_files = [Path(f) for f in files]
    else:
        py_files = [
            p for p in root.rglob("*.py")
            if not _is_under_skip_dir(p, root)
        ]

    def _rel(p: Path) -> str:
        try:
            return p.relative_to(root).as_posix()
        except ValueError:
            return p.as_posix()

    # 2. Build file hash map
    file_hash_map: dict[str, str] = {}
    file_bytes_map: dict[str, bytes] = {}
    for p in py_files:
        try:
            data = p.read_bytes()
        except OSError:
            continue
        rel = _rel(p)
        file_hash_map[rel] = _bytes_hash(data)
        file_bytes_map[rel] = data

    all_rel_paths = set(file_hash_map.keys())

    # 3. Build prev lookup by file path
    prev_file_nodes: dict[str, dict] = {}
    prev_symbol_nodes: dict[str, dict] = {}
    prev_edges_by_file: dict[str, list[dict]] = {}  # file path → edges involving it

    if prev is not None:
        for n in prev.get("nodes", []):
            if n.get("kind") == "file":
                prev_file_nodes[n["path"]] = n
            elif n.get("kind") == "symbol":
                prev_symbol_nodes[n["id"]] = n

        for e in prev.get("edges", []):
            # Group edges by src (which is a file or symbol id)
            src = e.get("src", "")
            # We'll group by the file path extracted from src
            file_path = src.split("::")[0] if "::" in src else src
            prev_edges_by_file.setdefault(file_path, []).append(e)

    # 4. Parse files; reuse from prev when hash unchanged
    all_nodes: list[dict] = []
    all_edges: list[dict] = []

    # Track which files are reused vs re-parsed
    reused_file_paths: set[str] = set()
    new_file_paths: set[str] = set()

    for rel_path, data in file_bytes_map.items():
        current_hash = file_hash_map[rel_path]
        prev_node = prev_file_nodes.get(rel_path)

        if prev_node is not None and prev_node.get("hash") == current_hash:
            # Reuse this file's nodes and edges
            reused_file_paths.add(rel_path)
        else:
            new_file_paths.add(rel_path)

    # Collect reused nodes/edges from prev for unchanged files
    if prev is not None:
        reused_symbol_ids: set[str] = set()
        for n in prev.get("nodes", []):
            kind = n.get("kind")
            if kind == "file" and n["path"] in reused_file_paths:
                all_nodes.append(n)
            elif kind == "symbol" and n.get("path") in reused_file_paths:
                all_nodes.append(n)
                reused_symbol_ids.add(n["id"])

        for e in prev.get("edges", []):
            src = e.get("src", "")
            dst = e.get("dst", "")
            # Edge belongs to reused file if its src file path is reused
            src_file = src.split("::")[0] if "::" not in src or e.get("kind") == "def" else src.split("::")[0]
            # Import edges: src is a file id (== path for file nodes)
            edge_kind = e.get("kind")
            if edge_kind == "import":
                # Both endpoints must be reused files (or at least src)
                if src in reused_file_paths and dst in reused_file_paths:
                    all_edges.append(e)
            elif edge_kind == "def":
                # src is file id, dst is symbol id
                if src in reused_file_paths:
                    all_edges.append(e)
            elif edge_kind in ("ref",):
                # src and dst are symbol ids
                src_file_path = src.split("::")[0] if "::" in src else src
                if src_file_path in reused_file_paths:
                    all_edges.append(e)

    # 5. Parse new/changed files
    # We need all symbol names across all files for ref resolution
    # First pass: collect symbols for new files
    new_file_symbols: dict[str, list[dict]] = {}  # rel_path → symbol dicts with ids

    for rel_path in new_file_paths:
        data = file_bytes_map[rel_path]
        raw_syms = _extract_symbols(data, rel_path)
        syms_with_ids = _assign_collision_ids(raw_syms, rel_path)
        new_file_symbols[rel_path] = syms_with_ids

    # 6. Build nodes for new files
    for rel_path in new_file_paths:
        data = file_bytes_map[rel_path]
        h = file_hash_map[rel_path]

        file_node: dict = {
            "id": rel_path,
            "kind": "file",
            "path": rel_path,
            "hash": h,
            "rank": 0.0,  # will be updated by PageRank
            "lang": "python",
        }
        all_nodes.append(file_node)

        syms_with_ids = new_file_symbols.get(rel_path, [])
        for sym in syms_with_ids:
            sym_data = data[:]  # we have the full file bytes
            sym_node: dict = {
                "id": sym["id"],
                "kind": "symbol",
                "path": rel_path,
                "name": sym["name"],
                "symKind": sym["symKind"],
                "span": sym["span"],
                "hash": h,  # use file hash for symbol (node-level hash)
                "rank": 0.0,  # updated by PageRank
            }
            if sym.get("signature"):
                sym_node["signature"] = sym["signature"]
            all_nodes.append(sym_node)

            # def edge: file → symbol
            all_edges.append({
                "src": rel_path,
                "dst": sym["id"],
                "kind": "def",
                "weight": 1.0,
            })

    # 7. Build import edges for new files
    # (import edges involving changed files; reused import edges already added above)
    for rel_path in new_file_paths:
        data = file_bytes_map[rel_path]
        import_pairs = _extract_imports(data, rel_path, all_rel_paths)
        for src_path, dst_path in import_pairs:
            all_edges.append({
                "src": src_path,
                "dst": dst_path,
                "kind": "import",
                "weight": 1.0,
            })

    # 8. Ref edges (best-effort) for new files
    # Build global symbol_id_by_name map from all nodes
    symbol_id_by_name: dict[str, list[str]] = {}
    for n in all_nodes:
        if n["kind"] == "symbol":
            symbol_id_by_name.setdefault(n["name"], []).append(n["id"])

    for rel_path in new_file_paths:
        data = file_bytes_map[rel_path]
        file_symbol_ids = {
            n["id"] for n in all_nodes
            if n["kind"] == "symbol" and n.get("path") == rel_path
        }
        ref_pairs = _extract_refs(data, rel_path, symbol_id_by_name, file_symbol_ids)
        for src_id, dst_id in ref_pairs:
            all_edges.append({
                "src": src_id,
                "dst": dst_id,
                "kind": "ref",
                "weight": 1.0,
            })

    # 9. Deduplicate edges
    seen_edges: set[tuple] = set()
    deduped_edges: list[dict] = []
    for e in all_edges:
        key = (e["src"], e["dst"], e["kind"])
        if key not in seen_edges:
            seen_edges.add(key)
            deduped_edges.append(e)
    all_edges = deduped_edges

    # 10. PageRank
    node_ids = [n["id"] for n in all_nodes]
    ranks = _pagerank(node_ids, all_edges)
    for n in all_nodes:
        n["rank"] = ranks.get(n["id"], 0.0)

    # 11. meta
    meta = {
        "backend": "tree-sitter",
        "repoHash": _repo_hash(file_hash_map),
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(),
    }

    return {
        "nodes": all_nodes,
        "edges": all_edges,
        "meta": meta,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate kata.graph.json from a Python codebase using tree-sitter."
    )
    parser.add_argument("--root", required=True, help="Repo root directory to scan.")
    parser.add_argument("--out", required=True, help="Output path for kata.graph.json.")
    parser.add_argument(
        "--prev",
        default=None,
        help="Path to an existing kata.graph.json for incremental build.",
    )
    args = parser.parse_args(argv)

    prev = None
    if args.prev:
        try:
            prev = json.loads(Path(args.prev).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Warning: could not load prev graph from {args.prev!r}: {exc}", file=sys.stderr)

    graph = build_graph(args.root, prev=prev)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    n_nodes = len(graph["nodes"])
    n_edges = len(graph["edges"])
    print(f"kata.graph.json written to {out_path} ({n_nodes} nodes, {n_edges} edges)")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
