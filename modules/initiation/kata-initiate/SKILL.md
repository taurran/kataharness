---
name: kata-initiate
description: >-
  Front door of the Kata Loop: ingest the user's design/brief, classify intent kind
  (project|research|version-up), lead interactive target/platform/vault configuration, drive the grill
  to readiness under dual control (user "execute" anytime OR grill self-proposes), then freeze INTENT.md
  and hand full context to the harness. Invoke to start any Kata Loop run.
license: Apache-2.0
version: 0.2.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Write, Edit, AskUserQuestion]
model: fable
source: >-
  new (KataHarness original, Phase 1 Kata Loop — D88/D91); composes kata-readiness, kata-grill,
  kata-bootstrap, kata-context
tags:
  - kata/coordinate
  - kata/module/initiation
  - freeze
  - intent
  - front-door
---

# kata-initiate — front door of the Kata Loop

The entry point of the **initiation module** (`modules/initiation/`). It transforms the user's raw
intent into a frozen `INTENT.md` artifact and hands full context to the harness. It **composes** —
never reimplements — the spine's existing skills.

Voice throughout: read `protocol/persona.md`. Plain-language, warm through clarity, outcome-first.
Never surface internal stage names. Never overclaim gated capabilities.

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

Do not ask yet — carry the classification forward into the mirror (Phase 2). If the signal is
genuinely ambiguous (two kinds equally plausible), note the ambiguity in the mirror for the human to
resolve.

---

## Phase 1b — loop-back context (version-up re-entry from [[kata-loop]]) + recall brief

This phase has two parts: the **loop-back consumption** (version-up re-entry only) and the **recall brief**
(always — cold start *and* loop-back). The loop-back consumption is skipped on a fresh start; the recall brief
is **not** — it runs on every initiation.

### Loop-back consumption (version-up re-entry only)

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
this is a fresh start — skip **the loop-back consumption above** (but still build the recall brief below).

### Recall brief (always — cold start *and* loop-back)

Build a **read-only RECALL BRIEF** from prior knowledge so the Phase-2 mirror/grill can weigh what was known
before. This is the read-side of a second brain (the `engram.backend` CONSULT-read seam) — it **surfaces**
material; it never decides, never gates, and **never writes `INTENT.md`** (see the invariant box below).
Contract doc: `protocol/recall.md` (the Recall read-CONTRACT — selection/staleness/read-only rules; sibling
slice, forward-ref OK). Engine: `tools/recall.py`.

**1. Build the payload.** Call `recall.recall_from_paths(...)` (`tools/recall.py :: recall_from_paths` — the
files-only default adapter; surface verified present) over the six on-disk sources, with `query_terms` derived
from the run's **goal + CONTEXT** terms (for a `version-up`, also fold in the prior INTENT goal) and `kind` set
to the classified run kind:

| `recall_from_paths` arg | Source |
|---|---|
| `lessons_path` | `.planning/LESSONS-LEARNED.md` |
| `decisions_path` | `.planning/DECISIONS.md` |
| `intent_path` | the prior frozen `INTENT.md` (loop-back only; omit on cold start) |
| `understand_path` | `.kata/understand.md` (the understand-map, written by [[kata-understand]]) |
| `misses_path` | `.planning/validation-misses.jsonl` |
| `handled_path` | `.planning/recurrence-handled.jsonl` |
| `query_terms` | tokens from the run goal + pinned `CONTEXT.md` terms (+ prior-INTENT goal on version-up) |
| `kind` | `project` \| `research` \| `version-up` |

The adapter returns the contract-shaped payload (`recall.recall_payload_schema`, `schema_version "recall/v1"`):
tag/keyword + recency-selected `records[]` and the **always-surfaced open validation-miss `recurrences[]`**.
Selection is **token-overlap + recency only — NO embeddings / NO RAG**.

**2. Render the RECALL BRIEF (Markdown).** From the payload, render a short brief in this order:

- **Recurring open validation-misses first** (`payload["recurrences"]` — always-surfaced, regardless of query
  overlap): one line per recurrence with its `failure_class` / `responsible_skill` / `distinct_runs` /
  `severity_tier`. (These carry only the projected recurrence fields — no raw miss text.)
