# KataHarness

### One-shot complex coding tasks — with the guardrails that make autonomy trustworthy.

KataHarness front-loads deep, doc-grounded planning, **freezes the plan**, executes it faithfully across one or
many subagents, and refuses to call anything "done" until a **fresh-context, default-FAIL evaluator** proves it —
then folds every run's lessons back into itself. The name *is* the method: the **Improvement Kata** — *every loop
sharpens the loop.*

> **v0.3.0 · experimental.** NEW in v0.3.0 (Adaptive tiering): model selection stops being a static
> table and starts learning from the run. A task that keeps failing its gate is **bumped up a rung for
> its next attempt**; work the plan graded low-complexity or a class on a clean-pass streak **steps
> down**; kill verdicts get a **cheap-then-escalate second opinion** before any redispatch (where a
> higher below-anchor tier exists to give one — the leg is stated-inert otherwise); and the
> expensive top rung (Fable today — any family's premium model tomorrow) fires **only on configured
> hard moments, inside a call budget you approve up front**, with every move a loud board line.
> Modeled on this repo's own prior build: **−86% premium-rung calls** vs class-scoped elevation
> *(modeled, not measured — the live A/B is queued)*. v0.2.1 shipped context autonomy (the 8-hour
> walk-away design); v0.2.0 the inline evaluator — both below.
> HONEST LIMITS: the live host-fired-compaction leg (R6) is queued first, the adaptive-vs-static live
> A/B rides the instrumented runs after it; ledger-driven acceptance routing (L2) ships as contract with activation OFF until
> real run volume exists; the single-model Claude core is the proven, dogfooded path (KataHarness
> builds itself); Codex/Kiro adapters are install-supported with partial live proof; the other platform
> guides are config-docs-only; IaC *apply* is gated and not shipped runnable. We're honest about
> maturity — that honesty is the product. New here? Start with [`AGENTS.md`](./AGENTS.md).

---

## Why it stands apart

Most "agentic loops" are a thin wrapper around *prompt → generate → hope*. The disciplined ones that do
validate tend to buy rigor with tokens — an LLM judge on every step, whether or not anything is wrong.
KataHarness refuses that trade. It is built for **both**: deep, adversarial validation *and* measured
token/wall-clock efficiency, in one loop.

- **⚡ Deep validation that costs ~nothing when the work is green.** The inline corrective ladder triggers
  on cheap, rule-verifiable evidence (test exits, lane drift, missing records) — **an LLM judge runs ONLY
  after a trigger**, at an economy tier. Measured on this repo's own instrumented v0.2.1 build (retroactive
  scan, real commits, not arranged): **44 of 57 worker checkpoints scored green — 0 evaluator calls, 0
  tokens on every one** (corroborated 25/31 on the integrated branch). The green path is free; the red path
  gets judgment. Fixed-cadence "judge every step" harnesses pay that cost on every step.
- **🧊 The plan doesn't drift.** The plan is *frozen* after planning; the orchestrator guards it; worker
  subagents execute and talk laterally but **never re-plan.** An unknown escalates or parks — it is never
  silently guessed.
- **🛡️ Nothing certifies its own work.** A **fresh-context, no-write, default-FAIL** evaluator independently
  reads the evidence and must return PASS — backed by an **adversarial review** before every merge. In this
  project's own build, those fresh-context reviews have repeatedly caught real defects a 2,895-test green
  suite had blessed (the v0.2.1 merge gate alone caught and folded two HIGHs).
- **🔋 The run outlives the context window.** v0.2.1's gauge-driven self-handoff + crash-proof resume: a
  compaction, crash, or killed terminal costs you a wave boundary, not the run.
- **🧠 A learning loop with a gate.** Telemetry from every run feeds threshold calibration; lessons distil
  into candidate skills — but promotion is **two-stage and human-gated**, never silent self-modification.
- **🏁 It benchmarks itself.** A built-in scoring engine ranks candidate approaches on real fail-to-pass /
  pass-to-pass evidence and produces an **honest scorecard** — quality you can measure, not vibes.
