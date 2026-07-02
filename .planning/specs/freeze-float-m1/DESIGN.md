---
spec: freeze-float-m1
title: Freeze/Float — Milestone 2, M1 (contract edges `builds_against` + 3 companions)
status: revised-v2-post-regate
created: 2026-07-02
revised: 2026-07-02
baseline_branch: hardening/kenjiri-lessons
freeze_gate: v1 HOLD (7 findings) → v2 HOLD (F3/F5 durability + F4 extractor + split) → all folded → phased build
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
(contracts) stay frozen + human-gated. M1's win: a contract-only dependent dispatches at freeze (in
parallel) instead of waiting for its provider task — **free wall-clock, same tokens**. Sound **only with
its 3 companions**; they ship together.

**HARD LINE:** any change to a contract, constant, criterion, or scope is never re-decomposition — it
routes through the human-gated supersede path (`protocol/escalation.md`, `kata-orchestrate:507-509`).

## Freeze-gate v1 (2026-07-02) — HELD with 7 findings; all folded into the LOCKED decisions below

The fresh-context adversarial freeze-gate held the first draft (5 soundness holes + 2 under-specs):
F1 stub-scan tested *location* not *content*; F2 stub fileset collided with disjoint-ownership; F3
BLOCK-until-enumerated was unenforced prose (not fail-closed); F4 un-superseded contract drift went
undetected; F5 restore re-shipped an invalidated integrated task; F6 `content_hash` is whole-dir; F7
`invalidation_set` risked a silent-permissive empty set. Every cited reuse point verified in-code.

**Freeze-gate v2 (2026-07-02) — HELD again; F1/F2/F6/F7 confirmed closed, F3/F5/F4 re-opened + scope.**
The v2 re-gate confirmed F1/F2/F6/F7 genuinely closed but found the v1 durability fixes leaked: **F5** —
`.kata/invalidated.json` is gitignored/disposable, lost on the canonical lost-run (`.kata/` wiped,
`refs/kata/trail` snapshots only `board.md`) → restore re-ships the stale task; **F3** — the "git
supersede trail" is an undefined signal (no `Kata-Supersede` artifact; drift ledger is a disposable
counter) → the independent re-derivation has nothing durable to check; **F4** — the surface extractor is
materially larger than `graph_gen._signature_of` → silent false negatives. Plus fail-closed gaps and
**#6 over-scope**. All folded below: durability → **git-durable commit trailers**, extractor **narrowed +
residual deferred**, fail-closed clauses (M1-L9), and M1 **split into a phased program** (see Phasing).
The frontier float clause lands LAST, only after its safety companions are wired.

## Grounding (verified — 3 investigators + freeze-gate, 2026-07-02)

- **Greenfield** — no `builds_against`/`contracts/`-stub/`contract_hash` in-repo (grep-clean).
- **Frontier is PROSE-DRIVEN** (no DAG engine): predicate at `kata-orchestrate:211` (+LD6 `:481`). Schema
  at `kata-plan/RUBRIC.md:29-35`. **Restore is PLAN-derived** (`kata_restore.parse_plan_tasks:251-269`),
  and today DROPS a `builds_against`-only task-id → the one hard restore fix.
- **Reuse:** pin verdict = `iac_apply.approval_verdict` (named `APPROVED`/`APPROVAL_INVALIDATED`);
  drift = `benchmark_control.detect_drift`; supersede hook `:507-509`; independent-re-derivation
  fail-closed pattern = the IaC gate (`kata-orchestrate:537-540`); abort = `kata-worktree:58-59`; re-open
  = fix loop `:572-618`; import-scan = `graph_gen._extract_imports`/`_resolve_module` (Python/tree-sitter
  only). **Net-new (not pure reuse):** interface **surface-hash** extraction (AST signatures, not bytes)
  — builds on `graph_gen`'s tree-sitter parser but is a new surface.

## LOCKED decisions (post-freeze-gate)

