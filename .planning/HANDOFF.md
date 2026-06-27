---
date: 2026-06-26 (MULTI-MODAL LAYER BUILT — full routing wiring over the proof-slice, D108; next = kata-preflight→Debug Mode OR capability-aware-assignment OR install+confirm a 2nd platform → benchmark)
branch: master — private remote github.com/taurran/kataharness, tip 1f58415 (PUSHED, in sync as of 2026-06-26 — `git log --oneline origin/master..HEAD` to verify)
green: validator 36 skills / 0 errors · pytest 552 passed · Snyk medium+ 0 (residual Low CWE-23 = documented FPs)
tags: pre-multimodel-layer · pre-install-portability · pre-multimodel-slice · pre-phantom-hardening · pre-ws3 · v0.1.0-alpha.3 · loop-hardening-complete
authored-for: kata-orient (sections map to the three orientation tiers)
---

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
> (§2). **UPDATE (2026-06-25, D102): the phantom-machinery FIRST HARDENING is DONE + MERGED (`47648bf`)** — the
> verify-before-reuse guard shipped through the full recipe (freeze-gate→build→evaluate PASS 9/9→T-fire PASS(n=1)→
> D98 red-team SHIP). **UPDATE (2026-06-26): Debug Mode fully GRILLED + DESIGN FROZEN + PARKED (`d010434`)** — a
> self-contained run-shape `debug` (peer of version-up, debug-in-confidence, the onboarding killer-app); 7 grill
> rounds + a 4-thread research pass + 3 repo assessments; two convergence-gate HOLDs → SHIP + freeze-gate SHIP. NEW
> `kata-comprehend` function-model oracle + 7-step corroboration-gated deviation pipeline + behavioral drift gate
> (surface/AST + calibration = honest fast-follows). **Build PARKED behind `install-portability` (built first) +
> `kata-preflight`** → **install-portability is now critical-path.** Also captured: `capability-aware-assignment`
> BRIEF (the "multi-modal assignment" item). **NEXT = grill/freeze/build `install-portability` (unblocks Debug Mode +
> Phase 5), then multi-model + the strategy BRIEFs + capability-aware-assignment + v0.1 release-checklist — see §4.**
> Durable + committed + **pushed** (tip `e630d27`). Live picture: `.planning/STATE.md` (top box) +
> `.planning/DECISIONS.md` **D87–D102**.

## 1. Read-in order  *(orientation: CONTEXT)*
1. `AGENTS.md` (spine + conventions; the **"The Kata Loop"** entry) · 2. `docs/STANDARDS.md` §1 (frontmatter —
   `allowed-tools` REQUIRED) · 3. `CONTEXT.md` (glossary — **Kata Loop / the Harness / loop-back** are defined here) ·
4. `.planning/STATE.md` (top CURRENT box — live picture) · 5. **`.planning/DECISIONS.md` D87–D95**
   (Kata Loop build · D92 rename/seam-fixes · D93 loop-hardening · D94 WS-2 · **D95 WS-3 user-friendliness**) ·
6. `.planning/LESSONS-LEARNED.md` (esp. **L12** — wire lessons into skills) · 7. **`.planning/DECISIONS.md`
   D96–D102** (WS-3R · WS-2-polish · D98 standing red-team · D99 second-brain · D100 fix-loop · D101 recurrence-
   hardening · **D102 phantom-hardening BUILT**) · 8. **NEXT-WORK specs (for the resume):**
   `.planning/specs/install-portability/BRIEF.md` (**the critical-path predecessor — grill this next**) +
   `.planning/specs/debug-mode/{DESIGN,GRILL-LEDGER,RESEARCH}.md` (frozen + parked behind install-portability) +
   `.planning/specs/{capability-aware-assignment,second-brain-learning,recurrence-hardening,multi-model-orchestration,testing-model}/BRIEF.md`
   (Phase-5 / strategy BRIEFs) · 9. **`protocol/reuse-claims.md`** (the D102 verify-before-reuse guard — now a standing
   pre-flight in design/plan/tdd). *(Older deep context — the built loop — if needed: `specs/ws3-user-friendliness/`,
   `specs/loop-hardening/`, `greater-loop/`; "Greater Loop" = provenance, live name "the Kata Loop".)*
⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated, harness-injected).

## 2. State *(orientation: VOLATILE)*
- Branch `master`, tip `1f58415` (**D108 multi-modal layer BUILT** · D104 install-portability · D105 multi-model frozen +
  proof-slice · D106 red-team hardened · D107 banner — run `git log --oneline -14` for the arc; check `origin/master..HEAD`
  for unpushed). **36 skills / 0 errors · pytest 552 · Snyk med+ 0.** **D108 = the full multi-model routing layer over the
  proof-slice** (freeze-gate SHIP → orchestrated 4-slice build → kata-evaluate PASS 9/9 → D98 SHIP): `kata-orchestrate` roles
  load-guard + cross-model dispatch wiring; `kata-initiate` Phase 2e multi-modal preflight + `kata-bootstrap` roles write;
  `kata_dispatch` kiro adapter (capture-model branch); `kata_install` `.agents/skills` + kiro probe + probe⊆dispatch invariant.
  **New tools (D104-D107):** `tools/{project_find,kata_settings,kata_install,kata_roles,kata_dispatch,kata_banner}.py` (+ tests).
  Specs: `specs/{install-portability,multi-model-orchestration}/{RESEARCH,GRILL-LEDGER,DESIGN}.md` + `multi-model-orchestration/PLAN.md`.
  Confirm: `cd tools && uv run pytest -q && uv run python validate_skills.py`. **Windows gotcha:** git-bash mangles
  `/tmp/...` args to native python — use `C:/...` paths, a `.kata`-relative path, or `MSYS_NO_PATHCONV=1`. Also: a
  `..` segment in any operator-supplied path is rejected by the `_safe_path` guards by design (CWE-23) — use
  absolute paths without `..` when driving tools by hand.
- **✅ THE KATA LOOP fully built + proven (Phases 0–3 + Phase-4 self-dogfood):** P0 `tools/gate_emit.py` +
  `graph_gen.py` · P1 `modules/initiation/` + `kata-initiate` + `protocol/intent.md` (D91 self-contained modules) ·
  P2 `modules/closeout/` + `kata-closeout` (never gates) + `kata-understand` (writes `.kata/understand.md`) ·
  P3 `skills/coordinate/kata-loop/` conductor (initiation→Harness→closeout + context-carrying loop-back).
  Adversarial-fixed (`2d71f2e`); Phase-4 dogfood shipped `v0.1.0-alpha.2` (the subagent-dashboard).
- **✅ loop-hardening S1–S3a DONE** (each a real orchestrated run → fresh-context `kata-evaluate` PASS → pushed):
  - **S1** (`fedbb87`) live telemetry — `tools/kata_board.py` + dashboard heartbeats (G1+G2). Title `KATAHARNESS 改善型`.
  - **S1.5** (`e753504`) status-surface adapters (G7) — seeded `adapters/claude/` (statusline + `refreshInterval:1`) +
    `tools/kata_statusline.py` + `tools/kata_web.py` (localhost web viewer, 127.0.0.1). Per-platform: Claude=in-window
    now · Codex=no surface→viewer fallback · Kiro=`.vsix` deferred (`RESEARCH-s1.5.md`). pytest →334.
  - **S2** (`cddf9ff`) mutation proof (G3) + interactive initiate (G4) — `tools/mutation_run.py` (restoring
    mutate→run→restore loop); `kata-evaluate` item 1 **requires** `.kata/mutation.json` `allNonVacuous:true` for
    code-bearing work; `tools/intent_scaffold.py`; `kata-initiate` hard interview STOP. pytest →367.
  - **S3a** (`4391deb`) grounding + research (G5) — `tools/escalation.py` + `tools/grounding_gate.py`
    (GROUND/REJECT/ESCALATE → `.kata/grounding.json`), wired into `kata-research` + `kata-evaluate`. pytest →420.
