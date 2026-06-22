---
date: 2026-06-21
spec: loop-hardening
sprint: S3b — the live loop-back (the finale of loop-hardening)
status: FROZEN — operator-driven; runs the live Kata Loop on KataHarness TWICE and grades the re-entry handoff
roadmapRef: ./ROADMAP.md · baseline: S3a green (23bc90a)
closes: G6 (loop-back never exercised) — proves the Kata Loop actually loops
tags: [plan, loop-hardening, sprint-s3b, loop-back, version-up, re-entry, operator-driven, frozen]
note: This is NOT a parallel-slice build sprint. It is a two-cycle live test. Each cycle's INNER build is
  small and code-bearing (so the S2 mutation rule fires) and is orchestrated per the recipe; the POINT is the
  loop ceremony between the cycles, not the features.
---

# S3b — the live loop-back · frozen PLAN

**Goal (the only thing this sprint proves):** the Kata Loop *loops*. We run the live loop on KataHarness itself
**twice** and verify the **second cycle starts informed by the first** (via `kata-initiate` Phase 1b) instead of
cold. That is G6, the last open gap. Everything else (G1–G5, G7) is already closed.

**Operator-driven (cannot be simulated, `exercise-harness-for-real`):** the `kata-initiate` interview answers (both
cycles) and the **"Run again (version-up)"** version-select at Cycle-1 closeout are the operator's. The agent never
invents them.

**Targets (small + code-bearing on purpose):** Cycle-1 = **NIT-2** (validator no-write assertion) · Cycle-2 =
**MAJOR-3** (machine `codeBearing` flag). Both close real BACKLOG items; Cycle-2 builds on Cycle-1's
validator/gate context, which is exactly the carried-context the re-entry test grades.

## LOCKED decisions (do NOT re-decide)
- **The test is the loop, not the features.** The two targets are deliberately minimal. Do not grow them. If a
  cycle's build wants to expand, `kata-defer` it — the sprint's value is the re-entry, not the code.
- **Each cycle is one full pass through the live Kata Loop:** `kata-initiate` (real interview → frozen `INTENT.md`)
  → the Harness (`kata-orchestrate`, orchestrated build of the cycle target per recipe §5) → `kata-evaluate`
  (fresh-context, no-write, PASS) → `kata-closeout` (report + understand-map + human decision gate). No inline
  shortcuts — the ceremony is the thing under test.
- **The loop-back carries existing artifacts only** (`kata-loop` Path A): new baseline SHA (`.kata/RESULT.json`
  `resultSha`), `.kata/understand.md`, `.planning/LESSONS-LEARNED.md`, prior `INTENT.md`. No new protocol fields.
- **Cycle-2 re-entry MUST go through `kata-initiate` Phase 1b** (not a cold Phase 1). Detection = prior frozen
  `INTENT.md` **and** `.kata/understand.md` both present. Phase 1b consumes the four carried inputs, pre-classifies
  `version-up`, surfaces the understand-map instead of re-deriving, and treats prior lessons as known-resolved
  grill branches.
- **Mutation rule fires both cycles (S2/MAJOR-2 live-proven).** Both targets change executable logic ⇒ the worker
  runs `mutation_run.prove_non_vacuous`, the orchestrator collects the union into `.kata/mutation.json`
  (`allNonVacuous: true`), and `kata-evaluate` rubric item 1 checks it. This is the seam-fix MAJOR-2 going live.
- **MAJOR-1 (grounding) is NOT in scope to live-fire.** Grounding only fires on a `research-needed` escalation; a
  small, well-specified validator/footprint change will not produce one. We accept that: G6 is the gap; grounding
  is already unit-proven (`tools/grounding_gate.py` tests). We will NOT manufacture a research need to chase it.
- **No self-cert (L8).** Each cycle's gate is a SEPARATE fresh-context `kata-evaluate` subagent; the final G6
  re-entry grade (Step 4) is likewise a fresh-context judgement, not the building agent's own say-so.

