"""contract_edges.py — Freeze/Float M1 engine (pure, fail-closed; NO wiring).

Contract edges (`builds_against`) let a contract-only dependent dispatch at freeze
instead of waiting for its provider task. This module is the deterministic engine
behind that scheduling float and its safety companions. It is PURE — nothing in the
harness calls it yet (M1-P0); wiring lands in M1-P1/P2. See
`.planning/specs/freeze-float-m1/DESIGN.md`.

Edge grammar (M1-L1):
    builds_against: { "<task>": [ "<contractId>@<surfaceHash>" ] }

Fail-closed discipline (M1-L9 / F7): every function that consumes `builds_against`
RAISES ``ValueError`` on a malformed structure rather than returning a silent
empty/permissive result. Only a *well-formed* empty map is vacuous. This mirrors
``kata_restore.parse_plan_tasks``'s raise-on-malformed template — an invalidation
set driving abort/re-open must never silently under-invalidate.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import tree_sitter_python as tsp
from tree_sitter import Language, Parser

_PY_LANG = Language(tsp.language())
_PARSER = Parser(_PY_LANG)

_FUNC_TYPES = ("function_definition", "async_function_definition")

# <contractId>@<surfaceHash> — id is a path-safe slug; hash is lowercase hex (8–64).
# \Z (not $) so a trailing newline is rejected, not silently accepted (M1-L9).
_EDGE_RE = re.compile(r"^(?P<id>[A-Za-z0-9._-]+)@(?P<hash>[0-9a-f]{8,64})\Z")


def _parse_edge(entry: object) -> tuple[str, str]:
    """Validate + split one ``"<contractId>@<hash>"`` entry. RAISE if malformed."""
    if not isinstance(entry, str):
        raise ValueError(f"builds_against edge entry must be a string, got {type(entry).__name__}")
    m = _EDGE_RE.match(entry)
    if m is None:
        raise ValueError(
            f"malformed builds_against edge {entry!r} — expected '<contractId>@<surfaceHash>' "
            f"(hash = 8-64 lowercase hex)"
        )
    return m.group("id"), m.group("hash")


def _validate_shape(builds_against: object) -> dict:
    """Validate ONLY the top-level shape ``{ task_str: [list] }``. RAISE if malformed.

    Entry-grammar validation lives in ``_parse_edge`` (the single place entries are
    split), so it is not duplicated here. An empty ``{}`` is well-formed (vacuous, BC).
    """
    if not isinstance(builds_against, dict):
        raise ValueError(
            f"builds_against must be a dict of task -> [edges], got {type(builds_against).__name__}"
        )
    for task, edges in builds_against.items():
        if not isinstance(task, str):
            raise ValueError(f"builds_against task key must be a string, got {type(task).__name__}")
        if not isinstance(edges, list):
            raise ValueError(
                f"builds_against[{task!r}] must be a list of edges, got {type(edges).__name__}"
            )
    return builds_against


def invert(builds_against: object) -> dict[str, list[str]]:
    """Invert ``{task: [contractId@hash]}`` to ``{contractId: [task, ...]}``.

    Tasks per contract are sorted + deduped. RAISES ``ValueError`` on any malformed
    structure — bad top-level shape (via ``_validate_shape``) or any malformed entry
    (via ``_parse_edge``) (M1-L9); a well-formed empty map returns ``{}``.
    """
    _validate_shape(builds_against)
    out: dict[str, set[str]] = {}
    for task, edges in builds_against.items():
        for entry in edges:
            contract_id, _hash = _parse_edge(entry)  # raises on malformed grammar
            out.setdefault(contract_id, set()).add(task)
    return {cid: sorted(tasks) for cid, tasks in out.items()}


def invalidation_set(builds_against: object, changed_contract_id: str) -> list[str]:
    """Return the sorted tasks bound to ``changed_contract_id``.

    The set a contract supersede must abort/re-open (M1-L3). RAISES on malformed
    ``builds_against`` (never a silent empty set); an unknown contract id or a
    contract with no dependents returns ``[]``.
    """
    if not isinstance(changed_contract_id, str) or not changed_contract_id:
        raise ValueError("changed_contract_id must be a non-empty string")
    inverted = invert(builds_against)
    return inverted.get(changed_contract_id, [])


# ---------------------------------------------------------------------------
# Slice B — surface_hash (narrowed interface-surface extractor, fail-closed)
# ---------------------------------------------------------------------------
#
# M1-L1 (F4-narrowed): the pinned surface is function/method SIGNATURES including
# return annotations + decorator lists + class headers — the robustly extractable
# set. A body-fill must NOT change the hash (M1-L8: bodies are excluded); an
# interface edit (param / return annotation / decorator / class header) MUST.
#
# DEFERRED residual (NOT machine-pinned, review-backstopped): module constants,
# type aliases, __all__, re-exports. A contract relying on a pinned constant is
# flagged to the kata-review edge-honesty backstop until a later milestone lands
# the export visitor. Documented in DESIGN M1-L1 — do not silently claim coverage.


def _text(node, src: bytes) -> str:
    return src[node.start_byte : node.end_byte].decode("utf-8", "replace")


def _decorators_of(defn, src: bytes) -> list[str]:
    """Decorator texts if *defn* is wrapped in a decorated_definition, else []."""
    parent = defn.parent
    if parent is not None and parent.type == "decorated_definition":
        return [_text(c, src) for c in parent.children if c.type == "decorator"]
    return []


_PUNCT_RE = re.compile(r"\s*(->|[(),:\[\]{}=|/*])\s*")


def _strip_comments(text: str) -> str:
    """Strip `#` line comments QUOTE-AWARELY: a `#` inside a string literal
    (including triple-quoted) is content, not a comment. The previous regex strip
    truncated everything after a `#` in a string default, masking every subsequent
    parameter edit in that signature — the exact edit class the pin exists to
    catch (adval P0-F3)."""
    out: list[str] = []
    i, n = 0, len(text)
    quote: str | None = None  # None, or the active quote token (' " ''' \"\"\")
    while i < n:
        c = text[i]
        if quote is not None:
            if c == "\\" and len(quote) == 1:  # escapes only end 1-char quotes
                out.append(text[i : i + 2])
                i += 2
                continue
            if text.startswith(quote, i):
                out.append(quote)
                i += len(quote)
                quote = None
                continue
            out.append(c)
            i += 1
            continue
        if c in ("'", '"'):
            quote = text[i : i + 3] if text.startswith(c * 3, i) else c
            out.append(quote)
            i += len(quote)
            continue
        if c == "#":  # real comment — drop to end of line
            j = i
            while j < n and text[j] not in "\n\r":
                j += 1
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _canon(text: str) -> str:
    """Canonicalize a signature fragment so cosmetic reformatting does NOT flip the
    surface hash (M1-L8: a body-fill + autoformatter must be a no-op): strip line
    comments (quote-aware — a `#` in a string default is content, adval P0-F3),
    collapse whitespace, remove whitespace around structural punctuation, and drop
    a single magic trailing comma before the closing `)`/`]` (black's multiline
    explode, adval P0-F5). Applied symmetrically to both sides, so genuine token
    differences still differ. (Residual, documented: whitespace INSIDE a string
    default is also collapsed — `"a, b"` and `"a,b"` canonicalize identically; a
    genuine-difference micro-collision, review-backstopped.)"""
    t = _strip_comments(text)
    t = re.sub(r"\s+", " ", t).strip()
    t = _PUNCT_RE.sub(r"\1", t)
    # magic trailing comma at the very end of the fragment only — inner tuple
    # defaults like `x=(1,)` are untouched
    if t.endswith(",)"):
        t = t[:-2] + ")"
    elif t.endswith(",]"):
        t = t[:-2] + "]"
    return t


def _emit_surface(defn, class_stack: list[str], src: bytes) -> str:
    """Build the surface string for one function/class definition (bodies excluded)."""
    name_node = defn.child_by_field_name("name")
    name = _text(name_node, src) if name_node else "?"
    qual = ".".join(class_stack + [name])
    decs = [_canon(d) for d in _decorators_of(defn, src)]
    if defn.type in _FUNC_TYPES:
        # async may be a distinct node type OR an `async` child token, depending on
        # the tree-sitter-python grammar version — detect both.
        is_async = defn.type == "async_function_definition" or any(
            c.type == "async" for c in defn.children
        )
        kw = "async def" if is_async else "def"
        params = defn.child_by_field_name("parameters")
        ret = defn.child_by_field_name("return_type")
        sig = f"{kw} {qual}{_canon(_text(params, src)) if params else '()'}"
        if ret is not None:
            sig += f"->{_canon(_text(ret, src))}"
        line = sig
    else:  # class_definition
        supers = defn.child_by_field_name("superclasses")
        line = f"class {qual}{_canon(_text(supers, src)) if supers else ''}"
    return "\n".join(decs + [line])


def _walk_surface(node, class_stack: list[str], src: bytes, out: list[str]) -> None:
    """Collect surface strings. Never descends into a function body (impl, not surface)."""
    for child in node.children:
        if child.type in _FUNC_TYPES:
            out.append(_emit_surface(child, class_stack, src))
            # do NOT recurse — nested defs inside a body are implementation
        elif child.type == "class_definition":
            out.append(_emit_surface(child, class_stack, src))
            name_node = child.child_by_field_name("name")
            cname = _text(name_node, src) if name_node else "?"
            _walk_surface(child, class_stack + [cname], src, out)  # capture methods
        else:
            # structural containers (module, block, decorated_definition, if/try, …)
            _walk_surface(child, class_stack, src, out)


def _extract_surface(src: bytes) -> list[str]:
    """Extract the interface surface of one source file. RAISE on any parse ERROR
    node (M1-L9 — no partial hash could hide an interface change in a broken region)."""
    tree = _PARSER.parse(src)
    if tree.root_node.has_error:
        raise ValueError(
            "contract file has a parse error (ERROR node) — surface_hash fails closed (M1-L9)"
        )
    out: list[str] = []
    _walk_surface(tree.root_node, [], src, out)
    return out


def _netstring_hash(items: list[str]) -> str:
    """Order-independent sha256 over netstring length-prefixed items (D98 collision-safe)."""
    h = hashlib.sha256()
    for s in sorted(items):
        b = s.encode("utf-8")
        h.update(f"{len(b)}:".encode("ascii"))
        h.update(b)
    return h.hexdigest()


def surface_hash(contract_dir: str | Path) -> str:
    """Content-hash the INTERFACE SURFACE of a contract directory (M1-L1).

    Hashes function/method signatures (params + return annotations) + decorators +
    class headers across every ``.py`` under *contract_dir*, each attributed to its
    relative path (so moving a symbol between files changes the hash). Bodies are
    excluded, so filling a stub body does not flip the pin (M1-L8). RAISES on a
    missing directory, any unparseable contract file, or a directory containing
    NO ``.py`` file at all (adval P0-F4: an empty hash would be a vacuous pin —
    an absent input to a decision hash hard-fails per D136/M1-L9).

    Residual (documented, review-backstopped): only ``.py`` files contribute to
    the pin — a ``.pyi``/non-Python interface file is NOT machine-pinned (it is
    still sentinel-scanned by ``surviving_stubs``).
    """
    root = Path(contract_dir)
    if not root.is_dir():
        raise ValueError(f"contract dir not found: {contract_dir!r}")
    items: list[str] = []
    py_files = sorted(root.rglob("*.py"))
    if not py_files:
        raise ValueError(
            f"contract dir {contract_dir!r} contains no .py file — refusing a "
            f"vacuous surface pin (M1-L9/D136); a non-Python contract surface is "
            f"not machine-pinnable yet"
        )
    for py in py_files:
        src = py.read_bytes()
        rel = py.relative_to(root).as_posix()
        for surface in _extract_surface(src):  # raises on parse error
            items.append(f"{rel}::{surface}")
    return _netstring_hash(items)


# ---------------------------------------------------------------------------
# Slice C — surviving_stubs + edge_honesty (scans, fail-closed)
# ---------------------------------------------------------------------------

STUB_SENTINEL = "# KATA-CONTRACT-STUB"


def surviving_stubs(repo_root: str | Path, sentinel: str = STUB_SENTINEL) -> list[str]:
    """Return sorted repo-relative paths of `contracts/` files still bearing the
    stub sentinel (M1-L4). A surviving sentinel ⇒ the provider never retired the
    stub ⇒ the final gate must fail. Language-agnostic (a content grep); empty ⇒ clean.

    Honest scope: this is the sentinel (content) half of M1-L4. The *dangling-import*
    half (a dependent still importing a deleted contract) needs the full dependent
    file set + merged-tree resolution context and is wired at the P2 final gate — it
    is NOT silently covered here.

    Fail-closed (M1-L9): an unreadable `contracts/` file RAISES (`OSError`) — a file
    the gate cannot read cannot be certified sentinel-free, so it is never silently
    skipped (that would let a surviving stub pass). Mirrors ``surface_hash``.

    Scope: EVERY file under a `contracts/` dir is scanned, not just `.py` — the
    DESIGN's "zero `contracts/` files may still bear the sentinel" is extension-
    blind (adval P0-F2: a `.pyi`/`.ts`/`.md` stub must not survive invisibly).
    The byte-level check also matches UTF-16-encoded sentinels (adval P0-F8).
    Note: `contracts` is matched at ANY path depth; a vendored tree containing a
    `contracts/` dir will be scanned too (fail-closed direction — the P2 wiring
    anchors/excludes ignore-dirs).
    """
    root = Path(repo_root)
    needles = (
        sentinel.encode("utf-8"),
        sentinel.encode("utf-16-le"),
        sentinel.encode("utf-16-be"),
    )
    found: list[str] = []
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(root)
        if "contracts" not in rel.parts:
            continue
        data = f.read_bytes()  # raises → fail-closed
        if any(n in data for n in needles):
            found.append(rel.as_posix())
    return sorted(found)


def edge_honesty(
    dependent_files: list[str],
    provider_paths: list[str],
    repo_root: str | Path,
) -> list[dict]:
    """M1-L5: a `builds_against` dependent's (test) files may import ONLY the contract
    surface, never a PROVIDER-owned implementation path. Returns sorted violations
    ``[{"file": <dependent file>, "imported": <provider path>}]``; empty ⇒ honest.

    Reuses ``graph_gen._extract_imports``/``_resolve_module`` for resolution
    (static ``import``/``from`` forms, including relative and submodule imports). A
    violation means the edge should be `depends_on`, not `builds_against` (dispatching
    it early is unsound). Residuals (DESIGN M1-L5, documented — review-backstopped):
    import-surface honesty ≠ semantic honesty — a dependent importing only the
    contract can still lean on provider internals the contract under-specifies; and
    DYNAMIC imports (``importlib.import_module``/``__import__``) are a mechanical
    bypass this scan cannot see (adval P0-F9). ``provider_paths`` must be exact
    repo-relative FILE paths — a directory entry matches nothing (adval P0-F10);
    the P2 caller expands ``ownership:`` dirs to files before calling.

    Fail-closed (M1-L9): an unreadable/absent dependent file RAISES (`OSError`) — a
    file the gate cannot read cannot be certified honest, so it is never silently
    deemed a non-violation.
    """
    from graph_gen import _extract_imports  # reuse the sole import scanner

    root = Path(repo_root)
    all_rel = {p.relative_to(root).as_posix() for p in root.rglob("*.py")}
    forbidden = {p.replace("\\", "/") for p in provider_paths}
    violations: list[dict] = []
    for f in dependent_files:
        f_norm = f.replace("\\", "/")
        src = (root / f_norm).read_bytes()  # raises → fail-closed
        for _src_rel, dst_rel in _extract_imports(src, f_norm, all_rel):
            if dst_rel in forbidden:
                violations.append({"file": f_norm, "imported": dst_rel})
    return sorted(violations, key=lambda v: (v["file"], v["imported"]))
