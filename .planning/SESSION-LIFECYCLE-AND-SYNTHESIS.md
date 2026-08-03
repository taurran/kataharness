---
date: 2026-07-26
kind: correction + architecture decisions
supersedes: the "cheap fix" handoff-section proposal in THIN-ORCHESTRATOR-DOCTRINE.md
---

# THE MAIN SESSION, COMPACTION, AND WHAT WE ACTUALLY SYNTHESIZE

## 1. CORRECTION — the thin-orchestrator doctrine does NOT rescue the model problem

> *"It does matter, if we're doing things like planning, grilling, design doc in the primary window
> that BECOMES the orchestrator."*

**Correct, and my previous answer was incomplete.** I argued that a thin orchestrator makes the
conductor's model largely irrelevant. That is true of the *orchestration* phase — and it ignores that
the main session does the **heaviest judgment work in the entire loop before it ever becomes an
orchestrator.**

The main session has **two phases with opposite model requirements:**

| phase | what happens | judgment load | model sensitivity |
|---|---|---|---|
| **1 — Initiation** | `kata-initiate` → grill → `kata-context` → design doc → plan → freeze | **MAXIMUM.** Interrogating the human, resolving ambiguity, freezing decisions that everything downstream inherits | **CRITICAL** |
| **2 — Orchestration** | assign, dispatch, gate, route escalations | coordination | low, *if* thin |

**The judgment is front-loaded.** A weak model in phase 1 produces a bad frozen plan, and no amount of
downstream elevation recovers it — the plan is frozen and every worker executes against it faithfully.
That is the drift-proof design working *against* us.

So: thin-orchestrator helps phase 2. **Phase 1 needs the right model, full stop**, which makes §3 the
real answer rather than a fallback.

## 2. CAN WE HANDOFF AND COMPACT THE PRIMARY WINDOW? — precisely

> *"Before we stated that we wanted to design a function to handoff and compact the primary window.
> Can we do that?"*

**Split the question, because the two halves have different answers.**

| | can we? |
|---|---|
| **Write a handoff from the main session, at any moment** | ✅ **YES — entirely ours.** It is a file write. Nothing blocks it |
| **Detect that we are approaching the boundary** | ✅ **YES** — `kata_gauge` reads the context bridge; the machinery exists (and has never fired at 0.70 — peak observed 69%) |
| **Programmatically TRIGGER compaction of the main session** | ❌ **NO.** The host owns it. There is no in-window call that compacts the primary session |
| **Know when the host is about to compact** | ✅ **YES** — the `PreCompact` hook fires first |
| **Re-anchor after the host compacts** | ✅ **YES** — `SessionStart(compact)` fires after |

**So the honest design target is not "we compact." It is "we are handoff-ready at every moment, so the
boundary — whoever triggers it — costs nothing."** Three ways across it, all supported:

1. **Host auto-compacts** → `PreCompact` writes the handoff first → `SessionStart(compact)` re-anchors.
   *(This is the leg our own record labels R6 UNOBSERVED — never seen fire.)*
2. **Operator says "handoff to a new session"** → we write a full handoff on demand → operator starts a
   fresh session which loads it. **This is the path the operator asked for and it is fully within our
   control today.**
3. **Operator runs `/compact`** → same as (1).

**What is missing is not capability — it is that none of it has ever been proven to fire.** That is
`KH-T01`, unchanged, but now with a sharper target: *handoff-ready always*, rather than *we manage
compaction*.

## 3. THE MODEL FIX IS SIMPLE — take the simple answer

> *"If they have the wrong model for the run can't we just tell them to use /model to load up the
> correct model before KataHarness goes into gear? It should be easy to address just by telling the
> user to select the correct model when they start."*

**Yes. That is the answer, and my KH-T11 framing over-complicated it.**

It is also the shape of the one precedent already in the repo — the premium "keep-using declined" arm
**hard-stops and advises a `/model` switch, resuming after.** Config cannot change a session's model;
the honest move is to stop and tell the operator *before anything is frozen.*

**KH-T11 simplified to:**
- **Where:** `kata-readiness` (Phase 0), before any grill work — the earliest point, and the cheapest
  place to be wrong.
- **What:** compare the session anchor against the run profile's floor. Advanced/critical work wants a
  high anchor; a sub-Sonnet anchor on an advanced run is a **BLOCK**, not a warning.
