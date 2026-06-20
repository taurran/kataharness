---
name: kata-promote
description: >-
  The end-of-session HUMAN promotion gate for agent-distilled candidate skills (stage 2 of managed learning).
  A candidate the loop distilled and the grounding gate cleared stays sandboxed (experimental, scope:agent, not
  loaded universally) until a human promotes it here — experimental→stable + a scope bump — into the agent-skills
  toolkit. Use at session end to review candidates; honors the engram.autonomy dial (default always-human).
license: Apache-2.0
version: 0.1.0
category: meta
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Edit, Write, AskUserQuestion]
source: >-
  new (KataHarness original, loop-cognition ML / LC-GB3/GB4/GB5, D60-D69) — two-stage gate vs Hermes' no-gate
  instant-universal model (RESEARCH.md bake-off: borrow the closed loop, keep our human gate)
tags:
  - kata/meta
  - kata/module/meta
  - promotion
  - managed-learning
  - skill-lifecycle
---
# kata-promote — the human gate that lets a learned skill persist

Stage 2 of **managed learning**. The loop can *distil* a reusable pattern into a **candidate skill** mid-run
(stage 1, via [[kata-write-skill]]), but a candidate is **sandboxed** — `status: experimental`, `scope: agent`,
living in the agent-skills toolkit's `candidates/` area, **never loaded universally**. It persists into the
toolkit only when a **human promotes it here**. This is the deliberate brake on Hermes' autonomous
instant-universal model: an uncontrolled positive-feedback loop is the wrong shape for a one-shot harness
(RESEARCH.md). The grounding gate ([[kata-evaluate]] injected-knowledge mode, D33) already cleared the
candidate's *soundness* at distillation time; this gate decides *persistence + reach*.

## Where candidates live (config, first-run)
`agentSkills.dir` (`protocol/config.md`, first-run-configured) is the toolkit root. Candidates sit in
`<agentSkills.dir>/candidates/`; promotion moves a candidate into `<agentSkills.dir>/skills/<category>/`.
**These are OUTSIDE this repo's `skills/` tree** — the validator never sees them; the toolkit is the user's,
not KataHarness's. `kata-promote` MUST preserve `name == dir` on the move (D27).

## The promotion review (per candidate)
For each candidate in `candidates/`, present to the human (via the choice-or-text question pattern) and decide:
1. **Read the candidate** + its provenance: `provenance: agent-distilled`, `source:` (the run/lesson it came
   from), the grounding-gate verdict that cleared it, its `summary` (≤60 chars). Show what it does, why it was
   distilled, and where it would load if promoted.
2. **Human decides promote / keep-sandboxed / reject:**
   - **Promote** → set `status: experimental→stable` (or `beta`), bump `scope:` (`agent → coding-agent` or
     `universal` per the human's call), move into `<agentSkills.dir>/skills/<category>/` preserving `name==dir`,
     and register it in the toolkit index. Conform to [[STANDARDS]] §1 + the agent-distilled discriminators (§1.3).
   - **Keep sandboxed** → leave it in `candidates/` for a future session (supersede-not-rewrite; it can mature).
   - **Reject** → move to a `candidates/rejected/` area with a one-line reason (never silent-delete; C5 decay).
3. **Record** the decision (promoted/kept/rejected + reason) so the next session and the engram LEARN feed
   (E6) see it — promotion choices are a strong preference signal (D72).

## Progressive autonomy (the engram.autonomy AND-gate — L6/LC-GB4)
`kata-promote` reads `engram.autonomy` (`protocol/config.md`; default **`always-human`**):
- **`always-human`** (default, today) — every candidate stops for a human decision. No exceptions.
- **`assisted`** — the engram pre-recommends promote/keep/reject; the **human still decides**.
- **`auto-when-confident`** — may auto-promote a candidate **only when ALL hold**: opted-in ∧ fingerprint-mature
  ∧ high-confidence ∧ precedented (a closely-matching prior promotion). **Novel / low-confidence /
  LOCKED-adjacent candidates ALWAYS stop for the human** (C2/C4). Every auto-promotion is logged in the audit
  surface (C6).
**Non-negotiable:** autonomy may replace the human's *judgment*, **never the grounding gate** (D33/L2) — a
candidate that did not clear grounding is not promotable at any autonomy level. This is gated on a mature engram
(D9/D56); until then the dial sits at `always-human` and this skill is purely a human review. Reuses the
sprint-cadence `auto-continue-while-green` pattern + engram invariants C2/C4/C5/C6.

## Boundary (vs neighbors)
- vs [[kata-write-skill]]: write-skill **authors** the candidate (stage 1, the *how* of making it); promote
  **decides persistence** (stage 2, the human gate). vs [[kata-improve]]: improve edits the **repo's** skills
  cross-run; promote governs the **agent-distilled toolkit** skills. No overlap.
