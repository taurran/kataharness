---
date: 2026-06-21
spec: subagent-dashboard
status: SHIPPED — v0.1.0-alpha.2. Phase 4 self-dogfood of the complete Greater Loop.
tags: [report, dogfood, greater-loop, phase-4, subagent-dashboard, shipped]
---

# REPORT — subagent-dashboard + the first complete-Greater-Loop dogfood

**The headline:** the entire Greater Loop ran end-to-end on KataHarness itself, for the first time, and shipped a
real feature. `kata-initiate → orchestrated harness → kata-closeout → human version-select`. Tag `v0.1.0-alpha.2`.

## What shipped
- `tools/kata_dash_model.py` — pure parser (`board.md` + `state.json` → `ViewModel`); 50 tests, no `rich`.
- `tools/kata_dash.py` — `rich` live TUI: artistic ASCII worker rows (`▰▱`), braille spinners (`⠹⠼⠧⠿`), the
  `KATAHARNESS ⛩ 道` frame, the `GRILL▸…▸IMPROVE` loop ribbon, board+drift footer; tails `.kata/` in a side
  terminal (`! python tools/kata_dash.py`). 43 tests. Stepped bars from task state (v1).
- `rich>=15.0.0` dep; docs `INTENT/PLAN/SECURITY/REPORT.md` + `.kata/understand.md`.

## The run (each stage actually happened)
1. **INITIATION** — `kata-initiate` froze `INTENT.md` (version-up, target=self) + a v1 DESIGN/PLAN; `rich` de-risked.
2. **HARNESS** — 2 Sonnet workers in isolated worktrees (DASH-model ∥ DASH-render) → zero-conflict octopus-merge →
   integration gate → `gate_emit` emitted `.kata/RESULT.json` (F1 dogfooded again) → fresh-context `kata-evaluate`
   **PASS 8/8** (205 tests, validator 35/0).
3. **CLOSEOUT** — `kata-understand` wrote a graph-backed `.kata/understand.md` (F2 mapped 107 dashboard symbols,
   tree-sitter); human version-select → **ship: merge + push + tag `v0.1.0-alpha.2`**.

## What the dogfood surfaced (the point of the exercise)
- **A real bug, caught by the gate:** the dashboard crashed with `UnicodeEncodeError` on the `⛩` glyph on a
  non-UTF-8 Windows stdout (piped/redirected/cp1252). The integration **smoke test** caught it; fixed with
  `sys.stdout.reconfigure(utf-8, replace)` + `Console(legacy_windows=False)` **before** evaluation. This is the
  loop doing its job — the gate caught what unit tests didn't.
- **Honest deferrals (logged, not hidden):** v2 smooth bars need worker progress-heartbeats (a small `board.md`
  addition); v3 cross-host unification pairs with multi-model; nothing yet auto-launches `kata_dash` alongside a
  run (manual second terminal today — candidate for a future orchestrate convenience hook).
- **Security:** 2 new Low CWE-23 on `--kata-dir` = documented FPs (operator CLI arg, read-only non-shipped tool,
  `..`-guard present) — same disposition as Phase 0 (`SECURITY.md`).

## Loop health verdict
The complete Greater Loop is now **proven end-to-end**, not just built: initiation froze a real intent, the
orchestrated harness built it with concurrent workers, the gate caught the one genuine defect, the understand-map
was graph-backed, and the human held the version-select. The adversarial-review seam fixes (D87–D91 follow-ups)
paid off — initiation/closeout/understand/loop composed without the seam breaks the red-team had flagged.

## Next candidates (not committed)
- Phase 5 external reach: install-portability mechanics · multi-model-orchestration.
- Dashboard v2 (progress heartbeats) + the auto-launch wire-in, if the live view proves useful in practice.
