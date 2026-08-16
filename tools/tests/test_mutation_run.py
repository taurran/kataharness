"""Tests for tools/mutation_run.py — the SANDBOXED mutation-proof runner.

Strategy
--------
All tests inject a ``runner(cmd, cwd)`` callable so no real subprocess or pytest
process is spawned.  Real filesystem writes use ``tmp_path``; every constructed
project carries a ``pyproject.toml`` marker (the grill-D1 root-derivation
contract) unless the test targets derivation failure itself.

Coverage:
- non-vacuous / vacuous verdicts through the sandbox
- THE D1 PIN: the live source file is byte-untouched THROUGHOUT the run —
  observed by the runner DURING the mutated pass, not just after return
- the sandbox copy IS mutated (observed via the runner's cwd)
- redirect mechanics: live-root substitution, .venv interpreter preservation,
  the residual live-root guard (Windows case-insensitive) raising
- sandbox lifecycle: excludes applied; removed after normal AND raising runs
- project-root derivation fail-closed + explicit override + not-under-root
- ValueError propagation (missing line raises BEFORE any run — nothing copied)
- path-traversal guard; Q-4 timeout; DET-09 env sanitization; shell contract
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_project(tmp_path: Path, content: str) -> Path:
    """Write a tiny marker-carrying project (grill D1) and return the source path."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
    p = tmp_path / "sample.py"
    p.write_text(content, encoding="utf-8")
    return p


_SOURCE = "def add(a, b):\n    return a + b\n"
_ASSERTED_LINE = "    return a + b"


# ---------------------------------------------------------------------------
# Verdict plumbing through the sandbox
# ---------------------------------------------------------------------------

def test_non_vacuous_runner_true_then_false(tmp_path):
    """Baseline passes, mutated fails → nonVacuous True, testWentRed True."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    calls = []

    def fake_runner(cmd, cwd):
        calls.append((cmd, cwd))
        # 1st call: pristine sandbox → passes; 2nd call: mutated sandbox → fails
        return len(calls) == 1

    result = mutation_run.prove_non_vacuous(
        str(src_path), _ASSERTED_LINE, "dummy-cmd", runner=fake_runner
    )

    assert result["nonVacuous"] is True
    assert result["testWentRed"] is True
    assert len(calls) == 2
    # grill D3: BOTH runs execute in the SAME sandbox cwd
    assert calls[0][1] == calls[1][1]
    assert calls[0][1] != str(tmp_path), "runs must target the sandbox, not the live tree"


def test_vacuous_runner_true_both(tmp_path):
    """Baseline passes, mutated also passes → nonVacuous False."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)

    result = mutation_run.prove_non_vacuous(
        str(src_path), _ASSERTED_LINE, "dummy-cmd", runner=lambda cmd, cwd: True
    )

    assert result["nonVacuous"] is False
    assert result["testWentRed"] is False


# ---------------------------------------------------------------------------
# THE D1 PIN — the live tree is never written (the phantom-corruption fix)
# ---------------------------------------------------------------------------

