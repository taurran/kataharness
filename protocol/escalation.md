# protocol/escalation.md — the escalation payload schema

Structured escalation payload produced by an escalating worker. Machine state — JSON at `.kata/escalations/<task-id>.json`. The append-only board (`protocol/board.md`) carries only the one-line pointer `ESCALATE | <task-id> | <summary>`; the structured object lives here (keeps the board one-line).

## Payload

| Field | Type | Meaning |
|---|---|---|
| `taskId` | string | REQUIRED — the task identifier this escalation belongs to |
| `kind` | `"orchestrator-resolvable" \| "research-needed" \| "human-required"` | REQUIRED — classification of the escalation. `research-needed` = a must-deliver feature with **no in-plan solution** that needs grounded research before a decision (routes to [[kata-research]], loop-cognition RS-GB1). The worker sets its best guess; the **orchestrator** makes the final routing call and may re-classify. |
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

## Notes

Resolved payloads are the engram learning surface (future, GB10).
