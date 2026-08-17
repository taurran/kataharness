---
name: kata-loop
description: >-
  The thin top-level conductor that sequences the Kata Loop end-to-end — INITIATION (kata-initiate
  → frozen INTENT.md) → HARNESS (kata-orchestrate + the built loop) → CLOSEOUT (kata-closeout +
  kata-understand) — and owns the context-carrying loop-back that re-enters initiation on version-up.
license: Apache-2.0
version: 0.3.0
category: coordinate
status: beta
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

## Phase awareness — the conductor is positioned by the cursor, not by memory

This conductor is **phase-aware by contract**. Two rules bind every stage boundary below, and
neither is optional or tiered.

### 1. Seam init before anything else

The FIRST act of a run is `kata_dispatch.run_start(kata_dir, repo_root=…)`. It performs
new-vs-resume discrimination mechanically (no live cursor, or a live cursor whose run is CLOSED ⇒
**new**: rotate + mint a fresh `runId`; a live cursor with an unclosed run ⇒ **resume**: ADOPT the
header's `runId`, reap orphan dispatch records, continue), writes the run marker, probes the hook +
deny tripwire, and returns the §6.4 minimal run-start `declaration`. **Print the declaration** —
enforcement / capture / resilience are DERIVED from the probes, never asserted. A resumed session
never re-mints; a re-loop and a loop-back always do (`force_new=True`).

### 2. Every stage boundary emits a PHASE event

Call the seam `phase()` function — `kata_dispatch.phase(kata_dir, "<msg>")` — at each boundary. It
appends the seam-authored PHASE line and fires the durability cadence. The msg grammar is
**enforced** (`open <PHASE> [k=v …]` | `close <PHASE> [k=v …]` | `run-closed [k=v …]`) over the
closed vocabulary `INITIATION · GRILL · AUTHORING · FREEZE · EXECUTION (wave=<n>) · FINAL-GATE ·
CLOSEOUT · LOOP-BACK`. Opening an already-open phase, closing an unopened one, or re-opening a
closed one is a **refusal recorded as a DENY event** — never a silent no-op.

| Boundary in the sequence below | The call |
|---|---|
| Initiation opens | `phase(kata, "open INITIATION")` |
| Initiation ends (frozen `INTENT.md` in hand) | `phase(kata, "close INITIATION")` |
| The harness begins | `phase(kata, "open EXECUTION wave=<n>")` |
| The harness's wave ends | `phase(kata, "close EXECUTION wave=<n>")` |
| The final gate opens / closes | `phase(kata, "open FINAL-GATE")` / `close FINAL-GATE` |
| Closeout opens / closes | `phase(kata, "open CLOSEOUT")` / `close CLOSEOUT` |
| A loop-back is taken | `phase(kata, "open LOOP-BACK")`, then the new run's header carries `prev-run:` |

GRILL / AUTHORING / FREEZE boundaries are emitted by the skills that own those stages (the grill
and the freeze act) — this conductor does not double-stamp them.

**`run-closed` is the terminal record**, written exactly once by `close_run` at the end of the
whole loop — `close_run` is W7 `close-machinery` (`tools/kata_close.py`) and is **NOT YET BUILT**.
Nothing is legal on the cursor after that line, but **until W7 lands the line is never written and
the run stays open**. Do not simulate it: hand-writing a `run-closed` PHASE line would be a
conductor authoring a seam TYPE, and the gap is meant to be visible, not papered over.

### 3. Position is READ, never remembered (TM-C5)

Before routing to the next stage, **read the position from the cursor** —
`kata_dispatch.phase_state(kata_dispatch_cursor)` returns `{"open": [...], "closed": [...],
"runClosed": bool}`, and `kata_dispatch.is_run_closed(cursor)` is the terminal test. Never re-derive
position from context memory: a conversational recollection does not survive a compaction, a crash,
or a fresh subagent, and "I think I already ran initiation" is not evidence that initiation ran.

### 4. In-session sequencing is CURSOR-TRACKED, not dispatch-gated (TM-B3)

The stage-to-stage sequencing in this file — kata-loop → [[kata-initiate]] → [[kata-bootstrap]] →
[[kata-orchestrate]] — is **the conductor reading its own instructions**. Those invocations emit
PHASE cursor events; they do **not** mint dispatch records and are **not** denied for lacking one.
Dispatch records are required only where the conductor **launches another agent** (workers, judges,
authors, the advisor, researchers) — that is `mint()`'s territory, not this sequence's.

---

## The sequence

### 1. INITIATION — [[kata-initiate]]

Emit `phase(kata, "open INITIATION")` first — the initiation governor rung's predicate is an **open
INITIATION or AUTHORING phase event on the live cursor**, so without this event an initiation-phase
mint has no legal rung and refuses. Then invoke [[kata-initiate]] (the front-half module,
`modules/initiation/`). It:
- Ingests the user's design/brief and classifies intent kind (`project | research | version-up`).
- Leads interactive target / platform / vault configuration.
- Drives the grill to readiness under dual control (user "execute" or grill self-proposes).
- Writes and **freezes `INTENT.md`** — the authoritative hand-off artifact (`protocol/intent.md`).

`kata-loop` waits for a frozen `INTENT.md` before proceeding, then emits
`phase(kata, "close INITIATION")`. It does not re-run initiation mid-harness — **re-opening
INITIATION on a run that already records a stronger governor (`plan:frozen` or `ledger:converged`)
is a recorded DENY-class event**, and the seam refuses it rather than trusting the conductor's
restraint.

"Frozen" here is the artifact's own recorded state, not the conductor's impression of it: the
`intent` governor rung reads `INTENT.md` frontmatter `status: frozen`, which
`intent_scaffold.write_intent` writes only when [[kata-initiate]]'s Phase-6 freeze act passes
`freeze=True`.

**BC:** `INTENT.md` absent ⇒ the harness reads the frozen DESIGN as today; initiation is additive.
A direct one-shot harness run that never entered via initiation governs under `plan` exactly as
today — `intent: frozen` binds only runs that entered via initiation/`kata-loop`.

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

Then emit `phase(kata, "open EXECUTION wave=<n>")` and hand the frozen `INTENT.md` + `kata.config`
(written by `kata-bootstrap` during initiation) to [[kata-orchestrate]]. `EXECUTION` is the one
parameterized phase and its per-wave `open`/`close` matching is enforced — a wave closed without
being opened, or opened twice, is refused. The orchestrator drives the full built loop:

```
grill → freeze (design-author → plan-author dispatch, DESIGN §4.2, KH-T13) → execute (distributed, plan-faithful)
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
`.kata/mutation.json`) and [[kata-evaluate]] has returned its PASS / NEEDS_WORK verdict, close the
execution wave and the final gate (`close EXECUTION wave=<n>`, `close FINAL-GATE`), emit
`phase(kata, "open CLOSEOUT")`, and invoke [[kata-closeout]] (the back-half module,
`modules/closeout/`). It:
1. Tracks and reports the machine artifacts (via [[kata-report]]).
2. **Offers [[kata-understand]]** (opt-in per run) — the structured comprehension map of what changed
   and what was built, backed by the `kata-graph` runtime (graph-backed primary; git/diff light fallback).
3. Runs the **human decision gate**: *satisfied?* → *commit / push / merge?* → *run again or build new?*
4. Composes the two-way [[kata-handoff]] for the session boundary.

`kata-loop` does not override the [[kata-evaluate]] verdict. A NEEDS_WORK verdict is surfaced verbatim
by [[kata-closeout]] — the conductor never converts it to a pass. The verdict it surfaces is the
**persisted VERDICT record** captured by `kata_dispatch.capture()` (a cursor VERDICT line plus its
required JSON payload), not a value carried in conversation.

**Closeout Decisions 1–4 land as structured cursor records** — including *backout-approved*, the
highest-stakes previously-unrecorded event. A decision the operator made and the cursor did not
record did not happen for any downstream fold.

---

## The loop-back (GL-R2d)

The loop-back is the one piece that belongs to `kata-loop` alone. After [[kata-closeout]] returns the
human's decision:

### Path A — "Run again (version-up)"

**Record the loop-back on the cursor, then emit the compact loop-back banner** so the operator sees
the new cycle begin. The order matters:

1. `phase(kata, "open LOOP-BACK")`.
2. Close the phases the run still holds open.
3. **⛔ PARKED UNTIL W7 — not an executable step today.** The terminal `run-closed` record is
   `close_run`'s to write, and `close_run` is W7 `close-machinery` (`tools/kata_close.py`), **NOT
   YET BUILT**: a conductor following this sequence today finds nothing to call. **The sequence
   STOPS here.** Record the gap — the run is left open on its cursor, with no terminal line — and
   surface it; do not hand-write the line, and do not improvise a substitute close. What happens
   between this step and the next run is W7's ruling to make, not this contract's to assume.
4. *(after W7)* The next run's `run_start(kata, force_new=True, prev_run=<this runId>)` mints a
   fresh `runId` whose header carries the `prev-run:` chain pointer. A loop-back **always
   re-mints**; only a crash-resume adopts.

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
- **Not** hand-write a PHASE (or any seam-authored) line onto the cursor. Seam TYPEs come from
  `tools/kata_dispatch.py` — `phase()`, `mint()`, `capture()`, `deny()` — and nowhere else.
- **Not** infer its own position from context memory when the cursor can be read.

---

## Backward-compatibility and spine

- **BC:** absent this conductor, a direct one-shot harness run (`kata-bootstrap` → `kata-orchestrate`)
  behaves exactly as today. `INTENT.md` absent ⇒ the harness reads the frozen DESIGN. Modules are additive.
- **Spine preserved:** plan-doesn't-drift · default-FAIL never weakened · two-way handoff ·
  everything-versioned · agnostic-via-adapters (now at module granularity, DESIGN §4).
- **No new protocol:** the loop-back carries existing artifacts (`RESULT.json`, `INTENT.md`,
  `LESSONS-LEARNED.md`, `understand.md`). No new schema fields are defined here; the phase events
  and the `prev-run:` chain pointer are the existing cursor contract (`protocol/cursor.md`).

---

## Composed skills (all already exist)

- [[kata-cursor]] — the run's one durable temporal record; the position this conductor reads.
- [[kata-initiate]] — front-half initiation module (INITIATION).
- [[kata-orchestrate]] — plan-guardian harness orchestrator (THE HARNESS).
- [[kata-closeout]] — back-half closeout module (CLOSEOUT).
- [[kata-evaluate]] — the default-FAIL gate (never invoked by this conductor — referenced for clarity).
- [[kata-handoff]] — two-way handoff artifact (composed inside [[kata-closeout]]).
- [[kata-report]] — durable run report (composed inside [[kata-closeout]]).
- [[kata-understand]] — understand-anything comprehension map (composed inside [[kata-closeout]], opt-in).
