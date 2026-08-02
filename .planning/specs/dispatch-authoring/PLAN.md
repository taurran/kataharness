---
title: "dispatch-authoring — PLAN (KH-T13 dispatch roles + KH-B42 gate rubric)"
status: frozen
spec: dispatch-authoring
design: .planning/specs/dispatch-authoring/DESIGN.md
ownership:
  T1: [tools/kata_roles.py, tools/kata_dispatch.py, tools/tests/test_kata_roles.py, tools/tests/test_kata_dispatch.py]
  T2: [protocol/authored-artifact-gate.md, protocol/config.md, protocol/escalation.md]
  T3: [skills/plan/kata-design-doc/SKILL.md, skills/plan/kata-plan-essential/SKILL.md, skills/plan/kata-plan-standard/SKILL.md, skills/plan/kata-plan-advanced/SKILL.md, skills/coordinate/kata-loop/SKILL.md]
  T4: [tools/tests/test_dispatch_authoring_smoke.py]
  T5: [.planning/DECISIONS.md, README.md, CHANGELOG.md]
waves:
  - [T1, T2]
  - [T3, T4]
  - [T5]
depends_on:
  T1: []
  T2: []
  T3: [T1, T2]
  T4: [T1]
  T5: [T3, T4]
tags:
  - kata/plan
  - dispatch-authoring
  - KH-T13
  - KH-B42
---

# dispatch-authoring — implementation PLAN

**Goal.** Wire DESIGN.md's LOCKED contract end-to-end (PD-1 — no stub, no unwired leg): the two new
`design-author`/`plan-author` roles in `tools/kata_roles.py`/`tools/kata_dispatch.py`, the new
`protocol/authored-artifact-gate.md` rubric plus its `protocol/config.md`/`protocol/escalation.md`
cross-references, the dispatch instruction landed in the four authoring skills + `kata-loop`, an
end-to-end stub-runner proof, and the durable record. Every existing role, payload shape, and
escalation `kind` stays byte-unchanged (DESIGN §6).

## Global constraints (every task)

- **Source of truth:** `.planning/specs/dispatch-authoring/DESIGN.md` (this spec's own DESIGN, itself
  gated under KH-B42 before this PLAN was written). Workers MUST NOT re-decide, weaken, or extend a
  section DESIGN marks resolved (§4/§5/§6); a discovered conflict is an escalation
  (`protocol/escalation.md`), never a silent re-decide.
- **DISJOINT file ownership is absolute** — a worker never touches a file outside its `ownership:`
  list. A needed change to another task's file ⇒ escalate.
- **Workers NEVER run git.** The conductor is the sole main-tree git writer (DESIGN §6); workers build
  in isolated worktrees and report; the conductor stages/commits.
- **Per-task gate (every task, default-FAIL):** the task ends only with (a) its own tests/verify
  command green and (b) `ruff` clean on its owned Python files. Prose-only tasks (T2/T3/T5) substitute
  `uv run python tools/validate_skills.py` green + a read-back conformance check against the DESIGN
  section cited in their acceptance.
- **Semver bump-on-modify** (`docs/STANDARDS.md` §3): every modified `SKILL.md` bumps MINOR (new
  capability, non-breaking) — see T3.
- **Additive only:** no existing frozen line is rewritten; supersede-never-rewrite. BC acceptance in
  T1 includes "existing tests pass unchanged."

---

## Wave 1 (parallel — disjoint files, no cross-dependencies)

### T1 — engine: `kata_roles.py` + `kata_dispatch.py` role/payload additions
**owns:** `tools/kata_roles.py`, `tools/kata_dispatch.py`, `tools/tests/test_kata_roles.py`,
`tools/tests/test_kata_dispatch.py`
**depends_on:** []
**action (DESIGN §4.1/§4.3):**
1. `tools/kata_roles.py:33` — add `"design-author"` and `"plan-author"` to `ROLE_GROUPS`. Do **not**
   add either to `HOST_ONLY_ROLES` (`:41`).
