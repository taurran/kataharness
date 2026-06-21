---
date: 2026-06-21 (loop-hardening S1 DONE + at the operator-demo boundary; next = S2 then S3; for a fresh/compacted session)
branch: master — on private remote github.com/taurran/kataharness (pushed), tip 5ed9020
green: validator 35 skills / 0 errors · pytest 268 passed · Snyk medium+ 0 (residual Low CWE-23 = documented FPs) · tags pre-s1 + v0.1.0-alpha.1 + v0.1.0-alpha.2
tags: [handoff, loop-hardening, s1-done, next-s2-s3, sprint-cadence, full-context]
authored-for: kata-orient (sections map to the three orientation tiers)
---

# HANDOFF — KataHarness — 2026-06-21 (loop-hardening S1 done · next = S2 then S3)

> **Fresh/compacted session: read in order, confirm green, resume at §4.** Everything below is durable +
> committed + **pushed to the private remote**. Maps to `kata-orient` tiers: §1 → context · §2+§4 → volatile ·
> §6 → human-required.

## 1. Read-in order  *(orientation: CONTEXT)*
1. `AGENTS.md` (spine + conventions; has a "The Greater Loop" entry) · 2. `docs/STANDARDS.md` §1 (frontmatter —
   `allowed-tools` REQUIRED) · 3. `.planning/STATE.md` (CURRENT box — the live picture) ·
4. **`.planning/DECISIONS.md` — D87–D91** (Greater Loop + module structure) · 5. `.planning/LESSONS-LEARNED.md` ·
6. **`.planning/specs/loop-hardening/{ROADMAP,PLAN-s1}.md` ← THE ACTIVE SPRINT PLAN** (S2/S3 are detailed in the
   ROADMAP) · 7. `.planning/specs/greater-loop/{DESIGN,PLAN-phase0..3}.md` (the built loop) ·
8. `.planning/specs/subagent-dashboard/{INTENT,PLAN,REPORT}.md` (the Phase-4 dogfood that shipped the dashboard).
⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated, harness-injected).

## 2. State *(orientation: VOLATILE)*
- Branch `master`, **pushed**, tree clean, tip `5ed9020`. **35 skills / 0 errors · pytest 268 · Snyk med+ 0**.
  Confirm: `cd tools && uv run pytest -q && uv run python validate_skills.py`. Windows: git-bash mangles `/tmp/...`
  args to native python — use `C:/...` paths or `MSYS_NO_PATHCONV=1` (a `.kata`-relative path is safest).
- **✅ GREATER LOOP fully built + proven (Phases 0–3 + Phase-4 self-dogfood):**
  - **P0** (`9e1b27c`): `tools/gate_emit.py` (emits `.kata/{RESULT,footprint,mutation}.json`) + `tools/graph_gen.py`
    (tree-sitter `kata.graph.json`). **P1** (`157804f`): `modules/initiation/` + `kata-initiate` + `protocol/intent.md`
    (D91 self-contained modules; validator discovers `modules/*/*/SKILL.md`). **P2** (`20dac30`): `modules/closeout/`
    + `kata-closeout` (never gates) + `kata-understand` (graph-backed, writes `.kata/understand.md`). **P3** (`f39f37b`):
    `skills/coordinate/kata-loop/` conductor (initiation→harness→closeout + context-carrying loop-back).
  - **Adversarial review fixed real seam breaks** (`2d71f2e`): kata-initiate gained `AskUserQuestion` + loop-back
    ingestion (Phase 1b); kata-understand WRITES `.kata/understand.md`; kata-closeout wikilinks `[[kata-loop]]`;
    kata-orchestrate RESULT.json precondition; kata-bootstrap points to kata-loop. (Always red-team after a build.)
  - **Phase-4 dogfood shipped `v0.1.0-alpha.2`** (`3ed18d3`): the **subagent-dashboard** (`tools/kata_dash.py` +
    `kata_dash_model.py`) built by running the WHOLE loop on self; caught+fixed a real Windows UTF-8 crash.
