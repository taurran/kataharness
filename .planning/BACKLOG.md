# BACKLOG — KataHarness

Promote to ROADMAP milestones when ready.

## ⟳ 2026-06-24 strategy + hardening session (D98–D101) — pointers
- **D98** standing adversarial red-team wired + `kata-evaluate` item 9 (reproduce-don't-trust). **DONE.**
- **D99** loop-learning strategy: A-now / C-destination / B-trap; **Second brain + Recall + Reason** model
  ("engram" retired, rename pending); `kata-loop-benchmark` promoted to keystone. BRIEF:
  `specs/second-brain-learning/` — **grill → freeze → build (the Recall *contract* is the load-bearing design).**
- **D100** fix-loop hardening (thrash budget + material re-verification) — **BUILT through the main loop** (`fc7f4f7`).
  Honest: wired, exercised by **zero real thrash events**; N=2 + ceiling provisional pending dogfood calibration.
- **D101** recurrence hardening — when a failure-class recurs, harden the responsible agent (gated). BRIEF:
  `specs/recurrence-hardening/`. **★ FIRST INSTANCE ✅ DONE (2026-06-25, D102, `47648bf`):** the
  **phantom-machinery / over-claimed-reuse** guard shipped — `protocol/reuse-claims.md` + pointers in
  `kata-design-doc`/`kata-plan` RUBRIC/`kata-tdd` + validator regression rule + T-fire proof-of-fire (full recipe,
  D98 red-team SHIP). Record: `specs/recurrence-hardening/{PLAN-phantom,REPORT-phantom}.md`. **REMAINING (general
  build):** the detector + `kata-improve` proposal loop + `kata-promote` gate — **grill → freeze → build** the BRIEF.
- **★ wiring-completeness gate — full build (SCHEDULED, after v0.1 cluster).** A `tools/` produced-vs-consumed
  sweep helper + tests + mutation bite (mirror `test_exec_safety.py` registry-completeness check) + a
  realistic-fixture end-to-end trace — run as an **ORCHESTRATOR INTEGRATION-GATE step** (NOT a no-write
  `kata-evaluate` item, which collides with the no-write invariant). Supersedes the interim prose-pin
  (2026-06-30); `kata-evaluate` item 9 and `kata-review` 6(b) hold a POINTER to this gate. Refs:
  `.planning/PROPOSAL-phantom-reuse.md` + `specs/recurrence-hardening/`. **Size M, tier standard. Grill →
  freeze → build.**

## ★★ PRE-PUBLIC PRIORITIES (operator notes, 2026-06-21 — post-S3b review) ★★
These are the operator's own end-of-S3b notes; several gate going public. Captured verbatim-in-intent.

- **WS-1 — Separation / IP hygiene (✅ DONE 2026-06-24; pre-public re-grep CLEAN).** The work-internal sister project's
  **proper name must not appear on any surface** — scrub it everywhere, replacing with indirect terms ("the work
  host", "an external/work ACP host", "the work backend"). **Quick is deliberately KEPT** as the named **ACP-host
  target** — it is the **integration seam** for plumbing the work backend in later, and the docs/skills carry
  explicit **pointers** marking that seam (without naming the work project), so the future plumb-in is low-friction.
  Public FM targets to start: **Claude + Codex**; **Kiro** public (v0.3 adapter); **`quick`** = the ACP-host
  plumbing anchor; **`other`** = catch-all. The platform enum is now `claude | codex | kiro | quick | other`
  (Codex added; the work proper-noun removed). **Done so far:** `protocol/intent.md` enum, `kata-initiate`
  Phase 2c + STOP gate, `AGENTS.md`, `docs/DESIGN.md`, `README.md`, `.planning/PROJECT.md`, `protocol/engram.md`,
  the two module `AGENTS.md`, DECISIONS/STATE, and the frozen-spec proper-noun mentions. **✅ Final
  public-sanitization re-grep DONE 2026-06-24:** name + variants returned **0 matches** across all tracked files,
  frozen specs, and the working tree (incl. untracked artifacts); the Quick/ACP plumbing seam is intact (20 files);
  scrub is consistent indirection (not bare deletion); light secret/key sweep clean. Also hardened `.gitignore`
  (`/INTENT.md` root run-artifact + `.claude/`) so stray artifacts can't leak. *(Kiro kept — it is a public Amazon
  product, not the internal work host; flag if it should also be gated.)*

- **WS-2 — Validate the INNER (harness) loop's autonomy + parallelism (the operator's confidence gap).**
  **[STATUS 2026-06-22 (D94): rolling-frontier PARALLELISM + the in-loop RS RESEARCH PATH are now LIVE-PROVEN 7/7
  via the `kata-slop-check` version-up dogfood (`specs/kata-slop-check/PLAN.md` + `specs/ws2-loop-autonomy/AUDIT.md`).
  ✅ WS-2 polish DONE 2026-06-24 (D97, `4d8f01b`): worker self-timestamping wired — workers self-stamp `CLAIM`/`DONE`
  with their own clock to the shared board; the gate derives `.kata/concurrency.json` (maxInFlight · per-task
  wall-clock · overlap windows) via an in-context snippet in `protocol/board.md` (NO new Python). Concurrency is
  now provable from artifacts alone, closing the orchestrator-written-timestamp caveat. Record: `specs/ws2-polish/PLAN.md`.
  Still deferred BY DESIGN: in-loop LEARN-between-iterations (β emit-only, D74) + engram CONSULT (D9/D56).]**
  The operator is NOT confident the harness loop genuinely runs autonomously for long stretches. Validate, with
  evidence: **(a) parallelism** — are we using subagents properly? Is the orchestrator actually running concurrent
  workers that check/communicate laterally (board), per Anthropic's long-running-agent best practice — and is it
  *better than Hermes*? Build a way to **evaluate** that parallel processes are used properly (not just dispatched
  serially). **(b) in-loop autonomy** — the harness loop should run **internally for long periods with no human**:
  LEARN between internal iterations, run **research internally** (RS), and **self-grade/QC within the loop**. NOTE
  the real gap: the β LEARN feed is **emit-only, zero CONSULT** (D74) and engram CONSULT is gated off (D9/D56), so
  "learn between loops" is **not happening today by design** — decide whether to light a bounded in-loop learning
  path. The greater (kata) loop is fine requiring human interaction; the *harness* loop's autonomous endurance is
  what needs proving. **Deliverable:** an honest audit + a validation harness, not a claim.

