---
title: "IaC live-apply (Tier 2) — FUTURE BRIEF (assessment recorded, not scheduled)"
status: BRIEF (future — captured 2026-06-26; operator intrigued, deliberately deferred behind Tier-1 author/review/gate)
spec: iac-live-apply
depends-on: iac-safety-specialist (Tier 1 — the review/gate discipline is the prerequisite that makes live-apply safe)
gated-on: authenticated cloud access in the platform (CLI creds / SSO / authenticated cloud MCP) — adapter-bound, never a core assumption
---

# IaC live-apply (Tier 2) — future BRIEF

> The operator is intrigued by having the harness actually **log into the cloud and apply** (run `terraform apply` /
> `execute-change-set`), not just write template/plan files. This BRIEF records the **honest assessment** (2026-06-26)
> and the conditions under which it should be built. **Deliberately deferred behind Tier 1** (`iac-safety-specialist`).

## The assessment (why it's a different beast, not just "more code")
The **mechanical** part is medium (~kata-preflight-sized): a guarded subprocess runner — `plan -out` → parse → gate →
`apply` the stored plan (TF), or `create-change-set` → `describe` → gate → `execute-change-set` (CFN). But the
**responsible** lift is large because of four surrounding concerns, one of them structural:

1. **Credentials/auth (operator's security domain).** The harness has zero cloud creds today and never touches them.
   Live-apply binds authenticated cloud access — framed as an **adapter/binding** (only available where the platform
   already provides it, never a core assumption), like the dispatch adapters.
2. **State + failure handling.** TF state backends (S3+lock, drift, concurrent-run corruption) + apply-failure recovery
   (tainted state, `UPDATE_ROLLBACK_FAILED`). A half-applied change is a real operational mess.
3. **Elevated gate stakes.** A wrong approval no longer ships a bad line of code — it **destroys a production database or
   opens a security group to the internet.** "Destroy needs separate pre-authorization", "approval invalidates on plan
   change", and cost-estimation gating become safety-critical, not nice-to-have.
4. **★ Structural — it breaks the harness's git-reversibility safety model.** Everything KataHarness does today is
   git-reversible (worktrees, octopus merge, backout tags, `git reset --hard <baselineSha>`; the offered-backout and
   never-auto-mutate posture all rest on "changes are tracked and undoable"). **A live cloud `apply` is the first action
   the harness could take that you cannot `git reset`** — a destroyed RDS instance isn't in a worktree. Live-apply needs
   its **own safety contract**, separate from the git-based one the whole loop assumes.

## When/how to build it (if ever)
- **Prerequisite:** Tier-1 `iac-safety-specialist` shipped + proven — the review/gate discipline is what makes live-apply
  safe (don't apply live until the gate is trusted on the analyze-only path).
- **Gated on** authenticated cloud access existing in the platform (adapter-bound).
- **Its own grill → DESIGN → build**, carrying: the non-git safety contract; plan→human-approve→apply with
  approval-invalidation (Atlantis `--discard-approval-on-plan`); **destroy as an operator *capability* gate** (HCP
  "Allow destroy plans" pattern), not just task-level approval; apply-failure recovery; cost gating (env0 pattern);
  a first-class infra audit trail (actor/time/rationale — SOC2/ISO/HIPAA). Research substrate already in
  `specs/iac-safety-specialist/RESEARCH.md` §1/§2/§5 (the plan→approve→apply platform patterns).

## Out of scope until then
Everything live: real plan generation, real apply, cloud creds, state mutation. Tier 1 stays **author/review/gate**.
