---
title: "kata-preflight — FROZEN DESIGN (the PRE-FLIGHT spine phase)"
status: FROZEN (2026-06-26) — grill converged (PF-1..PF-4). Pending freeze-gate kata-review, then build.
spec: kata-preflight
compiled-from: GRILL-LEDGER.md (PF-1..PF-4) + D29 + D-registry + protocol/dependencies.md + protocol/config.md (preflight block)
unblocks: Debug Mode (the second of its two build blockers; install-portability cleared the first — D103)
---

# kata-preflight — FROZEN DESIGN

> The mandatory **PRE-FLIGHT** spine phase (D29) between FREEZE and EXECUTE: provision the frozen, human-approved
> dependency set so a long-running loop never stalls mid-flight on a missing tool. One mechanism serves both a
> **build's declared deps** and an **existing target's runnable environment** (PF-3). Auto-runs the pre-approved
> installs under hard supply-chain guards (PF-1), prefers a sandbox (PF-4), records every install to a
> machine-global registry, and emits a reference-counted cleanup recommendation (PF-2). Default-FAIL; never tiered.

## 1. Requirements
- **R1** Read the frozen manifest (`kata.dependencies.json`, `protocol/dependencies.md`) and, for each entry,
  check presence via its `verify` command. Default-FAIL: a dep that won't verify after provisioning ⇒ BLOCK.
- **R2** Auto-run installs for missing deps (PF-1) under hard guards (recognized registries, pinned, hash-verified,
  Snyk SCA before install, no `curl|bash`).
- **R3** Prefer an isolated/disposable env; else install on host + warn (PF-4).
- **R4** Record every install to the machine-global registry (`~/.kata/installed-registry.json`, D-registry) and
  produce a cross-project reference-counted **cleanup recommendation** (recommend only; never auto-uninstall) (PF-2).
- **R5** Provision + verify an **existing target's runnable env**; if non-runnable after best-effort, return a
  `degrade` verdict (report-only/snapshot) Debug Mode consumes (PF-3, DG-1b-edge).
- **R6** `kata-orchestrate` refuses to dispatch until PRE-FLIGHT is cleared (D29).
- **R7** Approve-at-freeze: provision the approved set only; a dep not in the approved manifest ⇒ drift ⇒ escalate
  ⇒ re-freeze (never silent install). Workers cannot install (least-privilege).

## 2. Components — REUSE vs NEW (verify-before-reuse, `protocol/reuse-claims.md`)
**Reused (verified surfaces):** the `preflight` config block (`protocol/config.md:29-36` — `allowed_registries`,
`pin_policy`, `scan_required`, `approval_mode`, `sandbox_required`) · `target.baselineGate` as the target's
runnable-env gate command (`protocol/config.md:22`) · the gate-artifact emit pattern (`tools/gate_emit.py`) · the
**argv-builder + no-`shell=True` exec pattern** (`tools/kata_dispatch.py:150` `_COMMAND_BUILDERS`, `:168`
`_subprocess_runner`) and the **injectable-runner test seam** (`tools/kata_dispatch.py`, `tools/kata_install.py`) ·
`kata-orchestrate` Preconditions §0 (the fail-closed precondition site, `SKILL.md:33-51`).

