# protocol/escalation.md — the escalation payload schema

Structured escalation payload produced by an escalating worker. Machine state — JSON at `.kata/escalations/<task-id>.json`. The append-only board (`protocol/board.md`) carries only the one-line pointer `ESCALATE | <task-id> | <summary>`; the structured object lives here (keeps the board one-line).

## Payload

| Field | Type | Meaning |
|---|---|---|
| `taskId` | string | REQUIRED — the task identifier this escalation belongs to |
| `kind` | `"orchestrator-resolvable" \| "human-required"` | REQUIRED — classification of the escalation |
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

**Lifecycle:** orchestrator classifies/routes (orchestrator-resolvable → re-scope, never reaches a human; human-required → surfaces only when the frontier is blocked); the resolver writes `status: resolved` + `resolution`.

## Notes

Resolved payloads are the engram learning surface (future, GB10).
