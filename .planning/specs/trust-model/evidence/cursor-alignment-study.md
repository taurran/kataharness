---
spec: trust-model
artifact: evidence dossier 5 — cursor alignment study (TM-C1 operator rider)
date: 2026-08-16
provenance: dispatched research agent (repo + live web sources, URLs inline), committed
  verbatim-in-substance by the conductor
baseline: grill/dispatch-seam @ f43ee09
---

# Cursor alignment study — against learning-loop / run-record / graph models

**VERDICT: aligned, YES — the cursor is structurally the Temporal/event-sourcing model
implemented on git.** Append-only typed event log as the one authority + deterministic fold as
recovery + projections as the only views is precisely the strongest surveyed pattern (Temporal:
Event History + replay; event sourcing: fold + projections; Claude Code and Pi ship the same
shape informally as session JSONL). **D135 does not need defending — it matches best field
practice.** All deltas are hardening gaps, not shape gaps.

## Per-model findings

1. **LangGraph checkpointing** (thread_id + sortable checkpoint_id snapshots per super-step;
   Store for cross-thread memory; time-travel/fork; pending-writes so successful parallel nodes
   aren't re-run). Has that we lack: pending-write granularity (a gated-but-unintegrated task is
   re-dispatched whole under D134 — a durable VERDICT line is the pending-write that would let
   restore credit it); explicit `next`; first-class forking. We do better: full causal audit
   trail (snapshots can't answer who/when/why); git authority vs. an operated database; O(line)
   growth vs. snapshot-per-step. (docs.langchain.com/oss/python/langgraph/persistence)
2. **Temporal.io event history** — the closest industrial relative; deterministic replay IS
   recovery, the strongest validation of our posture. Has that we lack: **two-level identity**
   (Workflow Id spans a chain of Run Ids — we have no predecessor pointer across
   loop-backs/version-ups); **monotonic event IDs** (our ordering is timestamps with a specified
   -but-unimplemented tie-break); **bounded-history discipline** (10k-event warning /
   continue-as-new segmenting; our archives are write-only dead weight); a service-enforced
   closed event-type enum (our TYPEs are prose-enforced; orchestrator-only PHASE/VERDICT
   partially covers). We do better: zero-infra git authority; human-readable/greppable; trailer
   durability. (docs.temporal.io/workflow-execution/event)
3. **Event sourcing** (Fowler): fold + projections + snapshots-as-cache-never-authority. Adopt:
   a fold-cache snapshot in `.kata/` keyed by (runId, line-count) — D81 licenses exactly this;
   state the "fold is pure, side effects only after fold completes" invariant explicitly. Our
   recount-from-DECISION-lines is a projection with deliberate no-cache — more conservative than
   field norm. Naming: call fold outputs **projections** (imports twenty years of shared
   understanding). (martinfowler.com/eaaDev/EventSourcing.html)
4. **OpenTelemetry traces**: runId ≈ trace_id; the TM-B4 dispatch record ≈ a span. Has that we
   lack: **explicit parent chains** — worker lines carry no pointer to the dispatch that spawned
   them; reroll/attempt attribution is DECISION-prose + branch names. A dispatch-seq stamp on
   worker lines makes lineage mechanical AND strengthens fabrication detection (a forged line
   must forge a live parent). VERDICT ≈ span status; escalation idiom ≈ span events; a
   cursor→OTLP projection would be trivial. (opentelemetry.io/docs/concepts/signals/traces/)
5. **Agent-harness peers**: Pi = per-session append-only JSONL (same shape); Hermes'
   append-for-audit/**distill-for-load** applies to the cursor — folds/context injections consume
   a bounded distillation, never the raw log. GSD = mutable position snapshot (last-write-wins —
   the failure mode kata-board exists to avoid); its one stealable habit is O(1) "where are we,"
   reproduced by PHASE + a fold cache. Claude Code sessions are per-session append-only JSONL
   with replay-on-resume — field convergence on our shape, minus our stable grammar + git
   durability.
6. **Temporal knowledge graphs (Graphiti)**: bi-temporal validity mostly N/A at line level
   (lines are events, not facts) — and the invalidate-don't-delete discipline already exists in
   our `Kata-Supersede:`/`Kata-Invalidated:` trailers. The one applicable idea: **graph
   projections tag derived facts with the (runId, line) that produced them**, so a superseding
   DECISION invalidates downstream graph facts mechanically. Projection-layer note, not a cursor
   change. (github.com/getzep/graphiti)

## Ranked improvement candidates (all within the one-log architecture)

1. **Snapshot the trail on every PHASE/VERDICT append** — closes mid-gate resume without
   re-running the gate; existing fail-soft machinery gains two call sites. Cost: trivial.
2. **`prev-run:` pointer in the run-header** (Temporal run-chain) — loop-back/version-up becomes
   a walkable chain; anchors the unrecorded loop-back event. Cost: one field + one write.
3. **Monotonic per-run `seq` on cursor lines** — kills the same-second tie-break problem, gives
   TM-B4's chaining truncation/tamper teeth, total order for folds. Rides the same grammar
   two-step. Cost: small.
4. **Dispatch-lineage stamp on worker lines** (the parent_id analog) — mechanical
   attempt/reroll attribution; forged lines must forge a live parent. Bundles with #3 in one
   grammar migration. Cost: small.
5. **Chained, readable archives = continue-as-new segmenting** — rotation writes a fold-summary
   payload + `prev-segment` pointer; archives stop being dead weight; long Backlog Burn runs
   stay bounded. Cost: medium — reserve the header field now, build when a real cursor gets big.
6. **Operator ruling on pushing `refs/kata/trail`** — every surveyed durable system is
   remote-durable; our (iv) story otherwise rests on trailers + `.planning/`. A gated push at
   closeout closes it; "NEVER pushes" is deliberate, so this is a ruling, not a change to sneak
   in. Cost: one push call; the real cost is the consent decision. *(Ruled same session: TM-C3.)*

Nothing in the survey argues for a second journal, a state database, or replacing the fold.
