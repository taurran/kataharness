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
| Field | Type | Meaning |
|---|---|---|
| `name` | string | The dependency identifier (package/tool/MCP/repo/template name). |
| `type` | `"library" \| "tool" \| "mcp" \| "repo" \| "template" \| "runtime" \| "capability"` | What kind of thing it is. |
| `version` | string | Pinned version / constraint (honor `preflight.pin_policy`). |
| `purpose` | string | Why the build needs it (traceable to a DESIGN requirement). |
| `install` | string | The exact install command (recognized package manager — **never `curl \| bash` from an arbitrary domain**). |
| `verify` | string | A runnable command proving presence (e.g. `expo --version`, `python -c "import docx"`). PRE-FLIGHT is default-FAIL on this. |
| `source` | string | Registry/URL + a short trust note; reviewed by the human at freeze. |
| `hash` | string | Optional integrity hash/checksum for the pinned artifact; verified on install when present. |
| `scope` | `"global" \| "project-local"` | Install scope. Prefer `project-local` + pinned for determinism + easy cleanup (D-registry). |
| `classification` | `"build-time" \| "runtime"` | `runtime` ⇒ must be bundled into the artifact (a packaging task) → its global base copy becomes a cleanup candidate; `build-time` ⇒ removable after the run (D-registry). |

## Pre-flight gate (summary — full procedure in `kata-preflight`, Spec D)
enumerate → freeze+approve (set + sources) → check presence (`verify`) → Snyk SCA scan if `scan_required` →
install (recognized registry, pinned, hash-verified) → re-`verify` (default-FAIL) → append to the
machine-global installed-library registry (`~/.kata/installed-registry.json`, D-registry) → signal loop-ready.
Never auto-uninstall; the cleanup report (reference-counted across projects) recommends, the human executes.
