"""kata_advisor.py — the pure advisor-consult spend/state/outcome engine (advisor-executor).

Where :mod:`kata_models` owns the advisor LEGALITY gate (the §3.2 sibling
``advisor_status`` / ``advisor_rung_of`` — is a consult allowed, and at which rung),
this module owns the advisor SPEND layer: the per-run advisor state (used-count +
per-event tally + lapse log + per-consult outcomes), the OWN budget pool resolved from
the ``advisor.budget`` block, the FCFS-with-floor-reservation spend discipline copied in
SHAPE from :func:`kata_adaptive.can_spend` (never importing or mutating that engine —
``tools/kata_adaptive.py`` is BYTE-UNTOUCHED, DESIGN §3.11/S-11b), the grant-before-
dispatch spend commit (S-19a), the EV-1 outcome pairing enum, the loud ``advisor:``
board DECISION trail + its durable recount (S-23b), and the run-ledger ``advisor``
fragment (§3.9).

It is pure, fail-closed DECISION code (D136 — a swallowed error here would silently
over-spend the advisor pool or mis-pair an outcome, the exact defects this layer exists
to prevent), so malformed input RAISES :class:`AdvisorError` rather than defaulting
permissively. There is NO permissive absent-budget leg: the G-6 mode defaults
(standard 5/1 · advanced 10/2) are BOOTSTRAP-COMPOSITION constants written into the
``advisor`` block, NOT resolver fallbacks — :func:`resolve_advisor_budget` FAIL-CLOSES
on an absent or malformed ``budget`` in a present block (the hand-edit posture, agreeing
with ``kata_models._validate_advisor``'s budget-REQUIRED rule; the two layers must never
disagree).

Determinism Doctrine (``docs/DETERMINISM-DOCTRINE.md``): every emitted structure is
sorted at its boundary (consult rows by id, per-event tallies by event name), the board
DECISION line is byte-pinned so the recount re-derives byte-stable, and there is NO
dict-order-driven serialization. Exec-safety: this module spawns NO subprocess, does NO
I/O, and is stdlib-only — a pure in-memory state machine over already-parsed objects.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "ADVISOR_OUTCOMES",
    "ADVISOR_RESERVED_EVENTS",
    "AdvisorError",
    "can_spend_advisor",
    "ledger_fragment",
    "new_advisor_state",
    "record_advisor_spend",
    "record_outcome",
    "recount_from_advisor_decisions",
    "render_advisor_decision",
    "resolve_advisor_budget",
]


class AdvisorError(Exception):
    """Fail-closed advisor-engine error (D136).

    Raised by every guard on malformed input: a wrong-shaped ``advisor`` state, an
    absent/malformed ``advisor.budget`` in a present block, a non-int/negative budget
    total, an unknown EV-1 outcome, a non-string spend event, or a corrupt ``advisor:``
    recount payload. The orchestrator's documented response is a loud board NOTE +
    unadvised-proceed (advice never gates, DESIGN §3.10) for a runtime lapse, or a
    load-guard STOP for a malformed config — never a silent over-spend.
    """


# ---------------------------------------------------------------------------
# EV-1 outcome pairing enum (DESIGN §3.9 — exact, LOCKED)
# ---------------------------------------------------------------------------

#: The advised-redispatch outcome vocabulary (EV-1, ELEVATE-accepted). A consult's
#: outcome is derived by the orchestrator's single-writer state path: the advised
#: redispatch PASSES its gate ⇒ ``advised-pass``; it FAILS and the D150 bump then fires
#: ⇒ ``advised-fail-bumped``; it FAILS with no bump available (bump already consumed /
#: ``models.adaptive`` absent / rung at its mode ceiling) ⇒ ``advised-fail-ceiling``. A
#: run ending before the pairing resolves records an explicit ``None`` (honest absence,
#: never fabricated).
ADVISOR_OUTCOMES: tuple[str, str, str] = (
    "advised-pass",
    "advised-fail-bumped",
    "advised-fail-ceiling",
)

#: Per-mode reserved-event sets (S-13 — the reserve coverage intent). The standard
#: reserve (1) covers the fix-loop-ceiling consult; the advanced reserve (2) covers the
#: fix-loop-ceiling consult AND the reroll-grounding consult — the late-run hard
#: moments. Realized as the copied ``can_spend`` SHAPE: EITHER reserved event may draw
#: the reserve (the per-event ×1 is coverage intent, not a per-event sub-pool — the
#: AT-L13 precedent, DESIGN §7 risk 5).
ADVISOR_RESERVED_EVENTS: dict[str, tuple[str, ...]] = {
    "standard": ("advisor-fix-loop-ceiling",),
    "advanced": ("advisor-fix-loop-ceiling", "advisor-reroll-grounding"),
}

_STATE_KEYS: frozenset[str] = frozenset({"used", "byEvent", "lapses", "outcomes"})
_BUDGET_KEYS: frozenset[str] = frozenset({"calls", "reserved"})


def _strict_int(value: Any) -> bool:
    """Return True iff *value* is a real int (bool is rejected — it subclasses int)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _require_state(state: Any) -> None:
    """Raise :class:`AdvisorError` unless *state* has the :func:`new_advisor_state` shape."""
    if not isinstance(state, dict) or not _STATE_KEYS <= set(state):
        raise AdvisorError(
            f"advisor state must be a dict with keys {sorted(_STATE_KEYS)} "
            "(use new_advisor_state()) — a malformed state is a caller bug (D136). STOP."
        )