- **🧩 Tool-agnostic core + thin adapters.** One agnostic core (protocol, skills, planning engine, quality
  loop) with per-tool adapters and per-platform config guides — not locked to one vendor.
- **🪶 Zero-dependency install.** A pure-stdlib Python engine; one command drops it into your agent host.

---

## The Kata Loop

Six phases, every run feeding the next:

```
GRILL   →   FREEZE   →   EXECUTE   →   EVALUATE   →   HANDOFF   →   IMPROVE
interrogate  lock the    plan-faithful  fresh-context   durable,     distil + promote
the spec     design +    parallel       no-write,       two-way,     lessons back into
             the plan    workers        DEFAULT-FAIL    git-committed  the skills → next run
```

---

## What's in the box

### ⚡ The inline evaluator/reroll — DSpark-informed loop economics *(v0.2.0)*
The best-of-both-worlds core. The scheduler discipline is adapted from DeepSeek's **DSpark** paper
(confidence-scheduled speculative decoding) — not its inference code, its *principles*, translated to the
harness layer: a **separate cheap confidence signal** (never the worker self-scoring — rule-verifiable
trailer evidence only), **acceptance-length as the metric** (clean-checkpoint streaks per task class),
**per-class leashes** (code gets a long leash on cheap verifiable signals; research/debug trigger shorter),
**calibration from logged verdicts** (the telemetry ledger), and the **verifier's final say** (the
default-FAIL gate stays the untouched authority, so a mistuned ladder degrades to exactly today's behavior).
Explicitly rejected: fixed-cadence mid-task LLM judgment — an LLM judge costs about a chunk to judge a
chunk, so periodic judgment on green work is a net loss. Live-proven: trigger → diff-cited verdict →
corrective redispatch → green. `inlineEval: off|telemetry|on`; absent ⇒ off, byte-for-byte backward
compatible.

