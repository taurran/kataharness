---
name: kata-closeout
description: >-
  Back-half closeout that tracks a completed run's machine artifacts, composes a goal-anchored human-reviewable
  report (plain-language what-changed-and-why, by goal-aspect, before any path or gate number), offers the
  understand-map (opt-in), runs the human decision gate (satisfied / commit-push-merge / run-again or
  build-new / cleanly undo the whole run), and hands the decision to the conductor's loop-back — never gates
  correctness.
license: Apache-2.0
version: 0.1.0
category: handoff
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Bash]
model: fable
source: new (KataHarness original — Phase 2 Kata Loop back-half, D89/DESIGN §3)
tags:
  - kata/handoff
  - kata/module/closeout
  - closeout
  - human-gate
  - never-gates
---

# kata-closeout — the back-half closeout skill

`kata-closeout` owns the **back half of the Kata Loop**: it runs **after** the [[kata-evaluate]]
default-FAIL gate, tracks the run's machine artifacts, delivers a goal-anchored report (§5 skeleton,
plain-language-first), offers the comprehension map, runs the human decision gate, and hands the
decision to the conductor's loop-back. It **never gates** — gating stays with [[kata-evaluate]]
(spine principle #4, DESIGN §3). Voice: `protocol/persona.md`.

## Hard boundary — it reports, it never gates

The default-FAIL gate is and stays [[kata-evaluate]]. `kata-closeout`:
- Reads the gate's verdict from `.kata/RESULT.json` — verbatim, not re-derived.
- Surfaces a NEEDS_WORK verdict to the human as a clear finding; it does not override it.
- Never confers a pass/fail verdict of its own.
- Carries out git actions (commit/push/merge/rollback) **only on explicit human approval** — never
  autonomously.

## Step 1 — Track everything

Consume the three F1 machine artifacts written to `.kata/` by `tools/gate_emit.py`:

| Artifact | Path | What it contains |
|---|---|---|
| Gate result | `.kata/RESULT.json` | `gateName`, `exitCode`, `passed`/`failed`/`skipped`, `stdoutTail`, `baselineSha`, `resultSha`, `utc` |
| Footprint manifest | `.kata/footprint.json` | `footprint`, `changed`, `inFootprint`, `outOfFootprint`, `withinFootprint`, `diffstat` |
| Mutation proof | `.kata/mutation.json` | `records`, `allNonVacuous` — **required for a code-bearing run** (its absence makes [[kata-evaluate]] rubric item 1 NEEDS_WORK); legitimately absent only for a pure data/config/docs run |

Read all three with `Read` (or `Bash` for `cat` / `jq` formatting). Note `.kata/RESULT.json.baselineSha`
— this SHA is the **backout anchor** used in Step 4 (Decision 4). Do **not** reconstruct counts from
prose — the artifacts are the record. If any artifact is absent, note it explicitly as a gap in the
report; the "reports, never gates" principle still applies.

Also read the frozen `INTENT.md` to retrieve the plain-language goal statement for Step 2.

## Step 2 — Report (§5 skeleton — in order, always)

Compose [[kata-report]] over the consumed artifacts, passing the three artifact paths. Then present the
report to the human **in the fixed §5 order** below. Do **not** re-arrange this order; do not lead with
paths or gate numbers.

### §5.1 — Goal, restated

Open with the goal in plain language, taken directly from the frozen `INTENT.md`:

> "You wanted [goal statement from INTENT.md]."

No preamble. One or two sentences.

### §5.2 — What changed and why it matters to you (lead section — before any path or gate number)

Present the change story in **plain language**, organized **by goal-aspect** — the dimension of the goal
each change served. Each parallel worker's result folds into the goal-aspect it served.

- Group changes under headings like "To give you X, I…" or "To handle Y, I changed…"
- No file paths in this section. No gate numbers. No internal stage names (GRILL/FREEZE/…).
- If `kata-evaluate` returned NEEDS_WORK, report plainly what did not land: "I attempted X but it did
  not pass the check — here is what the check found." Never minimize or reframe a NEEDS_WORK.

This is the WS-5 hard requirement: plain-language what-changed-and-why leads every closeout.

### §5.3 — Did it hit the goal?

Honest assessment against the restated goal: fully / partially / here is the gap. One paragraph.
Quote the `kata-evaluate` verdict verbatim (from `.kata/RESULT.json`) — do not paraphrase it or confer
your own pass/fail. A NEEDS_WORK is reported plainly, never overridden.

### §5.4 — Risks and uncertainties

Name what is not fully certain, what is *exercised-not-proven* (run once end-to-end but no automated
regression), and what could bite. Follow the `protocol/persona.md` honesty norms: do not upgrade
"exercised" to "proven"; do not claim gated-off capabilities are live.

### §5.5 — Evidence, linked not dumped

For whoever wants to dig — list by path, do not re-transcribe:
- `.kata/RESULT.json` (gate result)
- The [[kata-report]] file (the full synthesis)
- `.kata/understand.md` — **only if** the understand-map was generated (Step 3 is opt-in)
- Any findings files (DEFERRED.md, ASSUMPTIONS.md, etc.)

### §5.6 — Your options (offered choices)

Present the options in plain language as explicit choices:

1. **Keep it** — commit / push / merge (the existing human-gated git actions; see Decision 2 below).
2. **Iterate** — run again (version-up) or build something new.
3. **Cleanly undo the whole run** — "I can cleanly roll this entire run back, as if it never happened."
   (See Decision 4 — Backout, below.)

**Foreground option 3 when the human is not satisfied** with the result.

## Step 3 — Offer the understand-map (opt-in)

**Offer** [[kata-understand]] to the human after the report is presented. This step is opt-in per run —
the human may skip it. When accepted:
- `kata-understand` produces a structured comprehension map of what changed + what was built, backed by
  the `kata-graph` runtime (graph-backed primary path; git/diff light fallback when the graph is
  unavailable).
- It is a comprehension aid, not a re-evaluation. It never blocks or gates.
- When run, it writes the map to `.kata/understand.md` — the path [[kata-loop]]'s loop-back carries
  forward.

## Step 4 — Human decision gate

Present the four decisions in sequence. Carry out only what the human explicitly approves.

### Decision 1 — Satisfaction

> *Are you satisfied with this run's output?*

- **Satisfied** → proceed to Decision 2.
- **Not satisfied** → surface the specific NEEDS_WORK items from `.kata/RESULT.json` + the `kata-report`
  drift ledger; foreground the backout option (Decision 4) as a first-class plain choice: "I can cleanly
  roll this entire run back, as if it never happened." Let the human decide whether to undo (Decision 4),
  loop (Decision 3), or stop.

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
  baseline: the understand-map (`.kata/understand.md`), the report, and any lessons. The [[kata-loop]]
  conductor carries this context into the next cycle's [[kata-initiate]] (see kata-loop's loop-back
  Path A).
