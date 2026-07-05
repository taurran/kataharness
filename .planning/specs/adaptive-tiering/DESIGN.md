---
spec: adaptive-tiering
status: FROZEN 2026-07-05 (D150) — grill-resolved; freeze-gate v1
  HOLD (2 BLOCKER / 4 HIGH / 8 MED / 5 LOW) → ALL FOLDED → re-gate SHIP-WITH-FIXES (3 MED / 5 LOW, folded); all three [VETO-FLAG]s RESOLVED by the operator 2026-07-05 to the draft defaults ("Yes, looks good") — N=10/reserve 2, F=2/K=3/damper ×2, compose-ON/load-OFF; paired amendment texts DRAFTED into both host specs; formerly
  open for the operator
directive: operator 2026-07-05 — "adaptive and driven by data… bake in evaluation into the mix… if a
  task fails over a certain amount of times, it gets bumped up to the higher model… if a step is
  assessed and grounded and determined to be low value, it gets sent down the chain… Make it smart…
  push this as the next update"
routing: PAIRED gated amendments (the Amendment #5 precedent — no frozen line edited anywhere):
  (a) Amendment #2 to specs/model-tiering/DESIGN.md (D148 successor — scope forms, budget, premium-rung
  registry); (b) Amendment #6 to specs/inline-eval-m4/DESIGN.md (the evaluator re-adjudication leg
  AT-L9 + the fail-bump signal wiring AT-L8 + the M4-owned ledger additive keys tierEvents/
  verdictByTier (AT-L20, the C-3 shared deliverable) touch M4 surfaces and MUST land as an M4
  amendment, never a silent breach — freeze-gate v1 BLOCKER-1 routing fix + re-gate LOW-7). NOTE
  (re-gate LOW-8) — the FREEZE ACT's deliverable includes DRAFTING both amendment texts appended to
  their host specs (supersede-never-rewrite, the Amendment #5 precedent); this header's declaration
  alone does not discharge the routing.
new_d_records: assigned at freeze (≥ D150)
tags: [kata/spine, model-tiering, adaptive, premium-rung, evaluation-driven]
---

# Adaptive tiering — evidence-driven model routing (FROZEN)

## §0 Mission (the operator's framing, verbatim-level)

Model selection stops being a static class×mode table and becomes **adaptive and driven by data**, with
the evaluation loop as a first-class signal source: a task that keeps failing its gate is **bumped up a
rung for its next attempt**; work assessed and grounded as low-value is **sent down the chain**; the
premium rung (Fable today; any family's expensive top rung tomorrow) is **gated to advanced mode behind
an operator approval whose pitch IS the optimization guarantee** — premium fires only on the hard
moments, within a budget, and everything else tiers down. Ships as the next update (v0.3.0).

**The one-sentence architecture:** three layers — **L0** the existing D131 differential table (the
deterministic base and the ONLY fallback), **L1** event- and evidence-scoped modulation per dispatch
(this build), **L2** ledger-driven acceptance routing (named-deferred until post-R6 data exists).

**Honesty note (freeze-gate v1 LOW-15/16, stated up front):** Leg B's *escalation* work is
advanced+approved-only by arithmetic — standard-critical already sits at the anchor (zero-step) and
essential is escalation-inert by design. "All three modes get smarter" is delivered to
standard/essential by the DOWNSHIFT legs (complexity, streaks, evaluator thrift) plus the fail-bump
within their ceilings; at a sonnet anchor, essential's bump ceiling can degenerate to a no-op
(anchor−1 == floor) — documented, not hidden.

## §1 Doctrine + provenance

- **L0 is D131/D59 unchanged** — relative, family-agnostic, no hard-baked IDs, inherit-by-omission,
  absent-block ⇒ byte-for-byte BC. It stays because an adaptive router MUST have a deterministic
  designed fallback for cold-start / degraded-telemetry / malformed-config legs (D136). L0 is that
  fallback; it is never edited, only modulated.
- **The premium mechanism is D148 reused, with ONE named shape change:** the four-conjunct fire rule
  keeps its shape, and conjunct #2 ("work-class ∈ scope") gains the new-form reading "event ∈
  scope.events" — the fail-bump path is covered by making `fail-bump-escalation` a REGISTRY EVENT
  (freeze-gate v1 HIGH-3's fold), so no premium dispatch ever fires outside the conjuncts.
- **The evaluation-integration leg extends M4 via a routed amendment** (Amendment #6 there): the
  ladder's verdicts and the task gate's rejections ARE the adaptation signals. D33 holds: worker
  self-assessment never drives tier — only orchestrator-side verdicts and mechanical evidence.
  **One NEW plan-frozen judgment surface is invented and named** (freeze-gate v1 MED-14): the
  plan-time `complexity` rating (AT-L10a) — mitigated by the plan freeze-gate attacking it, exactly
  like every other frozen plan judgment.
- **L2 is M4-L7's already-named consumer** (acceptance-driven routing from
  `firstPassAcceptanceByClassTier`) — contract here, activation deferred until the ledger has
  non-calibration volume (post-R6 instrumented runs).
- **DSpark principle #5 extended** ("calibrate the scorer against cached verifier outputs"): the
  *router* calibrates against logged gate verdicts, the same telemetry-first discipline as M4-P0.
- **C-3 calibration finding realized** as escalation WITHIN below-anchor space (haiku screens, sonnet
  adjudicates — C-3's own fix candidate), never at the anchor (M4-L7 stands un-breached; AT-L9).

## §2 Locked decisions (proposed — the freeze-gate attacks these)

### Leg A — the three-layer resolution order (AT-1)

- **AT-L1 — Resolution order per dispatch is PINNED (freeze-gate v1 HIGH-4):**
  `base = L2_row_if_active_else_L0(class, mode)` → apply **downward modulation, CAPPED at −1 total
  per dispatch** (complexity AT-L10a and streak AT-L11 do NOT stack — the deeper single downshift
  applies; re-gate MED-2, keeping AT-L2's one-rung-per-iteration line true in BOTH directions) →
  apply **fail-bump** (AT-L8) → clamp to [floor (AT-L3), ceiling (AT-L2)]. **Per-task state
  OVERRIDES class state:** a task with `bumpCounter ≥ 1` is EXEMPT from
  both downshift legs for all its remaining attempts — a failed task can never be re-dispatched at or
  below the rung that already failed it. Absent every adaptive input ⇒ the dispatch resolves EXACTLY
  as v0.2.1 does today.
- **AT-L2 — The ceiling ladder:** essential ⇒ anchor−1; standard ⇒ the anchor; advanced ⇒ the anchor,
  or the premium rung IFF the D148 conjuncts hold (approved ∧ conjunct-#2 per §1 ∧ offer exactly one
  rung above anchor ∧ mode == "advanced"). Nothing ever resolves above the premium rung; nothing ever
  adapts more than ONE rung per iteration.
- **AT-L2b — Emission contract (freeze-gate v1 MED-10):** L1 modulation yields a RUNG; emission
  follows the frozen contract byte-for-byte — a rung landing ON the anchor emits **`None`/OMIT**
  (never the anchor's explicit id — the R7/Fable-outage protection); a below-anchor rung emits its
  explicit id; the premium rung emits `premium.offer` itself (D148 §3.1 unchanged).
- **AT-L3 — The floor:** the family floor and the R1 coder-floor are untouched and bind every adaptive
  downshift (raise-only floors are never lowered by adaptation).
- **AT-L4 — Judgment NEVER adapts DOWN — exemption defined by FUNCTION with an explicit roster
  (freeze-gate v1 MED-11):** the D33 never-tiered gate family (kata-evaluate, freeze-gate/kata-review
  verdict passes, grill convergence, kata-validate, kata-slop-check) **plus `kata-inline-eval`**
  (economy-classed but kill-authority judgment — C-3 proves its tier changes verdicts) keep their L0
  resolution as the floor; adaptation may only move them UP (events, Leg B). The downshift legs
  (AT-L10/L11) apply ONLY to **`coding`-class dispatches** (the machine-checkable enum term against
  `SKILL_WORK_CLASS`; re-gate LOW-5 — `economy`-class dispatches already sit at their mode's floor
  and `critical` is roster-protected).

### Leg B — event-scoped escalation (the "hard moments" registry) (AT-2)

- **AT-L5 — The event registry is DATA** (in `kata_models`, `[TUNABLE]` membership like the M4
  weights), **each event citing its covering DISPATCH SITE** (freeze-gate v1 MED-12 — no phantom
  events; the conductor's own non-dispatched judgment can never be an event):
  | Event | Covering dispatch (site) |
  |---|---|
  | `freeze-gate-verdict` | the fresh-context kata-review freeze-gate dispatch (orchestrate freeze-gate step) |
  | `re-gate-after-hold` | the re-gate reviewer dispatch after any HOLD fold |
  | `escalation-adjudication` | the grounding-gate kata-evaluate / kata-review dispatches on the escalation path (NOT the conductor's routing call, which is not a dispatch) |
  | `fix-loop-diagnose` | the at-budget kata-diagnose dispatch in the gate fix-loop |
  | `final-initiative-review` | the D98 whole-initiative red-team dispatch |
  | `gate-rejection-rework-review` | fix-loop judge re-runs + the confirmation pass |
  | `fail-bump-escalation` | the AT-L8 bumped ATTEMPT dispatch — **CONJUNCT-COVERAGE-ONLY member (re-gate MED-1): AT-L6's mode scaling does NOT apply to it; bump mechanics are exclusively AT-L8 + the AT-L2 ceiling** (a registry listing so conjunct #2 is satisfiable by shape, never a second escalation rule for the same dispatch) |
  **Removed from v1's draft registry:** `ladder-trigger-2-grounding` — the trigger-#2 grounding pass
  is CONDUCTOR-AUTHORED (M4-L5, orchestrate prose), not a dispatch; it cannot be tiered and is not an
  event (freeze-gate v1 BLOCKER-2's fold; converting it to a dispatch is explicitly NOT proposed).
- **AT-L6 — Mode scaling (applies to every registry event EXCEPT `fail-bump-escalation`, per its
  AT-L5 row):** essential = registry INERT for escalation (downshift-only thrift; AT-L8 bumps still
  fire within essential's own anchor−1 ceiling — they are AT-L8's rule, not this one's); standard =
  registry events escalate to the ANCHOR (arithmetically material only where the L0 row sits below
  it — see §0 honesty note); advanced = registry events escalate to the PREMIUM RUNG under the
  conjuncts, else the anchor.
- **AT-L7 — Every adaptive move is LOUD:** a board `DECISION` line
  (`tier: <task|dispatch> <from>→<to> reason <event:<name>|failbump|streak|complexity>`) + a
  telemetry record (§Leg G). Never silent. These `tier:` lines are ALSO the durable recount trail
  for budget/counter state across conductor compaction (the thrash-budget recount precedent;
  freeze-gate v1 MED-8).

### Leg C — evaluation-driven adaptation (the operator's two mechanisms) (AT-3)

- **AT-L8 — Fail-count bump-up ("fast up"):** per task, the bump counter = gate REJECTIONS + STANDING
  ladder `reroll` verdicts (post-re-adjudication only — an overturned verdict never counts;
  freeze-gate v1 MED-9). At **F = 2** `[TUNABLE — VETO-FLAG-2]` the NEXT attempt's build worker
  dispatches one rung up from its current resolved rung (ceiling AT-L2, emission AT-L2b). **F fires
  ONCE per task** (no 2F re-trigger in v1 — freeze-gate v1 LOW-17); the bump persists for the task's
  remaining attempts, resets at task completion, never leaks cross-task (L2 owns cross-task
  learning). The bumped attempt IS the `fail-bump-escalation` registry event.
- **AT-L9 — Cheap-then-escalate evaluator ladder (C-3 realized; ROUTED as M4 Amendment #6):** the
  inline evaluator dispatches at its M4-L7 economy resolution (unchanged); a would-be **`reroll` or
  `correct`** verdict is re-adjudicated ONCE by an evaluator **one rung up from the economy
  resolution, CLAMPED STRICTLY BELOW THE ANCHOR** (M4-L7's never-anchor line is preserved, not
  amended). Where the economy resolution is already anchor−1 (advanced-mode Anthropic), **this leg is
  INERT — stated, not silent** (freeze-gate v1 BLOCKER-1's fold; C-3's own candidate is
  haiku-screens-sonnet-adjudicates, escalation within economy space). Conflicting verdicts ⇒ the
  higher evaluator stands + `verdictByTier` recorded. `continue` verdicts are never re-adjudicated
  (the green path stays one cheap call — M4-L1 intact; cost bound, stated per AT-L22's own
  discipline: the pre-fix scan measured TP 0/57 with the 13/57 FP class DESIGNED AWAY by Amendment
  #5; the post-fix trigger rate is UNMEASURED until owned-exit-emitting runs exist — re-gate LOW-6).
- **AT-L10 — "Low-value ⇒ down the chain" is TWO mechanical signals, never a runtime vibe:**
  **(a) plan-time:** optional per-task `complexity: low|standard|high` in plan frontmatter — assessed
  at plan/grill time, FROZEN with the plan, attacked by the plan freeze-gate (the one new judgment
  surface, §1); `low` ⇒ the task's build worker starts one rung below its L0 resolution
  (floor-clamped). Absent ⇒ L0 exactly (BC); present-but-malformed ⇒ plan-freeze validation failure
  (the A1-Q3 `estimate:` precedent). **(b) run-time streak:** AT-L11. No runtime LLM "value
  judgment" dispatch exists in this leg (it would spend tokens to save tokens).
- **AT-L11 — Streak-earned downshift ("slow down") with re-earn damper (freeze-gate v1 HIGH-4):**
  when a class×tier accumulates **K = 3** `[TUNABLE — VETO-FLAG-2]` consecutive FIRST-PASS gate
  acceptances within the run, subsequent same-class build dispatches step down one rung
  (floor-clamped; AT-L4 roster exempt; bump-carrying tasks exempt per AT-L1). Hysteresis is
  asymmetric by design: ONE gate rejection or standing reroll anywhere in the class clears the streak
  and restores the L0 resolution immediately (fast up, slow down). **Damper:** a rejection on a
  DOWNSHIFTED dispatch additionally DOUBLES K for that class for the run's remainder — a class that
  proves it can't pass a rung down stops oscillating instead of re-earning every K+1 tasks.

### Leg D — the premium budget envelope (AT-4)

- **AT-L12 — `models.premium.budget`:** `{calls: N}` (primary — orchestrator-side dispatch counting,
  platform-independent, always computable) with optional `{tokensOut: X}` where the host surfaces
  usage (usage_meter honesty: token budgets DEGRADE to the call budget when the platform reports
  nulls — never fabricated accounting). Default **N = 10 premium calls per run** `[TUNABLE —
  VETO-FLAG-1]`. Absent `budget` with the NEW scope form ⇒ the default N; with the OLD scope form ⇒
  unlimited, exactly as D148 shipped (BC).
- **AT-L13 — Spend discipline (freeze-gate v1 MED-8 fold):** **FCFS with a floor reservation** — the
  last **2** budget calls `[TUNABLE]` are reserved for `freeze-gate-verdict` / `re-gate-after-hold`
  events; a non-reserved event arriving with only reserved budget left dispatches at the anchor (no
  premium), LOUD. Concurrent-wave double-spend is prevented by counting at DISPATCH COMMIT (the
  conductor is the single dispatcher — one counter, no cross-process race); the counter's durable
  recount is the AT-L7 `tier:` DECISION lines. Exhaustion ⇒ premium LAPSES to the anchor for the
  run's remainder: LOUD DECISION + degraded record `{scope:"premium", reason:"budget-exhausted"}` +
  handoff note (CA-L30 discipline reused). No re-offers mid-run.
- **AT-L14 — Fail-bump premium spend:** a bumped attempt reaching the premium rung is legal ONLY in
  advanced+approved AND for `critical|coding` work (R-9: economy NEVER runs premium — an economy bump
  ceilings at the anchor), and ONLY via its registry event (`fail-bump-escalation` ∈ scope.events —
  conjunct-#2 satisfiable by shape, freeze-gate v1 HIGH-3).

### Leg E — scope-form BC + the gate (AT-5)

- **AT-L15 — Two scope forms, TYPE-DISPATCHED (freeze-gate v1 MED-7):** `scope` is one JSON key;
  a LIST value ⇒ the v0.2.1 work-class semantics BYTE-FOR-BYTE; an OBJECT value ⇒ the new adaptive
  form (`{events, budget}`); any other type, unknown event names, unknown object keys, or a non-int
  budget ⇒ load-guard RAISE (GB12/D45). **Object-form `events` key semantics (re-gate LOW-4):**
  ABSENT `events` in the object form ⇒ RAISE (the hand-edit-error posture — never inferred); an
  explicit `events: []` ⇒ legal no-op (premium never fires; the operator said so on purpose). (The v1 "both forms ⇒ RAISE" clause is struck —
  `json.loads` collapses duplicate keys last-wins, so the both-case is unobservable; type-dispatch
  makes it structurally impossible instead.)
- **AT-L16 — The approval pitch is the assurance (operator requirement verbatim):** the preflight
  premium gate's NEW-form disclaimer: *"Approving this sends exactly the <N> hard-moment events in
  your config's `scope.events` — listed here verbatim at the prompt — to <premium-rung>, capped at
  <budget.calls> calls this run; everything else tiers down as usual. Decline to stay on your
  current model at no added cost."* The enumeration is READ FROM CONFIG at the prompt, never a
  hand-maintained prose list (re-gate MED-3 — an under-enumerated pitch is a consent defect). The four conjuncts, `grantedMode` lapse, and the decline arms (D148 / kata-preflight
  0.2.1) are UNCHANGED.
- **AT-L17 — Family-agnostic + rename:** all prose says **"the premium rung,"** never "the Fable
  gate." The family ladder registry gains an optional per-family `premium` rung (anthropic: `fable`;
  others absent until registered — e.g. an `openai` ladder when GPT-5.6-class pricing lands).
  `premium.offer` remains an explicit id exactly one rung above the anchor IN ITS FAMILY; no
  registered rung / wrong relation ⇒ NO-FIRE + board NOTE (D148 generalized).
- **AT-L17b — Mid-run `/model` switch (freeze-gate v1 MED-13):** an anchor change RESETS ALL adaptive
  state — bump counters, streaks, dampers (budget spend does NOT reset — money spent is spent) —
  with a board NOTE naming the reset. Anchor-relative state re-based against a different ladder is
  undefined arithmetic; reset is the only honest posture (tracks D148 §3.4's switch handling).

### Leg F — L2 acceptance routing (contract now, activation deferred) (AT-6)

- **AT-L18 — The L2 contract:** for class c at mode m, the base row = the CHEAPEST tier t with ledger
  `firstPassAcceptanceByClassTier["c×t"] ≥ θ (0.85 [TUNABLE])` AND `n ≥ min_samples (5)` over
  NON-calibration rows, **clamped to ≤ the L0 row** (L2 may never raise the base above L0 — a cost
  increase needs an event or an approval, never a data inference; freeze-gate v1 LOW-18). No
  qualifying tier ⇒ the L0 row. Activation = `models.adaptive.l2: true`, default ABSENT ⇒ OFF.
- **AT-L19 — L2 is NAMED-DEFERRED at ship:** ledger has 5 rows, mostly calibration-flagged. L2 ships
  as contract + tests + OFF default; activation waits for post-R6 instrumented-run volume (one data
  pipeline shared with the calibration follow-on). Never a silent activation.

### Leg G — observability + fail-closed (AT-7)

- **AT-L20 — Telemetry additions are VERSION-SAFE (freeze-gate v1 HIGH-5 fold):** ledger rows STAY
  `v:3`; `tierEvents: [{at, dispatch, from, to, reason}]` and `verdictByTier` land as ADDITIVE
  OPTIONAL KEYS on the v3 row IFF the shipped strict reader provably tolerates unknown v3 keys
  (verified at build with a pinned test); if it does not, they ship in a SIDE ARTIFACT
  (`.kata/telemetry/tier-events-<runId>.json`, durable-citation rules applying) and the ledger is
  untouched. **No `v:4` is minted in this initiative** — a v4 row would RAISE in every deployed
  v0.2.1 reader mid-scan (the shared-ledger install model makes minting a version a fleet migration,
  not a feature).
- **AT-L21 — Fail-closed loading (D136):** malformed `models.premium`/`models.adaptive` (wrong-typed
  scope, unknown events, non-int budget/thresholds) ⇒ load-guard RAISE/STOP — never a silent
  fall-through to unlimited premium OR to no-premium. Absent keys ⇒ documented BC defaults only.
- **AT-L22 — A/B honesty + benchmark pinning (freeze-gate v1 LOW-19):** any efficiency claim cites
  arm/protocol/n + non-attribution caveats (LIVE-PROOF §5 discipline); benchmark/bake-off arm
  definitions MUST pin the full `models.adaptive` + `premium.scope` state (adaptive modulation is an
  arm variable, never ambient).

## §3 Config schema deltas (exact shapes, all additive)

```jsonc
"models": {
  "anchor": "session", "family": "auto", "coderFloor": "sonnet",
  "premium": {
    "offer": "fable", "approved": true, "grantedMode": "advanced",
    // EITHER (v0.2.1 form — LIST ⇒ run-long work-class semantics, byte-for-byte):
    "scope": ["critical", "coding"],
    // OR (NEW adaptive form — OBJECT ⇒ event-scoped + budgeted):
    "scope": {
      "events": ["freeze-gate-verdict", "re-gate-after-hold", "escalation-adjudication",
                  "fix-loop-diagnose", "final-initiative-review", "gate-rejection-rework-review",
                  "fail-bump-escalation"],
      "budget": { "calls": 10 }            // optional tokensOut where the host surfaces usage
    }
  },
  "adaptive": {                             // NEW block — ABSENT ⇒ every adaptive leg OFF (load-time BC).
    "failBumpAt": 2,                        //   Block PRESENT ⇒ consent; any absent KEY inside a present
    "streakDownAt": 3,                      //   block takes the default shown here (pinned per-key
    "planComplexityDownshift": true,        //   semantics — freeze-gate v1 HIGH-6).
    "evaluatorEscalate": true,
    "l2": false                             // AT-L18 activation gate, default OFF
  }
}
```

**BC matrix (every leg: absent ⇒ what):** `models` absent ⇒ inherit everywhere (R3, untouched) ·
`premium` absent ⇒ frozen tiering byte-for-byte (D148) · `scope` list form ⇒ v0.2.1 semantics
byte-for-byte · **`adaptive` absent ⇒ ALL adaptive legs OFF** (load-time; no retroactive flip —
the D147/CA-L34 discipline) · **bootstrap writes the full `adaptive` block explicitly at its next
COMPOSITION** (a config bootstrap composes is new consent — the "bake it in" arm; the block's
PRESENCE is the unambiguous marker, no provenance detection needed) `[VETO-FLAG-3: keep this
compose-ON/load-OFF split, or strict opt-in everywhere]`.

## §4 Acceptance criteria (default-FAIL, runnable at the gate)

1. No adaptive inputs ⇒ byte-identical resolution to v0.2.1 (golden test, 48-skill × 3-mode matrix).
2. Fail-bump: 2 arranged rejections ⇒ attempt-3 one rung up + `tier:` DECISION; ceiling respected per
   mode; the anchor-landing bump emits OMIT never the anchor id (AT-L2b mutation-pinned); the
   essential sonnet-anchor degenerate no-op is asserted AS a no-op (documented behavior).
3. Streak: 3 first-pass acceptances ⇒ rung down; one rejection ⇒ immediate restore; rejection on a
   downshifted dispatch ⇒ K doubled (damper mutation-pinned); a bump-carrying task is never
   downshifted (AT-L1 override pinned).
4. Evaluator ladder: red checkpoint ⇒ economy `reroll` ⇒ exactly one re-adjudication STRICTLY below
   anchor; advanced-Anthropic (economy = anchor−1) ⇒ leg inert, zero extra calls; `continue` never
   re-adjudicates; an overturned verdict does not increment the bump counter.
5. Budget: N=3 with reservation 2 ⇒ a non-reserved event at remaining=2 dispatches at anchor; a
   freeze-gate event spends reserve; exhaustion ⇒ lapse DECISION + degraded record; counter recounts
   correctly from `tier:` lines after a simulated conductor restart.
6. Scope forms: list ⇒ zero adaptive premium behavior; object with unknown event ⇒ load RAISE;
   non-int budget ⇒ RAISE; wrong-typed scope ⇒ RAISE.
7. Premium never fires: economy class (even bumped), essential/standard modes, unapproved, wrong-rung
   offer, budget-exhausted — 5-way matrix (D148 1728-cell precedent extended).
8. Telemetry: additive v3 keys round-trip through the SHIPPED strict reader (or the side-artifact leg
   activates — whichever AT-L20's build-time verification selects); v0.2.1-era reader reads a
   new-code ledger without raising (the reverse-direction test freeze-gate v1 HIGH-5 demanded).
9. Anchor switch mid-run ⇒ adaptive state reset + board NOTE; budget spend preserved.

## §5 Named deferrals

- **L2 activation** (AT-L19) — post-R6 ledger volume; pipeline shared with the calibration follow-on
  (τ/weights + verdict×tier).
- **Trigger-#2 grounding pass as a tierable dispatch** — explicitly NOT converted (BLOCKER-2); if a
  future M4 amendment ever makes it a dispatch, it re-enters the registry then.
- **Cross-run per-class memory** — L2's job, never L1's.
- **Non-Claude live legs** — machinery is model-blind; live proof rides the existing deferral.
- **Second bump (2F)** — one bump per task in v1; re-trigger escalation is a calibration-informed
  follow-on.
- **`policyOverride`** stays unconsumed (forward-compat only, unchanged).

## §6 Grill ledger (AT-R1.. — resolved conversationally with the operator, 2026-07-05)

- **AT-R1** Keep differential or replace? ⇒ KEEP as L0 base + fallback; adaptive is a modulation
  layer. (Operator: "I concur on all of the above.")
- **AT-R2** Bake in or advanced-only capability? ⇒ Adaptivity in ALL THREE modes (downshift/thrift
  everywhere); PREMIUM stays advanced-only + operator-approved. (Operator: "smarter across the board
  with the advanced mode being more liberal with the use of fable.")
- **AT-R3** Other expensive models (GPT-5.6-class)? ⇒ family-agnostic premium-rung registry (AT-L17);
  all prose renamed off "Fable."
- **AT-R4** Evaluation in the mix? ⇒ fail-count bump (AT-L8), grounded low-value downshift (AT-L10),
  evaluator cheap-then-escalate (AT-L9) — orchestrator-side signals only, D33-clean at runtime; one
  NEW plan-frozen judgment surface named honestly (§1).
- **AT-R5** Which signals count as "fails over a certain amount"? ⇒ gate rejections + STANDING ladder
  rerolls (mechanical, already recorded); never worker self-reports.
- **AT-R6** "Low value" grounding? ⇒ plan-frozen complexity rating + earned streaks — two mechanical
  runtime signals, no runtime LLM value-judgment dispatch.
- **AT-R7** Ship vehicle ⇒ v0.3.0 (minor — new capability), as the PAIRED gated amendments (§routing);
  jumps ahead of M2 shadow tasks in ship order BY OPERATOR DIRECTION (recorded so no fresh session
  re-derives "unsanctioned" — the D138 lesson).

### Freeze-gate history

**Gate v1 (2026-07-05, fresh-context, default-HOLD): HOLD — 2 BLOCKER / 4 HIGH / 8 MED / 5 LOW, all
folded into this v2:** B1 AT-L9 anchor breach ⇒ strictly-below-anchor clamp + inert-arm stated +
paired M4 routing; B2 phantom grounding event ⇒ struck (conductor-authored, not a dispatch); H3
fail-bump conjunct hole ⇒ `fail-bump-escalation` registry event; H4 bump×streak composition ⇒ pinned
order + per-task override + re-earn damper; H5 ledger v4 fleet-brick ⇒ no v4, additive-v3-keys-or-
side-artifact with reverse-direction test; H6 §3 self-contradiction ⇒ load-OFF pinned + per-key
semantics; M7 both-forms unobservable ⇒ type-dispatch; M8 budget priority/races/recount ⇒ FCFS +
reservation + dispatch-commit counting + DECISION-line recount; M9 overturned-verdict counting ⇒
standing-verdict-only; M10 anchor-id emission ⇒ AT-L2b OMIT contract; M11 kata-inline-eval exemption
⇒ AT-L4 roster; M12 event→site mapping ⇒ table + `fix-loop-diagnose` added; M13 /model switch ⇒
AT-L17b reset; M14 "no new judgment surface" overclaim ⇒ corrected; L15/L16 mode honesty ⇒ §0 note +
criterion 2; L17 ⇒ one bump per task; L18 ⇒ L2 ≤ L0 clamp; L19 ⇒ AT-L22 arm pinning. **Re-gate:
PENDING.**

**OPEN — [VETO-FLAG-1]:** premium budget default N=10 calls/run + reservation 2 (AT-L12/L13).
**[VETO-FLAG-2]:** F=2 fail-bump / K=3 streak-down (+damper ×2) (AT-L8/L11). **[VETO-FLAG-3]:**
compose-ON/load-OFF as drafted, or strict opt-in everywhere (§3). All three are values, not
structure — the re-gate can run with them flagged.

## §7 Tunables table (locked structure, tunable value)

| Tunable | Draft value | Home |
|---|---|---|
| `failBumpAt` (F) | 2 (fires once/task) | AT-L8 |
| `streakDownAt` (K) | 3 (+damper: ×2 on downshift-attributed rejection) | AT-L11 |
| `budget.calls` (N) | 10 | AT-L12 |
| Budget reservation | 2 (freeze-gate events) | AT-L13 |
| L2 θ acceptance | 0.85 | AT-L18 |
| L2 min_samples | 5 | AT-L18 |
| Event registry membership | 7 events (table AT-L5) | AT-L5 |

### Re-gate history (v2 → v3)

**Re-gate (2026-07-05, same fresh-context reviewer, fold-verification + v2-new-text sweep):
SHIP-WITH-FIXES — all 19 v1 folds verified RESOLVED (B1 arithmetic verified across the mode×family
matrix; H5's additive-v3-keys leg verified against the shipped no-whitelist reader); 3 MED + 5 LOW
fresh wording findings, all folded into this v3:** MED-1 `fail-bump-escalation` dual-semantics ⇒
conjunct-coverage-only pin (AT-L5 row + AT-L6); MED-2 −2 downshift stack ⇒ downward modulation
capped at −1/dispatch, no stacking (AT-L1); MED-3 under-enumerated consent pitch ⇒ disclaimer reads
`scope.events` from config verbatim (AT-L16); LOW-4 absent-`events` RAISE / explicit-`[]` no-op
(AT-L15); LOW-5 downshift population = `coding`-class enum term (AT-L4); LOW-6 evaluator-cost
citation corrected to pre-fix TP 0/57 + post-fix unmeasured (AT-L9); LOW-7 Amendment-#6 scope
includes the ledger additive keys (header); LOW-8 freeze-act must draft both amendment texts
(header). **Next: operator resolves VETO-FLAG-1/2/3 ⇒ FREEZE (drafts the paired amendment texts,
assigns D≥150) ⇒ plan ⇒ build as v0.3.0.**