### 🎯 Adaptive tiering — evidence-driven model routing *(new in v0.3.0)*
Three layers. **L0** — the relative differential table stays as the deterministic base and only
fallback (no data, no events ⇒ exactly the frozen behavior). **L1** — the run's own evidence modulates
each dispatch: a task that fails its gate twice is **bumped one rung up for its next attempt** (once
per task, from gate rejections and standing reroll verdicts only — never a worker's self-report); a
plan-rated low-complexity task or a class riding a 3-clean-first-pass streak **steps one rung down**
(coding work only, capped at −1, with a damper that stops oscillation the moment a downshifted
dispatch fails); a `correct`/`reroll` kill verdict gets **one second opinion from an evaluator a rung
up — strictly below the anchor** — before anything is killed, and only the standing verdict counts
(where the screening tier is already one rung below the anchor, the leg is INERT — stated, never
silent, and the kill proceeds on the single cheap verdict).
The **premium rung is event-scoped and budgeted** (the new object-form scope, which the composer now
writes by default; the v0.2.1 class-scope form stays valid, byte-for-byte): approve once and it fires
only on the configured hard moments (freeze-gate verdicts, HOLD re-reviews, escalations,
failed-task retries…), capped at N
calls with the last two reserved for freeze-gates — the consent prompt enumerates your exact event
list and budget, and exhaustion lapses to the anchor loudly. Every adaptive move is a board `tier:`
DECISION line (also the restart-recovery trail). Modeled on this repo's real v0.2.1 build shape via
the shipped engine: **−86% premium-rung calls** (59→8) vs run-long class scoping, and **13→0 wrongful
kills** on the pre-fix false-positive trigger mix *(modeled, not measured — every input cited in the
committed SMOKE-MODELED artifact; the live A/B is queued with arms pinned)*. **L2** — ledger
acceptance routing (a class *earns* a cheaper tier from recorded first-pass acceptance) ships as
contract with activation OFF until post-R6 run volume exists. Family-agnostic by construction: the
mechanism knows "the premium rung," not a model name — a GPT-5.6-class rung qualifies by registering
its family's ladder entry plus the adapter's model-ID map (per-adapter re-grounding, no mechanism
change). Backward compatible: no `models.adaptive` block ⇒ every leg OFF.

### 🔋 Context autonomy — the 8-hour walk-away *(v0.2.1)*
The conductor watches its own context gauge (a statusline **bridge** on Claude — installed chain-or-skip,
your own statusline is **never clobbered**) and self-hands-off at 0.70 of the effective window: durable
`HANDOFF.md` committed **before** any reset, host compaction recommended-never-written, a
SessionStart(compact) hook that re-anchors the fresh context, and resume at the next task boundary with
zero task loss. Where no gauge exists — headless `-p` runs were **verified on our host** to never tick
the statusline — deterministic N-wave rotation covers the same guarantee. One **preflight approval bundle** collects
everything up front (installs, permission allowlist, compact-window recommendation, host-settings writes,
the premium-model gate, the stranding check) so an unattended run never stalls on a prompt — and a
walk-away run missing every recovery leg is **BLOCKED at preflight**, not discovered dead 6 hours in.
The v0.2.1 loop also got measurably cheaper end-to-end: an identical-protocol A/B rerun of the v0.2.0
smoke measured **−23% conductor tokens / −44% tool calls / −29% wall clock at exact outcome parity**
*(n=1, directional, and not surgically attributable between the shipped riders and same-span prose
evolution — the full caveats are recorded in the committed LIVE-PROOF)*.

### 🧠 The learning loop — Hermes-informed, human-gated
The cross-run learning arc borrows from a formal deep-research bake-off of the **Hermes** learning-loop
agent — its prompt-builder tiering shapes `kata-orient`'s three-tier orientation assembly, its closed
learning loop shapes the improve→promote arc — with the bake-off verdict applied deliberately: **borrow
the mechanisms, keep our gates** (Hermes ships no default-FAIL testing model; ours is the spine).
Concretely: a committed **telemetry ledger** (schema v3) records every instrumented run's acceptance
streaks, per-class stats, cost columns, and failure kinds (the per-checkpoint signal vectors ride in
committed `Kata-Checkpoint` trailers) → threshold calibration works from logged verdicts,
never vibes; **recall** surfaces prior lessons/decisions/recurrences read-only at initiation; and
`kata-improve` distils run lessons into candidate skills that only enter the toolkit through
`kata-promote`'s **two-stage human gate**. The loop learns; nothing self-modifies silently.

### 🎛️ Frontmatter as the contract — and no model IDs, ever
Every skill's frontmatter is machine-read policy: **semver** (format validator-enforced; bump-on-modify
by standing convention), **cost-weight** (drives run-cost previews), **allowed-tools** (least-privilege per skill),
**source attribution**, and tags — the catalog below is auto-generated from it, so docs can't drift from
reality. Deliberately **absent**: any `model:` pin. Model routing is **relative to your session's anchor**
(critical work at the anchor, economy work tiered down; an optional four-conjunct-gated premium rung
above — **event-scoped and budgeted in its new default form, and modulated per-dispatch by run
evidence** when the v0.3.0 adaptive layer is composed on), so a renamed, gated, or unavailable model ID
never breaks the loop — and economy tiering is itself a token optimization baked into every dispatch.

### 🌐 Platform compatibility
One agnostic core; per-platform delivery at three honesty levels. **Claude Code** — the proven, dogfooded
adapter (hooks, statusline bridge, slash-commands; KataHarness builds itself on it). **Codex CLI · Kiro**
— installer-supported platforms (`--platform codex|kiro`), with the multi-model dispatch chain live-proven
on a real Codex install. **Gemini CLI · GitHub Copilot · Cursor** — shipped recommended-configuration
guides (`docs/platforms/`) mapping each host's context, checkpoint, and settings model onto the harness
contract; the deterministic-rotation leg is designed exactly for hosts with no gauge. Docs-first is
deliberate: a platform gets promoted to "supported" by live proof, not by a README claim.

### 🔁 Crash-proof resume
A session death — a crash, a killed terminal, an auto-compaction that wipes context mid-build — no longer costs
you the run. KataHarness keeps a **durable, git-committed progress trail** and restores the exact frontier:

- **Durable board.** The live work-board is snapshotted to a dedicated git ref (`refs/kata/trail`) with pure git
  plumbing — it never touches your working tree, never pushes, and can't corrupt a thing.
