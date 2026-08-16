# BACKLOG — KataHarness

Promote to ROADMAP milestones when ready.

---

## ★★ 2026-08-15 PLANNING BATCH — twelve features + six found-broken fixes (operator-directed)

> Source: the operator's feature prompt (typed 2026-08-15, recovered verbatim from the session
> transcript) + two additions made live at filing time + everything found broken while finishing
> `backlog-burn-01`. Session rulings already made: **file everything first, then deep-dive**;
> **first deep-dive = Backlog Burn mode (BL-N12)**. Codes are `BL-N##` (new-feature batch) and
> `BL-X##` (found-broken); per standing operator preference every code is paired with a plain-English
> name everywhere it appears.

### The twelve features

> **BL-N01 · 🔴 "Truth Serum" — make the never-stub/never-half-build promise mechanical.
> (PRIORITY ELEVATED by the operator 2026-08-16: "we need the TRUTH SERUM update to be air
> tight. The model lies and lies and lies. Can't be trusted with anything." The burn-02 loop
> bypass — the model walking around the loop and calling it a mode — is the live exhibit: any
> guarantee that depends on model obedience to prose is not a guarantee. Truth Serum, BL-M33/
> M34's mechanical enforcement, and BL-N20's required-own-agents are one program: move trust
> from the model's compliance to code that fails closed.)**
> The harness must never stub, defer, or half-build anything without being explicit and getting
> explicit approval. The *prose* contract already exists (PD-1/PD-2, clause-pinned + fingerprinted);
> what does not exist is mechanism beyond the gate's judgment. **The recorded blocker is `BL-M33`**
> (no code seam between conductor and host-only agents — any rule about how a judge was launched is
> unenforceable prose), so BL-N01 is largely "build the seam, then hang enforcement off it."
> Open questions: what is mechanically detectable (stub signatures, unwired symbols — `contract_edges.
> surviving_stubs` already exists), and where does approval get recorded so the gate can check it?

> **BL-N02 · "Human Prose" — selectable language modes for everything the harness says.**
> Modes sketched: Simplified Technical · ELI5 · a model↔model register optimized for concise
> machine-to-machine transfer (handoffs, orientation). More to brainstorm. Existing machinery: ONE
> agnostic voice already exists (`protocol/persona.md`, `protocol/narration.md`) — this generalizes
> it into a register dial. Natural config home: `kata.config` beside mode/effort. Open questions:
> does the register apply per-surface (closeout vs. board vs. handoff) or per-run; does model↔model
> compression conflict with the "never-summarized invariant block" handoff rule (D67)?

> **BL-N03 · Ubiquitous Language — research-backed term alignment as an optional grill step.**
> Ingest the Pocock ubiquitous-language approach fully: inventory the repo's real terminology (views,
> reports, resources, object names), build a small machine-readable reference (yaml/json/md/sqlite —
> format TBD) so human and machine align on language BEFORE building; research pass for marketability
> + industry-standard terms; runnable against EXISTING codebases for alignment sweeps. Existing
> machinery: `kata-context` (CONTEXT.md glossary) is *already* adapted from Pocock's skill — this
> deepens it (research + machine-readable artifact + existing-repo alignment mode) rather than
> starting from zero.

> **BL-N04 · Specialist Cadre — a library of installable specialist agents.**
> Standardized specialists (coding optimization, domain knowledge, **a GitHub specialist** — named
> explicitly by the operator) that research/coding agents can pick up; ingested into the user's
> designated vault; includes cloning + customizing a "KataHarness Superpowers" set that loads with
> the harness; users can author their own specialists and the harness generates the contextual
> references/files. **RULING (operator, 2026-08-16 — the independence doctrine):** the launch
> preload seam stays OPEN (UX-32) and near-term ingests the CURRENT third-party superpowers pack
> as a **placeholder only**; the kata-native superpowers set built under this item REPLACES it.
> Standing direction: **KataHarness divests from ALL third-party module components — superpowers
> and GSD included** — third-party packs are reference/placeholder material, never load-bearing
> harness components; the swap to kata-native must be a config change at the seam, not a rework. Open questions (operator-flagged): do superpowers live inside the cadre or in
> their own home; relationship to the existing agent-skills toolkit (`agentSkills.dir`,
> `kata-promote` two-stage gate, STANDARDS §1.3 discriminators) which already governs exactly this
> shape of thing.

> **BL-N05 · Settings module — a real settings command.**
> One command to view/set KataHarness system settings. Existing machinery: `tools/kata_settings.py`
> + `kata.config` + the bootstrap interview already own the values; what is missing is the direct
> user-facing surface. Small, but its UX belongs to the BL-N07 rework template.

> **BL-N06 · Branded launcher + the launch experience ("the front door", operator-clarified).**
> `kata-claude` / `kata-codex` / `kata-kiro` aliases that launch the host INTO a KataHarness
> interface: designed ASCII title (full ASCII font, color + gradient, branded), version, help,
> settings, new-project / run-existing commands, with all environmental skills + agentic files
> preloaded (kata superpowers etc.). The MindBridge `mbl-kiro` launcher is the reference experience.
> **Operator direction 2026-08-15: dial in the launch design FIRST — agree the template — because it
> becomes the design system BL-N07 carries across everything.** Brainstorm-deep flagged.

> **BL-N07 · The UX rework — carry the agreed design across every menu and phase. (NEW 2026-08-15)**
> Once the BL-N06 launch template is agreed, apply it across ALL menus and ALL phases of the harness
> — one visual/interaction language everywhere the human touches it (bootstrap dial, grill UX,
> narration, closeout, status). Operator: *"something that this has really needed for a long time."*
> Existing anchor points: persona/narration protocols, the two-tier closeout (CLI summary + branded
> HTML report), the one-dial bootstrap. This is the umbrella; BL-N05/N06 are its first tenants.

> **BL-N15 · Handoff on demand — one verb, standardized execution. (NEW 2026-08-15)**
> Saying "hand off to a new session" (or close variants) in ANY KataHarness-governed session
> executes the full standardized handoff: context update · handoff update (frontmatter per
> `protocol/handoff.md`) · **orientation printout in the locked UX grammar** (the hard agent-
> orientation format, copy block labeled "paste into new session"). Predictable and repeatable —
> same artifacts, same order, every time. Existing machinery: `kata-handoff` / `kata-selfhandoff` /
> `kata-orient` / `kata_handoff_break.py` are real but verb-triggered standardized execution is
> NOT; the held session-lifecycle grill's surviving findings (trigger never fired · staleness
> comparator unimplemented · frontmatter fields never carried by real handoffs) are input evidence,
> NOT its ledger. Ties into the UX rework (grammar) and the Kitchen (roles below). **Operator:
> work this during the current batch's execution.**

