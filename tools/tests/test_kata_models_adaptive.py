"""test_kata_models_adaptive.py — TDD suite for Amendment #2 (adaptive premium scope).

Covers the adaptive-tiering surface added to ``kata_models`` (D150 initiative;
model-tiering DESIGN Amendment #2 / adaptive-tiering DESIGN AT-L5/L6/L15/L17/L21):

  * ``ADAPTIVE_EVENTS`` / ``ADAPTIVE_EVENT_SITES`` — the ordered event registry
    (AT-L5; the tuple order IS the spend-priority documentation, AT-L13).
  * ``classify_premium_scope(scope)`` — TYPE-DISPATCHED scope forms (AT-L15):
    LIST ⇒ "classes" (v0.2.1 byte-for-byte), OBJECT ⇒ "events", anything else
    ⇒ RAISE (fail-closed, AT-L21/GB12/D45).
  * ``premium_status(..., event=...)`` / ``resolve(..., event=...)`` — conjunct
    #2 reads "event ∈ scope.events" in the events form; the other three
    conjuncts are UNTOUCHED.
  * ``premium_rung_of(family, anchor)`` — family-agnostic one-rung-above helper
    (AT-L17).

The existing ``test_kata_models.py`` + ``test_kata_models_premium.py`` suites
are the BC canaries and are deliberately left byte-unchanged — adaptive
coverage lives here, in a sibling file.

Run:
    cd C:/Dev/Projects/KataHarness/tools
    uv run pytest tests/test_kata_models_adaptive.py -v

Mutation-proof map (each disable → the named test goes RED → revert):
    MP-A1  events-form conjunct #2       → test_events_form_fires_only_when_event_in_scope
    MP-A2  event-not-in-scope no-fire    → test_event_not_in_scope_events_no_fire
    MP-A3  events [] legal no-op         → test_empty_events_list_never_fires
    MP-A4  absent events key RAISE       → test_absent_events_key_raises
    MP-A5  unknown event name RAISE      → test_unknown_event_name_raises
    MP-A6  unknown scope key RAISE       → test_unknown_scope_key_raises
    MP-A7  budget shape guard            → test_non_int_budget_calls_raises
    MP-A8  class-query vs events form    → test_class_query_against_events_form_no_fire_not_crash
    MP-A9  registry order pin            → test_adaptive_events_order_pinned
    MP-A10 premium_rung_of relation      → test_premium_rung_of_anthropic_opus_is_fable
"""
from __future__ import annotations

import pytest

import kata_models as km

ANTHROPIC = "anthropic"

_CRITICAL_SKILL = "kata-grill-essential"  # critical work-class
_CODING_SKILL = "kata-tdd"                # coding work-class
_ECONOMY_SKILL = "kata-report"            # economy work-class

_ALL_EVENTS = [
    "freeze-gate-verdict",
    "re-gate-after-hold",
    "escalation-adjudication",
    "fix-loop-diagnose",
    "final-initiative-review",
    "gate-rejection-rework-review",
    "fail-bump-escalation",
]


def _premium_classes(
    *,
    offer: str = "fable",
    approved: bool = True,
    scope: list[str] | None = None,
) -> dict:
    """v0.2.1 LIST-form premium block (opus-anchored fire config by default)."""
    return {
        "offer": offer,
        "approved": approved,
        "scope": ["critical", "coding"] if scope is None else scope,
        "grantedMode": "advanced",
    }


def _premium_events(
    *,
    offer: str = "fable",
    approved: bool = True,
    events: list[str] | None = None,
    budget: dict | None = None,
) -> dict:
    """NEW OBJECT-form premium block (AT-L15 events form)."""
    scope: dict = {"events": _ALL_EVENTS if events is None else events}
    if budget is not None:
        scope["budget"] = budget
    return {
        "offer": offer,
        "approved": approved,
        "scope": scope,
        "grantedMode": "advanced",
    }


def _resolve(skill, *, anchor="opus", mode="advanced", premium=None, event=None):
    return km.resolve(
        skill, mode, anchor,
        family=ANTHROPIC, coder_floor=None, premium=premium, event=event,
    )