- **✅ loop-hardening S1 DONE** (`fedbb87`, fresh-eval PASS 8/8) — **closes the gaps the Phase-4 accounting exposed**
  (see §3). Built `tools/kata_board.py` (live coordination-board emitter: `.kata/board.md` append-only incl.
  **PROGRESS heartbeats**, single-writer `.kata/state.json`, **self-creates `.kata/`**) + dashboard heartbeat bars +
  `tools/kata_dash_demo.py` replay driver. Title = **`KATAHARNESS 改善型`** (kaizen-gata; torii+hiragana removed per
  operator — memory `ui-text-japanese-concise`). pytest 244→268.
- **⏸ STOPPED at the S1 boundary for the operator to watch the live dashboard + give feedback** (sprint-cadence
  boundary). **Backout:** tag `pre-s1`. Policy A (skills held 0.1.0).

## 3. The verified gaps loop-hardening closes *(orientation: CONTEXT — why these sprints exist)*
The Phase-4 dogfood was an honest *first happy-path* run; an accounting (with `ls`/artifact proof) found load-bearing
mechanisms that never fired. **Grounded, not assumed:**
| Gap | Verified | Sprint |
|---|---|---|
| G1 no live board/state emitted | `ls .kata/board.md state.json` → absent after the real run | **S1 ✅ DONE** |
| G2 dashboard never tailed reality | consequence of G1 | **S1 ✅ DONE** |
| G3 mutation/non-vacuity proof never ran | `mutation.json` absent; gate_emit called w/o mutation_records | **S2** |
| G4 interactive initiation never prompted | the run decided inline; human got only the version-select | **S2** |
| G5 grounding gate / `kata-research` never fired | no research-need escalation occurred | **S3** |
| G6 loop-back never exercised | version-select chose "ship"; re-entry/handoff unproven | **S3** |

## 4. NEXT ACTION — S2, then S3 *(orientation: VOLATILE — the immediate work)*
**First, when the operator returns:** ask if S1's live dashboard is good / what to change (this is the sprint
boundary — `kata-sprint` G1–G4 is where steering happens; the roadmap is boundary-amendable). Then proceed.

### S2 — Vet the gate + bring the human into initiation (closes G3, G4). Baseline = S1 green (`5ed9020`).
Two disjoint slices, orchestrated foreground-parallel build (recipe in §5):
- **S2a — mutation/non-vacuity proof in the gate.** Wire the `kata-tdd` mutation step so the gate actually runs it:
  use the existing `tools/mutation_check.py` (`mutation_verdict`, `apply_line_removal`) to mutate a covered line,
  re-run the named test, collect `{testWentRed, nonVacuous}` per test, and pass them to `gate_emit` as
  `mutation_records` → `.kata/mutation.json` `{records, allNonVacuous}`. Make `kata-evaluate` READ it (NEEDS_WORK if
  a claimed-covered test is vacuous). Demonstrable artifact: a `.kata/mutation.json` proving tests *bite*. (Owns:
  a small `tools/mutation_run.py` helper + tests; kata-tdd + kata-evaluate SKILL edits. Note: SKILL-edit slices and
  tooling slices stay disjoint by file.)
