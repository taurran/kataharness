---
date: 2026-06-08
spec: modes-A4-version-up
status: FROZEN — passed convergence + coherence gate (D15); changes are deliberate re-freezes
source-ledger: ./GRILL-LEDGER.md (A4-GB1…GB10 + HOLD#1/#2/#3)
tags: [design, frozen, A4, version-up, kata-graph]
---

# A4 — Version-up + kata-graph — FROZEN DESIGN

The single contract execution serves. Compiled from the A4 grill ledger (converged + coherence-audited). No new
decisions here — every LOCKED decision traces to a resolved A4-GB branch.

## 1. Requirements satisfied
- **R1** Version-up: one-shot a feature into an **existing** repo without regressing the rest (the
  "review/feature an existing project" run-shape from A3-GB3/D36).
- **R2** Token-optimized ingestion of a large existing codebase (`kata-graph`) so the grill/plan/orchestrate
  loop runs cheaply (D41/GB8).
- **R3** "Don't break other aspects" is **structural**, not hope (footprint-scoped ownership + full-suite-green).
- **R4** Long-running survives human-in-the-loop: escalations are rare, async, high-signal (GB9/GB9.3/GB9.4).
- **R5** A clean substrate (`kata.graph.json` contract) that the deferred Obsidian-KG and kata-understand specs
  project from without back-modification (GB2/GB7).

## 2. Where it lives (components / insertion points)
| Path | Change | Responsibility |
|---|---|---|
| `skills/plan/kata-graph/SKILL.md` | **create** | build the token-budgeted structural map; pluggable backend; optional module `kata/module/graph` |
| `protocol/graph.md` | **create** | the `kata.graph.json` contract schema (nodes/edges/meta) |
| `protocol/escalation.md` | **create** | the structured escalation-payload schema (GB9.4) |
| `skills/plan/kata-grill/RUBRIC.md` | modify | Phase 0 invokes `kata-graph` when `target.kind == existing`; seeded digest into context |
| `skills/plan/kata-plan/RUBRIC.md` | modify | version-up: footprint = modified ∪ depth-1 reverse-dependents → disjoint ownership; blast-radius computed here |
| `skills/coordinate/kata-orchestrate/SKILL.md` | modify | **wave-loop → rolling DAG-frontier dispatch; synchronous escalation → async park/drain/hard-wait** (supersedes, P1) |
| `skills/coordinate/kata-readiness/SKILL.md` | modify | version-up readiness BLOCK if tree-sitter absent (GB1.1) |
| `skills/evaluate/kata-evaluate/SKILL.md` | modify | version-up note: regression = baseline suite still green + new tests green (reuses rubric #2/#6, no new evaluator) |
| `protocol/config.md` | modify | add `graph` block: `{ budget, marginDepth, backend }` tunables |
| `tools/validate_skills.py` + tests | modify | `REQUIRED_PROTOCOL` += `graph.md`, `escalation.md`; kata-graph frontmatter |
| `README.md` · `.planning/SKILL-COST-RATINGS.md` · `docs/TAXONOMY.md` | modify | register `kata-graph` |
| `.planning/DECISIONS.md` · `STATE.md` · `ROADMAP.md` | modify | promote A4-GB → D47+; status |

**Held at version 0.1.0** (pre-release policy A) — no skill version bumps.
**Out of scope (deferred, clean):** Obsidian KG emit/ingest + `knowledgeGraph` config + frontmatter profiles
(own spec under kata-understand, GB7); engram-mediated escalation (GB10). A4 adds NO `knowledgeGraph` config and
NO inert hooks.

## 3. LOCKED decisions
Each is locked *structure*; tunable *values* are marked `[TUNABLE]`.

**L1 (GB1/GB1.1) — tree-sitter is the hard floor.** `kata-graph`'s default backend requires tree-sitter
(local, no API, `uv`-installable, D29 pre-flight). "Agnostic" = tool-agnostic, not dependency-free (spine #3).
grep-only is a labeled "reduced — no AST" map for **greenfield/exploration only**; **version-up BLOCKs at
readiness if tree-sitter is absent** (no inert blast-radius). *Rejected:* grep-default (can't rank → defeats
token-optimization).

**L2 (GB2/GB2.1/GB2.2/GB2.4) — the `kata.graph.json` contract** (full schema → `protocol/graph.md`):
- `file` node: `id`(=path,REQ)·`kind:"file"`·`path`·`hash`·`rank`(REQ; PageRank every floor build)·`lang`(OPT)·`community`(OPT).
- `symbol` node: `id`(=`path::name[~N]`,REQ)·`kind:"symbol"`·`path`·`name`·`symKind`(enum {function,class,method,interface,type,constant,other})·`span`(`[startLine,endLine]` 1-idx incl.,REQ)·`hash`·`rank`(REQ)·`signature`(OPT)·`community`(OPT).
- `edge`: `src`·`dst`·`kind`({def,ref,call,import})·`weight`(REQ,default 1.0). `def` file→symbol · `ref`/`call` symbol→symbol · `import` **file→file**. Floor MUST populate def+ref(+import best-effort); **`call` is oracle-only** (may be absent).
- `meta`: `{backend, repoHash, generatedAt}` — **no `seedSymbols`** (P2).
- Ids are line-independent (span is a property) → incremental-cache-safe. *Rejected:* line-in-id (cache churn); test-coverage edges (full-suite-green floor makes them unneeded — anti-bloat).

**L3 (GB8/GB8.1/GB8.2/GB2.3) — feature-agnostic cached graph; seeding + blast-radius are use-time
projections.** `kata.graph.json` is cached (content-hash, incremental) and **never feature-specific**.
`seedSymbols` = a per-run input (tokenize the feature description → case-insensitive match vs symbol `name` →
×10 PageRank boost, + user-named files), **never cached**. The **digest** = top-rank signatures selected until a
`[TUNABLE: budget=3000]`-token estimate (chars/4) is hit (selection, not truncation); no ×8 expansion.
Blast-radius = the planner inverting forward `ref∪call` edges. *Rejected:* baking the feature seed into the
cached artifact (contradicts agnostic cache).

**L4 (GB9/GB9.1/GB9.2) — version-up wiring.** Grill Phase 0 ingests the seeded digest (existing target).
`kata-plan` scopes **disjoint file-ownership = footprint = modified-files (from frozen DESIGN) ∪
`[TUNABLE: marginDepth=1]`-hop reverse-dependents** (over ref∪call); files outside are **off-limits, owned by no
task**. Regression contract: orchestrate precond #2 records baseline via `target.baselineGate` (full suite green
at fork); version-up `kata-evaluate` = **baseline suite still green + new feature tests green**, default-FAIL
(reuses rubric #2/#6, **no new evaluator**). *Rejected:* transitive-closure margin (owns half the repo).

**L5 (GB9.2/GB9.3-rev/GB9.4/D42) — escalation discipline.**
- **Defer-vs-escalate predicate:** **escalate IFF completing the owned task's acceptance test requires a write
  to an unowned file; everything else → `kata-defer`** (`DEFERRED.md`). Baseline regressions from unowned files
  are caught by the full-suite gate → a deliberate **re-scope at gate-time** by the orchestrator.
- **Most escalations are orchestrator-resolvable** (re-scope, auto) and never reach a human; only a
  **LOCKED-decision conflict** is `human-required`.
- **Rolling DAG-frontier dispatch (supersedes wave-gate):** a task is dispatchable iff (all `depends_on`
  integrated) ∧ (owned files disjoint from in-flight). Waves = a derived view.
- **Async escalation:** park the escalating task + its DAG-dependents; keep dispatching the frontier; checkpoint
  each completion in integration order (linear history); **hard-wait for the human IFF frontier empty ∧ open
  escalations remain.** No separate "criticality" knob — frontier-blocked IS the test.
- **Structured payload is its OWN contract (GB9.4):** board stays one-line `ESCALATE | <task-id> | <summary>`
  (L3/append-only); the payload = `.kata/escalations/<task-id>.json` (schema → `protocol/escalation.md`):
  `{taskId, kind, decisionNeeded, optionsConsidered[], agentRecommendation, rationale, lockedDecisionInTension?,
  costOfWaiting, costOfProceeding, status, resolution?}`. Producer = escalating worker. *Rejected:* JSON in the
  one-line board message (breaks L3).

**L6 (GB6/D39 naming; GB10/D43 module) — `kata-graph` is ONE optional module** (`kata/module/graph`),
bundled-by-default by the version-up preset; pluggable backend (grep → tree-sitter floor → Graphify-MCP oracle),
not forked skills. `source:` names aider (MIT) + Graphify (MIT) per spine #12. Name-by-job (no `kata-pagerank`).

## 4. Integrity / edge cases
- **Stale cross-file edges on incremental rebuild:** ids are line-independent → a callee moving lines doesn't
  invalidate a caller's edges; only content-hash changes rebuild a file's nodes. ✔
- **Same-name symbols in one file:** `~N` ordinal in def order disambiguates. ✔
- **grep-reduced mode + version-up:** impossible by L1 (readiness BLOCKs) → no inert blast-radius.
- **Frontier dispatch + disjoint files:** the dispatch predicate's file-disjointness clause preserves the
  zero-merge-conflict worktree invariant even across former wave boundaries. ✔
- **Out-of-footprint write needed mid-run:** escalate (L5) → orchestrator re-scopes deliberately; never silent.
- **Human absent on a human-required escalation:** frontier keeps draining; hard-wait only when nothing else
  remains; (future GB10: engram auto-resolves first).

## 5. Backward-compatibility contract (checkable claims)
- **BC1** Greenfield runs are unchanged: with `target.kind == greenfield`, kata-graph is not invoked and the
  loop behaves exactly as today. *Check:* a greenfield run touches no `kata.graph.json`, no `.kata/escalations/`.
- **BC2** Rolling-frontier dispatch is a strict generalization of waves: any plan that ran wave-gated produces
  the same task set and the same disjoint-file guarantee. *Check:* a wave-structured plan integrates with 0
  merge conflicts and 0 drift under frontier dispatch.
- **BC3** No new evaluator: `kata-evaluate` is unmodified in contract (version-up note only); the conformance
  floor (D22) is unchanged. *Check:* validator still reports `kata-evaluate` cost 2, no `Write`/`Edit`.
- **BC4** All skills remain `0.1.0` (policy A). *Check:* validator green; no version bumped.
- **BC5** No `knowledgeGraph` config field is added (deferred). *Check:* `protocol/config.md` has no `knowledgeGraph`.

## 6. Acceptance criteria (default-FAIL, runnable)
- **A1** `cd tools && uv run pytest -q` → all pass (incl. new tests for `graph.md`/`escalation.md` required-terms).
- **A2** `cd tools && uv run python validate_skills.py` → `N skills checked — 0 error(s)` (N = 25: 24 + kata-graph),
  README in sync, kata-graph frontmatter conformant (`kata/plan`+`kata/module/graph`, cost-weight, source names aider+Graphify).
- **A3** `protocol/graph.md` documents every L2 field; `protocol/escalation.md` documents every L5 payload field;
  both enforced by `REQUIRED_PROTOCOL`.
- **A4** Behavioral (drift-magnet checks, fresh-context `kata-review` on the diff): (a) kata-graph emits no
  `seedSymbols` in `meta`; (b) `import` edges are file→file; (c) orchestrate has NO remaining synchronous
  wave-gate / synchronous-escalation prose (P1 actually applied, not narrated); (d) board stays one-line, payload
  is a separate `.kata/escalations/*.json`; (e) version-up readiness BLOCKs without tree-sitter; (f) no
  `knowledgeGraph` config leaked.
- **A5** Adversarial `kata-review` (D15) over the full A4 diff returns SHIP.

## 7. Test seams / testability
- **Highest machine seam:** the `tools/` validator (`REQUIRED_PROTOCOL` for graph.md/escalation.md; kata-graph
  frontmatter; README sync) — pytest-gated, the default-FAIL floor for the prose/schema work.
- **Contract seam:** `protocol/graph.md` + `protocol/escalation.md` are the testable schemas; a fixture
  `kata.graph.json` / escalation payload can be validated against the documented field sets.
- **Prose-correctness seam:** the fresh-context adversarial `kata-review` (A4/A5) — the no-write evaluator for
  the skill-body changes (orchestrate supersession, grill/plan version-up wiring) that the validator can't check.
- kata-graph's *runtime* (actual tree-sitter parsing/PageRank) is **not** built in A4 as executable code — A4
  ships the skill contract + protocol schemas; the executable backend is exercised when the harness runs
  version-up for real (dogfood). A4's acceptance is schema/frontmatter/prose-conformance + adversarial review.

---
**FROZEN.** Hand to `kata-plan` for the task-level PLAN (which MUST include P1's concrete `kata-orchestrate`
edit as a bounded task). Changes to this DESIGN are deliberate re-freezes, not edits-in-flight.
