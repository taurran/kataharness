# adapters/ADAPTER-CONTRACT-M4.md — the M4 inline-evaluator adapter contract

Canonical, **normative for every `adapters/*`** platform that wants to run Freeze/Float **M4** at
`inlineEval: on`. M4 (the inline evaluator / reroll — the smaller loop) moves detection down to the
checkpoint chunk and recovery down to reroll-from-last-good-commit. This file states the *platform
capabilities* M4 depends on, and the *degrade* that follows when a platform lacks one. Reference:
[`DESIGN.md`](../.planning/specs/inline-eval-m4/DESIGN.md) **M4-L2** (chunk = checkpoint commit; recovery
= kill + fresh dispatch), **M4-L7** (tier policy — strictly-below-anchor), **M4-L9** (ACP/file-only
visibility). BC governs: `inlineEval` absent ⇒ `off`; a platform that provides neither primitive still
runs `telemetry` and `off` unchanged — the contract below gates only the `on` posture's consuming legs.

## The two required primitives (M4-L9)

An adapter supporting `inlineEval: on` MUST provide **both**:

- **(a) Worker board-append at the integration root (S3b).** The worker context can append `CLAIM` /
  `PROGRESS` / `DONE` / `NOTE` / `Kata-Checkpoint:`-bearing commits that are visible from the shared
  `.kata/board.md` at the **integration/target-repo root** (not the per-task worktree's `.kata/`) — the
  S3b shared-root rule ([`protocol/board.md`](../protocol/board.md)). This is what makes every checkpoint
  a durable, orchestrator-readable event.
- **(b) Session kill + fresh-dispatch, confirmed-dead.** The platform can **kill** a dispatched worker
  session and **dispatch a fresh one** from an anchor commit. The kill MUST be **confirmed-dead before any
  fresh dispatch** — a kill *failure* ⇒ escalate `kind: human-required`, **never** proceed-and-redispatch
  over a possibly-live worker (the double-writer hazard; imports the contract-supersede abort-failure rule
  verbatim, M4-L2). Reroll needs nothing else — **no mid-session injection is required by design**.

A third primitive is added for context autonomy (v0.2.1), **conformance-only** — it governs conductor
respawn, not the `inlineEval: on` gate above (which still requires **both** (a) and (b)):

- (c) session-respawn — the platform's OUTER SHELL (host feature, cron wrapper, or human; never the
  in-session agent) can end the conductor session and start a fresh one that re-anchors from the newest
  durable handoff (SessionStart-equivalent injection or a documented manual step). Absent ⇒ degradation:
  conductor writes/refreshes the handoff and PROMPTS THE OPERATOR to rotate (universal fallback);
  unattended runs on such platforms are bounded by one session window, surfaced at preflight. Governs
  CONDUCTOR sessions only — worker attempt topology is out of scope; LD7 remains named-DEFERRED.

Plus the R-40 sentence: Absent primitive (b), budget-overrun enforcement degrades to worker compliance +
livenessDeadline escalation, surfaced at preflight.

**Claude binding (the only live leg in v0.2.1):** host compaction + SessionStart(compact) =
the (c)-equivalent. SR-14 scope guard honored — (c) does not silently absorb LD7.

**Absent either primitive ⇒ that platform runs M4 at `telemetry`** — record-only, no scheduler/ladder/
kill. This is **per-platform**, decidable at run start from the known platform set (precondition 0): a
mixed run keeps `on` where the primitive exists and degrades only the platforms that lack it (M4-L9c /
M4-L10). Every such degrade is **surfaced** — a board `NOTE` + a run-start (or discovery-point)
conversation line — and **recorded as a `degraded` ledger entry** `{scope, reason}` (row schema v2, D142
Amendment #4). Never silent.

## Signals are durable artifacts; the scheduler POLLS

Every M4 signal is a **durable artifact written at checkpoint time**, never an in-session observation:

- the **`Kata-Checkpoint:` commit trailer** on the checkpoint commit (the per-chunk verify record, A1-Q2);
- the board `PROGRESS` / `CLAIM` / `DONE` lines (the slack + concurrency substrate);
- the ladder **`DECISION`** line the orchestrator writes per ladder event (carrying the checkpoint sha).

The scheduler **POLLS these git/board artifacts at checkpoint granularity** — it does not stream, watch, or
observe a live session. It follows that **no M4 feature may require streaming output, mid-session
injection, or shared session memory.** A platform that offers only file-and-process visibility (the ACP /
Quick-driven case) is therefore **first-class**: primitives (a) and (b) are the whole dependency surface,
and both are satisfiable by "append to a shared file" + "kill a process, start a process."

## Kill bindings (per platform, M4-L2 as amended)

The kill primitive (b) binds to a concrete platform mechanism where the ladder uses it:

| Platform | Kill binding |
|---|---|
| **Claude host** | the host's **background-task stop** on the dispatched worker |
| **LD6 off-host** | **OS process kill** of the background subprocess |

**LD7 host-fallback mid-task is DEFERRED (L19 sweep MED-4 — named, not silent):** a platform failure that
triggers the LD7 host fallback re-dispatches the task as a fresh host session; its interaction with the
attempt-branch topology, checkpoint-index continuity, and confirmed-dead semantics for the abandoned off-host
process is NOT specified by this contract version — until it is, a run mixing `inlineEval: on` with off-host
workers should treat an LD7 fallback as a `reroll`-equivalent (new attempt branch, index continuity, kill
confirmed) or degrade that platform to `telemetry`.

Cross-model, LD6 workers are identical to the host case — subprocess kill *is* the primitive; there is no
new adapter surface for off-host workers. A platform with **no** kill binding has no primitive (b) ⇒ it
degrades to `telemetry` per the rule above (surfaced, recorded).

## Tier resolution for the inline evaluator (M4-L7)

The inline evaluator dispatches **strictly below anchor, never at anchor** — it is frequent, scoped work,
and anchor-tier inline eval is the overhead spiral in disguise. Its tier is resolved **ONLY** through the
D131 resolver (`kata_models.resolve()`), landing wherever the mode×family **economy** cell lands
(`kata_inline_eval` is registered `SKILL_WORK_CLASS = "economy"`). Two carve-outs make the "never anchor"
invariant unreachable-by-construction:

- **Resolution-time `None`** — an absent `models` block, unknown family/anchor, or a zero-step / floor-
  clamped cell ⇒ `resolve()` returns `None` ⇒ **skip the eval and degrade the run to `telemetry`,
  surfaced** — never a silent anchor-tier eval.
- **R2 carve-out** — the R2 dispatch-failure fallback terminus (≤2 step-downs then OMIT-inherit) does
  **NOT** apply to the inline-eval slot. On chain exhaustion, or a `fallback_chain` of `[None]` (the
  resolved economy model is already the family floor), **do NOT omit-and-inherit** — same route: skip the
  eval + degrade M4 to `telemetry`, surfaced. **Never OMIT-inherit for the inline-eval slot.**

The inline evaluator NEVER dispatches without an explicit below-anchor model id. Anchor stays reserved for
the M4-L5 grounding pass, `human-required` escalations, and the unchanged final gates (M4-L8).
