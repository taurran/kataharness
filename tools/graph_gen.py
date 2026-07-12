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
from datetime import UTC, datetime
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
    """SHA-256 hex digest of file contents (content-addressing for the cache)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bytes_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _repo_hash(file_hashes: dict[str, str]) -> str:
    """Stable hash of all file hashes (sorted by path)."""
    combined = "|".join(f"{k}:{v}" for k, v in sorted(file_hashes.items()))
    return hashlib.sha256(combined.encode()).hexdigest()


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

def _extract_imports(
    source_bytes: bytes,
    rel_path: str,
    all_rel_paths: set[str],
    source_roots: list[str] | None = None,
) -> list[tuple[str, str]]:
    """Return list of (src_rel_path, dst_rel_path) file→file import edges.

    Handles:
      import foo
      import foo.bar
      from foo import bar
      from foo.bar import baz
      from .foo import bar / from ..pkg import baz   (relative — adval P0-F1)
      from foo import mod / from . import mod        (submodule file targets)
    Resolves module name → repo-relative path if the corresponding .py file exists.
    ``source_roots`` (F2 src-layout) is discovered once from ``all_rel_paths``
    when not supplied — build_graph passes a precomputed set to avoid rework.
    """
    if source_roots is None:
        source_roots = _discover_source_roots(all_rel_paths)
    tree = _PARSER.parse(source_bytes)
    edges = []
    src_dir = str(Path(rel_path).parent)

    def _collect_imports(node: Any) -> None:
        if node.type == "import_statement":
            # import foo, import foo.bar
            for child in node.children:
                if child.type in ("dotted_name", "aliased_import"):
                    mod_text = _node_text(child.children[0] if child.type == "aliased_import" else child)
                    dst = _resolve_module(mod_text, src_dir, all_rel_paths, source_roots)
                    if dst:
                        edges.append((rel_path, dst))
        elif node.type == "import_from_statement":
            # from foo import bar
            mod_node = node.child_by_field_name("module_name")
            if mod_node:
                mod_text = _node_text(mod_node)
                dst = _resolve_module(mod_text, src_dir, all_rel_paths, source_roots)
                if dst:
                    edges.append((rel_path, dst))
                # Submodule imports: `from pkg import mod` / `from . import mod`
                # bind a MODULE, not a symbol — when `<module>.<name>` resolves to
                # a real file, that file is the true edge target (adval P0-F1: the
                # package __init__.py alone under-reports the dependency).
                if dst is None or dst.endswith("/__init__.py") or dst == "__init__.py":
                    for name_node in node.children_by_field_name("name"):
                        base = (
                            name_node.children[0]
                            if name_node.type == "aliased_import"
                            else name_node
                        )
                        # pure-dot module ("." / "..") already ends in its joiner
                        joiner = "" if mod_text.endswith(".") else "."
                        sub = f"{mod_text}{joiner}{_node_text(base)}"
                        sub_dst = _resolve_module(sub, src_dir, all_rel_paths, source_roots)
                        if sub_dst:
                            edges.append((rel_path, sub_dst))
        for child in node.children:
            _collect_imports(child)

    _collect_imports(tree.root_node)
    return edges


# Conventional non-source top-level dirs: a package inside these is not on
# sys.path in any standard layout, so promoting them to source roots would
# manufacture import edges that cannot resolve at runtime (adval F2 finding 2).
_NON_SOURCE_ROOTS = {"tests", "test", "docs", "doc", "examples", "example"}


def _discover_source_roots(all_rel_paths: set[str]) -> list[str]:
    """Discover non-root source roots for src-layout import resolution (F2).

    A *source root* is the parent directory of a TOP-LEVEL package — a dir
    holding an ``__init__.py`` whose own parent is NOT itself a package. On a
    src-layout project (``src/pkg/__init__.py``) this yields ``["src"]``; on a
    flat layout it yields ``[]`` (repo-root packages are already covered by the
    absolute candidates, so they are deliberately excluded here). This is what
    lets ``from pkg.mod import x`` resolve to ``src/pkg/mod.py``.

    Two refinements (L3 + adval):
    - Conventional non-source dirs (``tests/``, ``docs/``, …) are never promoted
      to roots — a package under them is not on sys.path, so a root there would
      manufacture false import edges.
    - Fallback (L3 verbatim): when no ``__init__.py``-derived root exists but a
      literal ``src/`` directory does (PEP-420 namespace src-layout), ``src`` is
      the root — candidates only ever match existing files, so this cannot
      create a false edge on a repo without ``src/``.
    """
    package_dirs = {
        Path(p).parent.as_posix()
        for p in all_rel_paths
        if Path(p).name == "__init__.py"
    }
    roots: set[str] = set()
    for pkg in package_dirs:
        parent = Path(pkg).parent.as_posix()
        # top-level package ⇒ its parent dir is not itself a package
        if (
            parent not in package_dirs
            and parent not in ("", ".")
            and Path(parent).parts[0] not in _NON_SOURCE_ROOTS
        ):
            roots.add(parent)
    if not roots and any(p.startswith("src/") for p in all_rel_paths):
        return ["src"]
    return sorted(roots)


def _module_to_path(
    module_name: str, src_dir: str, source_roots: list[str] | tuple[str, ...] = ()
) -> list[str]:
    """Convert dotted module name to candidate repo-relative .py paths.

    Candidate order (first-match-wins in ``_resolve_module``): import-relative,
    then repo-root-absolute, then source-root-prefixed (F2). Appending the
    src-layout candidates LAST preserves flat-layout resolution byte-for-byte.
    """
    # Explicit relative import (from .mod / from ..pkg.mod): leading dots walk up
    # from the importing file's dir. Handled first and exclusively — the previous
    # naive split produced interior-slash candidates ("pkg//mod.py") that never
    # matched, silently dropping every relative-import edge (adval P0-F1).
    if module_name.startswith("."):
        n_dots = len(module_name) - len(module_name.lstrip("."))
        rest = module_name.lstrip(".")
        base = src_dir if src_dir not in ("", ".") else ""
        for _ in range(n_dots - 1):
            base = Path(base).parent.as_posix() if base else ""
            if base == ".":
                base = ""
        prefix = (base + "/") if base else ""
        if rest:
            rest_path = "/".join(rest.split("."))
            return [prefix + rest_path + ".py", prefix + rest_path + "/__init__.py"]
        # bare `from . import name` — resolve to the package itself (its
        # __init__.py); the sibling-module half is resolved by the caller
        # (_extract_imports submodule candidates).
        return [prefix + "__init__.py"] if prefix else ["__init__.py"]

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
    # Source-root-prefixed (src-layout): appended last so flat layout is unchanged
    src_candidates: list[str] = []
    for root in source_roots:
        src_candidates.append(root + "/" + "/".join(parts) + ".py")
        src_candidates.append(root + "/" + "/".join(parts) + "/__init__.py")
    return rel_candidates + abs_candidates + src_candidates


def _resolve_module(
    module_name: str,
    src_dir: str,
    all_rel_paths: set[str],
    source_roots: list[str] | None = None,
) -> str | None:
    """Try to find a matching repo-relative path for a module name.

    ``source_roots`` is discovered lazily from ``all_rel_paths`` when not
    supplied, so direct callers get src-layout resolution without threading it.
    """
    if source_roots is None:
        source_roots = _discover_source_roots(all_rel_paths)
    for candidate in _module_to_path(module_name, src_dir, source_roots):
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
    generated_at: str | None = None,
) -> dict:
    """Build (or incrementally update) kata.graph.json.

    Parameters
    ----------
    root:  Repo root directory.
    files: Optional explicit list of .py file paths to include (still filtered by skip dirs).
    prev:  Previously-built graph dict. If provided, reuse nodes/edges for files whose
           content hash is unchanged; re-parse only changed files.
    generated_at: Optional ISO-8601 UTC stamp for ``meta.generatedAt`` (DET-14).
           Injectable clock (DETERMINISM-DOCTRINE law 7): a raw ``datetime.now()`` in
           the durable artifact makes an otherwise-unchanged graph diff-noisy on every
           regeneration. Nothing hashes this field — ``meta.repoHash`` is computed over
           ``file_hash_map`` only, EXCLUDING ``meta`` — so the stamp is a documented
           hint-only field, but pinning it lets callers/tests produce byte-stable
           artifacts. Defaults to ``datetime.now(tz=timezone.utc).isoformat()`` when None.

    Returns
    -------
    dict matching protocol/graph.md schema.
    """
    root = Path(root).resolve()

    # 1. Discover files — sorted: discovery order must never leak into the artifact
    # (rglob order is filesystem-dependent; DETERMINISM-DOCTRINE law 2, DET-01).
    if files is not None:
        py_files = sorted(Path(f) for f in files)
    else:
        py_files = sorted(
            p for p in root.rglob("*.py")
            if not _is_under_skip_dir(p, root)
        )

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

    # Iterate sets in sorted order everywhere below — set iteration is
    # PYTHONHASHSEED-dependent and must not drive node/edge order (DET-01).
    for rel_path in sorted(new_file_paths):
        data = file_bytes_map[rel_path]
        raw_syms = _extract_symbols(data, rel_path)
        syms_with_ids = _assign_collision_ids(raw_syms, rel_path)
        new_file_symbols[rel_path] = syms_with_ids

    # 6. Build nodes for new files
    for rel_path in sorted(new_file_paths):
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
    source_roots = _discover_source_roots(all_rel_paths)  # F2: src-layout, computed once
    for rel_path in sorted(new_file_paths):
        data = file_bytes_map[rel_path]
        import_pairs = _extract_imports(data, rel_path, all_rel_paths, source_roots)
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
    # Sort candidate lists: _extract_refs picks the FIRST out-of-file candidate, so
    # candidate order decides the ref-edge TARGET — node insertion order must not
    # pick graph topology (DET-01; DETERMINISM-DOCTRINE law 3).
    for _ids in symbol_id_by_name.values():
        _ids.sort()

    for rel_path in sorted(new_file_paths):
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
        # DET-14: injectable clock (DETERMINISM-DOCTRINE law 7). Nothing hashes
        # generatedAt (repoHash excludes meta), but pinning it keeps the durable
        # artifact byte-stable on regeneration of an unchanged tree.
        "generatedAt": generated_at
        if generated_at is not None
        else datetime.now(tz=UTC).isoformat(),
    }

    return {
        "nodes": all_nodes,
        "edges": all_edges,
        "meta": meta,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _safe_path(raw: str) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied CLI path, then resolve.

    Blocks any ``..`` segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree, while still allowing the
    absolute and nested-relative paths the maintainer legitimately targets.
    Sanitizes the tainted CLI input at the boundary before any filesystem sink.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"graph_gen: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


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

    root_path = _safe_path(args.root)
    out_path = _safe_path(args.out)

    prev = None
    if args.prev:
        prev_path = _safe_path(args.prev)
        try:
            prev = json.loads(prev_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Warning: could not load prev graph from {args.prev!r}: {exc}", file=sys.stderr)

    graph = build_graph(root_path, prev=prev)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    n_nodes = len(graph["nodes"])
    n_edges = len(graph["edges"])
    print(f"kata.graph.json written to {out_path} ({n_nodes} nodes, {n_edges} edges)")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
