"""test_kata_advisor.py — the pure advisor-consult engine (TDD + D136 guards, DESIGN §6).

Every RAISES clause in the DESIGN §3.5/§3.9 contract has a named test proving loud
failure on malformed input; the reservation boundary is mutation-guarded (a non-reserved
event is denied at ``remaining == reserved`` — flip ``>`` to ``>=`` and this test fails);
the ``advisor:`` DECISION trail round-trips render → recount byte-stable; and a structural
test pins the S-11b/S-16 promise that ``tools/kata_adaptive.py`` is BYTE-UNTOUCHED (never
imported-for-mutation, edited, or shadowed by this module).
"""
from __future__ import annotations

from pathlib import Path

import pytest

import kata_advisor as ka

# ---------------------------------------------------------------------------
# 1. State shape (§3.5)
# ---------------------------------------------------------------------------


def test_new_advisor_state_shape():
    state = ka.new_advisor_state()
    assert state == {"used": 0, "byEvent": {}, "lapses": [], "outcomes": {}}


def test_new_advisor_state_fresh_containers_each_call():
    a, b = ka.new_advisor_state(), ka.new_advisor_state()
    a["byEvent"]["x"] = 1
    a["lapses"].append("y")
    a["outcomes"]["z"] = None
    assert b == {"used": 0, "byEvent": {}, "lapses": [], "outcomes": {}}


@pytest.mark.parametrize(
    "consumer",
    [
        lambda s: ka.can_spend_advisor(5, 1, ("e",), s, "e"),
        lambda s: ka.record_advisor_spend(s, "advisor-fail-threshold"),
        lambda s: ka.record_outcome(s, "T1-1", None),
        lambda s: ka.ledger_fragment(s, 5),
    ],
)
@pytest.mark.parametrize("bad", [None, {}, [], "state", {"used": 0}, 5])
def test_malformed_state_raises_in_every_consumer(consumer, bad):
    with pytest.raises(ka.AdvisorError):
        consumer(bad)


# ---------------------------------------------------------------------------
# 2. Budget resolution (§3.5 / §5 — fail-closed, NO permissive fallback)
# ---------------------------------------------------------------------------


def test_resolve_budget_standard_composition():
    # The DESIGN §3.4 standard bootstrap composition.
    assert ka.resolve_advisor_budget({"budget": {"calls": 5, "reserved": 1}}) == (5, 1)


def test_resolve_budget_advanced_composition():
    # The DESIGN §3.4 advanced bootstrap composition.
    assert ka.resolve_advisor_budget({"budget": {"calls": 10, "reserved": 2}}) == (10, 2)


def test_resolve_budget_zero_is_legal():
    assert ka.resolve_advisor_budget({"budget": {"calls": 0, "reserved": 0}}) == (0, 0)


def test_resolve_budget_absent_budget_raises():
    # The G-6 defaults are bootstrap constants, NOT resolver fallbacks (§5).
    with pytest.raises(ka.AdvisorError, match="REQUIRES 'budget'"):
        ka.resolve_advisor_budget({"enabled": True})


def test_resolve_budget_non_dict_advisor_raises():
    with pytest.raises(ka.AdvisorError):
        ka.resolve_advisor_budget(None)


def test_resolve_budget_non_dict_budget_raises():
    with pytest.raises(ka.AdvisorError):
        ka.resolve_advisor_budget({"budget": [5, 1]})


def test_resolve_budget_unknown_budget_key_raises():
    with pytest.raises(ka.AdvisorError, match="unknown budget key"):
        ka.resolve_advisor_budget({"budget": {"calls": 5, "reserved": 1, "tokens": 3}})


@pytest.mark.parametrize("missing", ["calls", "reserved"])
def test_resolve_budget_missing_field_raises(missing):
    budget = {"calls": 5, "reserved": 1}
    del budget[missing]
    with pytest.raises(ka.AdvisorError):
        ka.resolve_advisor_budget({"budget": budget})


