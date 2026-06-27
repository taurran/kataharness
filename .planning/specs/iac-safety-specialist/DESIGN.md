---
title: "IaC-safety specialists (Tier 1: author/review/gate) — FROZEN DESIGN"
status: FROZEN (2026-06-26) — grill converged (IAC-1..IAC-4); research-grounded (RESEARCH.md). Pending freeze-gate kata-review, then build.
spec: iac-safety-specialist
tier: 1 (author/review/gate — NO live cloud apply; Tier 2 live-apply = specs/iac-live-apply/BRIEF.md)
relates-to: capability-aware-assignment (this is its v1 realization, IaC-scoped) · kata-orchestrate (dispatch + gate + escalation) · kata-orient (profile injection) · kata-preflight (never-auto-mutate posture, D109) · kata-evaluate (integration gate reads the IaC findings)
---

# IaC-safety specialists (Tier 1) — FROZEN DESIGN

> Two detection-activated specialists that make the loop **safe with infrastructure-as-code**: when a task owns IaC
> files, the worker gets an IaC-safety profile and the task's gate runs an IaC safety check — **scanner + safe-authoring
> lens + destructive-change analysis** — default-FAIL on high/critical findings or an un-approved destroy/replace, which
> escalates to the human. **Tier 1 is author/review/gate only: the harness WRITES and ANALYZES IaC; it never runs a live
> `terraform apply` / `execute-change-set`** (no cloud creds; a live apply is not git-reversible — Tier 2's own contract).

## 1. Locked decisions (grill IAC-1..IAC-4 + research)
- **IAC-1 — Two specialists:** `kata-iac-terraform` + `kata-iac-cloudformation` (CDK → `cdk synth` → treated as CFN).
  They share one safety contract (`protocol/iac-safety.md`, DRY-by-pointer) and differ only in tool-specific mechanics.
- **IAC-2 — Tier 1 = author/review/gate, NO live apply.** The plan/change-set is **analyzed**, not executed. Live
  generation (`terraform plan` needs creds+state; CFN change sets need a live stack) is **Tier 2** (`specs/iac-live-apply/`).
- **IAC-3 — Auto-activated by detected file-class.** A task owning IaC files → orchestrator injects the matching
  specialist profile + runs the IaC gate as that task's verify. No IaC files ⇒ no-op (BC — today's loop unchanged).
- **IAC-4 — Snyk IaC primary.** `mcp__Snyk__snyk_iac_scan` is **available in the Snyk MCP toolset** (the SCA sibling is
  wired in kata-preflight via an injected, fail-closed seam, `tools/kata_preflight.py:808-826`); the **IaC scan is NEW
  wiring** added by slice D (NOT pre-existing reuse), following that same injectable + **fail-closed** pattern. Plus
  `cfn-lint` for CFN syntax; Checkov / cfn-guard / Trivy are optional add-ons (config). Avoid the dead tools
  (Terrascan/cfn_nag/standalone-tfsec).

## 2. Components — REUSE vs NEW (verify-before-reuse at build, `protocol/reuse-claims.md`)
**Reused (verified):** `kata-orchestrate` per-task dispatch + AO hook ([[kata-orient]]) + per-task verify +
`human-required` escalation (`protocol/escalation.md`) · the integration-gate evidence pattern (`kata-evaluate` reads
`.kata/*.json`, e.g. mutation/concurrency) · the never-auto-mutate posture (D29/D109) · the injectable + **fail-closed**
scanner seam pattern from kata-preflight (`tools/kata_preflight.py:808-826`) · the optional-config + DRY-by-pointer
patterns. (The Snyk **SCA** tool is wired in kata-preflight; the Snyk **IaC** tool is NOT — see N4-scanner below.)

**NEW:**
- **N4-scanner — wire `mcp__Snyk__snyk_iac_scan`** (available in the MCP toolset, but called nowhere today) as the IaC
  gate's scanner via an injectable seam with the **fail-closed** guard (scanner unwired/unavailable/errored ⇒ gate FAIL,
  never pass — the exact kata-preflight MINOR-3 fix, `tools/kata_preflight.py:808-826`).
- **N1 — `tools/iac_detect.py`** — deterministic (a) **file-class classifier** (`.tf`/`.tf.json`/`.hcl` → terraform;
  CFN templates by signature `AWSTemplateFormatVersion`/top-level `Resources` with `Type: AWS::*` → cloudformation;
  `cdk.json`/`cdk.out/` → cdk) and (b) **plan/change-set JSON destructive-parsers** used **when such an artifact is
  provided** (TF `resource_changes[].change.actions`; CFN `Changes[].ResourceChange.{Action,Replacement,PolicyAction}`).
  It does NOT generate plans (Tier 2). Injectable/pure; tested on fixtures.
  **Detection limits (MAJOR-5 — a miss is a silent safety bypass):** CFN has no unique extension and
  `AWSTemplateFormatVersion` is optional, so a fragment / nested-stack child / unusual template can **false-negative** →
  the IaC gate silently does not fire (the file ships through normal verify). To shrink that gap, the classifier ALSO
  flags any `.yaml/.yml/.json` whose content contains a `Type:\s*AWS::` resource declaration (belt-and-suspenders), and
  the `iac` config block supports an operator **force-classify** list (paths/globs). The `Type: AWS::*` requirement is
  kept to avoid false-positives. This risk is acknowledged, not eliminated — detection is best-effort.
