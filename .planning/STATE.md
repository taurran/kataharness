# STATE — KataHarness

**Phase:** Foundation laid + test designed · **Version:** pre-v0.1 · **Updated:** 2026-06-06

## Where we are
- Project scaffolded at `C:\Dev\Projects\KataHarness` (git, `.gitattributes eol=lf`). Foundation committed.
- Canonical docs: `AGENTS.md`, `CLAUDE.md` (pointer), `docs/{DESIGN,STANDARDS,TEST-PLAN}.md`, `README.md`
  (versioned skill index). `.planning/{PROJECT,ROADMAP,DECISIONS(14),LESSONS-LEARNED(7),BACKLOG,STATE,STEERING}.md`.
- Reference skills vendored (gitignored): `research/reference/{mattpocock-skills,bmad-method}`; GSD local
  at `~/.claude/get-shit-done`.
- **0 `kata-*` skills built yet** — all 18 in the README index are `0.0.0 / planned`. v0.1 = 10 skills.
- **CPP baseline frozen** for the test: tag `cpp-phase2-baseline` pushed (220 tests green).

## Next action (fresh-context, in order)
1. **(Recommended) Wizard-of-Oz validation** — run the `DESIGN.md` loop *by hand* on CPP Phase 3 (Arm A)
   vs the GSD baseline (Arm B), **Sonnet both arms**, branches off `cpp-phase2-baseline`. Confirm the
   method beats the baseline before automating. See `docs/TEST-PLAN.md`.
2. **Build v0.1 skills on Opus 4.8** (D13) — the 10: `kata-grill, kata-context, kata-design-doc, kata-plan,
   kata-orchestrate, kata-board, kata-worktree, kata-tdd, kata-evaluate, kata-handoff`. ~7 are adaptations
   of vendored mattpocock skills + the CPP `cpp-*` skills; only `kata-board`, `kata-worktree`, and
   `kata-plan` file-ownership are new. Each to `docs/STANDARDS.md` frontmatter (semver, source, allowed-tools).
3. **Re-run the automated A/B** on CPP Phase 3 (Sonnet) for the real result; record in `LESSONS-LEARNED.md`.

## Model per stage
Build KataHarness → **Opus 4.8**. CPP test arms → **Sonnet 4.6** (constant across arms). I pin subagent
models on spawn; operator sets main-session model via `/model`.

## Concurrent
CPP runs in its own session (Phase 3 next). CPP will consume KataHarness at v0.1; CPP does periodic
status check-ins on this project.

## Open decisions for the user
- License (pre-public). Suite/plugin packaging shape. Whether to do WoZ-first (recommended) or build v0.1
  straight away.
