---
date: 2026-06-21 (v0.1.0-alpha.2 SHIPPED — Greater Loop proven end-to-end via Phase 4 self-dogfood; next = Phase 5 external; for a fresh/compacted session)
branch: master — on private remote github.com/taurran/kataharness (pushed), tip 3ed18d3
green: validator 35 skills / 0 errors · pytest 205 passed · Snyk residual-CWE23-FP-documented · tags pre-phase0..3 + pre-dash + v0.1.0-alpha.1 + v0.1.0-alpha.2
tags: [handoff, v0.1.0-alpha.2, greater-loop-PROVEN, phase4-dogfood-done, next-phase5-external, full-context]
authored-for: kata-orient (sections map to the three orientation tiers)
---

# HANDOFF — KataHarness — 2026-06-21 (v0.1.0-alpha.2 SHIPPED · Greater Loop proven end-to-end · next = Phase 5 external)

> **Fresh/compacted session: read in order, confirm green, resume at §4.** Everything below is durable +
> committed + **pushed to the private remote**. Maps to `kata-orient` tiers: §1 → context · §2+§4 → volatile ·
> §6 → human-required.

## 1. Read-in order  *(orientation: CONTEXT)*
1. `AGENTS.md` · 2. `docs/DESIGN.md` · 3. `docs/STANDARDS.md` (§1 frontmatter — `allowed-tools` is now REQUIRED) ·
4. `.planning/STATE.md` (CURRENT box) · 5. **`.planning/DECISIONS.md` — D70–D90 (D87–D90 = the Greater Loop)** ·
6. `.planning/LESSONS-LEARNED.md` (L11) · 7. **`.planning/specs/greater-loop/{DESIGN,ROADMAP,GRILL-LEDGER}.md`
   ← THE FROZEN BUILD** · 8. **`.planning/STEERING.md` — the active BUILD-THROUGH directive** · 9. the four BRIEFs
   `.planning/specs/{install-portability,multi-model-orchestration,testing-model,subagent-dashboard}/BRIEF.md`.
⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated, harness-injected).

## 2. State *(orientation: VOLATILE)*
- Branch `master`, **pushed to private remote** `github.com/taurran/kataharness`, tree clean, tip `f39f37b`.
  **35 skills / 0 errors · pytest 112** · Snyk: residual CWE-23 documented FP. Confirm:
  `cd tools && uv run pytest -q  &&  uv run python validate_skills.py`.
- **✅ GREATER-LOOP BUILD COMPLETE — Phases 0–3 all built, fresh-context-eval PASS (8/8 each), merged, pushed:**
  - **P0 FOUNDATIONS** (`9e1b27c`): `tools/gate_emit.py` (F1 — eval artifacts into the live gate, dogfood-2
    residual closed) + `tools/graph_gen.py` (F2 — tree-sitter `kata.graph.json` runtime).
  - **P1 INITIATION** (`157804f`): `modules/initiation/` + `kata-initiate` + `protocol/intent.md` (D91 self-contained
    modules; validator discovers `modules/*/*/SKILL.md`).
  - **P2 CLOSEOUT** (`20dac30`): `modules/closeout/` + `kata-closeout` (never gates) + `kata-understand` (graph-backed).
  - **P3 CONDUCTOR** (`f39f37b`): `kata-loop` (sequences initiation→harness→closeout + context-carrying loop-back).
  Plans `specs/greater-loop/PLAN-phase{0,1,2,3}.md`; decisions **D87–D91**.
- **Backout safety:** tags `pre-phase0..pre-phase3` + `pre-dogfood-2` + `v0.1.0-alpha.1` on remote. Policy A.

## 3. What shipped this session *(orientation: CONTEXT)*
- **sprint-cadence BUILT + SHIP** (D78–D86): `kata-sprint` (G1–G4 boundary), `kata-report` v1, `kata-plan`
  roadmap layer, `delivery` axis; `kata-bootstrap` = boundary router (D86).
- **GitHub repo created (private) + everything pushed.** README repositioned around **control + the mode
  spectrum**.
- **Dogfood #1** (GATE PASS): enforce `allowed-tools`. **Dogfood #2 — the REAL orchestrated run** → released
  **`v0.1.0-alpha.1`**: "evaluation self-sufficiency" by **4 concurrent worker subagents in worktrees**,
  zero-conflict merge, fresh-context eval PASS, human version-select. Added `tools/{run_result,footprint,
  mutation_check}.py` + `kata-tdd` mutation step + report/evaluate artifact contracts (pytest 40→72).
  **Residual: those eval artifacts are built but NOT wired into a live gate → Phase 0 / F1.**