- **N2 — `protocol/iac-safety.md`** — the shared safety contract: the 8-smell lens, the bake-vs-delegate line, the
  safe-authoring discipline, the destructive-change rules, and the escalation mapping (below). Both specialists cite it.
  **(MINOR-6)** The lens `smells` are the **authoring worker's self-check** — a floor-raiser, review-gated, NOT
  independently verified; the **scanner is the authoritative, objective, fail-closed gate**. `kata-evaluate` reads the
  artifact but does not re-derive smells; a clean self-reported `smells` is not independent assurance.
- **N3 — two skills `kata-iac-terraform` + `kata-iac-cloudformation`** (`category: execute`, `kata/spine` NOT set —
  they're optional specialists, not spine; never-tiered though — safety is not depth-relaxable). Each = the worker
  authoring profile + the tool-specific gate, pointing at N2.
- **N4 — `kata-orchestrate` activation + gate wiring** — detect (N1) → inject profile (AO hook) → run the IaC gate as
  the task verify → emit `.kata/iac.json` → default-FAIL/escalate per the table. + an optional `iac` config block.
- **N5 — `.kata/iac.json`** — the IaC findings artifact `kata-evaluate` reads at the integration gate (evidence).

## 3. The IaC gate (runs as an IaC-classed task's verify; default-FAIL)
Ordered, creds-free (Tier 1):
1. **Syntax/validate** — TF: `terraform fmt -check` + `terraform validate` (offline). CFN: `cfn-lint` (CDK: `cdk synth` first). Hard-fail on error.
2. **Security scan** — `mcp__Snyk__snyk_iac_scan` on the IaC source. **Default-FAIL on high/critical** (threshold configurable). Parse severity + rule-id + file:line. **FAIL-CLOSED (BLOCKER fix, mirrors kata-preflight MINOR-3):** if the scanner is **unwired, unavailable, or errors**, the gate **FAILS** with a "scanner not wired/unavailable" blocker — it never passes with zero coverage. "Default-FAIL on high/critical" governs *findings*; *scanner-absent* is also a FAIL.
3. **8-smell safe-authoring lens** (`protocol/iac-safety.md`) — the specialist self-checks the IaC it wrote/changed: IAM wildcards · open ingress · public storage · encryption at-rest/in-transit · logging · plaintext secrets · public datastores — **plus** the judgment checks scanners are blind to (stateful `DeletionPolicy`/`UpdateReplacePolicy`/`prevent_destroy` completeness; module/source provenance; CFN termination-protection/stack-policy *recommendations*).
4. **Destructive-change analysis** — (a) **static source-diff reasoning**: did the change remove a resource block, rename a `for_each`/`count` key, change an immutable attribute on a stateful resource, or drop a `DeletionPolicy`? (b) **if a plan/change-set JSON artifact is present**, parse it (N1) for `delete`/`replace` on stateful resources. Any detected destroy/replace ⇒ **escalate (human-required), never silent**.
   **Honesty (MAJOR-3):** static source-diff reasoning is **best-effort and provider-schema-blind** — without a plan it cannot know which attribute changes force replacement, so it both **misses** provider-forced replacements (false-negative) and may **over-flag** harmless changes. **A clean static result is NOT a verified no-destroy** — only a provided plan/change-set JSON is authoritative (RESEARCH §2/§5). The `.kata/iac.json` `source:"static"|"plan"` field records which fired; a static-only clean result is reported as *"no destroy detected (static, unverified)"*, never as a guarantee.
5. **Emit `.kata/iac.json`** — `{ tasks:[{taskId, kind:"terraform"|"cloudformation", scanner:{critical,high,med,low}, smells:[...], destructive:[{address,action,stateful,source:"static"|"plan"}], verdict:"pass"|"fail"|"escalate"}] }`.

## 4. Escalation mapping → the existing `human-required` path
| Signal | Action |
|---|---|
| Scanner clean + no smells + no destructive change | gate **pass** |
| **Scanner unwired / unavailable / errored** | **FAIL (fail-closed)** — never pass (BLOCKER fix) |
| Scanner **high/critical**, or a hard org-policy violation | **default-FAIL** (revise; not merely escalate) |
| Any destroy, or replace on a **stateful** resource (static OR plan-detected) | **escalate (human-required)** |
| IAM / secrets / network-topology change | **escalate** |
| Scanner medium / lens warn | surface; escalate if it touches a stateful/security-sensitive resource |
Mirrors the research's Sentinel advisory/soft/hard tiers + env0 default-to-pending. Never auto-resolve a destroy.

**Verdict → producer mapping (MAJOR-4 — the gate runs orchestrator-side, but escalations are worker-written):** the
IaC gate is run by the **orchestrator** as the task's verify, so on `verdict:"escalate"` the **orchestrator** writes the
`human-required` payload (`tools/escalation.py` `build_escalation` → `write_escalation`) and parks the task per the
existing async escalation path — NOT the worker. `verdict:"fail"` routes into the orchestrator's normal default-FAIL fix
loop (revise → re-gate). `verdict:"pass"` proceeds. The three-valued verdict is collapsed at the orchestrator: `fail` →
fix loop, `escalate` → human-required park, `pass` → integrate.

## 5. Activation + BC
- **Detection (N1)** runs over each task's **owned files** at dispatch. IaC kind found ⇒ inject the matching specialist
  profile (via the [[kata-orient]] hook) + mark the task's verify = the IaC gate (§3). A mixed task (IaC + code) runs
  **both** its normal verify and the IaC gate.
- **BC (MINOR-7):** no IaC observed ⇒ no IaC gate, no `.kata/iac.json`, **no change in artifacts or verdicts** (the
  detector runs at dispatch and returns empty — a no-op-output added code path, not a literal byte-for-byte identity).
  The `iac` config block is optional (thresholds/extra scanners/force-classify); absent ⇒ defaults (Snyk primary,
  high/critical fail, fail-closed if unwired).

## 6. Acceptance (default-FAIL, runnable)
- `iac_detect.classify_file` correctly classifies `.tf`, a CFN YAML/JSON template (by signature, not extension alone),
  a CDK project, and a non-IaC file (→ None). `classify_task(owned_files)` returns the set of kinds.
- The plan/change-set parsers flag `delete`/`delete+create` (TF) and `Action:Remove`/`Replacement:True|Conditional` (CFN)
  on fixtures; clean plans → no destructive flags.
- A task owning a `.tf` with a high-severity Snyk finding (stubbed) ⇒ gate **fail**; clean ⇒ **pass**.
- **Fail-closed:** an IaC task with the Snyk callable **absent / erroring** ⇒ gate **FAIL** with a "scanner not
  wired/unavailable" blocker (NOT pass) — the BLOCKER acceptance.
- A change that removes a stateful resource / renames a `for_each` key ⇒ **escalate** in `.kata/iac.json`.
- BC: a run with no IaC files ⇒ no IaC gate, no `.kata/iac.json`, no change in artifacts or verdicts (detector runs, returns empty).
- `kata-evaluate` reads `.kata/iac.json` and treats unresolved high/critical or un-approved destroy as NEEDS_WORK.

## 7. Test seams
N1 pure on fixtures (classify + parse; no live tools). The scanner is the injectable seam (stub a Snyk verdict). The
lens + static destructive reasoning are specialist prose (review-gated, not unit-tested). `.kata/iac.json` is a JSON
round-trip. Orchestrate wiring = fixture configs (IaC task present/absent → gate runs/no-op).

## 8. Build sequencing (PARKED until freeze-gate SHIP + operator go)
- **Wave 1 (parallel):** **A** `tools/iac_detect.py` + tests (detector + plan/change-set parsers). · **B**
  `protocol/iac-safety.md` (shared contract: 8-smell lens + bake-vs-delegate + safe-authoring + destructive rules +
  escalation mapping).
- **Wave 2:** **C** `kata-iac-terraform` + `kata-iac-cloudformation` skills (cite N1 + N2) + README (37→**39**).
- **Wave 3:** **D** `kata-orchestrate` activation+gate wiring (detect → profile → IaC verify → emit `.kata/iac.json` →
  escalation) + the optional `iac` config block in `protocol/config.md` + `kata-evaluate` reads `.kata/iac.json`.
Build through the recipe (contract+code-bearing): freeze-gate → orchestrated build → kata-evaluate → D98 → merge.

## 9. Explicitly deferred (Tier 2 / future)
- **Live apply** (`terraform apply` / `execute-change-set` against real cloud) — `specs/iac-live-apply/BRIEF.md`; needs
  authenticated cloud access (adapter-bound), a non-git safety contract (cloud changes aren't `git reset`-able),
  destroy-as-operator-capability-gate, apply-failure handling, cost gating, infra audit trail.
- Multi-cloud (Azure ARM/Bicep, GCP) — same 8 smells + Snyk already covers them; an increment after AWS v1.
- A pluggable multi-scanner layer (Checkov/Trivy/cfn-guard as first-class) — Snyk-primary suffices for v1.
