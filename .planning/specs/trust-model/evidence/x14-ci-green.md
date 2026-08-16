---
spec: trust-model
artifact: evidence note — BL-X14 CI record (the Linux vacuity-prover fix)
task: tm-w1-fix-mutation-prover (wave 1)
date: 2026-08-16
provenance: builder-authored during the task, from `gh run view` / `gh api .../jobs/<id>/logs`
  output on the pushed task branch. Every number below is a verbatim CI line, not a
  reconstruction. Dispatch recorded Honor-system (pre-seam), per BURN-CHARTER.
branch: task/tm-w1-fix-mutation-prover
declared-by: PLAN.md `evidence:` -> `artifact:.planning/specs/trust-model/evidence/x14-ci-green.md`
  (PLAN deviation 8: a CI run has no form in the closed evidence grammar, so it is captured
  as a committed evidence-note artifact — declared, not smuggled.)
---

# BL-X14 — CI record: red before, green after

**Bottom line.** On `ubuntu-latest` the gauntlet went from **64 failed / 4460 passed** to
**1 failed / 4538 passed**. All 63 mutation-proof failures are closed. The single remaining
failure is **BL-X15** (`test_statusline_chain.py::TestRunChild::test_empty_argv_fail_soft`),
which belongs to the `fix-statusline-crash` task and is outside this task's ownership — see
§5. **This note therefore records the X14 acceptance as met and the composite
"full gauntlet green" as blocked on X15, not achieved.**

## 1. The stated hypothesis was FALSIFIED (escalation rule E2)

BL-X14 recorded, explicitly as a working hypothesis to verify:

> in the CI environment the sandboxed mutated copy is never what the re-run imports
> (live/installed module resolves instead — `_redirect_cmd`'s residual-live-root guard checks
> the command argv, not the import path/environment)

That is **not** the mechanism. `_redirect_cmd`, the residual live-root guard, and the sandbox
copy are all correct and were never the problem. Nothing was ever imported at all, because the
command never ran.

**The observed mechanism.** Every mutation-proof caller in the repo builds the command shape
`cd /d "<dir>" && <py> -m pytest "<node-id>" -q --tb=no` (12 files: `test_benchmark`,
`test_benchmark_control`, `test_benchmark_def`, `test_debug_report`, `test_deviation`,
`test_drift_gate`, `test_escalation`, `test_iac_apply`, `test_recall`,
`test_recurrence_detect`, `test_usage_meter`, `test_validation_misses`). `cd /d` is a
**cmd.exe builtin flag**. The sink ran the string under `shell=True`, which on POSIX invokes
`/bin/sh`, whose `cd` takes one operand — so the `&&` chain short-circuited before `pytest`
was ever reached. Both the baseline run and the mutated run reported failure, and
`mutation_verdict(False, False)` is `{'testWentRed': False, 'nonVacuous': False}` — identical
to the verdict a genuine import-resolution bug would produce. **That collision is why the
wrong cause stayed on record for 12 days: the verdict dict alone cannot distinguish
"the command never ran" from "the live module answered the import".**

## 2. Reproduction environment (why CI, and not a container)

No Linux was available locally on the builder host — `wsl --status` reports
*"The Windows Subsystem for Linux is not installed"*, and `docker` is *"command not found"*.
Per the brief's stated preference order, the reproduction ran on the **ubuntu-latest CI leg**
of the pushed task branch (`workflow_dispatch`; the gauntlet's `on:` triggers are
`push: [master]`, `pull_request`, `workflow_dispatch`, so dispatching the task branch needed
neither a PR nor any workflow edit).

**Declared deviation from the brief.** The brief asked that the new isolation test be proven
red-against-pre-fix "by temporarily reverting the fix locally and recording the red output".
A local Windows revert cannot produce that red — the bug is Linux-only and the pre-fix code
passes on Windows. The proof used instead is stronger and is a real machine record: the test
was **committed and pushed BEFORE the fix** (`07d1179`) and observed failing on ubuntu in CI
run 1, then observed passing after the fix (`b996ee1`) in CI run 2. Same test, same
environment, fix as the only variable.

