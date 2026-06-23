---
title: "WS-2 — Inner-loop autonomy & parallelism: honest audit"
status: audit (findings; not a claim)
date: 2026-06-22
scope: project
source: >-
  primary-read of kata-orchestrate / kata-worktree / kata-research / kata-sprint / engram.md / board.md
  + dogfood-selfup-2 & loop-hardening/PLAN-s3b artifacts; benchmarked against Anthropic
  "effective-harnesses-for-long-running-agents" + "managed-agents" and the Hermes (Nous) open agent harness.
tags:
  - kata/audit
  - ws2
  - autonomy
  - parallelism
---

# WS-2 — Honest audit: does the *harness* (inner) loop genuinely run autonomously & in parallel?

**The operator's confidence gap (verbatim-in-intent):** *"I am NOT confident the harness loop genuinely
runs autonomously for long stretches… are we using subagents properly?… is it better than Hermes?"* WS-2's
deliverable is **an honest audit + a validation harness, not a claim.** This file is the audit. The
validation-harness design is proposed at the end (§5) and built separately.

> **One-line verdict.** The harness is **architecturally sound and competitive with Anthropic's and Hermes's
> patterns** — in several respects *stricter* (default-FAIL, fresh-context no-write evaluator, disjoint
> file-ownership, no-re-plan drift control). But its **parallelism is exercised exactly once and has zero
> automated tests**, and its **in-loop learning/research autonomy is almost entirely unwired** (named or
> gated-off by design). It is honest about this in its own docs — there is no silent wiring. The gap is
> *proof and endurance*, not architecture.

---

## 1. Method

Read the primary seams (`kata-orchestrate`, `kata-worktree`, `kata-research`, `kata-sprint`,
`protocol/engram.md`, `protocol/board.md`), then traced every "does a run actually *do* this?" question to
run artifacts (`dogfood-selfup-2/`, `loop-hardening/PLAN-s3b.md` + `REPORT-s3b.md`) and to `tools/` tests.
Benchmarked against two external references the project already cites as `source:` lineage:
Anthropic's long-running-agent + managed-agents guidance, and the Hermes (Nous Research) open agent harness.

---

## 2. Parallelism — designed well, exercised once, untested

### What's designed (strong)
`kata-orchestrate` specifies a genuine **rolling-frontier** model, not wave-batching: a task is dispatchable
iff its `depends_on` are integrated **and** its owned files are disjoint from every in-flight task; dispatch
all dispatchable tasks **concurrently**, each in its own `kata-worktree`; recompute the frontier on each
integration; **escalation is async and does NOT halt the run** (park the escalating task + its dependents,
keep dispatching the rest); hard-wait for a human **iff** the frontier is empty ∧ open human-required
escalations remain. Lateral comms = the append-only `board.md` (`CLAIM/DONE/BLOCK/ESCALATE/NOTE/DECISION/
PROGRESS`; workers never author `DECISION`). This is **at or above** Anthropic's managed-agents decoupling
and Hermes's "spawn N isolated subagents, synthesize" pattern.

### What's actually been exercised (thin)
- **Dogfood #2** (`.planning/specs/dogfood-selfup-2/`) **did** run **4 concurrent workers** (Sonnet) in
  isolated worktrees `d2/slice-a..d`, `depends_on: {}`, **octopus-merged with zero conflicts**,
  `mutation.json allNonVacuous:true`. So the concurrent path **works in practice — once.**
- **S3b** (the loop-hardening finale) was deliberately **two sequential single-worker cycles** — a loop-back
  test, not a parallel sprint (PLAN-s3b says so explicitly). So the most recent "live" runs were *not*
  parallel, which is why it *feels* unexercised.

### The real gap (honest)
- **Zero automated tests** of the orchestration logic. There is **no `tools/` model** of the rolling
  frontier / dependency resolution / in-flight disjointness / completion-order integration, and therefore
  **nothing that asserts** "given this DAG, exactly these tasks dispatch concurrently, this one parks on
  escalation, the frontier recomputes correctly." The concurrency is a **prose contract in `SKILL.md`**
  validated only by a human watching one run succeed. (`mutation_run`, `gate_emit`, `run_result` are
  well-tested; the *frontier* is not modelled in code at all.)
