# Sprint-cadence — plumbing research (pre-grill)

> **Status: RESEARCH (2026-06-11), pre-grill.** User-requested capability: a bootstrap-configurable toggle
> between **one-shot** execution (the current long-running loop) and **sprint** execution (break the project
> into GSD-style phases — "sprints" — execute one, emit output, let the user course-correct via grill, then
> iterate in the existing or a new session). This doc determines **where the toggle plumbs in**. The open
> design branches live in `GRILL-LEDGER.md` (answer those first; nothing here is frozen).

## 1. The feature in one paragraph

At bootstrap, the user picks a **cadence**: `one-shot` (today's behavior — FREEZE once, run the loop to the
final gate, output at the end) or `sprint` (the plan layer partitions the project into sprints; the loop runs
exactly one sprint to its gate, emits a durable output + handoff, **stops and returns control**; the user
course-corrects via a scoped grill; the harness re-enters — same or new session — and runs the next sprint).
It is *similar to a version-up* per sprint: sprint N's green gate is sprint N+1's regression baseline.

## 2. Spine compatibility (the load-bearing question)

The harness's identity is "one-shots complex tasks" (spine #2: *one-shot = no plan churn; re-planning is an
event, not a habit*). Sprint cadence is **compatible, not contradictory**, under one framing rule:

> **Each sprint is a one-shot.** The no-drift invariant (D1) holds *within* a sprint — frozen sprint plan,
> plan-guardian, escalate-don't-improvise, default-FAIL sprint gate. The sprint **boundary** is a
> *scheduled, deliberate* re-plan event (the course-correct grill) — exactly the "re-planning is an event"
> clause, with the event moved from exception-only (escalation) to also-scheduled (boundary).

Structural invariants (D33) are untouched: no-self-certification, no-drift, default-FAIL, DRY-by-pointer all
hold at every sprint gate. `kata-evaluate` runs unchanged at each sprint gate (D22 — the conformance floor is
what makes sprint N comparable to sprint N+1).

## 3. Where it plumbs (surface-by-surface)

| Surface | Change | Size |
|---|---|---|
| `protocol/config.md` (`kata.config`) | New **`cadence`** field: `{ shape: "one-shot" \| "sprint", ... }`. Shape + policy only — **sprint progression (current index, roadmap status) is machine state, not frozen provenance** (L3 single-writer; see GB-SC5). Default `"one-shot"` (today's behavior; absent ⇒ one-shot — backward compatible with D25's absent-config path). | S |
| `kata-bootstrap` | The configuration home the user asked for. (a) **Phase 1/2**: a cadence question, progressive-disclosure (GB13/D46) — sprint sub-fields appear only when `sprint` is picked; run-shape presets pre-fill a recommended cadence. (b) **Phase 0 re-entrancy**: detecting an existing config + open sprint state offers **"continue sprint N+1 / course-correct first / change cadence"** — this *is* the "iterate back through the harness in an existing or new session" path; it already half-exists (re-entrant detection, A3). | M |
| `kata-plan` (+ RUBRIC) | Sprint cadence activates the **roadmap layer** the planning engine already cites (GSD spec→roadmap→plan, DESIGN.md §planning-engine): GRILL freezes one whole-project DESIGN; the plan layer partitions into sprints — each sprint = its own task DAG + disjoint ownership + acceptance gate + **demonstrable output**. Detailed sprint plans are candidates for just-in-time freezing (GB-SC3). | M |
| `kata-orchestrate` | **Ideally near-zero.** Orchestrate executes *a* frozen plan to *its* final gate — if the plan it is handed is one sprint's plan, the existing loop, escalation, and final gate are the sprint loop/gate verbatim. Sprint *sequencing* should live above it (GB-SC4) to keep the dispatcher single and config-driven (D24d). | XS–M (hinges on GB-SC4) |
| `kata-handoff` | The **sprint-boundary artifact**: a two-way handoff (how to continue = next sprint, open corrections) + the user-facing sprint output/report (kata-report territory, D32 — synthesis of what the sprint built, gate evidence, demo pointer). Task-boundary handoff preference (D8) generalizes naturally to sprint-boundary. | S |
| `kata-grill` (tiered) | The **course-correct grill**: a *scoped delta-grill* between sprints — interrogate only (a) what sprint N's output calls into question and (b) the user's correction requests; bake accepted corrections into the DESIGN as **superseding** decisions (never silent rewrite). Tier choice = GB-SC6. | S |
| `kata-readiness` | Re-entrant detection extends to sprint state (open roadmap, sprint index, dirty-vs-gated boundary). | XS |
| `kata-evaluate` | **No change** (D22). Runs at every sprint gate. | 0 |

## 4. The version-up reuse (the user's instinct, confirmed)

"Will be similar to a version-up" holds structurally. For sprint N ≥ 2:
- The repo is no longer greenfield — it is **`target.kind: "existing"` with `baselineGate` = sprint N−1's
  full gate command** (the A4 regression contract, D50, verbatim).
- Footprint-scoped ownership (modified-files ∪ depth-1 reverse-dependents) + escalate-vs-defer protections
  (D50/D51) apply to sprint tasks unchanged.
- `kata-graph` is optionally bundled exactly as the version-up preset bundles it (D43/D53) — useful when the
  growing codebase makes later sprints token-heavy.
So sprint cadence is largely a **composition of shipped machinery** (A3 re-entrant bootstrap + A4 version-up
contract + handoff), not new machinery. The genuinely new pieces: the cadence config field, the roadmap/sprint
partition in `kata-plan`, the boundary artifact, and the course-correct delta-grill.

## 5. Prior art (oriented, not yet deep-researched)

- **GSD phases** — the named inspiration: discuss→plan→execute per phase, verify, milestone audits; local at
  `~/.claude/get-shit-done`. Sprint = phase with a hard gate + user checkpoint.
- **Scrum sprint/review/retrospective** — sprint = timebox with a demo (review) and a process-correct
  (retro); our course-correct grill fuses review+retro into one doc-grounded interrogation.
- **Anthropic long-running-agent harness** — checkpoint/commit discipline and two-way handoff already baked
  in (spine #5); sprint boundary = a human-visible checkpoint of the same kind.
- A deeper survey (Spec Kit iterative refinement, agent milestone-execution patterns) belongs in the spec's
  full RESEARCH pass if the grill surfaces a need — the plumbing determination above doesn't depend on it.

## 6. What this is NOT

- Not a new **mode** (modes trade quality/cost, D17/D24a) and not a new **run-shape** (presets over the mode
  axis, D34) — any run-shape can be sprinted. See GB-SC1.
- Not a task-queue/scheduler (rejected once already, D35).
- Not a relaxation of the conformance floor — every sprint ends at the same `kata-evaluate` gate.
