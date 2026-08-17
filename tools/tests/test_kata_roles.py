"""Tests for kata_roles.py — the multi-model roles routing resolver (N4)."""

from __future__ import annotations

import pytest

import kata_roles as kr


def test_absent_block_all_on_host():
    resolved = kr.resolve_roles(None, [], host_platform="claude")
    assert set(resolved) == kr.ROLE_GROUPS
    assert all(v["platform"] == "claude" for v in resolved.values())
    assert kr.is_multimodal(resolved, "claude") is False


def test_override_routes_role(host="claude"):
    block = {"validator": {"platform": "codex", "model": "gpt-5-codex"}}
    resolved = kr.resolve_roles(block, ["codex"], host_platform=host)
    assert resolved["validator"] == {"platform": "codex", "model": "gpt-5-codex"}
    assert resolved["coder"]["platform"] == "claude"  # unset → host
    assert kr.is_multimodal(resolved, host) is True


def test_unknown_role_rejected():
    with pytest.raises(ValueError, match="unknown role"):
        kr.resolve_roles({"banana": {"platform": "codex"}}, ["codex"])


def test_unconfirmed_platform_rejected():
    with pytest.raises(ValueError, match="not confirmed"):
        kr.resolve_roles({"validator": {"platform": "codex"}}, confirmed_platforms=[])


def test_host_always_confirmed():
    # routing a role explicitly to the host needs no confirmation entry
    resolved = kr.resolve_roles({"coder": {"platform": "claude"}}, [], host_platform="claude")
    assert resolved["coder"]["platform"] == "claude"


def test_non_dict_assignment_rejected():
    with pytest.raises(ValueError, match="must be an object"):
        kr.resolve_roles({"validator": "codex"}, ["codex"])


def test_effort_preserved():
    # validator is routable off-host (evaluator/orchestrator are host-only, LD11)
    block = {"validator": {"platform": "codex", "model": "m", "effort": "low"}}
    resolved = kr.resolve_roles(block, ["codex"])
    assert resolved["validator"]["effort"] == "low"


def test_host_only_roles_reject_off_host():
    """Red-team: orchestrator/evaluator MUST fail-closed when routed off-host (LD11).

    Was a doc-vs-code lie: config.md promised fail-closed validation, but
    resolve_roles silently accepted then dropped these assignments."""
    for role in ("orchestrator", "evaluator"):
        with pytest.raises(ValueError, match="host-only"):
            kr.resolve_roles({role: {"platform": "codex"}}, ["codex"])


def test_host_only_roles_allowed_on_host():
    """Explicitly pinning a host-only role to the host is fine (no-op)."""
    resolved = kr.resolve_roles({"evaluator": {"platform": "claude"}}, ["codex"])
    assert resolved["evaluator"]["platform"] == "claude"


# ---------------------------------------------------------------------------
# dispatch-authoring: design-author / plan-author (DESIGN §4.1, T1)
# ---------------------------------------------------------------------------

def test_role_groups_includes_dispatch_authoring_roles():
    """ROLE_GROUPS carries the dispatch-authoring pair (DESIGN §6) — additive, closed-enum.

    The exact-set assertion moved to ``test_role_groups_is_the_exact_closed_enum`` when the
    trust-model seam wave added its seven roles; this test keeps its own subject (the two
    authoring roles are members) rather than re-asserting the whole enum twice.
    """
    assert {"design-author", "plan-author"} <= kr.ROLE_GROUPS


# ---------------------------------------------------------------------------
# trust-model seam: the seven seam roles (DESIGN §1.6, R-M5)
# ---------------------------------------------------------------------------

_SEAM_ROLES = frozenset({
    "reviewer", "slop", "inline-eval", "advisor", "critic", "challenger", "grounding",
})


def test_role_groups_is_the_exact_closed_enum():
    """The enum is CLOSED — this is the one place its exact membership is pinned."""
    assert kr.ROLE_GROUPS == frozenset({
        "coder", "validator", "researcher", "orchestrator", "evaluator",
        "design-author", "plan-author",
        "reviewer", "slop", "inline-eval", "advisor", "critic", "challenger", "grounding",
    })


def test_seam_roles_are_additive():
    """R-M5: the seam's launch surfaces gain role tokens; nothing existing is removed."""
    assert _SEAM_ROLES <= kr.ROLE_GROUPS
    assert {"coder", "validator", "researcher", "orchestrator", "evaluator"} <= kr.ROLE_GROUPS


def test_host_only_roles_unchanged_by_the_seam_wave():
    """R-M5 verbatim: HOST_ONLY_ROLES is UNCHANGED pending the cadre grill."""
    assert kr.HOST_ONLY_ROLES == frozenset({"orchestrator", "evaluator"})
    assert not (_SEAM_ROLES & kr.HOST_ONLY_ROLES)


@pytest.mark.parametrize("role", sorted(_SEAM_ROLES))
def test_every_seam_role_resolves_and_routes_off_host(role):
    """Each new role is a first-class member: it defaults to the host and may route off it."""
    assert kr.resolve_roles(None)[role]["platform"] == "claude"
    resolved = kr.resolve_roles({role: {"platform": "codex"}}, ["codex"])
    assert resolved[role]["platform"] == "codex"


@pytest.mark.parametrize("role", sorted(_SEAM_ROLES))
def test_every_seam_role_fails_closed_on_an_unconfirmed_platform(role):
    """No special-casing bypasses the confirm check for the new roles."""
    with pytest.raises(ValueError, match="not confirmed"):
        kr.resolve_roles({role: {"platform": "codex"}}, confirmed_platforms=[])


