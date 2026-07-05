"""kata_adaptive.py — Adaptive-tiering L1 state machine (D150: AT-L1..AT-L17b, DECIDES).

Where :mod:`kata_models` owns the L0 differential table (D131/D59 — the deterministic
base and ONLY fallback) and the rung arithmetic, this module owns the ADAPTIVE layer's
per-run state and decisions: the fail-bump counter (AT-L8), the first-pass streak +
re-earn damper (AT-L11), the plan-complexity downshift signal (AT-L10a), the pinned
per-dispatch modulation delta (AT-L1, capped at −1, bump overrides class), the premium
budget's FCFS-with-reservation spend discipline (AT-L12/AT-L13), the loud ``tier:``
DECISION trail + its durable recount (AT-L7 — the counter that survives conductor
compaction), and the mid-run anchor-switch reset (AT-L17b).

It is pure, fail-closed DECISION code (D136 / AT-L21 — a swallowed error here would
silently route work to the wrong rung or under-count premium spend, the exact defects
the adaptive layer exists to prevent), so absent/unparseable input RAISES
:class:`AdaptiveError` rather than defaulting permissively. The ONE documented
permissive leg is BY DESIGN: an absent ``models.adaptive`` block resolves to
``{"enabled": False}`` — every adaptive leg OFF, byte-for-byte v0.2.1 behavior
(§3 BC matrix, load-time BC; block PRESENCE is consent).

Boundary of responsibility (stated, AT-L2/AT-L2b): :func:`modulate_step` returns ONLY
the L1 delta in ``{-1, 0, +1}``. Rung arithmetic — applying the delta to the L0 row,
clamping to the floor (AT-L3) / ceiling (AT-L2), and the anchor-landing OMIT emission
(AT-L2b) — is the CALLER's job (kata_models / kata-orchestrate), never this module's.
Likewise the AT-L9 evaluator ladder is M4-side (Amendment #6); this module carries the
``evaluatorEscalate`` config key as data but never consumes it.

Exec-safety (``protocol/exec-safety.md``): this module spawns NO subprocess, does NO
I/O, and is stdlib-only — a pure in-memory state machine over already-parsed objects
(the ``models.adaptive`` config value, the object-form premium scope, the run state
dict). A structural test pins the absent subprocess import.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "ADAPTIVE_DEFAULTS",
    "RESERVE",
    "RESERVED_EVENTS",
    "AdaptiveError",
    "anchor_switch_reset",
    "bump_pending",
    "can_spend",
    "modulate_step",
    "new_state",
    "record_gate_result",
    "record_spend",
    "record_standing_reroll",
    "recount_from_decisions",
    "render_tier_decision",
    "resolve_adaptive_config",
    "resolve_budget",
]


class AdaptiveError(Exception):
    """Fail-closed adaptive-tiering error (D136 / AT-L21).

    Raised by every guard on malformed input: a wrong-typed ``models.adaptive`` block,
    an unknown config key, a non-bool/non-int/sub-1 tunable, a malformed budget object,
    an unknown ``complexity`` or ``work_class`` value, an unknown DECISION reason, or a
    corrupt ``tier:`` recount payload. The orchestrator's documented response is
    load-guard STOP + escalate (GB12/D45) — never a silent fall-through to unlimited
    premium OR to no-premium (AT-L21 verbatim).
    """


# ---------------------------------------------------------------------------
# Defaults as DATA (§3 schema / §7 tunables; [TUNABLE] — all VETO-FLAGs resolved
# by the operator 2026-07-05 to these draft values)
# ---------------------------------------------------------------------------

# The per-key defaults a PRESENT ``models.adaptive`` block takes for any absent key
# (freeze-gate v1 HIGH-6 pinned per-key semantics). ``evaluatorEscalate`` is carried
# for the M4-side AT-L9 leg (never consumed here); ``l2`` is the AT-L18 activation
# gate, default OFF (AT-L19 named-deferred).
ADAPTIVE_DEFAULTS: dict[str, Any] = {
    "failBumpAt": 2,  # [TUNABLE] F — fail-count bump threshold (AT-L8, VETO-FLAG-2)
    "streakDownAt": 3,  # [TUNABLE] K — first-pass streak downshift (AT-L11, VETO-FLAG-2)
    "planComplexityDownshift": True,  # [TUNABLE] AT-L10a plan-time leg toggle
    "evaluatorEscalate": True,  # [TUNABLE] AT-L9 (M4 Amendment #6 side — data only here)
    "l2": False,  # AT-L18 activation gate — default ABSENT ⇒ OFF (AT-L19)
}

_BOOL_KEYS: frozenset[str] = frozenset({"planComplexityDownshift", "evaluatorEscalate", "l2"})
_INT_KEYS: frozenset[str] = frozenset({"failBumpAt", "streakDownAt"})

# AT-L4 / re-gate LOW-5: the machine-checkable work-class enum (the SKILL_WORK_CLASS
# value vocabulary in kata_models). Downshift applies ONLY to "coding"; "critical" is
# roster-protected and "economy" already sits at its mode's floor.
_WORK_CLASSES: frozenset[str] = frozenset({"critical", "coding", "economy"})

# AT-L10a: the plan-frontmatter complexity vocabulary. None ⇒ the key was absent
# (BC — L0 exactly); anything else present-but-malformed RAISES (the A1-Q3
# ``estimate:`` precedent — a plan-freeze validation failure).
_COMPLEXITY_VALUES: frozenset[str] = frozenset({"low", "standard", "high"})

# AT-L13: the last RESERVE budget calls are reserved for these two events; a
# non-reserved event arriving with only reserved budget left dispatches at the
# anchor (no premium), LOUD.
RESERVED_EVENTS: tuple[str, str] = ("freeze-gate-verdict", "re-gate-after-hold")
RESERVE: int = 2  # [TUNABLE] budget reservation (AT-L13)

_DEFAULT_BUDGET_CALLS: int = 10  # [TUNABLE] N — default premium calls/run (AT-L12, VETO-FLAG-1)
_BUDGET_KEYS: frozenset[str] = frozenset({"calls", "tokensOut"})

# AT-L7: the non-event DECISION reasons. An event reason is "event:<name>".
_STATIC_REASONS: frozenset[str] = frozenset(
    {"failbump", "streak", "complexity", "anchor-switch-reset", "budget-exhausted"}
)

_STATE_KEYS: frozenset[str] = frozenset(
    {"bumpCounters", "bumped", "streaks", "dampers", "budgetSpent"}
)


def _strict_int(value: Any) -> bool:
    """Return True iff *value* is a real int (bool is rejected — it subclasses int)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _require_state(state: Any) -> None:
    """Raise :class:`AdaptiveError` unless *state* has the :func:`new_state` shape."""
    if not isinstance(state, dict) or not _STATE_KEYS <= set(state):
        raise AdaptiveError(
            f"adaptive state must be a dict with keys {sorted(_STATE_KEYS)} "
            "(use new_state()) — a malformed state is a caller bug (D136). STOP."
        )