## 3. BEFORE — CI run 1 (pre-fix)

| | |
|---|---|
| run URL | https://github.com/taurran/kataharness/actions/runs/31978174967 |
| SHA | `07d1179a9697ec076d7be15b06e0a7cc769cf288` |
| conclusion | **failure** (`ubuntu-latest`: failure · `windows-latest`: success) |
| ubuntu job log | `gh api repos/taurran/kataharness/actions/jobs/95240705342/logs` |

```
collected 4525 items
================= 64 failed, 4460 passed, 1 skipped in 37.67s ==================
```

That matches BL-X14's filed measurement (62 failed / 4460 passed) plus the two probe tests
this task added in `07d1179`.

**The mechanism, verbatim from the ubuntu log** (temporary E2 repro probe
`test_x14_probe_live_cmd_shape_executes_on_this_platform`, deleted with the fix):

```
E  AssertionError: BL-X14 REPRO: the live mutation `test_cmd` shape is cmd.exe-only — it does
   not execute under this platform's shell, so every mutation proof is vacuous here.
   os.name='posix' rc=2 stdout='' stderr="/bin/sh: 1: cd: can't cd to /d\n"
   cmd='cd /d "/tmp/pytest-of-runner/pytest-0/test_x14_probe_live_cmd_shape_0/work" &&
        "/home/runner/work/kataharness/kataharness/tools/.venv/bin/python" -c "print(42)"'
```

**The discriminator, verbatim** (the pinning test
`test_sandbox_import_isolation_linux`, which asserts the *pair* of run outcomes rather than
only the verdict dict — precisely so the two candidate mechanisms separate):

```
FAILED tests/test_mutation_run.py::test_sandbox_import_isolation_linux -
AssertionError: BL-X14: the BASELINE run failed on the PRISTINE sandbox copy — the mutation
proof is vacuous by construction on this platform (os.name='posix', outcomes=[False, False],
verdict={'testWentRed': False, 'nonVacuous': False},
cmd='cd /d "/tmp/pytest-of-runner/pytest-0/test_sandbox_import_isolation_0" &&
     "/home/runner/work/kataharness/kataharness/tools/.venv/bin/python" -m pytest
     "tests/test_sample.py::test_classify_negative" -q --tb=no').
The command never ran as intended.
```

`outcomes=[False, False]` is the falsification. Under the recorded import-resolution
hypothesis the baseline would have PASSED and the mutated run would also have passed —
`[True, True]`. The **baseline failed on the pristine, unmutated sandbox copy**.

Pre-fix failures by file (64 total):

