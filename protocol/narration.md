# protocol/narration.md — narration contract (phase→plain-language map)

The narration contract for the **conversation channel** — the human-facing voice emitted by the harness
during a run. This is **distinct from the board/state firehose** (`protocol/board.md`, `.kata/board.md`):
the board carries every granular machine event for the dashboard; narration carries the human-meaningful
milestones and alerts in the conversation itself.

> **Reference:** DESIGN §3 L6 (WS-3 frozen). Implemented per PLAN Slice B (wave 1).

---

## 1. Phase→plain-language map

For each internal loop activity, the right column is the phrasing the narrator uses **in the conversation**.
The left column exists **only for the narrator's reference** — internal activity labels are **never surfaced
to the user**; the user sees only the plain-language phrasing.

| Internal activity (narrator reference only — never shown to user) | Plain-language phrasing (what the user hears) |
|---|---|
| Grill (planning / pressure-test) | "Working out and pressure-testing the plan against your goal." |
| Freeze (plan lock) | "Locking the plan so it can't drift." |
| Pre-flight (dependency provisioning) | "Getting the tools it needs ready." |
| Execute — parallel workers | "Building the pieces — N in parallel." (substitute the actual worker count for N) |
| Evaluate (fresh-context gate) | "Checking the work honestly against a fresh pair of eyes." |
| Handoff (durable artifact commit + two-way hand-back) | "Wrapping up and handing the result back to you." |
| Escalation (human-required fork) | "I've hit a fork I want your call on." |
| Loop-back (version-up re-entry carrying prior context) | "Starting the next improvement pass, carrying what we learned." |

**Usage rules for the map:**

- Use the plain-language phrasing as the basis; adapt wording naturally for context, but preserve the
  *intent* of each phrase (the meaning must match the activity).
- Never expose the internal label even as a parenthetical or "technical name." If a user asks what stage
  the run is in, answer in the plain-language terms of the map.
- For parallel workers, always substitute the real count — "Building the pieces — 3 in parallel" is clear;
  "Building the pieces — N in parallel" is a template, not output.
- Handoff and loop-back are distinct: handoff ends a pass; loop-back *begins* the next one.

---

## 2. Milestone-cadence rule

**Narrate at meaningful boundaries; stay quiet between.**

The harness narrates when a phase transition or a meaningful milestone actually occurs — not as a progress
stream. The `改善型` dashboard, the statusline, and the append-only board (`protocol/board.md`) carry the
granular live view for whoever wants to watch; they are the firehose, not the conversation.

**What counts as a meaningful boundary:**

- A phase transition: entering or completing one of the activities in the map above.
- A significant parallel-work event: all workers dispatched, all workers done (not individual completions
  unless one is notable — e.g. a worker found something the user cares about).
- The final verdict: what the fresh-context evaluation returned.
- The handoff: the run is complete and ready for the user's decision.

**What does not warrant a narration message:**

- Individual PROGRESS heartbeats (board TYPE `PROGRESS` — dashboard only).
- Internal state updates, board appends, or file writes the user has no action on.
- Routine forward motion within a phase (a worker is running; the plan has not changed).

The principle: **trust, not spam.** A user who sees a message from the harness should know it signals
something worth reading. Silence is not neglect — it is the dashboard's job to show the live view.

---

## 3. Breakthrough-alert rule

**Decisions, escalations, and critical failures surface in the conversation immediately and unmissably,
regardless of routine quiet.**

This invariant is **never tiered** and admits no exceptions. It is the narration-channel analogue of the
board's `ESCALATE`/`BLOCK` invariant (see `protocol/board.md`), adapted for the conversation:

| Trigger | Narration action |
|---|---|
| A decision or escalation requires the user's call (a fork the harness cannot resolve alone) | Deliver the escalation payload in the conversation immediately. Do not wait for a phase boundary. Do not let it queue behind routine narration. |
| A critical failure (the run cannot proceed; a spine invariant is at risk; a security-relevant finding) | Surface it in the conversation immediately, with the finding and the path forward. |
| The fresh-context evaluation returns NEEDS_WORK | State the verdict plainly in the conversation. Do not soften or delay it. |

**"Immediately and unmissably"** means: as the first message after the event is known, without holding it
until a later boundary. The user must be able to act.

**This invariant is never tiered** — it is a structural invariant (CONTEXT.md: never tiered, D33-class).
No mode, no run configuration, and no cadence setting can suppress a breakthrough alert.

The dashboard and board carry their own parallel signals (board `ESCALATE`/`BLOCK` → orchestrator
`DECISION`); the conversation breakthrough is **additive and independent** — not a substitute for the board
signal, and the board signal is not a substitute for this one.

---

## 4. Honesty guard

**Narration describes only what is actually happening.**

The narrator MUST NOT imply capabilities that are not wired in the running harness. Two categories are
explicitly forbidden today:

| Forbidden narration | Why it is forbidden |
|---|---|
| "I'm researching this myself" or any phrasing implying a standing in-loop research call-site is active | The research-mode RS path is not a standing in-loop call-site; its use is conditional and must not be implied as automatic. Narrating it as automatic is an overclaim. |
| "I'm learning from this" or "I'll remember your preference" implying live engram CONSULT is active | Engram CONSULT is gated off today (D9/D56/D74). The LEARN feed emits only — zero CONSULT. Narrating CONSULT as live recreates the L8-class overclaim the DESIGN explicitly forbids. |

**The test:** before writing a narration phrase, ask "Is the thing I am describing actually happening right
now in this run?" If the answer is "it might happen later when a gated capability is enabled," do not write
the phrase.

This guard exists because overclaiming wired autonomy is itself an inflation signal — the kind
`kata-slop-check` catches in other contexts. The harness's own narration must be free of it.

**What the narrator CAN say instead:**

- Instead of "I'm researching this myself" → describe the specific tool or step actually being taken, or
  stay silent until a meaningful boundary is reached.
- Instead of "I'll remember your preference" → say nothing, or if the preference is being recorded in a
  durable artifact (e.g. the grill ledger), describe that artifact honestly: "I've noted that in the plan."

The honesty guard does not prohibit warmth or plain language; it prohibits implied capabilities. Plain,
warm, accurate narration is always the goal.
