"""Tests for kata_adaptive.py — the D150 adaptive-tiering L1 state machine.

Coverage map (mutation-pinned, boundary-named):
- Config resolver: None ⇒ all-OFF; block presence = consent; per-key defaults (§3);
  unknown key / non-bool / non-int / <1 ⇒ AdaptiveError (AT-L21 fail-closed).
- Fail-bump (AT-L8): F=2 strict ``>=`` boundary; fires ONCE per task (no re-arm);
  bump persists for remaining attempts.
- Streak (AT-L11): K=3 boundary; one rejection clears; damper ×2 on a
  downshift-attributed rejection (3 more passes insufficient, 6 needed).
- Modulation order (AT-L1): bumped-task downshift exemption (per-task overrides
  class); downward cap at −1 (complexity + streak never stack — re-gate MED-2);
  coding-only downshift (AT-L4 — critical/economy ⇒ 0); disabled ⇒ all zeros.
- Budget (AT-L12/L13): default N=10; calls validation; FCFS reservation boundary
  (non-reserved blocked at remaining == RESERVE; reserved spends down to 0).
- Recount trail (AT-L7): render/recount round-trip; malformed ``tier:`` payload
  RAISES; non-``tier:`` payloads ignored.
- Anchor switch (AT-L17b): reset clears counters/streaks/dampers, PRESERVES spend.
"""

from __future__ import annotations

import pytest

import kata_adaptive
from kata_adaptive import (
    ADAPTIVE_DEFAULTS,
    RESERVE,
    RESERVED_EVENTS,
    AdaptiveError,
    anchor_switch_reset,
    apply_delta,
    bump_pending,
    can_spend,
    l2_base_rung,
    modulate_step,
    new_state,
    record_gate_result,
    record_spend,
    record_standing_reroll,
    recount_from_decisions,
    render_tier_decision,
    resolve_adaptive_config,
    resolve_budget,
    state_from_recount,
)


def _cfg(**overrides) -> dict:
    """An ENABLED adaptive config (block present ⇒ consent, §3) with overrides."""
    return resolve_adaptive_config(dict(overrides))


def _reject(state: dict, task_id: str, task_class: str = "impl", *, downshifted: bool = False) -> None:
    """One gate REJECTION for *task_id* (resets streak, arms the bump counter)."""
    record_gate_result(
        state, task_id, task_class, accepted=False, first_pass=False, downshifted=downshifted
    )


def _accept_first_pass(state: dict, task_id: str, task_class: str = "impl") -> None:
    """One FIRST-PASS gate acceptance (the only streak-building event, AT-L11)."""
    record_gate_result(
        state, task_id, task_class, accepted=True, first_pass=True, downshifted=False
    )


# ---------------------------------------------------------------------------
# Module 1 — constants + config resolver (§3, §7, AT-L21)
# ---------------------------------------------------------------------------


class TestDefaults:
    """§7 tunables are DATA'd exactly as the frozen design pins them."""

    def test_adaptive_defaults_values(self):
        assert ADAPTIVE_DEFAULTS == {
            "failBumpAt": 2,
            "streakDownAt": 3,
            "planComplexityDownshift": True,
            "evaluatorEscalate": True,
            "l2": False,
        }

    def test_reserved_events(self):
        # AT-L13: the reservation covers exactly the two freeze-gate events.
        assert RESERVED_EVENTS == ("freeze-gate-verdict", "re-gate-after-hold")

    def test_reserve_value(self):
        assert RESERVE == 2


