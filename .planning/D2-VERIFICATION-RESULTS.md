---
date: 2026-07-25
kind: verification-sweep
baseline: branch `docs/mergeback-ingest-itemization` @ `600eb4c` (master untouched at `fcb0338`)
method: fresh-context READ-ONLY subagents, evidence-cited, no-write
status: IN PROGRESS — batch 1 of 3 recorded
---

# D2 VERIFICATION SWEEP — does it actually work HERE?

The `alignment-report.md` §1 asserts 14 subsystems are "already aligned" with the fork. **An alignment
claim is not evidence our side works.** This is the evidence.

**Vocabulary:** FIRED (executed, artifacts prove it) · WIRED-UNFIRED (reachable, no execution
evidence) · BUILT-ONLY (present but nothing reaches it) · BROKEN (reachable and does not work) ·
INERT (structurally cannot act today).

---

## ⭐ THE CROSS-CUTTING FINDING

> **Three of the five gaps in batch 1 share one root cause: the invariant lives in a `SKILL.md`
> sentence with no executable owner.** Every subsystem that HAS a Python owner
> (`check_evaluator_no_write`, `gate_emit` `parsedCounts`, the benchmark floor-fail, `Kata-Checkpoint`
> trailers) shows hard FIRED evidence.

This is our own §6b script-vs-context axis pointing back at us. We told the fork that a rule-decidable
mechanism ported as prose is a determinism regression — and we have the same class of gap internally,
in the *original* direction rather than the ported one.

---

## Batch 1 — D2-1 … D2-5

### D2-1 — Spine + outer loop · **spine FIRED · `kata-loop` conductor BUILT-ONLY**
Real traversal is proven: `.kata/RESULT.json` carries `parsedCounts`, a key produced **only** by
`gate_emit.py:118` — so it came from the canonical producer, not a hand edit. A genuine loop-back
happened once (`.planning/specs/loop-hardening/REPORT-s3b.md:29-48`: cycle 1 `f72a3bb` → closeout →
`kata-initiate` Phase 1b → cycle 2 `222cc7e`, graded 7/7 by a separate read-only grader). 60 commits
carry real `Kata-Checkpoint:` trailers.

**But the `kata-loop` conductor itself is on no exercised path.** `/kata-start` routes to
`kata-initiate`; no slash command anywhere dispatches `kata-loop`. `kata-bootstrap` only *points at*
it. The loop-back that did happen ran through `kata-initiate` Phase 1b directly.

⚠ **`.kata/` and `INTENT.md` are gitignored** (`.gitignore:7,9`), so `git log -- .kata` is empty —
**every piece of spine evidence is mutable on-disk state with no git audit trail**, and the three
artifacts are from three different runs, none matching HEAD.

### D2-2 — Modes / tier families · **INERT**
Standard-as-fallback exists in exactly two places, both prose (`protocol/config.md:8`,
`kata-orchestrate/SKILL.md:33`). **No Python reads `mode` or `tiers` from the config at all** — the
config is parsed only for `preflight`, `roles`, `inlineEval`, `models`, `contextAutonomy`, `advisor`.
`mode` is a *parameter* callers pass to `kata_models.resolve()`, never read from disk. No test pins
the fallback.

Live corroboration that nothing reconciles it: `kata.config` sets `tiers: {kata-grill: essential}`
while `INTENT.md` records `grillDepth: standard`. **Nothing on any surface would notice.**

### D2-3 — D33 never-tiered invariants · **BUILT-ONLY (convention, not enforcement)**
No test pins that a tier variant cannot weaken a structural invariant. `check_evaluator_no_write`
covers the grader set — but none of those three is a *tiered* family, so it proves nothing about tier
variance. `check_tier_family` checks tags and RUBRIC existence only.

The invariants *are* present as prose in the cheap tiers today (`kata-plan-essential/SKILL.md:40-44`,
`kata-grill-essential/SKILL.md:46-49`) — the convention is held, not broken. **But deleting either
line keeps the validator green — verified: 49/0/0 and 53 tests still pass.**

### D2-4 — Default-FAIL fresh-context evaluator · **no-write FIRED · fresh-context BUILT-ONLY**
The no-write half is real and enforced: `validate_skills.py:140-158`, and the tree complies
(`kata-evaluate/SKILL.md:14` → `allowed-tools: [Read, Grep, Glob, Bash]`), pinned by 7 tests.

**The fresh-context half has no attestation anywhere.** Dispatch is prose
(`kata-orchestrate/SKILL.md:1414`). Grepping `tools/` for fresh-context vocabulary yields **only
comments and docstrings — zero executable check**. No telemetry field records evaluator identity or
context state. ⚠ And `Bash` is in the evaluator's allowed-tools, so the structural guard covers the
`Write`/`Edit` tool *names* while a shell write remains possible.

