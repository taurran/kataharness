---
title: "Advisor consult (kata-advise) — PLAN"
status: COMPILED 2026-07-19 — compiled from GRILL-LEDGER.md + DESIGN.md; awaiting freeze-gate
spec: advisor-executor
design: .planning/specs/advisor-executor/DESIGN.md
ownership:
  T1: [tools/kata_models.py, tools/tests/test_kata_models.py]
  T2: [tools/kata_advisor.py, tools/tests/test_kata_advisor.py, tools/kata_telemetry.py, tools/tests/test_kata_telemetry.py]
  T3: [protocol/advice.md, protocol/config.md, protocol/escalation.md]
  T4: [skills/plan/kata-advise/SKILL.md]
  T5: [skills/coordinate/kata-orchestrate/SKILL.md, skills/coordinate/kata-bootstrap/SKILL.md, skills/coordinate/kata-preflight/SKILL.md, modules/initiation/kata-initiate/SKILL.md, skills/plan/kata-design-doc/SKILL.md, skills/plan/kata-plan-essential/SKILL.md, skills/plan/kata-plan-standard/SKILL.md, skills/plan/kata-plan-advanced/SKILL.md]
  T6: [.planning/DECISIONS.md, README.md, CHANGELOG.md]
waves:
  - [T1, T2, T3]
  - [T4, T5, T6]
depends_on:
  T1: []
  T2: []
  T3: []
  T4: [T1, T3]
  T5: [T1, T2, T3, T4]
  T6: [T4, T5]
tags:
  - kata/plan
  - advisor
  - fable-target
---

# Advisor consult — implementation PLAN

**Goal.** Wire the DESIGN's LOCKED contract end-to-end (PD-1 — no stub, no unwired leg): the
`kata-advise` skill + `ADVISOR_EVENTS` registry + `advisor_rung_of` + the sibling legality gate
(`kata_models`), the pure spend/state/outcome engine (`kata_advisor`), the `protocol/advice.md`
schema + `advisor` config block + `advice-requested` escalation kind, and the orchestrator/
bootstrap/preflight/initiate/planner prose wiring — with `models.premium`, `ADAPTIVE_EVENTS`,
and `tools/kata_adaptive.py` **byte-untouched** (S-4/S-16/S-20) and absent-block behavior
byte-identical (S-4).

## Global constraints (every task)

- **Source of truth:** `GRILL-LEDGER.md` (28 LOCKED entries) as compiled by `DESIGN.md`.
  Workers MUST NOT re-decide, weaken, or extend a LOCKED decision; a discovered conflict is an
  escalation (`protocol/escalation.md`), never a silent re-decide.
- **DISJOINT file ownership is absolute:** a worker NEVER touches a file outside its `ownership:`
  list — not "just a line", not a test tweak, not a doc cross-reference. A needed change in
  another task's file ⇒ escalate.
- **Workers NEVER run git.** The conductor is the SOLE main-tree git writer (D1 policy,
  2026-07-12); workers build in isolated worktrees and report; the conductor stages/commits.
- **TDD mandate (engine tasks T1/T2):** tests are written WITH the code, never after;
  mutation-style guards where cheap (flip a gate conjunct / off-by-one the reservation boundary
  and confirm the test catches it). Determinism Doctrine (`docs/DETERMINISM-DOCTRINE.md`) binds
  all engine code: sorted-at-the-boundary output, `sort_keys` on committed JSON, injectable
  clock, no dict-order-driven bytes.
- **Per-task gate (every task, default-FAIL):** the task ends ONLY with (a) its OWN tests green
  (`uv run pytest -q <its test files>` for code tasks; full-suite regression at integration) and
  (b) `ruff` clean on its owned files. Prose-only tasks (T3/T5/T6) substitute
  `uv run python validate_skills.py` green + a read-back conformance check against the DESIGN
  section cited in their acceptance.
- **Semver bump-on-modify** (STANDARDS §3): every modified SKILL.md bumps per DESIGN §5's table;
  new skills enter at 0.1.0.
- **Additive only:** no existing frozen line is rewritten; supersede-never-rewrite. BC
  acceptance in T1/T2 includes "existing tests pass unchanged".

---

## Wave 1 (parallel — disjoint files, no cross-dependencies)

