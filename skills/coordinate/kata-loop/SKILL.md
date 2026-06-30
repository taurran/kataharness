---
name: kata-loop
description: >-
  The thin top-level conductor that sequences the Kata Loop end-to-end — INITIATION (kata-initiate
  → frozen INTENT.md) → HARNESS (kata-orchestrate + the built loop) → CLOSEOUT (kata-closeout +
  kata-understand) — and owns the context-carrying loop-back that re-enters initiation on version-up.
license: Apache-2.0
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob]
source: new (KataHarness original — Phase 3 Kata Loop conductor, D87/DESIGN §1)
tags:
  - kata/coordinate
  - kata/spine
  - conductor
  - greater-loop
  - loop-back
---

# kata-loop — the Kata Loop conductor

The **thin top-level conductor** for the Kata Loop (DESIGN §1, D87). It **sequences** three existing
modules and never reimplements, re-plans, or re-evaluates anything — it composes. The greater loop is
**optional**: absent this conductor, a direct one-shot harness run behaves exactly as today (BC, DESIGN §9).

> **Composes, never reimplements (BC).** `kata-loop` orchestrates existing skills and modules — it is the
> routing shell, not the logic. The plan stays the orchestrator's; the gate stays [[kata-evaluate]]'s. The
> conductor adds no drift surface.

---

## The sequence

### 1. INITIATION — [[kata-initiate]]

Invoke [[kata-initiate]] (the front-half module, `modules/initiation/`). It:
- Ingests the user's design/brief and classifies intent kind (`project | research | version-up`).
- Leads interactive target / platform / vault configuration.
- Drives the grill to readiness under dual control (user "execute" or grill self-proposes).
- Writes and **freezes `INTENT.md`** — the authoritative hand-off artifact (`protocol/intent.md`).

`kata-loop` waits for a frozen `INTENT.md` before proceeding. It does not re-run initiation mid-harness.

**BC:** `INTENT.md` absent ⇒ the harness reads the frozen DESIGN as today; initiation is additive.

---

### 2. THE HARNESS — [[kata-orchestrate]] + the built loop

**First, emit the loop-init banner.** Before handing off to the orchestrator, render and print the
KataHarness loop-init readout as the **first lines of the harness** so the operator sees, every run,
that it is KataHarness executing and a brief summary of what:

```
uv run python tools/kata_banner.py --color --goal "<INTENT goal>" --run-shape <runShape> \
    --mode <mode> --grill <grillDepth> --delivery <delivery.shape> [--tasks N --slices M]
```

Draw the fields from the frozen `INTENT.md` (goal, run-shape) + `kata.config` (mode, grill, delivery);
pass `--tasks/--slices` once the freeze produces a plan (omit them before then — the renderer drops
missing fields). `--color` paints it in the **closeout-report palette** (Hokusai ochre/Prussian/paper,
`modules/closeout/resources/BRAND.md`) via ANSI — run it as a command so the terminal renders the color;
drop `--color` (or set `NO_COLOR`) if a surface shows raw escape codes. It is a **deterministic** readout
(`tools/kata_banner.py`, the canonical format — consistency D18; `protocol/narration.md`), not improvised prose.

Then hand the frozen `INTENT.md` + `kata.config` (written by `kata-bootstrap` during initiation) to
[[kata-orchestrate]]. The orchestrator drives the full built loop:

```
grill → freeze → execute (distributed, plan-faithful)
  → evaluate (default-FAIL) → handoff (two-way)
```

`kata-loop` does **not** re-plan, modify the plan, or change the frozen spec during the harness.
The plan is the orchestrator's; the gate is [[kata-evaluate]]'s. This conductor cannot gate — it
sequences.

**No mode change:** [[kata-orchestrate]] behaves identically whether invoked from this conductor or
directly. The conductor is a thin wrapper around an unmodified orchestrator (BC2, `kata-sprint` pattern).

---

### 3. CLOSEOUT — [[kata-closeout]] + [[kata-understand]]

