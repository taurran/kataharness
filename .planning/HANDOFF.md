---
date: 2026-06-29 (a 5-feature subagent-driven arc, D117–D121: Debug Mode P3 [final phase] · recurrence-hardening T2 · IaC Tier-2 preview-half · second-brain Recall · Codex adapter live-hardened + multi-model LIVE; NEXT = adversarially validate the whole arc, THEN commit/push, THEN start the kata-loop-benchmark)
branch: master — private remote github.com/taurran/kataharness, tip a11b9de (all D117–D121 PUSHED + in sync; the THIS-SESSION doc updates [CONTEXT/HANDOFF/orientation] are UNCOMMITTED, to be committed next session after the ad-val pass)
green: validator 45 skills / 0 errors · pytest 1314 passed · Snyk medium+ 0 on all new/changed Python EXCEPT a flagged PRE-EXISTING item — `tools/kata_install.py` 6 LOW CWE-23 (in `..`-guarded code, below the medium+ gate, since D104/D108)
tags: pre-iac-specialist · pre-kata-preflight · pre-multimodel-layer · v0.1.0-alpha.3 · loop-hardening-complete
authored-for: kata-orient (sections map to the orientation tiers)
★ NEXT-SESSION START HERE: read `.planning/NEXT-SESSION-ORIENTATION.md` (self-contained, paste-able) — it sets the FIRST TASK = the adversarial-validation (ad-val) holistic red-team of D117–D121, then commit/push, then the kata-loop-benchmark. This HANDOFF body below is older historical context (D98–D116); STATE.md + DECISIONS.md D117–D121 are current.
---

> **★ 2026-06-29 UPDATE (D117–D121, a 5-feature subagent-driven arc — each through the full recipe):**
> **(D117)** Debug Mode **P3** — the FINAL phase; Debug Mode is now functionally complete at the skill/seam level
> (`tools/debug_report.py` LD12 closeout engine + `kata-debrief` + `kata-closeout` Step 3b + `kata-lang-profile` LD10
> [6 lang profiles] + `kata-onboard` LD13 + `kata-orchestrate` P3-seam/LD10-injection/Snyk-persist). D98 caught **2
> MAJOR fail-opens** (Snyk regression-masking; un-route-gated `applied:true`) → fixed at the engine.
> **(D118)** recurrence-hardening **T2** — recurrence→proposal, act-but-gated (`tools/recurrence_detect.py` +
> soft `failure_class` enum + nullable `run_id` in `validation_misses.py` + `kata-improve` v0.2.0 auto-draft +
> `kata-orchestrate` Final-gate detector hook + `protocol/validation-misses.md` T2). Invariant: T2 PROPOSES, never
> writes guards/decides/merges.
> **(D119)** IaC **Tier-2 preview/approve HALF** (execution DEFERRED) — `tools/iac_apply.py` (argv builders, plan-hash,
> typed self-binding capability-gate, `run_apply`=NotImplementedError seam) + exec-safety deferred rows + `iac-safety.md`
> §9 + both specialists v0.2.0. Catastrophic invariant (no reachable cloud mutation) holds **by construction**;
> live-apply future-gated on operator CLOUD creds.
> **(D120)** second-brain **Recall** (read-CONTRACT + files-only adapter) — `tools/recall.py` (shape-only/open-vocabulary
> contract, files-only adapter, hard token-overlap selection, NO embeddings, NO write path) + `protocol/recall.md` +
> `engram.backend` naming + `kata-initiate` v0.2.0 Phase-1b/mirror wiring. INTENT-never-written is STRUCTURAL. Decider
> (`kata-reason`) + write/distill half DEFERRED.
> **(D121)** Codex adapter **live-hardened + multi-model layer confirmed LIVE (n=0→1)** — operator installed Codex CLI
> 0.142.3 (ChatGPT-authed); first live run of the D108 chain caught a real defect → fixed (`--skip-git-repo-check` +
> `stdin=DEVNULL`). `kata_install.py --platform codex --confirm` → `confirmed:true`. Read-only validator/researcher
> routing now LIVE-proven; coder-routing + evaluator-thresholds still DEFERRED.
> **Gates:** pytest **1314** · **45 skills / 0** · Snyk **0** on all new/changed Python EXCEPT a flagged PRE-EXISTING
> `kata_install.py` **6 LOW** CWE-23 (separate hardening candidate). All D117–D121 committed + pushed (tip `a11b9de`).
> **NEXT (operator's explicit sequence): (1) adversarially validate the whole D117–D121 arc** (a fresh-context holistic
> red-team over the 5 builds + the seams BETWEEN them — the per-build D98s happened, the between-build seams did not);
> **(2) then commit/push** the doc updates + any ad-val fixes (each its own D-number); **(3) then start the
> `kata-loop-benchmark`** (queue item (e) step 2 — needs a grill). **(4) Operator intends to PROVIDE A REPO to intake**
> — confirm what they want done with it. Full detail: `.planning/NEXT-SESSION-ORIENTATION.md`, `STATE.md`,
> `DECISIONS.md` D117–D121.

