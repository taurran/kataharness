# CONTEXT — KataHarness ubiquitous language

The project glossary (per `kata-context` / STANDARDS §5). One canonical term per concept; `_Avoid_` lists
the synonyms we don't use. Glossary only — no implementation detail.

## Core loop
**Kata Loop**:
The **full outer cycle** — `INITIATION (kata-initiate) → the Harness → CLOSEOUT (kata-closeout)`, sequenced by the
thin `kata-loop` conductor, repeatable via loop-back. The branded name for what early docs called the "Greater
Loop" (D92). It *is* the Improvement Kata: run a build, evaluate, and loop back for the next version-up.
_Avoid_: Greater Loop (superseded placeholder, D92); outer loop.

**the Harness**:
Both **the tool** (KataHarness) and **the inner one-shot loop** it runs — `GRILL → FREEZE → EXECUTE → EVALUATE →
HANDOFF → IMPROVE` (`kata-orchestrate` drives it). One pass through the Harness is one build; the Kata Loop wraps
and repeats it. (Operator kept the shared name; context disambiguates, D92.)
_Avoid_: the inner loop (use "the Harness").

**Loop-back**:
The version-up **re-entry**: on a closeout "run again" decision, `kata-loop` re-enters `kata-initiate` Phase 1b
carrying the prior run's context (baseline SHA · `.kata/understand.md` · lessons · prior `INTENT.md`). The turn of
the Kata Loop that makes it iterate. _Avoid_: restart, re-run (those imply cold starts).

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
Improvement-Kata applied to live repos). **Built in Spec A4** (absorbed the old "Spec C").

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

## Version-up & the code graph (A4)
**Structural map / `kata.graph.json`**:
The feature-**agnostic**, content-hash-cached code graph built by `kata-graph` (nodes = files/symbols, edges =
def/ref/call/import, per-node PageRank). The token-saving substrate version-up ingests. Schema: `protocol/graph.md`.
Based on aider's repo-map; Graphify is an optional MCP oracle backend. _Avoid_: index, AST dump.

**Digest**:
The **use-time**, feature-seeded, token-budgeted projection of the structural map (top-PageRank signatures,
~3k tokens default) injected into grill/plan. A view, not the cached graph. _Avoid_: summary.

**Seeding**:
Use-time boosting of PageRank (×10) for symbols matching the feature description + user-named files, so the
digest is the feature's neighborhood. Never cached (the graph stays feature-agnostic). _Avoid_: filtering.

**Footprint**:
The ownership universe of a version-up run = **modified-files ∪ depth-1 reverse-dependents**; files outside are
**off-limits, owned by no task**. The structural form of "don't break other aspects." _Avoid_: scope.

