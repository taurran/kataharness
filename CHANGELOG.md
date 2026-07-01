# Changelog

All notable changes to KataHarness are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) at the **suite** level. Per-skill
semver is tracked independently in each skill's frontmatter `version` field — see `docs/STANDARDS.md §3`.

---

## [Unreleased]

## [0.1.0] — 2026-06-30

**First public release of the KataHarness agent harness — the single-model Claude core.**

47 skills · 2141 pytest · validate 47/0 · Snyk medium+ 0 · Apache-2.0.

### Core spine

- **10 spine skills** built and field-proven: `kata-grill`, `kata-context`, `kata-design-doc`,
  `kata-plan`, `kata-orchestrate`, `kata-board`, `kata-worktree`, `kata-tdd`, `kata-evaluate`,
  `kata-handoff`. Proof: KataHarness built itself via the loop (dogfood n=1).
- **Frontmatter schema v2** (D26/D31): `name`, `description`, `license`, `version`, `category`,
  `status`, `agnostic`, `cost-weight`, `allowed-tools`, `compatibility`, `source`, `supersedes`,
  `aliases`, `tags`. Model field (`model:`) **FORBIDDEN** in core skills — dispatch-resolved at
  runtime, never pinned in a skill body.
- **`tools/validate_skills.py`** enforcing the schema, cost-weight, license, no-write evaluator
  invariant (`kata-evaluate`/`kata-research` omit Write/Edit), model guard (A1), and
  `REQUIRED_PROTOCOL` registry.

### Modes and tiers (Spec A — A1–A4, D1–D56)

- **Tier families:** `kata-grill` / `kata-review` / `kata-plan` each in three tiers
  (essential / standard / advanced); `kata-diagnose` in two (light / full). RUBRIC per family;
  structural invariants never tiered (D33).
- **`kata-bootstrap`** — run-shape router (individual / batch-bakeoff / version-up / advanced),
  presets on top of the mode axis, cost preview, `kata.config` writer; re-entrant (cold-start vs
  reconfigure). **`kata-readiness`** — harness-health + target-readiness + re-entrant config
  detection (bootstrap-invoked).
- **`kata-graph`** — tree-sitter-floor, feature-agnostic `kata.graph.json` contract, ~3k-token
  feature-seeded digest, pluggable backend. Protocol: `protocol/graph.md`.
- **`kata-orchestrate`** — rolling DAG-frontier dispatch, async park/drain/hard-wait, structured
  escalation payload (`protocol/escalation.md`), fail-closed config load-guard, IaC region,
  multi-model dispatch, Debug Mode seams.
- **Version-up wiring** — grill Phase 0 ingest, footprint-scoped disjoint ownership,
  full-suite-green regression contract (A4).

### Sprint-cadence (D78–D85)

- **`kata-sprint`** (G1–G4 boundary) — sprint-scoped plan freeze, per-sprint immutable
  `PLAN-s<n>`, carry-outs to next sprint.
- **`kata-plan` roadmap layer** (`ROADMAP.md` tier) — sprint-boundary-amendable roadmap above
  the immutable per-sprint plan.
- **`kata-report` v1** — post-loop build-log synthesis.
- Extended: `config.md`, `state.md`, `handoff.md`, `escalation.md`; `kata-selfhandoff`;
  `kata-readiness`; `kata-handoff` all wired for sprint shape. Orchestrate stays sprint-blind (BC).

### Loop-cognition (D60–D77)

- **β LEARN feed** — `kata-improve` emit-only sub-mode (E6 seam): mines DECISIONS/LESSONS/
  GRILL-LEDGERs/REVIEWs into Karpathy-LLM-Wiki synthesis pages (`produced-by: loop`).
  Zero CONSULT; redaction-gated; no-op without `engram.learnFeed.dir`. Protocol: `protocol/engram.md`.
- **Priming-and-Grill (D71/D73):** grill-skip rung (`tiers["kata-grill"]="skip"`); `kata-defer`
  (new module skill — `DEFERRED.md` parking + `ASSUMPTIONS.md` grill-skip log).