- **M1-L1 — Contract = one subdir `contracts/<id>/`, pinned by its INTERFACE SURFACE, not raw bytes
  (F6, F4-corollary).** One contract per subdirectory (makes a per-contract pin clean; whole-dir
  `content_hash` reuse then fits). The pin is the contract's **public interface surface** — exported
  names + function/method signatures + type/constant declarations, extracted via tree-sitter — **NOT full
  bytes.** Rationale: the provider fills stub *bodies* in its own task; a body-fill must NOT flip the pin
  (intended fulfillment), an *interface* change MUST. New `contract_edges.surface_hash(contract_dir)`
  (signature-order-normalized, netstring length-prefixed per D98). Binding:
  `builds_against: { <task>: [ "<contractId>@<surfaceHash>" ] }`.
  **Extractor scope (F4-narrowed):** the pinned surface is **function/method signatures INCLUDING return
  annotations + decorator lists + exported names** — the robustly tree-sitter-extractable set (`graph_gen.
  _signature_of` covers params only; this extends it with the `return_type` field + decorator nodes).
  **DEFERRED (documented residual, review-backstopped, NOT silently pinned):** module constants,
  `TypeAlias` declarations, `__all__`, and re-exports — a full AST-export visitor with a long edge-case
  tail. The DESIGN does NOT claim these are machine-pinned; a contract relying on a pinned constant is
  flagged for the `kata-review` backstop until a later milestone lands the export visitor. `surface_hash`
  **fails closed** (raises) on any parse-ERROR node in a `contracts/` file (M1-L9).
- **M1-L2 — Frontier clause is additive prose; the restore parser union is the only hard base-code.**
  `kata-orchestrate:211` (+`:481`): a task whose only unmet edges are `builds_against` is dispatchable at
  freeze. `kata_restore.parse_plan_tasks` MUST union `builds_against` keys into the task-id set (+ tests).
  Absent any `builds_against` ⇒ byte-for-byte unchanged (BC).
- **M1-L3 — Invalidation is durable + independently re-derived + fail-closed (companion 1; F3/F5/F7).**
  `contract_edges.py`: `invert(builds_against)`, `invalidation_set(builds_against, changedContractId)`.
  **F7 default-FAIL:** `invalidation_set` RAISES on absent/malformed/partial `builds_against` (non-str
  task key, value not an `id@hash` list) — never a silent empty set; only a **well-formed-absent** block
  is vacuous (mirrors `kata_restore` fail-closed `:223-234`). On a human-gated supersede touching contract
  C (`:507-509`), the orchestrator (i) enumerates `invalidation_set(C)`, (ii) routes each member —
  in-flight → abort worktree (`kata-worktree` remove+prune) + re-dispatch; integrated → force re-open
  (fix loop) — and (iii) records the disposition in **git-durable commit trailers** (F5): each re-opened
  integrated task gets a `Kata-Invalidated: <task-id>` trailer on an integration-branch commit, symmetric
  with the working `Kata-Task:` trailer (`kata-orchestrate:369`). **F3 fail-closed cross-check via a
  durable supersede signal:** a contract supersede writes a `Kata-Supersede: <contractId>@<newSurfaceHash>`
  trailer (git-durable, contract-attributed — the signal v2 found missing). The FINAL gate INDEPENDENTLY
  re-derives from `git log` trailers + the frozen PLAN's `builds_against`: for every `Kata-Supersede:` on
  a contract C, `invalidation_set(C)` MUST be fully covered by `Kata-Invalidated:` trailers (in-flight
  members) + re-dispatch; absent/partial coverage ⇒ **NEEDS_WORK** (IaC-gate independent-re-derivation
  pattern, `:537-540`) — soundness never rests on orchestrator compliance or a disposable file. **F5
  restore-durable re-open:** `kata_restore.collect_integrated_tasks` subtracts `Kata-Invalidated:`
  task-ids from the integrated set, so a crash mid-invalidation re-dispatches them (the `Kata-Task:`
  trailer alone would mask an integrated-but-invalidated task; the durable trailer survives the `.kata/`
  wipe on the canonical lost-run). A malformed/partial invalidation record **fails closed** (M1-L9).
  Empty **well-formed** set ⇒ vacuous ⇒ today's `:507-509` path (BC).
- **M1-L4 — Provider owns the contract; stub-ness is content-decidable (companion 2; F1/F2).** The
  **PROVIDER owns `contracts/<id>/`** (F2: one writer — no disjoint-ownership collision, no dependent
  re-dispatch). At freeze the provider authors the interface + a stub body carrying a required sentinel
  **`# KATA-CONTRACT-STUB`**; it fills the real behavior in its own task behind the same stable import
  path, deleting the sentinel. The DEPENDENT only IMPORTS `contracts/<id>/`. **F1 content-decidable final
  scan** (`contract_edges.surviving_stubs`, `kata-orchestrate:525-540`): on the merged tree, **zero
  `contracts/` files may still bear the sentinel** AND every `builds_against` contract import must resolve
  (no dangling after a retire-by-deletion). Surviving sentinel or dangling import ⇒ NEEDS_WORK,
  fail-closed like absent `.kata/iac.json`. (Sentinel grep + `_extract_imports` resolution *together* —
  neither alone suffices: path-resolution can't see stub-ness; grep can't see danglers.) Sentinel grep is
  language-agnostic; import-resolution is Python-only (non-Python resolution deferred, flagged).
