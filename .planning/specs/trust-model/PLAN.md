---
status: frozen (D169 freeze act 2026-08-16, conductor-performed per BURN-CHARTER with operator veto standing; six-row gate PASS-WITH-FOLDS — GATE-PLAN.md)
spec: trust-model
plan-of: ".planning/specs/trust-model/DESIGN.md rev 1 (conductor-GATED 2026-08-16) +
  BURN-CHARTER.md (operator-ruled intake) + D173 (conductor-directed addition: the doctrine
  amendment task). Governing ledger: GRILL-LEDGER.md status: converged."
date: 2026-08-16
author: plan-author (KH-T13 dispatch; prose-era dispatch recorded honestly — Guardian
  Honor-system, stated. This PLAN is the FIRST authored under the TM-F1 per-task evidence rule.)

# ── House task maps (AUTHORITATIVE — parse_plan_tasks reads these, never headings) ──
ownership:
  fix-mutation-prover:
    - tools/mutation_run.py
    - tools/tests/test_mutation_run.py
    - ".planning/specs/trust-model/evidence/x14-ci-green.md (the task's own declared evidence note — freeze-gate fold f, recorded amendment)"
  fix-statusline-crash:
    - adapters/claude/statusline_chain.py
    - tools/tests/test_statusline_chain.py
  fix-learn-feed-truth:
    - tools/learn_feed.py
    - tools/tests/test_learn_feed.py
  deferral-contract:
    - protocol/deferral.md
    - .planning/DEFERRED.md
    - .planning/ASSUMPTIONS.md
    - tools/validate_skills.py
  exec-safety-registration:
    - protocol/exec-safety.md
  stale-anchor-fixes:
    - skills/plan/kata-plan-standard/SKILL.md
    - skills/plan/kata-plan-essential/SKILL.md
    - skills/plan/kata-plan-advanced/SKILL.md
    - skills/plan/kata-design-doc/SKILL.md
    - skills/coordinate/kata-preflight/SKILL.md
    - skills/evaluate/kata-validate/SKILL.md
  hook-capability-probe:
    - .planning/specs/trust-model/evidence/hook-probe.md
  cursor-grammar:
    - tools/kata_board.py
    - tools/tests/test_kata_board.py
    - protocol/board.md
  cursor-durability:
    - tools/kata_trail.py
    - tools/tests/test_kata_trail.py
  evidence-grammar:
    - tools/evidence_grammar.py
    - tools/tests/test_evidence_grammar.py
    - tools/kata_restore.py
    - tools/tests/test_kata_restore.py
    - tools/probe_registry.json
  intent-freeze-field:
    - tools/intent_scaffold.py
    - tools/tests/test_intent_scaffold.py
    - protocol/intent.md
  ledger-status-normalization:
    - .planning/specs/trust-model/GRILL-LEDGER.md
    - ".planning/specs/*/GRILL-LEDGER.md (frontmatter status: line ONLY; full set enumerated by grep at task start and listed in the task gate record)"
  seam-engine:
    - tools/kata_dispatch.py
    - tools/kata_roles.py
    - tools/tests/test_kata_dispatch.py
    - tools/tests/test_kata_roles.py
  evidence-identity:
    - tools/run_result.py
    - tools/tests/test_run_result.py
  orchestrate-seam-migration:
    - skills/coordinate/kata-orchestrate/SKILL.md
  coordinate-skills-migration:
    - skills/coordinate/kata-loop/SKILL.md
    - skills/coordinate/kata-bootstrap/SKILL.md
    - skills/coordinate/kata-sprint/SKILL.md
    - skills/coordinate/kata-board/SKILL.md
    - skills/coordinate/kata-worktree/SKILL.md
    - skills/coordinate/kata-readiness/SKILL.md
    - "tools/validate_skills.py (REQUIRED_PROTOCOL key rename only — freeze-gate fold, shared-file table row 1)"
  authoring-skills-migration:
    - skills/plan/kata-plan/RUBRIC.md
    - skills/plan/kata-grill-standard/SKILL.md
    - skills/plan/kata-grill-essential/SKILL.md
    - skills/plan/kata-grill-advanced/SKILL.md
    - skills/plan/kata-research/SKILL.md
    - skills/plan/kata-advise/SKILL.md
    - skills/handoff/kata-defer/SKILL.md
  judge-contract-rewrites:
    - skills/evaluate/kata-evaluate/SKILL.md
    - skills/evaluate/kata-review-standard/SKILL.md
    - skills/evaluate/kata-review-essential/SKILL.md
    - skills/evaluate/kata-review-advanced/SKILL.md
    - skills/evaluate/kata-slop-check/SKILL.md
    - skills/evaluate/kata-inline-eval/SKILL.md
  judge-tripwire-corpora:
    - "skills/evaluate/*/fixtures/** (NEW per-judge known-bad corpora)"
    - tools/tripwire_check.py
    - tools/tests/test_tripwire_check.py
  blocking-detectors:
    - tools/truth_serum.py
    - tools/tests/test_truth_serum.py
  signal-detectors:
    - tools/truth_signals.py
    - tools/tests/test_truth_signals.py
    - "tools/tests/fixtures/orphan-corpus/** (T6–T11 calibration fixtures)"
  gate-preconditions:
    - tools/gate_preconditions.py
    - tools/tests/test_gate_preconditions.py
    - tools/gate_emit.py
  grounding-agent:
    - skills/evaluate/kata-grounding/SKILL.md
    - tools/grounding_gate.py
    - tools/tests/test_grounding_gate.py
  close-machinery:
    - tools/kata_close.py
    - tools/tests/test_kata_close.py
    - tools/kata_settings.py
    - tools/kata_config.py
    - "tools/learn_feed.py (redaction class-table extension only — freeze-gate fold, shared-file table row 2)"
    - "tools/tests/test_learn_feed.py (redaction tests only — freeze-gate fold)"
  doctrine-amendment:
    - docs/DETERMINISM-DOCTRINE.md
    - "tools/validate_skills.py (doctrine fingerprint pin ONLY, and only if the pin lives here — verify at task start; freeze-gate fold, shared-file table row 1)"
  hook-activation:
    - adapters/claude/hooks/kata-seam-guard.py
    - adapters/claude/settings.snippet.json
    - tools/kata_scope.py
    - tools/tests/test_seam_guard.py
    - "protocol/exec-safety.md (the hook's sink row only, RS-L4 — freeze-gate fold, shared-file table row 3)"
  ev1-badge-registry:
    - tools/badge_registry.json
    - tools/tests/test_badge_registry.py
    - "tools/validate_skills.py (the EV-1 check + exec-safety scan-scope extension — freeze-gate fold, shared-file table row 1)"
  guardian-relabel-pass:
    - .planning/specs/trust-model/evidence/promise-audit.md
    - .planning/BACKLOG.md
    - protocol/observability.md

waves:
  wave1: [fix-mutation-prover, fix-statusline-crash, fix-learn-feed-truth, deferral-contract, exec-safety-registration, stale-anchor-fixes, hook-capability-probe]
  wave2: [cursor-grammar, cursor-durability, evidence-grammar, intent-freeze-field, ledger-status-normalization]
  wave3: [seam-engine, evidence-identity]
  wave4: [orchestrate-seam-migration, coordinate-skills-migration, authoring-skills-migration]
  wave5: [judge-contract-rewrites]
  wave6: [blocking-detectors, signal-detectors, judge-tripwire-corpora]
  wave7: [gate-preconditions, grounding-agent, close-machinery, doctrine-amendment]
  wave8: [hook-activation, ev1-badge-registry]
  wave9: [guardian-relabel-pass]

depends_on:
  evidence-grammar: [exec-safety-registration]
  seam-engine: [cursor-grammar, intent-freeze-field, ledger-status-normalization]
  evidence-identity: [cursor-grammar]
  orchestrate-seam-migration: [seam-engine]
  coordinate-skills-migration: [seam-engine, cursor-grammar, deferral-contract]
  authoring-skills-migration: [seam-engine, evidence-grammar, stale-anchor-fixes]
  judge-contract-rewrites: [seam-engine, evidence-identity, stale-anchor-fixes]
  judge-tripwire-corpora: [judge-contract-rewrites]
  blocking-detectors: [deferral-contract]
  gate-preconditions: [blocking-detectors, evidence-grammar, seam-engine, fix-mutation-prover, judge-tripwire-corpora]
  grounding-agent: [blocking-detectors, signal-detectors, seam-engine]
  close-machinery: [seam-engine, evidence-grammar, fix-learn-feed-truth, deferral-contract, cursor-durability]
  hook-activation: [hook-capability-probe, orchestrate-seam-migration, coordinate-skills-migration, authoring-skills-migration, judge-contract-rewrites, gate-preconditions]
  ev1-badge-registry: [blocking-detectors, deferral-contract]
  guardian-relabel-pass: [hook-activation, ev1-badge-registry, gate-preconditions]

