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

# Per-class signal-weight registry (M4-P2 / A1-Q4). EVERY class table carries the
# UNIVERSAL base hard trio (gate v1 HIGH-1: a missing checkpoint record or lane drift is
# never GREEN in ANY class — the unscoped hard signals of A1-Q2/A1-Q4) plus slack, plus
# that class's DATA'd extras. Hard signals 0.60 each cross every tau alone; the lone soft
# signals never cross alone (they need a partner). [TUNABLE — calibrated from the ledger
# at >=3 runs].
#
# Producer honesty (gate v1 HIGH-2/HIGH-3/MED-7): the class EXTRAS (coverage_gap,
# scope_drift, hypothesis_cycles_3plus, repro_regression, same_hypothesis_reentry) are
# ABSENT-by-default in v1 — the weights are DATA'd but NO producer emits them yet. The
# durable per-hypothesis diagnose record and the brief-pinned scope/coverage comparators
# are NAMED DEFERRALS (each arrives via its own gated amendment, never a silent claim).
# What ships live NOW: per-class tau leashes + the base trio + slack on every class, and
# the class-signal plumbing awaiting producers.
DEFAULT_WEIGHTS_BY_CLASS: dict[str, dict[str, float]] = {
    "code": {
        "verify_fail": 0.60,  # [TUNABLE] per-checkpoint verify FAIL (exit != 0)
        "lane_drift": 0.60,  # [TUNABLE] non-empty out-of-footprint set (F5)
        "missing_record": 0.60,  # [TUNABLE] mandated-but-missing checkpoint record (A1-Q2)
        "slack_ge_2x": 0.30,  # [TUNABLE] slack ratio >= 2.0x (the only code soft signal)
    },
    "research": {
        # base hard trio (gate v1 HIGH-1). The research-class per-checkpoint VERIFY IS the
        # citation-integrity check (gate v1 HIGH-3) — its exit rides verify.exit, so there
        # is NO separate citation_fail key; verify_fail carries it.
        "verify_fail": 0.60,  # [TUNABLE]
        "lane_drift": 0.60,  # [TUNABLE]
        "missing_record": 0.60,  # [TUNABLE]
        "coverage_gap": 0.25,  # [TUNABLE] ABSENT-by-default (named deferral — no comparator yet)
        "scope_drift": 0.25,  # [TUNABLE] ABSENT-by-default (named deferral — no comparator yet)
        "slack_ge_2x": 0.30,  # [TUNABLE]
    },
    "debug": {
        # base hard trio (gate v1 HIGH-1).
        "verify_fail": 0.60,  # [TUNABLE]
        "lane_drift": 0.60,  # [TUNABLE]
        "missing_record": 0.60,  # [TUNABLE]
        "hypothesis_cycles_3plus": 0.60,  # [TUNABLE] ABSENT-by-default (named deferral — no durable record yet)
        "repro_regression": 0.60,  # [TUNABLE] ABSENT-by-default (named deferral)
        "same_hypothesis_reentry": 0.30,  # [TUNABLE] ABSENT-by-default (named deferral)
        "slack_ge_2x": 0.30,  # [TUNABLE]
    },
}

# BC alias for the P1 code table — BY REFERENCE, the SAME object, never a copy (re-gate v2
# F2: a copy silently diverges under [TUNABLE] calibration edits). Pinned by an is-identity
# test. Every P1 caller of DEFAULT_WEIGHTS keeps working unmodified (additive BC).
DEFAULT_WEIGHTS: dict[str, float] = DEFAULT_WEIGHTS_BY_CLASS["code"]

# The UNION of every class's weight vocabulary — the key-set resolve_inline_eval_params
# validates weight overrides against (gate v1 MED-5). A union-valid key is DELIBERATELY
# INERT for any class whose table lacks it (documented in both docstrings + D144, never a
# bug): the overlay in should_trigger filters the override map to the target class's vocab.
_ALL_WEIGHT_KEYS: frozenset[str] = frozenset().union(
    *(table.keys() for table in DEFAULT_WEIGHTS_BY_CLASS.values())
)