- **Greater Loop DESIGN FROZEN** (3-round interactive grill → D87–D90). Four briefs aligned. **BUILD-THROUGH
  directive set.** (See §4.)

## 4. THE PLAN — Greater Loop BUILT (Phases 0–3); next = the self-dogfood TEST *(orientation: VOLATILE — the immediate action)*
> **✅ DONE this session:** the whole Greater Loop was built through Phases 0–3 (see §2) as real orchestrated
> runs with fresh-context evaluation each phase. The BUILD-THROUGH directive is satisfied. **The single
> remaining event is Phase 4 — the self-dogfood test — which the operator drives (NEXT ACTION below).**

**The Greater Loop** (FROZEN, D87–D90) wraps the harness: **INITIATION** (`kata-initiate` + frozen `INTENT.md` +
interactive target/platform/vault config — install-portability config layer folds in) → **HARNESS** (reused) →
**CLOSEOUT** (`kata-closeout` + `kata-understand` map, opt-in/graph-backed), sequenced by a thin **`kata-loop`**
conductor with a **context-carrying loop-back**. Modules = `modules/<name>/` dirs each with own `AGENTS.md`
(nested-rollup). testing-model folded into F1; execution UX = **foreground-parallel** + `subagent-dashboard`
(build-later).

**★ BUILD-THROUGH directive (operator, in `STEERING.md` + ROADMAP):** build **all of Phases 0–3 continuously —
NO intermediate dogfood/test ceremony.** Per-phase correctness gates (validator green · pytest · Snyk ·
fresh-context `kata-review` before each merge) **still apply** — they're build discipline, not "the test." **The
single next TEST = Phase 4 self-dogfood of the COMPLETE loop.**

**✅ Phase 4 self-dogfood DONE — `v0.1.0-alpha.2` shipped.** The complete Greater Loop ran end-to-end on
KataHarness itself and shipped the **subagent-dashboard** (`tools/kata_dash.py` + `kata_dash_model.py`):
`kata-initiate` → orchestrated harness (2 workers/worktrees, `gate_emit` RESULT.json, fresh-context `kata-evaluate`
PASS 8/8) → `kata-closeout` (graph-backed `.kata/understand.md`, human version-select). The dogfood caught + fixed
a real Windows UTF-8 render crash via the smoke test. Record: `specs/subagent-dashboard/{INTENT,PLAN,SECURITY,REPORT}.md`.
pytest 205, validator 35/0.

**NEXT ACTION — Phase 5 EXTERNAL reach (operator's call when ready; no active build in flight):**
1. **install-portability mechanics** — the per-platform installer + workspace binding behind `kata-initiate`'s
   config layer (PokeVault link / bring-your-own-vault scaffold / aim-each-folder; MindBridge brings its own).
   Unlocks running on external targets / your vault. Spec: `.planning/specs/install-portability/BRIEF.md`.
2. **multi-model-orchestration** — host-located orchestrator + per-component model/tool routing (incl. the latent
   route-eval-to-another-model option). Spec: `.planning/specs/multi-model-orchestration/BRIEF.md`. *(deps: install.)*
3. **Optional follow-ons:** dashboard **v2** (worker progress-heartbeats → smooth bars; a small `protocol/board.md`
   addition) + an **auto-launch wire-in** (kata-orchestrate convenience hook to open `kata_dash` beside a run).
Each Phase-5 item is a normal Greater-Loop version-up: `kata-initiate` (freeze INTENT) → orchestrated harness →
`kata-closeout` (version-select). Grill these before building — they touch external surfaces. v0.1 release-checklist
(flip Policy A → bump-on-modify) is the eventual milestone after Phase 5 proves out.

## 5. Suggested next skills *(orientation: task-type hint)*
Confirm green → `kata-plan` (Phase 0 slices) → **orchestrated foreground-parallel build** (worktrees + concurrent
workers) → `kata-evaluate` + fresh-context `kata-review` (D15) per merge → roll straight into the next phase.
Method: Opus judgment (Fable unavailable all session) / Sonnet workers; Snyk on new Python; supersede-never-
rewrite; no self-cert (L8). **Memory:** builds must be truly orchestrated, never inline (`exercise-harness-for-real`).
Tag a suite milestone (`v0.1.0-alpha.2`) only after Phase 4, per BUILD-THROUGH.

## 6. Open decisions for the human *(orientation: human-required)*
- **None blocking** — DESIGN frozen, BUILD-THROUGH set. Proceed to build Phase 0→3.
- Per-phase *detail* clarifications as we reach each (the operator wants to question/clarify per item — surface
  the genuine forks, don't stall).
- Future: v0.1 release-checklist (flip Policy A → bump-on-modify) after the loop proves out.

## 7. Redaction
No secrets / keys / PII in any artifact this session. Nothing to redact.
