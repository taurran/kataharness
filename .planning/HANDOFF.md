---
date: 2026-06-24 (WS-1 ✅ + WS-2 ✅ + WS-3 ✅ + WS-3 FIELD-EXERCISED; two-tier closeout shipped, D96; next = WS-1 re-grep + Phase 5)
branch: master — private remote github.com/taurran/kataharness, tip c265c42 (PUSHED, in sync — `git log --oneline -3` for latest)
green: validator 36 skills / 0 errors · pytest 447 passed · Snyk medium+ 0 (residual Low CWE-23 = documented FPs)
tags: pre-ws3 · pre-ws2-slopcheck · v0.1.0-alpha.3 · loop-hardening-complete (earlier: pre-s1/1.5/2/3a/3b · v0.1.0-alpha.1/.2/.3)
authored-for: kata-orient (sections map to the three orientation tiers)
---

# HANDOFF — KataHarness — 2026-06-24 (WS-1/2/3 DONE + WS-3 field-exercised · two-tier closeout shipped · next = WS-1 re-grep + Phase 5)

> **✅ loop-hardening · WS-1 · WS-2 · WS-3 ALL DONE; WS-3 now FIELD-EXERCISED (n=1).** WS-3 user-friendliness
> shipped (D95): persona + narration + reflective **goal-mirror** intake + one **"how careful"** dial + milestone
> narration + **goal-anchored closeout** with offered backout (WS-4/WS-5 folded in). Then **field-exercised
> (D96, merge `c265c42`)** by building a real feature through it: the closeout is now **two-tier** — a concise
> CLI/GUI summary linking to a durable, on-brand, self-contained **HTML report** (`.kata/closeout.html` +
> Markdown `.kata/CLOSEOUT.md`); the operator refined the brand live at the gate (the first **KataHarness logo**;
> Hokusai palette; readable serif headings; error/warning tiles). Fresh-context Opus `kata-evaluate` caught +
> fixed a cross-slice defect → PASS. Fresh/compacted session: read §1, confirm green (§2). **NEXT = (a) WS-1
> pre-launch re-grep · (b) WS-2 worker-self-timestamp polish · then Phase 5 EXTERNAL (install-portability ·
> multi-model) + v0.1 release-checklist; far-future = loop benchmark → DAG-in-DAG.** Durable + committed +
> **pushed** (tip `c265c42`, in sync). Live picture: `.planning/STATE.md` (top box) + `.planning/DECISIONS.md`
> **D95–D96**. (§4 below predates this — see the NEXT line here for the current agenda.)

## 1. Read-in order  *(orientation: CONTEXT)*
1. `AGENTS.md` (spine + conventions; the **"The Kata Loop"** entry) · 2. `docs/STANDARDS.md` §1 (frontmatter —
   `allowed-tools` REQUIRED) · 3. `CONTEXT.md` (glossary — **Kata Loop / the Harness / loop-back** are defined here) ·
4. `.planning/STATE.md` (top CURRENT box — live picture) · 5. **`.planning/DECISIONS.md` D87–D95**
   (Kata Loop build · D92 rename/seam-fixes · D93 loop-hardening · D94 WS-2 · **D95 WS-3 user-friendliness**) ·
6. `.planning/LESSONS-LEARNED.md` · 7. **`.planning/specs/ws3-user-friendliness/{DESIGN,PLAN}.md`** (WS-3 — built;
   LOCKED L1–L11) + **`protocol/persona.md`** (voice/SOUL) + **`protocol/narration.md`** (phase→plain map) — the
   live UX surfaces · 8. **`.planning/specs/loop-hardening/{ROADMAP,PLAN-s1..s3b}.md`** + `greater-loop/{DESIGN,PLAN-phase0..3}.md`
   (the built loop — frozen; keeps the old "Greater Loop" term as **provenance**, the live name is "the Kata Loop").
⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated, harness-injected).

