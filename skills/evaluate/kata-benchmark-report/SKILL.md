---
name: kata-benchmark-report
description: >-
  Two-tier author/renderer of the benchmark scorecard report. Drives tools/benchmark.py for every
  deterministic join (Axis Q floor+dual-gate+mutation, Axis C efficiency, floor-gated composite,
  Pareto position, per-arm ranking) and renders the kata-report two-tier {{TOKEN}} shape plus a
  repeat_from delta header. Active only when kata/module/benchmark is in the run's modules; silent
  no-op otherwise. It REPORTS; it never gates (kata-evaluate owns the gate). Every output carries
  the n=1-directional + exercised-not-proven honesty. Voice: protocol/persona.md.
license: Apache-2.0
version: 0.1.0
category: evaluate
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Write]
model: sonnet
source: >-
  new (KataHarness original — kata-loop-benchmark report; mirrors the kata-report/kata-debrief two-tier
  {{TOKEN}} render contract; engine tools/benchmark.py)
tags:
  - kata/evaluate
  - kata/module/benchmark
  - benchmark
  - report
  - synthesis
---

# kata-benchmark-report — benchmark scorecard report

The **author + renderer** of the benchmark run scorecard. When a benchmarked run finishes, `kata-benchmark-report`
turns the machine artifacts the benchmark engine left behind (`.kata/benchmark/<run-id>.json`,
`.kata/{RESULT,footprint,mutation}.json`, `.kata/usage.json`, and the benchmark definition) into a human
deliverable: an honest two-tier report a non-expert owner can read to understand how the run scored, how it
ranked against other arms and prior runs, and what the benchmark recommends next.

It is the benchmark-mode peer of `kata-debrief` (same `evaluate` category, same two-tier shape, same persona
voice). It is offered by `kata-orchestrate` only when `kata/module/benchmark` is active; absent that marker
it is a **silent no-op**.

Voice is governed by `protocol/persona.md`: plain-language-first, lead with outcomes not machinery, warm
through clarity, honest about uncertainty. The report renders in that voice throughout.

## Activation guard — silent no-op when module absent

**Active only when `kata/module/benchmark` appears in the run's declared modules** (the `modules` array in
`protocol/config.md:14`; the `benchmark` module key registered in `protocol/config.md:105-108`). If the
module is absent, this skill does **not** run — zero invocation cost, zero output, zero side effect. This
mirrors `kata-debrief`'s exact activation pattern (`skills/evaluate/kata-debrief/SKILL.md:1-46`) and
`kata-slop-check`'s guard (`skills/evaluate/kata-slop-check/SKILL.md:36-45`). The off-by-default module
is the load-guard; fail-closed on a module key with no provider means the skill is never invoked
accidentally on a non-benchmark run.

## Hard boundary — it reports, it never gates

`kata-benchmark-report` **synthesizes**; it does **not** evaluate or decide. The default-FAIL gate is and
stays `kata-evaluate` (D22). This skill only *transcribes* the benchmark engine's verdict and scores into
the page — it owns no pass/fail authority. If the run did not clear the floor, the report says so; it
confers no credit and opens no exemption. **Reports NEVER gate** is a frozen invariant of this skill
(DESIGN §12; DESIGN §7 "reports NEVER gate — spine #4").

## Drive the engine — never re-derive a join in prose

Every deterministic join belongs to `tools/benchmark.py`. `kata-benchmark-report` **consumes** the emitted
`.kata/benchmark/<run-id>.json` scorecard and **calls** the engine's rendering surfaces; it never
re-implements a join, a score, a floor check, a Pareto computation, or a ranking in prose. Cite the engine;
do not duplicate it.

Cited engine surfaces (each resolves in `tools/benchmark.py` — S2, `protocol/reuse-claims.md` verify-before-reuse):

- `benchmark.score_arms(arm_map, profile=<cfg.profile>, f2p_p2p_results=<assembled>)` — the pure multi-arm scorer (`profile` and `f2p_p2p_results` are **keyword-only**; the positional call `score_arms(arm_map, 'balanced')` crashes). Takes the `arm_label → clone-artifact-root` map plus pre-computed dual-gate booleans (produced by `benchmark.run_dual_gate`); performs Axis Q (floor-gate from `.kata/RESULT.json` `exitCode`/`failed`; dual-gate F2P/P2P pass-rates from injected `f2p_p2p_results`; mutation multiplier from `.kata/mutation.json` `allNonVacuous`); Axis C (normalized cost from `.kata/usage.json` per-arm fields); floor-gated composite (Pareto point `(Q, C)` + convenience scalar `Q / (1 + λ·C_norm)` among floor-passers only); per-arm ranking. **Floor fail ⇒ Q = 0** (absolute; no cost score unlocks a failed run). An arm absent from `f2p_p2p_results`, or with empty `f2p`/`p2p` maps, receives `dual_gate_evaluated: false` and Q = 0 (no free dual-credit). Profile weights applied per `benchmark.profile` config (`balanced | cost-lean | quality-strict`). Returns structured output conforming to `scorecard_schema()`.
- `benchmark.scorecard_schema()` — single source of truth for the emitted scorecard shape.
  Read it to interpret every field; do not invent fields.