**Blast-radius**:
Reverse-reachability over `ref ∪ call` edges from the changed symbols = the regression-risk surface. Computed by
the **planner** (inverting the graph's forward edges), not by `kata-graph`. _Avoid_: footprint (related, distinct).

**Rolling frontier / frontier dispatch**:
`kata-orchestrate`'s dispatch model — a task runs the moment its `depends_on` are integrated **and** its files are
disjoint from every in-flight task; **waves are a derived view**, not a hard gate. Generalizes the old wave-gate.
_Avoid_: wave (now derived).

**Async escalation**:
An escalation **parks** its task + DAG-dependents but does **not** halt the run; the frontier keeps draining;
hard-wait for a human only when the frontier is empty ∧ open human-required escalations remain. _Avoid_: blocking escalation.

**Escalation payload**:
The structured artifact (`.kata/escalations/<task-id>.json`, `protocol/escalation.md`) carrying
decision/options/recommendation/cost — its **own contract**, separate from the one-line board `ESCALATE`
pointer. The engram learning surface (future, D56). _Avoid_: board message (that's just the pointer).

## Surroundings (D57/D58)
**PokeVault**:
The Obsidian vault that is KataHarness's install/test home: `C:\Users\taurr_nvs748q\PokeVault\PokeVault`
(local). Zones: `daily/ personal/ projects/ research/ scratch/ second-brain/ toolkit/ work/`; KataHarness
installs under **`toolkit/`** (`agents/ agent-sops/ context/ skills/`). Vault alignment principle (matters
for the future KG-emit spec): the **wiki layer is universal** — every zone's `wiki/` tree is structurally
identical (`index/log/review` + `raw/{inbox,notes,media,processed,_archive}` +
`pages/{sources,entities,concepts,synthesis,references}`) — while the **CRM layer is zone-specific by
design** (never align it). _Avoid_: PortaVault (superseded name, D58); PocketVault (the upstream vault
PokeVault replicates — a different vault).

**Test-project target**:
The D16 A/B's target shape (D57): **small, one-shottable greenfield projects** landing in a dedicated test
directory — repeated paired measurements instead of one large task. _Avoid_: CPP phase (retired target).

## Live telemetry & the dashboard (loop-hardening S1, 2026-06-21)
**Coordination board** (`.kata/board.md`):
Append-only event log of an orchestrated run (`protocol/board.md`): `<utc> | <agent> | <TYPE> | <task> | <msg>`.
Workers append (`CLAIM/DONE/BLOCK/ESCALATE/NOTE/PROGRESS`); only the orchestrator authors `DECISION`. Written by
`tools/kata_board.py`. _Avoid_: editing prior lines (append-only, L3); confusing it with `state.json`.

**Run state** (`.kata/state.json`):
Single-writer current-truth snapshot owned by the orchestrator (`protocol/state.md`): tasks/gate/driftLedger/
wavesDone. Written ONLY via `kata_board.write_state`/`update_task`. _Avoid_: a worker writing it (corruption, L3).

**PROGRESS heartbeat**:
The opt-in board TYPE added in S1 for smooth dashboard bars — `… | PROGRESS | <task> | <step>/<n> <label>`. Read
ONLY by the dashboard; ignored by coordination logic. Maps to `percent = round(step/n*100)`. _Avoid_: treating it
as a coordination signal.

**kata_board**:
`tools/kata_board.py` — the single telemetry emitter both orchestrator and workers use; self-creates `.kata/`,
atomic single-writer state, `..`-guarded paths. _Avoid_: duplicating its write logic (the demo delegates to it).

**The dashboard (改善型)**:
`tools/kata_dash.py` — a `rich` separate-terminal TUI that **tails** board+state and renders workers as artistic
ASCII (block bars, braille spinners, loop ribbon, board feed). Title `KATAHARNESS 改善型` (kaizen-gata, "improvement
kata"). Host-agnostic (reads files, not a host UI). Pure model = `kata_dash_model.py`; replay/demo = `kata_dash_demo.py`.
_Avoid_: expecting it to render inside Claude's own session (append-only transcript — separate terminal only).

**loop-hardening**:
The sprint-cadence effort (`.planning/specs/loop-hardening/`) closing the verified gaps **G1–G7** the Phase-4
dogfood accounting exposed (no live board, no mutation proof, no interactive prompt, no grounding/research fire, no
loop-back, no per-platform status surface). **COMPLETE** — all 7 closed; **G6 proven** by the S3b live loop-back
(`222cc7e`, D93). The loop is "vetted, and demonstrably loops." _Avoid_: re-opening it as the active milestone.

## Platform targets & separation (WS-1, 2026-06-21)
**Platform target** (`target.platform`):
The agent host that drives a run — enum `claude | codex | kiro | quick | other`. **`claude` + `codex`** are the
v0.1 **public-FM** targets; **`kiro`** is the planned v0.3 adapter (public Amazon product); **`other`** is the
catch-all. _Avoid_: naming any work-internal host on a public surface.

**Quick (the plumbing seam)**:
The named **ACP desktop-host target** (`platform: quick`, the `acp-quick` adapter) and the **integration seam** the
separate work version plumbs its backend in behind — kept first-class *on purpose* (with explicit pointers) so the
future plumb-in is low-friction. Quick (Amazon Quick) is public and OK to name; the **work backend binds behind it
and is never named on a public surface**. _Avoid_: stripping Quick (it is the seam, not the secret).

**code-bearing** (`footprint.json.codeBearing`):
A run that **introduces or changes executable logic** (derived from changed-file extensions, `footprint.py`
`code_bearing()`, MAJOR-3). `kata-evaluate` rubric item 1 requires the mutation proof **only** for code-bearing
runs; pure docs/config runs are exempt. The flag makes that "is this code?" call evidence-driven, not the
evaluator's opinion. _Caveat:_ the extension set is conservative ⇒ `false` means "probably not code-bearing per the
heuristic," not "definitely not." _Avoid_: treating `codeBearing:false` as a guarantee on out-of-set languages.

**kata-slop-check / `kata/module/slop`** (D94, 2026-06-22):
An **optional EVALUATE-phase module** — a fresh-context, **no-write** check that grades a run for **AI-slop /
spiraling-session** signals (general checks G1–G6 + 3 MIT-attributed checks adopted from `ai-slop-detector`,
re-implemented as in-context heuristics, no Python). **Default-FAIL:** `SLOP-DETECTED ⇒ NEEDS_WORK`, never
advisory. **Off by default**; dispatched alongside `kata-evaluate` only when `kata/module/slop` is in the run's
modules (silent no-op otherwise). Built via the WS-2 version-up dogfood that also **exercised** rolling-frontier
parallelism + the in-loop RS research path (D94).

**exercised vs proven** (honesty convention, 2026-06-22):
A capability run live **once** end-to-end = **"exercised" (n=1)**, not **"proven"** — the latter implies an
automated regression test. WS-2's parallelism + RS path are *exercised*, not *proven* (board timestamps are
orchestrator-written → can't distinguish live from replay). Calling exercised work "proven/genuine" is itself an
**inflation** slop signal (the very thing `kata-slop-check` catches) — keep the words honest.

## User-facing UX (WS-3, 2026-06-24)
**Persona / SOUL** (`protocol/persona.md`):
The harness's single agnostic voice contract — Identity / Style / Avoid / Defaults (Hermes `SOUL.md` shape). The
voice is the **calm kata-craftsperson who translates** (改善型 patience + always "what I did and why it matters to
you"), **nameless** (the harness's own voice, not a mascot). Skills reference it **by path**, never `[[wikilink]]`
(wikilinks resolve to *skills*). _Avoid_: named character/mascot; per-skill bespoke voice.

**Register**:
The language-sophistication level the voice speaks at. v0.1 default = **moderate non-expert** (static, in
`persona.md` Defaults). _Avoid_: claiming it adapts live (see **register-adaptation seam**).

**Register-adaptation seam** (engram **E23**):
The gated, **not-live** path by which a matured fingerprint would dial the register toward the user's real
sophistication (LEARN surface = comprehension/correction signals + grill-ledger choices, D72). Emit/observe-only,
zero CONSULT (D9/D56/D74). _Avoid_: treating register adaptation as an active v0.1 feature (inflation slop).

**Reflective goal mirror** (`kata-initiate`):
The intake front: the agent synthesizes inputs into a plain-language *"here's what you want / what success looks
like / how I'd set it up"* and the human edits it conversationally before `INTENT.md` freezes — **infer-then-confirm**,
which **refines (not reverses)** the S2 anti-drift STOP gate (every frozen value still traces to an explicit human
confirmation, verified per-value, blanket "looks good" fails). _Avoid_: "config form" / "intake interview" (the thing
it replaced).

**"How careful" dial** (`kata-bootstrap`):
The single plain question surfaced to the user ("how thorough / how often should I check with you"); the agent infers
the rest and maps the dial to **existing** `kata.config` fields (`mode` + `tiers["kata-grill"]` + `delivery.boundary`).
The full composition ladder lives behind an **advanced drawer**. _Avoid_: exposing run-shape/mode/tier/cost machinery
to a non-expert; a new config field.

**Narration map** (`protocol/narration.md`):
The contract translating internal phases into human-action phrasing for the **conversation** channel (milestone
cadence, quiet between). **Internal stage names (GRILL/FREEZE/…) are never surfaced.** The `改善型` dashboard/board
stay the granular **firehose**. _Avoid_: streaming every action; reciting stage names.

**Breakthrough alert**:
The **never-tiered** (D33-class) invariant that anything needing the human — a decision/escalation or a critical
failure — surfaces in the conversation immediately and unmissably, regardless of routine narration quiet. _Avoid_:
burying an alert; gating it behind a verbosity setting.

**Goal-anchored closeout** (`kata-closeout` + `kata-report`):
The fixed closeout shape: restate the goal → **lead with what-changed-and-why in plain language, by goal-aspect**
(before any path/gate number) → did-it-hit-the-goal → risks/uncertainties → linked evidence → offered options
(incl. **backout**). Adapts Hermes by-topic synthesis; closeout still **never gates** (`kata-evaluate` owns the gate).
_Avoid_: leading with machine detail; a file-by-file dump.

**Offered backout** (WS-4):
The first-class, plain-language "I can cleanly roll this entire run back" option at the human gate, anchored on the
emitted `.kata/RESULT.json.baselineSha` (`git reset --hard`), **human-gated & never autonomous** (diff shown first).
_Avoid_: a buried git incantation; anchoring on a `pre-<run>` tag no surface guarantees.

## Closeout report (WS-3R, 2026-06-24)
**Two-tier closeout**:
The closeout's output shape — a **concise CLI/GUI summary** (persona voice, goal-anchored essentials) that **ends
with a link** to a **durable in-depth report**. The summary is glanceable; the report is keepable. _Avoid_: a wall
of chat text; a single dense dump.

**Closeout report** (`.kata/closeout.html` + `.kata/CLOSEOUT.md`):
The durable in-depth artifact `kata-closeout` writes each run. `.kata/CLOSEOUT.md` is the **Markdown
source-of-truth**; `.kata/closeout.html` is the **self-contained, on-brand HTML** (rendered by filling the
template **in-context** — no new Python; `.html`/`.css` aren't code-bearing). Both are run artifacts in `.kata/`
(gitignored). _Avoid_: committing the rendered artifacts; a server-rendered or external-asset report.

**Closeout report template** (`modules/closeout/resources/closeout-report.template.html`):
The committed, **self-contained** (inline CSS + inline SVG, no external/CDN/font refs — opens offline) report
skeleton with a **placeholder-token contract** (`{{GOAL}}`, `{{CHANGED_BY_ASPECT}}`, `{{VERDICT_BADGE}}`, …). `kata-report`
authors the content keyed to the tokens; `kata-closeout` substitutes them. _Avoid_: external refs; renaming tokens
out of sync with `kata-report`/`kata-closeout`.

**KataHarness logo**:
The project's first logo (defined 2026-06-24 in the report template + `BRAND.md`): an inline-SVG mark of **three
ascending Prussian-blue bars with a thin ochre arrow rising over them** — the Improvement-Kata "raise the bar"
idea. Subtle; reusable (favicon / docs / statusline glyph). _Avoid_: a mascot; making it loud.

**Report brand** (`BRAND.md`):
The closeout report's visual system — a **Hokusai-derived** palette (aged paper · Prussian blue · ochre · rust),
readable **serif** Title-Case section headings, the logo, and **callout tiles**. Recorded in
`modules/closeout/resources/BRAND.md`. _Avoid_: the dropped experiments (an SVG wave motif; a loop-phase ribbon
that read as broken tabs).

**Callout tiles**:
The report's scannability system — severity blocks: `.tile--warning` (ochre, risks), `.tile--error` (rust,
critical / backout), `.tile--note` (blue), `.tile--ok` (deep). Risks render as warning tiles; the backout as an
error tile. _Avoid_: a flat undifferentiated list for risks/alerts.

## Second-brain learning — Recall · Reason (the C-arc, D99, 2026-06-24)
**Second brain**:
The **data** layer of the learning subsystem — a **bring-your-own, agnostic** vault (PokeVault, the work repo, …)
holding raw knowledge + the user's decision history + (over time) synthesized decision-pattern pages. **Supersedes
"engram"** (which conflated data + a synthesized layer + a controller into one word — rename pending, D99).
_Avoid_: engram (being retired); assuming PokeVault (it is one backend among many).

**Recall** (the *Librarian*):
The **per-vault fetcher/adapter** that knows *its own* second brain's structure and serves KataHarness's standard
**Recall contract** — **lives with each second brain** (downstream repos build their own), **never decides**. The
adapter pattern (spine #3) applied to the second brain; it *is* the D30 clean-room backend binding, named. You point
KataHarness at the Recall, not the raw folder. _Avoid_: putting decision logic in a Librarian (kills cross-vault
consistency); pointing the core at a raw vault structure.

**Reason** (the *Advisor*, `kata-reason`):
KataHarness's **decider** — asks Recall to surface material, fuses it with research (RS + the grounding gate),
returns a **calibrated recommendation that mirrors the user**. **Advisory, not authoritative** (it pre-fills; the
gates/human dispose). The CONSULT read-path, finally named + skilled. _Recall serves; Reason decides._ _Avoid_:
treating Reason as authoritative; letting it expand the frozen goal (it re-plans *toward* the goal only).

**C/B invariant**:
The LOCKED-class line that keeps gated-learning (C) from sliding into Hermes-fluid (B): **every Reason decision
stays a deliberate, frozen, gated, thrash-bounded, audited event toward a human-frozen goal** — *protect the
process, not the decider.* Test: *did it produce a discrete frozen artifact the gates judged, or did the plan just
quietly become something else?* First = C; second = B. _Avoid_: equating "who decides" with the boundary (it's
"is it still a gated event").

**Readiness exam**:
The measurable gate that unlocks C — `kata-reason` must predict the user's **held-out** past decisions (with
research context) at **calibrated confidence** (high-confidence-wrong fails hard); fresh-context, no-self-cert,
standing + cached (project-start / on-request / corpus-growth — **not** every loop). Pass → C unlocks; fail →
graceful fallback to A. The measurable definition of "mature." _Avoid_: scoring raw confidence (must be
calibration vs held-out truth); running it every loop.

## Debug Mode P3 — closeout report · language profiles · onboarding (D117, 2026-06-27)
**Debug closeout report** (`tools/debug_report.py` + `kata-debrief`):
The fixed LD12 closeout shape for a **debug** run — per-module **confidence map** (assessed / low-confidence /
skipped, every entry `heuristic:true`) · each **deviation→fix→pinning-test** (route-gated `applied` claim) ·
a **proof rollup** (drift + characterization suite + mutation + **real Snyk before/after**). `tools/debug_report.py`
is the PURE assembly engine; `kata-debrief` (skills/evaluate) authors/renders it in the two-tier `kata-report` shape.
Reports **never gate**. Honesty is pinned at the engine (behavioral-only · heuristic-confidence · n=0-live).
_Avoid_: trusting prose-supplied Snyk counts (the engine recomputes `effective_new`); claiming "structure preserved"
(behavioral drift only).

**`.kata/snyk/<finding_id>.json`**:
The persisted Snyk **before/after** artifact a debug fix-loop writes (the D117 freeze-gate BLOCKER fix — the
DESIGN cited a `RESULT.json` Snyk field that no surface emitted). `finding_id` derivation is identical to
`drift_gate.defer_record`. _Avoid_: reading Snyk state from `RESULT.json` (it carries none).

**Language profile** (`kata-lang-profile`, LD10):
A **prose-only** in-mode specialist selected by **footprint file extensions** (the function-model has no `language`
field), injected at dispatch (the IaC-specialist precedent), layered on `kata-tdd`/`kata-diagnose`. 6 language
profiles + a config/context specialist. **No fork, no new Python.** _Avoid_: a per-language code path; a new agent.

**Onboard / convert-to-loop** (`kata-onboard`, LD13):
The dedicated first-run on-ramp (skills/coordinate) — fresh install → offer Debug Mode → on success offer
**convert-to-loop** + vault setup (writes kata.config + `.planning/` scaffold + commits the characterization suite).
Composes the BUILT install-portability surfaces. Tagged `kata/spine` (validator requires spine-or-module; least-wrong
for an on-ramp — a recorded divergence from PLAN-p3). _Avoid_: treating convert-to-loop/`.planning`-scaffold as reuse
(honestly labeled NEW).

## Recurrence-hardening Tier 2 — recurrence→proposal (D118, 2026-06-27)
**Actionable recurrence** (`tools/recurrence_detect.py`):
A failure **CLASS** that has recurred across **3 distinct runs** (or **2** for a BLOCKER), clustered by
`responsible_skill`×`failure_class`, **not yet `handled`**. Distinct-run counting uses `run_id` with a `ts`-fallback
(blank/whitespace `run_id` coerces to `ts`). The detector READs the manifest; it never writes guards. _Avoid_:
counting raw rows (must be distinct runs); re-tripping a `handled` cluster.

**`failure_class` (soft enum)**:
A curated 8-member classification on a validation-miss. **Soft:** published `_FAILURE_CLASS_VALUES` + a schema `enum`
key + non-blocking `is_known_class`; **`validate_miss` is UNCHANGED for `failure_class`** so an off-vocab value is
flagged by the detector, never DROPPED at write. _Avoid_: hard-rejecting off-vocab (would lose a real miss).

**T2 proposal** (`PROPOSAL-<class>.md`, `kata-improve` v0.2.0):
The human-gated hardening proposal the loop **auto-drafts** when a recurrence becomes actionable — cluster + evidence
rows + proposed target surface + guard text/test sketch. Routes to **freeze-gate `kata-review` → human merge** (NOT
`kata-promote`). Writable footprint pinned to EXACTLY `PROPOSAL-<class>.md` + the `proposed` sidecar marker. **T2
INVARIANT (load-bearing):** T2 proposes — it never changes a gate verdict, edits a skill/protocol/tool, writes the
`guarded` marker, or merges its own proposal. **T3** (auto-authoring the guard) = C-arc future. _Avoid_: treating the
proposal as the guard; auto-merging it.

**recurrence-handled sidecar** (`.planning/recurrence-handled.jsonl`):
The append-only `proposed`/`guarded` marker log the detector consults to skip already-actioned clusters. _Avoid_:
editing prior lines (append-only).

## IaC Tier-2 — preview/approve HALF (execution DEFERRED) (D119, 2026-06-28)
**IaC apply engine** (`tools/iac_apply.py`):
The PURE preview/approve/plan-capture engine for live IaC — structured-argv builders (TF + CFN; `shell=False`, no
`-target`/`-auto-approve`, dedicated CFN ARN grammar), `plan_hash`/`canonical_cfn_plan_bytes`, `approval_verdict`
(plan-hash-bound; re-plan ⇒ `APPROVAL_INVALIDATED`), the typed self-binding `capability_gate_verdict`, `apply_state`,
and the sibling `.kata/iac-apply.json`. **Contains NO subprocess on the path.** _Avoid_: extending `.kata/iac.json`
(sibling artifact only); reading it as proof apply "works".

**`run_apply` seam** (DEFERRED):
The single function that would actually mutate cloud infra — **raises `NotImplementedError` always.** The
**catastrophic invariant** (no reachable cloud mutation; a destroyed DB can't be `git revert`ed) holds **by
construction**. Live execution is future-gated on operator-authenticated CLOUD creds (its own session). _Avoid_:
claiming Tier-2 can apply; conflating cloud creds with the (now-installed) Codex CLI.

**Capability gate** (`capability_gate_verdict`, typed self-binding):
The stateful-destroy/replace gate (operator chose this over Tier-1's hard-block) — clears ONLY when all three hold:
`grant.approvedPlanHash == computed_plan_hash` AND `authorizedStatefulAddresses ⊇` the stateful-destroy set AND a
typed `confirmedToken`. Fail-closed on every miss. Contract: `protocol/iac-safety.md` **§9** (Tier-1 §1–§8 untouched).
_Avoid_: a grant not bound to the plan hash (a stale grant must not pass).

## Recall (BUILT) — read-contract + files-only adapter (D120, 2026-06-29)
**Recall engine** (`tools/recall.py`):
The BUILT read side of cross-run learning (the D99 *Librarian*, now concrete). `recall_payload_schema` validates
**SHAPE only, NEVER a closed vocabulary** — `source`/`provenance.backend`/`provenance.produced_by` are **OPEN**
adapter-supplied labels (the deliberate opposite of `validate_miss`'s hard enums) so an external Librarian implements
the contract without re-contracting. `recall_from_paths` is the **files-only default adapter** (six sources);
`select_records` is a **hard token-overlap>0 predicate** (recency only RANKS) — **NO embeddings/RAG**. **No exec
sink, NO WRITE PATH** (returns a dict). _Avoid_: adding embeddings; making the contract files-only-shaped.

**`engram.backend` (named)**:
The long-reserved CONSULT seam (D9/D30/D99), now named by Recall's read-side. The gated CONSULT **decider**
(`kata-reason`) stays OFF (deferred to its own grill); the write/distill half stays emit-only (β LEARN, D74).
Contract doc: `protocol/recall.md` (registered in `validate_skills.py REQUIRED_PROTOCOL`). _Avoid_: treating Recall
as the decider; re-opening the write half.

**INTENT-never-written invariant** (Recall):
`recall.py` has NO write path of any kind; `intent_scaffold.write_intent` (fed only by operator-confirmed `answers`)
stays the SOLE INTENT writer. `kata-initiate` Phase-1b renders a read-only **RECALL BRIEF** (open recurrences first,
then matched records w/ provenance/date/`stale`) that informs the mirror/grill and never enters `answers`.
**Structural, not procedural.** _Avoid_: writing recall output into INTENT; hard-filtering on staleness (surface it).

## Multi-model layer — now LIVE on Codex (D121, 2026-06-29)
**Multi-model LIVE status**:
The D108 read-only role routing (validator→codex, researcher→kiro) is **LIVE-proven on a real 2nd platform** for the
first time (n=0→1). Operator installed **Codex CLI 0.142.3** (ChatGPT-authed); the first live run caught a real
adapter defect (codex needs `--skip-git-repo-check` + closed stdin) → fixed in `kata_dispatch`/`kata_install`.
`kata_install.py --platform codex --confirm` → `confirmed:true`. **Coder-routing + evaluator-thresholds remain
DEFERRED** (D108 LD11/MM-1). _Avoid_: claiming the benchmark ran (the `kata-loop-benchmark` is still unbuilt — e step 2).

**Confirm-probe** (N5 standing guard):
The `kata_install` confirm probe that runs a real platform CLI and checks for the `SSENRAHATAK` token — the standing
guard the multi-model BRIEF anticipated for **stale per-CLI flags between releases**. It did its job: it surfaced the
codex 0.142.3 flag/stdin change. `_PROBE_COMMANDS ⊆ _COMMAND_BUILDERS` (L-MP2 invariant). _Avoid_: trusting a
stub-only adapter as live-confirmed.

## kata-loop-benchmark — the C-arc keystone (D123 BUILT · D124 deep-ad-val'd, 2026-06-29)
**The benchmark**:
The deterministic **outcome+efficiency benchmark** for the loop — the D99 keystone that measures **C-on/C-off learning
lift**. A **hidden, off-by-default `benchmark` module** (mirrors `kata/module/slop`; flag/`KATA_BENCHMARK=1`/config block;
**not in `kata-bootstrap`** — a power-user surface). **n=0 LIVE** — proven on synthetic fixtures + unit/e2e dry-runs,
**never run on a real control repo (= D5, operator-supplied)**. _Avoid_: claiming it ran live; calling it "proven."

**Control (the immutable reference)**:
The experimental **control** — an immutable reference (code repo or research project), **cloned per run** into
`<base>-katabenchmark<N>` (`benchmark_control.clone_control`; the reference is **never mutated**). **Rigidity lives in the
control** (byte-identical start + identical inputs across arms via `content_hash`/`detect_drift`), **not in the metric**.
_Avoid_: mutating the reference; treating the metric as the rigid element.

**Two-axis scorecard**:
**Axis Q** (∈[0,1], gated): the `kata-evaluate` default-FAIL **floor** (floor-fail ⇒ **Q=0 absolute**) + the SWE-bench-style
**dual-gate** `FAIL_TO_PASS`×`PASS_TO_PASS` + a **mutation** multiplier. **Axis C** (efficiency): tokens/$/wall-clock/
tool-calls/escalations/thrash (host-dependent fields **nullable**; missing/invalid → **worst-case imputed**, never excluded,
so omitting a dimension can't win). **Floor-gated composite**: a Pareto point `(Q,C)` + a convenience scalar
`Q/(1+λ·C_norm)`, efficiency scored **ONLY among floor-passers** (a cheap-wrong answer can't win). Profiles
`balanced|cost-lean|quality-strict`. _Avoid_: scoring efficiency for a floor-failer; letting a negative/NaN cost win
(the read-path `_validate_numeric` guards it).

**Benchmark Definition · repeat_from · delta** (replay-by-definition):
The durable, content-pinned `benchmark.def.json` (`benchmark_id`, `criteria_ref`, `control.content_hash`, `provenance`;
written to `def_out`, NOT `.kata/`). **A `repeat_from` re-run REUSES the prior `benchmark_id`** → `compute_delta.sameDefinition:true`
→ the **honest harness-delta** (same definition + newer provenance = the C-on/C-off number). **`parent_benchmark_id` is
FORK-only** (a NEW benchmark deriving from an old one); a plain repeat leaves it absent. Delta rendering activates on
`repeat_from`/`sameDefinition` — **NOT** `parent_benchmark_id`. _Avoid_: minting a fresh id on a repeat (→ false "drifted").

**Embedded criteria**:
`.kata-benchmark/criteria.json` in the control (`{fail_to_pass:[], pass_to_pass:[]}` of pytest node-IDs). `benchmark_def.load_criteria`
reads it → `benchmark.run_dual_gate(clone_root, f2p, p2p)` runs the IDs **as DATA** via `mutation_check.run_named_test`
(`cwd=clone_root` + PYTHONPATH so the control imports; `shell=False`; `_guard_node_id` blocks traversal). Missing criteria
⇒ empty lists ⇒ `dual_gate_evaluated:false` (no free credit). _Avoid_: shell-executing a control's command strings (only
declared test-IDs run); running the dual-gate without `cwd` (→ Q=0 for any importing control).

**Benchmark engines + report**:
PURE engines `tools/{usage_meter,benchmark,benchmark_def,benchmark_control}.py` (no new direct exec sink — `run_dual_gate`
delegates to the registered `mutation_check` sink, external-trust row in `exec-safety.md`). The `kata-benchmark-report`
skill (evaluate) renders the **two-tier** report into `modules/closeout/resources/benchmark-report.template.html` (the
new BRAND-consistent template). **Reports NEVER gate** (`kata-evaluate` owns the gate); **n=1 directional** honesty pinned
in the engine `honesty` block. _Avoid_: the report re-deriving a join in prose (it drives `benchmark.py`).

**k-repeats (honest-simplify, v1)**:
k-repeats are **independent per-repeat rows** (`<arm>·repeat<k>`); **mean±spread aggregation + cross-repeat ranking are
DEFERRED** (operator decision (b); DESIGN §6b superseded with an explicit R6-no-drift note). _Avoid_: claiming mean±spread;
ranking a repeat as "dominated" by its own sibling.

**Benchmark DEFERRED set (D1–D5)**:
**D1** concurrent bakeoff arms (gated on Spec B execution — v1 = sequential/single-arm + k-repeat + arm-ranking scorer);
**D2** research-mode judge; **D3** benchmark→`kata-improve` T2 optimization-proposal hook; **D4** promote-best-arm-to-master
(real-repo only); **D5** the real control FIXTURE (operator-supplied; design is fixture-agnostic). _Avoid_: treating any of
these as built.

## kata-validate — the validation mini-loop (D125, 2026-06-29)
**kata-validate / validation mini-loop** (`skills/evaluate/kata-validate`):
The always-available, **programmatically-callable** validator — `validate(payload, target="auto", profile) ->
Report{passed, findings[]}`. Runs **inline on ANY data** and **requires NO freeze/INTENT/`kata.config`** (its
defining property); **dual-target** (arbitrary content OR another agent's output) with **payload-as-data isolation**
(the payload is graded, never obeyed — injection containment). Four deterministic-first legs by **method-by-reference**
(grounding = `kata-evaluate` injected-knowledge + grounding_gate · review = `kata-review` 5-surface RUBRIC · slop =
`kata-slop-check` G1–G6/A1–A3 · score = `kata-evaluate` conformance, conditional/N-A when no plan). Drives its **own
thin conductor** (the `kata-loop`/`kata-onboard` composition-wrapper precedent) — it does **NOT** route through
`kata-orchestrate` (untouched); bounded **≤2 passes**; **tripwire + cross-family-judge** safety rails. **Report-only
by default**; a **per-finding human-gated fix** is applied by a **single writer** (the validators themselves stay
no-write). _Avoid_: calling it a module (it is always-available, not module-gated); saying it needs a freeze/plan;
routing it through `kata-orchestrate`; letting a validator write a fix (only the sole writer does, human-gated).

## Install & onboarding — final polish (D126, 2026-06-29)
**one-command install / bootstrap** (`install.sh` · `install.ps1` · `uninstall.sh` · `uninstall.ps1`, repo root):
The cross-platform front door — `curl|sh` (POSIX) or `irm|iex` (PowerShell) clone/seed then **invoke the existing
`tools/kata_install.py` engine** (the bootstrap scripts never re-implement install). Idempotent, no-cruft;
**`KATA_SRC`** overrides the source for **offline** install; an **uninstaller ships** alongside. The `curl|sh`
security caveat is **honest**: the checksum protects the **downloaded artifact** (download-then-run), **NOT the
pipe itself**. _Avoid_: "the installer" (name the engine `kata_install.py` vs the bootstrap scripts); implying
`curl|sh` is verified end-to-end (the network fetch is exercised, not proven); calling the engine new (it is
byte-for-byte untouched — the scripts wrap it).

**headless install surface** (the `kata_install.py` flags + exit codes):
The agent-friendly / non-interactive entry — ADDITIVE flags (`--yes`/`--non-interactive`, `--answers-json`,
`--json`, `--uninstall`, `--target-dir`) + non-TTY auto-skip, with **semantic exit codes** (0 ok · 1 not-confirmed
· 2 usage · 3 not-found · 4 permission · 5 conflict=non-kata-only). Machine JSON → stdout, human → stderr;
**idempotent re-install = exit 0 no-op** (deliberately **no `changed` field** — that would force an engine edit).
Autonomous-loop mode is **DEFERRED** (the build loop's commit/merge/fix gates stay human). _Avoid_: "the install
API"; expecting a `changed`/diff field; assuming it can drive an unattended build loop.

**kata_router / router stanza** (`tools/kata_router.py`; the marked block in a target AGENTS.md):
The pure stanza engine — `render`/`write`/`remove_stanza` perform a **`..`-guarded, idempotent marked-block
upsert** between `<!-- kata:begin -->` and `<!-- kata:end -->` (the **router stanza**, ~15 lines, instruction-
budgeted). `kata-onboard` (v0.2.0) gains an **opt-in, human-gated Step-3 item** that writes the stanza into the
target project's **canonical AGENTS.md**; the uninstaller removes **exactly that block**. _Avoid_: editing
CLAUDE.md (it stays a pointer, D5); hand-editing inside the markers; leaving an **orphan/unbalanced marker** (the
engine fails loud rather than risk the data-loss upsert edge).

**acceptance-criteria step** (`kata-initiate` step 2g + S2 gate value #9 + `intent_scaffold.acceptanceCriteria`):
The grill-for-goals polish — an **ADDITIVE optional `acceptanceCriteria`** field in `intent_scaffold` (byte-
identical BC when absent; **NOT required**) plus a `kata-initiate` step that **enumerates + confirms** the run's
acceptance/success criteria up front (start-with-the-end-in-mind). The S2 freeze-gate's value #9 is handled like
conditional value #8: an explicit **"no criteria for this run" PASSES** (no deadlock), while the verbatim
"blanket looks-good **FAILS**" rule is preserved — the gate is **strengthened, not loosened**. _Avoid_: treating
`acceptanceCriteria` as mandatory; reading the explicit-no-criteria path as a gate bypass.