- **✅ Red-team of S2+S3a + Kata Loop rename (`94539dd`, D92):** an adversarial review found two **documentation-only
  seams** — fixed inline: (MAJOR-1) `kata-orchestrate` now explicitly persists the grounding verdict via
  `tools/grounding_gate.py` → `.kata/grounding.json` (it was named only in the no-write `kata-evaluate`, so a real
  cycle would have silently skipped it); (MAJOR-2) the orchestrator now collects per-task `prove_non_vacuous` records
  into the integration `gate_emit` mutation set. **These two fixes are orchestrator *prose* — they get live-proven by
  S3b** (the first real cycle to route through them). "Greater Loop" → **"the Kata Loop"** across active surfaces
  (inner one-shot stays **"the Harness"**; **loop-back** unchanged); frozen specs keep the old term as provenance.
- **✅ ALL 7 GAPS CLOSED — loop-hardening DONE (S3b/G6 proven, `222cc7e`; tag `v0.1.0-alpha.3` + `loop-hardening-complete`).**
  S3b ran the live Kata Loop on KataHarness twice (Cycle 1 NIT-2 `f72a3bb` → loop-back → Cycle 2 MAJOR-3 `222cc7e`);
  fresh-context re-entry grade = **G6 PROVEN 7/7**. MAJOR-2 live-proven; MAJOR-1 correctly did not fire. Record:
  `specs/loop-hardening/{PLAN-s3b,REPORT-s3b}.md`. Adversarial review of the S3b code = **KEEP, not slop, no drift**.
- **✅ WS-1 separation done (`42e884b`):** the work-internal project's proper name is **scrubbed from every surface**
  (active + frozen specs); replaced with indirect terms. **`Quick` is KEPT** as the named **ACP-host target / plumbing
  seam** (+ pointers, so the future plumb-in is low-friction); **Codex added** to the platform enum (`claude | codex |
  kiro | quick | other`). Kiro kept (public Amazon product). Policy A (skills @ 0.1.0).
- **✅ WS-2 done (`d01cc11`, D94) — `kata-slop-check` shipped + parallelism/in-loop-RS exercised end-to-end.** A real
  version-up dogfood built **`kata-slop-check`** (optional EVALUATE module `kata/module/slop`: fresh-context no-write,
  default-FAIL slop verdict, in-context heuristics — general G1–G6 + 3 MIT-attributed checks from `ai-slop-detector`)
  AND served as the WS-2 validation: a fresh-context auditor graded it **7/7** (genuine wave-1 concurrency · a live
  `research-needed` escalation → park-sub-tree → `kata-research` grounded it → grounding gate → superseding re-plan →
  frontier recompute · mutation-proven code slice). The feature **caught a defect in its own build** (→ NEEDS_WORK →
  fixed → CLEAN). An **adversarial pass** confirmed SHIP (no errors) but flagged the writeup overclaimed — **de-inflated**
  "proven/genuine" → "exercised end-to-end (n=1)". Honest gap: board timestamps are orchestrator-written (live-vs-replay
  not artifact-distinguishable) → follow-up = **worker self-timestamping**. Record: `specs/kata-slop-check/PLAN.md` +
  `specs/ws2-loop-autonomy/AUDIT.md`. Backout tag `pre-ws2-slopcheck`.
- **✅ WS-3 user-friendliness done (`d08908d`, D95) — the last pre-public workstream.** persona (`protocol/persona.md`)
  + narration map (`protocol/narration.md`) + reflective **goal-mirror** intake (`kata-initiate`) + one **"how careful"**
  dial (`kata-bootstrap`) + milestone narration (`kata-orchestrate`) + **goal-anchored by-aspect closeout** with offered
  backout (`kata-closeout`+`kata-report`); **WS-4 + WS-5 folded in.** Freeze-gate `kata-review` HOLD→SHIP; orchestrated
  dogfood (2 waves, concurrent Sonnet workers, self-stamped); fresh-context Opus `kata-evaluate` **PASS 10/10**.
  **Built; now field-exercised (n=1) via WS-3R below.** Backout tag `pre-ws3`.
