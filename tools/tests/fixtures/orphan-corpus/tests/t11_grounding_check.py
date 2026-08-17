"""The TEST-ONLY callers that make T11 an orphan rather than a wired engine.

Named ``t11_grounding_check.py``, not ``test_*.py``, so the outer pytest run never collects a
fixture as a real test module. What S1's tests-path filter keys on is the ``tests/`` path
component, which this file has.
"""

from t11_grounding import build_verdict, grounding_verdict


def check_grounding_verdict():
    assert grounding_verdict({"groundsToPlan": "YES"}, True) == "GROUND"


def check_build_verdict():
    assert build_verdict({"groundsToPlan": "YES"}, True, "excerpt")["verdict"] == "GROUND"
