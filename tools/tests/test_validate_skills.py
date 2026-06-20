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


def test_beta_engram_learn_feed_schema_documented():
    # β: the wiki-synthesis LEARN-feed schema is enforced in engram.md (BP2 default-FAIL floor).
    from validate_skills import REQUIRED_PROTOCOL, check_protocol_schemas
    req = set(REQUIRED_PROTOCOL["engram.md"])
    assert {"wiki-synthesis", "produced-by", "learnFeed", "LEARN", "CONSULT"} <= req
    findings = [str(f) for f in check_protocol_schemas([])]
    assert not any("engram.md" in f for f in findings), findings


def test_beta_no_separate_wiki_synthesis_file():
    # BC5/A4f: the wiki-synthesis schema lives IN engram.md, never a separate protocol file.
    assert not (v.REPO_ROOT / "protocol" / "wiki-synthesis.md").exists()


def test_beta_kata_improve_learn_feed_emit_only():
    # β rides a kata-improve emit-only sub-mode; zero CONSULT (BC2), redaction-gated (C3), no-op unconfigured (BC1).
    body = (v.SKILLS_DIR / "meta" / "kata-improve" / "SKILL.md").read_text(encoding="utf-8")
    assert "LEARN-feed emit" in body, "kata-improve must host the β LEARN-feed sub-mode"
    assert "zero consult" in body.lower(), "β must be emit-only — no CONSULT call-site (BC2)"
    assert "redaction" in body.lower(), "β must redaction-gate before any write (C3)"
    assert "engram.learnFeed.dir" in body, "β must no-op without a configured feed dir (BC1)"


def test_ao_orientation_protocol_schema_documented():
    # AO: the orientation contract is enforced (tiers + adjacency + task-type + callout).
    from validate_skills import REQUIRED_PROTOCOL, check_protocol_schemas
    req = set(REQUIRED_PROTOCOL["orientation.md"])
    assert {"stable", "context", "volatile", "adjacency", "task-type", "callout"} <= req
    findings = [str(f) for f in check_protocol_schemas([])]
    assert not any("orientation.md" in f for f in findings), findings


def test_ao_kata_orient_present_spine_no_write():
    # AO: kata-orient is the read-side mirror of kata-handoff — spine, read-only (no Write/Edit/Agent).
    skills = {s.name: s for s in v.load_skills()}
    assert "kata-orient" in skills, "kata-orient must exist (loop-cognition AO)"
    fm = skills["kata-orient"].frontmatter
    assert fm.get("category") == "handoff", "kata-orient category must be handoff (read half of handoff)"
    assert "kata/spine" in (fm.get("tags") or []), "kata-orient is spine (receiving half of the two-way handoff)"
    tools = fm.get("allowed-tools") or []
    for forbidden in ("Write", "Edit", "Agent"):
        assert forbidden not in tools, f"kata-orient must be read-only — found {forbidden}"


def test_ao_handoff_orientation_tiein():
    # The write side (kata-handoff) must author for the read side (kata-orient) — aligned from both sides (D76).
    body = (v.SKILLS_DIR / "handoff" / "kata-handoff" / "SKILL.md").read_text(encoding="utf-8")
    assert "Orientation tie-in" in body, "kata-handoff must document the orientation tie-in"
    assert "kata-orient" in body, "kata-handoff must reference the read-side consumer"


def test_ml_kata_promote_present_human_gate():
    # ML: kata-promote is the stage-2 human promotion gate — meta, with AskUserQuestion (the human decision).
    skills = {s.name: s for s in v.load_skills()}
    assert "kata-promote" in skills, "kata-promote must exist (loop-cognition ML)"
    fm = skills["kata-promote"].frontmatter
    assert fm.get("category") == "meta", "kata-promote category must be meta"
    assert "AskUserQuestion" in (fm.get("allowed-tools") or []), "kata-promote must gate on a human (AskUserQuestion)"