# RUBRIC-legal work-class (code|research|debug — M4 risk leash). See Execution rules for why
# this stays the RUBRIC enum.
class:
  fix-mutation-prover: debug
  fix-statusline-crash: debug
  fix-learn-feed-truth: debug
  deferral-contract: code
  exec-safety-registration: code
  stale-anchor-fixes: code
  hook-capability-probe: research
  cursor-grammar: code
  cursor-durability: code
  evidence-grammar: code
  intent-freeze-field: code
  ledger-status-normalization: code
  seam-engine: code
  evidence-identity: code
  orchestrate-seam-migration: code
  coordinate-skills-migration: code
  authoring-skills-migration: code
  judge-contract-rewrites: code
  judge-tripwire-corpora: code
  blocking-detectors: code
  signal-detectors: code
  gate-preconditions: code
  grounding-agent: code
  close-machinery: code
  doctrine-amendment: code
  hook-activation: code
  ev1-badge-registry: code
  guardian-relabel-pass: code

# D59/D131 model-tier class per task (critical = anchor; coding = −1; economy = −1/−2).
# Dispatch-brief-required by the burn charter (Fable anchor).
dispatch_class:
  fix-mutation-prover: coding
  fix-statusline-crash: coding
  fix-learn-feed-truth: coding
  deferral-contract: coding
  exec-safety-registration: coding
  stale-anchor-fixes: economy
  hook-capability-probe: coding
  cursor-grammar: coding
  cursor-durability: coding
  evidence-grammar: coding
  intent-freeze-field: coding
  ledger-status-normalization: economy
  seam-engine: coding
  evidence-identity: coding
  orchestrate-seam-migration: coding
  coordinate-skills-migration: coding
  authoring-skills-migration: coding
  judge-contract-rewrites: critical
  judge-tripwire-corpora: coding
  blocking-detectors: coding
  signal-detectors: coding
  gate-preconditions: coding
  grounding-agent: coding
  close-machinery: coding
  doctrine-amendment: critical
  hook-activation: coding
  ev1-badge-registry: coding
  guardian-relabel-pass: coding

# TM-F1 / RS-H1 — per-task completion-evidence declarations (closed grammar, three forms:
# artifact:<path> | test:<pytest-node-id> | probe:<registered-name>). Test node ids named
# below are the NEW tests each task creates unless the node already exists (BL-X15's does).
evidence:
  fix-mutation-prover:
    - "test:tools/tests/test_mutation_run.py::test_sandbox_import_isolation_linux"
    - "artifact:.planning/specs/trust-model/evidence/x14-ci-green.md"
  fix-statusline-crash:
    - "test:tools/tests/test_statusline_chain.py::TestRunChild::test_empty_argv_fail_soft"
  fix-learn-feed-truth:
    - "test:tools/tests/test_learn_feed.py::test_real_ux_ledger_open_question_is_not_a_decision"
  deferral-contract:
    - "artifact:protocol/deferral.md"
  exec-safety-registration:
    - "artifact:protocol/exec-safety.md"
  stale-anchor-fixes:
    - "artifact:skills/plan/kata-plan-standard/SKILL.md"
    - "artifact:skills/plan/kata-plan-essential/SKILL.md"
    - "artifact:skills/plan/kata-plan-advanced/SKILL.md"
    - "artifact:skills/plan/kata-design-doc/SKILL.md"
    - "artifact:skills/coordinate/kata-preflight/SKILL.md"
    - "artifact:skills/evaluate/kata-validate/SKILL.md"
  hook-capability-probe:
    - "artifact:.planning/specs/trust-model/evidence/hook-probe.md"
  cursor-grammar:
    - "test:tools/tests/test_kata_board.py::test_cursor_grammar_roundtrip"
    - "artifact:protocol/board.md"
  cursor-durability:
    - "test:tools/tests/test_kata_trail.py::test_snapshot_carries_cursor_and_payloads"
  evidence-grammar:
    - "test:tools/tests/test_evidence_grammar.py::test_freeform_command_refused_at_freeze"
    - "artifact:tools/probe_registry.json"
  intent-freeze-field:
    - "test:tools/tests/test_intent_scaffold.py::test_freeze_true_writes_frozen_status"
  ledger-status-normalization:
    - "artifact:.planning/specs/trust-model/GRILL-LEDGER.md"
  seam-engine:
    - "test:tools/tests/test_kata_dispatch.py::test_mint_refuses_unmet_governor_state"
    - "test:tools/tests/test_kata_dispatch.py::test_record_claim_is_atomic_single_use"
  evidence-identity:
    - "test:tools/tests/test_run_result.py::test_wrong_runid_evidence_refused"
    - "test:tools/tests/test_run_result.py::test_per_gate_parsed_counts"
  orchestrate-seam-migration:
    - "artifact:skills/coordinate/kata-orchestrate/SKILL.md"
  coordinate-skills-migration:
    - "artifact:skills/coordinate/kata-loop/SKILL.md"
    - "artifact:skills/coordinate/kata-board/SKILL.md"
  authoring-skills-migration:
    - "artifact:skills/plan/kata-plan/RUBRIC.md"
  judge-contract-rewrites:
    - "artifact:skills/evaluate/kata-evaluate/SKILL.md"
  judge-tripwire-corpora:
    - "test:tools/tests/test_tripwire_check.py::test_every_landed_judge_fails_its_known_bad_corpus"
  blocking-detectors:
    - "test:tools/tests/test_truth_serum.py::test_stub_body_without_def_ref_blocks"
    - "test:tools/tests/test_truth_serum.py::test_zero_input_refuses_to_certify"
  signal-detectors:
    - "test:tools/tests/test_truth_signals.py::test_orphan_corpus_calibration_t6_t11"
  gate-preconditions:
    - "test:tools/tests/test_gate_preconditions.py::test_task_gate_refuses_without_mutation_rerun_record"
  grounding-agent:
    - "artifact:skills/evaluate/kata-grounding/SKILL.md"
    - "test:tools/tests/test_grounding_gate.py::test_fact_table_emit_and_attest"
  close-machinery:
    - "test:tools/tests/test_kata_close.py::test_close_refuses_absent_records"
    - "test:tools/tests/test_kata_close.py::test_provenance_drift_fails_close"
  doctrine-amendment:
    - "artifact:docs/DETERMINISM-DOCTRINE.md"
  hook-activation:
    - "probe:deny-tripwire"
    - "test:tools/tests/test_seam_guard.py::test_recordless_agent_call_denied"
  ev1-badge-registry:
    - "test:tools/tests/test_badge_registry.py::test_uncited_badge_fails_validator"
    - "test:tools/tests/test_badge_registry.py::test_cited_but_dead_check_fails_validator"
  guardian-relabel-pass:
    - "artifact:.planning/specs/trust-model/evidence/promise-audit.md"
---

# PLAN — the Trust Model burn

**In plain terms:** this plan sequences the Trust Model DESIGN (the seam, the cursor, Truth
Serum v1, grounding, the plan-grounding close) plus the three charter ride-alongs (the Linux
mutation-prover fix, the statusline crash fix, the learn_feed truth fix) into **nine waves /
28 tasks**, each wave one BBM-12 loop iteration. It adds no new decisions — every task quotes
its LOCKED anchor from the DESIGN; anything the DESIGN did not resolve is an ESCALATE, never a
builder guess.

**Reading rule:** the frontmatter maps are authoritative (`parse_plan_tasks`); the task blocks
below are the human-readable elaboration. DESIGN § references are to
`.planning/specs/trust-model/DESIGN.md` rev 1.

---

## Execution rules (binding on the executing session)

1. **BBM-12 — the ENTIRE loop, wave-per-loop.** Each wave below is ONE loop iteration with its
   own **default-FAIL final eval** (fresh-context, no-write kata-evaluate). A failed wave eval
   re-loops the wave as a **sibling child run** per DESIGN §2.7/R2-M2 (`parent-run:` = same
   parent, `prev-run:` = the failed sibling) and per §5.3's two-legal-paths rule: another loop
   pass, or recorded operator acceptance (`accepted_by`/`accepted_at`) — nothing else closes a
   failed wave.
2. **Hybrid gating (BBM-1)** · **manual pinned worktrees outside the repo root (BBM-9)** ·
   **builders briefed to push back (H7)** — all per the burn charter.
3. **Model routing — Fable anchor (charter):** `dispatch_class:` above is the D59/D131 tier map
   — `critical` at the anchor, `coding` −1, `economy` per-mode tier-down. `class:` stays the
   RUBRIC `code|research|debug` enum (the M4 risk-leash input) because an unknown `class:` value
   fails plan freeze — the two maps carry the two different meanings; neither is optional.
4. **Prose-era honesty (charter, DESIGN §11.12):** this burn BUILDS the seam. Dispatches are
   Honor-system-declared in every status surface until the seam exists. **Dogfood rule:** from
   the wave after `seam-engine` lands, the conductor mints every dispatch through the engine
   (`mint` → launch → `capture`) — still declared Honor-system until hook activation (wave 8),
   because nothing yet denies a bypass. Early-wave loop mechanics (sibling-child re-loops)
   are executed as prose discipline and recorded; the cursor machinery formalizes them once
   wave 2–3 land.
5. **Operator sequencing mandate (DESIGN §7, verbatim-intent):** no build dispatch before the
   full documented handoff + UX-15 agent orientation is committed. A dispatch before that is
   drift.
6. **Human-approval moments in this plan** (pin re-approvals, the intent-schema two-step, the
   doctrine fingerprint re-approval, the BL-X12 fork ruling if escalated): hybrid gating applies
   — unattended contexts PARK the task (TM-B5 park semantics), never proceed and never die
   silently.
