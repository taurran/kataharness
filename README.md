# KataHarness

**The agent harness with a control dial — from spec-driven, interview-shaped sprint coding to fully automated,
self-learning one-shots — on one vetted, grounded process that doesn't drift, doesn't spiral, and *proves* its
own work instead of trusting it.**

Most agent loops make you pick a side — **babysit every step, or let it loose and hope.** And under the hood,
most are the same shape: take a prompt, generate, declare victory. KataHarness is built differently, on purpose.
It **interviews you first** and learns your codebase before it writes a line; it **assumes its own work is
broken** until a fresh, no-write evaluator proves otherwise; its **plan can't drift**; it **catches its own
over-claims**; it **runs across multiple models at once**; and it **gets sharper every run** — with everything
landing in **your vault**, not a black box. The name is the method — the **Improvement Kata**: each loop sharpens
the loop.

> New here? Read [`AGENTS.md`](./AGENTS.md) (canonical) → [`docs/DESIGN.md`](./docs/DESIGN.md) (the charter) →
> [`docs/STANDARDS.md`](./docs/STANDARDS.md) (conventions).
>
> **Getting started / don't have a vault?** See **[`docs/SETUP.md`](./docs/SETUP.md)** — one central install, a
> small settings file (default project folder + optional vault), and a per-platform installer. No vault needed
> to start: point it at a plain project folder and go.

[PokeVault]: # "PokeVault — the reference vault/toolkit home (install link to be added)"

---

## Why it's different from other loops

Most "agentic loops" are a thin wrapper around *prompt → generate → done*. KataHarness is a **disciplined process**
with the guardrails that make autonomy actually trustworthy. The difference, point for point:

| Most agent loops | **KataHarness** |
|---|---|
| Take a prompt and start coding | **Interview-first** — the *grill* interrogates your idea and learns your conventions into a **frozen spec** before any code |
| The agent decides when it's "done" | **Default-FAIL** — a **fresh-context, no-write evaluator** must independently PASS; *nothing certifies its own work* |
| The agent re-plans whenever it gets stuck | **No drift** — the plan is frozen and guarded; an unknown **escalates or parks**, it never silently re-plans |
| Trust the agent's self-report | **Standing red-team** — an adversarial reviewer **tries to break** every contract-bearing build *before* it merges |
| Plausible-but-fake reuse ("uses the existing X") slips through | **Verify-before-reuse guard** — the harness **catches its own phantom machinery** and forces it to be labeled new + scoped |
| One model does everything | **Multi-model role routing** — bind each role to a different model/tool: Claude codes, Codex validates, Kiro researches |
| Babysit *or* fire-and-forget | **A per-run control dial** — `skip → full` grill, one-shot ↔ sprint, essential → advanced rigor |
| Output disappears into the tool | **Your vault** — durable **Obsidian-native, git-committed** plans, decisions, handoffs you own |
| Context loss = start over | **File-based two-way handoff** — survives compaction, a dead session, or a tool switch with no re-derivation |
| Static — same agent next month | **It learns** — mines every run into a second brain; distilled skills promote through a **human gate** |
| Locked to one vendor | **Tool-agnostic** — one `SKILL.md` standard across Claude · Codex · Kiro · Cursor · Copilot |

---

## The feature set

**The throughline is _control with proof_** — keeping you in charge *and* making "done" mean something.

- 🎛️ **A control dial, per run.** Fully human-in-the-loop (spec → grill → approve each sprint), fully automated
  (a hands-off learning one-shot), or anywhere between. Nothing happens off-plan without surfacing it first.
- 🪜 **Well-defined modes, not vibes.** A consistent system of **effort/rigor tiers** (essential · standard ·
  advanced), **run-shapes** (individual · batch · version-up), and a **delivery axis** (one-shot · incremental
  sprints). Compose the run, preview its cost, launch — same format every time (consistency is the north star).
- 🗣️ **An interview that codes like you do.** The **grill** interrogates your idea, learns your codebase's
  conventions and your style, and enriches *your* intent into a frozen spec — depth dialed by you
  (`skip → light → standard → full`). Ambiguity you don't resolve up front is resolved **in-loop by a no-write
  research subagent** or parked in an assumption log surfaced at the gate — never silently guessed.
