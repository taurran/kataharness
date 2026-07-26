---
date: 2026-07-26
kind: operator-rulings
status: RECORDED — these are decisions, not proposals
---

# OPERATOR RULINGS — 2026-07-26

Decisions on the plain-English queue, recorded in-repo so any later grill or review can cite them
rather than a transcript.

## Rulings on the queue

| # | item | ruling |
|---|---|---|
| 9 | Bugs travel backwards to MindBridge | **YES — tell them.** Build a return handoff **after** we work through current items, not now |
| 10 | Crash recovery deletes live branches | **"Pretty big deal."** Fix here **AND warn MindBridge in that handoff** |
| 11 | Stale results file accepted by the gate | **Optimize it** — proceed |
| 12 | Prime Directives can be inverted and pass | **"Well shit. We need to harden this. It is prime directive. It shouldn't have a workaround. We need everything to be built and confirmed or approved by the user."** → **KH-T02, top of queue** |
| 13 | Reviewer independence unverified | **Sure, should check** — proceed |
| 14 | Version-bump rule not enforced | **Harden it** — proceed |
| 15 | Log line miscounting | **Do it** |
| 16 | Read files back after writing | **Confirm the token cost first**, or find a lightweight evaluation. **If there is no token cost, just do it** |
| 17 | Automatic reproducibility checker | **Wants to understand it.** Questions: can it bake into our current validation standards? Should it be in the smoke check since it's about reproducibility? Part of standard adversarial review? **All of the above?** → answered in KH-T03 |
| 18 | Six new doctrine rules | **Wants to understand before deciding** → answered in KH-T04 |
| 20 | Rebuild the code map | **Yes** — plus the architecture questions below |
| — | The whole "worth building" backlog | **"Worth building is ALL OF IT."** Nothing is dismissed. Now itemized in `BACKLOG-FROM-MINDBRIDGE.md` |
| — | Lightweight orchestrator | **"A good one"** — keep |

---

## NEW TASKS FROM THIS RULING

### KH-T01 — Automated handoff must actually work · **BIG DEAL, operator-flagged**
> *"The handoff enforcement issue is a BIG DEAL … We have code for it but I don't see it properly
> engaging. I've never seen the parent agent actually recycle context on its own with proper
> handoffs."*

Confirmed by testing: the trigger has **never fired** in a real session (peak observed 69% against a
70% threshold), boundary-supersedes-self is prose with **zero code**, the staleness comparator does
not exist, and **no real handoff has ever carried its provenance fields.**

**Required scope — all three levels:**
1. **Subagents** — a worker that ends must leave a durable handoff.
2. **Orchestrator** — must recycle its own context at a boundary.
3. **The main session** — the one that has never worked. Including the manual path: saying
   *"handoff to a new session"* must trigger a **full context update, an in-depth handoff, and a
   persisted orientation** for the successor.

**Open question to resolve in the grill, operator-raised:**
> *"Do we need orientation if it is automated, or is handoff good enough and orientation a waste of
> tokens?"*

My initial read, to be tested not assumed: handoff carries *state*, orientation carries *how to
behave*. If the successor loads the same skills and prime directives from disk anyway, orientation
may be largely redundant with what the harness injects at launch — which would make it duplicated
tokens. **Measure both, don't argue it.**

### KH-T02 — Harden the Prime Directives so there is no workaround · **TOP OF QUEUE**
> *"It is prime directive. It shouldn't have a workaround. We need everything to be built and
> confirmed or approved by the user."*

The current check greps for seven words. A rewrite inverting both directives passed green.

**Scope:** replace word-presence with something that cannot be satisfied by an inverted document —
options to grill: a content hash with an explicit golden-update step, pinning the load-bearing
*phrases* rather than tokens, or a semantic conformance check. **Plus** the operator's stronger
requirement: **nothing is "done" unless it is built and either machine-confirmed or explicitly
approved by the user.** That is a bar above what PD-2 currently states, and it needs its own wording.

Note: this makes the incoming MC-07 proposal (their BUILT/WIRED/GATED vocabulary) an input, not the
answer — theirs gives a vocabulary and one decidable rule; the operator is asking for enforcement
with no escape hatch.

