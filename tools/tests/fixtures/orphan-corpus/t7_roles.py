"""T7 mirror — "Host-only roles never route off-host": FACADE.

Live shape: ``kata_roles.resolve_roles:99`` / ``kata_roles.HOST_ONLY_ROLES:55`` have zero
callers; preflight never calls them.

``HOST_ONLY_ROLES`` is a module constant here exactly as it is live. graph_gen extracts
function/class definitions only, so the constant is not a symbol node and cannot appear in an
S1 finding — T7's corpus finding is ``resolve_roles``.
"""

HOST_ONLY_ROLES = ("orchestrator", "evaluator")


def resolve_roles(requested):
    """Zero callers anywhere in the corpus — the T7 orphan."""
    return sorted(set(requested) - set(HOST_ONLY_ROLES))
