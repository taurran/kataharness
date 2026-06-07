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

**Pre-v0.1 (now):** finish `research/NOTES.md` deep-eval of mattpocock + BMAD + GSD (what to adopt);
then dogfood `kata-grill` to spec v0.1's first skills.

## Progress
| Milestone | Status |
|---|---|
| v0.1 core | 11 skills built; adversarially reviewed + fixed; execution half field-proven (A/B tied, L10) |
| v0.2 (pulled fwd) | diagnose/selfhandoff/improve/write-skill built; tasklist deferred (needs worker self-select) |
| v0.3–v0.4 | Not started (adapters; ACP/Quick + kata-engram) |
