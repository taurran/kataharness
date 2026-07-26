---
date: 2026-07-26
kind: doctrine + a newly-found gap it partly answers
status: principle ADOPTED (operator-directed); KH-T11 opened
---

# THE THIN-ORCHESTRATOR DOCTRINE

## The principle

> **A well-behaved orchestrator does not do the work itself.**

Operator-adopted 2026-07-26. Independently stated by three teams, in near-identical words:

- **Hermes:** *"a well-behaved orchestrator does not do the work itself. It decomposes the user's goal
  into tasks, links them, assigns each to one of the profiles."*
- **Anthropic (Workflows):** *"No direct filesystem or shell access from the workflow itself — Agents
  read, write, and run commands. **The script coordinates the agents.**"*
- **BMAD community:** *"A lightweight coordinator … **never reads files or writes code itself.** Every
  unit of work is delegated to a dedicated subagent with a fresh context window."*

This is what the withheld "thin orchestrator" feature (`DF-05 §3a`) was reaching for. **We take the
principle, not their implementation** — they explicitly recommended against adopting the feature,
because its quality half was never measured. The principle needs no such caveat: three teams reached
it independently.

---

## ⚡ THE CONNECTION NOBODY HAD MADE: this is the answer to the model-alignment problem

### The operator's question

> *"What happens if the user initiates KataHarness in a model that doesn't align with their run
> profile? How do we change models if the orchestrator is always the main session? Do we kick off
> another session? Can the agent change execution in-window in another model? I'm not sure we ever
> really answered this simple issue."*

**We never did. Verified: there is NO minimum-anchor check anywhere** in `kata_models.py`,
`kata_preflight.py`, or readiness.

### What actually happens today — measured

| anchor | critical work resolves to | economy work resolves to |
|---|---|---|
| `haiku` | `None` → **inherit → runs on haiku** | `None` → **runs on haiku** |
| `sonnet` | `None` → inherit → sonnet | `claude-haiku-4-5` |
| `opus` | `None` → inherit → opus | `claude-sonnet-5` |

Critical work **always** returns `None` — "inherit by omission" — by design (R7). That is correct
*when the anchor is high*. **It is catastrophic when the anchor is low**: start a run on Haiku and the
grill, the plan, the default-FAIL gate, and the adversarial reviewer **all run on Haiku**, with
nothing warning and nothing blocking. The whole tiering architecture assumes the anchor is high enough
that stepping *down* is the only interesting direction. It never checks that assumption.

### Can we change the model mid-run? Precisely:

| what | can its model change? |
|---|---|
| **The conductor / main session** | ❌ **No.** Fixed at launch by the operator's `/model`. Nothing in-window can change it |
| **Dispatched subagents** | ✅ **Yes** — a per-dispatch model override is available and we used it this session |
| **The evaluator** | ✅ Yes on model. `HOST_ONLY_ROLES` constrains **platform**, not model — so it can be elevated while staying on-host |

### So the thin-orchestrator doctrine IS the mitigation

**If the conductor only coordinates and never does the judgment work, its model largely stops
mattering** — because every act of judgment happens in a dispatched agent whose model *can* be
elevated. A thin orchestrator on Haiku dispatching an Opus evaluator is sound. A **thick** orchestrator
on Haiku doing its own grilling and gate-reading is not.

That reframes the doctrine. It is not primarily a token-efficiency measure — it is **what decouples run
quality from whatever model the operator happened to launch with.**

### The honest residual

The conductor cannot be reduced to zero judgment. It still routes, reads gate output, decides
escalations, and interprets drift signals. So a floor still exists — it is just much lower than today's
"the anchor is the ceiling for all critical work."

---

## KH-T11 — Run-profile / anchor alignment · **NEW, operator-found**

**Three things to resolve, in order:**

1. **Detect it.** A preflight check comparing the session anchor against the run profile's demands.
   Today's `validate_anchor` catches an *unrecognized* anchor; nothing catches a *recognized but
   inadequate* one. Cheapest possible version: warn when `mode: advanced` meets a sub-Sonnet anchor.
2. **Decide the response.** Precedent exists in exactly one place — the premium "keep-using declined"
   arm **hard-stops and advises a `/model` switch, resuming after**. That is the only in-repo answer to
   "your session model is wrong," and it is the right shape: config cannot change a session's model, so
   the honest move is to stop and tell the operator.
3. **Or dispatch around it.** Per the doctrine above: elevate the *dispatched* critical roles rather
   than blocking the run. This is strictly better where it works, and it is the reason to make the
   orchestrator thin.

**Open question for the grill:** is "kick off another session" ever the right answer? It is really a
handoff — which makes it `KH-T01` again. The operator's instinct that these are the same problem is
correct.

---

## KH-B41 — Kanban: a real framework around task/backlog management · **operator-requested**

> *"I think we should add kanban to our potential backlog items. We already do plan, backlog, etc. It
> would be cool to actually define it as something that can be presented visually and have a harder
> framework around task/backlog management."*

We already have the raw material and it is genuinely scattered: `.planning/BACKLOG.md`,
`.planning/ROADMAP.md`, frozen `PLAN.md` per spec, `.kata/board.md`, `DEFERRED.md`, and now five
ingest documents. **Six surfaces, no single view, no state machine.**

Hermes's Kanban is the strongest reference found: *"every task is a row in `~/.hermes/kanban.db`; every
handoff is a row anyone can read and write; every worker is a full OS process with its own identity"* —
plus a dispatcher that *"reclaims crashed workers (PID gone but TTL not yet expired)"* and returns
failed tasks to `ready`.

**What is worth stealing:** the **state machine** (`ready → claimed → done/failed`, with reclaim), the
**single durable row per task**, and **handoff-as-a-row** rather than handoff-as-a-document. **What we
should not copy blindly:** SQLite as the store — our artifacts are deliberately Obsidian-readable
markdown, and that is a real property we would lose.

**The visual half is the operator's actual ask** and it is achievable cheaply: a generated view over
whatever the durable store becomes.

---

## The chat-history-as-files question — assessed, and I do NOT recommend it

> *"I want to consider the possible bloat of saving chats. It's novel, but is it necessary with proper
> task management and handoff?"*

**The skepticism is right. Recommendation: don't save transcripts.**

Cursor's *"chat history as files"* exists because their compaction is lossy and **they have no curated
decision record** — the transcript is the only place the reasoning survives. We are not in that
position. `DECISIONS.md`, the grill ledgers, `LESSONS-LEARNED.md`, and the handoff artifacts already
capture the *why*, **deliberately and curated**. A searchable transcript is a strictly worse version of
something we already do better.

**Where the genuine gap is:** things **tried and rejected** that never made it into a decision record.
That is the only content a transcript holds which our artifacts do not.

**The cheap fix that gets the value without the bloat:** make the handoff carry an explicit
**"what was tried and rejected, and why"** section. Curated, bounded, and far cheaper than persisting
transcripts — and it converts a storage problem into a discipline problem, which is the trade we want.

**What we SHOULD take from Cursor is the other half:** making the compaction boundary **recoverable**
rather than merely survivable. That does not require saving chats — it requires the handoff to be
complete enough that crossing the boundary loses nothing that mattered. Which is `KH-T01`.