- **Auto-checkpoint before compaction.** A pre-compaction hook is wired to checkpoint the board *before* the
  context window is squeezed. *(Being live-verified: that Claude's PreCompact hook fires synchronously with a
  usable budget. Even if it doesn't, your progress is already durable at every integration checkpoint — above.)*
- **Task-granular restore.** On resume, `/kata-resume` re-derives which tasks were finished (from the git
  history, the authoritative source) and re-dispatches only the ones that weren't — no double work, no dropped
  work, no manual reconstruction.

### 🏁 Built-in benchmarking
Quality you can *measure*, not assert. A complete two-axis scoring engine ranks candidate build artifacts on real
**fail-to-pass / pass-to-pass** test evidence (weighted by a mutation-non-vacuity multiplier) and produces an
**honest scorecard** — it distinguishes a genuine all-pass from a vacuous one, with **no free credit for tests
that never ran**. *(v0.1 scores single-arm + k-repeat runs; the parallel multi-arm bake-off driver — launch N
approaches at once, judge, and promote the winner — is the next planned capability.)*

### 🐞 Debug Mode — a bug-hunting pipeline
Point it at a failing or mysterious codebase and it's *designed* to work like an engineer, not a guesser: build a
**function model** of the code, run a **deviation-discovery** pass to surface where behavior diverges from intent,
generate a **characterization suite** that pins current behavior, **diagnose** root cause (light or full depth),
and hand back a **debrief** with confidence and an optional version-up offer. *(Built and wired — P1–P3, gated on
`kata/module/debug`; proven on seeded fixtures. Launch it with `/kata-onboard` on a fresh repo, or just ask for a
**debug run** at `/kata-start` — "debug my repo".)*

### ☁️ Specialized Infrastructure-as-Code agents
First-class IaC specialists for **Terraform** and **CloudFormation**, injected automatically when a task touches
infra. They share a **safety contract** (`protocol/iac-safety.md`): structured plan-only argv, a **Snyk IaC**
scan gate, an explicit approval-artifact gate, and **no destructive `-target`**. Authoring, review, and planning
are live; *apply* is deliberately gated behind approval and not yet shipped runnable — safety before convenience.

### 🎚️ Modes, tiers & relative model routing
Three **modes** (**Essential · Standard · Advanced**) set breadth and depth. Tiered skill families
(`kata-grill`, `kata-plan`, `kata-review`, `kata-diagnose`) share one rubric and expose a depth dial. Model
selection is **relative** — critical work runs at your session's anchor model, economy work tiers *down* a rung —
so a gated or renamed model never breaks the loop, and no model ID is ever hard-baked into a skill.

### 🛡️ The quality loop
A **default-FAIL** evaluator owns the definition of "done." An **adversarial review** attacks the design before
every merge. Every code behavior is **mutation-proven non-vacuous** (a test that stays green when its assertion
is removed doesn't count). An optional **AI-slop check** fails a run for spiraling or over-claiming. And a
standing **silent-permissive-default guard** forbids decision-code from quietly degrading on bad input.

### 🔧 Adapt without forking upstream
Customize any skill via a local **overlay** or a promoted **fork** — your changes survive every update; the
upstream base stays pristine and is never edited or lost.

### 🗂️ Discoverable slash-commands *(Claude)*
`/kata` prints the index; `/kata-start`, `/kata-onboard`, `/kata-resume`, `/kata-status`, and `/kata-validate`
route straight to the right skill — no logic to drift, always in sync with the toolkit.

### 📚 48 versioned skills
Across six families — `plan` · `coordinate` · `execute` · `evaluate` · `handoff` · `meta` — plus the
`initiation` / `closeout` modules. Every skill carries a semver in its frontmatter; the generated catalog below
is the machine source of truth for what exists and at what version.

<details>
<summary><b>Full skill catalog</b> — name · version · cost · category · status · source · use (auto-generated from frontmatter; the versioning source of truth)</summary>

<!-- SKILL-INDEX:START -->
| Skill | Ver | Cost | Category | Status | Source | Use |
|---|---|---|---|---|---|---|
| `kata-comprehend` | 0.1.0 | 3 | plan | experimental | new (KataHarness original, Debug Mode P1 — function-model oracle, DESIGN LD2/LD7) | — |
| `kata-context` | 0.1.0 | 1 | plan | experimental | adapted-from mattpocock/skills {ubiquitous-language, grill-with-docs CONTEXT-FORMAT} | Build/maintain CONTEXT.md shared/ubiquitous language |
| `kata-design-doc` | 0.1.0 | 2 | plan | experimental | adapted-from mattpocock/skills {to-prd} + superpowers brainstorming + GSD spec-phase | Synthesize the frozen design doc / spec |
| `kata-graph` | 0.1.0 | 3 | plan | experimental | adapted-from aider repo-map (MIT — tree-sitter tag-queries + personalized PageRank + token budget) + Graphify (safishamsi/graphify, MIT — AST graph + MCP oracle get_neighbors/shortest_path/get_pr_impact) | Token-budgeted structural map of an existing repo (version-up ingestion); builds kata.graph.json |
| `kata-grill-advanced` | 0.1.0 | 5 | plan | experimental | adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model | — |
| `kata-grill-essential` | 0.1.0 | 3 | plan | experimental | adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model | — |
| `kata-grill-standard` | 0.1.0 | 4 | plan | experimental | adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model | — |
| `kata-plan-advanced` | 0.1.4 | 4 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-plan-essential` | 0.1.4 | 2 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-plan-standard` | 0.1.4 | 3 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-research` | 0.1.0 | 3 | plan | experimental | new (KataHarness original, loop-cognition RS-GB1/2/3, D62) — fresh-context no-write evaluator pattern (L4/L5) applied to in-loop research; escalation-routed like kata-orchestrate's no-re-plan escape valve (D52) | Research a must-deliver gap with no in-plan solution; ground every claim; return findings for the grounding gate, never re-plan |
| `kata-board` | 0.1.0 | 2 | coordinate | experimental | adapted-from Claude Agent Teams protocol (agnostic file reimplementation); CryptoPortfolioPlanner LESSONS-LEARNED L3 | Append-only mailbox/message board for lateral peer comms |
| `kata-bootstrap` | 0.4.0 | 2 | coordinate | experimental | adapted-from GSD discuss-phase Q&A model + docs/MODES-DESIGN.md D24c composition ladder (KataHarness design) | Compose a run (run-shape + ladder), preview cost, write kata.config, launch |
| `kata-initiate` | 0.2.1 | 3 | coordinate | experimental | new (KataHarness original, Phase 1 Kata Loop — D88/D91); composes kata-readiness, kata-grill, kata-bootstrap, kata-context | — |
| `kata-loop` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original — Phase 3 Kata Loop conductor, D87/DESIGN §1) | — |
| `kata-onboard` | 0.2.0 | 3 | coordinate | experimental | new (KataHarness original, Debug-Mode P3 / LD13 — DESIGN R6/LD13); a NEW composition of the BUILT install-portability surfaces (tools/kata_settings.py, tools/project_find.py, tools/kata_install.py, tools/intent_scaffold.py) + the initiate/bootstrap/closeout/loop spine skills. "convert-to-loop" and the ".planning/ scaffold" are NEW here (see "What is NEW", below), not a reused convert flow. | — |
| `kata-orchestrate` | 0.11.0 | 5 | coordinate | experimental | adapted-from cpp-orchestrator (CryptoPortfolioPlanner harness) + Anthropic effective-harnesses-for-long-running-agents + managed-agents | Plan-guardian lead: assign, partition files, gate, no-drift |
| `kata-preflight` | 0.3.0 | 2 | coordinate | experimental | new (KataHarness original, PRE-FLIGHT spine phase D29/N2); drives tools/kata_preflight.py (N1 engine); argv-builder pattern from the _COMMAND_BUILDERS registry in tools/kata_dispatch.py; injectable-runner from _subprocess_runner in tools/kata_dispatch.py | — |
| `kata-readiness` | 0.2.2 | 1 | coordinate | experimental | new (KataHarness original); pattern echoes environment "doctor" checks (e.g. brew/flutter doctor) — abstract, no external code adapted | Pre-run harness+target readiness check (bootstrap-invoked or standalone doctor) |
| `kata-sprint` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original — sprint-cadence D80; the thin boundary coordinator, GB4-C) | Own the sprint boundary (G1–G4 change-control); incremental delivery only |
| `kata-worktree` | 0.1.0 | 1 | coordinate | experimental | adapted-from CryptoPortfolioPlanner worktree proof (LESSONS-LEARNED L2/L3) | Per-owner git-worktree isolation for concurrent code |
| `kata-characterize` | 0.1.0 | 3 | execute | experimental | new (KataHarness original, Debug Mode P2b — characterization-suite generation, DESIGN LD6+§5) | — |
| `kata-deviate` | 0.1.0 | 4 | execute | experimental | new (KataHarness original, Debug Mode P2a — deviation-discovery pipeline, DESIGN LD4–LD5) | — |
| `kata-diagnose-full` | 0.1.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-diagnose-light` | 0.1.0 | 2 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-iac-cloudformation` | 0.2.0 | 3 | execute | experimental | new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4) | — |
| `kata-iac-terraform` | 0.2.0 | 3 | execute | experimental | new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4) | — |
| `kata-lang-profile` | 0.1.2 | 2 | execute | experimental | new (KataHarness original — Debug Mode LD10 in-mode language prompt-profiles, DESIGN §3 LD10 / PLAN-p3 Slice D). Selection + overlay mechanism mirrors the IaC specialist-injection precedent (skills/coordinate/kata-orchestrate "IaC activation" block + iac_detect.classify_task); STYLE templates are the sibling specialists kata-iac-terraform / kata-iac-cloudformation. | — |
| `kata-tdd` | 0.4.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/tdd | Red-green-refactor on a vertical slice |
| `kata-benchmark-report` | 0.1.0 | 1 | evaluate | experimental | new (KataHarness original — kata-loop-benchmark report; mirrors the kata-report/kata-debrief two-tier {{TOKEN}} render contract; engine tools/benchmark.py) | — |
| `kata-debrief` | 0.1.0 | 1 | evaluate | experimental | new (KataHarness original, Debug Mode P3 — LD12 closeout confidence report + LD3 recommendations / offered version-up; mirrors the kata-report two-tier + {{TOKEN}} render contract) | — |
| `kata-evaluate` | 0.3.1 | 2 | evaluate | experimental | adapted-from cpp-evaluation (CryptoPortfolioPlanner) + Anthropic fresh-context evaluator pattern | Fresh-context, no-write, default-FAIL PASS/NEEDS_WORK |
| `kata-inline-eval` | 0.1.0 | 1 | evaluate | experimental | — | — |
| `kata-report` | 0.1.2 | 1 | evaluate | experimental | new (KataHarness original — the D32 report, minimal v1; sprint-cadence D85/D2) | One-page report of a gated unit of work (reports the gate, never gates) |
| `kata-review-advanced` | 0.1.2 | 3 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-review-essential` | 0.1.2 | 1 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-review-standard` | 0.1.2 | 2 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-slop-check` | 0.1.0 | 2 | evaluate | experimental | General heuristics original to KataHarness; adopted-check concepts from ai-slop-detector by flamehaven01 (Flamehaven Labs), https://github.com/flamehaven01/ai-slop-detector, MIT License (Copyright (c) 2026 Flamehaven Labs) — concepts re-implemented as in-context heuristics, no source code copied. | — |
| `kata-validate` | 0.1.0 | 3 | evaluate | experimental | new (KataHarness original — validation mini-loop). Adapted patterns: Guardrails-AI on_fail propose-vs-apply seam; OASIS SARIF severity taxonomy (error/warning/note); Reflexion bounded self-critique loop. | — |
| `kata-closeout` | 0.1.0 | 2 | handoff | experimental | new (KataHarness original — Phase 2 Kata Loop back-half, D89/DESIGN §3) | — |
| `kata-defer` | 0.1.0 | 1 | handoff | experimental | new (KataHarness original, D42/D43 GB9) — the structural complement to the no-drift spine; assumption-log role added by D71 (Priming-and-Grill autonomous floor) | Park off-plan items + log grill-skip assumptions at the boundary, never drift the frozen plan |
| `kata-handoff` | 0.2.0 | 1 | handoff | experimental | adapted-from mattpocock/skills {handoff} + Anthropic reset-with-handoff / compaction guidance | Two-way durable handoff (session/agent/tool) |
| `kata-orient` | 0.2.1 | 2 | handoff | experimental | new (KataHarness original, loop-cognition AO-GB1/2/3 + D76) — receiving half of the two-way handoff (spine #5); three-tier assembly echoes Hermes prompt_builder (stable/context/volatile); nested-AGENTS.md rollup standard | Assemble a subagent's launch orientation: three-tier, task-type-tailored, derived pointers+callouts, routed questions — the read half of handoff |
| `kata-selfhandoff` | 0.2.0 | 1 | handoff | experimental | adapted-from Anthropic compaction guidance + mattpocock caveman compression | Configurable context-threshold self-handoff (delegates artifact to kata-handoff) |
| `kata-understand` | 0.1.0 | 2 | handoff | experimental | new (KataHarness original, Phase 2 GL-R2c / DESIGN §3 / PLAN-phase2 Task C1) — comprehension-map half of the closeout back-half; backed by the F2 graph runtime (tools/graph_gen.py → kata.graph.json) | — |
| `kata-improve` | 0.2.0 | 1 | meta | experimental | adapted-from the Improvement Kata (Toyota Kata) + mattpocock/skills engineering/improve-codebase-architecture | Fold cross-run lessons back into the skills/ tree; calls kata-write-skill |
| `kata-promote` | 0.1.0 | 2 | meta | experimental | new (KataHarness original, loop-cognition ML / LC-GB3/GB4/GB5, D60-D69) — two-stage gate vs Hermes' no-gate instant-universal model (RESEARCH.md bake-off: borrow the closed loop, keep our human gate) | Stage-2 human gate: promote a grounded agent-distilled candidate skill (experimental→stable + scope bump) into the toolkit; honors engram.autonomy |
| `kata-write-skill` | 0.1.0 | 1 | meta | experimental | adapted-from mattpocock/skills productivity/write-a-skill | Author new skills to STANDARDS (points, not restates); kata-improve calls it |
<!-- SKILL-INDEX:END -->

</details>

---

## Install

**Prerequisites:** `git`, and either [`uv`](https://docs.astral.sh/uv/) **or** Python 3.12+. The installer clones
KataHarness to `~/.kata-home` (`%USERPROFILE%\.kata-home` on Windows) and links (or copies) the skills into your
agent host. Default platform is **`claude`**; `--platform` also accepts `codex` and `kiro`.

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex
```

**macOS / Linux (and Git Bash on Windows):**
```sh
curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh | sh
```

**Choose a platform** (download-then-run so you can pass a flag — and inspect the script first):
```powershell
# Windows
irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 -OutFile install.ps1; .\install.ps1 --platform codex
```
```sh
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh -o install.sh; sh install.sh --platform codex
```

---

## Lifecycle — update · factory-reset · wipe & reinstall · uninstall

Every command below is copy-paste ready. Windows uses the scripts in `%USERPROFILE%\.kata-home\`; macOS/Linux
uses the mirrors in `~/.kata-home/`.

### ↻ Update — pull the latest engine + skills
Fast-forwards your clone and re-links the skills. Add `--check` to preview without changing anything; set
`KATA_REF` to pin a branch/tag/SHA (default `master`).

```powershell
# Windows
& "$env:USERPROFILE\.kata-home\update.ps1"            # apply the update
& "$env:USERPROFILE\.kata-home\update.ps1" --check    # preview only, no changes
```
```sh
# macOS / Linux
sh ~/.kata-home/update.sh                             # apply the update
sh ~/.kata-home/update.sh --check                    # preview only, no changes
```
> If you customized tracked base files, update **aborts** rather than clobbering them — re-run with
> `--discard-local` to overwrite, or commit/stash first. (Your overlays and forks are safe; they're separate.)

### ⟲ Factory-reset — restore pristine skills
Re-links the shipped skills without touching your clone's git history. Add `--hard` to also **clear the overlay
store** and reset the base tree (destructive — requires `--yes` when non-interactive).

```powershell
# Windows
& "$env:USERPROFILE\.kata-home\update.ps1" --factory-reset
& "$env:USERPROFILE\.kata-home\update.ps1" --factory-reset --hard --yes   # also wipe overlays/forks
```
```sh
# macOS / Linux
sh ~/.kata-home/update.sh --factory-reset
sh ~/.kata-home/update.sh --factory-reset --hard --yes                    # also wipe overlays/forks
```

### ⤾ Wipe & reinstall — nuke the clone and start fresh
Deletes `~/.kata-home` entirely and reinstalls from scratch. Safe: `~/.kata-home` is just the harness clone —
your projects and vault live elsewhere.

```powershell
# Windows
Remove-Item -Recurse -Force "$env:USERPROFILE\.kata-home"; irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex
```
```sh
# macOS / Linux
rm -rf ~/.kata-home && curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh | sh
```

### ✖ Uninstall — remove KataHarness from a project/host
Removes the flat-linked skills, the settings entry, and the router stanza from the **given** project. Run once
per project you installed into (the harness keeps no registry of every target). Add `--yes` to skip the prompt.

```powershell
# Windows
& "$env:USERPROFILE\.kata-home\uninstall.ps1" --platform claude --target-dir "C:\path\to\project" --yes
```
```sh
# macOS / Linux
sh ~/.kata-home/uninstall.sh --platform claude --target-dir /path/to/project --yes
```
> To remove the harness itself as well, follow up with the **wipe** command above
> (`Remove-Item …\.kata-home` / `rm -rf ~/.kata-home`).

---

## Start a run

Restart your agent so it loads the skills, then use a slash-command (Claude Code shown) — or just ask:

```text
/kata            show the command index
/kata-start      start a run (the front door → kata-initiate)
/kata-onboard    guided tour / convert an existing repo
/kata-status     show the live run board
/kata-resume     pick up a crashed or compacted run where it left off
/kata-validate   run the skill-conformance validator
```

> **“Start a KataHarness run on `<your project>`.”** — plain English works too; the installer prints these same
> next steps on success.

---

## Docs / status

**v0.3.0, experimental.** The single-model Claude core is the proven path; the Codex/Kiro adapters are
install-supported with partial live proof; Gemini CLI / Copilot / Cursor ship as config guides; the live
host-fired-compaction leg of context autonomy (R6) and the adaptive-vs-static live A/B are queued, in
that order; L2 acceptance routing ships activation-OFF pending run volume; IaC *apply* is gated and not
shipped runnable. Read next:

- [`AGENTS.md`](./AGENTS.md) — the vision, the spine, how to work in the repo (canonical).
- [`docs/SETUP.md`](./docs/SETUP.md) — install / update / overlay / factory-reset / uninstall in depth, plus the
  `curl | sh` security tradeoff and the audit-friendly git-clone path.
- [`docs/STANDARDS.md`](./docs/STANDARDS.md) — frontmatter, versioning, and naming conventions.

> **Security note.** `curl … | sh` and `irm … | iex` execute bytes as they stream — there's nothing to verify
> until after it runs. Pin a known ref with `KATA_REF`, or download-then-run to inspect first (see
> [`docs/SETUP.md`](./docs/SETUP.md)). On Windows without Developer Mode, the installer falls back to copy-mode
> (works fine; re-run `update` after each change to refresh copied skills).

Built on Anthropic's long-running-agent harness guidance and the best of
[mattpocock/skills](https://github.com/mattpocock/skills), GSD, BMAD, and DDD's ubiquitous language — plus
scheduler principles from DeepSeek's DSpark paper and learning-loop mechanisms surveyed from the Hermes
agent (both adopted with our gates kept in place) — attributed per skill in the `source` column and per
design doc in `.planning/specs/`. We stand on shoulders.
