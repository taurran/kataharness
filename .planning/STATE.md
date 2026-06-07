# STATE — KataHarness

**Phase:** v0.1 execution skills built + Arm A run green · **Version:** pre-v0.1 · **Updated:** 2026-06-06

## Where we are
- Project scaffolded at `C:\Dev\Projects\KataHarness` (git, `.gitattributes eol=lf`). Foundation committed.
- Canonical docs: `AGENTS.md`, `CLAUDE.md` (pointer), `docs/{DESIGN,STANDARDS,TEST-PLAN}.md`, `README.md`
  (versioned skill index). `.planning/{PROJECT,ROADMAP,DECISIONS(14),LESSONS-LEARNED(7),BACKLOG,STATE,STEERING}.md`.
- Reference skills vendored (gitignored): `research/reference/{mattpocock-skills,bmad-method}`; GSD local
  at `~/.claude/get-shit-done`.
- **11 `kata-*` skills built** (the v0.1 ten + `kata-review`), all `0.1.0/experimental`; 7 remain
  `0.0.0/planned` (diagnose, tasklist, selfhandoff, write-skill, improve, zoom-out, engram). The README
  index is the source of truth. (Adversarial-reviewed 2026-06-06 → `.planning/REVIEW-v0.1.md`; fixes applied.)
- **CPP baseline frozen** for the test: tag `cpp-phase2-baseline` pushed (220 tests green).

## Done so far (this session, 2026-06-06)
- Froze the shared control: CPP `03-DESIGN.md` + `03-01-PLAN.md` (4 locked decisions, 4-task disjoint partition).
- Built the **5 v0.1 execution skills** (`kata-orchestrate/worktree/board/tdd/evaluate`) → `0.1.0/experimental`.
- Ran **Arm A** (KataHarness via Sonnet subagents in CPP worktrees) → GREEN: 244 tests, det build, Snyk 0,
  fresh-context `kata-evaluate` 9/9 PASS, **0 drift / 0 escalations / 0 human interventions** ([[LESSONS-LEARNED]] L9).
- Arm A lives on CPP branch `test/phase3-kata` (worktree `C:/Dev/_kata_armA/integration`).

## Also done (2026-06-06, cont.)
- **A/B verdict recorded: TIE** ([[LESSONS-LEARNED]] L10). Arm B (GSD) matched Arm A on every objective
  metric incl. the identical in-lane auto-fix → execution half on-par, not better; differentiation lives in
  the (frozen-for-both) planning half. User shipping Arm B to CPP `main`.
- **Built the remaining v0.1 planning skills + the adversarial leg** → all `0.1.0/experimental`:
  `kata-grill` (deep, to the L8 standard: GSD-format choice-or-text questions, relentless + doc-grounded,
  doc-baking, convergence criteria, anti-shallow guard + a `resources/DECISION-LEDGER.md`),
  `kata-context`, `kata-design-doc`, `kata-plan` (disjoint file-ownership + wave DAG), `kata-handoff`,
  and **`kata-review`** (adversarial/red-team — the EVALUATE leg the A/B exposed as missing, L10).
- **v0.1 is now skill-complete: 11 skills built** (the 10 + kata-review). README index promoted.

## Next action (in order)
1. **The real test: an A/B that VARIES the planning step.** This run froze the spec for both arms, so the
   grill (the differentiator) was untested. Next: pick a fresh complex task; Arm A plans via `kata-grill`→
   `kata-design-doc`→`kata-plan` for real, Arm B via GSD planning; then execute + compare. Only this can
   show whether the grill earns the harness's complexity ([[LESSONS-LEARNED]] L10).
2. **Field-test `kata-grill` itself** — its depth is built but unproven on a live user. Watch for: does it
   actually converge on a *more specific* contract than the WoZ survey did?
3. **Backlog (post-v0.1):** `kata-diagnose, kata-tasklist, kata-selfhandoff, kata-write-skill, kata-improve,
   kata-zoom-out, kata-engram`; adapters (`claude/codex/kiro/acp-quick`); set a git remote before public release.

## Model per stage
Build KataHarness → **Opus 4.8**. CPP test arms → **Sonnet 4.6** (constant across arms). I pin subagent
models on spawn; operator sets main-session model via `/model`.

## Concurrent
CPP runs in its own session (Phase 3 next). CPP will consume KataHarness at v0.1; CPP does periodic
status check-ins on this project.

## Open decisions for the user
- License (pre-public). Suite/plugin packaging shape. Whether to do WoZ-first (recommended) or build v0.1
  straight away.
