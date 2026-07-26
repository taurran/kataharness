---
date: 2026-07-26
kind: correction + new tasks
severity: propagated outbound — MindBridge received the wrong characterization
---

# CORRECTION — we are NOT "scripts-first"

## What happened

The operator, 2026-07-26:

> *"I don't know if we're 'scripts first'. I think KataHarness should be **'prose first, scripts when
> optimal'**."*

The pinned glossary term said the opposite. `CONTEXT.md` carried **"Determinism-first
(script-where-deterministic)"** — *"anything rule-decidable … lives in a script, with prose only wiring
it in."* That makes a script the **default** for a whole class of mechanism. The operator's
architecture makes prose the default and a script an **optimization with a burden of justification.**

Provenance, stated plainly: the term was authored in `af29795` by a **prior session**, not by me. But I
**amplified it, built arguments on it, and shipped it outbound** without ever checking it against the
operator. That is the same class of failure as the DET registry — a record asserting something nobody
had re-confirmed.

## Where it propagated

| where | status |
|---|---|
| `CONTEXT.md` architecture principle (the pinned term) | ✅ **corrected** |
| `.planning/BACKLOG-FROM-MINDBRIDGE.md` KH-B09, KH-B38 | ✅ corrected |
| `.planning/INGEST-PLAIN-ENGLISH.md`, `MERGEBACK-INGEST.md` BL-M12 | ✅ corrected |
| `.planning/OPERATOR-RULINGS-2026-07-26.md` KH-T05 | ✅ reframed |
| **The outbound alignment package** (`mindbridge-alignment-rev2.zip`) | ⚠️ **SENT WITH THE WRONG TERM** |

**MindBridge was told our architecture is scripts-first**, and `DF-01`'s "HOLD your architecture, keep
ours" framing rests partly on that. The two harnesses are **closer than the package represents**. This
goes in the return handoff (`KH-T09`).

## The tension worth keeping visible

The operator's principle and this week's evidence pull in different directions, and pretending
otherwise would be the same dishonesty we keep finding:

- **Operator's design intent:** prose-first, scripts when optimal.
- **This week's measurement:** every subsystem with a code owner came back working; every invariant
  living only in a `SKILL.md` sentence came back unverifiable or quietly broken.

These reconcile if **"enforcement" is one of the things that makes a script optimal** — which is how
the corrected term now reads. Prose-first is the default; it is **not** a licence to leave a gate,
score, hash, or enforcement obligation in prose. `KH-T05` is where that test gets nailed down properly
rather than asserted.

---

# NEW TASKS

## KH-T10 — In-depth review and optimization of every agent we use · **operator-directed**
> *"We're just kind of using 'standard coding agent' and 'generic adversarial validator' for our
> agents. We really need to dive in and optimize them to make sure we are exceeding industry standard."*

This **supersedes and broadens** `KH-B14` (their BL-018), which only asked for a roster review.

**The honest current state:** our agents are defined almost entirely by the *prompt we happen to write
at dispatch time*. There is no per-agent specification, no rubric for what a good coding agent brief
contains, no measurement of whether one agent type outperforms another, and no version history on any
of them. The adversarial reviewers have earned their keep repeatedly this week — but by ad-hoc briefs,
not by design.

**Scope:**
1. **Enumerate every agent role we actually dispatch** — coder, adversarial reviewer, evaluator,
   researcher, validator, advisor, probe. For each: what defines it today, and where.
2. **Write a real specification per role** — inputs, forbidden actions, output contract, escalation
   path, what it must refuse.
3. **Rubrics for the judges** (their BL-018's strongest point): what PASS *means* per check, scored and
   evidence-anchored, so verdicts are consistent across runs — plus how a rubric stays in sync with the
   evaluator so they don't drift apart.
4. **Assess redundancy vs gaps** across the review legs — where are we double-covering, where is
   nothing looking?
5. **Benchmark against industry practice**, not just against ourselves.

**Grill tier: advanced.** These agents gate everything else.

## KH-T06 (EXPANDED) — Orchestrator: main session or persistent subagent?
> *"I would like to know how Pi and Hermes do it. And assess best practice. Are we using the main
> session wrong?"*

**What we already have, honestly:**
- **Hermes — we DID formally assess it.** `D69` (2026-06-18) is a recorded bake-off. We **adopted** its
  tiered prompt assembly (stable→context→volatile, now our `D63` orientation contract), its protected
  head+tail compaction with tool-call/response pairing (`D67`), `.usage.json`-style telemetry, and
  stale→archive curation. We **rejected** its no-gate instant-universal skills and its opaque user
  model. ⚠ **But that bake-off never covered orchestrator placement** — it was about learning,
  compaction, and prompt assembly. It does not answer this question.
- **Pi — we have no assessment at all.** It appears as a platform target in our tooling. We have never
  studied its architecture. I am not going to characterize it from memory.

**So this needs real research, not recall.** Deliverable:
1. How Pi and Hermes actually place the orchestrator — researched and cited, not asserted.
2. What our current constraint costs us: `kata_roles.HOST_ONLY_ROLES` pins **orchestrator and
   evaluator** to the host (`LD11`, a v1 decision). Why was it made, and does the reason still hold?
3. The concrete trade: a subagent orchestrator gets a fresh context budget and stops the main session
   being the thing that runs out — but inherits dispatch-depth limits, tool-access differences, and the
   question of who owns the git tree (today: conductor is sole main-tree writer).
4. **A recommendation with the reasoning shown.**

**Coupled to `KH-T01`.** If the orchestrator stops being the main session, the main session's handoff
problem changes shape entirely — so these two get grilled together, not separately.

## Standing instruction recorded
> *"We don't need to execute half-cocked. These are critical so we should be grilling a lot
> throughout."*

Every item in `KH-T01`, `KH-T02`, `KH-T05`, `KH-T06`, `KH-T10` gets its **own grill before any build**.
No batching, no "obvious" changes waved through. Recorded so a later reviewer can hold this run to it.
