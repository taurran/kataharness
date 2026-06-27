# protocol/iac-safety.md — shared IaC safety contract

> **Tier 1 (author/review/gate).** Shared contract for `kata-iac-terraform` and `kata-iac-cloudformation`;
> both cite this file by path, never by wikilink. Machine-coordination text — these sections are
> **normative**: a deviation is a contract violation, not a style preference.

---

## 1. Purpose and scope

The IaC-safety specialists make the harness loop **safe with infrastructure-as-code**: when a task owns IaC
files, the worker receives an IaC-safety authoring profile and the task's gate runs a structured IaC safety
check — scanner + safe-authoring lens + destructive-change analysis — with a default-FAIL posture on high
and critical findings or any un-approved destroy/replace action.

**Tier 1 only — NO live apply.** The harness writes and analyzes IaC. It never runs a live
`terraform apply` or `execute-change-set`. The harness carries no cloud credentials; a live apply is not
git-reversible. Live apply is Tier 2 (`specs/iac-live-apply/`), a wholly separate contract requiring
authenticated cloud access, a non-git safety contract, destroy-as-operator-capability-gate, apply-failure
handling, cost gating, and an infra audit trail.

**Never-auto-mutate posture (D29/D109).** The harness's existing never-auto-mutate stance (kata-preflight)
applies without relaxation to IaC: the specialist WRITES and ANALYZES IaC; it does not deploy it. Any
temptation to auto-apply — even a "clean" plan — is a Tier 2 capability that is explicitly deferred. An
agent that writes or modifies IaC under this contract must never emit `--auto-approve` or its equivalent.

**Activation.** This contract activates when a task's owned files are detected as IaC by `tools/iac_detect.py`
(`.tf`/`.tf.json`/`.hcl` → terraform; `AWSTemplateFormatVersion`/`Resources` with `Type: AWS::*` → cloudformation;
`cdk.json`/`cdk.out/` → cdk; belt-and-suspenders: any `.yaml/.yml/.json` with a `Type:\s*AWS::` resource
declaration). Detection is best-effort; a fragment or unusual template may false-negative (MAJOR-5 — a miss
is a silent safety bypass; the `force-classify` config list shrinks but does not eliminate the gap).

---

## 2. The 8-smell safe-authoring lens (MINOR-6)

> **(MINOR-6) Scope statement — read before using this lens.** These eight smells are the **authoring
> worker's self-check**: a floor-raiser that catches the highest-impact breach classes during authoring,
> review-gated (not independently verified). They are **NOT independent assurance**. The scanner
> (`mcp__Snyk__snyk_iac_scan`) is the **authoritative, objective, fail-closed gate**. A clean self-reported
> `smells` list in `.kata/iac.json` does not mean no security findings exist — the scanner may still fail the
> gate. `kata-evaluate` reads the artifact but does not re-derive smells from it; a worker-reported clean lens
> is advisory only.

Self-check the following before the scanner runs. Each smell is a judgment-and-pattern check that raises the
floor; the scanner carries the exhaustive rule set.

