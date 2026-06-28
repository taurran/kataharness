---
name: kata-orchestrate
description: >-
  Plan-guardian orchestration for executing a FROZEN design+plan via subagents. Use to drive a phase build
  end-to-end from a frozen PLAN: assign tasks by the wave/file-ownership DAG, dispatch one scoped subagent
  per task into isolated worktrees, gate every task default-FAIL, route escalations, and hold the no-drift
  line. Invoke when you have a frozen plan and need faithful distributed execution (not re-planning).
license: Apache-2.0
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 5
allowed-tools: [Read, Grep, Glob, Bash, Write, Agent]   # Agent = the Claude-adapter binding of the abstract "dispatch worker" capability; v0.1 ships only the Claude adapter
model: fable
source: >-
  adapted-from cpp-orchestrator (CryptoPortfolioPlanner harness) + Anthropic effective-harnesses-for-long-running-agents + managed-agents
tags:
  - kata/coordinate
  - kata/spine
  - orchestration
  - no-drift
  - plan-guardian
---

# kata-orchestrate — drive the frozen plan, dispatch, gate, hold the line

You are the **plan-guardian**. You own the frozen DESIGN + PLAN, task assignment, the file-ownership
partition, and the gates. Workers execute against the frozen plan and **never re-plan** — discovered
unknowns ESCALATE to you (via [[kata-board]]) for a *deliberate* decision. This is the spine: **the plan
does not drift.**

## Preconditions (verify before any dispatch)
0. **Load `kata.config`** (`protocol/config.md`). **Absent ⇒ assume Standard** (D25) and proceed. Present ⇒
   **fail closed (GB12):** if it is malformed JSON, or names a non-existent `mode`/`effort`, a `tiers[family]`
   that has no `kata-<family>-<tier>` skill, or a `module` with no provider — **STOP and escalate** (do not
   guess a default over a *present-but-broken* config; that is the drift the harness exists to prevent). This
   is the load-guard — bootstrap writes the config by construction, so the real risk is a stale / hand-edited /
   older-version config on a re-entrant run, which only this consumer-side check catches.
   - **Resolve tiers (D26):** for each bare family reference `[[kata-grill]]` / `[[kata-review]]` /
     `[[kata-plan]]` / `[[kata-diagnose]]`, dispatch the concrete `tiers[family]` skill (e.g.
     `kata-grill-standard`); a family absent from `tiers` ⇒ the mode's default tier.
   - **Grill-skip rung (D71):** if `tiers["kata-grill"] == "skip"`, dispatch **no grill skill** — freeze the
     **priming prompt as-is** as the spec input and engage the **autonomous-reliability floor**: default-FAIL
     stays (it never skips), the in-loop RS research subagent resolves ambiguity *(loop-cognition phase; named,
     not yet wired)*, and the `kata-defer` assumption/ambiguity log is surfaced at the gate/handoff. Skip
     **shifts** ambiguity resolution from up-front-with-human to in-loop-without-human (the grill↔RS spectrum);
     it never bypasses the `kata-evaluate` gate. (`protocol/config.md` → *Grill-depth dial*.)
   - **Version-up (`target.kind: "existing"`):** use `target.baselineGate` as the baseline command for the
     **green-at-fork-point** precondition below. (The version-up ingestion DAG — kata-graph — is Spec A4; A3
     only consumes the config fields.)
   - **Roles load-guard (N4/L-A):** read confirmed platforms via `kata_settings.confirmed_platforms()` and
     resolve `kata.config.roles` via `kata_roles.resolve_roles(roles_block, confirmed, host_platform)`.
     **`host_platform` is the orchestrator's runtime adapter identity** — in v1 this is `"claude"` (the only
     shipped dispatch adapter; see §"Cross-model dispatch" below — the `Agent` tool is the Claude-adapter
     binding of the abstract "dispatch worker" capability, and v0.1 ships only the Claude adapter; `"claude"`
     is also `resolve_roles`'s default `host_platform`). This is an adapter binding, not a
     `kata.config` field — there is no `target.platform`. A non-Claude orchestrator host is DEFERRED (LD11); a
     future fast-follow swaps only this binding. A `ValueError` from `resolve_roles` (unknown role name, a
     platform ∉ `confirmedPlatforms`, **or a host-only role [orchestrator/evaluator] routed off-host —
     `kata_roles.HOST_ONLY_ROLES`, LD11**) ⇒ **STOP + escalate at preflight** (same fail-closed posture as the
     mode/effort/tiers/modules guard above). **BC1:** `roles` absent ⇒ `resolve_roles` returns every role
     assigned to the host ⇒ today's single-host loop byte-for-byte (DESIGN R5/LD3).
