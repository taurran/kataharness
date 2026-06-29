---
title: kata-loop-benchmark — frozen task-level PLAN
status: FROZEN (authored from DESIGN.md; ready for freeze-gate kata-review)
date: 2026-06-28
design: ".planning/specs/kata-loop-benchmark/DESIGN.md"
spine: ".planning/specs/kata-loop-benchmark/RESEARCH.md"
policy: "Skills held at 0.1.0 (Policy A). NEW skills enter at 0.1.0."
---

# kata-loop-benchmark — PLAN (frozen)

> Buildable v1 = the **deterministic scorer (D99 smallest-v1)** enriched with the control / definition /
> report / hidden-module / **net-new metering hook** (DESIGN §1). Heavier pieces are phased out explicitly
> (DESIGN §1 D1–D5). Every slice owns a **disjoint file set** (one owner per file — no two slices touch the
> same file). Code-bearing slices are **TDD + mutation-proof** (`tools/mutation_run.py` discipline). The
> scorer/def/meter/control engines are **PURE** (no subprocess) — mirroring `tools/debug_report.py` — so
> `protocol/exec-safety.md` is **unchanged** (zero new sink, deliberate).

## v1 slice list (disjoint ownership)

### S1 — Metering engine → `.kata/usage.json` (NET-NEW, CONFIRMED dep)
- **Owns:** `tools/usage_meter.py` · `tools/tests/test_usage_meter.py`
- **Builds:** the `usage_schema()` (per-arm `tokensIn/tokensOut/costUSD/wallClockS/toolCalls/escalations/
  thrashIters/subagentDispatches`, arm `label`, `model`) · `build_usage(...)` (pure) · `cost_from_rate_table`
  (per-model `$`/token table; multi-model arms price independently) · `write_usage(.kata/usage.json)`. Token
  capture is host-dependent → `tokensIn/Out` are **nullable** and honestly labeled when the host did not
  surface them (wall-clock + tool-calls always present). PURE; injectable clock; no subprocess.
- **Verify:** `cd tools && uv run pytest tests/test_usage_meter.py -q`
- **TDD:** yes · **Mutation:** yes
- **Why first:** Axis C has no input without it (DESIGN §3.3); it is the confirmed net-new build dep.

### S2 — Deterministic scorer `tools/benchmark.py` (NEW; D99 smallest-v1)
- **Owns:** `tools/benchmark.py` · `tools/tests/test_benchmark.py`
- **Input contract (EXPLICIT — multi-arm).** The scorer takes a **map `arm_label → that arm's clone
  artifact root`**, where each root holds that arm's `.kata/{RESULT,footprint,mutation,usage}.json`. It
  scores **every arm** and produces the per-arm comparison table + per-arm Pareto positions (DESIGN §7) —
  it is **not** single-arm. A single-arm run is the degenerate 1-entry map. (S6 wires clone-dir →
  arm-map.)
- **Builds:** the pure scorer over each arm's `.kata/{RESULT,footprint,mutation}.json` + `.kata/usage.json`
  + the embedded criteria → **Axis Q** (floor-gate from RESULT.json `exitCode`/`failed`; **NEW** dual-gate
  F2P/P2P interpretation — both-green/partial; mutation multiplier from `mutation.json.allNonVacuous`) →
  **Axis C** (normalize the usage fields) → **floor-gated composite** (Pareto point `(Q,C)` + convenience
  scalar `Q/(1+λ·C_norm)` **only among floor-passers**) → per-arm ranking → `scorecard_schema()` →
  `emit_scorecard(.kata/benchmark/<run-id>.json)`. **Floor fail ⇒ Q=0** (absolute). Profile weights
  (`balanced|cost-lean|quality-strict`). The F2P/P2P **test-IDs are run as DATA** via the existing
  INTERNAL sink `mutation_check.run_named_test` (`tools/mutation_check.py:71`, fixed `shell=False` argv,
  registered `protocol/exec-safety.md:58`), looped per declared test-ID; the scorer consumes the booleans.
  **No `run_gate`, no `shell=True`, NO new subprocess sink** (DESIGN §3.1(2): a control's embedded
  *command strings* are never shell-executed — only its *test-IDs* run). The scorer's own engine functions
  stay PURE.
- **Verify:** `cd tools && uv run pytest tests/test_benchmark.py -q`
- **TDD:** yes · **Mutation:** yes
- **Dep:** S1 (reads `usage.json` shape).

