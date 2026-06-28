---
title: "IaC live-apply (Tier 2) — PREVIEW/APPROVE/PLAN-CAPTURE half — FROZEN-CANDIDATE PLAN"
status: "FROZEN — freeze-gate kata-review HOLD→SHIP (2026-06-27; F2 README-ownership + F1 self-binding-grant + F3 CFN-hash/ARN-grammar fixed → re-confirm SHIP)"
spec: iac-live-apply
tier: 2 (live-apply) — THIS PLAN = the preview/approve/plan-capture HALF ONLY; cloud EXECUTION is the DEFERRED n=0-live seam
depends-on: >-
  iac-safety-specialist (Tier 1, D110 — BUILT) · tools/iac_detect.py (stateful sets + plan/change-set parsers) ·
  protocol/iac-safety.md (Tier-1 contract) · protocol/exec-safety.md (D112 sink registry) ·
  tools/kata_preflight.py (H2 approval-hash precedent) · tools/drift_gate.py (NotImplementedError seam precedent) ·
  tools/escalation.py (human-required park/drain)
gated-on: authenticated cloud access (CLI creds / SSO / authenticated cloud MCP) — adapter-bound; NOT wired in this half
source: "Resolved grill (3 operator decisions + adopted defaults, LOCKED). Introduces NO decision beyond it."
---

# IaC live-apply (Tier 2) — preview/approve/plan-capture half — FROZEN-CANDIDATE PLAN

> THE HIGHEST-STAKES FEATURE IN THE PROJECT. A live cloud apply destroys real, non-git-reversible infra. This plan
> builds + unit-tests the **pure preview/approve/capture machinery** and **STOPS at the creds wall**: the actual cloud
> EXECUTION (`terraform plan` to generate a plan, `terraform apply`, `aws cloudformation execute-change-set`) is the
> **DEFERRED, n=0-live boundary** — never wired as a runnable shipping path. Err toward safety and honesty everywhere.

---

## Locked decisions (from grill) — introduce NOTHING beyond these

1. **Scope = the preview/approve/plan-capture half ONLY.** BUILD: the structured-argv BUILDERS + the approval
   state-machine + plan-hash binding + the stateful-destroy capability-gate + the artifact contract + the exec-safety
   sink registration + skill/orchestrate wiring. **STOP at the creds wall:** the actual cloud EXECUTION (running
   `terraform plan` to generate a plan, and `terraform apply` / `aws cloudformation execute-change-set`) is the
   **DEFERRED, n=0-live boundary — NOT wired as an executable shipping path.** Build + unit-test the argv builders
   (assert correct argv, `shell=False`) and all the pure gate/hash/capability logic; do NOT ship a cloud-mutating call
   that has never run. Mark the execution seam clearly (the `drift_gate.structural_drift_verdict` NotImplementedError-seam
   pattern, AND a hard creds+approval gate that honestly cannot fire without creds). Loudly label the whole apply path
   **n=0-live, creds-gated.**
