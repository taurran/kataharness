---
date: 2026-06-20 (Greater-Loop DESIGN FROZEN [D87–D90]; BUILD-THROUGH directive active; for a fresh/compacted session)
branch: master — on private remote github.com/taurran/kataharness (pushed)
green: validator 31 skills / 0 errors · pytest 72 passed · Snyk 0 · tag v0.1.0-alpha.1 (re-confirm before building)
tags: [handoff, v0.1.0-alpha.1, greater-loop-FROZEN, build-through, next-phase0-foundations, full-context]
authored-for: kata-orient (sections map to the three orientation tiers)
---

# HANDOFF — KataHarness — 2026-06-20 (Greater Loop FROZEN · BUILD-THROUGH · build Phase 0→3 then test)

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
- Branch `master`, **pushed to private remote** `github.com/taurran/kataharness`, tree clean. **31 skills / 0
  errors · pytest 109** (72 + F1 15 + F2 22) · Snyk: 3 real fixed + residual CWE-23 documented FP. Confirm:
  `cd tools && uv run pytest -q  &&  uv run python validate_skills.py`.
- **✅ Phase 0 FOUNDATIONS DONE** (merged `9e1b27c`): F1 `tools/gate_emit.py` (eval artifacts wired into the live
  gate — closes dogfood-2 residual) + F2 `tools/graph_gen.py` (tree-sitter graph runtime per protocol/graph.md).
  Real orchestrated run; fresh-context eval PASS 8/8. Plan/security: `specs/greater-loop/{PLAN,SECURITY}-phase0.md`.
- **Backout safety:** tags `pre-phase0` (before Phase 0 merge) + `pre-dogfood-2` + `v0.1.0-alpha.1` on remote.
  Policy A: skills held `0.1.0`.

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

## 4. THE PLAN — build the whole Greater Loop, THEN test *(orientation: VOLATILE — the immediate action)*
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

**NEXT ACTION — Phase 1 INITIATION (Phase 0 ✅ done; continue without testing per BUILD-THROUGH):**
1. **`kata-plan`** partitions **Phase 1 Initiation** into disjoint slices (orchestrated foreground-parallel build):
   - **`modules/initiation/`** — new module dir with its **own `AGENTS.md`** (nested-rollup; `kata-orient` supports it).
   - **`kata-initiate`** — front door: ingest intent → classify `kind: project|research|version-up` → capture the
     **frozen `INTENT.md`** artifact (schema in DESIGN §2: goal/fixes/features/modulesAdded/changeSummary/target/
     grillDepth/readiness). Composes `kata-readiness`/`kata-grill`/`kata-bootstrap`/`kata-context`.
   - **Interactive target/platform/vault config** (install-portability config layer, GL-R3c): self · existing repo ·
     vault (PokeVault link / bring-your-own / aim-each-folder) · platform (Claude/MindBridge/Kiro).
   - **Dual spec-to-ready control** (GL-R2b): user "execute" anytime (hard bail) OR grill self-proposes execute.
2. Same rhythm as Phase 0: worktrees + concurrent Sonnet workers → integration green (pytest · validator · Snyk)
   → fresh-context `kata-evaluate` PASS → merge → **continue straight into Phase 2.**
3. **Phase 2 CLOSEOUT** (`modules/closeout/` + `kata-closeout` + `kata-understand`, graph-backed by F2) → **Phase 3
   `kata-loop`** conductor — **without stopping to test.**
4. **THEN Phase 4** — self-dogfood the complete Greater Loop (the next test). **THEN Phase 5** — external reach
   (install installers / multi-model).

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
