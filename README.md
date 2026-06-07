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

**v0.1 skill-complete (experimental).** All 10 v0.1 skills built + `kata-review` (adversarial leg). The
**execution half** (`kata-orchestrate/worktree/board/tdd/evaluate`) is field-proven — it built CPP Phase 3
green via subagents in isolated worktrees (A/B vs GSD: tied on objective metrics — see
`.planning/LESSONS-LEARNED.md` L9/L10). The **planning half** (`kata-grill/context/design-doc/plan`) is built
but not yet field-tested; that is the next validation (an A/B that varies the planning step). Claude-only
core; adapters + the remaining skills are post-v0.1. Roadmap: `.planning/ROADMAP.md`.

## The spine

1. **The plan does not drift** — orchestrator is the plan-guardian; peers execute + talk, never re-plan.
2. **One-shot = no plan churn** — fix against the same plan, don't re-plan by reflex.
3. **Agnostic via adapters** — agnostic core + thin per-tool adapters (Claude/Codex/Kiro/ACP-Quick).
4. **Default-FAIL** — fresh-context, no-write evaluator gates "done."
5. **Two-way, file-based handoff** + configurable self-handoff (anti-context-rot, not over-conservative).
6. **Everything versioned** — per-skill semver in frontmatter; this index is the source of truth.

> **v0.1 status:** spine #1, #2, #4, #6 are implemented in the built skills; #3 (agnostic *adapters*) and #5
> (*self-handoff* automation) are designed but not yet built. See Status and `.planning/REVIEW-v0.1.md`.

## Skill index (source of truth — name · version · category · status · source · use)

> All `0.0.0 / planned` until built. `source` records provenance (we stand on shoulders and attribute).

| Skill | Ver | Category | Status | Source | Use |
|---|---|---|---|---|---|
| `kata-grill` | 0.1.0 | plan | experimental | mattpocock grill-me + grill-with-docs | Relentless doc-grounded interrogation that resolves every decision branch |
| `kata-context` | 0.1.0 | plan | experimental | mattpocock ubiquitous-language | Build/maintain CONTEXT.md shared/ubiquitous language |
| `kata-design-doc` | 0.1.0 | plan | experimental | mattpocock to-prd + brainstorming | Synthesize the frozen design doc / spec |
| `kata-plan` | 0.1.0 | plan | experimental | mattpocock to-issues (vertical) + GSD plan-phase + BMAD trade-offs | Produce the precise, task-level execution plan (vertical slices → disjoint file-ownership + wave DAG) |
| `kata-orchestrate` | 0.1.0 | coordinate | experimental | Anthropic harness + managed-agents | Plan-guardian lead: assign, partition files, gate, no-drift |
| `kata-board` | 0.1.0 | coordinate | experimental | Claude Teams *protocol* (agnostic reimpl) | Append-only mailbox/message board for lateral peer comms |
| `kata-tasklist` | 0.0.0 | coordinate | planned | Claude Teams *protocol* | Shared, file-locked task claim + dependencies |
| `kata-worktree` | 0.1.0 | coordinate | experimental | CPP worktree proof | Per-owner git-worktree isolation for concurrent code |
| `kata-tdd` | 0.1.0 | execute | experimental | mattpocock tdd | Red-green-refactor on a vertical slice |
| `kata-diagnose` | 0.1.0 | execute | experimental | mattpocock diagnose | Diagnosis loop for unexpected failures (feedback-loop-first); boundary vs kata-tdd |
| `kata-evaluate` | 0.1.0 | evaluate | experimental | Anthropic evaluator | Fresh-context, no-write, default-FAIL PASS/NEEDS_WORK |
| `kata-review` | 0.1.0 | evaluate | experimental | CPP cpp-adversarial-validation (+ review Standards axis → kata-evaluate) | Fresh-context adversarial red-team of design + impl; SHIP/HOLD |
| `kata-handoff` | 0.1.0 | handoff | experimental | mattpocock handoff + Anthropic reset-with-handoff | Two-way durable handoff (session/agent/tool) |
| `kata-selfhandoff` | 0.1.0 | handoff | experimental | Anthropic compaction + mattpocock caveman | Configurable context-threshold self-handoff (delegates artifact to kata-handoff) |
| `kata-write-skill` | 0.1.0 | meta | experimental | mattpocock write-a-skill | Author new skills to STANDARDS (points, not restates); kata-improve calls it |
| `kata-improve` | 0.1.0 | meta | experimental | Improvement Kata + improve-codebase-architecture | Fold cross-run lessons back into the skills/ tree; calls kata-write-skill |
| `kata-zoom-out` | 0.0.0 | meta | planned | mattpocock zoom-out | Higher-level perspective on unfamiliar areas |
| `kata-engram` | 0.0.0 | cognition | backlog | kiban/kagami second-brain tie-in | Inject user cognitive-fingerprint/engram (gated on mature engram) |

## Layout

```
AGENTS.md  CLAUDE.md(pointer)
docs/      DESIGN · STANDARDS · TEST-PLAN            (ARCHITECTURE · TAXONOMY: planned)
skills/    plan/ coordinate/ execute/ evaluate/ handoff/   (meta/ cognition/: planned)
protocol/  board · state · handoff                  (tasklist: planned)
research/  reference/ (vendored: mattpocock, BMAD; gitignored) · NOTES.md
.planning/ PROJECT · ROADMAP · STATE · DECISIONS · LESSONS-LEARNED · REVIEW-v0.1 · BACKLOG · STEERING
adapters/  (planned — v0.1 is a Claude-only core)
```

## License

TBD before public release (intended public / open-source).
