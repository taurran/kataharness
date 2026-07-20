# GRILL-LEDGER — advisor-executor (Fable-tier Advisor consult)

Run: 2026-07-19 · kind: version-up · target: self · grillDepth: standard · anchor: fable (session)
Grounding: fresh-context Fable-usage assessment (D59/D131/D148/D150 mechanics, file:line-cited) +
recall brief (0 open recurrences; top hits D148/D131/D59/D150/D143/D153/MM-1/MM-3/MM-7) + the
advisor-executor source pattern (structured-output advisor · executor-never-improvises · scoped
re-advise · 5–15% advisor token share).

## Phase 0 — decision tree (enumerated, dependency-ordered)

B1 advisor model resolution (anchor-relative rung) · B2 consult mechanism (skill shape) ·
B3 query/response contract · B4 who may request (worker vs conductor) · B5 evaluation-hook
composition with D150 (consult-vs-bump ordering; fix-loop valve) · B6 cross-phase availability
matrix (planning/execution/evaluation/closeout; Opus planning agent) · B7 mode defaults × D148
LOCKED composition (standard opt-in ⇒ premium amendment?) · B8 opt-in ask placement + once-per-
session semantics + headless · B9 budget/quota · B10 config schema home · B11 consult artifact +
telemetry · B12 fail postures · B13 BC · B14 naming vs kata-reason "Advisor" collision ·
B15 spine-wiring vs module.

## Self-resolved from code/docs (Phase 0.3) — surfaced here, operator may veto any

### S-1 — Consult mechanism: fresh-context, no-write, conductor-dispatched · LOCKED
**Decision:** The advisor consult is a NEW skill dispatched by the conductor as a fresh-context,
no-write subagent returning a structured payload. Workers NEVER dispatch it themselves — a worker
requests advice by raising an escalation (new kind, name pending B14), conductor-mediated like
every other dispatch. **Rationale:** only the conductor dispatches (spine L3/L8); mirrors the
built `kata-research` escalation-dispatch pattern exactly. **Provenance:** kata-orchestrate
escalation machinery (:1055-1077); assessment §5.

### S-2 — Advisory, never authoritative; never gates · LOCKED
**Decision:** Advice NEVER changes a gate verdict, is NEVER auto-applied, and NEVER expands the
frozen goal. It flows into the next redispatch brief / fix-loop instruction via the conductor;
the default-FAIL gate and LOCKED decisions are untouchable by it. **Rationale:** the C/B
invariant and the Reason posture (advisory pre-fill; gates/human dispose) — D99. **Provenance:**
CONTEXT.md §Second-brain (Reason); protocol/engram.md C4.

### S-3 — Durable consult artifact · LOCKED
**Decision:** Every consult writes `.kata/advice/<task-id>-<n>.json` (new `protocol/advice.md`
schema: question, scoped context refs, attempts-so-far, advisory response, model rung used,
disposition) + a board NOTE line at request and a DECISION line at disposition. Reports never
gate. **Rationale:** mirrors the escalation-payload contract (own artifact, board line = pointer).
**Provenance:** protocol/escalation.md pattern; CONTEXT.md §escalation payload.

### S-4 — BC: absent ⇒ OFF, byte-identical · LOCKED
**Decision:** No `advisor` config block ⇒ every leg OFF; behavior byte-identical to today.
**Provenance:** house BC rule (models.adaptive precedent, protocol/config.md:37).

### S-5 — Fail postures · LOCKED
**Decision:** (a) Consult dispatch failure ⇒ surfaced board NOTE + proceed UNADVISED — advice
never blocks the loop (advisory ≠ gate). (b) Malformed `advisor` config ⇒ ValueError → load-guard
STOP (D136 fail-closed). (c) No `model:` frontmatter on the new skill (validator A1). (d) Rung
resolution is anchor-RELATIVE via existing kata_models machinery — never a hard-coded id (D59/
D131). **Provenance:** assessment §6; D136; validator A1 guard.