# One tau per class (A1-Q4). Only ``code`` is consumed in P1; research/debug are
# DATA'd now (the score is class-parametric via ``task_class``) and wired in P2. [TUNABLE]
DEFAULT_TAU: dict[str, float] = {
    "code": 0.50,  # [TUNABLE]
    "research": 0.45,  # [TUNABLE]
    "debug": 0.45,  # [TUNABLE]
}

# The DERIVED signal FIELDS a caller may present in a scored vector. ``slack_ratio`` is an
# input field (the score derives the weighted ``slack_ge_2x`` term from it) — never an
# "unknown key" despite not appearing in the weights (gate v1 LOW-11). The class-extra
# fields (coverage_gap/scope_drift for research; hypothesis_cycles_3plus/repro_regression/
# same_hypothesis_reentry for debug) are the DERIVED names should_trigger writes into the
# vector; risk_score prices only those a class table carries. Any other key is a producer
# bug (loud, D136).
_VALID_SIGNAL_KEYS: frozenset[str] = frozenset(
    {
        "verify_fail",
        "lane_drift",
        "missing_record",
        "slack_ratio",
        "coverage_gap",
        "scope_drift",
        "hypothesis_cycles_3plus",
        "repro_regression",
        "same_hypothesis_reentry",
    }
)

# The RAW class-signal INPUT keys a producer may pass via ``should_trigger(class_signals=)``,
# per class (M4-P2). These are the producer-facing inputs — the debug ``hypothesis_cycles``
# int is derived internally to the ``hypothesis_cycles_3plus`` boolean (LOW-11 pattern).
# ``code`` carries NO class extras. A key from another class RAISES (cross-class
# contamination — a producer bug, loud); a key from no class RAISES (unknown producer bug).
_CLASS_SIGNAL_INPUT_VOCAB: dict[str, frozenset[str]] = {
    "code": frozenset(),
    "research": frozenset({"coverage_gap", "scope_drift"}),
    "debug": frozenset(
        {"hypothesis_cycles", "repro_regression", "same_hypothesis_reentry"}
    ),
}

# The union of every class's raw input vocabulary — used to tell a WRONG-CLASS key
# (cross-class contamination) apart from a genuinely UNKNOWN key.
_ALL_CLASS_SIGNAL_INPUTS: frozenset[str] = frozenset().union(
    *_CLASS_SIGNAL_INPUT_VOCAB.values()
)

# The slack term fires at or above this ratio (A1-Q4).
_SLACK_TRIGGER_RATIO = 2.0

# The debug ``hypothesis_cycles_3plus`` signal fires when the cycle count reaches this
# floor (A1-Q4; LOW-11 internal derivation). The ``>= 3`` boundary is mutation-pinned.
_HYPOTHESIS_CYCLES_FLOOR = 3


def _is_number(value: Any) -> bool:
    """Return True iff *value* is a real int/float (bool is rejected — it subclasses int)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---------------------------------------------------------------------------
# 1. risk_score — the capped-sum one-dial score (M4-L4)
# ---------------------------------------------------------------------------


def risk_score(signals: dict, weights: dict) -> float:
    """Return the capped-sum risk score ``min(1.0, sum of active-signal weights)``.

    *signals* is the DERIVED signal vector — the base ``{verify_fail: bool, lane_drift:
    bool, missing_record: bool, slack_ratio: float|None}`` plus any class-extra boolean
    fields the class carries (research: ``coverage_gap``/``scope_drift``; debug:
    ``hypothesis_cycles_3plus``/``repro_regression``/``same_hypothesis_reentry``). Each
    boolean signal contributes its weight when truthy; the soft ``slack_ge_2x`` term is
    derived INTERNALLY from ``slack_ratio >= 2.0`` (``slack_ratio`` is an input field,
    never a weight key — gate v1 LOW-11; ``None`` / absent ⇒ 0). A MISSING signal key
    scores 0 (the trigger-shy fail-safe).

    Pricing is driven by *weights* — only the keys the given class table carries are
    priced, so an override map carrying a signal for a DIFFERENT class is inert here (the
    overlay in :func:`should_trigger` filters it out before this call).

    Args:
        signals: The signal vector (see above). A missing key ⇒ that signal absent (0).
        weights: The per-signal weights for the target class (``DEFAULT_WEIGHTS_BY_CLASS``
            entry or a resolved overlay). Each key except ``slack_ge_2x`` names a boolean
            signal field; ``slack_ge_2x`` is derived from the ``slack_ratio`` input.

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
    for key, weight in weights.items():
        if key == "slack_ge_2x":
            slack_ratio = signals.get("slack_ratio")
            if slack_ratio is not None and slack_ratio >= _SLACK_TRIGGER_RATIO:
                total += weight
        elif signals.get(key):  # missing ⇒ None ⇒ falsy ⇒ absent (0)
            total += weight

    return min(1.0, total)