# ---------------------------------------------------------------------------
# ADAPTIVE_EVENTS registry — order pinned (MP-A9), sites verbatim (AT-L5)
# ---------------------------------------------------------------------------

def test_adaptive_events_order_pinned():
    # The tuple order IS the spend-priority documentation (AT-L13 FCFS +
    # reservation) — the reservation set is the FIRST TWO members.
    assert km.ADAPTIVE_EVENTS == (
        "freeze-gate-verdict",
        "re-gate-after-hold",
        "escalation-adjudication",
        "fix-loop-diagnose",
        "final-initiative-review",
        "gate-rejection-rework-review",
        "fail-bump-escalation",
    )
    assert isinstance(km.ADAPTIVE_EVENTS, tuple)


def test_reservation_set_is_first_two_events():
    assert km.ADAPTIVE_EVENTS[:2] == ("freeze-gate-verdict", "re-gate-after-hold")


def test_event_sites_cover_exactly_the_registry():
    # No phantom events (freeze-gate v1 MED-12): every event cites its covering
    # dispatch site, and only registry events appear.
    assert set(km.ADAPTIVE_EVENT_SITES) == set(km.ADAPTIVE_EVENTS)
    assert all(isinstance(v, str) and v for v in km.ADAPTIVE_EVENT_SITES.values())


def test_fail_bump_site_carries_conjunct_coverage_only_note():
    # re-gate MED-1: fail-bump-escalation is a CONJUNCT-COVERAGE-ONLY member.
    assert "CONJUNCT-COVERAGE-ONLY" in km.ADAPTIVE_EVENT_SITES["fail-bump-escalation"]


def test_selected_sites_verbatim():
    assert km.ADAPTIVE_EVENT_SITES["freeze-gate-verdict"] == (
        "the fresh-context kata-review freeze-gate dispatch (orchestrate freeze-gate step)"
    )
    assert km.ADAPTIVE_EVENT_SITES["re-gate-after-hold"] == (
        "the re-gate reviewer dispatch after any HOLD fold"
    )
    assert km.ADAPTIVE_EVENT_SITES["fix-loop-diagnose"] == (
        "the at-budget kata-diagnose dispatch in the gate fix-loop"
    )
    assert km.ADAPTIVE_EVENT_SITES["final-initiative-review"] == (
        "the D98 whole-initiative red-team dispatch"
    )


# ---------------------------------------------------------------------------
# classify_premium_scope — TYPE-DISPATCH (AT-L15)
# ---------------------------------------------------------------------------

def test_list_scope_classifies_as_classes():
    assert km.classify_premium_scope(["critical", "coding"]) == "classes"


def test_empty_list_scope_classifies_as_classes():
    assert km.classify_premium_scope([]) == "classes"


def test_dict_scope_classifies_as_events():
    assert km.classify_premium_scope({"events": _ALL_EVENTS}) == "events"


def test_dict_scope_with_budget_classifies_as_events():
    assert km.classify_premium_scope(
        {"events": ["freeze-gate-verdict"], "budget": {"calls": 10}}
    ) == "events"


def test_empty_events_list_is_legal_classifies_as_events():
    # AT-L15 / re-gate LOW-4: explicit [] ⇒ legal no-op, never a RAISE.
    assert km.classify_premium_scope({"events": []}) == "events"


@pytest.mark.parametrize("bad", [
    None,
    "critical",
    42,
    3.5,
    True,
    ("critical", "coding"),          # tuple is NOT a list — type-dispatch is strict
    {"critical", "coding"},          # set is neither list nor dict
])
def test_wrong_typed_scope_raises(bad):
    with pytest.raises(ValueError):
        km.classify_premium_scope(bad)


def test_list_scope_non_str_elements_raise():
    with pytest.raises(ValueError):
        km.classify_premium_scope([1, 2])


def test_absent_events_key_raises():
    # AT-L15: ABSENT events in the object form ⇒ RAISE (hand-edit posture —
    # never inferred).
    with pytest.raises(ValueError):
        km.classify_premium_scope({})
    with pytest.raises(ValueError):
        km.classify_premium_scope({"budget": {"calls": 5}})


