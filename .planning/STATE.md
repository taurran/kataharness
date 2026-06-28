# STATE — KataHarness

> **CURRENT (2026-06-27, DEBUG MODE PHASE 3 [the FINAL phase] BUILT — D117; pytest 1108 · 45 skills/0 · Snyk 0):**
> Completes Debug Mode end-to-end at the skill/seam level — the **core loop is now functionally complete** (comprehend
> P1 → find/route P2a → characterize/drift-gate/apply-or-defer P2b → **report/onboard P3**). Built **entirely through
> subagents** (operator directive). PLAN-p3 (planning subagent) → **freeze-gate kata-review HOLD→SHIP** (caught a real
> BLOCKER: LD12's mandated "Snyk before/after" cited a `RESULT.json` field that NO P1/P2 surface emits → resolved by a
> real persisted `.kata/snyk/<id>.json` artifact piggybacking the fix-loop's existing before/after states + Snyk MCP;
> +2 MINORs) → 6-slice 2-wave build (A engine; D/E wave-1; B/C/W wave-2) → `kata-evaluate` **PART A PASS** → **D98 PART
> B HOLD→fix→re-confirm SHIP** (caught 2 MAJOR fail-opens in the LD12 honesty machinery the conformance gate passed).
> **Built:** **(A)** `tools/debug_report.py` — the pure LD12 report-assembly engine (confidence map · deviation→fix→
> pinning-test · regression+security proof incl. real Snyk before/after · honesty pinned at the engine: behavioral-only
> + heuristic-confidence + n=0-live; **finding_id** join = `drift_gate.defer_record` derivation; 5 mutation proofs;
> no exec sink). **(B)** `skills/evaluate/kata-debrief` — the LD12 author/renderer (two-tier `kata-report` shape; reports
> never gates). **(C)** `kata-closeout` `Step 3b` — debug-gated; offers kata-debrief; reuses Decision 2/3 (no new git
> path). **(D)** `skills/execute/kata-lang-profile` + 6 lang profiles + config specialist — LD10, prose-only, selected by
> footprint file extensions, injected at dispatch (IaC precedent), no fork/no new Python. **(E)** `skills/coordinate/
> kata-onboard` — LD13 first-run/convert-to-loop, composes built install-portability surfaces; convert-to-loop +
> `.planning/` scaffold honestly labeled NEW. **(W)** `kata-orchestrate` — P3-seam resolved + LD10 injection + the
> `.kata/snyk/<id>.json` before/after persistence (no new sink — Snyk MCP already existed; persistence is a Write).
> **Security (load-bearing):** D98 caught (1) Snyk **regression-masking** (engine trusted prose `newFindings` → now
> recomputes `max(stored, max(0,after−before))`, missing-count ⇒ not-clean) and (2) `applied:true` **not route-gated**
> (research finding could inherit another's proof under a finding_id collision → now gated on `route=="auto-fix-eligible"`
> + ambiguous-id refuses to cross-join); both fixed at the **engine**, mutation-covered; re-confirm SHIP. **Honest scope:**
> behavioral drift only (structural = §5 fast-follow); confidence = LD5 v1 heuristic; **Debug Mode still n=0 live** (proven
> on seeded fixtures, never run end-to-end on a real repo — the natural next step, newly possible). 2 validation-misses
> logged (D114 manifest). **Deferred MINORs:** clamp the cosmetic `newFindings` display on malformed input; a pre-existing
> `kata-report`/`kata-closeout` "verdict from RESULT.json" wording inconsistency (RESULT.json has no `verdict` field).
> **kata-onboard** tagged `kata/spine` (validator requires spine-or-module; least-wrong for an on-ramp) — a recorded
> divergence from PLAN-p3's `kata/coordinate+onboarding`. **NEXT (operator picks):** exercise Debug Mode end-to-end on a
> seeded fixture repo (first live run); or recurrence-hardening T2; or IaC Tier-2; or second-brain Recall; or 2nd-platform
> benchmark. Records: `specs/debug-mode/{DESIGN,PLAN-p3}.md`, `DECISIONS.md` D117.

> **CURRENT (2026-06-27, DEBUG MODE PHASE 2b [the PROTECT half] BUILT — D116; pytest 1062 · 42 skills/0 · Snyk 0):**
> Completes the **core Debug Mode loop** (comprehend P1 → find/route P2a → characterize + drift-gate + apply-or-defer
> P2b). Built entirely through subagents. Freeze-gate SHIP → 3 slices (F1 engine; F2+F3 parallel) → evaluate PART A
> PASS → D98 PART B SHIP (found 2 MEDIUM fail-opens in the drift machinery → fixed → re-confirm SHIP). **Built:** (F1)
> `tools/drift_gate.py` — behavioral drift-gate engine (§5 v1): AEL integrity (rejects green-in-before exceptions;
> trusted finding-bound input), green→RED=BLOCK, **vanished-baseline-green=BLOCK** (D98 fix), narrowed nondeterminism
> scrub (D98 fix — no longer masks real value changes); 5 mutation proofs; no exec sink; structural layer = honest
> non-enforcing seam (FAST-FOLLOW). (F2) `skills/execute/kata-characterize/SKILL.md` — blast-radius characterization
> suite, pins-except-deviation, left-behind, establishes AEL. (F3) `kata-orchestrate` `## Fix-application phase` —
> per auto-fix-eligible finding: characterize → kata-tdd in worktree → drift gate → evaluate+D98+Snyk → apply or
> DEFER (can't-fix-without-drift); AEL orchestrator-owned (worker can't enlarge it). Gated on `kata/module/debug`.
> **Honest scope:** behavioral drift enforced; structural/public-API invariance = §5 v1 fast-follow. **NEXT: Debug
> Mode P3** (language prompt-profiles LD10 + onboarding/convert-to-loop LD13 + LD12 closeout confidence report) — the
> final phase; then Debug Mode is functionally complete. Records: `specs/debug-mode/{DESIGN,PLAN-p2b}.md`, `DECISIONS.md` D116.

> **CURRENT (2026-06-27, DEBUG MODE PHASE 2a [the FIND half] BUILT — D115; pytest 990 · 41 skills/0 · Snyk 0):**
> Built **entirely through the loop/subagents** (operator directive — every step delegated to spare main context):
> planning subagent → freeze-gate **HOLD→SHIP** → 3-slice build (D1 engine; D2+D3 parallel) → evaluate **PART A PASS**
> → D98 **PART B HOLD→fix→re-confirm SHIP** → merge. **Built:** (D1) `tools/deviation.py` — the pure LD4-funnel +
> LD5-confidence engine (self-consistency ≥2/3, **corroboration HARD gate**, confidence+routing, force-LOW;
> mutation-proven; no exec sink); (D2) `skills/execute/kata-deviate/SKILL.md` — the LLM driver (FM-deviation via the
> AST-safe `evaluate_spec`; `kata-research` escalation-only); (D3) `kata-orchestrate` `## Deviation-discovery phase`
> gated on `kata/module/debug`, emits `.kata/deviations/findings.json`, P2b seam left. **D98 caught a real fail-open**
> in the corroboration gate (`None==None` co-location → LLM-only finding could reach auto-fix-eligible) → fixed
> fail-closed + **corroborator objectivity now code-enforced** (`_OBJECTIVE_SOURCES`, no longer trusts prose) + null/
> empty hardening; re-confirm SHIP (every attack fails closed). **Honest scope:** P2a STOPS at routed findings — fixes
> NOTHING (characterization LD6 / drift gate §5 / fix loop LD9 = P2b). The first real "conformance-passed,
> adversarial-caught" event since the D114 manifest exists to record it. **NEXT: Debug Mode P2b** (the PROTECT half),
> then P3. Records: `specs/debug-mode/{DESIGN,PLAN-p2a}.md`, `DECISIONS.md` D115.

> **CURRENT (2026-06-27, VALIDATION-MISS MANIFEST T1 BUILT — D114; pytest 907 · 40 skills/0 · Snyk 0):**
> Operator-directed feature (their idea): a durable, **universal, observe-only** manifest logging when the conformance
> gate (`kata-evaluate`) PASSED something the adversarial lens (`kata-review`/D98)/re-confirm/human later CAUGHT — the
> **data layer for recurrence-hardening (D101)** / the Hermes C-arc's harness-facing sibling. Makes "operator notices a
> recurrence" (the D112 RCE catch) a first-class signal. Built alongside Debug Mode but universal (hook in the shared
> `kata-review` RUBRIC → every mode). Freeze-gate **HOLD→SHIP** (caught: emit hook contradicted kata-review's read-only
> contract → relocated write to orchestrator; non-fatal guarantee prose-only → pinned/tested) → evaluate **PART A PASS**
> → D98 **PART B SHIP** (2 LOW hardening fixes moved the BC guarantee fully in-code). **Built:** `tools/validation_misses.py`
> (schema/validate/append[append-only,CWE-23,non-fatal]/read/count_by_class/passive `recurrences`; mutation-proven) +
> `protocol/validation-misses.md` + the universal flag(read-only)→write(non-fatal) hook. **Tiers:** T1 done (log/count/
> surface, observe-only); **T2** = recurrence→gated-proposal (= D101, needs grill); **T3** = auto-author guards
> (C-arc-gated, future). **NEXT: Debug Mode P2** (7-step deviation pipeline LD4 + confidence routing LD5 +
> characterization-gen LD6 + behavioral drift gate §5) — the manifest's first live exerciser; then P3. Records:
> `specs/recurrence-hardening/{BRIEF-validation-misses,PLAN-t1-manifest}.md`, `DECISIONS.md` D114.

