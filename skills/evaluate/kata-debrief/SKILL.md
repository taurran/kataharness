---
name: kata-debrief
description: >-
  LLM-judgment author + renderer of the LD12 debug-run closeout confidence report. Drives the
  tools/debug_report.py engine for every deterministic join — the per-module confidence map
  (assessed / low-confidence / skipped), the deviation -> fix -> pinning-test table, and the regression
  + security proof rollup (drift + suite + mutation + the REAL Snyk before/after) — then authors the LD3
  recommendations list and the OFFERED version-up / sprint follow-on, renders all four elements in the
  kata-report two-tier {{TOKEN}} shape (so kata-closeout folds the debug section into .kata/CLOSEOUT.md /
  .kata/closeout.html), and emits the model to .kata/debug/closeout.json. Use at debug-run closeout
  (offered by kata-closeout when kata/module/debug is active) for an honest account of a Debug Mode run.
  It REPORTS; it never gates (kata-evaluate owns the gate). Every output states the §5 behavioral-only +
  LD5 heuristic-confidence + n=0-live honesty. Voice: protocol/persona.md.
license: Apache-2.0
version: 0.1.0
category: evaluate
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Write]
source: >-
  new (KataHarness original, Debug Mode P3 — LD12 closeout confidence report + LD3 recommendations /
  offered version-up; mirrors the kata-report two-tier + {{TOKEN}} render contract)
tags:
  - kata/evaluate
  - kata/spine
  - kata/module/debug
  - confidence
  - closeout
  - synthesis
---

# kata-debrief — LD12 debug-run closeout confidence report

The **author + renderer** of the Debug Mode closeout. When a debug run finishes, `kata-debrief` turns the
machine artifacts the P1/P2 passes left behind (`.kata/function_models/*.json`,
`.kata/deviations/findings.json`, `.kata/drift/*.json`, `.kata/fix_manifest/*.json`,
`.kata/deviations/deferred.json`, `.kata/snyk/*.json`, `.kata/RESULT.json`, `.kata/mutation.json`) into a
human deliverable: an honest confidence report a non-expert owner can read to understand what the run
assessed, what it fixed, what it proved, and what it recommends next.

It is the debug-mode peer of `kata-report` (same `evaluate` category, same two-tier shape, same persona
voice). It is offered by `kata-closeout` only when `kata/module/debug` is active (Slice C wiring); absent
that marker it does not run.

Voice is governed by `protocol/persona.md`: plain-language-first, lead with outcomes not machinery, warm
through clarity, honest about uncertainty. The report renders in that voice throughout.

## Hard boundary — it reports, it never gates

`kata-debrief` **synthesizes**; it does **not** evaluate or decide. The default-FAIL gate is and stays
`kata-evaluate` (D22). This skill only *transcribes* the gate's verdict and numbers into the page — it
owns no pass/fail authority. If there were no green gate, the report says so; it does not confer one.

## Drive the engine — never re-derive a join in prose

Every deterministic join belongs to `tools/debug_report.py` (Slice A, verified — `protocol/reuse-claims.md`
verify-before-reuse). `kata-debrief` **calls** these surfaces and renders their output; it never
re-implements a join, a classification, or a rollup in prose. The engine transcribes the artifacts' own
honest verdicts; it confers none — and neither does this skill.

Cited engine surfaces (each resolves in `tools/debug_report.py`):

- `debug_report.finding_id(finding)` — the single canonical join key (`id` → `locus` → `"unknown"`),
  identical to `drift_gate.defer_record`. Used everywhere a finding is matched to an artifact.
- `debug_report.build_confidence_map(function_models, *, graph_modules=None)` — element 1.
- `debug_report.build_deviation_table(findings, drift_reports, fix_manifests, deferrals)` — element 2.
- `debug_report.build_proof_rollup(drift_reports, result_json, mutation_json, snyk_reports)` — element 3.
- `debug_report.build_debug_report(confidence_map, deviation_table, proof_rollup, *, recommendations, offered_followups)`
  — composes the full data model conforming to `debug_report.debug_report_schema()`.
- `debug_report.snyk_report_schema()` — the single-source-of-truth shape of `.kata/snyk/<finding_id>.json`
  (`before`/`after` verdict + `findingCount`, `newFindings`, `available`) — read it to interpret the Snyk
  artifacts; do not invent fields.
- `debug_report.emit_debug_report(report, path)` / `debug_report.load_debug_report(path)` — JSON
  round-trip to `.kata/debug/closeout.json`.

