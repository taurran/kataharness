# STATE — KataHarness

**Phase:** v0.1 skill-complete · Modes Spec A1+A2+A3+A4 merged · **Version:** pre-v0.1 · **Updated:** 2026-06-10

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
- **2026-06-10 — CPP decoupled (D57) + PortaVault→PokeVault (D58).** CPP is no longer the test medium or
  consumer (history stands; provenance kept). The D16 A/B target is reshaped to **small one-shottable test
  projects**. PokeVault vault is READY (`C:\Users\taurr_nvs748q\PokeVault\PokeVault` ·
  `github.com/taurran/pokevault`, incl. `toolkit/agent-sops/`) — KataHarness's install/test home.

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

## Active workstream — OPERATING MODES (Spec A1 + A2 + A3 MERGED to master; A4 in progress)

**Spec A1 (foundations) DONE + merged**: skill-conformance validator (`tools/validate_skills.py`), schema-v2
frontmatter (`cost-weight`+`license`+namespaced `tags`), frontmatter-generated README index,
`protocol/config.md`+`protocol/dependencies.md`, `docs/TAXONOMY.md`, Apache-2.0 `LICENSE`. Reviewed HOLD→SHIP.
**Spec A2 (tier families) DONE**: `kata-grill`/`kata-review`/`kata-plan` → 3 tiers each, `kata-diagnose` →
light/full; shared `RUBRIC.md` per family (DRY-by-pointer); `kata-design-doc`/`kata-tdd` got a mode depth-hint;
validator gained tier-family rules. Adversarially reviewed (HOLD→SHIP; surfaced **D33: structural invariants
are never tiered**).
**Spec A3 (bootstrap + wiring) DONE + merged 2026-06-08** (merge `27ca76c`): **`kata-bootstrap`** (run-shape
router — individual/batch/version-up/advanced as PRESETS over the mode axis; D24c ladder; run-shape-relevant
interview) + new light **`kata-readiness`** (harness-health + target-readiness + re-entrant config detection) +
**`kata-orchestrate`** reads `kata.config`, resolves family→tier (fallback Standard/D25) with a **fail-closed
load-guard** (GB12). `kata.config` schema gained `runShape`+`target` (version-up). Grilled GB1–GB13 → promoted
to **D34–D46**; adversarially reviewed **SHIP** (`.../modes-A3-bootstrap-wiring/REVIEW.md`). **24 skills**,
validator green, 12 tests. Versioning **policy A** (hold all skills at 0.1.0 till v0.1 ships, then bump-on-modify).
**A4 (version-up + kata-graph) — DONE + MERGED to master 2026-06-08 (merge `de4b0ee`, reviewed SHIP; 25 skills,
validator green, 13 tests)**: DESIGN frozen (`.planning/specs/modes-A4-version-up/DESIGN.md`);
grill ledger fully converged (GB1…GB10 + HOLD#1/#2/#3 resolutions; coherence audit PASSED;
`.planning/specs/modes-A4-version-up/GRILL-LEDGER.md`); A4-GB decisions promoted to **D47–D56** (this
session). Scope: **`kata-graph`** (tree-sitter-floor, feature-agnostic cached `kata.graph.json` contract,
feature-seeded ~3k-token digest, pluggable grep/tree-sitter/Graphify-MCP backend) + **version-up wiring**
(grill Phase 0 ingest, footprint-scoped disjoint ownership with defer-first + escalate-rare protections,
full-suite-green regression contract) + **`kata-orchestrate` frontier/async-escalation supersession** (rolling
DAG-frontier dispatch, async park/drain/hard-wait, structured escalation payload in its own contract
`protocol/escalation.md`). Deferred clean: Obsidian KG story (own spec under kata-understand, D54);
engram-mediated escalation (D56). Then Spec B (bake-off), `design` module. Parallel outstanding: D16
planning-varied A/B.


Brainstormed a major new capability: cost/effort/thoroughness **operating modes** (Essential/Standard/Advanced),
all one-shot, consistency-first. Full design in `docs/MODES-DESIGN.md`; vocabulary in `CONTEXT.md`; skill
token-weights in `.planning/SKILL-COST-RATINGS.md`; decisions D17–D23. Prior art researched (FrugalGPT cascade,
Cursor/AgentHub best-of-N, Claude `effort`, GitHub Spec Kit) — pieces exist; our synthesis (skill-set tiering +
escalation-with-reuse + Improvement-Kata version-ups) is the contribution.

## Next action (sequencing decision pending — adversarial review recommends D16 first)
1. **D16 planning-varied A/B (the v0.1 validation gate; ROADMAP-sequenced FIRST):** prove the grill
   differentiates — Arm A plans via `kata-grill`→`kata-design-doc`→`kata-plan` vs a GSD baseline. **Target
   reshaped (D57): small one-shottable greenfield projects in a dedicated test directory** (repeated paired
   measurements, not one big task). Needs its own spec grill (`.planning/specs/`) — TEST-PLAN v1 is superseded.
2. **Obsidian-KG / kata-understand spec** — emit+ingest over the `kata.graph.json` contract (D54/D55).
   **PokeVault gate SATISFIED (D58)** — vault is git-versioned/durable, so no freshness pressure; sequenced
   AFTER D16 per ROADMAP + the 2026-06-10 adversarial review of the "grill-KG-first" option (REJECTED:
   premise decay — durable vault; post-v0.1 inversion; rework exposure from an unvalidated grill).
3. **Spec B — bake-off** (anytime; composes with version-up, D37).
- **Backlog:** A3-review carry-overs (`kata-readiness` harness-vs-target wording for the KG spec; `tools/`
  example-`kata.config` check) · `kata-defer`/`kata-understand`/`kata-tasklist`/`kata-engram` · adapters ·
  **set a git remote before public release** (still local-only).

## Model per stage
Build KataHarness → latest **Opus**. D16 test arms → **Sonnet** (constant across arms — D14 principle,
survives D57). I pin subagent models on spawn; operator sets main-session model via `/model`.

## Open decisions for the user
- Confirm D16-first sequencing (adversarial review recommends it; Option D "grill-KG-first" was reviewed
  and REJECTED 2026-06-10). Suite/plugin packaging shape. Git remote before public release.

## Session Continuity
Last session: 2026-06-10. Stopped at: D57/D58 recorded (CPP decoupled; PokeVault ready + named install
home); TEST-PLAN v1 marked superseded; adversarial review of sequencing options delivered — awaiting the
user's path confirmation (recommendation: open the D16 spec grill next).
