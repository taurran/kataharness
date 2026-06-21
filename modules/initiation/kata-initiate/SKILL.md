---
name: kata-initiate
description: >-
  Front door of the Greater Loop: ingest the user's design/brief, classify intent kind
  (project|research|version-up), lead interactive target/platform/vault configuration, drive the grill
  to readiness under dual control (user "execute" anytime OR grill self-proposes), then freeze INTENT.md
  and hand full context to the harness. Invoke to start any Greater Loop run.
license: Apache-2.0
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Write, Edit, AskUserQuestion]
model: fable
source: >-
  new (KataHarness original, Phase 1 Greater Loop — D88/D91); composes kata-readiness, kata-grill,
  kata-bootstrap, kata-context
tags:
  - kata/coordinate
  - kata/module/initiation
  - freeze
  - intent
  - front-door
---

# kata-initiate — front door of the Greater Loop

The entry point of the **initiation module** (`modules/initiation/`). It transforms the user's raw
intent into a frozen `INTENT.md` artifact and hands full context to the harness. It **composes** —
never reimplements — the spine's existing skills.

---

## Phase 0 — readiness check (always first)

Invoke [[kata-readiness]]. On **BLOCK**, stop and surface the blocker. On **WARN**, surface and allow
proceed. Use the readiness verdict's priming-prompt richness score to pre-select a recommended
grill depth for Phase 3 (the human always chooses).

---

## Phase 1 — ingest and classify

Read the user's intent from:
1. The **system prompt** (the priming context that launched this skill).
2. A **project-brief file** in the target directory, if one is named or discoverable (e.g.
   `BRIEF.md`, `brief.md`, `PROJECT.md`, `README.md` with a "goal" section). Use `[[kata-context]]`
   to extract and pin precise terms as they are discovered.

Classify **`kind`** — the single most important routing decision:

| kind | Signal |
|---|---|
| `project` | Building something new (greenfield or new feature set). No prior harness run to compare against. |
| `research` | Producing a structured findings/recommendation artifact, not executable code. |
| `version-up` | Improving something that already ran through the harness. A prior `RESULT.json` / DESIGN exists. |

For **`version-up`**: explicitly evaluate the **actual goal** — the gap being closed — not the surface
change. Ask: "What is missing or broken in the prior run's output that this version-up addresses?"
Capture that gap as the `goal` field. This is what D88 names as the most common INTENT failure mode:
version-up goals stated as code changes rather than outcomes.

Confirm classification with the user (one-line, non-blocking) before proceeding. If ambiguous, ask.

---

## Phase 1b — loop-back context (version-up re-entry from [[kata-loop]])

**Detect a loop-back run:** this initiation was re-entered by the [[kata-loop]] conductor's loop-back Path A if a
prior frozen `INTENT.md` **and** `.kata/understand.md` are present at the target. When detected, this is **not a
cold start** — consume the four named inputs the conductor carries (kata-loop's loop-back Path A is the
authoritative contract for this payload):

| Input | Read from | How to use it here |
|---|---|---|
| New green baseline SHA | `.kata/RESULT.json` → `resultSha` | The fork point; record as the version-up baseline. |
| Understand-map | `.kata/understand.md` | Surface during Phase 1 ingest — it already says what changed; do not re-derive it. |
| Lessons | `.planning/LESSONS-LEARNED.md` | Feed into Phase 5 as **known-resolved** grill branches — do not re-argue them. |
| Prior `INTENT.md` | the frozen prior `INTENT.md` | The starting frame: prior goal/kind/target/grillDepth. The new `goal` is the *next* gap, set against this. |

A loop-back run pre-classifies as `version-up` (the prior INTENT proves a prior harness run). Carry the prior
`target` config forward as the default (the user may change it). If no prior `INTENT.md`/understand-map exist,
this is a fresh start — skip this phase.

---

## Phase 2 — interactive target / platform / vault configuration

Lead the user through three configuration choices (structured choice-or-text; offer 2–4 options,
always a free-text escape):

### 2a. Target

| target.kind | Meaning |
|---|---|
| `self` | KataHarness is improving itself (dogfood run). |
| `existing` | An existing repo/project on disk. Collect `target.path`. |
| `greenfield` | A brand-new repo to be created. Collect name + destination. |

### 2b. Vault

How the skills and harness artifacts land relative to the user's knowledge workspace:

| Option | Meaning |
|---|---|
| Link/scaffold PokeVault | Use the user's configured PokeVault (preferred default if configured). |
| Point at own vault | User names an existing Obsidian vault or notes directory. |
| Aim each folder | Manual per-artifact path configuration (advanced). |

Collect `target.vault`. Record which approach was chosen; do not trigger installer mechanics — those
are deferred to Phase 5.

### 2c. Platform

Which agent host will execute the harness:

| Option | Meaning |
|---|---|
| `Claude` | Claude Code (current default). |
| `MindBridge/Quick` | ACP Quick — platform may bring its own `AGENTS.md`/installer. |
| `Kiro` | Amazon Kiro — uses the Kiro adapter. |

Collect `target.platform`. If `MindBridge/Quick` or `Kiro`, note that the platform's module-swap
mechanism applies (see `modules/initiation/AGENTS.md`).

