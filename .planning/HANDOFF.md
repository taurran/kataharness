---
date: 2026-06-21 (loop-hardening S1+S1.5+S2+S3a DONE + red-team seam-fixes + Kata Loop rename; ONLY G6 left = S3b live loop-back, operator-driven)
branch: master — private remote github.com/taurran/kataharness, tip 94539dd (pushed)
green: validator 35 skills / 0 errors · pytest 420 passed · Snyk medium+ 0 (residual Low CWE-23 = documented FPs)
tags: pre-s1 · pre-s1.5 · pre-s2 · pre-s3a · v0.1.0-alpha.1 · v0.1.0-alpha.2
authored-for: kata-orient (sections map to the three orientation tiers)
---

# HANDOFF — KataHarness — 2026-06-21 (loop-hardening 6/7 gaps closed · next = S3b loop-back, the finale)

> **Fresh/compacted session: read §1 in order, confirm green (§2), resume at §4 (S3b).** Everything below is
> durable + committed + **pushed**. Maps to `kata-orient` tiers: §1 → CONTEXT · §2+§4 → VOLATILE · §6 → human-required.

## 1. Read-in order  *(orientation: CONTEXT)*
1. `AGENTS.md` (spine + conventions; the **"The Kata Loop"** entry) · 2. `docs/STANDARDS.md` §1 (frontmatter —
   `allowed-tools` REQUIRED) · 3. `CONTEXT.md` (glossary — **Kata Loop / the Harness / loop-back** are defined here) ·
4. `.planning/STATE.md` (top CURRENT box — live picture) · 5. **`.planning/DECISIONS.md` D87–D92**
   (Kata Loop build, module structure, D92 = the Greater Loop→Kata Loop rename + the red-team seam fixes) ·
6. `.planning/LESSONS-LEARNED.md` · 7. **`.planning/specs/loop-hardening/{ROADMAP,RESEARCH-s1.5,PLAN-s1,PLAN-s1.5,PLAN-s2,PLAN-s3a}.md`**
   (the sprint record; ROADMAP has the S3 detail) · 8. `.planning/specs/greater-loop/{DESIGN,PLAN-phase0..3}.md`
   (the built loop — frozen; keeps the old "Greater Loop" term as **provenance**, the live name is now "the Kata Loop").
⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated, harness-injected).

## 2. State *(orientation: VOLATILE)*
- Branch `master`, **pushed**, tree clean, tip `94539dd`. **35 skills / 0 errors · pytest 420 · Snyk med+ 0.**
  Confirm: `cd tools && uv run pytest -q && uv run python validate_skills.py`. **Windows gotcha:** git-bash mangles
  `/tmp/...` args to native python — use `C:/...` paths, a `.kata`-relative path, or `MSYS_NO_PATHCONV=1`. Also: a
  `..` segment in any operator-supplied path is rejected by the `_safe_path` guards by design (CWE-23) — use
  absolute paths without `..` when driving tools by hand.
- **✅ THE KATA LOOP fully built + proven (Phases 0–3 + Phase-4 self-dogfood):** P0 `tools/gate_emit.py` +
  `graph_gen.py` · P1 `modules/initiation/` + `kata-initiate` + `protocol/intent.md` (D91 self-contained modules) ·
  P2 `modules/closeout/` + `kata-closeout` (never gates) + `kata-understand` (writes `.kata/understand.md`) ·
  P3 `skills/coordinate/kata-loop/` conductor (initiation→Harness→closeout + context-carrying loop-back).
  Adversarial-fixed (`2d71f2e`); Phase-4 dogfood shipped `v0.1.0-alpha.2` (the subagent-dashboard).
- **✅ loop-hardening S1–S3a DONE** (each a real orchestrated run → fresh-context `kata-evaluate` PASS → pushed):
  - **S1** (`fedbb87`) live telemetry — `tools/kata_board.py` + dashboard heartbeats (G1+G2). Title `KATAHARNESS 改善型`.
  - **S1.5** (`e753504`) status-surface adapters (G7) — seeded `adapters/claude/` (statusline + `refreshInterval:1`) +
    `tools/kata_statusline.py` + `tools/kata_web.py` (localhost web viewer, 127.0.0.1). Per-platform: Claude=in-window
    now · Codex=no surface→viewer fallback · Kiro=`.vsix` deferred (`RESEARCH-s1.5.md`). pytest →334.
  - **S2** (`cddf9ff`) mutation proof (G3) + interactive initiate (G4) — `tools/mutation_run.py` (restoring
    mutate→run→restore loop); `kata-evaluate` item 1 **requires** `.kata/mutation.json` `allNonVacuous:true` for
    code-bearing work; `tools/intent_scaffold.py`; `kata-initiate` hard interview STOP. pytest →367.
  - **S3a** (`4391deb`) grounding + research (G5) — `tools/escalation.py` + `tools/grounding_gate.py`
    (GROUND/REJECT/ESCALATE → `.kata/grounding.json`), wired into `kata-research` + `kata-evaluate`. pytest →420.
