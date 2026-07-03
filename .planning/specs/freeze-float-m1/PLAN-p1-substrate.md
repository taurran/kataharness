---
spec: freeze-float-m1
phase: M1-P1
title: durable trailer substrate — Kata-Invalidated/Kata-Supersede parsing + kata_restore union/subtract
status: frozen
created: 2026-07-02
branch: freeze-float/m1-contract-edges
tags: [kata/freeze-float, plan, restore, durability]
---

# M1-P1 — durable substrate (additive, BC, NO float)

Grounded against `tools/kata_restore.py` (read 2026-07-02). All changes are in `kata_restore.py` +
its tests. **No skill edits. No wiring of the float** (that is P2). BC by construction: every new surface
no-ops when no `builds_against` edge / no `Kata-Invalidated:` / no `Kata-Supersede:` trailer exists — which
is the case for every run today (grep-clean).

## Where the trailer parsing lives (D138 / grounding)
`kata_restore.py` — NOT a new `kata_supersede.py` (that name is taken by the unrelated install-domain
skill-fork resolver, stdlib/zero-git). `kata_restore.py` already owns `_KATA_TASK_RE` + the bounded git-body
scan, so the two new trailer regexes and their parsers sit beside it. `contract_edges.py` stays PURE (no git,
no subprocess) — the pure `invalidation_set` predicate there is consumed by the P2 final gate alongside these
parsers.

## Slice A — `parse_plan_tasks` unions `builds_against` keys (M1-L2, the one hard base-code fix)
- After the `waves:` union block, add: keys of `builds_against:` dict → `task_ids`. A contract-only dependent
  may appear only under `builds_against` in some plan shapes; unioning its keys guarantees it is never dropped
  from the restore re-dispatch set (M1-L2). `builds_against` absent / not-a-dict ⇒ no-op (BC).
- Tests: a PLAN whose only source of a task-id is `builds_against` yields that id (mutation: drop the union
  block → that test goes red); a PLAN with no `builds_against` yields the byte-identical set as today (BC).

## Slice B — `collect_integrated_tasks` subtracts `Kata-Invalidated:` (M1-L3 / F5)
- Extract the fork-point resolution + `git log --format=%B` scan into a private helper
  `_scan_integration_commit_bodies(repo_root, integration_branch, plan_path) -> list[str] | None`
  (returns body lines, `None` on git error). `collect_integrated_tasks` calls it and returns the SAME result
  as today when no `Kata-Invalidated:` trailer exists (BC — verified by the existing collect tests).
- New `_KATA_INVALIDATED_RE = ^\s*Kata-Invalidated:\s*(\S+)\s*$` (IGNORECASE, mirrors `_KATA_TASK_RE`).
- `collect_integrated_tasks` = `{Kata-Task ids}` **MINUS** `{Kata-Invalidated ids}`, from the one scan.
  **Set-based, over-dispatch-safe (D138):** a task integrated→invalidated→re-integrated bears both trailers
  and is subtracted ⇒ redundantly re-dispatched — the SAFE direction (D134/D135). Recency-precise subtraction
  is a deferred optimization, NOT a correctness requirement.
- Tests: an integrated task with a `Kata-Invalidated:` trailer is NOT in the integrated set (⇒ stays in the
  redispatch set via `compute_redispatch_set`); mutation (drop the subtract) → that test goes red; a run with
  no `Kata-Invalidated:` trailer returns the byte-identical integrated set (BC). Real-git fixture for the
  crash-mid-invalidation lost-run scenario.

## Slice C — `Kata-Supersede:` parser (provided in P1, CONSUMED by the P2 final gate)
- New `_KATA_SUPERSEDE_RE = ^\s*Kata-Supersede:\s*([A-Za-z0-9._-]+)@([0-9a-fA-F]{8,64})\s*$` (IGNORECASE on
  the key; hash normalized to **lowercase** in code so it matches `contract_edges._EDGE_RE`'s lowercase-hex
  pin — a case mismatch would silently fail the P2 re-derivation).
- New `parse_supersede_trailers(repo_root, integration_branch, plan_path=None) -> dict[str, str]` reusing
  `_scan_integration_commit_bodies`; returns `{contractId: newSurfaceHash}`, **most-recent-supersede wins**
  (git log is newest-first; keep the first occurrence per id). Empty ⇒ `{}` (no supersede this run, BC).
- NOT wired into any gate here (the final-gate re-derivation is P2). Provided + unit-tested so P2 consumes a
  proven parser.
- Tests: a single `Kata-Supersede: C1@<hash>` trailer parses to `{"C1": "<hash>"}`; an uppercase-hash trailer
  normalizes to lowercase; two supersedes of the same id keep the most-recent; no trailer ⇒ `{}`.

## Gate (P1 closeout)
- `validate_skills` 0/0 (no skill edits). `pytest` green + new tests; **each code-bearing change
  mutation-proven** (Slice A union, Slice B subtract). Snyk medium+ 0 on `kata_restore.py`.
- **BC explicit:** the full existing `kata_restore` suite passes unchanged (the helper extraction + subtract
  are no-ops without the new trailers).
- Fresh-context adversarial review of the built substrate (restore is recovery-path; highest-risk).

## Out of scope (P2)
The dispatchable-at-freeze frontier clause, the supersede enumerate+route at `kata-orchestrate:507-509`, the
final-gate independent re-derivation (consumes `parse_supersede_trailers` + `contract_edges.invalidation_set`
+ `Kata-Invalidated:` coverage), the surviving-stub dangling-import half, the `builds_against` schema in
`kata-plan/RUBRIC.md`, the `kata-review` edge-honesty surface. P2 is re-gated before merge.