- **Then the matched records** (`payload["records"]`, highest `match_score` first): each with its `title`,
  short `excerpt`, and **provenance markers** — `source` / `provenance.date` / a **`stale` hint** where set.
- **N2 — surface, don't silently drop (one honest line):** note that the surfaced recurrences are the
  detector's **actionable (over-threshold) open subset** — *sub-threshold validation-misses may exist but were
  not surfaced here*. This tells the human the recurrence list is the actionable subset, not the full miss log.

**3. Staleness is shown, never enforced.** Display `provenance.date` + the `stale` flag as **hints**; recall
**never** filters or drops a record by age. The human/grill judges what is still relevant.

**4. Non-fatal / degrades.** `recall_from_paths` reads tolerantly — an absent source contributes nothing and
never raises. A missing source ⇒ a partial or empty brief. Recall **never blocks** initiation or the freeze
(it mirrors the understand-map's "never gates" posture). Carry the rendered brief forward into Phase 2.

> **Recall is read-only — it has NO write path to `INTENT.md` (structural invariant, PINNED).**
> The RECALL BRIEF informs the Phase-2 mirror/grill **deliberation ONLY**. It is **DISPLAYED, never stored**.
> It **never** enters the operator-confirmed `answers` dict (Phase 4/6) and is **never** passed to
> `tools/intent_scaffold.py :: write_intent` — which remains the **sole** `INTENT.md` writer, fed only from the
> human-confirmed `answers`. Recall also never changes a gate verdict, auto-acts, mutates a skill/protocol/tool,
> or re-decides a LOCKED decision. `INTENT.md` stays PINNED (`protocol/intent.md`).

---

## Phase 2 — the reflective goal mirror

After ingesting the inputs (system prompt + any brief + light research + Phase 0 readiness verdict),
**synthesize** everything into a plain-language mirror and reflect it back to the human. Do not
present a form. Do not ask a list of questions. Propose a complete picture and invite editing.

### 2a. Build the mirror

Infer a complete candidate setup from everything available. Then write a short, warm mirror in
plain language covering two things:

**What you want and what success looks like** — restate the goal in the human's own words, sharpen
where the inputs allow. Name the outcome, not the implementation. For a `version-up`, name the gap
being closed, not the code change.

**Here is how I would set it up** — include the proposed config in human terms:

| Config value | What to say in the mirror |
|---|---|
| `kind` | "This looks like a [new build / structured research / improvement run]." |
| `target.kind` + `target.path` | "I'd run it [on this project / on a new repo / on the harness itself] — [path if known]." |
| `target.vault` | "I'd link your PokeVault / I'd skip the vault for this run / I'd aim at [path]." |
| `target.platform` | "We're running on [Claude / Codex / …]." |
| `roles` (multi-model routing) | **(Only when `confirmed_platforms()` (`tools/kata_settings.py:109`) returns a non-host platform AND the human opts in.)** "I'd route [coder=Claude · validator=Codex · researcher=Kiro / all roles on Claude]." Omit this line when single-host or when the human declined. |
| `grillDepth` | "I'd suggest [skip / light / standard / full] planning depth, because [one-line rationale from Phase 0]." |
| Dual-control execute | "After planning, you confirm before anything runs. That stays in your hands." |

Write the mirror as a short paragraph or two — not a table. The goal is a human reading it and
recognising their own intent, reflected back clearly with a sensible starting setup.

### 2a-recall. Surface the RECALL BRIEF as read-only recall context

Alongside the mirror, surface the **RECALL BRIEF** built in Phase 1b (`recall.recall_from_paths`) as
**read-only recall context** the human/grill weighs while editing the goal/setup. Frame it plainly as
**recall — what you knew before** (prior lessons, decisions, prior intent, the understand-map, and the
always-surfaced open validation-miss recurrences): it is **not a decision and not a default**. It informs the
human's deliberation; the human still owns every load-bearing value.

This brief is **displayed, never stored.** It does **not** pre-fill or alter any mirror value, never enters the
`answers` dict, and is **never** written to `INTENT.md` — recall has no write path to the frozen intent (see the
read-only invariant box in Phase 1b). Staleness (`provenance.date` / `stale`) is shown as a hint, never used to
filter; recall changes no gate verdict and blocks nothing.

### 2b. Invite conversational editing

After reflecting the mirror, ask one open question via `AskUserQuestion`:

> "Does this capture what you're after? Change anything you'd like — the goal, the setup, or the
> planning depth — and I'll adjust."

The human edits conversationally. You update the inferred values in response. Continue until the
human signals confirmation (agreement, "looks good", "yes", "go", etc.).

**What counts as confirmation:** an explicit signal from the human that the mirror is accurate —
including its load-bearing values. Silence or a generic approval that leaves specific values
uninspected does not count (see the gate checklist below).

### 2c. Reference tables (for your inference, not shown to the user as a form)

**target.kind:**

| target.kind | When to infer it |
|---|---|
| `self` | KataHarness is improving itself (dogfood run). |
| `existing` | An existing repo/project on disk. Collect `target.path` from the brief or ask. |
| `greenfield` | A brand-new repo to be created. Collect name + destination. |

**Vault:**

| Option | When to infer it |
|---|---|
| `linked` (PokeVault) | User's PokeVault is configured — prefer this. |
| `own:<path>` | User names an existing Obsidian vault or notes directory. |
| `per-folder:<path>` | Manual per-artifact path configuration (advanced — surface only if asked). |
| absent | No vault configured for this run. |

Collect `target.vault` from the mirror conversation. The default parent project folder + vault location
are remembered in the central settings file (`tools/kata_settings.py`); installer mechanics are shipped
(`tools/kata_install.py` + `docs/SETUP.md`). Seed `target.vault`/`target.path` from the settings when present.

**Platform:**

| Option | When to infer it |
|---|---|
| `claude` | Claude Code (current default — infer unless told otherwise). |
| `codex` | OpenAI Codex — uses the Codex adapter. |
| `kiro` | Amazon Kiro — uses the Kiro adapter (planned v0.3). |
| `quick` | ACP desktop host — the integration seam for an external/work ACP host. |
| `other` | Any additional host. |

If `Kiro`, `Quick`, or `Other`, note that the platform's module-swap mechanism applies (see
`modules/initiation/AGENTS.md`).