def _require_cfg(cfg: Any) -> None:
    """Raise :class:`AdaptiveError` unless *cfg* came from :func:`resolve_adaptive_config`."""
    if not isinstance(cfg, dict) or "enabled" not in cfg:
        raise AdaptiveError(
            "adaptive cfg must be the resolve_adaptive_config() result (a dict with "
            "'enabled') — passing the raw config value here is the classic mistake. STOP."
        )


# ---------------------------------------------------------------------------
# 1. Config resolver (§3 schema; AT-L21 fail-closed loading)
# ---------------------------------------------------------------------------


def resolve_adaptive_config(value: Any) -> dict:
    """Resolve the effective adaptive config from the ``models.adaptive`` VALUE.

    **The argument is the ``models.adaptive`` VALUE itself (dict or ``None`` when the
    block is absent) — NEVER the whole ``kata.config``** (the
    :func:`kata_risk.resolve_inline_eval_params` re-gate v2 MED-2 precedent: passing
    the whole config would hit the absent-block quiet path and silently disable every
    leg). Block PRESENCE is consent (§3 BC matrix): an absent block ⇒ every adaptive
    leg OFF, byte-for-byte v0.2.1 (load-time BC); a present block — even ``{}`` —
    enables the layer with the pinned per-key defaults (freeze-gate v1 HIGH-6).

    Args:
        value: The ``models.adaptive`` value (dict, or ``None`` when absent).

    Returns:
        ``{"enabled": False}`` when *value* is ``None``; otherwise
        ``{"enabled": True, **ADAPTIVE_DEFAULTS}`` with the block's overrides applied.

    Raises:
        AdaptiveError: On a non-dict non-None value, an unknown key, a non-bool value
            for a bool field, or a non-int / sub-1 value for ``failBumpAt`` /
            ``streakDownAt`` (bool rejected) — load-guard STOP material (GB12/D45,
            AT-L21), never a permissive default.
    """
    if value is None:
        return {"enabled": False}

    if not isinstance(value, dict):
        raise AdaptiveError(
            f"resolve_adaptive_config: models.adaptive must be an object or absent "
            f"(got {type(value).__name__}) — STOP + escalate (GB12/D45, AT-L21)."
        )

    unknown = set(value) - _BOOL_KEYS - _INT_KEYS
    if unknown:
        raise AdaptiveError(
            f"resolve_adaptive_config: unknown adaptive key(s) {sorted(unknown)} — "
            f"known keys: {sorted(ADAPTIVE_DEFAULTS)}. STOP (AT-L21)."
        )

    resolved: dict[str, Any] = {"enabled": True, **ADAPTIVE_DEFAULTS}
    for key, override in value.items():
        if key in _BOOL_KEYS and not isinstance(override, bool):
            raise AdaptiveError(
                f"resolve_adaptive_config: adaptive[{key!r}] must be a bool (got "
                f"{override!r}) — STOP (AT-L21)."
            )
        if key in _INT_KEYS and (not _strict_int(override) or override < 1):
            raise AdaptiveError(
                f"resolve_adaptive_config: adaptive[{key!r}] must be an int >= 1 (got "
                f"{override!r}) — a sub-1 threshold would fire on every dispatch. "
                "STOP (AT-L21)."
            )
        resolved[key] = override
    return resolved


