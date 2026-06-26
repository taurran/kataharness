"""kata_roles.py — resolve the multi-model `roles` routing block (N4, spec multi-model-orchestration).

KataHarness can route each loop ROLE to a different platform/model. The default is
all-roles-on-the-host (single-model, backward-compatible). A `roles` block in
`kata.config` overrides per role; assignments to a non-host platform must name a
platform that has been **confirmed** on this machine (`confirmedPlatforms`).

Role groups (DESIGN LD1): coder · validator · researcher · orchestrator · evaluator.

Public API
----------
ROLE_GROUPS : frozenset
resolve_roles(roles_block, confirmed_platforms, host_platform="claude") -> dict
    Pure. Returns ``{role: {"platform", "model"?, "effort"?}}`` for EVERY role group
    (absent roles default to the host). Raises ``ValueError`` (fail-closed) on an
    unknown role or a non-host platform not in ``confirmed_platforms``.
is_multimodal(resolved, host_platform="claude") -> bool
    True iff any role resolves to a platform other than the host.

BC1: ``roles_block`` falsy ⇒ every role on the host (today's single-model loop).
"""

from __future__ import annotations

ROLE_GROUPS = frozenset({"coder", "validator", "researcher", "orchestrator", "evaluator"})


def resolve_roles(
    roles_block: dict | None,
    confirmed_platforms: list[str] | None = None,
    host_platform: str = "claude",
) -> dict:
    """Resolve every role to a platform/model; default = host. Fail-closed on bad input."""
    confirmed = set(confirmed_platforms or []) | {host_platform}  # the host is always available
    resolved: dict = {role: {"platform": host_platform} for role in ROLE_GROUPS}
    if not roles_block:
        return resolved  # BC1 — all on host

    for role, assign in roles_block.items():
        if role not in ROLE_GROUPS:
            raise ValueError(f"kata_roles: unknown role {role!r} (valid: {sorted(ROLE_GROUPS)})")
        if not isinstance(assign, dict):
            raise ValueError(f"kata_roles: role {role!r} assignment must be an object, got {type(assign).__name__}")
        platform = assign.get("platform") or host_platform
        if platform not in confirmed:
            raise ValueError(
                f"kata_roles: role {role!r} → platform {platform!r} is not confirmed "
                f"(confirmedPlatforms={sorted(confirmed - {host_platform})}); confirm it or run on the host"
            )
        entry = {"platform": platform}
        if assign.get("model"):
            entry["model"] = assign["model"]
        if assign.get("effort"):
            entry["effort"] = assign["effort"]
        resolved[role] = entry
    return resolved


def is_multimodal(resolved: dict, host_platform: str = "claude") -> bool:
    """True iff any role is routed off the host."""
    return any(v.get("platform", host_platform) != host_platform for v in resolved.values())
