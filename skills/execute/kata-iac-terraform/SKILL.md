---
name: kata-iac-terraform
description: >-
  Execute a Terraform-authoring task with the IaC safety gate: terraform fmt -check + validate
  (offline, creds-free) → Snyk IaC scan (fail-closed) → 8-smell safe-authoring lens → destructive-change
  analysis (static diff; plan JSON parsed via iac_detect.scan_tf_plan if provided). Fail-closed on
  high/critical findings; escalate any destroy/replace on stateful resources. Tier 1 only — NO live
  terraform plan or apply.
license: Apache-2.0
version: 0.2.0
category: execute
status: experimental
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Bash, Write]
source: >-
  new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract
  protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4)
tags:
  - kata/execute
  - kata/module/iac
  - iac
  - terraform
  - security-gate
---

# kata-iac-terraform — Terraform authoring with the IaC safety gate

You are a **worker** executing exactly ONE Terraform-authoring task from a FROZEN plan.
You write safe Terraform, run the tool-specific gate, emit the findings artifact, and escalate when the
gate signals escalation. You do not own the plan; you do not re-plan.

The **shared IaC safety contract** lives at `protocol/iac-safety.md`. This skill is the
**Terraform-specific gate implementation** of that contract. It references the contract by path — it does
NOT duplicate the 8-smell definitions, the escalation decision table, or the `.kata/iac.json` schema.
See also the sibling specialist: [[kata-iac-cloudformation]].

---

## Hard constraints

- **Stay in your lane.** Edit only the files this task OWNS. Touching another task's file is drift.
- **Do not re-plan.** Decisions are frozen. If something is unclear, `ESCALATE` to [[kata-board]] and STOP.
- **Tier 1 only — NO live plan or apply.** The harness carries no cloud credentials; `terraform plan`
  requires creds + a state backend; `terraform apply` is not git-reversible. Tier 1 is
  **author / analyze / gate**. Generating or executing a live plan is Tier 2 (`specs/iac-live-apply/`).
  Never emit `--auto-approve` or any equivalent.
- **Never-tiered (safety is not depth-relaxable).** This skill does not have essential/standard/advanced
  tiers. Safety discipline applies identically at every depth. An operator cannot dial down the gate.
- **Verify-before-reuse.** Before claiming "this already calls X" — grep/read and cite `file:line` per
  `protocol/reuse-claims.md`. If the surface is absent, ESCALATE rather than improvise.
- **Default-FAIL.** The task is not done until the gate produces `verdict: "pass"` in `.kata/iac.json`.

---

## The IaC gate (Terraform) — 5 ordered steps, all creds-free

Run these steps in order. A hard FAIL at any step terminates the gate with `verdict: "fail"`.

### Step 1 — Syntax and validation (offline, creds-free)

```bash
# Check formatting (non-zero exit = formatting error; gate FAIL)
terraform fmt -check -recursive

# Validate configuration syntax and references (offline — no live state or provider credentials needed)
terraform validate
```

Both commands must exit 0. A non-zero exit is a hard FAIL — fix the error and re-run from Step 1.
These are offline commands: `terraform validate` initializes providers from the lock file only; it does
not contact cloud APIs or require a configured backend.

**Tier 1 boundary:** Do NOT run `terraform plan` or `terraform apply`. Plan generation requires live
cloud credentials and a state backend — those are Tier 2 capabilities (`specs/iac-live-apply/`).

#### Tier 2 — preview / approve / capture (n=0-live, creds-gated; apply EXECUTION DEFERRED)

> **This section is ADDITIVE and creds-FREE.** It does NOT relax the Tier-1 boundary above: this
> specialist still never runs a live `terraform plan`/`apply`. Tier 2 is the **preview/approve/capture
> half** of the separate contract — it operates on a **provided** plan artifact (exactly as Step 4(b)'s
> `scan_tf_plan` operates on a provided `plan_json`). The full Tier-2 contract is
> `protocol/iac-safety.md §9` (DRY-by-pointer — do NOT restate or fork it here).

When the FROZEN plan assigns a Tier-2 preview task, this specialist's role is the **author/produce →
approve-bind → capture → HAND-OFF → STOP** half. It NEVER executes a cloud mutation.

1. **Author the EXACT plan-capture command (structured argv, `shell=False`).** The plan that will be
   reviewed and (deferred) applied is produced by `terraform plan -out <tfplan>` — its argv is built by
   `iac_apply.build_tf_plan_argv` (`-input=false`, `-lock=true`, `-out <path>`; **no `-target`** — the
   builder exposes no such parameter, §9.5). The out-path is DATA, grammar-validated + `..`-guarded;
   never a shell string. Live generation of the plan is **creds-gated and DEFERRED** — author the EXACT
   command shape; the actual run arrives only behind authenticated cloud access.