1. **PRE-FLIGHT gate** — conditional, fail-closed, BC-preserving (N5/D29). Call
   `kata_preflight.preflight_required(repo_root)`:
   - **`False`** (no `kata.dependencies.json` manifest): PRE-FLIGHT is not required — proceed
     (today's loop unchanged; BC). This precondition is a no-op for dep-free runs.
   - **`True`** (manifest present): call `kata_preflight.gate_status(repo_root)`.
     - `"ready"` ⇒ proceed to dispatch.
     - `"degraded"` ⇒ the operator must have explicitly accepted this run (surfaced in-conversation
       as a breakthrough-alert by [[kata-preflight]]); absent recorded acceptance ⇒ **STOP + surface**.
     - `"blocked"` | `"absent"` | malformed ⇒ **STOP + surface** the `blockers` list (or the missing /
       malformed artifact); refuse dispatch. Run [[kata-preflight]] first to provision and clear the gate.
2. A **frozen** PLAN exists with a wave/ownership DAG (e.g. `ownership:` + `waves:` + `depends_on:` in
   frontmatter). If the plan is not frozen, stop — planning is a different phase.
3. The target repo is **green at the fork point** (run its test/build gate; record the baseline numbers).
4. The **file-ownership partition is disjoint** — no file appears under two tasks. If it isn't, the plan is
   not executable concurrently; escalate to re-freeze, do not improvise.

## Comprehension phase (ADDITIVE — debug run only; BC: absent `kata/module/debug` ⇒ silent no-op)

**If `kata/module/debug` is in the run's `modules`**, invoke [[kata-comprehend]] as a **fresh-context,
whole-repo comprehension pass before any change or dispatch**. When `kata/module/debug` is absent this is a
silent no-op (the module degrades gracefully, like every optional module); **version-up and greenfield runs are
byte-for-byte unchanged** — the comprehension hook fires **IFF `kata/module/debug` ∈ modules, NEVER off
`target.kind=="existing"` alone** (that field is also set by version-up; keying on it would break BC).

[[kata-comprehend]] builds a `function_model` per module (intent derivation from graph + docs/types/commit-history
+ cross-module contract inference) and emits schema-valid FMs to `.kata/function_models/`. `[[kata-comprehend]]`
is a forward reference resolved at P1 integration (built by Slice S3 in the same wave — expected not to exist
during S1 editing; no broken-wikilink concern at this stage).

A non-zero FM-validation error count ⇒ surface to the operator and STOP before any dispatch.

## Deviation-discovery phase (ADDITIVE — debug run only; BC: absent `kata/module/debug` ⇒ silent no-op)

**If `kata/module/debug` is in the run's `modules`**, and the comprehension phase above emitted FMs to `.kata/function_models/`, invoke [[kata-deviate]] to run the **7-step deviation-discovery funnel** (LD4) and produce **ROUTED findings** (LD5). When `kata/module/debug` is absent this is a silent no-op (the module degrades gracefully, like every optional module); **version-up and greenfield runs are byte-for-byte unchanged** — the deviation pipeline fires **IFF `kata/module/debug` ∈ modules, NEVER off `target.kind=="existing"` alone** (that field is also set by version-up; keying on it would break BC).

[[kata-deviate]] runs the full pipeline — multi-signal candidate gathering, semantic FM-vs-code comparison, ×3 self-consistency (via `deviation.tally_self_consistency`), the objective-corroboration HARD gate (via `deviation.corroboration_gate`; LLM-only findings ⇒ `route:"human"`, never `auto-fix-eligible`), adversarial refute-or-promote — then scores and routes each surviving finding via `deviation.compute_confidence` → `deviation.apply_force_low` → `deviation.route_finding` (composed via `deviation.run_funnel`), and emits the routed artifact via `deviation.emit_findings` (`tools/deviation.py`, `emit_findings` / `findings_schema`) to **`.kata/deviations/findings.json`**. [[kata-deviate]] is a forward reference resolved at P2a integration (Slice D2 in the same wave — expected not to exist during D3 editing; no broken-wikilink concern at this stage).

**P2a scope — FIND only; this phase produces routed findings and does NOT fix.** The four routes in `.kata/deviations/findings.json` are:
- `auto-fix-eligible` (C≥τ_H, ≥1 objective corroborator, ≥2/3 self-consistency, survived refute) — **recorded; NOT fixed here** (the fix loop is LD9 / P2b).
- `research` (τ_L<C<τ_H) → route via the existing [[kata-research]] grounding-gate path (≤2 rounds — escalation-only, NOT a discovery source per H5).
- `defer` (C≤τ_L) → recorded; surfaced at closeout / recommendations (LD12, produced in a later phase).
- `human` (LLM-only / uncorroborated at the HARD gate, or contested refute) → recorded and surfaced; never `auto-fix-eligible`.

P2a findings flow through the normal gates that feed the validation-miss manifest (`tools/validation_misses.py` + the universal hook) — P2a does **not** build that manifest.

## Fix-application phase (ADDITIVE — debug run only; BC: absent `kata/module/debug` ⇒ silent no-op)

**If `kata/module/debug` is in the run's `modules`**, and the deviation-discovery phase above produced `.kata/deviations/findings.json`, process each **`auto-fix-eligible`** finding through the gated fix-application loop. When `kata/module/debug` is absent this is a silent no-op (the module degrades gracefully, like every optional module); **version-up and greenfield runs are byte-for-byte unchanged** — the fix-application loop fires **IFF `kata/module/debug` ∈ modules, NEVER off `target.kind=="existing"` alone** (that field is also set by version-up; keying on it would break BC). When findings contain **zero `auto-fix-eligible` entries**, this phase is a clean no-op — no fixes are applied.

For each `auto-fix-eligible` finding in `.kata/deviations/findings.json`:

1. **Characterize** — invoke [[kata-characterize]] (forward reference; sibling Slice F2 is creating it — expected not to exist yet; no broken-wikilink concern at this stage) to: compute the blast-radius of the candidate fix, author characterization tests that pin current behavior across the blast-radius except at the deviation locus (the deviation-pinning test is RED before the fix, GREEN after; all other characterization tests pin unchanged behavior), capture before-snapshots of characterization outputs (using `drift_gate.scrub_nondeterminism` / `drift_gate.snapshots_match` semantics — never re-implemented in prose), and establish the **finding-bound Allowed Exception List (AEL)** written to the **orchestrator-owned trusted fix manifest**. The AEL is bound 1:1 to this finding. The fix worker **cannot enlarge the AEL** — the fix worker's worktree scope covers only the fix source and its characterization file; the fix manifest and `findings.json` are out of its lane. The AEL is a trusted input, never re-derived from after-results.

2. **Worktree** — open an isolated [[kata-worktree]] on the integration branch for this fix (disjoint per finding).

3. **Fix** — dispatch [[kata-tdd]] in the worktree to implement the fix against the characterization tests (the deviation-pinning test must go red→green; all other characterization tests must stay green). **Objective defects — those corroborated by test failure, type error, or Snyk finding — are fixed regardless of intent-confidence** (LD9). The fix worker stays within its owned footprint; it does not re-derive or modify the AEL.

   **LD10 language-profile overlay (per dispatch — ADDITIVE; BC: absent `kata/module/debug` ⇒ unchanged):**
   When `kata/module/debug` is in the run's `modules`, before dispatching detect the fix's stack from the
   **footprint's file extensions** — the **primary, always-available signal** (`.py` / `.ts` / `.tsx` /
   `.js` / `.java` / `.go` / `.cs` / `.rs`); the comprehension pass's `.kata/function_models/*.json`
   `derivation_sources` is a **weak secondary hint only** (`function_model_schema()` carries **no `language`
   field**, so no FM "module language" signal is claimed). If an extension matches a profile, inject
   **[[kata-lang-profile]]**'s matching `resources/<lang>.md` as the execute-phase **specialist overlay
   alongside [[kata-tdd]]** — exactly the **IaC activation** precedent (the profile *layers on* the worker's
   discipline; [[kata-tdd]] is never forked or edited). A polyglot fix may match more than one profile ⇒
   inject **each** (plus `config-context.md` for build/config files) — no exclusion, mirroring the IaC "a
   task may own both kinds" rule. **No new Python** — the extension signal is read directly, not via a new
   classifier. Absent a matching profile, or absent `kata/module/debug`, **no overlay**: the worker runs
   plain [[kata-tdd]], byte-for-byte unchanged (BC).

