---
spec: context-autonomy
phase: CA-P2
title: policy + prose + docs — bootstrap bundle step, readiness WARN, report budgets + continuation contract, observability + platform docs, contract primitive (c), glossary, riders, D-records, CHANGELOG — and the live-proof battery
status: frozen-candidate (pending plan gate)
created: 2026-07-04
branch: feat/context-autonomy
baseline: CA-P0 + CA-P1 integrated (suite grown-green, validator green with P1 bumps, Snyk medium+ 0)
tags: [kata/spine, context-autonomy, plan, CA-P2, bootstrap, docs, live-proof]
---

# CA-P2 — policy, prose, docs, records + the live-proof battery

The consuming layer: bootstrap collects the ONE bundle and writes the new config keys; the dispatch
briefs gain the budget/report/continuation contracts; the deliverable docs ship; the acceptance
suite's live legs run. Ends with the operator merge gate, where the two **[VETO-FLAG]** items
(CA-L22 report home, CA-L25 intent-keyed BLOCK) are surfaced per §0.

Build mode: direct with dispatched workers, disjoint files, conductor integrates (D137-L8). **Dogfood
mandate:** run config `inlineEval: "telemetry"`; every worker brief carries the checkpoint mandate —
and, dogfooding THIS initiative, the C3-authored budget line (numbers per CA-L10/R-31) once C3 lands.

## Ownership (disjoint) + DAG

```yaml
ownership:
  C1: [skills/coordinate/kata-bootstrap/SKILL.md, skills/coordinate/kata-preflight/SKILL.md]
  C2: [skills/coordinate/kata-readiness/SKILL.md]
  C3: [skills/coordinate/kata-orchestrate/SKILL.md, skills/execute/kata-tdd/SKILL.md]
  C4: [protocol/observability.md]
  C5: [docs/platforms/kiro.md, docs/platforms/codex-cli.md, docs/platforms/copilot.md, docs/platforms/cursor.md, docs/platforms/gemini-cli.md]
  C6: [adapters/ADAPTER-CONTRACT-M4.md]
  C7: [CONTEXT.md]
  C8: [skills/plan/kata-plan/RUBRIC.md, skills/plan/kata-plan-essential/SKILL.md, skills/plan/kata-plan-standard/SKILL.md, skills/plan/kata-plan-advanced/SKILL.md]
  C9: [skills/evaluate/kata-evaluate/SKILL.md, skills/evaluate/kata-review/RUBRIC.md, skills/evaluate/kata-review-essential/SKILL.md, skills/evaluate/kata-review-standard/SKILL.md, skills/evaluate/kata-review-advanced/SKILL.md, .planning/HANDOFF-NEXT-SESSION.md]
waves:
  wave1: [C1, C3, C4, C5, C6, C7, C8, C9]
  wave2: [C2]
depends_on:
  C2: [C1]
tasks:
  C1: { estimate: 45, class: code }
  C2: { estimate: 15, class: code }
  C3: { estimate: 45, class: code }
  C4: { estimate: 20, class: code }
  C5: { estimate: 35, class: code }
  C6: { estimate: 15, class: code }
  C7: { estimate: 15, class: code }
  C8: { estimate: 20, class: code }
  C9: { estimate: 15, class: code }
```

