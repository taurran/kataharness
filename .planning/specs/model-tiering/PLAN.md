---
title: "model-tiering — BUILD PLAN (wave DAG, disjoint ownership, TDD)"
status: FROZEN PLAN (2026-06-30) — derived from DESIGN.md; build order is binding
spec: model-tiering
design: DESIGN.md (this plan implements R1–R8)
waves: W1 (parallel, no cross-deps) → W2 (needs W1 Layer-1) → W3 (docs + decisions + full map)
parallelism: tasks WITHIN a wave have DISJOINT file ownership — no two parallel tasks touch the same file
tags: [plan, frozen, model-tiering, wave-dag, disjoint-ownership, tdd]
---

# model-tiering — BUILD PLAN

Three waves. **W1 is parallel with zero cross-deps** (each task owns a disjoint file set). **W2 needs W1's
Layer-1** (`kata_models.py`). **W3** finalizes docs + decisions + the full work-class map. TDD every task:
failing test first, default-FAIL, no task done until its tests are green and the wave gate passes.

---

## WAVE 1 — foundation (parallel; disjoint ownership)

### W1-A — Resolver core (Layer 1)  ·  OWNS: `tools/kata_models.py`, `tools/tests/test_kata_models.py`
- Implement the pure stdlib resolver (DESIGN §2 L1): family-ladder DATA registry (R4 plain strings; Anthropic IDs
  verified at build), work-class map (seed shape; full 47 fill is W3-B), `resolve(skill, mode, anchor, *, family,
  coder_floor)`, `fallback_chain(id, family)`.
- **R1 coder-floor:** raise a coding tier only when `floor_index ≤ anchor_index − 1`; never exceed standard's rung
  or the anchor. **R2 fallback_chain:** ≤2 step-downs then `None` (omit); never terminate on the anchor.
- **TDD/proof:** (1) **R1 monotonicity test across the FULL anchor×mode×work-class matrix** — `essential-coding ≤
  standard-coding ≤ anchor` everywhere; fable→sonnet, opus/sonnet/haiku→collapse, never inverts; (2) mode-table
  per-cell; (3) `resolve()` returns `None` on unknown family/anchor/skill + absent config (BC, R3); (4)
  `fallback_chain` ≤2-then-`None`, never anchor.
- **Gate:** unit tests green; pure stdlib (no import from `kata_install` private region); Snyk clean.

### W1-B — Re-introduction guard (A1)  ·  OWNS: `tools/validate_skills.py`, `tools/tests/test_validate_model_guard.py`, `docs/STANDARDS.md`
- Add the **A1 guard (R8):** `validate_skills.py` ERRORs on any absolute `model:` in **SKILL.md frontmatter only**
  (adapters/config untouched). Add the rule to `STANDARDS.md §1` (the `model:` field note becomes forbidden-in-core).
- **TDD/proof:** a planted `model: opus` in a SKILL.md fails validation with a clear message; a `model:` under
  `adapters/**` or in config does NOT trip it; lock-test scans every SKILL.md; **validate stays 47/0** with the guard.
- **Gate:** tests green; 47/0 with guard; Snyk clean.

### W1-C — update.ps1 exit-fix  ·  OWNS: `update.ps1`
- Apply the **same `iex`/`exit` fix already shipped in `install.ps1`:** replace every bare `exit` with
  `throw` / `$global:LASTEXITCODE` (under `irm | iex` a bare `exit` closes the host WINDOW). Mirror install.ps1's
  pattern: set `$global:LASTEXITCODE` for the propagate path, `throw` only on real failure.
- **Live proof:** offline smoke on PowerShell — download-then-run path does NOT close the host window; engine exit
  code propagates; failure surfaces as a throw. (No Python touched.)
- **Gate:** PowerShell smoke green; grep-assert no bare `exit` remains on the propagate path.

### W1-D — config schema docs  ·  OWNS: `protocol/config.md`
- Document the `kata.config.models` block (DESIGN §2): `anchor`/`family`/`coderFloor`/`policyOverride?`, the
  **BC guarantee** (absent ⇒ inherit, byte-for-byte, R3), and that only economy tier-down reads the anchor (R7).
- **Gate:** schema matches `kata_models.resolve()` inputs; no field documented that the resolver does not read.

---

## WAVE 2 — wiring (needs W1-A Layer-1)

