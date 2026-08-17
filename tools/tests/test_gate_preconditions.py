"""Tests for gate_preconditions.py — every gate refuses without attested facts (§3.3).

The acceptance this suite proves, verbatim from the frozen PLAN:

    "each gate's refusal fires on its absent-fact fixture; each refusal is a reasoned,
     recorded event (the visible-refusal contract, TM-G1's data half); activation tables
     read recorded closure/corpus state, never config assertions."

So the suite is organised in exactly those three parts, plus the gate_emit wiring:

1. **Absent-fact fixtures** — one per gate class, each proving the refusal FIRES.
2. **Reasoned + recorded** — every refusal names its fact class, system of record and
   remedy; the fold round-trips through the cursor as a NOTE + pointed-to payload.
3. **Activation tables** — the mutation table is derived from the RECORDED X14 closure
   note (green legs -> active; absent/unparseable/uncited -> honor-system on every
   platform), and the judge table is transcribed from tripwire_check's derivation.
4. **gate_emit wiring** — a REFUSED report stops the emit BEFORE the gate command runs.

All tests are PURE: no subprocess, no git, no real gate, injected timestamps.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import gate_preconditions as gp
import kata_board
import run_result
import tripwire_check as tc
import truth_serum as ts

FIXED_UTC = "2026-08-17T00:00:00+00:00"
RUN_ID = "run-20260817T034343Z-e3b50e43"
OTHER_RUN_ID = "run-20260101T000000Z-deadbeef"
SHA = "3f2994756938b221698ca63637052cb5de2da31a"
OTHER_SHA = "aaaaaaabbbbbbbcccccccdddddddeeeeeeefffff"

CI_RUN_URL = "https://github.com/taurran/kataharness/actions/runs/31979757460"


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def closure_note(*, legs: dict[str, str], run_url: str | None = CI_RUN_URL,
                 sha: str | None = SHA) -> str:
    """Render an X14-shaped closure note.  Mirrors the committed evidence note's table."""
    rows = []
    if run_url:
        rows.append(f"| run URL | {run_url} |")
    if sha:
        rows.append(f"| SHA | `{sha}` |")
    rows.append("| conclusion | **success** |")
    for runner, state in legs.items():
        rows.append(f"| `gauntlet ({runner})` | **completed / {state}** — job `95244552908` |")
    return "# BL-X14 — CI record\n\n| | |\n|---|---|\n" + "\n".join(rows) + "\n"


def write_closure(tmp_path: Path, text: str) -> Path:
    """Write a closure note at the module's default artifact path under *tmp_path*."""
    target = tmp_path / gp.MUTATION_CLOSURE_ARTIFACT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def result_json(*, run_id: str = RUN_ID, sha: str = SHA,
                output: str = "40 passed, 1 skipped in 1.0s") -> dict:
    """A real ``run_result.build_result`` artifact — never a hand-rolled lookalike."""
    return run_result.build_result(
        gate_name="task", command="pytest -q", output=output, exit_code=0,
        baseline_sha=OTHER_SHA, result_sha=sha, utc=FIXED_UTC, run_id=run_id,
    )


def detector_report(detector: str, *, verdict: str = ts.VERDICT_PASS,
                    files: tuple[str, ...] = ("tools/a.py",),
                    findings: tuple[ts.Finding, ...] = ()) -> ts.DetectorReport:
    """A real ``DetectorReport`` — its __post_init__ enforces the shape for us."""
    return ts.DetectorReport(
        detector=detector, verdict=verdict, findings=findings,
        candidates_scanned=0 if verdict == ts.VERDICT_ZERO_CANDIDATE else 3,
        files_scanned=files,
        refusal_reason="empty input set" if verdict == ts.VERDICT_REFUSE else None,
    )


ACTIVE_TABLE = {
    "linux": gp.PlatformActivation(
        platform="linux", activation=gp.ACTIVATION_ACTIVE,
        reason="BL-X14 closure RECORDED green on ubuntu-latest", citation=f"{CI_RUN_URL} @ {SHA}",
    ),
}
HONOR_TABLE = {
    "linux": gp.PlatformActivation(
        platform="linux", activation=gp.ACTIVATION_HONOR_SYSTEM,
        reason="closure not recorded", citation=None,
    ),
}


def task_facts(**overrides) -> dict:
    """A fully-attested task-gate fact bundle; override one key to make it absent."""
    facts = {
        "taskId": "tm-lb-gate-preconditions",
        "expectedSha": SHA,
        "expectedRunId": RUN_ID,
        "verifyRerun": result_json(),
        "footprintManifest": {
            "withinFootprint": True, "outOfFootprint": [], "changed": ["tools/a.py"],
        },
        "mutationRerun": {"records": [{"testWentRed": True, "nonVacuous": True}]},
        "platform": "linux",
        "mutationActivation": ACTIVE_TABLE,
        "detectorReports": {"B1": detector_report("B1"), "B3": detector_report("B3")},
        "modifiedFiles": ["tools/a.py"],
    }
    facts.update(overrides)
    return facts


def freeze_facts(**overrides) -> dict:
    facts = {
        "runId": RUN_ID,
        "designPresent": True,
        "planPresent": True,
        "ledgerStatus": "converged",
        "grillDepth": "standard",
        "evidenceValid": True,
        "isTreeRun": False,
        "baselineInput": run_result.input_reference(result_json(run_id=OTHER_RUN_ID)),
        "declaresContractEdges": False,
    }
    facts.update(overrides)
    return facts


