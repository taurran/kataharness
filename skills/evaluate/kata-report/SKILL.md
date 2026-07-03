---
name: kata-report
description: >-
  Synthesize a goal-anchored, by-goal-aspect report of a completed unit of work (a sprint, or any gated
  build segment) from the durable trail — gate result, what shipped grouped by the goal-aspect each change
  served, drift ledger, open items. Use at a sprint boundary to give the human a reviewable summary before
  they steer, or standalone after any gated run. It REPORTS; it does not gate (kata-evaluate owns the
  default-FAIL gate) — so a one-shot run can reuse it too. Voice: protocol/persona.md.
license: Apache-2.0
version: 0.1.2
category: evaluate
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Write]
source: new (KataHarness original — the D32 report, minimal v1; sprint-cadence D85/D2)
tags:
  - kata/evaluate
  - kata/module/report
  - report
  - synthesis
  - boundary
  - goal-anchored
---

# kata-report — goal-anchored report of a gated unit of work

The minimal **v1** of the D32 report (sprint-cadence D2: *the per-sprint one-page report **is** `kata-report v1`,
not throwaway; D32 expands later*). It reads the durable trail and writes a single reviewable page.
It is the **stop-side** companion `kata-sprint` composes at a boundary — but it is delivery-agnostic, so
a one-shot run can invoke it after its gate too.

Voice is governed by `protocol/persona.md`: plain-language-first, lead with outcomes not machinery, warm
through clarity, honest about uncertainty. The report renders in the persona's voice throughout.

## Hard boundary — it reports, it never gates

`kata-report` **synthesizes**; it does **not** evaluate or decide. The default-FAIL gate is and stays
`kata-evaluate` (D22). `kata-report` only *transcribes* the gate's verdict + numbers into the page. It
owns no pass/fail authority — if there were no green gate, the report says so, it does not confer one.

## Two-tier output (WS-3 follow-up, M1/M5)

`kata-report` composes **both tiers** from the run artifacts (`.kata/RESULT.json`, `footprint.json`, the
diff, and `INTENT.md`). The two tiers are:

1. **The concise CLI summary** — presented in-conversation at end-of-run, in the persona voice.
2. **The full report content** — the complete M5 skeleton, keyed to the exact `{{TOKEN}}` placeholders
   consumed by `kata-closeout` (slice S3) when it fills the committed HTML template.

`.kata/CLOSEOUT.md` is the **source-of-truth** for the full report: it is the durable Markdown document
that carries the complete M5 skeleton in plain text. The HTML at `.kata/closeout.html` is rendered from
the same content by `kata-closeout` via in-context token fill of the committed template at
`modules/closeout/resources/closeout-report.template.html`. The Markdown is the authoritative artifact;
the HTML is the polished presentation layer.

---

## Tier 1 — the concise CLI summary

This is the short, in-conversation account a non-expert owner reads to understand what happened. It
follows the persona voice defined in `protocol/persona.md`: plain-language-first, lead with outcomes,
warm through clarity, never chatty or jargon-laden. Internal stage names (GRILL / FREEZE / EXECUTE /
EVALUATE / HANDOFF / IMPROVE) are never surfaced.

The summary covers, in order:

### 1. Goal (one or two sentences)

"You wanted X." Lifted verbatim or closely paraphrased from the frozen `INTENT.md`. No preamble.

### 2. What changed and why — by goal-aspect (1–2 lines each)

The change story in plain language, organized by the goal-aspect each change served. For each goal-aspect
that the run addressed:

> **To give you [goal-aspect]:** [one or two plain-language sentences on what changed and why it matters
> to the owner — no file paths, no gate numbers.]

If `kata-evaluate` returned NEEDS_WORK on a goal-aspect, state it plainly:
"I attempted [X] but it did not pass the check — [brief plain-language finding]." Never minimize a
NEEDS_WORK.

### 3. Did it hit the goal?

One honest sentence: fully / partially / here is the gap. Quotes the `kata-evaluate` verdict verbatim
(from `.kata/RESULT.json`). Never re-interprets or softens the verdict.

### 4. Top risks (bullet list, ≤3 items)