- `benchmark.emit_scorecard(path, scorecard)` — **path is the FIRST arg**; writes `.kata/benchmark/<run-id>.json`. The report
  consumes this artifact; it does not re-emit it.

Delta-mode surface (resolves in `tools/benchmark_def.py` — S3):

- `benchmark_def.compute_delta(new_scorecard, prior_scorecard)` — returns
  `{dQuality, dCost, dParetoPosition, sameDefinition, provenanceDiff}`. Consumed only when the run
  was launched via `repeat_from`; produces the delta header that leads the report. Same definition +
  newer provenance = an honest harness-delta measurement. This is the only surface `kata-benchmark-report`
  calls from `tools/benchmark_def.py`.

**No phantom reuse** — every cited surface above resolves to a concrete function in the named file
(`protocol/reuse-claims.md`). If a surface is not yet present in the file, treat the claim as NEW and
do not freeze it; `kata-benchmark-report` consumes these surfaces because S2 and S3 build them before S5
activates (PLAN dependency DAG: S5 depends on S2, S3).

## Honesty — mandatory in every output (pinned, prose-restated)

Two honesty disclosures appear in **every** rendered output (Tier 1 and Tier 2) and in the emitted data
model. They are engine-pinned (the `scorecard_schema()` `honesty` block carries them so they cannot be
silently dropped); the skill adds the plain-language wording on top.

1. **n=1 directional honesty.** A single benchmark run (or even k-repeats at small k) is
   **directional — not proven**. Label every comparative claim *"directional at n=[k]; not statistically
   proven."* Never upgrade a small-n finding to a proven conclusion. The ΔQ / ΔC numbers in a delta
   header are a signal, not a certified improvement. The *n=1 = directional* convention is the benchmark
   module's extension of the harness's standard *exercised ≠ proven* invariant (DESIGN §6b; DESIGN §12).

2. **Exercised ≠ proven.** The test/mutation pass-rate and Axis Q score tell you the run exercised the
   embedded criteria. They do not prove correctness of unseen cases, correctness of deferred criteria, or
   any claim beyond the declared control's scope. State **"exercised, not proven beyond declared criteria"**
   wherever quality scores appear.

Additionally: **transcribe the floor verdict verbatim from `.kata/RESULT.json`** (`exitCode` / `failed`)
as scored by `benchmark.score_arms` — never re-derive, soften, or re-interpret it. **Do not confer a
floor pass** that the engine did not award.

---

## The benchmark report elements (each by consuming the engine)

### 1. Scorecard — Q, C, composite (from `.kata/benchmark/<run-id>.json`)

Read the emitted scorecard (conforming to `benchmark.scorecard_schema()`). Render, per arm:

- **Axis Q** (floor + dual-gate + mutation): the engine's `q` (Q score), the floor verdict (`floor_verdict` string / `floor_passed` boolean), the dual-gate results (`f2p_pass_rate` / `p2p_pass_rate` / `dual_gate_both_green`), the `dual_gate_evaluated` flag (false = no declared criteria, Q forced to 0 — no free dual-credit), and the mutation multiplier (`allNonVacuous` from `.kata/mutation.json`). **Floor fail ⇒ Q = 0 — quote it, never soften it.** If the dual-gate is partial (F2P partial, P2P green), render the partial credit honestly.
- **Axis C** (efficiency): the normalized cost fields from `.kata/usage.json` per-arm:
  `tokensIn / tokensOut / costUSD / wallClockS / toolCalls / escalations / thrashIters / subagentDispatches`.
  When a token/cost field is `null` (host did not surface it), render it as **"not reported by host"** —
  never as zero, never silently omitted.
- **Composite**: the floor-gated Pareto point `(Q, C)` and the convenience scalar
  `Q / (1 + λ·C_norm)`, profile weights applied. **Composite is blank for floor-fail arms** — render
  `"—"` or `"floor fail"`, not a number.

Attach the honesty footer to the scorecard tile: *"n=[k] directional; exercised, not proven beyond declared
criteria."*