4. **Drift gate** — run the operator suite + characterization suite **before** (pre-fix state from step 1) and **after** (fixed worktree) via the existing operator runner (`run_result.run_gate`). Then call **`drift_gate.drift_verdict`** + **`drift_gate.characterization_snapshot_verdict`** with the trusted AEL from the fix manifest. **Any `green->red` transition outside the AEL ⇒ BLOCK.** The engine (`tools/drift_gate.py`) enforces: (a) AEL integrity via `drift_gate.validate_allowed_exceptions` — any AEL entry that is GREEN in before (or unknown) is rejected; a green test can never be authorized to regress; (b) every AEL test must flip red→green — a still-RED nominee ⇒ BLOCK (the fix did not land); (c) characterization snapshots must be byte-identical (nondeterminism scrubbed) except the AEL entries.

   **§5 v1 LIMITATION (honest):** this gate enforces **behavioral** drift only — every baseline-GREEN test stays GREEN; characterization snapshots are stable except the AEL. The **structural / public-surface invariance layer** (public-API diff = ∅ + AST-edit-script = body-updates-only) is a **FAST-FOLLOW, NOT v1** — `tools/drift_gate.py` carries a named non-executing seam (`structural_drift_verdict`) for it. Do **not** claim "structure preserved" on the basis of this gate alone; full structural enforcement arrives with the fast-follow.

5. **Gate** — the fix must pass [[kata-evaluate]] (PASS) + D98 [[kata-review]] (SHIP) + Snyk (`mcp__Snyk__snyk_code_scan`) on the modified code.

   **LD12 Snyk before/after persistence (ADDITIVE; BC: absent `kata/module/debug` ⇒ unchanged):** when
   `kata/module/debug` is in the run's `modules`, the `mcp__Snyk__snyk_code_scan` call already invoked here
   on the **after** (fixed-worktree) state is **also** run on the **before** (pre-fix) state — the **same**
   before/after pair the drift gate established in step 4 (no new state is created, no new exec sink — the
   Snyk MCP call already exists in this step). Record both verdicts and finding counts and **`Write`** them
   to **`.kata/snyk/<finding_id>.json`** conforming to **`debug_report.snyk_report_schema()`** (Slice A owns
   the shape):
   `{finding_id, before: {verdict, findingCount}, after: {verdict, findingCount}, newFindings, available, utc}`
   where `newFindings = max(0, after.findingCount − before.findingCount)`, `finding_id` is derived with the
   **same key as everywhere else** (`finding.get("id") or finding.get("locus") or "unknown"` — the
   `drift_gate.defer_record` / `debug_report.finding_id` rule), and `available: false` is recorded
   **honestly** when a meaningful before-scan was not obtainable for this fix (**no fabrication** — never
   recorded as "clean"). Persistence is a skill **`Write`** — **no new Python**. Absent `kata/module/debug`,
   **no `.kata/snyk/*` artifact is written** and this step is byte-for-byte unchanged (BC).

6. **Apply or DEFER** — when all gates are green, merge the worktree (disjoint files → clean integration). Emit a per-fix drift proof via **`drift_gate.build_drift_report`** + **`drift_gate.emit_drift_report`** → `.kata/drift/<finding_id>.json` (feeds the LD12 regression proof in P3). **Can't-fix-without-drift** — a drift BLOCK that cannot be resolved without behavioral change → call **`drift_gate.defer_record`** and accumulate + write via **`drift_gate.emit_deferrals`** → `.kata/deviations/deferred.json` (preserves the no-drift guarantee; LD9/DG-12). Deferred records are consumed by the LD12 closeout confidence report in P3 and are distinct from the P3 recommendations report.

   **(Debug-mode only — gated on `kata/module/debug`; ADDITIVE, BC: absent it ⇒ unchanged):** the per-fix
   **`.kata/snyk/<finding_id>.json`** before/after artifact written at the Gate step (step 5) is emitted
   **alongside** this drift proof and likewise feeds the LD12 regression+security proof
   (`debug_report.build_proof_rollup`, via [[kata-debrief]] at closeout — see the resolved P3 seam above). An
   `available:false` artifact rolls up honestly as unavailable, never as "clean". Absent `kata/module/debug`,
   no Snyk artifact exists and this step is byte-for-byte unchanged (BC).

`research`, `defer`, and `human`-routed findings are **not** processed here (they were recorded and routed in the deviation-discovery phase above). The fix-application loop touches only `auto-fix-eligible` findings.

