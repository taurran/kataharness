---
name: kata-plan-essential
description: >-
  Coarse vertical slices with disjoint ownership and a runnable gate per task. Pick this for PoC-grade plans,
  time-boxed spikes, or any context where a lightweight DAG is enough and full threat modeling is not warranted.
license: Apache-2.0
version: 0.1.0
category: plan
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: >-
  adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format
tags:
  - kata/plan
  - kata/spine
  - kata/tier/essential
  - freeze
  - dag
  - file-ownership
  - waves
---
# kata-plan-essential — coarse vertical-slice plan

**Method:** see [`../kata-plan/RUBRIC.md`](../kata-plan/RUBRIC.md) — the tier-invariant method (vertical-slice
decomposition, disjoint file-ownership, the wave/DAG structure, per-task shape, the quality bar). This file
sets ONLY the depth. When `delivery.shape == "incremental"`, run the **roadmap layer**
([`../kata-plan/ROADMAP.md`](../kata-plan/ROADMAP.md)) first, then apply this depth to the active sprint only.

## Depth contract (Essential)

Produce **coarse vertical slices** with disjoint file ownership and a dependency DAG — enough to run execution
without drift:

- Decompose into the **minimum set of vertical slices** that covers the frozen DESIGN without leaving any
  LOCKED decision unassigned to a task.
- Assign **disjoint file ownership** (the load-bearing property — never skip this).
- Build the **wave/DAG** (`ownership`, `waves`, `depends_on` frontmatter) from the ownership partition.
- Every task MUST carry: **`owns`** (disjoint file set), **`action`** (quoting every LOCKED decision it
  implements verbatim from the DESIGN — the no-drift line, **non-waivable at any tier, D33**), **`verify`**
  (runnable, default-FAIL), and **falsifiable `acceptance_criteria`**. `read_first` is present but may be
  coarse at Essential tier. Dropping `action` or omitting verbatim decision quotes is never permitted
  regardless of tier — a tier may reduce slice granularity but may NOT remove the per-task `action`/
  verbatim-decision fields.
- **Skip the threat model** unless attacker-reachable surface is immediately obvious from the DESIGN (e.g., a
  new public endpoint, auth change, or data-trust boundary). If skipped, note it explicitly.
- No SUMMARY required.

**Explicitly does NOT** do finer-grained slice decomposition, STRIDE threat register, or per-task risk notes —
those are Standard and Advanced. Mark the plan header as Essential-tier so downstream consumers know the
coverage level.
