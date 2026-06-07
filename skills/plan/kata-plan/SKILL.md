---
name: kata-plan
description: >-
  Turn a frozen DESIGN into a task-level execution plan with DISJOINT file-ownership, a wave/dependency DAG,
  and per-task acceptance criteria — the structure that makes no-drift, concurrent, plan-faithful execution
  possible. Use after the design is frozen, before dispatching any worker.
version: 0.1.0
category: plan
status: experimental
agnostic: true
allowed-tools: [Read, Grep, Glob, Write, Edit]
model: opus
source: adapted-from mattpocock/skills {to-issues} + GSD plan-phase + BMAD role-agents + CPP plan format
tags: [plan, freeze, file-ownership, dag, waves]
---

# kata-plan — decompose into ownable, gateable, drift-proof tasks

The plan is the contract [[kata-orchestrate]] enforces. Its job is to make execution *mechanical*: each task
is small, owns a disjoint slice of files, has a runnable gate, and slots into a dependency DAG. **The plan
adds no new decisions** — it only sequences the frozen DESIGN. An unresolved decision here means the grill /
design-doc was incomplete; go back, don't decide in the plan.

## The load-bearing property: DISJOINT file ownership
Partition the work so **no file is owned by two tasks.** This is what lets concurrent workers run in isolated
worktrees and merge with zero conflicts ([[kata-worktree]]) — and what makes "stay in your lane" a checkable
rule rather than a hope. If two tasks genuinely must touch one file, either merge them into one task or split
the file; never let ownership overlap.

## Structure (frontmatter the orchestrator reads)
```yaml
ownership:      { T1: [files...], T2: [files...], ... }   # disjoint across all tasks
waves:          { wave1: [T1], wave2: [T2, T3], ... }     # parallelizable sets
depends_on:     { T2: [T1], T3: [T1], T4: [T1, T2] }      # the DAG
```
Derive waves from the DAG: a wave is the set of tasks whose dependencies are all satisfied and whose file
sets are disjoint. Sequential single-task waves are fine; parallel waves are the payoff.

## Per task
- **owns** — its exact file set (a subset of the partition).
- **read_first** — the DESIGN sections, closest code analogs, and conventions to load before editing.
- **action** — what to build, specifically, tied to the LOCKED decisions (quote them; never paraphrase a
  classification or magnitude — restate verbatim so a worker can't drift).
- **verify** — the runnable, default-FAIL command(s) that prove the task done.
- **acceptance_criteria** — falsifiable checks a fresh-context evaluator can confirm.

## Also include
- A **threat model** (trust boundaries + the STRIDE-ish register) for any task that adds attacker-reachable
  surface, with the mitigation named.
- **Phase verification** — the full default-FAIL gate (tests/build/security) + the drift-magnet checks.
- A pointer to write a per-plan SUMMARY on completion.

## Quality bar
- Ownership is provably disjoint (no file in two tasks).
- Every LOCKED decision the task implements is quoted verbatim from the DESIGN.
- Every task has a runnable verify and falsifiable acceptance criteria.
- The DAG is acyclic and every task is reachable. Then **freeze the plan** and hand to [[kata-orchestrate]].
