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

Endgame: the **orchestrator runs in a desktop app (e.g. Quick, AWS BI desktop with MCP/ACP/skills/tasks)**
driving coding agents via **ACP** or a local coding agent — and a parallel work-specific version exists.

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
| **COORDINATE** | `kata-orchestrate`, `kata-board`, `kata-tasklist`, `kata-worktree` | Plan-guardian assigns + partitions files; peers claim tasks, message laterally, isolate in worktrees |
| **EXECUTE** | `kata-tdd`, `kata-diagnose` | Build the slice; debug systematically; never re-plan (escalate) |
| **EVALUATE** | `kata-evaluate`, `kata-review` | Fresh-context, no-write, default-FAIL gate; NEEDS_WORK seeds a targeted fix |
| **HANDOFF** | `kata-handoff`, `kata-selfhandoff` | Two-way durable handoff; self-handoff at a configurable context threshold |
| **IMPROVE** | `kata-improve`, `kata-zoom-out`, `kata-write-skill` | Fold lessons back; the harness improves itself |

> **v0.1 built:** kata-grill, kata-context, kata-design-doc, kata-plan, kata-orchestrate, kata-board,
> kata-worktree, kata-tdd, kata-evaluate, kata-handoff (+ kata-review, the adversarial EVALUATE leg).
> **Not yet built (backlog):** kata-tasklist, kata-diagnose, kata-selfhandoff, kata-improve, kata-zoom-out,
> kata-write-skill, kata-engram — the rows above that name these describe the intended loop, not shipped v0.1.
> The IMPROVE phase in particular is not yet automated (improvement today = a human folding LESSONS-LEARNED back).

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

## Standards

Per-skill semver in frontmatter; README index is the source of truth; `kata-<verb>` naming; AGENTS.md
canonical + CLAUDE.md pointer; Obsidian-native durable artifacts. Full schema in `docs/STANDARDS.md`.

## Cognitive tie-in (extension point, backlog)

`cognition/kata-engram`: inject the user's cognitive-fingerprint/engram from a mature second brain
(`[[project-framework]]` kiban, `[[project-kagami]]`) to personalize planning/execution — **gated on a
well-developed engram**; not v0.1.

## Milestones

See `.planning/ROADMAP.md`. v0.1 = Claude-only one-shot core, **dogfooded by building KataHarness
itself**, then proven on CryptoPortfolioPlanner; adapters and concurrency follow.

## References

`research/reference/mattpocock-skills`, `research/reference/bmad-method`, local GSD at
`~/.claude/get-shit-done`; Anthropic engineering: effective-harnesses-for-long-running-agents,
harness-design-long-running-apps, managed-agents; agentskills.io; Claude Code agent-teams/sub-agents/skills.
