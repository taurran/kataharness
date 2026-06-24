---
title: "WS-3 follow-up — two-tier closeout (CLI summary + linked branded report): frozen PLAN"
status: FROZEN (freeze before dispatch; supersede-not-edit once orchestration starts)
date: 2026-06-24
mode: version-up (target.kind = self; baseline = current green master `00e6e7c`)
non-code-bearing: true   # .md skills + .html/.css template only; .html/.css NOT in footprint._CODE_EXTENSIONS ⇒ codeBearing:false ⇒ mutation-proof exempt
extends: .planning/specs/ws3-user-friendliness/ (WS-3 closeout, slice F territory; L7/L9 hold)
field-exercise: >-
  This build is the WS-3 field-exercise (n=0→1): it is built through the friendly Kata Loop AND its own closeout
  is the first live instance of the two-tier output it produces (the operator reviews the real .kata/closeout.html
  at the gate — also the brand-refinement point).
ownership:
  S1: [modules/closeout/resources/closeout-report.template.html, modules/closeout/resources/BRAND.md]
  S2: [skills/evaluate/kata-report/SKILL.md]
  S3: [modules/closeout/kata-closeout/SKILL.md]
waves:
  wave1: [S1, S2]
  wave2: [S3]
depends_on:
  S1: []
  S2: []
  S3: [S1, S2]
tags:
  - kata/spec
  - ws3
  - closeout
  - report
---

# WS-3 follow-up — two-tier closeout (CLI summary + linked branded report)

## Goal
Make the closeout **two-tier**: (1) a **concise summary rendered in the CLI/GUI** at end-of-run (the goal-anchored
essentials, in the persona voice), that **ends with a link** to (2) a **durable in-depth report** — a clean,
on-brand, self-contained **HTML** report (`.kata/closeout.html`) with a **Markdown source-of-truth**
(`.kata/CLOSEOUT.md`) underneath. The chat stream is ephemeral and dense; a linked, polished report is something a
non-expert owner can open, keep, and trust. Extends WS-3 closeout (slice F); spine + WS-3 LOCKs (L7 never-gates,
L9 offered-backout) hold. **Non-code-bearing** (markdown + a static HTML/CSS template; no new Python).

## LOCKED decisions (no worker may re-decide; conflict ⇒ escalate human-required)
- **M1 — Two tiers.** Concise CLI summary (persona voice, goal-anchored essentials, **ends with the report link**)
  + a durable in-depth report. The summary is what shows in-conversation; the report is the keep-it artifact.
- **M2 — Two artifacts, MD is source-of-truth.** Emit **`.kata/CLOSEOUT.md`** (full Markdown report — durable,
  agnostic, the source) and render **`.kata/closeout.html`** (the pretty layer) from it. Both are run artifacts in
  `.kata/` (gitignored, like RESULT.json). The CLI summary links the HTML (MD as fallback).
- **M3 — HTML via in-context fill of a committed static template; NO new Python.** The template
  (`modules/closeout/resources/closeout-report.template.html`) is **self-contained** (inline CSS, no external
  asset/font/CDN deps — opens anywhere offline) with clearly-marked placeholder tokens. `kata-closeout` fills the
  tokens **in-context** at run end. (Honors prefer-in-context-over-new-python.)
- **M4 — Brand = the minimal 改善型 system (§Brand below).** Defined in the template + `BRAND.md`. The operator
  refines it at the gate (it is backout-able; the gate is the review point).
- **M5 — Content = the WS-3 §5 goal-anchored skeleton, by-goal-aspect.** CLI summary = trimmed essentials; the
  report = the full skeleton (goal · what-changed-why by aspect · did-it-hit · risks/uncertainties · evidence
  links + diffstat + gate numbers + SHAs · offered backout).
- **M6 — Closeout still NEVER gates (WS-3 L7) and still offers backout (L9).** The report and summary surface the
  `kata-evaluate` verdict verbatim and the `.kata/RESULT.json.baselineSha`-anchored backout; closeout confers no
  pass/fail of its own.
