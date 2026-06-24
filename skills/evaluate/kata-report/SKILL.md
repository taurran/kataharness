---
name: kata-report
description: >-
  Synthesize a goal-anchored, by-goal-aspect report of a completed unit of work (a sprint, or any gated
  build segment) from the durable trail — gate result, what shipped grouped by the goal-aspect each change
  served, drift ledger, open items. Use at a sprint boundary to give the human a reviewable summary before
  they steer, or standalone after any gated run. It REPORTS; it does not gate (kata-evaluate owns the
  default-FAIL gate) — so a one-shot run can reuse it too. Voice: protocol/persona.md.
license: Apache-2.0
version: 0.1.0
category: evaluate
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Write]
model: sonnet
source: new (KataHarness original — the D32 report, minimal v1; sprint-cadence D85/D2)
tags:
  - kata/evaluate
  - kata/module/report
  - report
  - synthesis
  - boundary
  - goal-anchored
---

# kata-report — goal-anchored report of a gated unit of work

The minimal **v1** of the D32 report (sprint-cadence D2: *the per-sprint one-page report **is** `kata-report v1`,
not throwaway; D32 expands later*). It reads the durable trail and writes a single reviewable page.
It is the **stop-side** companion `kata-sprint` composes at a boundary — but it is delivery-agnostic, so
a one-shot run can invoke it after its gate too.

Voice is governed by `protocol/persona.md`: plain-language-first, lead with outcomes not machinery, warm
through clarity, honest about uncertainty. The report renders in the persona's voice throughout.

## Hard boundary — it reports, it never gates

`kata-report` **synthesizes**; it does **not** evaluate or decide. The default-FAIL gate is and stays
[[kata-evaluate]] (D22). `kata-report` only *transcribes* the gate's verdict + numbers into the page. It
owns no pass/fail authority — if there were no green gate, the report says so, it does not confer one.

## What the page contains

A durable, Obsidian-native doc (frontmatter + tags), one page, dense. Sections in order:

### 1. Goal, restated

Plain language, from the frozen `INTENT.md`: "You wanted X." One or two sentences. No preamble.

### 2. What changed and why it matters — by goal-aspect (lead section)

The change story in **plain language**, organized **by the goal-aspect each change served**. This is the
WS-5 hard requirement: it leads every report, before any path or gate number.

Group changes under goal-aspect headings, for example:

> **To give you [goal-aspect A]:** I built / changed…
> **To handle [goal-aspect B]:** I updated…

Each parallel worker's result folds into the goal-aspect it served — not listed by worker, by worker file,
or by execution order. The organizing principle is the *goal dimension*, not the implementation structure.

Rules for this section:
- **No file paths** in this section. No gate numbers. No internal stage names (GRILL/FREEZE/…).
- If `kata-evaluate` returned NEEDS_WORK on a goal-aspect, state it plainly: "I attempted [X] but it did
  not pass the check — [brief plain-language finding]." Never minimize or reframe a NEEDS_WORK.
- Write in the persona voice: lead with what it means for the human, not for the machinery.

### 3. Gate result

The [[kata-evaluate]] verdict + the green numbers verbatim: tests (pass/fail/skip), build
(deterministic hash), security (Snyk count). **Never re-compute — quote the gate** (from
`.kata/RESULT.json`). A NEEDS_WORK is quoted as-is; it is not softened or reframed.

### 4. What shipped — by path

Concretely, by **path** (the files/skills added or changed), tied to the plan task ids. Assert that the
set of touched files is a subset of (`⊆`) the plan's declared file-ownership partition. Any file outside
that set is an unauthorized deviation and must appear in the drift ledger (section 5 below).

### 5. Drift ledger

The run's `driftLedger` (authorized vs unauthorized deviations, escalations, interventions) from
[[protocol|state]]. Flag any unauthorized deviation explicitly. If there were none, state so briefly.

### 6. Risks and uncertainties

What is not fully certain, what is *exercised-not-proven* (run once but no automated regression), what
could bite. Governed by the `protocol/persona.md` honesty norms: "exercised, not proven" is not upgraded.

### 7. Open items

Anything deferred ([[kata-defer]] `DEFERRED.md`), assumptions logged (`ASSUMPTIONS.md`), and decisions
pending a human.

## Machine-readable artifacts the report MUST embed or reference

The report is the durable synthesis of the run's evidence trail. It **must** embed or point to (by path)
all three of the following artifact types — prose-only descriptions are not sufficient:

1. **`RESULT.json`** — the machine-readable gate output emitted during the [[kata-evaluate]] run. The
   report must quote (or path-link) the gate name, exit code, and `counts` (pass / fail / skip) verbatim
   from this file. Do **not** re-transcribe by hand; copy from the artifact.

2. **Footprint manifest + diff-stat** — the list of files actually touched by the run, plus the diff-stat
   summary (e.g. `git diff --stat baseline..result`). The report must assert that the set of touched files
   is a subset of (`⊆`) the plan's declared file-ownership partition. Any file outside that set is an
   unauthorized deviation and must appear in the drift ledger (section 5 above).

3. **Mutation / non-vacuity proof** — the record confirming that the test suite exercised real behavior
   (e.g., a mutation-test summary, a before/after snapshot, or a logged probe showing at least one
   meaningful assertion would fail if the logic were removed). This guards against a green gate achieved
   purely by disabling or vacuously passing tests.

All three artifacts are referenced by their committed path in the tier-2 durable trail. If any artifact is
absent, the report notes it explicitly as a gap — the "reports, never gates" principle does not change, but
absence is surfaced so [[kata-evaluate]] (or the human) can act.

## Discipline

- **Read the trail, don't re-derive.** Pull from the committed reports / state / board — the report is a
  synthesis of durable record, not a fresh investigation.
- **One page.** Dense and skimmable; the human reads it to decide whether to steer (at a boundary) or to
  confirm done (one-shot). Long detail belongs in the artifacts it points to, by path.
- **Lead with the goal-aspect synthesis** (section 2) — always before paths or gate numbers. This is the
  WS-5 hard requirement.
- **Lossless on the gate numbers + open items** — those drive the human's next decision.
- **Voice: `protocol/persona.md` throughout.** Plain-language outcomes before machinery; honest on
  uncertainty; no inflation.
- Write the report into the **tier-2 durable trail** (git-committed) so [[kata-readiness]] can find it on
  resume and `kata-sprint` can present it at the boundary.