### 2d. Find the project (search → confirm) — for `existing` runs

When `target.kind == existing` and the exact `target.path` isn't already known, **don't ask for a full
path up front.** Ask the human for the **project name + roughly where it is**, then resolve it:

1. Read the remembered **default parent project folder** from the settings (`kata_settings.read_settings()`);
   the human may override it for this run.
2. Run the search: `project_find.find_projects(name, parentDir, rough_location)`.
3. Resolve by candidate count:
   - **one match** → show it and confirm;
   - **several** → list them (best-first) and let the human pick;
   - **none** → ask for the full path directly.
4. The confirmed folder becomes `target.path`.

**Copy mode (Debug Mode import-a-copy / aggressive changes on untrusted or large repos):** if the human
chooses to work on a copy, also ask for a **destination folder**, then
`kata_install.copy_project(src, dest)` and set `target.path` to the copy. The original is left untouched
(the copy is a plain file copy — it never runs git against a vault).

### 2e. Multi-modal routing — "Make this run multi-modal?" (skip if single-host)

**Precondition:** call `confirmed_platforms()` (`tools/kata_settings.py:109`). If the result contains **only the host platform** (no non-host platform has been installed and confirmed), **skip this phase entirely** — do not surface the question, do not add `roles` to the mirror, and treat the run as single-host (BC1, `protocol/config.md:27` — absent `roles` ⇒ all roles on host).

When at least one **non-host** platform is present in `confirmedPlatforms`, surface this question via `AskUserQuestion` after the rest of the Phase 2 setup:

> "Your harness has [Codex / Kiro / …] confirmed. Do you want to route any roles to a different model? You can assign individual jobs — coder, validator, researcher, orchestrator, evaluator — to the platforms you have installed, or leave everything on the host."

