---
title: "WS-3 — User-friendliness (front-to-end UX): frozen DESIGN"
status: DESIGN (brainstormed 2026-06-24; freeze-gate kata-review + operator review pending before PLAN)
date: 2026-06-24
scope: project
supersedes-framing: >-
  Refines (does not reverse) the kata-initiate S2 hard-STOP gate presentation; folds BACKLOG WS-3 + WS-4 + WS-5.
source: >-
  brainstorm grounded in research/ Hermes (Nous) agent-harness UX + Devin Interactive Planning + Claude Code
  TodoWrite/Plan-mode legibility (digest in this session); operator UX-taste decisions Q1–Q6 (2026-06-24).
tags:
  - kata/spec
  - ws3
  - ux
  - user-friendliness
---

# WS-3 — User-friendliness, front-to-end (frozen DESIGN)

## 1. Why

The whole system is technically strong but **machine-shaped**. The WS-2 audit (`specs/ws2-loop-autonomy/AUDIT.md`
§4) is blunt: KataHarness **leads on rigor, trails on lived UX**. WS-5 was born from a real owner reaction —
*"I had no idea what changes were made."* WS-3 is the last workstream gating public release; **WS-4** (offered
backout) and **WS-5** (closeout change-transparency) fold into it.

This DESIGN makes the human-facing surfaces — **intake, the decision tree, in-loop narration, and closeout** —
legible, warm, and goal-anchored, **without** weakening any spine invariant (default-FAIL, no-drift,
no-self-cert, two-way handoff) and **without** faking capabilities that are gated off today.

## 2. Audience & success criteria

- **Primary audience (L1):** a **moderate non-expert owner** by default — someone who owns the *goal* but
  can't read the diff. Plain-language, warm, legible by default.
- **Adaptation (L1):** the persona + the learning path **progressively dial the register** toward the user's
  real sophistication *as it learns them* — **but see L8 (honesty): this ships as a default + a named seam,
  not wired adaptivity in v0.1.**
- **Success:** a non-expert can (a) state a goal and recognize it in the agent's reflected-back understanding;
  (b) trust a long run is progressing without watching logs; (c) read the closeout and know **what changed and
  why it matters to them**, what's uncertain, and how to **undo it** — in one screen, in plain language.

## 3. LOCKED design decisions (promote to DECISIONS D95+ at freeze/build; no worker may re-decide — conflict ⇒ escalate)

- **L1 — Default register = moderate non-expert; register-adaptation is a learned dimension.** The baseline
  voice is plain-language/warm; sophistication adapts over time via the persona + LEARN-fed seam (L8).
- **L2 — Persona = the calm kata-craftsperson-who-translates.** 改善型 patience and precision, but **always**
  renders "what I did and why it matters to you" in plain language. Warm through clarity, never chatty or
  kawaii. Calm gravity fits judgment work; the translator instinct serves the non-expert default. Carried by a
  new agnostic **persona/SOUL contract** (`protocol/persona.md`) + in-skill voice notes. **Nameless** — it is
  the harness's own voice, not a named mascot (resolved §9; a named character risks reading unserious against L2).
- **L3 — Intake = the reflective goal mirror (infer-then-confirm).** `kata-initiate`'s front is re-framed: the
  agent **synthesizes** system-prompt + brief + light research + grill into a plain-language *"here's what you
  want / what success looks like / how I'd set it up,"* reflects it back, and the user **edits conversationally
  until confirmed** — *then* `INTENT.md` is frozen.
- **L4 — Intake-gate refinement (NOT a reversal of the S2 hard-STOP).** The `kata-initiate` STOP gate's
  *requirement* — **every frozen answer (kind/target/vault/platform/grillDepth/goal) traces to an explicit human
  confirmation, never a silent inference** — is **preserved**. Only its *presentation* changes: from a naked
  config form to **infer-then-confirm** (the agent proposes config in human terms inside the mirror; the human
  confirms/corrects). The evaluator gate-checklist in `kata-initiate` is rewritten to verify *confirmation*, not
  *form-asking*. This is a deliberate, audited refinement of the S2 anti-drift fix — recorded, not silent.
