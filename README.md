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

Pre-**v0.1** — Claude-only one-shot core, dogfooded by building KataHarness itself, then applied to
CryptoPortfolioPlanner. Roadmap: `.planning/ROADMAP.md`.

## The spine

1. **The plan does not drift** — orchestrator is the plan-guardian; peers execute + talk, never re-plan.
2. **One-shot = no plan churn** — fix against the same plan, don't re-plan by reflex.
3. **Agnostic via adapters** — agnostic core + thin per-tool adapters (Claude/Codex/Kiro/ACP-Quick).
4. **Default-FAIL** — fresh-context, no-write evaluator gates "done."
5. **Two-way, file-based handoff** + configurable self-handoff (anti-context-rot, not over-conservative).
6. **Everything versioned** — per-skill semver in frontmatter; this index is the source of truth.

## Skill index (source of truth — name · version · category · status · source · use)

> All `0.0.0 / planned` until built. `source` records provenance (we stand on shoulders and attribute).

| Skill | Ver | Category | Status | Source | Use |
|---|---|---|---|---|---|
| `kata-grill` | 0.0.0 | plan | planned | mattpocock grill-me + grill-with-docs | Relentless doc-grounded interrogation that resolves every decision branch |
| `kata-context` | 0.0.0 | plan | planned | mattpocock ubiquitous-language | Build/maintain CONTEXT.md shared/ubiquitous language |
| `kata-design-doc` | 0.0.0 | plan | planned | mattpocock to-prd + brainstorming | Synthesize the frozen design doc / spec |
| `kata-plan` | 0.0.0 | plan | planned | mattpocock to-issues + GSD/BMAD | Produce the precise, task-level execution plan |
| `kata-orchestrate` | 0.0.0 | coordinate | planned | Anthropic harness + managed-agents | Plan-guardian lead: assign, partition files, gate, no-drift |
| `kata-board` | 0.0.0 | coordinate | planned | Claude Teams *protocol* (agnostic reimpl) | Append-only mailbox/message board for lateral peer comms |
| `kata-tasklist` | 0.0.0 | coordinate | planned | Claude Teams *protocol* | Shared, file-locked task claim + dependencies |
| `kata-worktree` | 0.0.0 | coordinate | planned | CPP worktree proof | Per-owner git-worktree isolation for concurrent code |
| `kata-tdd` | 0.0.0 | execute | planned | mattpocock tdd | Red-green-refactor on a vertical slice |
| `kata-diagnose` | 0.0.0 | execute | planned | mattpocock diagnose | Systematic debugging loop |
| `kata-evaluate` | 0.0.0 | evaluate | planned | Anthropic evaluator | Fresh-context, no-write, default-FAIL PASS/NEEDS_WORK |
| `kata-review` | 0.0.0 | evaluate | planned | mattpocock review | Adversarial/standards code review |
| `kata-handoff` | 0.0.0 | handoff | planned | mattpocock handoff + Anthropic reset-with-handoff | Two-way durable handoff (session/agent/tool) |
| `kata-selfhandoff` | 0.0.0 | handoff | planned | Anthropic compaction + mattpocock caveman | Configurable context-threshold self-handoff |
| `kata-write-skill` | 0.0.0 | meta | planned | mattpocock write-a-skill | Author new skills to this standard |
| `kata-improve` | 0.0.0 | meta | planned | Improvement Kata + improve-codebase-architecture | Fold lessons back into the harness |
| `kata-zoom-out` | 0.0.0 | meta | planned | mattpocock zoom-out | Higher-level perspective on unfamiliar areas |
| `kata-engram` | 0.0.0 | cognition | backlog | kiban/kagami second-brain tie-in | Inject user cognitive-fingerprint/engram (gated on mature engram) |

## Layout

```
AGENTS.md  CLAUDE.md(pointer)
docs/      DESIGN · ARCHITECTURE · STANDARDS · TAXONOMY
skills/    plan/ coordinate/ execute/ evaluate/ handoff/ meta/ cognition/
adapters/  claude/ codex/ kiro/ acp-quick/
protocol/  board · tasklist · state · handoff (agnostic file schemas)
research/  reference/ (vendored: mattpocock, BMAD; gitignored) · NOTES.md
.planning/ PROJECT · CONTEXT · ROADMAP · STATE · DECISIONS · STEERING · LESSONS-LEARNED · BACKLOG
```

## License

TBD before public release (intended public / open-source).