@pytest.mark.parametrize("bad", [True, False, 1.5, "5", None, -1])
def test_resolve_budget_non_int_calls_raises(bad):
    # bool is rejected (subclasses int); floats/strings/None/negatives too.
    with pytest.raises(ka.AdvisorError):
        ka.resolve_advisor_budget({"budget": {"calls": bad, "reserved": 0}})


@pytest.mark.parametrize("bad", [True, 1.5, "1", -1])
def test_resolve_budget_non_int_reserved_raises(bad):
    with pytest.raises(ka.AdvisorError):
        ka.resolve_advisor_budget({"budget": {"calls": 5, "reserved": bad}})


def test_resolve_budget_reserved_gt_calls_raises():
    with pytest.raises(ka.AdvisorError, match="must be <="):
        ka.resolve_advisor_budget({"budget": {"calls": 2, "reserved": 3}})


# ---------------------------------------------------------------------------
# 3. Reserved-event sets (S-13 — exact)
# ---------------------------------------------------------------------------


def test_reserved_event_sets_exact():
    assert ka.ADVISOR_RESERVED_EVENTS == {
        "standard": ("advisor-fix-loop-ceiling",),
        "advanced": ("advisor-fix-loop-ceiling", "advisor-reroll-grounding"),
    }


# ---------------------------------------------------------------------------
# 4. FCFS + floor reservation (§3.5 — the kata_adaptive.can_spend SHAPE)
# ---------------------------------------------------------------------------


def test_can_spend_non_reserved_denied_at_reserved_boundary():
    """MUTATION GUARD: a non-reserved event needs remaining > reserved — denied at the
    boundary remaining == reserved. Flip ``>`` to ``>=`` in can_spend_advisor and this
    fails."""
    reserved = ka.ADVISOR_RESERVED_EVENTS["advanced"]  # ("...ceiling", "...grounding")
    state = ka.new_advisor_state()
    state["used"] = 8  # calls=10 ⇒ remaining=2 == reserved_count(2)
    assert ka.can_spend_advisor(10, 2, reserved, state, "advisor-fail-threshold") is False
    # One fewer spent ⇒ remaining=3 > 2 ⇒ allowed.
    state["used"] = 7
    assert ka.can_spend_advisor(10, 2, reserved, state, "advisor-fail-threshold") is True


def test_can_spend_reserved_event_spends_to_zero():
    reserved = ka.ADVISOR_RESERVED_EVENTS["standard"]  # ("advisor-fix-loop-ceiling",)
    state = ka.new_advisor_state()
    state["used"] = 4  # calls=5 ⇒ remaining=1
    # Non-reserved is already denied here (1 > 1 is False)…
    assert ka.can_spend_advisor(5, 1, reserved, state, "advisor-fail-threshold") is False
    # …but the reserved event may draw the last call (remaining >= 1).
    assert ka.can_spend_advisor(5, 1, reserved, state, "advisor-fix-loop-ceiling") is True
    state["used"] = 5  # remaining=0 ⇒ even the reserved event is exhausted.
    assert ka.can_spend_advisor(5, 1, reserved, state, "advisor-fix-loop-ceiling") is False


def test_can_spend_is_read_only_no_spend_on_denial():
    state = ka.new_advisor_state()
    state["used"] = 5
    before = dict(state)
    assert ka.can_spend_advisor(5, 1, ("advisor-fix-loop-ceiling",), state, "x") is False
    assert state == before  # denial records NOTHING (spend is a separate commit)


def test_can_spend_zero_budget_always_denies():
    state = ka.new_advisor_state()
    assert ka.can_spend_advisor(0, 0, ("advisor-fix-loop-ceiling",), state, "advisor-fix-loop-ceiling") is False
    assert ka.can_spend_advisor(0, 0, ("advisor-fix-loop-ceiling",), state, "other") is False


@pytest.mark.parametrize("bad", [True, 1.5, "5", -1])
def test_can_spend_bad_calls_raises(bad):
    with pytest.raises(ka.AdvisorError):
        ka.can_spend_advisor(bad, 1, ("e",), ka.new_advisor_state(), "e")