class TestResolveAdaptiveConfig:
    """resolve_adaptive_config: block presence = consent; fail-closed validation."""

    def test_none_is_all_off(self):
        # §3 BC matrix: absent block ⇒ EVERY adaptive leg OFF (load-time BC).
        assert resolve_adaptive_config(None) == {"enabled": False}

    def test_empty_dict_enables_with_defaults(self):
        # Freeze-gate v1 HIGH-6: any absent KEY inside a present block ⇒ its default.
        cfg = resolve_adaptive_config({})
        assert cfg == {"enabled": True, **ADAPTIVE_DEFAULTS}

    def test_override_kept_others_default(self):
        cfg = resolve_adaptive_config({"failBumpAt": 4, "l2": True})
        assert cfg["failBumpAt"] == 4
        assert cfg["l2"] is True
        assert cfg["streakDownAt"] == 3
        assert cfg["planComplexityDownshift"] is True
        assert cfg["evaluatorEscalate"] is True
        assert cfg["enabled"] is True

    def test_unknown_key_raises(self):
        with pytest.raises(AdaptiveError, match="unknown"):
            resolve_adaptive_config({"failBumpAt": 2, "bogusKnob": 1})

    def test_fail_bump_at_zero_raises(self):
        # NAMED boundary: the int fields require >= 1; 0 would bump every dispatch.
        with pytest.raises(AdaptiveError):
            resolve_adaptive_config({"failBumpAt": 0})

    def test_fail_bump_at_one_is_legal(self):
        assert resolve_adaptive_config({"failBumpAt": 1})["failBumpAt"] == 1

    def test_streak_down_at_zero_raises(self):
        with pytest.raises(AdaptiveError):
            resolve_adaptive_config({"streakDownAt": 0})

    def test_bool_for_int_field_raises(self):
        # bool subclasses int — must be rejected, never counted as failBumpAt=1.
        with pytest.raises(AdaptiveError):
            resolve_adaptive_config({"failBumpAt": True})

    def test_string_for_int_field_raises(self):
        with pytest.raises(AdaptiveError):
            resolve_adaptive_config({"streakDownAt": "3"})

    def test_non_bool_for_bool_field_raises(self):
        with pytest.raises(AdaptiveError):
            resolve_adaptive_config({"planComplexityDownshift": 1})

    def test_non_bool_for_l2_raises(self):
        with pytest.raises(AdaptiveError):
            resolve_adaptive_config({"l2": "yes"})

    def test_non_dict_non_none_raises(self):
        # AT-L21: a wrong-typed adaptive block is load-guard STOP material.
        with pytest.raises(AdaptiveError):
            resolve_adaptive_config(["failBumpAt", 2])

    def test_string_value_raises(self):
        with pytest.raises(AdaptiveError):
            resolve_adaptive_config("on")


class TestNewState:
    def test_shape(self):
        assert new_state() == {
            "bumpCounters": {},
            "bumped": {},
            "streaks": {},
            "dampers": {},
            "budgetSpent": 0,
        }

    def test_fresh_instances(self):
        # Two states never share mutable sub-dicts.
        a, b = new_state(), new_state()
        a["streaks"]["impl"] = 5
        assert b["streaks"] == {}


# ---------------------------------------------------------------------------
# Module 2 — signal recording (AT-L8 / AT-L11 bookkeeping)
# ---------------------------------------------------------------------------


class TestRecordGateResult:
    def test_first_pass_acceptance_builds_streak(self):
        state = new_state()
        _accept_first_pass(state, "T1")
        _accept_first_pass(state, "T2")
        assert state["streaks"]["impl"] == 2

    def test_fix_cycled_acceptance_resets_streak(self):
        # AT-L11: only FIRST-PASS acceptances are streak members; an accepted-after-
        # fix-loop task resets the class streak to 0.
        state = new_state()
        _accept_first_pass(state, "T1")
        record_gate_result(
            state, "T2", "impl", accepted=True, first_pass=False, downshifted=False
        )
        assert state["streaks"]["impl"] == 0

    def test_rejection_resets_streak_and_arms_counter(self):
        state = new_state()
        _accept_first_pass(state, "T1")
        _accept_first_pass(state, "T2")
        _reject(state, "T3")
        assert state["streaks"]["impl"] == 0
        assert state["bumpCounters"]["T3"] == 1

    def test_rejection_on_downshifted_dispatch_doubles_damper(self):
        # AT-L11 damper: ×2 per downshift-attributed rejection (1 → 2 → 4).
        state = new_state()
        _reject(state, "T1", downshifted=True)
        assert state["dampers"]["impl"] == 2
        _reject(state, "T1", downshifted=True)
        assert state["dampers"]["impl"] == 4

    def test_rejection_not_downshifted_leaves_damper_alone(self):
        state = new_state()
        _reject(state, "T1", downshifted=False)
        assert "impl" not in state["dampers"]


