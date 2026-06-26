# KataHarness

**A controllable agent harness that spans the whole spectrum — from spec-driven, interview-shaped sprint
coding to fully automated, self-learning one-shots — all on one vetted, grounded process.**

Most agent tools force a bad choice: babysit every step, or let it loose and watch it spiral. KataHarness
gives you a **dial** instead. Tighten it for **spec-influenced, sprint-by-sprint control**, where an interview
(the "grill") shapes the work to *your* codebase and *your* style and you approve at every boundary. Loosen it
for **hands-off one-shots** that resolve their own ambiguity and learn from every run. In between sits a set of
**well-defined modes** — pick the rigor, the cadence, and how much the harness asks you. Whatever you pick, the
same backbone holds: the **plan doesn't drift**, a fresh-context evaluator that **assumes failure** gates
"done," everything is **grounded and versioned**, and the durable artifacts land in **your own project vault** —
not a black box. The name is the method — the **Improvement Kata**: each loop sharpens the loop.

> New here? Read [`AGENTS.md`](./AGENTS.md) (canonical) → [`docs/DESIGN.md`](./docs/DESIGN.md) (the charter) →
> [`docs/STANDARDS.md`](./docs/STANDARDS.md) (conventions).
>
> **Setting up / don't have a vault?** See **[`docs/SETUP.md`](./docs/SETUP.md)** — one central install, a
> small settings file (default project folder + optional vault), and a per-platform installer (Claude built;
> Codex/Kiro best-effort). No vault needed to start: the harness runs fine pointed at a plain project folder.

[PokeVault]: # "PokeVault — the reference vault/toolkit home (install link to be added)"

---

## What makes KataHarness different

**The throughline is _control_.** Everything below is a way of keeping you in charge while the agents do the work.

- 🎛️ **You set the level of control — per run.** Run it fully human-in-the-loop (spec → grill → approve each
  sprint), fully automated (a hands-off learning one-shot), or anywhere between. Nothing happens off-plan
  without surfacing it to you first.
- 🪜 **Well-defined modes, not vibes.** A consistent system of **effort/rigor tiers** (essential · standard ·
  advanced), **run-shapes** (individual · batch · version-up), and a **delivery axis** (one-shot · incremental
  sprints). Same format across every mode — you compose the run, preview its cost, then launch.
- 🗣️ **An interview that codes like you do.** The **grill** interrogates your idea, learns your codebase's
  conventions and your style, and enriches *your* intent into a frozen spec — with the depth dialed by you
  (`skip → light → standard → full`). Whatever ambiguity you don't resolve up front gets resolved **in-loop by
  a no-write research subagent**, or parked in an assumption log surfaced at the gate — never silently guessed.
- 👥 **Built for every kind of builder.** Spec-driven sprint coder, version-up maintainer, or
  one-shot-it-and-walk-away — same harness, different dials. It meets you where you work.
- ✅ **Backed by sound, vetted process.** Grounding gates, **default-FAIL** evaluation, fresh-context
  adversarial review, and industry-standard practice (TDD, DDD ubiquitous language, vertical-slice planning,
  disjoint file-ownership). "Done" is *earned*, never self-declared — no skill certifies its own work.
- 🧠 **It learns.** Every run mines its own decisions, reviews, and grill ledgers into a **second-brain LEARN
  feed**; agents can distil reusable skills that pass a grounding check **and a human promotion gate** before
  going universal. The harness you run next month is sharper than today's.
- 🗂️ **Lives in your own vault / project.** Durable artifacts are **Obsidian-native** (frontmatter +
  wikilinks + tags) and **git-committed** in *your* workspace — plans, decisions, handoffs, and the learn feed
  are yours to read, not locked in a tool.
- 💾 **Survives every boundary.** Two-way, file-based handoff means work outlives compaction, a dead session,
  or a switch between agents/tools — a fresh agent re-enters mid-stream without re-deriving anything.
- 🔌 **Tool-agnostic.** An agnostic core + thin per-tool adapters (Claude today; Codex/Kiro/ACP next). Your
  discipline travels with you, not with one vendor.

**In short — what people actually want:** an agent you can *trust* and *steer*, that *finishes*, doesn't
spiral, doesn't lose your context, fits *how you build*, and *gets better over time* — on whatever tool you use.

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

**`v0.1.0-alpha.1` (first tagged milestone) — skill suite complete & green, not yet field-proven end-to-end.**
35 skills, all `0.1.0`/experimental; validator 0 errors · tests passing · Snyk clean. Two self-dogfood runs
done — the second was a real **orchestrated** version-up (concurrent worker subagents in isolated worktrees,
fresh-context gate, human version-select). The full cognitive architecture is built for the **Claude-only
core**, now spanning **one-shot and incremental (sprint) delivery**, plus the learning loop (LEARN feed +
managed skill promotion). What remains before v0.1 *ships*: the **dogfood** (run the harness against a real
target — its own next version) to turn "built" into "proven"; a small **install & portability layer** (a
one-time init flow + workspace binding so it drops cleanly into *any* vault or project dir, not just the
reference one); then the multi-tool **adapters** (Codex, Kiro, ACP). Live state:
[`.planning/STATE.md`](./.planning/STATE.md) · roadmap: [`.planning/ROADMAP.md`](./.planning/ROADMAP.md).

## The spine (six non-negotiables)

1. **The plan does not drift** — the orchestrator guards it; peers execute + talk, never re-plan.
2. **One-shot = no plan churn** — fix against the same plan; don't re-plan by reflex.
3. **Agnostic via adapters** — agnostic core + thin per-tool adapters.
4. **Default-FAIL** — a fresh-context, no-write evaluator gates "done."
5. **Two-way, file-based handoff** — plus prime-frame self-handoff (survives context rot without bailing early).
6. **Everything versioned** — per-skill semver is the machine source of truth; the catalog is generated.

---

## The skills

35 skills across the six loop phases (plus the Greater-Loop initiation/closeout modules). Tiered families (`kata-grill`, `kata-plan`, `kata-review`,
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
│   ├── kata-orchestrate .... plan-guardian lead: assign, partition files, gate, no-drift
│   ├── kata-board .......... append-only message board for lateral peer comms
│   ├── kata-worktree ....... per-owner git-worktree isolation for concurrent work
│   └── kata-sprint ......... own the sprint boundary (G1–G4 change-control)   ·incremental only
│
├── execute/      do the work, in a lane
│   ├── kata-tdd ............ red-green-refactor on a vertical slice
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
| `kata-readiness` | 0.1.0 | 1 | coordinate | experimental | new (KataHarness original); pattern echoes environment "doctor" checks (e.g. brew/flutter doctor) — abstract, no external code adapted | Pre-run harness+target readiness check (bootstrap-invoked or standalone doctor) |
| `kata-sprint` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original — sprint-cadence D80; the thin boundary coordinator, GB4-C) | Own the sprint boundary (G1–G4 change-control); incremental delivery only |
| `kata-worktree` | 0.1.0 | 1 | coordinate | experimental | adapted-from CryptoPortfolioPlanner worktree proof (LESSONS-LEARNED L2/L3) | Per-owner git-worktree isolation for concurrent code |
| `kata-diagnose-full` | 0.1.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-diagnose-light` | 0.1.0 | 2 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | — |
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