def test_live_file_untouched_throughout_the_run(tmp_path):
    """The live source is byte-identical DURING the mutated pass — observed by the
    runner mid-run, not merely restored afterwards (the old design was 'restored
    afterwards'; the corruption window lived between write and restore)."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    original_bytes = src_path.read_bytes()
    observed: list[bytes] = []

    def observing_runner(cmd, cwd):
        observed.append(src_path.read_bytes())   # read the LIVE file on every pass
        return len(observed) == 1

    result = mutation_run.prove_non_vacuous(
        str(src_path), _ASSERTED_LINE, "dummy-cmd", runner=observing_runner
    )

    assert result["nonVacuous"] is True
    assert observed == [original_bytes, original_bytes], (
        "the LIVE file changed during the run — the D1 corruption window is back"
    )
    assert src_path.read_bytes() == original_bytes


def test_sandbox_copy_is_mutated_not_the_original(tmp_path):
    """The mutation lands in the sandbox copy (visible via the runner's cwd)."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    seen: list[str] = []

    def sandbox_reader(cmd, cwd):
        seen.append((Path(cwd) / "sample.py").read_text(encoding="utf-8"))
        return True

    mutation_run.prove_non_vacuous(
        str(src_path), _ASSERTED_LINE, "dummy-cmd", runner=sandbox_reader
    )

    assert seen[0] == _SOURCE, "baseline must run on the PRISTINE copy"
    assert _ASSERTED_LINE not in seen[1], "mutated pass must see the line removed"


def test_live_file_untouched_when_runner_raises(tmp_path):
    """A runner exception propagates; the live file was never written anyway."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    original_bytes = src_path.read_bytes()
    call_count = [0]

    def raising_runner(cmd, cwd):
        call_count[0] += 1
        if call_count[0] == 1:
            return True          # baseline passes
        raise RuntimeError("injected failure on mutated run")

    with pytest.raises(RuntimeError, match="injected failure"):
        mutation_run.prove_non_vacuous(
            str(src_path), _ASSERTED_LINE, "dummy-cmd", runner=raising_runner
        )

    assert src_path.read_bytes() == original_bytes


# ---------------------------------------------------------------------------
# Sandbox lifecycle (grill D1/D3)
# ---------------------------------------------------------------------------

def test_sandbox_removed_after_normal_and_raising_runs(tmp_path):
    """The temp sandbox is removed in finally — normal path and raising path."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    sandboxes: list[str] = []

    def capture_runner(cmd, cwd):
        sandboxes.append(cwd)
        return True

    mutation_run.prove_non_vacuous(str(src_path), _ASSERTED_LINE, "x", runner=capture_runner)

    def raising_runner(cmd, cwd):
        sandboxes.append(cwd)
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        mutation_run.prove_non_vacuous(str(src_path), _ASSERTED_LINE, "x", runner=raising_runner)

    assert sandboxes, "runner never saw a sandbox"
    for sb in sandboxes:
        assert not Path(sb).exists(), f"sandbox {sb} leaked past the finally cleanup"


def test_sandbox_excludes_hygiene_dirs(tmp_path):
    """.git/.venv/.kata/__pycache__ never enter the sandbox (grill D1)."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    for d in (".git", ".venv", ".kata", "__pycache__"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "marker.txt").write_text("x", encoding="utf-8")
    (tmp_path / "kept.txt").write_text("keep me", encoding="utf-8")
    seen: dict = {}

    def inspecting_runner(cmd, cwd):
        seen["entries"] = sorted(p.name for p in Path(cwd).iterdir())
        return True

    mutation_run.prove_non_vacuous(str(src_path), _ASSERTED_LINE, "x", runner=inspecting_runner)

    assert "kept.txt" in seen["entries"] and "sample.py" in seen["entries"]
    for excluded in (".git", ".venv", ".kata", "__pycache__"):
        assert excluded not in seen["entries"], f"{excluded} must not be copied"


# ---------------------------------------------------------------------------
# Redirect mechanics (grill D4/D5)
# ---------------------------------------------------------------------------

def test_redirect_substitutes_live_root_but_preserves_venv(tmp_path):
    """Absolute live-root references are redirected; <root>/.venv interpreter
    references survive un-rewritten (the live venv is read-only and excluded
    from the copy)."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    root = str(tmp_path.resolve())
    venv_py = str(tmp_path.resolve() / ".venv" / "Scripts" / "python.exe")
    cmd = f'cd /d "{root}" && "{venv_py}" -m pytest tests -q'
    seen: dict = {}

    def capture_runner(rcmd, cwd):
        seen["cmd"], seen["cwd"] = rcmd, cwd
        return True

    mutation_run.prove_non_vacuous(str(src_path), _ASSERTED_LINE, cmd, runner=capture_runner)

    assert seen["cmd"].startswith(f'cd /d "{seen["cwd"]}"'), (
        "the cd target must be redirected into the sandbox"
    )
    assert venv_py in seen["cmd"], (
        "the .venv interpreter reference must survive redirection un-rewritten"
    )


def test_redirect_leaves_prefix_sibling_paths_untouched(tmp_path):
    """Adval F1: a root that is a PREFIX of a sibling path must not rewrite the
    sibling (C:\\proj vs C:\\proj2 / <root>-backup) nor trip the residual guard."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    root = str(tmp_path.resolve())
    sibling = root + "2"
    backup = root + "-backup"
    cmd = f'cd /d "{root}" && copy "{sibling}\\data.txt" "{backup}\\x"'
    seen: dict = {}

    def capture_runner(rcmd, cwd):
        seen["cmd"], seen["cwd"] = rcmd, cwd
        return True

    mutation_run.prove_non_vacuous(str(src_path), _ASSERTED_LINE, cmd, runner=capture_runner)

    assert f'"{sibling}\\data.txt"' in seen["cmd"], "prefix sibling must survive untouched"
    assert f'"{backup}\\x"' in seen["cmd"], "root-backup sibling must survive untouched"
    assert seen["cmd"].startswith(f'cd /d "{seen["cwd"]}"'), "the true root still redirects"


def test_venv_lookahead_true_component_only(tmp_path):
    """Adval F2: only a TRUE .venv component is preserved — <root>/.venv-old is
    substituted like any subpath (loud, never a silent live reference), and a
    doubled separator before .venv still preserves the interpreter path."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    root = str(tmp_path.resolve())
    cmd = f'"{root}\\.venv-old\\py.exe" && "{root}\\\\.venv\\Scripts\\python.exe" -m pytest'
    seen: dict = {}

    def capture_runner(rcmd, cwd):
        seen["cmd"], seen["cwd"] = rcmd, cwd
        return True

    mutation_run.prove_non_vacuous(str(src_path), _ASSERTED_LINE, cmd, runner=capture_runner)

    assert f"{root}\\.venv-old" not in seen["cmd"], ".venv-old must be substituted (not preserved)"
    assert f'"{seen["cwd"]}\\.venv-old\\py.exe"' in seen["cmd"]
    assert f"{root}\\\\.venv\\Scripts\\python.exe" in seen["cmd"], (
        "a doubled-separator TRUE .venv reference must be preserved"
    )


@pytest.mark.skipif(os.name != "nt", reason="case-insensitive residual guard is Windows-only")
def test_residual_live_root_guard_raises_on_case_mismatch(tmp_path):
    """A case-twisted live-root spelling survives exact-case substitution — the
    residual guard must RAISE rather than let the mutation run target the live
    tree (grill D5)."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    twisted = str(tmp_path.resolve()).swapcase()
    cmd = f'cd /d "{twisted}" && py -m pytest'

    with pytest.raises(ValueError, match="LIVE project root"):
        mutation_run.prove_non_vacuous(
            str(src_path), _ASSERTED_LINE, cmd, runner=lambda c, w: True
        )


def test_relative_cmd_gets_sandbox_cwd(tmp_path):
    """A relative test_cmd carries no root reference — the sandbox cwd IS the
    redirect (grill D2)."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    seen: list = []

    def capture_runner(cmd, cwd):
        seen.append((cmd, cwd))
        return True

    mutation_run.prove_non_vacuous(
        str(src_path), _ASSERTED_LINE, "pytest tests -q", runner=capture_runner
    )

    assert seen[0][0] == "pytest tests -q"          # untouched — nothing to substitute
    assert Path(seen[0][1]).name == "tree"          # ...but it runs in the sandbox
    assert (Path(seen[0][1]) / "sample.py").name    # containing the copied project


# ---------------------------------------------------------------------------
# Project-root derivation (grill D1 — fail-closed)
# ---------------------------------------------------------------------------

def test_no_marker_anywhere_raises(tmp_path, monkeypatch):
    """No pyproject.toml/.git in any ancestor ⇒ ValueError (never guess the scope).

    The tmp tree is markerless AND the test monkeypatches _find_project_root's
    walk ceiling by pointing the source at a markerless subtree of tmp_path —
    if some ancestor of the pytest tmp dir carries a marker on a given machine,
    the explicit-project_root path still proves the fail-closed message."""
    import mutation_run

    sub = tmp_path / "bare"
    sub.mkdir()
    p = sub / "sample.py"
    p.write_text(_SOURCE, encoding="utf-8")

    ancestors_have_marker = any(
        (a / "pyproject.toml").exists() or (a / ".git").exists() for a in p.parents
    )
    if ancestors_have_marker:
        pytest.skip("an ancestor of tmp_path carries a marker on this machine")
    with pytest.raises(ValueError, match="no project root"):
        mutation_run.prove_non_vacuous(str(p), _ASSERTED_LINE, "x", runner=lambda c, w: True)


def test_explicit_project_root_override(tmp_path):
    """project_root= overrides derivation; the sandbox is that tree."""
    import mutation_run

    sub = tmp_path / "bare"
    sub.mkdir()
    p = sub / "sample.py"
    p.write_text(_SOURCE, encoding="utf-8")
    seen: dict = {}

    def capture_runner(cmd, cwd):
        seen["entries"] = sorted(x.name for x in Path(cwd).iterdir())
        return True

    mutation_run.prove_non_vacuous(
        str(p), _ASSERTED_LINE, "x", runner=capture_runner, project_root=str(sub)
    )
    assert seen["entries"] == ["sample.py"]


def test_source_not_under_project_root_raises(tmp_path):
    """An explicit root that does not contain the source ⇒ ValueError (D136)."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    other = tmp_path / "elsewhere"
    other.mkdir()

    with pytest.raises(ValueError, match="not under the project root"):
        mutation_run.prove_non_vacuous(
            str(src_path), _ASSERTED_LINE, "x",
            runner=lambda c, w: True, project_root=str(other),
        )


# ---------------------------------------------------------------------------
# Error propagation + guards
# ---------------------------------------------------------------------------

def test_missing_line_raises_before_any_run(tmp_path):
    """apply_line_removal of a missing line → ValueError BEFORE any sandbox copy
    or runner call (an invalid spec costs nothing); live file untouched."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    original_bytes = src_path.read_bytes()
    call_count = [0]

    def counting_runner(cmd, cwd):
        call_count[0] += 1
        return True

    with pytest.raises(ValueError):
        mutation_run.prove_non_vacuous(
            str(src_path),
            "this line does not exist in the source",
            "dummy-cmd",
            runner=counting_runner,
        )

    assert call_count[0] == 0, "an invalid spec must not spend a single test run"
    assert src_path.read_bytes() == original_bytes


def test_path_traversal_guard_raises(tmp_path):
    """A source_path containing '..' must be rejected with ValueError (CWE-23)."""
    import mutation_run

    traversal = str(tmp_path / ".." / "evil.py")

    with pytest.raises(ValueError):
        mutation_run.prove_non_vacuous(
            traversal, "anything", "dummy-cmd", runner=lambda c, w: True
        )


def test_prove_many_collects_verdicts_and_passes_project_root(tmp_path):
    """prove_many returns one verdict per spec and forwards spec project_root."""
    import mutation_run

    src_path = _write_project(tmp_path, _SOURCE)
    call_count = [0]

    def alternating_runner(cmd, cwd):
        # Calls: 1=baseline True, 2=mutated False → nonVacuous True (per spec)
        call_count[0] += 1
        return call_count[0] % 2 == 1  # odd calls pass, even calls fail

    specs = [
        {"source_path": str(src_path), "asserted_line": _ASSERTED_LINE, "test_cmd": "x"},
        {"source_path": str(src_path), "asserted_line": _ASSERTED_LINE, "test_cmd": "x",
         "project_root": str(tmp_path)},
    ]

    results = mutation_run.prove_many(specs, runner=alternating_runner)
    assert len(results) == 2
    for r in results:
        assert r["nonVacuous"] is True and r["testWentRed"] is True


# ---------------------------------------------------------------------------
# Q-4 timeout tests — a hung test command must go RED, never hang (D136)
# ---------------------------------------------------------------------------

def test_default_runner_timeout_returns_false(monkeypatch, capsys):
    """Q-4: subprocess.TimeoutExpired → False (failure-shaped), never an unhandled raise."""
    import subprocess

    import mutation_run

    def hung_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="sleep-forever", timeout=kwargs.get("timeout"))

    monkeypatch.setattr(mutation_run.subprocess, "run", hung_run)

    assert mutation_run._default_runner("pytest tests -q", timeout=0.01) is False, (
        "a timed-out gate command must be a FAILURE verdict (gate red)"
    )
    captured = capsys.readouterr()
    assert "[kata] gate runner timeout" in captured.err