- **L5 — Mode surface = infer + state-in-plain-language + one dial + advanced drawer.** `kata-bootstrap`'s
  surface is re-framed: infer run-shape + mode + grill-depth + delivery from the goal, state it in plain outcome
  language, surface **exactly one** plain dial ("how careful / how often should I check with you"), and hide the
  full composition ladder behind an **advanced drawer**. **The dial maps onto existing `kata.config` fields —
  `mode` + `tiers["kata-grill"]` (grill-depth) + `delivery.boundary`** (no new field; resolved §9): more careful
  ⇒ higher mode + deeper grill + `always-stop`; lighter ⇒ lower mode + lighter/skip grill. `kata.config` and the
  underlying machinery are **unchanged** — this is a presentation layer over the existing configurator.
- **L6 — Narration = milestone + breakthrough alerts; the dashboard stays the firehose.** In the host
  conversation: plain-language narration at meaningful boundaries, quiet between, with a phase→plain-language map
  (`protocol/narration.md`). **Internal stage names (GRILL/FREEZE/…) are never surfaced.** The `改善型`
  dashboard/statusline/web viewer remain the granular live view for whoever wants to watch. **Invariant:**
  anything needing the human — a decision/escalation or a critical failure — **breaks through into the
  conversation immediately and unmissably**, regardless of routine quiet (the Hermes floating-alert backstop,
  adapted). This breakthrough invariant is **never tiered** (D33-class).
