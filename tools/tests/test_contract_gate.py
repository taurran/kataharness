"""Tests for contract_gate.py — Freeze/Float M1-P2 final-gate re-derivation.

TDD discipline: every git-bearing test builds a REAL temporary git repo via
subprocess (no mocking of git internals); local helpers mirror the
``test_kata_restore.py`` pattern but are NOT imported from it (self-contained).

Coverage (the PLAN-p2 T1 test list — every function mutation-proven):
- pinned_contracts: happy / conflicting-pins-raise / malformed-raise / empty-vacuous
- verify_contract_gate: vacuous-BC; unknown-supersede-id; drift-without-supersede
  fails; drift-with-newest-supersede passes; body-fill passes; coverage-gap fails;
  full-coverage-at-route-time passes; double-supersede round-1-only FAILS (temporal);
  R1a same-body-any-order PASSES; R1b separate-older-commit FAILS; no-catch raise
  propagation.
- _scan_integration_commits: raises on unresolvable fork-point (R8) + on git error.
- dangling_contract_imports: dangler caught (raw-module form); R2a clean; R2b
  documented residual; non-contract dangling ignored; unreadable dependent raises.
- expand_ownership_paths: dir expansion + contract-dir exclusion (honest dependent
  yields empty edge_honesty violations, F5); missing path raises; C1/C10 boundary.
- write_contract_gate: artifact round-trip carrying all three check results.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import contract_edges as ce
import contract_gate as cg

# ---------------------------------------------------------------------------
# Surface bodies (distinct interface surfaces; body-fill leaves the surface fixed)
# ---------------------------------------------------------------------------

_STUB = "def foo(x: int) -> str:\n    ...  # KATA-CONTRACT-STUB\n"
_FILLED = "def foo(x: int) -> str:\n    return str(x)\n"            # same surface as _STUB
_S1 = "def foo(x: int, y: int) -> str:\n    return str(x)\n"        # drifted (added param)
_S2 = "def foo(x: int, y: int, z: int) -> str:\n    return str(x)\n"  # drifted further

_HX = "deadbeefcafe1234"  # a syntactically valid pin (used where the value is inert)


# ---------------------------------------------------------------------------
# Local git helpers (self-contained — NOT imported from test_kata_restore)
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args, cwd=str(cwd), capture_output=True, text=True, check=check
    )


def _make_repo(tmp_path: Path) -> Path:
    """Init a repo on an ``integration`` branch with one base commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], repo)
    _git(["config", "user.email", "test@kata.local"], repo)
    _git(["config", "user.name", "Kata Test"], repo)
    (repo / ".gitignore").write_text(".kata/\n", encoding="utf-8")
    _git(["add", ".gitignore"], repo)
    _git(["commit", "-m", "init"], repo)
    _git(["checkout", "-b", "integration"], repo)
    return repo


def _write_contract(repo: Path, cid: str, body: str) -> Path:
    d = repo / "contracts" / cid
    d.mkdir(parents=True, exist_ok=True)
    (d / "__init__.py").write_text(body, encoding="utf-8")
    return d


def _write_plan(repo: Path, builds_against: dict[str, list[str]]) -> Path:
    """Write a minimal frozen PLAN.md carrying a ``builds_against`` block."""
    lines = ["---", "ownership:"]
    for task in builds_against:
        lines.append(f"  {task}: []")
    lines.append("builds_against:")
    for task, edges in builds_against.items():
        edge_str = ", ".join(f'"{e}"' for e in edges)
        lines.append(f"  {task}: [{edge_str}]")
    lines += ["---", "", "# Frozen Plan", ""]
    plan_dir = repo / ".planning"
    plan_dir.mkdir(exist_ok=True)
    plan_path = plan_dir / "PLAN.md"
    plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return plan_path


def _commit_all(repo: Path, msg: str) -> None:
    _git(["add", "-A"], repo)
    _git(["commit", "-m", msg], repo)


def _commit_empty(repo: Path, msg: str) -> None:
    _git(["commit", "--allow-empty", "-m", msg], repo)