class TestRecordStandingReroll:
    def test_counts_toward_bump_and_clears_streak(self):
        # AT-L8: STANDING ladder rerolls count exactly like gate rejections.
        state = new_state()
        _accept_first_pass(state, "T1")
        record_standing_reroll(state, "T2", "impl")
        assert state["bumpCounters"]["T2"] == 1
        assert state["streaks"]["impl"] == 0


# ---------------------------------------------------------------------------
# Module 3 — bump_pending (AT-L8: F=2, strict >=, once per task)
# ---------------------------------------------------------------------------


class TestBumpPending:
    def test_one_rejection_no_bump(self):
        # NAMED F=2 boundary: counter 1 < 2 ⇒ no bump (mutation target: >= vs >).
        state, cfg = new_state(), _cfg()
        _reject(state, "T1")
        assert bump_pending(state, cfg, "T1") is False

    def test_two_rejections_bump(self):
        # NAMED F=2 boundary: counter 2 >= 2 ⇒ bump pending.
        state, cfg = new_state(), _cfg()
        _reject(state, "T1")
        _reject(state, "T1")
        assert bump_pending(state, cfg, "T1") is True

    def test_reroll_and_rejection_mix_reaches_f(self):
        state, cfg = new_state(), _cfg()
        _reject(state, "T1")
        record_standing_reroll(state, "T1", "impl")
        assert bump_pending(state, cfg, "T1") is True

    def test_disabled_config_never_pends(self):
        state = new_state()
        for _ in range(5):
            _reject(state, "T1")
        assert bump_pending(state, resolve_adaptive_config(None), "T1") is False

    def test_fires_once_per_task(self):
        # AT-L8: F fires ONCE per task — after the bump is consumed (marked), a
        # third rejection does NOT re-arm the pending flag.
        state, cfg = new_state(), _cfg()
        _reject(state, "T1")
        _reject(state, "T1")
        assert modulate_step(cfg, state, task_id="T1", task_class="impl", work_class="coding") == 1
        assert bump_pending(state, cfg, "T1") is False
        _reject(state, "T1")  # third rejection
        assert bump_pending(state, cfg, "T1") is False

    def test_per_task_isolation(self):
        state, cfg = new_state(), _cfg()
        _reject(state, "T1")
        _reject(state, "T1")
        assert bump_pending(state, cfg, "T2") is False


# ---------------------------------------------------------------------------
# Module 4 — modulate_step (AT-L1 pinned order, AT-L4 coding-only, cap at −1)
# ---------------------------------------------------------------------------


class TestModulateStepBump:
    def test_bump_returns_plus_one_and_marks(self):
        state, cfg = new_state(), _cfg()
        _reject(state, "T1")
        _reject(state, "T1")
        assert modulate_step(cfg, state, task_id="T1", task_class="impl", work_class="coding") == 1
        assert state["bumped"]["T1"] is True

    def test_bump_persists_for_remaining_attempts(self):
        # AT-L8: the bump persists — every later attempt of the task is +1.
        state, cfg = new_state(), _cfg()
        _reject(state, "T1")
        _reject(state, "T1")
        modulate_step(cfg, state, task_id="T1", task_class="impl", work_class="coding")
        assert modulate_step(cfg, state, task_id="T1", task_class="impl", work_class="coding") == 1

    def test_bumped_task_exempt_from_downshift(self):
        # AT-L1: per-task state OVERRIDES class state — a bumped task is never
        # downshifted, even with complexity=low AND an earned class streak.
        state, cfg = new_state(), _cfg()
        for tid in ("A", "B", "C"):
            _accept_first_pass(state, tid)
        _reject(state, "T1")
        _reject(state, "T1")
        step = modulate_step(
            cfg, state, task_id="T1", task_class="impl", work_class="coding", complexity="low"
        )
        assert step == 1