@pytest.mark.parametrize("bad", [True, 1.5, "1", -1])
def test_can_spend_bad_reserved_count_raises(bad):
    with pytest.raises(ka.AdvisorError):
        ka.can_spend_advisor(5, bad, ("e",), ka.new_advisor_state(), "e")


@pytest.mark.parametrize("bad", [None, "e", 3])
def test_can_spend_bad_reserved_events_raises(bad):
    with pytest.raises(ka.AdvisorError):
        ka.can_spend_advisor(5, 1, bad, ka.new_advisor_state(), "e")


# ---------------------------------------------------------------------------
# 5. Grant-before-dispatch spend commit (S-19a)
# ---------------------------------------------------------------------------


def test_record_advisor_spend_commits_used_and_by_event():
    state = ka.new_advisor_state()
    ka.record_advisor_spend(state, "advisor-fail-threshold")
    ka.record_advisor_spend(state, "advisor-fail-threshold")
    ka.record_advisor_spend(state, "advisor-fix-loop-ceiling")
    assert state["used"] == 3
    assert state["byEvent"] == {"advisor-fail-threshold": 2, "advisor-fix-loop-ceiling": 1}


@pytest.mark.parametrize("bad", [None, "", "has space", 5, True])
def test_record_advisor_spend_bad_event_raises(bad):
    with pytest.raises(ka.AdvisorError):
        ka.record_advisor_spend(ka.new_advisor_state(), bad)


def test_spend_committed_before_outcome_known():
    """S-19a: the spend commit is independent of any later outcome pairing — a granted
    consult consumes its call even if it ultimately fails (no retry-mining)."""
    state = ka.new_advisor_state()
    ka.record_advisor_spend(state, "advisor-fail-threshold")
    assert state["used"] == 1
    # A subsequent failure outcome does not refund the spend.
    ka.record_outcome(state, "T1-1", "advised-fail-ceiling")
    assert state["used"] == 1


# ---------------------------------------------------------------------------
# 6. EV-1 outcome pairing (§3.9)
# ---------------------------------------------------------------------------


def test_advisor_outcomes_enum_exact():
    assert ka.ADVISOR_OUTCOMES == (
        "advised-pass",
        "advised-fail-bumped",
        "advised-fail-ceiling",
    )


@pytest.mark.parametrize("outcome", list(ka.ADVISOR_OUTCOMES) + [None])
def test_record_outcome_accepts_enum_and_pending_null(outcome):
    state = ka.new_advisor_state()
    ka.record_outcome(state, "T4-2", outcome)
    assert state["outcomes"] == {"T4-2": outcome}


@pytest.mark.parametrize("bad", ["pass", "advised", "PASS", "advised_pass", "", 1, True])
def test_record_outcome_unknown_raises(bad):
    with pytest.raises(ka.AdvisorError):
        ka.record_outcome(ka.new_advisor_state(), "T1-1", bad)


@pytest.mark.parametrize("bad", [None, "", "has space", 5])
def test_record_outcome_bad_consult_id_raises(bad):
    with pytest.raises(ka.AdvisorError):
        ka.record_outcome(ka.new_advisor_state(), bad, None)


def test_record_outcome_null_pending_then_resolved():
    state = ka.new_advisor_state()
    ka.record_outcome(state, "T1-1", None)  # pending
    assert state["outcomes"]["T1-1"] is None
    ka.record_outcome(state, "T1-1", "advised-pass")  # resolves
    assert state["outcomes"]["T1-1"] == "advised-pass"


# ---------------------------------------------------------------------------
# 7. DECISION trail + durable recount (S-23b)
# ---------------------------------------------------------------------------


def test_render_advisor_decision_format():
    assert (
        ka.render_advisor_decision("T3-1", "advisor-fail-threshold")
        == "advisor: T3-1 event advisor-fail-threshold"
    )