- **M7 — Non-code-bearing.** Only `.md` (skills, BRAND.md, CLOSEOUT.md) + `.html`/`.css` (template). Verified:
  `.html`/`.css` are NOT in `footprint._CODE_EXTENSIONS` ⇒ `codeBearing:false` ⇒ mutation-proof exempt. **No new
  Python, no new config field, no validator change.** The rendered `.kata/closeout.html` is a run artifact (not committed).
- **M8 — Per-tool link surfacing stays thin here.** The CLI summary names the clickable `.kata/closeout.html`
  path (terminals/GUIs make file paths openable). Richer native rendering (Claude `Stop`/`SessionEnd` hook,
  statusline verdict line; other tools' surfaces) is **adapter work, OUT OF SCOPE** — captured as a follow-up.
- **M9 — Roster.** Workers = **Sonnet**; orchestrator + `kata-evaluate` + grader = **Opus** (Fable 5 unavailable).
- **M10 — Policy A:** skills stay `0.1.0`; the template/BRAND carry no semver (not skills).

## Brand — the minimal 改善型 system (S1 must implement; operator refines at gate)
Self-contained, dark, editorial-but-technical. Single source of CSS = inline `<style>` in the template.
- **Palette:** ground `#14141B` · card surface `#1C1C26` · border `#2E2E3C` · text `#EAEAF2` · muted `#9AA0B4` ·
  **accent (kaizen green) `#5BD6A6`** · warm highlight (sparingly, wordmark dot / gate-pass) `#D4A843` ·
  alert/needs-work `#E0764A`.
- **Type:** display/headers = `ui-monospace, "Cascadia Code", "JetBrains Mono", Consolas, monospace`;
  body = `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`. (No web-font fetch — offline-safe.)
- **Identity:** wordmark **`改善型 · KATAHARNESS`** in the header; a subtle loop ribbon
  **`GRILL ▸ FREEZE ▸ EXECUTE ▸ EVALUATE ▸ HANDOFF ▸ IMPROVE`** as a thin band; a **verdict badge**
  (green = goal-hit/PASS · amber = partial · terracotta = NEEDS_WORK).
- **Layout:** single column, ~`720px` max-width centered card, generous line-height, rounded corners, a thin
  accent left-border on each section heading. Sections in the M5 order. Footer = gate numbers · baseline→result
  SHAs · UTC. Calm, legible, not busy — matches the persona (calm craftsperson; never gaudy).

## Placeholder token contract (S1 defines, S2 fills with content, S3 substitutes)
The template MUST use these exact tokens (so S2/S3 agree): `{{RUN_TITLE}}` · `{{VERDICT_BADGE}}` (text + state
class) · `{{GOAL}}` · `{{CHANGED_BY_ASPECT}}` (repeatable aspect blocks: aspect heading + plain-language
what+why) · `{{HIT_ASSESSMENT}}` · `{{RISKS}}` (list) · `{{EVIDENCE}}` (linked list incl. diffstat) ·
`{{BACKOUT}}` (the plain-language backout line + command) · `{{GATE_NUMBERS}}` · `{{SHAS}}` · `{{TIMESTAMP}}`.
S1 documents the token list at the top of the template as an HTML comment so S2/S3 can rely on it.

## Slices

### S1 — report template + brand · wave 1 · not code-bearing
- **read_first:** this PLAN (§Brand + §Placeholder tokens), `.planning/specs/ws3-user-friendliness/DESIGN.md` §5
  (the closeout skeleton the report renders), `tools/kata_web.py` (existing 改善型 HTML/ASCII aesthetic for visual
  continuity — do NOT import it; just match the spirit), `docs/STANDARDS.md` §5.
- **action:**
  1. **Create `modules/closeout/resources/closeout-report.template.html`** — a self-contained HTML document with
     inline `<style>` implementing the §Brand system, laid out in the M5 section order, using the exact
     §Placeholder tokens. **No external CSS/JS/font/CDN refs** (offline-safe). At the top, an HTML comment listing
     every `{{TOKEN}}` and what it expects (the contract S2/S3 rely on). Include a `{{CHANGED_BY_ASPECT}}` repeatable
     block pattern (documented in the comment).
  2. **Create `modules/closeout/resources/BRAND.md`** — a short note recording the palette/type/identity/layout
     decisions (the durable brand reference; ≤1 screen).
- **acceptance:** template is valid self-contained HTML (opens offline; no external refs); implements the brand;
  uses exactly the §Placeholder tokens with a documented token-comment; `BRAND.md` records the system;
  `validate_skills.py` green (resources don't affect it, but confirm).
- **verify:** `cd tools && uv run python validate_skills.py` ; open the template in a browser to confirm it renders
  standalone (tokens visible as literal placeholders is fine).

### S2 — kata-report two-tier content · wave 1 · not code-bearing
- **read_first:** `skills/evaluate/kata-report/SKILL.md` (current by-goal-aspect synthesis from WS-3 slice F),
  `.planning/specs/ws3-user-friendliness/DESIGN.md` §5, this PLAN (§Placeholder tokens), `protocol/persona.md` (voice).
- **action:** Extend `kata-report` to compose **both tiers** from the run artifacts (`.kata/RESULT.json`,
  `footprint.json`, the diff, `INTENT.md` goal):
  - **The concise CLI summary** — persona voice, goal-anchored essentials (goal · what changed & why in 1–2 lines
    per aspect · did-it-hit · top risks · backout line), **ending with the link** to `.kata/closeout.html`.
  - **The full report content** — the complete M5 skeleton, mapped to the §Placeholder tokens (so S3 can fill the
    template). Specify, per token, what content goes in it (esp. the repeatable `{{CHANGED_BY_ASPECT}}` blocks).
  - State that the MD report (`.kata/CLOSEOUT.md`) is the source-of-truth and the HTML is rendered from the same
    content. Reference `protocol/persona.md` by path (never `[[wikilink]]`).
- **acceptance:** `kata-report` specifies both the concise summary and the full report content keyed to the exact
  §Placeholder tokens; persona voice referenced by path; `validate_skills.py` green.
- **verify:** `cd tools && uv run python validate_skills.py` ; `grep -niE "CLOSEOUT.md|closeout.html|CHANGED_BY_ASPECT" skills/evaluate/kata-report/SKILL.md`.

### S3 — kata-closeout emit + render + link · wave 2 · not code-bearing · depends_on S1, S2
- **read_first:** `modules/closeout/kata-closeout/SKILL.md` (current §5 skeleton + Decision-4 backout from WS-3
  slice F — extend, don't break), this PLAN (§Placeholder tokens, M2/M3/M8), the S1 template path, the S2 content
  spec, `protocol/persona.md`.
- **action:** Extend `kata-closeout`'s reporting step so that, after composing the report content (via
  `kata-report`):
  1. **Emit `.kata/CLOSEOUT.md`** — the full Markdown report (source-of-truth).
  2. **Render `.kata/closeout.html`** — load `modules/closeout/resources/closeout-report.template.html` and
     **fill every `{{TOKEN}}` in-context** from the report content (no Python; the agent substitutes). Write the
     result to `.kata/closeout.html`.
  3. **Present the concise CLI summary** in-conversation (persona voice), **ending with a clear link line** —
     e.g. *"📄 Full report: `.kata/closeout.html` (Markdown: `.kata/CLOSEOUT.md`)"* — so the user can open it.
  4. Keep Decision-4 **backout** (L9) and the **never-gates** boundary (L7) intact; the report/summary surface the
     `kata-evaluate` verdict verbatim. Note M8 (richer native rendering is deferred adapter work).
  - Reference `protocol/persona.md` + the template path; never `[[wikilink]]` a resource.
- **acceptance:** closeout emits `.kata/CLOSEOUT.md`, renders `.kata/closeout.html` from the S1 template via
  in-context token fill, and the CLI summary ends with the report link; backout + never-gates preserved;
  `validate_skills.py` green.
- **verify:** `cd tools && uv run python validate_skills.py` ; `grep -niE "CLOSEOUT.md|closeout.html|template" modules/closeout/kata-closeout/SKILL.md`.

## Orchestration sequence (operator-gated; never inline)
1. **FREEZE** (this doc) + `git tag pre-ws3-report` on baseline `00e6e7c`. ◆ operator go.
2. **Wave 1:** worktrees off master; dispatch **S1, S2 concurrently** (Sonnet); workers self-stamp start/end; commit in-worktree.
3. **Integrate wave 1** into `ws3report/integration` (disjoint ⇒ no conflict).
4. **Wave 2:** worktree off integration; dispatch **S3** (Sonnet); commit.
5. **Integrate wave 2**; full gate: `pytest -q` (expect 447) + `validate_skills.py` (expect 36/0) + Snyk N/A.
   Emit `.kata/RESULT.json` + `footprint.json` (expect **`codeBearing:false`**, `withinFootprint:true`, 0 drift).
6. **Fresh-context Opus `kata-evaluate`** (no-write, default-FAIL) + build-acceptance check (below). Must PASS.
7. **FIELD-EXERCISE PAYOFF — dogfood the feature on its own build:** using the just-built S1 template + S3 flow,
   generate THIS build's **two-tier closeout** — emit `.kata/CLOSEOUT.md` + render `.kata/closeout.html`, and
   present the concise CLI summary ending with the link. ◆ **Operator opens `.kata/closeout.html`, judges the
   friendliness + brand, and refines** (the n=0→1 UX test + brand-review point).
8. **Operator gate** (`AskUserQuestion`): satisfied? · refine brand? · merge+push? · backout?

## Build-acceptance check (fresh-context, after the run)
1. Template is self-contained (no external refs), implements the brand, uses exactly the §Placeholder tokens (M3/M4). ✅/❌
2. `kata-report` composes both tiers keyed to the tokens; summary ends with the link (M1/M5). ✅/❌
3. `kata-closeout` emits `.kata/CLOSEOUT.md` + renders `.kata/closeout.html` via in-context fill; summary links it (M2/M3). ✅/❌
4. Backout (L9) + never-gates (L7) intact; verdict surfaced verbatim (M6). ✅/❌
5. Non-code-bearing: only `.md`/`.html`/`.css`; `codeBearing:false`; no new Python/config/validator (M7). ✅/❌
6. No `[[wikilink]]` to a resource/contract; persona referenced by path (K3 carryover). ✅/❌
7. Disjoint drift: each file ⊆ its slice ownership; spine intact. ✅/❌
8. Green: pytest 447 · validator 36/0 · Snyk N/A. ✅/❌

## Gate & backout
- **Gate:** `cd tools && uv run pytest -q && uv run python validate_skills.py`. (Snyk N/A — no Python. If any `.py`
  is touched the run is no longer non-code-bearing → escalate; the PLAN forbids it.)
- **Backout (offered at closeout):** `git reset --hard pre-ws3-report` — surfaced as a first-class plain-language option.

## Carry-outs (NOT in this run)
- **Richer native end-of-run rendering (M8) — adapter follow-up:** Claude `Stop`/`SessionEnd` hook that surfaces
  `.kata/closeout.html` + a statusline verdict line; per-tool equivalents (Codex/Kiro/Quick) via their adapters.
- WS-2 polish (worker self-timestamping wired into the board) — returns to the queue.
- Promote M1–M10 to DECISIONS (D96) at build-merge + STATE/HANDOFF/BACKLOG updates.
