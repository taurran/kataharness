---
name: kata-evaluate
description: >-
  Fresh-context, no-write, default-FAIL gate that returns PASS / NEEDS_WORK on a completed phase against its
  frozen plan. Use as the final gate before "done" — run as a SEPARATE subagent with no Write/Edit so it
  cannot rubber-stamp the builder's work. Checks acceptance criteria, the green gate, drift against LOCKED
  decisions, and scope.
license: Apache-2.0
version: 0.3.1
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
   build (identical size on re-run where claimed), and **the security scan** — **tool-agnostic** (whatever
   scanner the project/toolchain provides; never assume a specific vendor). Paste the numbers. The verdict
   depends on `kata.config.securityScan` (Lever 2 / F6; **absent ⇒ `when-available`**, BC):
   - **`required`** — fail-closed: a scan that is not clean — **or that cannot run (no scanner wired /
     unsupported toolchain)** — AND has no sound documented-acceptance ⇒ NEEDS_WORK. Under `required`,
     scanner-absence **never** degrades-and-passes (the degrade-and-surface carve-out is `when-available`-only).
   - **`when-available`** — run the scan if a scanner is wired AND the toolchain is supported; if it cannot RUN
     (no scanner / unsupported toolchain), record it **`degraded` and surface it** — never a
     silent "clean", never a NEEDS_WORK purely for scanner-absence, never shim tooling to force a scan.
     A scan that RUNS and finds issues is NEVER `degraded` — findings that cannot converge to zero route
     ONLY through the documented-acceptance path below (adval F6-1: "cannot converge" is not a
     cannot-run condition; degrading it would bypass the three-party acceptance control).
   - **`off`** — operator opt-out; note it was skipped by policy (surfaced at handoff), do not fabricate a result.
   **Documented-acceptance is graded for SOUNDNESS, not raw count (F6).** A finding that cannot be driven to
   zero (e.g. a scanner that does not credit a custom sanitizer) terminates ONLY as: genuine hardening →
   in-repo acceptance (`.snyk` with reason + expiry) → a board DECISION. When such acceptance is present,
   grade whether it is **sound** — the reason is truthful, the residual risk is genuinely low, the expiry is
   set — NOT whether the raw finding count is zero. An unsound or undocumented suppression ⇒ NEEDS_WORK; a
   sound, dated, board-recorded acceptance ⇒ PASS on this item.
3. **No drift.** The LOCKED decisions were honored verbatim (e.g. a frozen classification/contract was not
   re-decided). Diff the result against each LOCKED decision. Any unauthorized deviation = NEEDS_WORK.