### D2-5 — RESULT.json staleness · **🔴 BROKEN — GAP CONFIRMED**
`kata-evaluate/SKILL.md:164` guards **absent or malformed only**. No staleness, freshness, or identity
language exists in the file. `run_result.py` is a pure emitter — `build_result` takes SHAs as
caller-supplied strings and never touches git. **Repo-wide grep finds zero code comparing
`resultSha`/`baselineSha` to `git rev-parse HEAD`.**

**Live proof the failure mode is active right now:** `.kata/RESULT.json` carries
`resultSha: 159fc9b`; HEAD is `600eb4c` — **37 commits later**. `.kata/mutation.json` is from
2026-06-26 and still asserts `allNonVacuous: true`, which `kata-evaluate` rubric item 1 credits for
any code-bearing run. **A gate run today reads all three as valid.**

Worse, it is by design: rubric item 9 explicitly **exempts** RESULT.json from reproduce-don't-trust
("Raw test/build output captured by `gate_emit` is *primary*, not derived").

**This confirms MC-05's claim for our tree and raises T-04's priority.** MC-05 is no longer a
speculative lack-fill; it closes a demonstrated live defect.

---

## Batch 2 — D2-6, D2-8, D2-9, D2-11, D2-14

### D2-6 — Contract edges / freeze-float M1 · **INERT here · and our own record is WRONG**
Zero `builds_against` keys in any frozen plan (the one hit is a fenced *schema example*,
`PLAN-p2-float.md:184`). Zero contract dirs, zero `contract-gate.json` ever written, zero float
trailers. The only call path is LLM-executed prose — **no Python caller** of
`contract_gate.verify_contract_gate` outside its 40 tests.

⚠ **But "zero edges exist in any run today" — which I repeated into `MERGEBACK-INGEST.md` — is
REFUTED.** `DECISIONS.md:2284` (**D145, 2026-07-04**) records a real `builds_against: stats@pin` edge
on a scratch repo, corroborated by the committed ledger row `telemetry-ledger.md:30` and a board line
(`float trio: pin MATCH, stubs 0, danglers 0, suite 15/15`). **D140 said "zero edges" on 2026-07-02
and was never amended after D145 two days later** — so the stale claim propagated from our own
DECISIONS log into the outbound package.

Honest residual: the scratch repo is **deleted**, so what survives is a self-report plus a telemetry
row — n=1, toy-scale, `calibration:true`, **not reproducible**. The float is untested-in-practice
*here*, which was the substance of the claim even though the wording was wrong.

### D2-8 — Restore-hardening · **substrate FIRED · restore() WIRED-UNFIRED · 🔴 LIVE DESTRUCTIVE HAZARD**
Substrate is real: **22 commits** carry genuine `Kata-Task:` trailers; `refs/kata/trail` holds ~20+
board snapshots through **today**. But `kata_restore.restore()` has **no Python caller** — its only
call sites are prose in `kata-readiness/SKILL.md:81` and `kata-orient/SKILL.md:112,119`.

🔴 **Concrete hazard found.** The caller contract says `integration_branch` defaults to `"integration"`.
**This repo has no such branch** (`git rev-parse --verify integration` → fatal; we integrate on
`master`), and `kata.config` carries **no integration-branch key**. Per `kata_restore.py:358-359` a
missing branch returns an empty set ⇒ `integrated = ∅` ⇒ **re-dispatch every PLAN task** ⇒ step 4
(`:831-832`) runs `cleanup_stale_task` → `git branch -D task/<id>` against the **six live `task/*`
branches** (`task/m4p1-W1..W4`, `task/m4p2-X1..X2`). Fail-safe in the over-dispatch direction,
**destructive in the branch direction.** `degraded=True` is set and nothing consumes it.

### D2-9 — Second-brain recall · **read side WIRED-UNFIRED · the `parsed_open_skipped=1` mystery is SOLVED**
The system is effectively **emit-only**. `tools/recall.py` has **no CLI** (contrast `learn_feed.py:758`),
so the CONSULT seam requires an agent to hand-write Python. Callers are prose only; zero Python
callers. The seam is *reachable* (config gate satisfied, 269 pages present) but there is **no record
of it ever being walked** — and this repo records live proofs loudly elsewhere, so the silence is
meaningful.

