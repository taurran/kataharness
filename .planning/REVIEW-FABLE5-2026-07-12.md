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
