---
date: 2026-06-21
spec: loop-hardening
sprint: S2 — vet the gate + bring the human into initiation
status: FROZEN — partitions S2 into disjoint slices for an orchestrated foreground-parallel build
roadmapRef: ./ROADMAP.md · baseline: S1.5 green (c513eb7)
closes: G3 (mutation/non-vacuity proof never ran) · G4 (interactive initiation never prompted)
tags: [plan, loop-hardening, sprint-s2, mutation-proof, interactive-initiate, frozen]
---

# S2 — vet the gate + bring the human into initiation · frozen PLAN

Make two documented-but-unfired mechanisms actually fire. **G3:** the mutation/non-vacuity PROVE step is described
in `kata-tdd` but nothing runs it and the evaluator treats absent `mutation.json` as a skip — so vacuous/absent
proof passes silently. **G4:** `kata-initiate` documents an interview but a run can decide inline (the dogfood gave
the human one prompt). Two disjoint slices, Sonnet workers in isolated worktrees → integration gate →
fresh-context `kata-evaluate`.

## LOCKED decisions (do NOT re-decide)
- **Mutation runner is a real, deterministic, restoring loop.** `tools/mutation_run.py` automates ONE PROVE: given
  `(source_path, asserted_line, test_cmd)` it (1) runs `test_cmd` on pristine source → `baseline_passed`; (2)
  backs up the file in-memory, applies `mutation_check.apply_line_removal(source, asserted_line)`, writes it; (3)
  runs `test_cmd` → `mutated_passed`; (4) **ALWAYS restores the original bytes** (try/finally — never leave the
  tree mutated, even on exception/interrupt); (5) returns `mutation_check.mutation_verdict(...)`. It REUSES
  `mutation_check` (never reimplements the verdict). `..`-guard on `source_path` (CWE-23, mirror gate_emit).