class TestModulateStepDownshift:
    def test_streak_below_k_no_downshift(self):
        # NAMED K=3 boundary: 2 first-pass acceptances are insufficient.
        state, cfg = new_state(), _cfg()
        _accept_first_pass(state, "A")
        _accept_first_pass(state, "B")
        assert modulate_step(cfg, state, task_id="T1", task_class="impl", work_class="coding") == 0

    def test_streak_at_k_downshifts(self):
        # NAMED K=3 boundary: 3 first-pass acceptances ⇒ −1.
        state, cfg = new_state(), _cfg()
        for tid in ("A", "B", "C"):
            _accept_first_pass(state, tid)
        assert modulate_step(cfg, state, task_id="T1", task_class="impl", work_class="coding") == -1

    def test_one_rejection_restores_immediately(self):
        # AT-L11 hysteresis: fast up, slow down.
        state, cfg = new_state(), _cfg()
        for tid in ("A", "B", "C"):
            _accept_first_pass(state, tid)
        _reject(state, "T1")
        assert modulate_step(cfg, state, task_id="T2", task_class="impl", work_class="coding") == 0

    def test_damper_doubles_k(self):
        # NAMED damper boundary (AT-L11): after a rejection on a DOWNSHIFTED
        # dispatch, K doubles — 3 more first-pass acceptances are insufficient,
        # 6 are needed.
        state, cfg = new_state(), _cfg()
        for tid in ("A", "B", "C"):
            _accept_first_pass(state, tid)
        _reject(state, "T1", downshifted=True)  # damper impl ⇒ 2, streak ⇒ 0
        for tid in ("D", "E", "F"):
            _accept_first_pass(state, tid)
        assert modulate_step(cfg, state, task_id="T2", task_class="impl", work_class="coding") == 0
        for tid in ("G", "H", "I"):
            _accept_first_pass(state, tid)
        assert modulate_step(cfg, state, task_id="T2", task_class="impl", work_class="coding") == -1

    def test_complexity_low_downshifts(self):
        # AT-L10a: plan-frozen complexity=low ⇒ start one rung below.
        state, cfg = new_state(), _cfg()
        step = modulate_step(
            cfg, state, task_id="T1", task_class="impl", work_class="coding", complexity="low"
        )
        assert step == -1

    def test_no_stacking_cap_minus_one(self):
        # Re-gate MED-2: complexity=low + earned streak ⇒ still −1, never −2.
        state, cfg = new_state(), _cfg()
        for tid in ("A", "B", "C"):
            _accept_first_pass(state, tid)
        step = modulate_step(
            cfg, state, task_id="T1", task_class="impl", work_class="coding", complexity="low"
        )
        assert step == -1

    def test_plan_complexity_toggle_off(self):
        # planComplexityDownshift=False disables the complexity leg only.
        state = new_state()
        cfg = _cfg(planComplexityDownshift=False)
        step = modulate_step(
            cfg, state, task_id="T1", task_class="impl", work_class="coding", complexity="low"
        )
        assert step == 0
        for tid in ("A", "B", "C"):
            _accept_first_pass(state, tid)
        assert modulate_step(cfg, state, task_id="T2", task_class="impl", work_class="coding") == -1

    def test_standard_and_high_complexity_no_downshift(self):
        state, cfg = new_state(), _cfg()
        for value in ("standard", "high"):
            step = modulate_step(
                cfg, state, task_id="T1", task_class="impl", work_class="coding", complexity=value
            )
            assert step == 0

    def test_critical_work_never_downshifts(self):
        # AT-L4: judgment NEVER adapts down — downshift is coding-class ONLY.
        state, cfg = new_state(), _cfg()
        for tid in ("A", "B", "C"):
            _accept_first_pass(state, tid)
        step = modulate_step(
            cfg, state, task_id="T1", task_class="impl", work_class="critical", complexity="low"
        )
        assert step == 0

    def test_economy_work_never_downshifts(self):
        # AT-L4 / re-gate LOW-5: economy already sits at its mode's floor.
        state, cfg = new_state(), _cfg()
        for tid in ("A", "B", "C"):
            _accept_first_pass(state, tid)
        step = modulate_step(
            cfg, state, task_id="T1", task_class="impl", work_class="economy", complexity="low"
        )
        assert step == 0

    def test_streaks_are_per_class(self):
        state, cfg = new_state(), _cfg()
        for tid in ("A", "B", "C"):
            _accept_first_pass(state, tid, task_class="impl")
        assert modulate_step(cfg, state, task_id="T1", task_class="docs", work_class="coding") == 0


