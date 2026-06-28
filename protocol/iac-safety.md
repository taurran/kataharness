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
declaration; extension matching is **case-insensitive** so `Stack.YAML`/`main.TF`/`deploy.Template` do not
skip the gate). Detection is best-effort; a fragment or unusual template may false-negative (MAJOR-5 — a miss
is a silent safety bypass; the `forceClassify` config map is **wired into `iac_detect.classify_task` at
dispatch** [a matched glob→kind override wins over auto-detection] and shrinks, but does not eliminate, the gap).

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
(`severityThreshold`); absent ⇒ default `high`.

**FAIL-CLOSED — the scanner-absent case is also a FAIL.** If the scanner callable is unwired, unavailable,
or errors at call time, the gate **FAILS** with a "scanner not wired/unavailable" blocker. The gate never
passes with zero scanner coverage. This mirrors the kata-preflight MINOR-3 fail-closed guard exactly
(the SCA fail-closed guard in `run_preflight`, `tools/kata_preflight.py`):

> ```python
> # the SCA precedent — the scanner-not-wired guard in run_preflight (quoted verbatim; the IaC gate applies the SAME structure with snyk_iac_scan)
> if not _snyk_check_wired:
>     blockers.append(
>         f"dep {name!r}: SCA scanner not wired — scan_required:true but no "
>         "snyk_check callable was provided; refusing to install without a scan "
>         "(LD3, MINOR 3). Wire mcp__Snyk__snyk_sca_scan or set "
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
EFS/SQS/SNS/Kinesis/OpenSearch/Neptune/DocumentDB/**KMS/SecretsManager/Backup/FSx/MSK/CloudWatch-Logs/
Timestream/QLDB/MemoryDB/Keyspaces** and equivalents — see `iac_detect._TF_STATEFUL_*` / `_CFN_STATEFUL_*`
for the authoritative families) or non-stateful.

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
| Destroy or replace on a **non-stateful** resource (static OR plan-detected) | `fail` | Surface the finding; default-FAIL fix loop. If the resource later proves security-sensitive, re-classify to `escalate`. Never silently pass a detected destroy. |
| IAM / secrets / network-topology change | `escalate` | Orchestrator writes `human-required` payload + parks task. |
| Scanner medium finding touching a stateful/security-sensitive resource | `escalate` | Orchestrator writes `human-required` payload + parks task. |
| Scanner medium finding on non-sensitive resource, lens warn only | `fail` | Surface finding; default-FAIL fix loop (configurable: `escalateMedium: true` in `iac` config block). |

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
- If no IaC files are detected for a run, no `.kata/iac.json` is written. `kata-evaluate` does **not** trust
  this by presence alone: it independently re-classifies the footprint's changed files
  (`iac_detect.classify_task`) and only treats absence as "no IaC finding" when no changed file is IaC-classed
  (BC, MINOR-7). A changed IaC file with no `.kata/iac.json` ⇒ **NEEDS_WORK** (skipped/crashed gate cannot pass).

---

## 8. Key citations (verify-before-reuse per `protocol/reuse-claims.md`)

| Claim | Verified surface |
|---|---|
| Fail-closed scanner-absent pattern | the SCA fail-closed guard in `run_preflight` (`tools/kata_preflight.py`) — `if not _snyk_check_wired: blockers.append(...); overall_status = "blocked"` |
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

---

## 9. Tier 2 — live-apply preview/approve/capture (creds-gated; execution DEFERRED)

> **Scope reconciliation (Tier-1 §1 stays accurate).** §1's "Tier 1 only — NO live apply" remains true and is
> **not weakened**. This section is the preview/approve/plan-capture **half** of the separate Tier-2 contract
> §1 already points at (`specs/iac-live-apply/`). It builds the **pure** preview→approve→capture machinery and
> **STOPS at the creds wall**: the actual cloud EXECUTION (running `terraform plan` to generate a plan,
> `terraform apply`, `aws cloudformation execute-change-set`, and any live state read) is the **DEFERRED,
> n=0-live seam** — `iac_apply.run_apply` raises `NotImplementedError` and is **never wired runnable** here.
> The engine is `tools/iac_apply.py`; it consumes a **provided** plan/change-set artifact exactly as Tier-1
> `scan_tf_plan` consumes a provided `plan_json`. Everything below is creds-FREE.

### 9.1 The apply lifecycle (preview → approve → plan-hash binding → capability-gate → READY_DEFERRED)

1. **Preview the EXACT plan/change-set.** The lifecycle operates on the exact artifact that would be consumed
   at apply (TF: the binary `tfplan`; CFN: the full `describe-change-set` response) — not a re-derived summary.
2. **Human approves.** Approval is recorded in the committable `kata.iac-apply-approval.json`
   (`iac_apply.build_approval_artifact`; read via `iac_apply.load_approval`).
3. **Plan-hash binding (re-plan invalidates — mirrors kata-preflight H2).** Approval is bound to the SHA-256 of
   the EXACT apply-consumed bytes: `iac_apply.plan_hash` over the binary `tfplan` (TF) or over
   `iac_apply.canonical_cfn_plan_bytes(describe_change_set)` (CFN — the FULL response so `ChangeSetId`/`StackId`/
   `StackName` fall WITHIN the hashed bytes, defeating replay against a different change-set or stack).
   `iac_apply.approval_verdict` returns `APPROVED` **iff** `approvedPlanHash == computed_plan_hash`; any re-plan
   or plan change → `APPROVAL_INVALIDATED`. Mismatch is **never** collapsed to a pass. Approval is never reused
   across plans.
4. **Typed stateful-destroy capability-gate (distinct from plan approval; self-binding).** For any destroy/
   replace on a resource classed **stateful** by `iac_detect` (`scan_tf_plan` / `scan_cfn_changeset`; the
   `_TF_STATEFUL_*` / `_CFN_STATEFUL_*` families of §5b), `iac_apply.capability_gate_verdict` clears ONLY when
   ALL THREE hold: (i) `grant["approvedPlanHash"] == computed_plan_hash` (self-binding — a stale grant from a
   prior plan can never authorize a destroy, even if approval/grant artifacts are split); (ii)
   `authorizedStatefulAddresses` ⊇ the full stateful-destroy set; (iii) a typed `confirmedToken` is present.
   **A plan approval ALONE never authorizes a stateful destroy** (grill #3). The grant shape is
   `iac_apply.build_capability_grant` (`{approvedPlanHash, authorizedStatefulAddresses, confirmedToken}`).
5. **Terminal `READY_DEFERRED` hands to the deferred seam — it does NOT execute.** `iac_apply.apply_state`
   composes approval + capability + drift + creds and resolves to one of
   `PENDING_PLAN · PLAN_CAPTURED · APPROVAL_INVALIDATED · CAPABILITY_REQUIRED · DRIFT_ABORT · CREDS_ABSENT ·
   READY_DEFERRED · BLOCKED`. The success terminal `READY_DEFERRED` hands to `iac_apply.run_apply`, which raises
   `NotImplementedError`. It is **not** an executed apply.
6. **Post-apply verify + captured recovery plan are design-level.** **Never auto-rollback** — no automated
   rollback ever (a captured recovery plan is for a human, not the harness).

### 9.2 Drift-abort (remote-state-required)

v1 **REQUIRES remote state + locking**. Pre-apply drift (real infra ≠ recorded state) is a hard abort:
`iac_apply.apply_state(..., drift_detected=True, ...)` → `DRIFT_ABORT` regardless of approval/grant; the
orchestrator escalates and never proceeds. Reading live state for drift is itself creds-gated and **not wired
here** — drift detection arrives only behind the creds wall.

### 9.3 The sibling artifact (`.kata/iac-apply.json`) — why sibling, not an extension of `.kata/iac.json`

Tier-2 writes a **sibling** runtime artifact `.kata/iac-apply.json` (`iac_apply.iac_apply_schema` is the single
source of truth; built by `iac_apply.build_iac_apply_artifact`, written by `iac_apply.emit_iac_apply`) plus the
committable approval input `kata.iac-apply-approval.json`. It is **NOT** an extension of Tier-1's `.kata/iac.json`:

- The D111 anti-fail-open guard makes `kata-evaluate` independently re-classify the footprint and treat an
  absent/malformed `.kata/iac.json` on IaC-classed changes as `NEEDS_WORK` (§7 field notes). Injecting
  apply-lifecycle state into that artifact risks perturbing the fail-closed Tier-1 re-classification — a
  regression on the most safety-critical surface. The sibling keeps Tier-1 byte-for-byte untouched.
- Separation of concerns / trust: `.kata/iac.json` = Tier-1 analysis FINDINGS (creds-free); `.kata/iac-apply.json`
  = Tier-2 approval/capture/audit LIFECYCLE (creds-gated). The human-authored grant lives at the committable
  repo-root path (tamper-resistance, mirroring kata-preflight's `kata.freeze-approval.json` H2), separate from
  the machine-written runtime state. An append-only audit row is built by `iac_apply.build_apply_audit_record`.

### 9.4 n=0-live / creds-wall honesty (the existential bound)

The whole Tier-2 apply path is **n=0-live, creds-gated**. Generating a plan live, reading live state for drift,
and executing an apply ALL require authenticated cloud access — **none is wired here**. The single cloud-mutating
function `iac_apply.run_apply` raises `NotImplementedError` (mirrors `drift_gate.structural_drift_verdict`); it
imports no subprocess on any path and **cannot mutate cloud infra by construction**. Live execution is a
separate, n=0-live, creds-gated build with its own grill/DESIGN.

### 9.5 Hard exclusions (do not weaken these)

- **`-target` / scoped apply is FORBIDDEN in v1** (bypasses the lifecycle guards). The TF builders expose no
  `-target` parameter and never emit the token.
- **Never `-auto-approve`** — `build_tf_apply_argv` applies the EXACT approved saved plan file (the artifact is
  the authorization) and never emits `-auto-approve`.
- **A parked apply stays parked — never auto-applies** (reuse `escalation.py` async park/drain).
- State surgery (import/mv/rm, backend migration), cost/blast-radius preview, multi-cloud, env-differentiated
  policy, and auto-rollback are OUT OF SCOPE / FORBIDDEN here.
- **(N1 — inherited caveat, not a Tier-2 regression)** The capability-gate's completeness is INHERITED from
  Tier-1's stateful sets (`iac_detect._TF_STATEFUL_*` / `_CFN_STATEFUL_*`): a data-bearing resource type MISSING
  from those families would class non-stateful and could clear via plan approval without the typed grant. This
  is the same property that gates Tier-1 escalation (§5b/§6) — a new gap is fixed in `iac_detect`, not here.

### 9.6 Tier-2 key citations (verify-before-reuse per `protocol/reuse-claims.md`)

| Claim | Verified surface (`tools/iac_apply.py`) |
|---|---|
| Structured-argv builders (`shell=False`, DATA identifiers, no `-target`/`-auto-approve`) | `iac_apply.build_tf_plan_argv` · `build_tf_apply_argv` · `build_cfn_create_changeset_argv` · `build_cfn_execute_changeset_argv` |
| Plan-hash binding input (TF binary bytes / CFN full-response bytes) | `iac_apply.plan_hash` · `iac_apply.canonical_cfn_plan_bytes` |
| Approval verdict (APPROVED iff hash matches; mismatch → invalidated, never pass) | `iac_apply.approval_verdict` (+ `load_approval`, `build_approval_artifact`) |
| Typed self-binding stateful-destroy capability-gate (distinct from approval) | `iac_apply.capability_gate_verdict` (+ `build_capability_grant`) |
| Apply state-machine resolver + terminal vocabulary | `iac_apply.apply_state` |
| Sibling runtime artifact schema / build / emit | `iac_apply.iac_apply_schema` · `build_iac_apply_artifact` · `emit_iac_apply` |
| Append-only apply-audit row | `iac_apply.build_apply_audit_record` |
| The DEFERRED cloud-execution seam (raises `NotImplementedError`; creds wall) | `iac_apply.run_apply` |
| Exec-safety sink registration (deferred, `shell=False`) | `protocol/exec-safety.md` sink registry (the four `iac_apply.run_apply` rows) |
