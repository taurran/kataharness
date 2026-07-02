---
name: kata-preflight
description: >-
  Spine gate that provisions the freeze-approved dependency set before EXECUTE. Reads kata.dependencies.json,
  verifies each dep, runs guarded installs (argv built from structured fields, Snyk SCA gated,
  manifest-hash checked), records installs to the machine-global D-registry, probes the target environment,
  and emits .kata/preflight.json. Default-FAIL; never tiered (D29/D33).
license: Apache-2.0
version: 0.1.1
category: coordinate
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Bash, Write, AskUserQuestion]
source: >-
  new (KataHarness original, PRE-FLIGHT spine phase D29/N2); drives tools/kata_preflight.py (N1 engine);
  argv-builder pattern from the _COMMAND_BUILDERS registry in tools/kata_dispatch.py; injectable-runner
  from _subprocess_runner in tools/kata_dispatch.py
tags:
  - kata/coordinate
  - kata/spine
  - preflight
  - default-fail
  - gate
---

# kata-preflight — PRE-FLIGHT spine gate

Provision the freeze-approved dependency set before EXECUTE. **Default-FAIL: a dep that won't verify
after provisioning blocks the gate.** Never tiered (D29/D33) — spine gates are a consistency floor, not
a depth dial.

## Invariants (never relax)

- **Never tiered** (D29/D33): no Essential/Standard/Advanced depth variants; spine gates apply uniformly.
- **Default-FAIL on verify**: a dep whose structured `verifyImport` check returns non-zero after
  provisioning ⇒ `blocked`. Nothing silently passes.
- **Manifest shape validated (F1)**: after parse and before dependency extraction, the top-level
  `dependencies` key MUST be present AND a list. A misspelled/renamed key (e.g. `deps`), an absent
  key, or a wrong-typed value ⇒ `blocked` (`manifest-shape` blocker) — never a vacuous `ready`. A
  present-but-**empty** list is a legitimate state and still proceeds to `ready` (do NOT block empty).
- **No freeform string is ever executed**: presence is checked via the structured `verifyImport`
  identifier (compiled to a safe argv), NOT the freeform `dep["verify"]` shell string — which, like
  `dep["install"]`, is documentation-only and is never read or executed (the RCE fix, LD2/LD3).
- **Approve-at-freeze**: provision ONLY the freeze-approved set (deps in `kata.dependencies.json` whose
  manifest hash matches the freeze approval artifact). A dep present at runtime but absent from the
  approved manifest ⇒ drift ⇒ escalate ⇒ re-freeze. Never silent install.
- **Workers never install** (least-privilege): only this gate installs; workers inherit the provisioned
  environment.
- **Never auto-uninstall**: the cleanup report recommends; the human executes.
- **Auto-install runs only behind the manifest-hash + Snyk + sandbox guards**: all four must pass before
  any install argv is executed.

## Engine

The engine is `tools/kata_preflight.py` (N1). This skill drives it; all deterministic logic lives in
the engine (default-FAIL verify, argv builder, guards, registry, hash check, sandbox branch). Do NOT
re-implement engine logic here — call the engine.

