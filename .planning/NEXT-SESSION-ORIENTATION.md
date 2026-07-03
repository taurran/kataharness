# KataHarness — NEXT-SESSION ORIENTATION (2026-07-02c · Milestone 1 MERGED · Freeze/Float M1 P0+P1 DONE · HELD before M1-P2)

> Paste-ready, self-contained. You are a fresh coding-agent window resuming KataHarness. Read this top to bottom
> before touching anything. Milestone 1 is **merged to master**; Freeze/Float **M1-P0 + M1-P1 are built, reviewed
> SHIP, and committed** on `freeze-float/m1-contract-edges` (PUSHED, tracking origin); nothing is broken; the operator has **HELD**
> before **M1-P2 (the float)**. Your first job is to re-anchor and confirm state, not to start a build. **P2 is the
> behavior change and requires its own adversarial freeze-gate + operator go before it is built or merged.**

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

## 1. ★ BRANCH TOPOLOGY
```
master  8653faf  (Milestone 1 "Release Hardening" MERGED — PR #4, merge commit)
   └── freeze-float/m1-contract-edges   ← Freeze/Float M1 P0+P1 DONE  ·  CURRENT TIP (rebased onto master, PUSHED)
```
- **Milestone 1 (Release Hardening): MERGED** to master `8653faf` (F1–F6 + tool-agnostic security gate, D137/L18).
  The `hardening/kenjiri-lessons` branch was deleted local+remote after merge.
- **Freeze/Float M1-P0 + M1-P1 (`freeze-float/m1-contract-edges`, current, PUSHED):** the pure `contract_edges`
  engine (P0) + the `kata_restore` durable-trailer substrate (P1). Rebased cleanly onto the merged master. Both
  fresh-context adversarially reviewed **SHIP**. Consumes M1's `footprint.file_content_hashes` + PROGRESS heartbeat.
- **The branch is a clean P0+P1 checkpoint.** The PR for Freeze/Float should wait until **P2** lands so the float
  ships reviewed-as-a-unit. Pushing the branch (no PR yet) is an operator call — HELD.

## 2. GREEN (at the freeze-float tip)
- `pytest 2236 passed / 3 skip` — run `-m "not integration"` (2 benchmark integration tests need `uv run pytest`
  over a temp clone → fail offline; NOT a regression). Arc: 653f501=2177 → M1=2190 → +P0=2219 → +P1/hardening=2236.
- `validate_skills` **47 / 0 / 0** · Snyk medium+ **0**.
- **Run tests via the repo venv from `tools/`:** `cd tools; uv run pytest tests -q -m "not integration"`;
  validator `uv run python validate_skills.py` (add `--write` to regen the README skill-index).