When the harness emits its `.kata/` artifacts (`.kata/RESULT.json`, `.kata/footprint.json`,
`.kata/mutation.json`) and [[kata-evaluate]] has returned its PASS / NEEDS_WORK verdict, invoke
[[kata-closeout]] (the back-half module, `modules/closeout/`). It:
1. Tracks and reports the machine artifacts (via [[kata-report]]).
2. **Offers [[kata-understand]]** (opt-in per run) — the structured comprehension map of what changed
   and what was built, backed by the `kata-graph` runtime (graph-backed primary; git/diff light fallback).
3. Runs the **human decision gate**: *satisfied?* → *commit / push / merge?* → *run again or build new?*
4. Composes the two-way [[kata-handoff]] for the session boundary.

`kata-loop` does not override the [[kata-evaluate]] verdict. A NEEDS_WORK verdict is surfaced verbatim
by [[kata-closeout]] — the conductor never converts it to a pass.

---

## The loop-back (GL-R2d)

The loop-back is the one piece that belongs to `kata-loop` alone. After [[kata-closeout]] returns the
human's decision:

### Path A — "Run again (version-up)"

**Emit the compact loop-back banner** so the operator sees the new cycle begin:
`uv run python tools/kata_banner.py --color --goal "<next goal>" --tasks N --compact`
(a single `↻ KATAHARNESS 改善型 · loop-back — …` line). Then:

Re-enter [[kata-initiate]] **carrying context** from the completed run. The exact context payload:

| Payload element | Where it lives | Purpose |
|---|---|---|
| **New green baseline SHA** | `.kata/RESULT.json` → `resultSha` | The fork point the next run builds from |
| **Understand-map artifact** | `.kata/understand.md` (if [[kata-understand]] ran) | What changed in the prior run — prevents re-grilling already-mapped territory |
| **Lessons** | `.planning/LESSONS-LEARNED.md` (appended by closeout) | Surprises, decisions, and anti-patterns the next initiation should factor in |
| **Prior `INTENT.md`** | `INTENT.md` (frozen by prior initiation) | The prior run's goal, kind, target config, and grill depth — gives the next grill its starting frame |

[[kata-initiate]] receives these four elements as named inputs. It is **not** a cold start: it uses
the prior INTENT.md as its starting frame, surfaces the understand-map during Phase 1 (ingest), and
pre-populates the grill with the lessons as known-resolved branches. This composes existing artifacts —
no new protocol fields are introduced.

### Path B — "Build something else"

Start a fresh [[kata-initiate]] (cold). No prior-run context is carried. The conductor resets.

---

## What this conductor must NOT do

- **Not** re-plan or modify the frozen DESIGN/plan mid-harness.
- **Not** gate correctness — that stays with [[kata-evaluate]].
- **Not** invoke [[kata-evaluate]] directly (the orchestrator calls it at the final gate).
- **Not** carry out git actions autonomously — those require explicit human approval inside [[kata-closeout]].
- **Not** reimplement grill / evaluate / report / understand logic — **compose** them.
- **Not** change [[kata-orchestrate]] behavior (it stays sprint-blind and harness-blind to this conductor).

---

## Backward-compatibility and spine

- **BC:** absent this conductor, a direct one-shot harness run (`kata-bootstrap` → `kata-orchestrate`)
  behaves exactly as today. `INTENT.md` absent ⇒ the harness reads the frozen DESIGN. Modules are additive.
- **Spine preserved:** plan-doesn't-drift · default-FAIL never weakened · two-way handoff ·
  everything-versioned · agnostic-via-adapters (now at module granularity, DESIGN §4).
- **No new protocol:** the loop-back carries existing artifacts (`RESULT.json`, `INTENT.md`,
  `LESSONS-LEARNED.md`, `understand.md`). No new schema fields are defined here.

---

## Composed skills (all already exist)

- [[kata-initiate]] — front-half initiation module (INITIATION).
- [[kata-orchestrate]] — plan-guardian harness orchestrator (THE HARNESS).
- [[kata-closeout]] — back-half closeout module (CLOSEOUT).
- [[kata-evaluate]] — the default-FAIL gate (never invoked by this conductor — referenced for clarity).
- [[kata-handoff]] — two-way handoff artifact (composed inside [[kata-closeout]]).
- [[kata-report]] — durable run report (composed inside [[kata-closeout]]).
- [[kata-understand]] — understand-anything comprehension map (composed inside [[kata-closeout]], opt-in).
