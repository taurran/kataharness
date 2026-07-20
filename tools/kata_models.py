"""kata_models.py — Pure-stdlib model-family ladder and resolver for KataHarness.

No third-party imports.  No imports from kata_install.

This module is the load-bearing abstraction for D59 model routing: skills carry
no ``model:`` frontmatter; the dispatcher calls ``resolve()`` at runtime to pick
a concrete model ID that is *below* the operator's current session anchor,
returning ``None`` (OMIT → inherit the anchor) whenever no step-down applies.

Public API
----------
FAMILY_LADDERS   : dict[str, list[str]]   — short-name ladder per family (low→high)
ID_MAP           : dict[str, str]          — short-name → full model ID (Anthropic)
SKILL_WORK_CLASS : dict[str, str]          — skill → work-class (critical|coding|economy)
ADAPTIVE_EVENTS  : tuple[str, ...]         — ordered event registry (AT-L5); the
                   order IS the spend-priority documentation (AT-L13 FCFS — the
                   reservation set is the first two members)
ADAPTIVE_EVENT_SITES : dict[str, str]      — event → covering dispatch site (AT-L5)
ADVISOR_EVENTS   : tuple[str, ...]         — advisor consult event registry (§3.3),
                   sibling to ADAPTIVE_EVENTS (byte-untouched, S-20)
ADVISOR_EVENT_SITES : dict[str, str]       — advisor event → covering kata-advise site
family_of(anchor) -> str | None
advisor_rung_of(family, anchor) -> str | None  — advisor consult rung ("fable" for any
                   sub-fable anchor, else None → inherit-at-anchor; §3.2, S-24)
validate_advisor_block(advisor) -> None    — fail-closed advisor-block shape guard (D136)
advisor_status(advisor, anchor, *, family, mode, event) -> {"fires", "reason", "rung"}
                   — the advisor sibling legality gate (§3.2, S-16/S-21/S-24)
step_down(anchor, steps, family) -> str | None
classify_premium_scope(scope) -> str       — "classes" | "events" (AT-L15 type-dispatch)
premium_rung_of(family, anchor) -> str | None  — one-rung-above helper (AT-L17)
resolve(skill, mode, anchor, *, family, coder_floor, premium=None, event=None) -> str | None
premium_status(premium, anchor, *, family, mode, event=None) -> {"fires": bool, "reason": str}
fallback_chain(id, family) -> list[str | None]

Premium gate (§3 GATED AMENDMENT to the frozen model-tiering DESIGN, D148)
--------------------------------------------------------------------------
``resolve()`` gains an ADDITIVE keyword-only ``premium`` param consuming the
``kata.config.models.premium`` dict.  ``premium=None`` (the default / absent-block
case) yields byte-for-byte frozen behaviour — no premium branch exists.  When a
well-formed ``premium`` block is supplied the branch fires ONLY when all four
conjuncts hold (approved ∧ work-class ∈ scope ∧ offer sits EXACTLY one rung above
the anchor ∧ ``mode == "advanced"``), returning the EXPLICIT ``offer`` id (never an
inherit, never a ladder-walk).  A present-but-malformed block RAISES ``ValueError``
(fail-closed, D136) — a broken approval is never silently ignored.

Adaptive premium scope (model-tiering DESIGN Amendment #2 / adaptive-tiering, D150)
-----------------------------------------------------------------------------------
``premium.scope`` becomes TYPE-DISPATCHED (AT-L15): a LIST value keeps the D148
work-class semantics BYTE-FOR-BYTE (above — zero change to any shipped path); an
OBJECT value ``{"events": [...], "budget": {"calls": N}}`` activates the ADAPTIVE
form, where conjunct #2 of the four-conjunct fire rule reads "event ∈ scope.events
AND work-class ∈ {critical, coding}" (the R-9 economy exclusion is STRUCTURAL in
BOTH forms — the events leg of the conjunction lives in premium_status, the
work-class leg in resolve, mirroring the list-form split) — the rule's SHAPE
(four conjuncts, offer exactly
one rung above the anchor, ``mode == "advanced"``, recorded approval) is unchanged.
Any other scope type / unknown event name / unknown object key / non-int budget ⇒
load-guard RAISE (AT-L15/AT-L21, GB12/D45).  Absent ``events`` key in the object
form ⇒ RAISE (the hand-edit posture); explicit ``events: []`` ⇒ legal no-op.
Budget SHAPE is validated at load; budget SPEND is enforced by the conductor
(kata_adaptive), never here.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Family-ladder registry
# ---------------------------------------------------------------------------

# Anthropic ladder (low → high).
# mythos is gated / unavailable for most accounts — retained as the deliberate
# availability-fallback test case.
_ANTHROPIC_LADDER: list[str] = ["haiku", "sonnet", "opus", "fable", "mythos"]

# Shape-only placeholders — re-grounded per-adapter when those adapters are built.
_OPENAI_LADDER:  list[str] = []   # placeholder: e.g. ["mini", "standard", "plus", ...]
_GEMINI_LADDER:  list[str] = []   # placeholder: e.g. ["flash", "pro", "ultra", ...]
_GENERIC_LADDER: list[str] = []   # placeholder: e.g. ["small", "medium", "large", ...]

FAMILY_LADDERS: dict[str, list[str]] = {
    "anthropic": _ANTHROPIC_LADDER,
    "openai":    _OPENAI_LADDER,
    "gemini":    _GEMINI_LADDER,
    "generic":   _GENERIC_LADDER,
}

# Verified short→full-ID map (Anthropic only; other families re-grounded per-adapter).
# Do NOT change these strings without a corresponding registry bump — tests reference
# these constants directly so a bump is caught automatically.
ID_MAP: dict[str, str] = {
    "haiku":  "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-5",
    "opus":   "claude-opus-4-8",
    "fable":  "claude-fable-5",
    "mythos": "claude-mythos-5",  # gated — deliberate fallback-test anchor
}

# Reverse map: full model ID → ladder short-name.
# Built from ID_MAP so it stays in sync automatically — no manual maintenance.
# Used by _normalize_anchor() to accept a full id wherever a short-name anchor is expected.
_ID_TO_SHORT: dict[str, str] = {full_id: short for short, full_id in ID_MAP.items()}


def _normalize_anchor(anchor: str) -> str:
    """Normalize a full model ID to its ladder short-name, or return *anchor* unchanged.

    If *anchor* is a known full model ID in ``_ID_TO_SHORT`` (e.g. ``"claude-opus-4-8"``),
    returns its short-name equivalent (e.g. ``"opus"``).  Otherwise returns *anchor*
    unchanged — short names, unknown IDs, and sentinels (``"session"``) all pass through
    without modification.

    Applied at the top of ``family_of()``, ``step_down()``, and ``resolve()`` so that a
    full-model-id anchor written by ``kata-initiate`` / ``kata-bootstrap`` into
    ``kata.config`` activates model-tiering identically to its short-name equivalent.

    BC guarantees
    -------------
    - Short-name anchors (``"opus"`` etc.) are not in ``_ID_TO_SHORT`` → unchanged.
    - Unknown full ids (e.g. ``"claude-zzz-9"``) are not in ``_ID_TO_SHORT`` → unchanged
      → ``family_of`` returns ``None`` → ``resolve`` returns ``None`` (inherit-on-doubt).
    - The ``"session"`` sentinel and any other non-ID string passes through unchanged.
    """
    return _ID_TO_SHORT.get(anchor, anchor)

# ---------------------------------------------------------------------------
# Work-class registry  (R5: full 47-skill coverage — W3-B build task)
# ---------------------------------------------------------------------------
# Three classes:
#   critical — judgment, grilling, evaluation, planning, the gate
#   coding   — build, refactor, encode, TDD
#   economy  — reporting, graphing, summaries, low-stakes loops
#
# Unlisted skills default to "critical" (safest / highest-judgment).

SKILL_WORK_CLASS: dict[str, str] = {
    # -----------------------------------------------------------------------
    # coordinate/
    # -----------------------------------------------------------------------
    "kata-board":       "economy",   # status board — reporting
    "kata-bootstrap":   "critical",  # initiation orchestration
    "kata-loop":        "critical",  # main execution loop — orchestration
    "kata-onboard":     "economy",   # mechanical onboarding
    "kata-orchestrate": "critical",  # orchestration
    "kata-preflight":   "critical",  # gate / readiness check
    "kata-readiness":   "critical",  # readiness assessment
    "kata-sprint":      "coding",    # sprint execution — build
    "kata-worktree":    "coding",    # worktree management — build support

    # -----------------------------------------------------------------------
    # evaluate/
    # -----------------------------------------------------------------------
    "kata-benchmark-report": "economy",   # reporting
    "kata-debrief":          "economy",   # reporting
    "kata-evaluate":         "critical",  # evaluation gate
    "kata-inline-eval":      "economy",   # frequent scoped chunk-eval, M4-L7 never-anchor (D131)
    "kata-report":           "economy",   # reporting
    "kata-review-advanced":  "critical",  # review gate
    "kata-review-essential": "critical",  # review gate
    "kata-review-standard":  "critical",  # review gate
    "kata-slop-check":       "critical",  # evaluation gate
    "kata-validate":         "critical",  # validation gate

    # -----------------------------------------------------------------------
    # execute/
    # -----------------------------------------------------------------------
    "kata-characterize":       "coding",   # characterization tests — TDD
    "kata-deviate":            "coding",   # deviation handling — implement
    "kata-diagnose-full":      "critical", # deep diagnostic — judgment
    "kata-diagnose-light":     "coding",   # quick diagnostic — encode
    "kata-iac-cloudformation": "coding",   # IaC implementation
    "kata-iac-terraform":      "coding",   # IaC implementation
    "kata-lang-profile":       "coding",   # language profile — build
    "kata-tdd":                "coding",   # TDD — build

    # -----------------------------------------------------------------------
    # handoff/
    # -----------------------------------------------------------------------
    "kata-defer":       "economy",  # mechanical defer
    "kata-handoff":     "economy",  # mechanical handoff
    "kata-orient":      "economy",  # context orientation
    "kata-selfhandoff": "economy",  # mechanical self-handoff

    # -----------------------------------------------------------------------
    # meta/
    # -----------------------------------------------------------------------
    "kata-improve":     "coding",   # refactor / improvement — build
    "kata-promote":     "critical", # promotion gate — judgment
    "kata-write-skill": "coding",   # skill authoring — implement

    # -----------------------------------------------------------------------
    # plan/
    # -----------------------------------------------------------------------
    "kata-advise":        "critical",  # advisor consult — judgment/consult work (S-7)
    "kata-comprehend":    "critical",  # understanding — research
    "kata-context":       "economy",   # context reporting
    "kata-design-doc":    "critical",  # design — orchestration
    "kata-graph":         "coding",    # graph generation — encode
    "kata-grill-advanced":  "critical",
    "kata-grill-essential": "critical",
    "kata-grill-standard":  "critical",
    "kata-plan-advanced":   "critical",
    "kata-plan-essential":  "critical",
    "kata-plan-standard":   "critical",
    "kata-research":        "critical",

    # -----------------------------------------------------------------------
    # modules/closeout/ and modules/initiation/
    # -----------------------------------------------------------------------
    "kata-closeout":   "critical",  # closeout orchestration
    "kata-initiate":   "critical",  # initiation orchestration
    "kata-understand": "critical",  # understanding — research
}

# ---------------------------------------------------------------------------
# Step-count tables — (mode, work_class) → steps (≤ 0), PER FAMILY.
# Negative value = rungs to descend from the anchor index.
# ---------------------------------------------------------------------------
#
# Anthropic (Fable-anchored; economy tiers one rung deeper than the generic
# default so standard/essential economy lands on Sonnet 5, and advanced economy
# on Opus — advanced keeps critical + coding on the Fable anchor):
#              critical  coding  economy
#   advanced      0        0      -1
#   standard      0       -1      -2
#   essential    -1       -2*     -2
#
# Default (every non-Anthropic family — empty-ladder placeholders today, so this
# table is currently unreachable; preserved unchanged for when those adapters land):
#              critical  coding  economy
#   advanced      0        0       0
#   standard      0       -1      -1
#   essential    -1       -2*     -1
#
# * coding/essential applies R1 coder-floor on top (see resolve()).

_STEPS_DEFAULT: dict[tuple[str, str], int] = {
    ("advanced",  "critical"): 0,
    ("advanced",  "coding"):   0,
    ("advanced",  "economy"):  0,
    ("standard",  "critical"): 0,
    ("standard",  "coding"):  -1,
    ("standard",  "economy"): -1,
    ("essential", "critical"): -1,
    ("essential", "coding"):  -2,
    ("essential", "economy"): -1,
}

_STEPS_ANTHROPIC: dict[tuple[str, str], int] = {
    ("advanced",  "critical"): 0,
    ("advanced",  "coding"):   0,
    ("advanced",  "economy"): -1,
    ("standard",  "critical"): 0,
    ("standard",  "coding"):  -1,
    ("standard",  "economy"): -2,
    ("essential", "critical"): -1,
    ("essential", "coding"):  -2,
    ("essential", "economy"): -2,
}

# Family → step table.  Absent family falls back to the generic default (BC).
_STEPS_BY_FAMILY: dict[str, dict[tuple[str, str], int]] = {
    "anthropic": _STEPS_ANTHROPIC,
}

# ---------------------------------------------------------------------------
# family_of() — pure helper (FIX-1)
# ---------------------------------------------------------------------------

def family_of(anchor: str) -> str | None:
    """Return the family key whose ladder contains *anchor* short-name, or None.

    Accepts a full model ID (e.g. ``"claude-opus-4-8"``) or a ladder short-name
    (e.g. ``"opus"``); a full ID is normalized to its short-name via
    ``_normalize_anchor()`` before the ladder search.

    Iterates ``FAMILY_LADDERS`` and returns the first matching family key.
    Returns ``None`` when the anchor is absent from every ladder (unknown anchor)
    or when all non-empty ladders are checked and none match.

    Used by ``step_down()`` and ``resolve()`` to derive the family when
    ``family="auto"`` (or falsy) is provided by the caller.
    """
    anchor = _normalize_anchor(anchor)
    for fam, ladder in FAMILY_LADDERS.items():
        if anchor in ladder:
            return fam
    return None


# ---------------------------------------------------------------------------
# step_down() — shared pure primitive (FIX-2)
# ---------------------------------------------------------------------------

def step_down(anchor: str, steps: int, family: str) -> str | None:
    """Pure primitive: step down *steps* rungs below *anchor* within *family*.

    Handles ``family="auto"`` (or falsy) derivation via ``family_of()``, ladder
    lookup, floor-clamp to ladder index 0, the zero-step contract
    (``resolved_idx == anchor_idx → None``), and the ``ID_MAP`` lookup.

    Returns ``None`` on any unknown / empty-ladder / zero-step case
    (inherit-on-doubt / BC guarantee).

    Parameters
    ----------
    anchor : short model name (e.g. ``"opus"``).
    steps  : number of rungs to descend (≥ 0).  ``0`` always returns ``None``
             (zero-step contract — the resolved rung equals the anchor rung).
    family : model-family key (e.g. ``"anthropic"``).  The canonical sentinel
             ``"auto"`` triggers ``family_of(anchor)`` derivation (FIX-1);
             any other value (including ``""``) is used as-is (BC — unknown
             family returns ``None``, inherit-on-doubt).
    """
    # Normalize: accept a full model id (e.g. "claude-opus-4-8") as anchor — maps it
    # to its short-name before any ladder lookup.  Short names and unknown ids pass through.
    anchor = _normalize_anchor(anchor)

    # FIX-1: derive family from anchor when explicitly "auto"
    # NOTE: family="" (empty string) preserves BC (unknown family → None);
    # only the canonical "auto" sentinel triggers derivation.
    if family == "auto":
        family = family_of(anchor) or ""

    ladder = FAMILY_LADDERS.get(family)
    if not ladder:
        return None
    if anchor not in ladder:
        return None

    anchor_idx: int = ladder.index(anchor)
    resolved_idx: int = max(0, anchor_idx - steps)

    # Zero-step contract: resolved == anchor → OMIT
    if resolved_idx == anchor_idx:
        return None

    short: str = ladder[resolved_idx]
    return ID_MAP.get(short)


# ---------------------------------------------------------------------------
# Adaptive event registry (AT-L5) — DATA, [TUNABLE] membership
# ---------------------------------------------------------------------------
# The tuple ORDER is the spend-priority documentation (AT-L13 FCFS with a floor
# reservation): the reservation set — the last budget calls held back — is the
# FIRST TWO members (freeze-gate-verdict, re-gate-after-hold).

ADAPTIVE_EVENTS: tuple[str, ...] = (
    "freeze-gate-verdict",
    "re-gate-after-hold",
    "escalation-adjudication",
    "fix-loop-diagnose",
    "final-initiative-review",
    "gate-rejection-rework-review",
    "fail-bump-escalation",
)

# Each event cites its covering DISPATCH SITE, verbatim from the AT-L5 table
# (freeze-gate v1 MED-12 — no phantom events; the conductor's own non-dispatched
# judgment can never be an event).  Note `ladder-trigger-2-grounding` was struck
# from the draft registry (BLOCKER-2): the trigger-#2 grounding pass is
# conductor-authored, not a dispatch — it cannot be tiered and is not an event.
ADAPTIVE_EVENT_SITES: dict[str, str] = {
    "freeze-gate-verdict":
        "the fresh-context kata-review freeze-gate dispatch (orchestrate freeze-gate step)",
    "re-gate-after-hold":
        "the re-gate reviewer dispatch after any HOLD fold",
    "escalation-adjudication":
        "the grounding-gate kata-evaluate / kata-review dispatches on the escalation path "
        "(NOT the conductor's routing call, which is not a dispatch)",
    "fix-loop-diagnose":
        "the at-budget kata-diagnose dispatch in the gate fix-loop",
    "final-initiative-review":
        "the D98 whole-initiative red-team dispatch",
    "gate-rejection-rework-review":
        "fix-loop judge re-runs + the confirmation pass",
    "fail-bump-escalation":
        "the AT-L8 bumped ATTEMPT dispatch — CONJUNCT-COVERAGE-ONLY member (re-gate MED-1): "
        "AT-L6's mode scaling does NOT apply to it; bump mechanics are exclusively AT-L8 + "
        "the AT-L2 ceiling (a registry listing so conjunct #2 is satisfiable by shape, "
        "never a second escalation rule for the same dispatch)",
}

# Known keys of the object-form scope / budget envelope (AT-L12/L15).
_SCOPE_OBJECT_KEYS: frozenset[str] = frozenset({"events", "budget"})
_BUDGET_KEYS: frozenset[str] = frozenset({"calls", "tokensOut"})


# ---------------------------------------------------------------------------
# Advisor event registry (advisor-executor §3.3) — DATA, sibling to
# ADAPTIVE_EVENTS (which stays BYTE-UNTOUCHED, S-20).
# ---------------------------------------------------------------------------
# Each event names a REAL covering kata-advise DISPATCH site (MED-12 discipline:
# the conductor's own non-dispatched judgment can never be an event).  These live
# in their OWN registry — an advisor event appearing in models.premium.scope.events
# stays ILLEGAL (classify_premium_scope RAISES, exactly as today).

ADVISOR_EVENTS: tuple[str, ...] = (
    "advisor-fail-threshold",
    "advisor-reroll-grounding",
    "advisor-fix-loop-ceiling",
    "advisor-worker-request",
    "advisor-planning-consult",
)

ADVISOR_EVENT_SITES: dict[str, str] = {
    "advisor-fail-threshold":
        "the conductor's auto kata-advise dispatch at the S-11 failure threshold "
        "(bump-pending observed, task unadvised) — kata-orchestrate loop, before the "
        "deferred bump (advisor-executor §3.6a)",
    "advisor-reroll-grounding":
        "the conductor's auto kata-advise dispatch at corrective-action ladder trigger #2, "
        "solicited BEFORE the tightened redispatch brief is authored (kata-orchestrate/"
        "SKILL.md:817-823; §3.6b) — covers the NEW kata-advise dispatch, NOT the "
        "conductor-authored grounding pass (the struck ladder-trigger-2-grounding "
        "ADAPTIVE event is not resurrected; BLOCKER-2 stands)",
    "advisor-fix-loop-ceiling":
        "the conductor's kata-advise dispatch at the fix-loop thrash valve, ONLY after a "
        "kata-diagnose fix-problem verdict (kata-orchestrate/SKILL.md:1235-1253; §3.6c)",
    "advisor-worker-request":
        "the conductor's kata-advise dispatch resolving an execution worker's "
        "advice-requested escalation (§3.7; escalation machinery "
        "kata-orchestrate/SKILL.md:1054-1080)",
    "advisor-planning-consult":
        "(a) the conductor's kata-advise dispatch resolving a planner-worker's "
        "advice-requested escalation during in-harness plan/design authoring (S-17a); "
        "(b) the session conductor's own direct kata-advise dispatch during the "
        "conductor-inline grill (kata-initiate Phase 5 — S-17b). Both advanced+granted only",
}


def classify_premium_scope(scope: object) -> str:
    """Type-dispatch + fail-closed validation for ``models.premium.scope`` (AT-L15).

    Returns
    -------
    ``"classes"``
        *scope* is a LIST — the v0.2.1 work-class form, byte-for-byte semantics
        (elements must be strings; content beyond that is the frozen D148 path's
        business — e.g. a hand-listed ``"economy"`` stays structurally excluded
        at fire time, R-9).
    ``"events"``
        *scope* is a DICT — the NEW adaptive form ``{events, budget}``:

        * ``events`` is REQUIRED (ABSENT ⇒ RAISE — the hand-edit posture, never
          inferred; an explicit ``[]`` is LEGAL — premium never fires, the
          operator said so on purpose).  Every member must be a registered
          :data:`ADAPTIVE_EVENTS` name (unknown ⇒ RAISE).
        * ``budget`` is OPTIONAL; when present it must be a dict with an int
          ``calls >= 0`` (bools rejected — fail-closed) and an optional int
          ``tokensOut >= 0`` (AT-L12); any unknown budget key ⇒ RAISE.  Only
          the SHAPE is validated here — spend enforcement is the conductor's
          (kata_adaptive), never the resolver's.
        * NO other scope keys are permitted (unknown key ⇒ RAISE).

    Any other *scope* type RAISES ``ValueError`` (AT-L15/AT-L21 fail-closed —
    GB12/D45: never a silent fall-through to unlimited premium OR to no-premium).
    Note ``bool``/tuple/set are NOT lists — type-dispatch is strict.
    """
    if isinstance(scope, list):
        if not all(isinstance(s, str) for s in scope):
            raise ValueError("models.premium.scope list form must be list[str]")
        return "classes"

    if isinstance(scope, dict):
        unknown = set(scope) - _SCOPE_OBJECT_KEYS
        if unknown:
            raise ValueError(
                f"models.premium.scope object form: unknown key(s) {sorted(unknown)}"
            )
        if "events" not in scope:
            raise ValueError(
                "models.premium.scope object form: required 'events' key is absent "
                "(explicit [] is the legal no-op; absence is a hand-edit error)"
            )
        events = scope["events"]
        if not isinstance(events, list):
            raise ValueError("models.premium.scope.events must be a list")
        for ev in events:
            if not isinstance(ev, str) or ev not in ADAPTIVE_EVENTS:
                raise ValueError(
                    f"models.premium.scope.events: unknown event {ev!r} "
                    f"(registry: {list(ADAPTIVE_EVENTS)})"
                )
        if "budget" in scope:
            budget = scope["budget"]
            if not isinstance(budget, dict):
                raise ValueError("models.premium.scope.budget must be a dict")
            unknown_b = set(budget) - _BUDGET_KEYS
            if unknown_b:
                raise ValueError(
                    f"models.premium.scope.budget: unknown key(s) {sorted(unknown_b)}"
                )
            if "calls" not in budget:
                raise ValueError("models.premium.scope.budget: required 'calls' key is absent")
            calls = budget["calls"]
            # bool is an int subclass — reject true/false, accept only real ints ≥ 0.
            if isinstance(calls, bool) or not isinstance(calls, int) or calls < 0:
                raise ValueError("models.premium.scope.budget.calls must be an int >= 0")
            if "tokensOut" in budget:
                tokens_out = budget["tokensOut"]
                if isinstance(tokens_out, bool) or not isinstance(tokens_out, int) \
                        or tokens_out < 0:
                    raise ValueError(
                        "models.premium.scope.budget.tokensOut must be an int >= 0"
                    )
        return "events"

    raise ValueError(
        f"models.premium.scope must be a list (classes form) or dict (events form), "
        f"got {type(scope).__name__}"
    )


def premium_rung_of(family: str, anchor: str) -> str | None:
    """Pure helper (AT-L17): the ladder rung EXACTLY one above *anchor* in
    *family*'s ladder, or ``None``.

    Family-agnostic — works for any registered :data:`FAMILY_LADDERS` ladder
    (anthropic today; an ``openai`` ladder's expensive top rung qualifies the
    moment it is registered).  Accepts a full model ID or a short-name anchor
    (normalized like every other entry point).  ``family="auto"`` derives the
    family from the anchor, consistent with :func:`step_down`.

    Returns ``None`` when: the family is unknown / its ladder is empty, the
    anchor is not on the ladder, or the anchor is already the TOP rung (no rung
    above — NO-FIRE territory, D148 generalized).
    """
    anchor = _normalize_anchor(anchor)
    if family == "auto":
        family = family_of(anchor) or ""
    ladder = FAMILY_LADDERS.get(family)
    if not ladder or anchor not in ladder:
        return None
    idx = ladder.index(anchor)
    if idx + 1 >= len(ladder):
        return None
    return ladder[idx + 1]


def advisor_rung_of(family: str, anchor: str) -> str | None:
    """Pure helper (advisor-executor §3.2, S-24): the advisor consult rung for
    *anchor* within *family* — the ladder's ``"fable"`` short-name for any
    sub-fable anchor, or ``None`` (arm (a) — inherit at the anchor).

    This is the sibling of :func:`premium_rung_of`, but it is NOT one-rung-above
    arithmetic: EVERY sub-fable anchor (sonnet AND haiku) consults **fable**, never
    the rung immediately above.  The multi-rung cost jump on low anchors is
    DELIBERATE — the feature IS a Fable-tier advisor (frozen goal); the budget pool
    bounds the spend.  **Never mythos by default.**

    Accepts a full model ID or a short-name anchor (normalized like every other
    entry point).  ``family="auto"`` derives the family from the anchor, consistent
    with :func:`step_down` / :func:`premium_rung_of`.

    Returns ``None`` (arm (a) — inherit-at-anchor) when ANY of:
      * the anchor is already fable/mythos-class (ladder index ≥ the ladder's
        ``"fable"`` index),
      * the family is unknown / its ladder is empty,
      * the ladder has no ``"fable"`` rung,
      * the anchor is not on the ladder.

    Non-Anthropic families (empty ladders) therefore return ``None`` ⇒ arm (a)
    inherit at the anchor (no fable-class rung exists in that family).
    """
    anchor = _normalize_anchor(anchor)
    if family == "auto":
        family = family_of(anchor) or ""
    ladder = FAMILY_LADDERS.get(family)
    if not ladder:
        return None
    if "fable" not in ladder:
        return None
    if anchor not in ladder:
        return None
    if ladder.index(anchor) >= ladder.index("fable"):
        return None
    return "fable"


# ---------------------------------------------------------------------------
# Premium gate (§3 GATED AMENDMENT / D148) — fail-closed conjunct evaluation
# ---------------------------------------------------------------------------

def _validate_premium(premium: dict) -> None:
    """Fail-closed shape guard for a ``models.premium`` block (D136).

    RAISES ``ValueError`` when *premium* is present-but-malformed — a broken
    approval is never silently ignored.  Validates ONLY the three fields the
    resolve-time decision reads: ``offer`` (str), ``approved`` (bool), ``scope``
    (list[str] classes form OR the AT-L15 events-form object — delegated to
    :func:`classify_premium_scope`).  ``grantedMode`` is the bootstrap
    mode-lapse arm (§3.3, a P2 prose consumer) and is NOT read here, so it is
    not required at resolve time.

    Note ``None`` is the *absent* case (handled by the callers), NOT malformed —
    it never reaches this guard.
    """
    if not isinstance(premium, dict):
        raise ValueError(
            f"models.premium must be a dict, got {type(premium).__name__}"
        )
    if "offer" not in premium or not isinstance(premium["offer"], str):
        raise ValueError("models.premium.offer missing or non-string")
    # bool is a subclass of int — accept only true booleans, reject 0/1 ints.
    if "approved" not in premium or not isinstance(premium["approved"], bool):
        raise ValueError("models.premium.approved missing or non-boolean")
    # Type-dispatched scope forms (AT-L15): list ⇒ classes (v0.2.1 byte-for-byte),
    # dict ⇒ events; anything else (including an absent key ⇒ None) RAISES.
    classify_premium_scope(premium.get("scope"))


def premium_status(
    premium: dict | None,
    anchor: str,
    *,
    family: str,
    mode: str,
    event: str | None = None,
) -> dict:
    """Report whether the premium gate FIRES at this anchor/mode, and why not.

    Returns ``{"fires": bool, "reason": str}`` for NO-FIRE surfacing / audit (the
    board-NOTE prose consumer is P2).  This evaluates the three *run-level*
    conjuncts that are independent of the dispatched skill — ``approved``,
    ``mode == "advanced"``, and the offer↔anchor relationship (offer EXACTLY one
    rung strictly above the anchor) — plus, in the EVENTS scope form only,
    conjunct #2 itself (``event ∈ scope.events``, Amendment #2).

    Conjunct #2 by scope form (AT-L15 type-dispatch)
    ------------------------------------------------
    * ``scope`` is a LIST (classes form): unchanged — conjunct #2 is
      ``work-class ∈ scope``, per-skill, applied by :func:`resolve`; *event* is
      IGNORED here (byte-for-byte v0.2.1 semantics).
    * ``scope`` is a DICT (events form): conjunct #2 is
      ``event is not None AND event ∈ scope["events"]`` and IS applied here —
      a class-based query (``event=None``) against an events-form scope is
      simply NO-FIRE, never a crash.

    Reasons (checked in this precedence order):
      * ``"absent"``           — *premium* is ``None`` (no block; frozen behaviour)
      * ``"not-approved"``     — ``approved`` is not ``True``
      * ``"mode-not-advanced"``— ``mode`` is not ``"advanced"`` (closes the silent
                                 standard-mode +2-rung cost blowout)
      * ``"no-family"``        — family unknown / empty ladder (inherit-on-doubt)
      * ``"unknown-anchor"``   — anchor absent from the family ladder
      * ``"unknown-offer"``    — offer absent from the family ladder
      * ``"offer-equals-anchor"`` — offer == anchor (e.g. anchor already fable)
      * ``"offer-below-anchor"``  — offer sits below the anchor
      * ``"offer-too-high"``   — offer 2+ rungs above (approval never escalates
                                 past ONE rung — the hand-edited-mythos guard)
      * ``"no-event"``         — events-form scope, but no *event* was supplied
                                 (the class-query-against-events-form case)
      * ``"event-not-in-scope"`` — events-form scope, *event* ∉ ``scope.events``
                                 (includes the explicit ``events: []`` no-op)
      * ``"fires"``            — every conjunct evaluated HERE holds (events form:
                                 the R-9 work-class leg is resolve()'s — a "fires"
                                 for an economy-destined dispatch is still declined
                                 there, the list-form status/resolve split mirrored)

    A present-but-malformed block RAISES ``ValueError`` (fail-closed, D136/AT-L21).
    """
    if premium is None:
        return {"fires": False, "reason": "absent"}

    _validate_premium(premium)  # fail-closed: malformed ⇒ raise

    if premium["approved"] is not True:
        return {"fires": False, "reason": "not-approved"}

    if mode != "advanced":
        return {"fires": False, "reason": "mode-not-advanced"}

    anchor_norm = _normalize_anchor(anchor)
    fam = family_of(anchor_norm) if family == "auto" else family
    ladder = FAMILY_LADDERS.get(fam or "")
    if not ladder:
        return {"fires": False, "reason": "no-family"}
    if anchor_norm not in ladder:
        return {"fires": False, "reason": "unknown-anchor"}

    offer_norm = _normalize_anchor(premium["offer"])
    if offer_norm not in ladder:
        return {"fires": False, "reason": "unknown-offer"}

    diff = ladder.index(offer_norm) - ladder.index(anchor_norm)
    if diff == 0:
        return {"fires": False, "reason": "offer-equals-anchor"}
    if diff < 0:
        return {"fires": False, "reason": "offer-below-anchor"}
    if diff > 1:
        return {"fires": False, "reason": "offer-too-high"}

    # diff == 1: offer sits EXACTLY one rung strictly above the anchor.

    # Amendment #2 (AT-L15 events form): the EVENTS leg of conjunct #2 ("event ∈
    # scope.events") is applied HERE; the R-9 work-class leg is resolve()'s.  The classes (list)
    # form is untouched: conjunct #2 stays per-skill in resolve(), event ignored.
    if isinstance(premium["scope"], dict):
        if event is None:
            return {"fires": False, "reason": "no-event"}
        if event not in premium["scope"]["events"]:
            return {"fires": False, "reason": "event-not-in-scope"}

    return {"fires": True, "reason": "fires"}


# ---------------------------------------------------------------------------
# Advisor sibling legality gate (advisor-executor §3.2) — fail-closed,
# DECOUPLED from models.premium (byte-untouched, S-16).  advisor.approved is the
# SOLE advisor legality/spend grant.
# ---------------------------------------------------------------------------

# Full §4 key set of a present ``advisor`` block (unknown keys RAISE at every level).
_ADVISOR_KEYS: frozenset[str] = frozenset(
    {"enabled", "approved", "grantedMode", "budget", "hooks", "phases"}
)
_ADVISOR_BUDGET_KEYS: frozenset[str] = frozenset({"calls", "reserved"})
_ADVISOR_HOOK_KEYS: frozenset[str] = frozenset(
    {"failThreshold", "rerollTrigger", "fixLoopCeiling"}
)
_ADVISOR_GRANTED_MODES: frozenset[str] = frozenset({"advanced", "standard"})
_ADVISOR_PHASES: frozenset[str] = frozenset({"planning", "execution", "fix-loop"})


def _is_strict_int(value: object) -> bool:
    """True iff *value* is a real ``int`` and NOT a ``bool`` (bool ⊂ int)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_advisor(advisor: dict) -> None:
    """Fail-closed shape guard for a present ``advisor`` config block (D136, S-5b).

    Mirrors :func:`_validate_premium`, enumerating the FULL advisor-executor §4 key
    set.  RAISES ``ValueError`` on ANY malformed field so the load-guard STOPs and
    escalates — a present-but-broken block is NEVER silently coerced to OFF.

    ``None`` is the *absent* case (all-OFF, byte-identical BC, S-4); it is handled
    by the callers and never reaches this guard.

    Rules
    -----
    * ``enabled`` — REQUIRED, strict ``bool``.
    * ``approved`` — REQUIRED, strict ``bool`` (the SOLE legality/spend grant, S-16).
    * ``grantedMode`` — OPTIONAL; when present ∈ {"advanced", "standard"}.
    * ``budget`` — REQUIRED in a present block: a dict with strict ints
      ``calls >= 0`` and ``0 <= reserved <= calls`` (both REQUIRED; bools rejected).
    * ``hooks`` — OPTIONAL; when present a dict; ``failThreshold`` a strict int ≥ 1
      (S-18 INTEGER), ``rerollTrigger`` a strict int, ``fixLoopCeiling`` a strict
      ``bool`` (each validated when present).
    * ``phases`` — OPTIONAL; when present a ``list[str]`` ⊆ {planning, execution,
      fix-loop}.
    * Unknown keys — top-level, in ``budget``, or in ``hooks`` — RAISE.
    """
    if not isinstance(advisor, dict):
        raise ValueError(
            f"advisor block must be a dict, got {type(advisor).__name__}"
        )

    unknown = set(advisor) - _ADVISOR_KEYS
    if unknown:
        raise ValueError(f"advisor block: unknown key(s) {sorted(unknown)}")

    # enabled / approved — required strict bools.
    if "enabled" not in advisor or not isinstance(advisor["enabled"], bool):
        raise ValueError("advisor.enabled missing or non-boolean")
    if "approved" not in advisor or not isinstance(advisor["approved"], bool):
        raise ValueError("advisor.approved missing or non-boolean")

    # grantedMode — optional; constrained value set when present.
    if "grantedMode" in advisor:
        gm = advisor["grantedMode"]
        if not isinstance(gm, str) or gm not in _ADVISOR_GRANTED_MODES:
            raise ValueError(
                f"advisor.grantedMode must be one of {sorted(_ADVISOR_GRANTED_MODES)} "
                f"when present, got {gm!r}"
            )

    # budget — REQUIRED in a present block (the layers-agree companion of
    # resolve_advisor_budget's fail-close; a hand-edited block without a budget
    # bricks the load-guard rather than silently defaulting).
    if "budget" not in advisor:
        raise ValueError("advisor.budget is required in a present advisor block")
    budget = advisor["budget"]
    if not isinstance(budget, dict):
        raise ValueError("advisor.budget must be a dict")
    unknown_b = set(budget) - _ADVISOR_BUDGET_KEYS
    if unknown_b:
        raise ValueError(f"advisor.budget: unknown key(s) {sorted(unknown_b)}")
    if "calls" not in budget or not _is_strict_int(budget["calls"]) or budget["calls"] < 0:
        raise ValueError("advisor.budget.calls must be an int >= 0")
    if "reserved" not in budget or not _is_strict_int(budget["reserved"]):
        raise ValueError("advisor.budget.reserved must be an int")
    if not (0 <= budget["reserved"] <= budget["calls"]):
        raise ValueError("advisor.budget.reserved must satisfy 0 <= reserved <= calls")

    # hooks — optional; each member validated when present.
    if "hooks" in advisor:
        hooks = advisor["hooks"]
        if not isinstance(hooks, dict):
            raise ValueError("advisor.hooks must be a dict")
        unknown_h = set(hooks) - _ADVISOR_HOOK_KEYS
        if unknown_h:
            raise ValueError(f"advisor.hooks: unknown key(s) {sorted(unknown_h)}")
        if "failThreshold" in hooks:
            ft = hooks["failThreshold"]
            if not _is_strict_int(ft) or ft < 1:
                raise ValueError("advisor.hooks.failThreshold must be an int >= 1")
        if "rerollTrigger" in hooks and not _is_strict_int(hooks["rerollTrigger"]):
            raise ValueError("advisor.hooks.rerollTrigger must be an int")
        if "fixLoopCeiling" in hooks and not isinstance(hooks["fixLoopCeiling"], bool):
            raise ValueError("advisor.hooks.fixLoopCeiling must be a bool")

    # phases — optional; documentation of the G-9 matrix, not a switch.
    if "phases" in advisor:
        phases = advisor["phases"]
        if not isinstance(phases, list):
            raise ValueError("advisor.phases must be a list")
        for ph in phases:
            if not isinstance(ph, str) or ph not in _ADVISOR_PHASES:
                raise ValueError(
                    f"advisor.phases members must be in {sorted(_ADVISOR_PHASES)}, "
                    f"got {ph!r}"
                )


