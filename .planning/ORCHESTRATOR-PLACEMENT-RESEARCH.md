---
date: 2026-07-26
kind: research finding — resolves KH-T06's core question
method: cited comparative survey, labelled [DOC] / [CODE] / [COMMUNITY] / [UNDETERMINED]
---

# ORCHESTRATOR PLACEMENT — what the industry actually does

## The answer to the literal question: near-unanimous

**Where an LLM orchestrates, it is the ROOT session.** Claude Code, Kiro, Hermes `AIAgent`, Devin's
coordinator, OpenAI's agents-as-tools manager, CrewAI's manager, every Pi community extension.

> **No surveyed system makes a spawned subagent the primary orchestrator by design.**

Claude Code enforces it *structurally*, not by convention:
- *"Lead is fixed: the main session is the lead for its lifetime. You can't promote a teammate to
  lead or transfer leadership."*
- *"No nested teams: teammates cannot spawn their own teammates."*

**So our current design — conductor in the root session — matches universal practice.** `LD11`
(orchestrator + evaluator pinned to host) is not a v1 compromise to be outgrown. It is what everyone
does.

## The answer to the question behind it: the orchestrator shouldn't be an LLM at all

The genuine convergence, and it dissolves the binary:

| system | what actually orchestrates |
|---|---|
| Anthropic **Workflows** | a JavaScript script — *"moves the orchestration into a script the runtime executes outside the conversation context"* |
| Hermes **Kanban** (v0.17) | SQLite board + dispatcher + OS-process workers, *"without fragile in-process subagent swarms"* |
| **Pi** orchestrator (experimental) | a Unix-socket **process supervisor** — not an LLM at all |
| **BMAD** | story files + *"always start a fresh chat for each workflow"* |
| **LangGraph** | a checkpointed graph |

And two independent teams state the same principle almost verbatim:

> **Anthropic:** *"No direct filesystem or shell access from the workflow itself — Agents read, write,
> and run commands. The script coordinates the agents."*
> **Hermes:** *"A well-behaved orchestrator does not do the work itself."*
> **BMAD community:** *"A lightweight coordinator … never reads files or writes code itself."*

**The orchestrator coordinates; workers write.** Closest thing to a real consensus principle found.

## Why a subagent orchestrator is a bad trade — four costs, one killer

1. **A depth level.** Claude Code's default has swung **5 → 1 → 3 across four releases** — do not build
   on that number. Hermes defaults to depth 1 with leaf agents unable to delegate at all. Agent teams
   forbid nesting outright.
2. **Steerability.** The subagent contract is one prompt in, one summary out. That both Pi's community
   extensions and Claude Code had to **bolt on child→parent messaging** is direct evidence the plain
   contract is too thin to orchestrate through.
3. **The user.** A subagent cannot ask a human anything — `AskUserQuestion` is withheld; teammate
   prompts bubble to the lead.
4. **🔑 It dies anyway.** Hermes: delegation *"remains tied to the owning session and Hermes process."*
   Claude Code: *"a teammate's background work can't outlive the lead's process."* **You pay the price
   and don't buy independence.**

> **A subagent orchestrator is only worth it paired with a durable external state contract — and once
> you have that contract, the LLM orchestrator is the part you no longer need.**

## What actually ships for long multi-hour builds

**Root-session conductor + durable on-disk plan + fresh-context workers.** Everywhere.

- **Root = conductor.** Owns the user, the plan, the tree, the gates.
- **Durable plan on disk is the real orchestrator** — story files (BMAD), `kanban.db` (Hermes),
  `~/.claude/tasks/` (agent teams), our frozen `PLAN.md`. *It is what survives.*
- **Fresh-context workers isolated by construction** — worktrees, microVMs, per-file copies.
- **Root recycles itself**, or dies and is restarted pointing at the plan.

BMAD — arguably the most battle-tested multi-hour *build* methodology surveyed — answers context
exhaustion with **pure avoidance** (*"always start a fresh chat"*) and invests everything in making
story files complete enough to survive it.

## Context exhaustion, ranked best→worst