# ---------------------------------------------------------------------------
# 2. Run state + signal recording (AT-L8 / AT-L11 bookkeeping)
# ---------------------------------------------------------------------------


def new_state() -> dict:
    """Return a fresh per-run adaptive state (all counters empty, zero spend).

    Shape: ``{"bumpCounters": {task_id: int}, "bumped": {task_id: True},
    "streaks": {task_class: int}, "dampers": {task_class: int},
    "budgetSpent": int}``. State is PER-RUN — cross-run memory is L2's job,
    never L1's (§5 named deferral).

    Returns:
        The empty state dict (fresh mutable sub-dicts every call).
    """
    return {"bumpCounters": {}, "bumped": {}, "streaks": {}, "dampers": {}, "budgetSpent": 0}


def record_gate_result(
    state: dict,
    task_id: str,
    task_class: str,
    *,
    accepted: bool,
    first_pass: bool,
    downshifted: bool,
) -> None:
    """Record one task-gate verdict into the adaptive state (mutates *state*).

    - ``accepted and first_pass`` ⇒ the class streak increments (AT-L11: only
      FIRST-PASS acceptances are streak members).
    - ``accepted and not first_pass`` ⇒ the class streak resets to 0 (a fix-cycled
      acceptance is not a first-pass streak member — it neither builds nor sustains
      the earned streak).
    - ``not accepted`` (a gate REJECTION) ⇒ the class streak resets to 0 (AT-L11
      asymmetric hysteresis — fast up, slow down), the task's bump counter
      increments (AT-L8), and — if the rejected dispatch was DOWNSHIFTED — the
      class damper DOUBLES (AT-L11: a class that proves it can't pass a rung down
      stops oscillating; K effectively becomes ``streakDownAt * damper``).

    Args:
        state: The :func:`new_state` dict (mutated in place).
        task_id: The rejected/accepted task's id (per-task bump scope, AT-L8).
        task_class: The task's class (per-class streak/damper scope, AT-L11).
        accepted: True iff the gate ACCEPTED the task.
        first_pass: True iff acceptance came with no fix cycle (ignored when
            ``accepted`` is False).
        downshifted: True iff the judged dispatch ran on an adaptively DOWNSHIFTED
            rung (drives the damper; ignored when ``accepted`` is True).

    Raises:
        AdaptiveError: On a malformed *state* (not the :func:`new_state` shape).
    """
    _require_state(state)
    if accepted and first_pass:
        state["streaks"][task_class] = state["streaks"].get(task_class, 0) + 1
        return
    state["streaks"][task_class] = 0
    if not accepted:
        state["bumpCounters"][task_id] = state["bumpCounters"].get(task_id, 0) + 1
        if downshifted:
            state["dampers"][task_class] = state["dampers"].get(task_class, 1) * 2


