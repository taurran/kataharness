---
title: kata-validate — DESIGN (FROZEN)
status: FROZEN
spec: kata-validate
tags: [kata/evaluate, validation, grounding, adversarial, conductor]
---

# DESIGN — kata-validate (the validation mini-loop)  · FROZEN

A NEW always-available skill that runs a **bounded, procedurally-driven validation mini-loop** over a supplied
payload (or another agent's output) by composing the four existing validator surfaces, then renders a
severity-ranked report with an opt-in, human-gated fix. It has its **own thin conductor** (it does NOT route
through `kata-orchestrate`). Everything below is frozen.

---

## 1. The skill (frontmatter contract)

NEW skill `skills/evaluate/kata-validate/SKILL.md`, conforming to `docs/STANDARDS.md:15-39`:

```yaml
name: kata-validate
description: >-          # trigger-rich — the ONLY thing the Claude host sees to auto-fire (STANDARDS:18-20)
  Always-available validation mini-loop. Fires on "adversarially validate this", "validate this",
  "ground this data", "check this for slop", "evaluate/score this". Composes the grounding gate,
  the kata-review adversarial rubric, kata-slop-check, and conformance scoring against a supplied
  payload OR another agent's output; returns a severity-ranked Report{passed, findings[]}. Report-only
  by default; fixes are per-finding human-gated and applied by a single writer, then re-validated once.
license: Apache-2.0
version: 0.1.0          # pre-release hold — new skills enter at 0.1.0 (STANDARDS:99-104)
category: evaluate
status: experimental
agnostic: true
cost-weight: 3          # spawn amplification — dispatches N validators + optional RS (CONTEXT.md:89-94); int 1-5 (validate_skills:130-136)
allowed-tools: [Read, Grep, Glob, Write, Edit, Bash, AskUserQuestion]   # WRITER+conductor — NOT a no-write grader
model: sonnet           # writer/build register (D59); critics route cross-family via roles (§7)
source: >-
  new (KataHarness original — validation mini-loop). Adapted patterns: Guardrails-AI on_fail propose-vs-apply
  seam; OASIS SARIF severity taxonomy (error/warning/note); Reflexion bounded self-critique loop.
tags:
  - kata/evaluate
  - kata/spine          # always-available, not a module → kata/spine is the required tag (validate_skills:187); see §10
  - validation
  - adversarial
  - grounding
```

**Why `kata/spine` and not `kata/module/<x>`.** `tools/validate_skills.py:187` requires every skill to carry
`kata/spine` OR `kata/module/<module>`. kata-validate is LOCKED always-available and explicitly **not** a
module, so `kata/spine` is the least-wrong required tag — the same recorded divergence `kata-onboard` made for
an always-available on-ramp (`skills/coordinate/kata-onboard/SKILL.md` tags; CONTEXT.md:400-405). It is *not*
claiming to run in every mode; the tag space has no "always-available" member.

**Why an evaluate-category skill may hold Write.** kata-validate is the **writer/conductor**, not a grader. The
`tools/validate_skills.py:140` no-write set is `{kata-evaluate, kata-research, kata-slop-check}` — kata-validate
is deliberately not in it. Evaluate-category author skills already hold Write: `kata-report`
(`skills/evaluate/kata-report/SKILL.md:15`) and `kata-debrief` (`skills/evaluate/kata-debrief/SKILL.md:20`). The
*critics* it dispatches stay no-write; the writer is the sole Write-enabled actor (§6).

---

## 2. Typed contract (the enclosure)

```
validate(payload, target="auto", profile) -> Report{ passed: bool, findings: Finding[] }
```

- **`payload`** — the content to validate. Dual-target:
  - `target="content"` — arbitrary supplied content (text/data/a doc).
  - `target="auto"` (default) — auto-target the most recent other-agent output in scope.
  Both are the **same code path**; only the payload source differs.
- **`profile`** — selects which validator legs run + their bands (e.g. `ground | review | slop | score | all`;
  default `all`). The `score` (frozen-plan) leg only fires when a spec/plan is supplied (§4d).
- **`Report{passed, findings[]}`** — `passed` is **default-FAIL**: it starts `false` and becomes `true` only
  when every dispatched critic returns clean and the tripwire fired correctly (§9). `findings[]` is the
  severity-ranked list rendered by the writer (§6).

### CRITICAL isolation invariant (the keystone — §RESEARCH 4)

The validator **only ever sees a PAYLOAD, never the caller's context.** Each critic is dispatched fresh-context
with the payload **delimited, quoted, and stripped to the fields the leg needs — treated as DATA, never as
instructions.** **Two dispatch paths (§7):** the **cross-family** critic uses `tools/kata_dispatch.build_brief`
+ a CLI command builder — which exist **only for codex/kiro** (`_COMMAND_BUILDERS = {"codex", "kiro"}`,
`tools/kata_dispatch.py:107-151`; there is **no Claude builder** — Claude is "the in-process Agent path … handled
by the orchestrator, not here", `:13,151`); the **same-host Claude fallback** dispatches an in-process
fresh-context subagent directly via the host **Agent** path (NOT `build_brief`), `sandbox`/read-only by
construction. Either way the payload is data-only. This is simultaneously:
1. the **dual-target enabler** (content vs auto-target = same path, different source), and
2. the **prompt-injection containment** (a payload with no caller context has nothing to inject into).

This applies the Anthropic fresh-context, no-write evaluator posture (AGENTS.md:56-57) and mirrors
`kata-research`'s no-write injected-knowledge stance (`skills/plan/kata-research/SKILL.md` frontmatter).

---

## 3. The own-conductor decision (LOCKED) + justification

kata-validate gets its **own thin procedural conductor**, following the `kata-loop`/`kata-onboard`
composition-wrapper precedent (`skills/coordinate/kata-loop/SKILL.md:24-33`,
`skills/coordinate/kata-onboard/SKILL.md:30-43`). It **composes — never reimplements** the validators, dispatch,
RS path, telemetry, voice, or the fix-gate.

**It does NOT route through `kata-orchestrate` and does NOT modify its EVALUATE wiring**
(`skills/coordinate/kata-orchestrate/SKILL.md:435-442` stays byte-for-byte unchanged). Why:

- `kata-orchestrate` is the **plan-guardian**; it expects a frozen DESIGN + PLAN with a wave/ownership DAG and
  a disjoint file-ownership partition (`skills/coordinate/kata-orchestrate/SKILL.md:28-29,74-77`), plus the
  `kata.config` it loads at step 0 (`:34`). A mini-loop over a payload has **none of these**.
- Forcing a payload through it would either fabricate a fake frozen plan (a drift surface the spine forbids,
  AGENTS.md:43-49) or fork the orchestrator's logic (the exact reimplementation the wrapper precedent rejects).
- It adds the orchestrator's full grill→freeze→execute latency for a task that must resolve **faster than a
  harness run** (LOCKED §6 mini-loop semantics).

The conductor **reuses shared primitives** (methods + tools, per §4): the validator **methods** (§4), the
subagent-brief path for cross-family critics (`tools/kata_dispatch.py`, §2/§7), the RS research **method** (the
grounding-gate routing pattern, `skills/coordinate/kata-orchestrate/SKILL.md:368-384` — applied directly, not a
worker-direct `kata-research` dispatch), `kata_banner`/`kata_board` telemetry (§8), persona / narration voice
(`protocol/persona.md`, `protocol/narration.md`), and the human-gated fix-apply pattern from `kata-closeout`
Decision-2 (`modules/closeout/kata-closeout/SKILL.md:180,40`).

---

## 4. The 4 validators — deterministic-first, METHOD-by-reference

Four surfaces, **deterministic-first ordering** (cheap/scriptable surfaces seed the verdict math before the
expensive judgment surfaces — the harness cascade, `skills/coordinate/kata-orchestrate/SKILL.md:447-449`). The
critic legs are framed **adversarially** ("list what's wrong," not "rate this" — `kata-review/RUBRIC.md:14-17`).

**REUSE = METHOD-by-reference, NOT skill/module dispatch (LOCKED — freeze-gate MAJOR 1).** The conductor does
**not** `[[wikilink]]`-dispatch the reused validator skills. It **applies their METHODS** — the slop
G1–G6/A1–A3 heuristics, the grounding/injected-knowledge rules, the 5-surface adversarial RUBRIC, the
conformance rubric — to its **own fresh-context critics** over the payload (§2). This is mandatory, not
stylistic, because two of the reused skills **self-suppress** under their own activation guards if dispatched
literally:

- `kata-slop-check` runs **only when `kata/module/slop` is in the run's modules** — "if absent, silent no-op …
  do not run it, do not report it" (`skills/evaluate/kata-slop-check/SKILL.md:5-7,39-41`).
- `kata-research` runs **only via orchestrator escalation routing (`research-needed`), never worker-direct**,
  and is gated `kata/module/research` (`skills/plan/kata-research/SKILL.md:8,21`).

A literal `[[kata-slop-check]]` / `[[kata-research]]` dispatch from this conductor would **self-no-op** (those
modules are not in a `kata.config` run here) — silently skipping the slop/grounding legs and **leaving the
tripwire unflagged** (§7-i), the exact leniency failure the tripwire exists to catch. Therefore the
**`kata/module/*` activation guard is a `kata.config`-run concept that does NOT gate this conductor.**
kata-validate is always-available (§1, not a module); it lifts the methods directly so the legs can never
self-suppress.

| # | Leg | Method applied (by reference — NOT dispatched) | Trigger phrase | Notes |
|---|---|---|---|---|
| **a** | **grounding** | `kata-evaluate` injected-knowledge rules (`skills/evaluate/kata-evaluate/SKILL.md:79-116`) + `kata-review` injected-knowledge soundness (`skills/evaluate/kata-review/RUBRIC.md:43-53`) | "ground this data" | Claims-vs-all-available-sources. Deterministic verdict math via `tools/grounding_gate.py:56-155` (`build_verdict`/`write_grounding`) → `.kata/validation/grounding.json`. When a claim needs external facts, the conductor applies the **`kata-research` method** itself on the same RS path (§5) — never a worker-direct `kata-research` dispatch (which would self-suppress per `:21`). |
| **b** | **review** | `kata-review` 5-surface adversarial RUBRIC (`skills/evaluate/kata-review/RUBRIC.md:20-41`; the `kata-review-standard` depth) | "adversarially validate this" | Findings, not fixes; SHIP/HOLD per finding. |
| **c** | **slop-check** | `kata-slop-check` G1–G6 + A1–A3 heuristics (`skills/evaluate/kata-slop-check/SKILL.md:49-189`) | "check this for slop" | SLOP-DETECTED ⇒ fail (`:212-221`). Its grep-based signals are the deterministic surface, ordered early. Method applied directly — the `kata/module/slop` guard does NOT gate this conductor (above). |
| **d** | **evaluate/score** | `kata-evaluate` conformance rubric (`skills/evaluate/kata-evaluate/SKILL.md:37-77`) | "evaluate/score this" | **Conditional:** the frozen-plan/conformance leg fires **ONLY when a spec/plan is supplied** — arbitrary content has nothing to conform to. Absent a plan ⇒ the writer renders an **explicit N/A row** ("N/A — no plan to conform to", §6 render guard), never a silent omission. |

**Deterministic-first cascade.** The pure verdict-math surfaces (`grounding_gate` verdict derivation, the new
`validation_report` severity mapping, the tripwire assertion, slop's grep signals) compute first and seed the
findings; the fresh-context LLM critics supply only the irreducibly-judgment inputs (`source_supports`,
`locked_conflict`, the adversarial findings). A leg whose deterministic surface already conclusively fails still
reports its finding (report-only collects ALL findings — it does not short-circuit the collection).

---

## 5. The mini-loop semantics (procedural, bounded ≤ 2)

Procedurally driven by the conductor (not `kata-orchestrate`):

1. **Banner** (§8) → emit "Running KataHarness validation loop…".
2. **Tripwire self-check** (§9-i) — run the validators against the known-bad corpus first; assert it is flagged.
3. **Pass 1 (validate):** dispatch the profile's legs fresh-context (payload-as-data, §2), deterministic-first.
   When the grounding leg needs external facts to verify a claim, the conductor applies the **`kata-research`
   method** itself on the same RS path as the standard loop
   (`skills/coordinate/kata-orchestrate/SKILL.md:368-384`) — not a worker-direct `kata-research` dispatch (§4).
4. **Writer renders** the severity-ranked table + `findings.json` (§6). **Default mode ends here — REPORT-ONLY.**
5. **Fix (opt-in, human-gated):** on per-finding / per-severity-band human approval (`AskUserQuestion`), the
   **writer** applies the approved fixes, then **Pass 2 (re-validate ONCE)** — bounded.
6. **Early-stop:** if a pass produces "no changes needed" / no new findings, stop before the ≤ 2 cap.

No fix ⇒ exactly one pass. Max two passes ever. This is the Reflexion bound, matching the harness thrash-budget
rationale (`skills/coordinate/kata-orchestrate/SKILL.md:465-491`) without re-using its budget machinery.

---

## 6. The WRITER role + fix-gate

The **single Write-enabled actor**. Critics stay fresh-context, no-write (spine-safe, §10). The writer:

- **Renders a severity-ranked TABLE** (markdown, SARIF-style `error | warning | info`): one row per finding,
  **severity-first**, then a **stable `finding_id`**, **location**, and a **one-line message**. The band rule:
  **"fixing it changes behavior ⇒ error"**; otherwise warning/info. **NO HTML** (unlike the closeout report).
  **N/A / skipped legs are surfaced EXPLICITLY (R4 guard, LOCKED):** any leg that did not run — above all the
  `score` leg when no plan was supplied — renders its own row (`info` severity, message **"N/A — no plan to
  conform to"** / "N/A — leg not selected"). `render_table` **never silently omits a leg**, so a skipped
  conformance leg can never read as a clean PASS.
- **Writes the machine source of truth** `.kata/validation/findings.json` — the authoritative artifact; the
  table is a view of it. (Same engine-owns-the-join discipline as `kata-debrief` driving `debug_report.py`,
  `skills/evaluate/kata-debrief/SKILL.md:56-77` — the writer **drives** the new `validation_report` engine and
  never re-derives a join in prose.)
- **Applies approved fixes** only on per-finding / per-severity-band HUMAN approval, then re-validates **once**
  (bounded). **Default REPORT-ONLY; fix is opt-in + human-gated; never blanket "fix everything"** — the
  human-gated apply mirrors `kata-closeout` Decision-2 (`modules/closeout/kata-closeout/SKILL.md:180,40`).

The deterministic table-build, severity mapping, `finding_id` derivation, and JSON emit live in a NEW pure tool
(`tools/validation_report.py`, §file-ownership) — stdlib-only, no exec sink, `..`-guarded writer (the
`tools/debug_report.py` / `tools/grounding_gate.py` precedent).

---

## 7. Safety rails (baked in)

- **(i) Tripwire fixtures.** A tiny known-bad corpus (`tools/tests/fixtures/validation_tripwire/`) the loop MUST
  flag on **every** run. The conductor runs the validators against it first (§5.2); if it ever passes clean the
  validator is broken (catches "silently passes everything" / leniency bias). A clean tripwire ⇒ STOP + a
  breakthrough-alert to the human (`protocol/narration.md:69-92`) — never a silent pass. The corpus +
  `validation_report.tripwire_corpus()` / `assert_tripwire_flagged()` are engine-owned and unit-asserted.
- **(ii) Cross-family judge.** The critic model differs from the writer model (defeats self-collusion +
  injection). Reuses the wired multi-model role routing (`protocol/config.md:28` `roles`; validator→codex is
  LIVE-proven, CONTEXT.md:472-484) via `tools/kata_dispatch.build_brief(role="validator", ...)` + the **codex**
  command builder — `build_brief`/the CLI builders are the **off-host (codex/kiro) path only**
  (`_COMMAND_BUILDERS = {"codex", "kiro"}`, `tools/kata_dispatch.py:107-151`; no Claude builder, `:13,151`).
  **Honest fallback:** roles unconfigured ⇒ same-host Claude critics dispatched fresh-context via the in-process
  **Agent** path (not `build_brief`) — same model family as the writer, so the anti-collusion guarantee is
  **explicitly weaker** and must be stated plainly (no implied collusion-proofing that isn't wired —
  `protocol/persona.md:54-59`).

---

## 8. Branded run banner

A punchy, deterministic **"Running KataHarness validation loop…"** marker shown whenever the loop runs
(marketing-visible that the tool is working). It follows the `kata_banner` pattern — tool-rendered,
byte-identical, closeout-report palette (`tools/kata_banner.py:21-50,57-116`; `protocol/narration.md:125-148`).

Implemented as a NEW additive function `render_validation_banner()` in `tools/kata_banner.py` (the canonical
banner home), reusing the existing `_PALETTE` / `_paint` primitives — **no new palette, no duplication**. The
conductor invokes it as a command so the terminal renders color (the `kata-loop` banner-emit precedent,
`skills/coordinate/kata-loop/SKILL.md:54-69`).

---

## 9. Telemetry reuse

The conductor emits to the existing primitives (no new telemetry surface):

- `tools/kata_board.append_event` (`tools/kata_board.py:60-99`) — board events for the validation pass
  (CLAIM/DONE/NOTE per leg). Single-writer rules honored.
- `tools/grounding_gate.write_grounding` (`tools/grounding_gate.py:130`) — the grounding leg's machine verdicts.
- `tools/validation_report.emit_findings` (NEW) — `.kata/validation/findings.json`.

Run artifacts live under `.kata/validation/` (gitignored run state, like every `.kata/` artifact).

---

## 10. Invariants it MUST hold (spine-safe / don't-break)

1. **Critics fresh-context, no-write.** Each critic applies a no-write validator **method** (§4: `kata-evaluate`,
   `kata-review`, `kata-slop-check`, `kata-research` rules) over the payload, dispatched with no Write; the
   conductor adds no Write to any critic. The no-write set in `tools/validate_skills.py:140` stays unchanged and
   green (kata-validate is not in it; the writer (§6) is the sole Write-enabled actor).
2. **Default-FAIL preserved.** `Report.passed` starts `false`; clean only when every leg clears AND the tripwire
   fired (§2, §7). SLOP-DETECTED / HOLD / REJECT / ESCALATE ⇒ `passed=false`.
3. **`kata-orchestrate` untouched.** No edit to its EVALUATE wiring or any other section (§3).
4. **Persona / narration respected.** No internal stage names surfaced (`protocol/persona.md:46-48`); the
   human-approval gate, a broken tripwire, and an injection-detected payload each fire a **breakthrough-alert**
   immediately and unmissably (`protocol/narration.md:69-92`). Voice via `protocol/persona.md` throughout.
5. **Isolation invariant** (§2) — payload-as-data, never caller context.
6. **No phantom reuse.** Every cited surface resolves to a real skill/symbol (`protocol/reuse-claims.md`); the
   `score` leg honestly N/A on arbitrary content; cross-family is exercised-not-proven when unconfigured.

---

## 11. Per-platform trigger story

- **Claude (built, v0.1).** The host decides invocation purely from the `description` frontmatter
  (`docs/STANDARDS.md:18-20`). The natural-language triggers ("adversarially validate this", "validate this",
  "ground this data", "check this for slop", "evaluate/score this") live in the description and auto-fire it.
- **Codex / Kiro (adapter seam, not built here).** These hosts do not description-match the same way; their
  trigger mechanisms are mapped through `adapters/<tool>/` (spine #3 — adapters normalize skill-definition
  format + trigger surface, AGENTS.md:53-55, `docs/STANDARDS.md:118-122`). v0.1 is the Claude-only core
  (AGENTS.md:86-88); the Codex/Kiro trigger mapping is documented as the seam, deferred to those adapters.
- **`[[kata-validate]]` as a referent.** Other skills that need validation reference `[[kata-validate]]`
  (resolves via `tools/validate_skills.py:370-377`). Wiring those references into other skills is a **future,
  optional** step — NOT part of this build (no other skill is edited in this freeze).

---

## 12. File-ownership map (NEW vs REUSED — honestly labeled)

**NEW files (this build authors them):**

| File | Kind | Role |
|---|---|---|
| `skills/evaluate/kata-validate/SKILL.md` | NEW skill | The conductor + writer prose; composes the four legs by reference. |
| `tools/validation_report.py` | NEW pure tool | Findings schema + `finding_id` derivation + SARIF severity mapping + markdown-table render + `emit_findings`/`load_findings` (`.kata/validation/findings.json`) + `tripwire_corpus()`/`assert_tripwire_flagged()`. Stdlib-only, no exec sink, `..`-guarded. |
| `tools/tests/test_validation_report.py` | NEW tests | TDD + mutation-proof for the engine. |
| `tools/tests/fixtures/validation_tripwire/` | NEW fixtures | The tiny known-bad corpus (one payload per leg) the loop MUST flag every run. |

**ADDITIVE edits (single-function, disjoint slices):**

| File | Edit |
|---|---|
| `tools/kata_banner.py` | Add `render_validation_banner()` (reuses `_PALETTE`/`_paint`; §8). + its test. |
| `README.md` | Mechanical skill-index regen via `validate_skills.py --write` (generated columns only; `tools/validate_skills.py:286-297` enforces sync). |

**REUSED (METHODS by reference — NOT dispatched, NOT modified):** the `kata-evaluate` /
`kata-review`(-standard) / `kata-slop-check` / `kata-research` **methods** (§4 — applied to fresh-context
critics, never literal skill/module dispatch); `tools/grounding_gate.py`, `tools/kata_dispatch.py` (codex/kiro
brief path only), `tools/kata_board.py`, `tools/kata_roles.py`; `protocol/persona.md`, `protocol/narration.md`,
`modules/closeout/kata-closeout/SKILL.md` (fix-gate pattern). **`kata-orchestrate` is explicitly NOT touched.**