2. `tools/kata_dispatch.py:263-313` — add two new `normalize()` branches (placed alongside the
   existing `validator`/`evaluator`/`researcher` branches, **before** the `coder`/`orchestrator`
   catch-all so the two new roles never fall through it):
   - `design-author` → requires `designPath` (non-empty str, else raise — default-FAIL, mirroring the
     `validator` missing-verdict raise at `:278-281`); requires `verdict` ∈
     `{"ready", "needs-rework"}` (else raise); `deviations` optional, defaults to `[]`.
   - `plan-author` → identical shape with `planPath` in place of `designPath`.
3. No change to `build_brief`, `dispatch`, `codex_command`, `kiro_command`, `_COMMAND_BUILDERS`, or any
   existing `normalize()` branch — the two new roles use the existing `sandbox="write"` path exactly
   as `coder` does today.
**tests (same task, TDD, write first):**
- `ROLE_GROUPS == frozenset({"coder","validator","researcher","orchestrator","evaluator","design-author","plan-author"})`.
- `HOST_ONLY_ROLES` unchanged; `resolve_roles({"design-author": {"platform": "codex"}}, ["codex"])`
  resolves without raising; the same call with `confirmed_platforms=[]` raises `ValueError`
  ("not confirmed") — proves no special-casing was added that bypasses the existing confirm check.
- `normalize("design-author", '{"designPath": "DESIGN.md", "verdict": "ready"}')` returns
  `{"designPath": "DESIGN.md", "verdict": "ready", "deviations": []}`.
- `normalize("design-author", '{"verdict": "ready"}')` (missing `designPath`) raises `ValueError`.
- `normalize("design-author", '{"designPath": "x", "verdict": "sideways"}')` (bad verdict) raises
  `ValueError`.
- The same three assertions mirrored for `"plan-author"`/`planPath`.
- `build_brief("t1", "design-author", "claude", model="m", objective="o", result_path="R",
  sandbox="write")` succeeds (role validation passes; no `ValueError: unknown role`).
- **Every pre-existing test in both files stays green, unmodified** (BC — no existing role touched).
**verify:** `cd tools && uv run pytest tests/test_kata_roles.py tests/test_kata_dispatch.py -q`
**acceptance:**
- All new tests above pass; full pre-existing suite in both files passes unchanged.
- `git diff` (conductor-verified) shows only additive hunks — no existing line in either module edited.
- `ruff` clean on both owned `.py` files.

