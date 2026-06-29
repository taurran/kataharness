"""test_exec_safety.py — regression guard for the execution-surface contract.

Enforces `protocol/exec-safety.md`: the command/code-injection (RCE) class recurred
THREE times in the kata-preflight auto-installer (freeform `install`, `package`
source-injection, freeform `verify`), each fixed in isolation. These tests make the
class non-recurring by failing CI if:

  1. a NEW `shell=True` appears outside the registered operator-domain allowlist,
  2. the external-input engine (kata_preflight) ever regains a `shell=True`,
  3. the freeform `verify`/`install` fields are ever read for execution again (#3 / #1),
  4. the structured builders / validators that replaced the freeform paths go missing,
  5. a registered `shell=True` sink is not documented in protocol/exec-safety.md.

Checks are AST-based (not text grep) so they bind to real code, not to the comments
that describe the safety properties. This is the mechanical guard that would have
caught the D111 `verify` RCE.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parent.parent
_REPO = _TOOLS.parent
_EXEC_SAFETY_DOC = _REPO / "protocol" / "exec-safety.md"

# The ONLY files permitted to use shell=True — operator-trust-domain commands
# (the operator's own test/gate/mutation command, same trust as a test runner).
# A new shell=True anywhere else must (a) be justified, (b) be added here, and
# (c) be registered in protocol/exec-safety.md. See that contract.
_SHELL_TRUE_ALLOWLIST = {"mutation_run.py", "run_result.py"}

# Manifest fields that are documentation-only and must NEVER be read for execution.
_FORBIDDEN_EXEC_FIELDS = {"verify", "install"}


def _tool_trees() -> dict[str, ast.Module]:
    """Map of `<filename>.py` -> parsed AST for every top-level tools/*.py."""
    return {p.name: ast.parse(p.read_text(encoding="utf-8")) for p in _TOOLS.glob("*.py")}


def _uses_shell_true(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if (kw.arg == "shell" and isinstance(kw.value, ast.Constant)
                        and kw.value.value is True):
                    return True
    return False


def _reads_fields(tree: ast.Module, fields: set[str]) -> set[str]:
    """Return which `fields` are read via `x["f"]` or `x.get("f")` (real reads only —
    NOT dict-literal keys like `{"verify": "ok"}`)."""
    hits: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            if node.slice.value in fields:
                hits.add(node.slice.value)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get" and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value in fields):
            hits.add(node.args[0].value)
    return hits


def _func_defs(tree: ast.Module) -> set[str]:
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def test_shell_true_confined_to_allowlist():
    """No tool may use shell=True except the registered operator-domain sinks."""
    offenders = {
        name for name, tree in _tool_trees().items()
        if _uses_shell_true(tree) and name not in _SHELL_TRUE_ALLOWLIST
    }
    assert not offenders, (
        f"shell=True found in unregistered file(s): {sorted(offenders)}. "
        "Per protocol/exec-safety.md, external input must use shell=False + structured "
        "argv. If this is a genuine operator-domain command, add it to the allowlist "
        "AND the exec-safety.md registry with its trust domain."
    )


def test_preflight_engine_has_no_shell_true():
    """The external-input engine (manifest-fed) must never use shell=True."""
    tree = ast.parse((_TOOLS / "kata_preflight.py").read_text(encoding="utf-8"))
    assert not _uses_shell_true(tree), (
        "kata_preflight.py consumes a (partially-trusted) dependency manifest; a "
        "shell=True here is an RCE vector. Build a validated structured argv instead."
    )


def test_preflight_never_reads_freeform_exec_fields():
    """Lock the D111 (#3) and freeze-gate (#1) fixes: the freeform `verify`/`install`
    manifest fields are docs-only and must never be read by the engine."""
    tree = ast.parse((_TOOLS / "kata_preflight.py").read_text(encoding="utf-8"))
    read = _reads_fields(tree, _FORBIDDEN_EXEC_FIELDS)
    assert not read, (
        f"kata_preflight.py reads freeform exec field(s) {sorted(read)} — these are "
        "documentation-only (protocol/exec-safety.md). Presence is checked ONLY via the "
        "structured `verifyImport` (_build_verify_argv); install argv is built from "
        "structured fields (_build_argv)."
    )


def test_structured_builders_and_validators_present():
    """The structured paths that replaced the freeform fields must exist."""
    defs = _func_defs(ast.parse((_TOOLS / "kata_preflight.py").read_text(encoding="utf-8")))
    for symbol in ("_build_argv", "_build_verify_argv", "_validate_package"):
        assert symbol in defs, (
            f"kata_preflight.py is missing {symbol!r} — the structured/validated "
            "execution path required by protocol/exec-safety.md."
        )


def test_exec_safety_contract_exists_and_registers_shell_true_sinks():
    """The contract must exist and name every registered shell=True sink."""
    assert _EXEC_SAFETY_DOC.exists(), "protocol/exec-safety.md is missing."
    doc = _EXEC_SAFETY_DOC.read_text(encoding="utf-8")
    for name in _SHELL_TRUE_ALLOWLIST:
        assert name[:-3] in doc, (  # drop ".py"
            f"protocol/exec-safety.md does not register the shell=True sink {name!r}. "
            "Every registered exception must appear in the sink registry."
        )


@pytest.mark.parametrize("payload", [
    "os; import subprocess",          # statement injection
    "x'); import os; os.system('id",  # quote-escape into require()
    "a b",                            # whitespace
    "a\nimport os",                   # newline
    "../evil",                        # path
])
def test_verify_import_grammar_rejects_injection(payload):
    """_build_verify_argv must reject any verifyImport that isn't a clean identifier."""
    import kata_preflight as pf
    for manager in ("pip", "uv", "npm", "cargo"):
        with pytest.raises(ValueError):
            pf._build_verify_argv({"verifyImport": payload}, manager)


# ---------------------------------------------------------------------------
# In-process surface: function_model._safe_eval (S2)
# ---------------------------------------------------------------------------

def test_function_model_never_calls_eval_or_exec():
    """function_model.py must never call eval or exec on an assertion string.

    AST-based check: walk every Call node in function_model.py and confirm
    that neither 'eval' nor 'exec' is called as a bare Name (the prohibited
    path per protocol/exec-safety.md in-process section).
    """
    src = (_TOOLS / "function_model.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec"}, (
                    f"function_model.py calls {node.func.id!r} — prohibited by "
                    "protocol/exec-safety.md (in-process section). Use _safe_eval "
                    "with the AST allowlist instead."
                )
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"eval", "exec"}, (
                    f"function_model.py calls .{node.func.attr}() — prohibited "
                    "by protocol/exec-safety.md (in-process section)."
                )


def test_safe_eval_symbol_exists_in_function_model():
    """_safe_eval must exist as a function definition in function_model.py."""
    src = (_TOOLS / "function_model.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    func_names = {
        n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
    }
    assert "_safe_eval" in func_names, (
        "function_model.py is missing '_safe_eval'. "
        "This surface must exist and be registered in protocol/exec-safety.md."
    )


def test_safe_eval_doc_registered_in_exec_safety():
    """_safe_eval must appear in the protocol/exec-safety.md registry.

    S2 registers the in-process evaluation surface (LLM-authored FM assertions)
    as required by the exec-safety contract.
    """
    assert _EXEC_SAFETY_DOC.exists(), "protocol/exec-safety.md is missing."
    doc = _EXEC_SAFETY_DOC.read_text(encoding="utf-8")
    assert "_safe_eval" in doc, (
        "protocol/exec-safety.md does not register '_safe_eval'. "
        "Per S2 requirements, the in-process FM-assertion evaluator must appear "
        "in the exec-safety registry with its trust domain and guard."
    )


def test_exec_safety_doc_has_in_process_section():
    """exec-safety.md must contain an in-process evaluation subsection.

    The file was originally scoped to subprocess sinks only; S2 widens it with
    an 'in-process evaluation of external expressions' section.
    """
    assert _EXEC_SAFETY_DOC.exists(), "protocol/exec-safety.md is missing."
    doc = _EXEC_SAFETY_DOC.read_text(encoding="utf-8")
    assert "in-process" in doc.lower(), (
        "protocol/exec-safety.md has no 'in-process' section. "
        "S2 requires a subsection covering AST-allowlist evaluation of "
        "external (LLM-authored) FM assertions."
    )


# ---------------------------------------------------------------------------
# Registry-completeness: every subprocess sink module must be registered (D5)
# ---------------------------------------------------------------------------

_SUBPROCESS_SINK_ATTRS = {"run", "Popen", "call", "check_output", "check_call"}


def _module_has_subprocess_sink(tree: ast.Module) -> bool:
    """Return True if *tree* contains a real subprocess.<sink>() Call node.

    Matches only ``subprocess.<name>(...)`` attribute calls (ast.Call where
    func is Attribute(value=Name(id='subprocess'), attr in _SUBPROCESS_SINK_ATTRS)).
    Strings, comments, and docstrings that mention subprocess are NOT matched.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr in _SUBPROCESS_SINK_ATTRS
                and isinstance(func.value, ast.Name)
                and func.value.id == "subprocess"
            ):
                return True
    return False


def test_every_subprocess_sink_module_is_registered():
    """Every production tools/*.py module that contains a subprocess sink must be
    registered in protocol/exec-safety.md.

    AST-walks every tools/*.py (glob excludes tools/tests/** automatically — only
    top-level *.py files are matched) and detects real subprocess.run /
    subprocess.Popen / subprocess.call / subprocess.check_output /
    subprocess.check_call call nodes — not strings, comments, or docstrings.
    For each module with ≥1 such sink, asserts that the module stem
    (e.g. ``kata_install``, ``kata_dispatch``) appears somewhere in
    protocol/exec-safety.md.

    A failure here means a real subprocess sink exists with no registry entry.
    Fix by adding the missing row to the exec-safety.md sink registry — do NOT
    silence or skip this test; an unregistered sink is a live security finding.
    """
    assert _EXEC_SAFETY_DOC.exists(), "protocol/exec-safety.md is missing."
    doc = _EXEC_SAFETY_DOC.read_text(encoding="utf-8")

    unregistered: list[str] = []
    for path in sorted(_TOOLS.glob("*.py")):
        module_name = path.stem
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if _module_has_subprocess_sink(tree) and module_name not in doc:
            unregistered.append(module_name)

    assert not unregistered, (
        f"Module(s) with subprocess sinks not registered in protocol/exec-safety.md: "
        f"{sorted(unregistered)}. Every subprocess sink must appear in the exec-safety "
        "registry (see 'Sink registry' section). Add the missing row(s) — do NOT "
        "silence this test; an unregistered sink is a live security finding."
    )
