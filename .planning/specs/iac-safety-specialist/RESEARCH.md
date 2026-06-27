---
title: "IaC-safety specialist — RESEARCH (AWS-first, grounding-gated)"
status: RESEARCH complete (2026-06-26) — 4 cited research agents (Terraform · CloudFormation · AWS misconfig taxonomy+Snyk IaC · IaC change-gating platforms). Feeds the grill → DESIGN.
spec: iac-safety-specialist
relates-to: capability-aware-assignment (this is its v1 realization, narrowed to IaC per operator 2026-06-26) · kata-preflight (target-env + the never-auto-mutate posture) · kata-orchestrate (escalation/human-gate) · kata-evaluate/kata-review (the gate)
verdict: BUILDABLE NOW, AWS-first, scanner-delegated. Extends to Azure/GCP in v2 with zero prompt-lens rewrite.
---

# IaC-safety specialist — RESEARCH

> **Why this exists:** the operator scoped capability-aware-assignment down to **"just an IaC specialist or specialists"**
> for v1 (2026-06-26), because — for frontier models — the specialist value is **not language expertise** but the
> **safety / security / gate discipline** that IaC needs and generic coding does not (a bad `apply` destroys a DB or
> opens a security group, not just fails a test). This research confirms the build is **bounded** because the mature
> scanners carry the exhaustive rules; the harness carries the *discipline*.

## 0. Headline verdict (grounded)
- **Bakeable in a normal timeframe, AWS-first** (Terraform + CloudFormation/CDK). The mechanism is well-defined and
  the rules are delegated to scanners the harness already has (`mcp__Snyk__snyk_iac_scan`).
- **The "deep research" is bounded:** it's synthesis of mature public best practice (AWS Well-Architected Security
  Pillar, CIS AWS v3.0, FSBP 200+ controls) — the *scanners* maintain the thousands of rules; the specialist carries
  a small durable discipline + an 8-smell lens. **Don't bake the encyclopedia** (anti-cathedral).
- **Multi-cloud extends cleanly (v2):** the same 8 smells transfer verbatim to Azure/GCP; Snyk IaC already covers all
  three. AWS-first is not a dead-end — it's the first increment.

## 1. The cardinal rule — plan/preview before mutate, never auto-apply destructive change
Universal across HashiCorp, Atlantis, HCP Terraform, Spacelift, env0 (all cited): **generate a plan/preview → surface
it → human approves → apply the *exact stored plan* (no re-plan at apply).** Real incident: an RDS module refactor +
`--auto-approve` → destroy/recreate → 3h13m downtime, data loss (Medium/Adedoyin). **Default-to-pending** (env0): when
impact is ambiguous or no rule clears it, **escalate, don't proceed.** This maps 1:1 onto KataHarness's existing
`human-required` escalation + the D29/kata-preflight **never-auto-mutate** posture.

