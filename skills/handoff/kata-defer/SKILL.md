---
name: kata-defer
description: >-
  Capture, don't drift. During a run, append out-of-scope-but-worth-keeping items to DEFERRED.md and any spec
  assumption made without a human grill to ASSUMPTIONS.md, instead of silently dropping them or scope-creeping
  the frozen plan. Both surface at the gate/handoff. Use as the grill-skip autonomous-floor safety net (D71) and
  as the in-loop deferral valve (D42). Invoke when a worker/orchestrator hits something off-plan but real.
license: Apache-2.0
version: 0.1.0
category: handoff
status: beta
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: >-
  new (KataHarness original, D42/D43 GB9) — the structural complement to the no-drift spine; assumption-log role
  added by D71 (Priming-and-Grill autonomous floor)
tags:
  - kata/handoff
  - kata/module/defer
  - defer
  - assumption-log
  - no-drift
---
# kata-defer — capture off-plan reality at the boundary, never drift

The **pressure-release valve** that makes one-shot = no-churn sustainable. The frozen plan does not drift
(spine #1/#2); but real, off-plan things surface mid-run — a worth-keeping idea, or an assumption the loop had
to make because no human grilled it. `kata-defer` gives both a durable home so they are **parked, not lost, and
not scope-crept into the frozen plan.** Optional module (`kata/module/defer`, D43) — additive, not spine.

## Two artifacts, two roles (both run-scoped, both surfaced at gate/handoff)

### 1. `DEFERRED.md` — out-of-scope parking (D42)
During a run, any out-of-scope-but-worth-keeping item (nice-to-have, post-processing candidate,
deferred-for-a-reason discovery a worker hit in-lane) is **appended** here rather than dropped or crept into the
frozen plan. This is the home the [[kata-orchestrate]] escalate predicate points workers to: *"record
out-of-scope discoveries as a deferral note and keep going."*

### 2. `ASSUMPTIONS.md` — the autonomous-floor safety net (D71)
The autonomous-reliability floor is on for **every** run, but it does the most work on a **grill-skip rung**
(`tiers["kata-grill"] == "skip"` — no grill ran, the priming prompt frozen as-is) or a low-grill run, where
ambiguity is resolved **in-loop without a human**. Every spec assumption the loop has to make to proceed is
**logged here with its provenance** (which prompt gap forced it, what was assumed, what the alternatives were). This is how the autonomous floor stays honest: misalignment with the designer's intent is
**caught at the boundary** (gate/handoff) without an up-front grill. It is the in-loop, without-human end of the
**grill ↔ RS ambiguity-resolution spectrum** (D71): the up-front-with-human grill and the in-loop RS research
subagent shore up alignment from the other ends; the assumption log makes whatever the loop *assumed* visible
for human review. (RS itself lands in the loop-cognition phase; the assumption log is the floor's available-now
backstop.)

## Append discipline
- **Append-only, checkpoint-as-you-go.** Write each entry the moment it arises (like the grill decision ledger)
  so an interrupted run loses nothing. One entry = item/assumption · why · provenance (task-id, the prompt gap
  or discovery) · optional suggested follow-up.
- **Never edit the frozen plan from here.** Capturing an item is the *alternative* to drifting — if acting on it
  would require touching the frozen plan or an unowned file, it is escalate-or-defer, never silent edit.
- Both files are run-scoped artifacts (Obsidian-readable, git-committed with the run).

## Surfacing (the whole point)
- **At the gate:** [[kata-evaluate]] grades `ASSUMPTIONS.md` (its rubric item 8) before PASS — an assumption
  that contradicts the priming prompt / frozen spec is **NEEDS_WORK**, not a footnote (especially on a skip run).
  The orchestrate Final gate points the evaluator at it. *(This is wired, not asserted — the gate actually reads
  it.)*
- **At handoff:** [[kata-handoff]] compiles both files into the handoff so the human/next session sees every
  parked item and every autonomous assumption. They feed the project backlog and [[kata-improve]].