- **WS-3 — User-friendliness, front-to-end (must precede public launch).**
  **[✅ BUILT 2026-06-24 (D95; merge `d08908d`; spec `specs/ws3-user-friendliness/{DESIGN,PLAN}.md`) — persona
  (`protocol/persona.md`) · narration map (`protocol/narration.md`) · reflective goal-mirror intake · one-dial
  mode surface · milestone narration · goal-anchored by-aspect closeout. Built + gate-PASS + fresh-eval PASS 10/10;
  **field-exercised (n=1) via the two-tier-closeout build (D96, `c265c42`)** — first live use of the friendly
  surfaces; operator refined the brand at the gate (first KataHarness logo · Hokusai palette · tiles). Adaptive
  register is a gated seam, not live.]** The whole system is technical, not
  intuitive. Likely a **combination** of a **persona/voice context file** AND **explicit voice in the skills**.
  Sub-items:
  - **Decision tree must be human-readable, not machine-oriented.** Speak in terms of the **modes** we set and
    *infer* behavior from mode selection, rather than exposing machinery.
  - **Goal-centric intake.** Be far more intuitive about understanding the **GOAL** — what is the user actually
    trying to achieve — and feed that to the loop true to the user's desired changes (the synthesis of the initial
    **system prompt + brainstorming + research + grill results**), not a mechanical form.
  - **In-loop narration.** While the loop runs, **don't call out stage names** (GRILL/FREEZE/…); **talk through
    what the agent is actually doing**, in human terms.
  - **Strategic progress display.** Show enough that the user trusts it's working and making progress, **without**
    spamming useless model internals or inviting them to butt in. Inspire confidence; surface **critical
    errors/alerts** prominently. Trust-building, not log-dumping.
  - **Verbose, goal-anchored closeout.** At the end: **restate/recall the goal**, focus on **what changes the loop
    made to achieve it**, **assess progress toward the goal**, and **call out uncertainties + risks** so the user
    can decide to iterate the kata loop again or go back and re-prompt/re-grill. **Link to the findings files** so
    the user can open and review them.
  - **Research Hermes's UX** (people are happy with how it guides users) for both the in-loop narration and the
    closeout — borrow the guidance pattern (keep our gates, D69).

- **WS-4 — Backout / rollback as a first-class option (safety).**
  **[✅ BUILT into WS-3 slice F (D95) — `kata-closeout` offers backout in plain language, anchored on the emitted
  `.kata/RESULT.json.baselineSha` (`git reset --hard`), human-gated & never autonomous, surfaced at the human
  gate. Field-exercised (n=1) via the two-tier closeout build, D96.]** There MUST be a surfaced way to **back out the
  loop's changes** if a run goes off the rails. We have `pre-s<n>` backout tags, but rollback must be an explicit,
  offered option at the human gate — not a buried git incantation.

