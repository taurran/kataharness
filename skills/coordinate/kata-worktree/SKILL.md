---
name: kata-worktree
description: >-
  Per-owner git worktree isolation for concurrent, plan-faithful execution. Use when an orchestrator must
  run multiple task-owners in parallel without collision, or build on a branch without disturbing a
  human's active checkout. Covers creating/removing worktrees, per-task branches, clean disjoint merges,
  and the cross-repo rule (isolate the TARGET repo, not the harness repo). Also carries base-SHA-pinned
  provisioning outside the repo root and the arm-is-a-run rule for child runs.
license: Apache-2.0
version: 0.2.0
category: coordinate
status: beta
agnostic: true
cost-weight: 1
allowed-tools: [Bash, Read]
source: adapted-from CryptoPortfolioPlanner worktree proof (LESSONS-LEARNED L2/L3)
tags:
  - kata/coordinate
  - kata/spine
  - worktree
  - isolation
  - git
---

# kata-worktree — isolate every concurrent owner

Concurrent code agents corrupt shared state ([[LESSONS-LEARNED]] L3) and clobber each other's files. Git
worktrees give each owner a private working tree on its own branch while sharing one object store — the
right isolation primitive ([[LESSONS-LEARNED]] L2).

## Rules
- **One worktree per concurrent task-owner.** Sequential single-task waves may share one integration worktree.
- **Never disturb the human's checkout.** Do not `git checkout` in a working tree someone else is using.
  Create *new* worktrees instead; the human's active branch stays untouched.
- **Isolate the TARGET repo, not the harness repo.** When the orchestrator's session repo differs from the
  repo being built, create the worktree in the *target* repo by absolute path. (Generic "worktree the
  current repo" helpers will isolate the wrong repo.)
- **Disjoint file ownership = conflict-free merge.** If the plan's partition is truly disjoint, task
  branches merge into the integration branch with no conflicts. A conflict means ownership was violated —
  stop and escalate, don't hand-resolve.
- **Pin line endings** (`.gitattributes eol=lf`) so build/handoff sizes stay deterministic
  ([[LESSONS-LEARNED]] L1).

## Pinned worktrees — the base SHA is structural, not a convention

**The provisioner pins the base SHA into `git worktree add` itself.** Two independent provisioners
have produced a wrong base when the base was left implicit, so "branch off the current tip" is not
an acceptable instruction — the SHA is written into the command.

- **Provision outside the repo root**, at a sibling path (e.g. `<REPO_PARENT>/_kata_wt/<run>/<task>`),
  not at a path nested inside the repo being built. **Outside-the-root placement is load-bearing,
  not cosmetic:** the graph backend has no worktree exclusion, so an embedded worktree is walked as
  part of the repo and poisons every count derived from it (file counts, blast radius, proof-run
  measurements).
- **Every brief names the pin, and the worker verifies it before touching anything.** The worker's
  step 0 is: `git rev-parse HEAD` MUST equal the pinned base SHA in the brief, and
  `git status --porcelain` MUST be empty. Both values are reported back. **A mismatch is a STOP and
  an ESCALATE, never a "fix"** — a worker who quietly re-bases has silently changed what the gate is
  measuring.
- The pin is what makes disjoint ownership provable: two task branches cut from the same recorded
  SHA merge on file-ownership alone.

## Child runs — an arm IS a run (the two-tier law)

Not every fan-out is a worktree of the same run. The classification rule is written, not judged
case by case:

| Shape | What it gets |
|---|---|
| **In-wave tasks** of one plan | lines on the **parent's** cursor; one worktree + task branch each |
| **Bakeoff arms · backlog-burn wave-loops · kitchen bakes** | a **CHILD RUN**: its own `runId`, its own cursor, its own worktree root, and a `parent-run:` header |

**One cursor per run stays true at every node of the tree** — that is what "arm = run" means. A
child run's worktree is not a shortcut around run identity; it is where a separate run lives.

- **The arm registry is FREEZE-MINTED.** The frozen PLAN (or benchmark definition) carries the whole
  tree *before* any dispatch: `arm_label → pre-minted child runId → worktree root → parent-close
  policy`. Provisioning reads the registry, which is what makes spawn **exactly-once** across a
  resume — a resumed run re-reads the registry rather than minting a second arm at the same label.
- **Per-arm parent-close policy is declared, one of `cancel | park | abandon-with-rendezvous`.**
  `abandon-with-rendezvous` is **MANDATORY across wave rollovers** — an arm that outlives its
  parent without a named successor rendezvous is the hazard this field exists to prevent.
- **Dispatcher-witnessed SPAWN / DOWN.** The parent's seam writes both: `mint()` writes the SPAWN
  line, and the parent's seam writes the `DOWN` record by reading the child cursor's terminal state
  at the next parent seam act. **Children NEVER write the parent's log.** Unrendezvoused orphans are
  reaped at seam init (`kata_dispatch.run_start`).
- **A re-loop of a wave is a SIBLING CHILD:** same `parent-run:` (the tree — roll-up folds walk this
  edge), with `prev-run:` naming the failed sibling (history — iteration walks this edge). A
  root-level re-loop has no parent by definition and carries a `prev-run:` chain only.
- **At parent close, arms are killed unless their close policy names a successor rendezvous**, and a
  closed run's arm commits are **quarantined** — never merged into graded results.
- **Child runs NEVER rewrite the committed `kata.config`;** per-arm variation lives only in the arm
  registry, so a fan-in cannot conflict on config by construction.
- **Fan-in is mechanical only.** Merge-parents plus the `Kata-Run:` / `Kata-Arm:` trailers, fail-closed
  on conflict — **no evil merges**. A merge commit that quietly changes content is a lie in git
  history. Bakeoff selection is a recorded supersede (a `DECISION` naming winner + losing runIds,
  `-s ours`-shaped), never content blending; the human picks the version.

## Recipe
`<WT_ROOT>` is **outside `<TARGET_REPO>`**, and `<BASE_SHA>` is the pinned, recorded fork point —
both spelled out in every brief.

```bash
# integration branch off the agreed fork point (no checkout in the main tree):
git -C <TARGET_REPO> branch <integration-branch> <BASE_SHA>
git -C <TARGET_REPO> worktree add <WT_ROOT>/integration <integration-branch>

# one worktree + task branch per concurrent owner in a wave — SHA pinned into the command:
git -C <TARGET_REPO> worktree add <WT_ROOT>/t2 -b <task/t2> <BASE_SHA>
git -C <TARGET_REPO> worktree add <WT_ROOT>/t3 -b <task/t3> <BASE_SHA>

# worker step 0, in ITS OWN worktree — both values reported back, mismatch ⇒ STOP:
git -C <WT_ROOT>/t2 rev-parse HEAD        # MUST equal <BASE_SHA>
git -C <WT_ROOT>/t2 status --porcelain    # MUST be empty

# after a task is gated green, integrate (run from the integration worktree):
git -C <WT_ROOT>/integration merge --no-ff <task/t2>
git -C <WT_ROOT>/integration merge --no-ff <task/t3>   # disjoint files → clean

# teardown when the run is done:
git -C <TARGET_REPO> worktree remove <WT_ROOT>/t2
git -C <TARGET_REPO> worktree prune
```

## Hand back to the orchestrator
Report each worktree path + branch + **pinned base SHA** on the cursor ([[kata-cursor]]) so the
orchestrator can route subagents to exact paths and track ownership. For a child run, report its
`runId` and its arm-registry label alongside the path — the worktree root and the run identity are
recorded together or the arm is not traceable.
