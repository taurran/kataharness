# KataHarness — NEXT-SESSION ORIENTATION (paste after compact / at session start)

> Self-contained. Paste this whole block to start the next session productive immediately. It sets your
> **FIRST TASK** (adversarially validate the D117–D121 arc), then commit/push, then start the kata-loop-benchmark —
> all driven via subagents, the cadence the operator wants.

---

## 0. WHO / WHERE
- **Project:** KataHarness — a tool-agnostic, skills-based agent harness (the "Kata Loop"). Dir `C:\Dev\Projects\KataHarness`.
- **Git:** own repo, private remote `github.com/taurran/kataharness`. Branch `master`, **tip `a11b9de`, all D117–D121
  PUSHED + in sync.** The THIS-SESSION doc updates (CONTEXT.md / HANDOFF.md / this orientation) are **UNCOMMITTED on
  purpose** — they get committed in step 3 below, AFTER the ad-val pass, so the red-team works the code arc as it shipped.
- **Multi-model is LIVE:** the operator installed **Codex CLI 0.142.3** (ChatGPT-authed) at
  `C:\Users\taurr_nvs748q\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe`. It is **NOT on PATH** — prepend that bin
  dir for codex invocations; the harness probe needs it on PATH. `kata_install.py --platform codex --confirm` →
  `confirmed:true` (D121).