def test_ml_config_autonomy_and_agentskills():
    # ML: config carries the promotion-autonomy dial (default always-human) + the agent-skills toolkit dir.
    text = (v.REPO_ROOT / "protocol" / "config.md").read_text(encoding="utf-8")
    assert "autonomy" in text and "always-human" in text, "config.md must document engram.autonomy (default always-human)"
    assert "agentSkills" in text, "config.md must document the agentSkills toolkit dir"


def test_ml_standards_agent_distilled_discriminators():
    # ML: the agent-distilled discriminator set is documented (matched-but-marked, L5).
    text = (v.REPO_ROOT / "docs" / "STANDARDS.md").read_text(encoding="utf-8")
    assert "agent-distilled" in text, "STANDARDS must document provenance: agent-distilled"
    assert "kata/origin/agent" in text, "STANDARDS must document the agent-origin tag"
    assert "scope:" in text or "scope " in text, "STANDARDS must document the scope discriminator"


def test_rs_kata_research_present_no_write():
    # RS: kata-research is the escalation-routed in-loop researcher — fresh-context, NO-WRITE (RS-GB3/L4).
    skills = {s.name: s for s in v.load_skills()}
    assert "kata-research" in skills, "kata-research must exist (loop-cognition RS)"
    fm = skills["kata-research"].frontmatter
    assert fm.get("category") == "plan", "kata-research category must be plan (control-flow, kin to grill/context)"
    assert "kata/module/research" in (fm.get("tags") or []), "kata-research is the research module"
    tools = fm.get("allowed-tools") or []
    for forbidden in ("Write", "Edit", "Agent"):
        assert forbidden not in tools, f"kata-research must be no-write/no-dispatch — found {forbidden}"


def test_rs_escalation_research_needed_kind():
    # The escalation payload must carry the research-needed routing kind (RS-GB1).
    text = (v.REPO_ROOT / "protocol" / "escalation.md").read_text(encoding="utf-8")
    assert "research-needed" in text, "escalation.md must document the research-needed kind"


def test_rs_grounding_gate_documented():
    # The L2 grounding gate (injected-knowledge mode) lives in kata-evaluate + kata-review RUBRIC, never bypassed (D33).
    ev = (v.SKILLS_DIR / "evaluate" / "kata-evaluate" / "SKILL.md").read_text(encoding="utf-8")
    assert "njected-knowledge grounding mode" in ev, "kata-evaluate must host the injected-knowledge grounding mode"
    assert "GROUND" in ev and "REJECT" in ev and "ESCALATE" in ev, "grounding gate verdicts must be defined"
    assert "D33" in ev, "the grounding gate must be marked the never-tiered structural invariant (D33)"
    rub = (v.SKILLS_DIR / "evaluate" / "kata-review" / "RUBRIC.md").read_text(encoding="utf-8")
    assert "njected-knowledge soundness" in rub, "kata-review RUBRIC must host the injected-knowledge soundness surface"


def test_d71_kata_defer_present_and_handoff_category():
    # kata-defer is the grill-skip autonomous-floor safety net (D71) + the no-drift parking valve (D42).
    skills = {s.name: s for s in v.load_skills()}
    assert "kata-defer" in skills, "kata-defer must exist (D71 floor safety net / D42 parking)"
    fm = skills["kata-defer"].frontmatter
    assert fm.get("category") == "handoff", "kata-defer category must be handoff (M3)"
    assert "kata/module/defer" in (fm.get("tags") or []), "kata-defer must be the optional defer module (D43)"


# ── sprint-cadence (D78–D85) ──────────────────────────────────────────────────

def test_sc_config_documents_delivery_axis():
    # T1/D78: config.md must carry the delivery axis with control-first defaults + prime-frame policy.
    from validate_skills import REQUIRED_PROTOCOL, check_protocol_schemas
    assert "delivery" in REQUIRED_PROTOCOL["config.md"]
    text = (v.REPO_ROOT / "protocol" / "config.md").read_text(encoding="utf-8")
    assert "Delivery axis" in text, "config.md must document the delivery axis (D78)"
    assert "one-shot" in text and "incremental" in text, "delivery.shape values must be documented"
    assert "always-stop" in text, "delivery.boundary must default control-first (always-stop, GB6)"
    assert "Prime-frame sizing" in text, "config.md must document the prime-frame policy (D83)"
    findings = [str(f) for f in check_protocol_schemas([])]
    assert not any("config.md" in f for f in findings), findings


