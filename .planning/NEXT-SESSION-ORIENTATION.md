# KataHarness — NEXT-SESSION ORIENTATION (2026-07-02 · two initiatives in flight · HELD at Freeze/Float M1-P0)

> Paste-ready, self-contained. You are a fresh coding-agent window resuming KataHarness. Read this top to bottom
> before touching anything. Two initiatives are in flight on **stacked branches**; nothing is broken; the operator
> has **HELD** further building. Your first job is to re-anchor and confirm state, not to start a build.

---

## 0. WHO / WHERE
- **Project:** KataHarness — a tool-agnostic, skills-based agent harness ("the Kata Loop") that one-shots complex
  coding tasks behind frozen plans + a fresh-context default-FAIL evaluator. Dir `C:\Dev\Projects\KataHarness`.
- **Git:** private remote `github.com/taurran/kataharness`.
- **You are the conductor:** you own the plan, the gates, and the merge. Real build work runs through subagents;
  the fresh-context adversarial sweep is non-negotiable.
- ⚠️ **IGNORE `C:\Dev\CLAUDE.md`** (it describes "Mise", an unrelated meal-planning app). Follow `AGENTS.md` + the
  repo's own `CLAUDE.md` only. ⚠️ The global `~/.claude/CLAUDE.md` Snyk block was softened this session to
  conditional/toolchain-aware — Snyk no longer hard-blocks a run when unavailable.