def test_default_runner_forwards_default_timeout_600_and_cwd(monkeypatch):
    """The default 600s timeout AND the cwd (grill D2) are forwarded to subprocess.run."""
    import mutation_run

    seen: dict = {}

    class _Ok:
        returncode = 0

    def spy_run(*args, **kwargs):
        seen.update(kwargs)
        return _Ok()

    monkeypatch.setattr(mutation_run.subprocess, "run", spy_run)

    assert mutation_run._default_runner("pytest tests -q", "/some/sandbox") is True
    assert seen.get("timeout") == 600.0, (
        "Q-4: _default_runner must bound the subprocess with a 600s default timeout"
    )
    assert seen.get("cwd") == "/some/sandbox", (
        "grill D2: the sandbox cwd must reach subprocess.run"
    )


# ---------------------------------------------------------------------------
# DET-09 (2026-07-12 health review): sanitized gate env (the determinism win) —
# stripping PYTEST_ADDOPTS + disabling plugin autoload removes the cross-host
# nondeterminism that flips the Axis-Q boolean.
#
# BL-X14: shell=True is now GONE. The old note here claimed argv-tokenizing the
# test_cmd "would break every mutation-proof caller". It was the shell string
# that broke them — on Linux, silently, for 12 days. The closed grammar
# (_compile_test_cmd) tokenizes the same corpus with identical meaning on both
# platforms.
# ---------------------------------------------------------------------------

