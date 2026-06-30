# KataHarness — NEXT-SESSION ORIENTATION (D131 model-tiering — SHIPPED · next: backlog Kata Loop cycles)

## 0. WHO / WHERE
- Project: KataHarness — tool-agnostic, skills-based agent harness ("the Kata Loop"). Dir `C:\Dev\Projects\KataHarness`.
- Git: private remote github.com/taurran/kataharness. `master`, tip **`fac090b`** (D131 model-tiering — SHIPPED + PUSHED +
  in sync). The D131 spec docs in `.planning/specs/model-tiering/` are **COMMITTED** (commit `fac090b`).
- You are the **conductor**: pick next backlog item → grill/freeze/plan → orchestrate subagents → gate → merge. Do NOT build inline.
- ★ OPERATOR DIRECTIVE: drive every step via subagents to spare main context. Resume a finished subagent with
  `SendMessage(agentId)`. Judge subagent liveness by **DISK PROGRESS** (the diff growing), NOT a process snapshot.
- ★ **STAY CONTEXT-LEAN: do NOT inline-read `.planning/STATE.md` or `AGENTS.md`.** Resume from `.planning/BACKLOG.md` +
  this file + the relevant spec docs for the chosen item only.

## 1. WHERE WE ARE — D131 model-tiering COMPLETE · next: backlog Kata Loop cycles
**Feature shipped:** D131 — **relative, mode-driven model selection.** At dispatch, resolve the model as a **differential
off the operator's current session model (the anchor)**; never a hard-baked `model:` ID. Implements the `CLAUDE.md` D59
note. Built on **D130** (`8af2e37`). Commit **`fac090b`** pushed to master.

**Loop position (exact):** D131 **COMPLETE**. All waves (W1–W3) built and gated. Integration gate green (pytest 2126
pass / 2 skip / 0 fail · validate 47/0 WITH the A1 guard · Snyk medium+ 0). LIVE PROOF passed. D98 adversarial sweep
passed — caught and fixed 2 real defects (advanced/coding coder-floor not gated to essential; full-id anchor silently
disabling tiering). Committed `fac090b`, pushed master. **Next: series of new Kata Loop cycles over the backlog toward v0.1.**

**Artifacts COMMITTED in `.planning/specs/model-tiering/`:** `ASSESSMENT.md` (pre-grill input), `DESIGN.md` (frozen
charter, R1–R8 baked in), `PLAN.md` (wave DAG + disjoint file-ownership). Two standing items in play: (a) `kata_install.py`
17 LOW CWE-23 hardening; (b) benchmark v1 n=0 → live with a real control fixture.

## 2. ★ FIRST ACTION — pick the next item from the backlog and start a new Kata Loop cycle
Read `.planning/BACKLOG.md` (+ this file). Then:

> **Pick the next backlog item** (the conductor chooses priority with the operator, or defaults to the top of the
> backlog queue). For each item, run the full inner loop: **grill** (kata-grill, Opus) → **freeze** (design doc) →
> **freeze-gate** (kata-review, Opus; expected SHIP) → **orchestrate build** (subagents, disjoint ownership, TDD) →
> **integration gate** (pytest · validate · Snyk) → **LIVE PROOF** → **D98 adversarial sweep** → **operator merge gate**.

Two standing items to schedule at appropriate points: (a) `kata_install.py` 17 LOW CWE-23 hardening (CWE-23
path-traversal class, below medium+ gate); (b) benchmark v1 n=0 → live with a real control fixture.

## 3. THE RESOLVED LEDGER (R1–R8) + the resolver contract — carry verbatim (zero re-derivation)
- **R1 coder-floor:** invariant `essential-coding ≤ standard-coding ≤ anchor`; `coder_floor` raises a tier only when
  `floor_index ≤ anchor_index−1`. The −2 win lands at a fable/top anchor (→sonnet). Unit-tested as a full anchor×mode matrix.
- **R2 fallback:** never string-match; ANY dispatch failure on a NON-INHERITED model steps down, EXCEPT HTTP **401/403**
  (auth/quota) which RAISE. Terminus = **OMIT** the model param (host default), never inherit-anchor. **≤2 step-downs** then omit.
- **R3 BC:** omitting Agent `model` inherits the session model — CONFIRMED for the Claude host (v0.1 Claude-only core).
- **R4 ladder:** PLAIN STRING lists. Anthropic = `[haiku, sonnet, opus, fable, mythos]`; fable & mythos DISTINCT (mythos =
  higher, gated → the live-fallback test). IDs (`claude-haiku-4-5`/`-sonnet-4-6`/`-opus-4-8`/`-fable-5`/`-mythos-5`)
  DATA-verified at build; OpenAI/Gemini = shape only, IDs re-pulled at build.
