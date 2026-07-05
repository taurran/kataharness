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
| `benchmark` | `{ profile: "balanced"\|"cost-lean"\|"quality-strict", k_repeats: int, repeat_from?: string, def_out: string, rate_table?: object }` | Benchmark config (ignored unless `kata/module/benchmark` is in `modules`; absent ⇒ silent no-op, BC). `profile` sets the Axis Q × Axis C composite weight (default `"balanced"`). `k_repeats` = sequential repeats per arm (default `1` — n=1 directional); one arm-map entry per `<arm>·repeat<k>`. `repeat_from` = location (path / registry id) of a prior `benchmark.def.json` to mirror — activates delta mode. `def_out` = durable path for the new `benchmark.def.json` (outside `.kata/`; required when the module is active). `rate_table?` (optional) = per-run cost-rate override table for Axis C; absent ⇒ `usage_meter.default_rate_table()`. *[A5 2026-06-29]* |
| `skillVersions` | `{ "<skill>": "<semver>" }` | The exact skill versions this branch was built with (reproducibility). |
| `runShape` | `"individual" \| "batch" \| "version-up" \| "advanced" \| "debug"` | The preset chosen at bootstrap (GB1) — provenance; presets pre-fill `mode`+`modules`. |
| `target` | `{ kind: "greenfield" \| "existing", path?: string, baselineGate?: string }` | `greenfield` (default) or `existing` (version-up): `path` = existing repo, `baselineGate` = the command that must be green before *and* after (the regression baseline). |
| `graph` | `{ budget: int, marginDepth: int, backend: "tree-sitter"\|"grep-reduced"\|"graphify" }` | `kata-graph` tunables: digest token budget (default 3000), ownership reverse-dependent hop depth (default 1), backend selection. |
| `delivery` | `{ shape: "one-shot"\|"incremental", boundary: "always-stop"\|"auto-continue-while-green", backend?: <engram pointer> }` | The **third orthogonal axis** (D78, sprint-cadence): cadence of the build. Default `shape: "one-shot"` (D25 absent ⇒ today's behavior exactly, BC1) · `boundary: "always-stop"` (control-first, GB6). `backend?` = the optional boundary CONSULT seam (E2/E19, no-op if absent). Composes with every other axis; it is **not** a run-shape and **not** a module. See *Delivery axis* + *Prime-frame sizing* below. |
| `engram` | `{ backend?: string, learnFeed?: { dir: string }, autonomy?: "always-human"\|"assisted"\|"auto-when-confident" }` | Optional cognitive-fingerprint config (`protocol/engram.md`). **`learnFeed.dir`** = the **LEARN-only feed** (β) emit target; absent ⇒ **no emit** (no-op, BC1). **`backend`** = the CONSULT backend (gated/off today, D9/D56) — **distinct from `learnFeed`**: the feed is active now, CONSULT is not. **`autonomy`** = the promotion-autonomy AND-gate (loop-cognition L6); default **`always-human`** (D25-safe); per-seam overridable; gated on a mature engram. Read by `kata-promote`; the grounding gate (D33) is never bypassed at any level. |
| `agentSkills` | `{ dir: string }` | The **agent-skills toolkit** root (first-run-configured, loop-cognition L5). `<dir>/candidates/` holds sandboxed agent-distilled candidates; `kata-promote` moves promoted skills into `<dir>/skills/<category>/`. **Outside this repo's `skills/` tree** — the validator never scans it. Absent ⇒ no agent-distilled skills persist (no-op). |
| `models` | `{ anchor: "session"\|"<id>", family: "auto"\|"<fam>", coderFloor: "sonnet", policyOverride?: {…} }` | Relative-tiering anchor block (DESIGN §2, R3/R7): supplies the three resolver inputs (`anchor`/`family`/`coder_floor`) consumed by `kata_models.resolve()`. **Absent ⇒ `resolve()` returns `None` everywhere ⇒ inherit by omission ⇒ today's single-model behavior, byte-for-byte (R3, BC1).** See *`models` block* below. |
| `livenessDeadline` | minutes (int) | F3 dark-worker detection (a **dispatch/execution** concern, NOT sprint/delivery — read by the sprint-blind orchestrator's liveness monitor): a worker with a `CLAIM` but no `DONE` whose most recent `CLAIM`/`PROGRESS` line is older than this is *stale* → nudge → escalate (`kind: human-required`) → human-approved re-dispatch (never a blind kill). Default `10`; absent ⇒ 10 min. (Honest-BC note: the monitor itself is NEW behavior for existing configs — parse-level BC only; it is non-blocking, a missing PROGRESS never gates a task.) |
| `securityScan` | `"required" \| "when-available" \| "off"` | First-party-code security-scan posture for the green gate (Lever 2 / F6) — **tool-agnostic** (the gate never names a scanner). `required` = fail-closed: no clean scan AND no documented-acceptance ⇒ NEEDS_WORK. `when-available` = run if a scanner is wired AND the toolchain is supported, else `degraded` + **surfaced** (never a silent skip, never a toolchain-shim fight). `off` = operator opt-out, surfaced at handoff. **Absent ⇒ `when-available` (today's behavior — run the scan when possible, never block a run for a missing/unsupported scanner; BC).** Distinct from `preflight.scan_required` (gates dependency INSTALLS via SCA) and from the debug-mode / IaC Snyk wirings (unchanged, named integrations). A finding that cannot converge to zero → harden → document acceptance in-repo (`.snyk` reason+expiry) → board DECISION → the evaluator grades acceptance **soundness**, not raw count. |
| `inlineEval` | `"off" \| "telemetry" \| "on"` **or** `{ mode, tau?, weights? }` | Freeze/Float **M4 inline-evaluator posture** (M4-L8/M4-L10). Validated mechanically by `kata_telemetry.validate_inline_eval`. **Absent ⇒ `off` — byte-for-byte today's behavior** (no checkpoint mandate enters any worker brief, no telemetry artifact is written; BC1). A **present-but-malformed** value (case-variant, wrong type, unknown string) ⇒ **load-guard STOP + escalate** (D45/GB12 — never a silent coercion to `"off"`). `telemetry` = **record-only**: adds the per-chunk worker **checkpoint-commit + `Kata-Checkpoint:` trailer mandate** to the dispatch brief and records signal vectors + a per-run calibration ledger row — it changes **no scheduling, gating, or recovery** behavior (NO risk score, NO τ, NO trigger, NO ladder, NO kill — all P1; the record mandate's cost is precisely what P0's <1% instrument measures). `on` = the P1 **consuming** mode, **now LIVE (M4-P1)**: the checkpoint mandate applies (mode ≠ `off`) **AND the scheduler + corrective-action ladder + reroll/kill now consume the checkpoint stream** — see `kata-orchestrate` → *The M4 scheduler* + *The corrective-action ladder* (the inline evaluator runs strictly below the anchor via the D131 resolver; on resolver-`None` / R2-chain-exhaustion / a missing per-platform kill binding it **degrades to `telemetry` — surfaced, never silent**). **Object form (M4-P1 — ADDITIVE; BC: the string form above stays valid, byte-for-byte):** `inlineEval` may instead be `{ mode: "off"|"telemetry"|"on", tau?: {class: float}, weights?: {signal: float} }` — the `mode` sub-key is **REQUIRED** (a mode-less object is the classic hand-edit error ⇒ **load-guard STOP + escalate**, never a silent `off`; re-gate v2 HIGH-1), and optional `tau`/`weights` override the A1-Q4 defaults, resolved+validated by `kata_risk.resolve_inline_eval_params` **against the `inlineEval` VALUE object (never the whole `kata.config` — re-gate v2 MED-2)**; a present-but-malformed override (non-numeric, unknown class/signal key, τ outside `(0, 1]`) ⇒ **load-guard STOP** (D45/GB12, the same posture as the malformed string value above). *(The per-task slack `estimate:` is **not** a `kata.config` field — it homes in the plan frontmatter, authored + freeze-validated per `kata-plan`'s RUBRIC; `kata_telemetry.resolve_estimate` is the runtime backstop.)* |
| `roles` | `{ "<role>": { platform: string, model?: string, effort?: string } }` | **Multi-model routing (D105, spec multi-model-orchestration) — wired**: resolved + validated **fail-closed at preflight** via `kata_roles.resolve_roles` — unknown role / unconfirmed platform / **a host-only role (`orchestrator`\|`evaluator`, `kata_roles.HOST_ONLY_ROLES`, LD11) routed off-host** ⇒ **STOP + escalate** (the host-only constraint is code-enforced, not advisory). Routes a loop **role** (`coder`\|`validator`\|`researcher`\|`orchestrator`\|`evaluator`) to a platform/model. **Absent ⇒ every role on the host platform (BC1, single-model — today's behavior).** A role assigned to a non-host platform must name a platform in `.kata-settings.json` `confirmedPlatforms`. |
| `iac` | `{ severityThreshold?: "low"\|"medium"\|"high"\|"critical", escalateMedium?: bool, extraScanners?: string[], forceClassify?: { "<path/glob>": "<kind>" } }` | Optional IaC-gate tunables (N4, DESIGN §5). **Absent ⇒ defaults: Snyk primary, `high`/`critical` fail, fail-closed if scanner unwired.** **Detection-activated** (IAC-3) — fires when `iac_detect.classify_task` finds IaC in a task's owned files; **NOT a `modules` opt-in** (BC: adding this field changes thresholds only, never silently enables the gate on non-IaC tasks). `severityThreshold` sets the lowest severity that causes a gate `fail` (default `"high"`). `escalateMedium` when `true` promotes `medium` findings on non-sensitive resources from `fail` to `escalate` (default `false` — medium on non-sensitive resources enters the fix loop). `extraScanners` — **reserved/not-yet-consumed**: lists optional add-on scanner names (Checkov, cfn-guard); v1 wires **only Snyk** as the authoritative gate, so this field is documented for forward-compat but has no effect today. `forceClassify` overrides automatic detection for specific paths/globs (e.g. `{"infra/**/*.yaml": "cloudformation"}`) — **wired**: passed to `iac_detect.classify_task` at dispatch (a matched override wins over auto-detection), the documented mitigation for the MAJOR-5 silent-bypass gap (`protocol/iac-safety.md §1`). **Note (no silent off-switch):** raising `severityThreshold` above `high` weakens misconfig gating — the scanner-absent FAIL is threshold-independent, but operators should treat a threshold above `high` as requiring recorded acceptance. |
| `contextAutonomy` | `"on" \| "off"` | Auto-context rotation for **incremental** shapes only (CA-L32); the load-guard validates it mechanically via `kata_gauge.validate_context_autonomy` (absent ⇒ `"off"`; exactly `"on"`/`"off"` ⇒ itself; anything else ⇒ RAISE). One-shot shapes **never consult it** — rotation is **unconditional** there (CA-L33/D147), **the ONE deliberate BC departure of this initiative** (§4 row 1: pre-v0.2.1 one-shot configs rotate too — protective + additive, always mandated by the selfhandoff prose but never wired; degradation stays graceful). Bootstrap Phase 3 writes `"on"`. **Absent-at-load ⇒ OFF on the key-consulted path** (BC). Malformed ⇒ load-guard STOP + escalate (D45/GB12, the delivery-field posture). |
| `contextTrigger` | number (0–1) | The conductor **trigger fraction** override; default **0.70** `[TUNABLE]` when absent (CA-L7). Shown only in bootstrap's advanced drawer; **never interactively asked** (no new dial, K5). Consulted only where rotation is active. Names the B1 one-shot self-handoff threshold source (CA-L8; see *Prime-frame sizing* below), distinct from and leaving unchanged the 0.40 sprint-sizing fraction. *(Key NAME is this DESIGN's compilation choice — structure locked, name freeze-gate-attackable.)* |
| `models.premium` | `{ offer: "fable", approved: bool, scope: ["critical","coding"] \| { events: string[], budget?: { calls: int, tokensOut?: int } }, grantedMode: "advanced" }` | The premium-offer record (CA-L28..L31; model-tiering §3 Amendment #1 + **Amendment #2/D150**). Written by bootstrap after the preflight gate; consumed by `kata_models.resolve()`'s four-conjunct premium branch (NO-FIRE reason surfaced via `premium_status`). **`scope` is TYPE-DISPATCHED (AT-L15):** a LIST ⇒ the v0.2.1 run-long work-class semantics byte-for-byte; an OBJECT ⇒ the ADAPTIVE form — conjunct #2 reads "event ∈ scope.events" (the 7-event hard-moments registry, `kata_models.ADAPTIVE_EVENTS`), spend capped by `budget.calls` (default 10; last 2 reserved for freeze-gate events; exhaustion ⇒ LOUD lapse to the anchor, CA-L30 discipline). Absent `events` key in the object form ⇒ load RAISE; explicit `[]` ⇒ legal no-op. **Absent `premium` ⇒ the resolver's frozen behavior byte-for-byte** (§4 row 4). `grantedMode` ≠ current `mode` at re-entrant bootstrap ⇒ `approved` cleared (lapse). Economy is structurally excluded from premium in BOTH forms (R-9). |
| `models.adaptive` | `{ failBumpAt?: 2, streakDownAt?: 3, planComplexityDownshift?: bool, evaluatorEscalate?: bool, l2?: false }` | The **adaptive-tiering L1/L2 switchboard** (D150, adaptive-tiering DESIGN §3; resolved by `kata_adaptive.resolve_adaptive_config`). **ABSENT ⇒ EVERY adaptive leg OFF** (load-time BC — no retroactive flip, the D147/CA-L34 discipline); **block PRESENT = consent** — absent keys inside a present block take the defaults shown (pinned per-key semantics). Bootstrap writes the full block explicitly at its next COMPOSITION (compose = consent — the operator's bake-it-in arm). `failBumpAt` (F): gate rejections + STANDING rerolls before the one-per-task rung bump. `streakDownAt` (K): consecutive first-pass acceptances before a `coding`-class downshift (×2 damper on a downshift-attributed rejection). `l2`: ledger acceptance-routing activation — **default OFF, named-deferred until post-R6 ledger volume** (AT-L19). Malformed ⇒ load-guard RAISE (D45/GB12). Every adaptive move is a board `tier:` DECISION line (the durable recount trail). Mid-run `/model` switch ⇒ adaptive state reset, budget spend preserved (AT-L17b). |

### `preflight` block (D29)
| Field | Type | Meaning |
|---|---|---|
| `allowed_registries` | `string[]` | Trusted install sources (e.g. `["npm","pypi","uv","cargo"]`). Anything outside requires an explicit approved override. **(engine-enforced)** |
| `pin_policy` | `"exact" \| "compatible"` | Version-pinning strictness; `"exact"` for determinism (L1). **Advisory/reserved** — not yet read by the engine; pinning is enforced structurally by requiring a `version` field. |
| `scan_required` | `bool` | Gate installs on a Snyk SCA scan (default `true`). Fail-closed: `true` + no scanner wired ⇒ `blocked`. **(engine-enforced)** |
| `approval_mode` | `"approve-at-freeze" \| "ask-each"` | When the human approves the dependency set. Default `"approve-at-freeze"`. **Advisory/reserved** — the engine provisions the freeze-approved (hash-matched) set; this field documents intent but is not yet a branch in the engine. |
| `sandbox_required` | `bool` | Require the loop to run in an isolated/disposable environment (container/devcontainer). **(engine-enforced)** |

### `models` block (DESIGN §2 — relative-tiering anchor, R3/R7)
| Field | Type | Meaning |
|---|---|---|
| `anchor` | `"session" \| "<id>"` | The operator's **session model** — the reference rung for all relative tier arithmetic. `"session"` defers to the platform's latest top rung at dispatch (default when the field is absent from the block); an explicit id — either a short-name (e.g. `"opus"`) or a full model id (e.g. `"claude-opus-4-8"`) — is accepted; a full model id is normalized to its ladder short-name by the resolver before any rung arithmetic. Written once per branch by `kata-bootstrap`/`kata-initiate` (R7, Layer 3). Passed as the `anchor` argument to `resolve()`. Read only by **below-anchor cells** (economy tier-down + `essential-critical = anchor−1`) — zero-step critical work inherits by omission and never reads the anchor name. |
| `family` | `"auto" \| "<fam>"` | The ladder family for rung resolution. `"auto"` derives the family by exact-matching the anchor short-name against each family ladder (after `_normalize_anchor` maps a full model id to its short-name); `"<fam>"` names the family explicitly (e.g. `"anthropic"`). Passed as the `family` argument to `resolve()`. An unknown or undetectable family → `resolve()` returns `None` (inherit by omission — safe fallback, never a crash). |
| `coderFloor` | string (rung name) | The **R1 coder-floor rung** — the minimum rung enforced for `coding` work-class dispatches (R1 invariant: `essential-coding ≤ standard-coding ≤ anchor`). Default `"sonnet"`. Passed as the `coder_floor` argument to `resolve()`. Applied raise-only: the floor raises a coding dispatch up when the raw step-down would land below it; it never exceeds standard's rung and never exceeds the anchor. |
| `policyOverride?` | `object` | **Flagged — present in DESIGN §2 block; no corresponding input in `resolve(skill, mode, anchor, *, family, coder_floor)`.** The resolver does not consume this field. Semantics are not yet specified; do not invent behavior. Documented here for config-load provenance and forward-compat only. |

**BC guarantee (R3):** **Absent the `models` block ⇒ `resolve()` returns `None` everywhere ⇒ inherit by omission ⇒ today's single-model behavior, byte-for-byte.** No `models` block = zero resolver involvement: the host picks its own model (the operator's session model) as if model selection never happened. This guarantee is structural — any future extension to this block is additive; the absent-block path never changes.

**Anchor and critical work (R7):** Zero-step critical work (advanced-critical + standard-critical; resolved rung `== anchor_index`) resolves to `None`/OMIT regardless — it **needs no anchor detection** and inherits by omission (always current, immune to a gated top rung and immune to a stale anchor). Only **below-anchor cells** read the anchor name to compute a rung: economy tier-down (`standard-coding`, `standard-economy`, `advanced-economy` *(Anthropic, `−1`)*, all `essential` work). An **unknown anchor** (id not found in the family ladder) → `resolve()` returns `None` → inherit — never a crash, never a forced model.

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

- **Preset pre-fill (GB4/D46):** `individual` ⇒ one-shot · `version-up` ⇒ **ask** · `debug` ⇒ **ask** · `batch` ⇒ one-shot.
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
- **Floor:** if the **whole project** already fits within **one** prime frame ⇒ refuse to sprint, recommend
  one-shot (sprinting buys nothing; the boundary ceremony is pure overhead). **Ceiling:** a single sprint whose
  context demand **exceeds** one prime frame ⇒ split it at the next seam. Max sprint count =
  `⌈project context demand ÷ prime frame⌉`, no arbitrary cap.
- **B1 (D83):** the one-shot self-handoff/refresh threshold changes from D8's user-set % → this model-resolved
  prime-frame fraction. **D8's principles survive** (anti-over-conservative; task-boundary-preferred).
- **Context-autonomy amendment (context-autonomy spec, CA-L8):** the B1 self-handoff/refresh threshold *source*
  is the context-autonomy **trigger fraction** — `contextTrigger` (default **0.70** of the host-reported effective
  window, CA-L7) — while this section's **0.40** sprint-sizing fraction above stays the sprint-sizing fraction,
  byte-unchanged (D83 is *not* edited; supersede-never-rewrite — one primitive lineage, two policies).

## Optional modules

Optional modules are à-la-carte additions to the `modules` array in `kata.config`. Each module has a
**provider skill** and is **off by default unless noted** (opt-in, control-first, GB6). A module key in
`modules` with no matching provider ⇒ `kata-orchestrate` load-guard STOP + escalate (fail-closed, D45).

| Module key | Provider skill | Default | Description |
|---|---|---|---|
| `kata/module/slop` | `kata-slop-check` | **off** (opt-in) | AI-slop / spiraling-session detection; dispatched in EVALUATE alongside kata-evaluate; a SLOP-DETECTED verdict is default-FAIL. |
| `kata/module/debug` | `kata-comprehend` | **off** (opt-in) | Pre-change whole-repo comprehension for the `debug` run-shape; orchestrate's comprehension phase invokes `[[kata-comprehend]]` iff this module is present — absent ⇒ silent no-op (BC: no effect on version-up or greenfield runs). |
| `kata/module/benchmark` | `kata-benchmark-report` | **off** (opt-in) | Two-axis scorecard + two-tier report for the benchmark path. Dispatched at benchmark closeout (after the frontier drains and gate artifacts are emitted). **Never gates** — reports only; `kata-evaluate` is the exclusive gate. `kata-orchestrate` wires: control clone (S4 `benchmark_control.clone_control`), usage write (S1 `usage_meter.write_usage`), scorer (S2 `benchmark.score_arms`/`emit_scorecard`), report dispatch (S5 `kata-benchmark-report`). Absent ⇒ silent no-op, zero overhead (BC). Load-guard: a `kata/module/benchmark` entry with no provider skill ⇒ `kata-orchestrate` load-guard STOP + escalate (fail-closed, D45). |

## Notes
- Tier resolution: `kata-orchestrate` maps a bare family reference (`[[kata-grill]]`) → `tiers["kata-grill"]`
  → e.g. `kata-grill-standard` (D26). `tiers["kata-grill"] == "skip"` ⇒ no grill dispatch + engage the floor
  (above). Absent config ⇒ Standard (D25).
- `kata.config` is never tiered or mode-specific in *format* — one schema, all modes (consistency, D18).
- `runShape` is provenance only: the bootstrap preset (GB1) pre-fills `mode`+`modules`; orchestrate dispatches
  off `mode`/`modules`/`tiers`, not off `runShape`. `target.kind: "existing"` (version-up) supplies the
  `baselineGate` that `kata-orchestrate`'s **green-at-fork-point** precondition records as the regression
  baseline. The version-up
  *execution* path (kata-graph ingestion) is Spec A4; A3 only writes/validates the config.
- `runShape: "debug"` is a peer of `version-up` (`target.kind: "existing"`); **gated by the `kata/module/debug` module, NOT by `runShape`** — orchestrate dispatches off `mode`/`modules` per existing rules; `runShape` stays provenance-only. The `debug` preset pre-fills `kata/module/debug` in `modules`; the comprehension phase fires IFF that module is present.
