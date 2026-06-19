from pathlib import Path

import validate_skills as v

FIXTURES = Path(__file__).parent / "fixtures"


def _skills_in(subdir: str) -> list[v.Skill]:
    return v.load_skills(FIXTURES / subdir)


def test_good_fixture_has_no_findings():
    findings = v.run_checks(_skills_in("good"))
    assert findings == [], f"expected clean, got {findings}"


def test_name_mismatch_is_an_error():
    findings = v.run_checks(_skills_in("bad-name"))
    assert any(f.level == "ERROR" and "name" in f.msg for f in findings)


def test_cost_weight_out_of_range_is_an_error():
    findings = v.run_checks(_skills_in("bad-cost"))
    assert any(f.level == "ERROR" and "cost-weight" in f.msg for f in findings)


def test_index_is_idempotent_under_regeneration():
    skills = _skills_in("good")
    use = {"kata-good": "does a good thing"}
    block = v._build_index(skills, use)
    # the generated block parses back to the same Use text
    assert v._parse_existing_use(block).get("kata-good") == "does a good thing"
    assert "| Cost |" in block


def test_protocol_schemas_present_on_real_tree():
    # check_protocol_schemas reads the real protocol/ dir, not fixtures
    findings = v.check_protocol_schemas([])
    assert findings == [], f"protocol schemas incomplete: {findings}"


def test_taxonomy_present_on_real_tree():
    assert v.check_taxonomy_present([]) == []


def test_unresolved_wikilink_is_an_error():
    findings = v.check_wikilinks(_skills_in("bad-link"))
    assert any("unresolved skill wikilink" in f.msg for f in findings)


def test_real_tree_wikilinks_all_resolve():
    assert v.check_wikilinks(v.load_skills()) == []


def test_real_tree_readme_in_sync():
    assert v.check_readme_sync(v.load_skills()) == []


def test_good_tier_skill_passes_tier_check():
    assert v.check_tier_family(_skills_in("good-tier")) == []


def test_tier_skill_missing_tag_and_rubric_errors():
    findings = v.check_tier_family(_skills_in("bad-tier"))
    assert any("kata/tier/standard" in f.msg for f in findings)
    assert any("RUBRIC.md" in f.msg for f in findings)


def test_config_schema_requires_runshape_and_target():
    from validate_skills import REQUIRED_PROTOCOL, check_protocol_schemas
    required = REQUIRED_PROTOCOL["config.md"]
    assert "runShape" in required and "target" in required
    # the real protocol/config.md must document them; check_protocol_schemas ignores its arg,
    # so pass []. Match on the stringified finding to avoid assuming the Finding field name.
    findings = check_protocol_schemas([])
    assert not any("config.md" in str(f) for f in findings), [str(f) for f in findings]


def test_a4_protocol_schemas_required():
    from validate_skills import REQUIRED_PROTOCOL, check_protocol_schemas
    assert {"id", "kind", "rank", "edge", "meta", "symKind"} <= set(REQUIRED_PROTOCOL["graph.md"])
    assert {"taskId", "decisionNeeded", "status", "kind"} <= set(REQUIRED_PROTOCOL["escalation.md"])
    assert "graph" in REQUIRED_PROTOCOL["config.md"]
    findings = [str(f) for f in check_protocol_schemas([])]
    assert not any("graph.md" in f or "escalation.md" in f for f in findings), findings


def test_d71_config_documents_grill_skip_rung():
    # protocol/config.md must wire the Priming-and-Grill dial incl. the new skip rung (D71).
    text = (v.REPO_ROOT / "protocol" / "config.md").read_text(encoding="utf-8")
    assert "Grill-depth dial" in text, "config.md must document the grill-depth dial (D71)"
    assert '"skip"' in text, "config.md must document the grill-skip rung value (D71)"


def test_d71_kata_defer_present_and_handoff_category():
    # kata-defer is the grill-skip autonomous-floor safety net (D71) + the no-drift parking valve (D42).
    skills = {s.name: s for s in v.load_skills()}
    assert "kata-defer" in skills, "kata-defer must exist (D71 floor safety net / D42 parking)"
    fm = skills["kata-defer"].frontmatter
    assert fm.get("category") == "handoff", "kata-defer category must be handoff (M3)"
    assert "kata/module/defer" in (fm.get("tags") or []), "kata-defer must be the optional defer module (D43)"
