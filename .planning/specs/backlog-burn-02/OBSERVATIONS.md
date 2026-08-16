---
spec: backlog-burn-02
kind: mode-design evidence (burn round 2)
opened: 2026-08-16
purpose: evidence for Burn mode (BL-N12) — second live data point, first under the BBM-1..11 rules
---

# OBSERVATIONS — backlog burn #2 (the five ≤1-file fixes)

**What is different from round 1, by design:** hybrid gating from the start (BBM-1: builder
self-gates + fresh-context judges + one conductor spot-audit) · worktrees provisioned OUTSIDE the
repo root at a conductor-pinned SHA (BBM-9 + the HIGH-2 contamination mitigation) · triage +
convergence review BEFORE freeze (BBM-7/8) · `waveBoundaries: autonomous` declared up front
(BBM-11).

## Pre-dispatch record

| fact | value |
|---|---|
| frozen plan | `PLAN.md` beside this file, `status: frozen` at commit `c2be1159ca1aedaf4e39c135b55f0e7f35f39998` |
| **baseSHA (MED-5 durable record)** | `c2be1159ca1aedaf4e39c135b55f0e7f35f39998` (= the freeze commit; all four wave-1 worktrees provisioned at it) |
| worktrees | `C:/dev/projects/kh-burn02-{x01,x02,x03,x07}` on branches `task/burn02-<item>` — conductor-verified post-provision: all four at `c2be115`, clean |
| convergence | CONVERGE-HOLD (4 HIGH / 5 MED / 4 LOW) → all resolved in the frozen revision; the review corrected the conductor's OWN triage claim (H3 class: "only quality has provider tags" was wrong — twelve provider tags exist) |
| mode evidence already | BBM-8 vindicated a THIRD time: 3 of 4 HIGH findings were in the shared half or shared claims; one was an H5 unsatisfiable pair (X03 proof-vs-clean) and one an H5 pair inside an item spec (X07 wrong gate primitives — the conductor's fix-wording itself was the defect) |

## Running log

*(appended as the burn proceeds)*

| when | item | event | note |
|---|---|---|---|
| pre-flight | all | triage re-verified all five filings live | first burn where NO item changed materially at triage (contrast H2's 2-of-6) — though the conductor's supporting claim on X01 was wrong in the other direction |
| freeze | plan | convergence HOLD → fixed → frozen `c2be115` | wall-clock ~9 min for the review (fresh-context judge, ~115k subagent tokens) |
| wave 1 | x01·x02·x03·x07 | dispatched concurrently, 4 pinned worktrees | briefs carry step-0 verification + push-back |
