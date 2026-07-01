# ROADMAP — KataHarness

Improvement-Kata cadence: each milestone ends with a retro into `LESSONS-LEARNED.md` → `kata-improve`.

- [x] **v0.1 — Claude-only one-shot core.** ✅ **SHIPPED 2026-06-30 (tag `v0.1.0`).** Prove the loop
  one-shots a complex task from a frozen design+plan. Skills: `kata-grill`, `kata-context`,
  `kata-design-doc`, `kata-plan`, `kata-orchestrate` (plan-guardian), `kata-board`, `kata-worktree`,
  `kata-tdd`, `kata-evaluate`, `kata-handoff`. Frontmatter/versioning/naming standard applied.
  **Dogfood: KataHarness builds itself**, then validate via the D16 planning-varied A/B on small
  one-shottable test projects (D57). No multi-tool adapters yet.
  - **RELEASE CHECKLIST — DONE 2026-06-30:** versioning policy flipped from **hold-at-`0.1.0`** to
    **bump-on-modify** (STANDARDS §3 — active). v0.1 cluster (items 1–5) ALL COMPLETE; remaining
    backlog explicitly deferred to v0.1.x (see `BACKLOG.md` "Explicitly deferred to v0.1.x" section).
    **Cluster gates met:** (1) sprint-cadence D15/A5 fresh-context `kata-review` SHIP ✅ · (2)
    wiring-completeness interim pin ✅ · (3) guard-consistency repo-wide ✅ · (4) CWE-23 `.snyk`
    record ✅ · (5) benchmark n=0→n=1 live ✅. **Final full adval: 2141 pytest PASS / validate 47/0
    / Snyk medium+ 0.**
