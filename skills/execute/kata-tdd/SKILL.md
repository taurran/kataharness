---
name: kata-tdd
description: >-
  Execute ONE task from a frozen plan with test-driven vertical slices, staying inside owned files and
  never re-planning. Use when a worker subagent is assigned a single plan task and must build it to its
  acceptance criteria — red→green→refactor, behavior over implementation, escalate unknowns instead of
  improvising.
version: 0.1.0
category: execute
status: experimental
agnostic: true
allowed-tools: [Read, Grep, Glob, Edit, Write, Bash]
source: adapted-from mattpocock/skills engineering/tdd
tags: [execute, tdd, red-green-refactor, worker]
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
and patterns). Then, for each behavior in the acceptance criteria:
```
RED:   write ONE test for the next behavior → it fails
GREEN: minimal code to pass → it passes
```
One test → one implementation → repeat. Don't write all tests up front (that tests imagined behavior). For
pure data/config tasks with no new logic, "test" = the project's structural/validation gate must stay green.

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