- **✅ WS-3R two-tier closeout done (`c265c42`, D96) — this WAS the WS-3 field-exercise (n=0→1).** The closeout is
  now two-tier: a concise CLI/GUI summary + a **self-contained, on-brand HTML report** (`.kata/closeout.html`) +
  Markdown source (`.kata/CLOSEOUT.md`), rendered by filling a committed template **in-context** (no new Python;
  `.html`/`.css` not code-bearing). 3-slice non-code-bearing dogfood; fresh-context `kata-evaluate` caught + fixed
  a cross-slice defect → PASS. Operator refined the brand live at the gate: the first **KataHarness logo** (kaizen
  ascending-bars + rising ochre arrow) · Hokusai palette · readable serif headings · error/warning tiles. Files:
  `modules/closeout/resources/{closeout-report.template.html,BRAND.md}` + `kata-report`/`kata-closeout`. Backout
  `pre-ws3-report`. **Follow-up (M8, BACKLOG):** native in-tool rendering (Claude `Stop`/`SessionEnd` hook +
  statusline; other tools per adapter).
- **⏸ Remaining (`.planning/BACKLOG.md` top):** WS-1/2/3 ✅ + WS-3 field-exercised. **OPEN, in order:** (a)
  **field-exercise WS-3 ✅ DONE** (D96 — two-tier closeout, n=0→1) · (b) **WS-1 pre-launch re-grep** · (c) **WS-2 polish** —
  wire worker self-timestamping into the board. Then **Phase 5 EXTERNAL** (install-portability · multi-model) +
  **v0.1 release-checklist**. **Far-future:** loop-tuning + an **agentic-loop benchmark** → **recursive parallelism
  (DAG-within-DAG)** gated on a hardened separability test (benchmark first). See §4.

## 3. The verified gaps loop-hardening closes *(orientation: CONTEXT — grounded in the Phase-4 dogfood accounting)*
| Gap | Verified-broken evidence | Closed by |
|---|---|---|
| G1 no live board/state · G2 dashboard never tailed reality | `.kata/board.md`/`state.json` absent after the run | **S1 ✅** |
| G7 viewer not seamless per-platform | only a separate-window TUI existed | **S1.5 ✅** |
| G3 mutation/non-vacuity proof never ran | `mutation.json` absent; no runner | **S2 ✅** |
| G4 interactive initiation never prompted | run decided inline; human got one prompt | **S2 ✅** |
| G5 grounding gate / `kata-research` never fired | no machine artifact/emitter; chain never invoked | **S3a ✅** |
| **G6 loop-back never exercised** | version-select chose "ship"; re-entry/handoff unproven | **S3b ✅ (G6 PROVEN, `222cc7e`)** |

## 4. NEXT ACTION — resume here *(VOLATILE — the immediate work)*
Pre-public WS-1/2/3 + loop-hardening + the Kata Loop are all DONE. This session added D98–D101 (see the banner).
The immediate agenda, in order:

1. **✅ THE PHANTOM-MACHINERY FIRST HARDENING — DONE + MERGED (2026-06-25, D102, `47648bf`).** The verify-before-reuse
   guard shipped through the full recipe: `protocol/reuse-claims.md` (the guard contract) + by-path pointers in
   `kata-design-doc` / `kata-plan` RUBRIC / `kata-tdd` + a `validate_skills.py` regression rule (dual mechanism +
   body-integrity full-phrase guard + producer-existence FAIL-loud check) + a non-vacuous test. Freeze-gate
   **HOLD→SHIP** · `kata-evaluate` **PASS 9/9** · **T-fire proof-of-fire** fired (a fresh `kata-design-doc` agent
   refused to freeze a phantom `orient.emit_pointers()` claim → labeled NEW) · standing D98 `kata-review`
   **SHIP-WITH-FIXES→SHIP** (it caught a default-FAIL gap: a renamed producer would have silently disabled the
   guard — fixed via the producer-existence check). pytest **456**, validator **36/0**, Snyk **0**. **Honest:** the
   rule enforces **presence, not behavior**; the T-fire is **n=1, contaminated, no guard-off control** (corroborating,
   not causal — the mutation-bitten regression rule is the durable proof). Backout `pre-phantom-hardening`. Record:
   `specs/recurrence-hardening/{PLAN-phantom,REPORT-phantom}.md`. **This makes the general `recurrence-hardening`
   spec (D101) concrete** — the detector + `kata-improve` proposal loop + `kata-promote` gate remain to grill→build.