- **Build something else** — a fresh initiation. The conductor starts a new loop cold.

Hand the human's decision to the conductor's loop-back as a durable artifact (written via [[kata-handoff]]).

### Decision 4 — Backout (WS-4; human-gated, never autonomous)

> *Cleanly undo this entire run, as if it never happened?*

Offer this in plain language:

> "I can cleanly roll this entire run back, as if it never happened. This resets the repository to the
> exact state it was in before this run started."

**Anchor:** `.kata/RESULT.json.baselineSha` — read in Step 1. This SHA is the **guaranteed** backout
point (emitted by `gate_emit.py` at run start; always present in the artifact). A `pre-<run>` tag is
optional convenience, not the anchor.

**Execution — human-gated, never autonomous:**
1. Show the diff first: `git diff <baselineSha>..HEAD --stat` — so the human sees exactly what will be
   discarded before approving.
2. Require **explicit approval** from the human ("yes, roll it back" or equivalent).
3. Only then execute: `git reset --hard <baselineSha>`
4. Confirm the reset completed and the working tree matches the baseline.

This action is **under the same behavioral guard as commit/push/merge** — never auto-run, never run
without the diff-first/explicit-approval sequence. Treat any autonomous rollback as a conformance
violation identical to an autonomous push.

**Foreground Decision 4 when the human is not satisfied** with the result (§5.6 / Decision 1 not-satisfied
path). It is a first-class option, not a footnote.

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
- The [[kata-loop]] conductor (Phase 3) sequences this skill and owns the loop-back; closeout hands it the
  human decision and the loop-back context payload.
- `allowed-tools` includes `Bash` only to read `.kata/` artifacts and carry human-approved git actions
  (including the backout `git reset --hard`). It never executes target code. **Note (known limitation):**
  `Bash` cannot be restricted to specific git subcommands in frontmatter, so the "never auto-push/merge/
  rollback" rule is a **behavioral** guard (human-gated above), not a structural one. Treat any push/merge/
  reset without explicit human approval as a conformance violation.
