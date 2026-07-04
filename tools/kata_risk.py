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