### T1 — `kata_models.py` additions (registry · rung helper · sibling gate · work-class entry)
**ownership:** `tools/kata_models.py`, `tools/tests/test_kata_models.py`
**depends_on:** []
**action:** Implement DESIGN §3.2 + §3.3 verbatim, additive-only:
1. `ADVISOR_EVENTS` (exact 5-member tuple) + `ADVISOR_EVENT_SITES` (each event citing its real
   covering dispatch site — the §3.3 table text), sibling to `ADAPTIVE_EVENTS`, which stays
   byte-untouched.
2. `advisor_rung_of(family, anchor) -> str | None` (S-24): full-id normalization; `"auto"`
   family derivation; `None` for at-fable/mythos anchors, unknown/empty ladders, no-`fable`-rung
   ladders, unknown anchors; the ladder's `"fable"` rung for ANY sub-fable anchor; never mythos.
3. `_validate_advisor` / exported `validate_advisor_block` (fail-closed, D136 — the FULL
   DESIGN §3.2/§4 key set: `enabled`/`approved` strict bools; `grantedMode` ∈
   {"advanced","standard"} when present; `budget` REQUIRED in a present block (strict ints,
   `0 ≤ reserved ≤ calls`); `hooks` with `failThreshold` int ≥ 1, `rerollTrigger` int,
   `fixLoopCeiling` bool; `phases` list[str] ⊆ {planning, execution, fix-loop}; unknown keys
   RAISE at every level).
4. `advisor_status(advisor, anchor, *, family, mode, event) -> {fires, reason, rung}` — the
   sibling gate with the §3.2 NO-FIRE reason table in its exact precedence order; rung computed
   internally via `advisor_rung_of` (the S-24 conjunct satisfied by construction).
