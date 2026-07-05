---
spec: context-autonomy
title: "Context autonomy — the gauge-driven self-handoff loop: warn → handoff → compact → re-anchor, unattended"
status: FROZEN 2026-07-04 (freeze-gate v1 SHIP-WITH-FIXES — 6 MED / 4 LOW, fidelity clean, all ten folded in place same-day; gate history: grill 6 rounds — convergence v1–v5 + delta-gate v6, CLOSED at R-43 — then freeze-gate v1; pending the operator commit gate)
created: 2026-07-04
version-target: v0.2.1
baseline: master 2c81beb (v0.2.0; pytest 2505/3 skip, validator 48/0/0, Snyk medium+ 0)
provenance: >-
  GRILL-LEDGER.md (this dir) is the sole decision source: operator pre-locks OP-1..OP-9, self-resolved
  SR-1..SR-17, resolutions R-1..R-43 (supersede chains honored: R-7→R-13 subagent leg; R-33→R-36 settings
  home; R-18 scoped by R-37; R-41's comparator field CORRECTED by R-43), handoff-taxonomy notes 1–6,
  tunable defaults, cautions C-1..C-4.
  Grounding: GROUNDING-CLAUDE.md (host facts), RESEARCH-CROSS-PLATFORM.md (degradation matrix),
  GLOSSARY-STAGED.md (canonical vocabulary — used verbatim here), DRAFT-observability.md (the
  observability deliverable). Nothing in this DESIGN is decided outside that ledger.
d-records: >-
  Planned at merge (new D# ≥ D146, supersede-never-rewrite): D146 = the context-autonomy initiative
  freeze (this DESIGN); D147 = the R-37 deliberate BC departure (one-shot configs — including
  pre-v0.2.1 — rotate unconditionally); D148 = the model-tiering gated premium amendment (§3).
tags: [kata/spine, context-autonomy, self-handoff, gauge, premium-gate, freeze, design-contract]
---

# Context autonomy — FROZEN DESIGN (v0.2.1)

Vocabulary is GLOSSARY-STAGED.md, used exactly: **smart zone**, **handoff**, **startup load**,
**work quantum**, **continuation report**, **trigger fraction**, **gauge**, **backstop**,
**premium offer**, **auto-context (rotation)**. Those glossary entries are normative for this spec
and stage into CONTEXT.md at merge.

## §0 Mission + the acceptance scenario

Main-session context management is the priority item of v0.2.1 (OP-7). The conductor's context is the
run-fatal resource; worker tokens are the cheap, parallel one (R-26 rationale). Today the trigger prose
exists (kata-selfhandoff SKILL.md:30-45 already mandates the model-resolved prime-frame trigger,
task-boundary preferred, generous-not-timid) but **nothing is wired to fire it** — SR-1: this initiative
wires a gauge to an existing policy; no new threshold concept is invented.

**The 8-hour walk-away scenario (OP-8 — the run this DESIGN must survive):** the operator composes a run
with `delivery.boundary: "auto-continue-while-green"` (SR-2), answers ONE preflight approval bundle
(installs/downloads + permission allowlist + premium gate + compact-window recommendation — OP-4), and
walks away for 8 hours. During that window the conductor session crosses its trigger fraction one or more
times; each time it writes/refreshes the durable handoff at a wave boundary, the host compaction (or a
platform respawn) resets the context on kata's recommended schedule, the SessionStart(compact) hook
re-anchors the fresh context on `.planning/HANDOFF.md`, and the run resumes at the exact next task
boundary with zero task loss and full context quality (R-2). Expected interactive prompts after the
bundle: **zero**. Under-threshold sessions never churn handoffs (R-8). If every leg is absent (no gauge,
no hooks, auto-compact disabled) the run degrades to deterministic rotation or a preflight BLOCK (R-12)
— it never dies silently at the hard limit.

Session scope pre-locks recorded: OP-1 (no PokeVault/MindBridge deploy this initiative — §8),
OP-6 (cross-platform docs scope = Kiro, Codex CLI, Copilot, Cursor, Gemini CLI; Windsurf cut).

Open operator items (freeze-gate fold #9): the two **[VETO-FLAG]** decisions — CA-L22 (report home) and
CA-L25 (intent-keyed BLOCK) — stand locked-pending-veto and **surface at the operator merge gate**.

## §1 Locked decisions (CA-L1..CA-L44)

Every resolved ledger branch appears below (or in §8 as a named deferral). Tunable **values** are marked
`[TUNABLE]` (locked structure, tunable value — §9 table). Items the ledger recorded PENDING OPERATOR VETO
are locked here with an explicit **[VETO-FLAG]** the freeze-gate must surface.

### Leg A — the gauge (CA-1)

- **CA-L1 — Chain-never-clobber; two bridge files, zero contention (SR-11, R-4, R-32).** Kata ALREADY
  ships a statusline (adapters/claude/statusline.py + settings.snippet.json) and the clobber hazard is
  ours: naively merging the snippet replaces a user's existing `statusLine` (e.g. the operator's
  gsd-statusline.js). LOCKED: kata **never clobbers**. If a user statusline exists, kata offers a
  **chaining wrapper** (exec the user's script as child, pass stdin through unmodified, never touch the
  user's output or bridge file) or skips to the fallback legs. The chained wrapper writes its OWN sibling
  bridge `%TEMP%/kata-ctx-<session_id>.json` (atomic temp+rename); the user's file is untouched.
  Reader priority: (1) kata bridge → (2) user bridge (4-field, %-only triggering) → (3) deterministic
  fallback (CA-L4). The operator's own statusline stays untouched (R-4: no operator action).
  **Fresh-profile owner (freeze-gate fold #3):** when NO user statusline exists, kata's OWN statusline
  (adapters/claude/statusline.py + kata_statusline.py) is extended to write the same superset bridge
  file unchained — a named build item of this initiative.
- **CA-L2 — Bridge superset schema (R-24).** Kata's bridge writes
  `{session_id, remaining_percentage, used_pct, timestamp, total_tokens}` — the wrapper receives the same
  statusline stdin (GROUNDING G3: `context_window.remaining_percentage` + `context_window.total_tokens`
  confirmed), so `total_tokens` is free; additive/BC with the gsd 4-field schema. Degrade (unchained
  pre-existing bridge only, no `total_tokens`): the trigger runs **percentage-only** (0.70 by %);
  backstop-recommendation tokens fall back to the advertised window as an ESTIMATE carrying an explicit
  approximation flag in the recommendation text. Never silent.
- **CA-L3 — Gauge staleness (G3 headless-freshness UNVERIFIED ⇒ mandatory).** Bridge timestamp older
  than **300 s** `[TUNABLE]` ⇒ stale ⇒ deterministic fallback leg. Stale or absent ⇒ never "assume fine"
  (glossary: gauge).
- **CA-L4 — Deterministic N-wave fallback (CA-1d).** No usable gauge ⇒ rotate every
  `N = max(1, floor(trigger_tokens ÷ est_wave_burn))` wave boundaries; `est_wave_burn` default **40k
  tokens** `[TUNABLE]` until parent-telemetry rows exist (CA-L40; SMOKE-3 seeded n=1).
- **CA-L5 — Trigger denominator = the HOST-REPORTED effective window (R-15).** The denominator is the
  gauge's `context_window.total_tokens` (post-cap): a capped session's real frame IS the cap. Gauge
  absent ⇒ there is no live host-reported denominator for the *trigger*, but the deterministic N-wave
  fallback (CA-L4) still needs a `trigger_tokens` value for its wave count: use
  `trigger_tokens = contextTrigger × advertised-window estimate` (a per-model window estimate, explicitly
  flagged **APPROXIMATE** — same posture as the `backstop_recommendation` approximate fallback). (Freeze-gate
  fold MED-1: the earlier "fallback rotation needs no denominator" wording was wrong — the wave count needs
  the token estimate; reconciled here.)
- **CA-L6 — Small-frame / absent-gauge ⇒ rotation is MANDATORY (CA-1e, OP-9 degradation clause).**
  Degradation is always graceful rotation — never "assume infinite context."

### Leg B — trigger policy + self-handoff wiring (CA-2 + threshold tree)

- **CA-L7 — Conductor trigger fraction: 0.70 of the effective window, ONE config key (R-1→R-7→R-13).**
  The operating target is the **smart zone** — above the context floor (kata-orient 3-tier load complete),
  below the rot ceiling (R-7: degradation is two-sided; the 0.40 band is NOT a conductor clamp). Trigger
  = **0.70 `[TUNABLE]` × host-reported effective window** (CA-L5). One key (`contextTrigger`, §2), shown
  in bootstrap's advanced drawer, **never interactively asked** (K5: no new dial). A note for 1M frames
  is recorded: a lower value is one config edit away (R-7). Rejected: flat-70%-of-raw — R-1's rationale,
  superseded by R-7 (operator: fraction-of-effective-window, with the 1M config note); 60% default
  (violates D8 generous-not-timid). *(Freeze-gate fold #6 wording — R-1's D83-reconciliation clamp was
  itself superseded; the standing rejection rests on R-7's smart-zone framing.)*
- **CA-L8 — D83 is NOT edited (supersede-never-rewrite, R-7).** The prime-frame **0.40** fraction
  (protocol/config.md:98-115) remains the **sprint-sizing** fraction unchanged. The per-role trigger
  policy here is the **B1 amendment**: the one-shot self-handoff threshold source named by D83/B1 is now
  this spec's trigger fraction, with the operator rationale (smart zone) recorded. Same primitive
  lineage, two policies — config.md gains a pointer, no rewrite.
- **CA-L9 — Subagent threshold is DERIVED, never user-configured (R-13, supersedes R-7's 0.50 leg;
  boundary + cap per R-26).** Rotation point = **startup load + 40pp work quantum** `[TUNABLE]` (start
  5% ⇒ rotate at 45%); invariant: every dispatch gets ≥40pp of the worker window for processing. Guards:
  **hard cap 0.80** `[TUNABLE]` of the worker window (cap WINS: startup > 0.40 makes the quantum
  unsatisfiable ⇒ the dispatch is OVER-BRIEFED and is caught at plan/freeze time — split the task or slim
  the brief, a **mandate**, not a WARN); over-briefing **WARN at startup > 0.30** `[TUNABLE]` (the early
  smell — surface, don't block). **Startup load** = the conductor-AUTHORED dispatch payload only (brief +
  packed orientation attachments), estimated at dispatch by the conductor (it authored the brief);
  worker-side read-ins count toward the worker's own budget, never startup. CONFIG SURFACE SHRINKS: no
  subagent threshold key exists.
- **CA-L10 — Quantum runtime semantics: plan-time target; soft budget with completion-awareness (R-26,
  R-31).** The well-planned case NEVER rotates. At runtime: at budget ⇒ finish the current chunk +
  checkpoint ⇒ if the remaining estimate fits under the 0.80 hard cap, CONTINUE to completion (no
  rotation to do 10% of a task); else return a **continuation report** (last checkpoint anchor + what
  remains + what was learned). Estimated activity ≥ cap ⇒ return UNCONDITIONALLY. Continuations reuse
  the existing M4 kill+fresh-dispatch primitive anchored at the last checkpoint (ADAPTER-CONTRACT-M4
  primitive (b) — no new machinery); green-path inter-part evaluation is checkpoint-trailer scoring
  (**zero LLM calls**). Continue/return is re-evaluated at EVERY checkpoint; the BRIEF embeds the numbers
  (budget tokens, cap tokens, estimator basis); the estimate is worker-local from brief-embedded numbers
  + own activity, stated as approximate in the brief (R-31 pins all four). Rationale recorded: rotation
  is a designed exception with bounded cost, not a cadence.
  **Substrate dependency (freeze-gate fold #4):** checkpoint-anchored continuation rides the M4
  checkpoint stream, which exists only at `inlineEval ≠ off`. `inlineEval: off` ⇒ the continuation
  machinery DEGRADES to the brief's budget prose + return-at-task-boundary only (no checkpoint-anchored
  continuation). Therefore bootstrap, whenever it writes `contextAutonomy: "on"`, ALSO mandates
  `inlineEval: "telemetry"` or higher for that config (the existing M4-L8 bootstrap default already
  writes `"telemetry"` for new runs — this pins the coupling, additive, never touching absent-key BC).
- **CA-L11 — Enforcement honesty (R-19, R-31).** Worker-side observance is **compliance** (M1-L3:
  soundness never rests on it); TRUE enforcement is conductor-side — existing liveness machinery + the
  M4 kill primitive terminate a worker that plows on. Plan/freeze-time: a **WARN** (never hard-fail) when
  estimated task burn > the 40pp quantum, estimator `[TUNABLE]` tokens-per-chunk seeded from ledger
  `perTask` medians; the budget line is mandatory prose in every dispatch brief (D136 posture: the
  estimate drives a WARN + split suggestion, fail-soft; splitting stays planner judgment).
- **CA-L12 — Boundary placement + post-handoff behavior (CA-2a/2b, R-2).** The conductor evaluates the
  trigger at **wave/frontier-recompute boundaries only**; **never mid-task** (existing kata-selfhandoff
  mandate, unchanged). Post-trigger: **keep working**, refreshing the handoff at every subsequent
  boundary until the host reset arrives (option (a)). Resume must reload FULL context quality —
  kata-orient 3-tier, budget-capped per protocol/orientation.md — seamless, no hangs, no degradation
  (graded at CA-A1, not just task continuity).
- **CA-L13 — Balance mandate: generous-not-timid stands (R-8).** Early exit is a risk equal to rot.
  The acceptance suite includes a **NO-FIRE case**: a session under threshold produces zero handoff
  churn (CA-A5).
- **CA-L14 — Reset ownership (R-14).** Host compaction is the SOLE reset mechanism on Claude (no
  programmatic /compact exists). Kata owns the **SCHEDULE + DURABILITY** (threshold, handoff freshness,
  recommended backstop placement); the host owns the **MECHANISM**. The selfhandoff prose "compact/reset"
  step = the host act arriving on kata's schedule. Platforms with respawn primitive (c): rotation =
  kata-initiated respawn. There is **no conductor self-compaction leg**.

### Leg C — host backstop (CA-3)

- **CA-L15 — Recommend-never-write (OP-3, CA-3c).** The backstop recommendation vector is the
  settings.json key `autoCompactWindow` (GROUNDING G1: settings key preferred; the env var takes
  precedence and is NOT used). Kata **never writes user settings silently** — the recommendation is
  surfaced in the preflight bundle (OP-4) and applied only with permission, set above the internal
  target or not at all if the default suffices. Ceiling semantics per G1 (the brief's reserve-semantics
  examples were corrected — GROUNDING §"CORRECTION").
- **CA-L16 — Backstop formula (R-21).** `gap = max(worst observed boundary burn + handoff write cost,
  0.10 × effective window)` — 10% **of the window** `[TUNABLE fallback]`, telemetry-derived once rows
  exist (OP-3). `recommended autoCompactWindow = clamp(target_tokens + gap, 100k key floor, model max)`.
  `target+gap ≥ model max` ⇒ recommend NOTHING (default suffices). `target+gap < 100k` ⇒ recommend the
  100k floor + note that rotation covers the remainder. Telemetry rows replace the fallback constants as
  they accumulate (CA-L40).
- **CA-L17 — autoCompactEnabled preflight check + observe-only PreCompact posture (CA-3b/3d, SR-5,
  SR-10, G2).** Preflight MUST verify auto-compact is ENABLED (it can be disabled — then the host
  backstop does not exist; feeds R-12 stranding logic). The existing PreCompact hook
  (adapters/claude/hooks/kata-precompact.py — board snapshot to refs/kata/trail + custom_instructions
  nudge; never raises) is extended ADDITIVELY to also surface HANDOFF.md existence/freshness. The hook
  **never blocks** compaction (G2: blocking near the limit is dangerous — no headroom left);
  observe-only + checkpoint guarantee. The hook README's sync-time-budget assumption is UNVERIFIED —
  live-proof item (CA-A1).

### Leg D — re-orientation (CA-4 + handoff taxonomy R-6)

- **CA-L18 — SessionStart(compact) re-anchor hook (CA-4a, SR-9, G2).** A SessionStart hook with matcher
  `compact` injects, via `hookSpecificOutput.additionalContext` (G2: confirmed mechanism), the re-anchor
  instruction pointing at the newest **`.planning/HANDOFF.md`** (protocol/handoff.md:7 — NOT the brief's
  "SELFHANDOFF.md"; brief corrected per SR-9). Orientation tiers consume it 1:1.
- **CA-L19 — Handoff staleness rule (R-20, R-27 + addendum; taxonomy note 3).** STRICT: any board
  `DONE`/`DECISION` line **newer** than the HANDOFF.md git commit demotes the handoff from sole-anchor to
  context-input; the kata-orient 3-tier rebuild becomes authoritative. Comparator = newest board
  DONE/DECISION ISO-8601-UTC line timestamp (protocol/board.md:9 line grammar, verified) vs HANDOFF.md's
  git commit timestamp, strict `>`; same-second ties favor the handoff. N=1 semantics; **no tunable**.
  Trail-ref independent; no reliance on `@sha` presence. **Clock-skew note (freeze-gate fold #10):** the
  comparator crosses clock domains — board lines carry writer PROCESS clocks (protocol/board.md's stated
  single-host assumption), the handoff carries the git COMMITTER clock. Acceptable on a single host at
  this rule's granularity; the strict `>` + ties-favor-the-handoff convention is also the skew posture
  (a same-second ambiguity never demotes). Multi-machine runs re-visit this with the board's own
  documented revisit item.
- **CA-L20 — AGENTS.md standing line (CA-4b).** The target-repo AGENTS.md router stanza gains ONE
  standing line: a resumed/compacted session re-anchors via `.planning/HANDOFF.md` + the staleness rule
  before doing anything else. (Universal fallback for platforms with no hook — §5.)
- **CA-L21 — Handoff taxonomy (R-6 notes 1–6; glossary "handoff" is normative).** (1) TERMINOLOGY: a
  handoff = the session-boundary durable artifact (`.planning/HANDOFF.md` family) ONLY; dispatch briefs,
  worker final reports, and escalation payloads are agent-exchange artifacts, never "handoffs".
  (2) PROVENANCE: HANDOFF.md frontmatter gains additive `kind: manual|self|boundary`. (4) REFRESH: an
  over-threshold refresh overwrites HANDOFF.md + commits (history lives in git); **T1 extended** — any
  coincident boundary handoff supersedes a same-boundary self-refresh (protocol/handoff.md:30-31 base
  rule). (6) **NO new artifact formats** — everything is additive to protocol/handoff.md + kata-handoff.
  (Notes 3 and 5 are CA-L19 and CA-L22/23.)

### Leg E — report budgets (CA-5)

- **CA-L22 — Report artifact home + naming (R-10) [VETO-FLAG: home recorded pending operator veto].**
  Reports live at project-local gitignored **`.kata/reports/<runId>-<taskId>-<agent>-<kind>.md`** —
  run- and target-scoped, readable by every dispatched agent via repo paths, consistent with the board's
  home, survives multi-project installs (a harness-install-dir home would collide across projects and be
  invisible to off-host/ACP agents). **Durable-citation rule (taxonomy note 5, matches D141 discipline):**
  anything a DECISION or ledger row cites must be quoted/restated in a committed artifact — never a bare
  pointer at a `.kata/*` path (DRAFT-observability.md table row "Reports (v0.2.1)" carries this verbatim).
  The freeze-gate attacks this split.
- **CA-L23 — Size contracts + narration economy (CA-5b, note 5).** Worker final reports are
  size-contracted: **verdict + pointer inline**, bulk to the `.kata/reports/` artifact. Narration-economy
  prose riders go into the dispatch-brief template and report contracts (this is what keeps startup load
  under the CA-L9 thresholds — over-briefing WARN is the symptom detector for violations, R-13).

### Leg F — preflight bundle (CA-6)

- **CA-L24 — ONE approval bundle, collected pre-run (OP-4, SR-3).** The bundle = dependency
  installs/downloads + permission allowlist + the premium gate (Leg G) + the compact-window
  recommendation (CA-L16) + **the host-settings write slot (freeze-gate fold #5)**: installing the
  SessionStart(compact) hook and the statusline/wrapper entries IS a write to `~/.claude/settings.json`,
  so it is an explicit bundle slot approved like an install — never an implied side effect. Merge
  discipline pinned: **hooks arrays are APPEND-NEVER-REPLACE; `statusLine` is only ever
  chained-or-skipped** — the CA-L1 never-clobber guarantee generalizes to EVERY settings key kata
  touches. Collected ONCE; zero expected prompts for 8 hours after. Extension is additive alongside the
  reserved `preflight.approval_mode` field (protocol/config.md:41, D29) and the default-FAIL
  `kata_preflight.py` engine (SR-16: today it covers dependency installs only).
  **Sequencing (freeze-gate fold #2):** bundle collection is a NEW bootstrap step between Phase 2 (the
  advanced drawer) and the Phase-3 config write — **bootstrap collects; kata.config is written AFTER,
  with `models.premium.approved` recorded from the collected answer**. kata-orchestrate's existing
  PRE-FLIGHT gate stays **enforcement-only**: it verifies/provisions the approved set and NEVER prompts
  a second time.
- **CA-L25 — Intent-keyed strictness (R-12) [VETO-FLAG: recorded pending veto — asked twice,
  unanswered; freeze-gate attacks].** A walk-away-configured run (auto-continue boundary or unattended
  flag) with a missing leg that would STRAND it (auto-compact disabled AND no gauge AND no respawn path
  ⇒ session death at hard limit with no recovery) = **BLOCK** at preflight. Attended runs: **WARN** +
  proceed.
- **CA-L26 — Allowlist-coverage check: a FIXED checklist, not an analyzer (CA-6b, C-2 resolved
  here — anti-cathedral).** Preflight WARNs when the host permission allowlist does not cover these
  run-critical pattern classes, enumerated and frozen: (1) git plumbing the loop uses (commit / branch /
  worktree / merge on the target repo); (2) the run's verify command (`target.baselineGate` / the test
  runner); (3) dependency installs from the approved `preflight.allowed_registries` set; (4) writes to
  the bridge temp path (`%TEMP%/kata-ctx-*.json`) and to `.kata/**` + `.planning/**` in the target;
  (5) invocation of the harness tools (`python`/`uv run` on `<harness_home>/tools/*`). Nothing else is
  checked; the list is the whole check.

### Leg G — premium gate (CA-7; the amendment text is §3)

- **CA-L27 — Gate semantics (OP-2, R-3, R-9).** Fable stays in the tiering matrix behind a once-per-run
  approval collected at the CA-L24 bundle, with a prominent cost disclaimer (disclaimer TEXT is a docs
  pass — CA-7b, build task). **Decline ⇒ pin `models.anchor: "opus"` + hard-stop advising a `/model`
  switch** — the only honest decline, because SR-4: config cannot stop a Fable SESSION from burning
  Fable on zero-step critical work (inherit-by-omission); the session model is the operator's own choice.
  **Anchor-IS-fable** ⇒ confirm keep-using + warn: "long-running loops on Fable as primary FM can drive
  costs up significantly." **The premium offer** (post-July-7): anchor=opus ∧ mode=advanced ⇒ kata MAY
  OFFER anchor+1 (Fable) at preflight approval, the user knowingly accruing Fable API usage. Scope
  (R-9, confirmed verbatim): the approved offer elevates **CRITICAL and CODING** work classes;
  economy/low-criticality NEVER runs Fable, even in advanced with approval.
- **CA-L28 — Config record (R-16, R-34).** New key `models.premium: {offer, approved, scope,
  grantedMode}` (§2), written by bootstrap after the gate. **kata.config is authoritative** for dispatch
  (the resolver reads config; survives clone); `.kata/preflight.json` carries the audit event only.
  Once-per-run = once per kata.config (R-17).
- **CA-L29 — The four conjuncts + explicit premium id (R-16, R-22).** `resolve()`'s premium branch fires
  ONLY when `approved ∧ work-class ∈ scope ∧ a premium rung exists above the anchor ∧ mode == "advanced"`
  (the fourth conjunct is resolve-time — closes the silent standard-mode +2-rung cost blowout). It
  returns the **EXPLICIT premium id** (inherit would give the session model — explicit is mandatory).
  Delivered as the §3 GATED AMENDMENT to the frozen model-tiering spec.
- **CA-L30 — Failure semantics (R-25, R-30, R-38).** Failed premium dispatch ⇒ **immediate OMIT/inherit
  at the anchor rung** — never an explicit anchor id (tracks mid-run `/model` switches; preserves the
  amended invariant). **One-step chain: premium → OMIT.** ANY premium dispatch failure — auth or not —
  **LAPSES `models.premium.approved` for the remainder of the run** (no re-offers, no retry storm — the
  exact pattern R2 exists to prevent). For the premium rung ONLY, 401/403 ⇒ *premium-unavailable*:
  OMIT-inherit + LOUD surface (board DECISION + ledger `degraded {scope:"premium",
  reason:"auth-40x"|"unavailable"}` + handoff note) — because premium is an OPTIONAL elevation whose
  failure has a semantically-correct safe fallback (the anchor = the exact no-approval behavior);
  unattended survival wins; never silent. Baseline (non-premium) R2 auth-raise behavior is unchanged.
- **CA-L31 — Gate home + lapse executor (R-17, R-22, R-34).** The gate is collected in the PREFLIGHT
  phase of bootstrap's launch sequence (bootstrap orchestrates; preflight collects). The approval record
  carries `grantedMode`; a re-entrant run that changes mode **LAPSES** the approval — the lapse executor
  is BOOTSTRAP: re-entrant Phase 0/1 detecting `mode ≠ grantedMode` clears `approved`; the next preflight
  re-asks. Fable-gate attach point is Layer 3 anchor resolution (SR-15: kata-bootstrap/kata-initiate
  write `models.anchor` once per branch; no proactive model-approval concept existed before — net-new,
  additive).

### Leg H — bootstrap + settings (CA-8 + OP-9)

- **CA-L32 — Auto-context posture (OP-9/R-11, R-18, R-23, R-28).** `delivery.shape == "one-shot"` ⇒
  rotation **UNCONDITIONAL** (the key is not consulted; operator: "assumed ON, not optional"). The
  config key `contextAutonomy: "on"|"off"` (string, securityScan-style convention) governs
  **incremental shapes only**; the operator's "individual feature / bug fix" phrasing was a parenthetical
  example of sprint-based processing, NOT runShape `individual` (R-28 pin). Default is **WRITE-TIME**:
  v0.2.1 bootstrap Phase 3 writes the key explicitly `"on"` for new configs; **absent-at-load ⇒ OFF**
  where the key is consulted (D25/BC1). Re-entrant bootstrap (same-as-last from a pre-v0.2.1 config)
  writes the key at next touch per its write-all-fields-by-construction Phase 3, surfaced in the
  composition summary (R-23).
- **CA-L33 — The R-37 deliberate BC departure (D147).** Absent-at-load ⇒ OFF applies ONLY where the key
  is consulted. One-shot configs — **INCLUDING pre-v0.2.1 ones** — rotate unconditionally. Rationale
  (recorded, D147): the behavior is protective and additive, and it was ALWAYS mandated by the
  selfhandoff prose (kata-selfhandoff SKILL.md:30-45) — it was simply never wired; degradation stays
  graceful (no gauge/hooks ⇒ deterministic rotation, never "assume infinite context"). R-18's
  no-retroactive-activation clause is hereby **scoped to the key-consulted (incremental) path**. §4 row 1.
- **CA-L34 — No mid-roadmap auto-write (R-29).** A pre-v0.2.1 incremental run in flight is never flipped
  (D25/BC1). Honest posture: sprint boundaries ALREADY rotate by design (the boundary handoff), so such
  a run is not stranded — only intra-sprint refresh is absent. kata-readiness (runs at every bootstrap
  entry incl. Phase 0b routing) gains a WARN: "pre-v0.2.1 config lacks contextAutonomy — written at next
  composition (Phase 3) or opt in by config edit." Surfaced, never silent, no retroactive flip.
- **CA-L35 — Settings home: extend the EXISTING `.kata-settings.json` (R-36, CORRECTING R-33; IP-A
  stands).** `.kata-settings.json` is the harness-home central-install settings file
  (tools/kata_settings.py:16,41; docs/SETUP.md:90) with existing read/write/merge machinery — **NO new
  file** (IP-A explicitly dropped a `~/.kata/` machine-layer file as over-engineered). New keys (§2):
  `firstRunCompletedAt`, `firstRunVersion`, `hostPosture {autoCompactChecked, recommendedWindowTokens,
  bridgeMode}`, `acceptedDefaults`. Semantics: per-install, not per-project. Everything RUN-scoped stays
  in per-branch kata.config (`contextAutonomy`, `models.premium` incl. `grantedMode`, `contextTrigger`).
- **CA-L36 — Force-run marker + upgrade re-arm (OP-5, R-39; R-41 comparator field CORRECTED by R-43 —
  operator confirmed).** Bootstrap force-executes the FULL first run when the marker is **absent OR
  `firstRunVersion ≠ the `.kata-version` stamp's `gitSha`** — re-armed on every install/upgrade
  (upgrades introduce new posture checks worth one forced pass). COMPARATOR PIN (R-43): the
  `.kata-version` stamp has **NO `version` field** — its fields are `gitSha` and `suiteSemver`
  (kata_version.py:22-31); the comparator reads **`gitSha`**. `suiteSemver` is EXPLICITLY REJECTED: it
  re-arms only on semver bumps, breaking R-39's re-arm-on-every-upgrade; `gitSha` re-arms on every
  update. The stamp IS written at install (kata_install.py:1472), `--update` (kata_install.py:1337),
  and `--factory-reset` (kata_install.py:1421) — **no new key**. Stamp absent OR `gitSha == "unknown"`
  (the plain-install path, kata_install.py:1171) ⇒ the version clause is SKIPPED — marker absence alone
  forces (dev in-repo homes are not force-every-run). Factory-reset additionally CLEARS
  `firstRunCompletedAt` (it wipes install state; one forced pass after reset is correct) —
  implementable at the factory-reset branch (kata_install.py:1359-1439), BUT `write_settings` cannot
  delete a key (`{**existing, **owned}` preserves all keys, kata_settings.py:165/177) ⇒ the clear
  requires a small **NEW fail-closed delete helper** in `kata_settings` — a NAMED build item of this
  initiative. Bootstrap's attach point is Phase 0 / kata-readiness (SR-16: no first-run gating exists
  today — greenfield, additive); re-entrant behavior otherwise unchanged (CA-8b).
- **CA-L37 — hostPosture is AUDIT-ONLY; corrupt-settings surface (R-42, C-1, C-3).** `hostPosture` is
  last-write-wins and **never consulted for suppression**; the compact-window recommendation is
  RECOMPUTED at every run's preflight per OP-4 (cheap; per-model/per-window correct by construction — no
  keyed-map cathedral). The ONLY do-once suppression in the file is `firstRunCompletedAt`, which
  suppresses the forced FULL bootstrap, never the per-run recommendation. **C-1 pinned:**
  `acceptedDefaults` value schema = `{ "<bundleItemId>": { "value": <json>, "v": "<harness semver>",
  "at": "<ISO-8601 UTC>" } }` — one entry per bundle item the operator accepted at CA-L24; audit-only,
  same last-write-wins posture as hostPosture. **C-3 resolved:** a corrupt `.kata-settings.json` reads
  leniently (marker reads absent ⇒ force) but writes fail closed (marker cannot persist) ⇒ a forced
  first-run that can't complete — bootstrap MUST detect the write failure, surface LOUDLY pointing at
  the corrupt file path, and stop; **never loop**. **C-4 (gate v6) — writer discipline:** the
  marker/hostPosture writer copies the fail-closed `_load_existing` pattern (kata_settings.py:120-144),
  NEVER the lenient `add_confirmed_platform` read-before-write (kata_settings.py:105-111), which
  silently clobbers a corrupt file — contradicting C-3.

### Leg I — adapter contract (CA-9)

- **CA-L38 — Primitive (c): session-respawn (R-35 + R-40; conformance-only in v0.2.1).** Added to
  ADAPTER-CONTRACT-M4's primitive list (after (a) board-append and (b) kill+fresh-dispatch,
  ADAPTER-CONTRACT-M4.md:14-26). Contract paragraph, frozen verbatim: *"(c) session-respawn — the
  platform's OUTER SHELL (host feature, cron wrapper, or human; never the in-session agent) can end the
  conductor session and start a fresh one that re-anchors from the newest durable handoff
  (SessionStart-equivalent injection or a documented manual step). Absent ⇒ degradation: conductor
  writes/refreshes the handoff and PROMPTS THE OPERATOR to rotate (universal fallback); unattended runs
  on such platforms are bounded by one session window, surfaced at preflight. Governs CONDUCTOR sessions
  only — worker attempt topology is out of scope; LD7 remains named-DEFERRED."* Plus the R-40 sentence:
  *"Absent primitive (b), budget-overrun enforcement degrades to worker compliance + livenessDeadline
  escalation, surfaced at preflight."* Claude binding = the ONLY live leg in v0.2.1 (host compaction +
  SessionStart(compact) = the (c)-equivalent); SR-14 scope guard honored: (c) does not silently absorb
  LD7.
- **CA-L39 — Per-platform recommended-config docs (CA-9b, locked deliverable).** A docs page per OP-6
  platform (Kiro, Codex CLI, Copilot, Cursor, Gemini CLI) stating the §5 degradation row: the knob to
  set, the gauge channel if any, the resume primitive, and the must-guard risks — sourced from
  RESEARCH-CROSS-PLATFORM.md verbatim (its Confidence Gaps carry into §8 as re-verify items). Docs only;
  no non-Claude code legs in v0.2.1.

### Leg J — telemetry + observability (CA-10)

- **CA-L40 — Parent-tokens/phase columns (CA-10a, additive).** The telemetry ledger row gains additive,
  nullable per-phase parent-context readings (`parentTokens: {"<phase>": int|null}`) — row schema
  **v2 → v3, additive, no backfill**, mirroring the D142 precedent exactly (absent-`v`⇒v1 unchanged;
  present-but-unknown version still RAISES). Named consumers: the CA-L16 gap formula's
  worst-observed-boundary-burn term; CA-L4's `est_wave_burn` replacement; OP-3's telemetry-derived gap.
  Nulls are honest absence, never zero (usage-meter honesty, unchanged).
- **CA-L41 — Observability orientation doc ships at `protocol/observability.md` (CA-10b, lean;
  self-resolved placement).** DRAFT-observability.md (this dir) is the deliverable text — it documents
  what exists at v0.2.0 plus the one v0.2.1 addition (the `.kata/reports/` row + durable-citation rule,
  CA-L22). Ships as `protocol/observability.md`; review dispatches receive its pointer-block brief.

### Leg K — installer fix (CA-11)

- **CA-L42 — Shared-base-dir install fix (SR-12, R-5).** ROOT CAUSE: `iter_skill_dirs()`
  (tools/kata_install.py:58-67) returns only dirs directly containing `SKILL.md`; shared tier-family
  base dirs (`kata-grill/` holding `RUBRIC.md` + `resources/`, likely also the `kata-plan` /
  `kata-review` / `kata-diagnose` families) are never linked, so Windows copy-fallback installs dangle
  the `../kata-grill/RUBRIC.md` relative reference (the SMOKE-observed real defect: kata-grill/RUBRIC.md
  absent from ~/.claude/skills). FIX SHAPE (locked): **ADDITIVE** — a new helper enumerating shared
  tier-family base dirs (a dir under `skills/` that contains no `SKILL.md` but is referenced by sibling
  tier skills' relative paths, or equivalently: the parent dirs of tier-family skills that carry
  non-SKILL payload) + an additive call in the Claude install path, following the D104
  install-portability pattern (SR-13: mirrors `_flat_link_skills`; Claude-only adapter surface). The
  five frozen engine fns stay **byte-unchanged** (CA-L43); `iter_skill_dirs` (public API but NOT
  frozen-five) keeps its exact current return contract — the new enumeration is a separate function.
  Never-git holds; stdlib-only holds (§7).
- **CA-L43 — The FROZEN FIVE, enumerated and frozen (SR-12 mandate: pin the list before touching the
  installer).** Per the repo's own authoritative record (D128, .planning/DECISIONS.md:1775-1776;
  MD5-verified per .planning/STATE.md:177-178), the 5 frozen `kata_install.py` engine fns are:
  1. `install` (kata_install.py:361)
  2. `copy_project` (kata_install.py:385)
  3. `confirm_platform` (kata_install.py:427)
  4. `_flat_link_skills` (kata_install.py:274)
  5. `_link_or_copy` (kata_install.py:112)
  This list is FROZEN by this DESIGN. (Honesty note: the module docstring's "Public API" block lists
  `install`, `iter_skill_dirs`, `ensure_plugin_manifest`, `copy_project` — four names, a DIFFERENT set;
  the frozen-five is the D128 byte-freeze set, and D128 is authoritative. `iter_skill_dirs` and
  `ensure_plugin_manifest` are public but not byte-frozen; CA-L42 still leaves them unchanged.)

### Leg L — prose riders (CA-11 riders, SR-8)

- **CA-L44 — Three SMOKE riders, one docs pass.** (F1) verdict-tier variance: a calibration note
  recorded where verdict-tier guidance lives (kata-evaluate/review docs). (F2) index-continuity: one
  dispatch-base sentence added where the reroll anchor/index rule is documented (the
  DRAFT-observability.md "How to read checkpoints" hedge becomes a stated rule: no last-good anchor ⇒
  fresh attempt indexes from 0 at the task's dispatch base). (F5) HANDOFF §7's stale
  "class_median returns None at min_samples=5" expectation corrected (GROUNDING SMOKE-1: 8.35 is the
  correct output; calibration exclusion HOLDS). All prose-only, no behavior change.

## §2 Config + settings schema deltas (exact shapes)

### kata.config (per-branch, protocol/config.md — three additive fields)

| Field | Type | Meaning / BC |
|---|---|---|
| `contextAutonomy` | `"on" \| "off"` | Auto-context rotation for **incremental** shapes only (CA-L32). One-shot shapes never consult it (unconditional ON, CA-L33/D147). Bootstrap Phase 3 writes `"on"`. **Absent-at-load ⇒ OFF on the key-consulted path** (BC). Malformed ⇒ load-guard STOP + escalate (D45/GB12, the delivery-field posture). |
| `contextTrigger` | number (0–1) | The conductor **trigger fraction** override; default **0.70** `[TUNABLE]` when absent (CA-L7). Shown only in bootstrap's advanced drawer; never interactively asked. Consulted only where rotation is active. *(Key NAME is this DESIGN's compilation choice — structure locked, name freeze-gate-attackable.)* |
| `models.premium` | `{ offer: "fable", approved: bool, scope: ["critical","coding"], grantedMode: "advanced" }` | The premium-offer record (CA-L28..L31; §3). Written by bootstrap after the preflight gate. **Absent ⇒ the resolver's frozen behavior byte-for-byte** (no premium branch exists). `grantedMode` ≠ current `mode` at re-entrant bootstrap ⇒ `approved` cleared (lapse). Scope is fixed to the two classes; economy is structurally excluded. |

### .kata-settings.json (harness-home, per-install — tools/kata_settings.py; four additive keys)

| Key | Type | Meaning |
|---|---|---|
| `firstRunCompletedAt` | ISO-8601 UTC string | The force-run marker (CA-L36). Absent ⇒ bootstrap force-executes the full first run. Cleared by factory-reset. |
| `firstRunVersion` | string | The `.kata-version` stamp **`gitSha`** the forced run completed for; compared to the current stamp's `gitSha` (CA-L36, R-43 — the stamp has no `version` field; `suiteSemver` rejected). Stamp absent OR `gitSha == "unknown"` ⇒ clause skipped, marker absence alone forces. *(Key NAME retained from R-39; value is a gitSha.)* |
| `hostPosture` | `{ autoCompactChecked: bool, recommendedWindowTokens: int\|null, bridgeMode: "chained"\|"user-only"\|"none" }` | AUDIT-ONLY, last-write-wins, never consulted for suppression (CA-L37/R-42). |
| `acceptedDefaults` | `{ "<bundleItemId>": { "value": <json>, "v": "<semver>", "at": "<ISO>" } }` | C-1 schema, pinned at CA-L37. Audit-only. |

Corrupt file ⇒ lenient read / fail-closed write / loud surface / never loop (CA-L37, C-3). Writer
discipline per C-4 (CA-L37): the fail-closed `_load_existing` pattern, never the lenient
read-before-write. NEW build item: a small fail-closed key-delete helper in `kata_settings`
(factory-reset marker clear — `write_settings` cannot delete a key; CA-L36/R-43).

### Other artifact deltas

- **Bridge file (NEW):** `%TEMP%/kata-ctx-<session_id>.json` =
  `{session_id, remaining_percentage, used_pct, timestamp, total_tokens}` (CA-L2), atomic temp+rename.
- **HANDOFF.md frontmatter (additive):** `kind: manual|self|boundary` (CA-L21).
- **Telemetry ledger row (additive, v3):** `parentTokens: {"<phase>": int|null}` (CA-L40).
- **Host settings.json (RECOMMENDED, never written silently):** `autoCompactWindow` per CA-L16.

## §3 GATED AMENDMENT to the frozen model-tiering DESIGN (D148)

Delivered as a post-freeze gated-amendment addendum APPENDED to `.planning/specs/model-tiering/DESIGN.md`
(the existing POST-FREEZE ADDENDUM precedent; supersede-never-rewrite — no frozen line is edited).
**Gating clause:** everything below activates ONLY under `kata.config.models.premium` with all four
conjuncts true; **absent `models.premium`, the frozen spec governs byte-for-byte** — zero change to any
existing path, including the absent-`models`-block BC guarantee (R3).

1. **What it amends (quoted).** The frozen zero-step contract (model-tiering DESIGN §2, Layer 1):
   > "`resolve()` returns `None` (= OMIT the model param → inherit) whenever the resolved rung index
   > `== anchor_index`; it returns an explicit id string ONLY for a rung strictly BELOW the anchor
   > (resolved index `< anchor_index`)."
   is amended to: *explicit ids for non-anchor rungs — strictly below the anchor as frozen, **or the
   single rung strictly ABOVE the anchor under a recorded premium approval**.* Zero-step cells still
   NEVER return the anchor's own id (the gated-top-rung protection is untouched).
2. **The premium branch (R-16, R-22; premium-id pin per freeze-gate fold #1).** The premium id is
   **`models.premium.offer` itself** — never derived by ladder walk. The branch fires iff **all four
   conjuncts** hold at resolve-time: `models.premium.approved == true` ∧ `work-class ∈
   models.premium.scope` (critical | coding only — economy never, R-9) ∧ **the `offer` rung sits
   EXACTLY ONE rung strictly above the anchor in the family ladder** ∧ `mode == "advanced"`. ANY other
   offer↔anchor relation ⇒ **NO FIRE + surfaced** (board NOTE): `offer == anchor` (e.g. anchor already
   fable); offer 2+ rungs above (e.g. a hand-edited mythos over an opus anchor — approval never
   escalates past one rung); offer below the anchor. `resolve()` then returns the explicit `offer` id
   (inherit would silently give the session model; explicit is mandatory).
3. **grantedMode lapse (R-22/R-34).** The approval record carries the mode it was granted under
   (`grantedMode`). A re-entrant run with `mode ≠ grantedMode` LAPSES the approval (bootstrap clears
   `approved`; the next preflight re-asks). This is the fourth conjunct's persistence arm.
4. **Any-failure run-lapse + the OMIT terminus (R-25, R-38).** ANY premium dispatch failure lapses
   `approved` for the remainder of the run — one fallback step only: **premium → OMIT/inherit at the
   anchor rung** (never an explicit anchor id; tracks mid-run `/model` switches; preserves the frozen
   "never re-selects the anchor as a terminus" discipline). No re-offers, no per-task retry (the exact
   retry-storm R2 exists to prevent).
5. **R2 auth carve-out, premium rung ONLY (R-30).** The frozen R2 text —
   > "EXCEPT **HTTP 401/403** (auth/quota) which surface as a real error (never a silent downgrade on a
   > billing problem)"
   — is amended for the premium rung only: premium 401/403 ⇒ **premium-unavailable**: OMIT-inherit +
   LOUD surface (board DECISION + ledger `degraded {scope:"premium", reason:"auth-40x"}` + handoff note)
   + approval LAPSED for the run. Rationale: R2's raise protects BASELINE dispatch (misconfig = stop);
   premium is an optional elevation whose failure has a semantically-correct safe fallback — the anchor,
   the exact no-approval behavior. Unattended survival wins; never silent. **Baseline rungs: R2
   unchanged, including the 401/403 raise.**
6. **Untouched invariants (stated so the gate can check):** R1 monotonicity
   (`essential-coding ≤ standard-coding ≤ anchor`) is below-anchor arithmetic and is unaffected; the R2
   ≤2-step-down bound for baseline chains is unaffected (premium has its own one-step chain); the
   inline-eval M4-L7 carve-outs are unaffected (inline eval is economy class — structurally outside
   `premium.scope`).

## §4 Backward-compatibility matrix (every leg: absent ⇒ what)

| # | Surface (absent / unconfigured) | Behavior | BC status |
|---|---|---|---|
| 1 | `contextAutonomy` absent, **one-shot** shape (incl. pre-v0.2.1 configs) | Rotation UNCONDITIONAL | **DELIBERATE BC DEPARTURE (R-37, D147).** Rationale: protective + additive; the selfhandoff prose always mandated the trigger (never wired); degradation stays graceful (no gauge/hooks ⇒ deterministic rotation). The ONE departure in this initiative. |
| 2 | `contextAutonomy` absent, **incremental** shape | OFF (no intra-sprint refresh; boundary handoffs already rotate) | BC preserved (R-18/R-28); readiness WARN surfaces it (R-29); never flipped mid-roadmap. |
| 3 | `contextTrigger` absent | 0.70 default, only where rotation is active | BC (pure default). |
| 4 | `models.premium` absent | Frozen model-tiering behavior byte-for-byte; no premium branch | BC structural (§3 gating clause). |
| 5 | `models` block absent entirely | `resolve()` `None` everywhere ⇒ inherit (R3) | BC unchanged — this initiative never touches the absent-block path. |
| 6 | Gauge absent / stale / user-bridge-only | Deterministic N-wave rotation / percentage-only triggering | Fail-safe by design (CA-L3/L4; CA-L2 degrade). Never silent. |
| 7 | User statusline exists | Chain or skip; NEVER clobbered; user's bridge file untouched | BC hard guarantee (CA-L1). |
| 8 | SessionStart/PreCompact hooks absent | AGENTS.md standing line + kata-orient rebuild = the manual re-anchor path | Degradation, surfaced (CA-L20). |
| 9 | Host auto-compact DISABLED | No backstop exists ⇒ preflight WARN (attended) / BLOCK (walk-away + stranding conjunction) | CA-L17 + CA-L25. |
| 10 | `.kata-settings.json` new keys absent | Marker absent ⇒ forced first run (designed, OP-5); hostPosture recomputed anyway (R-42) | Additive keys; existing keys/machinery untouched. |
| 11 | Pre-existing HANDOFF.md without `kind:` | Read as unknown kind; never gates | Additive frontmatter (CA-L21). |
| 12 | Ledger rows v1/v2 | Read unchanged; v3 fields nullable-additive; no backfill | D142 precedent (CA-L40). |
| 13 | Installer: existing installs | Frozen five byte-unchanged; base dirs appear on next install/`--update`; non-kata dirs never clobbered | Additive (CA-L42/L43); never-git + stdlib-only hold. |
| 14 | Adapter primitive (c) absent | Handoff + PROMPT-operator-to-rotate; unattended bounded by one window, surfaced at preflight | Contract degradation text (CA-L38). |
| 15 | Adapter primitive (b) absent | Budget-overrun enforcement degrades to compliance + livenessDeadline escalation, surfaced at preflight | R-40 (CA-L38). |
| 16 | `.kata-settings.json` corrupt | Lenient read + fail-closed write ⇒ loud surface pointing at the file; never loop | C-3 (CA-L37). |
| 17 | kata statusline writes `%TEMP%/kata-ctx-<session_id>.json` on every tick (incl. non-kata cwd), one file per `session_id` | Observability-only bridge write; the boundary-eval bridge selection (newest-by-mtime) **never depends on a kata cwd** and **never gates** — an absent/ambiguous bridge falls to deterministic rotation (§4 row 6) | **Benign + deliberate (LOW-5).** The gauge must not depend on where kata runs (CA-L1), so the tick writes unconditionally; the write is an on-absent-config side effect that is observability-only, never a gate. **Known-minor:** the files are never cleaned — one small JSON per `session_id` accumulates in `%TEMP%`. |

## §5 Per-platform degradation matrix (RESEARCH-CROSS-PLATFORM.md; docs-only for non-Claude in v0.2.1)

| Platform | Gauge for kata | Host knob | Resume primitive | v0.2.1 kata policy (the CA-L39 docs row) |
|---|---|---|---|---|
| **Claude Code** (the live leg) | Statusline bridge file (chained superset, CA-L1/L2); staleness-checked | `autoCompactWindow` settings.json key (recommend-only, CA-L15/L16); `autoCompactEnabled` preflight-checked | Host compaction + SessionStart(compact) re-anchor (= primitive (c) binding) | Full loop: gauge-driven trigger → handoff → host compact → hook re-anchor. Fallbacks at every leg (§4 rows 6–9). |
| **Kiro** | **NO** (interactive `/context show` + IDE meter only) | CLI retention knobs only; **no trigger-threshold knob**; IDE ~80% fixed | `/chat resume` (compaction spawns a new session) | **Deterministic-rotation-only.** Hook-enabled configs are higher-risk (issue #5527 auto-compact hard-fail loop, unconfirmed); headless compaction behavior docs-silent — flag in docs. |
| **Codex CLI** | **YES — best-in-class** (rollout JSONL `token_count` tailing; OTel `task.compact`) — reverse-engineered schema, parse defensively | `model_auto_compact_token_limit` (tokens) | `codex resume --last/<id>` | Full ladder: gauge → lowered limit / proactive `/compact` → resume-restart. Must-guard: 402-hang wall-clock watchdog; shared 5-hr quota on ChatGPT-plan auth (prefer API key unattended); non-convergent compaction ⇒ keep deterministic rotation as backstop. |
| **Copilot CLI / cloud** | **PARTIAL/UNTRUSTED** (`statusLine.command` experimental; % wrong per #1957); PreCompact hook = coarse event | **NO KNOB** (~80% auto, ~95% pause) | `--resume`/`--continue`/`--session-id`; cloud = unassign/reassign (fixed 1-hr timeout) | **Deterministic-rotation + PreCompact-event-driven**, never gauge-driven. Latency watchdog for #2755 headless state creep (periodic process recycle on 8-hr runs). |
| **Cursor** | **NO** (no documented context-% surface anywhere) | **NO KNOB** (silent auto-summarize; manual `/summarize` only) | `--resume`/`--continue`; Cloud Agents (architectural long-run) | **Deterministic-rotation-only** + resume checkpoint-restart + hang watchdog (headless exhaustion behavior undocumented). For real long autonomy, prefer the Cloud-Agents scoped-task pattern. |
| **Gemini CLI** | **YES** (official `--output-format json/stream-json` `stats` token counts; on-disk `chats/` side-channel) | `model.compressionThreshold` (fraction, default 0.5 — verify installed version; name churned) | `--resume` (+ 30-day retention), exit 53 on turn cap | Full ladder: JSON-stats gauge → tuned threshold → `/compress` → resume-and-continue on hard token errors (#8132/#9775). Must-guard: cap single-turn tool output; pin the model (auto-switch mid-session can hard-fail). |

3 of 5 non-Claude platforms have NO host knob and/or no gauge (SR-6) ⇒ **internal-threshold-primary is
the only portable architecture** (OP-3 confirmed by research). The RESEARCH doc's 15 Confidence Gaps are
carried as re-verify items on each platform's docs page (§8).

## §6 Acceptance criteria (default-FAIL, runnable; CA-12 frozen here)

1. **CA-A1 — The live proof cycle (CA-12, R-2).** In a THROWAWAY Claude profile: drive a run to the
   trigger → observe warn → handoff written+committed at a wave boundary (`kind: self`) → host
   auto-compact fires at/before the recommended window → SessionStart(compact) re-anchors on
   HANDOFF.md → the next task completes with **zero task loss** AND the resume is graded on
   **context-quality restoration** (kata-orient 3-tier reload complete, budget-capped), not just task
   continuity. Also measured empirically in the same profile (GROUNDING G4): the actual auto-compact
   firing margin, bridge freshness in unattended mode, the PreCompact input schema, the hook
   sync-time budget (CA-L17 UNVERIFIED item), and **that the gauge's `total_tokens` reflects
   `autoCompactWindow` capping** (fold #6 — the CA-L5 post-cap claim is currently ungrounded; this
   grounds it). Fixture pin (fold #4): the live-proof run's config carries `inlineEval: "telemetry"`
   (the CA-L10 substrate), stated in the fixture definition.
2. **CA-A2 — SMOKE-2/3 identical-protocol rerun (A/B).** Re-run the SMOKE-2/3 protocols byte-identical
   on-arm vs baseline: conductor context-per-task (gauge-read at each boundary) shows a **gated DROP**
   on-arm, with **identical run outcomes** (same gate verdicts, same green numbers). The DROP threshold
   is deliberately NOT a number invented here — it is **judgment-graded at the operator merge gate**
   (fold #7). Fixture pin (fold #4): both arms state their `inlineEval` posture in the fixture
   definition (`"telemetry"` on-arm; baseline as originally run).
3. **CA-A3 — Degradation-path tests (each a separate arranged run/fixture):** (a) no-gauge ⇒
   deterministic N-wave rotation fires per CA-L4; (b) no-hooks ⇒ AGENTS.md-line manual re-anchor path
   works; (c) auto-compact DISABLED ⇒ preflight WARN (attended) and BLOCK (walk-away stranding
   conjunction, R-12); (d) stale bridge (timestamp > 300s) ⇒ fallback leg engaged, surfaced.
4. **CA-A4 — Never-clobber:** install/preflight against a profile with an existing user statusline ⇒
   user's statusLine + bridge file byte-unchanged; kata offers chain-or-skip (CA-L1).
5. **CA-A5 — The NO-FIRE case (R-8):** an under-threshold session completes with ZERO handoff
   refreshes and zero rotation events (no churn).
6. **CA-A6 — Corrupt-settings surface (C-3):** a corrupted `.kata-settings.json` ⇒ forced-first-run
   detection + loud surface naming the file + clean stop; NEVER a loop (test asserts single pass).
7. **CA-A7 — Premium resolver matrix (§3):** unit tests over all four conjuncts (each false ⇒ no
   premium id); premium id EXPLICIT == `models.premium.offer` when all true; failed premium ⇒ one-step
   OMIT + `approved` lapsed for the run; premium 401/403 ⇒ OMIT + loud degraded entry (never a raise);
   baseline 401/403 still raises; mode-change lapse cleared by re-entrant bootstrap. **One-rung edge
   cases (fold #1):** anchor=fable + approved fable offer ⇒ NO FIRE (must NOT elevate to mythos);
   anchor=sonnet + approved fable offer (2 rungs above) ⇒ NO FIRE + surfaced. Absent `models.premium`
   ⇒ the existing model-tiering suite passes byte-unchanged.
8. **CA-A8 — BC matrix executable rows:** absent `contextAutonomy` + incremental ⇒ no rotation
   (row 2); one-shot ⇒ unconditional rotation incl. a pre-v0.2.1 config fixture (row 1, the D147
   departure — the test NAMES it); absent keys ⇒ rows 3–5, 10–12 hold.
9. **CA-A9 — Installer fix:** fresh install into a tmp host dir (symlink AND copy modes) ⇒ tier-family
   base payloads (`kata-grill/RUBRIC.md` etc.) resolve from every installed tier skill; the frozen five
   verified byte-identical (hash check, the STATE.md discipline); uninstall removes only kata-managed
   entries.
10. **CA-A10 — Standing gates:** pytest green (2505 baseline + new), validator 48+/0/0,
    Snyk medium+ 0 on new first-party code, bump-on-modify honored on every touched SKILL.md.
11. **CA-A11 — Test-at-build fixture rows (fold #8; each becomes a runnable test in the PLAN):**
    (a) over-briefing WARN — a dispatch with startup load > 0.30 surfaces the CA-L9 WARN (and > 0.40
    is a plan/freeze mandate failure); (b) continuation-report path — a task exceeding its quantum
    checkpoints, returns a continuation report, and the pt-N+1 fresh dispatch resumes from the anchor
    with index continuity (CA-L10); (c) report size contracts — a worker final report is
    verdict+pointer inline with bulk at the `.kata/reports/` path (CA-L22/L23); (d) allowlist checklist
    WARN — a host allowlist missing a CA-L26 pattern class produces exactly the enumerated WARN;
    (e) marker re-arm — a `.kata-version` `gitSha` change with the marker present forces the CA-L36
    first-run pass ("unknown"/absent-stamp fixtures assert the skip clause).

## §7 Dependency manifest

**Verified: NO new external dependencies.** `kata.dependencies.json` for this initiative = empty
(no entries). The install path stays **stdlib-only** (kata_install.py imports json/os/shutil/sys/pathlib
only — verified; the IP-A/D129 stdlib-only invariant holds). New runtime pieces (chained statusline
wrapper, hooks extensions, bootstrap/preflight logic, telemetry columns) are Python stdlib + existing
tools modules. Nothing to provision at PRE-FLIGHT beyond the already-approved set.

## §8 Named deferrals + carried cautions

Deferred — NAMED, never silent:
- **LD7** — host-fallback × attempt topology (worker respawn semantics). Primitive (c) governs
  CONDUCTOR sessions only (CA-L38); LD7 remains named-DEFERRED exactly as ADAPTER-CONTRACT-M4 records it.
- **Non-Claude live legs** — Kiro/Codex/Copilot/Cursor/Gemini get §5 docs + contract-conformance
  paragraphs only in v0.2.1 (R-35); live proofs are future milestones. The RESEARCH doc's 15
  Confidence-Gap items ride each platform's docs page as re-verify-before-build flags.
- **Research/debug class extras** — untouched by this initiative (M4 P2 named-deferred producers stand).
- **τ calibration** — unchanged M4 track (≥3 instrumented runs); this initiative only ADDS ledger
  columns (CA-L40) that future calibration consumes.
- **OP-1** — no PokeVault/MindBridge deploy in this initiative (operator pre-lock; deploy is the next
  phase after v0.2.1).
- **Windsurf** — cut from the cross-platform scope (OP-6).
- **Premium disclaimer TEXT** — a docs/build pass (CA-7b), not a design item.

Carried planning note (SR-7/SR-17): the `kata.graph.json` cache exists for version-up grounding (RUBRIC
Phase 0.4), but its top PageRank ranks are vendored `research/**` noise — any blast-radius use at PLAN
time MUST apply a path-prefix filter; the top core modules (gate_emit / run_result / mutation_check) are
NOT in this initiative's expected blast radius, which the planner should treat as a drift tripwire.

Cautions C-1..C-4: all RESOLVED into owning sections — C-1 (acceptedDefaults schema) pinned at CA-L37 +
§2; C-2 (allowlist checklist) enumerated at CA-L26; C-3 (corrupt settings) resolved at CA-L37 + tested
at CA-A6; C-4 (fail-closed settings-writer discipline, gate v6) pinned at CA-L37 + §2. Freeze-gate
attack surface, explicitly invited: every `[TUNABLE]` number (§9), the two `[VETO-FLAG]` items
(CA-L22 home, CA-L25 strictness), the R-37 departure (CA-L33), the `contextTrigger` key name (§2), and
the R-43 comparator pins (§2 — the ledger names the DESIGN freeze-gate as the next fresh adversarial
pass over them).

## §9 Tunables table (locked structure, tunable value)

| Tunable | Default | Provenance |
|---|---|---|
| Conductor trigger fraction (`contextTrigger`) | **0.70** of effective window | R-1 operator number, reconciled R-7/R-13; smart-zone rationale |
| Worker work quantum | **40pp** of worker window above startup load | R-13 (derived, never user-configured) |
| Worker hard cap | **0.80** of worker window | R-13 guard (i) |
| Over-briefing WARN threshold | startup load > **0.30** | R-13 guard (ii) / R-26 (0.40 = mandate, not tunable — cap-wins) |
| Gauge staleness | **300 s** | Self-resolved default; freeze-gate attacks |
| `est_wave_burn` (N-wave fallback) | **40k tokens** | Self-resolved default; replaced by CA-L40 telemetry (SMOKE-3 seeded n=1) |
| Backstop gap fallback | **0.10 × effective window** | R-21 (telemetry-derived once rows exist, OP-3) |
| Worker-burn estimator (freeze WARN) | tokens-per-chunk, seeded from ledger `perTask` medians | R-19 |
| Prime-frame sprint fraction | **0.40** (existing, UNTOUCHED) | D83 — recorded here only to state it is not edited (CA-L8) |
| Backstop key floor | 100k tokens | HOST-FIXED (G1: `int().min(1e5)`) — a constraint, not a kata tunable |

— FROZEN. Changes are deliberate re-freezes via the supersede/amendment path, never edits-in-flight.
Hand to kata-plan for the task-level execution plan. Deferred-security note: docs-only deliverable
(one .md); no first-party code written; Snyk scan not applicable to this compile step (per the
security-at-inception rule).
