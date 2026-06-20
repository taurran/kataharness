# STATE — KataHarness

**Phase:** v0.1 skill-complete · loop-cognition + sprint-cadence built · **DOGFOOD #1 + #2 done** · **first tagged release `v0.1.0-alpha.1`** · **31 skills / 0 errors · pytest 72 · Snyk 0** · private remote (taurran/kataharness) · **Updated:** 2026-06-19

> **Dogfood #2 — the REAL orchestrated run (2026-06-19, `v0.1.0-alpha.1`):** "evaluation self-sufficiency" built
> by **4 concurrent worker subagents in isolated git worktrees**, plan-guardian-driven, **zero-conflict merge**,
> fresh-context default-FAIL eval **PASS** (with its own non-vacuity probes), human version-select. Added
> `tools/run_result.py` (RESULT.json) · `tools/footprint.py` · `tools/mutation_check.py` + the `kata-tdd`
> mutation-proof step + `kata-report`/`kata-evaluate` machine-readable-artifact contracts. pytest 40→72.
> **Honest residual:** the emit/consume path is **not yet wired into a live gate** — the libraries + contracts
> exist; an integration slice must actually call them (→ BACKLOG ★, next increment). Safety tag `pre-dogfood-2`
> + `v0.1.0-alpha.1` on the remote. See `.planning/specs/dogfood-selfup-2/`.

> **Dogfood #1 (2026-06-19):** self version-up enforcing `allowed-tools` ran through the full loop (readiness →
> skip-grill → footprint plan → TDD → fresh-context default-FAIL eval **PASS** → report). **Machinery held**
> (regression contract green end-to-end). **Headline finding:** the end-of-run writeup is **not self-sufficient**
> for in-depth evaluation — needs self-emitted `RESULT.json` + footprint manifest + recorded mutation proof
> (→ BACKLOG ★, strong dogfood-#2 candidate). Also: tree-sitter BLOCK too coarse (R1); manual-drive friction
> (R2). See `.planning/specs/dogfood-selfup-1/`.

> **CURRENT (2026-06-19, top of file — older history below is preserved, not current):** **sprint-cadence is
> BUILT + reviewed SHIP** (D78–D85; 11 tasks / 5 waves; commits `43e7c2c`→`e0d0610`). NEW `kata-plan` roadmap
> layer (`ROADMAP.md`), `kata-sprint` (G1–G4 boundary change-control), `kata-report` v1; the
> `delivery: one-shot|incremental` axis + prime-frame sizing (build-grounded: Fable5/Opus4.8/Sonnet4.6 = 1M
> window, ~0.40 effective band). `kata-orchestrate` stays **sprint-blind** (BC2). A fresh-context `kata-review`
> (D15/A5) returned **SHIP**; its one should-fix — `kata-sprint` was wired-but-not-connected — is **fixed**:
> **`kata-bootstrap` is now the boundary router (D86)**, routing a gated boundary → `kata-sprint`. **31 skills ·
> validator 0 · pytest 38 · Snyk 0.** Loop-cognition (β/RS/AO/ML, D74–D77) + D71 Priming-and-Grill shipped
> earlier this session. **Next = the endgame: dogfood version-up on KataHarness itself** (first real
> `delivery: incremental` exercise — will light up the deferred-runtime BACKLOG). See `.planning/HANDOFF.md`.

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
- **D16 RETIRED as an RCT + Priming-and-Grill resolved (D70/D71/D72, L11).** Two A/B attempts (easy + hardened
  `wordfreq`) proved the autonomous deterministic-gate A/B can't isolate the grill (4/4→10/10 gate passes; grill's
  human-engine is off without a human). **Grill is now an OPTIONAL human certainty layer over the priming prompt,
  with an autonomous-reliability floor** (default-FAIL + RS + assumption-log); grill ledgers are a PRIMARY
  cognitive-fingerprint feed. **Autonomous reliability is demonstrated; v0.1 no longer gated on an RCT → the
  D16-first lock is dissolved → the full build is UNBLOCKED.**
