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

- **BBM-11 · Wave-boundary dial (operator question 2026-08-16: "do humans pause between waves?").**
  Three positions, set at bootstrap, DECLARED in the run-start report (truth serum — the user knows
  before anything runs whether they will be pinged, paused, or left alone):
  **autonomous** (waves flow; each boundary prints the phase-break block + a wave-end notice) ·
  **notify** (same flow + a real notification per wave end via the breakthrough-alert channel;
  intervene-able, never waits) · **approve** (hard human gate; the run WAITS at every wave end).
  Rationale for the gate existing at all: wave N can change the ground under wave N+1 (the
  prototype lived this — convergence findings amended the wave-2 contract), spend checkpoints, and
  attended-vs-walk-away reality (headless must never block — the quota-park posture). This is the
  burn/wave generalization of the existing sprint-boundary checkpoint (`kata-sprint` G1–G4) — reuse
  that seam, do not invent a second one. Not a different run — the same run, configured.
  **Refined (operator, 2026-08-16): driven by a RUN-CONFIG key with per-run-shape defaults.**
  `waveBoundaries: autonomous | notify | approve` in `kata.config`; defaults by shape:
  **burn ⇒ autonomous, always** (a burn never asks between waves) · **wave/sprint-cadence runs ⇒
  approve** (prompt at every boundary — that is what the cadence is FOR) · **version-up ⇒ no
  default, explicitly ASKED in the guided start flow**. Changeable: at bootstrap (the guided flow
  surfaces it), and mid-run via the steering channel (candidate: a `kata_steer` verb — verify that
  grammar exposes the seam at grill time, do not assume). The run-start report HIGHLIGHTS the
  declaration (chip treatment, UX-16) — it is the one line that tells the user whether the run
  will ever stop and wait for them.

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

## BBM-12 · 🔴 BURNS RUN THE ENTIRE LOOP — operator ruling 2026-08-16, verbatim intent, BINDING NOW

**A backlog burn USES THE ENTIRE LOOP** — initiation → grill → freeze → execute → evaluate →
handoff → improve — **iterating the loop as it was intended to function.** The conductor-driven
bypass that ran burn-01 and burn-02 (host-dispatch, no board, no kata-orchestrate, no
kata-evaluate contract, no final whole-run eval, no improve fold) **is DRIFT, not a mode** — the
operator's words: taking that shortcut means something is seriously wrong with the harness, and
"prototype" stopped being an excuse the day the loop machinery shipped.

Two sanctioned shapes, the fork to be ruled at the full grill (both keep the WHOLE loop):
- **(a) burn = ONE greater-loop run** — one broad triage+grill across the set (BBM-7/8), one
  freeze, waves as the execute phase's internal structure, ONE final default-FAIL evaluation of
  the integrated outcome; **if the final eval fails, the greater loop runs AGAIN — like normal.**
- **(b) wave = one greater loop each** — every wave is a full loop iteration with its own eval;
  the burn is the loop-back chain.

Consequences, binding on every future burn: the loop's seams (advisor, inline evaluator,
telemetry, board, orientation) apply BECAUSE the burn is inside the loop — the "which seams bind"
question below collapses to "all of them, via the loop." The prior entry's framing (seam gap as
an open design question) UNDERSOLD the defect and is superseded by this ruling: the gap is not
that seams lack reach into conductor-driven burns; it is that conductor-driven burns should not
exist. Enforcement is filed as 🔴 BL-M34 (a prose rule with nothing stopping the bypass is the
enforcement-sweep class all over again). Burn-02's missing final evaluation is being run
retroactively (2026-08-16) under the kata-evaluate contract; its verdict decides whether the
greater loop re-runs over that scope.

## Still open for the full grill (deliberately undecided today)

external-source adapter contract shape (what a GitHub issue must carry to be grillable) · gate-agent
brief template + how a judge's verdict is recorded durably · does the partition rule generalize
beyond this repo's shape (prototype question 4) · burn's interaction with freeze semantics (D169
blocks dispatch on non-frozen plans — what is "the plan" when the contract is a multi-item ledger?)
· cap tuning evidence beyond width-3.

**NEW (2026-08-16, from burn-02 live evidence — the dispatch-seam gap, third instance):** which
loop-cognition seams bind on a burn? Burn-02 ran conductor-driven through the host dispatch path,
and as a result: **zero telemetry rows** (BBM-6's own accuracy metric had to be hand-tallied),
**zero UX-33 agent-type counters**, and — found by operator question — **the standing advisor
grant never reached the run**: `kata.config` carries `advisor.approved: true` with `planning` in
its phases, yet the burn's plan authoring and convergence rounds never offered the advisor a
consult, because the trigger hooks (failThreshold/rerollTrigger/fixLoopCeiling) live inside
kata-orchestrate, which a conductor-driven burn never enters. (Honest half: no mechanical trigger
would have tripped anyway — 1 gate rejection vs threshold 2, 0 rerolls — the M4 fire-on-signal
doctrine behaved correctly; the gap is REACH, not misfire.) The full grill must decide: do burns
route through the loop's seams (advisor, inline evaluator, telemetry) or carry their own bindings
at the dispatch seam (BL-M33's missing conductor↔host seam is the common root of all three).