- **L7 — Closeout = goal-anchored, by-goal-aspect topic synthesis.** `kata-closeout` + `kata-report` re-framed to
  a fixed skeleton (§5). It **leads with plain-language what-changed-and-why** (before any path or gate number —
  the WS-5 hard requirement), organizes the change story **by the goal-aspect each change served** (adapting
  Hermes by-topic synthesis; each parallel worker's result folds into the goal-aspect it serves), assesses
  progress against the **restated goal**, surfaces **risks + uncertainties** (incl. *exercised-not-proven*
  honesty), links evidence rather than dumping it, and **offers a first-class plain-language backout** (L9). It
  doubles as a **re-entry briefing** (designed against Devin's known re-entry-context-loss failure).
- **L8 — Honesty: adaptive register ships as default + named seam, NOT wired.** Learning-between-loops is gated
  off by design today (β LEARN feed emit-only, D74; engram CONSULT gated, D9/D56). v0.1 therefore ships the
  **moderate-non-expert default for real** plus a **default-safe register-adaptation seam** — a new `engram`
  seam row + a config dial defaulting to the moderate register, fed by the D72 grill-ledger LEARN feed, lit up
  **later** when CONSULT matures (the pattern RS and `engram.autonomy` already use). **Claiming adaptive register
  is live when it is a default + a seam is itself an inflation slop signal (the thing `kata-slop-check` catches)
  — forbidden.**
- **L9 — Backout (WS-4) is a first-class, offered, plain-language option at the human gate.** Every run's
  closeout names — in plain words — "I can cleanly roll this entire run back, as if it never happened," wired to
  the existing `pre-<run>` backout tag. Always present and named; foregrounded when the human is not satisfied.
  Never a buried git incantation.
- **L10 — Spine invariants are untouched.** default-FAIL (`kata-evaluate` still gates; closeout never gates),
  no-drift, no-self-certification (L8), two-way file handoff, everything-versioned all hold. WS-3 changes
  *presentation and voice*, not the quality machinery.
- **L11 — Mostly-markdown, low code surface.** The change is predominantly skill-authoring + two new markdown
  contracts + one light config field/engram row. No new detection/UX Python engine (prefer-in-context; keeps the
  agnostic-core bias). Any code is confined to a config-field addition + its validator/test if needed.

## 4. Architecture

Two new agnostic contracts + a re-frame of the existing UX surfaces + one default-safe seam. **No parallel
"UX-layer" skill** — the voice and legibility live *in* the surfaces the user already meets, keeping the spine
coherent.

### 4.1 New agnostic contracts
- **`protocol/persona.md`** — the SOUL: **Identity / Style / Avoid / Defaults** (Hermes `SOUL.md` structure). The
  single source of voice; the agnostic body, rendered into each platform's instruction file by the adapter
  (Claude→CLAUDE.md/AGENTS.md; others per their adapter). Skills reference it; they do not re-author voice.
- **`protocol/narration.md`** — the **phase→plain-language map**: for each loop activity (grill / freeze /
  preflight / execute / evaluate / handoff / escalation / loop-back) a human-action phrasing the narrator uses,
  plus the milestone cadence rule and the breakthrough-alert rule (L6).

### 4.2 Re-framed surfaces
| Surface | Change | Owns |
|---|---|---|
| [[kata-initiate]] | front re-framed to the reflective goal mirror (L3); gate-checklist → confirm-not-form (L4) | the intake mirror |
| [[kata-bootstrap]] | surface re-framed to infer + plain-language + one dial + advanced drawer (L5) | the mode surface |
| [[kata-orchestrate]] | milestone narration + breakthrough alerts emitted to the conversation (L6); reads `narration.md` | in-loop narration |
| [[kata-closeout]] + [[kata-report]] | goal-anchored by-aspect synthesis skeleton (L7) + offered backout (L9) | the closeout |

### 4.3 The register-adaptation seam (L8 — default-safe, named, not wired; **reuses existing mechanisms, no new config field**)
- **No new config field** (resolved §9). The moderate-non-expert register is a **static default stated in
  `protocol/persona.md`** (the Defaults section). Adaptation is the **engram seam**, not a UX config knob.
- A new row in `protocol/engram.md` (next E-id) declaring: LEARN surface = the user's observed
  comprehension/correction signals + grill-ledger choices (D72); latent CONSULT = adjust the persona register
  from the matured fingerprint. **Gated off** (D9/D56) — emit/observe only, zero CONSULT, like every other
  engram seam. The seam is the future read/write site; v0.1 has no live register-setting path.

## 5. The closeout skeleton (L7 detail) — fixed order

1. **Goal, restated** — plain language, from frozen `INTENT.md`: "You wanted X."
2. **What changed & why it matters to you** — plain language, **first**, organized **by goal-aspect**: "To give
   you X, I built… / To handle Y, I changed…". No file paths or gate numbers in this section.
3. **Did it hit the goal?** — honest assessment against the restated goal: fully / partially / here's the gap.
4. **Risks & uncertainties** — what's not fully sure, what is *exercised-not-proven*, what could bite.
5. **Evidence, linked not dumped** — gate result (`.kata/RESULT.json`), the report, the understand-map,
   findings files — for whoever wants to dig.
6. **Your options, as plain choices** — keep it (commit/push/merge, the existing human-gated git actions),
   iterate (run again / version-up), or **cleanly undo the whole run** (L9 backout). Foregrounded when the human
   is not satisfied.

`kata-closeout` still **never gates** (L10); `kata-evaluate`'s verdict is read verbatim and surfaced — a
NEEDS_WORK is reported plainly, never overridden.

## 6. Slice DAG (disjoint ownership — seeds the orchestrated build PLAN)

| Slice | Owns (files) | depends_on | Code-bearing? |
|---|---|---|---|
| **A — persona + register seam** | `protocol/persona.md` (incl. the moderate default), `protocol/engram.md` (+1 row) | — | no |
| **B — narration map** | `protocol/narration.md` | — | no |
| **C — intake mirror** | `modules/initiation/kata-initiate/SKILL.md` | A | no |
| **D — mode surface** | `skills/coordinate/kata-bootstrap/SKILL.md` (+ `resources/run-shapes.md` if needed) | A | no |
| **E — milestone narration** | `skills/coordinate/kata-orchestrate/SKILL.md` | A, B | no |
| **F — goal-anchored closeout** | `modules/closeout/kata-closeout/SKILL.md`, `skills/evaluate/kata-report/SKILL.md` | A | no |

Ownership is disjoint (A is the only slice touching `persona.md`/`engram.md`; D is the only one touching
`kata-bootstrap`, etc.). Wave 1 = {A, B}; wave 2 = {C, D, E, F} once A (and B for E) integrate. **The whole
spec is non-code-bearing** (contract + skill authoring; no new config field, no validator change — L11). The
build is a **later orchestrated dogfood** (per `exercise-harness-for-real`), not part of this DESIGN.

## 7. Seams to existing decisions (coherence — no chimera)
- **D71/D88 (Priming-and-Grill + INTENT):** the mirror is the human-facing front of the *same* grill→freeze
  engine; grill still enriches the prompt, `INTENT.md` is still the frozen contract. The mirror is what the user
  *sees*; the grill is what fills it.
- **S2 hard-STOP gate:** refined in presentation, preserved in requirement (L4) — recorded, not silent.
- **D72 (grill ledgers feed the fingerprint) + D66/D74 (LEARN feed) + D9/D56 (CONSULT gated):** the
  register-adaptation seam (L8) is exactly this arc applied to *voice* — emit-only now, CONSULT later.
- **D17–D25 (modes) + D34/D46 (run-shapes, progressive disclosure) + kata.config:** L5 is a presentation layer;
  the mode/tier/run-shape/delivery machinery and `kata.config` are unchanged.
- **loop-hardening S1/S1.5 (the dashboard, statusline, web viewer):** L6 keeps them as the granular firehose;
  narration is the conversational channel, not a replacement.
- **D92 (the Kata Loop / the Harness vocabulary):** narration speaks human, but the internal vocabulary and the
  `改善型` motif are unchanged.
- **kata-slop-check / exercised-vs-proven:** L7 risk-surfacing + L8 honesty keep our *own* closeouts free of the
  inflation the detector catches.

## 8. Out of scope (this DESIGN)
- The actual build (a later orchestrated dogfood). The PLAN freezes ownership + LOCKED decisions; orchestration
  follows the §5 recipe in `HANDOFF.md`.
- Lighting up adaptive register (gated — L8).
- New dashboard/statusline features (loop-hardening already shipped them; L6 only references them).
- Adapter-specific persona rendering for non-Claude hosts (v0.3 adapter work; the contract is agnostic now).

## 9. Open items — RESOLVED at spec review (operator, 2026-06-24)
- **Persona naming → nameless.** It is the harness's own voice, not a named character (folded into L2).
- **Config wiring → reuse, no new field.** The moderate register is a static default in `protocol/persona.md`;
  adaptation is the gated engram seam (§4.3). The "how careful" dial sets **existing** `kata.config` fields
  (`mode` + `tiers["kata-grill"]` + `delivery.boundary`) — no new UX config field (folded into L5/§4.3).
  Consequence: the whole spec is non-code-bearing (§6).
- **Dial mapping → confirmed.** "how careful / how often should I check with you" maps to
  mode + grill-depth + `delivery.boundary` (folded into L5); the advanced drawer exposes the real ladder. The
  exact threshold detail (which dial position → which mode/grill tier) is a PLAN-time tuning, not a DESIGN fork.

## 10. Maps to BACKLOG
- **WS-3** (persona/voice · mode-spoken decision tree · goal-centric intake · in-loop narration · strategic
  progress · goal-anchored closeout) → L2 · L5 · L3/L4 · L6 · L6 · L7.
- **WS-4** (offered backout) → L9.
- **WS-5** (closeout change-transparency, lead with plain-language what-changed-why) → L7 step 2.
