---
name: kata-plan-essential
description: >-
  Coarse vertical slices with disjoint ownership and a runnable gate per task. Pick this for PoC-grade plans,
  time-boxed spikes, or any context where a lightweight DAG is enough and full threat modeling is not warranted.
license: Apache-2.0
version: 0.3.1
category: plan
status: beta
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

## Precondition — `DESIGN.md` is frozen

**Dispatched as `plan-author` (DESIGN §4.2, dispatch-authoring spec, KH-T13).** Once `DESIGN.md` is frozen,
the conductor session dispatches this skill as role `plan-author` (`kata_dispatch.build_brief`/`dispatch`,
`tools/kata_dispatch.py:43`/`:219`) — `sandbox="write"`, in its own [[kata-worktree]] worktree — instead of
running it in the conductor's own context (`protocol/orchestration.md`: the conductor gates, it does not
author under its own gate). The conductor applies `protocol/authored-artifact-gate.md`'s six-row rubric
(KH-B42) to the returned `PLAN.md` before writing it into the main tree. If a genuinely unresolved
plan-level question surfaces (not a scoped advisor question — see the escalation section below), this skill
has no `AskUserQuestion` channel and so does not decide it here: it raises the **existing** `human-required`
escalation (`protocol/escalation.md`) and the task parks; the conductor routes it back to a human decision on
the worker's behalf.

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

## Output

**Two-part output contract when dispatched as `plan-author`:** (1) write the `PLAN.md` file to the brief's
one `owned_files` path; (2) emit, as your FINAL message, the completion JSON
`{ "planPath": <path>, "verdict": "ready"|"needs-rework", "deviations": [<str>, ...] }` — the shape
`tools/kata_dispatch.py`'s `normalize()` validates (DESIGN §4.3). `verdict` is your own self-assessment; it
is never a substitute for the conductor actually reading the file (`protocol/authored-artifact-gate.md` row
2). `deviations` names any place you extrapolated beyond, or found ambiguous in, the cited DESIGN — every
entry is independently checked against the DESIGN by the conductor, never accepted at face value (row 5).

## Advice-request escalation (advisor-executor, S-17a — ADVANCED + granted ONLY; runtime-gated)
When dispatched in-harness as a planner-worker, on a **genuinely hard planning question** you MAY request a
scoped Fable-tier advisor consult by raising an **`advice-requested`** escalation (`protocol/escalation.md`) —
question in `decisionNeeded`, async/non-halting (the standard park contract). **Only the conductor dispatches
[[kata-advise]]** ([[kata-orchestrate]] § Advisor consult, event `advisor-planning-consult`); the advice
returns **INLINED VERBATIM** in your redispatch brief under a marked `ADVICE` section. Advice is **advisory,
never authoritative** (S-2) — it never re-decides a LOCKED decision or expands the frozen goal. This affordance
is **ALIVE only on an ADVANCED run with an existing advisor grant**; on any other run the conductor's
`advisor_status` gate NO-FIREs and you proceed unadvised. It rides **every tier variant because tier ≠ mode**
(D24c cross-picking) — runtime-gated by the grant, not by the plan tier. (An advisory consult is not a decision
source: an unresolved *decision branch* still routes back to grilling, never to advice.)
