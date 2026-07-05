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
family_of(anchor) -> str | None
step_down(anchor, steps, family) -> str | None
resolve(skill, mode, anchor, *, family, coder_floor, premium=None) -> str | None
premium_status(premium, anchor, *, family, mode) -> {"fires": bool, "reason": str}
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
# Premium gate (§3 GATED AMENDMENT / D148) — fail-closed conjunct evaluation
# ---------------------------------------------------------------------------

def _validate_premium(premium: dict) -> None:
    """Fail-closed shape guard for a ``models.premium`` block (D136).

    RAISES ``ValueError`` when *premium* is present-but-malformed — a broken
    approval is never silently ignored.  Validates ONLY the three fields the
    resolve-time decision reads: ``offer`` (str), ``approved`` (bool), ``scope``
    (list of str).  ``grantedMode`` is the bootstrap mode-lapse arm (§3.3, a P2
    prose consumer) and is NOT read here, so it is not required at resolve time.

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
    scope = premium.get("scope")
    if not isinstance(scope, list) or not all(isinstance(s, str) for s in scope):
        raise ValueError("models.premium.scope missing or not a list[str]")


def premium_status(
    premium: dict | None,
    anchor: str,
    *,
    family: str,
    mode: str,
) -> dict:
    """Report whether the premium gate FIRES at this anchor/mode, and why not.

    Returns ``{"fires": bool, "reason": str}`` for NO-FIRE surfacing / audit (the
    board-NOTE prose consumer is P2).  This evaluates the three *run-level*
    conjuncts that are independent of the dispatched skill — ``approved``,
    ``mode == "advanced"``, and the offer↔anchor relationship (offer EXACTLY one
    rung strictly above the anchor).  The fourth conjunct — ``work-class ∈ scope``
    — is per-skill and is applied by :func:`resolve`.

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
      * ``"fires"``            — all three run-level conjuncts hold

    A present-but-malformed block RAISES ``ValueError`` (fail-closed, D136).
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
    return {"fires": True, "reason": "fires"}


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

    Premium branch (§3 GATED AMENDMENT / D148 — additive, gated)
    ------------------------------------------------------------
    When *premium* is supplied and :func:`premium_status` reports ``fires`` (the
    three run-level conjuncts: ``approved`` ∧ ``mode == "advanced"`` ∧ offer EXACTLY
    one rung above the anchor) AND the dispatched skill's work-class is in
    ``premium.scope`` (critical | coding only — economy is structurally excluded,
    R-9), ``resolve()`` returns the EXPLICIT ``premium.offer`` id (never inherit,
    never a ladder walk).  ANY other case falls through to the frozen path below
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
        if premium_status(premium, anchor, family=family, mode=mode)["fires"]:
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
