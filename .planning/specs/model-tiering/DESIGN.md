---
title: "model-tiering — FROZEN DESIGN (relative, mode-driven model selection)"
status: FROZEN (2026-06-30) — operator-approved; dval + grounding research folded (R1–R8 supersede ASSESSMENT)
spec: model-tiering
decision: D131 (model-agnostic relative tiering) — builds on D130 (strip hard-coded model: frontmatter, 8af2e37)
builds-on: ASSESSMENT.md (base design); R1–R8 are the RESOLVED DECISIONS and override any conflicting ASSESSMENT text
scope: Claude-only core (v0.1) — OpenAI/Gemini ladders ship SHAPE-ONLY (IDs re-pulled at build)
invariant: essential-coding ≤ standard-coding ≤ anchor (R1) · inherit-on-doubt · default-FAIL · validate 47/0 · Snyk medium+ 0
tags: [design, frozen, model-tiering, relative-tiering, anchor, fallback, agnostic-core]
---

# model-tiering — FROZEN DESIGN

Model selection is a **relative differential off the operator's session model (the anchor)**, resolved at
dispatch — never a fixed ID in skill frontmatter. A gated model (`fable`) once took down `/kata-loop`; this
design makes that class of failure structurally impossible: **any ZERO-STEP cell inherits by omission** (resolves
to `None`/OMIT → always current, immune to a gated top rung), and any unavailable economy model **degrades, never
crashes**. **The determinant is step-count, not work-class:** `step-count == 0 → None` (inherit by omission —
advanced all-cells + standard-critical); `step-count < 0 → explicit id` (step strictly below the anchor — including
essential-critical at `anchor−1`). It is NOT "work-class == critical → None."

This freeze folds the adversarial-review (dval) + grounding-research outcomes **R1–R8**, which **supersede any
conflicting text in `ASSESSMENT.md`** (deltas noted inline).

> **POST-FREEZE ADDENDUM (2026-07-01, operator decision — Fable 5 re-release).** Two operator-approved re-tunes,
> implemented in `tools/kata_models.py` (authoritative) + `tests/test_kata_models.py`:
> 1. **Sonnet id → `claude-sonnet-5`** (was `claude-sonnet-4-6`; Sonnet 5 re-release).
> 2. **Per-family step tables.** The **Anthropic** family deepens the **economy** column by one rung —
>    `advanced −1 · standard −2 · essential −2` (was `0 / −1 / −1`), so Anthropic economy lands on **Opus**
>    (advanced) and **Sonnet 5** (standard/essential). `critical` + `coding` are **unchanged**. Every
>    **non-Anthropic** family keeps the original table (`0 / −1 / −1` economy) via `_STEPS_DEFAULT`.
> R1/R2/R3/R7 invariants are preserved unchanged (critical zero-step cells still inherit-by-omission;
> `essential-coding ≤ standard-coding ≤ anchor` still holds; economy monotonicity intact). This addendum
> overrides the **economy** column of the §1 Mode→model table — and supersedes **R8**'s "essential 'other
> economy' stays `anchor−1` (`==standard`)" clause — for **Anthropic only** (non-Anthropic keeps the R8 table).

---

## 0. Locked decisions (R1–R8 — operator-approved)