> **BL-N16 · The learning graph — a per-agent learning substrate. (NEW 2026-08-16, Kitchen-aligned)**
> **The shift: learning applies to INDIVIDUAL AGENTS, not the harness as a whole.** Every agent
> type in the harness gets a substrate file — YAML frontmatter + markdown (the field-standard
> agent-definition shape; verify against current conventions at grill) — carrying: full frontmatter
> · **learning modifications** accumulated for that agent · **temporal tracking** of when each
> learning was applied. **Every time the agent loads, its learning modifications load with it — and
> every application is auditable in the harness.**
> **Learning sources:** grilling · in-loop guidance (the user replies with items explicitly flagged
> as learning) · generated at agent close. **At run end, a learning session runs:** all learning
> notes collected during the run are auto-applied to their agents; the closeout offers (a) apply
> learning guidance against the run's learning-output list and (b) review/understand ALL learning
> applied this run. *(Closeout alignment: the "WHAT WE LEARNED" box and these two menu options are
> the same surface — UX-20 addendum.)*
> **Specialist spin-off:** when an agent's accumulated learning is deep enough, the harness OFFERS
> to spin off a cadre specialist (BL-N04) derived from it. Personalized/specialized cadre agents
> live in **the vault, in official KataHarness folders** — the substrate itself is vault-stored so
> **settings and learnings persist across uninstall/reinstall**.
> **Existing machinery this builds on (verified, not guessed):** `kata-promote`'s two-stage
> agent-distilled-skill promotion + STANDARDS §1.3 discriminators (the spin-off seam, human-gated)
> · the engram/learn-feed vault emission (`learn_feed.py`, D151 — run learnings → vault pages) ·
> `kata-improve` (today's HARNESS-wide folding — exactly what becomes per-agent) · `agentSkills.dir`
> + `engram.learnFeed.dir` (vault-external persistence precedent) · LESSONS-LEARNED.md capture.
> **Resilience/cursor — RULED (operator, 2026-08-16, the burn-02 final-eval exchange):** the
> CURSOR is the phase-to-phase interruption TOKEN — it (or files traveling with it) carries ALL
> history, rulings, and statuses, so any interruption knows exactly where to pick up. It must
> align with THIS item's graph-substrate configuration — one durable record; the rail/cursor is a
> VIEW over it (the conductor's one-source-of-truth recommendation, now operator-aligned). The
> grill's remaining job is the mechanism (what the cursor physically is relative to board ·
> `Kata-Task:` trailers · restore machinery), not the principle. Assessed-against-the-field: Hermes + Pi
> alignment research dispatched 2026-08-16.
> **RULINGS (operator, 2026-08-16 — the open questions are now settled):**
> 1. **A dedicated LEARNING AGENT + GATE apply all learning.** Learning application is never a side
>    effect — one agent role owns it, and a gate stands in front of every application (the
>    grounding-gate posture, D33 never bypassed). Additions are **confidence-scored and held until
>    the threshold is met** — below-threshold learning is never applied. *(D74 redaction still
>    binds the vault-bound half: secrets/PII scrub is a hard pre-write gate on anything emitted to
>    the vault — that is what redaction is for here.)* Plus the Hermes-derived security scan on
>    self-written learning (injection-persistence vector).
> 2. **Contradictions resolve by RECENCY** — newest learning wins mechanically — and the user is
>    pointed at the learning-management feature for the deliberate cleanup.
> 3. **Size control = the Hermes measure, adopted:** a capped, curated ACTIVE section (visible
>    fill %) is what injects at agent load; the full temporal append log stays as the audit layer;
>    condensation runs through the learning-management optimizer, never silently.
> 4. **BC holds:** an agent with no learning file behaves byte-identically.
>
> **NEW component — LEARNING MANAGEMENT (skill/feature within this item):** the user-facing
> surface for the substrate: review itemized learning PER AGENT · clean up contradictory entries ·
> align/prune by temporal recency · optimize + condense learning items to improve future
> performance (feeds the active-section distillation). This is where recency-resolved conflicts
> get surfaced for human judgment.
>
> **Second brain = an ADDITIONAL learning destination:** beyond per-agent substrate files, learning
> can be applied/emitted to the second brain (vault) — the learn-feed channel — so run learnings
> land in both the agent that earned them AND the durable knowledge store, each through its gate.
> **Field alignment (research landed 2026-08-16, `.planning/specs/learning-graph/RESEARCH-HERMES-PI.md`):**
> format + load-time injection MATCH the field; temporal audit + specialist spin-off EXCEED it
> (neither Hermes nor Pi has either). **Adopted design consequence: append for audit, distill for
> load** — the temporal log audits; a capped curated “active” section (visible fill %) is what
> injects (Hermes’ bounded-curation lesson). Also adopted: staged-write + unified-diff approval
> queue · security scan on self-written learning (injection-persistence vector).

> **BL-N19 · The re-loop path is FIRST-CLASS in the loop architecture, for ALL run shapes. (NEW
> 2026-08-16, operator-ruled)** Every run — not just burns — has an OPEN, mechanical path to
> re-running the greater loop when the final eval fails, exactly parallel to how the evaluator
> already re-loops an individual coding agent that fails enough times (reroll/fix-loop). Today
> this exists as prose + the loop-back seam (kata-loop's version-up carry) but there is no
> mechanical NEEDS_WORK→re-loop route at run level: burn-02's remediation cycle had to be
> conductor-hand-driven. Composes with BBM-12 (wave-per-loop: a wave re-loops on failed eval),
> BL-N18 (the threshold that decides "fails"), and the D71 grill dial (a re-loop's grill depth).
> The architecture rule: NO run shape ships without its failed-final-eval re-entry path defined.

> **BL-N20 · KataHarness runs its OWN agents — never bare host-default agents — for every role.
> (NEW 2026-08-16, operator-directed; current state VERIFIED)** Verified 2026-08-16: no
> harness-defined agent identities exist anywhere (`adapters/claude/agents/` absent, no repo
> agent definitions, `kata_dispatch` references none) — every coding/validation/eval agent in
> every session to date has been a HOST-DEFAULT agent shaped only by its prompt brief. The item:
> define KataHarness agent artifacts for every role (the role model: conductor · orchestrator ·
> coder · validator · evaluator · advisor · arbiter · challenger · learning agent), as the
> BL-N16 substrate files (frontmatter + markdown, per-agent learning attached), installed by the
> harness and REQUIRED by dispatch — a dispatch that would fall back to a bare host default
> fails closed or escalates. Host-native agent features (Claude subagent frontmatter, Codex/Kiro
> equivalents) are the adapter's rendering of OUR definitions, never the definition itself.
> **DESIGN RULINGS (operator, 2026-08-16, second sitting):** (1) our agents are **LIGHTWEIGHT —
> never general-purpose blobs**; (2) they MAY be **derived from the general-purpose agents** as a
> starting point and **aligned against other harnesses' agent designs — Hermes, Quicksilver, Pi
> named as references** — but the definitions are OURS, written by us (the UX-32 independence
> doctrine at agent level, explicit); (3) **conductor and orchestrators are THIN** — the
> thin-orchestrator doctrine (spine #8) baked into the agent definitions themselves, not just
> graded after the fact; (4) **coding agents carry actual coding best practice as GOOD-CODE /
> BAD-CODE EXAMPLES** — exemplar pairs in the agent substrate, not abstract style prose; the
> same exemplar pattern extends per-role (validator: real-vs-vacuous finding exemplars, etc. —
> grill decides the per-role set).
> Composes: BL-N16 (the substrate IS the agent file) · BL-M33/M34 (the dispatch seam is where
> "must be our agent" gets enforced) · UX-32 independence doctrine (same principle, agent-level).

> **BL-N21 · Always-loop: the personal global config makes EVERY coding task a full KataHarness
> loop run. (NEW 2026-08-16, operator-directed)** For the operator's own Claude/Codex/etc.
> environments (individual-case global config, not a product default): every coding-task
> execution routes into a FULL loop run — an onramp collects the run-configuration items (the
> guided flow: shape, care level, fan-out, models, brain/vault, docs, goal optimization — the
> BBM-5/UX-21 interview), then the loop executes. The onramp ALSO offers, every time, the choice
> of executing from (a) the INSTALLED KataHarness (the vault/skills install) or (b) the pre-prod
> LIVE repo (C:\dev\projects\KataHarness) — so dogfooding the development tip is a first-class
> choice at every launch. Mechanism candidates for the grill: the UX-28 wrapper as the enforcing
> door + host global-config/hooks that redirect bare coding requests into the onramp. Composes:
> BL-N06/07 (the wrapper owns the onramp) · UX-31 (all three hosts) · BL-N20 (the loop it
> launches uses our agents).
> **EXTENDED (operator, 2026-08-16, second sitting): existing-code executions get a mandatory
> INITIAL INTAKE.** Always-full-execution also covers onramps onto EXISTING code and code
> reviews: an initial intake pass scans ALL context so the run is fully aware of what it is
> looking at before anything else happens. **A CONTEXT-SCANNING capability is NECESSARY for
> executions on existing code** — assess at grill whether a dedicated context-scanning AGENT is
> needed for fully loading LARGE codebases. Honest current-state (verified surfaces): scanning
> FUNCTIONS exist — `graph_gen`/kata-graph (the F2 code map, token-budgeted digest),
> `kata-understand`, `kata-context`, `kata-onboard` (the existing-repo door), debug-mode intake —
> but no scanning AGENT role exists, and the functions' large-codebase behavior (budget
> exhaustion, partial-map honesty) is unassessed. The scanning agent, if built, joins the BL-N20
> role set with its own substrate file.

> **BL-N18 · Tunable judgment thresholds — advisor hooks AND evaluator strictness. (NEW
> 2026-08-16, operator-ruled during the burn-02 final-eval exchange)**
> The advisor's trigger thresholds are config-tunable today (`advisor.hooks.failThreshold`/
> `rerollTrigger`/`fixLoopCeiling` in `kata.config` — verified live) but surface nowhere in the
> guided start or settings; the EVALUATOR has no strictness dial at all — default-FAIL is the
> posture (never tunable away, D33), but what severity kicks a wave back vs rides as a finding
> has no operator knob. Ruling: both become tunable, surfaced in the guided-start interview +
> the settings screen (UX-21/22), with the D33 floor explicit: no dial ever disables the gate
> itself. Pairs with the wave-per-loop shape (BBM-12: each wave's eval can kick it back — the
> threshold decides what "fails" means) and the eval-challenger (BL-N10 extension).

> **BL-N17 · Scrub “engram” → “learning” across KataHarness. (NEW 2026-08-16)**
> The internal term “engram” becomes plain **“learning”** everywhere a user or agent meets it:
> config keys (`engram.autonomy` → `learning.autonomy`, `engram.learnFeed.dir` →
> `learning.feed.dir`, `engram.backend` → `learning.backend`), `protocol/engram.md`, the
> `kata-engram` cognition seam, STANDARDS/ROADMAP references, and skill prose. **BC-sensitive:**
> config keys are a compatibility surface — the rename ships with old-key aliases + a migration
> note, validated by the config load-guard; the protocol file rename must respect the
> REQUIRED_PROTOCOL registry + fingerprint machinery (a deliberate two-step re-approval, not a
> silent swap). Pairs naturally with BL-N16 — same grill, likely same run.

> **BL-N08 · "The Kitchen" — decouple the flat run; let tasks bake. (THE BIG ONE)**
> Chef (conductor) / sous-chef (orchestrator subagent) / dishes (tasks). Today's run pattern is
> flat and on-rails; the Kitchen lets execution branches parallelize and optimize *around each
> other* — a long-running task is put on to "bake" while non-dependent tasks run; each branch
> optimizes within itself for time and tokens; **fan out the fan-out** (branches that themselves
> fan out). Existing machinery to build on, not replace: the rolling DAG-frontier dispatch + async
> park/drain/hard-wait escalation (D47–D56), worktree isolation, the wave model. Evidence feeding
> it: the burn's H1 finding — **gating is the serial bottleneck, builders are not** — so the Kitchen
> must redesign gate placement, not just dispatch. Operator: has unspecified details; grill deep,
> live.
>
> **THE ROLE MODEL (operator-specified 2026-08-15):**
> - **Conductor** — the PRIMARY session agent: research + brainstorming, the human's interlocutor.
>   Highest tier the operator will run (recommend Fable, as this session runs).
> - **Orchestrator** — a THIN dispatched agent at the run's standard coding tier, carrying most of
>   the orchestration + subagent-execution load. Under the Kitchen it graduates to chef/sous-chef:
>   managing multiple branches concurrently — things "cooking" while non-dependent work executes —
>   running the working loop, and employing the judgment agents below.
> - **Advisor** — as shipped (D167 advisor-executor, fresh-context consult).
> - **Evaluator** — the fresh-context no-write default-FAIL gate (operator correction: evaluator,
>   NOT "assessor").
> - **ARBITER (NEW)** — advisor + second-brain decision-making combined: consults the vault's
>   decision history when arbitrating. Needs its own definition at grill time.
> - **Challenger** — cross-model challenge of the adversarial validator (BL-N10).
>
> **Cross-ref (2026-08-16):** the per-agent learning substrate (BL-N16, the learning graph) is
> Kitchen-aligned — the roles above are exactly the agents whose substrate files accrue learning.

> **BL-N09 · Fan-out dial — a run-config knob for Kitchen capacity. (NEW 2026-08-15, depends on BL-N08)**
> Once the Kitchen exists: a `fanOut` configuration alongside mode/economy — three positions,
> working names **minimal / standard / maximum** (better descriptive terms welcome at grill time):
> minimal caps parallel-branch capacity, standard is moderate *in context of the workload*, maximum
> lets the Kitchen architecture itself determine the parallel-branch ceiling. Config-surface work +
> the Kitchen's capacity model; strictly sequenced after BL-N08.

> **BL-N10 · "Challenger" — cross-model challenge of the adversarial validator ONLY.**
> The adversarial validator runs on a DIFFERENT model (another Claude, or a Codex model); then a
> strong model (Opus/Fable) comes back to CHALLENGE the validator's findings — accuracy control on
> the adval itself. **SCOPE CLARIFIED (operator, 2026-08-16, correcting a momentary extension):
> the challenger challenges ADVERSARIAL VALIDATION only — never the final default-FAIL evals —
> and MUST execute as a separate subagent or, better, a DIFFERENT MODEL** (independence is the
> point; a same-context challenge is theater). A brief same-day "challenge the evals too" reading
> was withdrawn by the operator within the hour — recorded so it is not resurrected. Includes proving Codex models can actually execute here (today `_COMMAND_BUILDERS`
> covers codex/kiro but the Claude path is orchestrator-prose, and non-Anthropic ladders in
> `kata_models.py` are empty placeholders). Open question: does this need multi-agent orchestration,
> and does it inherit BL-M33's missing dispatch seam?

> **BL-N11 · Backlog management — an explicit function, not a markdown convention.**
> Operator-recommended as its own item. Today the backlog is this file plus five sibling surfaces
> (the recorded `KH-B41` "six surfaces, no single view" problem). A real capability: add/triage/
> close/prioritize items, feed a burn, ingest external sources. **Elevated 2026-08-15 (ruling
> BBM-3): a designed PREREQUISITE of Burn mode's intake** — standardize/normalize the backlog as a
> low-touch alternative to full GitHub issue tracking, with the item shape designed so GitHub
> issues (the future primary source) maps onto it without rework.

> **BL-N12 · Backlog Burn mode — the operating mode this branch prototyped. (FIRST DEEP-DIVE)**
> Ingest a large item set (backlog, design issues, **external tickets/issues**), triage-then-grill
> ONCE across the whole set, burn in preplanned waves with parallel builders, throughput without
> losing accuracy. The evidence base is real and unusually good:
> `.planning/specs/backlog-burn-01/OBSERVATIONS.md` — headline findings: gating is the serial
> bottleneck (H1); triage must precede the grill because a third of items were mis-filed (H2); wave
> partitioning must be computed over the IMPORT GRAPH, not file lists (H4); the convergence gate is
> non-optional and must attack the SHARED half of the contract (H3/H5 ×2); provisioning must pin
> base SHAs itself (H6 ×2); builders briefed to push back catch real contract errors (H7).

> **BL-N13 · Goal/system-prompt optimization — a guided step in the start flow. (NEW 2026-08-15)**
> Named by the operator while ruling on Burn mode's entry surface (BBM-5): the guided `/kata-start`
> interview should include an optimization pass over the user's goal / system prompt — sharpening
> the priming prompt before anything freezes. Existing machinery it extends: the reflective goal
> mirror (WS-3 intake) + the priming-and-grill architecture (D71: the grill enriches the priming
> prompt into the frozen spec). Scope TBD at its own grill; filed so it survives the session.

> **BL-N14 · Run statistics — one metrics engine, surfaced everywhere. (NEW 2026-08-15)**
> A per-run statistics rollup and its display grammar. **Counts:** agent/subagent executions ·
> outer-loop cycles (the Kata Loop; naming TBD at grill) · miniloop executions (per-task TDD/fix
> cycles, inline-eval rerolls) · issues flagged vs. remediated · overall execution time · tokens
> total / input / output — per phase and per item. **Surfaces:** (a) mini-metric chips beside the
> phase progress strip during the run — one ALIGNED chip grammar so every section's stats read the
> same (order, units, separators fixed); (b) a full statistics section in the closeout report
> window covering the entire run and every executed item. A "confidence rating" chip is wanted but
> undefined — what it derives from (gate outcomes? adval verdicts?) is an open grill question, not
> an invention. Existing machinery: `kata_telemetry` ledger rows (perTask cost, failureKinds,
> evidence digests) + subagent token usage already captured — this is a rollup + grammar, not a
> from-scratch counter. **Sequencing (operator): part of this batch's burn — with the Kitchen
> (BL-N08) or right after it.**
> **Semantics ruling (2026-08-15):** every displayed vitals bar shows figures **cumulative for the
> run up to that moment** (not per-phase deltas); the closeout report shows the same counters at
> final values plus per-item breakdowns. Counters live in run STATE (`.kata/`, D81 tier-3), never
> in `kata.config` — config is settings, counters are state. New counters needed: agent executions
> · miniloop tally · flagged→remediated · confidence (derivation TBD); tokens/time already flow
> from the telemetry ledger.
> **Agent-type breakdown ruling (operator, 2026-08-16 — UX-33):** the agent-execution counter is
> PER TYPE, not a single total: conductor · coding/builders · validation (judges/reviewers) ·
> advisor · evaluation (gate + inline) · design/plan authors — each as agents/executions (resumes
> count), plus miniloops BY KIND and the model tier per type. Verified gap: host-Agent-tool
> dispatches (this planning branch's burns) write NO telemetry rows today — the counter must hook
> the dispatch seam itself, whichever path dispatches (kata_dispatch AND the conductor's direct
> host dispatches), or the crew box undercounts exactly the runs that most need auditing.

> *(Burn-mode design rulings from this session live in
> `.planning/specs/backlog-burn-mode/GRILL-LEDGER.md` — BBM-1..BBM-10.)*

### The six found-broken fixes (from finishing backlog-burn-01, 2026-08-15)

> **BL-X01 · `protocol/config.md:14`'s own example fails the new load-guard.** The schema example
> names modules `design`/`bakeoff`/`improve` — no skill on disk carries their provider tag (verified
> twice: builder + conductor's independent probe). Fix the example (or provide the tags) — the
> schema must pass its own validator. Clause-pin aware edit.

> **BL-X02 · The installer's "next steps" banner names commands that do not exist.**
> `tools/kata_install.py` (~:1305-1320) tells users to run `/kata-initiate` and `/kata-bootstrap`;
> neither is a command file (the real set: `/kata` `/kata-loop` `/kata-start` `/kata-onboard`
> `/kata-resume` `/kata-status` `/kata-validate`). First-run UX lies at the exact moment of first
> contact — also a BL-N07 tenant.

> **BL-X03 · `kata-understand` documents a graph-rebuild command the tool refuses.**
> `modules/closeout/kata-understand/SKILL.md:47` says `--root .. --out ../.kata/kata.graph.json`;
> `graph_gen._safe_path` raises on ANY `..` path (verified live 2026-08-15). Every literal follower
> of the doc hits a crash. Fix the doc to absolute/CWD-relative form.

> **BL-X04 · `graph_gen` scans embedded worktrees — a mid-burn map rebuild is garbage.**
> With six `.claude/worktrees/` copies present the scan returned 43,064 nodes vs. the honest 5,560
> (~7× over-count). Add worktree/gitignored-dir exclusion. **Directly load-bearing for BL-N12**,
> whose wave partitioning wants graph rebuilds while worktrees exist.

> **BL-X05 · Sweep the exact-version-pin class.** `test_validate_prime_directives.py` pinned the
> literal `version: 0.17.0` and redded on any legitimate bump (caught live by the BURN-D builder;
> fixed to a semver floor at `53cecf8`). Grep the suite for the same class — exact version/count pins
> against living files — and convert to floors or regenerable assertions.

> **BL-X07 · kata-promote's frontmatter mischaracterizes Hermes.** It calls Hermes a
> "no-gate instant-universal model"; the 2026 docs show an opt-in staging gate
> (`write_approval`, pending queue, unified diffs) exists. True of the DEFAULT config only —
> tighten the wording so our own comparison stays truthful. One-line doc fix + version bump.

> ## 🔴 **BL-M34 · The loop can be silently bypassed — and the harness's own burns just did it twice. (FILED 2026-08-16, operator-directed, angry and right)**
> Nothing structural stops a conductor from dispatching designed work straight through the host
> (Agent tool) with no initiation, no board CLAIM/DONE, no kata-orchestrate, no kata-evaluate
> contract, no final eval, no improve fold, no telemetry — the entire loop reduced to the
> conductor's self-discipline, which is exactly the "rule that exists only as prose" class the
> 2026-08 enforcement sweep existed to kill. Proven live: backlog-burn-01 AND backlog-burn-02
> both ran conductor-driven; the bypass surfaced only because the operator asked why zero advisor
> consults ran against a standing approved grant. **Ruling context: BBM-12 — burns use the ENTIRE
> loop; the bypass is drift, not a mode.** Fix direction (grill decides the mechanism, not the
> obligation): a structural guard at the dispatch seam — designed work (an item with a frozen
> plan) dispatched without live loop context (board run-id, CLAIM line) fails closed or escalates;
> composes with 🔴 BL-M33 (the missing conductor↔host code seam is where the guard must live —
> without M33's seam there is no chokepoint to guard). Related evidence: the UX-33/BL-N14
> telemetry gap and the advisor-reach gap are the same bypass seen from two other angles.

> **BL-X08 · The `batch` run-shape preset writes a config the load-guard STOPS. (FILED 2026-08-16,
> found by the burn-02 X01 gate judge, machine-verified.)** `skills/coordinate/kata-bootstrap/
> resources/run-shapes.md:6` pre-fills `modules: [bakeoff]`, and `bakeoff` has NO provider skill
> (no `kata/module/bakeoff` tag anywhere) — so bootstrapping the batch shape produces a config
> `validate_core_config` fail-closes on. Same family as BL-X01, but LIVE machinery, not a doc
> example. Fix direction needs a triage call: give bakeoff a provider tag, or change the preset,
> or both — do not guess at filing time.

> **BL-X09 · kata-understand's FALLBACK path documents a grep that fails on PowerShell. (FILED
> 2026-08-16, found by the burn-02 X03 gate judge.)** `modules/closeout/kata-understand/
> SKILL.md:138-140` instructs `grep -n "^def \|^class " <file>` — not a PowerShell cmdlet, so a
> literal follower on this project's stated primary shell fails there. Same doc-vs-mechanism class
> BL-X03 just fixed in the same file's primary path; pre-existing, out of that item's scope.

> **BL-X10 · kata-graph's canonical CLI doc still teaches the refused invocation. (FILED
> 2026-08-16, found by the burn-02 FINAL EVAL, F7 — a between-items residual no per-item gate
> could see.)** `skills/plan/kata-graph/SKILL.md:82` documents `--root <repo-root> --out
> kata.graph.json` — a placeholder readers naturally fill with `..` (which `_safe_path` provably
> refuses) and a relative `--out` that silently writes into `tools/`. Same doc-vs-mechanism
> family as BL-X03 (fixed) and BL-X09; align with X03's parameterized-absolute form.

> **BL-X11 · kata-evaluate's machine-input step doesn't route through the T-04 identity check.
> (FILED 2026-08-16, from the burn-02 final eval's F1 second-order finding, conductor-corrected.)**
> The contract prose tells the evaluator to read `.kata/RESULT.json` but never points it at
> `run_result.py:123`'s resultSha-vs-credited-SHA identity check (the T-04 fix, `bf163fd`) — so a
> literal evaluator meets a stale artifact raw; the burn-02 final eval read a JULY run's 537-green
> RESULT.json and had to catch the staleness by eye. Doc-seam fix: the skill's machine-input step
> cites and requires the identity check; NO new mechanism (the guard already exists in code).

> **BL-X06 · Host auto-worktree isolation fails on this repo (path casing) and provisions wrong
> bases.** The Claude Code worktree isolation refused `C:\dev\...` vs `C:/Dev/...` casing and left
> orphans at a stale base — the second independent provisioner to produce a wrong base (H6 ×2).
> Harness-side mitigation: burn/Kitchen briefs always pin + verify base SHAs (already standing);
> track whether a host fix lands, else make manual pinned provisioning the codified rule.

---

> ## 🔴 **BL-M33 · There is no code seam between the conductor and a host-only agent — FILED 2026-08-04**
>
> **In plain terms:** when the conductor dispatches the evaluator (or any host-only role), it does it by
> *writing a prompt*. There is no function that does it. So there is nowhere for enforcement to live:
> any rule about how a judge was launched is a sentence in a `SKILL.md` that the next agent may or may
> not honour, and nothing can detect the difference.
>
> **Measured, not asserted (2026-08-04, `f4096e6`):**
> - `kata_dispatch.build_brief` has **no non-test caller** — every reference is its own definition or
>   prose inside a `SKILL.md`.
> - `_COMMAND_BUILDERS` covers `codex` and `kiro` only; `kata_dispatch` states the Claude path *"is
>   handled by the orchestrator, not here"*.
> - the evaluator is `HOST_ONLY` (`kata_roles.py:46`) — i.e. exactly the path with no builder.
> - `contract_gate.write_contract_gate` emits `contract-gate.json` and **no Python ever reads it**;
>   `.planning/D2-VERIFICATION-RESULTS.md` records zero have ever been written in a real run. A
>   producer-only artifact is the same shape: the enforcement half is prose.
>
> **Why it matters:** this is the structural reason `T-05` could not be built honestly. The attempted
> design (a dispatch record the evaluator echoes) was **forgeable** — the evaluator has `Read`/`Bash`
> and is explicitly pointed at `.kata/`, so it could read the token off disk. Fixing that leaves the
> *comparator* as prose, so it would still be a rule with nothing enforcing it. See
> `.planning/specs/evaluator-dispatch-record/GRILL-LEDGER.md` `EDR-7`.
>
> **What was shipped instead:** the false claim was removed. `kata-evaluate` 0.3.2 and
> `kata-inline-eval` 0.1.1 now state plainly that `no Write/Edit` is structurally enforced while
> `fresh context` is an unverified, unrecorded dispatch convention.
>
> **Not scoped here.** Building the seam changes how the orchestrator works and is its own decision —
> it is the prerequisite for *any* mechanical guarantee about how a judge was launched, so it likely
> unblocks more than `T-05`.

> ## ✅ **BL-F01 · Freeze is not a recorded state — BUILT 2026-08-02** (`6b4e8db`)
>
> **Shipped as assessed, both halves.** `status:` is a closed `draft | frozen` enum read by
> `kata_restore.plan_status()` / `assert_frozen()` (fail-closed: absent ⇒ NOT frozen; unknown ⇒ raises;
> first-word rule so `DRAFT — awaiting …` parses as draft rather than erroring). `build_brief` gained a
> **required** `plan_path` and refuses a brief for a non-frozen plan — the chokepoint that makes BLOCK
> real, since nothing in code previously sat between a plan and a dispatched worker. `build_brief` had
> ZERO production callers, so "required" cost test churn only. 10 new tests, mutation-proven; 33 legacy
> call sites migrated with **zero assertions removed** (116→120, 12→12, 41→41).
> **Not built, because already durable:** "has execution started?" — `Kata-Task:` trailers + board CLAIM
> + `detect_lost_run`. **Not a skill:** freeze is a fact, not a behavior.
> *The assessment that produced this scope is preserved below, because the reasoning is the reusable part.*
>
> ---
>
> ### The original assessment (2026-08-01) — kept for the reasoning
>
> **In plain terms:** a plan is called "frozen" by convention and nothing records or checks it. If a
> session drops, you cannot tell a frozen plan from a draft someone is still editing.
>
> **The evidence is this repo, one commit ago.** `.planning/specs/dispatch-authoring/PLAN.md` carries
> `status: DRAFT — awaiting freeze-gate` **to this day**. It was gated, dispatched, built across five
> tasks, and committed while still claiming to be a draft. Nothing anywhere noticed.
>
> **Assessed scope — deliberately small. This is NOT a new skill.** Freeze is a *fact*, not a
> behavior; `kata-design-doc` and `kata-plan-*` already perform the authoring act. A `kata-freeze`
> skill would be ceremony. Verified before proposing anything:
>
> | question | answer |
> |---|---|
> | Is there a status field already? | **Yes** — `status:` exists in PLAN frontmatter today, as unvalidated free prose |
> | "Has execution started?" | **Already solved, build nothing.** `Kata-Task:` trailers on integration commits (git-durable, survives clone, strict regex `kata_restore.py:206`, parsed by `collect_integrated_tasks`) plus `.kata/board.md` CLAIM lines and `kata_restore.detect_lost_run` |
> | Is there a code chokepoint to block at? | **No — and this is the catch.** `build_brief(...)` never receives the plan, and `parse_plan_tasks` is called ONLY from crash recovery. The orchestrator is prose: it reads the plan and dispatches, with nothing in Python in between |
>
> **So it is two changes, not one** — and the second is what makes it real rather than another
> described rule:
> 1. **State.** Constrain the existing `status:` to a closed enum (`draft | frozen`); validate it in
>    the frontmatter reader that already runs. Fail closed on an unknown value (D45/GB12 posture).
> 2. **Chokepoint.** Give `kata_dispatch.build_brief` the plan path (additive kwarg) and refuse to
>    build a brief for a non-frozen plan. No worker can be dispatched without a brief, so this is a
>    real gate rather than an instruction.
>
> **Operator ruling (2026-08-01): it BLOCKS, it does not warn.** Verbatim: *"we don't want a model
> making assumptions and just executing because it sees warn as a soft status."* A warning would have
> scrolled past exactly as the DRAFT above did.
>
> **Why it matters:** `kata-orchestrate`'s entire no-drift guarantee is built on "the plan is frozen."
> Today that rests on an assumption no code makes — nothing prevents executing against a plan still
> being edited, or detects one silently re-frozen mid-run.
>
> **Same disease class as three other findings on this branch** — phase is derived and never stored;
> the handoff staleness rule is fully specified and implemented nowhere; gate evidence recorded its
> own identity and no consumer read it. A load-bearing state that exists only as prose.
>
> Discovered while building KH-T13: the rubric checks a returned artifact's quality, and then nothing
> locks it.

> **★★ 2026-07-25 — MERGE-BACK INGEST ITEMIZED: see `.planning/MERGEBACK-INGEST.md`.**
> The MindBridge-fork merge-back (`kataharness-mergeback-v0.2.1`, producer @ `75108b7`) has landed and
> is fully itemized: **8 merge candidates → tasks T-01..T-08**, plus T-00 (clean-room blocker), T-09
> (records correction), T-10 (ingest defect-carry). **16 new backlog items BL-M01..BL-M16** derived
> from their 26-item forward backlog, the 5 divergence flags, and our own review findings.
> That file also carries the **coverage matrix** (every arriving artifact ⇒ where it is tracked, no
> blank rows) and the **Part D verification checklist** for the 14 subsystems their alignment report
> calls "already aligned" — because an alignment claim is not evidence our side works.
> **Probed already:** learning-loop emit ✅ FIRED (269 pages) · learning-loop *loop* ⚠️ unverified ·
> advisor ✅ wired/UNFIRED · **M4 inline evaluator ❌ has NEVER fired here (0 machine-JSON verdicts in
> all history)** · `STANDARDS.md:112` bump-on-modify guarantee ❌ FALSE in our tree.
> **Nothing is ingested. Every MC awaits its own grill + work-linkage adval (§6).**

> **★★ 2026-07-20 — NEXT INITIATIVE (operator-directed, intake brief WRITTEN, build NOT started):
> QUOTA-RESILIENCE — per-provider rate-limit / token-exhaustion graceful stop + resume.**
> Full grounded brief: **`.planning/specs/quota-resilience/REQUIREMENT.md`** (pre-grill; every
> claim file:line-cited, verified against master `0d3abc6`). Ask: (1) advisor kill-switch when
> Fable is unavailable — skip remaining consults, report at closeout; (2) the general feature —
> detect provider quota/rate-limit exhaustion **per provider** (Anthropic/OpenAI/Cursor/Gemini),
> tell the operator plainly, **park the run via the existing handoff machinery so `/kata-resume`
> picks up exactly where it left off**, and emit the provider's upgrade command/URL.
> **Ground truth:** the save/resume half is BUILT+WIRED (selfhandoff · gauge · steer · restore ·
> `/kata-resume`) but triggers ONLY on context-utilization / operator-stop / crash — **quota is a
> trigger nowhere**. The detection half is effectively GREENFIELD: `429` appears nowhere in the
> repo; the 401/403 rules are SKILL prose with **no executable owner**; and **`tools/kata_dispatch.py:172-174`
> DISCARDS `proc.stderr`**, destroying the provider signal before anything could classify it
> (a standalone defect degrading ALL error reporting today — ~10-line fix, highest
> value-per-token item on this list). Hardest leg = codex **hang-on-402 with no exit code**
> (`docs/platforms/codex-cli.md:89`) landing in `TimeoutExpired`, indistinguishable from a slow
> task. Scope agreed with the operator: **Tier 1 (consecutive-failure run-wide lapse + a
> `kata_steer` kill-switch verb) + Tier 2 (stderr fix · classifier · human-required escalation +
> breakthrough alert + auto-handoff · `degraded {scope:"provider"}`) in ONE version-up; Tier 3
> (per-provider upgrade registry · silent-hang watchdog · preflight quota-headroom) is a
> follow-on needing its own grill.** Seven open grill questions enumerated in the brief §4.

> **★ 2026-07-14 — D1 PHANTOM-CORRUPTION ROOT CAUSE FOUND (caught live; HIGH-priority fix):**
> `mutation_run.prove_non_vacuous` **mutates the REAL source file in place**
> (`path.write_bytes` on e.g. `tools/recurrence_detect.py`), runs a pytest subprocess
> (seconds-long window), then restores in a `finally`. ANY concurrent reader during the window
> sees the mutated file — proven this session: a `git diff master` run while the background
> gauntlet executed the mutation-proof tests captured the exact documented IndentationError
> mutation in a patch file, while the tree was byte-clean before and after (the adval HOLD that
> caught it). This explains BOTH prior sessions' "transient IndentationError, self-healed,
> byte-clean vs HEAD" hauntings (2026-07-12, 2026-07-12b — same file, same error), and predicts
> the persistent case: a hard process kill (e.g. session-limit kill) inside the window leaves
> the mutation ON DISK. **Fix (own gated build):** mutate a sandboxed copy (temp tree +
> path-redirected test invocation) — never the live file; interim discipline: never read/diff/
> commit the tree while a gauntlet/mutation pass runs, and treat any IndentationError matching a
> documented mutation-proof payload as this class. D-record at next closeout.

> **★ 2026-07-12c SESSION QUEUE — RETURN EVAL EXECUTED SAME DAY (operator present; D160/D161):**
> 1. ~~Live-smoke D153~~ **DONE — LIVE-PROVEN n=1** (the D160 statusline grill; EV-1 accepted +
>    emitted to the real vault + recall read-back; PR #29). Scope note: kata-initiate Path-A/B
>    close-out legs ride the next real initiation run.
> 2. ~~stash@{0}~~ **DONE — forensics complete** (one lost artifact recovered, PR #28) **+ DROPPED**
>    (D161); stash-empty closeout tripwire cleanly enforceable.
> 3. ~~Statusline/GSD decision~~ **DONE — D160** (grilled live): kata-native segment ·
>    replace-in-kata-scopes · vestiges dropped. ~~**NEW BUILD ITEM (gated, M8-adjacent): the
>    kata-native statusline segment**~~ **BUILT + GATED (D162 frozen design) — LIVE-RENDER-UNPROVEN**:
>    shared `adapters/claude/kata_scope.py` (the ONE walk: `find_kata_root`/`is_kata_scope`/
>    `resolve_start`) + drift test pinning both call sites (gauge hook + chain wrapper) to it;
>    `statusline_chain.py` kata leg renders the pinned segment and never runs the child in kata
>    scopes; full suite green + ruff clean. **Honesty label: built + gated, the segment actually
>    rendering in a live kata-cwd session is UNPROVEN** — rides the SAME next session as the F-9/R6
>    live smokes (item 4; one repo-cwd session collects all three).
> 4. **F-9 + R6 live smokes — STILL OPEN** (the only remaining return item): need a session started
>    with cwd INSIDE the harness repo (the gauge hook's kata-scope gate walks UP from cwd; C:\Dev
>    does not qualify). Then flip GROUNDING-CLAUDE G1b + adapter README GROUNDED-BY-PATTERN →
>    CONFIRMED.
> 5. Optional: Defender exclusion for C:\Dev (admin; lock-amplification reduction only).
> 6. ~~Ratify provisionals~~ **DONE — D161, all seven LOCKED** (two riders: elevate brainstorm
>    inherits the hosting grill's model; free-text escape always present).
> 7. ~~Unify `statusline.py` onto `kata_scope`~~ **DONE — D164, 2026-07-13 (spec
>    `.planning/specs/statusline-scope-unify/DESIGN.md`):** `kata_scope` home moved to
>    `tools/` (core; no-shim, both adapter consumers re-pointed at their own depths);
>    `statusline_from_event` now routes through the ONE walk + ONE resolution — fresh profile
>    gains subdir + `kata.config` recognition; drift test extended to all three consumers.
>    Renderer restyle offered and operator-DECLINED (s1.5 freeze intact; decline = signal).
>    *(Original item preserved below for the record.)* The
>    fresh-profile renderer `adapters/claude/statusline.py` (`statusline_from_event`) still carries
>    its OWN third kata-scope check (`<cwd>/.kata` existence) and is a SECOND kata renderer distinct
>    from the chain wrapper's new segment. The D162 build (D1/D2) deliberately touched only the chain
>    wrapper; unifying the fresh-profile renderer's scope check onto the shared `kata_scope` helper —
>    and reconciling the two kata renderers — is the named follow-up. Not drift: recorded out-of-scope
>    in DESIGN S5 (G5) and carried here.
> *(2026-07-12b queue disposition: #1 ELEVATE → DONE D153 PR #24 · #2 single-question UX → DONE
> D153 PR #24 · #3 residuals → C-4 DONE D154, R6/F-9 open (cwd-blocked, above), PostToolUse
> cadence still evidence-gated, B1 recall-beyond-initiation DONE D156, A5 + memory-pointer LOWs
> unchanged-accepted · #4 first-run fallback → DONE D155 PR #25.)*

> **★ 2026-07-12b SESSION QUEUE (deep reviews + second-brain loop; operator-directed) — SUPERSEDED
> by the 2026-07-12c block above (disposition noted there):**
> 1. **"ELEVATE" recommendation step (NEXT SESSION, operator-priority):** at the END of every grill
>    session — on EACH KataHarness execution — the harness uses its deep context + task understanding
>    to make ONE brainstormed recommendation (more only if the user asks) that elevates the design and
>    function of the output. Always-on, single by default. Natural home: a grill-close step after the
>    convergence gate, beside the D151 learn-feed emit (and its recommendation is itself grill-ledger
>    material → second-brain input).
> 2. **Grill single-question UX (operator note 2026-07-12):** the doc-grounded grill must ask via
>    Claude's single-question output (AskUserQuestion) ONE question at a time — never a multi-question
>    dump ("throwing five out there isn't a good UX"). Applies to the grill tier skills' interactive
>    flow on the Claude adapter; general design discussion stays conversational prose.
> 3. **Deep-review residuals NOT built this session** (ledgers: this session's audits; built items are
>    D151/D152): C-4 autoCompactWindow backstop stays recommend-only (separate decision needed);
>    R6 attended live-proof EXECUTION (now possible post-D152 install; run it); **F-9 UserPromptSubmit
>    live-smoke** (flip GROUNDING-CLAUDE G1b + adapter README GROUNDED-BY-PATTERN → CONFIRMED after the
>    live install crosses the threshold in a kata cwd); PostToolUse-cadence
>    gauge sampling if UserPromptSubmit proves too coarse; B1 recall beyond initiation (kata-orient/
>    workers); A5 platform docs carry no pointer-structure reinforcement (cosmetic); memory does not
>    re-assert pointer discipline (orthogonal-by-design, revisit with engram CONSULT).
> 4. **7th-source first-run fallback (adval observation, 2026-07-12b):** on a FRESH project the recall
>    feed_dir row can never fire in run 1 (Phase 1b runs before bootstrap writes kata.config; row is
>    config-gated per SB-L6c). Follow-up decision: fall back to `kata_settings.default_learn_feed_dir`
>    when no kata.config exists, so G3's cross-project recall works from the first grill.

> **★ 2026-07-12 HEALTH-REVIEW FOLLOW-UPS — ⚠ MOSTLY BUILT; THIS BLOCK WAS STALE (corrected 2026-07-25).**
> The review's **Round 3** ("wire these up and fix ALL of these disconnects") built **every named
> health-review deferral** — see `.planning/REVIEW-FABLE5-2026-07-12.md` §Round 3. A 2026-07-25 audit
> re-verified each against code. **Items 1–6, 6c (F4/F5), 6d, and 8 are DONE.**
> **STILL OPEN — only these three:**
> - **6b (partial) — gauntlet gaps:** ruff LANDED (`gauntlet.py:74`); **no type checker · no coverage
>   floor** (CI runs `--cov` with no `--cov-fail-under`) · **no SCA path** (uv export → pip-audit; the
>   Snyk resolver can't read the uv manifest).
> - **6c (partial):** precompact `custom_instructions` output-key assumption (F6 — verify the host
>   actually reads it, or drop to the ref-commit-only guarantee); kata_trail error-path tests (T-3);
>   kata_dispatch injection-only seam (T-4, accepted/documented).
> - **7 — `_safe_path` consolidation (Q-12):** only PARTIALLY addressed — `test_path_guard_family.py`
>   pins all 29 `..`-guards as a drift-guard, but the 16 hand-copies were never consolidated.
>
> *(Original list preserved below for the record — do NOT plan work off it without checking the
> status above.)*
> 1. **STEERING channel real wiring** (F-3 follow-up): a boundary-cadence STEERING.md check in
>    kata-orchestrate + a real AGENT_STOP kill-switch. STEERING.md header now states honestly that
>    today it is a manual convention.
> 2. **Gate-input validation pass** (Q-2/Q-3/Q-6): grounding_gate `groundsToPlan` enum + empty-verdicts
>    vacuous-true; deviation.run_funnel hard-require `refuted`/`sparse_signal`.
> 3. **Benchmark integrity trio** (Q-8/Q-9/DET-11): malformed test-ID raise (not fail-as-test-failure);
>    truncated mutation.json ⇒ vacuous; explicit rank tie-break key.
> 4. **Gate-runner env sanitization** (DET-09): strip PYTEST_ADDOPTS / control plugin autoload; replace
>    mutation_run shell=True with argv. (Timeouts shipped this session.)
> 5. **Determinism residuals** (DET-06 diffstat COLUMNS; DET-10 evidence-digest netstring at next
>    digest-schema rev; DET-12 mac temp-path scrub + node-id separators; DET-13 content-addressed
>    benchmark id; DET-14 graph generatedAt sidecar-if-hashed).
> 6. **Small honesty/robustness LOWs** (Q-10 gate_emit exit codes + parsedCounts; Q-13 researcher
>    normalize grounding parity; Q-14 board-unreadable degraded flag; Q-15 approval CORRUPT-vs-absent;
>    Q-16 git timeouts; Q-17 precompact stderr trace; Q-18 ledger skippedLines; S-5 rate-table date;
>    S-6 web-viewer error surface; W-3 orphan helpers; W-6 banner invocation form; W-7 kata-validate
>    scope hint; L-3 proposal-path convention — kata-improve's LOCKED PROPOSAL dir vs where the
>    one real T2 proposal lives; M-2 ruff --fix pass over tests/).
> 6b. **Gauntlet gaps (M-1)**: add ruff + a type checker (hints exist, unverified) + a coverage
>    floor (one-off 2026-07-12 measurement: 97% total) + an SCA path that works with uv
>    (uv export → pip-audit; Snyk resolver can't read the uv manifest — deferred-security note).
> 6c. **Round-2 residual LOWs** (adapters/second-opinion): kata_overlay list-item key
>    regex (F4 — misreads non-indented `- k: v` as a top-level key); kata_preflight
>    `allowed_registries` naming footgun (holds manager names, not URLs); precompact
>    `custom_instructions` output-key assumption (F6 — verify the host actually reads it,
>    or drop to the ref-commit-only guarantee); kata_trail error-path tests (T-3);
>    kata_dispatch injection-only seam is accepted/documented (T-4).
> 6d. **CI is absent entirely** (T-1/T-2): the 2 integration tests + the 3 symlink install
>    tests never run automatically; add the S-07 CI exception and a pre-tag checklist that
>    runs `-m integration` and one non-Windows (or Dev-Mode) suite pass.
> 7. **`_safe_path` consolidation** (Q-12): shared helper or validator textual-identity check over the
>    16 hand-copies.
> 8. **Push discipline**: `f40a973` sits on local master unpushed (direct-to-master docs commit) —
>    operator decision to push or re-route.

> **★ v0.2.1 POST-MERGE TEST QUEUE (2026-07-05, operator-directed order — R6 leads):**
> 1. **R6 — live host-fired compaction end-to-end** (the ONE unproven leg of CA-A1): an ATTENDED
>    interactive session in a throwaway profile where a REAL auto-compact fires ⇒ SessionStart(compact)
>    re-anchor ⇒ next task zero-loss + kata-orient 3-tier context-quality grade. Every mechanical +
>    hook-I/O leg is already proven (LIVE-PROOF items 1–2); only the host-fired link remains.
> 2. **R1–R5 + R7 attended-host checks** (LIVE-PROOF item 7 residuals): auto-compact firing margin,
>    PreCompact stdin schema capture, gauge total_tokens-vs-autoCompactWindow capping, attended bridge
>    cadence, hook sync-time budget, install-time chain-or-skip OFFER.
> 3. **Calibration follow-on proper** (CALIBRATION-FINDINGS): τ/weights tuning — now UNBLOCKED by the
>    C-1 signal fix (D149) but needs fresh instrumented runs that EMIT `verify.owned` before τ gets a
>    fair test; wire the C-3 `verdict×tier` ledger columns in the same pass.
> 4. **LD7 × M4 attempt topology + ACP/Quick + non-Claude live legs** (contract-conformance shipped,
>    live exercise deferred).
> 5. **kata_settings atomic writes** (final-review LOW, engine reviewer finding 5): temp+`os.replace`
>    on every settings writer — the same discipline `write_bridge` already has; bites only under
>    concurrent same-home sessions.
> 6. **Adaptive-vs-static LIVE A/B (D150 follow-on, operator-directed 2026-07-05):** two arms,
>    identical seeded multi-task protocol, `models.adaptive` + `premium.scope` pinned per arm
>    (AT-L22); measure premium calls, evaluator calls, wrongful-kill count, wall clock, tokens —
>    the measured successors to SMOKE-MODELED's −86% premium-call / −93% FP-class-token modeled
>    numbers. Rides the same post-R6 instrumented runs as the calibration follow-on.
> 7. ~~PokeVault install / MindBridge ingest~~ **RESOLVED — D165 (PR #35, 2026-07-14), scope
>    corrected by operator:** MindBridge is OUT of kata scope permanently (operator-side platform,
>    never a work item — memory `mindbridge-hands-off`); "install" was reframed to **second brain
>    = user-definable optional target** + the PokeVault recommend-once flow. E1/E2's instrumented
>    unblock also landed in the same run (first verify.owned ledger row).

> **★ ACTIVE INITIATIVE (2026-07-02, D138): Milestone 2 — Freeze/Float (operator-directed).** This is the
> current focus, NOT any item below. Milestone 1 (Release Hardening) shipped (PR #4). Freeze/Float ship order
> **M1→M4→M2→M3**; **M1 COMPLETE + MERGED (PR #5, D137-D140)** — P0+P1+adval+P2 all shipped; **M4 (inline evaluator/reroll) is next**, after the operator-directed test path (new-project one-shot / version-up / debug run — the float needs its first live proof). See `ROADMAP.md`
> "Post-v0.1 hardening + efficiency track" + `specs/freeze-float-m1/`. The items below remain deferred/optional
> and are picked up only when the operator redirects there.

## ✅ v0.1 cluster — COMPLETE (2026-06-30, tag `v0.1.0`)

All five items committed, pushed, and gated before the release tag. Final full adval:
**2141 pytest PASSED / validate 47/0 / Snyk medium+ 0**.

1. **Sprint-cadence D15/A5 review SHIP** ✅ — fresh-context `kata-review` of the sprint-cadence build
   (D78–D85); SHIP verdict clears the final pending gate on the sprint-cadence milestone.
2. **Wiring-completeness interim pin** ✅ — prose pointers added to `kata-evaluate` item 9 and
   `kata-review` 6(b) marking the full produced-vs-consumed sweep as a post-v0.1 ORCHESTRATOR
   INTEGRATION-GATE step (supersedes ad-hoc discovery; the full build is SCHEDULED for v0.1.x).
3. **Guard-consistency repo-wide** ✅ — `_safe_path` guards in `mutation_run`, `grounding_gate`,
   `escalation`, and `intent_scaffold` unified to raise `ValueError` (the more catchable/consistent
   choice) on `..` traversal; eliminates the mixed `SystemExit`/`ValueError` class.
4. **CWE-23 `.snyk` record** ✅ — standing `.snyk` policy entry for the 17-LOW operator-supplies-own-path
   class in `kata_install.py`; below the medium+ gate; accepted as a known standing item.
5. **Benchmark machinery n=0→n=1 live** ✅ — the clone→dual-gate→score→scorecard chain ran clean on a
   cloned **synthetic** control (`0d3e729`, real `uv run pytest` subprocesses). **Correction (2026-07-02):
   the earlier wording "on a real control fixture, proving not synthetic-fixture-only" was an over-claim —
   it ran on a SYNTHETIC control.** The **real operator-supplied control fixture (benchmark-D5) is still
   DEFERRED**; the engine is not yet proven on a real control repo (CONTEXT.md honesty-pin).

## ↳ Explicitly deferred to v0.1.x (post-v0.1 release)

These items were in-flight or identified during the v0.1 build. None blocks the v0.1 core contract;
each is a hardening, quality, or audit item safe to ship as a patch. Deferral is intentional and
operator-approved.

- **#6 — Benchmark→improve hook (D3):** wire `kata-loop-benchmark` results into `kata-improve` T2
  optimization proposals. *Safe to defer: benchmark engine is live and useful standalone; the hook is an
  efficiency improvement, not a correctness gate.*
- **#7 — Planning-approach ↔ delivery-mode alignment audit:** confirm `kata-plan` tiers + roadmap layer
  align coherently with one-shot / sprint / version-up delivery modes; surface any bootstrap/orchestrate
  routing mismatch. *Safe to defer: the three modes work today; the audit is a consistency check, not a
  functional gap.*
- **#8 — Debug Mode live run (n=0→1):** first end-to-end live run of Debug Mode on a real repo.
  *Safe to defer: Debug Mode is functionally complete at the skill/seam level (P1+P2+P3 built, gated,
  reviewed); the live run is the confidence exercise, not a build item.*
- **#9 — AO lateral/module-rollup test seam:** add a pytest seam proving `kata-orient`'s nearest-module
  rollup + `kata-graph` adjacency pointers resolve correctly on a real multi-module target. *Safe to defer:
  AO degrades correctly to root-only today; the seam exercises forward-wiring that is inert until a
  multi-module consumer exists.*
- **#10 — Recurrence-hardening: `kata-promote` gate + T3 auto-author.** The T2 detector
  (`tools/recurrence_detect.py`) + the `kata-improve` v0.2.0 auto-DRAFT proposal loop **shipped in
  v0.1.0 (D118)**. Remaining: wire the proposal through `kata-promote` (D118 deliberately routed it to
  `kata-review`→human-merge) and T3 (auto-authoring the guard itself, C-arc-gated). *Safe to defer —
  the detect→draft→human-merge loop is live; promote-gating + auto-authoring are enhancements, not
  missing safety.*
- **#11 — β redaction filter — ✅ DONE (verified 2026-07-25; this entry was stale).** Built during the
  second-brain work: `tools/learn_feed.py` carries `redact` — the SB-L4 deterministic scrub with fixed
  apply order, bounded patterns (linear scan, no backtracking), `[REDACTED:<class>]` substitution, and
  per-page counts surfaced in frontmatter (`redactions: N`, emitted only when N>0).
  *(Original deferral rationale: the β LEARN feed was emit-only with no CONSULT; risk rose only when a
  real second-brain backend was bound — which then happened, and the filter landed with it.)*
- **#12 — Validator deeper checks (A1 REVIEW backlog):** structural checks for
  `check_protocol_schemas`/`check_taxonomy_present` (substring → structural) + `kata/...` prefix
  allowlist for `check_tags_namespace`. *Safe to defer: current checks catch the common cases; the
  deeper checks prevent edge-case erasure/bogus-namespace that have not bitten in practice.*
- **#13 — A3 REVIEW carry-overs:** (a) `tools/` example-`kata.config` coherence check; (b)
  `kata-readiness` Scope-1 wording for version-up on existing codebases; (c) `tiers`-key format
  enforcement (bare-verb vs `kata-<verb>`). *Safe to defer: three doc/validator polish items; none
  affects runtime correctness.*

**Also post-v0.1: wiring-completeness full build** (SCHEDULED) — `tools/` produced-vs-consumed sweep
helper + tests + mutation bite + realistic-fixture e2e trace as an ORCHESTRATOR INTEGRATION-GATE step.
Supersedes the interim prose-pin (cluster item 2 above). Size M; grill → freeze → build. Refs:
`.planning/PROPOSAL-phantom-reuse.md` + `specs/recurrence-hardening/`.

---

## ⟳ 2026-06-30 restore-hardening (D132–D135) — BUILT + follow-ups

Restore-hardening spec (`specs/restore-hardening/`) built + committed on `phase-2/restore-hardening`
(Increment A `8a020e2` commands+installer; Increment B `0e160c2` durable board + PreCompact hook +
task-granular restore). **D133** recovery-ref git carve-out · **D134** task-granular re-dispatch ·
**D135** board-is-the-trail (supersedes D132's continuous-replay-SPINE scope). Gate: pytest 2170 /
validate 47/0 / Snyk medium+ 0 / frozen install untouched; adversarial sweep SHIP after catching +
fixing 3 silent-under-dispatch bugs (heading-parse, unbounded history, unreadable-plan swallow).

Non-blocking follow-ups (surfaced by the SHIP sweep — all safe-direction, none a correctness gate):
- **#14 — Restore fork-point same-commit edge.** `collect_integrated_tasks` uses an exclusive
  `<fork>..<head>` range; a task whose `Kata-Task:` trailer sits on the SAME commit as a squashed
  plan-freeze is re-dispatched (over-dispatch — safe; canonical flow commits plan-freeze standalone so
  it doesn't arise). *Consider: include-the-boundary or detect squashed-freeze.*
- **#15 — Nested `waves:` value guard.** `parse_plan_tasks` handles canonical flat `waves: {w: [ids]}`;
  a nested `{w: [[a,b]]}` value would `str(list)` a bogus id into the set (over-dispatch — safe;
  ownership keys remain authoritative). *Consider: validate waves value shape.*
- **#16 — Restore degraded-mode signal is stdout-only.** The unbounded-fork-point fallback prints a
  NOTE but returns no structured field; a programmatic caller can't detect degraded mode. *Consider:
  add `bounded: false` / `warnings: [...]` to the `restore()` return dict.*

### Adval deferrals (2026-07-02 integrated M1→P1 sweep, D139)

- **#17 — RESULT.json has no security-state carrier field (adval F6-4).** `kata-report` must quote the
  security terminal state (`clean|accepted|degraded|off`) "verbatim from `.kata/RESULT.json`", but
  `run_result.build_result` carries no security field of any shape — the reporter is ordered to quote a
  field that does not exist (interim: report prose says `unrecorded`, never fabricate). *Fix: add an
  optional `security` state field to `build_result` + evaluate writes it + dash model consumes the state
  (test_kata_dash_model still count-shaped).*
- **#18 — `.snyk` named as THE acceptance artifact in a tool-agnostic gate (adval F6-6).** L6-verbatim, so
  compliant with the freeze — but incoherent when the wired scanner isn't Snyk. *Fix: future L6 amendment —
  "the scanner's native suppression/policy file (e.g. `.snyk`)".*
- **#19 — Sprint-blind guard doesn't cover config namespacing (adval F3-8).** `test_sc_orchestrate_stays_
  sprint_blind` pins orchestrate PROSE only; `REQUIRED_PROTOCOL["config.md"]` lists neither
  `livenessDeadline` nor `securityScan` — re-namespacing either under `delivery.` in config.md would pass
  every test. *Fix: extend validator/protocol schema checks (composes with #12).*
- **#20 — Preflight cleanup-recommendation helper bypasses the F1 shape guard (adval F1-3).**
  `kata_preflight.py` cleanup path reads `manifest.get("dependencies", [])` raw — a misspelled-key manifest
  collapses to `[]` and could mark a still-needed package `safe_to_remove`. Advisory-only, pre-existing.
  *Fix: route the helper through the same shape validation.*

---

## ⟳ 2026-06-24 strategy + hardening session (D98–D101) — pointers
- **D98** standing adversarial red-team wired + `kata-evaluate` item 9 (reproduce-don't-trust). **DONE.**
- **D99** loop-learning strategy: A-now / C-destination / B-trap; **Second brain + Recall + Reason** model
  ("engram" retired, rename pending); `kata-loop-benchmark` promoted to keystone. BRIEF:
  `specs/second-brain-learning/` — **grill → freeze → build (the Recall *contract* is the load-bearing design).**
- **D100** fix-loop hardening (thrash budget + material re-verification) — **BUILT through the main loop** (`fc7f4f7`).
  Honest: wired, exercised by **zero real thrash events**; N=2 + ceiling provisional pending dogfood calibration.
- **D101** recurrence hardening — when a failure-class recurs, harden the responsible agent (gated). BRIEF:
  `specs/recurrence-hardening/`. **★ FIRST INSTANCE ✅ DONE (2026-06-25, D102, `47648bf`):** the
  **phantom-machinery / over-claimed-reuse** guard shipped — `protocol/reuse-claims.md` + pointers in
  `kata-design-doc`/`kata-plan` RUBRIC/`kata-tdd` + validator regression rule + T-fire proof-of-fire (full recipe,
  D98 red-team SHIP). Record: `specs/recurrence-hardening/{PLAN-phantom,REPORT-phantom}.md`. **REMAINING (general
  build):** the detector + `kata-improve` proposal loop + `kata-promote` gate — **grill → freeze → build** the BRIEF.
  *(⚠ SUPERSEDED by D118/v0.1.0: the detector (`tools/recurrence_detect.py`) + `kata-improve` v0.2.0 auto-DRAFT
  proposal loop SHIPPED in D118. Only the `kata-promote` gate + T3 auto-authoring remain — see #10 above.)*
- **★ wiring-completeness gate — full build (SCHEDULED, after v0.1 cluster).** A `tools/` produced-vs-consumed
  sweep helper + tests + mutation bite (mirror `test_exec_safety.py` registry-completeness check) + a
  realistic-fixture end-to-end trace — run as an **ORCHESTRATOR INTEGRATION-GATE step** (NOT a no-write
  `kata-evaluate` item, which collides with the no-write invariant). Supersedes the interim prose-pin
  (2026-06-30); `kata-evaluate` item 9 and `kata-review` 6(b) hold a POINTER to this gate. Refs:
  `.planning/PROPOSAL-phantom-reuse.md` + `specs/recurrence-hardening/`. **Size M, tier standard. Grill →
  freeze → build.**

## ★★ PRE-PUBLIC PRIORITIES (operator notes, 2026-06-21 — post-S3b review) ★★
These are the operator's own end-of-S3b notes; several gate going public. Captured verbatim-in-intent.

- **WS-1 — Separation / IP hygiene (✅ DONE 2026-06-24; pre-public re-grep CLEAN).** The work-internal sister project's
  **proper name must not appear on any surface** — scrub it everywhere, replacing with indirect terms ("the work
  host", "an external/work ACP host", "the work backend"). **Quick is deliberately KEPT** as the named **ACP-host
  target** — it is the **integration seam** for plumbing the work backend in later, and the docs/skills carry
  explicit **pointers** marking that seam (without naming the work project), so the future plumb-in is low-friction.
  Public FM targets to start: **Claude + Codex**; **Kiro** public (v0.3 adapter); **`quick`** = the ACP-host
  plumbing anchor; **`other`** = catch-all. The platform enum is now `claude | codex | kiro | quick | other`
  (Codex added; the work proper-noun removed). **Done so far:** `protocol/intent.md` enum, `kata-initiate`
  Phase 2c + STOP gate, `AGENTS.md`, `docs/DESIGN.md`, `README.md`, `.planning/PROJECT.md`, `protocol/engram.md`,
  the two module `AGENTS.md`, DECISIONS/STATE, and the frozen-spec proper-noun mentions. **✅ Final
  public-sanitization re-grep DONE 2026-06-24:** name + variants returned **0 matches** across all tracked files,
  frozen specs, and the working tree (incl. untracked artifacts); the Quick/ACP plumbing seam is intact (20 files);
  scrub is consistent indirection (not bare deletion); light secret/key sweep clean. Also hardened `.gitignore`
  (`/INTENT.md` root run-artifact + `.claude/`) so stray artifacts can't leak. *(Kiro kept — it is a public Amazon
  product, not the internal work host; flag if it should also be gated.)*

- **WS-2 — Validate the INNER (harness) loop's autonomy + parallelism (the operator's confidence gap).**
  **[STATUS 2026-06-22 (D94): rolling-frontier PARALLELISM + the in-loop RS RESEARCH PATH are now LIVE-PROVEN 7/7
  via the `kata-slop-check` version-up dogfood (`specs/kata-slop-check/PLAN.md` + `specs/ws2-loop-autonomy/AUDIT.md`).
  ✅ WS-2 polish DONE 2026-06-24 (D97, `4d8f01b`): worker self-timestamping wired — workers self-stamp `CLAIM`/`DONE`
  with their own clock to the shared board; the gate derives `.kata/concurrency.json` (maxInFlight · per-task
  wall-clock · overlap windows) via an in-context snippet in `protocol/board.md` (NO new Python). Concurrency is
  now provable from artifacts alone, closing the orchestrator-written-timestamp caveat. Record: `specs/ws2-polish/PLAN.md`.
  Still deferred BY DESIGN: in-loop LEARN-between-iterations (β emit-only, D74) + engram CONSULT (D9/D56).]**
  The operator is NOT confident the harness loop genuinely runs autonomously for long stretches. Validate, with
  evidence: **(a) parallelism** — are we using subagents properly? Is the orchestrator actually running concurrent
  workers that check/communicate laterally (board), per Anthropic's long-running-agent best practice — and is it
  *better than Hermes*? Build a way to **evaluate** that parallel processes are used properly (not just dispatched
  serially). **(b) in-loop autonomy** — the harness loop should run **internally for long periods with no human**:
  LEARN between internal iterations, run **research internally** (RS), and **self-grade/QC within the loop**. NOTE
  the real gap: the β LEARN feed is **emit-only, zero CONSULT** (D74) and engram CONSULT is gated off (D9/D56), so
  "learn between loops" is **not happening today by design** — decide whether to light a bounded in-loop learning
  path. The greater (kata) loop is fine requiring human interaction; the *harness* loop's autonomous endurance is
  what needs proving. **Deliverable:** an honest audit + a validation harness, not a claim.

- **WS-3 — User-friendliness, front-to-end (must precede public launch).**
  **[✅ BUILT 2026-06-24 (D95; merge `d08908d`; spec `specs/ws3-user-friendliness/{DESIGN,PLAN}.md`) — persona
  (`protocol/persona.md`) · narration map (`protocol/narration.md`) · reflective goal-mirror intake · one-dial
  mode surface · milestone narration · goal-anchored by-aspect closeout. Built + gate-PASS + fresh-eval PASS 10/10;
  **field-exercised (n=1) via the two-tier-closeout build (D96, `c265c42`)** — first live use of the friendly
  surfaces; operator refined the brand at the gate (first KataHarness logo · Hokusai palette · tiles). Adaptive
  register is a gated seam, not live.]** The whole system is technical, not
  intuitive. Likely a **combination** of a **persona/voice context file** AND **explicit voice in the skills**.
  Sub-items:
  - **Decision tree must be human-readable, not machine-oriented.** Speak in terms of the **modes** we set and
    *infer* behavior from mode selection, rather than exposing machinery.
  - **Goal-centric intake.** Be far more intuitive about understanding the **GOAL** — what is the user actually
    trying to achieve — and feed that to the loop true to the user's desired changes (the synthesis of the initial
    **system prompt + brainstorming + research + grill results**), not a mechanical form.
  - **In-loop narration.** While the loop runs, **don't call out stage names** (GRILL/FREEZE/…); **talk through
    what the agent is actually doing**, in human terms.
  - **Strategic progress display.** Show enough that the user trusts it's working and making progress, **without**
    spamming useless model internals or inviting them to butt in. Inspire confidence; surface **critical
    errors/alerts** prominently. Trust-building, not log-dumping.
  - **Verbose, goal-anchored closeout.** At the end: **restate/recall the goal**, focus on **what changes the loop
    made to achieve it**, **assess progress toward the goal**, and **call out uncertainties + risks** so the user
    can decide to iterate the kata loop again or go back and re-prompt/re-grill. **Link to the findings files** so
    the user can open and review them.
  - **Research Hermes's UX** (people are happy with how it guides users) for both the in-loop narration and the
    closeout — borrow the guidance pattern (keep our gates, D69).

- **WS-4 — Backout / rollback as a first-class option (safety).**
  **[✅ BUILT into WS-3 slice F (D95) — `kata-closeout` offers backout in plain language, anchored on the emitted
  `.kata/RESULT.json.baselineSha` (`git reset --hard`), human-gated & never autonomous, surfaced at the human
  gate. Field-exercised (n=1) via the two-tier closeout build, D96.]** There MUST be a surfaced way to **back out the
  loop's changes** if a run goes off the rails. We have `pre-s<n>` backout tags, but rollback must be an explicit,
  offered option at the human gate — not a buried git incantation.

- **WS-5 — Change transparency at closeout (the acute miss this session).**
  **[✅ BUILT into WS-3 slice F (D95) — `kata-closeout` + `kata-report` lead with plain-language what-changed-why,
  organized by goal-aspect, before any path or gate number. Field-exercised (n=1) via the two-tier closeout build, D96.]** The closeout must make **exactly what
  changed** legible to a non-expert owner ("I had no idea what changes were made"). Overlaps WS-3's closeout item;
  call it out as a hard requirement: every closeout leads with a plain-language "what changed and why it matters to
  you," with links, before any machine detail.

- **Two-tier closeout — native in-tool rendering (M8 follow-up, 2026-06-24; adapter work).** The two-tier closeout
  shipped (D96): a concise CLI/GUI summary + a self-contained branded HTML report (`.kata/closeout.html`) +
  Markdown source. **Open:** surface the report *natively per host* — a Claude **`Stop`/`SessionEnd` hook** that
  opens/links `.kata/closeout.html` + a **statusline** verdict line (`✅ goal hit · backout: …`); Codex/Kiro/Quick
  via their adapters. Today the link is a clickable file path in the summary. Folds into the v0.3 adapter layer.
  Spec: `specs/ws3-closeout-report/PLAN.md` (Carry-outs). Also reusable: the **first KataHarness logo** (inline SVG
  in the template / `BRAND.md`) for favicon / docs / statusline glyph.
- **Gate-enforcement hardening (loop-hardening red-team residue, 2026-06-21 — non-blocking).** The S2/S3a
  adversarial review left three deferrable items. **(a) MAJOR-3 — machine `codeBearing` flag: ✅ DONE (S3b Cycle 2,
  `222cc7e`)** — `footprint.py` `code_bearing()` derives the flag from changed-file globs → `footprint.json`
  `codeBearing`; `kata-evaluate` rubric item 1 keys off it (BC fallback). **(b) NIT-2 — validator no-write
  assertion: ✅ DONE (S3b Cycle 1, `f72a3bb`)** — `validate_skills.py` `check_evaluator_no_write` asserts
  `{kata-evaluate, kata-research}` omit `Write`/`Edit`. **(c) NIT — guard consistency (REMAINING):**
  `mutation_run`/`grounding_gate`/`escalation` raise `SystemExit` on `..` traversal while `intent_scaffold` raises
  `ValueError`; pick one (ValueError is the more catchable/consistent choice) across the `_safe_path` guards.
  *(MAJOR-1/MAJOR-2 were fixed inline — D92; MAJOR-2 live-proven in S3b. Only the guard-consistency nit remains.)*
- **★ Planning-approach ↔ delivery-mode alignment (FUTURE assessment, user 2026-06-21).** Assess the **planning
  approach** (`kata-plan` essential/standard/advanced tiers + the roadmap layer `kata-plan/ROADMAP.md`) and confirm
  it **aligns coherently with each delivery mode in place**: **one-shot**, **sprint (incremental)**, and
  **version-up**. For each: is the plan *shape* right? (one-shot = a single frozen `PLAN`; sprint = `ROADMAP`
  boundary-amendable → per-sprint immutable `PLAN-s<n>`; version-up = footprint-scoped plan vs the most-recent-green
  baseline). Verify `kata-bootstrap`/`kata-orchestrate` route to the correct planning depth **and** shape per mode,
  and surface any mismatch/gap (e.g. does the roadmap layer fire only when `delivery.shape == incremental`? does
  version-up reuse the right planning tier?). *(Non-blocking; post-loop-hardening; raised right before the S3b
  loop-back test. This sprint cadence — `ROADMAP` → `PLAN-s<n>` → freeze → orchestrate — is itself live evidence to
  audit against.)*

- **★ BRIEF — Capability-aware ("multi-modal") agent assignment (2026-06-25, big Phase-5 item).** Detect the
  target's **stack** (languages + frameworks + build/test tooling + config/IaC file-classes present, plus what's
  **installed** in the env) → route each task to a **specialist agent** (per-language coders + config/context
  specialists, as prompt-profiles over the spine). A routing layer over `kata-orchestrate`'s existing dispatch,
  NOT a new orchestrator. **Resolves the "multi-modal — separate brief?" question the `multi-model-orchestration`
  BRIEF flagged**; distinct axis from model/host routing. Primary consumer = Debug Mode. BRIEF:
  `specs/capability-aware-assignment/BRIEF.md`. Depends on install-portability (detection) + `kata-graph`. **Grill → build.**
- **★ BRIEF — "Debug Mode" delivery mode (captured 2026-06-24, enriched 2026-06-25; do NOT build yet — grill first).**
  A one-shot run-shape **sibling to Version-Up**, opposite intent: hold features/structure **fixed**, run a
  **systematic deep-debug pass** (assess all modules/tie-ins/logic; bugs out, behavior preserved; promote coding
  efficiency). The pitch = **"point it at a repo and debug in confidence"** — nothing broken, bugs fixed, via the
  language-specialist debug agents + the security stack (Snyk + `kata-evaluate` + D98 `kata-review`). **The
  onboarding/conversion killer-app**: the ideal first run for a dev who installs KataHarness, before converting
  their repo to the loop + moving into the vault. Reuse-maximally (a mode over the Harness, not a parallel stack):
  `kata-diagnose` · `kata-graph` · version-up footprint+no-regression discipline · `kata-evaluate`/`kata-review` ·
  `kata-tdd` · closeout/backout. **Borrow** from industry agentic debuggers (the installed
  `superpowers:systematic-debugging` + `gsd-debug`, SWE-agent, OpenHands, Aider) — keep our gates. **A top-level
  MODE (peer of version-up), selected and pointed at a whole codebase — self-contained; NOT a debug agent injected
  into the loop/other modes (anti-bloat). Specialists live INSIDE the mode; does NOT depend on
  capability-aware-assignment** (independent item; may converge later). BRIEF: `specs/debug-mode/BRIEF.md`. Open: the
  behavior-preserving / no-structural-drift gate (load-bearing) · systematic-sweep planning · the
  fix-vs-improve line · 4th mode to align (planning-approach↔delivery-mode).
- **★ DOGFOOD #2 RESIDUAL — wire the eval artifacts into a live gate (NEXT increment, 2026-06-19).** Dogfood #2
  built the *libraries + contracts* for evaluation self-sufficiency (`tools/run_result.py`, `footprint.py`,
  `mutation_check.py`; `kata-report`/`kata-evaluate` require them) but **nothing yet CALLS them** during a real
  run — the fresh-context evaluator flagged it as the headline residual. Next slice: make `kata-evaluate`/the
  gate command actually **emit `RESULT.json`** (via `run_result.run_gate`+`build_result`+`write_result`), compute
  the **footprint manifest** against the plan, and record the **mutation-proof** result — so depth is delivered
  end-to-end, not staged as parts. (Cosmetic: `mutation_check.went_red`/`non_vacuous` are always-equal — tidy.)
- **★ DOGFOOD #1 FINDINGS (2026-06-19, self version-up — see `.planning/specs/dogfood-selfup-1/`).**
  - **★ Evaluation-artifact self-sufficiency (HIGH — the headline).** A live run must be **evaluable in depth
    from its end artifacts alone** — today it is not. Upgrade `kata-report`/`kata-evaluate` to **self-emit**: a
    `RESULT.json` (gate name + **verbatim** stdout + exit codes + pass/fail counts + timestamp), **baseline +
    result commit SHAs**, a **footprint manifest + diff-stat** (assert touched ⊆ plan), a **recorded mutation/
    non-vacuity proof** (bake "would this test fail if its asserted line were removed?" into `kata-tdd`), and a
    **corpus-wide new-findings delta**. Directly answers the user's "is the writeup enough?" → no. *Strong
    candidate for dogfood #2.*
  - **version-up tree-sitter BLOCK too coarse (R1).** `kata-readiness` BLOCKs every version-up when tree-sitter
    is absent, even changes that need **no** structural graph (docs/validator-only footprints). Scope the BLOCK
    to runs that actually require `kata-graph` (or make graph optional when the footprint ∌ code structure).
  - **manual-drive friction (R2).** The loop ran without automated orchestrate/worktree dispatch or an installed
    host — confirms [[install-portability]] + [[multi-model-orchestration]] are real, not theoretical.
- **research/NOTES.md deep-eval** — score mattpocock skills, BMAD, GSD; record exactly what each
  `kata-*` skill adopts from where (the core bake-in work). *(do before/with v0.1)*
- **Adapters** — `codex`, `kiro`, `acp-quick`; AGENTS.md→tool-instruction-file normalization; skill-format mapping. *(v0.3/v0.4)*
  - **Per-tool instruction-file mechanics (D60–D63 AO forward-dependency, user 2026-06-18):** Claude = `CLAUDE.md`
    pointer→`AGENTS.md` (done); **Codex** = reads `AGENTS.md` natively incl. nested (~zero work); **Copilot** =
    `.github/copilot-instructions.md` (AGENTS.md support firming up) → pointer/generator; **Kiro** = **steering**
    (`.kiro/steering/*.md` with inclusion modes: always / `fileMatch`-glob / manual) — **NOT a tree-walk**, the
    structurally-different one. **AO seam:** `kata-orient`'s agnostic orientation contract (`protocol/orientation.md`:
    tiers + nested-module rollup + `kata-graph` adjacency pointers) is *rendered* per tool by the adapter — Claude/
    Codex→nested AGENTS.md/CLAUDE.md tree-walk; **Kiro adapter must render the module rollup as steering `fileMatch`
    files**, not per-folder tree-walk files. Verify current Copilot AGENTS.md adoption + Kiro steering details at
    build time (facts may have moved past the Jan-2026 cutoff). Captured for design later; do NOT reopen frozen specs.
- **`kata-engram`** — cognitive-fingerprint/engram injection from kiban/kagami; gated on a mature second brain. *(v0.4)*
  **[RE-MODELED 2026-06-24 (D99): "engram" is retired → Second brain (data) + Recall (per-vault Librarian/adapter) +
  Reason (`kata-reason`, the Advisor/decider). The whole C-arc + four-tumbler unlock + the C/B invariant are specced
  in `specs/second-brain-learning/BRIEF.md`. The engram→second-brain rename across `protocol/engram.md`/E1–E23/
  D9/D56/D74/D65/CONTEXT is a PENDING migration (own contract pass). This item folds into that BRIEF.]**
- **Engram-mediated escalation (FUTURE phase, harness-wide — A4-GB10)** — every human-in-the-loop escalation
  *anywhere* in the harness routes through the engram: (a) consult the cognitive fingerprint first → auto-resolve
  known patterns, only novel decisions reach the human; (b) feed every human resolution back into the engram so
  the next identical escalation auto-resolves. Net: human interrupts asymptotically decrease as the engram matures
  → strengthens the long-running promise. **Gated on PokeVault installed (READY, D58) + cognitive-fingerprint
  synthesis built**; grows from `kata-engram` (D9). Ties to the cognitive-twin arc (kiban/kagami). Prereq for
  trusting version-up's escalate-not-silent-expand at scale.
- **Plugin packaging** — package the suite as a Claude Code plugin + a portable bundle; `plugin.json`/suite version.
- **License selection** — choose an OSS license before public release.
- **★ FUTURE-GAP BRIEFS (ordered; quick plan docs written 2026-06-19, to grill→freeze→build AFTER the
  dogfood/improvement passes — except #1's timing is to-confirm).** Each is a `BRIEF.md` (pre-grill, not frozen):
  1. [[install-portability]] — `.planning/specs/install-portability/BRIEF.md` (workspace config + modular
     per-platform install: optional PokeVault link · bring-your-own-vault scaffold · aim-each-folder; the work/ACP
     host brings its own installer; setup doc cordoned with pointers). **Foundation for #2/#3.**
  2. [[multi-model-orchestration]] — `.planning/specs/multi-model-orchestration/BRIEF.md` (host-located
     orchestrator [work host→Quick/ACP · Kiro/Claude→there] · per-component model/tool routing incl.
     eval+test · cross-model handoff on one filesystem). Depends on #1.
  3. [[testing-model]] — `.planning/specs/testing-model/BRIEF.md` (**assess** a purpose-specific testing/eval
     model as a routed quality component; contract unchanged, only the model). Leans on #2.
- **★ Install & portability layer (NEXT after self-dogfood — the "plug into any vault/project" bridge).**
  Today the harness operates *in its own repo*; getting it to run against an arbitrary user's vault or project
  dir needs two unbuilt layers: **(1) distribution/discovery** — place the skills where the host agent finds
  them (Claude Code plugin or `.claude/skills/`; other tools via adapters) — overlaps "Plugin packaging" + the
  v0.3 adapter layer (spine #3); **(2) a one-time workspace-binding config** — distinct from per-run
  `kata.config`: user-set **roots** (vault root · project root · where `.planning/`, the LEARN feed
  `engram.learnFeed.dir`, and candidate skills `agentSkills.dir` live relative to the user's workspace). The
  config schema already has the *seeds* (those dir fields are path-configurable); what's missing is the init
  flow + the top-level workspace binding so it is **not PokeVault-shaped**. Likely a small spec → a `kata-install`
  /init capability. **Sequencing:** self-dogfood (needs none of this) → spec this layer → plugin packaging +
  adapters. *(Raised 2026-06-19 in the positioning/portability assessment — "control + plugs into your vault".)*
- **PokeVault install path (D58)** — the *reference* instance of the install & portability layer above: how the
  PokeVault vault (`C:\Users\taurr_nvs748q\PokeVault\PokeVault`, `toolkit/` area) installs/pins KataHarness.
  (Replaces the retired CPP consumption path, D57.)
- **Protocol specs** — flesh out `protocol/{board,tasklist,state,handoff}.md` schemas.
- **Quick/work version** — fork/branch strategy for the AWS-internal variant.
- **`kata-tasklist` reframe (D23)** — virtual task board over GSD structure + backlog, syncing to Jira/Asana
  via MCP (env has `pm-skills`/`atlassian`). Replaces the old file-locked-claim purpose.
- **A3 REVIEW carry-overs (2026-06-08, non-blocking)** — (a) `tools/` example-`kata.config` coherence check
  (validate a config's `tiers` keys resolve, `mode`/`effort` valid, modules have providers) — the maintainer-time
  complement to orchestrate's runtime load-guard (GB12/D45). (b) **A4:** sharpen `kata-readiness` Scope 1 wording
  so "validator green" clearly means the *harness* install vs the *target* repo when running version-up on an
  existing codebase. (c) `tiers`-key format (bare-verb vs `kata-<verb>`) is documented-consistent but unenforced.
- **Validator deeper checks (A1 REVIEW backlog)** — (3.1) `check_protocol_schemas`/`check_taxonomy_present`
  use substring matching → can't detect substantive erasure; add structural checks if it bites. (3.3)
  `check_tags_namespace` allows bogus `kata/...` sub-namespaces; add a `kata/...` prefix allowlist when
  `kata/tier/<tier>` becomes load-bearing (A2-time).
- **AO lateral/module-rollup is unexercised until a multi-module target (D76 follow-up, 2026-06-19)** — the
  validation stack confirmed `kata-orient`'s **nearest-module `AGENTS.md`/`CLAUDE.md` vertical rollup** + the
  **kata-graph lateral adjacency pointers** are a **latent no-op in *this* repo** (only root `AGENTS.md`/`CLAUDE.md`
  exist; no `kata.graph.json` on a greenfield run). It **degrades correctly** to root-only (graceful, triplicated
  in orientation.md / kata-orient / the AO hook) — forward-wiring for the 2026 nested-AGENTS.md standard, not a
  bug. **Exercise + test it when the harness orients inside a real multi-module target** (e.g. the dogfood
  version-up on KataHarness itself, or a consumer repo with per-module instruction files): add an AO test seam
  that proves rollup picks the nearest module + adjacency pointers resolve. Until then it's correct-but-inert.
- **β-runtime: structural redaction filter + test seam (D74 follow-up, 2026-06-19)** — today the LEARN-feed
  redaction (C3) is a **prose contract** (`kata-handoff` §7 "confirm no secrets/keys/PII") the emitting agent
  honors; "fail-closed" is an instruction, not enforcement. The β feed writes synthesis to an **external dir**
  (egress surface). **When β goes runtime** (the dogfood/ε arc), add an **automated redaction filter** the emit
  path must pass + a **pytest seam** that proves a secret/PII-bearing page is blocked. Until then the guarantee
  rests on agent obedience. *(Security-domain priority before any real second-brain backend is bound.)*
- **AI-slop / spiraling-session detection — ✅ BUILT 2026-06-22 (D94) as `kata-slop-check`** (standalone optional
  module `kata/module/slop`; general checks G1–G6 + 3 MIT-attributed checks from ai-slop-detector; fresh-context
  no-write; default-FAIL `SLOP-DETECTED ⇒ NEEDS_WORK`; dispatched in EVALUATE alongside `kata-evaluate`). The design
  fork below (**embed in `kata-review` vs separate skill**) was RESOLVED → **separate skill**. Original note kept for
  provenance:* ingest the OSS
  **ai-slop-detector** (`https://github.com/flamehaven01/ai-slop-detector`) and **deep-eval which of its checks
  to adopt** to catch **spiraling agents / degraded sessions / AI-slop output** — a common, real risk in
  long-running loops. **Design decision to make:** *embed* the adopted checks into `kata-review` (a new
  review axis / mode) **vs.** stand up a *separate* skill that runs as part of the EVALUATE phase (e.g.
  `kata-slop-check`, dispatched alongside `kata-review`/`kata-evaluate`). Lean on the **minimal-step bake-in
  discipline** (D41/GB8 — extract only the necessary stripped-down checks; do not over-port). **License + `source:`
  attribution required** before adopting any code (spine #12 / D12 — verify the repo's license). **Seams:** ties
  to `kata-review` (adversarial), `kata-diagnose` (bad-session symptoms), and `kata-selfhandoff` (session-health
  trigger — slop/spiral signal could fire a self-handoff/abort); a slop verdict should be a **default-FAIL gate
  finding**, never advisory-only. Captured for a later spec; do NOT reopen frozen specs. *(post-v0.1; quality module.)*
- **`kata-report` (D32)** — post-loop, handoff-phase build report: lite-synthesis of loop artifacts (DESIGN,
  DAG, decision ledger, manifest, diffs, evaluate/review verdicts, gate numbers) → durable `BUILD-REPORT.md`
  with a Mermaid structural diagram (of our own build DAG). Non-goal: from-scratch comprehension — that is
  `kata-understand`'s job (the two are complementary: report = what the loop did, understand = what the code
  is). Feeds `kata-improve`; open pointer for a future PM overlay (D30). Baseline near-free (spine-light);
  visuals tier up.
- **`kata-graph` — pre-processing structural map (PROMOTED to active A4, GB6).** New skill: builds a compact
  symbol/dependency map of an **existing** codebase so grill/plan/orchestrate ingest a large repo cheaply
  (token-saving). The version-up ingestion engine (was working-name `kata-map`). **Optional module
  (`kata/module/graph`, GB10) — the version-up preset bundles it by default. The *skill* ships in A4**;
  the *accelerated backend* (Graphify's AST graph / an MCP graph server) stays an **optional adapter binding,
  never a core dep** (agnostic core = grep/glob/Read; pre-staged via D29). Usage discipline for the accelerated
  backend if adopted: AST-only in-loop, bounded `--budget` queries, out-of-context oracle, NO always-on hook,
  no semantic pass in-loop. Plan it by evaluating OSS minimal-step examples (GB8). Graphify attributed in
  `source:` (spine #12).
- **`kata-understand` — post-processing comprehension map (desired state, GB7).** Post-loop comprehension map
  of a **newly-built** codebase → helps the *user* navigate/understand what KataHarness created (Understand-
  Anything nod). **Distinct from `kata-report`:** report = build-log synthesis (comprehension is its non-goal);
  understand = from-scratch comprehension of the result. **Optional module (`kata/module/understand`, GB10).**
  **Base: Understand-Anything** (`Lum1104/Understand-Anything`, MIT — purpose-built for teach-the-human
  comprehension/onboarding: `/understand-onboard`, `/understand-domain`; "graphs that teach"); Graphify a
  secondary source (multimodal/infra). Compose pluggable skills, don't fork-splice (A4 RESEARCH §5b). Name by
  job not vendor (§5c). Own later spec, post-v0.1. Plan via OSS minimal-step eval (GB8).
- **`kata-defer` — in-loop deferral / "nice-to-haves" capture (GB9).** Optional module
  (`kata/module/defer`). During a run, any out-of-scope-but-worth-keeping item (nice-to-have, post-processing
  candidate, deferred-for-a-reason) is appended to a run-scoped `DEFERRED.md` instead of being dropped or
  scope-crept into the frozen plan; compiled at HANDOFF; feeds project backlog / `kata-improve` /
  post-processing. **The structural complement to no-drift** (#1/#2): the pressure-release valve that makes
  one-shot=no-churn sustainable. Name soft (`kata-park`/`kata-icebox` alt). Post-v0.1 unless pulled forward.
- **Research mode (major post-v0.1 spec — path-forward brief done 2026-06-09, `.planning/specs/research-mode/RESEARCH.md`).**
  A `research` run-shape + module: `projects/Research/<project>/` roots; a recursive loop of disciplinary
  **research** + **adversarial-validation** + **evaluation** agents (the Co-Scientist roster). Thesis: the SAME
  spine with three swaps — work-unit = question/hypothesis, conformance floor = an **evidence floor** (citation
  integrity + adversarial survival + empirical ratchet; the never-tiered D22 analog), roster = disciplinary
  researchers. Reuses `kata-review` (adversarial), generalizes the bake-off judge (Elo tournament) and
  `kata-graph` (→ evidence graph `protocol/evidence.md`), and **shares the KG-emit contract with
  `kata-understand`** (research-mode is the upstream producer that fills the PokeVault vault, D58). Empirical sub-loop =
  Karpathy's ratchet = version-up's no-regression gate. Optional backends (GPT Researcher / STORM / Co-Scientist
  OSS) behind module contracts (the aider/Graphify pattern). **Sequence:** after v0.1 validation (D16) + Spec B
  (bake-off judge) + the Obsidian-KG/`kata-understand` spec. Coherence-audited (no chimera). Discipline-lens
  registry + recursion/budget guard (depth×breadth×exploration) are the only genuinely new substrates.
- **`design` module (own spec)** — UI/UX, 2D/3D assets, slides, mobile, image-FM imagery; slots into Advanced.
- **`docs/TAXONOMY.md`** — categories + `kata-<verb>` naming + tier-family convention (`kata-<verb>-<tier>`) +
  spine-vs-module. Motivated by the modes tiering work; partially specced in `docs/MODES-DESIGN.md`.
- **Skill efficiency refactors** (`.planning/SKILL-COST-RATINGS.md`) — grill L8-narrative + convergence
  checklist → `resources/` (~30% lighter); orchestrate worker-prompt → `protocol/`; tdd supporting-depth → pointer.
  Fold the grill one into Spec A (we restructure grill for tiering anyway).
- **★★ FINAL-PHASE — Deep loop optimization + an agentic-loop benchmark module (mid/long-term, user 2026-06-22).**
  **[PROMOTED 2026-06-24 (D99): `kata-loop-benchmark` is no longer just speed-garnish — it is the KEYSTONE that
  *defines* the C-arc unlock. It proves "C-on beats C-off" on a fixed reference task, which is what makes the
  second-brain readiness gate falsifiable. Build it alongside the C-arc, not strictly last. See
  `specs/second-brain-learning/BRIEF.md`.]**
  Do **near the end** of building KataHarness, once the feature set is implemented: **tune the loop** for **context
  economy AND speed/latency** (not just token cost). Build a **`kata-loop-benchmark` development module** that runs
  the loop on a **fixed reference task** (same content each time) and scores the output on **accuracy · quality ·
  speed** — a repeatable harness to measure tuning gains. Survey GitHub for an existing **agentic-loop / AI-process
  optimization benchmark**; adopt or borrow pieces (license + `source:` per D12). **Goal:** offset KataHarness's
  rigor with **speed** so output is balanced — *more controlled than Hermes (including the learning portions) at
  similar performance*, but with our controlled, high-quality output. Sequenced **after** WS-3/4/5 + Phase-5
  EXTERNAL. Ties to: WS-2 worker-self-timestamping (real timing data feeds the benchmark), the [[testing-model]]
  brief, and [[multi-model-orchestration]] (per-component model/speed routing).
- **★★ FINAL-PHASE — Recursive parallelism: "DAG within DAG" (advanced orchestration research, user 2026-06-22).**
  Today `kata-orchestrate` is **flat**: one orchestrator → leaf workers over a single frontier. Investigate letting
  the orchestrator, when it detects a **truly separable module**, spawn a **nested sub-loop** (a full Harness
  GRILL→…→EVALUATE on its own frozen sub-plan) rather than a single worker — **DAG-within-DAG**, recursive. Sub-loops
  run **concurrently** (each owning a disjoint file-subtree, its own default-FAIL gate intact), and the parent
  integrates only **green, independently-evaluated module artifacts** — two levels of parallelism = more parallel
  surface area, the speed win. **The load-bearing piece = a HARDENED separability test** — the thing that makes the
  orchestrator *smarter*: it recurses **only when decomposition is a provable win**, never an overcomplication or
  collision (handle more at once, at high judgment + high efficacy). Design it as a **conservative gate:
  default-FLATTEN unless proven separable** (mirrors default-FAIL — burden of proof is on recursion). Criteria:
  **transitive disjoint file-ownership** across the whole sub-tree (kata-graph-checkable → no collisions) · **no
  shared LOCKED decisions** · a **clean declared inter-module interface** (the only coupling allowed) · module size
  **above the overhead break-even** (small ⇒ flatten; the benchmark above sets the threshold) · module-level acyclic
  deps. The cut is **checked by a fresh-context evaluator, not self-certified** (no-self-cert spine), with
  **cross-level escalation bubbling** (a sub-loop's human-required surfaces to parent/human) and a future **engram
  learning surface** (learn which cuts paid off). A bad cut yields coupled sub-loops that fight at integration — so
  strictness is the whole game. **Survey prior art:** Hermes (recursive subagent trees) + Anthropic managed/
  orchestrator-worker + classical HTN/hierarchical planning. `kata-graph` could *propose* the module cut from the
  structural map. Research-grade → own BRIEF → grill → spec; post-v0.1. Composes with the loop-optimization benchmark
  above + [[multi-model-orchestration]] (sub-loops route to different models).
