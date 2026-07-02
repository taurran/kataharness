---
spec: freeze-float-m1
title: Freeze/Float — Milestone 2, M1 (contract edges `builds_against` + 3 companions)
status: draft-pending-freeze-gate
created: 2026-07-02
baseline_branch: hardening/kenjiri-lessons
tags:
  - kata/freeze-float
  - kata/spine
  - contract-edges
---

# Freeze/Float M1 — contract edges (`builds_against`) + 3 companions

## Origin & principle

From the Freeze/Float doctrine (validated draft v2). **Control governs WHAT gets built; efficiency
governs WHEN and BY WHOM. Drift lives entirely in the WHAT.** KataHarness floats only layer **C (work
partition/scheduling)**, under machine-checked, fail-closed invariants; layers A (intent) and B
(contracts) stay frozen + human-gated. M1 is the first and safest float: a contract-only dependent
dispatches at freeze (in parallel) instead of waiting for its provider task to finish — **free
wall-clock, same tokens**. The doctrine's own critic found v1 UNSOUND (7 material holes); M1 is sound
**only with its 3 companions**, so they ship together.

**HARD LINE (critic-endorsed, unchanged):** any change to a contract, constant, criterion, or scope is
never re-decomposition — it routes through the existing human-gated supersede path
(`protocol/escalation.md`, `kata-orchestrate:507-509`).

## Grounding (verified against the code — 3 fresh-context investigators, 2026-07-02)

- **No `builds_against`/`contract_hash`/`contracts/`-stub exists yet** (grep-clean) — greenfield within a
  known doctrine.
- **Frontier is PROSE-DRIVEN** — no DAG engine. The dispatchable predicate is one sentence at
  `kata-orchestrate:211` (+ LD6 echo `:481`). Schema canonical at `kata-plan/RUBRIC.md:29-35`.
- **Restore is PLAN-derived** (`kata_restore.parse_plan_tasks`): re-dispatch set = PLAN task-ids −
  integrated (`Kata-Task:` trailers). A task-id known *only* via a `builds_against` key would be dropped
  → under-dispatch. **This is the one hard code requirement.**
- **Reuse targets:** pin = `iac_apply.plan_hash` + `approval_verdict` (yields named
  `APPROVED`/`APPROVAL_INVALIDATED`); multi-file = `benchmark_control.content_hash`/`detect_drift`;
  supersede hook = `kata-orchestrate:507-509`; abort in-flight = `kata-worktree:58-59` (remove+prune);
  re-open integrated = fix loop `:572-618` (footprint-intersection); import-scan =
  `graph_gen._extract_imports`/`_resolve_module` (the only import scanner; Python/tree-sitter only);
  final-gate machine-check slot = `kata-orchestrate:525-540` (fail-closed like `.kata/iac.json`);
  freeze-gate = fresh-context `kata-review` (`RUBRIC.md:20` attack surfaces).

## LOCKED decisions (grill surfaces resolved — freeze-gate will attack these)

- **M1-L1 — Contract = a named fileset, hashed as a set.** A contract has an id and a fileset (the
  degenerate case is one file). Pin `contractId@hash` via `benchmark_control.content_hash` (netstring
  length-prefixed, rename-sensitive, collision-safe — D98); a rename or byte change ⇒ new hash. The
  PLAN's `builds_against: { <task>: [ "<contractId>@<hash>" ] }` is the machine-readable binding.
- **M1-L2 — The frontier clause is additive prose; the restore parser union is the only hard code.**
  `kata-orchestrate:211` (+`:481`) gains: a task whose only unmet edges are `builds_against` is
  dispatchable at freeze (the contract is pinned). `kata_restore.parse_plan_tasks` MUST union
  `builds_against` keys into the task-id set (mirrors the `depends_on` block) — with tests. Absent any
  `builds_against` ⇒ byte-for-byte unchanged (BC).
- **M1-L3 — Invalidation is a deterministic inversion + a BLOCK-until-enumerated gate (companion 1).**
  New engine surface `contract_edges.py`: `invert(builds_against) -> {contractId: [tasks]}` and
  `invalidation_set(builds_against, changedContractId) -> [tasks]`. On a human-gated supersede that
  touches contract C (at the `kata-orchestrate:507-509` choke point), the orchestrator MUST enumerate
  `invalidation_set(C)` BEFORE folding the supersede; the fold is BLOCKED until the set is enumerated and
  each member routed: **in-flight** → abort worktree (`kata-worktree` remove+prune) + re-dispatch off the
  new point; **integrated** → force re-open through the fix loop (`:572-618`). Reuse
  `iac_apply.approval_verdict` shape (`APPROVED`/`APPROVAL_INVALIDATED`) for the per-contract verdict.
  Empty set (no `builds_against`) ⇒ vacuous ⇒ today's `:507-509` path unchanged (BC).