## The sequence (operator-decision points marked ◆)
```
Step 1  CYCLE 1 (NIT-2)
        ◆ kata-initiate interview (operator answers: kind=version-up, target=self, vault, platform, grillDepth, execute)
        → freeze INTENT.md (intent_scaffold.write_intent)
        → Harness: orchestrate build of NIT-2 (worktree + Sonnet worker + TDD + prove_non_vacuous)
        → gate (pytest + validator + Snyk) → gate_emit RESULT/footprint/mutation
        → fresh-context kata-evaluate → PASS
        → kata-closeout: kata-report → offer kata-understand (writes .kata/understand.md)
        ◆ human decision gate → operator picks "Run again (version-up)"
Step 2  LOOP-BACK  kata-loop Path A carries {resultSha, understand.md, lessons, prior INTENT.md} → Cycle 2
Step 3  CYCLE 2 (MAJOR-3)
        ◆ kata-initiate **Phase 1b** consumes carried context (NOT cold) → new goal = next gap vs prior INTENT
        → freeze INTENT.md → Harness build of MAJOR-3 → gate → fresh-context kata-evaluate → PASS → kata-closeout
Step 4  GRADE THE RE-ENTRY HANDOFF  (the G6 deliverable — fresh-context, against the rubric below)
Step 5  CLOSE OUT  checkpoint STATE/HANDOFF/ROADMAP, push, tag (v0.1.0-alpha.3 / loop-hardening-complete); mark all 7 gaps closed
```

