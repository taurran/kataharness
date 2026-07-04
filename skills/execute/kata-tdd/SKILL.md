---
name: kata-tdd
description: >-
  Execute ONE task from a frozen plan with test-driven vertical slices, staying inside owned files and
  never re-planning. Use when a worker subagent is assigned a single plan task and must build it to its
  acceptance criteria — red→green→refactor, behavior over implementation, escalate unknowns instead of
  improvising.
license: Apache-2.0
version: 0.2.0
category: execute
status: experimental
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Edit, Write, Bash]
source: adapted-from mattpocock/skills engineering/tdd
tags:
  - kata/execute
  - kata/spine
  - tdd
  - red-green-refactor
  - worker
---

# kata-tdd — build the slice, test-first, in your lane

You are a **worker** executing exactly ONE task from a FROZEN plan. You build it well and faithfully; you do
not own the plan. Stand on mattpocock's TDD (vertical slices, behavior not implementation) with the kata
constraints layered on.

## Hard constraints (the spine)
- **Stay in your lane.** Edit only the files this task OWNS (listed in your assignment). Touching another
  task's file is drift — don't.
- **Do not re-plan.** The interface, the decisions, and the acceptance criteria are frozen. If something is
  unclear, missing, or looks wrong, **append `ESCALATE` to [[kata-board]] and STOP** — do not improvise a fix
  or re-decide a LOCKED decision.
- **Default-FAIL.** The task is not done until its `<verify>` command passes (tests green; security clean if
  in scope). Read the evidence; don't assume.

## Loop (vertical slices — never horizontal)
Read your task's `<read_first>` and the closest existing code analogs first (match the project's vocabulary
and patterns). **Reuse-claims worker note:** Before claiming a reuse in code — "this already implements X" or
"I'll call the existing Y" — confirm the surface exists per `protocol/reuse-claims.md` (grep/read, cite
`file:line`). If the surface is absent, **ESCALATE** rather than improvise.
Then, for each behavior in the acceptance criteria:
```
RED:    write ONE test for the next behavior → it fails
GREEN:  minimal code to pass → it passes
PROVE:  non-vacuity — run tools/mutation_run.py prove_non_vacuous(...) to automate
        the PROVE step: it reads the pristine source, runs the test (baseline), removes
        the asserted line, runs the test again (mutated), and ALWAYS restores the file.
        A test that stays green after its asserted line is removed is vacuous and does
        not count. Do not advance to the next behavior until the current test bites.
```
One test → one implementation → prove non-vacuity → repeat. Don't write all tests up front (that tests imagined behavior). For
pure data/config tasks with no new logic, "test" = the project's structural/validation gate must stay green.

**A code-bearing task is not done until `.kata/mutation.json` exists with `allNonVacuous: true`.**
Pure data/config/docs tasks with no new executable logic are exempt from this requirement.

**Silent-permissive-default guard (D136).** If your task builds a **decision-bearing** function that reads or
parses an EXTERNAL artifact to drive a dispatch set, a resolver output, or a gate verdict, add ONE test proving
it **hard-fails (raises) on an ABSENT or UNPARSEABLE input** — it must never silently return a permissive default
(empty set, `None`-inherit, vacuous-pass). This is the one hostile-input behavior happy-path fixtures miss (it
caused ~6–7 real lenient-direction bugs that passed their build tests); it composes with the non-vacuity PROVE
step above. Scope is narrow: a legitimately empty COMPUTED result is fine (this guards unread INPUTS, not empty
OUTPUTS), and a **designed, documented fail-safe fallback is exempt** — do not defensively wrap every function.

### Running the PROVE step with mutation_run

Use `tools/mutation_run.prove_non_vacuous(source_path, asserted_line, test_cmd)` as the **runnable**
mechanism for the PROVE step — not a manual hand-edit.  It automates the full loop:
(1) runs `test_cmd` on pristine source → `baseline_passed`; (2) applies
`mutation_check.apply_line_removal`, writes the mutated file; (3) runs `test_cmd` again →
`mutated_passed`; (4) **always restores** the original bytes in a `try/finally`; (5) returns the
`mutation_check.mutation_verdict` dict `{testWentRed, nonVacuous}`.