- [~] **v0.2 — Self-handoff + concurrency.** PULLED FORWARD into the v0.1 build: `kata-selfhandoff`,
  `kata-diagnose`, `kata-review`, `kata-improve` (+ meta `kata-write-skill`) all built. **Remaining for v0.2:**
  `kata-tasklist` (file-locked self-claim) + the multi-agent self-claim model — deferred until workers
  self-select (today the orchestrator assigns, so it's redundant with state.json + the plan DAG).
- [ ] **v0.3 — Adapters: Codex + Kiro.** `adapters/codex`, `adapters/kiro`; AGENTS.md normalization
  across tools; skill-format mapping; portability tests.
- [ ] **v0.4 — ACP/Quick + cognition.** `adapters/acp-quick` (orchestrator-in-desktop via ACP);
  `cognition/kata-engram` tie-in (gated on a mature kiban/kagami engram).

### Modes & Cost-Tiering track (design DONE 2026-06-07 — `docs/MODES-DESIGN.md`; major new capability)
Operating modes that trade effort/thoroughness/cost, all one-shot; consistency-first. Sequence:
- [~] **Spec A — Mode/tier/module/config/bootstrap system.** **A1 (foundations) DONE+merged** (validator +
  cost-weight/license/namespaced-tags frontmatter + generated README index + schemas + TAXONOMY). **A2 (tier
  families) DONE+merged** (grill/review/plan → 3 tiers, diagnose → light/full; RUBRIC-per-family; depth-hint
  for design-doc/tdd; validator tier rules; reviewed HOLD→SHIP; **D33** structural-invariants-never-tiered).
  **A3 DONE + merged 2026-06-08 (merge `27ca76c`, reviewed SHIP); A4 remains.**
  - **A3 — bootstrap brain + greenfield wiring + version-up-aware/configurable.** ✅ **DONE+merged** (GB1–GB13
    → D34–D46; 24 skills; validator green). New skills: **`kata-bootstrap`** (full configurator: **run-shape router** —
    individual / batch=bakeoff / version-up / advanced, presets *on top of* the mode axis GB1; the D24c ladder;
    cost preview; run-shape-relevant interview only GB13; write `kata.config`) + **`kata-readiness`** (light,
    bootstrap-invoked: harness-health + target-readiness + re-entrant config detection, GB11). Wire
    **`kata-orchestrate`** to read config + resolve family→tier (fallback Standard, D25) **with a fail-closed
    load-guard** (GB12 — not a bootstrap validation phase). Bootstrap re-entrant (cold-start vs reconfigure —
    one skill, GB5) and version-up-aware day one (writes a correct version-up config routing to A4). Fold grill
    efficiency refactor in.
  - **A4 — version-up execution bundle (absorbs the old standalone Spec C).** ✅ **DONE+merged 2026-06-08**
    (merge `de4b0ee`, reviewed SHIP; 25 skills; D47–D56). Scope: **`kata-graph`** (new skill — tree-sitter-floor, feature-agnostic
    cached `kata.graph.json` contract, ~3k-token feature-seeded digest, pluggable backend; `protocol/graph.md`)
    + **version-up wiring** (grill Phase 0 ingest, footprint-scoped disjoint ownership, full-suite-green
    regression contract; no new evaluator) + **`kata-orchestrate` frontier/async-escalation supersession**
    (rolling DAG-frontier dispatch, async park/drain/hard-wait; structured escalation payload →
    `protocol/escalation.md`). Grill converged (GB1…GB10 + HOLD#1/#2/#3; coherence PASSED); decisions D47–D56.
    Composes with bakeoff (D37/D43).
- [ ] **Spec B — Bake-off.** N variants → judge → pick → refine up (AgentHub / worktrees). Composes with
  version-up (a baked-off version-up = N candidate feature-impls, judged on adds-feature ∧ no-regression).
- [ ] **`kata-understand` — post-processing comprehension map (desired state).** Helps the user understand a
  **newly-built** codebase (Understand-Anything nod, GB7). Distinct from `kata-report` (build-log synthesis).
  Own later spec/module, post-v0.1.
- [ ] **`design` module (own spec).** UI/UX, 2D/3D assets, slides, mobile, image-FM — Claude's design
  blind-spot; built to slot into Advanced; inherently tiered.

### loop-cognition track (DESIGN FROZEN 2026-06-18 — `.planning/specs/loop-cognition/`; D60–D69; major new capability)
Three entangled loop enhancements: **RS** in-loop research subagent (`kata-research`, escalation-routed,
grounding-gated), **AO** agent orientation (`kata-orient`, orchestrator-assembled three-tier + `kata-graph`
adjacency, the receiving half of handoff), **ML** managed learning (two-stage candidate→human-promotion skills
via `kata-promote`; second-brain LEARN feed; progressive `engram.autonomy`). Hermes-bake-off verdict (D69):
borrow mechanisms, keep our gates. Freeze-gate audited HOLD→SHIP.
- [x] **β — LEARN-only second-brain feed pipeline** ✅ **DONE 2026-06-18** (D66/D72; D74 + BP1/BP2): a
  `kata-improve` **emit-only sub-mode** (engram seam E6) mines DECISIONS/LESSONS/GRILL-LEDGERs/REVIEWs into
  Karpathy-LLM-Wiki synthesis pages (`produced-by: loop`), per the **wiki-synthesis schema in `protocol/engram.md`**
  (BC5 — no separate file). **Zero CONSULT** (BC2), **redaction-gated** (C3, fail-closed), no-op without
  `engram.learnFeed.dir` (BP1, BC1). Validator 26/0 (engram.md now in `REQUIRED_PROTOCOL`, BP2), pytest 18
  (+3 β seams). Pending: fresh-context `kata-review` (D15). **Next:** RS → AO → ML.
- [x] **D71 Priming-and-Grill wiring** ✅ **DONE 2026-06-18** (spec `priming-and-grill`, DESIGN FROZEN; D73 +
  micro-picks M1–M3): grill **skip** rung (`tiers["kata-grill"]="skip"`, D73) + `kata-bootstrap` grill-depth
  dial (Phase 1.5, D46) + `kata-readiness` Scope-3 prompt-richness recommendation + `kata-orchestrate` skip-floor
  branch + **`kata-defer` built** (new module skill — DEFERRED.md parking + ASSUMPTIONS.md grill-skip log;
  **25→26 skills**) + grill↔RS spectrum documented (`docs/DESIGN.md`, `protocol/config.md`, RUBRIC). Validator
  26/0, pytest 15 (+2 D71 seams). **Caveat:** the floor's RS slot is documented/wired-for but lit in the
  loop-cognition phase. Pending: fresh-context `kata-review` (D15) over the diff.
- [x] **RS — `kata-research` in-loop research subagent + L2 grounding gate** ✅ **DONE 2026-06-19** (D75;
  RS-GB1/2/3): escalation-routed (`research-needed` kind), fresh-context **no-write**, returns
  `{claim, source, confidence, grounds-to-plan?}`; injected-knowledge **grounding gate** in `kata-evaluate` +
  `kata-review` RUBRIC (never bypassed, D33); orchestrator folds GROUND findings via a deliberate superseding
  re-plan, else REJECT/escalate. `kata/module/research`; 26→**27 skills**. Validator 27/0, pytest 21 (+3 RS seams).
  Pending: fresh-context `kata-review` (D15).
- [x] **AO — `kata-orient` + `protocol/orientation.md`** ✅ **DONE 2026-06-19** (D76; AO-GB1/2/3 + user
  extensions): read-only three-tier launch orientation (stable→context→volatile), vertical rollup + kata-graph
  lateral adjacency pointers, **task-type-aware**, contextually-derived **pointers + callouts** from standard
  markdown, **smart questioning routed** (answer-inline / research-needed→RS / human-required→grill), `kata-handoff`
  **Orientation tie-in** (aligned both sides). `kata/spine`; 27→**28 skills**. Validator 28/0, pytest 24. Pending:
  full validation stack on RS **and** AO.
- [x] **ML — `kata-promote` two-stage promotion gate + autonomy dial** ✅ **DONE 2026-06-19** (D77; L5/L6,
  LC-GB3/4/5): stage-1 agent-distilled **candidate** (via `kata-write-skill`, `scope:agent`,
  `<agentSkills.dir>/candidates/`, not universal) → grounding gate → stage-2 **human** gate `kata-promote`
  (AskUserQuestion); `engram.autonomy` AND-gate (default **always-human**, grounding never bypassed); STANDARDS
  §1.3 discriminators; candidate lifecycle in `protocol/state.md`. 28→**29 skills**. Validator 29/0, pytest 27.
  **⇒ loop-cognition is COMPLETE (RS + AO + ML all built + validated).**
- [ ] **CONSULT + full autonomy — gated on a mature engram (D9/D56), post-β-maturity.** The dials
  (`engram.autonomy`, `engram.backend`) are wired + default-safe; lighting them up is the endgame, not now.
  Endgame (α–ε): build fully → full tests → **dogfood version-up on KataHarness itself**, CONSULT-enabled once β
  has matured the fingerprint.

**v0.1 SHIPPED 2026-06-30 (tag `v0.1.0`).** **Modes Spec A (A1–A4) COMPLETE + merged.** **D16-as-RCT is
RETIRED (D70, L11)** — the autonomous grill-vs-baseline A/B tests the wrong axis; **autonomous reliability is
demonstrated** instead, and the v0.1 gate was re-scoped to that + the **Priming-and-Grill architecture
(D71/D72).** Build path (HANDOFF §4): wire D71 ✅ → build loop-cognition β (LEARN feed) ✅ → RS/AO/ML ✅ →
**build sprint-cadence ✅ (D78–D85, 2026-06-19)** → **v0.1 cluster items 1–5 ✅ (2026-06-30)** → **tag
v0.1.0**. Sprint-cadence D15/A5 fresh-context `kata-review`: **SHIP ✅**. Remaining backlog explicitly
deferred to v0.1.x. **Next milestone: v0.2** (tasklist + multi-agent worker self-select; adapters;
post-v0.1 deferred items).

**Pre-public workstreams (post-loop-hardening, 2026-06-21 → 06-24) — COMPLETE:** **WS-1** IP separation (`42e884b`;
work-project name scrubbed, Quick kept as ACP seam, Codex added) · **WS-2** inner-loop autonomy + parallelism
*exercised* (n=1) + `kata-slop-check` shipped (D94) · **WS-3** user-friendliness (D95; persona + narration +
goal-mirror intake + one-dial mode surface + milestone narration + goal-anchored closeout; **WS-4** backout + **WS-5**
transparency folded in) · **WS-3 field-exercised (n=1)** by building **WS-3R** (D96): the two-tier closeout —
concise CLI summary + a self-contained on-brand HTML report + the first KataHarness logo. Remaining pre-public:
WS-1 re-grep · WS-2 worker-self-timestamp polish · (M8 native-in-tool closeout rendering = adapter work) · then **Phase 5 EXTERNAL**
(install-portability · multi-model) + the **v0.1 release-checklist** (flip Policy A). Far-future: agentic-loop
benchmark → recursive parallelism (DAG-within-DAG).

## Progress
| Milestone | Status |
|---|---|
| v0.1 core | ✅ **SHIPPED 2026-06-30 (tag `v0.1.0`)** — 47 skills; 2141 pytest; validate 47/0; Snyk medium+ 0. Cluster items 1–5 all done. Remaining backlog explicitly deferred to v0.1.x. |
| Modes Spec A (A1–A4) | **COMPLETE + merged** — validator + tiers + bootstrap/readiness + version-up/kata-graph + frontier/async-escalation; **25 skills**; D1–D56 |
| sprint-cadence | **COMPLETE + SHIPPED 2026-06-30** (D78–D85 + D15/A5 review SHIP). NEW: `kata-plan` roadmap layer (`ROADMAP.md`) + `kata-sprint` (G1–G4 boundary) + `kata-report` v1; EXTEND config/state/handoff/escalation + selfhandoff/readiness/handoff; orchestrate stays sprint-blind (BC2). D15/A5 fresh-context `kata-review`: **SHIP ✅** |
| loop-cognition | **COMPLETE + merged** (D60–D69 design + RS/AO/ML all built; 3 new skills; β feed DONE 2026-06-18) |
| v0.2 (pulled fwd) | diagnose/selfhandoff/improve/write-skill built; tasklist deferred (needs worker self-select) |
| v0.3–v0.4 | Not started (adapters; ACP/Quick + kata-engram) |
