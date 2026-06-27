---
title: "kata-preflight — FROZEN PLAN"
status: FROZEN (2026-06-26) — freeze-gate kata-review SHIP (HOLD→fixes→re-confirm). Pending operator go to build.
spec: kata-preflight
compiled-from: DESIGN.md (N0–N5, LD1–LD8, §8 build sequence + H1/H2 hardening)
recipe: HANDOFF §5
ownership-disjoint: true
waves:
  - wave-1: [A, C]
  - wave-2: [B]   # depends_on A (cites the engine surfaces; the new skill must exist for the orchestrate wikilink)
---

# kata-preflight — FROZEN PLAN

> Build the PRE-FLIGHT spine phase: a guarded auto-installer + machine-global registry + reference-counted cleanup
> report + target runnable-env probe, gated default-FAIL, never tiered. Security model is structural: **no freeform
> shell string is ever executed** — argv is built from structured manifest fields (manager allowlist → forced
> registry), `subprocess(argv)` never `shell=True`. See DESIGN LD1–LD8 + N0–N5.

## LOCKED (from DESIGN; trace there)
- **L-N0** EXTEND `protocol/dependencies.md` with structured install fields `{manager∈allowlist, package, version,
  index?}`; freeform `install` string demoted to **docs-only, never executed**; add the **freeze approval-hash**
  note (stored in a distinct freeze artifact, H2). · **L-N1** `tools/kata_preflight.py` engine (argv builder,
  guarded install, Snyk SCA pre-install, registry, cleanup, target-env probe, emit `.kata/preflight.json`),
  injectable argv runner. · **L-N2** new skill `kata-preflight` (`category: coordinate`, `kata/spine`, never
  tiered). · **L-N5** `kata-orchestrate` fail-closed precondition. · **L-H1** flag-injection guard (`--`
  separator, reject leading-`-` values, charset-validate). · **L-H2** approval-hash in a distinct freeze artifact.

## Slices (disjoint file ownership)

### Slice A — foundation schema + the engine  *(code-bearing; N0 + N1 + H1/H2)*
- **owns:** `protocol/dependencies.md`, `tools/kata_preflight.py`, `tools/tests/test_kata_preflight.py`
- **read_first:** `protocol/dependencies.md`, `protocol/config.md:22,29-36`, `tools/kata_dispatch.py`
  (`_COMMAND_BUILDERS`:150, `_subprocess_runner`:168, `build_brief` guards), `tools/gate_emit.py`,
  `tools/kata_settings.py` (registry-write pattern), `.planning/specs/kata-preflight/DESIGN.md`,
  `.planning/DECISIONS.md` (D29, D-registry), `protocol/reuse-claims.md`
- **action:**
  1. **N0:** add structured `{manager, package, version, index?}` fields to `protocol/dependencies.md`; mark the
     freeform `install` string **docs-only / never executed**; document the freeze approval-hash (a distinct
     committed freeze artifact, not beside `kata.dependencies.json`).
  2. **N1 engine** (`tools/kata_preflight.py`, injectable `runner(argv)->(exit,stdout)`):
     - read manifest + verify presence (run each `verify`); default-FAIL on failed verify.
     - **argv builder** = a fixed `manager`→builder table (only allowlisted managers ⊆ `allowed_registries`);
       force the index from `allowed_registries`; **H1**: `--` end-of-options separator, reject any field value
       starting with `-`, charset-validate `package`/`version`. `manager` ∉ allowlist / missing field ⇒ `blocked`.
     - **Snyk SCA pre-install** hook (`mcp__Snyk__snyk_sca_scan` on `package@version`; injected verdict in tests) —
       over-threshold ⇒ `blocked` before install.
     - guarded install via the runner (never `shell=True`) → re-verify → record to `~/.kata/installed-registry.json`.
     - **manifest-hash check (L-H2/LD8):** mismatch vs the approved hash ⇒ `blocked` + escalate.
     - **sandbox branch (LD4):** `sandbox_required:true`+no-sandbox ⇒ `blocked`; `false`+no-sandbox ⇒ `degraded`.
     - **cleanup report:** reference-count across recorded projects; missing/unreadable project ⇒ still-needed.
     - **target-env probe:** run `target.baselineGate`; fail ⇒ `targetEnv.runnable=false` ⇒ `degraded`.
     - emit `.kata/preflight.json` (N3 schema).
     - **`preflight_required(repo_root) -> bool`** helper (manifest present?) so the N5 BC branch is unit-testable,
       and a **`gate_status(repo_root) -> "ready"|"blocked"|"degraded"|"absent"`** reader the orchestrate
       precondition calls (keeps N5 prose thin + the BC decision in tested code).
- **acceptance (default-FAIL):**
  - argv built correctly per manager (asserted); `manager`∉allowlist / missing field / leading-`-` value ⇒
    `blocked`, nothing executed; freeform `install` string never run.
  - missing dep (allowlisted) ⇒ stub-install → re-verify → recorded → `ready`; failed re-verify ⇒ `blocked`.
  - manifest-hash mismatch ⇒ `blocked`; Snyk over-threshold (injected) ⇒ `blocked` pre-install.
  - `sandbox_required:true`+no-sandbox ⇒ `blocked`; `false`+no-sandbox ⇒ `degraded`.
  - non-runnable target ⇒ `degraded`; cleanup conservative on missing project.
  - `preflight_required` is False with no manifest / True with a manifest; `gate_status` reads each state incl. `absent`.
  - **mutation** `prove_non_vacuous` non-vacuous on a new line.
