"""The 6-seam deterministic advisor smoke — promoted from the pre-merge battery.

Provenance: the advisor-executor pre-merge proof (D167, PR #39) ran a 6-seam
deterministic smoke twice and recorded byte-equal results (digest ``ac81085c83748ae1``,
``.kata/smoke-advisor.json``) — but the smoke SCRIPT lived only in a session scratchpad
and was never committed. This module promotes it into the suite:

- the ``.kata/`` fixture dependency is REPLACED by constructed artifacts (``tmp_path``
  advice dirs + expected values baked below as constants, transcribed from the recorded
  smoke artifact);
- every seam is computed LIVE against the real engines and asserted equal to the baked
  expected values;
- the double-run determinism claim is re-proven in-process: two independent passes must
  serialize byte-equal (``sort_keys`` canonical JSON) and hash to the same digest.

HONESTY (PD-2): the original scratchpad script's exact serialization recipe was not
preserved, so THIS module's digest is not asserted against the historical
``ac81085c83748ae1`` — equality is pinned on the recorded seam VALUES (stronger: every
field is named) plus in-process double-run byte-equality.

Seams (mirroring the recorded artifact's keys):
  1. gate matrix        — ``advisor_status`` across mode × anchor × event + NO-FIRE
                          reasons + 7 poison blocks raising fail-closed
  2. rung table         — ``advisor_rung_of`` (fable-target for every sub-fable anchor)
  3. budget recount     — ``recount_from_advisor_decisions`` + the reserved-event sets
  4. telemetry          — ``ledger_fragment`` shape
  5. artifact contract  — once-guard / next-ordinal / grill-seeded spend, computed from
                          a CONSTRUCTED advice dir (no live ``.kata/`` read)
  6. advise-first loop  — the deferral protocol end-to-end across BOTH engines
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import kata_adaptive as kad
import kata_advisor as ka
import kata_models as km

# ---------------------------------------------------------------------------
# Expected values — transcribed VERBATIM from the recorded smoke artifact
# (.kata/smoke-advisor.json, digest ac81085c83748ae1); constructed constants,
# not a fixture read.
# ---------------------------------------------------------------------------

_ADV_BLOCK = {"enabled": True, "approved": True, "grantedMode": "advanced",
              "budget": {"calls": 10, "reserved": 2}}
_STD_BLOCK = {"enabled": True, "approved": True, "grantedMode": "standard",
              "budget": {"calls": 5, "reserved": 1}}

_ADV_ANCHORS = {"claude-fable-5": None, "haiku": "fable", "mythos": None,
                "opus": "fable", "sonnet": "fable"}

_EXPECTED_SEAM2 = {
    "claude-fable-5": None,
    "claude-haiku-4-5-20251001": "fable",
    "claude-opus-4-8": "fable",
    "fable": None,
    "haiku": "fable",
    "mythos": None,
    "opus": "fable",
    "sonnet": "fable",
    "unknown-model": None,
}

# Seven poison blocks — each present-but-malformed, each must RAISE (D136 fail-closed).
_POISONS = [
    {"enabled": True, "approved": True, "budget": {"calls": 5, "reserved": 1}, "extraKey": 1},
    {"approved": True, "budget": {"calls": 5, "reserved": 1}},                      # enabled missing
    {"enabled": 1, "approved": True, "budget": {"calls": 5, "reserved": 1}},        # enabled non-bool
    {"enabled": True, "approved": "yes", "budget": {"calls": 5, "reserved": 1}},    # approved non-bool
    {"enabled": True, "approved": True, "grantedMode": "essential",
     "budget": {"calls": 5, "reserved": 1}},                                        # bad grantedMode
    {"enabled": True, "approved": True},                                            # budget missing
    {"enabled": True, "approved": True, "budget": {"calls": 1, "reserved": 2}},     # reserved > calls
]


def _build_results(advice_dir: Path) -> dict:
    """Compute all six seams live. Pure function of the constructed *advice_dir*."""
    results: dict = {}

    # --- seam 1: the gate matrix -------------------------------------------------
    matrix: dict = {}
    for anchor in _ADV_ANCHORS:
        for event in km.ADVISOR_EVENTS:
            s = km.advisor_status(_ADV_BLOCK, anchor, family="auto", mode="advanced", event=event)
            matrix[f"adv|{anchor}|{event}"] = [s["fires"], s["reason"], s["rung"]]
    s = km.advisor_status(_STD_BLOCK, "opus", family="auto", mode="standard",
                          event="advisor-fail-threshold")
    matrix["std|opus|fail-threshold"] = [s["fires"], s["reason"], s["rung"]]
    matrix["nofire|absent"] = km.advisor_status(None, "opus", family="auto", mode="advanced",
                                                event="advisor-fail-threshold")["reason"]
    matrix["nofire|not-enabled"] = km.advisor_status(
        {**_ADV_BLOCK, "enabled": False}, "opus", family="auto", mode="advanced",
        event="advisor-fail-threshold")["reason"]
    matrix["nofire|not-approved"] = km.advisor_status(
        {**_ADV_BLOCK, "approved": False}, "opus", family="auto", mode="advanced",
        event="advisor-fail-threshold")["reason"]
    matrix["nofire|mode-excluded"] = km.advisor_status(
        _ADV_BLOCK, "opus", family="auto", mode="essential",
        event="advisor-fail-threshold")["reason"]
    matrix["nofire|unknown-event"] = km.advisor_status(
        _ADV_BLOCK, "opus", family="auto", mode="advanced", event="not-an-event")["reason"]
    raised = 0
    for poison in _POISONS:
        try:
            km.advisor_status(poison, "opus", family="auto", mode="advanced",
                              event="advisor-fail-threshold")
        except ValueError:
            raised += 1
    matrix["poisons-raised"] = f"{raised}/{len(_POISONS)}"
    results["seam1_gate_matrix"] = matrix

    # --- seam 2: the rung table --------------------------------------------------
    results["seam2_rung_table"] = {
        anchor: km.advisor_rung_of("auto", anchor) for anchor in _EXPECTED_SEAM2
    }

    # --- seam 3: budget recount + reserved sets ----------------------------------
    trail = [ka.render_advisor_decision(f"t{i}-1", "advisor-worker-request") for i in range(1, 5)]
    trail.append(ka.render_advisor_decision("t9-1", "advisor-fix-loop-ceiling"))
    trail.append("tier: T1 sonnet->opus reason failbump")  # non-advisor line — ignored
    results["seam3_budget_recount"] = {
        "recount": ka.recount_from_advisor_decisions(trail),
        "reserved_sets": {mode: sorted(events)
                          for mode, events in ka.ADVISOR_RESERVED_EVENTS.items()},
    }

    # --- seam 4: the telemetry fragment ------------------------------------------
    st = ka.new_advisor_state()
    ka.record_advisor_spend(st, "advisor-fail-threshold")
    ka.record_outcome(st, "t1-1", "advised-fail-bumped")
    results["seam4_telemetry"] = {"fragment": ka.ledger_fragment(st, 5)}

    # --- seam 5: the artifact contract (constructed advice dir) ------------------
    # Conventions under pin (kata-orchestrate § Advisor consult): standing advice for
    # a task = any <taskId>-<n>.json artifact (the once-guard); the next artifact
    # ordinal = max(n)+1; run-start spend seeding = count of grill-*.json artifacts.
    task_files = sorted(advice_dir.glob("live-exercise-1-*.json"))
    ordinals = [int(m.group(1)) for f in task_files
                if (m := re.fullmatch(r"live-exercise-1-(\d+)\.json", f.name))]
    results["seam5_artifacts"] = {
        "once_guard_armed": bool(task_files),
        "next_ordinal": (max(ordinals) + 1) if ordinals else 1,
        "grill_seeded_spend": len(list(advice_dir.glob("grill-*.json"))),
    }

    # --- seam 6: the advise-first loop, end-to-end across both engines -----------
    state, cfg = kad.new_state(), kad.resolve_adaptive_config({})
    advisor_state = ka.new_advisor_state()
    decisions: list[str] = []
    task = "T-hard-1"
    # two failures → threshold
    kad.record_gate_result(state, task, "impl", accepted=False, first_pass=False, downshifted=False)
    kad.record_gate_result(state, task, "impl", accepted=False, first_pass=False, downshifted=False)
    assert kad.bump_pending(state, cfg, task) is True
    # advise-first: consult fires, spend committed, DECISION rendered; NO modulate_step
    # (consult id = the task id — the recorded smoke's convention)
    ka.record_advisor_spend(advisor_state, "advisor-fail-threshold")
    ka.record_outcome(advisor_state, task, None)
    decisions.append(ka.render_advisor_decision(task, "advisor-fail-threshold"))
    # the advised same-rung attempt fails; bump-second: the normal path consumes
    kad.record_gate_result(state, task, "impl", accepted=False, first_pass=False, downshifted=False)
    delta = kad.modulate_step(cfg, state, task_id=task, task_class="impl", work_class="coding")
    ka.record_outcome(advisor_state, task, "advised-fail-bumped")
    results["seam6_advise_first_loop"] = {
        "delta": delta,
        "outcome": advisor_state["outcomes"][task],
        "recount_used": ka.recount_from_advisor_decisions(decisions)["used"],
        "fragment": ka.ledger_fragment(advisor_state, 5),
    }

    return results


def _make_advice_dir(tmp_path: Path) -> Path:
    """Construct the advice-dir fixture (replaces the original .kata/ dependency)."""
    d = tmp_path / "advice"
    d.mkdir(parents=True)
    (d / "live-exercise-1-1.json").write_text(
        json.dumps({"request": {"taskId": "live-exercise-1"}, "response": {}}),
        encoding="utf-8",
    )
    return d


def test_six_seams_match_the_recorded_smoke(tmp_path):
    """Every seam, computed live, equals the recorded pre-merge smoke values."""
    results = _build_results(_make_advice_dir(tmp_path))

    # seam 1 — the gate matrix
    m = results["seam1_gate_matrix"]
    for anchor, rung in _ADV_ANCHORS.items():
        for event in km.ADVISOR_EVENTS:
            assert m[f"adv|{anchor}|{event}"] == [True, "fires", rung], (anchor, event)
    assert m["std|opus|fail-threshold"] == [True, "fires", "fable"]
    assert m["nofire|absent"] == "absent"
    assert m["nofire|not-enabled"] == "not-enabled"
    assert m["nofire|not-approved"] == "not-approved"
    assert m["nofire|mode-excluded"] == "mode-excluded"
    assert m["nofire|unknown-event"] == "unknown-event"
    assert m["poisons-raised"] == "7/7"

    # seam 2 — the rung table
    assert results["seam2_rung_table"] == _EXPECTED_SEAM2

    # seam 3 — budget recount + reserved sets
    assert results["seam3_budget_recount"] == {
        "recount": {"used": 5, "byEvent": {"advisor-fix-loop-ceiling": 1,
                                           "advisor-worker-request": 4}},
        "reserved_sets": {"standard": ["advisor-fix-loop-ceiling"],
                          "advanced": ["advisor-fix-loop-ceiling",
                                       "advisor-reroll-grounding"]},
    }

    # seam 4 — the telemetry fragment
    assert results["seam4_telemetry"] == {"fragment": {
        "consults": [{"id": "t1-1", "outcome": "advised-fail-bumped"}],
        "byEvent": {"advisor-fail-threshold": 1},
        "budgetUsed": 1, "budgetCap": 5, "lapses": [],
    }}

    # seam 5 — the artifact contract (from the CONSTRUCTED dir)
    assert results["seam5_artifacts"] == {
        "once_guard_armed": True, "next_ordinal": 2, "grill_seeded_spend": 0,
    }

    # seam 6 — the advise-first loop
    s6 = results["seam6_advise_first_loop"]
    assert s6["delta"] == 1
    assert s6["outcome"] == "advised-fail-bumped"
    assert s6["recount_used"] == 1
    assert s6["fragment"] == {
        "consults": [{"id": "T-hard-1", "outcome": "advised-fail-bumped"}],
        "byEvent": {"advisor-fail-threshold": 1},
        "budgetUsed": 1, "budgetCap": 5, "lapses": [],
    }


def test_double_run_is_byte_equal(tmp_path):
    """The determinism proof, in-process: two independent passes serialize byte-equal
    and hash identically (the pre-merge battery's double-run claim, re-proven)."""
    dir_a = _make_advice_dir(tmp_path / "a")
    dir_b = _make_advice_dir(tmp_path / "b")
    blob_a = json.dumps(_build_results(dir_a), sort_keys=True, separators=(",", ":"))
    blob_b = json.dumps(_build_results(dir_b), sort_keys=True, separators=(",", ":"))
    assert blob_a == blob_b
    digest_a = hashlib.sha256(blob_a.encode("utf-8")).hexdigest()[:16]
    digest_b = hashlib.sha256(blob_b.encode("utf-8")).hexdigest()[:16]
    assert digest_a == digest_b
