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
| `effort` | `{ model: string, reasoning: "medium"\|"high"\|"xhigh"\|"max" }` | Orthogonal effort overlay (D19); set independently of `mode`. A3 maps `reasoning` to the host's actual effort enum; these values are indicative, not an API contract. |
| `tiers` | `{ "<family>": "<tier>" }` | Resolved tier per tiered family (`kata-grill` → **`skip`**\|essential\|standard\|advanced; `kata-review`/`kata-plan` → essential\|standard\|advanced; `kata-diagnose` → light\|full). Lets bootstrap override a single family (D24c cross-tier picking) without changing `mode`. Missing family ⇒ the mode's default tier. `tiers["kata-grill"] == "skip"` is the **grill-skip rung** (D71) — see *Grill-depth dial* below. |
| `ingested` | `[{ name, slot, source }]` | External/custom skills folded in (D24c): each declares where it slots in the loop. |
| `preflight` | `object` | Dependency pre-flight policy (D29) — see below. |
| `bakeoff` | `{ n: int, lineage: string[] }` | N-variant best-of-N (Spec B). `n: 1` ⇒ no bake-off. `lineage` records parent configs for escalation-with-reuse. |
| `skillVersions` | `{ "<skill>": "<semver>" }` | The exact skill versions this branch was built with (reproducibility). |
| `runShape` | `"individual" \| "batch" \| "version-up" \| "advanced"` | The preset chosen at bootstrap (GB1) — provenance; presets pre-fill `mode`+`modules`. |
| `target` | `{ kind: "greenfield" \| "existing", path?: string, baselineGate?: string }` | `greenfield` (default) or `existing` (version-up): `path` = existing repo, `baselineGate` = the command that must be green before *and* after (the regression baseline). |
| `graph` | `{ budget: int, marginDepth: int, backend: "tree-sitter"\|"grep-reduced"\|"graphify" }` | `kata-graph` tunables: digest token budget (default 3000), ownership reverse-dependent hop depth (default 1), backend selection. |
| `engram` | `{ backend?: string, learnFeed?: { dir: string } }` | Optional cognitive-fingerprint config (`protocol/engram.md`). **`learnFeed.dir`** = the **LEARN-only feed** (β) emit target; absent ⇒ **no emit** (no-op, BC1). **`backend`** = the CONSULT backend (gated/off today, D9/D56) — **distinct from `learnFeed`**: the feed is active now, CONSULT is not. |

### `preflight` block (D29)
| Field | Type | Meaning |
|---|---|---|
| `allowed_registries` | `string[]` | Trusted install sources (e.g. `["npm","pypi","uv","cargo"]`). Anything outside requires an explicit approved override. |
| `pin_policy` | `"exact" \| "compatible"` | Version-pinning strictness; `"exact"` for determinism (L1). |
| `scan_required` | `bool` | Gate installs on a Snyk SCA scan (default `true`). |
| `approval_mode` | `"approve-at-freeze" \| "ask-each"` | When the human approves the dependency set. Default `"approve-at-freeze"` (the manifest is approved as part of the freeze; pre-flight then provisions unattended). |
| `sandbox_required` | `bool` | Require the loop to run in an isolated/disposable environment (container/devcontainer). |

## Grill-depth dial (D71/D72 — Priming-and-Grill)
Every run starts from a **priming prompt** (the human's original spec). The grill is an **optional human
certainty layer** that interrogates the designer to enrich that prompt into the frozen spec — it adds alignment
certainty *by construction*, it is not benchmarked (L11). It is controlled by `tiers["kata-grill"]`:

| Dial label (human-facing) | `tiers["kata-grill"]` value | Behavior |
|---|---|---|
| **skip** | `"skip"` | **Run no grill skill.** Freeze the priming prompt as-is → the **autonomous-reliability floor**. |
| **light** | `"essential"` | `kata-grill-essential` — one focused pass over top-risk branches. |
| **standard** | `"standard"` | `kata-grill-standard` — the default; full decision-tree grill. |
| **full** | `"advanced"` | `kata-grill-advanced` — exhaustive, production-freeze depth. |

- **The autonomous-reliability floor is always on (every rung).** It is the substrate: **default-FAIL** +
  the **RS research subagent** (in-loop ambiguity resolution — *built in the loop-cognition phase; named here,
  not yet wired*) + an **assumption/ambiguity log surfaced at the gate** (`kata-defer` `ASSUMPTIONS.md`, graded
  by `kata-evaluate` rubric item 8) **and at handoff**. The grill **adds up-front certainty on top of** this
  floor (D71: *"both coexist; grill shores up results on top of a reliable autonomous floor"*) — it never
  replaces it. **`skip`** = lean entirely on the floor (no up-front grill); **light → standard → full** add
  increasing up-front human interrogation, so the floor has progressively fewer autonomous assumptions to make.
  Either way, misalignment is caught at the boundary.
- **Grill ↔ RS are one spectrum:** ambiguity is resolved either **up-front-with-human** (grill) or
  **in-loop-without-human** (RS). Skipping grill *shifts* resolution along the spectrum — it never removes it.
  The default-FAIL `kata-evaluate` gate is **never** skipped on any rung (D22/D33).
- `kata-readiness` recommends a starting dial position from priming-prompt richness/ambiguity; `kata-bootstrap`
  offers it (D46); the human always chooses. Grill ledgers feed the cognitive fingerprint (D72).

## Notes
- Tier resolution: `kata-orchestrate` maps a bare family reference (`[[kata-grill]]`) → `tiers["kata-grill"]`
  → e.g. `kata-grill-standard` (D26). `tiers["kata-grill"] == "skip"` ⇒ no grill dispatch + engage the floor
  (above). Absent config ⇒ Standard (D25).
- `kata.config` is never tiered or mode-specific in *format* — one schema, all modes (consistency, D18).
- `runShape` is provenance only: the bootstrap preset (GB1) pre-fills `mode`+`modules`; orchestrate dispatches
  off `mode`/`modules`/`tiers`, not off `runShape`. `target.kind: "existing"` (version-up) supplies the
  `baselineGate` that `kata-orchestrate` precondition #2 records as the regression baseline. The version-up
  *execution* path (kata-graph ingestion) is Spec A4; A3 only writes/validates the config.
