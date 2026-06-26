---
title: "Debug Mode — FROZEN DESIGN contract"
status: FROZEN (compiled from GRILL-LEDGER round-1..7 + RESEARCH; convergence gate SHIP 2026-06-25)
date: 2026-06-25
spec: debug-mode
compiled-by: kata-design-doc (from GRILL-LEDGER.md + RESEARCH.md)
build-gate: BLOCKED on install-portability (built first, LD-S2) + kata-preflight — build is PARKED
---

# Debug Mode — FROZEN DESIGN

A top-level KataHarness **run-shape `debug`** (peer of version-up, `target.kind==existing`): selected at
bootstrap, pointed at a whole codebase, **self-contained**, it systematically debugs the entire codebase
**in confidence** — bugs out, behavior/structure preserved — via a comprehension-first *function-model* oracle,
a corroboration-gated deviation pipeline, and the loop's gates. The onboarding/conversion killer-app.

> **Provenance:** every LOCKED decision below traces to a resolved grill branch (DG-n / H-n in
> `GRILL-LEDGER.md`) and, where mechanism-bearing, to `RESEARCH.md`. This DESIGN does not introduce new
> decisions; an unresolved branch here = return to the grill.

## 1. Requirements
- **R1** Debug an existing codebase and fix real defects **without changing behavior or structure** (F3).
- **R2** "Debug in confidence" — a dev points it at a repo and gets fixes, **not breakage** (F5).
- **R3** Systematic + thorough — assess all modules, tie-ins, and logic; promote correctness (BRIEF).
- **R4** Self-contained mode; **no debug machinery injected into other modes** (F1/F2, anti-bloat).
- **R5** Reuse built loop pieces maximally; new machinery only where verified-necessary (F4).
- **R6** Be the onboarding on-ramp: first-run → debug-in-confidence → convert repo to the loop + vault (F5).

## 2. Where it lives — components & insertion points (verify-before-reuse pre-flight applied, `protocol/reuse-claims.md`)
> Each reuse claim below was checked against the real surface during the grill's convergence gate; NEW
> capabilities are labeled NEW and scoped, not disguised as reuse (H2 — the gate caught a phantom
> `kata-understand` claim and it was relabeled).

**NEW capabilities to build (in-mode; F2):**
- **`kata-comprehend`** (NEW) — pre-change, whole-repo intent-derivation. Builds a per-module/function
  `function_model` from `kata-graph`/Graphify + docs/comments/types/config + commit-history + caller usage +
  cross-module contract inference. *Distinct from `kata-understand`, which is post-run/map-only and derives no
  intent (verified at `modules/closeout/kata-understand/SKILL.md`).*
