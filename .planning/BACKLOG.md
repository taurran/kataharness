# BACKLOG — KataHarness

Promote to ROADMAP milestones when ready.

- **research/NOTES.md deep-eval** — score mattpocock skills, BMAD, GSD; record exactly what each
  `kata-*` skill adopts from where (the core bake-in work). *(do before/with v0.1)*
- **Adapters** — `codex`, `kiro`, `acp-quick`; AGENTS.md→tool-instruction-file normalization; skill-format mapping. *(v0.3/v0.4)*
- **`kata-engram`** — cognitive-fingerprint/engram injection from kiban/kagami; gated on a mature second brain. *(v0.4)*
- **Plugin packaging** — package the suite as a Claude Code plugin + a portable bundle; `plugin.json`/suite version.
- **License selection** — choose an OSS license before public release.
- **CPP consumption path** — how CryptoPortfolioPlanner installs/pins KataHarness once v0.1 ships.
- **Protocol specs** — flesh out `protocol/{board,tasklist,state,handoff}.md` schemas.
- **Quick/work version** — fork/branch strategy for the AWS-internal variant.
- **Periodic CPP check-in hook** — lightweight status-eval of KataHarness surfaced into CPP sessions.
- **`kata-tasklist` reframe (D23)** — virtual task board over GSD structure + backlog, syncing to Jira/Asana
  via MCP (env has `pm-skills`/`atlassian`). Replaces the old file-locked-claim purpose.
- **`design` module (own spec)** — UI/UX, 2D/3D assets, slides, mobile, image-FM imagery; slots into Advanced.
- **`docs/TAXONOMY.md`** — categories + `kata-<verb>` naming + tier-family convention (`kata-<verb>-<tier>`) +
  spine-vs-module. Motivated by the modes tiering work; partially specced in `docs/MODES-DESIGN.md`.
- **Skill efficiency refactors** (`.planning/SKILL-COST-RATINGS.md`) — grill L8-narrative + convergence
  checklist → `resources/` (~30% lighter); orchestrate worker-prompt → `protocol/`; tdd supporting-depth → pointer.
  Fold the grill one into Spec A (we restructure grill for tiering anyway).
