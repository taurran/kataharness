---
date: 2026-07-26
kind: tasks + backlog from the 2026-07-26 architecture session
status: all UNBUILT — these are the decisions, itemized for execution
---

# ARCHITECTURE TASKS — from the 2026-07-26 session

Every architectural decision made this session, itemized. Detail is deliberate: the next session must
be able to execute these **without re-deriving the reasoning.**

---

## KH-T12 — Document the thin-orchestrator doctrine as binding · **SMALL, do first**

**Decision (operator-adopted):** *"A well-behaved orchestrator does not do the work itself."*

**Why it is more than a slogan:** it is what **decouples run quality from the model the operator
launched with** — every act of judgment happens in a dispatched agent whose model can be elevated,
while the conductor only coordinates.

**Where it must land:**
- `AGENTS.md` — as a spine principle (it constrains the orchestrator's role definition)
- `protocol/` — the orchestrator's own contract
- `CONTEXT.md` — pinned term
- `skills/coordinate/kata-orchestrate/SKILL.md` — bump-on-modify

**Provenance for the doc:** independently stated by Hermes (*"a well-behaved orchestrator does not do
the work itself"*), Anthropic Workflows (*"No direct filesystem or shell access from the workflow
itself — the script coordinates the agents"*), and the BMAD community variant. **Take the principle,
not DF-05's withheld thin-orchestrator feature** — its authors measured only the cost half and
recommend against adopting it.

**Honest residual to record:** the conductor cannot reach zero judgment. It still routes, reads gate
output, decides escalations, interprets drift. A floor exists — just far lower than today's "the
anchor is the ceiling for all critical work."

---

## KH-T13 — Dispatch design-doc and plan authoring as roles · **the big one**

**Decision:** design-doc authoring and plan authoring move OUT of the main session into dispatched
roles. The grill does **not** — see the structural reason below.

### The split, and why the line falls where it does
The dividing question is **"does this need to talk to the human?"** Subagents cannot —
`AskUserQuestion` is withheld from them structurally.

| activity | dispatch | reason |
|---|---|---|
| Grill | ❌ NO | **`D70`: "the grill's engine is interrogating the human, which is OFF in autonomous mode."** A grill with no human degenerates into an autonomous planning pass. Also: the infer-then-confirm gate needs each value named + confirmed by the human; dual control needs a live channel for "execute" |
| `kata-context` | 🟡 | rides the grill |
| ELEVATE | 🟡 | generate dispatched → present in-session |
| **Design-doc author** | ✅ YES | no human channel needed; synthesizes frozen grill output |
| **Plan author** | ✅ YES | no human channel needed; decomposes a frozen design |
| Freeze-gate review | ✅ | already dispatched |

### Ranked benefits (model control is THIRD, not first)
1. **Removes the largest context load from the main session.** Today the main window absorbs the grill
   conversation **plus** full generative authoring of both documents, *then* becomes the orchestrator.
   Dispatching leaves the session holding the conversation + the artifacts, not the drafting. Same move
   Anthropic gives as the Workflows rationale, one phase earlier.
2. **Makes the doctrine consistent.** Authoring a design doc **is** doing the work. Phase 1 is the one
   place the conductor personally writes the most load-bearing artifacts in the run.
3. **Model control** — a dispatched author takes an explicit model override.
4. **Gives `KH-T10` somewhere to land** — a dispatched author is a *role* that can carry a real spec.
5. **Advisor consults become natural** through existing machinery.

### Costs to resolve at grill — do NOT build past these
1. **The conductor must gate artifacts it did not author, and that rubric does not exist.** Precedent
   is default-FAIL on returned build work, but a design doc is judged differently from a diff.
2. **A dispatch level**, on an unstable number — Claude Code's depth default swung **5 → 1 → 3 across
   four releases.**
3. **Lossy return boundary.** Mitigation: **return the artifact as a FILE**; the payload is a path +
   verdict, and the conductor reads the file.
4. **🔴 Who writes `INTENT.md`.** `intent_scaffold.write_intent` is sole authorized writer; conductor is
   sole main-tree git writer. A dispatched author returns content for the conductor to write, or
   writes into a worktree. **Decide explicitly or we breach single-writer discipline on day one.**

### Target shape
```
MAIN SESSION — keeps exactly TWO things: the human conversation, and authority to freeze
├── grill · kata-context · ELEVATE-present · freeze INTENT.md   [in-session]
├── design-doc author ...... DISPATCHED · own model · own spec · returns a FILE
├── freeze-gate review ..... DISPATCHED (already)
├── plan author ............ DISPATCHED · own model · own spec · returns a FILE
├── plan check ............. DISPATCHED (already)
└── ORCHESTRATION .......... thin
```

### Open grill questions
What gate does a returned design doc face · is ELEVATE's split real or over-engineering · does the
design-author get the full grill ledger or a distilled brief · depth budget if design/plan take a level.

---

## KH-T11 (SIMPLIFIED) — anchor vs run-profile check at readiness

**Operator simplified this; my earlier framing over-engineered it.**

> *"Can't we just tell them to use `/model` to load up the correct model before KataHarness goes into
> gear?"* — **Yes. That is the answer.**

- **Where:** `kata-readiness` Phase 0 — before any grill work, the cheapest place to be wrong.
- **What:** compare session anchor against the run profile's floor.
- **Response: BLOCK**, not warn. Plain message: *"this profile wants at least X; you're on Y. Run
  `/model`, pick X, then re-run `/kata-start`."*
- **Precedent:** the premium "keep-using declined" arm already hard-stops and advises a `/model`
  switch. Same shape.
- **NOT** a mid-run switch, **NOT** a second session, **NOT** dispatch gymnastics.

**The measured gap this closes:** there is **no minimum-anchor check anywhere.** At a `haiku` anchor,
critical work resolves to `None` → inherit → **the grill, plan, default-FAIL gate and adversarial
reviewer all run on haiku**, with nothing warning. `KH-T13` narrows the exposure to the grill alone,
but does not remove it.

---

## KH-T14 — The project wiki · **supersedes the chat-saving idea**

**Decision:** we do **NOT** save transcripts. We synthesize into a **project wiki** with temporal
entries, in the Vault.

### The split
| | **Handoff** | **Project wiki** |
|---|---|---|
| Lifetime | ephemeral / transactional | long-lived |
| Purpose | get the next session running | keep decisions **on tap** |
| Content | current state, next step, ground truth | decision points, rationale, temporal narrative |
| Read by | successor session, once | anyone, repeatedly |
| Shape | one doc, superseded each time | accreting wiki |

**Why not transcripts:** Cursor needs *"chat history as files"* because their compaction is lossy **and
they have no curated decision record.** We have `DECISIONS.md`, grill ledgers, `LESSONS-LEARNED.md`.
A searchable transcript is a worse version of something we already do better — and unbounded.

### 🔴 The measured state of our synthesis — worse than "thin"
| page kind | pages |
|---|---|
| `synthesis/decision-patterns` | **269** |
| `concepts` · `entities` · `references` · `sources` | **0 each** |

By area: `second-brain` 280 · `professional` 10 · `personal` 14 · `work` 4.

One emitter, one bucket, **never read back**. No project rollup, no temporal narrative, no
cross-project synthesis. Individual page quality is genuinely good (`## Decision` + `## Rationale`,
provenance frontmatter, wikilinks) — everything *around* it is missing. **The vault already ships
`wiki-ingest`, `wiki-lint`, `research-init`, `research-promote`, `kiban-update`, `profile-build` — all
unfed.**

### To decide at grill
1. **Where a project wiki lives in the Vault.** Today everything lands flat in
   `second-brain/wiki/pages/synthesis/decision-patterns/` with the project encoded in the *filename*
   (`kagami--kagami-v2--b1.md`). A project needs its own home + a rollup page.
2. **Temporal entries** — trigger and content. Per run? Per phase? Per decision cluster?
3. **Promotion path to personal / professional / work** — the operator's *"tie it into decision making
   in the bigger picture."* 28 pages total across those three; machinery exists, unfed.
4. **🔑 Read-back — the load-bearing half.** A wiki nothing reads is the archive we already have. Same
   gap as `recall.py` having no CLI and zero Python callers.

---

## KH-T01 (REFINED) — handoff-ready always, not "we compact"

**Refinement from this session:** the design target is **not** "we manage compaction." We cannot
trigger it. It is **"handoff-ready at every moment, so the boundary costs nothing whoever triggers
it."**

| capability | ours? |
|---|---|
| Write a handoff at any moment | ✅ **entirely ours** — a file write |
| Detect the boundary approaching | ✅ `kata_gauge` (never fired at 0.70; peak 69%) |
| **Trigger** main-session compaction | ❌ **NO — the host owns it** |
| Know it is imminent | ✅ `PreCompact` hook |
| Re-anchor after | ✅ `SessionStart(compact)` |

**Three crossings, all must work:** host auto-compact · operator says *"handoff to a new session"*
(**fully in our control today**) · operator runs `/compact`.

**Borrowings, ranked:** Cursor's recoverable-boundary idea (**without** saving chats — `KH-T14` is how)
· Hermes's session-rotation-with-lineage (close the session row, create a child seeded by the summary
with a parent pointer) · Magentic-One's stall counter (≤2 non-progressing iterations → forced replan).

---

## KH-B41 — Kanban / unified task management

**Six planning surfaces today with no single view and no state machine:** `BACKLOG.md`, `ROADMAP.md`,
per-spec `PLAN.md`, `.kata/board.md`, `DEFERRED.md`, plus this session's ingest docs. ⚠️ **This session
added 13 more documents — the problem is now worse, and that is an argument for this item, not against
recording it honestly.**

**Steal from Hermes:** the **state machine** (`ready → claimed → done/failed`, with crashed-worker
reclaim), **one durable row per task**, **handoff-as-a-row** rather than handoff-as-a-document.
**Do NOT steal:** SQLite as the store — our artifacts are deliberately Obsidian-readable markdown and
that is a real property we would lose.

**The visual layer is the operator's actual ask** and is cheap once a durable store exists.

---

## KH-B42 — The conductor-gates-what-it-did-not-author rubric
Falls out of `KH-T13`. We gate returned *build* work default-FAIL. **We have no rubric for judging a
returned design doc or plan.** Blocks `KH-T13` from shipping.

## KH-B43 — Cross-host agent identity
From the Kiro observation (host defaults `Forge`/`Momus` visible during our runs). **The same run may
produce different agents on different hosts, with nothing surfacing it.** An adapter-contract gap, not
a prompt-quality gap. Feeds `KH-T10`.

---

## RECORDED FRAMING — the tiebreaker for close calls

> *"KataHarness's strength is validation and determinism. Not fast and loose execution."*
> *"We've conceptualized everything but struggled at execution."*

**Where a choice is between more capability and proving the capability we claim, take the proof.** The
gap between this harness and a wrapper around default tools is entirely whether the process is
**enforced** or merely **described** — and this week's evidence is that too much is described.
