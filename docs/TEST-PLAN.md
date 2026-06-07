# TEST-PLAN.md — KataHarness v0.1 validation (the A/B test)

> How we prove KataHarness *works* — distinct from *dogfooding* (building it with itself, which is a
> friction signal, not a correctness test). The test measures the core claim: **does the harness one-shot
> a complex task better than our current best process?**

## Target task
**CryptoPortfolioPlanner Phase 3 — the G_macro macro/sentiment gate** (MACRO-01/02). Chosen because it is
genuinely complex (core-algorithm surgery in `js/core.js` + sleeve classification + seed schema + UI +
tests), has an **independent, pre-existing pass/fail gate** the harness can't grade for itself
(`node --test js/*.test.cjs` green + Snyk clean + `cpp-evaluation` PASS), is well-specified (THESIS §1b/§7
Step 1.5; research done), and contains a real **design-decision branch** (which sleeves are "crypto/high-beta"
vs "safe") that a sloppy process drifts on — exercising the plan-guardian/no-drift spine.

## Experimental design
- **Fork point:** both arms branch from CPP tag **`cpp-phase2-baseline`** (frozen, 220 tests green).
- **Arm A — KataHarness:** build Phase 3 via the KataHarness loop (grill → frozen design+plan →
  plan-guardian execution → default-FAIL eval → handoff). Branch `test/phase3-kata`.
- **Arm B — Baseline:** build Phase 3 via our **current best process** (GSD plan → plan-checker →
  worktree executor → cpp-evaluation — exactly how Phase 2 was built). Branch `test/phase3-baseline`.
  *(Baseline is the real process, NOT a naive single-prompt agent — no strawman.)*
- **Hold the model CONSTANT:** **Sonnet 4.6 in both arms.** (If the harness arm uses Opus-for-plan for
  realism, add a Sonnet/Sonnet decomposition run to separate harness-structure lift from model lift.)
- **Fresh context per arm:** each arm runs in its own clean session reading only its branch's docs — so
  neither arm is contaminated by the design session. (Required for a fair A/B, not just hygiene.)
- **Same frozen Phase-3 design+plan fed to both** — the independent variable is the *process*, not the spec.

## Metrics (objective)
| Metric | Pass condition |
|---|---|
| One-shot success | reaches the green gate **without re-planning** |
| Plan drift | **0** unauthorized deviations (changes must be escalations) — esp. the sleeve-classification branch |
| Interventions | count of human touches during execution (fewer = better) |
| Gate integrity | fresh-context evaluator catches real issues; **no false PASS** |
| Handoff recovery | force a self-handoff/compaction mid-run → resume with **zero loss** |
| Hygiene | deterministic build; no state clobber under concurrency |

**v0.1 verdict:** KataHarness "passes" if Arm A reaches green with **0 drift** and **fewer interventions**
than Arm B on the same task. If it merely ties the baseline, the harness isn't earning its complexity yet.

## Sequencing (lean — validate before automating)
1. **Wizard-of-Oz first (recommended):** run the loop *by hand* (orchestrator executes `DESIGN.md` manually)
   on Arm A vs the Arm B baseline. If the *method* shows lift, then:
2. **Build v0.1 skills** (Opus 4.8 — see DECISIONS D13) to automate the proven loop.
3. **Re-run the automated A/B** for the real result.

## Model per stage (DECISIONS D13)
- **Building KataHarness skills → Opus 4.8** (best foot forward).
- **CPP Phase-3 test arms → Sonnet 4.6** (both arms; retry later if flubbed).
- I pin subagent models on spawn; the main session model is set by the operator via `/model`.
