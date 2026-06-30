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
resolve(skill, mode, anchor, *, family, coder_floor) -> str | None
fallback_chain(id, family) -> list[str | None]
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
    "sonnet": "claude-sonnet-4-6",
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
# Step-count table — (mode, work_class) → steps (≤ 0)
# Negative value = rungs to descend from the anchor index.
# ---------------------------------------------------------------------------
#
# Table:
#              critical  coding  economy
#   advanced      0        0       0
#   standard      0       -1      -1
#   essential    -1       -2*     -1
#
# * coding/essential applies R1 coder-floor on top (see resolve()).

_STEPS: dict[tuple[str, str], int] = {
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
# resolve()
# ---------------------------------------------------------------------------

def resolve(
    skill: str,
    mode: str,
    anchor: str,
    *,
    family: str,
    coder_floor: str | None,
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

    # Step count: unknown mode → None
    steps = _STEPS.get((mode, work_class))
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
    ['claude-sonnet-4-6', 'claude-haiku-4-5-20251001', None]
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