- **`kata-research`** — escalation-routed in-loop research subagent (`research-needed` kind);
  fresh-context no-write; grounding gate in `kata-evaluate` + `kata-review` RUBRIC (D33, never
  bypassed); returns `{claim, source, confidence, grounds-to-plan?}`.
- **`kata-orient`** — read-only three-tier launch orientation (stable → context → volatile),
  vertical rollup + `kata-graph` lateral adjacency pointers, task-type-aware, smart-questioning
  routed (answer-inline / research-needed / human-required). `kata-handoff` orientation tie-in.
- **`kata-promote`** — two-stage candidate→human promotion gate (`scope:agent` →
  grounding gate → `AskUserQuestion`); `engram.autonomy` AND-gate (default always-human).
  STANDARDS §1.3 discriminators; candidate lifecycle in `protocol/state.md`.

### User-friendliness (WS-3/4/5)

- **`protocol/persona.md`** — KataHarness voice and register.
- **`protocol/narration.md`** — in-loop narration map; stage names are not exposed; actions
  described in human terms.
- **Reflective goal-mirror intake** in `kata-initiate`; one-dial mode surface in `kata-bootstrap`.
- **Two-tier closeout** (`kata-closeout` + `kata-report`): concise CLI/GUI summary + self-contained
  branded HTML report (`.kata/closeout.html`); goal-anchored by-aspect; what-changed-why leads.
- **Backout** offered at the human gate (`.kata/RESULT.json.baselineSha`, `git reset --hard`,
  human-gated, never autonomous).
- **`kata-slop-check`** — standalone optional module (`kata/module/slop`); general checks G1–G6 +
  MIT-attributed checks; fresh-context no-write; default-FAIL (`SLOP-DETECTED ⇒ NEEDS_WORK`).

### Install / update / overlay / fork (D104, D125–D129)

- **`install.sh`** (`curl|sh`) + **`install.ps1`** (`irm|iex`) + **`uninstall.*`** — wrapping the
  `kata_install.py` engine; idempotent; `KATA_SRC` offline override.
- **`kata_install.py`** headless flags: `--yes`/`--non-interactive`, `--answers-json`, `--json`,
  `--uninstall`, `--target-dir`; semantic exit codes; non-TTY auto-skip.
- **`tools/kata_overlay.py`** — overlay store (`<home>/.kata-overlay/overlay.json`) + frontmatter
  composer (M4); `.kata-overlay-materialized` marker; fail-soft on missing base.
- **`tools/kata_supersede.py`** — resolve/validate shadows; fork > overlay > pristine precedence;
  validate-STOPs-before-materialize; factory-reset un-shadows.
- **`kata-improve` local-adaptation mode** — overlay vs fork by edit-category;
  `improve.allowUpstreamEdit` rail.
- **`tools/kata_version.py`** — `.kata-version` stamp + `.kata-manifest.json` content-hash;
  `is_pristine`/`suite_semver`; `update.sh`/`update.ps1` bootstraps with `--update`,
  `--factory-reset`, `--dry-run`, `--ref`.
- **`kata-onboard`** (v0.2.0) — optional human-gated router stanza into target project's
  `AGENTS.md` (via `tools/kata_router.py`; `<!-- kata:begin -->`/`<!-- kata:end -->` idempotent
  marked block).

### Multi-model dispatch (D105–D108, D121)

- **`tools/kata_roles.py`** — relative model tokens (`anchor` / `anchor-1` / `anchor-2`); model
  resolved at dispatch as a differential off the operator's session model; never pinned in skill.
- **`tools/kata_dispatch.py`** — files+CLI dispatch (concurrent background subprocesses);
  `kiro_command` + `codex_command`; `_brief_prompt` capture-model branch; host fallback.
- **5 role groups:** coder · validator · researcher · orchestrator · evaluator
  (read-only validator/researcher routing live; coder-routing + evaluator-thresholds deferred per D108).
