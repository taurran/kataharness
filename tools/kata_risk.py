"""kata_risk.py — Freeze/Float M4-P1 one-dial risk score + trigger decision (DECIDES, acts).

Where :mod:`kata_telemetry` (P0) only RECORDS signal vectors, this module (P1) turns a
vector into a decision: the capped-sum risk score (M4-L4), the strict ``score > tau``
trigger verdict, and the ``inlineEval`` override resolver. It is pure, fail-closed
DECISION code (D136 — a swallowed error here would let defective work sail past the
inline evaluator, the exact defect the score exists to catch), so absent/unparseable
input RAISES :class:`RiskError` rather than defaulting permissively.

Fail-closed vs trigger-shy (D136):
- An UNKNOWN signal key (a signal the weights cannot price), an UNKNOWN ``task_class``,
  a mode-less object config, or any malformed override RAISES :class:`RiskError` — the
  orchestrator's response is STOP + escalate / treat-as-triggered + surface.
- A MISSING (absent) signal key scores 0 — the documented trigger-shy fail-safe for a
  signal that simply was not produced (a missing estimate must never manufacture a
  trigger; D136-exempt as designed, A1-Q3/A1-Q4).

Exec-safety (``protocol/exec-safety.md``): this module spawns NO subprocess and is
stdlib-only; it may import :mod:`kata_telemetry` but adds ZERO new exec sink (a
structural test pins the absent ``subprocess`` import). All inputs are already-parsed
in-memory objects (the checkpoint record, the config value) — no git, no I/O.
"""

from __future__ import annotations

from typing import Any


class RiskError(Exception):
    """Fail-closed risk-scoring error (D136).

    Raised by every guard on unpriceable / unparseable input: an unknown signal key,
    an unknown ``task_class``, a mode-less object config, or a malformed override. The
    orchestrator's documented response is STOP + escalate / treat-as-triggered +
    surface — never a silent permissive default.
    """


# ---------------------------------------------------------------------------
# Defaults as DATA (A1-Q4; [TUNABLE] — calibrated from the ledger at >=3 runs)
# ---------------------------------------------------------------------------

# Code-class signal weights (A1-Q4). Hard signals 0.60 each cross every tau alone;
# the lone soft signal (slack) 0.30 crosses none — code triggers on hard evidence
# only (the "long leash"). [TUNABLE]
DEFAULT_WEIGHTS: dict[str, float] = {
    "verify_fail": 0.60,  # [TUNABLE] per-checkpoint verify FAIL (exit != 0)
    "lane_drift": 0.60,  # [TUNABLE] non-empty out-of-footprint set (F5)
    "missing_record": 0.60,  # [TUNABLE] mandated-but-missing checkpoint record (A1-Q2)
    "slack_ge_2x": 0.30,  # [TUNABLE] slack ratio >= 2.0x (the only code soft signal)
}

# One tau per class (A1-Q4). Only ``code`` is consumed in P1; research/debug are
# DATA'd now (the score is class-parametric via ``task_class``) and wired in P2. [TUNABLE]
DEFAULT_TAU: dict[str, float] = {
    "code": 0.50,  # [TUNABLE]
    "research": 0.45,  # [TUNABLE]
    "debug": 0.45,  # [TUNABLE]
}

# The signal FIELDS a caller may present. ``slack_ratio`` is an input field (the score
# derives the weighted ``slack_ge_2x`` term from it) — never an "unknown key" despite
# not appearing in the weights (gate v1 LOW-11). Any other key is a producer bug.
_VALID_SIGNAL_KEYS: frozenset[str] = frozenset(
    {"verify_fail", "lane_drift", "missing_record", "slack_ratio"}
)

# The slack term fires at or above this ratio (A1-Q4).
_SLACK_TRIGGER_RATIO = 2.0


