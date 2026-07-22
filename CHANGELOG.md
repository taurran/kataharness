# Changelog

All notable changes to KataHarness are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) at the **suite** level. Per-skill
semver is tracked independently in each skill's frontmatter `version` field — see `docs/STANDARDS.md §3`.

---

## [Unreleased] — Quota-resilience Tier 1+2: park-and-tell on provider exhaustion

**Running out of tokens stops being invisible.** A provider rate-limit / quota / auth failure is now
detected from dispatch results, lapses the failing lane run-wide, and — when the primary path is hit —
**PARKS the run**: plain operator message (provider named, evidence quoted, NO stale upgrade URLs),
`human-required` escalation + breakthrough alert, automatic handoff write (`trigger: quota`, kind
unchanged), graceful boundary stop, `/kata-resume` re-entry. Never a retry loop, never a silent model
downgrade. Grill: `.planning/specs/quota-resilience/GRILL-LEDGER.md` (G-1..G-12 LOCKED; run authorized
under the operator's recorded overnight delegation, all §4 branches resolved from recorded operator
intent + precedent).

### Added
- **`tools/kata_quota.py`** (NEW, pure stdlib) — `classify_dispatch_result` (deterministic clean-error
  classifier over RESULT envelopes: 429/rate-limit ⇒ `rate-limited`, 402/credit/plan-limit ⇒
  `quota-exhausted`, 401/403/key ⇒ `auth`; malformed envelope RAISES, D136) · `lapse_decision` (G-2
  hybrid: FIRST classified signal, or 2 consecutive generic failures ⇒ `provider-unavailable`) ·
  `parse_kill_switch` (`KATA_OFF advisor|provider[:name]` over the EXISTING steering directive grammar;
  malformed uses surfaced loudly, never dropped) · `park_message` (plain words, no URLs — Tier 3 owns
  the registry). +42 tests incl. real-world provider error shapes exercised through real dispatch
  envelopes.
- **kata-orchestrate 0.15.0** — boundary kill-switch parse (operator-directed lapse) + the
  quota-resilience dispatch-failure step (classify → lapse → route by path criticality: optional
  subsystems lapse-and-continue per LD7; the primary path parks per G-4). `protocol/steering.md` gains
  the `KATA_OFF` verb; `protocol/handoff.md` gains the additive `trigger:` frontmatter field.
- **`kata_telemetry._validate_degraded`** — the `degraded [{scope, reason}]` passthrough joins the
  fail-closed `_validate_*` family (exactly `{scope, reason}`, non-empty strings, violation RAISES;
  scope stays an open string — BC with existing producers). New records this feature:
  `{scope: "provider", reason: "quota-exhausted"|"rate-limited"|"auth"}`.

### Backward compatibility
- No failure signals + no `KATA_OFF` directive ⇒ byte-identical behavior. `kata_dispatch.py`,
  `kata_models.py`, `kata_steer.py`, `kata_adaptive.py` **byte-untouched** (diff-verified). Non-Anthropic
  ladders stay empty by decision (G-6): quota NEVER triggers a model downgrade — park, don't degrade.
- Tier 3 (per-provider upgrade registry · silent-hang watchdog · preflight quota headroom) is EXCLUDED —
  its own future grill (the codex hang-on-402 class still lands as `timeout`; its captured stderr now
  classifies when present, but the no-signal hang needs the watchdog).

### Honesty
- Engine legs are test-proven (42 quota + 9 telemetry pins); the orchestrate wiring is **prose,
  live-if-it-occurs, UNFIRED** — no real quota event has exercised the park sequence end-to-end. Labels
  travel with the claim (PD-2).

---

## [Unreleased] — Advisor consult (kata-advise): the Fable-tier advisor-executor pattern (D167)

**Hard tasks stop burning blind retries.** A scoped, anchor-relative **Fable-tier advisor** the loop can
consult — execution/coding workers ask a narrow question on an intensive issue, and the evaluation
mechanic consults after a generation reset or repeated failures instead of retrying blind. The advice is
**advisory only: it never changes a gate verdict, is never auto-applied, and never expands the frozen
goal** (S-2). Grill converged over five fresh-context passes (HOLD 8 → HOLD 3 → HOLD 3 → HOLD 2 → SHIP);
the adversarial freeze-gate then returned SHIP-WITH-FIXES (7 folds). Spec:
`.planning/specs/advisor-executor/` (28 LOCKED entries G-1..G-9 · S-1..S-27 · EV-1; D167).

### Added
- **`skills/plan/kata-advise/SKILL.md`** (NEW, 0.1.0, experimental) — the fresh-context, no-write advisor
  consult; conductor-dispatched only, returns a machine-ingestible `{diagnosis, approach, risks,
  citations, optional non-authoritative sketch}` payload consumed by the agent (redispatch brief /
  requesting planner), rolled up for the human after-action (G-7).
- **`tools/kata_advisor.py`** (NEW, pure stdlib) — the advisor spend/state/outcome engine: own budget
  pool (standard **5/1**, advanced **10/2**), FCFS + floor reservation, grant-before-dispatch commit,
  board-DECISION recount trail, and the **EV-1 outcome pairing** (`advised-pass` / `advised-fail-bumped`
  / `advised-fail-ceiling`) that makes advisor ROI an evidence question.
- **Sibling legality gate (`kata_models`):** `advisor.approved` is the **SOLE** advisor legality record,
  fully decoupled from `models.premium` — new pure `advisor_rung_of` (Fable-target for ANY sub-fable
  anchor; sonnet/haiku consult **fable**, never +1, never mythos), the `advisor_status` gate, and the
  `ADVISOR_EVENTS` registry (sibling to `ADAPTIVE_EVENTS`). The D148 amendment (G-2) is realized as a
  sibling gate, not an edit to the premium contract (S-16/S-20/S-24).
- **`advisor` config block** (`protocol/config.md`) + **`advice-requested` escalation kind**
  (`protocol/escalation.md`, async/non-halting, cap 2 per task) + **`protocol/advice.md`** payload schema
  of record.
- **Two-moment grant + hooks** (kata-orchestrate / bootstrap / preflight / initiate / planner prose):
  advanced consent at bootstrap composition, standard opt-in once per run at preflight, essential
  excluded (G-5/G-8/G-9); advise-first / bump-second at the failure threshold, reroll-trigger-#2
  grounding, fix-loop diagnose-first-then-consult; the gate and closeout never consult (G-4). Additive
  presence-discriminated `advisor` telemetry ledger key.
- **Semver bumps:** kata-orchestrate 0.13.0→0.14.0 · kata-bootstrap 0.6.0→0.7.0 · kata-preflight
  0.3.0→0.4.0 · kata-initiate 0.7.0→0.8.0 · kata-design-doc 0.1.0→0.2.0 · kata-plan-essential/-standard/
  -advanced 0.1.4→0.2.0 · kata-advise NEW at 0.1.0. Catalog **48→49** skills.

