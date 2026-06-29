"""Tests for tools/escalation.py — TDD (written FIRST, red before implementation).

Covers:
- build_escalation: full valid payload; missing required field → ValueError;
  bad kind → ValueError; bad status → ValueError; empty optionsConsidered → ValueError.
- write_escalation: creates dir + writes <kata_dir>/escalations/<taskId>.json;
  round-trips via json.load; ..‑guard rejects traversal (SystemExit).
- build_finding: returns correct dict; empty source → ValueError;
  bad confidence → ValueError; bad grounds_to_plan → ValueError.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module import
# ---------------------------------------------------------------------------


def test_escalation_module_importable():
    """escalation must be importable without side-effects."""
    import escalation  # noqa: F401


# ---------------------------------------------------------------------------
# build_escalation — happy path
# ---------------------------------------------------------------------------


def _valid_kwargs() -> dict:
    """Return a complete set of valid arguments for build_escalation."""
    return dict(
        taskId="T-42",
        kind="research-needed",
        decisionNeeded="Which caching strategy to adopt?",
        optionsConsidered=["redis", "memcached", "in-process LRU"],
        agentRecommendation="redis",
        rationale="No in-plan solution — requires research before proceeding.",
        lockedDecisionInTension="D15: no external services",
        costOfWaiting="Blocks sprint completion",
        costOfProceeding="Risk of locking in the wrong approach",
        status="open",
        resolution=None,
    )


def test_build_escalation_returns_full_payload():
    from escalation import build_escalation

    kw = _valid_kwargs()
    payload = build_escalation(**kw)

    assert payload["taskId"] == "T-42"
    assert payload["kind"] == "research-needed"
    assert payload["decisionNeeded"] == "Which caching strategy to adopt?"
    assert payload["optionsConsidered"] == ["redis", "memcached", "in-process LRU"]
    assert payload["agentRecommendation"] == "redis"
    assert payload["rationale"] == "No in-plan solution — requires research before proceeding."
    assert payload["lockedDecisionInTension"] == "D15: no external services"
    assert payload["costOfWaiting"] == "Blocks sprint completion"
    assert payload["costOfProceeding"] == "Risk of locking in the wrong approach"
    assert payload["status"] == "open"
    assert payload["resolution"] is None


def test_build_escalation_minimal_required_fields():
    """Optional fields absent → payload still valid."""
    from escalation import build_escalation

    payload = build_escalation(
        taskId="T-1",
        kind="orchestrator-resolvable",
        decisionNeeded="Do X or Y?",
        optionsConsidered=["X", "Y"],
        agentRecommendation="X",
        rationale="Y is ruled out by constraint Z.",
    )
    assert payload["status"] == "open"
    # Optional fields not provided should not be in dict (or be None — either is fine as long as
    # required fields are present and correct)
    assert payload["taskId"] == "T-1"
    assert payload["kind"] == "orchestrator-resolvable"


def test_build_escalation_status_resolved():
    from escalation import build_escalation

    payload = build_escalation(
        taskId="T-9",
        kind="human-required",
        decisionNeeded="Approve architecture?",
        optionsConsidered=["A"],
        agentRecommendation="A",
        rationale="Needs human sign-off.",
        status="resolved",
        resolution="Approved by @taurran 2026-06-21",
    )
    assert payload["status"] == "resolved"
    assert payload["resolution"] == "Approved by @taurran 2026-06-21"


# ---------------------------------------------------------------------------
# build_escalation — validation (fail-closed)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing_field", [
    "taskId", "kind", "decisionNeeded", "optionsConsidered",
    "agentRecommendation", "rationale",
])
def test_build_escalation_missing_required_field_raises(missing_field):
    from escalation import build_escalation

    kw = _valid_kwargs()
    # Remove optional fields that might not be positional
    kw.pop("lockedDecisionInTension", None)
    kw.pop("costOfWaiting", None)
    kw.pop("costOfProceeding", None)
    kw.pop("resolution", None)

    if missing_field in kw:
        del kw[missing_field]
    else:
        # Field might not be in minimal dict — use None to trigger empty-check
        kw[missing_field] = None

    with pytest.raises(ValueError):
        build_escalation(**kw)


def test_build_escalation_empty_task_id_raises():
    from escalation import build_escalation

    kw = _valid_kwargs()
    kw["taskId"] = ""
    with pytest.raises(ValueError):
        build_escalation(**kw)


def test_build_escalation_bad_kind_raises():
    from escalation import build_escalation

    kw = _valid_kwargs()
    kw["kind"] = "totally-invalid"
    with pytest.raises(ValueError):
        build_escalation(**kw)


def test_build_escalation_bad_status_raises():
    from escalation import build_escalation

    kw = _valid_kwargs()
    kw["status"] = "pending"
    with pytest.raises(ValueError):
        build_escalation(**kw)


def test_build_escalation_empty_options_raises():
    from escalation import build_escalation

    kw = _valid_kwargs()
    kw["optionsConsidered"] = []
    with pytest.raises(ValueError):
        build_escalation(**kw)


def test_build_escalation_options_not_list_raises():
    from escalation import build_escalation

    kw = _valid_kwargs()
    kw["optionsConsidered"] = "redis"  # string instead of list
    with pytest.raises(ValueError):
        build_escalation(**kw)


# ---------------------------------------------------------------------------
# write_escalation — happy path
# ---------------------------------------------------------------------------


def test_write_escalation_creates_file_and_dir(tmp_path):
    from escalation import build_escalation, write_escalation

    kata_dir = tmp_path / ".kata"
    payload = build_escalation(
        taskId="T-99",
        kind="research-needed",
        decisionNeeded="Decide something.",
        optionsConsidered=["opt-A", "opt-B"],
        agentRecommendation="opt-A",
        rationale="opt-B breaks LOCKED D7.",
    )
    written_path = write_escalation(str(kata_dir), payload)

    expected = kata_dir / "escalations" / "T-99.json"
    assert expected.exists(), f"Expected file not found: {expected}"
    assert Path(written_path) == expected


def test_write_escalation_round_trips_json(tmp_path):
    from escalation import build_escalation, write_escalation

    kata_dir = tmp_path / ".kata"
    payload = build_escalation(
        taskId="T-77",
        kind="orchestrator-resolvable",
        decisionNeeded="Use X or Y?",
        optionsConsidered=["X", "Y"],
        agentRecommendation="X",
        rationale="Y is slower.",
        costOfWaiting="Sprint delay",
    )
    written_path = write_escalation(str(kata_dir), payload)

    loaded = json.loads(Path(written_path).read_text(encoding="utf-8"))
    assert loaded["taskId"] == "T-77"
    assert loaded["kind"] == "orchestrator-resolvable"
    assert loaded["costOfWaiting"] == "Sprint delay"


def test_write_escalation_uses_indent2(tmp_path):
    """File must be pretty-printed (indent=2)."""
    from escalation import build_escalation, write_escalation

    kata_dir = tmp_path / ".kata"
    payload = build_escalation(
        taskId="T-50",
        kind="human-required",
        decisionNeeded="Q?",
        optionsConsidered=["A"],
        agentRecommendation="A",
        rationale="R.",
    )
    written_path = write_escalation(str(kata_dir), payload)
    raw = Path(written_path).read_text(encoding="utf-8")
    # indent=2 means lines have leading spaces in the JSON body
    assert "  " in raw


def test_write_escalation_returns_str(tmp_path):
    from escalation import build_escalation, write_escalation

    kata_dir = tmp_path / ".kata"
    payload = build_escalation(
        taskId="T-55",
        kind="orchestrator-resolvable",
        decisionNeeded="Q?",
        optionsConsidered=["A"],
        agentRecommendation="A",
        rationale="R.",
    )
    result = write_escalation(str(kata_dir), payload)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# write_escalation — ..‑guard (CWE-23)
# ---------------------------------------------------------------------------


def test_write_escalation_rejects_traversal_double_dot(tmp_path):
    """A kata_dir containing '..' must raise SystemExit (mirror gate_emit pattern)."""
    from escalation import build_escalation, write_escalation

    payload = build_escalation(
        taskId="T-EVIL",
        kind="orchestrator-resolvable",
        decisionNeeded="Q?",
        optionsConsidered=["A"],
        agentRecommendation="A",
        rationale="R.",
    )
    evil_dir = str(tmp_path / ".." / "escape")
    with pytest.raises(SystemExit):
        write_escalation(evil_dir, payload)


def test_write_escalation_rejects_traversal_in_middle(tmp_path):
    """'..'' in any segment of the path must be rejected."""
    from escalation import build_escalation, write_escalation

    payload = build_escalation(
        taskId="T-EVIL2",
        kind="orchestrator-resolvable",
        decisionNeeded="Q?",
        optionsConsidered=["A"],
        agentRecommendation="A",
        rationale="R.",
    )
    evil_dir = str(tmp_path / "sub" / ".." / "escape")
    with pytest.raises(SystemExit):
        write_escalation(evil_dir, payload)