- **verify:** `cd tools && uv run pytest tests/test_kata_preflight.py -q`

### Slice B — the skill + the orchestrate precondition  *(contract-bearing; N2 + N5; depends_on A)*
- **owns:** `skills/coordinate/kata-preflight/SKILL.md` (new), `skills/coordinate/kata-orchestrate/SKILL.md`, `README.md`
- **read_first:** `tools/kata_preflight.py` (Slice A — cite real surfaces), `.planning/specs/kata-preflight/DESIGN.md`,
  an existing spine skill for the frontmatter shape (e.g. `skills/evaluate/kata-evaluate/SKILL.md`),
  `skills/coordinate/kata-orchestrate/SKILL.md` Preconditions §0, `protocol/reuse-claims.md`
- **action:**
  1. **N2:** write `skills/coordinate/kata-preflight/SKILL.md` — drives the engine (approve-at-freeze provisioning;
     drift/block escalation; sandbox-degrade surfacing; honest narration). Frontmatter: `category: coordinate`,
     `kata/spine`, never-tiered, `allowed-tools` incl. `Bash` (verify/install) + the Snyk SCA tool + `Write`.
     Cite the engine surfaces by **section-name / real `file:line`** (verify-before-reuse).
  2. **N5:** add a `kata-orchestrate` Preconditions §0 precondition — **conditional + fail-closed (BC-preserving)**,
     thin prose that calls Slice A's `kata_preflight.preflight_required(repo_root)` + `gate_status(repo_root)`:
     if not required (no manifest) ⇒ proceed (today's loop); if required ⇒ refuse unless `ready` (or
     operator-accepted `degraded`); `blocked`/`absent`/malformed ⇒ refuse. The fail-closed bite applies only once
     deps are declared.
  3. **README index:** add the new skill row so `validate_skills` sync passes (36→**37** skills).
- **acceptance (REVIEW-gated content + default-FAIL validate):**
  - new skill parses; `[[kata-preflight]]` wikilink resolves; orchestrate precondition is fail-closed + cites the
    N3 contract; README index in sync. Reuse claims cite `file:line`.
  - `validate_skills.py` → **37 skills, 0 errors**.
- **verify:** `cd tools && uv run python validate_skills.py`  *(content acceptance = review-gated)*

### Slice C — manifest-enumeration wiring pointers  *(contract-bearing, `.md`; parallel with A)*
- **owns:** `skills/plan/kata-grill/...` (the grill skills), `skills/.../kata-design-doc/SKILL.md`,
  `skills/.../kata-plan/...` — **verify exact paths first; own only files actually edited**
- **read_first:** `protocol/dependencies.md`, the three skills, `protocol/reuse-claims.md`
- **action:** verify-before-reuse — check whether `kata-grill` (enumerate deps), `kata-design-doc` / `kata-plan`
  (write the manifest) already reference `protocol/dependencies.md`; **add a by-path pointer only where missing**
  (D29 responsibility split). If all already reference it → Slice C is a no-op (record that; own nothing).
- **acceptance:** the enumerate→manifest responsibility is pointed at `protocol/dependencies.md` in each of the
  three skills (or confirmed already present); `validate_skills.py` → 0 errors.
- **verify:** `cd tools && uv run python validate_skills.py`

## Integration gate
1. `cd tools && uv run pytest -q` (≥ 552 + new) + `uv run python validate_skills.py` (**37/0**).
2. `mcp__Snyk__snyk_code_scan` on `tools/kata_preflight.py` (the new code-bearing file).
3. `gate_emit.emit_gate_artifacts(..., mutation_records=<A's prove_non_vacuous>)` → `.kata/{RESULT,footprint,mutation}.json`;
   concurrency.json per `protocol/board.md`.
4. Fresh-context **`kata-evaluate`** (no-write, 9-rubric, default-FAIL) — reproduce artifacts + execute the guard
   seams live (argv-builder rejects bad input; manifest-hash mismatch blocks; sandbox branch; never runs a freeform string).
5. Standing **D98 `kata-review`** (≥ standard, adversarial) — re-attack the auto-install security model on the real code.
6. Operator merge gate → merge/push/checkpoint (D109) → **Debug Mode unblocked**.

## Scope / honesty
- Auto-install is **stub-tested** (injectable argv runner) — no real machine mutation in tests; a real install runs
  only behind the freeze-approved manifest + hash + Snyk gate + sandbox preference.
- Workers never install (least-privilege). Never auto-uninstall (cleanup recommends only).
- BC (RESOLVED): the N5 precondition is **conditional on a manifest existing** — a run that declared no deps
  (no `kata.dependencies.json`) never needs preflight and dispatches as today's loop; the fail-closed refusal
  applies only when a manifest is present but preflight is missing/blocked/unaccepted. Both branches are tested
  (Slice B). This closes the "no-deps run has no preflight.json → wrongly refused" hole.