1. **Eliminate orchestrator context** (Workflows, Kanban, Pi's supervisor) — the question becomes
   unaskable. Cost: no mid-run human input; plan must be decidable up front.
2. **Durable board + disposable workers + restartable orchestrator** (Hermes Kanban, BMAD) —
   orchestrator death becomes routine, not failure.
3. **Compaction with recoverable externalization** — Cursor's *"chat history as files"*, Hermes's
   parent/child session lineage, Anthropic's LeadResearcher *"saving its plan to Memory."* Best pure
   in-session answer because the lossy boundary becomes **reversible**.
4. **Plain compaction** — works, irreversibly lossy.
5. **Truncation** — silent loss.
6. **Subagent orchestrator with no durable contract** — strictly worse than (2), which it approximates
   badly.

---

## WHAT THIS MEANS FOR US

### ✅ KH-T06 largely RESOLVES — keep the orchestrator in the root session
Not a compromise. Universal practice, structurally enforced by the leaders. **Closing the question as
asked**, with one carve-out below.

### ✅ Our single-writer discipline is STRICTER than anything shipped
Claude Code's guidance is bluntly manual: *"Two teammates editing the same file leads to overwrites.
Break the work so each teammate owns a different set of files."* Kiro lets any agent with `write`
write. **Our conductor-is-sole-main-tree-writer + workers-in-worktrees policy exceeds the field.** Keep
it; it is a genuine differentiator.

### ⚠️ But it makes KH-T01 (handoff) MORE important, not less
The root's context ceiling is real. **The correct fix everywhere is externalizing the plan, not
relocating the conductor.** Anthropic's own answer to 200k truncation was the LeadResearcher *saving
its plan to Memory* — not spawning a sub-orchestrator.

So: our conductor placement is right, and **the thing that makes it survivable is exactly the handoff
machinery we confirmed has never fired.** KH-T01 is the load-bearing item, not KH-T06.

### 🔑 The real test for any future sub-orchestrator
> *If this agent is killed mid-flight, can a fresh one resume from disk alone?*

Gate it on the **state contract**, not the context budget. Today our answer is *partly* — `.planning/`
is rich, but `.kata/` is gitignored and no handoff has ever carried its provenance fields.

### Three concrete borrowings, ranked
1. **Cursor's "chat history as files"** — make the compaction boundary *recoverable*, not merely
   survivable. Post-summary the agent holds a reference to a searchable history file. Cheapest, highest
   value, directly addresses the operator's *"I've never seen the parent agent recycle context."*
2. **Hermes's session-rotation-with-lineage** — compaction closes the session row and creates a
   **child seeded by the summary with a parent pointer**, rather than rewriting a transcript. Maps
   cleanly onto our handoff artifacts.
3. **Magentic-One's stall counter** — ≤2 non-progressing iterations forces a replan + worker context
   reset. Cheap anti-thrash guard. *(Note: even Magentic-One never bounded its own Orchestrator ledger.)*

### Where a script orchestrator IS right for us
For **deterministic fan-out inside a phase** — sweep N files, run the same gate over M tasks — the
script orchestrator is strictly better: intermediate results live in script variables, not context.
This session's own D2 verification sweep is exactly that shape. Bounds to respect: 16 concurrent,
1,000 agents/run, **no mid-run human input**, resume only within the session.

---

## Research-integrity notes worth keeping

- **A circulating claim about Pi was refuted.** A search-result synthesis asserted Pi hands the
  orchestrator "a summary of its still-running sub-agents" during compaction. Both Pi's compaction doc
  and the oh-my-pi variant were fetched directly: **neither mentions subagents or orchestrators at
  all.** Unsourced — do not propagate.
- **AWS's "nest supervisors 3 layers deep" is unsourced too** — traces to a Medium post citing no AWS
  source; every relevant AWS page is silent. `[UNDETERMINED]`.
- **`pi-agent-core` exports a class called `AgentHarness`** that is single-session infrastructure, not
  a multi-agent orchestrator. A false positive for anyone reading the API surface for orchestration.
- **Cognition tension, unreconciled by either source:** *Don't Build Multi-Agents* argues for a
  single-threaded linear agent, while their own Managed Devins ships the coordinator-plus-children
  architecture the essay argues against.