def record_standing_reroll(state: dict, task_id: str, task_class: str) -> None:
    """Record one STANDING ladder ``reroll`` verdict (mutates *state*).

    A standing reroll counts exactly like a gate rejection for adaptation (AT-L8:
    bump counter = gate rejections + STANDING rerolls; AT-L11: it clears the class
    streak). **STANDING verdicts only** — the CALLER guarantees this is invoked
    post-re-adjudication (AT-L9 / freeze-gate v1 MED-9: an OVERTURNED verdict never
    counts; this module cannot see the evaluator ladder, so the caller owns that
    filter).

    Args:
        state: The :func:`new_state` dict (mutated in place).
        task_id: The rerolled task's id.
        task_class: The task's class.

    Raises:
        AdaptiveError: On a malformed *state*.
    """
    _require_state(state)
    state["bumpCounters"][task_id] = state["bumpCounters"].get(task_id, 0) + 1
    state["streaks"][task_class] = 0


# ---------------------------------------------------------------------------
# 3. bump_pending + modulate_step (AT-L8; AT-L1 pinned order; AT-L4 coding-only)
# ---------------------------------------------------------------------------


def bump_pending(state: dict, cfg: dict, task_id: str) -> bool:
    """Return True iff *task_id* has EARNED but NOT YET CONSUMED its fail bump.

    True iff the layer is enabled AND the task's bump counter has reached
    ``cfg["failBumpAt"]`` (F, strict ``>=`` boundary) AND the task has not already
    been bumped — **F fires ONCE per task** (AT-L8 / freeze-gate v1 LOW-17: no 2F
    re-trigger in v1; :func:`modulate_step` marks the bump consumed, after which
    this returns False for the task forever, while the consumed bump itself
    persists via ``state["bumped"]``).

    Args:
        state: The :func:`new_state` dict (read-only here).
        cfg: The :func:`resolve_adaptive_config` result.
        task_id: The task about to be dispatched.

    Returns:
        True iff the task's NEXT attempt should be the bumped attempt.

    Raises:
        AdaptiveError: On a malformed *state* or *cfg*.
    """
    _require_state(state)
    _require_cfg(cfg)
    if not cfg["enabled"]:
        return False
    if state["bumped"].get(task_id):
        return False
    return state["bumpCounters"].get(task_id, 0) >= cfg["failBumpAt"]