The consumed artifact shapes resolve in their owning modules (verified — cite by name, do not assume):
`deviation.findings_schema` / `deviation.load_findings` (`tools/deviation.py`, route enum
`auto-fix-eligible | research | defer | human`); `drift_gate.drift_schema` + `drift_gate.defer_record`
(`tools/drift_gate.py`); `function_model.function_model_schema` (`tools/function_model.py`); the
`.kata/fix_manifest/<id>.json` shape (`ael` / `characterization_files` / `blast_radius_manifest`) authored
by `kata-characterize`.

## Honesty — mandatory in every output (engine-pinned, prose-restated)

These three disclosures appear in **every** rendered output (Tier 1 and Tier 2) and in the emitted data
model. They are pinned at the engine (`debug_report_schema()`'s description, `build_proof_rollup`'s
`behavioral_only` flag, `build_confidence_map`'s `heuristic: true` tags, the report's `honesty` block) so
they cannot be silently dropped; the skill adds the plain-language wording on top. **If rendering the
report ever seems to "need" an over-claim to look complete, STOP and escalate** — the honesty is
load-bearing, not cosmetic.

1. **Behavioral-only (§5 v1).** The drift proofs rolled up here are **behavioral only** (baseline-green
   stays green; characterization snapshots stable except the AEL). Render
   **"behavior preserved (behavioral drift gate)"** — **never** "structure preserved." The structural /
   public-surface invariance layer is a named fast-follow (`drift_gate.structural_drift_verdict` stays a
   non-executing seam). The limitation string is carried verbatim by `build_proof_rollup`
   (`behavioral_only_note`); render it, do not paraphrase it away.
2. **Heuristic confidence (LD5).** The confidence map is a **v1 heuristic, uncalibrated**. Label it
   **"heuristic (v1, uncalibrated)"** wherever it appears; never imply calibration, never verbalize a
   number as if validated. Force-LOW / sparse modules render as **low-confidence**; modules with no
   function model render as **skipped** — never silently as "assessed." The isotonic-calibration
   fast-follow is named as deferred.
3. **n=0 live.** Debug Mode has **never** run end-to-end on a real repository. State this in every output.
   The report is proven on **seeded fixtures** only; do not imply a real-repo run occurred. A live dogfood
   is a separately-labeled exit item.

Additionally: **quote the `kata-evaluate` verdict verbatim** (`PASS` / `NEEDS_WORK`), never re-derived,
softened, or re-interpreted. **Source it honestly:** `kata-evaluate` is the fresh-context, **no-write**
gate — it returns its overall PASS / NEEDS_WORK as conversational output, not a persisted field — so the
verdict reaches closeout **as surfaced by the orchestrator / `kata-closeout`**, NOT from a
`.kata/RESULT.json` `verdict` field (that field does not exist). `.kata/RESULT.json` is the
`run_result.build_result` schema (`gateName` / `command` / `exitCode` / `passed` / `failed` / `skipped` /
`stdoutTail` / `baselineSha` / `resultSha` / `utc`); it carries the **gate-RESULT facts** kata-debrief
quotes verbatim for the proof rollup (suite pass/fail/skip counts + exit code) and carries **no evaluate
verdict** — do not invent one. If the surfaced verdict is not available when kata-debrief renders, say so
plainly (report the gate-RESULT facts and note the verdict is pending) rather than fabricate it.

---

## The four LD12 elements (each by CALLING the engine)

### 1. Confidence map — assessed / low-confidence / skipped

Read every `.kata/function_models/*.json` and pass the list to
`debug_report.build_confidence_map(function_models, graph_modules=...)`.

- **`graph_modules` (for the `skipped` set):** prefer the graph node inventory (`.kata/kata.graph.json`)
  so modules present in the graph with no function model render as **skipped**. If the graph is not present
  at closeout, fall back to the footprint module set (modules touched/known with no FM) — either inventory
  is honest; state which one was used. Do **not** silently treat a no-FM module as assessed.
- **Render** the map labeled **"heuristic (v1, uncalibrated)"**. Group by classification: assessed,
  low-confidence (carrying `forced_low` where set), skipped. Every entry carries `heuristic: true` from the
  engine — surface that the numbers are uncalibrated, not validated.
- Plain-language lead: what fraction of the touched surface the run could actually assess, and where it
  honestly could not (low-confidence + skipped), before any per-module detail.

