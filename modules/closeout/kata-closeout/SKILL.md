---
name: kata-closeout
description: >-
  Back-half closeout that tracks a completed run's machine artifacts, composes a human-reviewable report,
  offers the understand-map (opt-in), runs the human decision gate (satisfied / commit-push-merge /
  run-again or build-new), and hands the decision to the conductor's loop-back — never gates correctness.
license: Apache-2.0
version: 0.1.0
category: handoff
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Bash]
model: fable
source: new (KataHarness original — Phase 2 Greater Loop back-half, D89/DESIGN §3)
tags:
  - kata/handoff
  - kata/module/closeout
  - closeout
  - human-gate
  - never-gates
---

# kata-closeout — the back-half closeout skill

`kata-closeout` owns the **back half of the Greater Loop**: it runs **after** the [[kata-evaluate]]
default-FAIL gate, tracks the run's machine artifacts, reports, offers the comprehension map, runs the
human decision gate, and hands the decision to the conductor's loop-back. It **never gates** — gating
stays with [[kata-evaluate]] (spine principle #4, DESIGN §3).

## Hard boundary — it reports, it never gates

The default-FAIL gate is and stays [[kata-evaluate]]. `kata-closeout`:
- Reads the gate's verdict from `.kata/RESULT.json` — verbatim, not re-derived.
- Surfaces a NEEDS_WORK verdict to the human as a clear finding; it does not override it.
- Never confers a pass/fail verdict of its own.
- Carries out git actions (commit/push/merge) **only on explicit human approval** — never autonomously.

## Step 1 — Track everything

Consume the three F1 machine artifacts written to `.kata/` by `tools/gate_emit.py`:

| Artifact | Path | What it contains |
|---|---|---|
| Gate result | `.kata/RESULT.json` | `gateName`, `exitCode`, `passed`/`failed`/`skipped`, `stdoutTail`, `baselineSha`, `resultSha`, `utc` |
| Footprint manifest | `.kata/footprint.json` | `footprint`, `changed`, `inFootprint`, `outOfFootprint`, `withinFootprint`, `diffstat` |
| Mutation proof | `.kata/mutation.json` | `records`, `allNonVacuous` — absent if no mutation step ran |

Read all three with `Read` (or `Bash` for `cat` / `jq` formatting). Do **not** reconstruct counts from
prose — the artifacts are the record. If any artifact is absent, note it explicitly as a gap in the report;
the "reports, never gates" principle still applies.

## Step 2 — Report

Compose [[kata-report]] over the consumed artifacts. The report is the durable, Obsidian-native synthesis
of the run's evidence trail: gate result → what shipped (by path) → drift ledger → open items. Pass the
three artifact paths to `kata-report`; do not re-transcribe by hand.

## Step 3 — Offer the understand-map (opt-in)

**Offer** [[kata-understand]] to the human after the report is presented. This step is opt-in per run — the
human may skip it. When accepted:
- `kata-understand` produces a structured comprehension map of what changed + what was built, backed by the
  `kata-graph` runtime (graph-backed primary path; git/diff light fallback when the graph is unavailable).
- It is a comprehension aid, not a re-evaluation. It never blocks or gates.

Reference: `kata-understand` is built in parallel (slice C1) and resolves at integration.

## Step 4 — Human decision gate

Present the three decisions in sequence. Carry out only what the human explicitly approves.

### Decision 1 — Satisfaction

> *Are you satisfied with this run's output?*

- **Satisfied** → proceed to Decision 2.
- **Not satisfied** → surface the specific NEEDS_WORK items from `.kata/RESULT.json` + the `kata-report`
  drift ledger. Let the human decide whether to loop (Decision 3) or stop.

### Decision 2 — Git actions (only if satisfied or explicitly requested)

> *Commit / push / merge?*

Present the available git actions based on the current branch state (read via `Bash git status`):
- **Commit** — stage the declared footprint files and commit with a conventional commit message.
- **Push** — push the branch to the remote (only after explicit approval).
- **Merge** — merge to the target branch (only after explicit approval; present a dry-run diff first).

Carry out **only the actions the human selects**. Never auto-push or auto-merge. The git actions are
**human-gated** (spine principle #2 — no plan drift; no autonomous git actions beyond commit).

### Decision 3 — Loop disposition

> *Run again (version-up) or build something else?*

- **Run again (version-up)** — the next cycle re-enters the initiation module with this run's context as
  baseline: the understand-map, the report, and any lessons. The conductor (to be built in Phase 3 as the
  `kata-loop` skill; reference in prose only — not yet built) carries this context into the next cycle.
- **Build something else** — a fresh initiation. The conductor starts a new loop cold.

Hand the human's decision to the conductor's loop-back as a durable artifact (written via [[kata-handoff]]).

## Step 5 — Compose the two-way handoff

Compose [[kata-handoff]] for the session boundary. The handoff MUST include:
1. **Read-in order** — the canonical files to load to rebuild context.
2. **State** — branch / commit SHA / the gate result (`exitCode`, `passed`/`failed`/`skipped`).
3. **What shipped** — concretely, with paths from `.kata/footprint.json`.
4. **NEXT STEP** — the conductor's loop-back disposition (run-again or build-new) with enough context for
   the next session to start doing, not deciding.
5. **Open decisions for the human** — anything deferred or unresolved.

## Backward-compatibility and spine

- Closeout is **additive**. Absent the closeout module, the harness completes with `kata-evaluate` as today.
- The default-FAIL gate is **never weakened**: closeout never converts a NEEDS_WORK to a pass.
- `kata-loop` (the Phase 3 conductor) is referenced in prose only — it is not yet built and must not be
  wikilinked.
- `allowed-tools` includes `Bash` only to read `.kata/` artifacts and carry human-approved git actions.
  It never executes target code.
