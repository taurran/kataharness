---
name: kata-sprint
description: >-
  Own the boundary between sprints in an incremental run — the ONE place steering happens. Stop-side: when a
  sprint gate is green, compose the report + boundary handoff and STOP. Resume-side: run the G1-G4 boundary
  change-control protocol (explicit approval, drift-labelling, post-approval adversarial sweep, snowball guard),
  freeze the next sprint plan, and hand back to the orchestrator. Use only for delivery.shape == incremental;
  it composes existing skills and never reimplements them, and never touches the sprint-blind orchestrator.
license: Apache-2.0
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Write, Edit, AskUserQuestion]
model: fable
source: new (KataHarness original — sprint-cadence D80; the thin boundary coordinator, GB4-C)
tags:
  - kata/coordinate
  - kata/spine
  - sprint
  - boundary
  - change-control
---

# kata-sprint — the boundary coordinator

A **thin** coordinator for the boundary between sprints (sprint-cadence D80). The steering tenet:
**each sprint is a one-shot (no-drift holds within it); the boundary is the only place steering happens.**
`kata-sprint` runs **only** when `delivery.shape == "incremental"` (`protocol/config.md`).

> **Composes, never reimplements (BC2).** It orchestrates existing skills — [[kata-report]], [[kata-handoff]],
> [[kata-evaluate]], [[kata-review]], [[kata-grill]] (delta-mode), blast-radius — and **never edits or bypasses
> [[kata-orchestrate]]**, which stays *sprint-blind*. Delivery-awareness lives only in HANDOFF-phase routing.

## Two sides of a boundary

### Stop-side — close a green sprint
1. **Verify the sprint gate is green** — read the [[kata-evaluate]] verdict (the default-FAIL gate, D22, never
   re-computed here). A **red** sprint is **not** a boundary — it routes through escalation (`protocol/escalation.md`
   red-sprint routing, D51/D52). Only proceed when green.
2. **Compose the report** — [[kata-report]] writes the one-page per-sprint report into the tier-2 durable trail.
3. **Compose the boundary handoff** — [[kata-handoff]] writes the boundary-variant handoff (gate numbers + sprint
   index + any drift-labelling), per `protocol/handoff.md`. A boundary handoff **supersedes** a coincident
   self-handoff (T1) — one artifact, not two.
4. **STOP** — hard-stop for the human (G1), unless `delivery.boundary == "auto-continue-while-green"` AND the
   full AND-gate below holds.

### Resume-side — the G1-G4 Boundary Change-Control Protocol
**Structural invariants — never tiered, never bypassed (D33).** Ceremony scales with reach; default is light.

- **G1 — explicit approval gate.** The boundary hard-stops; **no correction applies without explicit user
  approval** (`AskUserQuestion`). Approval is **never inferred** from state. The *only* exception:
  `delivery.boundary == "auto-continue-while-green"` **AND** every one of
  **{ gate green ∧ no open escalations ∧ no pending corrections ∧ no G3 tertiary drift }** holds (an AND-gate;
  the moment any is false ⇒ stop and ask). A boundary CONSULT may **never** flip `stop → continue` while that
  set is not fully satisfied (sprint-cadence §9, subordinate to the GB6 AND-gate).
- **G2 — drift labelling.** Classify each requested change by **reach**: *next-sprint-plan* /
  *roadmap-reshape* / *DESIGN-amendment*. A change that is **drift from a frozen artifact** must be flagged and
  needs a **separate explicit** "yes, I am changing frozen X" — you may not fold a frozen-artifact change in
  under a general approval. Steering may reshape **remaining** sprints (roadmap layer) but **never the active
  sprint's plan** (D1, immutable within the sprint).
- **G3 — post-approval adversarial sweep.** After approval, run a **fresh-context [[kata-review]]** (D15) over
  the approved set to catch second/third-order drift the user did **not** ask for. On finds → **re-present for
  another approval round, capped at a PINNED 2 rounds** (a safety backstop, **NOT** a tunable). Still snowballing
  after 2 rounds ⇒ escalate to G4.
- **G4 — snowball guard.** The predicate is **solely** `blast-radius(approved corrections)` vs the
  **remaining-roadmap footprint**. Exceeds it ⇒ this is a **re-scope, not a tweak** → flag for a deliberate
  roadmap re-plan / new run. **There is no numeric threshold** (removed for D18 reproducibility) — blast-radius
  vs footprint only.
- **B5 — DESIGN-amendment gate.** A boundary change that amends the **project DESIGN** (north star) requires the
  **same fresh-context [[kata-review]] SHIP** the initial freeze demanded — a DESIGN amendment is never cheaper
  than the freeze. Supersede-by-appended-decision, never silent rewrite.
- **Safety spine:** *when in doubt, stop and make the human decide; never silently expand.*

## After the boundary
Compose [[kata-grill]] **delta-mode** (only the changed branches) over any approved roadmap reshape, then run the
**roadmap layer + tier method** ([[kata-plan]] `ROADMAP.md` → `RUBRIC.md`) to **freeze the next sprint's plan
just-in-time**, and hand that frozen plan to [[kata-orchestrate]] — which proceeds exactly as it does for a
one-shot run (it never knew it was in a sprint). Record every approved change as a **superseding decision /
roadmap amendment** in the tier-2 git trail (auditability, no repudiation).

## What it must NOT do
- **Not** edit, wrap, or special-case [[kata-orchestrate]] (it stays sprint-blind — the diff must prove it, BC2).
- **Not** reimplement grill / review / report / evaluate logic — **compose** them.
- **Not** apply any correction without G1 approval (except the explicit GB6 AND-gate).
- **Not** introduce a numeric threshold into G4, or make the G3 2-round cap configurable.
- **Not** steer the **active** sprint — only remaining sprints, only at the boundary.