**C10 (conductor closeout):** D146–D148 appended to `.planning/DECISIONS.md` (frontmatter d-records
clause verbatim: "D146 = the context-autonomy initiative freeze (this DESIGN); D147 = the R-37
deliberate BC departure (one-shot configs — including pre-v0.2.1 — rotate unconditionally); D148 =
the model-tiering gated premium amendment (§3)"); CHANGELOG v0.2.1 section; README skill-index regen
(`validate_skills --write`); `protocol/exec-safety.md` registry row for the A2 chain wrapper's
subprocess sink (deferred from P1 by single-owner discipline — a NOTE rides the P1 commit); the two
**[VETO-FLAG]** items surfaced explicitly at the operator merge gate; mutation-proof roster from
P0/P1 folded into the D-record.

**C11 (conductor, AFTER C1–C10 integrate) — the live-proof battery (CA-A1..A5 + CA-A11 b/c).**
In a THROWAWAY Claude profile (fixture pin, fold #4: the run config carries `inlineEval:
"telemetry"`, stated in each fixture definition):
- **CA-A1** verbatim: drive a run to the trigger → warn → handoff committed at a wave boundary
  (`kind: self`) → host auto-compact fires at/before the recommended window → SessionStart(compact)
  re-anchors on HANDOFF.md → next task completes with **zero task loss** AND resume graded on
  **context-quality restoration** (kata-orient 3-tier reload complete, budget-capped). Empirical
  measurements in the same profile (G4): actual auto-compact firing margin; bridge freshness
  unattended; the PreCompact input schema; the hook sync-time budget (the CA-L17 UNVERIFIED item);
  **that the gauge's `total_tokens` reflects `autoCompactWindow` capping** (grounds CA-L5's post-cap
  claim — fold #6).
- **CA-A2**: SMOKE-2/3 byte-identical protocol rerun, on-arm vs baseline; conductor context-per-task
  gauge-read per boundary shows a gated DROP with identical run outcomes; the DROP threshold is
  **judgment-graded at the operator merge gate** (fold #7 — deliberately not a number here); both
  arms' `inlineEval` posture stated in the fixture.
- **CA-A3** (each a separate arranged run/fixture): (a) no-gauge ⇒ N-wave rotation per CA-L4;
  (b) no-hooks ⇒ AGENTS.md-line manual re-anchor works; (c) auto-compact DISABLED ⇒ WARN attended /
  BLOCK walk-away (R-12); (d) stale bridge (>300 s) ⇒ fallback engaged, surfaced.
- **CA-A4**: install/preflight against a profile WITH a user statusline ⇒ user's statusLine + bridge
  byte-unchanged; chain-or-skip offered.
- **CA-A5**: under-threshold session ⇒ ZERO handoff refreshes, zero rotation events.
- **CA-A8 row 1**: a one-shot **pre-v0.2.1** config fixture (no `contextAutonomy` key) ⇒ rotation
  UNCONDITIONAL — the fixture NAMES the D147 departure (CA-L33; §4 row 1).
- **CA-A11(b)**: a task exceeding its quantum checkpoints → continuation report → pt-N+1 fresh
  dispatch resumes from the anchor with index continuity. **CA-A11(c)**: a worker final report is
  verdict+pointer inline with bulk at `.kata/reports/`.
**Fixture crossing mechanics (pinned):** the throwaway profile sets `autoCompactWindow: 100000`
(the key floor) and the fixture config carries a fixture-only `contextTrigger: 0.30`, so the
threshold crossing is affordable; the conductor drives the crossing by processing a sized fixture
corpus; G4 measurements read via the bridge file + `/context` readings.
Output: the CA REPORT to the operator — measurements, fixture verdicts, the A/B numbers, and the
merge-gate packet (VETO-FLAGs + the CA-A2 judgment grade).

## C1 — kata-bootstrap bundle step + config writes + lapse executor + force-run + premium gate

read_first: DESIGN Leg F (CA-L24..L26), Leg G (CA-L27/L28/L31), Leg H (CA-L32/L36/L37), CA-L10
substrate coupling; kata-bootstrap SKILL.md 0.2.0 (Phase 0 line 36, Phase 0b line 41, Phase 2 line
118, Phase 3 line 138); kata-preflight SKILL.md 0.1.2; E2 (`kata_settings.first_run_required`,
`record_*`), E4 (bundle engine fns) — cite the P0 function names exactly.

1. **The bundle step** (CA-L24, sequencing verbatim): "bundle collection is a NEW bootstrap step
   between Phase 2 (the advanced drawer) and the Phase-3 config write — **bootstrap collects;
   kata.config is written AFTER, with `models.premium.approved` recorded from the collected
   answer**." The bundle slots verbatim: "dependency installs/downloads + permission allowlist + the
   premium gate (Leg G) + the compact-window recommendation (CA-L16) + **the host-settings write
   slot** … approved like an install — never an implied side effect." "Collected ONCE; zero expected
   prompts for 8 hours after." Backstop slot is recommend-never-write (CA-L15: "Kata **never writes
   user settings silently**"); the recommendation is RECOMPUTED every run (CA-L37/R-42 — hostPosture
   never suppresses it). Accepted answers recorded via `record_accepted_defaults` (C-1 schema) +
   `record_host_posture` (audit-only).
2. **The premium gate** (CA-L27 verbatim, including): "**Decline ⇒ pin `models.anchor: "opus"` +
   hard-stop advising a `/model` switch** — the only honest decline (SR-4 …)"; "**Anchor-IS-fable**
   ⇒ confirm keep-using + warn: 'long-running loops on Fable as primary FM can drive costs up
   significantly.'"; the premium offer conditions (post-July-7, anchor=opus ∧ mode=advanced, scope =
   CRITICAL and CODING only, economy never). **Disclaimer TEXT authored here** (CA-7b — the §8 docs
   pass): a prominent cost disclaimer at the offer, plain language, stating knowing accrual of Fable
   API usage. Gate home (CA-L31): "collected in the PREFLIGHT phase of bootstrap's launch sequence
   (bootstrap orchestrates; preflight collects)" — the kata-preflight SKILL.md gains the collection
   prose; enforcement stays in orchestrate (P1/A4).
3. **Phase 3 writes** (CA-L32 + CA-L10 fold #4): new configs get `contextAutonomy: "on"` explicitly;
   "bootstrap, whenever it writes `contextAutonomy: "on"`, ALSO mandates `inlineEval: "telemetry"`
   or higher for that config"; `models.premium {offer, approved, scope, grantedMode}` written from
   the collected answer (CA-L28: "kata.config is authoritative … `.kata/preflight.json` carries the
   audit event only. Once-per-run = once per kata.config"); `contextTrigger` shown in the advanced
   drawer only, never asked (K5). Re-entrant same-as-last from a pre-v0.2.1 config writes the key at
   next touch, surfaced in the composition summary (R-23).
4. **Lapse executor** (CA-L31 verbatim): "re-entrant Phase 0/1 detecting `mode ≠ grantedMode` clears
   `approved`; the next preflight re-asks."
5. **Force-run marker** (CA-L36/CA-L37): Phase 0 calls `kata_settings.first_run_required` — absent
   marker OR gitSha mismatch ⇒ force the FULL first run; on completion `record_first_run(git_sha)`.
   Corrupt settings (C-3 verbatim): "bootstrap MUST detect the write failure, surface LOUDLY pointing
   at the corrupt file path, and stop; **never loop**."
6. Versions: kata-bootstrap 0.2.0 → 0.3.0 (MINOR), kata-preflight 0.1.2 → 0.2.0 (MINOR).

**Verify:** validator green with bumps; grep pins: "between Phase 2", "written AFTER",
"never an implied side effect", the anchor-is-fable warning string, "never loop",
`first_run_required`, "telemetry".

## C2 — kata-readiness WARN (pre-v0.2.1 configs) — after C1

read_first: DESIGN CA-L34; kata-readiness SKILL.md 0.2.0; C1's Phase-3 write-at-next-touch language
(match it verbatim — the WARN promises what C1 does).

1. CA-L34 verbatim: "kata-readiness (runs at every bootstrap entry incl. Phase 0b routing) gains a
   WARN: 'pre-v0.2.1 config lacks contextAutonomy — written at next composition (Phase 3) or opt in
   by config edit.' Surfaced, never silent, no retroactive flip." Plus the honest posture sentence
   (CA-L34): sprint boundaries already rotate by design; only intra-sprint refresh is absent —
   never a scare-WARN.
2. Version 0.2.0 → 0.2.1 (PATCH — additive WARN).

**Verify:** validator green; grep pin: the WARN text verbatim; no other readiness check altered
(`git diff` single-hunk discipline).

## C3 — report budgets + continuation contract + premium failure semantics (orchestrate + tdd briefs)

read_first: DESIGN Leg B (CA-L9/L10/L11), Leg E (CA-L22/L23), CA-L30; kata-orchestrate
SKILL.md 0.9.0 (dispatch template in "The loop"; "Dispatch-time model selection" + R2 at lines
697-778 — NOTE: lines 537-696, the M4 scheduler + ladder span, are OFF-LIMITS to this task);
kata-tdd SKILL.md 0.2.1 (checkpoint-cadence section); E1 `dispatch_budget` + E3 premium branch —
cite exactly.

1. **Dispatch brief template (orchestrate):** startup-load estimate at dispatch (CA-L9: "**Startup
   load** = the conductor-AUTHORED dispatch payload only (brief + packed orientation attachments),
   estimated at dispatch by the conductor"; worker read-ins never count); over-briefing WARN >0.30
   via `kata_gauge.dispatch_budget`; >0.40 = over-briefed ⇒ "split the task or slim the brief, a
   **mandate**, not a WARN" (cap WINS, CA-L9). **The budget line is mandatory prose in every
   dispatch brief** (CA-L11); R-31's four pins verbatim (CA-L10): "the BRIEF embeds the numbers
   (budget tokens, cap tokens, estimator basis); the estimate is worker-local from brief-embedded
   numbers + own activity, stated as approximate in the brief."
2. **Continuation contract (orchestrate + tdd):** CA-L10 verbatim: "at budget ⇒ finish the current
   chunk + checkpoint ⇒ if the remaining estimate fits under the 0.80 hard cap, CONTINUE to
   completion (no rotation to do 10% of a task); else return a **continuation report** (last
   checkpoint anchor + what remains + what was learned). Estimated activity ≥ cap ⇒ return
   UNCONDITIONALLY. Continuations reuse the existing M4 kill+fresh-dispatch primitive anchored at
   the last checkpoint (ADAPTER-CONTRACT-M4 primitive (b) — no new machinery); green-path inter-part
   evaluation is checkpoint-trailer scoring (**zero LLM calls**). Continue/return is re-evaluated at
   EVERY checkpoint." Substrate degrade (fold #4): "`inlineEval: off` ⇒ the continuation machinery
   DEGRADES to the brief's budget prose + return-at-task-boundary only." Enforcement honesty
   (CA-L11): worker observance is compliance; "TRUE enforcement is conductor-side — existing
   liveness machinery + the M4 kill primitive."
3. **Report contracts** (CA-L22/L23): worker final reports "size-contracted: **verdict + pointer
   inline**, bulk to the `.kata/reports/` artifact" at
   `.kata/reports/<runId>-<taskId>-<agent>-<kind>.md`; narration-economy riders in the brief
   template + report contracts; the durable-citation rule cross-referenced to
   protocol/observability.md (C4). [CA-L22 VETO-FLAG rides to the merge gate — noted.]
4. **Premium failure semantics** (CA-L30 verbatim, in the Dispatch-time model selection section):
   "Failed premium dispatch ⇒ **immediate OMIT/inherit at the anchor rung** — never an explicit
   anchor id … **One-step chain: premium → OMIT.** ANY premium dispatch failure — auth or not —
   **LAPSES `models.premium.approved` for the remainder of the run** … For the premium rung ONLY,
   401/403 ⇒ *premium-unavailable*: OMIT-inherit + LOUD surface (board DECISION + ledger `degraded
   {scope:"premium", reason:"auth-40x"|"unavailable"}` + handoff note) … Baseline (non-premium) R2
   auth-raise behavior is unchanged." The premium branch call site cites `kata_models`' E3 surface;
   NO-FIRE reasons surface as a board NOTE (§3.2).
5. Versions: kata-orchestrate 0.9.0 → 0.10.0 (MINOR), kata-tdd 0.2.1 → 0.3.0 (MINOR). Scope guard:
   the P1/A4 gauge sections land first and are untouched here except where this task's sections
   adjoin them. **F2's orchestrate-side leg is DROPPED from this task** — its target line sits
   inside the frozen ladder span (SKILL.md 608-696); the F2 stated rule ships in the observability
   doc (C4 — the home DESIGN F2 names). Deferred note: "F2 sentence in the frozen ladder span —
   deferred to the next M4-surface amendment."

**Verify:** validator green; grep pins: "verdict + pointer inline", ".kata/reports/", "One-step
chain: premium → OMIT", "auth-40x", "re-evaluated at EVERY checkpoint",
"0.30"/"0.40"/"0.80" present at the budget prose. Canary: **git diff of
skills/coordinate/kata-orchestrate/SKILL.md shows ZERO hunks intersecting lines 537-696** (the M4
scheduler + corrective-action ladder span).

## C4 — `protocol/observability.md` ships (from the committed draft)

read_first: DESIGN CA-L41 + CA-L22 durable-citation rule; DRAFT-observability.md (138 lines — the
deliverable text, this dir).

1. CA-L41 verbatim: "DRAFT-observability.md (this dir) is the deliverable text — it documents what
   exists at v0.2.0 plus the one v0.2.1 addition (the `.kata/reports/` row + durable-citation rule,
   CA-L22). Ships as `protocol/observability.md`; review dispatches receive its pointer-block brief."
   Copy the draft verbatim; fix only self-references ("this dir" pathing) and mark the v0.2.1 row as
   live. The "How to read checkpoints" hedge becomes the stated rule (CA-L44 F2, doc side): no
   last-good anchor ⇒ fresh attempt indexes from 0 at the task's dispatch base.
2. The draft file itself is left in place (spec history — never delete gate provenance).

**Verify:** file exists at protocol/observability.md; diff vs DRAFT is pathing + the F2 stated rule +
the live marker only; the durable-citation rule sentence present verbatim.

## C5 — per-platform recommended-config docs (5 pages)

read_first: DESIGN CA-L39 + §5 matrix (the content contract per page) + §8 (the 15 Confidence Gaps
ride as re-verify flags); RESEARCH-CROSS-PLATFORM.md (241 lines — source, "sourced … verbatim").

Per page (Kiro, Codex CLI, Copilot, Cursor, Gemini CLI — OP-6 set; Windsurf cut): "the knob to set,
the gauge channel if any, the resume primitive, and the must-guard risks" — each page carries its §5
row verbatim + the RESEARCH doc's per-platform detail + that platform's Confidence-Gap items as
re-verify-before-build flags (§8: "carried as re-verify items on each platform's docs page").
Header on every page: docs-only in v0.2.1 — no non-Claude code legs (CA-L39); the SR-6 conclusion
("internal-threshold-primary is the only portable architecture") stated once per page footer.

**Verify:** 5 files exist; each contains its §5 row content + a "Re-verify before build" section;
no page claims a live leg.

## C6 — adapter contract primitive (c) + the R-40 sentence

read_first: DESIGN CA-L38 (the paragraph is FROZEN VERBATIM — copy exactly);
adapters/ADAPTER-CONTRACT-M4.md:12-26 (primitives (a)/(b) — append after (b)).

1. Insert the CA-L38 "(c) session-respawn" paragraph verbatim (the full quoted text, including
   "Governs CONDUCTOR sessions only — worker attempt topology is out of scope; LD7 remains
   named-DEFERRED") + the R-40 sentence verbatim ("Absent primitive (b), budget-overrun enforcement
   degrades to worker compliance + livenessDeadline escalation, surfaced at preflight.").
2. Claude binding note: "host compaction + SessionStart(compact) = the (c)-equivalent" — the only
   live leg in v0.2.1; SR-14 scope guard ((c) does not silently absorb LD7).

**Verify:** diff is additive-only below the primitive list; the paragraph matches DESIGN CA-L38
byte-for-byte (mechanical: extract-and-compare the quoted span).

## C7 — glossary fold into CONTEXT.md

read_first: DESIGN header ("Those glossary entries are normative … stage into CONTEXT.md at merge");
GLOSSARY-STAGED.md (51 lines); CONTEXT.md section conventions (dated `##` sections).

1. New dated section "## Context autonomy — the gauge-driven self-handoff loop (D146, 2026-07-04)"
   holding the ten staged entries VERBATIM (smart zone, handoff, startup load, work quantum,
   continuation report, trigger fraction, gauge, backstop, premium offer, auto-context (rotation))
   including every `_Avoid_` line. No existing entry edited.

**Verify:** all ten terms present; diff additive-only; `_Avoid_` lines carried.

## C8 — kata-plan RUBRIC: plan-time quantum sizing (WARN + mandate) + tier PATCH bumps

read_first: DESIGN CA-L9 (plan/freeze mandate), CA-L11 (freeze WARN + estimator); kata-plan/RUBRIC.md
(the estimate:/class: precedent block); the D140/F7 rule (RUBRIC change ⇒ tier-skill PATCH bumps).

1. RUBRIC gains a "Dispatch sizing (context autonomy)" rule: CA-L11 verbatim — "a **WARN** (never
   hard-fail) when estimated task burn > the 40pp quantum, estimator `[TUNABLE]` tokens-per-chunk
   seeded from ledger `perTask` medians … (D136 posture: the estimate drives a WARN + split
   suggestion, fail-soft; splitting stays planner judgment)"; and the CA-L9 mandate leg — startup
   load > 0.40 ⇒ the dispatch is OVER-BRIEFED, "caught at plan/freeze time — split the task or slim
   the brief, a **mandate**, not a WARN". Arithmetic cited to `kata_gauge.dispatch_budget` (E1).
2. Tier bumps: kata-plan-essential/-standard/-advanced 0.1.2 → 0.1.3 (PATCH — the RUBRIC is their
   behavior, D140/F7).

**Verify:** validator green with the three bumps; grep pins: "40pp", "mandate, not a WARN",
"perTask".

## C9 — prose riders F1 + F5

read_first: DESIGN CA-L44; GROUNDING SMOKE-1 (8.35 is correct; calibration exclusion HOLDS);
.planning/HANDOFF-NEXT-SESSION.md:125 (the stale line); kata-evaluate SKILL.md + kata-review
RUBRIC.md (where verdict-tier guidance lives).

1. **F1** — verdict-tier variance calibration note where verdict-tier guidance lives (one note in
   kata-evaluate SKILL.md, cross-referenced from kata-review RUBRIC.md): SMOKE-observed verdict-tier
   variance is a calibration reality; graders state tier + rationale. Prose-only, no behavior
   change; kata-evaluate 0.3.0 → 0.3.1 (PATCH). **Because the kata-review family RUBRIC is touched,
   the three review tier skills get PATCH bumps per the D140/F7 rule C8 cites (RUBRIC change ⇒
   tier-skill PATCH bumps): kata-review-essential/-standard/-advanced each +0.0.1.**
2. **F5** — correct .planning/HANDOFF-NEXT-SESSION.md §7: "class_median returns None at
   min_samples=5" → the SMOKE-1 truth: non-calibration rows hold 6 code samples ≥ 5, so **8.35 is
   the correct output; calibration exclusion HOLDS**. *(Repo-note: the SMOKE doc names this "HANDOFF
   §7"; the line lives in HANDOFF-NEXT-SESSION.md:125 — this task pins the real file.)*

**Verify:** validator green with the kata-evaluate PATCH + the three kata-review tier PATCHes; the
stale sentence gone (grep returns the corrected text only).

## Phase verification (default-FAIL)

- Full suite green; validator 48+/0/0 with ALL bumps in sync; Snyk medium+ 0 on any changed
  first-party code; bump-on-modify honored on every touched SKILL.md (CA-A10).
- C11 battery complete: CA-A1 zero-task-loss + context-quality grade; CA-A2 A/B with stated fixture
  postures; CA-A3 (a)–(d) each surfaced; CA-A4 byte-unchanged user artifacts; CA-A5 zero churn;
  **CA-A8 row 1: one-shot pre-v0.2.1 fixture ⇒ unconditional rotation, D147 named**;
  CA-A11(b)/(c) fixtures pass; G4 empirical numbers recorded in the CA REPORT.
- Drift magnets: model-tiering frozen text above the appendix byte-unchanged; D83 0.40 untouched;
  DRAFT-observability retained; the M4 scheduler internals untouched.
- Operator merge gate packet: VETO-FLAGs (CA-L22, CA-L25), the CA-A2 judgment grade, D146–D148.

## Master coverage table (every DESIGN build item → exactly one owning task)

Legend: E# = PLAN-p0-engine, A# = PLAN-p1-claude-adapter, C# = this plan. Where a locked decision
has two named build legs, the legs are listed separately (each leg → one task).

| DESIGN item | Owning task |
|---|---|
| CA-L1 own-statusline superset writer (fold #3) | A1 |
| CA-L1 chain wrapper + never-clobber offer | A2 |
| CA-L1 reader priority (kata → user → fallback) | E1 |
| CA-L2 bridge superset schema (write) / %-only degrade (read) | A1 / E1 |
| CA-L3 gauge staleness 300 s | E1 |
| CA-L4 deterministic N-wave fallback | E1 |
| CA-L5 host-reported effective-window denominator | E1 (math) · A4 (wiring) |
| CA-L6 rotation-mandatory degradation | A5 |
| CA-L7 trigger fraction 0.70 / `contextTrigger` key | E1 (math) · E7 (key) · A5 (policy prose) |
| CA-L8 D83 untouched + pointer | E7 |
| CA-L9 quantum/cap/WARN arithmetic · plan mandate · dispatch WARN | E1 · C8 · C3 |
| CA-L10 continuation contract + inlineEval substrate coupling | C3 (contract) · C1 (coupling write) |
| CA-L11 enforcement honesty + freeze WARN | C3 · C8 |
| CA-L12 boundary placement + keep-working + resume quality | A4 · A5 (kata-orient leg) |
| CA-L13 generous-not-timid / NO-FIRE | A5 (prose) · C11 (CA-A5 proof) |
| CA-L14 reset ownership | A4 · A5 (mirror) |
| CA-L15 recommend-never-write | E4 (engine) · C1 (bundle surface) |
| CA-L16 backstop formula | E1 (formula) · E4 (bundle slot) |
| CA-L17 autoCompactEnabled check / PreCompact extension | E4 / A3 |
| CA-L18 SessionStart(compact) re-anchor | A3 |
| CA-L19 handoff staleness rule | A6 |
| CA-L20 AGENTS.md standing line | A7 |
| CA-L21 handoff taxonomy + `kind:` | A6 |
| CA-L22 reports home + durable-citation [VETO-FLAG] | C4 (rule) · C3 (contracts) · C10 (veto surface) |
| CA-L23 size contracts + narration economy | C3 |
| CA-L24 one bundle + host-settings slot + sequencing | C1 (collection) · E4 (audit event) · A4 (enforcement-only) |
| CA-L25 intent-keyed strictness [VETO-FLAG] | E4 (decision fn) · C10 (veto surface) |
| CA-L26 fixed allowlist checklist | E4 |
| CA-L27 premium gate semantics + disclaimer text (CA-7b) | C1 |
| CA-L28 `models.premium` config record | E7 (schema) · C1 (writer) |
| CA-L29 four conjuncts + explicit premium id | E3 |
| CA-L30 failure semantics (one-step OMIT, run-lapse, 401/403 carve-out) | C3 |
| CA-L31 gate home + mode-change lapse executor | C1 |
| CA-L32 contextAutonomy posture + Phase-3 write | E7 (key) · C1 (write) · E1 (validator fn) |
| CA-L33 R-37 departure (D147) | E7 (doc) · C10 (D147) · C11 (CA-A8 row-1 fixture) |
| CA-L34 no mid-roadmap auto-write + readiness WARN | C2 |
| CA-L35 settings home = existing `.kata-settings.json` | E2 |
| CA-L36 force-run marker + gitSha comparator + delete helper / factory-reset clear / bootstrap attach | E2 / E5 / C1 |
| CA-L37 audit-only posture + C-1 schema + C-3 + C-4 | E2 |
| CA-L38 primitive (c) + R-40 sentence | C6 |
| CA-L39 per-platform docs | C5 |
| CA-L40 parentTokens v3 columns | E6 |
| CA-L41 observability doc | C4 |
| CA-L42 shared-base-dir installer fix | E5 |
| CA-L43 frozen five pinned + hash-verified | E5 |
| CA-L44 F1 / F2 / F5 riders | C9 / C4 (orchestrate-span leg deferred to the next M4-surface amendment) / C9 |
| §2 kata.config rows / settings keys / bridge / kind / ledger v3 | E7 / E2 / A1 / A6 / E6 |
| §3 gated amendment (D148) | E3 (append) · C10 (D148 record) |
| CA-A1 live proof | C11 |
| CA-A2 SMOKE A/B rerun | C11 |
| CA-A3 degradation fixtures (a–d) | C11 (unit legs: E1 staleness/N-wave, E4 WARN/BLOCK) |
| CA-A4 never-clobber | C11 (mechanical leg: A2/A8 smoke) |
| CA-A5 NO-FIRE | C11 |
| CA-A6 corrupt-settings surface | E2 |
| CA-A7 premium resolver matrix | E3 |
| CA-A8 BC matrix executable rows | E1/E2/E3/E6/A6 (rows 1–5, 10–12) · C11 (row-1 run fixture) |
| CA-A9 installer fix | E5 |
| CA-A10 standing gates | every plan's phase verification |
| CA-A11 (a)/(d)/(e) unit · (b)/(c) fixtures | E1/E4/E2 · C11+C3 |

No orphans: every CA-L1..L44 row, every §2/§3 delta, and every CA-A row above maps to a named task.
Named deferrals (§8: LD7, non-Claude live legs, research/debug extras, τ calibration, OP-1,
Windsurf) are deliberately UNMAPPED — deferred, never silent.

## Out of scope

PokeVault/MindBridge deploy (OP-1); non-Claude live legs; any edit to frozen DESIGN text; τ
calibration; the operator commit gate itself (human).
