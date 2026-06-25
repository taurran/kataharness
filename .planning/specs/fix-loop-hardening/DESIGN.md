---
title: "Fix-loop hardening — material re-verification + thrash→re-plan budget"
status: FROZEN (DESIGN) — freeze-gate HOLD→resolved; re-confirm pending
date: 2026-06-24
spec: fix-loop-hardening
decision: D100 (on merge)
source: >-
  operator strategy session 2026-06-24 (the "shorten-on-fail / does it churn?" thread) + the Approach-A
  hardening named in D99. Composes existing primitives — no new machinery.
tags:
  - kata/coordinate
  - fix-loop
  - thrash-guard
  - no-new-python
---

# Fix-loop hardening — bound the loop, scope the re-verification

## Problem
The orchestrator's fix-loop today is **"NEEDS_WORK → targeted fix against the same plan → loop to PASS"**
(`kata-orchestrate` Final gate) — and it is **under-specified in two ways** that the operator flagged:

1. **Re-verification is unscoped.** After a fix, nothing says *what* to re-run. Re-running the full
   expensive stack (every fresh-context judge) after each fix is wasteful; re-running nothing risks a late
   fix silently invalidating an earlier PASS.
2. **The loop is unbounded.** `fail → fix → fail → fix …` has no stop signal. That is the **churn the spine
   fears** ("many small repeatable changes make it *longer*") — and the case where a fix *should have been a
   re-plan* gets band-aided indefinitely instead.

Neither is a new-machinery problem: the escalation valve, the drift ledger, `kata-diagnose`, and
footprint/blast-radius reasoning **already exist**. This spec *wires a rule and a budget between them*.

## The two rules

