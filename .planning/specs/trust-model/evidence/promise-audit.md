---
spec: trust-model
artifact: evidence dossier 1/4 — exhaustive promise audit
date: 2026-08-16
provenance: read-only survey agent, committed verbatim-in-substance by the conductor; conductor
  spot-verified the verdict classes, not every row — re-verify any single row before it becomes
  load-bearing in a DESIGN
baseline: grill/dispatch-seam @ fea7ccb (master de8578c)
---

# Evidence 1 — the promise audit (114 rows)

## What actually executes in this repo, exhaustively

| Live surface | Trigger | Fail posture |
|---|---|---|
| `tools/validate_skills.py` (23 `@check` functions) | GitHub Actions `gauntlet` on push-to-master / PR / dispatch (`.github/workflows/ci.yml:39-41`) + manual `tools/scripts/gauntlet.py` | hard-fail |
| `uvx ruff check` / `pytest` / `pytest -m integration` | same workflow | hard-fail |
| `adapters/claude/hooks/kata-sessionstart.py`, `kata-precompact.py`, `kata-gauge-check.py` | Claude Code host events, only if installed | **fail-soft** |
| `adapters/claude/statusline.py` / `statusline_chain.py` | host statusline tick | fail-soft |

No git hooks installed. No process launches, schedules, or gates an agent. Every "load-guard",
"gate", "preflight", and "engine" named in `protocol/` and `skills/` is a **sentence addressed to
an LLM**; only 11 of 62 `tools/*.py` modules have a `__main__`, and skills reference tool CLIs
exactly 7 times across the whole `skills/` + `modules/` tree.

Verdicts: **FACT** (machine check runs on a live path) · **PARTIAL** (runs but covers less than
asserted) · **PROSE** (instruction to a model) · **FACADE** (code exists + unit-tested, zero
production callers, sentence reads as machinery) · **FALSE** (contradicted by evidence).

## The headline counts

Across 114 audited promises: the FACT rows are almost exclusively **document-integrity checks run
by the gauntlet** (clause-pins, fingerprints, bump-on-modify, README sync, allowed-tools shapes,
no-model-ids, protocol-folder registration, `test_exec_safety.py`'s shell=True regression rule)
plus the three fail-soft hooks. ~25 rows are FACADE (correct, tested engines with zero production
callers described as running). 5 rows are FALSE.

## The FALSE rows

1. **`config.md:35` `contextTrigger`** — "the conductor trigger fraction override; default 0.70
   when absent." The key appears in **zero** Python files; the live hook hardcodes
   `kata_gauge.DEFAULT_TRIGGER_FRACTION` (`kata-gauge-check.py:173`) and never opens `kata.config`.
   The advertised dial for the flagship walk-away feature is not connected.
2. **`config.md:31` "`on` = the P1 consuming mode, now LIVE (M4-P1)"** — no scheduler process
   exists; `kata_risk.should_trigger` has no production caller. "LIVE" describes prose.
3. **`config.md:144` `delivery` "Fail-closed (D45): the load-guard validates `delivery` strictly"**
   — `validate_core_config` does not validate `delivery`; no other validator exists.
4. **`observability.md:18` reports at `.kata/reports/<runId>-…`** — no code mints a `runId`
   anywhere; the only reference reads a key nothing writes (`kata_telemetry.py:1436`).
5. **`README.md:89` "frozen plans workers structurally cannot drift" · `README.md:212-213` "that
   promotion gate is built and validator-enforced" · `README.md:60-61` (fresh-context presented
   unqualified) · `kata-review/RUBRIC.md:55`+`kata-evaluate:110-111` "enforced by the orchestrator
   integration gate (see BACKLOG)"** — each contradicted in-tree (no structure exists; the
   validator has no promotion check and `kata-promote:46` says it never sees candidates; the skill
   itself says freshness "is NOT verified and NOT recorded anywhere"; the "enforcing" gate is
   identified as unbuilt by its own citation).

## The 10 most consequential facade rows (ranked by reader-conclusion vs. reality gap)

1. `README.md:89` "workers **structurally** cannot drift" — no dispatch seam, no worktree
   enforcement, no ownership check, no per-task record. Drift is graded after the fact by prompt.
