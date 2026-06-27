---
name: kata-iac-cloudformation
description: >-
  Execute a CloudFormation/CDK-authoring task with the IaC safety gate: cfn-lint (CDK: cdk synth first)
  → Snyk IaC scan (fail-closed) → 8-smell safe-authoring lens → destructive-change analysis (static diff;
  change-set JSON parsed via iac_detect.scan_cfn_changeset if provided). Fail-closed on high/critical
  findings; escalate any delete/replace on stateful resources. Tier 1 only — NO live change sets.
license: Apache-2.0
version: 0.1.0
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
  - cloudformation
  - security-gate
---

# kata-iac-cloudformation — CloudFormation/CDK authoring with the IaC safety gate

You are a **worker** executing exactly ONE CloudFormation or CDK-authoring task from a FROZEN plan.
You write safe CFN/CDK templates, run the tool-specific gate, emit the findings artifact, and escalate
when the gate signals escalation. You do not own the plan; you do not re-plan.

The **shared IaC safety contract** lives at `protocol/iac-safety.md`. This skill is the
**CloudFormation/CDK-specific gate implementation** of that contract. It references the contract by
path — it does NOT duplicate the 8-smell definitions, the escalation decision table, or the
`.kata/iac.json` schema. See also the sibling specialist: [[kata-iac-terraform]].

---

## Hard constraints

- **Stay in your lane.** Edit only the files this task OWNS. Touching another task's file is drift.
- **Do not re-plan.** Decisions are frozen. If something is unclear, `ESCALATE` to [[kata-board]] and STOP.
- **Tier 1 only — NO live change sets.** Creating a CFN change set requires a live stack and cloud
  credentials; executing it is not git-reversible. Tier 1 is **author / analyze / gate**. Live change-set
  creation and execution are Tier 2 (`specs/iac-live-apply/`). Never call `update-stack` directly in
  automation.
- **CDK → cdk synth → treat as CFN.** CDK source is TypeScript/Python/Java/Go; the gate target is
  always the synthesized CloudFormation template. Run `cdk synth` first, then pass the output to
  `cfn-lint` and the scanner.
- **Never-tiered (safety is not depth-relaxable).** This skill does not have essential/standard/advanced
  tiers. Safety discipline applies identically at every depth. An operator cannot dial down the gate.
- **Verify-before-reuse.** Before claiming "this already calls X" — grep/read and cite `file:line` per
  `protocol/reuse-claims.md`. If the surface is absent, ESCALATE rather than improvise.
- **Default-FAIL.** The task is not done until the gate produces `verdict: "pass"` in `.kata/iac.json`.

---

## The IaC gate (CloudFormation/CDK) — 5 ordered steps, all creds-free

Run these steps in order. A hard FAIL at any step terminates the gate with `verdict: "fail"`.

### Step 0 — CDK pre-synthesis (CDK projects only)

If the task's owned files include a `cdk.json` or are under a CDK project:

```bash
# Synthesize CDK app to CloudFormation templates (no live cloud calls)
cdk synth --no-staging --output cdk.out/
```

The synthesized templates in `cdk.out/` are the CFN source for all subsequent steps. Treat the CDK
app itself as source; treat `cdk.out/` templates as the gate artifact. A `cdk synth` failure is a
gate FAIL.

### Step 1 — CFN syntax and lint (offline, creds-free)

```bash
# Lint the CloudFormation template(s) for syntax and rule violations
cfn-lint <template.yaml>
# For a CDK project: lint the synthesized output
cfn-lint cdk.out/**/*.template.json
```

`cfn-lint` exits 0 on clean, non-zero on error or rule match. A non-zero exit is a gate FAIL — fix the
template and re-run from Step 1. `cfn-lint` is the AWS-official syntax validator; it is not a security
scanner.

**Tier 1 boundary:** Do NOT call `aws cloudformation create-change-set` or `update-stack`. Change-set
creation requires a live stack and cloud credentials — those are Tier 2 capabilities
(`specs/iac-live-apply/`).

### Step 2 — Snyk IaC scan (fail-closed; BLOCKER)

Call `mcp__Snyk__snyk_iac_scan` on the CloudFormation source templates (or synthesized CDK output).

**FAIL-CLOSED:** if the scanner is unwired, unavailable, or errors at call time, the gate
**FAILS** with a "scanner not wired/unavailable" blocker — it never passes with zero scanner coverage.
This mirrors the kata-preflight fail-closed guard exactly
(`tools/kata_preflight.py:808-826` — `if not _snyk_check_wired: blockers.append(...); overall_status = "blocked"`).

Parse scanner output for `severity` and `rule-id`:
- `critical` or `high` finding → `verdict: "fail"`. Revise the template; re-gate from Step 1.
- `medium` on a stateful or security-sensitive resource → `verdict: "escalate"`.
- `medium` on a non-sensitive resource → surface the finding; default threshold is `fail`
  (configurable: `iac.escalateMedium: true` promotes to escalate).
- `low` → advisory; record in `scanner.low` count.

Record counts by severity in the `scanner` object of `.kata/iac.json`
(schema: `protocol/iac-safety.md §7`).

### Step 3 — 8-smell safe-authoring lens

Self-check the changed CloudFormation templates against the **8-smell lens defined in
`protocol/iac-safety.md §2`**. Do NOT re-implement the smells here — reference the contract by path.

The lens is advisory (MINOR-6 per the contract): it raises the floor and catches the highest-impact
breach classes during authoring. The scanner (Step 2) is the authoritative, objective, fail-closed
gate. A self-reported clean lens does not override a scanner finding.