### S-6 — Opt-in ask surface = preflight · LOCKED
**Decision:** The standard-mode opt-in ask lives in kata-preflight — the phase that sits exactly
"after design-doc freeze, before loop execution" (D29), where the D148 premium offer already
asks its question. Headless/non-TTY ⇒ default OFF + surfaced note, never blocks. (Once-per-
SESSION stickiness semantics remain OPEN — B8, operator question.) **Provenance:** D29 phase
topology; kata-preflight/SKILL.md:69-107.

## Operator-resolved branches
*(appended as each question resolves — one question at a time, D153/U1)*

### G-1 — Naming: the new feature owns "Advisor" · LOCKED
**Decision:** Skill `kata-advise`, config block `advisor`, canonical concept **advisor consult**.
The unbuilt kata-reason concept re-titles to plain "Reason (the decider)" — a cheap prose edit
since it is deferred. **Rejected:** "Counsel" naming (diverges from operator language); merging
into kata-reason v1 (its contract — recall-fusion + readiness exam — is bigger and explicitly
deferred to its own grill). **Rationale:** matches the operator's own vocabulary; keeps the
deferred decider unambiguous. **Provenance:** operator choice, Q1; CONTEXT.md §Second-brain.

### G-2 — D148 narrow amendment: standard opt-in unlocks advisor-events premium · LOCKED
**Decision:** Advisor consult events become premium-eligible on STANDARD mode IFF the operator
explicitly opted in that session — recorded approval (advisor-events-only scope, grantedMode:
standard), same budget + CA-L30 loud-lapse discipline. Advanced mode: advisor events ride the
existing default premium offer. The D148 amendment is NARROW: only advisor-class events, only
via the explicit once-per-session opt-in; the general premium offer stays advanced-only.
**Rejected:** anchor-only standard advisor (defeats the feature for Opus-anchored cost-conscious
sessions); advanced-only (contradicts the brief). **Rationale:** operator-directed re-scope of a
LOCKED decision — the sanctioned PD-1 path, recorded here + DECISIONS.md at freeze.
**Provenance:** operator choice, Q2; D148 (DECISIONS.md:2374-2398); kata-preflight branch (b).

### G-3 — Hook ordering: advise-first, bump-second · LOCKED
**Decision:** At the failure threshold (2 gate rejections, the existing `bump_pending` observable)
the loop fires a SCOPED advisor consult FIRST; the advice feeds the redispatch brief at the SAME
worker rung. If the advised attempt also fails (3rd rejection), the existing D150 +1 rung bump
fires — and the standing advice travels with the bumped redispatch. Advisor consult and rung bump
are ORDERED consequences of one counter, never simultaneous by default. **Rejected:** bump-first
(burns the bump before any diagnosis exists); both-at-once (double premium spend at every hard
spot — may become a future config posture, not the default). **Rationale:** matches the source
pattern's "re-advise" step; a stronger model without a diagnosis often repeats the mistake.
**Provenance:** operator choice, Q3; kata_adaptive.bump_pending (:299-326); AT-L14.

### G-4 — Cross-phase availability matrix · LOCKED
**Decision:** PLANNING/GRILL: YES — dispatched planners (incl. an Opus-anchored planner) may
request scoped consults on hard design questions, conductor-mediated. EXECUTION: YES (the core) —
workers raise an advice-request escalation; conductor dispatches; auto-fire at the G-3 failure
threshold and at inline-eval reroll trigger #2 (riding the existing conductor grounding pass).
THE GATE: NO — kata-evaluate/kata-inline-eval NEVER consult (judge independence, D33-class
extension of no-self-cert: builder and judge never share an advisor). POST-gate fix loop: MAY
consult (conductor-initiated at fix-loop thresholds, alongside the kata-diagnose valve).
CLOSEOUT: NO. **Rejected:** execution-only (starves the Opus planner); gate-may-consult (weakens
independence). **Provenance:** operator choice, Q4; brief items 6–7.

