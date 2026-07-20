---
spec: advisor-executor
status: COMPILED 2026-07-19 — the frozen compilation of the GRILL-LEDGER (28 LOCKED entries
  G-1..G-9, S-1..S-27, EV-1; five convergence passes HOLD(8)→HOLD(3)→HOLD(3)→HOLD(2)→SHIP);
  awaiting the adversarial freeze-gate. Nothing in this document is built; every claim of
  existing behavior is file:line-cited against the current tree (PD-2).
source_of_truth: .planning/specs/advisor-executor/GRILL-LEDGER.md — this DESIGN compiles it;
  where any sentence here and a LOCKED ledger entry diverge, the ledger governs.
intent: INTENT.md (frozen, kind version-up, target self) — goal + 8 acceptance criteria.
new_d_records: assigned at freeze (next free ≥ D167 — verify against DECISIONS.md tail)
tags: [kata/spine, advisor, fable-target, premium-carve-out, advisor-executor]
---

# Advisor consult (`kata-advise`) — the advisor-executor pattern (COMPILED DESIGN)

## §1 Goal + corrected INTENT restatement

**Goal (frozen INTENT, verbatim):** *"Close the gap that hard tasks burn blind retries: give the
loop a scoped, anchor-relative Fable-tier Advisor consult surface (advisor-executor pattern).
Execution/coding workers can ask narrowly-scoped questions on intensive issues; the evaluation
mechanic consults the advisor after a generation reset or repeated failures instead of another
blind retry; advanced runs get it by default (bootstrap consent), standard runs opt in once per
RUN at preflight (post-design-freeze, pre-execution); essential is excluded; advisor availability
across phases (planning = advanced-only, execution + fix-loop = both granted modes, gate +
closeout = never) is decided by design."*

**Corrected-wording restatement (S-19d, G-5, G-8, S-23c).** Two wordings from the pre-grill
draft were deliberately superseded during the grill and are already embedded in the frozen
INTENT text above; they are restated here so no reader regresses to the draft:

1. **Once per RUN, not once per session** (G-5): the standard-mode opt-in is asked exactly once
   per run at kata-preflight (post-freeze, pre-execution), recorded in `kata.config`
   (`advisor.approved` + grant scope) for that run. No session-identity machinery; a second run
   in the same conversation asks again (accepted trade-off).
2. **Essential is EXCLUDED, not included** (G-8): advisor = standard + advanced only. Essential
   gets no advisor and no ask — it stays the lean budget mode. The draft's "standard/essential"
   wording is dead.

**The S-23(c) evaluator instruction, verbatim (LOCKED):**

> *"Evaluator instruction pinned: AC #3 is graded per the G-5/G-8 recorded supersessions
> (once-per-RUN, essential excluded) — a literal reading of the frozen INTENT wording is NOT a
> failure."*

(The frozen INTENT's `readiness` field carries the same instruction: *"Evaluator instruction:
AC #3 is graded per the G-5/G-8 recorded supersessions (once-per-RUN, essential excluded)."* —
INTENT.md:42-43.)

## §2 Fable-usage-on-standard assessment (grounded, cited — satisfies INTENT AC #5)

### 2.1 The anchor-relative routing table (D59/D131 — the L0 base)

Model selection is a differential off the operator's session model (the **anchor**), resolved at
dispatch by `kata_models.resolve()` — never a hard-baked ID (CLAUDE.md "Model routing (D59)").
The Anthropic family ladder is `haiku < sonnet < opus < fable < mythos`
(`tools/kata_models.py:64`; ID map `:81-87` — `fable → claude-fable-5`). The per-family
step-count table (`tools/kata_models.py:238-248`, commented `:209-215`):

| Anthropic (mode × work-class) | critical | coding | economy |
|---|---|---|---|
| advanced  | 0 (anchor) | 0 (anchor) | −1 |
| standard  | 0 (anchor) | −1 | −2 |
| essential | −1 | −2 (coder-floor raised) | −2 |

Zero-step cells inherit by omission (never re-select the anchor's own id — the R7/Fable-outage
protection, `kata-orchestrate/SKILL.md:902-912`).

### 2.2 Where Fable lives per mode — fable-anchored sessions

On a **fable-anchored session** (the dogfood configuration; this run's anchor per the ledger
header), Fable is reached by **inherit-by-omission on every zero-step cell** — no premium
machinery involved:

| mode | critical | coding | economy |
|---|---|---|---|
| advanced  | **Fable** (inherit) | **Fable** (inherit) | Opus |
| standard  | **Fable** (inherit) | Opus | Sonnet |
| essential | Opus | Sonnet (R1 coder floor, `config.md:53`) | Sonnet |

So on a fable-anchored **standard** run, all critical-class work (judgment, planning, grilling,
evaluation, the gate) already runs at Fable today (`kata_models.py:242`,
`("standard","critical"): 0`). The preflight case-(a) gate confirms/declines the fable *anchor*
itself with the cost warning (`skills/coordinate/kata-preflight/SKILL.md:69-76`).

### 2.3 Where Fable lives per mode — opus-anchored (and lower) sessions