# Exported name shared by the orchestrate load-guard and the gate (one validator —
# the resolve_budget/classify_premium_scope layers-must-agree precedent).
validate_advisor_block = _validate_advisor


def advisor_status(
    advisor: dict | None,
    anchor: str,
    *,
    family: str,
    mode: str,
    event: str | None = None,
) -> dict:
    """The advisor sibling legality gate (advisor-executor §3.2, S-16/S-21/S-24).

    Returns ``{"fires": bool, "reason": str, "rung": str | None}``.  ``rung`` is
    computed by :func:`advisor_rung_of` and travels in the status so the S-24
    conjunct (``rung == advisor_rung_of(anchor)``) is satisfied BY CONSTRUCTION:
    the conductor dispatches ``kata-advise`` at EXACTLY ``status["rung"]``
    (``None`` ⇒ OMIT the model parameter — arm (a) inherit-at-anchor, no premium
    machinery consulted; a short-name ⇒ its ``ID_MAP`` id — arm (b)) and never
    proposes its own rung.

    NO-FIRE reasons, checked in this exact precedence order (the ``premium_status``
    register):

      * ``"absent"``               — *advisor* is ``None`` (no block; frozen
                                     behaviour byte-for-byte, S-4)
      * *(raise)*                  — present-but-malformed ⇒ ``ValueError`` (D136 —
                                     not a reason)
      * ``"not-enabled"``          — ``enabled`` is not ``True`` (gates hook WIRING,
                                     S-26e)
      * ``"not-approved"``         — ``approved`` is not ``True`` (gates SPEND, S-16)
      * ``"mode-excluded"``        — ``mode`` ∉ {"advanced", "standard"} (essential
                                     and unknown modes fail closed, G-8)
      * ``"standard-not-granted"`` — ``mode == "standard"`` and
                                     ``grantedMode != "standard"`` (G-2 carve-out arm
                                     unsatisfied)
      * ``"no-event"``             — no *event* supplied
      * ``"unknown-event"``        — *event* ∉ :data:`ADVISOR_EVENTS`
      * ``"fires"``                — every conjunct holds

    A NO-FIRE on ANY conjunct ⇒ unadvised-proceed with a surfaced reason (board
    NOTE) — NEVER a consult-at-anchor-without-consent, never a block (S-21).

    A present-but-malformed block RAISES ``ValueError`` (fail-closed, D136).
    """
    if advisor is None:
        return {"fires": False, "reason": "absent", "rung": None}

    _validate_advisor(advisor)  # fail-closed: malformed ⇒ raise

    rung = advisor_rung_of(family, anchor)

    if advisor["enabled"] is not True:
        return {"fires": False, "reason": "not-enabled", "rung": rung}
    if advisor["approved"] is not True:
        return {"fires": False, "reason": "not-approved", "rung": rung}
    if mode not in _ADVISOR_GRANTED_MODES:
        return {"fires": False, "reason": "mode-excluded", "rung": rung}
    if mode == "standard" and advisor.get("grantedMode") != "standard":
        return {"fires": False, "reason": "standard-not-granted", "rung": rung}
    if event is None:
        return {"fires": False, "reason": "no-event", "rung": rung}
    if event not in ADVISOR_EVENTS:
        return {"fires": False, "reason": "unknown-event", "rung": rung}

    return {"fires": True, "reason": "fires", "rung": rung}