### S3 — Benchmark Definition + `repeat_from` + delta (NEW)
- **Owns:** `tools/benchmark_def.py` · `tools/tests/test_benchmark_def.py`
- **Builds:** `def_schema()` (DESIGN §4 fields incl. content-pinned `control.content_hash`,
  `parent_benchmark_id`, `provenance`) · `build_def(...)` · `write_def`/`load_def` (durable, NOT `.kata/`
  — e.g. `benchmarks/<id>/benchmark.def.json`) · `resolve_repeat_from(location)` (path/registry id) ·
  `compute_delta(new_scorecard, prior_scorecard)` → `{dQuality, dCost, dParetoPosition, sameDefinition,
  provenanceDiff}` (the delta-mode headline; same-definition + newer-provenance ⇒ honest harness-delta).
  PURE.
- **Verify:** `cd tools && uv run pytest tests/test_benchmark_def.py -q`
- **TDD:** yes · **Mutation:** yes
- **Dep:** S2 (delta diffs `scorecard_schema`), S4 (pins `control.content_hash`).

### S4 — Control-clone + naming (NEW; not a worktree reuse)
- **Owns:** `tools/benchmark_control.py` · `tools/tests/test_benchmark_control.py`
- **Builds:** `sibling_name(base, n)` → `<base>-katabenchmark<N>` · `next_index(parent_dir, base)` ·
  `content_hash(ref_dir)` (hashlib over the sorted file set) · `detect_drift(ref_dir, pinned_hash)` ·
  `clone_control(ref_dir, dest)` (`shutil.copytree` — **no subprocess**) · `prune(copy_dir)` convenience
  (R4). Immutable reference is **never written**. PURE except the copytree/prune FS ops (injectable for
  tests). **No new exec sink** → `protocol/exec-safety.md` untouched.
- **Verify:** `cd tools && uv run pytest tests/test_benchmark_control.py -q`
- **TDD:** yes · **Mutation:** yes
- **Dep:** none (independent).

### S5 — `kata-benchmark-report` skill (NEW; mirrors `kata-debrief`)
- **Owns:** `skills/evaluate/kata-benchmark-report/SKILL.md` (+ optional `resources/`)
- **Builds:** the two-tier author/renderer that **drives `tools/benchmark.py`** (never re-derives a join
  in prose) and renders the `kata-report` `{{TOKEN}}` two-tier shape + BRAND tiles: scorecard (Q,C,
  composite), Pareto position, per-arm comparison table, optimization-recommendation tiles, and — when
  launched via `repeat_from` — the **delta header**. **Reports NEVER gate**; **n=1 directional honesty**
  in every output; voice `protocol/persona.md`.
- **Verify:** `cd tools && uv run python validate_skills.py` — this validates the **new skill's frontmatter
  standalone** (schema/naming/tags/allowed-tools). **It does NOT assert the full-suite index count**: the
  `45→46/0` index-count + central README regen is asserted only at the **integration gate** (S6 / D119
  precedent). S5-green = "this skill's frontmatter is valid," not "the suite index is consistent."
- **TDD:** n/a (skill prose) — gated by `validate_skills` + freeze-gate `kata-review`
- **Dep:** S2, S3 (contract dependency on scorecard + delta shapes).
- **Frontmatter (per STANDARDS §1):**
  ```yaml
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
  ```

### S6 — `benchmark` module + config + orchestrate wiring (NEW; reuses module mechanism)
- **Owns:** `protocol/config.md` (the `benchmark` Optional-modules row + the `benchmark` config block) ·
  `skills/coordinate/kata-orchestrate/SKILL.md` (dispatch `kata-benchmark-report` **iff**
  `kata/module/benchmark` present; the metering-hook write seam; the clone-per-run seam) · the central
  `README.md` skill-index regen is done at the **integration gate**, not owned here (D119 precedent).
- **Builds:** the off-by-default `benchmark` module (mirrors `kata/module/slop`,
  `protocol/config.md:105-108`) wired as a silent no-op when absent (BC); the `benchmark` config block
  `{profile, k_repeats, repeat_from?, def_out}` (mirrors `bakeoff:{n,lineage}`, `config.md:19`); the
  orchestrate seam that invokes the metering write (S1), the control clone (S4), the scorer (S2), and the
  report (S5) in the benchmark path. **`kata-bootstrap` is NOT touched** (flag stays out of the interview).