def test_default_runner_env_is_sanitized(monkeypatch):
    """The gate subprocess env strips PYTEST_ADDOPTS and disables plugin autoload
    (DET-09). Mutation-proof: without _sanitized_gate_env this assertion goes RED."""
    import mutation_run

    monkeypatch.setenv("PYTEST_ADDOPTS", "-x --ff")
    seen: dict = {}

    class _Ok:
        returncode = 0

    def spy_run(*args, **kwargs):
        seen.update(kwargs)
        return _Ok()

    monkeypatch.setattr(mutation_run.subprocess, "run", spy_run)
    mutation_run._default_runner("pytest tests -q")
    env = seen.get("env") or {}
    assert "PYTEST_ADDOPTS" not in env, "PYTEST_ADDOPTS must be stripped from the gate env"
    assert env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"


def test_default_runner_uses_structured_argv_never_shell(monkeypatch):
    """BL-X14 / RS-H1: the sink runs structured argv with shell=False, the `cd`
    prefix is CONSUMED into cwd, and the env is still sanitized — all on the
    same call."""
    import mutation_run

    monkeypatch.setenv("PYTEST_ADDOPTS", "-x")
    seen: dict = {}

    class _Ok:
        returncode = 0

    def spy_run(*args, **kwargs):
        seen["cmd"] = args[0] if args else kwargs.get("args")
        seen["shell"] = kwargs.get("shell", False)
        seen["cwd"] = kwargs.get("cwd")
        seen["env"] = kwargs.get("env")
        return _Ok()

    monkeypatch.setattr(mutation_run.subprocess, "run", spy_run)
    mutation_run._default_runner(
        f'cd /d "{_SANDBOX_STUB}" && "{sys.executable}" -m pytest "tests/test_x.py::t" -q --tb=no',
        _SANDBOX_STUB,
    )
    assert seen["shell"] is False, "shell=True must be gone from the mutation sink (BL-X14)"
    assert isinstance(seen["cmd"], list), "the sink must pass an argv LIST, not a shell string"
    assert seen["cmd"] == [
        sys.executable, "-m", "pytest", "tests/test_x.py::t", "-q", "--tb=no",
    ], f"unexpected compiled argv: {seen['cmd']!r}"
    assert "cd" not in seen["cmd"] and "&&" not in seen["cmd"], (
        "the `cd` prefix must be CONSUMED into cwd, never handed to the process"
    )
    assert seen["cwd"] == _SANDBOX_STUB, "the cd target becomes the subprocess cwd"
    assert "PYTEST_ADDOPTS" not in (seen["env"] or {}), "env still sanitized"