### 2. Deviation → fix → pinning-test

Read `.kata/deviations/findings.json` (via `deviation.load_findings` semantics), every
`.kata/drift/*.json`, every `.kata/fix_manifest/*.json`, and `.kata/deviations/deferred.json`. Pass them to
`debug_report.build_deviation_table(findings, drift_reports, fix_manifests, deferrals)`.

Render one row per finding from the engine output:

- **Applied fixes** (`applied: true`, drift `PASS`): show the **pinning test(s)** (the row's
  `pinning_tests` = the flipped AEL ids) and the **left-behind characterization file(s)**
  (`characterization_files` — the suite that stays in the target repo, conversion value LD6).
- **Deferred fixes** (`deferred: true`): show the deferral **reason** verbatim from the record
  (LD9 / DG-12). Do not imply a deferred fix was applied.
- **`research` / `defer` / `human` findings:** show their `route` and make **no applied-fix claim** —
  these are inputs to the recommendations list (element 4), not completed fixes.

Do not re-join in prose — the row's join key is `finding_id`, derived once by the engine, so a locus-only
finding still matches its drift / fix-manifest / Snyk artifact (no silent miss).

### 3. Regression + security proof

Read every `.kata/drift/*.json`, `.kata/RESULT.json`, `.kata/mutation.json`, and every
`.kata/snyk/*.json` (the per-fix before/after Snyk verdicts persisted by Slice W, conforming to
`debug_report.snyk_report_schema()`). Pass them to
`debug_report.build_proof_rollup(drift_reports, result_json, mutation_json, snyk_reports)`.

Render the rollup:

