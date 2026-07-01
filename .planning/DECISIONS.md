# DECISIONS — KataHarness (ADR log)

Locked decisions. Format: ID · decision · why. Never silently reverse — supersede with a new ID.

- **D1 — The plan does not drift.** Orchestrator = plan-guardian (owns frozen plan, task assignment,
  file-ownership, gating); peers execute + communicate, never re-plan; unknowns escalate. *Why:* drift
  is the enemy of one-shot; evidence (Anthropic managed-agents + harness) favors centralized plan ownership.
- **D2 — One-shot = no plan churn.** Deep plan → execute → eval → targeted fix vs the same plan.
- **D3 — Agnostic via adapter pattern.** Agnostic core + thin per-tool adapters. *Why:* pure-files-only
  forfeits every tool's good parts; depending on one tool forfeits agnosticism.
- **D4 — Do NOT depend on Claude Agent Teams; mine its protocol.** Reimplement mailbox + file-locked
  task-claim + lead as agnostic files. *Why:* Teams is Claude-only/experimental; cross-tool is the goal.
  Teams remains a reference + optional Claude-adapter feature.
- **D5 — AGENTS.md is canonical; CLAUDE.md is a pointer.** *Why:* AGENTS.md is the cross-tool industry
  standard; Claude is the exception.
- **D6 — Per-skill semver in frontmatter; README index is the source of truth.** Frontmatter + naming
  are first-class. *Why:* the suite must be independently versionable and discoverable.
- **D7 — Naming: `kata-<verb>`, categorized by loop phase.** Permeates skills/files/protocol/adapters.
- **D8 — Self-handoff threshold is configurable and anti-over-conservative; task-boundary preferred;
  re-anchor on plan.** *Why:* a naive fixed % kills sessions early / degrades context (user-flagged).
- **D9 — Engram/cognitive-fingerprint = designed extension point, backlog (not v0.1).** Gated on a
  mature second brain (kiban/kagami).
- **D10 — KataHarness is its own standalone public project, not a CPP sub-package.** *Why:* independent
  release; public vs private CPP; cross-tool by nature; own license/docs. CPP consumes it at v0.1.
- **D11 — Durable artifacts are Obsidian-native (YAML frontmatter + [[wikilinks]] + tags); machine
  coordination state kept separate.**
- **D12 — Provenance required (`source:` frontmatter) when adapting external skills.** Stand on
  shoulders *and* attribute.
- **D13 — Model routing for build vs test.** Building KataHarness skills → **Opus 4.8** (best foot
  forward; the harness quality matters most). The CPP Phase-3 **test arms → Sonnet 4.6** (both arms).
  *Why:* the headline claim is "the harness lifts the cheaper workhorse model"; Opus would mask the lift.
  If the test flubs, retry later. Subagent models are pinned on spawn; the main-session model is the
  operator's `/model`.
- **D14 — A/B test design (see docs/TEST-PLAN.md).** Target = CPP Phase 3 @ tag `cpp-phase2-baseline`.
  Arm A = KataHarness loop; Arm B = our **current GSD process** (the honest baseline, not a naive agent).
  **Hold model constant (Sonnet) across arms; fresh context per arm on its own branch; same frozen
  Phase-3 design+plan to both.** Metrics: one-shot-to-green, plan-drift (target 0, esp. sleeve
  classification), interventions, gate integrity, handoff recovery, hygiene. **Validate the loop manually
  (Wizard-of-Oz) before building all skills.**
- **D15 — Adversarial review (`kata-review`, fresh-context) is mandatory on everything built here, ≥ once,
  before it is called done.** *Why:* the v0.1 adversarial pass (`.planning/REVIEW-v0.1.md`) caught real
  defects a conformance gate missed — over-claims, source name-drops, the griller grading itself, a racy
  board. Conformance ≠ correctness ([[LESSONS-LEARNED]] L6/L10). This is now standing process, not optional.
- **D16 — v0.1 is NOT "validated" until a planning-VARIED A/B.** *Why:* the first A/B froze the plan for both
  arms and tied (L10), so the harness's hypothesized edge (the grill) is untested. The ship-gate for calling
  KataHarness validated is an A/B where Arm A plans via `kata-grill`→`kata-design-doc`→`kata-plan` for real
  vs a GSD-planned baseline. Until then, v0.1 is "experimental, execution-half-proven."
- **D17 — Operating modes are named Essential / Standard / Advanced.** *Why:* convey value, not cheapness
  ("cost" rejected); "Master" rejected for the master/slave connotation. All three are one-shot; Standard/
  Advanced raise quality. See `docs/MODES-DESIGN.md`.
- **D18 — Consistency is the harness's north star.** Same mode → comparable, reproducible output. "Without
  consistency it is nothing." Everything in the modes design serves this.
- **D19 — Effort is an orthogonal overlay, not a mode axis.** Model + reasoning effort (Claude `effort`) set
  independently at the bootstrap; "high effort + Essential skill set" is a valid combo.
- **D20 — Modes compose from a spine + additive modules; modules are independent + additive.** À-la-carte:
  any preset + added module (e.g. Essential + `design`). Each module declares needs/produces/slot.
- **D21 — Tiering is cost-gated, two mechanisms.** Separate per-tier skill files (max determinism — avoids the
  context-rot/overstep of one branching skill) for **high cost AND high variance** (`kata-grill`,
  `kata-review`, `kata-plan`, `kata-diagnose`); a mode-passed **depth hint** (one file) for medium skills
  (`kata-design-doc`, `kata-tdd`). The determinism premium scales with cost.
- **D22 — `kata-evaluate` is NEVER tiered — it is the conformance floor.** The uniform default-FAIL gate is
  the invariant that makes modes/variants comparable. `review` tiers (adversarial depth = discretionary);
  `evaluate` does not (conformance = constant). This is the operational core of D18.
- **D23 — `kata-tasklist` reframed** from file-locked claim → a **virtual task board** over GSD structure +
  backlog, syncing to Jira/Asana via MCP (env already has `pm-skills`/`atlassian`). Orthogonal to modes; backlog.
- **D24a — Mode is a single unified axis (CONFIRMED, was pending).** Picking a mode sets both breadth
  (active modules) and depth (the tier of each tiered skill) in one move — three named, reproducible presets
  (Essential/Standard/Advanced), not an independent tier×module matrix. *Why:* a combinatorial tier+module
  surface means two runs of the "same" mode could differ — the exact thing D18 (consistency) forbids.
  À-la-carte additions (D24c) are the pressure-release valve, not a second tier knob.
- **D24b — `kata-bootstrap` is its own pre-loop skill (CONFIRMED, was pending).** It runs *before* the loop
  and *writes* `kata.config`; `kata-orchestrate` *reads* it. Kept separate for single-responsibility, distinct
  `allowed-tools` (bootstrap needs Write+AskUserQuestion; orchestrate is the weight-5 spawn-hub), and
  independent invocability (re-bootstrap to step a branch up a tier without touching the orchestrator).
- **D24c — Bootstrap is an expressive composition ladder over a one-keystroke floor.** Four rungs:
  (1) **default → go** — the recommended mode yields a solid one-shot; the floor is never punishing.
  (2) **add modules** — à-la-carte (D20). (3) **cross-tier skill picking** — the menu surfaces skills from
  *other* tiers so a Standard run can pull in e.g. `kata-grill-advanced` for one cycle without promoting the
  whole mode. (4) **external/custom skill ingestion with a declared slot** — name a skill to fold into the
  cycle and specify *where it slots and at what point* (needs/produces/slot, the same clean interface every
  module declares, D20). The "and how" is load-bearing: ingested skills declare their DAG slot so the
  orchestrator knows where to run them. *Why:* expressiveness for power users without sacrificing the
  pick-default-and-go floor or the reproducibility of `kata.config`.
- **D25 — Standard is the DEFAULT mode** (pick-nothing-and-go). The bootstrap pre-selects Standard; it is
  also `kata-orchestrate`'s **fallback tier when `kata.config` is absent/silent** (e.g. orchestrate run
  directly without bootstrap → `[[kata-grill]]` resolves to `kata-grill-standard`). *Why:* the floor must be
  a *nice* one-shot (user) — Standard = production-reasonable. **Essential is a deliberate cost downshift;
  Advanced a deliberate upshift.** (Refines the earlier "floor leans Essential" assumption — floor = Standard.)
- **D26 — Tier-family layout = peer tier-skills + a shared rubric resource; the bare family name is a
  tier-agnostic alias (CONFIRMED, "Option A").** `skills/<cat>/kata-<verb>/RUBRIC.md` holds the tier-invariant
  method (no `SKILL.md` → not invocable); `kata-<verb>-<tier>/SKILL.md` are thin peers carrying ONLY their
  depth/breadth/stopping knob + a pointer to the rubric. The **bare `[[kata-<verb>]]` wikilink = the family**
  (tier-agnostic); `kata-orchestrate` resolves family→concrete tier via `kata.config` (fallback Standard,
  D25). *Why:* DRY-by-pointer with zero cross-tier bleed (D21), keeps every existing wikilink valid, and the
  rubric move *is* the grill efficiency refactor. Families: grill/review/plan = 3 tiers; diagnose = 2
  (`-light`/`-full`). **Spec A is split A1 (foundations) → A2 (tier families) → A3 (bootstrap+wiring)**, each
  shippable; `kata-review` (D15) at each plan's end.
- **D27 — A skill-conformance validator (`tools/`, Python/uv) is the default-FAIL gate for the modes work.**
  Maintainer tooling, NOT part of the shipped agnostic skill core (agnosticism governs skill *content*, not
  our own dev tooling) — skills stay pure markdown. Checks: required frontmatter incl. `cost-weight`,
  `name`==dir, README-index sync, tier-family membership, `[[wikilink]]`/rubric-pointer resolution
  (family aliases resolve to a folder, not a SKILL). Dogfoods spine #4.
- **D28 — Frontmatter is the machine source of truth; the README index is the generated catalog + public
  landing page (CONFIRMED).** The validator regenerates the README's mechanical columns
  (version/category/status/cost-weight) from frontmatter; the "Use" prose + suite version/status are
  hand-authored. *Why:* kills the dual-maintenance drift class; the README's real value post-spin-off is as
  the GitHub front door / human discovery surface, not the machine truth. Supersedes the legacy STANDARDS §3
  "README is the source of truth" line.
