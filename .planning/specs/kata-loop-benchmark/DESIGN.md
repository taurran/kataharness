---
title: kata-loop-benchmark — frozen DESIGN contract
status: FROZEN (authored from RESEARCH.md GRILL-RESOLVED 2026-06-28; ready for freeze-gate kata-review)
date: 2026-06-28
spine: ".planning/specs/kata-loop-benchmark/RESEARCH.md"
feeds: ".planning/specs/kata-loop-benchmark/PLAN.md"
related: "[[project-kataharness]]"
locks: D99 keystone · D13/D14 fairness · D118 T2 propose-never-apply · D81 durable/disposable · D57 small-greenfield
---

# kata-loop-benchmark — DESIGN (frozen)

> This is the **frozen design contract** for the benchmark feature. It is faithful to `RESEARCH.md`
> (the spine) and does **not** re-open any §11 RESOLVED fork. Reuse claims are verified per
> `protocol/reuse-claims.md` — each cites a concrete `file:anchor`, or is labeled **NEW** and scoped.
> Where RESEARCH's reuse assumption did not survive verification, the design says so and re-scopes
> (the one material case: concurrent **bakeoff** arms — see §6 and §11).

## 0. One-line contract
Anchor every benchmark on an **immutable reference (the control)**, clone it into a tagged sibling
working copy per run (`<name>-katabenchmark<N>`), and score each clone on **two axes — outcome quality
(Q) × efficiency (C)** with efficiency measured **only among runs that clear the default-FAIL floor**.
Ship as an **off-by-default `benchmark` module** behind a hidden flag; emit a **second two-tier report**
that **never gates**; feed recommendations into **human-gated** `kata-improve` proposals
(propose-never-apply). The **rigid element is the control, not the metric** (§2).

---

## 1. Scope — what v1 IS and what it DEFERS (honest phasing)

