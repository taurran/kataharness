---
date: 2026-06-19
spec: dogfood-selfup-1
kind: kata-report (v1, one-page)
tags: [report, dogfood, version-up]
---

# Report — Dogfood #1: self version-up (`allowed-tools` enforcement)

**Unit / goal.** Version-up KataHarness on itself: turn the prose-only `allowed-tools` conformance rule into an
enforced structural check — and stress-test the loop's evaluation depth.

**Gate result.** PASS. `pytest` **40 passed** (was 38; +2 seams) · validator **31 skills / 0 errors** · Snyk
(prior tools scan) 0. Fresh-context default-FAIL evaluator: **PASS**, with a recorded mutation proof.

**What shipped (footprint — validator/docs/tests only; no skill touched).**
- `tools/validate_skills.py` — `allowed-tools` added to `REQUIRED_KEYS`; new `check_allowed_tools` (non-empty
  list of strings).
- `tools/tests/test_validate_skills.py` — +2 seams (bad-fixture errors; real tree all well-formed).
- `tools/tests/fixtures/bad-tools/...` (new) + `good`, `bad-name`, `bad-cost`, `bad-link`, `bad-tier`,
  `good-tier` fixtures gain a valid `allowed-tools` (isolation hygiene).
- `docs/STANDARDS.md` — `allowed-tools` OPTIONAL → REQUIRED.

**Drift ledger.** 0 unauthorized deviations · 1 readiness override (tree-sitter BLOCK bypassed — footprint needs
no graph, recorded as finding R1) · 1 hygiene fix applied (fixture isolation) · 0 human interventions during build.

**Open items / findings.**
- **R1** version-up's tree-sitter BLOCK is too coarse (blocks graph-irrelevant changes) → backlog.
- **R2** loop driven manually (no automated orchestrate/install) → confirms install + multi-model briefs.
- **Headline:** the end-of-run writeup is **not yet self-sufficient** for in-depth evaluation — needs a
  self-emitted `RESULT.json` (verbatim gate output + exit codes + SHAs), a footprint manifest, and a recorded
  mutation proof. → next `kata-improve` cycle (see RUN.md §IMPROVE).