Example (Python, called from within the task's verify/report step):
```python
from mutation_run import prove_non_vacuous, prove_many
from gate_emit import emit_gate_artifacts

# Option A — one behavior at a time:
records = []
verdict = prove_non_vacuous(
    source_path="tools/my_task.py",
    asserted_line="    return computed_value",
    test_cmd="uv run pytest tests/test_my_task.py -q",
)
records.append(verdict)

# Option B — collect all behaviors at once:
specs = [
    {"source_path": "tools/my_task.py", "asserted_line": "    return computed_value",
     "test_cmd": "uv run pytest tests/test_my_task.py -q"},
]
records = prove_many(specs)

summary = emit_gate_artifacts(
    gate_name="my-task-gate",
    command="uv run pytest tests/test_my_task.py -q",
    footprint=["tools/my_task.py", "tools/tests/test_my_task.py"],
    baseline_sha=baseline_sha,
    result_sha=result_sha,
    out_dir=".kata",
    mutation_records=records,   # ← the verdicts prove_* returned
)
# summary["mutationPath"] → .kata/mutation.json (allNonVacuous must be True to pass)
```

A task whose `mutation.json` shows `allNonVacuous: false` has at least one vacuous test — the task is
**not done** until every behavior bites. The [[kata-evaluate]] gate reads this field and treats
absent or `allNonVacuous: false` as **NEEDS_WORK** for any code-bearing run.

## Refactor (only while GREEN)
After the task's behaviors pass: extract duplication, deepen modules, run the gate after each step. Never
refactor while RED. Never add speculative features beyond the task.

## Supporting depth (principles; full reference port is backlog)
TDD quality rests on **deep modules** (small interface, deep implementation), **testable interface design**,
disciplined **mocking** (test through public interfaces; don't mock internal collaborators — that couples
tests to implementation), and **refactoring** patterns. v0.1 names these as principles; mattpocock tdd's full
reference set (deep-modules / interface-design / mocking / tests / refactoring) is a backlog port. When a
boundary or mocking question arises, prefer integration-style tests through the public interface.

## Report
When your `<verify>` passes and you touched only owned files: append `DONE` to [[kata-board]] with the verify
result, and hand the diff back for the orchestrator's gate. If blocked: `BLOCK`/`ESCALATE` and stop.

## Checkpoint cadence (M4 — only when the dispatch brief mandates it)
When — and ONLY when — your dispatch brief carries the checkpoint-commit mandate (the run has `inlineEval`
≠ `off`), commit at each **owned-module completion** (the same boundary as the module-completion PROGRESS
line — one checkpoint commit per module, conventional message) carrying exactly ONE `Kata-Checkpoint:`
trailer. You do **not** hand-author the trailer JSON: the brief carries the concrete command (the
orchestrator injects its own resolved harness `tools/` path and your worktree root), of the form
`uv run --directory <tools-dir> python -m kata_telemetry emit-trailer --repo-root <your-worktree> --index <i>
--verify-exit <e> [--passed/--failed/--skipped N] [--lint E]` — run it and paste its single stdout line into
the commit message.

The trailer carries **mechanical verify outputs only** — exit codes and counts, re-runnable from the commit;
**never a self-assessment** ("it looks good" is not a checkpoint signal — the D33 boundary). **Never** write a
`Kata-Task:` trailer — that is the orchestrator's integration-only trailer, not the worker's. **Never** put a
checkpoint trailer on a **merge** commit, and **never** author **two** `Kata-Checkpoint:` trailers on one
commit (ambiguous evidence — the parser raises on both).

**Ordering mandate (never reorder):** stage EVERYTHING the chunk changed → **emit** the trailer (the digest
reads the index) → **commit IMMEDIATELY**. Make no edits between emit and commit — a mis-ordered worker stamps
a digest that diverges from the committed tree and pollutes the calibration data.

**Absent the mandate in your brief, this section is inert** — you build and report exactly as before (BC).

## Depth by mode
The active mode is set in `kata.config` and passed in the task by the orchestrator. Do not guess or infer it.

- **Essential** — cover the acceptance-criteria behaviors only: one test per behavior listed in the task,
  minimal GREEN implementation, stop. Skip the refactor pass. No edge-case or boundary tests beyond what the
  acceptance criteria explicitly name. Suitable for a PoC or cheap one-shot.
- **Standard** — the full skill as written above (red→green per behavior, refactor while GREEN, no
  speculative features). Default when no mode is specified.
- **Advanced** — Standard **+** a deeper refactor pass after all behaviors are green (extract duplication,
  deepen modules, verify deep-module boundaries), plus edge-case and boundary behaviors for each acceptance
  criterion that has a non-trivial failure mode. Run the gate after every refactor step.