- **WS-5 — Change transparency at closeout (the acute miss this session).**
  **[✅ BUILT into WS-3 slice F (D95) — `kata-closeout` + `kata-report` lead with plain-language what-changed-why,
  organized by goal-aspect, before any path or gate number. Field-exercised (n=1) via the two-tier closeout build, D96.]** The closeout must make **exactly what
  changed** legible to a non-expert owner ("I had no idea what changes were made"). Overlaps WS-3's closeout item;
  call it out as a hard requirement: every closeout leads with a plain-language "what changed and why it matters to
  you," with links, before any machine detail.

- **Two-tier closeout — native in-tool rendering (M8 follow-up, 2026-06-24; adapter work).** The two-tier closeout
  shipped (D96): a concise CLI/GUI summary + a self-contained branded HTML report (`.kata/closeout.html`) +
  Markdown source. **Open:** surface the report *natively per host* — a Claude **`Stop`/`SessionEnd` hook** that
  opens/links `.kata/closeout.html` + a **statusline** verdict line (`✅ goal hit · backout: …`); Codex/Kiro/Quick
  via their adapters. Today the link is a clickable file path in the summary. Folds into the v0.3 adapter layer.
  Spec: `specs/ws3-closeout-report/PLAN.md` (Carry-outs). Also reusable: the **first KataHarness logo** (inline SVG
  in the template / `BRAND.md`) for favicon / docs / statusline glyph.
- **Gate-enforcement hardening (loop-hardening red-team residue, 2026-06-21 — non-blocking).** The S2/S3a
  adversarial review left three deferrable items. **(a) MAJOR-3 — machine `codeBearing` flag: ✅ DONE (S3b Cycle 2,
  `222cc7e`)** — `footprint.py` `code_bearing()` derives the flag from changed-file globs → `footprint.json`
  `codeBearing`; `kata-evaluate` rubric item 1 keys off it (BC fallback). **(b) NIT-2 — validator no-write
  assertion: ✅ DONE (S3b Cycle 1, `f72a3bb`)** — `validate_skills.py` `check_evaluator_no_write` asserts
  `{kata-evaluate, kata-research}` omit `Write`/`Edit`. **(c) NIT — guard consistency (REMAINING):**
  `mutation_run`/`grounding_gate`/`escalation` raise `SystemExit` on `..` traversal while `intent_scaffold` raises
  `ValueError`; pick one (ValueError is the more catchable/consistent choice) across the `_safe_path` guards.
  *(MAJOR-1/MAJOR-2 were fixed inline — D92; MAJOR-2 live-proven in S3b. Only the guard-consistency nit remains.)*
- **★ Planning-approach ↔ delivery-mode alignment (FUTURE assessment, user 2026-06-21).** Assess the **planning
  approach** (`kata-plan` essential/standard/advanced tiers + the roadmap layer `kata-plan/ROADMAP.md`) and confirm
  it **aligns coherently with each delivery mode in place**: **one-shot**, **sprint (incremental)**, and
  **version-up**. For each: is the plan *shape* right? (one-shot = a single frozen `PLAN`; sprint = `ROADMAP`
  boundary-amendable → per-sprint immutable `PLAN-s<n>`; version-up = footprint-scoped plan vs the most-recent-green
  baseline). Verify `kata-bootstrap`/`kata-orchestrate` route to the correct planning depth **and** shape per mode,
  and surface any mismatch/gap (e.g. does the roadmap layer fire only when `delivery.shape == incremental`? does
  version-up reuse the right planning tier?). *(Non-blocking; post-loop-hardening; raised right before the S3b
  loop-back test. This sprint cadence — `ROADMAP` → `PLAN-s<n>` → freeze → orchestrate — is itself live evidence to
  audit against.)*

- **★ BRIEF — Capability-aware ("multi-modal") agent assignment (2026-06-25, big Phase-5 item).** Detect the
  target's **stack** (languages + frameworks + build/test tooling + config/IaC file-classes present, plus what's
  **installed** in the env) → route each task to a **specialist agent** (per-language coders + config/context
  specialists, as prompt-profiles over the spine). A routing layer over `kata-orchestrate`'s existing dispatch,
  NOT a new orchestrator. **Resolves the "multi-modal — separate brief?" question the `multi-model-orchestration`
  BRIEF flagged**; distinct axis from model/host routing. Primary consumer = Debug Mode. BRIEF:
  `specs/capability-aware-assignment/BRIEF.md`. Depends on install-portability (detection) + `kata-graph`. **Grill → build.**
