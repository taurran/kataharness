---
spec: freeze-float-m1
phase: M1-P2
title: wiring + THE FLOAT — builds_against schema, dispatchable-at-freeze, supersede route, final-gate re-derivation
status: frozen
created: 2026-07-02
revised: 2026-07-02 (v3+fixes — gate v1 HOLD folded; re-gate v2 HOLD folded; gate v3 SHIP-WITH-FIXES, all 7 fixes folded; FROZEN)
branch: freeze-float/m1-contract-edges
baseline: c2894ab (post-adval D139; pytest 2270/3 skip, validator 47/0/0, Snyk medium+ 0)
tags: [kata/freeze-float, plan, float, wiring]
---

# M1-P2 — wiring + the float (re-gated; the ONLY behavior change)

Grounded against the post-D139 tree (line anchors re-verified at c2894ab). **Only here does a
contract-only dependent actually dispatch early** — and only with every companion live (M1-L1..L9).
BC by construction (M1-L7): every surface no-ops when no `builds_against` edge is declared, which is
every run today. Built via the dogfooded loop (kata-orchestrate drives; the run executes the frozen
PRE-P2 skill text; edits land as owned files).

## Gate history
- **Gate v3 (2026-07-02): SHIP-WITH-FIXES — FROZEN after fold.** R1-R8/R10 verified genuinely closed
  (R1 empirically: NUL framing unbreakable — git refuses NUL in messages; a raw-object NUL truncates
  `%B`, which only REDUCES coverage, fail-closed). Fixes folded: R9 tag restored (the v3 fold had
  dropped it — DESIGN M1-L4 annotated); freeze-commit precondition (the R8 hard-fail depended on an
  unenforced plan-committed convention); mid-run supersede authorization requires hash-match; artifact
  carries all three check results; test-glob derived from pytest config where present; `__init__.py`
  sentinel-exempt; C1/C10 boundary test named.
- **Re-gate v2 (2026-07-02): HOLD** — R1 BLOCKER: the temporal-coverage clause was unimplementable
  from the flat `%B` line stream (`_scan_integration_commit_bodies` emits NO commit delimiters — "same
  commit" is unrecoverable; a positional heuristic is both deadlock-prone and exploitable one commit
  sideways). R2 HIGH: the dangler scan was under-determined (a `contracts/<id>/` without `__init__.py`
  fails every honest `from contracts.c1 import iface`). R3-R5 MED (post-supersede revert-to-pin
  wrong-green; exclude_dirs could unscan contract content; stub materialization had a verifier but no
  owner), R6-R10 LOW. 16/18 v1 findings verified genuinely closed. All folded in v3 (commit-delimited
  scan; base-module dangler semantics + `__init__.py` mandate; newest-supersede-only final surface;
  contracts-subtree exclusion immunity; orchestrator materializes at freeze).
- **Freeze-gate v1 (2026-07-02): HOLD** — 1 BLOCKER + 6 HIGH + 8 MED + 3 LOW. Headline: the T1↔T3
  trailer-placement contradiction deadlocked the compliant flow (F1) and defeated the locked
  crash-mid-invalidation guarantee (F2); the fix loop could ship unauthorized drift green (F3); the
  independence pattern lacked its artifact + evaluator leg (F4); the edge-honesty forbidden set
  contained the contract itself (F5); the cited dangler-scan reuse was structurally blind (F6);
  double-supersede was coverage-invisible (F7). All 18 folded below; **v2 rulings live in the DESIGN
  Amendment #2 (2026-07-02, pre-P2)**: trailer-at-route-time, whole-dir retirement OUT of M1 scope,
  `tools/contract_gate.py` as a sanctioned new decision-code module, `surviving_stubs` additive
  `exclude_dirs` param.

## The P2 gate OBLIGATIONS this plan discharges (DESIGN Phasing, adval D139)
(i) supersede-id cross-check (T1 step 3); (ii) vendored-tree exclusion via the engine's new
`exclude_dirs` (T1); (iii) `parse_supersede_trailers` raise PROPAGATES (T1 step 2, T3 item 5, named
no-catch test); (iv) dangling-import scan as NEW logic (T1 — the F6 fold; `_extract_imports` cannot
see danglers by construction); (v) `expand_ownership_paths` minus the contract dirs (T1 + T3 2(c),
the F5 fold).