def test_unknown_event_name_raises():
    with pytest.raises(ValueError):
        km.classify_premium_scope({"events": ["not-a-real-event"]})
    with pytest.raises(ValueError):
        km.classify_premium_scope({"events": ["freeze-gate-verdict", "phantom"]})


def test_ladder_trigger_2_grounding_is_not_an_event():
    # freeze-gate v1 BLOCKER-2: struck from the draft registry (conductor-
    # authored, not a dispatch) — must RAISE like any unknown name.
    with pytest.raises(ValueError):
        km.classify_premium_scope({"events": ["ladder-trigger-2-grounding"]})


def test_events_wrong_type_raises():
    with pytest.raises(ValueError):
        km.classify_premium_scope({"events": "freeze-gate-verdict"})
    with pytest.raises(ValueError):
        km.classify_premium_scope({"events": None})


def test_unknown_scope_key_raises():
    with pytest.raises(ValueError):
        km.classify_premium_scope({"events": [], "extra": True})
    with pytest.raises(ValueError):
        km.classify_premium_scope({"events": [], "budgets": {"calls": 1}})  # typo'd key


@pytest.mark.parametrize("bad_budget", [
    "10",                       # budget not a dict
    10,                         # budget not a dict
    ["calls", 10],              # budget not a dict
    {},                         # budget dict without calls (fail-closed)
    {"calls": "10"},            # non-int calls
    {"calls": 2.5},             # non-int calls
    {"calls": True},            # bool is not an int here (fail-closed)
    {"calls": -1},              # negative calls
    {"calls": 10, "bogus": 1},  # unknown budget key
    {"tokensOut": 500},         # tokensOut without the required calls
])
def test_non_int_budget_calls_raises(bad_budget):
    with pytest.raises(ValueError):
        km.classify_premium_scope({"events": ["freeze-gate-verdict"], "budget": bad_budget})


def test_budget_calls_zero_is_legal_shape():
    # calls >= 0: zero is a legal (if austere) budget shape.
    assert km.classify_premium_scope({"events": [], "budget": {"calls": 0}}) == "events"


def test_budget_tokens_out_is_a_known_key():
    # AT-L12: optional tokensOut where the host surfaces usage.
    assert km.classify_premium_scope(
        {"events": ["freeze-gate-verdict"], "budget": {"calls": 10, "tokensOut": 50000}}
    ) == "events"


def test_budget_tokens_out_non_int_raises():
    with pytest.raises(ValueError):
        km.classify_premium_scope(
            {"events": [], "budget": {"calls": 10, "tokensOut": "lots"}}
        )


# ---------------------------------------------------------------------------
# Events-form firing — conjunct #2 = event ∈ scope.events (MP-A1/MP-A2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("event", _ALL_EVENTS)
def test_events_form_fires_only_when_event_in_scope(event):
    # All four conjuncts hold: approved ∧ event ∈ scope.events ∧ offer exactly
    # one rung above anchor ∧ mode == advanced ⇒ EXPLICIT offer id.
    got = _resolve(_CRITICAL_SKILL, premium=_premium_events(), event=event)
    assert got == km.ID_MAP["fable"] == "claude-fable-5"


def test_events_form_status_fires():
    st = km.premium_status(_premium_events(), "opus", family=ANTHROPIC,
                           mode="advanced", event="freeze-gate-verdict")
    assert st == {"fires": True, "reason": "fires"}


def test_event_not_in_scope_events_no_fire():
    # Scope lists ONLY freeze-gate-verdict; a fix-loop-diagnose event must NOT
    # fire — resolve falls through to the frozen path (advanced/critical = None).
    prem = _premium_events(events=["freeze-gate-verdict"])
    got = _resolve(_CRITICAL_SKILL, premium=prem, event="fix-loop-diagnose")
    assert got is None
    st = km.premium_status(prem, "opus", family=ANTHROPIC,
                           mode="advanced", event="fix-loop-diagnose")
    assert st == {"fires": False, "reason": "event-not-in-scope"}


