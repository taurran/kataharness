# Sprint-cadence — Grill Decision Ledger

> Running ledger for the sprint-cadence design grill (per `kata-grill` RUBRIC). Grounded in `RESEARCH.md`
> (read it first — it carries the plumbing map and the spine-compatibility framing). **Status: IN PROGRESS
> (grill resumed 2026-06-15)** — SC-GB1 RESOLVED; SC-GB2–10 OPEN. Per L7/L8: options + a recommendation each,
> free-text always welcome.

## Steering tenet (apply to every branch)
**Each sprint is a one-shot.** No-drift (D1) holds within a sprint; the boundary is the *scheduled* re-plan
event. Any answer that lets a sprint drift mid-flight, or lets the boundary silently rewrite LOCKED
decisions, is out.

---

## SC-GB1 — Where does cadence sit architecturally? **(RESOLVED — A)**
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

> **RESOLVED 2026-06-15 → A**, with a sharpened framing (user: "own separate knob").
> - **Decision:** cadence is its **own orthogonal config axis** (`kata.config.cadence`), separate from
>   mode / run-shape / effort. It is best described not as an "overlay like effort" (effort = depth-per-step)
>   but as a **pacing / stopping axis** that *gates latent spine behavior*: picking `sprint` activates the
>   roadmap layer in `kata-plan`, the boundary artifact in `kata-handoff`, and the delta-grill re-entry in
>   `kata-bootstrap` — behavior those spine skills already contain. `kata-orchestrate` stays sprint-blind
>   (sets up GB4-A).
> - **Rationale:** B forks the preset table (would need sprint-greenfield, sprint-version-up, sprint-batch…);
>   C is wrong because cadence adds no skill, it changes loop topology. A composes freely with every existing
>   axis (cheap sprint, thorough one-shot, sprinted version-up, sprint+high-effort) — that free composition is
>   the positive evidence for "orthogonal axis, not a shape."
> - **Edges/clarification (load-bearing):** one-shot is NOT "no awareness between sections." It is the
>   long-running agent in its purest form — `kata-selfhandoff` (spine #5 / D8) hands off **agent→itself** at
>   task boundaries / context thresholds, re-anchored on the frozen plan, automatically and invisibly. So
>   *both* cadences preserve inter-section context via the same two-way-handoff machinery. The difference is
>   **who triggers the boundary and who it's for:** one-shot = agent-triggered, for the agent's continuity,
>   no human steering until the end; sprint = scheduled human-facing boundary that ALSO emits a report and
>   waits for a course-correct. Sprint layers human checkpoints onto machinery one-shot already uses.
> - **Provenance:** user confirmed "own separate knob" 2026-06-15; clarification that one-shot already
>   self-hands-off accepted as the answer to "shouldn't one-shot have handoffs between sections too?"

## SC-GB2 — Naming **(RESOLVED — `delivery: "one-shot" | "incremental"`; unit = sprint)**
- **A (recommended): `cadence: "one-shot" | "sprint"`.** "Sprint" per the user's naming. CONTEXT.md must
  disambiguate **sprint** (a cadence unit = one gated one-shot increment) from **phase** (already taken: the
  loop phases GRILL/FREEZE/…/IMPROVE) and from GSD's "phase". _Avoid_: "execution mode" (collides with Mode),
  "milestone" (GSD collision).
- **B:** `loopShape` / `executionStyle` / other. Free-text welcome.

> **RESOLVED 2026-06-15 → B (custom).** "cadence" rejected as the knob name; user wanted an
> increment / execution-pattern flavor.
> - **Decision:** knob = **`delivery`**; settings = **`one-shot` | `incremental`**. The **unit** of
>   incremental delivery = a **sprint** (one increment = one sprint). `one-shot` is kept (harness identity,
>   "one-shots complex tasks"). The setting is named `incremental` (not `sprint`) deliberately — it frees the
>   axis from Scrum-timebox rigidity while "sprint" stays the familiar word for one work-unit.
> - **Rationale:** "delivery" is plain, collision-free, and describes the execution pattern (how finished work
>   reaches the user — all at the end vs in reviewable increments). Naming the *setting* `incremental` (vs
>   `sprint`) means we never inherit Scrum's clock/standup/velocity connotations even though we keep "sprint"
>   as the unit noun.
> - **Glossary-ready terms (promote to CONTEXT.md at DESIGN freeze):**
>   - **Delivery** — the orthogonal pacing axis (GB1): `one-shot` vs `incremental`. _Avoid_: cadence (dropped),
>     mode (collision, D17/D24a), execution-mode.
>   - **One-shot** (delivery value) — run continuously to the final gate; output at the end; inter-section
>     handoffs are agent→self (`kata-selfhandoff`, spine #5/D8), automatic, no human checkpoint.
>   - **Incremental** (delivery value) — the project is built in sprints: run one sprint → gate → report →
>     human course-correct → next.
>   - **Sprint** (work unit) — one gated increment = a planner-sized, demonstrable vertical slice ending at
>     the full quality gate + a human course-correct point. _Avoid_: Scrum-sprint/timebox (no clock, standup,
>     or velocity), phase (loop stages GRILL/FREEZE/…), milestone (GSD).
> - **Naming knock-ons:** spec dir `sprint-cadence/` is now cosmetically misnamed (rename deferred —
>   non-blocking). Provenance: user 2026-06-15 — "delivery is fine. Let's call it incremental, but tie the
>   increment to a sprint. Sprint is standard in this but incremental frees us up a bit."

## SC-GB3 — Planning depth: what freezes when? **(RESOLVED — A, three-layer + boundary change-control)**
- **A (recommended): frozen project DESIGN + frozen sprint ROADMAP up front; detailed sprint PLANs frozen
  just-in-time** (sprint N+1's task-level plan is frozen only after sprint N's course-correct). The
  course-correct can then actually steer — corrections land *before* the next freeze, so they are never
  drift. The roadmap (sprint list, goals, gates) is stable; only the active sprint carries a task DAG.
- **B: freeze everything up front** (all sprint plans). Maximum rigidity; the course-correct degenerates to
  accept/abort because corrections would churn already-frozen plans — undercuts the feature's purpose.
- **C: freeze nothing beyond the active sprint** (no roadmap). Loses the whole-project DESIGN grounding and
  makes sprint sizing ad-hoc.

> **RESOLVED 2026-06-15 → A**, sharpened into a three-layer freeze model + a Boundary Change-Control Protocol
> (user: "controlled… user approves changes between incremental runs… remind of drift, require explicit
> approval for anything that could be drift… run adversarial validation for tertiary/unplanned drift…
> anticipate snowballing changes").
>
> **Three-layer freeze model:**
> | Layer | Freeze status | Change path |
> |---|---|---|
> | Project **DESIGN** (what it is) | North star | Only via an **appended superseding decision** at a boundary — never silent rewrite (DECISIONS.md rule). Rare. |
> | Sprint **ROADMAP** (ordered sprints + goals + gates) | Frozen, **boundary-amendable** | At a boundary, re-shape *remaining* sprints (add/drop/reorder) as a deliberate, recorded re-plan. |
> | Active sprint **PLAN** (task DAG + ownership) | **Immutable within the sprint** | None — D1 no-drift holds with full force. |
>
> Maps onto the steering tenet (each sprint = a one-shot; boundary = the scheduled re-plan event) and the
> project's supersede-never-rewrite habit (D57/D58/D59).
>
> **Boundary Change-Control Protocol (the controlled course-correct — also governs GB6):** ceremony scales
> with the change's reach; default/no-correction path stays light.
> - **G1 — Explicit approval gate.** Boundary hard-stops; **no** correction takes effect without explicit
>   user approval (default boundary = always-stop; ties to GB6 sub-question).
> - **G2 — Drift labeling + drift-specific approval.** Each proposed change is classified by reach
>   (next-sprint-plan / roadmap-reshape / DESIGN-amendment) and **explicitly flagged when it constitutes
>   drift** from a frozen artifact. Drift-class changes require a separate, explicit "yes, I am changing the
>   frozen X" approval. Nothing drift-like applies silently.
> - **G3 — Post-approval adversarial validation (tertiary-drift sweep).** Once corrections are approved,
>   `kata-review` (fresh-context, adversarial — D15) sweeps the approved set for **second/third-order drift
>   the user did not ask for** ("you approved X; X silently implies Y and Z"). Reuses D15 + blast-radius.
> - **G4 — Snowball/cascade guard.** Blast-radius (D50/D51) over the approved corrections; if the implied
>   change surface exceeds a `[TUNABLE]` threshold (e.g. reaches beyond the remaining roadmap's footprint),
>   the change is flagged **not a tweak but a re-scope** → escalate to a deliberate roadmap re-plan or a new
>   run, never a silent boundary edit.
>
> **Reuse (answers the over-complexity concern):** adversarial validation = existing `kata-review` (already
> mandatory, D15); cascade detection = existing blast-radius (D50/D51); audit trail = drift ledger +
> supersede-never-rewrite. New surface = the boundary protocol contract, not new heavy skills.
>
> **Edges (RESOLVED 2026-06-15 → A/A; fold into GB6):**
> - **E1 → A:** when G3 finds tertiary drift → **re-present the discovered cascade for another approval
>   round** (approve / defer / cancel); loop, **capped at `[TUNABLE: 2–3]` rounds**; if still snowballing →
>   G4 escalation ("this is no longer a correction — re-plan / new run"). Rejected: B auto-reject (too blunt,
>   blocks legit one-neighbor changes), C auto-defer (risks half-applied change).
> - **E2 → A:** the G4 snowball predicate = **blast-radius(approved corrections) vs the remaining roadmap's
>   footprint** — ripples beyond what the remaining sprints were scoped to touch ⇒ **re-scope event**, not a
>   tweak. Decidable + reproducible (D51 frontier-blocked style). Rejected: B raw count (arbitrary/gameable),
>   C reviewer-judgment-each-time (non-deterministic, violates D18 consistency).
> - Shared safety spine (user requirement): when in doubt, **stop and make the human decide; never silently
>   expand.**
>
> Provenance: user accepted A + added the control requirements + A/A on the edges, 2026-06-15.

## SC-GB4 — Who owns sprint sequencing? **(RESOLVED — A+C; B rejected on D24d/D8)**
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

> **RESOLVED 2026-06-15 → A + C** (user: "A+C yes. Assess for drift and tertiary drift. Make sure we have all
> the tie ins and explicit instructions and behavior planned.").
> - **Decision:** A is the sequencing model (re-entrant `kata-bootstrap` routes; `kata-orchestrate` stays
>   sprint-blind) **+** C adds a **thin `kata-sprint` boundary-coordinator** because the GB3 G1–G4 protocol
>   made the boundary too heavy for bootstrap prose. **B rejected:** an outer loop in orchestrate violates
>   **D24d** (orchestrate = single pure dispatcher) and triggers the **D8** pause-mid-skill failure mode.
> - **GB7 synergy:** a sprint boundary is a natural **context-refresh point** — re-entry gives sprint N+1 a
>   fresh prime frame. A's "spans sessions" IS the ideal delivery of GB7's model, not a cost.
>
> **Drift verdict — A+C is consistent with the locked corpus (reinforces D1/D2/D24d):**
> | Locked decision | How A+C complies |
> |---|---|
> | D1/D2 no-drift | Within a sprint the plan is immutable; boundary = the scheduled re-plan event (steering tenet). Reinforced. |
> | D24d orchestrate single dispatcher | Orchestrate UNCHANGED, sprint-blind; sequencing lives above it (bootstrap/kata-sprint). |
> | D8 self-handoff | Refined by GB7; intra-sprint refresh ≠ boundary (see T1). |
> | D44 readiness re-entrant detection | EXTEND readiness to detect sprint progression state. |
> | D45 load-guard | Validates new `delivery` field + sprint state (fail-closed). |
> | D25 absent-config | `delivery` absent ⇒ one-shot (today's behavior; backward-compatible). |
> | D22 evaluate floor | Every sprint gate = same `kata-evaluate`. |
> | D15 adversarial | G3 reuses `kata-review`. |
> | D50/D51/D52 version-up + escalation | Sprint N≥2 plan freeze = version-up vs sprint N (GB8); red sprint → async escalation, not a boundary (T4). |
> | D33 invariants never tiered | G1–G4 are boundary structural invariants — never tiered. |
>
> **Tie-in / wiring map (explicit):**
> - `kata-orchestrate` — **UNCHANGED.** Runs one frozen sprint plan → gate.
> - `kata-bootstrap` — **EXTEND.** Cold: `delivery` question (progressive disclosure D46) → build + freeze
>   roadmap → launch sprint 1. Re-entry: route on detected state (continue / course-correct / change-cadence /
>   abort).
> - `kata-readiness` — **EXTEND.** Detect sprint progression state: open roadmap, sprint index,
>   **gated-vs-dirty boundary** (T5).
> - **`kata-sprint` — NEW, thin coordinator.** Stop-side: verify gate green → compose `kata-report` +
>   `kata-handoff` → STOP. Resume-side: run G1–G4 controlled course-correct (composes `kata-grill` delta-mode
>   + `kata-review` + blast-radius) → freeze next sprint plan → hand to orchestrate. **Composes, never
>   reimplements.**
> - `kata-plan` — **EXTEND.** Roadmap layer (partition at DAG seams + prime-frame sizing, GB7); per-sprint
>   plan freeze; sprint N≥2 = version-up plan (D50).
> - `kata-grill` (delta mode, GB6), `kata-review` (G3/D15), `kata-handoff`, `kata-report` (D32 — **UNBUILT**,
>   see Dependency), `kata-selfhandoff` (intra-sprint refresh — delineate, T1), `kata-evaluate` (UNCHANGED),
>   `kata-worktree` (sprint-scoped naming, T7) — **REUSE.**
> - **Loop-wiring insight:** orchestrate stays blind; delivery-awareness lives in the loop's **HANDOFF-phase
>   routing** — one-shot → `kata-handoff` (+`kata-selfhandoff`); incremental → `kata-sprint` boundary. This is
>   GB1's "cadence gates latent spine behavior," localized to the HANDOFF phase.
> - **Protocol/config touched:** `protocol/config.md` (new `delivery` field + policy; D45 guard);
>   `protocol/handoff.md` (boundary artifact shape); `protocol/escalation.md` (red-sprint path, T4); sprint
>   progression state location → **GB5**.
>
> **Tertiary-drift register (ACCEPTED as a batch 2026-06-15 — these recommended behaviors are LOCKED):**
> - **T1 — selfhandoff vs boundary collision.** If the prime-frame edge hits at/near a planned sprint end,
>   prefer the **boundary** (it includes a refresh) over a separate selfhandoff. Selfhandoff = intra-sprint
>   backstop; boundary supersedes when both would fire.
> - **T2 — `kata-report` is UNBUILT (D32, backlog). RESOLVED → D2(c) 2026-06-15:** build `kata-report`'s
>   **minimal core as part of sprint-cadence** (the per-sprint report = `kata-report v1`, not throwaway); D32
>   expands later. No tech debt. Supersedes the earlier "throwaway inline report" idea.
> - **T3 — change-cadence mid-project.** incremental→one-shot = collapse remaining roadmap into one run;
>   one-shot→incremental = partition remaining work into sprints. Must be an explicit bootstrap re-entry path.
> - **T4 — red sprint (gate not green).** Boundary requires a GREEN gate. A sprint that can't go green loops
>   in-lane then **escalates (D51/D52)** — it does NOT produce a course-correct boundary.
> - **T5 — dirty vs gated boundary on re-entry.** Dirty (mid-sprint crash) → resume the sprint re-anchored on
>   its frozen plan (selfhandoff-style recovery), NOT course-correct. Gated → offer course-correct. (readiness)
> - **T6 — sprint state read by 3 consumers** (readiness, bootstrap, kata-sprint) → single-writer, plan-
>   guardian-owned (L3). Defined in **GB5**.
> - **T7 — sprint-scoped worktree/branch naming** must be deterministic + collision-free across sprints
>   (`kata-worktree`).
> - **T8 — STEERING/AGENT_STOP across the boundary.** The boundary is a natural STEERING-consumption +
>   kill-switch checkpoint; confirm file-based STEERING survives session spans.
>
> Provenance: user confirmed A+C + requested the drift/tertiary-drift assessment, 2026-06-15.

## SC-GB5 — Where does sprint progression state live? **(RESOLVED — A, three-tier + derived cache)**
- **A (recommended): split.** `kata.config.cadence` holds the frozen *shape + policy* (provenance,
  reproducibility). The *roadmap status* (sprint index, per-sprint gate evidence, open corrections) is
  **machine coordination state** under `.kata/` (single-writer, plan-guardian-owned — L3), with the
  human-facing trail in the durable sprint reports. Config stays append-stable; state churns.
- **B: everything in `kata.config`.** Rejected-leaning: progression churn in a frozen provenance file
  invites the stale-config class the load-guard (D45) exists to catch.

> **RESOLVED 2026-06-15 → A**, sharpened to a three-tier model + a derived-cache robustness rule (user A/yes).
> Governed by L3 (shared single-writer state corrupts), D11/STANDARDS §5 (durable docs ≠ machine state), D45
> (load-guard catches stale config).
>
> **Three-tier data model:**
> | Tier | Holds | Lives in | Lifecycle |
> |---|---|---|---|
> | **1. Frozen provenance** | `delivery: { shape, policy }` (boundary mode, prime-frame policy, grill tier) | `kata.config` (git-committed) | bootstrap-set, **append-stable**, D45-guarded |
> | **2. Durable trail** | per-sprint reports + boundary handoffs + **superseding decisions / roadmap amendments** | Obsidian-native `.planning`-style docs (git-committed) | **authoritative, resumable record** (spine #5) |
> | **3. Progression cache** | sprint index, gate status, open-correction status, dirty/gated flag (T5) | `.kata/` | single-writer plan-guardian (L3), **churns** |
>
> Mirrors D52 (escalation): tier 3 tracks a correction's **lifecycle** (open→approved→applied); tier 2 holds
> its **content** (the superseding decision).
>
> **Robustness rule (the "spans sessions" enabler):** tier 3 (`.kata/`) is a **gitignored, derived,
> disposable cache** — `kata-readiness` **rebuilds it from the git-committed tier-2 trail on re-entry**
> (current sprint index = which sprint reports exist + are gated). Git is the source of truth for "where are
> we?", never the fragile state file. Consequences: (a) resume works in a **new session / different clone**;
> (b) strongest L3 posture — if the cache corrupts, throw it away and rebuild from git.
>
> **Schema homes:** tier 1 → `protocol/config.md` (new `delivery` field); tier 2 → `protocol/handoff.md` +
> DESIGN/roadmap with DECISIONS-style superseding entries; tier 3 → extend `protocol/state.md`
> (single-writer plan-guardian machine state).
>
> Provenance: user confirmed A + the three-tier split + the derived-cache robustness rule, 2026-06-15.

## SC-GB6 — The course-correct: mechanism + depth **(RESOLVED — A + A; default always-stop)**
- **A (recommended): a scoped delta-grill** — interrogate only (a) what sprint N's output put in question,
  (b) the user's correction requests; accepted corrections bake into the DESIGN as **superseding decisions**
  (never silent rewrite — same rule as DECISIONS.md). Tier: default the run's grill tier, droppable to
  essential for small corrections (cross-tier pick, D24c).
- **B: full re-grill each boundary.** Cost-prohibitive at the cadence's whole point (cheap iteration).
- **C: no grill — free-text notes only.** Loses doc-grounding; corrections become drift vectors.
- Sub-question: when the user has **no** corrections, does the boundary still hard-stop for confirmation, or
  can the user pre-authorize "auto-continue while green"? (Recommend: ask at bootstrap —
  `cadence.boundary: "always-stop" | "auto-continue-while-green"`; default always-stop.)

> **RESOLVED 2026-06-15 → A (mechanism) + A (boundary policy)** (user "yes. a. I agree").
> - **Mechanism (A):** the course-correct is a **scoped delta-grill** — reuse `kata-grill` in delta mode,
>   interrogating only (a) what sprint N's output called into question + (b) the user's correction requests;
>   accepted corrections bake into the DESIGN as **superseding decisions** (never silent rewrite). Wrapped by
>   the GB3 G1–G4 protocol. Pure reuse — no new grilling machinery.
> - **Depth/tier (D24c):** default the run's grill tier, **droppable to essential** for small corrections
>   (cross-tier pick). Per **D33**, structural invariants (G1–G4, no-drift, default-FAIL) hold at **every**
>   tier — only interrogation depth varies.
> - **Boundary policy (A):** `delivery.boundary: "always-stop" | "auto-continue-while-green"`, **default
>   always-stop** (control-first). `auto-continue-while-green` is **opt-in** and proceeds ONLY when green ∧
>   no escalations ∧ no pending corrections ∧ G3 finds no tertiary drift; ANY of those false ⇒ stop (the
>   "when in doubt, stop" safety spine). Rejected: B always-stop-no-exceptions (forces babysitting a clean
>   run, against D8 anti-over-conservative), C auto-continue-by-default (violates the explicit-approval ethos).
> - Provenance: user 2026-06-15.

---

## CROSS-CUTTING — Engram / second-brain seam registry **(NEW DIRECTIVE 2026-06-15)**
User: "We need to think about engram/second brain input throughout. It needs to have a plugin. We should be
building a file that outlines all the pointers for where the engram second brain feature will tie in once
it's enabled, so we know where to wire it in." Arose at GB6 (the D56 auto-continue seam) but is **harness-wide**.
- **Decision:** consolidate the scattered engram intent (D9 backlog, D56 forward-seam, D30 protocol
  extension points, D52 escalation = learning surface) into one durable **seam registry + plugin contract**:
  **`protocol/engram.md`** (CREATED 2026-06-15).
- **Shape:** optional module `kata/module/engram` (D20/D43); pluggable second-brain backend (kiban/kagami)
  bound to an agnostic contract, core never hard-deps (the D53 pattern). Two ops: **CONSULT** (before a
  human is asked → auto-resolve/recommend) + **LEARN** (after a human decides → feed back). Core invariant:
  **consult-if-present, no-op if absent** (D30) — additive only, never a correctness dependency.
- **Adversarial-validated (D15 / no-self-certification L8):** `kata-review-advanced`, fresh-context Opus
  (Fable 5 unavailable), audited the first 9-seam draft → **HOLD** (5 HIGH misses + 4 blocking contract gaps).
  Findings accepted; registry expanded + hardened.
- **Seam registry now E1–E21** (was E1–E9): **added** E10 `kata-preflight` approval gate (HIGH — the most
  explicit human gate, security domain), E11 `kata-evaluate` PASS/NEEDS_WORK (HIGH), E12 `kata-review`
  SHIP/HOLD + finding-priority (HIGH), E13 `kata-grill` convergence-gate (HIGH), E14 `kata-diagnose`
  hypothesis-rank/fix-vs-escalate (HIGH), E15 tdd test-seam, E16 bootstrap composition-ladder, E17 readiness
  WARN-proceed, E18 `kata-defer` park-vs-pursue, E19 sprint re-entry routing, E20 G4 snowball re-scope, E21
  handoff open-decisions. **E8 reclassified** (substrate dependency, not a seam). **E9 RETIRED** (selfhandoff
  is agent→self, no human → fails membership test).
- **Contract invariants C1–C6 added:** C1 precedence/arbitration (D18), C2 fail-to-the-human on
  absent/slow/low-confidence backend (safety spine), C3 privacy/scoping/redaction (D30 + security), C4
  CONSULT may never auto-resolve a LOCKED-decision conflict (D1 no-drift), C5 supersession/decay
  (D57/58/59), C6 audit every auto-resolution to the drift ledger.
- **Backend binding (differentiator — user 2026-06-15):** ships with NO backend; agnostic CONSULT/LEARN
  contract + `engram.backend` config. Pluggable: kiban / kagami / **the work host** / plain vault / custom.
  **Clean-room (D30):** the work host binds *externally* and answers the contract → **zero AWS-internal IP
  imported into KataHarness**; public harness + AWS-internal second brain interoperate without coupling.
  "Bring your own cognitive fingerprint."
- **Gating:** PokeVault installed (SATISFIED D58) + cognitive-fingerprint synthesis built (kata-engram, D9).
- **Maintenance rule:** every new human-decision point or learning surface adds a seam row in the same change.
- Promote to a harness-wide **D-number** at freeze (alongside the sprint-cadence D-numbers).

## SC-GB7 — Sprint sizing: who cuts the boundaries, and to what bar? **(RESOLVED — A + prime-frame sizing)**
- **A (recommended): planner-derived, user-confirmed at FREEZE.** `kata-plan` proposes the sprint partition
  (vertical, demonstrable slices — each sprint independently green + produces *visible* output worth
  course-correcting on); the user confirms/adjusts the roadmap before it freezes. Bar per sprint: full gate
  green + a demo-able artifact + a one-page report.
- **B: user dictates sprint boundaries up front.** Fine as an override; weak as the default (the planner
  sees the DAG).
- **C: fixed-size timeboxes.** Scrum-literal; meaningless for an agent loop (cost ≠ wall-clock).
- Sub-question: minimum/maximum sprint count guidance? (e.g. a 2-task project should refuse sprint cadence
  and recommend one-shot — cadence has a floor where it's pure overhead.)

> **RESOLVED 2026-06-15 → A + a context-budget ("prime frame") sizing primitive** (user: floor/ceiling based
> on the ~1M context window + the recommended prime frame; same primitive drives the one-shot handover/refresh
> threshold).
> - **Decision (A):** `kata-plan` proposes the sprint partition, cutting at **natural seams in the task DAG**
>   (lowest cross-sprint coupling → smallest inter-sprint regression surface → cheap GB8 contract); the user
>   confirms/adjusts before the roadmap freezes (GB3).
> - **Per-sprint bar:** full quality gate green (`kata-evaluate`, D22) + a **reviewable artifact appropriate
>   to the project type** ("demonstrable" ≠ strictly visual — runnable test / CLI / API / skill invocation
>   for non-UI projects like KataHarness itself) + a one-page report.
> - **Prime frame = the sizing primitive.** The *prime frame* is the recommended effective working band of a
>   model's context window (below the degradation zone, headroom reserved) — not the max window.
>   - **Floor:** project fits comfortably in one prime frame → refuse sprint, recommend **one-shot**.
>   - **Ceiling:** a sprint that would exceed one prime frame is too big → **split**. Max sprint count falls
>     out of `(total project context demand ÷ prime frame)` — no arbitrary cap.
> - **Cross-cutting context-budget decision (REFINES D8 / `kata-selfhandoff`):** the *same* prime frame sets
>   the one-shot **self-handoff/refresh threshold**, replacing D8's naive "configurable %". **Self-handoff
>   runs inside sprints too** — intra-sprint context refresh (re-anchor on the frozen plan, **no human gate,
>   no drift**) is just the one-shot mechanism operating within a sprint. Unification: one-shot =
>   `[work→prime-frame edge→refresh]*` → final gate; **sprint = the same, but at planned prime-frame
>   boundaries it also stops for gate + report + course-correct.** Same primitive, two policies.
> - **Confirmed refinements (user A/A/A 2026-06-15):**
>   1. Prime frame is an **agnostic policy/fraction**; the **adapter resolves it to real tokens per-model**
>      (orchestrator/deep = Fable 5, workers = Sonnet — D59; spine #3 preserved).
>   2. Planner sizing is a **forecast** (token burn isn't perfectly predictable); the **runtime self-handoff
>      trigger is the backstop** for under-estimates mid-sprint.
>   3. Trigger at the **last clean task boundary before** the prime-frame edge (reserve headroom; D8
>      task-boundary preference) — never refresh mid-task into a lossy compression.
> - **Implementation flag:** the ~1M window + prime-frame fraction are `[TUNABLE]`s to **ground against
>   current model facts at DESIGN time** (verify real Fable 5 / Sonnet windows + recommended utilization; do
>   not pin from memory). Architecture is number-independent; the policy is not.
> - **New glossary terms (promote to CONTEXT.md at freeze):** **Prime frame** · **Context budget**.
> - Provenance: user 2026-06-15 — "floor/ceiling based on expected 1m token context window and the
>   recommended prime frame… in one shot mode it should be considered when setting the threshold for handover
>   and refresh within the harness loop."

## SC-GB8 — Sprint N≥2 = version-up? **(RESOLVED — A, unifying baseline rule)**
- **A (recommended): yes, structurally.** Sprint N's gate command becomes sprint N+1's
  `target.baselineGate`; footprint ownership + full-suite-green regression contract (D50) and async
  escalation (D51) apply verbatim; `kata-graph` optionally activates when the codebase grows past the point
  where digest-grounding pays (à-la-carte, D43). This makes sprint cadence mostly **composition of shipped
  machinery**.
- **B: sprints stay greenfield-shaped throughout.** Simpler config, but forfeits the regression contract —
  sprint N+1 could silently break sprint N's work, which is the exact "don't break other aspects" failure
  the user named.

> **RESOLVED 2026-06-15 → A**, with a unifying baseline rule (user "go with recommended").
> - **Decision:** a sprint is **version-up-shaped whenever there is a prior green baseline to protect.**
>   Unifying rule: **`baselineGate` = the most recent green gate** — the existing repo's gate, else the prior
>   sprint's. So: **greenfield** project → sprint 1 greenfield, sprints **2+** version-ups; **existing-repo**
>   project (run-shape = version-up) → **every** sprint a version-up. No special-casing; sprint 1 of a
>   greenfield simply has no prior baseline yet.
> - **Reuse (verbatim):** footprint ownership (modified ∪ depth-1 reverse-deps) + full-suite-green regression
>   contract (D50) + async escalation (D51/D52). `kata-graph` activates **à-la-carte on prime-frame pressure**
>   (GB7) — off for small early sprints, on when a later sprint's growing codebase would blow its prime frame
>   and the token-cheap digest is what keeps it inside the budget (D43/D53). Sprint cadence is therefore
>   **mostly composition of shipped A4 machinery**, not new code.
> - **Rejected B:** forfeits the regression contract → silent breakage of prior sprints (the D36 "don't break
>   other aspects" failure the user named).
> - Provenance: user 2026-06-15.

## SC-GB9 — Composition with bake-off + version-up run-shape **(RESOLVED — version-up first-class; bake-off trimmed)**
Orthogonality says a sprinted bake-off (N variants *per sprint*) and a sprinted version-up (sprints over an
existing repo) are both expressible. **Recommend:** declare them valid combinations in the contract but
**defer their execution paths** (Spec B isn't built; A4 composition needs its own check) — same
configurable-now/executable-later pattern as GB5/A3. Confirm or trim.

> **RESOLVED 2026-06-15** (user: "Sprinted bake off is kind of crazy… too intense").
> - **Sprinted version-up → FIRST-CLASS** (not deferred). GB8 already made "existing-repo project → every
>   sprint a version-up" a designed, buildable path. Core to the feature.
> - **`delivery` × mode / effort / modules (quality, design) → work today**, no special handling (the payoff
>   of GB1's orthogonal axis).
> - **Sprinted bake-off → TRIMMED (out of scope; NOT reserved).** N-variants-*per-sprint* is combinatorial
>   cost (N × every boundary, each with a gate + G3 adversarial sweep) for a thin use case. **Not architecturally
>   forbidden** (axes stay orthogonal), but **no config path, no bootstrap offer, no reserved seam.**
>   - **Trimming forecloses nothing:** the only sensible variant — bake-off *one* high-risk sprint — is just
>     ordinary à-la-carte module composition (D24c: add the `bakeoff` module to a single sprint's execution)
>     **if/when Spec B exists.** It needs no dedicated "sprinted-bakeoff" path. Revisit then, only on a concrete request.
> - Provenance: user 2026-06-15.

## SC-GB10 — Sequencing vs D16 **(RESOLVED — A; freeze now, build after D16)**
D16 (planning-varied A/B) is the v0.1 validation gate and the standing next step; its targets are *small
one-shottable* projects — **one-shot cadence; sprint cadence is not a D16 dependency.**
- **A (recommended):** answer this ledger + freeze the sprint-cadence DESIGN now (cheap, docs-only), **build
  after D16** — the unvalidated-grill rework-exposure argument that killed KG-first (L8) applies to building
  (not to specing) this too.
- **B:** build sprint cadence first. Costs the same rework exposure the 2026-06-10 adversarial review
  rejected for Option D.
- **C:** spec *and* build later; only log the capture. Loses tonight's momentum on a user-named priority.

> **RESOLVED 2026-06-15 → A** (user "A"). Freeze the sprint-cadence DESIGN now (docs-only, cheap,
> supersede-able), **build after D16.** Same logic that rejected grill-KG-first (L8 + 2026-06-10 review):
> *specing is cheap and safe; building on an unvalidated grill is rework exposure.* **Closes the standing
> "confirm D16-first sequencing" open decision (STATE.md) → LOCKED D16-first.**
> - **Precondition before freeze (per grill RUBRIC — no self-certification):** a fresh-context convergence +
>   negative-drift + complexity + loose-ends review of the whole ledger must return SHIP.
> - **Sequence:** (1) grill converged GB1–GB10 + engram ✅ → (2) fresh-context audit → (3) on SHIP freeze
>   `DESIGN.md` → (4) build after D16.
> - Provenance: user 2026-06-15.

---

## Convergence
All ten branches answered (GB1–GB10) + engram cross-cut. Per the RUBRIC, the grill does not grade its own
convergence — a fresh-context audit (convergence + negative-drift + complexity + loose-ends, per user
2026-06-15) runs before freeze. On SHIP → promote to D-numbers → freeze `DESIGN.md` → PLAN → build after D16.

### Status board (2026-06-15)
| Branch | Verdict |
|---|---|
| GB1 architecture | RESOLVED — own orthogonal `delivery` axis |
| GB2 naming | RESOLVED — `delivery: one-shot \| incremental`; unit = sprint |
| GB3 freeze model | RESOLVED — three-layer + Boundary Change-Control Protocol G1–G4 (+E1/E2) |
| GB4 sequencing | RESOLVED — A+C (bootstrap routes, orchestrate blind, new thin `kata-sprint`); drift-clean; T1–T8 |
| GB5 state | RESOLVED — three-tier + derived `.kata/` cache rebuilt from git trail |
| GB6 course-correct | RESOLVED — scoped delta-grill; `delivery.boundary` always-stop default |
| GB7 sizing | RESOLVED — A + prime-frame context-budget primitive (refines D8) |
| GB8 version-up reuse | RESOLVED — baseline = most recent green gate |
| GB9 composition | RESOLVED — version-up first-class; sprinted bake-off trimmed |
| GB10 sequencing | RESOLVED — freeze now, build after D16 (D16-first LOCKED) |
| Engram cross-cut | Registry E1–E21 + C1–C6 + backend binding; adversarially reviewed (HOLD→addressed) |

---

## FREEZE-GATE AUDIT (2026-06-15) — `kata-review-advanced`, fresh-context Opus → **HOLD → resolutions**
The grill's mandatory pre-freeze adversarial pass (RUBRIC; no self-certification). Verdict: **decisions sound,
specification fidelity not yet freeze-ready.** Cleared as solid (do NOT reopen): GB1 orthogonal-axis, D24d
compliance (orchestrate verified untouched), D33 invariant-tiering (G1–G4 never tiered), D22/D25/D45 compat,
GB8 baseline rule, GB9 bake-off trim, GB10 sequencing. Resolutions below.

**MUST-FIX (freeze-blocking):**
- **A1/D1 — roadmap layer is NET-NEW, not latent.** Verified: `kata-plan` has no roadmap layer; DESIGN.md
  cites GSD spec→roadmap→plan as *inspiration* only. Correct the GB1/GB4/GB5 "latent / already-contains"
  framing → the **sprint-roadmap layer is net-new in `kata-plan`** (the feature's largest build surface).
  **Roadmap-artifact schema stub (pin for DESIGN.md):** `{ projectDesignRef, frozenAt, sprints: [ { id,
  goal, gateCommand, demonstrableArtifactType, dagSeamRationale, dependsOn[] } ] }`.
- **A2 — pin tunables / fix predicate.** E1 re-approval round cap **PINNED = 2** (safety backstop, not a
  tuning knob). G4 snowball: **remove the numeric threshold**; predicate is **solely** blast-radius(approved
  corrections) vs remaining-roadmap footprint (exceeds ⇒ re-scope) — D18 reproducibility. The ~1M window +
  prime-frame fraction stay TUNABLE-grounded-at-DESIGN (genuinely model-fact-dependent).
- **B1 — D8 supersession recorded.** GB7's prime-frame self-handoff threshold **supersedes the threshold half
  of D8** (trigger basis changes from user-set % → model-resolved context-budget fraction) — not a mere
  "refinement." Promote at freeze as a D-number explicitly superseding D8's threshold clause (surviving D8
  principles — anti-over-conservative, task-boundary-preferred — carry forward). Flag `kata-selfhandoff`
  **EXTEND**.
- **B5 — freeze-gate guards mutation, not just birth.** Add to G3/G4: any **DESIGN-layer amendment** at a
  boundary (not roadmap-reshape, not next-sprint-plan) requires the **same fresh-context `kata-review` SHIP**
  GB10 mandates for the initial freeze. A boundary may not rewrite the north-star DESIGN and proceed unguarded.
- **D1 — honest tie-in labels (relabel the GB4 wiring map):** **NEW** = `kata-plan` roadmap layer; **EXTEND
  (new logic in an existing skill)** = `kata-readiness` (sprint-state detection + tier-3 cache rebuild +
  gated-vs-dirty), `kata-selfhandoff` (prime-frame trigger), `kata-handoff` (boundary-artifact content),
  `protocol/state.md` (tier-3 fields + disposable/rebuildable semantics); **REUSE (verbatim)** =
  `kata-orchestrate`, `kata-evaluate`, `kata-review` (G3), `kata-grill` delta-mode, blast-radius (G4), D50.
- **D3 — `delivery` config field pinned (write into `protocol/config.md` at freeze):** `delivery: { shape:
  "one-shot"|"incremental" (default one-shot, D25), boundary: "always-stop"|"auto-continue-while-green"
  (default always-stop), backend?: <engram ptr> }`. Preset pre-fill: individual ⇒ one-shot; version-up ⇒ ask;
  batch ⇒ one-shot. D45 load-guard validates fail-closed.
- **D2 — `kata-report`/D32 dependency → RESOLVED (c), user 2026-06-15.** Build `kata-report`'s **minimal core
  as part of sprint-cadence** — the per-sprint report *is* `kata-report v1` (not throwaway); D32 expands later.
  No tech debt; sprint-cadence's need bootstraps D32 with just-enough scope. **Build-scope impact:**
  sprint-cadence now includes a minimal `kata-report` (D32 v1); supersedes T2's "throwaway inline report"
  mitigation.

**SHOULD-FIX (not freeze-blocking):**
- **A3 — engram E2 subordinate to the GB6 AND-gate** (applied to `protocol/engram.md`): a boundary CONSULT may
  never flip `stop`→`continue` while any of {green ∧ no escalations ∧ no pending corrections ∧ no G3 tertiary
  drift} is false (C4-adjacent).
- **D4 — mid-project cadence change = drift-class:** T3's incremental↔one-shot switch routes through the
  G1/G2 approval gate (it changes the roadmap layer).
- **Lens C engram trim (E15–E21) → PENDING USER:** right-size the registry — keep the contract + C1–C6 +
  backend binding + HIGH seams (E1, E6, E10–E14); demote E15–E21 to a one-line "candidate seams, populate when
  the host skill exists" (the maintenance rule re-adds them when real). Simplification, not a correctness gate.

**Freeze path:** apply must-fix → resolve D2 + trim with user → re-confirm SHIP → freeze `DESIGN.md` (writing
in the A1 schema stub + D3 config field + B1 D-number) → build after D16.
