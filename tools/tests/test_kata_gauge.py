"""Tests for kata_gauge.py — the CA-P0 gauge/threshold arithmetic (pure, fail-closed).

Coverage map (E1, PLAN-p0-engine CA-P0):
- read_bridge: superset vs 4-field (%-only) parse; absent/unparseable/missing-field/
  non-numeric RAISES; staleness boundary (299 fresh / 300 fresh / 301 stale — strict >).
- resolve_gauge: CA-L1 reader priority (kata beats user; stale kata → fresh user; both
  stale/absent ⇒ none).
- trigger_crossed: CA-L5 full-token path; CA-L2 %-only degrade; out-of-range fraction RAISES.
- fallback_waves: CA-L4 max(1, floor(…)) floor; zero/negative RAISES.
- backstop_recommendation: CA-L16 three legs (recommend / nothing / floor+note); the
  telemetry-null fallback; the approximate flag (never silent).
- dispatch_budget: CA-L9 WARN@0.31, mandate@0.41, cap-wins identity; out-of-range RAISES.
- validate_context_autonomy: None ⇒ "off" (BC); "on"/"off" ⇒ itself; malformed RAISES.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timezone
from pathlib import Path

import pytest

import kata_gauge
from kata_gauge import GaugeError

# A fixed reference "now" (tz-aware UTC) used across staleness tests.
_NOW = datetime(2026, 7, 4, 12, 0, 0, tzinfo=UTC)
_NOW_EPOCH = _NOW.timestamp()


def _write_bridge(tmp_path: Path, name: str, payload: dict) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def _superset(age_s: float = 0.0, **over) -> dict:
    """A fresh kata superset bridge payload, `age_s` seconds old vs _NOW."""
    payload = {
        "session_id": "sess-kata",
        "remaining_percentage": 40.0,
        "used_pct": 60.0,
        "timestamp": _NOW_EPOCH - age_s,
        "total_tokens": 200_000,
    }
    payload.update(over)
    return payload


def _user_four_field(age_s: float = 0.0, **over) -> dict:
    """A fresh 4-field user bridge payload (no total_tokens ⇒ %-only)."""
    payload = {
        "session_id": "sess-user",
        "remaining_percentage": 55.0,
        "used_pct": 45.0,
        "timestamp": _NOW_EPOCH - age_s,
    }
    payload.update(over)
    return payload


# ---------------------------------------------------------------------------
# Module constants (locked structure / tunable value)
# ---------------------------------------------------------------------------


class TestConstants:
    def test_staleness_default(self):
        assert kata_gauge.STALENESS_S == 300

    def test_trigger_fraction_default(self):
        assert kata_gauge.DEFAULT_TRIGGER_FRACTION == 0.70

    def test_est_wave_burn_default(self):
        assert kata_gauge.EST_WAVE_BURN_DEFAULT == 40_000

    def test_backstop_floor_and_fraction(self):
        assert kata_gauge.BACKSTOP_KEY_FLOOR == 100_000
        assert kata_gauge.BACKSTOP_GAP_WINDOW_FRACTION == 0.10

    def test_dispatch_constants(self):
        assert kata_gauge.WORK_QUANTUM == 0.40
        assert kata_gauge.HARD_CAP == 0.80
        assert kata_gauge.OVER_BRIEF_WARN == 0.30
        assert kata_gauge.OVER_BRIEF_MANDATE == 0.40


# ---------------------------------------------------------------------------
# read_bridge
# ---------------------------------------------------------------------------


class TestReadBridge:
    def test_superset_parses_full_mode(self, tmp_path):
        p = _write_bridge(tmp_path, "kata.json", _superset())
        g = kata_gauge.read_bridge(p, now_utc=_NOW)
        assert g["mode"] == "full"
        assert g["total_tokens"] == 200_000
        assert g["used_pct"] == 60.0
        assert g["stale"] is False

    def test_four_field_parses_percentage_only(self, tmp_path):
        p = _write_bridge(tmp_path, "user.json", _user_four_field())
        g = kata_gauge.read_bridge(p, now_utc=_NOW)
        assert g["mode"] == "percentage-only"
        assert g["total_tokens"] is None
        assert g["stale"] is False

    def test_absent_file_raises(self, tmp_path):
        with pytest.raises(GaugeError):
            kata_gauge.read_bridge(tmp_path / "nope.json", now_utc=_NOW)

    def test_unparseable_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        with pytest.raises(GaugeError):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    def test_missing_required_field_raises(self, tmp_path):
        payload = _superset()
        del payload["used_pct"]
        p = _write_bridge(tmp_path, "miss.json", payload)
        with pytest.raises(GaugeError):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    def test_non_numeric_field_raises(self, tmp_path):
        p = _write_bridge(tmp_path, "nn.json", _superset(remaining_percentage="lots"))
        with pytest.raises(GaugeError):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    def test_bool_is_not_numeric_field(self, tmp_path):
        # bool subclasses int; a bool in a numeric field is malformed ⇒ RAISES.
        p = _write_bridge(tmp_path, "b.json", _superset(used_pct=True))
        with pytest.raises(GaugeError):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    def test_non_numeric_total_tokens_raises(self, tmp_path):
        p = _write_bridge(tmp_path, "tt.json", _superset(total_tokens="big"))
        with pytest.raises(GaugeError):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    def test_staleness_299_is_fresh(self, tmp_path):
        p = _write_bridge(tmp_path, "f.json", _superset(age_s=299))
        assert kata_gauge.read_bridge(p, now_utc=_NOW)["stale"] is False

    def test_staleness_300_is_fresh_strict(self, tmp_path):
        # "older than 300 s" ⇒ exactly 300 is NOT older ⇒ fresh (strict >).
        p = _write_bridge(tmp_path, "b.json", _superset(age_s=300))
        assert kata_gauge.read_bridge(p, now_utc=_NOW)["stale"] is False

    def test_staleness_301_is_stale(self, tmp_path):
        p = _write_bridge(tmp_path, "s.json", _superset(age_s=301))
        assert kata_gauge.read_bridge(p, now_utc=_NOW)["stale"] is True

    def test_now_utc_must_be_datetime(self, tmp_path):
        p = _write_bridge(tmp_path, "k.json", _superset())
        with pytest.raises(GaugeError):
            kata_gauge.read_bridge(p, now_utc=_NOW_EPOCH)  # float, not datetime


# ---------------------------------------------------------------------------
# resolve_gauge — CA-L1 reader priority
# ---------------------------------------------------------------------------


class TestResolveGauge:
    def test_kata_beats_user(self, tmp_path):
        k = _write_bridge(tmp_path, "kata.json", _superset())
        u = _write_bridge(tmp_path, "user.json", _user_four_field())
        r = kata_gauge.resolve_gauge(k, u, now_utc=_NOW)
        assert r["source"] == "kata"
        assert r["session_id"] == "sess-kata"

    def test_stale_kata_falls_to_fresh_user(self, tmp_path):
        k = _write_bridge(tmp_path, "kata.json", _superset(age_s=400))
        u = _write_bridge(tmp_path, "user.json", _user_four_field())
        r = kata_gauge.resolve_gauge(k, u, now_utc=_NOW)
        assert r["source"] == "user"
        assert r["session_id"] == "sess-user"

    def test_absent_kata_falls_to_user(self, tmp_path):
        u = _write_bridge(tmp_path, "user.json", _user_four_field())
        r = kata_gauge.resolve_gauge(tmp_path / "nope.json", u, now_utc=_NOW)
        assert r["source"] == "user"

    def test_corrupt_kata_falls_to_user(self, tmp_path):
        k = tmp_path / "kata.json"
        k.write_text("{corrupt", encoding="utf-8")
        u = _write_bridge(tmp_path, "user.json", _user_four_field())
        r = kata_gauge.resolve_gauge(k, u, now_utc=_NOW)
        assert r["source"] == "user"

    def test_both_stale_is_none(self, tmp_path):
        k = _write_bridge(tmp_path, "kata.json", _superset(age_s=400))
        u = _write_bridge(tmp_path, "user.json", _user_four_field(age_s=400))
        r = kata_gauge.resolve_gauge(k, u, now_utc=_NOW)
        assert r["source"] == "none"

    def test_both_absent_is_none(self, tmp_path):
        r = kata_gauge.resolve_gauge(
            tmp_path / "a.json", tmp_path / "b.json", now_utc=_NOW
        )
        assert r["source"] == "none"

    def test_user_path_none_skips_leg(self, tmp_path):
        r = kata_gauge.resolve_gauge(tmp_path / "a.json", None, now_utc=_NOW)
        assert r["source"] == "none"


# ---------------------------------------------------------------------------
# trigger_crossed — CA-L5 / CA-L2
# ---------------------------------------------------------------------------


class TestTriggerCrossed:
    def test_full_mode_crossed(self):
        g = {"mode": "full", "used_pct": 75.0, "total_tokens": 200_000}
        assert kata_gauge.trigger_crossed(g, 0.70) is True

    def test_full_mode_not_crossed(self):
        g = {"mode": "full", "used_pct": 60.0, "total_tokens": 200_000}
        assert kata_gauge.trigger_crossed(g, 0.70) is False

    def test_full_mode_exact_boundary_crosses(self):
        # used == fraction ⇒ crossed (>=): 70% of a 200k window.
        g = {"mode": "full", "used_pct": 70.0, "total_tokens": 200_000}
        assert kata_gauge.trigger_crossed(g, 0.70) is True

    def test_percentage_only_crossed(self):
        g = {"mode": "percentage-only", "used_pct": 72.0, "total_tokens": None}
        assert kata_gauge.trigger_crossed(g, 0.70) is True

    def test_percentage_only_not_crossed(self):
        g = {"mode": "percentage-only", "used_pct": 65.0, "total_tokens": None}
        assert kata_gauge.trigger_crossed(g) is False  # default 0.70

    def test_default_fraction_is_070(self):
        g = {"mode": "percentage-only", "used_pct": 70.0, "total_tokens": None}
        assert kata_gauge.trigger_crossed(g) is True

    def test_fraction_zero_raises(self):
        g = {"mode": "percentage-only", "used_pct": 70.0, "total_tokens": None}
        with pytest.raises(GaugeError):
            kata_gauge.trigger_crossed(g, 0.0)

    def test_fraction_one_raises(self):
        g = {"mode": "percentage-only", "used_pct": 70.0, "total_tokens": None}
        with pytest.raises(GaugeError):
            kata_gauge.trigger_crossed(g, 1.0)

    def test_missing_used_pct_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.trigger_crossed({"mode": "full", "total_tokens": 1}, 0.70)

    def test_none_source_gauge_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.trigger_crossed({"source": "none"}, 0.70)


# ---------------------------------------------------------------------------
# fallback_waves — CA-L4
# ---------------------------------------------------------------------------


class TestFallbackWaves:
    def test_basic_floor(self):
        # floor(140000 / 40000) = 3
        assert kata_gauge.fallback_waves(140_000, 40_000) == 3

    def test_default_est_wave_burn(self):
        assert kata_gauge.fallback_waves(140_000) == 3

    def test_max_one_floor(self):
        # floor(10000 / 40000) = 0 ⇒ max(1, 0) = 1
        assert kata_gauge.fallback_waves(10_000, 40_000) == 1

    def test_exact_multiple(self):
        assert kata_gauge.fallback_waves(80_000, 40_000) == 2

    def test_zero_trigger_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.fallback_waves(0, 40_000)

    def test_negative_trigger_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.fallback_waves(-1, 40_000)

    def test_zero_burn_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.fallback_waves(40_000, 0)

    def test_non_numeric_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.fallback_waves("140000", 40_000)


# ---------------------------------------------------------------------------
# backstop_recommendation — CA-L16
# ---------------------------------------------------------------------------


class TestBackstopRecommendation:
    def test_normal_recommend_leg(self):
        # gap = max(20000+5000, 0.10*200000=20000) = 25000
        # target+gap = 150000+25000 = 175000, within [100k, 1M) ⇒ recommend it
        r = kata_gauge.backstop_recommendation(
            target_tokens=150_000,
            worst_boundary_burn=20_000,
            handoff_write_cost=5_000,
            effective_window=200_000,
            model_max=1_000_000,
        )
        assert r["recommend"] == 175_000
        assert r["approximate"] is False

    def test_recommend_nothing_when_ge_model_max(self):
        # target+gap >= model_max ⇒ recommend NOTHING
        r = kata_gauge.backstop_recommendation(
            target_tokens=190_000,
            worst_boundary_burn=None,
            handoff_write_cost=None,
            effective_window=200_000,
            model_max=200_000,
        )
        assert r["recommend"] is None
        assert r["note"] is not None

    def test_floor_leg_when_below_100k(self):
        # small window: gap fallback = 0.10*50000 = 5000; target+gap = 40000+5000 = 45000
        # < 100k floor ⇒ recommend the 100k floor + rotation note
        r = kata_gauge.backstop_recommendation(
            target_tokens=40_000,
            worst_boundary_burn=None,
            handoff_write_cost=None,
            effective_window=50_000,
            model_max=1_000_000,
        )
        assert r["recommend"] == 100_000
        assert "rotation" in r["note"].lower()

    def test_null_telemetry_falls_to_window_fraction(self):
        # both telemetry terms None ⇒ gap = 0.10 * effective_window
        r = kata_gauge.backstop_recommendation(
            target_tokens=150_000,
            worst_boundary_burn=None,
            handoff_write_cost=None,
            effective_window=200_000,
            model_max=1_000_000,
        )
        # gap = 20000 ⇒ 170000
        assert r["recommend"] == 170_000

    def test_approximate_flag_is_surfaced_in_note(self):
        r = kata_gauge.backstop_recommendation(
            target_tokens=150_000,
            worst_boundary_burn=20_000,
            handoff_write_cost=5_000,
            effective_window=200_000,
            model_max=1_000_000,
            approximate=True,
        )
        assert r["approximate"] is True
        assert r["note"] is not None
        assert "approx" in r["note"].lower()

    def test_worst_burn_dominates_window_fraction(self):
        # gap = max(90000+10000=100000, 0.10*200000=20000) = 100000
        r = kata_gauge.backstop_recommendation(
            target_tokens=150_000,
            worst_boundary_burn=90_000,
            handoff_write_cost=10_000,
            effective_window=200_000,
            model_max=1_000_000,
        )
        assert r["recommend"] == 250_000

    def test_bad_target_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.backstop_recommendation(
                target_tokens=0,
                worst_boundary_burn=None,
                handoff_write_cost=None,
                effective_window=200_000,
                model_max=1_000_000,
            )

    def test_bad_model_max_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.backstop_recommendation(
                target_tokens=150_000,
                worst_boundary_burn=None,
                handoff_write_cost=None,
                effective_window=200_000,
                model_max=0,
            )

    def test_negative_burn_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.backstop_recommendation(
                target_tokens=150_000,
                worst_boundary_burn=-1,
                handoff_write_cost=5_000,
                effective_window=200_000,
                model_max=1_000_000,
            )


# ---------------------------------------------------------------------------
# dispatch_budget — CA-L9
# ---------------------------------------------------------------------------


class TestDispatchBudget:
    def test_healthy_startup(self):
        r = kata_gauge.dispatch_budget(0.05)
        assert r["budget_fraction"] == pytest.approx(0.45)
        assert r["cap_fraction"] == 0.80
        assert r["warn"] is False
        assert r["over_briefed"] is False

    def test_warn_at_031(self):
        r = kata_gauge.dispatch_budget(0.31)
        assert r["warn"] is True
        assert r["over_briefed"] is False

    def test_no_warn_at_030_exact(self):
        # WARN at startup > 0.30 (strict) ⇒ exactly 0.30 does not warn.
        r = kata_gauge.dispatch_budget(0.30)
        assert r["warn"] is False

    def test_mandate_at_041(self):
        r = kata_gauge.dispatch_budget(0.41)
        assert r["over_briefed"] is True
        assert r["warn"] is True  # mandate is above the warn threshold too

    def test_no_mandate_at_040_exact(self):
        r = kata_gauge.dispatch_budget(0.40)
        assert r["over_briefed"] is False

    def test_cap_wins_identity(self):
        # startup > 0.40 ⇒ budget_fraction pinned to the 0.80 cap (cap WINS).
        r = kata_gauge.dispatch_budget(0.50)
        assert r["budget_fraction"] == 0.80
        assert r["over_briefed"] is True

    def test_zero_startup_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.dispatch_budget(0.0)

    def test_one_startup_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.dispatch_budget(1.0)

    def test_non_numeric_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.dispatch_budget("0.3")


# ---------------------------------------------------------------------------
# validate_context_autonomy — the load-guard mechanical leg
# ---------------------------------------------------------------------------


class TestValidateContextAutonomy:
    def test_none_is_off(self):
        # CA-A8 row-2/3 mechanical pin: absent-at-load ⇒ OFF (BC).
        assert kata_gauge.validate_context_autonomy(None) == "off"

    def test_on_passes(self):
        assert kata_gauge.validate_context_autonomy("on") == "on"

    def test_off_passes(self):
        assert kata_gauge.validate_context_autonomy("off") == "off"

    def test_case_variant_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.validate_context_autonomy("On")

    def test_unknown_string_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.validate_context_autonomy("enabled")

    def test_wrong_type_raises(self):
        with pytest.raises(GaugeError):
            kata_gauge.validate_context_autonomy(True)


# ---------------------------------------------------------------------------
# Exec-safety — pure module, no subprocess sink
# ---------------------------------------------------------------------------


class TestExecSafety:
    """kata_gauge.py is pure: no subprocess import, no exec sink."""

    def test_no_subprocess_import(self):
        src = Path(kata_gauge.__file__).read_text(encoding="utf-8")
        hits = [
            m.group()
            for m in re.finditer(
                r"^\s*(?:import|from)\s+subprocess\b", src, re.MULTILINE
            )
        ]
        assert not hits, (
            f"subprocess import found in kata_gauge.py: {hits} — "
            "kata_gauge spawns NO subprocess (pure; exec-safety.md)"
        )


# ---------------------------------------------------------------------------
# Final-review fold (v0.2.1 merge gate): numeric sanity on bridge fields.
# A corrupt gauge must RAISE GaugeError (walk the CA-L1 leg), never parse as
# a fresh usable gauge that silently suppresses the trigger (D136).
# ---------------------------------------------------------------------------


class TestBridgeNumericSanity:
    """Fold of the final-review engine findings 1-3: NaN/Infinity/out-of-range
    bridge numerics must fail closed as GaugeError, so resolve_gauge walks the
    next reader-priority leg instead of anchoring on a corrupt gauge."""

    def test_nan_used_pct_raises(self, tmp_path):
        # NAMED: the never-triggers vector — NaN >= threshold is always False.
        p = _write_bridge(tmp_path, "k.json", _superset(used_pct=float("nan")))
        with pytest.raises(GaugeError, match="finite"):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    def test_infinity_total_tokens_raises_gauge_error_not_overflow(self, tmp_path):
        # int(inf) raised OverflowError THROUGH resolve_gauge before the fold.
        p = _write_bridge(tmp_path, "k.json", _superset(total_tokens=float("inf")))
        with pytest.raises(GaugeError):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    def test_nan_total_tokens_raises_gauge_error_not_valueerror(self, tmp_path):
        p = _write_bridge(tmp_path, "k.json", _superset(total_tokens=float("nan")))
        with pytest.raises(GaugeError):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    @pytest.mark.parametrize("bad_pct", [-75.0, 150.0, -0.001, 100.001])
    def test_out_of_range_percentages_raise(self, tmp_path, bad_pct):
        p = _write_bridge(tmp_path, "k.json", _superset(used_pct=bad_pct))
        with pytest.raises(GaugeError, match="0..100"):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    @pytest.mark.parametrize("bad_total", [0, -500_000])
    def test_nonpositive_total_tokens_raises(self, tmp_path, bad_total):
        # total_tokens <= 0 made trigger_crossed True at ANY usage (thrash) and
        # blew up fallback_waves(0) downstream — a malformed gauge, fail closed.
        p = _write_bridge(tmp_path, "k.json", _superset(total_tokens=bad_total))
        with pytest.raises(GaugeError, match="positive"):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    def test_nan_timestamp_raises(self, tmp_path):
        p = _write_bridge(tmp_path, "k.json", _superset(timestamp=float("nan")))
        with pytest.raises(GaugeError, match="finite"):
            kata_gauge.read_bridge(p, now_utc=_NOW)

    def test_corrupt_kata_bridge_walks_to_healthy_user_leg(self, tmp_path):
        # NAMED: the shadowing vector — before the fold a NaN kata bridge WON the
        # CA-L1 priority walk over a healthy user bridge and suppressed its trigger.
        kata = _write_bridge(tmp_path, "k.json", _superset(used_pct=float("nan")))
        user = _write_bridge(tmp_path, "u.json", _user_four_field(used_pct=92.0,
                                                                  remaining_percentage=8.0))
        resolved = kata_gauge.resolve_gauge(kata, user, now_utc=_NOW)
        assert resolved["source"] == "user"
        assert kata_gauge.trigger_crossed(resolved) is True

    def test_both_corrupt_resolves_none(self, tmp_path):
        kata = _write_bridge(tmp_path, "k.json", _superset(total_tokens=0))
        user = _write_bridge(tmp_path, "u.json", _user_four_field(used_pct=-5.0))
        assert kata_gauge.resolve_gauge(kata, user, now_utc=_NOW) == {"source": "none"}

    @pytest.mark.parametrize("field", ["used_pct", "total_tokens", "timestamp"])
    def test_astronomical_int_raises_gauge_error_not_overflow(self, tmp_path, field):
        # json.loads parses arbitrary-precision ints; float(10**400) raises
        # OverflowError AT the guard — must surface as GaugeError (walk the leg).
        p = _write_bridge(tmp_path, "k.json", _superset(**{field: 10**400}))
        with pytest.raises(GaugeError):
            kata_gauge.read_bridge(p, now_utc=_NOW)
