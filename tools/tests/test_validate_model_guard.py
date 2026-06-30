"""Tests for the A1 re-introduction guard: validate_skills.py must ERROR on any
absolute model: key in SKILL.md frontmatter (DESIGN §3 A1, R8, PLAN W1-B).

Scope (R8):
- skills/**/SKILL.md and modules/**/SKILL.md  →  hard ERROR (guard fires)
- adapters/**                                 →  guard must NOT fire (allowed negative case)
- config / JSON                               →  out of scope (not loaded by validate_skills)

TDD order: these tests are written BEFORE check_model_in_skill_frontmatter exists,
so they fail until the guard is implemented.
"""
from __future__ import annotations

import validate_skills as v


# ── helpers ──────────────────────────────────────────────────────────────────


def _core_skill(name: str, category: str, fm_extra: dict, tmp_path) -> v.Skill:
    """Build a minimal conformant core Skill with optional extra frontmatter entries."""
    skill_dir = tmp_path / category / name
    skill_dir.mkdir(parents=True)
    fm: dict = {
        "name": name,
        "description": "Fixture skill for model-guard test.",
        "license": "Apache-2.0",
        "version": "0.1.0",
        "category": category,
        "status": "experimental",
        "agnostic": True,
        "cost-weight": 2,
        "allowed-tools": ["Read", "Grep"],
        "tags": [f"kata/{category}", "kata/spine"],
        **fm_extra,
    }
    return v.Skill(name=name, dir=skill_dir, frontmatter=fm, body="")


def _adapter_skill(name: str, tmp_path) -> v.Skill:
    """Build a Skill whose dir is under adapters/claude/ — guard must NOT fire here."""
    skill_dir = tmp_path / "adapters" / "claude" / name
    skill_dir.mkdir(parents=True)
    fm: dict = {
        "name": name,
        "description": "Adapter fixture — may pin a model.",
        "license": "Apache-2.0",
        "version": "0.1.0",
        "category": "execute",
        "status": "experimental",
        "agnostic": False,   # adapters are allowed to be non-agnostic
        "cost-weight": 2,
        "allowed-tools": ["Read"],
        "tags": ["kata/execute", "kata/spine"],
        "model": "opus",     # ALLOWED inside adapters/
    }
    return v.Skill(name=name, dir=skill_dir, frontmatter=fm, body="")


# ── positive case: model: in core SKILL.md → hard ERROR ──────────────────────


def test_model_key_in_core_skill_is_error(tmp_path):
    """A planted model: opus in a core skills/** SKILL.md must produce a hard ERROR
    with a clear, actionable message pointing to dispatch-time resolution (A1 / R8)."""
    skill = _core_skill("kata-test", "plan", {"model": "opus"}, tmp_path)
    findings = v.check_model_in_skill_frontmatter([skill])
    errors = [f for f in findings if f.level == "ERROR"]
    assert errors, (
        "expected at least one ERROR for model: in core SKILL.md frontmatter; got no findings"
    )
    # Message must be actionable: reference dispatch-time resolution so the author knows what to do.
    assert any(
        "dispatch" in f.msg.lower() or "resolve" in f.msg.lower()
        for f in errors
    ), f"ERROR message must reference dispatch-time resolution; got: {[f.msg for f in errors]}"
    # Where must identify the skill directory name.
    assert any("kata-test" in f.where for f in errors), (
        f"finding must name the offending skill directory; got: {[f.where for f in errors]}"
    )


def test_model_key_arbitrary_value_in_core_skill_is_error(tmp_path):
    """The guard fires for any value of model:, not just opus."""
    for model_val in ("sonnet", "claude-opus-4-8", "haiku", "fable"):
        skill = _core_skill(f"kata-{model_val}", "plan", {"model": model_val}, tmp_path)
        findings = v.check_model_in_skill_frontmatter([skill])
        assert any(f.level == "ERROR" for f in findings), (
            f"model: {model_val!r} in core SKILL.md must produce an ERROR"
        )


def test_model_guard_fires_via_run_checks(tmp_path):
    """The model guard is wired into run_checks() — ERROR propagates end-to-end."""
    skill = _core_skill("kata-test", "plan", {"model": "sonnet"}, tmp_path)
    findings = v.run_checks([skill])
    assert any(
        f.level == "ERROR" and "model" in f.msg.lower()
        for f in findings
    ), f"run_checks must propagate the model guard ERROR; got {findings}"