def test_empty_events_list_never_fires():
    # AT-L15: explicit events [] ⇒ legal no-op — premium never fires, the
    # operator said so on purpose.
    prem = _premium_events(events=[])
    for event in _ALL_EVENTS:
        assert _resolve(_CRITICAL_SKILL, premium=prem, event=event) is None
    st = km.premium_status(prem, "opus", family=ANTHROPIC,
                           mode="advanced", event="freeze-gate-verdict")
    assert st == {"fires": False, "reason": "event-not-in-scope"}


def test_class_query_against_events_form_no_fire_not_crash():
    # A class-based query (no event kwarg) against an events-form scope is
    # simply NO-FIRE — never a crash, never a fire (MP-A8).
    got = _resolve(_CRITICAL_SKILL, premium=_premium_events())
    assert got is None  # frozen advanced/critical/opus = step 0 = None
    st = km.premium_status(_premium_events(), "opus", family=ANTHROPIC, mode="advanced")
    assert st == {"fires": False, "reason": "no-event"}


def test_events_form_other_conjuncts_untouched_mode():
    # Conjunct: mode == advanced. Standard/essential never fire the events form.
    prem = _premium_events()
    got = _resolve(_CODING_SKILL, mode="standard", premium=prem, event="freeze-gate-verdict")
    assert got == km.ID_MAP["sonnet"]  # frozen standard/coding/opus = -1
    st = km.premium_status(prem, "opus", family=ANTHROPIC,
                           mode="standard", event="freeze-gate-verdict")
    assert st == {"fires": False, "reason": "mode-not-advanced"}
    st_e = km.premium_status(prem, "opus", family=ANTHROPIC,
                             mode="essential", event="freeze-gate-verdict")
    assert st_e["fires"] is False


def test_events_form_other_conjuncts_untouched_approved():
    prem = _premium_events(approved=False)
    got = _resolve(_CRITICAL_SKILL, premium=prem, event="freeze-gate-verdict")
    assert got is None
    st = km.premium_status(prem, "opus", family=ANTHROPIC,
                           mode="advanced", event="freeze-gate-verdict")
    assert st == {"fires": False, "reason": "not-approved"}


def test_events_form_other_conjuncts_untouched_offer_relation():
    # anchor=sonnet, offer=fable ⇒ two rungs above ⇒ NO FIRE even with a valid event.
    prem = _premium_events()
    st = km.premium_status(prem, "sonnet", family=ANTHROPIC,
                           mode="advanced", event="freeze-gate-verdict")
    assert st == {"fires": False, "reason": "offer-too-high"}
    got = _resolve(_CRITICAL_SKILL, anchor="sonnet", premium=prem,
                   event="freeze-gate-verdict")
    assert got is None  # frozen advanced/critical/sonnet = None


def test_events_form_budget_shape_validated_but_not_enforced_here():
    # Budget is validated at load (shape) but spend is the CONDUCTOR's job —
    # a calls:0 budget does not stop the pure resolver from firing.
    prem = _premium_events(budget={"calls": 0})
    got = _resolve(_CRITICAL_SKILL, premium=prem, event="freeze-gate-verdict")
    assert got == km.ID_MAP["fable"]


def test_events_form_malformed_scope_raises_in_resolve():
    # AT-L21 fail-closed: malformed events form RAISES from resolve too — never
    # a silent fall-through to unlimited premium OR to no-premium.
    with pytest.raises(ValueError):
        _resolve(_CRITICAL_SKILL,
                 premium=_premium_events(events=["not-a-real-event"]),
                 event="freeze-gate-verdict")
    with pytest.raises(ValueError):
        km.resolve(_CRITICAL_SKILL, "advanced", "opus",
                   family=ANTHROPIC, coder_floor=None,
                   premium={"offer": "fable", "approved": True, "scope": {}})


def test_events_form_malformed_scope_raises_in_premium_status():
    with pytest.raises(ValueError):
        km.premium_status(_premium_events(events=["phantom"]), "opus",
                          family=ANTHROPIC, mode="advanced",
                          event="freeze-gate-verdict")