> **★ 2026-06-27 UPDATE (D111–D116, a 6-feature subagent-driven day):** **(D111)** holistic red-team of the D108/D109/
> D110 builds → fixed a real preflight RCE + IaC gate-skips + fail-opens. **(D112)** `protocol/exec-safety.md` standing
> guard + `test_exec_safety.py` — the RCE class recurred 3× in kata-preflight; now structurally guarded. **(D113)**
> Debug Mode **P1** — the `function_model` oracle (`tools/function_model.py`, AST-safe `_safe_eval`) + `kata-comprehend`
> + the `kata/module/debug` run-shape. **(D114)** the **validation-miss manifest** (`tools/validation_misses.py` +
> `protocol/validation-misses.md`) — universal, observe-only data layer for recurrence-hardening (operator's idea).
> **(D115)** Debug Mode **P2a** — the deviation-discovery pipeline (`tools/deviation.py` + `kata-deviate`). **(D116)**
> Debug Mode **P2b** — the PROTECT half (`tools/drift_gate.py` + `kata-characterize` + the fix-application loop). **The
> core Debug Mode loop went COMPLETE (comprehend → find → characterize/drift-gate/apply-or-defer); D117 then added the
> report/onboard P3 capstone.** Every phase built ENTIRELY via subagents and the standing D98 lens caught a real
> fail-open on every one. Full detail: `.planning/NEXT-SESSION-ORIENTATION.md`, `STATE.md`, `DECISIONS.md` D111–D121.

# HANDOFF — KataHarness — 2026-06-26 (install-portability BUILT · multi-model GRILLED+FROZEN+proof-slice · red-team hardened · banner — D104–D107)

> **This session: a deep strategy + hardening arc on top of the (already-done) WS-1/2/3 + two-tier closeout.** Four
> decisions, D98–D101: **(D98)** the **standing adversarial red-team** is now wired — `kata-review` runs after
> `kata-evaluate` PASS, before merge, on every code/contract-bearing build; `kata-evaluate` gained rubric **item 9
> "reproduce, don't trust"** (regenerate derived artifacts; execute claimed seams). This baked in L10c, a lesson
> the project recorded a month ago but never wired, so it kept recurring (L12). **(D99)** the **loop-learning
> strategy** is locked — ship **Controlled (A)** now, **Gated-learning (C)** is the destination, **Hermes-fluid (B)**
> is a trap; the learning subsystem is re-modeled **Second brain + Recall + Reason** (`kata-reason`; "engram"
> retired, rename pending), C gated by a **four-tumbler unlock** + the **C/B invariant**; `kata-loop-benchmark`
> promoted to keystone. Spec `specs/second-brain-learning/BRIEF.md`. **(D101)** **recurrence hardening** captured —
> when a failure-class recurs, the loop hardens the responsible agent (gated, never auto-mutate); the harness-facing
> sibling of Reason. Spec `specs/recurrence-hardening/BRIEF.md`. **(D100)** the **fix-loop hardening** was **built
> through the main orchestrated loop** — material (footprint-scoped) re-verification + a per-area (N=2) + run-level
> (`2×tasks+2` `[TUNABLE]`) thrash budget → `kata-diagnose` fix-vs-plan verdict → human only on a plan-problem;
> freeze-gate HOLD→resolved, re-confirm HOLD→resolved, build `kata-evaluate` PASS 7/7 + standing D98 red-team
> SHIP-WITH-FIXES (fixed). **The adversarial lens caught the phantom-machinery / over-claimed-reuse class FOUR times
> this session** → memory `verify-primitives-before-claiming-reuse`. Fresh/compacted session: read §1, confirm green
> (§2).

## 1. Read-in order  *(orientation: CONTEXT)*
1. `AGENTS.md` (spine + conventions; the **"The Kata Loop"** entry) · 2. `docs/STANDARDS.md` §1 (frontmatter —
   `allowed-tools` REQUIRED) · 3. `CONTEXT.md` (glossary — now extended with the D117–D121 surfaces:
   debug-report/kata-debrief/kata-lang-profile/kata-onboard · recurrence T2 · iac_apply · Recall · multi-model-LIVE) ·
4. `.planning/STATE.md` (top CURRENT box — live picture) · 5. **`.planning/DECISIONS.md` D117–D121** (this session) ·
6. **`.planning/DECISIONS.md` D111–D116** (the prior session — exec-safety guard + Debug P1/P2a/P2b + validation-miss
   manifest) · 7. `protocol/{reuse-claims,exec-safety,validation-misses,recall,iac-safety}.md` (the standing guards +
   the new contracts) · 8. `.planning/LESSONS-LEARNED.md` (esp. **L12** — wire lessons into skills).
⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated, harness-injected). PokeVault is LOCAL-ONLY, never git.