- **M1-L5 — Edge honesty = freeze-time machine check + review backstop; residual acknowledged
  (companion 3).** At FREEZE a `builds_against` dependent's test files may import ONLY `contracts/<id>/`,
  never the PROVIDER's owned impl paths (from `ownership:`). `contract_edges.edge_honesty(plan)` reuses
  `_extract_imports`/`_resolve_module`; a violation ⇒ the edge is really `depends_on`, reclassify before
  freeze. Backstop: a new `kata-review` attack surface → HOLD → deliberate reclassification.
  **Acknowledged residual (not hard-blockable):** import-surface honesty ≠ *semantic* honesty — a
  dependent importing only the contract surface can still depend at runtime on provider internals the
  contract under-specifies; the review backstop owns that judgment. Stated, not over-claimed.
- **M1-L6 — No layer-A/B float.** A contract/criterion/scope change is NEVER re-decomposition — it is the
  human-gated supersede (M1-L3). Frozen INTENT + LOCKED decisions untouched.
- **M1-L7 — Additive-BC everywhere.** Every surface no-ops when no `builds_against` edge is declared
  (0 exist today). No existing run acquires new blocking behavior.
- **M1-L8 — Contract immutability is machine-enforced between freeze and supersede (F4).**
  `contract_edges` re-verifies the **surface-hash** at each provider integration and the final gate:
  `surface_hash(contracts/<id>) != frozen pin` **without** a matching `Kata-Supersede: <id>@<newHash>`
  trailer (the git-durable authorization from M1-L3) ⇒ NEEDS_WORK (reuses the `detect_drift`/
  `approval_verdict` fail-closed pattern). A provider filling stub *bodies* leaves the surface unchanged
  (no trip); any *interface* edit trips unless authorized by a `Kata-Supersede:` trailer whose new hash
  matches the current surface — the same durable signal the final-gate F3 re-derivation audits for
  invalidation-completeness (M1-L3), so the authorize path and the audit path read one artifact.