def test_events_form_never_fires_for_economy_class_r9_structural():
    # ADVAL F1 fold (AT-L14 / R-9): economy work NEVER runs the premium rung in
    # EITHER scope form — an event-tagged economy dispatch falls through to the
    # frozen path (code-enforced, not prose-enforced). Mutation target: removing
    # the events-form work-class guard turns this RED.
    got = _resolve(_ECONOMY_SKILL, premium=_premium_events(), event="escalation-adjudication")
    assert got != km.ID_MAP["fable"]
    # ...and the frozen advanced-economy resolution (anchor−1 off the opus
    # anchor = sonnet) still applies:
    assert got == km.ID_MAP["sonnet"]


def test_events_form_ac7_premium_never_fires_matrix():
    # AC-7 (DESIGN §4 criterion 7): the 5-way premium-NEVER-fires matrix.
    fable = km.ID_MAP["fable"]
    # (1) economy class, even event-tagged (the F1 structural guard):
    assert _resolve(_ECONOMY_SKILL, premium=_premium_events(),
                    event="fail-bump-escalation") != fable
    # (2) essential / (3) standard modes (conjunct #4):
    for mode in ("essential", "standard"):
        assert km.resolve(_CRITICAL_SKILL, mode, "opus", family=ANTHROPIC,
                          coder_floor=None, premium=_premium_events(),
                          event="freeze-gate-verdict") != fable
    # (4) unapproved:
    unapproved = _premium_events()
    unapproved["approved"] = False
    assert _resolve(_CRITICAL_SKILL, premium=unapproved,
                    event="freeze-gate-verdict") != fable
    # (5) wrong-rung offer (two rungs above a sonnet anchor):
    assert km.resolve(_CRITICAL_SKILL, "advanced", "sonnet", family=ANTHROPIC,
                      coder_floor=None, premium=_premium_events(),
                      event="freeze-gate-verdict") != fable
    # (budget exhaustion is conductor-side: kata_adaptive.can_spend tests own it.)


# ---------------------------------------------------------------------------
# List-form BC — classify "classes" + behavior identical, event IGNORED
# ---------------------------------------------------------------------------

def test_list_form_known_fire_cell_unchanged():
    # Known matrix fire cell: advanced/critical/opus + list scope ⇒ fable.
    got = _resolve(_CRITICAL_SKILL, premium=_premium_classes())
    assert got == km.ID_MAP["fable"]


def test_list_form_known_no_fire_cell_unchanged():
    # Known matrix no-fire cell: economy stays on the frozen advanced economy
    # step (-1 = sonnet), never elevated.
    got = _resolve(_ECONOMY_SKILL, premium=_premium_classes())
    assert got == km.ID_MAP["sonnet"]


def test_list_form_event_kwarg_is_ignored():
    # LIST scope ⇒ conjunct #2 = work-class ∈ scope, event IGNORED: passing an
    # event changes nothing in either direction.
    prem = _premium_classes()
    assert _resolve(_CRITICAL_SKILL, premium=prem, event="freeze-gate-verdict") \
        == _resolve(_CRITICAL_SKILL, premium=prem) == km.ID_MAP["fable"]
    assert _resolve(_ECONOMY_SKILL, premium=prem, event="freeze-gate-verdict") \
        == _resolve(_ECONOMY_SKILL, premium=prem) == km.ID_MAP["sonnet"]
    st = km.premium_status(prem, "opus", family=ANTHROPIC,
                           mode="advanced", event="freeze-gate-verdict")
    assert st == {"fires": True, "reason": "fires"}


def test_no_event_default_matches_frozen_resolve_everywhere():
    # event=None + premium=None ⇒ byte-for-byte the frozen resolution.
    for skill in (_CRITICAL_SKILL, _CODING_SKILL, _ECONOMY_SKILL):
        for mode in ("advanced", "standard", "essential"):
            for anchor in ("haiku", "sonnet", "opus", "fable", "mythos"):
                frozen = km.resolve(skill, mode, anchor,
                                    family=ANTHROPIC, coder_floor=None)
                with_kwargs = km.resolve(skill, mode, anchor,
                                         family=ANTHROPIC, coder_floor=None,
                                         premium=None, event=None)
                assert with_kwargs == frozen


