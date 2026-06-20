---
date: 2026-06-19 (loop-cognition COMPLETE + sprint-cadence DESIGN FROZEN; handoff for a fresh/compacted session)
branch: master (local only — no remote yet)
green: validator 29 skills / 0 errors · pytest 27 passed · Snyk 0 (re-confirm before building)
tags: [handoff, loop-cognition-complete, sprint-cadence-frozen, next-build-sprint-cadence, full-context]
authored-for: kata-orient (the Orientation tie-in — sections below map to the three orientation tiers)
---

# HANDOFF — KataHarness — 2026-06-19 (loop-cognition done · sprint-cadence frozen · build sprint-cadence next)

> **Fresh/compacted session: read in order, confirm green, then resume at §4 THE PLAN.** Everything below is
> durable + committed. This handoff is authored to the `kata-handoff` **Orientation tie-in** so it maps straight
> into `kata-orient`'s tiers: **§1 read-in order → orientation *context* · §2+§4 state/next → *volatile* · §6
> open decisions → the human-required questions.** (We built that read-side skill this session — see §3 AO.)

## 1. Read-in order  *(orientation: CONTEXT tier)*
1. `AGENTS.md` · 2. `docs/DESIGN.md` (charter; carries the Priming-and-Grill section) · 3. `docs/STANDARDS.md`
   (frontmatter v2 §1 + **§1.3 agent-distilled discriminators**; versioning hold A §3) · 4. `.planning/STATE.md`
   (read the CURRENT box at the top) · 5. **`.planning/DECISIONS.md` — focus D70–D85 (the current spine)** ·
6. `.planning/LESSONS-LEARNED.md` (**L11** is the pivot) · 7. `protocol/engram.md` (engram contract + the
   wiki-synthesis schema) · 8. `.planning/specs/loop-cognition/{DESIGN,GRILL-LEDGER,RESEARCH}.md` (FROZEN, BUILT) ·
9. **`.planning/specs/sprint-cadence/{DESIGN,GRILL-LEDGER}.md` (FROZEN — the next build)** ·
10. `.planning/specs/priming-and-grill/DESIGN.md` (FROZEN, BUILT).
⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated, harness-injected).

## 2. State *(orientation: VOLATILE tier)*
- Branch `master`, local-only (no remote). Tip after this session = the sprint-cadence freeze commit (`79716ca`)
  + this handoff. **29 skills / 0 validator errors · pytest 27 · Snyk 0.** Confirm before building:
  `cd tools && uv run pytest -q  &&  uv run python validate_skills.py`.
- Versioning hold **Policy A**: every skill stays `0.1.0` until v0.1 ships (then bump-on-modify).

## 3. What shipped this session (all committed, reviewed-SHIP) *(orientation: CONTEXT tier)*
The whole **loop-cognition** trio + its prelude, then the **sprint-cadence** freeze:
- **D71 Priming-and-Grill** (`808df3f`) — grill is an OPTIONAL human certainty layer over the priming prompt;
  the **autonomous-reliability floor is the always-on substrate** (default-FAIL + RS + `kata-defer` assumption
  log). Dial `skip|light|standard|full` = `tiers["kata-grill"]` (D73). NEW `kata-defer`.
- **β LEARN feed** (`8ac6740`, D74) — `kata-improve` emit-only sub-mode → Karpathy wiki-synthesis pages
  (`produced-by: loop`); zero CONSULT, redaction-gated; schema in `protocol/engram.md`.
- **RS** (`88a964f`, D75) — NEW `kata-research`: escalation-routed (`research-needed`), fresh-context **no-write**;
  the **L2 grounding gate** (injected-knowledge mode in `kata-evaluate` + `kata-review` RUBRIC, never bypassed
  D33) gates findings → GROUND-only fold via superseding re-plan.
- **AO** (`34ee3ab`, D76) — NEW `kata-orient` (spine, read-only): **smart, task-type-aware launch orientation** —
  the receiving half of handoff. Three tiers + vertical nested-AGENTS.md rollup + kata-graph lateral adjacency
  pointers; contextually-derived pointers+callouts from standard markdown; smart questioning routed (answer-inline
  / research-needed→RS / human→grill). `protocol/orientation.md`; `kata-handoff` **Orientation tie-in** (this
  file uses it). **This is the AO skill — the "other end of handover."**