5. `SKILL_WORK_CLASS["kata-advise"] = "critical"` (S-7) — pre-staged here (this task owns the
   file; the R5 coverage test only requires discovered ⊆ map, so the entry is safe before T4
   lands, and T4's gate proves it live).
**tests (same task, TDD):** the DESIGN §6 `test_kata_models.py` row in full — every NO-FIRE
reason, both rung arms, both mode arms, malformed-raise per field, registry membership +
disjointness + S-20 premium-scope illegality, absent-block reason `"absent"`, work-class entry
assertion. **REQUIRED (FIX 1): BOTH canonical bootstrap compositions — the DESIGN §3.4
advanced default AND standard default blocks, verbatim — round-trip `_validate_advisor`
clean** (guards against a composed default bricking every run at the load-guard). Mutation
guards: negate one conjunct at a time in a scratch copy and confirm a test fails.
**acceptance:**
- All new tests green; ALL pre-existing `test_kata_models.py` tests green UNCHANGED.
- `git diff` (conductor-verified) shows `ADAPTIVE_EVENTS`/`ADAPTIVE_EVENT_SITES`/premium
  functions/ladders/`ID_MAP` byte-untouched; additions only.
- `advisor_status(None, …)` ⇒ `{"fires": False, "reason": "absent", "rung": None}` (S-4).
- ruff clean on both owned files.

### T2 — NEW `kata_advisor.py` engine + telemetry additive key
**ownership:** `tools/kata_advisor.py`, `tools/tests/test_kata_advisor.py`,
`tools/kata_telemetry.py`, `tools/tests/test_kata_telemetry.py`
**depends_on:** []
**action:** Implement DESIGN §3.5 + §3.9 verbatim:
1. `tools/kata_advisor.py` (pure, stdlib-only, Determinism Doctrine): `new_advisor_state()`
   (`{used, byEvent, lapses, outcomes}`); `resolve_advisor_budget` (validates calls/reserved;
   the G-6 defaults 5/1 · 10/2 are BOOTSTRAP-COMPOSITION constants, NOT resolver fallbacks —
   FAIL-CLOSES on an absent or malformed `budget` in a present block, DESIGN §5);
   `ADVISOR_RESERVED_EVENTS` per-mode sets (S-13); `can_spend_advisor` (FCFS +
   floor reservation — the `kata_adaptive.can_spend` shape: reserved event ⇒ `remaining ≥ 1`,
   non-reserved ⇒ `remaining > reserved`); `record_advisor_spend` (dispatch-commit,
   grant-before-dispatch S-19a); `ADVISOR_OUTCOMES = ("advised-pass", "advised-fail-bumped",
   "advised-fail-ceiling")` + `record_outcome` (unknown ⇒ raise; explicit `None` pending
   allowed); `render_advisor_decision` + `recount_from_advisor_decisions` (board DECISION
   recount trail, S-23b); `ledger_fragment(state, cap)` (the §3.9 `advisor` ledger value).
   **DO NOT import-for-mutation, edit, or shadow `tools/kata_adaptive.py` — byte-untouched.**
2. `tools/kata_telemetry.py`: ONE additive, presence-discriminated `advisor` key in
   `build_ledger_row` + its fail-closed validator (the `verdictByTier` precedent at
   `:1259-1301`): absent ⇒ key omitted, row byte-identical; present ⇒ validated (shape,
   non-negative ints, outcome enum, `null`-pending allowed) else raise.
**tests (same task, TDD):** the DESIGN §6 `test_kata_advisor.py` + `test_kata_telemetry.py`
rows in full, incl. the reservation-boundary mutation guard and the BC byte-identical-row test.
**acceptance:**
- All new tests green; ALL pre-existing `test_kata_telemetry.py` tests green UNCHANGED.
- `git diff` shows ZERO change to `tools/kata_adaptive.py`.
- A pre-feature run summary (no `advisor` key) produces a byte-identical ledger row to today's.
- ruff clean on all four owned files.

### T3 — Protocol docs (`advice.md` NEW · `config.md` · `escalation.md`)
**ownership:** `protocol/advice.md`, `protocol/config.md`, `protocol/escalation.md`
**depends_on:** []
**action:**
1. `protocol/advice.md` (NEW): the DESIGN §3.8 schema of record — the JSON payload (request /
   response / meta, exact field names), `.kata/advice/<task-id>-<n>.json` location + 1-based
   per-task ordinal, board-line contract (NOTE at request, DECISION at disposition), the
   non-authoritative-sketch rule, advisory-never-gates (S-2), producer/consumer table.
2. `protocol/config.md`: add the `advisor` row to the schema table — the DESIGN §4 block +
   field table verbatim (incl. `phases` = documentation of the G-9 matrix, not a switch;
   absent ⇒ OFF byte-identical; malformed ⇒ load-guard STOP; grantedMode absent-on-decline).
3. `protocol/escalation.md`: extend the `kind` enum with `"advice-requested"` + a routing
   section per DESIGN §3.7 (async/non-halting, standard park semantics, question carried in
   `decisionNeeded`, conductor composes the advice request and inlines the response verbatim in
   the redispatch brief, 2-per-task cap S-23a). Payload schema and every existing kind's
   contract otherwise UNCHANGED (additive; supersede-not-rewrite).
**acceptance:**
- `advice.md` schema field-for-field identical to DESIGN §3.8 (a reader diffing them finds no
  divergence).
- `config.md` `advisor` row states: sole-legality `approved` (S-16), budget defaults 5/1 · 10/2,
  integer `failThreshold` + adaptive-present-ignores rule (S-18), absent ⇒ byte-identical BC.
- `escalation.md`: `advice-requested` added; existing kinds/payload/park contract untouched.
- `uv run python validate_skills.py` green (protocol files aren't skills; confirms no breakage).

---

## Wave 2 (after wave 1; intra-wave `depends_on` ordering holds)

### T4 — the `kata-advise` skill
**ownership:** `skills/plan/kata-advise/SKILL.md`
**depends_on:** [T1, T3]
**action:** Author the skill per DESIGN §5: category `plan`; frontmatter per STANDARDS §1
(`name: kata-advise`, `version: 0.1.0`, `status: experimental`, `agnostic: true`,
`cost-weight` per `.planning/SKILL-COST-RATINGS.md` conventions, **NO `model:` key** — A1,
`allowed-tools` read-only, omitting Write/Edit); tags `kata/plan` + `kata/spine` + `advisor`.
Body: consume ONE `protocol/advice.md` request (inlined by the conductor); ground only in the
supplied `scopedContext`; return the structured `response` object; advisory-never-authoritative
(S-2 — never a gate verdict, never goal expansion, sketch non-authoritative); fresh-context,
no-write, conductor-dispatched-only framing (S-1); one narrow question per consult.
**acceptance:**
- `uv run python validate_skills.py` ⇒ **49 skills validated / 0 errors** (frontmatter schema,
  A1 no-`model:` guard).
- The R5 work-class coverage test (`test_kata_models.py:514-535`) green — `kata-advise`
  resolves to `critical` via T1's pre-staged entry (run, not edited, by this task).
- Read-back: the skill claims no dispatch authority, no write capability, no gate power.

### T5 — prose wave (orchestrate · bootstrap · preflight · initiate · planner briefs)
**ownership:** `skills/coordinate/kata-orchestrate/SKILL.md`,
`skills/coordinate/kata-bootstrap/SKILL.md`, `skills/coordinate/kata-preflight/SKILL.md`,
`modules/initiation/kata-initiate/SKILL.md`, `skills/plan/kata-design-doc/SKILL.md`,
`skills/plan/kata-plan-essential/SKILL.md`, `skills/plan/kata-plan-standard/SKILL.md`,
`skills/plan/kata-plan-advanced/SKILL.md`
**depends_on:** [T1, T2, T3, T4]
**action (per file, additive; every file per DESIGN §5's row for it):**
1. **kata-orchestrate** (0.13.0→0.14.0): the full advisor spine wiring — load-guard via
   `validate_advisor_block` (malformed ⇒ STOP); the three hooks with their exact orderings
   (§3.6a advise-first bump deferral + shared once-guard + S-27 standing-advice suppression;
   §3.6b trigger-#2 solicit-BEFORE-authoring; §3.6c diagnose-first, fix-problem-only consult).
   **Anchoring (FIX 4, mandatory):** the §3.6a advise-first text is placed ADJACENT to the
   existing Leg C bump paragraph (SKILL.md:1013-1015, "When `bump_pending(state, cfg, task_id)`
   is True, the task's NEXT attempt dispatches one rung up…") and that sentence is AMENDED with
   the explicit cross-reference *"unless the advisor fail-threshold hook fires first — the bump
   defers one failure (§advisor)"* — the skill body must never carry two contradictory standing
   instructions about the same counter;
   `advice-requested` handling + verbatim ADVICE-section inlining (§3.7); dispatch mechanics
   (`advisor_status` → rung emission `None`⇒OMIT / short-name⇒`ID_MAP` id; NO-FIRE ⇒ board NOTE
   + unadvised-proceed; spend via `kata_advisor.can_spend_advisor`/`record_advisor_spend`;
   `render_advisor_decision` DECISION lines; state via `kata_board.write_state`); fail postures
   (§3.10 — dispatch failure ⇒ one-step unadvised lapse, never a ladder walk); EV-1 outcome
   recording with the §3.9 derivation rule; the after-action rollup in the run report + the
   ledger `advisor` key at closeout; grant lapse on mid-run `/model`/mode switch (loud NOTE,
   terminal in-run). The gate and closeout NEVER consult (G-4) — stated where the hooks are.
2. **kata-bootstrap** (0.6.0→0.7.0): advanced pre-checked veto-able consent at composition +
   Phase-3 `advisor` block writes (advanced `{enabled:true, approved:<consent>,
   grantedMode:"advanced", budget:{calls:10,reserved:2}, hooks, phases:[planning,execution,
   fix-loop]}`; standard `{enabled:true, approved:false, budget:{calls:5,reserved:1}, hooks,
   phases:[execution,fix-loop]}`; essential ⇒ NO block); headless composition per DESIGN §3.4
   (compose-consent stands, surfaced); never inferred from mode on load (G-9).
3. **kata-preflight** (0.3.0→0.4.0): the standard once-per-RUN opt-in ask (own question,
   independent of the premium gate; accept ⇒ `approved:true, grantedMode:"standard"`; decline ⇒
   `approved:false`, `grantedMode` ABSENT; headless ⇒ OFF + surfaced note, never blocks).
4. **kata-initiate** (0.7.0→0.8.0): the S-17b Phase-5 note (conductor-inline `kata-advise`
   dispatch, advanced+granted only, same budget; alive only on a pre-existing grant — S-26d).
5. **kata-design-doc + the three kata-plan tiers** (→0.2.0 each): the S-17a advice-request
   instruction — a dispatched planner MAY raise `advice-requested` on a hard design question,
   advanced+granted only (runtime-gated; present in all tiers because tier ≠ mode).
**acceptance:**
- Each addition is traceable to its DESIGN § (read-back check); NO existing line rewritten; the
  D148 premium gate text, adaptive-tiering section, and every existing hook contract untouched.
- All 8 files carry their DESIGN §5 semver bump.
- `uv run python validate_skills.py` green (49/0).
- The hook prose quotes the LOCKED orderings (G-3 advise-first/bump-second; S-19c
  solicit-then-author; S-14 diagnose-first) verbatim-level — two independent conductors reading
  it cannot diverge on order.
- **FIX-4 criterion:** the Leg C `bump_pending` sentence (formerly SKILL.md:1013-1015) carries
  the "unless the advisor fail-threshold hook fires first — the bump defers one failure
  (§advisor)" cross-reference, and the §3.6a advise-first text sits adjacent to it — a read-back
  finds NO unqualified "bump at threshold" instruction anywhere in the skill body.

### T6 — records (D-record · README index · CHANGELOG)
**ownership:** `.planning/DECISIONS.md`, `README.md`, `CHANGELOG.md`
**depends_on:** [T4, T5]
**action:**
1. `.planning/DECISIONS.md`: append the initiative's D-record at the next free number
   (≥ D167 — verify the tail at write time): the advisor-consult contract in the house register
   (sibling gate + fable-target rung + two-moment grant + own budget pool + advise-first
   ordering + BC guarantees), citing GRILL-LEDGER entry IDs and this spec's DESIGN/PLAN paths.
2. `README.md`: skill index gains `kata-advise` (mechanical columns validator-regenerated via
   `validate_skills.py --write`; hand-author the "Use" prose column). Honesty labels on any
   usage claim (live n=1 / test-proven legs, DESIGN §7).
3. `CHANGELOG.md`: the initiative entry — new skill, new `tools/kata_advisor.py`, `advisor`
   config block, `advice-requested` kind, `protocol/advice.md`, hooks, telemetry key, and the
   full semver-bump list.
**acceptance:**
- D-record number verified unused; entry cites ledger IDs (not re-stated decisions that could
  drift).
- `validate_skills.py` README-sync check green after the index write.
- CHANGELOG lists every touched skill with old→new versions matching DESIGN §5.

---

## Integration & gate (conductor — sole git writer)

0. **AC #8 standing duty (conductor-owned, outside the task DAG):** the transfer handoff doc
   `.planning/HANDOFF-ADVISOR-EXECUTOR.md` exists from run start (verified present on disk
   2026-07-19) and the conductor maintains it LIVE through the run — it is not any worker's
   owned file.
1. Merge order: wave 1 (octopus — disjoint), then T4, T5, T6 per `depends_on`; `cd tools && uv
   sync`.
2. Full gate on the integration branch: `uv run pytest -q` all-pass (existing suite + new
   tests) · `uv run python validate_skills.py` **49/0** · ruff clean · Snyk med+ 0 (AC #7).
   Emit `.kata/RESULT.json` + footprint + mutation records via `gate_emit` (code-bearing run).
3. **Byte-untouched verification (AC #6):** `git diff` on `tools/kata_adaptive.py` (empty) and
   on the `ADAPTIVE_EVENTS`/premium regions of `kata_models.py` (additions only); a config
   without an `advisor` block drives zero behavior change (the T1/T2 BC tests are the proof).
4. **AC #8 pre-gate check, then the gate:** BEFORE dispatching the evaluator, the conductor
   verifies `.planning/HANDOFF-ADVISOR-EXECUTOR.md` (a) exists, (b) is detailed enough to
   reproduce the approach in another loop project, and (c) carries no work-linkage on public
   surfaces. Then dispatch fresh-context **kata-evaluate** (no-write, default-FAIL) against the
   frozen INTENT ACs — grading AC #3 per the S-23(c) evaluator instruction (DESIGN §1).
5. Standing adversarial **kata-review** (D98 — contract-bearing build): attack the sibling-gate
   conjuncts, the once-guard/suppression semantics, the deferral's engine-byte-untouched claim,
   the headless-advanced interpolation (DESIGN §7 risk 3), and the prose-wired hook seams.
6. **Live n=1 (AC #1) — grant mechanism named:** this run's config predates the feature and
   both legal grant moments (bootstrap composition / preflight) are already past, so the live
   exercise uses an **OPERATOR-PRESENT, EXPLICITLY-CONSENTED in-session grant**, recorded as a
   deliberate operator DECISION board line before any consult fires (operator authority — the
   PD-1 sanctioned re-scope path; NOT a new grant moment added to the §3.4 model). AC #1 is
   then exercised live on the session anchor — arm (a). **AC #2 is test-proven and
   live-if-it-occurs** (the fail-threshold hook fires only if a real task fails twice — never
   forced); honesty labels travel with every claim (DESIGN §7).
