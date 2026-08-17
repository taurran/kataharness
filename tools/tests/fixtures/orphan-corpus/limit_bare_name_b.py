"""Limit fixture — verbatim: "bare-name matching". The REAL call target.

``limit_bare_name_caller.py`` imports and calls THIS ``shared_name``, yet bare-name matching
credits ``limit_bare_name_a.py`` (first sorted candidate), so this genuinely-called symbol is
reported unwired: the false-positive half of the same defect.
"""


def shared_name():
    return "b"
