# EXECUTION-WINDOW ORIENTATION #2 — written 2026-08-17 (waves 1–3 CLOSED gate-PASS; wave 4 is YOUR step 0; dogfood rule now BINDS)

> **Locked agent-orientation format (UX-15).** Successor to `ORIENTATION-EXECUTION.md` (superseded —
> its step 0 is done). This is the EXECUTION window of the TWO-WINDOW split; a planning window may
> still be live CONCURRENTLY in the main checkout. Honor the ownership fence.

━━ KATAHARNESS · AGENT ORIENTATION · EXECUTION WINDOW #2 ━━━━━━━
run: the Trust Model burn, waves 4–9 · full loop under BBM-12 · Fable anchor · MAX PARALLEL FAN-OUT (operator-directed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## GROUND TRUTH (verify before anything)

- Branch `burn/trust-model-01` @ `6a06b4b` (PUSHED). CI GREEN both platforms at `6bd7e7d`
  (run 31990449823; `6a06b4b` is one docs-only commit later). Local gauntlet 4/4.
- **Waves 1–3 CLOSED, each with a fresh-context default-FAIL FINAL EVAL PASS** — records in
  `.planning/specs/trust-model/OBSERVATIONS.md` (the wave integration records + D-1..D-27).
- Built so far: BL-X14/X15/X12 fixes (CI's 12-day red ENDED) · protocol/deferral.md ·
  exec-safety `evidence:` registration · hook-probe evidence · the CURSOR (grammar §2.2,
  durability, consumers migrated) · the closed `evidence:` grammar + reflexive PLAN check ·
  INTENT freeze field · **the SEAM ENGINE** (`kata_dispatch.mint/run_start/capture/phase/deny`,
  governor ladder, atomic-claim records, honest Guardian declaration) · evidence identity
  (runId-exact crediting, BL-X11 code side + BL-X13). Conductor live spot-audit of the seam:
  mint→SPAWN→claim→replay-refused→bad-mint-parks-with-DENY, all live.
- **NOTHING calls the seam or the identity gate in production yet** — W4 wires the ~52 launch
  sites; W5/W7 wire the identity consumers. Honest label, recorded (N1, wave-3 record).
- The main checkout (`C:\dev\projects\KataHarness`) may be the LIVE planning window — NEVER
  switch its branch or edit tracked files there. Conduct from
  `C:\dev\projects\_kata_wt\trust-model\conductor` (this worktree). Task worktrees live under
  `C:\dev\projects\_kata_wt\trust-model\<task>` — create per task, pinned:
  `git worktree add -b task/tm-w<N>-<task> <path> <baseSHA>` (run from the MAIN repo dir;
  wrap in `cmd /c "... 2>&1"` to avoid PS stderr-wrapping).

## MISSION — waves 4–9, wave-per-loop (BBM-12), max fan-out WITHIN each wave

**STEP 0 = WAVE 4 dispatch (3 concurrent Opus builders), each dispatch MINTED through the live
seam first** (Execution rule 4's dogfood rule now binds: in the conductor worktree, call
`kata_dispatch.run_start` once (kata dir `.kata/`), then `mint(governs="plan", role=..., task_id=...,
plan_path=<the frozen PLAN>, kata_dir=...)` per dispatch, `claim_record` at launch — Honor-system
declared, nothing denies a bypass yet). The three tasks (frozen PLAN Wave 4 blocks + amendments):
1. `orchestrate-seam-migration` — the ~52 kata-orchestrate launch sites → mint→launch→capture;
   park semantics; mutation re-run trigger contract (N=5 cap, deterministic sample key); arm
   registry; fold reducers; board→cursor prose; its own stale anchors.
2. `coordinate-skills-migration` — conductor spine phase-aware; sprint stop-gate consumes the
   PERSISTED verdict; **the board→cursor heritage RENAME** (files, skill, `REQUIRED_PROTOCOL`
   key in validate_skills.py — granted); **+ G7: `modules/initiation/kata-initiate/SKILL.md`
   Phase-6 `freeze=True` call site** (one line; makes `intent: frozen` reachable).
3. `authoring-skills-migration` — evidence-field method in RUBRIC + tiers; convergence-pass
   record duty; grill-close status write; kata-defer → deferral.md grammar; **+ G5:
   `skills/plan/kata-grill/resources/DECISION-LEDGER.md` gains the frontmatter block**
   (`spec:`/`status:` enum/`opened:` — kills the 15-key-absent-ledgers drift class at the source).

Then per wave: builder self-gates → conductor RE-RUNS (incl. ≥10× loops on concurrency tests,
G11) → fresh-context judge per item (Explore agent, anchor model, default-FAIL) → cures → ONE
spot-audit → integration (no-ff merges via HERE-STRINGS with `Kata-Task:` trailer, VERIFY the
trailer post-merge — G10) → gauntlet → push + `gh workflow run gauntlet --ref burn/trust-model-01`
+ watch → wave FINAL EVAL (fresh-context, default-FAIL; a fail re-loops). **Wave N+1 never
dispatches before wave N's gate passes.**

**WAVES 5–9 (key inputs each, from the records):**
- **W5** `judge-contract-rewrites` (1 task, `dispatch_class: critical` — ANCHOR model builder):
  VERDICT first-line enums enumerated; fact-table inputs; kata-evaluate names
  `run_result.gate_evidence_is_creditable`; **assign the convergence-reviewer role token its
  ladder row** (named seam comment in kata_dispatch); kata-validate alignment (cross-wave file).
- **W6** detectors (3 tasks): truth_serum B1/B3/B5 + anti-vacuity companions; truth_signals
  S1/S2/S3 (T6–T11 corpus); tripwire corpora + tools/tripwire_check.py; DEF-3 (shell-true
  allowlist line) may ride here.
- **W7** (4 tasks): gate_preconditions (activation tables read RECORDED closure — X14 is closed,
  cite run 31979757460; per-judge per R-M6) · grounding agent (NEW skill + fact table) ·
  close-machinery (three-way join; D134; provenance drift; redaction ONE-scrub extending
  learn_feed.redact; consent; `run-closed`; **+ G6: protocol/config.md `cursor.pushTrail` row**)
  · **doctrine-amendment (D173): D2-16 probe FIRST (hard prerequisite,
  INGEST-EXECUTION-ORDER.md:108), laws 13+15 + D172 language ONLY (11/12/14/16 + two clauses
  DECLINED — E5), one advanced grill, fingerprint two-step at integration (G3), + fold the
  stale law-8 mutation_run example (D-20 note)**.
- **W8** (2 tasks): the HOOK — build to `evidence/hook-probe.md` OBSERVED facts (fail-open is
  the limit ⇒ deny-on-internal-error + post-hoc verification MANDATORY; matcher payload says
  "Agent" never "Task"; capture needs PostToolUse+SubagentStop BOTH; scope via run marker) ·
  EV-1 badge registry + validator check + exec-safety scan extension. Hook activates LAST.
- **W9** relabel: promise-audit rows with citations; §6.6 truth-status marks — **BACKLOG.md leg
  ONLY if the planning-window fence has lifted, else file via OBSERVATIONS + park (GATE-PLAN
  ruling 2)**; then the program close: `close_run` over the burn's own cursor.

## GUARDRAILS (all standing, none new)

- BBM-12 entire-loop wave-per-loop · PD-1/PD-2 · D169 · D172 · hybrid gating BBM-1 · pinned
  worktrees BBM-9 · builders push back H7 · Fable anchor, builders Opus (W5 anchor) ·
  Honor-system declared until W8 activates the hook (then Guardian per probe results ONLY).
- **Rulings G1–G11 (all in OBSERVATIONS/GATE-PLAN, binding):** G1 X12 closure boundary · G2
  README regen = per-wave conductor act (`validate_skills.py --write` once at integration) ·
  G3 fingerprint re-approvals = conductor integration acts, distinct vetoable commits,
  re-derive-diff-review-paste · G4 fence-constrained ledger scope · G5/G6/G7 ownership
  amendments (folded into W4/W7 briefs above) · G8 (done) · G9 first-use registry
  acknowledgments = conductor acts (fingerprints, path-guard family — verify invariants
  before pasting) · **G10: here-strings ONLY for commit messages; verify trailers post-merge;
  workers NEVER write `Kata-Task:` (integration-only); file appends via Python UTF-8, never
  Get-Content|Add-Content** · **G11: concurrency tests race N× in-process + forced
  interleaving; conductor loops them ≥10×**.
- **Advisor channel (operator-directed):** every builder brief states — on a hard technical
  blocker, return a narrowly-scoped ADVICE-REQUEST (one question + scoped context); the
  conductor dispatches a fresh-context Fable-tier no-write advisor (kata-advise pattern) and
  relays the response; advisory never authoritative.
- **Declared-evidence-node rule:** every brief quotes the task's `evidence:` node names
  VERBATIM from the PLAN frontmatter; conductor re-runs them standalone at the task gate.
- **The fence:** THIS window owns tools/** · skills/** · protocol/** · modules/** ·
  adapters/** · specs/trust-model/** · .kata/** · burn branches. NEVER touches BACKLOG.md ·
  DECISIONS.md · other spec dirs. Discoveries → OBSERVATIONS (single-writer: conductor) ·
  DEFERRED.md per protocol/deferral.md.
- Conductor context discipline (operator-directed): stay LIGHT — briefs point at PLAN/DESIGN/
  OBSERVATIONS sections, builders read in-worktree; summaries terse; fan-out does the work.

## CONTEXT — read in this order
`protocol/prime-directives.md` → this file → frozen `specs/trust-model/PLAN.md` (waves 4–9
blocks + Execution rules + `evidence:` map) → `specs/trust-model/OBSERVATIONS.md` IN FULL
(rulings + D-1..D-27 + three wave records) → DESIGN sections per task (cited in PLAN) →
`evidence/hook-probe.md` before W8 · `evidence/ledger-status-table.md` for context.

## OPERATOR GATES (surface, never close)
Freeze veto (standing) · G3 re-approvals + D-25 §1.5 erratum + D-8 initial pin
(vetoable-by-objection, one revert each) · D-9 pin-count prose two-step (23/21→24/22) ·
UX round C1 (presentation wave stays OUT) · planning-window folds (D-1/D-13/D-15/D-16/D-23
writebacks) · PAT rotation (inherited, NOT dropped) · trail-push + provenance-commit consents
when W7 §2.5/§5.4 land.

## REPORT CONTRACT before THIS window closes
☐ every wave ran the FULL loop with durable gate evidence in OBSERVATIONS · ☐ hook activated
LAST with deny-tripwire-derived Guardian claims · ☐ EV-1 in the gauntlet · ☐ the burn's own
close via `close_run` (W9) · ☐ CI green at close · ☐ discoveries fence-filed · ☐ STATE/HANDOFF
+ orientation #3 (or the closeout) at close · ☐ the retroactive-emit + Kiban records intact.

━━━━━ end orientation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## YOUR BRIEF — ✂ copy below · paste into the NEW EXECUTION window ✂

Load KataHarness context per CLAUDE.md (prime directives first, then AGENTS.md).
Read .planning/ORIENTATION-EXECUTION-2.md on branch burn/trust-model-01 IN FULL
(check out nothing in the main repo — conduct from the existing worktree
C:\dev\projects\_kata_wt\trust-model\conductor, branch already checked out
there, tip 6a06b4b pushed). This session EXECUTES waves 4-9 of the Trust Model
burn as FULL loops under BBM-12, max parallel fan-out within each wave,
concurrent with a possibly-live planning window - honor the fence. STEP 0:
dispatch wave 4's three builders (worktrees pinned off the tip), each dispatch
MINTED through the live seam engine first (the dogfood rule), each brief
carrying the advisor channel and the verbatim evidence-node names. Then
wave-per-loop through W9: builders -> conductor re-runs (G11 loops) -> judges
-> cures -> spot-audit -> integration (G10 trailers verified; G2/G3/G9
conductor acts) -> gauntlet -> CI -> default-FAIL final eval. Hook LAST (W8,
build to hook-probe.md observed facts). Presentation wave OUT. Fable anchor;
builders Opus except W5 at anchor. The gated DESIGN rev 1 + frozen PLAN are
the contract; rulings G1-G11 bind. Wave, never sprint. The vault is Kiban.

✂ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ copy ends ━━━━━━━━━━━━━━━━━━━━━━
