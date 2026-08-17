"""Negative control — genuinely wired.

``helper_wired`` is called from ``wired_pipeline.py`` (non-test) AND from
``tests/wired_helper_check.py``. S1 must report it CLEAR: a test caller neither creates nor
destroys wiring. A detector that flags this is vacuous.
"""


def helper_wired(payload):
    return {"wired": payload}