def _require_token(value: Any, field: str, context: str) -> None:
    """Raise unless *value* is a non-empty, whitespace-free string (recount-safe)."""
    if not isinstance(value, str) or not value or any(ch.isspace() for ch in value):
        raise AdvisorError(
            f"{context}: {field} must be a non-empty string without whitespace "
            f"(got {value!r}) — it must survive the advisor: recount parse (S-23b). STOP."
        )


# ---------------------------------------------------------------------------
# 1. Per-run advisor state (§3.5)
# ---------------------------------------------------------------------------


def new_advisor_state() -> dict:
    """Return a fresh per-run advisor state (zero spend, empty tallies/log/outcomes).

    Shape (§3.5): ``{"used": int, "byEvent": {event: n}, "lapses": [str],
    "outcomes": {"<task-id>-<n>": <outcome|None>}}``. State is PER-RUN; the single
    writer is the orchestrator (``kata_board.write_state``), and its durable recount
    across conductor compaction is the ``advisor:`` DECISION trail
    (:func:`render_advisor_decision` / :func:`recount_from_advisor_decisions`).

    Returns:
        The empty state dict (fresh mutable sub-containers every call).
    """
    return {"used": 0, "byEvent": {}, "lapses": [], "outcomes": {}}


# ---------------------------------------------------------------------------
# 2. Budget resolution (§3.5 / §5 — fail-closed, NO permissive fallback)
# ---------------------------------------------------------------------------


def resolve_advisor_budget(advisor: Any) -> tuple[int, int]:
    """Resolve ``(calls, reserved)`` from a PRESENT ``advisor`` block's ``budget``.

    **The G-6 mode defaults (standard 5/1 · advanced 10/2) are BOOTSTRAP-COMPOSITION
    constants documented in DESIGN §4, NOT resolver fallbacks.** This function FAIL-
    CLOSES (raises) on an absent or malformed ``budget`` in a present block — the
    hand-edit posture, agreeing with ``kata_models._validate_advisor``'s budget-REQUIRED
    rule so the two layers never disagree (DESIGN §5).

    Args:
        advisor: The ``advisor`` config block (a dict; ``budget`` REQUIRED).

    Returns:
        ``(calls, reserved)`` — strict ints with ``0 <= reserved <= calls``.

    Raises:
        AdvisorError: On a non-dict *advisor*, an absent/non-dict ``budget``, an
            unknown budget key, a non-int (bool included) / negative ``calls`` or
            ``reserved``, or ``reserved > calls`` (D136 — load-guard STOP material).
    """
    if not isinstance(advisor, dict):
        raise AdvisorError(
            f"resolve_advisor_budget: advisor block must be a dict (got "
            f"{type(advisor).__name__}) — STOP (D136)."
        )
    if "budget" not in advisor:
        raise AdvisorError(
            "resolve_advisor_budget: a present advisor block REQUIRES 'budget' — the "
            "G-6 defaults (5/1 · 10/2) are bootstrap-composition constants, NOT resolver "
            "fallbacks (DESIGN §5). STOP (D136)."
        )
    budget = advisor["budget"]
    if not isinstance(budget, dict):
        raise AdvisorError(
            f"resolve_advisor_budget: advisor.budget must be an object (got "
            f"{type(budget).__name__}) — STOP (D136)."
        )
    unknown = set(budget) - _BUDGET_KEYS
    if unknown:
        raise AdvisorError(
            f"resolve_advisor_budget: unknown budget key(s) {sorted(unknown)} — known: "
            f"{sorted(_BUDGET_KEYS)}. STOP (D136)."
        )
    for key in ("calls", "reserved"):
        if key not in budget:
            raise AdvisorError(
                f"resolve_advisor_budget: advisor.budget requires {key!r} (strict int) — "
                "STOP (D136)."
            )
        if not _strict_int(budget[key]) or budget[key] < 0:
            raise AdvisorError(
                f"resolve_advisor_budget: budget[{key!r}] must be an int >= 0 (got "
                f"{budget[key]!r}) — STOP (D136)."
            )
    calls, reserved = budget["calls"], budget["reserved"]
    if reserved > calls:
        raise AdvisorError(
            f"resolve_advisor_budget: reserved ({reserved}) must be <= calls ({calls}) — "
            "an over-reservation would deny every non-reserved consult. STOP (D136)."
        )
    return calls, reserved


