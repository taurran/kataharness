---
spec: inline-eval-m4
phase: M4-P0
title: telemetry — the measurement substrate (record everything, act on nothing)
status: frozen
created: 2026-07-04
revised: 2026-07-04 (v3 — gate v1 HOLD folded; re-gate v2 SHIP-WITH-FIXES, all 11 fixes folded; FROZEN)
branch: m4/inline-eval
baseline: 1cd1a60 (DESIGN frozen; pytest 2306/3 skip, validator 47/0/0, Snyk medium+ 0)
tags: [kata/freeze-float, plan, inline-eval, telemetry, M4-P0]
---

# M4-P0 — telemetry (pure measurement; NO scheduling/gating/recovery behavior change)

## Gate history
- **Re-gate v2 (2026-07-04): SHIP-WITH-FIXES — FROZEN after fold.** 13/15 v1 folds verified landed
  (MED-5/MED-11 PARTIAL → completed by the F2/F3 folds). Fresh catches, all folded: **F1** the T5
  n=1 wall-clock A/B could not honestly resolve a <1% threshold (the D16/A4 precedent) → kill-switch
  redefined over mechanical per-chunk overhead (exact tool-call counts + brief token size), wall-clock
  reported directional/exercised-not-proven; **F2** `uv run --directory` changes CWD to the harness
  tools dir — the CLI would have digested the WRONG REPO at every checkpoint → required `--repo-root`;
  **F3** rename detection silently drops `old:ABSENT` + makes the digest git-config-dependent →
  `--no-renames` + `core.quotepath=off` pinned on both the CLI default and `checkpoint_changed_files`
  (+ rename test); **F4** `telemetryLedger` was never set anywhere + read/append resolution was
  asymmetric → T4 sets + documents the key; identical resolution both directions; **F5** the
  tools-dir-unresolvable degrade now records `effectiveMode: "off"` (existing taxonomy, not a third
  shape); **F6** calibration rows marked `"calibration": true` and EXCLUDED from `class_median` (toy
  durations must not bias real medians); **F7** the three `kata-plan-<tier>` skills get PATCH bumps
  (the RUBRIC is their behavior); **F8** ledger-append approval recorded as a board `DECISION`;
  **F9** root-commit parent tree = empty (right error class); **F10** empty-staging maps to a
  worker-facing stage-first error; **F11** T5 run-shape pinned (one skeleton, two fresh clones, same
  frozen mini-PLAN, config differs only in `inlineEval`, model constant).
- **Freeze-gate v1 (2026-07-04): HOLD** — 1 BLOCKER + 3 HIGH + 7 MED + 4 LOW, all folded. Headline:
  the plan had silently relocated the frozen STOP-at-P0 kill-switch to P1 (BLOCKER → T5 instrumented
  calibration run added, criterion 6 rewritten); `estimate:` docs homed in prose that does not exist
  (→ kata-plan RUBRIC, T3.3); the ledger append's "human-gated" property was asserted but not carried
  by step 8's bare "Commit" (→ approval requirement stated at the append site); new subprocess-git
  sinks had no exec-safety registry owner (→ T1.8 — the D140 accepted-deviation class closed at
  freeze). Plus: CLI staged-paths default fixed to `git diff --cached --name-only` (deletion
  detectability); verify-mode parent-tree deletion semantics; lane-check blocking posture scope
  guard; stage→emit→commit ordering mandate; `missing_ok` deleted (dangling configured path raises);
  acceptance keyed class×tier + verify counts carried; cross-repo CLI invocation form; corrupted
  unattributable board line documented as fail-safe; bootstrap 0.2.0; DESIGN status-note anchor;
  kata_trail sentinel dict shape.

Implements M4-L10 + the A1-Q2/A1-Q3 transports as amended (DESIGN FROZEN 2026-07-04). P0 records
signal vectors and builds the calibration substrate; it computes **no risk score, no τ, no triggers,
no ladder, no kills** (all P1). BC: `kata.config.inlineEval` absent ⇒ `off` ⇒ byte-for-byte today's
behavior (no mandate text enters any worker brief; no artifact is written). The honest P0 behavior
delta (DESIGN criterion 3 as amended): in `telemetry`/`on` modes the worker dispatch brief GAINS the
checkpoint-commit + trailer mandate — that mandate's cost is what the <1% instrument measures.

