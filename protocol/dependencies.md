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
maps `manager` → a fixed argv builder (like `kata_dispatch._COMMAND_BUILDERS`,
`tools/kata_dispatch.py:150`) and forces the registry/index from `preflight.allowed_registries`.
No freeform string is ever executed.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `manager` | `"pip" \| "uv" \| "npm" \| "cargo"` | **yes** | The package manager. Must be in `preflight.allowed_registries` **and** in the engine's hard `ALLOWED_MANAGERS` allowlist (`tools/kata_preflight.py`). Any `manager` not in both lists ⇒ `blocked`, nothing executed. |
| `package` | string | **yes** | Package/crate/npm name. Charset-validated (alphanumeric + `.-_/@:+`). A value starting with `-` is **rejected** (flag-injection guard H1). |
| `version` | string | **yes** | Pinned version string (honor `preflight.pin_policy`). Same charset/leading-dash validation as `package`. |
| `index` | string | no | Optional override label (e.g. `"pypi"`, `"npmjs"`). **Informational only** — the engine **forces** the actual registry URL from `preflight.allowed_registries`; a manifest-supplied URL is never used. |
| `verify` | string | recommended | A runnable shell command proving presence (e.g. `expo --version`, `python -c "import docx"`). PRE-FLIGHT is **default-FAIL** on this: a dep that won't verify after provisioning ⇒ `blocked`. |

### Docs-only field (NEVER executed)

| Field | Type | Meaning |
|---|---|---|
| `install` | string | **Documentation-only — the PRE-FLIGHT engine NEVER reads or executes this string.** It exists solely as a human-readable reference showing what the auto-installer will do. The engine builds its argv from the structured `{manager, package, version}` fields above. This structural separation kills the `curl\|bash` / untrusted-registry injection class: there is no freeform string for an attacker to hijack (LD2/LD3, DESIGN §3). |

## Freeze approval hash (H2 / LD8)

At **FREEZE**, `kata-freeze` records the SHA-256 of `kata.dependencies.json` as the
**freeze approval hash** in a **distinct committed artifact** — **not** beside
`kata.dependencies.json`. The canonical default path is
`.kata/kata.freeze-approval.json` (JSON: `{ "manifestHash": "<sha256-hex>" }`),
committed at freeze, on a separate branch or in a protected location so it cannot be
trivially overwritten by the same author who edits the manifest.

At **PRE-FLIGHT**, the engine recomputes the hash and compares it to the approved value:
- **Match** → the manifest is as approved; auto-install may proceed.
- **Mismatch** → the manifest changed after approval ⇒ `blocked` + escalate
  (`human-required`) ⇒ re-freeze. **Never silently installs a post-approval edit.**

This tamper-resistance only holds if the approval artifact and the manifest are not
equally writable (i.e. not co-located in the same uncommitted working-branch file).
Store them separately (H2 hardening note from DESIGN §8).

## Pre-flight gate (summary — full procedure in `kata-preflight`, Spec D)
enumerate → freeze+approve (set + sources) → **record approval hash in distinct artifact (H2)** →
check presence (`verify`) → Snyk SCA scan if `scan_required` → **build argv from structured fields
(manager/package/version) — never the freeform `install` string** → install via
`subprocess(argv, shell=False)` forced to an allowed registry → re-`verify` (default-FAIL) →
append to the machine-global installed-library registry (`~/.kata/installed-registry.json`, D-registry) →
signal loop-ready.
Never auto-uninstall; the cleanup report (reference-counted across projects) recommends, the human executes.
