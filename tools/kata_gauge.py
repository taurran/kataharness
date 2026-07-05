"""kata_gauge.py — CA-P0 context-autonomy gauge/threshold arithmetic (pure, fail-closed).

The mechanical substrate of the context-autonomy DESIGN (FROZEN 2026-07-04): every number,
comparator, and fail-closed guard that the prose legs (P1 adapter, P2 policy) will consume.
Nothing here changes any run's behavior by itself — these functions are dormant until P1/P2
wire them. This module is the DESIGN §7 "new runtime pieces" home for the gauge math (the
DESIGN names no module for it; mirrors the M4-P0 choice of :mod:`kata_telemetry`).

Fail-closed posture (D136): all decision-code parsing RAISES :class:`GaugeError` on
absent/unparseable/malformed input — never a permissive default ("assume fine"). The
graceful-degradation legs (stale gauge ⇒ deterministic fallback) are EXPLICIT return values
from successful parses (the ``stale`` flag, ``source: "none"``), never silent exception
swallowing. The one caller that catches :class:`GaugeError` — :func:`resolve_gauge` — does so
to walk the CA-L1 reader priority explicitly (fall to the next leg), which is itself the
fail-closed action: an absent/corrupt gauge yields ``source: "none"`` ⇒ deterministic
rotation (protective), never "assume infinite context".

Exec-safety (``protocol/exec-safety.md``): stdlib-only; spawns NO subprocess (a structural
test pins the absent ``subprocess`` import). Closest analog: :mod:`kata_risk` (pure decision
module, no subprocess, no git).
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Locked constants ([TUNABLE] value, locked structure — DESIGN §9 tunables table)
# ---------------------------------------------------------------------------

#: Bridge staleness bound, seconds (CA-L3). Older than this ⇒ stale ⇒ fallback leg.
STALENESS_S = 300

#: Conductor trigger fraction default (CA-L7): 0.70 of the effective window.
DEFAULT_TRIGGER_FRACTION = 0.70

#: Deterministic N-wave fallback burn estimate (CA-L4): 40k tokens per wave.
EST_WAVE_BURN_DEFAULT = 40_000

#: Backstop key floor (CA-L16): host-fixed `autoCompactWindow` minimum (G1: int().min(1e5)).
BACKSTOP_KEY_FLOOR = 100_000

#: Backstop gap fallback fraction (CA-L16 [TUNABLE fallback]): 0.10 × effective window.
BACKSTOP_GAP_WINDOW_FRACTION = 0.10

#: Worker work quantum (CA-L9): 40pp of the worker window above startup load.
WORK_QUANTUM = 0.40

#: Worker hard cap (CA-L9 guard i): 0.80 of the worker window. Cap WINS over the quantum.
HARD_CAP = 0.80

#: Over-briefing WARN threshold (CA-L9 guard ii): startup load > 0.30 ⇒ WARN.
OVER_BRIEF_WARN = 0.30

#: Over-briefing MANDATE threshold (CA-L9 / R-26): startup load > 0.40 ⇒ over-briefed
#: (a plan/freeze mandate, not a WARN — the quantum is unsatisfiable under the cap).
OVER_BRIEF_MANDATE = 0.40

#: The 4-field user bridge required keys (GROUNDING G3). ``total_tokens`` is the kata
#: superset addition (CA-L2) — its ABSENCE degrades the gauge to percentage-only mode.
_REQUIRED_BRIDGE_KEYS = ("session_id", "remaining_percentage", "used_pct", "timestamp")

#: The bridge fields that must be real numbers when present.
_NUMERIC_BRIDGE_KEYS = ("remaining_percentage", "used_pct", "timestamp")

#: The exactly-valid ``contextAutonomy`` config strings (CA-L32; §2 schema row).
_VALID_CONTEXT_AUTONOMY = frozenset({"on", "off"})


class GaugeError(Exception):
    """Fail-closed gauge/threshold error (D136).

    Raised by every guard on absent/unparseable/malformed input: a missing or corrupt
    bridge file, a missing/non-numeric bridge field, an out-of-range trigger fraction or
    startup load, non-positive fallback inputs, or a malformed ``contextAutonomy`` value.
    Never a silent permissive default — the caller's documented response is to walk the
    next reader-priority leg (:func:`resolve_gauge`), STOP + escalate (the load-guard
    functions, D45/GB12), or surface the failure loudly.
    """


def _is_number(value: Any) -> bool:
    """Return True iff *value* is a real int/float (bool is rejected — it subclasses int)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---------------------------------------------------------------------------