## 3. CONTEXT LOADING ORDER (what to read, in order — stay context-lean)
1. **This file** (you're in it) + `.planning/HANDOFF.md` (frontmatter + the ★2026-07-02 block + §2/§4).
2. `AGENTS.md` — the spine (plan-no-drift, default-FAIL, agnostic-via-adapters, two-way handoff, everything versioned).
   `CLAUDE.md` is a thin pointer to it.
3. **Milestone 1 (background — MERGED):** `.planning/specs/kenjiri-lessons/{DESIGN,PLAN}.md` + `DECISIONS.md`
   **D137** (LOCKED L1–L10) + `LESSONS-LEARNED.md` **L18** (verify field-lessons before freezing).
4. **★ Freeze/Float M1 (the active initiative):** `.planning/specs/freeze-float-m1/DESIGN.md` (LOCKED **M1-L1…L9**,
   the two freeze-gate histories, the **D138 amendment**, the **Phasing** section — P0+P1 marked DONE, P2 pending) +
   `PLAN-p0-engine.md` + `PLAN-p1-substrate.md`. **D138** (`DECISIONS.md`) = the sanction + reconciliation record.
5. **The built engine + substrate (P0+P1):** `tools/contract_edges.py` + `tools/tests/test_contract_edges.py`
   (38 tests) — pure predicates; and `tools/kata_restore.py` P1 additions (`parse_plan_tasks` union,
   `collect_integrated_tasks` subtract via `_scan_integration_commit_bodies`, `parse_supersede_trailers`) +
   `tools/tests/test_kata_restore.py` (the "Freeze/Float M1-P1" section). Understand these before wiring P2.
6. **The source doctrine** (the north star for M1→M4): the **Freeze/Float doctrine (validated draft v2)** — the
   operator has it; it defines M1 (contract edges), M4 (inline evaluator/reroll), M2 (shadow tasks), M3 (runtime
   re-partition). Ship order **M1 → M4 → M2 → M3**; M3 earns the most scrutiny (its own review).
7. Restore/durability context (P1 lives here): `tools/kata_restore.py`, `tools/kata_trail.py`, `protocol/board.md`.

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
- **M1-P0 — the engine — ✅ DONE.** `tools/contract_edges.py`: `invert`, `invalidation_set` (both
  raise-on-malformed), `surface_hash` (narrowed extractor, fail-closed, format-invariant, async-aware),
  `surviving_stubs` (sentinel content scan — **language-agnostic**), `edge_honesty` (import-surface check). 38 tests
  (incl. 2 fail-closed for the OSError paths closed under D138), every predicate mutation-proven, Snyk 0, **zero
  wiring → BC by construction**. Adversarially reviewed (SHIP-WITH-FIXES → fixed).
- **M1-P1 — durable substrate — ✅ DONE (`PLAN-p1-substrate.md`, commit `46c7601`).** All in `kata_restore.py`
  (NOT a new `kata_supersede.py` — that name is taken): `parse_plan_tasks` unions `builds_against` keys (M1-L2);
  `collect_integrated_tasks` subtracts `Kata-Invalidated:` (set-based, **over-dispatch-safe** per D138) via the
  extracted `_scan_integration_commit_bodies` helper; `parse_supersede_trailers` provided for the P2 gate (hash
  lowercased to match `_EDGE_RE`). +10 tests (union + subtract mutation-proven; malformed-invalidation surfaced,
  not swallowed). Fresh-context adversarial review: **SHIP** (over-dispatch-only + hash symmetry verified). BC, no float.
- **M1-P2 — wiring + THE FLOAT — ⏳ NEXT, re-gated.** The `builds_against` schema in `kata-plan/RUBRIC.md`
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
- **Supersede-never-rewrite** decisions (new D-numbers ≥ D139; never edit a prior D-entry). D137 = Milestone 1;
  **D138 = Freeze/Float sanction (operator-directed M2) + M1 DESIGN reconciliation** (do not re-question the sanction).
- **Model routing:** judgment/plan/grill/eval/gate = Opus (anchor); build/encode/workers = Sonnet (economy).
- **Complex commit messages via `git commit -F <file>`** — PowerShell mangles here-strings containing `|`, `>`,
  `->`, `=>`, or quotes; write the message to a scratch file and `-F` it (learned the hard way this session).

## 7. FIRST ACTIONS (in order) — ★ ADVAL FIRST, THEN P2
> **★ The detailed session brief is `.planning/HANDOFF-FABLE5-ADVAL-P2.md`** — it carries the float-assessment
> logic + the enumerated adval target set. Read it. The plan is: **adval all Milestone-1→P1 changes → fix → P2.**
1. Confirm green at the freeze-float tip (§2). `git status` clean, branch `freeze-float/m1-contract-edges`, tip
   `d26a0ba` (PUSHED, tracking origin).
2. **Run the comprehensive fresh-context adval** over **every code-bearing change from Milestone 1 → M1-P1**
   (enumerated in `HANDOFF-FABLE5-ADVAL-P2.md` §6: F1 `kata_preflight`, F2 `graph_gen`, F5 `footprint`, F3/F6/F4
   prose in orchestrate/board/config/evaluate/report/bootstrap/lang-profile, P0 `contract_edges`, P1
   `kata_restore`). Each was reviewed as built; this is the **integrated cross-seam sweep before the risky P2.**
   Fresh-context reviewers, one per module/group, told to BREAK the change vs its spec. Prioritize the
   Freeze/Float pair (P0+P1) and the spine-gate prose (F6 security, F3 sprint-blindness).
3. **Fix every real finding** (fix → mutation-re-prove → Snyk re-scan → keep green). **Do NOT proceed to P2 with
   an open HOLD.**
4. **Only then build M1-P2 (the float)** via the FULL freeze-gate recipe (§6): grill/freeze `PLAN-p2` → **fresh-
   context adversarial freeze-gate on the DESIGN/PLAN (HOLD→SHIP)** → build (TDD, mutation-proof, M1-L9
   fail-closed, **bump every edited SKILL** — P2 touches kata-plan RUBRIC + kata-orchestrate + kata-review) →
   integration gate → **fresh-context adversarial sweep of built code** → operator merge gate. The P1 substrate
   it consumes is ready: `parse_supersede_trailers`, the `Kata-Invalidated:` subtract, the `builds_against` union.
5. **P2 is the ONLY place a contract-only dependent actually dispatches early.** It touches the dispatch core —
   do not shortcut its freeze-gate.

## 8. THE THREE THINGS MOST LIKELY TO BITE (in P2)
- **The `surface_hash` residual:** constants/type-aliases/re-exports are NOT machine-pinned (M1-L1) — if a P2
  contract leans on a pinned constant, it MUST be flagged to the `kata-review` edge-honesty backstop, not assumed.
- **Provider-owns-contract ownership:** the `contracts/<id>/` fileset is owned by the PROVIDER only (M1-L4) — the
  disjoint-ownership invariant depends on it; the dependent never writes the contract.
- **The restore subtract is best-effort, the P2 gate is the authority:** a *malformed* `Kata-Invalidated:` trailer
  is surfaced (loud NOTE) but not subtracted at restore — the fail-closed handling of malformed/partial
  invalidation records is P2's final-gate independent re-derivation (M1-L9). Wire that as the real gate.