## 2. Machine-readable destructive-operation detection (LOAD-BEARING for the build)
**Terraform** — `terraform plan -out=tfplan` → `terraform show -json tfplan > plan.json`; filter
`resource_changes[].change.actions`:
- `["delete"]` = destroy · `["delete","create"]` / `["create","delete"]` = **replace** (still destroys the old object) → **flag/escalate.**
- `change.action_reason` explains *why* — `delete_because_each_key` / `delete_because_count_index` = a `for_each`/`count`
  rename silently destroying resources (the #1 accidental-deletion cause — annotate it explicitly).
- `terraform plan -detailed-exitcode`: 0=no-op, 2=changes, 1=error (machine-readable change presence).
**CloudFormation** — `create-change-set` → `describe-change-set` → parse `Changes[].ResourceChange`:
- `.Action == "Remove"` (delete) · `.Replacement in {"True","Conditional"}` (replace) · `.PolicyAction in
  {"Delete","ReplaceAndDelete"}` (old not retained) · `.Details[].Target.RequiresRecreation == "Always"` → **flag/escalate**, especially on stateful types (RDS/DynamoDB/S3/EBS/ElastiCache/Redshift).
- **Never** direct `update-stack` in automation — change sets are the preview gate. CDK → `cdk synth` → treat as CFN.

## 3. Tooling — what to call (and what to avoid)
- **Primary scanner = Snyk IaC (`mcp__Snyk__snyk_iac_scan`) — already wired.** 400+ rules from CIS/NIST/HIPAA/PCI/ISO;
  covers Terraform (+ plan JSON via `--scan=resource-changes`), CloudFormation, ARM, GCP, K8s; JSON/SARIF output with
  severity + rule ID + file:line + remediation. Block on high/critical (configurable threshold).
- **CFN syntax:** `cfn-lint` (AWS-official, required first pass — not a security tool). **Org policy-as-code:**
  `cfn-guard` (AWS) can validate change sets to block replacement; Sentinel/OPA-Conftest for Terraform.
- **AVOID / dead:** **Terrascan** (archived Nov 2025), **cfn_nag** (unmaintained), **standalone tfsec** (merged into
  Trivy — use Trivy if you want that rule set). Checkov/KICS = solid OSS alternatives if a non-Snyk scanner is wanted.

## 4. The lean prompt-lens — the 8 durable smells to BAKE (provider-agnostic)
Self-check these *before* the scanner runs (they're the highest-impact breach classes; the scanner is authoritative,
the lens raises the floor + catches what needs judgment):
1. **S1 IAM wildcards** — `"*"` action/resource, AdministratorAccess on non-human principals (the #1 breach origin — Capital One; 99% over-permissive). *Judgment-needed; scanner partial.*
2. **S2 Open network ingress** — `0.0.0.0/0`/`::/0` on 22/3389/5432/3306/etc.
3. **S3 Public storage** — S3/Blob/GCS block-public-access off / public ACL.
4. **S4 Encryption at rest** — data stores without `encrypted=true`/KMS.
5. **S5 Encryption in transit** — endpoints without TLS / HTTP-redirect off.
6. **S6 Logging/audit disabled** — CloudTrail multi-region, VPC flow logs, DB audit logs.
7. **S7 Plaintext secrets** — `AKIA*`/password/token strings in params/env/tags; CFN params missing `NoEcho`.
8. **S8 Public datastores** — RDS/Redshift `publicly_accessible`, public snapshots, IMDSv2 not enforced (`http_tokens=required`).
**Plus the judgment-only checks scanners are blind to:** stateful-resource `DeletionPolicy`/`UpdateReplacePolicy` (CFN)
& `lifecycle.prevent_destroy` (TF) completeness; **the plan-level destroy/replace analysis (§2)**; module/source
provenance (untrusted registries / `git::` refs); termination protection + stack policy (CFN — runtime stack attrs,
not in the template); long-lived static IAM keys (`aws_iam_access_key`).

## 5. Bake-vs-delegate (the anti-cathedral line)
- **Delegate to the scanner (exhaustive, maintained, machine-authoritative):** all provider-service control IDs
  (EC2.x/RDS.x/S3.x/CloudTrail.x…), version/age rules, cross-resource relationships, compliance mapping, K8s/container
  hardening, OPA/Rego org policy. **Never re-implement scanner logic in prose.**
- **Bake into the specialist (small, durable, judgment/state-dependent):** the 8 smells (floor-raisers), the plan-level
  destroy/replace detection (§2 — no scanner detects this), safe-authoring discipline (DeletionPolicy/prevent_destroy on
  stateful, never emit `--auto-approve`), runtime-state checks (termination protection, stack policy), module provenance,
  and the **plan→approve→apply gating discipline**.

## 6. Escalation decision table → maps to the harness's `human-required` escalation
| Signal | Action in the harness |
|---|---|
| Read-only / no-op / additive-in-dev, scanner clean | auto-proceed |
| Scanner *warn* / medium risk | escalate (human reviews) |
| ANY delete/destroy, or replace on a stateful resource | **escalate** (human-required) |
| IAM / secrets / network-topology change | **escalate** |
| Scanner hard finding (high/critical) / org-policy hard-block | **default-FAIL** (reject → revise; not merely escalate) |
| Destroy-class when destroy not pre-authorized | reject → escalate to operator (a *capability* gate, not just approval) |
Mirrors Sentinel's advisory/soft/hard tiers + env0 default-to-pending. **Approval invalidates if the plan changes**
(Atlantis `--discard-approval-on-plan`) — the harness's freeze/re-gate already embodies this.

## 7. How it maps onto KataHarness (reuse, verify-before-reuse at design time)
- The **specialist = a prompt/gate profile** for the IaC file-class, layered on the existing worker + `kata-tdd` — NOT a
  new code stack (`prefer-in-context-over-new-python`).
- Its **gate** = `snyk_iac_scan` + cfn-lint/`validate` + the §2 plan/change-set destroy-detection + the 8-smell lens,
  run as the IaC task's verify, default-FAIL on high/critical + on un-approved destroy/replace.
- Its **escalations** = the existing `human-required` path (`protocol/escalation.md`); destroy/replace/IAM → human.
- Its **safety posture** = the same never-auto-mutate stance kata-preflight just shipped (D29/D109).
- **kata-orient** injects the IaC safety callouts for IaC-classed tasks (it's already task-type-aware).

## 8. The key scoping fork for the grill (the one real decision)
KataHarness writes code in worktrees and has **no cloud credentials / does not run live infra.** So v1 is almost
certainly an **author + review + gate** specialist (write safe IaC; run scanners + plan/change-set *analysis*; flag
destroy/replace/IAM; enforce safe-authoring) — it does **not** run live `terraform apply`/`execute-change-set` (that
stays with CI/human). The plan→approve→apply *discipline* governs what the specialist WRITES and FLAGS, not a live
deploy. **Confirm this boundary at the grill** (recommended: author/review/gate, no live apply in v1). Live-apply
orchestration (creds, state backends, real plan execution) is a much bigger, separate future item if ever wanted.

## 9. Sources (representative — full citations in the agent findings)
AWS Well-Architected Security Pillar · CIS AWS Foundations v3.0 · AWS FSBP · HashiCorp core-workflow + JSON plan format
+ lifecycle + state/backend prescriptive guidance · AWS CFN change-sets/stack-policies/DeletionPolicy/drift + cfn-lint
+ cfn-guard docs · Snyk IaC docs + MCP cheat sheet · Atlantis / HCP Terraform / Spacelift / env0 approval-policy docs ·
OPA Terraform · Datadog State of Cloud Security 2024/25 · Verizon DBIR 2025 · Unit 42 / IBM X-Force.
