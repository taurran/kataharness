"""test_kata_models.py — TDD suite for kata_models resolver.

Tests are organised into five groups matching the BUILD CONTRACT:
  1. Monotonicity  — essential-coding ≤ standard-coding ≤ anchor at every anchor
  2. Per-cell table — each (anchor, mode, work_class) cell resolves correctly
  3. Floor-clamp edge — haiku anchor all-None; clamp-to-anchor → None not floor id;
                        essential-critical at opus → sonnet id (via module constant)
  4. BC / inherit-on-doubt — unknown family/anchor/skill/config → None
  5. fallback_chain — ≤2 step-downs then None; anchor never in result

Run:
    cd C:/Dev/Projects/KataHarness/tools
    uv run pytest tests/test_kata_models.py -v
"""
from __future__ import annotations

import pytest

import kata_models as km

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ANTHROPIC = "anthropic"
ANCHORS: list[str] = km.FAMILY_LADDERS["anthropic"]  # haiku..mythos low→high
MODES: list[str] = ["advanced", "standard", "essential"]

# Representative skills per work-class
_CRITICAL_SKILL = "kata-grill-essential"
_CODING_SKILL   = "kata-tdd"
_ECONOMY_SKILL  = "kata-report"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _short_to_idx(short: str) -> int:
    """Index of short name in anthropic ladder."""
    return ANCHORS.index(short)


def _id_to_idx(full_id: str) -> int:
    """Reverse-map full model ID → ladder index.  Fails loudly for unknowns."""
    for i, short in enumerate(ANCHORS):
        if km.ID_MAP.get(short) == full_id:
            return i
    raise ValueError(f"Unknown full model id: {full_id!r}")


def _resolve_idx(skill: str, mode: str, anchor: str) -> int:
    """Resolve then return ladder index; None resolves to anchor_idx."""
    anchor_idx = _short_to_idx(anchor)
    result = km.resolve(skill, mode, anchor, family=ANTHROPIC, coder_floor=None)
    return anchor_idx if result is None else _id_to_idx(result)


# ===========================================================================
# 1. Monotonicity
# ===========================================================================

class TestMonotonicity:
    """essential-coding ≤ standard-coding ≤ anchor at every anchor."""

    @pytest.mark.parametrize("anchor", ANCHORS)
    def test_coding_monotonicity(self, anchor: str) -> None:
        anchor_idx      = _short_to_idx(anchor)
        std_coding_idx  = _resolve_idx(_CODING_SKILL, "standard",  anchor)
        ess_coding_idx  = _resolve_idx(_CODING_SKILL, "essential", anchor)

        assert ess_coding_idx <= std_coding_idx, (
            f"anchor={anchor}: essential-coding ({ess_coding_idx}) "
            f"> standard-coding ({std_coding_idx}) — invariant violated"
        )
        assert std_coding_idx <= anchor_idx, (
            f"anchor={anchor}: standard-coding ({std_coding_idx}) "
            f"> anchor ({anchor_idx}) — invariant violated"
        )

    def test_fable_essential_coding_lands_sonnet(self) -> None:
        result = km.resolve(_CODING_SKILL, "essential", "fable",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"], (
            f"fable/essential-coding: expected {km.ID_MAP['sonnet']!r}, got {result!r}"
        )

    @pytest.mark.parametrize("anchor", ["opus", "sonnet", "haiku"])
    def test_no_inversion_below_fable(self, anchor: str) -> None:
        """opus, sonnet, haiku anchors collapse cleanly; never invert."""
        std_idx = _resolve_idx(_CODING_SKILL, "standard",  anchor)
        ess_idx = _resolve_idx(_CODING_SKILL, "essential", anchor)
        assert ess_idx <= std_idx, (
            f"anchor={anchor}: ess-coding ({ess_idx}) > std-coding ({std_idx}) — inversion"
        )


# ===========================================================================
# 2. Per-cell mode table
# ===========================================================================