- **n=1 exercise.** One zero-conflict 4-way merge is encouraging but is not evidence the frontier behaves
  under: a non-empty `depends_on` graph, a mid-run escalation that parks a sub-tree, or a partial-failure
  integration. None of those branches has ever executed.

### vs the benchmarks
| Dimension | KataHarness | Anthropic guidance | Hermes |
|---|---|---|---|
| Concurrent isolated subagents | ✅ designed (worktree-per-task) | ✅ managed-agents | ✅ spawn_subagent (auto-parallel on multi-call) |
| Dependency-aware scheduling | ✅ rolling frontier (DAG) | ◐ decompose-into-chunks | ◐ "when to parallelize" in prompt |
| Lateral comms | ✅ append-only board | — | ◐ RPC results |
| Result synthesis after fan-out | ◐ orchestrator gates+integrates per task | ✅ evaluator | ✅ unified by-topic synthesis |
| **Proven by automated test** | ❌ **none** | n/a | partial |
| **Exercised live (multi-worker)** | ⚠️ **once** (dogfood #2) | ✅ | ✅ |

**Parallelism verdict:** architecture is competitive-to-superior; **proof is the deficit.** This is the
single highest-value target for the validation harness (§5).

---

## 3. In-loop autonomy — mostly unwired (by design), and that's the honest headline

The operator wants the *harness* loop to run "internally for long periods with no human": **LEARN** between
iterations, **research internally (RS)**, and **self-grade/QC** within the loop. Status, feature by feature:

| Capability | Status | Evidence |
|---|---|---|
| **Default-FAIL gate** (self-QC floor) | ✅ **wired, never skips** | `kata-orchestrate` final gate → fresh-context no-write `kata-evaluate`; even grill-skip keeps it |
| **Mutation / non-vacuity proof** | ✅ **wired + live-proven** (both dogfoods) | `tools/mutation_run.prove_non_vacuous`; `mutation.json allNonVacuous:true` |
| **Fresh-context no-write evaluator** (no self-cert) | ✅ **wired** | separate Sonnet, `allowed-tools` omits Write/Edit (validator-enforced, NIT-2) |
| **In-loop RS research subagent** (resolve ambiguity w/o human) | ❌ **named, NOT wired** | `kata-orchestrate` grill-skip rung: "the in-loop RS research subagent… *named, not yet wired*"; **zero** `.kata/escalations/` ever produced; `kata-research` exists but **nothing dispatches it** in a real run |
| **Auto-continue-while-green** (run past a boundary w/o human) | ❌ **gated off by default** | `delivery.boundary` default `always-stop`; no run set `incremental` shape; AND-gate is prose, untested |
| **LEARN feed (β)** — emit decision history for a future fingerprint | ⚠️ **built, emit-only, never invoked** | emit-only / **zero CONSULT** (structural); no run set `engram.learnFeed.dir` ⇒ no page ever emitted |
| **Engram CONSULT** — auto-resolve known decisions before asking a human | ❌ **gated off** (future) | `engram.md`: "gated and not wired today" (D9/D56); cognitive-fingerprint synthesis not built |

### The honest bottom line on autonomy
**"Learn between loops" is not happening today, and neither is in-loop research.** What the loop *can* do
autonomously: dispatch → execute (TDD) → **default-FAIL self-QC** → integrate → and only **stop for a human
when frontier-blocked on a LOCKED conflict.** That is real, bounded autonomy and it is safety-first (C2
"fail to the human"). What it **cannot** do today: resolve a novel ambiguity by researching mid-flight
(RS named-not-wired), carry a lesson from one iteration into the next (β emit-only, CONSULT off), or
auto-continue across a sprint boundary (gated off). So "long autonomous stretches" are bounded by
**how often the run hits something only a human or unwired-research can resolve** — and every such point is
a hard stop, not an autonomous resolution.

This matches the project's own design intent (D74 emit-only, D9/D56 CONSULT-gated, C2 fail-to-human) — it is
**deliberate conservatism, not an accident.** The WS-2 decision the operator must make: **light a *bounded*
in-loop learning/research path** (wire the RS researcher into the escalation route as a real call-site; or
turn on β→CONSULT behind a strict confidence+LOCKED guardrail), or **accept human-gated autonomy as the v0.1
posture** and prove the parallelism instead. These are not exclusive; §5 sequences them.

---

## 4. "Better than Hermes?" — the fair answer

**Architecturally, KataHarness and Hermes are siblings** (both use a stable/context/volatile tiered
orientation; both fan out isolated subagents). Where each leads:

- **KataHarness leads on rigor:** default-FAIL evaluation, a *fresh-context no-write* evaluator (no
  self-certification), disjoint file-ownership for conflict-free merges, an auditable drift ledger,
  no-re-plan escalation, supersede-not-rewrite. Hermes optimizes for fluid capability; KataHarness optimizes
  for *not drifting* and *being judged honestly*. For the operator's stated goal (one-shot a complex task and
  trust the result), this is the right bias.