@pytest.mark.parametrize("bad", [None, "", "has space", 5, True])
def test_render_advisor_decision_bad_field_raises(bad):
    with pytest.raises(ka.AdvisorError):
        ka.render_advisor_decision(bad, "advisor-fail-threshold")
    with pytest.raises(ka.AdvisorError):
        ka.render_advisor_decision("T1-1", bad)


def test_recount_round_trip_recovers_used_and_by_event():
    payloads = [
        ka.render_advisor_decision("T1-1", "advisor-fail-threshold"),
        ka.render_advisor_decision("T1-2", "advisor-fail-threshold"),
        ka.render_advisor_decision("T2-1", "advisor-fix-loop-ceiling"),
    ]
    assert ka.recount_from_advisor_decisions(payloads) == {
        "used": 3,
        "byEvent": {"advisor-fail-threshold": 2, "advisor-fix-loop-ceiling": 1},
    }


def test_recount_ignores_other_decision_lines():
    payloads = [
        "tier: T1 sonnet->opus reason failbump",  # a kata_adaptive line — ignored
        "some other DECISION",
        ka.render_advisor_decision("T1-1", "advisor-worker-request"),
    ]
    assert ka.recount_from_advisor_decisions(payloads) == {
        "used": 1,
        "byEvent": {"advisor-worker-request": 1},
    }


def test_recount_empty_is_zero():
    assert ka.recount_from_advisor_decisions([]) == {"used": 0, "byEvent": {}}


@pytest.mark.parametrize(
    "bad",
    [
        "advisor: T1-1 advisor-fail-threshold",  # missing 'event' keyword (3 tokens)
        "advisor: T1-1 event a b",  # too many tokens
        "advisor: T1-1 vent advisor-x",  # wrong keyword
        "advisor:",  # bare
    ],
)
def test_recount_malformed_advisor_line_raises(bad):
    with pytest.raises(ka.AdvisorError):
        ka.recount_from_advisor_decisions([bad])


def test_recount_non_string_payload_raises():
    with pytest.raises(ka.AdvisorError):
        ka.recount_from_advisor_decisions([None])


def test_recount_is_deterministic_same_inputs_same_output():
    payloads = [ka.render_advisor_decision(f"T{i}-1", "advisor-fail-threshold") for i in range(5)]
    assert ka.recount_from_advisor_decisions(payloads) == ka.recount_from_advisor_decisions(payloads)


# ---------------------------------------------------------------------------
# 8. Ledger fragment (§3.9 — deterministic ordering)
# ---------------------------------------------------------------------------


def test_ledger_fragment_shape():
    state = ka.new_advisor_state()
    ka.record_advisor_spend(state, "advisor-fail-threshold")
    ka.record_outcome(state, "T1-1", "advised-pass")
    state["lapses"].append("budget-exhausted")
    frag = ka.ledger_fragment(state, 5)
    assert frag == {
        "consults": [{"id": "T1-1", "outcome": "advised-pass"}],
        "byEvent": {"advisor-fail-threshold": 1},
        "budgetUsed": 1,
        "budgetCap": 5,
        "lapses": ["budget-exhausted"],
    }


def test_ledger_fragment_sorts_consults_and_by_event_deterministically():
    state = ka.new_advisor_state()
    # Insert out of order; the fragment must sort at the boundary.
    for cid in ("T3-1", "T1-2", "T1-1"):
        ka.record_outcome(state, cid, None)
    for ev in ("advisor-worker-request", "advisor-fail-threshold"):
        ka.record_advisor_spend(state, ev)
    frag = ka.ledger_fragment(state, 10)
    assert [c["id"] for c in frag["consults"]] == ["T1-1", "T1-2", "T3-1"]
    assert list(frag["byEvent"].keys()) == ["advisor-fail-threshold", "advisor-worker-request"]


def test_ledger_fragment_carries_null_pending_outcome():
    state = ka.new_advisor_state()
    ka.record_outcome(state, "T2-1", None)
    frag = ka.ledger_fragment(state, 5)
    assert frag["consults"] == [{"id": "T2-1", "outcome": None}]