- **★ BRIEF — "Debug Mode" delivery mode (captured 2026-06-24, enriched 2026-06-25; do NOT build yet — grill first).**
  A one-shot run-shape **sibling to Version-Up**, opposite intent: hold features/structure **fixed**, run a
  **systematic deep-debug pass** (assess all modules/tie-ins/logic; bugs out, behavior preserved; promote coding
  efficiency). The pitch = **"point it at a repo and debug in confidence"** — nothing broken, bugs fixed, via the
  language-specialist debug agents + the security stack (Snyk + `kata-evaluate` + D98 `kata-review`). **The
  onboarding/conversion killer-app**: the ideal first run for a dev who installs KataHarness, before converting
  their repo to the loop + moving into the vault. Reuse-maximally (a mode over the Harness, not a parallel stack):
  `kata-diagnose` · `kata-graph` · version-up footprint+no-regression discipline · `kata-evaluate`/`kata-review` ·
  `kata-tdd` · closeout/backout. **Borrow** from industry agentic debuggers (the installed
  `superpowers:systematic-debugging` + `gsd-debug`, SWE-agent, OpenHands, Aider) — keep our gates. **A top-level
  MODE (peer of version-up), selected and pointed at a whole codebase — self-contained; NOT a debug agent injected
  into the loop/other modes (anti-bloat). Specialists live INSIDE the mode; does NOT depend on
  capability-aware-assignment** (independent item; may converge later). BRIEF: `specs/debug-mode/BRIEF.md`. Open: the
  behavior-preserving / no-structural-drift gate (load-bearing) · systematic-sweep planning · the
  fix-vs-improve line · 4th mode to align (planning-approach↔delivery-mode).
- **★ DOGFOOD #2 RESIDUAL — wire the eval artifacts into a live gate (NEXT increment, 2026-06-19).** Dogfood #2
  built the *libraries + contracts* for evaluation self-sufficiency (`tools/run_result.py`, `footprint.py`,
  `mutation_check.py`; `kata-report`/`kata-evaluate` require them) but **nothing yet CALLS them** during a real
  run — the fresh-context evaluator flagged it as the headline residual. Next slice: make `kata-evaluate`/the
  gate command actually **emit `RESULT.json`** (via `run_result.run_gate`+`build_result`+`write_result`), compute
  the **footprint manifest** against the plan, and record the **mutation-proof** result — so depth is delivered
  end-to-end, not staged as parts. (Cosmetic: `mutation_check.went_red`/`non_vacuous` are always-equal — tidy.)
- **★ DOGFOOD #1 FINDINGS (2026-06-19, self version-up — see `.planning/specs/dogfood-selfup-1/`).**
  - **★ Evaluation-artifact self-sufficiency (HIGH — the headline).** A live run must be **evaluable in depth
    from its end artifacts alone** — today it is not. Upgrade `kata-report`/`kata-evaluate` to **self-emit**: a
    `RESULT.json` (gate name + **verbatim** stdout + exit codes + pass/fail counts + timestamp), **baseline +
    result commit SHAs**, a **footprint manifest + diff-stat** (assert touched ⊆ plan), a **recorded mutation/
    non-vacuity proof** (bake "would this test fail if its asserted line were removed?" into `kata-tdd`), and a
    **corpus-wide new-findings delta**. Directly answers the user's "is the writeup enough?" → no. *Strong
    candidate for dogfood #2.*
  - **version-up tree-sitter BLOCK too coarse (R1).** `kata-readiness` BLOCKs every version-up when tree-sitter
    is absent, even changes that need **no** structural graph (docs/validator-only footprints). Scope the BLOCK
    to runs that actually require `kata-graph` (or make graph optional when the footprint ∌ code structure).
  - **manual-drive friction (R2).** The loop ran without automated orchestrate/worktree dispatch or an installed
    host — confirms [[install-portability]] + [[multi-model-orchestration]] are real, not theoretical.
- **research/NOTES.md deep-eval** — score mattpocock skills, BMAD, GSD; record exactly what each
  `kata-*` skill adopts from where (the core bake-in work). *(do before/with v0.1)*
