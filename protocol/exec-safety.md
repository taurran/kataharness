# protocol/exec-safety.md — the execution-surface contract

A cross-tool contract enforcing **structured-argv-only execution** — the guard that stops the
command/code-injection (RCE) class from recurring. This is the canonical source of truth; responsible code
and skills reference it by path (`protocol/exec-safety.md`), never by `[[wikilink]]`.

## Why this exists

The dependency-manifest auto-installer (`kata-preflight`) surfaced the **same execution-injection class three
times** — three different manifest fields each reached a subprocess (D111):

1. the freeform `install` shell string was executable (caught at freeze-gate),
2. the `package` field accepted a URL/VCS/path *source* that bypassed the forced registry → postinstall RCE
   (caught by D98),
3. the freeform `verify` shell string was executed via `shlex.split` *before* the SCA gate (caught by the
   D111 holistic red-team).

Each was fixed in isolation — whack-a-mole — because there was no standing rule that the *next* field would
have to satisfy. This contract makes the rule explicit and the sink set auditable, so a new field or a new
sink must be justified against it rather than rediscovered as a vulnerability.

This is a **structural invariant** in the sense of D33 (never tiered) and an instance of recurrence-hardening
(D101): a class that recurred is now hardened at the responsible surface, not re-patched per occurrence.

## The guard (verbatim contract text)

> **Any value that originates outside the orchestrator's own trust boundary (a dependency manifest, a
> downstream artifact, a worker-supplied field) and reaches a subprocess MUST be a STRUCTURED, validated
> field compiled into an `argv list` run with `shell=False`.** A freeform command/shell string from such a
> source is **never executed** — it is documentation-only (like `dep["install"]` / `dep["verify"]`). Validate
> every external field with an explicit allowlist/grammar (`fullmatch`-anchored) before it enters argv. Treat
> "this string is safe to run" as a **claim to verify, not an assumption**. `shell=True` is permitted ONLY
> for an **operator-trust-domain** command (the operator's own test/gate/mutation command from `kata.config`
> or the frozen plan — the same trust as a test runner), never for external input, and every such sink must
> appear in the registry below.

## Trust domains

| Domain | Definition | Execution rule |
|---|---|---|
| **external** | A value from a dependency manifest, a downstream/contributed artifact, or a worker payload. Partially-trusted even when hash-approved at freeze (it may be AI-generated or contributed and only skimmed). | **Structured argv + `shell=False` + validated.** Never a freeform string. Never `shell=True`. |
| **operator** | A command the operator authored in `kata.config` or the frozen plan (test command, `baselineGate`, mutation/gate command). | May use `shell=False` (preferred) or `shell=True` (same trust as a test runner). Must be registered below. |
| **internal** | A fixed argv the harness constructs from its own constants (e.g. `["git","diff",ref]`). | Fixed argv + `shell=False`. The variable part (a ref/path) is data, not the program. |

## Sink registry (verify-before-add — keep in sync with the code)

Every place the harness spawns a subprocess. **A new sink — or a new external field feeding an existing sink
— must be added here with its trust domain and guard, and must satisfy the guard above.** The
`tools/tests/test_exec_safety.py` regression rule fails if a new `shell=True` appears outside this registry.

| Sink (`tools/…`) | Input source | Domain | Guard |
|---|---|---|---|
| `kata_preflight._default_runner` (install) | manifest `manager`/`package`/`version` | **external** | `_build_argv` — fixed manager→builder table; `_validate_package` per-manager name grammar; `_MANAGER_REGISTRY_URLS` forced; `shell=False`; `--` end-of-options. |
| `kata_preflight._default_runner` (verify) | manifest `verifyImport` | **external** | `_build_verify_argv` — per-manager identifier grammar (`fullmatch`) compiled to `python -c`/`node -e`/`<bin> --version`; `shell=False`. Freeform `dep["verify"]`/`dep["install"]` are **docs-only, never executed**. |
| `kata_preflight` target-env probe | `target.baselineGate` (`kata.config`) | operator | `shlex.split` → `shell=False`. Operator-authored command. |
| `kata_dispatch._subprocess_runner` | role/platform brief (`kata.config` roles) | operator | Built by the fixed `_COMMAND_BUILDERS` table; `shell=False`. |
| `kata_install` runner | per-platform install command | internal | Fixed argv per platform; `shell=False`. |
| `mutation_check.run_test` | test path/name | internal | Fixed `["uv","run","pytest",…]` argv; `shell=False`. |
| `footprint` (`changed_files`/`diff_stat`) | git ref | internal | Fixed `["git",…,ref]` argv; `shell=False`. |
| `mutation_run` default runner | mutation test command (frozen plan) | operator | `shell=True` — **registered exception**: operator/plan-authored test command, never external input. |
| `run_result.run_gate` | gate command (`kata.config`/plan) | operator | `shell=True` — **registered exception**: operator-authored gate command, never external input. |

## When the surface is not safe

If an external value must influence execution but cannot be expressed as a validated structured field, it is a
**NEW execution capability**, not a reuse of an existing safe sink. Scope it explicitly: define the field, its
grammar, the argv it compiles to, the trust domain, add it to the registry, and re-review before freeze. Do not
soft-label ("probably fine", "operator controls it") — the distinction is binary: validated-structured-external,
or operator/internal-and-registered.

## Watch-list (operator-domain `shell=True` sinks)

`mutation_run` and `run_result.run_gate` use `shell=True` on operator-authored commands. They are safe **only
while** their input stays operator/internal. If a future change ever routes an external (manifest/worker) value
into either, that is an immediate RCE — convert it to `shell=False` + structured argv first and move its row to
the **external** domain.
