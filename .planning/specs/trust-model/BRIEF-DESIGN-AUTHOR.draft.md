---
spec: trust-model
artifact: "DRAFT dispatch brief — design-author (KH-T13 role). NON-BINDING until the grill closes;
  dispatched only after convergence pass 2 SHIPs + ELEVATE records. Prepared in parallel per
  operator direction 2026-08-16."
status: draft
---

# DRAFT — design-author brief: compile the Trust Model DESIGN

## Role + posture
- Role: `design-author` (dispatched worker, `sandbox="write"`, own worktree — never authored in
  the conductor's context, `protocol/orchestration.md`).
- Mint note (R-H1): this dispatch is pre-freeze by definition — the record's `governs` field
  points at the CONVERGED GRILL LEDGER, not a plan. (Until the seam is built, the dispatch is
  prose-era; the brief records that honestly — Guardian: Honor-system dispatch, stated.)

## Objective
Compile `.planning/specs/trust-model/GRILL-LEDGER.md` — 24 LOCKED branches (TM-A1..A3, B1..B5,
C1..C7, D1..D5, E1..E2, F1..F2, G1..G3, H1..H4) **with the 18 R-\* amendments applied as
binding** — into `DESIGN.md`: one specific, testable, freeze-ready contract.

## Inputs (read in this order)
1. The GRILL-LEDGER in full (branches + amendments + the security register TM-H4 + both
   convergence verdicts).
2. `DETAILED-PASS.md` (the seven-component program + eight discoveries) and `ASSESSMENT.md`
   (T1–T18).
3. `evidence/` — all six dossiers (promise-audit, cursor-dossier, detectability, gate-inventory,
   cursor-alignment-study, fanout-survey) + `../dispatch-seam/SURFACE-MAP.md`.
4. Standing rulings the DESIGN must not contradict: D81, D135, D169, D172, D134, BBM-11/12,
   EDR-7, thin-orchestrator, the Determinism Doctrine (all engine code under its ten laws — D172
   makes the loop's seams a doctrine surface).

## The DESIGN must contain (checklist — every row maps to locked branches)
- The seam: engine API (mint/dispatch/capture), per-role required-field table incl. `governs`
  (R-H1), record schema + single-use/expiry semantics (R-M1, R-L4), role vocabulary extension
  (R-M5), deny-and-route + park semantics (TM-B5), per-host interception capability + loud
  degrade table (TM-B2, R-M7 honest residual on the Bash leg).
- The cursor: ONE grammar migration BNF (R-M3 — seq, parent-seq, TYPE enumeration PHASE/VERDICT/
  SPAWN/DOWN/DENY, run-header block), seam-authored writer classes (R-M2), snapshot cadence +
  derived resilience levels (TM-C3, R-M4), run-membership law verbatim (R-H2), tree-of-runs +
  arm registry + parent-close policies + reducers (TM-C7), projections + provenance tagging
  (TM-C6).
- Truth Serum v1: detector specs per class with anti-vacuity companions (TM-D2/D3), the
  hardened deferral schema + protocol/deferral.md contract text (TM-D1), gate-precondition map
  over the ~40-gate inventory with the NEW artifacts (TM-D4, R-M6 per-judge activation),
  evidence-identity wiring list (TM-D5).
- Grounding: agent charter + stack-head placement + trigger table + the mutation re-run seam
  (TM-E1/E2, R-M10).
- The close: three-way join + evidence: PLAN field (TM-F1, R-M9), fail-closed close verdicts +
  re-loop routing (TM-F2), provenance drift check incl. tree semantics (TM-A2, R-M8).
- Presentation: the four surfaces + rendering law + Guardian scale usage (TM-G1..G3, TM-A1);
  UX sequencing per R-H4 (combined round-3 before the operator freeze; non-UX build unblocked).
- Migration + activation order (TM-H1 incl. R-M9's plan-schema scope), degradation honesty
  (TM-H2), the security register as design constraints (TM-H4), backlog mapping with v1-scope
  statement (TM-H3, R-L3).
- **Honest-residual section** (EDR-5 house style): adversarial-conductor detection-not-
  prevention, entry residual, validator-source meta-layer, Bash-leg partial verification,
  detector humility (burn-02 meta-finding verbatim).

## Output contract
Two-part (kata_dispatch normalize shape): write `DESIGN.md` at the brief's owned path; final
message `{designPath, verdict: ready|needs-rework, deviations: []}` — every deviation from a
locked branch is a listed deviation, never silent (PD-1/PD-2).

## Gate (conductor-side, recorded here so the author knows the bar)
The authored-artifact six-row rubric (`protocol/authored-artifact-gate.md`) + a diff against
every LOCKED branch id — a DESIGN row with no ledger anchor is drift; a ledger branch with no
DESIGN row is an omission (registry-vs-tree, both directions).