## Ownership (disjoint) + DAG

```yaml
ownership:
  T1: [tools/contract_gate.py, tools/tests/test_contract_gate.py, tools/contract_edges.py, tools/tests/test_contract_edges.py]
  T2: [skills/plan/kata-plan/RUBRIC.md]
  T3: [skills/coordinate/kata-orchestrate/SKILL.md]
  T4: [skills/evaluate/kata-review/RUBRIC.md]
  T5: [skills/evaluate/kata-evaluate/SKILL.md]
waves:
  wave1: [T1, T2, T4]
  wave2: [T3, T5]
depends_on:
  T3: [T1]
  T5: [T1]
```

T6 (closeout, conductor-owned, F16): README index regen (`validate_skills --write`), CHANGELOG entry,
DESIGN Phasing P2→DONE, D140 record.

## Durable-trailer placement — the ONE canonical rule (F1/F2 fold; DESIGN Amendment #2)

**`Kata-Invalidated: <task-id>` trailers for EVERY routed member of `invalidation_set(C)` — both
in-flight-aborted AND integrated-re-opened — are written AT ROUTE TIME, on the SUPERSEDING integration
commit itself** (the same commit that carries `Kata-Supersede: <id>@<newHash>`). Consequences, both
locked-in: (a) a crash at ANY point after the supersede commit re-dispatches every routed member —
`collect_integrated_tasks` subtracts them (restores DESIGN acceptance 4 / the F5 lost-run guarantee);
(b) the T1 coverage check is satisfiable by every compliant execution (kills the v1 deadlock), stays
strict set-membership, and gains the temporal clause (F7): **a covering invalidation event must be at
the same commit as, or newer than, the newest `Kata-Supersede:` for that contract** — a stale round-1
trailer cannot cover a round-2 supersede.

## T1 — `tools/contract_gate.py` + engine param (code-bearing)