# ---------------------------------------------------------------------------
# 3. Spend discipline (§3.5 — the kata_adaptive.can_spend SHAPE, copied not imported)
# ---------------------------------------------------------------------------


def can_spend_advisor(
    calls: int,
    reserved_count: int,
    reserved_events: Any,
    state: dict,
    event: str,
) -> bool:
    """Decide whether one advisor consult for *event* may spend budget (FCFS + reserve).

    The copied SHAPE of :func:`kata_adaptive.can_spend` (which is BYTE-UNTOUCHED — this
    is a sibling, never an import-for-reuse): the last *reserved_count* calls are
    reserved for the mode's *reserved_events* (S-13). A reserved event may spend down to
    zero (``remaining >= 1``); a non-reserved event needs ``remaining > reserved_count``.
    A denial means the caller proceeds UNADVISED (no consult), LOUD — denying spend is
    the conservative direction, so an event outside *reserved_events* is simply
    non-reserved here (registry-membership validation is the legality gate's job,
    ``kata_models.advisor_status``).

    Args:
        calls: The resolved call budget N (:func:`resolve_advisor_budget`).
        reserved_count: The mode's reserve (standard 1 · advanced 2).
        reserved_events: The mode's :data:`ADVISOR_RESERVED_EVENTS` set.
        state: The :func:`new_advisor_state` dict (reads ``used``).
        event: The advisor event name driving this consult.

    Returns:
        True iff the consult may commit an advisor spend.

    Raises:
        AdvisorError: On a malformed *state*, a non-int/negative *calls* or
            *reserved_count*, or a non-container *reserved_events* (D136).
    """
    _require_state(state)
    if not _strict_int(calls) or calls < 0:
        raise AdvisorError(
            f"can_spend_advisor: calls must be an int >= 0 (got {calls!r}) — STOP (D136)."
        )
    if not _strict_int(reserved_count) or reserved_count < 0:
        raise AdvisorError(
            f"can_spend_advisor: reserved_count must be an int >= 0 (got "
            f"{reserved_count!r}) — STOP (D136)."
        )
    if not isinstance(reserved_events, (tuple, list, set, frozenset)):
        raise AdvisorError(
            f"can_spend_advisor: reserved_events must be a tuple/list/set (got "
            f"{type(reserved_events).__name__}) — STOP (D136)."
        )
    remaining = calls - state["used"]
    if event in reserved_events:
        return remaining >= 1
    return remaining > reserved_count


def record_advisor_spend(state: dict, event: str) -> None:
    """Commit one advisor spend (mutates *state*; counted at DISPATCH COMMIT, S-19a).

    Grant-before-dispatch: a granted consult CONSUMES its budget call at dispatch time,
    BEFORE the dispatch outcome is known (prevents retry-mining — a failed consult still
    spent). The conductor is the single dispatcher, so one counter, no cross-process
    race; the durable recount of this counter is the ``advisor:`` DECISION trail.

    Args:
        state: The :func:`new_advisor_state` dict (mutated in place).
        event: The advisor event name for this consult.

    Raises:
        AdvisorError: On a malformed *state* or a non-string/empty *event*.
    """
    _require_state(state)
    _require_token(event, "event", "record_advisor_spend")
    state["used"] += 1
    state["byEvent"][event] = state["byEvent"].get(event, 0) + 1


# ---------------------------------------------------------------------------
# 4. EV-1 outcome pairing (§3.9)
# ---------------------------------------------------------------------------


def record_outcome(state: dict, consult_id: str, outcome: str | None) -> None:
    """Record a consult's EV-1 outcome (mutates *state*; explicit ``None`` = pending).

    The outcome is pure derived data written by the single-writer state path (§3.9):
    :data:`ADVISOR_OUTCOMES` for a resolved pairing, or ``None`` for a consult whose
    pairing has not yet resolved (a run ending before the pairing resolves records the
    explicit ``None`` — honest absence, never fabricated).

    Args:
        state: The :func:`new_advisor_state` dict (mutated in place).
        consult_id: The consult identity ``"<task-id>-<n>"`` (the outcomes key).
        outcome: A member of :data:`ADVISOR_OUTCOMES`, or ``None`` (pending).

    Raises:
        AdvisorError: On a malformed *state*, a non-string/empty *consult_id*, or an
            *outcome* neither ``None`` nor in :data:`ADVISOR_OUTCOMES` (D136).
    """
    _require_state(state)
    _require_token(consult_id, "consult_id", "record_outcome")
    if outcome is not None and outcome not in ADVISOR_OUTCOMES:
        raise AdvisorError(
            f"record_outcome: outcome {outcome!r} not in the EV-1 enum "
            f"{list(ADVISOR_OUTCOMES)} (or None for pending) — an unknown outcome is a "
            "producer bug (D136). STOP."
        )
    state["outcomes"][consult_id] = outcome


