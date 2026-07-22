# DEFERRED — parked designed work (kata-defer ledger)

> PD-1 sanctioned deferral path: every entry here is operator-visible, graded at the gate,
> and surfaced at handoff. An entry is closed by the run that builds it (link the record).

## DEF-1 — kata_preflight._default_runner stderr widening · OPEN (2026-07-21)
- **What:** `tools/kata_preflight.py:397-407` `_default_runner` returns `(returncode, stdout)`
  — same stderr-discard class as the kata_dispatch defect fixed by the dispatch-stderr-fix run.
- **Why deferred:** the quota-resilience classifier (its own grilled run,
  `.planning/specs/quota-resilience/REQUIREMENT.md`) decides what preflight signal it consumes;
  widening now is scope creep on a surgical fix. Grill record:
  `.planning/specs/dispatch-stderr-fix/GRILL-LEDGER.md` D4 (operator-approved).
- **Owed to:** the quota-resilience Tier 1+2 run.
