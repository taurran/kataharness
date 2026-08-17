"""T8 mirror — "The contract gate ran": FACADE.

Live shape: ``contract-gate.json`` is producer-only; zero were ever written in a real run.
"""


def write_contract_gate(kata_dir, rows):
    """Producer with zero callers."""
    return f"{kata_dir}/contract-gate.json:{len(rows)}"