# 1. read_bridge — parse one bridge JSON file (CA-L2, CA-L3)
# ---------------------------------------------------------------------------


def read_bridge(path: str | Path, *, now_utc: datetime) -> dict:
    """Parse one statusline bridge JSON file into a normalized gauge dict.

    Kata superset schema (CA-L2):
    ``{session_id, remaining_percentage, used_pct, timestamp, total_tokens}``. The 4-field
    user bridge (no ``total_tokens``, GROUNDING G3) parses as ``mode: "percentage-only"``;
    the superset (with ``total_tokens``) parses as ``mode: "full"``. ``timestamp`` is Unix
    epoch seconds (GROUNDING G3).

    Staleness (CA-L3): a bridge whose ``timestamp`` is older than :data:`STALENESS_S`
    seconds relative to *now_utc* is returned with ``stale: True`` (strict ``>`` — exactly
    300 s old is still fresh). The read itself never rewrites or deletes the file.

    Args:
        path: The bridge file path.
        now_utc: The reference "now" as a timezone-aware :class:`datetime.datetime`
            (its ``.timestamp()`` is compared to the bridge ``timestamp``).

    Returns:
        ``{session_id, remaining_percentage, used_pct, timestamp, total_tokens: int|None,
        mode: "full"|"percentage-only", stale: bool}``.

    Raises:
        GaugeError: Absent file (caller falls to the next priority leg explicitly);
            unparseable JSON, a missing required field, or a non-numeric numeric field
            (fail-closed — never "assume fine"); a non-datetime *now_utc*.
    """
    if not isinstance(now_utc, datetime):
        raise GaugeError(
            f"read_bridge: now_utc must be a datetime (got {type(now_utc).__name__}) — "
            "the staleness comparator needs a real clock, never a silent default."
        )

    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError, OSError) as exc:
        raise GaugeError(
            f"read_bridge: bridge file {p!s} is absent/unreadable ({exc}) — the caller "
            "falls to the next reader-priority leg (CA-L1); never 'assume fine'."
        ) from exc

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise GaugeError(
            f"read_bridge: bridge file {p!s} is not valid JSON ({exc}) — fail-closed "
            "(D136), never a permissive default."
        ) from exc

    if not isinstance(data, dict):
        raise GaugeError(
            f"read_bridge: bridge file {p!s} must be a JSON object (got "
            f"{type(data).__name__}) — fail-closed (D136)."
        )

    missing = [k for k in _REQUIRED_BRIDGE_KEYS if k not in data]
    if missing:
        raise GaugeError(
            f"read_bridge: bridge file {p!s} missing required field(s) {missing} — "
            "fail-closed (D136); a malformed gauge is never treated as usable."
        )

    for key in _NUMERIC_BRIDGE_KEYS:
        if not _is_number(data[key]):
            raise GaugeError(
                f"read_bridge: bridge field {key!r} must be numeric (got {data[key]!r}) "
                "— fail-closed (D136)."
            )

    total_tokens = data.get("total_tokens")
    if total_tokens is not None and not _is_number(total_tokens):
        raise GaugeError(
            f"read_bridge: total_tokens must be numeric when present (got "
            f"{total_tokens!r}) — fail-closed (D136)."
        )

    age_s = now_utc.timestamp() - float(data["timestamp"])
    return {
        "session_id": data["session_id"],
        "remaining_percentage": data["remaining_percentage"],
        "used_pct": data["used_pct"],
        "timestamp": data["timestamp"],
        "total_tokens": int(total_tokens) if total_tokens is not None else None,
        "mode": "full" if total_tokens is not None else "percentage-only",
        "stale": age_s > STALENESS_S,
    }


# ---------------------------------------------------------------------------
# 2. resolve_gauge — CA-L1 reader priority
# ---------------------------------------------------------------------------


