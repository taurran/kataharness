---
spec: backlog-burn-mode
status: draft
opened: 2026-08-15
tier: pre-design operator rulings (planning-session brainstorm; full grill still owed before DESIGN)
evidence: ../backlog-burn-01/OBSERVATIONS.md (the prototype run's live-recorded evidence base)
---

# GRILL LEDGER — Backlog Burn mode (BL-N12)

**What this is:** the operator's design rulings from the 2026-08-15 planning session, recorded
in-repo so the eventual full grill starts from decisions, not transcript archaeology. The
prototype's evidence file (`.planning/specs/backlog-burn-01/OBSERVATIONS.md`, H1–H7) is the
grounding for every entry. **This is NOT a frozen contract** — the mode still owes a full
doc-grounded grill + convergence gate + DESIGN before any build.

## Operator rulings (2026-08-15)

- **BBM-1 · Gate design — HYBRID.** Two layers replace serial conductor gating (the confirmed H1
  bottleneck): (1) every builder MUST ship mechanical self-gates (assertions, pins, the gauntlet)
  that the conductor merely RE-RUNS; (2) a fresh-context no-write **gate agent per item** runs
  concurrently with other items' gates for the judgment half (diff-vs-brief, independent claim
  reproduction). The conductor adjudicates conflicts and **spot-audits one item per wave**.
  Independence is kept; the serial queue is broken.

- **BBM-2 · Partitioning — FULL DEDICATED ENGINE.** A new `tools/burn_partition.py` owns the whole
  pipeline: graph rebuild → import-closure owner sets (module + everything importing it + every
  test touching those, per H4) → wave assignment → unowned-test detection, fail-closed on overlap.
  *Operator chose the dedicated module over the conductor's smaller-surface recommendation —
  deliberate, on the expectation the mode grows.* **Prerequisite: BL-X06→BL-X04 — `graph_gen` must
  exclude embedded worktrees first** (a mid-burn rebuild is ~7× garbage today, measured).

- **BBM-3 · Intake — normalized backlog first; GitHub issues is the future primary.** v1 burns the
  in-repo backlog ONLY — but the backlog mechanism itself gets **standardized and normalized as a
  low-touch alternative to full GitHub issue tracking** (BL-N11 is therefore a designed
  PREREQUISITE of this mode's intake, not a sibling), with the item shape designed so GitHub
  issues maps onto it later without rework.

- **BBM-4 · Wave width — partition-bound with a config cap.** The partition engine emits the
  maximal safe wave; a configurable cap (default ~4) trims it to adjudication capacity. **When the
  Kitchen's fan-out dial (BL-N09) lands, that dial becomes the cap's owner** — one knob family,
  never two.

- **BBM-5 · Entry — burn is a run-shape; the primary path is the guided `/kata-start` flow.** No
  separate command as the primary door. The guided interview EXPANDS to cover: run-shape (incl.
  burn) · economy settings · multi-model settings · **fan-out settings** · second-brain location
  (skipped when config carries it) · vault location (same) · grill-with-docs · **goal/system-prompt
  optimization** (new capability, filed as BL-N13). The whole interview **rolls up into the agent
  launch command + UX rework** (BL-N06/BL-N07), which the operator directed be grilled in this same
  planning run.

- **BBM-6 · Accuracy is a number — ledger rows + defect linkback.** Every burn writes per-item
  telemetry rows (wall-clock, tokens, gate outcome, brief-was-wrong?, escalations) at close via the
  existing `kata_telemetry` ledger; **any defect later found in burned code is linked back to its
  burn item**, so each burn accrues an honest defects-shipped count over time. The linkback
  discipline is the only new obligation.

## Locked from prototype evidence (not re-litigated; cite OBSERVATIONS.md)

- **BBM-7 · Triage precedes the grill, mandatorily** (H2: 2 of 6 items changed materially under
  investigation — building from filings builds the wrong things).
- **BBM-8 · The convergence gate is non-optional and must attack the SHARED half** — the wave plan
  and standing rules are explicit targets, not just item specs (H3 confirmed + H5 ×2: every
  high-severity finding lived in the shared contract; one brief was internally unsatisfiable).
- **BBM-9 · Base-SHA pinning is structural** (H6 ×2: two independent provisioners produced a wrong
  base). The conductor pins the SHA into `git worktree add` itself; every brief's step 0 is
  builder-verified base + clean-tree, reported back.
- **BBM-10 · Builders are briefed to push back** (H7: "if the brief is wrong, say so and STOP" —
  three real catches in one wave; it converts builders into second reviewers for one sentence).

## Still open for the full grill (deliberately undecided today)

external-source adapter contract shape (what a GitHub issue must carry to be grillable) · gate-agent
brief template + how a judge's verdict is recorded durably · does the partition rule generalize
beyond this repo's shape (prototype question 4) · burn's interaction with freeze semantics (D169
blocks dispatch on non-frozen plans — what is "the plan" when the contract is a multi-item ledger?)
· cap tuning evidence beyond width-3.