4. **Ownership respected.** Each task touched only its owned files; concurrent merges were conflict-free.
   Ownership is judged **commit-scoped** (the task's own changes vs. its fork point — `withinFootprint`
   fed by `footprint.changed_in_task`, a three-dot merge-base diff), **not** a branch-range
   `integration..task` diff (which falsely flags files integration changed after the task forked — F5).
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
9. **Reproduce, don't trust (derived artifacts + claimed seams) (L12).** Do **not** accept a *derived* artifact
   or a *claimed wiring* at face value — this is the project's signature failure mode (recorded/documented but
   not independently reproduced). For any artifact the run **computed or rendered** from other inputs (e.g.
   `.kata/concurrency.json` from the board, a generated report from a template + tokens, a computed manifest):
   **regenerate it yourself from its stated source and reconcile** — a material mismatch between the presented
   artifact and the freshly-reproduced one is **NEEDS_WORK** (the presented copy may have been hand-massaged).
   For any **seam the build claims is wired** ("the orchestrator runs X", "the gate emits Y"): trace the
   **WHOLE orchestrated flow** once on a realistic fixture (not a single isolated seam) — assert every PRODUCED
   surface is CONSUMED and every CONSUMED surface is PRODUCED. A produced-but-unconsumed or
   consumed-but-unproduced seam is **NEEDS_WORK**. (Scope: code-bearing wiring — greppable producer→consumer
   handoffs; prose-orchestrated LLM seams are out of scope here.) (Raw test/build output captured by `gate_emit`
   is *primary*, not derived — item 2 already re-runs it; this item targets *second-order* artifacts and wiring
   claims. A run with no derived artifacts and no new seam ⇒ N/A, not a failure.)

   > **Caveat (no-write fresh-context grade limit):** a no-write grader CAN grep produced-vs-consumed handoffs
   > in the wiring files and assert handoff shapes match; it CANNOT build or run the fixture itself. The
   > build-and-run leg is enforced by the orchestrator integration gate (the scheduled wiring-completeness build
   > — see BACKLOG), not by this no-write item.

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
| Concurrency evidence | `.kata/concurrency.json` | `maxInFlight` (int), `genuinelyParallel` (bool), `workerCount` (int), `workers` (map of task-id → `{agent, start, end, sec}`), `overlaps` (list of `[iso-start, iso-end]` windows where ≥2 workers were in-flight), `source` (string); emitted by the canonical snippet in `protocol/board.md` (Concurrency evidence) |
| IaC findings | `.kata/iac.json` | `tasks` (list of per-task entries, schema `protocol/iac-safety.md §7`): each entry carries `taskId`, `kind`, `scanner` (counts + `wired` bool), `smells`, `destructive`, and `verdict:"pass"\|"fail"\|"escalate"`. **Present only when IaC-classed tasks ran; absent on non-IaC runs (N/A — not a failure, BC, MINOR-7).** |

Optional parallelism evidence — for a run that claims concurrent work, read it to corroborate rubric item 4 (ownership / conflict-free concurrent merges); `genuinelyParallel:false` on a legitimately single-worker run is **not** a finding (it is expected). Never a stand-alone default-FAIL trigger.

`tools/gate_emit.py` composes `run_result`, `footprint`, and `mutation_check` without reimplementing them.
If `.kata/footprint.json` is present, use `withinFootprint` for rubric item 4 (ownership respected).
For rubric item 1 on a code-bearing run: `.kata/mutation.json` MUST be present with `allNonVacuous: true`;
absent or `allNonVacuous: false` is a **NEEDS_WORK** finding (not a skip).

**IaC evidence (N5):** if `.kata/iac.json` is present (one or more IaC-classed tasks ran), read every task
entry per `protocol/iac-safety.md §7` and apply these default-FAIL rules:
- `scanner.wired: false` — scanner was absent/errored (fail-closed); gate should have blocked this ⇒ **NEEDS_WORK**.
- `scanner.critical > 0` or `scanner.high > 0` — unresolved high/critical scanner finding ⇒ **NEEDS_WORK**.
- `verdict: "escalate"` with no human-approved resolution (escalation `resolution` absent or `"open"`) — un-approved
  destroy/replace must not integrate ⇒ **NEEDS_WORK**.
- `verdict: "fail"` at evaluation time — the IaC gate fix loop did not clear this finding ⇒ **NEEDS_WORK**.

**Absent / malformed `.kata/iac.json` — do NOT trust presence alone (reproduce, item 9).** Presence-of-artifact
cannot distinguish "no IaC ran" from "the IaC gate was skipped or crashed without emitting." So **independently
re-derive** whether the run touched IaC: classify the footprint's changed files (`.kata/footprint.json` →
`changed`) with `iac_detect.classify_task(changed)`.
- changed files classify as IaC **and** `.kata/iac.json` is absent or malformed ⇒ **NEEDS_WORK** (the IaC gate
  did not run / did not emit — it cannot pass as "no IaC"; symmetric with the malformed-RESULT.json rule above).
- no changed file classifies as IaC **and** `.kata/iac.json` absent ⇒ **N/A — not a failure** (BC, MINOR-7).
Do not fail a genuinely non-IaC run on the absence of this artifact.