- ✅ **"Done" is earned, never declared.** Grounding gates, **default-FAIL** evaluation, a **standing
  fresh-context adversarial review** before every merge, and a **verify-before-reuse** guard that kills
  documentation-only seams. Industry-standard practice underneath (TDD, DDD ubiquitous language, vertical-slice
  planning, disjoint file-ownership, mutation-proven tests).
- 🧩 **Multi-model orchestration.** Route loop *roles* to different platforms — Claude as coder, Codex as
  validator, Kiro as researcher — coordinating over the shared filesystem, with the orchestrator as the single
  source of truth. Default is single-model; multi-modal is an opt-in at setup. *(Foundation built; full routing
  in progress.)*
- 🧠 **It gets sharper every run.** Every run mines its own decisions, reviews, and grill ledgers into a
  **second brain**; agents distil reusable skills that pass a grounding check **and a human promotion gate**
  before going universal. When a failure-class *recurs*, the harness proposes **hardening the responsible
  agent** — gated, never auto-mutated.
- 🗂️ **Lives in your own vault.** Durable artifacts are **Obsidian-native** (frontmatter + wikilinks + tags)
  and **git-committed** in *your* workspace — plans, decisions, handoffs, and the learn feed are yours to read.
- 💾 **Survives every boundary.** Two-way, file-based handoff + prime-frame self-handoff means work outlives
  compaction, a dead session, or a switch between agents/tools — a fresh agent re-enters mid-stream cold.
- 🔌 **Tool-agnostic by design.** An agnostic core + thin per-tool adapters and a shared skills format
  (Claude today; Codex/Kiro/Cursor/Copilot via the same `SKILL.md`). Your discipline travels with you, not the vendor.
- 🖥️ **You always see what it's doing.** Every run opens with an on-brand `KATAHARNESS 改善型` readout — what
  it's executing, in a glance — plus a live statusline and a durable, branded HTML closeout report.
- 🐛 **Debug Mode (designed, next up).** Point it at a whole codebase and tell it to *debug in confidence* —
  bugs out, behavior preserved — via an intent-model oracle + a corroboration-gated deviation pipeline. The
  onboarding on-ramp: convert an existing repo to the loop.

**In short — what people actually want:** an agent you can *trust* and *steer*, that *finishes*, doesn't
spiral, doesn't lose your context, fits *how you build*, proves its work, and *gets better over time* — on
whatever model(s) you use.

---

## The loop

```
                  ┌──────────────────────  the improvement kata  ──────────────────────┐
                  │            every run folds its lessons back into the harness        │
                  ▼                                                                     │
   ┌─────────┐   ┌────────┐   ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌─────────┐    │
   │  GRILL  │──▶│ FREEZE │──▶│ EXECUTE │──▶│ EVALUATE │──▶│ HANDOFF │──▶│ IMPROVE │────┘
   └─────────┘   └────────┘   └─────────┘   └──────────┘   └─────────┘   └─────────┘
   interrogate   lock the     plan-faithful fresh-context  durable,      distil +
   the spec →    design +     parallel      no-write,       two-way,      promote +
   a frozen      plan         workers in    DEFAULT-FAIL    git-committed  fold lessons
   intent        (no drift)   worktrees     gate            file           → next run
        ▲                          │                                            
        │                          ▼                                            
   research subagent ◀──── escalate (ambiguity / no in-plan solution)           
   + assumption log         resolve in-loop, never re-plan blindly              

   incremental delivery: EXECUTE→EVALUATE repeats per sprint; a controlled
   boundary (approve · label drift · adversarial sweep · snowball guard)
   sits between sprints — the only place steering happens.
```

---

## Status

**`v0.1.0-alpha` — the full loop is built, green, and self-dogfooded; hardening toward a field-proven v0.1.**
39 skills, all `0.1.0`/experimental; validator 0 errors · 540+ tests passing · Snyk clean (medium+ 0). The
complete cognitive architecture runs on the **Claude core** across **one-shot and incremental (sprint)**
delivery, with the learning loop (second-brain LEARN feed + human-gated skill promotion) wired. The harness
has been built *by itself* through its own orchestrated loop multiple times — concurrent worker subagents in
isolated worktrees, a fresh-context default-FAIL gate, a standing adversarial red-team, and human approval at
each boundary.

