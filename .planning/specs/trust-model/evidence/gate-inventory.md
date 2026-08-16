---
spec: trust-model
artifact: evidence dossier 4/4 — gate & judge-stack inventory
date: 2026-08-16
provenance: read-only survey agent, committed verbatim-in-substance by the conductor; spot-verified
  by class — re-verify any single row before it becomes load-bearing in a DESIGN
baseline: grill/dispatch-seam @ fea7ccb (master de8578c)
---

# Evidence 4 — every completion gate + the judge stack + plan-grounding current state

**SEAM** = the gate already requires a durable artifact a truth-serum precondition could hang off;
**NEW** = a precondition would need a new artifact.

## A. Gate inventory (condensed to the design-shaping rows; the full sweep covered ~40 gates)

### Pre-dispatch / freeze

| Gate | Judge | Machine evidence today | Accepted on faith | Seam |
|---|---|---|---|---|
| Config load-guard (`kata-orchestrate:38-124`) | code (5 validators) | full — when it runs (it never runs; promise-audit rows 62-66) | — | SEAM `kata.config` |
| PRE-FLIGHT (`:126-141`) | code + operator acceptance | `kata.dependencies.json` + `.kata/preflight.json` | "recorded acceptance" for degraded has no schema'd location | SEAM |
| Green-at-fork-point (`:144`) | conductor prose | **none — no artifact named** | that it ran | **NEW** |
| Disjoint ownership partition (`:145-146`) | conductor prose | none (`footprint.partition` exists, uninvoked here) | the reading | **NEW** |
| Contract-edge freeze checks (`:159-189`) | code | three engine calls | the plan-committed check has no artifact | SEAM |
| DESIGN author verdict (`kata-design-doc:82-86`) | author self-reports; `normalize()` shape-validates | shape only | **the author's own verdict + own deviations list** | SEAM (the DESIGN file) |
| Authored-artifact six-row rubric (`authored-artifact-gate.md`) | conductor mixed | rows 1/3-existence/4-detection "could be scripted" — **none is scripted today** | rows 2/3-support/5/6 declared judgment | SEAM |
| Grill-ledger-passed-convergence precondition (`kata-design-doc:33-35`) | conductor reading a prior verdict | **none — SHIP verdicts are conversational** | that a pass ran and SHIPped | **NEW** |
| `assert_frozen` chokepoint (`kata_dispatch:76`) | code | full | **nothing runs it** | SEAM (dormant) |

### Grill convergence

Self-assessed 5-box criteria: no evidence, named self-bias. Tier backstops (kata-review
SHIP): **no artifact records that a pass ran, that context was fresh, or (Advanced) that two
distinct passes ran.** Only the `EV-{n} · LOCKED` ELEVATE entry has a machine-parseable anchor.

### Per-task execution

| Gate | Machine evidence | On faith | Seam |
|---|---|---|---|
| Worker self-gate (kata-tdd verify + mutation) | `prove_non_vacuous` is a real sandboxed runner | worker decides when to run; reports verdicts with its DONE; nothing forces the run | SEAM `.kata/mutation.json` |
| Checkpoint trailer | full — "mechanical verify outputs only, never a self-assessment" (the D33 boundary at `kata-tdd:160`) | that one was emitted at all | SEAM trailer |
| Orchestrator task gate (`:485-489`) | lane check mechanical (`footprint.changed_in_task` → `is_within_footprint`) | **the verify re-run is prose; no per-task artifact is emitted** (telemetry is detection-only, never blocks) | SEAM footprint/telemetry; **NEW** per-task RESULT |
| IaC Tier-1/Tier-2 | strong — fail-closed scanner + state machine + artifacts | 8-smell lens is prose | SEAM |
| Provider surface re-verify | full (git-durable Supersede trailers) | — | SEAM |
| Integration re-gate per merge | none emitted | that it ran | **NEW** |
| Wave "gate" | — | **there is no wave gate** — waves are a derived view (`:322-324`) | **NEW** if wanted (BBM-12 wants it) |

### In-flight (M4)

Checkpoint trigger: full (trailer + `should_trigger`), zero-LLM happy path. Inline-eval verdict:
inputs mandate "trust the diff, not the worker"; **its own fresh context is unverified while it
holds kill authority at economy tier** (the skill names this itself). Ladder DECISION lines are
the only durable trace.

### Final gate (the load-bearing rows)

| Step | Machine evidence | Accepted on faith | Seam |
|---|---|---|---|
| RESULT.json emit (`gate_emit`) | full schema incl. baselineSha/resultSha | **mutation records are a worker-reported union — "take their union"; the conductor does not re-run them** (`:1375-1379`) | SEAM — the canonical artifact |
| Contract-edge final gate | full; absence-is-the-signal | "sentinel-absence ≠ implemented — structure only" (`:1422`); producer has zero production callers (T8) | SEAM |
| **kata-evaluate PASS/NEEDS_WORK** | substantial mandated inputs (RESULT/mutation/footprint/iac/contract-gate, absent⇒NEEDS_WORK) | freshness unverified; rubric items 3/5/6/7/8 prose; **RESULT freshness not checked — `evidence_is_current` exists and is never called here (BL-X11)**; **the verdict itself is conversational output, never persisted** | SEAM + the dormant identity check |
| kata-slop-check | none — all greps/heuristics | entire verdict; silent no-op without the module | checks are **NEW** |
| Fix loop / thrash budget | footprint intersection mechanical | cited-files set extracted from prose findings; counters in-context, recount from DECISION lines | SEAM board |
| **kata-review SHIP/HOLD** | **none required** — surface 6 asks regenerate-and-diff but nothing captures whether it happened | whole verdict | SEAM artifacts; **NEW** proof-it-ran |
| Validation-miss emit / recurrence | real code, observe-only by contract | — | SEAM jsonl |
| Telemetry ledger row | schema v2, human-gated commit | zero rows ever produced (T9) | SEAM (dormant) |
| Benchmark floor gate | **full — and the ONE place `evidence_is_current` is enforced** (`benchmark.py:387`) | reports never gate (frozen invariant) | SEAM |