7. **Freeze:** this PLAN was authored `status: DRAFT — awaiting freeze-gate`; the conductor
   gated it (six-row rubric, PASS-WITH-FOLDS — `GATE-PLAN.md`) and performed the **D169 freeze
   act 2026-08-16** (conductor-performed per the BURN-CHARTER; the operator may veto — the
   freeze is surfaced, not silent).
8. **Worker-brief budget** (`kata_gauge.dispatch_budget`, CA-L9/CA-L11) applies at dispatch time;
   tasks are sized here to ≤ one builder session each (the two largest — `seam-engine`,
   `orchestrate-seam-migration` — are single-file-focused precisely so a split, if needed at
   dispatch, is mechanical).

### Shared-file sequencing (RUBRIC's cross-wave rule, declared not hidden)

Ownership is **disjoint within every wave** (the concurrency guarantee). Four files recur
across *sequential* waves, per RUBRIC's "sequence them in the DAG" rule — listed so no gate
reads overlap as drift:

| File | Waves / tasks |
|---|---|
| `tools/validate_skills.py` | W1 `deferral-contract` (REQUIRED_PROTOCOL entry) → W4 `coordinate-skills-migration` (board→cursor registry key) → W8 `ev1-badge-registry` (new check + exec-safety scan-scope extension) → W7 `doctrine-amendment` touches only the doctrine fingerprint pin if it lives here (verify at task start) |
| `tools/learn_feed.py` | W1 `fix-learn-feed-truth` → W7 `close-machinery` (redaction class-table extension — ONE scrub per RS-M7) |
| `protocol/exec-safety.md` | W1 `exec-safety-registration` → W8 `hook-activation` (the hook's own sink row, RS-L4) |
| the five stale-anchor SKILL.md files | W1 `stale-anchor-fixes` (anchor lines only) → W4/W5 full inbound-contract rewrites |
| `README.md` (generated skill index) | **Amendment G2 (conductor, 2026-08-16):** owned by NO task — every SKILL.md version bump desyncs the generated index, so regeneration (`validate_skills.py --write`) is a per-wave INTEGRATION-time conductor act, run exactly once on the integration branch after merging the wave's task branches, before the wave-gate validator run. Skill-touching task gates are judged green-except-README (that one error class is integration-owed). Applies to W1 and especially W4/W5. |

`kata-orchestrate/SKILL.md`'s stale anchors are fixed inside its own W4 rewrite (not W1) to
avoid a same-file double-touch; the ledger's "five skills fix in wave 1" is satisfied by the
six non-orchestrate cite-sites landing in W1 (the grep-verified full set is enumerated in the
`stale-anchor-fixes` task).

### Out of scope — by design, not omission

- **The presentation-layer build wave (DESIGN §6.1 surfaces 1–4 in full UX grammar) is
  EXCLUDED from this plan** — it waits on UX round C1 + the operator's freeze sign-off
  (DESIGN §6.5, charter). The **minimal run-start declaration (§6.4) is NOT excluded** — it
  ships inside `seam-engine` (wave 3), so the interim has its honest surface from day one.
- BL-X04/X08/X09/X10 (post-burn queue) · everything priority 6+ (charter).
- Truth Serum v2 promotions — BL-N24. **Standing rule (TM-D2): any v1 scope cut made during
  this burn lands in BL-N24 with its promotion criterion, or it is a PD-1 silent deferral.**
- The wrapper door (BL-N21), agentDef population (BL-N20), learning-scope taxonomy (BL-N16
  grill) — FEEDS, not builds (DESIGN §10).

---

## Threat register — STRIDE-lite for this build's new surfaces

References DESIGN §8 rows — **do not re-derive**; builders read the cited row before touching
the surface.

| Surface (task) | S | T | R | I | D | E | DESIGN §8 anchor |
|---|---|---|---|---|---|---|---|
| Deny/capture hook (`hook-activation`) | absent/neutered hook impersonating enforcement → fingerprint + live deny-tripwire; no-result ⇒ Dormant | settings entry tamper → install digest compare; `~/.claude/settings.json` unguardable (stated residual) | DENY events are cursor records | hook input parsed structured, never string-eval | wedged hook detected at seam init; internal timeout pinned below host's; marker-loss edge stated | hook runs only in kata scope (run marker); non-kata untouched | S3, S6, RS-H4, RS-M10, RS-M11, RS-L5 |
| Dispatch record store (`seam-engine`) | fabricated record → cursor-lineage mismatch (post-hoc); adversarial-conductor residual stated | records tier-3; cursor chain entry is the durable half; trail refs = git tamper-evidence (evidential-until-pushed) | mint/claim/consume all cursor-lined | briefHash + governed-artifact refs are data | replay → atomic single-use claim (os.rename); expiry defense-in-depth only | governor ladder: no mint without required state; unknown ⇒ refuse ⇒ park | S1, RS-H2, RS-M8, RS-M12 |
| `evidence:` grammar + verify commands (`evidence-grammar`) | — | probe registry committed with repo | freeze gate records grammar validation | closed three-form grammar; freeform command REFUSED; `_guard_path`/`_guard_node_id` reuse (CWE-23) | parse failure = refusal, never skip (anti-vacuity) | structured argv, no shell; trust domain LLM-authored ⇒ compile-or-refuse | S2, RS-H1 |
| Cursor + payloads (`cursor-grammar`) | worker-line forgery → `~parent-seq` lineage stamps | append-only; retro-edit tamper-evidence via trail snapshots | seam-authored types have one writer class | line content is DATA to folds/renderers; ANSI/control-strip + provenance-fields rendering | fold purity: side effects only after fold completes | children never write the parent's log | S1, S2, RS-M13 |
| Redaction/consent at close (`close-machinery`) | — | scrub at the COMMIT act (TOCTOU-closed) | first-run consent remembered machine-local | detection-not-prevention stated | — | outward acts human-gated; no auto-push | S4, S5, RS-M6, RS-M7 |

---

## Escalation register (recorded forks a builder may trip on — ESCALATE, never guess)

| # | Where | The fork / trap | Rule |
|---|---|---|---|
| E1 | `fix-learn-feed-truth` | **BL-X12's recorded design fork:** status vocabulary in the bullets parser vs refusing the DECISIONS route on grill-ledger-marked files. | Triage FIRST inside the task; propose the fork choice as an ESCALATE/DECISION to the conductor **before building**. The backlog filing is explicit: "triage before building, do not guess." |
| E2 | `fix-mutation-prover` | BL-X14's cause is a **working hypothesis** (sandbox import-path resolution), "verify, do not assume". | Reproduce/falsify on Linux (CI or container) before fixing. Hypothesis falsified ⇒ ESCALATE with the observed mechanism; never fix the hypothesis instead of the bug. |
| E3 | `blocking-detectors` | B1 legitimately-empty bodies beyond the explicit mechanical suppressors (ABC/protocol-handler/`__init__.py`). | Residual legitimacy judgment **routes to the signal channel, never silently suppresses** (DESIGN §3.1 B1). New suppressor classes ⇒ ESCALATE. |
| E4 | `judge-contract-rewrites` | Per-judge VERDICT enum contents are enumerated AT this wave (R4 residual 4). | Enums must be closed and strict-fullmatch-parseable; any judge whose verdict space resists a closed enum ⇒ ESCALATE, don't invent a body-scan fallback (pass-2 low 14 forbids it). |
| E5 | `doctrine-amendment` | Scope creep: laws 11/12/14/16 + the two judgment-boundary clauses are **DECLINED by D173** with reasons recorded. | If the amendment grill reviewer proposes admitting any of them, that is a re-open of D173 — ESCALATE to the operator; the task must NOT include them. |
| E6 | `seam-engine` | `absorbed` ledger status **routes the mint to the absorbing ledger** — never satisfies, never hard-fails as unknown (pass-1 SHIP residual 2). | Implement routing; ambiguous absorption target ⇒ refuse-to-mint ⇒ park. |
| E7 | any task | A needed capability claimed as "reuses existing X" that the cited surface doesn't expose. | Verify the primitive before building on it (`protocol/reuse-claims.md`); mismatch ⇒ ESCALATE, not a silent shim. |
| E8 | `gate-preconditions` | Mutation-precondition activation is per-platform, **gated on BL-X14 closure** (R3-H3). | Activation table reads X14's recorded closure; "no Linux task gate fail-closes on a Broken prover." Activating early = drift. |

---

## Wave 1 — Bleeding fixes + standing contracts (7 tasks, one loop pass)

*Why first:* the charter rides BL-X14/X15/X12 explicitly EARLY; X14 ends the CI-red-12-days
state and gates every later mutation-precondition activation; X12 unblocks all grill-close
emits (including this grill's own retroactive emit); the two protocol contracts must exist
before anything consumes their grammars; the hook capability probe is DESIGN-mandated as "an
explicit early task (UX-28 discipline: assess, never assume)" (TM-B2.1).

### fix-mutation-prover — BL-X14: the Linux vacuity-prover fix (the anti-vacuity engine must itself be non-vacuous)
- **What it builds:** the fix for "the sandboxed mutated copy is never what the re-run imports"
  on Linux (`_redirect_cmd`'s residual-live-root guard checks argv, not the import
  path/environment — hypothesis, see E2), plus a pinning regression test proving sandbox import
  isolation per-platform. Also converts the mutation sink's command execution to **structured
  argv under the RS-H1 grammar** (pass-2 medium 3 — "the mutation runner's command execution
  converts to structured argv under the same grammar"), reusing the live `_guard_node_id`
  precedents (`benchmark_def.py:805`, `benchmark.py:106`) — assigned here, not to
  `evidence-grammar`, to keep `mutation_run.py` single-owner.
- **read_first:** DESIGN §3.6; BACKLOG BL-X14 (line 486); `tools/mutation_run.py:218-315`.
- **Acceptance (falsifiable):** the ~61 mutation-proof meta-tests
  (`test_benchmark.py:1636-1710`, `test_recurrence_detect.py`, `test_usage_meter.py`,
  `test_validation_misses.py`) return `{'testWentRed': True}` for biting mutations on
  ubuntu-latest; full gauntlet CI green on a pushed branch; new isolation test fails against
  the pre-fix code (proven by reverting locally); `shell=True` absent from the mutation sink.
- **Verify:** `python -m pytest tools/tests/test_mutation_run.py -q` locally + the CI gauntlet
  run on the task branch (the ubuntu leg is the load-bearing one — record run URL + SHA in
  `.planning/specs/trust-model/evidence/x14-ci-green.md`).
- **Evidence:** per frontmatter. *(Judgment call, declared: a green CI run has no form in the
  closed evidence grammar, so it is captured as a committed evidence-note artifact.)*
- **Closes:** the activation gate for §3.6 on Linux; the CI-red state. Guardian: the CI
  gauntlet moves Broken → Verified **only with this evidence cited** (§6.6).

### fix-statusline-crash — BL-X15: statusline empty-argv fail-soft on Linux
- **What it builds:** `statusline_chain` must never crash — fix the `IndexError` on empty
  delegate argv on the Linux path.
- **Acceptance:** `tools/tests/test_statusline_chain.py::TestRunChild::test_empty_argv_fail_soft`
  passes on ubuntu-latest (it already passes on Windows — the CI leg is the proof).
- **Verify:** `python -m pytest tools/tests/test_statusline_chain.py -q` + same CI run as X14
  (charter: "rides X14's run").

### fix-learn-feed-truth — BL-X12: learn_feed must never emit OPEN as resolved
- **What it builds:** fixes for the four challenger-reproduced sub-defects: (a) `--ledger`
  route returns zero entries for bullet-form ledgers; (b) `--decisions` drops
  wrapped-bold-anchor entries; (c) `parse_decisions_bullets` hardcodes `status="resolved"`
  (the live wrong-output defect); (d) `·`-separator anchors yield unstable page keys.
- **Escalation point E1 (the recorded fork) — triage before building.**
- **Acceptance:** each sub-defect has a pinning test reproducing the challenger's case against
  the real UX GRILL-LEDGER shape; the verbatim "UX-5 · OPEN QUESTION" fixture never emits as a
  resolved decision; the UX-28/UX-32 wrapped-anchor entries parse.
- **Verify:** `python -m pytest tools/tests/test_learn_feed.py -q`.
- **Post-close note (conductor act, not this task):** the trust-model grill's own retroactive
  `learn_feed` emit unblocks when this lands (DESIGN §1.4 ledger row: a blocked emit never
  blocks convergence status — the emit is owed, not the status).

### deferral-contract — protocol/deferral.md: the sanctioned-deferral ledger contract
- **What it builds:** `protocol/deferral.md` landing the DESIGN §3.2 draft text
  verbatim-in-substance (entry grammar `## DEF-<n> — <title> · <STATUS> (<date>)`, required
  What/Why/Provenance/Owed-to, STATUS enum `OPEN|ACCEPTED|CLOSED`, `accepted_by`/`accepted_at`
  approval record, closure-requires-closing-commit, the D3b same-line `DEF-*` BLOCKER rule,
  parse-failure-is-refusal); registration in `REQUIRED_PROTOCOL` + clause pin
  (`tools/validate_skills.py`); retrofit of `.planning/DEFERRED.md` + `.planning/ASSUMPTIONS.md`
  (`ASM-<n>`) to the schema.
- **Acceptance:** `python tools/validate_skills.py` green with the new registration; both
  ledgers parse under the schema (mechanical parse check included in the contract's terms);
  contract text passes the authored-artifact gate.
- **Verify:** `python tools/validate_skills.py`.

### exec-safety-registration — the `evidence:` capability registered in protocol/exec-safety.md
- **What it builds:** the RS-H1 registration: field + closed three-form grammar + structured
  argv compilation + trust domains (LLM-authored ⇒ compile-through-grammar-or-refuse), per
  exec-safety's own new-capability law.
- **Sequencing note (declared deviation):** DESIGN says this happens "BEFORE build". It is
  scheduled as a wave-1 task — inside the first loop pass, strictly before any
  grammar-consuming machinery activates (`evidence-grammar` W2 depends on it; gate wiring is
  W7). If the conductor prefers the literal reading, this task lifts out of wave 1 into the
  freeze package unchanged — surfaced at the freeze gate.
- **Verify:** `python tools/validate_skills.py`.

### stale-anchor-fixes — fix the Broken `kata_dispatch` line anchors across the citing skills
- **What it builds:** §7 migration scope: "stale `kata_dispatch` line anchors across five
  skills fix in wave 1 (already Broken rows)." Grep-verified cite-set outside kata-orchestrate:
  the three kata-plan tiers, kata-design-doc, kata-preflight, kata-validate. Anchor lines
  re-pointed at the live `tools/kata_dispatch.py` symbols (`build_brief:43`, `dispatch:219`,
  `normalize:283` per DESIGN §1.3 — re-verify against HEAD at task start). Anchor lines ONLY —
  the full inbound-contract rewrites are W4/W5's.
- **Acceptance:** every `kata_dispatch` `file:line` citation in the six files resolves to the
  named symbol at the named line; validator green.
- **Verify:** `python tools/validate_skills.py` + a recorded grep of the six files' anchors.

### hook-capability-probe — assess, never assume: do both hook edges work on this host?
- **What it builds:** the TM-B2.1 "explicit early task": live-probe PreToolUse-class deny
  capability and PostToolUse-class capture capability on the Claude host (benign scratch-scope
  hook, both edges), plus the Bash-leg command-shape visibility check (`codex exec` /
  `kiro-cli chat` shapes). Records results, versions, and limits in
  `.planning/specs/trust-model/evidence/hook-probe.md`. **Kiro floor per BL-N25:** interception
  UNPROBED ⇒ plan as detection-only (Honor-system declared) — this probe covers the Claude
  host only; it must state that scope.
- **Acceptance:** the evidence note answers, with observed (not assumed) results: can a
  PreToolUse hook deny an Agent call; can a PostToolUse hook read the return envelope's first
  line; what the Bash leg can and cannot see. Wave-8's design inputs cite this note.
- **Verify:** the note's probe transcripts are reproducible (commands included).

**Wave-1 gate:** default-FAIL final eval over all seven task gates + CI green on the X14/X15
branch. Re-loop per Execution rule 1.

---

## Wave 2 — The cursor (5 tasks, one loop pass)

*Why now:* the seam (W3) authors cursor lines — the grammar must exist first (DESIGN §7
order: engine + cursor first; within that pair, cursor before seam is forced by the
write-dependency; declared as a split of the brief's single "wave 1", see Deviations).

### cursor-grammar — one log, upgraded: the cursor grammar migration + ONE pin re-approval
- **What it builds (all in THIS task — R-M3: "Everything below lands in the SAME build wave
  with ONE re-approval of the pinned clause"):** the run-header block
  (`prev-run:`/`parent-run:`/`prev-segment:` reserved), the full TYPE enumeration
  (worker/orch/seam types), `seq~parent-seq` lineage stamps, ` | ` field separators,
  ` payload=<path>` pointed-to JSON payloads under `.kata/payloads/<runId>-<seq>.json`,
  VERDICT payload schema `{verdict, evidencePointers[], judgeDispatchSeq, runId}`, seq
  assignment `(observed max)+1` with duplicate-worker-seq file-position ordering, and the
  fold/parser updates **including the K3 concurrency snippet rewrite to a cross-cursor
  (runId, seq) fold** — exact BNF per DESIGN §2.2, transcribed not re-derived. `protocol/
  board.md` rewritten to the cursor contract (grammar + writer classes + the CURSOR name;
  erratum carried: the fanout-survey's "K3" schema anchor is the K5 schema, `board.md:57`).
  **The old 5-field grammar parses nowhere after this task.**
- **Human moment:** the ONE clause-pin re-approval of `protocol/board.md` (Execution rule 6).
  The file RENAME (board→cursor heritage) rides W4 `coordinate-skills-migration`, not here.
- **Acceptance:** round-trip write/parse tests over every line type + header pointer +
  payload pointer; ordering-of-record = (runId, seq) + parent fold-order with wall-clock
  never load-bearing (TM-C7/C6); a 5-field legacy line is a parse REFUSAL; pin re-approval
  recorded.
- **Verify:** `python -m pytest tools/tests/test_kata_board.py -q` +
  `python tools/validate_skills.py`.

### cursor-durability — snapshots that make "durable at the moment they exist" true
- **What it builds:** TM-C3/C4/RS-L3/R-M4: snapshot cadence fires on every PHASE and VERDICT
  append; snapshot content extends from board-only to **cursor file + pointed-to payloads**;
  per-run trail refs `refs/kata/trail/<runId>` (legacy ref unchanged, BC); the snapshot skip
  sentinel becomes a recorded cursor event at the seam call site; resilience levels
  **derived** (full requires a push receipt recorded on the cursor — never the config flag /
  local / degraded); the `cursor.pushTrail` config key (default never-push; the OFFER itself
  is closeout's, later).
- **Acceptance:** snapshot after a VERDICT append contains the payload file; per-run ref
  created per runId; skip sentinel appears as a cursor event; derived level is "Partially
  verified (local)" on a healthy default run (pass-1 SHIP residual 6 wording).
- **Verify:** `python -m pytest tools/tests/test_kata_trail.py -q`.

### evidence-grammar — the closed `evidence:` grammar + plan-schema extension + probe registry
- **What it builds:** `tools/evidence_grammar.py` — the three forms (`artifact:` path-guarded
  via the `_guard_path` pattern; `test:` fullmatch node-id grammar compiled to structured argv
  `[python, -m, pytest, <id>]`, reusing `_guard_node_id` (`benchmark_def.py:805`); `probe:`
  resolved against the committed `tools/probe_registry.json` — unknown name ⇒ refuse;
  **freeform command string REFUSED at the freeze gate**); `parse_plan_tasks`
  (`tools/kata_restore.py:235`) extended to carry + grammar-check the per-task `evidence:`
  frontmatter map (R-M9) — absent or grammar-invalid declarations fail the freeze check.
  Registry seeded with `deny-tripwire` and `gauntlet` argv templates (wave 8 cites the first).
- **Acceptance:** each of the three forms parses and compiles to argv/path/registry-lookup;
  freeform string refused; traversal attempts refused (CWE-23 cases in tests); a PLAN missing
  a task's `evidence:` fails `parse_plan_tasks`' extended check; THIS plan's own frontmatter
  passes it (reflexive TM-F1 — the first plan under the rule validates under its own machinery).
- **Verify:** `python -m pytest tools/tests/test_evidence_grammar.py tools/tests/test_kata_restore.py -q`.

### intent-freeze-field — INTENT.md gains a machine-checkable frozen status
- **What it builds:** R2-H1/R3-L2: `INTENT.md` frontmatter `status: draft|frozen`;
  `intent_scaffold.write_intent` writes `frozen` at Phase 6 via a new **explicit `freeze=True`
  keyword argument (named, not inferred)**; `protocol/intent.md` schema amendment as an
  explicit additive amendment **with its own two-step** (the acceptanceCriteria precedent —
  human re-approval, Execution rule 6). The BC law travels with the text: a direct one-shot
  harness run (`protocol/intent.md:11`) governs under `plan` exactly as today — `intent:frozen`
  binds only initiation-entered runs (R3-H2).
- **Acceptance:** `freeze=True` writes `status: frozen`; default writes `draft`; schema
  amendment approved and recorded; the BC case stated in the protocol text.
- **Verify:** `python -m pytest tools/tests/test_intent_scaffold.py -q` +
  `python tools/validate_skills.py`.

### ledger-status-normalization — the live free-prose ledger statuses become the closed enum
- **What it builds:** R3-M3/R4 residual 5: every live grill ledger's frontmatter `status:`
  normalizes to the four-value enum `draft|converged|frozen|absorbed` (first-word parse rule,
  BL-F01), so W3's `ledger_status` predicate has a clean corpus. Grep-enumerate the live set
  (`GRILL COMPLETE…`, `GRILL DONE…` forms) at task start; list the touched files in the task
  gate record. Data-only — no code (the predicate is `seam-engine`'s).
- **Acceptance:** grep for non-enum `status:` first-words across `.planning/specs/*/GRILL-LEDGER.md`
  returns zero; the trust-model ledger reads `converged`.
- **Verify:** the recorded grep + `python tools/validate_skills.py`.

**Wave-2 gate:** default-FAIL final eval; both human re-approvals recorded.

---

## Wave 3 — The seam engine (2 tasks, one loop pass)

### seam-engine — every agent launch becomes a code act
- **What it builds** (extends `tools/kata_dispatch.py` — "module layout is a build detail; the
  surface is contract", all engine code under the Determinism Doctrine, D172):
  - `mint(*, governs, role, …)` — **`governs` required, keyword-only, no default** (R3-M4);
    the governor ladder per DESIGN §1.4: `plan`→`assert_frozen` (unchanged, D169);
    `ledger`→new `ledger_status` predicate (four-value enum, first-word parse; ordering
    `draft < converged`, `frozen` satisfies what `converged` satisfies, **`absorbed` ROUTES**
    — E6); `intent`→`intent_status` reader; `initiation`→open INITIATION/AUTHORING phase on
    the live cursor + priming-prompt hash, graded Honor-system with **rung exclusivity**
    (refused once a stronger governor is recorded or the phase closed; re-open = recorded
    DENY-class event, RS-H3). Per-role minimum states exactly per the §1.4 table. Unknown
    governor / unmet state ⇒ **refuse to mint** ⇒ TM-B5 park.
  - The dispatch record (§1.5): all required fields incl. `agentDef` slot RESERVED-unpopulated;
    `.kata/dispatch/<runId>-<seq>.json` pending → **atomic claim by `os.rename` into
    `consumed/`** (RS-H2 — order-independence ACHIEVED BY the claim; `fs_atomic`'s
    replace-only primitive explicitly NOT the consume mechanism) → mark-consumed-and-retain;
    `mintedUtc` bounds MINT→LAUNCH only, defense-in-depth (RS-M12).
  - `run_start()` (§1.3/§2.4): new-run vs resume discrimination (no live cursor / closed run ⇒
    rotate + mint runId; unclosed ⇒ ADOPT, never re-mint; re-loop and loop-back always mint);
    atomic rotation sequence (archive rename then header write; torn rotation detected);
    orphan-record reaping; run-marker write (RS-L5); hook fingerprint + deny-tripwire probes
    (graceful pre-hook: no hook ⇒ enforcement **Dormant**); config-vs-settings consistency
    check; **the minimal run-start declaration (§6.4)** — plain-text
    enforcement/resilience/capture Guardian line, seam-derived, mode words in parentheses only.
  - `capture()` — the **ONE verdict parser, two callers**: strict fullmatch on line 1 of the
    tool-result ENVELOPE, never scanning the body; no-match ⇒ the absent-records refusal path,
    **never a body-scan fallback**; conductor-invoked leg declared Honor-system (RS-M5). VERDICT
    (judges) / DOWN (child runs, parent-seam-authored per §2.3) lines + payloads.
  - `phase()` / `deny()` — the §2.6 phase vocabulary (closed enum, `open/close/run-closed` msg
    grammar); DENY lines naming the legal path, incl. the retry-race re-mint message (pass-2
    low 11).
  - `ROLE_GROUPS` extension (`kata_roles.py:35`): + `reviewer · slop · inline-eval · advisor ·
    critic · challenger · grounding`; `HOST_ONLY_ROLES` UNCHANGED (R-M5).
  - **NOT here:** `close_run` internals (W7 `close-machinery` — exposed per the §1.3 contract
    from `tools/kata_close.py`); the hook itself (W8).
- **read_first:** DESIGN §1 entire + §2.4 + §2.6 + §6.4; `tools/kata_dispatch.py` live seeds;
  `tools/kata_roles.py:35-46`; `tools/kata_models.py:318`.
- **Acceptance:** per-rung mint refusal tests (each governor × unmet state); atomic-claim race
  test (two claimants, one winner, loser denies); resume-adopts/rotation-mints discrimination
  tests; verdict parser rejects body-embedded fake verdicts; SPAWN/DENY/PHASE lines valid under
  the W2 grammar; declaration renders the three Guardian lines with honest pre-hook values
  (enforcement Dormant).
- **Verify:** `python -m pytest tools/tests/test_kata_dispatch.py tools/tests/test_kata_roles.py -q`.
- **Sizing note:** the largest task in the plan; single-file-centered so a dispatch-time split
  (mint/records vs run_start/capture) is mechanical if `dispatch_budget` demands it — split
  along that line ONLY, keeping `governs` and the parser whole.

### evidence-identity — evidence is credited only for THIS run (BL-X11 + BL-X13 fold in)
- **What it builds:** TM-C2/TM-D5: `evidence_is_current` (`run_result.py:122`) extended to
  **SHA fresh AND runId exact** — fail-closed on every old artifact (kills the
  July-artifact-read-raw class); `RESULT.json` gains `runId`; report filenames carry runId
  (making `observability.md:18` TRUE — the relabel itself is W9's); **BL-X13**: per-gate
  `gates[]` parsed counts or the multi-block honesty flag (per its filing) — no more
  cross-gate chimera tuples; the code side of **BL-X11** (the identity check callable as the
  evaluator's machine-input step; the kata-evaluate contract text pointing at it is W5's).
  The run-membership law travels verbatim (R-H2): ancestor/prior-run artifacts legal as
  *inputs*, never as gate evidence; green-at-fork baseline RESULT recorded as input with
  origin runId (R2-M6).
- **Acceptance:** stale-SHA refused; wrong-runId refused; absent artifact ⇒ refusal not pass
  (anti-vacuity); multi-gate stdout yields per-gate counts (the 4-gate gauntlet fixture from
  BL-X13's filing produces no chimera tuple).
- **Verify:** `python -m pytest tools/tests/test_run_result.py -q`.

**Wave-3 gate:** default-FAIL final eval. From the next wave on, Execution rule 4's dogfood
rule applies: the conductor mints wave-4+ dispatches through the engine.

---

## Wave 4 — Skills migration A: the dispatch spine (3 tasks, one loop pass)

### orchestrate-seam-migration — the ~52 launch sites route through the seam
- **What it builds:** every launch site in `kata-orchestrate/SKILL.md` (~52, per TM-H1)
  rewritten to the seam sequence (mint → launch → capture), with: park semantics on
  refuse-to-mint (`kata-orchestrate:884-885` async-park pattern, TM-B5); the per-task
  **mutation re-run trigger contract** (§3.6: engine re-run with the task's OWN verify
  command; cap N=5; beyond N, sample by the stated deterministic key — sort
  `(file path, line number)` ascending, take first N — **recorded on the cursor, no silent
  truncation**); freeze-minted **arm registry** consumption for tree runs (exactly-once spawn,
  per-arm close policies `cancel|park|abandon-with-rendezvous` — the last MANDATORY across
  BBM-12 wave rollovers); declared fold reducers (undeclared concurrent merge = fail-loud
  refusal); DECISION-as-cursor-record; rider-2 pre-assessed-overlap rule at partition time;
  board→cursor naming in prose; this file's stale anchors fixed here.
- **Acceptance:** a recorded grep shows zero launch sites using the pre-seam bare idiom; every
  dispatch instruction names `mint` and its `governs` rung; the mutation-trigger text quotes
  the sampling key verbatim; validator green.
- **Verify:** `python tools/validate_skills.py` + the recorded greps.

### coordinate-skills-migration — the conductor spine becomes phase-aware; board becomes cursor
- **What it builds:** kata-loop / kata-bootstrap / kata-sprint contracts emit §2.6 PHASE
  events at every stage boundary (in-session skill sequencing is **cursor-tracked, NOT
  dispatch-gated** — TM-B3) and read position from the cursor, never context memory (TM-C5);
  the sprint stop-gate consumes the PERSISTED evaluate VERDICT record with identity check
  (§3.3); kata-worktree carries the pinned-worktree + child-run (arm = run) rules;
  kata-readiness learns the run-marker/seam-init checks; **the board→cursor heritage rename**:
  `skills/coordinate/kata-board` → the cursor skill, `protocol/board.md` → its cursor name,
  with the `REQUIRED_PROTOCOL` key updated in `tools/validate_skills.py` (shared-file
  sequencing table) and every cross-reference migrated.
- **Acceptance:** validator green after the rename (no orphaned registry key, no dangling
  wikilinks); phase-emission contract text cites the seam `phase()` function; sprint stop-gate
  text names the persisted-record requirement.
- **Verify:** `python tools/validate_skills.py`.

### authoring-skills-migration — plan/grill/research skills carry the new authoring duties
- **What it builds:** `kata-plan/RUBRIC.md` + tier skills gain the **per-task `evidence:`
  field method** (TM-F1/R-M9: no plan item freezes without its declaration; the three-form
  grammar cited, never restated divergently); grill skills gain the **convergence-pass record**
  duty (§3.3: proof the Advanced double-pass ran as two distinct dispatches, via seam records)
  and the grill-close status write (`converged` written ONLY by the grill-close act,
  independent of the learn_feed emit); kata-research/kata-advise inbound contracts carry their
  dispatch-gated seam identity (TM-B3) and the brief's inlined-content-as-DATA delimiting
  (§8 S2); kata-defer aligns to `protocol/deferral.md`'s grammar (DEF/ASM forms, approval
  fields).
- **Acceptance:** RUBRIC's evidence-field section round-trips against `evidence_grammar` (the
  examples it shows parse); grill contract quotes the two-distinct-dispatches requirement;
  kata-defer's entry template emits schema-valid DEF entries; validator green.
- **Verify:** `python tools/validate_skills.py`.

**Wave-4 gate:** default-FAIL final eval; dogfood: these dispatches were engine-minted.

---

## Wave 5 — Skills migration B: the judges (1 task, one loop pass)

*A deliberate single-task wave: judge contracts are the judgment-critical surface
(dispatch_class: critical — anchor-model work) and get their own default-FAIL loop pass.*

### judge-contract-rewrites — judges judge ON attested facts, and say VERDICT first
- **What it builds** (TM-E2, R3-M2, R4 residual 4) for kata-evaluate, the three kata-review
  tiers, kata-slop-check, kata-inline-eval: (a) the pinned machine-parseable **first line
  `VERDICT: <enum>`** with the per-judge closed enum table **enumerated in this task** (E4;
  kata-inline-eval's `continue|correct|reroll` is the generalization seed and stays); (b) the
  **attested fact table as required input** — judge ON the facts, never re-derive what an
  engine attested, never accept a worker claim the table contradicts; (c) residual-judgment
  surfaces stated explicitly (quality, design fidelity, threat reasoning); (d) the TM-D3
  tripwire clause (Honor-system-declared until its corpus lands — R-M6); (e) kata-evaluate's
  machine-input step routed through `evidence_is_current` FIRST (the BL-X11 text fix) and the
  grounding-attested mutation record set as its precondition (R-M10); (f) the burn-02
  meta-finding travels with every description, verbatim: *"the judgment+human layers found all
  of these; the automated mechanical gates found none."*
- **Acceptance:** every rewritten contract's first-line spec strict-fullmatch-parses under the
  W3 parser; enum tables closed; fact-table input section present in all six; kata-evaluate
  names `run_result.evidence_is_current` by symbol; validator green.
- **Verify:** `python tools/validate_skills.py` + parser round-trip test additions riding
  `tools/tests/test_kata_dispatch.py` (owned W3 — coordinate via the wave gate, not by
  editing: submit fixture strings, the W3 owner's parametrized test table reads a fixtures
  file if needed — if that fixtures file is created, it lives under this task's fixtures dir).
- **Note:** kata-validate's SKILL.md already carries the tripwire precedent; its anchor fixes
  landed W1. Its contract-alignment edits ride this task's acceptance but its file is owned
  here? — **No:** kata-validate stays owned by W1's anchor task for its anchor lines only;
  its judge-contract alignment is IN SCOPE HERE and the file joins this task's edit set
  sequentially (cross-wave shared-file rule; recorded in the gate record).

**Wave-5 gate:** default-FAIL final eval by a fresh-context judge running under the OLD
contract (the new contracts take effect for consumers the next wave — activation ordering,
never a mid-wave self-referential gate).

---

## Wave 6 — Detectors + judge corpora (3 tasks, one loop pass)

### blocking-detectors — Truth Serum v1's gate-refusing engines (B1, B3, B5)
- **What it builds** (`tools/truth_serum.py`, per the DESIGN §3.1 table — specs transcribed,
  not re-derived): **B1** stub-body AST scan over `graph_gen` tree-sitter spans (the five
  syntactic families; `DEF-*` same-line suppression; explicit mechanical suppressors for
  ABC/protocol-handler/`__init__.py`; residual legitimacy → signal channel, E3); **B3**
  debt-marker-without-`DEF-*` (the D3b rule); **B5** citation-existence resolver
  (`check_wikilinks` precedent; existence MECH, "support" stays judgment). **Every detector
  ships its anti-vacuity companion** (TM-D3): zero-function scan / absent-stale graph
  (`repoHash`) / empty modified-file set / unreadable artifact ⇒ REFUSE to certify, and
  zero-candidate is reported as zero-candidate. B2 (three-way join) is close-machinery's;
  B4 (evidence identity) landed W3; B6 (mutation re-run) is engine+gate work (W1/W7).
- **Standing humility, in every docstring/report string** (TM-D2, verbatim): detectors ATTEST
  and NARROW; judges judge.
- **Acceptance:** each family blocks in a fixture repo; `DEF-*` reference suppresses; each
  companion refuses on its vacuous input; suppressor predicates are explicit code, not judgment.
- **Verify:** `python -m pytest tools/tests/test_truth_serum.py -q`.

### signal-detectors — the SEMI layer that feeds judges, never blocks (S1, S2, S3)
- **What it builds** (`tools/truth_signals.py`): **S1** unwired-symbol detection (graph ref
  edges + tests-path filter + `edge_honesty` import-level), **calibrated on the T6–T11 orphan
  corpus** with the honest limits carried verbatim (call-only edges, bare-name matching,
  fabricated `src` attribution, dynamic imports invisible, out-of-graph entry points look
  dead); **S2** prose-claim narrowing (reuse-claim trigger phrases + adjacent `file:line`
  resolved via B5's resolver; producer-existence guard precedent); **S3** honesty-label
  propagation signal (clause-pin presence; the doc-layer half is EV-1's, W8). Signal outputs
  land in the attested fact table format (consumed by W7 grounding).
- **Acceptance:** T6–T11 corpus fixtures produce the known-orphan findings; each stated limit
  has a test DEMONSTRATING the miss (honest limits are pinned, not just prosed); signals never
  return a blocking verdict type.
- **Verify:** `python -m pytest tools/tests/test_truth_signals.py -q`.

### judge-tripwire-corpora — every judge proves it can still fail
- **What it builds** (TM-D3/R-M6): per-judge known-bad fixture corpora (kata-validate's
  precedent generalized) under each judge's skill dir; `tools/tripwire_check.py` — runs each
  landed corpus against its judge contract shape, proof cadence per-build (CI, riding the
  gauntlet) with the **corpus hash recorded on the cursor**; **corpora activate PER JUDGE as
  they land** — a judge without a corpus is declared Honor-system, never blocked
  (deny-everything dissolved); a judge that cannot demonstrate failure-capability is
  **Dormant, not Verified**.
- **Acceptance:** every judge with a corpus fails its known-bad; activation state per judge is
  a derived, recorded fact; CI wiring green.
- **Verify:** `python -m pytest tools/tests/test_tripwire_check.py -q`.

**Wave-6 gate:** default-FAIL final eval — the first wave whose eval judge runs under the W5
contracts with a live tripwire where its corpus landed.

---

## Wave 7 — Gates, grounding, the close, the doctrine (4 tasks, one loop pass)

### gate-preconditions — every gate refuses without attested facts
- **What it builds** (`tools/gate_preconditions.py` + `gate_emit.py` wiring; the §3.3 map
  transcribed): freeze-gate fact set (DESIGN+PLAN present; governing-ledger record; per-task
  `evidence:` present + grammar-valid; arm registry for tree runs; green-at-fork baseline
  recorded **as INPUT**); per-task gate record (verify re-run + `footprint` lane check +
  **engine mutation re-run record** + B1/B3 passes + B4 identity); wave-gate record (member
  task gates + integration re-gate + judge VERDICTs); final-gate preconditions (RESULT +
  identity + fact table + grounding-attested mutation set + per-gate counts); convergence-pass
  record; sprint stop-gate persisted-verdict check. **Refuse-not-warn everywhere** (locked
  house shape). **Activation ordering is part of the precondition itself:** mutation
  precondition per-platform gated on BL-X14 closure (E8); per-judge tripwire preconditions per
  R-M6; **no gate requires a grill artifact of a run that legally has none** (pass-1
  residual 4 — the never-a-de-facto-mandate law in every fact set).
- **Acceptance:** each gate's refusal fires on its absent-fact fixture; each refusal is a
  reasoned, recorded event (visible-refusal contract, TM-G1's data half); activation tables
  read recorded closure/corpus state, never config assertions.
- **Verify:** `python -m pytest tools/tests/test_gate_preconditions.py -q`.

### grounding-agent — agent proposes, engine attests
- **What it builds:** `skills/evaluate/kata-grounding/SKILL.md` (NEW; roster placement +
  agentDef land via BL-N20 — the skill states this): the tier-2 grounding agent **first in
  the validation stack** at the greater-loop level (~3–5 bounded dispatches per run,
  economy-tiered under D131 — fact-orchestration, not judgment); the signal-trigger table
  (reuse-claim phrase · unattestable DONE · research finding · resolved-but-unread citation);
  AC-10 execute-the-tooling as standing law; scope boundary verbatim (grounding attests FACTS
  pre-judgment; the challenger attacks JUDGMENTS post-hoc); **the stack-head mutation
  attestation** (R-M10: re-runs a sampled subset against the gate command, attests the whole
  record set as the evaluator's precondition). `tools/grounding_gate.py` extends to emit the
  **attested fact table** (detector outputs + grounding verdicts + evidence identity) that
  W5's judge contracts consume.
- **Acceptance:** fact-table schema round-trips; trigger table is closed; the overhead record
  is quoted as modeled-and-labeled (TM-E1 as corrected by R3-H3 — engines are milliseconds
  EXCEPT the mutation re-run); skill passes validator + authored-artifact gate.
- **Verify:** `python tools/validate_skills.py` +
  `python -m pytest tools/tests/test_grounding_gate.py -q`.

### close-machinery — the run ends by proving itself against the frozen plan
- **What it builds** (`tools/kata_close.py`, exposing the §1.3 `close_run` contract):
  **refuses without required records**; the TOTAL three-way join (§5.2: PLAN
  `parse_plan_tasks` ⋈ tree `Kata-Task:` trailers/`footprint` ⋈ DEFERRED.md — every item
  resolves to built-and-exercised / recorded-deferral / **named drift**, behavioral items
  resolving through their declared `evidence:` form, never file-touch heuristics); fail-closed
  close verdicts + the two legal paths (§5.3); **D134 reconciliation stated in code + docstring**
  (trailers AUTHORITATIVE for DONE; the cursor gates only its own fact classes; refusals bind
  per fact class to that class's system of record); the provenance drift check (TM-A2:
  committed `kata.config`/`INTENT.md` vs the cursor's recorded execution; tree semantics =
  committed config + arm registry vs EACH cursor; machine-specific values migrated to
  `.kata-settings.json` via `kata_settings.py`/`kata_config.py`); **redaction at the commit
  act** (RS-M7: extends `learn_feed.redact`'s class table — ONE scrub, two named points:
  branch-close commit act + snapshot-or-push edge); the **first-run consent moment**
  (per-target, remembered machine-local — RS-M6; redaction is not consent, both apply); the
  terminal `run-closed` PHASE record written exactly once; truth metrics feed for the final
  report (§5.1 rider 2 — leftovers always displayed with the run-again option); TM-A1 routing
  (Broken / Dormant-claimed-as-Verified ⇒ NEEDS_WORK-class ⇒ re-loop, operator verbatim: "if
  anything is false or facade it should be another loop pass").
- **Acceptance:** close refuses on absent records / unresolved plan items / drift; a passing
  close emits the verdict artifact + `run-closed`; nothing appends after `run-closed`;
  drift fixture fails close and routes to the two legal paths; secret-class fixture fails the
  commit act; consent prompt fires exactly once per target.
- **Verify:** `python -m pytest tools/tests/test_kata_close.py -q`.

### doctrine-amendment — D173: laws 13 + 15 enter the Determinism Doctrine (conductor-added task)
- **What it builds** (per `.planning/DECISIONS.md` D173, operator-directed 2026-08-16): the
  amendment TEXT for `docs/DETERMINISM-DOCTRINE.md` — **law 13 (recompute, don't shape-check)**
  + **law 15 (scope honesty)**, combined with **the D172 loop-execution scope language** the
  doctrine is already committed to — via the deliberate two-step: ONE advanced grill of the
  amendment text + ONE fingerprint re-approval. Doctrine text is **never-tiered**
  (dispatch_class: critical).
- **Steps (in order, each recorded):**
  0. **The D2-16 probe — recorded HARD PREREQUISITE** (`.planning/INGEST-EXECUTION-ORDER.md:108`):
     verify MC-02's claim that its two appended judgment-boundary clauses *narrow* rather than
     widen the judgment zone. Run and record the probe BEFORE the amendment grill. (The clauses
     themselves are DECLINED by D173 — the probe result informs the grill's boundary review;
     it does not admit them. E5.)
  1. Draft the amendment text: laws 13 + 15 + the D172 scope language. **Preserved constraints,
     verbatim from D173:** core rule verbatim; laws 1–10 never renumbered or dropped; the
     judgment boundary never blurred. **Laws 11/12/14/16 + the two judgment-boundary clauses
     are DECLINED** (batch-reviewed not adversarially grilled, single-corpus, foreign harness,
     no live-run evidence) — the task must NOT include them (E5).
  2. ONE advanced-tier fresh-context grill of the amendment text.
  3. Operator fingerprint re-approval (the two-step; updater prints, never rewrites — human
     moment, Execution rule 6).
  4. Land the text.
- **Acceptance:** doctrine contains laws 13 + 15 + the D172 scope language; laws 1–10
  byte-identical; no trace of 11/12/14/16 or the clauses; grill record + probe record +
  re-approved fingerprint all cited in the task gate record.
- **Verify:** `python tools/validate_skills.py` (the doctrine fingerprint check) + a recorded
  diff showing laws 1–10 untouched.

**Wave-7 gate:** default-FAIL final eval; the close machinery is exercised against THIS wave's
own close as its first live subject (dogfood, Honor-system-declared).

---

## Wave 8 — The LAST switch + the standing regression (2 tasks, one loop pass)

### hook-activation — the fail-closed hook flips LAST
- **What it builds** (only now — TM-H1's binding law: "activated only after every sanctioned
  path is migrated; a hook activated early would deny un-migrated legitimate prose sites, and
  a soft interim mode is the rejected warn-shape"):
  `adapters/claude/hooks/kata-seam-guard.py` — **deny edge** (PreToolUse-class: fail-close any
  `Agent` call lacking a valid record; SEMANTIC re-validation, not existence — stale/hand-copied
  records fail, T-04 stays dead; deliberately breaks the all-hooks-fail-soft precedent,
  `kata-gauge-check.py:34-36`, scope-gated via the run marker) + **Bash leg** (match
  `codex exec` / `kiro-cli chat` dispatch shapes — **best-effort, declared Partially verified,
  never "intercepting"**, R-M7) + **capture edge** (PostToolUse-class: appends VERDICT/DOWN
  mechanically, correlated via the record). Plus: `settings.snippet.json` entry recording the
  **full expected command string + script digest at install** (RS-M10); the pinned source
  FINGERPRINT + live **deny-tripwire** at seam init (RS-H4 — declaration derives from the
  probe result; no-result ⇒ Dormant, never inheriting); internal timeout pinned strictly below
  the host's + payload cap (oversized/timeout ⇒ deny with reason, recorded — RS-M11); run-marker
  scope check in `kata_scope.py` (marker present ⇒ fail closed; absent ⇒ allow; marker-loss
  edge stated, post-hoc lineage audit the residual channel — RS-L5); the hook's exec-safety
  row in `protocol/exec-safety.md` (RS-L4; the mechanical scan-scope extension itself rides
  `ev1-badge-registry`'s validator ownership — coordination noted, preference: extend the scan).
- **Design input:** the W1 `hook-probe.md` results — build to what was OBSERVED.
- **Acceptance:** record-less Agent call denied with the legal-path message; valid-record call
  passes; consumed-record replay denied; deny-tripwire passes and flips the run-start
  declaration to "Verified (intercepting)"; non-kata session (no marker) fully untouched;
  digest mismatch reads as not-Verified.
- **Verify:** `python -m pytest tools/tests/test_seam_guard.py -q` + the registered
  `probe:deny-tripwire`.

### ev1-badge-registry — trust can only be claimed where a machine can re-derive it (EV-1, LOCKED)
- **What it builds:** the committed `tools/badge_registry.json` (`badge-site → check-id`); a
  `validate_skills` check walking BOTH directions on every commit — an uncited Guardian
  "Verified" badge fails; a cited-but-dead check fails (the
  `check_reuse_claims_producers_exist` registry-vs-tree precedent); riding the existing
  gauntlet. Also carries the exec-safety mechanical scan extension to
  `adapters/**/hooks/*.py` (RS-L4 preference; see hook-activation's note). This suite is where
  the T6–T11 facade rows graduate as wiring lands.
- **Acceptance:** both failure directions demonstrated by fixture; the registry's initial
  population covers every Guardian badge currently in the doc layer (grep-enumerated, count
  recorded); gauntlet green.
- **Verify:** `python -m pytest tools/tests/test_badge_registry.py -q` +
  `python tools/validate_skills.py`.

**Wave-8 gate:** default-FAIL final eval **including the live deny-tripwire result** — the
first wave whose enforcement claim is probe-derived, not declared.

---

## Wave 9 — Truth in the labels (1 task, one loop pass)

*Sequenced AFTER hook activation (a declared split of the brief's single last wave): the
relabel must CITE the deny-tripwire and gauntlet results, which only exist post-activation —
a same-wave relabel would grade enforcement from a state it cannot yet cite.*

### guardian-relabel-pass — the FALSE/FACADE rows become honest, with mechanisms cited
- **What it builds** (TM-A1 routing — remediation THROUGH the loop, never out-of-band doc
  edits): every FALSE/FACADE row in
  `.planning/specs/trust-model/evidence/promise-audit.md` relabeled in Guardian terms **with
  the mechanism cited where wiring landed this burn** (evidence pointers to the task gate
  records above; rows whose wiring did NOT land stay honestly labeled and route to their
  backlog homes); `protocol/observability.md:18`'s report-filename row updated to TRUE citing
  W3; backlog **truth-status marks** (§6.6: `FILED · GRILLED · DESIGNED (freeze-candidate) ·
  FROZEN · BUILT—Verified (with cited evidence) · CLOSED`) applied across `.planning/BACKLOG.md`
  — **"BUILT" is legal ONLY with the Verified evidence citation**; the §10 closes recorded:
  BL-M33, BL-M34, BL-N01 (v1 scope), BL-N19's mechanical route, BL-X11, BL-X13, BL-X14,
  BL-X15, BL-X12 — each with its citation; the heavy cross-documentation commitment (TM-C7,
  committed d785370) checked leg-by-leg — **any unmet leg surfaces at handoff, never silently**.
- **Acceptance:** zero uncited "BUILT"/"Verified" claims (the W8 EV-1 check enforces this
  mechanically — this task must leave the validator green); every relabel's citation resolves
  (B5 detector run over the touched files); unwired rows still carry their honest grade.
- **Verify:** `python tools/validate_skills.py` +
  `python -m pytest tools/tests/test_badge_registry.py -q`.

**Wave-9 gate:** default-FAIL final eval, then the program-level close: `close_run` over the
burn's own parent cursor — the close machinery grounding the run that built it
(Honor-system-declared where the conductor invoked capture legs by hand).

---

## Honest sizing

9 waves = 9 BBM-12 loop iterations; 28 tasks (7/5/2/3/1/3/4/2/1 per wave). Largest tasks:
`seam-engine` (W3) and `orchestrate-seam-migration` (W4) — both deliberately single-file-
centered so any dispatch-time split forced by `kata_gauge.dispatch_budget` is mechanical.
Wave 5 is a deliberate single-task anchor-model wave. Worker-brief budgets bind at dispatch
(CA-L9/CA-L11), not here.

## Deviations from the DESIGN / brief (PD-1/PD-2 — complete list, also returned to the conductor)

1. **`class:` vs the brief:** the brief asked for `class: critical/coding/economy`; RUBRIC's
   freeze gate fails unknown `class:` values, so `class:` keeps the RUBRIC enum and the D59
   tier map lands as the added `dispatch_class:` frontmatter map. Both are per-task and
   authoritative for their own consumers.
2. **The brief's "wave 1" is split into waves 1–3** (fixes/contracts → cursor → seam): the
   seam authors cursor lines, so it cannot build concurrently with the grammar it writes.
   Dependency honesty, not scope change; the DESIGN's own order (§7: "engine + cursor first")
   is preserved as a stage.
3. **The brief's single last wave is split into waves 8–9:** the Guardian relabel must cite
   post-activation probe results (deny-tripwire, gauntlet) that do not exist until the hook
   wave's gate passes.
4. **`exec-safety-registration` is a wave-1 task, not literally pre-build** (DESIGN RS-H1 says
   "BEFORE build"): it lands in the first loop pass, strictly before any grammar consumer.
   The conductor may lift it into the freeze package unchanged — surfaced at the freeze gate.
5. **`hook-capability-probe` added to wave 1** — not in the brief's wave-1 list, but
   DESIGN TM-B2.1 mandates it as "an explicit early task"; omitting it would be a silent
   deferral.
6. **The mutation sink's argv re-domaining (pass-2 medium 3) rides `fix-mutation-prover`**,
   not the evidence-grammar task, to keep `tools/mutation_run.py` single-owner; the grammar
   reuse is via the live `_guard_node_id` precedents, per §3.5's own citation.
7. **BL-X15's test path corrected:** the backlog cites `tests/test_statusline_chain.py`; the
   file lives at `tools/tests/test_statusline_chain.py` (glob-verified) — the evidence
   declaration uses the real path.
8. **BL-X14's CI-green evidence is a committed evidence-note artifact** — a CI run has no form
   in the closed evidence grammar; the note records run URL + SHA (declared, not smuggled).
9. **`doctrine-amendment` (D173) added to wave 7** per the conductor's mid-dispatch addition —
   not in the original brief or DESIGN §12; anchored to `.planning/DECISIONS.md` D173 and the
   D2-16 probe prerequisite.
10. **kata-validate's SKILL.md** takes anchor fixes in W1 and judge-contract alignment in W5
    (cross-wave shared file, recorded) — the alternative (one task spanning two waves' duties)
    would have coupled an economy fix to a critical rewrite.
11. **Stale-anchor scope:** the ledger says "five skills"; grep finds six non-orchestrate
    citing files (+ kata-orchestrate, fixed in its own W4 rewrite). The plan fixes all six in
    W1 — over-inclusion declared rather than guessing which five the ledger meant.
13. **Recorded amendment G1 (conductor, 2026-08-16, post-freeze — wave-1 escalation
    outcome):** `fix-learn-feed-truth` is **CLOSED-AS-ALREADY-SATISFIED** — BL-X12 was fixed
    at `2a1b1cf` (2026-08-16 12:40, an ancestor of the burn base; conductor-gated CLOSED per
    `.planning/specs/backlog-burn-02/OBSERVATIONS.md:84`), four hours BEFORE this plan froze;
    the frozen plan scheduled work already done because the backlog's 🔴 marker was never
    written back (the writeback-gap discovery, filed in `OBSERVATIONS.md`). The E1 fork was
    already ruled as a shipped hybrid (route refusal + ledger-parser status vocabulary).
    Evidence declaration amended from the planned NEW test node (never needed) to the live
    equivalent pinning test (`test_real_ux_ledger_open_question_is_not_a_decision` — the
    challenger's live case); conductor re-ran the full gate: 105/105 pass. No phase B built.
12. **Freeze-gate folds (conductor-applied at the six-row gate, 2026-08-16 — recorded in
    `GATE-PLAN.md`):** four `ownership:` additions reconciling the frontmatter map with this
    plan's own Shared-file sequencing table (the body declared the touches; the authoritative
    map omitted them and would have tripped lane checks as false drift):
    `coordinate-skills-migration` + `tools/validate_skills.py` (key rename) ·
    `close-machinery` + `tools/learn_feed.py` + its test (redaction extension, RS-M7) ·
    `hook-activation` + `protocol/exec-safety.md` (sink row, RS-L4) ·
    `ev1-badge-registry` + `tools/validate_skills.py` (EV-1 check + scan-scope) ·
    `doctrine-amendment` + conditional `tools/validate_skills.py` (fingerprint pin,
    verify-at-task-start). All additions preserve within-wave disjoint ownership. No task,
    wave, dependency, or evidence content changed.