- **Arm-map wiring (the MINOR-1 producer side).** S4 produces one clone dir per arm
  (`<name>-katabenchmark<N>`); each arm's run emits its `.kata/{RESULT,footprint,mutation,usage}.json`
  under that clone root. This seam **assembles the `arm_label → clone-artifact-root` map** that S2's
  scorer consumes (DESIGN §7 per-arm comparison/Pareto). For a single-arm run the map has one entry; for
  k-repeats, one entry per `<arm>·repeat<k>`. (Concurrent multi-arm assembly is the same map shape — only
  the *launch* of arms is deferred with bakeoff/Spec B, D1.)
- **Verify:** `cd tools && uv run pytest tests/test_validate_skills.py -q` (module/provider registration)
  + `cd tools && uv run python validate_skills.py`
- **TDD:** n/a (doc/skill) — gated by `validate_skills` + freeze-gate `kata-review`
- **Dep:** S5 (provider skill must exist or the load-guard fail-closes), S1, S4 (seams it wires).

## Dependency DAG (build order)
```
Wave 1:  S1 (metering)      S4 (control-clone)      ← independent
Wave 2:  S2 (scorer)         [needs S1]
Wave 3:  S3 (def/delta)      [needs S2, S4]
Wave 4:  S5 (report skill)   [needs S2, S3]
Wave 5:  S6 (module+wiring)  [needs S5, S1, S4]
```
S1 ∥ S4 may run concurrently (disjoint, no dep). All file ownership is disjoint across all six slices.

## Where the control reference FIXTURE plugs in (deferred — D5)
The design is **fixture-agnostic** (RESEARCH §2.6). v1 tests use a **tiny synthetic fixture** under
`tools/tests/` (a few files with embedded F2P/P2P + mutation criteria). The **real** standardized control
fixture (the repo the operator may supply, orientation §5) plugs into the `control` slot later — it does
**not** block freeze. `S4.clone_control` + `S3.def_schema.control` are the slots it fills.

## Integration gate (per D98 / freeze-gate expectations)
1. **Freeze-gate `kata-review`** on THIS plan (fresh-context; HOLD→SHIP) — *before* build.
2. Build the DAG (waves above), each code slice TDD + mutation-proven in isolation (worktree per owner).
3. `kata-evaluate` **PART A** (default-FAIL conformance) PASS.
4. **D98 PART B** fresh-context `kata-review` red-team (reproduce-don't-trust: regenerate a scorecard,
   execute the F2P/P2P + metering seams) → SHIP.
5. **Gates green:** `pytest` (S1–S4 tests added) · **`validate_skills` 46/0** (one new skill registered;
   central README regenerated at the gate) · **Snyk med+ 0** on changed lines.
6. **Freeze invariants:** reports never gate · default-FAIL floor absolute · zero new exec sink
   (`exec-safety.md` unchanged) · n=1 directional honesty surfaced · no secrets · skills at 0.1.0.

## Explicitly DEFERRED to a later phase (named)
- **D1** Concurrent bakeoff arms (use-case a) — gated on **Spec B execution** (not built). v1 scorer
  already ranks arms; only the concurrent driver waits.
- **D2** Research-mode fresh-context judge (R3) — v2 opt-in.
- **D3** Benchmark→`kata-improve` T2 optimization-proposal sub-mode (config-defaults + routing-tables
  scope; propose-never-apply) — own slice + own grill; needs v1 scorecard/definition first.
- **D4** Promotion (promote-best-arm-to-master) for real-repo runs — NEW action; control never promoted.
- **D5** The real control FIXTURE — operator-supplied; design is fixture-agnostic.

## Risks / operator calls before freeze
1. **Use-case (a) re-scope (already taken in DESIGN §6):** RESEARCH §6 routed concurrent arms onto the
   `bakeoff` module, but bakeoff **execution is Spec B — not built**. The plan **defers** the concurrent
   driver (D1) and ships the arm-ranking scorer. **Confirm** this re-scope is acceptable (it does not
   change the metric; it only defers the parallel-launch plumbing). This is the one place the plan
   diverges from a literal RESEARCH reuse assumption — surfaced per `protocol/reuse-claims.md`.
2. **Token/$ fidelity:** per-arm token capture is **host-dependent**; v1 lands wall-clock + tool-calls
   reliably and labels tokens/$ honestly where the host does not surface them. Confirm that an
   Axis-C that is partially host-dependent is acceptable for v1 (it is the honest state of the surface).
3. **Six slices** is at the upper end of "lean" — S3/S5 could merge into S2 if the operator prefers a
   smaller slice count, at the cost of single-responsibility/disjoint-ownership cleanliness. Default
   keeps them split.