def _supersede_body(cid: str, new_hash: str, invalidated: list[str]) -> str:
    """A superseding-commit message: title + Kata-Supersede then Kata-Invalidated
    lines (invalidated lines BELOW the supersede line — R1a intra-body order)."""
    trailer = [f"Kata-Supersede: {cid}@{new_hash}"]
    trailer += [f"Kata-Invalidated: {task}" for task in invalidated]
    return f"supersede {cid}\n\n" + "\n".join(trailer)


# ============================================================================
# pinned_contracts
# ============================================================================


def test_pinned_contracts_happy():
    ba = {"T2": [f"C1@{_HX}"], "T3": [f"C1@{_HX}", f"C2@{_HX}"]}
    assert cg.pinned_contracts(ba) == {"C1": _HX, "C2": _HX}


def test_pinned_contracts_empty_is_vacuous():
    assert cg.pinned_contracts({}) == {}


def test_pinned_contracts_raises_on_conflicting_pins():
    # One contract, one pin (M1-L1): two tasks pinning C1 to different hashes RAISE.
    ba = {"T2": ["C1@deadbeefcafe1234"], "T3": ["C1@0123456789abcdef"]}
    with pytest.raises(ValueError):
        cg.pinned_contracts(ba)


def test_pinned_contracts_raises_on_malformed_edge():
    with pytest.raises(ValueError):
        cg.pinned_contracts({"T2": ["C1_no_hash"]})


# ============================================================================
# verify_contract_gate
# ============================================================================


def test_verify_vacuous_bc_empty_edges(tmp_path):
    # BC: no builds_against ⇒ vacuous pass, no scan needed.
    repo = _make_repo(tmp_path)
    plan = _write_plan(repo, {})
    _commit_all(repo, "freeze")
    got = cg.verify_contract_gate(str(repo), "integration", {}, str(plan))
    assert got == {"passed": True, "vacuous": True, "findings": []}


def test_verify_body_fill_passes(tmp_path):
    # A provider filling a stub body leaves the surface unchanged ⇒ no supersede
    # needed ⇒ gate passes (M1-L8).
    repo = _make_repo(tmp_path)
    cdir = _write_contract(repo, "c1", _STUB)
    pin = ce.surface_hash(str(cdir))
    plan = _write_plan(repo, {"T2": [f"c1@{pin}"]})
    _commit_all(repo, "freeze: stub + plan")
    _write_contract(repo, "c1", _FILLED)  # fill body, surface unchanged
    _commit_all(repo, "feat: fill c1 body\n\nKata-Task: T1")
    got = cg.verify_contract_gate(str(repo), "integration", {"T2": [f"c1@{pin}"]}, str(plan))
    assert got["passed"] is True and got["vacuous"] is False and got["findings"] == []


def test_verify_drift_without_supersede_fails(tmp_path):
    # An interface edit with NO Kata-Supersede trailer ⇒ unauthorized-surface-drift.
    repo = _make_repo(tmp_path)
    cdir = _write_contract(repo, "c1", _STUB)
    pin = ce.surface_hash(str(cdir))
    ba = {"T2": [f"c1@{pin}"]}
    plan = _write_plan(repo, ba)
    _commit_all(repo, "freeze")
    _write_contract(repo, "c1", _S1)  # SURFACE changed, no supersede trailer
    _commit_all(repo, "chore: sneaky surface edit")
    got = cg.verify_contract_gate(str(repo), "integration", ba, str(plan))
    assert got["passed"] is False
    assert {"kind": "unauthorized-surface-drift", "detail": "c1"} in got["findings"]


def test_verify_drift_with_newest_supersede_and_full_coverage_passes(tmp_path):
    # An authorized surface change: Kata-Supersede: c1@<new> whose hash == the new
    # surface, AND a Kata-Invalidated for every dependent in the SAME commit ⇒ pass.
    # (Covers both drift-with-newest-supersede AND full-coverage-at-route-time.)
    repo = _make_repo(tmp_path)
    cdir = _write_contract(repo, "c1", _STUB)
    pin = ce.surface_hash(str(cdir))
    ba = {"T2": [f"c1@{pin}"]}
    plan = _write_plan(repo, ba)
    _commit_all(repo, "freeze")
    _write_contract(repo, "c1", _S1)
    new_hash = ce.surface_hash(str(cdir))
    _commit_all(repo, _supersede_body("c1", new_hash, ["T2"]))
    got = cg.verify_contract_gate(str(repo), "integration", ba, str(plan))
    assert got["passed"] is True and got["findings"] == []