✅ **`parsed_open_skipped=1` root-caused — it is benign.** It is the ledger's **own H1 title** parsed
as an unresolved entry: `_HEADING_LINE_RE` (`learn_feed.py:123`) matches h1–h6, and the literal string
`GRILL-LEDGER` matches `_ANCHOR_RE`. Every ledger's H1 is `# GRILL-LEDGER — <spec>`, with no status
token ⇒ `status="open"` ⇒ counted and skipped. Arithmetic confirms exactly (4/5/12 LOCKED entries +1
title each). **Nothing substantive is being lost.** Cheap fix: anchor the regex to `^#{2,6}`.

### D2-11 — Prime-directive enforcement · **deletion detector only, 7 substrings**
`validate_skills.py:321-322` checks containment of `PD-1`, `PD-2`, `DRIFT`, `kata-defer`,
`escalation`, `truthful`, `stable tier` — order-free, context-free. The file's own footer admits it.

**A concrete gutting edit was demonstrated that passes green**: a 6-line replacement inverting both
directives ("stub it and move on. Present-but-dead counts as built" / "Be truthful where convenient")
contains all seven tokens ⇒ **validator green**. `test_prime_directives_guard.py` is weaker in the same
direction — all presence assertions. **This is the strongest possible argument for MC-07 (T-07).**

### D2-14 — Adaptive L2 · **absent-block BC FIRED · but the premise was wrong**
Absent-block-is-off is genuinely test-pinned in three places. **However `l2: false` in a PRESENT block
is NOT "off"** — block-present = consent, so `failBumpAt`, `streakDownAt`, `planComplexityDownshift`,
`evaluatorEscalate` are all **live right now** in our config. And the `l2` key is **INERT**: it is
validated and stored but **never read** by any code path. `l2_base_rung` has **zero non-test callers**
— BUILT-ONLY.

## Batch 3 — D2-10, D2-12, D2-13

### D2-10 — Handoff family · **artifacts FIRED · every automated DECISION is prose**
- **(a) Self-handoff at 0.70 — never crossed on this host.** The engine is real
  (`kata_gauge.py:39,273-326`) and mechanically proven at a *fixture* threshold of 0.30 in a throwaway
  repo (`context-autonomy/LIVE-PROOF.md:25-63`). But across **22 real-session bridges** in `%TEMP%`,
  **peak observed is `used_pct: 69`** — one point short. The only dedupe sidecar belongs to a synthetic
  test session. **No real session has ever been injected.**
- **(b) Boundary-supersedes-self — PROSE, zero code.** Two sentences (`protocol/handoff.md:36-38`,
  `kata-sprint/SKILL.md:47-48`). `kata_supersede.py` is unrelated (promoted-skill shadowing). **No
  boundary handoff has ever been written** — zero files match `^kind: (self|boundary|manual)`.
- **(c) Staleness rule — comparator unimplemented.** Reaches the model only as injected prose in two
  hooks; no Python compares board timestamps to the handoff commit time. Demotion is an unlogged LLM
  judgement every time.
- **(d) Fresh-agent resume — YES, demonstrated**, on the strength of `.planning/` (HANDOFF 13.5 KB,
  HANDOFF-NEXT-SESSION 21.7 KB with an explicit ground-truth §0, STATE 151 KB). ⚠ But **not one real
  handoff carries the `kind:`/`trigger:` provenance fields** — the whole CA-L21 provenance layer is
  **BUILT-ONLY**. And `.kata/` is gitignored, so a fresh *clone* gets `.planning/` only.
- **(e) Runs CAN end without a durable handoff — confirmed.** The write is prose at all three sites;
  there is **no exit gate, no Stop/SessionEnd hook, no validator check**. Installed hooks are
  SessionStart / UserPromptSubmit / PreCompact only. The clearest hole is D2-12's own case: host-session
  quota kills the conductor and the handoff instruction never executes.

### D2-12 — Quota park sequence · **WIRED-UNFIRED (our label is correct) · limit accurate**
Zero hits for `quota` or `degraded` anywhere in `.kata/`; no handoff carries `trigger: quota`.
**`kata_quota` is imported by exactly one file — its own test.** Zero production callers; the
classify→lapse→park chain exists only as conductor prose. The structural limit we recorded is
**accurate**: `classify_dispatch_result`'s scan surface is fixed to dispatch RESULT envelopes, so a
host-session kill leaves no envelope and no surviving process — **INERT by construction, not omission.**

### D2-13 — Graph / kata-understand · **and MC-08's premise is partly wrong**
- **Graph FIRED but 35 days stale and scoped**: `.kata/kata.graph.json` (344 KB, `generatedAt`
  2026-06-21) has 450 nodes covering only `tools/` and `research/`, with **425 `def`, 104 `ref`, and
  just 3 `import` edges**. It predates the 2026-07-02 src-layout fix.