## Ownership (disjoint) + DAG

```yaml
ownership:
  T1: [tools/kata_telemetry.py, tools/tests/test_kata_telemetry.py, protocol/exec-safety.md]
  T2: [skills/coordinate/kata-orchestrate/SKILL.md, protocol/config.md]
  T3: [skills/execute/kata-tdd/SKILL.md, skills/coordinate/kata-bootstrap/SKILL.md, skills/plan/kata-plan/RUBRIC.md, skills/plan/kata-plan-essential/SKILL.md, skills/plan/kata-plan-standard/SKILL.md, skills/plan/kata-plan-advanced/SKILL.md]
waves:
  wave1: [T1]
  wave2: [T2, T3]
depends_on:
  T2: [T1]
  T3: [T1]
```

T4 (closeout, conductor-owned): create `.planning/telemetry-ledger.md` (header + row schema §T1.6),
**set `telemetryLedger` (absolute path to the harness-repo ledger) in the harness-home
`.kata-settings.json` + document the key** (gate v2 F4a — without it T5's target-repo run hits the
absent-locator fail-safe and AC-6's "≥1 real ledger row" is mechanically unmeetable), README
skill-index regen (`validate_skills --write`), CHANGELOG entry, a dated P0-status note in the
DESIGN's gate-history section (gate v1 LOW-14 — the DESIGN has no "Phasing" section; never invent an
anchor on a FROZEN doc). **Read/append symmetry (gate v2 F4b):** the ledger path resolves
IDENTICALLY for the read path (T2.4 class-median source) and the append path (T2.5) — harness-repo
run ⇒ local `.planning/telemetry-ledger.md` for BOTH; target-repo run ⇒ the `telemetryLedger`
locator for BOTH; never one rule for reads and another for appends.