### G-5 — Opt-in semantics: once per RUN, at preflight · LOCKED
**Decision:** The standard-mode advisor opt-in is asked exactly ONCE per run, at kata-preflight
(post-freeze, pre-execution — S-6), recorded in kata.config (`advisor.approved` + grant scope)
for that run. No session-identity machinery. Headless/non-TTY ⇒ default OFF + surfaced note
(never blocks). A second run in the same conversation asks again — accepted trade-off.
**Rejected:** sticky-per-host-session (session-identity marker machinery + staleness edges);
sticky-until-mode-change (furthest from the operator's "per session" intent). **Provenance:**
operator choice, Q5; D29 phase topology.

### G-6 — Budget: own pool, mode-scaled · LOCKED
**Decision:** The advisor gets its OWN budget pool, `advisor.budget.calls`, separate from the
premium events pool (advisor can never starve the freeze-gate reserve, and vice versa).
Mode-scaled defaults: **standard = 5 calls / 1 reserved** (the reserve covers the fix-loop-
ceiling consult, the highest-value moment); **advanced = 10 calls / 2 reserved** (fix-loop
ceiling + one freeze-gate-class hard moment; mirrors the premium pool shape). Exhaustion ⇒ loud
lapse for the run's remainder, CA-L30 discipline; every consult a `tier:`-style board DECISION
line (AT-L7). **Rejected:** shared premium pool (consult-heavy runs eat hard-moment headroom);
unbounded. **Provenance:** operator (free text "option 1 for standard mode, scale out for
advanced" + confirm of 10/2), Q6a/Q6b; kata_adaptive budget mechanics (:105-108, 487-518).

### G-7 — Advice payload: machine-ingestible, agent-consumed, automated in-execution · LOCKED
**Decision:** The advisor response is a STRUCTURED, MACHINE-INGESTIBLE payload consumed by the
AGENT (conductor → redispatch brief / requesting planner), fully automated within execution —
never a human-facing artifact on the hot path. Shape: diagnosis · recommended approach · risks ·
citations · optional short illustrative code sketch marked non-authoritative (never applied
verbatim; the executor owns implementation). The human sees advisor activity as an AFTER-ACTION
ROLLUP in the run report/closeout (consults made, dispositions, budget used) — feedback, not a
gate. **Operator rider (verbatim intent):** "the ADVISOR RESPONSE goes to the AGENT. So it has
to be ingestible by the agent … roll it up in feedback after action for the result, to the user.
But primarily it should be automated within execution." **Rejected:** prose-only advice (cripples
three-specific-lines problems); full patch (blurred roles, drift surface). **Provenance:**
operator, Q7 + free-text rider; source-pattern failure modes.

### S-7 — Advisor model resolution: Fable-tier target, anchor-relative · LOCKED
**Decision:** The advisor targets the FABLE-CLASS rung, resolved anchor-relatively at dispatch:
anchor already fable/mythos-class ⇒ advisor runs AT the anchor (inherit-by-omission, no premium
machinery); anchor below fable ⇒ advisor = anchor+1 via the EXISTING premium machinery
(`premium_rung_of`), gated by G-2's grant. Never silently above fable (no auto-mythos). Skill
`kata-advise`: fresh-context, no-write, work-class `critical`, no `model:` frontmatter; dispatch
failure ⇒ one-step lapse to UNADVISED-proceed (S-5), never a ladder walk. **Provenance:** D59/
D131/D148 mechanics; assessment §2/§6.

### S-8 — Config home: new top-level `advisor` block · LOCKED
**Decision:** `kata.config.advisor = { "enabled": bool, "approved": bool, "grantedMode": str,
"budget": {"calls": N, "reserved": M}, "hooks": {"failThreshold": "adaptive.failBumpAt",
"rerollTrigger": 2, "fixLoopCeiling": true}, "phases": ["planning","execution","fix-loop"] }` —
behavior lives here; MODEL legality stays with the existing premium machinery (G-2 grant writes
the premium approval with advisor-events scope). Absent block ⇒ all OFF (S-4). Malformed ⇒
load-guard STOP (D136). Advisor events join the ADAPTIVE_EVENTS registry, each citing its real
covering dispatch site (MED-12): `advisor-fail-threshold` · `advisor-reroll-grounding` ·
`advisor-fix-loop-ceiling` · `advisor-worker-request` · `advisor-planning-consult`.
**Provenance:** protocol/config.md precedents (models.adaptive/premium); MED-12.

### S-9 — Spine wiring, not a module · LOCKED
**Decision:** The advisor is config-gated SPINE wiring in kata-orchestrate/kata-preflight (like
adaptive tiering), NOT a `kata/module/*` — its defaults are mode-driven and its hooks live inside
the orchestrator's existing dispatch/fix-loop steps; module packaging would buy nothing.
Escalation kind for worker requests: `advice-requested` (new kind in protocol/escalation.md,
non-halting/async — the frontier keeps draining while the consult runs). **Provenance:**
adaptive-tiering precedent (D150 spine); CONTEXT.md §async escalation.

## Convergence HOLD #1 resolutions (8 findings, fresh-context pass 2026-07-19)

### G-8 — Essential mode EXCLUDED (H5) · LOCKED
**Decision:** Advisor = standard + advanced ONLY. Essential gets no advisor, no ask — it stays
the lean budget mode. The INTENT draft's "standard/essential" wording is corrected at freeze;
recorded here as a deliberate supersession (the operator's original brief named standard only).
**Provenance:** operator choice, H5.

### G-9 — Two-moment grant model (H6+H7) · LOCKED
**Decision:** ADVANCED: the advisor consent question is asked at BOOTSTRAP composition (pre-
planning) — "on by default" operationally = pre-checked, one veto-able consent; planning-phase
consults are thereby legal in advanced. STANDARD: the ask stays at preflight (post-freeze) —
advisor covers execution + fix-loop only; standard planning has NO advisor (honest temporal
consequence of the operator's placement directive; G-4 matrix note amended). Bootstrap writes
the `advisor` block in BOTH modes by construction (`enabled` = wiring on; `approved` = spend
grant; standard: `enabled:true, approved:false` until the preflight ask). Absent block (pre-
feature / never-re-bootstrapped configs) ⇒ OFF strictly — NO implicit mode==advanced ON (S-4
holds; a builder must never infer the grant from the mode). **Provenance:** operator choice,
H6/H7; D29 topology; models.adaptive compose-consent precedent.

### S-10 — Worker request disposition + advice delivery (H1) · LOCKED
**Decision:** An `advice-requested` escalation follows the STANDARD escalation contract: the
requesting attempt ENDS (task parks, DAG-dependents park, frontier keeps draining). The conductor
dispatches `kata-advise`; on payload return the task redispatches with the advice payload
**INLINED verbatim in the redispatch brief** (workers in isolated worktrees cannot read the main
tree's `.kata/` — a path reference would be unreadable; the JSON is embedded under a marked
ADVICE section). `.kata/advice/<task-id>-<n>.json` remains the durable conductor-side record
(S-3). The advised redispatch is a NEW attempt on the attempt branch, counted normally in streak/
damper accounting. **Provenance:** protocol/escalation.md park semantics; worktree isolation.

### S-11 — Fail-threshold counter + bump deferral + double-fire guard (H2) · LOCKED
**Decision:** (a) The advisor fail-threshold rides the ENGINE counter when `models.adaptive` is
present (the `bump_pending` observable, standing rerolls counted exactly as the engine counts
them — G-3's "2 gate rejections" = shorthand for that counter). When `models.adaptive` is ABSENT,
the conductor maintains its own per-task rejection count with the same default threshold 2
(`advisor.hooks.failThreshold`, integer) — the advisor never requires the adaptive block. (b)
Advise-first is ORCHESTRATOR-SIDE bump deferral: on bump-pending with no prior consult for the
task, the conductor dispatches the consult and defers consuming the bump until the NEXT failure —
`kata_adaptive` engine semantics BYTE-UNTOUCHED. (c) Once-guard: at most ONE auto-consult per
task across the fail-threshold and reroll-trigger hooks (they share the guard; no double-fire);
the fix-loop-ceiling consult is a separate, reserve-backed event. **Provenance:** kata_adaptive
:299-326 consume semantics; config.md:37 absent⇒OFF.

### S-12 — Budget accounting: advisor pool is SOLE spend authority (H3) · LOCKED
**Decision:** Advisor dispatches NEVER draw from the premium events pool and never call the
premium `can_spend`. LEGALITY = the premium-machinery gate variant (approval + advisor-events
scope + exact-rung + mode-or-G-2-carve-out); SPEND = exclusively `advisor.budget` (own
`can_spend`-style check, FCFS + reservation, same shape). Schema amendments recorded: `models.
premium.grantedMode` gains legal value `"standard"` (advisor-carve-out grants only); advisor
events in `scope.events` are legality markers, not premium-pool draws. Leg-B's standard branch
("escalate to the anchor") is UNCHANGED for non-advisor events. **Provenance:** G-6 separate-pool
intent; kata_adaptive can_spend (:487-518) as the copied shape.

### S-13 — Advanced reserve mapping (H4) · LOCKED
**Decision:** Advanced reserve (2) = `advisor-fix-loop-ceiling` ×1 + `advisor-reroll-grounding`
×1 — the two late-run hard moments. G-6's "freeze-gate-class" phrasing was WRONG and is
superseded (G-4 locks the gate to no-consult; no advisor event is freeze-gate-class). Standard
reserve (1) = `advisor-fix-loop-ceiling`. **Provenance:** H4; G-4 matrix.

### S-14 — Fix-loop ordering: diagnose-first (H8) · LOCKED
**Decision:** At the fix-loop thrash valve, `kata-diagnose` dispatches FIRST (cheap
classification, existing contract untouched). Advisor consult fires ONLY on a `fix-problem`
verdict — advice feeds the resumed fixing. A `plan-problem` verdict escalates human-required as
today, WITHOUT a consult (the human decides; advice would pre-empt them). Never parallel.
**Provenance:** kata-orchestrate :1235-1253; C/B invariant (human disposes).

### S-15 — Residual LOW items pinned (H-LOW) · LOCKED
**Decision:** (a) ONE `protocol/advice.md` schema = the S-3 ∪ G-7 field union: request{taskId,
phase, question, scopedContext{planTaskIds[], gateExcerpt, filePaths[], attemptsSoFar}} +
response{diagnosis, approach, risks[], citations[], sketch?{lang, code, nonAuthoritative:true}} +
meta{event, rungUsed, disposition, ts}. "Scoped context refs" ≡ that scopedContext shape —
nothing else. (b) Telemetry: run-ledger gains an `advisor` key {consults, byEvent{}, budgetUsed/
cap, lapses[]} — the after-action rollup's data source; board lines per S-3. (c) Mid-run `/model`
switch or mode change ⇒ the advisor grant LAPSES (AT-L17b analog: re-ask required at the next
legal moment; spend already recorded is preserved). (d) S-7 clarified: the advisor rung for ANY
sub-fable anchor = the premium offer rung (fable) via `premium_rung_of`; sonnet-anchor sessions
therefore consult fable, not opus. (e) Advised redispatches count toward streak/damper accounting
as normal attempts (no special-casing). **Provenance:** HOLD residual list; AT-L17b.

## Convergence HOLD #2 resolutions (fresh-context re-gate 2026-07-19)

### S-16 — `advisor.approved` is the SOLE advisor legality record (H2-HOLD-1) · LOCKED
**Decision:** Advisor-event legality DECOUPLES from `models.premium` entirely. The `advisor`
block carries its own grant: `advisor.approved` (bool) + `advisor.grantedMode` — written by
BOOTSTRAP at composition in advanced (the veto-able consent), by PREFLIGHT on standard (the
opt-in ask). `models.premium` is BYTE-UNTOUCHED by this feature — no schema change, no shared
`approved` bool. A preflight premium decline does NOT touch the advisor grant (independent
spends); a bootstrap advisor veto does not touch the premium offer. Legality check = a SIBLING
gate function in `kata_models` (conjuncts: `advisor.approved` ∧ event ∈ the 5 advisor events ∧
rung == `premium_rung_of(anchor)` ∧ (`mode=="advanced"` ∨ (`mode=="standard"` ∧
`grantedMode=="standard"`)) — fail-closed, NO-FIRE reasons enumerated + surfaced like premium's).
Sub-fable non-opus anchors (e.g. sonnet) get advisor legality through THIS gate — the
opus-only condition governs the general premium OFFER, not the advisor. **Supersedes:** S-12's
"models.premium.grantedMode gains 'standard'" (no premium schema edit at all) and S-8's "MODEL
legality stays with the existing premium machinery" (it reuses `premium_rung_of` + the gate
PATTERN, not the premium record). The D148 amendment (G-2) is thereby realized as a sibling
gate, not an edit to the premium contract. **Provenance:** re-gate HOLD-1; config.md:36.

### S-17 — Planning-consult dispatcher named (H2-HOLD-2) · LOCKED
**Decision:** `advisor-planning-consult`'s covering dispatch sites: (a) IN-HARNESS plan/design
authoring — dispatched planner-workers raise `advice-requested` escalations through the SAME
kata-orchestrate escalation machinery as execution workers (orchestrate is running during the
freeze stage; the kata-plan/kata-design-doc dispatch briefs gain the advice-request instruction,
advanced+granted only); (b) CONDUCTOR-INLINE grill (kata-initiate Phase 5) — the session
conductor itself dispatches `kata-advise` directly at its own discretion (it is the main session;
dispatch capability exists), advanced+granted only, drawing the same budget. No third path.
**Provenance:** re-gate HOLD-2; MED-12 real-site rule.

### S-18 — Standalone counter mirrors engine semantics (H2-borderline) · LOCKED
**Decision:** `models.adaptive` PRESENT ⇒ the engine counter + `failBumpAt` are authoritative;
`advisor.hooks.failThreshold` is IGNORED with a surfaced load NOTE if set to a conflicting value.
ABSENT ⇒ the conductor-maintained per-task count mirrors engine semantics EXACTLY (gate
rejections + standing rerolls both count), threshold = `advisor.hooks.failThreshold` (INTEGER,
default 2 — S-8's string-pointer rendering superseded). One semantics, two sources, never dual
counters on one run. **Provenance:** re-gate borderline; kata-orchestrate :1009-1013.

### S-19 — Final LOW pins (H2-LOW) · LOCKED
**Decision:** (a) A granted-then-FAILED consult dispatch CONSUMES its budget call (grant-before-
dispatch, matches kata_adaptive precedent; prevents retry-mining; the failure is still a loud
lapse per S-5). (b) Standard-mode mid-run mode/model switch AFTER preflight ⇒ the run is
unadvised to completion with a loud NOTE — no legal re-ask moment remains; never a silent state.
(c) Reroll-trigger-#2 ordering: advice is solicited BEFORE the tightened redispatch brief is
authored and folded INTO it — one deterministic order. (d) The frozen INTENT's
"standard/essential" + "once-per-session" wording is restated corrected in the DESIGN (G-5/G-8
supersessions, deliberate + recorded). **Provenance:** re-gate LOW list.

## Convergence HOLD #3 resolutions (fresh-context pass 3, 2026-07-19)

### S-20 — SIBLING event registry; ADAPTIVE_EVENTS byte-untouched (H3-1) · LOCKED
**Decision:** The five advisor events live in their OWN registry — `ADVISOR_EVENTS` +
`ADVISOR_EVENT_SITES` in `kata_models.py`, sibling to (and shaped like) `ADAPTIVE_EVENTS`, each
event citing its real covering dispatch site (MED-12 discipline). `ADAPTIVE_EVENTS` and the
`models.premium.scope.events` vocabulary are BYTE-UNTOUCHED; an advisor event name appearing in
`models.premium.scope.events` remains ILLEGAL (fail-closed classify, as today). **Supersedes**
S-8's "advisor events join the ADAPTIVE_EVENTS registry" sentence. **Provenance:** pass-3 H3-1;
S-16 decoupling.

### S-21 — Sibling-gate arms: at-fable bypasses the rung conjunct (H3-2) · LOCKED
**Decision:** The advisor legality gate has TWO rung arms: (a) anchor already fable/mythos-class
⇒ rung arm SATISFIED by inherit-at-anchor (OMIT — no premium helper consulted; S-7's no-premium-
machinery path); (b) sub-fable anchor ⇒ rung must equal `premium_rung_of(anchor)`. Common
conjuncts in both arms: `advisor.approved` ∧ event ∈ ADVISOR_EVENTS ∧ mode-arm (advanced, or
standard+grantedMode=="standard"). A NO-FIRE on ANY conjunct ⇒ **unadvised-proceed with a
surfaced reason** — NEVER a consult-at-anchor-without-consent, never a block. On the fable-
anchored dogfood configuration the feature is therefore ALIVE via arm (a). **Provenance:** pass-3
H3-2; S-7/S-16 composition.

### S-22 — Glossary refreshed to the S-16 grant model (H3-3) · LOCKED
**Decision:** CONTEXT.md "Advisor grant" entry rewritten: `advisor.approved` is the SOLE
legality record (no premium scope involvement); advanced consent at BOOTSTRAP composition
(veto-able), standard at preflight. Applied in the same session as this entry. **Provenance:**
pass-3 H3-3.

### S-23 — Pass-3 LOW pins · LOCKED
**Decision:** (a) Worker-requested consults: capped at 2 per task (surfaced NOTE beyond;
budget still the outer bound) — one pathological task can never drain the pool. (b) Advisor
spend state lives in `.kata/state.json` (an `advisor` field: {used, byEvent, lapses[]}),
single-writer orchestrator via kata_board.write_state; restore recounts from board DECISION
lines (fix-loop-counter precedent). (c) Evaluator instruction pinned: AC #3 is graded per the
G-5/G-8 recorded supersessions (once-per-RUN, essential excluded) — a literal reading of the
frozen INTENT wording is NOT a failure. (d) Bootstrap writes `advisor.grantedMode: "advanced"`
in advanced (cosmetic — the advanced arm ignores it; recorded for config completeness).
**Provenance:** pass-3 LOW list.

## Convergence HOLD #4 resolutions (fresh-context pass 4, 2026-07-19)

### S-24 — Advisor rung = FABLE-TARGET, not one-rung-above (FORK-1) · LOCKED
**Decision:** The advisor targets the FABLE rung for ANY sub-fable anchor — sonnet- and haiku-
anchored runs consult FABLE, not their +1 rung. `premium_rung_of` is the WRONG helper for this
and is NOT used by the advisor gate; a new pure helper `advisor_rung_of(family, anchor)` returns:
anchor already fable/mythos-class ⇒ None (inherit-at-anchor, arm (a)); any sub-fable anchor ⇒
the family ladder's `fable` rung id. Never mythos by default. S-21's rung conjunct (b) is
REWRITTEN to `rung == advisor_rung_of(anchor)`; S-15d's intent (fable, stated with the wrong
helper name) is thereby made true. The multi-rung cost jump on low anchors is DELIBERATE — the
feature IS a Fable-tier advisor (frozen goal); the budget pool bounds the spend. Non-Anthropic
families: empty ladders ⇒ `advisor_rung_of` returns None ⇒ arm (a) inherit — advisor runs at the
anchor, honest NOTE (no fable-class rung exists there). **Supersedes:** S-21(b)'s
`premium_rung_of` conjunct; S-15d's helper naming. **Provenance:** pass-4 FORK-1; frozen INTENT
goal ("Fable-tier"); kata_models.py:64,:462-485.

### S-25 — Any prior consult satisfies the advised condition (FORK-2) · LOCKED
**Decision:** S-11b's bump deferral fires ONLY for an UNADVISED task: a prior consult of ANY
kind (auto or worker-requested) counts as standing advice — the auto-consult is skipped and the
bump consumes normally at threshold (the standing advice travels with the bumped redispatch, per
G-3). Rationale: the advice already exists; a second consult before the bump would double-spend
on the same diagnosis. **Provenance:** pass-4 FORK-2; G-3 advice-travels rule.

### S-26 — Pass-4 LOW pins · LOCKED
**Decision:** (a) Glossary "Advisor consult" first sentence reworded to the fable-target rule
(applied same session). (b) Standard preflight DECLINE writes `approved:false` and leaves
`grantedMode` absent — `approved` is authoritative; no grantedMode value is ever required for
the declined state. (c) Advanced mid-run mode/model switch ⇒ same terminal posture as standard:
grant lapses, no legal re-ask moment remains in-run, unadvised to completion with a loud NOTE
(next run re-consents at bootstrap). (d) S-17b conductor-inline grill consults are ALIVE only
when a grant already exists at grill time (re-entrant configs / loop-back runs); on first-run
flows the gate fail-closes — recorded as the DELIBERATE temporal consequence of G-9 (same class
as standard planning). (e) `advisor.enabled` gates hook WIRING; `advisor.approved` gates SPEND —
both required to consult; `enabled:false, approved:true` (hand-edited) converges on no-consult
with a surfaced NO-FIRE reason. **Provenance:** pass-4 LOW list.

### S-27 — Standing advice suppresses ALL auto-consults (pass-5 pin) · LOCKED
**Decision:** Any standing advice for a task (auto OR worker-requested) suppresses BOTH auto
hooks (fail-threshold AND reroll-trigger) — S-25 generalized: one diagnosis per task; the
standing advice rides every subsequent redispatch. The fix-loop-ceiling consult remains separate
(different phase, reserve-backed). Glossary "Advisor grant" rung clause fixed to
`advisor_rung_of` (S-24) same session. **Provenance:** pass-5 SHIP residuals 1–2.

### EV-1 — Elevate: advice-effectiveness telemetry pairing · LOCKED
**Decision:** ACCEPTED — each consult's telemetry row gains an OUTCOME pairing (advised→pass /
advised→fail→bumped / advised→fail→ceiling), pure derived data written by the S-23(b)
single-writer state path; surfaced in the after-action rollup. Makes advisor ROI an evidence
question for the E1/E2 calibration queue; future failThreshold tuning becomes evidence-driven.
**Rationale:** operator acceptance; grounded in G-6 (budget) + S-23(b) (spend state) + the D150
evidence-driven ethos this grill composed with throughout. Compiled into the frozen DESIGN.
**Provenance:** ELEVATE step (D153), this grill close.

## CONVERGENCE: SHIP (pass 5, fresh-context, 2026-07-19)
Five passes: HOLD(8) → HOLD(3) → HOLD(3) → HOLD(2) → **SHIP**. All findings folded above.
DESIGN of record prints the FINAL `advisor` schema (S-8 superseded three ways) + the corrected
INTENT wording restatement + the S-23(c) evaluator instruction.
