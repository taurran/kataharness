---
date: 2026-06-19
spec: testing-model
status: BRIEF — pre-grill, not frozen. A captured gap; the build (if greenlit) needs its own grill → DESIGN → PLAN.
order: 3 of 3 (future-gap sequence — a refinement; integrates with the routing layer)
tags: [brief, future-gap, testing, evaluation, model-routing, quality]
---

# Dedicated Testing Model — assessment + quick plan

> **Quick plan brief.** This one is genuinely an **assessment first**: should KataHarness route its
> testing/validation work to a **purpose-specific model**, distinct from the general orchestrator/worker model?

## Why (the gap)
The loop's quality spine — [[kata-evaluate]] (default-FAIL gate), [[kata-tdd]], [[kata-review]] — currently runs
on the same model class as the build. A **testing-specialized model** could (a) write more adversarial,
higher-coverage tests, (b) judge "done" with less of the build agent's optimism, and (c) be cheaper to run
often. This may meaningfully strengthen the default-FAIL guarantee (spine #4). It may also be unnecessary if a
fresh-context same-model evaluator already suffices (today's design's bet). **Assess before building.**

## Assessment questions to answer first
- Does a separate testing model measurably catch more than the existing **fresh-context, no-write** evaluator
  (which already removes author bias by construction)? Where's the evidence/A-B?
- Which steps benefit most — **test authoring** (kata-tdd), the **gate** (kata-evaluate), the **adversarial
  review** (kata-review), or all three?
- Cost/latency trade: a cheaper specialized model run more often, vs. a strong general model run once.

## Scope IF greenlit
- A configurable **testing/eval model** binding (e.g. `effort`/routing per quality component) so the gate, TDD,
  and review can each be pinned to a chosen model — **not** hard-coded.
- Keep the **structural invariants** intact: default-FAIL, fresh-context, no-write, never-tiered (D33). The
  *model* changes; the *contract* does not.
- A way to record which model gated a run (reproducibility — extends `kata.config.skillVersions`/effort
  provenance).

## Modularity / key constraints
- Must compose with [[multi-model-orchestration]] — the testing model is just a **routed component** in that
  layer, not a parallel mechanism. (If #2 is built well, this is largely a *config + assessment*, not new
  machinery.)
- Must not weaken any existing gate; a testing model is additive rigor, never a bypass.

## Dependencies & sequencing
- **Leans on [[multi-model-orchestration]]** for the routing mechanism; this brief mostly adds the
  **assessment** + the quality-component binding + provenance.
- Lowest urgency of the three — a sharpening pass once the platform/model layer exists.

## Out of scope (for now)
Procuring/benchmarking specific models; any change to the evaluation *contract* (only the model behind it).
