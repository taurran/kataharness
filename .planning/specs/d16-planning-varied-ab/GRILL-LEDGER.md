# D16 — planning-varied A/B — Grill Decision Ledger

> **The v0.1 validation gate** (ROADMAP-LOCKED; D68 confirmed D16-first). Prove the **grill differentiates**:
> Arm A plans via `kata-grill`→`kata-design-doc`→`kata-plan`; Arm B via a GSD baseline; both then execute +
> `kata-review` on the **same small greenfield test projects**. Supersedes TEST-PLAN v1. Carried principles
> (D14/D57/D59): **model constant across arms (Sonnet) · fresh context per run · honest GSD baseline (no
> strawman) · both arms get `kata-review`** (the L10 loop gap). L9/L10 finding: execution **tied** → any lift
> must show in **planning quality**, so we measure *downstream plan-quality effects*, not execution parity.
> **Status: RESOLVED 2026-06-18** (user: fine spending tokens on execution, keep the grill surgical → all
> recs adopted; stacks + N pinned below). Converged in one pass.

## D16-GB1 — Test corpus: count · stack · complexity bar · per-project gate **(REC)**
**3 small greenfield projects**, distinct domains, single-language, each **one-shottable** (≈3–8 files, a crisp
spec, and an **automated pass/fail acceptance gate** = its own test suite + lint). Live in a dedicated test dir
outside the repo. **Pinned stacks (default, swap if a domain matters): (1) a CLI tool · (2) a small REST API ·
(3) a parser/transformer** — single-language each, distinct shapes. *Rejected:* one big task (D57 — too few
measurements); >5 projects (token cost). **RESOLVED 2026-06-18.**

## D16-GB2 — N runs per arm per project **(REC)**
**N=3 paired runs/arm/project** (3 projects × 2 arms × 3 = 18 runs). Pre-register N (no peek-and-extend).
Budget floor N=2 if tokens tight. *Rejected:* N=1 (noise = signal).

## D16-GB3 — The single independent variable + held-constant set **(REC, confirm)**
IV = **the planning method only.** Arm A = `kata-grill`→`design-doc`→`plan`; Arm B = local GSD spec→plan
(`~/.claude/get-shit-done`). Held constant: **model = Sonnet** (D14/D59), execution machinery
(`kata-orchestrate`/`worktree`/`tdd`), fresh context per run, identical project spec + acceptance gate, **both
arms get `kata-review`** (L10).

## D16-GB4 — Metrics: plan-quality downstream, not execution parity **(REC)**
Pre-registered fixed set: **(a) ambiguity-driven drift events · (b) escalations · (c) human interventions ·
(d) re-plans · (e) first-pass acceptance-gate green (y/n) · (f) defects caught at `kata-evaluate` · (g) rework
commits.** These are exactly the L9 zeros for Arm A — measure whether Arm B incurs more. Token/wall-cost logged
as a **covariate, not the verdict.** *Rejected:* execution-parity metrics (L10 already tied).

## D16-GB5 — Judge protocol + pre-registered verdict rule **(REC)**
**Objective metrics primary** (count GB4 events per run) + a **fresh-context `kata-review`/LLM-judge as a
qualitative plan-quality tiebreak** (arm-blind where feasible). Pre-register the rule **before** running:
*"grill differentiates IFF Arm A shows materially fewer drift+intervention+re-plan events on a **majority of
projects** AND ≥ Arm B first-pass-green."* Tie/worse ⇒ grill **not yet proven** → iterate the grill (kata, not
ship). *Rejected:* post-hoc metric selection (p-hacking).

## D16-GB6 — GSD baseline fairness + scope guard **(REC, confirm)**
Arm B = the **actual local GSD** flow configured comparably (real spec→plan, **no strawman** — D14 surviving
principle); equal human availability both arms. Scope guard: this gate is **docs + measurement, not new
skills**; runs on Sonnet; loop-cognition **β may run ∥ to harvest the decision corpus but must NOT feed either
arm** (D68 isolation).

---

## Convergence
On one-pass confirm of GB1–GB6 → freeze a **short DESIGN** (the experimental protocol + pre-registered verdict
rule) → run the 18 arms → record **L11** + the verdict → adversarial **REVIEW** (D15). Per RUBRIC, a
fresh-context check precedes the DESIGN freeze.

### Status board (2026-06-18)
| Branch | Verdict |
|---|---|
| D16-GB1 corpus | RESOLVED — 3 small greenfield (CLI · REST API · parser), automated gate each |
| D16-GB2 N | RESOLVED — N=3/arm/project (18 runs); pre-registered |
| D16-GB3 IV/constants | RESOLVED — IV=planning method; Sonnet + machinery + kata-review held constant |
| D16-GB4 metrics | RESOLVED — drift/escalation/intervention/re-plan/first-pass-green/defects/rework; cost=covariate |
| D16-GB5 judge+rule | RESOLVED — objective primary + blind kata-review tiebreak; pre-registered majority rule |
| D16-GB6 baseline+scope | RESOLVED — honest GSD; docs-only; β must not feed arms |
