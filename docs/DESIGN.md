# DESIGN.md — KataHarness charter

**Status:** draft v0 (foundation). Supersedes the project-local `cpp-*` harness in CryptoPortfolioPlanner,
which was the medium it was incubated in. Read with `AGENTS.md` (canonical) and `docs/STANDARDS.md`.

## Vision

A **tool-agnostic, iteratively-improved agent harness that one-shots complex tasks** described in a
design doc + plan. It maximizes one-shot success by front-loading deep, doc-grounded planning, freezing
that plan, then executing it faithfully across one or many agents — gated by a default-FAIL evaluator
and stitched by two-way, file-based handoff. It is an **iteration on Anthropic's long-running-agent
harness**, with industry best practices baked in (mattpocock/skills, GSD, BMAD, DDD ubiquitous
language). The name is the method: the **Improvement Kata** — every run improves the harness.

Endgame: the **orchestrator runs in a desktop app (an ACP host — e.g. Amazon Quick — with MCP/skills/tasks)**
driving coding agents via **ACP** or a local coding agent — and a parallel work-specific version exists (kept
separate until import). **Quick is the integration seam** for that ACP host; the work backend binds behind it.

## The spine (see AGENTS.md §spine)

Plan-doesn't-drift · one-shot=no-churn · agnostic-via-adapters · default-FAIL · two-way handoff ·
everything versioned. These are the load-bearing invariants; features serve them.

## Architecture

```
                         ┌──────────────── agnostic CORE ────────────────┐
  design doc + plan ──▶  │  plan/  coordinate/  execute/  evaluate/        │
   (frozen)              │  handoff/  meta/  cognition/    + protocol/     │
                         │  (skills, all agnostic: true)   (file schemas)  │
                         └───────────────────────┬────────────────────────┘
                                                 │ normalized by
                         ┌───────────────────────▼────────────────────────┐
                         │  ADAPTERS:  claude | codex | kiro | acp-quick    │
                         │  map skill-format + AGENTS.md/CLAUDE.md + native │
                         │  features (Claude: Teams/hooks/subagents)        │
                         └──────────────────────────────────────────────────┘
```

- **Core** = portable skills + a file-based **protocol** (`board`, `tasklist`, `state`, `handoff`
  schemas) + the planning engine + the quality loop. No tool-specific dependencies.
- **Adapters** = thin per-tool layers. They translate the canonical instruction file (`AGENTS.md`) to
  the tool's file, map the skill-definition format, and *may* opt into native features (the Claude
  adapter may use Agent Teams; the core never requires them).

## The loop → skills

| Phase | Skills | What happens |
|---|---|---|
| **GRILL** | `kata-grill`, `kata-context` | Doc-grounded interrogation; resolve every branch; build ubiquitous language |
| **FREEZE** | `kata-design-doc`, `kata-plan` | Produce the design doc + a precise, task-level plan; **freeze it** |
| **COORDINATE** | `kata-orchestrate`, `kata-board`, `kata-tasklist`, `kata-worktree`, `kata-bootstrap`, `kata-readiness` | Plan-guardian assigns + partitions files; peers claim tasks, message laterally, isolate in worktrees |
| **EXECUTE** | `kata-tdd`, `kata-diagnose` | Build the slice; debug systematically; never re-plan (escalate) |
| **EVALUATE** | `kata-evaluate`, `kata-review` | Fresh-context, no-write, default-FAIL gate; NEEDS_WORK seeds a targeted fix |
| **HANDOFF** | `kata-handoff`, `kata-selfhandoff` | Two-way durable handoff; self-handoff at a configurable context threshold |
| **IMPROVE** | `kata-improve`, `kata-zoom-out`, `kata-write-skill` | Fold lessons back; the harness improves itself |

> **Built (15, all `0.1.0`):** kata-grill, kata-context, kata-design-doc, kata-plan, kata-orchestrate,
> kata-board, kata-worktree, kata-tdd, kata-diagnose, kata-evaluate, kata-review, kata-handoff,
> kata-selfhandoff, kata-improve, kata-write-skill — the full loop GRILL→…→IMPROVE is wired.
> **Not yet built:** kata-tasklist (deferred — needs worker self-selection; redundant with state.json + the
> plan DAG today), kata-zoom-out (deferred — too thin), kata-engram (backlog, D9, gated on a mature engram).

## Priming-and-Grill — the GRILL phase is optional (D71/D72)

