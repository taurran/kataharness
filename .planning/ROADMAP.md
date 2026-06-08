# ROADMAP — KataHarness

Improvement-Kata cadence: each milestone ends with a retro into `LESSONS-LEARNED.md` → `kata-improve`.

- [ ] **v0.1 — Claude-only one-shot core.** Prove the loop one-shots a complex task from a frozen
  design+plan. Skills: `kata-grill`, `kata-context`, `kata-design-doc`, `kata-plan`, `kata-orchestrate`
  (plan-guardian), `kata-board`, `kata-worktree`, `kata-tdd`, `kata-evaluate`, `kata-handoff`.
  Frontmatter/versioning/naming standard applied. **Dogfood: KataHarness builds itself**, then run it
  on CryptoPortfolioPlanner. No multi-tool adapters yet.
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
- [~] **Spec A — Mode/tier/module/config/bootstrap system.** **A1 (foundations) DONE** (validator +
  cost-weight/license/namespaced-tags frontmatter + generated README index + `kata.config`/dependency-manifest
  schemas + `docs/TAXONOMY.md`; reviewed HOLD→SHIP). **A2 (tier families) + A3 (bootstrap+wiring) remain.**
  cost-weight metadata on all skills; tier
  `kata-grill`/`kata-review`/`kata-plan`/`kata-diagnose` (separate files, shared rubric); mode-hint depth for
  `kata-design-doc`/`kata-tdd`; `kata-evaluate` stays single (floor, D22); `kata.config`; `kata-bootstrap`
  (selector + cost preview); `docs/TAXONOMY.md`; orchestrate reads config. Fold grill efficiency refactor in.
- [ ] **Spec B — Bake-off.** N variants → judge → pick → refine up (AgentHub / worktrees).
- [ ] **Spec C — Version-ups of existing projects.** Improvement-Kata on live repos; consumes `kata.config`.
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
