# protocol/config.md — the `kata.config` schema

> Per-branch provenance written by `kata-bootstrap` (Spec A3) and read by `kata-orchestrate` (D24d). It is
> machine-coordination state — JSON, not vault-managed (STANDARDS §5). It is the reproducibility backbone:
> what makes escalation (Spec C) and bake-off (Spec B) comparable.

## Location
`kata.config` (JSON) at the working-branch root. Absent ⇒ orchestrator assumes **Standard** (D25).

## Schema
| Field | Type | Meaning |
|---|---|---|
| `mode` | `"essential" \| "standard" \| "advanced"` | The unified tier+module axis (D24a). Default `"standard"` (D25). |
| `modules` | `string[]` | Active à-la-carte modules beyond the mode's bundle (D20): e.g. `["quality","design","bakeoff","improve"]`. |
| `effort` | `{ model: string, reasoning: "medium"\|"high"\|"xhigh"\|"max" }` | Orthogonal effort overlay (D19); set independently of `mode`. |
| `tiers` | `{ "<family>": "<tier>" }` | Resolved tier per tiered family (`kata-grill`/`kata-review`/`kata-plan` → essential\|standard\|advanced; `kata-diagnose` → light\|full). Lets bootstrap override a single family (D24c cross-tier picking) without changing `mode`. Missing family ⇒ the mode's default tier. |
| `ingested` | `[{ name, slot, source }]` | External/custom skills folded in (D24c): each declares where it slots in the loop. |
| `preflight` | `object` | Dependency pre-flight policy (D29) — see below. |
| `bakeoff` | `{ n: int, lineage: string[] }` | N-variant best-of-N (Spec B). `n: 1` ⇒ no bake-off. `lineage` records parent configs for escalation-with-reuse. |
| `skillVersions` | `{ "<skill>": "<semver>" }` | The exact skill versions this branch was built with (reproducibility). |

### `preflight` block (D29)
| Field | Type | Meaning |
|---|---|---|
| `allowed_registries` | `string[]` | Trusted install sources (e.g. `["npm","pypi","uv","cargo"]`). Anything outside requires an explicit approved override. |
| `pin_policy` | `"exact" \| "compatible"` | Version-pinning strictness; `"exact"` for determinism (L1). |
| `scan_required` | `bool` | Gate installs on a Snyk SCA scan (default `true`). |
| `approval_mode` | `"approve-at-freeze" \| "ask-each"` | When the human approves the dependency set. Default `"approve-at-freeze"` (the manifest is approved as part of the freeze; pre-flight then provisions unattended). |
| `sandbox_required` | `bool` | Require the loop to run in an isolated/disposable environment (container/devcontainer). |

## Notes
- Tier resolution: `kata-orchestrate` maps a bare family reference (`[[kata-grill]]`) → `tiers["kata-grill"]`
  → e.g. `kata-grill-standard` (D26). Absent config ⇒ Standard (D25).
- `kata.config` is never tiered or mode-specific in *format* — one schema, all modes (consistency, D18).