Every run starts from a **priming prompt** (the human's original spec). The **grill is an optional human
certainty layer over that prompt**, not a benchmarked gate (L11): it interrogates the designer to resolve
ambiguity and enrich the prompt into the frozen spec, adding alignment certainty **by construction**. It is a
dial — **`skip | light | standard | full`** (→ `tiers["kata-grill"] = skip|essential|standard|advanced`;
`kata-readiness` recommends a position from prompt richness, `kata-bootstrap` offers it, the human chooses).

- **The autonomous-reliability floor is always on** (default-FAIL + the **RS research subagent** [in-loop
  ambiguity resolution, loop-cognition phase] + a **`kata-defer` assumption/ambiguity log graded at the gate and
  surfaced at handoff**). Autonomous reliability is the demonstrated floor (D70); the grill *adds* up-front
  certainty **on top** of it (D71: "both coexist; grill shores up results on top of a reliable autonomous
  floor"). **`skip`** leans entirely on the floor (no up-front grill); **light → standard → full** add
  increasing up-front interrogation, so the floor makes progressively fewer autonomous assumptions.
- **Grill ↔ RS are one ambiguity-resolution spectrum:** up-front-with-human (grill) ⟷ in-loop-without-human
  (RS). Skipping the grill **shifts** resolution along the spectrum; it never removes it, and **never** skips the
  `kata-evaluate` default-FAIL gate (D22/D33).
- **Grill output trains the engram (D72):** each grill's decision ledger is a primary cognitive-fingerprint
  feed; a matured fingerprint pre-answers future grills, so human grill-effort decreases over time.

## Planning engine (the one-shot enabler)

A **portable** synthesis (not a dependency on any one tool's planner): mattpocock's **grill-with-docs +
grill-me** interrogation + ubiquitous-language CONTEXT.md; **GSD's** spec→roadmap→plan depth; **BMAD's**
role-agents (analyst/architect/PM/dev/QA). Output: a frozen `DESIGN` + a task-level `PLAN` with
file-ownership and acceptance criteria. The evaluation in `research/NOTES.md` records exactly which
patterns we adopt from each (the most important bake-in work).

## Concurrency & coordination

Mine the **Claude Agent Teams *protocol*** — mailbox, file-locked task-claim, shared task list, lead —
and **reimplement it agnostically as files** (`protocol/`): an **append-only board** (no last-writer
clobber), a file-locked **task list**, a single-writer **state** owned by the plan-guardian, and
**git-worktree isolation** per file-owner. The orchestrator (lead) is the plan-guardian, not a passive
observer; peers communicate directly but never author the plan.

## Context management

`kata-selfhandoff`: at a **configurable, non-over-conservative** threshold, write a handoff → compact →
resume from it, **re-anchoring on the frozen plan**. Prefer **task-boundary** handoff over arbitrary-%
to avoid lossy mid-task compression. Uses caveman-style compression. Tuned explicitly *not* to wrap up
sessions early (the failure mode the user flagged).

## User-facing UX (WS-3 — built 2026-06-24, D95)

The human-facing surfaces are designed to be **friendly to a non-expert owner by default**, carried by one agnostic
voice — a **nameless calm kata-craftsperson who translates** (`protocol/persona.md`). Intake is a **reflective goal
mirror** (infer-then-confirm, refining the anti-drift STOP gate); the decision tree collapses to **one "how careful"
dial** (machinery inferred, hidden behind an advanced drawer); in-loop **milestone narration** speaks in human terms
(never stage names; `protocol/narration.md`) with a **never-tiered breakthrough alert** for anything needing the human;
and the **closeout is goal-anchored** — it leads with plain-language what-changed-and-why and **offers a clean backout**
(WS-4) at the human gate. Register adaptation toward the user's sophistication is a **gated engram seam, not live**
(D9/D56). Full contract: `.planning/specs/ws3-user-friendliness/DESIGN.md` (L1–L11).

The closeout is **two-tier** (WS-3R, D96): a concise CLI/GUI summary that links to a durable, self-contained,
on-brand **HTML report** (`.kata/closeout.html`) with a Markdown source (`.kata/CLOSEOUT.md`), rendered by filling
a committed template in-context. Carries the first **KataHarness logo** (`modules/closeout/resources/`). Per-host
native rendering of that report (hooks/statusline) is deferred adapter work (M8). WS-3 was field-exercised (n=1)
by building this through the friendly loop.

## Standards

Per-skill semver in frontmatter; README index is the source of truth; `kata-<verb>` naming; AGENTS.md
canonical + CLAUDE.md pointer; Obsidian-native durable artifacts. Full schema in `docs/STANDARDS.md`.

## Cognitive tie-in (extension point, backlog)

`cognition/kata-engram`: inject the user's cognitive-fingerprint/engram from a mature second brain
(`[[project-framework]]` kiban, `[[project-kagami]]`) to personalize planning/execution — **gated on a
well-developed engram**; not v0.1.

## Milestones

See `.planning/ROADMAP.md`. v0.1 = Claude-only one-shot core, **dogfooded by building KataHarness
itself**. The D16 planning-varied A/B was **retired as an RCT (D70, L11)** — it tested the wrong axis; what it
proved (autonomous reliability) is the floor, and v0.1 is re-scoped to the **Priming-and-Grill architecture
(D71/D72)** above. Installs into the PokeVault vault (D58); adapters and concurrency follow.

## References

`research/reference/mattpocock-skills`, `research/reference/bmad-method`, local GSD at
`~/.claude/get-shit-done`; Anthropic engineering: effective-harnesses-for-long-running-agents,
harness-design-long-running-apps, managed-agents; agentskills.io; Claude Code agent-teams/sub-agents/skills.
