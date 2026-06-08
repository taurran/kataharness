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