- **✅ Red-team of S2+S3a + Kata Loop rename (`94539dd`, D92):** an adversarial review found two **documentation-only
  seams** — fixed inline: (MAJOR-1) `kata-orchestrate` now explicitly persists the grounding verdict via
  `tools/grounding_gate.py` → `.kata/grounding.json` (it was named only in the no-write `kata-evaluate`, so a real
  cycle would have silently skipped it); (MAJOR-2) the orchestrator now collects per-task `prove_non_vacuous` records
  into the integration `gate_emit` mutation set. **These two fixes are orchestrator *prose* — they get live-proven by
  S3b** (the first real cycle to route through them). "Greater Loop" → **"the Kata Loop"** across active surfaces
  (inner one-shot stays **"the Harness"**; **loop-back** unchanged); frozen specs keep the old term as provenance.
- **⏸ 6 of 7 verified gaps closed (G1–G5, G7). ONLY G6 remains = S3b, the live loop-back — operator-driven.** The
  human "run again (version-up)" decision can't be simulated (`exercise-harness-for-real`). Policy A (skills @ 0.1.0).

## 3. The verified gaps loop-hardening closes *(orientation: CONTEXT — grounded in the Phase-4 dogfood accounting)*
| Gap | Verified-broken evidence | Closed by |
|---|---|---|
| G1 no live board/state · G2 dashboard never tailed reality | `.kata/board.md`/`state.json` absent after the run | **S1 ✅** |
| G7 viewer not seamless per-platform | only a separate-window TUI existed | **S1.5 ✅** |
| G3 mutation/non-vacuity proof never ran | `mutation.json` absent; no runner | **S2 ✅** |
| G4 interactive initiation never prompted | run decided inline; human got one prompt | **S2 ✅** |
| G5 grounding gate / `kata-research` never fired | no machine artifact/emitter; chain never invoked | **S3a ✅** |
| **G6 loop-back never exercised** | version-select chose "ship"; re-entry/handoff unproven | **S3b ← NEXT** |

## 4. NEXT ACTION — S3b, the live loop-back (closes G6; proves the Kata Loop loops) *(VOLATILE — the immediate work)*
**This is the operator's hard requirement and the finale of loop-hardening.** It is NOT a tooling-build sprint — it
**RUNS the live Kata Loop on KataHarness itself, twice**, with the operator making the un-simulatable calls, and then
**grades the re-entry handoff**. It also live-proves the MAJOR-1/MAJOR-2 orchestrator seam fixes.

**Step 0 — Freeze `PLAN-s3b.md`** (recipe §5 step 1) defining: the two small **code-bearing** version-up targets
(so each cycle also exercises the S2 mutation requirement), and the **re-entry-handoff grading rubric**.
*Recommended targets (close real backlog items as we go):* **Cycle-1 = NIT-2** (add a `validate_skills.py` check that
evaluator skills `kata-evaluate`/`kata-research` exclude `Write`/`Edit`); **Cycle-2 = MAJOR-3** (derive a
`codeBearing` boolean in `footprint.json`/`gate_emit` so rubric item 1 keys off evidence, not evaluator discretion).
Both are small, testable, and Cycle-2 naturally builds on Cycle-1's context. (Operator may pick different targets.)

**Step 1 — Cycle 1 (a real version-up through the Kata Loop):**
- `kata-initiate` — run the **real interview** (`AskUserQuestion`; exercises G4): kind=version-up · target=self ·
  vault · platform · grillDepth · the execute decision → freeze `INTENT.md` via `tools/intent_scaffold.py`.
- The Harness — orchestrated build of Cycle-1's target per recipe §5 (worktree + Sonnet worker + TDD). Because it's
  code-bearing, the worker runs `mutation_run.prove_non_vacuous` and the orchestrator collects records into
  `.kata/mutation.json` (exercises G3 + live-proves MAJOR-2).
- `kata-evaluate` (fresh-context, no-write) → PASS.
- `kata-closeout` — report + **offer the understand-map** (writes `.kata/understand.md`) → **human decision gate**.
  **➜ Operator picks "Run again (version-up)"** — the un-simulatable version-select that triggers the loop-back.