2. **Bind approval to the plan HASH.** The captured binary `tfplan` is hashed by `iac_apply.plan_hash`
   (the exact bytes `terraform apply` would consume). The human approval in the committable
   `kata.iac-apply-approval.json` is bound to that hash; `iac_apply.approval_verdict` returns `APPROVED`
   **iff** `approvedPlanHash == computed_plan_hash`. Any re-plan changes the bytes → `APPROVAL_INVALIDATED`
   — approval is never reused across plans (§9.1).
3. **Typed stateful-destroy capability-gate (distinct from approval).** Any destroy/replace on an
   `iac_detect`-stateful resource (from Step 4(b)'s `scan_tf_plan`, `stateful: true`) requires a typed
   grant **separate from a bare plan approval**; `iac_apply.capability_gate_verdict` clears ONLY when the
   grant is self-bound to this exact plan hash, lists every stateful address, and carries a typed
   `confirmedToken` (§9.1). A plan approval ALONE never authorizes a stateful destroy.
4. **Hand the captured plan to the orchestrate Tier-2 apply state-machine, then STOP.** The orchestrator
   composes the terminal state via `iac_apply.apply_state` (see [[kata-orchestrate]] "Tier 2 — apply
   approval state-machine"). The success terminal is **`READY_DEFERRED`** — it does **not** execute. This
   specialist does NOT call apply; `iac_apply.build_tf_apply_argv` (applies the EXACT saved plan file —
   **never `-auto-approve`**, never a freeform target) describes the deferred command only.
5. **The cloud EXECUTION is the DEFERRED seam.** `READY_DEFERRED` hands to `iac_apply.run_apply`, which
   raises `NotImplementedError` ALWAYS (n=0-live, creds-gated; reachable only behind a present+matching
   approval + capability grant + creds, and not runnable even then). **Never auto-rollback** — a captured
   recovery plan is design-level, for a human (§9.1, §9.5).

Loud honesty: the whole Tier-2 apply path is **n=0-live / creds-gated / execution DEFERRED**. Apply does
not "work" here. The plan/change-set identifier is always **DATA** in a structured `shell=False` argv —
never program, never shell-interpolated (§9.4, §9.6).

### Step 2 — Snyk IaC scan (fail-closed; BLOCKER)

Call `mcp__Snyk__snyk_iac_scan` on the Terraform source files.

**FAIL-CLOSED:** if the scanner is unwired, unavailable, or errors at call time, the gate
**FAILS** with a "scanner not wired/unavailable" blocker — it never passes with zero scanner coverage.
This mirrors the kata-preflight fail-closed guard exactly
(the SCA fail-closed guard in `run_preflight`, `tools/kata_preflight.py` — `if not _snyk_check_wired: blockers.append(...); overall_status = "blocked"`).

Parse scanner output for `severity` and `rule-id`:
- `critical` or `high` finding → `verdict: "fail"`. Revise the IaC; re-gate from Step 1.
- `medium` on a stateful or security-sensitive resource → `verdict: "escalate"`.
- `medium` on a non-sensitive resource → surface the finding; default threshold is `fail`
  (configurable: `iac.escalateMedium: true` promotes to escalate).
- `low` → advisory; record in `scanner.low` count.

Record counts by severity in the `scanner` object of `.kata/iac.json`
(schema: `protocol/iac-safety.md §7`).

### Step 3 — 8-smell safe-authoring lens

Self-check the changed Terraform against the **8-smell lens defined in `protocol/iac-safety.md §2`**.
Do NOT re-implement the smells here — reference the contract by path.

The lens is advisory (MINOR-6 per the contract): it raises the floor and catches the highest-impact
breach classes during authoring. The scanner (Step 2) is the authoritative, objective, fail-closed
gate. A self-reported clean lens does not override a scanner finding.

Record triggered smells (id, finding, severity) in the `smells` array of `.kata/iac.json`.

### Step 4 — Destructive-change analysis

Two modes; always run (a); run (b) only when a plan artifact is provided.

#### (a) Static source-diff reasoning (always; `source: "static"`)

Examine the diff of the Terraform source for these patterns:

| Pattern | What it signals |
|---|---|
| A `resource` block **removed** entirely | destroy |
| A `for_each` or `count` key **renamed or removed** | silent destroy of all resources keyed to the old value (`action_reason: delete_because_each_key` / `delete_because_count_index`) — the #1 accidental-deletion cause |
| An **immutable attribute** changed on a stateful resource type (e.g. `engine`/`engine_version` on `aws_db_instance`; `availability_zone`/`volume_type` on `aws_ebs_volume`) | provider-forced replacement (destroy + recreate) |
| `lifecycle { prevent_destroy = true }` **dropped** from a stateful resource | destroy protection removed |

**Honesty contract (MAJOR-3 per `protocol/iac-safety.md §5c`):** Static source-diff is best-effort and
provider-schema-blind. Without a plan artifact, the gate cannot know which attribute changes force
replacement — every provider has its own immutability rules, and they change with provider versions. A
clean static result must be reported as *"no destroy detected (static, unverified)"* — never as a
guarantee that no infrastructure will be destroyed. Record each finding with `source: "static"`.

#### (b) Plan JSON parsing (when artifact is provided; `source: "plan"`)

When a Terraform plan JSON (`terraform show -json tfplan`) is provided as task input, parse it via:

```python
# iac_detect.scan_tf_plan
from iac_detect import scan_tf_plan

results = scan_tf_plan(plan_json)  # raises ValueError on malformed input — treat as gate FAIL
# returns: [{address, type, actions, action_reason, stateful}, ...]
# "delete" in actions → destructive; stateful=True → must escalate
# (action_reason is read from the resource-change object — a SIBLING of `change`)
```

**Verified reuse:** `iac_detect.scan_tf_plan`; it filters
`resource_changes[].change.actions` for `"delete"` (covers `["delete"]`, `["delete","create"]`,
`["create","delete"]`) and classifies resource types as stateful (RDS, DynamoDB, S3, EBS,
ElastiCache-*, Redshift-*). A `ValueError` from malformed plan input is a gate FAIL
(returning `[]` silently on corrupt input would be a safety bypass per the module's contract).

Record each destructive change with `source: "plan"` — plan-detected results are authoritative for
the fields parsed.

**Escalation trigger:** any entry with `stateful: true` → `verdict: "escalate"` regardless of scanner
result. See `protocol/iac-safety.md §6` for the full verdict decision table.

### Step 5 — Emit `.kata/iac.json`

Write the findings artifact per the schema at `protocol/iac-safety.md §7`:

```jsonc
{
  "tasks": [{
    "taskId": "<this task's id>",
    "kind": "terraform",
    "scanner": { "critical": 0, "high": 0, "med": 0, "low": 0, "wired": true, "error": null },
    "smells":      [ /* triggered smells; empty if none */ ],
    "destructive": [ /* {address, action, stateful, source:"static"|"plan"}; empty if none */ ],
    "verdict": "pass" | "fail" | "escalate"
  }]
}
```

Verdict rules (from `protocol/iac-safety.md §6` — authoritative; these are reminders only):
- `scanner.wired: false` → `fail` (fail-closed; §4).
- Any `critical` or `high` scanner finding → `fail`.
- Any `destructive` entry with `stateful: true` → `escalate`.
- IAM / secrets / network-topology change → `escalate`.
- No findings, clean lens, no destructive change → `pass`.

---

## State hazards (Terraform-specific)

These hazards apply even in Tier 1 (authoring-time decisions affect Tier 2 outcomes):

**`prevent_destroy` is a partial guard only.**
`lifecycle { prevent_destroy = true }` prevents `terraform plan/apply` from destroying the resource,
but it does NOT guard against `terraform state rm` (removes from state without destroying), `terraform
import` collisions, manual state file edits, or `--target`-scoped applies that bypass the lifecycle.
When marking a resource with `prevent_destroy`, note in comments that state manipulation can bypass it.

**State locking (advisory — Tier 2 concern, worth authoring for).**
Remote state backends (S3+DynamoDB, GCS, Azure Blob) must have locking enabled to prevent concurrent
applies from corrupting state. The harness does not modify state, but when authoring backend
configuration, always include the locking configuration (e.g. `dynamodb_table` for S3 backend).

---

## Escalation

On `verdict: "escalate"`, the **orchestrator** (not this worker) calls
`tools/escalation.py:47` (`build_escalation`) then `tools/escalation.py:153` (`write_escalation`)
with `kind: "human-required"` and parks the task per `protocol/escalation.md`.

This worker does NOT write the escalation payload. On an `escalate` verdict, emit `.kata/iac.json`
and append `ESCALATE` to [[kata-board]] with a one-line summary. Stop; do not apply or re-gate.

On `verdict: "fail"`, append `BLOCK` to [[kata-board]] with the specific finding. Revise the IaC,
re-run the gate from Step 1. On `verdict: "pass"`, append `DONE` and hand the diff to the
orchestrator for integration.

**Never auto-resolve a destroy.** No rule in this skill clears a destructive change automatically.
Default-to-pending: when impact is ambiguous, escalate rather than proceed.