def wave_facts(**overrides) -> dict:
    satisfied = gp.task_gate(task_facts(), utc=FIXED_UTC)
    facts = {
        "wave": "wave7",
        "memberTasks": ["tm-lb-gate-preconditions"],
        "taskGateRecords": {"tm-lb-gate-preconditions": satisfied},
        "integrationRegate": result_json(),
        "expectedSha": SHA,
        "expectedRunId": RUN_ID,
        "requiredJudges": ["kata-evaluate"],
        "judgeVerdicts": [
            {"judge": "kata-evaluate", "verdict": "PASS", "payload": "payloads/x-1.json"},
        ],
        "judgeActivation": {"kata-evaluate": tc.ACTIVATION_VERIFIED},
        "judgeStackError": None,
    }
    facts.update(overrides)
    return facts


def final_facts(**overrides) -> dict:
    facts = {
        "runId": RUN_ID,
        "result": result_json(),
        "expectedSha": SHA,
        "expectedRunId": RUN_ID,
        "factTable": {"rows": []},
        "mutationAttestation": {
            "attestedBy": "run-20260817T034343Z-e3b50e43-99", "complete": True,
            "recordCount": 4, "sampled": ["tools/a.py:1"],
        },
    }
    facts.update(overrides)
    return facts


# ===========================================================================
# 0. Module shape
# ===========================================================================


def test_the_status_enum_has_no_warn_member():
    """Refuse-not-warn is enforced by the ENUM, not by a convention someone remembers."""
    assert "warn" not in gp.STATUSES
    assert "warn" not in gp.VERDICTS
    assert "WARN" not in gp.VERDICTS
    assert "refuse" in gp.REFUSE_NOT_WARN_LAW.lower()


def test_every_fact_class_has_a_system_of_record():
    """A refusal whose system of record is unknown cannot be audited (D134)."""
    for fact_class, sor in gp.FACT_SYSTEM_OF_RECORD.items():
        assert sor.strip(), f"{fact_class} has an empty system of record"


def test_the_close_vocabulary_is_reused_not_forked():
    """The close and the gates must never drift into two vocabularies for one fact."""
    import kata_close

    for fact_class, sor in kata_close.SYSTEM_OF_RECORD.items():
        assert gp.FACT_SYSTEM_OF_RECORD[fact_class] == sor


def test_an_unregistered_fact_class_raises_rather_than_refusing_anonymously():
    with pytest.raises(gp.PreconditionError, match="unregistered fact class"):
        gp._check(gp.GATE_TASK, "not-a-fact-class", gp.STATUS_SATISFIED, "x")


def test_a_report_cannot_claim_satisfied_while_carrying_a_refusal():
    refusal = gp._check(gp.GATE_TASK, "lane", gp.STATUS_REFUSED, "absent", "do the thing")
    with pytest.raises(gp.PreconditionError, match="contradicts the checks"):
        gp.PreconditionReport(
            gate=gp.GATE_TASK, verdict=gp.VERDICT_SATISFIED, checks=(refusal,)
        )


def test_a_report_over_zero_checks_is_refused_as_vacuous():
    with pytest.raises(gp.PreconditionError, match="ZERO checks"):
        gp.PreconditionReport(gate=gp.GATE_TASK, verdict=gp.VERDICT_SATISFIED, checks=())


def test_a_refusal_without_a_remedy_is_refused():
    """A refusal with no legal path is a dead end, not a gate."""
    with pytest.raises(gp.PreconditionError, match="name the remedy"):
        gp._check(gp.GATE_TASK, "lane", gp.STATUS_REFUSED, "absent")


def test_gate_preconditions_spawns_no_subprocess_and_never_evals():
    """No new exec-safety sink: this engine composes recorded facts, it runs nothing."""
    source = Path(gp.__file__).read_text(encoding="utf-8")
    assert "import subprocess" not in source
    assert "shell=True" not in source
    for forbidden in ("eval(", "exec("):
        assert forbidden not in source


# ===========================================================================
# 1. Absent-fact fixtures — ONE PER GATE CLASS.  Each refusal must FIRE.
# ===========================================================================


def test_task_gate_refuses_without_mutation_rerun_record():
    """THE EVIDENCE NODE.  Absent §3.6 engine mutation re-run, activation ACTIVE ⇒ REFUSE.

    This is the whole task in one assertion: the gate does not warn, does not proceed
    with a note, and does not credit the worker's own claimed mutation set.  It refuses,
    and the refusal names the fact class, its system of record, and the remedy.
    """
    report = gp.task_gate(task_facts(mutationRerun=None), utc=FIXED_UTC)

    assert report.verdict == gp.VERDICT_REFUSED
    assert report.blocking is True

    refused = [c for c in report.refusals if c.fact_class == "mutation-rerun"]
    assert len(refused) == 1, "the mutation-rerun refusal did not fire"
    check = refused[0]
    assert check.status == gp.STATUS_REFUSED
    assert "ENGINE mutation re-run record" in check.reason
    assert "ACTIVE on this platform" in check.reason
    assert "worker-reported" in check.reason
    assert "verify command" in check.remedy
    assert "DESIGN" in check.system_of_record or "§3.6" in check.system_of_record
    # A refusal is a recorded event, not a warning: it survives serialisation whole.
    assert json.loads(report.to_json())["verdict"] == gp.VERDICT_REFUSED