The final-gate re-derivation as mutation-provable decision code (D136; sanctioned by DESIGN Amendment
#2 — F9). Imports `contract_edges` (pure) + `kata_restore` parsers (git). All fail-closed (M1-L9).

**Engine change (additive-BC, F8):** `contract_edges.surviving_stubs` gains
`exclude_dirs: tuple[str, ...] = ()` — a path is skipped iff an excluded component appears
**BEFORE the first `contracts` component** in its parts (a vendored tree that CONTAINS a contracts
dir); components at-or-under `contracts/` are NEVER excluded (R4 — a contract id literally named
`vendor`, or a `vendor/` subdir inside a contract, stays scanned; exclusion must never fail-open the
sentinel invariant). Default `()` = current behavior byte-for-byte (BC test). `expand_ownership_paths`
`exclude_prefixes` are posix-normalized WITH a trailing slash before matching (R10 —
`contracts/C1/` never matches `contracts/C10/...`).

`contract_gate` functions:
- `pinned_contracts(builds_against) -> dict[str, str]` — `{contractId: pinnedHash}`; RAISES on
  malformed edges; RAISES on conflicting pins for one id (one contract, one pin).
- `_scan_integration_commits(repo_root, integration_branch, plan_path) -> list[list[str]]` —
  **commit-DELIMITED** bounded scan (R1: `%B` alone is a flat undelimited stream — "same commit" is
  unrecoverable from it): `git log --format=%x00%H%n%B`, split on the NUL sentinel ⇒ per-commit body
  line-lists, newest-first; same fork-point bounding as `_scan_integration_commit_bodies`. **Gate
  semantics: an unresolvable fork-point RAISES** (R8 — the restore parser's degraded unbounded
  fallback is fine for over-dispatch but NOT for the audit: prior-run trailers for reused contract
  ids would corrupt coverage); a git error RAISES.
- `parse_trailer_events(repo_root, integration_branch, plan_path) -> list[tuple[int, str, str, str]]`
  — `(commit_index, kind, id, hash|"")` events (kind ∈ {"supersede","invalidated"}), commit_index 0 =
  newest, from `_scan_integration_commits`; hashes lowercased + malformed-looking trailer lines
  surfaced via the P1 prefix-detector NOTEs (R7 parity); raises propagate (never a permissive `[]`).
- `dangling_contract_imports(dependent_files, repo_root) -> list[dict]` — **NEW logic, not a reuse**
  (F6): `_extract_imports` emits edges only for imports that RESOLVE, so a dangler is invisible to it
  by construction. Mechanism: tree-sitter-parse each dependent file (reuse the parser + import-node
  walk PATTERN from `graph_gen`), extract RAW module names, map each through
  `graph_gen._module_to_path` candidates; if ANY candidate path starts with a `contracts/` prefix
  (the import targets the contract namespace) AND NO candidate exists on disk ⇒
  `{"file":…, "import":…}`. Unreadable dependent file ⇒ RAISE.
  **Existence is decided at the BASE-MODULE level (R2):** only the raw module name's own candidates
  are checked — from-import NAMES are never expanded to paths (expanding `from contracts.c1 import
  SomeClass` to `contracts/c1/SomeClass.py` would false-flag the most common import form). Residual
  (documented, suite-backstopped): a deleted submodule behind a surviving `__init__.py` referenced as
  `from contracts.c1 import iface` is invisible to the scan — the full-suite re-run's ImportError is
  the behavioral backstop; `from contracts.c1.iface import X` (raw module names the file) IS caught.
  T2's `__init__.py` mandate makes the base-module candidates well-defined.
- `expand_ownership_paths(ownership_entry, repo_root, exclude_prefixes=()) -> list[str]` — expand dir
  entries to `.py` files (recursive), pass through file entries, missing path ⇒ RAISE. The T3 2(c)
  caller passes `exclude_prefixes=("contracts/",)`-resolved contract dirs so **the provider-owned
  contract itself is never in the edge-honesty forbidden set** (F5 — the honest contract-only
  dependent must pass).
- `verify_contract_gate(repo_root, integration_branch, builds_against, plan_path) -> dict` — the
  re-derivation (M1-L3/L8 + obligations i/iii; `dependent_files_by_task` param DROPPED — F11; the
  dangling scan is invoked separately with explicit file lists):
  1. `pins = pinned_contracts(builds_against)`; well-formed empty ⇒ `{"passed": True, "vacuous": True}` (BC).
  2. `events = parse_trailer_events(...)` and `supersedes = parse_supersede_trailers(...)` — a raise
     PROPAGATES (obligation iii; no catch anywhere in this module).
  3. **(i)** every supersede id ∈ `pins` else finding `unknown-supersede-id`.
  4. **Surface drift (M1-L8, R3):** a NEVER-superseded contract's `surface_hash` must == its pin; a
     SUPERSEDED contract's must == its NEWEST supersede hash — at the FINAL gate the pin branch is
     closed for superseded contracts (a provider reverting to the pre-supersede pin after dependents
     re-dispatched against the new surface is drift, not authorization). (The mid-run
     provider-integration re-verify keeps pin-OR-supersede — the routing window is legitimate there.)
     Else finding `unauthorized-surface-drift`. A missing/no-`.py` dir
     RAISES (whole-dir retirement is OUT of M1 scope — DESIGN Amendment #2/F10; the pinned dir must
     survive the run with bodies filled).
  5. **Invalidation coverage + temporal (M1-L3/F7, R1 — COMMIT granularity):** for each superseded
     C, every task in `contract_edges.invalidation_set(builds_against, C)` must have an `invalidated`
     event whose `commit_index` ≤ the `commit_index` of C's newest `supersede` event (newest-first:
     lower index = newer; equal = the same commit — intra-body line order is IRRELEVANT); else finding
     `invalidation-coverage-gap`.
  6. Returns `{"passed": bool, "vacuous": bool, "findings": [{kind, detail}...]}` — never None/empty
     on failure; every failure is a named finding.