def _is_number(value: Any) -> bool:
    """Return True iff *value* is a real int/float (bool is rejected — it subclasses int)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---------------------------------------------------------------------------
# 1. risk_score — the capped-sum one-dial score (M4-L4)
# ---------------------------------------------------------------------------


def risk_score(signals: dict, weights: dict) -> float:
    """Return the capped-sum risk score ``min(1.0, sum of active-signal weights)``.

    *signals* is ``{verify_fail: bool, lane_drift: bool, missing_record: bool,
    slack_ratio: float|None}``. The three hard signals contribute their weight when
    truthy; the soft ``slack_ge_2x`` term is derived INTERNALLY from ``slack_ratio >=
    2.0`` (``slack_ratio`` is an input field, never a weight key — gate v1 LOW-11;
    ``None`` / absent ⇒ 0). A MISSING signal key scores 0 (the trigger-shy fail-safe).

    Args:
        signals: The signal vector (see above). A missing key ⇒ that signal absent (0).
        weights: The per-signal weights (``DEFAULT_WEIGHTS`` or a resolved override) —
            keyed ``verify_fail``/``lane_drift``/``missing_record``/``slack_ge_2x``.

    Returns:
        The capped sum in ``[0.0, 1.0]``.

    Raises:
        RiskError: On an UNKNOWN signal key in *signals* — a signal the weights cannot
            price is a producer bug (loud, never silently ignored, D136).
    """
    unknown = set(signals) - _VALID_SIGNAL_KEYS
    if unknown:
        raise RiskError(
            f"risk_score: unknown signal key(s) {sorted(unknown)} — a signal the "
            "weights cannot price is a producer bug (never silently ignored, D136). "
            f"Valid keys: {sorted(_VALID_SIGNAL_KEYS)}."
        )

    total = 0.0
    for key in ("verify_fail", "lane_drift", "missing_record"):
        if signals.get(key):  # missing ⇒ None ⇒ falsy ⇒ absent (0)
            total += weights[key]

    slack_ratio = signals.get("slack_ratio")
    if slack_ratio is not None and slack_ratio >= _SLACK_TRIGGER_RATIO:
        total += weights["slack_ge_2x"]

    return min(1.0, total)


# ---------------------------------------------------------------------------
# 2. should_trigger — the decision function (strict score > tau ⇒ trigger)
# ---------------------------------------------------------------------------


def should_trigger(
    record_or_none: dict | None,
    lane_drift: bool,
    slack_ratio: float | None,
    *,
    task_class: str,
    weights: dict | None = None,
    tau: dict | None = None,
) -> dict:
    """Decide whether a checkpoint's evidence trips the inline-eval trigger.

    Builds the signal vector from a parsed ``Kata-Checkpoint`` *record* (or ``None`` on
    a checkpoint commit that carries no record — under mode ``on`` that IS the A1-Q2
    hard signal ``missing_record``), scores it, and returns the full vector for the
    telemetry record + the ladder DECISION line. The trigger verdict is **strict**:
    ``score > tau_class`` (M4-L4 verbatim "score > tau_class ⇒ trigger" — an exact
    ``score == tau`` does NOT trigger).

    Args:
        record_or_none: A parsed checkpoint record (``{"verify": {"exit": int, ...},
            ...}``) or ``None`` when the mandated record is absent.
        lane_drift: True iff the checkpoint's out-of-footprint set is non-empty (F5).
        slack_ratio: The scheduler-computed slack ratio, or ``None`` when absent (A1-Q3).
        task_class: The task's class (``code``/``research``/``debug``) — selects tau.
        weights: Optional weight override (defaults to ``DEFAULT_WEIGHTS``).
        tau: Optional tau override (defaults to ``DEFAULT_TAU``).

    Returns:
        ``{triggered: bool, score: float, signals: dict, tau: float}``.

    Raises:
        RiskError: On an unknown *task_class* (never a default leash), or on an unknown
            signal key via :func:`risk_score`.
    """
    active_weights = weights if weights is not None else DEFAULT_WEIGHTS
    active_tau = tau if tau is not None else DEFAULT_TAU

    if task_class not in active_tau:
        raise RiskError(
            f"should_trigger: unknown task_class {task_class!r} — no default leash "
            f"(D136). Known classes: {sorted(active_tau)}."
        )
    tau_class = active_tau[task_class]

    signals = {
        "verify_fail": record_or_none is not None
        and record_or_none["verify"]["exit"] != 0,
        "lane_drift": bool(lane_drift),
        "missing_record": record_or_none is None,
        "slack_ratio": slack_ratio,
    }

    score = risk_score(signals, active_weights)
    return {
        "triggered": score > tau_class,
        "score": score,
        "signals": signals,
        "tau": tau_class,
    }


# ---------------------------------------------------------------------------
# 3. resolve_inline_eval_params — the config override resolver (load-guard STOP material)
# ---------------------------------------------------------------------------

# The keys a valid object-form ``inlineEval`` value may carry. Anything else (notably a
# whole-config dict carrying an ``inlineEval`` key passed by mistake) is a producer bug.
_INLINE_EVAL_KEYS: frozenset[str] = frozenset({"mode", "tau", "weights"})


def resolve_inline_eval_params(value: Any) -> dict:
    """Resolve effective ``{weights, tau}`` from the ``inlineEval`` VALUE.

    **The argument is the ``inlineEval`` VALUE itself (string, dict, or ``None`` when the
    field is absent) — NEVER the whole ``kata.config``** (re-gate v2 MED-2: passing the
    whole config would hit the absent-block quiet path and silently ignore every
    override). A dict carrying an ``inlineEval`` key is therefore a whole-config mistake
    and RAISES via the unknown-key guard.

    - ``None`` (field absent) or a string mode ⇒ the ``DEFAULT_WEIGHTS``/``DEFAULT_TAU``
      defaults (BC: the string form gains no override surface).
    - A dict: the ``mode`` key is **REQUIRED** — a mode-less object RAISES (re-gate v2
      HIGH-1: ``validate_inline_eval(None)``'s BC "off" leg is for an ABSENT FIELD, not a
      present-but-mode-less object — the classic hand-edit error must STOP, never
      silently run ``off``). Optional ``tau: {class: float}`` / ``weights: {signal:
      float}`` sub-fields override the defaults; a present-but-malformed value
      (non-numeric, unknown class key, unknown signal key, tau outside ``(0, 1]``) RAISES.

    Args:
        value: The ``inlineEval`` value (string, dict, or ``None``).

    Returns:
        ``{"weights": {...}, "tau": {...}}`` — full dicts (defaults with overrides
        applied), safe to pass straight to :func:`should_trigger`.

    Raises:
        RiskError: On a mode-less object, an unknown top-level / class / signal key, a
            non-dict override block, a non-numeric override, or a tau outside ``(0, 1]``
            — load-guard STOP material (GB12/D45), the ``validate_inline_eval`` posture.
    """
    weights = dict(DEFAULT_WEIGHTS)
    tau = dict(DEFAULT_TAU)

    if value is None or isinstance(value, str):
        return {"weights": weights, "tau": tau}

    if not isinstance(value, dict):
        raise RiskError(
            f"resolve_inline_eval_params: inlineEval value must be a string, dict, or "
            f"None (got {type(value).__name__}) — STOP + escalate (GB12/D45)."
        )

    if "mode" not in value:
        raise RiskError(
            "resolve_inline_eval_params: object-form inlineEval requires a 'mode' key — "
            "a mode-less object must STOP, never silently run 'off' (re-gate v2 HIGH-1)."
        )

    unknown = set(value) - _INLINE_EVAL_KEYS
    if unknown:
        raise RiskError(
            f"resolve_inline_eval_params: unknown inlineEval key(s) {sorted(unknown)} — "
            f"a valid value object carries only {sorted(_INLINE_EVAL_KEYS)}. Passing the "
            "whole kata.config (an 'inlineEval' key) is the classic mistake (MED-2). STOP."
        )

    weight_override = value.get("weights")
    if weight_override is not None:
        if not isinstance(weight_override, dict):
            raise RiskError(
                f"resolve_inline_eval_params: 'weights' must be an object (got "
                f"{type(weight_override).__name__}) — STOP (GB12/D45)."
            )
        for key, override in weight_override.items():
            if key not in DEFAULT_WEIGHTS:
                raise RiskError(
                    f"resolve_inline_eval_params: unknown weights signal key {key!r} — "
                    f"known: {sorted(DEFAULT_WEIGHTS)}. STOP."
                )
            if not _is_number(override):
                raise RiskError(
                    f"resolve_inline_eval_params: weights[{key!r}] must be numeric (got "
                    f"{override!r}) — STOP (GB12/D45)."
                )
            weights[key] = float(override)

    tau_override = value.get("tau")
    if tau_override is not None:
        if not isinstance(tau_override, dict):
            raise RiskError(
                f"resolve_inline_eval_params: 'tau' must be an object (got "
                f"{type(tau_override).__name__}) — STOP (GB12/D45)."
            )
        for key, override in tau_override.items():
            if key not in DEFAULT_TAU:
                raise RiskError(
                    f"resolve_inline_eval_params: unknown tau class key {key!r} — "
                    f"known: {sorted(DEFAULT_TAU)}. STOP."
                )
            if not _is_number(override):
                raise RiskError(
                    f"resolve_inline_eval_params: tau[{key!r}] must be numeric (got "
                    f"{override!r}) — STOP (GB12/D45)."
                )
            if not (0.0 < override <= 1.0):
                raise RiskError(
                    f"resolve_inline_eval_params: tau[{key!r}] = {override!r} is outside "
                    "(0, 1] — STOP (GB12/D45)."
                )
            tau[key] = float(override)

    return {"weights": weights, "tau": tau}
