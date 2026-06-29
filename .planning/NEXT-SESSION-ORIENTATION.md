# KataHarness — NEXT-SESSION ORIENTATION

## 0. WHO / WHERE
- Project: KataHarness — tool-agnostic, skills-based agent harness ("the Kata Loop"). Dir `C:\Dev\Projects\KataHarness`.
- Git: private remote github.com/taurran/kataharness. `master`, tip `b750211`, **all PUSHED + in sync** (D122 ad-val →
  D123 benchmark build → D124 deep ad-val are on origin). Only the THIS-SESSION doc updates (CONTEXT/HANDOFF/this file)
  may be uncommitted — commit them after the first read-in.
- You are the **conductor**: grill/plan → freeze → orchestrate subagents → gate → merge. Do NOT build inline.
- ★ OPERATOR DIRECTIVE: drive every step via subagents to spare main context. Resume a finished subagent with
  `SendMessage(agentId)` ("had no active task; resumed" is normal).
- Multi-model is LIVE: Codex CLI 0.142.3 (ChatGPT-authed) at
  `C:\Users\taurr_nvs748q\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` — NOT on PATH (prepend that bin dir).

## 1. FIRST — confirm green + read-in
```
cd C:/Dev/Projects/KataHarness/tools
uv run pytest -q                  # expect 1597 passed
uv run python validate_skills.py  # expect 46 skills, 0 errors
git -C C:/Dev/Projects/KataHarness log --oneline origin/master..HEAD   # expect empty (in sync)
git -C C:/Dev/Projects/KataHarness status -sb   # expect only uncommitted CONTEXT/HANDOFF/orientation (if any)
```
Read: `AGENTS.md` → `CONTEXT.md` (glossary — now has the **kata-loop-benchmark** section) → `.planning/STATE.md` (top box)
→ `DECISIONS.md` **D122–D124** → `protocol/{reuse-claims,exec-safety,validation-misses,recall,iac-safety}.md` →
`.planning/specs/kata-loop-benchmark/{RESEARCH,DESIGN,PLAN}.md` → `.planning/PROPOSAL-phantom-reuse.md`.

## 2. WHAT SHIPPED THIS SESSION (D122–D124, 2026-06-28→29)
- **D122 — ad-val of the D117–D121 arc + fixes.** 5 fresh-context reviewers over the between-build seams → NO
  BLOCKER/MAJOR-invariant-break; fixed: Tier-2 escalation-clobber, debug_report snyk negative-floor, 2 doc-truth drifts,
  exec-safety registry **completeness test** (now structural). 3 fail-opens logged.
- **D123 — kata-loop-benchmark v1 BUILT (the D99 C-arc keystone).** Research (SWE-bench + deep web) → grill-RESOLVED
  RESEARCH.md → freeze-gate SHIP → 6-slice build → eval → D98 (caught the orphaned dual-gate BLOCKER) → fixed. See the
  CONTEXT **kata-loop-benchmark** section for the full model.
- **D124 — DEEP ad-val of the benchmark (operator-requested, pre-push).** 5 reviewers found the engine slices unit-solid
  but the **integration/render/metric layers ship-blocking**: every real control scored **Q=0** (dual-gate had no
  cwd/import-context); the **replay-definition + criteria + delta were built-but-UNWIRED**; the report **couldn't render**
  (template tokens absent); the metric could be **gamed** (negative/NaN cost, omit-worst-dimension); delta **mis-fired**
  (fresh id → false "drifted"). **All fixed (TDD/mutation), re-confirmed CLEAN/SHIP.** Gates: **pytest 1597 · 46/0 ·
  Snyk med+ 0.**
- **★ The recurrence system caught itself:** `kata-orchestrate × phantom-reuse` hit the BLOCKER threshold (D123 +
  D124 built-but-unwired) → T2 auto-drafted `.planning/PROPOSAL-phantom-reuse.md` (proposed standing **end-to-end
  wiring-completeness gate**) → marked `proposed` → **awaiting human merge** (T2 proposes, never applies).