**Public engine surfaces (verify-before-reuse — `protocol/reuse-claims.md`; cited by stable symbol name,
not line number, per the cite-by-anchor discipline — line numbers drift, names don't):**

- `run_preflight(repo_root, *, kata_config, runner, snyk_check, sandbox_check, home_dir, approved_hash_path, project_path, branch) -> dict`
  — the deterministic PRE-FLIGHT engine. Returns the N3 `preflight.json` schema dict.
- `preflight_required(repo_root) -> bool` — True iff `kata.dependencies.json` is present at `repo_root`.
  Used by `kata-orchestrate` Preconditions (N5) to determine whether the gate applies.
- `gate_status(repo_root) -> "ready" | "blocked" | "degraded" | "absent"` — reads `.kata/preflight.json`
  status field; `"absent"` if the artifact is missing or malformed.
- `_build_argv(dep, registry_url) -> list[str]` — builds install argv from structured
  `manager`/`package`/`version` fields ONLY. The freeform `dep["install"]` string is **never read or
  executed** (LD2/LD3).
- `_build_verify_argv(dep, manager) -> list[str] | None` — builds the presence-check argv from the
  structured `verifyImport` identifier ONLY (validated per-manager). The freeform `dep["verify"]` string
  is **never executed** (the RCE fix). Returns `None` when no `verifyImport` is supplied.
- `_validate_package(package, manager) -> None` — per-manager package-NAME grammar: rejects any URL/VCS/
  path source spec so no value can bypass the forced registry (`fullmatch`-anchored).
- `_validate_field_value(value, field_name) -> None` — H1 flag-injection guard: rejects leading `-` and
  unsafe charsets (`fullmatch`-anchored).
- `ALLOWED_MANAGERS` — the hard global allowlist: `frozenset({"pip", "uv", "npm", "cargo"})`.

## Procedure

### 0. Read `kata.config` preflight block

Read the `preflight` block from `kata.config` (see `protocol/config.md` → preflight block):
the engine consumes `allowed_registries`, `scan_required` (default `true`), and `sandbox_required`.
(`pin_policy` and `approval_mode` are **advisory/reserved** — documented but not yet enforced by the
engine; version pinning is enforced structurally by requiring a `version` field.) Also read
`target.baselineGate` for the target-env probe. Pass as `kata_config` to `run_preflight`.

### 1. Check whether PRE-FLIGHT is required

Call `preflight_required(repo_root)`.

- **False** (no `kata.dependencies.json`): PRE-FLIGHT is not required. The engine emits
  `status: ready` immediately (BC path). Proceed — today's loop is unchanged.
- **True**: a manifest is present; the gate applies. Continue to step 2.

### 2. Manifest-hash guard (LD8/H2)

`run_preflight` reads the manifest bytes once, computes their SHA-256, and parses those same bytes (no
re-read — TOCTOU-safe), comparing the hash to the approved hash at the default artifact path
`kata.freeze-approval.json` at repo root
(not under `.kata/`; overridable via `approved_hash_path`). **Mismatch ⇒ `blocked` + escalate; the
engine returns before any install.**

This mechanism **detects post-freeze manifest drift** — the loop cannot silently change what it installs
without triggering a mismatch, and the engine **fails closed** on a missing or mismatched artifact. It is
**not** tamper-resistance against a local actor who controls both files; for stronger guarantees, point
`approved_hash_path` at a committed or access-controlled location.

### 3. Snyk SCA pre-install gate (LD3)

When `scan_required: true` (default), the engine calls `snyk_check(package, version)` on each missing
dep BEFORE running any install argv. **Fail-closed both ways:** a scanner that raises ⇒ `blocked`, and the
verdict must be the strict sentinel `True` to proceed — any non-`True` value (incl. a truthy raw result
object) ⇒ `blocked`. When `scan_required: true` and no `snyk_check` is wired ⇒ `blocked` (never installs
unscanned).

Wire `mcp__Snyk__snyk_sca_scan` as the `snyk_check` callable when invoking `run_preflight`, adapting its
result to a strict `bool` (`True` = clean). (Tests inject a stub to avoid real network calls and machine
mutation.)

### 4. Guarded install (LD2/LD3)

For each missing dep that passes all guards above, the engine:

1. Calls `_build_argv(dep, registry_url)` to build install argv from structured
   `manager`/`package`/`version` fields ONLY. `manager` must be in `ALLOWED_MANAGERS`. The forced
   registry URL comes from `_MANAGER_REGISTRY_URLS` — the manifest cannot override it to an untrusted
   index. The freeform `dep["install"]` string is **never read** (LD2/LD3).
2. Validates the package via `_validate_package` (per-manager NAME grammar — no URL/VCS/path source can
   pass) and the version via `_validate_field_value` (H1: rejects leading `-` and unsafe charsets); both
   are `fullmatch`-anchored. Inserts the `--` end-of-options separator before positional package args.
3. Runs install via the injectable runner (`subprocess.run(argv, shell=False)` — never `shell=True`).

**If `manager` ∉ `ALLOWED_MANAGERS`, or any required structured field is missing, or H1 validation
fails: the engine sets `status: blocked` and skips that dep — no install is attempted.**

### 5. Sandbox branch (LD4)

The engine branches on `sandbox_required` from the config:

- `sandbox_required: true` + no sandbox available ⇒ `blocked` (hard-stop; the policy is not silently
  downgraded).
- `sandbox_required: false` + no sandbox ⇒ install on host ⇒ `status: degraded` + warning (operator
  must explicitly accept; surface via breakthrough-alert before any dispatch).

Wire the `sandbox_check` injectable when calling `run_preflight`.

### 6. Re-verify after install (LD7 — default-FAIL)

After each install the engine re-runs the dep's structured `verifyImport` presence check (the same safe
argv built by `_build_verify_argv` — never the freeform `verify` string). Non-zero exit ⇒ `blocked`. An
install that succeeds but whose verify still fails is a gate failure — default-FAIL is not relaxed
post-install.