- **The 7-step deviation pipeline** (NEW) — `RESEARCH.md §H1`.
- **Characterization-suite generation** (NEW) — systematic pin-existing-behavior synthesis across a blast-radius
  (not `kata-tdd` red-green-for-new-behavior, not `kata-diagnose`'s single-seam test; H7).
- **The behavioral drift gate** (NEW, v1) + in-mode language-specialist **prompt-profiles** (DG-7).
- **The `debug` run-shape wiring** in `kata-bootstrap`/`kata-orchestrate` (parallels version-up; DG-11).

**Reused (verified-real surfaces):** git **worktrees** (`skills/coordinate/kata-worktree`) · **version-up
footprint + baseline-green regression** discipline (`specs/modes-A4-version-up/DESIGN.md`) · **`kata-diagnose`**
root-cause loop · **`kata-evaluate`** + standing **D98 `kata-review`** · **run-shape** mechanism · **closeout +
offered-backout** (`modules/closeout`) · **Snyk** MCP code scan.

**Forward dependencies (must exist before build; H6):** full **`install-portability`** (built FIRST, LD-S2;
the convert-to-loop surface is pinned by *its* DESIGN, referenced not invented here) · **`kata-preflight`**
(D29, planned-not-built) for the runnable-env provisioning of DG-1b-edge.

## 3. LOCKED decisions
*Structure is locked; values marked `[TUNABLE]` may be calibrated without re-freezing.*

- **LD1 — Run-shape `debug`, peer of version-up** (`target.kind==existing`), self-contained, selected at
  bootstrap; `kata-orchestrate` stays config-driven. "Mode" = user-facing word; run-shape = mechanism. (DG-11)
- **LD2 — Comprehension-first oracle.** A bug = a **deviation of code from its derived intended function**.
  `kata-comprehend` builds a `function_model` per module: **executable pre/postcondition assertions + NL
  `intent_summary` + behavioral examples + `derivation_sources` + `confidence`** (full form, H1). Checkable via
  a spec-wrapper; **every FM is a hypothesis to corroborate** (repo-level spec-gen ~20% fidelity — the
  architecture gates on corroboration, not FM accuracy). (DG-1, H1)
- **LD3 — Change scope = bug fixes + security ONLY, strictly behavior-preserving.** No feature/behavior change.
  The run ALSO produces a **recommendations report** for advisable behavior/feature changes and **offers a
  follow-on `version-up`/`sprint`** at closeout (DG-2, DG-2b).
- **LD4 — Discovery = the full 7-step deviation pipeline** (H1/H2): multi-signal candidates (function-model
  **deviation detector** + cross-module tie-in/contract mismatch + Snyk + run-tests/SBFL + static/types/lint +
  `kata-diagnose` + dynamic stack-gated) → semantic LLM comparison → **self-consistency ≥2/3** `[TUNABLE]` →
  **objective-corroboration HARD gate** (≥1 tool/test/type/Snyk co-locates, else LLM-only→human) → **adversarial
  refute-or-promote** (ties to D98) → fix gate. `kata-research` is NOT a discovery source (escalation-only, H5).
- **LD5 — Confidence-tiering (v1 heuristic).** `C = w1·MSAS + w2·(1−self-consistency-entropy) + w3·StructuralPrior`
  `[TUNABLE weights/cutoffs]`; **NOT verbalized confidence**. **Force-LOW** for sparse-signal modules. Routing:
  `C≥τ_H` → auto-fix · `τ_L<C<τ_H` → research ≤2 rounds `[TUNABLE]` → defer · `C≤τ_L` → defer. **Formal isotonic
  calibration on a labeled corpus = fast-follow (deferred).** (DG-1-edge, H3)
- **LD6 — Regression signal = scoped characterization tests** (NEW, H7): per fix's blast-radius, generate tests
  pinning current behavior **except the deviation being fixed**; run before/after; the generated suite is **left
  behind** (conversion value). (DG-1b)
- **LD7 — Comprehension inputs:** graph + docs/comments/types/config + commit-history/blame + **cross-module
  contract inference** + low-confidence flagging; in-mode idiom research lives in `kata-comprehend` (H5). (DG-1c)
- **LD8 — Sweep = whole-repo comprehension; per-fix footprint-scoped changes; graph + churn-risk ordered.**
  Comprehend everything; each fix touches only its blast-radius (version-up footprint discipline); visit modules
  in dependency/PageRank order, weighting churn/hotspots. (DG-5/6)
- **LD9 — Fix application = through the loop, gated; human gate at closeout + one-command backout.** Each fix is
  TDD'd against its characterization tests + passes `kata-evaluate` + D98 `kata-review`; applied in worktrees.
  Objective defects (test/type/Snyk) fixed regardless of intent-confidence; **can't-fix-without-drift → defer to
  recommendations** (DG-8, DG-12, DG-1-edge).
- **LD10 — In-mode specialists = prompt-profiles by detected stack** (per major language + a config/context
  specialist), layered on `kata-tdd`/`kata-diagnose`, inside the mode; no new Python (DG-7).
- **LD11 — Pass model is a bootstrap config choice:** (1) one graph-ordered resumable pass | (2) loop-until-dry
  (DG-3). **Execution locus is a bootstrap config choice:** in-place worktrees (DEFAULT) | import-a-copy (opt-in
  for read-only/untrusted/hard-fork; needs its own pre-flight, falls back to snapshot/report-only) (DG-10c-import).
- **LD12 — Closeout = the confidence report:** per-module **confidence map** (assessed/low-confidence/skipped) ·
  each **deviation→fix→pinning test** · **regression+security proof** (suite green + new tests + mutation +
  Snyk before/after) · the **recommendations list** + offered version-up/sprint handoff (DG-9, DG-2b).
- **LD13 — Onboarding (v1): dedicated first-run path** — fresh install → offer Debug Mode → on success offer
  convert-to-loop + vault setup. **Depends on full `install-portability` built first** (LD-S2); convert-to-loop
  writes kata.config + `.planning/` + commits the characterization suite + vault binding (DG-10, DG-10b/c, H6).

## 4. Integrity / edge cases (resolved)
- **Low-confidence oracle (DG-1-edge):** never auto-fix an intent-deviation against a low-confidence FM →
  research(≤2) → defer. Objective defects bypass this (they don't depend on the oracle).
- **Untested / non-runnable target (DG-1b-edge):** `kata-preflight` establishes the runnable env; if it can't,
  that area drops to **behavior-snapshot diff or report-only** (honest, no false confidence).
- **Can't-fix-without-drift (DG-12):** defer to recommendations; preserves the no-drift guarantee.
- **False-positive control:** the objective-corroboration HARD gate + self-consistency + adversarial
  refute-or-promote (LD4) keep LLM-only findings out of auto-fix.

## 5. Backward-compatibility contract  ⚠ includes the v1 limitation (FREEZE note, H4)
- **The behavior-preservation guarantee (v1) = the BEHAVIORAL drift gate:** every baseline-GREEN test stays
  GREEN; characterization snapshots byte-identical (nondeterminism scrubbed) EXCEPT an **Allowed Exception List**
  (the nominated buggy test[s] that may go RED→GREEN). Any previously-green test → RED = **BLOCK**. (LD6/H4)
- **⚠ v1 LIMITATION (must be surfaced to the user):** the **surface/structural invariance layer** (public-API
  diff = ∅ + AST-edit-script = body-updates-only) is a **fast-follow, NOT in v1**. Therefore v1 guards
  *behavioral* drift strongly but **structural/public-surface drift only loosely**. The "structure preserved"
  promise (F3) is **behaviorally** enforced in v1; full structural enforcement arrives with the fast-follow.
- Single-host / existing modes are unaffected — `debug` is an additive run-shape; absent selection, nothing changes.

## 6. Acceptance criteria (default-FAIL, runnable) — for the eventual build
- `kata-comprehend` emits a schema-valid `function_model` per module; spec-wrapper executes the pre/post.
- The 7-step pipeline: a finding reaches "auto-fix eligible" ONLY with ≥1 objective corroborator + ≥2/3
  self-consistency + surviving adversarial refute (verifiable on a seeded fixture with a known deviation).
- The behavioral drift gate BLOCKS on any baseline-green→RED transition outside the Allowed Exception List
  (verifiable: inject an unrelated regression → gate blocks).
- Each fix ships with a characterization test that pins it (deviation→fix→test traceable in the closeout report).
- Full loop gates green: `kata-evaluate` PASS + D98 `kata-review` + Snyk on modified code; mutation non-vacuous.
- Confidence report renders all four LD12 elements incl. the honest per-module confidence map.

## 7. Test seams / testability
- **Function-model**: the spec-wrapper (inject pre/post, run) is the seam — testable on fixtures with known intent.
- **Deviation pipeline**: each gate (self-consistency, objective-corroboration, refute) is independently testable
  on seeded deviations (true-positive fires; false-positive is filtered at the corroboration gate).
- **Drift gate**: testable by injecting an unrelated regression (must BLOCK) vs. the nominated fix (must PASS).
- **Run-shape wiring**: `kata.config` round-trip + bootstrap selection, mirroring version-up's tests.

## Build sequencing (PARKED)
**Build is BLOCKED** until **`install-portability` is built first** (LD-S2/DG-10b) and **`kata-preflight`** exists.
When unblocked: grill is done → this DESIGN → `kata-plan` partitions the NEW capabilities (`kata-comprehend` ·
deviation pipeline · characterization-gen · behavioral drift gate · run-shape wiring · onboarding path) into
disjoint slices → build through the loop (the recipe). Fast-follows after v1: confidence calibration (LD5) ·
the surface/AST structural drift layer (LD-H4).
