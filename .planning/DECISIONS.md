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

- **D94 — WS-2 PROVEN (rolling-frontier parallelism + the in-loop RS research path, live-exercised) — and the
  `kata-slop-check` quality module shipped, both via one version-up dogfood.** (2026-06-22.) The WS-2 audit
  (`specs/ws2-loop-autonomy/AUDIT.md`) found concurrency well-designed but exercised once (dogfood #2, n=1) with
  **no automated test**, and in-loop learning/research autonomy largely **unwired**. Operator chose **in-context
  grading (zero new Python)** and to **wire the in-loop RS researcher now**. Vehicle = a real selected feature:
  **`kata-slop-check`** — standalone optional EVALUATE module (`kata/module/slop`), fresh-context no-write,
  default-FAIL slop verdict, **in-context heuristics** (general G1–G6 + 3 checks adopted from the MIT-licensed
  `ai-slop-detector`, attributed + re-implemented, no code copied). The 5-slice disjoint DAG carried a **genuine
  `research-needed` escalation** on S1 (which external checks + license). A fresh-context auditor graded the run
  **7/7**: 3 workers genuinely concurrent → S1 escalated → orchestrator **parked S1+S4+S5** while S2/S3 integrated
  → **`kata-research`** (fresh-context no-write) grounded the gap → **grounding gate independently re-verified MIT**
  (GROUND×6, `.kata/grounding.json`) → **superseding re-plan** folded the 3 checks → frontier recomputed (S4 after
  S1; S5 after S1+S3) → **mutation-proven** code-bearing slice S4. The feature **smoke-tested itself**: run on its
  own build it caught a real dangling seam-pointer (SLOP-DETECTED→NEEDS_WORK), forced the fix, re-ran **CLEAN**.
  Feature gate `kata-evaluate` **PASS**. **So the parallelism + in-loop RS path the audit flagged "unexercised" are
  now exercised end-to-end.** pytest **447**, validator **36/0**. **Honest caveat:** the durable `board.md`
  timestamps are orchestrator-written, so they can't by themselves distinguish *live* concurrency from a faithful
  replay — the genuine evidence was subagent wall-clock overlap; follow-up = **worker self-stamped start/end**
  (BACKLOG). Record: `specs/kata-slop-check/PLAN.md`, `specs/ws2-loop-autonomy/AUDIT.md`, `.kata/board.md`. Backout
  tag `pre-ws2-slopcheck`.