- **R5 work-class coverage:** the map must EXPLICITLY classify ALL ~47 loaded skills (`skills/` + 3 `modules/` skills, via
  `load_skills`) as `critical|coding|economy`. `unknown→critical` default for genuinely-new skills only.
- **R6 architecture:** ladders = DATA registry in core `tools/kata_models.py`, extensible via `kata.config.models` (NOT an
  adapter indirection; precedent: `kata_dispatch` carries codex/kiro in core).
- **R7 anchor:** anchor = operator session model. Zero-step cells inherit by omission (`None`). Only below-anchor cells need
  the anchor NAME (`kata.config.models.anchor`, default = platform latest top rung). Stale anchor mis-tiers economy COST
  only, never critical correctness. Bootstrap/initiate sets/confirms it.
- **R8 guard + minors:** validator A1 hard-fail scoped to `SKILL.md` frontmatter ONLY (adapters/config MAY pin). Fallback
  cap ≤2. essential "other economy" = anchor−1 (==standard); essential's savings = critical→anchor−1 + coding→anchor−2-floored.

**★ CRITICAL RESOLVER CONTRACT (freeze-gate fix — MUST hold):** `resolve()` returns **`None`** (=OMIT→inherit) when
resolved rung index **== anchor_index** (step==0); returns an explicit **id string** ONLY for a rung **strictly below**
anchor (step<0). Determinant = **STEP-COUNT, not work-class** → essential-critical (=anchor−1) returns an explicit id;
advanced cells + standard-critical return `None`.

**MODE→MODEL (critical / non-critical-coding / other-economy):** advanced = anchor/anchor/anchor · standard =
anchor/anchor−1/anchor−1 · essential = anchor−1/anchor−2(coder-floored)/anchor−1.

## 4. THE BUILD WAVE DAG — D131 SHIPPED `fac090b` (historical record; next cycle: see BACKLOG.md)
- **W1 (parallel, disjoint OWNS):**
  - **W1-A** `tools/kata_models.py` + `tools/tests/test_kata_models.py` — resolver, ladders, `fallback_chain`, R1 matrix test.
  - **W1-B** `tools/validate_skills.py` + `tools/tests/test_validate_model_guard.py` + `docs/STANDARDS.md` — the A1 guard.
  - **W1-C** `update.ps1` — bare `exit`→`throw`/`$global:LASTEXITCODE` (same `iex` bug as `install.ps1`).
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
  **LIVE PROOF** ✓ → **D98** adversarial sweep ✓ (caught + fixed 2 real defects: advanced/coding coder-floor not gated to
  essential; full-id anchor silently disabling tiering) → operator merge gate ✓ → checkpoint committed `fac090b`.
- **Final baseline:** validate **47/0** WITH the A1 guard; pytest **2126 pass / 2 skip / 0 fail**; Snyk med+ 0
  (`kata_install.py` 17 LOW CWE-23 below gate — STANDING item).

## 5. HARD RULES
Drive EVERY step via subagents (conductor judges liveness by **disk progress**, not a process snapshot; resume finished
ones via `SendMessage(agentId)`) · commit/merge/push ONLY on explicit operator approval (does NOT carry across contexts) ·
Snyk on all new/changed first-party Python, fix + rescan until clean · repo PRIVATE, no secrets/PII · "mindbridge" in
public-facing text = KataHarness · the install/materialize/shadow path is **STDLIB-ONLY** (never import `yaml` there, never
import `validate_skills`) · the **5 frozen `kata_install.py` engine fns stay BYTE-UNCHANGED + never run git** ·
`validate_skills.py --write` centrally BEFORE pytest when a skill/version changed (README conductor/validator-owned) ·
decisions SUPERSEDED with new D-numbers, never rewritten · IGNORE `C:\Dev\CLAUDE.md` (Mise — unrelated). Routing:
judgment/plan/eval/grill/D98/re-confirm = **Opus**; build/encode/workers = **Sonnet**.

## 6. THE RECIPE (the inner build loop — never inline)
grill/plain → freeze → freeze-gate `kata-review` (HOLD/SHIP) → orchestrated build (subagents, disjoint ownership, TDD,
mutation-proof) → integration gate (pytest + validate 47/0 + Snyk + central README `--write`) → **LIVE PROOF** (the model
actually changes per mode) → fresh-context `kata-evaluate` (PART A, default-FAIL) → standing **D98** `kata-review` (PART B,
adversarial) → re-confirm after fixes → operator merge gate → checkpoint (new D-number). **[YOU ARE HERE: D131 COMPLETE at
`fac090b`; start the next cycle from BACKLOG.md.]** ★ Load-bearing (D124 — confirmed live on D131): unit tests + PART A
CANNOT see built-but-unwired / cross-seam gaps — the LIVE PROOF + D98 adversarial sweep are mandatory gates, not ceremony.
Honesty: "exercised (n=1) ≠ proven." Supersede-never-rewrite.
