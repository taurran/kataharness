# Context-Autonomy grill — decision ledger (running)

> kata-grill-standard, opened 2026-07-04. Moves to .planning/specs/context-autonomy/ when the branch opens.
> Checkpoint discipline: append after EVERY resolved branch, before posing the next question.

## Pre-locked by operator (this session, before grill)
- OP-1: No PokeVault/MindBridge deploy this session.
- OP-2: Fable stays in tiering matrix behind a once-per-run approval gate collected at bootstrap;
  decline ⇒ those slots go to Opus; prominent cost disclaimer. Motivation: avoid post-July-7 charges.
- OP-3: Internal kata threshold is the PRIMARY mechanism; host autoCompactWindow is backstop only,
  set (with permission) above the target or not at all if default suffices. Gap telemetry-derived,
  10% fallback. Never write user settings silently.
- OP-4: Preflight approval bundle: installs/downloads + permission allowlist + Fable gate +
  compact-window recommendation, collected ONCE pre-run; zero expected prompts for 8 hours after.
- OP-5: Bootstrap force-executes first run after install; persists settings to YAML/JSON.
- OP-6: Cross-platform scope: Kiro, Codex CLI, Copilot, Cursor, Gemini CLI (Windsurf cut).
- OP-7: Main-session context management is the priority item of v0.2.1.
- OP-8: 8-hour walk-away unattended run is the acceptance scenario.

## Self-resolved from docs/code (Phase 0.3 — cite, don't ask)
- SR-1: Prime-frame primitive EXISTS (config.md §Prime-frame sizing, D83): ≈0.40 of advertised window
  (restart ceiling ≈0.48), adapter-resolved to tokens, explicitly named as the one-shot
  self-handoff/refresh threshold source (B1). The initiative wires a gauge to an existing policy —
  kata-selfhandoff SKILL.md L30-45 already says "trigger at the model-resolved prime-frame fraction,
  task-boundary preferred, generous-not-timid, durable-first." No new threshold concept needed.
- SR-2: Delivery axis EXISTS (config.md §Delivery axis, D78): delivery.boundary
  "auto-continue-while-green" is the walk-away cadence; preflight strictness can key off it.
- SR-3: preflight config block EXISTS (D29) with reserved approval_mode field — the approval bundle
  has a designed home; extension is additive.
- SR-4: models block anchor semantics (config.md §models, R7): zero-step critical work inherits by
  omission (never names a model) — therefore a config-only Fable gate CANNOT stop a Fable session
  from burning Fable on critical work; the session model itself is the operator's choice. Gate design
  must account for this (→ Q3).
- SR-5: Gauge grounding (grounding-claude-code.md): autoCompactWindow = ceiling-in-tokens semantics;
  settings.json key preferred over env var; auto-compact can be DISABLED (preflight must check);
  SessionStart compact matcher + additionalContext confirmed; statusline bridge schema confirmed;
  headless statusline freshness UNVERIFIED ⇒ staleness check + deterministic fallback mandatory.
- SR-6: Cross-platform (cross-platform-compaction-research.md): 3 of 5 platforms have NO host knob ⇒
  internal-threshold-primary is the only portable architecture; per-platform degradation matrix drafted.
- SR-7: kata.graph.json cache exists (.kata/) — version-up grounding available per RUBRIC Phase 0.4.
- SR-8: SMOKE findings feed riders: F1 verdict-tier variance (calibration note), F2 index-continuity
  dispatch-base sentence, F5 HANDOFF §7 stale expectation, installer shared-base-dir gap
  (kata-grill/RUBRIC.md absent from ~/.claude/skills — REAL install defect, cause TBD via digest).

## DECISION TREE (dependency-ordered; ⏳ = awaiting grounding digest, Q = operator question)
CA-1 Gauge: 1a source priority + chain-never-clobber (locked shape; mechanics ⏳ hook/installer digest)
  · 1b staleness threshold (default TBD) · 1c THRESHOLD POLICY (→ Q1) · 1d N-waves fallback default
  · 1e small-frame absent-gauge ⇒ mandatory rotation (locked)
CA-2 Self-handoff wiring: 2a boundary placement (locked: wave/frontier recompute) · 2b never mid-task
  (existing) · 2c post-handoff behavior (→ Q2)
CA-3 Host reset: 3a settings.json recommendation formula (locked shape; formula = target+gap) ·
  3b autoCompactEnabled preflight check (new, locked) · 3c recommend-never-write (locked) ·
  3d PreCompact hook extension, observe-only posture (⏳ current hook)
CA-4 Re-orientation: 4a SessionStart(compact) hook + newest-handoff location (⏳ handoff artifact
  conventions) · 4b AGENTS.md standing line (locked)