### T2 — protocol layer: the B42 rubric + its two cross-references
**owns:** `protocol/authored-artifact-gate.md` (NEW), `protocol/config.md`, `protocol/escalation.md`
**depends_on:** []
**action (DESIGN §3):**
1. `protocol/authored-artifact-gate.md` (NEW) — the KH-B42 rubric verbatim per DESIGN §3.3/§3.4/§3.5:
   the six-row table (SCOPE · CLAIM vs ARTIFACT · CITATIONS RESOLVE · NO UNCITED REUSE CLAIM ·
   DEVIATIONS CONFIRMED · NO FROZEN INVARIANT RETIRED), each row's check/evidence/FAIL-shape/
   mechanical-or-judgment split, the §3.4 honesty note (do not overstate enforcement, citing
   `protocol/orchestration.md:58-64`'s own posture as the model to follow), and the §3.5 note that one
   table covers both `DESIGN.md` and `PLAN.md` gates. Follow the `protocol/reuse-claims.md` file shape
   (Purpose / the guard / a table / producer sites) — same genre of document, same house style.
2. `protocol/config.md:32` — the `roles` schema row's role enum
   (`coder|validator|researcher|orchestrator|evaluator`) gains `|design-author|plan-author`; add one
   sentence per new role naming its payload shape (pointer to `tools/kata_dispatch.py` `normalize()`,
   not a re-statement).
3. `protocol/escalation.md:78-80` — tighten the existing "Planner-workers... dispatched during the
   freeze stage" sentence to name `design-author`/`plan-author` explicitly by role string, and add one
   sentence for the `human-required` path (DESIGN §4.4): a genuinely unresolved ledger branch raises
   the **existing** `human-required` kind (`protocol/escalation.md:10`) — no new `kind` value.
**acceptance:**
- `protocol/authored-artifact-gate.md` exists; its six rows are traceable one-to-one to DESIGN §3.3's
  table (a reader diffing them finds no divergence); each row states mechanical vs. judgment.
- `protocol/config.md`'s `roles` row lists all seven role names.
- `protocol/escalation.md`'s `kind` enum (`orchestrator-resolvable | research-needed | human-required |
  advice-requested`) is **unchanged** — grep confirms exactly four values, no fifth added.
- `uv run python tools/validate_skills.py` still green (protocol files aren't skills; confirms no
  collateral breakage).
**verify:** `uv run python tools/validate_skills.py`

---

## Wave 2 (after wave 1)

### T3 — skill prose: the four authoring skills + `kata-loop`
**owns:** `skills/plan/kata-design-doc/SKILL.md`, `skills/plan/kata-plan-essential/SKILL.md`,
`skills/plan/kata-plan-standard/SKILL.md`, `skills/plan/kata-plan-advanced/SKILL.md`,
`skills/coordinate/kata-loop/SKILL.md`
**depends_on:** [T1, T2]
**action (DESIGN §4.2/§4.4, per file):**
1. **`kata-design-doc`** (0.2.0→0.3.0): Precondition section (`:30-33`) gains the dispatch instruction
   — once the grill ledger converges, a conductor session dispatches this skill as role
   `design-author` (citing `tools/kata_dispatch.py:42`/`:199`) rather than running it in-context. Add
   the two-part output contract (write `DESIGN.md` to the brief's one `owned_files` path + emit/write
   the small completion JSON per DESIGN §4.3's shape) and the escalate-not-decide instruction for a
   genuinely unresolved branch (raise `human-required` per `protocol/escalation.md`, replacing the
   current "return to grilling" phrasing at `:26-28` with the dispatched-worker-correct version — the
   conductor is the one who "returns to grilling" on the worker's behalf). Output section (`:66-68`)
   gains the parallel instruction for handing off to `plan-author`.
2. **`kata-plan-essential`/`-standard`/`-advanced`** (0.2.0→0.3.0 each): the mirrored Precondition
   instruction — once `DESIGN.md` is frozen, the conductor dispatches the appropriate tier skill as
   role `plan-author`; the same two-part output contract and escalate-not-decide instruction, scoped to
   a plan-level unresolved question.
3. **`kata-loop`** (0.1.0→0.2.0): the step-2 preamble's "grill → freeze → execute" line
   (`:70-75`) gains one clause naming what "freeze" now is (the `design-author` then `plan-author`
   dispatch) — the surrounding text is otherwise unchanged.
**acceptance:**
- All 5 files bump MINOR per `docs/STANDARDS.md` §3.
- Each of the 4 authoring skills' body states, traceably to DESIGN §4.2, that a conductor dispatches it
  as its named role rather than running it in-context, once its existing precondition is met.
- Each of the 4 skills states the two-part output contract and the escalate-via-`human-required`
  instruction, citing `protocol/escalation.md`.
- `kata-loop`'s diff is exactly the one added clause — no other line in the file changes.
- `uv run python tools/validate_skills.py` green, same skill **count** as the pre-task baseline (no
  new skill files are added by this task — only edits to five existing ones).
**verify:** `uv run python tools/validate_skills.py`

### T4 — end-to-end stub-runner proof
**owns:** `tools/tests/test_dispatch_authoring_smoke.py` (NEW)
**depends_on:** [T1]
**action:** A new test file (kept separate from T1's `test_kata_roles.py`/`test_kata_dispatch.py` to
avoid file-ownership collision) proving the whole chain round-trips using the injectable stub runner
(`tools/kata_dispatch.py:191-196`'s seam — the same seam already proven for `validator`→codex,
`.planning/DECISIONS.md:1032-1033`):
1. `resolve_roles({"design-author": {"platform": "codex"}}, ["codex"]) → build_brief(...,
   sandbox="write") → dispatch(brief, worktree, runner=stub)` with a stub that returns
   `{"designPath": "DESIGN.md", "verdict": "ready"}` yields a `completed` envelope whose
   `payload["designPath"] == "DESIGN.md"`.
2. The same round trip for `plan-author`/`planPath`.
3. A stub returning malformed JSON (missing `designPath`) yields a `failed` envelope via `dispatch()`'s
   existing catch (`tools/kata_dispatch.py:239-248`) — **no new code path is exercised**, proving T1
   added no special-casing that bypasses the existing failure handling.
**acceptance:**
- All three round trips pass against the stub runner; no live CLI/network call is made.
- The new file does not modify `test_kata_roles.py` or `test_kata_dispatch.py`.
**verify:** `cd tools && uv run pytest tests/test_dispatch_authoring_smoke.py -q`

---

## Wave 3 (after wave 2)

### T5 — records
**owns:** `.planning/DECISIONS.md`, `README.md`, `CHANGELOG.md`
**depends_on:** [T3, T4]
**action:**
1. `.planning/DECISIONS.md`: append the next free D-number (**verify the tail is still unused at write
   time** — D167 was the highest entry as of this PLAN's authoring) recording KH-T13 (dispatch
   design/plan as roles) and KH-B42 (the gate rubric) as one entry: the two new roles + their payload
   shapes, the new `protocol/authored-artifact-gate.md` contract, and the BC guarantees (§6). Cite
   `.planning/TASKS-ARCHITECTURE-2026-07-26.md` (KH-T13/KH-B42 sections) and this spec's
   `DESIGN.md`/`PLAN.md` paths — do not re-state the reasoning those documents already carry.
2. `README.md`: skill-index entries for the 4 touched skills reflect their new version numbers
   (mechanical, `validate_skills.py --write`-regenerated column); hand-author the "Use" column note for
   the dispatch behavior on `kata-design-doc` and the three `kata-plan-<tier>` rows.
3. `CHANGELOG.md`: an `[Unreleased]` entry naming the two new roles, the two `normalize()` payload
   shapes, the new `protocol/authored-artifact-gate.md` file, and the version-bumped skill list —
   labeled honestly per DESIGN §7 (stub-proven, not yet live-run against a real platform).
**acceptance:**
- D-record number verified unused at write time; entry cites the source documents rather than
  re-deriving them.
- `uv run python tools/validate_skills.py` README-sync check green after the index write.
- `CHANGELOG.md` lists every touched skill with old→new versions matching T3's bump list.
**verify:** `uv run python tools/validate_skills.py`

---

## Integration & gate (conductor — sole git writer)

1. Merge order: wave 1 (T1 ∥ T2, disjoint) → wave 2 (T3 ∥ T4, disjoint) → T5; `cd tools && uv sync`.
2. Full gate on the integration branch: `uv run pytest -q` all-pass (existing suite + T1's new tests +
   T4's smoke file) · `uv run python validate_skills.py` green at the same skill count as baseline ·
   `ruff` clean · Snyk medium+ 0 on `tools/kata_roles.py`/`tools/kata_dispatch.py`/T4's new file.
3. **B42 dogfoods itself (DESIGN §1's framing):** before writing this very DESIGN.md/PLAN.md into the
   main tree, the conductor applies `protocol/authored-artifact-gate.md` (T2's own output) to them —
   the six rows, against the citations in this PLAN and DESIGN.md. This is the first live exercise of
   the rubric the build itself defines; note the result honestly (stub-scope caveat does not apply
   here — this gate check is real, not simulated) rather than skipping it as "the rubric doesn't exist
   yet to gate its own design."
4. Standing adversarial `kata-review` (contract-bearing build): attack the `HOST_ONLY_ROLES`
   non-membership claim, the `normalize()` required-field validation (missing/malformed
   `designPath`/`planPath`/`verdict`), the escalation `kind`-enum-unchanged claim, and every reuse
   claim in DESIGN §2 (re-verify each cited `file:line` independently).
5. Dispatch fresh-context `kata-evaluate` (no-write, default-FAIL) against this PLAN's acceptance
   criteria before "done" is claimed for any task.
