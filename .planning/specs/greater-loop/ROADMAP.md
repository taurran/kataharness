---
date: 2026-06-20
spec: greater-loop
status: DRAFT — master build-order across the Greater Loop + foundations + prior briefs. Freezes with DESIGN.md.
anchor: Greater Loop working END-TO-END on SELF before going external
tags: [roadmap, master-order, greater-loop, sequencing]
---

# Master Build-Order — the Greater Loop (and everything around it)

One ordered sequence aligning the Greater Loop modules, the foundations they need, and the prior briefs.
**Each phase is built as a REAL orchestrated run** (disjoint slices → concurrent worker subagents in worktrees →
integration gate → fresh-context evaluator → human version-select), per the no-half-assing rule. Phases gate
into the next; foundations parallelize.

## Phase 0 — FOUNDATIONS (build first; F1 ∥ F2 can run in parallel)
- **F1 — Wire the eval artifacts into the live gate.** Make `kata-evaluate`/the gate **emit** `RESULT.json`
  (`run_result`), compute the **footprint manifest** (`footprint`) vs the plan, and record the **mutation proof**
  (`mutation_check`). Closes the dogfood-2 residual. **Folds in the testing rigor** (DESIGN §7 — the
  testing-model substitute). *Deps: none (libs already built).* → closeout's data layer.
- **F2 — Graph runtime operational (minimal).** Install tree-sitter + a generator → `kata.graph.json` per
  `protocol/graph.md` (Python first). Makes `kata-graph` actually run; backs `kata-understand` + version-up
  footprint. Defer the Graphify oracle. *Deps: none.*

## Phase 1 — INITIATION module  *(deps: none hard; pairs with F-phase)*
- **M1 — `modules/initiation/` (own `AGENTS.md`) + `kata-initiate`.** Front door: ingest intent → classify
  kind → capture `INTENT.md` (goal/fixes/features/modules/changeSummary). **Interactive target/platform/vault
  configuration** (the install-portability *config layer*, GL-R3c). Grill-to-ready **or** user-says-execute →
  freeze `INTENT.md`. Composes readiness/grill/bootstrap/context. *Deps: none (config layer only; installer
  mechanics deferred to Phase 5).*

## Phase 2 — CLOSEOUT module  *(deps: F1, F2)*
- **M2 — `modules/closeout/` (own `AGENTS.md`) + `kata-closeout` + `kata-understand`.** Track the F1 artifacts →
  `kata-report` → **offer `kata-understand`** (graph-backed via F2, light fallback) → human gate (satisfied? /
  commit·push·merge? / run-again·new?). *Deps: F1 (data), F2 (graph).*

## Phase 3 — CONDUCTOR + loop-back  *(deps: M1, M2)*
- **M3 — `kata-loop` (thin conductor).** Sequence initiation → harness → closeout; own the **loop-back with
  context carry**. Optional (BC: absent ⇒ today's direct run). *Deps: M1, M2 (the modules it sequences).*

## Phase 4 — DOGFOOD: the Greater Loop end-to-end on SELF  *(deps: M3)*
- Run a full greater-loop cycle on KataHarness itself: `kata-initiate` (capture a real version-up INTENT) →
  harness (orchestrated) → `kata-closeout` (report + understand map + human gate + version-select). This is the
  **self-end-to-end anchor** proving the whole wrapped loop. Surfaces the next round of findings.

## Phase 5 — EXTERNAL reach  *(deps: Phase 4 green)*
- **install-portability (installer mechanics).** The modular per-platform installers + workspace binding beyond
  the initiation config layer (PokeVault link / bring-your-own-vault scaffold / aim-each-folder; MindBridge
  brings its own). Unlocks running on external targets / your vault. *(Config layer already in M1.)*
- **multi-model-orchestration.** Host-located orchestrator (MindBridge→Quick/ACP · Kiro/Claude→there) +
  per-component model/tool routing — including the **latent testing-model option** (route eval to another model
  if a real need shows). *Deps: install-portability.*

## Retired / folded
- **testing-model brief → folded into F1** (DESIGN §7, pending ratification). Not a separate build; the latent
  "route eval to another model" lives in Phase 5 multi-model.
- **Graphify oracle (full)** → deferred upgrade after F2's minimal runtime.

## Dependency graph (text)
```
F1 ─┐
F2 ─┼─▶ M2 ─┐
M1 ─┴───────┼─▶ M3 ─▶ Phase4 (self dogfood) ─▶ Phase5 (install → multi-model)
            │
  (M1 independent of F1/F2; M2 needs both F's; M3 needs M1+M2)
```

## Execution UX (decided 2026-06-20)
- Orchestrated runs dispatch workers **foreground-parallel** (Claude Code's native live agent panel) — chosen
  over background for visibility.
- A **host-agnostic KataHarness live dashboard** (artistic ASCII + animated bars on board+state) = `[[subagent-dashboard]]`
  BRIEF — **build-later**, pairs with multi-model (Phase 5) or pulled earlier as a fun standalone. Orthogonal;
  never blocks the loop.

## Notes
- Every NEW skill stays `0.1.0` (Policy A) until v0.1; suite tags continue `v0.1.0-alpha.N` per milestone.
- Phases 0–3 each end with a fresh-context `kata-review` SHIP + Snyk before merge; Phase 4 is the integration
  proof. Update this order if Phase 4 findings demand it (supersede-never-rewrite).
