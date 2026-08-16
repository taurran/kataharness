---
spec: trust-model
artifact: evidence note — BL-X14 CI record (the Linux vacuity-prover fix)
task: tm-w1-fix-mutation-prover (wave 1)
date: 2026-08-16
provenance: builder-authored during the task, from `gh run view` / `gh api .../jobs/<id>/logs`
  output on the pushed task branch. Every number below is a verbatim CI line, not a
  reconstruction. Dispatch recorded Honor-system (pre-seam), per BURN-CHARTER.
amended: 2026-08-16 by the same builder, on conductor direction, after wave-1 integration —
  (a) §5 rewritten to record the zero-failure run `31979757460` @ `3f29947` that discharges
  the residual, (b) §4's run-1 `testWentRed` count CORRECTED 46 -> 91 (a too-narrow grep that
  understated pre-fix badness; flagged by the fresh-context judge, re-derived here from the
  raw job-log API). Every fact re-verified with `gh` by the amending builder rather than
  copied from the direction. Amendment leaves §§1-3 unchanged.
branch: task/tm-w1-fix-mutation-prover (amendment authored on task/tm-w1-x14-note-amend off
  burn/trust-model-01 @ 3f29947)
declared-by: PLAN.md `evidence:` -> `artifact:.planning/specs/trust-model/evidence/x14-ci-green.md`
  (PLAN deviation 8: a CI run has no form in the closed evidence grammar, so it is captured
  as a committed evidence-note artifact — declared, not smuggled.)
---

# BL-X14 — CI record: red before, green after

**Bottom line.** On `ubuntu-latest` the gauntlet went from **64 failed / 4460 passed** to
**1 failed / 4538 passed** on the task branch. All 63 mutation-proof failures are closed. The
one remaining failure was **BL-X15**
(`test_statusline_chain.py::TestRunChild::test_empty_argv_fail_soft`), owned by the
`fix-statusline-crash` task and outside this task's ownership.

**Both fixes are now integrated, and the gauntlet is green on both legs** — run
[`31979757460`](https://github.com/taurran/kataharness/actions/runs/31979757460) @
`3f29947`, ubuntu **success** + windows **success**, zero failures. **The X14 acceptance and
the composite "full gauntlet green" are both MET; the Guardian CI-gauntlet row may move
Broken → Verified citing that run (§5).**

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
run-2 ubuntu log (under `-q` it is printed only by a failing mutation assertion), against
**91** occurrences in run 1.

> **CORRECTION (2026-08-16, amendment commit).** This line first read *"against 46
> occurrences in run 1"*. **46 was wrong; the correct count is 91**, re-derived by this task
> from the raw job-log API for job `95240705342` and independently counted at 91 by the
> fresh-context judge. The error was a too-narrow grep: `grep -c "testWentRed': False"` matches
> only the single-quoted verdict dicts inside assertion messages. The full breakdown of the 91
> is `46` single-quoted `testWentRed': False` + `40` `["testWentRed"]` (test source echoed by
> pytest tracebacks) + `5` docstring prose lines — `46 + 40 + 5 = 91`.
> **The correction runs against this note's own interest: it understated how bad the pre-fix
> state was.** The comparison side was never affected — run 2 and the §5 green run were both
> measured with the bare-token method (`grep -o "testWentRed" | wc -l`) and are genuinely `0`;
> only the pre-fix magnitude was undercounted. Re-verified at amendment time: run 1 = **91**,
> run 2 = **0**, green run = **0**, all three by the identical bare-token method.

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

## 5. The zero-failure run — full gauntlet green, ACHIEVED (amended)

**The residual this section recorded is now discharged.** The task-branch runs in §3–§4 left
exactly one failure, BL-X15's `adapters/claude/statusline_chain.py` empty-argv `IndexError`,
owned by the wave-1 task `fix-statusline-crash` and outside this task's ownership (the
BURN-CHARTER anticipated the coupling: *"BL-X15 ... rides X14's run"*). Both fixes have since
been integrated and the gauntlet re-dispatched on the integrated tip.