- **`kata-understand` has only ever run the DIFF-FALLBACK path.** `.kata/understand.md` is genuine
  output (cites real SHAs and counts) but its own line 3 says *"diff-fallback path"*.
  `understand-cycle1.md` is byte-identical — one run, copied. **The graph-backed primary path has never
  produced an artifact.**
- **The documented degradation is prose only.** No code detects backend absence; `graph_gen.py:28-29`
  imports tree-sitter at module top, so an absent backend is a hard `ImportError` the caller must catch.
- ⚠ **MC-08's premise is PARTIALLY INACCURATE.** The src-layout resolver **already exists here** —
  `graph_gen.py:264-300` + `:303-353`, shipped 2026-07-02 (`47ddc2d`), with 22 src-layout test
  references. Executed against synthetic layouts, three of four resolve correctly. **The real residual
  is narrower**: the PEP-420 fallback at `:298` fires only for paths literally starting `src/`, so a
  **nested** namespace src-layout resolves nothing — which is exactly why the 144
  `research/reference/bmad-method/src/**` nodes contribute **zero** import edges. PageRank is
  consequently flat: 3 distinct values across 25 file nodes, stdev 1.6e-5, min at the uniform 1/N floor.
  So "flatter PageRank" is **true of the artifact**, but the cause is staleness + the nested-namespace
  hole, **not an absent resolver**.

---

## 🔴 INCIDENTAL SECURITY FINDING (out of probe scope, operator action required)

A probe surfaced this and I verified it directly, without echoing the value:

**`~/.claude/settings.json` contains a plaintext GitHub fine-grained PAT** in
`env.GITHUB_PERSONAL_ACCESS_TOKEN` — 93 chars, `github_pat_` prefix. **File mode `666`.**

- ✅ **Not git-tracked** — `~/.claude/.git` does not exist, so it has not been published anywhere.
- ⚠ But it is world-readable on this filesystem view, and it is injected into the environment of
  **every** process this harness spawns — including every subagent and every `Bash` call.
- **I did not rotate it.** Rotating touches your GitHub account, which is outward-facing and yours to
  do. Recommended: rotate the token, then restore it via a credential helper or an env var sourced
  from a mode-600 file rather than `settings.json`.

---

## What this does to the ingest queue

| task | before | after batch 1 |
|---|---|---|
| **T-04 (MC-05 run-identity)** | standard grill, BC risk | **PRIORITY UP** — closes a confirmed BROKEN gate (D2-5) |
| **T-05 (MC-04 verdict self-declaration)** | standard grill | **PRIORITY UP** — D2-4 confirms fresh-context is unattested here |
| new | — | **BL-M17** — no executable owner for `mode`/`tiers` (D2-2) |
| new | — | **BL-M18** — no test pins D33 never-tiered across tier variants (D2-3) |
| new | — | **BL-M19** — spine evidence is gitignored, so loop traversal has no audit trail (D2-1) |
| new | — | **BL-M20** — `kata-loop` conductor is unreachable from any entry point (D2-1) |
| **T-08 (MC-08 src-layout)** | standard grill | **RE-SCOPE** — we already have the resolver (`47ddc2d`). Real gap is the nested-namespace hole at `graph_gen.py:298`. Do not merge a duplicate |
| **T-07 (MC-07 PD enforcement)** | advanced grill | **PRIORITY UP** — D2-11 demonstrated a green-passing PD gutting edit |
| new | — | **BL-M21** — 🔴 `kata_restore` defaults to a nonexistent `integration` branch ⇒ a real restore would `git branch -D` six live `task/*` branches (D2-8) |
| new | — | **BL-M22** — no Stop/SessionEnd gate, so runs can end with no durable handoff (D2-10e) |
| new | — | **BL-M23** — handoff `kind:`/`trigger:` provenance layer is BUILT-ONLY; no real handoff carries it (D2-10d) |
| new | — | **BL-M24** — `learn_feed` heading regex counts the ledger's own H1 as an open entry; anchor to `^#{2,6}` (D2-9, benign) |
| new | — | **BL-M25** — `models.adaptive.l2` is INERT (validated, never read); `l2_base_rung` BUILT-ONLY (D2-14) |
| new | — | **BL-M26** — rebuild `kata.graph.json` (35 days stale, predates the src-layout fix) and measure rank variance (D2-13) |
| new | — | **BL-M27** — 🔴 rotate the GitHub PAT out of `~/.claude/settings.json` (operator action) |
| **D140 record** | — | **CORRECT IT** — "zero `builds_against` edges in any run" was refuted by D145 two days later and never amended (D2-6) |
