# FULL HEALTH REVIEW — KataHarness — 2026-07-12 (Fable 5, fresh-context)

> Executed per `.planning/REVIEW-PROCEDURE.md`. Reviewer: Fable 5, fresh context, OUTSIDE the
> kata loop (the loop is the subject under audit — D33 no-self-certification applied to the
> harness itself). Ground truth at review start: local `master` @ `f40a973`, tag `v0.3.0`.

## Phase 0 — Independent baseline (REPRODUCED)

| Gate | Claimed (v0.3.0 tag) | Reproduced 2026-07-12 | Verdict |
|---|---|---|---|
| pytest `-m "not integration"` | 3120 pass / 3 skip | **3120 pass / 3 skip / 2 deselected** | MATCH |
| validate_skills | 48/0/0 | **48 skills, 0 err, 0 warn** | MATCH |
| Snyk medium+ | 0 | deferred to fix phase (scan runs on modified code) | PENDING |

Ground-truth notes:
- **G-1:** local `master` is 1 commit ahead of `origin/master` (`f40a973`, README docs pass) —
  committed STRAIGHT to master and unpushed; violates the project's own standing order
  (branch→PR→merge, never straight to master). GitHub README is therefore one pass stale.
- **G-2:** untracked file `.planning/config.json`.

## Findings ledger (live — appended as the review proceeds)

| ID | Sev | Class | Where | Evidence | Proposed fix |
|---|---|---|---|---|---|
| F-1 | MED | doc-drift | `AGENTS.md` §Status | Says "v0.2.0 (Freeze/Float M1+M4 shipped)"; repo is v0.3.0 | Update status para |
| F-2 | MED | process | `master` vs `origin/master` | Unpushed direct-to-master docs commit `f40a973`; untracked `.planning/config.json` | Operator: push or re-route via PR; classify/commit or ignore the config |
| F-3 | HIGH | facade | `.planning/STEERING.md` | Claims "the harness reads this on a cadence" + `AGENT_STOP` kill-switch; grep over skills/tools/protocol/adapters finds ZERO implementation (only a filename mention in STANDARDS.md §102) | Either wire a steering-check into the orchestrate boundary cadence or rewrite STEERING.md to say it is a manual convention, not a harness behavior |
| F-4 | MED | doc-drift | `docs/DESIGN.md` | Charter drift: references `cognition/` family, `kata-tasklist` in loop table, un-tiered skill names, "Built (15, all 0.1.0)" block — all stale vs 48-skill reality; file self-labels "draft v0" but README cites it as the charter | Refresh charter or stamp it as historical with a pointer to current docs |

| F-5 | HIGH | doc-honesty | `README.md` benchmark box (~189–194) | Claims ranking on "real fail-to-pass/pass-to-pass evidence"; CHANGELOG v0.1.0 item 5 + CONTEXT.md carry the pin "n=0 LIVE — synthetic control only, DO NOT CLAIM OTHERWISE"; README nowhere says "synthetic". The one place the public surface is weaker than an internal honesty-pin | Add the synthetic-control-only caveat line to the README benchmark box |
| F-6 | MED | doc-honesty | `README.md` adaptive box (~146–148) | "perfect precision — every one of 13 noise signals correctly ignored" — SMOKE-MODELED's own Honest frame says this rests on an n=1 overturn observation ("the model's weakest assumption") and models a pre-fix regime already designed away; README compresses to the word "modeled" | Carry the n=1-assumption qualifier into the README sentence |
| F-7 | MED | doc-drift | `README.md:72` | "Zero-dependency install. A pure-stdlib Python engine" — installer IS stdlib-pure, but `kata_restore.py:34` + `intent_scaffold.py:28` import yaml unguarded; graph/contract_gate need tree-sitter; dash/statusline need rich (all via tools/pyproject.toml + uv) | Reword: "pure-stdlib installer; engine deps resolved by uv" |
| F-8 | LOW | doc-honesty | `README.md` green-path cost claim | "<1% green-run overhead" thesis is flagged AT-RISK in CHANGELOG v0.2.0; README's "costs ~nothing" doesn't surface the qualifier | Optional one-word hedge |