- **Drift:** PASS / BLOCK counts; state **"behavior preserved (behavioral drift gate)"** — never
  "structure preserved" (render the engine's `behavioral_only_note` verbatim).
- **Suite-green:** from `RESULT.json` (`suite_green`); quote the gate counts verbatim, never recompute.
- **Mutation non-vacuous:** `allNonVacuous` from `mutation.json` — the proof the suite exercised real
  behavior.
- **Security (real Snyk before/after):** render the per-fix `before` / `after` verdicts + `findingCount`
  and the rolled-up `newFindings`. An `available: false` artifact is rendered honestly as
  **"before-scan unavailable for this fix"** — **never** as clean. The Snyk before/after is read only from
  `.kata/snyk/*.json`; `RESULT.json` carries no Snyk field, so nothing is invented from it.

### 4. Recommendations + offered follow-on (LD3) — author these

This is the skill's authored judgment (the engine carries it through unchanged):

- **Recommendations list:** the advisable behavior/feature changes the no-drift run **could not** make —
  drawn from the `research` / `human` / `defer` findings and the deferred records. Each recommendation is a
  small dict (e.g. `{module, finding_id, recommendation, rationale, source_route}`). Author them in the
  persona voice: what the owner should consider next and why it matters, grounded in the run's evidence.
- **Offered follow-on:** the **offered** version-up / sprint handoff as a dict (e.g.
  `{kind: "version-up" | "sprint", summary, handoff_to: "[[kata-loop]]"}`). The follow-on is **offered**,
  handed to the `[[kata-loop]]` conductor's loop-back (Decision 3 path) — it is **never auto-started**.
  Committing the left-behind characterization suite remains the human-gated Decision 2 git action in
  `kata-closeout`; this report only surfaces the offer.

Pass both into `debug_report.build_debug_report(..., recommendations=..., offered_followups=...)`.

---

## Two-tier render + emit

Compose **both tiers** in the `kata-report` shape, then emit the data model.

### Tier 1 — concise CLI summary (persona voice)

The short in-conversation account a non-expert owner reads, in `protocol/persona.md` voice (no internal
stage names, no jargon dump). In order:

1. **What the run did** — one or two plain sentences.
2. **Confidence** — how much of the touched surface was assessed vs honestly low-confidence/skipped,
   labeled **"heuristic (v1, uncalibrated)"**.
3. **Fixes** — how many deviations were fixed-and-pinned, how many deferred (with the headline reason).
4. **Proof** — **"behavior preserved (behavioral drift gate)"**, suite-green + mutation-non-vacuous in one
   line, and the real Snyk before/after (new-findings count, or "before-scan unavailable" where honest).
5. **Verdict** — the `kata-evaluate` PASS / NEEDS_WORK quoted verbatim as surfaced by the orchestrator /
   `kata-closeout` (the no-write gate's output — not a `.kata/RESULT.json` field); alongside it, the
   gate-RESULT facts from `.kata/RESULT.json` (suite pass/fail/skip + exit code). If the verdict is not yet
   surfaced, say so plainly — never fabricate one.
6. **Top recommendations** (≤3) and the **offered** follow-on (offered, not started).
7. **Honesty footer** — the three disclosures (behavioral-only, heuristic-confidence, n=0 live) in one
   compact line.
8. **Link line** to the full report (ends the summary), e.g. `Full report: .kata/closeout.html`.

### Tier 2 — full content keyed to the {{TOKEN}} contract

The complete debug section, keyed to the exact `{{TOKEN}}` placeholders `kata-closeout` (Slice C)
substitutes when it folds the debug section into `.kata/CLOSEOUT.md` / `.kata/closeout.html`. This skill is
the **producer** of this token contract for the debug section (the way `kata-report` is the producer of the
standard-report tokens); Slice C is the consumer. Do not invent extra tokens or rename these.

- `{{DEBUG_RUN_TITLE}}` — short human title for the debug run + date.
- `{{DEBUG_CONFIDENCE_MAP}}` — element 1, labeled "heuristic (v1, uncalibrated)"; assessed /
  low-confidence / skipped, with the inventory source noted.
- `{{DEBUG_DEVIATION_TABLE}}` — element 2, one row per finding (applied fixes with pinning test(s) +
  characterization file(s); deferred with reason; research/human/defer with route, no applied-fix claim).
- `{{DEBUG_PROOF_ROLLUP}}` — element 3: "behavior preserved (behavioral drift gate)", suite-green,
  mutation non-vacuous, and the real Snyk before/after (incl. honest `available:false`).
- `{{DEBUG_RECOMMENDATIONS}}` — element 4, the authored LD3 recommendations list.
- `{{DEBUG_OFFERED_FOLLOWON}}` — element 4, the offered version-up / sprint handoff (offered, never
  auto-started; handed to `[[kata-loop]]`).
- `{{DEBUG_VERDICT}}` — the `kata-evaluate` PASS / NEEDS_WORK quoted verbatim **as surfaced by the
  orchestrator / `kata-closeout`** (the fresh-context, no-write gate's output — there is no
  `.kata/RESULT.json` `verdict` field), shown with the gate-RESULT facts (`exitCode` / `passed` / `failed`
  / `skipped`) read verbatim from `.kata/RESULT.json`. Never invent a verdict field; if the verdict is not
  surfaced, render it as pending.
- `{{DEBUG_HONESTY}}` — the three mandatory disclosures (§5 behavioral-only, LD5 heuristic-confidence,
  n=0 live), rendered from the report's `honesty` block (with the engine's verbatim note strings).

Render the `{{DEBUG_HONESTY}}` block as honest scannable content (the standard report uses warning tiles —
`tile--warning` — for the risk register; the debug honesty disclosures may reuse that pattern so they are
not buried). The Markdown content is authoritative; the HTML is the presentation layer `kata-closeout`
renders from the same content.

### Emit

Build the data model with `debug_report.build_debug_report(...)` and write it with
`debug_report.emit_debug_report(report, ".kata/debug/closeout.json")`. The emitted model is the durable,
machine-readable artifact behind both tiers; `kata-closeout` and any operator can `load_debug_report` it.

---

## Discipline

- **Read the artifacts, don't re-derive.** Every confidence class, deviation join, and proof number comes
  from the engine over the committed artifacts — not from a fresh investigation.
- **Delegate every deterministic join** (confidence map / deviation table / proof rollup) to
  `tools/debug_report.py`. Never re-implement one in prose. No phantom reuse — every cited engine surface
  resolves to a real symbol; every cited artifact field resolves to a real schema field.
- **Reports, never gates.** `kata-evaluate` owns the gate; quote its verdict verbatim, never confer one.
- **Both tiers, every honesty disclosure.** The concise CLI summary and the full `{{TOKEN}}`-keyed content
  are both required; the three honesty disclosures appear in both and in the emitted model.
- **Never over-claim.** No "structure preserved", no "calibrated confidence", no implied live run. These
  are the project's signature failure modes — pinned at the engine and restated here on purpose.
- **Voice: `protocol/persona.md` throughout.** Plain-language outcomes before machinery; honest on
  uncertainty; no inflation.
</content>
</invoke>