# ---------------------------------------------------------------------------
# resolve()
# ---------------------------------------------------------------------------

def resolve(
    skill: str,
    mode: str,
    anchor: str,
    *,
    family: str,
    coder_floor: str | None,
    premium: dict | None = None,
    event: str | None = None,
) -> str | None:
    """Resolve the concrete model ID for a (skill, mode) slot below *anchor*.

    Returns an explicit full model ID when the resolved ladder rung is strictly
    *below* the anchor rung, or ``None`` (OMIT → inherit the anchor) when:

    * the resolved rung equals the anchor rung (zero-step contract), or
    * any required lookup fails (inherit-on-doubt / BC guarantee).

    Parameters
    ----------
    skill       : skill short-name.  Unlisted skills default to work-class
                  ``"critical"`` (safest / highest-judgment path).
    mode        : ``"advanced"`` | ``"standard"`` | ``"essential"``
    anchor      : short model name within *family* (e.g. ``"opus"``).
    family      : model-family key (e.g. ``"anthropic"``).  The canonical sentinel
                  ``"auto"`` triggers ``family_of(anchor)`` derivation (FIX-1);
                  any other value is used as-is (BC).
    coder_floor : optional short name of the minimum rung for coding work (R1).
                  Pass ``None`` to disable (clamp to ladder index 0 only).
    premium     : optional ``kata.config.models.premium`` dict.  ``None`` (default)
                  ⇒ byte-for-byte frozen behaviour (no premium branch).  A
                  well-formed block fires the §3 gated amendment only when all four
                  conjuncts hold (see below); a malformed block RAISES ``ValueError``.
    event       : optional adaptive-event name (a :data:`ADAPTIVE_EVENTS` member),
                  supplied by the conductor at a covering dispatch site (AT-L5).
                  Only consulted when ``premium.scope`` is the EVENTS (dict) form;
                  IGNORED for the classes (list) form and when *premium* is absent
                  (``None`` default ⇒ byte-for-byte existing behaviour).

    Premium branch (§3 GATED AMENDMENT / D148 — additive, gated)
    ------------------------------------------------------------
    When *premium* is supplied and :func:`premium_status` reports ``fires`` (the
    three run-level conjuncts: ``approved`` ∧ ``mode == "advanced"`` ∧ offer EXACTLY
    one rung above the anchor) AND conjunct #2 holds, ``resolve()`` returns the
    EXPLICIT ``premium.offer`` id (never inherit, never a ladder walk).  Conjunct #2
    is TYPE-DISPATCHED on the scope form (Amendment #2 / AT-L15):

    * LIST scope (classes form, v0.2.1 byte-for-byte): the dispatched skill's
      work-class ∈ ``premium.scope`` (critical | coding only — economy is
      structurally excluded, R-9); *event* is ignored.
    * DICT scope (events form): ``event is not None AND event ∈ scope["events"]``
      (evaluated inside :func:`premium_status`) **AND work-class ∈ {critical,
      coding}** (the R-9 STRUCTURAL guard, applied below — adval F1); a
      class-based query against an events-form scope is simply NO-FIRE.  Budget SHAPE is validated at load;
      budget SPEND is the conductor's (kata_adaptive), never enforced here.

    ANY other case falls through to the frozen path below
    unchanged; ``premium_status`` carries the NO-FIRE reason for surfacing.  The
    returned offer is one rung ABOVE the anchor, so it can never be the anchor's own
    id (the zero-step / gated-top-rung protections are untouched).

    R1 coder-floor rule (coding work only)
    ---------------------------------------
    When *coder_floor* is given and ``floor_idx ≤ anchor_idx − 1``, the
    essential-coding rung is raised to *floor_idx* so that slow machines still
    get a capable coder.  The raise is capped at ``anchor_idx − 1`` (standard's
    rung) to uphold the invariant:

        essential-coding ≤ standard-coding ≤ anchor

    Zero-step contract
    ------------------
    The determinant for returning ``None`` is the resolved *index*, not the
    work-class.  Whenever ``resolved_idx == anchor_idx`` — including when a
    step of −1 or −2 is clamped back up to the anchor floor — the function
    returns ``None`` (never re-selects the anchor id).

    BC / inherit-on-doubt
    ---------------------
    Unknown family, anchor, or mode → ``None``.  Empty ladders (openai, gemini,
    generic placeholders) → ``None`` for every call, preserving today's behaviour
    byte-for-byte until those adapters are wired in.  ``family="auto"`` derives
    the family from *anchor* via ``family_of()``; if derivation fails, returns
    ``None`` (safe fallback, never a crash).
    """
    # Normalize: accept a full model id (e.g. "claude-opus-4-8") as anchor — maps it
    # to its short-name before any ladder lookup.  Short names and unknown ids pass through.
    anchor = _normalize_anchor(anchor)

    # §3 GATED AMENDMENT (D148) — premium branch.  premium=None ⇒ skip entirely
    # (byte-for-byte frozen behaviour).  A malformed block RAISES via premium_status
    # (fail-closed, D136).  Fires only when the three run-level conjuncts hold AND the
    # dispatched skill's work-class is in scope (critical | coding only; economy is
    # structurally excluded even if hand-listed in scope — R-9).
    if premium is not None:
        if premium_status(premium, anchor, family=family, mode=mode, event=event)["fires"]:
            if isinstance(premium["scope"], dict):
                # Events form (Amendment #2 / AT-L15): conjunct #2 (event ∈
                # scope.events) was already evaluated inside premium_status.
                # R-9 STRUCTURAL GUARD (adval F1 fold, AT-L14): economy work
                # NEVER runs the premium rung IN EITHER FORM — an event-tagged
                # economy dispatch (e.g. a bumped economy attempt) falls through
                # to the frozen path (its bump ceilings at the anchor). The
                # exclusion is code, not prose, exactly as config.md/preflight/
                # AT-L14 claim.
                work_class_e: str = SKILL_WORK_CLASS.get(skill, "critical")
                if work_class_e in ("critical", "coding"):
                    # EXPLICIT offer id — never inherit, never a ladder walk (§3.2).
                    return ID_MAP.get(_normalize_anchor(premium["offer"]))
            work_class_p: str = SKILL_WORK_CLASS.get(skill, "critical")
            if work_class_p in ("critical", "coding") and work_class_p in premium["scope"]:
                # EXPLICIT offer id — never inherit, never a ladder walk (§3.2).
                return ID_MAP.get(_normalize_anchor(premium["offer"]))
        # NO-FIRE (or out-of-scope) ⇒ fall through to the frozen path unchanged.

    # FIX-1: derive family from anchor when explicitly "auto"
    # NOTE: family="" and family=unknown-string preserve BC (unknown family → None);
    # only the canonical "auto" sentinel triggers family_of() derivation.
    if family == "auto":
        family = family_of(anchor) or ""

    # BC: unknown or empty family → None (absent config)
    ladder = FAMILY_LADDERS.get(family)
    if not ladder:
        return None

    # BC: unknown anchor → None
    if anchor not in ladder:
        return None

    anchor_idx: int = ladder.index(anchor)

    # Work-class: unknown skill → critical (default)
    work_class: str = SKILL_WORK_CLASS.get(skill, "critical")

    # Step count: per-family table (anthropic tiers economy one rung deeper);
    # absent family falls back to the generic default. Unknown mode → None.
    steps_table = _STEPS_BY_FAMILY.get(family, _STEPS_DEFAULT)
    steps = steps_table.get((mode, work_class))
    if steps is None:
        return None

    # Base walk (steps ≤ 0)
    resolved_idx: int = anchor_idx + steps

    # General clamp to ladder floor (index 0)
    resolved_idx = max(0, resolved_idx)

    # R1 coder-floor: raise coding rung when floor is reachable below anchor.
    # ONLY applies to essential/coding — advanced and standard coding must never
    # be touched by the coder-floor (advanced=step-0 → None; standard=step-1, no raise needed).
    if mode == "essential" and work_class == "coding" and coder_floor is not None:
        if coder_floor in ladder:
            floor_idx: int = ladder.index(coder_floor)
            if floor_idx <= anchor_idx - 1:
                # Raise to floor, then cap at standard-coding's rung (anchor_idx − 1)
                resolved_idx = min(max(resolved_idx, floor_idx), anchor_idx - 1)

    # FIX-2: delegate zero-step check + ID lookup to step_down
    # effective_steps = rungs descended after coder-floor adjustment (always ≥ 0)
    return step_down(anchor, anchor_idx - resolved_idx, family)


