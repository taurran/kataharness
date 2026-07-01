"""function_model.py — Function-model oracle for KataHarness debug mode (LD2/LD7).

Security note
-------------
FM assertions are authored by ``kata-comprehend`` (an LLM) — they are
**external-trust-domain input** per ``protocol/exec-safety.md``.
Evaluating them via ``eval``/``exec`` is **PROHIBITED**, including
``eval(expr, {"__builtins__": {}}, ns)`` (known-escapable sandbox).
All assertion evaluation goes through ``_safe_eval``: parse with
``ast.parse(expr, mode="eval")``, walk every node through a strict
whitelist, then recursively evaluate — no ``eval``/``exec`` at any point.
Registered in ``protocol/exec-safety.md`` (in-process evaluation section).

Public surfaces
---------------
function_model_schema() -> dict
validate_function_model(fm) -> list[str]
_safe_eval(expr, names) -> bool
evaluate_spec(fm, call) -> dict
emit_function_model(fm, path)
load_function_model(path) -> dict
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Allowed derivation sources (single source of truth)
# ---------------------------------------------------------------------------

_ALLOWED_SOURCES: frozenset[str] = frozenset({
    "graph",
    "docs",
    "types",
    "commit-history",
    "callers",
    "contract-inference",
})

# ---------------------------------------------------------------------------
# Safe-symbol table — the ONLY callables accessible inside assertions
# ---------------------------------------------------------------------------

_SAFE_SYMBOLS: dict[str, Any] = {
    # Numeric / collection utilities
    "len": len,
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    # Type checks — common in pre/postconditions; safe because the second arg
    # must also resolve from this table or the call namespace (no Attribute).
    "isinstance": isinstance,
    "type": type,
    # Primitive type constructors (used as second arg to isinstance, or conversion)
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    # Other safe builtins
    "round": round,
    "all": all,
    "any": any,
    # NOTE: `range` is deliberately EXCLUDED — it is the one symbol that lets a
    # (finite, valid) assertion build an unbounded iterable, enabling a
    # resource-exhaustion DoS via `sum(range(10**12))` etc. (D98 finding). Every
    # remaining symbol operates only over finite literals or bound-namespace
    # values (themselves authored finite data), so iteration is bounded.
}

# Hard cap on a `<<` shift amount — a huge shift builds a giant integer with no
# call (CPU/memory DoS). `**` is removed entirely (rejected at walk). (D98.)
_MAX_SHIFT = 1024
# Hard cap on AST node count per assertion — defense-in-depth against a
# pathologically large expression.
_MAX_ASSERTION_NODES = 256

# ---------------------------------------------------------------------------
# JSON Schema (single source of truth for the function_model artifact)
# ---------------------------------------------------------------------------


def function_model_schema() -> dict:
    """Return the JSON Schema for a function_model artifact.

    This is the single source of truth; validators, emitters, and downstream
    consumers reference this schema rather than duplicating field definitions.
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "function_model",
        "type": "object",
        "required": [
            "module",
            "intent_summary",
            "preconditions",
            "postconditions",
            "behavioral_examples",
            "derivation_sources",
            "confidence",
        ],
        "properties": {
            "module": {
                "type": "string",
                "description": "Repo-relative path or qualified symbol.",
            },
            "intent_summary": {
                "type": "string",
                "description": "Natural-language description of intended function.",
            },
            "preconditions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Python boolean expressions over named inputs.",
            },
            "postconditions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Python boolean expressions over result and inputs.",
            },
            "behavioral_examples": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Concrete input/expected pairs.",
            },
            "derivation_sources": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": sorted(_ALLOWED_SOURCES),
                },
                "description": "Which evidence sources informed this FM.",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Heuristic confidence score in [0, 1].",
            },
        },
        "additionalProperties": False,
    }


# ---------------------------------------------------------------------------
# AST allowlist verification (structural, no evaluation)
# ---------------------------------------------------------------------------