- **The message:** plain — *"this run profile wants at least X; you're on Y. Run `/model`, pick X, then
  re-run `/kata-start`."*
- **Not** a mid-run switch, **not** a second session, **not** dispatch gymnastics. Just tell them, early.

Elevating dispatched roles stays available as a *secondary* mitigation for phase 2 — but it is no
longer load-bearing, because we now stop the run before phase 1 with a bad anchor.

## 4. 🔴 WHAT WE ACTUALLY SYNTHESIZE — the operator's suspicion is correct

> *"I'm not even sure we are properly synthesizing anything into second brain right now, which is sad
> too."*

**Measured. It is worse than "not properly" — it is one bucket out of five, never read.**

| page kind | pages |
|---|---|
| `synthesis/decision-patterns` | **269** |
| `concepts` | **0** |
| `entities` | **0** |
| `references` | **0** |
| `sources` | **0** |

And by area: `second-brain` 280 · `professional` 10 · `personal` 14 · `work` 4.

**What the 269 actually are:** one page per LOCKED grill decision — `## Decision` + `## Rationale`,
frontmatter with `produced-by: loop`, a source path, tags. **The individual page quality is genuinely
good.** The problem is everything around it:

- **One emitter, one bucket.** We emit grill decisions and nothing else. Four of five defined page
  kinds have never received a single page.
- **Nothing is ever read back** (confirmed by probe — `recall.py` has no CLI and zero Python callers).
  It is a write-only archive.
- **No project rollup, no temporal narrative, no cross-project synthesis.** 269 atomic decisions with
  nothing that turns them into knowledge.
- **The vault already ships the machinery we are not feeding** — `wiki-ingest`, `wiki-lint`,
  `research-init`, `research-promote`, `kiban-update`, `profile-build` all exist as vault skills.

**This is the same disease again**: a capability described (a "second brain") where only the narrowest
mechanical slice was ever built, and nothing verifies the rest.

## 5. ✅ ADOPTED — the project wiki, not saved chats

> *"Rather than chat saving we rely on the synthesis process to the project in the form of a project
> wiki that updates via llmwiki throughout, with temporal entries … handoff is for more ephemeral
> transition/transactional transitions to other sessions. The project based wiki is more for
> long-living decision points and such. Things that are synthesized and on tap."*

**Adopted. This supersedes my "add a "what was tried and rejected" handoff section" proposal**, which
was the cheap fix. This is the right one, and it uses a strength instead of bolting on storage.

**The split, stated cleanly:**

| | **Handoff** | **Project wiki** |
|---|---|---|
| Lifetime | **Ephemeral / transactional** | **Long-lived** |
| Purpose | get the *next session* running | keep decisions *on tap* |
| Content | current state, next step, ground truth | decision points, rationale, temporal narrative |
| Read by | the successor session, once | anyone, any time, repeatedly |
| Shape | one document, superseded each time | accreting wiki with temporal entries |

**Why this beats saving transcripts:** a transcript is raw and unbounded; a wiki is *synthesized and
curated*. We already have the emitter, the page schema, the redaction filter, and the vault. **We are
using perhaps 20% of it.**

**What has to be decided (grill material):**
1. **Where in the Vault a project wiki lives.** Today everything lands in
   `second-brain/wiki/pages/synthesis/decision-patterns/` regardless of project — flat, with the
   project encoded in the *filename* (`kagami--kagami-v2--b1.md`). A project wiki needs its own home
   and a rollup page.
2. **Temporal entries** — what triggers one, and what it contains. Per run? Per phase? Per decision
   cluster?
3. **The promotion path to personal / professional / work.** The operator's *"tie it into decision
   making in the bigger picture"*. Those areas hold 28 pages between them; the machinery exists
   (`research-promote`, `kiban-update`) and is unfed.
4. **Read-back.** A wiki nothing reads is the archive we already have. **This is the load-bearing
   half** — and it is the same gap as `recall.py` having no caller.

## 6. Recorded — what KataHarness is for

> *"We've conceptualized everything but struggled at execution … KataHarness's strength is validation
> and determinism. Not fast and loose execution."*

Recorded as the framing that should decide close calls. Where a choice is between *more capability* and
*proving the capability we claim*, take the proof. The gap between this harness and a wrapper around
default tools is entirely whether the process is **enforced** or merely **described** — and this week's
evidence is that too much is described.