def test_model_guard_is_registered_in_checks():
    """check_model_in_skill_frontmatter must be in CHECKS (auto-fires via run_checks)."""
    assert v.check_model_in_skill_frontmatter in v.CHECKS, (
        "check_model_in_skill_frontmatter must be registered in CHECKS via @check decorator"
    )


# ── negative case: model: under adapters/ must NOT fire ──────────────────────


def test_model_key_under_adapters_does_not_trigger_guard(tmp_path):
    """A model: pin in an adapters/** SKILL must NOT produce any finding.
    Adapters/config may still pin models (DESIGN §3 A1 / R8 explicit carve-out)."""
    skill = _adapter_skill("kata-claude-adapter", tmp_path)
    findings = v.check_model_in_skill_frontmatter([skill])
    assert findings == [], (
        f"guard must NOT fire for adapters/ skills; model: is allowed there; got {findings}"
    )


def test_model_key_absent_in_core_skill_passes(tmp_path):
    """A clean core SKILL.md with no model: key must produce zero model-guard findings."""
    skill = _core_skill("kata-clean", "plan", {}, tmp_path)
    findings = v.check_model_in_skill_frontmatter([skill])
    assert findings == [], f"no model: key should not trigger the guard; got {findings}"


def test_mixed_core_and_adapter_skills_only_core_flagged(tmp_path):
    """When core and adapter skills are mixed, only the core skill with model: is flagged."""
    core = _core_skill("kata-core", "plan", {"model": "opus"}, tmp_path)
    adapter = _adapter_skill("kata-claude-adapter", tmp_path)
    findings = v.check_model_in_skill_frontmatter([core, adapter])
    errors = [f for f in findings if f.level == "ERROR"]
    assert len(errors) == 1, f"exactly one ERROR expected (core skill only); got {errors}"
    assert "kata-core" in errors[0].where, (
        f"ERROR must name the core skill, not the adapter; got {errors[0].where}"
    )


# ── lock-test: guard scans every real SKILL.md (47/0 with guard active) ──────


def test_model_guard_zero_violations_in_real_tree():
    """Lock-test: check_model_in_skill_frontmatter over the full real skills + modules tree
    must produce ZERO findings.

    This test serves two purposes:
    1. Confirms the existing clean tree has no false positives (guard does not break 47/0).
    2. Proves that a planted violation anywhere in the real tree is caught — if a skill ever
       gains model: frontmatter the test fails immediately (the lock-test posture).
    """
    skills = v.load_skills()
    findings = v.check_model_in_skill_frontmatter(skills)
    assert findings == [], (
        f"real skill tree must have no model: in SKILL.md frontmatter; violations found:\n"
        + "\n".join(f"  {f.level}: {f.where}: {f.msg}" for f in findings)
    )


def test_model_guard_real_tree_skill_count():
    """The real tree must contain at least 47 skills — confirms the lock-test has meaningful coverage."""
    skills = v.load_skills()
    assert len(skills) >= 47, (
        f"expected ≥47 skills for full lock-test coverage; found only {len(skills)}"
    )


# ── FIX-3 NIT-1: case-insensitive model key detection ────────────────────────


def test_model_key_capitalized_is_caught(tmp_path):
    """A capitalized 'Model: opus' in a core SKILL.md frontmatter must produce a hard ERROR.

    YAML is case-sensitive, so 'Model' and 'model' are distinct keys. The guard
    must catch any capitalisation variant (model:/Model:/MODEL:) so that a trivial
    capitalisation change cannot bypass the A1 re-introduction guard (FIX-3 NIT-1).
    """
    skill = _core_skill("kata-capitalized", "plan", {"Model": "opus"}, tmp_path)
    findings = v.check_model_in_skill_frontmatter([skill])
    errors = [f for f in findings if f.level == "ERROR"]
    assert errors, (
        "expected at least one ERROR for capitalized 'Model: opus' in core SKILL.md; "
        "got no findings — the guard must match case-insensitively"
    )
    assert any("kata-capitalized" in f.where for f in errors), (
        f"finding must name the offending skill directory; got: {[f.where for f in errors]}"
    )
