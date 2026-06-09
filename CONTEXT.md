# CONTEXT — KataHarness ubiquitous language

The project glossary (per `kata-context` / STANDARDS §5). One canonical term per concept; `_Avoid_` lists
the synonyms we don't use. Glossary only — no implementation detail.

## Core loop
**Spine**:
The skills that run in **every** mode — the one-shot machine (grill→…→evaluate→handoff). Always present; the
source of consistency.
_Avoid_: core set, base skills

**Module**:
An additive, independent feature-set of skills layered onto the spine (e.g. `quality`, `design`, `bakeoff`,
`improve`). Declares what it needs/produces/where it slots; bolts onto any mode.
_Avoid_: plugin, pack, extension

**Mode**:
A named operating point = spine + a module bundle + the tier of each tiered skill. The three: **Essential /
Standard / Advanced**. Sets breadth (modules) and depth (tiers) on one axis.
_Avoid_: profile, level, preset (preset = the *default* bundle of a mode, not the mode itself)

**Effort overlay**:
An orthogonal dial — model + reasoning effort (Claude `effort`) — set independently of the mode.
_Avoid_: power, intensity

## Quality & consistency
**Consistency**:
The harness's north star: the same mode yields comparable, reproducible output run-to-run. Enforced by
declared bundles + the uniform conformance floor + the frozen spec control + `kata.config` provenance.

**Conformance floor**:
The uniform `kata-evaluate` default-FAIL gate every mode ends at ("builds/tests/scan green"). Never tiered —
the invariant that makes modes/variants comparable.
_Avoid_: quality gate (too broad), the bar

**Tier**:
The depth level of a *tiered skill* (essential/standard/advanced), selected by the mode. Tiered via separate
files (high-cost skills) or a mode-passed depth hint (medium skills).

**Tier-family**:
A skill that exists as multiple per-tier files (`kata-<verb>-<tier>`) sharing one rubric resource.

**RUBRIC**:
The tier-invariant method shared by a tier-family's per-tier files, at `skills/<cat>/kata-<verb>/RUBRIC.md` —
a resource, **not** a skill (no SKILL.md). The tier files carry only their depth knob and point to it
(DRY-by-pointer).
_Avoid_: base skill, template, shared SKILL

**Family-alias**:
A bare `[[kata-<verb>]]` reference = the **tier-agnostic family**; `kata-orchestrate` resolves it to a
concrete tier via `kata.config` (fallback **Standard**, D25). Cross-skill references stay bare by design.
_Avoid_: default skill, the base

**Structural invariant**:
A spine guarantee that holds at **every** tier — no-self-certification (L8), no-drift (verbatim LOCKED-decision
quoting), default-FAIL, DRY-by-pointer. **Never tiered** (D33); tiers vary depth only. Generalizes the
conformance floor from one skill to a principle.
_Avoid_: rule, constraint

## Pre-flight & dependencies
**Pre-flight**:
The mandatory spine phase between FREEZE and EXECUTE that pre-stages every external dependency —
human-approved at FREEZE, then installed + verified — **before** the loop runs; workers cannot install (D29).
A long-running loop must never stall mid-flight on a missing tool/lib/MCP.
_Avoid_: setup, provisioning, install step

**Dependency manifest**:
The frozen list of external deps (name · version · install · verify · source/trust · scope · build-time/runtime)
approved at FREEZE and provisioned at pre-flight. Schema: `protocol/dependencies.md`.
_Avoid_: requirements, deps list

**cost-weight**:
A skill's 1–5 token-cost rating (base × amplification × exec-context), metadata used to price a mode.

**Amplification**:
The cost-driver dimension: `spawn` (dispatches subagents = fresh windows) ≫ `loop` (iterates in-context) ≫
`none`. Dominates a skill's true cost over base footprint.

## Modes of operation (the feature)
**Bake-off**:
Running N variants of the same one-shot in parallel, judging, picking the best, then refining the winner up a
tier. (Uses AgentHub / worktrees.) The `bakeoff` module; its "tier" is N.
_Avoid_: best-of-N (the underlying technique — fine to reference), tournament

**Escalation / step-up**:
Refining an existing result up a tier (Essential→Standard→Advanced). Cheap because the prior tier's frozen
artifacts seed the next; the validated cost-saving path.
_Avoid_: upgrade, promote

**`kata.config`**:
The per-branch provenance record: mode, active modules, effort, bake-off lineage, skill versions. Reproducibility backbone.

**Bootstrap**:
The pre-loop GSD-style Q&A (`kata-bootstrap`) that selects mode + modules + effort, previews cost, writes
`kata.config`, and launches the loop.
_Avoid_: wizard, setup

**Version-up**:
A one-shot feature-rollout / new version of an *existing* project, driven through the modes (the
Improvement-Kata applied to live repos). Spec C.

**Run-shape**:
A named preset over the mode axis (individual / batch / version-up / advanced) that `kata-bootstrap`
pre-fills; not a new axis (GB1/D34). Sets `(mode, modules[], config-defaults)` before the user drills
down via the D24c composition ladder.
_Avoid_: mode (the underlying axis), workflow-type

**Preset**:
The `(mode, modules, target)` bundle a run-shape pre-fills; the user may then drill down via the ladder
(D24c). Pre-seeds the bootstrap interview without locking the user in.
_Avoid_: template, default

**Readiness**:
The pre-run check (`kata-readiness`) of harness-health + target-readiness + re-entrant config detection,
invoked by bootstrap (D44/GB11). Distinct from pre-flight (D29), which is the dependency-provisioning
phase between FREEZE and EXECUTE.
_Avoid_: pre-flight (that's the dependency-provisioning phase, D29)

**Load-guard**:
`kata-orchestrate`'s fail-closed `kata.config` check on read: absent ⇒ Standard (D25),
present-but-broken ⇒ stop (D45/GB12). Bootstrap writes by construction; this is the consumer-side
guard against stale or hand-edited configs on re-entrant runs.
_Avoid_: validation (bootstrap writes by construction; this is the consumer-side guard)

**`target`**:
The run's subject: `greenfield` (new project) or `existing` (version-up — an existing repo `path` +
a `baselineGate` regression command). Set in `kata.config`; determines which run-shape bundle applies.
_Avoid_: project, repo
