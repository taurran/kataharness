# protocol/dependencies.md — the Dependency Manifest schema

> Enumerated during GRILL, frozen into the DESIGN/PLAN, approved as part of the freeze, and provisioned by
> `kata-preflight` (Spec D) in the PRE-FLIGHT phase BEFORE the loop launches (D29). A long-running closed
> loop must never stall mid-flight on a missing dependency. Machine state (JSON/table), not vault-managed.

## Location
`kata.dependencies.json` (JSON) at the working-branch root — written from the frozen manifest at FREEZE, read by `kata-preflight` in PRE-FLIGHT.

## Why it is a *frozen decision*, not a pre-flight decision
The manifest is part of the frozen contract: the human approves the dependency *set + sources* when approving
the design (`approval_mode: approve-at-freeze`). PRE-FLIGHT only **provisions** the approved set and verifies
it — it makes no new decisions. A dependency discovered later that is NOT in the approved manifest is a drift
signal ⇒ escalate ⇒ deliberate re-freeze (never a silent install). Workers **cannot install** at all
(least-privilege); discovery mid-loop escalates to the orchestrator.

## Per-entry fields

### Identity + metadata
| Field | Type | Meaning |
|---|---|---|
| `name` | string | The dependency identifier (package/tool/MCP/repo/template name). |
| `type` | `"library" \| "tool" \| "mcp" \| "repo" \| "template" \| "runtime" \| "capability"` | What kind of thing it is. |
| `purpose` | string | Why the build needs it (traceable to a DESIGN requirement). |
| `source` | string | Registry/URL + a short trust note; reviewed by the human at freeze. |
| `hash` | string | Optional integrity hash/checksum for the pinned artifact; verified on install when present. |
| `scope` | `"global" \| "project-local"` | Install scope. Prefer `project-local` + pinned for determinism + easy cleanup (D-registry). |
| `classification` | `"build-time" \| "runtime"` | `runtime` ⇒ must be bundled into the artifact (a packaging task) → its global base copy becomes a cleanup candidate; `build-time` ⇒ removable after the run (D-registry). |

### Structured install fields (N0 — REQUIRED for PRE-FLIGHT auto-install)

These fields let `kata-preflight` **build the install argv from structured data** — the engine
maps `manager` → a fixed argv builder (like `kata_dispatch._COMMAND_BUILDERS`) and forces the
registry/index from `preflight.allowed_registries`. No freeform string is ever executed.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `manager` | `"pip" \| "uv" \| "npm" \| "cargo"` | **yes** | The package manager. Must be in `preflight.allowed_registries` **and** in the engine's hard `ALLOWED_MANAGERS` allowlist (`tools/kata_preflight.py`). Any `manager` not in both lists ⇒ `blocked`, nothing executed. |
| `package` | string | **yes** | Package/crate/npm name. Per-manager name grammar enforced: pip/uv `[A-Za-z0-9._-]+` (with optional `[extras]`); npm optional `@scope/` prefix + `[a-z0-9._-]+`; cargo `[A-Za-z0-9_-]+`. Universal rejects: values containing `://`, starting with `git+`/`http`, containing `..` (source-injection guard, BLOCKER 1). A value starting with `-` is **rejected** (flag-injection guard H1). `:`, `/` (non-npm), and other source-spec characters are rejected by the per-manager grammar. |
| `version` | string | **yes** | Pinned version string (honor `preflight.pin_policy`). Charset: `[A-Za-z0-9._\-+~^]` only — `:` and `/` are forbidden (they would make a version value a source spec). Leading `-` is **rejected** (H1). |
| `index` | string | no | Optional override label (e.g. `"pypi"`, `"npmjs"`). **Informational only** — the engine **forces** the actual registry URL from `preflight.allowed_registries`; a manifest-supplied URL is never used. |
| `verifyImport` | string | recommended | A **validated identifier** proving presence — the engine compiles it into a safe argv (pip/uv → `python -c "import <name>"`; npm → `node -e "require('<name>')"`; cargo → `<name> --version`), never a freeform shell. Per-manager grammar enforced (Python dotted module / npm name / cargo binary name); an identifier that fails the grammar ⇒ `blocked`, nothing executed. PRE-FLIGHT is **default-FAIL** on it: a dep that won't verify after provisioning ⇒ `blocked`. |

### Docs-only fields (NEVER executed)

| Field | Type | Meaning |
|---|---|---|
| `install` | string | **Documentation-only — the PRE-FLIGHT engine NEVER reads or executes this string.** It exists solely as a human-readable reference showing what the auto-installer will do. The engine builds its argv from the structured `{manager, package, version}` fields above. |
| `verify` | string | **Documentation-only — NEVER executed** (e.g. `expo --version`, `python -c "import docx"`). A human-readable note of how presence is conceptually checked; the engine checks presence ONLY via the structured `verifyImport` above. A freeform shell `verify` that was executed would be an arbitrary-command-execution path bypassing the registry/grammar/SCA guards — so it is demoted exactly like `install` (the RCE fix). This structural separation kills the `curl\|bash` / untrusted-source injection class for BOTH install and verify: there is no freeform string for an attacker to hijack (LD2/LD3, DESIGN §3). |

## Freeze approval hash (H2 / LD8)

At **FREEZE**, `kata-freeze` records the SHA-256 of `kata.dependencies.json` as the
**freeze approval hash** in a **distinct artifact** — **not** beside
`kata.dependencies.json`. The canonical default path is
`kata.freeze-approval.json` at the **repo root** (not under `.kata/`; JSON:
`{ "manifestHash": "<sha256-hex>" }`). The `approved_hash_path` parameter to
`run_preflight` overrides this default; operators may point it at a committed or
access-controlled location for stronger guarantees.

At **PRE-FLIGHT**, the engine recomputes the hash and compares it to the approved value:
- **Match** → the manifest is as approved; auto-install may proceed.
- **Mismatch** → the manifest changed after freeze approval ⇒ `blocked` + escalate
  (`human-required`) ⇒ re-freeze. **Never silently installs a post-approval edit.**

**What this mechanism delivers:** it **detects post-freeze manifest drift** — the loop
cannot silently change what it installs without triggering a mismatch. The engine
**fails closed** on a missing or mismatched approval artifact. It is **not** a defense
against a local actor who controls both the manifest and the approval file (they own
the machine). For stronger guarantees, point `approved_hash_path` at a committed or
access-controlled location that is not writable by the same author as the manifest.

## Pre-flight gate (summary — full procedure in `kata-preflight`, Spec D)
enumerate → freeze+approve (set + sources) → **record approval hash in distinct artifact (H2)** →
check presence (structured `verifyImport`) → Snyk SCA scan if `scan_required` (fail-closed; strict-True) →
**build argv from structured fields (manager/package/version) — never the freeform `install` string** →
install via `subprocess(argv, shell=False)` forced to an allowed registry → re-check `verifyImport`
(default-FAIL) →
append to the machine-global installed-library registry (`~/.kata/installed-registry.json`, D-registry) →
signal loop-ready.
Never auto-uninstall; the cleanup report (reference-counted across projects) recommends, the human executes.