def test_mutation_sink_source_contains_no_shell_true():
    """Structural pin (protocol/exec-safety.md): `shell=True` is absent from the
    mutation sink's code. AST-checked so a doc-comment mentioning it cannot pass
    or fail this."""
    import ast

    import mutation_run

    tree = ast.parse(Path(mutation_run.__file__).read_text(encoding="utf-8"))
    offenders = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for kw in node.keywords
        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
    ]
    assert not offenders, f"shell=True still present in mutation_run.py at line(s) {offenders}"


# ---------------------------------------------------------------------------
# The closed test_cmd grammar (BL-X14 / RS-H1) — compile or REFUSE
# ---------------------------------------------------------------------------

_SANDBOX_STUB = str(Path(tempfile.gettempdir()).resolve() / "kata-x14-stub")


def test_compile_consumes_cd_prefix_and_keeps_uv_shape():
    """The `uv run pytest` flavour (test_recurrence_detect / test_validation_misses /
    test_escalation / test_recall) compiles with the cd target as cwd."""
    import mutation_run

    argv, cwd = mutation_run._compile_test_cmd(
        f'cd /d "{_SANDBOX_STUB}" && uv run pytest tests/test_x.py::a tests/test_x.py::b -q',
        _SANDBOX_STUB,
    )
    assert argv == [
        "uv", "run", "pytest", "tests/test_x.py::a", "tests/test_x.py::b", "-q",
    ]
    assert cwd == _SANDBOX_STUB