def test_verify_unknown_supersede_id(tmp_path):
    # obligation (i): a supersede id absent from the pinned set has an empty
    # invalidation_set and would be vacuously "fully covered" — flag it.
    repo = _make_repo(tmp_path)
    cdir = _write_contract(repo, "c1", _STUB)
    pin = ce.surface_hash(str(cdir))
    ba = {"T2": [f"c1@{pin}"]}
    plan = _write_plan(repo, ba)
    _commit_all(repo, "freeze")
    _commit_empty(repo, f"chore: typo supersede\n\nKata-Supersede: cX@{_HX}")
    got = cg.verify_contract_gate(str(repo), "integration", ba, str(plan))
    assert got["passed"] is False
    assert {"kind": "unknown-supersede-id", "detail": "cX"} in got["findings"]


def test_verify_coverage_gap_fails(tmp_path):
    # An authorized surface change that FAILS to invalidate a dependent ⇒ gap.
    repo = _make_repo(tmp_path)
    cdir = _write_contract(repo, "c1", _STUB)
    pin = ce.surface_hash(str(cdir))
    ba = {"T2": [f"c1@{pin}"]}
    plan = _write_plan(repo, ba)
    _commit_all(repo, "freeze")
    _write_contract(repo, "c1", _S1)
    new_hash = ce.surface_hash(str(cdir))
    _commit_all(repo, _supersede_body("c1", new_hash, []))  # NO Kata-Invalidated
    got = cg.verify_contract_gate(str(repo), "integration", ba, str(plan))
    assert got["passed"] is False
    assert {"kind": "invalidation-coverage-gap", "detail": "c1:T2"} in got["findings"]


def test_verify_double_supersede_round1_only_fails_temporal(tmp_path):
    # F7 temporal: a stale round-1 invalidation cannot cover a round-2 supersede.
    repo = _make_repo(tmp_path)
    cdir = _write_contract(repo, "c1", _STUB)
    pin = ce.surface_hash(str(cdir))
    ba = {"T2": [f"c1@{pin}"]}
    plan = _write_plan(repo, ba)
    _commit_all(repo, "freeze")
    # round 1 — surface S1, supersede + invalidate T2 (older commit)
    _write_contract(repo, "c1", _S1)
    h1 = ce.surface_hash(str(cdir))
    _commit_all(repo, _supersede_body("c1", h1, ["T2"]))
    # round 2 — surface S2, supersede ONLY (newer commit; T2 NOT re-invalidated)
    _write_contract(repo, "c1", _S2)
    h2 = ce.surface_hash(str(cdir))
    _commit_all(repo, _supersede_body("c1", h2, []))
    got = cg.verify_contract_gate(str(repo), "integration", ba, str(plan))
    assert got["passed"] is False
    assert {"kind": "invalidation-coverage-gap", "detail": "c1:T2"} in got["findings"]


def test_verify_r1a_same_body_any_order_passes(tmp_path):
    # R1a: supersede + its covering invalidation in ONE commit body, with the
    # Kata-Invalidated line BELOW the Kata-Supersede line — intra-body order is
    # irrelevant (only commit_index matters).
    repo = _make_repo(tmp_path)
    cdir = _write_contract(repo, "c1", _STUB)
    pin = ce.surface_hash(str(cdir))
    ba = {"T2": [f"c1@{pin}"]}
    plan = _write_plan(repo, ba)
    _commit_all(repo, "freeze")
    _write_contract(repo, "c1", _S1)
    new_hash = ce.surface_hash(str(cdir))
    # _supersede_body puts the invalidated line strictly below the supersede line.
    _commit_all(repo, _supersede_body("c1", new_hash, ["T2"]))
    got = cg.verify_contract_gate(str(repo), "integration", ba, str(plan))
    assert got["passed"] is True and got["findings"] == []