def test_sc_state_three_tier_sprint_progression():
    # T2/D81: tier-3 sprint cache documented as disposable + rebuilt from the committed tier-2 trail.
    from validate_skills import REQUIRED_PROTOCOL, check_protocol_schemas
    assert {"sprint", "gateStatus", "dirty", "gated", "rebuild"} <= set(REQUIRED_PROTOCOL["state.md"])
    text = (v.REPO_ROOT / "protocol" / "state.md").read_text(encoding="utf-8")
    assert "git-committed tier-2 trail" in text, "tier-3 must be rebuildable from the git trail (R5)"
    assert "disposable" in text.lower(), "tier-3 cache must be marked disposable, never authoritative"
    findings = [str(f) for f in check_protocol_schemas([])]
    assert not any("state.md" in f for f in findings), findings


def test_sc_handoff_boundary_artifact():
    # T3/D79: the boundary-handoff variant is documented in the protocol schema.
    from validate_skills import REQUIRED_PROTOCOL, check_protocol_schemas
    assert {"Boundary handoff", "sprint index"} <= set(REQUIRED_PROTOCOL["handoff.md"])
    findings = [str(f) for f in check_protocol_schemas([])]
    assert not any("handoff.md" in f for f in findings), findings


def test_sc_escalation_red_sprint_routing():
    # T3/T4: a red sprint routes through escalation, never a boundary.
    text = (v.REPO_ROOT / "protocol" / "escalation.md").read_text(encoding="utf-8")
    assert "Red-sprint routing" in text, "escalation.md must document red-sprint routing"
    assert "never a boundary" in text.lower() or "not a boundary" in text.lower(), \
        "a red gate must NOT become a boundary stop"


def test_sc_kata_report_reports_never_gates():
    # T8/D85/D2: kata-report v1 — evaluate category, reports the gate, never confers one.
    skills = {s.name: s for s in v.load_skills()}
    assert "kata-report" in skills, "kata-report must exist (sprint-cadence D85)"
    fm = skills["kata-report"].frontmatter
    assert fm.get("category") == "evaluate", "kata-report category must be evaluate (M1)"
    body = (v.SKILLS_DIR / "evaluate" / "kata-report" / "SKILL.md").read_text(encoding="utf-8")
    assert "does not gate" in body.lower() or "never gate" in body.lower(), \
        "kata-report must explicitly NOT gate (kata-evaluate owns the gate, D22)"


def test_sc_roadmap_layer_artifact_schema():
    # T4/D85: the roadmap layer is a method file (not a counted skill) and pins the artifact schema.
    roadmap = v.SKILLS_DIR / "plan" / "kata-plan" / "ROADMAP.md"
    assert roadmap.exists(), "the kata-plan roadmap layer (ROADMAP.md) must exist"
    text = roadmap.read_text(encoding="utf-8")
    for key in ("projectDesignRef", "gateCommand", "demonstrableArtifactType", "dagSeamRationale", "dependsOn"):
        assert key in text, f"roadmap artifact schema must pin '{key}' (D85/A1)"
    # it is a layer, not a skill: no SKILL.md in the family folder.
    assert not (v.SKILLS_DIR / "plan" / "kata-plan" / "SKILL.md").exists(), \
        "kata-plan stays a family folder (RUBRIC + ROADMAP), not a counted skill (M2)"