**v1 (this DESIGN + the PLAN's vertical slice).** The deterministic scorer (D99 smallest-v1) enriched
with exactly the machinery that makes one benchmarked run *real and replayable*:
- The **control mechanism** — immutable reference → clone-per-run sibling copy → content-hash pin (§2).
- The **two-axis scorecard** + floor-gated composite (Pareto point + convenience scalar), Q **purely
  test/mutation-mechanical** (R-judge RESOLVED) (§3).
- The **Benchmark Definition** artifact (`benchmark.def.json`) + `repeat_from` + **delta mode** (§4).
- **Hidden activation** — the off-by-default `benchmark` module + flag; **not** in bootstrap (§5).
- The **net-new metering hook** → `.kata/usage.json` (Axis C's confirmed prerequisite) (§3.3).
- The **two-tier benchmark report** mirroring `kata-report`/`kata-debrief` (§7).
- **Use-case (b)** — sequential / paired **mode-comparison** runs over a fixture, k-repeats, n=1
  directional honesty (§6b).

**DEFERRED to a later phase (named, not silently dropped):**
- **D1 — Concurrent bakeoff arms (use-case a).** Rides the `bakeoff` module, whose **execution is Spec B
  ("configurable now, executable later")** — *not built* (verified §11). v1 ships the scorer that can
  rank arms; the concurrent-arm *driver* lands when Spec B does.
- **D2 — Research-mode judge (R3).** Q is mechanical for v1; the fresh-context judge for the subjective
  remainder is a **v2 opt-in** (R-judge RESOLVED).
- **D3 — The optimization-proposal hook.** The benchmark→`kata-improve` T2 proposal sub-mode (§8) is its
  own coherent slice; it needs the v1 scorecard/definition to exist first. Scoped, deferred, own grill.
- **D4 — Promotion (copy→master).** Promote-best-arm-to-master for **real-repo** runs (R2 RESOLVED a).
  The control is never promoted. NEW action; deferred (the v1 fixture is a pure control, never promoted).
- **D5 — The reference FIXTURE itself.** The design is **fixture-agnostic** (RESEARCH §2.6): the control
  plugs into the `control` slot. The operator may supply it later; v1 tests use a tiny synthetic fixture.

---

## 2. The control mechanism (the spine) — LOCKED

The benchmark is an **experimental control design**, not a rigid scoring rubric.

### 2.1 Immutable reference = the control
- A benchmark anchors on an **immutable reference** — a reference code repo (coding) or research project.
  **The original is never mutated.** It is the control.
- Each run **clones the reference into a sibling working copy** named `<name>-katabenchmark<N>` (N = run
  index). **R4 RESOLVED — sibling directories** beside `<name>`; **persist until pruned or promoted**;
  a `prune` convenience exists.
- Run N times → N standing frozen copies, each scored vs the control's embedded criteria **and** vs each
  other.
- **Rigidity = the control, not the metric.** Byte-identical start + identical system/input/prompt across
  arms ⇒ any outcome delta is attributable to the variable under test.

### 2.2 NEW vs reused (the clone primitive)
- **NEW capability — `tools/benchmark_control.py`.** Sibling-directory **byte-copy** of the immutable
  reference + `*-katabenchmark<N>` naming + next-N allocation + **content-hash pin** (hashlib over the
  sorted file set) + drift detection (flag if the ref dir was touched since pin). v1 uses `shutil.copytree`
  + `hashlib` — **no subprocess, no new exec sink** (deliberate zero-new-sink posture; `protocol/exec-safety.md`
  unchanged).
- **NOT a `kata-worktree` reuse.** `kata-worktree` (`skills/coordinate/kata-worktree/SKILL.md:43-60`)
  creates **branches off a fork-point inside one repo sharing the object store** — a different primitive
  from a sibling-directory byte-copy of an immutable reference. `kata-worktree` is reused **only** on the
  deferred concurrent-arm path (D1), to isolate per-arm work *within* clones.

### 2.3 Promotion — LOCKED, DEFERRED (R2 RESOLVED a)
Promotion (pick best arm → new master) applies **only** to runs against the user's **real** repo; the
synthetic fixture is a pure control, never promoted. The control reference is **never** overwritten either
way. NEW action — deferred (D4).

### 2.4 Benchmark-data anchor — LOCKED (R5 RESOLVED: both)
Comparison uses **both** (i) **embedded criteria** in the reference (hidden dual-gate tests + mutation
criteria + expected outcomes) and (ii) the **accumulated historical-scorecard distribution** across prior
runs ("is this optimal vs prior runs").

### 2.5 R1 control semantics — LOCKED
Immutable reference = frozen **starting state + embedded criteria**; scoring = run-vs-criteria +
run-vs-run; any gold/reference solution is **optional reference material only**, never the grader.

---

## 3. The two-axis scorecard + control-anchored metric

### 3.1 Axis Q — outcome quality (gated, ∈ [0,1]) — LOCKED mechanical (R-judge)
1. **Floor (necessary).** The `kata-evaluate` default-FAIL conformance signal, read from
   `.kata/RESULT.json` (`exitCode`/`failed` — `run_result.build_result`, `tools/run_result.py:54-97`).
   **Floor fails ⇒ Q = 0**, regardless of cost.
2. **Dual-gate (SWE-bench-style) — NEW interpretation, test-IDs-as-DATA.** The reference declares
   `FAIL_TO_PASS` + `PASS_TO_PASS` **test-ID lists** (embedded criteria). Both green = full credit;
   partial F2P = partial credit (secondary). `.kata/RESULT.json` carries only **aggregate** pass/fail
   counts (`_parse_pytest_counts`, `tools/run_result.py:84`), **not** per-test IDs.
   **The F2P/P2P test-IDs are run as DATA via the existing INTERNAL sink** `mutation_check.run_named_test`
   (`tools/mutation_check.py:71` — fixed `["uv","run","pytest", "<path>::<name>", "-q"]` argv, `shell=False`;
   registered `protocol/exec-safety.md:58`), looped **once per declared test-ID**. The node-ID is **data in
   the argv list**, never string-interpolated into a shell command — also **correctness-preserving** vs the
   `::`/`[param]` metacharacters a `shell=True` string would mangle. The **interpretation** (both-green /
   partial) is NEW logic in `tools/benchmark.py`. **No `shell=True`, no `run_gate`, NO new subprocess sink,
   no external-trust question.** *(v1 fixtures are flat-function tests (D57 small-greenfield), which
   `run_named_test`'s `path::name` shape covers; full class-nested node-ID grammar is a deferred concern,
   not a v1 blocker.)*
   > **Frozen note — embedded commands are never shell-executed.** A control reference's embedded
   > criteria, and any control resolved by `repeat_from` (path / registry / URL = **external trust
   > domain**), supply **declared test-IDs (data) only**. A control-supplied **command string is never
   > passed to a shell** — that would be the exact RCE class `protocol/exec-safety.md` forbids. Only
   > test-IDs flow into the fixed argv. This keeps "zero new exec sink / no exec-injection" a frozen
   > invariant the artifact actually satisfies (§12).
3. **Mutation survival (anti-weak-test multiplier).** Reuse `.kata/mutation.json` `allNonVacuous`
   (`gate_emit.emit_gate_artifacts`, `tools/gate_emit.py:129-136`; records `{testWentRed, nonVacuous}`
   from `tools/mutation_run.py`). This is the structural edge over SWE-bench's weak-test failure mode.

### 3.2 Axis C — efficiency (normalized cost)
tokens in/out · **$ cost** (per-model rate table — multi-model arms price differently) · wall-clock ·
tool-call count · #escalations · #fix-loop iterations (thrash) · #subagent dispatches. All sourced from
the metering hook (§3.3).

### 3.3 Metering hook → `.kata/usage.json` — **NET-NEW, CONFIRMED build dep** (R-cost RESOLVED)
The harness does **NOT** persist per-arm token/cost today (verified): `kata_dispatch.build_result`
captures `taskId/role/platform/model/status/payload/raw` only — **no usage**
(`tools/kata_dispatch.py:216-223`); `run_result.build_result` (RESULT.json) carries none
(`tools/run_result.py:86-97`). Axis C therefore requires a **net-new** `tools/usage_meter.py` writing
`.kata/usage.json` (per-arm tokens/$/wall-clock/tool-calls/escalations/thrash). Wall-clock is trivially
available; $ derives from a per-model rate table; token capture is **host-dependent** and labeled honestly
(host metering for the main loop; CLI-emitted usage for routed arms). Without this hook there is no Axis C.

### 3.4 The metric — dynamically applicable, control-anchored (NOT a rigid standard)
- The **fixed element is the control** (§2); the metric is **comparison-relative** (run-vs-criteria,
  run-vs-siblings).
- **Floor-gate (the "without one dominating" mechanism).** Efficiency is scored **only among
  floor-passers** — a cheap-wrong answer scores Q=0 and can never win. **Default-FAIL floor is absolute.**
- **R-A RESOLVED: both.** Present the **Pareto point (Q, C)** (per *AI Agents That Matter*) **and** a
  convenience scalar (e.g. `Composite = Q / (1 + λ·C_norm)` among passers) — **both behind the floor-gate.**
- **Weights flex by profile** — `benchmark.profile: balanced | cost-lean | quality-strict` (the *dynamic*
  half; the *control* is the rigid half).

---

## 4. The Benchmark Definition artifact — replay-by-definition (LOCKED)

Every benchmark emits a durable, **content-pinned** `benchmark.def.json` (the benchmark's analog of
`kata.config`) that **fully re-runs it by definition**. **NEW** — `tools/benchmark_def.py`.

- **Fields:** `benchmark_id` · `created` · `parent_benchmark_id` (lineage) · `control {kind: code|research,
  ref, content_hash}` · `criteria_ref` · `arms[] {label, mode, modules, effort, model, routing}` ·
  `metric {profile, weights, floor_gate}` · `k_repeats` · `inputs {system, prompt, input_refs}` ·
  `naming "<name>-katabenchmark{N}"` · `provenance {tool_version, skill_versions}`.
- **Content-pinned control** ⇒ a repeat re-clones the **byte-identical** reference; drift is detected and
  flagged.
- **Durable/disposable split (D81):** the **definition is durable + pointable** (e.g.
  `benchmarks/<id>/benchmark.def.json` or a registry); the spawned copies + raw scorecards are disposable
  run artifacts. The definition is **NOT** trapped in `.kata/`.
- **`repeat_from` pointer:** the benchmark config names an existing definition by **location** (path /
  registry id / URL) and re-executes an exact mirror — you point, you don't re-specify.
- **Delta mode (first-class):** a `repeat_from` re-run produces a **delta report** that diffs the new
  scorecard against the referenced prior run(s) and **leads with the delta** (Δquality, Δcost,
  ΔPareto-position), `provenance`-stamped. **Same definition + newer harness = an honest harness-delta
  measurement** — which IS the **C-on/C-off learning-lift** measurement (D99).

---

## 5. Hidden activation — the off-by-default `benchmark` module (LOCKED)

Mirror the **exact** `kata/module/slop` mechanism (verified precedent —
`skills/evaluate/kata-slop-check/SKILL.md:36-45` activation guard; `protocol/config.md:105-108` Optional
modules table; `modules` array `protocol/config.md:14`; load-guard fail-closed on a module key with no
provider `protocol/config.md:103-104`).
- **NEW:** a `benchmark` module key (`kata/module/benchmark`), its provider skill `kata-benchmark-report`,
  and a `benchmark` config block (mirrors `bakeoff: {n, lineage}`, `protocol/config.md:19`) carrying
  `{profile, k_repeats, repeat_from?, def_out}`.
- Triggered by `--benchmark` / `KATA_BENCHMARK=1` / a hand-added `benchmark:` block in `kata.config`.
- **NOT** surfaced in `kata-bootstrap`'s "how careful" dial and **not** in the standard advanced drawer —
  discoverable only if you know it exists. **Bootstrap stays untouched** (clean for normal users).
- **Absent ⇒ zero overhead, zero behavior change (BC).** Silent no-op, exactly like slop.

---

## 6. The two operator use-cases → run-shapes

**(b) Dev mode-comparison over a standard fixture — v1.** Repeated **paired / sequential** runs (D57
small-greenfield shape) of mode X vs mode Y against the immutable reference. Support **k-repeats per arm**
→ report mean ± spread, **label n explicitly**, bake in **"n=1 = directional, not proven"** (extends the
*exercised ≠ proven* convention). **R6 RESOLVED: k default = 1** (honest n=1 directional), configurable.

**(a) Concurrent same-task loops — DEFERRED (D1).** RESEARCH §6 routes this onto the `bakeoff` module
(best-of-N, AgentHub/worktrees). **Verification finding:** the bakeoff **config surface** exists
(`protocol/config.md:19`; `batch` runshape `skills/coordinate/kata-bootstrap/resources/run-shapes.md`) but
its **execution is Spec B — "configurable now, executable later," not built.** Claiming v1 "rides the
bakeoff module for concurrent arms" would be a documentation-only seam. v1 therefore delivers the **scorer
that ranks arms** (so the moment Spec B lands, concurrent ranking is free) but the **concurrent-arm driver
is deferred** with Spec B. This is the **legal outcome-comparison axis** (modes/routing/config), never the
retired grill-vs-baseline RCT (D70/L11).

---

## 7. The benchmark report — second report, same two-tier format (LOCKED: reports NEVER gate)

Mirror the two-tier closeout. **NEW skill `kata-benchmark-report`** (evaluate category, module-gated —
exact precedent: `kata-debrief`, `skills/evaluate/kata-debrief/SKILL.md`) authors it; the pure
deterministic engine `tools/benchmark.py` (the D99 smallest-v1 scorer) does every join over
`.kata/{RESULT,footprint,mutation}.json` + `.kata/usage.json` + the criteria → emits
`.kata/benchmark/<run-id>.json`.
- Reuses the `kata-report` two-tier `{{TOKEN}}` shape (`skills/evaluate/kata-report/SKILL.md:44-57`) +
  the committed template + BRAND palette (`modules/closeout/resources/closeout-report.template.html:6-33`,
  `BRAND.md`).
- Benchmark-specific tiles: scorecard (Q, C, composite) · **Pareto position** vs control/baseline ·
  **per-arm comparison table** · **optimization recommendations** as callout tiles.
- **Delta header (§4):** when launched via `repeat_from`, the report leads with Δquality · Δcost ·
  ΔPareto-position vs the referenced prior run + a *same-definition/different-provenance* banner.
- **Reports NEVER gate** (spine #4; the gate is and stays `kata-evaluate`). The report **transcribes**
  the floor verdict; it confers none. **n=1 directional honesty** is mandatory in every output.

---

## 8. Human-gated optimization feedback (C-arc tie-in) — LOCKED, DEFERRED (D3)

At a benchmarked run's close, report recommendations feed the **`kata-improve` T2 proposal mechanism**
(propose-never-apply, verified `skills/meta/kata-improve/SKILL.md:85-153`: auto-DRAFT `PROPOSAL-*.md` →
freeze-gate `kata-review` → **human merge**, footprint pinned, **never auto-applies**).
- **R-scope RESOLVED:** the proposal surface starts with **`kata.config` defaults + routing tables**
  (low blast-radius); skill-prompt edits are a later tier. "The KataHarness model" = the harness's own
  config/skills, **NOT** a trained ML model.
- **C/B invariant — LOCKED:** optimization is **propose-never-apply, human-gated.** The benchmark and the
  learning-loop optimizer are **one mechanism viewed twice** (D99 tumbler #4: same machinery measures
  C-on vs C-off lift).
- The kata-improve T2 *pattern* is reused; the **benchmark-specific proposal sub-mode is NEW and
  DEFERRED** (its own slice + grill — it needs the v1 scorecard/definition to exist first).

---

## 9. Fairness + anti-contamination (KataHarness edge)
Comparing **configs of the same harness on the same control with the model held constant** (D13/D14) means
training-leakage hits every arm **equally** and **cancels in the relative ranking**. It does **not** cancel
for the **absolute** "was this optimal" judgment → answered by the control's embedded criteria + historical
scorecards (§2.4) + **mutation-proof + hidden criteria** to kill weak-test inflation.

## 10. Maps onto existing machinery (verified ledger)

| Need | Surface | Verified `file:anchor` | Kind |
|---|---|---|---|
| Floor verdict | `.kata/RESULT.json` | `tools/run_result.py:54-97` | REUSE |
| Anti-weak-test multiplier | `.kata/mutation.json` `allNonVacuous` | `tools/gate_emit.py:129-136` | REUSE |
| Footprint manifest | `.kata/footprint.json` | `tools/footprint.py:107-133` via `gate_emit.py:117-122` | REUSE |
| Run F2P/P2P **test-IDs (data)** | `mutation_check.run_named_test` per test-ID (fixed `shell=False` argv, registered INTERNAL) | `tools/mutation_check.py:71`; `protocol/exec-safety.md:58` | REUSE (no new sink; no `run_gate`) |
| Off-by-default module | `kata/module/slop` precedent | `kata-slop-check:36-45`; `config.md:105-108` | REUSE pattern |
| Two-tier `{{TOKEN}}` report | `kata-report` + template + BRAND | `kata-report:44-57`; template `:6-33` | REUSE |
| Module-gated report skill | `kata-debrief` precedent | `skills/evaluate/kata-debrief/SKILL.md:1-46` | REUSE pattern |
| Propose-never-apply | `kata-improve` T2 | `skills/meta/kata-improve/SKILL.md:85-153` | REUSE pattern (instance NEW/deferred) |
| Per-arm tokens/$/wall-clock | **none persisted** | `kata_dispatch.py:216-223`; `run_result.py:86-97` | **NEW** `tools/usage_meter.py` |
| Deterministic scorer | — | — | **NEW** `tools/benchmark.py` |
| Dual-gate F2P/P2P interpretation | RESULT.json has aggregate counts only | `run_result.py:84` | **NEW** (in `benchmark.py`) |
| Benchmark Definition + delta | — | — | **NEW** `tools/benchmark_def.py` |
| Control-clone sibling-dir + hash | not `kata-worktree` (branches, not byte-copy) | `kata-worktree:43-60` | **NEW** `tools/benchmark_control.py` |
| `benchmark` module + config block | mirrors slop + `bakeoff:{n,lineage}` | `config.md:19,105-108` | **NEW** |
| Report skill | mirrors `kata-debrief` | — | **NEW** `kata-benchmark-report` |
| Concurrent bakeoff arms | bakeoff **execution = Spec B, not built** | `config.md:19` (Spec B); run-shapes.md | **DEFERRED (D1)** |

## 11. LOCKED decisions (RESEARCH §11) — frozen
- **R1 control semantics — LOCKED:** frozen starting state + embedded criteria; run-vs-criteria + run-vs-run; gold solution = reference material only.
- **R2 promotion — LOCKED (a):** real-repo only; fixture never promoted; control never overwritten. (DEFERRED build, D4.)
- **R3 research-mode scoring — LOCKED (ii):** deterministic-where-possible + fresh-context judge for the remainder; human final call. (DEFERRED build, D2.)
- **R4 spawned-copy location/retention — LOCKED:** sibling dirs; persist until pruned/promoted; `prune` convenience.
- **R5 benchmark-data anchor — LOCKED:** both embedded criteria + historical-scorecard distribution.
- **R-A composite — LOCKED:** both Pareto point + convenience scalar, both behind the floor-gate.
- **R6 k-repeats — LOCKED:** default 1 (n=1 directional), configurable to k.
- **R-cost metering — LOCKED (verified):** not persisted today → metering hook is a confirmed net-new build dep.
- **R-scope optimization surfaces — LOCKED:** start with `kata.config` defaults + routing tables; skill-prompt edits later tier; "the model" = harness config/skills, not a trained ML model.
- **R-judge — LOCKED:** Q is purely test/mutation-mechanical for v1; judged code-quality is v2 opt-in.
- **Replay-by-definition — LOCKED (operator add):** content-pinned, provenance-stamped Benchmark Definition; `repeat_from` + delta mode.

## 12. Invariants honored
Reports never gate · default-FAIL floor is absolute (Q=0 below it) · C/B invariant (optimization is
propose-never-apply, human-gated) · n=1 directional honesty · exercised ≠ proven · no exec-injection (v1
introduces **zero** new subprocess sinks; any future clone-via-git or judge-spawn registers in
`protocol/exec-safety.md` with structured argv + `shell=False`) · no secrets · skills held at 0.1.0
(Policy A).