**T5 (conductor-owned, AFTER T1–T4 integrate) — instrumented calibration run #1 (gate v1 BLOCKER-1
fold; the frozen STOP-at-P0 kill-switch decision point stays IN P0).** One small real run with
`inlineEval: "telemetry"`, **run-shape pinned (gate v2 F11):** ONE scratch skeleton, TWO fresh
clones (one per arm), the SAME frozen 2-task mini-PLAN + `kata.config` differing ONLY in
`inlineEval` (`off` vs `telemetry`), model resolution held constant across arms (D131 per-skill-slot
constancy). Telemetry arm: workers dispatched with the checkpoint mandate, per-task telemetry
emitted, **≥1 ledger row appended** (board-`DECISION`-recorded operator approval — gate v2 F8; the
row carries `"calibration": true`, gate v2 F6 — `class_median` EXCLUDES calibration rows so toy
durations never bias real medians; the documented alternative of counting them was rejected: A1-Q3
names bad estimates as THE false-trigger source). **Measurement honesty (gate v2 F1 — the D16/A4
n=1 precedent):** the kill-switch call is defined over the honest measurables — the MECHANICAL
per-chunk overhead (added tool calls per checkpoint: emit-trailer + commit, counted exactly; the
mandate's brief token size where surfaced) bounded worst-case against the §1 waste pool; the
wall-clock A/B is reported as **directional / exercised-not-proven, n=1** (never presented as
resolving a 1% threshold — LLM-agent wall-clock variance exceeds it by orders of magnitude).
Output = the P0 REPORT to the operator: machinery numbers + first-run rows + the mechanical
overhead bound + the directional wall-clock + the explicit kill-switch call (proceed to P1 / STOP
at P0 per the frozen DESIGN — telemetry retained, mechanism shelved).

Build mode: **direct with dispatched workers** (one agent per task, disjoint files, conductor
integrates + commits on the branch — the D137-L8 direct pattern; P1 dogfoods). Build workers tier
down per D131 (coding class); gates run at anchor.

## T1 — `tools/kata_telemetry.py` (code-bearing; TDD + mutation proofs; stdlib-only)

All functions that PARSE an external artifact to feed a decision or a record are **fail-closed
(D136)**: absent/unparseable input RAISES `TelemetryError` (a named exception), never a permissive
default. Telemetry WRITES are fail-soft (observability): a write failure returns/raises to the
caller-documented NOTE path, never gates. No third-party imports; git via `subprocess.run(list)`
(the exec-safety registry pattern — no `shell=True`).

1. **`parse_checkpoint_trailer(body: str) -> dict | None`** — extract the `Kata-Checkpoint: {json}`
   trailer from ONE commit-message body. Zero trailers ⇒ `None` (a plain commit — NOT malformed).
   **RAISES** on: >1 trailer (v2-MED-5 — ambiguous evidence, never first/last-wins), JSON parse
   failure, or schema violation. Required keys (schema v1): `v == 1`, `i` (int ≥ 0), `verify.exit`
   (int). Optional nullable: `verify.passed/failed/skipped` (ints), `lint` (int), `evidence`
   (sha256 hex string). Unknown keys tolerated (forward-compat, additive).
2. **`scan_checkpoints(repo_root, branch, integration_ref) -> list[dict]`** — the task's own
   commits via `git rev-list --reverse <branch> ^<integration_ref>` (two-dot log semantics — no
   merge-base ambiguity for a LOG walk), then per commit `git show -s --format=%P%n%B`: a commit
   with >1 parent (merge) carrying a trailer ⇒ **RAISES** (v2-MED-5; a trailer-free merge commit is
   skipped, not an error); otherwise → `{sha, record: dict|None}` via #1. Any git error ⇒ **RAISES**
   (D139 — never `[]` on a git failure). Oldest-first output; the caller derives streaks from order.
3. **`evidence_digest(repo_root, paths, *, commit: str|None) -> str`** — sha256 over sorted
   `"<path>:<blob-sha>"` entries. **Worker/stamp mode (`commit=None`):** staged blob hashes via
   `git ls-files -s -- <paths>` (the index IS the future commit's tree for those paths — resolves
   the author-time chicken-and-egg: the trailer is written into the message of the commit whose tree
   it describes; parse only the blob SHA column — ls-files carries stage numbers, ls-tree carries
   object types; the BLOB SHA is the invariant). A path absent from the index but present in the
   path list ⇒ check HEAD: tracked-in-HEAD + absent-from-index ⇒ entry `"<path>:ABSENT"` (a staged
   deletion, detectable); never-tracked + not-staged ⇒ **RAISES** (unresolvable path — loud, never
   hashed-as-missing). **Verify/gate mode (`commit=<sha>`):** the same entries from
   `git ls-tree <sha> -- <paths>`; **deletion semantics (gate v1 MED-6):** a path absent from
   `<sha>`'s tree ⇒ check the parent tree `<sha>^`: present-in-parent ⇒ `"<path>:ABSENT"` (deleted
   by this chunk — round-trips the stamp-mode entry); absent-from-both ⇒ **RAISES** (never
   existed — unresolvable, mirrors stamp mode); a ROOT commit (no parent) treats the parent tree as
   EMPTY ⇒ the never-existed raise, not a generic git error (gate v2 F9 — the right error class for
   a greenfield first checkpoint). Identical values across modes by the git object
   model. Empty `paths` ⇒ **RAISES** (a digest over nothing is a vacuous pin — the D131 0-of-0
   lesson). Forward-slash path normalization on both modes (Windows).
