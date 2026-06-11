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
  D54/D56 — formerly "PortaVault" — is the **PokeVault** project: `github.com/taurran/pokevault`, local at
  `C:\Users\taurr_nvs748q\PokeVault\PokeVault`, with `toolkit/agent-sops/` present (verified 2026-06-10).
  KataHarness installs into and is field-tested from this vault when ready. The D54 "PortaVault must exist
  first" gate is **SATISFIED**. Forward-looking references renamed; historical artifacts unmodified.