# ---------------------------------------------------------------------------
# build_finding — happy path
# ---------------------------------------------------------------------------


def test_build_finding_returns_correct_dict():
    from escalation import build_finding

    f = build_finding(
        claim="Redis supports Lua scripting natively.",
        source="https://redis.io/docs/manual/programmability/eval-intro/",
        confidence="HIGH",
        grounds_to_plan="YES",
    )
    assert f == {
        "claim": "Redis supports Lua scripting natively.",
        "source": "https://redis.io/docs/manual/programmability/eval-intro/",
        "confidence": "HIGH",
        "groundsToPlan": "YES",
    }


def test_build_finding_med_confidence():
    from escalation import build_finding

    f = build_finding(
        claim="In-process LRU may suffice for < 10k entries.",
        source="tools/README.md:L42",
        confidence="MED",
        grounds_to_plan="PARTIAL",
    )
    assert f["confidence"] == "MED"
    assert f["groundsToPlan"] == "PARTIAL"


def test_build_finding_low_confidence_no():
    from escalation import build_finding

    f = build_finding(
        claim="Memcached is deprecated in the ecosystem.",
        source="https://example.com/article",
        confidence="LOW",
        grounds_to_plan="NO",
    )
    assert f["confidence"] == "LOW"
    assert f["groundsToPlan"] == "NO"


