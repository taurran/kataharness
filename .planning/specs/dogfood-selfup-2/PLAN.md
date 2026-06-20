---
date: 2026-06-19
spec: dogfood-selfup-2
status: FROZEN — orchestrated version-up run (4 concurrent workers in isolated worktrees)
target: KataHarness self version-up
baselineGate: "cd tools && uv run pytest -q  &&  uv run python validate_skills.py"
baseline: validator 31/0 · pytest 40 · Snyk 0 @ 97c94d8 (restore tag: pre-dogfood-2)
integration_branch: dogfood-2/eval-self-sufficiency
ownership:
  A: [tools/run_result.py, tools/tests/test_run_result.py]
  B: [tools/footprint.py, tools/tests/test_footprint.py]
  C: [tools/mutation_check.py, tools/tests/test_mutation_check.py, skills/execute/kata-tdd/SKILL.md]
  D: [skills/evaluate/kata-report/SKILL.md, skills/evaluate/kata-evaluate/SKILL.md]
waves: { wave1: [A, B, C, D] }   # fully independent — 4 concurrent workers
depends_on: {}
worktrees:
  A: { branch: d2/slice-a, path: /c/Dev/_kata_d2/slice-a }
  B: { branch: d2/slice-b, path: /c/Dev/_kata_d2/slice-b }
  C: { branch: d2/slice-c, path: /c/Dev/_kata_d2/slice-c }
  D: { branch: d2/slice-d, path: /c/Dev/_kata_d2/slice-d }
tags: [plan, dogfood, version-up, orchestrated, frozen]
---

# Dogfood #2 — evaluation self-sufficiency (the REAL orchestrated run)

**Feature:** make a KataHarness run **evaluable in depth from its end artifacts alone** (closes Dogfood #1's
headline finding). Four disjoint slices → four concurrent worker subagents in isolated git worktrees, driven by
the orchestrator (plan-guardian), gated, then a human version selection.

## Slices (disjoint file ownership — zero-conflict merge)

### A — `RESULT.json` emitter
- **owns:** `tools/run_result.py`, `tools/tests/test_run_result.py`
- **action:** a pure-core + thin-shell module that captures a gate run into a machine-readable result:
  `{ gateName, command, exitCode, passed, failed, skipped, stdoutTail, baselineSha, resultSha, utc }`. Keep the
  parsing/serialization **pure** (input = command output string + metadata → dict) so it is testable without
  running a real gate; a thin wrapper may shell out. Write a `RESULT.json` to a given path.
- **verify:** `uv run pytest test_run_result.py` — asserts the pure builder yields all required keys from a
  sample pytest-style output (e.g. "40 passed"), and round-trips to/from JSON.
- **acceptance:** required keys present; counts parsed from a sample; JSON valid. Negative: no network, no global
  state; the builder is pure (same input → same output).

### B — footprint manifest + diff-stat
- **owns:** `tools/footprint.py`, `tools/tests/test_footprint.py`
- **action:** a **pure** core `partition(changed_files, footprint) -> {in_footprint, out_of_footprint}` plus a
  thin git wrapper (changed files vs a baseline ref) and a diff-stat formatter. Emits a footprint manifest dict.
- **verify:** `uv run pytest test_footprint.py` — pure partition over sample lists; an out-of-footprint file is
  flagged.
- **acceptance:** partition correct; out-of-footprint detection works. Negative: the pure core does not call git.

### C — mutation / non-vacuity check (bake into kata-tdd)
- **owns:** `tools/mutation_check.py`, `tools/tests/test_mutation_check.py`, `skills/execute/kata-tdd/SKILL.md`
- **action:** a minimal helper that, given a "green" test and a caller-supplied mutation (a line removal/negation
  applied to a target file), re-runs the named test and asserts it flips **green→red** (proving the test bites);
  returns `{ mutated, testWentRed: bool }`. Document the **mandatory mutation-proof step** in `kata-tdd/SKILL.md`
  (after green, prove non-vacuity). Keep the core logic pure/testable (decide red-vs-green from a result object);
  a thin shell runs the actual test.
- **verify:** `uv run pytest test_mutation_check.py` — the pure decider returns `testWentRed=True` when the
  mutated run reports failure, `False` otherwise; validator stays green after the kata-tdd edit.
- **acceptance:** decider correct both ways; kata-tdd documents the step. Negative: no skill OTHER than kata-tdd
  touched; wikilinks still resolve.

### D — wire `kata-report` + `kata-evaluate` to require the artifacts
- **owns:** `skills/evaluate/kata-report/SKILL.md`, `skills/evaluate/kata-evaluate/SKILL.md`
- **action:** update the **contracts** (prose): `kata-report` MUST embed/point to the machine-readable
  `RESULT.json` + footprint manifest + mutation-proof result; `kata-evaluate` MUST consume the machine-readable
  `RESULT.json` (verbatim gate output + exit code) rather than a transcribed number, and record baseline+result
  SHAs. Reference A/B/C by contract, not by import.
- **verify:** `uv run python validate_skills.py` (31/0 — wikilinks/frontmatter intact).
- **acceptance:** both skills require the new artifacts; default-FAIL + no-write contracts unchanged. Negative:
  no version bump (Policy A, 0.1.0 hold); no other skill touched.

## Gate (default-FAIL, on the integrated branch)
Full `pytest` (40 existing + A/B/C new) green · `validate_skills.py` 31/0 · Snyk 0 on new Python. Then a
**fresh-context** evaluator (D15) over the integrated diff → SHIP. **Then present the changeset + a recommended
semver and ask the human to select the new version** (the version-up culmination).

## Safety / backout
Restore tag **`pre-dogfood-2`** (pushed). `master` untouched until human version-select. Workers quarantined in
worktrees; bad output never merges (gated). Backout: `git reset --hard pre-dogfood-2` + `git worktree prune`.