def test_verify_r1b_separate_older_commit_fails(tmp_path):
    # R1b: an invalidation in a separate, immediately-OLDER commit does NOT cover a
    # newer supersede (commit_index of the invalidation > that of the supersede).
    repo = _make_repo(tmp_path)
    cdir = _write_contract(repo, "c1", _STUB)
    pin = ce.surface_hash(str(cdir))
    ba = {"T2": [f"c1@{pin}"]}
    plan = _write_plan(repo, ba)
    _commit_all(repo, "freeze")
    # older commit — invalidation only
    _commit_empty(repo, "chore: premature invalidate\n\nKata-Invalidated: T2")
    # newer commit — the supersede (no invalidation here)
    _write_contract(repo, "c1", _S1)
    new_hash = ce.surface_hash(str(cdir))
    _commit_all(repo, _supersede_body("c1", new_hash, []))
    got = cg.verify_contract_gate(str(repo), "integration", ba, str(plan))
    assert got["passed"] is False
    assert {"kind": "invalidation-coverage-gap", "detail": "c1:T2"} in got["findings"]


def test_verify_no_catch_propagates_scan_raise(tmp_path):
    # obligation (iii): an unresolvable fork-point raise from the scan PROPAGATES
    # out of verify_contract_gate — never caught-and-continued to a permissive pass.
    repo = _make_repo(tmp_path)
    cdir = _write_contract(repo, "c1", _STUB)
    pin = ce.surface_hash(str(cdir))
    ba = {"T2": [f"c1@{pin}"]}
    _commit_all(repo, "freeze")
    # An uncommitted plan path ⇒ unresolvable fork-point ⇒ ValueError.
    ghost = repo / ".planning" / "GHOST.md"
    ghost.parent.mkdir(exist_ok=True)
    ghost.write_text("# never committed\n", encoding="utf-8")
    with pytest.raises(ValueError):
        cg.verify_contract_gate(str(repo), "integration", ba, str(ghost))


# ============================================================================
# _scan_integration_commits — gate-semantics raises
# ============================================================================


def test_scan_raises_on_unresolvable_fork_point(tmp_path):
    # R8: the frozen PLAN is not in the branch's history ⇒ RAISE (never fall back to
    # an unbounded audit that could read prior-run trailers).
    repo = _make_repo(tmp_path)
    _write_plan(repo, {"T2": [f"c1@{_HX}"]})
    _commit_all(repo, "freeze")
    ghost = repo / ".planning" / "GHOST.md"
    ghost.write_text("# never committed\n", encoding="utf-8")
    with pytest.raises(ValueError):
        cg._scan_integration_commits(str(repo), "integration", str(ghost))


def test_scan_raises_on_git_error(tmp_path):
    # A nonexistent branch is a git error ⇒ RAISE (fail-closed).
    repo = _make_repo(tmp_path)
    plan = _write_plan(repo, {"T2": [f"c1@{_HX}"]})
    _commit_all(repo, "freeze")
    with pytest.raises(ValueError):
        cg._scan_integration_commits(str(repo), "no-such-branch", str(plan))


# ============================================================================
# dangling_contract_imports
# ============================================================================


def test_dangling_caught_raw_module_form(tmp_path):
    # `from contracts.c1.iface import X` names the raw module contracts.c1.iface;
    # with iface.py deleted (only __init__.py present) ⇒ a dangler.
    _write_contract(tmp_path, "c1", "def foo():\n    ...\n")  # __init__.py only
    (tmp_path / "test_dep.py").write_text(
        "from contracts.c1.iface import X\n\ndef test_x():\n    X()\n", encoding="utf-8"
    )
    got = cg.dangling_contract_imports(["test_dep.py"], tmp_path)
    assert got == [{"file": "test_dep.py", "import": "contracts.c1.iface"}]


def test_dangling_r2a_clean_when_base_module_resolves(tmp_path):
    # R2a: `from contracts.c1 import iface` with iface.py + __init__.py present ⇒
    # the base module contracts.c1 resolves ⇒ clean.
    d = _write_contract(tmp_path, "c1", "def foo():\n    ...\n")
    (d / "iface.py").write_text("def X():\n    ...\n", encoding="utf-8")
    (tmp_path / "test_dep.py").write_text(
        "from contracts.c1 import iface\n\ndef test_x():\n    iface.X()\n", encoding="utf-8"
    )
    assert cg.dangling_contract_imports(["test_dep.py"], tmp_path) == []


