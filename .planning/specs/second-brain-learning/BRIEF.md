---
title: "Second-brain learning (Recall · Reason) — pre-grill BRIEF"
status: BRIEF (pre-grill, NOT frozen)
date: 2026-06-24
spec: second-brain-learning
supersedes-framing: protocol/engram.md ("engram"/"CONSULT" — rename pending, see D99)
decision: D99
tags:
  - kata/cognition
  - learning
  - second-brain
  - recall
  - reason
  - c-arc
---

# Second-brain learning — Recall · Reason (the C-arc)

> **Pre-grill brief, not frozen.** Captures the operator strategy session (2026-06-24) that chose the
> learning approach, corrected the model, and locked the vocabulary. Grill → freeze → build later; the
> immediate buildable work is the **A-hardening (thrash guard)**, not this. This whole arc gets a
> freeze-gate adversarial review before any build.

## Why (the problem)
KataHarness today **cold-starts every run** — it never learns between loops (the β LEARN feed is emit-only,
D74; CONSULT is gated off, D9/D56). That leaves Hermes's *compounding* advantage on the table. The goal:
capture in-loop learning **without** surrendering the spine (reproducibility, default-FAIL, no-self-cert,
plan-doesn't-drift). The strategy assessment (D99, adversarially validated) chose **C — a gated-learning
hybrid** as the destination, with **A (controlled)** as the immediate next move and **B (Hermes-fluid)** ruled
out as a trap (it deletes reproducibility + poisons memory ungated).

## The model (supersedes "engram" — which conflated three things into one word)
| Term | Role | Lives in |
|---|---|---|
| **Second brain** | the data — BYO, agnostic; raw knowledge + the user's decision history + synthesized decision-pattern pages (accrete over time via the β feed) | the user's vault (PokeVault, the work repo, …) |
| **Recall** *(the Librarian)* | per-vault **fetcher/adapter** — knows *its* structure, serves the standard contract, **never decides** | **with each second brain** (downstream repos build their own) |
| **Reason** *(the Advisor, `kata-reason`)* | KataHarness's **decider** — asks Recall to surface material, fuses it with research (RS + the grounding gate), returns a **calibrated recommendation that mirrors the user**; advisory, not authoritative | **KataHarness core** |

Tagline: **Recall what you know · Reason what you'd do.** *Recall serves; Reason decides* — decision logic
stays in KataHarness (consistent across every second brain); vault-navigation stays per-vault (the adapter
pattern, spine #3 — Recall **is** the D30 clean-room backend binding, finally named). You point KataHarness at
the **Recall**, never the raw folder.

**What KataHarness ships:** the **Recall contract** (the interface) + **`kata-reason`** + the readiness exam +
the inline triage. **The Librarians are downstream** — PokeVault / the work repo implement their own Recall
against the contract. This keeps the core lean.

## C's unlock — four tumblers (no hand-waved "maturity")
1. **A pointed-at second brain + a Recall implementing the contract** (config; depends on install-portability's
   workspace-binding layer). No backend → no C.
2. **Readiness exam** — `kata-reason` must predict the user's **held-out** past decisions (each presented *with
   its research context*) at **calibrated confidence** — high-confidence-wrong fails hard (catches the
   poisoned/overconfident fingerprint). Fresh-context, no-write, **no-self-cert** (Reason can't grade itself);
   **standing + re-runnable + cached** (project-start / on-request / corpus-growth trigger — **not** every loop).
   Pass → C unlocks; fail → **graceful fallback to A**. This is the *measurable* definition of "mature."
3. **Inline triage red-team** per Reason decision — a structured, **fail-toward-escalation** in-context check
   that may auto-clear **only** low-stakes ∧ high-confidence calls; anything it flags, or any high-stakes class,
   **escalates** to a fresh-context `kata-review` and/or the human. The cheap stage of the staged cascade applied
   to judgment; the authoritative gate stays fresh-context (preserves no-self-cert).
4. **Outcome benchmark** (`kata-loop-benchmark`) — proves **C-on beats C-off** on a fixed reference task; sets
   the unlock *threshold*. Promoted from far-future garnish to the **keystone** that makes C's gate falsifiable.

Autonomy opens **progressively, risk-tiered** (the D65 dial): low-stakes (the thrash-seam) first; **scope /
drift / feature decisions last, recommend-before-auto,** at the strictest exam bar.

## The C/B invariant (LOCKED-class — getting it wrong IS sliding into B)
Every Reason decision stays a **deliberate, frozen, gated, thrash-bounded, audited event toward a
human-frozen goal.** **Protect the process, not the decider.** Reason may re-plan *toward* the frozen
INTENT/goal; it may **never expand the goal** (that re-freezes with the human); `kata-defer` still parks
nice-to-haves. **The one-line test:** *did the decision produce a discrete frozen artifact the gates then
judged — or did the plan just quietly become something else?* First = C; second = B.

## Open questions for the grill (not yet decided)
- **The Recall contract shape** — the seam between 3 repos; too thin starves Reason, too vault-specific makes
  Librarians painful. *This is the load-bearing design.* What does Reason ask for; in what shape does Recall
  answer (decision-history records? distilled patterns? both)?
- **Who synthesizes the decision-pattern pages** — KataHarness's β LEARN-emit (for cross-vault consistency)
  writing *through* Recall, vs. each Librarian synthesizing its own? (Lean: KataHarness synthesizes, Recall
  persists/serves — keeps consistency.)
- **The calibration metric + threshold** — exact scoring of "calibrated decision-mirroring"; what score, on
  which decision-classes, earns which autonomy rung (ties to the benchmark).
- **"Mature enough" corpus floor** — minimum decision-history to even run the exam (can't hold-out a near-empty
  vault).
- **Thrash budget N** + what "material" means for the material-re-verify rule (shared with the A-hardening).

## Scope split
- **KataHarness builds:** Recall contract · `kata-reason` (Advisor) · the readiness exam · the inline triage ·
  the β LEARN-emit→synthesis path · the outcome benchmark.
- **Downstream (other repos):** PokeVault Recall · the work-repo Recall (each against the contract).
- **Depends on:** install-portability (the BYO-backend pointer / workspace-binding config) — Phase 5 foundation.

## Out of scope
- **Second-brain *security*** (encrypting/access-controlling the user's vault) — the user's responsibility.
  KataHarness-as-egress-vector re-enters only at public-release/multi-user, localized to **each Librarian's
  egress boundary** (per-vault redaction in its own repo), never the core.
- Wholesale Hermes-fluid learning (B) — ruled out (D99).
- The full **engram→second-brain rename** of existing surfaces (`protocol/engram.md`, E1–E23, D9/D56/D74/D65,
  CONTEXT) — a **pending migration** to run as its own deliberate contract pass, not part of this BRIEF.

## Sequencing
**A-hardening (thrash guard) now** → install-portability (BYO-backend pointer) + `kata-loop-benchmark`
(defines the unlock) + the β-feed maturing the corpus → grill/freeze this BRIEF → build `kata-reason` + the
Recall contract → Librarians downstream → open the autonomy dial only as far as the benchmark earns.
