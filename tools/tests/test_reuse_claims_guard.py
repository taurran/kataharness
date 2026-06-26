"""T3 regression tests for the reuse-claims guard (LD5).

Exercises `validate_skills.check_reuse_claims_pointers` (dual-mechanism pointer
presence check) and the `check_protocol_schemas` entry for `reuse-claims.md`
(contract-body integrity), both added in T3.

All tests call the real validator functions (imported from validate_skills).
No rule is re-implemented here; fixtures and monkeypatching supply the
controlled inputs so the validator function itself is the thing under test.

Coverage required by LD5 / T3 acceptance criteria:
1. present → passes (pointer presence + contract-body, real tree)
2. each of the THREE pointers removed individually → error
   (a) kata-design-doc body missing pointer
   (b) kata-tdd body missing pointer
   (c) kata-plan/RUBRIC.md missing pointer (separate-glob path)
3. contract-body term removed → error
"""

from pathlib import Path

import validate_skills as v

POINTER = "protocol/reuse-claims.md"
# LD3 load-bearing terms as they appear verbatim in protocol/reuse-claims.md (the contract is
# reflowed so the full phrase stays on one line, m5).
LD3_TERMS = ["claim to verify, not an assumption", "NEW capability", "documentation-only seam"]


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _skill(name: str, body: str, tmp_path: Path) -> v.Skill:
    """Minimal Skill object for unit-testing check_reuse_claims_pointers."""
    category = "plan" if name == "kata-design-doc" else "execute"
    d = tmp_path / category / name
    d.mkdir(parents=True, exist_ok=True)
    return v.Skill(name=name, dir=d, frontmatter={}, body=body)


def _both_skills_with_pointer(tmp_path: Path) -> list[v.Skill]:
    """Return kata-design-doc and kata-tdd skills whose bodies contain the pointer."""
    return [
        _skill("kata-design-doc", f"body with {POINTER} here", tmp_path),
        _skill("kata-tdd", f"body with {POINTER} here", tmp_path),
    ]


def _make_rubric_skills_dir(tmp_path: Path, *, include_pointer: bool) -> Path:
    """Write a kata-plan/RUBRIC.md fixture under tmp_path/skills and return that path.

    When include_pointer=True the RUBRIC contains the pointer; False omits it.
    The returned path is suitable for monkeypatching v.SKILLS_DIR.
    """
    rubric_dir = tmp_path / "skills" / "plan" / "kata-plan"
    rubric_dir.mkdir(parents=True, exist_ok=True)
    content = (
        f"Quality bar: {POINTER} applies here."
        if include_pointer
        else "Quality bar: (pointer removed for test)."
    )
    (rubric_dir / "RUBRIC.md").write_text(content, encoding="utf-8")
    return tmp_path / "skills"


# ---------------------------------------------------------------------------
# 1. present → passes (real tree)
# ---------------------------------------------------------------------------

def test_real_tree_pointer_presence_passes():
    """All three real-tree pointers present → check_reuse_claims_pointers returns no findings."""
    skills = v.load_skills()
    findings = v.check_reuse_claims_pointers(skills)
    assert findings == [], f"real tree must have no pointer findings; got {findings}"


def test_real_tree_contract_body_passes():
    """Real protocol/reuse-claims.md has all three LD3 terms → check_protocol_schemas clean."""
    findings = v.check_protocol_schemas([])
    reuse_findings = [f for f in findings if "reuse-claims.md" in f.where]
    assert reuse_findings == [], f"expected no reuse-claims.md errors; got {reuse_findings}"


def test_reuse_claims_in_required_protocol():
    """reuse-claims.md is registered in REQUIRED_PROTOCOL with all three LD3 terms."""
    assert "reuse-claims.md" in v.REQUIRED_PROTOCOL, "reuse-claims.md must be in REQUIRED_PROTOCOL"
    registered = v.REQUIRED_PROTOCOL["reuse-claims.md"]
    for term in LD3_TERMS:
        assert term in registered, f"REQUIRED_PROTOCOL['reuse-claims.md'] must include {term!r}"


# ---------------------------------------------------------------------------
# 2a. kata-design-doc pointer removed → error (skill-body path)
# ---------------------------------------------------------------------------

def test_kata_design_doc_pointer_missing_errors(tmp_path, monkeypatch):
    """Removing the pointer from kata-design-doc's body → ERROR from check_reuse_claims_pointers."""
    skills = [
        _skill("kata-design-doc", "body WITHOUT the pointer here", tmp_path),  # missing
        _skill("kata-tdd", f"body with {POINTER} here", tmp_path),
    ]
    # Supply a good RUBRIC so only the kata-design-doc error fires.
    skills_dir = _make_rubric_skills_dir(tmp_path, include_pointer=True)
    monkeypatch.setattr(v, "SKILLS_DIR", skills_dir)

    findings = v.check_reuse_claims_pointers(skills)

    assert any(
        f.level == "ERROR" and "kata-design-doc" in f.where
        for f in findings
    ), f"expected ERROR for kata-design-doc missing pointer; got {findings}"


