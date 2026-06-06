# STATE — KataHarness

**Phase:** Foundation laid · **Version:** pre-v0.1 · **Created:** 2026-06-06

## Where we are
- Project scaffolded at `C:\Dev\Projects\KataHarness` (git init, `.gitattributes eol=lf`).
- Canonical docs written: `AGENTS.md`, `CLAUDE.md` (pointer), `docs/DESIGN.md`, `docs/STANDARDS.md`,
  `README.md` (versioned skill index), `.planning/{PROJECT,ROADMAP,DECISIONS,LESSONS-LEARNED,BACKLOG}.md`.
- Reference skills vendored for evaluation: `research/reference/{mattpocock-skills,bmad-method}` (gitignored);
  GSD referenced locally at `~/.claude/get-shit-done`.
- 12 decisions locked (DECISIONS.md); 7 lessons seeded from the CPP session (LESSONS-LEARNED.md).

## Next action
1. Write `research/NOTES.md` — deep eval of mattpocock + BMAD + GSD; map adopted patterns → each `kata-*` skill.
2. Dogfood `kata-grill` on **v0.1 core** to spec the first real skills (`kata-grill`, `kata-context`,
   `kata-design-doc`, `kata-plan`, `kata-orchestrate`, `kata-board`, `kata-worktree`, `kata-tdd`,
   `kata-evaluate`, `kata-handoff`).
3. Then run the agentic loop to build v0.1; prove it by having KataHarness build itself.

## Concurrent
- CryptoPortfolioPlanner runs in its own session (Phase 3 / G_macro next). CPP will consume KataHarness
  at v0.1; CPP sessions do periodic status check-ins on this project.

## Open decisions for the user
- License choice (pre-public). Suite/plugin packaging shape. Whether v0.1 dogfood target is
  KataHarness-builds-itself first or CPP first (currently: itself, then CPP).