| | |
|---|---|
| run URL | https://github.com/taurran/kataharness/actions/runs/31979757460 |
| SHA | `3f2994756938b221698ca63637052cb5de2da31a` |
| branch | `burn/trust-model-01` (wave-1 integrated tip) · event `workflow_dispatch` |
| conclusion | **success** |
| `gauntlet (ubuntu-latest)` | **completed / success** — job `95244552908` |
| `gauntlet (windows-latest)` | **completed / success** — job `95244552944` |

Both fixes verified present in that SHA by ancestry, not by assertion:
`git merge-base --is-ancestor` confirms **`e484ce3`** (*"merge(trust-model): integrate
tm-w1-fix-mutation-prover (wave 1)"* — this task) and **`75e215a`** (*"merge(trust-model):
integrate tm-w1-fix-statusline-crash (wave 1)"* — BL-X15) are both ancestors of
`3f29947`.

Verbatim, `ubuntu-latest` (job log `gh api repos/taurran/kataharness/actions/jobs/95244552908/logs`):

```
collected 4560 items
================== 4559 passed, 1 skipped in 80.43s (0:01:20) ==================
Required test coverage of 90.0% reached. Total coverage: 92.49%
collected 4560 items / 4558 deselected / 2 selected
====================== 2 passed, 4558 deselected in 1.93s ======================
```

Verbatim, `windows-latest` (job log `gh api repos/taurran/kataharness/actions/jobs/95244552944/logs`):

```
collected 4560 items
====================== 4560 passed in 255.64s (0:04:15) =======================
collected 4560 items / 4558 deselected / 2 selected
===================== 2 passed, 4558 deselected in 3.04s ======================
```

`FAILED` occurs **0 times** in either job log. `testWentRed` occurs **0 times** in the ubuntu
log — no mutation proof reported a non-biting mutation on Linux.

**Consequence for §3.6 / §6.6 — the acceptance is now MET.** X14's own falsifiable criteria
were already met on the task branch (meta-tests return `{'testWentRed': True}` for biting
mutations; the prover is proven able to fail on Linux — TM-D3 applied to the prover). The
composite criterion that was outstanding, **full gauntlet CI green**, is now satisfied by run
`31979757460` on `3f29947`: zero failures on **both** platform legs.

**The Guardian CI-gauntlet row may therefore move Broken → Verified, citing this run.** Per
§6.6 the citation is what makes BUILT legal — the row is licensed by
`https://github.com/taurran/kataharness/actions/runs/31979757460` @ `3f29947`, not by this
note's say-so. A future run that reds again re-opens it; the transition is a claim about that
SHA, not a permanent property.

**Honesty labels that remain true and are NOT discharged by this run:**

- The **hypothesis-falsification** record (§1) stands unchanged — BL-X14's filed cause was
  wrong, and the BACKLOG entry still carries the falsified text.
- The **`n=1`-per-platform** character of the proof: green on `ubuntu-latest` and
  `windows-latest` runner images at one point in time. No other Linux distro, libc, shell, or
  Python patch level is covered; `/bin/sh` being `dash` on the runner is what made the original
  bug bite, and a different `/bin/sh` was never the fix's dependency but was never tested
  either.
- The mutation re-run's **cost basis** (§4): ~43s added to the ubuntu leg because ~126 real
  proof subprocesses now actually execute. That is a standing cost, not a one-off.
- §3.6's own residual is untouched by any of this: the re-run proves the **claimed** mutation
  set bites; **claimed-set completeness stays worker-asserted**.

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

All verified ancestors of the green run's SHA `3f29947` via `git merge-base --is-ancestor`.

| SHA | what |
|---|---|
| `07d1179` | the E2 falsification probes + the pinning test, **pushed pre-fix on purpose** — the RED half of the record |
| `b996ee1` | the fix: closed-grammar compile to structured argv, `shell=False`, sandbox-containment guarantee |
| `23583a1` | this evidence note, first version |
| `1243aa7` | note update recording the observed run-2 Windows leg |
| `e484ce3` | `merge(trust-model): integrate tm-w1-fix-mutation-prover (wave 1)` |
| `75e215a` | `merge(trust-model): integrate tm-w1-fix-statusline-crash (wave 1)` — BL-X15, the other half of the green run |
| *this commit* | the amendment: §5 zero-failure run recorded, §4 count corrected 46 → 91 |
