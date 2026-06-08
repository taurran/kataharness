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
- **D24d — `kata-orchestrate` stays a single config-driven skill, NOT three per-mode variants (CONFIRMED;
  reaffirms D21).** The tiered skills (grill/review/plan/diagnose) are forked because they carry
  judgment-heavy *branching prose* that risks context-rot/overstep across tiers; orchestrate is a
  *dispatcher* — what varies by mode (which skills/tiers, how many bake-off variants N) is a **data lookup
  from `kata.config`**, not a prose branch. Three orchestrators = three near-identical copies of the
  spawn/board/worktree/merge plumbing (duplicated substance) and three subtly different execution engines,
  which destroys cross-mode comparability. *Why:* orchestrate + `kata-evaluate` are the two spine invariants
  that make modes comparable to each other (D18/D22); they must stay singular.
