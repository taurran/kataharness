---
date: 2026-06-20
spec: greater-loop
phase: 3 — CONDUCTOR
status: FROZEN — single cohesive slice (the conductor is thin); built orchestrated in an isolated worktree
designRef: ./DESIGN.md §1 (FROZEN, D87–D90) · ./ROADMAP.md Phase 3
delivery: build-through (this CLOSES the build; the next event is Phase 4 self-dogfood — the test)
tags: [plan, greater-loop, phase-3, conductor, kata-loop, loop-back, frozen]
---

# Phase 3 — CONDUCTOR (`kata-loop`) · frozen PLAN

Builds the **thin top-level conductor** that sequences `initiation → harness → closeout` and owns the
**loop-back**. Per DESIGN §1 it **composes, never reimplements** (like `kata-sprint`): it calls the modules and
the inner `kata-orchestrate`; it does not re-plan or re-evaluate. The greater loop is **optional** — absent the
conductor, a direct one-shot harness run behaves exactly as today (BC). This is the LAST build phase: it makes all
three modules wireable end-to-end. Built as a single orchestrated slice (one Sonnet worker, isolated worktree) →
integration → fresh-context `kata-evaluate`.

## LOCKED decisions (quoted, verbatim — do NOT re-decide)
- **D87 / DESIGN §1:** `kata-loop` is a **thin** conductor sequencing `initiation → harness → closeout`, owning
  the loop-back. **Composes, never reimplements** — calls the modules + `kata-orchestrate`; never re-plans/
  re-evaluates. **Optional:** absent ⇒ today's direct one-shot harness run (BC).
- **Loop-back carries context (GL-R2d):** after closeout, *"run again (version-up)"* re-enters `kata-initiate`
  **with the prior run's context** — new baseline, the understand-map, lessons, the prior `INTENT.md` — so the
  next cycle starts informed, not cold. *"Build something else"* = a fresh initiation.
- **Spine preserved:** plan-doesn't-drift · default-FAIL never weakened (the conductor never gates — `kata-evaluate`
  does) · two-way handoff · everything-versioned.

## Wave DAG
```
Single slice L:  kata-loop conductor + root-AGENTS greater-loop entry
Integration:     --write regen README (35 skills) → validate 35/0 → pytest 112 → fresh eval
```
One slice — the conductor is thin and the wiring is cohesive (no meaningful disjoint second lane). Still built in
an **isolated worktree** with a **fresh-context evaluation** before merge (orchestrated, never inline).

---

## Task L — `kata-loop` conductor + greater-loop entry wiring
**Owns:**
- `skills/coordinate/kata-loop/SKILL.md` (NEW)
- `AGENTS.md` (EDIT — add a short "The Greater Loop" subsection)

**read_first:** `.planning/specs/greater-loop/DESIGN.md` §1–§4 (the whole loop), `skills/coordinate/kata-sprint/SKILL.md`
(the analogous thin conductor — MATCH its compose-never-reimplement style + frontmatter shape), the three modules
it sequences (`modules/initiation/AGENTS.md` + `modules/initiation/kata-initiate/SKILL.md`,
`modules/closeout/AGENTS.md` + `modules/closeout/kata-closeout/SKILL.md`), `skills/coordinate/kata-orchestrate/SKILL.md`
(the harness middle it calls), `protocol/intent.md`, `docs/STANDARDS.md` §1, the root `AGENTS.md`.

