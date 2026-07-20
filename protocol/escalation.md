# protocol/escalation.md — the escalation payload schema

Structured escalation payload produced by an escalating worker. Machine state — JSON at `.kata/escalations/<task-id>.json`. The append-only board (`protocol/board.md`) carries only the one-line pointer `ESCALATE | <task-id> | <summary>`; the structured object lives here (keeps the board one-line).

## Payload

| Field | Type | Meaning |
|---|---|---|
| `taskId` | string | REQUIRED — the task identifier this escalation belongs to |
| `kind` | `"orchestrator-resolvable" \| "research-needed" \| "human-required" \| "advice-requested"` | REQUIRED — classification of the escalation. `research-needed` = a must-deliver feature with **no in-plan solution** that needs grounded research before a decision (routes to [[kata-research]], loop-cognition RS-GB1). `advice-requested` = the worker wants a **scoped advisor consult** on a hard, narrowly-bounded question — async/non-halting, routed to the conductor's [[kata-advise]] dispatch (see *Advice-requested routing* below). The worker sets its best guess; the **orchestrator** makes the final routing call and may re-classify. |
| `decisionNeeded` | string | REQUIRED — clear statement of the decision that must be made |
| `optionsConsidered` | array | REQUIRED — list of options the worker evaluated before escalating |
| `agentRecommendation` | string | REQUIRED — the worker's recommended option with reasoning |
| `rationale` | string | REQUIRED — why the worker cannot proceed without resolution |
| `lockedDecisionInTension` | string | OPTIONAL — any locked decision that conflicts with the current situation |
| `costOfWaiting` | string | cost/impact of blocking on resolution |
| `costOfProceeding` | string | cost/impact of proceeding without resolution |
| `status` | `"open" \| "resolved"` | REQUIRED |
| `resolution` | string | OPTIONAL — written by the resolver when `status` becomes `"resolved"` |

## Lifecycle

**Producer:** the escalating worker writes it (status `open`).

**Lifecycle:** orchestrator classifies/routes — `orchestrator-resolvable` → re-scope, never reaches a human;
`research-needed` → dispatch a fresh-context, no-write [[kata-research]]; its findings pass the grounding gate
([[kata-evaluate]] injected-knowledge mode, never bypassed, D33); **gate-passed** findings are folded via a
**deliberate superseding re-plan** (audited), rejected findings are logged, can't-ground → re-classify
`human-required`; `human-required` → surfaces only when the frontier is blocked. The resolver writes
`status: resolved` + `resolution`.

## Red-sprint routing (sprint-cadence T4 — a failed gate is NOT a boundary)
In an incremental run, a **red sprint** (its `kata-evaluate` gate fails) routes through **this escalation
lifecycle** — it does **not** open a course-correct boundary. A boundary ([[kata-sprint]] G1–G4) is the
*scheduled, green* steering event; a red gate is an *unplanned failure* and is handled exactly as any blocked
frontier: the failing worker writes an escalation payload (kind per the usual classification — typically
`orchestrator-resolvable`, or `human-required` if the frontier is truly blocked), and the existing async
park/drain/hard-wait path (D51/D52) applies. **Never** present a red sprint as a clean boundary stop: the
boundary protocol assumes a green gate as its precondition (sprint-cadence §10 T4). Only once the sprint is
green does `kata-sprint` compose the report + boundary handoff and stop.

## Thrash → re-plan-candidate routing (fix-loop-hardening, L3/L6)

