# D1 — transient file corruption/revert: ROOT-CAUSED (2026-07-12c)

> Investigation run by a read-only subagent (repro sandbox in session scratchpad; repo untouched).
> Closes the D1 hunt opened in NEXT-SESSION-ORIENTATION Phase D. Code fix = D159 (atomic writes);
> policy fix below. Operator actions flagged ★.

## Verdicts (ranked)

1. **Session A (2026-07-12) "silent mid-session reverts" — CONFIRMED: a `git stash`** executed
   2026-07-12 10:37:39 −0600 in the main tree (almost certainly a subagent/cleanup step during
   branch churn) swept ~25 files of uncommitted edits (+851 lines: 13 tools modules, 8 test files,
   README, STEERING, orchestrate SKILL, validator). **★ The edits are NOT lost — they sit in
   `stash@{0}` right now.** Recovery is an operator decision: `git stash show -p stash@{0}`, diff
   against master (later commits redid some of it), then pop or drop deliberately. Never leave a
   session with a non-empty stash list.
2. **Session B phantom IndentationError (recurrence_detect.py) — mechanism PROVEN:** a concurrent
   **non-atomic truncate-then-write** gives readers empty/partial views. Sandbox repro: fragmented
   rewrite ⇒ **22 IndentationErrors + 26 SyntaxErrors + 193 empty + 70 partial reads in 8 s**;
   single-write truncate-then-write ⇒ 3,992 empty reads; **atomic tmp+`os.replace` ⇒ 0 corruption
   in 12,606 rewrites**. Author of the observed live hit: any truncate-then-write writer (host
   Write/Edit, `--write` regens, git tree rewrites) racing the reader.
3. **Session A function_model corruption — HIGH-MED confidence:** `function_model.py`'s non-atomic
   `write_text` racing parallel comprehension agents. Five non-atomic writers found in `tools/`:
   function_model.py:725 · debug_report.py:692 · benchmark.py:841 · iac_apply.py:697 ·
   intent_scaffold.py:203 → **all converted to atomic in D159.**
4. **RULED OUT:** Windows Defender as corruption cause (real-time ON but the 7/12 Operational log
   has ZERO detection/remediation events; minifilter delays opens, never serves partial content) ·
   `__pycache__`/pyc races (atomic write; a torn pyc is ImportError, never IndentationError) ·
   uv/venv (untouched since Jun 7).

## Standing policy (binding, replaces the "trust the disk" mitigation)

- **The conductor is the SOLE main-tree git writer.** No `git stash`, `git checkout -- .`,
  `git restore`, or branch switch in the shared main tree while any other agent is running;
  subagents mutate only their own worktrees (or run no-git, conductor commits).
- **End-of-session tripwire:** `git stash list` MUST be empty + `git status` reviewed at closeout.
- **Reader retry guard (discipline until wired):** an empty read / FileNotFoundError /
  parse-error-on-a-known-good-file is treated as TRANSIENT — re-read once (~250 ms) before
  declaring failure; capture `len(bytes)` first (a 16 KB-multiple partial is this bug's
  fingerprint).
- All durable artifact writes use the atomic helper (D159); new writers must too (review point).

## Stash forensics (2026-07-12c, operator-present follow-up) — FULLY ACCOUNTED

Line-level sweep of all 25 stashed files (every line the stash added vs its base `9e0d2e0`, checked
against master) + function-level verification of every flagged candidate:

- **Re-applied and merged (verified present in master):** DET-06 footprint `--stat=200` pinning ·
  DET-10 netstring `evidence_digest` · DET-12 drift_gate temp-scrub + separator normalization ·
  benchmark_def `content_addressed_id` · kata_restore/deviation/grounding_gate/benchmark/trail/
  telemetry/contract_gate/graph_gen edits + ALL their test additions · STEERING.md semantics ·
  validate_skills lines. The session visibly re-typed the swept work within the hour (commits
  11:03–11:38) — the discipline held.
- **Deliberately superseded (NOT lost — replaced by the adval-R1 decision):** the stash's BLANKET
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD` + shell-to-argv rework of mutation_check/mutation_run and their
  tests; master carries the post-R1 SURGICAL form (`-p no:randomly` on the pytest path; blanket env
  + retained `shell=True` only on the arbitrary-command path) with its own tests.
- **GENUINELY LOST (one artifact, ~20 lines): `test_diff_stat_argv_pins_fixed_width`** — the DET-06
  mutation-guard test. The FEATURE shipped; its pin-test didn't, so a refactor could have silently
  dropped `--stat=200` unnoticed. **RECOVERED from the stash 2026-07-12c** (test_footprint.py,
  adapted verbatim — it was drop-in compatible).

**MindBridge export implication:** the export reads GitHub/master — a stash is INVISIBLE to it.
With the one lost test recovered, master now contains 100% of the stashed work (as-merged or
deliberately-superseded), so the export misses nothing from this incident. The standing protection
is the closeout tripwire: `git stash list` empty = nothing export-invisible left behind.

**Stash disposition:** fully accounted; nothing further to recover → safe to `git stash drop`
(operator's call — the forensics above is the durable record).

## ★ Operator actions at return

1. Decide `stash@{0}`: **forensics complete (above) — safe to drop**; or keep as artifact.
2. Optional: Defender exclusion for `C:\Dev` (admin) — not required for correctness, reduces lock
   amplification under heavy parallel I/O.

Repro harnesses (kept for re-verification): session scratchpad `d1-corruption/` (`race_harness.py`,
`git_race.py`).
