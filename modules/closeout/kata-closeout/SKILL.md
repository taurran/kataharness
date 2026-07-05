---
name: kata-closeout
description: >-
  Back-half closeout that tracks a completed run's machine artifacts, composes a goal-anchored human-reviewable
  report (plain-language what-changed-and-why, by goal-aspect, before any path or gate number), offers the
  understand-map (opt-in), runs the human decision gate (satisfied / commit-push-merge / run-again or
  build-new / cleanly undo the whole run), and hands the decision to the conductor's loop-back — never gates
  correctness.
license: Apache-2.0
version: 0.1.0
category: handoff
status: beta
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Bash, Write]
source: new (KataHarness original — Phase 2 Kata Loop back-half, D89/DESIGN §3)
tags:
  - kata/handoff
  - kata/module/closeout
  - closeout
  - human-gate
  - never-gates
---

# kata-closeout — the back-half closeout skill

`kata-closeout` owns the **back half of the Kata Loop**: it runs **after** the [[kata-evaluate]]
default-FAIL gate, tracks the run's machine artifacts, delivers a goal-anchored report (§5 skeleton,
plain-language-first), offers the comprehension map, runs the human decision gate, and hands the
decision to the conductor's loop-back. It **never gates** — gating stays with [[kata-evaluate]]
(spine principle #4, DESIGN §3). Voice: `protocol/persona.md`.

## Hard boundary — it reports, it never gates

The default-FAIL gate is and stays [[kata-evaluate]]. `kata-closeout`:
- Reads the gate's verdict from `.kata/RESULT.json` — verbatim, not re-derived.
- Surfaces a NEEDS_WORK verdict to the human as a clear finding; it does not override it.
- Never confers a pass/fail verdict of its own.
- Carries out git actions (commit/push/merge/rollback) **only on explicit human approval** — never
  autonomously.

## Step 1 — Track everything

Consume the three F1 machine artifacts written to `.kata/` by `tools/gate_emit.py`:

| Artifact | Path | What it contains |
|---|---|---|
| Gate result | `.kata/RESULT.json` | `gateName`, `exitCode`, `passed`/`failed`/`skipped`, `stdoutTail`, `baselineSha`, `resultSha`, `utc` |
| Footprint manifest | `.kata/footprint.json` | `footprint`, `changed`, `inFootprint`, `outOfFootprint`, `withinFootprint`, `diffstat` |
| Mutation proof | `.kata/mutation.json` | `records`, `allNonVacuous` — **required for a code-bearing run** (its absence makes [[kata-evaluate]] rubric item 1 NEEDS_WORK); legitimately absent only for a pure data/config/docs run |

Read all three with `Read` (or `Bash` for `cat` / `jq` formatting). Note `.kata/RESULT.json.baselineSha`
— this SHA is the **backout anchor** used in Step 4 (Decision 4). Do **not** reconstruct counts from
prose — the artifacts are the record. If any artifact is absent, note it explicitly as a gap in the
report; the "reports, never gates" principle still applies.

Also read the frozen `INTENT.md` to retrieve the plain-language goal statement for Step 2.

## Step 2 — Report (§5 skeleton — in order, always)

Compose `kata-report` over the consumed artifacts, passing the three artifact paths. `kata-report`
produces **both tiers** (defined in `skills/evaluate/kata-report/SKILL.md`):

1. **The concise CLI summary** (Tier 1) — persona voice, goal-anchored essentials.
2. **The full report content** (Tier 2) — the complete M5 skeleton keyed to the `{{TOKEN}}` contract.

After composing report content via `kata-report`, carry out the following emit/render/link sequence
**before** presenting anything to the human.

### Step 2a — Emit `.kata/CLOSEOUT.md` (source-of-truth)

Write the full Markdown report to `.kata/CLOSEOUT.md`. This is the durable source-of-truth artifact.
It carries the complete M5 skeleton in plain text: goal restated · what-changed-by-aspect · did-it-hit ·
risks/uncertainties · evidence links + diffstat + gate numbers + SHAs · offered backout. The file is
written to `.kata/` (gitignored, like `RESULT.json`), making it a run artifact, not a committed skill.

### Step 2b — Render `.kata/closeout.html` (in-context token fill — no Python)

Load the committed HTML template at `modules/closeout/resources/closeout-report.template.html` by
reading it in-context with the `Read` tool. Then **substitute every `{{TOKEN}}`** from the report
content assembled in Tier 2:

1. Read `modules/closeout/resources/closeout-report.template.html` in full.
2. For each token listed in the template's leading HTML comment (reproduced here for reference):
   - `{{RUN_TITLE}}` — short human-readable title (goal phrase + run date; from `INTENT.md` + `RESULT.json`).
   - `{{VERDICT_BADGE}}` — the full `<span class="badge badge--{STATE}">{LABEL}</span>` element, where
     STATE is one of `pass` / `partial` / `needs-work` and LABEL is the `kata-evaluate` verdict string
     verbatim (from `.kata/RESULT.json`). Never re-derived; always quoted from the artifact.
   - `{{GOAL}}` — the restated goal in 1–2 plain-language sentences (from frozen `INTENT.md`), persona
     voice (`protocol/persona.md`): "You wanted X."
   - `{{CHANGED_BY_ASPECT}}` — **repeatable block**: one `<div class="aspect-block">…</div>` per
     goal-aspect. Each block contains an `<h3 class="aspect-heading">` heading and a `<p>` body in
     plain language (no file paths, no gate numbers). Concatenate all aspect blocks and substitute the
     full concatenation for this single token. The template's HTML comment documents the repeatable-block
     pattern; follow it exactly.
   - `{{HIT_ASSESSMENT}}` — honest 1–3 sentence assessment; quotes the `kata-evaluate` verdict verbatim.
   - `{{RISKS}}` — an HTML `<ul>…</ul>` of risks and exercised-not-proven caveats (≥1 item).
   - `{{EVIDENCE}}` — an HTML linked list of evidence artifacts (gate result path, diffstat, footprint
     manifest, mutation-proof if present, findings files). Linked-not-dumped.
   - `{{BACKOUT}}` — plain-language backout offer + literal `git reset --hard <baselineSha>` command,
     anchored on `.kata/RESULT.json.baselineSha`. Destructive; executes only on explicit human approval.
   - `{{GATE_NUMBERS}}` — pytest result + validator result quoted verbatim from `.kata/RESULT.json`.
   - `{{SHAS}}` — `<baselineSha> → <resultSha>` pair from `.kata/RESULT.json`.
   - `{{TIMESTAMP}}` — UTC ISO-8601 timestamp of the closeout moment (system clock at emit time).
3. Perform the substitutions **in-context** — the agent holds the template text and replaces each
   `{{TOKEN}}` with its resolved value. No Python, no shell script, no external rendering tool.
4. Write the fully-substituted HTML to `.kata/closeout.html` with the `Write` tool. Every `{{TOKEN}}`
   must be replaced; none may remain in the final rendered artifact.

The `Write` tool (added to `allowed-tools` in the frontmatter) is used only for Step 2a/2b. The
behavioral guard — "never write files outside `.kata/`" — applies here; `Write` is scoped to `.kata/`
run artifacts only.

### Step 2c — Present the concise CLI summary (Tier 1), ending with the link

Present the **Tier 1 concise CLI summary** in-conversation, in the persona voice defined in
`protocol/persona.md`. The summary covers the §5 skeleton essentials (goal · what-changed-by-aspect
in 1–2 lines · did-it-hit · top risks · backout offer) and **must end with a clear link line**:

```
Full report: .kata/closeout.html
Markdown:    .kata/CLOSEOUT.md
```

This ending link line is a hard requirement (PLAN M1). It makes the durable artifact discoverable to
any operator or tool that can open a file path. Do not omit it.

### Step 2d — Carry forward to §5 order (below)

The §5 sections below remain in order for the full in-conversation report when the operator asks for
detail. In a two-tier run, the concise summary (Step 2c) is the default in-conversation account;
the §5 detail is available on request and is fully captured in `.kata/CLOSEOUT.md`.

### §5.1 — Goal, restated

Open with the goal in plain language, taken directly from the frozen `INTENT.md`:

> "You wanted [goal statement from INTENT.md]."

No preamble. One or two sentences.

### §5.2 — What changed and why it matters to you (lead section — before any path or gate number)

Present the change story in **plain language**, organized **by goal-aspect** — the dimension of the goal
each change served. Each parallel worker's result folds into the goal-aspect it served.

- Group changes under headings like "To give you X, I…" or "To handle Y, I changed…"
- No file paths in this section. No gate numbers. No internal stage names (GRILL/FREEZE/…).
- If `kata-evaluate` returned NEEDS_WORK, report plainly what did not land: "I attempted X but it did
  not pass the check — here is what the check found." Never minimize or reframe a NEEDS_WORK.

This is the WS-5 hard requirement: plain-language what-changed-and-why leads every closeout.

### §5.3 — Did it hit the goal?

Honest assessment against the restated goal: fully / partially / here is the gap. One paragraph.
Quote the `kata-evaluate` verdict verbatim (from `.kata/RESULT.json`) — do not paraphrase it or confer
your own pass/fail. A NEEDS_WORK is reported plainly, never overridden.

### §5.4 — Risks and uncertainties

Name what is not fully certain, what is *exercised-not-proven* (run once end-to-end but no automated
regression), and what could bite. Follow the `protocol/persona.md` honesty norms: do not upgrade
"exercised" to "proven"; do not claim gated-off capabilities are live.

### §5.5 — Evidence, linked not dumped

For whoever wants to dig — list by path, do not re-transcribe:
- `.kata/RESULT.json` (gate result)
- `.kata/CLOSEOUT.md` (the full Markdown report — source-of-truth)
- `.kata/closeout.html` (the rendered HTML report)
- `.kata/understand.md` — **only if** the understand-map was generated (Step 3 is opt-in)
- Any findings files (DEFERRED.md, ASSUMPTIONS.md, etc.)

### §5.6 — Your options (offered choices)

Present the options in plain language as explicit choices:

1. **Keep it** — commit / push / merge (the existing human-gated git actions; see Decision 2 below).
2. **Iterate** — run again (version-up) or build something new.
3. **Cleanly undo the whole run** — "I can cleanly roll this entire run back, as if it never happened."
   (See Decision 4 — Backout, below.)

**Foreground option 3 when the human is not satisfied** with the result.

### Note on richer native rendering (M8 — deferred adapter work)

The CLI summary names the clickable `.kata/closeout.html` path; terminals and GUI shells make file
paths openable. Richer native rendering — a Claude `Stop`/`SessionEnd` hook that surfaces the report
automatically, a statusline verdict line, or per-tool equivalents for Codex/Kiro/Quick via their
adapters — is **out of scope here** and captured as a follow-up (PLAN M8).

## Step 3 — Offer the understand-map (opt-in)

**Offer** [[kata-understand]] to the human after the report is presented. This step is opt-in per run —
the human may skip it. When accepted:
- `kata-understand` produces a structured comprehension map of what changed + what was built, backed by
  the `kata-graph` runtime (graph-backed primary path; git/diff light fallback when the graph is
  unavailable).
- It is a comprehension aid, not a re-evaluation. It never blocks or gates.
- When run, it writes the map to `.kata/understand.md` — the path [[kata-loop]]'s loop-back carries
  forward.

## Step 3b — debug-run confidence report (ADDITIVE — debug run only; BC: absent `kata/module/debug` ⇒ silent no-op)

**If `kata/module/debug` is in the run's `modules`**, after the standard report (Step 2) and the opt-in
understand-map (Step 3), **offer/compose** [[kata-debrief]] to produce the **LD12 debug-run confidence
section** and fold it into the closeout deliverables alongside the standard report. When `kata/module/debug`
is absent this is a **silent no-op** (the module degrades gracefully, like every optional module); the general
closeout is **byte-for-byte unchanged** — this section fires **IFF `kata/module/debug` ∈ modules, NEVER off
`runShape` and NEVER off `target.kind=="existing"` alone** (those fields are also set by version-up; keying on
them would break BC for version-up/greenfield/one-shot closeouts).

[[kata-debrief]] is the LLM-judgment author/renderer for the LD12 report. It renders the four LD12 elements —
the per-module **confidence map** (assessed / low-confidence / skipped, labeled "heuristic (v1, uncalibrated)"),
the **deviation → fix → pinning-test** traceability rows, the **regression + security proof** (drift PASS +
characterization suite green + new pinning tests + mutation non-vacuous + real Snyk before/after), and the
**recommendations list + offered follow-on version-up/sprint** handoff — and states the §5 behavioral-only,
LD5 heuristic-confidence, and n=0-live honesty in every output. It produces both tiers in the `kata-report`
shape, so its debug section is folded into **`.kata/CLOSEOUT.md`** (Step 2a source-of-truth) and
**`.kata/closeout.html`** (Step 2b render) next to the standard §5 report content. `[[kata-debrief]]` is a
**forward reference** resolved at integration (built by Slice B in the same wave — expected not to exist during
this slice's editing; no broken-wikilink concern at this stage, the same convention P2b used for
`[[kata-characterize]]`).

**It still never gates** — gating stays with [[kata-evaluate]] (Hard boundary above; spine principle #4). This
section only adds a report section and an **offered** follow-on; it confers no verdict and overrides no
NEEDS_WORK. The two debug follow-ons reuse the **existing** decision gate below — **no new git path, no new
decision**:
- The **offered version-up/sprint** follow-on is surfaced in the existing **Decision 3** (loop disposition) —
  handed to the [[kata-loop]] conductor's loop-back, never auto-started.
- Committing the **left-behind characterization suite** (authored into the target repo by `kata-characterize`)
  is surfaced via the existing **human-gated Decision 2** git actions — under the same behavioral guard
  (diff-first / explicit approval), never autonomous.

## Step 4 — Human decision gate

Present the four decisions in sequence. Carry out only what the human explicitly approves.

### Decision 1 — Satisfaction

> *Are you satisfied with this run's output?*

- **Satisfied** → proceed to Decision 2.
- **Not satisfied** → surface the specific NEEDS_WORK items from `.kata/RESULT.json` + the `kata-report`
  drift ledger; foreground the backout option (Decision 4) as a first-class plain choice: "I can cleanly
  roll this entire run back, as if it never happened." Let the human decide whether to undo (Decision 4),
  loop (Decision 3), or stop.

### Decision 2 — Git actions (only if satisfied or explicitly requested)

> *Commit / push / merge?*

Present the available git actions based on the current branch state (read via `Bash git status`):
- **Commit** — stage the declared footprint files and commit with a conventional commit message.
- **Push** — push the branch to the remote (only after explicit approval).
- **Merge** — merge to the target branch (only after explicit approval; present a dry-run diff first).

Carry out **only the actions the human selects**. Never auto-push or auto-merge. The git actions are
**human-gated** (spine principle #2 — no plan drift; no autonomous git actions beyond commit).

### Decision 3 — Loop disposition

> *Run again (version-up) or build something else?*

- **Run again (version-up)** — the next cycle re-enters the initiation module with this run's context as
  baseline: the understand-map (`.kata/understand.md`), the report, and any lessons. The [[kata-loop]]
  conductor carries this context into the next cycle's [[kata-initiate]] (see kata-loop's loop-back
  Path A).
- **Build something else** — a fresh initiation. The conductor starts a new loop cold.

Hand the human's decision to the conductor's loop-back as a durable artifact (written via [[kata-handoff]]).

### Decision 4 — Backout (WS-4; human-gated, never autonomous)

> *Cleanly undo this entire run, as if it never happened?*

Offer this in plain language:

> "I can cleanly roll this entire run back, as if it never happened. This resets the repository to the
> exact state it was in before this run started."

**Anchor:** `.kata/RESULT.json.baselineSha` — read in Step 1. This SHA is the **guaranteed** backout
point (emitted by `gate_emit.py` at run start; always present in the artifact). A `pre-<run>` tag is
optional convenience, not the anchor.

**Execution — human-gated, never autonomous:**
1. Show the diff first: `git diff <baselineSha>..HEAD --stat` — so the human sees exactly what will be
   discarded before approving.
2. Require **explicit approval** from the human ("yes, roll it back" or equivalent).
3. Only then execute: `git reset --hard <baselineSha>`
4. Confirm the reset completed and the working tree matches the baseline.

This action is **under the same behavioral guard as commit/push/merge** — never auto-run, never run
without the diff-first/explicit-approval sequence. Treat any autonomous rollback as a conformance
violation identical to an autonomous push.

**Foreground Decision 4 when the human is not satisfied** with the result (§5.6 / Decision 1 not-satisfied
path). It is a first-class option, not a footnote.

## Step 5 — Compose the two-way handoff

Compose [[kata-handoff]] for the session boundary. The handoff MUST include:
1. **Read-in order** — the canonical files to load to rebuild context.
2. **State** — branch / commit SHA / the gate result (`exitCode`, `passed`/`failed`/`skipped`).
3. **What shipped** — concretely, with paths from `.kata/footprint.json`.
4. **NEXT STEP** — the conductor's loop-back disposition (run-again or build-new) with enough context for
   the next session to start doing, not deciding.
5. **Open decisions for the human** — anything deferred or unresolved.

## Backward-compatibility and spine

- Closeout is **additive**. Absent the closeout module, the harness completes with `kata-evaluate` as today.
- The default-FAIL gate is **never weakened**: closeout never converts a NEEDS_WORK to a pass.
- The [[kata-loop]] conductor (Phase 3) sequences this skill and owns the loop-back; closeout hands it the
  human decision and the loop-back context payload.
- `allowed-tools` includes `Bash` only to read `.kata/` artifacts and carry human-approved git actions
  (including the backout `git reset --hard`). It never executes target code. `Write` is included only to
  emit `.kata/CLOSEOUT.md` and `.kata/closeout.html` (Step 2a/2b); it is scoped to `.kata/` run
  artifacts. **Note (known limitation):** `Bash` cannot be restricted to specific git subcommands in
  frontmatter, so the "never auto-push/merge/rollback" rule is a **behavioral** guard (human-gated
  above), not a structural one. Treat any push/merge/reset without explicit human approval as a
  conformance violation.
