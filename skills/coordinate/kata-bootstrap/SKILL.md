---
name: kata-bootstrap
description: >-
  Pre-loop configurator and on-ramp: evaluate readiness (via kata-readiness), infer run-shape + mode +
  grill-depth + delivery from the goal, state the plan in plain language, surface one dial for how careful
  and how often to check in, then write kata.config and launch the loop. Re-entrant — reads an existing
  config to reconfigure. Invoke to start or reconfigure any kata run.
license: Apache-2.0
version: 0.1.2
category: coordinate
status: experimental
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

## Phase 3 — write kata.config + launch
Write `kata.config` (JSON, branch root) per `protocol/config.md`: `mode`, `modules`, `effort`, `tiers`,
`ingested`, `preflight`, `bakeoff`, `skillVersions`, **`runShape`**, **`target`**, **`delivery`**, **`roles`**, **`models`**. Bootstrap writes the config
**by construction** — it does NOT re-validate it (that is [[kata-orchestrate]]'s fail-closed load-guard, GB12;
a second validation pass here would be redundant bloat). Then hand off to the loop ([[kata-orchestrate]]).

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
