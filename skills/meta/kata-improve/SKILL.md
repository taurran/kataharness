---
name: kata-improve
description: >-
  The Improvement Kata applied to the harness itself — fold accumulated LESSONS-LEARNED, review findings, and
  run surprises back into the SKILLS. Use after a run/milestone to deepen skills, close recurring gaps, and
  bump versions. Targets the skills/ tree (not product code); decides WHAT to change and delegates new-skill
  authoring to kata-write-skill.
license: Apache-2.0
version: 0.1.0
category: meta
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Edit, Write, Bash]
source: adapted-from the Improvement Kata (Toyota Kata) + mattpocock/skills engineering/improve-codebase-architecture
tags:
  - kata/meta
  - kata/module/meta
  - improvement-kata
  - retrospective
  - continuous-improvement
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
- **Managed-learning path (loop-cognition L5):** if a recurring lesson is reusable as a skill but the loop
  (not a human) is distilling it mid-stream, author it as an **agent-distilled candidate** via
  [[kata-write-skill]] (sandboxed: `scope: agent`, in `<agentSkills.dir>/candidates/`, NOT loaded universally) →
  grounding gate → the human persistence gate [[kata-promote]] at session end. Repo-skill edits go the normal
  route above; only *agent-distilled* skills route through the two-stage candidate→promote gate.
- Record the improvement back into `LESSONS-LEARNED.md`/`DECISIONS.md` so the kata compounds.
- Keep changes evidence-driven: cite the lesson/finding that motivated each. No speculative gold-plating.

## Output
A small, cited set of skill/doc edits + version bumps + an index update, and a one-line "expected effect to
verify next run." The harness is now incrementally better; the loop continues.

## LEARN-feed emit sub-mode (β — emit-only, the primary fingerprint feed; D66/D72)
A **separate sub-mode** from the kata above (which edits skills). This one **only emits**: it mines the run's
durable decision artifacts into **synthesis pages** for the second-brain LEARN feed, so a future cognitive
fingerprint has raw material. It changes **no skill and no product code** — output goes solely to the feed dir.
Run it at IMPROVE / handoff time (engram seam E6), never as a per-task hook (keep it out of the one-shot budget).

- **Observe → synthesize → emit.** Read `DECISIONS.md`, `LESSONS-LEARNED.md`, the run's `GRILL-LEDGER.md`(s),
  and any `REVIEW-*.md`. Emit compact, cross-linked **synthesis pages** per the **wiki-synthesis output schema
  in `protocol/engram.md`** (Karpathy LLM-Wiki raw↔synthesis split;
  frontmatter `produced-by: loop`, `source:`, `scope:`; `[[wikilinks]]`; one page = one pattern). **Grill
  ledgers are a primary feed (D72)** — each resolved decision + the human's choice + rationale is fingerprint
  signal.
- **Zero CONSULT (structural).** This sub-mode **never reads a fingerprint back into planning or execution** —
  there is no CONSULT call-site. It is purely additive; emitting cannot influence any build (BC2).
- **Redaction is a HARD pre-write gate (C3).** Every page passes the **`kata-handoff` §7 redaction filter**
  (no secrets / keys / PII) and is **project-scoped** (`scope:`) **before any write**. Redaction failure ⇒ do
  not emit that page (fail-closed). This is the data-exfiltration / IP-leak surface — never bypass it. *(Maturity:
  §7 is a prose contract today; a structural redaction filter + test seam land with β-runtime — see `protocol/engram.md`.)*
- **No-op if unconfigured (BC1).** Emit only when `engram.learnFeed.dir` is set (`protocol/config.md`); absent
  ⇒ write nothing. Distinct from `engram.backend` (the CONSULT backend, still gated/off).
- **Output:** N synthesis pages written to `engram.learnFeed.dir` (provenance `produced-by: loop`), plus a
  one-line emit summary. No skill edits, no version bumps in this sub-mode.
