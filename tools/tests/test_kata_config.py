"""test_kata_config.py — TDD suite for the GB12 core-config load-guard (BURN-D).

The defect: skills/coordinate/kata-orchestrate/SKILL.md promised fail-closed
validation of a present kata.config's ``mode`` / ``tiers`` / ``modules`` with no
named mechanism behind the promise. ``kata_config.validate_core_config`` is that
mechanism. Style-matched to ``kata_models.validate_advisor_block``: RAISES
``ValueError`` on any malformed field so the load-guard STOPs and escalates;
absent keys pass (documented defaults apply — ``mode`` absent ⇒ "standard", D25).

Out of scope BY CONTRACT (GRILL-LEDGER Amendment 6): ``effort.reasoning``
(protocol/config.md:15 disclaims its own enum — "indicative, not an API
contract") and malformed-JSON detection (the caller's read step owns that).

Run:
    cd tools && uv run pytest tests/test_kata_config.py -v
"""
from __future__ import annotations

import pytest

import kata_config as kc

# ---------------------------------------------------------------------------
# Fixtures — a realistic available-skills surface (names + provided module tags)
# ---------------------------------------------------------------------------

AVAILABLE: set[str] = {
    "kata-grill-essential", "kata-grill-standard", "kata-grill-advanced",
    "kata-review-essential", "kata-review-standard", "kata-review-advanced",
    "kata-plan-essential", "kata-plan-standard", "kata-plan-advanced",
    "kata-diagnose-light", "kata-diagnose-full",
    "kata-slop-check", "kata-comprehend", "kata-benchmark-report",
    "kata-orchestrate", "kata-evaluate",
}

PROVIDED: set[str] = {
    "kata/module/slop",
    "kata/module/debug",
    "kata/module/benchmark",
    "kata/module/quality",
}


def validate(config: dict) -> None:
    """Shorthand: validate *config* against the fixture surface."""
    kc.validate_core_config(config, AVAILABLE, PROVIDED)


# ---------------------------------------------------------------------------
# 1. Valid configs pass
# ---------------------------------------------------------------------------

class TestValidConfigsPass:
    def test_fully_valid_config_passes(self):
        validate({
            "mode": "standard",
            "tiers": {"kata-grill": "advanced", "kata-diagnose": "light"},
            "modules": ["kata/module/slop", "kata/module/debug"],
        })

    def test_empty_config_passes(self):
        """Absent keys ⇒ documented defaults apply (mode ⇒ standard, D25)."""
        validate({})

    def test_absent_mode_passes(self):
        validate({"tiers": {"kata-review": "essential"}})

    def test_absent_tiers_and_modules_pass(self):
        validate({"mode": "essential"})

    def test_unvalidated_registry_keys_are_ignored(self):
        """config.md is a growing key registry — keys outside this validator's
        scope (effort, target, delivery, ...) must not raise here; each has its
        own named validator or is disclaimed (effort.reasoning)."""
        validate({
            "mode": "advanced",
            "effort": {"model": "whatever", "reasoning": "not-an-enum-value"},
            "runShape": "individual",
            "target": {"kind": "greenfield"},
        })

    def test_empty_modules_list_passes(self):
        validate({"modules": []})

    def test_empty_tiers_dict_passes(self):
        validate({"tiers": {}})


# ---------------------------------------------------------------------------
# 2. mode — {"essential", "standard", "advanced"} or absent
# ---------------------------------------------------------------------------

class TestMode:
    @pytest.mark.parametrize("mode", ["essential", "standard", "advanced"])
    def test_each_valid_mode_passes(self, mode):
        validate({"mode": mode})

    def test_unknown_mode_raises_and_names_the_value(self):
        with pytest.raises(ValueError, match=r"mode.*'turbo'"):
            validate({"mode": "turbo"})

    def test_case_variant_mode_raises(self):
        """Never a silent coercion (D45/GB12)."""
        with pytest.raises(ValueError, match="mode"):
            validate({"mode": "Standard"})

    def test_non_string_mode_raises(self):
        with pytest.raises(ValueError, match="mode"):
            validate({"mode": 2})


# ---------------------------------------------------------------------------
# 3. tiers — every tiers[family] must name a kata-<family>-<tier> skill,
#    with the ONE grill-skip carve-out (D71/D73)
# ---------------------------------------------------------------------------