<!-- P3 seam — RESOLVED (was: "kata-closeout consumes .kata/drift/*.json + .kata/deviations/deferred.json
for the LD12 confidence report; language prompt-profiles (LD10); onboarding/convert-to-loop (LD13)"). The P3
deliverables that consume this phase's artifacts are now wired in sibling skills, NOT built here:
- **LD12** — the debug-run closeout confidence report is produced by [[kata-debrief]], **offered at closeout
  via [[kata-closeout]]** (which folds the debug section into `.kata/CLOSEOUT.md` / `.kata/closeout.html`
  from `.kata/drift/*.json` + `.kata/deviations/deferred.json` + the `.kata/snyk/*.json` before/after proofs
  written at the fix-loop Gate step below).
- **LD13** — onboarding / convert-to-loop by [[kata-onboard]] (the dedicated first-run path).
- **LD10** — in-mode language prompt-profiles by [[kata-lang-profile]], **injected at the fix/diagnose
  dispatch sites** (see the LD10 overlay notes at the Fix step above and the diagnose dispatch in the
  final-gate fix loop).
The closeout itself runs in the **back-half** (kata-loop → kata-closeout), not inside this skill — so this
seam is a **resolved pointer, not an executing stub**. All of it is gated on `kata/module/debug`; absent that
marker these references are inert and version-up/greenfield runs are byte-for-byte unchanged (BC).
([[kata-debrief]] / [[kata-onboard]] are forward references to sibling P3 slices — broken-wikilink at
authoring is expected, resolved at integration per the P2a/P2b convention; [[kata-lang-profile]] already
exists.) -->

## The loop
**Maintain a rolling frontier.** A task is **dispatchable** iff (all its `depends_on` are integrated) ∧ (its
owned files are disjoint from every in-flight task). Dispatch every dispatchable task concurrently (each in its
own [[kata-worktree]]); as each integrates, **recompute the frontier** and dispatch newly-eligible tasks. The
`waves:` in the plan are a *derived view* of this frontier, not a hard gate — independent work never waits on
an unrelated wave.

**Run-start board hygiene (run-isolation).** Before the first dispatch, **rotate any pre-existing
`.kata/board.md`** to `.kata/board.<utc>.archive.md` (or truncate it) so the board holds **only this run's**
events. The concurrency evidence (`protocol/board.md` → Concurrency evidence) computes over the whole board;
stale prior-run `CLAIM`/`DONE` rows would otherwise contaminate `maxInFlight`/`overlaps` and falsify the
`worker-clock` provenance. A per-run board is the precondition for honest concurrency evidence.

1. **Isolate.** Use [[kata-worktree]] to give each dispatchable task-owner its own worktree on a per-task
   branch (a lone sequential task may run directly on the integration branch).
2. **Orient, then dispatch one worker subagent per task** via the host's subagent mechanism *(adapter binding:
   Claude → the `Agent` tool; other hosts → their subagent/ACP call — the capability is abstract, the binding is
   the adapter's job)*. Pin the implementer model to the cheaper workhorse, held constant across any A/B.
   - **AO hook (per dispatch):** invoke [[kata-orient]] (read-only) to assemble the worker's **launch
     orientation** (three-tier, task-type-tailored, prime-frame-budgeted — `protocol/orientation.md`); inject it
     as the worker's context. Act on the **routed-question flags** it returns: **`research-needed`** → route to
     [[kata-research]] via the grounding-gate path *before* dispatching (don't launch a worker into a known
     unresolved gap); **human-required** → escalate. This is a **hook** — the assembly logic lives in
     `kata-orient`, not here (D24d). No `kata.graph.json` / module files ⇒ kata-orient degrades to the vertical
     rollup; never blocks a dispatch.
   - **IaC activation (per dispatch, N4 — ADDITIVE; BC: no IaC ⇒ unchanged):** call
     `iac_detect.classify_task(task.owned_files, overrides=<kata.config.iac.forceClassify or None>)` on the
     task's owned file list. **`forceClassify` (the operator's glob→kind override map) MUST be passed** — it is
     the documented mitigation for auto-detection false-negatives (MAJOR-5); a matched override wins over
     auto-detection. An **empty set ⇒ no IaC in this task — all downstream behavior unchanged (BC)**.
     A non-empty set ⇒ inject the matching IaC specialist profile alongside `[[kata-tdd]]` in the worker's
     discipline:
     - `"terraform"` in the set → inject **`[[kata-iac-terraform]]`** as the execute-phase specialist.
     - `"cloudformation"` or `"cdk"` in the set → inject **`[[kata-iac-cloudformation]]`** as the execute-phase specialist.
     - Both ⇒ inject both specialists. A task may own both IaC kinds and ordinary code — no exclusion.
     - Mark the task as **IaC-classed**: its verify (step 3) runs the IaC gate in addition to its normal verify.
   Each worker prompt MUST carry, and ONLY carry, its task (the orientation frames it; the task scopes it):
   - an instruction to **execute via [[kata-tdd]]** (the worker's execute-phase discipline — vertical
     red→green, stay in lane, escalate don't re-plan);
   - the task's `<action>`, `<read_first>`, `<acceptance_criteria>`, and its **owned files** (it may edit
     nothing else);
   - the rule: *"Execute against the frozen plan. Do not re-plan or re-decide any LOCKED decision. If you
     hit an unknown or the plan seems wrong, STOP and ESCALATE via the board — do not improvise."*
   - the escalate predicate: *"Escalate if completing your task's acceptance test requires writing a file you
     do not own (`kind: orchestrator-resolvable`), OR if the frozen plan has no solution for a must-deliver
     part of your task and you cannot resolve it without improvising (`kind: research-needed` — do NOT guess;
     the orchestrator will route it to research). Otherwise record out-of-scope discoveries as a deferral note
     ([[kata-defer]]) and keep going. In a grill-skip run, also log any spec assumption you had to make to
     [[kata-defer]] so it surfaces at the gate/handoff."*
   - the per-task verify command (default-FAIL).
   - self-stamp `CLAIM` (start) to the **shared** `.kata/board.md` at the **integration/target-repo root**
     (not the per-task worktree's `.kata/`) via `kata_board.append_event` with your **own process clock**
     when you begin, and `DONE` (end) when your verify passes — so concurrency is provable from artifacts
     (see `protocol/board.md` → Concurrency evidence). The shared root is the integration/target-repo root,
     not the per-task worktree (S3b lesson: per-task worktrees have their own `.kata/` paths; only the
     integration root's `.kata/board.md` is the shared board the orchestrator and evaluator read).
   Every dispatchable task → dispatch concurrently (background); each in its own worktree.
3. **Gate each task (default-FAIL).** When a subagent reports done, YOU read the diff and run the task's
   verify (tests + security scan). Not done until evidence is read and passes. Confirm it touched **only its
   owned files** (drift check).
   **IaC gate (IaC-classed tasks only; ADDITIVE — non-IaC tasks unchanged):** for any task marked
   IaC-classed at dispatch (step 2), also run the **IaC gate** per `protocol/iac-safety.md §3` as part
   of this task's verify. The five ordered gate steps (all creds-free, Tier 1):
   1. Syntax/validate — TF: `terraform fmt -check` + `terraform validate` (offline). CFN: `cfn-lint`
      (CDK: `cdk synth` first). Hard-fail on any error.
   2. Security scan — call `mcp__Snyk__snyk_iac_scan` on the IaC source.
      **Fail-closed (mirrors the SCA fail-closed guard in `tools/kata_preflight.py` `run_preflight`):** scanner unwired/unavailable/errored ⇒
      `verdict:"fail"` with "scanner not wired/unavailable" blocker; gate never passes with zero scanner
      coverage. Any `high`/`critical` finding ⇒ `verdict:"fail"`. Threshold configurable via
      `iac.severityThreshold` (`protocol/config.md`).
   3. 8-smell safe-authoring lens — per `protocol/iac-safety.md §2` (DRY-by-pointer; do not re-implement here).
   4. Destructive-change analysis — static diff always; plan/change-set JSON if provided, parsed via
      `iac_detect.scan_tf_plan` or `iac_detect.scan_cfn_changeset`.
      A `ValueError` from malformed input ⇒ `verdict:"fail"`.
   5. Emit `.kata/iac.json` per the schema at `protocol/iac-safety.md §7`.

   **Verdict routing (per `protocol/iac-safety.md §6`, MAJOR-4):**

   | Verdict | Orchestrator action |
   |---|---|
   | `"pass"` | Proceed to integrate. |
   | `"fail"` (scanner high/critical, scanner unwired/errored, syntax error, malformed plan artifact) | Default-FAIL fix loop — worker revises IaC; gate re-runs. |
   | `"escalate"` (destroy/replace on stateful resource; IAM/secrets/network-topology change) | **Orchestrator** calls `build_escalation` (`tools/escalation.py:47`) then `write_escalation` (`tools/escalation.py:153`) with `kind:"human-required"`, writes `.kata/escalations/<task-id>.json`, and parks the task per `protocol/escalation.md`. Never auto-resolved — no rule clears a destroy silently. |

   **Mixed IaC + code task:** run **both** the normal verify (tests/security scan) and the IaC gate.
   Both must pass before the task integrates.
4. **Integrate.** Merge each completed task branch into the integration branch ([[kata-worktree]] — disjoint
   files merge cleanly by construction). Re-run the gate on the integration branch, then recompute the frontier.
5. **Commit at the checkpoint** (conventional commit + project trailer) so compaction can't lose work.
   Completions integrate **in completion order** — a linear integration-branch history, not a wave-batched one.

## Cross-model dispatch (multi-model routing)

This section is **additive** — the host/`Agent`-tool path (step 2 of the loop above) is the default branch. When a role's resolved platform equals the host platform, the existing `Agent`-tool subagent dispatch applies unchanged. When it differs, the procedure below replaces the subagent call at that role-group dispatch site.

**At each role-group dispatch site**, if `resolved_roles[role]["platform"] ≠ host_platform`:

1. Build a task-brief via `kata_dispatch.build_brief(task_id, role, platform, model=..., objective=..., result_path=..., ...)` (`tools/kata_dispatch.py:42`). Use `sandbox="read-only"` for read-only roles (validator, researcher); `sandbox="write"` for coder.
2. Call `kata_dispatch.dispatch(brief, worktree)` (`tools/kata_dispatch.py:176`) — this launches the platform's headless CLI in the worktree (N2 adapter) and captures a normalized RESULT envelope (N3).
3. Read the RESULT envelope; fold the role's `payload` per the per-role contract: validator → `{verdict, findings}`; researcher → `{claim, source, confidence, groundsToPlan}`; coder → the gate RESULT shape.

**Role-group → dispatch-site map (L-MP5):**

| Role | Dispatch site in this skill | Notes |
|---|---|---|
| `validator` | the **Adversarial red-team before merge** step (`## Final gate` step 6) + the **Research-needed → grounding gate** review (`## Escalation`) | Read-only; **stub-test-proven v1 path** (validator→codex; live-CLI flags pinned at build, guarded by the confirm-probe). |
| `researcher` | `kata-research` on a **Research-needed** escalation (`## Escalation`) | Read-only; **stub-test-proven v1 path** (researcher→kiro; live-CLI flags pinned at build, guarded by the confirm-probe). |
| `coder` | the per-task **worker dispatch** (`## The loop` step 2, sandbox=write) | Supported by `build_brief(sandbox="write")` (`tools/kata_dispatch.py:42`); **NOT a path this build proves** (honest scope). |
| `evaluator` | Host only | The accept/send-back/reroll mechanism is **DEFERRED** (DESIGN §8 *Deferred / fast-follow*, MM-1). |
| `orchestrator` | Host only in v1 | Non-Claude orchestrator host is **DEFERRED** (LD11). |

**LD6 — Concurrency:** Off-host dispatches run as **concurrent background subprocesses** reconciled with the rolling frontier and `.kata/concurrency.json`. Disjoint file-ownership ensures no races; the same frontier invariants (dispatchable iff `depends_on` drained + owned files disjoint from in-flight tasks) apply equally to cross-model tasks.

**LD7 — Host fallback:** When the RESULT envelope carries `status ∈ {failed, timeout, fallback}`, **fall back to the host's `Agent`-tool path** (the existing subagent dispatch), **log the failure** (a board `ESCALATE` or `BLOCK` event), and **surface it** in the conversation. A routed platform failing repeatedly within a run is **flagged unconfirmed for that run** — all subsequent dispatch sites for that platform revert to the host path, and the incident is recorded in the drift ledger. The next run's preflight re-evaluates `confirmedPlatforms`.

**Honest scope (v1):** The **read-only roles** (validator→codex, researcher→kiro) are **wired and stub-test-proven** this build — the cross-model chain is exercised end-to-end against an injectable stub runner; the **live per-platform CLI flags are point-in-time and pinned/verified at build, with the confirm-probe as the standing guard** (a real multi-model run is gated on install + confirm). Coder-routing (write sandbox) is architecturally described and supported by `build_brief(sandbox="write")` (`tools/kata_dispatch.py:42`) but is **not** proven by this build. Evaluator injection-point thresholds are deferred (DESIGN §8 *Deferred / fast-follow*, MM-1). Orchestrator-host reassignment is deferred (LD11).

## Escalation (the no-re-plan escape valve)
An escalation is an **async event** — it does **NOT halt the run**. The escalating worker writes the
**structured payload** (`protocol/escalation.md` → `.kata/escalations/<task-id>.json`) and appends the
one-line `ESCALATE | <task-id> | <summary>` to [[kata-board]] (the board stays one-line; detail lives in the
payload). You then **park** the escalating task **and its DAG-dependents** (remove them from the frontier),
**keep dispatching the rest of the frontier**, and checkpoint completions as they integrate.

**Classify every escalation** (you make the final routing call; the worker's `kind` is a hint you may re-classify):
- **Orchestrator-resolvable** — e.g. a needed re-scope / re-partition of file-ownership. You decide it
  yourself and re-dispatch a tightened task; this **never reaches a human**.
- **Research-needed** — a must-deliver feature with **no in-plan solution** (RS-GB1). Dispatch [[kata-research]]
  as a **fresh-context, no-write** subagent, scoped to the escalation payload *(build + persist the payload via
  `tools/escalation.py` — `build_escalation(...)` → `write_escalation(kata_dir, payload)` →
  `.kata/escalations/<task-id>.json`)*. Its findings (`{claim, source, confidence, groundsToPlan}` — the
  `tools/escalation.py` `build_finding` shape) are an *input*, never auto-applied — run them through the
  **grounding gate** ([[kata-evaluate]] injected-knowledge mode + [[kata-review]]'s injected-knowledge soundness
  surface; **never bypassed, D33**). **You — the orchestrator — persist the verdict** (the no-write
  [[kata-evaluate]] grades but cannot write): for each finding call `tools/grounding_gate.py`
  `build_verdict(finding, source_supports, locked_conflict, evidence)`, then `write_grounding(kata_dir, verdicts)`
  → `.kata/grounding.json` (carries `allGrounded`). Then route per verdict:
  - **GROUND** → fold the finding via a **deliberate re-plan baked as a superseding decision** (audited in the
    drift ledger + the escalation `resolution`) — supersede, never silently rewrite the frozen plan; re-dispatch
    the tightened task. This is the *only* way new knowledge enters the build.
  - **REJECT** (ungrounded/unsound) → log it in the escalation payload; do **not** fold; if the gap remains,
    re-classify **human-required**.
  - **ESCALATE / can't-ground** (LOCKED tension, or no authoritative answer) → re-classify **human-required**.
  Research that can't ground is **never** improvised into the build.
- **Human-required** — a LOCKED-decision conflict. **Only this surfaces to a human.** A LOCKED-decision
  conflict is escalated to the human, **never silently re-decided** (that is the exact drift the harness
  exists to prevent). *(Consulting an engram to auto-resolve before a hard-wait is a future capability — not
  wired here.)*

**Hard-wait for the human IFF the frontier is empty ∧ open human-required escalations remain.** Being
"frontier-blocked" **is** the criticality test — there is no separate criticality knob. As long as unrelated
dispatchable work exists, the run keeps moving; it only stalls for a human when nothing else can progress.

## Final gate
After the frontier drains (all tasks integrated), on the integration branch:
1. Full default-FAIL gate green (tests + security + deterministic build).
2. **Emit the gate artifact set** before handing to [[kata-evaluate]]:
   run `tools/gate_emit.py` (the canonical emitter) to produce `.kata/RESULT.json`,
   `.kata/footprint.json`, and — **for any code-bearing run** — `.kata/mutation.json`.
   **Collect the mutation records first:** gather each task's `prove_non_vacuous` verdicts (workers run them per
   [[kata-tdd]] and report them with their `DONE`); take their **union** and pass it as `mutation_records` so the
   integration `.kata/mutation.json` carries the proof the gate ([[kata-evaluate]] rubric item 1) requires for
   code-bearing work. The `python -m gate_emit` CLI emits RESULT+footprint; **to include mutation records call the
   Python API** `gate_emit.emit_gate_artifacts(..., mutation_records=<union>)` (the CLI form omits mutation).
   **IaC-bearing runs:** additionally ensure `.kata/iac.json` is present before step 4 — it is emitted at
   each IaC task's verify (step 3 above, one entry per IaC-classed task, merged into a single `tasks` array).
   Absent `.kata/iac.json` on a run with **no IaC tasks** ⇒ safe no-op (BC, MINOR-7,
   `protocol/iac-safety.md §7`). **This is not self-certifying:** [[kata-evaluate]] independently re-derives
   whether IaC ran by classifying the footprint's changed files (`iac_detect.classify_task`); if any changed
   file is IaC-classed but `.kata/iac.json` is absent or malformed, the gate **returns NEEDS_WORK** (a skipped
   or crashed IaC gate cannot pass as "no IaC"). So a missing emit is caught at the gate, not trusted away.
   Example invocation (RESULT + footprint):
   ```
   python -m gate_emit \
     --gate-name integration \
     --command "uv run pytest -q" \
     --footprint tools/ skills/ \
     --baseline <baseline_sha> \
     --result <integration_head_sha> \
     --out .kata
   ```
   The emitter composes `run_result`, `footprint`, and `mutation_check` — it does not reimplement them.
   Pass `--out .kata` so [[kata-evaluate]] finds artifacts at the conventional paths.
   **Precondition (do not skip):** `.kata/RESULT.json` MUST exist before step 4. If it is absent, run
   `gate_emit.py` first — never dispatch [[kata-evaluate]] with no artifacts to read (it would default-FAIL to
   NEEDS_WORK anyway; emit first so the gate grades real evidence, not a missing file).
3. **Emit the concurrency evidence** — run the canonical snippet from `protocol/board.md`
   (section: "Concurrency evidence (`.kata/concurrency.json`)") against the run's `.kata/` to produce
   `.kata/concurrency.json`. The snippet body lives only in `protocol/board.md` (K3 — do not duplicate it
   here). This is parallelism evidence the evaluator reads to corroborate rubric item 4; a legitimately
   single-worker run producing `maxInFlight:1`/`genuinelyParallel:false` is **not** a failure — this step
   never fails a sequential run (K6). Preconditions the snippet relies on (see `protocol/board.md`): the board
   was rotated to be **per-run** (run-start hygiene above), and workers **share a synchronized clock** — flag
   the latter as a known limitation for any future multi-host run before trusting `overlaps`.
4. Dispatch [[kata-evaluate]] as a **fresh-context, no-write** subagent → PASS / NEEDS_WORK. On a grill-skip /
   low-grill run, point it at the priming prompt as the frozen spec and at any [[kata-defer]] `ASSUMPTIONS.md`,
   so the autonomous floor's assumption log is graded for prompt-contradiction (rubric item 8) — not just asserted.
   Point it at `.kata/` so it reads the emitted artifacts directly.
   **If `kata/module/slop` is configured** (`protocol/config.md`), also dispatch [[kata-slop-check]] as a
   fresh-context, no-write check **alongside** [[kata-evaluate]] (concurrent). A `SLOP-DETECTED` verdict is
   **default-FAIL** (treated as NEEDS_WORK) — never advisory-only. When `kata/module/slop` is absent this is a
   silent no-op (the module degrades gracefully, like every optional module).
5. NEEDS_WORK → a **targeted fix against the same plan** (not a re-plan); loop to PASS.

   ### Fix-loop — material re-verification + thrash budget (fix-loop-hardening L1/L2/L3/L5)

   **Staged cascade (L5 / reaffirmed):** within each judge's findings, collect **all** findings → fix in **one
   batch** → re-verify that judge. The cheap deterministic gate (tests / validator / lint / scan) always runs
   first; a red cheap gate never reaches a fresh-context judge (the cascade ordering is invariant).

   **Material re-verification after each fix (L1 — LOCKED):**
   - **Always re-run the cheap deterministic gate** — fast, idempotent, required on every fix cycle.
   - **Re-run a fresh-context judge** (`kata-evaluate` / `kata-review`) **iff the fix's footprint** (the files
     it changed, per `.kata/footprint.json.changed`) **intersects a file that judge's findings cited.** This is a
     *files-cited* intersection — **not** the code-symbol "blast-radius" relation (which does not range over a
     judge's prose findings; keep the two terms distinct).
   - **Indeterminate ⇒ re-run (fail-safe, LOCKED).** If the intersection cannot be determined, treat the fix as
     material and re-run the judge.
   - **After the *final* batch of fixes, run exactly ONE confirmation pass:** cheap gate **+ a re-run of
     `kata-evaluate`** (cross-fix interaction is a conformance question). Do **not** run multiple confirmation
     passes. The D98 `kata-review` (step 6 below) runs **once, after the confirmation pass settles, on the final
     post-fix artifact — never inside the fix loop.** A fix made in response to the red-team re-enters at the
     confirmation pass (so what was attacked is what ships), governed by the thrash budget.

   **Thrash budget — orchestrator-transient in-context counts (L2/L3 — LOCKED):**

   Track **two counters** as transient in-context bookkeeping **while running the fix loop** — the orchestrator
   counts its own eval→fix iterations as it goes:
   - **Per-area count** — keyed on the task being fixed; tracks how many consecutive fix cycles that area has
     failed. The orchestrator **writes a `DECISION` board line per fix-cycle** (`NEEDS_WORK fix: <area> cycle <n>`)
     — these are the durable recount trail on resume. (The `DECISION` TYPE already exists; this specifies the
     per-fix-cycle *cadence*, not a new TYPE — L6.)
   - **Run-level ceiling** — a total fix-cycle count across all areas, so A↔B oscillation (area A passes after
     breaking area B, which passes after re-breaking A) cannot evade a per-area reset. Provisional value:
     **`2 × (number of plan tasks) + 2` total fix-cycles** `[TUNABLE — provisional, pending dogfood
     calibration]` — large enough that a healthy build (each task needing ≤ 2 fixes) never trips it, small
     enough that unbounded oscillation does. (A bare "ceiling" with no number is unenforceable; this is the
     operative value until the benchmark recalibrates it.)
   - A confirmation-pass regression **counts against the budget**. A later-invalidated PASS does **not** zero
     the count.

   > **L3 (verbatim):** *"At budget, `kata-diagnose` (resolved tier) returns fix-problem vs plan-problem; the
   > human valve fires only on plan-problem, via the existing `human-required` kind (no enum change — distinction
   > in `decisionNeeded`/`rationale`), async-parked per the existing contract, supersede-not-rewrite, never
   > silent. Spine #1/#2 preserved."*

   These counts are **NOT** a `state.json` field, **NOT** a board event TYPE, **NOT** written via
   `kata_board.update_task`, and introduce **no new Python** (L4). They are the orchestrator's own fix-loop
   bookkeeping; the `DECISION` board lines are the recount trail.

   **At N=2 (3rd failure of one area) OR the run-level ceiling:**
   1. STOP the fix loop on that area.
   2. Dispatch **`kata-diagnose`** (resolved tier) as a fresh-context root-cause pass — cheap, no human.
      It returns a **fix-problem vs plan-problem** verdict (see `kata-diagnose/RUBRIC.md` Phase 6 → Verdict).
      **LD10 language-profile overlay (ADDITIVE; BC: absent `kata/module/debug` ⇒ unchanged):** when
      `kata/module/debug` is in the run's `modules`, detect the area's stack from its **footprint file
      extensions** (the primary, always-available signal; FM `derivation_sources` a weak hint only — no
      `language` field) and inject the matching **[[kata-lang-profile]]** `resources/<lang>.md` as a
      specialist overlay **alongside [[kata-diagnose]]** — the same dispatch-time injection as the IaC
      precedent; [[kata-diagnose]] is never forked or edited, and **no new Python** is added. A polyglot area
      may match more than one profile ⇒ inject each (plus `config-context.md`). Absent a matching profile, or
      absent `kata/module/debug`, **no overlay** — plain [[kata-diagnose]], byte-for-byte unchanged (BC).
   3. **Fix-problem verdict:** the area is legitimately hard but fixable — this is **not** a human interrupt.
      Resume fixing with the diagnosis context.
   4. **Plan-problem verdict:** escalate a **re-plan candidate** via the existing `kind: "human-required"`
      (no enum change — L6). Carry the thrash distinction in `decisionNeeded`/`rationale` (note that
      `kata-diagnose` ran first and returned plan-problem). Park the task + DAG-dependents; frontier keeps
      draining. Deliberate, human-gated, supersede-not-rewrite, never silent.

6. **Adversarial red-team before merge — on a code/contract-bearing build (L12).** After [[kata-evaluate]]
   returns PASS, and **before merge-to-master**, dispatch [[kata-review]] (**≥ standard tier** — a merge-gate
   warrants depth; do not red-team a contract change at `essential`) as a **separate fresh-context, no-write**
   adversarial subagent whose job is to *break* the result — not re-grade conformance, but hunt the failure modes
   the default-FAIL gate structurally misses: documentation-only seams (wired-in-prose, dead-in-a-real-run),
   derived artifacts that don't reproduce from source, and overclaim/slop (RUBRIC surface 6). This is the **second
   lens** the project learned it needs ([[LESSONS-LEARNED]] L10c, recurred as L12) — `kata-evaluate` grades against
   the plan; this actively attacks. **SHIP-WITH-FIXES / HOLD → targeted fixes against the same plan, then
   re-confirm.** It is *additive* to the [[kata-evaluate]] gate (item 9 *reproduces* artifacts; this *attacks* the
   whole build), never a replacement.
   - **Scope — "code/contract-bearing" is an evaluator/operator judgment, NOT the `codeBearing` footprint flag.**
     `footprint.codeBearing` keys off *code* extensions only (`tools/footprint.py`), so a pure **protocol/skill
     `.md` contract edit is `codeBearing:false` yet IS contract-bearing** (this very loop-hardening change was —
     and a naïve `codeBearing` gate would have skipped its own red-team). Trigger the red-team when the build
     changes **executable logic (`codeBearing:true`) OR a contract/protocol/skill surface** (`protocol/**`,
     `skills/**/SKILL.md` or `RUBRIC.md`, a frozen spec contract) — the latter judged, not flag-derived. Only a
     genuinely trivial docs/prose run (planning notes, READMEs, comments) may skip, at the operator's call.
   - **Validation-miss emit (non-fatal — pure side-effect; BC: no gate verdict changes):** after [[kata-review]]
     returns its findings, for each finding it flagged as a conformance-escape (per `protocol/validation-misses.md`
     — a confirmed defect the preceding `kata-evaluate` PASSED), build a miss entry (fields: `ts`, `mode`,
     `failure_class`, `responsible_skill`, `severity`, `what_conformance_missed`, `what_caught_it:"d98"`,
     `guard_ref`, `decision_ref`) and call
     `validation_misses.append_miss(entry, ".planning/validation-misses.jsonl")` (`tools/validation_misses.py`).
     **A `False` return or any error is surfaced as a NOTE in the conversation — it NEVER fails the build or
     changes any gate verdict.** Logging is a pure side-effect (T1, observe-only; `protocol/validation-misses.md`
     §Observe-only). Skip silently if [[kata-review]] flagged no conformance-escapes.
7. Commit; if a handoff is needed, [[kata-handoff]].

## Milestone narration (WS-3 — ADDITIVE; does not alter dispatch, frontier, or gate logic)

> **Contracts:** `protocol/narration.md` (the phase→plain-language map + cadence + breakthrough + honesty guard)
> and `protocol/persona.md` (the voice). Read both before emitting any narration. This section wires
> them into the orchestrator's conversation output; the `改善型` dashboard, statusline, and board
> (`protocol/board.md`) remain the granular firehose and are **unchanged** by this section.

### When to narrate

Narrate **in the conversation** at the meaningful boundaries listed in `protocol/narration.md §1`
(the phase→plain-language map). Stay quiet between. The milestone-cadence rule (`narration.md §2`):
**narrate at phase transitions and significant parallel-work events; do not narrate routine forward motion,
individual PROGRESS heartbeats, or internal state updates the user has no action on.**

Use the plain-language phrasings from `protocol/narration.md §1` — never the internal stage names
(GRILL / FREEZE / PREFLIGHT / EXECUTE / EVALUATE / HANDOFF). The internal labels are the
orchestrator's reference vocabulary; the user receives the plain-language account. Voice per
`protocol/persona.md`.

**Orchestrator narration points** (mapped to this skill's own loop):

| Orchestrator event | Narration action |
|---|---|
| All wave-1 tasks dispatched (or first-wave workers running) | "Building the pieces — N in parallel." (substitute real count per `narration.md §1`) |
| All tasks integrated; frontier drains | Narrate the transition to the evaluation step: "Checking the work honestly against a fresh pair of eyes." |
| `kata-evaluate` returns a verdict | State the verdict plainly ("The evaluation passed." or "The evaluation found issues — here is what needs to be addressed."). A NEEDS_WORK is stated plainly, never softened or delayed. |
| Handoff complete (durable artifacts committed, ready for owner review) | "Wrapping up and handing the result back to you." |

Between these points: silence. The dashboard carries the live view.

### Breakthrough-alert invariant (never tiered — `narration.md §3`)

**Decisions, escalations, and critical failures surface in the conversation immediately and unmissably,
regardless of routine quiet.** This invariant is **never tiered** (D33-class) — no mode, cadence setting,
or run configuration can suppress a breakthrough alert.

| Trigger | Narration action |
|---|---|
| An escalation reaches `human-required` classification (a fork the orchestrator cannot resolve alone) | Deliver the escalation payload in the conversation immediately. Do not wait for a phase boundary; do not let it queue behind routine narration. |
| A critical failure (run cannot proceed; a spine invariant is at risk; a security-relevant finding) | Surface it in the conversation immediately, with the finding and the path forward. |
| `kata-evaluate` returns NEEDS_WORK | State the verdict plainly in the first message after the result is known. |

This is additive and independent of the board signal: the board's `ESCALATE`/`BLOCK` entries and the
conversation breakthrough alert are **both** required — neither substitutes for the other.

### Honesty guard (`narration.md §4`)

Narration describes **only what is actually happening**. Before writing a narration phrase, ask:
"Is the thing I am describing actually happening right now in this run?" If the answer is "it might
happen later when a gated capability is enabled," do not write the phrase.

**Explicitly forbidden today:**

- Any phrasing implying a standing in-loop research call-site is active ("I'm researching this
  myself") when research-mode RS is not a standing call-site in the current run.
- Any phrasing implying live engram CONSULT is active ("I'm learning from this" / "I'll remember
  your preference") — engram CONSULT is gated off (D9/D56/D74); the LEARN feed emits only.

Narrating un-wired autonomy recreates the L8-class overclaim `kata-slop-check` catches in other
contexts. The harness's own narration channel must be free of it.

---

## Drift ledger (for A/B / audit)
Track, as you go: unauthorized deviations from LOCKED decisions (target **0**), files touched outside
ownership, human interventions, escalations, and whether the gate caught real issues. This is the evidence
the run is judged on.
