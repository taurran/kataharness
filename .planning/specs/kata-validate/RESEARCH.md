---
title: kata-validate — RESEARCH (grill-resolved approach + transferable patterns)
status: FROZEN
spec: kata-validate
tags: [kata/evaluate, validation, grounding, adversarial, research]
---

# RESEARCH — kata-validate (the validation mini-loop)

> The grill is **COMPLETE**. Every fork below is **RESOLVED** and LOCKED by the operator. This file records
> *why* the resolved shape is right and the transferable patterns it stands on. It does not re-open anything.
> Build follows `DESIGN.md` + `PLAN.md`; nothing here is a decision still in play.

## 1. The problem this resolves

KataHarness already owns four strong validation surfaces, but they only fire **inside** the harness's EVALUATE
phase, on a *built phase* graded against a *frozen plan* (`skills/coordinate/kata-orchestrate/SKILL.md:435-442`,
`skills/evaluate/kata-evaluate/SKILL.md:25-30`). There is **no first-class way to point that same rigor at an
arbitrary piece of content** — "adversarially validate this", "ground this data", "check this for slop",
"score this" — outside a full grill→freeze→execute run. `kata-validate` is that go-to: a thin **mini-loop**
that composes the existing validators against a supplied payload (or another agent's output), resolves faster
than a full harness run, and returns a severity-ranked report with an opt-in, human-gated fix.

## 2. Resolved forks (all RESOLVED — do not relitigate)

| Fork | Options weighed | **RESOLVED** | Why (rationale, grounded) |
|---|---|---|---|
| **Orchestrator** | route through `kata-orchestrate` vs own thin conductor | **Own thin conductor** | `kata-orchestrate` expects a frozen DESIGN/PLAN with a wave/ownership DAG + disjoint file-ownership partition (`skills/coordinate/kata-orchestrate/SKILL.md:28-29,74-77`), plus the `kata.config` it loads at step 0 (`:34`), that a mini-loop simply lacks. Forcing a payload through it risks the no-drift spine (AGENTS.md:43-49) and adds latency for zero benefit. The thin-composition-wrapper precedent is `kata-loop`/`kata-onboard` (`skills/coordinate/kata-loop/SKILL.md:24-33`, `skills/coordinate/kata-onboard/SKILL.md:30-43`): compose existing skills, reimplement nothing. |
| **Availability** | off-by-default `kata/module/*` toggle vs always-available | **Always-available (NOT a module)** | It is the SYSTEM go-to for validation. A module would hide it behind `kata.config.modules` opt-in (`protocol/config.md:106-110`) and a load-guard. Always-available means other skills can lean on `[[kata-validate]]` and the host auto-fires on natural-language triggers via the `description` field (`docs/STANDARDS.md:18-20`). |
| **Default mode** | fix-everything vs report-only | **Report-only default; fix opt-in + human-gated** | Mirrors the project's never-silent-fix posture: validators produce *findings, not fixes* (`skills/evaluate/kata-review/RUBRIC.md:14-17,83-85`). A blanket auto-fix is exactly the drift the spine forbids (AGENTS.md:46-49). Fix is per-finding / per-severity-band HUMAN-approved, then re-validated once. |
| **Who fixes** | a validator applies its own fix vs a separate writer | **A single WRITER (sole Write-enabled actor)** | Keeps every critic fresh-context, no-write (spine-safe; `docs/STANDARDS.md:51-54`, validator set pinned in `tools/validate_skills.py:140`). A critic that edits is structurally misconfigured (`skills/evaluate/kata-slop-check/SKILL.md:31-33`). The writer is the only actor holding Write/Edit — same split as `kata-report`/`kata-debrief` (evaluate-category authors that hold Write: `skills/evaluate/kata-report/SKILL.md:15`, `skills/evaluate/kata-debrief/SKILL.md:20`). |
| **Iteration bound** | unbounded refine vs bounded | **Bounded ≤ 2; early-stop on "no changes needed"** | A validation pass is not a build; it must resolve fast. Bounded loops defeat thrash (the harness fix-loop already runs a thrash budget for the same reason — `skills/coordinate/kata-orchestrate/SKILL.md:465-491`). Pass 1 = validate; pass 2 = re-validate after an approved fix. No fix ⇒ one pass. |

## 3. Transferable patterns (the shoulders we stand on — provenance required, AGENTS.md:82)

- **LLM-as-judge, decomposed rubric.** Don't ask one model "is this good?"; decompose into independent,
  evidence-citing attack surfaces. This is exactly `kata-review`'s 5-surface RUBRIC
  (`skills/evaluate/kata-review/RUBRIC.md:20-41`) and `kata-evaluate`'s 9-item rubric
  (`skills/evaluate/kata-evaluate/SKILL.md:37-77`). kata-validate **reuses these by reference**, never
  re-authors them.
- **Deterministic-first cascade.** Run the cheap, scriptable surfaces before the expensive judgment ones; a
  red deterministic gate never wastes a fresh-context judge. Lifted verbatim from the harness fix-loop cascade
  (`skills/coordinate/kata-orchestrate/SKILL.md:447-449`). The deterministic *verdict math* stays in pure
  tools (`tools/grounding_gate.py:56-127`, the new `validation_report` engine); the LLM supplies only the
  irreducibly-judgment inputs (`source_supports`, `locked_conflict`).
- **Guardrails `on_fail` propose-vs-apply seam.** `source:` Guardrails-AI `on_fail` policy (reask / fix /
  filter / exception). We adopt the *propose-then-apply* seam: the validator **proposes** a severity-ranked
  set of findings (report-only); applying any fix is a **separate, human-gated** act by the writer. Never the
  guardrail's silent auto-`fix`.
- **SARIF severity taxonomy.** `source:` OASIS SARIF (`level: error | warning | note`). The findings table and
  `findings.json` rank by a three-band severity with one decision rule: **"fixing it changes behavior ⇒
  error"**; otherwise warning/info. Aligns with the project's existing BLOCKER/MAJOR/MINOR + slop
  critical/major/minor bands (`skills/evaluate/kata-slop-check/SKILL.md:201-210`) — the engine maps between them.
- **Reflexion bounded loop.** `source:` Reflexion (Shinn et al.) — a self-critique→revise loop with a hard
  iteration cap so it converges instead of spiraling. We bound at ≤ 2 with early-stop, the anti-spiral the
  project already enforces in its thrash budget and slop checks (G1/G3, `skills/evaluate/kata-slop-check/SKILL.md:54-87`).
- **Tripwire fixtures (leniency guard).** A tiny known-bad corpus the loop MUST flag on **every** run. If it
  ever passes clean, the validator is broken — this catches the "silently passes everything" / leniency-bias
  failure that a default-FAIL gate exists to prevent (`skills/evaluate/kata-evaluate/SKILL.md:29-30`). Original
  to KataHarness; conceptually a canary/smoke-fixture.
- **Cross-family judge (anti-collusion).** The critic model differs from the writer model, defeating
  self-collusion and prompt-injection. Reuses the already-wired multi-model role routing
  (`protocol/config.md:28` `roles`; validator→codex is LIVE-proven, D121 / `CONTEXT.md:472-484`). Falls back to
  fresh-context same-host with an honestly-weaker guarantee when roles are unconfigured.

## 4. Isolation as the keystone (both a feature and a containment)

The single design move that makes the dual-target contract *and* the prompt-injection containment work is the
same: **the validator only ever sees a PAYLOAD, never the caller's context.** Each critic is dispatched
fresh-context with the payload **delimited, quoted, and stripped to the needed fields — treated as data, never
as instructions.** This is the fresh-context, no-write evaluator pattern (Anthropic; AGENTS.md:56-57) applied
to validation, and the same posture `kata-research` takes on injected knowledge
(`skills/plan/kata-research/SKILL.md` frontmatter, no-write + escalation-routed). Because the critic has no
caller context, "validate arbitrary content" and "auto-target another agent's output" are the *same code path*
with a different payload source — and a payload that tries to inject instructions has nothing to inject into.

## 5. Honest scope (exercised-vs-proven discipline, CONTEXT.md:256-260)

- The cross-family judge guarantee is only as strong as the multi-model install for the run. With roles
  configured it routes off-host (validator→codex LIVE n=1); unconfigured ⇒ fresh-context same-host fallback —
  state that plainly, never imply collusion-proofing that isn't wired.
- v0.1 is the Claude-only core (AGENTS.md:86-88). The Claude trigger story (description-match auto-fire) is the
  built path; Codex/Kiro trigger mapping is the documented **adapter seam** (spine #3, AGENTS.md:53-55), not
  built here.
- The mini-loop is **exercised** on fixtures at build (tripwire + unit/e2e); calling it "proven" before a real
  regression corpus runs is itself the inflation slop signal the harness catches (`protocol/persona.md:54-59`).
