---
name: kata-orient
description: >-
  Assemble launch orientation for a subagent — the read-side mirror of kata-handoff. Read-only: builds a
  three-tier (stable/context/volatile), prime-frame-budgeted brief from the standard markdown in scope, tailored
  to the task-type, with contextually-derived pointers + callouts and the questions a good hire would ask
  (routed: answer-inline / research-needed / human-required). Invoke from kata-orchestrate per dispatch so a
  worker starts oriented, not cold.
license: Apache-2.0
version: 0.4.0
category: handoff
status: beta
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
   - **stable** — identity · **the Prime Directives** (`protocol/prime-directives.md` — always
     injected verbatim-in-substance, never summarized away) · spine · conventions · model-routing
     (root `AGENTS.md`/`CLAUDE.md`, [[STANDARDS]]).
   - **context** — the frozen DESIGN/PLAN slice · **vertical rollup** (root invariants + the *nearest-module*
     `AGENTS.md`/`CLAUDE.md` along the task's owned-files path) · `CONTEXT.md` glossary · relevant ADRs ·
     **lateral adjacency pointers** projected from [[kata-graph]]'s `kata.graph.json` (collaborating modules — a
     path + one-line why, **lazy-loaded, never inlined**; no graph ⇒ skip, vertical rollup still applies).
   - **volatile** — the task `<action>`/`<owned files>`/`<acceptance>` · [[kata-board]]/state · open
     escalations · any inbound [[kata-handoff]] artifact (maps directly into context+volatile — see its
     *Orientation tie-in*).
   Over budget ⇒ degrade from the bottom (volatile → pointers) before touching context; never drop stable.
2b. **Build the worker recall brief (D156 — context tier, narrow).** Call `recall.recall_from_paths(...)`
   (`tools/recall.py` — the same seven sources as kata-initiate Phase 1b, incl. the D155 first-run
   fallback) with `query_terms` from THIS task's `<action>` + owned-file names + DESIGN-slice terms and the
   run's `kind`; render at most a handful of records as **pointers** (source · one-line why · provenance
   date — never inlined page bodies). Read-only, never gates, never blocks; absent sources ⇒ no brief. This
   is the **first context-tier element dropped** under budget pressure. Contract: `protocol/orientation.md`
   §Worker recall brief.
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

## Resume / restore flow (D134 — restore-hardening B2)

When invoked via `kata-resume` (rather than `kata-orchestrate` per-task dispatch), orient detects the
*lost-run* variant and assembles a restore-specific orientation instead of a normal task brief.

### Detect a lost run
Check whether `.kata/board.md` is absent or empty AND `refs/kata/trail` is present
(`git rev-parse --verify refs/kata/trail`).  If yes → lost run; proceed with the steps below.
If no trail → no durable state to restore from; surface as WARN and offer a cold-start.

### Read the durable board
`git cat-file -p refs/kata/trail:board.md` reads the last durably committed board snapshot.
Fold it to a frontier view with the canonical concurrency reduce (`fold_board` in `tools/kata_restore.py`,
which implements the `protocol/board.md` canonical snippet).  The folded frontier shows which tasks had
in-flight CLAIMs and which had completed CLAIM+DONE at the point of loss.

### Compute the re-dispatch set (PLAN-minus-integration)
Re-dispatch set = all task-ids in the frozen PLAN **minus** tasks that have a durable integration commit
on the integration branch.  Integration commits are identified by the `Kata-Task: <id>` conventional-commit
trailer written by [[kata-orchestrate]] step 5 (`collect_integrated_tasks` in `tools/kata_restore.py`).

**Precedence rule (tier-2 authoritative for DONE):**
- A task with an integration commit → NOT re-dispatched, regardless of board state.
- A task with board `DONE` but no integration commit → IS re-dispatched (tier-2 wins over board).
- A task not on the board at all → IS re-dispatched (PLAN-derived, not board-gated).

The folded board CORROBORATES in-flight ownership (which task a dead worker held) but **never limits the
re-dispatch set.**  Gating on board CLAIMs would silently drop early-wave tasks a crash never durably
recorded (e.g. a wide first wave that crashed before any board write).

