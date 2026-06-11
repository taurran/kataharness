# Sprint-cadence — Grill Decision Ledger

> Running ledger for the sprint-cadence design grill (per `kata-grill` RUBRIC). Grounded in `RESEARCH.md`
> (read it first — it carries the plumbing map and the spine-compatibility framing). **Status: ALL branches
> OPEN (2026-06-11)** — recommendations are on file; the user answers these to converge. Per L7/L8: options +
> a recommendation each, free-text always welcome.

## Steering tenet (apply to every branch)
**Each sprint is a one-shot.** No-drift (D1) holds within a sprint; the boundary is the *scheduled* re-plan
event. Any answer that lets a sprint drift mid-flight, or lets the boundary silently rewrite LOCKED
decisions, is out.

---

## SC-GB1 — Where does cadence sit architecturally? **(OPEN)**
The toggle must not collide with the frozen axes: mode (D24a, quality/cost), run-shape (D34, presets), effort
(D19, orthogonal overlay).
- **A (recommended): a third orthogonal dial**, peer to the effort overlay — `kata.config.cadence`. Any
  run-shape can be sprinted (a sprinted greenfield, a sprinted version-up); run-shape presets *pre-fill* a
  recommended cadence (individual ⇒ one-shot; version-up ⇒ ask). Precedent: D19 (effort), D37 (orthogonality
  → composability).
- **B: a new run-shape** (`sprint-project`). Rejected-leaning: run-shapes are presets *over* axes (D34), and
  cadence composes with every existing shape — making it a shape forks the preset table.
- **C: a module.** Rejected-leaning: modules add skills (D20); cadence changes *loop topology*, not the
  skill set.

## SC-GB2 — Naming **(OPEN)**
- **A (recommended): `cadence: "one-shot" | "sprint"`.** "Sprint" per the user's naming. CONTEXT.md must
  disambiguate **sprint** (a cadence unit = one gated one-shot increment) from **phase** (already taken: the
  loop phases GRILL/FREEZE/…/IMPROVE) and from GSD's "phase". _Avoid_: "execution mode" (collides with Mode),
  "milestone" (GSD collision).
- **B:** `loopShape` / `executionStyle` / other. Free-text welcome.

## SC-GB3 — Planning depth: what freezes when? **(OPEN)**
- **A (recommended): frozen project DESIGN + frozen sprint ROADMAP up front; detailed sprint PLANs frozen
  just-in-time** (sprint N+1's task-level plan is frozen only after sprint N's course-correct). The
  course-correct can then actually steer — corrections land *before* the next freeze, so they are never
  drift. The roadmap (sprint list, goals, gates) is stable; only the active sprint carries a task DAG.
- **B: freeze everything up front** (all sprint plans). Maximum rigidity; the course-correct degenerates to
  accept/abort because corrections would churn already-frozen plans — undercuts the feature's purpose.
- **C: freeze nothing beyond the active sprint** (no roadmap). Loses the whole-project DESIGN grounding and
  makes sprint sizing ad-hoc.

## SC-GB4 — Who owns sprint sequencing? **(OPEN — biggest structural branch)**
The sprint loop is: plan sprint → orchestrate to gate → boundary artifact → STOP → course-correct →
next sprint.
- **A (recommended): re-entrant `kata-bootstrap` is the sequencer; `kata-orchestrate` stays sprint-blind.**
  Orchestrate executes the (one-sprint) frozen plan to its gate exactly as today — zero topology change to
  the weight-5 spawn hub (preserves D24d: single config-driven dispatcher). The boundary artifact
  (handoff + report) ends the run; re-entering bootstrap detects sprint state and routes
  continue/course-correct/change-cadence. Costs: the "loop" spans sessions by design — which matches the
  user's spec ("existing or a new session").
- **B: `kata-orchestrate` gains an outer sprint loop.** One session can run sprint→pause→sprint; but it
  bloats the spine invariant skill, and "pause for the user mid-skill" is exactly the long-running-session
  failure mode D8 exists to avoid.
- **C: a new thin coordinate skill (`kata-sprint`)** owning only the boundary (gate→report→handoff→stop +
  the course-correct hand-back). Clean single-responsibility; one more skill. Viable as A's companion if the
  boundary logic outgrows bootstrap prose.