### Sprint / closeout / meta

- Sprint stop-gate consumes the kata-evaluate verdict "never re-computed here" — **as a value,
  with no artifact identity check** (and the verdict is undurable, cursor-dossier).
- G1 approval "never inferred from state"; its auto-continue exception has four AND-conjuncts with
  no named artifact source. G2/G4 pure judgment, no artifacts.
- Closeout reads the RESULT verdict **verbatim, not re-derived**; backout anchored on
  `baselineSha` (tier-3); the never-auto-push rule is confessed **behavioral** ("Bash cannot be
  restricted to specific git subcommands").
- **kata-validate `Report.passed`**: verdict math fully mechanical over `findings.json`; findings
  are LLM output. **Its tripwire self-check (`assert_tripwire_flagged` over a known-bad corpus) is
  the only meta-gate in the harness — the one place a judge must prove it can still fail.**
- kata-promote two-stage gate: stage-1 grounding verdict recorded in `state.json.candidates[]` —
  never written in a live run (T10).
- The gauntlet: fully mechanical, deterministic, first-non-zero-exit honest — **the strongest
  existing precedent**, but it governs the harness repo's dev loop, not the dispatched loop, and
  has no notion of a run.

## B. Judge stack — inputs, independence, verify-vs-assess duties

| Judge | Independently derived | Worker-self-reported | Named holes |
|---|---|---|---|
| kata-evaluate | own green-gate re-run ("run it yourself, paste the numbers"); IaC re-derivation; contract-gate companion arrays | `.kata/mutation.json` union; DONE counts; ASSUMPTIONS entries | freshness unverified; item-9 build-and-run leg deferred to a gate its own citation says is unbuilt; no `evidence_is_current` call |
| kata-review | regenerate-derived-artifacts-and-diff; whole-flow produced↔consumed trace; D136 raise-confirmation; injected-knowledge open-the-source | everything the build asserts about itself | no-write caveat; verdict not tier-portable (recorded); nothing captures whether the regenerate duty ran |
| kata-slop-check | nothing — all read/assess heuristics | all inputs | silent no-op without module tag |
| kata-inline-eval | reads the diff itself; trailer is mechanically derived | — | own freshness unverified while holding kill authority |
| kata-validate critics | deterministic-first cascade (grounding math, severity mapping, tripwire, grep signals) before LLM legs | findings are LLM output | cross-family anti-collusion only when roles configured; honest weaker-fallback statement mandated |
| challenger (practice, not built) | **executes the session's own tooling against its own artifacts** — found the only live wrong-output defect (BL-X12) after two validators + two convergence rounds audited as prose; refuted 2 of 3 HIGH framings (validators over-grade) | — | AC-10/11 design rules recorded; roster row 9 verdict schema CONFIRMED/REFUTED/RESCOPED |
| report-only (debrief, benchmark-report, understand, report) | quote-verbatim-never-recompute discipline | — | correctly never gate |

## C. Plan-grounding current state — what compares outcome to the frozen plan at close

| Mechanism | Mechanical or prose | Plan-item → artifact mapping produced |
|---|---|---|
| kata-evaluate item 1 (acceptance criteria) | hybrid — codeBearing keyed off footprint; criterion satisfaction is prose | **none** — no per-criterion table; the verdict is conversational (kata-debrief must say "verdict pending") |
| kata-closeout goal-anchored report | prose — groups the diff by "goal-aspect", a category invented at compose time; the cited `RESULT.json` "goal-aspect breakdown (if present)" is produced by nothing | goal-aspect → prose paragraph, not item → artifact |
| kata-understand | hybrid (graph-backed, degrades to git/diff map) | what-changed map, not promised-vs-built |
| DEFERRED/ASSUMPTIONS surfacing | prose grading of a real artifact (rubric item 8) | assumption → contradiction-verdict; **no mapping from a deferral back to its plan item; nothing detects an UNRECORDED gap** |
| Drift ledger | three integer counters in a schema never written | none |
| BBM-6 accuracy record | designed mechanical, executed by hand (zero telemetry rows; hand-tallied) | the one real item→outcome table exists at `specs/backlog-burn-02/OBSERVATIONS.md:118-140` — **authored by hand** |
| Plan-grounding as a step | **does not exist** | — |

**The decisive seed:** `Kata-Task:` trailers already map every integration commit back to its plan
task, and `parse_plan_tasks` already yields the authoritative plan task set — **nothing joins the
two sets at close.** The operator's plan-grounding step is, at its mechanical core, one
set-difference over data that already exists (plus the DEFERRED leg to make absences legal or
named drift).
