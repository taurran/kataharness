---
title: "Debug Mode — Phase 3 PLAN (the FINAL phase: closeout report + language profiles + onboarding)"
status: "FROZEN — freeze-gate kata-review HOLD→SHIP (2026-06-27; BLOCKER Snyk-before/after-persistence + 2 MINORs fixed → re-confirm SHIP)"
date: 2026-06-27
spec: debug-mode
phase: P3 (LD12 debug-run closeout confidence report + LD3 recommendations/offered-version-up · LD10 in-mode language prompt-profiles · LD13 onboarding / convert-to-loop · §5 v1 honesty carry-forward)
source: >-
  FROZEN DESIGN .planning/specs/debug-mode/DESIGN.md (LD12, LD3, LD10, LD13, §3, §4, §5 incl. the v1
  structural-drift LIMITATION, §6, §7); PLAN-p2b.md (the PROTECT half — tools/drift_gate.py + kata-characterize
  fix_manifest + the P3 comment-seam in kata-orchestrate); the BUILT P1/P2 surfaces (tools/function_model.py,
  tools/deviation.py, tools/drift_gate.py, tools/footprint.py; skills/plan/kata-comprehend,
  skills/execute/kata-deviate, skills/execute/kata-characterize); the BUILT install-portability surfaces
  (tools/kata_settings.py, tools/project_find.py, tools/kata_install.py, modules/initiation/kata-initiate);
  recipe per .planning/HANDOFF.md §5
---

# Debug Mode — Phase 3 PLAN (the FINAL phase)

