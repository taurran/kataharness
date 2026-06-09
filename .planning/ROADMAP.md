# ROADMAP — KataHarness

Improvement-Kata cadence: each milestone ends with a retro into `LESSONS-LEARNED.md` → `kata-improve`.

- [ ] **v0.1 — Claude-only one-shot core.** Prove the loop one-shots a complex task from a frozen
  design+plan. Skills: `kata-grill`, `kata-context`, `kata-design-doc`, `kata-plan`, `kata-orchestrate`
  (plan-guardian), `kata-board`, `kata-worktree`, `kata-tdd`, `kata-evaluate`, `kata-handoff`.
  Frontmatter/versioning/naming standard applied. **Dogfood: KataHarness builds itself**, then run it
  on CryptoPortfolioPlanner. No multi-tool adapters yet.
  - **RELEASE CHECKLIST — on v0.1 ship:** flip the versioning policy from **hold-at-`0.1.0`** to
    **bump-on-modify** (STANDARDS §3). Until then every skill stays `0.1.0`; after, every skill modification
    bumps semver. Easy to forget — this is the trigger point.
- [~] **v0.2 — Self-handoff + concurrency.** PULLED FORWARD into the v0.1 build: `kata-selfhandoff`,
  `kata-diagnose`, `kata-review`, `kata-improve` (+ meta `kata-write-skill`) all built. **Remaining for v0.2:**
  `kata-tasklist` (file-locked self-claim) + the multi-agent self-claim model — deferred until workers
  self-select (today the orchestrator assigns, so it's redundant with state.json + the plan DAG).
- [ ] **v0.3 — Adapters: Codex + Kiro.** `adapters/codex`, `adapters/kiro`; AGENTS.md normalization
  across tools; skill-format mapping; portability tests.
- [ ] **v0.4 — ACP/Quick + cognition.** `adapters/acp-quick` (orchestrator-in-desktop via ACP);
  `cognition/kata-engram` tie-in (gated on a mature kiban/kagami engram).

### Modes & Cost-Tiering track (design DONE 2026-06-07 — `docs/MODES-DESIGN.md`; major new capability)
Operating modes that trade effort/thoroughness/cost, all one-shot; consistency-first. Sequence:
- [~] **Spec A — Mode/tier/module/config/bootstrap system.** **A1 (foundations) DONE+merged** (validator +
  cost-weight/license/namespaced-tags frontmatter + generated README index + schemas + TAXONOMY). **A2 (tier
  families) DONE+merged** (grill/review/plan → 3 tiers, diagnose → light/full; RUBRIC-per-family; depth-hint
  for design-doc/tdd; validator tier rules; reviewed HOLD→SHIP; **D33** structural-invariants-never-tiered).
  **A3 DONE + merged 2026-06-08 (merge `27ca76c`, reviewed SHIP); A4 remains.**
  - **A3 — bootstrap brain + greenfield wiring + version-up-aware/configurable.** ✅ **DONE+merged** (GB1–GB13
    → D34–D46; 24 skills; validator green). New skills: **`kata-bootstrap`** (full configurator: **run-shape router** —
    individual / batch=bakeoff / version-up / advanced, presets *on top of* the mode axis GB1; the D24c ladder;
    cost preview; run-shape-relevant interview only GB13; write `kata.config`) + **`kata-readiness`** (light,
    bootstrap-invoked: harness-health + target-readiness + re-entrant config detection, GB11). Wire
    **`kata-orchestrate`** to read config + resolve family→tier (fallback Standard, D25) **with a fail-closed
    load-guard** (GB12 — not a bootstrap validation phase). Bootstrap re-entrant (cold-start vs reconfigure —
    one skill, GB5) and version-up-aware day one (writes a correct version-up config routing to A4). Fold grill
    efficiency refactor in.
  - **A4 — version-up execution bundle (absorbs the old standalone Spec C).** ✅ **DONE+merged 2026-06-08**
    (merge `de4b0ee`, reviewed SHIP; 25 skills; D47–D56). Scope: **`kata-graph`** (new skill — tree-sitter-floor, feature-agnostic
    cached `kata.graph.json` contract, ~3k-token feature-seeded digest, pluggable backend; `protocol/graph.md`)
    + **version-up wiring** (grill Phase 0 ingest, footprint-scoped disjoint ownership, full-suite-green
    regression contract; no new evaluator) + **`kata-orchestrate` frontier/async-escalation supersession**
    (rolling DAG-frontier dispatch, async park/drain/hard-wait; structured escalation payload →
    `protocol/escalation.md`). Grill converged (GB1…GB10 + HOLD#1/#2/#3; coherence PASSED); decisions D47–D56.
    Composes with bakeoff (D37/D43).
- [ ] **Spec B — Bake-off.** N variants → judge → pick → refine up (AgentHub / worktrees). Composes with
  version-up (a baked-off version-up = N candidate feature-impls, judged on adds-feature ∧ no-regression).
- [ ] **`kata-understand` — post-processing comprehension map (desired state).** Helps the user understand a
  **newly-built** codebase (Understand-Anything nod, GB7). Distinct from `kata-report` (build-log synthesis).
  Own later spec/module, post-v0.1.
- [ ] **`design` module (own spec).** UI/UX, 2D/3D assets, slides, mobile, image-FM — Claude's design
  blind-spot; built to slot into Advanced; inherently tiered.

**Pre-v0.1 (now):** finish `research/NOTES.md` deep-eval of mattpocock + BMAD + GSD (what to adopt);
then dogfood `kata-grill` to spec v0.1's first skills.

## Progress
| Milestone | Status |
|---|---|
| v0.1 core | 11 skills built; adversarially reviewed + fixed; execution half field-proven (A/B tied, L10) |
| v0.2 (pulled fwd) | diagnose/selfhandoff/improve/write-skill built; tasklist deferred (needs worker self-select) |
| v0.3–v0.4 | Not started (adapters; ACP/Quick + kata-engram) |
