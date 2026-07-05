# Context-autonomy glossary additions (staged for CONTEXT.md at branch time)

**smart zone** — the operating band of an agent's context window: above the *context floor* (enough
grounding loaded — kata-orient's three tiers complete — to produce well-grounded output) and below
the *rot ceiling* (the utilization beyond which quality degrades). All threshold policy in the
context-autonomy design targets keeping agents inside this band. Coined by the operator, 2026-07-04.
_Avoid_: "safe zone," "healthy context" (fuzzy).

**handoff** — a session-boundary durable artifact (`.planning/HANDOFF.md` family, protocol/handoff.md),
produced by kata-handoff in one of three kinds: `manual`, `self`, `boundary`. The ONLY thing called a
handoff. _Avoid_: calling dispatch briefs, worker final reports, or escalation payloads "handoffs" —
those are agent-exchange artifacts with their own contracts.

**startup load** — the conductor-authored dispatch payload (brief + packed orientation attachments)
measured as a fraction of the worker's window, estimated at dispatch time by the conductor. Excludes
worker-side read-ins (those are the worker's own budget consumption). >0.30 ⇒ over-briefing WARN;
>0.40 ⇒ over-briefed dispatch, split/slim mandated at plan time.

**work quantum** — the guaranteed processing budget of a dispatch: ≥40pp of the worker window above
startup load (TUNABLE). A plan-time sizing target — a well-sized task completes inside one quantum
and never rotates. Runtime: a soft budget with completion-awareness (finish chunk → checkpoint →
continue if the remainder fits under the 0.80 hard cap, else return a continuation report).

**continuation report** — a worker's return artifact when its task exceeds the quantum: last
checkpoint anchor + what remains + what was learned (the reasoning that commits don't carry). Input
to the pt-N+1 fresh dispatch (reuses the M4 kill+fresh-dispatch primitive). _Avoid_: "partial
handoff."

**trigger fraction** — the conductor's rot-ceiling threshold: default 0.70 of the HOST-REPORTED
effective window (gauge `total_tokens`, post-cap), one config key, shown in bootstrap's advanced
drawer, never interactively asked. Subagents have NO trigger fraction — theirs is derived
(startup + quantum).

**gauge** — the machine-readable context-utilization signal read by the conductor at wave
boundaries. On Claude: the statusline bridge file (superset schema incl. total_tokens when kata's
chained wrapper writes it). Stale (>300s) or absent ⇒ the deterministic rotation fallback, never
"assume fine."

**backstop** — the host's own compaction mechanism (the sole reset mechanism on Claude), recommended
(never silently set) to fire at trigger + gap. Kata owns the schedule and durability; the host owns
the act. _Avoid_: "backup," "the env var" (the settings.json key `autoCompactWindow` is the
recommendation vector).

**premium offer** — the mode==advanced, preflight-approved above-anchor elevation (e.g. Fable above
an Opus anchor) for critical + coding work classes only; recorded in kata.config `models.premium`
with the granting mode; lapses on mode change; failed premium dispatch OMIT-inherits, never re-offers.
_Avoid_: "+1" in prose (write "above-anchor premium").

**auto-context (rotation)** — the whole context-autonomy behavior as a run posture: unconditional
for one-shot delivery shape; ON-by-write-time-default with opt-out for incremental shapes;
absent-at-load ⇒ OFF (BC for pre-v0.2.1 configs).
