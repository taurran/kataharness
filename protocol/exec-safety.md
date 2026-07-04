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
| `kata_install._real_probe_runner` (confirm-probe) | fixed per-platform `_PROBE_COMMANDS` argv (codex/kiro lambdas, `kata_install.py:278-281`) | internal | Fixed argv from `_PROBE_COMMANDS` lambda; `shell=False`; `stdin=subprocess.DEVNULL`. |
| `mutation_check.run_named_test` | test path/name | internal | Fixed `["uv","run","pytest", f"{path}::{name}", "-q"]` argv; `shell=False`. Test node-ID is a flag-VALUE (DATA), never the program. |
| `benchmark.run_dual_gate` → `mutation_check.run_named_test` (delegated) | control/`repeat_from`-supplied test-IDs (control criteria fields, external trust domain) | **external** | `benchmark._guard_node_id` — rejects leading `-` path segments (pytest-flag injection), `..` traversal (via `_guard_path` / CWE-23), and node-ID paths escaping the clone root (resolved-containment check) — applied before any ID reaches `run_named_test`; `shell=False` (inherited from delegated sink). |
| `footprint` (`changed_files`/`diff_stat`) | git ref | internal | Fixed `["git",…,ref]` argv; `shell=False`. |
| `kata_trail.snapshot_board` | resolved board path + prior trail ref (from `git rev-parse --verify`) | internal | Fixed argv list for each git plumbing call (`hash-object -w`, `mktree`, `rev-parse --verify`, `commit-tree`, `update-ref`); `shell=False` throughout. The board path is resolved from the trusted `repo_root` argument and never originates from external input. The mktree stdin is constructed from the blob SHA (hex-safe ASCII from git) and the literal filename `board.md`. No external field influences any argv element. |
| `kata_restore` (`_ref_exists`, `read_board_from_trail`, `collect_integrated_tasks`, `cleanup_stale_task`) | `repo_root` (resolved by `Path.resolve()`), `integration_branch` (harness-supplied branch name), `task_id` (harness-supplied task-id parsed from PLAN.md) | internal | `shell=False` throughout; fixed argv lists for all git calls (`rev-parse --verify`, `cat-file -p`, `log --format=%B`, `worktree prune`, `branch -D`). Variable parts (`integration_branch`, `task_id`, branch name `task/<id>`) are DATA, never the program (`argv[0]`). Both originate from the harness's own PLAN-parsing output or the `integration_branch` parameter supplied by the orchestrator — not from any external manifest or worker payload. No external field influences any argv element. |
| `contract_gate._scan_integration_commits` (Freeze/Float M1-P2 final gate) | `repo_root` (resolved by `Path.resolve()`), `integration_branch` (harness-supplied branch name), `plan_path` (harness-supplied frozen-PLAN path) | internal | `shell=False` throughout; fixed argv lists for both git reads (`log -1 --format=%H <branch> -- <plan>` for the fork-point, `log <fork>..<branch> --format=%x00%H%n%B --` for the commit-delimited body scan). Variable parts (`integration_branch`, `plan_path`) are DATA (a branch name and a flag-valued path after `--`), never the program (`argv[0]`); both originate from the orchestrator's own freeze context, not from any external manifest or worker payload. Fails closed (raises) on any git error or unresolvable fork-point — never a permissive fallback. No external field influences any argv element. |
| `kata_telemetry.scan_checkpoints` (Freeze/Float M4-P0 checkpoint scan) | `repo_root` (resolved by `Path.resolve()`), `branch` + `integration_ref` (harness-supplied refs) | internal | `shell=False` throughout; fixed argv lists for both git reads (`rev-list --reverse <branch> ^<integration_ref>` for the task-own commit walk, `show -s --format=%P%n%B <sha>` per commit) via the shared `_run_git` helper (`git -c core.quotepath=off …`). Variable parts (`branch`, `integration_ref`, `sha`) are DATA (refs/positional operands), never the program (`argv[0]`); all originate from the orchestrator's own dispatch context, not from any external manifest or worker payload. Fails closed (raises `TelemetryError`) on any git error — never a permissive `[]` (D139). No external field influences any argv element. |
| `kata_telemetry.evidence_digest` / `evidence_entries` (M4-P0 evidence pin) | `repo_root` (resolved by `Path.resolve()`), chunk `paths` (harness/CLI-resolved from `git diff --cached`), optional `commit` (harness-supplied SHA) | internal | `shell=False` throughout; fixed argv lists (`ls-files -s -- <paths>` for stamp mode, `ls-tree -r <treeish> -- <paths>` for verify + parent-tree mode, `ls-tree HEAD -- <path>` for the tracked-in-HEAD deletion check, `show -s --format=%P <commit>` for parents) via `_run_git` (`core.quotepath=off` pinned so unicode paths are byte-stable). The paths are flag-VALUES after `--` (DATA), never the program; they originate from the harness's own staged-diff resolution, not from any external manifest or worker payload. Fails closed (raises `TelemetryError`) on empty paths (vacuous pin) or an unresolvable path — never hashed-as-missing. No external field influences any argv element. |
| `kata_telemetry.checkpoint_changed_files` (M4-P0 per-checkpoint lane drift) | `repo_root` (resolved by `Path.resolve()`), `sha` (harness-supplied SHA) | internal | `shell=False`; fixed argv `show --no-renames --name-only --format= <sha>` via `_run_git` (`core.quotepath=off` + `--no-renames` pin a deletion-visible, config-independent changed-set — the `changed_in_task` F5-1 precedent). The `sha` is a positional DATA operand, never the program; it originates from `scan_checkpoints`' own walk, not from any external payload. Fails closed (raises `TelemetryError`) on any git error (D139). No external field influences any argv element. |
| `kata_telemetry._emit_trailer` (M4-P0 CLI `emit-trailer`) | `--repo-root` (worker worktree root, orchestrator-injected), staged `paths` (default = `git diff --cached --name-only`) | internal | `shell=False`; fixed argv `diff --cached --name-only --no-renames` (default path resolution) via `_run_git` (`core.quotepath=off`), then delegates to `evidence_digest` (stamp mode). All git runs against the required `--repo-root` argv value (gate v2 F2 — never a CWD-relative default, so the `uv run --directory <tools-dir>` prefix cannot digest the wrong repo). The worktree root and paths are DATA supplied by the orchestrator's dispatch brief, not from any external manifest; the trailer JSON is authored by the tool, never hand-written by the worker. Empty staging fails closed (raises `TelemetryError` — the stage-first worker error). No external field influences any argv element. |
| `mutation_run` default runner | mutation test command (frozen plan) | operator | `shell=True` — **registered exception**: operator/plan-authored test command, never external input. |
| `run_result.run_gate` | gate command (`kata.config`/plan) | operator | `shell=True` — **registered exception**: operator-authored gate command, never external input. |
| `iac_apply.run_apply` — **TF plan** flow (`iac_apply.build_tf_plan_argv`) | plan-out path / var-file paths / chdir | **operator + approval-artifact gate** | Structured argv built by `build_tf_plan_argv` (`["terraform",…,"plan","-input=false","-lock=true","-out",<out>,…]`); `shell=False`; path identifiers are flag-VALUES (DATA), `fullmatch`-grammar-validated + `..`-guarded, leading `-` rejected; **no `-target` parameter** (FORBIDDEN). Gated on present+matching `kata.iac-apply-approval.json` + capability grant + creds. **Execution DEFERRED — `run_apply` raises `NotImplementedError` (n=0-live); not shipped runnable.** |
| `iac_apply.run_apply` — **TF apply** flow (`iac_apply.build_tf_apply_argv`) | saved plan-file path / chdir | **operator + approval-artifact gate** | Structured argv built by `build_tf_apply_argv` (`["terraform",…,"apply","-input=false","-lock=true","--",<plan_file>]`); `shell=False`; the approved saved plan file IS the authorization (Atlantis discipline) — **never `-auto-approve`**, never a freeform target; `--` end-of-options before the positional DATA; `plan_file` grammar-validated + `..`-guarded. Gated as above. **Execution DEFERRED — `run_apply` raises `NotImplementedError` (n=0-live); not shipped runnable.** |
| `iac_apply.run_apply` — **CFN create-change-set** flow (`iac_apply.build_cfn_create_changeset_argv`) | stack name / change-set name / template path | **operator + approval-artifact gate** | Structured argv built by `build_cfn_create_changeset_argv`; `shell=False`; stack/change-set names validated against the strict CFN name grammar, `template_path` `..`-guarded then `file://`-prefixed; identifiers are DATA, never the program. Gated as above. **Execution DEFERRED — `run_apply` raises `NotImplementedError` (n=0-live); not shipped runnable.** |
| `iac_apply.run_apply` — **CFN execute-change-set** flow (`iac_apply.build_cfn_execute_changeset_argv`) | stack name / change-set id (ARN) | **operator + approval-artifact gate** | Structured argv built by `build_cfn_execute_changeset_argv`; `shell=False`; the immutable `change_set_id` is DATA validated by its OWN dedicated `fullmatch` ARN grammar (permits `:`/`/`; rejects whitespace/`;`/`|`/`..`/`://`/leading `-`), distinct from + stricter than the stack-name grammar. Gated as above. **Execution DEFERRED — `run_apply` raises `NotImplementedError` (n=0-live); not shipped runnable.** |

