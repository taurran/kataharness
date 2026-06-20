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
| `delivery` | `{ shape: "one-shot"\|"incremental", boundary: "always-stop"\|"auto-continue-while-green", backend?: <engram pointer> }` | The **third orthogonal axis** (D78, sprint-cadence): cadence of the build. Default `shape: "one-shot"` (D25 absent ⇒ today's behavior exactly, BC1) · `boundary: "always-stop"` (control-first, GB6). `backend?` = the optional boundary CONSULT seam (E2/E19, no-op if absent). Composes with every other axis; it is **not** a run-shape and **not** a module. See *Delivery axis* + *Prime-frame sizing* below. |
| `engram` | `{ backend?: string, learnFeed?: { dir: string }, autonomy?: "always-human"\|"assisted"\|"auto-when-confident" }` | Optional cognitive-fingerprint config (`protocol/engram.md`). **`learnFeed.dir`** = the **LEARN-only feed** (β) emit target; absent ⇒ **no emit** (no-op, BC1). **`backend`** = the CONSULT backend (gated/off today, D9/D56) — **distinct from `learnFeed`**: the feed is active now, CONSULT is not. **`autonomy`** = the promotion-autonomy AND-gate (loop-cognition L6); default **`always-human`** (D25-safe); per-seam overridable; gated on a mature engram. Read by `kata-promote`; the grounding gate (D33) is never bypassed at any level. |
| `agentSkills` | `{ dir: string }` | The **agent-skills toolkit** root (first-run-configured, loop-cognition L5). `<dir>/candidates/` holds sandboxed agent-distilled candidates; `kata-promote` moves promoted skills into `<dir>/skills/<category>/`. **Outside this repo's `skills/` tree** — the validator never scans it. Absent ⇒ no agent-distilled skills persist (no-op). |

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

## Delivery axis (D78 — sprint-cadence)
`delivery` selects the build **cadence** — one continuous run, or gated reviewable increments (sprints). It is a
third orthogonal axis composing with `mode` × `effort` × `modules` (D78); the unit of an incremental run is a
**sprint** (each sprint is itself a one-shot; the boundary between sprints is the only place steering happens).

| Field | Values | Default | Meaning |
|---|---|---|---|
| `delivery.shape` | `one-shot` \| `incremental` | **`one-shot`** | `one-shot` = today's loop, byte-for-byte (D25/BC1). `incremental` = partition into sprints via the `kata-plan` roadmap layer; `kata-sprint` owns the boundary. |
| `delivery.boundary` | `always-stop` \| `auto-continue-while-green` | **`always-stop`** | Control-first (GB6). `always-stop` = every boundary hard-stops for the human (G1). `auto-continue-while-green` = continue **only** while {green ∧ no escalations ∧ no pending corrections ∧ no G3 tertiary drift} all hold (an AND-gate; the moment any is false ⇒ stop). |
| `delivery.backend?` | engram pointer | absent | Optional boundary CONSULT seam (E2/E19); no-op when absent (gated like all CONSULT, D9/D56). |

- **Preset pre-fill (GB4/D46):** `individual` ⇒ one-shot · `version-up` ⇒ **ask** · `batch` ⇒ one-shot.
- **Fail-closed (D45):** the load-guard validates `delivery` strictly — a malformed value ⇒ **stop + escalate,
  never guess**. Absent ⇒ one-shot (BC1). `kata-orchestrate` stays **sprint-blind** (BC2): delivery-awareness
  lives only in HANDOFF-phase routing (one-shot → `kata-handoff`/`kata-selfhandoff`; incremental → `kata-sprint`).

## Prime-frame sizing (D83 — supersedes D8's threshold clause)
The **prime frame** = a model's *recommended effective working band* — the span below the degradation zone, with
headroom reserved. It is an **agnostic fraction/policy; the adapter resolves it to real tokens per model** (D59).
It is the *single* primitive that both **sizes sprints** (`kata-plan` roadmap layer) and **sets the one-shot
self-handoff/refresh threshold** (`kata-selfhandoff`) — same primitive, two policies.

- **Default `[TUNABLE]` fraction ≈ 0.40 of the model's advertised window** (restart ceiling ≈ 0.48). Grounded at
  build (2026-06-19, WebSearch) against real model facts — **do not pin from memory**: Fable 5 / Opus 4.8 /
  Sonnet 4.6 all advertise a **1M-token** window, but reliable retrieval holds to ~200–256K and self-reported
  degradation begins ≈40% / restart-recommended ≈48% utilization. So the effective working band on a 1M model is
  ≈400K. These numbers are **tunable and model-specific**; the architecture is number-independent.
- **Floor:** a candidate sprint that already fits within **one** prime frame ⇒ refuse to sprint, recommend
  one-shot. **Ceiling:** a sprint whose context demand **exceeds** one prime frame ⇒ split. Max sprint count =
  `⌈project context demand ÷ prime frame⌉`, no arbitrary cap.
- **B1 (D83):** the one-shot self-handoff/refresh threshold changes from D8's user-set % → this model-resolved
  prime-frame fraction. **D8's principles survive** (anti-over-conservative; task-boundary-preferred).

## Notes
- Tier resolution: `kata-orchestrate` maps a bare family reference (`[[kata-grill]]`) → `tiers["kata-grill"]`
  → e.g. `kata-grill-standard` (D26). `tiers["kata-grill"] == "skip"` ⇒ no grill dispatch + engage the floor
  (above). Absent config ⇒ Standard (D25).
- `kata.config` is never tiered or mode-specific in *format* — one schema, all modes (consistency, D18).
- `runShape` is provenance only: the bootstrap preset (GB1) pre-fills `mode`+`modules`; orchestrate dispatches
  off `mode`/`modules`/`tiers`, not off `runShape`. `target.kind: "existing"` (version-up) supplies the
  `baselineGate` that `kata-orchestrate` precondition #2 records as the regression baseline. The version-up
  *execution* path (kata-graph ingestion) is Spec A4; A3 only writes/validates the config.
