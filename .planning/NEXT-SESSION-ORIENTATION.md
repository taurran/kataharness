# KataHarness — NEXT-SESSION ORIENTATION (paste after compact / at session start)

> Self-contained. Paste this whole block to start the next session productive immediately. It sets your
> **FIRST TASK** (build Debug Mode P3, the final phase) and the **subagent-driven cadence** the operator wants.

---

## 0. WHO / WHERE
- **Project:** KataHarness — a tool-agnostic, skills-based agent harness (the "Kata Loop"). Dir `C:\Dev\Projects\KataHarness`.
- **Git:** own repo, private remote `github.com/taurran/kataharness`. Branch `master`, **tip `8f6efb2`, PUSHED + in sync.**
- **You are the conductor.** You drive the loop: grill/plan → freeze → orchestrate subagents → gate → merge. You do NOT build inline.
- **★ OPERATOR DIRECTIVE (standing this session): drive EVERY step via subagents** (planning, freeze-gate, build,
  evaluate, D98, even the fix loops) to spare the main context. Your main context stays on orchestration + gates +
  the checkpoint/commit. This works well — keep doing it. Resume a completed subagent with **SendMessage(agentId)** to
  apply fixes with its context intact (the "had no active task; resumed" message is normal, not an error).

## 1. FIRST — confirm green (before anything)
```
cd C:/Dev/Projects/KataHarness/tools
uv run pytest -q                 # expect 1062 passed
uv run python validate_skills.py # expect 42 skills, 0 errors
git -C C:/Dev/Projects/KataHarness log --oneline origin/master..HEAD   # expect empty (in sync)
```
Then read, in order: `AGENTS.md` → `CONTEXT.md` (glossary) → `.planning/STATE.md` (top CURRENT box) →
`.planning/DECISIONS.md` **D111–D116** → `protocol/{reuse-claims,exec-safety,validation-misses}.md` →
`.planning/specs/debug-mode/DESIGN.md` (the frozen contract) + `PLAN-p1.md`/`PLAN-p2a.md`/`PLAN-p2b.md` (what's built).

## 2. ★ YOUR FIRST TASK — build Debug Mode **P3** (the final phase), subagent-driven
The **core Debug Mode loop is COMPLETE** (P1 comprehend → P2a find/route → P2b characterize/drift-gate/apply-or-defer).
**P3 is the last phase**, after which Debug Mode is functionally complete. From the frozen DESIGN:
- **LD10 — language prompt-profiles:** in-mode specialists by detected stack (per major language + a config/context
  specialist), layered on `kata-tdd`/`kata-diagnose`, **no new Python** (prompt-profiles only).
- **LD13 — onboarding / convert-to-loop:** the dedicated first-run path — fresh install → offer Debug Mode → on
  success offer convert-to-loop + vault setup (writes kata.config + `.planning/` + commits the characterization
  suite + vault binding). Depends on `install-portability` (built, D104) — verify its surfaces before claiming reuse.
- **LD12 — closeout confidence report:** the fixed closeout shape for a debug run — per-module **confidence map**
  (assessed / low-confidence / skipped) · each **deviation→fix→pinning-test** · **regression+security proof** ·
  the **recommendations list** + offered version-up/sprint handoff. It CONSUMES the P2b artifacts:
  `.kata/drift/*.json`, `.kata/deviations/{findings,deferred}.json`, `.kata/function_models/`. (Reuse `kata-closeout`/
  `kata-report` patterns; the P3 comment-seam for this is already in `kata-orchestrate/SKILL.md`.)

**How to run it (the cadence that worked all of D113–D116):**
1. **Delegate the PLAN** to a planning subagent → it writes `.planning/specs/debug-mode/PLAN-p3.md` + returns a
   compact summary. Likely sub-phase if large (LD12 closeout is the highest-value; LD10/LD13 can follow).
2. **Freeze-gate** via a fresh-context `kata-review` subagent (HOLD/SHIP) → apply fixes via the planning agent → FROZEN.
3. **Build** via worker subagents in waves (disjoint file ownership; TDD + mutation-proof for any Python; reuse-by-anchor).
4. **Integration gate:** `pytest` + `validate_skills --write` (run --write BEFORE pytest when a new skill is added, so
   the README-sync test passes) + Snyk on any new Python.
5. **Fresh-context `kata-evaluate` (PART A) + standing D98 `kata-review` (PART B)** via ONE subagent → fix HOLDs via a
   worker → re-confirm via SendMessage to the same evaluator.
6. **Operator merge gate** (present options; wait) → commit `-F <file>` + push + checkpoint STATE/DECISIONS (new D-number).

**Honest-scope notes to carry into P3:** Debug Mode is exercised at the unit/seam level, **not yet run end-to-end on a
real fixture repo** (n=0 live debug runs) — P3's closeout report is the natural place to do the first live exercise.
The §5 structural/public-API drift layer is a v1 FAST-FOLLOW (behavioral drift only is enforced) — don't over-claim
"structure preserved". Confidence (LD5) is a v1 heuristic; formal calibration is deferred.

## 3. HARD RULES (operator-standing — never violate)
- **Human-attended loop:** commit / merge / push **only on explicit operator approval.** Present a merge gate; wait.
- **Drive every step via subagents** (operator directive — saves main context). Main context = orchestration + gates.
- **IGNORE `C:\Dev\CLAUDE.md`** (a Mise project, unrelated). **PokeVault** (`C:\Users\taurr_nvs748q\PokeVault\PokeVault`)
  is **LOCAL-ONLY — never run git against it.**
- **Decisions are SUPERSEDED with new D-numbers, never rewritten.** Commit trailer:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **Snyk** `snyk_code_scan` on all new first-party Python; fix; rescan (global CLAUDE.md). Repo PRIVATE — no secrets/PII.
- **Windows/PowerShell:** git here-strings mis-parse multi-line commit messages → write the message to a scratchpad
  file and `git commit -F <file>`. A `..` in an operator path trips the CWE-23 `_safe_*` guards — use absolute paths.
  When a PS `;`-chain runs `pytest` then `validate --write`, the README-sync test can fail on the FIRST pytest (stale
  README) — run `validate_skills.py --write` BEFORE pytest when a skill was added.

## 4. THE RECIPE + the standing guards (why the loop keeps catching real bugs)
**grill/plan (in-depth, plain — `kata-grill/RUBRIC.md` + memory [[grill-in-plain-terms]]) → freeze DESIGN/PLAN →
freeze-gate `kata-review` (HOLD/SHIP) → orchestrated build (subagents, disjoint ownership, TDD red→green,
mutation-proof via `mutation_run.prove_non_vacuous`) → integration gate (pytest + validate 42/0 + Snyk + gate_emit) →
fresh-context `kata-evaluate` (9-rubric, default-FAIL) → standing D98 `kata-review` (adversarial, fresh-context) →
operator merge gate → merge/push/checkpoint.**
- **D98 is load-bearing — never skip it.** This session it caught a real defect the conformance gate (PART A PASS)
  missed on EVERY build: a preflight RCE, an IaC stateful-set hole, a function-model DoS (+ a chained-Pow on
  re-confirm), a corroboration-gate fail-open, and two drift-gate fail-opens. Run it AND re-confirm after fixes.
- **Verify-before-reuse** (`protocol/reuse-claims.md`): cite reuse surfaces by **stable symbol/section name, NOT line
  numbers** (memory [[cite-skills-by-section-anchor]]) — line cites drift and have bitten the project repeatedly.
- **exec-safety** (`protocol/exec-safety.md`, D112): any externally-sourced value reaching a subprocess = structured
  argv + `shell=False`; any in-process eval of an external expression = AST-allowlist, never `eval`/`exec`. New sinks
  go in the registry. `tools/tests/test_exec_safety.py` enforces it. (The freeze-gate caught an `eval`-RCE in the
  Debug-P1 plan — this guard pays off.)
- **validation-miss manifest** (`protocol/validation-misses.md`, D114): when D98/a human catches what `kata-evaluate`
  passed, the reviewer flags it and the orchestrator appends to `.planning/validation-misses.jsonl` (observe-only). It
  is the data layer for recurrence-hardening — this session would have auto-logged ~6 entries.
- Model routing: judgment/plan/eval/grill = **Opus** (inherit; omit model on Agent calls); workers = **Sonnet**.

## 5. OPEN QUEUE (after Debug Mode P3 — operator picks)
- **(a) Exercise Debug Mode end-to-end** on a seeded fixture repo (first live run, n=0→1) — proves the whole loop.
- **(b) recurrence-hardening T2** — the recurrence detector over `validation-misses.jsonl` → gated `kata-improve`
  proposal → `kata-promote` (= D101; needs a grill: threshold, class taxonomy, skill-attribution).
  `specs/recurrence-hardening/{BRIEF,BRIEF-validation-misses,PLAN-t1-manifest}.md`. (T3 = auto-author guards, C-arc-gated, future.)
- **(c) IaC Tier-2 live-apply** — `specs/iac-live-apply/BRIEF.md` (its own grill; gated on cloud creds + a non-git safety contract).
- **(d) second-brain-learning** — the Recall contract (`specs/second-brain-learning/BRIEF.md`).
- **(e) install+confirm a 2nd platform (codex/kiro) live → run the single-vs-multi-model `kata-loop-benchmark`** (D108
  made it runnable; needs the CLI installed — operator action).

## 6. WHAT SHIPPED THIS SESSION (2026-06-27) — context for P3
- **D111** holistic red-team of D108/D109/D110 → fixed a preflight `verify`-field RCE, IaC case-sensitivity gate-skip,
  dead `forceClassify`, stateful-set gaps, Snyk truthiness, an iac.json cross-seam fail-open, resolve_roles host-only.
- **D112** `protocol/exec-safety.md` + `tools/tests/test_exec_safety.py` — the execution-injection class hardened.
- **D113** Debug Mode P1 — `tools/function_model.py` (oracle + AST-safe `_safe_eval`), `skills/plan/kata-comprehend`,
  the `kata/module/debug` run-shape.
- **D114** validation-miss manifest — `tools/validation_misses.py`, `protocol/validation-misses.md`, the universal hook.
- **D115** Debug Mode P2a — `tools/deviation.py` (LD4 funnel + LD5 confidence/routing), `skills/execute/kata-deviate`.
- **D116** Debug Mode P2b — `tools/drift_gate.py` (behavioral drift gate + AEL integrity),
  `skills/execute/kata-characterize`, the `## Fix-application phase` wiring in `kata-orchestrate`.
- Backout/anchor: every D has a commit on `origin/master` (D116 = `8f6efb2`). 42 skills, pytest 1062, Snyk 0.
- **Debug Mode artifacts** a debug run produces (P3's closeout consumes them): `.kata/function_models/` (P1),
  `.kata/deviations/findings.json` + `deferred.json` (P2a/P2b), `.kata/drift/*.json` (P2b).