2. **Both Terraform AND CloudFormation** in this pass.
3. **Stateful destroy/replace = a separate TYPED CAPABILITY-GATE** (NOT a routine approve): a destroy/replace on a
   stateful resource (detected via the BUILT `iac_detect` stateful sets + `scan_tf_plan`/`scan_cfn_changeset`) requires
   an explicit typed confirmation distinct from normal plan approval. (Operator chose this over Tier-1's hard-block.)

**Adopted defaults (LOCKED):**
- **Safety contract:** preview the EXACT plan/change-set → human approves → **approval bound to a plan HASH** (re-plan /
  plan-change invalidates approval — reuse the kata-preflight approval-hash drift-gate pattern) → plan-capture artifact →
  **(apply DEFERRED)** → post-apply verify + captured recovery plan (design-level) → **never auto-rollback.**
- The plan/apply subprocess = **fixed-argv builder, `shell=False`, operator-trust-domain, gated on a present+matching
  approval artifact**, registered as new rows in the `protocol/exec-safety.md` sink registry. NEVER a freeform command
  (the RCE class recurred 3× — D111/D112). **The plan/change-set identifier is DATA, not program.**
- **State/drift:** v1 REQUIRES remote state + locking; pre-apply drift (real infra ≠ state) = abort/escalate; state
  surgery (import/mv/rm, backend migration) = OUT OF SCOPE.
- **Approval timeout:** a parked apply stays parked, never auto-applies (reuse `escalation.py` async park/drain).
- **OUT OF SCOPE / v1.1+:** cost/blast-radius preview, `-target`/scoped apply (explicitly **FORBID in v1** — bypasses
  lifecycle guards), multi-cloud, env-differentiated policy. Keep a minimal **append-only apply-audit log** in-scope
  (reuse escalation/board surfaces).

**The creds-wall boundary (verbatim-in-spirit, pinned):** Everything in this half is creds-FREE and operates on a
**provided** plan/change-set artifact (exactly as Tier-1 `scan_tf_plan` operates on a provided `plan_json`). Generating
a plan live, reading live state for drift, and executing an apply ALL require authenticated cloud access — **none is
wired here.** The execution seam (`iac_apply.run_apply`) is reachable only behind a present+matching approval artifact
AND a present capability grant AND present creds, and **even then raises `NotImplementedError`** (n=0-live). It cannot
mutate cloud infra by construction.

---

## In scope (this half)

- **A pure engine `tools/iac_apply.py` (NEW)** — structured-argv builders (TF plan/apply, CFN create/execute-change-set),
  plan-hash binding, the approval state-machine, the typed stateful-destroy capability-gate, the sibling-artifact schema,
  the append-only apply-audit record builder, and the **deferred execution seam** (`run_apply` → `NotImplementedError`).
  Pure / injectable / mutation-proof / no subprocess / no eval / no exec / Snyk-scanned.
- **`protocol/exec-safety.md`** — register the new (DEFERRED, `shell=False`) plan/apply sinks with trust domain =
  operator + the approval-artifact gate. `test_exec_safety.py` must stay green (no new `shell=True`).
- **`protocol/iac-safety.md`** — add a **Tier-2 section** extending the Tier-1 contract (the preview→approve→capture
  pipeline, the capability-gate, drift-abort, never-auto-rollback, the sibling artifact, the deferred-execution seam).
- **`kata-iac-terraform` + `kata-iac-cloudformation` SKILL.md** — Tier-2 preview/approve/capture sections slotted at the
  existing **"Tier 1 boundary: do NOT run plan/apply"** markers; cite the engine surfaces by name; label n=0-live/creds-gated.
- **`kata-orchestrate` SKILL.md** — the orchestrator-side approval state-machine binding + capability-gate →
  `human-required` park (reuse `escalation.py`) + parked-apply-stays-parked + the minimal append-only apply-audit log;
  the apply EXECUTION stays the deferred seam (never wired runnable); `-target` explicitly FORBIDDEN.
- **The sibling runtime artifact `.kata/iac-apply.json`** (machine-written: captured plan ref + plan hash + state + audit)
  and the **committable approval artifact `kata.iac-apply-approval.json`** (human-authored: approved plan hash + the typed
  stateful-destroy grant) — distinct paths (tamper-resistance, mirrors kata_preflight H2).

## Out of scope (DEFERRED / v1.1+ — do NOT build here)

- **The live cloud EXECUTION** — running `terraform plan` to generate a plan, `terraform apply`, `aws cloudformation
  execute-change-set`, and any live state read for drift. All creds-gated, all the n=0-live seam. **If a slice "needs"
  to make `run_apply` actually spawn a subprocess → STOP (creds-wall violation).**
- **`-target`/scoped apply** — explicitly FORBIDDEN in v1 (bypasses lifecycle guards).
- Cost / blast-radius preview; multi-cloud (Azure/GCP); env-differentiated policy; state surgery
  (import/mv/rm, backend migration); auto-rollback (never — by contract).

---

## Architecture split (pure engine vs specialist-skill extensions vs orchestrate/protocol wiring)

**Pure engine — `tools/iac_apply.py` (NEW; the only new Python).** Mirrors the established recipe (pure decision/builder
logic, injectable, mutation-proof, zero execution surface). It consumes a **provided** plan/change-set artifact + the
approval/grant artifacts as plain bytes/dicts and returns argv lists, hashes, verdict dicts, and schema dicts. It calls
**no subprocess, no `eval`, no `exec`** (assertable by source scan, mirroring `drift_gate.py` `TestExecSafety`). The single
cloud-mutating function, `run_apply`, is the **deferred seam**: it raises `NotImplementedError` (mirrors
`drift_gate.structural_drift_verdict`).

**Specialist-skill extensions — `kata-iac-terraform` / `kata-iac-cloudformation`.** Worker-side authoring prose for the
Tier-2 preview/approve/capture flow, slotted at the existing Tier-1 boundary markers. They cite the engine surfaces by
name; they never re-implement gate logic in prose; they keep the never-tiered safety posture.

**Orchestrate/protocol wiring — `kata-orchestrate` + `protocol/{exec-safety,iac-safety}.md`.** Orchestrator-side: the
approval state-machine binding, the capability-gate → `human-required` escalation park (reuse), the parked-apply
guarantee, the append-only apply-audit log. Protocol: register the deferred sinks; add the Tier-2 contract section.

### exec-safety posture (CRITICAL — the apply sink is the highest-stakes in the repo)

- **Zero uncontrolled sink per slice.** `tools/iac_apply.py` spawns **no** subprocess and calls **no** `eval`/`exec`.
  The argv **builders** are pure functions returning a `list[str]` (program = `argv[0]`; the plan/change-set identifier
  is a positional DATA element, never the program, never shell-interpolated). `shell=False` is the only mode the builders
  describe; they never emit a shell string. The plan/apply EXECUTION is `run_apply`, which **raises `NotImplementedError`
  before any `subprocess` import** — un-triggerable without creds AND a present+matching approval AND a capability grant,
  and not runnable even then.
- **Identifier validation (anti-injection, mirrors `kata_preflight._validate_field_value` + `_safe_abs`):** every
  external/operator-supplied value that enters an argv (plan-file path, stack name, change-set name/ARN, var-file path) is
  `fullmatch`-anchored against an explicit grammar and `..`-guarded (CWE-23) BEFORE it enters the list; a leading `-` is
  rejected (flag injection) and `--` end-of-options is inserted before positional data. A value that cannot be expressed
  as a validated structured field is a NEW capability, not a reuse — STOP and escalate (per `protocol/exec-safety.md`
  "When the surface is not safe").
- **New (DEFERRED) sink rows** are added to the `protocol/exec-safety.md` registry with trust domain = **operator +
  approval-artifact gate** and guard = "structured argv, `shell=False`, present+matching approval + capability grant +
  creds required; **execution DEFERRED (raises `NotImplementedError`) — not shipped runnable.**" Because they are
  `shell=False`, they are **NOT** added to `_SHELL_TRUE_ALLOWLIST` — `test_exec_safety.py` stays green unchanged.

---

## Slices (disjoint ownership · Surfaces-by-name · default-FAIL runnable Acceptance · mutation targets · depends_on)

### Slice A — `tools/iac_apply.py` engine + tests  *(NEW Python; pure, mutation-proof, Snyk-scanned)*

**Owns:**
- `tools/iac_apply.py` (NEW)
- `tools/tests/test_iac_apply.py` (NEW)

**Surfaces (public, cite-able by name per `protocol/reuse-claims.md`):**
- `iac_apply.build_tf_plan_argv(*, chdir=None, out_path, var_files=()) -> list[str]` — pure; e.g.
  `["terraform", "-chdir", <dir>, "plan", "-input=false", "-lock=true", "-out", <out_path>, ...]`. `out_path`/`var_files`
  validated + `..`-guarded; **never `-target`** (FORBIDDEN — the builder has no such parameter). `shell=False` semantics.
- `iac_apply.build_tf_apply_argv(*, chdir=None, plan_file) -> list[str]` — e.g.
  `["terraform", "-chdir", <dir>, "apply", "-input=false", "-lock=true", "--", <plan_file>]`. **Applies the EXACT saved
  plan file** (the Atlantis discipline — the approved artifact IS the authorization; **never `-auto-approve`**, never a
  freeform target). `plan_file` validated + `..`-guarded.
- `iac_apply.build_cfn_create_changeset_argv(*, stack_name, change_set_name, template_path, change_set_type="UPDATE") -> list[str]`
  — `["aws", "cloudformation", "create-change-set", "--stack-name", <name>, "--change-set-name", <name>, "--template-body", "file://"+<path>, "--change-set-type", <UPDATE|CREATE>]`; all identifiers grammar-validated.
- `iac_apply.build_cfn_execute_changeset_argv(*, stack_name, change_set_id) -> list[str]` —
  `["aws", "cloudformation", "execute-change-set", "--stack-name", <name>, "--change-set-name", <change_set_id>]`. The
  **immutable `change_set_id` (ARN) is DATA**, the binding subject for CFN (see judgment calls). Because an ARN legally
  contains `:` and `/` (which the other identifier grammars forbid), `change_set_id` has its **OWN** `fullmatch`-anchored
  grammar, e.g. `^arn:aws:cloudformation:[a-z0-9-]+:\d{12}:changeSet/[A-Za-z0-9][A-Za-z0-9-]{0,127}/[0-9a-f-]{36}$`
  (still no whitespace, `;`, `|`, `..`, `://`, or leading `-`). Distinct from the stack-name/change-set-name grammar.
- `iac_apply.plan_hash(plan_bytes: bytes) -> str` — SHA-256 of the exact bytes that will be consumed at apply
  (mirrors the inline `hashlib.sha256(manifest_bytes)` H2 block in `kata_preflight.run_preflight`). **TF** = the binary
  `tfplan` bytes; **CFN** = the bytes of the **FULL `describe-change-set` response** (which embeds `ChangeSetId` /
  `StackId` / `StackName`), NOT just the `Changes` array — so the ARN + target stack fall WITHIN the hashed bytes and an
  approval cannot be replayed against a different change-set or stack (see judgment call #1).
- `iac_apply.load_approval(path) -> dict | None` — read the committable approval artifact; `None` if absent/malformed
  (mirrors `kata_preflight._load_approved_hash`).
- `iac_apply.approval_verdict(*, computed_plan_hash, approval) -> dict` — `{state, reason}`: `APPROVED` iff
  `approval["approvedPlanHash"] == computed_plan_hash`; `APPROVAL_INVALIDATED` on mismatch (re-plan changed the plan);
  `PENDING_PLAN`/`BLOCKED` otherwise. **Never collapses mismatch to pass** (mirrors kata_preflight H2 mismatch→blocked).
- `iac_apply.capability_gate_verdict(*, computed_plan_hash, destructive: list[dict], grant: dict | None) -> dict` —
  keys off the **`stateful: True`** entries from `iac_detect.scan_tf_plan` / `iac_detect.scan_cfn_changeset` (and, for
  static-source callers, `iac_detect._is_tf_stateful`/`_is_cfn_stateful`). For the most dangerous op the grant is
  **self-binding to the plan hash**: the gate clears ONLY when ALL THREE hold — (i)
  `grant["approvedPlanHash"] == computed_plan_hash` (the freshly-computed hash of the exact apply-consumed plan, so a
  STALE grant from a prior plan can never authorize a destroy even if the approval/grant artifacts are ever split);
  (ii) EVERY stateful destroy/replace `address`/`logicalId` is explicitly listed in `grant["authorizedStatefulAddresses"]`;
  and (iii) a typed `grant["confirmedToken"]` is present — a confirmation **distinct from a bare plan approval** (grill #3).
  Otherwise returns `CAPABILITY_REQUIRED`. A plan approval alone never authorizes a stateful destroy; a grant bound to a
  DIFFERENT plan hash never authorizes one either.
- `iac_apply.apply_state(*, computed_plan_hash, approval, destructive, grant, drift_detected, creds_present) -> str` —
  the state-machine resolver composing the above: one of
  `PENDING_PLAN · PLAN_CAPTURED · APPROVAL_INVALIDATED · CAPABILITY_REQUIRED · DRIFT_ABORT · CREDS_ABSENT · READY_DEFERRED · BLOCKED`.
  `drift_detected=True` → `DRIFT_ABORT` (real infra ≠ state; never proceed). The terminal success state is
  **`READY_DEFERRED`** (all gates pass) — it does NOT execute; it hands to the deferred seam.
- `iac_apply.iac_apply_schema() -> dict` — single source of truth for the sibling artifact `.kata/iac-apply.json`
  (mirrors `drift_gate.drift_schema` / `validation_misses.miss_schema`).
- `iac_apply.build_apply_audit_record(*, task_id, kind, plan_hash, state, actor, ts, rationale) -> dict` — one
  append-only audit row (actor/time/rationale — the SOC2/ISO substrate; append-only like `validation_misses.append_miss`).
- `iac_apply.run_apply(*args, **kwargs) -> dict` — **THE DEFERRED EXECUTION SEAM.** Raises `NotImplementedError`
  ALWAYS (mirrors `drift_gate.structural_drift_verdict`), with a message stating: n=0-live, creds-gated, requires a
  present+matching approval + capability grant, and that live execution arrives only behind authenticated cloud access.
  Stable name/signature (cite-able). No `subprocess` import on the path.

**Reuse (verify-before-reuse, cited surfaces):** `iac_detect.scan_tf_plan`/`scan_cfn_changeset` + `_is_tf_stateful`/
`_is_cfn_stateful` + `_TF_STATEFUL_*`/`_CFN_STATEFUL_*` (the stateful classification the capability-gate keys off) ·
`kata_preflight` H2 inline `hashlib.sha256(...)` + `_load_approved_hash` + `_DEFAULT_FREEZE_APPROVAL_FILENAME` pattern +
`_validate_field_value`/`_safe_abs` (the argv validators + CWE-23 guard) · `drift_gate.structural_drift_verdict` (the
NotImplementedError seam shape + its `TestExecSafety` source-scan).

**Acceptance (default-FAIL, runnable):**
- **Builders are structured + `shell=False`:** each `build_*_argv` returns a `list[str]` whose `argv[0]` is the program
  (`terraform`/`aws`) and whose plan/stack/change-set identifier is a non-first positional DATA element; assert the EXACT
  expected list for a known input. No element is a shell string; no builder accepts or emits `shell=True`.
- **Anti-injection:** a plan path / stack name / change-set name containing `;`, `|`, a leading `-`, `..`, or `://`
  raises `ValueError` (mirrors `_validate_package`/`_validate_field_value`); `--` separates positional data. A
  `change_set_id` that is NOT a well-formed CloudFormation change-set ARN (its dedicated grammar) raises `ValueError`;
  a valid ARN (containing `:` and `/`) is accepted by that grammar and rejected by the stricter stack-name grammar
  (the two grammars are distinct).
- **No `-target`:** `build_tf_plan_argv`/`build_tf_apply_argv` expose **no** target parameter and never emit `-target`
  (assert the token is absent from every produced argv).
- **No `-auto-approve`:** `build_tf_apply_argv` never emits `-auto-approve` (assert absent).
- **Plan-hash binding:** `approval_verdict` returns `APPROVED` iff `approvedPlanHash` == `plan_hash(plan_bytes)`; a
  one-byte change to the plan → `APPROVAL_INVALIDATED` (re-plan invalidates approval).
- **Capability-gate (typed, distinct, self-binding):** a plan with a stateful `delete`/replace and NO grant →
  `CAPABILITY_REQUIRED`; a grant whose `approvedPlanHash` matches but omits the stateful address → still
  `CAPABILITY_REQUIRED`; **a grant with a MISMATCHED `approvedPlanHash` but a valid `authorizedStatefulAddresses` ⊇ the
  stateful set + `confirmedToken` → still `CAPABILITY_REQUIRED`** (a stale grant from a prior plan cannot authorize this
  destroy); only `grant["approvedPlanHash"] == computed_plan_hash` AND `authorizedStatefulAddresses` ⊇ the stateful
  destroy set AND `confirmedToken` present → cleared. (Stateful set proven via a fixture exercising the `iac_detect`
  families.)
- **Drift-abort:** `apply_state(..., drift_detected=True, ...)` → `DRIFT_ABORT` regardless of approval/grant.
- **Execution seam un-triggerable:** `run_apply(...)` raises `NotImplementedError`; its docstring states the n=0-live /
  creds-gated LIMITATION (asserted, mirroring the `structural_drift_verdict` docstring test).
- **Zero execution surface:** an AST source scan of `tools/iac_apply.py` finds **no** `subprocess`, **no** `eval`/`exec`,
  **no** `shell=True` (mirrors `drift_gate` `TestExecSafety`).
- **Schema round-trip:** `iac_apply_schema()` keys match the documented `.kata/iac-apply.json` field set; audit record
  validates + is append-only-shaped.

**Mutation targets (non-vacuous):** (a) the `approval_verdict` `approvedPlanHash == computed_plan_hash` equality (flip →
false approval); (b) the capability-gate `authorizedStatefulAddresses ⊇ stateful-destroy-set` containment (weaken →
stateful destroy slips through on plan approval alone); (c) the **capability-gate's OWN `grant["approvedPlanHash"] ==
computed_plan_hash` self-binding equality** — removing this check must FAIL a test (a grant with a mismatched
`approvedPlanHash` + valid authorized-set + token must NOT clear); (d) the `drift_detected → DRIFT_ABORT` branch; (e) the
`stateful: True` filter feeding the capability-gate; (f) the `run_apply` raise (remove → the seam becomes a silent no-op /
fall-through).

**depends_on:** none (reuses Tier-1 surfaces by import).

---

### Slice B — exec-safety sink registration + iac-safety Tier-2 contract  *(protocol docs; depends_on A for surface names)*

**Owns:**
- `protocol/exec-safety.md` (register the deferred plan/apply sinks)
- `protocol/iac-safety.md` (add the Tier-2 section)

**Content — `protocol/exec-safety.md`:** add sink-registry rows for `iac_apply.run_apply` (the TF plan, TF apply, CFN
create-change-set, CFN execute-change-set argv flows) with **Domain = operator + approval-artifact gate** and Guard =
"structured argv built by `iac_apply.build_*_argv`; `shell=False`; the plan/change-set identifier is positional DATA;
gated on present+matching `kata.iac-apply-approval.json` + capability grant + creds; **execution DEFERRED — raises
`NotImplementedError` (n=0-live), not shipped runnable.**" Add a one-line note that these rows are `shell=False` and
therefore **NOT** in `_SHELL_TRUE_ALLOWLIST`. State the **zero-uncontrolled-sink posture** for the slice.

**Content — `protocol/iac-safety.md` "Tier 2 — live-apply preview/approve/capture (creds-gated; execution DEFERRED)"
section:** the safety pipeline (preview EXACT plan → human approve → **approval bound to a plan HASH** → plan-capture
artifact → apply DEFERRED → post-apply verify + captured recovery plan [design-level] → **never auto-rollback**); the
typed stateful-destroy capability-gate (distinct from approval; keys off `iac_detect` stateful sets / `scan_*`); the
remote-state+locking requirement; **pre-apply drift = abort/escalate**; state-surgery + `-target` OUT OF SCOPE; the
sibling `.kata/iac-apply.json` + the committable `kata.iac-apply-approval.json` (cite `iac_apply.iac_apply_schema` for the
field set). Keep the Tier-1 §1 "NO live apply" statement accurate by **scoping** it: Tier-1 stays author/analyze/gate;
Tier-2 builds preview/approve/capture but its apply EXECUTION remains DEFERRED behind the creds wall.

**Acceptance (default-FAIL, runnable):**
- `test_exec_safety.py` **green, unchanged** — the new rows are `shell=False` (AST scan finds no new `shell=True`); the
  doc-registration test still finds `mutation_run`/`run_result`; `_SHELL_TRUE_ALLOWLIST` is NOT modified.
- The exec-safety rows name `iac_apply.run_apply` + the four `build_*_argv` surfaces and label them DEFERRED/`shell=False`.
- The iac-safety Tier-2 section cites `iac_apply.iac_apply_schema`, `approval_verdict`, `capability_gate_verdict`,
  `run_apply` **by name** (anchors resolve to Slice A — no phantom reuse, `protocol/reuse-claims.md`).
- The Tier-1 §1 statement remains accurate (scoped, not contradicted).

**depends_on:** A (cites engine surfaces by name).

---

### Slice C — specialist-skill Tier-2 sections  *(skills/docs; depends_on A + B)*

**Owns:**
- `skills/execute/kata-iac-terraform/SKILL.md` (incl. its version bump)
- `skills/execute/kata-iac-cloudformation/SKILL.md` (incl. its version bump)
- (No NEW skill — both are edited. **README index is NOT owned by any slice** — its regeneration is centralized at the
  Integration gate; see F2.)

**Content:** at each skill's existing **"Tier 1 boundary: do NOT run `terraform plan`/`apply`"** (TF) and **"Tier 1
boundary: do NOT call `create-change-set`/`update-stack`"** (CFN) markers, slot a **"Tier 2 — preview/approve/capture
(n=0-live, creds-gated; apply EXECUTION DEFERRED)"** section: the worker authors the plan-capture + approval-binding +
capability-gate flow against the provided plan/change-set; cites `iac_apply.build_tf_plan_argv`/`build_tf_apply_argv`
(TF) or `build_cfn_create_changeset_argv`/`build_cfn_execute_changeset_argv` (CFN), `iac_apply.plan_hash`,
`iac_apply.approval_verdict`, `iac_apply.capability_gate_verdict` **by name**; states **never `-auto-approve`**, **never
`-target`**, **never auto-rollback**, and that `iac_apply.run_apply` is the DEFERRED seam (raises). Keep the
never-tiered + verify-before-reuse + default-FAIL constraints. The Tier-1 boundary text is **scoped** (Tier-1 still never
runs live), not deleted.

**Acceptance:**
- `validate_skills.py` (**read-only**, in-worktree) passes EXCEPT the expected "README index out of sync" error caused by
  the two version bumps — that error is the **integration-resolved consequence** (the conductor regenerates the README
  centrally at the Integration gate; **no slice runs `--write`**). Same skill count; both versions bumped.
- Each skill's Tier-2 section cites the real `iac_apply` surfaces by name (anchors resolve to Slice A).
- Each states explicitly: **n=0-live / creds-gated / apply execution DEFERRED / never `-auto-approve` / never `-target` /
  never auto-rollback**, and that the plan/change-set identifier is DATA (the builder is structured, `shell=False`).
- The Tier-1 "no live apply" boundary remains accurate (scoped).

**depends_on:** A (engine surfaces) + B (the Tier-2 contract section the skills point at).

---

### Slice D — kata-orchestrate approval-state-machine + park + audit wiring  *(skill; depends_on A)*

**Owns:** `skills/coordinate/kata-orchestrate/SKILL.md` — only the IaC region (adjacent to the Tier-1 IaC gate wiring).

**Content — "Tier 2 — apply approval state-machine (creds-gated; execution DEFERRED, all paths)":**
1. Orchestrator-side, mirroring how the Tier-1 IaC gate runs as a task's verify: compute `iac_apply.plan_hash` over the
   provided plan/change-set, run `iac_apply.apply_state(...)`, and write the sibling `.kata/iac-apply.json`
   (`iac_apply.iac_apply_schema`).
2. **`CAPABILITY_REQUIRED` and `APPROVAL_INVALIDATED` and `DRIFT_ABORT` → `human-required` escalation:** orchestrator
   calls `escalation.build_escalation` → `escalation.write_escalation` with `kind:"human-required"` and parks the task per
   the async park/drain path (`protocol/escalation.md`). **A parked apply stays parked — never auto-applies** (reuse).
3. **The minimal append-only apply-audit log:** append `iac_apply.build_apply_audit_record(...)` rows (actor/time/
   rationale) — reusing the escalation/board surfaces; no new sink.
4. **The apply EXECUTION is the deferred seam:** the terminal `READY_DEFERRED` state hands to `iac_apply.run_apply`,
   which raises `NotImplementedError`. The orchestrator NEVER wires a runnable cloud-mutating path. **`-target`/scoped
   apply is FORBIDDEN.** Creds-absent → `CREDS_ABSENT` (honest park), never a host-side apply.
5. Document that the whole Tier-2 apply path is **n=0-live, creds-gated**, and non-fatal to the existing loop (no IaC
   apply request ⇒ silent no-op; BC unchanged).

**Acceptance:**
- `validate_skills.py` (**read-only**, in-worktree) passes EXCEPT the expected "README index out of sync" error from the
  `kata-orchestrate` version bump — that error is the **integration-resolved consequence** (README regenerated centrally
  at the Integration gate; **this slice does NOT own the README and does NOT run `--write`**).
- The wiring cites `iac_apply.apply_state`, `iac_apply.plan_hash`, `iac_apply.iac_apply_schema`,
  `iac_apply.build_apply_audit_record`, `escalation.build_escalation`/`write_escalation` **by name**.
- States: capability/invalidation/drift → `human-required` park; **parked apply never auto-applies**; execution DEFERRED
  (`run_apply` raises); **`-target` FORBIDDEN**; creds-absent → honest park.
- **BC:** absent any IaC apply request ⇒ silent no-op; no Tier-1 verdict or artifact changes.

**depends_on:** A (engine surfaces); forward-refs B's Tier-2 contract by path.

---

## Wave DAG

```
ownership:
  A: [tools/iac_apply.py, tools/tests/test_iac_apply.py]
  B: [protocol/exec-safety.md, protocol/iac-safety.md]
  C: [skills/execute/kata-iac-terraform/SKILL.md, skills/execute/kata-iac-cloudformation/SKILL.md]
  D: [skills/coordinate/kata-orchestrate/SKILL.md]   # only the IaC region
  # README index: owned by NO slice — regenerated centrally by the conductor at the Integration gate (F2)
waves:
  - wave: 1
    slices: [A]
  - wave: 2
    slices: [B, D]      # both depend on A only; disjoint files (protocol/*.md vs orchestrate skill)
  - wave: 3
    slices: [C]         # depends on A + B (skills point at the Tier-2 contract section)
depends_on:
  A: []
  B: [A]
  C: [A, B]
  D: [A]
```
- **Wave 1:** A — the pure engine + tests (no deps; everything else cites its named surfaces).
- **Wave 2 (parallel, ≤2 workers, git worktrees, disjoint ownership verified):** B (protocol docs) + D (orchestrate wiring).
- **Wave 3:** C (specialist skills — needs both the engine and the Tier-2 contract section to cite).

---

## Safety invariants (PINNED — read before every slice)

1. **The stateful-destroy capability-gate is distinct from plan approval AND self-binding to the plan hash.** A
   destroy/replace on an `iac_detect`-stateful resource clears only when ALL THREE hold:
   `grant["approvedPlanHash"] == computed_plan_hash` (the grant is bound to THIS exact apply-consumed plan — a stale grant
   from a prior plan never authorizes a destroy, even if the approval/grant artifacts are ever split),
   `authorizedStatefulAddresses` ⊇ the stateful destroy set, and a typed `confirmedToken` is present (grill #3). A plan
   approval ALONE never authorizes it. Weakening this to "approval implies destroy" — or dropping the self-binding hash
   check — is the cardinal failure.
2. **Plan-hash invalidation.** Approval is bound to the SHA-256 of the EXACT bytes consumed at apply; any re-plan /
   plan change → `APPROVAL_INVALIDATED` (mirrors kata_preflight H2 mismatch→blocked). Approval is never reused across plans.
3. **Drift-abort.** Pre-apply drift (real infra ≠ state) → `DRIFT_ABORT` / escalate; never proceed. (v1 REQUIRES remote
   state + locking.)
4. **Never auto-rollback.** Post-apply verify + a captured recovery plan are **design-level**; no automated rollback ever.
5. **The execution is DEFERRED (n=0-live, creds-gated).** `iac_apply.run_apply` raises `NotImplementedError`; no
   subprocess on the path; reachable only behind a present+matching approval + capability grant + creds, and not runnable
   even then. The builders are pure structured-argv (`shell=False`); the plan/change-set identifier is DATA, never program.
   `-target`/scoped apply FORBIDDEN; `-auto-approve` never emitted. Zero uncontrolled sink.

## Artifact decision — Tier-2 adds a SIBLING artifact (does NOT extend `.kata/iac.json`)

**Decision (delegated to this plan by the grill):** add a **sibling** runtime artifact `.kata/iac-apply.json` (plus the
committable approval artifact `kata.iac-apply-approval.json`), **not** an extension of `.kata/iac.json`. **Why:**
- The D111 anti-fail-open guard makes `kata-evaluate` independently re-classify the footprint and treat an absent/malformed
  `.kata/iac.json` on IaC-classed changes as `NEEDS_WORK`. Injecting apply-lifecycle state into that artifact risks
  perturbing the fail-closed Tier-1 logic — a safety regression on the most safety-critical surface.
- Separation of concerns: `.kata/iac.json` = Tier-1 analysis FINDINGS (creds-free); `.kata/iac-apply.json` = Tier-2
  approval/capture/audit LIFECYCLE (creds-gated). Different producers, different trust, different lifecycle.
- The committable **approval input** lives at repo root (`kata.iac-apply-approval.json`), separate from the gitignored
  `.kata/` runtime artifact — tamper-resistance, mirroring kata_preflight's `kata.freeze-approval.json` (H2). The
  human-authored grant is not co-located with machine-written state.

This keeps Tier-1 byte-for-byte untouched and green. (Flagged below as a freeze-gate judgment call to confirm.)

## Integration gate (after the frontier drains)

`pytest` green incl. **`test_iac_apply.py`** · **`test_exec_safety.py` green and UNCHANGED** (no new `shell=True`; the
deferred sinks are `shell=False` registry rows; `_SHELL_TRUE_ALLOWLIST` untouched) · **Snyk code scan on
`tools/iac_apply.py`** (new first-party Python — CLAUDE.md; rescan-to-clean) · an explicit assertion that
`iac_apply.run_apply` raises (the seam is un-triggerable) and that the module has zero subprocess/eval/exec ·
`gate_emit` RESULT/footprint/mutation artifacts.

**README regeneration is centralized here, owned by the conductor — NOT by any slice (F2).** No slice runs
`validate_skills.py --write`; each version-bumping slice (C, D) tolerates the expected "README index out of sync" error
in its worktree as the integration-resolved consequence. After all slices land, the conductor runs
**`validate_skills.py --write` then `validate_skills.py`** once and confirms **0 errors / 0 warnings** (the two
specialists + `kata-orchestrate` edited, versions bumped, README index regenerated; no new skill — same count). This is
buildability only — no safety impact.

Then fresh-context **`kata-evaluate`** (default-FAIL; exercises the hash-binding, the typed capability-gate [incl. the
self-binding-hash case], drift-abort, and the deferred seam on seeded fixtures) → **freeze-gate `kata-review`** →
**operator merge gate.**

## Risks / escalation triggers

- **Over-reach destroys real infra (the existential risk).** The bound is the creds wall + the `NotImplementedError`
  seam. **If any slice starts making `run_apply` spawn a subprocess, read live state, or call a cloud MCP → STOP.** Live
  execution is a SEPARATE, n=0-live, creds-gated build with its own grill/DESIGN.
- **Capability-gate dilution (the #1 logic risk).** If a refactor lets plan approval imply stateful-destroy authorization,
  the typed gate is defeated. The mutation target (b) guards this; keep it non-vacuous.
- **Plan-hash binding-input ambiguity (judgment call, below).** Hashing the wrong bytes (the human-reviewed JSON vs the
  binary apply input) would let an approved-but-different plan apply. Resolve per the judgment call before freeze.
- **Tier-1 perturbation.** Do NOT touch `.kata/iac.json` shape or the D111 re-classification — the sibling artifact exists
  precisely to avoid this. STOP if a slice "needs" to change the Tier-1 artifact.
- **exec-safety regression.** Do NOT add the new sinks to `_SHELL_TRUE_ALLOWLIST` (they are `shell=False`); do NOT
  introduce `shell=True`. `test_exec_safety.py` must stay green untouched.
- **Scope creep into deferred items** (`-target`, cost preview, multi-cloud, state surgery, auto-rollback). All FORBIDDEN
  / OUT OF SCOPE here.
- **(N1 — note only, no change) Capability-gate completeness is INHERITED from Tier-1's stateful sets.** The gate keys off
  `iac_detect._TF_STATEFUL_*` / `_CFN_STATEFUL_*`; a data-bearing resource type MISSING from those sets would class
  non-stateful and could clear via plan approval without the typed grant. This is an **inherited Tier-1 property** (the
  same sets gate Tier-1 escalation), **not a Tier-2 regression** — flagged for awareness; the families were hardened in
  D110/D111 (D98 caught the original narrow set). A new gap is fixed in `iac_detect`, not here.

## Judgment calls for the freeze gate (confirm before SHIP)

1. **Plan-hash binding input (TF vs CFN asymmetry) — RESOLVE.** Proposed (derived from "approval bound to a plan HASH",
   not a new decision): **TF** — hash the **binary `tfplan` file** (the exact bytes `terraform apply` consumes), and
   ALSO capture `terraform show -json tfplan` for human review + `scan_tf_plan` destructive analysis; bind approval to the
   binary-plan hash (mirrors kata_preflight hashing the exact consumed bytes). **CFN** — a change-set is server-side and
   immutable once created, identified by `ChangeSetId` (ARN); bind approval to the **SHA-256 of the FULL
   `describe-change-set` response** — the full response (NOT just the `Changes` array) so that `ChangeSetId` / `StackId` /
   `StackName` fall WITHIN the hashed bytes; an approval therefore cannot be replayed against a different change-set or a
   different target stack. Freeze-gate to confirm this TF-binary-bytes / CFN-full-response-hash split.
2. **Sibling vs extend artifact — CONFIRM** the sibling `.kata/iac-apply.json` + committable
   `kata.iac-apply-approval.json` choice (rationale above; avoids perturbing the D111 fail-closed Tier-1 surface).
3. **Capability-grant shape — CONFIRM** `{approvedPlanHash, authorizedStatefulAddresses:[...], confirmedToken}` as the
   typed grant. The grant carries its OWN `approvedPlanHash` so the capability-gate is **self-binding** — it re-checks
   `grant["approvedPlanHash"] == computed_plan_hash` itself rather than trusting a separate `approval_verdict` call or
   artifact co-location; the `confirmedToken` makes the destroy authorization explicit + distinct from a bare plan approval.
4. **`apply_state` terminal-state names** (`READY_DEFERRED`, `CREDS_ABSENT`, `DRIFT_ABORT`, `CAPABILITY_REQUIRED`,
   `APPROVAL_INVALIDATED`) — confirm the vocabulary before skills/orchestrate cite it.

No unresolved grill points remain; every item above is either LOCKED by the grill or a derived specification flagged for
freeze-gate confirmation. If any reviewer finds a point that requires a NEW decision, **return to grill** — do not invent.
