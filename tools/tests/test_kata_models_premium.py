"""test_kata_models_premium.py — TDD suite for the §3 GATED AMENDMENT (D148).

Covers the premium gate added to ``kata_models`` in the context-autonomy
initiative (CA-P0 / task E3):

  * ``premium_status(premium, anchor, *, family, mode)`` — run-level conjunct
    reporter for NO-FIRE surfacing / audit.
  * ``resolve(..., premium=...)`` — the additive premium branch: fires iff all
    FOUR conjuncts hold, returning the EXPLICIT ``offer`` id.

The existing ``test_kata_models.py`` suite is the BC canary (§4 row 4/5) and is
deliberately left byte-unchanged — premium coverage lives here, in a sibling file.

Run:
    cd C:/Dev/Projects/KataHarness/tools
    uv run pytest tests/test_kata_models_premium.py -v

Mutation-proof map (each disable → the named test goes RED → revert):
    MP-1  approved conjunct        → test_conjunct_approved_false_no_fire
    MP-2  mode==advanced conjunct  → test_conjunct_mode_not_advanced_no_fire
    MP-3  one-rung-above conjunct  → test_conjunct_offer_two_rungs_no_fire
    MP-4  scope conjunct           → test_conjunct_economy_out_of_scope_no_fire
    MP-5  explicit-id return       → test_all_conjuncts_true_returns_explicit_offer_id
"""
from __future__ import annotations

import pytest

import kata_models as km

ANTHROPIC = "anthropic"

# Ladder (low→high): haiku(0) sonnet(1) opus(2) fable(3) mythos(4)
_CRITICAL_SKILL = "kata-grill-essential"  # critical work-class
_CODING_SKILL = "kata-tdd"                # coding work-class
_ECONOMY_SKILL = "kata-report"            # economy work-class


def _premium(
    *,
    offer: str = "fable",
    approved: bool = True,
    scope: list[str] | None = None,
    granted_mode: str = "advanced",
) -> dict:
    """Build a well-formed models.premium block (opus-anchored fire config by default)."""
    return {
        "offer": offer,
        "approved": approved,
        "scope": ["critical", "coding"] if scope is None else scope,
        "grantedMode": granted_mode,
    }


def _resolve(skill, *, anchor="opus", mode="advanced", premium=None):
    return km.resolve(
        skill, mode, anchor,
        family=ANTHROPIC, coder_floor=None, premium=premium,
    )


# ---------------------------------------------------------------------------
# All four conjuncts TRUE ⇒ explicit offer id (MP-5)
# ---------------------------------------------------------------------------

def test_all_conjuncts_true_returns_explicit_offer_id():
    # anchor=opus, offer=fable (exactly one rung above), advanced, approved,
    # critical work in scope. Frozen advanced/critical = step 0 = None; premium
    # elevates that None to the EXPLICIT fable id.
    got = _resolve(_CRITICAL_SKILL, premium=_premium())
    assert got == km.ID_MAP["fable"] == "claude-fable-5"


def test_all_conjuncts_true_coding_class_also_fires():
    got = _resolve(_CODING_SKILL, premium=_premium())
    assert got == km.ID_MAP["fable"]


def test_returned_id_is_explicit_never_none_when_firing():
    # The whole point: inherit (None) would silently give the session model.
    assert _resolve(_CRITICAL_SKILL, premium=_premium()) is not None


# ---------------------------------------------------------------------------
# Conjunct 1 — approved (MP-1)
# ---------------------------------------------------------------------------

def test_conjunct_approved_false_no_fire():
    got = _resolve(_CRITICAL_SKILL, premium=_premium(approved=False))
    # Falls through to frozen path: advanced/critical/opus = step 0 = None.
    assert got is None


def test_status_not_approved_reason():
    st = km.premium_status(_premium(approved=False), "opus", family=ANTHROPIC, mode="advanced")
    assert st == {"fires": False, "reason": "not-approved"}


# ---------------------------------------------------------------------------
# Conjunct 2 — work-class ∈ scope (MP-4); economy structurally excluded (R-9)
# ---------------------------------------------------------------------------