def test_task_gate_does_not_refuse_when_the_platform_is_honor_system():
    """E8, the other direction: 'no Linux task gate fail-closes on a Broken prover.'"""
    report = gp.task_gate(
        task_facts(mutationRerun=None, mutationActivation=HONOR_TABLE), utc=FIXED_UTC
    )

    assert report.verdict == gp.VERDICT_SATISFIED
    honor = [c for c in report.honor_system if c.fact_class == "mutation-rerun"]
    assert len(honor) == 1
    assert "NOT ACTIVE" in honor[0].reason
    assert "Honor-system" in honor[0].reason
    # Declared, not silent: the state is IN the record.
    assert "mutation-rerun" in gp.precondition_record(report, run_id=RUN_ID)[
        "honorSystemClasses"
    ]


def test_task_gate_refuses_on_an_unknown_platform_rather_than_assuming_active():
    """An activation table that does not cover the platform never activates (E8)."""
    report = gp.task_gate(
        task_facts(mutationRerun=None, platform="sunos5"), utc=FIXED_UTC
    )
    assert report.verdict == gp.VERDICT_SATISFIED
    assert any("no recorded activation entry" in c.reason for c in report.honor_system)


@pytest.mark.parametrize("absent,fact_class", [
    ("verifyRerun", "verify-rerun"),
    ("footprintManifest", "lane"),
    ("detectorReports", "detector-pass"),
])
def test_task_gate_refuses_on_each_absent_fact(absent, fact_class):
    report = gp.task_gate(task_facts(**{absent: None}), utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_REFUSED
    assert fact_class in {c.fact_class for c in report.refusals}


def test_task_gate_refuses_stale_or_wrong_run_evidence():
    """B4 identity: SHA fresh AND runId exact, delegated to the ONE strict gate."""
    stale = gp.task_gate(task_facts(verifyRerun=result_json(sha=OTHER_SHA)), utc=FIXED_UTC)
    assert stale.verdict == gp.VERDICT_REFUSED
    assert any("stale-evidence" in c.reason for c in stale.refusals)

    wrong = gp.task_gate(
        task_facts(verifyRerun=result_json(run_id=OTHER_RUN_ID)), utc=FIXED_UTC
    )
    assert wrong.verdict == gp.VERDICT_REFUSED
    assert any("wrong-run" in c.reason for c in wrong.refusals)
    assert any(run_result.RUN_MEMBERSHIP_LAW in c.reason for c in wrong.refusals)


def test_task_gate_refuses_an_out_of_lane_change():
    report = gp.task_gate(task_facts(footprintManifest={
        "withinFootprint": False, "outOfFootprint": ["tools/other.py"],
    }), utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_REFUSED
    lane = [c for c in report.refusals if c.fact_class == "lane"][0]
    assert "tools/other.py" in lane.reason


def test_freeze_gate_refuses_on_each_absent_fact():
    for absent, fact_class in [
        ({"designPresent": False}, "design"),
        ({"planPresent": False}, "plan"),
        ({"ledgerStatus": "open"}, "governing-ledger"),
        ({"evidenceValid": False, "evidenceError": "freeform command"}, "task-evidence"),
        ({"baselineInput": None}, "baseline-input"),
        ({"isTreeRun": True, "armRegistryPresent": False}, "arm-registry"),
        ({"declaresContractEdges": True, "contractEdgeFreezePresent": False},
         "contract-edge-freeze"),
    ]:
        report = gp.freeze_gate(freeze_facts(**absent), utc=FIXED_UTC)
        assert report.verdict == gp.VERDICT_REFUSED, absent
        assert fact_class in {c.fact_class for c in report.refusals}, absent


def test_freeze_gate_refuses_a_baseline_credited_as_gate_evidence():
    """BASELINE_INPUT_LAW: the baseline is an INPUT, never gate evidence."""
    bad = dict(run_result.input_reference(result_json(run_id=OTHER_RUN_ID)))
    bad["creditableAsGateEvidence"] = True
    report = gp.freeze_gate(freeze_facts(baselineInput=bad), utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_REFUSED
    check = [c for c in report.refusals if c.fact_class == "baseline-input"][0]
    assert run_result.BASELINE_INPUT_LAW in check.reason


def test_freeze_gate_satisfied_on_the_full_fact_set():
    report = gp.freeze_gate(freeze_facts(), utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_SATISFIED
    assert report.utc == FIXED_UTC


def test_wave_gate_refuses_on_each_absent_fact():
    refused_task = gp.task_gate(task_facts(mutationRerun=None), utc=FIXED_UTC)
    for absent, fact_class in [
        ({"taskGateRecords": {}}, "task-gate-record"),
        ({"taskGateRecords": {"tm-lb-gate-preconditions": refused_task}}, "task-gate-record"),
        ({"integrationRegate": None}, "integration-regate"),
        ({"judgeVerdicts": []}, "verdict"),
        ({"requiredJudges": []}, "verdict"),
        ({"memberTasks": []}, "task-gate-record"),
    ]:
        report = gp.wave_gate(wave_facts(**absent), utc=FIXED_UTC)
        assert report.verdict == gp.VERDICT_REFUSED, absent
        assert fact_class in {c.fact_class for c in report.refusals}, absent


def test_wave_gate_refuses_a_conversational_judge_verdict():
    """A verdict with no payload pointer is a value that lived only in a conversation."""
    report = gp.wave_gate(wave_facts(judgeVerdicts=[
        {"judge": "kata-evaluate", "verdict": "PASS"},
    ]), utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_REFUSED
    assert any("conversational value" in c.reason for c in report.refusals)


def test_wave_gate_refuses_when_the_judge_stack_cannot_be_enumerated():
    report = gp.wave_gate(
        wave_facts(judgeStackError="skills/evaluate is absent"), utc=FIXED_UTC
    )
    assert report.verdict == gp.VERDICT_REFUSED
    check = [c for c in report.refusals if c.fact_class == "judge-activation"][0]
    assert "anti-vacuity" in check.reason


def test_wave_gate_records_a_dormant_judge_as_honor_system_never_blocked():
    """R-M6: deny-everything dissolved — a Dormant judge is declared, not blocked."""
    report = gp.wave_gate(
        wave_facts(judgeActivation={"kata-evaluate": tc.ACTIVATION_DORMANT}), utc=FIXED_UTC
    )
    assert report.verdict == gp.VERDICT_SATISFIED
    honor = [c for c in report.honor_system if c.fact_class == "judge-activation"]
    assert len(honor) == 1
    assert "Dormant, not Verified" in honor[0].reason


def test_wave_gate_satisfied_on_the_full_fact_set():
    assert gp.wave_gate(wave_facts(), utc=FIXED_UTC).verdict == gp.VERDICT_SATISFIED


def test_final_gate_refuses_on_each_absent_fact():
    for absent, fact_class in [
        ({"result": None}, "verify-rerun"),
        ({"factTable": None}, "fact-table"),
        ({"mutationAttestation": None}, "mutation-attestation"),
    ]:
        report = gp.final_gate(final_facts(**absent), utc=FIXED_UTC)
        assert report.verdict == gp.VERDICT_REFUSED, absent
        assert fact_class in {c.fact_class for c in report.refusals}, absent


def test_final_gate_refuses_an_incomplete_or_unattributed_mutation_attestation():
    """R-M10: the attestation covers the WHOLE record set, and names who attested it."""
    incomplete = gp.final_gate(final_facts(mutationAttestation={
        "attestedBy": "rec-1", "complete": False, "recordCount": 2,
    }), utc=FIXED_UTC)
    assert incomplete.verdict == gp.VERDICT_REFUSED
    assert any("INCOMPLETE" in c.reason for c in incomplete.refusals)

    anon = gp.final_gate(final_facts(mutationAttestation={
        "complete": True, "recordCount": 2,
    }), utc=FIXED_UTC)
    assert anon.verdict == gp.VERDICT_REFUSED
    assert any("unattributed" in c.reason for c in anon.refusals)


def test_final_gate_refuses_a_no_counts_result_rather_than_reading_zero_failures():
    """BL-X13 honesty: unavailable counts are never a success-shaped clean 0/0."""
    report = gp.final_gate(
        final_facts(result=result_json(output="build finished with no summary line")),
        utc=FIXED_UTC,
    )
    assert report.verdict == gp.VERDICT_REFUSED
    check = [c for c in report.refusals if c.fact_class == "per-gate-counts"][0]
    assert "never to be read as zero failures" in check.reason


def test_final_gate_satisfied_on_the_full_fact_set():
    assert gp.final_gate(final_facts(), utc=FIXED_UTC).verdict == gp.VERDICT_SATISFIED


def test_convergence_gate_refuses_without_a_record():
    report = gp.convergence_gate(
        {"grillDepth": "standard", "convergenceRecord": None}, utc=FIXED_UTC
    )
    assert report.verdict == gp.VERDICT_REFUSED
    assert "convergence-pass" in {c.fact_class for c in report.refusals}


def test_convergence_gate_refuses_a_pass_with_no_dispatch_record_id():
    report = gp.convergence_gate({
        "grillDepth": "standard", "convergenceRecord": {"passes": [{"tier": "standard"}]},
    }, utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_REFUSED
    assert any("no seam record id" in c.reason for c in report.refusals)


def test_convergence_gate_refuses_a_single_dispatch_at_the_double_pass_depth():
    """§3.3: proof the Advanced double-pass ran as TWO DISTINCT dispatches."""
    report = gp.convergence_gate({
        "grillDepth": "full",
        "convergenceRecord": {"passes": [{"recordId": "r-1"}, {"recordId": "r-1"}]},
    }, utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_REFUSED
    assert any("one pass twice" in c.reason for c in report.refusals)

    ok = gp.convergence_gate({
        "grillDepth": "full",
        "convergenceRecord": {"passes": [{"recordId": "r-1"}, {"recordId": "r-2"}]},
    }, utc=FIXED_UTC)
    assert ok.verdict == gp.VERDICT_SATISFIED


def test_sprint_stop_gate_refuses_on_each_absent_fact():
    good = {"judge": "kata-evaluate", "verdict": "PASS",
            "payload": "payloads/x-1.json", "runId": RUN_ID}
    for facts, needle in [
        ({"persistedVerdict": None, "expectedRunId": RUN_ID}, "no PERSISTED"),
        ({"persistedVerdict": {k: v for k, v in good.items() if k != "payload"},
          "expectedRunId": RUN_ID}, "conversational value"),
        ({"persistedVerdict": good, "expectedRunId": None}, "did not state which run"),
        ({"persistedVerdict": {**good, "runId": OTHER_RUN_ID}, "expectedRunId": RUN_ID},
         "belongs to run"),
    ]:
        report = gp.sprint_stop_gate(facts, utc=FIXED_UTC)
        assert report.verdict == gp.VERDICT_REFUSED, facts
        assert any(needle in c.reason for c in report.refusals), needle

    assert gp.sprint_stop_gate(
        {"persistedVerdict": good, "expectedRunId": RUN_ID}, utc=FIXED_UTC
    ).verdict == gp.VERDICT_SATISFIED


# ===========================================================================
# 1b. The never-a-de-facto-mandate law (pass-1 residual 4)
# ===========================================================================


def test_a_grill_less_run_is_never_required_to_produce_a_grill_artifact():
    """No gate requires a grill artifact of a run that legally has none (D71)."""
    freeze = gp.freeze_gate(
        freeze_facts(grillDepth="skip", ledgerStatus=None), utc=FIXED_UTC
    )
    assert freeze.verdict == gp.VERDICT_SATISFIED
    absent = [c for c in freeze.legally_absent if c.fact_class == "governing-ledger"]
    assert len(absent) == 1
    assert gp.NEVER_A_DE_FACTO_MANDATE_LAW in absent[0].reason

    conv = gp.convergence_gate({"grillDepth": "skip"}, utc=FIXED_UTC)
    assert conv.verdict == gp.VERDICT_SATISFIED
    assert conv.legally_absent[0].fact_class == "convergence-pass"


def test_an_undeclared_run_shape_is_not_a_legally_grill_less_one():
    """Fail-closed: unknown != skip.  A shape nobody stated does not earn the exemption."""
    report = gp.freeze_gate(
        freeze_facts(grillDepth=None, ledgerStatus=None), utc=FIXED_UTC
    )
    assert report.verdict == gp.VERDICT_REFUSED
    check = [c for c in report.refusals if c.fact_class == "governing-ledger"][0]
    assert "no grillDepth was declared" in check.reason


def test_legally_absent_is_neither_a_refusal_nor_a_silent_pass():
    """It is a STATED fact about the run's shape — it appears in the record."""
    report = gp.convergence_gate({"grillDepth": "skip"}, utc=FIXED_UTC)
    record = gp.precondition_record(report, run_id=RUN_ID)
    assert record["legallyAbsentClasses"] == ["convergence-pass"]
    assert record["refusedClasses"] == []
    assert "legally-absent=convergence-pass" in gp.format_precondition_line(record)


# ===========================================================================
# 2. Every refusal is a REASONED, RECORDED event (TM-G1's data half)
# ===========================================================================


@pytest.mark.parametrize("report", [
    gp.freeze_gate(freeze_facts(designPresent=False), utc=FIXED_UTC),
    gp.task_gate(task_facts(mutationRerun=None), utc=FIXED_UTC),
    gp.wave_gate(wave_facts(integrationRegate=None), utc=FIXED_UTC),
    gp.final_gate(final_facts(factTable=None), utc=FIXED_UTC),
    gp.convergence_gate({"grillDepth": "standard"}, utc=FIXED_UTC),
    gp.sprint_stop_gate({"persistedVerdict": None, "expectedRunId": RUN_ID}, utc=FIXED_UTC),
])
def test_every_refusal_names_its_fact_class_system_of_record_and_remedy(report):
    assert report.refusals, "the absent-fact fixture did not produce a refusal"
    for check in report.refusals:
        assert check.fact_class in gp.FACT_SYSTEM_OF_RECORD
        assert check.system_of_record == gp.FACT_SYSTEM_OF_RECORD[check.fact_class]
        assert check.reason.strip() and check.remedy.strip()


def test_every_gate_class_has_an_absent_fact_refusal():
    """The acceptance, as a completeness assertion over the §3.3 map's rows."""
    refusing = {
        gp.freeze_gate(freeze_facts(designPresent=False), utc=FIXED_UTC),
        gp.task_gate(task_facts(mutationRerun=None), utc=FIXED_UTC),
        gp.wave_gate(wave_facts(integrationRegate=None), utc=FIXED_UTC),
        gp.final_gate(final_facts(factTable=None), utc=FIXED_UTC),
        gp.convergence_gate({"grillDepth": "standard"}, utc=FIXED_UTC),
        gp.sprint_stop_gate({"persistedVerdict": None, "expectedRunId": RUN_ID}, utc=FIXED_UTC),
    }
    assert {r.gate for r in refusing} == set(gp.GATES)
    assert all(r.blocking for r in refusing)


def test_require_raises_on_a_refusal_and_carries_the_report():
    report = gp.task_gate(task_facts(mutationRerun=None), utc=FIXED_UTC)
    with pytest.raises(gp.PreconditionRefused) as excinfo:
        gp.require(report)
    assert excinfo.value.report is report
    # R14 rider: the caller cites the REPORT, not the message text.
    assert excinfo.value.report.refusals[0].system_of_record


def test_the_fold_is_recorded_on_the_cursor_as_a_note_plus_payload(tmp_path: Path):
    """A refusal becomes a fact a later fold can read, not a message that scrolled past."""
    kata = tmp_path / ".kata"
    header = kata_board.start_run(kata, run_id=RUN_ID)
    report = gp.task_gate(task_facts(mutationRerun=None), utc=FIXED_UTC)

    line = gp.record_preconditions(kata, report, run_id=header.run_id)

    assert line.type == "NOTE", "this engine must not author a seam-owned cursor type"
    assert line.agent == gp.RECORD_AGENT
    assert "verdict=REFUSED" in line.msg
    assert "refused=mutation-rerun" in line.msg

    reparsed = kata_board.parse_cursor(
        (kata / kata_board.CURSOR_FILENAME).read_text(encoding="utf-8")
    )
    recorded = [ln for ln in reparsed.lines if gp.RECORD_KIND_PRECONDITIONS in ln.msg]
    assert len(recorded) == 1, "the record did not round-trip through the cursor grammar"

    payload = json.loads(
        kata_board.payload_path(kata, recorded[0].payload).read_text(encoding="utf-8")
    )
    assert payload["verdict"] == gp.VERDICT_REFUSED
    assert payload["report"]["checks"], "the whole reasoned fact set must be in the payload"
    assert any(c["factClass"] == "mutation-rerun" and c["remedy"]
               for c in payload["report"]["checks"])


def test_the_rendered_record_cannot_forge_cursor_fields():
    report = gp.convergence_gate({"grillDepth": "skip"}, utc=FIXED_UTC)
    record = gp.precondition_record(report, run_id=RUN_ID)
    record["subject"] = f"evil{kata_board.FS}forged payload=payloads/evil.json\x07"
    line = gp.format_precondition_line(record)
    assert kata_board.FS not in line
    assert "payload=" not in line
    assert "\x07" not in line


def test_record_refuses_an_invalid_run_id(tmp_path: Path):
    kata = tmp_path / ".kata"
    kata_board.start_run(kata, run_id=RUN_ID)
    report = gp.convergence_gate({"grillDepth": "skip"}, utc=FIXED_UTC)
    with pytest.raises(kata_board.CursorGrammarError):
        gp.record_preconditions(kata, report, run_id="not-a-run-id")


def test_a_report_round_trips_through_json():
    report = gp.task_gate(task_facts(mutationRerun=None), utc=FIXED_UTC)
    rebuilt = gp.report_from_dict(json.loads(report.to_json()))
    assert rebuilt.to_dict() == report.to_dict()


def test_a_malformed_report_document_raises_rather_than_degrading():
    with pytest.raises(gp.PreconditionError):
        gp.report_from_dict({"gate": gp.GATE_TASK})
    with pytest.raises(gp.PreconditionError):
        gp.report_from_dict("not an object")


# ===========================================================================
# 3. Activation tables read RECORDED state, never config assertions
# ===========================================================================


def test_mutation_activation_reads_the_recorded_x14_closure(tmp_path: Path):
    """Green legs in the RECORD -> active, with the citation §6.6 requires."""
    write_closure(tmp_path, closure_note(
        legs={"ubuntu-latest": "success", "windows-latest": "success"}
    ))
    table = gp.mutation_activation(tmp_path)

    assert table["linux"].activation == gp.ACTIVATION_ACTIVE
    assert table["win32"].activation == gp.ACTIVATION_ACTIVE
    assert table["linux"].citation == f"{CI_RUN_URL} @ {SHA}"
    # macOS has no recorded leg — never activated by the other legs' success.
    assert table["darwin"].activation == gp.ACTIVATION_HONOR_SYSTEM


def test_a_red_leg_never_activates_its_platform(tmp_path: Path):
    write_closure(tmp_path, closure_note(
        legs={"ubuntu-latest": "failure", "windows-latest": "success"}
    ))
    table = gp.mutation_activation(tmp_path)
    assert table["linux"].activation == gp.ACTIVATION_HONOR_SYSTEM
    assert table["win32"].activation == gp.ACTIVATION_ACTIVE


def test_an_absent_closure_record_leaves_every_platform_honor_system(tmp_path: Path):
    """E8: activating before the recorded closure is drift, so the default is never-active."""
    table = gp.mutation_activation(tmp_path)
    assert {a.activation for a in table.values()} == {gp.ACTIVATION_HONOR_SYSTEM}
    assert all("unreadable" in a.reason for a in table.values())


def test_an_uncited_closure_does_not_activate(tmp_path: Path):
    """DESIGN §6.6: the citation is what makes the transition legal, not the note's say-so."""
    write_closure(tmp_path, closure_note(
        legs={"ubuntu-latest": "success"}, run_url=None, sha=None
    ))
    closure = gp.read_mutation_closure(tmp_path)
    assert closure["readable"] is False
    assert any("citation" in r for r in closure["reasons"])
    assert gp.mutation_activation(tmp_path)["linux"].activation == gp.ACTIVATION_HONOR_SYSTEM


def test_a_contradictory_leg_record_does_not_activate(tmp_path: Path):
    """One runner recorded both green and red is not a closure."""
    write_closure(tmp_path, closure_note(
        legs={"ubuntu-latest": "success"}
    ) + "| `gauntlet (ubuntu-latest)` | **completed / failure** — job `1` |\n")
    assert gp.mutation_activation(tmp_path)["linux"].activation == gp.ACTIVATION_HONOR_SYSTEM


def test_the_citation_is_bound_to_the_table_that_records_the_legs(tmp_path: Path):
    """A note records several CI runs; the closure's citation must come from ONE table.

    A file-wide scan would pair the closure run's URL with an earlier table's SHA — a
    citation naming a pair no CI run ever produced.  The committed X14 note has exactly
    this shape (three run/SHA tables, legs in only one), so this is a live hazard, not a
    hypothetical one.
    """
    decoy = (
        "## An earlier, superseded run\n\n"
        "| | |\n|---|---|\n"
        "| run URL | https://github.com/o/r/actions/runs/11111111111 |\n"
        f"| SHA | `{OTHER_SHA}` |\n\n"
    )
    write_closure(tmp_path, decoy + closure_note(legs={"ubuntu-latest": "success"}))

    closure = gp.read_mutation_closure(tmp_path)
    assert closure["readable"] is True
    assert closure["sha"] == SHA, "the citation cross-bound to a different table's SHA"
    assert closure["ciRunId"] == "31979757460"


def test_two_tables_with_leg_rows_are_ambiguous_and_activate_nothing(tmp_path: Path):
    write_closure(tmp_path, (
        closure_note(legs={"ubuntu-latest": "success"})
        + "\ntext between the tables\n\n"
        + closure_note(legs={"ubuntu-latest": "success"})
    ))
    closure = gp.read_mutation_closure(tmp_path)
    assert closure["readable"] is False
    assert any("ambiguous" in r for r in closure["reasons"])
    assert gp.mutation_activation(tmp_path)["linux"].activation == gp.ACTIVATION_HONOR_SYSTEM


def test_a_citation_outside_the_leg_table_does_not_count(tmp_path: Path):
    """§6.6: the citation must sit with the legs, not somewhere in the prose."""
    write_closure(tmp_path, (
        f"Cited in prose: {CI_RUN_URL} @ `{SHA}`\n\n"
        + closure_note(legs={"ubuntu-latest": "success"}, run_url=None, sha=None)
    ))
    closure = gp.read_mutation_closure(tmp_path)
    assert closure["readable"] is False
    assert any("SAME table" in r for r in closure["reasons"])


def test_mutation_activation_never_assumes_a_state():
    with pytest.raises(gp.PreconditionError, match="never assumes an activation state"):
        gp.mutation_activation()


def test_the_engine_pins_no_activation_state_as_a_constant():
    """The activation table reads recorded state — never a config assertion in the code.

    The artifact PATH is a pointer to the record; a hard-coded CI run id or a per-platform
    'active' constant would be the config assertion the law forbids, so neither exists.
    """
    source = Path(gp.__file__).read_text(encoding="utf-8")
    assert "31979757460" not in source, "a pinned CI run id is a config assertion"
    assert gp.MUTATION_CLOSURE_ARTIFACT.endswith(".md")
    assert "evidence/x14-ci-green.md" in gp.MUTATION_CLOSURE_ARTIFACT


def test_the_committed_closure_record_is_the_one_the_burn_cites(tmp_path: Path):
    """Live read of the REAL committed record — the burn's own activation fact.

    Not a fixture: this asserts the engine can parse the artifact that actually exists in
    this repo, so the activation table the run uses is derived from the same bytes a human
    reviewer reads.
    """
    repo_root = Path(__file__).resolve().parents[2]
    closure = gp.read_mutation_closure(repo_root)
    if not (repo_root / gp.MUTATION_CLOSURE_ARTIFACT).is_file():
        pytest.skip("the X14 closure record is not present in this tree")
    assert closure["readable"] is True, closure["reasons"]
    assert closure["legs"], "no CI leg was parsed out of the committed record"
    assert closure["runUrl"] and closure["sha"]
    table = gp.mutation_activation(repo_root, closure=closure)
    assert set(table) == set(gp.PLATFORMS)


def test_judge_activation_transcribes_tripwire_checks_derivation():
    table, err = gp.judge_activation(summary={
        "judges": [
            {"judge": "kata-evaluate", "activation": tc.ACTIVATION_VERIFIED},
            {"judge": "kata-slop-check", "activation": tc.ACTIVATION_HONOR_SYSTEM},
        ],
    })
    assert err is None
    assert table == {
        "kata-evaluate": tc.ACTIVATION_VERIFIED,
        "kata-slop-check": tc.ACTIVATION_HONOR_SYSTEM,
    }


def test_judge_activation_reports_an_unreadable_stack_rather_than_an_empty_table():
    table, err = gp.judge_activation(summary={"judges": []})
    assert table == {}
    assert err and "anti-vacuity" in err


def test_judge_activation_over_the_live_tree_matches_tripwire_check():
    """The table is a transcription, never a second derivation (one source of truth)."""
    repo_root = Path(__file__).resolve().parents[2]
    try:
        summary = tc.check_all(repo_root)
    except tc.TripwireRefusal:
        pytest.skip("the judge stack is not readable in this tree")
    table, err = gp.judge_activation(repo_root)
    assert err is None
    assert table == {j["judge"]: j["activation"] for j in summary["judges"]}
    assert set(table.values()) <= tc.ACTIVATION_STATES


# ===========================================================================
# 3b. The B1/B3 input-set ruling (DEF-16 / the Loop-A spot-audit)
# ===========================================================================


def test_a_whole_tree_detector_scan_is_not_a_task_gate_pass():
    """The ruling, mechanically: B1/B3 are credited only over the TASK-MODIFIED set."""
    report = gp.task_gate(task_facts(detectorReports={
        "B1": detector_report("B1", files=("tools/a.py", "tools/drift_gate.py")),
        "B3": detector_report("B3"),
    }), utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_REFUSED
    check = [c for c in report.refusals if c.fact_class == "detector-pass"][0]
    assert "OUTSIDE the task-modified set" in check.reason
    assert "tools/drift_gate.py" in check.reason


def test_an_undeclared_modified_set_refuses_rather_than_crediting_an_unbounded_scan():
    report = gp.task_gate(task_facts(modifiedFiles=[]), utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_REFUSED
    assert any("unbounded input set" in c.reason for c in report.refusals)


def test_a_blocking_detector_verdict_is_carried_not_overruled():
    """E3: no new suppressor class.  A real BLOCK in the task's own files stands."""
    finding = ts.Finding(
        detector="B3", path="tools/a.py", line=7, family="debt-marker:TODO",
        message="debt marker with no DEF-* on the same line",
    )
    report = gp.task_gate(task_facts(detectorReports={
        "B1": detector_report("B1"),
        "B3": detector_report("B3", verdict=ts.VERDICT_BLOCK, findings=(finding,)),
    }), utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_REFUSED
    check = [c for c in report.refusals if c.fact_class == "detector-pass"][0]
    assert "BLOCK" in check.reason
    assert "does not overrule it" in check.reason
    assert "never add a suppressor" in check.remedy


def test_a_detector_refusal_blocks_the_task_gate():
    report = gp.task_gate(task_facts(detectorReports={
        "B1": detector_report("B1", verdict=ts.VERDICT_REFUSE, files=()),
        "B3": detector_report("B3"),
    }), utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_REFUSED
    assert any(ts.VERDICT_REFUSE in c.reason for c in report.refusals)


def test_zero_candidate_is_recorded_honestly_and_does_not_block():
    """ZERO_CANDIDATE is a fact about the INPUT — carried as such, never as a clean bill."""
    report = gp.task_gate(task_facts(detectorReports={
        "B1": detector_report("B1", verdict=ts.VERDICT_ZERO_CANDIDATE),
        "B3": detector_report("B3"),
    }), utc=FIXED_UTC)
    assert report.verdict == gp.VERDICT_SATISFIED
    assert any("certifies nothing about content" in c.reason for c in report.checks)


def test_the_engine_adds_no_self_exemption_for_the_detectors_own_source():
    """DEF-16 stays a ledger question: E3 forbids inventing a suppressor here.

    Asserted over the detector-check CODE, not the module prose: the ruling is that the
    input set is the task's own changed files, full stop.  A per-path carve-out — for
    ``truth_serum`` or for the three known live tree findings — would be the silent
    suppressor E3 forbids, so no filename appears in the decision path at all.
    """
    import inspect

    source = inspect.getsource(gp._detector_checks)
    for forbidden in ("truth_serum.py", "drift_gate.py", "iac_apply.py", "kata_web.py",
                      "tools/truth_serum", "tools/drift_gate"):
        assert forbidden not in source, f"{forbidden} is special-cased in the decision path"
    # And the only file set the decision reads is the caller-declared modified one: there is
    # no module-owned second set to smuggle an exemption into.
    assert 'facts.get("modifiedFiles")' in source
    assert source.count("facts.get(") == 2, "the decision reads exactly two fact keys"


# ===========================================================================
# 4. gate_emit wiring — a REFUSED report stops the emit BEFORE the gate runs
# ===========================================================================


def _boom_runner(command: str):  # pragma: no cover - must never be reached
    raise AssertionError("the gate command ran despite a REFUSED precondition report")


def test_gate_emit_refuses_before_running_the_gate(tmp_path: Path):
    report = gp.task_gate(task_facts(mutationRerun=None), utc=FIXED_UTC)
    import gate_emit

    with pytest.raises(gp.PreconditionRefused) as excinfo:
        gate_emit.emit_gate_artifacts(
            gate_name="task", command="pytest -q", footprint=["tools/"],
            baseline_sha=OTHER_SHA, result_sha=SHA, out_dir=tmp_path,
            preconditions=report, runner=_boom_runner, utc=FIXED_UTC,
        )

    assert excinfo.value.report is report
    # The refusal is RECORDED before it is raised — a cited artifact, not a message.
    written = json.loads((tmp_path / "preconditions.json").read_text(encoding="utf-8"))
    assert written["verdict"] == gp.VERDICT_REFUSED
    assert not (tmp_path / "RESULT.json").exists(), "the gate emitted under unattested facts"


def test_gate_emit_records_a_satisfied_report_and_proceeds(tmp_path: Path):
    import gate_emit

    report = gp.task_gate(task_facts(), utc=FIXED_UTC)
    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        summary = gate_emit.emit_gate_artifacts(
            gate_name="task", command="pytest -q", footprint=["tools/"],
            baseline_sha=OTHER_SHA, result_sha=SHA, out_dir=tmp_path,
            preconditions=report,
            runner=lambda cmd: ("3 passed in 0.1s", 0),
            utc=FIXED_UTC,
        )
    assert summary["preconditionsAsserted"] is True
    assert summary["preconditionPath"].endswith("preconditions.json")
    assert (tmp_path / "RESULT.json").exists()


def test_gate_emit_without_a_report_says_not_asserted_never_passed(tmp_path: Path):
    """The declared BC mode — the summary states the caller never said (D136 honesty)."""
    import gate_emit

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        summary = gate_emit.emit_gate_artifacts(
            gate_name="task", command="pytest -q", footprint=["tools/"],
            baseline_sha=OTHER_SHA, result_sha=SHA, out_dir=tmp_path,
            runner=lambda cmd: ("3 passed in 0.1s", 0), utc=FIXED_UTC,
        )
    assert summary["preconditionsAsserted"] is False
    assert summary["preconditionPath"] is None


def test_combine_orders_reports_deterministically():
    reports = [
        gp.final_gate(final_facts(), utc=FIXED_UTC),
        gp.task_gate(task_facts(), utc=FIXED_UTC),
        gp.freeze_gate(freeze_facts(), utc=FIXED_UTC),
    ]
    assert [r.gate for r in gp.combine(reports)] == [
        gp.GATE_FINAL, gp.GATE_FREEZE, gp.GATE_TASK,
    ]
    assert gp.combine(reports) == gp.combine(list(reversed(reports)))