## 1. ★ BRANCH TOPOLOGY (read this twice — two initiatives are stacked)
```
master  653f501  (pre-hardening; the last thing actually merged is v0.1.x restore-hardening)
   └── hardening/kenjiri-lessons   ← Milestone 1 "Release Hardening"  ·  PR #4 OPEN (not merged)
          └── freeze-float/m1-contract-edges   ← Milestone 2 / Freeze-Float M1-P0  ·  CURRENT TIP (stacked)
```
- **Milestone 1 (`hardening/kenjiri-lessons`, PR #4 OPEN):** six field-verified fixes from the Kenjiri one-shot
  (F1–F6) + a tool-agnostic security gate. Done, reviewed, pushed; **awaiting operator merge.**
- **Freeze/Float M1-P0 (`freeze-float/m1-contract-edges`, current):** the pure `contract_edges` engine, stacked on
  the hardening substrate (it consumes Milestone 1's `footprint.file_content_hashes` + the PROGRESS heartbeat).
- **First action after green-check:** merge PR #4 to master, then **rebase `freeze-float/m1-contract-edges` onto
  master** (`git rebase master`), then continue. Doing this before P1 avoids a messy stacked history.

## 2. GREEN (at the freeze-float tip)
- `pytest 2219 passed / 3 skip` — run `-m "not integration"` (2 benchmark integration tests need `uv run pytest`
  over a temp clone → fail offline; NOT a regression). Baseline arc: 653f501=2177 → hardening=2190 → +engine=2219.
- `validate_skills` **47 / 0 / 0** · Snyk medium+ **0**.
- **Run tests via the repo venv from `tools/`:** `cd tools; uv run pytest tests -q -m "not integration"`;
  validator `uv run python validate_skills.py` (add `--write` to regen the README skill-index).

## 3. CONTEXT LOADING ORDER (what to read, in order — stay context-lean)
1. **This file** (you're in it) + `.planning/HANDOFF.md` (frontmatter + the ★2026-07-02 block + §2/§4).
2. `AGENTS.md` — the spine (plan-no-drift, default-FAIL, agnostic-via-adapters, two-way handoff, everything versioned).
   `CLAUDE.md` is a thin pointer to it.
3. **Milestone 1 (context for PR #4, if touching it):** `.planning/specs/kenjiri-lessons/{DESIGN,PLAN}.md` +
   `DECISIONS.md` **D137** (LOCKED L1–L10) + `LESSONS-LEARNED.md` **L18** (verify field-lessons before freezing).
4. **★ Freeze/Float M1 (the active initiative):** `.planning/specs/freeze-float-m1/DESIGN.md` (LOCKED **M1-L1…L9**,
   the two freeze-gate histories, the **Phasing** section) + `PLAN-p0-engine.md`. This is the current design.
5. **The built P0 engine:** `tools/contract_edges.py` + `tools/tests/test_contract_edges.py` (36 tests). Understand
   `invert` / `invalidation_set` / `surface_hash` / `surviving_stubs` / `edge_honesty` before wiring them.
6. **The source doctrine** (the north star for M1→M4): the **Freeze/Float doctrine (validated draft v2)** — the
   operator has it; it defines M1 (contract edges), M4 (inline evaluator/reroll), M2 (shadow tasks), M3 (runtime
   re-partition). Ship order **M1 → M4 → M2 → M3**; M3 earns the most scrutiny (its own review).
7. Only if touching restore/durability: `tools/kata_restore.py`, `tools/kata_trail.py`, `protocol/board.md`.

## 4. THE CURRENT DESIGN — Freeze/Float M1 (contract edges)
**Principle:** *Control governs WHAT gets built; efficiency governs WHEN and BY WHOM. Drift lives entirely in the
WHAT.* KataHarness floats only **layer C (work partition/scheduling)** under machine-checked, fail-closed
invariants; layers A (intent) and B (contracts) stay frozen + human-gated. **M1's win:** a contract-only dependent
dispatches *at freeze* (in parallel) instead of waiting for its provider task — free wall-clock, same tokens. Sound
**only with its 3 companions** (contract pin+invalidation, stub lifecycle, edge-honesty).

**LOCKED decisions (M1-L1…L9 — full text in the DESIGN; the load-bearing ones):**
- **M1-L1** — a contract is one subdir `contracts/<id>/`, pinned by its **interface SURFACE-hash** (signatures +
  return annotations + decorators + class headers; **bodies excluded** so a stub body-fill doesn't flip the pin).
  Constants/type-aliases/re-exports are a **documented deferred residual** (review-backstopped, NOT machine-pinned).
- **M1-L2** — the frontier is prose-driven; the dispatchable-at-freeze clause is one sentence (`kata-orchestrate:211`
  +`:481`). **The one hard base-code change:** `kata_restore.parse_plan_tasks` must union `builds_against` keys
  (else a contract-only dependent is dropped from the restore re-dispatch set → under-dispatch).
- **M1-L3 / M1-L8** — durability is **git-durable commit trailers**, not `.kata/` files: `Kata-Supersede:
  <id>@<newSurfaceHash>` authorizes a contract surface change; `Kata-Invalidated: <task-id>` marks a re-opened
  integrated dependent. The final gate **independently re-derives** from `git log` trailers that every superseded
  contract's `invalidation_set` was fully dispositioned — fail-closed (IaC-gate pattern), never orchestrator trust.
- **M1-L4** — the **provider owns `contracts/<id>/`** (one writer; authors a stub carrying `# KATA-CONTRACT-STUB`,
  fills real behavior in its own task). Final-gate scan: **zero surviving sentinels** (+ dangling-import check).
- **M1-L5** — freeze-time machine check: a dependent's tests import ONLY the contract surface, never provider impl
  paths (else the edge is really `depends_on`). Residual: import-honesty ≠ semantic-honesty → review backstop.
- **M1-L9** — fail-closed everywhere (`surface_hash` raises on parse error; `invalidation_set` raises on malformed
  `builds_against`; a partial/absent invalidation record ⇒ NEEDS_WORK). **Sentinel-absence ≠ implemented** — real
  behavior is proven by the final-gate full-suite re-run, not the scan.

## 5. WHAT'S BUILT vs WHAT'S PLANNED (the phased program)
- **M1-P0 — the engine — ✅ DONE (this session).** `tools/contract_edges.py`: `invert`, `invalidation_set`
  (both raise-on-malformed), `surface_hash` (narrowed extractor, fail-closed, format-invariant, async-aware),
  `surviving_stubs` (sentinel content scan — **language-agnostic**), `edge_honesty` (import-surface check). 36 tests,
  every predicate mutation-proven, Snyk 0, **zero wiring → zero behavioral change (BC by construction)**.
  Adversarially reviewed (SHIP-WITH-FIXES → fixed). Commits `429556a`→`c68ec1d`→`4c78dc3`→`1c65045`.
- **M1-P1 — durable substrate — ⏳ NEXT.** Parse `Kata-Invalidated:` + `Kata-Supersede:` commit trailers;
  `kata_restore.parse_plan_tasks` unions `builds_against` keys; `collect_integrated_tasks` **subtracts**
  `Kata-Invalidated:` ids (so a crash mid-invalidation re-dispatches the task). Lost-run re-dispatch tests.
  **Still additive, still no float.** Freeze a `PLAN-p1` slice → build (TDD/mutation) → engine-review before merge.
- **M1-P2 — wiring + THE FLOAT — ⏳ AFTER P1, re-gated.** The `builds_against` schema in `kata-plan/RUBRIC.md`
  (provider-owned `contracts/<id>/` + sentinel + retirement obligation); the dispatchable-at-freeze clause
  (`kata-orchestrate:211`,`:481`); the supersede enumerate+trailer+route (`:507-509`); the final-gate independent
  re-derivation + surviving-stub (incl. the **dangling-import** half, moved here from P0 per the #3 amendment) +
  surface-drift checks (`:525-540`); a `kata-review` edge-honesty attack surface. **Only here does a contract-only
  dependent actually dispatch early** — and only with every companion live. **Needs its own adversarial freeze-gate
  before merge.**

## 6. HARD RULES (no exceptions)
- **Freeze-gate discipline (proved its worth twice this session):** grill → freeze `DESIGN.md` → **fresh-context
  adversarial `kata-review` (HOLD→SHIP)** → `PLAN.md` → build → integration gate → **fresh-context adversarial
  sweep of the BUILT code** → operator merge gate. Do not self-certify correctness-critical work. P2 in particular
  MUST be freeze-gated before the float lands.
- **M1-L9 / D136 fail-closed:** any decision-code that reads an external artifact to drive a dispatch set / verdict
  **hard-fails on absent/malformed input** — never a silent permissive default. (The P0 engine already obeys this;
  P1/P2 must too.)
- **Durability = git-durable, not `.kata/`:** `.kata/` is disposable (gitignored, rebuilt from `refs/kata/trail`
  which snapshots only `board.md`). Invalidation/supersede state MUST be commit trailers (M1-L3) — the v2
  freeze-gate caught exactly this leak. Do not put load-bearing recovery state in `.kata/`.
- **bump-on-modify ACTIVE:** every `SKILL.md` edit → semver bump (minor = new capability, patch = fix); a shared
  `RUBRIC.md` edit needs NO peer bump; run `validate_skills --write` to regen the README index after a bump.
- **5 frozen `kata_install.py` engine fns stay byte-identical**; **stdlib-only on the install/materialize path.**
- **Commit only on explicit operator approval** (re-ask each session — it does not carry across contexts).
  GitHub-flow: branch per feature/phase → PR → merge → delete branch; never commit straight to master.
- **Supersede-never-rewrite** decisions (new D-numbers ≥ D138; never edit a prior D-entry). D137 = Milestone 1.
- **Model routing:** judgment/plan/grill/eval/gate = Opus (anchor); build/encode/workers = Sonnet (economy).
- **Complex commit messages via `git commit -F <file>`** — PowerShell mangles here-strings containing `|`, `>`,
  `->`, `=>`, or quotes; write the message to a scratch file and `-F` it (learned the hard way this session).

## 7. FIRST ACTIONS (in order)
1. Confirm green at the freeze-float tip (§2). Confirm `git status` clean, `git branch --show-current` =
   `freeze-float/m1-contract-edges`.
2. **Ask the operator:** merge PR #4 (Milestone 1) now? If yes → merge → `git checkout freeze-float/m1-contract-edges;
   git rebase master` → re-confirm green.
3. **Then, on operator go, build M1-P1** via the recipe (§6): freeze `PLAN-p1` → build the trailer substrate + the
   `kata_restore` union/subtract (TDD, mutation-proof, M1-L9 fail-closed) → engine-review → merge gate.
4. **Do NOT jump to P2** (the float) without its own freeze-gate — it is the behavior change and the highest-risk
   phase; the DESIGN requires it re-gated.

## 8. THE THREE THINGS MOST LIKELY TO BITE
- **Stacked-branch hygiene:** if PR #4 merges via squash, the stacked history needs a rebase; do it early.
- **The `surface_hash` residual:** constants/type-aliases/re-exports are NOT machine-pinned (M1-L1) — if a P2
  contract leans on a pinned constant, it MUST be flagged to the `kata-review` edge-honesty backstop, not assumed.
- **Provider-owns-contract ownership:** the `contracts/<id>/` fileset is owned by the PROVIDER only (M1-L4) — the
  disjoint-ownership invariant depends on it; the dependent never writes the contract.
