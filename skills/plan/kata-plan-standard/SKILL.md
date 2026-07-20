---
name: kata-plan-standard
description: >-
  Full vertical-slice plan with disjoint ownership, wave DAG, threat model, phase verification, and SUMMARY.
  The default for any non-trivial build — today's kata-plan at its original depth.
license: Apache-2.0
version: 0.2.0
category: plan
status: beta
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: >-
  adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format
tags:
  - kata/plan
  - kata/spine
  - kata/tier/standard
  - freeze
  - dag
  - file-ownership
  - waves
---
# kata-plan-standard — full vertical-slice plan (default)

**Method:** see [`../kata-plan/RUBRIC.md`](../kata-plan/RUBRIC.md) — the tier-invariant method (vertical-slice
decomposition, disjoint file-ownership, the wave/DAG structure, per-task shape, the quality bar). This file
sets ONLY the depth. When `delivery.shape == "incremental"`, run the **roadmap layer**
([`../kata-plan/ROADMAP.md`](../kata-plan/ROADMAP.md)) first, then apply this depth to the active sprint only.

## Depth contract (Standard)

Run the **full method** as defined in the RUBRIC:

- Decompose into well-scoped vertical slices, each cutting end-to-end through the layers it needs.
- Assign **disjoint file ownership** across all tasks; sequence shared-file contention in the DAG.
- Build the complete `ownership` / `waves` / `depends_on` frontmatter from the partition.
- Every task has a **runnable `verify`** (default-FAIL), **`read_first`**, **`action`** (LOCKED decisions
  quoted verbatim from the DESIGN), and **falsifiable acceptance criteria**.
- Include a **threat model** (trust boundaries + STRIDE-ish register) for every task that adds
  attacker-reachable surface, with the mitigation named.
- Include **phase verification** — the full default-FAIL gate (tests / build / security) + drift-magnet checks.
- Write a per-plan **SUMMARY** on completion.

This is today's `kata-plan` at its original depth — the default for production-quality planning.

## Advice-request escalation (advisor-executor, S-17a — ADVANCED + granted ONLY; runtime-gated)
When dispatched in-harness as a planner-worker, on a **genuinely hard planning question** you MAY request a
scoped Fable-tier advisor consult by raising an **`advice-requested`** escalation (`protocol/escalation.md`) —
question in `decisionNeeded`, async/non-halting (the standard park contract). **Only the conductor dispatches
[[kata-advise]]** ([[kata-orchestrate]] § Advisor consult, event `advisor-planning-consult`); the advice
returns **INLINED VERBATIM** in your redispatch brief under a marked `ADVICE` section. Advice is **advisory,
never authoritative** (S-2) — it never re-decides a LOCKED decision or expands the frozen goal. This affordance
is **ALIVE only on an ADVANCED run with an existing advisor grant**; on any other run the conductor's
`advisor_status` gate NO-FIREs and you proceed unadvised. It rides **every tier variant because tier ≠ mode**
(D24c cross-picking) — runtime-gated by the grant, not by the plan tier.