## SC-GB5 — Where does sprint progression state live? **(OPEN)**
- **A (recommended): split.** `kata.config.cadence` holds the frozen *shape + policy* (provenance,
  reproducibility). The *roadmap status* (sprint index, per-sprint gate evidence, open corrections) is
  **machine coordination state** under `.kata/` (single-writer, plan-guardian-owned — L3), with the
  human-facing trail in the durable sprint reports. Config stays append-stable; state churns.
- **B: everything in `kata.config`.** Rejected-leaning: progression churn in a frozen provenance file
  invites the stale-config class the load-guard (D45) exists to catch.

## SC-GB6 — The course-correct: mechanism + depth **(OPEN)**
- **A (recommended): a scoped delta-grill** — interrogate only (a) what sprint N's output put in question,
  (b) the user's correction requests; accepted corrections bake into the DESIGN as **superseding decisions**
  (never silent rewrite — same rule as DECISIONS.md). Tier: default the run's grill tier, droppable to
  essential for small corrections (cross-tier pick, D24c).
- **B: full re-grill each boundary.** Cost-prohibitive at the cadence's whole point (cheap iteration).
- **C: no grill — free-text notes only.** Loses doc-grounding; corrections become drift vectors.
- Sub-question: when the user has **no** corrections, does the boundary still hard-stop for confirmation, or
  can the user pre-authorize "auto-continue while green"? (Recommend: ask at bootstrap —
  `cadence.boundary: "always-stop" | "auto-continue-while-green"`; default always-stop.)

## SC-GB7 — Sprint sizing: who cuts the boundaries, and to what bar? **(OPEN)**
- **A (recommended): planner-derived, user-confirmed at FREEZE.** `kata-plan` proposes the sprint partition
  (vertical, demonstrable slices — each sprint independently green + produces *visible* output worth
  course-correcting on); the user confirms/adjusts the roadmap before it freezes. Bar per sprint: full gate
  green + a demo-able artifact + a one-page report.
- **B: user dictates sprint boundaries up front.** Fine as an override; weak as the default (the planner
  sees the DAG).
- **C: fixed-size timeboxes.** Scrum-literal; meaningless for an agent loop (cost ≠ wall-clock).
- Sub-question: minimum/maximum sprint count guidance? (e.g. a 2-task project should refuse sprint cadence
  and recommend one-shot — cadence has a floor where it's pure overhead.)

## SC-GB8 — Sprint N≥2 = version-up? **(OPEN — confirm the reuse)**
- **A (recommended): yes, structurally.** Sprint N's gate command becomes sprint N+1's
  `target.baselineGate`; footprint ownership + full-suite-green regression contract (D50) and async
  escalation (D51) apply verbatim; `kata-graph` optionally activates when the codebase grows past the point
  where digest-grounding pays (à-la-carte, D43). This makes sprint cadence mostly **composition of shipped
  machinery**.
- **B: sprints stay greenfield-shaped throughout.** Simpler config, but forfeits the regression contract —
  sprint N+1 could silently break sprint N's work, which is the exact "don't break other aspects" failure
  the user named.

## SC-GB9 — Composition with bake-off + version-up run-shape **(OPEN — scope check)**
Orthogonality says a sprinted bake-off (N variants *per sprint*) and a sprinted version-up (sprints over an
existing repo) are both expressible. **Recommend:** declare them valid combinations in the contract but
**defer their execution paths** (Spec B isn't built; A4 composition needs its own check) — same
configurable-now/executable-later pattern as GB5/A3. Confirm or trim.

## SC-GB10 — Sequencing vs D16 **(OPEN — the meta question)**
D16 (planning-varied A/B) is the v0.1 validation gate and the standing next step; its targets are *small
one-shottable* projects — **one-shot cadence; sprint cadence is not a D16 dependency.**
- **A (recommended):** answer this ledger + freeze the sprint-cadence DESIGN now (cheap, docs-only), **build
  after D16** — the unvalidated-grill rework-exposure argument that killed KG-first (L8) applies to building
  (not to specing) this too.
- **B:** build sprint cadence first. Costs the same rework exposure the 2026-06-10 adversarial review
  rejected for Option D.
- **C:** spec *and* build later; only log the capture. Loses tonight's momentum on a user-named priority.

---

## Convergence
All ten branches answered → promote to D-numbers → freeze `DESIGN.md` (this spec dir) → PLAN → build (per
SC-GB10's answer). Per the RUBRIC, the grill does not grade its own convergence — the freeze gets a
fresh-context check before build.