def _walk_verify(node: ast.expr) -> None:  # noqa: C901
    """Walk *node* and raise ValueError if any disallowed construct is found.

    Only the node types listed below are accepted; everything else — Attribute
    access, out-of-allowlist Call, comprehensions, lambdas, walrus, starred —
    raises immediately.  This is called by both ``validate_function_model``
    (structure-only, before evaluation) and ``_safe_eval`` (before each eval).
    """
    if isinstance(node, ast.Constant):
        return

    if isinstance(node, ast.Name):
        if not isinstance(node.ctx, ast.Load):
            raise ValueError("Non-load Name context rejected in assertion")
        return  # id checked at eval time when namespace is known

    if isinstance(node, ast.BoolOp):
        for val in node.values:
            _walk_verify(val)
        return

    if isinstance(node, ast.UnaryOp):
        _walk_verify(node.operand)
        return

    if isinstance(node, ast.BinOp):
        # Exponentiation is removed entirely (D98): a chained `**`
        # (`(((10**1000)**1000)**1000)`) explodes the integer multiplicatively
        # while each exponent stays under any per-exponent cap and the whole
        # expression stays under the node cap → resource-exhaustion DoS. Boolean
        # pre/postconditions never need `**`. (Mult/LShift grow size only
        # linearly in node count, so they stay bounded.)
        if isinstance(node.op, ast.Pow):
            raise ValueError("Exponentiation (**) rejected in assertion (resource-exhaustion guard)")
        _walk_verify(node.left)
        _walk_verify(node.right)
        return

    if isinstance(node, ast.Compare):
        _walk_verify(node.left)
        for comp in node.comparators:
            _walk_verify(comp)
        return

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError(
                f"Call to non-Name function rejected (Attribute call?): "
                f"{ast.dump(node.func)}"
            )
        if node.func.id not in _SAFE_SYMBOLS:
            raise ValueError(
                f"Call to {node.func.id!r} rejected — not in safe-symbol table"
            )
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                raise ValueError("Starred argument in Call rejected")
            _walk_verify(arg)
        if node.keywords:
            raise ValueError("Keyword arguments in Call rejected")
        return

    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for elt in node.elts:
            _walk_verify(elt)
        return

    if isinstance(node, ast.Dict):
        for k in node.keys:
            if k is None:
                # `{**d}` dict-unpacking — a None key. Reject (it would otherwise
                # evaluate to a wrong {None: d} result; D98 correctness finding).
                raise ValueError("Dict unpacking ({**d}) rejected in assertion")
            _walk_verify(k)
        for v in node.values:
            _walk_verify(v)
        return

    if isinstance(node, ast.Subscript):
        _walk_verify(node.value)
        slice_node = node.slice
        # Python 3.8 wraps slices in ast.Index; 3.9+ does not.
        if isinstance(slice_node, ast.Index):  # type: ignore[attr-defined]
            slice_node = slice_node.value  # type: ignore[attr-defined]
        if isinstance(slice_node, ast.Slice):
            if slice_node.lower is not None:
                _walk_verify(slice_node.lower)
            if slice_node.upper is not None:
                _walk_verify(slice_node.upper)
            if slice_node.step is not None:
                _walk_verify(slice_node.step)
        else:
            _walk_verify(slice_node)
        return

    # --- Explicitly rejected node types ---
    if isinstance(node, ast.Attribute):
        raise ValueError("Attribute access rejected in assertion")

    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
        raise ValueError("Comprehension/generator rejected in assertion")

    if isinstance(node, ast.Lambda):
        raise ValueError("Lambda rejected in assertion")

    if isinstance(node, ast.NamedExpr):
        raise ValueError("Walrus operator (:=) rejected in assertion")

    if isinstance(node, ast.Starred):
        raise ValueError("Starred expression rejected in assertion")

    if isinstance(node, ast.IfExp):
        raise ValueError("Ternary (if-expression) rejected in assertion")

    if isinstance(node, ast.JoinedStr):
        raise ValueError("f-string rejected in assertion")

    raise ValueError(f"Node type {type(node).__name__!r} not allowed in assertion")