### Claims-verification pass (agent, full README+CHANGELOG, 3-leg audit)
~19 load-bearing claims audited (engine/wiring/test legs): **0 FALSE, 0 UNSUBSTANTIATED.**
Verified real and wired, among others: inline ladder (trigger→judge structural in code),
44/57+25/31 checkpoint numbers (CALIBRATION-FINDINGS C-2 + LIVE-PROOF), −23/−44/−29 A/B
(LIVE-PROOF with caveats verbatim), −86% premium (SMOKE-MODELED artifact + modeled label),
refs/kata/trail + PreCompact/SessionStart hooks registered in the shipped settings snippet,
48-skill count exact (45+3), all 6 slash commands exist and install, all README lifecycle
flags exist in update.sh/ps1, IaC run_apply structurally unreachable, evaluator no-write +
no-model-IDs validator-enforced. Deferral labels (R6, L2 OFF, IaC apply, multi-arm next,
codex/kiro partial, seeded-fixtures Debug Mode) all present in README where claimed.

### Engine quality / fail-open pass (agent, all 51 tools/*.py + adapters, gate modules read in full)
Verdict: disciplined B+ engine; gate SPINE is genuinely fail-closed (contract_gate exemplary);
the holes are at gate INPUTS. Ledger (Q-ids):

| ID | Sev | Class | Where | Evidence | Fix |
|---|---|---|---|---|---|
| Q-1 | HIGH | fail-open | `drift_gate.py:130-151,221-316` | `parse_test_outcomes` → `{}` on unparseable output; `drift_verdict(before={},…)` returns PASS "all baseline-green stayed green" having certified nothing | Raise/BLOCK `empty-baseline` when before=={} and AEL empty (D136) |
| Q-2 | MED | silent-default | `grounding_gate.py:82` | `.get("groundsToPlan")=="NO"` — absent/lowercase/typo silently skips ESCALATE; enum enforced only at build_finding, not at verdict | Validate ∈{YES,NO,PARTIAL}, raise otherwise |
| Q-3 | MED | fail-open | `grounding_gate.py:148-151` | empty verdicts list ⇒ `allGrounded:true` written to grounding.json (fold-authorization signal) | Raise on empty, or emit vacuous:true |
| Q-4 | MED | resource | `mutation_run.py:55`, `run_result.py:118-125`, `mutation_check.py:97-102` | The three gate runners have NO subprocess timeout — a hung test deadlocks gate/mutation/benchmark forever (dispatch/install DID get timeouts) | timeout= (600s) + TimeoutExpired ⇒ gate red |
| Q-5 | MED | duplication-drift | `kata_supersede.py:196-199` | `except ValueError: return {}` — traversal swallowed, forks silently not honored; comment says "fail-closed", behavior is permissive; only diverged member of the 16-copy _safe_path family | Propagate like the rest |
| Q-6 | MED | silent-default | `deviation.py:344-347` | `refuted`/`sparse_signal` default False on absence ⇒ auto-fix-eligible without the human route | Hard-require keys per docstring contract |
| Q-7 | MED | fail-open | `validate_skills.py:476-499` | main() exits 0 on ZERO skills discovered ("0 skills checked — 0 errors", green) — validator self-certifies over an empty set | `if not skills: return 1` |
| Q-8 | MED | lying-error | `benchmark.py:877-886` | `::`-less test-ID silently scored as test FAILURE — scorecard says "arm failed F2P" when truth is "criteria malformed" | Raise ValueError (authoring error) |
| Q-9 | LOW | silent-default | `benchmark.py:394` | present-but-truncated mutation.json missing `allNonVacuous` gets full 1.0 multiplier | treat as vacuous or raise |
| Q-10 | LOW | silent-default | `run_result.py:30-41`+`gate_emit.py:196-206` | non-pytest gate output parses to 0/0 with success shape; gate_emit CLI exits 0 regardless of exitCode/withinFootprint | parsedCounts flag + non-zero exit |
| Q-11 | LOW | doc-lie | `intent_scaffold.py:215-217` | stale docstring claims gate_emit raises SystemExit; unification to ValueError is real, docstring lies | fix docstring |
| Q-12 | LOW | duplication | 16 hand-copied `.. `-guards | drift started: supersede swallow (Q-5), `recall._guard_path` missing `.resolve()` | shared helper or validator identity check |
| Q-13 | LOW | silent-default | `kata_dispatch.py:253-259` | researcher normalize accepts claim with source/confidence None; escalation.build_finding would hard-fail the same payload | route through build_finding validation |
| Q-14 | LOW | silent-default | `kata_restore.py:758-761` | orphan-trail board read `except Exception: ""` — degraded flag NOT set for this loss | append board-unreadable to degraded_reasons |
| Q-15 | LOW | lying-error | `iac_apply.py:402-417,707-711` | corrupt approval file reported as "not approved" (fail-closed but diagnostic lies) | distinguish CORRUPT vs absent |
| Q-16 | LOW | resource | git subprocess sites in contract_gate/footprint/restore/telemetry/trail | no timeouts; stale index.lock could stall final gate | 60s timeout on git helpers |
| Q-17 | LOW | fail-open | `adapters/claude/hooks/kata-precompact.py:115-118` | top-level `except: pass` (documented fail-soft) but failed board snapshot leaves ZERO trace | one stderr line, keep exit 0 |
| Q-18 | LOW | silent-default | `validation_misses.py:302-331`, `recurrence_detect.py:358-371` | ledger readers silently skip corrupt lines — erases the very recurrence signal the ledger preserves | surface skippedLines count |

