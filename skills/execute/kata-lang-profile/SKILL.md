---
name: kata-lang-profile
description: >-
  Debug-mode language specialist pack: given the detected stack, apply the matching prose prompt-profile
  as an execute-phase overlay on kata-tdd (debug fix-loop) and kata-diagnose (diagnosis). Selection key
  is the footprint's file extensions (primary); FM derivation_sources is a weak secondary hint only. The
  overlay LAYERS via the orchestrator's dispatch — it never forks or edits kata-tdd/kata-diagnose, adds no
  Python, and is prompt guidance only (it relaxes no gate). No matching profile ⇒ no overlay (BC).
license: Apache-2.0
version: 0.1.1
category: execute
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob]
source: >-
  new (KataHarness original — Debug Mode LD10 in-mode language prompt-profiles, DESIGN §3 LD10 / PLAN-p3
  Slice D). Selection + overlay mechanism mirrors the IaC specialist-injection precedent
  (skills/coordinate/kata-orchestrate "IaC activation" block + iac_detect.classify_task); STYLE templates
  are the sibling specialists kata-iac-terraform / kata-iac-cloudformation.
tags:
  - kata/execute
  - kata/spine
  - kata/module/debug
  - language-profile
  - overlay
---

# kata-lang-profile — in-mode language specialist overlay (LD10)

You are the **selection + overlay contract** for Debug Mode's in-mode language specialists. Given the
detected stack of the codebase under debug, you point the worker at the matching **prose profile** in
`resources/`, which is injected **alongside** the worker's base discipline — `[[kata-tdd]]` for the debug
fix-loop, `[[kata-diagnose]]` for diagnosis. You add **no Python**, fork **nothing**, and gate **nothing**.

