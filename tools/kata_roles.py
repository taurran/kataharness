"""kata_roles.py — resolve the multi-model `roles` routing block (N4, spec multi-model-orchestration).

KataHarness can route each loop ROLE to a different platform/model. The default is
all-roles-on-the-host (single-model, backward-compatible). A `roles` block in
`kata.config` overrides per role; assignments to a non-host platform must name a
platform that has been **confirmed** on this machine (`confirmedPlatforms`).

Role groups (DESIGN LD1): coder · validator · researcher · orchestrator · evaluator.

Public API
----------
ROLE_GROUPS : frozenset
resolve_roles(roles_block, confirmed_platforms, host_platform="claude", *, anchor=None, family=None) -> dict
    Pure. Returns ``{role: {"platform", "model"?, "effort"?}}`` for EVERY role group
    (absent roles default to the host). Raises ``ValueError`` (fail-closed) on an
    unknown role, a non-host platform not in ``confirmed_platforms``, or an attempt
    to route a HOST_ONLY_ROLES role (orchestrator/evaluator) off the host (LD11).
    Relative model tokens ("anchor", "anchor-1", "anchor-2") in a role's ``model``
    field are resolved via ``kata_models`` using *anchor* + *family*; unknown or
    absent context inherits by omission (model field omitted from the entry).
is_multimodal(resolved, host_platform="claude") -> bool
    True iff any role resolves to a platform other than the host.

BC1: ``roles_block`` falsy ⇒ every role on the host (today's single-model loop).
BC2: Absent *anchor* / *family* ⇒ relative tokens inherit (model field omitted);
     existing call-sites without these kwargs are unaffected.
"""

from __future__ import annotations

import kata_models as _km

ROLE_GROUPS = frozenset({"coder", "validator", "researcher", "orchestrator", "evaluator"})

# Roles that MUST run on the orchestrator's own host in v1 (DESIGN LD11 / MM-1):
# the orchestrator is the plan-guardian and the evaluator is the default-FAIL gate —
# neither has a wired off-host dispatch path. config.md advertises `roles` as
# "validated fail-closed at preflight"; this set is the code that makes the
# host-only half of that promise real (an off-host assignment STOPs, never silently
# resolves-then-drops).
HOST_ONLY_ROLES = frozenset({"orchestrator", "evaluator"})

# Relative model tokens recognised in a role's ``model`` field (DESIGN D59).
# Resolved at call time against the operator's current anchor model + family;
# unknown anchor / unknown family → None (inherit-on-doubt / fail-closed).
_RELATIVE_MODEL_TOKENS = frozenset({"anchor", "anchor-1", "anchor-2"})


def _resolve_relative_model_token(token: str, anchor: str, family: str) -> str | None:
    """Resolve a relative model token to a full model ID, or None (inherit).

    Delegates to ``kata_models.step_down()`` for the ladder walk (FIX-2 DRY).

    Parameters
    ----------
    token  : one of "anchor", "anchor-1", "anchor-2"
    anchor : short model name within the family (e.g. "opus")
    family : model-family key (e.g. "anthropic")

    Rules
    -----
    "anchor"   → None (zero-step contract; step_down(anchor, 0, family) → None)
    "anchor-1" → step_down(anchor, 1, family) — one rung below, or None at floor
    "anchor-2" → step_down(anchor, 2, family) — two rungs below, or None at floor

    Unknown anchor, unknown family, or empty ladder → None (inherit-on-doubt).
    ``family="auto"`` triggers ``family_of(anchor)`` derivation inside
    ``step_down`` (consistent with ``resolve()``); other values are used as-is (BC).
    """
    if token == "anchor":
        return _km.step_down(anchor, 0, family)  # zero-step contract → None
    elif token == "anchor-1":
        return _km.step_down(anchor, 1, family)
    elif token == "anchor-2":
        return _km.step_down(anchor, 2, family)
    else:
        return None  # unrecognised token → inherit-on-doubt


def resolve_roles(
    roles_block: dict | None,
    confirmed_platforms: list[str] | None = None,
    host_platform: str = "claude",
    *,
    anchor: str | None = None,
    family: str | None = None,
) -> dict:
    """Resolve every role to a platform/model; default = host. Fail-closed on bad input.

    Parameters
    ----------
    roles_block         : the ``roles`` mapping from ``kata.config`` (or None / {})
    confirmed_platforms : platforms confirmed on this machine (the host is always implicit)
    host_platform       : the host's own platform name (default "claude")
    anchor              : short model name of the current session anchor (e.g. "opus");
                          required for relative model-token resolution (DESIGN D59)
    family              : model-family key (e.g. "anthropic"); required for relative tokens
    """
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
        if role in HOST_ONLY_ROLES and platform != host_platform:
            raise ValueError(
                f"kata_roles: role {role!r} is host-only in v1 (DESIGN LD11) and cannot be "
                f"routed to {platform!r}; it has no off-host dispatch path. Remove the override "
                f"or run it on the host {host_platform!r}."
            )
        if platform not in confirmed:
            raise ValueError(
                f"kata_roles: role {role!r} → platform {platform!r} is not confirmed "
                f"(confirmedPlatforms={sorted(confirmed - {host_platform})}); confirm it or run on the host"
            )
        entry = {"platform": platform}
        if assign.get("model"):
            model_val: str = assign["model"]
            if model_val in _RELATIVE_MODEL_TOKENS:
                # Relative token: resolve via kata_models ladder (DESIGN D59).
                # Unknown anchor / family → inherit by omission (fail-closed / BC).
                resolved_model = _resolve_relative_model_token(
                    model_val, anchor or "", family or ""
                )
                if resolved_model is not None:
                    entry["model"] = resolved_model
                # else: inherit by omission — no model field added
            else:
                entry["model"] = model_val  # absolute ID passes through unchanged
        if assign.get("effort"):
            entry["effort"] = assign["effort"]
        resolved[role] = entry
    return resolved


def is_multimodal(resolved: dict, host_platform: str = "claude") -> bool:
    """True iff any role is routed off the host."""
    return any(v.get("platform", host_platform) != host_platform for v in resolved.values())