2. `README.md:212-213` promotion gate "built and validator-enforced" — contradicted twice in-tree.
3. `README.md:60-61` fresh-context evaluator presented to readers with no qualifier the skill
   itself carries.
4. `config.md:193` + `kata-orchestrate:38-50` the Core load-guard — `validate_core_config` has no
   caller, no CLI; zero `python -c` invocations exist in skills. Every downstream "load-guard
   STOP" row inherits this hollowness.
5. `config.md:32` `roles` "**wired** … code-enforced, not advisory" — the only contract-layer text
   that explicitly draws the code-vs-advisory distinction, and it lands on the wrong side.
6. `config.md:43,45,47` "(engine-enforced)" ×3 — implemented correctly in
   `kata_preflight.run_preflight`, which never executes. The badge trains readers to trust labels.
7. `config.md:35` `contextTrigger` (see FALSE row 1).
8. `iac-safety.md:297-299` the "| Claim | Verified surface |" table — a verification ritual whose
   cited proof is a function with no caller. The ritual itself is the facade.
9. `kata-evaluate:219` "soundness never rests on orchestrator compliance" — its evidence artifact
   is produced by a callerless module and its own escape clause (`:229-232`) makes it N/A "every
   run today."
10. `kata-review/RUBRIC.md:55` "enforced by the orchestrator integration gate (see BACKLOG)" — the
    word *enforced* applied, in two files, to a gate the same sentence identifies as unbuilt.

## The counterweight — what is genuinely FACT, and the distribution finding

Doc integrity is real and runs in CI. `test_exec_safety.py` genuinely blocks new `shell=True`
sinks in `tools/`. Three fail-soft hooks run live. And a striking set of files state their own
non-enforcement **precisely and correctly**: `orchestration.md:58-64`, `engram.md:153-158`,
`steering.md:45-50`, `authored-artifact-gate.md:44-52`, `recall.md:120-134`,
`validation-misses.md:92`, `DETERMINISM-DOCTRINE.md:81-83`, `kata-evaluate/SKILL.md:27-33`.

