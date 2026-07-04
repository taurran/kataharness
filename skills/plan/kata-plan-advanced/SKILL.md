---
name: kata-plan-advanced
description: >-
  Exhaustive plan with finer-grained slicing, an explicit STRIDE threat register, richer falsifiable
  acceptance criteria, and a per-task risk note. Use when a missed ownership gap or unmitigated threat has
  very high downstream cost — e.g., security-critical features or architecturally load-bearing phases.
license: Apache-2.0
version: 0.1.2
category: plan
status: experimental
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