This is the **prose** half of LD10. The **injection** (reading the file-extension signal at the debug
fix-loop / diagnose dispatch and attaching the profile to the worker's launch context) is wired by the
orchestrator — see the resolved P3 seam in `skills/coordinate/kata-orchestrate/SKILL.md` (Slice W). This
skill owns *which* profile and *what it says*; the orchestrator owns *when* it is attached.

It is the exact shape of the **IaC specialist precedent**: the "IaC activation (per dispatch …) → inject
the matching IaC specialist profile alongside `[[kata-tdd]]`" block in
`skills/coordinate/kata-orchestrate/SKILL.md`, selected by `iac_detect.classify_task` (`tools/iac_detect.py`).
Where IaC injects `[[kata-iac-terraform]]` / `[[kata-iac-cloudformation]]`, debug-mode injects the matching
`resources/<lang>.md` from this pack. The STYLE of each profile follows those two sibling specialists
(DRY-by-pointer, never-tiered, prose lens — not a re-implementation of the base skill).

---

## Hard constraints

- **Overlay, never fork.** `[[kata-tdd]]` and `[[kata-diagnose]]` (the family RUBRIC + the `-light` / `-full`
  tiers) are **not edited or forked**. The profile is *additional* launch context layered on top of the
  base skill — exactly as the IaC specialist is injected *alongside* `[[kata-tdd]]`, not merged into it.
- **No new Python.** Selection reads the footprint's **file extensions directly**; there is **no new
  language classifier**, no tool to add. (Contrast the IaC path, which *does* have a deterministic
  classifier `iac_detect.classify_task` — LD10 deliberately does not, per the frozen plan.)
- **Prompt guidance, not a gate.** Profiles raise the floor on idiom, test-runner, and diagnosis quality.
  They **never** relax the **default-FAIL** verify gate or the **behavioral drift gate**, and they confer
  no confidence. A profile cannot make a finding auto-fix-eligible; only the deviation pipeline's gates can.
- **Debug-only, never-tiered.** This pack is part of the debug spine (tags `kata/spine` + `kata/module/debug`).
  Absent `kata/module/debug` it is never injected. There are no depth tiers — the profile is the same at
  every depth (the *base* skill carries the depth via its own tiers).
- **Honest scope (§5 carry-forward).** A profile is a lens, not a guarantee. It does not assert structure-
  preservation and does not calibrate confidence; those honesty contracts live in the drift gate and the
  LD12 closeout report, not here.

---

## Selection — detected stack → profile

**Primary signal: the footprint's file extensions.** The footprint of the changed/under-debug files is
always available and is the real, deterministic signal. Map the extension of the task's files to the profile:

| Detected extension(s) | Profile |
|---|---|
| `.py` | [`resources/python.md`](resources/python.md) |
| `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs` | [`resources/typescript-javascript.md`](resources/typescript-javascript.md) |
| `.java` | [`resources/java.md`](resources/java.md) |
| `.go` | [`resources/go.md`](resources/go.md) |
| `.cs` | [`resources/csharp.md`](resources/csharp.md) |
| `.rs` | [`resources/rust.md`](resources/rust.md) |
| build/config/IaC-adjacent files (e.g. `Dockerfile`, `*.toml`, `*.yaml`/`*.yml`, `Makefile`, `*.gradle`, lockfiles) | [`resources/config-context.md`](resources/config-context.md) |

**Secondary hint (weak): `derivation_sources`.** The comprehension pass's `.kata/function_models/*.json`
carry a `derivation_sources` array (`function_model.function_model_schema()`, `tools/function_model.py`).
It can corroborate the stack but is **only a weak hint** — many modules have no FM, and the FM is a
hypothesis. **`function_model_schema()` has NO `language` field**, so this skill makes **no** claim of an FM
"module language" signal. The file-extension footprint is authoritative; the FM hint never overrides it.

**Multiple stacks in one task.** A polyglot task may match more than one profile (e.g. a `.py` service with
a `Dockerfile`). Inject **each** matching profile — there is no exclusion, mirroring the IaC rule "a task may
own both IaC kinds and ordinary code." `config-context.md` is additive, not a replacement for a language
profile.

**No match ⇒ no overlay (BC).** If no extension matches a profile, or `kata/module/debug` is absent, the
worker runs **plain** `[[kata-tdd]]` / `[[kata-diagnose]]`, byte-for-byte unchanged. The absence of a
profile is never an error — it is the backward-compatible default.

---

## How the overlay is applied (worker-facing)

When the orchestrator attaches a profile to a worker, the worker:

1. Runs its **base discipline unchanged** — `[[kata-tdd]]`'s red→green→refactor + stay-in-lane for a debug
   fix, or the `[[kata-diagnose]]` feedback-loop-first method for a diagnosis.
2. **Reads the attached `resources/<lang>.md`** as a stack lens over that method: which test runner to reach
   for, the idioms that make a characterization test pin real behavior, the language's common failure modes,
   and the stack-specific diagnosis hooks.
3. Still obeys **every gate**: default-FAIL verify, the behavioral drift gate (baseline-green stays green;
   characterization snapshots stable except the Allowed Exception List), Snyk on modified code. The profile
   informs *how* to satisfy them faster; it never lowers the bar.

The profile is reference material the worker consults — it issues no commands of its own and writes no
artifacts (this skill's `allowed-tools` are read-only by design: no execution sink, consistent with the
LD10 "prose-only" posture in the frozen plan's exec-safety section).

---

## Reuse surfaces (verified — cite by name, `protocol/reuse-claims.md`)

- **IaC injection precedent** — the "IaC activation (per dispatch …)" block in
  `skills/coordinate/kata-orchestrate/SKILL.md` (injects the matching IaC specialist alongside `[[kata-tdd]]`).
  Verified real; this skill's overlay is the same dispatch-time-injection mechanism.
- **`iac_detect.classify_task`** (`tools/iac_detect.py`) — the deterministic per-task classifier the IaC
  path uses. Cited as the **precedent**; LD10 deliberately adds **no** analogous classifier (file extensions
  are read directly — no new Python).
- **`[[kata-tdd]]`** (`skills/execute/kata-tdd/SKILL.md`) — the base execute-phase discipline this overlays.
  Not edited, not forked.
- **`[[kata-diagnose]]`** (`skills/execute/kata-diagnose/` — the tier-invariant `RUBRIC.md` + the
  `-light` / `-full` tiers) — the base diagnosis method this overlays. Not edited, not forked.
- **STYLE templates** — `skills/execute/kata-iac-terraform/SKILL.md` and
  `skills/execute/kata-iac-cloudformation/SKILL.md` (never-tiered, DRY-by-pointer specialists).
- **`function_model.function_model_schema()`** (`tools/function_model.py`) — confirms the FM carries
  `derivation_sources` (weak hint) and **no `language` field**.
