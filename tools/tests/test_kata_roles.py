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
