# protocol/advice.md — the advice payload schema (advisor consult)

Structured request/response payload for the **advisor consult** (the advisor-executor pattern). Machine
state — JSON at `.kata/advice/<task-id>-<n>.json`, where `n` is the **1-based per-task consult ordinal**
(the first consult on task `T4` is `.kata/advice/T4-1.json`, the second `.kata/advice/T4-2.json`, …). This
is the durable conductor-side record of one consult; the append-only board (`protocol/board.md`) carries
only the one-line pointers (a `NOTE` at request, a `DECISION` at disposition — see *Board-line contract*).

The advice payload is **machine-ingestible, agent-consumed, automated in-execution** (G-7): the response is
consumed by the AGENT (the conductor folds it into a redispatch brief, or the requesting planner reads it),
never a human-facing artifact on the hot path. The human sees an **after-action rollup** in the run
report / closeout, not this JSON.

Advice is **advisory, never authoritative** (S-2): it never changes a gate verdict, is never auto-applied,
never expands the frozen goal. The default-FAIL gate (`kata-evaluate` / `kata-inline-eval`) and every LOCKED
decision are untouchable by it. Advice serves; the executor decides.

## Payload

One artifact per consult, three top-level objects — `request` (composed by the conductor from the
escalation payload / hook context), `response` (returned by the `kata-advise` dispatch), and `meta`
(the conductor's disposition + provenance).

**Exactly ONE artifact file per consult** — `.kata/advice/<task-id>-<n>.json`, and **no sibling files**. The
shared once-guard, the per-task cap (S-23a), and the ordinal (`n`) derivation ALL glob `<task-id>-*.json`, so
a stray sibling (a `.tmp`, a `.bak`, a partial second write) **corrupts** the guard, the cap count, and the
next-ordinal computation at once. One consult writes exactly one JSON at its computed ordinal path and
nothing else.

The schema of record, field-for-field:

```json
{
  "request": {
    "taskId": "T4",
    "phase": "planning | execution | fix-loop",
    "question": "<ONE narrowly-scoped question>",
    "scopedContext": {
      "planTaskIds": ["T4"],
      "gateExcerpt": "<verbatim gate/eval failure excerpt>",
      "filePaths": ["tools/kata_models.py"],
      "attemptsSoFar": "<what was tried, per attempt>"
    }
  },
  "response": {
    "diagnosis": "<what is actually wrong>",
    "approach": "<recommended approach>",
    "risks": ["<risk>", "..."],
    "citations": ["<file:line / doc ref>", "..."],
    "sketch": { "lang": "python", "code": "<short illustrative sketch>", "nonAuthoritative": true }
  },
  "meta": {
    "event": "advisor-fail-threshold",
    "rungUsed": "fable",
    "disposition": "<free text: how the conductor disposed of the advice>",
    "ts": "<UTC ISO-8601>"
  }
}
```

### Field semantics

| Field | Type | Meaning |
|---|---|---|
| `request.taskId` | string | The task this consult belongs to; the `<task-id>` in the artifact path. |
| `request.phase` | `"planning" \| "execution" \| "fix-loop"` | The phase the consult fires in (the G-9 availability matrix decides where each is legal). |
| `request.question` | string | **ONE narrowly-scoped question** — the consult is scoped, anchor-relative, never an open-ended chat. |
| `request.scopedContext` | object | **The ONLY context the advisor reads** — "scoped context refs" ≡ exactly this shape, nothing else. `planTaskIds` (list), `gateExcerpt` (verbatim gate/eval failure text), `filePaths` (list), `attemptsSoFar` (what was tried, per attempt). |
| `response.diagnosis` | string | What is actually wrong (the advisor's read of the scoped context). |
| `response.approach` | string | The recommended approach — advisory input to the executor, never a mandate. |
| `response.risks` | string[] | Named risks in the recommended approach. |
| `response.citations` | string[] | `file:line` / doc refs grounding the advice (grounded in the supplied `scopedContext` only). |
| `response.sketch` | object, OPTIONAL | `{lang, code, nonAuthoritative: true}`. **Always `nonAuthoritative: true` — never applied verbatim; the executor owns implementation** (G-7). A consult may omit `sketch` entirely. |
| `meta.event` | string | The `ADVISOR_EVENTS` member that fired this consult (`tools/kata_models.py`). |
| `meta.rungUsed` | `string \| null` | The dispatched rung short-name (e.g. `"fable"`), or **`null`** for an arm-(a) inherit-at-anchor consult (no model parameter emitted; the anchor answered). |
| `meta.disposition` | string | Free text: how the conductor disposed of the advice (folded into the redispatch brief / handed to the requesting planner / noted-and-declined). |
| `meta.ts` | string | UTC ISO-8601 timestamp of disposition (injectable-clock sourced per the Determinism Doctrine). |

The `response.sketch` object is the S-15a union member: the response is `diagnosis / approach / risks /
citations` **plus an optional non-authoritative `sketch`** — never more. A reader diffing this schema
against the composed payload finds no divergence.

## Board-line contract

Two board lines per consult (`protocol/board.md` register), plus the spend line:

- **NOTE at request** (worker/conductor lateral info): the consult was requested — task, event, question
  summary. A NO-FIRE on any legality conjunct (`advisor_status`) is *also* a surfaced `NOTE` (the reason),
  and the loop proceeds **unadvised** — never a block.
- **DECISION at disposition** (orchestrator-only ruling): how the advice was disposed of — the `meta.disposition`
  summary. **Free text that MUST NOT begin `advisor:`** — a second `advisor:`-prefixed line would double-count
  or raise in the recount.
- **The per-consult spend/recount DECISION line** (§3.5): the SINGLE board `DECISION` beginning `advisor:`
  (`advisor: <consult-id> event <event>`), rendered by `kata_advisor.render_advisor_decision` — the durable
  recount trail `recount_from_advisor_decisions` reads (it parses ONLY `advisor:`-prefixed lines) to restore
  `used`/`byEvent`. Because a SECOND `advisor:`-prefixed line would double-count or raise, the disposition
  DECISION above is pinned to free text and never begins `advisor:`.

Reports and board lines **never gate** — they are the audit trail, not a control point (S-2).

## Producer / consumer

**Producer.** The **conductor** (`kata-orchestrate`) composes the `request` object — from an
`advice-requested` escalation payload (`protocol/escalation.md`) or from auto-hook context (the failure
threshold, reroll-grounding, or fix-loop-ceiling hooks) — dispatches `kata-advise` at the rung the sibling
legality gate computed (`advisor_status["rung"]`: `null` ⇒ OMIT the model parameter, arm (a) inherit-at-anchor;
a short-name ⇒ emit its `ID_MAP` id, arm (b)), folds the returned `response` into the payload, and writes
`meta` at disposition. **Only the conductor dispatches `kata-advise`** — a worker never does; it *requests*
via an escalation. `kata-advise` itself is fresh-context, **no-write**, and returns only the `response`
object.

**Consumer.** The **redispatch brief** (execution/coding workers in isolated worktrees cannot read the main
tree's `.kata/`, so the advice JSON is **inlined VERBATIM** under a marked `ADVICE` section of the brief — a
path reference would be unreadable) **or the requesting planner** (in-harness plan/design authoring). The
advice feeds the next attempt at the same worker rung; the advised redispatch is a NEW attempt on the
attempt branch, counted normally.

**Rollup (human surface).** The run **report / closeout** carries an **after-action rollup** built from the
telemetry `advisor` ledger key (`tools/kata_telemetry.py`) — consult count, per-event breakdown, budget
used/cap, lapses, and each consult's EV-1 outcome (`advised-pass` / `advised-fail-bumped` /
`advised-fail-ceiling`, or explicit `null` when a run ends before the pairing resolves). This is the only
human-facing view of the advice; the payload JSON stays on the machine hot path.

## Fail postures

- **Consult dispatch failure** ⇒ surfaced board `NOTE` + proceed **UNADVISED** — advice never blocks the
  loop (advisory ≠ gate). One-step lapse to unadvised-proceed, **never a ladder walk**; the consumed budget
  call stays consumed (grant-before-dispatch, S-19a).
- **NO-FIRE on any legality conjunct** (`advisor_status` returns `fires: False`) ⇒ unadvised-proceed with the
  surfaced reason as a board `NOTE` — never a consult-at-anchor-without-consent, never a block.
- **`response.sketch` is never applied verbatim** — `nonAuthoritative: true` is invariant; the executor owns
  implementation (G-7).
- **Budget exhaustion / grant lapse** ⇒ loud lapse (board `DECISION` + state `lapses[]` + handoff note); the
  loop proceeds unadvised to completion (never blocks).
- **The gate and closeout NEVER consult** (G-4): `kata-evaluate` / `kata-inline-eval` / closeout do not read,
  request, or produce advice — builder and judge never share an advisor (a D33-class extension of
  no-self-cert).

## Honesty / never-gates posture

Advice is **advisory, never authoritative** end to end (S-2, PD-2): it never changes a gate verdict, is never
auto-applied, never expands the frozen goal, and the `sketch` is never copied in verbatim. Every consult and
its budget draw are recorded (board `DECISION` lines + `.kata/state.json` `advisor` field), and the
after-action rollup states the true state — consults taken, budget spent, lapses, and each consult's outcome,
with honest `null` for a pairing a run ended before resolving. The advisor closes the blind-retry gap; it
never overrides the default-FAIL gate or a LOCKED decision.

## Cross-references

- `tools/kata_models.py` — `advisor_status` (the sibling legality gate), `advisor_rung_of` (anchor-relative
  rung), `ADVISOR_EVENTS` / `ADVISOR_EVENT_SITES` (the event registry).
- `tools/kata_advisor.py` — the pure spend/state/outcome engine + `render_advisor_decision` /
  `recount_from_advisor_decisions` (the board recount trail) + `ledger_fragment`.
- `protocol/escalation.md` — the `advice-requested` escalation kind a worker/planner raises to request a
  consult.
- `protocol/config.md` — the `advisor` block (legality/spend grant, budget pool, hooks).
- `protocol/board.md` — the `NOTE` / `DECISION` board register the consult writes to.
- `skills/plan/kata-advise/SKILL.md` — the advisor skill the conductor dispatches (fresh-context, no-write).