# ---------------------------------------------------------------------------
# 2. should_trigger — the decision function (strict score > tau ⇒ trigger)
# ---------------------------------------------------------------------------


def _derive_class_extras(task_class: str, class_signals: dict) -> dict:
    """Validate *class_signals* against *task_class* and derive its extra boolean signals.

    ``code`` carries no extras (an empty dict). For research/debug, EVERY class-extra
    boolean is written (ABSENT-by-default ⇒ ``False`` ⇒ 0, the trigger-shy fail-safe) so
    the telemetry vector is uniform. The debug ``hypothesis_cycles`` int is derived to the
    ``hypothesis_cycles_3plus`` boolean at ``>= _HYPOTHESIS_CYCLES_FLOOR`` (LOW-11).

    Raises:
        RiskError: On a class-signal key from ANOTHER class (cross-class contamination —
            a producer bug, loud) or from NO class (unknown producer bug). Both are D136
            STOP material, never silently dropped.
    """
    own_vocab = _CLASS_SIGNAL_INPUT_VOCAB[task_class]
    for key in class_signals:
        if key in own_vocab:
            continue
        if key in _ALL_CLASS_SIGNAL_INPUTS:
            owner = next(
                cls
                for cls, vocab in _CLASS_SIGNAL_INPUT_VOCAB.items()
                if key in vocab
            )
            raise RiskError(
                f"should_trigger: class-signal key {key!r} belongs to class {owner!r}, "
                f"not {task_class!r} — cross-class contamination is a producer bug "
                "(loud, never silently dropped, D136)."
            )
        raise RiskError(
            f"should_trigger: unknown class-signal key {key!r} for class {task_class!r} "
            f"— known {task_class!r} signals: {sorted(own_vocab)}. Producer bug (D136)."
        )

    if task_class == "research":
        return {
            "coverage_gap": bool(class_signals.get("coverage_gap")),
            "scope_drift": bool(class_signals.get("scope_drift")),
        }
    if task_class == "debug":
        cycles = class_signals.get("hypothesis_cycles")
        return {
            "hypothesis_cycles_3plus": cycles is not None
            and cycles >= _HYPOTHESIS_CYCLES_FLOOR,
            "repro_regression": bool(class_signals.get("repro_regression")),
            "same_hypothesis_reentry": bool(class_signals.get("same_hypothesis_reentry")),
        }
    return {}


