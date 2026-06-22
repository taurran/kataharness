---
name: kata-evaluate
description: >-
  Fresh-context, no-write, default-FAIL gate that returns PASS / NEEDS_WORK on a completed phase against its
  frozen plan. Use as the final gate before "done" — run as a SEPARATE subagent with no Write/Edit so it
  cannot rubber-stamp the builder's work. Checks acceptance criteria, the green gate, drift against LOCKED
  decisions, and scope.
license: Apache-2.0
version: 0.1.0
category: evaluate
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Bash]
source: adapted-from cpp-evaluation (CryptoPortfolioPlanner) + Anthropic fresh-context evaluator pattern
tags:
  - kata/evaluate
  - kata/spine
  - conformance
  - default-fail
  - gate
  - no-write
---

# kata-evaluate — the default-FAIL gate

Run from a **fresh context**, as a separate subagent with **no Write/Edit** (enforced structurally by the
frontmatter above — [[STANDARDS]] §1 / [[LESSONS-LEARNED]] L4). You grade; you do not fix. Return
**PASS / NEEDS_WORK** with cited evidence. **Default-FAIL: nothing passes until evidence is read and proves
it.** ([[LESSONS-LEARNED]] L5.)

## Inputs
The frozen DESIGN + PLAN (acceptance criteria + LOCKED decisions + the file-ownership partition), and the
integration branch to grade. **On a grill-skip run, the priming prompt IS the frozen spec** (no grill ran, D71);
also read `ASSUMPTIONS.md` if [[kata-defer]] produced one (the autonomous floor's assumption/ambiguity log).

## Rubric — score each PASS / NEEDS_WORK + a one-line reason with evidence
1. **Acceptance criteria met + mutation proof present (code-bearing runs).** Every criterion in the PLAN's
   tasks and the DESIGN's phase-level acceptance is satisfied — checked against actual files/output, not the
   builder's say-so.  **For any run that introduces or changes executable logic:** `.kata/mutation.json`
   MUST be present AND its `allNonVacuous` field MUST be `true`; absent or `false` ⇒ **NEEDS_WORK**
   (default-FAIL — vacuous or unproven tests do not satisfy the acceptance criteria).  A pure
   data/config/docs task with no new executable logic is exempt; the evaluator states explicitly which
   applies and why.
   **Evidence-driven (MAJOR-3):** when `.kata/footprint.json` contains a `codeBearing` field, key the
   "is this run code-bearing?" decision off **that flag** (`true` ⇒ mutation proof required; `false` ⇒
   exempt) — do not apply evaluator discretion to override it.  When the field is **absent** (older runs
   or a gate_emit that pre-dates MAJOR-3), fall back to the explicit-statement behavior above (backward-
   compatible).
2. **Green gate.** Run it yourself: the project's full test command (count + 0 fail + 0 skip), a deterministic
   build (identical size on re-run where claimed), and the security scan clean. Paste the numbers.
3. **No drift.** The LOCKED decisions were honored verbatim (e.g. a frozen classification/contract was not
   re-decided). Diff the result against each LOCKED decision. Any unauthorized deviation = NEEDS_WORK.
4. **Ownership respected.** Each task touched only its owned files; concurrent merges were conflict-free.
5. **No scope creep.** Nothing built beyond the plan; no speculative features; no unrelated edits.
6. **Backward-compatibility.** Pre-existing behavior/tests preserved where the plan promised it.
   **Version-up regression contract:** for an existing-repo feature add, the gate is the **baseline suite still
   green + new feature tests green** (the existing green-gate and backward-compat criteria applied to the full
   existing suite). No new evaluator — the conformance floor is unchanged (D22).
7. **Standards conformance.** The change follows the repo's *documented* standards — `AGENTS.md`, the
   `CONTEXT.md` glossary, ADRs, coding conventions — not only the spec (conformance-to-spec ≠
   conformance-to-house-rules; mattpocock review's Standards axis).
8. **Assumption log clean (autonomous-floor honesty, D71).** If an `ASSUMPTIONS.md` exists (a grill-skip / low-
   grill run logged autonomous assumptions via [[kata-defer]]), read every entry: any assumption that
   **contradicts the priming prompt / frozen spec** — or silently resolved a genuine ambiguity the human should
   have decided — is **NEEDS_WORK**. This is how the floor's "misalignment caught at the boundary" promise is
   actually enforced, not merely asserted. (No `ASSUMPTIONS.md` ⇒ this item is N/A, not a failure.)

## Injected-knowledge grounding mode (the L2 gate — RS findings / ML candidates; D33)
A distinct invocation: instead of grading a built phase, grade **knowledge about to influence the build** —
[[kata-research]] findings (loop-cognition RS-GB2) or, later, ML candidate skills. The orchestrator runs this
**before** folding any injected knowledge. **Structural invariant (D33) — never tiered, never bypassed, even at
full autonomy** (an engram may replace human *judgment*, never this gate). Fresh-context, no-write, default-FAIL.
Grade each finding/candidate:
1. **Grounding.** Open the cited `source` and confirm it **actually supports** the `claim` — verbatim, not
   paraphrase-drift. An uncited or source-doesn't-say claim ⇒ **REJECT** (a hallucinated source is the failure
   mode this gate exists to catch).
2. **No drift.** Folding it in must not contradict a **LOCKED decision** or the frozen plan. `grounds-to-plan?:
   NO` (a `lockedDecisionInTension`) ⇒ **ESCALATE to the human** — never let injected knowledge silently
   re-decide a LOCKED decision (D1/C4).
3. **Adversarial soundness.** The finding must survive a red-team — source authoritative (not a low-quality or
   stale page), confidence not overstated, no second-order breakage. For depth here, pair with [[kata-review]]'s
   injected-knowledge soundness surface.
**Verdict per finding: GROUND** (cited, source-supported, no LOCKED conflict → orchestrator may fold via a
deliberate superseding re-plan) / **REJECT** (source does not support the claim — ungrounded/unsound → logged,
not used) / **ESCALATE** (LOCKED decision in tension OR `groundsToPlan == "NO"` OR can't-ground → human).
Default-FAIL: nothing is GROUND until its source is read and proves the claim.

**Deterministic verdict emitter (S3a-2):** After this gate completes its evaluation, the **orchestrator** runs
`tools/grounding_gate.py` to derive and persist the machine-readable verdict for each finding. The gate skill
itself remains no-write — it returns per-finding scores; the orchestrator calls `grounding_gate.build_verdict`
(one per finding) and `grounding_gate.write_grounding(kata_dir, verdicts)` to emit `.kata/grounding.json`:

```json
{
  "verdicts": [{ "finding": {...}, "verdict": "GROUND|REJECT|ESCALATE", "evidence": "..." }],
  "allGrounded": true
}
```

The verdict logic in `grounding_gate.grounding_verdict` is the authoritative implementation of the three rules
above — locked in priority order: (1) `locked_conflict OR groundsToPlan == "NO"` ⇒ `ESCALATE`; (2)
`not source_supports` ⇒ `REJECT`; (3) otherwise ⇒ `GROUND`. `allGrounded: true` only when every finding
is `GROUND`. This module is stdlib-only, path-traversal-guarded (CWE-23), and produces the auditable artifact
that closes G5.

## Machine-readable inputs the gate MUST consume

Before scoring any rubric item, the gate **must** locate and read a `RESULT.json` emitted by the run.
This file is authoritative — the gate does **not** accept a human-transcribed pass count in its place.

Required fields consumed from `RESULT.json` — **the canonical schema emitted by `tools/run_result.py`
(`build_result`)**, the single source of truth (producer and consumer agree on this shape):

| Field | Required content |
|---|---|
| `gateName` | The gate name that produced this result (string, e.g. `"kata-evaluate"`) |
| `command` | The exact gate command that was run (string) |
| `exitCode` | Numeric exit code of the test/build command |
| `passed` / `failed` / `skipped` | Test-case counts (ints) |
| `stdoutTail` | Verbatim tail of the run's terminal output (string) |
| `baselineSha` / `resultSha` | Commit SHAs — the tip *before* the work, and the integration HEAD evaluated |
| `utc` | ISO-8601 UTC timestamp of the result |

If `RESULT.json` is absent or malformed, the gate verdict is automatically **NEEDS_WORK** — the default-FAIL
invariant applies here too. Do not attempt to reconstruct the counts from prose.

`baselineSha`/`resultSha` make the run reproducible: the report and any future auditor can recompute the exact
diff (`git diff <baselineSha>..<resultSha>`).

### Artifact paths and canonical producer (Phase 0+)

The three gate artifacts are written to the `.kata/` output directory by **`tools/gate_emit.py`**, the
canonical producer. The gate reads them at these paths (relative to the repo root, or the `--out` path passed
to the emitter):

| Artifact | Path | Content |
|---|---|---|
| Gate result | `.kata/RESULT.json` | The pinned `run_result.build_result` schema (see table above) |
| Footprint manifest | `.kata/footprint.json` | `footprint`, `changed`, `inFootprint`, `outOfFootprint`, `withinFootprint`, `diffstat`, `codeBearing` (bool — present when produced by MAJOR-3+; absent in older artifacts) |
| Mutation proof | `.kata/mutation.json` | `records` (list of `{testWentRed, nonVacuous}`) + `allNonVacuous` (bool) — **REQUIRED for any run that introduces or changes executable logic** (`allNonVacuous: true` must be present; absent or `false` ⇒ rubric item 1 is NEEDS_WORK); exempt for pure data/config/docs tasks |

`tools/gate_emit.py` composes `run_result`, `footprint`, and `mutation_check` without reimplementing them.
If `.kata/footprint.json` is present, use `withinFootprint` for rubric item 4 (ownership respected).
For rubric item 1 on a code-bearing run: `.kata/mutation.json` MUST be present with `allNonVacuous: true`;
absent or `allNonVacuous: false` is a **NEEDS_WORK** finding (not a skip).

## Output
A scored line per rubric item, an overall **PASS / NEEDS_WORK**, and — for any NEEDS_WORK — concrete,
minimal remediation **targeted at the existing plan** (not a re-plan). Seed the orchestrator's fix loop.
The output **must** include the consumed `baseline_sha` + `result_sha` and the `RESULT.json` field values
used for rubric items 1–2 so the record is self-contained.
*(In injected-knowledge mode, output is the per-finding GROUND/REJECT/ESCALATE verdict + cited evidence instead.)*
