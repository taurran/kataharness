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