## 2. State *(orientation: VOLATILE)*
- Branch `master`, tip `3ad3c73` (**pushed, in sync**; loop-hardening + WS-1 + WS-2 + WS-3 done — run `git log --oneline -3` for the exact latest). **36 skills / 0 errors · pytest 447 · Snyk med+ 0.**
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
**WS-1, WS-2, WS-3 are all DONE** (the pre-public workstreams; WS-4 offered-backout + WS-5 closeout-transparency
folded into WS-3). loop-hardening + the Kata Loop are complete. The immediate agenda, in order:

1. **Field-exercise WS-3 — ✅ DONE (n=0→1, D96).** Built a real feature (the **two-tier closeout**, merge `c265c42`)
   THROUGH the friendly loop — the first live use of the goal-mirror intake / milestone narration / goal-anchored
   closeout; the operator refined the brand live at the gate (first KataHarness logo · Hokusai palette · tiles).
   **Follow-up (M8, deferred adapter work) — recommended when adapters are touched:** native in-tool rendering of the
   closeout — a Claude `Stop`/`SessionEnd` hook that surfaces `.kata/closeout.html` + a statusline verdict line;
   other tools per their adapter. Spec: `specs/ws3-closeout-report/PLAN.md`.
2. **WS-1 pre-launch public-sanitization re-grep — ✅ DONE 2026-06-24.** Name + variants = **0 matches** across all
   tracked files, frozen specs, and the working tree; Quick/ACP seam intact; scrub is consistent indirection; secret
   sweep clean. Hardened `.gitignore` (`/INTENT.md` + `.claude/`). The last pre-public sanitization gate is closed.
3. **WS-2 polish — worker self-timestamping.** The WS-3 build had workers self-stamp start/end (proving concurrency) but
   ad-hoc in the dispatch; wire it into `tools/kata_board.py`/the board so concurrency is provable from artifacts on
   every run.
4. **Phase 5 EXTERNAL + v0.1 release-checklist.** install-portability + multi-model-orchestration (BRIEFs exist:
   `specs/{install-portability,multi-model-orchestration,testing-model}/`); then the v0.1 release-checklist — flip
   **Policy A** (hold-at-0.1.0 → bump-on-modify, STANDARDS §3 / ROADMAP).
5. **Far-future (after the above).** loop-tuning + an **agentic-loop benchmark** module (context economy + speed) →
   **recursive parallelism (DAG-within-DAG)** gated on a hardened **separability test** (default-flatten,
   checked-not-self-certified). Benchmark sequences first (it measures whether each recursive cut wins). BACKLOG end.

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
   owned files, TDD (red→green), **code-bearing tasks run `mutation_run.prove_non_vacuous`**, commit in-worktree.
4. **Integrate:** branch off master, `git merge --no-ff` the slices (octopus; disjoint = no conflict), `cd tools && uv sync`.
5. **Gate:** `uv run pytest -q` + `validate_skills.py` (36/0) + `mcp__Snyk__snyk_code_scan` on new Python (CWE-23
   CLI/stdin-path FPs are documented). **Emit `.kata/RESULT.json` via `gate_emit`** — and for a code-bearing run pass
   `mutation_records` so `.kata/mutation.json` exists with `allNonVacuous:true` (rubric item 1 requires it). If a
   `research-needed` escalation arises, persist the grounding verdict via `grounding_gate.write_grounding`.
6. **Fresh-context `kata-evaluate`** — SEPARATE no-write Agent subagent (sonnet), 8-rubric, default-FAIL. **No
   self-cert (L8).** Must PASS. (It pre-emptively regenerates RESULT.json for the integration if needed — S2 lesson.)
7. **Merge to master**, push, `git worktree remove` + `git branch -D` the slices, checkpoint STATE/HANDOFF, push.
8. **At an operator-decision boundary** (S3b's version-select; any demo): STOP and ask via `AskUserQuestion`.
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