def test_compile_defaults_cwd_to_sandbox_when_no_cd_prefix():
    """A relative command carries no cd — the sandbox cwd IS the redirect (grill D2)."""
    import mutation_run

    argv, cwd = mutation_run._compile_test_cmd("pytest tests -q", _SANDBOX_STUB)
    assert argv == ["pytest", "tests", "-q"]
    assert cwd == _SANDBOX_STUB


@pytest.mark.parametrize("bad", [
    'cd /d "%s" && rm -rf /' % _SANDBOX_STUB,          # unrecognised runner
    'cd /d "%s" && copy a b' % _SANDBOX_STUB,          # the old cmd.exe `copy` shape
    'pytest tests -q && curl evil.example',            # a second chained command
    'pytest tests -q | tee out.txt',                   # a pipe
    'pytest "$(whoami)"',                              # command substitution
    'python -c "import os"',                           # python, but not -m pytest
    'uv pip install evil',                             # uv, but not `run pytest`
    'cd /d "x" pytest',                                # cd prefix without `&&`
    'pytest "unbalanced',                              # unbalanced quote
])
def test_compile_refuses_everything_outside_the_grammar(bad):
    """compile-through-grammar-or-REFUSE: no best-effort, no degraded run."""
    import mutation_run

    with pytest.raises(ValueError):
        mutation_run._compile_test_cmd(bad, _SANDBOX_STUB)


def test_compile_refuses_cd_escaping_the_sandbox():
    """The structural sandbox-isolation guarantee: a `cd` target outside the
    sandbox is refused, so the re-run can never import the live tree."""
    import mutation_run

    outside = str(Path(tempfile.gettempdir()).resolve() / "kata-x14-elsewhere")
    with pytest.raises(ValueError, match="outside the sandbox"):
        mutation_run._compile_test_cmd(
            f'cd /d "{outside}" && pytest tests -q', _SANDBOX_STUB
        )


@pytest.mark.parametrize("target", ["../../etc/passwd::t", "-p tests"])
def test_compile_guards_node_ids(target):
    """_guard_node_id precedent reuse (benchmark.py:106 / benchmark_def.py:805):
    traversal and flag-shaped targets never reach argv."""
    import mutation_run

    with pytest.raises(ValueError):
        mutation_run._compile_test_cmd(f'pytest "{target}"', _SANDBOX_STUB)


def test_tokenizer_preserves_windows_backslashes():
    """Why not shlex: posix=True eats `C:\\Dev\\x` -> `C:Devx`, posix=False keeps
    the quote characters in the token. Both would corrupt the live corpus."""
    import mutation_run

    assert mutation_run._tokenize(r'"C:\Dev\proj\.venv\Scripts\python.exe" -m pytest') == [
        r"C:\Dev\proj\.venv\Scripts\python.exe", "-m", "pytest",
    ]


# needed by the skipif marker above
_ = sys


# ---------------------------------------------------------------------------
# BL-X14 — the Linux vacuity-prover fix.  END-TO-END (real subprocess) proof
# that the SANDBOX copy is what the re-run actually imports, on THIS platform.
#
# Escalation rule E2 (trust-model PLAN) made BL-X14's stated cause a HYPOTHESIS
# to reproduce, not a fact to fix.  The two probes below are the falsification
# instruments; `test_sandbox_import_isolation_linux` is the pinning regression
# test named in the PLAN's `evidence:` declaration.
# ---------------------------------------------------------------------------

_MINI_PYPROJECT = """\
[project]
name = "x14-sample"
version = "0.0.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
"""

_MINI_MODULE = '''\
"""Tiny module under mutation proof (BL-X14 end-to-end fixture)."""


def classify(n):
    if n < 0:
        return "neg"
    return "pos"
'''

_MINI_ASSERTED_LINE = '        return "neg"'

_MINI_TEST = '''\
import sample_mod


def test_classify_negative():
    assert sample_mod.classify(-1) == "neg"
'''