**The distribution finding (the audit's core conclusion):** the failure is not that the repo
cannot tell the truth about itself — it is that the honest labels are concentrated in the deep
protocol layer, while the config schema, the orchestrate preconditions, and the README use the
vocabulary of machinery ("wired", "engine-enforced", "code-enforced", "structurally", "LIVE",
"automatically") for the same dead code.

## Selected per-file rows (retained for design use; full sweep was 114 rows)

- `prime-directives.md:13-18` PD-1 "complete means wired end-to-end" — PROSE, and self-contradicted
  by ~25 FACADE rows in this audit; the *text* is tamper-evident (FACT).
- `prime-directives.md:117-119` "nothing defends the validator's own source mechanically" — FACT
  (honest residual, correctly stated).
- `exec-safety.md:27-29` structured-argv/shell=False — FACT for `tools/` code (regression-tested in
  the gauntlet); PARTIAL for the registry (a new `shell=False` external sink is not detected); 5 of
  17 registry rows describe modules with zero production callers.
- `board.md:45-47` run-isolation MUST (rotate at run start) — PROSE; text pinned (FACT); no run-id
  exists so a cross-run board is undetectable.
- `observability.md:27,58,92` "malformed row RAISES / never treat null as 0 / treat-as-triggered" —
  FACADE (implemented, clause-pinned, whole suite has zero production callers).
- `kata-evaluate:46` mutation.json `allNonVacuous` MUST be true — PARTIAL, and the **strongest real
  evidence chain in the harness** (gate_emit has a `__main__`; consumption is an LLM reading JSON).
- `kata-evaluate:133-136` "the orchestrator runs `tools/grounding_gate.py`" — FALSE as written: the
  module has no `__main__` and cannot be "run" as stated.
- `kata-bootstrap:250` "does NOT re-validate (that is kata-orchestrate's fail-closed load-guard)" —
  FACADE by deferral: validation is deferred to a guard that never runs.
- `DETERMINISM-DOCTRINE.md:81-83` "Skill-level enforcement is NOT built — a named open follow-up"
  — FACT; the best-practice disclosure in the repo. The DET-01..14 table is PARTIAL (accurate at
  verification time, no regression guard; nothing detects a 15th violation).
- `README.md:53-55` the 44/57 checkpoint measurement — FACT, honestly scoped as a one-time
  retroactive scan.
- `README.md:235-241` durable board / restore — FACADE for the trail snapshot path in live terms
  (writer orphaned), FACT for the PreCompact hook when installed, PARTIAL for /kata-resume
  (real code, prompt-triggered).

---

## Guardian relabel pass — truth-in-the-labels (Loop D / W9, guardian-relabel-pass)

**What this section is.** The audit above graded each promise in the internal FACT/PARTIAL/PROSE/
FACADE/FALSE vocabulary as of the burn's fork (`fea7ccb`). This section re-grades every FALSE and
FACADE row in the **Guardian scale** (DESIGN §6.2 — the user-facing vocabulary), **with the
mechanism cited where the wiring actually landed this burn** (TM-A1: remediation THROUGH the loop,
never out-of-band edits). A row whose wiring did NOT land keeps an honest **downgrade** grade
(`Honor-system` · `Dormant` · `Broken`) and routes to its backlog home — a downgrade asserts no
trust and needs no citation (EV-1 residual 3). A row that graduated to a machine-checkable trust
grade carries a live check in the `tools/badge_registry.json` entry that covers it (EV-1 forward
direction); the two such lines below are the only new claim sites this pass introduces.

**The two rows that GRADUATED to a claim term this burn** (each backed by a live check registered in
`tools/badge_registry.json`, same commit):

- **R-ENF** — `README.md:89` "workers **structurally** cannot drift" + the whole "no dispatch seam,
  no worktree enforcement, no ownership check, no per-task record" facade: the dispatch seam
  (`tools/kata_dispatch.py`, W3 seam-engine `4ee15af`/`58732cb`) now mints a per-task record with a
  `SPAWN` cursor line and refuses an unfrozen-plan mint (`test_mint_refuses_unmet_governor_state`),
  and the fail-closed pre-hook (`adapters/claude/hooks/kata-seam-guard.py`, Loop C `6dddf32`,
  integration `0301955`) **denies a record-less `Agent` launch at `PreToolUse`**. Guardian grade:
  **Verified (intercepting) — where installed** · check `test:tools/tests/test_seam_guard.py::test_recordless_agent_call_denied`
  · corroborated by `probe:deny-tripwire` (active, G29/G30) and CI run `32028410601` (both platforms,
  Loop-C tip). Honest qualifier carried (§11): enforcement is **install-gated** — a host without the
  guard in `~/.claude/settings.json` runs `Honor-system` (nothing denies a bypass); the burn's own
  conductor dispatches ran Honor-system for exactly this reason.
- **R-ROLE** — `config.md:32` `roles` "**wired** … code-enforced, not advisory" (the one contract
  line that drew the code-vs-advisory distinction and landed on the wrong side): role→rung
  resolution is now consumed at mint by the seam governor (`kata_dispatch._ROLE_CLASS` /
  `GOVERNOR_GRADE`, role-class-scoped fail-closed rung). Guardian grade: **Verified — role resolution
  enforced at mint** · check `test:tools/tests/test_kata_dispatch.py::test_mint_wires_the_role_resolver`.

**Every remaining FALSE/FACADE row — honest downgrade + backlog route** (grades here are downgrades,
not claim terms; the "old" column is the audit's internal verdict):

| Audit row | Old | Guardian grade (mode) | Mechanism / why unwired | Route |
|---|---|---|---|---|
| `config.md:35` `contextTrigger` walk-away dial | FALSE | **Broken** | the key is absent from **every** Python file (re-verified 2026-08-17); the live gauge hardcodes `DEFAULT_TRIGGER_FRACTION` and never opens `kata.config` — not built this burn | backlog: M4 walk-away dial |
| `config.md:31` `on` = "P1 consuming mode, now LIVE" | FALSE | **Dormant** | no scheduler process exists; `kata_risk.should_trigger` still has no production caller — not built this burn | backlog: M4 consuming mode |
| `config.md:144` `delivery` "load-guard validates strictly" | FALSE | **Broken** | `validate_core_config` still does not validate `delivery` and no other validator exists | backlog: config-schema load-guard |
| `config.md:193` + `kata-orchestrate:38-50` Core load-guard | FACADE | **Broken** | `validate_core_config` has **zero call sites** in `tools/*.py` (re-verified 2026-08-17); the seam governor is a *different*, live load-guard for plan/governor state (`test_mint_refuses_unmet_governor_state`), it does not resurrect this function | backlog: config load-guard wiring |
| `kata-bootstrap:250` "defers to kata-orchestrate's fail-closed load-guard" | FACADE | **Broken** | same family — validation is deferred to `validate_core_config`, which never runs | backlog: config load-guard wiring |
| `config.md:43,45,47` "(engine-enforced)" ×3 | FACADE | **Honor-system** | `kata_preflight.run_preflight` still has **no production caller** (re-verified 2026-08-17: referenced only in docstrings/skill prose) | backlog: preflight wiring |
| `README.md:212-213` promotion gate "built and validator-enforced" | FALSE/FACADE | **Broken** | no promotion gate was built this burn; `kata-promote` still sees no candidates and the validator has no promotion check | backlog: skill promotion gate. (README source is conductor's G2 regen — out of grant) |
| `README.md:60-61` fresh-context evaluator (unqualified) | FACADE | **Honor-system** | `kata-evaluate` genuinely runs as a no-write subagent, but freshness "is NOT verified and NOT recorded anywhere" (the skill's own qualifier); presenting it unqualified is the facade | README G2 regen carries the qualifier; kata-evaluate already carries it |
| `kata-review/RUBRIC.md:55` + `kata-evaluate:110-111`/`:192` "enforced by the orchestrator integration gate" | FALSE/FACADE | **Broken** | the cited "scheduled wiring-completeness build gate" is a *different* mechanism from the seam guard and was **not** built this burn; the word "enforced" still applies to an unbuilt gate | backlog: wiring-completeness build gate. **UNMET LEG:** the RUBRIC/evaluate source lines still carry "enforced" (out of grant — surfaced) |
| `kata-evaluate:219` "soundness never rests on orchestrator compliance" | FACADE | **Honor-system** | the orchestrator-independent evidence substrate (the cursor + git-durable trailers) is now LIVE (W3–W4), but the gate does not yet *consume* it — the fact-table→final-gate hop is honestly unwired (Loop B record) | backlog: gate-consumption wiring (BL-N19 route) |
| `iac-safety.md:297-299` + the `iac_apply` sibling table headers | FACADE | **Honor-system** | `iac_apply` is a declared n=0-live surface; wiring did NOT land this burn (finding 8, re-read) — the two rows stay in `pending_graduation` per ruling G27 | BL-N24 / iac follow-up |
| `observability.md:27,58,92` read suite ("RAISES / never null-as-0 / treat-as-triggered") | FACADE | **Honor-system** | implemented + clause-pinned; the cursor-consumer migration (D-21) wired the *parsers*, but a production consumer of the ledger read-suite is not established this burn | BL-N16 substrate |
| `observability.md:18` reports at `.kata/reports/<runId>` | FALSE | **RESOLVED this pass** | `<runId>` is now minted by `kata_dispatch.run_start` (W3; dogfood run `run-20260817T034343Z-e3b50e43`); `protocol/observability.md:18` updated to cite the seam — no longer "a key nothing writes" | — |

**The audit's ~25 unenumerated FACADE rows** that are not individually listed above fall in the
**callerless-engine family** (`validate_core_config`, `kata_preflight.run_preflight`, the
`kata_telemetry` read-suite, and the iac verification tables): each carries **`Honor-system`** until a
production consumer *and* a live check land, and each routes to its backlog home (config load-guard /
preflight / BL-N16 / BL-N24). None is graded a claim term, so none is a facade-with-a-footnote.
EV-1 (`check_badge_registry`) is what keeps this honest going forward: a future line that spells a
Guardian trust-claim term on any of these surfaces fails the gauntlet on the commit that adds it,
until a human classifies it.