- **The proof becomes REQUIRED for code-bearing work (close the silent-skip hole).** `kata-evaluate` rubric item 1:
  for a run that introduces/*changes executable logic*, `.kata/mutation.json` MUST be present AND `allNonVacuous:
  true`; **absent or `false` ⇒ NEEDS_WORK** (default-FAIL). The existing carve-out stands: a **pure data/config/
  docs** task with no new logic is exempt (the evaluator judges applicability and states which). This is a
  *wording/strength* change to item 1, not a new rubric item and not a tier change (structural invariant, D33).
- **Initiation interview is a HARD structural stop (not optional).** `kata-initiate` must, before any execute
  decision, STOP and use `AskUserQuestion` for the load-bearing choices (kind confirmation · target.kind/path ·
  vault · platform · grillDepth) and the dual-control execute decision — it MUST NOT infer them inline from the
  priming prompt. Add an explicit "do not proceed on inferred answers" gate + a short checklist the evaluator can
  verify. `INTENT.md` is frozen FROM the answers.
- **INTENT.md is written deterministically.** `tools/intent_scaffold.py` builds the `INTENT.md` text from an
  `answers` dict per the `protocol/intent.md` schema (mirrors how `gate_emit` writes RESULT.json) — so the frozen
  intent always conforms to the schema and the freeze is testable. `kata-initiate` calls it with the gathered
  answers. (Tool produces the artifact; the SKILL runs the interview.)
- **BC preserved.** Absent `INTENT.md` ⇒ harness reads frozen DESIGN as today. Mutation proof is additive: runs
  that already emit it are unaffected; the change is the evaluator now *requires* it for code-bearing work.

## Wave DAG
```
Wave 1 (parallel):  S2a mutation proof (runner + kata-tdd + kata-evaluate) ──┐
                    S2b interactive initiate (kata-initiate + intent_scaffold) ┘  (disjoint files)
Integration:        octopus-merge → uv sync → pytest + validator 35/0 + Snyk → gate_emit RESULT.json
                    → fresh-context kata-evaluate (PASS)
```

## Task S2a — mutation/non-vacuity proof actually runs + is required
**Owns (disjoint):** `tools/mutation_run.py` (NEW), `tools/tests/test_mutation_run.py` (NEW),
`skills/execute/kata-tdd/SKILL.md` (EDIT), `skills/evaluate/kata-evaluate/SKILL.md` (EDIT).
**read_first:** `tools/mutation_check.py` (`mutation_verdict`/`apply_line_removal`/`run_named_test`),
`tools/gate_emit.py` (`emit_gate_artifacts(..., mutation_records=...)` already writes `.kata/mutation.json`),
`skills/execute/kata-tdd/SKILL.md` (the PROVE step + the recording example), `skills/evaluate/kata-evaluate/SKILL.md`
(rubric item 1 + the "Mutation proof" artifact row), this PLAN's LOCKED section.
**action:**
- **`tools/mutation_run.py`** — `prove_non_vacuous(source_path, asserted_line, test_cmd, *, runner=None) -> dict`:
  the deterministic restoring loop in the LOCKED decision. `runner` injectable `(cmd) -> bool` (default: real
  subprocess via `mutation_check.run_named_test`-style `uv run pytest` returning pass/fail) so tests are pure.
  ALWAYS restore original bytes in a `finally`. Return the `mutation_verdict` dict (`{testWentRed, nonVacuous}`).
  `..`-guard on `source_path`. Optionally a thin `prove_many(specs) -> list[dict]` collecting records for
  `gate_emit`.
- **`skills/execute/kata-tdd/SKILL.md`** (EDIT): change the PROVE step so it points at `tools/mutation_run.py`
  (`prove_non_vacuous(...)`) as the **runnable** way to execute the mutation — not a manual hand-edit — and keep
  the `gate_emit` recording example, now feeding it the records `prove_*` returns. Tighten: "a code-bearing task is
  not done until `.kata/mutation.json` exists with `allNonVacuous: true`."
- **`skills/evaluate/kata-evaluate/SKILL.md`** (EDIT): strengthen **rubric item 1** to the LOCKED rule — for a
  code-bearing run, absent/`false` `mutation.json` ⇒ **NEEDS_WORK**; pure data/config/docs exempt (state which).
  Update the "Mutation proof" artifact row note from "absent if no mutation step ran" to the required-for-code rule.
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_mutation_run.py -q` (TDD red→green). Cover: a
genuinely non-vacuous case (baseline pass, mutated fail ⇒ `nonVacuous: true`); a vacuous case (mutated still
passes ⇒ `false`); **the file is byte-identical after the run** (restore proven, incl. when the runner raises —
`finally` path); `apply_line_removal` of a missing line surfaces cleanly; `..`-guard rejects traversal. Full suite
+ `validate_skills.py` 35/0 stay green (SKILL edits keep frontmatter valid).
**acceptance:** `prove_non_vacuous` on a real tiny source+test returns a correct verdict and leaves the file
unchanged; the two SKILLs now make the proof runnable and required-for-code. Demonstrable: a `mutation.json`
showing `allNonVacuous: true` produced by the runner.
**threat model:** writes only the operator-supplied `source_path` (`..`-guard), restores it; `test_cmd` runs at the
same trust level as the existing gate (operator/orchestrator). New Python ⇒ Snyk at the gate.

## Task S2b — kata-initiate actually prompts + deterministic INTENT.md
**Owns (disjoint):** `modules/initiation/kata-initiate/SKILL.md` (EDIT), `tools/intent_scaffold.py` (NEW),
`tools/tests/test_intent_scaffold.py` (NEW).
**read_first:** `modules/initiation/kata-initiate/SKILL.md` (current phases), `protocol/intent.md` (the INTENT.md
schema — authoritative), `docs/STANDARDS.md` §1 (frontmatter), this PLAN's LOCKED section.
**action:**
- **`tools/intent_scaffold.py`** — `build_intent(answers: dict) -> str` (pure): given the gathered answers
  (`kind, goal, fixes, features, modulesAdded, changeSummary, target{kind,path,vault,platform}, grillDepth,
  readiness`), return the full `INTENT.md` text (YAML frontmatter + north-star body) **exactly per
  `protocol/intent.md`**. Validate required keys; raise a clear error on a missing/invalid `kind`/`target.kind`/
  `grillDepth` (fail-closed). No file I/O in the pure function; a thin `write_intent(path, answers)` wrapper does
  the write with a `..`-guard.
- **`modules/initiation/kata-initiate/SKILL.md`** (EDIT): make the interview a **HARD structural stop** — add an
  explicit gate before Phase 6: "**STOP. Do NOT infer these from the priming prompt — ask via `AskUserQuestion`:**
  kind · target.kind/path · vault · platform · grillDepth · the execute decision. Proceeding without asking is a
  drift failure the gate will catch." Point Phase 4/6 at `tools/intent_scaffold.py` as the deterministic writer
  (the SKILL runs the interview; the tool emits the schema-conformant file). Add a short end-of-phase **checklist**
  an evaluator can verify (each load-bearing answer came from an operator prompt, not inference).
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_intent_scaffold.py -q` (red→green). Cover:
`build_intent` over a full answers dict produces frontmatter with every required `protocol/intent.md` key + the
chosen values; a missing `kind`/`target.kind`/`grillDepth` raises; `write_intent` writes the file and the
`..`-guard rejects traversal; the output round-trips as valid YAML frontmatter. Full suite + validator 35/0 stay
green (the kata-initiate SKILL edit keeps frontmatter valid + the validator's required-protocol checks pass).
**acceptance:** `build_intent(answers)` yields a schema-conformant `INTENT.md`; the SKILL now structurally forces
the interview. Demonstrable: a frozen `INTENT.md` produced from an answers dict, schema-valid.
**threat model:** `write_intent` writes only the operator-supplied path (`..`-guard); pure builder otherwise. New
Python ⇒ Snyk at the gate.

## Integration + gate (the boundary artifact)
1. Octopus-merge `s2/mutation` + `s2/initiate` off master → `s2/integration`. `cd tools && uv sync` (no new deps).
2. Full gate: `uv run pytest -q` (334 + new) · `uv run python validate_skills.py` (35/0 — SKILL edits, no new/renamed
   skills) · `mcp__Snyk__snyk_code_scan` on the new Python (`..`-guards are the controls; CWE-23 on operator/CLI
   args = the documented FP class). Emit `.kata/RESULT.json` via `tools/gate_emit.py`.
3. **Fresh-context `kata-evaluate`** — a SEPARATE no-write Sonnet subagent, 8-rubric, default-FAIL. **No
   self-certification (L8).** Must return PASS. (Bonus dogfood: this evaluation can itself exercise the strengthened
   rubric item 1 against S2a's own `mutation.json`.)
4. Merge to master, push, checkpoint STATE/HANDOFF/ROADMAP, clean up worktrees+branches. Backout: tag `pre-s2`.
   Then **S3** (grounding/research G5 + the loop-back G6 — the operator's must-have, proves the loop loops).

## Ownership disjointness
| File | Owner |
|---|---|
| `tools/mutation_run.py`, `tools/tests/test_mutation_run.py`, `skills/execute/kata-tdd/SKILL.md`, `skills/evaluate/kata-evaluate/SKILL.md` | S2a |
| `modules/initiation/kata-initiate/SKILL.md`, `tools/intent_scaffold.py`, `tools/tests/test_intent_scaffold.py` | S2b |
| integration RESULT.json, STATE/HANDOFF/ROADMAP checkpoint | Integrator |
No file in two lanes. ✓
