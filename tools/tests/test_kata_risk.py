"""Tests for kata_risk.py — the M4-P1 risk score + trigger decision + override resolver.

Coverage map:
- Module 1 (risk_score + constants): the A1-Q4 arithmetic pins, the unknown-signal
  guard, None-slack absent, the capped sum, missing-key-absent.
- Module 2 (should_trigger): every hard signal alone triggers every class; no lone soft
  signal triggers; code slack-alone never triggers; the strict ``>`` boundary (score ==
  tau does NOT trigger); the missing-record hard signal; the unknown-class guard.
- Module 3 (resolve_inline_eval_params): string/None ⇒ defaults; dict overrides
  validated; mode-less-object raise; whole-config-by-mistake raise; malformed overrides.
- Exec-safety: the no-subprocess-import structural pin.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import kata_risk

_TESTS = Path(__file__).resolve().parent
_TOOLS = _TESTS.parent


# ---------------------------------------------------------------------------
# Module 1 — risk_score + constants (A1-Q4 arithmetic)
# ---------------------------------------------------------------------------


class TestDefaults:
    """The A1-Q4 defaults are DATA'd exactly as the design pins them."""

    def test_default_weights_values(self):
        assert kata_risk.DEFAULT_WEIGHTS == {
            "verify_fail": 0.60,
            "lane_drift": 0.60,
            "missing_record": 0.60,
            "slack_ge_2x": 0.30,
        }

    def test_default_tau_values(self):
        assert kata_risk.DEFAULT_TAU == {"code": 0.50, "research": 0.45, "debug": 0.45}


class TestRiskScore:
    """risk_score: capped sum of active-signal weights (M4-L4)."""

    def test_all_absent_is_zero(self):
        assert kata_risk.risk_score({}, kata_risk.DEFAULT_WEIGHTS) == 0.0

    def test_single_hard_signal_is_its_weight(self):
        score = kata_risk.risk_score({"verify_fail": True}, kata_risk.DEFAULT_WEIGHTS)
        assert score == 0.60

    def test_missing_key_is_absent(self):
        # lane_drift/missing_record/slack_ratio all absent ⇒ only verify_fail counts.
        score = kata_risk.risk_score({"verify_fail": True}, kata_risk.DEFAULT_WEIGHTS)
        assert score == 0.60

    def test_false_hard_signal_scores_zero(self):
        score = kata_risk.risk_score(
            {"verify_fail": False, "lane_drift": False, "missing_record": False},
            kata_risk.DEFAULT_WEIGHTS,
        )
        assert score == 0.0

    def test_slack_ratio_below_threshold_absent(self):
        score = kata_risk.risk_score({"slack_ratio": 1.9}, kata_risk.DEFAULT_WEIGHTS)
        assert score == 0.0

    def test_slack_ratio_at_threshold_fires(self):
        score = kata_risk.risk_score({"slack_ratio": 2.0}, kata_risk.DEFAULT_WEIGHTS)
        assert score == 0.30

    def test_none_slack_ratio_absent(self):
        score = kata_risk.risk_score({"slack_ratio": None}, kata_risk.DEFAULT_WEIGHTS)
        assert score == 0.0

    def test_capped_sum_at_one(self):
        # 0.60 * 3 + 0.30 = 2.10 ⇒ capped to 1.0.
        score = kata_risk.risk_score(
            {
                "verify_fail": True,
                "lane_drift": True,
                "missing_record": True,
                "slack_ratio": 3.0,
            },
            kata_risk.DEFAULT_WEIGHTS,
        )
        assert score == 1.0

    def test_unknown_signal_key_raises(self):
        # NAMED: unknown-signal guard mutation target.
        with pytest.raises(kata_risk.RiskError, match=r"unknown signal key"):
            kata_risk.risk_score(
                {"verify_fail": True, "bogus_signal": True}, kata_risk.DEFAULT_WEIGHTS
            )

    def test_slack_ratio_is_not_an_unknown_key(self):
        # gate v1 LOW-11: slack_ratio is a recognized input field, never unknown.
        score = kata_risk.risk_score(
            {"slack_ratio": 2.5}, kata_risk.DEFAULT_WEIGHTS
        )
        assert score == 0.30


# ---------------------------------------------------------------------------
# Module 2 — should_trigger (strict score > tau ⇒ trigger)
# ---------------------------------------------------------------------------


