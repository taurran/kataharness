# protocol/orientation.md — the launch-orientation contract

The **receiving half of the handoff**. Where `kata-handoff` *writes* a durable brief at a boundary,
**`kata-orient` assembles the right context INTO a subagent at launch** so it starts oriented, not cold. This
file is the agnostic contract both sides share (loop-cognition L4/AO-GB1-3, extended D76). A host adapter
*renders* it (Claude → the worker prompt; nested-AGENTS.md tools → tree-walk; Kiro → steering files).

> **North star — orient like you would a good new employee on a specific task.** Not a context dump: figure
> out *what kind of work* they're doing, surface *exactly the right* references, flag the landmines, and raise
> the questions the role must get answered — routing each to whoever can answer it. An oriented worker knows
> both **what it knows** and **what it must escalate rather than improvise**.

## The three tiers (priority-ordered — Hermes `prompt_builder` pattern)
Assembled stable→context→volatile; **budget-capped to the prime frame** (sprint-cadence SC-GB7). When over
budget, degrade from the bottom: shrink **volatile** detail to pointers before touching **context**, and never
drop **stable**. Each tier names its sources; absent sources degrade gracefully (no error).

| Tier | Holds | Sources |
|---|---|---|
| **stable** | identity · the spine · conventions · model-routing — the non-negotiables, same every task | root `AGENTS.md` (+ adapter `CLAUDE.md` notes), `docs/STANDARDS.md` |
| **context** | where the work sits + who it collaborates with | the **frozen DESIGN/PLAN slice** for this task · **nearest-module `AGENTS.md`/`CLAUDE.md`** (vertical rollup) · `CONTEXT.md` glossary · relevant ADRs · **lateral adjacency pointers** (below) |
| **volatile** | the assignment + current state | task `<action>`/`<owned files>`/`<acceptance>` · `kata-board`/state · open escalations · any inbound `kata-handoff` artifact |

## Vertical rollup (the 2026 nested-AGENTS.md standard)
Compose **root invariants + the nearest module's `AGENTS.md`/`CLAUDE.md` along the path** to the task's owned
files (nearest-along-path wins). This is the *standard* part. Absent a module file ⇒ root only.

## Lateral adjacency pointers (our kata-graph-derived contribution — novel)
For the modules this task **collaborates with**, include **pointers, never inlined content**: projected by
`kata-orient` from `kata.graph.json` `ref`∪`call` edges (kata-graph stays a pure map-builder; consumers
project — see `protocol/graph.md`). **Lazy-loaded** (a path + one-line why, the worker loads on demand) so they
are **rot-proof and token-safe**. No `kata.graph.json` (greenfield / no tree-sitter) ⇒ no lateral pointers
(vertical rollup still applies) — graceful degradation, never a hard fail.

## Task-type awareness (NEW, D76 — tailor the orientation to the role)
Classify the dispatched task into a **task-type** (from the invoked skill + the task shape); the type selects
which docs to surface, which callouts to raise, and which questions to generate:

| task-type | surface | callout (the landmine) |
|---|---|---|
| **implement-feature** (`kata-tdd`) | DESIGN acceptance · module test conventions · disjoint owned files | "escalate, don't re-plan; in grill-skip, log assumptions to `kata-defer`" |
| **fix-bug** (`kata-diagnose`) | the failing gate · regression baseline | "fix in-lane; don't expand scope" |
| **refactor / version-up** (`kata-graph`) | blast-radius digest · full-suite-green regression contract | "baseline stays green; footprint-scoped ownership" |
| **research** (`kata-research`) | the `research-needed` escalation payload · the grounding-gate contract | "ground every claim; no-write; never re-plan/inject" |
| **evaluate / review** (`kata-evaluate`/`kata-review`) | acceptance criteria · LOCKED decisions | "fresh-context, no-write, default-FAIL; never certify your own work (L8)" |
| **grill / plan** (`kata-grill`/`kata-plan`) | `CONTEXT.md` · ADRs · the priming prompt | "convergence is a fresh-context review, not self-graded" |

## Contextually-derived pointers + callouts (NEW, D76 — from standard markdown)
`kata-orient` **scans the in-scope standard markdown** (root + nearest-module `AGENTS.md`/`CLAUDE.md`,
`CONTEXT.md`, ADRs, the DESIGN/PLAN slice, README) and **derives**, for *this* task-type + owned files:
- **Pointers** — "for X, see `<file:section>`" (by path, lazy-loaded) — the right reference, not the whole file.
- **Callouts** — the landmines: a **relevant LOCKED decision**, a **drift-magnet glossary term**, an
  **applicable `LESSONS-LEARNED` lesson**, a convention this task is likely to violate. Derived from the markdown
  by relevance to the task — never a hand-maintained list.

## Smart questioning + routing (NEW, D76 — "ask the questions a good hire would ask")
From the task-type + what the in-scope docs leave **unresolved for this task**, generate the relevant questions,
then **route each** (this is AO as the launch-time *detector* on the grill↔RS spectrum, D71):
- **Docs-answerable** ⇒ resolve from the markdown and **answer it inline** in the orientation (don't make the
  worker ask what AO can find).
- **Genuinely ambiguous / no in-plan answer** ⇒ **pre-flag as a likely `research-needed` escalation**
  (`protocol/escalation.md`) for the orchestrator to route to `kata-research`. AO does not dispatch — it flags.
- **LOCKED-tension / preference** ⇒ surface as an **open question for the human / grill** (never auto-resolve;
  D1/C4).

## Handoff tie-in (aligned from both sides — D76)
A `kata-handoff` artifact is a **first-class orientation source** and maps directly into the tiers:
`read-in order` → **context** pointers · `state` + `NEXT STEP` → **volatile** · `suggested next skills` →
**task-type** hint · `open decisions for the human` → AO's **human-required questions**. `kata-handoff` is
authored to this mapping (see its *Orientation tie-in*), so the write side and read side compose without loss.

## Producer / consumer
**Producer:** `kata-orient` (read-only — `[Read, Grep, Glob]`, no Write/Agent; it *returns* the assembled
orientation + the routed-question flags). **Consumer:** `kata-orchestrate` — invokes `kata-orient` per dispatch
(hook only, D24d), injects the orientation into the worker launch, and acts on the flags (research-needed →
route to `kata-research`; human-required → escalate). The *logic* lives here + in `kata-orient`, never in the
weight-5 dispatcher.
