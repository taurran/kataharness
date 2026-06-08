# STATE — KataHarness

**Phase:** v0.1 execution skills built + Arm A run green · **Version:** pre-v0.1 · **Updated:** 2026-06-06

## Where we are
- Project scaffolded at `C:\Dev\Projects\KataHarness` (git, `.gitattributes eol=lf`). Foundation committed.
- Canonical docs: `AGENTS.md`, `CLAUDE.md` (pointer), `docs/{DESIGN,STANDARDS,TEST-PLAN}.md`, `README.md`
  (versioned skill index). `.planning/{PROJECT,ROADMAP,DECISIONS(16),LESSONS-LEARNED(10),BACKLOG,STATE,STEERING,REVIEW-v0.1}.md`.
- Reference skills vendored (gitignored): `research/reference/{mattpocock-skills,bmad-method}`; GSD local
  at `~/.claude/get-shit-done`.
- **15 `kata-*` skills built**, all `0.1.0/experimental`: the v0.1 ten + `kata-review` + the four
  v0.2-pulled-forward (`kata-diagnose`, `kata-selfhandoff`, `kata-improve`, `kata-write-skill`). 3 remain
  unbuilt: `kata-tasklist` (deferred — redundant with state.json + the plan DAG until workers self-select),
  `kata-zoom-out` (deferred — too thin), `kata-engram` (backlog, gated on a mature engram, D9). The README
  index is the source of truth. (Adversarial-reviewed → `.planning/REVIEW-v0.1.md`; new batch review pending.)
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

## Active workstream — OPERATING MODES (Spec A1 BUILT 2026-06-07)

**Spec A1 (foundations) DONE** on branch `modes/A1-foundations` (not yet merged): skill-conformance validator
(`tools/validate_skills.py`, 9 tests), schema-v2 frontmatter on all 15 skills (`cost-weight`+`license`+
namespaced `tags`), frontmatter-generated README index, `protocol/config.md`+`protocol/dependencies.md`
schemas, `docs/TAXONOMY.md`, Apache-2.0 `LICENSE`. Adversarially reviewed (`.planning/specs/modes-A1-foundations/REVIEW.md` — HOLD→SHIP; 4 blockers + 9 secondary fixed). **Next: A2 (tier families).**


Brainstormed a major new capability: cost/effort/thoroughness **operating modes** (Essential/Standard/Advanced),
all one-shot, consistency-first. Full design in `docs/MODES-DESIGN.md`; vocabulary in `CONTEXT.md`; skill
token-weights in `.planning/SKILL-COST-RATINGS.md`; decisions D17–D23. Prior art researched (FrugalGPT cascade,
Cursor/AgentHub best-of-N, Claude `effort`, GitHub Spec Kit) — pieces exist; our synthesis (skill-set tiering +
escalation-with-reuse + Improvement-Kata version-ups) is the contribution.

## Next action (in order)
1. **Modes: spec review → implement.** On resume: user reviews `docs/MODES-DESIGN.md`; confirm the 2 pending
   items (mode=tier unification; `kata-bootstrap` as its own skill); then `kata-plan`/writing-plans for
   **Spec A** (mode/tier/module/`kata.config`/`kata-bootstrap` + bake cost-weights into frontmatter + tier
   `kata-grill`/`kata-review`/`kata-plan`/`kata-diagnose`; `kata-evaluate` stays single, D22; write `TAXONOMY.md`;
   fold grill efficiency refactor in). Then Spec B (bake-off), Spec C (version-ups), `design` module (own spec).
2. **D16 A/B (parallel priority):** planning-VARIED A/B to prove the grill differentiates — still outstanding;
   do before calling v0.1 "validated."
3. **Backlog:** `kata-tasklist` (reframed → virtual board/PM), `kata-zoom-out`, `kata-engram`; adapters; set a
   git remote before public release.

## Model per stage
Build KataHarness → **Opus 4.8**. CPP test arms → **Sonnet 4.6** (constant across arms). I pin subagent
models on spawn; operator sets main-session model via `/model`.

## Concurrent
CPP runs in its own session (Phase 3 next). CPP will consume KataHarness at v0.1; CPP does periodic
status check-ins on this project.

## Open decisions for the user
- License (pre-public). Suite/plugin packaging shape. Whether to do WoZ-first (recommended) or build v0.1
  straight away.
