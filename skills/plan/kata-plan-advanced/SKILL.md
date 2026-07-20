---
name: kata-plan-advanced
description: >-
  Exhaustive plan with finer-grained slicing, an explicit STRIDE threat register, richer falsifiable
  acceptance criteria, and a per-task risk note. Use when a missed ownership gap or unmitigated threat has
  very high downstream cost — e.g., security-critical features or architecturally load-bearing phases.
license: Apache-2.0
version: 0.2.0
category: plan
status: beta
agnostic: true
cost-weight: 4
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: >-
  adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format
tags:
  - kata/plan
  - kata/spine
  - kata/tier/advanced
  - freeze
  - dag
  - file-ownership
  - waves
---
# kata-plan-advanced — exhaustive plan with threat register

**Method:** see [`../kata-plan/RUBRIC.md`](../kata-plan/RUBRIC.md) — the tier-invariant method (vertical-slice
decomposition, disjoint file-ownership, the wave/DAG structure, per-task shape, the quality bar). This file
sets ONLY the depth. When `delivery.shape == "incremental"`, run the **roadmap layer**
([`../kata-plan/ROADMAP.md`](../kata-plan/ROADMAP.md)) first, then apply this depth to the active sprint only.

## Depth contract (Advanced)

Run the **full Standard-depth method (see the RUBRIC)** **plus**:

- **Finer-grained slicing.** Where Standard might group related layers into one task, Advanced breaks them
  into smaller, more precisely scoped slices — each task's ownership set is tighter and its verify gate more
  surgical.
- **Explicit STRIDE threat register.** For every task that touches any attacker-reachable surface, produce a
  full STRIDE pass (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of
  Privilege), name each mitigation, and confirm it is reflected in the task's action or a sequenced follow-on
  task.
- **Richer falsifiable acceptance criteria.** Each task's `acceptance_criteria` must include at least one
  negative assertion (what must NOT be true if the task is done correctly) in addition to the positive ones.
- **Per-task risk note.** After each task's acceptance criteria, add a one-line `risk:` field naming the
  highest-residual risk if this task is implemented incorrectly and what the blast radius is.

The Advanced tier is strictly a superset of Standard — it produces the same artifact types (plan frontmatter +
per-task structure + SUMMARY) but with higher coverage, tighter slicing, and an explicit threat register.

## Advice-request escalation (advisor-executor, S-17a — ADVANCED + granted ONLY; runtime-gated)
When dispatched in-harness as a planner-worker, on a **genuinely hard planning question** you MAY request a
scoped Fable-tier advisor consult by raising an **`advice-requested`** escalation (`protocol/escalation.md`) —
question in `decisionNeeded`, async/non-halting (the standard park contract). **Only the conductor dispatches
[[kata-advise]]** ([[kata-orchestrate]] § Advisor consult, event `advisor-planning-consult`); the advice
returns **INLINED VERBATIM** in your redispatch brief under a marked `ADVICE` section. Advice is **advisory,
never authoritative** (S-2) — it never re-decides a LOCKED decision or expands the frozen goal. This affordance
is **ALIVE on an ADVANCED run with an existing advisor grant** (advanced is this tier's typical mode, but the
gate is still the grant, not the tier); on an ungranted run the conductor's `advisor_status` gate NO-FIREs and
you proceed unadvised. It rides **every tier variant because tier ≠ mode** (D24c cross-picking) — runtime-gated
by the grant, not by the plan tier.
