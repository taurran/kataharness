# kata-plan — shared method (RUBRIC)

The tier-invariant plan method. The `kata-plan-<tier>` skills set only depth; they all obey this.

---

## Purpose

The plan is the contract [[kata-orchestrate]] enforces. Its job is to make execution *mechanical*: each task
is small, owns a disjoint slice of files, has a runnable gate, and slots into a dependency DAG. **The plan
adds no new decisions** — it only sequences the frozen DESIGN. An unresolved decision here means the grill /
design-doc was incomplete; go back, don't decide in the plan.

## Decompose vertically FIRST, then assign ownership

Decompose by **vertical tracer-slices** — each task cuts through the layers it needs end-to-end (mattpocock
to-issues; [[kata-tdd]] "vertical slices, never horizontal"). THEN take each slice's touched files as its
ownership set. **File-ownership is the isolation mechanism, not the decomposition axis** — never carve
horizontal layer-tasks just to make files disjoint. If two vertical slices genuinely share a file, sequence
them in the DAG (one wave after another) rather than splitting into horizontal layers.

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

## Version-up ownership (existing-repo runs)

When `target.kind == existing`, the ownership partition's universe is the **footprint**, defined as:
**footprint = modified-files (the files the frozen DESIGN says the feature changes/adds) ∪ the
`marginDepth`-hop reverse-dependents of those files** (over `ref ∪ call` edges; default `marginDepth = 1`,
from `kata.config.graph.marginDepth`). The planner computes the reverse-dependents by inverting the forward
edge list in `kata.graph.json` (built by [[kata-graph]]).

- Files **outside the footprint are off-limits — owned by no task.** This is the structural form of "don't
  break other aspects": a worker physically cannot edit beyond the footprint.
- Pre-owning the depth-1 reverse-dependents puts the common "update a caller of what I changed" case
  in-lane, so it does not trigger an escalation.
- Disjoint-ownership, waves, and the DAG rules are otherwise unchanged.
- The regression contract is enforced at evaluation: the **full baseline suite still green + new feature
  tests green** (gated by [[kata-evaluate]] — no new evaluator).

## Per task

- **owns** — its exact file set (a subset of the partition).
- **read_first** — the DESIGN sections, closest code analogs, and conventions to load before editing.
- **action** — what to build, specifically, tied to the LOCKED decisions (quote them; never paraphrase a
  classification or magnitude — restate verbatim so a worker can't drift).
- **verify** — the runnable, default-FAIL command(s) that prove the task done.
- **acceptance_criteria** — falsifiable checks a fresh-context evaluator can confirm.

## Quality bar (the invariant — all tiers must meet this)

- Ownership is provably disjoint (no file in two tasks).
- Every LOCKED decision the task implements is quoted verbatim from the DESIGN.
- Every task has a runnable verify and falsifiable acceptance criteria.
- The DAG is acyclic and every task is reachable.
- Any "reuses / composes / already exists" claim in `read_first` or `action` obeys `protocol/reuse-claims.md` —
  the surface is cited with a concrete `file:line`, or the capability is labeled NEW.

When these hold, **freeze the plan** and hand to [[kata-orchestrate]].

## Incremental delivery — run the roadmap layer first
When `delivery.shape == "incremental"` (`protocol/config.md`), **before** applying this tier method, run the
**roadmap layer** ([`ROADMAP.md`](./ROADMAP.md), sprint-cadence D85): partition the frozen DESIGN into
prime-frame-sized sprints, emit the roadmap artifact, then apply *this* method at the configured tier to **only
the active sprint's** slice, just-in-time. One-shot delivery (the default) ignores the roadmap layer entirely.