class TestTiers:
    def test_known_tier_passes(self):
        validate({"tiers": {"kata-grill": "essential"}})

    def test_grill_skip_carveout_passes(self):
        validate({"tiers": {"kata-grill": "skip"}})

    def test_unknown_tier_raises_and_names_family_and_tier(self):
        with pytest.raises(ValueError, match=r"kata-grill.*'ultra'"):
            validate({"tiers": {"kata-grill": "ultra"}})

    def test_skip_on_non_grill_family_raises(self):
        """'skip' is legal ONLY for kata-grill (D71) — kata-review-skip is not a skill."""
        with pytest.raises(ValueError, match=r"kata-review.*'skip'"):
            validate({"tiers": {"kata-review": "skip"}})

    def test_unknown_family_raises(self):
        """An unknown family can name no kata-<family>-<tier> skill."""
        with pytest.raises(ValueError, match=r"kata-nonesuch"):
            validate({"tiers": {"kata-nonesuch": "standard"}})

    def test_diagnose_two_tier_family_passes(self):
        validate({"tiers": {"kata-diagnose": "full"}})

    def test_three_tier_value_on_two_tier_family_raises(self):
        """kata-diagnose has light|full only — 'standard' names no skill."""
        with pytest.raises(ValueError, match=r"kata-diagnose.*'standard'"):
            validate({"tiers": {"kata-diagnose": "standard"}})

    def test_non_dict_tiers_raises(self):
        with pytest.raises(ValueError, match="tiers"):
            validate({"tiers": ["kata-grill"]})

    def test_non_string_tier_value_raises(self):
        with pytest.raises(ValueError, match="tiers"):
            validate({"tiers": {"kata-grill": 3}})


# ---------------------------------------------------------------------------
# 4. modules — every entry must have a provider skill (a skill tagged
#    kata/module/<module>); short and full forms both accepted
# ---------------------------------------------------------------------------

class TestModules:
    def test_full_form_module_with_provider_passes(self):
        validate({"modules": ["kata/module/debug"]})

    def test_short_form_module_with_provider_passes(self):
        """protocol/config.md's own schema example uses short names
        ('quality', ...); the modules table uses full kata/module/<x> keys.
        Both documented forms are accepted; both resolve to the tag."""
        validate({"modules": ["debug", "slop"]})

    def test_module_without_provider_raises_and_names_the_entry(self):
        with pytest.raises(ValueError, match=r"kata/module/nonesuch"):
            validate({"modules": ["kata/module/nonesuch"]})

    def test_short_form_without_provider_raises(self):
        with pytest.raises(ValueError, match=r"'bakeoff'"):
            validate({"modules": ["bakeoff"]})

    def test_non_list_modules_raises(self):
        with pytest.raises(ValueError, match="modules"):
            validate({"modules": "kata/module/debug"})

    def test_non_string_module_entry_raises(self):
        with pytest.raises(ValueError, match="modules"):
            validate({"modules": [42]})


# ---------------------------------------------------------------------------
# 5. Top-level shape + determinism
# ---------------------------------------------------------------------------

class TestShapeAndDeterminism:
    def test_non_dict_config_raises(self):
        with pytest.raises(ValueError, match="dict"):
            validate(["mode", "standard"])

    def test_multi_error_message_order_is_sorted(self):
        """Determinism Doctrine: sets never drive output order — with two
        unprovided modules, the error names them in sorted order."""
        with pytest.raises(ValueError) as exc:
            validate({"modules": ["zzz-mod", "aaa-mod"]})
        msg = str(exc.value)
        assert msg.index("aaa-mod") < msg.index("zzz-mod")


# ---------------------------------------------------------------------------
# 6. available_from_skills — the producer bridge over load_skills() output
# ---------------------------------------------------------------------------

class _StubSkill:
    """Duck-typed stand-in for validate_skills.Skill (.name + .frontmatter)."""

    def __init__(self, name: str, tags: list[str] | None = None):
        self.name = name
        self.frontmatter = {"tags": tags} if tags is not None else {}


class TestAvailableFromSkills:
    def test_derives_names_and_module_tags(self):
        skills = [
            _StubSkill("kata-slop-check", ["kata/evaluate", "kata/module/slop"]),
            _StubSkill("kata-grill-standard", ["kata/plan", "kata/spine", "kata/tier/standard"]),
            _StubSkill("kata-comprehend", ["kata/plan", "kata/module/debug"]),
        ]
        names, provided = kc.available_from_skills(skills)
        assert names == {"kata-slop-check", "kata-grill-standard", "kata-comprehend"}
        assert provided == {"kata/module/slop", "kata/module/debug"}

    def test_missing_tags_key_is_tolerated(self):
        names, provided = kc.available_from_skills([_StubSkill("kata-evaluate")])
        assert names == {"kata-evaluate"}
        assert provided == set()

    def test_round_trip_with_validator(self):
        skills = [
            _StubSkill("kata-grill-standard", ["kata/plan", "kata/spine"]),
            _StubSkill("kata-slop-check", ["kata/evaluate", "kata/module/slop"]),
        ]
        names, provided = kc.available_from_skills(skills)
        kc.validate_core_config(
            {"mode": "standard", "tiers": {"kata-grill": "standard"},
             "modules": ["kata/module/slop"]},
            names, provided,
        )
        with pytest.raises(ValueError, match=r"kata/module/debug"):
            kc.validate_core_config({"modules": ["kata/module/debug"]}, names, provided)