## Cycle-1 target — NIT-2 (validator no-write assertion)
**What:** add a `validate_skills.py` `@check` asserting the **no-write evaluator contract** (STANDARDS §1, line
"Evaluators MUST omit Write/Edit") is structural, not just prose — so it can't regress undetected.
**Owns (the cycle's inner build, disjoint within the cycle):** `tools/validate_skills.py` (EDIT),
`tools/tests/test_validate_skills.py` (EDIT), plus a fixture under `tests/fixtures/` if the worker's TDD needs one.
**read_first:** `tools/validate_skills.py` (the `@check` decorator pattern + `check_allowed_tools`),
`docs/STANDARDS.md` §1 (the evaluator no-write rule), `skills/evaluate/kata-evaluate/SKILL.md` +
`skills/plan/kata-research/SKILL.md` (the two evaluator skills + their no-write `allowed-tools`), this LOCKED section.
**action:** add `check_evaluator_no_write(skills)` — for a defined evaluator set (the no-write graders
**`kata-evaluate`** and **`kata-research`**), assert neither `Write` nor `Edit` appears in `allowed-tools`; ERROR
finding otherwise. Register it via the existing `@check`. Keep the set explicit and commented (why these are the
no-write graders). No change to any other check.
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_validate_skills.py -q` (TDD red→green) — a fixture
evaluator skill carrying `Write` flags the ERROR; the real `kata-evaluate`/`kata-research` pass. Full suite +
`validate_skills.py` (35/0, no new skill) stay green.
**acceptance:** adding `Write`/`Edit` to an evaluator skill's `allowed-tools` makes the validator fail; the current
tree stays green.

## Cycle-2 target — MAJOR-3 (machine `codeBearing` flag)
**What:** derive `codeBearing` from the changed-file set so `kata-evaluate` rubric item 1 keys off **evidence**, not
the evaluator's discretion about whether a run is "code-bearing."
**Owns (the cycle's inner build, disjoint within the cycle):** `tools/footprint.py` (EDIT),
`tools/tests/test_footprint.py` (EDIT), `skills/evaluate/kata-evaluate/SKILL.md` (EDIT).
**read_first:** `tools/footprint.py` (`manifest`), `tools/gate_emit.py` (it already calls `manifest` → the flag
flows into `footprint.json` for free), `skills/evaluate/kata-evaluate/SKILL.md` (rubric item 1 wording), the prior
**Cycle-1 INTENT.md + `.kata/understand.md`** (this is a version-up against Cycle-1's green baseline), this LOCKED.
**action:**
- `tools/footprint.py`: add `code_bearing(changed_files) -> bool` (True iff any changed path matches a code glob —
  `*.py`, `*.js`, `*.ts`, `*.tsx`, `*.jsx`, `*.go`, `*.rs`, `*.java`; extend conservatively); include
  `"codeBearing": code_bearing(changed_files)` in `manifest()`'s returned dict. `gate_emit` already calls
  `manifest`, so `.kata/footprint.json` gains the field with no gate_emit change required (optionally surface it in
  the `emit_gate_artifacts` summary dict).
- `skills/evaluate/kata-evaluate/SKILL.md` (EDIT): rubric item 1 — when `.kata/footprint.json` `codeBearing` is
  present, key the "is this run code-bearing?" decision off it (so the mutation-proof requirement is evidence-driven);
  retain the explicit-statement fallback when the flag is absent (BC). Keep frontmatter no-write.
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_footprint.py -q` (red→green) — `code_bearing` True
for a `*.py` change, False for a docs/`*.md`-only change; `manifest` carries `codeBearing`. Full suite + validator
35/0 stay green.
**acceptance:** `footprint.json` carries a correct `codeBearing` flag; a docs-only change reports `False`, a
`*.py` change reports `True`; `kata-evaluate` rubric item 1 references it.

## Re-entry-handoff grading rubric (Step 4 — the G6 proof, scored fresh-context)
Grade whether **Cycle-2's `kata-initiate` Phase 1b started informed**, not cold. Each item PASS/FAIL with evidence:
1. **Loop-back detected** — Phase 1b fired (prior `INTENT.md` + `.kata/understand.md` both present were recognized);
   it did NOT run a cold Phase 1.
2. **Baseline SHA carried** — the Cycle-1 `resultSha` (`.kata/RESULT.json`) was recorded as the version-up baseline
   (the fork point), not re-derived from scratch.
3. **Understand-map ingested** — `.kata/understand.md` was surfaced during ingest; Phase 1b did NOT re-derive what
   Cycle-1 changed.
4. **Prior INTENT as frame** — the new `goal` was set as the *next gap* against the prior `INTENT.md` (NIT-2 → the
   adjacent MAJOR-3), not authored as an unrelated cold goal.
5. **Lessons treated as resolved** — prior `LESSONS-LEARNED` entries were carried as known-resolved branches; no
   re-arguing of ground Cycle-1 already settled.
6. **No re-grill of mapped vocabulary** — terms pinned in `CONTEXT.md` during Cycle-1 were not re-grilled in Cycle-2.
7. **Pre-classified version-up** — Phase 1b classified `version-up` from the carried context rather than asking
   `kind` from a blank slate.

**Verdict:** all PASS ⇒ **the Kata Loop demonstrably loops ⇒ G6 closed ⇒ loop-hardening DONE.** Any FAIL is a
real loop-back defect to fix before the sprint closes (the seam was documentation-wired, not connected).

## Cadence & boundary (sprint-cadence)
- Baseline = most-recent-green (S3a, `23bc90a`). Backout: `git tag pre-s3b` before Cycle 1.
- Each cycle's inner build is a real orchestrated run (worktree + Sonnet worker + fresh-context eval), never inline.
  A lone-task cycle may run on the integration branch directly (kata-orchestrate allows a single sequential task).
- The only steering happens at the operator-decision points (◆) — the two interviews + the version-select.
- This PLAN is frozen; the ROADMAP remains boundary-amendable. If Cycle 1 reveals the targets are mis-sized, amend
  the ROADMAP at the boundary — do not edit this frozen PLAN mid-cycle.

## Ownership disjointness (within each cycle)
| File | Owner |
|---|---|
| `tools/validate_skills.py`, `tools/tests/test_validate_skills.py`, (opt. fixture) | Cycle-1 build |
| `tools/footprint.py`, `tools/tests/test_footprint.py`, `skills/evaluate/kata-evaluate/SKILL.md` | Cycle-2 build |
| `INTENT.md`, `.kata/*` (per cycle), STATE/HANDOFF/ROADMAP checkpoint, the re-entry grade | Conductor/Integrator |
Cycle-1 and Cycle-2 are sequential (Cycle-2 baselines on Cycle-1's merged green), so no cross-cycle file race. ✓