**action:**
1. **`skills/coordinate/kata-loop/SKILL.md`** — the thin conductor. Conformant frontmatter:
   `name: kata-loop`, `description:` (one strong sentence), `license: Apache-2.0`, `version: 0.1.0`,
   `category: coordinate`, `status: experimental`, `agnostic: true`, `cost-weight: 2`,
   `allowed-tools: [Read, Grep, Glob]`, `model: fable`, `source:` short provenance,
   `tags: [kata/coordinate, kata/spine, conductor, greater-loop, loop-back]` (MUST include `kata/coordinate` +
   `kata/spine`). Body:
   - **Sequence:** `[[kata-initiate]]` (front half → frozen `INTENT.md`) → the **harness** (`[[kata-orchestrate]]`
     + the built loop — grill/plan/orchestrate/worktree/tdd/evaluate/handoff) → `[[kata-closeout]]` (back half →
     report + understand-map + human decision). State clearly it **composes** these and never re-plans or
     re-evaluates (the gate stays `[[kata-evaluate]]`; the plan stays the orchestrator's).
   - **Own the loop-back (GL-R2d):** on closeout's decision *"run again (version-up)"*, re-enter `kata-initiate`
     **carrying context** — the new green baseline, the understand-map, the lessons, and the prior `INTENT.md` —
     so the next cycle starts informed. *"Build something else"* ⇒ a fresh `kata-initiate` (cold). Document the
     exact context payload carried across the loop-back (baseline SHA · understand-map artifact · lessons ·
     prior INTENT) — it composes existing artifacts, defines no new protocol.
   - **Optional / BC (DESIGN §9):** absent the conductor, a direct one-shot harness run behaves exactly as today;
     `INTENT.md` absent ⇒ harness reads the frozen DESIGN. The conductor adds no drift surface — it only sequences.
   - **Wikilinks** (ALL now resolve): `[[kata-initiate]]`, `[[kata-orchestrate]]`, `[[kata-closeout]]`,
     `[[kata-evaluate]]`. (Optionally `[[kata-handoff]]`, `[[kata-report]]`, `[[kata-understand]]` — all exist.)
2. **`AGENTS.md` (EDIT)** — add a brief **"The Greater Loop"** subsection (just after `## What KataHarness is`)
   naming `kata-loop` as the optional full-loop entry point: INITIATION (`kata-initiate`) → HARNESS (reused) →
   CLOSEOUT (`kata-closeout` + `kata-understand`), sequenced by the thin `kata-loop` conductor with a
   context-carrying loop-back; modules are self-contained `modules/<name>/` dirs (D91). Keep it to a short
   paragraph + the mini-diagram; do NOT restate the whole spine. Touch ONLY this added subsection — leave the rest
   of AGENTS.md unchanged.

**verify (default-FAIL):** `cd tools && uv run python validate_skills.py` in the worktree — module discovery is
already in place, so the new skill is seen; **expect 35 skills** with **only a README-sync error** (integrator
regens the index) and **no other error** (all wikilinks resolve, since the modules exist on this base). If any
error other than README-sync appears, fix it. `uv run pytest -q` stays green (112). Parse-check the kata-loop
frontmatter against `docs/STANDARDS.md` §1 (all REQUIRED keys, name==dir, tags include kata/coordinate +
kata/spine, agnostic:true).

**acceptance (falsifiable):**
- `kata-loop` frontmatter passes every STANDARDS §1 rule (verified at integration: 35/0).
- The body sequences initiation → harness → closeout, explicitly composes (never re-plans/re-evaluates/gates),
  and documents the loop-back context payload (baseline · understand-map · lessons · prior INTENT).
- BC stated: absent the conductor ⇒ today's direct run.
- All wikilinks resolve; no unresolved/forward references.
- `AGENTS.md` gains a focused "The Greater Loop" subsection and nothing else changed in it.

**threat model:** none new — markdown conductor; `allowed-tools` Read/Grep/Glob (it sequences other skills; the
git/push/merge actions remain human-gated inside `kata-closeout`, not here).

## Integration (after the slice is green in its worktree)
1. Merge `phase3/kata-loop` into `phase3/integration` (single branch — fast-forward or no-ff).
2. `cd tools && uv run python validate_skills.py --write` (35 skills, regen index) → `validate_skills.py` =
   **35 skills / 0 errors**.
3. `uv run pytest -q` — full green (112; no new code).
4. Snyk: no new first-party Python → none required (note pre-existing documented CWE-23 FPs unchanged).
5. **Fresh-context `kata-evaluate`** over this PLAN → PASS/NEEDS_WORK. Then merge to `master`. Backout safety: tag
   `pre-phase3` before merge.
6. **This CLOSES the Greater-Loop build (Phases 0–3).** The next event is **Phase 4 — the self-dogfood test of the
   complete loop** (the first TEST per BUILD-THROUGH) — which the operator drives.

## Ownership
| File | Owner |
|---|---|
| `skills/coordinate/kata-loop/SKILL.md`, `AGENTS.md` (Greater-Loop subsection) | L |
| `README.md` (index regen via --write) | Integrator (post-merge) |
