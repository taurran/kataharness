---
spec: trust-model
artifact: evidence dossier 1/4 — exhaustive promise audit
date: 2026-08-16
provenance: read-only survey agent, committed verbatim-in-substance by the conductor; conductor
  spot-verified the verdict classes, not every row — re-verify any single row before it becomes
  load-bearing in a DESIGN
baseline: grill/dispatch-seam @ fea7ccb (master de8578c)
---

# Evidence 1 — the promise audit (114 rows)

## What actually executes in this repo, exhaustively

| Live surface | Trigger | Fail posture |
|---|---|---|
| `tools/validate_skills.py` (23 `@check` functions) | GitHub Actions `gauntlet` on push-to-master / PR / dispatch (`.github/workflows/ci.yml:39-41`) + manual `tools/scripts/gauntlet.py` | hard-fail |
| `uvx ruff check` / `pytest` / `pytest -m integration` | same workflow | hard-fail |
| `adapters/claude/hooks/kata-sessionstart.py`, `kata-precompact.py`, `kata-gauge-check.py` | Claude Code host events, only if installed | **fail-soft** |
| `adapters/claude/statusline.py` / `statusline_chain.py` | host statusline tick | fail-soft |

No git hooks installed. No process launches, schedules, or gates an agent. Every "load-guard",
"gate", "preflight", and "engine" named in `protocol/` and `skills/` is a **sentence addressed to
an LLM**; only 11 of 62 `tools/*.py` modules have a `__main__`, and skills reference tool CLIs
exactly 7 times across the whole `skills/` + `modules/` tree.

Verdicts: **FACT** (machine check runs on a live path) · **PARTIAL** (runs but covers less than
asserted) · **PROSE** (instruction to a model) · **FACADE** (code exists + unit-tested, zero
production callers, sentence reads as machinery) · **FALSE** (contradicted by evidence).

## The headline counts

Across 114 audited promises: the FACT rows are almost exclusively **document-integrity checks run
by the gauntlet** (clause-pins, fingerprints, bump-on-modify, README sync, allowed-tools shapes,
no-model-ids, protocol-folder registration, `test_exec_safety.py`'s shell=True regression rule)
plus the three fail-soft hooks. ~25 rows are FACADE (correct, tested engines with zero production
callers described as running). 5 rows are FALSE.

## The FALSE rows

1. **`config.md:35` `contextTrigger`** — "the conductor trigger fraction override; default 0.70
   when absent." The key appears in **zero** Python files; the live hook hardcodes
   `kata_gauge.DEFAULT_TRIGGER_FRACTION` (`kata-gauge-check.py:173`) and never opens `kata.config`.
   The advertised dial for the flagship walk-away feature is not connected.
2. **`config.md:31` "`on` = the P1 consuming mode, now LIVE (M4-P1)"** — no scheduler process
   exists; `kata_risk.should_trigger` has no production caller. "LIVE" describes prose.
3. **`config.md:144` `delivery` "Fail-closed (D45): the load-guard validates `delivery` strictly"**
   — `validate_core_config` does not validate `delivery`; no other validator exists.
4. **`observability.md:18` reports at `.kata/reports/<runId>-…`** — no code mints a `runId`
   anywhere; the only reference reads a key nothing writes (`kata_telemetry.py:1436`).
5. **`README.md:89` "frozen plans workers structurally cannot drift" · `README.md:212-213` "that
   promotion gate is built and validator-enforced" · `README.md:60-61` (fresh-context presented
   unqualified) · `kata-review/RUBRIC.md:55`+`kata-evaluate:110-111` "enforced by the orchestrator
   integration gate (see BACKLOG)"** — each contradicted in-tree (no structure exists; the
   validator has no promotion check and `kata-promote:46` says it never sees candidates; the skill
   itself says freshness "is NOT verified and NOT recorded anywhere"; the "enforcing" gate is
   identified as unbuilt by its own citation).

## The 10 most consequential facade rows (ranked by reader-conclusion vs. reality gap)

1. `README.md:89` "workers **structurally** cannot drift" — no dispatch seam, no worktree
   enforcement, no ownership check, no per-task record. Drift is graded after the fact by prompt.
2. `README.md:212-213` promotion gate "built and validator-enforced" — contradicted twice in-tree.
3. `README.md:60-61` fresh-context evaluator presented to readers with no qualifier the skill
   itself carries.