def resolve_gauge(
    kata_bridge_path: str | Path | None,
    user_bridge_path: str | Path | None,
    *,
    now_utc: datetime,
) -> dict:
    """Resolve the active gauge by the CA-L1 reader priority.

    Priority (CA-L1, verbatim): (1) kata bridge → (2) user bridge (4-field, %-only
    triggering) → (3) deterministic fallback. A leg that is absent, corrupt, OR stale is
    skipped explicitly (walking the next leg is the fail-closed action — never "assume
    fine"). When no leg yields a fresh, parseable gauge the result is ``source: "none"``
    (CA-L3: "Stale or absent ⇒ never 'assume fine'"), which the caller turns into
    deterministic N-wave rotation (:func:`fallback_waves`).

    Args:
        kata_bridge_path: The kata superset bridge path (or ``None`` if that leg is absent).
        user_bridge_path: The user 4-field bridge path (or ``None``).
        now_utc: The reference "now" (timezone-aware datetime), passed to :func:`read_bridge`.

    Returns:
        On a hit: ``{source: "kata"|"user", **gauge}`` (the :func:`read_bridge` dict,
        ``stale`` always False). On no usable leg: ``{"source": "none"}``.
    """
    for source, path in (("kata", kata_bridge_path), ("user", user_bridge_path)):
        if path is None:
            continue
        try:
            gauge = read_bridge(path, now_utc=now_utc)
        except GaugeError:
            continue  # absent/corrupt ⇒ walk the next reader-priority leg (CA-L1)
        if gauge["stale"]:
            continue  # stale ⇒ never sole-anchor (CA-L3); walk the next leg
        return {"source": source, **gauge}
    return {"source": "none"}


# ---------------------------------------------------------------------------
# 3. trigger_crossed — CA-L5 / CA-L2
# ---------------------------------------------------------------------------


def trigger_crossed(gauge: dict, fraction: float = DEFAULT_TRIGGER_FRACTION) -> bool:
    """Return True iff the gauge's usage has crossed the trigger fraction.

    CA-L5/CA-L7: the trigger denominator is the HOST-REPORTED effective window — the
    gauge's ``total_tokens`` (post-cap). In ``full`` mode the threshold is
    ``fraction × total_tokens`` compared to the used tokens (``used_pct/100 ×
    total_tokens``). A ``percentage-only`` gauge (CA-L2 degrade) triggers directly on
    ``used_pct ≥ fraction × 100``. The two paths are numerically equivalent (the window
    cancels) but are kept distinct to honor the CA-L5 denominator / CA-L2 degrade prose.

    Args:
        gauge: A resolved gauge dict (from :func:`read_bridge`/:func:`resolve_gauge`) —
            must carry ``mode`` and ``used_pct``.
        fraction: The trigger fraction (default :data:`DEFAULT_TRIGGER_FRACTION` = 0.70).

    Returns:
        True iff usage ≥ the trigger threshold.

    Raises:
        GaugeError: *fraction* out of range (≤ 0 or ≥ 1); a gauge missing ``used_pct``/
            ``mode`` (e.g. a ``source: "none"`` gauge) — fail-closed on malformed input.
    """
    if not _is_number(fraction) or not (0.0 < fraction < 1.0):
        raise GaugeError(
            f"trigger_crossed: fraction must be in the open interval (0, 1) (got "
            f"{fraction!r}) — fail-closed (D136)."
        )
    if not isinstance(gauge, dict) or "used_pct" not in gauge or "mode" not in gauge:
        raise GaugeError(
            "trigger_crossed: gauge must be a resolved gauge dict with 'used_pct' and "
            f"'mode' (got {gauge!r}) — a source:'none' gauge has no usage to compare; "
            "the caller must use fallback rotation, never this trigger (fail-closed)."
        )
    used_pct = gauge["used_pct"]
    if not _is_number(used_pct):
        raise GaugeError(
            f"trigger_crossed: gauge['used_pct'] must be numeric (got {used_pct!r}) — "
            "fail-closed (D136)."
        )

    if gauge["mode"] == "full":
        effective_window = gauge["total_tokens"]
        if not _is_number(effective_window):
            raise GaugeError(
                "trigger_crossed: full-mode gauge missing numeric 'total_tokens' — "
                "fail-closed (D136)."
            )
        threshold_tokens = fraction * effective_window
        used_tokens = (used_pct / 100.0) * effective_window
        return used_tokens >= threshold_tokens

    # percentage-only degrade (CA-L2): trigger on the raw percentage.
    return used_pct >= fraction * 100.0


# ---------------------------------------------------------------------------
# 4. fallback_waves — CA-L4 deterministic N-wave fallback
# ---------------------------------------------------------------------------