- `write_contract_gate(kata_dir, verdict) -> Path` — emits **`.kata/contract-gate.json`** (F4: the
  durable artifact the evaluator's independence leg reads; schema = the verify dict + utc + branch
  **+ the step-5 companion results: `surviving_stubs: [paths]` and `danglers: [dicts]`** (gate-v3 F4
  — the artifact must prove ALL THREE final-gate contract checks ran, not just the re-derivation;
  they are computed at the same step, so the caller passes them in).

**Tests (TDD; every function mutation-proven):** vacuous-BC empty edges; unknown-supersede-id;
conflicting pins raise; drift-without-supersede fails; drift-with-newest-supersede passes; body-fill
passes; coverage-gap fails; full-coverage-at-route-time passes; **double-supersede with only round-1
invalidation fails (temporal, F7)**; supersede-parser/scan raise propagates (no-catch); dangler caught
(deleted contract file, import remains); resolving contract import clean; non-contract dangling import
ignored; unreadable dependent raises; ownership-dir expansion + contract-dir exclusion (**honest
contract-only dependent yields empty forbidden-set violation list — F5**); missing ownership path
raises; `surviving_stubs` exclude_dirs skips a `.venv/`-nested sentinel + does NOT skip
`contracts/vendor/` content (R4) + default-() BC; **same-commit coverage passes with the invalidated
line BELOW the supersede line in one body (R1a — intra-body order irrelevant)**; **invalidation in a
separate immediately-OLDER commit fails (R1b)**; `_scan_integration_commits` raises on unresolvable
fork-point (R8) and on git error; dangler: `from contracts.c1 import iface` with `iface.py` +
`__init__.py` present ⇒ clean (R2a); deleted-submodule-behind-`__init__.py` documented-residual
fixture (R2b — scan clean, suite backstop noted); artifact round-trip carrying all three check results (gate-v3 F4); `expand_ownership_paths`
prefix-boundary: `contracts/C1/` never excludes `contracts/C10/...` (gate-v3 F7). Real-git fixtures
reuse the `test_kata_restore.py` helper pattern.

## T2 — `kata-plan/RUBRIC.md` — the `builds_against` schema (prose)

Extend the frontmatter Structure block (`:29-35`):

```yaml
builds_against: { D1: ["C1@<64-hex surfaceHash>"] }   # dependent -> contract pins (OPTIONAL)
```

Authoring rules (M1-L1/L4/L5): one contract = one `contracts/<id>/` subdir **containing an
`__init__.py`** (R2 — makes the import namespace and the dangler scan's base-module candidates
well-defined), in the PROVIDER task's `ownership:` (the dependent NEVER writes it). **Stub materialization (F18): the plan-guardian
(orchestrator) commits the contract interface + stub bodies (each bearing `# KATA-CONTRACT-STUB`) to
the integration branch AT FREEZE, before any worker exists** — dependent worktrees fork with the stubs
present; the provider task fills real behavior behind the same import paths in its own worktree,
**deleting the sentinel lines (sentinel retirement — the only M1 retirement; whole-dir deletion is out
of scope, Amendment #2)**. The pin is `contract_edges.surface_hash(contracts/<id>)` computed at freeze **by the plan-guardian
(orchestrator), who records it in the edge and commits the frozen PLAN to the integration branch in
the same freeze step** (gate-v3 F2 — the named writer; the final gate's scan bound depends on this
commit). **The mandated `__init__.py` is sentinel-EXEMPT** (gate-v3 F6 — it may be empty/namespace
glue; requiring a sentinel there with no body to fill would make retirement ambiguous). A dependent's tests import ONLY `contracts/<id>/`, never
provider impl paths (edge honesty; violation ⇒ the edge is really `depends_on`, reclassify before
freeze). Constants/type-aliases/`__all__` are NOT machine-pinned (M1-L1 residual) — flag for
[[kata-review]]. Shared RUBRIC ⇒ no peer bump.

## T3 — `kata-orchestrate/SKILL.md` (prose; bump 0.4.3 → 0.5.0 MINOR)

Anchors at c2894ab. Every edit conditioned on `builds_against` present (BC). **Constraints:** never
use the substring "delivery" (sprint-blind conformance test, F15). **Step-insertion rule (F13):** the
new final-gate step renumbers existing steps — re-anchor ALL internal cross-references in the same
edit (`:490` role-table "step 6", `:549` + `:568` "before step 4", `:605` "step 6 below"); grep the
file for `step [0-9]` before closing the task.

1. **Frontier clause** (`:215-219`): dispatchable iff (all `depends_on` integrated) ∧ (owned files
   disjoint) — ADD: "∧ its `builds_against` edges are satisfied at freeze (they never wait on provider
   integration): a dependent whose only unmet edges are `builds_against` dispatches at freeze, in
   parallel with its provider." Mirror one clause into LD6 (`:496`).
2. **Freeze-time companion checks** (new precondition 6): when the plan declares `builds_against` —
   (a) every referenced `contracts/<id>/` exists on the integration branch with provider ownership +
   sentinel present + an `__init__.py` (T2 mandate, R2); **if absent, the ORCHESTRATOR materializes
   it** (R5: author the interface + sentinel stubs from the plan's contract spec, commit to the
   integration branch — the same commit authority as its step-5 integration commits) — STOP only if
   the plan carries no authorable interface spec; **and the frozen PLAN itself (with its recorded
   pins) is verified COMMITTED on the integration branch** (the 6(a) materialization commit may carry
   it) — else STOP at freeze (gate-v3 F2: the final gate's bounded scan hard-fails on an unresolvable
   plan fork-point; this check makes the freeze commit the perfect scan bound and costs nothing); (b) `surface_hash` of each contract dir equals
   the plan's pin (stale ⇒ STOP, re-freeze); (c) `edge_honesty(dependent test files,
   expand_ownership_paths(provider ownership, exclude the contract dirs — F5), repo_root)` is empty —
   a violation ⇒ the edge is really `depends_on`: STOP, reclassify. All three fail-closed.
3. **Provider-integration re-verify** (task gate step 3, near the lane check): when a PROVIDER task
   integrates, re-run `surface_hash` on its contract dir(s); pin mismatch is authorized ONLY by a
   `Kata-Supersede: <id>@<newHash>` trailer **whose `<newHash>` equals the re-computed
   `surface_hash`** (gate-v3 F3 — a stale round-1 trailer must not authorize arbitrary later drift),
   **on the candidate integration commit itself or in prior bounded history** (F14 — the evaluation
   point is candidate-commit-body ∪ scan); unauthorized ⇒
   BLOCK the integration, escalate. Body-fill (sentinel retired, surface unchanged) passes untouched.
4. **Supersede route — applies to ANY deliberate contract-surface supersede regardless of which path
   produced it (GROUND fold `:518-530`, a human-required resolution, or a fix-loop re-plan — F12; one
   canonical statement, cross-referenced from the other two anchors):** (a) enumerate
   `contract_edges.invalidation_set(builds_against, C)`; (b) write the DURABLE RECORD FIRST (F1/F2):
   the superseding integration commit carries `Kata-Supersede: <id>@<newHash>` AND a
   `Kata-Invalidated: <task-id>` line for EVERY member (both dispositions); (c) then route each member
   — in-flight ⇒ abort worktree ([[kata-worktree]] remove+prune; **abort failure ⇒ escalate
   human-required, never proceed-and-re-dispatch over a possibly-live worker — F17**) + re-dispatch
   against the new surface; integrated ⇒ force re-open via the fix loop (its re-integration commit
   carries `Kata-Task:` as normal — the invalidation record already exists at route time).
   **Dependent-file derivation (R6):** for the 2(c) honesty check, "dependent test files" = the files
   in the dependent task's `ownership:` matching the project's test convention (**derived from
   pytest config (`testpaths`/`python_files`) where present, defaulting to** `tests/` +
   `test_*.py` / `*_test.py` — M1-L5's locked scope is TEST files; a nonstandard convention that
   yields an EMPTY dependent-test set is surfaced to the [[kata-review]] backstop, never silently
   vacuous — gate-v3 F5); for the final-gate dangling scan,
   "dependent files" = ALL files in every `builds_against` task's `ownership:`.
5. **Final gate step** (`## Final gate`, new step after the artifact emit): when the plan declares
   `builds_against` — run `contract_gate.verify_contract_gate(...)` from the integration root, then
   `contract_gate.write_contract_gate(kata_dir, verdict)` (**the artifact is written even on pass —
   its ABSENCE is the evaluator's signal, F4**); run `surviving_stubs(root,
   exclude_dirs=(".venv","node_modules","vendor",".git"))` (zero sentinels) and
   `dangling_contract_imports(dependent files, root)` (zero danglers). ANY finding, ANY raise
   (including the supersede-parser git-error raise — propagate, never catch-and-continue), a
   surviving sentinel, or a dangler ⇒ NEEDS_WORK. No `builds_against` ⇒ silent no-op, no artifact
   (BC). **Sentinel-absence ≠ implemented** (M1-L9): real behavior is proven by the full-suite re-run.
6. **Fix-loop re-verification (F3):** in the fix loop's cheap deterministic gate AND the confirmation
   pass, when the plan declares `builds_against`, the contract checks (step 5's trio) are PART of the
   cheap gate — a fix-worker edit to any `contracts/<id>/` or dependent file re-runs them, so
   post-gate drift cannot ship green.

## T4 — `kata-review/RUBRIC.md` — edge-honesty attack surface (prose)

New attack surface (`:20+`): **contract-edge honesty** — for any run declaring `builds_against`: does
a dependent lean on provider INTERNALS the contract under-specifies (semantic honesty — the machine
check proves import-surface honesty only, M1-L5 residual)? Does any contract rely on a
constant/type-alias/`__all__` (NOT machine-pinned, M1-L1 residual)? Is a `builds_against` edge really
a `depends_on` in disguise (mock-shielded tests that would fail against the real body)? Shared RUBRIC
⇒ no peer bump.

## T5 — `kata-evaluate/SKILL.md` — the independence leg (prose; bump 0.2.1 → 0.3.0 MINOR; F4)

New rubric rule (the `.kata/iac.json` presence-pattern, mirrored): when the frozen PLAN declares
`builds_against`, `.kata/contract-gate.json` MUST be present, well-formed, and `passed: true` —
**absent, malformed, or failed ⇒ NEEDS_WORK** (an orchestrator that skipped the contract step cannot
pass; soundness never rests on orchestrator compliance, M1-L3). No `builds_against` in the plan ⇒ the
artifact's absence is a silent no-op (BC — mirrors the IaC no-op clause).

## Acceptance criteria (DESIGN §Acceptance, P2 slice)
1. `validate_skills` 0/0; README index regenerated; kata-orchestrate 0.5.0 + kata-evaluate 0.3.0.
2. pytest green; every T1 function mutation-proven; NEEDS_WORK-shaped findings proven for:
   supersede-with-no-coverage, STALE-ROUND coverage (F7), unknown-supersede-id, unauthorized drift,
   surviving sentinel (incl. exclude_dirs honored), dangling import.
3. **BC explicit:** no `builds_against` ⇒ byte-for-byte unchanged (frontier, preconditions, supersede
   route, final gate, fix loop, evaluate rule all no-op; `verify_contract_gate` vacuous pass;
   `surviving_stubs()` default-args behavior byte-identical — tested).
4. Snyk medium+ 0 on `contract_gate.py` + `contract_edges.py`.
5. Fresh-context adversarial RE-GATE on THIS v2 (HOLD→SHIP) before build; fresh-context adversarial
   sweep of built code + prose before the operator merge gate.

## Out of scope
M4/M2/M3 (staged, L9). Whole-dir contract retirement (Amendment #2 — needs a retirement-record design,
later milestone). Non-Python import-resolution for the scans (flagged residual). Recency-precise
invalidation subtraction (D138#2). RESULT.json security carrier (#17).
