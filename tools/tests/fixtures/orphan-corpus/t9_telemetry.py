"""T9 mirror — "Runs are accounted (telemetry, counters, ledger rows)": FACADE.

Live shape: a 71 KB engine with zero callers; the burns produced zero rows.
"""


def build_ledger_row(run_id, kind):
    return {"kind": kind, "runId": run_id}


def record_dispatch(run_id):
    """Same-file caller of build_ledger_row — no self-file ref edge, and itself uncalled."""
    return build_ledger_row(run_id, "dispatch")