**Step 2 — The loop-back:** `kata-loop` carries the context forward — new **baseline SHA** (`.kata/RESULT.json`
`resultSha`), **`.kata/understand.md`**, **`LESSONS-LEARNED.md`**, and the **prior `INTENT.md`** — into Cycle 2.

**Step 3 — Cycle 2 (re-entry, the actual G6 proof):** `kata-initiate` **Phase 1b** MUST detect the loop-back and
consume the carried context (NOT cold-start): pre-classify version-up, surface the understand-map instead of
re-deriving it, treat prior lessons as known-resolved grill branches (no re-grilling mapped ground), set the new
`goal` as the *next* gap against the prior INTENT. Then freeze a new `INTENT.md` → build Cycle-2's target → evaluate
→ closeout.

**Step 4 — GRADE THE RE-ENTRY HANDOFF (the deliverable):** a fresh-context evaluation that specifically checks —
*did Phase 1b actually ingest `.kata/understand.md` + the prior `INTENT.md` + the baseline SHA? did it avoid
re-grilling resolved vocabulary? did Cycle 2 provably start **informed**?* Document the verdict. **If yes → the Kata
Loop demonstrably loops → loop-hardening is DONE.**

**Step 5 — Close out S3b:** checkpoint STATE/HANDOFF/ROADMAP, push, tag (e.g. `v0.1.0-alpha.3` or
`loop-hardening-complete`). Mark G6 ✅ and all 7 gaps closed.

**After S3b:** loop-hardening complete → "vetted, demonstrably loops." Remaining backlog hardening (the rest of the
red-team residue + planning-modes alignment — `.planning/BACKLOG.md`), then **Phase 5 EXTERNAL** (install-portability ·
multi-model-orchestration; `BRIEF.md`s under `.planning/specs/`). v0.1 release-checklist (flip Policy A →
bump-on-modify) is the eventual milestone.

## 5. The orchestration recipe (each cycle's *inner* build follows this — never inline) *(task-type hint)*
The **vetted, never-inline** loop (memory `exercise-harness-for-real`). S3b uses it **once per cycle** for the inner build:
1. **Freeze** the plan → `PLAN-s<n>.md` (LOCKED decisions + disjoint file-ownership slices + per-slice runnable
   `verify`). Commit. `git tag -f pre-s<n>`.
2. **Worktrees:** `git worktree add -b s<n>/<slice> C:/Dev/_kata_s<n>/<slice> master` per slice.
3. **Dispatch concurrent worker subagents** (Agent tool, **model: sonnet**) — one per slice, scoped to its worktree +
   owned files, TDD (red→green), **code-bearing tasks run `mutation_run.prove_non_vacuous`**, commit in-worktree.
4. **Integrate:** branch off master, `git merge --no-ff` the slices (octopus; disjoint = no conflict), `cd tools && uv sync`.
5. **Gate:** `uv run pytest -q` + `validate_skills.py` (35/0) + `mcp__Snyk__snyk_code_scan` on new Python (CWE-23
   CLI/stdin-path FPs are documented). **Emit `.kata/RESULT.json` via `gate_emit`** — and for a code-bearing run pass
   `mutation_records` so `.kata/mutation.json` exists with `allNonVacuous:true` (rubric item 1 requires it). If a
   `research-needed` escalation arises, persist the grounding verdict via `grounding_gate.write_grounding`.
6. **Fresh-context `kata-evaluate`** — SEPARATE no-write Agent subagent (sonnet), 8-rubric, default-FAIL. **No
   self-cert (L8).** Must PASS. (It pre-emptively regenerates RESULT.json for the integration if needed — S2 lesson.)
7. **Merge to master**, push, `git worktree remove` + `git branch -D` the slices, checkpoint STATE/HANDOFF, push.
8. **At an operator-decision boundary** (S3b's version-select; any demo): STOP and ask via `AskUserQuestion`.
Model routing: **judgment/eval = Opus** (Fable 5 has been unavailable), **workers = Sonnet**. Supersede-never-rewrite.

## 6. Open decisions for the human *(orientation: human-required)*
- **S3b is operator-driven:** the `kata-initiate` interview answers (both cycles) + the **"run again (version-up)"
  version-select** at Cycle-1 closeout are yours — do not simulate them. Confirm/choose the two cycle targets at Step 0.
- **S3b must include a real loop-back** (your explicit requirement) — do not collapse it to a single cycle.
- Future: v0.1 release-checklist (flip Policy A → bump-on-modify) after loop-hardening + Phase 5 prove out.

## 7. Redaction
No secrets / keys / PII in any artifact this session. Repo is PRIVATE. Nothing to redact.