class TestModulateStepGuards:
    def test_disabled_config_all_zeros(self):
        # AC-1: no adaptive inputs ⇒ the L0 resolution exactly (delta 0 everywhere).
        state = new_state()
        cfg = resolve_adaptive_config(None)
        for tid in ("A", "B", "C"):
            _accept_first_pass(state, tid)
        _reject(state, "T1")
        _reject(state, "T1")
        assert (
            modulate_step(
                cfg, state, task_id="T1", task_class="impl", work_class="coding", complexity="low"
            )
            == 0
        )
        assert state["bumped"] == {}  # a disabled config never consumes the bump

    def test_unknown_complexity_raises(self):
        # AT-L10a: present-but-malformed complexity is a plan-freeze validation
        # failure — RAISES, never silently ignored (D136).
        state, cfg = new_state(), _cfg()
        with pytest.raises(AdaptiveError):
            modulate_step(
                cfg, state, task_id="T1", task_class="impl", work_class="coding", complexity="tiny"
            )

    def test_unknown_work_class_raises(self):
        # AT-L4 / re-gate LOW-5: work_class is the machine-checkable enum term
        # against SKILL_WORK_CLASS — an unknown value is a producer bug (D136).
        state, cfg = new_state(), _cfg()
        with pytest.raises(AdaptiveError):
            modulate_step(cfg, state, task_id="T1", task_class="impl", work_class="build")


# ---------------------------------------------------------------------------
# Module 5 — budget (AT-L12 default + validation; AT-L13 FCFS reservation)
# ---------------------------------------------------------------------------


class TestResolveBudget:
    def test_absent_budget_defaults_to_ten(self):
        # AT-L12: absent budget with the NEW scope form ⇒ N=10 default.
        assert resolve_budget({"events": ["freeze-gate-verdict"]}) == 10

    def test_explicit_calls(self):
        assert resolve_budget({"events": [], "budget": {"calls": 3}}) == 3

    def test_zero_calls_is_legal(self):
        # calls=0 is a deliberate operator no-premium budget, not malformed.
        assert resolve_budget({"events": [], "budget": {"calls": 0}}) == 0

    def test_negative_calls_raises(self):
        with pytest.raises(AdaptiveError):
            resolve_budget({"events": [], "budget": {"calls": -1}})

    def test_bool_calls_raises(self):
        with pytest.raises(AdaptiveError):
            resolve_budget({"events": [], "budget": {"calls": True}})

    def test_non_int_calls_raises(self):
        # AT-L15: a non-int budget ⇒ load-guard RAISE.
        with pytest.raises(AdaptiveError):
            resolve_budget({"events": [], "budget": {"calls": "10"}})

    def test_unknown_budget_key_raises(self):
        with pytest.raises(AdaptiveError):
            resolve_budget({"events": [], "budget": {"calls": 5, "dollars": 1}})

    def test_tokens_out_is_a_known_key(self):
        # AT-L12: optional tokensOut rides alongside calls (unconsumed here).
        assert resolve_budget({"events": [], "budget": {"calls": 5, "tokensOut": 9000}}) == 5

    def test_tokens_out_only_budget_raises(self):
        # Integration seam pin: a present budget object REQUIRES calls — the
        # kata_models load guard raises on this shape, and the two layers must
        # agree (fail-closed hand-edit posture; the AT-L12 degrade rule is an
        # ACCOUNTING rule, not a config-validation leniency).
        with pytest.raises(AdaptiveError, match="REQUIRES 'calls'"):
            resolve_budget({"events": [], "budget": {"tokensOut": 9000}})

    def test_non_dict_budget_raises(self):
        with pytest.raises(AdaptiveError):
            resolve_budget({"events": [], "budget": 10})

    def test_non_dict_scope_raises(self):
        with pytest.raises(AdaptiveError):
            resolve_budget(["critical", "coding"])