def _check_assertion_ast(expr: str) -> None:
    """Parse *expr* and verify every node is in the AST allowlist.

    Raises:
        ValueError: if any disallowed node is found, or if *expr* has a
            syntax error.

    This validates structure only — Name identifiers are checked at evaluation
    time when the bound namespace is known.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Assertion syntax error: {exc}") from exc
    _enforce_node_cap(tree)
    _walk_verify(tree.body)


def _enforce_node_cap(tree: ast.AST) -> None:
    """Reject a pathologically large assertion (resource-exhaustion guard, D98)."""
    node_count = sum(1 for _ in ast.walk(tree))
    if node_count > _MAX_ASSERTION_NODES:
        raise ValueError(
            f"Assertion too large ({node_count} AST nodes > {_MAX_ASSERTION_NODES} "
            "cap) — rejected (resource-exhaustion guard)"
        )


# ---------------------------------------------------------------------------
# Pure recursive AST evaluator — no eval/exec
# ---------------------------------------------------------------------------


def _eval_node(node: ast.expr, names: dict) -> Any:  # noqa: C901
    """Recursively evaluate *node* against *names* and _SAFE_SYMBOLS.

    Every branch first verifies the node is allowed, then evaluates it.
    Attribute access, out-of-allowlist calls, and unknown names all raise
    ValueError — the same class as _walk_verify so callers see a uniform
    surface.
    """
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if not isinstance(node.ctx, ast.Load):
            raise ValueError("Non-load Name context rejected in assertion")
        if node.id in names:
            return names[node.id]
        if node.id in _SAFE_SYMBOLS:
            return _SAFE_SYMBOLS[node.id]
        raise ValueError(f"Name {node.id!r} not in assertion namespace")

    if isinstance(node, ast.BoolOp):
        values = node.values
        if isinstance(node.op, ast.And):
            result: Any = True
            for val in values:
                result = _eval_node(val, names)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for val in values:
                result = _eval_node(val, names)
                if result:
                    return result
            return result
        raise ValueError(f"Unknown BoolOp: {type(node.op).__name__}")

    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, names)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.Invert):
            return ~operand
        raise ValueError(f"Unknown UnaryOp: {type(node.op).__name__}")

    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, names)
        right = _eval_node(node.right, names)
        _BIN_OPS: dict[type, Any] = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.FloorDiv: lambda a, b: a // b,
            ast.Mod: lambda a, b: a % b,
            # ast.Pow intentionally absent — rejected at walk time (D98 DoS guard).
            ast.BitAnd: lambda a, b: a & b,
            ast.BitOr: lambda a, b: a | b,
            ast.BitXor: lambda a, b: a ^ b,
            ast.LShift: lambda a, b: a << b,
            ast.RShift: lambda a, b: a >> b,
            ast.MatMult: lambda a, b: a @ b,
        }
        fn = _BIN_OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"Unknown BinOp: {type(node.op).__name__}")
        # Resource-exhaustion guard (D98): a huge `<<` shift builds a giant
        # integer with no call — cap it. (`**` is removed entirely above.)
        if isinstance(node.op, ast.LShift) and isinstance(right, int):
            if right > _MAX_SHIFT:
                raise ValueError(
                    f"Shift {right} exceeds cap {_MAX_SHIFT} (resource-exhaustion guard)"
                )
        return fn(left, right)

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, names)
        _CMP_OPS: dict[type, Any] = {
            ast.Eq: lambda a, b: a == b,
            ast.NotEq: lambda a, b: a != b,
            ast.Lt: lambda a, b: a < b,
            ast.LtE: lambda a, b: a <= b,
            ast.Gt: lambda a, b: a > b,
            ast.GtE: lambda a, b: a >= b,
            ast.In: lambda a, b: a in b,
            ast.NotIn: lambda a, b: a not in b,
            ast.Is: lambda a, b: a is b,
            ast.IsNot: lambda a, b: a is not b,
        }
        for op, comp_node in zip(node.ops, node.comparators):
            right = _eval_node(comp_node, names)
            fn = _CMP_OPS.get(type(op))
            if fn is None:
                raise ValueError(f"Unknown Compare op: {type(op).__name__}")
            if not fn(left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError(
                f"Call to non-Name function rejected: {ast.dump(node.func)}"
            )
        if node.func.id not in _SAFE_SYMBOLS:
            raise ValueError(
                f"Call to {node.func.id!r} rejected — not in safe-symbol table"
            )
        if any(isinstance(a, ast.Starred) for a in node.args):
            raise ValueError("Starred argument in Call rejected")
        if node.keywords:
            raise ValueError("Keyword arguments in Call rejected")
        fn = _SAFE_SYMBOLS[node.func.id]
        args = [_eval_node(a, names) for a in node.args]
        return fn(*args)

    if isinstance(node, ast.List):
        return [_eval_node(e, names) for e in node.elts]

    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(e, names) for e in node.elts)

    if isinstance(node, ast.Set):
        return {_eval_node(e, names) for e in node.elts}

    if isinstance(node, ast.Dict):
        if any(k is None for k in node.keys):
            raise ValueError("Dict unpacking ({**d}) rejected in assertion")
        keys = [_eval_node(k, names) for k in node.keys]
        vals = [_eval_node(v, names) for v in node.values]
        return dict(zip(keys, vals))

    if isinstance(node, ast.Subscript):
        value = _eval_node(node.value, names)
        slice_node = node.slice
        if isinstance(slice_node, ast.Index):  # type: ignore[attr-defined]
            slice_node = slice_node.value  # type: ignore[attr-defined]
        if isinstance(slice_node, ast.Slice):
            lo = _eval_node(slice_node.lower, names) if slice_node.lower is not None else None
            hi = _eval_node(slice_node.upper, names) if slice_node.upper is not None else None
            st = _eval_node(slice_node.step, names) if slice_node.step is not None else None
            return value[lo:hi:st]
        return value[_eval_node(slice_node, names)]

    # Rejected node types — same messages as _walk_verify for consistency
    if isinstance(node, ast.Attribute):
        raise ValueError("Attribute access rejected in assertion")

    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
        raise ValueError("Comprehension/generator rejected in assertion")

    if isinstance(node, ast.Lambda):
        raise ValueError("Lambda rejected in assertion")

    if isinstance(node, ast.NamedExpr):
        raise ValueError("Walrus operator (:=) rejected in assertion")

    if isinstance(node, ast.Starred):
        raise ValueError("Starred expression rejected in assertion")

    raise ValueError(f"Node type {type(node).__name__!r} not allowed in assertion")


# ---------------------------------------------------------------------------
# Public: _safe_eval
# ---------------------------------------------------------------------------


def _safe_eval(expr: str, names: dict) -> bool:
    """Evaluate a boolean assertion expression over *names* WITHOUT eval/exec.

    Security-critical: this is the ONLY sanctioned path for evaluating
    LLM-authored FM assertions.  ``eval``/``exec`` are prohibited throughout
    this module (registered in ``protocol/exec-safety.md``).

    Algorithm:
        1. ``ast.parse(expr, mode="eval")`` — raises ValueError on syntax error.
        2. ``_walk_verify(tree.body)`` — AST allowlist check; raises ValueError
           on any disallowed node.
        3. ``_eval_node(tree.body, names)`` — pure recursive evaluation.

    Args:
        expr:  A Python expression string (LLM-authored assertion).
        names: Bound variable namespace (e.g. inputs + "result").

    Returns:
        bool — the truth value of the expression.

    Raises:
        ValueError: if *expr* contains any disallowed node, an unknown name,
            or a syntax error.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Assertion syntax error: {exc}") from exc
    _enforce_node_cap(tree)
    _walk_verify(tree.body)
    return bool(_eval_node(tree.body, names))