def modulate_step(
    cfg: dict,
    state: dict,
    *,
    task_id: str,
    task_class: str,
    work_class: str,
    complexity: str | None = None,
) -> int:
    """Return the L1 modulation DELTA for one dispatch, in ``{-1, 0, +1}`` (AT-L1).

    The PINNED resolution order (AT-L1, freeze-gate v1 HIGH-4):

    1. Layer disabled ⇒ ``0`` (the L0 row resolves exactly as v0.2.1 — AC-1).
    2. Bump leg: a pending OR already-consumed bump ⇒ mark ``bumped[task_id]`` and
       return ``+1``. **Per-task state OVERRIDES class state** — a bumped task is
       EXEMPT from both downshift legs for all its remaining attempts (a failed
       task can never be re-dispatched at or below the rung that already failed it).
    3. Downshift legs — ONLY for ``work_class == "coding"`` (AT-L4: judgment never
       adapts down; critical is roster-protected, economy already sits at its
       mode's floor — re-gate LOW-5): plan-frozen ``complexity == "low"`` (AT-L10a,
       gated by ``cfg["planComplexityDownshift"]``) OR an earned class streak
       ``streaks[task_class] >= streakDownAt * damper`` (AT-L11) ⇒ ``-1``.
       **CAPPED at −1 total** — the two legs never stack to −2 (re-gate MED-2;
       the deeper single downshift applies, and one rung IS the deepest single
       L1 step in either direction).
    4. Otherwise ``0``.

    Boundary of responsibility (AT-L2/AT-L2b, stated): this returns ONLY the delta.
    Applying it to the L0 rung, clamping to floor/ceiling, and the anchor-landing
    ``None``/OMIT emission are the CALLER's job (kata_models / kata-orchestrate).

    Args:
        cfg: The :func:`resolve_adaptive_config` result.
        state: The :func:`new_state` dict (mutated only to mark a consumed bump).
        task_id: The dispatched task's id.
        task_class: The task's class (streak/damper scope).
        work_class: The dispatch's work class (``critical``/``coding``/``economy``
            — the SKILL_WORK_CLASS enum term, AT-L4).
        complexity: The plan-frozen per-task complexity rating (AT-L10a):
            ``"low"``/``"standard"``/``"high"``, or ``None`` when the plan key is
            absent (BC — L0 exactly).

    Returns:
        The delta: ``+1`` (bump), ``-1`` (downshift), or ``0``.

    Raises:
        AdaptiveError: On a malformed *state*/*cfg*, an unknown *work_class* (a
            producer bug against the enum — D136), or a present-but-malformed
            *complexity* (the A1-Q3 ``estimate:`` precedent — plan-freeze
            validation failure, raised here even when the layer is disabled:
            malformed input never rides a disabled config out the door).
    """
    _require_state(state)
    _require_cfg(cfg)
    if work_class not in _WORK_CLASSES:
        raise AdaptiveError(
            f"modulate_step: unknown work_class {work_class!r} — known (the "
            f"SKILL_WORK_CLASS enum, AT-L4): {sorted(_WORK_CLASSES)}. Producer bug (D136)."
        )
    if complexity is not None and complexity not in _COMPLEXITY_VALUES:
        raise AdaptiveError(
            f"modulate_step: complexity must be one of {sorted(_COMPLEXITY_VALUES)} or "
            f"absent (got {complexity!r}) — present-but-malformed is a plan-freeze "
            "validation failure (AT-L10a, the A1-Q3 estimate: precedent). STOP."
        )

    if not cfg["enabled"]:
        return 0

    # Bump leg — per-task overrides class (AT-L1): once earned, +1 for every
    # remaining attempt; the mark makes bump_pending fire-once (AT-L8).
    if bump_pending(state, cfg, task_id) or state["bumped"].get(task_id):
        state["bumped"][task_id] = True
        return 1

    # Downshift legs — coding-class only (AT-L4), capped at −1 (re-gate MED-2).
    if work_class != "coding":
        return 0
    complexity_leg = cfg["planComplexityDownshift"] and complexity == "low"
    threshold = cfg["streakDownAt"] * state["dampers"].get(task_class, 1)
    streak_leg = state["streaks"].get(task_class, 0) >= threshold
    if complexity_leg or streak_leg:
        return -1
    return 0


