---
name: kata-improve
description: >-
  The Improvement Kata applied to the harness itself — fold accumulated LESSONS-LEARNED, review findings, and
  run surprises back into the SKILLS. Use after a run/milestone to deepen skills, close recurring gaps, and
  bump versions. Targets the skills/ tree (not product code); decides WHAT to change and delegates new-skill
  authoring to kata-write-skill.
version: 0.1.0
category: meta
status: experimental
agnostic: true
allowed-tools: [Read, Grep, Glob, Edit, Write, Bash]
source: adapted-from the Improvement Kata (Toyota Kata) + mattpocock/skills engineering/improve-codebase-architecture
tags: [meta, kata, retrospective, continuous-improvement]
---

# kata-improve — every run improves the harness

This is the phase that makes the project's name true. It is **cross-run and retrospective**, and it edits the
**skills**, not the product. Boundaries that keep it from competing:
- vs [[kata-review]]: review *finds* defects in **one** run (a gate); improve folds **accumulated** lessons
  back over many runs (the kata). Review's HOLD findings are *inputs* here.
- vs the worker's fix loop: workers fix **product code**; improve changes **`skills/**`, docs, protocol**.
- when a gap needs a **new** skill, improve doesn't free-hand it — it calls [[kata-write-skill]].

## Inputs (read on demand — don't embed)
`.planning/LESSONS-LEARNED.md`, `DECISIONS.md`, any `REVIEW-*.md`, and the latest run's surprises/handoff.
These are durable files; load them when improving, not into the loop.

## The kata (target-condition → current → experiment)
1. **Target condition** — what should the harness do better? (e.g. "the grill converges to a more specific
   contract"; "no recurring class of drift"). State it concretely.
2. **Grasp the current condition** — what do the lessons/reviews show is actually happening? Cluster
   recurring signals; a lesson that recurs is a skill defect, not a footnote.
3. **Next experiment** — the smallest change to a skill/doc that moves toward the target. One step, not a
   rewrite. Apply it; record the expected effect so the *next* run can tell if it worked.

## Applying a change (with discipline)
- Edit the skill body; **bump its semver** (PATCH wording/fix, MINOR new capability, MAJOR contract change)
  and update the **README index** (the source of truth — keep it honest; the v0.1 review caught drift here).
- If the change is a new skill → [[kata-write-skill]]. If it retires one → `deprecated/` + `supersedes`, never
  silent deletion.
- Record the improvement back into `LESSONS-LEARNED.md`/`DECISIONS.md` so the kata compounds.
- Keep changes evidence-driven: cite the lesson/finding that motivated each. No speculative gold-plating.

## Output
A small, cited set of skill/doc edits + version bumps + an index update, and a one-line "expected effect to
verify next run." The harness is now incrementally better; the loop continues.
