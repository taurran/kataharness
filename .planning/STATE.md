# STATE — KataHarness

**Phase:** v0.1 execution skills built + Arm A run green · **Version:** pre-v0.1 · **Updated:** 2026-06-06

## Where we are
- Project scaffolded at `C:\Dev\Projects\KataHarness` (git, `.gitattributes eol=lf`). Foundation committed.
- Canonical docs: `AGENTS.md`, `CLAUDE.md` (pointer), `docs/{DESIGN,STANDARDS,TEST-PLAN}.md`, `README.md`
  (versioned skill index). `.planning/{PROJECT,ROADMAP,DECISIONS(14),LESSONS-LEARNED(7),BACKLOG,STATE,STEERING}.md`.
- Reference skills vendored (gitignored): `research/reference/{mattpocock-skills,bmad-method}`; GSD local
  at `~/.claude/get-shit-done`.
- **0 `kata-*` skills built yet** — all 18 in the README index are `0.0.0 / planned`. v0.1 = 10 skills.
- **CPP baseline frozen** for the test: tag `cpp-phase2-baseline` pushed (220 tests green).

## Done so far (this session, 2026-06-06)
- Froze the shared control: CPP `03-DESIGN.md` + `03-01-PLAN.md` (4 locked decisions, 4-task disjoint partition).
- Built the **5 v0.1 execution skills** (`kata-orchestrate/worktree/board/tdd/evaluate`) → `0.1.0/experimental`.
- Ran **Arm A** (KataHarness via Sonnet subagents in CPP worktrees) → GREEN: 244 tests, det build, Snyk 0,
  fresh-context `kata-evaluate` 9/9 PASS, **0 drift / 0 escalations / 0 human interventions** ([[LESSONS-LEARNED]] L9).
- Arm A lives on CPP branch `test/phase3-kata` (worktree `C:/Dev/_kata_armA/integration`).

## Next action (in order)
1. **Get Arm B numbers + render the A/B verdict.** User is running standard GSD as Arm B on CPP
   `phase-3/gsd-baseline`. Compare one-shot-to-green / plan-drift / interventions / gate-integrity / hygiene
   (per `docs/TEST-PLAN.md`); record the verdict in `LESSONS-LEARNED.md`. Decide which branch CPP keeps.
2. **Fix the weak link: `kata-grill` (see [[LESSONS-LEARNED]] L8).** GSD-format clickable-or-plain-text
   questions, iterative + demanding, grill-with-docs thoroughness + doc-baking, converging on a *very
   specific* design contract. The one-pass WoZ grill is below standard.
3. **Build the remaining v0.1 planning skills** (`kata-context, kata-design-doc, kata-plan`) + `kata-handoff`
   to `docs/STANDARDS.md` frontmatter; then bump README + suite version.

## Model per stage
Build KataHarness → **Opus 4.8**. CPP test arms → **Sonnet 4.6** (constant across arms). I pin subagent
models on spawn; operator sets main-session model via `/model`.

## Concurrent
CPP runs in its own session (Phase 3 next). CPP will consume KataHarness at v0.1; CPP does periodic
status check-ins on this project.

## Open decisions for the user
- License (pre-public). Suite/plugin packaging shape. Whether to do WoZ-first (recommended) or build v0.1
  straight away.