What is not fully certain; what is exercised-not-proven; what could bite. In the persona's honesty
register: "exercised, not proven" is never upgraded. Keep it brief — detail belongs in the full report.

### 5. Backout

One plain-language sentence naming the backout option:
"I can cleanly undo this entire run, as if it never happened."
Then the literal command, anchored on `.kata/RESULT.json.baselineSha`:
`git reset --hard <baselineSha>`

The backout is offered, never auto-run. It is a destructive `git reset --hard`; it executes only on
explicit human approval, per the human-gated git guard (`kata-closeout` L9).

### 6. Link to the full report (REQUIRED — ends the summary)

The summary **must end** with a clear link line:

```
Full report: .kata/closeout.html
Markdown:    .kata/CLOSEOUT.md
```

This is a hard requirement (PLAN M1). The link makes the durable artifact discoverable to any operator
or tool that can open a file path.

---

## Tier 2 — the full report content (M5 skeleton, mapped to template tokens)

This section specifies what content goes into each `{{TOKEN}}` in the committed template. The token
names are the exact contract defined in the PLAN (§Placeholder token contract). Do NOT invent new
tokens or rename existing ones. Slice S3 (`kata-closeout`) substitutes these into the template.

### `{{RUN_TITLE}}`

A short human-readable title for this run: the goal stated in ≤10 words, followed by the run date.
Derived from `INTENT.md` (goal field) + `RESULT.json` (timestamp or run id).

Example: `"Two-tier closeout report — 2026-06-24"`

### `{{VERDICT_BADGE}}`

Two parts consumed by the template:
- **Text:** the `kata-evaluate` verdict string verbatim from `.kata/RESULT.json` (`PASS`, `PARTIAL`, or
  `NEEDS_WORK`).
- **State class:** one of `badge--pass` / `badge--partial` / `badge--needs-work` — the exact classes the
  template's inline CSS defines (kata-closeout emits `<span class="badge badge--{STATE}">`, STATE ∈
  `pass`/`partial`/`needs-work`), coloring the badge green / amber / terracotta per the brand system.

Source: `.kata/RESULT.json` → field `verdict`. Never re-derived; always quoted from the artifact.

### `{{GOAL}}`

The restated goal in 1–2 plain-language sentences. Source: the frozen `INTENT.md` goal statement.
Written as "You wanted X." in the persona voice (`protocol/persona.md`). No preamble.

### `{{CHANGED_BY_ASPECT}}`

A **repeatable block** — one instance per goal-aspect the run addressed. Each block contains:

```
<aspect-heading>: [goal-aspect label, plain language]
<aspect-body>: "To give you [aspect], I [what changed and why it matters to the owner]."
```

Rules:
- Organized by goal-dimension, not by worker, file, or execution order.
- No file paths in this section. No gate numbers.
- If a goal-aspect did not pass `kata-evaluate`, state it plainly in the body: "I attempted [X] but it
  did not pass the check — [brief finding]."
- Each parallel worker's result folds into the goal-aspect it served.
- Source: diff + `RESULT.json` goal-aspect breakdown (if present) + plan task mapping.

The template uses a documented repeatable-block pattern (see the HTML comment at the top of
`modules/closeout/resources/closeout-report.template.html`). S3 iterates over the aspect blocks and
substitutes one template block per aspect.

### `{{HIT_ASSESSMENT}}`

Honest 1–3 sentence assessment of progress against the restated goal: fully hit / partially hit / not
hit, with a plain-language account of the gap where applicable. Quotes the `kata-evaluate` verdict
verbatim; adds the plain-language reading for a non-expert. Source: `.kata/RESULT.json` verdict + counts.

### `{{RISKS}}`

Risks and uncertainties — what is not fully certain, what is exercised-not-proven, what could bite. In the
honesty register of `protocol/persona.md`: "exercised, not proven" is never upgraded. Typically 3–5 items.

**Render each as a warning tile** (the template defines `.tile--warning`, ochre) so the section is scannable:

```html
<div class="tile tile--warning"><div class="tile-label">Watch</div><p>{the risk, plain language}</p></div>
```

