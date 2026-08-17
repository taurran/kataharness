---
name: kata-sprint
description: >-
  Own the boundary between sprints in an incremental run — the ONE place steering happens. Stop-side: when a
  sprint gate is green, compose the report + boundary handoff and STOP. Resume-side: run the G1-G4 boundary
  change-control protocol (explicit approval, drift-labelling, post-approval adversarial sweep, snowball guard),
  freeze the next sprint plan, and hand back to the orchestrator. Use only for delivery.shape == incremental;
  it composes existing skills and never reimplements them, and never touches the sprint-blind orchestrator.
license: Apache-2.0
version: 0.2.0
category: coordinate
status: beta
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Write, Edit, AskUserQuestion]
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

> **Invoked by:** re-entrant [[kata-bootstrap]] (Phase 0b) when [[kata-readiness]] reports a **gated** sprint
> boundary — bootstrap is the boundary router (D80); [[kata-orchestrate]] stays sprint-blind and cannot dispatch
> here. The resume-side hands the next frozen sprint plan back to [[kata-orchestrate]].

> **Composes, never reimplements (BC2).** It orchestrates existing skills — [[kata-report]], [[kata-handoff]],
> [[kata-evaluate]], [[kata-review]], [[kata-grill]] (delta-mode), blast-radius — and **never edits or bypasses
> [[kata-orchestrate]]**, which stays *sprint-blind*. Delivery-awareness lives only in HANDOFF-phase routing.

## Phase awareness — the boundary is a recorded position, not a remembered one

A boundary is a stage transition, so it emits PHASE events through the seam `phase()` function,
`kata_dispatch.phase(kata_dir, "<msg>")`: **close** the finishing sprint's
`EXECUTION wave=<n>` on the stop-side, and **open** the next sprint's `EXECUTION wave=<n+1>` when
the resume-side hands the next frozen plan to [[kata-orchestrate]]. Per-wave open/close matching is
enforced — closing a wave that was never opened is a refusal, recorded as a DENY event.

**Which sprint is in flight is READ from the cursor, never remembered** —
`kata_dispatch.phase_state(cursor)` returns `{"open": [...], "closed": [...], "runClosed": bool}`,
and [[kata-readiness]]'s sprint-progression verdict rebuilds `{sprintIndex, gateStatus, boundary}`
from the git-committed tier-2 trail. Both are recorded fact. A conversational recollection of "we
just finished sprint 3" is not a position and never satisfies this check.

**In-session sequencing here is CURSOR-TRACKED, NOT dispatch-gated (TM-B3):** this skill invoking
[[kata-report]], [[kata-handoff]], or [[kata-plan]] is the conductor reading its own instructions —
PHASE events, no dispatch record. The **fresh-context [[kata-review]] dispatched at G3 is a real
agent launch** and therefore mints through `kata_dispatch.mint(governs=…, role="reviewer", …)` like
any other judge.

## Two sides of a boundary

### Stop-side — close a green sprint

1. **Verify the sprint gate is green — from the PERSISTED evaluate VERDICT RECORD, never a
   conversational value.** The stop-gate's input is the seam-authored `VERDICT` line on the cursor
   plus its **REQUIRED** JSON payload (`{verdict, evidencePointers[], judgeDispatchSeq, runId}`),
   written by `kata_dispatch.capture()` when the judge returned. Three refusals, all fail-closed —
   the gate defaults to NOT-a-boundary:
   - **No persisted VERDICT record ⇒ REFUSE.** An absent record is the §5.3 absent-records refusal
     path: it is not "assume green", not "ask the agent what the verdict was", and not a re-run of
     the gate here (the verdict stays [[kata-evaluate]]'s, D22 — never re-computed on this side).
     A `VERDICT` line whose payload pointer is missing was refused at write time and is refused
     again on read; there is no half-recorded verdict.
   - **Identity check ⇒ the record must belong to THIS run.** Route the gate artifact through
     `run_result.gate_evidence_is_creditable(result_json, expected_sha, expected_run_id)` —
     equivalently `evidence_is_current(..., expected_run_id=<live runId>, require_run_id=True)`.
     Evidence is credited only if the **SHA is fresh AND the `runId` matches EXACTLY**. A
     prior-sprint or sibling-arm artifact sitting at the same SHA is refused (`wrong-run`); an
     artifact with no `runId` is refused (`evidence-missing-run-id`); a caller that cannot say which
     run is live is refused (`unknown-expected-run`). A SHA-only verdict is **not** sufficient.
   - **Run-membership law, verbatim:** ancestor / prior-run artifacts are legal as *inputs*, never
     as gate evidence. The sanctioned cross-run path is this boundary consuming a child's recorded
     `DOWN`/`VERDICT` summary, which carries the child's own `runId`.

   A **red** sprint is **not** a boundary — it routes through escalation (`protocol/escalation.md`
   red-sprint routing, D51/D52). Only proceed when the persisted record says green.
2. **Compose the report** — [[kata-report]] writes the one-page per-sprint report into the tier-2 durable trail.
3. **Compose the boundary handoff** — [[kata-handoff]] writes the boundary-variant handoff (gate numbers + sprint
   index + any drift-labelling), per `protocol/handoff.md`. A boundary handoff **supersedes** a coincident
   self-handoff (T1) — one artifact, not two.
4. **Close the wave on the cursor** — `phase(kata, "close EXECUTION wave=<n>")`.
5. **STOP** — hard-stop for the human (G1), unless `delivery.boundary == "auto-continue-while-green"` AND the
   full AND-gate below holds. In the auto-continue arm, "green" is the same persisted-record test
   as step 1 — the AND-gate never reads a remembered verdict.

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
one-shot run (it never knew it was in a sprint) — emitting
`phase(kata, "open EXECUTION wave=<n+1>")` at the handoff. Record every approved change as a
**superseding decision / roadmap amendment** in the tier-2 git trail (auditability, no repudiation)
**and as a `DECISION` line on the cursor** — a boundary ruling the cursor did not record did not
happen for any downstream fold.

## What it must NOT do
- **Not** edit, wrap, or special-case [[kata-orchestrate]] (it stays sprint-blind — the diff must prove it, BC2).
- **Not** reimplement grill / review / report / evaluate logic — **compose** them.
- **Not** apply any correction without G1 approval (except the explicit GB6 AND-gate).
- **Not** introduce a numeric threshold into G4, or make the G3 2-round cap configurable.
- **Not** steer the **active** sprint — only remaining sprints, only at the boundary.
- **Not** treat a conversational verdict, an agent's recollection, or a stale-runId artifact as the
  sprint gate. The persisted VERDICT record with its identity check is the only input.
- **Not** hand-write a PHASE or VERDICT line onto the cursor — those come from
  `kata_dispatch.phase()` / `capture()`.
