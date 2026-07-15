# GRILL-LEDGER — subagent-monitor (standard tier, 2026-07-14, operator present)

> Subject: the kata statusline gains (1) the main-session model and (2) a stylized subagent/crew
> tracker in the D162 theme — per-worker role, model, effort, liveness. Operator-initiated
> ("evaluate… listing the model kataharness is using in the main session… a stylized subagent
> sub worker tracker… the job of the subagent… the model each is running… if its running
> thinking"). Feasibility assessment preceded the grill (payload model.display_name live-proven;
> subagents invisible to the host payload; live thinking-state unobservable).

### D1 — scope: claude now; codex parked for MindBridge alignment; kiro later · LOCKED
- **Question:** what does "works on all (claude/codex/kiro)" mean for this run?
- **Provenance:** operator first picked "core-everywhere + honest legs", then re-scoped mid-grill
  (interrupt): "I am working on the same thing in mindbridge loop, and I intend to bring over
  full context… so we can align here. We should focus on claude now (codex is also installed
  here), and then we can worry about kiro later."
- **Decision:** **This run builds the agnostic core (pure renderer + layout goldens — the
  portable guarantee) + the claude binding + live smoke.** Codex research/binding is PARKED
  until the operator imports MindBridge-side context for alignment; kiro is LATER (not installed
  here — a live smoke is impossible today, named honestly). The earlier "honest legs" answer is
  SUPERSEDED by this re-scope, not contradicted.
- **Edges:** the core renderer sits behind a narrow contract (`render` over a normalized roster
  view) so the incoming alignment can re-skin without rework (memory `mindbridge-hands-off`
  update 2026-07-14).
- **Doc-baked:** this entry; DESIGN §frame.

### D2 — main-session model in the segment · LOCKED
- **Question:** can the segment show the conductor's model truthfully?
- **Provenance:** feasibility assessment — the host statusline payload carries
  `model.display_name` on every tick (live-proven 2026-07-13: the D162 render repro consumed
  `{"model":{"display_name":"Fable 5"}}`).
- **Decision:** **Yes — a dim model shortname chip after the gauge** (`… 9% │ fable │ …`),
  derived from the payload, absent when the field is absent (degrade golden, EV-1).

### D3 — crew tracker via the conductor-written dispatch roster · LOCKED
- **Question:** the host payload carries zero subagent info — where does crew truth come from?
- **Provenance:** feasibility assessment; the conductor knows role/model/effort/task at dispatch
  (D131 resolver output); board CLAIM/PROGRESS carries liveness but not role/model.
- **Decision:** **`.kata/dispatch.json` roster — single-writer (the conductor), entry written at
  dispatch, closed at gate; the renderer reads it fail-soft** (absent/corrupt ⇒ no crew chip,
  never an error). **Stale-out is render-time and display-only** via the existing
  `livenessDeadline` primitive (default 10 min) against the entry's last-heartbeat timestamp
  (board PROGRESS corroborates) — a stale chip renders hollow (▱), it never gates or kills.
- **Edges:** crashed conductor ⇒ roster goes stale ⇒ chips hollow ⇒ next run-start rotation
  clears it (same lifecycle class as the board).

### D4 — the honesty limit: no live "thinking" signal · LOCKED
- **Question:** operator asked for "if its running thinking whatever."
- **Provenance:** feasibility assessment (PD-2): a subagent's live reasoning state is not
  observable from outside the host — no surface exposes it.
- **Decision:** **The chip shows the dispatch-time reasoning-effort tier (L/M/H) + liveness
  (▰ fresh heartbeat / ▱ stale) — never a fabricated "thinking now" indicator.** Recorded as the
  truthful substitute, accepted by the operator in the assessment exchange.

### D5 — layout: per-worker chips · LOCKED
- **Question:** chip format under the one-line constraint.
- **Provenance:** operator picked "Per-worker chips" from the two mocked options.
- **Decision:** `⚒ <Role>·<model>·<effort><liveness>` per live worker (e.g. `C·opus·H▰`),
  dim/theme-matched, truncating at 3 chips + `+N`; segment slot ABSENT entirely when the roster
  is empty/absent (idle render = gauge + model + run-hint only). Layout goldens byte-pin:
  idle · 1 worker · 3 workers · many (+N) · stale-chip.

### EV-1 — Elevate: the degrade-golden family · LOCKED
- **Recommendation:** extend the golden suite with byte-pinned DEGRADE renders — payload missing
  `model` (today's exact segment, no model chip) · roster absent (gauge+model only) · roster
  corrupt (same as absent, never an error render) · all-stale roster (hollow chips, never
  dropped). Grounding: the D162 build's v2-F6 rule (a malformed meter omits ONLY the meter —
  never blank the segment), generalized to the new failure lattice.
- **Decision:** Accepted — the failure modes are byte-pinned alongside the happy layouts; the
  segment can never blank or crash from bad crew data.
