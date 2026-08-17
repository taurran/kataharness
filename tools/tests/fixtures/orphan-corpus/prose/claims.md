# S2 fixture — reuse claims with and without resolvable citations

A verified claim: this **reuses** the existing contract-gate writer (`t8_contract_gate.py:8`),
whose surface is present at the cited line.

A phantom claim: this **composes** the existing telemetry ledger writer to emit run rows.
No `file:line` is cited anywhere near it, so the surface was never confirmed.

Another phantom, second trigger form: the orchestrator already writes the fact table for every
gate, so nothing more is needed here.

A dangling citation: this **reuses** the resolver at `phantom_module.py:42` — the module does not
exist in this corpus at all.

An out-of-range citation: this **reuses** the writer at `t8_contract_gate.py:9999`; the file is
real, the line is not.

The D-5 case (existence is not support): this **reuses** the lost-run detector at
`t10_restore.py:1`. Line 1 exists and resolves, and it is the module docstring's opening quote —
it does not define, mention, or support a lost-run detector. B5/S2 attest EXISTENCE only; whether
a cited line supports the claim stays judgment, routed to grounding.