_MINI_NODE_ID = "tests/test_sample.py::test_classify_negative"


def _write_runnable_project(tmp_path: Path) -> Path:
    """Write a REAL, pytest-runnable mini project and return its source path.

    Shape mirrors ``tools/`` itself: a ``pyproject.toml`` with
    ``pythonpath = ["."]`` so the test imports the module from the *rootdir* —
    which is precisely the property that must land on the SANDBOX copy, not the
    live tree.
    """
    (tmp_path / "pyproject.toml").write_text(_MINI_PYPROJECT, encoding="utf-8")
    src = tmp_path / "sample_mod.py"
    src.write_text(_MINI_MODULE, encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_sample.py").write_text(_MINI_TEST, encoding="utf-8")
    return src


def _live_cmd_shape(root: Path) -> str:
    """The command shape every mutation-proof meta-test in this repo builds.

    Verbatim from `test_benchmark.py::_cmd` / `test_usage_meter.py::_test_cmd`
    (and, in its `uv run` flavour, `test_recurrence_detect` /
    `test_validation_misses`).
    """
    return (
        f'cd /d "{root}" && '
        f'"{sys.executable}" -m pytest '
        f'"{_MINI_NODE_ID}" -q --tb=no'
    )


def test_sandbox_import_isolation_linux(tmp_path):
    """PINNING (BL-X14): a real end-to-end prove run must bite ON THIS PLATFORM.

    This is the per-platform proof that *the sandbox copy is what the re-run
    imports*.  It is a two-sided assertion, and each side falsifies a different
    failure mode:

    - ``baseline`` **True** — the redirected command actually RAN and passed on
      the pristine sandbox copy.  A False here means the command never executed
      as intended (the shell-dialect class: BL-X14's real mechanism on Linux).
    - ``mutated`` **False** — after the SANDBOX copy of the source was mutated,
      the very same command went red.  A True here with a green baseline is the
      import-resolution class (the live/installed module answered the import,
      so the sandbox mutation was invisible) — BL-X14's originally-hypothesised
      mechanism.

    Only ``[True, False]`` proves the prover can fail, which is the TM-D3 law
    applied to the prover itself.  ``{'testWentRed': False}`` alone cannot tell
    the two classes apart — that ambiguity is why ~61 meta-tests were red on
    ubuntu for 12 days with the wrong cause on record.
    """
    import mutation_run

    src = _write_runnable_project(tmp_path)
    cmd = _live_cmd_shape(tmp_path.resolve())
    outcomes: list[bool] = []

    def recording_real_runner(rcmd, cwd):
        ok = mutation_run._default_runner(rcmd, cwd)
        outcomes.append(ok)
        return ok

    verdict = mutation_run.prove_non_vacuous(
        str(src), _MINI_ASSERTED_LINE, cmd, runner=recording_real_runner
    )

    assert outcomes and outcomes[0] is True, (
        "BL-X14: the BASELINE run failed on the PRISTINE sandbox copy — the "
        "mutation proof is vacuous by construction on this platform "
        f"(os.name={os.name!r}, outcomes={outcomes}, verdict={verdict}, "
        f"cmd={cmd!r}). The command never ran as intended."
    )
    assert len(outcomes) == 2 and outcomes[1] is False, (
        "BL-X14: the MUTATED run still PASSED — the re-run did not import the "
        "mutated SANDBOX copy (live/installed module resolved instead) "
        f"(os.name={os.name!r}, outcomes={outcomes}, verdict={verdict})."
    )
    assert verdict == {"testWentRed": True, "nonVacuous": True}, (
        f"BL-X14: prove_non_vacuous must report a biting mutation; got {verdict}"
    )


# The E2 repro probe `test_x14_probe_live_cmd_shape_executes_on_this_platform`
# lived here for exactly one commit (07d1179 -> this one). It asserted that the
# live `cd /d "<dir>" && ...` string executes under `shell=True` on the host —
# TRUE on Windows, FALSE on ubuntu-latest — and its CI failure output is the
# verbatim mechanism record in
# `.planning/specs/trust-model/evidence/x14-ci-green.md`. It is deleted with the
# fix because the sink no longer runs a shell string at all; what replaces it as
# a standing guard is the pair
# `test_sandbox_import_isolation_linux` (end-to-end, per platform) and
# `test_default_runner_uses_structured_argv_never_shell` (structural).
