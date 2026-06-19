# D16 metric sheet (v2, post-pilot) — one row per run (18: 3 projects × 2 arms × 3)

Pre-registered v2 metrics. **No metric added or changed after the first counted run.** v1's self-judged
`first_pass_green` was dropped (unmeasurable post-hoc — see PILOT-NOTES.md).

## Objective metrics (experimenter-measured, Opus side — PRIMARY)
| field | meaning |
|---|---|
| **gate_pass** | held-out `pytest` all-pass ∧ `ruff check .` clean on the **delivered** build — yes/no |
| **gate_fail_count** | # held-out gate cases failing on the delivered build (0 if gate_pass) |

## Self-reported metrics (precise, identical definitions both arms — SECONDARY)
| field | meaning |
|---|---|
| **drift_events** | build actions that deviated from the **frozen functional plan**. A lint/style auto-fix is **NOT** drift. |
| **replans** | revisions to the frozen plan after freeze |
| **escalations** | escalations raised during the run |
| **interventions** | times a human was genuinely needed (the run had to stop) |
| **eval_defects** | NEEDS_WORK items found by the arm's own evaluate/review |
| **fix_iterations** | count of `failing test or lint → fix` cycles before the build first reached all-green |

## Covariates (not part of the verdict)
`tokens`, `tool_uses`, `wall_min`, `files`, `self_tests`.

## Per-run record key
`run_id = <project>-<arm>-<n>` (e.g. `01cli-A-2`); `project ∈ {01cli,02api,03expr}`; `arm ∈ {A,B}`; `n ∈ 1..3`.
Plus `kata_review_verdict` (SHIP/HOLD + one-line plan-quality note, arm-blind where feasible).

## Aggregation + verdict (v2, pre-registered)
Per project, per arm: **planning-cost = Σ(drift_events + replans + interventions + fix_iterations)** across the
3 runs; and **gate_pass rate** (/3).

| project | A planning-cost | B planning-cost | A gate_pass | B gate_pass | A < B planning-cost? |
|---|---|---|---|---|---|
| 01cli |  |  |  /3 |  /3 |  |
| 02api |  |  |  /3 |  /3 |  |
| 03expr |  |  |  /3 |  /3 |  |

**Verdict rule (PRE-REGISTERED v2):** the grill differentiates IFF Arm A has **lower planning-cost on ≥2/3
projects** AND Arm A's gate_pass rate ≥ Arm B's overall. Tie/worse → grill **not yet proven** → iterate the
grill (do not ship v0.1). Record verdict + write **L11**; adversarial `kata-review` (D15) on the conclusion.