- **Adapters** — `codex`, `kiro`, `acp-quick`; AGENTS.md→tool-instruction-file normalization; skill-format mapping. *(v0.3/v0.4)*
  - **Per-tool instruction-file mechanics (D60–D63 AO forward-dependency, user 2026-06-18):** Claude = `CLAUDE.md`
    pointer→`AGENTS.md` (done); **Codex** = reads `AGENTS.md` natively incl. nested (~zero work); **Copilot** =
    `.github/copilot-instructions.md` (AGENTS.md support firming up) → pointer/generator; **Kiro** = **steering**
    (`.kiro/steering/*.md` with inclusion modes: always / `fileMatch`-glob / manual) — **NOT a tree-walk**, the
    structurally-different one. **AO seam:** `kata-orient`'s agnostic orientation contract (`protocol/orientation.md`:
    tiers + nested-module rollup + `kata-graph` adjacency pointers) is *rendered* per tool by the adapter — Claude/
    Codex→nested AGENTS.md/CLAUDE.md tree-walk; **Kiro adapter must render the module rollup as steering `fileMatch`
    files**, not per-folder tree-walk files. Verify current Copilot AGENTS.md adoption + Kiro steering details at
    build time (facts may have moved past the Jan-2026 cutoff). Captured for design later; do NOT reopen frozen specs.
- **`kata-engram`** — cognitive-fingerprint/engram injection from kiban/kagami; gated on a mature second brain. *(v0.4)*
  **[RE-MODELED 2026-06-24 (D99): "engram" is retired → Second brain (data) + Recall (per-vault Librarian/adapter) +
  Reason (`kata-reason`, the Advisor/decider). The whole C-arc + four-tumbler unlock + the C/B invariant are specced
  in `specs/second-brain-learning/BRIEF.md`. The engram→second-brain rename across `protocol/engram.md`/E1–E23/
  D9/D56/D74/D65/CONTEXT is a PENDING migration (own contract pass). This item folds into that BRIEF.]**
- **Engram-mediated escalation (FUTURE phase, harness-wide — A4-GB10)** — every human-in-the-loop escalation
  *anywhere* in the harness routes through the engram: (a) consult the cognitive fingerprint first → auto-resolve
  known patterns, only novel decisions reach the human; (b) feed every human resolution back into the engram so
  the next identical escalation auto-resolves. Net: human interrupts asymptotically decrease as the engram matures
  → strengthens the long-running promise. **Gated on PokeVault installed (READY, D58) + cognitive-fingerprint
  synthesis built**; grows from `kata-engram` (D9). Ties to the cognitive-twin arc (kiban/kagami). Prereq for
  trusting version-up's escalate-not-silent-expand at scale.
