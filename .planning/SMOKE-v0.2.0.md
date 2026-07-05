# v0.2.0 POST-SHIP SMOKE REPORT — 2026-07-04 (adval-style, per HANDOFF §7)

Judged at anchor (Fable). All artifacts referenced live in this scratchpad or the repo.

## SMOKE-1 (read-path) — PASS, one protocol finding

- `git describe` = v0.2.0-4-g8caabc7 on clean master (the 4 = docs PRs #9/#10 only).
- pytest: **2505 passed / 3 skipped** (75s, 2 deselected integration). Validator: **48 / 0 / 0**.
- Ledger: 4 rows parse; `failure_kinds_of` per-version correct (v1→empty; row 4's test-regression intact).
- **FINDING F5 (stale protocol expectation):** HANDOFF §7 expects `class_median` → None at min_samples=5.
  Actual: **8.35 — CORRECT.** Non-calibration rows 2+3 hold SIX code durations (≥5); 8.35 = median of
  [3.6,4.5,7.2,9.5,11.1,15.8]; all-rows median would be 3.8, proving calibration exclusion HOLDS.
  Mechanism right, expectation miscounted. FIX: amend HANDOFF §7 line in this session's docs pass.

## SMOKE-2 (prose-executability) — **PASS. Gap-audit items 3 and 4 CLOSED.**

Fresh-context conductor (Opus 4.8, author-blind, given ONLY verbatim SKILL.md 0.8.0 extractions
[32–38, 63–83, 537–696, 697–778] + seeded target repo). Full setup: smoke2-prep-report.md; full
conductor report: session transcript (task ac23…/output).

From shipped prose alone it: resolved `inlineEval:"on"` from kata.config via precondition-0; scanned
`ec28e0e` and parsed the trailer; scored **0.60 > τ 0.50 strict** (verify_fail only; lane_drift false via
footprint; slack null with no board); entered the ladder; **dispatched kata-inline-eval BY SKILL FILE**
(first time ever — gap 3 closed) as fresh-context/no-write; **resolved the eval tier correctly through the
never-anchor gauntlet** (anchor sentinel "session"→opus; economy −2 standard → haiku; explicit ID passed,
never OMIT; fallback chain noted) — the 4×-resurfaced defect class, navigated clean by a fresh reader;
received verdict `reroll`; executed A1-Q1's reroll leg exactly (kill evidence-backed; anchor = dispatch
base 9daab34 since no below-τ checkpoint existed; new branch `task/T-F-attempt1` named in the DECISION;
corrective brief staged as NOTE; worktree prune; CLAIM-liveness per L19 MED-2); wrote the @sha ladder
DECISION line to `.kata/board.md`.

### Findings (none block; all feed the loop)
- **F1 — verdict variance by evaluator tier:** live proof (sonnet) said `correct` on the same defect
  flavor; haiku said `reroll`. Both legal ladder outcomes; cost profile differs (reroll discards the
  chunk). GRILL ITEM: pin the evaluator verdict tier, or add verdict-calibration guidance to the
  inline-eval prose; ledger should eventually carry verdict×tier for calibration.
- **F2 — prose gap, index continuity at dispatch-base anchor:** SKILL.md L194–197 defines continuity
  only off "the anchor checkpoint's i" (⇒ k+1). When reroll anchors at the DISPATCH BASE (no checkpoint),
  the text is silent; conductor correctly inferred `--index 0`. One-sentence prose hardening: "anchor =
  dispatch base ⇒ fresh session's first trailer is --index 0."
- **F3 — scope boundary honored:** rebuild-worker dispatch (§ The loop) was outside the extraction;
  conductor staged the brief and named the boundary instead of improvising. Full-loop leg exercises on
  the first real on-run.
- **F4 — seeding minimalism:** no PLAN frontmatter in micro repo; class/footprint taken from handoff.
  Didn't affect the verdict (0.60 hard signal alone). Note for future smoke seeds.

## SMOKE-3 (efficiency BASELINE — the pre-fix A/B arm)

| Metric | Value | Notes |
|---|---|---|
| Conductor tokens per task gated | **94,489** | Opus; one full ladder cycle (scan→score→eval dispatch→reroll adjudication+records); includes its haiku eval child |
| Conductor tool calls | 25 | |
| Wall clock | 472s | |
| Main-session ingestion for whole smoke | 3 contract reports (~15+10+30 lines) | prep ×2 + conductor final; no raw transcripts ingested |

Methodology caveats, recorded honestly: (a) the smoke conductor already ran under a ≤30-line
final-report contract imposed by dispatch — the M4 incident's unbounded-prose reports are NOT
reproduced here; the post-fix A/B must re-run THIS identical protocol so the delta isolates the shipped
fix, not the dispatch prompt. (b) child-eval tokens are inside the conductor number (harness reports
spawn-inclusive). PASS bar for the post-fix rerun: conductor tokens/task-gated and main-session
ingestion DROP (or hold) with IDENTICAL ladder outcomes (same trigger, same A1-Q1 conformance).

## Session scope riders (operator-directed, this session)
- No PokeVault/MindBridge deploy. Fable stays in matrix behind a once-per-run bootstrap approval gate
  (decline ⇒ Opus). Preflight approval bundle (installs, allowlist, Fable gate, compact-window
  recommendation) collected once pre-run. Internal-threshold-primary context architecture (host knob =
  backstop only). Bootstrap force-runs first time post-install + persists settings (YAML/JSON).
