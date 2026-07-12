---
name: kata-characterize
description: >-
  LLM-judgment author of the characterization suite for a single auto-fix-eligible finding (P2b /
  DESIGN LD6+§5). Scopes the candidate fix's blast-radius via footprint.partition/footprint.manifest
  (+ footprint.changed_since), generates tests that PIN current behavior across that blast-radius
  EXCEPT the nominated deviation locus, establishes the finding-bound Allowed Exception List (AEL),
  captures before-snapshots for the drift gate (via drift_gate.scrub_nondeterminism /
  drift_gate.snapshots_match semantics), and leaves the generated suite behind in the target repo
  (conversion value, LD6). Gated on kata/module/debug; invoked by kata-orchestrate per auto-fix-
  eligible finding before kata-tdd. kata-characterize GENERATES and PINS; it does NOT apply the fix
  (that is kata-tdd) and does NOT itself apply the drift verdict (the orchestrator does via the engine).
license: Apache-2.0
version: 0.1.0
category: execute
status: beta
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Bash, Write]
source: >-
  new (KataHarness original, Debug Mode P2b — characterization-suite generation, DESIGN LD6+§5)
tags:
  - kata/execute
  - kata/spine
  - kata/module/debug
  - characterization
---

# kata-characterize — characterization-suite author for a gated fix

The P2b fix-protection pass. Given a single **`auto-fix-eligible`** finding from
`.kata/deviations/findings.json`, `kata-characterize` authors the behavioral pinning suite that makes
the fix **verifiably safe**: tests that capture current behavior across the fix's blast-radius, a
finding-bound **Allowed Exception List (AEL)** for the one deviation being corrected, and
before-snapshots for the §5 behavioral drift gate.

**Honest scope (P2b — characterize only):** this skill **GENERATES** tests and **PINS** current
behavior. It does **not** apply the fix — that is `kata-tdd`, downstream in the fix loop. It does
**not** run or apply the drift verdict — the orchestrator does, by calling `drift_gate.drift_verdict`
and `drift_gate.characterization_snapshot_verdict` with the before/after results. The generated suite
is left behind in the target repo and is run via pytest as normal worker output (no new execution sink).

**§5 v1 LIMITATION — state it here and in every output artifact:** this skill enforces
**BEHAVIORAL pinning only**. The structural / public-surface invariance layer (public-API diff = ∅ +
AST-edit-script) is a **FAST-FOLLOW, NOT v1**. Do **not** claim "structure preserved" on the basis of
behavioral tests alone. Full structural enforcement arrives with the §5 fast-follow.

**Gating:** this skill is invoked only when `kata/module/debug` is present in the run's modules and a
finding carries `route=="auto-fix-eligible"`. Absent `kata/module/debug`, this skill is a silent no-op.
Version-up and greenfield runs are byte-for-byte unchanged.

## Inputs

- **Finding record** — a single finding dict from `.kata/deviations/findings.json` with
  `route=="auto-fix-eligible"`. Carries `module`, `locus`, `confidence`, FM signals, and corroboration
  evidence.
- **`.kata/function_models/*.json`** — FM artifacts from the P1 comprehension pass. The FM's
  `intent_summary` and `postconditions` (consulted via `function_model.evaluate_spec`) establish the
  **derived-correct** behavior that the deviation-pinning test should assert.
- **`kata.graph.json`** — caller/callee graph; used together with `footprint.partition` to scope the
  blast-radius beyond the immediate module.
- **Operator test runner** — the project's configured test command (existing operator sink,
  `protocol/exec-safety.md` operator domain); used to establish the before-state for characterization.
  No new execution sink is introduced.

## Procedure

### Step 1 — Blast-radius scoping (LD6/LD8)

