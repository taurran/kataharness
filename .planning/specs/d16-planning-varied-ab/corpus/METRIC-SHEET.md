# D16 metric sheet — one row per run (18 rows: 3 projects × 2 arms × 3)

Pre-registered metrics (DESIGN §3). Fill exactly; **no metric added or changed after the first run.**

## Per-run record
| field | meaning |
|---|---|
| `run_id` | `<project>-<arm>-<n>` e.g. `01cli-A-2` |
| `project` | 01cli / 02api / 03expr |
| `arm` | A (kata-grill→design→plan) / B (GSD) |
| `n` | 1..3 |
| **(a) drift_events** | count of build actions that deviated from the frozen plan (scope creep, off-plan files) |
| **(b) escalations** | count of escalations raised during execution |
| **(c) interventions** | count of human interventions required to proceed |
| **(d) replans** | count of re-planning events after freeze |
| **(e) first_pass_green** | `pytest` ∧ `ruff` both pass on the **first** delivered build — yes/no |
| **(f) eval_defects** | defects caught at `kata-evaluate` (NEEDS_WORK items) |
| **(g) rework_commits** | commits whose sole purpose was fixing the arm's own prior output |
| `kata_review_verdict` | SHIP / HOLD + a one-line plan-quality note (arm-blind where feasible) |
| _cov_ `tokens` | total tokens (covariate, not verdict) |
| _cov_ `wall_min` | wall-clock minutes (covariate) |
| notes | anything notable (free text) |

## Aggregation (for the verdict, DESIGN §4)
Per project, sum (a)+(c)+(d) for each arm and compare; tally first-pass-green rate per arm.

| project | A: drift+intv+replan | B: drift+intv+replan | A first-pass-green | B first-pass-green | A<B on (a+c+d)? |
|---|---|---|---|---|---|
| 01cli |  |  |  /3 |  /3 |  |
| 02api |  |  |  /3 |  /3 |  |
| 03expr |  |  |  /3 |  /3 |  |

**Verdict (pre-registered rule):** grill differentiates IFF Arm A has materially fewer (drift+interventions+
replans) on **≥2/3 projects** AND Arm A first-pass-green rate ≥ Arm B. Tie/worse → grill not yet proven →
iterate (do not ship v0.1). Record the computed verdict + write **L11**.