# ---------------------------------------------------------------------------
# 4. Premium budget (AT-L12 resolution; AT-L13 FCFS with reservation)
# ---------------------------------------------------------------------------


def resolve_budget(scope_obj: Any) -> int:
    """Resolve the premium call budget N from the OBJECT-form premium scope.

    **The argument is the object-form ``models.premium.scope`` value**
    (``{"events": [...], "budget": {"calls": N}}``). List-form scope (v0.2.1
    semantics — unlimited, BC) never reaches this function; full scope-form
    type-dispatch and event-name validation are the load guard's job in
    kata_models (AT-L15) — this function owns ONLY the budget leg.

    - Absent ``budget`` ⇒ the default N (AT-L12: 10 calls/run).
    - ``budget.calls`` present ⇒ that value (0 is a legal deliberate no-premium
      budget).
    - A ``budget`` dict WITHOUT ``calls`` (e.g. ``tokensOut``-only) ⇒ RAISE — the
      load guard (``kata_models.classify_premium_scope``) requires ``calls`` when a
      budget object is present (the fail-closed hand-edit posture, AT-L15/AT-L21);
      this function matches it so the two layers never disagree. The AT-L12 degrade
      rule (token budgets degrade to the CALL budget where the host reports nulls)
      applies to ACCOUNTING, not to config validation.

    Args:
        scope_obj: The object-form premium scope value.

    Returns:
        The call budget N (an int >= 0).

    Raises:
        AdaptiveError: On a non-dict *scope_obj*, a non-dict ``budget``, an unknown
            budget key, or a non-int (bool included) / negative ``calls``/``tokensOut``
            — load-guard STOP material (AT-L15/AT-L21).
    """
    if not isinstance(scope_obj, dict):
        raise AdaptiveError(
            f"resolve_budget: object-form scope must be a dict (got "
            f"{type(scope_obj).__name__}) — list-form scope never budgets (AT-L15). STOP."
        )
    if "budget" not in scope_obj:
        return _DEFAULT_BUDGET_CALLS

    budget = scope_obj["budget"]
    if not isinstance(budget, dict):
        raise AdaptiveError(
            f"resolve_budget: scope.budget must be an object (got "
            f"{type(budget).__name__}) — STOP (AT-L15/AT-L21)."
        )
    unknown = set(budget) - _BUDGET_KEYS
    if unknown:
        raise AdaptiveError(
            f"resolve_budget: unknown budget key(s) {sorted(unknown)} — known: "
            f"{sorted(_BUDGET_KEYS)}. STOP (AT-L15/AT-L21)."
        )
    for key in _BUDGET_KEYS & set(budget):
        if not _strict_int(budget[key]) or budget[key] < 0:
            raise AdaptiveError(
                f"resolve_budget: budget[{key!r}] must be an int >= 0 (got "
                f"{budget[key]!r}) — STOP (AT-L15/AT-L21)."
            )
    if "calls" not in budget:
        raise AdaptiveError(
            "resolve_budget: a present budget object REQUIRES 'calls' (the load "
            "guard's fail-closed hand-edit posture — kata_models.classify_premium_scope "
            "raises on the same shape; the layers must agree). Omit 'budget' entirely "
            "for the default, or state calls explicitly. STOP (AT-L15/AT-L21)."
        )
    return budget["calls"]