## 2. State *(orientation: VOLATILE)*
- Branch `master`, tip `a11b9de` (**D121 Codex adapter live-hardened + multi-model LIVE** · D120 Recall · D119 IaC
  Tier-2 preview-half · D118 recurrence T2 · D117 Debug Mode P3 — `git log --oneline -10` for the arc). **45 skills /
  0 · pytest 1314 · Snyk med+ 0** (PRE-EXISTING `kata_install.py` 6 LOW CWE-23 flagged, below gate). **All D117–D121
  committed + pushed, in sync.** The THIS-SESSION doc updates (CONTEXT/HANDOFF/orientation) are **uncommitted** — they
  get committed next session after the ad-val pass (an operator decision: keep the docs out of the tree the ad-val
  red-teams).
- **Codex CLI is LIVE** at `C:\Users\taurr_nvs748q\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` (version 0.142.3,
  ChatGPT-authed). It is **NOT on PATH** — prepend that bin dir for codex invocations; the harness probe needs it on PATH.
- **The arc is older context now in CONTEXT.md + STATE.md.** Debug Mode is functionally complete at the skill/seam
  level (P1→P3) but **still n=0 LIVE** (never run end-to-end on a real repo — queue item (a)). IaC Tier-2 live-apply
  EXECUTION is DEFERRED + creds-gated. Recall's decider (`kata-reason`) + write/distill half are DEFERRED. Multi-model
  coder-routing + evaluator-thresholds are DEFERRED.
- **Historical (still true):** the Kata Loop is fully built + proven (Phases 0–3 + Phase-4 dogfood); loop-hardening is
  DONE (G1–G7, G6 proven by the S3b live loop-back). WS-1/2/3 + two-tier closeout shipped. Debug Mode P1–P3, the
  exec-safety standing guard, the validation-miss manifest, the IaC Tier-1 specialists, kata-preflight, the multi-model
  layer, and install-portability all shipped across D102–D121.

## 3. NEXT ACTION — resume here *(VOLATILE — the operator's EXPLICIT sequence)*
**The next session's spine — do these IN ORDER:**
1. **FIRST TASK: adversarially validate ("ad-val") the whole D117–D121 arc** — a fresh-context, cross-cutting holistic
   red-team over the 5 builds + the seams BETWEEN them (mirror the D111 holistic-red-team pattern: parallel
   fresh-context reviewers → synthesis → operator-gated fix scope). The per-build D98s already happened; the
   **between-build seams are unreviewed as a set** — the shared `kata-orchestrate`, the shared `validation_misses.py`
   (T2 extended it; debug consumed it), the exec-safety registry (IaC added deferred rows), and the multi-model
   surfaces (live now). See the ORIENTATION §2 for how to run it.
2. **THEN commit/push** — the uncommitted doc updates from THIS session (CONTEXT/HANDOFF/orientation) + any fixes the
   ad-val produces (each its own D-number, supersede-never-rewrite, trailer
   `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`). git may diverge from operator GitHub-web edits →
   `git fetch` + rebase before push (happened this session with LICENSE/README web edits → `cae9fae`/`6a15bfb`).
3. **THEN start the `kata-loop-benchmark`** (queue item (e), step 2 — the C-arc keystone, D99). It needs a fresh grill
   (deferred this session). **Captured pre-decisions so the next session doesn't re-derive** (see ORIENTATION §4):
   smallest-v1 = a DETERMINISTIC scorer over `.kata/{RESULT,footprint,mutation}.json` + the frozen `01-cli-wordfreq`
   fixture + run-metadata → `.kata/benchmark/<run-id>.json` scorecard; reuse the now-LIVE multi-model machinery;
   fairness = frozen task + fresh context per arm + constant Claude model (D13/D14). **Operator pre-decided:**
   build-vs-adopt deferred (lean native); **include the LIVE multi-model arm in v1** (spend ~1 Codex run for a real
   single-vs-multi n=1 number); scoring metric set + LLM-judge = GRILL next session.