@pytest.mark.parametrize("bad", [True, 1.5, "5", -1])
def test_ledger_fragment_bad_cap_raises(bad):
    with pytest.raises(ka.AdvisorError):
        ka.ledger_fragment(ka.new_advisor_state(), bad)


# ---------------------------------------------------------------------------
# 9. Byte-untouched guard (S-11b / S-16 — kata_adaptive never imported/mutated)
# ---------------------------------------------------------------------------


def test_kata_advisor_does_not_import_or_reference_kata_adaptive():
    """S-11b: the adaptive engine is only OBSERVED and DEFERRED-AROUND by the
    orchestrator, never imported/edited/shadowed by this pure engine. (Docstring
    mentions of the name are expected — the guard is on import + module binding.)"""
    src = Path(ka.__file__).read_text(encoding="utf-8")
    assert "import kata_adaptive" not in src
    assert "from kata_adaptive" not in src
    assert not hasattr(ka, "kata_adaptive")  # no module-level binding, no shadow


def test_kata_advisor_is_stdlib_only():
    """DESIGN §5: kata_advisor is pure, stdlib-only — no first-party engine imports."""
    src = Path(ka.__file__).read_text(encoding="utf-8")
    for banned in ("import kata_models", "import kata_board", "import kata_telemetry", "import footprint"):
        assert banned not in src


# ---------------------------------------------------------------------------
# 10. The advise-first DEFERRAL seam — executable owner of the orchestrator
#     protocol (kata-orchestrate SKILL.md § advise-first / bump-second).
#
# These pins realize the pinning-test sketch from the advisor's own live consult
# (.kata/advice/live-exercise-1-1.json, archived verbatim; grant: operator
# in-session DECISION, live-exercise-1). They simulate the CONDUCTOR's deferral
# protocol as code against the REAL engines — kata_adaptive is imported here
# deliberately (this is the seam-owner test, NOT the pure kata_advisor engine;
# the S-11b byte-untouched guard above still holds for kata_advisor itself).
#
# The protocol under pin (S-11b — orchestrator-side deferral, engine untouched):
#   failure → failure → bump_pending OBSERVED True → advisor consult fires FIRST
#   (advisor-fail-threshold) → redispatch at the SAME rung with advice folded in
#   (modulate_step NOT called — the deferral) → the advised attempt fails →
#   normal path: modulate_step consumes the bump (+1) exactly once.
# ---------------------------------------------------------------------------


