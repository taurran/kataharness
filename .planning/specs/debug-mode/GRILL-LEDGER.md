---
title: "Debug Mode — grill decision ledger"
status: GRILL COMPLETE — convergence gate SHIP (2026-06-25). Ready to FREEZE via kata-design-doc; build gated behind install-portability (DG-10b).
date: 2026-06-25
spec: debug-mode
method: skills/plan/kata-grill (standard→advanced depth)
---

# Debug Mode — GRILL LEDGER

Running record of the design interrogation. Each branch: chosen option · rejected alternatives · rationale ·
provenance. Convergence (per RUBRIC) requires every branch resolved + no fuzzy terms + every edge defined +
no contradictions + two-builders-can't-diverge, then a fresh-context `kata-review` SHIP.

## Frozen framing (operator, pre-grill — treated as LOCKED inputs, not re-litigated)
- **F1** Debug Mode is a **top-level KataHarness mode, peer of version-up** — selected at bootstrap, pointed at a
  whole codebase, **self-contained**; it debugs the entire codebase **without touching other modes**.
- **F2 (anti-bloat)** No debug agent injected into the loop / other modes. Specialists live **inside** the mode.
- **F3** Intent = behavior-preserving: **bugs out, structure/features fixed.** Opposite of version-up.
- **F4** Reuse built pieces maximally (version-up footprint+regression discipline, `kata-diagnose`, `kata-graph`,
  Snyk + `kata-evaluate` + D98 `kata-review`); NOT dependent on `capability-aware-assignment`.
- **F5** Strategic role = the onboarding/conversion killer-app (debug-in-confidence → convert to loop + vault).

## Open decision tree (DG-n) — enumerated; resolve in dependency order
- **DG-1 — The "nothing broken" guarantee when the target has weak/no tests.** The regression signal is the
  spine of "confidence"; converting devs often have thin coverage. (Provenance: F3/F5 + version-up's
  "full baseline suite green" gate assumes tests exist.) **← load-bearing; round 1**
- **DG-2 — Change scope: bug-fix-only vs. behavior-preserving cleanups vs. broader.** The fix-vs-"promote coding
  efficiency" line. (Provenance: BRIEF open Q "fix-vs-improve line".) **← round 1**
- **DG-3 — One-shot vs. iterate-until-clean vs. resumable.** Reconcile operator's "one-shot" with "systematic,
  thorough, assess all modules". (Provenance: BRIEF.) **← round 1**
- **DG-4 — Bug-discovery sources.** What finds the defects (security stack, test run, static/type/lint,
  kata-diagnose reasoning, dynamic/property). (Provenance: F4.) **← round 1**
- **DG-5 — Whole-codebase footprint vs. version-up's narrow footprint.** What "the whole thing" means for
  ownership/blast-radius and one-shot sizing. (Provenance: F1 vs version-up footprint.)
- **DG-6 — Systematic-sweep coverage strategy.** Graph-ordered traversal? risk-ranked? how "all modules/tie-ins/
  logic" is made exhaustive yet bounded. (Provenance: BRIEF.)
