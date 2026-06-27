# kata-preflight — GRILL LEDGER

> Grill in plain terms ([[grill-in-plain-terms]]). The spine PRE-FLIGHT phase (D29) + the installed-library
> registry (D-registry) + the manifest schema (`protocol/dependencies.md`) were already locked, so this grill
> resolved only the genuinely-open forks. CONVERGED 2026-06-26 (operator answers Q1–Q4).

## Already LOCKED before this grill (carried in, not re-litigated)
- **PRE-FLIGHT is a mandatory spine phase between FREEZE and EXECUTE; never tiered** (D29/D33 — like kata-evaluate).
- **Approve-at-freeze:** the human approves the dependency *set + sources* when approving the DESIGN; PRE-FLIGHT
  **provisions** the approved set, makes **no new decisions**. A dep discovered later that is NOT in the approved
  manifest is **drift ⇒ escalate ⇒ deliberate re-freeze** (never a silent install). **Workers cannot install**
  (least-privilege). (D29, `dependencies.md`.)
- **Manifest schema** = `protocol/dependencies.md` (`kata.dependencies.json`); per-entry
  name/type/version/purpose/install/verify/source/hash/scope/classification.
- **Default-FAIL on `verify`** — a dep that won't verify ⇒ BLOCK the loop. (D29.)
- **Installed-library registry** = machine-global `~/.kata/installed-registry.json`, record-and-recommend,
  **never auto-uninstall** (D-registry).
- **Responsibilities:** `kata-grill` enumerates → `kata-design-doc`/`kata-plan` write the manifest →
  **NEW `kata-preflight`** approve/install/verify gate → `kata-orchestrate` precondition refuses dispatch until
  PRE-FLIGHT is cleared. (D29.)

## Resolved forks (this grill)
- **PF-1 — Install execution = AUTO-RUN the pre-approved installs (unattended).** After approve-at-freeze,
  `kata-preflight` shells out and runs the pinned/hash-verified installs from recognized registries itself, then
  re-verifies. *Operator chose autonomy over check-and-hand-to-human.* **Hard guards (because it now mutates the
  machine):** install only from `preflight.allowed_registries` (default-deny; reject `curl|bash`/arbitrary-domain
  strings); pin per `preflight.pin_policy`; verify `hash` when present; **Snyk SCA scan BEFORE install** when
  `scan_required` (block on findings over threshold); never auto-uninstall. *Provenance: Q1.*
- **PF-2 — v1 scope = FULL: the gate + the machine-global registry + the reference-counted cleanup report.**
  v1 includes the cross-project reference-counted "what is safe to uninstall" **recommendation** report
  (recommend only; the human executes). *Operator chose include-now over defer.* *Provenance: Q2 (supersedes
  D-registry's "cleanup report is a fast-follow" staging — promoted into v1).*
- **PF-3 — ONE mechanism for both a build's deps AND an existing target's runnable env.** `kata-preflight`
  provisions (a) the build's declared manifest deps AND (b) an existing target's **runnable environment**:
  provision the target's deps, then verify its gate/test command runs; if it cannot run after best-effort
  provisioning, return a **`non-runnable → degrade to report-only/snapshot`** verdict that Debug Mode consumes
  (DG-1b-edge). *Operator chose now / one-mechanism. Unblocks Debug Mode's build.* *Provenance: Q3 + debug-mode
  DESIGN:103.*
- **PF-4 — Sandbox = isolated env when available, else machine + warn (honest degrade).** Auto-install prefers
  an isolated/disposable env (`preflight.sandbox_required`); when none is available it falls back to installing on
  the host and **surfaces a clear warning**. *Operator chose degrade-with-warning over hard-block / direct.*
  *Provenance: Q4.*