### Rule 1 — Material re-verification (conservative, footprint-cited)
After a targeted fix:
- **Always re-run the cheap deterministic gate** (pytest / validator / lint / scan) — fast, idempotent.
- **Re-run a *fresh-context* judge** (`kata-evaluate` / `kata-review`) **iff the fix's footprint** (the files
  it changed, per `.kata/footprint.json.changed`) **intersects a file that judge's findings cited.** **If the
  intersection cannot be determined, the fix is treated as material and the judge is re-run** (indeterminate ⇒
  re-run — **fail-safe**). This is a *files-cited* intersection, **not** the code-symbol "blast-radius" relation
  (which does not range over a judge's prose findings) — keep the two terms distinct.
- **After the *final* batch of fixes, run exactly ONE full-stack confirmation pass** to catch cross-fix
  interaction. The confirmation pass = the cheap gate **+ a re-run of `kata-evaluate`** (cross-fix breakage is a
  conformance question). The standing adversarial `kata-review` (D98, Final-gate step 6) runs **once, after the
  confirmation pass settles, on the final post-fix artifact — never inside the loop.** A fix made *in response
  to* the red-team re-enters at the confirmation pass (so what was attacked is what ships), governed by the
  thrash budget.

### Rule 2 — Thrash budget → diagnose-first, then deliberate re-plan
- Track **fix-cycles two ways** — a **per-area** count (keyed on the task) and a **run-level** count — as
  **transient orchestrator in-context bookkeeping during the final-gate fix loop.** The orchestrator *runs* the
  eval→fix→re-verify loop, so it **counts its own iterations as it goes** — the live escalate-at-N decision
  needs no persistence. The orchestrator's **existing `DECISION` board lines** (it already writes one per gate
  decision, e.g. `NEEDS_WORK fix: …`) are the **durable recount trail** for a mid-loop resume. **No new board
  TYPE, no `state.json` field, no new Python** (see L4). *(The board records no "NEEDS_WORK→fix" event TYPE; the
  count is the orchestrator's own loop state, audit-traceable via its DECISION lines — not a parsed board event.)*
- **Per-area:** when the **same area** hits **N=2** (the **3rd** failure of one area), STOP looping on it.
- **Run-level ceiling:** a total fix-cycle ceiling catches **A-breaks-B oscillation** that a per-area count
  (which resets on that task's PASS) would never trip. A confirmation-pass regression (Rule 1) **counts against
  the budget** — a PASS later invalidated does **not** zero the count.
- On hitting **either** budget, **dispatch `kata-diagnose` FIRST** (cheap, no human) for a root-cause pass that
  returns a **fix-problem vs plan-problem** verdict. **The human valve fires only on a *plan-problem* verdict** —
  a legitimately-hard-but-fixable area is **not** a human interrupt; only a genuine plan defect is.
- A plan-problem escalates as a **re-plan candidate** through the **existing `human-required` escalation kind**
  (no enum change — the thrash distinction lives in the payload's `decisionNeeded`/`rationale` + a routing note
  that `kata-diagnose` ran first), **async-parked** per the existing async-escalation contract (park task +
  DAG-dependents; frontier keeps draining). **Deliberate, human-gated, supersede-not-rewrite; never silent**
  (spine #2: *re-planning is an event, not a habit*). The missing **bridge** between "fix loop exhausted" and
  "deliberate re-plan."

## Why this is the right shape (not "full stack every time", not "fix-one-rerun-all")
The efficient topology is a **staged cascade**: cheap deterministic gates gate the expensive fresh-context
judges (already the order); within each judge, **all findings at once → one batch fix → re-verify by
blast-radius**; the thrash budget makes the loop **terminate by escalating**, not by giving up or churning.
"Full-stack-every-time" is cleaner to reason about but pays for doomed builds; "fix-one-rerun-all" is the
churn trap. This spec is the middle, and it is **the spine's own conclusion** — forbidding silent re-planning
*and* unbounded fixing forces an explicit bridge between them.

## C-arc tie-in (forward value)
The thrash budget is **also the safety rail for the future `Reason`/C-arc** (D99): every `Reason`-approved
re-plan counts against the same budget, so repeated engram-approved drift on one area **escalates to the
human** instead of compounding. Building it now **pre-builds a C-arc safety** and the thrash-seam where
`Reason`'s lowest-risk decisions first plug in.

## LOCKED decisions
- **L1 — Material re-verification (conservative).** Always re-run the cheap gate; re-run a fresh-context judge
  **iff** the fix footprint (`.kata/footprint.json.changed`) intersects a file that judge's findings cited;
  **indeterminate ⇒ re-run (fail-safe, LOCKED).** One confirmation pass after the final fix batch = cheap gate
  **+ `kata-evaluate`**; the D98 `kata-review` runs **once after it settles, never inside the loop.** A
  *files-cited* intersection, **not** the code-symbol "blast-radius" relation.
- **L2 — Thrash budget (two counters, orchestrator-in-context).** A **per-area** count (keyed on task, **default
  N=2** → 3rd failure) **and** a **run-level** fix-cycle ceiling so cross-area oscillation can't hide. Both are
  **transient in-context counts** the orchestrator keeps while running the fix loop (it counts its own
  iterations); the existing `DECISION` board lines are the durable recount trail — **not** a `state.json` field,
  **no new board TYPE.** A confirmation-pass regression counts against the budget (a later-invalidated PASS does
  not zero it). **N=2 + the ceiling are provisional defaults pending dogfood calibration** (no evidence yet —
  stated honestly; not hard-trusted).
- **L3 — Thrash → diagnose-first → deliberate human-gated re-plan.** At budget, `kata-diagnose` (resolved tier)
  returns **fix-problem vs plan-problem**; **the human valve fires only on plan-problem**, via the existing
  `human-required` kind (**no enum change** — distinction in `decisionNeeded`/`rationale`), **async-parked** per
  the existing contract, **supersede-not-rewrite, never silent.** Spine #1/#2 preserved.
- **L4 — No new committed Python; counter is orchestrator in-context.** The fix-cycle counts are the
  orchestrator's own loop bookkeeping during the final-gate fix loop (it counts its eval→fix iterations);
  the existing `DECISION` board lines provide a recount on resume — **no `tools/` change, no `update_task`/
  state-schema change, no new board TYPE.** **Non-code-bearing** (`.md` only). (`prefer-in-context-over-new-python`.)
- **L5 — Batch-fix + staged-cascade (made explicit).** Within one judge's findings: collect **all** → fix in
  **one batch** → re-verify that judge (never fix-one-rerun-one). The cheap→expensive gate *ordering* (a red
  test never reaches a fresh-context judge) is reaffirmed.
- **L6 — Additive between the gates.** This changes **neither** the default-FAIL gate, the no-self-cert rule,
  **nor** the escalation contract — it **bounds and scopes** the loop *between* them. The conformance floor is
  untouched (D22).

## Freeze-gate review (2026-06-24) — HOLD → resolved
A fresh-context adversarial freeze-gate returned **HOLD** and caught four real design holes; all resolved above:
- **B1 ("material" referenced non-existent machinery)** → L1 re-scoped to a *files-cited* footprint intersection
  (no judge "evidence basis" exists; "blast-radius" is the code-symbol relation — kept distinct). Operator chose
  the **conservative rule** (b): when in doubt, re-run.
- **B2 (unsafe default)** → **indeterminate ⇒ re-run** is now LOCKED in L1.
- **B3 (`kata-diagnose` tie-in: wrong path + invented capability)** → the verdict lands in the **shared
  `kata-diagnose/RUBRIC.md`** (both tiers inherit); it is acknowledged as a **NEW** capability formalized from
  the RUBRIC's existing Phase-6 "if architectural → kata-improve" seam (not "already does this").
- **B4 (`fixAttempts` can't persist via `update_task`; L4 contradictory)** → operator chose **(b)**: the counter
  is the orchestrator's **own in-context fix-loop bookkeeping** (it counts its own iterations), with the existing
  `DECISION` board lines as the durable recount trail — **not** a `state.json` field, **no new board TYPE.** L4
  now honest. *(Re-confirm H1: an earlier draft wrongly claimed the board logs a "NEEDS_WORK→fix" event — it
  does not; corrected to orchestrator-in-context + DECISION-line audit trail.)*
- **M1 (per-task counter evadable by A↔B oscillation)** → added the **run-level ceiling** + count
  confirmation-pass regressions (L2).
- **M2/M3/M4** → N=2 marked provisional + human-valve-on-verdict-not-N (L3); `kind` stays `human-required`, no
  enum change (L6); confirmation-pass ↔ red-team interaction locked (L1).

## Remaining open (build-eval + future calibration)
- **N=2 + the run-level ceiling are provisional** — the first multi-fix dogfood that exercises them is the
  calibration data; revisit both numbers then.
- **The `kata-diagnose` fix-vs-plan verdict is a NEW capability** — its acceptance test must **prove it
  actually returns the verdict** (the D98/L12 *reproduce-don't-trust* rule applies), not merely document it.