def fallback_waves(
    trigger_tokens: float, est_wave_burn: float = EST_WAVE_BURN_DEFAULT
) -> int:
    """Return the deterministic rotation cadence in wave boundaries (CA-L4).

    ``N = max(1, floor(trigger_tokens ÷ est_wave_burn))`` — rotate every N wave
    boundaries when no usable gauge exists. The ``max(1, …)`` floor guarantees at least
    one rotation cadence even for a tiny trigger budget.

    Args:
        trigger_tokens: The trigger threshold in tokens (must be > 0).
        est_wave_burn: The per-wave burn estimate (default
            :data:`EST_WAVE_BURN_DEFAULT` = 40k tokens; must be > 0).

    Returns:
        The rotation cadence N ≥ 1.

    Raises:
        GaugeError: Non-numeric or non-positive input — fail-closed (D136).
    """
    if not _is_number(trigger_tokens) or trigger_tokens <= 0:
        raise GaugeError(
            f"fallback_waves: trigger_tokens must be a positive number (got "
            f"{trigger_tokens!r}) — fail-closed (D136)."
        )
    if not _is_number(est_wave_burn) or est_wave_burn <= 0:
        raise GaugeError(
            f"fallback_waves: est_wave_burn must be a positive number (got "
            f"{est_wave_burn!r}) — fail-closed (D136)."
        )
    return max(1, math.floor(trigger_tokens / est_wave_burn))


# ---------------------------------------------------------------------------
# 5. backstop_recommendation — CA-L16 host auto-compact-window recommendation
# ---------------------------------------------------------------------------


def backstop_recommendation(
    target_tokens: float,
    worst_boundary_burn: float | None,
    handoff_write_cost: float | None,
    effective_window: float,
    model_max: float,
    *,
    approximate: bool = False,
) -> dict:
    """Recommend an ``autoCompactWindow`` value (or nothing), per CA-L16.

    ``gap = max(worst_boundary_burn + handoff_write_cost, 0.10 × effective_window)``.
    When either telemetry term is ``None`` (no rows yet, CA-L40 consumers replace them
    later) the first term is unavailable and ``gap`` falls to the ``0.10 × effective_window``
    fallback constant. Then:

    - ``target+gap ≥ model_max`` ⇒ recommend NOTHING (the host default suffices).
    - ``target+gap < 100k`` (the key floor) ⇒ recommend the 100k floor + note that
      deterministic rotation covers the remainder.
    - otherwise ⇒ recommend ``clamp(target+gap, 100k, model_max)``.

    The CA-L2 estimate degrade (no host ``total_tokens`` ⇒ *effective_window* is an
    advertised-window estimate) is surfaced via *approximate*: the returned ``approximate``
    is carried through and the ``note`` always names the approximation — "Never silent".

    Args:
        target_tokens: The internal trigger target in tokens (must be > 0).
        worst_boundary_burn: Worst observed boundary burn (tokens), or ``None``.
        handoff_write_cost: Handoff write cost (tokens), or ``None``.
        effective_window: The effective context window in tokens (must be > 0).
        model_max: The model's maximum window in tokens (must be > 0).
        approximate: True when *effective_window* is an advertised-window estimate
            (CA-L2 degrade) — surfaced in the return + note.

    Returns:
        ``{recommend: int|None, note: str|None, approximate: bool}``.

    Raises:
        GaugeError: Non-positive/non-numeric ``target_tokens``/``effective_window``/
            ``model_max``, or a negative/non-numeric telemetry term when present.
    """
    for name, val in (
        ("target_tokens", target_tokens),
        ("effective_window", effective_window),
        ("model_max", model_max),
    ):
        if not _is_number(val) or val <= 0:
            raise GaugeError(
                f"backstop_recommendation: {name} must be a positive number (got "
                f"{val!r}) — fail-closed (D136)."
            )
    for name, val in (
        ("worst_boundary_burn", worst_boundary_burn),
        ("handoff_write_cost", handoff_write_cost),
    ):
        if val is not None and (not _is_number(val) or val < 0):
            raise GaugeError(
                f"backstop_recommendation: {name} must be a non-negative number or None "
                f"(got {val!r}) — fail-closed (D136)."
            )

    window_fraction_gap = BACKSTOP_GAP_WINDOW_FRACTION * effective_window
    if worst_boundary_burn is None or handoff_write_cost is None:
        gap = window_fraction_gap  # telemetry-null fallback constant (CA-L40)
    else:
        gap = max(worst_boundary_burn + handoff_write_cost, window_fraction_gap)

    target_plus_gap = target_tokens + gap

    def _approx_suffix(note: str | None) -> str | None:
        if not approximate:
            return note
        clause = (
            "approximate — effective window estimated from the advertised size "
            "(no host total_tokens; CA-L2 degrade)"
        )
        return clause if note is None else f"{note} ({clause})"

    if target_plus_gap >= model_max:
        note = "target+gap ≥ model max; host default auto-compact suffices, recommend nothing."
        return {"recommend": None, "note": _approx_suffix(note), "approximate": approximate}

    if target_plus_gap < BACKSTOP_KEY_FLOOR:
        note = (
            "target+gap below the 100k key floor; recommend the 100k floor — "
            "deterministic rotation covers the remainder."
        )
        return {
            "recommend": BACKSTOP_KEY_FLOOR,
            "note": _approx_suffix(note),
            "approximate": approximate,
        }

    recommend = min(max(target_plus_gap, BACKSTOP_KEY_FLOOR), model_max)
    return {
        "recommend": int(round(recommend)),
        "note": _approx_suffix(None),
        "approximate": approximate,
    }


