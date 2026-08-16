---
name: kata-design-doc
description: >-
  Compile a grill's decision ledger + glossary into a single FROZEN design contract — the locked source of
  truth both planning and execution serve. Use after grilling, before task-planning, to turn resolved
  decisions into a specific, testable, freeze-ready DESIGN with explicit acceptance and locked decisions.
license: Apache-2.0
version: 0.3.1
category: plan
status: beta
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: adapted-from mattpocock/skills {to-prd} + superpowers brainstorming + GSD spec-phase
tags:
  - kata/plan
  - kata/spine
  - freeze
  - design-contract
  - spec
---

# kata-design-doc — freeze the decisions into a contract

FREEZE turns the grill's output into the **single document execution serves**. It does not introduce new
decisions — every decision must already be resolved in the ledger ([[kata-grill]]). If the design-doc author
finds an unresolved branch, that is a signal the grill was incomplete — it is not decided here. Dispatched as
a `design-author` worker (see Precondition below) it has no `AskUserQuestion` channel and so cannot literally
"return to grilling" itself; instead it raises the **existing** `human-required` escalation
(`protocol/escalation.md`) and the task parks. The conductor — which still holds the human channel — is the
one that returns to grilling on the worker's behalf.

## Precondition — the ledger passed its adversarial gate
Do not freeze a ledger that hasn't passed [[kata-grill]]'s fresh-context convergence check ([[kata-review]]).
Freezing an un-audited ledger just launders an under-specified grill into a "frozen" contract. No gate → back
to grilling.

**Dispatched as `design-author` (DESIGN §4.2, dispatch-authoring spec, KH-T13).** Once the grill ledger has
converged, the conductor session dispatches this skill as role `design-author`
(`kata_dispatch.build_brief`/`dispatch`, `tools/kata_dispatch.py:43`/`:219`) — `sandbox="write"`, in its own
[[kata-worktree]] worktree — instead of running it in the conductor's own context
(`protocol/orchestration.md`: the conductor gates, it does not author under its own gate). The conductor
applies `protocol/authored-artifact-gate.md`'s six-row rubric (KH-B42) to the returned `DESIGN.md` before
writing it into the main tree.

## Inputs
The decision ledger (`resources/DECISION-LEDGER.md` shape), the glossary ([[kata-context]]), any ADRs, and
the original spec/requirements.

## The DESIGN contract MUST contain
1. **Requirements** it satisfies (traceable IDs where they exist).
2. **Where it lives** — the exact components/files/insertion points it touches (grounded in the code).
   **Reuse-claims pre-flight (`protocol/reuse-claims.md`):** Before writing any "reuses / composes / via the
   existing X" or "already exists" claim — in §2 or §5 — follow `protocol/reuse-claims.md`: grep/read X and
   cite the concrete `file:line`, or label it a NEW capability. Do not freeze a phantom claim.
3. **LOCKED decisions** — each resolved branch from the ledger, restated as a numbered locked decision with
   its rationale. Mark any tunable knobs explicitly (locked *structure*, tunable *value*).
4. **The integrity/edge cases** surfaced during grilling and how they're handled.
5. **Backward-compatibility contract** — what existing behavior must be preserved, stated as a checkable claim.
6. **Acceptance criteria** — phase-level, **default-FAIL and runnable**: tests/build/security gates with real
   numbers, plus behavioral assertions (incl. the drift-magnet checks). "Done" is defined here.
7. **Test seams / testability** — the highest seam(s) at which the work will be tested + any testing
   decisions, so the EXECUTE TDD phase builds to them (mattpocock to-prd).
8. **Dependency Manifest** — write `kata.dependencies.json` from the external dependencies enumerated
   during grilling, one entry per `protocol/dependencies.md` schema, with all fields filled. This manifest
   is approved at freeze (not at build time; D29); the PRE-FLIGHT phase provisions the approved set before
   the loop launches.

## Quality bar (freeze-readiness)
- **Trade-offs over verdicts** (BMAD): each LOCKED decision records the trade-off and the rejected
  alternative, not just the pick — favor boring, reversible technology where the call is close.
- Every LOCKED decision is specific enough to execute without re-deciding (the two-builders-can't-diverge test).
- Acceptance criteria are **falsifiable** — each maps to something a fresh-context evaluator can run/read.
- Nothing in the doc is "TBD". A TBD means the grill isn't finished.
- The doc is the *control*: if it feeds an A/B or multiple executors, it must be identical for all of them.

## Output
A `DESIGN.md` (SCREAMING-KEBAB, durable). Hand to [[kata-plan]] for the task-level execution plan. Once
written, the DESIGN is **frozen** — changes are deliberate re-freezes, not edits-in-flight ([[kata-orchestrate]]).

**Two-part output contract when dispatched as `design-author`:** (1) write the `DESIGN.md` file to the
brief's one `owned_files` path; (2) emit, as your FINAL message, the completion JSON
`{ "designPath": <path>, "verdict": "ready"|"needs-rework", "deviations": [<str>, ...] }` — the shape
`tools/kata_dispatch.py`'s `normalize()` validates (DESIGN §4.3). `verdict` is your own self-assessment; it
is never a substitute for the conductor actually reading the file (`protocol/authored-artifact-gate.md` row
2). `deviations` names any place you extrapolated beyond, or found ambiguous in, the cited ledger — every
entry is independently checked against the ledger by the conductor, never accepted at face value (row 5).
Once the conductor has gated and written this `DESIGN.md` into the main tree, it dispatches the appropriate
`kata-plan-<tier>` skill as role `plan-author` the same way (DESIGN §4.2).

## Advice-request escalation (advisor-executor, S-17a — ADVANCED + granted ONLY; runtime-gated)
When dispatched in-harness as a planner-worker, on a **genuinely hard design question** you MAY request a
scoped Fable-tier advisor consult by raising an **`advice-requested`** escalation (`protocol/escalation.md`) —
question in `decisionNeeded`, async/non-halting (the standard park contract). **Only the conductor dispatches
[[kata-advise]]** ([[kata-orchestrate]] § Advisor consult, event `advisor-planning-consult`); the advice
returns **INLINED VERBATIM** in your redispatch brief under a marked `ADVICE` section. The advice is
**advisory, never authoritative** (S-2) — it never resolves a LOCKED decision or expands the frozen goal; an
unresolved *decision branch* is still a signal to **return to grilling**, not to advice. This affordance is
**ALIVE only on an ADVANCED run with an existing advisor grant** — on any other run the conductor's
`advisor_status` gate NO-FIREs and you simply proceed unadvised. This instruction rides **every tier variant
because tier ≠ mode** (D24c cross-picking); it is runtime-gated by the grant, not by the doc tier.

## Depth by mode
The active mode is set in `kata.config` and passed in the task by the orchestrator. Do not guess or infer it.

- **Essential** — minimum viable artifact: requirements, LOCKED decisions, and acceptance criteria only.
  Omit the backward-compat contract and test-seams sections unless they are obviously load-bearing for the
  task. Suitable for a PoC or cheap one-shot where grill depth was also Essential.
- **Standard** — the full skill as written above (all seven DESIGN contract sections, full quality bar).
  Default when no mode is specified.
- **Advanced** — Standard **+** fuller backward-compat analysis (enumerate every preserved invariant with a
  checkable claim), threat notes (flag attacker-reachable surfaces from the integrity/edge-case section),
  and explicit test seams for each acceptance criterion (not just the highest seam).
