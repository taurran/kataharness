"""Limit fixture — verbatim: "bare-name matching". The GENUINE orphan.

Nothing calls this ``shared_name``. Because graph_gen matches call targets by bare NAME and
takes the first sorted candidate, the call in ``limit_bare_name_caller.py`` — which imports
``limit_bare_name_b`` — is credited to THIS file instead. The genuine orphan therefore looks
wired: a false negative, the direction that actually hides a facade.
"""


def shared_name():
    return "a"