### C2 cleanup before re-dispatch
For each task in the re-dispatch set, call `cleanup_stale_task(repo_root, task_id)` which:
1. Runs `git worktree prune` to remove stale `.git/worktrees/<name>` metadata (dead-session paths).
2. Force-deletes `task/<task_id>` branch so a fresh `git worktree add -b task/<task_id>` never collides.
Half-written artifacts in the dead worktree are **discarded, not reused.**

### No rotation on resume
The resume path calls `kata_restore.restore(...)` which writes the trail board back to `.kata/board.md`
**without rotation** — no `.kata/board.<utc>.archive.md` is created.  Rotation is a run-start action
([[kata-orchestrate]] loop preamble); resuming skips it entirely.  Rotating would archive the recovered
CLAIM/DONE lines and empty the live board.

### Caller contract — resolving plan_path and integration_branch

`kata_restore.restore()` requires two caller-resolved values:

- **`plan_path`** — the run's frozen PLAN under `.planning/specs/<spec-name>/PLAN.md`.  The
  caller (this skill, via `kata-resume`) reads the active spec name from `kata.config` or the
  most recent frozen PLAN under `.planning/specs/`.  Pass the absolute path; `kata_restore`
  resolves it relative to `repo_root` internally for git commands.
- **`integration_branch`** — the branch holding durable integration commits (kata-orchestrate
  step 5).  Defaults to `"integration"` for all standard kata runs; pass an explicit value only
  when `kata.config` names a different branch.

### Return to the orchestrator
Surface the restore result as the volatile tier of the orientation brief:
- `lost_run: true`
- `redispatch`: the PLAN-minus-integration re-dispatch set (the tasks to restart)
- `board_frontier`: the folded board snapshot (corroborating context for in-flight ownership)
- `integrated`: task-ids already durable (do not re-dispatch)

The orchestrator (`kata-resume` → [[kata-orchestrate]]) acts on this to re-dispatch the incomplete tasks.

## Compacted / respawned session — the injected HANDOFF.md pointer (context-autonomy CA-L12/L19)

A **compacted or respawned** session is a distinct resume variant from the D134 lost-run restore above. On
Claude, the SessionStart(`compact`/`resume`) hook injects a re-anchor instruction pointing at the newest
**`.planning/HANDOFF.md`** (the SessionStart re-anchor hook; `protocol/handoff.md`). That pointer is this skill's
**volatile-tier input** on resume — it maps 1:1 into context+volatile like any inbound [[kata-handoff]]
artifact.

- **Subject to the staleness rule (CA-L19, `protocol/handoff.md`).** Any board `DONE`/`DECISION` line **newer**
  than the HANDOFF.md git commit **demotes** the handoff from sole-anchor to **context-input** — the
  kata-orient **3-tier rebuild becomes authoritative**. A fresh handoff anchors; a **demoted** handoff is
  corroborating context only, and this skill's tiers are rebuilt from the standard markdown regardless.
- **Resume quality bar (CA-L12).** *Resume must reload FULL context quality — kata-orient 3-tier, budget-capped
  per `protocol/orientation.md` — seamless, no hangs, no degradation* (graded at CA-A1, not just task
  continuity). A demoted-handoff resume still meets this bar via the full rebuild; it never degrades to
  handoff-only.

---

## Discipline
- **Pointers over payload.** Adjacency + most references are *pointers* (path + why), lazy-loaded — rot-proof,
  token-safe, and they keep the orientation inside the prime frame.
- **Graceful degradation.** Missing nearest-module file ⇒ root only; missing `kata.graph.json` ⇒ no lateral
  pointers; missing `CONTEXT.md` ⇒ skip glossary. Never error on an absent optional source.
- **Hooks, not logic in the dispatcher.** The orchestrator invokes this and acts on the flags; the assembly
  logic lives here + `protocol/orientation.md` (D24d — the weight-5 dispatcher stays thin).