- **Codex live-proven (D121):** `--skip-git-repo-check`, `stdin=DEVNULL` fixes; confirm probe
  PASSES on real `codex exec` (`confirmedPlatforms:["codex"]`).

### Model-tiering (D131)

- **`tools/kata_models.py`** — pure-stdlib resolver: `resolve`/`step_down`/`fallback_chain`/
  `family_of`; family ladders DATA registry; `ID_MAP`; `SKILL_WORK_CLASS` (47 skills, 3 work
  classes: critical / coding / economy).
- **`kata_roles.py`** relative tokens wired to `step_down`; `_normalize_anchor` maps full ids.
- **`kata-orchestrate`** dispatch-time model-selection prose + R2 ≤2-then-omit fallback.
- **`kata-bootstrap`/`kata-initiate`** anchor-write of the `models` block.
- A1 model guard (`check_model_in_skill_frontmatter`) in `tools/validate_skills.py`.
- `protocol/config.md` `models` schema. Contract: BC absent config ⇒ inherit by omission.

### Debug Mode (D103, D113–D117)

- **`kata-comprehend`** (P1) — builds executable `function_model` oracle via AST-safe `evaluate_spec`;
  `tools/function_model.py` (`_safe_eval` AST-allowlist, no `eval`/`exec`; `**` removed categorically).
- **`kata-deviate`** (P2a) + **`tools/deviation.py`** — 7-step deviation pipeline (self-consistency
  ≥2/3, corroboration HARD gate, confidence+routing, force-LOW; corroborator objectivity code-enforced).
- **`kata-characterize`** (P2b) + **`tools/drift_gate.py`** — blast-radius characterization; behavioral
  drift gate (green→RED=BLOCK, vanished-baseline-green=BLOCK); AEL orchestrator-owned.
- **`kata-lang-profile`** + 6 language profiles + config specialist (P3 LD10) — injected at dispatch
  by footprint file extensions; prose-only, no new Python.
- **`kata-debrief`** (P3 LD12) + **`tools/debug_report.py`** — confidence map, deviation→fix→
  pinning-test, Snyk before/after; honesty pinned at the engine (behavioral-only + heuristic
  confidence + n=0-live labeled).
- `kata-orchestrate` Debug Mode seams (P1/P2/P3) gated on `kata/module/debug`.
- **`kata-onboard`** (P3 LD13) — first-run/convert-to-loop.
- **`kata-closeout`** Step 3b — debug-gated; offers `kata-debrief`.

### Second-brain Recall (D120)

- **`tools/recall.py`** — pure engine: shape-validated open-vocabulary contract
  (`source`/`backend`/`produced_by` adapter-supplied); files-only adapter (reads
  LESSONS/DECISIONS/prior-INTENT/understand-map/validation-misses); `select_records` (hard
  token-overlap>0 predicate; no embeddings/RAG); always-surface open recurrences; no write path.
- **`protocol/recall.md`** — Recall contract. `kata-initiate` v0.2.0 Phase-1b recall-brief.
- CONSULT decider + write-half deferred (gated on engram maturity, D9/D56).

### IaC specialists (D110, D119)

- **`kata-iac-terraform`** + **`kata-iac-cloudformation`** (Tier 1 + Tier 2).
- **`tools/iac_detect.py`** — classifier + plan/change-set destructive-parsers, fail-closed;
  stateful-set (EFS/SQS/SNS/Kinesis/OpenSearch/Neptune/DocDB/KMS/Secrets/MSK/FSx et al.).
- **Tier 1:** author/review/gate; validate/cfn-lint → `snyk_iac_scan` (default-FAIL; fail-closed
  if unwired) → 8-smell lens → destructive analysis → `.kata/iac.json` → pass/fail/escalate.
- **Tier 2 (preview/approve):** `tools/iac_apply.py` — `plan_hash` (TF binary / CFN full
  describe-change-set), `approval_verdict` (plan-hash-bound), `capability_gate_verdict`
  (self-binding: grant.hash + authorized-set + typed token); `run_apply` = NotImplementedError
  (creds-gated, never auto-applies). `protocol/iac-safety.md` §9.