**If the human opts in:** for each loop role, ask which platform from `confirmedPlatforms` to assign it (default = host; any unassigned role stays on host). Produce a `roles` mapping:

| Role | Default | Description |
|---|---|---|
| `coder` | host | The primary build agent (single sustained agent). |
| `validator` | host | Red-team + anti-slop + grounding review. |
| `researcher` | host | Research escalations (`kata-research`). |
| `orchestrator` | host | Plan-guardian; **must remain host in v1** (`.planning/specs/multi-model-orchestration/DESIGN.md` LD11). |
| `evaluator` | host | Lightweight inline scorer. |

Surface the confirmed assignment in the **Phase 2 mirror** as load-bearing value #8 (see the infer-then-confirm gate below). The `roles` mapping is carried to `kata-bootstrap` for writing to `kata.config` (`protocol/config.md:27`); it is NOT written to `INTENT.md` (`roles` is executable routing — a `kata.config` concern only).

**Orchestrator constraint (v1):** the orchestrator role must remain on the host in v1 (`.planning/specs/multi-model-orchestration/DESIGN.md` LD11). If the human assigns orchestrator to a non-host platform, explain this constraint and reset it to host.

**If the human declines or no non-host platforms are confirmed:** omit `roles` entirely — the run is single-host (BC1). `kata-bootstrap` writes no `roles` block to `kata.config` (`protocol/config.md:27`).

### 2g. Acceptance / success criteria — "start with the end in mind"

After the multi-model routing question (or after 2e is skipped on a single-host run), enumerate and reflect back
the **checkable success criteria** for this run: "how we'll know it's done."