### 2. Pareto position vs control/baseline

Render the arm's Pareto point `(Q, C)` on the Pareto frontier relative to the control and any prior-run
baseline the scorecard carries. State which arms dominate and which are dominated — an arm is dominated when the top-level `recommendations` list carries a `{kind: "dominated", arm: <label>}` entry for it (the engine's `_build_recommendations` emits this; there is no per-arm `pareto_dominated` field). Use the per-arm `pareto{q, c}`, `rank`, `in_efficiency_set`, `composite`, and `c_norm` fields for the Pareto-point table. If there is only one arm or no prior baseline, state so plainly — *"single-arm run; no relative Pareto comparison available."*

Use a **note tile** (`.tile--note`, blue) for dominated arms and an **ok tile** (`.tile--ok`, deep
Prussian) for Pareto-optimal arms (BRAND.md callout-tile convention from
`modules/closeout/resources/BRAND.md`).

### 3. Per-arm comparison table

Render one row per arm from the engine's scorecard: arm label · floor verdict · Q · C (key fields, null
shown as "—") · composite · Pareto rank. Source all values from `scorecard_schema()` fields — no hand-
computed columns. If only one arm is present, label the table *"single-arm run"* and still render it
(the degenerate case is valid; k-repeats each appear as a separate arm row).

**Optimization recommendation tiles**: after the comparison table, render one tile per
optimization finding that the scorecard's `recommendations` field carries (authored by the engine's
internal heuristics). Each tile follows the BRAND `.tile--warning` convention (ochre, `Watch` label) for
marginal items and `.tile--error` (rust) for floor failures. **These tiles are OFFERED observations —
never auto-applied directives.** The D3 hook into `kata-improve` T2 proposals is deferred; the skill
surfaces the tile content for human review only.

### 4. Delta header (repeat_from runs only)

**Render only when the run was launched via `repeat_from`** (a `parent_benchmark_id` is present in the
definition). In all other runs this section is omitted entirely.

When present, call `benchmark_def.compute_delta(new_scorecard, prior_scorecard)` and lead the entire
report with the delta block — before the scorecard, before the comparison table:

- **Δ headline**: `ΔQ = {dQuality:+.3f}` · `ΔC = {dCost:+.3f}` · `ΔPareto = {dParetoPosition}`
- **Provenance stamp**: `sameDefinition = {true|false}`; `provenanceDiff` (harness version, skill
  versions) — same definition + newer provenance = honest harness-delta. Render `provenanceDiff` verbatim.
- **Honesty banner**: *"n=[k] repeat; delta is directional, not a statistically certified improvement."*
  Render as a `.tile--warning` (ochre) so it cannot be missed.

If `sameDefinition` is false, render a `.tile--error` (rust) warning: the definition drifted between runs
— the delta reflects a mixed signal (criteria change + harness change), not a clean harness-delta.

---

## Two-tier render + emit

Compose **both tiers** in the `kata-report` shape, then emit the data model.

### Tier 1 — concise CLI summary (persona voice)

The short in-conversation account a non-expert owner reads, in `protocol/persona.md` voice (no internal
stage names, no jargon dump). In order:

1. **What the benchmark ran** — one or two plain sentences: the control, how many arms, the profile.
2. **Scorecard headline** — the winning arm (or only arm), its Q/C/composite, floor verdict. If the floor
   failed, lead with that plainly.
3. **Pareto position** — one sentence: where the arm sits relative to the control and any baseline.
4. **Delta headline** — only if `repeat_from`: the three Δ numbers + the provenance stamp, labeled
   *"directional."*
5. **Top optimization observations** (≤3 tiles, summarized in a sentence each) — offered, never directives.
6. **Honesty footer** — the two mandatory disclosures (n=1 directional; exercised ≠ proven) in one compact
   line.
7. **Link line** to the full report (ends the summary):
   ```
   Full report: .kata/benchmark/<run-id>-report.html
   Scorecard:   .kata/benchmark/<run-id>.json
   ```
   This link is a hard requirement (mirrors kata-report PLAN M1). Both paths must be present.

### Tier 2 — full report content keyed to the {{TOKEN}} contract

The complete benchmark report, keyed to `{{TOKEN}}` placeholders that parallel the `kata-report`
two-tier shape (`skills/evaluate/kata-report/SKILL.md:44-57`) and render via the committed template +
BRAND system (`modules/closeout/resources/closeout-report.template.html:6-33`;
`modules/closeout/resources/BRAND.md`). Do not invent extra tokens or rename these.