def _record(exit_code: int = 0) -> dict:
    """A minimal parsed checkpoint record with the given verify exit."""
    return {"v": 1, "i": 0, "verify": {"exit": exit_code}}


class TestShouldTriggerArithmetic:
    """A1-Q4 arithmetic PINNED: every hard signal alone crosses every tau; no lone
    soft signal crosses any tau; code slack-alone never triggers."""

    HARD_ARGS = {
        "verify_fail": dict(record_or_none=_record(1), lane_drift=False, slack_ratio=None),
        "lane_drift": dict(record_or_none=_record(0), lane_drift=True, slack_ratio=None),
        "missing_record": dict(record_or_none=None, lane_drift=False, slack_ratio=None),
    }

    @pytest.mark.parametrize("task_class", ["code", "research", "debug"])
    @pytest.mark.parametrize("signal", ["verify_fail", "lane_drift", "missing_record"])
    def test_every_hard_signal_alone_triggers_every_class(self, signal, task_class):
        result = kata_risk.should_trigger(task_class=task_class, **self.HARD_ARGS[signal])
        assert result["score"] == 0.60
        assert result["triggered"] is True

    @pytest.mark.parametrize("task_class", ["code", "research", "debug"])
    def test_lone_soft_slack_never_triggers_any_class(self, task_class):
        # slack alone = 0.30 < every tau (0.45/0.50) ⇒ never triggers pre-calibration.
        result = kata_risk.should_trigger(
            _record(0), lane_drift=False, slack_ratio=5.0, task_class=task_class
        )
        assert result["score"] == 0.30
        assert result["triggered"] is False

    def test_code_slack_alone_never_triggers(self):
        # Code's only soft signal is slack; 0.30 < 0.50 ⇒ code triggers on hard evidence only.
        result = kata_risk.should_trigger(
            _record(0), lane_drift=False, slack_ratio=10.0, task_class="code"
        )
        assert result["triggered"] is False

    def test_clean_checkpoint_does_not_trigger(self):
        result = kata_risk.should_trigger(
            _record(0), lane_drift=False, slack_ratio=None, task_class="code"
        )
        assert result["score"] == 0.0
        assert result["triggered"] is False

    def test_missing_record_is_hard_signal(self):
        # A1-Q2: None record on a checkpoint commit under mode `on` ⇒ missing_record hard.
        result = kata_risk.should_trigger(
            None, lane_drift=False, slack_ratio=None, task_class="code"
        )
        assert result["signals"]["missing_record"] is True
        assert result["score"] == 0.60
        assert result["triggered"] is True

    def test_returned_vector_shape(self):
        result = kata_risk.should_trigger(
            _record(1), lane_drift=True, slack_ratio=2.0, task_class="code"
        )
        assert set(result) == {"triggered", "score", "signals", "tau"}
        assert result["tau"] == 0.50
        assert result["signals"] == {
            "verify_fail": True,
            "lane_drift": True,
            "missing_record": False,
            "slack_ratio": 2.0,
        }


class TestShouldTriggerBoundary:
    """The strict-`>` comparator: score == tau does NOT trigger (M4-L4 verbatim).

    Mutating `>` to `>=` turns test_score_equal_tau_does_not_trigger RED.
    """

    def test_score_equal_tau_does_not_trigger(self):
        # NAMED: the `>` comparator mutation target. Custom weights put a single hard
        # signal at EXACTLY the code tau (0.50), so score == tau == 0.50.
        boundary_weights = {
            "verify_fail": 0.50,
            "lane_drift": 0.60,
            "missing_record": 0.60,
            "slack_ge_2x": 0.30,
        }
        result = kata_risk.should_trigger(
            _record(1),
            lane_drift=False,
            slack_ratio=None,
            task_class="code",
            weights=boundary_weights,
        )
        assert result["score"] == 0.50
        assert result["tau"] == 0.50
        assert result["triggered"] is False  # strict `>`: equality does NOT trigger

    def test_score_just_above_tau_triggers(self):
        # The companion: one epsilon above the boundary DOES trigger (strict `>` holds).
        boundary_weights = {
            "verify_fail": 0.51,
            "lane_drift": 0.60,
            "missing_record": 0.60,
            "slack_ge_2x": 0.30,
        }
        result = kata_risk.should_trigger(
            _record(1),
            lane_drift=False,
            slack_ratio=None,
            task_class="code",
            weights=boundary_weights,
        )
        assert result["score"] == 0.51
        assert result["triggered"] is True