**Infer candidates** from the goal + brief (e.g. "the CLI exits 0 on a clean re-install", "validate_skills
reports 0 errors", "Snyk medium+ 0 on the new Python file").  Frame each criterion as an **observable
outcome**, not an implementation step — the test you'd run at the end, not the code you'd write.

Reflect them back as a **numbered list** inside the mirror, inviting the human to confirm, edit, add, or delete
each one.  Require **per-criterion confirmation or correction** — the same S2 discipline as every other load-
bearing value.

**Confirmed-absent is a valid outcome (no deadlock for empty / research runs):** if the human confirms there
are no checkable criteria for this run (e.g. a `research` run producing findings, or a quick spike with no
verifiable end-state), record that explicit opt-out and carry an **empty `acceptanceCriteria`** forward.  The
gate PASSES for a confirmed-absent decision exactly as it does for confirmed value #8 (single-host / skip).

The confirmed list (or the confirmed-absent decision) is written into `INTENT.md` via the `acceptanceCriteria`
field (`tools/intent_scaffold.py` `build_intent` — Slice D).  When the list is empty, the field is omitted
from the frontmatter (byte-identical to a pre-field build — BC).

---

## Phase 3 — grill depth

The grill-depth is surfaced inside the mirror (Phase 2) as part of the proposed setup. The
pre-selection comes from [[kata-readiness]]'s Scope-3 recommendation, carried forward with a
one-line rationale. The human confirms or changes it during the mirror conversation.

For reference — the depth options and their meanings:

| grillDepth | Meaning |
|---|---|
| `skip` | Trust the priming prompt; no grill runs. Ambiguity resolved in-loop. |
| `light` | Shallow grill — top-risk branches only. |
| `standard` | Full method, full decision tree. **Default for non-trivial work.** |
| `full` | Standard + adversarial stress-test + convergence gate. High-stakes / hard-to-reverse. |

Record the confirmed depth as `grillDepth` in `INTENT.md`. The human always chooses; the pre-selection
is a proposal inside the mirror, not a default that is silently carried forward.

---

## Infer-then-confirm gate

> **This gate is a hard structural stop. Do NOT freeze `INTENT.md` until the human has
> confirmed each load-bearing value by name, inside the mirror conversation. Inferring a value
> and proceeding without surfacing it to the human is a drift failure. The gate measures
> confirmation, not form-asking — but a blanket "looks good" over un-itemized inferred values
> is not confirmation.**

The mirror (Phase 2) is the confirmation surface. Each load-bearing value must have been **individually
named and visible** in the reflected-back mirror, and must have **received either an explicit approval
or a correction** from the human. Values that were inferred internally but not named in the mirror
are not confirmed, regardless of any overall approval.

**Requirement (unchanged from S2):** every answer in `INTENT.md` must trace back to a human
confirmation — either the human said it first, or the agent proposed it in the mirror and the human
approved or corrected it by name.

**What changed (presentation only):** the gate now accepts confirmation via the mirror conversation
rather than requiring a naked form. The requirement — every frozen value traces to an explicit human
confirmation — is identical. This is a recorded, audited refinement of the S2 anti-drift fix, not a
weakening of it.

**The load-bearing values** that must each be individually visible in the mirror and confirmed:

1. `kind` — the classified run kind (project / research / version-up).
2. `target.kind` — self / existing / greenfield.
3. `target.path` — required when `target.kind == "existing"`.
4. `target.vault` — vault strategy (linked / own:path / per-folder:path / absent).
5. `target.platform` — the agent host driving this run.
6. `grillDepth` — the planning depth (skip / light / standard / full).
7. Dual-control execute — the human's understanding that they confirm before anything runs.
8. **Multi-model routing** (`roles`) — the per-role platform assignment, or single-host (absent). **Applies only when `confirmed_platforms()` (`tools/kata_settings.py:109`) lists a non-host platform.** If Phase 2e was skipped (single-host) or the human declined, record this as single-host / absent. If the human opted in, the confirmed `roles` mapping must have been named in the mirror.
9. **Acceptance / success criteria** (`acceptanceCriteria`) — the checkable "how we'll know it's done" list confirmed in step 2g. **Handled exactly like conditional value #8:** when there are no checkable criteria for this run (e.g. a `research` run, or the human explicitly opts out), an explicit "no acceptance criteria for this run" is a valid confirmation and the run PASSES with an **empty `acceptanceCriteria`**. The gate fails only on an un-itemized, unconfirmed value — never on a legitimately empty or research run.

If any value was not named in the mirror — or the human's response was ambiguous on that value
specifically — surface it explicitly via `AskUserQuestion` before proceeding.

### Gate checklist (for the evaluator — with teeth)

An evaluator verifying this run MUST confirm ALL of the following before marking initiation as
complete. A blanket finding of "looks good" is not sufficient — each item below must be checked
individually against the mirror transcript and the frozen `INTENT.md`.

**Mirror visibility — each load-bearing value was individually visible in the reflected-back mirror:**
- [ ] `kind` was named in the mirror (not only inferred internally).
- [ ] `target.kind` was named in the mirror.
- [ ] `target.path` was named in the mirror when `target.kind == "existing"`.
- [ ] `target.vault` was named in the mirror (the vault strategy was stated, not assumed).
- [ ] `target.platform` was named in the mirror.
- [ ] `grillDepth` was named in the mirror, with its rationale.
- [ ] Dual-control execute was named in the mirror (the human was told they confirm before anything runs).
- [ ] Multi-model routing (`roles`) was handled correctly: either (a) `confirmed_platforms()` (`tools/kata_settings.py:109`) returned only the host ⇒ Phase 2e was skipped (no mirror entry required); or (b) a non-host platform was confirmed ⇒ the human was asked and the outcome — confirmed `roles` assignment or all-on-host decline — was named in the mirror.
- [ ] Acceptance criteria (step 2g) were handled correctly: either (a) each acceptance criterion was individually named in the mirror and the human confirmed or corrected it; OR (b) the human explicitly confirmed "no acceptance criteria for this run" — and that confirmed-absent decision was named in the mirror (not silently assumed).

**Human confirmation — each value survived into the frozen `INTENT.md` unchanged or was explicitly corrected:**
- [ ] `kind` in `INTENT.md` matches what the human confirmed (approved or corrected in the mirror).
- [ ] `target.kind` in `INTENT.md` matches the human-confirmed value.
- [ ] `target.path` in `INTENT.md` matches the human-supplied path (when applicable).
- [ ] `target.vault` in `INTENT.md` matches the human-confirmed vault strategy.
- [ ] `target.platform` in `INTENT.md` matches the human-confirmed platform.
- [ ] `grillDepth` in `INTENT.md` matches the human-confirmed depth.
- [ ] The dual-control execute decision was made by the human (not auto-decided by the agent).
- [ ] The multi-model routing decision was made by the human: either all-on-host was confirmed (or Phase 2e was skipped as single-host), or a per-role `roles` mapping was confirmed by the human and will be written to `kata.config` by `kata-bootstrap` — not to `INTENT.md` (`roles` is a config concern only, `protocol/config.md:27`).
- [ ] The acceptance criteria decision was made by the human: either each criterion in `INTENT.md` traces to an explicit human approval or correction from step 2g; OR a confirmed-absent decision is recorded (empty `acceptanceCriteria` in `INTENT.md`, or field omitted). A blanket "looks good" over un-itemized criteria does **not** satisfy this check; an explicit "no criteria for this run" **does**.

**A value that was inferred, not named in the mirror, and passed through with a blanket approval
FAILS this gate — even if the value happens to be correct.** The confirmation must be traceable
to that value specifically.

**Writer and schema:**
- [ ] `INTENT.md` frontmatter was written by `tools/intent_scaffold.py` (`write_intent`) from the
  collected answers — not hand-crafted inline.
- [ ] `INTENT.md` conforms to `protocol/intent.md` (all required keys present, valid enum values).

---

## Phase 4 — capture the GOAL and write INTENT.md (draft)

Collect the operator's goal narrative (one paragraph north star — the outcome, not the
implementation), and any `fixes`, `features`, `modulesAdded`, `changeSummary` details via
`AskUserQuestion` if not already captured.