def test_dangling_r2b_documented_residual(tmp_path):
    # R2b (DOCUMENTED RESIDUAL, not a bug): a deleted submodule behind a surviving
    # __init__.py, referenced via the base-module form `from contracts.c1 import
    # iface`, is INVISIBLE to this scan — contracts.c1 resolves via __init__.py, and
    # from-import NAMES are never expanded (R2). The full-suite re-run's ImportError
    # is the behavioral backstop. This test pins the known gap so it is visible.
    _write_contract(tmp_path, "c1", "def foo():\n    ...\n")  # __init__.py only; iface.py deleted
    (tmp_path / "test_dep.py").write_text(
        "from contracts.c1 import iface\n\ndef test_x():\n    iface.X()\n", encoding="utf-8"
    )
    assert cg.dangling_contract_imports(["test_dep.py"], tmp_path) == []  # residual: unseen here


def test_dangling_ignores_non_contract_import(tmp_path):
    # An unresolved import OUTSIDE the contracts/ namespace is not this gate's
    # concern (a provider/dependent's own tree) — ignored.
    (tmp_path / "test_dep.py").write_text(
        "from some.other.module import Thing\n", encoding="utf-8"
    )
    assert cg.dangling_contract_imports(["test_dep.py"], tmp_path) == []


def test_dangling_raises_on_unreadable_dependent(tmp_path):
    with pytest.raises(OSError):
        cg.dangling_contract_imports(["does_not_exist.py"], tmp_path)


# ============================================================================
# expand_ownership_paths
# ============================================================================


def test_expand_ownership_dir_expansion_and_contract_exclusion_f5(tmp_path):
    # F5: expanding provider ownership while EXCLUDING the contract dirs keeps the
    # provider-owned contract itself OUT of the edge-honesty forbidden set, so an
    # honest contract-only dependent yields EMPTY violations.
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "provider.py").write_text("def bar():\n    return 1\n", encoding="utf-8")
    _write_contract(tmp_path, "c1", "def foo():\n    ...\n")
    (tmp_path / "test_dep.py").write_text(
        "from contracts.c1 import foo\n\ndef test_x():\n    foo()\n", encoding="utf-8"
    )
    expanded = cg.expand_ownership_paths(
        ["src", "contracts/c1"], tmp_path, exclude_prefixes=("contracts/c1",)
    )
    assert expanded == ["src/provider.py"]  # contract dir excluded
    # The honest dependent imports only the contract surface ⇒ zero violations.
    assert ce.edge_honesty(["test_dep.py"], expanded, tmp_path) == []


def test_expand_ownership_raises_on_missing_path(tmp_path):
    with pytest.raises(ValueError):
        cg.expand_ownership_paths(["nope_dir"], tmp_path)


def test_expand_ownership_prefix_boundary_c1_c10(tmp_path):
    # R10: `contracts/C1/` must never exclude `contracts/C10/...` (trailing-slash
    # normalized prefix match).
    _write_contract(tmp_path, "C1", "def a():\n    ...\n")
    _write_contract(tmp_path, "C10", "def b():\n    ...\n")
    expanded = cg.expand_ownership_paths(
        ["contracts/C1", "contracts/C10"], tmp_path, exclude_prefixes=("contracts/C1",)
    )
    assert expanded == ["contracts/C10/__init__.py"]


def test_expand_ownership_passthrough_file_entry(tmp_path):
    (tmp_path / "solo.py").write_text("x = 1\n", encoding="utf-8")
    assert cg.expand_ownership_paths(["solo.py"], tmp_path) == ["solo.py"]


# ============================================================================
# write_contract_gate — artifact round-trip (all three check results)
# ============================================================================


def test_write_contract_gate_artifact_round_trip(tmp_path):
    kata_dir = tmp_path / ".kata"
    verdict = {
        "passed": False,
        "vacuous": False,
        "findings": [{"kind": "invalidation-coverage-gap", "detail": "c1:T2"}],
        "branch": "integration",
        "surviving_stubs": ["contracts/c1/__init__.py"],
        "danglers": [{"file": "test_dep.py", "import": "contracts.c1.iface"}],
    }
    out = cg.write_contract_gate(kata_dir, verdict)
    assert out == kata_dir / "contract-gate.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    # All THREE final-gate checks are carried in the durable artifact (F4).
    assert data["passed"] is False
    assert data["findings"] == [{"kind": "invalidation-coverage-gap", "detail": "c1:T2"}]
    assert data["surviving_stubs"] == ["contracts/c1/__init__.py"]
    assert data["danglers"] == [{"file": "test_dep.py", "import": "contracts.c1.iface"}]
    assert data["branch"] == "integration"
    assert "utc" in data  # write-time stamp


