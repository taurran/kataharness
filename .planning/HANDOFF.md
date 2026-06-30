---
date: 2026-06-30 (D131 model-tiering — SHIPPED + PUSHED commit `fac090b`, master in sync. Builds on D130 `8af2e37`. Final baseline: pytest 2126 pass / 2 skip / 0 fail · validate 47/0 WITH the A1 guard · Snyk medium+ 0.)
branch: master — private remote github.com/taurran/kataharness, tip `fac090b` (D131 model-tiering — SHIPPED + PUSHED + in sync). The D131 spec docs (`.planning/specs/model-tiering/{ASSESSMENT,DESIGN,PLAN}.md`) are COMMITTED.
green: validator 47 skills / 0 errors · pytest 2126 passed / 2 skip / 0 fail (WITH kata_models + A1-guard + roles tests) · Snyk medium+ 0 on new/changed Python (pre-existing `tools/kata_install.py` 17 LOW CWE-23 still below gate — STANDING hardening item)
tags: model-tiering · D131 · relative-model-selection · anchor-differential · resolver-contract · R1-R8 · SHIPPED · v0.1-Claude-only-core
authored-for: kata-orient (sections map to the orientation tiers)
★ NEXT-SESSION START HERE: read `.planning/NEXT-SESSION-ORIENTATION.md` (self-contained). D131 is COMPLETE (commit `fac090b`, pushed master). Next = a series of new Kata Loop cycles over the backlog (toward v0.1). Two standing items: `kata_install.py` 17 LOW CWE-23 hardening; benchmark v1 n=0 → live with a real control fixture. The conductor grills/freezes/plans/executes each.
---

> **★ 2026-06-30 (D131 model-tiering — SHIPPED + PUSHED `fac090b`, master in sync):** D131 makes model
> selection **relative + mode-driven** — at dispatch, the model is resolved as a **differential off the operator's current
> session model (the anchor)**, never a hard-baked `model:` ID. Built directly on **D130** (strip hard-coded `model:`
> frontmatter — SHIPPED + PUSHED, commit `8af2e37`, master in sync). This session, ALL via subagents: adversarial dval
> (HOLD, 3 blockers) + grounding research → synthesized into the resolved decision ledger **R1–R8** → freeze (DESIGN + PLAN
> authored) → freeze-gate adversarial review (HOLD: 2 blockers + 1 major) → fixes applied → freeze re-confirmed (SHIP) →
> build W1–W3 → integration gate → **LIVE PROOF passed** (D124 thesis confirmed live: LIVE PROOF + D98 adversarial sweep
> caught two real defects that unit tests blessed — advanced/coding coder-floor not gated to essential; full-id anchor
> silently disabling tiering) → commit `fac090b` pushed master. **Final baseline: pytest 2126 pass / 2 skip / 0 fail ·
> validate 47/0 WITH the A1 guard · Snyk medium+ 0.** Spec docs (ASSESSMENT/DESIGN/PLAN) are **COMMITTED**. **Next: series
> of new Kata Loop cycles over the backlog (toward v0.1).**

# HANDOFF — KataHarness — 2026-06-30 (D131 model-tiering — SHIPPED + PUSHED `fac090b`)

> **This session: ONE feature (D131 model-tiering), driven ENTIRELY through subagents, taken from grill to SHIPPED master.**
> All waves (W1–W3) built and gated. Integration gate green; LIVE PROOF passed; D98 adversarial sweep caught and fixed two
> real defects (advanced/coding coder-floor not gated to essential; full-id anchor silently disabling tiering); committed
> `fac090b` + pushed master. **Final baseline: pytest 2126 pass / 2 skip / 0 fail · validate 47/0 WITH the A1 guard · Snyk
> medium+ 0.** Spec docs committed. Next: series of new Kata Loop cycles over the backlog (toward v0.1). Drive every step
> via subagents. Commit/merge/push ONLY on explicit operator approval.

## 1. Read-in order  *(orientation: CONTEXT)*
**★ Context-lean rule: do NOT inline-read STATE.md or AGENTS.md.** Resume from:
1. `.planning/NEXT-SESSION-ORIENTATION.md` (self-contained, paste-able) · 2. `.planning/BACKLOG.md` (the current queue of
   work toward v0.1; this is the primary next-action source now that D131 is complete) · 3. `.planning/specs/model-tiering/
   DESIGN.md` + `PLAN.md` (COMMITTED — reference only if backlog work touches the model-tiering contracts).
