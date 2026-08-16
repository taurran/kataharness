---
spec: trust-model
artifact: evidence dossier 6 — fan-out / merge / async patterns survey (TM-C7)
date: 2026-08-16
provenance: dispatched research agent (six external lenses + in-repo ground truth, URLs and
  file:line inline), committed verbatim-in-substance by the conductor. Two flagged soft claims:
  the GH-Actions job-output clobber wording is community-corroborated rather than docs-verbatim;
  Temporal parent-child links are history-derived (ParentWorkflowId as a search attribute
  unconfirmed).
baseline: grill/dispatch-seam @ 302b7f1
---

# TM-C7 survey — parallel branched fan-out for the cursor

## External lenses (steal / avoid per system)

1. **LangGraph** (Send/supersteps/reducers): branches are ephemeral (no addressable identity —
   AVOID); **declared reducer per channel is the merge, and an undeclared concurrent write is a
   fail-loud `InvalidUpdateError`** (STEAL); pending-writes let resume re-run only the failed
   branch (STEAL).
2. **Temporal** (child workflows): children are first-class — own Workflow/Run ID, **own event
   history; the parent log holds only spawn/terminal events** (STEAL — this IS tree-of-runs at
   scale); ID conflict policies give exactly-once spawn on retry (STEAL); **Parent Close Policy**
   per child: TERMINATE/REQUEST_CANCEL/ABANDON (STEAL the vocabulary, AVOID default-TERMINATE);
   history hard limits (warn 10,240, **kill 51,200 events/50 MB**) are the empirical case against
   one shared log; **Continue-As-New severs parent-child links** — the BBM-12 wave-per-loop
   analog hazard.
3. **Airflow/Dagster** (declared DAGs, dynamic mapping): identity assigned at fan-out
   (`map_index`/`mapping_key`) + **storage keyed by that identity so siblings physically cannot
   clobber** (STEAL); single-arm retry reusing sibling results (STEAL); explicit join-policy
   vocabulary (trigger rules / `.collect()`) (STEAL); AVOID skip-cascades through all_success
   joins.
4. **Erlang/OTP supervision trees** (the Kitchen-async blueprint): monitors — the parent gets one
   **DOWN message carrying the termination reason** (STEAL as the arm-terminal event); Registry
   identity auto-purged on death (no stale identity); restart-intensity escalation = the
   reroll-ceiling analog; **recursive supervision = "fan out the fan-out"**; awaited-shutdown
   protocol = the run-teardown contract. Nothing structural to avoid.
5. **GitHub Actions matrix**: pre-declared fan-out + **per-arm-named artifacts + explicit merge
   step** (STEAL — upload-artifact v4 went unique-named precisely because same-name append
   corrupted); fail-fast dial per fan (STEAL); **matrix job outputs = one shared namespace,
   last-writer-wins — the clobber counter-example** (AVOID any unkeyed shared output channel).
6. **Git-native merge**: merge-commit parents + trailers = the immutable, (iv)-durable fan-in
   record; **octopus refuses any conflicting N-way merge — the disjoint-ownership contract as a
   mechanism**; `-s ours` = record-parents-take-one-tree (the honest bakeoff-selection shape;
   never confuse with `-X ours` content blending); AVOID the **evil merge** (changes in no
   parent — PD-2 violation in git form) and Cthulhu-scale octopi.

## In-repo ground truth + collision analysis