4. **`validate_inline_eval(value) -> str`** — the mechanical leg of the config load-guard:
   `None` ⇒ `"off"` (absent ⇒ off, the BC fail-safe, documented); exactly `"off"|"telemetry"|"on"`
   ⇒ itself; ANYTHING else (case-variant, wrong type, unknown string) ⇒ **RAISES** (MED-9a — the
   orchestrator's prose response is STOP + escalate, GB12/D45 posture).
5. **Slack substrate (A1-Q3, scheduler-computed — P0 records it, P1 scores it):**
   - `parse_progress_events(board_text, task_id) -> list[dict]` — `{ts, done, owned}` from the
     task's `PROGRESS` lines (`protocol/board.md` format); a malformed done/owned msg on a PROGRESS
     line for THIS task ⇒ **RAISES**; other tasks' lines and non-PROGRESS types are ignored
     (the board legitimately holds them). **Documented fail-safe (gate v1 LOW-12):** a corrupted
     line that no longer splits into 5 fields is UNATTRIBUTABLE (its task-id field is unreadable)
     and is skipped — the board-snippet skip precedent (`protocol/board.md` concurrency snippet),
     stated, not implied. Board format itself is UNTOUCHED.
   - `read_ledger(path) -> list[dict]` — parses row-lines (one JSON object per line, after the
     header block); a malformed row ⇒ **RAISES** (MED-9b — never skip-and-average); a missing FILE
     ⇒ **RAISES, always** (gate v1 MED-9: A1-Q3's documented fail-safe is the `telemetryLedger`
     SETTING being absent — in which case `read_ledger` is never called; a configured-but-dangling
     path is a present-but-broken pointer ⇒ GB12/D45 raise. No `missing_ok` parameter exists).
   - `class_median(rows, task_class, min_samples=5) -> float | None` — median of per-task duration
     samples for the class; `< min_samples` ⇒ `None` (documented fall-through, A1-Q3).
   - `resolve_estimate(median, frontmatter_estimate) -> tuple[float|None, str]` — precedence
     ledger-median → frontmatter → `(None, "absent")`; a present-but-non-numeric frontmatter value
     ⇒ **RAISES** (freeze-time validation is T3 prose; this is the runtime backstop).
   - `slack_ratio(events, estimate_min, now_utc) -> float | None` — progress-normalized
     `elapsed / (estimate × done/owned)`; `estimate is None` OR `done == 0` ⇒ `None`
     (v2-MED-6 — never a manufactured early trigger); non-monotonic/unparseable timestamps ⇒ RAISES.
6. **Records + ledger rows:**
   - `build_task_telemetry(...) -> dict` — schema v1: `{v, taskId, class, tier, effectiveMode,
     chunkCount, checkpoints: [{i, sha, verifyExit, verifyPassed, verifyFailed, verifySkipped,
     lint, evidence, laneDrift: [paths], slack}], firstTripIndex: null, ladderEvents: [],
     gateVerdict, fixCycles, wallClockS, tokensIn: null|int, tokensOut: null|int, utc}` —
     checkpoint entries carry the verify COUNTS the trailer already parses (gate v1 MED-10; M4-L6's
     "pass/fail/delta" signal needs them); `firstTripIndex`/`ladderEvents` are SCHEMA'd now, always
     null/empty in P0 (no triggers exist); nullable tokens per the usage_meter honesty.
   - `write_task_telemetry(kata_dir, record)` → `.kata/telemetry/<taskId>.json` (fail-soft: OSError
     is caught and returned as a `{"skipped": "<reason>"}` dict — the exact `kata_trail` sentinel
     shape, gate v1 LOW-15 — surfaced as a NOTE by the caller).
   - `checkpoint_changed_files(repo_root, sha) -> list[str]` — `git show --name-only --format=`
     for the single commit (merge commits never reach here — excluded in #2); git error ⇒ RAISES.
     Per-checkpoint lane drift = `footprint.partition(changed, ownership)["out_of_footprint"]`
     (REUSES footprint — no reimplementation).
   - `build_ledger_row(run_summary: dict) -> str` — one-line JSON row, schema v1:
     `{v, utc, runId, target, tasks, checkpoints, zeroCheckpointTasks,
     firstPassAcceptanceByClassTier, streaksByClass, fixCycles, gateRejections,
     taskDurationsByClass, wallClockS, tokensIn, tokensOut, effectiveModes}` —
     `firstPassAcceptanceByClassTier` is keyed `"<class>×<tier>"` (gate v1 MED-10; M4-L10/M4-L7's
     acceptance-per-(class×tier) routing report needs the keys, not a bare rate);
     `zeroCheckpointTasks` = the LOW-12 tell. `append_ledger_row(path, row)` — append-only; never
     creates the file (the ledger file is a committed, header-carrying artifact — T4 creates it;
     append to a missing file ⇒ RAISES).
7. **CLI (worker tooling):** `python -m kata_telemetry emit-trailer --index N --verify-exit E
   [--passed/--failed/--skipped N] [--lint E] [--paths ...]` — computes the staged-mode evidence
   digest and prints the complete single-line `Kata-Checkpoint: {...}` trailer to stdout. Workers
   never hand-author trailer JSON. **Required `--repo-root <path>` (gate v2 F2):** all git calls
   run against it — the orchestrator injects the worker's WORKTREE root into the command (the
   `uv run --directory <tools-dir>` prefix changes CWD to the harness tools dir, so a CWD-relative
   default would digest the wrong repo and raise empty-paths at every checkpoint; the board-snippet
   pass-the-path-as-argv discipline). **Default paths = `git -c core.quotepath=off diff --cached
   --name-only --no-renames`** (gate v1 MED-5 + gate v2 F3 — `ls-files -s` emits nothing for a
   staged deletion; rename detection reports only the destination AND is `diff.renames`
   config-dependent, silently dropping `old:ABSENT` and making the digest non-deterministic across
   operator configs; `--no-renames` + quotepath pin both — the `changed_in_task` F5-1 precedent
   verbatim; the same flags apply to `checkpoint_changed_files`). Empty staging area ⇒ a
   worker-facing "nothing staged — stage the chunk before emitting" error (gate v2 F10 — maps the
   vacuous-pin raise to the T3.1 ordering mandate, same loud outcome). Named tests: CLI default
   with a staged deletion ⇒ `path:ABSENT` in the digest; staged RENAME ⇒ `old:ABSENT` AND
   `new:<blob>` both present; absent `--repo-root` ⇒ usage error (the flag is required).
8. **Exec-safety registry (gate v1 HIGH-4 — the D140 accepted-deviation class, closed at freeze
   this time):** T1 adds descriptive registry rows to `protocol/exec-safety.md` for the new
   subprocess-git sinks (`scan_checkpoints`, `evidence_digest`, `checkpoint_changed_files`,
   CLI emit-trailer) — list-form `subprocess.run`, no `shell=True`, same posture as the
   `contract_gate._scan_integration_commits` row.

**Test obligations (TDD, D136-guard tests, mutation proofs):** every RAISES clause above has a named
test proving loud failure on absent/malformed input; BC tests: `validate_inline_eval(None) == "off"`;
`parse_checkpoint_trailer` on a plain commit body ⇒ None; digest stamp-mode == verify-mode on a real
tmp-repo commit (round-trip test); deletion → `path:ABSENT` detectable (≠ pre-deletion digest);
duplicate-trailer and trailer-on-merge raises; empty-paths digest raise; ledger malformed-row raise;
append-to-missing-ledger raise; zero-progress slack None; ≥6 mutation proofs on the decision guards
(each: disable guard → named test goes red → revert), recorded for the D-record.

## T2 — kata-orchestrate 0.5.0 → 0.6.0 + protocol/config.md (prose)

1. **config.md:** add the `inlineEval` row — `"off" | "telemetry" | "on"`; **absent ⇒ `off`,
   byte-for-byte BC**; present-but-malformed ⇒ load-guard **STOP + escalate** (D45/GB12 posture,
   validated mechanically via `kata_telemetry.validate_inline_eval`); `telemetry` = record-only
   (adds the worker checkpoint mandate; NO trigger/ladder/kill); `on` = P1 (documented as
   not-yet-consumed until P1 lands — honest, the `extraScanners` precedent). *(Gate v1 HIGH-2 fold:
   `estimate:` is NOT documented here — config.md documents the `kata.config` schema only; the task
   field homes in `kata-plan/RUBRIC.md` → T3.3.)*
2. **Load-guard (precondition 0):** add `inlineEval` to the strict-validation list (malformed ⇒
   STOP; the mechanical check is `validate_inline_eval`).
3. **Dispatch template (loop step 2):** when effective mode ≠ `off`, the worker prompt additionally
   mandates: commit at each **owned-module completion** (the F3 `done/owned` unit — one checkpoint
   commit per module, same boundary as the PROGRESS line; conventional message; NO `Kata-Task:`
   trailer — that stays integration-only) carrying exactly ONE `Kata-Checkpoint:` trailer emitted
   via the T1 CLI (never hand-authored, never on a merge commit); mechanical outputs only (exit
   codes/counts — never self-assessment, D33 boundary as amended). **Invocation form (gate v1
   MED-11):** the orchestrator resolves its own harness `tools/` directory at dispatch time and
   injects the CONCRETE command into the brief (`uv run --directory <resolved-tools-dir> python -m
   kata_telemetry emit-trailer ...` — the `protocol/board.md` run-form precedent); a worker in a
   target worktree never guesses a path. If the orchestrator cannot resolve its tools dir, the
   mandate is omitted and the task's `effectiveMode` is recorded `"off"` (mandate not dispatched)
   with a board NOTE — the EXISTING per-task effective-mode degrade taxonomy (M4-L10 as amended /
   v2-LOW-10), NOT a third degrade shape; the task then shows in `zeroCheckpointTasks` only as the
   arithmetic consequence, and the ledger distinguishes cause by mode (gate v2 F5).
4. **Per-task telemetry step (gate step 3, after the lane check):** when mode ≠ `off`, scan the
   task's branch (`kata_telemetry.scan_checkpoints`), compute per-checkpoint lane drift + slack
   (PROGRESS events + `resolve_estimate` with the ledger source per A1-Q3), and
   `write_task_telemetry` → `.kata/telemetry/<taskId>.json`. A task that reports DONE with ZERO
   checkpoint commits under mode ≠ off ⇒ record `zeroCheckpointTasks` (LOW-12 tell) — **a NOTE,
   never a gate**. A RAISE from the ADDITIONAL per-checkpoint telemetry computation
   (`scan_checkpoints`, per-checkpoint drift, slack) ⇒ surface + record in the task telemetry as a
   malformed-signal event — in P0 this never blocks the task (detection-only; the
   treat-as-triggered response is P1's). **Scope guard (gate v1 MED-7):** the EXISTING gate-step-3
   lane check — its own `footprint.changed_in_task` invocation and its BLOCKING posture on a raise
   (multi-merge-base, F5-2/D136) — is **byte-for-byte untouched**; "never blocks" governs ONLY the
   new telemetry computation, never the task gate (M4-L8).
5. **Closeout (final gate step 8):** build the run summary + `build_ledger_row`; resolve the ledger
   path — **harness-repo run ⇒ the local `.planning/telemetry-ledger.md` directly; target-repo run
   ⇒ the `telemetryLedger` locator in `.kata-settings.json`** (gate v1 HIGH-3 pin; absent locator ⇒
   source-absent fail-safe: row written to `.kata/telemetry/ledger-row.pending.json`, surfaced);
   append via `append_ledger_row`. **The authored step-8 text itself states the approval
   requirement (gate v1 HIGH-3):** the commit carrying the ledger row is made ONLY on explicit
   operator approval recorded at the append site — step 8's bare "Commit" is not self-authorizing
   for this row, and D141(b) forbids creating an autonomous-git path by implication; ledger outside
   the target repo ⇒ request the SECOND explicitly human-gated commit in the ledger's repo;
   declined/failed ⇒ surfaced pending-uncommitted (v2-HIGH-2). Version-bump discipline: 0.6.0,
   bump-on-modify.

## T3 — kata-tdd 0.1.1 → 0.2.0 + kata-bootstrap 0.1.3 → 0.2.0 + kata-plan RUBRIC (prose)

1. **kata-tdd:** a "checkpoint cadence (M4)" subsection: when the dispatch brief carries the
   checkpoint mandate, commit at each owned-module completion with the CLI-emitted trailer; the
   trailer carries mechanical verify outputs only; workers never write `Kata-Task:` (integration
   trailer, orchestrator-only), never commit on a merge, never author two trailers. **Ordering
   mandate (gate v1 MED-8):** stage EVERYTHING the chunk changed → emit the trailer (the digest
   reads the index) → commit IMMEDIATELY — no edits between emit and commit (a mis-ordered worker
   stamps a digest that diverges from the commit tree; P1's verify-mode re-derivation is the
   eventual detector, but P0 calibration data must not be polluted). Absent the mandate in the
   brief ⇒ this section is inert (BC).
2. **kata-bootstrap (0.1.3 → 0.2.0, gate v1 LOW-13):** new-run configs get
   `inlineEval: "telemetry"` (M4-L8 bootstrap default); document the "offers `on` once the ledger
   holds ≥3 runs" forward rule.
3. **kata-plan/RUBRIC.md (gate v1 HIGH-2 — the estimate's real home, per the DESIGN change-surface
   list + LOW-14a):** add the optional per-task `estimate:` (minutes) to the plan-frontmatter
   authoring rules + the freeze-time validation rule: a present-but-non-numeric `estimate:` FAILS
   plan freeze (A1-Q3 — freeze-time raise, not a mid-run surprise). Bootstrap does NOT validate
   plans (it runs before any plan exists); the runtime `resolve_estimate` raise (T1.5) is the
   backstop. **The RUBRIC carries no version of its own — the three `kata-plan-<tier>` SKILL.md
   files get PATCH bumps (0.1.0 → 0.1.1) since the family RUBRIC IS their behavior** (gate v2 F7;
   STANDARDS §3 bump-on-modify; the D140 kata-review-tier precedent — RUBRIC change ⇒ tier-skill
   bumps).

## Acceptance criteria (falsifiable)

1. Full suite green (grown from 2306; every T1 RAISES clause test-pinned); validator 47/0/0 with
   bumped versions + README index regen; Snyk medium+ 0 on `tools/kata_telemetry.py`.
2. Mutation proofs: ≥6 decision guards proven non-vacuous (disable → red → revert), listed in the
   commit/D-record.
3. BC: `validate_inline_eval(None) == "off"` pinned; with `inlineEval` absent no orchestrate step
   references execute (prose BC — acknowledged unfalsifiable mechanically, the D139 AC-3 precedent;
   the falsifiable leg is the Python default).
4. Round-trip: a tmp-repo integration test builds a fake task branch with CLI-emitted trailers and
   proves `scan_checkpoints` + `evidence_digest(commit=...)` reproduce the stamped records exactly —
   **including a deleted path round-tripping as `path:ABSENT`** (gate v1 MED-6).
5. The ledger file exists (header + schema), committed on the branch; board.md diff = ∅;
   exec-safety registry rows present for every new sink (gate v1 HIGH-4).
6. **Instrumented calibration run #1 complete (T5 — gate v1 BLOCKER-1):** ≥1 real ledger row
   appended (human-gated commit); the mandate-overhead A/B measured (wall-clock + tool-calls;
   tokens where surfaced, labeled); the P0 REPORT delivered to the operator with the numbers and
   the explicit kill-switch call (proceed to P1 / STOP at P0) — the frozen STOP-at-P0 decision
   point stays in P0.

## Out of scope (P1+)

Risk score, τ, weights, triggers, the inline evaluator skill + its SKILL_WORK_CLASS registration,
the ladder/reroll/grounding pass, attempt branches, kill bindings, `on`-mode consumption, adapter
contract docs, research/debug adapters.

---

## P0.1 — observability schema bump (operator-directed, DESIGN Amendment #4; routing branch 3)

Status: draft-pending-delta-gate → build after gate. Additive-only; ledger row v1 → v2; no
backfill (v1 rows read as `unclassified`/null); zero new per-checkpoint worker emissions (M4-L1).

### U1 — `tools/kata_telemetry.py` schema v2 (code; TDD + mutation proofs)
- `FAILURE_KINDS` frozenset: `{test-regression, lane-drift, spec-misread, integration-conflict,
  packaging, security, other}` (producer vocabulary; `unclassified` is READER-side only, never
  producible).
- `build_ledger_row` emits `v: 2` + three additive fields: `perTask: {taskId: {tokensIn,
  tokensOut, wallClockS}}` (explicit nulls where the host surfaces nothing — never fabricated);
  `failureKinds: [{taskId, kind, at}]` — an unknown/missing `kind` at BUILD time RAISES
  `TelemetryError` (producer bug, loud; `at` = ISO-UTC); `degraded: [{scope, reason}]`.
- Reader tolerance: `read_ledger` accepts v1 AND v2 rows (unknown-version RAISES); a documented
  accessor (`failure_kinds_of(row)`) maps v1/absent → `[{kind: "unclassified"}]`-equivalent and
  absent cost → nulls. `class_median` unchanged (duration source untouched; calibration exclusion
  untouched).
- Tests: v2 round-trip; v1-row read-back tolerance (the committed row 1 shape verbatim as a
  fixture); unknown-kind build raise; unknown-version raise. Mutation proofs on the two new
  guards (unknown-kind, unknown-version): disable → named test RED → revert.

### U2 — `tools/kata_restore.py` structured degraded signal (code; BACKLOG #16 fold)
- Additive `collect_integrated_tasks_ex(repo_root, integration_branch, plan_path) ->
  {"tasks": set, "degraded": bool, "reasons": list[str]}` — `degraded: true` + a reason exactly
  when the unbounded-fallback NOTE fires (and for the malformed-trailer / phantom-id NOTEs, same
  additive pattern); `collect_integrated_tasks` delegates to it and returns `["tasks"]`
  (byte-identical behavior + prints, BC — existing tests untouched and green).
- `restore()` gains additive keys `degraded: bool` + `degraded_reasons: list[str]` (dict-additive
  BC). NOTE prints stay verbatim (the human leg).
- Tests: unbounded-fallback sets degraded+reason; bounded path degraded=false; restore() carries
  the keys; existing suite untouched. Mutation proof: degraded-flag guard (disable → RED → revert).

### U3 — prose (conductor): orchestrate 0.6.0 → 0.6.1 (gate-time failure-kind classification —
orchestrator classifies from the gate evidence, never the worker, D33; ledger v2 fields named in
the closeout step; every degrade path records a `degraded` entry); telemetry-ledger.md header
notes schema v2 (rows append-only, v1 row 1 stands); CHANGELOG; D142 (disposition + delivery).

### Acceptance
Full gauntlet (suite grown; validator 0/0; Snyk 0 on changed tools); v1 row 1 still parses via
read_ledger; mutation proofs listed; D142 + board DECISION recorded; same done-bar as every phase.

### P0.1 delta-gate history (2026-07-04): SHIP-WITH-FIXES — FROZEN after fold (all 5 folded)
- **HIGH-1 (the seam, named):** `_scan_integration_commit_bodies` widens its return to
  `(lines, degraded_reasons: list[str])`; BOTH internal callers (`collect_integrated_tasks`,
  `parse_supersede_trailers`) unpack it; every NOTE print stays at its current site verbatim.
- **MED-2 (git-error false-clean closed):** `lines is None` (integration history unreadable — the
  MOST degraded path, which today prints no NOTE) ⇒ `degraded: true, reason:
  "integration-history-unreadable"`. `parse_supersede_trailers`' malformed-supersede NOTE stays
  stdout-only — deliberately OUT of the #16 fold (it feeds the P2 contract gate's own raise path).
- **MED-3 (taskId pinned):** P0.1 `failureKinds` covers PER-TASK gate rejections only (taskId
  well-defined); final-gate fix-loop (per-AREA) + M4 ladder-event classification are DEFERRED to P1,
  which widens the entry to `{taskId|area, kind, at}` — deferred, stated, never silently skipped.
- **LOW-4 (provenance fixed):** the unmeasured failure-type-mix parameter cite is HANDOFF §1
  ("3 unmeasured parameters: acceptance rate, failure-type mix, trigger precision"), not the DESIGN.
- **LOW-5 (contract edges pinned):** a row with ABSENT `v` reads as v1 (accessor rule); an unknown
  PRESENT version RAISES; `restore()`'s non-lost-run `_empty` early return also carries
  `degraded: False` + `degraded_reasons: []` (stable dict contract).
