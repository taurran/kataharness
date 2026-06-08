---
name: kata-worktree
description: >-
  Per-owner git worktree isolation for concurrent, plan-faithful execution. Use when an orchestrator must
  run multiple task-owners in parallel without collision, or build on a branch without disturbing a
  human's active checkout. Covers creating/removing worktrees, per-task branches, clean disjoint merges,
  and the cross-repo rule (isolate the TARGET repo, not the harness repo).
license: Apache-2.0
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Bash, Read]
source: adapted-from CryptoPortfolioPlanner worktree proof (LESSONS-LEARNED L2/L3)
tags:
  - kata/coordinate
  - kata/spine
  - worktree
  - isolation
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

## Recipe
```bash
# integration branch off the agreed fork point (no checkout in the main tree):
git -C <TARGET_REPO> branch <integration-branch> <fork-point>
git -C <TARGET_REPO> worktree add <WT_ROOT>/integration <integration-branch>

# one worktree + task branch per concurrent owner in a wave:
git -C <TARGET_REPO> worktree add <WT_ROOT>/t2 -b <task/t2> <integration-branch>
git -C <TARGET_REPO> worktree add <WT_ROOT>/t3 -b <task/t3> <integration-branch>

# after a task is gated green, integrate (run from the integration worktree):
git -C <WT_ROOT>/integration merge --no-ff <task/t2>
git -C <WT_ROOT>/integration merge --no-ff <task/t3>   # disjoint files → clean

# teardown when the run is done:
git -C <TARGET_REPO> worktree remove <WT_ROOT>/t2
git -C <TARGET_REPO> worktree prune
```

## Hand back to the orchestrator
Report each worktree path + branch on the board ([[kata-board]]) so the orchestrator can route subagents to
exact paths and track ownership.
