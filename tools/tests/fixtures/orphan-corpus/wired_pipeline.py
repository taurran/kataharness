"""Negative control + the out-of-graph-entry-point limit fixture.

``run_pipeline`` wires ``helper_wired`` and ``run_preflight``. It is itself invoked only by
``entrypoints/run.sh`` — which graph_gen never scans (it globs ``*.py``) — so S1 reports
``run_pipeline`` unwired. That FALSE POSITIVE is the verbatim limit "entry points outside the
graph look dead", and it is pinned by a test rather than merely prosed.
"""

from t7_preflight import run_preflight
from wired_helper import helper_wired


def run_pipeline(config):
    return helper_wired(run_preflight(config))