| ID | Name | What to check |
|---|---|---|
| **S1** | IAM wildcards | `"*"` in action or resource on non-human principals; `AdministratorAccess` attached to roles/instance profiles (the #1 breach origin — over-permissive IAM). |
| **S2** | Open network ingress | `0.0.0.0/0` or `::/0` on sensitive ports (22/3389/5432/3306/1433/6379/etc.) in security-group ingress rules. |
| **S3** | Public storage | S3 `block_public_acls`/`block_public_policy`/`ignore_public_acls`/`restrict_public_buckets` unset or false; public ACL grants; Blob/GCS equivalents. |
| **S4** | Encryption at rest | Data stores (RDS, DynamoDB, S3, EBS, ElastiCache, Redshift, EFS) without `encrypted = true` or a KMS key reference. |
| **S5** | Encryption in transit | Endpoints without TLS enforcement; HTTP-to-HTTPS redirect disabled; `ssl_policy` absent on load-balancer listeners. |
| **S6** | Logging/audit disabled | CloudTrail multi-region trail absent; VPC flow logs off; DB audit logs / enhanced monitoring disabled; S3 server access logging off. |
| **S7** | Plaintext secrets | `AKIA*` / `password` / `token` / `secret` strings in params, env vars, or tags; CFN parameters missing `NoEcho: true`; long-lived static IAM access keys (`aws_iam_access_key`). |
| **S8** | Public datastores | RDS/Redshift `publicly_accessible = true`; public snapshots; EC2 instance metadata IMDSv2 not enforced (`http_tokens = "required"` absent). |

**Plus the judgment-only checks that scanners are structurally blind to (also baked — see §3):**

- Stateful-resource deletion protection: `lifecycle { prevent_destroy = true }` (TF) or
  `DeletionPolicy: Retain` / `UpdateReplacePolicy: Retain` (CFN) on data stores, queues, and other
  stateful types.
- Module/source provenance: untrusted registry paths or raw `git::` refs without a pinned revision.
- CFN termination protection and stack policy: runtime stack attributes not visible in the template —
  flag their absence from the worker's provisioning runbook as a recommendation.
- Plan-level destroy/replace analysis (§5 — no scanner detects this; it requires diff or plan parsing).

---

## 3. Bake-vs-delegate (the anti-cathedral line)

**Delegate to the scanner — never re-implement scanner logic in prose.** The scanner (`mcp__Snyk__snyk_iac_scan`)
carries 400+ rules from CIS/NIST/HIPAA/PCI/ISO covering all provider-service control IDs (EC2.x, RDS.x, S3.x,
CloudTrail.x, …), version/age rules, cross-resource relationships, compliance mapping, K8s/container
hardening, and OPA/Rego org policy. These are maintained externally and evolve with providers. Writing them
into prose would create a maintenance liability and a false confidence surface. The contract bakes only what
the scanner cannot and will not carry.

**Baked into this contract (small, durable, judgment/state-dependent):**
- The 8 smells (§2) — floor-raisers, highest-impact breach classes, augmented by judgment (S1/S7 require
  context the scanner has partially, not fully).
- Deletion-protection and `prevent_destroy` completeness — stateful resource lifecycle is a design-time
  decision, not a static rule match.
- Plan-level destroy/replace detection (§5) — no scanner detects this without a plan artifact.
- Safe-authoring discipline: never emit `--auto-approve`; always `DeletionPolicy`/`prevent_destroy` on
  stateful resources; module provenance review.
- Runtime-state checks (termination protection, stack policy) — recommendations only; not in the template.
- The plan→gate→human-approve→apply discipline (not executable in Tier 1, but governs what the worker writes
  and flags for downstream CI/human).

---

## 4. Scanner rule — fail-closed (BLOCKER)

The IaC gate calls `mcp__Snyk__snyk_iac_scan` on the IaC source. This is **new wiring** (N4 in DESIGN §2)
added by slice D, following the injectable + fail-closed seam pattern established in kata-preflight.

**Default-FAIL on high/critical.** Parse the scanner output for severity and rule-id; any `high` or
`critical` finding causes the gate to `fail`. The threshold is configurable via the `iac` config block
(`severity_threshold`); absent ⇒ default `high`.

**FAIL-CLOSED — the scanner-absent case is also a FAIL.** If the scanner callable is unwired, unavailable,
or errors at call time, the gate **FAILS** with a "scanner not wired/unavailable" blocker. The gate never
passes with zero scanner coverage. This mirrors the kata-preflight MINOR-3 fail-closed guard exactly
(`tools/kata_preflight.py:808-826`):

> ```python
> # tools/kata_preflight.py:808-826
> if not _snyk_check_wired:
>     blockers.append(
>         f"dep {name!r}: SCA scanner not wired — scan_required:true but no "
>         "snyk_check callable was provided; refusing to install without a scan "
>         "(LD3, MINOR 3). Wire mcp__Snyk__snyk_iac_scan or set "
>         "scan_required:false for an explicit opt-out."
>     )
>     ...
>     overall_status = "blocked"
>     continue
> ```

The IaC gate applies the same structure: `if not _iac_scanner_wired: blockers.append(...); overall_status = "blocked"`.
The MCP tool `mcp__Snyk__snyk_iac_scan` is available in the Snyk MCP toolset; wiring it is the slice D task.
**"Default-FAIL on high/critical" governs findings; "scanner-absent" is a separate, always-FAIL condition.**

**Scanner output fields to parse:** severity (`critical`/`high`/`medium`/`low`), rule-id, file path, line
number, and remediation hint. Record counts by severity in `.kata/iac.json` `scanner` object (§7).

---

## 5. Destructive-change rules

Destructive-change analysis is the part of the gate that no security scanner covers: it detects whether the
IaC change will **destroy or replace** existing infrastructure. Two modes, one per available artifact.

### 5a. Static source-diff reasoning (always run; `source: "static"`)

Examine the diff of the IaC source for these patterns:

**Terraform:**
- A `resource` block is **removed** entirely.
- A `for_each` or `count` key is **renamed or removed** — silently destroys all resources keyed to the old
  value (`action_reason: delete_because_each_key` / `delete_because_count_index`).
- An **immutable attribute** is changed on a stateful resource type (e.g. `engine`, `engine_version` on
  `aws_db_instance`; `availability_zone`, `volume_type` on `aws_ebs_volume`) — these force replacement
  without explicit naming.
- `lifecycle { prevent_destroy = true }` is **dropped** from a stateful resource.

**CloudFormation:**
- A resource's `LogicalId` is **renamed** — CFN deletes the old resource and creates a new one.
- `DeletionPolicy` is **dropped** or changed from `Retain` to `Delete`/`Snapshot` on a stateful type.
- `UpdateReplacePolicy` is **dropped** or changed to `Delete` on a stateful type.
- A resource block is **removed** from the template entirely.

### 5b. Plan/change-set JSON parsing (run when an artifact is provided; `source: "plan"`)

When a Terraform plan JSON or CloudFormation change-set JSON artifact is provided as input, parse it using
the destructive-parser in `tools/iac_detect.py`:

**Terraform plan JSON** (`terraform show -json tfplan`): filter
`resource_changes[].change.actions`:
- `["delete"]` — destroy.
- `["delete","create"]` or `["create","delete"]` — replace (destroys the old object; still a flag).
- Record `action_reason` for annotation (e.g. `delete_because_each_key` = accidental `for_each` rename).

**CloudFormation change-set JSON** (`describe-change-set`): filter
`Changes[].ResourceChange`:
- `.Action == "Remove"` — delete.
- `.Replacement in {"True","Conditional"}` — replace.
- `.PolicyAction in {"Delete","ReplaceAndDelete"}` — old resource not retained.
- `.Details[].Target.RequiresRecreation == "Always"` — replacement forced.

For each flagged change, classify the resource type as **stateful** (RDS/DynamoDB/S3/EBS/ElastiCache/Redshift/
EFS/SQS/SNS/Kinesis/OpenSearch/Neptune/DocumentDB and equivalents) or non-stateful.

### 5c. Honesty contract (MAJOR-3)

> **Static source-diff reasoning is best-effort and provider-schema-blind.**

Without a plan artifact, the gate cannot know which attribute changes force replacement — every IaC provider
has its own immutability rules, and they change with provider versions. Static analysis both **misses**
provider-forced replacements (false-negative: a changed attribute the static check doesn't know is immutable)
and may **over-flag** harmless changes (false-positive: a changed attribute that looks immutable but the
provider handles in-place).

**A clean static result is NOT a verified no-destroy.** Only a provided plan/change-set JSON is authoritative
(grounded in the provider's actual compute of the operation).

The `.kata/iac.json` artifact records the `source` field per destructive finding:
- `"source": "static"` — static diff only; result is best-effort, unverified.
- `"source": "plan"` — plan/change-set JSON parsed; result is authoritative for the fields parsed.

A static-only clean result must be reported as *"no destroy detected (static, unverified)"* — never as a
guarantee that no infrastructure will be destroyed.

---

## 6. Escalation mapping (MAJOR-4)

The gate's verdict is one of `pass`, `fail`, or `escalate`. The gate runs **orchestrator-side** as the task's
verify step. The three verdict values map to three orchestrator actions (never collapsed to two):

| Signal | Verdict | Orchestrator action |
|---|---|---|
| Scanner clean + no lens smells + no destructive change | `pass` | Integrate. |
| Scanner unwired / unavailable / errored | `fail` | Default-FAIL — blocker; fix loop (re-wire scanner, then re-gate). |
| Scanner high/critical finding | `fail` | Default-FAIL — revise + re-gate; not merely escalate. |
| CFN syntax / TF validate / fmt error | `fail` | Default-FAIL — fix syntax, re-gate. |
| Any destroy or replace on a **stateful** resource (static OR plan-detected) | `escalate` | Orchestrator writes `human-required` payload + parks task. |
| IAM / secrets / network-topology change | `escalate` | Orchestrator writes `human-required` payload + parks task. |
| Scanner medium finding touching a stateful/security-sensitive resource | `escalate` | Orchestrator writes `human-required` payload + parks task. |
| Scanner medium finding on non-sensitive resource, lens warn only | `fail` | Surface finding; default-FAIL fix loop (configurable: `escalate_medium: true` in `iac` config block). |

**Verdict → producer mapping.** The gate is run by the **orchestrator** as the task's verify, so:
- `verdict: "escalate"` → the **orchestrator** calls `build_escalation` then `write_escalation`
  (`tools/escalation.py:47` and `tools/escalation.py:153`) with `kind: "human-required"` and parks the task
  per the existing async park/drain/hard-wait path (`protocol/escalation.md`). The **worker does not** write
  the escalation payload on an `escalate` verdict.
- `verdict: "fail"` → routes into the orchestrator's normal default-FAIL fix loop: the worker revises the IaC
  and the gate re-runs.
- `verdict: "pass"` → the orchestrator proceeds to integrate.

The three-valued verdict is never silently collapsed: `escalate` must not become `fail` (losing the human
signal) and `fail` must not become `pass` (defeating the scanner). Cite `protocol/escalation.md` for the
full escalation payload schema and lifecycle.

**Never auto-resolve a destroy.** No rule clears a destroy automatically — `default-to-pending` (env0
pattern): when impact is ambiguous or no rule clears it, escalate, don't proceed. An approval is invalidated
if the plan changes (the harness's freeze/re-gate embodies this).

---

## 7. `.kata/iac.json` artifact schema

Written by the IaC gate at step 5 of the gate sequence (DESIGN §3). Read by `kata-evaluate` at the
integration gate; unresolved high/critical findings or an un-approved destroy ⇒ `NEEDS_WORK`.

```jsonc
{
  "tasks": [
    {
      "taskId": "<string>",          // task identifier (matches the task's taskId)
      "kind": "terraform" | "cloudformation",  // IaC kind detected
      "scanner": {
        "critical": <int>,           // count of critical-severity findings
        "high":     <int>,           // count of high-severity findings
        "med":      <int>,           // count of medium-severity findings
        "low":      <int>,           // count of low-severity findings
        "wired":    <bool>,          // false if scanner was unwired/errored (gate: fail)
        "error":    "<string>|null"  // scanner error message if wired=false
      },
      "smells": [
        {
          "id":      "S1".."S8",     // smell identifier from §2
          "finding": "<string>",     // one-line description of what was found
          "severity": "warn"|"flag"  // warn = advisory; flag = escalate-candidate
        }
        // ... one entry per triggered smell; empty array if none
      ],
      "destructive": [
        {
          "address":  "<string>",    // TF resource address or CFN logical ID
          "action":   "delete"|"replace"|"delete+create",
          "stateful": <bool>,        // true if resource type is stateful (§5b)
          "source":   "static"|"plan"  // which analysis mode detected this (§5c)
        }
        // ... one entry per destructive change detected; empty array if none
      ],
      "verdict": "pass" | "fail" | "escalate"  // §6
    }
    // ... one entry per IaC-classed task in the run
  ]
}
```

**Field notes:**
- `scanner.wired: false` forces `verdict: "fail"` regardless of all other fields (fail-closed, §4).
- `destructive` entries with `stateful: true` force `verdict: "escalate"` regardless of scanner result (§6).
- `smells` entries do not independently force a verdict; they are advisory inputs to the scanner and
  destructive-change verdict logic.
- `source: "static"` on a `destructive` entry must be treated as unverified (MAJOR-3, §5c); the human
  reviewer must be informed of this when `verdict: "escalate"` is written.
- If no IaC files are detected for a run, no `.kata/iac.json` is written and `kata-evaluate` treats its
  absence as no IaC finding (BC — no change to artifacts or verdicts for non-IaC tasks, MINOR-7).

---

## 8. Key citations (verify-before-reuse per `protocol/reuse-claims.md`)

| Claim | Verified surface |
|---|---|
| Fail-closed scanner-absent pattern | `tools/kata_preflight.py:808-826` — `if not _snyk_check_wired: blockers.append(...); overall_status = "blocked"` |
| `build_escalation` signature | `tools/escalation.py:47` — `def build_escalation(taskId, kind, decisionNeeded, optionsConsidered, agentRecommendation, rationale, ...)` |
| `write_escalation` signature | `tools/escalation.py:153` — `def write_escalation(kata_dir: str, payload: dict) -> str` |
| Escalation payload schema + lifecycle | `protocol/escalation.md` — `kind: "human-required"` path + async park/drain |
| Verify-before-reuse guard | `protocol/reuse-claims.md` — LD3 guard text + `file:line` requirement |
| Never-auto-mutate posture | DESIGN §1 IAC-2 / RESEARCH §1 — D29/D109, confirmed locked |
| IaC gate sequence (5 steps) | DESIGN §3 steps 1–5 |
| N4 scanner = new wiring (not pre-existing reuse) | DESIGN §2 N4 — "called nowhere today" |
| Snyk IaC MCP tool availability | DESIGN §1 IAC-4 — "available in the Snyk MCP toolset" |
| TF plan JSON `resource_changes[].change.actions` | RESEARCH §2 — `["delete"]`, `["delete","create"]` |
| CFN change-set `Changes[].ResourceChange` fields | RESEARCH §2 — `.Action`, `.Replacement`, `.PolicyAction` |
| 8 smells source | RESEARCH §4 — S1–S8 with context |
| Bake-vs-delegate line | RESEARCH §5 — "Never re-implement scanner logic in prose" |
| Escalation decision table | RESEARCH §6 → DESIGN §4 |