- **You are the conductor.** You drive: grill/plan → freeze → orchestrate subagents → gate → merge. You do NOT build inline.
- **★ OPERATOR DIRECTIVE (standing): drive EVERY step via subagents** (planning, freeze-gate, build, evaluate, D98,
  even fix loops) to spare main context. Your main context stays on orchestration + gates + the checkpoint/commit.
  Resume a completed subagent with **SendMessage(agentId)** to apply fixes with its context intact (the "had no active
  task; resumed" message is normal, not an error).

## 1. FIRST — confirm green + read-in (before anything)
```
cd C:/Dev/Projects/KataHarness/tools
uv run pytest -q                 # expect 1314 passed
uv run python validate_skills.py # expect 45 skills, 0 errors
git -C C:/Dev/Projects/KataHarness log --oneline origin/master..HEAD   # expect empty (in sync)
git -C C:/Dev/Projects/KataHarness status -sb   # expect only the uncommitted doc updates (CONTEXT/HANDOFF/orientation)
```
Then read, in order: `AGENTS.md` → `CONTEXT.md` (glossary — now extended with the D117–D121 surfaces) →
`.planning/STATE.md` (top CURRENT box) → `.planning/DECISIONS.md` **D117–D121** →
`protocol/{reuse-claims,exec-safety,validation-misses,recall,iac-safety}.md` (the standing guards + new contracts) →
the per-build specs as needed (`specs/debug-mode/PLAN-p3.md`, `specs/recurrence-hardening/PLAN-t2.md`,
`specs/iac-live-apply/PLAN-tier2-preview.md`, `specs/second-brain-learning/PLAN-recall.md`).

## 2. ★ YOUR FIRST TASK — adversarially validate ("ad-val") the D117–D121 arc
A fresh-context, **cross-cutting holistic red-team** of everything built this session — **mirror the D111 pattern**
(parallel fresh-context reviewers → synthesis → operator-gated fix scope). The per-build D98 reviews already happened
and were clean/fixed; **what is UNREVIEWED is the seams BETWEEN the 5 builds as a set** — the shared surfaces that
multiple builds touched independently:
- **The shared `kata-orchestrate`** — D117 added the P3-seam + LD10 dispatch injection + `.kata/snyk/<id>.json` persist;
  D118 added the Final-gate `run_id` stamp + detector hook; D119 added the whole Tier-2 IaC apply state-machine region.
  Three independent edits to one conductor skill — check they compose, don't contradict, and don't double-write artifacts.
- **The shared `tools/validation_misses.py`** — D114 created it (observe-only); D118 extended its schema (soft
  `failure_class` enum + nullable `run_id`, 9→10 fields) and D117's debug pipeline consumes it. Check the schema
  extension is BC for D114/D117 readers and the detector (D118) reads what the orchestrator (D118) writes.
- **The exec-safety registry** (`protocol/exec-safety.md` + `test_exec_safety.py`) — D119 added 4 DEFERRED sink rows
  for `iac_apply.py`; D121 changed `kata_dispatch`/`kata_install` subprocess calls (new flag + `stdin=DEVNULL`). Confirm
  the registry still matches reality and `test_exec_safety` still guards the RCE class (no new unregistered sink).
- **The multi-model surfaces** — now LIVE (D121). The confirm-probe is the standing guard; check the `_PROBE_COMMANDS ⊆
  _COMMAND_BUILDERS` invariant still holds and the codex fix didn't regress kiro.
- **The honesty/no-write invariants across builds** — debug_report (engine-pinned honesty), recall (no write path),
  iac_apply (no reachable subprocess), T2 (propose-never-guard). Probe whether any cross-build interaction can defeat one.

**How to run it (the cadence):**
1. **Dispatch N parallel fresh-context reviewer subagents** (opus; one per build or per seam-cluster), each told to try
   to BREAK its target — fail-opens, doc-only seams that don't reproduce from source, overclaim/slop, and especially
   **cross-build seam contradictions** — not to re-grade conformance. Give each the relevant DECISIONS entry + files.
2. **Synthesize** their findings into one ranked list (BLOCKER / MAJOR / MINOR / cosmetic).
3. **Operator-gate the fix scope** (present the synthesis; the operator trims — drop LOW cosmetic, confirm real ones;
   watch for over-fix spirals, as in D111 where a cosmetic over-fix had to be reverted).
4. **Fix the confirmed findings** via worker subagents (TDD, mutation-proof), then re-confirm. Each material fix is its
   own D-number.
5. **Log any "PART A passed it, ad-val caught it" misses** to `.planning/validation-misses.jsonl` (D114, observe-only) —
   this is exactly the data T2 (D118) would auto-propose against.

## 3. THEN — commit/push (after the ad-val pass)
- Commit the **uncommitted doc updates** from the prior session (CONTEXT.md / HANDOFF.md / this orientation) **+** any
  ad-val fixes. Each material change = its own D-number (supersede-never-rewrite). Trailer:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **Windows:** write multi-line commit messages to a scratchpad file and `git commit -F <file>` (PS here-strings mangle them).
- **git may diverge from operator GitHub-web edits** → `git fetch` + rebase BEFORE push (this happened this session with
  LICENSE/README web edits, `cae9fae`/`6a15bfb`). Commit/push ONLY on explicit operator approval (present a merge gate; wait).

## 4. THEN — start the `kata-loop-benchmark` (queue item (e), step 2 — the C-arc keystone, D99)
The benchmark mechanism that measures whether learning/hardening pays off (it defines the C-arc unlock, D99). It needs a
**fresh grill** (deferred this session). **Capture these already-decided/known facts so you don't re-derive them:**
- **Smallest-v1 shape:** a **DETERMINISTIC scorer** over the gate artifacts a run already emits
  (`.kata/{RESULT,footprint,mutation}.json`) + run-metadata → a `.kata/benchmark/<run-id>.json` scorecard.
- **Reuse the frozen fixture:** `01-cli-wordfreq` — `.planning/specs/d16-planning-varied-ab/corpus/01-cli-wordfreq.md`
  + its `METRIC-SHEET.md` (already frozen). Don't author a new task.
- **Reuse the now-LIVE multi-model machinery** (D121) — Codex is confirmed live, so a real arm is possible.
- **Fairness invariants (D13/D14):** frozen task + fresh context per arm + a constant Claude model.
- **Operator pre-decisions captured this session:** (build-vs-adopt = **deferred, lean native**); (**INCLUDE the LIVE
  multi-model arm in v1** — the operator chose to spend ~1 Codex run for a real single-vs-multi number, n=1 directional);
  (scoring metric set + LLM-judge = **GRILL next session** — these are the open questions to re-grill with the operator).
- A grill-prep framing already exists in this session's transcript — **re-grill scoring + build-vs-adopt with the operator**
  before freezing.

## 5. ★ FLAG — the operator will PROVIDE A REPO to intake
The operator intends to **hand over a repo** next session. Most likely the **Debug Mode end-to-end live-run target**
(queue item (a), still n=0 live — Debug Mode is functionally complete at the skill/seam level but has never run on a real
repo) OR a new build target. **Confirm what they want done with it before assuming** — do not start the benchmark or the
ad-val on it without checking; it may re-order the agenda above.

## 6. HARD RULES (operator-standing — never violate)
- **Human-attended loop:** commit / merge / push **only on explicit operator approval.** Present a gate; wait. Approval
  does NOT carry across contexts.
- **Drive every step via subagents** (operator directive — saves main context). Main context = orchestration + gates.
- **IGNORE `C:\Dev\CLAUDE.md`** (a Mise project, unrelated). **PokeVault** (`C:\Users\taurr_nvs748q\PokeVault\PokeVault`)
  is **LOCAL-ONLY — never run git against it.**
- **Decisions are SUPERSEDED with new D-numbers, never rewritten.** Trailer:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **Snyk** `snyk_code_scan` on all new first-party Python; fix; rescan (global CLAUDE.md). Repo PRIVATE — no secrets/PII.
- **Windows/PowerShell:** `git commit -F <file>` for multi-line messages. A `..` in an operator path trips the CWE-23
  `_safe_*` guards — use absolute paths. Run `validate_skills.py --write` (conductor, centrally at the integration gate)
  BEFORE pytest when a skill/version changed (README-sync test). README is conductor-owned, not slice-owned (F2).
- **git may diverge from operator GitHub-web edits** → `git fetch` + rebase before push.

## 7. THE RECIPE + the standing guards (why the loop keeps catching real bugs)
**grill/plain (`kata-grill/RUBRIC.md` + memory [[grill-in-plain-terms]]) → freeze → freeze-gate `kata-review`
(HOLD/SHIP) → orchestrated build (subagents, disjoint ownership, TDD red→green, mutation-proof via
`mutation_run.prove_non_vacuous`) → integration gate (pytest 1314 + validate 45/0 + Snyk + central README --write) →
fresh-context `kata-evaluate` (PART A, 9-rubric, default-FAIL) → standing D98 `kata-review` (PART B, adversarial,
fresh-context) → operator merge gate → merge/push/checkpoint.**
- **D98 is load-bearing — never skip it.** This session it caught real fail-opens the conformance gate (PART A PASS)
  missed: D117's Snyk regression-masking + un-route-gated `applied:true` (2 MAJOR). Run it AND re-confirm after fixes.
- **Verify-before-reuse** (`protocol/reuse-claims.md`): cite reuse surfaces by **stable symbol/section name, NOT line
  numbers** (memory [[cite-skills-by-section-anchor]]). The D117 freeze-gate caught a phantom Snyk-from-RESULT.json
  capability — this is the exact class.
- **exec-safety** (`protocol/exec-safety.md`, D112): externally-sourced value → subprocess = structured argv +
  `shell=False`; in-process eval of an external expression = AST-allowlist, never `eval`/`exec`. New sinks go in the
  registry; `tools/tests/test_exec_safety.py` enforces it. (The exec-injection class recurred 3× — memory
  [[exec-injection-class-hardened]].)
- **validation-miss manifest** (`protocol/validation-misses.md`, D114; T2 act-but-gated, D118): when D98/a human catches
  what `kata-evaluate` passed, flag it → orchestrator appends to `.planning/validation-misses.jsonl`. T2 auto-drafts a
  human-gated `PROPOSAL-<class>.md` when a class recurs (3 distinct runs / 2 for BLOCKER). **T2 proposes, never
  guards/decides/merges.**
- **multi-model confirm-probe** (now LIVE, D121): the standing guard for stale per-CLI flags between releases — it caught
  the codex 0.142.3 flag/stdin change. `_PROBE_COMMANDS ⊆ _COMMAND_BUILDERS`.
- Model routing: judgment/plan/eval/grill/D98 = **Opus** (inherit; omit model on Agent calls); workers = **Sonnet**.

## 8. OPEN QUEUE + deferred MINORs
- **(a) Debug Mode end-to-end live run** on a fixture repo (n=0→1) — may be the repo the operator provides (§5).
- **(e) step 2 = the `kata-loop-benchmark`** (grill + build) — the immediate post-ad-val item (§4).
- **IaC Tier-2 LIVE-APPLY execution** — future-gated on operator CLOUD creds (a SEPARATE gate from the now-installed Codex).
- **recurrence-hardening T3** (auto-author guards) — C-arc-gated, future.
- **`kata-reason` decider + second-brain write/distill half** — deferred (their own grills).
- **Deferred MINORs:** `kata_install.py` **6 LOW CWE-23** path-traversal (in `..`-guarded code, below the medium+ gate —
  a separate hardening pass); D119 (`approval_verdict` PENDING_PLAN-vs-BLOCKED; redundant CFN argv flag; N1 stateful-set
  completeness in `iac_detect`); D120 (recall.md min-token-length doc note; `query.kind` schema `open:True` comment).

## 9. WHAT SHIPPED THIS SESSION (D117–D121, 2026-06-27→29) — context for the ad-val
- **D117 — Debug Mode P3** (the FINAL phase; Debug Mode now functionally complete at the skill/seam level):
  `tools/debug_report.py` (LD12 closeout engine) + `kata-debrief` + `kata-closeout` Step 3b + `kata-lang-profile` (LD10,
  6 lang profiles) + `kata-onboard` (LD13) + `kata-orchestrate` P3-seam/LD10-injection/Snyk-persist. D98 caught 2 MAJOR
  fail-opens (Snyk regression-masking; un-route-gated `applied:true`) → fixed at the engine. pytest →1108, 42→45 skills.
- **D118 — recurrence-hardening T2** (recurrence→proposal, act-but-gated): `tools/recurrence_detect.py` (severity-aware
  threshold 3 / BLOCKER-2, distinct-run via `run_id`+ts-fallback, handled-skip) + soft `failure_class` enum + nullable
  `run_id` in `validation_misses.py` + `kata-improve` v0.2.0 auto-draft + `kata-orchestrate` Final-gate detector hook +
  `protocol/validation-misses.md` T2. Invariant: T2 proposes, never writes guards/decides/merges. pytest →1175.
- **D119 — IaC Tier-2 (preview/approve HALF; execution DEFERRED):** `tools/iac_apply.py` (argv builders, plan-hash
  [TF binary / CFN full-response], typed self-binding capability-gate, `apply_state`, `run_apply`=NotImplementedError
  seam) + exec-safety deferred rows + `iac-safety.md` §9 + `kata-orchestrate` IaC region + both specialists v0.2.0.
  Catastrophic invariant (no reachable cloud mutation) holds BY CONSTRUCTION. D98 = first zero-fail-open build of the
  session. pytest →1261.
- **D120 — second-brain Recall (read-CONTRACT + files-only adapter):** `tools/recall.py` (shape-only/open-vocabulary
  contract, files-only adapter, hard token-overlap selection, NO embeddings, evidence-projection, NO write path) +
  `protocol/recall.md` + `engram.backend` naming + REQUIRED_PROTOCOL registration + `kata-initiate` v0.2.0
  Phase-1b/mirror wiring. INTENT-never-written is STRUCTURAL. Decider (`kata-reason`) + write/distill half DEFERRED.
  pytest →1310.
- **D121 — Codex adapter live-hardened + multi-model layer confirmed LIVE (n=0→1):** operator installed Codex CLI
  0.142.3 (ChatGPT-authed). First live run of the D108 dispatch chain found a real defect → fixed
  (`--skip-git-repo-check` + `stdin=DEVNULL` in `kata_dispatch.codex_command`/`_subprocess_runner` +
  `kata_install._PROBE_COMMANDS["codex"]`/`_real_probe_runner`). `kata_install.py --platform codex --confirm` →
  `confirmed:true, confirmedPlatforms:["codex"]`. Read-only validator/researcher routing now LIVE-proven; coder-routing
  + evaluator-thresholds still DEFERRED (D108 MM-1). pytest →1314.
- **Gates now:** pytest **1314** · **45 skills / 0** · Snyk **0** on all new/changed Python EXCEPT a flagged
  PRE-EXISTING `tools/kata_install.py` **6 LOW** CWE-23 (in `..`-guarded code, below the medium+ gate — separate pass).
- **Anchors:** every D has a commit on `origin/master` (D121 = `a11b9de`). The session's doc updates
  (CONTEXT/HANDOFF/orientation) are uncommitted pending the ad-val (step 3).
- **Debug Mode run artifacts** (P3's closeout consumes them): `.kata/function_models/` (P1),
  `.kata/deviations/{findings,deferred}.json` (P2a/P2b), `.kata/drift/*.json` (P2b), `.kata/snyk/<finding_id>.json` (P3).