- **M1-L9 — Fail-closed everywhere decision-code touches contracts (F7-extended, v2).**
  `surface_hash` RAISES on any parse-ERROR node in a `contracts/` file (no partial hash → no hidden
  interface change). `invalidation_set` RAISES on malformed `builds_against` (M1-L3). The final-gate
  invalidation re-derivation treats an absent/malformed/partial `Kata-Invalidated`/`Kata-Supersede`
  record as **NEEDS_WORK**, never a silent pass. **Stated residual (v2 #4/#5, not over-claimed):**
  **sentinel-absence ≠ implemented** — no machine gate proves a stub body was actually filled with real
  behavior; the real-behavior proof is the final-gate **full-suite re-run on the merged tree** (which
  exercises the dependent's tests against the provider's integrated body, `kata-orchestrate:525`) plus the
  M1-L5 review backstop for mock-shielded tests. The scans prove *structure* (no surviving sentinel, no
  dangling import, no un-superseded surface drift); *behavior* is proven by the existing green gate.

## Phasing (v2 #6 — the milestone is split; the float lands LAST)

Two HOLDs converged on "M1 is a multi-milestone program." It is delivered as three phases; **the frontier
float clause (the behavior change) ships only in P2, after its safety substrate is built and gated:**

- **M1-P0 — the `contract_edges` engine (pure, tested, NO wiring).** `surface_hash` (narrowed extractor,
  fail-closed), `invert`, `invalidation_set` (raise-on-malformed), `surviving_stubs` (sentinel +
  dangling-import), `edge_honesty`. Self-contained; adversarially reviewed as built code. No behavioral
  change to any run (nothing calls it yet). **This is the foundation and lands first.**
- **M1-P1 — durable substrate.** `Kata-Invalidated:` + `Kata-Supersede:` commit-trailer parsing;
  `kata_restore.parse_plan_tasks` unions `builds_against` keys; `collect_integrated_tasks` subtracts
  `Kata-Invalidated:` ids. Restore-correctness tests (lost-run re-dispatch). Still no float — additive,
  BC.
- **M1-P2 — wiring + the float.** The `builds_against` schema in `kata-plan/RUBRIC.md`; the
  dispatchable-at-freeze clause (`kata-orchestrate:211,481`); the supersede enumerate+trailer+route
  (`:507-509`); the final-gate independent re-derivation + surviving-stub + surface-drift checks
  (`:525-540`); the `kata-review` edge-honesty surface. Re-gated on its own before merge. **Only here does
  a contract-only dependent actually dispatch early** — and only with every companion live.

Each phase is its own freeze→build→gate cycle. P0 is buildable now against this DESIGN; P1/P2 re-freeze
their own PLAN slices as they come.

## Companions ↔ critic + freeze-gate findings (coverage this DESIGN satisfies)

| Finding | Covered by |
|---|---|
| doctrine #1 vacuous gate via leaking stubs | M1-L4 content-decidable sentinel + dangling-import scan |
| doctrine #2 supersede strands in-flight consumers | M1-L3 durable+re-derived invalidation + M1-L8 drift gate |
| doctrine #3 builds_against honor-system | M1-L5 machine edge-honesty + review |
| gate F1 scan tested location | M1-L4 sentinel content check |
| gate F2 ownership collision | M1-L4 provider-owns-contract (one writer) |
| gate F3 unenforced BLOCK | M1-L3 independent final-gate re-derivation, fail-closed |
| gate F4 un-superseded drift | M1-L8 surface-hash re-verification |
| gate F5 restore re-ships invalidated | M1-L3 `.kata/invalidated.json` subtracted on restore |
| gate F6 whole-dir hash | M1-L1 one-contract-per-subdir |
| gate F7 silent-permissive set | M1-L3 `invalidation_set` RAISES on malformed |

## Change-map (per phase — see PLAN)

| Surface | File | Change | Kind |
|---|---|---|---|
| Engine (new) | `tools/contract_edges.py` (+tests) | `surface_hash`, `invert`, `invalidation_set` (raise-on-malformed), `surviving_stubs`, `edge_honesty`, drift re-verify | **code** |
| Restore | `tools/kata_restore.py` | union `builds_against` keys; subtract `.kata/invalidated.json` from integrated (+tests) | **code** |
| Schema | `skills/plan/kata-plan/RUBRIC.md` | `builds_against:` + provider-owned `contracts/<id>/` + sentinel + retirement obligation | prose |
| Frontier | `skills/coordinate/kata-orchestrate/SKILL.md:211,481` | dispatchable-at-freeze clause | prose |
| Supersede + gates | `skills/coordinate/kata-orchestrate/SKILL.md:507-509,525-540` | enumerate+durable-record+route; final-gate independent re-derivation + surviving-stub + surface-drift checks, fail-closed | prose |
| Edge honesty | `skills/evaluate/kata-review/RUBRIC.md` | new attack surface | prose |

## Acceptance criteria

1. `validate_skills` 0/0; README in sync; edited skills semver-bumped.
2. `pytest` green + new tests, each code-bearing change **mutation-proven**:
   parse_plan_tasks unions `builds_against` (restore under-dispatch guard) + subtracts `invalidated.json`;
   `surface_hash` stable across body-fill, changes on interface edit + rename; `invert`/`invalidation_set`
   correctness incl. **RAISE on malformed** + empty-well-formed BC; `surviving_stubs` catches a surviving
   sentinel AND a dangling import, passes when retired; `edge_honesty` flags an impl-import + passes a
   contract-only dependent; the final-gate independent re-derivation returns NEEDS_WORK when a supersede
   touched a contract with no covering record.
3. **BC:** a run with no `builds_against` edge is byte-for-byte unchanged (parser, frontier, supersede,
   final gate) — explicit BC tests.
4. **Restore:** a crash mid-invalidation re-dispatches the correct set (integrated-but-invalidated task
   re-opened via `.kata/invalidated.json`) — proven against `kata_restore` tests.
5. Snyk medium+ 0 on `contract_edges.py` + `kata_restore.py` (or documented-acceptance).
6. **Re-gate:** the adversarial freeze-gate (`kata-review`, fresh context) on THIS revised DESIGN → SHIP
   before the PLAN freezes. Plus a fresh-context adversarial review of the built invalidation + drift-gate
   logic (the highest-risk pieces) at closeout.

## Out of scope (staged — L9)

M4 (inline evaluator/reroll — consumes M1 edges + F5/F3 substrate), M2 (shadow tasks), M3 (`partition_gate.py`,
own review). Language-agnostic import-resolution for the stub/honesty scans (Python/tree-sitter only now,
flagged; sentinel grep is already language-agnostic). This spec is M1 only.