# ---------------------------------------------------------------------------
# fallback_chain()
# ---------------------------------------------------------------------------

def fallback_chain(id: str, family: str) -> list[str | None]:
    """Return a ≤2-step fallback chain below *id* within *family*.

    The chain lists up to two consecutive step-downs from *id* (one rung per
    step), then terminates with ``None`` (OMIT).  The input *id* itself never
    appears in the result.  If *id* is already the family floor (no step-downs
    exist), the chain is ``[None]``.

    Parameters
    ----------
    id     : full model ID (e.g. ``"claude-opus-4-8"``).
    family : model-family key (e.g. ``"anthropic"``).

    Example
    -------
    >>> fallback_chain("claude-opus-4-8", "anthropic")
    ['claude-sonnet-5', 'claude-haiku-4-5-20251001', None]
    """
    ladder = FAMILY_LADDERS.get(family)
    if not ladder:
        return [None]

    # Reverse-lookup: full model ID → ladder index
    start_idx: int | None = None
    for i, short in enumerate(ladder):
        if ID_MAP.get(short) == id:
            start_idx = i
            break

    if start_idx is None:
        return [None]

    result: list[str | None] = []
    for step in range(1, 3):          # 1 rung below, then 2 rungs below
        new_idx = start_idx - step
        if new_idx < 0:
            break
        short = ladder[new_idx]
        full_id = ID_MAP.get(short)
        if full_id is not None:
            result.append(full_id)

    result.append(None)
    return result