---

## Phase 3 — grill depth

Present the grill-depth dial (from [[kata-readiness]]'s Scope-3 recommendation, pre-selected):

| grillDepth | Meaning |
|---|---|
| `skip` | Trust the priming prompt; no grill runs. Ambiguity resolved in-loop. |
| `light` | Shallow grill — top-risk branches only. |
| `standard` | Full method, full decision tree. **Default for non-trivial work.** |
| `full` | Standard + adversarial stress-test + convergence gate. High-stakes / hard-to-reverse. |

Show the readiness verdict's one-line rationale for the pre-selected depth. The human always chooses.
Record the chosen depth as `grillDepth` in `INTENT.md`.

---

## Phase 4 — capture the GOAL and write INTENT.md (draft)

Write a **draft** `INTENT.md` at the repo/project root per the schema in `protocol/intent.md`:

```yaml
---
kind: project | research | version-up
goal: <one-paragraph north star — the outcome, not the implementation>
fixes: []                   # version-up: what is being repaired
features: []                # what is being added
modulesAdded: []            # new modules or skills this run introduces
changeSummary: <what changes in this version>
target:
  kind: self | existing | greenfield
  path: <absolute path or "" for self>
  vault: <vault path or strategy label>
  platform: Claude | MindBridge/Quick | Kiro
grillDepth: skip | light | standard | full
readiness: ""               # filled after Phase 5
---
```

The `INTENT.md` body (below frontmatter) holds the **north-star narrative**: a human-readable
expansion of `goal` that a builder reading it cold can understand without further context. It is NOT
a plan — it is the intent the plan must serve.

Use [[kata-context]] immediately when any ambiguous term appears in the goal narrative. The term is
pinned in `CONTEXT.md` before the grill begins — this prevents the grill from re-arguing resolved
vocabulary.

---

## Phase 5 — grill to readiness (dual control)

This is the spec-to-ready engine. Drive `[[kata-grill-standard]]` (or the tier chosen in Phase 3) at
the selected depth. Two independent paths can end the grill — either suffices:

### Path A — user says "execute"
The user may type **"execute"** (or equivalent: "go", "ship it", "skip the rest") at **any point
during the grill**. This is a **hard bail**: stop all remaining grill rounds immediately. Proceed
directly to Phase 6 with the grill in its current state.

### Path B — grill self-proposes execute
After each grill round, `[[kata-grill-standard]]` self-assesses readiness: *"Are there any remaining
decision branches whose resolution would materially change the plan?"* When the answer is no — the
decision tree is resolved enough to one-shot — the grill **proposes execute** with a one-paragraph
rationale. The user confirms (Y/n). On confirm, proceed to Phase 6. On reject, run another round.

**Neither path is the "right" path.** Both produce the same output. The grill does not block
execution when the user has enough confidence; the grill does not force execution when the user
wants more certainty.

During the grill, use [[kata-context]] to pin every resolved term into `CONTEXT.md` (inline, not
batched). Use [[kata-bootstrap]] to write or update `kata.config` when run-shape or composition
decisions are resolved in the grill (so the config is ready at Phase 6).

**Config authority (avoid divergence):** the frozen `INTENT.md` `target` block (kind/path/vault/platform) is the
**authoritative** record of *what* this run targets; `kata.config` is the *executable* projection
`kata-bootstrap` derives from it for `kata-orchestrate`. If they ever disagree (e.g. the user changed target
mid-grill), **`INTENT.md` wins** — it is frozen; regenerate `kata.config` from it. Never let a stale `kata.config`
override the frozen intent.

Note: the understand-map ([[kata-understand]]) is offered by [[kata-closeout]] at run end, not here; the
[[kata-loop]] conductor sequences this skill and, on a version-up re-entry, feeds it the prior run's context
(see Phase 1b).

---

## Phase 6 — freeze INTENT.md and hand off

1. **Fill `readiness`** in `INTENT.md` frontmatter: the agent's "enough-to-execute" verdict and its
   one-paragraph rationale (which branches were resolved, which were deferred and why, what the
   autonomous floor will handle in-loop via `kata-defer`).

2. **Freeze `INTENT.md`**: write the final content (overwrite the draft). The file is now frozen —
   it is the contract the harness executes against. Do not modify it after this point; a new
   initiation session is required to produce a new INTENT.md.

3. **Hand off**: surface the frozen `INTENT.md` + the written `kata.config` + a summary of the
   `CONTEXT.md` additions made during this session. The harness (kata-bootstrap →
   kata-orchestrate) picks up from here.

---

## Backward-compatibility

`INTENT.md` absent ⇒ the harness reads the frozen DESIGN as today. This skill is invoked explicitly
— it is never a required step for direct one-shot harness runs. (BC, DESIGN §9.)

## Composed skills (all already exist)

- [[kata-readiness]] — Phase 0 preflight and grill-depth recommendation.
- [[kata-grill-standard]] (via `[[kata-grill]]` alias) — Phase 5 grill engine.
- [[kata-bootstrap]] — Phase 5 config writer; Phase 6 run launcher.
- [[kata-context]] — Phase 1 and Phase 5 ubiquitous-language pinning.