- **DG-7 — In-mode specialist roster + selection.** Which language/config specialists, prompt-profiles, selection
  by detected stack — kept inside the mode (F2). (Provenance: F2 + operator's original capture.)
- **DG-8 — Fix application + human gate.** Auto-apply (gated) vs. propose; per-fix vs. batch; backout. (F3/F4.)
- **DG-9 — Confidence reporting.** What evidence the closeout shows to substantiate "debugged in confidence".
- **DG-10 — Onboarding integration.** Dedicated first-run path tied to install + the convert-to-loop handoff. (F5.)
- **DG-11 — Mode mechanics.** How selected (a `mode`/`delivery.shape` value), bootstrap wiring, `kata.config` shape.
- **DG-12 — No-fix-found / can't-fix-safely behavior.** What happens to a bug it can't fix without drift (escalate?
  defer? report-only?).

## Resolved branches (round 1, 2026-06-25)

- **DG-1 → REFRAMED: confidence basis = DEEP COMPREHENSION FIRST (the function-model), not characterization tests.**
  Before any change, Debug Mode runs a **stronger, thorough `kata-graph`/Graphify review** to assess + document the
  **intended function** of the codebase: ingest ALL structural context (graph: def/ref/call/import + PageRank) +
  all available context (docs, comments, docstrings, types, config/IaC), **combine** them, and **determine each
  module's function**; then **review the code's state for alignment** with that derived function. Where context is
  thin, **assess deeply and synthesize the function** (flagged as lower-confidence). A **bug = a deviation of the
  code from its derived/intended function.** *Rationale:* characterization tests pin *current* behavior (bugs and
  all); a function-model gives an **oracle of intent** to debug against. Provenance: operator round 1.
  - **Opens DG-1b** (regression signal — the function-model says *what's wrong*; we still need proof a fix doesn't
    break *unrelated* behavior) and **DG-1c** (which comprehension inputs strengthen the model).
- **DG-2 → RESOLVED: bug fixes + security ONLY (strictly behavior-preserving).** Debug Mode does NOT do feature/
  behavior changes. **But the run also produces a RECOMMENDATIONS report** documenting where behavior/feature
  changes are advisable — and **routes the user to run a `version-up` or `sprint` pass** for those. Clean
  separation: debug = preserve behavior; version-up/sprint = change behavior. Provenance: operator round 1.
  - **Opens DG-2b** (the recommendations→version-up/sprint handoff artifact + how it's offered).
- **DG-3 → RESOLVED: the pass model is a USER CONFIG CHOICE at bootstrap** — (1) one thorough graph-ordered pass,
  resumable (loop-back) **OR** (2) loop-until-dry (repeat until a pass finds nothing new). Both offered, cleanly
  labeled, selected at configuration. Provenance: operator round 1.
- **DG-4 → PARTIAL: confirmed discovery sources** = Snyk security stack · run existing tests · static analysis/
  types/lint · `kata-diagnose` reasoning · **+ the in-loop research agent (`kata-research`)** to assess modules/
  language and gather **codebase-tailored** debugging research. **Opens DG-4b** (brainstorm further sources).
  Provenance: operator round 1.

## New open branches (opened by round 1)
- **DG-1b — Regression signal for fixes.** Given comprehension-first: do we ALSO generate characterization/
  regression tests (proving a fix doesn't break unrelated behavior + leaving a suite behind for conversion), rely
  on the existing suite + re-run, or behavior-snapshot diff? (The function-model is the *oracle*; this is the
  *don't-regress* proof.) **← round 2**
- **DG-1c — Comprehension inputs.** What feeds the function-model beyond the graph (docs/comments/types/config,
  commit history, `kata-understand` reuse, research-agent idioms, low-confidence flagging). **← round 2**
- **DG-2b — Recommendations handoff.** The behavior/feature-change recommendations artifact + how Debug Mode
  offers/launches a follow-on `version-up`/`sprint`.
- **DG-4b — Further discovery techniques (brainstorm).** function-model deviation detector · cross-module
  tie-in/contract mismatch · commit-churn/blame hotspots · dynamic (fuzz/property/sanitizers) · dependency SCA ·
  concurrency/race. **← round 2**

## Resolved branches (round 2, 2026-06-25)
- **DG-1b → RESOLVED: generate scoped characterization tests.** For each fix's blast-radius, generate regression
  tests pinning current behavior **except the deviation being fixed**; run before/after. So the confidence basis =
  **function-model (oracle of intent) + scoped characterization suite (don't-break proof)** — and the generated
  suite is **left behind** as conversion value (a tested repo). Provenance: operator round 2.
- **DG-1c → RESOLVED: comprehension inputs = graph + core context (assumed) + ALL of:** commit history/blame
  (intent-over-time + churn hotspots) · **cross-module contract inference** (the tie-ins) · ~~reuse `kata-understand`~~
  · ~~`kata-research` idioms~~ + low-confidence flagging (thin-context areas flagged, deepened or surfaced — never
  silently guessed). Provenance: operator round 2. **⚠ SUPERSEDED by round-7 H2/H5:** the function-model is built by
  the NEW **`kata-comprehend`** (NOT `kata-understand` — phantom reuse); in-mode idiom research lives in
  `kata-comprehend` (NOT escalation-routed `kata-research`). See the round-7 remediation + the synced design summary.
- **DG-4b → RESOLVED: v1 discovery techniques = the confirmed five (Snyk · run tests · static/types/lint ·
  `kata-diagnose` · ~~`kata-research`~~ **⚠ see round-7 H5**: general comprehension/idiom research moved into
  `kata-comprehend`; `kata-research` stays escalation-only, dropped from the discovery list) PLUS:** the
  **function-model deviation detector** (the headline SEMANTIC
  source) · **cross-module tie-in/contract mismatch** · **commit-churn/blame hotspots** · **dynamic analysis**
  (fuzz/property/sanitizers, stack-gated). Dependency SCA + concurrency/race = also-considered (defer/free-text).
  Provenance: operator round 2.

## Resolved branches (round 3, 2026-06-25)
- **DG-8 → RESOLVED: apply through the loop, gate at closeout + backout.** Each fix is TDD'd + passes
  `kata-evaluate`/`kata-review`, integrated; the whole run is presented at the closeout human gate with a clean
  one-command backout. Consistent with version-up's gated autonomy. Provenance: operator round 3.
- **DG-12 → RESOLVED: defer + report (route to version-up).** A real bug that can't be fixed without behavior/
  structure drift is **not forced** — it's logged to the recommendations report as "needs a behavior change →
  version-up / human decision." Preserves the no-drift guarantee; nothing silently broken. Provenance: operator round 3.
- **DG-5/6 → RESOLVED: whole-repo comprehension; per-fix footprint-scoped changes; graph + risk-ordered sweep.**
  Understand the entire codebase (the function-model); each **fix** touches only its blast-radius (version-up
  footprint discipline); the sweep visits modules in dependency/PageRank order, **weighting churn/hotspots first**.
  Thorough yet bounded. Provenance: operator round 3.
- **DG-9 → RESOLVED: closeout confidence report shows ALL of:** per-module **confidence map** (assessed/low-
  confidence/skipped) · **each bug: deviation → fix → pinning test** · **regression + security proof** (suite green
  + new tests, mutation non-vacuous, Snyk before/after) · the **recommendations list** (behavior/feature changes
  deliberately NOT made → version-up/sprint). Provenance: operator round 3.

## Resolved branches (round 4, 2026-06-25)
- **DG-11 → RESOLVED: a run-shape `debug` (peer of version-up), `target.kind == existing`.** Mirrors version-up on
  the run-shape axis; `kata-bootstrap` router selects it; `kata-orchestrate` stays config-driven. ("Mode" = the
  user-facing word; run-shape = the mechanism.) Provenance: operator round 4.
- **DG-7 → RESOLVED: prompt-profile specialists by detected stack, in-mode.** System-prompt profiles (per major
  language + a config/context specialist) layered on `kata-tdd`/`kata-diagnose`, selected by the detected stack,
  living **inside** Debug Mode (F2). No new Python (prefer-in-context). Provenance: operator round 4.
- **DG-2b → RESOLVED: recommendations doc + offered handoff at closeout.** Closeout lists behavior/feature
  recommendations and **offers** to launch a `version-up`/`sprint` run seeded with them (human opts in; uses the
  loop-back/conductor). No behavior change without the user's choice. Provenance: operator round 4.
- **DG-10 → RESOLVED: dedicated first-run path IN v1.** Fresh install pointed at a repo → bootstrap offers Debug
  Mode as the intro run; on success, offer **convert-to-loop + vault setup**. **Consequence:** this **couples Debug
  Mode v1 to (part of) `install-portability`** — the first-run detection + bring-your-own-vault binding + the
  convert-to-loop handoff. Updates the earlier "fully decoupled, ships standalone" note. Provenance: operator round 4.
  - **Opens DG-10b** (how much of install-portability is in v1 scope) and **DG-10c** (what "convert to the loop"
    concretely does to the repo).

## Resolved branches (round 5, 2026-06-25)
- **DG-1-edge → RESOLVED: research-first, then defer.** Low-confidence-intent areas → dispatch `kata-research` to
  raise confidence; if still low, **defer** the candidate to the recommendations report (don't auto-fix against an
  uncertain oracle). *Implication to confirm at FREEZE (not re-litigated): objective defects — failing tests, type
  errors, Snyk findings — don't depend on the oracle, so they stay fixable regardless of intent-confidence.*
  Provenance: operator round 5.
- **DG-1b-edge → RESOLVED: pre-flight establishes the env; fallback to snapshot/report-only.** Reuse D29 pre-flight
  to provision deps + a runnable suite; if the env can't be made runnable, that area drops to behavior-snapshot diff
  or report-only (honest — no false confidence). Provenance: operator round 5.
- **DG-10b → RESOLVED: build FULL `install-portability` FIRST.** Debug Mode is sequenced **after** a complete
  install-portability build (cleanest dependency story). **Roadmap consequence: install-portability becomes Debug
  Mode's immediate predecessor.** Provenance: operator round 5.
- **DG-10c → RESOLVED: convert-to-loop writes** kata.config · `.planning/` scaffold · **commits the generated
  characterization suite** (new regression baseline) · vault binding. **Opens DG-10c-import** (below — operator
  asked to evaluate import-vs-in-place). Provenance: operator round 5.

## Resolved branches (round 6, 2026-06-25)
- **DG-10c-import → RESOLVED: configurable per run — in-place (worktrees) DEFAULT, import-a-copy OPT-IN.**
  Default = operate on the real repo in **isolated git worktrees** (aggressive-but-safe, tests run in the real
  env, cheap for large repos via shared git objects); the **vault holds the artifacts** (function-model,
  `.planning/`, report, generated test suite), not a source mirror. **Import-a-copy** is an offered bootstrap
  option for special cases (read-only / untrusted / deliberate hard-fork) — it needs its own pre-flight to make the
  copy runnable, and **falls back to snapshot/report-only if it can't** (shares the DG-1b-edge confidence-fallback).
  Provenance: orchestrator evaluation + operator round 6.

## ✅ Decision tree COMPLETE (all branches resolved, 2026-06-25)
Every DG branch has a chosen option + rationale + provenance. **Next per RUBRIC: fresh-context `kata-review`
convergence gate** ("could two independent builders still diverge?") — the griller does NOT self-certify (L8).
On SHIP → hand to `kata-design-doc` (FREEZE) to compile the DESIGN contract; glossary terms (`kata-comprehend` ·
function-model · intended-function oracle · function deviation · 7-step deviation pipeline · characterization suite ·
confidence map (MSAS) · drift gate · debug run-shape · in-mode specialist · recommendations handoff · convert-to-loop)
bake into CONTEXT.md at freeze. **FREEZE note:** the H4 v1 caveat (structural drift only loosely guarded until the
surface/AST fast-follow) MUST surface in the DESIGN's backward-compat/limitations section (F3 is frozen framing).

## Design summary (FREEZE handoff — SYNCED to round 7; supersedes the original-HOLD text above as history)
Debug Mode = a **run-shape `debug`** (peer of version-up, `target.kind==existing`), self-contained, selected at
bootstrap, pointed at a whole codebase. Pipeline:
1. **Comprehend** (whole-repo): **`kata-comprehend` — a NEW in-mode capability** (H2; NOT `kata-understand`, which is
   post-run/map-only) — ingests `kata-graph`/Graphify + all context (docs/comments/types/config + commit history +
   cross-module contract inference) and builds a **`function_model`** per module: **executable pre/postcondition
   assertions + NL `intent_summary` + behavioral examples + `derivation_sources` + `confidence`** (H1, full form),
   checkable via a spec-wrapper; every FM is a hypothesis to corroborate. **Confidence-tiering (H3, v1 heuristic):** a
   composite `C = w1·MSAS + w2·(1−self-consistency-entropy) + w3·StructuralPrior` (NOT verbalized confidence);
   **force-LOW** for sparse-signal modules; formal isotonic calibration = fast-follow. In-mode comprehension/idiom
   research lives in `kata-comprehend` (H5) — distinct from escalation-routed `kata-research`.
2. **Discover** (graph + churn-risk ordered sweep) via the **full 7-step deviation pipeline** (H2): multi-signal
   candidates (function-model **deviation detector** + cross-module tie-in/contract mismatch + Snyk + run existing
   tests/SBFL + static/types/lint + `kata-diagnose` + dynamic stack-gated) → semantic LLM comparison →
   **self-consistency ≥2/3** → **objective-corroboration HARD gate** (≥1 tool/test/type/Snyk co-locates, else
   LLM-only→human) → **adversarial refute-or-promote**.
3. **Fix** (per-fix, footprint-scoped, in worktrees): bug+security only, behavior-preserving; **generate scoped
   characterization tests** (a NEW capability, H7) pinning behavior except the fixed deviation; **`kata-preflight`
   (forward dep, H6) establishes the runnable env**, else snapshot/report-only. Routing: high-confidence intent →
   auto-fix; low-confidence → research(≤2) → **defer to recommendations** if still unclear; objective defects
   (test/type/Snyk) fixed regardless; can't-fix-without-drift → **defer**.
4. **Gate**: the **v1 drift gate = BEHAVIORAL** (H4) — characterization/golden-master + baseline-suite-green EXCEPT an
   **Allowed Exception List** (the nominated buggy test[s]); any previously-green test→RED = BLOCK. *(Surface/API-diff
   + AST-edit-script structural layer = fast-follow; v1 structural-drift exposure noted.)* Then `kata-evaluate` +
   standing D98 `kata-review`; apply through the loop, **human gate at closeout + one-command backout**. Specialists =
   in-mode prompt-profiles by detected stack.
5. **Closeout**: confidence report (per-module confidence map · each deviation→fix→pinning test · regression+security
   proof · recommendations list) + **offered handoff** to `version-up`/`sprint` for the behavior/feature recs.
6. **Onboarding (v1)**: dedicated first-run path — **forward dep on full `install-portability` built first** (H6;
   convert-to-loop surface pinned by the install-portability DESIGN, referenced not invented here); convert-to-loop
   writes kata.config + `.planning/` + commits the characterization suite + vault binding.
**NEW capabilities to build:** `kata-comprehend` · the 7-step deviation pipeline · characterization-suite generation ·
the behavioral drift gate. **Forward deps:** full `install-portability` · `kata-preflight`. **Reused (verified real):**
worktrees · version-up footprint discipline · `kata-diagnose` · `kata-evaluate` · D98 `kata-review` · run-shape
mechanism · gate/backout/closeout · Snyk. Pass model (one graph-ordered resumable pass | loop-until-dry) and execution
locus (in-place worktrees | import) are **bootstrap config choices**.

## Convergence gate — HOLD (fresh-context kata-review, 2026-06-25)
The griller resolved *which* decisions exist but stopped at **labels, not mechanisms** for the hardest semantic
concepts (the survey-not-grill failure, RUBRIC L21-27). Two builders would diverge. **Back to Phase 1 on H1–H4;
clear H5–H7; re-run the gate before FREEZE.**

**BLOCKERS:**
- **H1 — the function-model / "intended function" oracle (DG-1) is TBD.** No artifact schema (what "intended
  function" *is* on disk) and no concrete deviation-detection procedure. The single most divergence-prone
  component is 100% unspecified. PIN: the function-model schema + the deviation detector (inputs→comparison→output).
- **H2 — `kata-understand` reuse is PHANTOM MACHINERY (caught by `protocol/reuse-claims.md`).** `kata-understand`
  is a **post-run, map-only** comprehension tool (footprint∩graph; "does not judge"; ingests no docs/types to
  derive intent) — the OPPOSITE of a pre-change whole-repo intent-derivation oracle. The function-model is a **NEW
  capability**, not reuse. PIN: relabel NEW, scope ownership/acceptance/cost; re-examine the F2 anti-bloat rationale.
- **H3 — confidence-tiering (DG-1-edge) is undefined.** No signal, no threshold for high- vs low-confidence intent.
  The research→defer routing gates on a boundary that doesn't exist. PIN: the concrete confidence signal + cutoff.
- **H4 — the no-structural-drift gate (F3/DG-2) — the BRIEF's named load-bearing design — is still hand-wavy.** The
  ledger pinned scope (bug+security), regression signal (characterization tests), footprint — but NOT the
  public-surface/structural-invariance assertion. PIN: the actual surface-invariance mechanism, or explicitly state
  footprint+baseline-green IS the whole gate (surface-invariance dropped).

**SECONDARY (pin or explicitly defer with an owner):**
- **H5 — `kata-research` used outside its contract** (it's escalation-routed, no-write, scoped to "must-deliver
  feature, no in-plan solution" — not a whole-codebase comprehension sweep). Route via a real escalation or label NEW.
- **H6 — forward deps on un-frozen `install-portability` + un-built `kata-preflight` (D29, planned not built).**
  Debug Mode's first-run (DG-10c) presumes install-portability decisions not yet made (its config layer may fold
  into `kata-initiate`). Mark DG-10c's surface "pinned by install-portability DESIGN, not here." Label preflight a
  forward dependency, not reuse.
- **H7 — characterization-suite generation (DG-1b) is NEW**, not clean `kata-tdd` (red-green for *new* behavior) /
  `kata-diagnose` (one test at a known seam) reuse. Scope it NEW.

**Verified-solid (so the re-grill is targeted):** worktree isolation · version-up footprint+baseline-green
discipline · `kata-diagnose` root-cause loop · the run-shape mechanism (DG-11) · gate/backout/closeout (DG-8). The
pipeline *skeleton* composes; the **semantic core (H1–H4)** is what needs another Phase-1 round.

## Convergence-gate remediation — H1–H7 RESOLVED (round 7, research-grounded, 2026-06-25)
Grounded in `RESEARCH.md` (4 research threads + 3 repo assessments). v1-ambition calls = operator round 7.

- **H1 → RESOLVED: the oracle = an executable+NL `function_model` per module (FULL).** LLM-derived **runnable
  pre/postcondition assertions + NL `intent_summary` + behavioral examples + `derivation_sources` + `confidence`**,
  checkable via a spec-wrapper (inject pre/post, run) — no provers. Every FM is a HYPOTHESIS to corroborate
  (repo-level spec-gen ~20% fidelity). Reinforced by debug-skill's "invariant-as-intent-assertion" idea.
- **H2 → RESOLVED: the FM-builder is a NEW in-mode capability — `kata-comprehend`** (pre-change, whole-repo,
  confidence-tiered; derives intent from graph+docs+types+commit+callers). NOT `kata-understand` reuse (that's
  post-run, map-only — phantom reuse, caught by the gate). Scope NEW with own ownership/acceptance/cost; F2
  anti-bloat holds (in-mode). **Deviation detection = the FULL 7-step pipeline**: multi-signal candidates (static/
  type/test-SBFL + peer-anomaly + graph-localization) → semantic LLM comparison → **self-consistency ≥2/3** →
  **objective-corroboration HARD gate** (≥1 tool/test/type/Snyk co-locates, else LLM-only→human) → **adversarial
  refute-or-promote** (ties to D98 `kata-review`) → fix gate (re-run on patch + Snyk).
- **H3 → RESOLVED: confidence-tiering = MSAS + self-consistency HEURISTIC for v1** (composite of multi-source
  agreement + cross-sample behavioral-semantic consistency + structural prior; **NOT verbalized confidence**).
  Sensible default cutoffs route auto-fix / research(≤2 rounds) / defer; **force-LOW** for sparse-signal modules.
  **Formal isotonic calibration on a labeled corpus = fast-follow** (deferred), tuned by feel until a corpus exists.
- **H4 → RESOLVED: drift gate = BEHAVIORAL for v1, surface/AST fast-follow.** v1 = characterization/golden-master
  + **baseline-suite-green EXCEPT an Allowed Exception List** (the nominated buggy test[s] that may go RED→GREEN);
  any previously-green test→RED = BLOCK; snapshots byte-identical (scrub nondeterminism). **Fast-follow**: the
  public-API-diff(=∅) + AST-edit-script(body-updates-only) surface/structural layer (per-language plugins +
  Semgrep/tree-sitter fallback). *Honest v1 caveat: structural drift only loosely guarded until the fast-follow.*
- **H5 → CLEARED: split the two research uses.** The in-mode comprehension/idiom research (raising FM confidence)
  is part of **`kata-comprehend`** (a NEW in-mode step), NOT the escalation-routed no-write `kata-research`
  (which stays for genuine in-loop `research-needed` escalations, used within its real contract).
- **H6 → CLEARED: forward deps labeled, not "reuse."** `install-portability` is Debug Mode's built-first
  predecessor (DG-10b); **`kata-preflight` (D29) is planned-not-built → a forward dependency** Debug Mode needs
  built (DG-1b-edge env provisioning). **DG-10c's convert-to-loop surface is pinned by the install-portability
  DESIGN, not specified here** — Debug Mode's DESIGN references it, doesn't invent it.
- **H7 → CLEARED: characterization-suite generation is NEW** (systematic pin-existing-behavior synthesis across a
  blast-radius), not clean `kata-tdd` (red-green for NEW behavior) / `kata-diagnose` (one test at a seam) reuse.
  Part of the drift-gate/regression machinery; scope NEW.

## v1 scope summary (post-remediation)
**Invest in the semantic core:** full `function_model` oracle (`kata-comprehend`) + full 7-step deviation pipeline.
**Defer to fast-follows:** formal confidence calibration; the surface/AST drift layer. **NEW capabilities to build:**
`kata-comprehend` · the deviation pipeline · characterization-suite generation · the behavioral drift gate. **Forward
deps:** full `install-portability` (built first) · `kata-preflight`. **Reused (verified real):** worktrees,
version-up footprint discipline, `kata-diagnose`, `kata-evaluate`, D98 `kata-review`, run-shape mechanism, gate/
backout/closeout, Snyk. **Status: re-run the fresh-context convergence gate before FREEZE.**