| file | n | | file | n |
|---|---|---|---|---|
| `test_recall.py` | 10 | | `test_benchmark_def.py` | 4 |
| `test_benchmark.py` | 8 | | `test_deviation.py` | 3 |
| `test_recurrence_detect.py` | 7 | | `test_benchmark_control.py` | 3 |
| `test_iac_apply.py` | 6 | | `test_validation_misses.py` | 2 |
| `test_debug_report.py` | 6 | | `test_mutation_run.py` | 2 (this task's probes) |
| `test_usage_meter.py` | 5 | | `test_escalation.py` | 2 |
| `test_drift_gate.py` | 5 | | `test_statusline_chain.py` | **1 (BL-X15, not X14)** |

## 4. AFTER — CI run 2 (post-fix)

| | |
|---|---|
| run URL | https://github.com/taurran/kataharness/actions/runs/31978557692 |
| SHA | `b996ee17a3d3f0fa764380e646f25205fcf7e18f` |
| ubuntu leg | **1 failed / 4538 passed** — the one failure is BL-X15, not a mutation proof |
| ubuntu job log | `gh api repos/taurran/kataharness/actions/jobs/95241647012/logs` |

```
collected 4540 items
============= 1 failed, 4538 passed, 1 skipped in 80.72s (0:01:20) =============
FAILED tests/test_statusline_chain.py::TestRunChild::test_empty_argv_fail_soft -
IndexError: list index out of range
Required test coverage of 90.0% reached. Total coverage: 92.45%
```

**All 63 mutation-proof failures closed.** The string `testWentRed` occurs **0 times** in the
run-2 ubuntu log (under `-q` it is printed only by a failing mutation assertion), against 46
occurrences in run 1.

**Machine confirmation for `test_sandbox_import_isolation_linux` specifically**, since `-q`
names only failures: collected went `4525 -> 4540` (**+15**, exactly the tests added in
`b996ee1`: `39 - 24` in `test_mutation_run.py`), the test is absent from run 2's FAILED list,
and `4460 + 64 + 15 = 4538 + 1 = 4540` closes exactly. It was collected and it passed on
ubuntu-latest.

**A second, independent signal that the proofs now really execute:** the suite went from
**37.67s to 80.72s**. The +43s is the mutation work that was previously short-circuiting in
the shell — roughly 126 real pytest subprocesses (63 proofs × baseline + mutated) that never
ran on Linux before.

**Windows leg, same SHA: success** (job log
`gh api repos/taurran/kataharness/actions/jobs/95241647039/logs`) — the platform the fix had
to not regress:

```
collected 4540 items
====================== 4540 passed in 267.90s (0:04:27) =======================
collected 4540 items / 4538 deselected / 2 selected
===================== 2 passed, 4538 deselected in 2.90s ======================
```

Zero failures on Windows against 1 (BL-X15) on ubuntu: the closed grammar parses the existing
caller corpus with identical meaning on both platforms, which was the point.

## 5. Honest residual — "full gauntlet CI green" is NOT achieved on this branch

The task acceptance reads "full gauntlet CI green on the pushed branch". It is not, and this
task cannot make it so:

- The remaining failure is `adapters/claude/statusline_chain.py`'s empty-argv `IndexError`
  — **BL-X15**, owned by the wave-1 task `fix-statusline-crash`.
- `.planning/specs/trust-model/PLAN.md` assigns that file to that task; touching it here would
  be an ownership violation. The BURN-CHARTER already anticipated this coupling
  ("BL-X15 ... rides X14's run").

**Consequence for §3.6 / §6.6.** X14's own falsifiable criteria are met on ubuntu-latest — the
meta-tests return `{'testWentRed': True}` for biting mutations, and the prover is proven able
to fail on Linux (TM-D3 applied to the prover). But the Guardian **Broken -> Verified**
transition for the CI gauntlet needs a run with **zero** failures, which requires X15's fix on
the same branch or after both merge. **Until such a run exists and is recorded here, the
gauntlet stays Broken.** A re-dispatch of `gh workflow run gauntlet --ref <branch>` after X15
lands closes it; this note should be amended with that run's URL + SHA at that point.

## 6. Local verification (builder host, Windows 11, Python 3.14.3)

```
tools> uv run python -m pytest tests/test_mutation_run.py -q     ->  39 passed in 0.78s
tools> uv run python -m pytest -q                                ->  4537 passed, 3 skipped in 157.42s
tools> uv run python -m pytest -m integration -q                 ->  2 passed, 4538 deselected
tools> uvx ruff check .                                          ->  All checks passed!
tools> uv run python validate_skills.py                          ->  49 skills checked, 0 errors, 0 warnings
```

`shell=True` is absent from the mutation sink's code — AST-pinned by the new
`test_mutation_sink_source_contains_no_shell_true` (an AST check, so the surviving prose
mentions in the module docstring can neither satisfy nor break it).

Snyk Code scan over `tools/`: **0 findings in `mutation_run.py` or `test_mutation_run.py`**
(93 repo-wide, all `Low`, all pre-existing `HardcodedNonCryptoSecret` hits in unrelated test
fixtures).

## 7. Commits

| SHA | what |
|---|---|
| `07d1179` | the E2 falsification probes + the pinning test, **pushed pre-fix on purpose** — the RED half of the record |
| `b996ee1` | the fix: closed-grammar compile to structured argv, `shell=False`, sandbox-containment guarantee |
