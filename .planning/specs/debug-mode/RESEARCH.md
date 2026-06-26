---
title: "Debug Mode — research pass (resolves the convergence-gate HOLD H1–H4) + 3 repo assessments"
status: RESEARCH (grounds the H1–H4 re-grill; not frozen)
date: 2026-06-25
spec: debug-mode
method: 4 parallel research threads + 3 repo assessments (operator-requested)
---

# Debug Mode — RESEARCH (for the H1–H4 re-grill)

The convergence gate HELD on the semantic core (H1 oracle, H2 phantom reuse, H3 confidence-tier, H4 drift-gate).
This pass surveyed how real systems do each, to ground the re-grill in concrete options. Below: a recommended
resolution per HOLD item + the 3 repo assessments the operator asked for.

## H1 — the function-model oracle: representation + deviation detection
**Representation (recommended): an executable+NL `function_model.json` per module/function** — the
literature (CodeSpecBench, SpecRover/ICSE'25, VeriAct) converges on **LLM-generated executable pre/postcondition
functions + a natural-language `intent_summary` anchor + behavioral examples**, NOT formal specs (JML/refinement
types are language-locked + too costly) and NOT NL-only (not checkable). Fields: `intent_summary`,
`signature`(+param constraints), `preconditions`/`postconditions` (runnable assertion fns in the target
language), `behavioral_examples`, `derivation_sources` (docstring · commit msgs · caller usage · types · tests),
`confidence`, `derivation_method`. Derived from graph+docs+types+commit-history+callers; **checkable** via a
spec-wrapper harness (inject pre/post, run) — no SMT/provers needed. *Treat every FM as a HYPOTHESIS* —
repo-level spec-gen fidelity is ~20% even in the best models (CodeSpecBench), so it MUST be corroborated.

**Deviation detection (recommended 7-step pipeline, low false-positive by construction):**
1. **Extract** the FM per module (cached). 2. **Multi-signal candidate gen** (parallel, cheap): objective signals
(static analysis: Infer/CodeQL/Semgrep/type-checkers + test runner via SBFL suspicion scores) · embedding
peer-anomaly ("unlike its peers") · graph-localization (LocAgent-style traversal on call/dep edges).
3. **Semantic comparison** (primary LLM signal): reasoning model walks code against the FM, emits structured
deviation {location, type, evidence}. 4. **Self-consistency**: run ×3 shuffled/rephrased, advance only if **≥2/3
agree** on location+type (kills position/verbosity bias). 5. **Objective-corroboration HARD gate**: a finding is
"confirmed-candidate" only if ≥1 objective signal co-locates (analyzer/test-fail/type-error/Snyk); else
"LLM-only → human review, never auto-fix" (the IRIS pattern). 6. **Adversarial refute-or-promote** (ties to D98
`kata-review`): a fresh instance argues the code is CORRECT; can't rebut → promote; plausible rebuttal →
"contested → human". (Refutation killed ~79–83% of candidates in the lit while keeping real bugs.) 7. **Fix gate**:
only confirmed-deviations → fix; re-run 2–6 on the patch; Snyk on modified code. Sources: SpecRover, Agentless,
AutoCodeRover (SBFL), LocAgent, IRIS, MCTS-Judge, Refute-or-Promote, CodeSpecBench.

## H2 — `kata-understand` is phantom reuse → the function-model builder is a NEW capability
Confirmed by both the convergence gate AND the research: `kata-understand` is a post-run, map-only,
footprint∩graph tool that *derives no intent*. The FM-builder above is a **NEW in-mode capability** (working name
**`kata-comprehend`** — derives intended function pre-change, whole-repo, confidence-tiered). Scope it NEW with
its own ownership/acceptance/cost; the F2 anti-bloat story stands (it's in-mode), but it is NOT free reuse.

## H3 — confidence-tiering: a real signal, not a magic constant
**Measure (recommended): a composite, NOT verbalized confidence** (verbalized ≈ random, AUROC ~0.62, RLHF
overconfidence). Use **`C = w1·MSAS + w2·(1−entropy) + w3·StructuralPrior`**:
- **MSAS (Multi-Source Agreement Score)** — independent intent derivations from naming · types · docstring ·
  caller-usage · commit-history · test-assertions; fraction of source-pairs agreeing on core behavior. *(Best
  single discriminator; multi-format agreement hits AUROC ~0.81 vs 0.62 verbalized.)*
- **Cross-sample self-consistency** — k≈5 intent inferences, cluster by **behavioral semantics** (symbolic, not
  embedding — embedding clustering is non-significant for code), low entropy = high confidence.
- **StructuralPrior** — doc/test/type presence (cheap prior).
**Calibrate** C→P(correct) via **isotonic regression on a ~200–500 labeled corpus**; set the HIGH cutoff τ_H by
**constrained optimization** (HIGH-tier precision ≥90%), not intuition; optional **conformal prediction** for a
distribution-free coverage guarantee. **Route:** C≥τ_H → auto-fix · τ_L<C<τ_H → research (≤2 rounds, re-score) →
defer if still low · C≤τ_L → defer. **Force-LOW** for sparse-signal modules (no docs/tests/opaque names).
Caveats: consensus-trap (require ≥1 structurally-independent anchor), per-language calibration (distribution
shift), recalibrate on model change. Sources: UCCI, ReDAct, ConU, MFA, abstention survey.

## H4 — the no-structural-drift gate: a concrete two-layer, language-agnostic gate
**Layer 1 — Behavioral**: at mode entry capture a baseline (full suite + golden-master/characterization snapshots
for untested paths). Pass = every baseline-GREEN test stays GREEN + snapshots byte-identical (scrub
nondeterminism), EXCEPT an **Allowed Exception List** (the nominated buggy test(s) that may go RED→GREEN). Any
previously-green test → RED = BLOCK. **Layer 2 — Surface+Structural**: (a) **public-API diff** normalized to
`{added,removed,changed}` which must all be **empty** (per-language: TS api-extractor · Java japicmp · Rust
cargo-semver-checks/public-api · Go apidiff · Python griffe; **fallback = Semgrep+tree-sitter symbol extraction**);
(b) **AST edit-script** (GumTree/difftastic) classified — **only `UPDATE body-of-existing-decl` allowed**;
INSERT/DELETE/MOVE/signature-change = BLOCK. **Language-agnostic** via a plugin interface
(`captureBaseline/diffSurface`) + a Semgrep/tree-sitter fallback (30+ langs); the orchestrator only sees
test-states + normalized surface-diffs + AST edit-classes. This **answers the BRIEF's named load-bearing gap**:
the fix is allowed only as an internal body edit to an already-declared entity, behavior change only on the
exception list, nothing else moves. Sources: Feathers characterization/ApprovalTests, api-extractor/japicmp/
cargo-semver-checks/griffe, GumTree/difftastic, SafeRefactor/differential testing, Semgrep.

---

# Repo assessments (operator-requested) — all three = BORROW-PATTERN, none ADOPT

> **Key framing: two different debugging paradigms.** All three repos do **runtime interactive debugging** (DAP:
> breakpoints/stepping, tool-specific). Debug Mode's CORE is **static, whole-codebase, intent-deviation** debugging
> (the research above). Runtime debugging is at most a **future in-mode dynamic-analysis discovery source (DG-4b)**
> or a separate interactive-debug adapter — NOT the core. So the takeaways are patterns, not architectures.

## AlmogBaku/debug-skill — BORROW-PATTERN (the most valuable of the three)
A Claude skill (`skills/debugging-code/SKILL.md`) + a Go `dap` CLI (DAP wrapper: Python/Go/Node/Rust/C++). 291★,
MIT, active. Runtime interactive debugger — tool-locked to `dap`, so not adoptable. **3 high-value takeaways:**
1. **Invariant breakpoints → intent assertions** — "conditional breakpoint as a runtime assertion / tripwire for a
   condition that should never be true." **This maps DIRECTLY onto H1**: express a module's intended function as
   checkable boundary invariants (= our pre/postconditions), giving the adversarial reviewer a concrete claim to
   attack. The single best idea across all three repos.
2. **Hypothesis-first forcing function** — "I believe the bug is in X because Y (falsifiable)" as a *required*
   precondition before any diagnostic step → an auditable claim for the gate.
3. **Two-strikes rule** — two failed hypotheses at one site ⇒ the mental model is wrong, rebuild it. Maps to a
   Debug-Mode thrash trigger: 2 failed fixes at a module → force an FM re-derivation rather than more fix attempts.
`source: https://github.com/AlmogBaku/debug-skill` if any text is adapted.

## matt1398/claude-devtools — BORROW-PATTERN (Claude-adapter patterns)
An Electron GUI that reconstructs Claude Code sessions from `~/.claude` JSONL. 3.6k★, MIT, active. The app is
non-transferable (tool-agnostic concern) but its `.claude/` internals give **3 adapter-level patterns**:
1. **`SessionStart`/`compact` hook** re-injecting domain context after compaction → directly fills a KataHarness
   gap (re-anchor loop phase/board/worktree after context compaction; for the Claude adapter).
2. **`PreToolUse` jq-pipe + `exit 2`** as a concrete reference for a hook-enforced gate.
3. **`NotificationTrigger` schema** (`error_status|content_match|token_threshold` × content-type) — a clean,
   YAML-portable model for declaring **FAIL conditions** in skill frontmatter; "interruption" as a first-class
   event type is a vocab gap worth adopting on the board.

## withpointbreak/pointbreak-claude — BORROW-PATTERN (weak; low maturity)
A Claude Code plugin wrapping a **proprietary** Pointbreak MCP/DAP server (IDE-locked). 2★, 1-day history, MIT.
Closed-source dep = not adoptable, contradicts tool-agnosticism. **Takeaways (mostly things KataHarness already
half-does):** the **`## Contract` (Inputs/Outputs + argument-hint)** block for command/skill files; the
**`references/` lazy-load guard** pattern (KataHarness already uses `references/`); and a **DAP-via-MCP blueprint**
useful only if a future interactive-debug adapter is built.

**Net:** none change Debug Mode's architecture. The one idea that feeds the core design is debug-skill's
**invariant-as-intent-assertion** (reinforces H1). The rest are Claude-adapter / future-runtime-debug patterns →
park in BACKLOG, not the Debug Mode core.
