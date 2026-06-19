---
date: 2026-06-18
spec: d16-planning-varied-ab
status: FROZEN — pre-registered protocol (changes are deliberate re-freezes)
source-ledger: ./GRILL-LEDGER.md (D16-GB1–6)
tags: [design, frozen, d16, ab-test, validation-gate, pre-registered]
---

# D16 — planning-varied A/B — FROZEN DESIGN (pre-registered protocol)

The v0.1 validation gate. **Pre-registered**: this protocol + the verdict rule are fixed *before* any run, so
the result can't be p-hacked. Supersedes TEST-PLAN v1. Carried principles (D14/D57/D59): model constant
(Sonnet), fresh context per run, honest GSD baseline, both arms get `kata-review` (L10).

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

## 3. Metrics (per run; plan-quality downstream, not execution parity)
(a) ambiguity-driven **drift events** · (b) **escalations** · (c) **human interventions** · (d) **re-plans** ·
(e) **first-pass acceptance-gate green** (y/n) · (f) **defects caught at `kata-evaluate`** · (g) **rework
commits**. Token/wall cost logged as a **covariate**, not part of the verdict.

## 4. Verdict rule (PRE-REGISTERED — fixed before running)
- **Primary:** objective counts of (a)–(g) per run, aggregated per project.
- **Tiebreak:** a fresh-context `kata-review`/LLM-judge plan-quality rating, **arm-blind** where feasible.
- **Decision:** *the grill differentiates IFF Arm A shows materially fewer (drift + interventions + re-plans)
  on a **majority of projects (≥2/3)** AND Arm A's first-pass-green rate ≥ Arm B's.*
- **On tie/worse:** the grill is **not yet proven** → iterate the grill via the kata (do **not** ship v0.1 on
  an unproven differentiator — L8). This is a real fail condition, not a formality.

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