class TestBudgetReservation:
    """AT-L13 / acceptance criterion 5: N=3 with RESERVE=2."""

    def test_non_reserved_spends_above_reserve(self):
        state = new_state()
        assert can_spend(3, state, "fix-loop-diagnose") is True

    def test_non_reserved_blocked_at_remaining_equals_reserve(self):
        # NAMED reservation boundary: remaining == RESERVE ⇒ non-reserved blocked
        # (mutation target: > vs >=).
        state = new_state()
        record_spend(state)  # remaining = 2 == RESERVE
        assert can_spend(3, state, "fix-loop-diagnose") is False

    def test_reserved_event_spends_reserve(self):
        state = new_state()
        record_spend(state)
        assert can_spend(3, state, "freeze-gate-verdict") is True
        assert can_spend(3, state, "re-gate-after-hold") is True

    def test_reserved_spends_down_to_zero_then_blocks(self):
        state = new_state()
        for _ in range(3):
            assert can_spend(3, state, "freeze-gate-verdict") is True
            record_spend(state)
        # remaining = 0: even reserved events are exhausted (lapse, AT-L13).
        assert can_spend(3, state, "freeze-gate-verdict") is False

    def test_record_spend_increments(self):
        state = new_state()
        record_spend(state)
        record_spend(state)
        assert state["budgetSpent"] == 2


# ---------------------------------------------------------------------------
# Module 6 — DECISION rendering + recount (AT-L7 durable trail)
# ---------------------------------------------------------------------------


class TestRenderTierDecision:
    def test_format_exact(self):
        line = render_tier_decision("T1", "sonnet", "opus", "failbump")
        assert line == "tier: T1 sonnet->opus reason failbump"

    def test_event_reason(self):
        line = render_tier_decision("freeze-gate", "opus", "fable", "event:freeze-gate-verdict")
        assert line == "tier: freeze-gate opus->fable reason event:freeze-gate-verdict"

    def test_all_static_reasons_render(self):
        for reason in ("failbump", "streak", "complexity", "anchor-switch-reset", "budget-exhausted"):
            assert render_tier_decision("T1", "a", "b", reason).endswith(f"reason {reason}")

    def test_unknown_reason_raises(self):
        with pytest.raises(AdaptiveError):
            render_tier_decision("T1", "sonnet", "opus", "vibes")

    def test_empty_event_name_raises(self):
        with pytest.raises(AdaptiveError):
            render_tier_decision("T1", "sonnet", "opus", "event:")

    def test_whitespace_in_task_raises(self):
        # A space would corrupt the recount trail — fail-closed at render time.
        with pytest.raises(AdaptiveError):
            render_tier_decision("T 1", "sonnet", "opus", "failbump")

    def test_arrow_in_rung_raises(self):
        with pytest.raises(AdaptiveError):
            render_tier_decision("T1", "a->b", "opus", "failbump")


class TestRecountFromDecisions:
    def test_round_trip(self):
        # Render N lines ⇒ recount rebuilds spend + bumped EXACTLY (AT-L7/AT-L13:
        # the tier: lines are the durable counter across conductor compaction).
        payloads = [
            render_tier_decision("freeze-gate", "opus", "fable", "event:freeze-gate-verdict"),
            render_tier_decision("re-gate", "opus", "fable", "event:re-gate-after-hold"),
            render_tier_decision("diag", "sonnet", "opus", "event:fix-loop-diagnose"),  # not premium
            render_tier_decision("T1", "sonnet", "opus", "failbump"),
            render_tier_decision("T2", "opus", "sonnet", "streak"),
            render_tier_decision("T3", "opus", "sonnet", "complexity"),
            "wave: 2 started",  # a non-tier DECISION type — ignored, not malformed
        ]
        result = recount_from_decisions(payloads, "fable")
        assert result == {"budgetSpent": 2, "bumped": {"T1": True}}

    def test_empty_trail(self):
        assert recount_from_decisions([], "fable") == {"budgetSpent": 0, "bumped": {}}

    def test_event_to_non_premium_rung_not_spend(self):
        payloads = [render_tier_decision("diag", "haiku", "sonnet", "event:fix-loop-diagnose")]
        assert recount_from_decisions(payloads, "fable")["budgetSpent"] == 0

    def test_multiple_failbump_tasks(self):
        payloads = [
            render_tier_decision("T1", "sonnet", "opus", "failbump"),
            render_tier_decision("T2", "sonnet", "opus", "failbump"),
        ]
        assert recount_from_decisions(payloads, "fable")["bumped"] == {"T1": True, "T2": True}

    def test_malformed_tier_payload_raises(self):
        # Fail-closed recount: a corrupt trail must never silently under-count
        # spend (AT-L13 / D136).
        with pytest.raises(AdaptiveError):
            recount_from_decisions(["tier: T1 sonnet opus failbump"], "fable")

    def test_tier_payload_missing_arrow_raises(self):
        with pytest.raises(AdaptiveError):
            recount_from_decisions(["tier: T1 sonnetopus reason failbump"], "fable")

    def test_tier_payload_bad_reason_raises(self):
        with pytest.raises(AdaptiveError):
            recount_from_decisions(["tier: T1 sonnet->opus reason vibes"], "fable")

    def test_non_tier_payloads_ignored(self):
        result = recount_from_decisions(["note: anchor switched", "gate: T1 PASS"], "fable")
        assert result == {"budgetSpent": 0, "bumped": {}}