# ---------------------------------------------------------------------------
# Public: validate_function_model
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = (
    "module",
    "intent_summary",
    "preconditions",
    "postconditions",
    "behavioral_examples",
    "derivation_sources",
    "confidence",
)


def validate_function_model(fm: dict) -> list[str]:
    """Validate *fm* against the function_model schema.

    Returns a list of error strings; an empty list means the FM is valid.
    Checks performed:
      - all required fields present
      - ``module`` and ``intent_summary`` are strings
      - ``preconditions`` and ``postconditions`` are lists of strings
      - ``behavioral_examples`` is a list of dicts
      - ``derivation_sources`` is a list of strings, each in the allowed set
      - ``confidence`` is a float/int in [0, 1]
      - every precondition and postcondition passes the AST allowlist

    A non-conforming assertion is a validation error (surfaced before
    any evaluation, as required by exec-safety.md).
    """
    errors: list[str] = []

    # Required fields
    for field in _REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"Missing required field: {field!r}")

    if errors:
        # Stop early — further checks assume the fields exist
        return errors

    # additionalProperties: False — the schema forbids extra keys (D98 drift fix)
    extra = set(fm) - set(_REQUIRED_FIELDS)
    if extra:
        errors.append(f"Unexpected field(s) not in schema: {sorted(extra)}")

    # module / intent_summary
    if not isinstance(fm["module"], str):
        errors.append("'module' must be a string")
    if not isinstance(fm["intent_summary"], str):
        errors.append("'intent_summary' must be a string")

    # preconditions
    if not isinstance(fm["preconditions"], list):
        errors.append("'preconditions' must be a list of strings")
    else:
        for i, item in enumerate(fm["preconditions"]):
            if not isinstance(item, str):
                errors.append(f"'preconditions[{i}]' must be a string, got {type(item).__name__}")

    # postconditions
    if not isinstance(fm["postconditions"], list):
        errors.append("'postconditions' must be a list of strings")
    else:
        for i, item in enumerate(fm["postconditions"]):
            if not isinstance(item, str):
                errors.append(f"'postconditions[{i}]' must be a string, got {type(item).__name__}")

    # behavioral_examples
    if not isinstance(fm["behavioral_examples"], list):
        errors.append("'behavioral_examples' must be a list")
    else:
        for i, item in enumerate(fm["behavioral_examples"]):
            if not isinstance(item, dict):
                errors.append(f"'behavioral_examples[{i}]' must be a dict")

    # derivation_sources
    if not isinstance(fm["derivation_sources"], list):
        errors.append("'derivation_sources' must be a list of strings")
    else:
        for i, src in enumerate(fm["derivation_sources"]):
            if not isinstance(src, str):
                errors.append(f"'derivation_sources[{i}]' must be a string")
            elif src not in _ALLOWED_SOURCES:
                errors.append(
                    f"'derivation_sources[{i}]' value {src!r} not in allowed set "
                    f"{sorted(_ALLOWED_SOURCES)}"
                )

    # confidence — reject bool (isinstance(True, int) is True) per schema (D98)
    conf = fm["confidence"]
    if isinstance(conf, bool) or not isinstance(conf, (int, float)):
        errors.append("'confidence' must be a number (not a bool)")
    elif not (0.0 <= float(conf) <= 1.0):
        errors.append(f"'confidence' must be in [0, 1], got {conf}")

    # AST allowlist check for assertion fields (only if they are lists of strings)
    if isinstance(fm["preconditions"], list):
        for i, cond in enumerate(fm["preconditions"]):
            if isinstance(cond, str):
                try:
                    _check_assertion_ast(cond)
                except ValueError as exc:
                    errors.append(f"'preconditions[{i}]' fails AST allowlist: {exc}")

    if isinstance(fm["postconditions"], list):
        for i, cond in enumerate(fm["postconditions"]):
            if isinstance(cond, str):
                try:
                    _check_assertion_ast(cond)
                except ValueError as exc:
                    errors.append(f"'postconditions[{i}]' fails AST allowlist: {exc}")

    return errors