- **S2b — `kata-initiate` actually prompts.** Today the skill *documents* the interview but a run can skip it. Make
  the interview real: the skill must STOP and use `AskUserQuestion` (it's in allowed-tools now) for kind/target/
  grill-depth and the dual-control execute decision — not decide inline. This is mostly a SKILL.md rigor pass +
  possibly a tiny `kata.config`/INTENT scaffolding helper. Demonstrable: a dry initiation that asks the operator
  questions and freezes an `INTENT.md` from the answers. (Owns: `modules/initiation/kata-initiate/SKILL.md` + maybe
  a helper + test.) **Disjoint from S2a** (different files).

### S3 — Exercise the cognition + PROVE THE LOOP LOOPS (closes G5, G6). Baseline = S2 green.
**This is the operator's hard requirement: ≥1 real loop-back iteration with the handoff evaluated as it cycles back.**
- **S3a — grounding + research.** Deliberately introduce a `research-needed` task → run `kata-research` (no-write,
  fresh-context) → the **grounding gate** (`kata-evaluate` injected-knowledge mode: GROUND/REJECT/ESCALATE on each
  finding, source must support the claim). Demonstrable: real GROUND/REJECT verdicts on cited findings.
- **S3b — the loop-back.** Run a real version-up cycle: `kata-closeout` decision "run again (version-up)" →
  `kata-loop` loop-back → `kata-initiate` **Phase 1b** re-entry consuming the carried context (`.kata/understand.md`,
  prior `INTENT.md`, `LESSONS-LEARNED.md`, baseline SHA) → a second small build → close out. **Evaluate the handoff
  on re-entry** (did Phase 1b actually ingest the prior context? did it avoid re-grilling mapped territory?).
  Demonstrable: a second loop cycle that provably started *informed*, with the re-entry handoff graded.

After S3: loop-hardening is done → the loop is "vetted, demonstrably loops." **Then Phase 5 EXTERNAL** (install-
portability mechanics · multi-model-orchestration; briefs in `.planning/specs/{install-portability,multi-model-
orchestration}/BRIEF.md`) remains the post-hardening horizon. v0.1 release-checklist (flip Policy A → bump-on-modify)
is the eventual milestone.

## 5. The orchestration recipe (how every sprint/phase is built — follow it exactly) *(orientation: task-type hint)*
This is the **vetted, never-inline** loop the operator requires (memory `exercise-harness-for-real`):
1. **Freeze** the sprint plan (`kata-plan` roadmap-layer/JIT) → `.planning/specs/loop-hardening/PLAN-s<n>.md` with
   LOCKED decisions + disjoint file-ownership slices + per-slice runnable `verify`/acceptance. Commit it. `git tag -f pre-s<n>`.
2. **Worktrees:** `git worktree add -b s<n>/<slice> /c/Dev/_kata_s<n>/<slice> master` per slice (isolated).
3. **Dispatch concurrent worker subagents** (Agent tool, **model: sonnet**) — one per slice, each scoped to its
   worktree + owned files only, TDD (tests red→green), commit in-worktree. Workers report SHAs + green numbers.
4. **Integrate:** new branch off master, `git merge --no-ff s<n>/<sliceA> s<n>/<sliceB>` (octopus; disjoint = no
   conflict). `cd tools && uv sync` (if deps changed). Apply any integrator robustness fix the gate surfaces.
5. **Gate:** `uv run pytest -q` + `uv run python validate_skills.py` (35/0) + `mcp__Snyk__snyk_code_scan` on new
   Python (fix real issues; CWE-23 CLI-path FPs are documented — see `SECURITY-phase0.md`). Emit `.kata/RESULT.json`
   via `tools/gate_emit.py`.
6. **Fresh-context `kata-evaluate`** — a SEPARATE no-write Agent subagent (sonnet), 8-rubric, default-FAIL, runs the
   gate itself. **No self-certification (L8).** Must return PASS.
7. **Merge to master**, push, `git worktree remove` + `git branch -D` the slices, checkpoint STATE/HANDOFF, commit+push.
8. **At a sprint boundary that the operator must see/decide** (like S1's demo, or any version-select): STOP and ask.
Model routing: **judgment/eval = Opus** (Fable 5 unavailable all session), **workers = Sonnet**. Snyk on new Python.
Supersede-never-rewrite. Surface genuine forks via `AskUserQuestion`; don't decide the operator's calls inline.

## 6. Open decisions for the human *(orientation: human-required)*
- **At the S1 boundary now:** is the live dashboard good? anything to change? proceed to S2? (operator is watching it).
- **S3 must include a real loop-back iteration** (operator's explicit requirement) — do not skip it.
- Future: v0.1 release-checklist (flip Policy A → bump-on-modify) after loop-hardening + Phase 5 prove out.

## 7. Redaction
No secrets / keys / PII in any artifact this session. Repo is PRIVATE. Nothing to redact.