class TestShouldTriggerGuards:
    """Fail-closed guards on the decision function."""

    def test_unknown_task_class_raises(self):
        # NAMED: unknown-class guard mutation target.
        with pytest.raises(kata_risk.RiskError, match=r"unknown task_class"):
            kata_risk.should_trigger(
                _record(0), lane_drift=False, slack_ratio=None, task_class="marketing"
            )

    def test_custom_tau_override_selects_class(self):
        result = kata_risk.should_trigger(
            _record(0),
            lane_drift=False,
            slack_ratio=2.0,
            task_class="code",
            tau={"code": 0.25, "research": 0.45, "debug": 0.45},
        )
        # slack 0.30 > custom code tau 0.25 ⇒ triggers under the override.
        assert result["tau"] == 0.25
        assert result["triggered"] is True


# ---------------------------------------------------------------------------
# Module 3 — resolve_inline_eval_params (the inlineEval VALUE, never the whole config)
# ---------------------------------------------------------------------------


class TestResolveDefaults:
    """String / None values ⇒ the untouched defaults (BC: no override surface)."""

    def test_none_value_returns_defaults(self):
        result = kata_risk.resolve_inline_eval_params(None)
        assert result == {"weights": kata_risk.DEFAULT_WEIGHTS, "tau": kata_risk.DEFAULT_TAU}

    @pytest.mark.parametrize("mode", ["off", "telemetry", "on"])
    def test_string_value_returns_defaults(self, mode):
        result = kata_risk.resolve_inline_eval_params(mode)
        assert result == {"weights": kata_risk.DEFAULT_WEIGHTS, "tau": kata_risk.DEFAULT_TAU}

    def test_defaults_are_copies_not_aliases(self):
        result = kata_risk.resolve_inline_eval_params(None)
        result["weights"]["verify_fail"] = 0.99
        result["tau"]["code"] = 0.99
        # Mutating the returned dicts must not corrupt the module constants.
        assert kata_risk.DEFAULT_WEIGHTS["verify_fail"] == 0.60
        assert kata_risk.DEFAULT_TAU["code"] == 0.50


class TestResolveOverrides:
    """Object-form values with valid overrides merge onto the defaults."""

    def test_mode_only_object_returns_defaults(self):
        result = kata_risk.resolve_inline_eval_params({"mode": "on"})
        assert result == {"weights": kata_risk.DEFAULT_WEIGHTS, "tau": kata_risk.DEFAULT_TAU}

    def test_weights_override_merges(self):
        result = kata_risk.resolve_inline_eval_params(
            {"mode": "on", "weights": {"slack_ge_2x": 0.40}}
        )
        assert result["weights"]["slack_ge_2x"] == 0.40
        # Untouched signals keep their default.
        assert result["weights"]["verify_fail"] == 0.60

    def test_tau_override_merges(self):
        result = kata_risk.resolve_inline_eval_params(
            {"mode": "on", "tau": {"code": 0.70}}
        )
        assert result["tau"]["code"] == 0.70
        assert result["tau"]["research"] == 0.45

    def test_tau_boundary_one_is_valid(self):
        result = kata_risk.resolve_inline_eval_params({"mode": "on", "tau": {"code": 1.0}})
        assert result["tau"]["code"] == 1.0

    def test_int_override_coerced_to_float(self):
        result = kata_risk.resolve_inline_eval_params({"mode": "on", "tau": {"code": 1}})
        assert result["tau"]["code"] == 1.0