# ---------------------------------------------------------------------------
# Public: evaluate_spec
# ---------------------------------------------------------------------------


def evaluate_spec(fm: dict, call: dict) -> dict:
    """Evaluate an FM's pre/postconditions against a call record.

    Given an FM and ``call = {"inputs": {...}, "result": <value>}``, evaluates
    each precondition over ``inputs`` and each postcondition over
    ``inputs | {"result": result}`` via ``_safe_eval``.

    Returns:
        ``{"ok": bool, "violations": [<failed assertion strings>]}``
        An assertion that raises ValueError is appended as
        ``"<cond> [error: <msg>]"``.
    """
    # Fail-closed on a malformed call record (don't leak a KeyError to the caller).
    if not isinstance(call, dict) or "inputs" not in call or "result" not in call:
        return {"ok": False, "violations": ["malformed call record (need 'inputs' + 'result')"]}
    inputs = call["inputs"]
    if not isinstance(inputs, dict):
        return {"ok": False, "violations": ["call['inputs'] must be a dict"]}
    result: Any = call["result"]
    violations: list[str] = []

    # Evaluate preconditions
    for pre in fm.get("preconditions", []):
        try:
            ok_pre = _safe_eval(pre, dict(inputs))
        except Exception as exc:  # noqa: BLE001
            violations.append(f"{pre} [error: {exc}]")
        else:
            if not ok_pre:
                violations.append(pre)

    # Evaluate postconditions
    for post in fm.get("postconditions", []):
        ns = {**inputs, "result": result}
        try:
            ok_post = _safe_eval(post, ns)
        except Exception as exc:  # noqa: BLE001
            violations.append(f"{post} [error: {exc}]")
        else:
            if not ok_post:
                violations.append(post)

    ok = len(violations) == 0
    return {"ok": ok, "violations": violations}


# ---------------------------------------------------------------------------
# Public: emit_function_model / load_function_model
# ---------------------------------------------------------------------------


def emit_function_model(fm: dict, path: str | Path) -> None:
    """Write *fm* to *path* as pretty-printed JSON.

    Args:
        fm:   A function_model dict (should pass validate_function_model).
        path: Destination file path (created, including parents, if needed).
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(fm, indent=2, ensure_ascii=False), encoding="utf-8")


def load_function_model(path: str | Path) -> dict:
    """Load and return a function_model dict from *path*.

    Args:
        path: Path to a JSON file previously written by emit_function_model.

    Returns:
        The parsed function_model dict.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))
