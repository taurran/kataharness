---
title: "Fix-loop hardening — material re-verification + thrash→re-plan budget"
status: FROZEN (DESIGN) — pending freeze-gate adversarial review
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

### Rule 1 — Material re-verification (blast-radius-scoped)
After a targeted fix:
- **Always re-run the cheap deterministic gate** (pytest / validator / lint / scan) — fast, idempotent, no reason to skip.
- **Re-run a *fresh-context* judge** (`kata-evaluate` / `kata-review`) **only if the fix is *material* to its
  verdict** — i.e. the fix's **footprint intersects that judge's evidence basis** (the files/concerns its
  findings rested on). A docs-only fix to a red-team nit does not require re-running the full `kata-evaluate`;
  a fix that changes executable logic does. ("Material" = footprint intersection, computed with the existing
  blast-radius reasoning — not evaluator vibes.)
- **After the *final* batch of fixes, run exactly ONE full-stack confirmation pass** to catch cross-fix
  interaction (fixing X broke Y). **One** — never per-fix.

### Rule 2 — Thrash budget → escalate as a deliberate re-plan
- Track **`fixAttempts` per task/area** in the **drift ledger** (`state.json`, orchestrator-owned — it already
  maintains the ledger; this adds one counter).
- When the **same area** fails → fixes → fails for **N cycles** (default **N=2**, i.e. the **3rd** failure on
  one area), **STOP looping on it.**
- Route it to **`kata-diagnose`** for a systematic root-cause pass: *is this a fix problem or a **plan**
  problem?*
- If the frozen plan has **no clean fix**, escalate it as a **re-plan candidate** through the **existing
  escalation valve** — a **deliberate, human-gated re-plan event, supersede-not-rewrite**, never a silent
  re-plan. This is the missing **bridge** between "fix loop exhausted" and "deliberate re-plan" (spine #1/#2:
  *re-planning is an event, not a habit*).

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
- **L1 — Material re-verification.** Always re-run the cheap gate; re-run a fresh-context judge **only** if the
  fix's footprint intersects its evidence basis; **one** bounded full-stack confirmation pass after the final
  fix batch. Computed with existing blast-radius reasoning.
- **L2 — Thrash budget.** Per-task `fixAttempts` counter in the drift ledger (`state.json`); **default N=2**
  (escalate on the 3rd failure of one area). The default is conservative and **documented**; a `kata.config`
  override is a future option, **not** in this spec.
- **L3 — Thrash → deliberate re-plan event.** Route via `kata-diagnose` → the existing escalation valve →
  **human-gated** re-plan, **supersede-not-rewrite**. **Never a silent re-plan.** Spine #1/#2 preserved.
- **L4 — No new committed Python.** The counter lives in the **existing** drift ledger the orchestrator
  maintains (`state.json` via `kata_board.update_task` / the ledger). **Non-code-bearing** (`.md` + a state
  field). (`prefer-in-context-over-new-python`.)
- **L5 — Batch-fix + staged-cascade (made explicit).** Within one judge's findings: collect **all** → fix in
  **one batch** → re-verify that judge (never fix-one-rerun-one). The cheap→expensive gate *ordering* (a red
  test never reaches a fresh-context judge) is reaffirmed.
- **L6 — Additive between the gates.** This changes **neither** the default-FAIL gate, the no-self-cert rule,
  **nor** the escalation contract — it **bounds and scopes** the loop *between* them. The conformance floor is
  untouched (D22).

## Open questions for the freeze-gate to attack
- **Is N=2 right?** Too trigger-happy → premature re-plans on legitimately-hard-but-fixable areas; too high →
  still churns. What's the evidence for the default?
- **"Material" definability.** Is "footprint intersects the judge's evidence basis" crisp enough to act on, or
  subjective mush? What's the fallback when blast-radius is unknown (re-run, fail-safe)?
- **"Area" granularity.** Per-task? per-file? per-finding-cluster? — what does `fixAttempts` key on, and can a
  fix to area A that breaks area B evade the counter?
- **Async-escalation interaction.** Does a thrash-escalation **park the sub-tree** like other escalations
  (frontier keeps draining), or hard-stop? (Should match the existing async-escalation contract.)
- **Does the confirmation pass (L1) re-trigger the standing red-team (D98)?** Or only the cheap gate?