Already ruled/built: the frontier predicate (waves are a derived view — `kata-orchestrate:315-324`);
the deferred concurrent multi-arm driver with its arm→clone-root registry shape (`:304-312`, D1);
bakeoff config + D24d ONE-dispatcher-as-data constraint (`MODES-DESIGN.md:94-98`); BBM-2
fail-closed partition; BBM-12 wave-per-loop + cursor-as-interruption-token; board append-only +
**the flagged clock-trust hazard** (`board.md:52-55`); worktree ownership ("a conflict means
ownership was violated — stop and escalate").

Collisions resolved: (1) **D135 holds iff arm = run** — one cursor per run stays true at every
tree node; N cursors for ONE run would be the forbidden journals — rule the equivalence
explicitly. (2) The shared in-run board stays for in-wave workers; the tree applies at RUN level
— per-arm cursors dissolve the cross-machine seq contention. (3) Concurrency evidence becomes a
cross-cursor fold ordered by (runId, seq) + parent fold-order — closing the clock-skew flag.
(4) **BBM-12 wave rollover = the Continue-As-New hazard**: Kitchen bakes spanning wave boundaries
must be ABANDON-with-rendezvous via the registry + `prev-run:` chain. (5) D24d honored: the tree
driver is data in the frozen PLAN/registry, consumed by the one orchestrator.

## Verdict

**Tree-of-runs is correct, with one mandatory refinement: TWO-TIER.** In-wave tasks stay as lines
on the parent's cursor (Temporal-activity class); only bakeoff arms, Backlog Burn wave-loops, and
Kitchen bakes mint child runs (own runId + cursor + worktree, `parent-run:` header). All five
operator requirements are met by the composed elements below; shared-multi-writer and
one-run-many-cursors alternatives each fail at least two requirements outright.

## The eight design elements (ranked; source → cost)

1. **Two-tier fan-out law** — task-lines vs child-runs, written classification rule (Temporal
   activities-vs-children). Cost: a rule, or every task inflates into a run.
2. **Freeze-minted arm registry** — the frozen PLAN/benchmark_def carries the whole tree before
   dispatch: arm_label → pre-minted child runId → worktree root → parent-close policy; resume
   reads the registry (exactly-once spawn). (GH matrix + Temporal Use-Existing + `:304-312`
   precedent.) Cost: registry schema + one freeze-gate check.
3. **Dispatcher-witnessed lifecycle events on the PARENT cursor** — seam mint appends SPAWN;
   arm terminal appends a DOWN-with-reason event; children never write the parent's log. (OTP
   monitors + TM-B4/C4.) Cost: one append per arm.
4. **Per-arm parent-close policy** — cancel | park | abandon-with-rendezvous, declared in the
   registry; wave boundaries re-link abandoned bakes. (Temporal PCP + OTP shutdown + BBM-11.)
   Cost: one field + a resume-time orphan pass.
5. **Declared fold reducers; bounded child summaries only** — undeclared concurrent merge is a
   fail-loud refusal. (LangGraph + Hermes distill.) Cost: a reducer table beside the grammar.
6. **Ordering = (runId, seq) + parent fold-order as order-of-record** — cross-arm wall-clock
   never load-bearing; closes board.md:52-55. Cost: rewrite the K3 concurrency snippet.
7. **Fan-in as merge-parents + trailers** — `--no-ff` (octopus only for provably disjoint
   waves), fail-closed on conflict; merge commit carries `Kata-Run:` + new `Kata-Arm:` trailer —
   the (iv)-durable fan-in record. Cost: near zero.
8. **Bakeoff selection-merge as recorded supersede** — a DECISION event records winner + losing
   runIds (human version-select per standing rule); any losing-arm merge is `-s ours`-shaped,
   never content blending. Cost: discipline.

## Named hazards (each with its answering pattern)

Orphan-kill/leak at parent death or wave rollover (→ element 4; BBM-12 guarantees the situation
occurs every burn) · parent-log blowup (→ per-child cursors + summaries + `prev-segment`
chaining) · shared-output clobber (→ per-arm keys everywhere) · undeclared concurrent merge
(→ reducers, refuse) · **evil merge** at fan-in (→ mechanical-only fan-in commits — PD-2 extended
into git history) · clock-skew ordering lies (→ (runId, seq)) · Cthulhu fan-ins (→ wave-sized
bounds, pairwise `--no-ff` default).
