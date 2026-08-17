"""T7's would-be caller — WIRED, and that is the point.

``run_preflight`` is called from ``wired_pipeline.py`` (a non-test file), so S1 must report it
CLEAR. The T7 facade is not "preflight is dead"; it is "preflight is alive and never calls
``resolve_roles``".
"""


def run_preflight(config):
    return {"ok": bool(config)}