For any **critical error / NEEDS_WORK** item, use `<div class="tile tile--error">…</div>` (rust) instead so it
stands out. A plain `<ul>` is an accepted fallback, but tiles are the standing design — they break the report
up and make it easy to read.

### `{{EVIDENCE}}`

A linked list of evidence artifacts — for whoever wants to dig. Must include:

1. `.kata/RESULT.json` — gate result: name, exit code, counts (pass / fail / skip) quoted verbatim.
2. Diffstat — `git diff --stat <baselineSha>..<resultSha>` output, embedded inline.
3. Footprint manifest — the list of files actually touched, asserting the set is a subset (`⊆`) of the
   plan's declared file-ownership partition. Any file outside that set is an unauthorized deviation.
4. Mutation / non-vacuity proof — the record confirming real behavior was exercised (mutation-test
   summary, before/after snapshot, or logged probe). If absent, note the gap explicitly.
5. Links (by path) to any other committed evaluation artifacts: findings files, understand-map (if
   generated), assumptions log.

### `{{BACKOUT}}`

Two elements:

1. **Plain-language offer:** "I can cleanly undo this entire run, as if it never happened. The baseline
   commit is `<baselineSha>`."
2. **The literal command:** `git reset --hard <baselineSha>` — anchored on
   `.kata/RESULT.json.baselineSha` (the already-emitted baseline; always present at closeout).

A PLAN may additionally have set a convenience tag (e.g. `pre-<run>`), but the **guaranteed** anchor is
the emitted baseline SHA. The backout is destructive; it executes only on explicit human approval. Never
auto-run. This surfaces the L9 option foregrounded for a dissatisfied operator.

The template wraps this content in a **fixed error tile** (`.tile--error`, rust) — provide only the
plain-language sentence + the `<code>command</code>`, not the wrapping `<div>`.

### `{{GATE_NUMBERS}}`

The gate counts, quoted verbatim from `.kata/RESULT.json`:
- Tests: `<pass> passed / <fail> failed / <skip> skipped`
- Build hash (deterministic): `<hash>` (if present)
- Security: the scan's terminal **state** — tool-agnostic (F6): `clean` (0 findings) · `accepted`
  (documented `.snyk` acceptance + board DECISION, reason + expiry — quote the acceptance, not just a count)
  · `degraded` (scanner unavailable / toolchain unsupported under `securityScan: when-available`, surfaced)
  · `off` (policy opt-out) · or "N/A — non-code-bearing". Report the **state**, not merely a raw count —
  a nonzero count with a sound documented-acceptance is a passing terminal state, not a failure.

Never re-computed; always quoted from the artifact.

### `{{SHAS}}`

Baseline SHA → result SHA pair:
- Baseline: `.kata/RESULT.json.baselineSha`
- Result: `.kata/RESULT.json.resultSha` (or `git rev-parse HEAD` at close)

Format: `<baselineSha> → <resultSha>` (short or full — match the template's expected length).

### `{{TIMESTAMP}}`

UTC timestamp of the closeout: ISO 8601, e.g. `2026-06-24T20:36:18Z`. Read from system clock at the
moment `kata-closeout` emits the artifacts (not from the gate run timestamp, which may differ).

---

## What the durable page contains (retained from v1, now also feeds Tier 2)

A durable, one-page synthesis. Sections in order:

### 1. Goal, restated

Plain language, from the frozen `INTENT.md`: "You wanted X." One or two sentences. No preamble.

### 2. What changed and why it matters — by goal-aspect (lead section)

The change story in **plain language**, organized **by the goal-aspect each change served**. This is the
WS-5 hard requirement: it leads every report, before any path or gate number.

Group changes under goal-aspect headings, for example:

> **To give you [goal-aspect A]:** I built / changed…
> **To handle [goal-aspect B]:** I updated…

Each parallel worker's result folds into the goal-aspect it served — not listed by worker, by worker file,
or by execution order. The organizing principle is the *goal dimension*, not the implementation structure.

Rules for this section:
- **No file paths** in this section. No gate numbers. No internal stage names (GRILL/FREEZE/…).
- If `kata-evaluate` returned NEEDS_WORK on a goal-aspect, state it plainly: "I attempted [X] but it did
  not pass the check — [brief plain-language finding]." Never minimize or reframe a NEEDS_WORK.
- Write in the persona voice: lead with what it means for the human, not for the machinery.

### 3. Gate result

The `kata-evaluate` verdict + the green numbers verbatim: tests (pass/fail/skip), build
(deterministic hash), security — the scan's terminal **state** (`clean` / `accepted` / `degraded` /
`off`, tool-agnostic, per `{{GATE_NUMBERS}}` above), never a vendor-named raw count. **Never
re-compute — quote the gate** (from `.kata/RESULT.json` and the board DECISION for an acceptance).
If the artifact carries no security record, report it as **`unrecorded`** — NEVER fabricate a count
or a "clean" (adval F6-2/F6-4). A NEEDS_WORK is quoted as-is; it is not softened or reframed.