On an **opus-anchored session**, no step-down cell can reach Fable (all steps are ≤ 0). Fable is
reachable **only** via the D148 premium branch: the recorded `models.premium` approval whose
`offer` sits exactly one rung above the anchor, firing only when all four conjuncts hold —
`approved` ∧ conjunct #2 (work-class/event in scope) ∧ offer exactly +1 ∧ **`mode ==
"advanced"`** (`kata_models.premium_status`, `tools/kata_models.py:520-612`; the resolve premium
branch `:619-731`; D148, DECISIONS.md:2374-2398). The offer itself is made only when `anchor ==
opus ∧ mode == "advanced"` (`kata-preflight/SKILL.md:77-83`).

**Consequence for standard mode (the gap this feature closes):** a standard-mode opus-anchored
run has **zero Fable access on every path today** — `premium_status` returns NO-FIRE
`"mode-not-advanced"` (`kata_models.py:578-579`), the adaptive fail bump ceilings at the anchor
for standard (AT-L2; `kata-orchestrate/SKILL.md:983-987`), and Leg-B event escalation on
standard escalates only **to the anchor**, never above (`kata-orchestrate/SKILL.md:995-999`).
A sonnet- or haiku-anchored run is further still: `premium_rung_of` yields only +1
(`tools/kata_models.py:462-485`) — opus for a sonnet anchor, never Fable.

### 2.4 D148 premium mechanics summary (what this feature reuses, and what it must not touch)

- **Record:** `models.premium {offer, approved, scope (list|object form), grantedMode}` —
  `protocol/config.md:36`; written by bootstrap after the preflight gate.
- **Gate:** four conjuncts, fail-closed, NO-FIRE reasons enumerated and surfaced
  (`premium_status`, `kata_models.py:520-612`); malformed block RAISES (D136,
  `_validate_premium` `:492-517`).
- **Spend:** object-form budget, conductor-enforced via `kata_adaptive.can_spend` — FCFS with
  the last `RESERVE = 2` calls reserved for `freeze-gate-verdict`/`re-gate-after-hold`
  (`tools/kata_adaptive.py:105-108, 487-518`).
- **Failure semantics (CA-L30):** one-step chain premium → OMIT/inherit at the anchor; any
  premium dispatch failure lapses `approved` for the run; premium-only 401/403 =
  premium-unavailable, LOUD (`kata-orchestrate/SKILL.md:941-961`).
- **This feature's relation to it:** the advisor **reuses the gate PATTERN and the ladder
  helpers, not the premium record or pool** — `models.premium` and `ADAPTIVE_EVENTS` are
  **byte-untouched** (S-16, S-20, S-4; AC #6). The G-2 "D148 narrow amendment" is realized as a
  **sibling gate** (§3.2), not an edit to the premium contract.

## §3 The LOCKED contract (the ledger, compiled by subsystem — supersession chains flattened)

Every rule below states only the **final surviving** form; the cited ledger IDs carry the
provenance. Builders MUST NOT re-decide, weaken, or extend any of them.

### 3.1 Naming + glossary (G-1, S-22, S-26a, S-27)

- Skill **`kata-advise`** · config block **`advisor`** · canonical concept **advisor consult**.
- The deferred kata-reason concept is re-titled plain **"Reason (the decider)"** — never "the
  Advisor" (cheap prose edit, already applied to CONTEXT.md). The CONTEXT.md "## Advisor
  consult" glossary section (CONTEXT.md:753-788) is already refreshed to the S-16 grant model
  and the S-24 fable-target rule (S-22/S-26a/S-27 — applied in the grill session; **no further
  CONTEXT.md edit is in this build's scope**).
- Advisory, never authoritative (S-2): advice never changes a gate verdict, is never
  auto-applied, never expands the frozen goal. The default-FAIL gate and LOCKED decisions are
  untouchable by it.

### 3.2 The sibling legality gate (S-16 · S-21 · S-24 — supersedes S-8's premium-machinery
legality and S-12's `grantedMode:"standard"` premium edit)

**`advisor.approved` is the SOLE advisor legality record.** Advisor legality is fully DECOUPLED
from `models.premium` (byte-untouched — no schema change, no shared bool; a preflight premium
decline never touches the advisor grant and a bootstrap advisor veto never touches the premium
offer).

**New pure functions in `tools/kata_models.py`** (sibling to, and shaped like,
`premium_status`/`premium_rung_of`):

- **`advisor_rung_of(family, anchor) -> str | None`** (S-24 — supersedes S-21(b)'s
  `premium_rung_of` conjunct and S-15(d)'s helper naming): normalizes the anchor
  (`_normalize_anchor` precedent, `kata_models.py:95-114`); `family == "auto"` derives via
  `family_of`. Returns:
  - `None` (arm (a) — inherit-at-anchor) when: the anchor is already fable/mythos-class
    (ladder index ≥ the ladder's `fable` index), OR the family is unknown / its ladder is
    empty, OR the ladder has no `"fable"` rung, OR the anchor is not on the ladder.
  - the family ladder's **`"fable"` rung id** for any sub-fable anchor (sonnet AND haiku
    anchors consult **fable**, never one-rung-above arithmetic). **Never mythos by default.**
  The multi-rung cost jump on low anchors is DELIBERATE — the feature IS a Fable-tier advisor
  (frozen goal); the budget pool bounds the spend. Non-Anthropic families (empty ladders,
  `kata_models.py:67-69`) return `None` ⇒ arm (a) inherit at the anchor, with an honest
  conductor NOTE that no fable-class rung exists in that family.

- **`_validate_advisor(advisor: dict) -> None`** — fail-closed shape guard (D136, S-5b),
  mirroring `_validate_premium` (`kata_models.py:492-517`), enumerating the FULL §4 key set:
  `enabled`/`approved` strict bools; `grantedMode` (when present) ∈ {"advanced","standard"};
  `budget` **REQUIRED in a present block** — a dict with strict ints `calls ≥ 0`,
  `0 ≤ reserved ≤ calls` (bools rejected; the layers-agree companion of the §3.5
  `resolve_advisor_budget` fail-close); `hooks` (when present) a dict with `failThreshold` a
  strict int ≥ 1 (S-18 — INTEGER; S-8's string-pointer rendering superseded), `rerollTrigger` a
  strict int, `fixLoopCeiling` a strict bool; `phases` (when present) a `list[str]` with every
  member ∈ {"planning", "execution", "fix-loop"}. Unknown keys — top-level, in `budget`, or in
  `hooks` — RAISE. **Both canonical bootstrap compositions (§3.4 advanced default and standard
  default) MUST round-trip this validator clean** (a composed default that bricks the
  load-guard is a producer bug caught at T1's tests, not at run time).
  Present-but-malformed ⇒ `ValueError` ⇒ load-guard STOP + escalate — never a silent OFF.
  Exported (as `validate_advisor_block`) so the orchestrate load-guard and the gate share ONE
  validator (the `resolve_budget`/`classify_premium_scope` layers-must-agree precedent,
  `kata_adaptive.py:477-483`).

- **`advisor_status(advisor, anchor, *, family, mode, event) -> {"fires": bool, "reason": str,
  "rung": str | None}`** — the sibling gate. Conjuncts (S-16 as re-armed by S-21/S-24), with
  NO-FIRE reasons enumerated in this precedence order (the `premium_status` register):

  | reason | condition |
  |---|---|
  | `"absent"` | `advisor` is `None` — no block; frozen behavior byte-for-byte (S-4) |
  | *(raise)* | present-but-malformed ⇒ `ValueError` (D136 — not a reason) |
  | `"not-enabled"` | `enabled` is not `True` (S-26e — `enabled` gates hook WIRING) |
  | `"not-approved"` | `approved` is not `True` (S-16 — `approved` gates SPEND; both required) |
  | `"mode-excluded"` | `mode` not in {"advanced","standard"} — essential and unknown modes fail closed (G-8) |
  | `"standard-not-granted"` | `mode == "standard"` and `grantedMode != "standard"` (the G-2 carve-out arm unsatisfied) |
  | `"no-event"` | no event supplied |
  | `"unknown-event"` | event ∉ `ADVISOR_EVENTS` (fail-closed classify) |
  | `"fires"` | every conjunct holds |

  **Rung arms (S-21, conjunct rewritten by S-24):** the gate COMPUTES
  `rung = advisor_rung_of(family, anchor)` and returns it in the status — the S-24 conjunct
  `rung == advisor_rung_of(anchor)` is satisfied **by construction**: the conductor dispatches
  `kata-advise` at EXACTLY `status["rung"]` (`None` ⇒ OMIT the model parameter — arm (a)
  inherit-at-anchor, no premium machinery consulted, S-7/S-21(a); a short-name ⇒ emit its
  `ID_MAP` id — arm (b)) and never proposes its own rung. On the fable-anchored dogfood
  configuration the feature is ALIVE via arm (a).

  **A NO-FIRE on ANY conjunct ⇒ unadvised-proceed with a surfaced reason (board NOTE) —
  NEVER a consult-at-anchor-without-consent, never a block** (S-21).

### 3.3 The `ADVISOR_EVENTS` sibling registry (S-20 — supersedes S-8's "join ADAPTIVE_EVENTS")

The five advisor events live in their **own** registry in `tools/kata_models.py` —
`ADVISOR_EVENTS: tuple[str, ...]` + `ADVISOR_EVENT_SITES: dict[str, str]` — sibling to and
shaped like `ADAPTIVE_EVENTS`/`ADAPTIVE_EVENT_SITES` (`kata_models.py:338-372`).
`ADAPTIVE_EVENTS` and the `models.premium.scope.events` vocabulary are **byte-untouched**; an
advisor event name appearing in `models.premium.scope.events` remains **ILLEGAL** (fail-closed
classify raises, exactly as today — `classify_premium_scope`, `kata_models.py:426-431`).

Each event cites its **real covering dispatch site** (MED-12 discipline — the conductor's own
non-dispatched judgment can never be an event; every site below is a real `kata-advise`
DISPATCH):

| Event | Covering dispatch site |
|---|---|
| `advisor-fail-threshold` | the conductor's auto `kata-advise` dispatch at the S-11 failure threshold (bump-pending observed, task unadvised) — kata-orchestrate loop, before the deferred bump (§3.6a) |
| `advisor-reroll-grounding` | the conductor's auto `kata-advise` dispatch at corrective-action ladder **trigger #2**, solicited BEFORE the tightened redispatch brief is authored (`kata-orchestrate/SKILL.md:817-823`; §3.6b). NOTE: the struck `ladder-trigger-2-grounding` ADAPTIVE event was removed because the *grounding pass* is conductor-authored, not a dispatch (`kata_models.py:349-352`) — THIS event covers the new `kata-advise` dispatch itself, a real dispatch, so MED-12 is satisfied without reversing that ruling |
| `advisor-fix-loop-ceiling` | the conductor's `kata-advise` dispatch at the fix-loop thrash valve, ONLY after a `kata-diagnose` **fix-problem** verdict (`kata-orchestrate/SKILL.md:1235-1253`; §3.6c) |
| `advisor-worker-request` | the conductor's `kata-advise` dispatch resolving an execution worker's `advice-requested` escalation (§3.7; escalation machinery `kata-orchestrate/SKILL.md:1054-1080`) |
| `advisor-planning-consult` | (a) the conductor's `kata-advise` dispatch resolving a **planner-worker's** `advice-requested` escalation during in-harness plan/design authoring (same escalation machinery — S-17a); (b) the session conductor's own direct `kata-advise` dispatch during the conductor-inline grill (kata-initiate Phase 5 — S-17b). Both advanced+granted only. No third path |

### 3.4 Two-moment grant model + opt-in UX + headless posture (G-9, G-5, S-6, S-26b/c/d, S-23d)

- **ADVANCED:** the advisor consent question is asked at **BOOTSTRAP composition**
  (pre-planning) — "on by default" operationally = pre-checked, one veto-able consent; planning
  consults are thereby legal in advanced. Bootstrap writes
  `{enabled: true, approved: <consent>, grantedMode: "advanced", budget: {calls: 10, reserved: 2}}`
  (`grantedMode: "advanced"` is cosmetic — the advanced mode-arm ignores it; recorded for config
  completeness, S-23d). *Headless/non-TTY advanced composition:* the pre-checked consent stands
  without an interactive veto — G-9's cited provenance is the `models.adaptive`
  compose-consent precedent (`kata-bootstrap/SKILL.md:207-214`: composition itself is consent);
  the veto is the attended affordance. Surfaced in the composed-config summary, never silent.
- **STANDARD:** the ask stays at **kata-preflight** (post-freeze, pre-execution — S-6, D29;
  alongside the premium offer, `kata-preflight/SKILL.md:64-111`, as its own independent
  question). Asked exactly **once per RUN** (G-5). Accept ⇒ preflight writes
  `approved: true, grantedMode: "standard"`. **Decline ⇒ `approved: false` and `grantedMode`
  ABSENT** — `approved` is authoritative; no grantedMode value is ever required for the
  declined state (S-26b). Bootstrap composes the standard block as
  `{enabled: true, approved: false, budget: {calls: 5, reserved: 1}}` until the preflight ask.
  **Standard planning has NO advisor** — the honest temporal consequence of the post-freeze
  placement (G-9; the G-4 matrix as amended).
- **Headless/non-TTY standard preflight ⇒ default OFF + surfaced note — never blocks** (G-5/S-6).
- **ESSENTIAL:** no block, no ask (G-8). Bootstrap essential compositions write **no `advisor`
  block** (absent ⇒ OFF strictly, S-4).
- **Absent block (pre-feature / never-re-bootstrapped configs) ⇒ OFF strictly — NO implicit
  `mode == advanced` ON**; a builder must never infer the grant from the mode (G-9, S-4).
- **Grant lapse (S-15c, S-19b, S-26c):** a mid-run `/model` switch or mode change lapses the
  advisor grant in BOTH modes — no legal re-ask moment remains in-run; the run completes
  unadvised with a loud NOTE (never silent); spend already recorded is preserved. The next run
  re-consents at its mode's moment (AT-L17b analog).
- **Conductor-inline grill consults (S-17b) are ALIVE only when a grant already exists at grill
  time** (re-entrant configs / loop-back runs); on first-run flows the gate fail-closes —
  recorded as the DELIBERATE temporal consequence of G-9, same class as standard planning
  (S-26d).

### 3.5 Budget pool + reserves + spend state (G-6, S-12, S-13, S-23a/b, S-19a)

- **Own pool, sole spend authority (S-12):** advisor dispatches NEVER draw from the premium
  events pool and never call the premium `can_spend`. LEGALITY = the §3.2 sibling gate;
  SPEND = exclusively `advisor.budget` via an own `can_spend`-style check in
  `tools/kata_advisor.py` (FCFS + floor reservation — the copied shape of
  `kata_adaptive.can_spend`, `tools/kata_adaptive.py:487-518`: a reserved event may spend down
  to zero, `remaining ≥ 1`; a non-reserved event needs `remaining > reserved`).
- **Mode-scaled defaults (G-6):** standard = **5 calls / 1 reserved**; advanced =
  **10 calls / 2 reserved**.
- **Reserve mapping (S-13 — supersedes G-6's "freeze-gate-class" phrasing, which was WRONG; G-4
  locks the gate to no-consult, no advisor event is freeze-gate-class):** standard reserve (1)
  covers `advisor-fix-loop-ceiling`; advanced reserve (2) covers `advisor-fix-loop-ceiling` ×1
  + `advisor-reroll-grounding` ×1 — the two late-run hard moments. Realized as per-mode
  reserved-event sets in `kata_advisor` (`ADVISOR_RESERVED_EVENTS`): standard =
  `("advisor-fix-loop-ceiling",)`, advanced = `("advisor-fix-loop-ceiling",
  "advisor-reroll-grounding")`.
- **Grant-before-dispatch (S-19a):** a granted-then-FAILED consult dispatch CONSUMES its budget
  call (matches the kata_adaptive dispatch-commit precedent, `kata_adaptive.py:521-535`;
  prevents retry-mining); the failure is still a loud lapse per S-5(a).
- **Exhaustion ⇒ loud lapse** for the run's remainder (CA-L30 discipline): board DECISION +
  state `lapses[]` entry + handoff note; the loop proceeds UNADVISED (never blocks).
- **Worker-request cap (S-23a):** worker-requested consults are capped at **2 per task**
  (surfaced NOTE beyond; the budget is still the outer bound) — one pathological task can never
  drain the pool. The per-task count is derived from the durable advice artifacts
  (`.kata/advice/<task-id>-*.json` ordinals) — no extra counter state.
- **Spend state home (S-23b, extended by EV-1):** `.kata/state.json` gains an `advisor` field
  `{used: int, byEvent: {<event>: n}, lapses: [str], outcomes: {"<task-id>-<n>": <outcome|null>}}`
  — single-writer orchestrator via `kata_board.write_state`; restore recounts `used`/`byEvent`
  from the board's advisor DECISION lines (the fix-loop-counter recount precedent). Every
  consult writes a `tier:`-style board **DECISION** line (AT-L7 register), rendered by
  `kata_advisor.render_advisor_decision` — the durable recount trail.

### 3.6 Hooks (auto-consult wiring — all orchestrator-side; engines byte-untouched)

**(a) Failure threshold — advise-first, bump-second (G-3, S-11, S-18, S-25, S-27).**
- **Counter:** `models.adaptive` PRESENT ⇒ the ENGINE counter is authoritative — the
  `bump_pending` observable (`tools/kata_adaptive.py:299-326`; gate rejections + standing
  rerolls counted exactly as the engine counts them via `record_gate_result` /
  `record_standing_reroll`, `kata-orchestrate/SKILL.md:1009-1016`); G-3's "2 gate rejections" is
  shorthand for that counter, threshold = `failBumpAt`. `advisor.hooks.failThreshold` is
  IGNORED with a surfaced load NOTE if set to a conflicting value (S-18). `models.adaptive`
  ABSENT ⇒ the conductor maintains its own per-task rejection count **mirroring engine
  semantics EXACTLY** (gate rejections + standing rerolls both count), threshold =
  `advisor.hooks.failThreshold` (integer, default 2). One semantics, two sources, never dual
  counters on one run (S-18). The advisor never requires the adaptive block (S-11a).
- **Ordering (G-3):** at the threshold the loop fires a SCOPED advisor consult FIRST (event
  `advisor-fail-threshold`); the advice feeds the redispatch brief at the SAME worker rung. If
  the advised attempt also fails, the existing D150 +1 rung bump fires — the standing advice
  travels with the bumped redispatch. Consult and bump are ORDERED consequences of one counter,
  never simultaneous by default (both-at-once was REJECTED as the default; it may become a
  future config posture — not this build).
- **Deferral mechanics (S-11b — `kata_adaptive` BYTE-UNTOUCHED):** advise-first is
  ORCHESTRATOR-SIDE bump deferral. On bump-pending with **no standing advice** for the task,
  the conductor dispatches the consult and redispatches at the prior attempt's rung **without
  consulting `modulate_step` for that one dispatch** (the pending bump is not consumed; the
  engine's counters/state are not touched for the deferral). On the NEXT failure the normal
  path runs — `bump_pending` is still True, `modulate_step` consumes the bump (+1), and the
  standing advice rides the bumped brief. Evidence recording (`record_gate_result`,
  `record_standing_reroll`) continues normally throughout — advised redispatches count toward
  streak/damper accounting as normal attempts, no special-casing (S-15e).
- **Standing-advice suppression (S-25 generalized by S-27):** ANY standing advice for a task
  (auto OR worker-requested — i.e. any `.kata/advice/<task-id>-*.json` exists) suppresses
  **BOTH** auto hooks (fail-threshold AND reroll-trigger): one diagnosis per task; the standing
  advice rides every subsequent redispatch; at threshold the bump consumes normally (G-3's
  advice-travels rule). The fix-loop-ceiling consult remains separate (different phase,
  reserve-backed). Corollary (S-11c): at most ONE auto-consult per task across the two auto
  hooks — they share the guard; no double-fire.

**(b) Reroll trigger #2 (G-4, S-19c).** At corrective-action ladder **trigger #2** (same task —
the grounding pass before any second reroll, `kata-orchestrate/SKILL.md:817-823`), when no
standing advice exists (shared once-guard, §3.6a): advice is solicited FIRST (event
`advisor-reroll-grounding`), **BEFORE the tightened redispatch brief is authored, and folded
INTO it** — one deterministic order (S-19c). The grounding pass itself remains
conductor-authored and untiered (BLOCKER-2's ruling stands).

**(c) Fix loop — diagnose-first (S-14, G-4).** At the fix-loop thrash valve
(`kata-orchestrate/SKILL.md:1235-1253`), `kata-diagnose` dispatches FIRST (cheap
classification, existing contract untouched). The advisor consult (event
`advisor-fix-loop-ceiling`, reserve-backed) fires ONLY on a **fix-problem** verdict — advice
feeds the resumed fixing. A **plan-problem** verdict escalates human-required as today,
WITHOUT a consult (the human decides; advice would pre-empt them). Never parallel.

**(d) The gate and closeout NEVER consult (G-4).** `kata-evaluate` / `kata-inline-eval` never
consult (judge independence — a D33-class extension of no-self-cert: builder and judge never
share an advisor). Closeout: no.

### 3.7 Worker advice-requested escalation (S-1, S-9, S-10, S-17, S-23a)

- **Only the conductor dispatches `kata-advise`** (S-1 — spine L3/L8; mirrors the built
  `kata-research` escalation-dispatch pattern, `kata-orchestrate/SKILL.md:1054-1080`). A worker
  requests advice by raising an escalation of the **new kind `advice-requested`** in
  `protocol/escalation.md` (S-9) — **non-halting/async**: the standard escalation contract
  applies (S-10) — the requesting attempt ENDS, the task and its DAG-dependents park, the
  frontier keeps draining.
- On payload return the task **redispatches with the advice payload INLINED VERBATIM in the
  redispatch brief** — workers in isolated worktrees cannot read the main tree's `.kata/`; a
  path reference would be unreadable; the JSON is embedded under a marked `ADVICE` section
  (S-10). `.kata/advice/<task-id>-<n>.json` remains the durable conductor-side record (S-3).
  The advised redispatch is a NEW attempt on the attempt branch, counted normally (S-15e).
- **Planner-workers** (in-harness plan/design authoring, dispatched during the freeze stage)
  raise `advice-requested` through the SAME machinery; the kata-design-doc / kata-plan-tier
  dispatch briefs gain the advice-request instruction, **advanced+granted only** (S-17a).
  Classified as event `advisor-planning-consult`.
- Cap: 2 worker-requested consults per task (S-23a; §3.5).

### 3.8 Advice payload — the FINAL `protocol/advice.md` schema (S-3 ∪ G-7, pinned by S-15a)

Machine-ingestible, agent-consumed, automated in-execution (G-7): the response is consumed by
the AGENT (conductor → redispatch brief / requesting planner), never a human-facing artifact on
the hot path; the human sees an AFTER-ACTION ROLLUP in the run report/closeout. One artifact
per consult: **`.kata/advice/<task-id>-<n>.json`** (n = 1-based per-task consult ordinal).
"Scoped context refs" ≡ the `scopedContext` shape below — nothing else (S-15a).

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

- `response.sketch` is OPTIONAL and always `nonAuthoritative: true` — never applied verbatim;
  the executor owns implementation (G-7).
- `meta.rungUsed` is the dispatched rung short-name, or `null` for an arm-(a) inherit-at-anchor
  consult.
- Board lines (S-3): a **NOTE** at request, a **DECISION** at disposition (plus the per-consult
  spend DECISION line, §3.5). Reports never gate.

### 3.9 Telemetry + effectiveness pairing (S-15b, S-23b, EV-1)

- **Run-ledger:** the run's ledger row gains an **`advisor`** key
  `{consults: [<row>], byEvent: {<event>: n}, budgetUsed: int, budgetCap: int, lapses: [str]}` —
  the after-action rollup's data source. Realized as a presence-discriminated ADDITIVE key in
  `kata_telemetry.build_ledger_row` (the `verdictByTier`/`tierEvents` precedent,
  `tools/kata_telemetry.py:1259-1301`): ABSENT ⇒ omitted from the row entirely (pre-feature
  rows byte-preserved); PRESENT ⇒ validated fail-closed. *(Note: `tools/kata_telemetry.py` is
  therefore a modified file — required to wire S-15b end-to-end, PD-1; see §5.)*
- **EV-1 outcome pairing (LOCKED, ELEVATE-accepted):** each consult's telemetry row gains an
  OUTCOME, exact enum:
  **`advised-pass` / `advised-fail-bumped` / `advised-fail-ceiling`** — pure derived data
  written by the S-23(b) single-writer state path, surfaced in the after-action rollup.
  Derivation rule (stated so builders cannot diverge): the advised redispatch **passes its
  gate** ⇒ `advised-pass`; it **fails and the D150 bump then fires** for the task ⇒
  `advised-fail-bumped`; it **fails with no bump available** (bump already consumed /
  `models.adaptive` absent / rung at its mode ceiling) ⇒ `advised-fail-ceiling`. A run ending
  before the pairing resolves records an explicit `null` (honest absence, never fabricated —
  the telemetry precedent). Makes advisor ROI an evidence question for the E1/E2 calibration
  queue; future `failThreshold` tuning becomes evidence-driven.

### 3.10 Fail postures (S-5, S-19a/b, S-26c/e)

- **(a)** Consult dispatch failure ⇒ surfaced board NOTE + proceed **UNADVISED** — advice never
  blocks the loop (advisory ≠ gate). One-step lapse to unadvised-proceed — **never a ladder
  walk** (S-7); the consumed budget call stays consumed (S-19a).
- **(b)** Malformed `advisor` config ⇒ `ValueError` → load-guard STOP (D136 fail-closed).
- **(c)** No `model:` frontmatter on `kata-advise` (validator A1 guard,
  `tools/validate_skills.py:450-473`).
- **(d)** Rung resolution is anchor-RELATIVE via `advisor_rung_of` — never a hard-coded id
  (D59/D131; S-24).
- **(e)** Budget exhaustion / grant lapse ⇒ loud lapse, unadvised to completion (§3.4/§3.5).
- **(f)** `enabled: false, approved: true` (hand-edited) converges on no-consult with a
  surfaced NO-FIRE reason (S-26e).

### 3.11 BC (S-4, S-16, S-20 — AC #6)

- **Absent `advisor` block ⇒ every leg OFF; behavior byte-identical to today** (S-4 — the
  `models.adaptive` precedent, `protocol/config.md:37`).
- **`models.premium` byte-untouched** (S-16): no schema change, no new legal `grantedMode`
  value, no shared approval.
- **`ADAPTIVE_EVENTS` / `ADAPTIVE_EVENT_SITES` byte-untouched** (S-20); an advisor event in
  `models.premium.scope.events` stays ILLEGAL.
- **`tools/kata_adaptive.py` byte-untouched** (S-11b; the engine is only *observed* and
  *deferred around*, never edited).
- The default-FAIL gate is never weakened (S-2, G-4).

## §4 The FINAL `advisor` config block (schema of record — S-8 as amended by S-16/S-18/S-20)

```json
"advisor": {
  "enabled": true,
  "approved": true,
  "grantedMode": "standard",
  "budget": { "calls": 5, "reserved": 1 },
  "hooks": { "failThreshold": 2, "rerollTrigger": 2, "fixLoopCeiling": true },
  "phases": ["execution", "fix-loop"]
}
```

*(The example is a real composition: a standard-mode run after an ACCEPTED preflight opt-in —
internally consistent per §3.4. The advanced composition differs per §3.4: `grantedMode:
"advanced"`, `budget: {calls: 10, reserved: 2}`, `phases: ["planning","execution","fix-loop"]`.)*

| Field | Type | Semantics |
|---|---|---|
| `enabled` | bool | Gates hook WIRING (S-26e). Both `enabled` and `approved` are required to consult. |
| `approved` | bool | **The SOLE advisor legality/spend grant** (S-16). Written by bootstrap consent (advanced) or the preflight opt-in (standard). |
| `grantedMode` | `"advanced" \| "standard"`, optional | The mode the grant was recorded under. `"standard"` is the G-2 carve-out marker checked by the gate's standard arm. ABSENT on a declined standard run (S-26b); `"advanced"` is cosmetic — the advanced arm ignores it (S-23d). |
| `budget` | `{calls: int, reserved: int}` | The advisor's OWN pool (G-6): standard 5/1, advanced 10/2. `0 ≤ reserved ≤ calls`, strict ints. Reserve coverage per S-13 (§3.5). |
| `hooks.failThreshold` | int (default 2) | The standalone-counter threshold — consulted ONLY when `models.adaptive` is absent; otherwise the engine's `failBumpAt` is authoritative and a conflicting value here is IGNORED with a surfaced load NOTE (S-18 — INTEGER, superseding S-8's string-pointer rendering). |
| `hooks.rerollTrigger` | `2` | The corrective-action ladder trigger number the reroll-grounding hook rides (S-8). |
| `hooks.fixLoopCeiling` | bool (`true`) | Wires the fix-loop-ceiling hook (S-8; ordering fixed by S-14 regardless). |
| `phases` | string[] | **Documentation of the G-9 availability matrix — NOT an independent switch.** Bootstrap writes `["planning","execution","fix-loop"]` in advanced and `["execution","fix-loop"]` in standard; the gate + hook wiring enforce availability, never this field. |

Written by bootstrap **by construction** in advanced and standard compositions (§3.4);
**never written in essential** (G-8). Absent ⇒ all OFF (S-4). Malformed ⇒ load-guard STOP
(D136). MODEL legality lives in the §3.2 sibling gate — this block carries no model id
anywhere (D59/D131).

## §5 File-touch map

**New files:**

| File | Content |
|---|---|
| `tools/kata_advisor.py` | The pure advisor engine (Determinism Doctrine binds): `new_advisor_state()` (the §3.5 state shape); `resolve_advisor_budget(advisor)` (validated calls/reserved; **the G-6 mode defaults 5/1 · 10/2 are BOOTSTRAP-COMPOSITION constants documented in §4, NOT resolver fallbacks — the function FAIL-CLOSES (raises) on an absent or malformed `budget` in a present `advisor` block**, the hand-edit posture, agreeing with `_validate_advisor`'s budget-REQUIRED rule §3.2); `ADVISOR_RESERVED_EVENTS` (per-mode sets, S-13); `can_spend_advisor(calls, reserved_count, reserved_events, state, event)` (FCFS + floor reservation, the `kata_adaptive.can_spend` shape); `record_advisor_spend(state, event)` (grant-before-dispatch commit, S-19a); `ADVISOR_OUTCOMES` (the EV-1 enum) + `record_outcome(state, consult_id, outcome)` (fail-closed on unknown outcome); `render_advisor_decision(...)` + `recount_from_advisor_decisions(...)` (the board DECISION recount trail, S-23b); `ledger_fragment(state, cap)` (builds the §3.9 ledger `advisor` value). **`tools/kata_adaptive.py` is BYTE-UNTOUCHED.** |
| `protocol/advice.md` | The §3.8 schema of record: payload table, location/naming, board-line contract, producer/consumer (producer: the conductor composes the request from the escalation payload/hook context and folds the `kata-advise` response; consumer: the redispatch brief / requesting planner; rollup: report/closeout), G-7 non-authoritative-sketch rule, S-2 advisory-never-gates rule. |
| `skills/plan/kata-advise/SKILL.md` | The advisor skill. **Category `plan`** (STANDARDS §2 — judgment/consult work; S-1 mirrors `kata-research`, which lives in `skills/plan/`). Frontmatter per STANDARDS §1: `version: 0.1.0`, `status: experimental`, `agnostic: true`, **NO `model:` key** (A1 guard), `allowed-tools` a read-only set omitting Write/Edit (fresh-context, **no-write** — S-1/S-7). Body: consume ONE `protocol/advice.md` request; return the structured `response` object (diagnosis/approach/risks/citations/optional non-authoritative sketch); advisory-never-authoritative framing (S-2); never expand the frozen goal; scoped-context-only reading. Work-class: **`critical`** via a `SKILL_WORK_CLASS` entry (S-7; the R5 coverage test enforces presence). |

**Modified files:**

| File | Change |
|---|---|
| `tools/kata_models.py` | ADD (additive-only): `ADVISOR_EVENTS` + `ADVISOR_EVENT_SITES` (§3.3) · `advisor_rung_of` (§3.2) · `_validate_advisor`/`validate_advisor_block` + `advisor_status` (§3.2) · `SKILL_WORK_CLASS["kata-advise"] = "critical"`. `ADAPTIVE_EVENTS`, premium functions, ladders, ID_MAP untouched. |
| `tools/kata_telemetry.py` | ADD the presence-discriminated additive `advisor` ledger key to `build_ledger_row` + its fail-closed validator (§3.9; the `verdictByTier` precedent). Absent ⇒ row byte-preserved. |
| `protocol/config.md` | ADD the `advisor` row/section (§4 verbatim) to the schema table. |
| `protocol/escalation.md` | ADD `"advice-requested"` to the `kind` enum + a section: async/non-halting, standard park semantics, question in `decisionNeeded`, conductor composes the `protocol/advice.md` request, advice INLINED in the redispatch brief, cap 2/task (S-9/S-10/S-23a). Payload schema otherwise unchanged. |
| `skills/coordinate/kata-orchestrate/SKILL.md` | ADD the advisor spine wiring (S-9 — config-gated spine, not a module): load-guard (`validate_advisor_block`, fail-closed) · the §3.6 hooks (advise-first bump deferral + shared once-guard/standing-advice suppression; reroll-trigger #2 solicit-then-author ordering; fix-loop diagnose-first consult) · `advice-requested` escalation handling + verbatim ADVICE-section inlining (§3.7) · dispatch mechanics (gate → `advisor_status`; rung emission per §3.2; NO-FIRE board NOTE; spend via `kata_advisor`; DECISION lines; state writes via `kata_board.write_state`) · fail postures (§3.10) · EV-1 outcome recording + the after-action rollup folded into the run report + the ledger `advisor` key at closeout · grant-lapse on mid-run `/model`/mode switch. |
| `skills/coordinate/kata-bootstrap/SKILL.md` | ADD Phase-2 advanced advisor consent (pre-checked, veto-able; compose-consent precedent) + Phase-3 `advisor` block composition for advanced/standard, never essential (§3.4/§4). |
| `skills/coordinate/kata-preflight/SKILL.md` | ADD the standard-mode once-per-RUN advisor opt-in ask (own question, independent of the premium offer; accept/decline writes per §3.4; headless ⇒ OFF + note, never blocks). |
| `modules/initiation/kata-initiate/SKILL.md` | ADD the S-17b note to Phase 5: the session conductor MAY dispatch `kata-advise` directly during the grill, advanced+granted only, same budget; alive only when a grant already exists (S-26d). |
| `skills/plan/kata-design-doc/SKILL.md`, `skills/plan/kata-plan-essential/SKILL.md`, `skills/plan/kata-plan-standard/SKILL.md`, `skills/plan/kata-plan-advanced/SKILL.md` | ADD the S-17a advice-request instruction: a dispatched planner MAY raise an `advice-requested` escalation on a hard design question — **advanced+granted only** (runtime-gated; the tier variants all carry it because tier ≠ mode, D24c cross-picking). |
| `.planning/DECISIONS.md` | ADD the new D-record (next free number ≥ D167) compiling this initiative's decision set (pointer to the ledger + this DESIGN). |
| `README.md` | Skill index gains `kata-advise` (validator-regenerated mechanical columns + hand-authored Use prose — D28). |
| `CHANGELOG.md` | The initiative entry (new skill, new engine module, config field, escalation kind, hooks; version bumps). |

**Semver bumps (STANDARDS §3 — bump-on-modify, MINOR = new capability):** kata-orchestrate
0.13.0→0.14.0 · kata-bootstrap 0.6.0→0.7.0 · kata-preflight 0.3.0→0.4.0 · kata-initiate
0.7.0→0.8.0 · kata-design-doc 0.1.0→0.2.0 · kata-plan-essential/-standard/-advanced
0.1.4→0.2.0 · kata-advise NEW at 0.1.0.

**Not in scope / already done:** `CONTEXT.md` glossary (applied in the grill session —
S-22/S-26a/S-27). `.planning/HANDOFF-ADVISOR-EXECUTOR.md` (INTENT feature 7 / AC #8) is a
**conductor-maintained live run artifact** — created at run start and maintained through the
run by the conductor, not owned by any plan task.

## §6 Test surface

Determinism Doctrine (`docs/DETERMINISM-DOCTRINE.md`, STANDARDS §4a) applies to ALL engine
code: sorted-at-the-boundary output, no dict-order-driven serialization, `sort_keys` on
committed JSON, injectable clock for `meta.ts`, explicit tie-breaks. TDD mandate: tests are
written WITH the code (never after); mutation-style guards where cheap (flip a conjunct /
off-by-one the reservation boundary and assert the test fails).

| Test file | Classes of tests |
|---|---|
| `tools/tests/test_kata_models.py` (additions) | **Gate conjuncts:** `advisor_status` fires-matrix — every NO-FIRE reason in §3.2's table hit at least once, in precedence order; both mode arms (advanced; standard+granted; standard-not-granted; essential ⇒ `mode-excluded`; unknown mode fail-closed); BOTH rung arms (fable anchor ⇒ fires with `rung=None`; mythos anchor ⇒ `rung=None`; opus/sonnet/haiku anchors ⇒ `rung="fable"` — never `premium_rung_of` arithmetic, never mythos); full-id anchor normalization. **`advisor_rung_of`:** at-fable/above ⇒ None; every sub-fable Anthropic rung ⇒ `"fable"`; unknown anchor/family, empty ladders (openai/gemini/generic) ⇒ None; `family="auto"` derivation. **Malformed block:** each field's bad shape RAISES (bools-as-ints rejected, unknown keys, reserved > calls, non-int failThreshold). **Registry:** `ADVISOR_EVENTS` exact 5-member tuple + `ADVISOR_EVENT_SITES` covers exactly the registry; disjoint from `ADAPTIVE_EVENTS`; an advisor event in `models.premium.scope.events` still RAISES (S-20). **BC:** `ADAPTIVE_EVENTS` tuple + premium behavior byte-identical (existing tests untouched and green); `advisor_status(None, …) == {"fires": False, "reason": "absent", …}`. **Work-class:** `SKILL_WORK_CLASS["kata-advise"] == "critical"`; the existing R5 coverage test (`test_kata_models.py:514-535`) passes once the skill lands. |
| `tools/tests/test_kata_advisor.py` (new) | **State shape:** `new_advisor_state()` keys; malformed state RAISES in every consumer. **Budget:** `resolve_advisor_budget` fail-closes on an absent/malformed `budget` in a present block (the G-6 5/1 · 10/2 values are bootstrap-composition constants, not resolver fallbacks — §5) + fail-closed validation; **FCFS + reservation:** non-reserved denied at `remaining == reserved` (boundary, mutation-guarded), reserved spends to zero, per-mode reserved sets exactly per S-13; **exhaustion lapse** path (denied ⇒ caller-visible, spend not recorded on denial); **grant-before-dispatch:** `record_advisor_spend` commits before dispatch outcome is known (S-19a). **Outcomes:** enum exactly `{advised-pass, advised-fail-bumped, advised-fail-ceiling}`; unknown outcome RAISES; explicit-null pending allowed. **Recount:** `render_advisor_decision` → `recount_from_advisor_decisions` round-trip (used/byEvent recovered; determinism — same inputs ⇒ same bytes). **Byte-untouched guard:** no import-time or call-time mutation of `kata_adaptive` (and the build's diff shows zero change to `tools/kata_adaptive.py`). |
| `tools/tests/test_kata_telemetry.py` (additions) | Ledger `advisor` key: ABSENT ⇒ row byte-identical to a pre-feature row (BC); PRESENT ⇒ validated fail-closed (bad shape/negative counts/unknown outcome RAISE); presence-discriminated (never null-backfilled). |
| Config load-guard (in the two engine test files) | Present-but-malformed `advisor` block ⇒ `ValueError` (STOP posture, D136) — never a silent coercion to OFF; absent ⇒ clean no-op. |
| Validator / skill conformance | `uv run python validate_skills.py` green with the new skill (count 48→49, 0 errors): frontmatter schema, A1 no-`model:` guard, README-index sync. The R5 work-class coverage test is the structural guard that `kata-advise` cannot land without its `critical` entry. |

**Deliberately untestable-in-code (prose wiring):** the orchestrate/bootstrap/preflight hook
prose. Their acceptance is read-back conformance at the per-task gate + the freeze-gate/D98
red-team attacking wired-in-prose seams; the live n=1 proof is AC #1 (exercised in this run) —
honesty labels per §7.

## §7 Risks + named non-goals

**Risks (named, with mitigations):**

1. **Prose-wired hooks** — the §3.6 hooks live in kata-orchestrate prose, not engine code
   (S-9's spine-wiring choice). Risk: wired-in-prose, dead-in-a-real-run. Mitigation: **AC #1
   requires live exercise (n=1) this run; AC #2 is test-proven and live-if-it-occurs** (the
   threshold hook fires only if a real task fails twice — never forced), honesty-labeled
   wherever claimed; the D98 red-team attacks documentation-only seams.
2. **`tools/kata_telemetry.py` touch** — S-15b's ledger key requires one additive,
   presence-discriminated change to `build_ledger_row` (§3.9). Scope is minimal and
   BC-guarded (absent ⇒ byte-identical row); still, it widens the code footprint beyond the
   two pure-new engine surfaces. Flagged for the freeze-gate.
3. **Headless-advanced consent** — the ledger pins headless for the standard preflight ask
   (OFF + note) but not explicitly for the advanced bootstrap consent; §3.4 compiles
   pre-checked-consent-stands from G-9's cited compose-consent provenance. Freeze-gate should
   confirm or overturn this interpolation.
4. **advisor-reroll-grounding vs BLOCKER-2** — the struck `ladder-trigger-2-grounding`
   ADAPTIVE event must not be resurrected by analogy: the advisor event covers the NEW
   `kata-advise` dispatch only (§3.3); the grounding pass stays conductor-authored/untiered.
5. **Budget-reserve granularity** — S-13's "×1 + ×1" reserve coverage is realized with the
   copied `can_spend` SHAPE (either reserved event may draw the reserve); the per-event ×1 is
   coverage intent, not a per-event sub-pool (matches the AT-L13 precedent). Stated so the
   freeze-gate can attack it knowingly.

**Named non-goals (LOCKED exclusions — building any of these is drift):**

- **No kata-reason merge** (G-1 rejected): the deferred decider keeps its own future grill;
  it is re-titled "Reason (the decider)" and nothing more.
- **No gate consults, ever** (G-4): kata-evaluate / kata-inline-eval / closeout never consult.
- **No premium schema edits** (S-16): `models.premium`, `ADAPTIVE_EVENTS`,
  `kata_adaptive.py` byte-untouched; no `"standard"` value enters `models.premium.grantedMode`.
- **No both-at-once consult+bump default** (G-3 rejected — a possible future config posture,
  not this build).
- **No essential-mode advisor, no essential ask** (G-8).
- **No human-facing advice doc on the hot path; no verbatim sketch application** (G-7).
- **Live multi-anchor proof limited to the session anchor** (honesty labels, PD-2): this run's
  live n=1 exercises arm (a) on the fable-anchored dogfood configuration; arm (b) (sub-fable ⇒
  fable-rung dispatch) and the standard-mode carve-out are **test-proven, not live-proven** in
  this run. The labels travel with every claim (README/report/closeout).