# ---------------------------------------------------------------------------
# 2b. kata-tdd pointer removed → error (skill-body path)
# ---------------------------------------------------------------------------

def test_kata_tdd_pointer_missing_errors(tmp_path, monkeypatch):
    """Removing the pointer from kata-tdd's body → ERROR from check_reuse_claims_pointers."""
    skills = [
        _skill("kata-design-doc", f"body with {POINTER} here", tmp_path),
        _skill("kata-tdd", "body WITHOUT the pointer here", tmp_path),  # missing
    ]
    skills_dir = _make_rubric_skills_dir(tmp_path, include_pointer=True)
    monkeypatch.setattr(v, "SKILLS_DIR", skills_dir)

    findings = v.check_reuse_claims_pointers(skills)

    assert any(
        f.level == "ERROR" and "kata-tdd" in f.where
        for f in findings
    ), f"expected ERROR for kata-tdd missing pointer; got {findings}"


# ---------------------------------------------------------------------------
# 2c. kata-plan/RUBRIC.md pointer removed → error (separate-glob path)
# ---------------------------------------------------------------------------

def test_kata_plan_rubric_pointer_missing_errors(tmp_path, monkeypatch):
    """Removing the pointer from kata-plan/RUBRIC.md → ERROR (separate file read, not a loaded skill)."""
    skills = _both_skills_with_pointer(tmp_path)
    # RUBRIC is written without the pointer; skills have it → only the RUBRIC error fires.
    skills_dir = _make_rubric_skills_dir(tmp_path, include_pointer=False)
    monkeypatch.setattr(v, "SKILLS_DIR", skills_dir)

    findings = v.check_reuse_claims_pointers(skills)

    assert any(
        f.level == "ERROR" and "kata-plan" in f.where
        for f in findings
    ), f"expected ERROR for kata-plan/RUBRIC.md missing pointer; got {findings}"


# ---------------------------------------------------------------------------
# 2d. a producer skill ABSENT entirely → error (m4: default-FAIL, never silently stop enforcing)
# ---------------------------------------------------------------------------

def test_real_tree_producers_exist_passes():
    """The real tree has both producer skills → check_reuse_claims_producers_exist is clean."""
    assert v.check_reuse_claims_producers_exist(v.load_skills()) == []


def test_absent_producer_skill_errors(tmp_path, monkeypatch):
    """If a producer skill (e.g. kata-tdd) is missing from the tree, the existence guard must
    ERROR loudly rather than let the content-check silently stop enforcing (m4 / L12c)."""
    # A SKILLS_DIR that has kata-design-doc but NOT kata-tdd.
    skills_dir = tmp_path / "skills"
    (skills_dir / "plan" / "kata-design-doc").mkdir(parents=True)
    (skills_dir / "plan" / "kata-design-doc" / "SKILL.md").write_text("x", encoding="utf-8")
    monkeypatch.setattr(v, "SKILLS_DIR", skills_dir)

    findings = v.check_reuse_claims_producers_exist([])

    assert any(
        f.level == "ERROR" and "kata-tdd" in f.where
        for f in findings
    ), f"expected ERROR for absent producer skill kata-tdd; got {findings}"


# ---------------------------------------------------------------------------
# 3. contract-body term removed → error
# ---------------------------------------------------------------------------

def test_contract_body_term_missing_errors(tmp_path, monkeypatch):
    """Removing a LD3 load-bearing term from reuse-claims.md → check_protocol_schemas ERROR."""
    proto_dir = tmp_path / "protocol"
    proto_dir.mkdir()
    # Write a reuse-claims.md that has the other two terms but is MISSING "documentation-only seam".
    (proto_dir / "reuse-claims.md").write_text(
        "claim to verify, not an assumption\nNEW capability\n(seam line intentionally absent)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(v, "PROTOCOL_DIR", proto_dir)
    # Patch REQUIRED_PROTOCOL so only reuse-claims.md terms are checked (avoid errors for absent
    # sibling files in the fixture proto_dir that don't exist here).
    patched = {"reuse-claims.md": list(LD3_TERMS)}
    monkeypatch.setattr(v, "REQUIRED_PROTOCOL", patched)

    findings = v.check_protocol_schemas([])

    errors = [f for f in findings if "reuse-claims.md" in f.where]
    assert any("documentation-only seam" in f.msg for f in errors), (
        f"expected ERROR for missing 'documentation-only seam'; got {errors}"
    )
