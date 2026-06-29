---
title: kata-loop-benchmark — research + design approach (pre-grill)
status: GRILL-RESOLVED (operator concurred 2026-06-28 — ready for planning subagent to author frozen DESIGN/PLAN)
date: 2026-06-28
feeds: the kata-loop-benchmark grill (D99 keystone, orientation §4)
sources: deep-research wf_7f373992-209 + SWE-bench code-level review (ac0f77d) + DECISIONS D99/D13/D14/D57/D108/D118
related: "[[project-kataharness]]"
---

# kata-loop-benchmark — Design Approach (research-grounded)

> **Reading note.** This is the RESEARCH/approach doc that feeds the benchmark grill — NOT a frozen
> PLAN. Sections marked ⟪FORK⟫ are open decisions for the operator grill. The frozen DESIGN/PLAN is
> authored by a planning subagent AFTER the grill (per the recipe).

## 0. The one-line thesis
Adopt SWE-bench's **skeleton** (frozen task-as-data · hermetic isolation · hidden dual-gate grader)
but reject its **fatal flaw** (correctness-only, no efficiency axis). Anchor every benchmark on an
**immutable reference (the control)** that is **cloned into a tagged working copy per run**; measure
each run on **two axes — outcome quality × token/cost efficiency** with a **dynamically-applicable
metric** whose only *rigid* element is the **control** (identical start + identical inputs across
arms). Efficiency is scored **only among runs that clear the default-FAIL floor**, so a cheap wrong
answer can never win. Ship as an **off-by-default `benchmark` module** behind a hidden power-user
flag, emit a **second two-tier report**, and feed its recommendations into **human-gated optimization
proposals** via the existing `kata-improve` mechanism.

---

## 1. Research foundation (what's established vs thin)

**Machine-verified high-confidence (SWE-bench mechanics + pitfalls — topics 1–2):**

| Copy from SWE-bench | Source |
|---|---|
| Task-as-data, frozen: repo + `base_commit` + `environment_setup_commit` + explicit test-ID lists; specs are diff-able data, not code | swebench.com docs |
| Dual-gate resolution: `FAIL_TO_PASS` (objective tests flip red→green) **AND** `PASS_TO_PASS` (existing suite stays green); **both** required | OpenAI Verified |
| Hidden grader injected at eval via **workspace reset** — agent physically can't weaken/delete the grading tests | SWE-bench harness |
| Deterministic grading + a small human-verified "golden" subset as the trusted headline | OpenAI Verified |

| Avoid (documented failure modes) | Source |
|---|---|
| **Correctness-only metric** — SWE-bench has zero cost/token/time dimension (the gap we fill) | SWE-bench harness review |
| **Weak tests inflate scores** — ~31% of "passed" patches passed on inadequate tests; filtering cut resolution ~3× (12.5→4.0%) | arXiv:2410.06992 (SWE-Bench+) |
| **Contamination kills frozen benchmarks** — OpenAI *stopped* evaluating SWE-bench Verified (Feb 2026); 59.4% of hard tasks had material test/spec flaws; all frontier models reproduced gold patches verbatim | openai.com/why-we-no-longer-evaluate |
| **Ambiguous task statements** — #1 reason Verified was needed (38% underspecified) | OpenAI Verified |
| **Per-language log-regex parser sprawl** — maintenance debt; prefer a structured result protocol (JSON/junit-xml) | SWE-bench harness review |

> **KataHarness edge:** the **mutation-proof** requirement directly attacks the weak-test failure mode
> SWE-bench couldn't — a genuine structural advantage.

**Medium confidence (cost-efficiency methodology):** Princeton *"AI Agents That Matter"*
(arXiv:2407.01502) — accuracy-only agent leaderboards are misleading; evaluate **jointly on a
cost–accuracy Pareto frontier** and be **explicit about weights** rather than hiding them in one
scalar. The load-bearing source for the two-axis metric.