# ---------------------------------------------------------------------------
# Module 7 — anchor switch reset (AT-L17b)
# ---------------------------------------------------------------------------


class TestAnchorSwitchReset:
    def test_reset_clears_adaptive_state_preserves_spend(self):
        # AT-L17b: anchor change resets bump counters/bumped/streaks/dampers;
        # budget spend does NOT reset — money spent is spent.
        state, cfg = new_state(), _cfg()
        _reject(state, "T1", downshifted=True)
        _reject(state, "T1")
        modulate_step(cfg, state, task_id="T1", task_class="impl", work_class="coding")
        _accept_first_pass(state, "T2")
        record_spend(state)
        record_spend(state)
        anchor_switch_reset(state)
        assert state == {
            "bumpCounters": {},
            "bumped": {},
            "streaks": {},
            "dampers": {},
            "budgetSpent": 2,
        }


# ---------------------------------------------------------------------------
# Exec-safety — the no-subprocess structural pin (protocol/exec-safety.md)
# ---------------------------------------------------------------------------


class TestExecSafety:
    def test_no_subprocess_import(self):
        import re
        from pathlib import Path

        source = Path(kata_adaptive.__file__).read_text(encoding="utf-8")
        assert not re.search(r"^\s*(import subprocess|from subprocess)", source, re.M)
        assert "subprocess" not in dir(kata_adaptive)


# ---------------------------------------------------------------------------
# ADVAL folds (pre-merge): state_from_recount (F5), apply_delta (F6/AC-2),
# l2_base_rung (F4/AT-L18)
# ---------------------------------------------------------------------------

LADDER = ["haiku", "sonnet", "opus", "fable"]


class TestStateFromRecount:
    def test_materializes_full_state_from_recount(self):
        state = new_state()
        record_spend(state)
        record_spend(state)
        lines = [
            render_tier_decision("gate-1", "opus", "fable", "event:freeze-gate-verdict"),
            render_tier_decision("gate-2", "opus", "fable", "event:re-gate-after-hold"),
            render_tier_decision("T-3", "sonnet", "opus", "failbump"),
        ]
        recount = recount_from_decisions(lines, "fable")
        full = state_from_recount(recount)
        assert set(full) == {"bumpCounters", "bumped", "streaks", "dampers", "budgetSpent"}
        assert full["budgetSpent"] == state["budgetSpent"] == 2
        assert full["bumped"] == {"T-3": True}
        # The materialized state is CONSUMABLE (F5: the raw recount dict raises):
        cfg = resolve_adaptive_config({})
        assert modulate_step(cfg, full, task_id="T-9", task_class="code",
                             work_class="coding") == 0

    def test_raw_recount_dict_rejected_by_consumers(self):
        # The exact F5 crash, pinned as the designed fail-closed behavior.
        recount = {"budgetSpent": 1, "bumped": {}}
        cfg = resolve_adaptive_config({})
        with pytest.raises(AdaptiveError, match="new_state"):
            modulate_step(cfg, recount, task_id="T", task_class="code", work_class="coding")

    def test_partial_recount_raises(self):
        with pytest.raises(AdaptiveError, match="recount_from_decisions"):
            state_from_recount({"budgetSpent": 1})