def should_trigger(
    record_or_none: dict | None,
    lane_drift: bool,
    slack_ratio: float | None,
    *,
    task_class: str,
    weights: dict | None = None,
    tau: dict | None = None,
    class_signals: dict | None = None,
) -> dict:
    """Decide whether a checkpoint's evidence trips the inline-eval trigger.

    Builds the signal vector from a parsed ``Kata-Checkpoint`` *record* (or ``None`` on
    a checkpoint commit that carries no record — under mode ``on`` that IS the A1-Q2
    hard signal ``missing_record``) plus any per-class extras, scores it against the
    class weight table, and returns the full vector for the telemetry record + the ladder
    DECISION line. The trigger verdict is **strict**: ``score > tau_class`` (M4-L4
    verbatim "score > tau_class ⇒ trigger" — an exact ``score == tau`` does NOT trigger).

    **By-class plumbing (gate v1 MED-5; re-gate v2 F1/F3):** the passed *weights* is an
    OVERRIDE MAP overlaid on ``DEFAULT_WEIGHTS_BY_CLASS[task_class]`` **filtered to that
    class's vocabulary** — NOT a replacement table. The P1 boundary tests pass unchanged
    because they supply full code-vocabulary maps and overlay-of-a-full-map ≡ replacement.
    A union-valid override key for a signal this class's table lacks is DELIBERATELY INERT
    (never a bug — documented here + in :func:`resolve_inline_eval_params` + D144).

    Args:
        record_or_none: A parsed checkpoint record (``{"verify": {"exit": int, ...},
            ...}``) or ``None`` when the mandated record is absent.
        lane_drift: True iff the checkpoint's out-of-footprint set is non-empty (F5).
        slack_ratio: The scheduler-computed slack ratio, or ``None`` when absent (A1-Q3).
        task_class: The task's class (``code``/``research``/``debug``) — selects the tau
            leash AND the weight table.
        weights: Optional OVERRIDE MAP overlaid on the class table (see above). ``None`` ⇒
            the class's default table.
        tau: Optional tau override (defaults to ``DEFAULT_TAU``).
        class_signals: Optional producer inputs for the class extras — research:
            ``{coverage_gap: bool, scope_drift: bool}``; debug: ``{hypothesis_cycles:
            int, repro_regression: bool, same_hypothesis_reentry: bool}``. ``None`` /
            missing keys ⇒ absent ⇒ 0 (trigger-shy). A wrong-class or unknown key RAISES.

    Returns:
        ``{triggered: bool, score: float, signals: dict, tau: float}``.

    Raises:
        RiskError: On an unknown *task_class* (never a default leash), a wrong-class /
            unknown *class_signals* key, or an unknown signal key via :func:`risk_score`.
    """
    active_tau = tau if tau is not None else DEFAULT_TAU

    if task_class not in active_tau:
        raise RiskError(
            f"should_trigger: unknown task_class {task_class!r} — no default leash "
            f"(D136). Known classes: {sorted(active_tau)}."
        )
    if task_class not in DEFAULT_WEIGHTS_BY_CLASS:
        raise RiskError(
            f"should_trigger: no weight table for task_class {task_class!r} — no default "
            f"leash (D136). Known classes: {sorted(DEFAULT_WEIGHTS_BY_CLASS)}."
        )
    tau_class = active_tau[task_class]

    # Overlay: start from the class table, apply override values for keys the class
    # carries, ignore (filter out) override keys the class lacks — deliberately inert.
    base_weights = DEFAULT_WEIGHTS_BY_CLASS[task_class]
    if weights is None:
        active_weights = base_weights
    else:
        active_weights = {
            key: (weights[key] if key in weights else default)
            for key, default in base_weights.items()
        }

    extras = _derive_class_extras(task_class, class_signals or {})

    signals = {
        "verify_fail": record_or_none is not None
        and record_or_none["verify"]["exit"] != 0,
        "lane_drift": bool(lane_drift),
        "missing_record": record_or_none is None,
        "slack_ratio": slack_ratio,
        **extras,
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

    **Weight-override keys are validated against the UNION of all class vocabularies**
    (gate v1 MED-5), so a research/debug extra (e.g. ``coverage_gap``) is accepted here.
    The return keeps its P1-flat shape (a single weights map). A union-valid key that a
    given class's table lacks is **DELIBERATELY INERT** for that class — :func:`should_trigger`
    overlays this map onto the target class table filtered to that class's vocabulary, so
    a ``coverage_gap`` override changes a research trigger but is silently inert for code
    (documented + D144, never read as a bug). Only a key in NO class vocabulary RAISES.

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
            if key not in _ALL_WEIGHT_KEYS:
                raise RiskError(
                    f"resolve_inline_eval_params: unknown weights signal key {key!r} — "
                    f"known (union of all class vocabularies): {sorted(_ALL_WEIGHT_KEYS)}. "
                    "STOP."
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
