# STATE — KataHarness

**Phase:** v0.1 skill-complete · Modes A1–A4 merged · 2 specs converging (sprint-cadence, loop-cognition) · **Version:** pre-v0.1 · **Updated:** 2026-06-18

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
  projects**. PokeVault vault is READY (`C:\Users\taurr_nvs748q\PokeVault\PokeVault`, incl.
  `toolkit/agent-sops/`) — KataHarness's install/test home (under `toolkit/`).

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

## 2026-06-11 (evening session) — D59 + sprint-cadence spec opened
- **D59 — model routing Opus → Fable 5** for deep/judgment work (`claude-fable-5`); Sonnet stays the
  lightweight workhorse; 8 skill `model:` pins flipped to `fable`; test arms remain Sonnet (D14/D57).
- **NEW capability spec opened: sprint-cadence** (`.planning/specs/sprint-cadence/`) — user-requested
  bootstrap toggle between **one-shot** (current loop) and **sprint** execution (plan partitions the project
  into GSD-style sprints; run one sprint → gate → output → user course-corrects via grill → re-enter, same
  or new session). RESEARCH.md maps the plumbing (config `cadence` field, bootstrap question + re-entrancy,
  kata-plan roadmap layer, boundary handoff/report, delta-grill; orchestrate ideally sprint-blind; sprint
  N≥2 reuses the A4 version-up regression contract). GRILL-LEDGER.md holds **10 OPEN branches (SC-GB1–10)**
  with recommendations — **user answers them next session.** Framing rule: each sprint is a one-shot; the
  boundary is the scheduled re-plan event (spine #2 compatible).

## 2026-06-15 — sprint-cadence grill CONVERGED + engram registry created (uncommitted until 2026-06-18)
- **Sprint-cadence ledger fully resolved (SC-GB1–10 + engram cross-cut).** Knob = **`delivery: one-shot |
  incremental`** (unit = sprint); three-layer freeze (DESIGN north-star / ROADMAP boundary-amendable / sprint
  PLAN immutable) + Boundary Change-Control Protocol G1–G4; sequencing A+C (re-entrant `kata-bootstrap` routes,
  `kata-orchestrate` stays sprint-blind, NEW thin `kata-sprint`); three-tier state w/ derived `.kata/` cache
  rebuilt from git; scoped delta-grill course-correct (default always-stop); prime-frame sizing primitive
  (refines D8); sprint N≥2 = version-up vs most-recent-green baseline; bake-off trimmed; **D16-first LOCKED**.
- **`protocol/engram.md` CREATED** — engram plugin contract + seam registry (E1–E21, C1–C6, backend binding
  incl. MindBridge clean-room). Adversarially reviewed (HOLD→hardened). Freeze-gate audit on sprint-cadence
  returned HOLD with must-fixes (roadmap-layer is NET-NEW in kata-plan; pin tunables; D8 supersession; etc.).

## 2026-06-18 — loop-cognition spec OPENED + CONVERGED (this session)
- **NEW umbrella spec `loop-cognition`** (`.planning/specs/loop-cognition/{RESEARCH,GRILL-LEDGER}.md`): three
  entangled loop enhancements — **RS** in-loop research subagent (escalation-routed, grounding-gated,
  fresh-context no-write `kata-research`), **AO** agent orientation (orchestrator-assembled stable→context→
  volatile tiers; vertical rollup + `kata-graph` lazy adjacency pointers; `protocol/orientation.md` +
  `kata-orient`), **ML** managed learning (candidate-skill distillation → 2-stage gate → human promotion
  `kata-promote`; second-brain LEARN feed as Karpathy-LLM-Wiki-pattern synthesis; progressive autonomy
  `engram.autonomy` maturity∧config AND-gate, grounding never bypassed).
- **Hermes Agent (Nous) baked off** — verdict: borrow mechanisms (autonomous distillation, protected
  head+tail compaction, tiered prompt assembly, `.usage.json` telemetry), keep OUR gates (default-FAIL +
  human promotion). Their no-gate skills + emergent-plan compaction = the failure modes our spine prevents.
- **LC-GB1–9 + RS-GB1–3 + AO-GB1–3 all RESOLVED + user-confirmed.** Sequencing = **Path 2**: D16 first, build
  the LEARN-only feed pipeline (β) in parallel (it's an engram *prerequisite*, low-drift, observe-and-emit,
  zero CONSULT). Artifact map recorded (NEW: kata-research/kata-orient/kata-promote + protocol/orientation +
  protocol/wiki-synthesis; EXTEND: evaluate/review/selfhandoff/orchestrate/handoff/improve/graph).
- **Freeze-gate audited HOLD→SHIP** (fresh-context Opus; MF1–MF3 + SF1–SF4 resolved; re-confirm SHIP).
  **DESIGN FROZEN** (`loop-cognition/DESIGN.md`); decisions promoted **D60–D69**; β ingested into ROADMAP
  (∥ D16), rest post-D16.
- **NEXT:** build the β feed pipeline (∥ D16) per DESIGN §L7/L9; in parallel open the D16 spec grill (the
  LOCKED v0.1 gate) and apply sprint-cadence's must-fixes before its own freeze. Tracked in the live task list.

## Next action (sequencing decision pending — adversarial review recommends D16 first)
0. **Answer the sprint-cadence grill ledger** (`.planning/specs/sprint-cadence/GRILL-LEDGER.md`, SC-GB1–10)
   — note SC-GB10 proposes: freeze the sprint DESIGN now, build after D16.
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
Build KataHarness → **Claude Fable 5** (`claude-fable-5`, D59 — supersedes the Opus routing). D16 test
arms → **Sonnet** (constant across arms — D14 principle, survives D57/D59). I pin subagent models on
spawn; operator sets main-session model via `/model`.

## Open decisions for the user
- Confirm D16-first sequencing (adversarial review recommends it; Option D "grill-KG-first" was reviewed
  and REJECTED 2026-06-10). Suite/plugin packaging shape. Git remote before public release.

## Session Continuity
Last session: 2026-06-18. Stopped at: loop-cognition grill fully converged + user-confirmed (LC-GB1–9,
RS-GB1–3, AO-GB1–3); STATE/HANDOFF refreshed; checkpoint commit of 2026-06-15 (sprint-cadence converged +
engram.md) + 2026-06-18 (loop-cognition spec) work. Resume file: `.planning/HANDOFF.md` (read it first).
**Immediate next:** loop-cognition DESIGN is FROZEN (D60–D69; audit HOLD→SHIP) and β is ingested into ROADMAP.
Next = (1) build the β LEARN-only feed pipeline (∥ D16, observe-and-emit, zero CONSULT, redaction-gated);
(2) open the D16 spec grill (the LOCKED v0.1 gate); (3) apply sprint-cadence must-fixes before its freeze.
D16-first remains LOCKED; everything except β builds after D16. Live task list carries the path.