**NEW capabilities (scoped + schema'd below):**
- **N0 — EXTEND `protocol/dependencies.md` with STRUCTURED install fields** (resolves the freeze-gate BLOCKER):
  `manager` (∈ a fixed allowlist mapped to `preflight.allowed_registries`), `package`, `version`, optional
  `index`/`registry-url`. The existing freeform `install` string is **demoted to human-readable documentation —
  NEVER executed.** The engine BUILDS argv from the structured fields; a freeform shell string is never run.
- **N1 — `tools/kata_preflight.py`** — the deterministic PRE-FLIGHT engine (read manifest → verify → **build argv
  → guarded install** → re-verify → record → target-env probe → cleanup report → emit), behind an **injectable
  runner** whose `cmd` is an **argv list** (never a shell string).
- **N2 — the NEW skill `kata-preflight`** — the spine gate that drives N1, handles approve-at-freeze provisioning,
  escalates drift/blocks, and emits `.kata/preflight.json`.
- **N3 — `.kata/preflight.json`** — the PRE-FLIGHT result artifact (the gate output `kata-orchestrate` reads).
- **N4 — `~/.kata/installed-registry.json`** — the machine-global installed-library registry (D-registry).
- **N5 — `kata-orchestrate` precondition** — **conditional + fail-closed (BC-preserving):** *if a manifest
  (`kata.dependencies.json`) is present* (deps were declared), refuse dispatch unless `.kata/preflight.json`
  exists, parses, and is `ready` (or a `degraded` the operator explicitly accepted). *If no manifest is present*
  (a run that declared no deps), **PRE-FLIGHT is not required and dispatch proceeds** — today's loop unchanged
  (BC). The fail-closed bite applies only once deps exist: a declared manifest with a missing/blocked/unaccepted
  preflight.json ⇒ refuse.

## 3. LOCKED decisions (from D29 + the ledger)
- **LD1 — PRE-FLIGHT is a spine phase, never tiered** (D29/D33). Like `kata-evaluate`, it is a consistency floor.
- **LD2 — Auto-run installs (PF-1)** after approve-at-freeze; the engine **builds argv from the structured
  manifest fields (N0)** and runs it via the injectable runner with `subprocess.run(argv)` — **never
  `shell=True`, never a freeform string** (mirrors `tools/kata_dispatch.py:150,168`).
- **LD3 — Hard supply-chain guards (PF-1), enforced structurally not by string-matching:**
  - **No freeform execution.** The engine maps `manager` → an argv builder (a fixed `_COMMAND_BUILDERS`-style
    table); only allowlisted managers (`pip`, `uv`, `npm`, `cargo`, … ⊆ `preflight.allowed_registries`) have a
    builder. A `manager` ∉ the allowlist, or a missing/garbled structured field ⇒ `blocked`, nothing executed.
    The freeform `install` string is documentation-only and is **never** parsed-and-run (this is what kills the
    `curl|bash` / `npm … --registry http://evil` class — there is no string to smuggle through).
  - The builder **forces the registry/index** from `preflight.allowed_registries` (the manifest cannot override
    it to an untrusted index).
  - Pin per `preflight.pin_policy`; verify `hash` when present.
  - **Snyk SCA scan BEFORE install** when `scan_required` (the `mcp__Snyk__snyk_sca_scan` tool; scan input =
    the resolved `package@version` / a synthesized minimal manifest) — block over threshold.
  - Never auto-uninstall.
- **LD4 — Sandbox (PF-4), branches on the field's value:** prefer an isolated/disposable env. **If
  `sandbox_required: true` and none is available ⇒ `blocked` (hard-stop)** — an explicit policy is not silently
  downgraded. **If `sandbox_required: false` and none is available ⇒ host install, status `degraded`** (operator
  must accept, LD8) + a warning the orchestrator surfaces in-conversation (not merely logged).
- **LD5 — One mechanism, two inputs (PF-3):** the same provision+verify path serves (a) a build manifest and
  (b) a target's runnable env (verify `target.baselineGate`; non-runnable ⇒ `degrade`).
- **LD6 — Full v1 (PF-2):** the gate + the machine-global registry + the reference-counted cleanup report.
- **LD7 — Default-FAIL + least-privilege (R1/R7).** A dep that won't verify ⇒ `blocked`. Workers never install.
- **LD8 — D29 reconciliation + manifest-integrity (resolves the never-auto-install tension explicitly):** D29's
  *"never auto-install"* is reinterpreted as **"never install a dep that is not in the freeze-approved set"** —
  approve-at-freeze moves the human approval *earlier*, it does not remove it. To make that trustworthy, FREEZE
  records a **manifest approval hash**; PRE-FLIGHT recomputes the manifest hash and, on mismatch (the manifest
  changed after approval), **refuses to auto-install ⇒ `blocked` + escalate (`human-required`) ⇒ re-freeze.**
  A dep present at preflight but absent from the approved manifest is the same drift ⇒ `blocked`.

## 4. NEW schemas

### N3 — `.kata/preflight.json` (engine writes; `kata-orchestrate` reads)
```jsonc
{ "status": "ready" | "blocked" | "degraded",   // gate verdict
  "deps": [ { "name": "...", "verify": "ok"|"failed", "action": "present"|"installed"|"handoff"|"skipped",
              "source": "...", "scope": "...", "classification": "..." } ],
  "installed": [ "<name@version>" ],             // appended to the registry this run
  "targetEnv": { "gate": "<target.baselineGate>", "runnable": true|false } | null,  // PF-3, null for non-target runs
  "warnings": [ "..." ],                          // e.g. "no sandbox available — installed on host"
  "blockers": [ "..." ],                          // why status==blocked (a default-FAIL verify, a Snyk finding, drift)
  "sandbox": "isolated" | "host" }
```
- `status: ready` ⇒ every approved dep verifies **and** (if installs happened) they ran in a sandbox; `blocked` ⇒
  a verify failed / Snyk over threshold / manifest-hash or dep drift (LD8) / `manager` ∉ allowlist / missing
  structured field / `sandbox_required:true` with no sandbox (LD4); `degraded` ⇒ **either** the target env is
  non-runnable (PF-3) **or** installs ran on the host without a sandbox (`sandbox_required:false`, LD4) — in both
  cases the loop may proceed only on **explicit operator acceptance**, surfaced in-conversation by
  `kata-orchestrate` (N5), never auto-proceeded.

### N4 — `~/.kata/installed-registry.json` (D-registry)
```jsonc
{ "registryVersion": 1,
  "installs": [ { "package": "...", "version": "...", "source": "...", "scope": "global"|"project-local",
                  "classification": "build-time"|"runtime", "project": "<path>", "branch": "...",
                  "installedAt": "<iso>", "used": true } ] }
```
Cleanup report = reference-count `package` across all recorded projects' frozen manifests → **safe-to-remove iff
no other project's manifest still needs it** → recommend; the human executes. Never auto-uninstall.
**Conservative edge handling:** a recorded `project` path that no longer exists or whose manifest is
unreadable/moved ⇒ treat the package as **still needed** (skip-and-note) — never recommend removal on incomplete
evidence. `used` defaults `true`; it is only ever set `false` by an explicit human cleanup action, never inferred.

## 5. Edges / integrity
- **Drift (two forms):** (a) a dep present at preflight but absent from the approved manifest, or (b) the manifest
  hash ≠ the freeze-approved hash (LD8) ⇒ `blocked` + escalate (`human-required`) ⇒ re-freeze. Never install
  outside the approved set.
- **Unbuildable install** (a `manager` ∉ the allowlist, or a missing/garbled structured field) ⇒ `blocked`,
  nothing executed. There is **no freeform string to run**, so `curl|bash` / untrusted-index attacks have no path.
- **Snyk SCA over threshold** ⇒ `blocked` before any install (`mcp__Snyk__snyk_sca_scan`).
- **Install succeeds but re-verify fails** ⇒ `blocked` (default-FAIL).
- **Sandbox:** `sandbox_required:true` + none available ⇒ `blocked` (LD4); `sandbox_required:false` + none ⇒
  host install ⇒ `degraded` (operator must accept; warning surfaced in-conversation).
- **BC:** no manifest / empty manifest ⇒ `status: ready` immediately (nothing to provision; today's loop unchanged).
  `kata-preflight` is invoked by the spine; a run with no declared deps is a no-op pass.

## 6. Acceptance criteria (default-FAIL, runnable)
- A manifest with a present dep ⇒ `ready`, no install attempted (verify passes).
- A manifest with a missing dep (allowlisted `manager` + structured fields) ⇒ engine **builds argv** and runs the
  pinned install (stub runner in tests, argv asserted), re-verifies, records it, `ready`.
- A dep whose `manager` ∉ the allowlist, or with a missing structured field ⇒ `blocked`, install NOT executed;
  the freeform `install` string is never parsed-and-run.
- A dep that fails re-verify after install ⇒ `blocked`.
- A manifest whose hash ≠ the freeze-approved hash ⇒ `blocked` + escalate (LD8).
- `sandbox_required:true` + no sandbox ⇒ `blocked`; `sandbox_required:false` + no sandbox ⇒ `degraded` (not `ready`).
- A target run: `targetEnv.runnable=false` when `target.baselineGate` fails after provisioning ⇒ `degraded`.
- The registry records each install; the cleanup report marks a package safe-to-remove only when no other
  recorded project's manifest needs it (a missing/unreadable project ⇒ treated as still-needed).
- **N5 conditional fail-closed:** with a **manifest present**, `kata-orchestrate` refuses to dispatch when
  `.kata/preflight.json` is **absent, malformed, `blocked`, OR `degraded` without recorded operator acceptance** —
  only `ready` (or accepted-`degraded`) proceeds. With **no manifest present**, PRE-FLIGHT is not required ⇒
  dispatch proceeds (BC — today's loop). A test covers both: no-manifest run dispatches; manifest + missing
  preflight.json refuses.

## 7. Test seams
- N1 engine behind an **injectable runner** `(argv: list[str]) -> (exit, stdout)` — `cmd` is an **argv list**, never
  a shell string; stub verify/install/Snyk in tests; no real machine mutation. Manifest + registry + preflight.json
  are pure JSON round-trips on fixtures. Guard tests: **argv built correctly per `manager`**; `manager` ∉ allowlist
  / missing structured field ⇒ `blocked` (nothing executed); manifest-hash mismatch ⇒ `blocked` (LD8); drift
  rejected; default-FAIL on failed re-verify; `sandbox_required:true`+no-sandbox ⇒ `blocked`,
  `false`+no-sandbox ⇒ `degraded`; cleanup reference-count on multi-project fixtures incl. a missing-project edge;
  Snyk gate via injected verdict (over-threshold ⇒ `blocked` before install).

## 8. Build sequencing (PARKED until freeze-gate SHIP + operator go)
0. **N0 — EXTEND `protocol/dependencies.md`** with the structured install fields (`manager` ∈ allowlist,
   `package`, `version`, optional `index`); demote the freeform `install` string to documentation-only ("never
   executed"); add the **manifest approval-hash** note (recorded at freeze, checked at preflight, LD8). Foundation
   change — do FIRST.
1. **N1 `tools/kata_preflight.py`** (pure core + injectable argv runner) + tests — manifest read/verify, the
   `manager`→argv builder table (allowlisted managers only, forced index), `mcp__Snyk__snyk_sca_scan` SCA gate on
   `package@version` before install, guarded install, re-verify, registry read/write, cleanup reference-count
   (conservative missing-project edge), target-env probe, manifest-hash check, emit `.kata/preflight.json`.
2. **N2 skill `kata-preflight`** (`category: coordinate`, `kata/spine`, never tiered; `allowed-tools` incl.
   `Bash` for verify/install + the Snyk SCA tool + `Write` for the artifacts) driving N1; approve-at-freeze
   provisioning; drift/block escalation; sandbox-degrade surfacing; honest narration.
3. **N5 `kata-orchestrate` precondition** — fail-closed: refuse dispatch unless `.kata/preflight.json` exists,
   parses, and is `ready` (or an operator-accepted `degraded`).
4. **Wiring pointers:** confirm `kata-grill` (enumerate) + `kata-design-doc`/`kata-plan` (write manifest)
   reference `protocol/dependencies.md` (add a by-path pointer if missing — verify-before-reuse first).
**Build-time hardening (from the freeze-gate re-confirm SHIP — fold into N1/N0, not freeze blockers):**
- **H1 — flag/argument injection:** even with argv + no-shell, a `package`/`version` value like `--editable …`,
  `-r …`, or a leading `-` can inject *flags* into an allowlisted manager. N1 MUST: insert a `--` end-of-options
  separator before positional package args, **reject field values beginning with `-`**, and charset-validate
  `package`/`version`.
- **H2 — approval-hash tamper-resistance (LD8):** the manifest approval-hash defends against post-freeze edits
  only if it is **not co-located with / equally writable as** the working-branch manifest. N0/N1 MUST store the
  approval hash in a distinct **freeze artifact** (e.g. committed at freeze), not beside `kata.dependencies.json`.

Build through the recipe (contract+code-bearing): freeze-gate → orchestrated build → kata-evaluate → D98 → merge.
Then **Debug Mode** is unblocked (both blockers cleared).