4. **Operator will PROVIDE A REPO to intake** — flag prominently. Likely the Debug Mode end-to-end live-run target
   (queue item (a), still n=0 live) or a new build target. **Confirm what they want done with it before assuming.**

> **Process reminder (the discipline that paid off ~5× this session):** every contract/code-bearing build is
> grill/plain → freeze → **freeze-gate adversarial review (HOLD/SHIP)** → orchestrated build (subagents, disjoint
> ownership, TDD, mutation-proof) → integration gate (pytest + validate 45/0 + Snyk + central README --write) →
> fresh-context **kata-evaluate (PART A, default-FAIL)** → standing **D98 kata-review (PART B, adversarial)** →
> re-confirm after fixes → operator merge gate → checkpoint. **D98 is load-bearing** (caught real fail-opens on most
> builds this session). Guards: exec-safety, verify-before-reuse/cite-by-anchor, the validation-miss manifest, and the
> now-LIVE multi-model confirm-probe (the standing guard for stale per-CLI flags).

## 4. The orchestration recipe (each cycle's *inner* build follows this — never inline) *(task-type hint)*
The **vetted, never-inline** loop, driven ENTIRELY via subagents (operator directive — spare main context):
1. **Delegate the PLAN** to a planning subagent → it writes `.planning/specs/<feature>/PLAN-*.md` + returns a compact
   summary. **Freeze** it (LOCKED decisions + disjoint file-ownership slices + per-slice runnable `verify`). Commit + tag.
2. **Freeze-gate** via a fresh-context `kata-review` subagent (HOLD/SHIP) → apply fixes via the planning agent → FROZEN.
3. **Worktrees + dispatch concurrent worker subagents** (Agent tool, **model: sonnet**) — one per slice, scoped to its
   worktree + owned files, TDD (red→green), code-bearing tasks run `mutation_run.prove_non_vacuous`, commit in-worktree,
   self-stamp `CLAIM`/`DONE` to the shared `.kata/board.md`.
4. **Integrate** (octopus merge; disjoint = no conflict) → `cd tools && uv sync`.
5. **Integration gate:** `validate_skills.py --write` (run BEFORE pytest when a skill/version changed — README-sync;
   README is conductor-owned, F2) → `uv run pytest -q` (expect 1314) → `mcp__Snyk__snyk_code_scan` on new Python →
   emit `.kata/RESULT.json` via `gate_emit` (+ `mutation.json` for code-bearing).
6. **Fresh-context `kata-evaluate` (PART A)** — SEPARATE no-write Agent subagent, 9-rubric, default-FAIL, no self-cert.
7. **Standing `kata-review` (PART B, D98)** — SEPARATE fresh-context no-write subagent (opus) that tries to BREAK it
   (fail-opens, doc-only seams, overclaim) — not re-grade conformance. HOLD → targeted fixes (via SendMessage to a
   worker, then re-confirm via SendMessage to the same evaluator). **Never skip D98.**
8. **Operator merge gate** (present options; wait) → `git commit -F <file>` + push + checkpoint STATE/DECISIONS (new
   D-number) + push.
Model routing: judgment/eval/plan/grill = **Opus** (inherit; omit model on Agent calls); workers = **Sonnet**.
Supersede-never-rewrite.

## 5. Open decisions / queue *(orientation: human-required + deferred)*
- **OPEN QUEUE (operator picks after ad-val + benchmark):** (a) Debug Mode end-to-end live run on a fixture repo
  (n=0→1) — may be the repo the operator provides; (e) step 2 = the `kata-loop-benchmark` keystone (grill + build) —
  the immediate post-ad-val item; IaC Tier-2 LIVE-APPLY execution (future-gated on operator CLOUD creds);
  recurrence-hardening T3 (auto-author guards, C-arc-gated); the `kata-reason` decider + second-brain write/distill
  half (own grills).
- **Deferred MINORs:** `kata_install.py` 6 LOW CWE-23 (separate hardening pass); D119 nice-to-haves (`approval_verdict`
  PENDING_PLAN-vs-BLOCKED; redundant CFN argv flag; N1 stateful-set completeness in `iac_detect`); D120 nice-to-haves
  (recall.md min-token-length doc note; `query.kind` schema `open:True` comment).
- **Standing platform facts:** Codex LIVE (ChatGPT-authed, not on PATH); Kiro/Quick still stubs/seams; cloud creds for
  IaC Tier-2 are a SEPARATE gate from the now-installed Codex.

## 6. Redaction
No secrets / keys / PII in any artifact this session. Repo is PRIVATE. Nothing to redact.