Vestigial sweep: CLEAN (no invalidated.json residue, no replay-spine remnants, no dead schema branches).

### Engine stub/facade sweep (agent — all 51 tools modules, AST hollow-body scan, wiring matrix, 549 targeted tests run)
**No facades found in the engine.** All special targets VERIFIED-REAL (kata_adaptive state
machine incl. byte-pinned recount that raises on corruption; iac_apply plan_hash/approval/
capability gates; usage_meter with anti-gaming guards; kata_supersede ≠ kata_restore — name
collision only, different domains; dash/web = real, tested, localhost-only). Zero dead modules.
Hollow bodies: only the two documented NotImplementedError seams + 2 deliberate silencers.
`kata_preflight._default_snyk_check → True` is NOT a facade (fail-closed guard + opt-out tested).

| ID | Sev | Class | Where | Evidence | Fix |
|---|---|---|---|---|---|
| S-1 | MED | doc-drift (inverse facade) | README/CHANGELOG vs kata_dash*/kata_web | Whole shipped+tested dashboard/web-viewer surface (~1,500 LOC, own spec, backout tags) absent from README features and CHANGELOG; documented only in CONTEXT.md/STATE/adapters README | Add README bullet + CHANGELOG line |
| S-2 | MED | doc-drift | `CLAUDE.md:16` vs `kata_models.py:67-69,217-218` | CLAUDE.md: "other families keep the generic one-rung default" — but OPENAI/GEMINI/GENERIC ladders are `[]` (code admits "currently unreachable"); non-Anthropic families get NO tier-down at all | Reword CLAUDE.md honestly |
| S-3 | LOW | doc-drift | `kata_install.py:1418` | Stale "(no-op stub in Phase A…)" comment over fully-implemented `_materialize_pass` | Fix comment |
| S-4 | LOW | doc-drift | `kata_dash_demo.py:53` | Stale "no kata_board" section comment; helper delegates TO kata_board | Fix comment |
| S-5 | LOW | loose-end | `usage_meter.py:316-336` | Hard-coded 2026-06 USD rate table silently stales benchmark cost axis (override + None-policy mitigate) | Emit table date into usage.json |
| S-6 | LOW | loose-end | `kata_web.py:569-571` | `/api/view` catches Exception → renders as "waiting for a run"; error only in hidden JSON key | Surface error in page UI |

### Determinism pass (agent — 14 findings + 10 doctrine inputs; clean modules verified incl. kata_risk/kata_adaptive/kata_gauge/contract_edges/benchmark_control)