# ---------------------------------------------------------------------------
# 5. The loud DECISION trail + durable recount (S-23b)
# ---------------------------------------------------------------------------


def render_advisor_decision(consult_id: str, event: str) -> str:
    """Render the LOUD board ``DECISION`` payload for one advisor consult (S-23b).

    Format (byte-pinned — the recount trail depends on it):
    ``advisor: <consult-id> event <event>``. These lines are the DURABLE recount trail
    for ``used`` / ``byEvent`` across conductor compaction (the fix-loop-counter recount
    precedent), so every field is validated to survive the parse.

    Args:
        consult_id: The consult identity ``"<task-id>-<n>"``.
        event: The advisor event name driving this consult.

    Returns:
        The payload string.

    Raises:
        AdvisorError: On a field containing whitespace or an empty field (it would
            corrupt the recount trail — fail-closed at render time, D136).
    """
    _require_token(consult_id, "consult_id", "render_advisor_decision")
    _require_token(event, "event", "render_advisor_decision")
    return f"advisor: {consult_id} event {event}"


def recount_from_advisor_decisions(payloads: list[str]) -> dict:
    """Rebuild ``used`` / ``byEvent`` from a board ``advisor:`` DECISION trail (S-23b).

    The recount after a conductor restart/compaction: ``used`` = the count of
    ``advisor:`` lines; ``byEvent`` = the per-event tally over those lines. Non-
    ``advisor:`` payloads are IGNORED — they are other DECISION types, not malformed. A
    payload that DOES start with ``advisor:`` but fails the parse RAISES: a corrupt trail
    must never silently under-count spend (fail-closed recount, D136).

    Args:
        payloads: The board DECISION payload strings, any order.

    Returns:
        ``{"used": int, "byEvent": {event: n, ...}}``.

    Raises:
        AdvisorError: On a non-string payload or a malformed ``advisor:`` payload
            (wrong token count or a missing ``event`` keyword).
    """
    used = 0
    by_event: dict[str, int] = {}
    for payload in payloads:
        if not isinstance(payload, str):
            raise AdvisorError(
                f"recount_from_advisor_decisions: payload must be a string (got "
                f"{payload!r}) — a corrupt trail must not silently under-count (D136). STOP."
            )
        if not payload.startswith("advisor:"):
            continue  # another DECISION type — ignored, not malformed
        tokens = payload.split(" ")
        if len(tokens) != 4 or tokens[0] != "advisor:" or tokens[2] != "event":
            raise AdvisorError(
                f"recount_from_advisor_decisions: malformed advisor: payload {payload!r} "
                "— expected 'advisor: <consult-id> event <event>' (S-23b). STOP."
            )
        event = tokens[3]
        used += 1
        by_event[event] = by_event.get(event, 0) + 1
    return {"used": used, "byEvent": by_event}


# ---------------------------------------------------------------------------
# 6. The run-ledger advisor fragment (§3.9)
# ---------------------------------------------------------------------------


def ledger_fragment(state: dict, cap: int) -> dict:
    """Build the §3.9 run-ledger ``advisor`` value from the run's advisor *state*.

    Shape (§3.9): ``{"consults": [{"id", "outcome"}], "byEvent": {event: n},
    "budgetUsed": int, "budgetCap": int, "lapses": [str]}`` — the after-action rollup's
    data source, consumed by ``kata_telemetry.build_ledger_row``. Determinism Doctrine:
    the ``consults`` list is sorted by consult id and ``byEvent`` is rebuilt in sorted
    key order, so the same state ⇒ the same bytes regardless of insertion order.

    Args:
        state: The :func:`new_advisor_state` dict (read-only here).
        cap: The advisor budget cap N (:func:`resolve_advisor_budget`'s ``calls``).

    Returns:
        The ledger ``advisor`` value (fresh, deterministically ordered).

    Raises:
        AdvisorError: On a malformed *state* or a non-int/negative *cap* (D136).
    """
    _require_state(state)
    if not _strict_int(cap) or cap < 0:
        raise AdvisorError(
            f"ledger_fragment: cap must be an int >= 0 (got {cap!r}) — STOP (D136)."
        )
    consults = [
        {"id": cid, "outcome": state["outcomes"][cid]}
        for cid in sorted(state["outcomes"])
    ]
    by_event = {event: state["byEvent"][event] for event in sorted(state["byEvent"])}
    return {
        "consults": consults,
        "byEvent": by_event,
        "budgetUsed": state["used"],
        "budgetCap": cap,
        "lapses": list(state["lapses"]),
    }