Compute the **blast-radius**: the set of modules whose behavior must be pinned by the characterization
suite (everything that could be affected by a change at the finding's locus).

1. **Gather changed-file candidates.** Use **`footprint.changed_since`** to obtain the set of files
   changed since the integration-branch base. In a pre-fix worktree, the candidate set is the fix's
   owned footprint as declared by its task assignment.

2. **Partition into in-footprint and out-of-footprint.** Call **`footprint.partition`**
   (`footprint.partition(changed_files, footprint)`) with the declared footprint for this finding. The
   returned `"in_footprint"` bucket is the direct mutation surface; `"out_of_footprint"` is out-of-lane
   (should be empty — a non-empty bucket is an escalation signal).

3. **Extend to transitive callers/callees.** From `kata.graph.json`, walk the caller/callee edges from
   the finding's `module` and `locus`. Any module that transitively calls into, or is called from, the
   mutation surface must be included in the blast-radius.

4. **Build the full footprint manifest.** Call **`footprint.manifest`**
   (`footprint.manifest(changed_files, footprint, diffstat)`) to produce the canonical blast-radius
   manifest (`inFootprint`, `outOfFootprint`, `withinFootprint`, `codeBearing`). Record this manifest
   — it is part of the characterization outputs handed to the orchestrator.

The blast-radius is the union of:
- `inFootprint` modules (direct mutation surface), and
- all transitively-reachable modules from the graph walk.

### Step 2 — Author characterization tests (PIN current behavior)

For each module in the blast-radius, author tests that **pin the current (pre-fix) behavior**. These
tests are **GREEN before the fix** and must remain **GREEN after** (they hold the world still while
the fix lands).

**Test authoring rules:**

- **Coverage:** every observable behavior of each blast-radius module that could be disturbed by the
  fix must have at least one pinning test. Prioritize the module at the finding's locus and its direct
  callers/callees; extend to transitive modules proportional to coupling depth.

- **Naming convention:** tests live in the target repo's own test tree, following the project's
  established test layout and naming patterns (discovered by reading existing test files via Read/Grep).
  File: `tests/characterization/<module_slug>_char_<finding_id>.py` (or the project's nearest analog).
  Each test function name carries the prefix `test_char_` and a short behavior label.

- **Pin behavior, not structure:** tests assert *what* the function returns, *what* side-effects it
  produces, and *what* it emits — not *how* it is implemented. This is a behavioral pinning suite;
  structural invariance (AST shape, public-API signature stability) is a §5 v1 fast-follow (see
  Limitation note above).

- **The deviation locus is the exception:** the test that covers the **deviation being fixed** (the
  nominated buggy behavior) is handled in Step 3 below. It is **not** authored as a passing green test
  here — it is the deviation-pinning test that starts RED.

- **Consult the FM for derived-correct behavior:** for the deviation locus, call
  **`function_model.evaluate_spec`** (the AST-safe spec-wrapper; `function_model._safe_eval` allowlist;
  registered in `protocol/exec-safety.md`) to establish the derived-correct postcondition. The
  deviation-pinning test (Step 3) asserts the FM-derived correct behavior, not the current buggy
  behavior. All other characterization tests assert current behavior.

- **No new execution sink:** all test-run instrumentation routes through the existing operator runner
  (`run_result.run_gate`). The generated tests are pytest files; they run via `pytest` as normal
  worker output. No harness code evaluates a worker-supplied string; `eval`/`exec` are prohibited.

### Step 3 — Establish the finding-bound Allowed Exception List (AEL)

**AEL INTEGRITY — load-bearing safety control (state this in every output):**

The AEL is established HERE, bound **1:1 to this finding**, and recorded in the
**orchestrator-owned trusted fix manifest** (`.kata/fix_manifest/<finding_id>.json`). It is
**NOT** something the downstream fix worker (`kata-tdd` in its worktree) may enlarge. The fix worker
owns only the fix source and the finding's characterization file; the fix manifest is **out of its
lane**.

The engine enforces AEL integrity with **`drift_gate.validate_allowed_exceptions`**:
- An AEL entry is valid **only if** the test is present AND **RED** in the before-run.
- An entry that is **GREEN in before** (or unknown) is **REJECTED** — a green test can never be
  authorized to regress.
- `drift_gate.drift_verdict` requires every AEL test to actually flip **red→green**; a still-RED
  nominee ⇒ BLOCK. The engine never infers or enlarges the AEL from after-results.

**Nominating AEL entries:**

1. From Step 2, identify the test(s) that cover the **deviation locus** — the function or code path
   where the current buggy behavior lives.
2. Author the deviation-pinning test(s) to assert the **FM-derived correct** postcondition (not the
   current buggy output). Because the fix has not been applied yet, these tests will be **RED** in the
   before-run — that is expected and required.
3. Confirm each nominated test id is RED in the before-run (captured via Step 4). Add it to the AEL
   only if before-outcome is `"red"`. If a test you intend to nominate is somehow GREEN (the current
   code already satisfies the FM-correct condition), it MUST NOT enter the AEL — re-examine the
   deviation record and escalate if the finding appears misrouted.
4. Record the AEL as a list of test ids in the trusted fix manifest. The AEL nominated here is the
   complete, final AEL for this finding. No downstream step may add to it.

### Step 4 — Capture before-snapshots for the §5 drift gate

Capture characterization-output snapshots in the **pre-fix** state. These are the reference
byte-strings the drift gate will compare against after-fix snapshots.

**Snapshot format:** for each characterization test, the snapshot is the serialized test output
(stdout, return value, side-effect log, or any observable output the test pins). Capture via the
operator test runner before the fix worktree diverges.

**Nondeterminism scrubbing:** before storing any snapshot, apply
**`drift_gate.scrub_nondeterminism`** to strip timestamps, hex addresses, tmp paths, and UUIDs.
Store the **scrubbed** string as the before-snapshot. (The scrub pattern list is
`drift_gate.DEFAULT_SCRUB_PATTERNS`, which is TUNABLE without re-freezing the PLAN.)

**Snapshot matching:** the downstream drift gate uses **`drift_gate.snapshots_match`** and
**`drift_gate.characterization_snapshot_verdict`** to compare before/after snapshots. This skill
does **not** re-implement snapshot comparison logic — it calls these surfaces or stores the scrubbed
snapshots for the engine to compare downstream. Never re-implement `scrub_nondeterminism` or
`snapshots_match` in prose.

Write before-snapshots to the trusted fix manifest keyed by test id:

```json
{
  "finding_id": "<id>",
  "ael": ["<test_id_1>"],
  "blast_radius_manifest": { ... },
  "before_snapshots": {
    "<test_id>": "<scrubbed snapshot text>",
    ...
  }
}
```

### Step 5 — Leave the suite behind (conversion value, LD6)

Write the characterization test file(s) into the **target repo's test tree** (not the harness's own
test directory). These files are part of the fix's owned footprint and ship with the eventual merge.

**Why left behind:** the characterization suite is conversion value — after the debug run is complete,
the target repo retains behavioral coverage for the previously-deviating locus. The suite is authored
once (here), gated through the fix loop, and remains in the repo as a permanent test asset.

**Confirm disjoint ownership:** the characterization test files must not overlap with any file owned
by another concurrent worker. Verify the file paths against the task's declared footprint before
writing. Any overlap is an escalation signal.

## Engine surfaces — `tools/drift_gate.py`

All surfaces confirmed present in `tools/drift_gate.py` (verify-before-reuse per
`protocol/reuse-claims.md`). This skill delegates all deterministic snapshot and AEL decisions to
the engine; it never re-implements them in prose.

- **`drift_gate.scrub_nondeterminism(text, *, patterns=DEFAULT_SCRUB_PATTERNS)`** — scrub
  timestamps, hex addresses, tmp paths, and UUIDs before byte-comparison. TUNABLE pattern list.
  Called here to prepare before-snapshots.
- **`drift_gate.snapshots_match(before_snap, after_snap, *, scrub=True)`** — byte-compare after
  scrubbing. The orchestrator calls this surface downstream; this skill stores scrubbed snapshots so
  the comparison is engine-delegated.
- **`drift_gate.characterization_snapshot_verdict(before_snaps, after_snaps, allowed_exceptions)`**
  — snapshots must be byte-identical (scrubbed) EXCEPT the AEL; returns
  `{"verdict": "PASS"|"BLOCK", "changed_outside_ael": [...]}`. Run by the orchestrator after the
  fix; not called by this skill.
- **`drift_gate.validate_allowed_exceptions(allowed, before)`** — AEL integrity gate: rejects any
  AEL entry that is GREEN-in-before or unknown. Called here to verify each nominated AEL entry before
  recording it in the fix manifest. Returns `{"valid": bool, "rejected": [...]}`.
- **`drift_gate.DEFAULT_SCRUB_PATTERNS`** — the tunable nondeterminism-scrub pattern list applied by
  `scrub_nondeterminism`.

The following surfaces are consumed by the orchestrator downstream (cited for completeness; not called
by this skill):

- **`drift_gate.drift_verdict(before, after, *, allowed_exceptions)`** — §5 behavioral gate;
  composes AEL validation + transition classification + PASS/BLOCK decision. Orchestrator-owned.
- **`drift_gate.parse_test_outcomes(output_text)`** — pure parse of verbose test-runner output into
  `{test_id: "green"|"red"}`. Called by the orchestrator to produce before/after outcome maps from
  captured runner output.
- **`drift_gate.classify_transitions(before, after)`** — per-test transition classification.
  Orchestrator-owned.

## Footprint surfaces — `tools/footprint.py`

All surfaces confirmed present in `tools/footprint.py`:

- **`footprint.partition(changed_files, footprint)`** — split changed files into in-footprint and
  out-of-footprint buckets; returns `{"in_footprint": [...], "out_of_footprint": [...]}`.
- **`footprint.manifest(changed_files, footprint, diffstat="")`** — build the full footprint manifest
  (`inFootprint`, `outOfFootprint`, `withinFootprint`, `codeBearing`, `diffstat`). The canonical
  blast-radius artifact recorded in the fix manifest.
- **`footprint.changed_since(ref)`** — thin git wrapper; returns sorted list of files changed since
  `ref`. Used to determine the candidate changed-file set before partitioning.

## FM engine surface — `tools/function_model.py`

- **`function_model.evaluate_spec(fm, call)`** — AST-safe spec-wrapper; evaluates FM
  pre/postconditions against a call record via `function_model._safe_eval` (registered in
  `protocol/exec-safety.md`; in-process evaluation, AST allowlist). Returns
  `{"ok": bool, "violations": [...]}`. Used to establish the derived-correct behavior asserted by the
  deviation-pinning test. No new evaluator; `eval`/`exec` are prohibited throughout.

## Output artifacts

1. **Characterization test file(s)** — written to the target repo's test tree
   (e.g. `tests/characterization/<module_slug>_char_<finding_id>.py`). Left behind as conversion
   value.

2. **Trusted fix manifest** — `.kata/fix_manifest/<finding_id>.json` — orchestrator-owned:
   ```json
   {
     "finding_id":           "<id>",
     "ael":                  ["<test_id>"],
     "blast_radius_manifest": { "footprint": [...], "inFootprint": [...], ... },
     "before_snapshots":     { "<test_id>": "<scrubbed text>", ... },
     "characterization_files": ["<path>"],
     "utc":                  "<ISO-8601>"
   }
   ```
   This is the only authorized source of the AEL for the downstream fix loop. No downstream worker
   may edit or extend this file.

## Invariants

- **Never-tiered / debug-spine:** invoked only when `kata/module/debug` is present and the finding
  carries `route=="auto-fix-eligible"`. Silent no-op otherwise. Absent the debug module, version-up
  and greenfield runs are byte-for-byte unchanged (BC: additive only).

- **Engine delegation — no re-implementation in prose:** every deterministic decision (snapshot
  scrubbing, snapshot matching, AEL integrity validation) is delegated to `tools/drift_gate.py`. This
  skill never re-implements `scrub_nondeterminism`, `snapshots_match`, or `validate_allowed_exceptions`
  in prose.

- **AEL is finding-bound and orchestrator-owned:** this skill nominates from the finding only — it
  does not author an open-ended or worker-expandable AEL. The AEL recorded in the fix manifest is
  the complete, final AEL. Downstream workers cannot enlarge it; `drift_gate.validate_allowed_exceptions`
  hard-rejects any AEL entry that was GREEN-in-before.

- **kata-characterize GENERATES, not fixes:** this skill produces the characterization suite and the
  AEL. It does not apply the fix (that is `kata-tdd`). It does not apply the drift verdict (the
  orchestrator calls `drift_gate.drift_verdict` + `drift_gate.characterization_snapshot_verdict`
  after the fix). The deviance-pinning test is expected to be RED before the fix and GREEN after;
  confirming it flipped is the orchestrator's drift-gate responsibility, not this skill's.

- **§5 v1 LIMITATION — state this in every output artifact and summary:** behavioral pinning only.
  The structural / public-surface invariance layer (public-API diff = ∅ + AST-edit-script) is a
  FAST-FOLLOW, NOT v1. Do NOT claim "structure preserved" on the basis of behavioral tests generated
  here. `drift_gate.structural_drift_verdict` is the named non-executing seam for the fast-follow;
  it raises `NotImplementedError` in v1.

- **No new execution sink:** characterization tests are LLM-generated files run via pytest as normal
  worker output (the fix's owned footprint, gated by `kata-tdd` + `kata-evaluate` + the drift gate).
  No harness code evaluates a worker-supplied string. Operator test runs for before-snapshot capture
  go through the existing `run_result.run_gate` operator sink. No new exec-safety row is registered.

- **No phantom reuse:** every engine surface cited above resolves to a real symbol in
  `tools/drift_gate.py`, `tools/footprint.py`, or `tools/function_model.py`.
  `[[kata-tdd]]` resolves to `skills/execute/kata-tdd/`.
  `[[kata-evaluate]]` resolves to `skills/evaluate/kata-evaluate/`.
  `[[kata-review]]` resolves to `skills/evaluate/kata-review/`.