- **D71 Priming-and-Grill wiring ✅ DONE 2026-06-18** (spec `priming-and-grill`, DESIGN FROZEN; D73 + M1–M3):
  grill **skip** rung (`tiers["kata-grill"]="skip"`) + bootstrap grill-depth dial (Phase 1.5) + readiness Scope-3
  prompt-richness recommendation + orchestrate skip-floor branch + **`kata-defer` built** (DEFERRED.md parking +
  ASSUMPTIONS.md grill-skip log; **25→26 skills**) + grill↔RS spectrum doc'd. Validator 26/0, pytest 15.
  **Caveat:** RS slot doc'd/wired-for, lit in the loop-cognition phase. **Pending: fresh-context `kata-review`.**
- **β LEARN feed ✅ DONE 2026-06-18** (D74 + BP1/BP2): `kata-improve` emit-only sub-mode (E6) → Karpathy-LLM-Wiki
  synthesis pages per the schema in `protocol/engram.md` (`produced-by: loop`); **zero CONSULT** (BC2),
  **redaction-gated** (C3), no-op without `engram.learnFeed.dir` (BP1/BC1); `engram.md` now validator-enforced
  (BP2). Validator 26/0, pytest 18. **Pending: fresh-context `kata-review`.**
- **RS ✅ DONE 2026-06-19** (D75; RS-GB1/2/3): `kata-research` escalation-routed fresh-context **no-write**
  researcher (`research-needed` kind); **L2 grounding gate** = injected-knowledge mode of `kata-evaluate` +
  `kata-review` RUBRIC (never bypassed, D33); orchestrator folds GROUND findings via deliberate superseding
  re-plan, else REJECT/escalate-to-human. `kata/module/research`; **27 skills**. Validator 27/0, pytest 21.
  **Pending: fresh-context `kata-review`.**
- **AO ✅ DONE 2026-06-19** (D76; AO-GB1/2/3 + user extensions): `kata-orient` (spine, read-only) three-tier
  launch orientation + `protocol/orientation.md`; **task-type-aware**, contextually-derived **pointers+callouts**
  from standard markdown, **smart questioning routed** (answer-inline / research-needed→RS / human→grill),
  `kata-handoff` Orientation tie-in (aligned both sides). **28 skills.** Validator 28/0, pytest 24.
- **ML ✅ DONE 2026-06-19** (D77; L5/L6): `kata-promote` stage-2 human promotion gate (AskUserQuestion);
  agent-distilled candidates (STANDARDS §1.3, `<agentSkills.dir>/candidates/`, not universal) → grounding gate →
  human gate; `engram.autonomy` AND-gate default **always-human**; candidate lifecycle in `state.md`. **29 skills.**
  Validator 29/0, pytest 27. **⇒ loop-cognition COMPLETE (RS + AO + ML).**
- **NEXT (see HANDOFF §4 THE PLAN):** (1)–(4) ✅ D71/β/RS/AO; (5) ✅ RS+AO validation; (6) ✅ ML →
  **loop-cognition done.** **(7) ✅ sprint-cadence DESIGN FROZEN 2026-06-19** (D78–D85; freeze-gate HOLD→SHIP) →
  **BUILD it next** (NEW: `kata-plan` roadmap layer + `kata-sprint` + `kata-report` v1; needs PLAN + approval);
  **(8) dogfood version-up on KataHarness itself** (the endgame: build fully → full tests → self-improve). CONSULT/full-autonomy
  stay gated on a mature engram.

## Next action — RS → AO → ML (D16 lock dissolved by D70; D71 + β DONE 2026-06-18)
> ⚠️ The numbered list below predates D70 and is **superseded** — it described the D16-first sequencing that no
> longer applies. Authoritative next step: **RS (research subagent), then AO, then ML.** Kept for provenance.
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
**Immediate next:** the session resolved the **Priming-and-Grill architecture (D70/D71/D72, L11)** and
**retired D16 as an RCT** — autonomous reliability is demonstrated, so the full build is UNBLOCKED. Read
`.planning/HANDOFF.md` (rewritten for this hand-off) — §4 THE PLAN: wire D71 → build β → RS/AO/ML → freeze
sprint-cadence → dogfood version-up. loop-cognition DESIGN is FROZEN (D60–D69). The user will compact + orient
a fresh session from the handoff.