CA-5 Report budgets: 5a artifact location + size contracts (→ Q4) · 5b narration economy prose
CA-6 Preflight bundle: 6a BLOCK/WARN posture per item (→ Q5, keyed to walk-away intent?) ·
  6b allowlist-coverage check depth (anti-cathedral guard — keep simple)
CA-7 Fable gate: 7a decline semantics + run-type defaults (→ Q3) · 7b disclaimer text (docs pass)
CA-8 Bootstrap: 8a force-run detection + settings split user-level vs per-branch (⏳ bootstrap digest,
  then confirm with operator) · 8b re-entrant unchanged
CA-9 Adapter contract: 9a session-respawn + gauge primitives placement (⏳ contract digest) ·
  9b per-platform recommended-config docs (locked deliverable)
CA-10 Telemetry: 10a parent-tokens/phase columns (additive schema) · 10b observability orientation
  doc placement (lean: protocol/, self-resolve unless operator objects)
CA-11 Prose/install riders: F1, F2, F5, installer base-dir fix (⏳ cause)
CA-12 Acceptance: live proof cycle + SMOKE-2/3 rerun A/B + degradation-path tests (freeze at DESIGN)

## Self-resolved from grounding digest (grill-grounding-digest.md, cites within)
- SR-9: Handoff artifact = `.planning/HANDOFF.md` per protocol/handoff.md (NOT the brief's
  "SELFHANDOFF.md" — brief corrected). Boundary handoff supersedes coincident self-handoff (T1).
  SessionStart(compact) hook points at HANDOFF.md; orientation tiers consume it 1:1.
- SR-10: PreCompact hook EXISTS (adapters/claude/hooks/kata-precompact.py): board snapshot to
  refs/kata/trail + custom_instructions nudge; never raises. L3 extension = additive (also surface
  HANDOFF.md existence/freshness). README carries an UNVERIFIED assumption (sync time budget) —
  live-proof item.
- SR-11: kata ALREADY ships a statusline (adapters/claude/statusline.py + settings.snippet.json,
  refreshInterval:1, with a note that Claude's statusline is event-driven and goes quiet during
  background subagent work — gauge staleness independently confirmed). CLOBBER HAZARD IS REAL AND
  IS OURS: naively merging kata's snippet replaces a user's existing statusLine (e.g. operator's
  gsd-statusline.js). Chain-or-skip detection is mandatory (CA-1a sharpened).
- SR-12: Installer gap ROOT CAUSE: iter_skill_dirs() returns only dirs directly containing SKILL.md;
  shared tier-family base dirs (kata-grill/ etc. holding RUBRIC.md + resources/) are never linked;
  Windows copy-fallback installs dangle the ../kata-grill/RUBRIC.md relative reference. Likely also
  kata-plan/kata-review/kata-diagnose families. CA-11 fix scoped; MUST first enumerate the "5 frozen
  engine fns" (referenced by count 4x, never named — pin the list in DESIGN before touching installer).
- SR-13: "Increment-A precedent" phrase doesn't exist in-repo → maps to D104 install-portability
  pattern (Adapter Claude-only, mirrors _flat_link_skills, frozen engine fns byte-unchanged).
- SR-14: Adapter contract has primitives (a) board-append, (b) kill+fresh-dispatch only.
  Session-respawn = new primitive (c); touches named-DEFERRED LD7 (host-fallback × attempt topology)
  — scope carefully, don't silently absorb LD7.
- SR-15: Fable gate attaches at Layer 3 (anchor resolution — kata-bootstrap/kata-initiate write
  models.anchor once per branch); NO proactive model-approval concept exists today (only reactive R2
  fallback-after-failure). Net-new control, additive.
- SR-16: Bootstrap has NO first-run/force gating today — CA-8 is greenfield; bootstrap Phase 0
  (kata-readiness) is the natural attach point. Preflight engine (kata_preflight.py) is
  default-FAIL, covers dependency installs only; approval-bundle extension is additive alongside
  reserved approval_mode field.