- **ML** (`1eaf181`, D77) — NEW `kata-promote`: stage-2 **human** promotion gate for agent-distilled candidate
  skills; `engram.autonomy` AND-gate (default always-human); grounding gate never bypassed. ⇒ **loop-cognition
  COMPLETE.**
- **Full validation stack on RS+AO** (`7cfe2f5`) and a separate deep RS+AO+β+D71 validation: both legs SHIP.
- **sprint-cadence DESIGN FROZEN** (`79716ca`, D78–D85) — see §4.

## 4. THE PLAN — build sprint-cadence next *(orientation: VOLATILE tier — the immediate action)*
sprint-cadence (incremental delivery) is **DESIGN FROZEN** (freeze-gate HOLD→SHIP, all 7 must-fixes applied;
D78–D85). **It builds next — ungated** (GB10's D16-first lock dissolved by D70). **The build needs its own
task-level PLAN (`kata-plan`) + human approval before code** — it is the LARGEST surface yet:
- **NEW `kata-plan` roadmap layer** (D85 — "the feature's largest build surface", net-new): partition the DAG
  into prime-frame-sized sprints; emit the roadmap artifact `{ projectDesignRef, frozenAt, sprints:[{ id, goal,
  gateCommand, demonstrableArtifactType, dagSeamRationale, dependsOn[] }] }`; per-sprint just-in-time freeze.
- **NEW `kata-sprint`** (thin boundary coordinator, D80) — runs the **G1–G4 Boundary Change-Control Protocol**
  (explicit approval · drift-labelling · post-approval `kata-review` sweep [cap=2] · G4 snowball = blast-radius
  vs remaining-roadmap footprint). Composes, never reimplements.
- **NEW `kata-report` v1** (D85/D2) — the per-sprint one-page report = minimal `kata-report` (D32 v1).
- **EXTEND:** `kata-readiness` (sprint-state detect + rebuild tier-3 cache from git trail), `kata-selfhandoff`
  (prime-frame trigger — D83 supersedes D8's % threshold), `kata-handoff` (boundary artifact); `protocol/{config
  (delivery field),state (tier-3),handoff,escalation}.md`. **REUSE verbatim:** `kata-orchestrate` (stays
  **sprint-blind**, D24d), `kata-evaluate`, `kata-review`, `kata-grill` delta-mode, blast-radius, D50 version-up.
- **⚠ Build-time grounding (D83):** the prime-frame token numbers for Fable 5 / Sonnet are `[TUNABLE]` — verify
  **real current model windows + recommended utilization at build time** (WebSearch), do NOT pin from memory.
- **After sprint-cadence:** the endgame — **dogfood version-up on KataHarness itself** (build fully → full tests
  → self-improve), which also exercises the deferred-runtime BACKLOG items.

## 5. Suggested next skills *(orientation: task-type hint)*
`kata-plan` (draft the sprint-cadence build PLAN) → present for approval → then subagent-driven build gated on
validator+pytest, with a fresh-context `kata-review` (D15) before done. Method: Fable 5 on judgment (Opus
fallback — Fable unavailable all session) / Sonnet on mechanical + workers; Snyk on new Python; supersede-never-
rewrite; no skill self-certifies (L8); held at 0.1.0 (Policy A).

## 6. Open decisions for the human *(orientation: human-required questions)*
- **Approve the sprint-cadence build** (or re-plan) — it's the biggest build; plan-then-approve.
- The grill↔RS↔AO machinery is **forward-wired but partly inert** until exercised on a real multi-module target
  / mature engram (BACKLOG: AO module-rollup+lateral-adjacency; β structural redaction filter; CONSULT + full
  `engram.autonomy`). Confirm these stay deferred to the dogfood/endgame.
- Git remote before any public release (still local-only).

## 7. Redaction
No secrets / keys / PII in any artifact this session. Nothing to redact.
