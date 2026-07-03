---
spec: freeze-float-m1
phase: M1-P0
title: contract_edges engine (pure, tested, NO wiring)
status: frozen
created: 2026-07-02
branch: freeze-float/m1-contract-edges
tags: [kata/freeze-float, plan, engine]
---

# M1-P0 — `tools/contract_edges.py` engine

Pure engine, **no wiring** (nothing calls it yet → zero behavioral change to any run, BC by
construction). Each function fail-closed per M1-L9. Built TDD; every function mutation-proven. Adversarial
review of the built engine at P0 closeout (not a design gate).

Edge grammar (M1-L1): `builds_against: { "<task>": [ "<contractId>@<surfaceHash>" ] }`.

## Slice A — `invert` + `invalidation_set` (pure, fail-closed)
- `invert(builds_against) -> {contractId: [task, ...]}` — invert the edge map. **RAISE `ValueError` on
  malformed** (not a dict; task key not str; value not a list; entry not a `str`; entry not matching the
  `<id>@<hash>` grammar). Only a well-formed empty `{}` returns `{}` (BC-vacuous).
- `invalidation_set(builds_against, changed_contract_id) -> [task, ...]` — tasks bound to that contract
  (sorted, deduped). Reuses `invert`; same raise-on-malformed.
- Tests: happy path (multi-task, multi-contract); empty `{}` → `{}`/`[]`; each malformed shape RAISES;
  a contract with no dependents → `[]`; changed-id not present → `[]`. Mutation: weaken the grammar check
  → a malformed-entry test goes red.

## Slice B — `surface_hash` (narrowed extractor, fail-closed)
- `surface_hash(contract_dir) -> str` — over every `.py` in the dir, extract the **narrowed surface**
  (M1-L1): exported function/method **signatures incl. return annotations + decorator lists** + top-level
  names. Normalize order; netstring length-prefix (D98); sha256. Reuse `graph_gen`'s tree-sitter parser;
  extend `_signature_of` to include the `return_type` field + decorators. **RAISE on any parse-ERROR node
  in a contract file** (M1-L9 — no partial hash).
- Tests: stable across a **body-fill** (same signatures, different body) → identical hash; changes on a
  **return-annotation** edit, a **decorator** add/remove, a **param** change, a **rename**; RAISES on an
  unparseable file. Mutation: drop the return-annotation from extraction → the return-annotation test goes
  red. Deferred-residual test: a module-**constant** change does NOT change the hash (documents the known
  gap, not a bug — the review backstop owns it).

## Slice C — `surviving_stubs` + `edge_honesty` (scans, fail-closed)
- `surviving_stubs(repo_root, sentinel="# KATA-CONTRACT-STUB") -> [path]` — sorted `contracts/` files
  still bearing the sentinel (language-agnostic content check). Empty ⇒ clean.
  **AMENDED (post P0-engine-review, #3):** the **dangling-import** half — a `builds_against` contract
  import that fails to resolve after retire-by-deletion — is **moved to M1-P2**, the final-gate wiring
  where the dependent file-set + merged integration tree exist (DESIGN M1-L4 already locates the combined
  sentinel+dangling scan there). P0 delivers the sentinel primitive only; the descope is recorded here
  and in the DESIGN Phasing, not silently taken.
- `edge_honesty(builds_against, ownership, repo_root) -> [violation]`
  **AMENDED (D138 Amendment #3):** built as the lowered primitive
  `edge_honesty(dependent_files, provider_paths, repo_root)` — the `builds_against→dependent-files` +
  `ownership→provider-paths` resolution lives in the P2 caller. A P2 builder wires the BUILT signature,
  not this line's shorthand. — for each `builds_against`
  dependent, a violation if any of its test files imports a path owned by the provider (from `ownership`)
  rather than only `contracts/<id>/`. Reuses `_extract_imports`/`_resolve_module`.
- Tests: surviving sentinel caught; retired ⇒ clean; a non-`contracts/` sentinel ignored; an impl-import
  dependent flagged; a contract-only dependent clean. Mutation on each. (Dangling-import tests move to
  P2 with that primitive — #3 amendment.)

## Gate (P0 closeout)
- `validate_skills` 0/0 (no skill edits in P0 — engine only); `pytest` green + new `test_contract_edges.py`;
  every function mutation-proven; Snyk medium+ 0 on `contract_edges.py`.
- **Adversarial review of the BUILT engine** (fresh context) — SHIP before P0 merges.
- BC: no skill/protocol/config touched; nothing calls the engine → every existing run byte-for-byte
  unchanged.

## Out of P0
Trailers + restore union (P1); schema + frontier float + gate wiring + review surface (P2). No wiring here.
