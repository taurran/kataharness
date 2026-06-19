---
name: kata-bootstrap
description: >-
  Pre-loop configurator and on-ramp: evaluate readiness (via kata-readiness), route by run-shape
  (individual / batch / version-up / advanced — presets over the mode axis), compose mode+modules+tiers via
  the ladder, preview cost, then write kata.config and launch the loop. Re-entrant — reads an existing config
  to reconfigure. Invoke to start or reconfigure any kata run.
license: Apache-2.0
version: 0.1.0
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

The on-ramp. Turns a one-keystroke "default → go" into an expressive composition ladder, then writes the
frozen `kata.config` (schema: `protocol/config.md`) that [[kata-orchestrate]] dispatches off. Interaction
uses **structured choice-or-text questions** (offer 2–4 options, recommendation first, always a free-text
escape) — *(adapter binding: Claude → `AskUserQuestion`; a plain CLI → numbered options + a free-text prompt)*.

## Phase 0 — readiness (always)
Invoke [[kata-readiness]]. On **BLOCK**, stop and surface the blocker (don't compose a run on a broken env). On
re-entrant detection (an existing `kata.config`), offer **same-as-last / step a family up a tier / change
run-shape** instead of cold-start. WARNs are surfaced, not blocking.

## Phase 1 — run-shape (the router, GB1)
Ask the run-shape: **individual / batch / version-up / advanced**. Each is a **preset** (see
`resources/run-shapes.md`) that pre-fills `mode` + `modules` + `target` — not a new axis. `batch` (Spec B) and
`version-up` (Spec A4) are configurable now but flagged **execution-pending** by readiness; bootstrap still
writes a valid config. For **version-up**, additionally collect `target.path` (the existing repo) and
`target.baselineGate` (the command that must be green before *and* after — the regression baseline). Describe
the version-up ingestion engine (kata-graph) in prose only; do **not** wikilink it (A4, unbuilt).

## Phase 1.5 — grill-depth dial (D71)
Offer the **grill-depth** as a first-class choice: **skip / light / standard / full** (writes
`tiers["kata-grill"] = skip|essential|standard|advanced` — the dial↔value map lives in `protocol/config.md`).
**Pre-select [[kata-readiness]]'s Scope-3 recommendation** (from priming-prompt richness) and show its one-line
rationale, but the human always chooses (choice-or-text). Frame it as *how much up-front certainty the human
wants*, not a quality knob. The **autonomous-reliability floor is always on** (default-FAIL + the RS research
subagent *(loop-cognition phase; named, not yet wired)* + a `kata-defer` assumption/ambiguity log surfaced at
the gate/handoff); the grill adds up-front certainty **on top of** it:
- **skip** ⇒ *no grill runs* — trust the priming prompt and lean entirely on the floor; ambiguity is resolved
  in-loop, not up-front.
- **light** ⇒ a shallow grill (`kata-grill-essential`, top-risk branches only) on top of the floor.
- **standard / full** ⇒ a fuller grill (`kata-grill-standard`/`-advanced`) to enrich the prompt into the frozen
  spec before execution.
This is the *priming-and-grill* control surface; grill ↔ RS are one ambiguity-resolution spectrum. The
default-FAIL gate runs on **every** rung. (Equivalent to a `tiers["kata-grill"]` cross-tier pick, surfaced
up-front because it is the highest-leverage certainty dial — Phase-2 step 3 can still override it.)

## Phase 2 — the composition ladder (D24c), interview = run-shape-relevant only (GB13)
1. **default → go** — accept the preset's recommended mode and launch. The floor is never punishing.
2. **add modules** — à-la-carte beyond the preset bundle (D20).
3. **cross-tier pick** — override a single family's tier (`tiers[family]`) without changing `mode`
   (e.g. pull `kata-grill-advanced` into a Standard run for one cycle).
4. **external/custom ingest** — name a skill + declare its slot (`needs`/`produces`/`slot`) → `ingested[]`.
Surface ONLY the `kata.config` fields the chosen run-shape needs (progressive disclosure) — the default→go path
stays one keystroke; advanced fields appear only when the path opens them.

## Phase 3 — cost preview
Sum the `cost-weight` of every skill the composed run will invoke (authority:
`.planning/SKILL-COST-RATINGS.md` / each skill's frontmatter). Show the total + the per-skill breakdown before
committing, so the user prices the run.

## Phase 4 — write kata.config + launch
Write `kata.config` (JSON, branch root) per `protocol/config.md`: `mode`, `modules`, `effort`, `tiers`,
`ingested`, `preflight`, `bakeoff`, `skillVersions`, **`runShape`**, **`target`**. Bootstrap writes the config
**by construction** — it does NOT re-validate it (that is [[kata-orchestrate]]'s fail-closed load-guard, GB12;
a second validation pass here would be redundant bloat). Then hand off to the loop ([[kata-orchestrate]]).
