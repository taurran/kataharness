"""A test caller for an ALREADY-wired symbol.

Proves the tests-path filter subtracts test callers without inventing an orphan:
``helper_wired`` keeps its non-test caller in ``wired_pipeline.py`` and stays CLEAR.
"""

from wired_helper import helper_wired


def check_helper_wired():
    assert helper_wired(1) == {"wired": 1}