Assemble an `answers` dict from **all** of the operator-supplied values gathered in Phases 1–3 and
the gate above. Call `tools/intent_scaffold.py :: write_intent(path, answers)` to produce the draft
`INTENT.md` at the repo/project root. **Do not hand-craft the INTENT.md frontmatter inline** —
`write_intent` is the only authorised writer; it enforces the `protocol/intent.md` schema and
validates enum values fail-closed.

The `answers` dict keys match the `build_intent` signature exactly:

```python
answers = {
    "kind":          kind,           # operator-confirmed
    "goal":          goal,           # operator narrative
    "fixes":         fixes,          # list[str]; empty for project/research
    "features":      features,       # list[str]
    "modulesAdded":  modules_added,  # list[str]
    "changeSummary": change_summary, # one sentence
    "target": {
        "kind":     target_kind,     # operator-confirmed
        "path":     target_path,     # operator-supplied or ""
        "vault":    vault,           # operator-confirmed
        "platform": platform,        # operator-confirmed
    },
    "grillDepth": grill_depth,       # operator-confirmed
    "readiness":  "",                # filled after Phase 5
    # OPTIONAL — Slice D additive field (step 2g); empty list when no criteria confirmed
    "acceptanceCriteria": acceptance_criteria,  # list[str]; [] for research/opted-out runs
}
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

1. **Fill `readiness`** in the `answers` dict: the agent's "enough-to-execute" verdict and its
   one-paragraph rationale (which branches were resolved, which were deferred and why, what the
   autonomous floor will handle in-loop via `kata-defer`).

2. **Freeze `INTENT.md`**: call `tools/intent_scaffold.py :: write_intent(path, answers)` with the
   complete `answers` dict (including the populated `readiness` field) to overwrite the draft.
   The file is now frozen — it is the contract the harness executes against. Do not modify it after
   this point; a new initiation session is required to produce a new `INTENT.md`.
   `write_intent` enforces the schema and `..`-traversal guard; pass the absolute path of the
   repo/project root + `"INTENT.md"`.

3. **Verify the freeze:** confirm the written file's frontmatter round-trips as valid YAML and that
   all required keys from `protocol/intent.md` are present (parse and spot-check — `build_intent`
   already validates, but this is the final belt-and-suspenders check before hand-off).

4. **Hand off**: surface the frozen `INTENT.md` + the written `kata.config` + a summary of the
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