4. `config.md:193` + `kata-orchestrate:38-50` the Core load-guard — `validate_core_config` has no
   caller, no CLI; zero `python -c` invocations exist in skills. Every downstream "load-guard
   STOP" row inherits this hollowness.
5. `config.md:32` `roles` "**wired** … code-enforced, not advisory" — the only contract-layer text
   that explicitly draws the code-vs-advisory distinction, and it lands on the wrong side.
6. `config.md:43,45,47` "(engine-enforced)" ×3 — implemented correctly in
   `kata_preflight.run_preflight`, which never executes. The badge trains readers to trust labels.
7. `config.md:35` `contextTrigger` (see FALSE row 1).
8. `iac-safety.md:297-299` the "| Claim | Verified surface |" table — a verification ritual whose
   cited proof is a function with no caller. The ritual itself is the facade.
9. `kata-evaluate:219` "soundness never rests on orchestrator compliance" — its evidence artifact
   is produced by a callerless module and its own escape clause (`:229-232`) makes it N/A "every
   run today."
10. `kata-review/RUBRIC.md:55` "enforced by the orchestrator integration gate (see BACKLOG)" — the
    word *enforced* applied, in two files, to a gate the same sentence identifies as unbuilt.

## The counterweight — what is genuinely FACT, and the distribution finding

Doc integrity is real and runs in CI. `test_exec_safety.py` genuinely blocks new `shell=True`
sinks in `tools/`. Three fail-soft hooks run live. And a striking set of files state their own
non-enforcement **precisely and correctly**: `orchestration.md:58-64`, `engram.md:153-158`,
`steering.md:45-50`, `authored-artifact-gate.md:44-52`, `recall.md:120-134`,
`validation-misses.md:92`, `DETERMINISM-DOCTRINE.md:81-83`, `kata-evaluate/SKILL.md:27-33`.

**The distribution finding (the audit's core conclusion):** the failure is not that the repo
cannot tell the truth about itself — it is that the honest labels are concentrated in the deep
protocol layer, while the config schema, the orchestrate preconditions, and the README use the
vocabulary of machinery ("wired", "engine-enforced", "code-enforced", "structurally", "LIVE",
"automatically") for the same dead code.

## Selected per-file rows (retained for design use; full sweep was 114 rows)

- `prime-directives.md:13-18` PD-1 "complete means wired end-to-end" — PROSE, and self-contradicted
  by ~25 FACADE rows in this audit; the *text* is tamper-evident (FACT).
- `prime-directives.md:117-119` "nothing defends the validator's own source mechanically" — FACT
  (honest residual, correctly stated).
- `exec-safety.md:27-29` structured-argv/shell=False — FACT for `tools/` code (regression-tested in
  the gauntlet); PARTIAL for the registry (a new `shell=False` external sink is not detected); 5 of
  17 registry rows describe modules with zero production callers.
- `board.md:45-47` run-isolation MUST (rotate at run start) — PROSE; text pinned (FACT); no run-id
  exists so a cross-run board is undetectable.
- `observability.md:27,58,92` "malformed row RAISES / never treat null as 0 / treat-as-triggered" —
  FACADE (implemented, clause-pinned, whole suite has zero production callers).
- `kata-evaluate:46` mutation.json `allNonVacuous` MUST be true — PARTIAL, and the **strongest real
  evidence chain in the harness** (gate_emit has a `__main__`; consumption is an LLM reading JSON).
- `kata-evaluate:133-136` "the orchestrator runs `tools/grounding_gate.py`" — FALSE as written: the
  module has no `__main__` and cannot be "run" as stated.
- `kata-bootstrap:250` "does NOT re-validate (that is kata-orchestrate's fail-closed load-guard)" —
  FACADE by deferral: validation is deferred to a guard that never runs.
- `DETERMINISM-DOCTRINE.md:81-83` "Skill-level enforcement is NOT built — a named open follow-up"
  — FACT; the best-practice disclosure in the repo. The DET-01..14 table is PARTIAL (accurate at
  verification time, no regression guard; nothing detects a 15th violation).
- `README.md:53-55` the 44/57 checkpoint measurement — FACT, honestly scoped as a one-time
  retroactive scan.
- `README.md:235-241` durable board / restore — FACADE for the trail snapshot path in live terms
  (writer orphaned), FACT for the PreCompact hook when installed, PARTIAL for /kata-resume
  (real code, prompt-triggered).
