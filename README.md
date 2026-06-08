# KataHarness

**A tool-agnostic, iteratively-improved agent harness that one-shots complex tasks.**

Deep grill-based planning → a *frozen* design doc + precise plan → distributed, plan-faithful
execution → default-FAIL evaluation → two-way handoff → kata-driven improvement. Built on Anthropic's
long-running-agent harness and the best of [mattpocock/skills](https://github.com/mattpocock/skills),
GSD, BMAD, and DDD ubiquitous language. The name is the method — the **Improvement Kata**: every loop
run improves the harness.

> **Read [`AGENTS.md`](./AGENTS.md)** (canonical) and [`docs/DESIGN.md`](./docs/DESIGN.md) (charter).
> Conventions live in [`docs/STANDARDS.md`](./docs/STANDARDS.md).

## Status

**v0.1 skill-complete (experimental).** All 15 skills built (the v0.1 ten + `kata-review` + the
v0.2-pulled-forward four: `kata-diagnose`, `kata-selfhandoff`, `kata-improve`, `kata-write-skill`). The
**execution half** (`kata-orchestrate/worktree/board/tdd/evaluate`) is field-proven — it built CPP Phase 3
green via subagents in isolated worktrees (A/B vs GSD: tied on objective metrics — see
`.planning/LESSONS-LEARNED.md` L9/L10). The **planning half** (`kata-grill/context/design-doc/plan`) is built
but not yet field-tested; that is the next validation (an A/B that varies the planning step). Claude-only
core; adapters + the 3 remaining skills (`kata-tasklist`, `kata-zoom-out`, `kata-engram`) are post-v0.1.
Roadmap: `.planning/ROADMAP.md`.

## The spine

1. **The plan does not drift** — orchestrator is the plan-guardian; peers execute + talk, never re-plan.
2. **One-shot = no plan churn** — fix against the same plan, don't re-plan by reflex.
3. **Agnostic via adapters** — agnostic core + thin per-tool adapters (Claude/Codex/Kiro/ACP-Quick).
4. **Default-FAIL** — fresh-context, no-write evaluator gates "done."
5. **Two-way, file-based handoff** + configurable self-handoff (anti-context-rot, not over-conservative).
6. **Everything versioned** — per-skill semver in frontmatter; this index is the source of truth.

> **v0.1 status:** spine #1, #2, #4, #5, #6 are implemented in the built skills; only #3 (agnostic *adapters*)
> remains — v0.1 is a Claude-only core. See Status and `.planning/REVIEW-v0.1.md`.

## Skill index (source of truth — name · version · category · status · source · use)

> `source` records provenance (we stand on shoulders and attribute).

<!-- SKILL-INDEX:START -->
| Skill | Ver | Cost | Category | Status | Source | Use |
|---|---|---|---|---|---|---|
| `kata-context` | 0.1.0 | 1 | plan | experimental | adapted-from mattpocock/skills {ubiquitous-language, grill-with-docs CONTEXT-FORMAT} | Build/maintain CONTEXT.md shared/ubiquitous language |
| `kata-design-doc` | 0.1.0 | 2 | plan | experimental | adapted-from mattpocock/skills {to-prd} + superpowers brainstorming + GSD spec-phase | Synthesize the frozen design doc / spec |
| `kata-grill` | 0.1.0 | 4 | plan | experimental | adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model | Relentless doc-grounded interrogation that resolves every decision branch |
| `kata-plan` | 0.1.0 | 3 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | Produce the precise, task-level execution plan (vertical slices → disjoint file-ownership + wave DAG) |
| `kata-board` | 0.1.0 | 2 | coordinate | experimental | adapted-from Claude Agent Teams protocol (agnostic file reimplementation); CryptoPortfolioPlanner LESSONS-LEARNED L3 | Append-only mailbox/message board for lateral peer comms |
| `kata-orchestrate` | 0.1.0 | 5 | coordinate | experimental | adapted-from cpp-orchestrator (CryptoPortfolioPlanner harness) + Anthropic effective-harnesses-for-long-running-agents + managed-agents | Plan-guardian lead: assign, partition files, gate, no-drift |
| `kata-worktree` | 0.1.0 | 1 | coordinate | experimental | adapted-from CryptoPortfolioPlanner worktree proof (LESSONS-LEARNED L2/L3) | Per-owner git-worktree isolation for concurrent code |
| `kata-diagnose` | 0.1.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | Diagnosis loop for unexpected failures (feedback-loop-first); boundary vs kata-tdd |
| `kata-tdd` | 0.1.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/tdd | Red-green-refactor on a vertical slice |
| `kata-evaluate` | 0.1.0 | 2 | evaluate | experimental | adapted-from cpp-evaluation (CryptoPortfolioPlanner) + Anthropic fresh-context evaluator pattern | Fresh-context, no-write, default-FAIL PASS/NEEDS_WORK |
| `kata-review` | 0.1.0 | 2 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | Fresh-context adversarial red-team of design + impl; SHIP/HOLD |
| `kata-handoff` | 0.1.0 | 1 | handoff | experimental | adapted-from mattpocock/skills {handoff} + Anthropic reset-with-handoff / compaction guidance | Two-way durable handoff (session/agent/tool) |
| `kata-selfhandoff` | 0.1.0 | 1 | handoff | experimental | adapted-from Anthropic compaction guidance + mattpocock caveman compression | Configurable context-threshold self-handoff (delegates artifact to kata-handoff) |
| `kata-improve` | 0.1.0 | 1 | meta | experimental | adapted-from the Improvement Kata (Toyota Kata) + mattpocock/skills engineering/improve-codebase-architecture | Fold cross-run lessons back into the skills/ tree; calls kata-write-skill |
| `kata-write-skill` | 0.1.0 | 1 | meta | experimental | adapted-from mattpocock/skills productivity/write-a-skill | Author new skills to STANDARDS (points, not restates); kata-improve calls it |
<!-- SKILL-INDEX:END -->

> **Planned (roadmap, not yet built):** `kata-tasklist` · `kata-zoom-out` · `kata-engram` — see `.planning/ROADMAP.md`.

## Layout

```
AGENTS.md  CLAUDE.md(pointer)
docs/      DESIGN · STANDARDS · TEST-PLAN            (ARCHITECTURE · TAXONOMY: planned)
skills/    plan/ coordinate/ execute/ evaluate/ handoff/ meta/   (cognition/: planned)
protocol/  board · state · handoff                  (tasklist: planned)
research/  reference/ (vendored: mattpocock, BMAD; gitignored) · NOTES.md
.planning/ PROJECT · ROADMAP · STATE · DECISIONS · LESSONS-LEARNED · REVIEW-v0.1 · BACKLOG · STEERING
adapters/  (planned — v0.1 is a Claude-only core)
```

## License

Apache-2.0 — see [LICENSE](./LICENSE).