class TestApplyDelta:
    """AC-2's executable owner (adval F6): clamp + the AT-L2b OMIT emission."""

    def test_anchor_landing_bump_emits_omit_never_anchor_id(self):
        # NAMED mutation target (AC-2): a +1 landing ON the anchor returns None.
        assert apply_delta(LADDER, "opus", 1, anchor="fable", mode="advanced") is None

    def test_below_anchor_result_emits_explicit_rung(self):
        assert apply_delta(LADDER, "opus", -1, anchor="fable", mode="advanced") == "sonnet"

    def test_essential_ceiling_is_anchor_minus_one(self):
        # +1 from anchor-2 in essential clamps at anchor-1 (never the anchor).
        assert apply_delta(LADDER, "sonnet", 1, anchor="fable", mode="essential") == "opus"
        assert apply_delta(LADDER, "opus", 1, anchor="fable", mode="essential") == "opus"

    def test_essential_sonnet_anchor_bump_is_a_no_op(self):
        # AC-2's degenerate case asserted AS a no-op: sonnet anchor, essential
        # ceiling = haiku; a bumped haiku dispatch clamps back to haiku.
        assert apply_delta(LADDER, "haiku", 1, anchor="sonnet", mode="essential") == "haiku"

    def test_floor_clamp(self):
        assert apply_delta(LADDER, "haiku", -1, anchor="opus", mode="standard") == "haiku"

    def test_none_current_means_at_anchor(self):
        assert apply_delta(LADDER, None, -1, anchor="opus", mode="standard") == "sonnet"
        assert apply_delta(LADDER, None, 0, anchor="opus", mode="standard") is None

    @pytest.mark.parametrize("bad", [("nope", "opus"), ("opus", "nope")])
    def test_unknown_rung_or_anchor_raises(self, bad):
        current, anchor = bad
        with pytest.raises(AdaptiveError):
            apply_delta(LADDER, current, 0, anchor=anchor, mode="standard")

    def test_unknown_mode_raises(self):
        with pytest.raises(AdaptiveError, match="mode"):
            apply_delta(LADDER, "opus", 0, anchor="fable", mode="turbo")


class TestL2BaseRung:
    """AT-L18's shipped contract (adval F4): cheapest qualifying tier, <= L0."""

    ACC = {"code×haiku": 0.90, "code×sonnet": 0.95, "code×opus": 1.0}
    N5 = {"code×haiku": 5, "code×sonnet": 7, "code×opus": 9}

    def test_cheapest_qualifying_tier_wins(self):
        assert l2_base_rung(self.ACC, self.N5, LADDER, "opus", "code") == "haiku"

    def test_theta_boundary_excludes_below(self):
        acc = dict(self.ACC, **{"code×haiku": 0.84})  # < 0.85 by one point
        assert l2_base_rung(acc, self.N5, LADDER, "opus", "code") == "sonnet"

    def test_min_samples_boundary(self):
        n = dict(self.N5, **{"code×haiku": 4})  # below the 5-row floor
        assert l2_base_rung(self.ACC, n, LADDER, "opus", "code") == "sonnet"

    def test_never_above_l0(self):
        # Only the ANCHOR tier qualifies — but L2 may never raise above L0.
        acc = {"code×opus": 1.0}
        n = {"code×opus": 9}
        assert l2_base_rung(acc, n, LADDER, "sonnet", "code") == "sonnet"

    def test_no_data_returns_l0_exactly(self):
        assert l2_base_rung({}, {}, LADDER, "opus", "code") == "opus"

    def test_unknown_l0_raises(self):
        with pytest.raises(AdaptiveError):
            l2_base_rung({}, {}, LADDER, "gpt", "code")


class TestApplyDeltaStrictness:
    """Re-gate N3 fold: out-of-band deltas RAISE (one rung per iteration, AT-L2)."""

    @pytest.mark.parametrize("bad", [7, -9, 2, -2])
    def test_out_of_band_delta_raises(self, bad):
        with pytest.raises(AdaptiveError, match="one rung"):
            apply_delta(LADDER, "opus", bad, anchor="fable", mode="advanced")