1a. **✅ Debug Mode GRILLED + DESIGN FROZEN + PARKED (2026-06-25, `d010434`).** A self-contained run-shape `debug`
   (peer of version-up, debug-in-confidence, the onboarding killer-app). 7 grill rounds + a 4-thread research pass +
   3 repo assessments; two convergence-gate HOLDs → SHIP; freeze-gate `kata-review` SHIP. NEW `kata-comprehend`
   function-model oracle + 7-step corroboration-gated deviation pipeline + behavioral drift gate (surface/AST +
   calibration = fast-follows). LD1–LD13. **Build PARKED behind `install-portability` (built first) + `kata-preflight`**
   → **install-portability is now the critical-path predecessor.** Also captured: `capability-aware-assignment` BRIEF
   (the "multi-modal assignment" item). Artifacts: `specs/debug-mode/{BRIEF,GRILL-LEDGER,RESEARCH,DESIGN}.md`.
2. **★ NEXT (D103, 2026-06-26 — re-sequenced Track-A-first; IN PROGRESS):** the critical path to the Debug Mode
   killer-app has **TWO** locks, not one — **install-portability AND `kata-preflight`** (`debug-mode/DESIGN.md:137`);
   install-portability alone does **not** unblock Debug Mode. A grounded scoping pass corrected the old "THE unblock"
   claim: install-portability's **selection UX already landed** in `kata-initiate` Phase 2 (the GL-R3c fold,
   `modules/initiation/kata-initiate/SKILL.md:93–170`), so its v1 = the **full installer layer** (workspace-binding
   file + discovery + 3 user paths + install contract + per-platform dispatch + `docs/SETUP.md`), NOT the interview.
   **Order:** grill→freeze→build **install-portability** → **kata-preflight** (fold-vs-separate grill decided at
   install-portability's freeze; `preflight.*` seeds at `protocol/config.md:28–35` couple them) → **Debug Mode**
   build → THEN Phase-5 strategic: multi-model-orchestration · capability-aware-assignment · testing-model · the
   strategy BRIEFs (`specs/second-brain-learning/BRIEF.md` — the Recall *contract* is load-bearing — +
   `specs/recurrence-hardening/BRIEF.md`) · then the v0.1 release-checklist (flip **Policy A**, STANDARDS §3 / ROADMAP).
   **✅ install-portability BUILT (D104, the simple model — central install + 2-setting file + per-run project
   search + copy mode + per-platform install: Claude verified, Codex/Kiro best-effort, Quick own).** pytest 490,
   validate 36/0, Snyk 0 med+, D98 review SHIP-WITH-FIXES→fixed. Records: `specs/install-portability/{DESIGN,GRILL-LEDGER}.md`.
   **✅ multi-model-orchestration GRILLED + DESIGN FROZEN (D105)** — the operator's real "multi-modal" vision
   (route loop ROLES to platforms: Claude=coder, Codex=validator, Kiro=researcher). 5 cited research agents
   (`RESEARCH.md` — SKILL.md is a shared standard across all 5 tools; all headless-automatable), grill→DESIGN
   (5 role groups incl. a lightweight **evaluator** scorer; default all-on-host, multi-modal opt-in at preflight;
   files+CLI dispatch; NEW N1–N5 with schemas). **Convergence HOLD#1: the D102 guard caught over-claimed reuse →
   relabeled NEW → re-confirm SHIP.** Records: `specs/multi-model-orchestration/{RESEARCH,GRILL-LEDGER,DESIGN}.md`.
   **✅ Codex-validator PROOF-SLICE BUILT (`11bf609`+`2570cce`):** `tools/{kata_roles,kata_dispatch}.py` + confirm-probe
   + `roles` config; end-to-end proof (validator→codex→normalized verdict) against the stub-CLI seam; pytest 522,
   validate 36/0, Snyk 0 med+, D98 SHIP-WITH-FIXES→fixed. **Honest:** codex not installed → stub-proven, real run gated
   on install+confirm; only the codex adapter built (kiro/copilot/cursor = stubs).
   **✅ MULTI-MODAL LAYER BUILT (D108, `1f58415`)** — the full routing wiring over the proof-slice: `kata-orchestrate`
   `roles` load-guard + cross-model dispatch (LD6/LD7); `kata-initiate` Phase 2e preflight + `kata-bootstrap` roles write;
   `kata_dispatch` kiro adapter (capture-model branch); `kata_install` `.agents/skills` + kiro probe + probe⊆dispatch
   invariant. Recipe-built (freeze-gate SHIP → kata-evaluate PASS 9/9 → D98 SHIP). Read-only roles (validator→codex,
   researcher→kiro) wired + stub-test-proven; real run gated on install+confirm. PLAN: `specs/multi-model-orchestration/PLAN.md`.
   **★ NEXT (choose):** (a) **`kata-preflight`** (the other Debug Mode blocker, D29/D103) → **Debug Mode** build (the
   onboarding killer-app); OR (b) grill **capability-aware-assignment** (the specialist axis that multiplies with multi-model);
   OR (c) the strategy BRIEFs (`second-brain-learning` Recall contract is load-bearing; `recurrence-hardening` general build);
   OR (d) **install + confirm a 2nd platform live** (codex or kiro) and run the single-vs-multi-model `kata-loop-benchmark`
   (D108 makes this runnable). **DEFERRED in D108:** coder-routing (write sandbox), copilot/cursor adapters, the evaluator
   injection-points + score-threshold mechanism (MM-1). NOTE memory [[grill-in-plain-terms]] — keep design questions plain.
3. **Far-future.** `kata-loop-benchmark` (now the **keystone** that defines the C-arc unlock + measures whether
   learning/hardening pays off — D99) → recursive parallelism (DAG-within-DAG) gated on a hardened separability test.

> **Process reminder (the discipline that paid off ~6× this session):** every contract/code-bearing build is
> freeze → freeze-gate adversarial review (HOLD/SHIP) → build → `kata-evaluate` PASS → **standing D98 `kata-review`**
> → operator gate → merge. The red-team is NOT optional on contract-bearing work (D98). And **verify primitives
> before claiming reuse** (the memory) — that is the exact failure the next task hardens away.

**Small carry-alongs (fold into whatever touches the area):** `codeBearing` doc-fix (`footprint.py` note + a DECISIONS
line that `codeBearing:false` = "probably not, per the extension heuristic, not definitely"); `_safe_path`
SystemExit-vs-ValueError guard-consistency nit; the planning-approach↔delivery-mode alignment assessment.

**A carried lesson from the S3b live run (for whoever drives the next live loop):** `INTENT.md` + the `.kata/`
artifacts live at the **target repo root**, not in the per-task worktree — point a fresh-context evaluator at the
worktree for the *diff* but at the main root for `INTENT.md`/the understand-map. Emit gate artifacts to the
**worktree-root `.kata/`** (run `gate_emit` from `tools/` with an absolute `out_dir` so pytest still runs from
`tools/`). The loop-back payload (`RESULT.json` + `understand.md`) must sit at the main root for Phase 1b to find it.

## 5. The orchestration recipe (each cycle's *inner* build follows this — never inline) *(task-type hint)*
The **vetted, never-inline** loop (memory `exercise-harness-for-real`). S3b uses it **once per cycle** for the inner build:
1. **Freeze** the plan → `PLAN-s<n>.md` (LOCKED decisions + disjoint file-ownership slices + per-slice runnable
   `verify`). Commit. `git tag -f pre-s<n>`.
2. **Worktrees:** `git worktree add -b s<n>/<slice> C:/Dev/_kata_s<n>/<slice> master` per slice.
3. **Dispatch concurrent worker subagents** (Agent tool, **model: sonnet**) — one per slice, scoped to its worktree +
   owned files, TDD (red→green), **code-bearing tasks run `mutation_run.prove_non_vacuous`**, commit in-worktree. Workers
   self-stamp `CLAIM` (start) and `DONE` (end) to the shared `.kata/board.md` at the integration root via `kata_board.append_event` with their own clock.
4. **Integrate:** branch off master, `git merge --no-ff` the slices (octopus; disjoint = no conflict), `cd tools && uv sync`.
5. **Gate:** `uv run pytest -q` + `validate_skills.py` (36/0) + `mcp__Snyk__snyk_code_scan` on new Python (CWE-23
   CLI/stdin-path FPs are documented). **Emit `.kata/RESULT.json` via `gate_emit`** — and for a code-bearing run pass
   `mutation_records` so `.kata/mutation.json` exists with `allNonVacuous:true` (rubric item 1 requires it). If a
   `research-needed` escalation arises, persist the grounding verdict via `grounding_gate.write_grounding` — and emit
   `.kata/concurrency.json` via the `protocol/board.md` snippet (Concurrency evidence).
6. **Fresh-context `kata-evaluate`** — SEPARATE no-write Agent subagent, 9-rubric, default-FAIL. **No self-cert
   (L8).** Must PASS. (It pre-emptively regenerates RESULT.json for the integration if needed — S2 lesson; rubric
   item 9 = *reproduce derived artifacts, don't trust them* — L12.)
7. **Adversarial `kata-review` before merge — on a code/contract-bearing build (L12).** SEPARATE fresh-context
   no-write subagent (opus, **≥ standard tier**) that tries to **break** it — documentation-only seams, derived
   artifacts that don't reproduce from source, overclaim/slop (RUBRIC surface 6) — not re-grade conformance.
   SHIP-WITH-FIXES/HOLD → targeted fixes → re-confirm. The second lens the project kept re-learning it needs
   (L10c → L12). **"Contract-bearing" is judged, not the `codeBearing` flag** (a protocol/skill `.md` edit is
   `codeBearing:false` yet contract-bearing); only a trivially-prose docs run may skip.
8. **Merge to master**, push, `git worktree remove` + `git branch -D` the slices, checkpoint STATE/HANDOFF, push.
9. **At an operator-decision boundary** (S3b's version-select; any demo): STOP and ask via `AskUserQuestion`.
Model routing: **judgment/eval = Opus** (Fable 5 has been unavailable), **workers = Sonnet**. Supersede-never-rewrite.

## 6. Open decisions for the human *(orientation: human-required)*
- **WS-3 UX taste — DECIDED + BUILT (D95).** persona = nameless calm kata-craftsperson-who-translates; moderate-
  non-expert default register; reflective goal-mirror intake; one "how careful" dial; milestone narration;
  goal-anchored closeout. **Open:** judge the friendliness on the first **field-exercise** run (n=0→1) and fold back
  any persona/narration tone refinements — the voice remains the operator's call.
- **Platform targets are settled (user 2026-06-22):** **Kiro AND Quick both stay compatible — do NOT gate either**;
  the work-internal project's proper name must **never** appear on any surface. For Quick, the orchestrator lives inside
  Quick and ACP drives the per-task coding with file handoff (capture in `multi-model-orchestration` when built).
- **Pre-launch:** the public-sanitization re-grep (WS-1 tail) is still owed before going public.
- Future: v0.1 release-checklist (flip Policy A → bump-on-modify) after WS-3/4/5 + Phase 5 prove out.

## 7. Redaction
No secrets / keys / PII in any artifact this session. Repo is PRIVATE. Nothing to redact.