**Recently landed:** the **install & portability layer** (one central install + a 2-setting workspace config +
per-run project search → it drops into any vault or project dir); the **multi-model orchestration** design +
first cross-model proof-slice (route a role to Codex over the shared filesystem); the **loop-init banner**; and
a **verify-before-reuse hardening** that makes the harness catch its own phantom machinery.

**Honest about maturity:** experimental, not yet 1.0. The single-model Claude loop is the proven path;
multi-model routing, the multi-tool adapters (Codex/Kiro/Cursor/Copilot), and **Debug Mode** are designed and
partially built — see the roadmap. Live state: [`.planning/STATE.md`](./.planning/STATE.md) · roadmap:
[`.planning/ROADMAP.md`](./.planning/ROADMAP.md).

## The spine (six non-negotiables)

1. **The plan does not drift** — the orchestrator guards it; peers execute + talk, never re-plan.
2. **One-shot = no plan churn** — fix against the same plan; don't re-plan by reflex.
3. **Agnostic via adapters** — agnostic core + thin per-tool adapters.
4. **Default-FAIL** — a fresh-context, no-write evaluator gates "done."
5. **Two-way, file-based handoff** — plus prime-frame self-handoff (survives context rot without bailing early).
6. **Everything versioned** — per-skill semver is the machine source of truth; the catalog is generated.

---

## The skills

39 skills across the six loop phases (plus the initiation/closeout modules). Tiered families (`kata-grill`, `kata-plan`, `kata-review`,
`kata-diagnose`) share one `RUBRIC.md` method and expose depth tiers you dial per run.

```
skills/
├── plan/         turn an idea into a frozen, executable spec
│   ├── kata-context ........ build/maintain CONTEXT.md (shared, ubiquitous language)
│   ├── kata-grill/ ......... interrogate the spec to kill ambiguity   ·tiers: essential·standard·advanced
│   ├── kata-design-doc ..... synthesize the frozen design doc / spec
│   ├── kata-plan/ .......... vertical-slice plan: disjoint file-ownership + a wave/DAG
│   │                         └ ROADMAP.md: partition into prime-frame sprints (incremental)  ·tiers: e·s·a
│   ├── kata-graph .......... token-budgeted structural map of an existing repo (version-up)
│   └── kata-research ....... in-loop, escalation-routed, NO-WRITE researcher (grounds before it folds)
│
├── coordinate/   compose, dispatch, and guard the run
│   ├── kata-bootstrap ...... the on-ramp: compose a run, write kata.config, launch; routes sprint boundaries
│   ├── kata-readiness ...... pre-run harness+target doctor; detects sprint progression
│   ├── kata-preflight ...... provision the freeze-approved dep set; manifest-hash + Snyk gated; emits .kata/preflight.json
│   ├── kata-orchestrate .... plan-guardian lead: assign, partition files, gate, no-drift
│   ├── kata-board .......... append-only message board for lateral peer comms
│   ├── kata-worktree ....... per-owner git-worktree isolation for concurrent work
│   └── kata-sprint ......... own the sprint boundary (G1–G4 change-control)   ·incremental only
│
├── execute/      do the work, in a lane
│   ├── kata-tdd ............ red-green-refactor on a vertical slice
│   ├── kata-iac-terraform .. Terraform authoring with the IaC safety gate     ·specialist (never-tiered)
│   ├── kata-iac-cloudformation . CFN/CDK authoring with the IaC safety gate   ·specialist (never-tiered)
│   └── kata-diagnose/ ...... root-cause a failure                              ·tiers: light·full
│
├── evaluate/     prove it, don't trust it
│   ├── kata-evaluate ....... fresh-context, no-write, DEFAULT-FAIL gate (owns "done")
│   ├── kata-review/ ........ adversarial pre-done review                       ·tiers: essential·standard·advanced
│   └── kata-report ......... one-page report of a gated unit (reports the gate, never gates)
│
├── handoff/      survive every boundary
│   ├── kata-handoff ........ durable, two-way, git-committed handoff
│   ├── kata-selfhandoff .... prime-frame self-handoff (compaction survival, no early bail)
│   ├── kata-orient ......... assemble a subagent's launch orientation (the read half of handoff)
│   └── kata-defer .......... park off-plan items + log assumptions — never drift the frozen plan
│
└── meta/         improve the harness itself
    ├── kata-improve ........ fold cross-run lessons into skills/ + emit the LEARN feed
    ├── kata-write-skill .... author new skills to STANDARDS
    └── kata-promote ........ stage-2 HUMAN gate: promote a grounded agent-distilled skill into the toolkit
```