> **CURRENT (2026-06-27, DEBUG MODE PHASE 1 BUILT — D113; pytest 867 · 40 skills/0 · Snyk 0):** First phase of the
> phased Debug Mode build (queue item a; DESIGN frozen). 3 disjoint slices → freeze-gate **HOLD→SHIP** (caught the
> `eval`-RCE class in the PLAN — D112 paying off) → orchestrated build → `kata-evaluate` PART A **PASS** → D98 PART B
> **HOLD→fix→re-confirm HOLD→fix→SHIP**. **Built:** (S1) the `debug` run-shape, gated on a distinct `kata/module/debug`
> module marker (mirrors kata-slop-check; version-up provably unaffected, BC); (S2) `tools/function_model.py` — the
> `function_model` oracle with `_safe_eval` (**AST-allowlist, no eval/exec**) spec-wrapper, registered in exec-safety.md;
> (S3) `skills/plan/kata-comprehend/SKILL.md`. **The evaluator is escape-safe AND DoS-safe** after two HOLD rounds —
> the re-confirm caught a chained-Pow explosion the first fix missed → fixed categorically (`**` removed entirely).
> **Honest scope:** P1 produces+validates the oracle only — no deviation pipeline / fix loop / drift gate (all P2);
> confidence stored not routed. **NEXT: Debug Mode P2** (7-step deviation pipeline + confidence routing +
> characterization-gen + behavioral drift gate), then P3 (language profiles + onboarding). **Operator-raised future
> feature (assessing lift, not yet built): a validation-miss manifest** — log critical misses by the validation stack,
> feed the recurrence-hardening/learning loop (D101 + the Hermes-borrowed C-arc), eventually auto-propose+author its own
> guards (gated). Maps onto existing recurrence-hardening + second-brain-learning. Records: `specs/debug-mode/{DESIGN,PLAN-p1}.md`, `DECISIONS.md` D113.

> **CURRENT (2026-06-27, EXEC-SAFETY STANDING GUARD BUILT — D112; pytest 786 · 39 skills/0 · Snyk 0):** Operator
> noticed RCEs recurring and asked "is this the first?" — it was the **3rd instance of one class in one component**
> (`kata-preflight`: freeform `install` [freeze-gate] → `package` source-injection [D98] → freeform `verify` [D111]),
> each fixed in isolation (whack-a-mole). Fired the **recurrence-hardening** loop (D101): built
> `protocol/exec-safety.md` (structured-argv-only contract + a **sink registry** of every `subprocess` in `tools/`
> with trust domain external/operator/internal) + `tools/tests/test_exec_safety.py` (**AST-based** regression — fails
> CI on a new `shell=True` outside the operator-domain allowlist, on `kata_preflight` regaining `shell=True` or reading
> the freeform `verify`/`install` fields, etc. — the guard that would have caught #3). Audit: shipped code clean (only
> `mutation_run`/`run_result` use `shell=True`, both operator-authored). **NEXT: starting the Debug Mode build (queue
> item (a)) — DESIGN frozen `specs/debug-mode/DESIGN.md`, both blockers long cleared.** Record: `DECISIONS.md` D112.

> **CURRENT (2026-06-27, HOLISTIC RED-TEAM of D108/D109/D110 + FIXES — D111; pytest 776 · 39 skills/0 · Snyk 0;
> D98 re-review CLEAN):** Session first-task per `NEXT-SESSION-ORIENTATION.md` — a fresh-context *cross-cutting*
> adversarial pass over the day's 3 back-to-back builds (the seams *between* them were unreviewed). 5 parallel
> reviewers → synthesis → operator-gated trimmed scope (fix confirmed findings; drop LOW cosmetic). **Real defects
> the per-build passes missed, all fixed + test-proven:** a **preflight RCE** (freeform `dep["verify"]` was executed
> before the SCA gate → structured `verifyImport` builder; freeform `verify` demoted docs-only), **IaC gate-skips**
> (case-sensitive ext match; `forceClassify` documented-but-never-wired; stateful-set gaps incl. KMS/Secrets/MSK/
> FSx/Backup/Logs/Timestream/QLDB/MemoryDB/Keyspaces/CFN-EC2::Volume), **Snyk truthiness** (→ strict `is True` +
> fail-closed), the **iac.json cross-seam fail-open** (kata-evaluate now independently re-classifies the footprint),
> **`resolve_roles` host-only** silently-dropped (→ `HOST_ONLY_ROLES` fail-closed), TF **`action_reason`** wrong
> nesting, manifest **TOCTOU**, regex `fullmatch`, and the **4th doc-drift recurrence** (worst `file:line` cites →
> function/section anchors, killing the class). **Operator caught one spiral** (a sandbox-default flip over-fixing a
> cosmetic finding) → reverted — the spiral-check was load-bearing. Deferred LOW/architectural (snake→camel rename,
> severity-floor enforcement, CDK-source, deterministic `iac_gate.py`). Applied **inline** (operator directive), not
> orchestrated. **Not a planned feature** — a hardening pass. Record: `DECISIONS.md` D111. **NEXT (the open queue,
> operator picks):** (a) **Debug Mode** build (DESIGN frozen, both blockers cleared — the onboarding killer-app);
> (b) IaC Tier-2 live-apply; (c) recurrence-hardening; (d) second-brain-learning; (e) install+confirm a 2nd platform
> → multi-model benchmark.