**Lower confidence (specific figures didn't survive adversarial verification — rate-limited; principles are standard):**
- Small-n rigor: pass@1 = *capability*, pass^k (all-k-succeed) = *reliability*; they diverge; single
  runs carry real variance ⇒ **n=1 is directional only**, support k-repeats. (arXiv refs unverified.)
- Self-improvement: the credible pattern is *propose → implement → empirically evaluate → keep-if-better*
  (Darwin Gödel Machine, arXiv:2505.22954). KataHarness's contribution = a **human gate** on "keep"
  (= the C/B invariant).

---

## 2. THE CONTROL MECHANISM (operator-specified — the spine of the design)

The benchmark is an **experimental control design**, not a rigid scoring rubric. (Operator correction,
2026-06-28: *"the rigidity shouldn't be enforced on the standards, rather on the control that models
real data used and compared between runs as an actual control comparison."*)

### 2.1 Immutable reference = the control
- A benchmark anchors on an **immutable reference**: a **reference code repo** (coding) or a
  **reference research project** (research). **The original is never mutated** — it is the control.
- Each run **clones/copies** the reference into a **spawned working copy** tagged
  `<name>-katabenchmark<N>` (N = run index: `…-katabenchmark1`, `…-katabenchmark2`, …). The agent acts
  **only on the copy**.
- Run **N times** → N standing result-sets, each frozen in its own copy. Compared **against the
  control's benchmark data** (embedded criteria) AND **against each other** (run-to-run).
- **Rigidity = the control, not the metric.** Byte-identical start + identical system/input/prompt
  across arms ⇒ any outcome delta is attributable to the variable under test (mode/config/model/
  run-variance). This is exactly SWE-bench's clone-from-`base_commit`-act-on-copy pattern, generalized
  and made the experimental control.

### 2.2 Two flavors
- **Coding benchmark.** Reference repo carries embedded **benchmark data** (the dual-gate
  `FAIL_TO_PASS`/`PASS_TO_PASS` tests + mutation criteria). Each clone is graded objectively;
  clones are ranked by the two-axis metric (§3). The control repo stays pristine.
- **Research benchmark.** Reference is a research project (system + input + prompt). Each run spawns a
  copy `<name>-katabenchmarkN` and produces a research artifact; copies are compared (⟪FORK R3⟫ judge
  vs human). Same name + tag convention.

### 2.3 Promotion (control stays immutable)
- A spawned result the user likes can be **promoted to become the new master** of their codebase
  (human-gated, diff shown first — reuses the WS-4 offered-backout/promotion plumbing shape).
- The **control reference is never promoted into / overwritten** — promotion moves a *copy's* result
  to a *master* (a different repo than the control).
- ⟪FORK R2⟫ Does promotion apply only when benchmarking a clone of the user's **real** repo, or to any
  spawned copy including fixture-derived ones?

### 2.4 "benchmark data" = the comparison anchor
- **Both:** (i) **embedded criteria** in the reference (hidden tests / expected outcomes) define
  pass/quality; (ii) **accumulated historical scorecards** across prior runs give the "is this optimal
  vs prior runs" distribution. *(R5 RESOLVED: both.)*

### 2.5 Replay-by-definition — the Benchmark Definition artifact (operator add, 2026-06-28)
Every benchmark emits a durable, **content-pinned Benchmark Definition** (`benchmark.def.json` — the
benchmark's analog of `kata.config`/`INTENT.md`) that **fully re-runs it by definition**. Replay =
`kata benchmark --from <benchmark_id | benchmark.def.json>`.
- **Fields:** `benchmark_id` · `created` · `parent_benchmark_id` (lineage when repeated/derived from a
  prior benchmark) · `control {kind: code|research, ref, content_hash|commit}` · `criteria_ref` ·
  `arms[] {label, mode, modules, effort, model, routing}` · `metric {profile, weights, floor_gate}` ·
  `k_repeats` · `inputs {system, prompt, input_refs}` · `naming "<name>-katabenchmark{N}"` ·
  `provenance {tool_version, skill_versions}`.
- The control is pinned by **content-hash**, so a repeat re-clones the **byte-identical** reference
  (drift-detected and flagged if the ref dir was later touched). This is what makes "repeat by
  definition from a previous benchmark" faithful, not approximate.
- A repeat **after a harness change** keeps the definition identical but records a different
  `provenance` → the report flags *"same definition, newer harness"* so the comparison is honestly a
  **harness-delta measurement** — which IS the C-on/C-off learning-lift measurement (D99).
- Every run links back to its definition → re-runs accumulate into the **historical-scorecard
  distribution** (§2.4 / R5). A definition is itself promotable/forkable (`parent_benchmark_id`), so a
  tuned benchmark becomes a reusable standard.

### 2.6 Point-and-repeat + delta mode (operator refinement, 2026-06-28)
The definition is a **durable, addressable artifact** — committed/persistent (e.g.
`benchmarks/<id>/benchmark.def.json` or a benchmark registry), **NOT** trapped in disposable `.kata/`.
This is the durable/disposable split (D81): the **definition is durable + pointable**; the spawned
working copies + raw scorecards are disposable run artifacts.
- **`repeat_from` config pointer:** the benchmark config can name an existing definition by **location**
  (path / registry id / URL) and re-execute an **exact mirror** (content-pinned control + pinned
  inputs/arms/metric). You don't re-specify — you point at a prior benchmark wherever it lives.
- **Delta mode (first-class report):** the operator workflow is *run → adjust the loop → come back →
  re-execute the mirror → read the delta.* A `repeat_from` re-run produces a **delta report** that
  diffs the new scorecard against the referenced prior run(s) and **leads with the improvement/
  regression delta** (Δquality, Δcost, ΔPareto-position), `provenance`-stamped so the delta is honestly
  attributed to the harness change, not noise. This IS the C-on/C-off learning-lift measurement (D99),
  surfaced as the headline.
- **Consequence for sequencing:** because point-and-repeat is fixture-agnostic, the **control fixture
  can be supplied later** (or a definition can point at one living elsewhere) — the design freezes now;
  the fixture plugs into the `control` slot.

---

## 3. The two-axis scorecard + the (now control-anchored) metric

**Axis Q — Outcome quality** (gated, ∈ [0,1]):
- **Floor (necessary):** the `kata-evaluate` default-FAIL conformance gate (builds/tests/scan green).
  Floor fails ⇒ **Q = 0** regardless of cost.
- **Dual-gate (SWE-bench-style):** the reference declares `FAIL_TO_PASS` (objective tests) +
  `PASS_TO_PASS` (regression guard). Both green = full credit; partial F2P = partial credit (secondary).
- **Mutation survival** (reuse `mutation_run`/`mutation.json`): the anti-weak-test multiplier.

**Axis C — Efficiency** (normalized cost): tokens in/out · **$ cost** (per-model rate table —
multi-model arms price differently) · wall-clock · tool-call count · # escalations · # fix-loop
iterations (thrash) · # subagent dispatches.

**The metric — dynamically applicable, control-anchored (NOT a rigid standard):**
- The **fixed element is the control** (§2): identical start + inputs across arms. The metric is
  **comparison-relative** — each run scored vs the control's criteria and vs sibling runs.
- **Floor-gate** keeps cost from dominating: efficiency is scored **only among floor-passers**, so a
  cheap-wrong answer scores Q=0 and never wins. *This is the "without one dominating" mechanism.*
- **Present the Pareto point (Q, C)** (per "AI Agents That Matter") AND a convenience scalar (e.g.
  `Composite = Q / (1 + λ·C_norm)` among passers). ⟪FORK R-A⟫ Pareto-only vs Pareto+scalar.
- **Weights flex by profile** (`benchmark.profile: balanced | cost-lean | quality-strict`) — the
  *dynamic* half; the *control* is the rigid half.

> ⚠️ **Instrumentation prerequisite — CONFIRMED build dep (R-cost RESOLVED, verified 2026-06-28):** the
> harness does **NOT** persist per-arm token/cost today. `kata_dispatch.build_result` captures
> `taskId/role/platform/model/status/payload/raw` only; `gate_emit` (RESULT.json) and `run_result` carry
> no usage. Axis C therefore requires a **net-new metering hook**: capture CLI-emitted usage for routed
> arms + host metering for the main loop → persist to a new `.kata/usage.json` (+ wall-clock, trivially
> available). Well-scoped, not a blocker, but it is a real build task the efficiency axis depends on.

---

## 4. Activation — the hidden power-user flag
Off-by-default **`benchmark` module** (same mechanism as `kata/module/slop`, silent no-op unless
present in the run's modules):
- Triggered by `--benchmark` / `KATA_BENCHMARK=1` / a hand-added `benchmark:` block in `kata.config`.
- **Not** surfaced in the `kata-bootstrap` "how careful" dial; **not** listed in the standard advanced
  drawer — discoverable only if you know it exists. Bootstrap stays clean for normal users.
- Absent ⇒ zero overhead, zero behavior change (BC).

---

## 5. The benchmark report (second report, same two-tier format)
Reuse the **two-tier closeout** (`kata-report` template + `BRAND.md`): concise CLI/MD summary linking a
durable on-brand HTML report. Add benchmark-specific tiles: scorecard (Q, C, composite) · **Pareto
position** vs control/baseline · **per-arm comparison table** (concurrent/mode runs) · **optimization
recommendations** as callout tiles. New `kata-benchmark-report` skill (evaluate cat) authors it
(mirrors `kata-debrief`); pure deterministic engine `tools/benchmark.py` (the D99 smallest-v1 scorer
over `.kata/{RESULT,footprint,mutation}.json` + metadata → `.kata/benchmark/<run-id>.json`). **Reports
never gate.** **Delta mode (§2.6):** when the run was launched via `repeat_from`, the report adds a
**delta header** (Δquality · Δcost · ΔPareto-position vs the referenced prior run) and a
same-definition/different-provenance banner.

---

## 6. The two operator use-cases → run-shapes
- **(a) Concurrent same-task loops** → ride the **`bakeoff` module** (best-of-N, AgentHub/worktrees):
  N arms · the immutable control cloned per arm · **fresh context per arm · constant Claude model ·
  isolated worktrees** (D13/D14 fairness, all exist). Scorer ranks arms by the two-axis metric. This is
  an *outcome* comparison of modes/routing/config — the **legal axis** (NOT the retired grill-vs-baseline
  RCT, D70/L11).
- **(b) Dev mode-comparison over a standard fixture** → repeated **paired runs** (D57 small-greenfield
  shape) of mode X vs mode Y against the immutable reference. Support **k-repeats per arm** → report
  mean ± spread, label **n explicitly**, bake in **"n=1 = directional, not proven"** (extends the
  *exercised ≠ proven* convention). ⟪FORK R6⟫ k default = 1 (cheap) vs 3 (variance).

---

## 7. Fairness + anti-contamination — KataHarness-specific
The contamination that killed SWE-bench Verified is **largely neutralized for the primary use-case**:
comparing **configs of the same harness on the same control with the model held constant** (D13/D14)
means training-leakage hits every arm **equally** and **cancels in the relative ranking**. That's a
real edge.
- It does NOT cancel for the **absolute** "was this optimal" judgment → answer with the **control's
  embedded criteria + historical scorecards** (§2.4) + **mutation-proof + hidden-grader** to kill
  weak-test inflation.

---

## 8. The human-gated optimization feedback (C-arc tie-in)
"Optimize the KataHarness model itself" = optimize the **harness's own config/skills/prompts/routing**
(⟪FORK R-scope⟫ confirm: not a trained ML model — KataHarness has none). At a benchmarked run's close:
- Report recommendations feed the **`kata-improve` T2 proposal mechanism** (D118): a sub-optimal
  pattern (*"Standard spent 3× tokens for equal Q vs Essential"*; *"validator→Codex added latency, no
  Q gain"*) **auto-drafts `PROPOSAL-<…>.md`** → freeze-gate `kata-review` → **human merge**. **Never
  auto-applies** (C/B invariant; propose-never-apply) — the human gate "at the conclusion of the
  benchmarked run" you specified.
- Human-merged proposals edit `kata.config` defaults / mode definitions / routing tables / skill
  prompts. The DGM loop *with* KataHarness's mandatory human gate.
- **This IS the C-arc keystone (D99 tumbler #4):** the same machinery measures **C-on vs C-off learning
  lift**. Benchmark and learning-loop optimizer are one mechanism viewed twice.

---

## 9. Build-vs-adopt — lean native (confirms operator pre-decision)
Adopt SWE-bench **patterns** (spec-as-data · dual-gate · hidden-grader-via-reset · hermetic-via-worktree
· structured result protocol), **not** its Docker/log-regex implementation. Fixtures = small
one-shottable greenfield projects (D57); reuse worktrees + existing `RESULT/footprint/mutation`
artifacts; fixtures emit **structured test results (JSON/junit-xml), not log regex**.

---

## 10. Maps onto existing machinery

| Need | Existing | New |
|---|---|---|
| Hidden activation | module-bundle (`kata/module/slop`) | `benchmark` module + flag |
| Immutable control + clone-per-run | worktree isolation; bakeoff | reference-clone + `*-katabenchmarkN` tagging |
| Quality floor | `kata-evaluate` default-FAIL | dual-gate F2P/P2P spec fields |
| Anti-weak-test | `mutation_run` / `mutation.json` | reuse as multiplier |
| Concurrent arms | `bakeoff` + worktrees + multi-model (LIVE) | scorer ranks arms |
| Promotion | WS-4 offered-backout/diff-gate shape | promote-copy-to-master action |
| Report | two-tier closeout + `BRAND.md` + `kata-report` | `kata-benchmark-report` + `tools/benchmark.py` |
| Human-gated optimization | `kata-improve` T2 propose-never-apply | benchmark→proposal hook |
| Fairness | D13/D14 frozen-task/fresh-context/constant-model | k-repeat variance reporting |
| **Cost metering** | **⚠️ verify persisted** | **likely a metering hook (build dep)** |

---

## 11. GRILL — RESOLVED (operator concurred 2026-06-28; ready to freeze)
- **R1 control semantics — RESOLVED:** immutable reference = frozen *starting state + embedded criteria*;
  scoring = run-vs-criteria + run-vs-run; gold/reference solution optional reference material only.
- **R2 promotion scope — RESOLVED (a):** promotion applies to runs against the user's **real** repo
  (pick best arm → new master); the synthetic fixture is a pure control, never promoted. Control
  reference never overwritten either way.
- **R3 research-mode scoring — RESOLVED (ii):** deterministic-where-possible + a fresh-context judge for
  the subjective remainder; judge variance flagged honestly; human makes the final call.
- **R4 spawned-copy location + retention — RESOLVED:** **sibling directories** (`<name>-katabenchmark1`
  beside `<name>`); **persist until explicitly pruned or promoted**; a `prune` convenience.
- **R5 benchmark-data anchor — RESOLVED:** **both** embedded criteria + historical-scorecard distribution.
- **R-A composite shape — RESOLVED:** **both** Pareto point (Q, C) + a convenience scalar, both behind
  the default-FAIL floor-gate.
- **R6 k-repeats default — RESOLVED:** default **1** (honest "n=1 directional"), configurable to k.
- **R-cost cost-metering — RESOLVED (verified):** NOT persisted today → a metering hook is a confirmed
  net-new build dep (§3 note).
- **R-scope "model optimization" surfaces — RESOLVED:** start with **`kata.config` defaults + routing
  tables** (low blast-radius, easy to diff/gate); skill-prompt edits gated to a later tier. Confirmed:
  "the KataHarness model" = the harness's own config/skills, **NOT** a trained ML model.
- **R-judge — RESOLVED:** Q is **purely test/mutation-mechanical for v1**; a judged code-quality
  dimension is a v2 opt-in.
- **NEW (operator add) — replay-by-definition:** the Benchmark Definition artifact (§2.5) makes a
  benchmark re-runnable by definition from a prior one; content-pinned control; provenance-stamped for
  honest cross-version comparison.

## 12. Next step
Grill the §11 forks → planning subagent writes the frozen `DESIGN.md` + `PLAN.md` → freeze-gate
`kata-review` → orchestrated build (recipe). Reference fixture candidate: the repo the operator intends
to provide (orientation §5) may be the standardized control for use-case (b).
