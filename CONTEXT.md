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