# ---------------------------------------------------------------------------
# build_finding — validation (fail-closed)
# ---------------------------------------------------------------------------


def test_build_finding_empty_claim_raises():
    from escalation import build_finding

    with pytest.raises(ValueError):
        build_finding(claim="", source="https://example.com", confidence="HIGH", grounds_to_plan="YES")


def test_build_finding_empty_source_raises():
    """An ungrounded claim is not a finding — empty source must raise ValueError."""
    from escalation import build_finding

    with pytest.raises(ValueError):
        build_finding(claim="Some claim.", source="", confidence="HIGH", grounds_to_plan="YES")


def test_build_finding_none_source_raises():
    from escalation import build_finding

    with pytest.raises((ValueError, TypeError)):
        build_finding(claim="Some claim.", source=None, confidence="HIGH", grounds_to_plan="YES")


def test_build_finding_bad_confidence_raises():
    from escalation import build_finding

    with pytest.raises(ValueError):
        build_finding(
            claim="Some claim.",
            source="https://example.com",
            confidence="VERY_HIGH",
            grounds_to_plan="YES",
        )


def test_build_finding_bad_grounds_to_plan_raises():
    from escalation import build_finding

    with pytest.raises(ValueError):
        build_finding(
            claim="Some claim.",
            source="https://example.com",
            confidence="MED",
            grounds_to_plan="MAYBE",
        )


def test_build_finding_confidence_case_sensitive():
    """'high' (lowercase) is not a valid confidence — must raise."""
    from escalation import build_finding

    with pytest.raises(ValueError):
        build_finding(
            claim="Some claim.",
            source="https://example.com",
            confidence="high",
            grounds_to_plan="YES",
        )


# ---------------------------------------------------------------------------
# Non-clobber guard behavior tests (TDD — written before implementation)
# ---------------------------------------------------------------------------

_SOURCE = Path(__file__).resolve().parent.parent / "escalation.py"


def test_write_escalation_clobber_different_decision_raises(tmp_path):
    """Overwriting an open escalation with a DIFFERENT decisionNeeded must raise ValueError.

    Defense-in-depth for the IaC Tier-1/Tier-2 double-write: two human-required
    decisions for the same task in one pass must never silently merge.
    """
    from escalation import build_escalation, write_escalation

    kata_dir = tmp_path / ".kata"
    first = build_escalation(
        taskId="T-CLOBBER",
        kind="human-required",
        decisionNeeded="Approve stateful destroy?",
        optionsConsidered=["yes", "no"],
        agentRecommendation="no",
        rationale="Destroys prod DB replica.",
    )
    write_escalation(str(kata_dir), first)

    second = build_escalation(
        taskId="T-CLOBBER",
        kind="human-required",
        decisionNeeded="Authorize IAM privilege escalation?",
        optionsConsidered=["yes", "no"],
        agentRecommendation="no",
        rationale="Grants Admin role to service account.",
    )
    with pytest.raises(ValueError):
        write_escalation(str(kata_dir), second)


def test_write_escalation_idempotent_same_decision_allowed(tmp_path):
    """Re-writing with the SAME open decisionNeeded must be allowed (idempotent)."""
    from escalation import build_escalation, write_escalation

    kata_dir = tmp_path / ".kata"
    payload = build_escalation(
        taskId="T-IDEM",
        kind="human-required",
        decisionNeeded="Approve stateful destroy?",
        optionsConsidered=["yes", "no"],
        agentRecommendation="no",
        rationale="Destroys prod DB replica.",
    )
    write_escalation(str(kata_dir), payload)
    # Idempotent re-write — must not raise
    written_path = write_escalation(str(kata_dir), payload)
    assert written_path.endswith("T-IDEM.json")