## 3. ★ OPEN QUEUE — what's next (operator picks)
- **(a) D5 — the real control FIXTURE + first LIVE benchmark run (n=0→1).** The benchmark is **n=0 LIVE** (synthetic
  fixtures only). The operator intends to **provide a repo** — it plugs into the `control` slot
  (`.kata-benchmark/criteria.json` with `{fail_to_pass,pass_to_pass}`; clone-per-run; the design is fixture-agnostic).
  The natural keystone next step. **Confirm what they want done with the repo before assuming.**
- **(b) PROPOSAL-phantom-reuse → freeze-gate `kata-review` → human merge.** Adopt the proposed standing **wiring-
  completeness gate** so the built-but-unwired class can't recur. The meta-lesson is load-bearing: PART A + D98
  (unit/injected) **cannot** see unwired seams.
- **(c) D3 — benchmark → `kata-improve` T2 optimization-proposal hook** (config-defaults + routing-tables; propose-never-
  apply). Needs the v1 scorecard/definition (now built) + its own grill.
- Other DEFERRED benchmark items: **D1** concurrent bakeoff arms (gated on Spec B execution), **D2** research-mode judge,
  **D4** promote-best-arm-to-master.
- Older queue (pre-benchmark): **Debug Mode end-to-end live run** (n=0→1); **IaC Tier-2 LIVE-APPLY** (operator cloud
  creds); **recurrence-hardening T3** (auto-author guards, C-arc-gated); **`kata-reason` decider + second-brain
  write/distill half** (own grills).

## 4. DEFERRED MINORs / honest-scope notes (do not lose)
- Benchmark **dual-gate nested-`uv-run`** is environment-sensitive (green canonically; full per-control dep-env isolation
  is a D5/real-fixture concern). `default_rate_table()` is a **v1 placeholder** (model keys/prices to calibrate;
  override-able via `config.benchmark.rate_table`).
- Deferred from D124 re-confirm (low/internal-trust): partial-dual-gate inverse hole (f2p dropped + p2p present →
  vacuous credit; low reachability); floor truthiness extends to `exitCode:0.0/False`; the completeness test's
  substring-module-match + `subprocess.`-prefix-only detection.
- Pre-existing: `kata_install.py` 6 LOW CWE-23 (`..`-guarded, below gate).

## 5. HARD RULES
Human-attended (commit/merge/push ONLY on explicit operator approval; doesn't carry across contexts) · drive every step
via subagents · decisions SUPERSEDED with new D-numbers, never rewritten (dated notes; preserve provenance) · Snyk on all
new/changed first-party Python; fix; rescan · repo PRIVATE, no secrets/PII · IGNORE `C:\Dev\CLAUDE.md` (Mise) · PokeVault
LOCAL-ONLY, never git · Windows: `git commit -F <file>`; `validate_skills.py --write` centrally before pytest when a
skill/version changed; README conductor-owned · git fetch+rebase before push (operator web edits).

## 6. THE RECIPE + standing guards
grill/plain → freeze → freeze-gate `kata-review` (HOLD/SHIP) → orchestrated build (subagents, disjoint ownership, TDD,
mutation-proof) → integration gate (pytest + validate 46/0 + Snyk + central README --write) → fresh-context
`kata-evaluate` (PART A, default-FAIL) → standing **D98** `kata-review` (PART B, adversarial) → re-confirm after fixes →
operator merge gate → checkpoint STATE/DECISIONS (new D-number). **★ NEW load-bearing lesson (D124):** PART A + D98 test
units + injected data and **cannot see built-but-unwired / execution-context / metric-read-path gaps** — for any build
touching `kata-orchestrate` wiring or claiming an end-to-end flow, **add a realistic end-to-end dry-run** (see
PROPOSAL-phantom-reuse). Guards: exec-safety (+ completeness test), verify-before-reuse/cite-by-anchor, validation-miss
manifest + T2, multi-model confirm-probe (LIVE). Routing: judgment/plan/eval/grill/D98 = **Opus**; workers = **Sonnet**.