- **M1-L4 — Stub lifecycle is plan-authored + final-gate machine-scanned (companion 2).** The planner
  pre-owns a `contracts/` STUB fileset to the DEPENDENT (an `ownership:` entry — precedent `RUBRIC.md:48-51`);
  the PROVIDER task's `action` + a falsifiable `acceptance_criteria` carry the stub-retirement obligation.
  The FINAL gate (`kata-orchestrate:525-540`) adds a deterministic machine check (new
  `contract_edges.surviving_stubs(...)` over `graph_gen._extract_imports`): on the merged integration tree,
  **zero `builds_against` contract imports may still resolve to a `contracts/` stub path** — every contract
  import must resolve to the provider's real integrated module. A surviving stub ⇒ NEEDS_WORK (fail-closed,
  same posture as absent `.kata/iac.json`). Non-Python contracts are out of scope for the machine scan (the
  scanner is tree-sitter/Python); a language-agnostic scan is deferred (flagged, not silently skipped).
- **M1-L5 — Edge honesty is a freeze-time machine check + a review backstop (companion 3).** At FREEZE,
  a `builds_against` dependent's test files may import ONLY the declared contract surface (the `contracts/`
  fileset paths), never the PROVIDER's owned implementation paths (known from the `ownership:` map). New
  `contract_edges.edge_honesty(plan) -> [violations]` reuses `_extract_imports`/`_resolve_module`. A
  violation ⇒ the edge is really `depends_on` and MUST be reclassified before freeze. Backstop: a new
  `kata-review` attack surface (`RUBRIC.md`) flags it as HOLD → deliberate reclassification. (Primary is
  the machine check because it is deterministic; the review is the human-judgment net.)
- **M1-L6 — No layer-A/B float.** M1 floats only scheduling. A contract/criterion/scope change is NEVER
  re-decomposition — it is the human-gated supersede (M1-L3). The frozen INTENT and LOCKED decisions are
  untouched by anything here.
- **M1-L7 — Additive-BC everywhere.** Every surface no-ops when no `builds_against` edge is declared
  (0 exist today). No existing run acquires new blocking behavior. This is the same additive boundary as
  `kata_preflight` manifest-absent and IaC-absent.

## Companions ↔ critic findings (v1→v2 coverage this DESIGN must satisfy)

| Critic finding (v1) | Covered by |
|---|---|
| #1 dependents gate vacuously via leaking stubs | M1-L4 final-gate surviving-stub scan |
| #2 contract supersede strands in-flight consumers | M1-L3 invalidation set + abort/re-open |
| #3 builds_against honor-system | M1-L5 edge-honesty machine check + review |

## Change-map (grounded, per phase — see PLAN)

| Surface | File | Change | Kind |
|---|---|---|---|
| Schema | `skills/plan/kata-plan/RUBRIC.md:29-35,56-63` | add `builds_against:` + `contracts/` stub ownership + provider retirement obligation | prose |
| Frontier | `skills/coordinate/kata-orchestrate/SKILL.md:211,481` | dispatchable-at-freeze clause | prose |
| Restore | `tools/kata_restore.py` `parse_plan_tasks` | union `builds_against` keys (+ tests) | **code** |
| Pin+invalidate | `tools/contract_edges.py` (new) | `content_hash` pin, `invert`, `invalidation_set`, verdict (+ tests) | **code** |
| Supersede wiring | `skills/coordinate/kata-orchestrate/SKILL.md:507-509,634-637` | enumerate-and-BLOCK before fold; route abort/re-open | prose |
| Stub scan | `tools/contract_edges.py` `surviving_stubs` + `kata-orchestrate:525-540` | final-gate machine check, fail-closed (+ tests) | **code+prose** |
| Edge honesty | `tools/contract_edges.py` `edge_honesty` + `kata-review/RUBRIC.md:20` | freeze-time machine check + review surface (+ tests) | **code+prose** |

## Acceptance criteria

1. `validate_skills` 0/0; README in sync; every edited skill semver-bumped.
2. `pytest` green (baseline preserved) + new tests: parse_plan_tasks unions `builds_against` (restore
   under-dispatch guard); `content_hash` pin/verify + rename-sensitivity; `invert`/`invalidation_set`
   correctness incl. empty-set BC; `surviving_stubs` catches a stub that survives + passes when retired;
   `edge_honesty` flags an impl-import violation + passes a contract-only dependent. Each code-bearing
   change **mutation-proven**.
3. **BC:** a run with no `builds_against` edge is byte-for-byte unchanged across parser, frontier,
   supersede, final gate (explicit BC tests).
4. Snyk medium+ 0 on `tools/contract_edges.py` + `tools/kata_restore.py` (or documented-acceptance).
5. **Adversarial freeze-gate (`kata-review`, fresh context) on this DESIGN → SHIP** before the PLAN
   freezes; a HOLD routes back here. Plus a fresh-context adversarial review of the built invalidation
   logic (companion 1 — the highest-risk piece) at closeout.
6. Restore-hardening regression: an interrupted run with `builds_against` edges re-dispatches the correct
   set (no under-/over-dispatch) — proven against `kata_restore` tests.

## Out of scope (staged later — L9)

M4 (inline evaluator/reroll — consumes M1's edges + the F5/F3 substrate), M2 (shadow tasks), M3
(runtime re-partition / `partition_gate.py`, highest-power, own review). Language-agnostic contract
scanning (M1 scan is Python/tree-sitter only, flagged). This spec is M1 only.