| ID | Sev | Where | Vector | Failure scenario | Fix |
|---|---|---|---|---|---|
| DET-01 | HIGH | `graph_gen.py:499-501,551,596,603,644,662,419-421` | unsorted rglob + set iteration + first-candidate ref-target selection | Two runs on identical tree ⇒ different node/edge order AND (multi-defined symbols) different ref-edge targets ⇒ different topology ⇒ different PageRank ⇒ different prioritization | sort discovery/sets/candidates; sort outputs pre-emit |
| DET-02 | HIGH | `contract_gate.py:135-141`, `kata_restore.py:482-487` | single-pathspec `git log` without `-c log.follow=false` | operator `log.follow=true` + ever-renamed PLAN ⇒ earlier fork point ⇒ prior-run trailers ingested ⇒ the exact coverage corruption M1-L9/R8 prevents; per-operator verdicts differ | pin log.follow=false (shared git helper) |
| DET-03 | HIGH | `contract_gate.py:159-182`, `kata_telemetry.py:276` | no `log.showSignature=false` pin | signed commits ⇒ gpg lines shift commit_index ⇒ temporal invalidation comparison silently wrong (contract_gate) / TelemetryError (telemetry) | pin showSignature=false everywhere stdout parsed |
| DET-04 | HIGH | `footprint.py:211-218` (`changed_in_task` lane check) | `--no-renames` pinned but `core.quotepath` NOT | non-ASCII path ⇒ quoted octal form never matches footprint prefix ⇒ FALSE lane-drift trip on default config; opposite outcomes per operator config | pin quotepath=off (reuse telemetry helper) |
| DET-05 | MED | `footprint.py:153-160` (`changed_since` → footprint.json) | no --no-renames/quotepath | rename detection config changes changed-set; `git mv foreign.txt owned/` hides foreign deletion | mirror changed_in_task pins |
| DET-06 | MED | `footprint.py:267-273` diff_stat | `COLUMNS` env drives --stat width | byte-different diffstat in durable manifest per terminal width | `--stat=200` or --numstat |
| DET-07 | MED | `drift_gate.py:169-186,249-306` | set-union iteration order → blocking[]/reason order | byte-different drift artifacts per PYTHONHASHSEED (sibling characterization verdict SORTS — inconsistent) | sorted(all_ids); sort blocking |
| DET-08 | MED | `kata_telemetry.py:1281` build_ledger_row | json.dumps without sort_keys on pass-through maps | committed calibration ledger rows byte-differ per producer dict order (contract_gate uses sort_keys — inconsistent) | sort_keys=True (one line) |
| DET-09 | MED | `mutation_check.py:91-103`, `mutation_run.py:53-56` (shell=True) | inherited env (PYTEST_ADDOPTS, plugin autoload) + platform shell semantics feed gate/score booleans | same clone scores F2P/P2P differently across hosts | sanitized env allowlist + argv list |
| DET-10 | LOW | `kata_telemetry.py:428` evidence_digest | bare "\n".join (no netstring) — the in-repo D98 lesson applied twice elsewhere but not here | newline-in-filename collision class | netstring on next digest rev |
| DET-11 | LOW | `benchmark.py:772-774,588-592` | float-tie rank by caller insertion order | arm listing order decides rank-1 on exact tie | explicit tie-break key |
| DET-12 | LOW | `drift_gate.py:92-111` | temp-path scrub misses /var/folders + path-separator in test ids | cross-platform AEL false-BLOCK | add pattern; normalize separators |
| DET-13 | LOW | `benchmark_def.py:444-445` | uuid4+now identity later compared | rebuild without passing id ⇒ sameDefinition structurally False (documented-not-enforced persist-reuse) | content-address or document in write_def |
| DET-14 | LOW | graph_gen/benchmark/drift/debug_report timestamps | wall-clock in durable artifacts (nothing hashes them — verified) | diff noise on unchanged regenerate | sidecar if ever hashed whole |

Doctrine inputs captured for the Determinism Doctrine (see DETERMINISM-DOCTRINE.md).

### Skills↔engine wiring audit (agent — 259 module.symbol references AST-verified, config-key audit both directions, slash commands)
**Zero HIGH in either orphan class. Not one of 259 prose-cited engine surfaces is phantom;
every quoted signature accurate; zero undocumented config reads; zero silently-dead documented
keys (4 reserved keys are self-labeled "not yet consumed").** The verify-before-reuse guard
demonstrably works.

| ID | Sev | Class | Where | Evidence | Fix |
|---|---|---|---|---|---|
| W-1 | MED | built-unwired | `benchmark_control.py:161 detect_drift` / `:238 prune` vs orchestrate benchmark setup | content_hash pinned expressly for drift detection but NO prose ever instructs calling detect_drift (even on repeat_from); immutable-control guarantee recorded, never enforced | orchestrate repeat_from branch: call detect_drift; drift ⇒ STOP+escalate |
| W-2 | LOW | built-unwired | `kata_board.py:101 append_progress` vs board.md/orchestrate PROGRESS mandate | heartbeat mandated but the purpose-built wrapper never named; format re-derived in prose | name append_progress in the worker-brief bullet |
| W-3 | LOW | built-unwired | `footprint.file_content_hashes`, `usage_meter.load_usage` | public surfaces, tests-only consumers | wire/privatize/mark |
| W-4 | LOW | stale-cite | kata-initiate ×4 → `kata_settings.py:109` (actual :121); orchestrate:990 → dispatch:176 (actual :177) | line-cite drift only, symbols real | refresh cites |
| W-5 | LOW | naming | orchestrate:1221 `footprint.codeBearing` | manifest key rendered as if a Python symbol (`code_bearing`) | rephrase |
| W-6 | LOW | invocation-drift | kata-validate `-m tools.kata_banner` vs kata-loop file-path form | -m form fragile (no __init__.py; CWD-dependent) | standardize file-path form |
| W-7 | LOW | over-promise | commands/kata-validate.md arg-hint "scope to one skill" | validator parses only --write; always scans all | soften hint or add --only |