class TestAdvisorDeferralCompat:
    """The three consult-sketch pins: observe≠consume · single consume · recount-invisible."""

    @staticmethod
    def _cfg():
        import kata_adaptive

        return kata_adaptive.resolve_adaptive_config({})  # enabled, failBumpAt=2 default

    def test_repeated_observation_never_consumes(self):
        """Pin 1 (observe≠consume): the deferral window observes bump_pending —
        repeatedly, alongside the full advisor-side consult bookkeeping — and NONE
        of it consumes the bump or touches the adaptive counters."""
        import kata_adaptive as kad

        state, cfg = kad.new_state(), self._cfg()
        kad.record_gate_result(state, "T1", "impl", accepted=False, first_pass=False, downshifted=False)
        kad.record_gate_result(state, "T1", "impl", accepted=False, first_pass=False, downshifted=False)

        # The conductor's deferral-window activity: observe the pending bump (many
        # times — status renders, board notes, re-checks) and run the WHOLE advisor
        # consult on the advisor engine. The adaptive engine must be inert throughout.
        advisor_state = ka.new_advisor_state()
        for _ in range(5):
            assert kad.bump_pending(state, cfg, "T1") is True  # pure read, idempotent
        ka.record_advisor_spend(advisor_state, "advisor-fail-threshold")
        ka.record_outcome(advisor_state, "T1-1", None)  # consult dispatched, outcome pending

        assert state["bumped"] == {}                      # never consumed by observation
        assert state["bumpCounters"]["T1"] == 2           # untouched by the consult
        assert kad.bump_pending(state, cfg, "T1") is True  # still pending after it all

    def test_deferral_window_then_single_consume(self):
        """Pin 2 (exactly-one +1): after the advised same-rung attempt fails, the
        normal path consumes the bump ONCE; double-bump is structurally impossible
        (delta domain {-1,0,+1}; the bumped mark blocks re-arm forever)."""
        import kata_adaptive as kad

        state, cfg = kad.new_state(), self._cfg()
        kad.record_gate_result(state, "T1", "impl", accepted=False, first_pass=False, downshifted=False)
        kad.record_gate_result(state, "T1", "impl", accepted=False, first_pass=False, downshifted=False)
        assert kad.bump_pending(state, cfg, "T1") is True

        # DEFERRAL: the advised redispatch runs at the PRIOR rung — the conductor
        # does NOT call modulate_step for that one dispatch. The advised attempt
        # then FAILS and is recorded normally (S-15e: no special-casing).
        kad.record_gate_result(state, "T1", "impl", accepted=False, first_pass=False, downshifted=False)
        assert state["bumped"] == {}                      # still unconsumed after the advised failure
        assert state["bumpCounters"]["T1"] == 3           # 2→3; the >= boundary tolerates it

        # NEXT dispatch: the normal path consumes — exactly one +1.
        delta = kad.modulate_step(cfg, state, task_id="T1", task_class="impl", work_class="coding")
        assert delta == 1
        assert state["bumped"]["T1"] is True

        # EV-1 closes on the advisor side; the adaptive engine saw nothing special.
        advisor_state = ka.new_advisor_state()
        ka.record_advisor_spend(advisor_state, "advisor-fail-threshold")
        ka.record_outcome(advisor_state, "T1-1", "advised-fail-bumped")

        # Structural no-double-bump: the mark blocks re-arm; later attempts stay at
        # +1 (the SAME consumed bump riding out, never a second one) even after
        # further rejections.
        assert kad.bump_pending(state, cfg, "T1") is False
        kad.record_gate_result(state, "T1", "impl", accepted=False, first_pass=False, downshifted=False)
        assert kad.bump_pending(state, cfg, "T1") is False
        assert kad.modulate_step(cfg, state, task_id="T1", task_class="impl", work_class="coding") == 1

    def test_deferral_invisible_to_recount(self):
        """Pin 3 (mid-deferral recount carries no mark): the DECISION trail during
        the deferral window holds the advisor SPEND line but NO tier failbump line —
        a restart mid-deferral rebuilds counters WITHOUT the bump mark (the accepted
        under-adapt loss, S-11b corollary) while the advisor spend recounts fully.
        The failbump line is emitted ONLY at actual consume."""
        import kata_adaptive as kad

        # Mid-deferral trail: the consult's spend DECISION exists; no failbump line
        # (the loop NEVER emits it at earn/deferral time — consult risk 3).
        mid_deferral_trail = [
            ka.render_advisor_decision("T1-1", "advisor-fail-threshold"),
        ]
        adaptive_recount = kad.recount_from_decisions(mid_deferral_trail, "fable")
        assert adaptive_recount["bumped"] == {}           # no mark — bump re-earned post-restart
        advisor_recount = ka.recount_from_advisor_decisions(mid_deferral_trail)
        assert advisor_recount["used"] == 1               # the spend trail IS durable
        assert advisor_recount["byEvent"] == {"advisor-fail-threshold": 1}

        # Post-consume trail: the conductor emitted the failbump line at consume —
        # NOW the recount carries the once-per-task mark.
        post_consume_trail = mid_deferral_trail + [
            kad.render_tier_decision("T1", "sonnet", "opus", "failbump"),
        ]
        adaptive_recount = kad.recount_from_decisions(post_consume_trail, "fable")
        assert adaptive_recount["bumped"] == {"T1": True}
        assert adaptive_recount["budgetSpent"] == 0       # failbump is not a premium spend