- **D29 — Dependency pre-flight is a mandatory spine phase (NEW REQUIREMENT; architecture recommended,
  confirming).** A long-running closed loop must NEVER stall mid-flight on a missing tool/library/MCP/OSS
  repo/design-template/runtime/doc-capability. The grill+plan must **enumerate every external dependency**,
  record it in a **Dependency Manifest** (name · type · version · purpose · install cmd · **verify cmd** ·
  source/trust), and a **pre-flight gate pre-stages them — human-approved, then installed and verified —
  BEFORE the loop launches.** Default-FAIL: the loop does not start until every declared dep verifies green.
  **Spine, never tiered** (like `kata-evaluate` — missing deps break any mode; it's a consistency floor).
  **Security posture (user's domain):** never auto-install — enumerate → present with source/trust →
  human-approve → install → verify → record (supply-chain hygiene); pre-staging is also a determinism win
  ([[LESSONS-LEARNED]] L1). New loop phase **PRE-FLIGHT** between FREEZE and EXECUTE. *Recommended shape
  (confirming):* responsibilities distributed to `kata-grill` (enumerate) + `kata-design-doc`/`kata-plan`
  (manifest) + a **new `kata-preflight` skill** (approve/install/verify gate) + a `kata-orchestrate`
  precondition (refuse to dispatch until pre-flight cleared). Manifest schema → `protocol/dependencies.md`
  (an A1 foundations deliverable alongside `kata.config`).
- **D30 — KataHarness is clean-room independent of the user's AWS-internal harness/PM suite; its tracking
  surfaces are modular trackers with open pointers, not a PM system.** The user is building a related
  agent-harness + full project-management overlay for AWS-internal use (their design there). KataHarness is
  the **independent, general, non-AWS** version — **no AWS-internal IP is imported**; build only from
  general/public best practice + the user's general direction. The installed-library registry (D-registry),
  the `kata-tasklist` board (D23), and any PM-ish surface are designed as **modular trackers exposing
  documented `protocol/` extension points** so an *optional* external PM overlay (theirs or otherwise) can
  attach later via D20's independent-additive-module contract — the **core never depends on a PM layer**.
  This version stays the lite, general substrate. *Why:* protects the user's AWS-IP separation; keeps the
  public project original; preserves a clean seam for an optional heavier overlay without coupling.
- **D-multisession — Multi-session/tmux is NOT a core dependency; the board/state/worktree protocol already
  IS multi-session support; the spawn/launch mechanism is an adapter binding.** Orchestrator/executor/
  validator-in-separate-contexts works via the append-only board + single-writer state + worktree isolation
  (already core, agnostic, L3). The *launcher* (subagents vs panes) is tool-specific: Claude adapter = the
  `Agent` tool (subagents, one session — the user's stated preference over "many windows"); a future
  **session-pool/multiplexer launcher adapter** (backlog, v0.3+) targets the platform terminal (Windows
  Terminal/wezterm on the user's Win11 box; tmux on Linux — **tmux is Unix-only, wrong primitive to hard-code**).
- **D-registry — Installed-library registry: machine-global, reference-counted, record-and-recommend (NEVER
  auto-uninstall).** `kata-preflight` appends every install to a machine-global ledger (`~/.kata/
  installed-registry.json`): package · version · source · **scope (global|project-local)** · requesting
  project/branch · timestamp · used/unused. A cleanup-report mode **reference-counts across projects**
  (safe-to-remove only if no other project's manifest still needs it) and recommends; the human executes.
  Manifest gains **`scope`** and **`classification: build-time|runtime`** fields (A1) — runtime deps get
  bundled into the artifact (a packaging task) → their global base copy becomes a cleanup candidate;
  build-time deps are removable post-run. *Why:* leave-no-trace hygiene; cross-project view makes cleanup
  *safe*; no destructive autonomous env changes (consistent with D29). Hooks (fields + ledger) land now;
  the reference-counted cleanup report is a fast-follow within Spec D.
- **D31 — Frontmatter schema v2 (audited live vs agentskills.io + Anthropic + Obsidian 1.9).** See
  `.planning/specs/modes-A1-foundations/FRONTMATTER-AUDIT.md`. (a) **Governance fields stay top-level**
  (Obsidian #1 priority; spec-tolerated) — no `metadata:` nesting, no duplication. (b) **`allowed-tools` keeps
  the YAML list** for the Claude v0.1 adapter; the adapter normalizes to the open standard's space-separated
  string. (c) **License = Apache-2.0** (patent grant, sensible for a framework) — adds the spec `license`
  field to every skill AND closes the open license-selection item. (d) **Adopt `context: fork` as the
  Claude-adapter evaluator binding + reserve `hooks`** for future automation (docs-only). Plus: add spec
  `compatibility` (env hint / pre-flight), enforce the spec `name` regex + `description` ≤1024 in the
  validator (spec-compliance by construction), and restructure `tags` into a `kata/...` automation namespace.
  *Why:* fixes three real gaps (`license`, `compatibility`, name/description validation), maximizes Obsidian
  compatibility, and scaffolds future automation — locked before A1 execution because the A1 validator
  enforces this schema.
- **D32 — Post-loop build report (`kata-report`), lite-synthesis not comprehension.** A handoff-phase skill
  that compiles artifacts the loop ALREADY emitted (DESIGN, plan DAG, decision ledger, dependency manifest,
  diffs, `kata-evaluate`/`kata-review` verdicts, drift ledger, gate numbers) into a durable Obsidian-native
  `BUILD-REPORT.md`: TL;DR · LOCKED decisions · files changed · a **Mermaid structural diagram** of our own
  build DAG/structure · evidence (green/drift=0) · next/open. (Renamed from "graphify-lite" to avoid collision
  with the external Graphify code-navigation tool — see the optional-navigation-capability backlog item.) **Explicit non-goal: from-scratch code comprehension**
  (synthesize known artifacts, never re-derive — that's why it's cheap and can't hallucinate). Distinct from
  `kata-handoff` by audience (report = "what was done" for the human; handoff = "how to continue"); feeds
  `kata-improve`; a natural open pointer for the future PM overlay (D30); any aesthetic polish belongs to the
  `design` module, not here. Baseline report is near-free → leans always-on/spine-light, visuals tier up.
  **Backlog — does NOT block A1** (no foundation depends on it).
- **D33 — Structural invariants are never tiered; tiers vary depth only.** Surfaced by the A2 adversarial
  review (REVIEW.md H2/H3): the cheap tiers had accidentally dropped *spine invariants* — `kata-grill-essential`
  went silent on the "don't grade your own convergence" backstop (the L8 anti-bias), and `kata-plan-essential`
  dropped the `action` field that quotes LOCKED decisions verbatim (the no-drift line). **Rule:** a tier may
  reduce depth/breadth/rigor, but may NOT relax a structural invariant — **no-self-certification (L8),
  no-drift (verbatim LOCKED-decision quoting), default-FAIL, and DRY-by-pointer hold at EVERY tier.** This
  generalizes D22 (kata-evaluate never tiered) from one skill to a principle. Essential still runs the
  convergence gate (scoped to its branches, cheapest review tier); essential plans still carry `action` with
  verbatim decisions. *Why:* consistency is the north star (D18) — if a cheap tier can silently skip the
  anti-drift/anti-bias machinery, the harness's core guarantee evaporates at exactly the tier most likely to
  ship fast.
- **D24d — `kata-orchestrate` stays a single config-driven skill, NOT three per-mode variants (CONFIRMED;
  reaffirms D21).** The tiered skills (grill/review/plan/diagnose) are forked because they carry
  judgment-heavy *branching prose* that risks context-rot/overstep across tiers; orchestrate is a
  *dispatcher* — what varies by mode (which skills/tiers, how many bake-off variants N) is a **data lookup
  from `kata.config`**, not a prose branch. Three orchestrators = three near-identical copies of the
  spawn/board/worktree/merge plumbing (duplicated substance) and three subtly different execution engines,
  which destroys cross-mode comparability. *Why:* orchestrate + `kata-evaluate` are the two spine invariants
  that make modes comparable to each other (D18/D22); they must stay singular.
- **D34 — Run-shapes are named presets ON TOP OF the mode axis, not a new axis. (GB1)** Each run-shape
  (individual / batch / version-up / advanced) is a bundle `(mode, modules[], config-defaults)` that
  pre-seeds the D24c composition ladder; the user can still drill down from any preset. **Rejected:**
  run-shapes as a competing second top-level axis. Keeps the frozen D24a unified axis intact; a preset is
  data, not a code branch.
- **D35 — "Batch" preset = bakeoff (best-of-N), NOT a task-queue. (GB2)** Batch maps to the `bakeoff`
  module (N variants → judge → pick → refine up, Spec B). **Rejected:** a multi-task scheduling queue
  (new machinery, competes with the single-frozen-plan premise). Provenance: user — "Bake off is what I
  meant."
- **D36 — "Review of existing project" run-shape = version-up (Spec C), NOT a read-only audit. (GB3)**
  The preset = one-shot feature-addition to a live project without regressing the rest (the
  Improvement-Kata on existing repos). **Rejected:** read-only `kata-review` audit. Provenance: user —
  "Versioning up a project with [a] feature and being able to one-shot the feature addition without breaking
  other aspects." Matches Spec C.
- **D37 — Bakeoff composes with version-up; modules and run-shapes are orthogonal. (GB4)** A baked-off
  version-up = spawn N candidate feature-implementations, evaluate each for adds-the-feature AND
  regresses-nothing, pick the winner. Bakeoff is a module (how many variants); run-shape is the target
  (greenfield vs existing). Orthogonality → composability; reinforces GB1.
- **D38 — A3 / A4 cut: version-up execution is A4; bootstrap is version-up-aware now. (GB5)** A3 delivers
  bootstrap + readiness + greenfield wiring + version-up *fully configurable* (writes a correct version-up
  `kata.config`, routes to A4 bundle). A4 = version-up execution bundle — `kata-graph` ingestion engine +
  context-aware plan→build→regression-gate on a real existing repo. A4 absorbs the old standalone Spec C
  and is committed next-in-line, not deferred. Greenfield vs version-up differ in only two places:
  `kata-graph` (ingestion) and existing-file-aware planning + baseline-green regression contract; everything
  else is reused as-is.
- **D39 — `kata-graph` = pre-processing structural map; version-up's A4 ingestion engine. (GB6)** New skill
  — builds a compact symbol/dependency map of an existing codebase so grill/plan/orchestrate ingest large
  repos cheaply. Default backend = agnostic grep/glob/Read; accelerated AST/MCP backend stays an optional
  adapter binding (spine #3 — core never hard-deps on Graphify). Promoted from deferred-optional → active
  A4 component; accelerated backend stays optional. Supersedes working name `kata-map`.
- **D40 — `kata-understand` = post-processing comprehension map of newly-built codebases; backlog. (GB7)**
  Desired-state capability — helps the user understand/navigate what KataHarness created. **Distinct from
  `kata-report` (D32):** report synthesizes the build log; `kata-understand` provides from-scratch
  comprehension. Scope: own later spec or module, post-v0.1, not in A3/A4.
  **↑ SUPERSEDED by D89 (2026-06-20):** `kata-understand` is now BUILT (Phase 2 of the Greater Loop) as
  `modules/closeout/kata-understand/` — opt-in, graph-backed (F2 runtime), git/diff fallback, writes
  `.kata/understand.md`. The "backlog / post-v0.1 / own later spec" framing here (and the deferred framing in
  D54/D55) no longer holds; the capability shipped as part of closeout.
- **D41 — When designing `kata-graph` / `kata-understand`, evaluate OSS repo-mappers and bake in only the
  necessary stripped-down steps. (GB8)** Evaluate against: Graphify, aider repo-map/tree-sitter, repomix,
  gitingest, code2prompt, ctags, DeepWiki-class comprehension tools. Extract minimal needed steps; do not
  over-port.
- **D42 — `kata-defer`: in-loop deferral capture skill (new optional module). (GB9)** During a run, any
  out-of-scope item is captured to a run-scoped `DEFERRED.md` instead of being silently dropped or
  scope-crept into the frozen plan. Artifact compiled at HANDOFF; feeds the backlog / `kata-improve` /
  post-processing. Structural complement to the no-drift spine (#1/#2) — parks tempting additions
  sustainably. Needs: none; produces: `DEFERRED.md`.
- **D43 — `kata-graph`, `kata-understand`, and `kata-defer` are optional modules, not spine. (GB10)**
  All three are additive, independent, selectable from any mode (`kata/module/<m>`); each declares
  needs/produces/slot. The version-up preset bundles `kata-graph` by default; otherwise à-la-carte.
  Advanced default-bundle membership: TBD when mode default-bundles are defined.
- **D44 — Readiness eval is a separate light skill `kata-readiness`, invoked by bootstrap. (GB11)**
  Factored out of bootstrap for reuse: ≥3 callers (re-entrant bootstrap every run, orchestrate
  Standard-fallback D25, pre-flight D29). Two scopes: harness-health (validator green / skills present /
  tools on PATH) + target-readiness (git repo + clean tree, AGENTS/CONTEXT present, deps installable,
  existing `kata.config` → re-entrant detection). Keeps bootstrap lean.
- **D45 — Config validation = fail-closed load-guard in `kata-orchestrate` on READ, not a bootstrap
  phase. (GB12)** Bootstrap writes `kata.config` by construction — a separate post-write validation step
  is redundant bloat. `kata-orchestrate` guards on read: fail-closed if `kata.config` is malformed or
  references a non-existent tier/module/effort. The real risk is a stale/hand-edited/older-version config
  on a re-entrant run, which only a consumer-side load-guard catches. Consistent with default-FAIL spine.
- **D46 — Bootstrap interview uses progressive disclosure: surface only run-shape-relevant config fields.
  (GB13)** Ask only the `kata.config` fields relevant to the chosen run-shape; the default→go floor stays
  fast, advanced fields appear only when the path needs them. Provenance: user — "Only ones relevant to
  the run shape."
- **D47 — tree-sitter is the hard floor for `kata-graph`; grep-only is a labeled "reduced" fallback for
  greenfield/exploration only; version-up BLOCKs at readiness if tree-sitter is absent. (GB1/GB1.1)**
  "Agnostic" = tool-agnostic (Claude/Codex/Kiro), NOT dependency-free. tree-sitter is local, no API,
  `uv`-installable → a benign build-time dep in the D29 pre-flight manifest. Requiring it does not violate
  the agnostic core. A grep-only map emits "reduced — no AST" explicitly; it is never the default. Version-up
  needs AST-ranked seeding + blast-radius — a grep-only map is structurally insufficient, so readiness BLOCKs
  rather than serving an inert partial capability. *Rejected:* grep-default with tree-sitter as a pure
  optional accelerator (can't rank by reference-importance → defeats token-optimization premise).
  *Provenance:* aider, Graphify, Understand-Anything all stand on tree-sitter; proven primitive.
  *See* `.planning/specs/modes-A4-version-up/` (GRILL-LEDGER GB1/GB1.1, DESIGN L1).
- **D48 — `kata.graph.json` is the anti-chimera contract; byte-level schema locked. (GB2/GB2.1/GB2.2/GB2.4)**
  Full schema in `protocol/graph.md`. Nodes: `file` (`id`=path, `kind:"file"`, `path`, `hash`, `rank`[REQ],
  `lang`[OPT], `community`[OPT]) and `symbol` (`id`=`path::name[~N]`, `kind:"symbol"`, `path`, `name`,
  `symKind`∈{function,class,method,interface,type,constant,other}, `span`=[startLine,endLine] 1-indexed
  inclusive[REQ], `hash`, `rank`[REQ], `signature`[OPT], `community`[OPT]). Edges: `src`, `dst`,
  `kind`∈{def,ref,call,import}, `weight`[REQ, default 1.0]. `def` = file→symbol; `ref`/`call` = symbol→symbol
  (`call` oracle-only, may be absent); `import` = file→file (symbol-level import is oracle-only). `meta`:
  `{backend, repoHash, generatedAt}` — **no `seedSymbols`** (see D49). Floor MUST populate def+ref (+import
  best-effort). Ids are line-independent (span is a property) → incremental-cache-safe. Same-name symbols in
  one file disambiguated by `~N` ordinal (def order). *Rejected:* line-in-id (cache churn); test-coverage
  edges (full-suite-green floor makes them unneeded — anti-bloat; user confirmed). *Provenance:* user
  confirmed the contract + "keep test edges out." *See* `.planning/specs/modes-A4-version-up/`
  (GRILL-LEDGER GB2/GB2.1–GB2.4, DESIGN L2).
- **D49 — `kata.graph.json` is feature-agnostic and content-hash cached; seeding + blast-radius are use-time
  projections, never cached. (GB8/GB8.1/GB8.2/GB2.3)** `seedSymbols` is a per-run projection input (tokenize
  feature description → identifier-like tokens → case-insensitive match vs symbol `name` → ×10 PageRank boost;
  user-named files also boosted) — never stored in the cached artifact (fixes the GB2↔GB8 contradiction).
  The **digest** = top-rank signatures selected until a `[TUNABLE: budget=3000]`-token estimate (chars/4
  heuristic; no host-specific tokenizer) is hit — selection, not post-truncation. Blast-radius = planner
  inverting the forward `ref∪call` edge list; no reverse-index in the contract. No ×8 no-scope expansion
  (version-up always has a feature in scope). *Rejected:* baking the feature seed into the cached artifact
  (contradicts agnostic cache). *Provenance:* user — "go with your rec" (agnostic cached graph · ~3k default
  · blast-radius in the planner). *See* `.planning/specs/modes-A4-version-up/`
  (GRILL-LEDGER GB8/GB8.1/GB8.2/GB2.3, DESIGN L3).
- **D50 — version-up footprint ownership is bounded to modified-files ∪ depth-1 reverse-dependents; escalate
  predicate is decidable. (GB9/GB9.1/GB9.2)** Grill Phase 0 invokes `kata-graph` when `target.kind ==
  existing` → injects the feature-seeded digest into grill + plan so design is resolved against the existing
  architecture. `kata-plan` scopes disjoint file-ownership = **footprint = modified-files (from frozen DESIGN)
  ∪ `[TUNABLE: marginDepth=1]`-hop reverse-dependents** over ref∪call; files outside are off-limits, owned by
  no task. Regression contract: orchestrate precond #2 records baseline via `target.baselineGate` (full suite
  green at fork); version-up `kata-evaluate` = baseline suite still green + new feature tests green,
  default-FAIL — **no new evaluator** (reuses rubric #2/#6). **Escalate predicate (decidable):** escalate IFF
  completing the owned task's acceptance test requires a write to an unowned file; everything else → `kata-defer`
  (`DEFERRED.md`). Baseline regressions from unowned files caught by the full-suite gate → deliberate re-scope
  at gate-time by orchestrator, never a worker's silent expansion. *Rejected:* transitive-closure ownership
  margin (owns half the repo, breaks disjoint partition). *Provenance:* user confirmed escalate-not-silent-
  expand "as long as there are protections against overuse." *See* `.planning/specs/modes-A4-version-up/`
  (GRILL-LEDGER GB9/GB9.1/GB9.2, DESIGN L4).
- **D51 — Rolling DAG-frontier dispatch supersedes wave-gated dispatch; async escalation is the harness-wide
  protocol. (GB9.3/GB9.3-rev)** A task is dispatchable iff (all `depends_on` integrated) ∧ (owned files
  disjoint from all in-flight tasks), regardless of original wave. Waves become a derived view, not a hard gate.
  Supersedes the current synchronous per-wave loop + synchronous escalation paragraph in
  `skills/coordinate/kata-orchestrate/SKILL.md`. **Async escalation:** park the escalating task + its
  DAG-dependents; keep dispatching the frontier; checkpoint each completion in integration order (linear
  history); **hard-wait for the human IFF frontier empty ∧ open escalations remain.** Frontier-blocked IS the
  criticality test (decidable; operationalizes "truly critical"). Overuse protections: (1) defer-vs-escalate
  split (GB9.2/D50, the main lever); (2) generous plan-time scoping — blast-radius pre-owns the common caller-
  update case (escalation frequency is a plan-quality metric, not a runtime constant); (3) escalation telemetry
  in the drift ledger (crossing threshold = "plan under-scoped" → re-grill, not normal). *Provenance:* user —
  "when we escalate make sure we aren't interrupting unfinished processes … continue to execute until
  necessary." *See* `.planning/specs/modes-A4-version-up/` (GRILL-LEDGER GB9.3/GB9.3-rev, DESIGN L5).
- **D52 — The structured escalation payload is its OWN contract, separate from the board. (GB9.4)** Board
  stays one-line (append-only, `protocol/board.md` L3 invariant): worker appends `ESCALATE | <task-id> |
  <summary>` (a pointer). Structured payload = separate artifact `.kata/escalations/<task-id>.json` with schema
  in `protocol/escalation.md`: `{taskId, kind: "orchestrator-resolvable"|"human-required", decisionNeeded,
  optionsConsidered[], agentRecommendation, rationale, lockedDecisionInTension?, costOfWaiting,
  costOfProceeding, status: "open"|"resolved", resolution?}`. Producer = escalating worker; orchestrator
  reads/classifies/routes; resolver writes `status→resolved`; engram (D56/future) learns from resolved payloads.
  Structured = fast human decision + forward-compatible engram seam + resumable. *Rejected:* JSON in the
  one-line board message (breaks the L3 append-only invariant). *Provenance:* GB9.4 — "problem: board locks
  to a single one-line message; fused payload can't live there." *See* `.planning/specs/modes-A4-version-up/`
  (GRILL-LEDGER GB9.4, DESIGN L5).
- **D53 — `kata-graph` is ONE optional module (`kata/module/graph`), name-by-job, compose-not-fork; pluggable
  backend. (GB6/GB10 + D39 naming/D43 module)** One skill, pluggable backend tiers: grep-glob-Read (reduced
  fallback) → tree-sitter floor (default) → Graphify-MCP oracle (accelerated). Each backend either fully
  produces the `kata.graph.json` contract or is not bound — no backend leaks its own format upward. No forked
  skills per backend. External skills (Graphify-MCP) are composed via the MCP adapter binding; never
  reimplemented or fork-spliced. Name = `kata-graph` (the job: build the structural graph); never
  `kata-pagerank` or `kata-map`. `source:` frontmatter names aider (MIT) + Graphify (MIT) per spine #12.
  Bundled-by-default by the version-up run-shape preset; à-la-carte otherwise (D20/D43). *Provenance:*
  "no chimera" tenet + GB6 (bootstrap asks KG question) + GB10 (engram composability). *See*
  `.planning/specs/modes-A4-version-up/` (GRILL-LEDGER GB6/GB10 + RESEARCH, DESIGN L6).
- **D54 — The Obsidian KG story ships as its OWN next spec under kata-understand; A4 does not add inert hooks.
  (GB3/GB7)** A4 ships version-up execution + the `kata.graph.json` contract (the durable substrate). The
  complete Obsidian KG story — emit (contract→vault: node→note, edge→`[[wikilink]]`, community/kind→`#tag`),
  ingest (vault→contract: note→node, wikilink→edge, folds PortaVault in), bootstrap `knowledgeGraph` config,
  pluggable `frontmatterProfile` (base + dataview/breadcrumbs/juggl/custom plugin layers), and the
  comprehension/onboarding layer — ships as a **whole**, under kata-understand, when kata-understand exists.
  A4 adds NO `knowledgeGraph` config field and NO inert hooks. *Rejected:* a partial emit bolted into A4
  (creates an ownership seam — "owned by kata-understand" but built before kata-understand exists = a chimera
  at the spec level). Anti-chimera honored at the spec boundary. PortaVault must exist before emit can target
  it. *Provenance:* user — "go with your gut recommendation." *See* `.planning/specs/modes-A4-version-up/`
  (GRILL-LEDGER GB3/GB7, DESIGN §2 out-of-scope block).
- **D55 — `kata-understand` base capability = Understand-Anything; own later spec. (RESEARCH §5b)**
  `kata-understand` (D40) targets from-scratch comprehension of a newly-built codebase. The researched
  primitive is the Understand-Anything framework (grounded in tree-sitter, incremental, multi-language) —
  the same floor as `kata-graph`, making the two skills a coherent pair (shared tree-sitter dep, shared
  `kata.graph.json` substrate). `kata-understand` owns the Obsidian KG emit/ingest projection (D54) and the
  future `kata-engram` feed. Distinct from `kata-report` (D32, build-log synthesis) and from `kata-graph`
  (pre-processing structural map → token-optimized planning input). Backlog; post-v0.1; own spec.
  *See* `.planning/specs/modes-A4-version-up/` (RESEARCH §5b, GRILL-LEDGER GB7).
- **D56 — Engram-mediated escalation is a future harness-wide phase; gated on PortaVault + cognitive-fingerprint
  synthesis. (GB10)** Every human-in-the-loop escalation should eventually route through the engram / cognitive
  fingerprint: (a) consult the engram first — if the user's known patterns resolve it, auto-resolve + log; only
  novel decisions reach the human; (b) feed every human resolution back into the engram so the next identical
  escalation auto-resolves. Net: as the engram matures, human interrupts asymptotically decrease → the
  long-running promise strengthens over time. **Not wired in A4** — the A4 async escalation protocol (D51/D52)
  is designed with a forward-compatible seam (structured payloads feed the engram when ready). Gated on:
  PortaVault installed + cognitive-fingerprint synthesis built (from `kata-engram`, D9; ties to
  [[cognitive-twin-architecture]], [[project-framework]] / kiban, [[project-kagami]]). *Provenance:* user —
  "these escalations no matter where they are should take the engram into consideration … if the user has to
  enter a human-in-the-loop escalation it should feed into our engram … add it as a future phase after
  PortaVault + cognitive fingerprint synthesis." *See* `.planning/specs/modes-A4-version-up/`
  (GRILL-LEDGER GB10, DESIGN §2 out-of-scope block).
- **D57 — CPP is decoupled: no longer the test medium or the v0.1 consumer; the D16 A/B targets small,
  one-shottable greenfield projects in a dedicated test directory.** Historical records (D10/D13/D14, L9/L10,
  REVIEW-v0.1, TEST-PLAN v1) stand as history; skill `source:` provenance keeps attributing `cpp-*` origins
  (D12). *Why:* user direction 2026-06-10. Small repeated one-shots give multiple paired measurements (better
  signal than one big task), drop the cross-project entanglement, and match the harness's actual purpose
  (one-shotting). Supersedes the CPP-target half of D14 and D10's "CPP consumes at v0.1" consumption path;
  D14's surviving principles (model constant across arms, fresh context per arm, honest-GSD baseline — no
  strawman) carry into the D16 v2 design unchanged.
- **D58 — PortaVault is now PokeVault; PokeVault is KataHarness's install/test home.** The vault gating
  D54/D56 — formerly "PortaVault" — is the **PokeVault** vault, local at
  `C:\Users\taurr_nvs748q\PokeVault\PokeVault`, with `toolkit/agent-sops/` present (verified 2026-06-10).
  KataHarness installs into and is field-tested from this vault when ready (under `toolkit/`). The D54
  "PortaVault must exist first" gate is **SATISFIED**. Forward references renamed; history unmodified.
- **D59 — Model routing: deep/judgment work moves from Opus to Fable 5; Sonnet stays the lightweight
  workhorse.** Building KataHarness (research, grilling, planning, design, orchestration, adversarial
  review) → **Claude Fable 5** (`claude-fable-5` — Anthropic's most capable model, the Mythos-class tier
  above Opus). Mechanical/lightweight work (workers, encode/refactor, evaluators) → **Sonnet**, unchanged.
  Skill frontmatter `model: opus` pins → `model: fable` (the Claude-adapter binding; the agnostic body is
  untouched). *Why:* user direction 2026-06-11 — Fable 5 supersedes Opus as the deep-task model.
  **Supersedes the Opus half of D13's routing**; D13's surviving principle — test arms run the cheaper
  workhorse model, held constant, so the harness lift isn't masked — carries forward unchanged (the D16
  arms stay Sonnet, per D14/D57). History (D13 text, L9/L10, REVIEW files, frozen specs) unmodified.

<!-- loop-cognition spec (FROZEN 2026-06-18; freeze-gate audit HOLD→SHIP). Ledger:
     .planning/specs/loop-cognition/{GRILL-LEDGER,RESEARCH,DESIGN}.md -->
- **D60 — loop-cognition: one umbrella spec, three loop enhancements (RS research subagent · AO agent
  orientation · ML managed learning), spine-compatible. (LC-GB1)** Shared substrate = the grounding gate +
  `kata-graph`. No-drift (D1) holds within a run; new knowledge influences the build only past the grounding
  gate; learning persists only through a human gate. The spec name is NOT a category — skills are category-split
  (research→plan, orient→handoff, promote→meta; engram/second-brain → `cognition/`'s first tenant). *Provenance:*
  user 2026-06-18; freeze-gate audit MF2.
- **D61 — ONE grounding gate, two callers; a structural invariant. (LC-GB2)** An "injected-knowledge"
  assessment mode of `kata-evaluate`/`kata-review` grades both RS findings and ML candidate skills for
  grounding + drift + adversarial soundness. **Never tiered, never bypassed (D33)** — even at full engram
  autonomy. The counter-pressure to the research subagent's "negative pressure."
- **D62 — `kata-research` is escalation-routed, fresh-context, no-write. (RS-GB1/2/3)** Worker → D52 escalation
  payload → orchestrator dispatches `kata-research` (no Write) → findings → D61 gate → orchestrator folds
  *grounded* findings via a **deliberate re-plan baked as a superseding decision**, or rejects; can't ground →
  escalate to human. `category: plan`. *Rejected:* worker-direct research (silent drift, spine #1). Never silent injection.
- **D63 — `kata-orient` assembles launch orientation: orchestrator-owned, three-tier, prime-frame-budgeted.
  (AO-GB1/2/3)** Tiers **stable→context→volatile** (Hermes `prompt_builder`). Vertical rollup = root invariants
  + nearest module file (2026 nearest-along-path standard); lateral = `kata-graph`-derived adjacency **pointers**,
  lazy (rot-proof, token-safe); capped to the prime frame (SC-GB7). Orchestrate gains **hooks only** (D24d
  intact). Contract → `protocol/orientation.md`; `kata-orient` = the read-side mirror of `kata-handoff`.
- **D64 — managed learning: two-stage skill lifecycle, matched-but-marked taxonomy, vault-hosted +
  configurable. (LC-GB3/5/7)** Stage 1 candidate (`experimental`/`scope:agent`, sandboxed) past the D61
  grounding gate; Stage 2 **end-of-session human promotion gate** (`kata-promote`) → `experimental→stable` +
  scope bump. Same taxonomy + discriminators (`provenance:agent-distilled`, `scope`, tag `kata/origin/agent`,
  ≤60-char `summary`). Home install-seeded + first-run-configured (`agentSkills.dir`):
  `toolkit/skills/candidates/` → `toolkit/skills/<category>/` (preserve `name==dir`, D27). *Rejected:* Hermes'
  no-gate instant-universal model (uncontrolled positive feedback — wrong for a one-shot harness).
- **D65 — progressive promotion autonomy = maturity ∧ config AND-gate; grounding never bypassed. (LC-GB4)**
  `engram.autonomy: always-human | assisted | auto-when-confident`, default **always-human** (D25-safe),
  per-seam; **skill-promotion is the first seam.** Autonomy fires only when `opted-in ∧ fingerprint-mature ∧
  high-confidence ∧ precedented`; novel/low-confidence/LOCKED-adjacent always stop the human (C2/C4). **The
  engram replaces human judgment, never the grounding gate (D61/D33).** Reuses `auto-continue-while-green` +
  engram C2/C4/C5/C6.
- **D66 — second-brain LEARN feed; ONE wiki-synthesis output contract; the feed is an engram PREREQUISITE.
  (LC-GB6 + RESEARCH §5/§7)** The loop mines decision artifacts into **Karpathy-LLM-Wiki-pattern synthesis
  pages** (markdown, frontmatter taxonomy, cross-linked, `produced-by: loop|wiki|agent`), emitted via the
  agnostic LEARN contract, redaction-gated (C3). Two producers, **one schema** (a section of
  `protocol/engram.md`; the loop contract LEADS the immature vault). **Building the feed is the prerequisite for
  the engram CONSULT (D9), not gated by it** — this partially reorders the engram backlog. *Confirmed:*
  "llm-wiki" = Karpathy's LLM Wiki pattern (user 2026-06-18).
- **D67 — unified loop map + self-handoff structured preservation. (LC-GB9)** `protocol/handoff.md` carries the
  loop map (every agent × handoff edge × owning skill — no ownerless edges). `kata-selfhandoff` EXTEND with
  Hermes' protected head+tail + tool-call/response pairing guardrail + a **never-summarized invariant block
  `{frozen-plan ref, goals, open decisions, open escalations}`** — converting Hermes' "plan emerges organically
  (lossy)" vulnerability into our structural guarantee. **D33 invariant.**
- **D68 — Path 2 sequencing: D16-first holds; only the β LEARN-only feed builds ∥ D16. (LC-GB8)** β =
  observe-and-emit, **zero CONSULT**, redaction-gated — drift into the D16 A/B is structurally impossible
  (LEARN-only ⇒ no read-back path; arms stay constant, D14/D57). Everything else (RS, AO, ML distillation +
  `kata-promote`, the D61 injected-knowledge mode, CONSULT, autonomy) builds **after D16**. *Rejected:* build
  all pre-D16 (the KG-first rework exposure). Closes the standing D16-first confirmation.
- **D69 — Hermes Agent (Nous) bake-off verdict: borrow mechanisms, keep our gates. (RESEARCH §3)** Adopt
  Hermes' closed-loop distillation, protected head+tail compaction, tiered prompt assembly, `.usage.json`-style
  telemetry, stale→archive curation, ≤60-char description discipline; **reject** its no-gate instant-universal
  skills and opaque (Honcho) user model. Our differentiator: Hermes' learning loop **gated by default-FAIL +
  human promotion + artifact-grounded fingerprint.** Applies to the sister **work-loop** project too.
  *Provenance:* user-requested deep research + bake-off 2026-06-18.

<!-- D16 resolution + Priming-and-Grill architecture (2026-06-18). See PILOT-NOTES.md, L11,
     .planning/specs/d16-planning-varied-ab/. -->
- **D70 — D16 retired as an autonomous grill-vs-baseline RCT; v0.1 is NOT gated on it. (2026-06-18)** Two
  counted attempts (easy pilot + a hardened pair) plus a structural argument show the autonomous,
  deterministic-gate A/B **cannot isolate the grill's value:** (a) a fully-specified task — any difficulty — is
  built correctly by a capable Sonnet agent under either method (**4/4 held-out gate passes**, ~0 on every
  metric); (b) the grill's engine is *interrogating the human*, which is OFF in autonomous mode (Arm A:
  "no ambiguities required human resolution"); (c) a deterministic gate cannot encode genuine ambiguity.
  Empirical confirmation of L8/L10. What the runs DID establish: **autonomous reliability is demonstrated**
  (both methods one-shot correct, gated, lint-clean builds). Halting the 18-run fan-out is **instrument-
  invalidity on a near-tie** (not outcome-driven → not p-hacking). Corpus/gates/builds kept as the reliability
  demonstration. Supersedes the "planning-varied A/B" framing (D16/TEST-PLAN); **v0.1 validation is re-scoped
  per D71.** *Provenance:* runs + user 2026-06-18; see PILOT-NOTES.md, L11.
- **D71 — Priming-and-Grill: grill is an OPTIONAL human certainty layer over the priming prompt; autonomous-
  reliability is the floor. (2026-06-18)** Every project starts from a **priming prompt** (the human's original
  priming spec). **Grill = an optional, human-facing enrichment dial** — depth `skip | light | standard | full`
  (reuses the `kata-grill` A2 tier-family + a NEW skip rung; bootstrap-offered, D46; `kata-readiness` recommends
  depth from prompt richness/ambiguity). Grill interrogates the designer to resolve ambiguity and **enrich the
  priming prompt into the frozen spec**, adding alignment certainty **by construction** (NOT by benchmark — it is
  "additional certainty the loop output aligns with the designer's spec/requirements"). **Opt out / light →
  autonomous-reliability floor:** freeze the prompt and one-shot it on default-FAIL + the RS research subagent
  (in-loop ambiguity, D62) + **an assumption/ambiguity log surfaced at the gate/handoff** (`kata-defer`) so
  misalignment is caught at the boundary without grilling. **Grill ↔ RS are one spectrum:** ambiguity resolved
  up-front-with-human (grill) vs in-loop-without-human (RS); skipping grill *shifts* resolution from the former
  to the latter — it never removes it. Both coexist; grill shores up results on top of a reliable autonomous
  floor. *Provenance:* user 2026-06-18 ("keep grill, make it an option… decline/light → fall back on the Nous
  autonomous-reliability approach… grill shores up the priming prompt… logical approach to rich context, not a
  bake-off").
- **D72 — Grill output is a PRIMARY cognitive-fingerprint (engram LEARN) feed; a matured fingerprint pre-answers
  future grills. (2026-06-18)** Grill ledgers (resolved decisions + the human's choices + rationale) are a
  **primary** LEARN source for the second brain (reinforces D66; binds engram seams E4 option-biasing + E13
  convergence-gate). The virtuous cycle: as the fingerprint matures it **pre-answers** grill questions (D56
  AND-gate, default-human), so each grill both shores up the current project AND trains the engram for the next
  → human grill-effort asymptotically decreases. *Net-new vs D66:* names grill the *primary* feed + the cycle.
  *Provenance:* user 2026-06-18 ("grilling needs to feed into our cognitive fingerprinting… the agentic learning path").
- **D73 — Grill-depth `skip` is a value of `tiers["kata-grill"]`, not a separate config field. (2026-06-18 —
  D71 wiring micro-pick M1)** The Priming-and-Grill dial `skip | light | standard | full` maps to
  `tiers["kata-grill"] = skip | essential | standard | advanced` — **one source of truth**, no `grillDepth`
  field to diverge from the tier mechanism. `"skip"` means *dispatch no grill skill; freeze the priming prompt
  and engage the autonomous-reliability floor* (default-FAIL + RS [loop-cognition phase] + `kata-defer`
  assumption log); it **never** bypasses the `kata-evaluate` gate (D22/D33). `kata-orchestrate` already resolves
  `tiers[family]`; skip adds one branch there. Companion micro-picks: **M2** `kata-defer` built once with both
  the D71 assumption-log and D42 parking roles; **M3** `kata-defer` category = `handoff` (both artifacts surface
  at the gate/handoff boundary), module `kata/module/defer`. Wired in spec `priming-and-grill` (DESIGN FROZEN
  2026-06-18). *Provenance:* user-approved plan + micro-picks 2026-06-18.
- **D74 — β LEARN feed: emit-only, zero CONSULT; `engram.learnFeed.dir` is the emit target, distinct from
  `engram.backend`; the wiki-synthesis schema lives in `engram.md`. (2026-06-18 — loop-cognition β build, micro-
  picks BP1/BP2)** Built the LEARN-only second-brain feed (D66; the **primary** fingerprint feed, D72) as a
  **`kata-improve` emit-only sub-mode** (engram seam E6, run at IMPROVE/handoff — out of the one-shot budget). It
  mines DECISIONS/LESSONS/GRILL-LEDGERs/REVIEWs into **Karpathy-LLM-Wiki synthesis pages** (raw↔synthesis split,
  `produced-by: loop`, `scope:`, `[[wikilinks]]`) per a schema documented **in `protocol/engram.md`** (one
  schema, two producers — loop + vault llm-wiki; NOT a separate `wiki-synthesis.md`, BC5). **Emit-only — zero
  CONSULT** (no read-back path ⇒ cannot influence a build, BC2/A4e). **Redaction is a HARD pre-write gate**
  (`kata-handoff` §7, C3 — fail-closed). **BP1:** the emit target is a **dedicated `engram.learnFeed.dir`**
  (active now; the engram prerequisite), **separate from `engram.backend`** (the CONSULT side, still gated/off
  D9/D56) — absent ⇒ no emit (no-op, BC1). **BP2:** `engram.md` added to the validator's `REQUIRED_PROTOCOL`
  (default-FAIL floor on the schema). Held 0.1.0 (policy A; no bump despite kata-improve's general semver rule).
  *Provenance:* user-approved β plan + BP1/BP2 2026-06-18.
- **D75 — RS: `kata-research` is an escalation-routed, fresh-context, NO-WRITE in-loop research subagent;
  findings pass a never-bypassed grounding gate before a deliberate superseding re-plan. (2026-06-19 —
  loop-cognition RS-GB1/2/3 build)** The autonomous floor's in-loop ambiguity resolver (the without-human end of
  the grill↔RS spectrum, D71). **Routing (RS-GB1):** a worker hits a must-deliver feature with **no in-plan
  solution** → writes a `kind: "research-needed"` escalation (`protocol/escalation.md`) → the **orchestrator**
  (never the worker) dispatches `kata-research` (fresh-context, `allowed-tools: [Read,Grep,Glob,WebFetch,
  WebSearch]` — no Write/Edit/Agent) scoped to the payload. It returns `{claim, source, confidence,
  grounds-to-plan?}`, grounding every claim in a cited source; it never re-plans, writes, or injects.
  **Grounding gate (RS-GB2, L2):** findings pass an **injected-knowledge mode** of `kata-evaluate` (grounding +
  drift → GROUND/REJECT/ESCALATE) paired with `kata-review`'s **injected-knowledge soundness** surface
  (source-authority/hallucination/confidence). **Structural invariant — never tiered, never bypassed (D33).**
  **Fold (RS-GB3):** only GROUND findings enter the build, via a **deliberate re-plan baked as a superseding
  decision** (audited in the drift ledger + escalation `resolution`); REJECT → logged; can't-ground / LOCKED
  tension → re-classify `human-required` (D1/C4 — never improvise). **Category `plan`** (control-flow, kin to
  grill/context); **module `kata/module/research`** (fires only on a research-needed escalation — conditional/
  additive, not always-runs spine, though it is the floor's *designated* resolver). cost-weight 3; 26→27 skills.
  *Provenance:* user-approved RS plan (HANDOFF §4) 2026-06-19; frozen loop-cognition DESIGN L2/L3.
- **D76 — AO: `kata-orient` is a SMART, task-type-aware launch orientation — the read half of the handoff;
  extends frozen loop-cognition L4. (2026-06-19, user-directed)** New skill `kata-orient` (`category: handoff`,
  **`kata/spine`** — receiving half of spine #5; **read-only** `[Read, Grep, Glob]`, no Write/Agent — returns the
  assembled orientation + routed-question flags) + new contract **`protocol/orientation.md`**. Beyond the frozen
  L4 (three tiers stable→context→volatile; vertical rollup = root + nearest-module `AGENTS.md`; lateral =
  kata-graph adjacency *pointers*, lazy-loaded; prime-frame cap; orchestrate hook-only), the user directed it be
  **smart like a good employee's orientation**, adding: **(a) task-type awareness** — classify the dispatched
  task (implement-feature / fix-bug / refactor|version-up / research / evaluate|review / grill|plan) → tailor
  which docs to surface + which callouts to raise; **(b) contextually-derived pointers + callouts** — scan the
  in-scope standard markdown (root + nearest-module `AGENTS.md`/`CLAUDE.md`, `CONTEXT.md`, ADRs, DESIGN/PLAN
  slice, README) and *derive* task-relevant pointers (by path) + callouts (a relevant LOCKED decision, a
  drift-magnet glossary term, an applicable LESSONS-LEARNED lesson), never inlined wholesale; **(c) smart
  questioning + routing** — generate the questions a good hire would ask for this task-type/gaps, then route each
  **docs-answerable → answer inline · genuinely-ambiguous → pre-flag `research-needed` (hand to RS) ·
  LOCKED-tension/preference → human/grill** — making AO the launch-time *detector* on the grill↔RS spectrum
  (D71); **(d) handoff alignment from both sides** — `kata-handoff` gains an *Orientation tie-in* mapping its
  sections to the orientation tiers, so a handoff loads directly into orientation with no re-derivation.
  `kata-graph` stays a pure map-builder (AO *projects* adjacency from `ref`∪`call`, like the planner projects
  blast-radius); graceful degradation when graph/module-files absent. `REQUIRED_PROTOCOL += orientation.md`;
  27→28 skills. *Provenance:* user 2026-06-19 ("make it smart as a good employee… contextually-derived pointers
  and callouts from standard markdown… task type should cause relative questions… align handoff from both sides").
- **D77 — ML: two-stage candidate→human-promotion gate (`kata-promote`); agent-distilled skills are
  matched-but-marked + sandboxed until a human promotes them; `engram.autonomy` is a maturity∧config AND-gate,
  default `always-human`; the grounding gate is never bypassed. (2026-06-19 — loop-cognition L5/L6, LC-GB3/4/5)**
  Completes loop-cognition. **Stage 1 (L5):** the loop distils a reusable pattern into an **agent-distilled
  candidate** via `kata-write-skill` — `provenance: agent-distilled`, `scope: agent`, `summary` ≤60ch, tag
  `kata/origin/agent` (STANDARDS §1.3), written to `<agentSkills.dir>/candidates/` (**outside the repo
  `skills/` tree** — validator never scans it), **not loaded universally** → clears the **grounding gate**
  (`kata-evaluate` injected-knowledge mode, D33). **Stage 2 (L5):** end-of-session **human** gate `kata-promote`
  (new; `category: meta`, cost-weight 2, `allowed-tools` incl. `AskUserQuestion`) decides
  promote/keep-sandboxed/reject → on promote: `experimental→stable` + `scope` bump, move into
  `<agentSkills.dir>/skills/<category>/` preserving `name==dir` (D27). *Rejected:* Hermes' no-gate
  instant-universal model (uncontrolled positive feedback — wrong for a one-shot harness; RESEARCH bake-off).
  **Progressive autonomy (L6):** `engram.autonomy: always-human | assisted | auto-when-confident`
  (`protocol/config.md`; default **always-human**, D25-safe); `auto-when-confident` fires only when opted-in ∧
  fingerprint-mature ∧ high-confidence ∧ precedented, per-decision; novel/low-confidence/LOCKED-adjacent always
  stop the human (C2/C4); every auto-promotion logged (C6). **Autonomy replaces human *judgment*, never the
  grounding gate (D33/L2).** Gated on a mature engram (D9/D56) — today the dial sits at always-human, so
  kata-promote is a pure human review. `agentSkills.dir` first-run-configured; candidate lifecycle
  (`distilled→grounded→promoted|sandboxed|rejected`) tracked in `protocol/state.md`. 28→29 skills; loop-cognition
  COMPLETE (RS+AO+ML all built). *Provenance:* user-approved continue 2026-06-19; frozen loop-cognition DESIGN L5/L6.

### sprint-cadence (DESIGN FROZEN 2026-06-19 — `.planning/specs/sprint-cadence/DESIGN.md`; grill SC-GB1–10 + engram, freeze-gate audit HOLD→SHIP). Builds next (D16-first lock dissolved by D70).
- **D78 — `delivery` is a third orthogonal config axis (`one-shot | incremental`); unit = sprint. (SC-GB1/GB2)**
  Not a run-shape (would fork the preset table) nor a module (adds no skill — it changes loop topology). Composes
  with every existing axis. A **sprint** = one gated, demonstrable vertical slice ending at the full quality gate
  + a human course-correct. `incremental` (not "sprint") names the setting to avoid Scrum-timebox connotations.
- **D79 — three-layer freeze + Boundary Change-Control Protocol G1–G4. (SC-GB3)** Project DESIGN (north-star,
  superseding-decision only **+ a DESIGN-amendment at a boundary requires the same fresh-context `kata-review`
  SHIP as the initial freeze — B5**) · sprint ROADMAP (boundary-amendable) · active PLAN (immutable, D1). G1
  explicit approval · G2 drift-labelling · G3 post-approval adversarial sweep (`kata-review`, re-approval cap
  **PINNED=2**, a backstop not a tunable) · G4 snowball guard (**predicate = blast-radius vs remaining-roadmap
  footprint ONLY**, numeric threshold removed, D18). G1–G4 never tiered (D33). Safety spine: when in doubt, stop.
- **D80 — sequencing A+C: re-entrant `kata-bootstrap` routes, `kata-orchestrate` stays sprint-blind, NEW thin
  `kata-sprint` owns the boundary. (SC-GB4)** B (outer loop in orchestrate) rejected on D24d + the D8 pause-mid-
  skill failure mode. Delivery-awareness lives only in HANDOFF-phase routing (one-shot → `kata-handoff`/
  `kata-selfhandoff`; incremental → `kata-sprint`). T1–T8 tertiary-drift register LOCKED.
- **D81 — three-tier state; tier-3 `.kata/` cache is disposable, rebuilt from the git-committed trail. (SC-GB5)**
  Tier 1 frozen provenance (`kata.config`) · tier 2 durable trail (reports + boundary handoffs + superseding
  decisions, git) · tier 3 progression cache (`.kata/`, single-writer L3, churns). `kata-readiness` rebuilds
  tier 3 from tier 2 on re-entry → resume works in a new session/clone; git is the source of truth for "where are we?".
- **D82 — course-correct = a scoped delta-grill; `delivery.boundary` default `always-stop`. (SC-GB6)** Reuse
  `kata-grill` delta-mode (interrogate only what sprint N called into question + the user's requests; bake as
  superseding decisions); droppable to essential (D24c); G1–G4 hold at every tier (D33). `auto-continue-while-green`
  is opt-in and proceeds ONLY when green ∧ no escalations ∧ no pending corrections ∧ no G3 tertiary drift.
- **D83 — prime-frame context-budget sizing primitive; SUPERSEDES the threshold half of D8. (SC-GB7/B1)** The
  *prime frame* (recommended effective working band, agnostic fraction; adapter resolves to per-model tokens,
  D59) sizes sprints (floor ⇒ refuse sprint; ceiling ⇒ split) AND sets the one-shot self-handoff/refresh
  threshold — replacing D8's user-set %. D8's surviving principles (anti-over-conservative, task-boundary-
  preferred) carry forward. `kata-selfhandoff` EXTEND; runs intra-sprint too. ~1M window + fraction are
  `[TUNABLE]` grounded against real model facts **at build time** (not pinned from memory).
- **D84 — sprint baseline = the most recent green gate; sprinted version-up first-class, sprinted bake-off
  trimmed. (SC-GB8/GB9)** A sprint is version-up-shaped whenever a prior green baseline exists (existing repo's
  gate, else the prior sprint's). Reuses D50 footprint+regression + D51/D52 escalation verbatim; `kata-graph`
  à-la-carte on prime-frame pressure. Sprinted bake-off has no config path/offer/seam (revisit only on a concrete
  request once Spec B exists) — not forbidden, just not built.
- **D85 — the `kata-plan` sprint-roadmap layer is NET-NEW (the feature's largest build surface), not latent.
  (SC freeze-gate A1)** Roadmap-artifact schema pinned `{ projectDesignRef, frozenAt, sprints:[{ id, goal,
  gateCommand, demonstrableArtifactType, dagSeamRationale, dependsOn[] }] }`. `delivery` config field pinned
  (D3); `kata-report` minimal core built here = D32 v1 (not throwaway, D2). NEW skills: `kata-plan` roadmap
  layer · `kata-sprint` · `kata-report` v1. *Provenance for D78–D85:* sprint-cadence grill (2026-06-15) +
  freeze-gate audit HOLD→SHIP (fresh-context, 2026-06-19); frozen DESIGN.
- **D86 — `kata-bootstrap` is the sprint-boundary ROUTER (build-time gap-closure).** The frozen DESIGN §5
  wiring table omitted `kata-bootstrap` even though R4/D80 prose names it the router; the build (faithful to the
  PLAN) shipped `kata-sprint` *wired-but-not-connected* — nothing invoked it at a boundary. Closing the gap
  (faithful to R4/D80, not a new axis): `kata-bootstrap` Phase 0b reads `kata-readiness`'s sprint-progression
  verdict and dispatches — **`gated` ⇒ `kata-sprint`** (course-correct), **`dirty` ⇒ resume via
  `kata-orchestrate`**, red ⇒ escalation. Bootstrap also pre-fills + writes the `delivery` axis (preset:
  individual/batch ⇒ one-shot, version-up ⇒ ask). `kata-orchestrate` stays sprint-blind (BC2 intact — it never
  dispatches the boundary). *Provenance:* fresh-context `kata-review` (D15/A5) of the sprint-cadence build,
  2026-06-19 — Finding 1 (should-fix), accepted + fixed. Makes the feature invocable end-to-end.
- **D87 — The Greater Loop (architecture).** A thin NEW `kata-loop` conductor sequences **INITIATION → HARNESS
  (reused) → CLOSEOUT**, with a **context-carrying loop-back**. The two ends are **plug-and-play modules** =
  `modules/<name>/` dirs **each with its own `AGENTS.md`** (composed via the nested-AGENTS.md rollup `kata-orient`
  already supports). The greater loop is **optional/BC** (conductor absent ⇒ today's direct harness run). The
  conductor composes, never reimplements (kin to `kata-sprint`). (GL-R1a/c/d, R2a)
- **D88 — Initiation = NEW `kata-initiate` + frozen `INTENT.md`.** Front door: ingest the user's design → classify
  **kind (project|research|version-up)** → capture the **GOAL** to a frozen `INTENT.md` (goal/fixes[]/features[]/
  modulesAdded[]/changeSummary/target{kind,path,vault,platform}/grillDepth/readiness). **Interactive
  target/platform/vault configuration is part of initiation** — the **install-portability config layer folds in
  here** (installer mechanics stay later). **Dual spec-to-execute control:** the user may say "execute" anytime
  (hard bail) OR the grill self-judges readiness and **proposes** execute (user confirms); either path freezes
  `INTENT.md`. Composes readiness/grill/bootstrap/context. (GL-R1a/b, R2b, R3c)
- **D89 — Closeout = NEW `kata-closeout` + `kata-understand`.** Back-half control flow (composes, never gates —
  `kata-evaluate` keeps the gate): track the run artifacts → `kata-report` → **offer `kata-understand`** (opt-in,
  **graph-backed** via the F2 runtime, light git/diff fallback) → human gate (satisfied? / commit·push·merge? /
  run-again·build-new?). **Loop-back returns to initiation WITH context carried** (new baseline + understand map +
  lessons). (GL-R1c, R2c, R2d)
- **D90 — Foundations-first order + scoping.** Build **F1** (wire the dogfood-2 eval artifacts —
  `run_result`/`footprint`/`mutation_check` — into the live gate; closes the residual) and **F2** (make
  `kata-graph` operational: tree-sitter + a generator → `kata.graph.json`, **minimal/Python-first**, defer the
  Graphify oracle) **before** the modules. **testing-model is NOT a separate model** (Hermes has no grounding
  gate; our rigor is process-based) → **folded into F1**; the "route eval to another model" option stays latent in
  multi-model. **Execution UX:** orchestrated runs dispatch **foreground-parallel**; a host-agnostic artistic
  ASCII **`subagent-dashboard`** is build-later. (GL-R3a/b/d + UX) · *Provenance for D87–D90:* greater-loop
  interactive grill (3 rounds, 2026-06-20), `GRILL-LEDGER.md`; DESIGN **FROZEN** 2026-06-20.
- **D91 — Modules are self-contained directories under `modules/<name>/` (own AGENTS.md + own skills).** Phase-1
  structural resolution (user-chosen 2026-06-20). A module dir holds **both** its `AGENTS.md` (which *drives* it
  via kata-orient's path-based nested-rollup) **and** its skills (`modules/<name>/<skill>/SKILL.md`) — a true
  plug-and-play unit a host platform can swap wholesale. The skill-conformance validator is extended to
  **discover `modules/*/*/SKILL.md`** alongside `skills/*/*/SKILL.md` (index + wikilink-resolution + README-sync
  apply uniformly); module skills carry their functional `category` + a `kata/module/<module>` tag. Chosen over
  "skills stay in `skills/`, module = AGENTS.md + tag" because the path-based rollup only drives skills physically
  under the module path, and the modular/swappable vision (recurring user requirement) needs a self-contained dir.
  DESIGN §2/§4 "no new plumbing" refers to kata-orient's rollup (genuinely unchanged); the small validator-glob
  extension is Phase-1 foundational work. Applies to initiation, closeout, and the kata-loop conductor module.

- **D92 — "Greater Loop" rebranded → "the Kata Loop" (loop vocabulary).** (User 2026-06-21.) "Greater Loop" was a
  generic first-draft placeholder; the full outer cycle is now **the Kata Loop** (it *is* the Improvement Kata —
  ties to KataHarness + 改善型, easy to identify in-tool). The **inner one-shot stays "the Harness"** (operator's
  call — kept despite the product-name overlap; context disambiguates) and the version-up re-entry stays
  **"loop-back."** Glossary in `CONTEXT.md`. **Scope (supersede-never-rewrite):** the term is updated in the
  *active/canonical* surfaces only — `AGENTS.md`, `README.md`, `protocol/intent.md`, the `kata-loop`/`kata-bootstrap`/
  `kata-initiate`/`kata-closeout` skills + the two module `AGENTS.md`. The **frozen `.planning/specs/greater-loop/`
  spec dir + historical decisions/session-logs keep "Greater Loop" as provenance** (the dir slug is unchanged).
  Two **adversarial-surfaced seam fixes** shipped alongside (red-team of S2+S3a, 2026-06-21): `kata-orchestrate` now
  explicitly persists the grounding verdict via `tools/grounding_gate.py` → `.kata/grounding.json` (MAJOR-1: it was
  named only in the no-write `kata-evaluate`, so a real cycle would silently skip it) and collects per-task
  `prove_non_vacuous` records into the integration `gate_emit` mutation set (MAJOR-2). Deferred to BACKLOG: a
  machine `codeBearing` flag in `footprint.json` so rubric item 1 keys off evidence not evaluator discretion
  (MAJOR-3); a validator assertion that evaluator skills exclude Write/Edit (NIT-2); `_safe_path` SystemExit-vs-
  ValueError consistency across the tools (nit).

- **D93 — loop-hardening COMPLETE: the Kata Loop demonstrably loops (G6 proven via the S3b live loop-back).**
  (2026-06-21.) S3b ran the live Kata Loop on KataHarness itself **twice**, operator-driven (the un-simulatable
  `kata-initiate` interview answers + the Cycle-1 "run again (version-up)" version-select), and a **fresh-context
  re-entry grade returned G6 PROVEN (7/7)** — corroborated against independent evidence, not the self-written
  `readiness` prose: the Cycle-2 `INTENT.md` goal is a near-literal instantiation of the gap the **Cycle-1
  understand-map** named, and the carried baseline SHA matched `RESULT.json.resultSha`. Cycle 1 = **NIT-2**
  (validator asserts `kata-evaluate`/`kata-research` omit Write/Edit, `f72a3bb`); Cycle 2 (Phase-1b loop-back
  re-entry) = **MAJOR-3** (machine `codeBearing` flag in `footprint.py`; `kata-evaluate` rubric item 1 keys off it,
  `222cc7e`). Both BACKLOG items closed. **MAJOR-2** (D92 orchestrator collects per-task `prove_non_vacuous` →
  integration `mutation.json`) was **live-proven** both cycles; **MAJOR-1** (grounding-verdict persistence)
  correctly did **not** fire — a small, well-specified change produces no `research-needed` escalation (as
  PLAN-s3b predicted), and we did not manufacture one; it stays unit-proven. **All 7 loop-hardening gaps (G1–G7)
  are closed** — the Kata Loop is now "vetted, and demonstrably loops." pytest 445, validator 35/0, Snyk 0.
  *Provenance:* operator-driven S3b session 2026-06-21; record `specs/loop-hardening/{PLAN-s3b,REPORT-s3b}.md`.

- **D94 — WS-2 EXERCISED END-TO-END (parallelism + in-loop RS path live-run once, n=1 — not yet automated-test-proven) — and the
  `kata-slop-check` quality module shipped, both via one version-up dogfood.** (2026-06-22.) The WS-2 audit
  (`specs/ws2-loop-autonomy/AUDIT.md`) found concurrency well-designed but exercised once (dogfood #2, n=1) with
  **no automated test**, and in-loop learning/research autonomy largely **unwired**. Operator chose **in-context
  grading (zero new Python)** and to **wire the in-loop RS researcher now**. Vehicle = a real selected feature:
  **`kata-slop-check`** — standalone optional EVALUATE module (`kata/module/slop`), fresh-context no-write,
  default-FAIL slop verdict, **in-context heuristics** (general G1–G6 + 3 checks adopted from the MIT-licensed
  `ai-slop-detector`, attributed + re-implemented, no code copied). The 5-slice disjoint DAG carried a **genuine
  `research-needed` escalation** on S1 (which external checks + license). A fresh-context auditor graded the run
  **7/7**: 3 workers concurrent → S1 escalated → orchestrator **parked S1+S4+S5** while S2/S3 integrated
  → **`kata-research`** (fresh-context no-write) grounded the gap → **grounding gate GROUND×6**
  (`.kata/grounding.json`) → **superseding re-plan** folded the 3 checks → frontier recomputed (S4 after
  S1; S5 after S1+S3) → **mutation-proven** slice S4 (a 1-line registration). The feature **smoke-tested itself**: run on its
  own build it caught a real dangling seam-pointer (SLOP-DETECTED→NEEDS_WORK), forced the fix, re-ran **CLEAN**.
  Feature gate `kata-evaluate` **PASS**. **So the parallelism + in-loop RS path the audit flagged "unexercised" are
  now exercised end-to-end.** pytest **447**, validator **36/0**. **Honest caveat:** the durable `board.md`
  timestamps are orchestrator-written, so they can't by themselves distinguish *live* concurrency from a faithful
  replay — the genuine evidence was subagent wall-clock overlap; follow-up = **worker self-stamped start/end**
  (BACKLOG). Record: `specs/kata-slop-check/PLAN.md`, `specs/ws2-loop-autonomy/AUDIT.md`, `.kata/board.md`. Backout
  tag `pre-ws2-slopcheck`.

<!-- WS-3 user-friendliness (DESIGN+PLAN FROZEN, freeze-gate kata-review HOLD→SHIP; built 2026-06-24).
     Spec: .planning/specs/ws3-user-friendliness/{DESIGN,PLAN}.md (LOCKED L1–L11 / K1–K11). -->
- **D95 — WS-3 user-friendliness BUILT: the human-facing surfaces are friendly, goal-anchored, and honest; WS-4
  (offered backout) + WS-5 (closeout change-transparency) folded in. Built + gate-PASS + fresh-eval PASS, NOT yet
  field-exercised (n=0 live UX runs).** (2026-06-24.) The last pre-public workstream. A brainstorm (grounded in
  Hermes/Devin/Claude-Code UX research) → frozen DESIGN (L1–L11) → freeze-gate `kata-review` (**HOLD→SHIP** — it
  caught a real documentation-only seam: backout was wired to a `pre-<run>` tag no surface creates; re-anchored to
  the emitted `.kata/RESULT.json.baselineSha`) → frozen PLAN (6-slice disjoint DAG) → an **orchestrated version-up
  dogfood** (2 waves, concurrent Sonnet workers in worktrees, self-stamped overlapping wall-clock = provable
  concurrency) → fresh-context Opus `kata-evaluate` **PASS (10/10 build-acceptance)**. **Shipped (8 files,
  non-code-bearing, `codeBearing:false`, 0 drift):** **(a)** `protocol/persona.md` — a **nameless calm
  kata-craftsperson-who-translates** SOUL (Identity/Style/Avoid/Defaults; moderate-non-expert default register);
  **(b)** `protocol/narration.md` — a phase→plain-language map, milestone cadence, a **never-tiered**
  breakthrough-alert invariant, and an honesty guard; **(c)** `protocol/engram.md` **E23** register-adaptation
  seam (gated, zero CONSULT); **(d)** `kata-initiate` reflective **goal-mirror** (infer-then-confirm) that
  **refines, not reverses, the S2 anti-drift gate** — per-value mirror-visibility + INTENT-survival teeth, blanket
  approval FAILS; **(e)** `kata-bootstrap` one **"how careful"** dial mapping to *existing*
  `mode`/`tiers["kata-grill"]`/`delivery.boundary` (no new config field), the composition ladder behind an advanced
  drawer; **(f)** `kata-orchestrate` additive **milestone narration** (dispatch logic untouched); **(g)**
  `kata-closeout` + `kata-report` **goal-anchored by-aspect closeout** leading with plain-language what-changed-why,
  plus a **first-class offered backout** (`git reset --hard <baselineSha>`, human-gated, never autonomous).
  **Honesty (exercised-vs-proven):** this is an authored UX *verified by the validator + a fresh-context
  evaluator* — **not yet exercised in a live user-facing run**; the next real Kata Loop run is the first true UX
  test. **Adaptive register is a gated seam, not live** (D9/D56/D74). The build's own closeout dogfooded slice F.
  pytest **447**, validator **36/0**. Backout tag `pre-ws3`; merge `d08908d`. *Provenance:* operator UX decisions
  Q1–Q6 + open-items (2026-06-24); freeze-gate + re-confirm; orchestrated build. Record:
  `specs/ws3-user-friendliness/{DESIGN,PLAN}.md`.

<!-- WS-3 follow-up — two-tier closeout (PLAN FROZEN + built 2026-06-24).
     Spec: .planning/specs/ws3-closeout-report/PLAN.md (LOCKED M1–M10). -->
- **D96 — WS-3 follow-up: the closeout is now TWO-TIER — a concise CLI/GUI summary that links to a durable,
  on-brand, self-contained HTML report; and this build WAS the WS-3 field-exercise (n=0→1). First KataHarness
  logo defined.** (2026-06-24, merge `c265c42`.) Operator direction: emit a summary closeout in the CLI/GUI + a
  link to an in-depth report, "ideally a high-quality templatized clean/on-brand HTML report." Built as a
  3-slice non-code-bearing version-up dogfood (concurrent Sonnet workers, self-stamped): **(S1)**
  `modules/closeout/resources/closeout-report.template.html` — a **self-contained** (inline CSS+SVG, no external
  refs, offline) branded report template with a placeholder-token contract + `BRAND.md`; **(S2)** `kata-report`
  composes **both tiers** (concise summary ending in the report link + the tokenized full report; risks→warning
  tiles, backout→error tile); **(S3)** `kata-closeout` **emits `.kata/CLOSEOUT.md`** (Markdown source-of-truth)
  + **renders `.kata/closeout.html`** by filling the template **in-context** (no new Python; `.html`/`.css` are
  not in `footprint._CODE_EXTENSIONS` ⇒ `codeBearing:false`) + presents the CLI summary ending with the link.
  Never-gates (L7) + offered backout (L9) preserved. Gate PASS; a fresh-context Opus `kata-evaluate` **caught a
  cross-slice defect** (verdict-badge CSS class mismatch) → fixed → PASS. **Field-exercise (the point):** the
  build's own closeout was the **first live run of the friendly closeout** (WS-3 n=0→1), and the **operator
  refined the brand live at the gate** — dropped a tried inline-SVG wave motif + a tab-like loop ribbon; landed
  a subtle **KataHarness logo** (the project's first — kaizen ascending-bars + a rising ochre arrow), readable
  **serif Title-Case** section headings, and **error/warning/note/ok callout tiles**, on a **Hokusai-derived**
  palette (aged paper · Prussian blue · ochre · rust). **Carry-outs:** native in-tool rendering (Claude
  `Stop`/`SessionEnd` hook + statusline verdict line; other tools per adapter) is **deferred adapter work**
  (M8); WS-2 worker-self-timestamp polish returns to the queue. pytest **447**, validator **36/0**. Backout tag
  `pre-ws3-report`. Record: `specs/ws3-closeout-report/PLAN.md`.

<!-- WS-2 polish — worker self-timestamping + artifact-provable concurrency (built 2026-06-24).
     Spec: .planning/specs/ws2-polish/PLAN.md (LOCKED K1–K7). -->
- **D97 — WS-2 polish: worker concurrency is now provable from artifacts (`.kata/concurrency.json`) via worker
  self-stamping + an in-context snippet — NO new committed Python.** (2026-06-24, merge `4d8f01b`.) Closes the
  WS-2 honest gap surfaced by `specs/ws2-loop-autonomy/AUDIT.md` §7: the durable `.kata/board.md` timestamps were
  **orchestrator-written**, so they recorded concurrency but could not, on their own, distinguish a live run from
  a faithful replay (D94 caveat). Fix = a **worker self-stamp contract** (each worker appends `CLAIM`(start)/
  `DONE`(end) to the **shared** integration-root board via `kata_board.append_event` with its **own** process
  clock) + a **concurrency-evidence artifact** (`.kata/concurrency.json`: `maxInFlight`, `genuinelyParallel`,
  per-task wall-clock, overlap windows) the gate derives and a fresh-context evaluator reads. **Operator
  direction (this session):** keep the rich evidence artifact but produce it **in-context, not as a new tool** —
  so the concurrency computation is an **embedded snippet stored in `protocol/board.md`** (the single source of
  truth, K3), run by the orchestrator at the gate; **no `tools/` module** added ([[prefer-in-context-over-new-python]],
  K1). That keeps the whole run **non-code-bearing** (`codeBearing:false`, K2 — `.md` only ⇒ mutation-proof N/A).
  3-slice / 2-wave orchestrated dogfood (concurrent Sonnet workers in worktrees): **(A)** `protocol/board.md` —
  CLAIM/DONE self-stamp framing + the "Concurrency evidence" section (schema + canonical snippet); **(B)**
  `kata-orchestrate` — worker-prompt self-stamp requirement + a Final-gate concurrency-emit step (pointer to A,
  never duplicating the snippet); **(C)** `kata-evaluate` reads `concurrency.json` as **evidence, never a
  stand-alone default-FAIL trigger** (K6 — a legitimately single-worker run is not a failure) + HANDOFF §5 recipe.
  **Self-proving:** the build's own wave-2 workers (B+C) ran genuinely concurrently and this run's
  `concurrency.json` shows **`maxInFlight:2`** with a ~75s overlap window — the feature demonstrated on its own
  construction. Fresh-context Opus `kata-evaluate` **PASS 7/7** (snippet byte-for-byte vs PLAN; no `.py` touched;
  `withinFootprint:true`). pytest **447**, validator **36/0**. Backout tag `pre-ws2-polish`. Record:
  `specs/ws2-polish/PLAN.md`. **Honest scope:** this proves a run *recorded* concurrency from worker clocks; it
  is not a forgery-proof attestation, and the snippet is recipe text validated in-context (not a committed unit
  test). **Still deferred BY DESIGN:** in-loop LEARN-between-iterations (β emit-only, D74) + engram CONSULT
  (D9/D56) — WS-2's autonomy posture remains *bounded, human-gated autonomy + now-provable parallelism*.

<!-- Loop-hardening fold-back from the WS-2 red-team (kata-improve). Lesson: L12. -->
- **D98 — The adversarial red-team (`kata-review`) is now a STANDING loop step on code/contract-bearing builds,
  and `kata-evaluate` must reproduce derived artifacts rather than trust them.** (2026-06-24, operator-prompted
  Improvement-Kata fold-back.) Trigger: the WS-2 polish build passed `kata-evaluate` 7/7, but a separate
  adversarial `kata-review` — run only because the operator asked — caught a real correctness defect (the
  concurrency artifact was computed over an un-cleared board; the committed copy disagreed with what the snippet
  actually emits → it had been hand-filtered). The default-FAIL gate **graded the artifact as-presented** instead
  of regenerating it from source — the project's signature "recorded-not-reproduced" failure mode (L12). Operator's
  framing: *"if code is coming out of our loop and an external red-team is still catching problems, we should
  improve the loop."* Decision: **(1)** `kata-evaluate` gains **rubric item 9 — "reproduce, don't trust"**: any
  *derived* artifact is regenerated from its stated source and reconciled (mismatch ⇒ NEEDS_WORK), and any *claimed
  seam* is executed once, not accepted as prose. **(2)** A fresh-context no-write `kata-review` becomes a **standing
  Final-gate step** (`kata-orchestrate` step 6 + recipe HANDOFF §5 step 7) that runs **after `kata-evaluate` PASS,
  before merge**, on a **code/contract-bearing** build (a trivial docs-only run may skip — operator cadence choice,
  "merge-gate on substantive builds"). The two lenses are complementary, not redundant: `kata-evaluate` grades
  against the frozen plan; `kata-review` actively attacks (seams, reproduction, slop). This **wires** a lesson the
  project had already recorded once (**L10c**) but never baked into a skill, so it recurred — the meta-lesson being
  *fold lessons into the skills, not just the ledger.* Non-code-bearing change (skill/doc edits). validator 36/0.
  **Dogfooded immediately:** this fold-back is itself contract-bearing, so it was run through the *new* standing
  red-team before commit — `kata-review` caught a duplicate HANDOFF step number AND the irony that "contract-bearing"
  had no machine signal (`.md` ⇒ `codeBearing:false`), so the rule would have skipped its own gate. Both fixed:
  `kata-review` RUBRIC gains **surface 6 (reproduction & seam-liveness)** so the orchestrator's named deliverables
  map to a surface; the scope clause now states "contract-bearing" is *judged* (covers `protocol/**` +
  `skills/**/SKILL.md|RUBRIC.md`), not flag-derived; merge-gate red-team pinned to **≥ standard tier**. (The new
  lens proving its worth on its own introduction is the cleanest possible validation of L12.)

<!-- Strategy: the second-brain learning arc (Recall · Reason). Supersedes the "engram" framing.
     BRIEF: .planning/specs/second-brain-learning/BRIEF.md (pre-grill). -->
- **D99 — Loop-learning strategy locked: ship Controlled (A) now, Gated-learning (C) is the destination,
  Hermes-fluid (B) is a trap; and the learning subsystem is re-modeled as Second brain + Recall + Reason
  (drop "engram").** (2026-06-24, operator strategy session; adversarially validated by a fresh-context
  red-team.) Three approaches to the loop's failure/learning topology were assessed and attacked:
  - **A — Controlled (NEXT):** staged gate cascade + a thrash-budget that escalates an oscillating fix-loop to a
    deliberate RE-PLAN; churn = defect signal; no in-loop learning. Ship the *honest* version: + wire the live RS
    researcher harder, + log churn into the β feed so cold-starts still feed the corpus. "Harden what exists, add
    nothing" — also the answer to the live "is the loop bloated?" question.
  - **B — Hermes-fluid (TRAP):** ungated distill→retry, plan emerges organically. Deletes KataHarness's reason to
    exist — kills reproducibility (the north star) and poisons memory with no gate (D64/D67/D69). **Borrow its
    mechanisms (D69), never its philosophy.**
  - **C — Gated-learning hybrid (DESTINATION):** A's spine + a bounded, gated in-loop learning layer — the only
    approach that captures Hermes's compounding without surrendering the spine; the project's stated endgame.

  **Corrected model (supersedes "engram", which conflated three things into one word/file):**
  **Second brain** = the data (BYO, agnostic). **Recall** (the *Librarian*) = a per-vault fetcher/adapter that
  serves a standard contract and **lives with each second brain** (PokeVault / the work repo build their own),
  never decides — the adapter pattern (spine #3) applied to the second brain; it **is** the D30 clean-room backend
  binding, named. **Reason** (the *Advisor*, `kata-reason`) = KataHarness's decider — asks Recall to surface
  material, fuses it with research (RS + grounding gate), returns a **calibrated recommendation that mirrors the
  user**; advisory, not authoritative (the CONSULT path, finally named + skilled). KataHarness ships the **Recall
  contract + `kata-reason` + the exam + the triage**; Librarians are downstream. *Recall serves; Reason decides.*
  Names collision-checked (both clean; "Reason" has 0 concept-uses). Tagline: **Recall what you know · Reason what
  you'd do.**

  **C's unlock — four tumblers (no hand-waved "maturity"):** (1) a pointed-at second brain + a Recall
  implementing the contract (install-portability dependency); (2) **readiness exam** — `kata-reason` predicts the
  user's **held-out** past decisions (with research context) at **calibrated confidence** (high-confidence-wrong
  fails hard); fresh-context, no-self-cert, standing+cached (project-start / on-request / corpus-growth — NOT every
  loop); pass → C unlocks, fail → graceful fallback to A — *the measurable definition of "mature" the red-team said
  was missing*; (3) **inline triage red-team** per Reason decision — structured, fail-toward-escalation, auto-clears
  only low-stakes ∧ high-confidence, else escalates to fresh-context `kata-review`/human (cheap cascade stage on
  judgment; authoritative gate stays fresh-context); (4) **outcome benchmark** (`kata-loop-benchmark`, **promoted
  from far-future garnish to keystone**) — proves C-on beats C-off, sets the unlock threshold. Autonomy opens
  **progressively, risk-tiered** (D65 dial): low-stakes first; **scope/drift/feature last, recommend-before-auto.**

  **C/B invariant (LOCKED-class — getting it wrong IS sliding into B):** every Reason decision stays a
  **deliberate, frozen, gated, thrash-bounded, audited event toward a human-frozen goal.** *Protect the process,
  not the decider.* Reason may re-plan *toward* the frozen INTENT/goal; it may **never expand the goal** (that
  re-freezes with the human); `kata-defer` parks nice-to-haves. **Test:** *did the decision produce a discrete
  frozen artifact the gates judged, or did the plan just quietly become something else?* First = C; second = B.

  **Security/egress** descoped per operator (their second brain, their responsibility); re-enters only at
  public-release/multi-user, localized to **each Librarian's egress boundary** (per-vault, in its own repo), never
  the core. **Re-sequences the backlog:** promotes `kata-loop-benchmark` to the keystone that *defines* C's unlock;
  the **engram→second-brain/Recall/Reason rename is a pending migration** (`protocol/engram.md`, E1–E23, D9/D56/
  D74/D65, CONTEXT) — its own deliberate contract pass, NOT half-done now. **Immediate buildable work stays
  A-hardening (the thrash guard).** Record: `specs/second-brain-learning/BRIEF.md` (pre-grill; gets the freeze-gate
  adversarial review before any build).

<!-- Approach-A hardening (D99). Spec: specs/fix-loop-hardening/. Lesson context: D98/L12. -->
- **D100 — Fix-loop hardening: the orchestrator's fix-loop is now bounded (thrash budget) and its
  re-verification scoped (material re-verification).** (2026-06-24, merge `fc7f4f7`; the Approach-A hardening
  from D99.) Closes the "shorten-on-fail / does it churn?" gap: the fix-loop (`NEEDS_WORK → targeted fix → loop
  to PASS`) was unscoped (re-running the full expensive stack after each fix) and unbounded (no stop signal —
  the churn the spine fears). **Rule 1 (material re-verification):** after a fix, always re-run the cheap
  deterministic gate; re-run a fresh-context judge **iff** the fix footprint (`.kata/footprint.json.changed`)
  intersects a file that judge's findings cited — **indeterminate ⇒ re-run (fail-safe, LOCKED)**; one
  confirmation pass after the final fix batch = cheap gate + `kata-evaluate`, with the D98 `kata-review`
  running **once after, never inside the loop.** **Rule 2 (thrash budget):** a **per-area** count (N=2 → 3rd
  failure) **+ a run-level ceiling** (`2×tasks+2` `[TUNABLE]`) so A↔B oscillation can't hide, both
  **orchestrator-in-context** (it counts its own eval→fix iterations; it **writes a `DECISION` line per
  fix-cycle** as the durable recount trail — no `state.json` field, no new board TYPE, no `update_task`, no
  Python, L4); at budget → **`kata-diagnose`** (resolved tier) returns a **NEW fix-problem vs plan-problem
  verdict** (shared `RUBRIC.md`, from its Phase-6 seam) → the **human valve fires only on plan-problem**, via
  the existing `human-required` kind (**no enum change**, L6), async-parked, supersede-not-rewrite, never
  silent. The missing **bridge** between "fix loop exhausted" and "deliberate re-plan" (spine #2:
  re-planning is an event, not a habit). **Also the C-arc safety rail (D99):** every future `Reason`-approved
  re-plan counts against the same budget. **Process:** built through the **main orchestrated loop** (S1
  contract → S2 wiring, sequential), with the full freeze-gate discipline that paid off repeatedly — freeze-gate
  **HOLD** (4 blockers + 4 majors, all on phantom/contradictory machinery) → resolved → re-confirm **HOLD** (B4
  regressed into a new phantom seam + 2 stale) → resolved → build `kata-evaluate` **PASS 7/7** + standing D98
  `kata-review` **SHIP-WITH-FIXES** (2 degrade-safe: ceiling had no number; "already writes" overstatement →
  instruction). pytest **447**, validator **36/0**, `codeBearing:false`. Backout `pre-fix-loop-hardening`.
  Record: `specs/fix-loop-hardening/{DESIGN,PLAN}.md`. **Honest scope:** **wired + two-lens-PASSed, but
  exercised by ZERO real thrash events** — N=2 + the ceiling are provisional pending dogfood calibration; the
  `kata-diagnose` verdict is a new, untested-in-anger capability. **Meta:** the freeze-gate/re-confirm/red-team
  caught the **phantom-machinery / over-claimed-reuse class FOUR times** across this spec — the live case for
  D101's recurrence-hardening (and the memory `verify-primitives-before-claiming-reuse`).
<!-- Recurrence hardening — the harness hardens its own agents. BRIEF: specs/recurrence-hardening/. -->
- **D101 — Recurrence hardening: when a failure-class recurs across runs, the loop hardens the responsible
  agent — automatically detected, deliberately gated. The harness-facing sibling of Reason/C (D99).**
  (2026-06-24, operator directive: *"when it happens over and over we need to harden the tool — that's how
  learning should work; I feel like it should be doing this."*) Today, hardening the harness's own agents
  (planner/coder/evaluator) against recurring failure-classes is **human-driven and per-instance** — a human
  notices and writes a lesson/memory. That is repeated manual patching, not learning. **Decision:** make it
  systematic in the **IMPROVE phase** — a **recurrence detector** clusters `kata-evaluate`/`kata-review`
  findings by (responsible-skill × failure-class) across runs (corpus = the β LEARN feed, D74); a class crossing
  a threshold triggers `kata-improve` to **propose a permanent guard in the responsible skill** (pre-flight /
  rubric / checklist item); the proposal is **fresh-context reviewed (no-self-cert) AND human-approved** (the
  `kata-promote` gate pattern + D98) before it modifies the skill — **never an auto-mutation** (a loop rewriting
  its own skills ungated is the **B-trap**; the **C/B invariant holds** — a hardening is a deliberate, frozen,
  gated, audited skill change). **First concrete instance (in hand):** the class caught **3× this session** —
  spec/planning agents **over-claiming that machinery exists** — becomes the first hardening (a
  `kata-plan`/`kata-design-doc` pre-flight to verify a primitive exposes the needed surface before claiming
  reuse; cf. memory `verify-primitives-before-claiming-reuse`). Its value is benchmark-measurable (did the
  class's recurrence drop?), tying it to the `kata-loop-benchmark` keystone (D99). **Gets its own
  grill → freeze → freeze-gate review → build** (the discipline that paid off 3× this session); **not** bundled
  into any other frozen build. Record: `specs/recurrence-hardening/BRIEF.md` (pre-grill).

<!-- D101 first instance BUILT — the phantom-machinery verify-before-reuse guard. -->
- **D102 — Phantom-machinery first hardening BUILT + MERGED (`47648bf`, 2026-06-25) — D101's worked example.**
  The verify-before-reuse guard ships: `protocol/reuse-claims.md` (cross-skill contract, the LD3 guard:
  *before claiming "reuses/composes X", grep/read X and cite the concrete `file:line`, else label NEW*) +
  by-path pointers in `kata-design-doc`, `kata-plan/RUBRIC.md`, `kata-tdd` + a `validate_skills.py` regression
  rule (dual mechanism — skill bodies for the two loaded producers, separate glob for the RUBRIC; **body-integrity**
  guard requiring the full LD3 phrase verbatim; **producer-existence** check so a renamed producer FAILs loudly
  rather than silently disabling the guard). Built through the full recipe (subagent-driven Sonnet T1/T2/T3,
  Opus judgment): freeze-gate `kata-review` HOLD→SHIP · `kata-evaluate` **PASS 9/9** · **T-fire proof-of-fire**
  (a fresh `kata-design-doc` agent refused to freeze a phantom `orient.emit_pointers()` claim, labeling it NEW) ·
  standing D98 `kata-review` **SHIP-WITH-FIXES→SHIP**. pytest **456**, validator **36/0**, Snyk **0**, mutation
  non-vacuous. **Honest scope (D98 M2/M3):** the validator enforces **presence, not behavior** — it catches
  removal/drift of the guard surface forever, but author-time compliance still rests on the LLM obeying the
  prose; the **T-fire is n=1, contaminated (probe surface named in the committed plan), with no guard-off
  control** — corroborating evidence, not proof of causation. The structural regression rule (with a real
  mutation bite) is the durable proof. Record: `specs/recurrence-hardening/{PLAN-phantom,REPORT-phantom}.md`.
  Backout tag `pre-phantom-hardening`. **This makes the general `recurrence-hardening` spec (D101) concrete** —
  the detector/`kata-improve`-proposal/`kata-promote`-gate machinery is still the deferred general build.
- **D103 — Phase-5 re-sequencing + install-portability scope-lock (2026-06-26).** A grounded scoping pass
  (verify-before-reuse pre-flight per [[reuse-claims]], `file:line`-cited) corrected two HANDOFF assumptions:
  **(1)** install-portability's **selection UX already landed** — target/platform/vault selection lives in
  `kata-initiate` Phase 2 (`modules/initiation/kata-initiate/SKILL.md:93–170`, the GL-R3c fold), and the
  kata.config path-seeds exist schema-level (`protocol/config.md:22–35`); so install-portability's *real*
  remaining surface is the **installer mechanics + workspace binding**, not the interview. **(2)** Debug Mode's
  build blocks on **TWO** locks, not one: install-portability **AND** `kata-preflight` (D29, planned-not-built;
  `debug-mode/DESIGN.md:137`) — install-portability alone does **not** unblock Debug Mode. *Scope:* install-
  portability v1 = **full installer layer** (workspace-binding file + discovery + the three user paths
  [PokeVault-link · BYO-vault-scaffold · aim-each-folder] + the stable install contract + per-platform installer
  dispatch + `docs/SETUP.md`); selection UX is NOT re-built. *Sequence (Track A first):* grill→freeze→build
  **install-portability** → **kata-preflight** → **Debug Mode** build, THEN Phase-5 strategic (multi-model ·
  capability-aware-assignment · testing-model · strategy BRIEFs · v0.1 release-checklist). *Why Track-A-first:*
  Debug Mode is the onboarding/conversion killer-app and the sole reason install-portability became critical-path;
  nothing else is currently blocked waiting on the foundation items. *Open (decided at install-portability's
  freeze):* whether the `kata-preflight` grill folds into install-portability's (the `preflight.*` config seeds,
  `protocol/config.md:28–35`, already couple them) or runs as a clean separate grill.
- **D104 — install-portability BUILT (the simple model) — 2026-06-26.** Grilled (`kata-grill-standard`), frozen,
  built, reviewed. **Mid-grill course-correction (operator):** the early grill drifted into a config-resolution
  cathedral (two-layer bindings, discovery precedence chains, install-contract taxonomy). Operator reset it to a
  plain model → memory [[grill-in-plain-terms]]. **The shipped model:** KataHarness lives in one central place and
  installs into the platform there; a small git-ignored `.kata-settings.json` remembers **two settings** — the
  default parent project folder + the vault location (where the second brain sits, for the learning component);
  each run, preflight asks project **name + rough location**, **searches** under the parent, and **confirms** the
  match (N→list, 0→type path); **copy mode** also asks a destination and works on the copy (original untouched).
  **Multi-platform (needed today, before benchmarking):** one small install routine per platform —
  **`claude` built + verified end-to-end** (flat-links all 36 skills into the host skills dir → discoverable;
  `.claude-plugin/plugin.json` for plugin distribution), **`codex`/`kiro` best-effort** (same pattern, not
  host-verifiable here), **`quick` no-op** (brings its own installer), unknown → manual steps.
  **Code:** `tools/{project_find,kata_settings,kata_install}.py` (+ CLI) + tests; `docs/SETUP.md` (cordoned, README
  points to it); `kata-initiate` Phase 2d (search/confirm + copy). **Gates:** pytest **490**, validate **36/0**,
  Snyk **0 medium+** (residual Low CWE-23 path FPs, `..`-guarded). **D98 adversarial review = SHIP-WITH-FIXES** →
  fixed: settings-write overclaim (docs corrected), destructive re-link now refuses to clobber a non-kata dir
  (`.kata-managed` marker), `write_settings` validates parentDir/vaultDir existence. **Honest scope:** never-git-
  vault is structural (no subprocess import); "verified" = on-disk placement, not in-host discovery; Codex/Kiro
  ship documented best-effort; Windows install method = copy (symlink needs Developer Mode → re-run to update).
  **Supersedes the "full installer layer" framing of D103** — multi-platform stays in scope but built the simple
  way, not as an installer-interface taxonomy. Records: `specs/install-portability/{DESIGN,GRILL-LEDGER}.md`.
  Backout tag `pre-install-portability`. **Debug Mode still also needs `kata-preflight` before its build (D103).**
- **D105 — multi-model-orchestration GRILLED + DESIGN FROZEN (2026-06-26).** The operator's real "multi-modal" vision:
  install KataHarness on the machine + on all models, confirm, then route loop **roles** to different platforms/models
  (Claude=coder, Codex=validator, Kiro=researcher…). Grounded in 5 cited research agents (`RESEARCH.md`): **two
  headline findings** — (1) the `SKILL.md` Agent-Skills format is now a **shared standard** across Claude/Codex/Kiro/
  Copilot/Cursor (one skill payload targets all; the D104 flat-link installer generalizes by pointing at
  `.agents/skills/`); (2) **every target is headless-automatable** (Kiro via `kiro-cli`, not the IDE). **Grill (plain
  terms, per [[grill-in-plain-terms]]) → DESIGN:** **5 role groups** (coder · validator=red-team+anti-slop+grounding ·
  researcher · orchestrator · **evaluator**=a lightweight inline scorer that accepts/sends-back/**reroll**s via the
  existing `bakeoff` best-of-N); **default all-on-host, multi-modal opt-in at preflight** with per-role overrides
  (BC1); **any role routable** (coder stays one sustained agent — coding parallelizes poorly, Anthropic); **dispatch =
  files + headless CLI** (a NEW task-brief artifact + NEW per-platform CLI adapters), **concurrent background
  subprocesses** reconciled with the rolling frontier; **failure → host fallback + log + surface**; **two orthogonal
  layers** (platform/model × `capability-aware-assignment` specialist); **orchestrator on the init host in v1**,
  configurable later (Quick→Kiro/Codex). **Convergence gate HOLD#1** — the D102 verify-before-reuse guard caught the
  ledger **over-claiming reuse** of kata-orient/kata-orchestrate/D104/kata.config (all read-only/Claude-only/absent);
  relabeled as **NEW capabilities N1–N5** with concrete schemas (BRIEF.json, per-role RESULT.json envelope, `roles`
  config + `confirmedPlatforms`, sentinel confirm probe) → **re-confirm SHIP**. KataHarness's own seams ARE the
  best-practice answer (FS-as-substrate, kata-orient three-tier = the Hermes pattern, orchestrator-as-plan-guardian,
  worktrees). **The lift is a thin routing layer over existing machinery, not a new orchestrator.** Records:
  `specs/multi-model-orchestration/{RESEARCH,GRILL-LEDGER,DESIGN}.md`. **Build PARKED** — sequence: extend install+
  confirm (N5) → roles config + BRIEF/RESULT schemas (N4/N1/N3) → Codex-as-validator dispatch adapter (N2) first →
  generalize. **Deferred to own pass:** the evaluator injection-points + score-threshold mechanism (supplies the
  evaluator's accept/send-back/reroll cutoffs; its result *shape* is frozen, its *thresholds* are not).
  **UPDATE (2026-06-26) — Codex-validator PROOF-SLICE BUILT** (`11bf609` + D98 fixes `2570cce`): N4 `tools/kata_roles.py`
  (roles resolver, default all-on-host/BC1, fail-closed) · N1/N3/N2 `tools/kata_dispatch.py` (build_brief + per-role
  result normalizer + RESULT envelope [status=dispatch-outcome ⊥ verdict-in-payload] + codex adapter behind an
  **injectable runner** = DESIGN §7 stub-CLI seam) · N5 `tools/kata_install.py` `confirm_platform` probe +
  `tools/kata_settings.py` `confirmedPlatforms` · `protocol/config.md` `roles` block. **End-to-end proof:** validator
  routed→codex → brief → dispatch(stub) → normalized HOLD verdict. pytest 522, validate 36/0, Snyk 0 med+. **D98
  SHIP-WITH-FIXES→fixed** (normalizer crash on non-object JSON; resultPath `..`-guard; codex `--output-schema`→`-o`).
  **Honest scope:** codex NOT installed → proven against the stub; real run gated on install+confirm; only the codex
  adapter built (kiro/copilot/cursor = stubs). Backout `pre-multimodel-slice`. **Remaining for the full layer:** wire
  dispatch into `kata-orchestrate` (LD6 concurrency + LD7 fallback) + the `roles` load-guard + the multi-modal
  preflight question in `kata-initiate` + kiro/copilot/cursor adapters + `.agents/skills` install targeting.
- **D106 — Red-team hardening of today's install + multi-model work (2026-06-26, `14e2ff3`).** A 3-pass adversarial
  sweep (dead-code/loose-ends + per-feature break-it) on D104/D105 found real defects, all fixed: **copy_project
  destroyed the SOURCE** when dest was an ancestor of src (broke copy-mode's "original untouched" promise) → reject
  any overlap; **researcher/coder reported `completed` on an empty result** → normalize default-FAILs on empty for
  every role; **the confirm probe false-positived on prompt echo** (token was IN the prompt) → the model must now
  GENERATE a transformed token; **a confirmed-but-undispatchable platform crashed dispatch** → returns a `failed`
  envelope + `_PROBE_COMMANDS` restricted to codex (the only dispatch adapter); **read_settings crashed on corrupt
  JSON** → degrades to BC1; **flat-link silently dropped same-named skills** → refuses dupes; build_brief rejects
  absolute/`..` resultPath (cross-OS); evaluator score validated [0,1]. **Dead code/loose ends:** `_brief_prompt`
  now conveys the unused inputs/ownedFiles/outputContract fields + fixes the write-vs-emit collision; `confirm_platform`
  wired into the CLI (`--confirm`, was test-only); dangling copilot/cursor probe entries removed. **Doc-vs-code lies
  corrected:** `protocol/config.md` + multi-model DESIGN no longer claim (present-tense, false `file:line`) that the
  orchestrator load-guard validates `roles` (it doesn't yet — marked design-staged/PARKED); the install DESIGN's "no
  subprocess import" reworded; both DESIGNs note `adapters/<platform>` + `.agents/skills` are TARGET not current.
  +14 tests. pytest 532, validate 36/0, Snyk 0 med+. What held under attack: path-traversal guards, the non-clobber
  marker, fail-closed routing, no command injection, the prior fixes.
- **D107 — Loop-init banner (WS-3 narration, 2026-06-26, `2826df1`+`fe8d015`).** Every run now opens with a
  **deterministic boxed readout** so the operator sees, in the conversation, that it is **KataHarness** executing +
  a brief summary of what: `tools/kata_banner.py` (pure, stdlib-only, byte-identical every run — consistency D18;
  full boxed banner at loop init, compact `↻ … loop-back` line on version-up re-entry; missing fields omitted).
  Wired into `kata-loop` (drawn from INTENT.md + kata.config + the frozen plan); documented in `protocol/narration.md`
  §5 as the one fixed-format narration element, additive to the phase map + bound by the honesty guard. **Painted in
  the closeout-report palette** (`modules/closeout/resources/BRAND.md` — Hokusai ochre brand-mark / warm-border frame
  / mid-blue labels / paper values, dark-terminal accents) via 24-bit ANSI behind `--color` (auto-on at a TTY, honors
  `NO_COLOR`); the run readout + the closeout report now share one visual identity. **Caveat:** ANSI renders on an
  ANSI-capable surface (the conductor runs it as a command); `--no-color`/`NO_COLOR` falls back to plain on a
  markdown-only surface. +10 tests. pytest 542, validate 36/0.

<!-- multi-model FULL LAYER built over the D105 proof-slice. PLAN: specs/multi-model-orchestration/PLAN.md
     (freeze-gate SHIP). Built through the recipe; merge 1f58415. -->
- **D108 — Multi-model layer BUILT over the proof-slice (full routing wiring) — 2026-06-26, merge `1f58415`.**
  The D105 frozen DESIGN's PARKED full layer is now wired. Authored a frozen PLAN (4 disjoint slices) →
  **freeze-gate `kata-review` HOLD→SHIP** (caught a kiro write-vs-emit seam + a `config.md` false-contract +
  a self-introduced phantom `target.platform` citation, all fixed) → orchestrated build (4 concurrent Sonnet
  workers in worktrees, TDD, mutation-proven, self-stamped — `concurrency.json maxInFlight:3`) → fresh-context
  `kata-evaluate` **PASS 9/9** (reproduced every artifact + executed the seams live) → standing D98 `kata-review`
  **SHIP-WITH-FIXES→SHIP** (caught 5 stale role-map `file:line` citations + 1 "proven" overclaim → fixed via
  **stable section-name anchors**, not line numbers). **What is now wired:** **(A)** `kata-orchestrate`
  Preconditions §0 gains a **`roles` load-guard** (reads `kata_settings.confirmed_platforms()`, resolves
  `kata.config.roles` via `kata_roles.resolve_roles` with `host_platform` = the orchestrator's runtime adapter
  identity [`"claude"` v1; non-Claude host DEFERRED, LD11], fail-closed STOP on unknown role / unconfirmed
  platform) + a **"Cross-model dispatch"** section (build_brief→dispatch→fold per role-group site; LD6 concurrent
  background; LD7 host-fallback + log + surface); `protocol/config.md:27` flipped DESIGN-STAGED→**wired**.
  **(B)** `kata-initiate` Phase 2e **"Make this run multi-modal?"** (surfaced only when a non-host platform is
  confirmed) + load-bearing value #8 + gate item; `kata-bootstrap` Phase 3 writes the `roles` block (omit when
  single-host). **(C)** `kata_dispatch` — a **capture-model branch in `_brief_prompt`** (`emit` for codex's `-o`
  capture; **`write` for kiro**, which has no `-o` → the worker writes `resultPath`) + `kiro_command` registered
  in `_COMMAND_BUILDERS`. **(D)** `kata_install` — **`.agents/skills/`** cross-tool flat-link target for
  best-effort platforms + a **kiro confirm-probe** + the **`_PROBE_COMMANDS ⊆ _COMMAND_BUILDERS` invariant**
  (a platform is routable only if it has both a dispatch adapter AND a probe). **Gates:** pytest **552**,
  validate **36/0**, Snyk **0 med+**, mutation `allNonVacuous:true`. **Honest scope:** the read-only roles
  (validator→codex, researcher→kiro) are **wired and stub-test-proven** (exercised end-to-end against an
  injectable stub runner); a real multi-model run is gated on **install + confirm**; the per-platform CLI flags
  are point-in-time (the confirm-probe is the standing guard). **DEFERRED (unchanged):** coder-routing
  (write-sandbox path described + supported by `build_brief(sandbox="write")`, not proven); **copilot/cursor**
  adapters; the **evaluator injection-points + score-threshold mechanism** (its result *shape* is frozen, its
  *thresholds* are not — MM-1). **This makes a real single-vs-multi-model `kata-loop-benchmark` runnable** once a
  second platform is installed + confirmed. Backout tag `pre-multimodel-layer`. Records:
  `specs/multi-model-orchestration/{DESIGN,PLAN}.md`. **Meta:** the three adversarial passes each caught a real
  defect the deterministic gate structurally misses (incl. the verify-before-reuse guard biting my own phantom
  citation) — the D98/D102 discipline working as designed.

<!-- kata-preflight BUILT — the PRE-FLIGHT spine phase. Spec: specs/kata-preflight/{GRILL-LEDGER,DESIGN,PLAN}.md.
     Merge 710347a. Clears the 2nd of Debug Mode's two build blockers (install-portability cleared the 1st). -->
- **D109 — kata-preflight BUILT: the PRE-FLIGHT spine phase (D29 realized) — 2026-06-26, merge `710347a`.**
  Grilled in plain terms ([[grill-in-plain-terms]]) → 4 operator decisions (PF-1 auto-run pre-approved installs ·
  PF-2 full v1 incl. the reference-counted cleanup report · PF-3 one mechanism for build-deps AND a target's
  runnable env · PF-4 sandbox-when-available-else-host+warn) on top of the pre-locked D29 + D-registry +
  `protocol/dependencies.md`. Built through the recipe: **freeze-gate `kata-review` HOLD→SHIP** (caught a
  command-injection BLOCKER — freeform-shell-string execution — + 3 MAJORs; fixed: structured argv, sandbox
  hard-block, host-install→degraded, D29 reconciliation + manifest approval-hash) → orchestrated 3-slice build
  (concurrent Sonnet workers, TDD, mutation-proven) → `kata-evaluate` **PASS 9/9** (executed every seam live) →
  **D98 red-team HOLD→SHIP** — **the red-team caught a real untrusted-source RCE path** the evaluator missed:
  `package="https://evil.com/m.tgz"` / `git+https://…` was a *positional source* pip/npm fetch **ignoring** the
  forced registry → postinstall → RCE. Fixed: **per-manager package-NAME grammar** (`_validate_package`; pip/uv
  `^[A-Za-z0-9._-]+(\[…\])?$`, npm `^(@scope/)?name$`, cargo `^[A-Za-z0-9_-]+$`; universal reject of `://`,
  leading `git+`/`http`/`.`/`/`, `..`) so **no package value can express a URL/VCS/tarball/path source for any
  manager**; + MAJOR-2 (approval artifact out of gitignored `.kata/` → committable repo-root path; tamper-claims
  downgraded to honest drift-detection) + MINOR-3 (Snyk SCA gate fail-**closed** when `scan_required` + no scanner
  wired). **What now exists:** `tools/kata_preflight.py` (guarded auto-installer — structured argv from a fixed
  `manager`→builder table, never `shell=True`, freeform `install` string **never executed**; forced trusted
  registry; Snyk SCA pre-install; manifest-hash drift gate; machine-global `~/.kata/installed-registry.json` +
  reference-counted cleanup recommendation, **never auto-uninstall**; target `baselineGate` runnable-env probe →
  `degrade` verdict; `preflight_required`/`gate_status` helpers) · the new spine skill `kata-preflight`
  (`coordinate`, `kata/spine`, never tiered) · `kata-orchestrate` **conditional fail-closed** PRE-FLIGHT
  precondition (no manifest ⇒ today's loop, BC; manifest + missing/blocked/unaccepted preflight.json ⇒ refuse) ·
  structured fields in `protocol/dependencies.md` · enumerate→manifest pointers in grill/design-doc/plan.
  **Gates:** pytest **633** (+21), validate **37/0** (36→37 skills), Snyk **0 med+**, mutation `allNonVacuous`.
  **Honest scope:** auto-install is **stub-tested** (injectable argv runner — no real machine mutation in tests);
  a real install runs only behind freeze-approved-manifest + hash + Snyk + sandbox guards; workers never install
  (least-privilege). **Clears the SECOND of Debug Mode's two build blockers (install-portability was the first,
  D104/D103) → Debug Mode is now UNBLOCKED.** Backout tag `pre-kata-preflight`. Records:
  `specs/kata-preflight/{GRILL-LEDGER,DESIGN,PLAN}.md`. **Meta:** D98 again caught what the conformance gate
  could not — the adversarial second lens is load-bearing on security-critical code (D98 working exactly as designed).

<!-- IaC-safety specialists (Tier 1) BUILT — the v1 of capability-aware-assignment, IaC-scoped.
     Specs: specs/iac-safety-specialist/{RESEARCH,DESIGN}.md + specs/iac-live-apply/BRIEF.md. Merge 396baa3. -->
- **D110 — IaC-safety specialists (Tier 1) BUILT — 2026-06-26, merge `396baa3`.** capability-aware-assignment,
  narrowed (operator) to **IaC specialists** for v1 — because for frontier models the specialist value is **safety/
  security/gate discipline, NOT language expertise** (a bad `apply` destroys a DB; a generic coder won't apply the
  plan-not-apply / destroy-escalation / misconfig discipline). 4-agent grounded research spike (`RESEARCH.md`) →
  grill (IAC-1..4) → freeze. **Two specialists** `kata-iac-terraform` + `kata-iac-cloudformation` (`category:
  execute`, never-tiered, DRY-by-pointer to `protocol/iac-safety.md`); **Tier 1 = author/review/gate, NO live apply**
  (the harness has no cloud creds; a live apply isn't git-reversible — **Tier 2 deferred** with a full assessment in
  `specs/iac-live-apply/BRIEF.md`: the structural blocker is that cloud applies break the loop's git-reversibility
  safety model). **Auto-activated by detected file-class** (`tools/iac_detect.py` — classifier + plan/change-set
  destructive-parsers, fail-closed on malformed); **Snyk IaC primary** (NEW wiring, injectable + **fail-closed** when
  unwired). The gate: validate/cfn-lint → `mcp__Snyk__snyk_iac_scan` (default-FAIL high/critical; FAIL if unwired) →
  8-smell lens → destructive analysis (static source-diff + parse a plan/change-set JSON *if provided* — Tier 1 does
  NOT generate plans) → emit `.kata/iac.json` → verdict pass/fail/**escalate** (destroy/replace on a stateful
  resource → `human-required`, orchestrator-written). `kata-evaluate` reads `.kata/iac.json`. BC: no IaC ⇒ no-op.
  **Built through the recipe** (4 disjoint slices, concurrent Sonnet workers): freeze-gate `kata-review` **HOLD→SHIP**
  (caught a command-injection-class freeform overclaim + fail-open scanner + a phantom `target.platform`-style "already
  wired" reuse claim) → `kata-evaluate` **PASS 9/9** → standing D98 `kata-review` **HOLD→SHIP** — **D98 caught a real
  safety BLOCKER kata-evaluate missed: the stateful set was too narrow** (EFS/SQS/SNS/Kinesis/OpenSearch/Neptune/
  DocumentDB classified non-stateful → their destruction silently would NOT escalate); fixed (prefix families) +
  RequiresRecreation impl + malformed-input fail-closed (`ValueError`, incl. the `actions`-as-string substring
  fail-open) + finding-7 Details/Target guards. **Gates:** pytest **739** (36→**39 skills**), validate 39/0, Snyk 0
  med+, mutation nonVacuous. **Honest scope:** Snyk-IaC + the gate are wired; auto-install/live-apply absent (Tier 2);
  detection is best-effort (false-negative acknowledged + `forceClassify` mitigation); the 8-smell lens is a
  self-check floor-raiser, the scanner is the authoritative gate. Backout tag `pre-iac-specialist`. Records:
  `specs/iac-safety-specialist/{RESEARCH,DESIGN}.md`, `specs/iac-live-apply/BRIEF.md`. **Meta:** D98 again caught
  what conformance passed over — the adversarial lens is load-bearing on security code (3rd session-instance).

<!-- Holistic cross-build red-team of D108/D109/D110 + fixes. No new feature — a hardening pass. -->
- **D111 — Holistic red-team of the D108/D109/D110 builds + fixes — 2026-06-27.** First-task of the session per
  `NEXT-SESSION-ORIENTATION.md`: a fresh-context, *cross-cutting* adversarial pass over the three back-to-back
  builds (each had only its own per-build D98; the seams *between* them were unreviewed). 5 parallel reviewers →
  synthesis → **operator-gated trimmed scope** (fix confirmed A/B/C; drop LOW cosmetic). **Real defects the
  per-build passes missed, all fixed + test-proven:** **(BLOCKER) preflight RCE** — `dep["verify"]` was a freeform
  shell string executed via `shlex.split`→runner *before* the SCA gate (bypassed registry-forcing + name-grammar +
  Snyk); fixed by a structured `verifyImport` builder (`_build_verify_argv`, per-manager fullmatch grammar →
  `python -c "import x"` / `node -e "require('x')"` / `bin --version`); freeform `verify` demoted to docs-only like
  `install`. **(HIGH) IaC gate-skips:** extension match was case-sensitive (`.YAML`/`.TF`/`.Template` skipped the
  gate) → case-insensitive; `iac.forceClassify` was a *documented mitigation that was never wired* → now passed into
  `iac_detect.classify_task` at dispatch; stateful-set was incomplete (KMS/Secrets/MSK/FSx/Backup/CloudWatch-Logs/
  Timestream/QLDB/MemoryDB/Keyspaces/dynamodb-prefix/S3-objects + CFN `EC2::Volume` missing → destroy downgraded
  escalate→fail, losing the human gate) → families added. **(HIGH) Snyk verdict** trusted by truthiness → strict
  `is True` + exception-fail-closed. **(MAJOR) iac.json cross-seam fail-open** — orchestrate claimed kata-evaluate
  catches an absent iac.json on an IaC run, but evaluate keyed off *presence* and couldn't tell "no IaC" from
  "gate skipped/crashed"; fixed: kata-evaluate independently re-classifies the footprint's changed files
  (`classify_task`) → absent/malformed iac.json on IaC-classed changes ⇒ NEEDS_WORK. **(MAJOR) `resolve_roles`**
  silently accepted-then-dropped off-host `orchestrator`/`evaluator` (config promised fail-closed) → `HOST_ONLY_ROLES`
  guard raises. **(MED)** TF `action_reason` was read from `change` (always "" on real plans) → entry-level (sibling
  of `change`); the test fixture had nested it wrong, masking the bug. **(MED)** manifest TOCTOU → single-read bytes.
  **(LOW)** validators `match`→`fullmatch`. **Doc-drift (4th recurrence):** the worst `file:line` cites converted to
  **function/section anchors** ([[cite-skills-by-section-anchor]]) — kills the class permanently; dead config fields
  (`extraScanners`/`pin_policy`/`approval_mode`) labeled reserved/advisory. **Honestly deferred (LOW/architectural,
  NOT built):** a sandbox-default flip (started, then *reverted* — the operator caught it as over-engineering a
  cosmetic finding; the spiral-check was load-bearing), snake→camel config rename, `severityThreshold`-floor
  enforcement, CDK-source classification (Tier-1 = TF+CFN; `forceClassify` is the escape hatch), a deterministic
  `iac_gate.py` (a separate build). **Gates:** pytest **776** (+37 proof tests), validate **39/0**, Snyk **0** on all
  3 changed Python files, D98 fresh-context re-review **CLEAN**. Applied **inline** (operator directive "apply +
  assess as you apply"), not orchestrated — surgical fixes across shared seam files. **Meta:** the holistic pass
  earns its keep — per-build red-teams are necessary but not sufficient after a fast multi-build day; the
  *between-build* seams (shared `kata-orchestrate`/`kata-evaluate`/`config.md`) are where the fail-opens hid.

<!-- Recurrence-hardening (D101) fired on the execution-injection/RCE class. Operator-prompted. -->
- **D112 — Execution-surface contract: standing guard for the RCE class — 2026-06-27.** Operator observed RCEs
  "popping up time and time again" and asked whether it was the first. **It was the third instance of ONE class
  in ONE component** (`kata-preflight` auto-installer): (#1) freeform `install` shell string executable (freeze-gate),
  (#2) `package` accepting a URL/VCS/path source bypassing the forced registry → postinstall RCE (D98), (#3) freeform
  `verify` shell string executed via `shlex.split` (D111, this session). Root cause: the dependency manifest is
  partially-trusted external input, the installer has several free-text fields, and each was hardened **in isolation**
  (whack-a-mole) with no standing rule the next field had to satisfy — so #3 slipped in after #1/#2 were "fixed." This
  is the **recurrence-hardening** loop (D101): a class that recurred is now hardened at the responsible surface, not
  re-patched per occurrence. **Built (operator-gated, inline, small):** `protocol/exec-safety.md` — the contract
  (*any externally-sourced value reaching a subprocess MUST be a structured, validated, `fullmatch`-anchored field
  compiled to an argv with `shell=False`; freeform command strings are docs-only; `shell=True` only for
  operator-trust-domain commands*) **+ a sink registry** of every `subprocess` call in `tools/` with its trust domain
  (external / operator / internal) and guard — the "config file that tracks these" the operator intuited. Plus
  `tools/tests/test_exec_safety.py` (**AST-based**, not text-grep): fails CI if a new `shell=True` appears outside the
  registered operator-domain allowlist (`mutation_run`, `run_result`), if `kata_preflight` regains a `shell=True`, if
  it ever reads the freeform `verify`/`install` fields for execution, if the structured builders/validators go
  missing, or if a registered sink is undocumented — **the mechanical guard that would have caught #3.** Audit result:
  current shipped code is clean (all manifest-fed sinks structured; only `mutation_run`/`run_result` use `shell=True`,
  both on operator-authored commands). **Gates:** pytest **786** (+10), validate **39/0**, Snyk **0** on the new test.
  Pointer added from `protocol/dependencies.md`. **Meta:** the operator's "is this the first?" question *is* the
  recurrence detector — a human noticing a pattern the per-build gates treated as independents.

<!-- Debug Mode Phase 1 (foundation) built. Spec: specs/debug-mode/{DESIGN,PLAN-p1}.md. -->
- **D113 — Debug Mode Phase 1 (foundation) BUILT — 2026-06-27.** First phase of the phased Debug Mode build (queue
  item a; DESIGN frozen `specs/debug-mode/DESIGN.md`, blockers cleared D104+D109). Authored `PLAN-p1.md` (3 disjoint
  slices) → **freeze-gate `kata-review` HOLD→SHIP** (caught the `eval`-RCE class in the *plan* — the spec-wrapper had
  proposed `eval(expr, {"__builtins__": {}})`, a known-escapable sandbox, on LLM-authored assertions; the D112
  exec-safety guard paying off one feature later — plus the debug-vs-version-up discriminator gap) → orchestrated
  3-worker build (S1+S2 parallel, S3 after S2) → `kata-evaluate` **PART A PASS** → **D98 PART B HOLD→(fix)→re-confirm
  HOLD→(fix)→SHIP**. **Built:** **(S1)** the `debug` run-shape (peer of version-up, `target.kind==existing`), gated on
  a distinct **`kata/module/debug`** module marker (mirrors kata-slop-check's `kata/module/slop` gating, so version-up
  is provably unaffected — BC); config enum + bootstrap preset + a `kata-orchestrate` comprehension-phase hook (P2
  pipeline/drift left as a comment seam). **(S2)** `tools/function_model.py` — the `function_model` oracle (LD2):
  schema + `validate_function_model` + **`_safe_eval` (AST-allowlist evaluator, NO `eval`/`exec`)** + `evaluate_spec`
  spec-wrapper + emit/load; registered as a NEW in-process execution surface in `protocol/exec-safety.md`. **(S3)**
  `skills/plan/kata-comprehend/SKILL.md` (category `plan`, never-tiered; drives the engine; does NOT reuse
  kata-understand). **Security (the load-bearing part):** the evaluator is **escape-safe** (D98 ran every breakout —
  `().__class__.__bases__`, `__import__`, attribute chains, comprehensions, lambda, walrus — all rejected; no builtins
  leak) AND **DoS-safe after two HOLD rounds**: (1st) `range` removed + per-exponent/shift cap + AST node-count cap;
  (2nd, re-confirm caught) a **chained-Pow** (`(((10**1000)**1000)**1000)`, 14 nodes, each exponent ≤ cap) still
  exploded multiplicatively → fixed **categorically: `**` rejected entirely** (boolean assertions never need it;
  Mult/LShift grow integer size only linearly in node count). Self-verified the reviewer's exact probes all raise in
  0.000s. **Gates:** pytest **867** (552→867 across the build), validate **40/0** (39→40 skills — `kata-comprehend`),
  Snyk **0** on `function_model.py`. **Honest scope:** P1 PRODUCES + VALIDATES the oracle only — no deviation
  pipeline, no fix loop, no drift gate (all P2); `confidence` is stored, not yet routed; FM derivation is LLM-authored
  (the engine validates/executes, it doesn't derive). **NEXT:** Debug Mode **P2** (7-step deviation pipeline LD4 +
  confidence routing LD5 + characterization-gen LD6 + behavioral drift gate §5), then **P3** (language prompt-profiles
  LD10 + onboarding LD13). Records: `specs/debug-mode/{DESIGN,PLAN-p1}.md`. **Meta:** D98 caught a real DoS the
  conformance gate (PART A PASS) missed — *again* — and the re-confirm caught a second-order miss in the first fix;
  the standing adversarial lens + re-confirm loop is load-bearing on security code (now the 4th+ session-instance).

<!-- Validation-miss manifest (T1) — recurrence-hardening data layer. Spec: specs/recurrence-hardening/{BRIEF-validation-misses,PLAN-t1-manifest}.md. -->
- **D114 — Validation-miss manifest (T1, universal/observe-only) BUILT — 2026-06-27.** Operator-directed feature
  (their own idea, refined from the assessment): a durable, universal manifest logging when the conformance gate
  (`kata-evaluate`) PASSED something the adversarial lens (`kata-review`/D98), a re-confirm, or a human later CAUGHT —
  the **data layer for recurrence-hardening (D101)**, the harness-facing sibling of the Hermes-borrowed C-arc (D99).
  It makes "the operator notices a recurrence" (the D112 RCE catch) a first-class, queryable signal. **Tiered:** T1
  (this — log/count/surface, observe-only) · T2 (recurrence→gated-proposal, = D101 proper, needs grill) · T3
  (auto-author guards, C-arc-gated, FUTURE). Built alongside Debug Mode (debug surfaces misses most) but **universal —
  the emit hook is in the shared `kata-review` RUBRIC, run by every mode's build.** Authored `BRIEF-validation-misses.md`
  + `PLAN-t1-manifest.md` (2 slices) → **freeze-gate HOLD→SHIP** (caught: the emit hook contradicted kata-review's
  read-only contract → relocated the write to the orchestrator [reviewer flags read-only → orchestrator appends]; and
  the non-fatal BC guarantee was prose-only → pinned as a tested contract) → build → `kata-evaluate` **PART A PASS** →
  **D98 PART B SHIP** (escape/RCE N/A — pure data; found 4 LOW edge cases, applied the 2 that move the BC guarantee
  in-code: B1 pathological-path → `False` not raise, B3 non-dict tolerance). **Built:** **(S1)** `tools/validation_misses.py`
  — `miss_schema`/`validate_miss`/`append_miss`(append-only, CWE-23-safe, **non-fatal: raises only on `..`/malformed
  caller-bugs, returns False on any I/O/path failure**)/`read_misses`(crash-tolerant)/`count_by_class`(string keys)/
  `recurrences`(passive `>=` detector); mutation-proven; Snyk 0. **(S2)** `protocol/validation-misses.md` (contract) +
  the universal hook: `kata-review/RUBRIC.md` flags conformance-escapes **read-only** → `kata-orchestrate` Final-gate
  appends them **non-fatally** + a `kata-evaluate` pointer. **Observe-only / C/B-invariant:** T1 records + counts +
  surfaces; it NEVER changes a gate verdict or mutates a skill. **Gates:** pytest **907** (867→907), validate **40/0**,
  Snyk **0**. Records: `specs/recurrence-hardening/{BRIEF-validation-misses,PLAN-t1-manifest}.md`; memory
  [[exec-injection-class-hardened]] is an example of what its T2/T3 would auto-propose. **Meta:** the freeze-gate's
  read-only-contradiction catch is itself the kind of doc-vs-code seam this manifest exists to record.

<!-- Debug Mode Phase 2a (the FIND half) built. Spec: specs/debug-mode/{DESIGN,PLAN-p2a}.md. Fully subagent-driven. -->
- **D115 — Debug Mode Phase 2a (deviation-discovery / the FIND half) BUILT — 2026-06-27.** Second phase of Debug Mode,
  built **entirely through the loop/subagents** (operator directive: drive every step via subagents to spare the main
  context). PLAN authored by a planning subagent → **freeze-gate `kata-review` HOLD→SHIP** (caught 2 LOW: pin FM-capture
  to observation-not-synthesis; add the `k_min` boundary to mutation targets) → 3-slice build (D1 engine; D2+D3 parallel)
  → `kata-evaluate` **PART A PASS** → **D98 PART B HOLD→fix→re-confirm SHIP** → operator merge gate. **Built:** **(D1)**
  `tools/deviation.py` — the PURE, deterministic LD4-funnel + LD5-confidence engine: `tally_self_consistency` (≥2/3
  `k_min`), `corroboration_gate` (the HARD false-positive control), `compute_confidence` (`C = w1·MSAS + w2·(1−entropy)
  + w3·StructuralPrior`, TUNABLE `DEFAULT_WEIGHTS`/`DEFAULT_THRESHOLDS`), `apply_force_low`, `route_finding`
  (auto-fix-eligible/research/defer/human), `run_funnel`, `findings_schema`/`emit_findings`/`load_findings`;
  mutation-proven (co-location, routing boundary, k_min); **no exec sink** (pure dict logic). **(D2)**
  `skills/execute/kata-deviate/SKILL.md` — the LLM-judgment driver of the 7 steps (FM-deviation via the AST-safe
  `function_model.evaluate_spec`; semantic compare; self-consistency; corroboration; adversarial-refute-as-bool); FM
  call-capture is **observation of operator test runs, not harness-synthesized invocation** (no new exec sink);
  `kata-research` **escalation-only** (H5). **(D3)** `kata-orchestrate` `## Deviation-discovery phase` — gated on
  `kata/module/debug` (BC: never off `target.kind`), emits `.kata/deviations/findings.json`, leaves a clean P2b seam.
  **Security (the load-bearing part):** D98 caught a real **fail-open in the corroboration HARD gate** — `_co_locates`
  did `None==None→True`, so a vague LLM-only finding (null module/locus) could reach `auto-fix-eligible`; fixed
  fail-closed (require truthy+equal module AND locus), **plus M-2: corroborator objectivity is now CODE-enforced**
  (`_OBJECTIVE_SOURCES` allowlist; a non-objective/missing `source` is ignored — the gate no longer trusts prose), plus
  null-coerce robustness (L-1) and the empty-string variant (L-3). Re-confirm: every attack (null/empty/wrong-locus/
  non-objective/missing-source/refuted/force-LOW) now fails closed. **Honest scope:** P2a STOPS at routed findings — it
  FIXES NOTHING; characterization-gen (LD6), the behavioral drift gate (§5), and the fix-application loop (LD9) are P2b.
  **Gates:** pytest **990** (907→990), validate **41/0** (40→41 — `kata-deviate`), Snyk **0** on `deviation.py`.
  Records: `specs/debug-mode/{DESIGN,PLAN-p2a}.md`. **Meta:** D98 again caught a real fail-open the conformance gate
  (PART A PASS) missed — in the very control the feature's correctness rests on — exactly the kind of "conformance
  passed, adversarial caught" event the D114 validation-miss manifest now exists to record. **NEXT: Debug Mode P2b**
  (the PROTECT half: characterization-suite gen + behavioral drift gate + the gated fix-application loop), then P3.

<!-- Debug Mode Phase 2b (the PROTECT half) built. Spec: specs/debug-mode/{DESIGN,PLAN-p2b}.md. Fully subagent-driven. -->
- **D116 — Debug Mode Phase 2b (the PROTECT half — apply fixes safely) BUILT — 2026-06-27.** Completes the core Debug
  Mode loop (comprehend P1 → find/route P2a → **characterize + drift-gate + apply-or-defer P2b**). Built **entirely
  through the loop/subagents** (operator directive). Planning subagent → **freeze-gate HOLD... wait SHIP** (1 LOW
  cite-by-line → anchor) → 3-slice build (F1 engine; F2+F3 parallel) → `kata-evaluate` **PART A PASS** → **D98 PART B
  SHIP** (found 2 MEDIUM fail-opens in the drift machinery → fixed → re-confirm SHIP). **Built:** **(F1)**
  `tools/drift_gate.py` — the behavioral drift-gate engine (§5 v1): `parse_test_outcomes`, `classify_transitions`,
  `validate_allowed_exceptions` (the **AEL integrity** guard — hard-rejects any Allowed-Exception entry that was
  GREEN-in-before; the AEL is a trusted finding-bound input, never inferred from after-results), `drift_verdict`
  (green→RED = BLOCK; AEL tests must flip RED→GREEN; **+ Step 2b: a baseline-GREEN test that VANISHES in after = BLOCK**,
  the D98 fail-open fix), `scrub_nondeterminism` (narrowed to object-repr addresses + labeled/ISO timestamps — the 2nd
  D98 fix, so real value changes are no longer masked), `characterization_snapshot_verdict`, `defer_record`/
  `emit_deferrals`, drift-report emit; mutation-proven (5 proofs); **no exec sink** (pure); `structural_drift_verdict`
  is a non-enforcing seam (§5 structural layer = FAST-FOLLOW, NOT v1 — surfaced honestly). **(F2)**
  `skills/execute/kata-characterize/SKILL.md` — blast-radius-scoped (via `footprint`) characterization-suite gen,
  pins-except-the-deviation, left-behind; establishes the AEL bound 1:1 to the finding. **(F3)** `kata-orchestrate`
  `## Fix-application phase` — gated on `kata/module/debug`: per auto-fix-eligible finding → characterize → `kata-tdd`
  fix in a `kata-worktree` → `drift_gate` verdict → `kata-evaluate` + D98 + Snyk → apply or **DEFER** (can't-fix-without-
  drift → `.kata/deviations/deferred.json`, preserving the no-drift guarantee); objective defects fixed regardless of
  confidence (LD9). **AEL is orchestrator-manifest-owned; the fix worker's lane excludes it (can't authorize its own
  breakage).** P3 seam left (comment only). **Honest scope:** behavioral drift enforced; structural/public-API
  invariance is a §5 v1 FAST-FOLLOW (not over-claimed). **Gates:** pytest **1062** (990→1062), validate **42/0**
  (41→42 — `kata-characterize`), Snyk **0** on `drift_gate.py`. Records: `specs/debug-mode/{DESIGN,PLAN-p2b}.md`.
  **Meta:** D98 *again* caught real fail-opens (in the very safety machinery, where conformance PART A PASS'd) — the
  load-bearing adversarial+re-confirm loop, 5th+ session-instance. **NEXT: Debug Mode P3** (language prompt-profiles
  LD10 + onboarding/convert-to-loop LD13 + the LD12 closeout confidence report) — the final phase; then Debug Mode is
  functionally complete. Optionally: exercise the full debug loop end-to-end on a seeded fixture repo.

<!-- Debug Mode Phase 3 (the FINAL phase) built. Spec: specs/debug-mode/{DESIGN,PLAN-p3}.md. Fully subagent-driven. -->
- **D117 — Debug Mode Phase 3 (the FINAL phase — closeout report + language profiles + onboarding) BUILT — 2026-06-27.**
  Completes the **core Debug Mode loop** (comprehend P1 → find/route P2a → characterize/drift-gate/apply-or-defer P2b →
  **report/onboard P3**); Debug Mode is now functionally complete at the skill/seam level. Built **entirely through the
  loop/subagents** (operator directive: drive every step via subagents to spare main context). PLAN-p3 authored by a
  planning subagent → **freeze-gate `kata-review` HOLD→SHIP** → 6-slice 2-wave build → `kata-evaluate` **PART A PASS** →
  **D98 PART B HOLD→fix→re-confirm SHIP** → operator merge gate. **Built:** **(A)** `tools/debug_report.py` — the PURE
  LD12 report-assembly engine: `debug_report_schema`/`snyk_report_schema`, `finding_id` (derivation identical to
  `drift_gate.defer_record`), `build_confidence_map` (assessed/low-confidence/skipped; every entry `heuristic:true`),
  `build_deviation_table` (deviation→fix→pinning-test; route-gated applied claim + ambiguous-id no-cross-join),
  `build_proof_rollup` (drift + suite + mutation + **real Snyk before/after** read from `.kata/snyk/*.json`),
  `build_debug_report`/`emit`/`load`; **5 mutation proofs; no exec sink**. **(B)** `skills/evaluate/kata-debrief` — the
  LD12 author/renderer (two-tier `kata-report` shape; reports, never gates). **(C)** `modules/closeout/kata-closeout`
  `Step 3b` — debug-gated; offers `[[kata-debrief]]`; reuses the human-gated Decision 2/3 (no new git path). **(D)**
  `skills/execute/kata-lang-profile` + 6 language profiles + a config/context specialist — LD10 prose-only specialists,
  selected by **footprint file extensions** (FM has no `language` field), injected at dispatch (mirrors the IaC precedent),
  **no fork / no new Python**. **(E)** `skills/coordinate/kata-onboard` — LD13 first-run/convert-to-loop, composes the
  BUILT install-portability surfaces (`kata_settings`/`project_find`/`kata_install`/`intent_scaffold` + `[[kata-initiate]]`/
  `[[kata-bootstrap]]`/`[[kata-closeout]]`/`[[kata-loop]]`); **convert-to-loop** and the **`.planning/` scaffold** honestly
  labeled NEW (no single existing surface). **(W)** `kata-orchestrate` — P3-seam resolved to a pointer + LD10 dispatch
  injection + the **`.kata/snyk/<finding_id>.json` before/after persistence** (the freeze-gate BLOCKER fix). **Freeze-gate
  caught a real BLOCKER:** LD12's DESIGN-mandated "Snyk before/after" cited a `RESULT.json` field that **no P1/P2 surface
  emits** (`run_result.build_result`/`gate_emit` carry no Snyk field; the P2b fix loop ran Snyk but discarded it) → phantom
  capability that would read nothing on a real run → resolved by persisting the fix-loop's existing before/after Snyk to a
  new `.kata/snyk/<id>.json` artifact (no new Python, no new sink — the Snyk MCP call already existed; persistence is a
  Write). **Security (the load-bearing part):** D98 caught **2 MAJOR fail-opens** the conformance gate (PART A PASS) missed,
  both in the LD12 honesty machinery: (1) **Snyk regression-masking** — `_snyk_rollup` trusted the prose-supplied
  `newFindings` (a +5 regression with `newFindings:0` rendered CLEAN) → now **recomputes** `effective_new =
  max(stored, max(0, after−before))`, a too-low stored value can't lower the result, missing/malformed count ⇒ `clean=False`
  (+ a 5th mutation branch); (2) **`applied:true` not route-gated** — a drift PASS marked any row applied regardless of the
  finding's route, so a `research` finding could inherit another's proof under a `finding_id` collision → now gated on
  `route=="auto-fix-eligible"` + ambiguous-id refuses to cross-join. Both fixed **at the engine** (not the prose — the exact
  principle the plan pins), mutation-covered; re-confirm SHIP (the conservative directions all err toward UNDER-claiming,
  the correct bias for the honesty surface). Plus 2 robustness MINORs (non-numeric/bool confidence + non-dict records →
  fail-honest, never crash) and the kata-debrief `#6` fix (removed an invented `.kata/RESULT.json` `verdict` field —
  kata-evaluate is no-write; the verdict is surfaced by the orchestrator/closeout). **Gates:** pytest **1108** (1062→1108),
  validate **45/0** (42→45 — `kata-debrief`/`kata-lang-profile`/`kata-onboard`), Snyk **0** on `debug_report.py`. **Honest
  scope:** behavioral drift only (structural = §5 v1 fast-follow); confidence = LD5 v1 heuristic (uncalibrated); **Debug
  Mode is n=0 LIVE** — proven on seeded fixtures, never run end-to-end on a real repo (the natural next step, newly possible
  now that install-portability + kata-preflight exist). **Plan divergence recorded (per D98 #5):** `kata-onboard` is tagged
  `kata/spine` (the validator structurally requires `kata/spine` OR `kata/module/<x>`; `kata/spine` is the least-wrong for
  a first-run on-ramp — `kata/module/debug` would be actively wrong) rather than PLAN-p3's `kata/coordinate+onboarding`.
  **Validation-misses:** the 2 MAJOR fail-opens logged to `.planning/validation-misses.jsonl` (D114, observe-only).
  **Deferred MINORs (NOT built):** clamp the cosmetic `newFindings` display integer on contrived-malformed input (`clean`
  already fails closed); the pre-existing `kata-report`/`kata-closeout` "verdict from `.kata/RESULT.json`" wording
  inconsistency. Records: `specs/debug-mode/{DESIGN,PLAN-p3}.md`. **Meta:** D98 *again* caught real fail-opens (in the LD12
  honesty surface, where PART A PASS'd) — the load-bearing adversarial+re-confirm loop, now the 6th+ session-instance; and
  the freeze-gate's phantom-capability catch (Snyk-from-RESULT.json) is exactly the verify-before-reuse class the project
  keeps surfacing.

<!-- Recurrence-hardening T2 (recurrence->proposal loop, act-but-gated) built. Spec: specs/recurrence-hardening/PLAN-t2.md. Fully subagent-driven. -->
- **D118 — Recurrence-hardening Tier 2 (the recurrence→proposal loop, act-but-gated) BUILT — 2026-06-27.** Queue item (b).
  Closes the recurrence loop the T1 manifest (D114) opened, realizing **D101**: when a failure-CLASS recurs, the loop
  **auto-drafts a human-gated hardening proposal** — automating the exact "operator noticed the RCE recurred a 3rd time"
  move that hand-triggered **D112**. Built **entirely through the loop/subagents** (operator directive). A grill-prep
  subagent framed the open decisions → **operator decided 3 calls** ((1) trigger = **3rd** recurrence, **2nd** for BLOCKER,
  clustered by `responsible_skill`×`failure_class`, counting **distinct runs**; (2) `failure_class` → **soft curated enum**;
  (3) **auto-draft** the proposal, human-gated) + adopted defaults (proposal names the target surface defaulting to a
  protocol-contract + mechanical-test, the D102/D112 shape; output `PROPOSAL-<class>.md` → freeze-gate `kata-review` →
  **human merge**, NOT `kata-promote`; detector at the Final-gate append hook + on-demand; a **handled sidecar**; count
  **distinct runs** not raw rows) → PLAN-t2 (planning subagent) → **freeze-gate `kata-review` HOLD→SHIP** → 3-slice 2-wave
  build → `kata-evaluate` **PART A PASS** → **D98 PART B SHIP** → operator merge gate. **Built:** **(S1)**
  `tools/recurrence_detect.py` — the PURE detector: `actionable_recurrences` (severity-aware threshold; **distinct-run
  counting** via `run_id` with `ts`-fallback **incl. blank/whitespace-coerce**; handled-skip; off-vocab flagging),
  `distinct_run_counts`, `cluster_severity_tier`, `detect_from_paths`, and the `.planning/recurrence-handled.jsonl`
  sidecar (`read_handled`/`append_handled`/`validate_handled`/`handled_schema` — `..`-guarded, non-fatal); **+ the BC-safe
  schema extension** to `tools/validation_misses.py`: a **soft** 8-member `failure_class` enum (published
  `_FAILURE_CLASS_VALUES` + a schema `enum` key + non-blocking `is_known_class`; **`validate_miss` UNCHANGED for
  `failure_class`** so a non-fatal append never DROPS a real miss — off-vocab is flagged by the detector, not rejected at
  write) and a **nullable `run_id`** field (→ 10-field schema). Pure, no exec sink; mutation-proven (8 targets incl. the
  blank-run_id guard). **(S2)** `skills/meta/kata-improve` **v0.1.0→0.2.0** — the auto-DRAFT proposal sub-mode: drafts a
  one-page `PROPOSAL-<failure_class>.md` (cluster + evidence rows + proposed target surface + guard text/test sketch) +
  appends the `proposed` sidecar marker; **writable footprint pinned to EXACTLY those 2 paths**; routes to freeze-gate
  `kata-review` → human merge. + `protocol/validation-misses.md` T2 contract section (act-but-gated; T1 observe-only kept
  accurate). **(S3)** `skills/coordinate/kata-orchestrate` Final gate — one **`run_id` per run** stamping on every appended
  miss + the **non-fatal** detector hook (all modes: NOTE per newly-actionable cluster + auto-invoke the draft; silent
  no-op absent any actionable recurrence; an error never breaks the run or changes a verdict). **Freeze-gate caught a real
  BC contradiction:** adding `run_id` to `miss_schema()` breaks `test_schema_round_trips` (asserts the exact field set)
  while the plan claimed "existing tests unchanged" → resolved via **option-b**: keep `run_id` documented in the schema
  (10 fields) AND own the single intentional `test_schema_round_trips` 9→10 edit; BC re-scoped to "existing DATA + BEHAVIOUR
  unchanged, one documented test edit." **D98 PART B SHIP** — every fail-open/invariant/BC attack held (re-proposal loop:
  a `proposed` cluster + a new miss does NOT re-trip; soft enum: off-vocab validates AND is flagged, never dropped;
  severity short-circuit fires at 2 for BLOCKER only; detector fails non-fatal on malformed manifest/sidecar) — 1
  nice-to-have **hardened pre-merge**: a blank/whitespace `run_id` ("" / "  ") was non-None so it collapsed distinct-run
  counting and silently suppressed detection → now coerced to fall back to `ts` (mutation-covered). **The INVARIANT
  (load-bearing):** T2 **READs the manifest + AUTHORs a proposal** — it never (i) changes a gate verdict, (ii) edits any
  skill/protocol/tool, (iii) writes the `guarded` marker, or (iv) merges its own proposal. The `guarded` marker + the
  actual guard authoring/merge stay **human**. **T3** (auto-authoring the guard doc+test itself) = OUT OF SCOPE / C-arc
  future. **Honest scope:** the footprint/`guarded` invariant is **prose-pinned** (LLM-skill architecture — no runtime
  code gate is possible on a markdown instruction; the plan acknowledges it; same risk class as every Write-capable skill).
  **Gates:** pytest **1175** (1108→1175), validate **45/0** (no new skill — kata-improve version-bumped), Snyk **0** on
  `recurrence_detect.py` + `validation_misses.py`. Records: `specs/recurrence-hardening/PLAN-t2.md`. **Meta:** the
  freeze-gate again caught a real internal contradiction (the BC claim vs the round-trip test) the planner was too close
  to see, and D98's distinct-run/soft-enum/non-fatality probes confirmed the act-but-gated boundary holds — T2 is the
  machinery that would have auto-proposed exactly the D112 exec-safety guard.

<!-- IaC Tier-2 (preview/approve/plan-capture HALF; execution DEFERRED). Spec: specs/iac-live-apply/PLAN-tier2-preview.md. Fully subagent-driven. -->
- **D119 — IaC Tier-2 (the live-apply preview/approve/plan-capture HALF; cloud EXECUTION DEFERRED) BUILT — 2026-06-28.**
  Queue item (c). The live-apply half the IaC specialists (Tier-1 = author/review/gate, D110) deliberately deferred —
  because a cloud apply is the **one operation `git` cannot undo** (you can't `git revert` a destroyed database). Per
  operator decision, scoped to the **preview/approve/plan-capture HALF ONLY**; the actual cloud EXECUTION (`terraform
  plan`/`apply`, `cfn execute-change-set`, live-state drift reads) is a **DEFERRED, n=0-live, creds-gated seam** —
  `run_apply` raises `NotImplementedError`; **nothing in this build can mutate infrastructure**. Built **entirely through
  the loop/subagents** (operator directive). A grill-prep subagent framed the open decisions → **operator decided 3 calls**
  ((1) scope = build-the-preview-half-now, STOP at the creds wall [not full-apply-mocked, not defer-entirely]; (2) **both
  Terraform AND CloudFormation**; (3) stateful destroy/replace = a separate **typed capability-gate** [the operator chose
  this over Tier-1's hard-block]) + adopted defaults (plan-hash approval-invalidation mirroring kata-preflight; fixed-argv/
  `shell=False`/operator-domain/approval-gated sinks, NEVER freeform; remote-state-required + drift-abort; never
  auto-rollback; `-target`/`-auto-approve` FORBIDDEN; parked-apply never auto-applies; **sibling** `.kata/iac-apply.json`
  not extending `.kata/iac.json`) → PLAN (planning subagent) → **freeze-gate `kata-review` HOLD→SHIP** → 4-slice 3-wave
  build → `kata-evaluate` **PART A PASS** → **D98 PART B SHIP** → operator merge gate. **Built:** **(A)**
  `tools/iac_apply.py` — the PURE engine: `build_tf_plan_argv`/`build_tf_apply_argv`/`build_cfn_create_changeset_argv`/
  `build_cfn_execute_changeset_argv` (structured argv, `shell=False`, identifier = positional DATA validated by `fullmatch`
  grammars incl. a **dedicated CFN ARN grammar**, `--` end-of-options, never `-target`/`-auto-approve`); `plan_hash` +
  `canonical_cfn_plan_bytes` (TF binds the binary `tfplan`; CFN binds the **FULL** `describe-change-set` so ARN/StackId are
  inside the hashed bytes — no replay against a different change-set/stack); `approval_verdict` (plan-hash-bound; re-plan ⇒
  `APPROVAL_INVALIDATED`, never collapses to pass); `capability_gate_verdict` (the typed stateful-destroy gate — clears
  ONLY when all three self-binding conditions hold: `grant.approvedPlanHash == computed_plan_hash` AND
  `authorizedStatefulAddresses ⊇` the stateful-destroy set AND a typed `confirmedToken`; fail-closed on every missing/null);
  `apply_state`; sibling artifact `.kata/iac-apply.json` (`iac_apply_schema`/`emit`/`load`); approval/grant/audit builders;
  and **`run_apply` = the deferred `NotImplementedError` seam** (no `subprocess` import on the path). Pure (AST no-sink
  scan), 6 mutation proofs incl. the `⊇` containment (b), the **self-binding hash equality (c)**, and the seam (f). **(B)**
  `protocol/exec-safety.md` — 4 DEFERRED sink rows (operator-domain + approval-artifact gate, `shell=False`, labeled
  not-shipped-runnable; `_SHELL_TRUE_ALLOWLIST` untouched so `test_exec_safety` stays green) + `protocol/iac-safety.md` §9
  Tier-2 contract (Tier-1 §1–§8 untouched). **(D)** `skills/coordinate/kata-orchestrate` (v0.1.0→0.2.0) — the Tier-2 apply
  state-machine in the IaC region, slotted AFTER Tier-1's escalate verdict; park-never-auto-apply via `escalation`; STOPS
  at `READY_DEFERRED`; sibling artifact only (Tier-1 `.kata/iac.json` + the D111 fail-closed re-classification byte-for-byte
  untouched). **(C)** `skills/execute/kata-iac-terraform` + `kata-iac-cloudformation` (both v0.1.0→0.2.0) — Tier-2
  preview/capture sections at the Tier-1 boundary markers, DRY-pointing to §9. **Freeze-gate caught (HOLD→SHIP):** **F2**
  a real ownership contradiction (Slice D bumps a skill version → README-sync fails, but README was owned by another
  slice) → README regen centralized to the conductor's integration gate (no slice owns/regens README; per-slice validate
  is read-only + tolerates the expected out-of-sync); **F1** the capability grant was NOT self-binding to the plan hash
  (safety rested on a separate call + artifact co-location) → made `capability_gate_verdict` itself assert
  `grant.approvedPlanHash == computed_plan_hash` (+ a dedicated mutation target); **F3** CFN bound only the `Changes` array
  → bind the FULL `describe-change-set` (ARN/stack inside the hash) + a dedicated `fullmatch` ARN grammar. **D98 PART B
  SHIP with NO must-fix** — the FIRST zero-fail-open build this session: every bypass attack failed CLOSED (no-grant,
  empty/partial authorized set, **stale grant bound to a different plan hash**, missing token → all `CAPABILITY_REQUIRED`;
  TF one-byte / CFN ARN-swap → `APPROVAL_INVALIDATED`; injection [`;`/`|`/`..`/`://`/leading-`-`/`-target`/`-auto-approve`/
  `$(...)`] all rejected; `run_apply` raises before any subprocess). 3 nice-to-haves recorded, deferred (all fail-SAFE on
  the never-run path): `approval_verdict` returns `PENDING_PLAN` vs `BLOCKED` on a non-dict approval; a redundant CFN argv
  flag; N1 inherited stateful-set completeness (fix belongs in `iac_detect`, already documented §9.5). **Gates:** pytest
  **1261** (1175→1261), validate **45/0** (no new skill — 3 version bumps), Snyk **0** on `iac_apply.py`. **Honest scope:**
  the entire apply path is **n=0-live / creds-gated / DEFERRED** — loudly labeled across the module, both specialists, §9,
  and all 4 exec-safety rows; nothing claims apply "works." **Tier-2 live-apply EXECUTION** remains future-gated on
  operator-authenticated cloud creds (its own session). Records: `specs/iac-live-apply/PLAN-tier2-preview.md`. **Meta:** on
  the single most destructive feature in the project, the freeze-gate caught 3 real defects (one self-binding-safety gap)
  and D98 found zero residual fail-opens — the catastrophic invariant (no reachable cloud mutation) is enforced **by
  construction** (no subprocess; the seam raises), which is why this was the cleanest D98 pass of the session.

<!-- second-brain-learning Recall (the READ contract + files-only adapter, v1). Spec: specs/second-brain-learning/PLAN-recall.md. Fully subagent-driven. -->
- **D120 — second-brain-learning: the Recall read-CONTRACT + a files-only default adapter (v1) BUILT — 2026-06-29.**
  Queue item (d). The READ side of the loop's cross-run learning, finally naming the long-reserved `engram.backend`
  CONSULT seam (D9 engram-backlog / D30 clean-room backend / D99 the Recall(Librarian)+Reason(decider)+Second-brain
  model). Per operator decision, scoped to the **Recall read-CONTRACT (the interface) + a FILES-ONLY default adapter** —
  **DEFER** external second-brain stores (Obsidian/kiban/kagami = downstream adapters behind the same contract), the
  **`kata-reason` decider** (separate future grill), and the **write/distill half** (already emit-only via the β LEARN
  feed, D74 — NOT re-opened). Operator calls: (1) scope = contract + files-only adapter; (2) selection = tag/keyword
  overlap (hard >0 predicate) + recency-ranks, ALWAYS surface open validation-miss recurrences, **NO embeddings/RAG**;
  (3) output = a structured payload rendered into a recall BRIEF in the `kata-initiate` Phase-2 mirror, **NEVER written
  into the frozen/pinned INTENT**; (4) staleness = surface provenance + date, prefer recency, **do NOT hard-filter**.
  Built **entirely through the loop/subagents**. **Resumed cleanly after a session-token-limit cut the freeze-gate
  re-confirm mid-verdict** — re-ran a FRESH freeze-gate: **HOLD→SHIP** (B1 the contract risked being secretly
  files-only-shaped → pinned `source`/`backend`/`produced_by` as OPEN shape-validated strings + an external-adapter
  acceptance test; B2 the validator-registration precedent was wrong [validation-misses.md is NOT in REQUIRED_PROTOCOL;
  engram.md IS, D74 BP2] → register recall.md + give R2 the validate_skills.py line; N1 hard-overlap predicate; N2
  sub-threshold note; N3 project out raw evidence; + 2 ownership-map reconciliations [add validate_skills.py to R2's DAG
  entry; README is conductor-owned not slice-owned, per the F2 convention]) → 3-slice 2-wave build → `kata-evaluate`
  **PART A PASS** → **D98 PART B SHIP**. **Built:** **(R1)** `tools/recall.py` — the PURE engine: `recall_payload_schema`
  (THE contract — validates SHAPE [keys+types] NEVER a closed vocabulary; the deliberate OPPOSITE of
  `validation_misses.miss_schema`/`validate_miss`'s hard `severity`/`what_caught_it` enums — `source`/`provenance.backend`/
  `provenance.produced_by` are OPEN adapter-supplied labels so an external Librarian implements the contract WITHOUT
  re-contracting), `validate_payload`, the files-only `recall_from_paths` adapter (the six sources), `select_records`
  (hard token-overlap>0 predicate; recency only RANKS among passers; recurrences bypass selection; **no embeddings/RAG**,
  asserted by a source-scan over 15 vector/LLM libs), `parse_lessons/decisions/intent/understand`, `match_score`/
  `token_overlap`, `_guard_path` (CWE-23); `RecurrenceRecord` projects out the raw `evidence` (the 7-field projection —
  no `what_conformance_missed` miss-text reaches the payload/brief); staleness surfaced-not-filtered. **No exec sink, NO
  WRITE PATH** (pure reads → returns a dict); 7 mutation proofs (incl. the overlap predicate, recency-ranks-not-filters,
  the open-contract strings, evidence-projection). **(R2)** `protocol/recall.md` (NEW — the read-side interface contract,
  mirrors the B1 open-vocabulary rule so external adapters know they may use own labels) + `protocol/engram.md` pointer
  section (names Recall as the read-side of `engram.backend`; explicitly does NOT activate the gated CONSULT decider
  [`kata-reason` deferred]; the 6 engram required terms preserved) + `tools/validate_skills.py`
  `REQUIRED_PROTOCOL["recall.md"]` (terms: `schema_version`/`recall/v1`/no-embeddings/INTENT-never-written/read-only —
  each verified present in recall.md; the engram/D74-BP2 precedent). **(R3)** `modules/initiation/kata-initiate`
  v0.1.0→0.2.0 — Phase-1b builds the payload via `recall.recall_from_paths` + renders a short RECALL BRIEF (open
  recurrences first, then matched records with provenance/date/`stale`; the N2 honest note that surfaced recurrences are
  the actionable over-threshold subset and sub-threshold misses may exist) + a Phase-2 "2a-recall" subsection surfacing
  the brief as **read-only recall context** (displayed, never stored). **The INTENT-never-written invariant is
  STRUCTURAL, not procedural:** `recall.py` has NO write path of any kind; `intent_scaffold.write_intent` (fed only by
  the operator-confirmed `answers` dict) stays the SOLE INTENT writer; the brief informs the mirror/grill and never
  enters `answers`. **Read-only:** Recall changes no gate verdict, auto-acts on nothing, mutates no surface, re-decides
  no LOCKED decision (engram C2/C4/C6). **Degradation:** absent sources (no recurrence-handled.jsonl etc.) contribute
  `[]` — Recall does NOT depend on the unbuilt recurrence-hardening T2 runtime. **Honest scope:** the decider +
  write/distill half are NOT activated (deferred to their own grills); external stores are deferred adapters behind the
  same contract; the contract-vs-files-only-adapter separation is the load-bearing design (proven by the
  external-adapter acceptance test). **Gates:** pytest **1310** (1261→1310), validate **45/0** (no new skill —
  kata-initiate version-bumped; `check_protocol_schemas` green for the new recall.md), Snyk **0** on `recall.py` +
  `validate_skills.py`. **Deferred MINORs (D98 nice-to-haves, NOT built):** a min-token-length(2) doc note in recall.md
  §2; a `query.kind` schema `open:True`/comment (the `values` key is advisory — validation is type-only by design).
  Records: `specs/second-brain-learning/PLAN-recall.md`. **Meta:** the session-limit interrupt was resumed cleanly (no
  half-built code; only the uncommitted plan awaited its verdict) — a fresh freeze-gate re-derived the same SHIP after
  the fixes; D98 found zero must-fix (2nd clean pass of the session), the read-only/no-write-path invariant holding **by
  construction** (like IaC Tier-2's no-subprocess seam) being why.

<!-- D108 codex adapter live-hardened + multi-model layer confirmed LIVE (n=0->1). Queue item (e) step 1. -->
- **D121 — Codex adapter live-hardened; the multi-model dispatch chain confirmed LIVE (n=0→1) — 2026-06-29.** Queue
  item (e), step 1. The operator installed **Codex CLI 0.142.3** (ChatGPT-authed) locally, lifting the 2nd-platform
  install gate that had blocked the multi-model benchmark. The **first live exercise of the D108 dispatch/probe/confirm
  chain** (built stub-only; D108 honest scope = n=0 live) immediately surfaced a real defect — exactly the class only a
  live run can catch: codex-cli 0.142.3 (a) refuses to `codex exec` outside a trusted git dir without
  **`--skip-git-repo-check`** (`"Not inside a trusted directory…"`), and (b) **blocks reading instructions from stdin**
  when the runner leaves stdin open → the harness confirm-probe hit its 120s timeout. **Diagnosed + fix verified live**
  (`codex exec --sandbox read-only --skip-git-repo-check "<prompt>"` with stdin closed returns the `SSENRAHATAK` token in
  ~6s) **before touching code.** **Fixed (4 surgical edits, TDD, subagent-driven):** (1) `kata_dispatch.codex_command`
  adds `--skip-git-repo-check` (order: `exec`→skip-flag→`--cd`…); (2) `kata_install._PROBE_COMMANDS["codex"]` adds the
  same flag; (3) `kata_dispatch._subprocess_runner` and (4) `kata_install._real_probe_runner` pass
  `stdin=subprocess.DEVNULL`. The kiro builder/probe are untouched; the `--sandbox` policy logic is unchanged; **no new
  exec sink / no `shell=True`** (a fixed flag on an already-registered structured-argv sink + a stdin kwarg) — the N5
  confirm-probe is the standing guard the BRIEF anticipated for stale per-CLI flags between releases, and it did its job.
  Tests: `test_codex_command_has_skip_git_repo_check`, `test_subprocess_runner_closes_stdin`,
  `test_codex_probe_command_has_skip_git_repo_check`, `test_real_probe_runner_closes_stdin` (the stdin ones patch
  `subprocess.run` and assert `stdin is subprocess.DEVNULL`); the L-MP2 `_PROBE_COMMANDS ⊆ _COMMAND_BUILDERS` invariant +
  all kiro tests stay green. **Live confirm now PASSES:** `kata_install.py --platform codex --confirm` →
  `{"confirmed": true, "detail": "probe ok", "confirmedPlatforms": ["codex"]}` — the D108 multi-model layer (read-only
  validator/researcher routing; coder-routing + evaluator-thresholds still DEFERRED per D108 LD11/MM-1) is **LIVE-proven
  on a real 2nd platform for the first time.** **Gates:** pytest **1314** (1310→1314), `kata_dispatch.py` Snyk **0**.
  **Pre-existing observation (NOT fixed — flagged):** `kata_install.py` carries **6 LOW** CWE-23 path-traversal Snyk
  findings in its `..`-guarded path-handling code (`_safe_abs`/`_default_home`/`_flat_link_skills`/`_link_or_copy`/
  `copy_project`) — present since D104/D108, untouched by this fix, below the project's medium+ gate; a candidate for a
  separate hardening pass (the `..`-guards are the intended mitigation; Snyk flags them Low regardless). **Honest scope:**
  this validates the dispatch/probe/confirm path live; the `kata-loop-benchmark` itself is still unbuilt (e step 2) and a
  real multi-model *benchmark run* awaits it. Meta: queue item (e) delivered its first real value not as a benchmark run
  but as a **live-caught adapter bug** — the n=0→1 transition is where stub-tested integrations meet reality.

<!-- Adversarial validation (ad-val) of the D117-D121 arc + targeted fixes. Cross-cutting holistic red-team (D111 pattern). Fully subagent-driven. -->
- **D122 — Adversarial validation (ad-val) of the D117–D121 arc + targeted fixes BUILT — 2026-06-28.** The cross-cutting
  holistic red-team of the 5-build arc — the **between-build seams** the per-build D98s structurally could NOT see —
  mirroring the D111 pattern. **5 parallel fresh-context opus reviewers** (one per seam-cluster: shared kata-orchestrate
  composition · shared validation_misses.py BC · exec-safety registry · multi-model live surfaces · honesty/no-write
  invariants cross-build) → synthesis → **operator-gated fix scope** → workers (TDD, mutation-proof) → integration gate →
  **fresh-context D98 re-confirm (all 4 fixes SOLID)**. Built **entirely via subagents** (operator directive).
  **Headline: NO BLOCKER, NO invariant-defeating MAJOR** — every D117–D121 structural invariant **survives cross-build
  composition** (verified at code level: recall's evidence-projection is airtight; no `finding_id` collision across
  debug_report/iac_apply; `run_apply` unconditionally dead, no subprocess import; the L-MP2 `_PROBE_COMMANDS ⊆
  _COMMAND_BUILDERS` invariant holds + is tested; kiro untouched by the codex fix; the confirm-token can't false-pass via
  prompt-echo; the 6 LOW CWE-23 install guards are sufficient for the trust model). ~11 MINOR/NIT findings, mostly
  latent/prose/doc. **FIX-NOW scope (operator-gated, 4 clusters + 1 cosmetic):** **(1) MAJOR escalation-clobber** — a
  Tier-2 apply park could overwrite the Tier-1 `escalate` artifact (`.kata/escalations/<task-id>.json`) for the **same
  task** on the stateful-destroy-apply path (the one scenario Tier-2 exists for), silently losing one of two
  human-required reasons; a D110(Tier-1)↔D119(Tier-2) seam. Fixed at **BOTH layers**: `kata-orchestrate` made explicit
  that a Tier-1 `escalate` **parks-and-returns** (Tier-2 reached ONLY for a task that cleared Tier-1) + `escalation.py`
  `write_escalation` gained a **fail-closed non-clobber guard** (refuses to overwrite an OPEN escalation with a different
  `decisionNeeded`; idempotent same-decision rewrites + status→resolved updates still allowed; 2 mutation proofs).
  **(2) honesty-fail-open** — `debug_report._snyk_rollup` now floors `effective_new = max(0, …)` (a negative
  `newFindings` artifact deflated the advisory regression total; could NOT flip `clean`; floor + mutation proof).
  **(3+4) doc-truth drift on standing-guard contracts** — `protocol/validation-misses.md` corrected 9→10 fields (adds
  `run_id`); `protocol/exec-safety.md` `kata_install` row corrected to name the **real** sink (`_real_probe_runner`, the
  confirm-probe — the D121-modified one; the old row described a nonexistent "install command"). **(5) exec-safety
  registry COMPLETENESS made structural** — new `test_every_subprocess_sink_module_is_registered` asserts every
  `tools/*.py` subprocess-sink module appears in the registry (was human-enforced only; the mis-described row was a live
  instance). Plus the #12 cosmetic stale-pointer fix in kata-orchestrate. **DEFERRED (per D111 anti-over-fix):** the
  latent/prose findings (coarse-`ts` distinct-run collapse window; the "every mode" recurrence-detector overclaim given
  its placement in the skippable red-team; the proposed→guarded prose-only backstop; the kata-onboard `.planning/`
  scaffold clobber hazard; confirm-probe validates the platform-CLI not the routed-model; `stdin=DEVNULL` runner-wide) +
  2 D98-re-confirm nice-to-haves (`escalation.py` raises a confusing parse error on a corrupt existing escalation file
  [fail-CLOSED, untested]; the completeness test's substring-module-match + `subprocess.`-prefix-only sink detection
  [zero active miss]). **Validation-misses:** the 3 genuine fail-opens (#1/#2/#5) logged to
  `.planning/validation-misses.jsonl` (`run_id` `d122-adval`, `what_caught_it:d98`). **NOTE:**
  `kata-debrief × honesty-fail-open` is now at **2 distinct runs** (D117 Snyk-masking + this negative-floor) — **1 short
  of the T2 auto-proposal threshold**; the LD12 honesty engine is a recurring fail-open surface the recurrence loop is
  now watching. **Gates:** pytest **1324** (1314→1324, +10 tests), validate **45/0** (README regenerated), Snyk
  **medium+ 0** on all changed Python. **Meta:** the cross-cut found the between-build seams genuinely held — the arc was
  partitioned into disjoint regions/artifacts; the only MAJOR was a Tier-1↔Tier-2 escalation-artifact seam, exactly the
  class a per-build review cannot see; and the D98 re-confirm found **zero** new fail-open in the fixes (no over-fix
  spiral). Records: `.planning/specs/` (no new spec — fixes to existing surfaces); the ad-val itself was the deliverable.

<!-- kata-loop-benchmark v1 (the D99 C-arc keystone) BUILT. Spec: specs/kata-loop-benchmark/{RESEARCH,DESIGN,PLAN}.md. Fully subagent-driven; autonomous full-recipe run. -->
- **D123 — kata-loop-benchmark v1 BUILT (the D99 C-arc keystone) — 2026-06-29.** Queue item (e) step 2. The deterministic
  outcome+efficiency benchmark for the loop — the keystone that measures **C-on/C-off learning lift** (D99 tumbler #4).
  Built **entirely via subagents** through the full recipe, executed **AUTONOMOUSLY at operator request**. Research
  (SWE-bench code-level review + deep web research, wf_7f373992-209) → `RESEARCH.md` (operator grill RESOLVED:
  control-anchored 2-axis metric, hidden module, replay-by-definition) → planning subagent `DESIGN`/`PLAN` → **freeze-gate
  `kata-review` HOLD→SHIP** (caught a dual-gate RCE seam: F2P/P2P now run as **test-IDs-as-DATA** via
  `mutation_check.run_named_test` `shell=False`, NOT `run_gate`) → 6-slice / 5-wave build → integration gate →
  `kata-evaluate` **PART A PASS** → **D98 PART B HOLD** (1 BLOCKER + 2 MAJOR + 3 MINOR, all proven by running the code) →
  fix (Wave-1 engine ∥ Wave-2 wiring) → **re-confirm D98 SHIP** (all 6 reproduced fixed; new-break sweep clean).
  **Design (operator-shaped):** the benchmark is an **EXPERIMENTAL CONTROL** — an immutable reference (code repo or
  research project) **cloned per run** into `<base>-katabenchmark<N>`; **rigidity = the control** (identical start+inputs
  across arms), not the metric. **Two-axis scorecard:** Axis Q (floor-gated default-FAIL + SWE-bench-style dual-gate
  F2P/P2P + mutation multiplier; **floor-fail ⇒ Q=0 absolute**) × Axis C (tokens/$/wall-clock/tool-calls/escalations/
  thrash — host-dependent fields honestly **nullable**); **floor-gated composite** (Pareto point + scalar `Q/(1+λ·C_norm)`,
  efficiency scored **ONLY among floor-passers** so a cheap-wrong answer never wins; profiles `balanced|cost-lean|
  quality-strict`). **Content-pinned Benchmark Definition + `repeat_from` + delta mode** (same-definition / newer-provenance
  = honest harness-delta = the C-on/C-off number). **Hidden off-by-default `benchmark` module** (NOT in bootstrap). Two-tier
  report skill mirrors `kata-debrief`; **reports never gate**; n=1 directional honesty. **Built (6 PURE-engine slices, no new
  DIRECT exec sink):** (S1) `tools/usage_meter.py` (Axis-C metering → `.kata/usage.json`; the CONFIRMED net-new dep — the
  harness persisted no per-arm tokens/cost); (S2) `tools/benchmark.py` (the deterministic scorer; pure engine + a thin
  `run_dual_gate` that runs test-IDs-as-data via the existing `mutation_check` sink); (S3) `tools/benchmark_def.py`
  (Definition + `repeat_from` [no network] + `compute_delta`); (S4) `tools/benchmark_control.py` (immutable-ref clone +
  `content_hash` + drift + prune; ref never written); (S5) `skills/evaluate/kata-benchmark-report` (two-tier report author,
  drives `benchmark.py`); (S6) `protocol/config.md` (module row + config block) + `kata-orchestrate` wiring (module-gated,
  BC, arm-map assembly, D1 deferral). **D98 caught REAL fail-opens PART A missed (the load-bearing value):** **(BLOCKER)**
  the dual-gate runner was **orphaned** — never wired → `score_arms` ran with no gate data → **every floor-passing arm
  scored Q=1.0; the quality axis was non-functional** (PART A tested `score_arms` in isolation with injected booleans, so it
  passed) → wired `run_dual_gate` per arm + engine now flags `dual_gate_evaluated:false` / no-free-credit; **(MAJOR)**
  `run_dual_gate` joined external-trust control test-IDs without a `..`-guard → pytest code-exec → added `_guard_node_id`
  (reject `..`/escape/leading-`-`) + registered the external-field sink in `exec-safety.md`; **(MAJOR)** the report skill
  cited phantom scorecard fields incl. a **fake "engine-pinned honesty block"** → made `honesty`+`recommendations` REAL
  engine fields + skill cites only real fields + fixed reversed `emit_scorecard` arg order. **3 integrity MINORs fixed:**
  `content_hash` path‖bytes collision (length-prefixed), floor partial-RESULT fail-open (require present `failed==0`),
  `build_usage` negative-value gaming (reject negatives). All TDD + mutation-proven. **Validation-misses:** the 3
  D98-caught fail-opens (BLOCKER+2 MAJOR) logged (`run_id` `d123-benchmark`). Also fixed a **stale test**
  (`test_logged_misses_stay_valid_and_known` asserted `run_id` absent — broke when D122 logged run_id'd misses; now allows
  the nullable `run_id`) + the residual freeze-gate **name-drift** (`exec-safety.md` `run_test`→`run_named_test`).
  **DEFERRED (named, phased):** **D1** concurrent bakeoff arms (gated on Spec B execution — NOT built; v1 ships the
  **sequential/single-arm + k-repeat** path + the arm-ranking scorer); **D2** research-mode judge; **D3** benchmark→
  `kata-improve` T2 optimization-proposal sub-mode (config-defaults + routing-tables; propose-never-apply); **D4**
  promotion (promote-best-arm-to-master, real-repo only); **D5** the real control FIXTURE (operator-supplied; design is
  fixture-agnostic). Plus 1 residual NIT (floor accepts `failed:0.0`/`False` — internal-trust robustness edge). **Gates:**
  pytest **1536** (1324→1536, +212 build+fix tests), validate **46/0** (new skill `kata-benchmark-report`; README regen),
  Snyk **medium+ 0** on all new/changed Python. **Honest scope:** **n=0 LIVE** — proven on synthetic fixtures + unit tests,
  never run end-to-end on a real control repo (D5). **COMMITTED-LOCAL; PUSH HELD** for operator return (the standing
  commit/push gate — built autonomously while the operator was away). **Meta:** D98 again caught real fail-opens PART A
  passed — the orphaned dual-gate is the starkest this session (a whole axis conformance-green yet non-functional); the
  freeze-gate caught the dual-gate RCE seam *before* build; the autonomous full-recipe run held the
  grill→freeze→freeze-gate→build→eval→D98→re-confirm discipline end to end. Records:
  `specs/kata-loop-benchmark/{RESEARCH,DESIGN,PLAN}.md`, `DECISIONS.md` D123.

<!-- Deep adversarial validation of the D123 benchmark build + integration-completion + metric-hardening. Operator-requested pre-push. Fully subagent-driven. -->
- **D124 — Deep adversarial validation of the benchmark build + integration-completion + metric-hardening — 2026-06-29.**
  Operator-requested **deep ad-val** of the D123 benchmark build *before push* ("check the agents' work — end-to-end
  applied properly, no loose ends, no overcomplication, no drift"). **5 parallel fresh-context opus reviewers** (E2E
  integration dry-run · drift vs DESIGN/PLAN/STANDARDS · overcomplication/loose-ends/dead-code · deep adversarial
  correctness · prose/skill coherence) → synthesis → **operator-gated fix scope** → 6 fix workers (TDD/mutation, 2 waves)
  + 1 delta-identity fix → **re-confirm (3 reviewers resumed) → all CLEAN/SHIP**. **Headline:** the engine SLICES were
  unit-solid (no drift; lean/idiomatic; no phantom *function* citations; the D123 fixes held under re-attack) — but the
  **INTEGRATION + RENDER + METRIC-INTEGRITY** layers had ship-blocking gaps the unit-level gates (PART A + D98)
  **structurally could not see**. As built, D123 would have: **(1)** scored **every REAL control Q=0** (the dual-gate ran
  a control's tests with no `cwd`/import-context → `from src import X` fails collection → Q=0 despite floor PASS); **(2)**
  **never produced its replay-definition** (`build_def`/`write_def`/`content_hash` unwired; `def_out` required-but-never-
  written); **(3)** failed to **resolve criteria** (`criteria_ref` produced-never-consumed; no loader); **(4)** failed to
  **render its report** (the `{{BENCHMARK_*}}` tokens didn't exist in the closeout template → broken page); **(5)** let an
  arm **WIN the ranking** via a negative/NaN `costUSD` or by omitting its worst Axis-C dimension (the D98 non-negativity
  guard was on the *writer* not the *reader*; FIX-6b exclude-from-mean was an over-fix); **(6)** **mis-fired delta-mode**
  (fresh `benchmark_id` per run → `sameDefinition` always False → false "definition drifted" on every honest repeat).
  **Fixed (D124, all TDD + mutation-proven, gates green throughout):** **A1** dual-gate exec context (`mutation_check.run_named_test`
  gained `cwd` [BC] + `run_dual_gate` passes `cwd=clone_root`+PYTHONPATH → **proven Q=0→Q=1** on an importing fixture;
  honest scope: nested-`uv-run` is environment-sensitive — green canonically; full per-control dep-env isolation is a
  D5/real-fixture concern). **A2/A3** wiring: `content_hash`→`build_def`→`write_def(def_out)`; new `.kata-benchmark/criteria.json`
  schema + `load_criteria`→`run_dual_gate`; `benchmark_id`/`provenance` stamped; durable scorecard co-located via
  `emit_scorecard`; `repeat_from`→`resolve_repeat_from`→`compute_delta`. **C1/C2** metric integrity: read-path
  `_validate_numeric` (`isfinite & >=0`; invalid→missing+`usage_incomplete`); **worst-case imputation** replaces
  exclude-from-mean (omitting your worst dim no longer wins; an honest null-token host is penalized once, conservatively);
  `build_usage` rejects NaN/inf — **re-attack confirmed both gaming vectors DEAD, over-fix sweep CLEAN**. **A4** k-repeats
  honest-simplify (operator decision (b)): per-repeat rows, mean±spread **DEFERRED**, cross-repeat dominance suppressed;
  DESIGN §6b superseded with an **explicit R6-no-drift confirmation**. **A5** cost wiring: `default_rate_table()` +
  `cost_from_rate_table` → `costUSD` populated (was always null; rate table is a v1 placeholder, override-able). **B1–B5/A6**
  render: NEW **`benchmark-report.template.html`** (BRAND-consistent — Hokusai palette/tiles/logo, 10 tokens 1:1,
  self-contained); tile mapping fixed; C-fields-from-`usage.json`; `usage_incomplete` rendered; footprint de-claimed;
  "no-write renderer" dropped. **Delta-identity:** repeat = **same `benchmark_id`** (`sameDefinition:true` → honest
  harness-delta); `parent_benchmark_id` is fork-only; delta activates on `repeat_from`/`sameDefinition` (NOT
  `parent_benchmark_id`) — resolved a schema tension across orchestrate/report/`def_schema`. Cleanup: registered the
  `integration` pytest marker; dead vars cut. **Re-confirm:** R1(e2e) **CLEAN** (full path + `repeat_from` delta
  reproduced), R4(correctness) **SHIP** (over-fix sweep clean), R5(prose) all named fixes good; the A1 integration test
  verified **green in the canonical env** (R4's sandbox failure was nested-`uv-run` env, not a regression). **★ ACTIONABLE
  RECURRENCE (the system caught itself):** `kata-orchestrate × phantom-reuse` reached the **BLOCKER-tier threshold** (2
  distinct runs: D123 orphaned-dual-gate + D124 unwired-chain). **T2 auto-drafted `.planning/PROPOSAL-phantom-reuse.md`**
  (proposed standing guard: an **end-to-end WIRING-COMPLETENESS gate** — trace the whole flow on a realistic fixture +
  a produced-vs-consumed sweep; PART A + D98 unit/injected **cannot** see built-but-unwired seams) → marked `proposed` in
  `recurrence-handled.jsonl` → routes to freeze-gate `kata-review` → **human merge**. **T2 invariant held (proposed, never
  applied).** **Validation-misses:** 3 deep-ad-val fail-opens logged (`d124-deepadval`). **Meta-lesson (load-bearing):**
  the per-build gates test units + injected data; **built-but-unwired + execution-context + metric-read-path gaps need an
  end-to-end dry-run with a realistic fixture** — now a *proposed* standing gate. **Gates:** pytest **1597** (1536→1597,
  +61), validate **46/0**, Snyk **medium+ 0**. **Honest scope unchanged: n=0 LIVE** (the real control fixture is D5,
  operator-supplied). **COMMITTED-LOCAL; PUSH** (b90a8a2 freeze + 72c1b8f D123 + this D124) **HELD for the operator
  commit/push gate.** Records: `specs/kata-loop-benchmark/{RESEARCH,DESIGN,PLAN}.md` (DESIGN amended), `DECISIONS.md` D124,
  `PROPOSAL-phantom-reuse.md`.

<!-- kata-validate: the always-available validation mini-loop. Spec: specs/kata-validate/. Fully gated. -->
- **D125 — kata-validate BUILT: the always-available validation mini-loop — 2026-06-29.** A NEW EVALUATE-family
  skill `skills/evaluate/kata-validate/SKILL.md` (v0.1.0, category `evaluate`, status experimental, cost-weight 3,
  `kata/spine` tag) exposing a **programmatically-callable validation mini-loop**:
  `validate(payload, target="auto", profile) -> Report{passed, findings[]}`. **LOCKED decisions:** **(1)
  Always-available, NOT a module** — callable inline on ANY data, **dual-target** (arbitrary content OR another
  agent's output), with **payload-as-data isolation** (injection containment: the payload is graded, never obeyed).
  **(2) Requires NO runtime freeze/INTENT/`kata.config`** — a defining property; it validates inline data with zero
  loop scaffolding (the conformance `score` leg is conditional — N/A when no plan exists). **(3) Method-by-reference
  reuse** — 4 deterministic-first legs CITE the existing methods rather than re-implement: `grounding`
  (`kata-evaluate` injected-knowledge + grounding_gate) · `review` (`kata-review` 5-surface RUBRIC) · `slop`
  (`kata-slop-check` G1–G6/A1–A3) · `score` (`kata-evaluate` conformance, conditional). **(4) Own thin conductor,
  NOT `kata-orchestrate`** — a composition-wrapper (the `kata-loop`/`kata-onboard` precedent); `kata-orchestrate`
  is **byte-for-byte untouched**. Bounded **≤2 passes**; optional RS research method for grounding; a branded
  "Running KataHarness validation loop…" banner. **(5) Report-only by DEFAULT + per-finding human-gated fix via a
  single writer** — validators stay no-write; one sole Write actor applies a fix only on a per-finding human gate.
  **(6) Safety rails:** a **tripwire** corpus + a **cross-family-judge** (honest weaker same-host fallback). **Built:**
  NEW PURE engine `tools/validation_report.py` (findings schema · SARIF severity error/warn/info · `render_table`
  with an explicit N/A-row guard · `..`-guarded `emit`/`load` of `findings.json` · **default-FAIL** `compute_passed`
  · `tripwire_corpus` + `assert_tripwire_flagged`; **no exec sink**) + tests + tripwire fixtures; ADDITIVE
  `tools/kata_banner.py` (`render_validation_banner` + a `--validation` CLI flag); README regen (**47 skills**).
  **Gate journey:** freeze-gate `kata-review` **HOLD** (reuse-as-module-dispatch would self-no-op — built-but-unwired
  risk) → fixed in the frozen docs → **SHIP**; **live end-to-end wiring proof WIRED** (clean payload byte-identical ·
  known-bad flagged **6 errors across 3 surfaces** · injection **flagged-not-obeyed**; n=1 exercised); `kata-evaluate`
  **PART A PASS**; **PART B `kata-review` HOLD twice → SHIP**. **★ Two fail-opens PART A + the unit tests missed,
  PART B caught (the default-FAIL/gate-escape class):** **(F1)** `validation_report.severity_of` was case-sensitive —
  `ERROR`/`Error`/`REJECT`/`ESCALATE` fell through to `info`, so `compute_passed` returned **True on a real error
  finding** (a default-FAIL escape) → fixed: case-normalize + synonym map + a mutation-proof test. **(F1b)** that
  band-map fix was a half-measure — `slop-detected`/`needs_work`/`hold` tokens + slop major/minor severities still
  slipped to `passed=True`, violating `kata-slop-check` LOCKED **L2** ("SLOP-DETECTED fails regardless of severity")
  → fixed: full `§10-2` verdict-token coverage in the engine + the conductor contract (writer stamps `hold:true`) +
  a major-slop fixture. **Meta-lesson:** the unit-test layer under-covered the fail-open class; the standing
  adversarial review caught it — both logged (`d125-kata-validate`). **Gates:** pytest **1680** (+84: 78 engine +
  6 banner), validate **47 skills / 0**, Snyk **medium+ 0**. Records: `.planning/specs/kata-validate/`, `DECISIONS.md`
  D125, `validation-misses.jsonl` (F1/F1b).
- **D126 — Feature 2 BUILT: install/onboarding final polish (one-command + headless + grill-for-goals + router
  stanza) — 2026-06-29.** The install/onboarding surface is finished off in four gated slices, **ADDITIVE and
  backward-compatible throughout** — the **5 `tools/kata_install.py` install-engine functions are byte-for-byte
  untouched** and **no working pattern is altered**. **LOCKED decisions:** **(G1) Cross-platform one-command +
  GitHub install** — NEW repo-root `install.sh` (`curl|sh`) + `install.ps1` (`irm|iex`) + `uninstall.sh` +
  `uninstall.ps1`; they clone/seed then **invoke the EXISTING `tools/kata_install.py` engine** (no engine fork);
  idempotent, no-cruft, **`KATA_SRC` offline override**; documents the clone path + "Use this template"; an
  **honest `curl|sh` security caveat** (the checksum protects download-then-run, **NOT** the pipe); an uninstaller
  ships. README + `docs/SETUP` updated. **(G2) Agent-friendly / headless install+setup** — ADDITIVE flags on
  `kata_install.py` (`--yes`/`--non-interactive`, `--answers-json`, `--json`, `--uninstall`, `--target-dir`) +
  non-TTY auto-skip; **SEMANTIC EXIT CODES** (0 ok / 1 not-confirmed / 2 usage / 3 not-found / 4 permission /
  5 conflict=non-kata-only); **idempotent re-install = 0 no-op** (no `changed` field — that would have forced an
  engine edit); machine JSON to stdout, human to stderr. **Autonomous-loop mode explicitly DEFERRED** — the build
  loop's commit/merge/fix gates stay human. **(G3) Grill-for-goals** — ADDITIVE optional `acceptanceCriteria`
  field in `intent_scaffold` (**byte-identical BC when absent; NOT required**) + a `protocol/intent.md` amendment;
  ADDITIVE `kata-initiate` **step 2g** (enumerate + confirm acceptance/success criteria — start-with-the-end-in-mind)
  + **S2 gate value #9** handled like conditional value #8 (an explicit "no criteria for this run" **PASSES** — no
  deadlock; the verbatim "blanket looks-good FAILS" rule is preserved; the gate is **STRENGTHENED, not loosened**).
  **(G4) Project-router stanza** — NEW pure `tools/kata_router.py` (`render`/`write`/`remove_stanza` — `..`-guarded,
  idempotent marked-block upsert between `<!-- kata:begin -->` / `<!-- kata:end -->`); `kata-onboard` (**v0.2.0**)
  gains an **opt-in, human-gated Step-3 item** that EXECUTES `kata_router.write_stanza` into the target project's
  AGENTS.md; the uninstaller removes **exactly that block**; stanza ~15 lines (instruction-budget). **Canonical
  AGENTS.md; CLAUDE.md stays a pointer** (D5). **Locked assessment:** the "system prompt" concept (persona SOUL +
  AGENTS.md-as-router + CLAUDE.md pointer) is **ALREADY SOUND** — no change beyond G4. **Build:** 7 disjoint slices
  in 3 waves (W1 `kata_router` + intent/initiate; W2 `kata_install` headless + uninstall; W3 `kata-onboard` stanza +
  bootstrap scripts + README/SETUP). **Gate journey:** freeze-gate `kata-review` **HOLD** (two real contradictions:
  a `changed:false` field would have FORCED an engine edit — dropped for the no-op-returns-0 contract; and the
  optional-field-as-gate-value **deadlock** on G3 value #9) → fixed in the frozen docs → **SHIP**; live **offline
  install / re-install / uninstall smoke ran on BOTH Git Bash and PowerShell**; **PART A `kata-evaluate` PASS**;
  **PART B `kata-review` SHIP** (6 minor findings). **Hardening pass folded in:** Finding 1 (a `kata_router`
  marker-corruption **data-loss guard** — see below), Finding 2 (headless `OSError` → exit 4), Finding 4
  (`render_stanza` summary test). **★ One validation-miss the unit tests missed, PART B caught (`stateful-hole`):**
  the `kata_router` marked-stanza upsert had a **data-loss state edge** — an unmatched/orphan `<!-- kata:begin -->`
  (no matching end) would, on the **2nd write**, pair the stray begin with the new block's end and **delete the lines
  between**. The unit tests covered the happy/complete-block paths but missed the orphan-marker state edge → fixed
  with a **fail-loud guard + a byte-identical-after-raise test**; logged (`d126-install-onboarding`). **Gates:**
  pytest **1764 passed** (new tests: `kata_router` + `install_cli_headless` + `intent_scaffold` additions),
  `validate_skills` **47 / 0**, Snyk **medium+ 0**, offline install/re-install/uninstall smoke green on **both
  shells**. **Honest scope:** (a) the known **D124 environment-sensitive benchmark test**
  (`test_benchmark.py::TestRunDualGateCwd::test_importing_fixture_gives_q_one`) is **green canonically (1764 passed)**
  but flaky in some subagent venvs — this is **NOT a Feature-2 regression and NOT a validation-miss**, noted only for
  honesty; (b) the `curl|sh` network-fetch path is **exercised, not proven** (the honest caveat above stands — the
  checksum guards the downloaded artifact, never the pipe); (c) **Codex/Kiro install is honest-scoped** (verify
  in-host). Records: `.planning/specs/install-onboarding/`, `DECISIONS.md` D126, `validation-misses.jsonl`
  (`d126-install-onboarding`).
  **Known rough edges (pre-existing / honest-scoped; NOT Feature-2 regressions):** (a) `write_settings` does
  not merge — an install with `--parent-dir` overwrites `.kata-settings.json` and drops any `confirmedPlatforms`
  (D121 multi-model confirm state); pre-existing in `kata_settings.py` (a NOT-TOUCHED working pattern);
  recoverable via re-`--confirm`; recommend a separate merge-preserving fix as a follow-up. (b)
  `intent_scaffold`/pyyaml is only available under `tools/` — `build_intent`/`write_intent` must run from
  `tools/`; the install path is stdlib-only and unaffected. (c) Windows-without-Developer-Mode uses copy-mode
  fallback (documented), so harness skill updates need reinstall to propagate.
- **D127 — write_settings MERGE-fix (install-update-polish item 3, the single working-pattern edit) — 2026-06-29.**
  `write_settings` now **MERGES** instead of clobbering: validate (unchanged, first) → strict fail-closed
  load-existing (new private `_load_existing` — fails closed on corrupt JSON AND valid-but-non-dict JSON; does
  NOT reuse lenient `read_settings`) → overlay owned keys (`settingsVersion`/`parentDir`/`vaultDir`) → preserve
  prior `vaultDir` when not re-supplied → preserve `confirmedPlatforms` + ALL unknown keys verbatim.
  **Denylist-of-owned / preserve-everything-else** (future keys safe by default). Kills the **D121 confirm-state
  clobber on `--parent-dir` reconfigure** and the sibling `vaultDir`-drop. **Strict BC:** all 13 prior
  `kata_settings` tests unchanged; **7 new non-tautological tests**; live reconfigure proof
  (confirmedPlatforms + vaultDir preserved, parentDir updated). **Process:** own freeze-gate **(SHIP)** +
  post-build adversarial review **(PASS)**. **Gates:** pytest **1772**, validate **47/0**, Snyk **0**. Files:
  `tools/kata_settings.py`, `tools/tests/test_kata_settings.py`. Spec:
  `.planning/specs/install-update-polish/FREEZE-write-settings-merge.md`. Supersedes nothing; precedes the
  install-update-polish update-system build (Phase A next).
- **D128 — install-update-polish Phase A (core update path) + hybrid update-system design ADOPTED — 2026-06-29.**
  Upstream base is immutable from the user's side → update is a clean overwrite; parametric local change →
  overlay store (Phase B); deep divergence → supersedes/fork (Phase C); factory-reset = drop overlay. Phase A
  is ALL ADDITIVE: the 5 frozen `kata_install.py` engine fns (`_flat_link_skills`, `_link_or_copy`, `install`,
  `copy_project`, `confirm_platform`) are **BYTE-UNCHANGED**; the never-git guarantee holds (all git in
  `update.{sh,ps1}`; engine fed only `--git-sha`). **A1** new pure `tools/kata_version.py` (`.kata-version`
  stamp + `.kata-manifest.json` content-hash + `is_pristine` + `suite_semver`). **A2** engine wiring
  (`--update`, `--factory-reset`/`--reinstall`, `--hard`, `--dry-run`, `--git-sha`; M1 plain-install stamp
  `gitSha:"unknown"` when absent; `_sweep_managed_slots` fail-closed orphan sweep; `_materialize_pass` no-op
  stub for B). **A3** `update.sh` + `update.ps1` bootstraps (git fetch/ref/reset; M2 dirty-tree guard
  abort-by-default + `--discard-local`; `--check` no-mutation; minor-c non-git-clone detection; `--hard`
  confirm-gated). **A4** `.gitignore` (`.kata-version`/`.kata-manifest.json`/`.kata-overlay/`) + `SETUP.md` §4
  + README. **Process:** design freeze-gate **SHIP** (M1–M4 folded) + per-task TDD + **LIVE PROOF 11/11**
  (real install→update→factory-reset→uninstall on scratch home+host; bootstrap→engine→`kata_version` chain
  WIRED, the D124 lesson) + post-build adversarial review **SHIP**. **Gates:** pytest **1844** (+2
  Windows-DevMode skips), validate **47/0**, Snyk medium+ **0** (`kata_install` 9 LOW CWE-23 operator-path
  class, below gate → standing hardening item). **Carried to Phase B:** wire a real `--ref` (stamp ref-field
  honesty — currently hardcoded `"master"`); split `_materialize_pass` out of `install`'s `except` before
  fleshing it. Specs: `.planning/specs/install-update-polish/{SPIKE-learning-overlay,DESIGN,PLAN}.md`. Phase B
  (overlay) + C (fork) next.
- **D129 — install-update-polish Phase B (overlay) + Phase C (fork/supersedes) — 2026-06-29.**
  Completes the hybrid update system: local adaptation lands as an OVERLAY (parametric) or a FORK
  (deep), never mutating the installed base. **Phase B — overlay layer:** B1 new STDLIB-ONLY
  `tools/kata_overlay.py` (overlay store `<home>/.kata-overlay/overlay.json` + M4 line-based
  frontmatter composer + `materialized.json`); B2 engine `_materialize_pass` — materializes
  overlaid skills into concrete host slots (markers `.kata-managed` + `.kata-overlay-materialized`;
  M3 missing-base fail-soft; split OUT of the stamp's `except` — no silent swallow); B3
  `kata-improve` local-adaptation mode (adaptation_context via `.kata-version`;
  `improve.allowUpstreamEdit` safety rail; edit-category→overlay/fork decision table); B4 `SETUP.md`
  overlay docs. **Phase C — fork/supersedes layer:** C1 new STDLIB-ONLY `tools/kata_supersede.py`
  (`resolve_shadows` + `validate_shadows` — fail-closed on unknown base / double-supersede); C2
  engine shadow precedence (fork > overlay > pristine; dormant-overlay NOTE;
  validate-STOPs-before-materialize; factory-reset un-shadows); C3 `kata-promote` shadow-binding
  note; C4 `STANDARDS` supersedes-now-wired note; `update.{sh,ps1}` `--ref` passthrough (stamp ref
  honesty, replacing hardcoded `"master"`). **KEY FIX — deployment blocker:** `kata_overlay` and
  `kata_supersede` are STDLIB-ONLY (no pyyaml) because the install/materialize path runs via
  `uv run`/plain-python from the home root where pyyaml is absent (pyproject.toml is at `tools/`,
  not root); without this, overlays/forks silently no-op'd in a real install. The
  "install path is stdlib-only" invariant now holds for the full materialize/shadow path. **Process:**
  per-task TDD; design freeze-gate SHIP earlier; LIVE PROOFS — Phase B overlay-materialize 15/15
  and Phase C fork/shadow 8/8, both in the real no-yaml `uv run`-from-home-root env; post-build
  adversarial review SHIP. Note: C2 had a premature-kill recovery (one agent wrote the `test_c2_*`
  tests, another wrote the impl; the review confirmed tests are sound, non-tautological, and
  satisfied). The 5 frozen `kata_install.py` engine fns remain BYTE-UNCHANGED; `kata_settings.py`
  untouched. **Gates:** pytest **1991** (+2 Windows-DevMode skips), validate **47/0**, Snyk medium+
  **0** (`kata_install` 17 LOW CWE-23 operator-path class, below gate → standing hardening item).
  **Deferred nits:** a stdlib-invariant comment at the shadow-path `ImportError` guard;
  stamp-written-before-materialize-raises on a failed structural-shadow install. Specs:
  `.planning/specs/install-update-polish/{DESIGN,PLAN}.md`. **NEXT:** cross-phase final gate +
  clean-install capstone, then operator merge/push gate.
- **D131 — relative, mode-driven model selection (model-tiering resolver, W3-B) — 2026-06-30.** Model resolved
  at dispatch as a **differential off the operator's session model (the anchor)**; skills carry no `model:`
  frontmatter (enforced by the A1 guard in `validate_skills.py`). **Folds R1–R8** (operator-approved; R1–R8
  supersede any conflicting text in `.planning/specs/model-tiering/ASSESSMENT.md`). Builds on **D130** (stripped
  hard-baked `model:` frontmatter, commit `8af2e37`) and implements the **D59 relative-routing note**.
  **Locked decisions (R1–R8):** **(R1)** Coder-floor monotonicity invariant — `essential-coding ≤ standard-coding
  ≤ anchor` at every anchor; coder-floor raises a coding tier only when `floor_index ≤ anchor_index − 1`, capped
  at standard's rung, never exceeds the anchor. **(R2)** Availability fallback: any non-inherited dispatch failure
  triggers a step-down (≤2 then OMIT the `model` param entirely — terminus is OMIT, never re-inherit a gated
  anchor); 401/403 surfaces as a real error, never silently downgraded. **(R3)** BC grounding: absent
  `kata.config.models` ⇒ `resolve()` returns `None` everywhere ⇒ inherit ⇒ today's single-model behavior
  byte-for-byte (confirmed for Claude host: omitting the `model` param inherits the session model). **(R4)**
  Ladders are plain string lists, not alias lists — `["haiku","sonnet","opus","fable","mythos"]`; fable and
  mythos are distinct models (mythos-gated is the live fallback test case); the alias-list model from ASSESSMENT
  is dropped. **(R5)** Work-class map covers **all 47 skills** — `skills/` AND the 3 `modules/` skills (`load_skills`
  counts both) — so economy tier-down fires; `unknown → critical` only for genuinely-new/unseen skills.
  **(R6)** Ladders live as DATA in `tools/kata_models.py` (deliberate v0.1 Claude-only core; agnostic-core
  adapter boundary is honest-scoped). **(R7)** Zero-step cells (advanced all-cells + standard-critical) inherit
  by omission — `resolve()` returns `None`/OMIT, never re-selects the anchor ID; only strictly-below-anchor cells
  return an explicit id string. This is the determinant: step-count, not work-class. **(R8)** Guard scope: A1
  re-introduction guard (`validate_skills.py` `check_model_in_skill_frontmatter`) ERRORs on any absolute `model:`
  in **SKILL.md frontmatter only**; adapters/config MAY still pin models (explicit carve-out); fallback step cap
  ≤2. **Architecture:** NEW pure-stdlib `tools/kata_models.py` — `FAMILY_LADDERS` data registry, `SKILL_WORK_CLASS`
  map (47/47 explicitly covered), `resolve(skill, mode, anchor, *, family, coder_floor) → id | None` (OMIT on
  zero-step or any uncertainty), `step_down()`, `family_of()`, `fallback_chain(id, family) → [id, …, None]`
  (≤2 entries then `None`). `kata.config.models` block (`anchor`/`family`/`coderFloor`) is BC-safe: absent ⇒
  all-`None` ⇒ today's behavior byte-for-byte. **W3-B gates:** pytest green (coverage test asserts every skill
  from `load_skills()` is in the map — count-agnostic, derives the set dynamically), validate 47/0 with A1 guard
  active, Snyk medium+ 0. Spec: `.planning/specs/model-tiering/{ASSESSMENT,DESIGN,PLAN}.md`.
- **D132 — restore-hardening + continuous-replay + Claude slash-command surface (Option 2) — DECIDED 2026-06-30;
  design PENDING (grill → freeze next session).** Does NOT supersede D131; it is the next initiative after v0.1.0
  ships. Two read-only assessments were run on 2026-06-30, both confirmed before the v0.1.0 tag was pushed:
  **(Assessment 1 — slash-command surface)** KataHarness ships **0** true Claude slash commands (the `/kata-*`
  in the README are skills rendered with a slash prefix, not `.claude/commands/` files). Gap = **discoverability**
  (a user typing `/` in the Claude UI sees nothing). Fix = a small set of THIN, pointer-only commands living in
  `adapters/claude/commands/` that each simply route to an existing skill (DRY-by-pointer — no logic duplication).
  Recommended 6 must-have: `/kata` (help/index — the one genuinely new artifact), `/kata-start` → kata-initiate,
  `/kata-onboard` → kata-onboard, `/kata-resume` → kata-orient / kata-handoff, `/kata-status` → kata-board,
  `/kata-validate` → kata-validate.
  **(Assessment 2 — mid-build loss / restore)** State is held in a three-tier model (D81): durable git trail
  (tier-2) commits only at task INTEGRATION, not mid-task; `.kata/state.json` (tier-3) is gitignored / disposable.
  Self-handoff is NOT automatic — it is a skill the agent must consciously invoke at the ~0.40 prime-frame
  threshold; `kata-orchestrate` never calls it in-loop; nothing enforces it. Result: planned restore = GOOD-but-
  manual; **unplanned mid-task loss = POOR** (stale handoff, uncommitted work redone, recovery hint board.md is
  gitignored); subagent-dies-mid-wave = MEDIUM-to-POOR. A `/kata-resume` command alone cannot fix three root gaps:
  (Gap 1) no automatic pre-compaction checkpoint; (Gap 2) per-task-integration checkpoint granularity is too coarse
  — mid-wave worker progress is lost; (Gap 3) in-flight task ownership is not durable (the `tasks{}` claim map
  is in-memory / gitignored, so a fresh conductor cannot rebuild the frontier).
  **Operator decision = Option 2 (close ALL gaps) PLUS a continuous-replay capability.** Full scope:
  **(Adapter — Claude-only, never touches core):** the 6 thin pointer commands + a NEW helper installer (mirrors
  `_flat_link_skills`, the 5 frozen engine fns stay byte-unchanged) + an **auto-handoff hook** wired via
  `adapters/claude/settings.snippet.json` (Claude PreCompact-style hook fires `kata-selfhandoff`, writes + commits
  a handoff artifact BEFORE auto-compaction) — closes Gap 1.
  **(Core — careful; touches the loop spine + state protocol; new D-numbers required):** Gap 2 = mid-wave
  checkpoint granularity — workers commit progress to their task branch as-they-go, not only at orchestrator
  integration; Gap 3 = durable in-flight ownership — the `tasks{}` / board CLAIM map is persisted into the
  git-committed tier-2 trail so a fresh conductor can rebuild the active frontier, not just the integrated task
  list. **Continuous-replay:** a capability that saves loop progress CONTINUOUSLY as the loop executes (an
  incremental checkpoint / event-log the loop appends to), so the run can be replayed/restored from near the
  point of loss — this unifies and deepens Gaps 2 + 3 and is the SPINE of the restore-hardening, not a bolt-on.
  Design questions that must be resolved before build: how the continuous-replay log is structured (event log?
  append-only journal? where — committed vs gitignored?); how it reconciles with the three-tier model (replaces /
  extends tier-3?); how mid-wave worker commits interact with the worktree / integration-branch model; what the
  PreCompact hook writes + commits and whether it can finish before the window closes; adapter-vs-core boundary
  for each piece. **★ FIRST ACTION next session: grill → freeze the design BEFORE any build.**