### Benchmark engine (D123–D124)

- **`kata-loop-benchmark`** + **`kata-benchmark-report`** skills.
- **`tools/benchmark.py`** — 2-axis scorecard (Q: floor-gated dual-gate F2P/P2P + mutation;
  C: tokens/$/wall-clock/etc; host-dependent fields nullable); floor-gated composite (Pareto +
  scalar, efficiency only among floor-passers).
- **`tools/benchmark_def.py`** — content-pinned Benchmark Definition + `repeat_from` + delta mode;
  `delta_identity` (same benchmark_id → `sameDefinition:true`).
- **`tools/benchmark_control.py`** — immutable reference clone (`<base>-katabenchmark<N>`).
- **`tools/usage_meter.py`** — net-new metering (tokens/$/wall-clock).
- Module: `kata/module/benchmark` (off-by-default; not in bootstrap).

### `kata-validate` always-available validation mini-loop (D125)

- `skills/evaluate/kata-validate` — programmatically-callable `validate(payload, target, profile)
  -> Report{passed, findings[]}`; NO freeze/INTENT/`kata.config` required; dual-target (content
  OR agent output); payload-as-data isolation; 4 deterministic-first legs (grounding / review /
  slop / conformance); bounded ≤2 passes; default-FAIL `compute_passed`.
- `tools/validation_report.py` — findings schema, SARIF severity, `render_table`,
  `tripwire_corpus`/`assert_tripwire_flagged`; no exec sink.

### Validation-miss manifest + recurrence hardening (D101, D112, D114, D118)

- **`tools/validation_misses.py`** — schema/validate/append (append-only, CWE-23, non-fatal)/
  read/count_by_class; `passive recurrences`. Protocol: `protocol/validation-misses.md`.
- **`tools/recurrence_detect.py`** — severity-aware threshold (3× distinct runs or 2× for
  BLOCKERs); distinct-run via `run_id`; `detect_from_paths`; `.planning/recurrence-handled.jsonl`
  sidecar. `kata-improve` v0.2.0 auto-draft sub-mode.
- **`protocol/exec-safety.md`** — structured-argv-only contract; sink registry of every
  `subprocess` in `tools/`. **`tools/tests/test_exec_safety.py`** — AST-based CI guard (fails
  on new `shell=True` outside the operator-domain allowlist).

### v0.1 cluster hardening (2026-06-30)

These five items closed the v0.1 gate:

1. **Sprint-cadence D15/A5 fresh-context `kata-review` SHIP** — clears the last pending gate on
   the sprint-cadence milestone.
2. **Wiring-completeness interim pin** — prose pointers in `kata-evaluate` item 9 and `kata-review`
   6(b) marking the full produced-vs-consumed sweep as a post-v0.1 ORCHESTRATOR INTEGRATION-GATE
   step (the full build is scheduled for v0.1.x).
3. **Guard-consistency repo-wide** — `_safe_path` guards unified to `ValueError` across
   `mutation_run`, `grounding_gate`, `escalation`, and `intent_scaffold`.
4. **CWE-23 `.snyk` record** — standing policy entry for the 17-LOW operator-supplies-own-path
   class in `kata_install.py`; below the medium+ gate; accepted as a known item.
5. **Benchmark n=0→n=1 live** — first live benchmark run on a real control fixture (D5).

**Versioning policy change:** STANDARDS §3 flipped from the pre-release hold (all skills held at
`0.1.0`, 2026-06-08 policy) to **bump-on-modify** (mandatory for all skill modifications going
forward).

### Explicitly deferred to v0.1.x

Items #6–#13 and the wiring-completeness full build. See `BACKLOG.md` "Explicitly deferred to
v0.1.x" section for rationale per item.

---

[0.1.0]: https://github.com/taurran/KataHarness/releases/tag/v0.1.0
