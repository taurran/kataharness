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