def test_write_contract_gate_vacuous_pass_still_emitted(tmp_path):
    # The artifact is written even on a (vacuous) pass — its ABSENCE is the
    # evaluator's signal (F4).
    kata_dir = tmp_path / ".kata"
    out = cg.write_contract_gate(
        kata_dir,
        {"passed": True, "vacuous": True, "findings": [], "branch": "integration",
         "surviving_stubs": [], "danglers": []},
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["passed"] is True and data["vacuous"] is True


# ============================================================================
# parse_trailer_events — malformed trailer surfaced (R7 parity, not swallowed)
# ============================================================================


def test_parse_trailer_events_surfaces_malformed_supersede(tmp_path, capsys):
    repo = _make_repo(tmp_path)
    plan = _write_plan(repo, {"T2": [f"c1@{_HX}"]})
    _commit_all(repo, "freeze")
    _commit_empty(repo, "chore: bad trailer\n\nKata-Supersede: c1@NOTHEX")
    events = cg.parse_trailer_events(str(repo), "integration", str(plan))
    # The malformed line is NOT a supersede event (grammar failed) ...
    assert all(kind != "supersede" for (_i, kind, _id, _h) in events)
    # ... but it is surfaced loudly, never silently swallowed.
    assert "malformed Kata-Supersede" in capsys.readouterr().out


# --- Sweep fold (2026-07-02): C1, C2, C4, C5 ---------------------------------

def test_dangling_bare_contracts_namespace_import_is_clean(tmp_path):
    # Sweep C1: `from contracts import c1` / `import contracts` resolve at
    # runtime as a PEP-420 namespace package — never a dangler while the
    # contracts/ dir exists.
    (tmp_path / "contracts" / "c1").mkdir(parents=True)
    (tmp_path / "contracts" / "c1" / "__init__.py").write_text("def foo(): ...\n", encoding="utf-8")
    (tmp_path / "dep.py").write_text("from contracts import c1\nimport contracts\n", encoding="utf-8")
    assert cg.dangling_contract_imports(["dep.py"], tmp_path) == []


def test_dangling_bare_contracts_flagged_when_dir_gone(tmp_path):
    # ...but with the contracts/ dir entirely absent, the bare import IS a dangler.
    (tmp_path / "dep.py").write_text("import contracts\n", encoding="utf-8")
    got = cg.dangling_contract_imports(["dep.py"], tmp_path)
    assert got == [{"file": "dep.py", "import": "contracts"}]


def test_verify_pin_revert_after_supersede_is_drift(tmp_path):
    # Sweep C2 (mutation pin for the R3 rule): after a supersede with FULL
    # coverage, a provider reverting the surface back to the ORIGINAL PIN must
    # be unauthorized-surface-drift — the pin branch is closed for superseded
    # contracts at the final gate.
    repo = _make_repo(tmp_path)
    _write_contract(repo, "c1", "def foo(x):\n    ...\n")
    pin = ce.surface_hash(str(repo / "contracts" / "c1"))
    plan = _write_plan(repo, {"D1": [f"c1@{pin}"]})
    _commit_all(repo, "chore: freeze PLAN")
    # supersede to a new surface, full coverage at route time
    _write_contract(repo, "c1", "def foo(x, y):\n    ...\n")
    new_hash = ce.surface_hash(str(repo / "contracts" / "c1"))
    _commit_all(repo, f"feat: supersede c1\n\nKata-Supersede: c1@{new_hash}\nKata-Invalidated: D1")
    # provider REVERTS the surface back to the pre-supersede pin (uncommitted tree state)
    _write_contract(repo, "c1", "def foo(x):\n    ...\n")
    verdict = cg.verify_contract_gate(
        str(repo), "integration", {"D1": [f"c1@{pin}"]}, str(plan)
    )
    assert verdict["passed"] is False
    assert {"kind": "unauthorized-surface-drift", "detail": "c1"} in verdict["findings"]


def test_pinned_contracts_rejects_dot_only_id():
    # Sweep C4: "." / ".." pass the edge grammar but escape contracts/ as paths.
    with pytest.raises(ValueError, match="degenerate contract id"):
        cg.pinned_contracts({"T1": ["..@deadbeefcafe1234"]})
    with pytest.raises(ValueError, match="degenerate contract id"):
        cg.pinned_contracts({"T1": [".@deadbeefcafe1234"]})


def test_parse_trailer_events_surfaces_malformed_invalidated(tmp_path, capsys):
    # Sweep C5: the malformed-Kata-Invalidated NOTE branch (under-dispatch
    # visibility) — previously unpinned; deleting it must go red here.
    repo = _make_repo(tmp_path)
    plan = _write_plan(repo, {"D1": ["c1@deadbeefcafe1234"]})
    _commit_all(repo, "chore: freeze PLAN")
    _commit_empty(repo, "chore: x\n\nKata-Invalidated:")
    cg.parse_trailer_events(str(repo), "integration", str(plan))
    out = capsys.readouterr().out
    assert "malformed" in out.lower() and "Kata-Invalidated" in out


# ============================================================================
# DET-02 / DET-03 (2026-07-12 health review) — git-config pins on parsed stdout
# ============================================================================


def _pin_present(cmd: list[str], setting: str) -> bool:
    """True iff ``-c <setting>`` appears in *cmd* (the pinned-argv shape)."""
    return any(cmd[i] == "-c" and cmd[i + 1] == setting for i in range(len(cmd) - 1))


def test_scan_integration_commits_argv_pins(tmp_path, monkeypatch):
    """DET-02: fork-point resolution (single-pathspec `git log -1`) must pin
    log.follow=false — operator log.follow=true follows renames to an OLDER
    commit, a wrong fork point that ingests prior-run trailers — plus
    log.showSignature=false (gpg: lines corrupt the parsed %H) and
    core.quotepath=off. DET-03: the commit-delimited scan must pin
    log.showSignature=false (gpg: lines silently shift commit_index — the
    temporal-invalidation comparison would misread commit order)."""
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if "-1" in cmd:  # fork-point resolution
            return subprocess.CompletedProcess(cmd, 0, stdout="abc123\n", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(cg.subprocess, "run", fake_run)
    cg._scan_integration_commits(str(tmp_path), "integration", tmp_path / "PLAN.md")

    assert len(calls) == 2, "expected exactly fork-point + bounded-scan git calls"
    fork_cmd, scan_cmd = calls
    assert fork_cmd[0] == "git" and scan_cmd[0] == "git"
    assert _pin_present(fork_cmd, "log.follow=false")
    assert _pin_present(fork_cmd, "log.showSignature=false")
    assert _pin_present(fork_cmd, "core.quotepath=off")
    assert _pin_present(scan_cmd, "log.showSignature=false")
    assert _pin_present(scan_cmd, "core.quotepath=off")


# ============================================================================
# Q-16 (2026-07-12 health review) — git timeout fails closed (RAISE, not pass)
# ============================================================================


def test_scan_forkpoint_timeout_raises(tmp_path, monkeypatch):
    """Q-16: a hung fork-point resolution ⇒ ValueError (fail-closed) — the final
    gate never swallows a timeout into a permissive unbounded/empty scan."""
    def fake_run(cmd, **kwargs):
        if "-1" in cmd:
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=cg._GIT_TIMEOUT_S)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(cg.subprocess, "run", fake_run)
    with pytest.raises(ValueError):
        cg._scan_integration_commits(str(tmp_path), "integration", tmp_path / "PLAN.md")


def test_scan_bounded_timeout_raises(tmp_path, monkeypatch):
    """Q-16: a hung bounded commit scan (fork-point resolves) ⇒ ValueError
    (fail-closed) — never a permissive empty commit list."""
    def fake_run(cmd, **kwargs):
        if "-1" in cmd:  # fork-point resolves
            return subprocess.CompletedProcess(cmd, 0, stdout="abc123\n", stderr="")
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=cg._GIT_TIMEOUT_S)

    monkeypatch.setattr(cg.subprocess, "run", fake_run)
    with pytest.raises(ValueError):
        cg._scan_integration_commits(str(tmp_path), "integration", tmp_path / "PLAN.md")