### W2-A — Relative-token roles  ·  OWNS: `tools/kata_roles.py`, `tools/tests/test_kata_roles.py` (additive)
- Accept relative tokens `anchor` / `anchor-1` / `anchor-2` in a role's `model` field → resolve via `kata_models`
  (anchor + family from `kata.config.models`). Absolute IDs and absent model stay BC.
- **Depends on:** W1-A. **TDD:** each token resolves to the right ladder rung; unknown anchor → inherit (`None`);
  existing `test_kata_roles.py` tests still pass.
- **Gate:** tests green; Snyk clean.

### W2-B — Dispatch wiring + fallback loop  ·  OWNS: `skills/coordinate/kata-orchestrate/SKILL.md`
- Wire DESIGN §2 L2 into the orchestrator prose: classify work-class → `resolve()` → pass `model=` or **omit on
  `None`** → the **≤2-step R2 fallback loop** (any failure on a non-inherited model except 401/403 → advance
  `fallback_chain`, retry, NOTE; then omit; never abort). Rework any residual absolute-model language to relative.
- **Depends on:** W1-A. **Live proof (gate-level):** tier-down actually changes the model per mode; coder-floor at
  a fable anchor lands essential-coding on sonnet; a **simulated-unavailable / mythos-gated** model degrades
  instead of crashing; 401/403 surfaces as a real error.
- **Gate:** prose carries no absolute model ID; live-proof transcript attached.

### W2-C — Anchor-write at initiation  ·  OWNS: `skills/coordinate/kata-bootstrap/SKILL.md`, `modules/initiation/kata-initiate/SKILL.md`
- `kata-bootstrap` / `kata-initiate` resolve/confirm the anchor once → write `kata.config.models.anchor`
  (default = the platform's latest top rung, R7). Critical work still inherits by omission; only economy reads the name.
- **Depends on:** W1-D (schema). **Proof:** a bootstrap run writes a valid `models` block; absent-block path still inherits.
- **Gate:** written block validates against `protocol/config.md`.

---

## WAVE 3 — docs + decisions + full map

### W3-A — STANDARDS / kata-write-skill rule note  ·  OWNS: `skills/meta/kata-write-skill/SKILL.md`
- Note that core SKILL.md frontmatter carries **no `model:`** (R8 guard); model is dispatch-resolved.
  (STANDARDS.md §1 itself is owned by W1-B — this task only updates the authoring skill.)
- **Gate:** authoring guidance matches the A1 guard message.

### W3-B — DECISIONS D131 + full work-class map  ·  OWNS: `.planning/DECISIONS.md`, `tools/kata_models.py` work-class-map region (sequenced AFTER W1-A lands)
- Write the **D131** entry (relative model-tiering; folds R1–R8; supersedes ASSESSMENT conflicts).
- **R5 build task — enumerate + classify ALL ~47 repo skills** into the work-class map (`critical | coding | economy`);
  coverage must explicitly INCLUDE the 3 `modules/` skills (`load_skills` counts them), not just `skills/`;
  every execute/coding skill explicitly classified so economy fires; `unknown → critical` only for unseen skills.
- **Sequencing:** the map-fill edits `kata_models.py` AFTER W1-A is merged (W1-A owns the file first → no parallel
  conflict; this is a follow-on edit, not a concurrent one).
- **TDD/proof:** the work-class coverage test lives in `tools/tests/test_kata_models.py` (owned by W1-A; W3-B is
  sequenced after W1-A merges, so this is a follow-on edit, NOT a co-edit). It asserts every loaded skill name
  (`skills/` + the 3 `modules/` skills) is present in the map; spot-check tier-down per class.
- **Gate:** map covers 47/47 skills; D131 entry complete.

---

## Integration gate (all waves)
- **pytest green** (existing suite + W1-A/W1-B/W2-A/W3-B new) · **validate_skills 47/0 WITH the new A1 guard** ·
  **Snyk medium+ 0** on all new/changed Python (`kata_models.py`, `validate_skills.py`, `kata_roles.py`).

## Live-proof obligations (must be demonstrated, not asserted)
1. **Tier-down changes the model per mode** — advanced/standard/essential resolve to distinct rungs at a given anchor.
2. **Coder-floor (R1)** — at a fable anchor, essential-coding lands on sonnet; at opus/sonnet/haiku it collapses,
   never inverts (the full-matrix monotonicity test is the machine proof; one live transcript confirms it).
3. **Availability fallback (R2)** — a **simulated-unavailable / mythos-gated** model degrades (≤2 step-downs then
   omit) instead of crashing; a 401/403 surfaces as a real error, not a silent downgrade.