- **Hermes leads on lived autonomy & UX:** it actually **spawns N subagents per turn and auto-parallelizes**,
  **synthesizes results into one unified answer**, and ships **persistent memory + self-improvement** — i.e.
  the exact LEARN-between-iterations loop KataHarness has gated off. Hermes's subagent **tool-restriction**
  pattern (exclude task-mgmt tools to prevent races; minimize blast radius) is a concrete idea worth
  adopting at our worker-dispatch seam. Its by-topic result synthesis is a model for WS-3's closeout.

**So: "better" on discipline and honesty; "behind" on proven parallel throughput and on in-loop
learning/UX.** The credible claim after WS-2 is *"as capable in architecture, stricter in evaluation, and —
once the validation harness lands — provably parallel,"* **not** "more autonomous than Hermes" (we are not,
until learning is wired).

---

## 5. Proposed second deliverable — the validation harness (design next, build after approval)

The audit's companion is **a way to *evaluate* that parallelism is real and the loop's autonomy is what we
claim** — so this never has to be re-argued by reading prose. Proposed shape (to brainstorm → spec → build):

1. **A frontier model with tests (highest value).** Extract the rolling-frontier scheduling logic into a
   small, pure `tools/` module (`dispatch_frontier.py`-ish): inputs = the DAG (`ownership` + `depends_on`),
   events = `integrated(task)` / `escalate(task)`; outputs = the set dispatched concurrently at each step.
   Then pytest asserts: independent tasks co-dispatch; a dependent waits; an escalation parks its sub-tree
   but **not** unrelated work; integration is completion-ordered. This converts the prose contract into an
   **executable, regression-proof** spec — and is reusable by the live orchestrator.
2. **A concurrency-evidence artifact.** Teach the run to emit `.kata/concurrency.json` from board timestamps
   (max in-flight workers, overlap intervals, per-task wall-clock) so a run can be *shown* to have run N
   workers truly concurrently — answering "are we parallelizing or just dispatching serially?" with data.
3. **A small multi-worker dogfood (n→3+).** A purpose-built run with a **non-trivial `depends_on` graph and a
   deliberately-injected escalation**, to exercise the branches dogfood #2 never hit (park-a-subtree,
   frontier recompute, partial integration). The validation harness (1–2) grades it.
4. **An autonomy-posture decision (operator).** Either (a) wire the **in-loop RS researcher** as a real
   escalation call-site (bounded, grounding-gated — the safety rails already exist), and/or (b) accept
   human-gated autonomy for v0.1 and defer β→CONSULT. Pick before WS-3, because WS-3's in-loop narration
   describes whatever autonomy is actually on.

**Sequencing:** §5.1 (frontier tests) → §5.2 (evidence artifact) → §5.3 (multi-worker dogfood) → §5.4
(posture decision). §5.1 is pure-Python and TDD-shaped — a clean first build slice once the design is
approved.

---

## 6. Carry-outs

- This audit supersedes the summary-line claim that S3b's runs prove parallelism — **they don't**; dogfood
  #2 is the only multi-worker exercise, and it is **n=1, untested.**
- No silent wiring was found: every deferred/gated capability is marked as such in its own doc. The repo is
  honest; the deficit is *proof and lived autonomy*, exactly as the operator suspected.