- **R1 — coder-floor monotonicity.** Invariant for EVERY anchor: `essential-coding ≤ standard-coding ≤ anchor`.
  The coder-floor raises a coding tier toward a competent coder ONLY when `floor_index ≤ anchor_index − 1`; it
  must never exceed standard's rung and never exceed the anchor. At a fable/top anchor `essential` coding lands
  on **sonnet** (the real −2 win); at opus/sonnet/haiku anchors it collapses to `==standard` or `==anchor` and
  NEVER inverts. *(Δ ASSESSMENT: refines decision 2's "anchor−2 coder-floored" into a hard, tested invariant.)*
- **R2 — availability fallback.** ANY dispatch failure on a **non-inherited** model triggers a step-down —
  **no error-string matching** — EXCEPT **HTTP 401/403** (auth/quota) which surface as a real error (never a
  silent downgrade on a billing problem). Terminus = **OMIT the model param entirely** (host picks its default),
  **never "inherit the anchor"** (re-inheriting a gated top rung re-triggers the outage). Bound to **≤2
  step-downs, then omit.** *(Δ ASSESSMENT: replaces decision 4's "step to floor THEN inherit the anchor" terminus.)*
- **R3 — BC grounding (Claude path).** Omitting the Agent `model` param inherits the operator's session model —
  **CONFIRMED for the Claude host** (the only built path in v0.1). **BC guarantee:** absent `kata.config.models`
  ⇒ `resolve()` returns `None` everywhere ⇒ inherit ⇒ today's single-model behavior, **byte-for-byte**. Grounded
  for Claude; other hosts are honestly scoped to their adapters. *(Δ ASSESSMENT: closes open grounding unknown #1.)*
- **R4 — ladders are PLAIN STRING lists, not alias lists.** Anthropic = `["haiku","sonnet","opus","fable","mythos"]`.
  `fable` and `mythos` are **DISTINCT** models (mythos is higher and gated for most accounts) — the
  "alias / survives-rename" rationale is **dropped entirely (it was false).** mythos-gated-for-this-account is the
  natural **live test case** for the availability fallback. Exact IDs (`claude-haiku-4-5`, `claude-sonnet-4-6`,
  `claude-opus-4-8`, `claude-fable-5`, `claude-mythos-5`) are DATA verified at build. *(Δ ASSESSMENT: replaces the
  "top rung is an alias list" model.)*
- **R5 — work-class map covers ALL ~47 skills.** Every skill in the repo is classified explicitly (not just the 19
  from the original split). Every execute/coding skill (`kata-tdd`, `kata-characterize`, `kata-diagnose-*`,
  `kata-iac-*`, `kata-lang-profile`, `kata-sprint`, …) is seeded so the economy tier actually fires.
  `unknown → critical` remains the safe default ONLY for genuinely-new/unseen skills. *(Δ ASSESSMENT: expands the
  19-skill seed to full coverage; enumeration is a build task, PLAN W3.)*
- **R6 — ladders live as a DATA registry in core `tools/kata_models.py`.** Data, not provider logic; extensible via
  the `kata.config.models` block. This is a **deliberate v0.1 decision** (Claude-only core), NOT an adapter
  indirection — recorded so the agnostic-core/adapter reviewer does not flag it.
- **R7 — anchor = the operator's session model.** **Zero-step critical** (advanced-critical + standard-critical)
  needs **no detection** (inherits by omission — `None` → always current, immune to staleness AND to a gated top
  rung). Any **below-anchor cell** needs the anchor NAME to compute the rung — that is the economy tier-down AND
  `essential-critical = anchor−1` (a below-anchor cell returning an explicit id, NOT inherit-by-omission). The
  anchor name is read from `kata.config.models.anchor` (default = the platform's latest top rung). A stale anchor
  only mis-tiers below-anchor COST, never zero-step (inherited) correctness. `kata-bootstrap`/`kata-initiate`
  sets/confirms the anchor.
- **R8 — guard scope + minors.** The validator hard-fail on absolute `model:` is scoped to **SKILL.md frontmatter
  ONLY** (adapters/config MAY still pin models). Fallback step cap **≤2**. `essential` "other economy" stays
  `anchor−1` (`==standard`) per the operator's locked table; essential's savings come from `critical→anchor−1`
  and `coding→anchor−2-floored`.

---

## 1. Mode → model policy (the differential)

Anchor = the session model. `−n` = n rungs down the anchor's family ladder, clamped to the floor (R4 ladder).

| Mode | Critical (judgment · plan · grill · evaluate · gate) | Coding (build · encode · refactor) | Other economy (report) |
|---|---|---|---|
| **advanced** | anchor | anchor | anchor |
| **standard** (default) | anchor | anchor − 1 | anchor − 1 |
| **essential** | anchor − 1 | anchor − 2 (coder-floored, R1) | anchor − 1 |

Read across: advanced = top model exclusively; standard = top for deep, step down for writing; essential = lower
model exclusively (max speed/economy). **Resolution mapping:** every `anchor` cell (zero-step) resolves to
**`None`/OMIT** (inherit by omission); every `anchor − n` cell (`n ≥ 1`, below-anchor — including
`essential-critical = anchor − 1`) resolves to an **explicit id**. The determinant is step-count, not work-class.
**R1 binds every cell:** `essential-coding ≤ standard-coding ≤ anchor` at
every anchor position — at fable/top → sonnet; at opus/sonnet/haiku → collapses to `==standard`/`==anchor`, never inverts.

---

## 2. Architecture — pure resolver, called at dispatch, fed by config at the top

### Layer 1 — `tools/kata_models.py` (NEW, pure stdlib) — the resolver contract (R6)
- **Family ladders (DATA registry, R4):** plain string lists per family —
  `{"anthropic": ["haiku","sonnet","opus","fable","mythos"], "openai": [...shape], "gemini": [...shape], "generic": [...]}`.
  Anthropic IDs verified at build; OpenAI/Gemini ship shape-only. Extensible via `kata.config.models`.
- **Work-class map (DATA):** `skill → critical | coding | economy`, seeded for **ALL ~47 skills (R5)**.
  `unknown → critical` is the safe default for genuinely-unseen skills only.
- **`resolve(skill, mode, anchor, *, family, coder_floor) -> id | None`:** work-class → step count (table §1) →
  walk ladder from `anchor_index` → clamp to floor → apply the **R1 coder-floor** for `coding`
  (raise only when `floor_index ≤ anchor_index − 1`; never exceed standard's rung or the anchor) → `None`
  (= inherit by omission) on ANY uncertainty (unknown family/anchor/skill, absent config).
  **Zero-step contract:** `resolve()` returns `None` (= OMIT the model param → inherit) whenever the resolved
  rung index `== anchor_index`; it returns an explicit id string ONLY for a rung strictly BELOW the anchor
  (resolved index `< anchor_index`). This is structural — a zero-step cell must never re-select the anchor's own
  id (which could re-select a gated top-rung anchor, e.g. `mythos`, and re-trigger the outage).
- **`fallback_chain(id, family) -> [id, …, None]`:** ordered step-down, **≤2 entries then `None`** (= OMIT param,
  R2). Never re-selects the anchor as a terminus.

### Layer 2 — dispatch wiring (the only place a model is chosen)
- **Host `Agent`-tool path** (`kata-orchestrate` loop + grill/plan/evaluate/review sites): classify work-class →
  `resolve()` → pass `model=` or **OMIT on `None`** (inherit). Wrap in the **R2 fallback loop**: any dispatch
  failure on a non-inherited model (EXCEPT 401/403, which raise) → advance `fallback_chain`, retry, NOTE; after
  ≤2 step-downs → omit the param; **never abort.**
- **Cross-model path:** `build_brief(model=resolve(...))` (already plumbed in `kata_dispatch.py`).
- **`kata_roles.py`:** accept relative tokens (`anchor` / `anchor-1` / `anchor-2`) → resolve via `kata_models`.

### Layer 3 — anchor resolution at the top of the chain (R7)
`kata-bootstrap`/`kata-initiate` resolve/confirm the anchor once → write `kata.config.models.anchor`. Critical work
needs no detection (inherits by omission); only economy tier-down reads the anchor NAME; unknown anchor → inherit.

### `kata.config.models` (NEW block, BC-safe)
```json
"models": { "anchor": "session"|"<id>", "family": "auto"|"<fam>", "coderFloor": "sonnet", "policyOverride"?: {…} }
```
**Absent ⇒ `resolve()` returns `None` everywhere ⇒ inherit ⇒ today's single-model behavior, byte-for-byte (R3).**

---

## 3. Robustness guarantees
- **A1 — re-introduction guard:** `validate_skills.py` ERRORs on any absolute `model:` in **SKILL.md frontmatter
  ONLY (R8)**; rule in `STANDARDS.md` + `kata-write-skill`; a lock-test scans every SKILL.md. (47/0 stays the bar.)
  Adapters/config MAY pin models — out of scope for the guard.
- **A2 — availability fallback (R2):** the dispatch fallback loop — gated/unavailable model steps down ≤2 then
  omits the param; 401/403 surface as a real error; never aborts, never re-selects a gated anchor.
- **B — inherit-on-doubt (R3/R7):** every uncertain path collapses to "run at the anchor by omission," never
  "force a model."

---

## 4. Acceptance criteria (freeze-gate bar)
1. **BC:** absent `kata.config.models` ⇒ `resolve()` returns `None` everywhere ⇒ inherit ⇒ today's behavior byte-for-byte.
2. **Mode table honored per work-class:** every (anchor × mode × work-class) cell resolves to the table §1 value —
   and every ZERO-STEP cell (resolved rung `== anchor_index`: advanced all-cells + standard-critical) resolves to
   **`None`/OMIT** (inherit), NOT the anchor id string; only strictly-below-anchor cells return an explicit id.
3. **R1 monotonicity:** `essential-coding ≤ standard-coding ≤ anchor` across the FULL anchor×mode×work-class matrix —
   a unit test; fable→sonnet, opus/sonnet/haiku→collapse, never inverts.
4. **Fallback (R2):** never aborts; ≤2 step-downs then omit; 401/403 raises; terminus is OMIT, never a re-selected
   gated anchor; mythos-gated case degrades.
5. **Guard (A1):** validator hard-fails an absolute `model:` in SKILL.md frontmatter; validate 47/0 WITH the guard.
6. **R5 coverage:** the work-class map covers **100% of loaded skills** — `skills/` PLUS the 3 `modules/` skills
   (`load_skills` counts them), not just `skills/`.
7. **R8 guard negative case:** the validator A1 guard hard-fails an absolute `model:` in a SKILL.md frontmatter but
   does **NOT** block a model pin in `adapters/**` or config (the allowed negative case).

## 5. Honest scope
Claude-only core (v0.1): the inherit-by-omission BC guarantee (R3) and the Anthropic ladder IDs (R4) are grounded
for the Claude host. OpenAI/Gemini ladders ship **shape-only**; their IDs and inherit semantics are re-pulled and
re-grounded at each adapter's implementation, not assumed here.

---

## POST-FREEZE GATED AMENDMENT (2026-07-04, D148 — context-autonomy premium gate)

> **Provenance.** Copied VERBATIM from the FROZEN context-autonomy DESIGN §3
> (`.planning/specs/context-autonomy/DESIGN.md`), where it is the frozen amendment text.
> Appended here (supersede-never-rewrite — no line above this point is edited), following the
> 2026-07-01 POST-FREEZE ADDENDUM precedent. Implemented in `tools/kata_models.py` (`resolve()`'s
> additive `premium=` branch + the exported `premium_status()`) + `tools/tests/test_kata_models_premium.py`
> (CA-P0 task E3). The existing `tests/test_kata_models.py` BC canary is byte-unchanged.

## §3 GATED AMENDMENT to the frozen model-tiering DESIGN (D148)

Delivered as a post-freeze gated-amendment addendum APPENDED to `.planning/specs/model-tiering/DESIGN.md`
(the existing POST-FREEZE ADDENDUM precedent; supersede-never-rewrite — no frozen line is edited).
**Gating clause:** everything below activates ONLY under `kata.config.models.premium` with all four
conjuncts true; **absent `models.premium`, the frozen spec governs byte-for-byte** — zero change to any
existing path, including the absent-`models`-block BC guarantee (R3).

1. **What it amends (quoted).** The frozen zero-step contract (model-tiering DESIGN §2, Layer 1):
   > "`resolve()` returns `None` (= OMIT the model param → inherit) whenever the resolved rung index
   > `== anchor_index`; it returns an explicit id string ONLY for a rung strictly BELOW the anchor
   > (resolved index `< anchor_index`)."
   is amended to: *explicit ids for non-anchor rungs — strictly below the anchor as frozen, **or the
   single rung strictly ABOVE the anchor under a recorded premium approval**.* Zero-step cells still
   NEVER return the anchor's own id (the gated-top-rung protection is untouched).
2. **The premium branch (R-16, R-22; premium-id pin per freeze-gate fold #1).** The premium id is
   **`models.premium.offer` itself** — never derived by ladder walk. The branch fires iff **all four
   conjuncts** hold at resolve-time: `models.premium.approved == true` ∧ `work-class ∈
   models.premium.scope` (critical | coding only — economy never, R-9) ∧ **the `offer` rung sits
   EXACTLY ONE rung strictly above the anchor in the family ladder** ∧ `mode == "advanced"`. ANY other
   offer↔anchor relation ⇒ **NO FIRE + surfaced** (board NOTE): `offer == anchor` (e.g. anchor already
   fable); offer 2+ rungs above (e.g. a hand-edited mythos over an opus anchor — approval never
   escalates past one rung); offer below the anchor. `resolve()` then returns the explicit `offer` id
   (inherit would silently give the session model; explicit is mandatory).
3. **grantedMode lapse (R-22/R-34).** The approval record carries the mode it was granted under
   (`grantedMode`). A re-entrant run with `mode ≠ grantedMode` LAPSES the approval (bootstrap clears
   `approved`; the next preflight re-asks). This is the fourth conjunct's persistence arm.
4. **Any-failure run-lapse + the OMIT terminus (R-25, R-38).** ANY premium dispatch failure lapses
   `approved` for the remainder of the run — one fallback step only: **premium → OMIT/inherit at the
   anchor rung** (never an explicit anchor id; tracks mid-run `/model` switches; preserves the frozen
   "never re-selects the anchor as a terminus" discipline). No re-offers, no per-task retry (the exact
   retry-storm R2 exists to prevent).
5. **R2 auth carve-out, premium rung ONLY (R-30).** The frozen R2 text —
   > "EXCEPT **HTTP 401/403** (auth/quota) which surface as a real error (never a silent downgrade on a
   > billing problem)"
   — is amended for the premium rung only: premium 401/403 ⇒ **premium-unavailable**: OMIT-inherit +
   LOUD surface (board DECISION + ledger `degraded {scope:"premium", reason:"auth-40x"}` + handoff note)
   + approval LAPSED for the run. Rationale: R2's raise protects BASELINE dispatch (misconfig = stop);
   premium is an optional elevation whose failure has a semantically-correct safe fallback — the anchor,
   the exact no-approval behavior. Unattended survival wins; never silent. **Baseline rungs: R2
   unchanged, including the 401/403 raise.**
6. **Untouched invariants (stated so the gate can check):** R1 monotonicity
   (`essential-coding ≤ standard-coding ≤ anchor`) is below-anchor arithmetic and is unaffected; the R2
   ≤2-step-down bound for baseline chains is unaffected (premium has its own one-step chain); the
   inline-eval M4-L7 carve-outs are unaffected (inline eval is economy class — structurally outside
   `premium.scope`).

## Amendment #2 (2026-07-05, GATED — adaptive premium scope: event form + budget envelope;
## delivered by the adaptive-tiering initiative, D150)

**Routing:** POST-FREEZE gated-amendment addendum (the Amendment-#1/D148 precedent — no frozen line
above is edited). Full contract: `.planning/specs/adaptive-tiering/DESIGN.md` (FROZEN 2026-07-05;
freeze-gate v1 HOLD → 19 folds → re-gate SHIP-WITH-FIXES → 8 folds). This addendum records ONLY what
changes on THIS spec's surface.

1. **`premium.scope` becomes TYPE-DISPATCHED (AT-L15).** A LIST value keeps the Amendment-#1
   work-class semantics BYTE-FOR-BYTE (run-long class scope — zero change to any shipped path). An
   OBJECT value `{events: [...], budget: {calls: N}}` activates the ADAPTIVE form: conjunct #2 of the
   four-conjunct fire rule reads "event ∈ scope.events **AND work-class ∈ {critical, coding}**" —
   the R-9 economy exclusion is STRUCTURAL (code-enforced) in BOTH forms, exactly as the list form
   always had it (adval F1 fold: an event-tagged economy dispatch falls through to the frozen path;
   its fail-bump ceilings at the anchor). The rule's SHAPE (four conjuncts, offer exactly one rung
   above the anchor, mode == "advanced", recorded approval) is unchanged. Any other type / unknown event name / unknown object key / non-int budget ⇒
   load-guard RAISE (GB12/D45). Absent `events` key in the object form ⇒ RAISE; explicit `[]` ⇒ legal
   no-op. Absent `premium` block entirely ⇒ the frozen spec governs byte-for-byte (R3 restated).
2. **The budget envelope (AT-L12/L13).** Object form carries `budget.calls` (default 10; token budgets
   degrade to call budgets where the host reports nulls — usage_meter honesty). FCFS spend with the
   last 2 calls RESERVED for `freeze-gate-verdict`/`re-gate-after-hold` events; exhaustion ⇒ premium
   LAPSES to the anchor for the run's remainder (LOUD DECISION + degraded record + handoff note — the
   CA-L30 lapse discipline). Counting at DISPATCH COMMIT by the single conductor; durable recount from
   the board `tier:` DECISION lines.
3. **Family generalization + rename (AT-L17).** All prose says "the premium rung." The fire relation
   ("offer exactly one rung above the anchor IN ITS FAMILY") is already family-parametric via the
   ladder registry; a family without a registered rung above the anchor ⇒ NO-FIRE + board NOTE
   (unchanged mechanics, generalized statement — e.g. an `openai` ladder's expensive top rung
   qualifies the moment it is registered).
4. **Adaptive modulation NEVER breaks this spec's emission contract (AT-L2b):** a modulated rung
   landing ON the anchor emits `None`/OMIT (never the anchor's explicit id — R7); below-anchor rungs
   emit explicit ids; the premium rung emits `premium.offer` itself (Amendment #1 §3.1 verbatim).
5. **Untouched invariants (stated for the gate):** R1 coder-floor monotonicity; R2's ≤2-step baseline
   bound + the 401/403 raise; the premium one-step lapse chain (Amendment #1 items 3–5); zero-step
   OMIT. The adaptive layer only supplies WHICH rung to emit — every emission and failure rule above
   stands.