def test_dispatch_authoring_roles_not_host_only():
    """Neither new role is in HOST_ONLY_ROLES (DESIGN §4.1) — they may route off-host."""
    assert "design-author" not in kr.HOST_ONLY_ROLES
    assert "plan-author" not in kr.HOST_ONLY_ROLES


def test_design_author_resolves_to_confirmed_platform():
    resolved = kr.resolve_roles({"design-author": {"platform": "codex"}}, ["codex"])
    assert resolved["design-author"]["platform"] == "codex"


def test_design_author_unconfirmed_platform_rejected():
    """Same fail-closed confirm check as every other role — no special-casing bypasses it."""
    with pytest.raises(ValueError, match="not confirmed"):
        kr.resolve_roles({"design-author": {"platform": "codex"}}, confirmed_platforms=[])


def test_plan_author_resolves_to_confirmed_platform():
    resolved = kr.resolve_roles({"plan-author": {"platform": "codex"}}, ["codex"])
    assert resolved["plan-author"]["platform"] == "codex"


# ---------------------------------------------------------------------------
# PART 1: relative model tokens (DESIGN D59)
# ---------------------------------------------------------------------------
import kata_models as km  # noqa: E402 — imported after the existing tests for grouping clarity

_CONFIRMED_CODEX = ["codex"]


class TestRelativeModelTokens:
    """'anchor' / 'anchor-1' / 'anchor-2' tokens in a role's model field."""

    def test_anchor_token_omits_model(self):
        """'anchor' → zero-step contract → model field omitted (inherit)."""
        block = {"coder": {"platform": "codex", "model": "anchor"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="opus", family="anthropic")
        assert "model" not in resolved["coder"]

    def test_anchor_minus1_returns_one_rung_below(self):
        """anchor-1 with anchor=opus (index 2) → sonnet (index 1)."""
        block = {"coder": {"platform": "codex", "model": "anchor-1"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="opus", family="anthropic")
        assert resolved["coder"]["model"] == km.ID_MAP["sonnet"]

    def test_anchor_minus1_at_floor_omits_model(self):
        """anchor-1 with anchor=haiku (floor, index 0) → clamped to anchor_idx → inherit."""
        block = {"coder": {"platform": "codex", "model": "anchor-1"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="haiku", family="anthropic")
        assert "model" not in resolved["coder"]

    def test_anchor_minus2_opus_returns_haiku(self):
        """anchor-2 with anchor=opus (index 2) → max(0, 0) = 0 → haiku."""
        block = {"coder": {"platform": "codex", "model": "anchor-2"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="opus", family="anthropic")
        assert resolved["coder"]["model"] == km.ID_MAP["haiku"]

    def test_anchor_minus2_sonnet_returns_haiku(self):
        """anchor-2 with anchor=sonnet (index 1) → max(0, -1) = 0 → haiku."""
        block = {"coder": {"platform": "codex", "model": "anchor-2"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="sonnet", family="anthropic")
        assert resolved["coder"]["model"] == km.ID_MAP["haiku"]

    def test_anchor_minus2_at_floor_omits_model(self):
        """anchor-2 with anchor=haiku (floor, index 0) → max(0,-2)=0 == anchor_idx → inherit."""
        block = {"coder": {"platform": "codex", "model": "anchor-2"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="haiku", family="anthropic")
        assert "model" not in resolved["coder"]

    def test_unknown_anchor_omits_model(self):
        """Unknown anchor short-name → inherit-on-doubt → model omitted."""
        block = {"coder": {"platform": "codex", "model": "anchor-1"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="unknown-model", family="anthropic")
        assert "model" not in resolved["coder"]

    def test_unknown_family_omits_model(self):
        """Unknown family key → inherit-on-doubt → model omitted."""
        block = {"coder": {"platform": "codex", "model": "anchor-1"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="opus", family="unknown-family")
        assert "model" not in resolved["coder"]

    def test_absolute_model_id_passes_through(self):
        """Absolute model ID is never treated as a relative token — passes through unchanged (BC)."""
        block = {"coder": {"platform": "codex", "model": "claude-opus-4-8"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="sonnet", family="anthropic")
        assert resolved["coder"]["model"] == "claude-opus-4-8"

    def test_absent_model_field_bc(self):
        """Absent model field in assignment → no model in result (BC unchanged)."""
        block = {"coder": {"platform": "codex"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="sonnet", family="anthropic")
        assert "model" not in resolved["coder"]

    def test_no_anchor_family_relative_token_inherits(self):
        """No anchor/family kwargs supplied → relative token falls through to inherit; old call-sites unaffected."""
        block = {"coder": {"platform": "codex", "model": "anchor-1"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX)
        assert "model" not in resolved["coder"]

    def test_anchor_minus1_fable_returns_opus(self):
        """anchor-1 with anchor=fable (index 3) → opus (index 2)."""
        block = {"coder": {"platform": "codex", "model": "anchor-1"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="fable", family="anthropic")
        assert resolved["coder"]["model"] == km.ID_MAP["opus"]

    def test_effort_preserved_alongside_relative_token(self):
        """effort field is retained regardless of relative model token resolution."""
        block = {"coder": {"platform": "codex", "model": "anchor-1", "effort": "low"}}
        resolved = kr.resolve_roles(block, _CONFIRMED_CODEX, anchor="opus", family="anthropic")
        assert resolved["coder"]["effort"] == "low"
        assert resolved["coder"]["model"] == km.ID_MAP["sonnet"]