def test_conjunct_economy_out_of_scope_no_fire():
    # Economy skill, default scope = [critical, coding]. Premium must NOT fire;
    # resolve returns the FROZEN economy result (advanced anthropic economy = -1 = opus id).
    got = _resolve(_ECONOMY_SKILL, premium=_premium())
    assert got == km.ID_MAP["sonnet"]  # frozen advanced economy = -1 = sonnet, NOT fable


def test_economy_never_fires_even_if_scope_lists_economy():
    # Hand-edited scope including "economy" must NOT elevate economy work (R-9,
    # "economy is structurally excluded"). Frozen economy result stands.
    got = _resolve(_ECONOMY_SKILL, premium=_premium(scope=["critical", "coding", "economy"]))
    assert got == km.ID_MAP["sonnet"]  # frozen advanced economy = -1 = sonnet


def test_critical_absent_from_scope_no_fire():
    # scope lists only "coding" → a critical skill is out of scope → frozen path.
    got = _resolve(_CRITICAL_SKILL, premium=_premium(scope=["coding"]))
    assert got is None  # frozen advanced/critical = None


# ---------------------------------------------------------------------------
# Conjunct 3 — offer EXACTLY one rung above anchor (MP-3) + fold-#1 edge cases
# ---------------------------------------------------------------------------

def test_conjunct_offer_two_rungs_no_fire():
    # anchor=sonnet, offer=fable → 2 rungs above ⇒ NO FIRE + surfaced (§3.2).
    st = km.premium_status(_premium(offer="fable"), "sonnet", family=ANTHROPIC, mode="advanced")
    assert st == {"fires": False, "reason": "offer-too-high"}
    # resolve falls through to frozen sonnet advanced/critical = step 0 = None.
    got = _resolve(_CRITICAL_SKILL, anchor="sonnet", premium=_premium(offer="fable"))
    assert got is None


def test_anchor_fable_offer_fable_no_fire_never_elevates_to_mythos():
    # anchor already fable + approved fable offer ⇒ offer==anchor ⇒ NO FIRE.
    # Must NOT elevate to mythos.
    st = km.premium_status(_premium(offer="fable"), "fable", family=ANTHROPIC, mode="advanced")
    assert st == {"fires": False, "reason": "offer-equals-anchor"}
    got = _resolve(_CRITICAL_SKILL, anchor="fable", premium=_premium(offer="fable"))
    assert got != km.ID_MAP["mythos"]
    assert got is None  # frozen advanced/critical/fable = None


def test_offer_below_anchor_no_fire():
    # anchor=fable, offer=opus (below) ⇒ NO FIRE.
    st = km.premium_status(_premium(offer="opus"), "fable", family=ANTHROPIC, mode="advanced")
    assert st == {"fires": False, "reason": "offer-below-anchor"}


def test_offer_one_rung_above_fires_status():
    st = km.premium_status(_premium(offer="fable"), "opus", family=ANTHROPIC, mode="advanced")
    assert st == {"fires": True, "reason": "fires"}


# ---------------------------------------------------------------------------
# Conjunct 4 — mode == advanced (MP-2) — the standard-mode blowout closure
# ---------------------------------------------------------------------------

def test_conjunct_mode_not_advanced_no_fire():
    st = km.premium_status(_premium(), "opus", family=ANTHROPIC, mode="standard")
    assert st == {"fires": False, "reason": "mode-not-advanced"}
    # resolve in standard mode falls through to the frozen standard-coding step.
    got = _resolve(_CODING_SKILL, mode="standard", premium=_premium())
    assert got == km.ID_MAP["sonnet"]  # frozen standard/coding/opus = -1 = sonnet


def test_mode_essential_no_fire():
    st = km.premium_status(_premium(), "opus", family=ANTHROPIC, mode="essential")
    assert st["fires"] is False and st["reason"] == "mode-not-advanced"


# ---------------------------------------------------------------------------
# Zero-step / gated-top-rung protection
# ---------------------------------------------------------------------------

def test_premium_never_returns_anchor_own_id():
    # When firing, the offer is one rung ABOVE the anchor → returned id != anchor id.
    got = _resolve(_CRITICAL_SKILL, anchor="opus", premium=_premium(offer="fable"))
    assert got != km.ID_MAP["opus"]
    assert got == km.ID_MAP["fable"]


