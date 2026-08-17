"""T6 mirror — "Nothing builds from a draft (D169)": FACADE.

Live shape: ``kata_restore.assert_frozen:557`` is called by ``kata_dispatch.build_brief:80``
and by nothing else; ``build_brief`` itself has zero production callers. Both are orphans.
"""


def assert_frozen(plan_path):
    """Same-file caller only — graph_gen never emits a self-file ref edge."""
    return str(plan_path).endswith("PLAN.md")


def build_brief(plan_path):
    """The chokepoint nothing in production dispatches through."""
    assert_frozen(plan_path)
    return {"plan": plan_path}