> **Planned (roadmap, not yet built):** `kata-tasklist` · `kata-zoom-out` · `kata-engram`.

<details>
<summary><b>Full machine index</b> — name · version · cost · category · status · source · use (auto-generated from frontmatter; the versioning source of truth)</summary>

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
| `kata-plan-advanced` | 0.1.0 | 4 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-plan-essential` | 0.1.0 | 2 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-plan-standard` | 0.1.0 | 3 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-research` | 0.1.0 | 3 | plan | experimental | new (KataHarness original, loop-cognition RS-GB1/2/3, D62) — fresh-context no-write evaluator pattern (L4/L5) applied to in-loop research; escalation-routed like kata-orchestrate's no-re-plan escape valve (D52) | Research a must-deliver gap with no in-plan solution; ground every claim; return findings for the grounding gate, never re-plan |
| `kata-board` | 0.1.0 | 2 | coordinate | experimental | adapted-from Claude Agent Teams protocol (agnostic file reimplementation); CryptoPortfolioPlanner LESSONS-LEARNED L3 | Append-only mailbox/message board for lateral peer comms |
| `kata-bootstrap` | 0.1.0 | 2 | coordinate | experimental | adapted-from GSD discuss-phase Q&A model + docs/MODES-DESIGN.md D24c composition ladder (KataHarness design) | Compose a run (run-shape + ladder), preview cost, write kata.config, launch |
| `kata-initiate` | 0.1.0 | 3 | coordinate | experimental | new (KataHarness original, Phase 1 Kata Loop — D88/D91); composes kata-readiness, kata-grill, kata-bootstrap, kata-context | — |
| `kata-loop` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original — Phase 3 Kata Loop conductor, D87/DESIGN §1) | — |
| `kata-orchestrate` | 0.1.0 | 5 | coordinate | experimental | adapted-from cpp-orchestrator (CryptoPortfolioPlanner harness) + Anthropic effective-harnesses-for-long-running-agents + managed-agents | Plan-guardian lead: assign, partition files, gate, no-drift |
| `kata-preflight` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original, PRE-FLIGHT spine phase D29/N2); drives tools/kata_preflight.py (N1 engine); argv-builder pattern from the _COMMAND_BUILDERS registry in tools/kata_dispatch.py; injectable-runner from _subprocess_runner in tools/kata_dispatch.py | — |
| `kata-readiness` | 0.1.0 | 1 | coordinate | experimental | new (KataHarness original); pattern echoes environment "doctor" checks (e.g. brew/flutter doctor) — abstract, no external code adapted | Pre-run harness+target readiness check (bootstrap-invoked or standalone doctor) |
| `kata-sprint` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original — sprint-cadence D80; the thin boundary coordinator, GB4-C) | Own the sprint boundary (G1–G4 change-control); incremental delivery only |
| `kata-worktree` | 0.1.0 | 1 | coordinate | experimental | adapted-from CryptoPortfolioPlanner worktree proof (LESSONS-LEARNED L2/L3) | Per-owner git-worktree isolation for concurrent code |
| `kata-deviate` | 0.1.0 | 4 | execute | experimental | new (KataHarness original, Debug Mode P2a — deviation-discovery pipeline, DESIGN LD4–LD5) | — |
| `kata-diagnose-full` | 0.1.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-diagnose-light` | 0.1.0 | 2 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-iac-cloudformation` | 0.1.0 | 3 | execute | experimental | new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4) | — |
| `kata-iac-terraform` | 0.1.0 | 3 | execute | experimental | new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4) | — |
| `kata-tdd` | 0.1.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/tdd | Red-green-refactor on a vertical slice |
| `kata-evaluate` | 0.1.0 | 2 | evaluate | experimental | adapted-from cpp-evaluation (CryptoPortfolioPlanner) + Anthropic fresh-context evaluator pattern | Fresh-context, no-write, default-FAIL PASS/NEEDS_WORK |
| `kata-report` | 0.1.0 | 1 | evaluate | experimental | new (KataHarness original — the D32 report, minimal v1; sprint-cadence D85/D2) | One-page report of a gated unit of work (reports the gate, never gates) |
| `kata-review-advanced` | 0.1.0 | 3 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-review-essential` | 0.1.0 | 1 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-review-standard` | 0.1.0 | 2 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-slop-check` | 0.1.0 | 2 | evaluate | experimental | General heuristics original to KataHarness; adopted-check concepts from ai-slop-detector by flamehaven01 (Flamehaven Labs), https://github.com/flamehaven01/ai-slop-detector, MIT License (Copyright (c) 2026 Flamehaven Labs) — concepts re-implemented as in-context heuristics, no source code copied. | — |
| `kata-closeout` | 0.1.0 | 2 | handoff | experimental | new (KataHarness original — Phase 2 Kata Loop back-half, D89/DESIGN §3) | — |
| `kata-defer` | 0.1.0 | 1 | handoff | experimental | new (KataHarness original, D42/D43 GB9) — the structural complement to the no-drift spine; assumption-log role added by D71 (Priming-and-Grill autonomous floor) | Park off-plan items + log grill-skip assumptions at the boundary, never drift the frozen plan |
| `kata-handoff` | 0.1.0 | 1 | handoff | experimental | adapted-from mattpocock/skills {handoff} + Anthropic reset-with-handoff / compaction guidance | Two-way durable handoff (session/agent/tool) |
| `kata-orient` | 0.1.0 | 2 | handoff | experimental | new (KataHarness original, loop-cognition AO-GB1/2/3 + D76) — receiving half of the two-way handoff (spine #5); three-tier assembly echoes Hermes prompt_builder (stable/context/volatile); nested-AGENTS.md rollup standard | Assemble a subagent's launch orientation: three-tier, task-type-tailored, derived pointers+callouts, routed questions — the read half of handoff |
| `kata-selfhandoff` | 0.1.0 | 1 | handoff | experimental | adapted-from Anthropic compaction guidance + mattpocock caveman compression | Configurable context-threshold self-handoff (delegates artifact to kata-handoff) |
| `kata-understand` | 0.1.0 | 2 | handoff | experimental | new (KataHarness original, Phase 2 GL-R2c / DESIGN §3 / PLAN-phase2 Task C1) — comprehension-map half of the closeout back-half; backed by the F2 graph runtime (tools/graph_gen.py → kata.graph.json) | — |
| `kata-improve` | 0.1.0 | 1 | meta | experimental | adapted-from the Improvement Kata (Toyota Kata) + mattpocock/skills engineering/improve-codebase-architecture | Fold cross-run lessons back into the skills/ tree; calls kata-write-skill |
| `kata-promote` | 0.1.0 | 2 | meta | experimental | new (KataHarness original, loop-cognition ML / LC-GB3/GB4/GB5, D60-D69) — two-stage gate vs Hermes' no-gate instant-universal model (RESEARCH.md bake-off: borrow the closed loop, keep our human gate) | Stage-2 human gate: promote a grounded agent-distilled candidate skill (experimental→stable + scope bump) into the toolkit; honors engram.autonomy |
| `kata-write-skill` | 0.1.0 | 1 | meta | experimental | adapted-from mattpocock/skills productivity/write-a-skill | Author new skills to STANDARDS (points, not restates); kata-improve calls it |
<!-- SKILL-INDEX:END -->

</details>

---

## Repository layout

```
AGENTS.md            canonical agent instructions   ·   CLAUDE.md   pointer to AGENTS.md
docs/                DESIGN · STANDARDS · TAXONOMY · TEST-PLAN · MODES-DESIGN
skills/              plan · coordinate · execute · evaluate · handoff · meta   (cognition: planned)
protocol/            machine schemas: config · state · board · handoff · escalation · graph · engram · orientation
tools/               validate_skills.py — the conformance validator + the README index generator
.planning/           PROJECT · ROADMAP · STATE · DECISIONS · LESSONS-LEARNED · BACKLOG · HANDOFF · specs/
adapters/            per-tool adapters (planned — v0.1 is a Claude-only core)
research/            vendored references (gitignored) + NOTES.md
```

Built on Anthropic's long-running-agent harness guidance and the best of
[mattpocock/skills](https://github.com/mattpocock/skills), GSD, BMAD, and DDD's ubiquitous language —
attributed per skill in the `source` column. We stand on shoulders.

## License

Apache-2.0 — see [LICENSE](./LICENSE).