- `{{BENCHMARK_RUN_TITLE}}` — short human title: control name + profile + date.
  Example: `"Benchmark · balanced profile — 2026-06-28"`.
- `{{BENCHMARK_VERDICT_BADGE}}` — `<span class="badge badge--{STATE}">{LABEL}</span>`. STATE ∈
  `pass | partial | needs-work`. Derived from the highest-ranking arm's floor verdict. A floor-fail-only
  run renders `badge--needs-work`. Mirrors the `{{VERDICT_BADGE}}` contract from `kata-report`.
- `{{BENCHMARK_DELTA_HEADER}}` — the delta block (§4 above, full content). **Omit this token entirely**
  when not a `repeat_from` run; `kata-orchestrate` skips substitution when the block is absent.
- `{{BENCHMARK_SCORECARD}}` — element 1: scorecard table (Q, C, composite) per arm, with the honesty
  footer tile. Each floor-fail arm's composite cell shows `"—"`.
- `{{BENCHMARK_PARETO}}` — element 2: Pareto position section. Dominated arms in `.tile--note`;
  Pareto-optimal arms in `.tile--ok`. Single-arm runs render as labeled single-entry.
- `{{BENCHMARK_ARM_TABLE}}` — element 3: per-arm comparison table (one row per arm: label · floor · Q · C
  key fields · composite · Pareto rank). Source: `scorecard_schema()` fields verbatim.
- `{{BENCHMARK_RECOMMENDATIONS}}` — element 3 (cont.): optimization recommendation tiles, one per top-level `recommendations` entry (`kind` ∈ `pareto-best | cost-outlier | dominated`; `arm`; optional `detail`). `.tile--ok` (deep Prussian) for `pareto-best`; `.tile--warning` (ochre) for `cost-outlier`/`dominated` observations. Labeled **OFFERED — not auto-applied**. D3 optimization-proposal hook is deferred; these tiles are human-facing content only.
- `{{BENCHMARK_EVIDENCE}}` — evidence artifact links: `.kata/benchmark/<run-id>.json` (scorecard path +
  arm count + profile); `.kata/RESULT.json` per arm (gate counts verbatim); `.kata/usage.json` per arm
  (cost fields, nulls noted); `.kata/mutation.json` per arm (`allNonVacuous` value).
- `{{BENCHMARK_HONESTY}}` — the two mandatory disclosures (n=1 directional; exercised ≠ proven beyond
  declared criteria), rendered from the scorecard's `honesty` block (`{directional, basis, disclosure}` — engine-pinned; cannot be silently dropped). Read `honesty.basis` (e.g. `"n=1"`) and `honesty.disclosure` verbatim for the rendered text. Render as a `.tile--warning` (ochre) so it is not buried. The Markdown content is authoritative; the HTML is the presentation layer.
- `{{BENCHMARK_TIMESTAMP}}` — UTC ISO-8601 timestamp at report-emit time.

### Emit

Write the Tier 2 content to `.kata/benchmark/<run-id>-report.html` by substituting the `{{BENCHMARK_*}}`
tokens into the template at `modules/closeout/resources/closeout-report.template.html` (same BRAND,
same layout, benchmark-specific content). Write the Tier 1 summary to conversation output. Both tiers
are required; neither is optional.

---

## Discipline

- **Read the scorecard, don't re-derive.** Every Q score, C value, composite, Pareto flag, and ranking
  comes from `tools/benchmark.py` over the committed artifacts — not from a fresh investigation.
- **Delegate every deterministic join** (Axis Q / Axis C / composite / Pareto / ranking / delta) to
  the named engine surfaces. Never re-implement a join in prose. No phantom reuse — every cited surface
  resolves to a real symbol in `tools/benchmark.py` or `tools/benchmark_def.py` per `protocol/reuse-claims.md`.
- **Reports, never gates.** `kata-evaluate` owns the gate; transcribe the floor verdict verbatim, never
  confer one.
- **Both tiers, both honesty disclosures.** The concise CLI summary and the full `{{TOKEN}}`-keyed content
  are both required; the two honesty disclosures appear in both.
- **Silent no-op when module absent.** If `kata/module/benchmark` is not in the run's modules, this skill
  does not run, does not emit, and does not report. Zero cost, zero side effect.
- **Never over-claim.** No "proven improvement," no "certified reduction," no small-n finding upgraded to
  a statistically valid conclusion. These are the benchmark module's signature failure modes — pinned at the
  engine and restated here on purpose.
- **Voice: `protocol/persona.md` throughout.** Plain-language outcomes before machinery; honest on
  uncertainty; no inflation.