### Backward compatibility
- **Absent `advisor` block ⇒ every leg OFF; behavior byte-identical to today** (S-4 — the
  `models.adaptive` precedent). `models.premium`, `ADAPTIVE_EVENTS`, and `tools/kata_adaptive.py` are
  **byte-untouched** (S-16/S-20); an advisor event in `models.premium.scope.events` stays ILLEGAL. The
  default-FAIL gate is never weakened. Malformed `advisor` block ⇒ load-guard STOP (D136 fail-closed).

### Honesty
- Engine legs (legality gate, Fable-target routing, budget/spend/telemetry) are **test-proven**. The
  **dispatch mechanics are exercised live n=1** — an operator-granted consult on this repo's fable-anchored
  dogfood run (arm (a) inherit-at-anchor: gate → budget → dispatch → structured response → disposition). The
  **four hooks are test-proven prose — live-if-they-occur, unexercised**; arm (b) (sub-fable ⇒ Fable
  dispatch) and the standard-mode carve-out are **test-proven, not live-proven** this run. Labels travel with
  every claim (PD-2).

### Fixed
- **Mutation proving corrupted the live tree (D1 phantom-corruption, root-caused 2026-07-14).**
  `mutation_run.prove_non_vacuous` wrote mutated bytes to the REAL source file and restored in
  `finally` — concurrent readers saw corruption inside the write→restore window, and a hard kill
  persisted the mutation on disk (the recurring IndentationError hauntings). The vector fired on
  EVERY gauntlet: seven real mutation proofs run inside pytest-unit. Now the proof runs
  **SANDBOXED**: the project root (marker-derived from `pyproject.toml`/`.git`, fail-closed; or
  explicit `project_root=`) is copied to a temp tree (`.git`/`.venv`/`.kata`/caches excluded),
  the `test_cmd` is path-redirected into the sandbox (live-root substitution with a `.venv`
  interpreter lookahead + a Windows case-insensitive residual live-root guard that RAISES),
  baseline AND mutated both run inside the copy (Doctrine law 8: the comparison differs only by
  the mutation), and the live file is **never written** — pinned by a runner that reads the live
  file mid-run. Runner contract widened to `(cmd, cwd)`. Blast radius (adval-corrected count):
  the seven proofs NAMED in the INTENT plus the whole fleet — **~60 real `prove_non_vacuous`
  call sites across 14 test modules** — all route through the sandbox, all green (~0.8s/proof;
  ~3.5 MB/copy). Adval folds: `_root_pattern` right boundary (a root that PREFIXES a sibling
  path — `C:\proj` vs `C:\proj2`, `<root>-backup` — is never rewritten and never trips the
  guard) + true-`.venv`-component-only preservation (`.venv-old` substitutes loudly; doubled
  separators still preserve); kata-tdd SKILL prose updated off the superseded mutate-live
  design (0.4.0→0.4.1). Grill record: `.planning/specs/mutation-sandbox/GRILL-LEDGER.md`
  (D1–D5 LOCKED + adval addendum).
- **Worker dispatch discarded the provider error signal (`tools/kata_dispatch.py`).**
  `_subprocess_runner` ran `capture_output=True` but returned only `proc.stdout`, and `dispatch()`
  built every failure envelope as bare `worker exited {code}` — the codex/kiro CLIs' stderr
  (rate-limit / quota / auth text) was captured and thrown away. The injectable runner contract is
  now a hard 4-tuple `(exit_code, stdout, stderr, result_text)`; a deterministic dispatch-side tail
  cap (`_stderr_tail`, last 4000 chars, literal marker when clipped) carries stderr into the payload
  of all three FAILURE envelopes — exit≠0, timeout (captured-so-far `TimeoutExpired.stderr`,
  decode-if-bytes), and unparseable-result. The `completed` envelope is **byte-unchanged** and `raw`
  keeps stdout-only semantics; blast radius is codex/kiro dispatch only (Claude workers use the
  in-process path). Prerequisite for the quota-resilience classifier. The `kata_preflight.py`
  sibling runner still discards stderr — deliberately deferred (`.planning/DEFERRED.md` DEF-1).
  Grill record: `.planning/specs/dispatch-stderr-fix/GRILL-LEDGER.md` (D1–D4 LOCKED).
- **Windows bootstrap scripts abort on native git stderr under merged streams (observed live
  2026-07-21).** PS 5.1 wraps a native command's stderr in ErrorRecords whenever an enclosing pipeline
  merges streams (`update.ps1 ... 2>&1`, CI/automation hosts); under the scripts'
  `$ErrorActionPreference='Stop'` the FIRST record becomes a TERMINATING error even on exit 0.
  `update.ps1 --check` aborted at `git fetch origin` **precisely when an update was available** (fetch
  prints its ref summary to stderr on success) — and the mid-fetch abort left a stale
  `origin/master.lock` behind (the exact D157 silent-stale-install precursor; the D157 guard caught it
  on re-run). Same class in `install.ps1`: `git clone` always writes "Cloning into ..." to stderr, so a
  merged-stream install aborted a SUCCESSFUL clone (A/B-proven). The ENGINE leg carried the same
  class (adval catch): `kata_install.py` prints its vault-recommendation note to stderr BY DESIGN on
  a successful fresh install, and `uv` prints sync progress to stderr — so a merged-stream run could
  still terminate at the engine, on the update path AFTER `git reset --hard`. Fix: new
  `Invoke-KataGit` helper in `update.ps1` (EAP drops to 'Continue' for the one native call, stderr
  merges into the pipeline as plain strings, `$LASTEXITCODE` untouched for the existing
  `Assert-GitOk` gates) routed through both fetch sites, the `Test-GitClone` origin probe, the 3-leg
  checkout fallback (interim-leg stderr no longer kills legs 2-3), and the `Assert-RemoteTruth`
  ls-remote; the `install.ps1` clone and BOTH scripts' engine invocations get the inline equivalent.
  Fetch/clone gain `--quiet` (success stderr suppressed; the script's own D157c advancement message
  reports the outcome). Bash mirrors (`update.sh`/`install.sh`) are exit-code-gated and unaffected —
  gating parity preserved (ps1 fetch/clone are now `--quiet`; the sh mirrors are not — cosmetic
  divergence only). Proven live: the exact failing invocation now passes both `--check` branches
  (update-available + already-current, exit 0); the clone A/B shows old-pattern ABORT vs new-pattern
  success on the same successful clone; a fresh-context adval empirically re-derived the PS 5.1
  semantics in a live child host (EAP/exit-code/splat behavior all confirmed). **Honesty (PD-2): the
  full-update path (checkout fallback legs, reset, ls-remote truth check), the factory-reset fetch,
  and the wrapped engine legs are code-proven + pin-tested only, NOT live-run this session** — they
  exercise the same wrapped primitive and get their live n=1 at the operator's next real update.