class TestResolveGuards:
    """Fail-closed guards — load-guard STOP material (GB12/D45)."""

    def test_mode_less_object_raises(self):
        # NAMED: re-gate v2 HIGH-1 — a present-but-mode-less object must STOP.
        with pytest.raises(kata_risk.RiskError, match=r"requires a 'mode' key"):
            kata_risk.resolve_inline_eval_params({"tau": {"code": 0.40}})

    def test_whole_config_by_mistake_raises(self):
        # NAMED: a dict carrying an `inlineEval` key is a whole-config mistake ⇒
        # unknown-key raise (has `mode`, so it passes the mode check first).
        with pytest.raises(kata_risk.RiskError, match=r"unknown inlineEval key"):
            kata_risk.resolve_inline_eval_params(
                {"mode": "on", "inlineEval": "on", "runShape": "project"}
            )

    def test_unknown_top_level_key_raises(self):
        with pytest.raises(kata_risk.RiskError, match=r"unknown inlineEval key"):
            kata_risk.resolve_inline_eval_params({"mode": "on", "bogus": 1})

    def test_non_dict_value_raises(self):
        with pytest.raises(kata_risk.RiskError, match=r"must be a string, dict, or"):
            kata_risk.resolve_inline_eval_params(42)

    def test_unknown_weights_signal_key_raises(self):
        # NAMED: malformed-override guard mutation target (unknown signal key leg).
        with pytest.raises(kata_risk.RiskError, match=r"unknown weights signal key"):
            kata_risk.resolve_inline_eval_params(
                {"mode": "on", "weights": {"citation_integrity": 0.60}}
            )

    def test_unknown_tau_class_key_raises(self):
        with pytest.raises(kata_risk.RiskError, match=r"unknown tau class key"):
            kata_risk.resolve_inline_eval_params({"mode": "on", "tau": {"marketing": 0.40}})

    def test_non_numeric_weight_raises(self):
        with pytest.raises(kata_risk.RiskError, match=r"must be numeric"):
            kata_risk.resolve_inline_eval_params(
                {"mode": "on", "weights": {"verify_fail": "high"}}
            )

    def test_bool_weight_rejected_as_non_numeric(self):
        # bool subclasses int — must be rejected, not silently accepted as 1.0.
        with pytest.raises(kata_risk.RiskError, match=r"must be numeric"):
            kata_risk.resolve_inline_eval_params(
                {"mode": "on", "weights": {"verify_fail": True}}
            )

    def test_non_numeric_tau_raises(self):
        with pytest.raises(kata_risk.RiskError, match=r"must be numeric"):
            kata_risk.resolve_inline_eval_params({"mode": "on", "tau": {"code": "low"}})

    def test_tau_zero_raises(self):
        # NAMED: malformed-override guard mutation target (tau range leg).
        with pytest.raises(kata_risk.RiskError, match=r"outside"):
            kata_risk.resolve_inline_eval_params({"mode": "on", "tau": {"code": 0.0}})

    def test_tau_above_one_raises(self):
        with pytest.raises(kata_risk.RiskError, match=r"outside"):
            kata_risk.resolve_inline_eval_params({"mode": "on", "tau": {"code": 1.5}})

    def test_non_dict_weights_block_raises(self):
        with pytest.raises(kata_risk.RiskError, match=r"'weights' must be an object"):
            kata_risk.resolve_inline_eval_params({"mode": "on", "weights": [0.6]})

    def test_non_dict_tau_block_raises(self):
        with pytest.raises(kata_risk.RiskError, match=r"'tau' must be an object"):
            kata_risk.resolve_inline_eval_params({"mode": "on", "tau": 0.5})


class TestResolveIntegration:
    """The resolver's output feeds should_trigger directly."""

    def test_resolved_override_drives_trigger(self):
        params = kata_risk.resolve_inline_eval_params(
            {"mode": "on", "tau": {"code": 0.25}}
        )
        result = kata_risk.should_trigger(
            _record(0),
            lane_drift=False,
            slack_ratio=2.0,
            task_class="code",
            weights=params["weights"],
            tau=params["tau"],
        )
        # slack 0.30 > lowered code tau 0.25 ⇒ triggers.
        assert result["triggered"] is True


# ---------------------------------------------------------------------------
# Exec-safety — source-scan structural pin (mirrors TestExecSafety in test_benchmark.py)
# ---------------------------------------------------------------------------


class TestExecSafety:
    """kata_risk.py is pure: no subprocess import, no exec sink."""

    def _source(self) -> str:
        return (_TOOLS / "kata_risk.py").read_text(encoding="utf-8")

    def test_no_subprocess_import(self):
        """kata_risk.py must NOT import subprocess (pure decision code, zero exec sink)."""
        hits = [
            m.group()
            for m in re.finditer(
                r"^\s*(?:import|from)\s+subprocess\b", self._source(), re.MULTILINE
            )
        ]
        assert not hits, (
            f"subprocess import found in kata_risk.py: {hits} — "
            "kata_risk spawns NO subprocess (pure; exec-safety.md)"
        )