def can_spend(budget_total: int, state: dict, event: str) -> bool:
    """Decide whether one premium dispatch for *event* may spend budget (AT-L13).

    FCFS with a floor reservation: the last :data:`RESERVE` calls are reserved for
    the :data:`RESERVED_EVENTS` (``freeze-gate-verdict`` / ``re-gate-after-hold``).
    A reserved event may spend down to zero (``remaining >= 1``); a non-reserved
    event needs ``remaining > RESERVE``. A denial here means the caller dispatches
    at the ANCHOR (no premium), LOUD — denying spend is the conservative direction,
    so an event name outside the registry is simply non-reserved here (registry
    membership validation is the load guard's job, AT-L5/AT-L15).

    Args:
        budget_total: The resolved call budget N (:func:`resolve_budget`).
        state: The :func:`new_state` dict (reads ``budgetSpent``).
        event: The registry event name driving this premium dispatch.

    Returns:
        True iff the dispatch may commit a premium spend.

    Raises:
        AdaptiveError: On a malformed *state* or a non-int/negative *budget_total*.
    """
    _require_state(state)
    if not _strict_int(budget_total) or budget_total < 0:
        raise AdaptiveError(
            f"can_spend: budget_total must be an int >= 0 (got {budget_total!r}) — "
            "STOP (D136)."
        )
    remaining = budget_total - state["budgetSpent"]
    if event in RESERVED_EVENTS:
        return remaining >= 1
    return remaining > RESERVE


def record_spend(state: dict) -> None:
    """Commit one premium spend (mutates *state*; counted at DISPATCH COMMIT, AT-L13).

    The conductor is the single dispatcher — one counter, no cross-process race.
    The durable recount of this counter across conductor compaction is the
    :func:`render_tier_decision` ``tier:`` trail via :func:`recount_from_decisions`.

    Args:
        state: The :func:`new_state` dict (mutated in place).

    Raises:
        AdaptiveError: On a malformed *state*.
    """
    _require_state(state)
    state["budgetSpent"] += 1


# ---------------------------------------------------------------------------
# 5. The loud DECISION trail + durable recount (AT-L7 / AT-L13)
# ---------------------------------------------------------------------------


def _validate_reason(reason: Any, context: str) -> None:
    """Raise :class:`AdaptiveError` unless *reason* is a valid AT-L7 reason token."""
    if not isinstance(reason, str):
        raise AdaptiveError(f"{context}: reason must be a string (got {reason!r}). STOP.")
    if reason in _STATIC_REASONS:
        return
    if reason.startswith("event:"):
        name = reason[len("event:") :]
        if name and not any(ch.isspace() for ch in name):
            return
    raise AdaptiveError(
        f"{context}: unknown reason {reason!r} — valid reasons: 'event:<name>' or "
        f"{sorted(_STATIC_REASONS)} (AT-L7). STOP."
    )


def _validate_token(value: Any, field: str, context: str) -> None:
    """Raise unless *value* is a non-empty, whitespace-free, arrow-free string token."""
    if (
        not isinstance(value, str)
        or not value
        or any(ch.isspace() for ch in value)
        or "->" in value
    ):
        raise AdaptiveError(
            f"{context}: {field} must be a non-empty string without whitespace or "
            f"'->' (got {value!r}) — it must survive the recount parse (AT-L7). STOP."
        )


def render_tier_decision(
    task_or_dispatch: str, from_rung: str, to_rung: str, reason: str
) -> str:
    """Render the LOUD board ``DECISION`` payload for one adaptive move (AT-L7).

    Format (byte-pinned — the recount trail depends on it):
    ``tier: <task|dispatch> <from>-><to> reason <reason>``. These lines are the
    DURABLE recount trail for budget spend and bump state across conductor
    compaction (AT-L7/AT-L13 — the thrash-budget recount precedent), so every
    field is validated to survive the parse. Every adaptive move is LOUD — never
    silent.

    Args:
        task_or_dispatch: The task id or dispatch name that moved.
        from_rung: The rung the dispatch would have resolved to without adaptation.
        to_rung: The rung it actually resolved to.
        reason: ``event:<name>`` or one of ``failbump`` / ``streak`` /
            ``complexity`` / ``anchor-switch-reset`` / ``budget-exhausted``.

    Returns:
        The payload string.

    Raises:
        AdaptiveError: On an unknown/malformed reason, or a field containing
            whitespace or ``->`` (it would corrupt the recount trail — fail-closed
            at render time, D136).
    """
    _validate_token(task_or_dispatch, "task_or_dispatch", "render_tier_decision")
    _validate_token(from_rung, "from_rung", "render_tier_decision")
    _validate_token(to_rung, "to_rung", "render_tier_decision")
    _validate_reason(reason, "render_tier_decision")
    return f"tier: {task_or_dispatch} {from_rung}->{to_rung} reason {reason}"