**The deferred `iac_apply` rows are `shell=False`** (the four `build_*_argv` are pure functions returning a `list[str]`; the plan/change-set identifier is positional/flag-valued DATA, never `argv[0]`, never shell-interpolated). They are therefore **NOT** added to `_SHELL_TRUE_ALLOWLIST` and `tools/tests/test_exec_safety.py` stays green unchanged. They are the **highest-stakes sink class in the repo** — a live cloud apply destroys real, non-git-reversible infra — and they are **NOT runnable in this build**: `iac_apply.run_apply` is the single cloud-mutating seam and raises `NotImplementedError` before any `subprocess` import, reachable only behind a present+matching approval artifact AND a present capability grant AND present creds, and not runnable even then (the creds wall). **Zero-uncontrolled-sink posture for the slice:** `tools/iac_apply.py` spawns no subprocess and calls no `eval`/`exec`; the builders are pure structured-argv (assertable by source scan, mirroring `drift_gate.TestExecSafety`).

## When the surface is not safe

If an external value must influence execution but cannot be expressed as a validated structured field, it is a
**NEW execution capability**, not a reuse of an existing safe sink. Scope it explicitly: define the field, its
grammar, the argv it compiles to, the trust domain, add it to the registry, and re-review before freeze. Do not
soft-label ("probably fine", "operator controls it") — the distinction is binary: validated-structured-external,
or operator/internal-and-registered.

