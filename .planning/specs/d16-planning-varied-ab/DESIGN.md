---
date: 2026-06-18
spec: d16-planning-varied-ab
status: FROZEN v2 — re-registered post-pilot (2026-06-18); changes are deliberate re-freezes
source-ledger: ./GRILL-LEDGER.md (D16-GB1–6)
tags: [design, frozen, d16, ab-test, validation-gate, pre-registered]
---

# D16 — planning-varied A/B — FROZEN DESIGN (pre-registered protocol)

> **⛔ RETIRED as an RCT (D70, 2026-06-18).** Two counted attempts (easy + hardened `wordfreq`) showed the
> autonomous deterministic-gate A/B **cannot isolate the grill's value** (both methods 4/4→10/10 gate passes;
> the grill's human-interrogation engine is off without a human — L11). **Kept as the autonomous-reliability
> demonstration**, not a benchmark. v0.1 validation is re-scoped to *Priming-and-Grill* (D71/D72): grill is an
> optional human certainty layer over the priming prompt; autonomous reliability is the floor. The protocol
> below is the executed-and-superseded record. **Do not run the remaining arms.**

The v0.1 validation gate. **Pre-registered**: this protocol + the verdict rule are fixed *before* any run, so
the result can't be p-hacked. Supersedes TEST-PLAN v1. Carried principles (D14/D57/D59): model constant
(Sonnet), fresh context per run, honest GSD baseline, both arms get `kata-review` (L10).

**v2 re-registration (post-pilot, see PILOT-NOTES.md):** the 2026-06-18 pilot (project 1, 1 pair) ran cleanly
but **tied** — the corpus was too easy to discriminate, and self-judged `first_pass_green` proved unmeasurable.
Instrument-driven fixes (on a *tied* result, so not p-hacking): **(i)** corpus hardened to be *planning*-hard
(interacting rules, order-of-operations, subtle edges — still small/one-shottable, D57); **(ii)** metrics fixed
(§3) — objective `gate_pass` + `fix_iterations` replace `first_pass_green`; **(iii)** verdict rule restated (§4).
Pilot data retained as history. No counted run had occurred, so re-registration is clean.

## 1. Hypothesis
The KataHarness planning chain (`kata-grill`→`kata-design-doc`→`kata-plan`) produces plans that **one-shot with
fewer downstream failures** (ambiguity-driven drift, escalations, interventions, re-plans) than a GSD baseline
plan — on the same small greenfield projects. (L10: execution was tied → the lift, if real, lives in planning.)

## 2. Design (one independent variable)
- **IV:** planning method. **Arm A** = `kata-grill`→`kata-design-doc`→`kata-plan`. **Arm B** = local GSD
  spec→plan (`~/.claude/get-shit-done`), configured comparably — honest, no strawman (D14).
- **Held constant:** model = **Sonnet** (D14/D59); execution machinery (`kata-orchestrate`/`worktree`/`tdd`);
  fresh context per run; identical project spec + acceptance gate; **both arms then run `kata-review`** (L10).
- **Corpus:** 3 small greenfield projects — **CLI tool · small REST API · parser/transformer** — single-
  language, ≈3–8 files, each with an automated pass/fail acceptance gate (own test suite + lint), in a
  dedicated test dir outside this repo.
- **N:** 3 paired runs per arm per project → **18 runs** (pre-registered; no peek-and-extend).
- **Isolation:** loop-cognition **β may run ∥ to harvest the decision corpus but MUST NOT feed either arm**
  (D68 — LEARN-only, zero CONSULT).

## 3. Metrics (v2 — per run; plan-quality downstream, not execution parity)
- **Objective (experimenter-measured, PRIMARY):** `gate_pass` (held-out `pytest` ∧ `ruff` on the delivered
  build, y/n) · `gate_fail_count`.
- **Self-reported (precise, identical defs both arms, SECONDARY):** `drift_events` (deviations from the frozen
  **functional** plan — a lint auto-fix is NOT drift) · `replans` · `escalations` · `interventions` ·
  `eval_defects` · `fix_iterations` (failing-test-or-lint→fix cycles to first all-green).
- **Covariates (not in the verdict):** tokens, tool_uses, wall_min, files, self_tests.
(Full definitions: `corpus/METRIC-SHEET.md`.)

## 4. Verdict rule (PRE-REGISTERED v2 — fixed before any counted run)
- **Primary:** per project per arm, **planning-cost = Σ(drift_events + replans + interventions +
  fix_iterations)** over the 3 runs; plus each arm's `gate_pass` rate.
- **Tiebreak:** a fresh-context `kata-review`/LLM-judge plan-quality rating, **arm-blind** where feasible.
- **Decision:** *the grill differentiates IFF Arm A has **lower planning-cost on ≥2/3 projects** AND Arm A's
  overall `gate_pass` rate ≥ Arm B's.*
- **On tie/worse:** the grill is **not yet proven** → iterate the grill via the kata (do **not** ship v0.1 on
  an unproven differentiator — L8). A real fail condition, not a formality.

## 5. Acceptance criteria (of the experiment itself)
- **A1** All 18 runs executed under the frozen protocol; per-run metric sheet recorded.
- **A2** Verdict computed strictly by §4 (no post-hoc metric changes).
- **A3** Result written to **`LESSONS-LEARNED.md` (L11)** + a verdict note; adversarial **`kata-review`
  (D15)** over the experiment + conclusion returns SHIP.
- **A4** If PASS → v0.1 validation gate cleared (unblocks the post-D16 build per D68). If FAIL → a grill-
  iteration task is opened; v0.1 stays gated.

## 6. Scope guard
Docs + measurement + test-project scaffolding only — **no new harness skills**. Runs on Sonnet. Both arms get
equal human availability. The test projects are throwaway (dedicated dir), not part of the repo.

---
**FROZEN.** Next: scaffold the 3 test projects + their acceptance gates, then run the 18 arms. Changes to this
protocol are deliberate re-freezes (and, post-hoc, invalidate pre-registration).