Phase 3 turns the debug run's machine outputs into the **human deliverable** and closes the onboarding loop.
Scope = the three remaining LOCKED decisions — **LD12** (the debug-run closeout confidence report, carrying
**LD3**'s recommendations list + offered version-up/sprint), **LD10** (in-mode language prompt-profiles), and
**LD13** (the onboarding / convert-to-loop first-run path) — plus the **§5 v1 structural-drift honesty
carry-forward** and the **LD5 confidence-is-a-v1-heuristic** honesty note baked into the report wording.

P3 **starts at the artifacts P1/P2 produced** (`.kata/function_models/*.json`, `.kata/deviations/findings.json`,
`.kata/deviations/deferred.json`, `.kata/drift/<id>.json`, `.kata/fix_manifest/<id>.json`, `.kata/RESULT.json` +
`.kata/mutation.json`) and **ends at** a rendered confidence report, a stack-aware execute overlay, and a
first-run onboarding path. It does **not** discover, fix, or re-gate anything (P2a/P2b own those).

This PLAN introduces **no decisions**; every choice traces to a LOCKED decision in the frozen DESIGN. An
unresolved point ⇒ flagged as a "return to DESIGN/grill" item (see Judgment calls), never invented. It
partitions P3 into **disjoint-ownership slices** with a wave DAG, following the same recipe shape P2a/P2b used
(deterministic Python engine + LLM-judgment skill(s) + thin wiring).

## In scope (P3 — the FINAL phase)
- **LD12 — the debug-run closeout confidence report.** Four elements, honestly worded: (1) a per-module
  **confidence map** (assessed / low-confidence / skipped); (2) each **deviation → fix → pinning-test**
  traceable row; (3) the **regression + security proof** (drift PASS + characterization suite green + new
  pinning tests + mutation non-vacuous + Snyk before/after); (4) the **recommendations list** (LD3 — advisable
  behavior/feature changes the no-drift run could not make) **+ offered follow-on version-up/sprint** handoff.
- **LD10 — in-mode language prompt-profiles.** Per-major-language + a config/context specialist profile,
  **layered on** `kata-tdd` / `kata-diagnose` **inside the debug mode**, selected by the detected stack, with
  **NO new Python** (prose profiles + orchestrator injection, mirroring the IaC specialist precedent).
- **LD13 — onboarding / convert-to-loop (v1).** A **dedicated first-run path**: fresh install → offer Debug
  Mode → on success offer **convert-to-loop + vault setup** (writes `kata.config` + scaffolds `.planning/` +
  surfaces the human-gated commit of the left-behind characterization suite + binds the vault). Composes the
  **BUILT** install-portability surfaces; introduces no new installer Python.
- **§5 v1 + LD5 honesty carry-forward.** Every P3 artifact (report data model, report skill prose, the HTML/MD
  render) states that v1 enforces **behavioral** drift only (structure not fully enforced) and that confidence
  is a **v1 heuristic, not calibrated** — so "structure preserved" and "high confidence" are never over-claimed.

## Out of scope (fast-follow / other phases — do NOT build here)
- **Re-running discovery / fix** (`tools/deviation.py`, `kata-deviate`, `tools/drift_gate.py`, `kata-characterize`,
  the P2b fix-application loop body) — P2a/P2b-owned and already built. P3 **reads** their artifacts.
- **§5 fast-follow** the surface/structural-invariance layer (public-API diff = ∅ + AST-edit-script) — remains
  the named non-executing seam `drift_gate.structural_drift_verdict` (raises `NotImplementedError`).
- **LD5 fast-follow** formal isotonic confidence calibration on a labeled corpus.
- **A real-repo live dogfood of Debug Mode end-to-end** (n=0 live today). P3 proves on **seeded fixtures**; the
  live exercise is scoped **honestly** as a separate, explicitly-labeled exit item, not silently claimed
  (see Judgment calls + Risks).
- **Rich native render hooks** (Stop/SessionEnd surfacing) — inherits kata-closeout's deferred M8 follow-up.

## ⚠ §5 v1 + LD5 honesty — carried into LD12's report (FREEZE note, DESIGN §5/H4 + LD5)
LD12's closeout report **must not over-claim**:
- **Structure.** The drift proofs the report rolls up are **BEHAVIORAL only** (baseline-green stays green;
  characterization snapshots stable except the AEL). The structural / public-surface invariance layer
  (public-API diff = ∅ **+** AST-edit-script = body-updates-only) is a **FAST-FOLLOW, NOT v1**. The report says
  "behavior preserved (behavioral drift gate)" — it **never** says "structure preserved" on the basis of the v1
  gate. The `drift_gate.structural_drift_verdict` seam stays non-executing; the report data model carries a
  fixed limitation note string sourced from `drift_schema()`'s own description.
- **Confidence.** The per-module confidence map is the **LD5 / kata-comprehend v1 heuristic**
  (`C = w1·MSAS + w2·(1−entropy) + w3·StructuralPrior`, force-LOW for sparse signal) — **not** calibrated, not
  verbalized. The map is labeled "heuristic (v1, uncalibrated)"; force-LOW / sparse modules render as
  **low-confidence**, modules with no FM render as **skipped** — never silently as "assessed."
- **Liveness.** Debug Mode has **never run end-to-end on a real fixture** (n=0 live). The report's
  self-description and the P3 acceptance both state this; the closeout does not imply a real-repo run occurred.

`tools/debug_report.py` is **pure data assembly** — it neither asserts structure-preservation nor re-derives
confidence; it transcribes the artifacts' own (already-honest) verdicts and labels. The skill prose adds the
plain-language honesty wording on top, in the `protocol/persona.md` voice.

## Architecture split (the recipe — deterministic engine vs LLM-judgment skill vs wiring)
- **`tools/debug_report.py` (NEW engine, Slice A)** — pure, injectable, **mutation-proof** deterministic
  **assembly** of the LD12 report **data model** from the real P1/P2 artifact shapes: build the per-module
  confidence map, join each finding to its drift proof + fix manifest + deferred record into a
  deviation→fix→pinning-test row, roll up the regression+security proof, and carry the (skill-authored)
  recommendations list. **No subprocess, no eval, no exec** — it `json.load`s artifacts and returns/emits dicts.
  It transcribes verdicts; it confers none. Single source of truth for the report schema.
- **`kata-debrief` (NEW skill, Slice B; category `evaluate`, never-tiered debug-spine)** — the LLM-judgment
  **author + renderer**: calls the engine for every deterministic join, authors the **recommendations list**
  (LD3) and the offered **version-up/sprint** handoff, renders the **four LD12 elements** in the two-tier
  `kata-report` shape, and **states the §5/LD5/n=0 honesty** in every output. It **reports, never gates**
  (kata-evaluate owns the gate) and **never re-implements** a join the engine owns.
- **`kata-lang-profile` (NEW skill, Slice D; category `execute`, never-tiered debug-spine) + prose profiles** —
  the LD10 in-mode specialist pack: one `resources/<lang>.md` prompt-profile per major language + a
  `config-context.md` specialist; the SKILL.md is the **selection + overlay** contract (given the detected
  stack, apply the matching profile as an execute-phase overlay on `kata-tdd`/`kata-diagnose`). **No new Python.**
- **`kata-onboard` (NEW skill, Slice E; category `coordinate`, first-run path)** — the LD13 onboarding flow:
  detect a fresh install, offer Debug Mode, and on success offer convert-to-loop + vault setup. **Composes** the
  built install-portability tools + `kata-initiate`/`kata-bootstrap`/`kata-closeout` by wikilink; introduces
  no new installer Python.
- **Wiring (Slices C + W)** — `kata-closeout` offers/composes `kata-debrief` on debug runs (Slice C); and
  `kata-orchestrate` resolves the P3 comment-seam + injects the LD10 profile at the debug fix-loop / diagnose
  dispatch (Slice W). Both gated on `kata/module/debug`; absent it, byte-for-byte unchanged.

### exec-safety posture (mandatory — `protocol/exec-safety.md`)
**P3 introduces ZERO new execution sinks** and registers **no new row** in the sink registry. Confirmed:
- **`tools/debug_report.py` is PURE data assembly.** It reads JSON artifacts via `json.load`, joins plain
  dicts, and writes JSON. It **spawns no subprocess and calls no `eval`/`exec`** — assertable by source scan in
  its test (re-asserting the P2a/P2b posture for the new module). It transcribes the artifacts' own verdicts; it
  runs nothing.
- **`kata-debrief` runs no code.** Its `allowed-tools` mirror `kata-report` (Read/Grep/Glob/Write) — it reads
  artifacts and writes the report to `.kata/`. No operator runs, no evaluator.
- **`kata-lang-profile` is prose-only (LD10).** Profiles are markdown overlays injected into a worker's launch
  context; nothing in the profile pack executes. **No new Python.**
- **`kata-onboard` adds no sink.** It composes **already-registered / sink-free** surfaces by wikilink:
  `kata_install.copy_project` (uses `shutil`, **never git** — install-portability §5), `kata_settings.*`
  (pure builders + `_safe_path`-guarded writers), `project_find.find_projects` (pure search),
  `intent_scaffold.write_intent` (`..`-guarded writer), and the **human-gated** git actions that already live
  in `kata-closeout` (commit/merge/backout — behavioral guard, not new). The `.planning/` scaffold is **skill
  `Write` into the target tree** (no subprocess). `test_exec_safety.py` is unaffected.

## Slices (disjoint file ownership)

### Slice A — `tools/debug_report.py` LD12 report-assembly engine  *(NEW Python; pure, mutation-proof)*
**Owns:**
- `tools/debug_report.py`
- `tools/tests/test_debug_report.py`
- `tools/tests/fixtures/debug_report/` (seeded fixtures: a small set of `.kata/function_models/*.json` spanning
  HIGH / LOW-forced / sparse + a module present in the graph with **no FM** [skipped]; a `findings.json` with
  one each of `auto-fix-eligible` / `research` / `defer` / `human`; matching `.kata/drift/<id>.json` PASS and
  BLOCK proofs; a `.kata/fix_manifest/<id>.json` with `ael` + `characterization_files`; a `deferred.json`
  record; **two `.kata/snyk/<id>.json` before/after fixtures — one clean, one with a new finding**; a
  `RESULT.json` + `mutation.json`)

**Surfaces (public, cite-able by name per `protocol/reuse-claims.md` + cite-by-section-name):**
- `debug_report_schema() -> dict` — JSON schema (single source of truth) for the LD12 report data model; its
  `description` carries the **fixed §5/LD5/n=0 honesty note** (behavioral-only; heuristic-confidence;
  no live run).
- `snyk_report_schema() -> dict` — JSON schema (single source of truth) for the per-fix Snyk artifact
  `.kata/snyk/<finding_id>.json` (the artifact W writes; shape owned here, A). Shape:
  `{finding_id, before: {verdict, findingCount}, after: {verdict, findingCount}, newFindings, available, utc}`
  where `before`/`after` record the real Snyk MCP verdict on the pre-fix and fixed-worktree states,
  `newFindings = max(0, after.findingCount − before.findingCount)`, and `available:false` records honestly
  that a meaningful before-scan was not obtainable for this fix (no fabrication).
- `build_confidence_map(function_models: list[dict], *, graph_modules: list[str] | None = None) -> dict` —
  per-module classification into `assessed` / `low_confidence` / `skipped`. **Honest rules:** an FM with
  force-LOW / sparse-signal-equivalent `confidence` (≤ the LD5 `low_cap`) ⇒ `low_confidence`; a `graph_modules`
  entry with no FM ⇒ `skipped`; otherwise `assessed`. Every entry tagged `"heuristic": true` (LD5 v1).
- `build_deviation_table(findings, drift_reports, fix_manifests, deferrals) -> list[dict]` — one row per finding,
  joining: `finding_id`/`module`/`locus`/`route`; the drift `verdict` + `flipped` AEL ids (the **pinning
  tests**); the fix manifest's `characterization_files` (the left-behind suite); and `applied` vs
  `deferred` + `reason`. This is the **deviation → fix → pinning-test** traceability (DESIGN §6).
- **finding_id join key (pinned — MINOR 2):** every artifact join (`findings` → `.kata/drift/<id>.json` →
  `.kata/fix_manifest/<id>.json` → `.kata/snyk/<id>.json`) uses the **SAME** `finding_id` derivation as
  `drift_gate.defer_record` / `drift_gate.build_drift_report`: `finding.get("id") or finding.get("locus") or
  "unknown"`. A module-level helper `finding_id(finding) -> str` encodes this once and is reused by every
  builder, so the table can never silently mis-join on a divergent key.
- `build_proof_rollup(drift_reports, result_json, mutation_json, snyk_reports) -> dict` — the regression+security
  proof: drift PASS/BLOCK counts, suite-green from `RESULT.json`, `allNonVacuous` from `mutation.json`, and the
  **real Snyk before/after** verdict + `newFindings` rolled up from `.kata/snyk/*.json` (NOT a RESULT.json Snyk
  field — RESULT.json carries none). A fix whose `.kata/snyk/<id>.json` records `available:false` is rolled up
  as such, honestly. Carries the **behavioral-only** limitation flag verbatim.
- `build_debug_report(confidence_map, deviation_table, proof_rollup, *, recommendations: list[dict], offered_followups: dict) -> dict`
  — compose the full data model conforming to `debug_report_schema()`; `recommendations` + `offered_followups`
  are **skill-authored inputs** the engine carries through unchanged (LD3).
- `emit_debug_report(report, path) -> None` / `load_debug_report(path) -> dict` — JSON round-trip to
  `.kata/debug/closeout.json`.

**Reuse (verified — cite by section/symbol name):** consumes the REAL artifact shapes —
`deviation.findings_schema` / `deviation.load_findings` (`tools/deviation.py`, route enum
`auto-fix-eligible|research|defer|human`); `drift_gate.drift_schema` + the `.kata/drift/<id>.json` shape
(`behavioral.verdict`/`behavioral.flipped`/`snapshot`/`verdict`) and the `defer_record` shape
(`finding_id`/`finding`/`reason`/`utc`) (`tools/drift_gate.py`); `function_model.function_model_schema`
(`module`/`confidence`/`derivation_sources`) (`tools/function_model.py`); the `.kata/fix_manifest/<id>.json`
shape (`ael`/`characterization_files`/`blast_radius_manifest`) authored by **kata-characterize** (Output
artifacts); and the **NEW `.kata/snyk/<finding_id>.json`** artifact **authored by Slice W** (shape owned here
via `snyk_report_schema()` — fixed by this plan; W writes conforming JSON, A reads it; disjoint files, resolved
at integration). The `finding_id` join key reuses the exact `drift_gate.defer_record` derivation
(`finding.get("id") or finding.get("locus")`) verified in `tools/drift_gate.py`. The engine **reads** all of
these via `json.load`; it imports **no evaluator** and adds **no exec sink**.

**Acceptance (default-FAIL, runnable — on the seeded fixtures):**
- `debug_report_schema()` returns a schema whose `description` contains the §5 behavioral-only **and** LD5
  heuristic-confidence **and** n=0-live honesty strings.
- `build_confidence_map`: the HIGH FM → `assessed`; the force-LOW/sparse FM → `low_confidence`; the graph module
  with no FM → `skipped`; every entry carries `heuristic: true`.
- `build_deviation_table`: the `auto-fix-eligible`+PASS finding row shows `applied:true` with its `flipped` AEL
  id and `characterization_files`; the BLOCK/deferred finding row shows `applied:false` + the deferral `reason`;
  `research`/`defer`/`human` findings appear with their route and **no** applied-fix claim.
- `snyk_report_schema()` returns the single-source-of-truth shape for `.kata/snyk/<id>.json`
  (`before`/`after` verdict + `findingCount`, `newFindings`, `available`).
- `build_proof_rollup`: rolls up drift PASS count, `allNonVacuous`, suite-green, and the **real Snyk
  before/after** verdict + `newFindings` read from the two `.kata/snyk/<id>.json` fixtures (the clean one →
  `newFindings:0`; the with-finding one → `newFindings ≥ 1`); an `available:false` Snyk artifact rolls up
  honestly as unavailable, never as "clean"; the behavioral-only flag is present and `True`.
- **finding_id join (MINOR 2):** the `finding_id(finding)` helper derives the key identically to
  `drift_gate.defer_record` (`id` then `locus` then `"unknown"`); a fixture whose finding has only `locus`
  joins to the drift/fix-manifest/snyk artifact keyed by that `locus` — the table row is complete (no
  silent miss).
- `build_debug_report` + `emit_debug_report`/`load_debug_report`: round-trip schema-valid JSON; skill-supplied
  `recommendations` + `offered_followups` survive unchanged.
- **No `eval`/`exec`/`subprocess` in `tools/debug_report.py`** (assertable by source scan in the test).
- **Mutation non-vacuous** on (a) the `low_confidence` vs `skipped` classification branch, (b) the
  applied-vs-deferred join branch, (c) the honesty-flag propagation, and (d) the Snyk `available:false` →
  honest-unavailable vs `newFindings` roll-up branch.

**Test seam (DESIGN §7):** the report assembly is testable on seeded artifact sets — the confidence
classification, the deviation join, and the proof rollup are each independently testable on plain dict inputs.

**depends_on:** none.

### Slice B — `kata-debrief` skill  *(the LLM-judgment author/renderer; depends_on A)*
**Skill name + category:** **`kata-debrief`**, category **`evaluate`** (peer to `kata-report`; reports, never
gates). **Tiering: never-tiered debug-spine** — debug-only; tags `kata/evaluate` + `kata/spine` +
`kata/module/debug`. **One `SKILL.md`** (no tier variants, no RUBRIC).

**Owns:** `skills/evaluate/kata-debrief/SKILL.md` (+ `resources/` only if a split-out is needed — author inline
first).

**Content (renders LD12's four elements; drives the engine; cites engine + reuse surfaces by NAME):**
1. **Confidence map (assessed/low-confidence/skipped).** Call `debug_report.build_confidence_map` over
   `.kata/function_models/*.json` (+ the graph node set for `skipped`). Render the map labeled **"heuristic
   (v1, uncalibrated)"** (LD5) — never imply calibration.
2. **Deviation → fix → pinning-test.** Call `debug_report.build_deviation_table` over `findings.json` +
   `.kata/drift/*` + `.kata/fix_manifest/*` + `deferred.json`. Render each applied fix with its pinning test(s)
   and left-behind characterization file(s); render deferred fixes with their reason (LD9/DG-12).
3. **Regression + security proof.** Call `debug_report.build_proof_rollup` over `.kata/drift/*` +
   `.kata/RESULT.json` + `.kata/mutation.json` + **`.kata/snyk/*.json`** (the per-fix before/after Snyk
   verdicts persisted by Slice W). Render the **real** Snyk before/after + new-findings count; an
   `available:false` artifact is rendered honestly as "before-scan unavailable for this fix", never as clean.
   State **"behavior preserved (behavioral drift gate)"** — **never** "structure preserved" (§5 v1 limitation,
   sourced from `drift_schema()`'s own note).
4. **Recommendations + offered follow-on (LD3).** Author the recommendations list (advisable behavior/feature
   changes the no-drift run could not make — drawn from `research`/`human`/`defer` findings + deferred records)
   and the **offered version-up/sprint** handoff; pass both into `debug_report.build_debug_report`. The
   follow-on is **offered**, handed to the **[[kata-loop]]** conductor's loop-back (Decision 3 path) — never
   auto-started.
5. **Two-tier render + emit.** Produce the **two-tier** output in the `kata-report` shape (Tier 1 concise CLI
   summary; Tier 2 full content keyed to the M5 `{{TOKEN}}` contract) so `kata-closeout` can fold the debug
   section into `.kata/CLOSEOUT.md` / `.kata/closeout.html`. Emit the data model via
   `debug_report.emit_debug_report` → `.kata/debug/closeout.json`.
- **Honest scope:** reports, never gates; states §5 behavioral-only + LD5 heuristic-confidence + **n=0 live**
  (no real-repo run has occurred) in every output; quotes the kata-evaluate verdict verbatim, never re-derives.
- **Reuse claims** verified per `protocol/reuse-claims.md`: `debug_report.*` resolve in `tools/debug_report.py`
  (Slice A); the two-tier/token contract resolves in `skills/evaluate/kata-report/SKILL.md`; the consumed
  artifact shapes resolve in `tools/deviation.py` / `tools/drift_gate.py` / `tools/function_model.py` and the
  kata-characterize fix-manifest output.

**Acceptance (slice-level, runnable):**
- `validate_skills` passes (frontmatter/schema/anchors); new-skill count increments.
- **No phantom reuse** — every cited engine surface resolves to a real symbol in `tools/debug_report.py`;
  every artifact field cited resolves to a real schema field.
- The skill **delegates every deterministic join** (confidence map / deviation table / proof rollup) to the
  engine and **never re-derives** one in prose.
- Every rendered output **states the §5 behavioral-only + LD5 heuristic + n=0-live** honesty (checked at the
  integration `kata-evaluate` gate on the seeded fixture — the render shows all four LD12 elements and never
  over-claims "structure preserved" or "calibrated confidence").

**depends_on:** A (cites the engine's real surfaces).

### Slice C — `kata-closeout` debug-section wiring  *(extend kata-closeout; forward-refs B; gated)*
**Owns:** `modules/closeout/kata-closeout/SKILL.md` (only a new, clearly-named **debug-gated region** — e.g.
a `### Step 3b — debug-run confidence report (kata/module/debug only)` block; does not alter the
general report/decision flow).

**Content:** when `kata/module/debug` is in the run's modules, `kata-closeout` **offers/composes**
**[[kata-debrief]]** (forward reference, resolved at integration — mirrors how P2b forward-referenced
`[[kata-characterize]]`) to produce the LD12 debug confidence section, and folds it into `.kata/CLOSEOUT.md` /
`.kata/closeout.html` alongside the standard report. The offered **version-up/sprint** follow-on is surfaced in
Decision 3 (loop disposition); committing the **left-behind characterization suite** is surfaced via the
existing **human-gated** Decision 2 git actions (no new git path). Absent `kata/module/debug`, this block is a
**silent no-op** — the general closeout is byte-for-byte unchanged (BC).
- **It still never gates** — kata-evaluate owns the gate; this only adds a report section + offered follow-on.

**Acceptance:**
- `validate_skills` green.
- The block is **unambiguously gated on `kata/module/debug` presence** (not on `runShape`, not on
  `target.kind=="existing"` — keying on those would break version-up BC).
- **BC line:** absent `kata/module/debug` ⇒ no debug section (silent no-op); **version-up/greenfield/one-shot
  closeouts are byte-for-byte unchanged.** (Verifiable by reading the gating condition; end-to-end confirmed at
  the integration gate — C owns no Python.)

**depends_on:** forward-refs B (name fixed by this plan; broken-wikilink resolved at integration, same wave).

### Slice D — `kata-lang-profile` skill + prose profiles  *(LD10; NO new Python)*
**Skill name + category:** **`kata-lang-profile`**, category **`execute`**. **Tiering: never-tiered
debug-spine** — debug-only specialist; tags `kata/execute` + `kata/spine` + `kata/module/debug`. **One
`SKILL.md`** (the selection + overlay contract) + a `resources/` profile pack.

**Owns:**
- `skills/execute/kata-lang-profile/SKILL.md`
- `skills/execute/kata-lang-profile/resources/` — one prompt-profile per major language
  (`python.md`, `typescript-javascript.md`, `java.md`, `go.md`, `csharp.md`, `rust.md` `[TUNABLE set]`) + a
  `config-context.md` specialist (build/config/IaC-adjacent context). Each profile is a **prose overlay**:
  idioms, test-runner conventions, common failure modes, and stack-specific characterization/diagnosis hints.

**Content (selection + overlay; cite by NAME; no fork of kata-tdd/kata-diagnose):**
1. **Selection key = the DETECTED stack** — the **footprint's file extensions are the PRIMARY signal**
   (real, always available: `.py`/`.ts`/`.tsx`/`.java`/`.go`/`.cs`/`.rs` → the matching profile). The
   comprehension pass's `.kata/function_models/*.json` `derivation_sources` is a **weak secondary hint** only.
   `function_model_schema()` carries **no `language` field**, so this plan makes **no** claim of an FM
   "module language" signal. **No new Python classifier** (LD10): the file-extension signal is read directly.
2. **Overlay, don't fork.** The profile is injected into the worker's launch context **alongside**
   `[[kata-tdd]]` (debug fix-loop) and `[[kata-diagnose]]` (diagnosis) — exactly the **IaC specialist
   precedent** (`kata-iac-terraform`/`kata-iac-cloudformation` injected alongside `kata-tdd`, selected by
   `iac_detect.classify_task`). `kata-tdd` / `kata-diagnose` are **not edited or forked**; the overlay layers
   on top via the orchestrator's dispatch (Slice W).
3. **No match ⇒ no overlay (BC).** Absent a matching profile, or absent `kata/module/debug`, the worker runs
   plain `kata-tdd`/`kata-diagnose` — unchanged.
- **Honest scope:** profiles are **prompt guidance**, not gates; they never relax the default-FAIL gate or the
  drift gate.

**Reuse (verified):** the injection mechanism mirrors the **real** IaC precedent in
`skills/coordinate/kata-orchestrate/SKILL.md` (the "IaC activation (per dispatch …) → inject the matching IaC
specialist profile alongside `[[kata-tdd]]`" block) + `iac_detect.classify_task` (`tools/iac_detect.py`); the
base skills resolve at `skills/execute/kata-tdd/` and `skills/execute/kata-diagnose/` (the tier-invariant
`RUBRIC.md` + `-light`/`-full` tiers, D26).

**Acceptance (slice-level, runnable):**
- `validate_skills` passes (frontmatter/schema/anchors); new-skill count increments; each `resources/<lang>.md`
  resolves (no dangling reference from SKILL.md).
- The SKILL.md states selection-by-detected-stack with **no new Python** and **no fork** of
  `kata-tdd`/`kata-diagnose`; absent a match ⇒ no overlay (BC).
- **No phantom reuse** — the IaC injection precedent + `iac_detect.classify_task` + the base skills all resolve
  to real surfaces.

**depends_on:** none.

### Slice E — `kata-onboard` skill  *(LD13 onboarding / convert-to-loop; NO new Python)*
**Skill name + category:** **`kata-onboard`**, category **`coordinate`** (a first-run orchestration wrapper).
**Tiering: not debug-spine** (it is the on-ramp, not a debug-only spine step) — tags `kata/coordinate` +
`onboarding`. It **composes** existing skills/tools by wikilink/symbol; it reimplements none.

**Owns:** `skills/coordinate/kata-onboard/SKILL.md`.

**Content (the dedicated first-run path; cite reuse by NAME):**
1. **Detect a fresh install.** Settings present (post-install) but **no `kata.config` / no `INTENT.md`** at the
   target ⇒ first run. Read settings via **`kata_settings.read_settings`** / locate home via
   **`kata_settings.harness_home`**; confirmed platforms via **`kata_settings.confirmed_platforms`**.
2. **Offer Debug Mode.** Route into a debug run: hand to **[[kata-initiate]]** (front door — it already does
   classify-kind, target/platform/vault config, **project find→confirm** via `project_find.find_projects`, and
   **copy-mode** via `kata_install.copy_project`), with `kind`/run-shape steered to **debug** so
   **[[kata-bootstrap]]** writes `kata.config` with `runShape:"debug"` + `modules` including
   **`kata/module/debug`** (the marker the whole debug pipeline gates on).
3. **On success, offer convert-to-loop + vault setup.** After the debug run's closeout reports success, offer to
   **convert the repo to the loop**:
   - **`kata.config`** for ongoing loop use — written by **[[kata-bootstrap]]** (Phase 3 config writer).
   - **Vault binding** — via **`kata_settings.write_settings`** / **`kata_settings.build_settings`** (the
     `vaultDir` setting; install-portability IP-A).
   - **Commit the left-behind characterization suite** — surfaced via **[[kata-closeout]]**'s existing
     **human-gated** Decision 2 git actions (the suite was authored into the target repo by
     **kata-characterize** in P2b). Human-gated; never autonomous.
   - **Scaffold `.planning/`** — *(NEW, scoped — see relabel below)* create the minimal `.planning/` layout via
     skill `Write` into the target tree (no reusable scaffolder tool exists; this is skill-prose, not a reused
     surface).
   - **Offered version-up/sprint** — hand the follow-on disposition to the **[[kata-loop]]** conductor's
     loop-back (Decision 3), matching LD12's offered handoff.
- **Honest scope:** the **Claude** install path is the verified one (install-portability §"Build note"); Codex/
  Kiro are **best-effort, documented** (IP-D) — the onboarding skill states this and never claims a verified
  cross-host install. n=0 live still holds — onboarding has not been exercised on a real fresh install end-to-end.

**Reuse (verified — install-portability is BUILT):** `kata_settings.read_settings` / `build_settings` /
`write_settings` / `confirmed_platforms` / `harness_home` (`tools/kata_settings.py`);
`project_find.find_projects` (`tools/project_find.py`); `kata_install.install` / `copy_project` /
`confirm_platform` (`tools/kata_install.py`); `intent_scaffold.write_intent` (`tools/intent_scaffold.py`);
`[[kata-initiate]]` (`modules/initiation/kata-initiate/SKILL.md` — already wires project-find + copy-mode);
`[[kata-bootstrap]]` (`skills/coordinate/kata-bootstrap/SKILL.md` — writes `kata.config` incl.
`runShape`/`target`/`modules`); `[[kata-closeout]]` (human-gated git, Decision 2/3); `[[kata-loop]]`
(`skills/coordinate/kata-loop` — loop-back / offered version-up).
- **Relabeled NEW (not phantom reuse):** "**convert-to-loop**" is **not a single existing surface** — it is a
  **NEW composition** of the verified surfaces above. The "**`.planning/` scaffold**" is **NEW** skill-prose
  (no scaffolder tool exists). Both are scoped here, not disguised as reuse.

**Acceptance (slice-level, runnable):**
- `validate_skills` passes (frontmatter/schema/anchors); new-skill count increments; every wikilink resolves to
  a real skill, every cited tool symbol resolves to a real function.
- **No phantom reuse** — `convert-to-loop` and `.planning/`-scaffold are labeled **NEW**; every other cited
  surface resolves to a real symbol/skill.
- The skill states: Debug Mode is **offered** (not auto-run); convert-to-loop + the suite commit are
  **human-gated**; the Claude install path is verified, Codex/Kiro best-effort; **n=0 live** disclosed.
- **The onboarding flow is exercised at the integration `kata-evaluate` gate** (model run — the
  detect→offer→convert sequence reads/writes the real settings/config surfaces on a seeded fixture; not a slice
  unit test, mirroring how P2a/P2b verify skill flows).

**depends_on:** none (forward-refs existing built skills/tools).

### Slice W — `kata-orchestrate` P3-seam resolution + LD10 profile injection  *(extend the P3 seam; gated)*
**Owns:** `skills/coordinate/kata-orchestrate/SKILL.md` (only: the **P3 comment-seam** after the
`## Fix-application phase` — `<!-- P3: kata-closeout consumes … LD10 … LD13 … -->`; the debug fix-loop **Fix**
dispatch step [step 3] + the diagnose dispatch site, for the LD10 injection; **and** the fix-loop **Gate** step
[step 5, the existing Snyk MCP call] + **Apply** step [step 6], for the LD12 Snyk before/after persistence).
W is the **sole** editor of `kata-orchestrate` in P3 (two slices cannot both edit it).

**Content:**
1. **Resolve the P3 comment-seam.** Replace the forward-pointer comment with the resolved wiring note: LD12 is
   produced by **[[kata-debrief]]** (offered at closeout via `kata-closeout`); LD13 onboarding by
   **[[kata-onboard]]**; LD10 profiles by **[[kata-lang-profile]]** (injected below). The closeout itself runs
   in the back-half (kata-loop → kata-closeout), not inside this skill — so the seam becomes a resolved pointer,
   not an executing stub.
2. **LD10 injection (ADDITIVE; BC: absent `kata/module/debug` ⇒ unchanged).** At the debug fix-loop **Fix**
   dispatch (step 3, alongside `[[kata-tdd]]`) and at the diagnose dispatch site (alongside `[[kata-diagnose]]`),
   inject **[[kata-lang-profile]]** as the execute-phase specialist overlay, selected by the **detected stack** —
   **the footprint's file extensions are the primary signal** (real, always available), with the comprehension
   pass's `.kata/function_models/*.json` `derivation_sources` as a **weak secondary hint** — mirroring the
   existing **IaC activation** block. **No new Python**: the file-extension signal is read directly, not via a
   new classifier. Absent a matching profile, or absent `kata/module/debug`, **no overlay** (BC).
3. **LD12 Snyk before/after persistence (ADDITIVE; BC: absent `kata/module/debug` ⇒ unchanged).** The
   fix-application phase **already** establishes a **before (pre-fix)** and **after (fixed-worktree)** state for
   the drift gate's before/after suite runs, and **already** invokes `mcp__Snyk__snyk_code_scan` (step 5). P3
   **piggybacks on those same two states**: run the Snyk MCP on the **before** and **after** states and **`Write`
   the verdicts** to **`.kata/snyk/<finding_id>.json`** conforming to `debug_report.snyk_report_schema()` (Slice
   A owns the shape). **No new Python, no new exec sink** — the Snyk MCP call already exists in the loop;
   persistence is a `Write`. `finding_id` is derived with the same key as everywhere else
   (`finding.get("id") or finding.get("locus")`). If a meaningful before-scan is not obtainable for a fix, record
   `available:false` honestly (no fabrication).
- **`[[kata-debrief]]` / `[[kata-onboard]]` / `[[kata-lang-profile]]`** are forward references (sibling slices
  create them — expected not to exist during W editing; no broken-wikilink concern at this stage, per the P2a/P2b
  forward-ref convention).

**Acceptance:**
- `validate_skills` green.
- The LD10 injection is **unambiguously gated on `kata/module/debug` presence** (not on `runShape`, not on
  `target.kind=="existing"`); the detected stack uses **footprint file extensions** as the primary signal.
- **The Snyk before/after artifact is written per applied fix** — `.kata/snyk/<finding_id>.json` conforming to
  `debug_report.snyk_report_schema()`, gated on `kata/module/debug` (absent it ⇒ no Snyk artifact, no change).
  An unobtainable before-scan is recorded `available:false`, not fabricated.
- The injection + persistence add **no new Python** and **no new exec sink** (the per-dispatch
  specialist-injection mechanism and the Snyk MCP call already exist; persistence is a `Write`).
- **BC line:** absent `kata/module/debug` ⇒ no profile overlay, no `.kata/snyk/*` artifact, and the P3 seam is
  an inert resolved comment; **version-up/greenfield runs are byte-for-byte unchanged.** (Verifiable by reading
  the gating condition; end-to-end confirmed at the integration gate — W owns no Python.)

**depends_on:** D (cites `[[kata-lang-profile]]`'s name/contract); A (writes JSON conforming to
`debug_report.snyk_report_schema()` — the `.kata/snyk/<id>.json` shape A owns; disjoint files, resolved at
integration); forward-refs B (`[[kata-debrief]]`) and E (`[[kata-onboard]]`), names fixed by this plan,
resolved at integration.

## Wave DAG
```
ownership:
  A: [tools/debug_report.py, tools/tests/test_debug_report.py, tools/tests/fixtures/debug_report/]
  B: [skills/evaluate/kata-debrief/]
  C: [modules/closeout/kata-closeout/SKILL.md]          # only the debug-gated Step 3b region
  D: [skills/execute/kata-lang-profile/]
  E: [skills/coordinate/kata-onboard/]
  W: [skills/coordinate/kata-orchestrate/SKILL.md]      # only the P3-seam region + LD10 injection at dispatch
waves:
  - wave: 1
    slices: [A, D, E]
  - wave: 2
    slices: [B, C, W]
depends_on:
  A: []
  D: []
  E: []
  B: [A]
  C: []   # forward-refs B (name fixed by this plan; broken-wikilink resolved at integration, same wave)
  W: [D, A]  # cites D's name; writes JSON conforming to A's snyk_report_schema (artifact contract, NOT a code
             # import — resolved at integration); forward-refs B, E (names fixed by this plan)
```
- **Wave 1 (parallel):** A (the pure engine — no deps), D (LD10 profiles — no deps), E (LD13 onboarding —
  composes built surfaces, no deps). Disjoint files → no interdependency.
- **Wave 2 (parallel):** B (kata-debrief, cites A's engine by name), C (kata-closeout debug section,
  forward-refs B), W (kata-orchestrate seam + LD10 injection + LD12 Snyk-artifact persistence; cites D, writes
  JSON conforming to A's `snyk_report_schema()`, forward-refs B/E). Disjoint files → no interdependency; the
  A→W link is a **shared artifact contract, not a code dependency** (W writes conforming JSON; it imports
  nothing from A) — resolved at integration along with the forward-ref wikilinks (P2a/P2b convention).
- Concurrency: ≤3 workers per wave; all slices in git worktrees; disjoint ownership verified before dispatch.

## LD12 honesty integrity (pinned)
The report is the project's signature over-claim surface — pin the honesty at the **engine**, not just the prose:
1. **Behavioral-only.** `build_proof_rollup` carries the behavioral-only limitation flag sourced from
   `drift_schema()`'s own description; `kata-debrief` renders "behavior preserved (behavioral drift gate)" and
   **never** "structure preserved." `drift_gate.structural_drift_verdict` stays the non-executing seam.
2. **Heuristic confidence.** `build_confidence_map` tags every entry `heuristic: true` and uses the LD5
   `low_cap` to force-LOW → `low_confidence`; modules with no FM → `skipped`. No calibration is implied; the
   isotonic-calibration fast-follow is named as deferred.
3. **n=0 live.** `debug_report_schema()`'s description states no real-repo run has occurred; `kata-debrief`
   renders this in every output. The integration gate proves the **seeded-fixture** path; the live dogfood is a
   separately-labeled exit item (Risks).
4. **Real Snyk, not fabricated.** `build_proof_rollup` rolls up the **real** before/after Snyk verdicts that
   Slice W persists to `.kata/snyk/<id>.json` (the fix loop's existing MCP call); RESULT.json carries no Snyk
   field, so nothing is invented from it. A fix with no obtainable before-scan is rolled up `available:false`,
   never as "clean."
These four are **mutation-covered** (Slice A acceptance) so the honesty cannot be silently regressed.

## §5 v1-limitation handling (pinned — carried forward from P2b)
- v1 = **behavioral drift only**; the structural / public-surface invariance layer (public-API diff = ∅ +
  AST-edit-script) is a **FAST-FOLLOW, NOT v1** — `drift_gate.structural_drift_verdict` remains the named
  non-executing seam (raises `NotImplementedError`).
- Every P3 artifact (report data model description, kata-debrief prose, the rendered MD/HTML) **states** this so
  the "structure preserved" promise (F3) is honestly scoped to **behavioral** enforcement in v1.

## Integration gate (after the frontier drains)
pytest green (incl. `test_debug_report.py`) · `validate_skills` (expect new count — `kata-debrief`,
`kata-lang-profile`, `kata-onboard` are new; `kata-lang-profile/resources/*.md` resolve) ·
**Snyk code scan on `tools/debug_report.py`** (new first-party Python — per CLAUDE.md security rule;
rescan-to-clean) · `test_exec_safety.py` regression still green (**no new sink** — debug_report is pure;
profiles are prose; onboard composes sink-free/registered surfaces) · `gate_emit` RESULT/footprint/mutation
(`emit_gate_artifacts`, `prove_non_vacuous`) · README regen (`validate_skills.py --write`). Then fresh-context
**`kata-evaluate`** (9-rubric, default-FAIL) — which **exercises the seeded-fixture LD12 render end-to-end**
(the four elements present; the regression+security proof reads the **real `.kata/snyk/*.json` before/after**
[clean → `newFindings:0`; with-finding → `≥1`; `available:false` → honest]; **no "structure preserved" / no
"calibrated confidence" over-claim**; n=0 disclosed),
the **LD10 overlay injection** (debug dispatch injects the matching profile; absent-match ⇒ no overlay), and the
**LD13 onboarding** detect→offer→convert sequence on a fixture → standing **D98 `kata-review`** → operator merge
gate. **n=0 live is disclosed at the gate, not papered over.**

## Risks / escalation triggers
- **LD12 over-claim is the load-bearing honesty surface.** If a slice finds the report "needs" to assert
  structure-preservation or calibrated confidence to look complete, **STOP and escalate** — that violates the
  §5/LD5 FREEZE notes. The honesty is engine-pinned + mutation-covered; do not move it to prose-only.
- **n=0 live.** Debug Mode has **never** run end-to-end on a real repo. Do **not** let LD12/LD13 acceptance
  imply otherwise. P3 proves on seeded fixtures; a real-repo dogfood is scoped as an explicit, separately-labeled
  exit item. Claiming a live run is a defect.
- **Phantom reuse (LD13).** `convert-to-loop` and the `.planning/` scaffold are **NEW** (no single existing
  surface) — they are labeled NEW here. If a slice silently re-labels them "reuses the existing convert flow",
  STOP — that is the project's signature failure mode (`protocol/reuse-claims.md`).
- **No new exec sink.** If any slice finds it "needs" a subprocess/`eval` (e.g. to run the target's tests for the
  proof rollup), STOP and escalate — the proof rollup **reads** the already-emitted `RESULT.json`/`mutation.json`/
  drift proofs; it never runs the suite. `debug_report.py` is pure; onboarding composes
  registered/sink-free surfaces only.
- **LD10 must not fork the spine.** If a slice finds it "needs" to edit `kata-tdd`/`kata-diagnose` bodies to
  layer the profile, STOP — the overlay is **injected at dispatch** (IaC precedent), not forked into the base
  skills. No new Python classifier (LD10 says prose-only).
- **BC.** Any change that alters a non-debug run is a defect — every P3 surface is purely additive, gated on
  `kata/module/debug`; absent that marker, version-up/greenfield/one-shot runs are byte-for-byte unchanged.
- **Scope creep.** If a slice finds it needs to re-discover/re-fix/re-gate, STOP — that is P2a/P2b, already
  built. P3 **reads** their artifacts and reports.

## Judgment calls (flagged for the freeze gate)
- **Build order / split recommendation (explicit): ship LD12 first, then LD10 + LD13 in parallel.** LD12 is the
  highest-value, most self-contained payoff — it makes the entire P1/P2 pipeline legible to a human and has a
  clean pure-Python engine (Slice A) that everything downstream cites. Recommend building **Wave-1 Slice A +
  Wave-2 Slice B + Slice C** as the **LD12 milestone first**, then **LD10 (D + W-injection)** and **LD13 (E)**
  as a second milestone (both are lower-risk: LD10 is prose-only, LD13 composes already-built install surfaces).
  The wave DAG above lets all of P3 run together if desired, but if splitting, **LD12 ships first**.
- **LD12 = a NEW `kata-debrief` skill offered by `kata-closeout`, not a fork of `kata-closeout`.** This matches
  the debug-spine convention (kata-comprehend/kata-deviate/kata-characterize are all separate debug-only skills)
  and keeps `kata-closeout` BC-clean (debug section is a gated no-op when absent). **Divergence to confirm:** the
  P2b orchestrate seam literally says "kata-closeout consumes …"; this plan keeps kata-closeout as the **offering
  host** but delegates the LD12 content to `kata-debrief`. Confirm this is the intended reading (vs. inlining the
  report into kata-closeout).
- **LD12 engine (`tools/debug_report.py`) is justified NEW Python.** The confidence-map / deviation-join / proof
  rollup is genuinely deterministic and testable (it mirrors how `deviation.py`/`drift_gate.py` own their
  schemas). It is **pure** (no sink), mutation-proof, and Snyk-scanned — meeting the "new Python only when a
  deterministic testable surface is genuinely needed" bar.
- **LD13 = a NEW `kata-onboard` skill, not a `kata-initiate` Phase-0 extension.** DESIGN says "dedicated
  first-run path"; a standalone skill keeps `kata-initiate` (shared spine) unforked and BC-clean. **Confirm**
  vs. extending kata-initiate.
- **`.planning/` scaffold = skill `Write` (prose), not a tool.** No scaffolder exists; to honor "reuse-max /
  minimal new Python," I propose skill-prose. **Flag:** if the freeze prefers testability, a tiny pure
  `tools/planning_scaffold.py` (pure file writes, `..`-guarded) is the alternative — call it.
- **LD10 selection key = the detected stack from the comprehension pass + footprint extensions, injected at
  dispatch (IaC precedent), no new Python.** Confirm this is acceptable (LD10 says prose-profiles only). If the
  freeze wants a deterministic stack-classifier, that is a **return-to-DESIGN** item (LD10 currently forbids new
  Python).
- **`skipped` confidence-map category needs a module inventory.** `build_confidence_map` computes `skipped` from
  graph nodes that have no FM; this assumes the graph node set is available at closeout. **Flag:** confirm the
  graph (`kata.graph.json`) is present at closeout, or fall back to "FM-set only" (then `skipped` = modules in
  the footprint with no FM). Either is honest; pick one at freeze.
- **n=0 live exit criterion.** Recommend P3 exits on seeded-fixture proof + **explicit n=0 disclosure**, with a
  real-repo dogfood as a separate, honestly-labeled follow-up. **Confirm** the freeze accepts this rather than
  requiring a live run as a P3 blocker (Debug Mode build was PARKED behind install-portability + kata-preflight;
  both now exist, so a live dogfood is newly possible but out of P3's authoring scope).
