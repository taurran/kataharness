# model-tiering — relative, mode-driven model selection (pre-grill design assessment)

**Status:** pre-grill design input. Grill refines → DESIGN freezes → build through the loop.
**Proposed decision:** D131 (model-agnostic relative tiering). Builds on D130 (strip hard-coded
`model:` frontmatter — already shipped, commit `8af2e37`).

## Problem
Model selection was hard-baked in skill frontmatter `model:` — Claude-specific, absolute, static.
A gated model (`fable`) took down `/kata-loop`. A tool-agnostic harness must choose models as a
**relative differential off the operator's anchor**, resolved at dispatch, never as a fixed ID.

## Locked decisions (operator-approved 2026-06-30)
1. **Anchor = the operator's session model if detectable, else the platform's *latest* top rung**
   (resolved dynamically — never a pinned ID; auto-tracks the fable→mythos rename).
2. **Coder-floor default = `sonnet`-class** — `essential` non-critical coding tiers to `anchor−2`
   but never below a competent-coder rung (stops opus-anchor essential coding dropping to Haiku).
3. **Frontmatter `model:` is forbidden entirely** — model is dispatch-resolved; the validator
   hard-fails any absolute `model:` in a SKILL.md.
4. **Fallback terminus = step down the family ladder to the floor, THEN inherit the anchor** —
   never crash on an unavailable model.

## Mode → model policy (the differential)
Anchor = session model (else latest top). `−n` = n rungs down the anchor's family ladder
(`haiku < sonnet < opus < fable|mythos`; one version down for GPT/Gemini), clamped to floor.

| Mode | Critical (judgment · plan · grill · evaluate · gate) | Non-critical coding (build · encode · refactor) | Other economy (report) |
|---|---|---|---|
| **advanced** | anchor | anchor | anchor |
| **standard** (default) | anchor | anchor − 1 | anchor − 1 |
| **essential** | anchor − 1 | anchor − 2 (coder-floored) | anchor − 1 |

Read across: advanced = top model exclusively; standard = top for deep, step down for writing;
essential = lower model exclusively (max speed/economy). Relative — scales to whatever anchor is on.

## Architecture — one pure resolver, called at dispatch, fed by config at the top of the chain

### Layer 1 — `tools/kata_models.py` (NEW, pure stdlib)
- **Family ladders (data):** `{"anthropic": ["haiku","sonnet","opus",["fable","mythos"]], "openai": [...],
  "gemini": [...], "generic": [...]}`. Top rung is an **alias list** — the rename survives as data.
- **Work-class map (data):** skill → `critical | coding | economy`. Seeded from the removed split
  (14 ex-`fable` = critical; 4 ex-`sonnet` = economy; `kata-tdd` = coding). Unknown skill → `critical`.
- **`resolve(skill, mode, anchor, *, family, coder_floor) -> alias | None`:** work-class → step count
  → walk ladder from anchor index → clamp to floor → coder-floor for `coding` → `None` (= inherit anchor)
  on any uncertainty (unknown family/anchor/skill, absent config).
- **`fallback_chain(alias, family) -> [alias, …, None]`:** ordered step-down terminating in inherit.

### Layer 2 — dispatch wiring (the only place model is chosen)
- **Host `Agent`-tool path** (`kata-orchestrate` loop step 2 + grill/plan/evaluate/review sites):
  classify work-class → `resolve()` → pass `model=` or **omit on `None`** (inherit). Wrap in the
  **fallback loop**: model-unavailable → advance `fallback_chain`, retry, NOTE, never abort.
- **Cross-model path:** `build_brief(model=resolve(...))` (already plumbed in `kata_dispatch.py`).
- **`kata_roles.py`:** accept relative tokens (`anchor`/`anchor-1`/`anchor-2`) → resolve via `kata_models`.

### Layer 3 — anchor resolution at the top of the chain
`kata-bootstrap`/`kata-initiate` resolve the anchor once → write `kata.config.models`.
Critical work needs no detection (inherits by omission); only economy tier-down needs the anchor name,
and if even that is unknown → inherit (degrade safe).

### `kata.config.models` (NEW block, BC-safe)
`"models": { "anchor": "session"|"<id>", "family": "auto"|"<fam>", "coderFloor": "sonnet", "policyOverride"?: {…} }`
**Absent ⇒ resolve() returns None everywhere ⇒ inherit ⇒ today's single-model behavior, byte-for-byte.**

## Robustness guarantees
- **A1 — re-introduction guard:** `validate_skills.py` ERRORs on any absolute `model:` in frontmatter;
  rule in `STANDARDS.md` + `kata-write-skill`; a lock-test scans every SKILL.md. (47/0 stays the bar.)
- **A2 — availability fallback:** the dispatch fallback loop — gated model steps down or inherits.
- **B — inherit-on-doubt:** every uncertain path collapses to "run at the anchor," never "force a model."

## Open grounding unknowns (research, not assumed — D124)
1. Does Claude Code expose the session model to a skill/subagent (env var / probe)? Does omitting the
   Agent `model` reliably inherit it? → decides auto-detect vs config-set anchor.
2. The unavailable-model error signature (Agent tool + codex/claude CLIs) → the fallback trigger.
3. Current latest top rung per family (Anthropic/OpenAI/Gemini) → ladder data, **verified at build**.

## The loop (all evaluation gates in place)
GRILL (`kata-grill-standard`, + grounding research subagent) → FREEZE (`kata-design-doc` DESIGN +
`kata-plan-standard` PLAN, disjoint-ownership wave DAG) → FREEZE-GATE (`kata-review` HOLD/SHIP) →
BUILD (`kata-orchestrate` → `kata-tdd` per task, worktrees, TDD) → INTEGRATION GATE (pytest · validate
47/0 *with guard* · Snyk medium+ 0) → LIVE PROOF (tier-down per mode + coder-floor + simulated-unavailable
fallback) → EVALUATE (`kata-evaluate`, fresh, default-FAIL) → ADVERSARIAL REVIEW (`kata-review-standard`)
→ MERGE GATE (operator).

**Wave DAG (disjoint file-ownership):**
- W1 (parallel): `kata_models.py`+tests · `validate_skills` guard+tests · `update.ps1` exit-fix+live-proof · `config.md` schema.
- W2 (needs L1): `kata_roles` relative tokens · `kata-orchestrate` dispatch+fallback+prose · `bootstrap`/`initiate` anchor-write.
- W3: `STANDARDS`/`kata-write-skill` rule · `DECISIONS.md` (D131) + spec docs.

## Deferred (carried in freeze, NOT built)
- **Essential up-front triage gate** to shorten the loop ("is the first pass worth iterating?"). Caveat:
  an early-reject gate biases toward regenerate-and-reroll over iterate-and-fix — needs a **slot-machine
  guard** before it ships. Revisit in tweaks (operator, 2026-06-30).
