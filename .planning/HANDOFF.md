# HANDOFF — KataHarness — 2026-06-06

> **Fresh session: read in order, then resume.**
> 1. `AGENTS.md` (canonical spine) · 2. `docs/DESIGN.md` (charter) · 3. `docs/STANDARDS.md`
>    (frontmatter/versioning/naming) · 4. `docs/TEST-PLAN.md` (the A/B validation) · 5. `.planning/STATE.md`
>    + `.planning/DECISIONS.md` (14 locked) + `.planning/LESSONS-LEARNED.md` (7, seeded from CPP).

## What this project is
A tool-agnostic, iteratively-improved agent harness that **one-shots complex tasks** (grill → frozen
design+plan → distributed plan-faithful execution → default-FAIL eval → two-way handoff → kata-improve).
Spun out of CryptoPortfolioPlanner's `cpp-*` harness. At `C:\Dev\Projects\KataHarness`, public-intended.

## State
- **Foundation committed** (docs + standards + planning + vendored references). Branch `master` (local only;
  no remote yet — set one before public release).
- **0 skills built.** v0.1 = 10 skills (README index; all `0.0.0/planned`). ~7 adapt from vendored
  mattpocock skills + the CPP `cpp-*` set; new construction = `kata-board`, `kata-worktree`, `kata-plan`
  file-ownership.
- **Test ready:** CPP baseline frozen at tag `cpp-phase2-baseline` (in the CPP repo). Test target = CPP
  **Phase 3 (G_macro)**.

## NEXT STEP (do these in a fresh context, in order)
1. **(Recommended) Wizard-of-Oz** the loop on CPP Phase 3 vs the GSD baseline — **Sonnet both arms**,
   branches off `cpp-phase2-baseline` — to prove the method before building skills. (`docs/TEST-PLAN.md`)
2. **Build v0.1 skills → Opus 4.8** (D13), to `docs/STANDARDS.md` frontmatter. Adapt from
   `research/reference/mattpocock-skills` + the CPP `cpp-*` skills.
3. **Automated A/B** on Phase 3 (Sonnet); log results in `LESSONS-LEARNED.md`; bump README skill versions.

## Models per stage (D13)
Build KataHarness → **Opus 4.8**. CPP Phase-3 test arms → **Sonnet 4.6** (constant across arms). Subagent
models pinned on spawn; operator sets main-session model via `/model`. No auto-compact reliance — durable
to git first, then compact/fresh-session (kata-selfhandoff not built yet).

## Artifacts (by path — don't re-derive)
`AGENTS.md` · `docs/{DESIGN,STANDARDS,TEST-PLAN}.md` · `README.md` (skill index) ·
`.planning/{PROJECT,ROADMAP,DECISIONS,LESSONS-LEARNED,BACKLOG,STATE,STEERING}.md` ·
`research/reference/{mattpocock-skills,bmad-method}` (vendored, gitignored) · GSD at `~/.claude/get-shit-done`.

## Open decisions for the user
License (pre-public) · suite/plugin packaging shape · WoZ-first (recommended) vs build-v0.1-straight-away ·
set a git remote for the public repo.

## Redaction
No secrets/keys/PII. Nothing to redact.