# ---------------------------------------------------------------------------
# Absent premium ⇒ byte-for-byte frozen behaviour (§4 row 4/5 BC)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("skill", [_CRITICAL_SKILL, _CODING_SKILL, _ECONOMY_SKILL])
@pytest.mark.parametrize("mode", ["advanced", "standard", "essential"])
@pytest.mark.parametrize("anchor", ["haiku", "sonnet", "opus", "fable", "mythos"])
def test_premium_none_matches_frozen_resolve(skill, mode, anchor):
    frozen = km.resolve(skill, mode, anchor, family=ANTHROPIC, coder_floor=None)
    with_none = km.resolve(skill, mode, anchor, family=ANTHROPIC, coder_floor=None, premium=None)
    assert with_none == frozen


def test_premium_status_none_is_absent():
    st = km.premium_status(None, "opus", family=ANTHROPIC, mode="advanced")
    assert st == {"fires": False, "reason": "absent"}


# ---------------------------------------------------------------------------
# Family resolution: auto + unknown-context NO-FIRE reasons
# ---------------------------------------------------------------------------

def test_family_auto_fires_when_derivable():
    got = km.resolve(_CRITICAL_SKILL, "advanced", "opus",
                     family="auto", coder_floor=None, premium=_premium())
    assert got == km.ID_MAP["fable"]


def test_status_no_family_when_ladder_empty():
    st = km.premium_status(_premium(), "opus", family="openai", mode="advanced")
    assert st == {"fires": False, "reason": "no-family"}


def test_status_unknown_anchor():
    st = km.premium_status(_premium(), "zzz-not-a-model", family=ANTHROPIC, mode="advanced")
    assert st == {"fires": False, "reason": "unknown-anchor"}


def test_status_unknown_offer():
    st = km.premium_status(_premium(offer="zzz"), "opus", family=ANTHROPIC, mode="advanced")
    assert st == {"fires": False, "reason": "unknown-offer"}


def test_offer_accepts_full_model_id():
    # A full-id offer normalizes to its short-name for the ladder check + return.
    got = _resolve(_CRITICAL_SKILL, premium=_premium(offer="claude-fable-5"))
    assert got == km.ID_MAP["fable"]


def test_anchor_full_id_fires():
    got = km.resolve(_CRITICAL_SKILL, "advanced", "claude-opus-4-8",
                     family=ANTHROPIC, coder_floor=None, premium=_premium())
    assert got == km.ID_MAP["fable"]


# ---------------------------------------------------------------------------
# Fail-closed: malformed premium block RAISES (D136) — resolve AND premium_status
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [
    "not-a-dict",
    123,
    ["offer", "fable"],
    {},                                                  # missing all keys
    {"approved": True, "scope": ["critical"]},           # missing offer
    {"offer": "fable", "scope": ["critical"]},           # missing approved
    {"offer": "fable", "approved": True},                # missing scope
    {"offer": 3, "approved": True, "scope": ["critical"]},          # offer wrong type
    {"offer": "fable", "approved": "yes", "scope": ["critical"]},   # approved wrong type
    {"offer": "fable", "approved": 1, "scope": ["critical"]},       # int-not-bool
    {"offer": "fable", "approved": True, "scope": "critical"},      # scope not a list
    {"offer": "fable", "approved": True, "scope": [1, 2]},          # scope non-str elems
])
def test_malformed_premium_raises_in_resolve(bad):
    with pytest.raises(ValueError):
        km.resolve(_CRITICAL_SKILL, "advanced", "opus",
                   family=ANTHROPIC, coder_floor=None, premium=bad)


def test_malformed_premium_raises_in_premium_status():
    with pytest.raises(ValueError):
        km.premium_status({"offer": "fable"}, "opus", family=ANTHROPIC, mode="advanced")


def test_approved_int_one_is_malformed_not_truthy():
    # bool is an int subclass; approved:1 must be rejected as malformed, never
    # silently treated as True (fail-closed).
    with pytest.raises(ValueError):
        km.premium_status({"offer": "fable", "approved": 1, "scope": ["critical"]},
                          "opus", family=ANTHROPIC, mode="advanced")