### 7. Record to D-registry (N4)

Successful installs are appended to `~/.kata/installed-registry.json` by `_record_install`.
Pass `project_path` and `branch` so cleanup reference-counting is accurate.

### 8. Target-env probe (PF-3 / LD5)

If `target.baselineGate` is set, the engine runs it as the target-env probe. Failure ⇒
`targetEnv.runnable: false` ⇒ `status: degraded`. Report-only; Debug Mode consumes this snapshot.
(The `baselineGate` is an operator-supplied `kata.config` command — the same trust domain as a test
runner — so it is split with `shlex`; it is NOT a manifest-supplied string.)

### 9. Cleanup report (PF-2 / LD6)

The engine reference-counts each recorded package across all recorded projects' manifests via
`_compute_cleanup_report`. A package is `safe_to_remove: true` only
when no other recorded project's manifest still needs it. **Never auto-uninstall** — the report is a
recommendation the human executes. Conservative: a missing or unreadable project path ⇒ treat the
package as still needed (never recommend removal on incomplete evidence).

### 10. Emit `.kata/preflight.json` (N3)

The engine writes the N3 schema artifact via `_write_preflight`.
`kata-orchestrate` reads the `status` field from this artifact via `gate_status(repo_root)`.

## Escalation paths

**`status: blocked`:** Surface the `blockers` list in the conversation immediately (breakthrough-alert —
never silently queued). Do NOT dispatch workers. Requires human action:

- Hash mismatch or drift ⇒ re-freeze, re-approve, re-run PRE-FLIGHT.
- Missing structured field (`manager`/`package`/`version`) ⇒ fix manifest schema, re-freeze.
- Snyk finding ⇒ resolve the advisory, re-approve, re-run.
- Sandbox-required + no sandbox ⇒ provide an isolated environment or change `sandbox_required`.

**`status: degraded`:** Surface the `warnings` list in the conversation immediately. Use
`AskUserQuestion` to ask the operator whether to accept this degraded run (no sandbox installed on host;
non-runnable target environment). Operator acceptance is explicit and per-run — never cached or inferred.
Only on explicit acceptance may downstream dispatch proceed.

**Drift (post-freeze manifest edit, or dep absent from the approved manifest):** `blocked` + escalate
(`human-required`). The path forward: re-freeze, re-approve, re-run PRE-FLIGHT.

## Honest scope

Auto-install is stub-tested via the injectable runner — no freeform shell string is ever executed; the
`dep["install"]` **and** `dep["verify"]` freeform fields are documentation-only and are never read or run
by the engine (presence is checked only via the structured `verifyImport`). The real Snyk
SCA scan is wired in the skill layer (`mcp__Snyk__snyk_sca_scan`); tests inject a stub verdict to avoid
real network calls and machine mutation. Workers inherit the provisioned environment; they do not
install. If a worker's environment is missing a dep that PRE-FLIGHT passed, that is an isolation or
install-scope issue to escalate — not a reason for the worker to self-install.