def test_sc_selfhandoff_prime_frame_trigger():
    # T5/B1/D83: the self-handoff trigger is the prime-frame fraction (supersedes D8's %), runs intra-sprint.
    body = (v.SKILLS_DIR / "handoff" / "kata-selfhandoff" / "SKILL.md").read_text(encoding="utf-8")
    assert "prime-frame" in body.lower() or "prime frame" in body.lower(), \
        "self-handoff must trigger on the prime frame (B1/D83)"
    assert "intra-sprint" in body.lower(), "self-handoff must also run intra-sprint (no gate, no drift)"


def test_sc_readiness_sprint_detect_rebuild_readonly():
    # T6/D81: readiness detects sprint state + rebuilds tier-3 from the trail, but stays read-only (L3).
    body = (v.SKILLS_DIR / "coordinate" / "kata-readiness" / "SKILL.md").read_text(encoding="utf-8")
    assert "Sprint-progression detection" in body, "readiness must detect sprint progression (D81)"
    assert "dirty" in body and "gated" in body, "readiness must distinguish dirty (resume) vs gated (course-correct)"
    assert "never write" in body.lower() or "read-only" in body.lower(), \
        "readiness must stay read-only — orchestrator is the single writer (L3)"
    fm = {s.name: s for s in v.load_skills()}["kata-readiness"].frontmatter
    for forbidden in ("Write", "Edit"):
        assert forbidden not in (fm.get("allowed-tools") or []), f"kata-readiness must not gain {forbidden}"


def test_sc_kata_sprint_boundary_protocol():
    # T7/D79/D80: kata-sprint is the spine boundary coordinator with the full G1-G4 protocol.
    skills = {s.name: s for s in v.load_skills()}
    assert "kata-sprint" in skills, "kata-sprint must exist (sprint-cadence D80)"
    fm = skills["kata-sprint"].frontmatter
    assert fm.get("category") == "coordinate", "kata-sprint category must be coordinate"
    assert "kata/spine" in (fm.get("tags") or []), "kata-sprint is spine (the boundary is the steering spine)"
    assert "AskUserQuestion" in (fm.get("allowed-tools") or []), "G1 needs an explicit human approval gate"
    body = (v.SKILLS_DIR / "coordinate" / "kata-sprint" / "SKILL.md").read_text(encoding="utf-8")
    for gate in ("G1", "G2", "G3", "G4"):
        assert gate in body, f"the boundary protocol must encode {gate}"
    assert "PINNED 2 rounds" in body, "G3 must encode the PINNED 2-round cap (not a tunable)"
    assert "blast-radius" in body.lower() and "no numeric threshold" in body.lower(), \
        "G4 must be blast-radius-vs-footprint only — no numeric threshold (D18)"
    assert "never tiered" in body.lower() or "never be tiered" in body.lower(), \
        "G1-G4 are structural invariants, never tiered (D33)"


def test_sc_orchestrate_stays_sprint_blind():
    # BC2: delivery-awareness never leaks into the sprint-blind orchestrator.
    body = (v.SKILLS_DIR / "coordinate" / "kata-orchestrate" / "SKILL.md").read_text(encoding="utf-8")
    assert "kata-sprint" not in body, "kata-orchestrate must stay sprint-blind (BC2) — no kata-sprint reference"
    assert "delivery" not in body.lower(), "kata-orchestrate must not gain delivery-awareness (BC2)"


def test_sc_bootstrap_is_the_boundary_router():
    # D86 (review fix): kata-bootstrap is the entry host — it routes a gated boundary to kata-sprint.
    # Closes the wired-but-not-connected gap (kata-orchestrate is sprint-blind and cannot dispatch).
    body = (v.SKILLS_DIR / "coordinate" / "kata-bootstrap" / "SKILL.md").read_text(encoding="utf-8")
    assert "boundary router" in body.lower(), "kata-bootstrap must declare itself the boundary router (D80/D86)"
    assert "[[kata-sprint]]" in body, "kata-bootstrap must dispatch to kata-sprint on a gated boundary"
    assert "gated" in body and "dirty" in body, "bootstrap must route gated->kata-sprint vs dirty->resume"
    assert "delivery" in body, "bootstrap must write the delivery axis (D78)"