def recount_from_decisions(payloads: list[str], premium_rung: str) -> dict:
    """Rebuild durable adaptive counters from a board DECISION trail (AT-L7/AT-L13).

    The recount after a conductor restart/compaction: ``budgetSpent`` = the count of
    ``tier:`` lines whose reason is ``event:<name>`` AND whose ``to`` rung equals
    *premium_rung* (premium spends are exactly the event escalations that LANDED on
    the premium rung — an event escalation that ceilinged at the anchor spent
    nothing); ``bumped`` = ``{task: True}`` for every ``failbump`` line (AT-L8's
    once-per-task mark survives the restart).

    Non-``tier:`` payloads are IGNORED — they are other DECISION types, not
    malformed. A payload that DOES start with ``tier:`` but fails the parse RAISES:
    a corrupt trail must never silently under-count spend (fail-closed recount,
    D136/AT-L13).

    Args:
        payloads: The board DECISION payload strings, oldest-first or any order.
        premium_rung: The family's premium rung name (e.g. ``"fable"``, AT-L17).

    Returns:
        ``{"budgetSpent": int, "bumped": {task_id: True, ...}}``.

    Raises:
        AdaptiveError: On a non-string payload or a malformed ``tier:`` payload
            (wrong token count, missing ``reason`` keyword, malformed ``from->to``
            transition, or an invalid reason token).
    """
    budget_spent = 0
    bumped: dict[str, bool] = {}
    for payload in payloads:
        if not isinstance(payload, str):
            raise AdaptiveError(
                f"recount_from_decisions: payload must be a string (got {payload!r}) — "
                "a corrupt trail must not silently under-count spend (D136). STOP."
            )
        if not payload.startswith("tier:"):
            continue  # another DECISION type — ignored, not malformed

        tokens = payload.split(" ")
        if len(tokens) != 5 or tokens[0] != "tier:" or tokens[3] != "reason":
            raise AdaptiveError(
                f"recount_from_decisions: malformed tier: payload {payload!r} — "
                "expected 'tier: <task> <from>-><to> reason <reason>' (AT-L7). STOP."
            )
        task, transition, reason = tokens[1], tokens[2], tokens[4]
        rungs = transition.split("->")
        if len(rungs) != 2 or not rungs[0] or not rungs[1]:
            raise AdaptiveError(
                f"recount_from_decisions: malformed transition {transition!r} in "
                f"{payload!r} — expected '<from>-><to>' (AT-L7). STOP."
            )
        _validate_reason(reason, "recount_from_decisions")

        if reason == "failbump":
            bumped[task] = True
        elif reason.startswith("event:") and rungs[1] == premium_rung:
            budget_spent += 1
    return {"budgetSpent": budget_spent, "bumped": bumped}


# ---------------------------------------------------------------------------
# 6. Mid-run anchor switch (AT-L17b)
# ---------------------------------------------------------------------------


def anchor_switch_reset(state: dict) -> None:
    """Reset ALL adaptive state on a mid-run anchor change (mutates *state*).

    AT-L17b: anchor-relative state re-based against a different ladder is undefined
    arithmetic — reset is the only honest posture. Clears bump counters, bump marks,
    streaks, and dampers; **PRESERVES ``budgetSpent``** (money spent is spent). The
    caller emits the accompanying board NOTE naming the reset (never silent).

    Args:
        state: The :func:`new_state` dict (mutated in place).

    Raises:
        AdaptiveError: On a malformed *state*.
    """
    _require_state(state)
    state["bumpCounters"].clear()
    state["bumped"].clear()
    state["streaks"].clear()
    state["dampers"].clear()