**Contract-gate evidence (M1-L3, the independence leg — mirrors the IaC presence rule):** when the
frozen PLAN declares `builds_against` (contract-only dependents that dispatch at freeze, in parallel
with their provider), the run MUST have executed the final-gate contract re-derivation. Its durable
artifact is `.kata/contract-gate.json` (emitted by `tools/contract_gate.py` `write_contract_gate` —
schema = the `verify_contract_gate` dict `{passed, vacuous, findings}` PLUS `utc`, `branch`, and the two
companion arrays `surviving_stubs` and `danglers`). Apply these default-FAIL rules — soundness never
rests on orchestrator compliance (an orchestrator that skipped the contract step cannot pass):
- `builds_against` declared **and** `.kata/contract-gate.json` is absent, malformed (not parseable, or
  missing `passed` / either companion array), or its `passed` is not `true` ⇒ **NEEDS_WORK** (the gate
  did not run / did not clear — it cannot pass as "no contract"; symmetric with the malformed-`RESULT.json`
  and IaC rules above).
- `builds_against` declared **and** the artifact's companion `surviving_stubs` array is non-empty (a
  contract stub sentinel survived the merged tree) **or** its `danglers` array is non-empty (a dependent
  still imports a deleted/renamed contract module) ⇒ **NEEDS_WORK** — the artifact must prove ALL THREE
  final-gate contract checks came back clean (the re-derivation, the sentinel scan, and the
  dangling-import scan), not just `passed`.
- no `builds_against` in the plan **and** `.kata/contract-gate.json` absent ⇒ **N/A — not a failure**
  (BC — mirrors the IaC no-op clause; every contract surface no-ops when no edge is declared, which is
  every run today).
Do not fail a genuinely non-contract run on the absence of this artifact.

## Output
A scored line per rubric item, an overall **PASS / NEEDS_WORK**, and — for any NEEDS_WORK — concrete,
minimal remediation **targeted at the existing plan** (not a re-plan). Seed the orchestrator's fix loop.
The output **must** include the consumed `baseline_sha` + `result_sha` and the `RESULT.json` field values
used for rubric items 1–2 so the record is self-contained.
*(In injected-knowledge mode, output is the per-finding GROUND/REJECT/ESCALATE verdict + cited evidence instead.)*

> **Conformance-escape note (observe-only):** Any finding this gate PASSES that the subsequent [[kata-review]]/D98
> adversarial pass or a human later catches is a conformance-escape; [[kata-review]] flags it and the orchestrator
> records it to `.planning/validation-misses.jsonl` (non-fatally, via `validation_misses.append_miss`). This is
> purely observational — it does not change this gate's own verdict or behavior (T1, `protocol/validation-misses.md`).

> **Verdict-tier variance is a calibration reality (CA-L44 F1; SMOKE-2 finding F1, `.planning/SMOKE-v0.2.0.md`).**
> The same evidence can draw a different verdict at a different evaluator tier. The record: on the same defect
> flavor, the sonnet evaluator returned `correct` (the live proof) and the haiku evaluator returned `reroll`
> (SMOKE-2) — **both economy-tier evaluators; the anchor issued no verdict in either run**. That is sonnet-vs-haiku
> economy-tier variance at n=1 vs n=1 — a noted observation, NOT a statistical claim. Both are legal ladder
> outcomes; the cost profile differs (a `reroll` discards the chunk). This is expected, not a defect — but a
> verdict is not interpretable without its tier. So **every grade states the tier it ran at and the rationale
> behind the verdict**. Calibration data path (per the smoke record's own recommendation): the ledger should
> eventually carry **verdict×tier** so τ/verdict calibration can consume it. Prose guidance only; it changes no
> gate behavior or threshold. (Mirrored for the adversarial SHIP/HOLD verdict in [[kata-review]]'s RUBRIC.)