- If deeper context is genuinely needed: `.planning/specs/model-tiering/ASSESSMENT.md` (pre-grill input), STATE.md TOP
  box only, `CLAUDE.md` (the D59 relative-routing note D131 implements).
⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated, harness-injected). "mindbridge" in any public-facing text = KataHarness.

## 2. State *(orientation: VOLATILE)*
- Branch `master`, tip **`fac090b`** (D131 SHIPPED + PUSHED + in sync). **47 skills / 0 · pytest 2126 pass / 2 skip / 0 fail · Snyk med+ 0.**
  `kata_install.py` carries **17 LOW CWE-23** (operator-supplies-own-path class, below the medium+ gate → STANDING item).
- The D131 spec docs in `.planning/specs/model-tiering/` (`ASSESSMENT.md`, `DESIGN.md`, `PLAN.md`) are **COMMITTED** (commit `fac090b`).
- **LOOP POSITION:** D131 **COMPLETE**. Design FROZEN; freeze re-confirmed SHIP; build W1–W3 executed; integration gate
  green; LIVE PROOF passed; D98 adversarial sweep passed (caught and fixed 2 real defects — see block quote above);
  committed + pushed master. Next = series of new Kata Loop cycles over the backlog.
- **Two standing items:** (a) `kata_install.py` 17 LOW CWE-23 hardening (operator-supplies-own-path, CWE-23); (b) benchmark
  v1 n=0 → live with a real control fixture (n=0 means the benchmark is wired but not yet exercised with a real run).

## 3. NEXT ACTION — series of new Kata Loop cycles over the backlog *(VOLATILE)*
**D131 is COMPLETE** (commit `fac090b`, pushed master). The next work is a series of new Kata Loop cycles over the
backlog toward v0.1. See `.planning/BACKLOG.md` for the current queue. For each item: the conductor grills / freezes /
plans / executes (subagents only). Two standing items to work in at appropriate points: (a) `kata_install.py` 17 LOW
CWE-23 hardening; (b) benchmark v1 n=0 → live with a real control fixture. Commit/merge/push ONLY on explicit operator
approval (does NOT carry across contexts — re-ask each session).

## 4. RESOLVED DECISION LEDGER (R1–R8) + the resolver contract — carry VERBATIM *(the zero-re-derivation core)*
- **R1 (coder-floor):** invariant `essential-coding ≤ standard-coding ≤ anchor` for every anchor; `coder_floor` raises a
  tier only when `floor_index ≤ anchor_index−1`. The −2 win lands at a fable/top anchor (→sonnet); opus/sonnet/haiku
  collapse to ==standard or ==anchor, never invert. Unit-tested as a full anchor×mode matrix.
- **R2 (fallback):** never string-match the error; ANY dispatch failure on a **NON-INHERITED** model steps down, EXCEPT
  HTTP **401/403** (auth/quota) which RAISE (never silent-downgrade on billing). Terminus = **OMIT** the model param (host
  default), NEVER inherit-anchor. **≤2 step-downs** then omit.
- **R3 (BC):** omitting Agent `model` inherits the session model — CONFIRMED for the Claude host (v0.1 Claude-only core).
  Byte-for-byte BC grounded for the built path; other hosts scoped to adapters.
- **R4 (ladder):** family ladders are **PLAIN STRING lists**, not alias lists. Anthropic = `[haiku, sonnet, opus, fable,
  mythos]`. fable & mythos are DISTINCT models (mythos = higher, gated for most accounts → the natural live-fallback test).
  Exact IDs (`claude-haiku-4-5`, `claude-sonnet-4-6`, `claude-opus-4-8`, `claude-fable-5`, `claude-mythos-5`) are **DATA
  verified at build**; OpenAI/Gemini = ladder shape only, IDs re-pulled at build.
- **R5 (work-class coverage):** the work-class map must EXPLICITLY classify ALL loaded skills (`skills/` + the 3 `modules/`
  skills; ~47 total via `load_skills`) as `critical|coding|economy`. `unknown→critical` is the safe default for
  genuinely-new skills only.
- **R6 (architecture):** family ladders = **DATA registry** inside core `tools/kata_models.py` (data, not provider logic),
  extensible via `kata.config.models`. Deliberate v0.1 decision (precedent: `kata_dispatch` carries codex/kiro in core).
  NOT an adapter indirection.
- **R7 (anchor):** anchor = **operator session model**. Zero-step cells inherit by omission (`None`) — always current,
  immune to staleness AND a gated top rung. Only below-anchor cells need the anchor NAME (from `kata.config.models.anchor`,
  default = platform latest top rung). Stale anchor only mis-tiers economy COST, never critical correctness.
  Bootstrap/initiate sets/confirms it.