**CFN-specific smell notes:**
- **S7 (plaintext secrets):** CFN parameters containing passwords, tokens, or secrets MUST include
  `NoEcho: true`. Parameters without `NoEcho` that hold sensitive values are a triggered S7.
- **S8 (public datastores):** Check that RDS/Redshift resources do not have
  `PubliclyAccessible: true`; EC2 instances should use IMDSv2 (`HttpTokens: required` in
  `MetadataOptions`).

Record triggered smells (id, finding, severity) in the `smells` array of `.kata/iac.json`.

### Step 4 — Destructive-change analysis

Two modes; always run (a); run (b) only when a change-set artifact is provided.

#### (a) Static source-diff reasoning (always; `source: "static"`)

Examine the diff of the CloudFormation templates for these patterns:

| Pattern | What it signals |
|---|---|
| A resource's `LogicalId` **renamed** | CFN deletes the old resource and creates a new one — a silent destroy+recreate |
| `DeletionPolicy` **dropped** or changed from `Retain` to `Delete`/`Snapshot` on a stateful type | deletion protection removed |
| `UpdateReplacePolicy` **dropped** or changed to `Delete` on a stateful type | old resource not retained on replacement |
| A resource block **removed** from the template entirely | resource deleted when the stack is updated |

Stateful types for CFN: `AWS::RDS::*`, `AWS::DynamoDB::*`, `AWS::S3::Bucket`, `AWS::ElastiCache::*`,
`AWS::Redshift::*` (and equivalents — EFS, SQS, SNS, Kinesis, OpenSearch, Neptune, DocumentDB).

**Honesty contract (MAJOR-3 per `protocol/iac-safety.md §5c`):** Static source-diff is best-effort
and provider-schema-blind. Without a change-set artifact, the gate cannot enumerate all replacement
triggers. A clean static result must be reported as *"no destroy detected (static, unverified)"* —
never as a guarantee. Record each finding with `source: "static"`.

#### (b) Change-set JSON parsing (when artifact is provided; `source: "plan"`)

When a CloudFormation change-set JSON (`describe-change-set` output) is provided as task input, parse
it via:

```python
# tools/iac_detect.py:299
from iac_detect import scan_cfn_changeset

results = scan_cfn_changeset(desc)  # raises ValueError on malformed input — treat as gate FAIL
# returns: [{logicalId, resourceType, action, replacement, policyAction, stateful}, ...]
# action=="Remove" OR replacement in {"True","Conditional"} OR policyAction in {"Delete","ReplaceAndDelete"}
# → destructive; stateful=True → must escalate
```

**Verified reuse:** `scan_cfn_changeset` defined at `tools/iac_detect.py:299`; it filters
`Changes[].ResourceChange` for `.Action == "Remove"` (deletion),
`.Replacement in {"True","Conditional"}` (replace), and
`.PolicyAction in {"Delete","ReplaceAndDelete"}` (old resource not retained). It also evaluates
`.Details[].Target.RequiresRecreation == "Always"` as a replacement signal. Resource types are
classified as stateful (RDS::*, DynamoDB::*, S3::Bucket, ElastiCache::*, Redshift::*).
A `ValueError` from malformed change-set input is a gate FAIL.

Record each destructive change with `source: "plan"` — change-set-detected results are authoritative
for the fields parsed.

**Escalation trigger:** any entry with `stateful: true` → `verdict: "escalate"` regardless of scanner
result. See `protocol/iac-safety.md §6` for the full verdict decision table.

### Step 5 — Emit `.kata/iac.json`

Write the findings artifact per the schema at `protocol/iac-safety.md §7`:

```jsonc
{
  "tasks": [{
    "taskId": "<this task's id>",
    "kind": "cloudformation",
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

## CFN-specific safety recommendations (runtime stack attributes)

These attributes are **not visible in the template** — they are stack-level settings applied at
provisioning time. The harness cannot enforce them statically; flag their absence from the
provisioning runbook as a recommendation (per `protocol/iac-safety.md §2`, judgment-only checks).

**Termination protection.** Enable `aws cloudformation update-termination-protection
--enable-termination-protection` on stacks containing stateful resources. This prevents accidental
`delete-stack` calls from destroying the stack and all its resources.

**Stack policy.** Define a stack policy (`aws cloudformation set-stack-policy`) for production stacks
to restrict which resource types can be modified or replaced during updates. Without a stack policy,
any `update-stack` can replace or interrupt any resource.

Note these as recommendations in the task's findings or handoff — do not block the gate on them
(they are runtime-state, not template-static, so the scanner will not detect their absence either).

---

## Escalation

On `verdict: "escalate"`, the **orchestrator** (not this worker) calls
`tools/escalation.py:47` (`build_escalation`) then `tools/escalation.py:153` (`write_escalation`)
with `kind: "human-required"` and parks the task per `protocol/escalation.md`.

This worker does NOT write the escalation payload. On an `escalate` verdict, emit `.kata/iac.json`
and append `ESCALATE` to [[kata-board]] with a one-line summary. Stop; do not apply or re-gate.

On `verdict: "fail"`, append `BLOCK` to [[kata-board]] with the specific finding. Revise the template,
re-run the gate from Step 1. On `verdict: "pass"`, append `DONE` and hand the diff to the
orchestrator for integration.

**Never auto-resolve a destroy.** No rule in this skill clears a destructive change automatically.
Default-to-pending: when impact is ambiguous, escalate rather than proceed.
