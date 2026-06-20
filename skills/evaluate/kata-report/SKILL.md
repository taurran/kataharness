---
name: kata-report
description: >-
  Synthesize a one-page report of a completed unit of work (a sprint, or any gated build segment) from the
  durable trail — gate result, what shipped, drift ledger, open items. Use at a sprint boundary to give the
  human a reviewable summary before they steer, or standalone after any gated run. It REPORTS; it does not
  gate (kata-evaluate owns the default-FAIL gate) — so a one-shot run can reuse it too.
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
---

# kata-report — one-page report of a gated unit of work

The minimal **v1** of the D32 report (sprint-cadence D2: *the per-sprint one-page report **is** `kata-report v1`,
not throwaway; D32 expands later*). It reads the durable trail and writes a single reviewable page. It is the
**stop-side** companion `kata-sprint` composes at a boundary — but it is delivery-agnostic, so a one-shot run can
invoke it after its gate too.

## Hard boundary — it reports, it never gates
`kata-report` **synthesizes**; it does **not** evaluate or decide. The default-FAIL gate is and stays
[[kata-evaluate]] (D22). `kata-report` only *transcribes* the gate's verdict + numbers into the page. It owns no
pass/fail authority — if there were no green gate, the report says so, it does not confer one.

## What the page contains
A durable, Obsidian-native doc (frontmatter + tags), one page, dense:
1. **Unit + goal** — the sprint id (or run id) and the goal it was meant to deliver (from the roadmap / plan).
2. **Gate result** — the [[kata-evaluate]] verdict + the green numbers verbatim: tests (pass/fail/skip), build
   (deterministic hash), security (Snyk count). Never re-compute — quote the gate.
3. **What shipped** — concretely, by **path** (the files/skills added or changed), tied to the plan task ids.
4. **Drift ledger** — the run's `driftLedger` (authorized vs unauthorized deviations, escalations,
   interventions) from [[protocol|state]]; flag any unauthorized deviation explicitly.
5. **Open items** — anything deferred ([[kata-defer]] `DEFERRED.md`), assumptions logged
   (`ASSUMPTIONS.md`), and decisions pending a human.

## Discipline
- **Read the trail, don't re-derive.** Pull from the committed reports / state / board — the report is a
  synthesis of durable record, not a fresh investigation.
- **One page.** Dense and skimmable; the human reads it to decide whether to steer (at a boundary) or to
  confirm done (one-shot). Long detail belongs in the artifacts it points to, by path.
- **Lossless on the gate numbers + open items** — those drive the human's next decision.
- Write the report into the **tier-2 durable trail** (git-committed) so [[kata-readiness]] can find it on
  resume and `kata-sprint` can present it at the boundary.