- **R8 (guard + minors):** validator A1 hard-fail scoped to **`SKILL.md` frontmatter ONLY** (adapters/config MAY pin).
  Fallback cap **≤2**. essential "other economy" = anchor−1 (==standard) per the operator's locked table; essential's
  savings come from critical→anchor−1 + coding→anchor−2-floored.

**★ CRITICAL RESOLVER CONTRACT (the freeze-gate fix — MUST hold):** `resolve()` returns **`None`** (=OMIT → inherit anchor
by omission) whenever resolved rung index **== anchor_index**; returns an explicit **id string ONLY** for a rung **strictly
BELOW** the anchor. The determinant is **STEP-COUNT** (step==0 → `None`; step<0 → explicit id), **NOT work-class**. So
**essential-critical (=anchor−1) returns an explicit id**; **advanced cells + standard-critical return `None`**.

**MODE→MODEL TABLE** (columns: critical / non-critical-coding / other-economy):
- advanced  = anchor / anchor / anchor
- standard  = anchor / anchor−1 / anchor−1
- essential = anchor−1 / anchor−2 (coder-floored) / anchor−1

## 5. THE BUILD WAVE DAG (from PLAN.md — SHIPPED commit `fac090b`) *(historical record — D131 COMPLETE)*
- **W1 (parallel, disjoint OWNS):**
  - **W1-A** `tools/kata_models.py` + `tools/tests/test_kata_models.py` — resolver, ladders, `fallback_chain`, R1 matrix test.
  - **W1-B** `tools/validate_skills.py` + `tools/tests/test_validate_model_guard.py` + `docs/STANDARDS.md` — the A1 guard.
  - **W1-C** `update.ps1` — bare `exit`→`throw`/`$global:LASTEXITCODE` (the same `iex` bug as `install.ps1`).
  - **W1-D** `protocol/config.md` — the `kata.config.models` schema.
- **W2 (needs W1-A / W1-D):**
  - **W2-A** `tools/kata_roles.py` + tests — relative tokens.
  - **W2-B** `skills/coordinate/kata-orchestrate/SKILL.md` — dispatch + ≤2-fallback wiring + prose rework.
  - **W2-C** `skills/coordinate/kata-bootstrap/SKILL.md` + `modules/initiation/kata-initiate/SKILL.md` — anchor-write.
- **W3:**
  - **W3-A** `skills/meta/kata-write-skill/SKILL.md` — authoring note.
  - **W3-B** `.planning/DECISIONS.md` (D131) + the work-class-map region of `kata_models.py` (sequenced AFTER W1-A merges;
    coverage test in `test_kata_models.py`).
- **GATES — PASSED:** integration gate (pytest 2126/2/0 · validate **47/0 WITH the A1 guard** · Snyk medium+ 0) ✓ →
  **LIVE PROOF** ✓ → D98 adversarial sweep ✓ (caught + fixed 2 real defects: advanced/coding coder-floor not gated to
  essential; full-id anchor silently disabling tiering) → operator merge gate ✓ → checkpoint committed `fac090b`.

## 6. STANDING CONSTRAINTS (must persist) *(orientation: HARD RULES)*
- **Drive EVERY step via subagents** — the conductor judges liveness by **disk progress** (the diff growing), NOT a process
  snapshot. Resume a finished subagent via `SendMessage(agentId)`.
- **Commit / merge / push ONLY on explicit operator approval** — this does NOT carry across contexts; re-ask each session.
- **Snyk** on all new/changed first-party Python; fix + rescan until clean.
- Repo is **PRIVATE**; no secrets / PII. "mindbridge" in public-facing text = KataHarness.
- **The install/materialize/shadow path is STDLIB-ONLY** — never import `yaml` there (and never import `validate_skills`,
  which imports yaml).
- The **5 frozen `kata_install.py` engine functions stay BYTE-UNCHANGED** and never run git.
- Run `validate_skills.py --write` centrally BEFORE pytest when a skill/version changed (README-sync; README is
  conductor/validator-owned).
- **Decisions are SUPERSEDED with new D-numbers, never rewritten** (preserve provenance with dated notes).
- ⚠️ **Context-lean:** do NOT inline-read STATE.md / AGENTS.md; resume from DESIGN.md + PLAN.md + the orientation, drive via
  subagents.

## 7. Redaction
No secrets / keys / PII in any artifact this session. Repo is PRIVATE. Nothing to redact.
