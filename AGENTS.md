# AGENTS.md — KataHarness

> **This is the canonical agent-instructions file.** It follows the cross-tool `AGENTS.md`
> industry convention so KataHarness works in Codex, Kiro, Quick (ACP), and any AGENTS.md-aware
> agent. `CLAUDE.md` is a thin pointer to this file — Claude Code is the *exception* to the
> standard, not the standard. Keep canonical guidance here; keep only Claude-specific notes in CLAUDE.md.

## What KataHarness is

A **tool-agnostic, iteratively-improved agent harness that one-shots complex tasks.** The loop:

```
GRILL (deep planning) → FREEZE (design doc + precise plan) → EXECUTE (distributed, plan-faithful)
  → EVALUATE (default-FAIL) → HANDOFF (two-way) → IMPROVE (kata)
```

The name is the method: **Kata = the Improvement Kata** — continuous, deliberate process improvement.
Every loop run is a kata; the harness improves *itself* via kata. We stand on Anthropic's
long-running-agent harness + the best of mattpocock/skills, GSD, BMAD, and DDD ubiquitous language.

## The Kata Loop

The **full loop** wraps the harness with a front half and back half, sequenced by the thin `kata-loop`
conductor. It is **optional** — absent the conductor, the direct one-shot harness run is unchanged (BC).

```
INITIATION          THE HARNESS              CLOSEOUT
kata-initiate  ──▶  kata-orchestrate    ──▶  kata-closeout ──┐
(intent→           (grill→freeze→exec→       (report+          │
frozen INTENT.md)   evaluate→handoff)         understand+      │
                                              human decision)  │
                                                               │
◀──────── loop-back (version-up: carry context) ◀─────────────┘
          build-new: fresh initiation (cold)
```

`kata-loop` composes three self-contained modules (each a `modules/<name>/` dir with its own `AGENTS.md`,
D91): **initiation** (`kata-initiate`), the **reused harness** (`kata-orchestrate` + the built loop),
and **closeout** (`kata-closeout` + `kata-understand`). On a "run again (version-up)" decision, the
loop-back re-enters `kata-initiate` carrying the prior run's context — new baseline SHA, understand-map,
lessons, and prior `INTENT.md` — so the next cycle starts informed. A platform may swap any module.

## Commands & run-shapes (Claude adapter)

`/kata` prints the index. `/kata-start` → `kata-initiate` (the front door); `/kata-onboard` onboards an
existing repo (and is the on-ramp for **Debug Mode**); `/kata-resume`, `/kata-status`, `/kata-validate`.

A run's **run-shape** is chosen at bootstrap (it pre-fills `mode`+`modules`+`target`): `individual` · `batch`
(best-of-N) · `version-up` (improve a repo that already ran the loop) · **`debug`** (systematically debug an
existing repo in confidence) · `advanced`. A **debug run** is filed as `kind: version-up` + `target.kind:
existing`; bootstrap sets `runShape: debug` + module `kata/module/debug`. To start one, ask for it at
`/kata-start` ("debug my repo") or use `/kata-onboard`.

## The spine (non-negotiable principles)

1. **The plan does not drift.** The orchestrator is the **plan-guardian**: it owns the frozen
   design doc + plan, task assignment, file-ownership partitioning, and gating. Worker/peer agents
   **execute against the frozen plan and communicate laterally — they never re-plan.** Discovered
   unknowns **escalate** to the orchestrator for a *deliberate* re-plan. Any drift signal → fall
   back to orchestrator-mediated execution.
2. **One-shot = no plan churn.** Deep plan up front → execute → eval → *targeted fix against the
   same plan*. Re-planning is an event, not a habit.
3. **Agnostic via adapters.** An agnostic **core** (protocol + file conventions + skills + planning
   engine + quality loop) plus thin **per-tool adapters** (`adapters/claude`, `codex`, `kiro`,
   `acp-quick`). Adapters normalize the two real cross-tool differences: **skill-definition format**
   and the **AGENTS.md vs CLAUDE.md** instruction-file standard.
4. **Default-FAIL quality loop.** Nothing is "done" until evidence is *read* and passes:
   tests/lint/security green **+** a **fresh-context, no-write evaluator** returns PASS. (Anthropic.)
5. **Two-way, file-based handoff.** Handoffs flow both directions — session↔session, agent↔agent,
   tool↔tool — as durable, git-committed, Obsidian-readable artifacts. Plus **self-handoff** at a
   *configurable, non-over-conservative* context threshold (task-boundary preferred; re-anchor on
   the plan).
6. **Everything is versioned.** Every skill carries a semver in its frontmatter; the README skill
   index is the source of truth for what exists and at what version. See `docs/STANDARDS.md`.

## How to work in this repo

- **Read first:** this file, then `docs/DESIGN.md` (charter), `docs/STANDARDS.md` (frontmatter +
  versioning + naming), `.planning/STATE.md` + `.planning/HANDOFF.md`.
- **Plan before building.** Use the `plan/` skills (grill → context → design-doc → plan). Freeze the
  plan before execution.
- **Build in isolation.** Concurrent code work uses git worktrees (one owner per file set).
- **Commit at every checkpoint.** Conventional commits (`feat:`/`fix:`/`docs:`/`chore:`). End commit
  messages with the project co-author trailer.
- **Improve via kata.** Every milestone: capture surprises/decisions in `.planning/LESSONS-LEARNED.md`
  and `.planning/DECISIONS.md`; fold improvements back into the skills (`meta/kata-improve`).

## Conventions

- Line endings pinned to **LF** (`.gitattributes`) — build/handoff sizes must be deterministic.
- Durable artifacts use **YAML frontmatter + `[[wikilinks]]` + `#tags`** (Obsidian-native).
- Machine coordination state (board, task list) is separate from human/durable docs.
- Provenance is required: when a skill adapts external work, record `source:` in its frontmatter.

## Status

Pre-v0.1. See `.planning/ROADMAP.md`. v0.1 = Claude-only one-shot core, dogfooded by building
KataHarness itself, then validated via the D16 planning-varied A/B on small one-shottable test
projects (D57); installs into the PokeVault vault (D58).