### 4. What shipped — by path

Concretely, by **path** (the files/skills added or changed), tied to the plan task ids. Assert that the
set of touched files is a subset of (`⊆`) the plan's declared file-ownership partition. Any file outside
that set is an unauthorized deviation and must appear in the drift ledger (section 5 below).

### 5. Drift ledger

The run's `driftLedger` (authorized vs unauthorized deviations, escalations, interventions) from
protocol state. Flag any unauthorized deviation explicitly. If there were none, state so briefly.

### 6. Risks and uncertainties

What is not fully certain, what is *exercised-not-proven* (run once but no automated regression), what
could bite. Governed by the `protocol/persona.md` honesty norms: "exercised, not proven" is not upgraded.

### 7. Open items

Anything deferred (`kata-defer` `DEFERRED.md`), assumptions logged (`ASSUMPTIONS.md`), and decisions
pending a human.

## Machine-readable artifacts the report MUST embed or reference

The report is the durable synthesis of the run's evidence trail. It **must** embed or point to (by path)
all three of the following artifact types — prose-only descriptions are not sufficient:

1. **`RESULT.json`** — the machine-readable gate output emitted during the `kata-evaluate` run. The
   report must quote (or path-link) the gate name, exit code, and `counts` (pass / fail / skip) verbatim
   from this file. Do **not** re-transcribe by hand; copy from the artifact.

2. **Footprint manifest + diff-stat** — the list of files actually touched by the run, plus the diff-stat
   summary (e.g. `git diff --stat baseline..result`). The report must assert that the set of touched files
   is a subset of (`⊆`) the plan's declared file-ownership partition. Any file outside that set is an
   unauthorized deviation and must appear in the drift ledger (section 5 above).

3. **Mutation / non-vacuity proof** — the record confirming that the test suite exercised real behavior
   (e.g., a mutation-test summary, a before/after snapshot, or a logged probe showing at least one
   meaningful assertion would fail if the logic were removed). This guards against a green gate achieved
   purely by disabling or vacuously passing tests.

All three artifacts are referenced by their committed path in the tier-2 durable trail. If any artifact is
absent, the report notes it explicitly as a gap — the "reports, never gates" principle does not change, but
absence is surfaced so `kata-evaluate` (or the human) can act.

## Discipline

- **Read the trail, don't re-derive.** Pull from the committed reports / state / board — the report is a
  synthesis of durable record, not a fresh investigation.
- **One page.** Dense and skimmable; the human reads it to decide whether to steer (at a boundary) or to
  confirm done (one-shot). Long detail belongs in the artifacts it points to, by path.
- **Lead with the goal-aspect synthesis** (section 2) — always before paths or gate numbers. This is the
  WS-5 hard requirement.
- **Lossless on the gate numbers + open items** — those drive the human's next decision.
- **Voice: `protocol/persona.md` throughout.** Plain-language outcomes before machinery; honest on
  uncertainty; no inflation.
- Write the report into the **tier-2 durable trail** (git-committed) so `kata-readiness` can find it on
  resume and `kata-sprint` can present it at the boundary.
- **Both tiers must be produced.** The concise CLI summary is what the owner reads in-conversation. The
  full M5 report, keyed to the exact `{{TOKEN}}` contract, is what `kata-closeout` (S3) uses to emit
  `.kata/CLOSEOUT.md` and render `.kata/closeout.html`. Neither tier is optional.