class TestPerCellModeTable:
    """Verify explicit None / ID per (anchor, mode, work_class)."""

    # ---- advanced: critical + coding are 0-step (None); economy steps −1 (anthropic) ----

    @pytest.mark.parametrize("anchor", ANCHORS)
    @pytest.mark.parametrize("skill", [_CRITICAL_SKILL, _CODING_SKILL])
    def test_advanced_critical_coding_none(self, anchor: str, skill: str) -> None:
        result = km.resolve(skill, "advanced", anchor, family=ANTHROPIC, coder_floor=None)
        assert result is None, (
            f"advanced/{anchor}/{skill}: expected None (zero-step), got {result!r}"
        )

    def test_advanced_economy_fable_returns_opus(self) -> None:
        """anthropic advanced/economy steps −1: fable → opus (advanced keeps high+mid on Fable)."""
        result = km.resolve(_ECONOMY_SKILL, "advanced", "fable",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["opus"]

    def test_advanced_economy_haiku_none(self) -> None:
        """anthropic advanced/economy at the floor clamps to anchor → None."""
        result = km.resolve(_ECONOMY_SKILL, "advanced", "haiku",
                            family=ANTHROPIC, coder_floor=None)
        assert result is None

    # ---- standard-critical: always None (0 steps) ----

    @pytest.mark.parametrize("anchor", ANCHORS)
    def test_standard_critical_always_none(self, anchor: str) -> None:
        result = km.resolve(_CRITICAL_SKILL, "standard", anchor,
                            family=ANTHROPIC, coder_floor=None)
        assert result is None, f"standard/critical/{anchor}: expected None, got {result!r}"

    # ---- standard-coding (step −1) ----

    def test_standard_coding_haiku_none(self) -> None:
        assert km.resolve(_CODING_SKILL, "standard", "haiku",
                          family=ANTHROPIC, coder_floor=None) is None

    def test_standard_coding_sonnet_returns_haiku(self) -> None:
        result = km.resolve(_CODING_SKILL, "standard", "sonnet",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["haiku"]

    def test_standard_coding_opus_returns_sonnet(self) -> None:
        result = km.resolve(_CODING_SKILL, "standard", "opus",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"]

    def test_standard_coding_fable_returns_opus(self) -> None:
        result = km.resolve(_CODING_SKILL, "standard", "fable",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["opus"]

    # ---- standard-economy (anthropic step −2) ----

    def test_standard_economy_haiku_none(self) -> None:
        assert km.resolve(_ECONOMY_SKILL, "standard", "haiku",
                          family=ANTHROPIC, coder_floor=None) is None

    def test_standard_economy_sonnet_returns_haiku(self) -> None:
        result = km.resolve(_ECONOMY_SKILL, "standard", "sonnet",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["haiku"]

    def test_standard_economy_fable_returns_sonnet(self) -> None:
        # anthropic standard/economy = −2: fable (idx3) → sonnet (idx1)
        result = km.resolve(_ECONOMY_SKILL, "standard", "fable",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"]

    # ---- essential-critical (step −1) ----

    def test_essential_critical_haiku_none(self) -> None:
        assert km.resolve(_CRITICAL_SKILL, "essential", "haiku",
                          family=ANTHROPIC, coder_floor=None) is None

    def test_essential_critical_sonnet_returns_haiku(self) -> None:
        result = km.resolve(_CRITICAL_SKILL, "essential", "sonnet",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["haiku"]

    def test_essential_critical_opus_returns_sonnet(self) -> None:
        result = km.resolve(_CRITICAL_SKILL, "essential", "opus",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"]

    def test_essential_critical_fable_returns_opus(self) -> None:
        result = km.resolve(_CRITICAL_SKILL, "essential", "fable",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["opus"]

    # ---- essential-economy (anthropic step −2) ----

    def test_essential_economy_haiku_none(self) -> None:
        assert km.resolve(_ECONOMY_SKILL, "essential", "haiku",
                          family=ANTHROPIC, coder_floor=None) is None

    def test_essential_economy_sonnet_returns_haiku(self) -> None:
        result = km.resolve(_ECONOMY_SKILL, "essential", "sonnet",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["haiku"]

    def test_essential_economy_fable_returns_sonnet(self) -> None:
        # anthropic essential/economy = −2: fable (idx3) → sonnet (idx1)
        result = km.resolve(_ECONOMY_SKILL, "essential", "fable",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"]

    # ---- essential-coding (step −2, R1 floor) ----

    def test_essential_coding_haiku_none(self) -> None:
        assert km.resolve(_CODING_SKILL, "essential", "haiku",
                          family=ANTHROPIC, coder_floor=None) is None

    def test_essential_coding_sonnet_returns_haiku(self) -> None:
        # 1 - 2 = -1 → clamp to 0 (haiku); 0 < 1 → explicit
        result = km.resolve(_CODING_SKILL, "essential", "sonnet",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["haiku"]

    def test_essential_coding_opus_returns_haiku(self) -> None:
        # 2 - 2 = 0 (haiku); 0 < 2 → explicit
        result = km.resolve(_CODING_SKILL, "essential", "opus",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["haiku"]

    def test_essential_coding_fable_returns_sonnet(self) -> None:
        # 3 - 2 = 1 (sonnet); 1 < 3 → explicit
        result = km.resolve(_CODING_SKILL, "essential", "fable",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"]

    # ---- unknown skill defaults to critical (BC) ----

    def test_unknown_skill_defaults_critical_standard_none(self) -> None:
        # critical + standard = 0 steps → None
        result = km.resolve("completely-unknown-skill-xyz", "standard", "opus",
                            family=ANTHROPIC, coder_floor=None)
        assert result is None

    def test_unknown_skill_defaults_critical_essential_explicit(self) -> None:
        # critical + essential = −1 → opus−1 = sonnet
        result = km.resolve("completely-unknown-skill-xyz", "essential", "opus",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"]


# ===========================================================================
# 3. Floor-clamp → None edge
# ===========================================================================

class TestFloorClampEdge:
    """haiku-anchor all-None; clamp-to-anchor → None; essential-critical/opus → sonnet."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("skill", [_CRITICAL_SKILL, _CODING_SKILL, _ECONOMY_SKILL])
    def test_haiku_anchor_every_cell_none(self, mode: str, skill: str) -> None:
        result = km.resolve(skill, mode, "haiku", family=ANTHROPIC, coder_floor=None)
        assert result is None, (
            f"haiku/{mode}/{skill}: expected None (all steps clamp to anchor), got {result!r}"
        )

    def test_haiku_anchor_with_coder_floor_still_none(self) -> None:
        """Coder floor must not override the zero-step contract at haiku anchor."""
        result = km.resolve(_CODING_SKILL, "essential", "haiku",
                            family=ANTHROPIC, coder_floor="sonnet")
        assert result is None, (
            "haiku/essential-coding with coder_floor=sonnet: "
            f"expected None, got {result!r}"
        )

    @pytest.mark.parametrize("anchor", ANCHORS)
    def test_advanced_coding_coder_floor_never_applied(self, anchor: str) -> None:
        """R1 coder-floor must NOT fire for advanced/coding — step is 0, result must always be None.

        This is the regression guard for the contract-violation bug where the coder-floor
        block fired for ALL coding cells (not just essential), incorrectly stepping down
        advanced/coding by one rung when coder_floor was provided.
        """
        result = km.resolve(_CODING_SKILL, "advanced", anchor,
                            family=ANTHROPIC, coder_floor="sonnet")
        assert result is None, (
            f"advanced/coding/{anchor} with coder_floor=sonnet: "
            f"expected None (zero-step; coder-floor must not apply to advanced mode), "
            f"got {result!r}"
        )

    def test_sonnet_with_high_coder_floor_not_applied(self) -> None:
        """floor_idx > anchor_idx−1 → R1 NOT applied → natural result returned."""
        # sonnet anchor, essential-coding, coder_floor=sonnet (floor_idx=1 > anchor−1=0)
        # raw: 1−2=−1 → clamp to 0 (haiku); not raised by floor; 0 < 1 → haiku ID
        result = km.resolve(_CODING_SKILL, "essential", "sonnet",
                            family=ANTHROPIC, coder_floor="sonnet")
        assert result == km.ID_MAP["haiku"], (
            "sonnet/essential-coding: floor=sonnet is above anchor−1, "
            f"expected haiku id, got {result!r}"
        )

    def test_essential_critical_opus_returns_sonnet_via_module_constant(self) -> None:
        """Canonical check: references km.ID_MAP, not a hardcoded string."""
        result = km.resolve(_CRITICAL_SKILL, "essential", "opus",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"]

    def test_r1_floor_raises_coding_rung(self) -> None:
        """When floor_idx ≤ anchor_idx−1, essential-coding is raised to the floor."""
        # opus anchor (idx=2), essential-coding: raw = 2−2=0 (haiku)
        # coder_floor=sonnet (idx=1); floor_idx (1) ≤ anchor_idx−1 (1) → YES
        # max(0, 1) = 1 (sonnet), min(1, 1) = 1 → sonnet ID
        result = km.resolve(_CODING_SKILL, "essential", "opus",
                            family=ANTHROPIC, coder_floor="sonnet")
        assert result == km.ID_MAP["sonnet"], (
            f"opus/essential-coding with coder_floor=sonnet: expected sonnet, got {result!r}"
        )

    def test_r1_floor_never_exceeds_standard_coding_rung(self) -> None:
        """After R1 raise, essential-coding must not exceed standard-coding."""
        for anchor in ANCHORS:
            anchor_idx = _short_to_idx(anchor)
            if anchor_idx < 2:
                continue  # not enough headroom to test meaningfully
            # Use a floor that is at anchor−1 (max legal floor)
            floor_short = ANCHORS[anchor_idx - 1]
            std_idx = _resolve_idx(_CODING_SKILL, "standard", anchor)
            ess_result = km.resolve(_CODING_SKILL, "essential", anchor,
                                    family=ANTHROPIC, coder_floor=floor_short)
            ess_idx = anchor_idx if ess_result is None else _id_to_idx(ess_result)
            assert ess_idx <= std_idx, (
                f"anchor={anchor}: ess-coding ({ess_idx}) > std-coding ({std_idx}) "
                "after R1 floor — invariant violated"
            )


# ===========================================================================
# 4. BC / inherit-on-doubt
# ===========================================================================

class TestInheritOnDoubt:
    """resolve() returns None for every absent-config scenario."""

    def test_unknown_family_returns_none(self) -> None:
        result = km.resolve(_CODING_SKILL, "standard", "sonnet",
                            family="unknown_family", coder_floor=None)
        assert result is None

    def test_empty_string_family_returns_none(self) -> None:
        result = km.resolve(_CODING_SKILL, "standard", "sonnet",
                            family="", coder_floor=None)
        assert result is None

    def test_unknown_anchor_returns_none(self) -> None:
        result = km.resolve(_CODING_SKILL, "standard", "gpt-4o",
                            family=ANTHROPIC, coder_floor=None)
        assert result is None

    def test_openai_empty_ladder_returns_none(self) -> None:
        """openai / gemini / generic families are shape-only placeholders → always None."""
        for family in ("openai", "gemini", "generic"):
            result = km.resolve(_CODING_SKILL, "standard", "sonnet",
                                family=family, coder_floor=None)
            assert result is None, f"{family}/standard/sonnet: expected None, got {result!r}"

    def test_unknown_mode_returns_none(self) -> None:
        result = km.resolve(_CODING_SKILL, "ultra", "sonnet",
                            family=ANTHROPIC, coder_floor=None)
        assert result is None

    def test_bc_structural_guarantee(self) -> None:
        """Absent config ⇒ None everywhere — every (mode, anchor) pair for openai."""
        for mode in MODES:
            for anchor in ("mini", "gpt-5", "sonnet"):  # all unknown for openai
                result = km.resolve(_CODING_SKILL, mode, anchor,
                                    family="openai", coder_floor=None)
                assert result is None


# ===========================================================================
# 5. fallback_chain
# ===========================================================================

class TestFallbackChain:
    """fallback_chain: ≤2 step-downs then None; anchor id never in result."""

    def test_opus_chain_two_stepdowns(self) -> None:
        chain = km.fallback_chain(km.ID_MAP["opus"], ANTHROPIC)
        assert chain[-1] is None
        assert km.ID_MAP["opus"] not in chain, "anchor id must not appear in fallback chain"
        non_none = [x for x in chain if x is not None]
        assert len(non_none) == 2
        assert non_none[0] == km.ID_MAP["sonnet"]
        assert non_none[1] == km.ID_MAP["haiku"]

    def test_sonnet_chain_one_stepdown(self) -> None:
        chain = km.fallback_chain(km.ID_MAP["sonnet"], ANTHROPIC)
        assert chain[-1] is None
        assert km.ID_MAP["sonnet"] not in chain
        non_none = [x for x in chain if x is not None]
        assert len(non_none) == 1
        assert non_none[0] == km.ID_MAP["haiku"]

    def test_haiku_floor_just_none(self) -> None:
        chain = km.fallback_chain(km.ID_MAP["haiku"], ANTHROPIC)
        assert chain == [None], f"haiku floor: expected [None], got {chain!r}"

    def test_fable_chain_two_stepdowns(self) -> None:
        chain = km.fallback_chain(km.ID_MAP["fable"], ANTHROPIC)
        assert chain[-1] is None
        assert km.ID_MAP["fable"] not in chain
        non_none = [x for x in chain if x is not None]
        assert len(non_none) == 2
        assert non_none[0] == km.ID_MAP["opus"]
        assert non_none[1] == km.ID_MAP["sonnet"]

    def test_mythos_chain_capped_at_two(self) -> None:
        chain = km.fallback_chain(km.ID_MAP["mythos"], ANTHROPIC)
        assert chain[-1] is None
        assert km.ID_MAP["mythos"] not in chain
        non_none = [x for x in chain if x is not None]
        assert len(non_none) <= 2

    def test_chain_terminates_with_none(self) -> None:
        """Every chain, for every anchor, ends with None."""
        for short in ANCHORS:
            chain = km.fallback_chain(km.ID_MAP[short], ANTHROPIC)
            assert chain[-1] is None, f"{short}: chain does not end with None: {chain!r}"

    def test_anchor_never_in_chain(self) -> None:
        """Input id must never appear in its own fallback chain."""
        for short in ANCHORS:
            chain = km.fallback_chain(km.ID_MAP[short], ANTHROPIC)
            assert km.ID_MAP[short] not in chain, (
                f"{short}: anchor id {km.ID_MAP[short]!r} appears in chain {chain!r}"
            )

    def test_unknown_family_returns_none_list(self) -> None:
        chain = km.fallback_chain(km.ID_MAP["opus"], "unknown")
        assert chain == [None]

    def test_unknown_id_returns_none_list(self) -> None:
        chain = km.fallback_chain("gpt-99-mega", ANTHROPIC)
        assert chain == [None]


# ===========================================================================
# 6. family="auto" derivation (FIX-1 activation)
# ===========================================================================

class TestAutoFamilyDerivation:
    """FIX-1: family='auto' activates resolve() via family_of(anchor) derivation.

    The canonical config block ``{anchor:"session", family:"auto", coderFloor:"sonnet"}``
    was a dormant no-op because ``FAMILY_LADDERS.get("auto")`` is ``None``.
    These tests prove the feature is now live: with ``family="auto"``, resolve()
    derives the family from the anchor and returns an explicit (non-None) ID for
    below-anchor cells.
    """

    def test_auto_family_fable_essential_coding_activates(self) -> None:
        """Canonical block activation: anchor='fable', family='auto', coder_floor='sonnet'.

        essential-coding with fable anchor (idx=3) steps down 2 rungs → idx=1 (sonnet).
        The coder_floor='sonnet' (idx=1) applies: min(max(1,1),2)=1 — still sonnet.
        family='auto' must auto-derive 'anthropic' from anchor='fable' and return
        the sonnet ID, proving the canonical block is no longer a dormant no-op.
        """
        result = km.resolve(_CODING_SKILL, "essential", "fable",
                            family="auto", coder_floor="sonnet")
        assert result is not None, (
            "family='auto' with anchor='fable' must activate (non-None) for essential-coding"
        )
        assert result == km.ID_MAP["sonnet"], (
            f"fable/essential-coding/coder_floor=sonnet: expected sonnet id, got {result!r}"
        )

    def test_auto_family_opus_essential_critical_activates(self) -> None:
        """family='auto' with anchor='opus' resolves for essential-critical (below anchor).

        essential-critical steps down 1 rung from opus (idx=2) → idx=1 (sonnet).
        family='auto' must derive 'anthropic' and return the sonnet ID.
        """
        result = km.resolve(_CRITICAL_SKILL, "essential", "opus",
                            family="auto", coder_floor=None)
        assert result is not None, (
            "family='auto' with anchor='opus' must activate for essential-critical"
        )
        assert result == km.ID_MAP["sonnet"], (
            f"opus/essential-critical/auto: expected sonnet id, got {result!r}"
        )

    def test_auto_family_unknown_anchor_returns_none(self) -> None:
        """family='auto' with an unknown anchor (not in any ladder) → None (BC / inherit-on-doubt)."""
        result = km.resolve(_CODING_SKILL, "essential", "gpt-99",
                            family="auto", coder_floor=None)
        assert result is None, (
            f"family='auto' with unknown anchor must return None; got {result!r}"
        )

    def test_family_of_returns_correct_family_for_anthropic_anchors(self) -> None:
        """family_of() returns 'anthropic' for every anchor in the Anthropic ladder."""
        for short in ANCHORS:
            fam = km.family_of(short)
            assert fam == ANTHROPIC, (
                f"family_of({short!r}) expected 'anthropic', got {fam!r}"
            )

    def test_family_of_returns_none_for_unknown_anchor(self) -> None:
        """family_of() returns None for an anchor not present in any ladder."""
        assert km.family_of("gpt-99") is None
        assert km.family_of("") is None


# ===========================================================================
# 7. Work-class map coverage (R5)
# ===========================================================================

class TestWorkClassMapCoverage:
    """R5: every skill discovered by load_skills() must be present in SKILL_WORK_CLASS.

    Uses the same runtime mechanism as the validator (load_skills() from validate_skills)
    so the assertion set tracks the actual repo as skills are added or removed.
    Count-agnostic: no hardcoded total; the set is derived dynamically.
    """

    def test_all_loaded_skills_in_work_class_map(self) -> None:
        """Every skill enumerated by load_skills() — skills/ PLUS all modules/ skills —
        must have an explicit entry in SKILL_WORK_CLASS."""
        from validate_skills import load_skills  # same mechanism as the runtime validator

        skills = load_skills()
        assert skills, "load_skills() returned no skills — check repo structure"

        missing = [s.name for s in skills if s.name not in km.SKILL_WORK_CLASS]
        assert not missing, (
            f"{len(missing)} skill(s) missing from SKILL_WORK_CLASS: {missing!r}\n"
            f"Total loaded: {len(skills)}"
        )

    def test_spot_check_critical_inherits_at_standard(self) -> None:
        """Critical class / standard mode: zero-step → None (inherit by omission)."""
        result = km.resolve("kata-evaluate", "standard", "opus",
                            family=ANTHROPIC, coder_floor=None)
        assert result is None, (
            f"critical/standard/opus: expected None (zero-step inherit), got {result!r}"
        )

    def test_spot_check_critical_steps_down_at_essential(self) -> None:
        """Critical class / essential mode: −1 step → explicit id strictly below anchor."""
        result = km.resolve("kata-evaluate", "essential", "opus",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"], (
            f"critical/essential/opus: expected sonnet id, got {result!r}"
        )

    def test_spot_check_coding_steps_down_at_standard(self) -> None:
        """Coding class / standard mode: −1 step → explicit id strictly below anchor."""
        result = km.resolve("kata-tdd", "standard", "opus",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"], (
            f"coding/standard/opus: expected sonnet id, got {result!r}"
        )

    def test_spot_check_economy_steps_down_at_standard(self) -> None:
        """Economy class / standard mode (anthropic −2): opus → haiku (two rungs below)."""
        result = km.resolve("kata-report", "standard", "opus",
                            family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["haiku"], (
            f"economy/standard/opus: expected haiku id, got {result!r}"
        )


# ===========================================================================
# 8. Full-model-id anchor normalization (MAJOR-1 fix)
# ===========================================================================

class TestFullIdAnchorNormalization:
    """MAJOR-1 fix: full model ids are accepted as anchors and normalized to short-names.

    A full id written by kata-initiate/kata-bootstrap (e.g. ``"claude-opus-4-8"``) must
    activate model-tiering identically to its short-name equivalent (``"opus"``).  Before
    this fix, ``family_of("claude-opus-4-8")`` returned ``None`` and all tiering silently
    no-op'd on the documented full-id path.
    """

    # ---- family_of: every known full id → "anthropic" ----

    @pytest.mark.parametrize("short_name", ["haiku", "sonnet", "opus", "fable", "mythos"])
    def test_family_of_full_id_returns_anthropic(self, short_name: str) -> None:
        """family_of(full_id) → 'anthropic' for every known Anthropic full model id."""
        full_id = km.ID_MAP[short_name]
        result = km.family_of(full_id)
        assert result == ANTHROPIC, (
            f"family_of({full_id!r}) expected 'anthropic', got {result!r}"
        )

    # ---- resolve: full-id anchor activates tiering (non-None for below-anchor cells) ----

    def test_resolve_full_id_opus_standard_coding_activates_tiering(self) -> None:
        """resolve() with a full-id anchor (claude-opus-4-8) activates tiering — returns sonnet id."""
        full_id_opus = km.ID_MAP["opus"]
        result = km.resolve(
            _CODING_SKILL, "standard", full_id_opus,
            family="auto", coder_floor="sonnet",
        )
        assert result == km.ID_MAP["sonnet"], (
            f"resolve(kata-tdd, standard, {full_id_opus!r}, family=auto, coder_floor=sonnet): "
            f"expected {km.ID_MAP['sonnet']!r}, got {result!r}"
        )

    # ---- equivalence: full-id anchor and short-name anchor produce identical results ----

    @pytest.mark.parametrize("short_name", ["haiku", "sonnet", "opus", "fable"])
    def test_full_id_and_short_name_produce_identical_results(self, short_name: str) -> None:
        """Full-id anchor and its short-name equivalent produce identical resolve() results
        across all modes and work-classes (equivalence proof)."""
        full_id = km.ID_MAP[short_name]
        for mode in MODES:
            for skill in [_CRITICAL_SKILL, _CODING_SKILL, _ECONOMY_SKILL]:
                result_short = km.resolve(
                    skill, mode, short_name, family="auto", coder_floor="sonnet"
                )
                result_full = km.resolve(
                    skill, mode, full_id, family="auto", coder_floor="sonnet"
                )
                assert result_short == result_full, (
                    f"Equivalence failure: anchor={short_name!r} vs {full_id!r} "
                    f"for (skill={skill!r}, mode={mode!r}): "
                    f"{result_short!r} != {result_full!r}"
                )

    # ---- BC: unknown full id → None everywhere ----

    def test_unknown_full_id_family_of_returns_none(self) -> None:
        """Unknown full id 'claude-zzz-9' → family_of returns None (BC preserved)."""
        assert km.family_of("claude-zzz-9") is None

    @pytest.mark.parametrize("mode", MODES)
    def test_unknown_full_id_resolve_returns_none(self, mode: str) -> None:
        """Unknown full id 'claude-zzz-9' → resolve returns None for every mode (BC preserved)."""
        result = km.resolve(
            _CODING_SKILL, mode, "claude-zzz-9",
            family="auto", coder_floor="sonnet",
        )
        assert result is None, (
            f"resolve(kata-tdd, {mode!r}, 'claude-zzz-9'): expected None, got {result!r}"
        )

    # ---- BC: existing short-name anchors are unchanged ----

    def test_existing_short_name_anchors_still_work(self) -> None:
        """Short-name anchors are not affected by normalization — regression guard."""
        result = km.resolve("kata-tdd", "standard", "opus", family=ANTHROPIC, coder_floor=None)
        assert result == km.ID_MAP["sonnet"], (
            f"Short-name anchor 'opus' regressed: expected {km.ID_MAP['sonnet']!r}, got {result!r}"
        )


# ===========================================================================
# 9. Per-family step tables (Anthropic economy-deepened; default preserved)
# ===========================================================================

class TestPerFamilyStepTables:
    """Anthropic uses the economy-deepened matrix; every other family keeps the
    generic default. critical + coding are identical across both tables — only
    the economy column differs (one rung deeper for Anthropic)."""

    def test_anthropic_economy_column_is_deepened(self) -> None:
        assert km._STEPS_ANTHROPIC[("advanced", "economy")] == -1
        assert km._STEPS_ANTHROPIC[("standard", "economy")] == -2
        assert km._STEPS_ANTHROPIC[("essential", "economy")] == -2

    def test_default_table_unchanged(self) -> None:
        """Non-Anthropic families keep the original layout (0 / −1 / −1 economy)."""
        assert km._STEPS_DEFAULT[("advanced", "economy")] == 0
        assert km._STEPS_DEFAULT[("standard", "economy")] == -1
        assert km._STEPS_DEFAULT[("essential", "economy")] == -1

    def test_critical_and_coding_identical_across_tables(self) -> None:
        for mode in MODES:
            for wc in ("critical", "coding"):
                assert km._STEPS_ANTHROPIC[(mode, wc)] == km._STEPS_DEFAULT[(mode, wc)], (
                    f"({mode},{wc}) must match across tables"
                )

    def test_anthropic_family_selects_anthropic_table(self) -> None:
        assert km._STEPS_BY_FAMILY.get("anthropic") is km._STEPS_ANTHROPIC

    def test_absent_family_falls_back_to_default(self) -> None:
        assert km._STEPS_BY_FAMILY.get("openai", km._STEPS_DEFAULT) is km._STEPS_DEFAULT


# ===========================================================================
# 10. Sonnet 5 id freshness
# ===========================================================================

class TestSonnetFiveId:
    """The sonnet rung maps to Sonnet 5 (re-release), not the stale 4-6 id."""

    def test_sonnet_id_is_sonnet_5(self) -> None:
        assert km.ID_MAP["sonnet"] == "claude-sonnet-5"

    def test_fable_essential_coding_lands_sonnet_5(self) -> None:
        result = km.resolve(_CODING_SKILL, "essential", "fable",
                            family=ANTHROPIC, coder_floor=None)
        assert result == "claude-sonnet-5"


# ===========================================================================
# 11. M4-L7 never-anchor pin — kata-inline-eval (D131)
# ===========================================================================

class TestInlineEvalNeverAnchor:
    """M4-L7 as amended: the inline evaluator runs STRICTLY BELOW the anchor, NEVER at anchor.

    kata-inline-eval registers as economy in SKILL_WORK_CLASS (D131). For every
    (mode, anchor) cell in the Anthropic family, resolve() must return either None
    (OMIT — the orchestrator then degrades M4 to telemetry, never inheriting the
    anchor) or an id STRICTLY BELOW the anchor rung. It must NEVER return the
    anchor's own id — that would run the frequent, scoped inline eval at anchor
    tier, the overhead spiral M4-L7 exists to prevent.

    Pinned against regression: the zero-step contract guarantees this structurally
    today, but a future step-table or resolver change must not silently break it.
    """

    @pytest.mark.parametrize("anchor", ANCHORS)
    @pytest.mark.parametrize("mode", MODES)
    def test_inline_eval_never_resolves_to_anchor(self, mode: str, anchor: str) -> None:
        result = km.resolve("kata-inline-eval", mode, anchor,
                            family=ANTHROPIC, coder_floor=None)
        anchor_id = km.ID_MAP[anchor]
        # Never the anchor's own id.
        assert result != anchor_id, (
            f"inline-eval/{mode}/{anchor}: resolved to the ANCHOR id {anchor_id!r} "
            "— M4-L7 requires strictly-below-anchor or None, never at anchor"
        )
        # When explicit, it must be a strictly-lower rung.
        if result is not None:
            anchor_idx = _short_to_idx(anchor)
            resolved_idx = _id_to_idx(result)
            assert resolved_idx < anchor_idx, (
                f"inline-eval/{mode}/{anchor}: resolved id {result!r} (idx {resolved_idx}) "
                f"is not strictly below the anchor (idx {anchor_idx})"
            )

    def test_inline_eval_registered_as_economy(self) -> None:
        """D131: kata-inline-eval is registered as economy work-class (forces the ladder tier-down)."""
        assert km.SKILL_WORK_CLASS.get("kata-inline-eval") == "economy"


# ===========================================================================
# 12. Advisor consult — event registry (advisor-executor §3.3, S-20)
# ===========================================================================

_ADVISOR_EVENTS_EXPECTED: tuple[str, ...] = (
    "advisor-fail-threshold",
    "advisor-reroll-grounding",
    "advisor-fix-loop-ceiling",
    "advisor-worker-request",
    "advisor-planning-consult",
)


class TestAdvisorEventRegistry:
    """ADVISOR_EVENTS is its OWN 5-member registry, disjoint from ADAPTIVE_EVENTS;
    ADAPTIVE_EVENTS stays byte-untouched; an advisor event in the premium scope is
    still ILLEGAL (fail-closed classify, S-20)."""

    def test_advisor_events_exact_five_member_tuple(self) -> None:
        assert isinstance(km.ADVISOR_EVENTS, tuple)
        assert km.ADVISOR_EVENTS == _ADVISOR_EVENTS_EXPECTED
        assert len(km.ADVISOR_EVENTS) == 5

    def test_advisor_event_sites_covers_exactly_the_registry(self) -> None:
        assert set(km.ADVISOR_EVENT_SITES) == set(km.ADVISOR_EVENTS)
        # every site is a non-empty description string
        for ev, site in km.ADVISOR_EVENT_SITES.items():
            assert isinstance(site, str) and site.strip(), f"empty site for {ev!r}"

    def test_advisor_events_disjoint_from_adaptive_events(self) -> None:
        assert set(km.ADVISOR_EVENTS).isdisjoint(set(km.ADAPTIVE_EVENTS))

    def test_adaptive_events_byte_untouched(self) -> None:
        """S-20 regression pin: the ADAPTIVE_EVENTS tuple is exactly the frozen 7-member set."""
        assert km.ADAPTIVE_EVENTS == (
            "freeze-gate-verdict",
            "re-gate-after-hold",
            "escalation-adjudication",
            "fix-loop-diagnose",
            "final-initiative-review",
            "gate-rejection-rework-review",
            "fail-bump-escalation",
        )

    @pytest.mark.parametrize("advisor_event", _ADVISOR_EVENTS_EXPECTED)
    def test_advisor_event_in_premium_scope_still_raises(self, advisor_event: str) -> None:
        """S-20: an advisor event name in models.premium.scope.events is ILLEGAL —
        classify_premium_scope RAISES exactly as today (advisor events never join the
        adaptive vocabulary)."""
        with pytest.raises(ValueError):
            km.classify_premium_scope({"events": [advisor_event]})


# ===========================================================================
# 13. Advisor consult — advisor_rung_of (advisor-executor §3.2, S-24)
# ===========================================================================

class TestAdvisorRungOf:
    """The advisor consult rung is the ladder's 'fable' for ANY sub-fable anchor —
    never one-rung-above arithmetic, never mythos; None (inherit-at-anchor) at
    fable/mythos, unknown/empty ladders, no-fable ladders, unknown anchors."""

    @pytest.mark.parametrize("anchor", ["haiku", "sonnet", "opus"])
    def test_sub_fable_anchor_consults_fable(self, anchor: str) -> None:
        assert km.advisor_rung_of(ANTHROPIC, anchor) == "fable"

    def test_sonnet_and_haiku_both_reach_fable_not_one_rung_above(self) -> None:
        # premium_rung_of would give opus for sonnet, sonnet for haiku — advisor differs.
        assert km.advisor_rung_of(ANTHROPIC, "sonnet") == "fable"
        assert km.advisor_rung_of(ANTHROPIC, "haiku") == "fable"
        assert km.premium_rung_of(ANTHROPIC, "sonnet") == "opus"   # contrast, not fable
        assert km.premium_rung_of(ANTHROPIC, "haiku") == "sonnet"  # contrast

    def test_fable_anchor_returns_none_inherit_at_anchor(self) -> None:
        assert km.advisor_rung_of(ANTHROPIC, "fable") is None

    def test_mythos_anchor_returns_none_never_above_fable(self) -> None:
        assert km.advisor_rung_of(ANTHROPIC, "mythos") is None

    def test_unknown_anchor_returns_none(self) -> None:
        assert km.advisor_rung_of(ANTHROPIC, "gpt-99") is None

    @pytest.mark.parametrize("family", ["openai", "gemini", "generic"])
    def test_empty_ladder_families_return_none(self, family: str) -> None:
        # No 'fable' rung on an empty ladder ⇒ None (arm (a) inherit at anchor).
        assert km.advisor_rung_of(family, "opus") is None

    def test_unknown_family_returns_none(self) -> None:
        assert km.advisor_rung_of("nonesuch", "opus") is None

    def test_family_auto_derivation(self) -> None:
        assert km.advisor_rung_of("auto", "opus") == "fable"
        assert km.advisor_rung_of("auto", "fable") is None
        assert km.advisor_rung_of("auto", "gpt-99") is None

    @pytest.mark.parametrize("short", ["haiku", "sonnet", "opus"])
    def test_full_id_anchor_normalization(self, short: str) -> None:
        full_id = km.ID_MAP[short]
        assert km.advisor_rung_of("auto", full_id) == "fable"

    def test_full_id_fable_anchor_returns_none(self) -> None:
        assert km.advisor_rung_of("auto", km.ID_MAP["fable"]) is None


# ===========================================================================
# 14. Advisor consult — _validate_advisor / validate_advisor_block (D136)
# ===========================================================================

# The two canonical bootstrap compositions (advisor-executor §3.4) + the §4 example.
_ADVISOR_ADVANCED_DEFAULT: dict = {
    "enabled": True,
    "approved": True,
    "grantedMode": "advanced",
    "budget": {"calls": 10, "reserved": 2},
}
_ADVISOR_ADVANCED_DECLINED: dict = {
    "enabled": True,
    "approved": False,
    "grantedMode": "advanced",
    "budget": {"calls": 10, "reserved": 2},
}
_ADVISOR_STANDARD_DEFAULT: dict = {
    "enabled": True,
    "approved": False,
    "budget": {"calls": 5, "reserved": 1},
}
_ADVISOR_SECTION4_EXAMPLE: dict = {
    "enabled": True,
    "approved": True,
    "grantedMode": "standard",
    "budget": {"calls": 5, "reserved": 1},
    "hooks": {"failThreshold": 2, "rerollTrigger": 2, "fixLoopCeiling": True},
    "phases": ["execution", "fix-loop"],
}
_ADVISOR_ADVANCED_FULL: dict = {
    "enabled": True,
    "approved": True,
    "grantedMode": "advanced",
    "budget": {"calls": 10, "reserved": 2},
    "hooks": {"failThreshold": 2, "rerollTrigger": 2, "fixLoopCeiling": True},
    "phases": ["planning", "execution", "fix-loop"],
}


class TestValidateAdvisorRoundTrip:
    """FIX-1 (mandatory): BOTH canonical bootstrap compositions — advanced default
    AND standard default — round-trip the validator CLEAN.  A composed default that
    bricks the load-guard is a producer bug this test catches before run time."""

    @pytest.mark.parametrize("block", [
        _ADVISOR_ADVANCED_DEFAULT,
        _ADVISOR_ADVANCED_DECLINED,
        _ADVISOR_STANDARD_DEFAULT,
        _ADVISOR_SECTION4_EXAMPLE,
        _ADVISOR_ADVANCED_FULL,
    ])
    def test_canonical_compositions_validate_clean(self, block: dict) -> None:
        # Must not raise.
        km.validate_advisor_block(block)

    def test_exported_alias_is_the_validator(self) -> None:
        assert km.validate_advisor_block is km._validate_advisor


class TestValidateAdvisorMalformed:
    """Every field's bad shape RAISES (D136 fail-closed) — never a silent OFF."""

    def _base(self) -> dict:
        # a deep-ish copy of a firing block to mutate per-test
        return {
            "enabled": True,
            "approved": True,
            "grantedMode": "advanced",
            "budget": {"calls": 10, "reserved": 2},
            "hooks": {"failThreshold": 2, "rerollTrigger": 2, "fixLoopCeiling": True},
            "phases": ["planning", "execution", "fix-loop"],
        }

    def test_not_a_dict_raises(self) -> None:
        for bad in (["enabled"], "advisor", 3, True):
            with pytest.raises(ValueError):
                km.validate_advisor_block(bad)  # type: ignore[arg-type]

    def test_unknown_top_level_key_raises(self) -> None:
        b = self._base()
        b["extra"] = 1
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_enabled_missing_raises(self) -> None:
        b = self._base(); del b["enabled"]
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_enabled_non_bool_raises(self) -> None:
        b = self._base(); b["enabled"] = 1  # bool ⊂ int — an int is NOT a bool here
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_approved_missing_raises(self) -> None:
        b = self._base(); del b["approved"]
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_approved_non_bool_raises(self) -> None:
        b = self._base(); b["approved"] = 0
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_granted_mode_bad_value_raises(self) -> None:
        b = self._base(); b["grantedMode"] = "essential"
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_granted_mode_wrong_type_raises(self) -> None:
        b = self._base(); b["grantedMode"] = 1
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_missing_raises(self) -> None:
        b = self._base(); del b["budget"]
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_not_dict_raises(self) -> None:
        b = self._base(); b["budget"] = [10, 2]
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_unknown_key_raises(self) -> None:
        b = self._base(); b["budget"] = {"calls": 10, "reserved": 2, "tokensOut": 5}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_calls_missing_raises(self) -> None:
        b = self._base(); b["budget"] = {"reserved": 0}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_calls_bool_raises(self) -> None:
        b = self._base(); b["budget"] = {"calls": True, "reserved": 0}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_calls_negative_raises(self) -> None:
        b = self._base(); b["budget"] = {"calls": -1, "reserved": 0}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_reserved_missing_raises(self) -> None:
        b = self._base(); b["budget"] = {"calls": 5}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_reserved_bool_raises(self) -> None:
        b = self._base(); b["budget"] = {"calls": 5, "reserved": True}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_reserved_negative_raises(self) -> None:
        b = self._base(); b["budget"] = {"calls": 5, "reserved": -1}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_reserved_exceeds_calls_raises(self) -> None:
        b = self._base(); b["budget"] = {"calls": 2, "reserved": 3}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_budget_reserved_equals_calls_ok(self) -> None:
        # boundary: reserved == calls is legal (0 <= reserved <= calls).
        b = self._base(); b["budget"] = {"calls": 2, "reserved": 2}
        km.validate_advisor_block(b)  # must not raise

    def test_hooks_not_dict_raises(self) -> None:
        b = self._base(); b["hooks"] = ["failThreshold"]
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_hooks_unknown_key_raises(self) -> None:
        b = self._base(); b["hooks"] = {"failThreshold": 2, "bogus": 1}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_hooks_fail_threshold_zero_raises(self) -> None:
        b = self._base(); b["hooks"] = {"failThreshold": 0}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_hooks_fail_threshold_bool_raises(self) -> None:
        b = self._base(); b["hooks"] = {"failThreshold": True}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_hooks_fail_threshold_non_int_raises(self) -> None:
        b = self._base(); b["hooks"] = {"failThreshold": "2"}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_hooks_reroll_trigger_bool_raises(self) -> None:
        b = self._base(); b["hooks"] = {"rerollTrigger": True}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_hooks_fix_loop_ceiling_non_bool_raises(self) -> None:
        b = self._base(); b["hooks"] = {"fixLoopCeiling": 1}
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_phases_not_list_raises(self) -> None:
        b = self._base(); b["phases"] = "execution"
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_phases_bad_member_raises(self) -> None:
        b = self._base(); b["phases"] = ["execution", "gate"]
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)

    def test_phases_non_string_member_raises(self) -> None:
        b = self._base(); b["phases"] = ["execution", 3]
        with pytest.raises(ValueError):
            km.validate_advisor_block(b)


# ===========================================================================
# 15. Advisor consult — advisor_status sibling gate (§3.2, S-16/S-21/S-24)
# ===========================================================================

def _advisor(**overrides: object) -> dict:
    """A firing advisor block; override individual fields per-test."""
    base = {
        "enabled": True,
        "approved": True,
        "grantedMode": "advanced",
        "budget": {"calls": 10, "reserved": 2},
    }
    base.update(overrides)
    return base


_FIRING_EVENT = "advisor-fail-threshold"


class TestAdvisorStatusFiresMatrix:
    """Every NO-FIRE reason in the §3.2 table, hit at least once, in precedence order;
    both mode arms; both rung arms; absent."""

    def test_absent_block(self) -> None:
        assert km.advisor_status(None, "opus", family=ANTHROPIC, mode="standard",
                                 event=_FIRING_EVENT) == {
            "fires": False, "reason": "absent", "rung": None,
        }

    def test_malformed_block_raises_not_a_reason(self) -> None:
        with pytest.raises(ValueError):
            km.advisor_status({"enabled": True}, "opus", family=ANTHROPIC,
                              mode="advanced", event=_FIRING_EVENT)

    def test_not_enabled(self) -> None:
        st = km.advisor_status(_advisor(enabled=False), "opus",
                               family=ANTHROPIC, mode="advanced", event=_FIRING_EVENT)
        assert st["fires"] is False and st["reason"] == "not-enabled"

    def test_not_approved(self) -> None:
        st = km.advisor_status(_advisor(approved=False), "opus",
                               family=ANTHROPIC, mode="advanced", event=_FIRING_EVENT)
        assert st["fires"] is False and st["reason"] == "not-approved"

    def test_mode_excluded_essential(self) -> None:
        st = km.advisor_status(_advisor(), "opus",
                               family=ANTHROPIC, mode="essential", event=_FIRING_EVENT)
        assert st["fires"] is False and st["reason"] == "mode-excluded"

    def test_mode_excluded_unknown_mode_fail_closed(self) -> None:
        st = km.advisor_status(_advisor(), "opus",
                               family=ANTHROPIC, mode="bogus", event=_FIRING_EVENT)
        assert st["fires"] is False and st["reason"] == "mode-excluded"

    def test_standard_not_granted_when_granted_mode_absent(self) -> None:
        adv = {"enabled": True, "approved": True, "budget": {"calls": 5, "reserved": 1}}
        st = km.advisor_status(adv, "opus", family=ANTHROPIC, mode="standard",
                               event=_FIRING_EVENT)
        assert st["fires"] is False and st["reason"] == "standard-not-granted"

    def test_standard_not_granted_when_granted_mode_advanced(self) -> None:
        st = km.advisor_status(_advisor(grantedMode="advanced"), "opus",
                               family=ANTHROPIC, mode="standard", event=_FIRING_EVENT)
        assert st["fires"] is False and st["reason"] == "standard-not-granted"

    def test_no_event(self) -> None:
        st = km.advisor_status(_advisor(), "opus",
                               family=ANTHROPIC, mode="advanced", event=None)
        assert st["fires"] is False and st["reason"] == "no-event"

    def test_unknown_event(self) -> None:
        st = km.advisor_status(_advisor(), "opus",
                               family=ANTHROPIC, mode="advanced", event="not-real")
        assert st["fires"] is False and st["reason"] == "unknown-event"

    # ---- firing: both mode arms ----

    def test_advanced_fires(self) -> None:
        st = km.advisor_status(_advisor(), "opus",
                               family=ANTHROPIC, mode="advanced", event=_FIRING_EVENT)
        assert st == {"fires": True, "reason": "fires", "rung": "fable"}

    def test_standard_granted_fires(self) -> None:
        adv = _advisor(grantedMode="standard", budget={"calls": 5, "reserved": 1})
        st = km.advisor_status(adv, "opus", family=ANTHROPIC, mode="standard",
                               event=_FIRING_EVENT)
        assert st == {"fires": True, "reason": "fires", "rung": "fable"}

    @pytest.mark.parametrize("event", _ADVISOR_EVENTS_EXPECTED)
    def test_all_registered_events_fire(self, event: str) -> None:
        st = km.advisor_status(_advisor(), "opus",
                               family=ANTHROPIC, mode="advanced", event=event)
        assert st["fires"] is True and st["reason"] == "fires"

    # ---- firing: both rung arms (S-24) ----

    @pytest.mark.parametrize("anchor", ["haiku", "sonnet", "opus"])
    def test_sub_fable_anchor_fires_with_fable_rung(self, anchor: str) -> None:
        st = km.advisor_status(_advisor(), anchor,
                               family=ANTHROPIC, mode="advanced", event=_FIRING_EVENT)
        assert st["fires"] is True and st["rung"] == "fable"

    def test_fable_anchor_fires_with_none_rung(self) -> None:
        st = km.advisor_status(_advisor(), "fable",
                               family=ANTHROPIC, mode="advanced", event=_FIRING_EVENT)
        assert st["fires"] is True and st["rung"] is None

    def test_mythos_anchor_fires_with_none_rung(self) -> None:
        st = km.advisor_status(_advisor(), "mythos",
                               family=ANTHROPIC, mode="advanced", event=_FIRING_EVENT)
        assert st["fires"] is True and st["rung"] is None

    def test_full_id_anchor_normalized(self) -> None:
        st = km.advisor_status(_advisor(), km.ID_MAP["opus"],
                               family="auto", mode="advanced", event=_FIRING_EVENT)
        assert st["fires"] is True and st["rung"] == "fable"

    def test_rung_never_premium_arithmetic_never_mythos(self) -> None:
        # sonnet anchor: advisor rung is fable, NOT opus (premium arithmetic) nor mythos.
        st = km.advisor_status(_advisor(), "sonnet",
                               family=ANTHROPIC, mode="advanced", event=_FIRING_EVENT)
        assert st["rung"] == "fable"
        assert st["rung"] != km.premium_rung_of(ANTHROPIC, "sonnet")  # != "opus"
        assert st["rung"] != "mythos"


class TestAdvisorStatusPrecedenceMutationGuards:
    """Mutation-style guards: each conjunct precedes the next in the exact order of
    the §3.2 register.  Flip a conjunct's order in kata_models and one of these fails."""

    def test_not_enabled_precedes_not_approved(self) -> None:
        # BOTH enabled and approved False ⇒ 'not-enabled' wins (enabled checked first).
        st = km.advisor_status(_advisor(enabled=False, approved=False), "opus",
                               family=ANTHROPIC, mode="advanced", event=_FIRING_EVENT)
        assert st["reason"] == "not-enabled"

    def test_not_approved_precedes_mode_excluded(self) -> None:
        # approved False AND essential mode ⇒ 'not-approved' wins.
        st = km.advisor_status(_advisor(approved=False), "opus",
                               family=ANTHROPIC, mode="essential", event=_FIRING_EVENT)
        assert st["reason"] == "not-approved"

    def test_mode_excluded_precedes_standard_not_granted(self) -> None:
        # essential + no grantedMode ⇒ 'mode-excluded' wins (mode checked before the
        # standard carve-out arm).
        adv = {"enabled": True, "approved": True, "budget": {"calls": 5, "reserved": 1}}
        st = km.advisor_status(adv, "opus", family=ANTHROPIC, mode="essential",
                               event=_FIRING_EVENT)
        assert st["reason"] == "mode-excluded"

    def test_standard_not_granted_precedes_no_event(self) -> None:
        # standard + not granted + event None ⇒ 'standard-not-granted' wins.
        adv = {"enabled": True, "approved": True, "budget": {"calls": 5, "reserved": 1}}
        st = km.advisor_status(adv, "opus", family=ANTHROPIC, mode="standard", event=None)
        assert st["reason"] == "standard-not-granted"

    def test_no_event_precedes_unknown_event(self) -> None:
        # event None ⇒ 'no-event' (not 'unknown-event').
        st = km.advisor_status(_advisor(), "opus",
                               family=ANTHROPIC, mode="advanced", event=None)
        assert st["reason"] == "no-event"


class TestAdvisorWorkClassEntry:
    """S-7: kata-advise is registered critical (pre-staged by T1; the R5 coverage
    test proves it live once T4's skill lands)."""

    def test_kata_advise_is_critical(self) -> None:
        assert km.SKILL_WORK_CLASS["kata-advise"] == "critical"