# ---------------------------------------------------------------------------
# 6. dispatch_budget — CA-L9 worker rotation point + over-briefing guards
# ---------------------------------------------------------------------------


def dispatch_budget(startup_fraction: float) -> dict:
    """Return the worker rotation point + over-briefing verdicts (CA-L9).

    Rotation point = ``startup load + 40pp work quantum``, clamped by the ``0.80`` hard
    cap of the worker window. The cap WINS: when ``startup > 0.40`` the full quantum is
    unsatisfiable below the cap, so ``budget_fraction`` pins to the cap and the dispatch
    is ``over_briefed`` (a plan/freeze mandate, not a WARN). Over-briefing WARNs earlier,
    at ``startup > 0.30`` (the early smell — surface, don't block). This is the mechanical
    leg of CA-A11(a).

    Args:
        startup_fraction: The conductor-authored startup load as a fraction of the worker
            window (must be in the open interval (0, 1)).

    Returns:
        ``{budget_fraction: float, cap_fraction: 0.80, warn: bool, over_briefed: bool}``.

    Raises:
        GaugeError: *startup_fraction* out of range (≤ 0 or ≥ 1) or non-numeric —
            fail-closed (D136).
    """
    if not _is_number(startup_fraction) or not (0.0 < startup_fraction < 1.0):
        raise GaugeError(
            f"dispatch_budget: startup_fraction must be in the open interval (0, 1) (got "
            f"{startup_fraction!r}) — fail-closed (D136)."
        )
    budget_fraction = min(startup_fraction + WORK_QUANTUM, HARD_CAP)
    return {
        "budget_fraction": budget_fraction,
        "cap_fraction": HARD_CAP,
        "warn": startup_fraction > OVER_BRIEF_WARN,
        "over_briefed": startup_fraction > OVER_BRIEF_MANDATE,
    }


# ---------------------------------------------------------------------------
# 7. validate_context_autonomy — the config load-guard mechanical leg
# ---------------------------------------------------------------------------


def validate_context_autonomy(value: Any) -> str:
    """Return the validated ``contextAutonomy`` value (the config load-guard's leg).

    Mirrors :func:`kata_telemetry.validate_inline_eval` exactly (§2 schema row):
    ``None`` (absent-at-load) ⇒ ``"off"`` on the key-consulted path (BC fail-safe);
    exactly ``"on"``/``"off"`` ⇒ itself; anything else (a case-variant, a wrong type, an
    unknown string) RAISES — "Malformed ⇒ load-guard STOP + escalate (D45/GB12)", never a
    silent "off".

    NOTE: one-shot delivery shapes NEVER call this — for them rotation is UNCONDITIONAL
    and the key is not consulted (CA-L32/L33/D147). This guard governs the incremental
    key-consulted path only.

    Args:
        value: The raw ``kata.config.contextAutonomy`` value (or ``None`` when absent).

    Returns:
        ``"off"`` when *value* is ``None``; the value itself when it is exactly
        ``"on"``/``"off"``.

    Raises:
        GaugeError: On any case-variant, wrong type, or unknown string — STOP + escalate
            (D45/GB12), never a silent "off".
    """
    if value is None:
        return "off"
    if isinstance(value, str) and value in _VALID_CONTEXT_AUTONOMY:
        return value
    raise GaugeError(
        f"validate_context_autonomy: {value!r} is not a valid contextAutonomy value "
        "(on|off) — STOP + escalate, never a silent 'off' (D45/GB12)."
    )