## FIXED THIS SESSION (branch `review/fable5-health`; gauntlet after fixes: pytest 3152/3 · validator 48/0/0 · Snyk medium+ 0)

- **Prime Directives shipped + wired** (the operator's directive): `protocol/prime-directives.md`
  (PD-1 never-silently-defer/stub/skip; PD-2 absolute truthfulness — stub-reported-as-built IS
  DRIFT), injected via orientation STABLE tier + AGENTS.md spine #7 + kata-orient 0.3.0 +
  REQUIRED_PROTOCOL registration + 5 guard tests.
- **Determinism Doctrine adopted**: `docs/DETERMINISM-DOCTRINE.md` (ten laws + judgment boundary +
  enforcement; straggler debt registry cites DET-ids).
- F-1 AGENTS.md status v0.2.0→v0.3.0 · F-3 STEERING.md rewritten honestly (facade removed; real
  wiring = backlog #1) · F-4 DESIGN.md historical-charter stamp · F-5 README synthetic-control
  caveat · F-6 README n=1-precision qualifier · F-7 README stdlib-installer reword · S-1 README
  dashboard/web-viewer section added · S-2 CLAUDE.md non-Anthropic-ladder honesty · S-3/S-4/Q-11
  stale comments/docstring fixed.
- Q-1 drift_gate empty-baseline ⇒ BLOCK (+5 tests, mutation-proven) · DET-07 drift output ordering
  · Q-5 kata_supersede traversal now propagates (+2 tests) · Q-7 validator refuses to certify an
  empty tree (+3 tests) · Q-4 600s timeouts on all three gate runners (+6 tests).
- DET-01 graph_gen fully order-pinned incl. lexicographic ref-target selection (+2 tests) ·
  DET-02/03/04/05 git pins (log.follow/showSignature/quotepath/no-renames) across contract_gate,
  kata_restore, footprint, kata_telemetry._run_git (+7 tests incl. real-git quotepath proofs) ·
  DET-08 ledger rows sort_keys (+1 test, reader-safety verified).
- W-1 detect_drift now MANDATED in orchestrate repeat_from (drift ⇒ STOP+escalate) · W-2
  append_progress named in the worker brief · W-4/W-5 stale cites + codeBearing phrasing ·
  kata-orchestrate 0.11.1, kata-initiate 0.2.2, README index regenerated.
- Everything NOT fixed is a named deferral: BACKLOG "2026-07-12 health-review follow-ups" #1–8.

## Round 2 (operator follow-up: "did we really check everything?") — mechanical checks

| Check | Result | Notes |
|---|---|---|
| Coverage (pytest-cov one-off) | **TOTAL 97%** | Weak: kata_dash 60 / kata_dash_demo 64 / function_model 76 / gate_emit 76 / kata_web 77 / kata_trail 80 / kata_install 81 / recall 82 — mostly render/CLI mains |
| Lint (ruff one-off) | **34 findings, ALL in tests/** — production code ruff-clean | 18 unused-import, 6 `l` names, 4 unused vars; cosmetic |
| Type check | **NOT CONFIGURED** (no mypy/pyright) | Type hints present but unverified — finding M-1 below |
| Lint config | **NOT CONFIGURED** (no ruff in gauntlet) | finding M-1 |
| Coverage in gauntlet | **NOT CONFIGURED** | finding M-1 |
| Snyk SCA (dependency scan) | **DEFERRED** — resolver cannot read the uv-native manifest (3 attempts incl. requirements export) | Deferred-security note per operator global policy. Mitigation: dependency surface is 12 pinned mainstream packages (pyyaml/rich/tree-sitter/pytest chain) |

| ID | Sev | Class | Finding | Proposed fix |
|---|---|---|---|---|
| M-1 | MED | loose-end | The gauntlet (pytest+validator+Snyk SAST) has NO lint, NO type-check, NO coverage floor, NO dependency (SCA) scan — four standard checks absent from "green" | Add ruff (config committed, tests included), mypy or pyright on tools/ (hints already exist), coverage floor (e.g. 90%), and an SCA path that works with uv (uv export → pip-audit, or Snyk once uv-supported) to the standing gauntlet |
| M-2 | LOW | quality | 34 ruff findings in tests/ (unused imports etc.) | one `ruff --fix` pass |

## Round 2 — learning-loop deep e2e validation (agent; every hop EXECUTED live on committed data)

| Hop | Status |
|---|---|
| run → telemetry ledger | CLOSES-LIVE (5 real rows, schema round-trips, medians match calibration doc to the digit) — but "every run" overclaimed: v0.2.1 main build + v0.3.0 build have NO row (row commits are human-gated by design, omission unlabeled) |
| ledger → calibration | BUILT-AWAITING-DATA, exemplarily labeled (τ gated on ≥3 instrumented runs; 2 exist; C-1 finding DID already flow into scorer code via gated commit — the loop's first real closure) |
| recall → kata-initiate | CLOSES-LIVE (live run: payload validates, 10 records, correct ranking/staleness, recurrences correctly empty) |
| misses → recurrence → auto-draft → human gate | CLOSES-LIVE, fired once end-to-end historically (phantom-reuse: 2 distinct BLOCKER runs → T2 draft → proposed marker; handled-aware skip verified live returning 0 now) |
| β LEARN feed | OPEN-BY-DESIGN, labeled in 3 places; zero CONSULT structurally asserted by a validator test |
| lessons → skills | repo route CLOSES-LIVE (human-mediated, dozens of lesson-cited bumps); candidate→PROMOTE route BUILT-NEVER-EXERCISED, was unlabeled |

| ID | Sev | Finding | Status |
|---|---|---|---|
| L-1 | MED | README "telemetry from every run" false vs ledger (2 rowless real runs) | **FIXED** — README reworded (instrumented runs; human-gated rows) |
| L-2 | MED | README present-tense "lessons distil into candidate skills" — leg never executed once | **FIXED** — README states gate built+validated, first candidate pending |
| L-3 | LOW | Proposal-path convention drift (LOCKED convention dir vs where the one real proposal lives) | backlog (health-review follow-ups) |

Verdict: the learning loop is REAL machinery (~85% honest as previously marketed; 100% at
artifact level) — what closes live today is recall read-back, recurrence→draft→human, and
human-mediated findings→code; τ calibration and candidate promotion are honestly gated/pending.

## Round 2 — test-suite quality audit (agent)

High-integrity suite: zero `assert True`, zero swallowed assertions; ~30 assert-free tests all
legitimate must-not-raise proofs; all 5 sampled "mutation-proven" guards VERIFIED killed by
reading their tests (several name the exact mutation); boundary pairs (== tau, == RESERVE)
textbook; real-git/real-subprocess e2e on telemetry/restore/install/contract chains. No
untested module (thinnest: kata_trail 5 deep real-git tests).

| ID | Sev | Finding | Status |
|---|---|---|---|
| T-1 | HIGH | NO CI exists; the 2 `-m integration` tests (the ONLY real-subprocess proof the benchmark F2P leg isn't vacuous) run only on human memory | **integration run EXECUTED 2026-07-12: 2 passed (2.42s)** — green on this branch today; standing fix = pre-tag checklist step / CI when S-07 exception lands → backlog |
| T-2 | MED | 3 symlink-path install tests have plausibly NEVER executed anywhere (Windows box without symlink priv, no CI) — symlink replace/orphan-sweep code proven only by always-skipping tests | operator: one WSL/Linux (or Dev-Mode) suite pass before any release touching kata_install → backlog |
| T-3 | LOW | kata_trail error paths (corrupt ref, read-only .git) untested | backlog |
| T-4 | LOW/INFO | kata_dispatch is pure-injection (real-CLI seam untestable in units — the D124 shape); live-proof battery tests are doc-drift tripwires by design | accepted, documented |

## Round 2 — adapters/hooks/lifecycle-scripts review (agent) + second-opinion non-gate engine review (agent)

**The biggest catch of the whole review is here:** the flagship crash-durability guarantee
silently no-oped in the installed deployment.

| ID | Sev | Where | Finding | Status |
|---|---|---|---|---|
| A-1 | HIGH | `kata-precompact.py:80` | repo_root = `__file__`.parents[3] = the HARNESS HOME, not the session repo → snapshots `~/.kata-home/.kata/board.md` (absent in a clone) → silent no-op every compaction → Gap-1 durability void in every `~/.kata-home` install (only worked inside the harness repo). Sibling hook already reads stdin cwd. | **FIXED** — reads payload cwd; +3 real-git tests |
| A-2 | HIGH | `function_model.py` `_safe_eval` Mult | seq*int repetition (`[0]*N`) allocates ∝ N — DoS class closed for `**`/`<<` but left open for seq*int; reachable from LLM-authored FM assertions | **FIXED** — eval-time cap at _MAX_SHIFT; +3 tests |
| A-3 | HIGH | `escalation.py:182` `write_escalation` | taskId flows into filename unguarded despite the module advertising CWE-23 protection; taskId carries worker/LLM content → path traversal | **FIXED** — separator/../dash/NUL guard + containment assert; +2 tests |
| A-4 | MED | `kata_install.py` `uninstall` | install links commands/*.md + records manifest; uninstall removed only skills/settings/router → commands + manifest orphaned | **FIXED** — managed-command sweep + manifest removal |
| A-5 | MED | `update.ps1:162,196` | native git fetch/checkout/reset never exit-checked (PS 5.1 Stop doesn't trip on natives) → offline fetch fail-open "already current"; failed checkout stamps a version never applied | **FIXED** — Assert-GitOk + sh fallback chain ported |
| A-6 | MED | `update.sh:61-98` | engine args whitespace-joined + unquoted (SC2086) → spaces/globs in --target-dir split | **FIXED** — positional-param rebuild + quoted "$@" |
| A-7 | MED | `install.ps1:67`, `precompact/sessionstart/statusline` | install.ps1 false "clone complete." on failed clone (F5); Windows ANSI stdin decode gap (F7); zero-trace fail-soft (F8) | **FIXED** — clone check + bytes-UTF8 stdin + stderr breadcrumbs |
| A-8 | LOW | `update.ps1:83` cwd restore (F9); `uninstall.ps1` dead-code/console-close exit (F10) | script-parity polish | **FIXED** |
| A-9 | LOW | `kata_overlay.py:262` list-item key regex (F4); `kata_preflight` allowed_registries naming (F5); F6 custom_instructions output-key assumption | minor | backlog (health-review follow-ups) |

Second-opinion verdict on the non-gate engine half: **high-quality, consistently fail-closed,
`..`-guard idiom nearly everywhere**; the two genuine security bugs (A-2/A-3) were exactly the
class a gate-focused pass wouldn't catch — both now fixed with mutation-proof tests.

Round-2 gauntlet: **pytest 3160/3 · validator 48/0/0 · Snyk medium+ 0 (changed files) ·
integration tests 2/2 green · PS scripts parse-clean ×3 · update.sh bash -n clean**.

## Round 3 (operator: "wire these up and fix ALL of these disconnects") — the backlog built out

Every named health-review deferral was built (operator-directed), across 5 parallel fix-groups +
STEERING wiring + gauntlet infra, done by me. Commits: `feat(steering)`, `fix(engine)`,
`chore(gauntlet)`, `style(ruff)`.

- **F-3 STEERING facade → real**: `tools/kata_steer.py` (stop_requested + read_active_directives,
  +9 tests), `protocol/steering.md`, kata-orchestrate 0.12.0 boundary step, STEERING.md rewritten,
  REQUIRED_PROTOCOL-registered. The AGENT_STOP graceful kill-switch is now implemented.
- **Gate-input validation** (Q-2/Q-3/Q-6): groundsToPlan enum hard-fail; empty-verdicts vacuous:true;
  run_funnel hard-requires refuted/sparse_signal.
- **Benchmark integrity** (Q-8/Q-9/DET-11): malformed test-ID raises; truncated mutation.json ⇒
  vacuous; explicit tie-break key.
- **Gate-runner determinism** (DET-09): sanitized env (strip PYTEST_ADDOPTS + disable plugin
  autoload) — shell=True RETAINED after I caught that the argv rewrite broke the shell-string
  test_cmd contract (65 mutation-proof tests). The env sanitization is the real cross-host win.
- **Determinism residuals** (DET-06/10/12/13/14): fixed-width diffstat, netstring digest, /var/folders
  scrub + node-id separator normalize, content-addressed benchmark id, injectable generated_at.
- **Git-hang safety** (Q-16/Q-14): 60s timeout on every parsed git call; board-unreadable degraded flag.
- **Robustness LOWs** (Q-10/Q-13/Q-18/S-5/S-6/F4/F5): gate_emit exit codes+parsedCounts; researcher
  source-required; ledger skippedLines; rate-table date; web error-vs-waiting; overlay key regex;
  preflight naming doc.
- **Path-guard family drift-guard** (Q-12): `test_path_guard_family.py` pins all 29 `..`-guards +
  a completeness tripwire — chosen over a merge-risky 30-file shared-helper refactor (rationale
  recorded; the physical DRY extraction is the one consciously-deferred item, operator-visible).
- **W-7**: `validate_skills --only <skill>`.
- **Gauntlet infra** (M-1/M-2/6d): ruff (E/W/F/I core), coverage floor 90, `tools/scripts/sca.sh`
  (uv export → pip-audit), `.github/workflows/ci.yml` (Linux+Windows), `docs/RELEASE-CHECKLIST.md`.
  Repo-wide ruff `--fix` hygiene pass applied.

**Note on worktree instability:** several parallel fix-groups (and 3 of my own edits — STEERING.md,
orchestrate 0.12.0, the DET-09 reapply) were transiently reverted mid-session by a
worktree/git operation; each was detected via re-grep/failing tests and re-applied, then committed
promptly to lock in. Adval covers the committed final state.

Round-3 gauntlet: pytest 3270+/3 · validator 48/0/0 · ruff clean · integration 2/2 · Snyk med+ 0.

## Adval — fresh-context adversarial review of the full day's diff (master..HEAD, 3 reviewers)

Per the project's own D33/adversarial-review discipline before merge. Each reviewer told to
REFUTE. Result: **1 HIGH defect caught in a fix I wrote, folded; no cross-seam regression; both
new protocol files confirmed genuinely wired (not docs-only); STEERING confirmed a real tested
engine at parity, not a facade.**

- **DEFECT-1 (HIGH, folded):** my F1 sequence-repetition cap was a PARTIAL FACADE — it bounded the
  count operand (`abs(count) > 1024`) not the result length, so chained `[0]*1000*1000*1000`
  (each count < cap, product 10⁹) bypassed it, verified live. **Fixed:** cap the materialized
  output length `len(seq)*count` at each step (kills the chain at the 10⁶ intermediate); +2
  exploit tests.
- **R1 (MED, folded):** blanket `PYTEST_DISABLE_PLUGIN_AUTOLOAD` on the benchmark scoring path could
  DEFLATE a third-party target's numbers (autoload-reliant tests fail under the gate). Confirmed
  *conservative* (never inflates). **Fixed:** made `run_named_test` surgical — keep autoload, block
  only `-p no:randomly` (harmless when absent), strip ADDOPTS; blanket-disable reserved for the
  arbitrary-command `_default_runner`. Doctrine law 8 updated.
- **Steering polish (folded):** self-contradicting `kata_steer._safe_path` docstring cite corrected
  (PD-2 truthfulness); `_is_placeholder` tightened so a real `(none-blocking)…` directive isn't
  dropped (+test); steering docs now state the stop is conductor-invoked/prose-gated, not
  host-enforced (adval #1); prime-directives validator claim corrected to term-removal not
  "hollowing" (adval #4).
- **Confirmed SOUND (cited by reviewers):** escalation traversal (two-layer), grounding enum,
  deviation run_funnel (no real breaking caller), dispatch researcher, gate_emit exit codes,
  evidence_digest framing (stamp/verify co-temporal, no old-framing pin), git timeouts (all
  fail-closed, no pin removed), graph ordering, drift scrub. Cross-seam: ruff × functional hunks
  disjoint; kata_telemetry triple-compose clean.
- **Left as documented LOW/INFO:** R3 (backslash in param node-id collision — niche), R2 (digest
  contract unversioned — negligible, fail-closed), escalation `C:foo` drive-relative collision.

Post-adval gauntlet: pytest 3271+/3 · integration 2/2 · ruff clean · validator 48/0/0 · Snyk med+ 0.

## Facade-audit conclusion (the BIG ONE, answered)
Across four independent passes (claims 3-leg, engine stub sweep, wiring both-directions,
quality): **KataHarness is NOT a facade.** The advertised feature set is implemented, wired,
and tested to an unusually verifiable degree; deferred work is consistently named. The genuine
gaps found are: one operator-facing facade in an internal planning file (STEERING/AGENT_STOP,
F-3 — fixed: rewritten honestly), one enforcement gap (detect_drift unwired, W-1), one
public-surface honesty-pin violation (benchmark "real evidence" vs synthetic-only, F-5 —
fixed), input-side fail-opens in two gates (Q-1..Q-3), and determinism debt in graph/git
surfaces (DET-01..09). The "oversimplified feel" the operator reported is the OPPOSITE problem:
built capability (dashboard/web viewer) is under-advertised (S-1 — fixed).