## [0.3.0] — 2026-07-05 — Adaptive tiering: evidence-driven model routing (D150)

**Model selection stops being a static table and starts learning from the run.** Three layers: **L0**
the D131 relative-differential table (unchanged — the deterministic base and ONLY fallback); **L1**
per-dispatch evidence modulation; **L2** ledger acceptance routing (contract shipped, activation
`models.adaptive.l2` default-OFF, named-deferred until post-R6 ledger volume). Delivered as PAIRED
gated amendments (model-tiering Amendment #2 + inline-eval-m4 Amendment #6 — no frozen line edited).
Gate journey: freeze-gate v1 HOLD (2 BLOCKER) → 19 folds → re-gate SHIP-WITH-FIXES → 8 folds →
operator VETO-FLAG resolution → whole-feature Fable ADVAL SHIP-WITH-FIXES (1 HIGH: the R-9 economy
exclusion made STRUCTURAL in code) → 11 folds → re-gate **SHIP**.

### Added
- **`tools/kata_adaptive.py`** (NEW, pure stdlib) — the L1 state machine: fail-bump (F=2, once/task,
  gate rejections + STANDING rerolls only; bumped tasks exempt from downshift), streak downshift
  (K=3, `coding`-class only, ×2 damper on a downshift-attributed rejection), −1-capped downward
  modulation (complexity and streak never stack), FCFS premium budget (N=10, last 2 reserved for
  freeze-gate events), `tier:` DECISION render/recount (fail-closed durable trail),
  `state_from_recount` restart recovery, `apply_delta` clamp + anchor-landing OMIT emission,
  `l2_base_rung` (the AT-L18 contract), anchor-switch reset (budget spend preserved).
- **Event-scoped premium (`kata_models`):** `premium.scope` is TYPE-DISPATCHED — a LIST keeps the
  v0.2.1 run-long class semantics byte-for-byte; an OBJECT `{events, budget}` scopes the premium
  rung to the 7-event hard-moments registry (`ADAPTIVE_EVENTS`, each citing its covering dispatch
  site) within the call budget. **R-9 is structural in BOTH forms** (economy never fires premium —
  code-enforced). `premium_rung_of` family-agnostic helper; all prose renamed to "the premium rung"
  (GPT-5.6-class models qualify by registering a family ladder rung — no mechanism change).
- **Calibration columns (`kata_telemetry`; M4 Amendment #6):** ADDITIVE OPTIONAL v3 ledger keys
  `verdictByTier` (standing verdicts by deciding tier; overturned screens under
  `overturned×<tier>` — the C-3 input) + `tierEvents`; absent-honest accessors;
  `verdict_by_tier_totals` + `overturn_rate` aggregates (calibration-row exclusion, min_samples=5).
  **NO v4 minted** — deployed v0.2.1 readers keep reading the shared ledger.
- **Cheap-then-escalate evaluator ladder (kata-orchestrate 0.11.0; M4 Amendment #6):** a `correct`/
  `reroll` verdict is re-adjudicated once, one rung up, CLAMPED STRICTLY BELOW the anchor (M4-L7
  preserved; the advanced-Anthropic inert arm stated); only the STANDING verdict drives the ladder,
  the bump counter, and the streaks. `continue` never re-adjudicates (green path stays one call).
- **Plan-frozen `complexity: low|standard|high`** per-task rating (kata-plan 0.1.4) — `low` starts
  the build worker one rung down; assessed at plan time, attacked by the plan freeze-gate, never a
  runtime LLM value judgment.
- **Two-variant consent pitch (kata-preflight 0.3.0):** the OBJECT-form premium disclaimer reads
  the composed `scope.events` + budget verbatim at the prompt — the approval IS the optimization
  guarantee. kata-bootstrap 0.4.0 composes the full `adaptive` block at Phase 3 (compose = consent).
- **SMOKE-MODELED** (`.planning/specs/adaptive-tiering/SMOKE-MODELED.md`): on the real v0.2.1 build
  shape, event-scope premium = **−86% premium-rung calls** (59→8) and the re-adjudication ladder =
  **−93% modeled tokens + 13→0 wrongful kills** on the pre-fix FP trigger mix — MODELED not
  measured, every input cited, caveats stated; the live A/B is queued post-R6 with arms pinned.

### Backward compatibility
- `models.adaptive` ABSENT ⇒ **every adaptive leg OFF** (load-time; no retroactive flip — the
  D147/CA-L34 discipline); block presence = consent; bootstrap writes it explicitly at its next
  composition. `premium.scope` LIST form ⇒ v0.2.1 byte-for-byte (golden 48-skill × 3-mode × 5-anchor
  inertness sweep + literal pinned sample). Absent `models`/`premium` ⇒ frozen behavior (R3/D148).
  Mid-run `/model` switch ⇒ adaptive state reset (LOUD), budget spend preserved.

## [0.2.1] — 2026-07-05 — Context autonomy: the gauge-driven self-handoff loop

**The conductor's context stops being the run-fatal resource.** v0.2.1 wires a context gauge to the
ALREADY-EXISTING self-handoff trigger prose (kata-selfhandoff SKILL.md) — SR-1: no new threshold concept,
a mechanism for a policy that shipped un-wired. The 8-hour walk-away scenario (OP-8): one preflight approval
bundle, then trigger @ 0.70 of the host-reported effective window → durable HANDOFF refresh at a wave
boundary → host auto-compact / respawn on kata's recommended schedule → SessionStart(compact) re-anchor →
resume at the next task boundary with **zero task loss**. Every degradation leg is graceful rotation or a
surfaced preflight BLOCK — never silent death at the hard context limit. Frozen DESIGN + build: **D146**.
Both **[VETO-FLAG]** items resolved LOCKED by the operator: report home = `.kata/reports/…` (CA-L22),
preflight strictness = intent-keyed BLOCK (CA-L25). *Tagged 2026-07-05 after the C11 live-proof battery
(CA-A1..A5 + A8 row 1 + A11 b/c), the operator-directed pre-merge tasks (M4 Amendment #5/D149 + the
final 3-reviewer fresh-context pass, all findings folded), and the operator merge gate.*

### Added
- **The context gauge + fallback** (`kata_gauge`): 0.70-of-effective-window trigger arithmetic, backstop
  window recommendation, deterministic N-wave rotation fallback, 300 s bridge staleness. (E1)
- **Claude statusline bridge + chain-never-clobber wrapper** (`adapters/claude/statusline.py`,
  `statusline_chain.py`): kata's own statusline writes a superset bridge unchained; when a user statusline
  exists, kata offers a chaining wrapper (shell=False list-argv, shlex-or-skip, batch/metachar gate) that
  writes its own sibling bridge and never clobbers the user's. (A1/A2)
- **SessionStart(compact) re-anchor + PreCompact HANDOFF surface hooks**; kata-selfhandoff trigger wiring;
  kata-orient 3-tier resume; handoff `kind:` taxonomy; AGENTS.md standing re-anchor line. (A3–A7)
- **Preflight approval bundle + premium gate** (kata-bootstrap 0.3.0, kata-preflight 0.2.0): ONE bundle
  (installs + allowlist + premium gate + compact-window recommendation + host-settings write slot),
  collected once; force-run marker + gitSha re-arm; five-class allowlist checklist; stranding verdict. (C1/E4)
- **Report budgets + continuation contract** (kata-orchestrate 0.10.0, kata-tdd 0.3.0): dispatch
  startup-load budget (WARN >0.30 / mandate >0.40), size-contracted worker reports (verdict + pointer
  inline, bulk to `.kata/reports/`), the M4-primitive-reusing continuation contract. (C3)
- **`protocol/observability.md`** — the log-reader orientation contract (telemetry ledger, board, checkpoint
  trailers, preflight, handoff, reports, durable-citation rule; no gauge/bridge row — CA-L41). (C4)
- **Five per-platform recommended-config pages** — Kiro, Codex CLI, Copilot, Cursor, Gemini CLI (docs-only,
  no non-Claude live legs; Windsurf cut). (C5)
- **Adapter contract primitive (c) session-respawn** (`adapters/ADAPTER-CONTRACT-M4.md`); glossary fold into
  `CONTEXT.md`; plan-time quantum-sizing RUBRIC (kata-plan tiers 0.1.3). (C6/C7/C8)
- New kata.config keys `contextAutonomy`, `contextTrigger`,
  `models.premium {offer, approved, scope, grantedMode}`; `.kata-settings.json` keys `firstRunCompletedAt`/
  `firstRunVersion`/`hostPosture`/`acceptedDefaults`; ledger schema v3 `parentTokens`. (E7/E2/E6)

### Changed
- **Model tiering — gated premium amendment (D148):** under `kata.config.models.premium` with all four
  conjuncts (`approved` ∧ work-class ∈ `scope` ∧ `offer` exactly one rung above the anchor ∧
  `mode == "advanced"`), CRITICAL and CODING work MAY elevate to the premium rung (Fable); economy never.
  Appended as a post-freeze addendum to the model-tiering DESIGN; absent `models.premium`, the frozen spec
  governs byte-for-byte.
- **kata-readiness 0.2.1** gains a WARN for pre-v0.2.1 configs lacking `contextAutonomy` (written at next
  composition, or opt in by config edit); no retroactive flip. (C2)
- **kata-evaluate 0.3.1** + kata-review tiers: verdict-tier variance calibration note (prose-only). (C9)
- **M4 Amendment #5 (D149, pre-merge):** the inline-eval `verify_fail` signal is now OWNED-SCOPED — the
  checkpoint trailer gains an optional nullable `verify.owned` exit (`emit-trailer --owned-exit`; kata-tdd
  0.4.0 producer mandate), and the scorer reads it in preference to the suite-scoped `verify.exit` (BC
  fallback — the C-1 false-positive class: 13/13 retroactive triggers were sibling-task suite artifacts).
  Plus the F2 dispatch-base index sentence in the kata-orchestrate ladder span (0.10.2): a reroll anchored
  at the dispatch base indexes the fresh attempt from 0 (CA-L44). τ/weights deliberately untouched.

### Backward compatibility
- **BC guarantee:** absent/unconfigured, EVERY new surface degrades to prior behavior — `contextAutonomy`
  absent ⇒ OFF on the key-consulted (incremental) path; `contextTrigger` absent ⇒ 0.70 default; `models`
  block absent ⇒ inherit everywhere; gauge absent/stale ⇒ deterministic N-wave rotation; a user statusline
  is NEVER clobbered (chain-or-skip); hooks absent ⇒ AGENTS.md-line manual re-anchor. See DESIGN §4.
- **The ONE named BC departure (D147, R-37):** one-shot run shapes — INCLUDING pre-v0.2.1 configs with no
  `contextAutonomy` key — rotate context UNCONDITIONALLY. Deliberate: protective + additive, always mandated
  by the self-handoff prose, degrades gracefully. The absent-⇒-OFF rule is scoped to the incremental path.

### Security
- **Statusline chain wrapper subprocess sink** (`adapters/claude/statusline_chain.py`, A2): runs the
  operator's OWN `statusLine.command` with strictly LESS privilege than the host already grants it —
  `shell=False` list-argv, shlex-plain-parse-or-SKIP eligibility, full shell-metacharacter gate (incl. the
  cmd.exe-only `%`/`^`), and `.bat`/`.cmd`/`.com` targets SKIP-ineligible (implicit-`cmd.exe` vector closed;
  extensionless PATHEXT residual disproven live). Registered in `protocol/exec-safety.md` (operator trust
  domain). Snyk MEDIUM CWE-78 (argv → subprocess) accepted as a gate-adjudicated FALSE POSITIVE in `.snyk`
  (reason recorded; 6-month expiry 2027-01-04 — execution sink).

## [0.2.0] — 2026-07-04 — Freeze/Float M4: the inline evaluator/reroll (DSpark-informed)

**The smaller loop, sharpened — shipped end-to-end in one operator-directed pass.** Everything
below this header up to and including the M1-P2 float section ships as v0.2.0. Live proof (D145):
the ladder fired on real evidence (trigger → diff-cited `correct` verdict at a D131-resolved
below-anchor tier → kill-and-redispatch with a corrective NOTE → green), the happy path cost zero
LLM calls, the A/B showed 0 gate rejections vs the control's 1 rejection + 1 fix cycle, and the
float ran its first real `builds_against` edge (pin MATCH, stubs 0, danglers 0). Nine adversarial
gates ran this milestone (2 DESIGN, 2+2+2 PLAN, 1 P0.1 delta, 1 L19 cross-seam, 1 P0+P0.1 eval) —
every one caught real defects, all folded. Honest limits: the <1% green-run cap is AT-RISK at
owned-module chunking (remediation named: coarsen the chunk unit); research/debug class EXTRAS
await producers (named deferrals); LD7-fallback × M4 topology deferred; toy-scale recovery
economics favor the control (D145 — the payoff is scale-dependent by design).

## [Unreleased] — Freeze/Float M4-P2: research + debug adapters (per-class leashes)

**One scheduler, three signal sets — honestly scoped.** The freeze-gate's HOLD caught both new
signal sets pointing at artifacts that don't exist in the claimed shapes; v2 shrank the phase:
per-class τ leashes (0.45 vs 0.50) ship LIVE on the universal base trio + slack; the class extras
(coverage/scope/hypothesis signals) are DATA'd at A1-Q4 weights with ABSENT-by-default,
NAMED-DEFERRED producers. `kata_risk` DEFAULT_WEIGHTS_BY_CLASS + class_signals overlay plumbing
(+35 tests, 3 mutation proofs); orchestrate 0.8.0 (class adapters subsection + the one declared
call-line edit); kata-plan RUBRIC `class:` field + the `area:` task-id freeze guard (tiers 0.1.2).
Instrumented run #3: 4/4 evidence MATCH; **the ledger's ≥3-run threshold for offering
`inlineEval: on` is met.** Suite 2505/3; validator 48/0/0. D144.

## [Unreleased] — Freeze/Float M4-P1: the code-class mechanism (`inlineEval: on` live)

**Detection now acts.** PLAN double-gated (v1 HOLD 4H/4M/5L; re-gate v2 SHIP-WITH-FIXES 1H/3M/3L —
all 20 folded); built dogfooded + instrumented (ledger row #2: 4 tasks / 10 checkpoints, 10/10
evidence digests re-derived MATCH, zero drift, first-pass 4/4); L19 integrated cross-seam sweep
over the whole M4 body: SHIP-WITH-FIXES 0 HIGH / 4 MED / 6 LOW, all folded.

- `tools/kata_risk.py` (NEW): the one-dial capped-sum risk score (A1-Q4 weights/τ as `[TUNABLE]`
  data; STRICT `>` trigger comparator, mutation-pinned), `should_trigger` decision function,
  VALUE-object `resolve_inline_eval_params` (object form REQUIRES `mode`); pure/no-subprocess,
  57 tests, 4 mutation proofs, Snyk 0.
- `kata-inline-eval` 0.1.0 (NEW, 48th skill): one-page fresh-context no-write chunk evaluator
  (`VERDICT: continue|correct|reroll`); registered `economy` in D131 with a 15-cell never-anchor
  pin test.
- `kata-orchestrate` 0.7.0: the M4 scheduler (scan at liveness passes + DONE, sha-carrying ladder
  `DECISION` lines, cursor recovery, SCAN-ERR once-per-window, ONE batch slack rule) + the
  corrective-action ladder (inline eval at strictly-below-anchor with BOTH never-anchor carve-outs
  incl. the R2 reciprocal exception; correct/reroll = one kill-and-restart primitive on attempt
  branches with confirmed-dead + index-continuity + liveness-reset semantics; grounding pass before
  reroll #2; trigger #3 = existing `human-required`; A1-Q5 arbitration verbatim; per-platform kill
  bindings); `inlineEval` object form live (`{mode, tau?, weights?}`).
- `adapters/ADAPTER-CONTRACT-M4.md` (NEW, M4-L9 normative; LD7 fallback named-deferred);
  `kata-tdd` 0.2.1; config.md `inlineEval` v2 row; +1 restore seam pin test (checkpoint-trailer
  bodies inert through --no-ff merges). Suite 2396 → 2470; validator 48/0/0. D143.

## [Unreleased] — Freeze/Float M4-P0: telemetry (the inline-evaluator measurement substrate)

**Pure measurement — record everything, act on nothing.** M4 DESIGN frozen through a double
fresh-context freeze-gate (v1 HOLD 4 HIGH/7 MED/3 LOW; v2 SHIP-WITH-FIXES 2 HIGH/4 MED/4 LOW — all
folded); PLAN-p0 likewise double-gated (v1 HOLD incl. a relocated kill-switch BLOCKER; v2
SHIP-WITH-FIXES incl. a wrong-repo CWD bug and a git-config-dependent digest). BC:
`kata.config.inlineEval` absent ⇒ `off` ⇒ byte-for-byte today's behavior.

- `tools/kata_telemetry.py` (NEW): fail-closed (D136) `Kata-Checkpoint:` trailer parser +
  checkpoint scanner (duplicate/merge-commit trailers raise), evidence digest over git blob hashes
  (stamp = index, verify = commit tree + parent-tree deletion semantics; `--no-renames` +
  `core.quotepath=off` pinned), slack substrate (PROGRESS events, ledger class-median with
  calibration-row exclusion, zero-progress guard), per-task telemetry records, ledger rows, and the
  worker CLI `emit-trailer` (required `--repo-root`). Suite 2306 → 2376 (+70, incl. a real-git
  round-trip with deletion + rename); 7 mutation proofs; Snyk medium+ 0.
- `kata-orchestrate` 0.6.0: `inlineEval` load-guard (malformed ⇒ STOP, never coerced); the
  conditional worker checkpoint mandate (concrete injected CLI invocation; tools-dir-unresolvable ⇒
  `effectiveMode: "off"` + NOTE); per-task telemetry step (detection-only — the existing lane
  check's blocking posture untouched); ledger closeout with D141(b) board-`DECISION` approval gate.
- `kata-tdd` 0.2.0 (checkpoint cadence: stage → emit → commit, mechanical outputs only, D33);
  `kata-bootstrap` 0.2.0 (`inlineEval: "telemetry"` new-run default; offer `on` at ≥3 ledger runs);
  `kata-plan` RUBRIC `estimate:` authoring + freeze-time validation (tier skills 0.1.1).
- `protocol/config.md` `inlineEval` row; 4 new exec-safety sink registry rows;
  `.planning/telemetry-ledger.md` (NEW — the committed calibration ledger, human-gated appends);
  `.kata-settings.json` gains the `telemetryLedger` locator (documented in `kata_settings.py`).
- D141: partial supersede of D134 (worker checkpoint commits become load-bearing for M4 reroll
  anchoring; restore semantics unchanged) + the ledger commit-authority ruling.
- **P0.1 (operator-directed observability addition, DESIGN Amendment #4, routing branch 3, D142):**
  ledger row schema v1 → v2 (additive) — `perTask` cost columns (explicit nulls), `failureKinds`
  (orchestrator-classified at gate time, `FAILURE_KINDS` enum, D33), `degraded` events; v1 rows
  read as `unclassified`/null (no backfill; `failure_kinds_of` accessor; unknown ledger version
  raises). `kata_restore` structured degraded signal (folds BACKLOG #16): additive
  `collect_integrated_tasks_ex` + `restore()` `degraded`/`degraded_reasons` keys incl. the
  previously NOTE-less git-error path (`integration-history-unreadable`); NOTE prints stay.
  Suite 2376 → 2396 (+20); 3 mutation proofs; Snyk 0; orchestrate 0.6.1 (gate-time failure-kind
  classification step).

## [Unreleased] — Freeze/Float M1-P2: the float (contract-edge scheduling)

**The behavior change of the Freeze/Float program (D138): a contract-only dependent now dispatches at
freeze, in parallel with its provider — free wall-clock, same tokens.** BC: every surface no-ops when no
`builds_against` edge is declared (which is every existing run). Frozen `PLAN-p2-float.md` survived THREE
adversarial freeze-gates (v1 HOLD 18 findings, v2 HOLD 10, v3 SHIP-WITH-FIXES) before any code.

- `tools/contract_gate.py` (NEW, 460 lines): the final-gate independent re-derivation as fail-closed,
  mutation-proven decision code — `verify_contract_gate` (supersede-id cross-check, surface-drift vs
  pin/newest-supersede, commit-granular temporal invalidation coverage), `dangling_contract_imports`
  (base-module semantics), `expand_ownership_paths`, `parse_trailer_events` over a NUL-delimited commit
  scan, `write_contract_gate` → `.kata/contract-gate.json`. 28 tests, 6 guards mutation-proven, Snyk 0.
- `contract_edges.surviving_stubs` gains additive `exclude_dirs` (vendored trees; never excludes
  at-or-under `contracts/`).
- `kata-plan/RUBRIC.md`: the `builds_against:` schema + contract authoring rules (provider-owned
  `contracts/<id>/` + `__init__.py`, sentinel lifecycle, freeze-time pin + plan commit).
- `kata-orchestrate` 0.5.0: dispatchable-at-freeze frontier clause; freeze-time companion checks
  (materialization, pin verify, edge honesty); provider-integration surface re-verify; the canonical
  supersede route (durable trailers at ROUTE TIME on the superseding commit); the contract final-gate
  step; fix-loop contract re-verification.
- `kata-evaluate` 0.3.0: contract-gate evidence rule (artifact absent/malformed/failed/non-empty
  companions ⇒ NEEDS_WORK — the independence leg; orchestrator compliance is never trusted).
- `kata-review/RUBRIC.md`: contract-edge-honesty attack surface (semantic honesty, pinned-constant
  reliance, `depends_on`-in-disguise).
- Adval D139 preceded this build: 9-reviewer integrated sweep of Milestone 1 → P1, 5 HIGHs folded.

## [Unreleased]

### Release Hardening — Milestone 1 (Kenjiri one-shot lessons) — 2026-07-02

Six field-verified harness fixes from the Kenjiri v1.0.0 one-shot, each verified against the code by
fresh-context investigators before the fix (three reshaped from the run's proposal to avoid regressions).
Spec: `.planning/specs/kenjiri-lessons/`. Baseline `653f501` (pytest 2177) → **2190 pytest**, validate
47/0, Snyk medium+ 0.

- **F1 · Preflight fail-closed on malformed manifest** (`kata-preflight` 0.1.1) — a misspelled/absent/
  wrong-typed top-level `dependencies` key collapsed to `[]` and passed vacuously as `ready`. Now shape-
  validated (key present + list); a present-but-empty `[]` stays `ready` (legit state). +4 tests, mutation-proven.
- **F2 · Graph src-layout import resolution** (`graph_gen.py`) — `from pkg.mod import x` on a `src/` layout
  resolved to nothing → flat PageRank. Source roots discovered from `__init__.py` dirs; src-prefixed
  candidates appended last (flat layout byte-for-byte unchanged). +5 tests, mutation-proven.
- **F5 · Commit-scoped lane-check + file-hash stamping** (`kata-orchestrate` 0.4.x, `kata-evaluate` 0.2.0,
  `footprint.py`) — the drift check prescribed no git method; a task forked from an earlier integration
  head false-flagged foreign files. New `changed_in_task` (three-dot merge-base diff) + `file_content_hashes`
  (Freeze/Float M4 evidence substrate). +4 tests incl. a real-git fork scenario, mutation-proven.
- **F3 · Structured PROGRESS heartbeat + liveness monitor** (`kata-orchestrate`, `protocol/board.md`) —
  workers stamped only CLAIM/DONE (Kenjiri: 37 min dark). Mandated per-owned-module PROGRESS
  (`modulesDone/modulesOwned`, also the M4 slack-timing signal) + a liveness monitor routing stale workers
  through the existing escalation path (nudge → escalate → human-gated re-dispatch; **no blind kill**). New
  top-level `livenessDeadline` config (keeps orchestrate sprint-blind, BC2).
- **F6 + Lever 2 · Tool-agnostic security-gate posture** (`kata-evaluate` 0.2.0, `kata-orchestrate`,
  `kata-report` 0.1.1, `kata-bootstrap` 0.1.3, `protocol/config.md`) — the gate said "security scan clean"
  (fix-until-zero) and graded a raw Snyk count, but Snyk can't converge on custom sanitizers and a run may
  have no scanner. New `securityScan: required|when-available|off` (absent ⇒ `when-available`, BC);
  documented-acceptance terminal state graded for **soundness**, not raw count. Debug-mode/IaC Snyk wirings
  untouched.
- **F4 · Greenfield src-layout seeding precondition** (`kata-orchestrate`, `kata-lang-profile` 0.1.1) —
  `uv init --bare` wrote no `[build-system]`; workers added `sys.path` shims. Generic "own package
  importable before wave-1" precondition in the core, Python specifics (build-system + `packages.find
  where=src` + import verify) in the language overlay.

_Also: softened the operator's global `~/.claude/CLAUDE.md` Snyk mandate to conditional + toolchain-aware
(Lever 1, external — the actual cause of the Kenjiri mid-run Snyk derailment). Freeze/Float doctrine
(M1–M4) deferred to Milestone 2._

## [0.1.0] — 2026-06-30

**First public release of the KataHarness agent harness — the single-model Claude core.**

47 skills · 2141 pytest · validate 47/0 · Snyk medium+ 0 · Apache-2.0.

### Core spine

- **10 spine skills** built and field-proven: `kata-grill`, `kata-context`, `kata-design-doc`,
  `kata-plan`, `kata-orchestrate`, `kata-board`, `kata-worktree`, `kata-tdd`, `kata-evaluate`,
  `kata-handoff`. Proof: KataHarness built itself via the loop (dogfood n=1).
- **Frontmatter schema v2** (D26/D31): `name`, `description`, `license`, `version`, `category`,
  `status`, `agnostic`, `cost-weight`, `allowed-tools`, `compatibility`, `source`, `supersedes`,
  `aliases`, `tags`. Model field (`model:`) **FORBIDDEN** in core skills — dispatch-resolved at
  runtime, never pinned in a skill body.
- **`tools/validate_skills.py`** enforcing the schema, cost-weight, license, no-write evaluator
  invariant (`kata-evaluate`/`kata-research` omit Write/Edit), model guard (A1), and
  `REQUIRED_PROTOCOL` registry.

### Modes and tiers (Spec A — A1–A4, D1–D56)

- **Tier families:** `kata-grill` / `kata-review` / `kata-plan` each in three tiers
  (essential / standard / advanced); `kata-diagnose` in two (light / full). RUBRIC per family;
  structural invariants never tiered (D33).
- **`kata-bootstrap`** — run-shape router (individual / batch-bakeoff / version-up / advanced),
  presets on top of the mode axis, cost preview, `kata.config` writer; re-entrant (cold-start vs
  reconfigure). **`kata-readiness`** — harness-health + target-readiness + re-entrant config
  detection (bootstrap-invoked).
- **`kata-graph`** — tree-sitter-floor, feature-agnostic `kata.graph.json` contract, ~3k-token
  feature-seeded digest, pluggable backend. Protocol: `protocol/graph.md`.
- **`kata-orchestrate`** — rolling DAG-frontier dispatch, async park/drain/hard-wait, structured
  escalation payload (`protocol/escalation.md`), fail-closed config load-guard, IaC region,
  multi-model dispatch, Debug Mode seams.
- **Version-up wiring** — grill Phase 0 ingest, footprint-scoped disjoint ownership,
  full-suite-green regression contract (A4).

### Sprint-cadence (D78–D85)

- **`kata-sprint`** (G1–G4 boundary) — sprint-scoped plan freeze, per-sprint immutable
  `PLAN-s<n>`, carry-outs to next sprint.
- **`kata-plan` roadmap layer** (`ROADMAP.md` tier) — sprint-boundary-amendable roadmap above
  the immutable per-sprint plan.
- **`kata-report` v1** — post-loop build-log synthesis.
- Extended: `config.md`, `state.md`, `handoff.md`, `escalation.md`; `kata-selfhandoff`;
  `kata-readiness`; `kata-handoff` all wired for sprint shape. Orchestrate stays sprint-blind (BC).

### Loop-cognition (D60–D77)

- **β LEARN feed** — `kata-improve` emit-only sub-mode (E6 seam): mines DECISIONS/LESSONS/
  GRILL-LEDGERs/REVIEWs into Karpathy-LLM-Wiki synthesis pages (`produced-by: loop`).
  Zero CONSULT; redaction-gated; no-op without `engram.learnFeed.dir`. Protocol: `protocol/engram.md`.
- **Priming-and-Grill (D71/D73):** grill-skip rung (`tiers["kata-grill"]="skip"`); `kata-defer`
  (new module skill — `DEFERRED.md` parking + `ASSUMPTIONS.md` grill-skip log).
- **`kata-research`** — escalation-routed in-loop research subagent (`research-needed` kind);
  fresh-context no-write; grounding gate in `kata-evaluate` + `kata-review` RUBRIC (D33, never
  bypassed); returns `{claim, source, confidence, grounds-to-plan?}`.
- **`kata-orient`** — read-only three-tier launch orientation (stable → context → volatile),
  vertical rollup + `kata-graph` lateral adjacency pointers, task-type-aware, smart-questioning
  routed (answer-inline / research-needed / human-required). `kata-handoff` orientation tie-in.
- **`kata-promote`** — two-stage candidate→human promotion gate (`scope:agent` →
  grounding gate → `AskUserQuestion`); `engram.autonomy` AND-gate (default always-human).
  STANDARDS §1.3 discriminators; candidate lifecycle in `protocol/state.md`.

### User-friendliness (WS-3/4/5)

- **`protocol/persona.md`** — KataHarness voice and register.
- **`protocol/narration.md`** — in-loop narration map; stage names are not exposed; actions
  described in human terms.
- **Reflective goal-mirror intake** in `kata-initiate`; one-dial mode surface in `kata-bootstrap`.
- **Two-tier closeout** (`kata-closeout` + `kata-report`): concise CLI/GUI summary + self-contained
  branded HTML report (`.kata/closeout.html`); goal-anchored by-aspect; what-changed-why leads.
- **Backout** offered at the human gate (`.kata/RESULT.json.baselineSha`, `git reset --hard`,
  human-gated, never autonomous).
- **`kata-slop-check`** — standalone optional module (`kata/module/slop`); general checks G1–G6 +
  MIT-attributed checks; fresh-context no-write; default-FAIL (`SLOP-DETECTED ⇒ NEEDS_WORK`).

### Install / update / overlay / fork (D104, D125–D129)

- **`install.sh`** (`curl|sh`) + **`install.ps1`** (`irm|iex`) + **`uninstall.*`** — wrapping the
  `kata_install.py` engine; idempotent; `KATA_SRC` offline override.
- **`kata_install.py`** headless flags: `--yes`/`--non-interactive`, `--answers-json`, `--json`,
  `--uninstall`, `--target-dir`; semantic exit codes; non-TTY auto-skip.
- **`tools/kata_overlay.py`** — overlay store (`<home>/.kata-overlay/overlay.json`) + frontmatter
  composer (M4); `.kata-overlay-materialized` marker; fail-soft on missing base.
- **`tools/kata_supersede.py`** — resolve/validate shadows; fork > overlay > pristine precedence;
  validate-STOPs-before-materialize; factory-reset un-shadows.
- **`kata-improve` local-adaptation mode** — overlay vs fork by edit-category;
  `improve.allowUpstreamEdit` rail.
- **`tools/kata_version.py`** — `.kata-version` stamp + `.kata-manifest.json` content-hash;
  `is_pristine`/`suite_semver`; `update.sh`/`update.ps1` bootstraps with `--update`,
  `--factory-reset`, `--dry-run`, `--ref`.
- **`kata-onboard`** (v0.2.0) — optional human-gated router stanza into target project's
  `AGENTS.md` (via `tools/kata_router.py`; `<!-- kata:begin -->`/`<!-- kata:end -->` idempotent
  marked block).

### Multi-model dispatch (D105–D108, D121)

- **`tools/kata_roles.py`** — relative model tokens (`anchor` / `anchor-1` / `anchor-2`); model
  resolved at dispatch as a differential off the operator's session model; never pinned in skill.
- **`tools/kata_dispatch.py`** — files+CLI dispatch (concurrent background subprocesses);
  `kiro_command` + `codex_command`; `_brief_prompt` capture-model branch; host fallback.
- **5 role groups:** coder · validator · researcher · orchestrator · evaluator
  (read-only validator/researcher routing live; coder-routing + evaluator-thresholds deferred per D108).
- **Codex live-proven (D121):** `--skip-git-repo-check`, `stdin=DEVNULL` fixes; confirm probe
  PASSES on real `codex exec` (`confirmedPlatforms:["codex"]`).

### Model-tiering (D131)

- **`tools/kata_models.py`** — pure-stdlib resolver: `resolve`/`step_down`/`fallback_chain`/
  `family_of`; family ladders DATA registry; `ID_MAP`; `SKILL_WORK_CLASS` (47 skills, 3 work
  classes: critical / coding / economy).
- **`kata_roles.py`** relative tokens wired to `step_down`; `_normalize_anchor` maps full ids.
- **`kata-orchestrate`** dispatch-time model-selection prose + R2 ≤2-then-omit fallback.
- **`kata-bootstrap`/`kata-initiate`** anchor-write of the `models` block.
- A1 model guard (`check_model_in_skill_frontmatter`) in `tools/validate_skills.py`.
- `protocol/config.md` `models` schema. Contract: BC absent config ⇒ inherit by omission.

### Debug Mode (D103, D113–D117)

- **`kata-comprehend`** (P1) — builds executable `function_model` oracle via AST-safe `evaluate_spec`;
  `tools/function_model.py` (`_safe_eval` AST-allowlist, no `eval`/`exec`; `**` removed categorically).
- **`kata-deviate`** (P2a) + **`tools/deviation.py`** — 7-step deviation pipeline (self-consistency
  ≥2/3, corroboration HARD gate, confidence+routing, force-LOW; corroborator objectivity code-enforced).
- **`kata-characterize`** (P2b) + **`tools/drift_gate.py`** — blast-radius characterization; behavioral
  drift gate (green→RED=BLOCK, vanished-baseline-green=BLOCK); AEL orchestrator-owned.
- **`kata-lang-profile`** + 6 language profiles + config specialist (P3 LD10) — injected at dispatch
  by footprint file extensions; prose-only, no new Python.
- **`kata-debrief`** (P3 LD12) + **`tools/debug_report.py`** — confidence map, deviation→fix→
  pinning-test, Snyk before/after; honesty pinned at the engine (behavioral-only + heuristic
  confidence + n=0-live labeled).
- `kata-orchestrate` Debug Mode seams (P1/P2/P3) gated on `kata/module/debug`.
- **`kata-onboard`** (P3 LD13) — first-run/convert-to-loop.
- **`kata-closeout`** Step 3b — debug-gated; offers `kata-debrief`.

### Second-brain Recall (D120)

- **`tools/recall.py`** — pure engine: shape-validated open-vocabulary contract
  (`source`/`backend`/`produced_by` adapter-supplied); files-only adapter (reads
  LESSONS/DECISIONS/prior-INTENT/understand-map/validation-misses); `select_records` (hard
  token-overlap>0 predicate; no embeddings/RAG); always-surface open recurrences; no write path.
- **`protocol/recall.md`** — Recall contract. `kata-initiate` v0.2.0 Phase-1b recall-brief.
- CONSULT decider + write-half deferred (gated on engram maturity, D9/D56).

### IaC specialists (D110, D119)

- **`kata-iac-terraform`** + **`kata-iac-cloudformation`** (Tier 1 + Tier 2).
- **`tools/iac_detect.py`** — classifier + plan/change-set destructive-parsers, fail-closed;
  stateful-set (EFS/SQS/SNS/Kinesis/OpenSearch/Neptune/DocDB/KMS/Secrets/MSK/FSx et al.).
- **Tier 1:** author/review/gate; validate/cfn-lint → `snyk_iac_scan` (default-FAIL; fail-closed
  if unwired) → 8-smell lens → destructive analysis → `.kata/iac.json` → pass/fail/escalate.
- **Tier 2 (preview/approve):** `tools/iac_apply.py` — `plan_hash` (TF binary / CFN full
  describe-change-set), `approval_verdict` (plan-hash-bound), `capability_gate_verdict`
  (self-binding: grant.hash + authorized-set + typed token); `run_apply` = NotImplementedError
  (creds-gated, never auto-applies). `protocol/iac-safety.md` §9.

### Benchmark engine (D123–D124)

- **`kata-loop-benchmark`** + **`kata-benchmark-report`** skills.
- **`tools/benchmark.py`** — 2-axis scorecard (Q: floor-gated dual-gate F2P/P2P + mutation;
  C: tokens/$/wall-clock/etc; host-dependent fields nullable); floor-gated composite (Pareto +
  scalar, efficiency only among floor-passers).
- **`tools/benchmark_def.py`** — content-pinned Benchmark Definition + `repeat_from` + delta mode;
  `delta_identity` (same benchmark_id → `sameDefinition:true`).
- **`tools/benchmark_control.py`** — immutable reference clone (`<base>-katabenchmark<N>`).
- **`tools/usage_meter.py`** — net-new metering (tokens/$/wall-clock).
- Module: `kata/module/benchmark` (off-by-default; not in bootstrap).

### `kata-validate` always-available validation mini-loop (D125)

- `skills/evaluate/kata-validate` — programmatically-callable `validate(payload, target, profile)
  -> Report{passed, findings[]}`; NO freeze/INTENT/`kata.config` required; dual-target (content
  OR agent output); payload-as-data isolation; 4 deterministic-first legs (grounding / review /
  slop / conformance); bounded ≤2 passes; default-FAIL `compute_passed`.
- `tools/validation_report.py` — findings schema, SARIF severity, `render_table`,
  `tripwire_corpus`/`assert_tripwire_flagged`; no exec sink.

### Validation-miss manifest + recurrence hardening (D101, D112, D114, D118)

- **`tools/validation_misses.py`** — schema/validate/append (append-only, CWE-23, non-fatal)/
  read/count_by_class; `passive recurrences`. Protocol: `protocol/validation-misses.md`.
- **`tools/recurrence_detect.py`** — severity-aware threshold (3× distinct runs or 2× for
  BLOCKERs); distinct-run via `run_id`; `detect_from_paths`; `.planning/recurrence-handled.jsonl`
  sidecar. `kata-improve` v0.2.0 auto-draft sub-mode.
- **`protocol/exec-safety.md`** — structured-argv-only contract; sink registry of every
  `subprocess` in `tools/`. **`tools/tests/test_exec_safety.py`** — AST-based CI guard (fails
  on new `shell=True` outside the operator-domain allowlist).

### v0.1 cluster hardening (2026-06-30)

These five items closed the v0.1 gate:

1. **Sprint-cadence D15/A5 fresh-context `kata-review` SHIP** — clears the last pending gate on
   the sprint-cadence milestone.
2. **Wiring-completeness interim pin** — prose pointers in `kata-evaluate` item 9 and `kata-review`
   6(b) marking the full produced-vs-consumed sweep as a post-v0.1 ORCHESTRATOR INTEGRATION-GATE
   step (the full build is scheduled for v0.1.x).
3. **Guard-consistency repo-wide** — `_safe_path` guards unified to `ValueError` across
   `mutation_run`, `grounding_gate`, `escalation`, and `intent_scaffold`.
4. **CWE-23 `.snyk` record** — standing policy entry for the 17-LOW operator-supplies-own-path
   class in `kata_install.py`; below the medium+ gate; accepted as a known item.
5. **Benchmark machinery n=0→n=1 live** — the clone→dual-gate→score→scorecard chain ran clean on a
   cloned **synthetic** control with real `uv run pytest` subprocesses (`0d3e729`). The **real
   operator-supplied control fixture (benchmark-D5) remains DEFERRED** — the engine is not yet proven on a
   real control repo (CONTEXT.md honesty-pin; do not claim otherwise).

**Versioning policy change:** STANDARDS §3 flipped from the pre-release hold (all skills held at
`0.1.0`, 2026-06-08 policy) to **bump-on-modify** (mandatory for all skill modifications going
forward).

### Explicitly deferred to v0.1.x

Items #6–#13 and the wiring-completeness full build. See `BACKLOG.md` "Explicitly deferred to
v0.1.x" section for rationale per item.

---

[0.1.0]: https://github.com/taurran/KataHarness/releases/tag/v0.1.0