def test_write_escalation_resolved_update_same_decision_allowed(tmp_path):
    """Writing a resolved update of the SAME decision must be allowed."""
    from escalation import build_escalation, write_escalation

    kata_dir = tmp_path / ".kata"
    open_payload = build_escalation(
        taskId="T-RES",
        kind="human-required",
        decisionNeeded="Approve IAM change?",
        optionsConsidered=["yes", "no"],
        agentRecommendation="yes",
        rationale="Required for deployment.",
    )
    write_escalation(str(kata_dir), open_payload)

    resolved_payload = build_escalation(
        taskId="T-RES",
        kind="human-required",
        decisionNeeded="Approve IAM change?",
        optionsConsidered=["yes", "no"],
        agentRecommendation="yes",
        rationale="Required for deployment.",
        status="resolved",
        resolution="Approved by @taurran 2026-06-28",
    )
    written_path = write_escalation(str(kata_dir), resolved_payload)
    assert written_path.endswith("T-RES.json")


def test_write_escalation_fresh_task_allowed(tmp_path):
    """Writing to a fresh task (no existing file) must always be allowed."""
    from escalation import build_escalation, write_escalation

    kata_dir = tmp_path / ".kata"
    payload = build_escalation(
        taskId="T-FRESH",
        kind="human-required",
        decisionNeeded="Initial decision?",
        optionsConsidered=["A", "B"],
        agentRecommendation="A",
        rationale="B is incompatible.",
    )
    written_path = write_escalation(str(kata_dir), payload)
    assert written_path.endswith("T-FRESH.json")


def test_write_escalation_existing_resolved_then_new_open_allowed(tmp_path):
    """After an escalation is resolved, a new open escalation for the same task is allowed."""
    from escalation import build_escalation, write_escalation

    kata_dir = tmp_path / ".kata"
    resolved = build_escalation(
        taskId="T-REOPEN",
        kind="human-required",
        decisionNeeded="Old decision?",
        optionsConsidered=["A"],
        agentRecommendation="A",
        rationale="Was blocked.",
        status="resolved",
        resolution="Done.",
    )
    write_escalation(str(kata_dir), resolved)

    new_open = build_escalation(
        taskId="T-REOPEN",
        kind="human-required",
        decisionNeeded="New different decision?",
        optionsConsidered=["X", "Y"],
        agentRecommendation="X",
        rationale="New blocker emerged.",
    )
    written_path = write_escalation(str(kata_dir), new_open)
    assert written_path.endswith("T-REOPEN.json")


# ---------------------------------------------------------------------------
# Mutation non-vacuity proofs — spawn real subprocess via prove_non_vacuous
# ---------------------------------------------------------------------------


def _tools_dir() -> str:
    return str(Path(__file__).parent.parent.resolve())


def _src() -> str:
    return str(_SOURCE.resolve())


def _cmd(test_name: str) -> str:
    return (
        f'cd /d "{_tools_dir()}" && uv run pytest '
        f"tests/test_escalation.py::{test_name} -q"
    )


def test_mutation_proof_non_clobber_guard_condition():
    """(a) Removing the guard condition makes idempotent-write test go red.

    Asserted line (exact, 8-space indent):
        '        if existing_open and incoming_open and different_decision:'
    Removed -> orphan raise -> IndentationError on import -> all tests fail including
    test_write_escalation_idempotent_same_decision_allowed.
    """
    import mutation_run

    asserted_line = "        if existing_open and incoming_open and different_decision:"
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_write_escalation_idempotent_same_decision_allowed")
    )
    assert verdict["nonVacuous"] is True, f"guard condition not load-bearing: {verdict}"


def test_mutation_proof_non_clobber_different_decision():
    """(b) Removing the different_decision assignment makes clobber test go red.

    Asserted line (exact, 8-space indent):
        '        different_decision = existing.get("decisionNeeded") != payload.get("decisionNeeded")'
    Removed -> NameError on `different_decision` reference -> clobber test fails
    (NameError != ValueError; pytest.raises(ValueError) does not catch it).
    """
    import mutation_run

    asserted_line = '        different_decision = existing.get("decisionNeeded") != payload.get("decisionNeeded")'
    verdict = mutation_run.prove_non_vacuous(
        _src(), asserted_line, _cmd("test_write_escalation_clobber_different_decision_raises")
    )
    assert verdict["nonVacuous"] is True, f"different_decision check not load-bearing: {verdict}"