- **Plugin packaging** — package the suite as a Claude Code plugin + a portable bundle; `plugin.json`/suite version.
- **License selection** — choose an OSS license before public release.
- **★ FUTURE-GAP BRIEFS (ordered; quick plan docs written 2026-06-19, to grill→freeze→build AFTER the
  dogfood/improvement passes — except #1's timing is to-confirm).** Each is a `BRIEF.md` (pre-grill, not frozen):
  1. [[install-portability]] — `.planning/specs/install-portability/BRIEF.md` (workspace config + modular
     per-platform install: optional PokeVault link · bring-your-own-vault scaffold · aim-each-folder; the work/ACP
     host brings its own installer; setup doc cordoned with pointers). **Foundation for #2/#3.**
  2. [[multi-model-orchestration]] — `.planning/specs/multi-model-orchestration/BRIEF.md` (host-located
     orchestrator [work host→Quick/ACP · Kiro/Claude→there] · per-component model/tool routing incl.
     eval+test · cross-model handoff on one filesystem). Depends on #1.
  3. [[testing-model]] — `.planning/specs/testing-model/BRIEF.md` (**assess** a purpose-specific testing/eval
     model as a routed quality component; contract unchanged, only the model). Leans on #2.
- **★ Install & portability layer (NEXT after self-dogfood — the "plug into any vault/project" bridge).**
  Today the harness operates *in its own repo*; getting it to run against an arbitrary user's vault or project
  dir needs two unbuilt layers: **(1) distribution/discovery** — place the skills where the host agent finds
  them (Claude Code plugin or `.claude/skills/`; other tools via adapters) — overlaps "Plugin packaging" + the
  v0.3 adapter layer (spine #3); **(2) a one-time workspace-binding config** — distinct from per-run
  `kata.config`: user-set **roots** (vault root · project root · where `.planning/`, the LEARN feed
  `engram.learnFeed.dir`, and candidate skills `agentSkills.dir` live relative to the user's workspace). The
  config schema already has the *seeds* (those dir fields are path-configurable); what's missing is the init
  flow + the top-level workspace binding so it is **not PokeVault-shaped**. Likely a small spec → a `kata-install`
  /init capability. **Sequencing:** self-dogfood (needs none of this) → spec this layer → plugin packaging +
  adapters. *(Raised 2026-06-19 in the positioning/portability assessment — "control + plugs into your vault".)*
- **PokeVault install path (D58)** — the *reference* instance of the install & portability layer above: how the
  PokeVault vault (`C:\Users\taurr_nvs748q\PokeVault\PokeVault`, `toolkit/` area) installs/pins KataHarness.
  (Replaces the retired CPP consumption path, D57.)
- **Protocol specs** — flesh out `protocol/{board,tasklist,state,handoff}.md` schemas.
- **Quick/work version** — fork/branch strategy for the AWS-internal variant.
- **`kata-tasklist` reframe (D23)** — virtual task board over GSD structure + backlog, syncing to Jira/Asana
  via MCP (env has `pm-skills`/`atlassian`). Replaces the old file-locked-claim purpose.
- **A3 REVIEW carry-overs (2026-06-08, non-blocking)** — (a) `tools/` example-`kata.config` coherence check
  (validate a config's `tiers` keys resolve, `mode`/`effort` valid, modules have providers) — the maintainer-time
  complement to orchestrate's runtime load-guard (GB12/D45). (b) **A4:** sharpen `kata-readiness` Scope 1 wording
  so "validator green" clearly means the *harness* install vs the *target* repo when running version-up on an
  existing codebase. (c) `tiers`-key format (bare-verb vs `kata-<verb>`) is documented-consistent but unenforced.
- **Validator deeper checks (A1 REVIEW backlog)** — (3.1) `check_protocol_schemas`/`check_taxonomy_present`
  use substring matching → can't detect substantive erasure; add structural checks if it bites. (3.3)
  `check_tags_namespace` allows bogus `kata/...` sub-namespaces; add a `kata/...` prefix allowlist when
  `kata/tier/<tier>` becomes load-bearing (A2-time).
- **AO lateral/module-rollup is unexercised until a multi-module target (D76 follow-up, 2026-06-19)** — the
  validation stack confirmed `kata-orient`'s **nearest-module `AGENTS.md`/`CLAUDE.md` vertical rollup** + the
  **kata-graph lateral adjacency pointers** are a **latent no-op in *this* repo** (only root `AGENTS.md`/`CLAUDE.md`
  exist; no `kata.graph.json` on a greenfield run). It **degrades correctly** to root-only (graceful, triplicated
  in orientation.md / kata-orient / the AO hook) — forward-wiring for the 2026 nested-AGENTS.md standard, not a
  bug. **Exercise + test it when the harness orients inside a real multi-module target** (e.g. the dogfood
  version-up on KataHarness itself, or a consumer repo with per-module instruction files): add an AO test seam
  that proves rollup picks the nearest module + adjacency pointers resolve. Until then it's correct-but-inert.
- **β-runtime: structural redaction filter + test seam (D74 follow-up, 2026-06-19)** — today the LEARN-feed
  redaction (C3) is a **prose contract** (`kata-handoff` §7 "confirm no secrets/keys/PII") the emitting agent
  honors; "fail-closed" is an instruction, not enforcement. The β feed writes synthesis to an **external dir**
  (egress surface). **When β goes runtime** (the dogfood/ε arc), add an **automated redaction filter** the emit
  path must pass + a **pytest seam** that proves a secret/PII-bearing page is blocked. Until then the guarantee
  rests on agent obedience. *(Security-domain priority before any real second-brain backend is bound.)*
- **AI-slop / spiraling-session detection — ✅ BUILT 2026-06-22 (D94) as `kata-slop-check`** (standalone optional
  module `kata/module/slop`; general checks G1–G6 + 3 MIT-attributed checks from ai-slop-detector; fresh-context
  no-write; default-FAIL `SLOP-DETECTED ⇒ NEEDS_WORK`; dispatched in EVALUATE alongside `kata-evaluate`). The design
  fork below (**embed in `kata-review` vs separate skill**) was RESOLVED → **separate skill**. Original note kept for
  provenance:* ingest the OSS
  **ai-slop-detector** (`https://github.com/flamehaven01/ai-slop-detector`) and **deep-eval which of its checks
  to adopt** to catch **spiraling agents / degraded sessions / AI-slop output** — a common, real risk in
  long-running loops. **Design decision to make:** *embed* the adopted checks into `kata-review` (a new
  review axis / mode) **vs.** stand up a *separate* skill that runs as part of the EVALUATE phase (e.g.
  `kata-slop-check`, dispatched alongside `kata-review`/`kata-evaluate`). Lean on the **minimal-step bake-in
  discipline** (D41/GB8 — extract only the necessary stripped-down checks; do not over-port). **License + `source:`
  attribution required** before adopting any code (spine #12 / D12 — verify the repo's license). **Seams:** ties
  to `kata-review` (adversarial), `kata-diagnose` (bad-session symptoms), and `kata-selfhandoff` (session-health
  trigger — slop/spiral signal could fire a self-handoff/abort); a slop verdict should be a **default-FAIL gate
  finding**, never advisory-only. Captured for a later spec; do NOT reopen frozen specs. *(post-v0.1; quality module.)*
- **`kata-report` (D32)** — post-loop, handoff-phase build report: lite-synthesis of loop artifacts (DESIGN,
  DAG, decision ledger, manifest, diffs, evaluate/review verdicts, gate numbers) → durable `BUILD-REPORT.md`
  with a Mermaid structural diagram (of our own build DAG). Non-goal: from-scratch comprehension — that is
  `kata-understand`'s job (the two are complementary: report = what the loop did, understand = what the code
  is). Feeds `kata-improve`; open pointer for a future PM overlay (D30). Baseline near-free (spine-light);
  visuals tier up.
- **`kata-graph` — pre-processing structural map (PROMOTED to active A4, GB6).** New skill: builds a compact
  symbol/dependency map of an **existing** codebase so grill/plan/orchestrate ingest a large repo cheaply
  (token-saving). The version-up ingestion engine (was working-name `kata-map`). **Optional module
  (`kata/module/graph`, GB10) — the version-up preset bundles it by default. The *skill* ships in A4**;
  the *accelerated backend* (Graphify's AST graph / an MCP graph server) stays an **optional adapter binding,
  never a core dep** (agnostic core = grep/glob/Read; pre-staged via D29). Usage discipline for the accelerated
  backend if adopted: AST-only in-loop, bounded `--budget` queries, out-of-context oracle, NO always-on hook,
  no semantic pass in-loop. Plan it by evaluating OSS minimal-step examples (GB8). Graphify attributed in
  `source:` (spine #12).
- **`kata-understand` — post-processing comprehension map (desired state, GB7).** Post-loop comprehension map
  of a **newly-built** codebase → helps the *user* navigate/understand what KataHarness created (Understand-
  Anything nod). **Distinct from `kata-report`:** report = build-log synthesis (comprehension is its non-goal);
  understand = from-scratch comprehension of the result. **Optional module (`kata/module/understand`, GB10).**
  **Base: Understand-Anything** (`Lum1104/Understand-Anything`, MIT — purpose-built for teach-the-human
  comprehension/onboarding: `/understand-onboard`, `/understand-domain`; "graphs that teach"); Graphify a
  secondary source (multimodal/infra). Compose pluggable skills, don't fork-splice (A4 RESEARCH §5b). Name by
  job not vendor (§5c). Own later spec, post-v0.1. Plan via OSS minimal-step eval (GB8).
- **`kata-defer` — in-loop deferral / "nice-to-haves" capture (GB9).** Optional module
  (`kata/module/defer`). During a run, any out-of-scope-but-worth-keeping item (nice-to-have, post-processing
  candidate, deferred-for-a-reason) is appended to a run-scoped `DEFERRED.md` instead of being dropped or
  scope-crept into the frozen plan; compiled at HANDOFF; feeds project backlog / `kata-improve` /
  post-processing. **The structural complement to no-drift** (#1/#2): the pressure-release valve that makes
  one-shot=no-churn sustainable. Name soft (`kata-park`/`kata-icebox` alt). Post-v0.1 unless pulled forward.
- **Research mode (major post-v0.1 spec — path-forward brief done 2026-06-09, `.planning/specs/research-mode/RESEARCH.md`).**
  A `research` run-shape + module: `projects/Research/<project>/` roots; a recursive loop of disciplinary
  **research** + **adversarial-validation** + **evaluation** agents (the Co-Scientist roster). Thesis: the SAME
  spine with three swaps — work-unit = question/hypothesis, conformance floor = an **evidence floor** (citation
  integrity + adversarial survival + empirical ratchet; the never-tiered D22 analog), roster = disciplinary
  researchers. Reuses `kata-review` (adversarial), generalizes the bake-off judge (Elo tournament) and
  `kata-graph` (→ evidence graph `protocol/evidence.md`), and **shares the KG-emit contract with
  `kata-understand`** (research-mode is the upstream producer that fills the PokeVault vault, D58). Empirical sub-loop =
  Karpathy's ratchet = version-up's no-regression gate. Optional backends (GPT Researcher / STORM / Co-Scientist
  OSS) behind module contracts (the aider/Graphify pattern). **Sequence:** after v0.1 validation (D16) + Spec B
  (bake-off judge) + the Obsidian-KG/`kata-understand` spec. Coherence-audited (no chimera). Discipline-lens
  registry + recursion/budget guard (depth×breadth×exploration) are the only genuinely new substrates.
- **`design` module (own spec)** — UI/UX, 2D/3D assets, slides, mobile, image-FM imagery; slots into Advanced.
- **`docs/TAXONOMY.md`** — categories + `kata-<verb>` naming + tier-family convention (`kata-<verb>-<tier>`) +
  spine-vs-module. Motivated by the modes tiering work; partially specced in `docs/MODES-DESIGN.md`.
- **Skill efficiency refactors** (`.planning/SKILL-COST-RATINGS.md`) — grill L8-narrative + convergence
  checklist → `resources/` (~30% lighter); orchestrate worker-prompt → `protocol/`; tdd supporting-depth → pointer.
  Fold the grill one into Spec A (we restructure grill for tiering anyway).
- **★★ FINAL-PHASE — Deep loop optimization + an agentic-loop benchmark module (mid/long-term, user 2026-06-22).**
  **[PROMOTED 2026-06-24 (D99): `kata-loop-benchmark` is no longer just speed-garnish — it is the KEYSTONE that
  *defines* the C-arc unlock. It proves "C-on beats C-off" on a fixed reference task, which is what makes the
  second-brain readiness gate falsifiable. Build it alongside the C-arc, not strictly last. See
  `specs/second-brain-learning/BRIEF.md`.]**
  Do **near the end** of building KataHarness, once the feature set is implemented: **tune the loop** for **context
  economy AND speed/latency** (not just token cost). Build a **`kata-loop-benchmark` development module** that runs
  the loop on a **fixed reference task** (same content each time) and scores the output on **accuracy · quality ·
  speed** — a repeatable harness to measure tuning gains. Survey GitHub for an existing **agentic-loop / AI-process
  optimization benchmark**; adopt or borrow pieces (license + `source:` per D12). **Goal:** offset KataHarness's
  rigor with **speed** so output is balanced — *more controlled than Hermes (including the learning portions) at
  similar performance*, but with our controlled, high-quality output. Sequenced **after** WS-3/4/5 + Phase-5
  EXTERNAL. Ties to: WS-2 worker-self-timestamping (real timing data feeds the benchmark), the [[testing-model]]
  brief, and [[multi-model-orchestration]] (per-component model/speed routing).
- **★★ FINAL-PHASE — Recursive parallelism: "DAG within DAG" (advanced orchestration research, user 2026-06-22).**
  Today `kata-orchestrate` is **flat**: one orchestrator → leaf workers over a single frontier. Investigate letting
  the orchestrator, when it detects a **truly separable module**, spawn a **nested sub-loop** (a full Harness
  GRILL→…→EVALUATE on its own frozen sub-plan) rather than a single worker — **DAG-within-DAG**, recursive. Sub-loops
  run **concurrently** (each owning a disjoint file-subtree, its own default-FAIL gate intact), and the parent
  integrates only **green, independently-evaluated module artifacts** — two levels of parallelism = more parallel
  surface area, the speed win. **The load-bearing piece = a HARDENED separability test** — the thing that makes the
  orchestrator *smarter*: it recurses **only when decomposition is a provable win**, never an overcomplication or
  collision (handle more at once, at high judgment + high efficacy). Design it as a **conservative gate:
  default-FLATTEN unless proven separable** (mirrors default-FAIL — burden of proof is on recursion). Criteria:
  **transitive disjoint file-ownership** across the whole sub-tree (kata-graph-checkable → no collisions) · **no
  shared LOCKED decisions** · a **clean declared inter-module interface** (the only coupling allowed) · module size
  **above the overhead break-even** (small ⇒ flatten; the benchmark above sets the threshold) · module-level acyclic
  deps. The cut is **checked by a fresh-context evaluator, not self-certified** (no-self-cert spine), with
  **cross-level escalation bubbling** (a sub-loop's human-required surfaces to parent/human) and a future **engram
  learning surface** (learn which cuts paid off). A bad cut yields coupled sub-loops that fight at integration — so
  strictness is the whole game. **Survey prior art:** Hermes (recursive subagent trees) + Anthropic managed/
  orchestrator-worker + classical HTN/hierarchical planning. `kata-graph` could *propose* the module cut from the
  structural map. Research-grade → own BRIEF → grill → spec; post-v0.1. Composes with the loop-optimization benchmark
  above + [[multi-model-orchestration]] (sub-loops route to different models).
