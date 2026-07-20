---
name: kata-bootstrap
description: >-
  Pre-loop configurator and on-ramp: evaluate readiness (via kata-readiness), infer run-shape + mode +
  grill-depth + delivery from the goal, state the plan in plain language, surface one dial for how careful
  and how often to check in, then write kata.config and launch the loop. Re-entrant — reads an existing
  config to reconfigure. Invoke to start or reconfigure any kata run.
license: Apache-2.0
version: 0.7.0
category: coordinate
status: beta
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Write, AskUserQuestion]
source: >-
  adapted-from GSD discuss-phase Q&A model + docs/MODES-DESIGN.md D24c composition ladder (KataHarness design)
tags:
  - kata/coordinate
  - kata/spine
  - bootstrap
  - composition-ladder
---
# kata-bootstrap — compose a run, write kata.config, launch

The on-ramp. Reads the goal, **infers** the right run shape, and states the plan in plain language before asking
anything. Interaction uses **structured choice-or-text questions** (offer 2–4 options, recommendation first,
always a free-text escape) — *(adapter binding: Claude → `AskUserQuestion`; a plain CLI → numbered options + a
free-text prompt)*. Voice per `protocol/persona.md`.

> **Full Kata Loop?** `kata-bootstrap` is the on-ramp for the **harness middle** (compose → orchestrate). For
> a complete **Kata Loop** run — a real initiation that captures a frozen `INTENT.md` first, and a closeout
> with the understand-map + human decision + loop-back after — start from the [[kata-loop]] conductor instead
> (`initiation → harness → closeout`). `kata-loop` calls this skill for the middle. Direct `kata-bootstrap` use
> stays valid and unchanged (BC: the loop is optional).