### KH-T03 — Where does the reproducibility checker belong? · **answers ruling 17**
Operator asked whether it belongs in validation standards, the smoke check, standard adversarial
review, or all three. **Short answer: three of the four, at different strengths.** Full reasoning
lives in the response; the task is to grill and wire it:

- **Skill validator** — as a report-only counter first, because it currently flags 101 sites here and
  ~59 are false alarms from an exception our own rules make. It cannot gate until that carve-out lands.
- **Standard adversarial review** — **yes, strongest fit.** Reviewers already hunt this class by hand;
  giving them a machine pre-pass makes the finding cheap and consistent.
- **Smoke check** — **no, and the distinction matters.** Reproducibility is *"same input, same output."*
  Smoke (KH-B03) is *"the same data made it through every hop."* Different failure classes; merging
  them would blur both.
- **The gate** — eventually, per-law, only after triage.

### KH-T04 — Understand the six proposed doctrine rules before deciding · **answers ruling 18**
Produce a plain-English brief on each of the six, what it would cost us, and whether it survives our
architecture — then decide. **Hard prerequisite:** verify their claim that the additions *narrow*
rather than widen where human judgment is allowed. That claim is unverified and it is the crux.

### KH-T05 — Determinism doctrine vs. when code is actually REQUIRED · **operator assessment**
> *"Is there a necessity that we go outside of context as code, but are able to marry determinism
> doctrine with ACTUAL REQUIREMENTS to use code? … We can be more precise here since the no-code
> requirement isn't as strong. If determinism doctrine truly does unlock context as code we use it.
> If we need code, we make the assessment of its criticality and enhance our function here."*

This is the policy question behind every finding this week. MindBridge is prose-first **because their
host forced it**; we are scripts-first by choice. Their doctrine is a way to make prose *safe*. Ours
can simply require code where code is warranted.

**Deliverable:** a written rule for when a mechanism MUST be code here rather than prose — and the
honest test of whether their doctrine genuinely makes prose safe enough to keep in the cases where we
currently use it. **KH-B39** (grep every promise for its producing code site) is the enforcement arm.

### KH-T06 — Is the orchestrator the main session, or a persistent subagent? · **operator question**
> *"We need to lean less on the main session. Let's determine if orchestrator is the main session or a
> persistent orchestrator subagent. What is best practice? Are we using the main session wrong?"*

Today our contract pins the orchestrator role to the **host/main session** (recorded as a v1
constraint). The operator is asking whether that was right.

**To resolve:** what breaks if the orchestrator is a subagent (dispatch depth, tool access, context
lifetime, who owns the git tree); whether a persistent orchestrator subagent survives long enough to
be useful; and what it would buy — chiefly that the main session stops being the thing that runs out
of context. **Directly coupled to KH-T01**, because if the main session isn't the orchestrator, the
main session's handoff problem changes shape entirely.

### KH-T07 — Installed vs. prototype: which source does natural language execute from?
> *"We need KataHarness to execute from the INSTALLED version based upon code. Maybe differentiate
> between what natural language executes from installed canonical vs the cutting edge
> uninstalled/prototyped version."*

Right now the two can silently diverge — our installed copy currently lags master, and the session
target toggle is the only thing distinguishing them. Define which source is authoritative for
execution, make the distinction explicit at run start, and make a mismatch visible rather than
incidental.

### KH-T08 — Criticality: a measure, or derived from modality?
> *"We could either have a criticality measure, or assess it from the content vs the modality
> advanced/standard/economy. Typically the critical stuff will be designated advanced right?"*

Largely yes today — critical work runs at the anchor and advanced buys the deepest tiers. But the
mapping is **implicit**, and KH-B31 found that nothing in code even reads the mode. Decide whether
criticality becomes a first-class declared property or stays derived — and if derived, make the
derivation executable rather than assumed.

### KH-T09 — Return handoff to MindBridge · **deferred by operator ruling**
Build **after** we work through current items. Must include, at minimum:
- The **crash-recovery branch-deletion hazard** (ruling 10 — operator explicitly asked they be warned).
- That **defects travel backwards through an ingest** (ruling 9), with our five reappeared defects as
  the worked example.
- The **DF-06 request** — the withheld-item note that never arrived.
- Two citation errors in their package.
- Our verification results where they bear on their own claims — notably that **MC-08's premise is
  partly wrong** (we already shipped that resolver) and that their **`[::2]` counting bug class**
  is worth checking for on both sides.