## In-process evaluation of external expressions

Not all external-trust-domain input reaches a subprocess. The `kata-comprehend` oracle (LD2/LD7) produces
**LLM-authored Python boolean expressions** (FM pre/postcondition assertions) that the spec-wrapper evaluates
at runtime. These are also external-trust-domain input — they are partially-trusted even after schema
validation — and the same injection class applies: if evaluated via `eval`/`exec`, a crafted assertion can
escape the sandbox (e.g. `().__class__.__bases__[0].__subclasses__()…` reaches `os`/`subprocess`).

**Rule for in-process evaluation of external expressions:**

> An LLM-authored or contributor-supplied expression string **MUST NEVER be passed to `eval` or `exec`**,
> including `eval(expr, {"__builtins__": {}}, ns)` (known-escapable). The evaluator must be an **AST
> allowlist**: parse with `ast.parse(expr, mode="eval")`, walk every node, and **reject** any node outside a
> strict whitelist (`Compare`, `BoolOp`, `UnaryOp`, `BinOp`, operators, `Constant`, `Name` (Load-only),
> `List`/`Tuple`/`Dict`/`Set` literals, `Subscript`/`Slice` over those). **No `Attribute` access; no `Call`
> outside a fixed safe-symbol table** (`len`, `abs`, `min`, `max`, `sum`, `sorted`); no comprehensions; no
> `Lambda`; no walrus. Names resolve only from the bound call-namespace + the fixed safe-symbol table.
> A non-conforming expression → `ValueError`, never execution. **The guard also covers resource
> exhaustion** (a structurally-valid assertion can still hang/OOM): exclude unbounded-iteration symbols
> (`range`), **reject `**` exponentiation entirely** (chained Pow explodes multiplicatively under any
> per-exponent cap), cap `<<` shifts, and cap the AST node count.

### In-process sink registry

Every place the harness evaluates an external expression in-process (not via subprocess).

| Sink (`tools/…`) | Input source | Domain | Guard |
|---|---|---|---|
| `function_model._safe_eval` | FM pre/postcondition assertions (LLM-authored by `kata-comprehend`) | **external** | AST allowlist — `ast.parse` + `_walk_verify` rejects any non-whitelisted node; pure recursive `_eval_node` evaluates — **never `eval`/`exec`**; no `Attribute`; no out-of-allowlist `Call`. **Resource-exhaustion guard** (D98): `range` is excluded from the safe-symbol table (no unbounded iteration), **`**` exponentiation is rejected entirely** (a chained Pow explodes the integer multiplicatively under any per-exponent cap), `<<` shifts are capped (`_MAX_SHIFT`), and the AST node count is capped (`_MAX_ASSERTION_NODES`) — so all integer sizes grow only linearly in node count. A structurally-valid but resource-exhausting assertion is rejected, not run. |

## Watch-list (operator-domain `shell=True` sinks)

`mutation_run` and `run_result.run_gate` use `shell=True` on operator-authored commands. They are safe **only
while** their input stays operator/internal. If a future change ever routes an external (manifest/worker) value
into either, that is an immediate RCE — convert it to `shell=False` + structured argv first and move its row to
the **external** domain.
