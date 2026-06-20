---
name: kata-orient
description: >-
  Assemble launch orientation for a subagent — the read-side mirror of kata-handoff. Read-only: builds a
  three-tier (stable/context/volatile), prime-frame-budgeted brief from the standard markdown in scope, tailored
  to the task-type, with contextually-derived pointers + callouts and the questions a good hire would ask
  (routed: answer-inline / research-needed / human-required). Invoke from kata-orchestrate per dispatch so a
  worker starts oriented, not cold.
license: Apache-2.0
version: 0.1.0
category: handoff
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob]
source: >-
  new (KataHarness original, loop-cognition AO-GB1/2/3 + D76) — receiving half of the two-way handoff (spine #5);
  three-tier assembly echoes Hermes prompt_builder (stable/context/volatile); nested-AGENTS.md rollup standard
tags:
  - kata/handoff
  - kata/spine
  - orientation
  - context-assembly
  - onboarding
---
# kata-orient — orient a subagent at launch, like a good employee on a specific task

The **receiving half of the handoff** (spine #5). `kata-handoff` *writes* a durable brief; `kata-orient`
*assembles* the right context INTO a subagent as it launches, so it starts oriented. **Read-only** — it returns
the assembled orientation + routed-question flags to its caller ([[kata-orchestrate]]); it does not write, plan,
or dispatch. The full contract is **`protocol/orientation.md`** — this skill is the method that obeys it.

> **North star:** orient like a good new employee on a *specific* task. Don't dump context — figure out what
> kind of work this is, surface exactly the right references, flag the landmines, and raise the questions the
> role must get answered. The worker should leave orientation knowing **what it knows AND what it must escalate
> rather than improvise.**

## Method
1. **Classify the task-type** (`implement-feature` / `fix-bug` / `refactor`/`version-up` / `research` /
   `evaluate`/`review` / `grill`/`plan`) from the invoked skill + the task shape. The type drives steps 3–5
   (which docs, which callouts, which questions) — `protocol/orientation.md` → *Task-type awareness*.
2. **Assemble the three tiers, priority-ordered, capped to the prime frame:**
   - **stable** — identity · spine · conventions · model-routing (root `AGENTS.md`/`CLAUDE.md`, [[STANDARDS]]).
   - **context** — the frozen DESIGN/PLAN slice · **vertical rollup** (root invariants + the *nearest-module*
     `AGENTS.md`/`CLAUDE.md` along the task's owned-files path) · `CONTEXT.md` glossary · relevant ADRs ·
     **lateral adjacency pointers** projected from [[kata-graph]]'s `kata.graph.json` (collaborating modules — a
     path + one-line why, **lazy-loaded, never inlined**; no graph ⇒ skip, vertical rollup still applies).
   - **volatile** — the task `<action>`/`<owned files>`/`<acceptance>` · [[kata-board]]/state · open
     escalations · any inbound [[kata-handoff]] artifact (maps directly into context+volatile — see its
     *Orientation tie-in*).
   Over budget ⇒ degrade from the bottom (volatile → pointers) before touching context; never drop stable.
3. **Derive pointers + callouts from the standard markdown** (don't inline whole files). Scan root +
   nearest-module `AGENTS.md`/`CLAUDE.md`, `CONTEXT.md`, ADRs, the DESIGN/PLAN slice, README; extract for *this*
   task-type + owned files: **pointers** ("for X, see `<file:section>`") and **callouts** — the landmines: a
   relevant LOCKED decision, a drift-magnet glossary term, an applicable `[[LESSONS-LEARNED]]` lesson, a
   convention this task is likely to violate.
4. **Generate the questions a good hire would ask** for this task-type + the gaps the in-scope docs leave
   **unresolved for this task** — then **route each** (the launch-time end of the grill↔RS spectrum, D71):
   - **docs-answerable** ⇒ resolve from the markdown and **answer inline** (don't make the worker ask it);
   - **genuinely ambiguous / no in-plan answer** ⇒ **flag `research-needed`** (`protocol/escalation.md`) for the
     orchestrator to route to [[kata-research]] — AO flags, never dispatches;
   - **LOCKED-tension / preference** ⇒ surface as an **open question for the human / grill** (never auto-resolve,
     D1/C4).
5. **Return** the assembled orientation + the routed-question flags to [[kata-orchestrate]]. No writes.

## Discipline
- **Pointers over payload.** Adjacency + most references are *pointers* (path + why), lazy-loaded — rot-proof,
  token-safe, and they keep the orientation inside the prime frame.
- **Graceful degradation.** Missing nearest-module file ⇒ root only; missing `kata.graph.json` ⇒ no lateral
  pointers; missing `CONTEXT.md` ⇒ skip glossary. Never error on an absent optional source.
- **Hooks, not logic in the dispatcher.** The orchestrator invokes this and acts on the flags; the assembly
  logic lives here + `protocol/orientation.md` (D24d — the weight-5 dispatcher stays thin).