## Phase 0 — readiness (always)
Invoke [[kata-readiness]]. On **BLOCK**, stop and surface the blocker (don't compose a run on a broken env). On
re-entrant detection (an existing `kata.config`), offer **same-as-last / step a family up a tier / change
run-shape** instead of cold-start. WARNs are surfaced, not blocking.

### Phase 0 — force-run marker (CA-L36/CA-L37, first-run gating)
Before composing, call `kata_settings.first_run_required(home)` (E2). It returns
`{required, reason, clause_skipped}`: **an absent marker OR a `.kata-version` `gitSha` mismatch**
(`firstRunVersion ≠` the stamp's `gitSha`) ⇒ force the FULL first run — re-armed on every install/upgrade
(a fresh install or `--update` writes a new stamp, and a new posture pass is worth one forced full run).
Stamp absent OR `gitSha == "unknown"` (the dev in-repo path) ⇒ the version clause is SKIPPED and marker
absence alone forces. On a completed forced first run, call `kata_settings.record_first_run(git_sha)` to
stamp `firstRunCompletedAt` + `firstRunVersion`.

**Corrupt settings (C-3, D136 fail-closed):** the marker READ is lenient (a corrupt `.kata-settings.json`
reads as *absent* ⇒ force), but `record_first_run` **fails closed** — it cannot persist over a corrupt
file. Bootstrap MUST detect that write failure, surface **LOUDLY** pointing at the corrupt file path, and
**stop; never loop** (a forced first run that can't record its completion would otherwise re-force forever).

### Phase 0/1 — premium lapse executor (CA-L31)
On re-entrant detection, compare the composed `mode` against the recorded `models.premium.grantedMode`. A
run that **changes mode LAPSES** the approval: the lapse executor is BOOTSTRAP — re-entrant Phase 0/1
detecting `mode ≠ grantedMode` **clears `approved`**, and the next preflight bundle (Phase 2.5) re-asks.

### Phase 0b — sprint-boundary routing (sprint-cadence D80 — bootstrap is the boundary router)
When the re-entered config has `delivery.shape == "incremental"`, read [[kata-readiness]]'s **sprint-progression
verdict** (`{sprintIndex, gateStatus, boundary}`, rebuilt from the git trail) and **route** — this is the entry
host for the boundary; `kata-orchestrate` stays sprint-blind (D24d), so the dispatch lives here:
- **`boundary: gated`** (sprint gate green, awaiting the boundary) ⇒ invoke **[[kata-sprint]]** to run the G1–G4
  course-correct (the only place steering happens), then proceed to the next sprint plan.
- **`boundary: dirty`** (mid-sprint, uncommitted work) ⇒ **resume the active sprint** via [[kata-orchestrate]]
  (no boundary, no steering — the sprint is a one-shot in flight).
- **no open roadmap** ⇒ normal composition (Phases 1–4 below).
A **red** sprint is never a boundary — it routes through escalation (`protocol/escalation.md`), not here.

## Phase 1 — infer + plain-language statement (WS-3 L5)

**Before asking anything**, read the goal and infer the full run plan. State it in plain outcome language:

> *"I'll do a thorough build and check with you at the end."*
> *"I'll work through this step-by-step and pause for your sign-off at each stage."*
> *"This looks like a light update — I'll run a quick pass and show you the result."*

The statement covers what the run will do, how careful it will be, and when you will hear from it. The human
confirms, corrects, or continues — not reads a config form.

**What is inferred:**
- **Run-shape** (`individual / batch / version-up / debug / advanced`) from the goal's character — is it a new build, a
  change to an existing repo, a batch job, a systematic debug pass? Each is a **preset** (see `resources/run-shapes.md`) that pre-fills
  `mode` + `modules` + `target`. **`version-up` and `debug` are built and wired** — `debug` runs the P1–P3
  pipeline ([[kata-comprehend]] → [[kata-deviate]] → [[kata-characterize]] → [[kata-debrief]], gated on module
  `kata/module/debug`); `version-up` uses [[kata-graph]] ingestion. `batch` (Spec B) writes a valid config now,
  but its **concurrent** best-of-N arms remain execution-pending (sequential + k-repeat is built). For
  **version-up** and **debug**, additionally collect `target.path` (the existing repo) and `target.baselineGate`
  (the command that must be green before *and* after).
- **Mode** (`essential / standard / advanced`) from goal complexity and stated urgency.
- **Grill-depth** (`skip / light / standard / full`) from priming-prompt richness and ambiguity — [[kata-readiness]]'s
  Scope-3 recommendation is the starting point.
- **Delivery** (`one-shot` vs. `incremental`, `always-stop` vs. `auto-continue-while-green`) from whether the
  goal implies a long multi-phase build or a single run. `individual` ⇒ one-shot · `batch` ⇒ one-shot ·
  `version-up` ⇒ ask · `debug` ⇒ ask. `delivery.boundary` defaults `always-stop` (control-first, GB6).

**Do not present a config form.** State the inferred plan as outcomes. The human edits it in plain language;
the configuration follows from the edit.

## Phase 1.5 — the one dial: how careful / how often (WS-3 L5)

Surface **exactly one** plain question:

> *"How careful and how often should I check in with you?"*

Offer **three named positions** (recommendation highlighted based on the inferred plan):

| Position | Plain meaning | `mode` | `tiers["kata-grill"]` | `delivery.boundary` |
|---|---|---|---|---|
| **Lighter** | Move fast, check only at the end | `essential` | `skip` or `essential` | `auto-continue-while-green` |
| **Standard** *(default)* | Steady build, check at the end | `standard` | `standard` | `always-stop` |
| **More careful** | Thorough + check in more often | `advanced` | `standard` or `advanced` | `always-stop` |

**Dial → config field mapping (K5 — no new field):**
- **More careful** ⇒ higher `mode` (`advanced`) + deeper grill (`tiers["kata-grill"]` = `standard` or `advanced`)
  + `delivery.boundary = "always-stop"`.
- **Standard** ⇒ `mode = "standard"` + `tiers["kata-grill"] = "standard"` + `delivery.boundary = "always-stop"`.
- **Lighter** ⇒ lower `mode` (`essential`) + lighter or skipped grill (`tiers["kata-grill"]` = `essential` or
  `"skip"`) + `delivery.boundary = "auto-continue-while-green"`.

This is the only question the default path asks. A free-text escape is always available (the human can say
"somewhere between careful and standard" and bootstrap resolves it). The mapping above is the authoritative
translation: whatever the human says in plain language, it maps onto these three existing `kata.config` fields
and no others. (K5: no new config field is ever introduced here.)

The **autonomous-reliability floor is always on regardless of dial position** (default-FAIL + the RS research
subagent *(loop-cognition phase; named, not yet wired)* + a `kata-defer` assumption/ambiguity log surfaced at
the gate/handoff). The dial controls *up-front certainty* and *check-in frequency*, not the quality gate.

Frame grill-depth as *how much up-front certainty you want before work starts*, not a quality knob. Grill ↔ RS
are one ambiguity-resolution spectrum: the lighter the grill, the more ambiguity is resolved in-loop rather
than up-front. The default-FAIL `kata-evaluate` gate runs on **every** rung. (Equivalent to a
`tiers["kata-grill"]` cross-tier pick, surfaced here because it is the highest-leverage certainty dial — the
advanced drawer can still override it individually.)

## Phase 2 — advanced settings drawer (D24c, available not default)

> **Advanced settings** — available if you want them. Most runs don't need this.

The full composition ladder (D24c) is here, behind this drawer. Open it only if needed:

1. **default → go** — accept the preset's recommended mode and launch. The floor is never punishing.
2. **add modules** — à-la-carte beyond the preset bundle (D20).
3. **cross-tier pick** — override a single family's tier (`tiers[family]`) without changing `mode`
   (e.g. pull `kata-grill-advanced` into a Standard run for one cycle).
4. **external/custom ingest** — name a skill + declare its slot (`needs`/`produces`/`slot`) → `ingested[]`.

Surface ONLY the `kata.config` fields the chosen run-shape needs (progressive disclosure) — the default→go path
stays one keystroke; advanced fields appear only when this drawer is opened.

**Cost preview** (also in the drawer): sum the `cost-weight` of every skill the composed run will invoke
(authority: `.planning/SKILL-COST-RATINGS.md` / each skill's frontmatter). Show the total + per-skill breakdown.
The cost preview is shown here for runs opened via the drawer; on the default path it is surfaced as a single
line in the plain-language statement ("this is a medium-cost run").

## Phase 2.5 — the approval bundle (preflight collection; CA-L24)

**Bundle collection is a NEW bootstrap step between Phase 2** (the advanced drawer) **and the Phase-3
config write** — **bootstrap collects; kata.config is written AFTER, with `models.premium.approved`
recorded from the collected answer.** Bootstrap orchestrates; [[kata-preflight]] collects (CA-L31 gate
home). The existing [[kata-orchestrate]] PRE-FLIGHT gate stays **enforcement-only** — it verifies /
provisions the approved set and NEVER prompts a second time.

**The ONE bundle** — **Collected ONCE**; **zero expected prompts for 8 hours after**. Every slot is
approved like an install, **never an implied side effect**:

1. **Dependency installs/downloads** — the freeze-approved set (existing [[kata-preflight]] scope).
2. **Permission allowlist** — the CA-L26 fixed-checklist coverage WARNs.
3. **The premium gate** (Leg G) — collected here; full semantics + the cost disclaimer live in
   [[kata-preflight]].
4. **The compact-window recommendation** (CA-L16 backstop) — **recommend-never-write**: Kata **never
   writes user settings silently**; the recommendation is surfaced and applied only with permission (set
   above the internal target, or not at all if the default suffices). It is **RECOMPUTED every run**
   (CA-L37/R-42 — `hostPosture` is audit-only and never suppresses it). The executable, consent-gated
   apply path is `kata_install.py --install-hooks --auto-compact-window N` (D154); the loop itself
   still never writes the key.
5. **The host-settings write slot** — installing the SessionStart(compact) hook and the statusline /
   wrapper entries IS a write to `~/.claude/settings.json`, so it is an explicit bundle slot approved like
   an install. Merge discipline: **hooks arrays are APPEND-NEVER-REPLACE; `statusLine` is only ever
   chained-or-skipped** (the CA-L1 never-clobber guarantee, generalized to every settings key kata touches).
6. **The stranding verdict (CA-L25)** — computed by [[kata-preflight]] inside this same collection (its
   *The stranding verdict* section owns the semantics): a walk-away-configured run with the full stranding
   conjunction ⇒ preflight `blockers` entry (`status: blocked`, launch refused); attended ⇒ WARN + proceed.
   The host-posture question that resolves `read_host_autocompact`'s unknown rides in this bundle.
7. **The second-brain recommendation (the optional-target ask, SB / EV-1)** — when composing a run with
   `vaultDir` unset AND `kata_settings.vault_recommendation(kata_settings.read_settings(home))` recommends,
   surface ONE structured recommendation question (recommendation-first, 2–4 options, free-text escape):
   **link PokeVault** (`git clone https://github.com/taurran/pokevault` + bootstrap, or install) · **name
   their own vault path** · **decline**. Persist the answer at answer time — **accept-a-path** ⇒ the existing
   `--vault-dir`/settings write path (`kata_settings.write_settings(..., vault_dir=<the path>)`); **decline**
   ⇒ `kata_settings.record_vault_decline()` (EV-1 — surfaced once, re-armed only by an install/upgrade). This
   slot and the [[kata-initiate]] Phase-2 vault ask read the **SAME live pull-check** (`vault_recommendation`):
   if kata-initiate already persisted the answer this session (an accept-a-path write or a recorded decline),
   the pull-check returns `recommend=False` and this slot is **skipped — it never re-asks** (the same-session
   once-guard, HIGH-3). Second brain stays **optional** — never a requirement; the question **NEVER blocks**:
   a headless/no-TTY composition skips it (the floor: the learn feed is simply a no-op, BC1). An accepted
   path sets `vaultDir`, so the Phase-3 `engram.learnFeed.dir` seeding below picks it up unchanged.

8. **The ADVANCED advisor consent (advisor-executor, G-9 — ADVANCED runs ONLY; independent of the premium
   gate).** In **advanced** mode, present the advisor consult as a **pre-checked, one-veto-able consent** at
   composition — "on by default" operationally = pre-checked; the operator may veto it. **Composition itself is
   consent** (the `models.adaptive` compose-consent precedent, Phase 3 below): the answer sets `approved` in the
   Phase-3 advanced `advisor` block, and planning consults are thereby legal in advanced. This consent is
   **DECOUPLED from `models.premium`** — a premium decline never touches the advisor grant and this advisor veto
   never touches the premium offer (S-16). **Headless/non-TTY advanced composition ⇒ the pre-checked consent
   STANDS without an interactive veto** (G-9 — composition is consent; the veto is the attended affordance),
   surfaced in the composed-config summary, never silent. **STANDARD and ESSENTIAL are NOT asked here** —
   standard opts in later at [[kata-preflight]] (once per RUN, post-freeze); essential gets no advisor and no
   ask (G-8).

Record the operator's accepted answers via `kata_settings.record_accepted_defaults(entries)` (the C-1
`{value, v, at}` schema) and the host posture via `kata_settings.record_host_posture(posture)` — both
**audit-only, last-write-wins, never consulted for suppression**.

## Phase 3 — write kata.config + launch
Write `kata.config` (JSON, branch root) per `protocol/config.md`: `mode`, `modules`, `effort`, `tiers`,
`ingested`, `preflight`, `bakeoff`, `skillVersions`, **`runShape`**, **`target`**, **`delivery`**, **`roles`**, **`models`**, **`securityScan`**, **`inlineEval`**, **`advisor`** (advanced/standard only — §3.4).
**`models.adaptive` (D150 — compose = consent):** every Phase-3 composition writes the FULL `adaptive`
block EXPLICITLY (all five keys, `protocol/config.md` defaults: `failBumpAt: 2, streakDownAt: 3,
planComplexityDownshift: true, evaluatorEscalate: true, l2: false`) — a config bootstrap composes is
new consent, so adaptivity is baked in going forward; a config the loop merely LOADS without the block
keeps every adaptive leg OFF (no retroactive flip — the D147/CA-L34 discipline). In ADVANCED mode with
the premium offer approved, write the OBJECT-form `premium.scope` (`{events: <the 7-event registry>,
budget: {calls: 10}}`) unless the operator edited the event list or budget at the gate; other modes
never write a premium block.

**`advisor` block (advisor-executor — compose BY CONSTRUCTION in advanced + standard, NEVER essential; §3.4/§4;
DECOUPLED from `models.premium`).** Write the `advisor` block per mode; **essential composes NO `advisor` block**
(absent ⇒ OFF strictly, S-4/G-8):
- **ADVANCED:** `{"enabled": true, "approved": <the Phase-2.5 slot-8 consent>, "grantedMode": "advanced",
  "budget": {"calls": 10, "reserved": 2}, "hooks": {"failThreshold": 2, "rerollTrigger": 2,
  "fixLoopCeiling": true}, "phases": ["planning", "execution", "fix-loop"]}`. `grantedMode: "advanced"` is
  **cosmetic** — the advanced mode-arm ignores it; recorded for config completeness (S-23d). Planning is
  advisor-legal in advanced.
- **STANDARD (until the preflight opt-in):** `{"enabled": true, "approved": false, "budget": {"calls": 5,
  "reserved": 1}, "hooks": {"failThreshold": 2, "rerollTrigger": 2, "fixLoopCeiling": true}, "phases":
  ["execution", "fix-loop"]}`. **`grantedMode` is ABSENT** on the composed-and-not-yet-opted-in block —
  [[kata-preflight]]'s once-per-RUN ask writes `approved: true, grantedMode: "standard"` on accept, or leaves
  `approved: false` with `grantedMode` ABSENT on decline (S-26b). **Standard planning has NO advisor** — the
  honest temporal consequence of the post-freeze placement (G-9). `phases` is **documentation of the G-9
  availability matrix, NOT an independent switch** — the gate + hook wiring enforce availability, never this
  field.
- **Never inferred from `mode` on load** — an absent block is OFF even in advanced; a builder must never infer
  the grant from the mode (G-9/S-4). Both compositions round-trip `kata_models.validate_advisor_block` clean by
  construction (T1's tests guard this — a composed default that bricks the load-guard is a producer bug).
Surface the advisor posture in the composed-config summary (never silent).

Bootstrap writes the config
**by construction** — it does NOT re-validate it (that is [[kata-orchestrate]]'s fail-closed load-guard, GB12;
a second validation pass here would be redundant bloat). Then hand off to the loop ([[kata-orchestrate]]).

**Second-brain learn feed (`engram.learnFeed.dir`, SB-L7):** at config-write, seed `engram.learnFeed.dir`
from `kata_settings.default_learn_feed_dir(settings)` (`tools/kata_settings.py`) when `vaultDir` is set —
`<vaultDir>/second-brain/wiki/pages/synthesis`, computed top-down from `vaultDir`. The operator may override
the seeded path. `vaultDir` absent ⇒ leave the key unset (the learn feed is then a no-op — BC1; never invent
a feed dir).

**Security-scan posture (`securityScan`, Lever 2 / F6):** write `"when-available"` by default — run a
scan when a scanner is wired and the toolchain supports it, else degrade-and-surface (never a silent skip,
never a toolchain-shim fight). Write `"required"` only when the operator asks for a fail-closed security
gate; write `"off"` only on an explicit, surfaced opt-out. **Omitting the field is equivalent to
`"when-available"`** (BC) — so a run written without it behaves exactly as today.

**Multi-model routing (`roles`):** if the mirror conversation (via `kata-initiate` Phase 2e or the grill)
produced a confirmed per-role platform assignment, write it as the `roles` block per `protocol/config.md:27`:
`{ "<role>": { "platform": "<platform>", "model": "<model-id-if-known>" } }`.
**Omit `roles` entirely when the run is single-host** — when no confirmed off-host assignment was made, the
human declined, or no non-host platforms are installed. Absent `roles` ⇒ all roles on host (BC1,
`protocol/config.md:27`). `roles` is a `kata.config` concern only — do NOT write it to `INTENT.md`.

**`models` block — anchor write (Layer 3, R7):** At run setup, resolve the operator's session model as the
**anchor** — the reference rung for all relative tier arithmetic — and write the `models` block into
`kata.config` once per branch. The canonical written shape is:
`{ "anchor": "session", "family": "auto", "coderFloor": "sonnet" }`.

`"session"` is the default sentinel — it defers to the platform's latest top rung at dispatch when the
operator's current model is not detectable or not confirmed. If the session model is identifiable (e.g.
from `kata_settings` or the platform context), write that identifier in place of `"session"`; always refer
to it in prose as "the platform's latest top rung," never as a hard-coded model name.

Note: `"session"` is a deferred sentinel; the orchestrator substitutes it with the concrete session-model ladder short-name (haiku/sonnet/opus/fable/mythos) at dispatch before calling `resolve()`. A detected full model id (e.g. returned by the platform context) is also acceptable as the anchor value — `resolve()` normalizes it to its ladder short-name via the id map, so full-id anchors activate tiering identically to their short-name equivalents.

**R7 contract:** zero-step critical work (advanced-critical and standard-critical cells, resolved rung
`== anchor_index`) resolves to `None`/OMIT regardless — these cells **never read the anchor name** and
inherit by omission, always running at the current session model. Only **below-anchor cells** read the
anchor name to step down a rung: economy tier-down (`standard-coding`, `standard-economy`, `advanced-economy`
*(Anthropic, `−1`)*, all `essential` work). An unknown anchor (id not found in the family ladder) → `resolve()` returns `None` → inherit —
never a crash, never a forced model.

**BC:** the **absent-block path still inherits** (today's behavior, byte-for-byte). Writing the `models`
block is ADDITIVE — it supplies inputs to `kata_models.resolve()` but never alters the absent-block path.
A run written without a `models` block continues to behave exactly as before; adding the block only
activates the relative-tier resolver for below-anchor cells. Never write the block in a way that could
break the no-block path.

**Inline-eval mode (`inlineEval`, M4-L8 bootstrap default):** write `"telemetry"` for every new-run config.
`telemetry` is record-only — per-task checkpoint records plus the git-durable calibration ledger, with NO
triggers, ladder, or kills (all P1). Its one behavior delta is the worker checkpoint-commit mandate added to
the dispatch brief; that mandate's cost is exactly what the M4-P0 instrument measures. **Absent ⇒ `"off"`
(byte-for-byte BC)** — omitting the field on an existing run leaves that run unchanged. **Forward rule:**
offer `"on"` (the P1 scheduling/reroll mode) only once the harness telemetry ledger holds **≥3 instrumented
runs** — until that calibration data exists, stay on `"telemetry"`.

**Context-autonomy posture (`contextAutonomy`, CA-L32 + CA-L10 fold #4):** write `contextAutonomy: "on"`
explicitly for every new config. The key governs **incremental shapes only** — one-shot shapes rotate
**unconditionally** and never consult it (CA-L33/D147, the ONE deliberate BC departure). **Whenever
bootstrap writes `contextAutonomy: "on"`, it ALSO mandates `inlineEval: "telemetry"` or higher for that
config** — checkpoint-anchored continuation rides the M4 checkpoint stream, which exists only at
`inlineEval ≠ off`; the M4-L8 default above already writes `"telemetry"` for new runs, so this pins the
coupling additively. `contextTrigger` (the trigger fraction, default `0.70`) is shown in the **advanced
drawer only** and is **never interactively asked** (K5). Re-entrant **same-as-last from a pre-v0.2.1
config** (no `contextAutonomy` key) writes the key **at the next composition touch** per Phase 3's
write-all-fields-by-construction, **surfaced in the composition summary** (R-23) — never a silent
retroactive flip.

**Premium record (`models.premium`, CA-L27/L28):** write `models.premium: {offer, approved, scope,
grantedMode}` from the Phase-2.5 collected answer — **kata.config is authoritative** for dispatch, while
`.kata/preflight.json` carries the audit event only (once-per-run = once per kata.config). The two decline
arms are distinct — never conflate them:
- **Offer declined (the DEFAULT arm — anchor=opus ∧ mode=advanced):** record `approved: false` in the
  §2-shaped block (or write no `models.premium` block — absent ⇒ the resolver's frozen behavior
  byte-for-byte), stay at the anchor, and the run **PROCEEDS normally**. No hard-stop, no anchor pin.
- **Keep-using declined — ONLY when the session anchor is already Fable/Mythos-class:** pin
  `models.anchor: "opus"` + hard-stop advising a `/model` switch, resume after the switch (the only honest
  decline for that case — config cannot stop a Fable *session* from inheriting Fable on zero-step critical
  work; the session model is the operator's own choice).