# ---------------------------------------------------------------------------
# premium_rung_of — family-agnostic one-rung-above helper (AT-L17, MP-A10)
# ---------------------------------------------------------------------------

def test_premium_rung_of_anthropic_opus_is_fable():
    assert km.premium_rung_of("anthropic", "opus") == "fable"


def test_premium_rung_of_top_rung_anchor_is_none():
    # mythos is the anthropic top rung — no rung above.
    assert km.premium_rung_of("anthropic", "mythos") is None


def test_premium_rung_of_unknown_family_is_none():
    assert km.premium_rung_of("no-such-family", "opus") is None


def test_premium_rung_of_empty_ladder_family_is_none():
    assert km.premium_rung_of("openai", "opus") is None


def test_premium_rung_of_unknown_anchor_is_none():
    assert km.premium_rung_of("anthropic", "zzz-not-a-model") is None


def test_premium_rung_of_accepts_full_model_id():
    assert km.premium_rung_of("anthropic", "claude-opus-4-8") == "fable"


def test_premium_rung_of_lower_rungs():
    assert km.premium_rung_of("anthropic", "sonnet") == "opus"
    assert km.premium_rung_of("anthropic", "fable") == "mythos"


def test_premium_rung_of_is_family_agnostic(monkeypatch):
    # AT-L17: must work for ANY registered family ladder — prove it with a
    # temporarily registered non-Anthropic ladder.
    monkeypatch.setitem(km.FAMILY_LADDERS, "testfam", ["small", "medium", "large"])
    assert km.premium_rung_of("testfam", "medium") == "large"
    assert km.premium_rung_of("testfam", "large") is None
    assert km.premium_rung_of("testfam", "small") == "medium"


# ---------------------------------------------------------------------------
# ADVAL F3 fold — AC-1's golden matrix: the FULL 48-skill × 3-mode × 5-anchor
# equivalence sweep (new kwargs at defaults ⇒ byte-identical resolution) plus a
# literal pinned sample (hand-derived v0.2.1 expectations, not self-comparison).
# ---------------------------------------------------------------------------


def test_ac1_golden_full_matrix_new_kwargs_are_inert():
    anchors = ["haiku", "sonnet", "opus", "fable", "claude-opus-4-8"]
    modes = ["essential", "standard", "advanced"]
    cells = 0
    for skill in sorted(km.SKILL_WORK_CLASS):
        for mode in modes:
            for anchor in anchors:
                baseline = km.resolve(skill, mode, anchor, family=ANTHROPIC, coder_floor=None)
                with_kwargs = km.resolve(
                    skill, mode, anchor, family=ANTHROPIC, coder_floor=None,
                    premium=None, event=None,
                )
                assert with_kwargs == baseline, (skill, mode, anchor)
                cells += 1
    assert cells == len(km.SKILL_WORK_CLASS) * 3 * 5
    assert len(km.SKILL_WORK_CLASS) >= 48  # the full registry, never a sample


def test_ac1_golden_literal_pinned_sample():
    # Hand-derived v0.2.1 expectations (D131 table: advanced economy −1;
    # standard economy −2; standard coding −1; zero-step ⇒ None/OMIT) — a
    # literal cross-check independent of the code's own arithmetic.
    pins = [
        ("kata-evaluate", "advanced", "fable", None),            # zero-step critical
        ("kata-evaluate", "standard", "opus", None),             # zero-step critical
        ("kata-tdd", "standard", "opus", km.ID_MAP["sonnet"]),   # coding −1
        ("kata-tdd", "advanced", "fable", None),                 # advanced coding zero-step
        ("kata-report", "advanced", "fable", km.ID_MAP["opus"]),  # advanced economy −1
        ("kata-report", "standard", "opus", km.ID_MAP["haiku"]),  # standard economy −2
    ]
    for skill, mode, anchor, expected in pins:
        got = km.resolve(skill, mode, anchor, family=ANTHROPIC, coder_floor=None,
                         premium=None, event=None)
        assert got == expected, (skill, mode, anchor, got, expected)