When the orchestrator's final-gate fix loop hits the thrash budget (per-area N=2 — the 3rd failure of one area —
or the run-level ceiling), it dispatches **`kata-diagnose` first** (cheap, no human) for a root-cause pass that
returns a **fix-problem vs plan-problem** verdict. This routing **reuses the existing `kind: "human-required"`**
— **no enum change** (L6). The thrash distinction is carried entirely in the `decisionNeeded` and `rationale`
fields of the escalation payload (e.g. `decisionNeeded: "re-plan candidate: area X oscillated N times after
kata-diagnose returned plan-problem — operator decision needed"` and `rationale` quoting the diagnose verdict).
A note that `kata-diagnose` ran first, and that only a **plan-problem verdict** surfaces to the human, belongs
in `rationale` (a fix-problem verdict means the loop was legitimately stuck, not that the plan is defective —
it is **not** a human interrupt). The escalation is **async-parked** per the existing contract — the task and
its DAG-dependents are parked; the frontier keeps draining. The resolver writes `status: resolved` +
`resolution` as usual. The `kind` enum values, payload schema, and async park/drain contract are otherwise
**unchanged** (L3/L6 — additive only; supersede-not-rewrite; never silent).

## Advice-requested routing (advisor-executor — S-9/S-10/S-23a)

A worker requests a **scoped advisor consult** by raising an escalation of kind `advice-requested` — the
sanctioned way for an execution/coding worker (or an in-harness **planner-worker**) to ask a hard,
narrowly-scoped question instead of burning another blind retry. It is **async/non-halting**: the standard
escalation park/drain contract applies **unchanged** — the requesting attempt ENDS, the task and its
DAG-dependents park, and the frontier keeps draining (D51/D52). It is **not** a course-correct boundary and
**not** a human interrupt.

- **Payload carries the question in `decisionNeeded`** — one narrowly-scoped question. `optionsConsidered`,
  `agentRecommendation`, and `rationale` carry the worker's attempts-so-far and why it cannot proceed
  unadvised. The payload schema is otherwise **unchanged** (additive; supersede-not-rewrite).
- **Only the conductor dispatches [[kata-advise]]** (S-1 — a worker never does; it *requests* via this
  escalation, mirroring the [[kata-research]] escalation-dispatch pattern). On routing, the orchestrator
  ([[kata-orchestrate]]) composes the `protocol/advice.md` **request** object from the escalation payload,
  dispatches `kata-advise` at the sibling gate's computed rung, and records the durable consult artifact at
  `.kata/advice/<task-id>-<n>.json` (`n` = 1-based per-task ordinal).
- **On payload return the task redispatches with the advice INLINED VERBATIM** under a marked `ADVICE`
  section of the redispatch brief — workers in isolated worktrees cannot read the main tree's `.kata/`, so a
  path reference would be unreadable; the JSON is embedded. The advised redispatch is a **NEW attempt** on the
  attempt branch, counted normally. The resolver writes `status: resolved` + `resolution` as usual.
- **Planner-workers** (in-harness plan/design authoring, dispatched during the freeze stage) raise
  `advice-requested` through this SAME machinery — **advanced + granted only** (runtime-gated); classified as
  the advisor's `advisor-planning-consult` event.
- **Cap: 2 worker-requested consults per task** (S-23a) — a surfaced NOTE beyond the cap; the advisor budget
  pool is still the outer bound. The per-task count is derived from the durable `.kata/advice/<task-id>-*.json`
  ordinals (no extra counter state). One pathological task can never drain the pool.
- **Legality is the advisor sibling gate, not this escalation:** a NO-FIRE (`advisor_status` — grant absent,
  mode excluded, …) ⇒ unadvised-proceed with a surfaced board NOTE, never a block. **Budget exhaustion is NOT
  an `advisor_status` NO-FIRE reason** — it is a separate `can_spend_advisor` denial (the spend gate, not the
  legality gate), which likewise ⇒ unadvised-proceed with a surfaced NOTE/lapse, never a block. Advice is
  **advisory, never authoritative** — it never changes a gate verdict, is never auto-applied, never expands
  the frozen goal (S-2). Full consult contract: `protocol/advice.md`; grant/budget: `protocol/config.md` (the
  `advisor` block). The `kind` enum's other values, payload schema, and async park/drain contract are
  otherwise **unchanged** (S-9/S-10 — additive only; supersede-not-rewrite; never silent).

## Notes

Resolved payloads are the engram learning surface (future, GB10).