- SR-17: kata.graph.json top ranks are vendored research/** noise — blast-radius use requires a
  path-prefix filter; top core modules = gate_emit/run_result/mutation_check (not in this
  initiative's expected blast radius).

## Resolved branches (append-only below)

### R-1 (CA-1c) Threshold policy — RESOLVED 2026-07-04
Operator: 70% default, "fine no matter how much it really is," surfaced as a configurable
recommendation at configuration; default stands. Reconciled with D83 (frozen: quality degrades ≈40%
into a 1M advertised window — flat 70%-of-raw would sit deep in the degradation zone) by defining:
**trigger = 0.70 × prime frame**, where prime-frame tokens = min(actual session window, D83 TUNABLE
fraction × advertised window). On a 200k session that IS 70% of the session (operator's number,
exactly); on a genuine 1M session it lands ~280–340k — inside the reliable band. One rule, no
special cases, reuses the existing D83 primitive, 0.70 bootstrap-configurable. Rejected: flat 70%
of raw window (contradicts D83 on big frames); lower default 60% (violates D8 generous-not-timid).
PENDING OPERATOR VETO — stated as recorded resolution, invited objection.

### R-2 (CA-2c) Post-handoff behavior — RESOLVED
Option (a): keep working, refresh handoff at every subsequent boundary until reset. Operator
addendum = acceptance criteria: resume must reload FULL context quality (kata-orient 3-tier,
budget-capped per protocol/orientation.md), seamless, no hangs, no quality degradation. → CA-12
acceptance: post-compact resume graded on context-quality restoration, not just task continuity.

### R-3 (CA-7a) Fable gate — RESOLVED core + NEW above-anchor concept; one sub-Q open
Option A confirmed (decline ⇒ pin anchor opus + hard-stop advising /model switch — the only honest
decline). Anchor-IS-fable case: confirm keep-using + warn "long-running loops on Fable as primary
FM can drive costs up significantly." NEW (operator): post-July-7, anchor=opus + mode=advanced ⇒
kata may OFFER anchor+1 (Fable) at PREFLIGHT approval, user knowingly accruing Fable API usage.
This adds above-anchor arithmetic to the tiering table (currently ceiling=anchor everywhere;
net-new, additive, approval-gated, never silent). R2 fallback unchanged (failed fable dispatch
steps down, never re-offers). OPEN sub-Q: does +1 apply to critical/judgment work only
(recommended) or also coding? Operator wrote "+1 +1" — ambiguous, needs one clarification.

### R-4 (statusline discovery) — NO OPERATOR ACTION; design mandate stands
Operator's own statusline works and stays untouched. The hazard was kata's settings.snippet.json
replacing a user's statusLine if applied naively — chain-or-skip detection is LOCKED into CA-1a
(kata never clobbers; if a statusline exists, recommend a chaining wrapper or skip to bridge-file/
fallback legs).

### R-5 (CA-11) Installer fix — ACCEPTED
Fix shared-base-dir install gap; enumerate + freeze the "5 frozen engine fns" list in DESIGN first.

### R-6 (NEW — handoff taxonomy) Operator-requested assessment: "clean handoff management for
manual, self, and agent↔orchestrator handoffs — assess what needs clarifying." Assessment below.

### R-7 (CA-1c FINAL) Per-role thresholds + the "smart zone" — RESOLVED (supersedes R-1's clamp)
Operator REJECTS the 0.40 band as a conductor clamp: degradation is two-sided — too little context
produces poorly-grounded output; too much produces rot. The operating target is the SMART ZONE
(glossary term): above the context floor (kata-orient 3-tier load complete), below the rot ceiling.
RESOLUTION: per-ROLE trigger fractions of the EFFECTIVE session window (= min(actual, advertised)):
**conductor 0.70 · subagent budget 0.50** — both TUNABLE, surfaced as bootstrap recommendations,
defaults as stated. D83's 0.40 fraction is NOT edited (supersede-never-rewrite): it remains the
sprint-sizing fraction; the NEW per-role trigger fractions are the context-autonomy policy and the
DESIGN records the B1 amendment + operator rationale. Note for 1M frames recorded (one config key
away if operator ever wants lower).
MECHANICAL HONESTY (subagent leg): workers have NO live gauge (no statusline; usage visible to the
conductor via task stats, not to the worker). The 0.50 is therefore (i) a PLAN-TIME sizing budget —
expected task burn ≤ 0.50 × worker frame (composes with existing chunk-unit sizing), and (ii) a
dispatch-brief rule — "if running long, checkpoint-commit and return with a continuation report"
(M4 checkpoints make worker death/rotation cheap). Two mechanisms, one principle; the DESIGN must
say so explicitly rather than pretend workers self-gauge.

### R-8 (CA-2c reinforced) Balance mandate — RESOLVED
Early-exit is a risk equal to rot ("forcing an exit too soon when the session is just getting
running"). Trigger policy stays generous-not-timid; the acceptance tests must include a NO-FIRE
case (session under threshold ⇒ no handoff churn).

### R-9 (CA-7a FINAL) +1 scope — RESOLVED
Approved Fable offer elevates the first two work classes: CRITICAL (planning/judgment/gates) AND
CODING. Economy/low-criticality NEVER runs Fable, even in advanced with approval. Confirmed verbatim.

### R-10 (CA-5a FINAL) Report artifacts — RESOLVED core; home recommendation pending veto
Names: descriptive + unique, tied to run/task/agent: `.kata/reports/<runId>-<taskId>-<agent>-<kind>.md`.
HOME (operator asked to determine): RECOMMEND project-local gitignored `.kata/reports/` — run- and
target-scoped, readable by every dispatched agent via repo paths, consistent with board.md's home,
survives multi-project installs (a harness-install-dir home would collide across projects and be
invisible to off-host/ACP agents). Durable-citation rule from item 5 unchanged: anything a DECISION
cites must live in committed artifacts. PENDING OPERATOR VETO.

### R-11 (NEW OP-9) Auto-context default ON — RESOLVED (operator-directed)
"Default to auto-context rotation." One-shots: assumed ON, not optional. Sprint/incremental (and
individual-feature/bug-fix shapes): ON by default with an explicit opt-out. BC NOTE (freeze-gate
must attack): this is a deliberate default-ON feature — a departure from the M4-style absent⇒off
convention, justified because the selfhandoff PROSE always mandated the trigger (it was never
wired); degradation stays graceful (no gauge/hooks ⇒ deterministic rotation, never "assume infinite
context"). Config key + delivery-shape-aware opt-out to be shaped at DESIGN.

### R-12 (CA-6a) Preflight strictness — RECORDED PENDING VETO (asked twice, unanswered)
Intent-keyed: walk-away-configured run (auto-continue boundary or unattended flag) + a missing leg
that would STRAND it (auto-compact disabled AND no gauge AND no respawn path ⇒ session death at
hard limit with no recovery) = BLOCK at preflight. Attended runs: WARN + proceed. Freeze-gate attacks.

### Self-resolved defaults (TUNABLE, freeze-gate attacks numbers)
- Gauge staleness: bridge timestamp older than 300s ⇒ stale ⇒ deterministic fallback leg.
- N-wave fallback: N = max(1, floor(trigger_tokens ÷ est_wave_burn)), est_wave_burn default 40k
  tokens until parent-telemetry rows exist (SMOKE-3 seeded n=1).
- Worker soft budget line in every dispatch brief (checkpoint + return, never mid-chunk death).

### R-13 (supersedes R-7's subagent leg) DERIVED subagent threshold — RESOLVED (operator-directed)
Subagent rotation point is DERIVED, never user-configured: **threshold = startup load + 40pp
processing quantum** (start 5% ⇒ rotate at 45%; start 20% ⇒ 60%). Invariant: every dispatch gets
≥40% of the worker window for actual processing. Assessment (recorded): elegant — it bounds the
WORK-PER-DISPATCH quantum uniformly regardless of brief size, making checkpoint/continuation
granularity predictable; two guards added: (i) HARD CAP total at 0.80 of worker window (a fat brief
never pushes rotation into the rot zone); (ii) dispatch-time over-briefing WARN when startup load
> 0.30 (symptom of report-budget violations — surface, don't block). All numbers TUNABLE.
CONFIG SURFACE SHRINKS: no subagent threshold key. Conductor threshold keeps ONE key, default 0.70,
shown in bootstrap's advanced drawer, never interactively asked (K5: no new dial). Mechanics stay
honest per R-7: conductor estimates startup load at dispatch (it authored the brief); worker gets
the numeric budget IN the brief ("checkpoint and return with a continuation report as you approach
~N% / ~X tokens of activity"); checkpoints keep overrun cheap. Workers still have no live gauge —
stated in DESIGN.

### R-14..R-21 — Convergence-gate HOLD branches folded (gate v1, 8 findings)
- R-14 (gate#1 reset ownership): host compaction is the SOLE reset mechanism on Claude (no
  programmatic /compact exists). Framing corrected: kata owns the SCHEDULE + DURABILITY (threshold,
  handoff freshness, recommended backstop placement); the host owns the MECHANISM. selfhandoff
  prose "compact/reset" step = the host act, arriving on kata's recommended schedule. Platforms
  with respawn primitive (c): rotation = kata-initiated respawn. No conductor self-compaction leg.
- R-15 (gate#2 denominator): trigger denominator = HOST-REPORTED effective window
  (context_window.total_tokens from the gauge, post-cap). A capped session's real frame IS the cap.
  Gauge absent ⇒ fallback rotation (no denominator needed).
- R-16 (gate#3 +1 mechanism): new config key `models.premium: {offer:"fable", approved:bool,
  scope:["critical","coding"]}` written by bootstrap after the gate. resolve() amendment: premium
  approved + work-class ∈ scope + premium rung exists above anchor ⇒ return EXPLICIT premium id
  (inherit would give the session model — explicit is mandatory). This amends the FROZEN
  model-tiering invariant ("explicit ids only strictly-below-anchor") ⇒ delivered as a GATED
  AMENDMENT to that spec: "explicit ids for non-anchor rungs; above-anchor only under recorded
  premium approval." R2 fallback unchanged (failed premium dispatch steps down, never re-offers).
- R-17 (gate#4 gate home): the Fable gate is collected in the PREFLIGHT phase of bootstrap's launch
  sequence (bootstrap orchestrates; preflight collects — matches operator "at the approval (in the
  preflight)"). Authoritative record for dispatch = kata.config `models.premium.approved` (resolver
  reads config); `.kata/preflight.json` carries the audit event. Once-per-run = once per kata.config.
- R-18 (gate#5 default-ON semantics): WRITE-TIME default — v0.2.1 bootstrap writes the key
  explicitly ON for new configs; ABSENT-at-load ⇒ OFF (D25/BC1 preserved; no retroactive activation
  of pre-v0.2.1 configs mid-flight). Operator default-ON intent satisfied going forward.
- R-19 (gate#6 worker budget enforcement): superseded by R-13's derived formula. Enforcement =
  advisory-plus-estimator: freeze-time WARN (never hard-fail) when estimated task burn > the 40pp
  quantum, estimator = TUNABLE tokens-per-chunk seeded from ledger perTask medians; the brief rule
  is mandatory prose. D136 posture: the estimate drives a WARN + split suggestion, not a decision —
  fail-soft acceptable, splitting stays planner judgment.
- R-20 (gate#7 staleness N): STRICT — any board DONE/DECISION line newer than the HANDOFF.md commit
  demotes the handoff from sole-anchor to context-input; kata-orient 3-tier rebuild becomes
  authoritative. (N=1 semantics; no tunable.)
- R-21 (gate#8 backstop formula): gap = max(worst observed boundary burn + handoff write cost,
  0.10 × effective window) — 10% OF THE WINDOW, not of target. Recommended autoCompactWindow =
  clamp(target_tokens + gap, 100k key floor, model max). target+gap ≥ model max ⇒ recommend
  nothing (default suffices). target+gap < 100k ⇒ recommend the 100k floor + note rotation covers
  the remainder. Telemetry replaces the fallback constants as rows accumulate.

### R-22..R-27 — Convergence re-gate v2 HOLD branches folded (gate v2, 6 findings)
- R-22 (v2#1 premium mode-guard): resolve()'s premium branch REQUIRES mode=="advanced" at
  resolve-time (a fourth conjunct: approved ∧ class∈scope ∧ rung-above-anchor-exists ∧
  mode==advanced). The approval RECORD carries the mode it was granted under; a re-entrant run that
  changes mode LAPSES the approval (re-ask at next preflight). Closes the silent standard-mode
  +2-rung cost blowout.
- R-23 (v2#2 one-shot unconditional): delivery.shape one-shot ⇒ rotation UNCONDITIONAL (key not
  consulted; operator "assumed ON, not optional"). The contextAutonomy key governs incremental
  shapes only. Re-entrant bootstrap (same-as-last from a pre-v0.2.1 config) writes the key at next
  touch per its write-all-fields-by-construction Phase 3, surfaced in the composition summary.
- R-24 (v2#3 bridge superset): kata's CHAINED wrapper writes the superset schema
  {session_id, remaining_percentage, used_pct, timestamp, total_tokens} — it receives the same
  statusline stdin, so total_tokens is free; additive/BC with the gsd schema. Degrade (only an
  unchained pre-existing bridge, no total_tokens): trigger runs percentage-only (0.70 by %);
  backstop-recommendation tokens fall back to the advertised window as an ESTIMATE with an explicit
  approximation flag in the recommendation text. Never silent.
- R-25 (v2#4 premium fallback terminus): failed premium dispatch ⇒ immediate OMIT/inherit at the
  anchor rung. Never an explicit anchor id (preserves the amended invariant "explicit ids for
  non-anchor rungs only"; tracks mid-run /model switches). One-step chain: premium → OMIT.
- R-26 (v2#5 startup-load boundary + cap-vs-invariant, enriched by operator check-me): startup
  load = the conductor-AUTHORED dispatch payload only (brief + packed orientation attachments);
  worker-side read-ins count toward the worker's own budget consumption, never startup. CAP WINS:
  startup > 0.40 makes the 40pp invariant unsatisfiable ⇒ that dispatch is OVER-BRIEFED and gets
  caught at plan/freeze time (split the task or slim the brief — a mandate, not a WARN); the 0.30
  WARN stays as the early-smell threshold. RUNTIME SEMANTICS (operator-directed, this round): the
  quantum is a plan-time sizing target — the well-planned case NEVER rotates; at runtime it is a
  soft budget with completion-awareness: at budget ⇒ finish current chunk + checkpoint ⇒ if
  remaining estimate fits under the 0.80 hard cap, CONTINUE to completion (no rotation to do 10%
  of a task); else return with a continuation report. Continuations reuse the existing
  kill+fresh-dispatch primitive anchored at the last checkpoint (no new machinery); green-path
  inter-part evaluation is checkpoint-trailer scoring (zero LLM calls). Rationale recorded:
  worker tokens are the cheap/parallel resource, conductor context is the run-fatal one —
  rotation is a designed exception with bounded cost, not a cadence.
- R-27 (v2#6 staleness comparator): board lines are ISO-8601-UTC-stamped by protocol/board.md line
  format (L9, verified). Comparator = newest board DONE/DECISION line timestamp vs HANDOFF.md's
  git commit timestamp; any newer board line demotes the handoff to context-input. Trail-ref
  independent; no reliance on @sha presence.

### R-28..R-35 — Convergence re-gate v3 HOLD branches folded (gate v3, 8 findings)
- R-28 (v3#1 opt-out scope + key): operator's "individual feature deployment/individual bug fix"
  was a PARENTHETICAL EXAMPLE of sprint-based processing, not runShape individual. Pin: opt-out
  keys off **delivery.shape** — one-shot ⇒ unconditional ON (key not consulted); incremental ⇒ key
  consulted. Key = `contextAutonomy: "on"|"off"` (string, matching securityScan-style conventions);
  absent-at-load ⇒ OFF (BC); bootstrap Phase 3 writes "on".
- R-29 (v3#2 mid-roadmap resume): NO mid-roadmap auto-write (D25/BC1 — never change behavior
  mid-flight). Honest posture: sprint boundaries ALREADY rotate by design (the boundary handoff),
  so a pre-v0.2.1 incremental run is not stranded — only intra-sprint refresh is absent. kata-
  readiness (runs at every bootstrap entry incl. Phase 0b routing) gains a WARN: "pre-v0.2.1
  config lacks contextAutonomy — written at next composition (Phase 3) or opt in by config edit."
  Surfaced, never silent, no retroactive flip.
- R-30 (v3#3 premium 401/403): for the PREMIUM rung only, 401/403 ⇒ premium-unavailable: OMIT-
  inherit + LOUD surface (board DECISION + ledger degraded {scope:"premium", reason:"auth-40x"} +
  handoff note) + approval marked LAPSED for the remainder of the run (no retry storm). Rationale:
  R2's raise-on-auth protects baseline dispatch (misconfig = stop); premium is an OPTIONAL
  elevation whose failure has a semantically-correct safe fallback (the anchor — the exact
  no-approval behavior). Unattended survival wins; never silent. Delivered inside the same gated
  tiering-spec amendment as R-16 (the frozen R2 text is amended, not contradicted).
- R-31 (v3#4 continuation locus): pin all four — (i) the BRIEF embeds the numbers (budget tokens,
  cap tokens, estimator basis); (ii) the continue/return rule is re-evaluated at EVERY checkpoint;
  (iii) the estimate is worker-local from brief-embedded numbers + own activity (approximate,
  stated as such in the brief); (iv) estimated activity ≥ cap ⇒ return UNCONDITIONALLY with a
  continuation report. Enforcement honesty: worker-side = compliance (M1-L3: soundness never rests
  on it); the TRUE enforcement is conductor-side — existing liveness machinery + the M4 kill
  primitive terminate a worker that plows on. Both stated in DESIGN.
- R-32 (v3#5 bridge identity): TWO files, zero contention. Kata's chained wrapper writes its OWN
  sibling `%TEMP%/kata-ctx-<session_id>.json` (superset schema, atomic temp+rename); the user's
  script keeps writing its own file untouched (chain = exec child, pass stdin through, never
  modify its output or its file). Reader priority: (1) kata bridge, (2) user bridge (4-field,
  %-only triggering), (3) deterministic fallback.
- R-33 (v3#6 settings split — WAS ⏳ CA-8a; operator-flagged, pinned PENDING VETO): user/install-
  level home = **`~/.kata/settings.json`** (JSON; sibling of the existing ~/.kata/installed-
  registry.json D-registry precedent). Keys: `firstRunCompletedAt` (the force-run marker — absent
  ⇒ bootstrap force-executes), `hostPosture` {autoCompactChecked, recommendedWindowTokens,
  bridgeMode: chained|user-only|none}, acceptedDefaults. Everything RUN-scoped stays in per-branch
  kata.config (contextAutonomy, models.premium incl. grantedMode, trigger-fraction override).
  Target-repo .kata-settings.json unchanged (telemetryLedger, confirmedPlatforms — repo-scoped).
- R-34 (v3#7 grantedMode): `models.premium` schema = {offer, approved, scope, grantedMode}.
  kata.config authoritative (survives clone); .kata/preflight.json audit-only. Lapse executor =
  BOOTSTRAP: re-entrant Phase 0/1 detecting mode ≠ grantedMode clears approved and the next
  preflight re-asks.
- R-35 (v3#8 primitive (c) scope): IN v0.2.1, contract-conformance only (per initiative brief).
  Contract paragraph: "(c) session-respawn — the platform's OUTER SHELL (host feature, cron
  wrapper, or human; never the in-session agent) can end the conductor session and start a fresh
  one that re-anchors from the newest durable handoff (SessionStart-equivalent injection or a
  documented manual step). Absent ⇒ degradation: conductor writes/refreshes the handoff and
  PROMPTS THE OPERATOR to rotate (universal fallback); unattended runs on such platforms are
  bounded by one session window, surfaced at preflight. Governs CONDUCTOR sessions only — worker
  attempt topology is out of scope; LD7 remains named-DEFERRED." Claude binding = the only live
  leg in v0.2.1.
- R-27 addendum (gate v3 re-derivation caution, adopted): staleness comparator uses strict `>`;
  same-second ties favor the handoff.

### R-36..R-40 — Convergence re-gate v4 HOLD branches folded (gate v4, 5 findings)
- R-36 (v4#1 — CORRECTS R-33; gate caught a FALSE PREMISE): `.kata-settings.json` is the
  HARNESS-HOME central-install settings file (tools/kata_settings.py:16, docs/SETUP.md:90) — my
  "target-repo-scoped" claim was wrong, and IP-A (install-portability grill ledger, LOCKED
  2026-06-26) explicitly DROPPED a ~/.kata/ machine-layer settings file as over-engineered.
  CORRECTED PIN: extend the EXISTING `.kata-settings.json` (existing read/write/merge machinery)
  with `firstRunCompletedAt`, `hostPosture` {autoCompactChecked, recommendedWindowTokens,
  bridgeMode}, `acceptedDefaults`. NO new file; IP-A stands. Semantics unchanged: per-install,
  not per-project.
- R-37 (v4#2 BC seam): absent-at-load ⇒ OFF applies ONLY where the key is consulted (incremental
  shapes). One-shot configs — INCLUDING pre-v0.2.1 ones — rotate unconditionally (operator OP-9:
  "assumed ON, not optional"). This is a deliberate, recorded BC departure for old one-shot
  configs: the added behavior is protective, additive, and was ALWAYS mandated by the selfhandoff
  prose (just never wired); D-record will state the rationale. R-18's no-retroactive-activation
  clause is hereby scoped to the key-consulted path.
- R-38 (v4#3 premium lapse scope): ANY premium dispatch failure — auth or not — lapses
  `models.premium.approved` for the remainder of the run (one OMIT step per R-25, then no
  re-offers). Retry-per-task would recreate the exact Fable-outage retry pattern R2 exists to
  prevent. Ledger degraded reason distinguishes "auth-40x" vs "unavailable". Loud surface always.
- R-39 (v4#4 marker re-arm): the marker RECORDS THE VERSION it completed for
  (`firstRunCompletedAt` + `firstRunVersion`); the installer stamps `installedVersion`; bootstrap
  force-runs when the marker is absent OR firstRunVersion ≠ installedVersion — i.e. RE-ARMED ON
  EVERY INSTALL/UPGRADE (matches OP-5 literally: "first time after install"; upgrades introduce
  new posture checks worth one forced pass). PENDING OPERATOR VETO (user-facing cadence).
- R-40 (v4#5 absent-(b) enforcement): added to the R-35 contract text: "Absent primitive (b),
  budget-overrun enforcement degrades to worker compliance + livenessDeadline escalation,
  surfaced at preflight." No silent gap.

### R-41..R-42 — Convergence re-gate v5 pins folded (gate v5; all other sections verified converged)
- R-41 (v5#1 marker comparator — adopting the gate's own closing text + one extension):
  `installedVersion` := the existing `.kata-version` stamp's `version` field, written at
  install/update/factory-reset (no new key). Stamp absent OR version "unknown" ⇒ the version
  clause is SKIPPED — marker absence alone forces (dev in-repo homes are not force-every-run).
  EXTENSION: factory-reset additionally CLEARS `firstRunCompletedAt` (it wipes install state; one
  forced pass after reset is correct). Operator confirmed upgrade re-arm this round ("go with
  your recommendation").
- R-42 (v5#2 hostPosture semantics): AUDIT-ONLY, last-write-wins, never consulted for
  suppression. The compact-window recommendation is RECOMPUTED at every run's preflight per OP-4
  (cheap; correct per-model/per-window by construction — no keyed-map cathedral). The only
  do-once suppression in the file is `firstRunCompletedAt`, which suppresses the forced FULL
  bootstrap, never the per-run recommendation.

### R-43 — Delta-gate v6 fold (grill CLOSED after this entry)
- R-43 (v6#1 — CORRECTS R-41's comparator field; gate caught a second false premise):
  `.kata-version` has NO `version` field — its fields are `gitSha` and `suiteSemver`
  (kata_version.py:22-31, 109-117). PIN: the comparator reads **`gitSha`** (suiteSemver EXPLICITLY
  REJECTED — it re-arms only on semver bumps, breaking R-39's re-arm-on-every-upgrade; gitSha
  re-arms on every update, and "unknown" (kata_install.py:1171) is exactly the skip-clause case).
  Verified by the gate: stamp IS written at install (kata_install.py:1472), --update (1337),
  --factory-reset (1421); the marker-clear extension IS implementable at the factory-reset branch
  (1359-1439) BUT `write_settings` cannot delete a key ({**existing, **owned} preserves all,
  kata_settings.py:165/177) ⇒ the clear needs a small NEW fail-closed delete helper.
GRILL CONVERGENCE: gate v5 verified all other sections converged; v6 verified R-41/R-42 with this
one field correction (which adopts v6's own drafted answer). The grill is CLOSED; the DESIGN
freeze-gate is the next fresh adversarial pass and re-attacks these pins in §2.

### Cautions carried to DESIGN (gates v5+v6, non-blocking)
- C-1: pin `acceptedDefaults` value schema at DESIGN before bootstrap writes it.
- C-2: CA-6b allowlist-coverage check — DESIGN enumerates the run-critical patterns it warns on
  (a fixed checklist, not an analyzer; anti-cathedral).
- C-3: corrupt `.kata-settings.json` ⇒ lenient read (marker reads absent ⇒ force) + fail-closed
  write (marker cannot persist) = forced first-run that can't complete. Surface loudly + point at
  the corrupt file; never loop.
- C-4 (gate v6): the marker/hostPosture writer must copy the fail-closed `_load_existing` pattern
  (kata_settings.py:120-144), NOT the lenient `add_confirmed_platform` read-before-write
  (kata_settings.py:105-111), which silently clobbers a corrupt file — contradicting C-3.

## Handoff-taxonomy assessment (R-6 working notes)
Current state (grounded): ONE durable artifact family — .planning/HANDOFF.md (protocol/handoff.md),
git-committed, with a boundary variant; T1: boundary supersedes coincident self-handoff. Manual
(/kata-handoff), self (kata-selfhandoff trigger), boundary (kata-sprint) all converge on the SAME
file+format. Agent↔conductor exchanges are NOT handoffs: conductor→worker = dispatch brief;
worker→conductor = final report (+ board lines); escalations = board + protocol/escalation.md.
Gaps needing clarification in DESIGN:
1. TERMINOLOGY (glossary): "handoff" is overloaded. Canonical: handoff = session-boundary durable
   artifact (HANDOFF.md family). _Avoid_: calling dispatch briefs / final reports "handoffs."
2. PROVENANCE: add `kind: manual|self|boundary` to HANDOFF.md frontmatter (additive) so the
   re-anchor path + audits know what produced it. Git history already gives sequence.
3. STALENESS RULE for re-anchor: SessionStart(compact) points at HANDOFF.md; if its commit predates
   the session or is older than the last N task completions (board tells), the resumer must fall
   back to full kata-orient 3-tier rebuild (never trust a stale handoff over the board/STATE).
4. REFRESH SEMANTICS (from R-2): over-threshold refresh overwrites HANDOFF.md + commits (history in
   git); T1 extended: any coincident boundary handoff supersedes a same-boundary self-refresh.
5. WORKER FINAL REPORTS (CA-5): size-contracted verdict+pointer inline; full report artifact home +
   durability split: bulk to .kata/reports/<task>-<kind>.md (session-local, gitignored) BUT anything
   a DECISION cites must live durable (board/commit/spec) — matches existing D141 discipline.
   Freeze-gate attacks this split.
6. NO new artifact formats. Everything above is additive to protocol/handoff.md + kata-handoff.