> **CURRENT (2026-06-26, IaC-SAFETY SPECIALISTS (Tier 1) BUILT — merge `396baa3`, D110; pytest 739 · 39 skills/0 ·
> Snyk 0; PUSHED, in sync):** capability-aware-assignment, narrowed to **IaC specialists** for v1 (the specialist
> value for frontier models is **safety/security/gate discipline, not language expertise**). 4-agent grounded research
> spike → grill → freeze → recipe build (4 slices). **Two specialists** `kata-iac-terraform` + `kata-iac-cloudformation`
> (`execute`, never-tiered, DRY-by-pointer to `protocol/iac-safety.md`); **Tier 1 = author/review/gate, NO live apply**
> (no cloud creds; cloud apply breaks git-reversibility — **Tier 2 deferred**, `specs/iac-live-apply/BRIEF.md`).
> Auto-activated by `tools/iac_detect.py` (classifier + plan/change-set destructive-parsers, fail-closed); gate =
> validate/cfn-lint → `snyk_iac_scan` (default-FAIL high/critical; **fail-closed if unwired**) → 8-smell lens →
> destructive analysis (static + parse-if-provided; no live plan gen) → `.kata/iac.json` → pass/fail/**escalate**
> (destroy/replace on a stateful resource → human-required). `kata-evaluate` reads the artifact; BC: no IaC ⇒ no-op.
> freeze-gate **HOLD→SHIP** · `kata-evaluate` **PASS 9/9** · **D98 HOLD→SHIP — caught a real safety BLOCKER** (stateful
> set too narrow: EFS/SQS/SNS/Kinesis/OpenSearch/Neptune/DocDB weren't escalating on destroy) + fail-open + overclaim,
> all fixed. Backout `pre-iac-specialist`. **NEXT (choose):** (a) **Debug Mode** build (both blockers cleared long ago;
> DESIGN frozen — the onboarding killer-app); (b) **Tier-2 IaC live-apply** (its own grill, gated on authenticated
> cloud access); (c) **recurrence-hardening** general build; (d) **second-brain-learning** (Recall contract); (e)
> install+confirm a 2nd platform → multi-model benchmark. Records: `specs/iac-safety-specialist/*`, `specs/iac-live-apply/BRIEF.md`.

> **CURRENT (2026-06-26, kata-preflight BUILT — the PRE-FLIGHT spine phase — merge `710347a`, D109; pytest 633 ·
> validate 37/0 · Snyk 0 med+; PUSHED, in sync):** D29 realized. Grilled in plain terms → 4 operator decisions
> (auto-run pre-approved installs · full v1 incl. cleanup report · one mechanism for build-deps + target runnable-env ·
> sandbox-when-available-else-host+warn), built through the recipe. **freeze-gate HOLD→SHIP** (command-injection
> BLOCKER + 3 MAJORs fixed) → 3-slice orchestrated build → **kata-evaluate PASS 9/9** → **D98 red-team HOLD→SHIP —
> caught a real untrusted-source RCE path** (`package=https://evil…` bypassing the forced registry) the evaluator
> missed; fixed via **per-manager package-NAME grammar** (no URL/VCS/source expressible) + approval-artifact path/claims
> + Snyk fail-closed. **Exists:** `tools/kata_preflight.py` (guarded auto-installer — structured argv never shell,
> freeform install string never executed, forced trusted registry, Snyk SCA pre-install, manifest-hash drift gate,
> machine-global registry + reference-counted cleanup [never auto-uninstall], target runnable-env probe,
> `preflight_required`/`gate_status`) · the spine skill `kata-preflight` (never tiered) · `kata-orchestrate`
> conditional fail-closed PRE-FLIGHT precondition (BC: no manifest ⇒ today's loop) · structured `dependencies.md` ·
> grill/design-doc/plan manifest pointers (36→**37 skills**). **Honest scope:** auto-install stub-tested (injectable
> runner); real install only behind freeze-approved-hash + Snyk + sandbox; workers never install. **Clears the 2nd of
> Debug Mode's two blockers (install-portability was 1st) → Debug Mode UNBLOCKED.** Backout `pre-kata-preflight`.
> **NEXT (choose):** (a) **Debug Mode** build (both blockers now cleared — DESIGN frozen `specs/debug-mode/DESIGN.md`;
> the onboarding killer-app); (b) grill **capability-aware-assignment**; (c) strategy BRIEFs (second-brain-learning ·
> recurrence-hardening); (d) install+confirm a 2nd platform → multi-model benchmark. Records:
> `specs/kata-preflight/{GRILL-LEDGER,DESIGN,PLAN}.md`.

> **CURRENT (2026-06-26, MULTI-MODAL LAYER BUILT — full routing wiring over the proof-slice — merge `1f58415`,
> D108; pytest 552 · validate 36/0 · Snyk 0 med+; PUSHED, in sync):** The D105 PARKED full layer is now wired,
> built through the full recipe. Frozen PLAN (4 disjoint slices) → **freeze-gate `kata-review` HOLD→SHIP**
> (caught a kiro write-vs-emit seam + a `config.md` false-contract + a self-introduced phantom `target.platform`
> citation) → **orchestrated build** (4 concurrent Sonnet workers in worktrees, TDD, mutation-proven, self-stamped
> — `concurrency.json maxInFlight:3`) → fresh-context **`kata-evaluate` PASS 9/9** (reproduced artifacts + executed
> seams live) → standing **D98 `kata-review` SHIP** (caught 5 stale role-map citations + 1 overclaim → fixed via
> stable section-name anchors). **Wired:** (A) `kata-orchestrate` `roles` load-guard (resolve via `kata_roles`,
> host=runtime adapter identity `"claude"` v1, fail-closed) + "Cross-model dispatch" section (build_brief→dispatch→fold
> per role-group site, LD6 concurrency, LD7 host-fallback); `config.md:27` flipped DESIGN-STAGED→**wired**. (B)
> `kata-initiate` Phase 2e "Make this run multi-modal?" + value #8; `kata-bootstrap` writes `roles`. (C)
> `kata_dispatch` `_brief_prompt` capture-model branch (codex emit / **kiro writes resultPath**) + `kiro_command`.
> (D) `kata_install` `.agents/skills/` targeting + kiro probe + `_PROBE_COMMANDS ⊆ _COMMAND_BUILDERS` invariant.
> **Honest scope:** read-only roles (validator→codex, researcher→kiro) **wired + stub-test-proven**; real run gated
> on install+confirm; coder-routing + copilot/cursor + evaluator-thresholds DEFERRED. **This makes a real
> single-vs-multi-model `kata-loop-benchmark` runnable** once a 2nd platform is installed+confirmed. Backout
> `pre-multimodel-layer`. **NEXT (choose):** (a) `kata-preflight` (the other Debug Mode blocker, D29/D103) → Debug
> Mode; (b) grill **capability-aware-assignment** (the specialist axis that multiplies with multi-model); (c) the
> strategy BRIEFs (second-brain-learning Recall contract; recurrence-hardening general build); (d) install+confirm a
> 2nd platform live + run the benchmark. Records: `specs/multi-model-orchestration/{DESIGN,PLAN}.md`.

> **CURRENT (2026-06-26, install-portability BUILT · multi-model GRILLED+FROZEN+proof-slice BUILT · red-team
> hardened · loop-init banner — tip `fe8d015`, D104–D107; pytest 542 · validator 36/0 · Snyk 0 med+):** A big
> build+research day. **(D104) install-portability BUILT** (the *simple* model after an operator course-correction
> from a config-resolution cathedral → memory [[grill-in-plain-terms]]): one central install + a 2-setting
> `.kata-settings.json` (default parent project folder + vault/second-brain location) + per-run **project search**
> (name + rough location → search → confirm; copy mode) + per-platform installer (Claude verified end-to-end via
> flat-link into `~/.claude/skills/`; Codex/Kiro best-effort; Quick own) + `docs/SETUP.md` + `.claude-plugin/plugin.json`.
> **(D105) multi-model-orchestration GRILLED → FROZEN DESIGN → Codex-validator PROOF-SLICE BUILT** (the operator's
> real "multi-modal" vision: route loop ROLES to platforms — Claude=coder, Codex=validator, Kiro=researcher).
> Grounded in **5 cited research agents** (`RESEARCH.md`): the `SKILL.md` Agent-Skills format is a **shared standard**
> across Claude/Codex/Kiro/Copilot/Cursor, and **all are headless-automatable**. **5 role groups** (coder · validator
> [red-team+anti-slop+grounding] · researcher · orchestrator · **evaluator** = a lightweight inline scorer that
> accepts/sends-back/**rerolls** via `bakeoff`); **default all-on-host, multi-modal opt-in at preflight**; **any role
> routable** (coder stays one sustained agent); **files+CLI dispatch** (concurrent background subprocesses); **failure
> → host fallback**; two orthogonal layers (platform/model × specialist). **Convergence HOLD#1: the D102 guard caught
> over-claimed reuse → relabeled NEW (N1–N5 with schemas) → re-confirm SHIP.** Proof-slice = `tools/{kata_roles,
> kata_dispatch}.py` + confirm-probe + `roles` config; **end-to-end proof** (validator→codex→normalized verdict)
> against a stub-CLI seam (codex not installed → real run gated on install+confirm). **(D106) 3-pass red-team
> hardening** of D104/D105 — fixed copy_project source-destruction, default-FAIL gaps, a spoofable confirm probe, a
> confirm→crash trap, corrupt-JSON/dup-skill robustness, + doc-vs-code lies (the `roles` load-guard is design-staged,
> not wired). **(D107) loop-init banner** — every run opens with a deterministic boxed `KATAHARNESS 改善型 · executing`
> readout (`tools/kata_banner.py`), painted in the closeout-report palette (`--color`); wired into `kata-loop`,
> documented in `protocol/narration.md` §5. **NEXT (choose):** finish the multi-model layer (wire `kata_dispatch`
> into `kata-orchestrate` + the `roles` load-guard + the "make this multi-modal?" preflight + more adapters) — makes
> a real single-vs-multi-model benchmark runnable; OR `kata-preflight` (the other Debug Mode blocker) → Debug Mode
> build; OR grill capability-aware-assignment. Records: `specs/{install-portability,multi-model-orchestration}/*`.

> **CURRENT (2026-06-25, Debug Mode GRILLED + DESIGN FROZEN + PARKED — `d010434`):** Roadmap session. Captured two
> big Phase-5 items as pre-grill BRIEFs — **capability-aware (multi-modal) assignment** (loop-wide stack-detection →
> specialist routing; resolves multi-model-orchestration's flagged "multi-modal?" question) and **Debug Mode** — then
> **fully grilled Debug Mode** to a frozen DESIGN. **Debug Mode** = a self-contained **run-shape `debug`** (peer of
> version-up), pointed at a whole codebase, **debug-in-confidence** (bugs out, behavior preserved); the
> onboarding/conversion killer-app. Design (7 grill rounds + a 4-thread research pass + 3 repo assessments, two
> convergence-gate HOLDs → SHIP): a NEW **`kata-comprehend`** builds an executable **`function_model`** oracle of
> intent; a **7-step deviation pipeline** (self-consistency → objective-corroboration HARD gate → adversarial
> refute-or-promote) gates on corroboration, not oracle accuracy; **behavioral drift gate** v1 (surface/AST +
> confidence-calibration = honest fast-follows, H4 caveat in backward-compat). LOCKED LD1–LD13; reuse claims
> verified (the D102 guard caught a phantom `kata-understand` reuse mid-grill — recurrence-hardening working). **Build
> PARKED** behind **`install-portability` (built first, DG-10b) + `kata-preflight`**. Artifacts:
> `specs/debug-mode/{BRIEF,GRILL-LEDGER,RESEARCH,DESIGN}.md`; the 3 assessed repos (debug-skill/claude-devtools/
> pointbreak-claude) = all BORROW-PATTERN, takeaways parked. **NEXT:** Phase 5 — **`install-portability`** (now the
> critical-path predecessor for Debug Mode) → multi-model → grill the strategy BRIEFs + capability-aware-assignment +
> v0.1 release-checklist.

> **CURRENT (2026-06-25, phantom-machinery first hardening BUILT + MERGED — `47648bf`, D102):** D101's worked
> example shipped — the **verify-before-reuse guard**. `protocol/reuse-claims.md` (cross-skill contract: *before
> claiming "reuses/composes X", grep/read X + cite `file:line`, else label NEW*) + by-path pointers in
> `kata-design-doc` / `kata-plan` RUBRIC / `kata-tdd` + a `validate_skills.py` regression rule (dual mechanism +
> body-integrity full-phrase guard + producer-existence FAIL-loud check). Built through the **full recipe**
> (subagent-driven Sonnet T1/T2/T3, Opus judgment): freeze-gate **HOLD→SHIP** · `kata-evaluate` **PASS 9/9** ·
> **T-fire proof-of-fire** (a fresh `kata-design-doc` agent refused to freeze a phantom `orient.emit_pointers()`
> claim → labeled NEW) · standing D98 `kata-review` **SHIP-WITH-FIXES→SHIP** (caught a default-FAIL gap where a
> renamed producer would silently disable the guard — fixed). pytest **456**, validator **36/0**, Snyk **0**,
> mutation non-vacuous. **Honest:** the rule enforces **presence, not behavior**; T-fire is **n=1, contaminated,
> no guard-off control** — corroborating, not causal proof (the mutation-bitten regression rule is the durable
> proof). Backout `pre-phantom-hardening`. Record: `specs/recurrence-hardening/{PLAN-phantom,REPORT-phantom}.md`.
> **NEXT:** Phase 5 EXTERNAL (install-portability → multi-model → testing-model) + **grill → freeze** the two
> strategy BRIEFs (`second-brain-learning` Recall-contract is load-bearing; `recurrence-hardening` general build)
> + v0.1 release-checklist (flip Policy A). Far-future: `kata-loop-benchmark` → DAG-in-DAG.

> **CURRENT (2026-06-24, loop-learning strategy locked + fix-loop hardening BUILT — `fc7f4f7`, D98–D101):** A long
> strategy + hardening session. **(1) The standing adversarial red-team is now wired (D98/L12):** `kata-review`
> runs after `kata-evaluate` PASS, before merge, on every code/contract-bearing build; `kata-evaluate` gained
> rubric **item 9 "reproduce, don't trust"** (regenerate derived artifacts; execute claimed seams). This wired a
> lesson the project had recorded (L10c) but never baked in — so it kept recurring. **(2) Loop-learning strategy
> locked (D99):** ship **Controlled (A)** now, **Gated-learning (C)** is the destination, **Hermes-fluid (B)** is a
> trap; the learning subsystem is re-modeled as **Second brain (data, BYO) + Recall (per-vault Librarian/adapter,
> downstream) + Reason (`kata-reason`, the Advisor/decider, core)** — *"Recall what you know · Reason what you'd
> do"*; "engram" retired (rename pending). C unlocks via a **four-tumbler** gate (BYO backend · a **readiness exam**
> = the measurable maturity def · **inline triage** red-team · **outcome benchmark** — `kata-loop-benchmark`
> promoted to keystone), bounded by the **C/B invariant** (*every Reason decision stays a frozen, gated,
> thrash-bounded, audited event toward a human-frozen goal — protect the process, not the decider*). Spec:
> `specs/second-brain-learning/BRIEF.md`. **(3) Recurrence hardening captured (D101):** when a failure-class recurs,
> the loop hardens the responsible agent (auto-detect → propose → gated human-approve, never auto-mutate) — the
> harness-facing sibling of Reason. Spec: `specs/recurrence-hardening/BRIEF.md`. **(4) Fix-loop hardening BUILT
> through the main loop (D100, `fc7f4f7`):** the Approach-A thrash guard — material (footprint-scoped)
> re-verification + a per-area (N=2) + run-level (`2×tasks+2` `[TUNABLE]`) thrash budget → `kata-diagnose`
> fix-vs-plan verdict → human only on a plan-problem. Freeze-gate **HOLD→resolved**, re-confirm **HOLD→resolved**,
> build `kata-evaluate` **PASS 7/7** + standing D98 red-team **SHIP-WITH-FIXES** (2 degrade-safe, fixed). pytest
> **447**, validator **36/0**, `codeBearing:false`. **Honest:** wired, exercised by **zero real thrash events**;
> N=2+ceiling provisional. **The adversarial lens caught the phantom-machinery / over-claimed-reuse class FOUR
> times** this session → memory `verify-primitives-before-claiming-reuse` + the live case for D101. **NEXT:** the
> **phantom-machinery first hardening** (document the fix-guide + place the guard in the responsible planning skill,
> then test it — D101's worked example) · then Phase 5 EXTERNAL (install-portability → multi-model → testing-model)
> + grill/freeze the second-brain-learning + recurrence-hardening BRIEFs + v0.1 release-checklist.

> **CURRENT (2026-06-24, WS-2 polish DONE — worker concurrency now artifact-provable — `4d8f01b`, D97):** Closed
> the last WS-2 honest gap (AUDIT §7): durable board timestamps were orchestrator-written (couldn't distinguish
> live concurrency from replay). Now **workers self-stamp `CLAIM`/`DONE` with their own clock** to the shared
> board, and the gate derives **`.kata/concurrency.json`** (maxInFlight · per-task wall-clock · overlap windows).
> Per operator direction, the evidence is produced by an **embedded in-context snippet in `protocol/board.md`** —
> **NO new committed Python** ([[prefer-in-context-over-new-python]]) — keeping the run **non-code-bearing**
> (`codeBearing:false`). 3-slice/2-wave orchestrated dogfood; **self-proving** — the build's own wave-2 workers
> (B+C) overlapped and this run's `concurrency.json` shows **`maxInFlight:2`** (~75s overlap). Fresh-context Opus
> `kata-evaluate` **PASS 7/7**; pytest **447**, validator **36/0**. Backout `pre-ws2-polish`. Record:
> `specs/ws2-polish/PLAN.md`. **NEXT:** Phase 5 EXTERNAL (install-portability → multi-model → testing-model) +
> v0.1 release-checklist (flip Policy A); M8 native-in-tool closeout rendering = adapter work; far-future = loop
> benchmark → DAG-in-DAG.

> **CURRENT (2026-06-24, WS-1 pre-launch re-grep CLEAN):** Ran the final pre-public sanitization pass — the
> work-internal proper noun + variants return **0 matches** across all tracked files, frozen specs, and the
> working tree (incl. untracked artifacts); the `Quick`/ACP plumbing seam is intact (20 files) and the scrub is
> consistent indirection, not bare deletion; light secret/key sweep clean. Hardened `.gitignore` (`/INTENT.md`
> root run-artifact + `.claude/`). **WS-1 is DONE** — the last pre-public sanitization gate. validator **36/0**,
> pytest **447**. **NEXT:** WS-2 worker-self-timestamp polish (code-bearing orchestrated build) → Phase 5 EXTERNAL
> + v0.1 release-checklist.

> **CURRENT (2026-06-24, WS-3 field-exercised + two-tier closeout shipped — `c265c42`, D96):** Ran the **first
> live use** of the WS-3 friendly closeout (n=0→1) by building a real feature through it: the closeout is now
> **two-tier** — a concise CLI/GUI summary that **links to a durable, on-brand, self-contained HTML report**
> (`.kata/closeout.html`) with a Markdown source (`.kata/CLOSEOUT.md`). 3-slice non-code-bearing dogfood
> (concurrent Sonnet workers, self-stamped): template+`BRAND.md` (S1), `kata-report` two-tier content (S2),
> `kata-closeout` emit+render-in-context+link (S3). Fresh-context Opus `kata-evaluate` **caught a cross-slice
> badge-class defect → fixed → PASS**. **Operator refined the brand live at the gate** (M4): dropped a wave
> motif + tab-like loop ribbon; landed the **first KataHarness logo** (kaizen ascending-bars + rising ochre
> arrow), readable **serif** section titles, and **error/warning/ok callout tiles**, on a **Hokusai-derived**
> palette. Non-code-bearing (`codeBearing:false`, 0 drift); pytest **447**, validator **36/0**. **Carry-out:**
> native in-tool rendering (hooks/statusline) deferred to adapters (M8). Backout `pre-ws3-report`. Record:
> `specs/ws3-closeout-report/PLAN.md`. **NEXT:** WS-1 pre-launch re-grep · WS-2 worker-self-timestamp polish ·
> then Phase 5 EXTERNAL + v0.1 release-checklist (far-future: loop benchmark → DAG-in-DAG).

> **CURRENT (2026-06-24, WS-3 user-friendliness BUILT — `d08908d`, D95):** The last pre-public workstream shipped.
> Brainstorm (Hermes/Devin/Claude-Code UX research) → frozen DESIGN (L1–L11) → freeze-gate `kata-review`
> **HOLD→SHIP** (caught a real backout seam — re-anchored to `.kata/RESULT.json.baselineSha`) → frozen PLAN
> (6-slice DAG) → **orchestrated version-up dogfood** (2 waves, concurrent Sonnet workers in worktrees,
> self-stamped overlapping wall-clock) → fresh-context Opus `kata-evaluate` **PASS 10/10**. **Shipped (8 files,
> non-code-bearing, `codeBearing:false`, 0 drift):** `protocol/persona.md` (nameless calm kata-craftsperson SOUL,
> moderate-non-expert default), `protocol/narration.md` (phase→plain map + never-tiered breakthrough + honesty
> guard), `engram.md` E23 register seam (gated), `kata-initiate` reflective **goal-mirror** (S2 gate refined-not-
> reversed, with teeth), `kata-bootstrap` one **"how careful"** dial (existing fields, advanced drawer),
> `kata-orchestrate` additive milestone narration, `kata-closeout`+`kata-report` **goal-anchored by-aspect
> closeout** + offered backout. **WS-4 + WS-5 folded in.** The build's own closeout dogfooded slice F. pytest
> **447**, validator **36/0**. **Honesty:** built + gate-PASS + fresh-eval PASS, **NOT yet field-exercised (n=0
> live UX runs)** — the next real Kata Loop run is the first UX test; adaptive register is a gated seam, not live.
> Backout `pre-ws3`. **NEXT:** field-exercise WS-3 on a real friendly run · WS-1 pre-launch re-grep · then Phase 5
> EXTERNAL (install-portability · multi-model) + v0.1 release-checklist; far-future = loop benchmark → DAG-in-DAG.

> **CURRENT (2026-06-22, WS-2 EXERCISED + `kata-slop-check` shipped — `ece872e`):** Built **`kata-slop-check`** (optional
> EVALUATE module `kata/module/slop`: fresh-context no-write, default-FAIL slop verdict, **in-context heuristics** —
> general G1–G6 + 3 MIT-attributed checks adopted from `ai-slop-detector`, no code copied) via a **real version-up
> dogfood** that doubled as the **WS-2 validation**. A fresh-context auditor graded the run **7/7**: 3-worker
> concurrency → a **live `research-needed` escalation** → orchestrator **parked the sub-tree** (S1+S4+S5) while S2/S3
> integrated → **`kata-research`** grounded the gap → **grounding gate GROUND×6** → **superseding re-plan** fold →
> frontier recompute → **mutation-proven** slice. The feature **caught a defect in
> its own build** (dangling seam pointer → NEEDS_WORK → fixed → CLEAN). **Parallelism + the in-loop RS path
> (audit-flagged "unexercised") are now exercised end-to-end (n=1).** Feature gate `kata-evaluate` **PASS**; pytest **447**,
> validator **36/0**. **Caveat:** board timestamps are orchestrator-written (live-vs-replay not artifact-distinguishable)
> → follow-up = **worker self-timestamping** (BACKLOG). Record: `specs/kata-slop-check/PLAN.md` +
> `specs/ws2-loop-autonomy/AUDIT.md`; audit trail `.kata/board.md`. Backout `pre-ws2-slopcheck`. **NEXT:** **WS-3**
> (user-friendliness — the big pre-public workstream) or remaining WS-2 polish (worker self-stamp).

> **CURRENT (2026-06-21, S3b DONE — G6 PROVEN; loop-hardening COMPLETE — `222cc7e`):** The live loop-back ran:
> KataHarness ran its own **Kata Loop twice**, operator-driven, and a fresh-context grade returned **G6 PROVEN**
> (7/7, corroborated against independent evidence — the Cycle-2 goal is a near-literal instantiation of the
> Cycle-1 understand-map's named adjacent gap, baseline SHA matched `RESULT.json`). **Cycle 1** = NIT-2 (validator
> asserts evaluators `kata-evaluate`/`kata-research` omit Write/Edit; `f72a3bb`); **Cycle 2** (loop-back, Phase 1b
> consumed the carried context) = MAJOR-3 (machine `codeBearing` flag in `footprint.py`; `kata-evaluate` rubric
> item 1 keys off it; `222cc7e`). Both cycles: real `kata-initiate` interview (G4 live), orchestrated Sonnet-worker
> build in a worktree, `prove_non_vacuous` → `mutation.json allNonVacuous:true` (**MAJOR-2 live-proven**),
> fresh-context `kata-evaluate` PASS, operator git/version-select gates. **MAJOR-1 (grounding) correctly did not
> fire** (no research-needed escalation — as PLAN-s3b predicted; stays unit-proven). **ALL 7 GAPS CLOSED
> (G1–G7).** pytest **445**, validator **35/0**, Snyk 0. Tag `pre-s3b`; closes BACKLOG NIT-2 + MAJOR-3. Record:
> `specs/loop-hardening/{PLAN-s3b,REPORT-s3b}.md`. **loop-hardening is DONE — "vetted, and demonstrably loops."**
> **NEXT:** remaining BACKLOG hardening (`_safe_path` guard consistency; planning-approach↔delivery-mode alignment)
> → **Phase 5 EXTERNAL** (install-portability · multi-model-orchestration) → v0.1 release-checklist.

> **CURRENT (2026-06-21, red-team seam-fixes + Kata Loop rename — `94539dd`; AT THE S3b BOUNDARY):** An adversarial
> red-team of S2+S3a confirmed the project's known **documentation-only seam** failure mode had partially recurred and
> we **fixed it inline (D92):** `kata-orchestrate` now explicitly **persists the grounding verdict** via
> `tools/grounding_gate.py` → `.kata/grounding.json` (MAJOR-1 — it was named only in the no-write `kata-evaluate`, so a
> real cycle would have silently skipped it) and **collects per-task `prove_non_vacuous` records** into the integration
> `gate_emit` mutation set (MAJOR-2). `kata-closeout` mutation row aligned to the strengthened S2 rule (MINOR-1).
> **Branding (D92, user):** "Greater Loop" → **"the Kata Loop"** across active/canonical surfaces; inner one-shot
> stays **"the Harness"**; **loop-back** unchanged; frozen `specs/greater-loop/` + history keep the old term as
> provenance; `CONTEXT.md` glossary added. **Deferred to BACKLOG:** machine `codeBearing` flag (MAJOR-3), validator
> no-write assertion (NIT-2), `_safe_path` guard consistency; plus the planning-approach↔delivery-mode alignment
> assessment. **validator 35/0, pytest 420, Snyk 0.** **6 of 7 gaps closed (G1–G5, G7).** **NEXT = S3b, the live
> loop-back (G6)** — operator-driven; the MAJOR-1/MAJOR-2 prose fixes get **live-proven** by it. Full S3b plan in
> `.planning/HANDOFF.md` §4.

> **CURRENT (2026-06-21, loop-hardening S3a DONE — `4391deb`):** **Grounding + research now have a concrete,
> testable substrate** (closes G5). `tools/escalation.py` = `research-needed` escalation payload + research-finding
> builders/writer (`.kata/escalations/<id>.json`); `tools/grounding_gate.py` = deterministic GROUND/REJECT/ESCALATE
> verdict + `.kata/grounding.json` (`allGrounded`); wired into `kata-research` (finding schema) + `kata-evaluate`
> injected-knowledge mode (both stay no-write). **G5 demonstrated end-to-end**: a real escalation + three findings
> graded GROUND·REJECT·ESCALATE (`allGrounded:false` correctly). Grounding is **conditional** (fires only on a
> `research-needed` escalation, not per-run). **pytest 420, validator 35/0, Snyk 0.** Fresh-context `kata-evaluate`
> **PASS 8/8**. Backout tag `pre-s3a`. **6 of 7 verified gaps closed (G1–G5, G7).** **ONLY G6 REMAINS = S3b, the
> live loop-back** — a real version-up re-entry that proves the loop loops (operator-driven: the human "run again"
> decision can't be simulated, `exercise-harness-for-real`). That is the next session, done WITH the operator.

> **CURRENT (2026-06-21, loop-hardening S2 DONE — `cddf9ff`):** **The gate now proves tests bite + initiation is a
> hard human stop** (closes G3+G4). `tools/mutation_run.py` = deterministic restoring mutate→run→restore loop (reuses
> `mutation_check`); `kata-tdd` PROVE points at it; `kata-evaluate` rubric item 1 now **requires** `.kata/mutation.json`
> `allNonVacuous:true` for code-bearing runs (closes the silent-skip hole). `tools/intent_scaffold.py` = schema-conformant
> `INTENT.md` writer; `kata-initiate` now a **hard structural interview STOP** (must `AskUserQuestion` for kind/target/
> vault/platform/grillDepth + execute, no inline inference). **G3 demonstrated end-to-end**: the runner mutated a live
> line → test flipped green→red → file restored byte-for-byte → `mutation.json` (`allNonVacuous:true`) emitted; fresh
> RESULT.json (`s2-integration`, 367) + footprint (`withinFootprint:true`). **pytest 367, validator 35/0, Snyk 0.**
> Fresh-context `kata-evaluate` **PASS 8/8** (it caught a missing RESULT.json regen — fixed — then re-confirmed).
> Backout tag `pre-s2`. **NEXT = S3** — grounding/research (G5) + the **loop-back** (G6): a real version-up re-entry that
> proves the loop loops, evaluating the handoff as it cycles back through `kata-initiate` Phase 1b (operator's hard
> requirement). See `.planning/HANDOFF.md` §4.

> **CURRENT (2026-06-21, loop-hardening S1.5 DONE — `e753504`):** **Status-surface adapters shipped** (closes G7) —
> the live view is now seamless per-platform via the *adapter* pattern applied to OUTPUT. **Seeded `adapters/`** with
> its first concrete member `adapters/claude/` (statusline command + `settings.snippet.json` w/ `refreshInterval:1` +
> README); `tools/kata_statusline.py` (agnostic `render_statusline` + fail-soft Claude entry); `tools/kata_web.py`
> (localhost web viewer, stdlib `http.server` bound 127.0.0.1, polls `/api/view` every 1s, renders 改善型 bars/ribbon/
> feed). Both **pull-consume** `build_view_model` — no push StatusSink, no `kata-loop` wiring. Grounded by
> `specs/loop-hardening/RESEARCH-s1.5.md`: **Claude** statusline feasible now; **Codex** has no live in-TUI surface
> (→ web/TUI fallback); **Kiro** only via a VS Code `.vsix` (deferred) — all documented, no fake bars. Fresh-context
> `kata-evaluate` **PASS**; operator-demo caught two render bugs (statusline SystemExit fail-soft + web numeric-child),
> both fixed w/ regression tests. **pytest 334, validator 35/0, Snyk 0.** Backout tag `pre-s1.5`. **NEXT = S2**
> (mutation proof G3 + interactive initiate G4), then **S3** (grounding/research G5 + the **loop-back** G6 — proves the
> loop loops). See `.planning/HANDOFF.md` §4.

**Phase:** **✅ `v0.1.0-alpha.2` SHIPPED — Greater Loop proven end-to-end (Phase 4 self-dogfood done)** · Phases 0–3 built + adversarial-reviewed + seam-fixed · **35 skills / 0 errors · pytest 205 · Snyk: residual CWE-23 documented FP** · private remote (taurran/kataharness), tip `3ed18d3` · **Updated:** 2026-06-21

> **CURRENT (2026-06-21, alpha.2 shipped):** **The complete Greater Loop ran end-to-end on KataHarness itself for
> the first time and shipped a real feature** — the **subagent-dashboard** (`tools/kata_dash.py` + `kata_dash_model.py`):
> a `rich` live TUI that tails `.kata/board.md`+`state.json` and renders worker subagents as artistic ASCII
> (`⛩ 道`, block bars, braille spinners, `GRILL▸…▸IMPROVE` ribbon). The run: `kata-initiate` (froze INTENT/PLAN) →
> orchestrated harness (DASH-model ∥ DASH-render, 2 workers/worktrees, octopus-merge, `gate_emit` RESULT.json,
> fresh-context `kata-evaluate` **PASS 8/8**) → `kata-closeout` (graph-backed `.kata/understand.md` via F2 — 107
> dashboard symbols mapped; human **version-select** → ship+tag). **The dogfood caught + fixed a real Windows
> UTF-8 render crash via the integration smoke test** (the gate doing its job). pytest 112→205. Record:
> `specs/subagent-dashboard/{INTENT,PLAN,SECURITY,REPORT}.md`. Backout tags `pre-dash` + `pre-phase0..3`.
> **loop-hardening sprint-cadence IN PROGRESS (closes the verified Phase-4 gaps).** Roadmap+grounding:
> `specs/loop-hardening/{ROADMAP,PLAN-s1}.md`. **✅ S1 DONE (`fedbb87`, fresh-eval PASS 8/8):** `tools/kata_board.py`
> emits the live coordination board (`.kata/board.md` incl. **PROGRESS heartbeats**) + single-writer `state.json`
> (self-creates `.kata/`); dashboard renders smooth heartbeat bars + progressLabel; title **`KATAHARNESS 改善型`**
> (kaizen-gata; torii+hiragana removed per operator, see [[ui-text-japanese-concise]]); `tools/kata_dash_demo.py`
> replay driver (delegates to kata_board). Closes **G1+G2**. pytest 244→268, validator 35/0, Snyk med+ 0.
> **⏸ STOPPED at the S1 boundary for the operator to WATCH the live dashboard + give feedback before S2/S3.**
> **S2** (mutation proof + interactive initiation; G3+G4) and **S3** (grounding/research + **loop-back iteration**
> proving the loop loops; G5+G6) are queued, not started. Backout tag `pre-s1`.
> **Then Phase 5 EXTERNAL reach** (install-portability · multi-model) remains after loop-hardening.

> **CURRENT (2026-06-20, BUILD-THROUGH COMPLETE):** **The entire Greater Loop is BUILT + merged + pushed
> (Phases 0–3, `f39f37b`).** Each phase = a real orchestrated foreground-parallel run (Sonnet workers in isolated
> worktrees → octopus-merge → integration gate → **fresh-context `kata-evaluate` PASS 8/8** → merge → push), per
> the no-inline rule. **What now exists end-to-end:**
> - **Phase 0 FOUNDATIONS** (`9e1b27c`): **F1** `tools/gate_emit.py` wires the eval artifacts into the live gate
>   (emits `.kata/{RESULT,footprint,mutation}.json`; dogfooded on the integration gate — closes the dogfood-2
>   residual). **F2** `tools/graph_gen.py` tree-sitter graph runtime → `kata.graph.json` per protocol/graph.md
>   (def/ref/import + PageRank, `call` deferred). Security: sha1→sha256 fixed; CWE-23 path-guard + documented FP.
> - **Phase 1 INITIATION** (`157804f`): **D91** self-contained modules (validator discovers `modules/*/*/SKILL.md`);
>   `modules/initiation/` + **`kata-initiate`** + **`protocol/intent.md`** (PINNED INTENT.md contract). Ingest →
>   classify kind → capture+freeze INTENT.md → interactive target/platform/vault config → dual spec-to-ready control.
> - **Phase 2 CLOSEOUT** (`20dac30`): `modules/closeout/` + **`kata-closeout`** (composes report/understand/handoff/
>   git; consumes F1 `.kata/` artifacts; NEVER gates; human gate satisfied?/commit·push·merge?/run-again·new?) +
>   **`kata-understand`** (opt-in graph-backed comprehension map, git/diff fallback).
> - **Phase 3 CONDUCTOR** (`f39f37b`): **`kata-loop`** thin conductor sequences initiation→harness→closeout, owns
>   the context-carrying loop-back (baseline · understand-map · lessons · prior INTENT); optional (absent ⇒ today's
>   direct run). Root `AGENTS.md` gains a "The Greater Loop" entry.
> Plans: `specs/greater-loop/PLAN-phase{0,1,2,3}.md` + `SECURITY-phase0.md`. Decisions **D87–D91**. Backout tags
> `pre-phase0..pre-phase3` on remote.
> **Adversarial review (2026-06-20, post-build):** a fresh-context red-team found the loop was "skills authored,
> wired by docs, with broken seams" — the sprint-cadence *wired-but-not-connected* anti-pattern partially
> repeating at the Phase-2/3 seam. **All findings fixed (`2d71f2e`):** kata-understand now WRITES `.kata/understand.md`
> (loop-back was reading a never-written file); kata-initiate gained a loop-back-context Phase 1b + `AskUserQuestion`;
> kata-closeout dropped stale "kata-loop not yet built" drift and wikilinks it; kata-orchestrate gained an explicit
> RESULT.json precondition; kata-bootstrap points to kata-loop; D40 marked superseded; INTENT.md/kata.config
> authority pinned. Validator 35/0, pytest 112. **Loop seams now consistent end-to-end (still documentation-wired
> — the Phase 4 dogfood is what proves the live run).**
> **★ NEXT = Phase 4 — the SELF-DOGFOOD TEST of the complete Greater Loop (operator-driven).** Per BUILD-THROUGH
> this is the single next TEST: run a full greater-loop cycle on KataHarness itself — `kata-initiate` (capture a
> real version-up INTENT) → harness (orchestrated) → `kata-closeout` (report + understand-map + **human
> version-select**). Real orchestrated run, never inline (`exercise-harness-for-real`). Likely tags
> `v0.1.0-alpha.2`. **THEN Phase 5** — external reach (install installers / multi-model / optional dashboard).

> **CURRENT (2026-06-20, Phase 0 closed):** **Phase 0 of the Greater Loop is BUILT + merged.** Real orchestrated
> foreground-parallel run: 2 worker subagents (Sonnet) in isolated worktrees → octopus-merge (0 conflict) →
> integration gate → fresh-context `kata-evaluate` **PASS (8/8)** → merged to master `9e1b27c`, pushed.
> **F1 — eval artifacts wired into the live gate** (closes the dogfood-2 residual): `tools/gate_emit.py` composes
> run_result/footprint/mutation_check → emits `.kata/{RESULT,footprint,mutation}.json`; dogfooded on the
> integration gate itself (109 passed, withinFootprint True). Skills wired: kata-evaluate (consumer),
> kata-orchestrate (emits at integration gate), kata-tdd (records mutation proof). **F2 — graph runtime
> operational**: `tools/graph_gen.py` tree-sitter floor produces `kata.graph.json` per protocol/graph.md
> (file/symbol nodes, def/ref/import edges, PageRank, content-hash incremental; `call` omitted = oracle-deferred);
> kata-graph SKILL names it the floor producer. Security: sha1→sha256 (CWE-916, real, fixed); CWE-23 path-guard
> added, residual = documented Snyk FP (operator CLI args, non-shipped tool; see `specs/greater-loop/SECURITY-phase0.md`).
> Plan: `specs/greater-loop/PLAN-phase0.md`. Safety tag `pre-phase0`.
> **★ NEXT (BUILD-THROUGH, no test until Phase 4) = Phase 1 INITIATION:** `modules/initiation/` (own AGENTS.md) +
> `kata-initiate` + frozen `INTENT.md` artifact + interactive target/platform/vault config (install-portability
> config layer folds in) + dual spec-to-ready control (user-says-execute OR grill self-proposes). Then Phase 2
> CLOSEOUT (`kata-closeout` + `kata-understand`, graph-backed by F2), Phase 3 `kata-loop` conductor — straight
> through. Then Phase 4 self-dogfood (the next test).

> **CURRENT (2026-06-20):** **Greater Loop DESIGN is FROZEN** (D87–D90; `.planning/specs/greater-loop/`). The
> wrapper around the harness: **INITIATION** (`kata-initiate` + frozen `INTENT.md` + interactive
> target/platform/vault config) → **HARNESS** (reused) → **CLOSEOUT** (`kata-closeout` + `kata-understand` map),
> sequenced by a thin **`kata-loop`** conductor with a context-carrying loop-back. Modules = `modules/<name>/`
> dirs w/ own AGENTS.md. testing-model folded into F1 (Hermes-grounded); install-portability config layer folds
> into initiation; execution UX = **foreground-parallel** + `subagent-dashboard` brief (build-later).
> **★ BUILD-THROUGH directive (operator):** build the WHOLE Greater Loop (Phases 0–3) continuously, **NO
> intermediate dogfood/test ceremony** — per-phase correctness gates (green/review) still apply; the next TEST is
> the **Phase 4 self-dogfood of the complete loop.** **NEXT ACTION = `kata-plan` partitions Phase 0 (F1 wire the
> dogfood-2 eval artifacts into the live gate · F2 make `kata-graph` actually run via tree-sitter) into disjoint
> slices → orchestrated foreground-parallel build → green+review → CONTINUE straight into Phase 1 (initiation),
> Phase 2 (closeout), Phase 3 (`kata-loop`) without stopping to test.** Then Phase 4 self-dogfood, then Phase 5
> external (install/multi-model). dogfood #2's eval libraries (run_result/footprint/mutation) exist but are
> **unwired** — F1 wires them. Safety tags `pre-dogfood-2` + `v0.1.0-alpha.1` on remote.

> **Dogfood #1 (2026-06-19):** self version-up enforcing `allowed-tools` ran through the full loop (readiness →
> skip-grill → footprint plan → TDD → fresh-context default-FAIL eval **PASS** → report). **Machinery held**
> (regression contract green end-to-end). **Headline finding:** the end-of-run writeup is **not self-sufficient**
> for in-depth evaluation — needs self-emitted `RESULT.json` + footprint manifest + recorded mutation proof
> (→ BACKLOG ★, strong dogfood-#2 candidate). Also: tree-sitter BLOCK too coarse (R1); manual-drive friction
> (R2). See `.planning/specs/dogfood-selfup-1/`.

> **CURRENT (2026-06-19, top of file — older history below is preserved, not current):** **sprint-cadence is
> BUILT + reviewed SHIP** (D78–D85; 11 tasks / 5 waves; commits `43e7c2c`→`e0d0610`). NEW `kata-plan` roadmap
> layer (`ROADMAP.md`), `kata-sprint` (G1–G4 boundary change-control), `kata-report` v1; the
> `delivery: one-shot|incremental` axis + prime-frame sizing (build-grounded: Fable5/Opus4.8/Sonnet4.6 = 1M
> window, ~0.40 effective band). `kata-orchestrate` stays **sprint-blind** (BC2). A fresh-context `kata-review`
> (D15/A5) returned **SHIP**; its one should-fix — `kata-sprint` was wired-but-not-connected — is **fixed**:
> **`kata-bootstrap` is now the boundary router (D86)**, routing a gated boundary → `kata-sprint`. **31 skills ·
> validator 0 · pytest 38 · Snyk 0.** Loop-cognition (β/RS/AO/ML, D74–D77) + D71 Priming-and-Grill shipped
> earlier this session. **Next = the endgame: dogfood version-up on KataHarness itself** (first real
> `delivery: incremental` exercise — will light up the deferred-runtime BACKLOG). See `.planning/HANDOFF.md`.

## Where we are
- Project scaffolded at `C:\Dev\Projects\KataHarness` (git, `.gitattributes eol=lf`). Foundation committed.
- Canonical docs: `AGENTS.md`, `CLAUDE.md` (pointer), `docs/{DESIGN,STANDARDS,TEST-PLAN}.md`, `README.md`
  (versioned skill index). `.planning/{PROJECT,ROADMAP,DECISIONS(16),LESSONS-LEARNED(10),BACKLOG,STATE,STEERING,REVIEW-v0.1}.md`.
- Reference skills vendored (gitignored): `research/reference/{mattpocock-skills,bmad-method}`; GSD local
  at `~/.claude/get-shit-done`.
- **15 `kata-*` skills built**, all `0.1.0/experimental`: the v0.1 ten + `kata-review` + the four
  v0.2-pulled-forward (`kata-diagnose`, `kata-selfhandoff`, `kata-improve`, `kata-write-skill`). 3 remain
  unbuilt: `kata-tasklist` (deferred — redundant with state.json + the plan DAG until workers self-select),
  `kata-zoom-out` (deferred — too thin), `kata-engram` (backlog, gated on a mature engram, D9). The README
  index is the source of truth. (Adversarial-reviewed → `.planning/REVIEW-v0.1.md`; new batch review pending.)
- **2026-06-10 — CPP decoupled (D57) + PortaVault→PokeVault (D58).** CPP is no longer the test medium or
  consumer (history stands; provenance kept). The D16 A/B target is reshaped to **small one-shottable test
  projects**. PokeVault vault is READY (`C:\Users\taurr_nvs748q\PokeVault\PokeVault`, incl.
  `toolkit/agent-sops/`) — KataHarness's install/test home (under `toolkit/`).

## Done so far (this session, 2026-06-06)
- Froze the shared control: CPP `03-DESIGN.md` + `03-01-PLAN.md` (4 locked decisions, 4-task disjoint partition).
- Built the **5 v0.1 execution skills** (`kata-orchestrate/worktree/board/tdd/evaluate`) → `0.1.0/experimental`.
- Ran **Arm A** (KataHarness via Sonnet subagents in CPP worktrees) → GREEN: 244 tests, det build, Snyk 0,
  fresh-context `kata-evaluate` 9/9 PASS, **0 drift / 0 escalations / 0 human interventions** ([[LESSONS-LEARNED]] L9).
- Arm A lives on CPP branch `test/phase3-kata` (worktree `C:/Dev/_kata_armA/integration`).

## Also done (2026-06-06, cont.)
- **A/B verdict recorded: TIE** ([[LESSONS-LEARNED]] L10). Arm B (GSD) matched Arm A on every objective
  metric incl. the identical in-lane auto-fix → execution half on-par, not better; differentiation lives in
  the (frozen-for-both) planning half. User shipping Arm B to CPP `main`.
- **Built the remaining v0.1 planning skills + the adversarial leg** → all `0.1.0/experimental`:
  `kata-grill` (deep, to the L8 standard: GSD-format choice-or-text questions, relentless + doc-grounded,
  doc-baking, convergence criteria, anti-shallow guard + a `resources/DECISION-LEDGER.md`),
  `kata-context`, `kata-design-doc`, `kata-plan` (disjoint file-ownership + wave DAG), `kata-handoff`,
  and **`kata-review`** (adversarial/red-team — the EVALUATE leg the A/B exposed as missing, L10).
- **v0.1 is now skill-complete: 11 skills built** (the 10 + kata-review). README index promoted.

## Active workstream — OPERATING MODES (Spec A1 + A2 + A3 MERGED to master; A4 in progress)

**Spec A1 (foundations) DONE + merged**: skill-conformance validator (`tools/validate_skills.py`), schema-v2
frontmatter (`cost-weight`+`license`+namespaced `tags`), frontmatter-generated README index,
`protocol/config.md`+`protocol/dependencies.md`, `docs/TAXONOMY.md`, Apache-2.0 `LICENSE`. Reviewed HOLD→SHIP.
**Spec A2 (tier families) DONE**: `kata-grill`/`kata-review`/`kata-plan` → 3 tiers each, `kata-diagnose` →
light/full; shared `RUBRIC.md` per family (DRY-by-pointer); `kata-design-doc`/`kata-tdd` got a mode depth-hint;
validator gained tier-family rules. Adversarially reviewed (HOLD→SHIP; surfaced **D33: structural invariants
are never tiered**).
**Spec A3 (bootstrap + wiring) DONE + merged 2026-06-08** (merge `27ca76c`): **`kata-bootstrap`** (run-shape
router — individual/batch/version-up/advanced as PRESETS over the mode axis; D24c ladder; run-shape-relevant
interview) + new light **`kata-readiness`** (harness-health + target-readiness + re-entrant config detection) +
**`kata-orchestrate`** reads `kata.config`, resolves family→tier (fallback Standard/D25) with a **fail-closed
load-guard** (GB12). `kata.config` schema gained `runShape`+`target` (version-up). Grilled GB1–GB13 → promoted
to **D34–D46**; adversarially reviewed **SHIP** (`.../modes-A3-bootstrap-wiring/REVIEW.md`). **24 skills**,
validator green, 12 tests. Versioning **policy A** (hold all skills at 0.1.0 till v0.1 ships, then bump-on-modify).
**A4 (version-up + kata-graph) — DONE + MERGED to master 2026-06-08 (merge `de4b0ee`, reviewed SHIP; 25 skills,
validator green, 13 tests)**: DESIGN frozen (`.planning/specs/modes-A4-version-up/DESIGN.md`);
grill ledger fully converged (GB1…GB10 + HOLD#1/#2/#3 resolutions; coherence audit PASSED;
`.planning/specs/modes-A4-version-up/GRILL-LEDGER.md`); A4-GB decisions promoted to **D47–D56** (this
session). Scope: **`kata-graph`** (tree-sitter-floor, feature-agnostic cached `kata.graph.json` contract,
feature-seeded ~3k-token digest, pluggable grep/tree-sitter/Graphify-MCP backend) + **version-up wiring**
(grill Phase 0 ingest, footprint-scoped disjoint ownership with defer-first + escalate-rare protections,
full-suite-green regression contract) + **`kata-orchestrate` frontier/async-escalation supersession** (rolling
DAG-frontier dispatch, async park/drain/hard-wait, structured escalation payload in its own contract
`protocol/escalation.md`). Deferred clean: Obsidian KG story (own spec under kata-understand, D54);
engram-mediated escalation (D56). Then Spec B (bake-off), `design` module. Parallel outstanding: D16
planning-varied A/B.


Brainstormed a major new capability: cost/effort/thoroughness **operating modes** (Essential/Standard/Advanced),
all one-shot, consistency-first. Full design in `docs/MODES-DESIGN.md`; vocabulary in `CONTEXT.md`; skill
token-weights in `.planning/SKILL-COST-RATINGS.md`; decisions D17–D23. Prior art researched (FrugalGPT cascade,
Cursor/AgentHub best-of-N, Claude `effort`, GitHub Spec Kit) — pieces exist; our synthesis (skill-set tiering +
escalation-with-reuse + Improvement-Kata version-ups) is the contribution.

## 2026-06-11 (evening session) — D59 + sprint-cadence spec opened
- **D59 — model routing Opus → Fable 5** for deep/judgment work (`claude-fable-5`); Sonnet stays the
  lightweight workhorse; 8 skill `model:` pins flipped to `fable`; test arms remain Sonnet (D14/D57).
- **NEW capability spec opened: sprint-cadence** (`.planning/specs/sprint-cadence/`) — user-requested
  bootstrap toggle between **one-shot** (current loop) and **sprint** execution (plan partitions the project
  into GSD-style sprints; run one sprint → gate → output → user course-corrects via grill → re-enter, same
  or new session). RESEARCH.md maps the plumbing (config `cadence` field, bootstrap question + re-entrancy,
  kata-plan roadmap layer, boundary handoff/report, delta-grill; orchestrate ideally sprint-blind; sprint
  N≥2 reuses the A4 version-up regression contract). GRILL-LEDGER.md holds **10 OPEN branches (SC-GB1–10)**
  with recommendations — **user answers them next session.** Framing rule: each sprint is a one-shot; the
  boundary is the scheduled re-plan event (spine #2 compatible).

## 2026-06-15 — sprint-cadence grill CONVERGED + engram registry created (uncommitted until 2026-06-18)
- **Sprint-cadence ledger fully resolved (SC-GB1–10 + engram cross-cut).** Knob = **`delivery: one-shot |
  incremental`** (unit = sprint); three-layer freeze (DESIGN north-star / ROADMAP boundary-amendable / sprint
  PLAN immutable) + Boundary Change-Control Protocol G1–G4; sequencing A+C (re-entrant `kata-bootstrap` routes,
  `kata-orchestrate` stays sprint-blind, NEW thin `kata-sprint`); three-tier state w/ derived `.kata/` cache
  rebuilt from git; scoped delta-grill course-correct (default always-stop); prime-frame sizing primitive
  (refines D8); sprint N≥2 = version-up vs most-recent-green baseline; bake-off trimmed; **D16-first LOCKED**.
- **`protocol/engram.md` CREATED** — engram plugin contract + seam registry (E1–E21, C1–C6, backend binding
  incl. external-backend clean-room). Adversarially reviewed (HOLD→hardened). Freeze-gate audit on sprint-cadence
  returned HOLD with must-fixes (roadmap-layer is NET-NEW in kata-plan; pin tunables; D8 supersession; etc.).

## 2026-06-18 — loop-cognition spec OPENED + CONVERGED (this session)
- **NEW umbrella spec `loop-cognition`** (`.planning/specs/loop-cognition/{RESEARCH,GRILL-LEDGER}.md`): three
  entangled loop enhancements — **RS** in-loop research subagent (escalation-routed, grounding-gated,
  fresh-context no-write `kata-research`), **AO** agent orientation (orchestrator-assembled stable→context→
  volatile tiers; vertical rollup + `kata-graph` lazy adjacency pointers; `protocol/orientation.md` +
  `kata-orient`), **ML** managed learning (candidate-skill distillation → 2-stage gate → human promotion
  `kata-promote`; second-brain LEARN feed as Karpathy-LLM-Wiki-pattern synthesis; progressive autonomy
  `engram.autonomy` maturity∧config AND-gate, grounding never bypassed).
- **Hermes Agent (Nous) baked off** — verdict: borrow mechanisms (autonomous distillation, protected
  head+tail compaction, tiered prompt assembly, `.usage.json` telemetry), keep OUR gates (default-FAIL +
  human promotion). Their no-gate skills + emergent-plan compaction = the failure modes our spine prevents.
- **LC-GB1–9 + RS-GB1–3 + AO-GB1–3 all RESOLVED + user-confirmed.** Sequencing = **Path 2**: D16 first, build
  the LEARN-only feed pipeline (β) in parallel (it's an engram *prerequisite*, low-drift, observe-and-emit,
  zero CONSULT). Artifact map recorded (NEW: kata-research/kata-orient/kata-promote + protocol/orientation +
  protocol/wiki-synthesis; EXTEND: evaluate/review/selfhandoff/orchestrate/handoff/improve/graph).
- **Freeze-gate audited HOLD→SHIP** (fresh-context Opus; MF1–MF3 + SF1–SF4 resolved; re-confirm SHIP).
  **DESIGN FROZEN** (`loop-cognition/DESIGN.md`); decisions promoted **D60–D69**; β ingested into ROADMAP
  (∥ D16), rest post-D16.
- **D16 RETIRED as an RCT + Priming-and-Grill resolved (D70/D71/D72, L11).** Two A/B attempts (easy + hardened
  `wordfreq`) proved the autonomous deterministic-gate A/B can't isolate the grill (4/4→10/10 gate passes; grill's
  human-engine is off without a human). **Grill is now an OPTIONAL human certainty layer over the priming prompt,
  with an autonomous-reliability floor** (default-FAIL + RS + assumption-log); grill ledgers are a PRIMARY
  cognitive-fingerprint feed. **Autonomous reliability is demonstrated; v0.1 no longer gated on an RCT → the
  D16-first lock is dissolved → the full build is UNBLOCKED.**
- **D71 Priming-and-Grill wiring ✅ DONE 2026-06-18** (spec `priming-and-grill`, DESIGN FROZEN; D73 + M1–M3):
  grill **skip** rung (`tiers["kata-grill"]="skip"`) + bootstrap grill-depth dial (Phase 1.5) + readiness Scope-3
  prompt-richness recommendation + orchestrate skip-floor branch + **`kata-defer` built** (DEFERRED.md parking +
  ASSUMPTIONS.md grill-skip log; **25→26 skills**) + grill↔RS spectrum doc'd. Validator 26/0, pytest 15.
  **Caveat:** RS slot doc'd/wired-for, lit in the loop-cognition phase. **Pending: fresh-context `kata-review`.**
- **β LEARN feed ✅ DONE 2026-06-18** (D74 + BP1/BP2): `kata-improve` emit-only sub-mode (E6) → Karpathy-LLM-Wiki
  synthesis pages per the schema in `protocol/engram.md` (`produced-by: loop`); **zero CONSULT** (BC2),
  **redaction-gated** (C3), no-op without `engram.learnFeed.dir` (BP1/BC1); `engram.md` now validator-enforced
  (BP2). Validator 26/0, pytest 18. **Pending: fresh-context `kata-review`.**
- **RS ✅ DONE 2026-06-19** (D75; RS-GB1/2/3): `kata-research` escalation-routed fresh-context **no-write**
  researcher (`research-needed` kind); **L2 grounding gate** = injected-knowledge mode of `kata-evaluate` +
  `kata-review` RUBRIC (never bypassed, D33); orchestrator folds GROUND findings via deliberate superseding
  re-plan, else REJECT/escalate-to-human. `kata/module/research`; **27 skills**. Validator 27/0, pytest 21.
  **Pending: fresh-context `kata-review`.**
- **AO ✅ DONE 2026-06-19** (D76; AO-GB1/2/3 + user extensions): `kata-orient` (spine, read-only) three-tier
  launch orientation + `protocol/orientation.md`; **task-type-aware**, contextually-derived **pointers+callouts**
  from standard markdown, **smart questioning routed** (answer-inline / research-needed→RS / human→grill),
  `kata-handoff` Orientation tie-in (aligned both sides). **28 skills.** Validator 28/0, pytest 24.
- **ML ✅ DONE 2026-06-19** (D77; L5/L6): `kata-promote` stage-2 human promotion gate (AskUserQuestion);
  agent-distilled candidates (STANDARDS §1.3, `<agentSkills.dir>/candidates/`, not universal) → grounding gate →
  human gate; `engram.autonomy` AND-gate default **always-human**; candidate lifecycle in `state.md`. **29 skills.**
  Validator 29/0, pytest 27. **⇒ loop-cognition COMPLETE (RS + AO + ML).**
- **NEXT (see HANDOFF §4 THE PLAN):** (1)–(4) ✅ D71/β/RS/AO; (5) ✅ RS+AO validation; (6) ✅ ML →
  **loop-cognition done.** **(7) ✅ sprint-cadence DESIGN FROZEN 2026-06-19** (D78–D85; freeze-gate HOLD→SHIP) →
  **BUILD it next** (NEW: `kata-plan` roadmap layer + `kata-sprint` + `kata-report` v1; needs PLAN + approval);
  **(8) dogfood version-up on KataHarness itself** (the endgame: build fully → full tests → self-improve). CONSULT/full-autonomy
  stay gated on a mature engram.

## Next action — RS → AO → ML (D16 lock dissolved by D70; D71 + β DONE 2026-06-18)
> ⚠️ The numbered list below predates D70 and is **superseded** — it described the D16-first sequencing that no
> longer applies. Authoritative next step: **RS (research subagent), then AO, then ML.** Kept for provenance.
0. **Answer the sprint-cadence grill ledger** (`.planning/specs/sprint-cadence/GRILL-LEDGER.md`, SC-GB1–10)
   — note SC-GB10 proposes: freeze the sprint DESIGN now, build after D16.
1. **D16 planning-varied A/B (the v0.1 validation gate; ROADMAP-sequenced FIRST):** prove the grill
   differentiates — Arm A plans via `kata-grill`→`kata-design-doc`→`kata-plan` vs a GSD baseline. **Target
   reshaped (D57): small one-shottable greenfield projects in a dedicated test directory** (repeated paired
   measurements, not one big task). Needs its own spec grill (`.planning/specs/`) — TEST-PLAN v1 is superseded.
2. **Obsidian-KG / kata-understand spec** — emit+ingest over the `kata.graph.json` contract (D54/D55).
   **PokeVault gate SATISFIED (D58)** — vault is git-versioned/durable, so no freshness pressure; sequenced
   AFTER D16 per ROADMAP + the 2026-06-10 adversarial review of the "grill-KG-first" option (REJECTED:
   premise decay — durable vault; post-v0.1 inversion; rework exposure from an unvalidated grill).
3. **Spec B — bake-off** (anytime; composes with version-up, D37).
- **Backlog:** A3-review carry-overs (`kata-readiness` harness-vs-target wording for the KG spec; `tools/`
  example-`kata.config` check) · `kata-defer`/`kata-understand`/`kata-tasklist`/`kata-engram` · adapters ·
  **set a git remote before public release** (still local-only).

## Model per stage
Build KataHarness → **Claude Fable 5** (`claude-fable-5`, D59 — supersedes the Opus routing). D16 test
arms → **Sonnet** (constant across arms — D14 principle, survives D57/D59). I pin subagent models on
spawn; operator sets main-session model via `/model`.

## Open decisions for the user
- Confirm D16-first sequencing (adversarial review recommends it; Option D "grill-KG-first" was reviewed
  and REJECTED 2026-06-10). Suite/plugin packaging shape. Git remote before public release.

## Session Continuity
Last session: 2026-06-18. Stopped at: loop-cognition grill fully converged + user-confirmed (LC-GB1–9,
RS-GB1–3, AO-GB1–3); STATE/HANDOFF refreshed; checkpoint commit of 2026-06-15 (sprint-cadence converged +
engram.md) + 2026-06-18 (loop-cognition spec) work. Resume file: `.planning/HANDOFF.md` (read it first).
**Immediate next:** the session resolved the **Priming-and-Grill architecture (D70/D71/D72, L11)** and
**retired D16 as an RCT** — autonomous reliability is demonstrated, so the full build is UNBLOCKED. Read
`.planning/HANDOFF.md` (rewritten for this hand-off) — §4 THE PLAN: wire D71 → build β → RS/AO/ML → freeze
sprint-cadence → dogfood version-up. loop-cognition DESIGN is FROZEN (D60–D69). The user will compact + orient
a fresh session from the handoff.
