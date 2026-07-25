---
date: 2026-07-25
source: kataharness-mergeback-v0.2.1 (producer fork @ 75108b7, tag v0.2.1)
consumer_baseline: master `fcb0338`, tag v0.4.0
status: ITEMIZED — nothing ingested yet; every MC awaits its own grill
tags: mindbridge-import · ingest · coverage-matrix · verification-checklist
---

# MERGE-BACK INGEST — full itemization + coverage validation

**Purpose.** Every actionable thing that arrived in `kataharness-mergeback-v0.2.1`, itemized into
tasks and backlog items, with a coverage matrix proving nothing was dropped, and an in-depth
verification checklist for the subsystems the package claims are **already aligned** on both sides.

**Governing protocol:** `.planning/HANDOFF-NEXT-SESSION.md` §6 (clean-room scrub gate + work-linkage
adval) and §6b (script-vs-context axis). Nothing here auto-applies. Each MC is a version-up with its
own INTENT freeze → grill → build → gauntlet → correctness adval **+ work-linkage adval** → PR.

---

## PART A — COVERAGE MATRIX (what arrived ⇒ where it is tracked)

Every artifact in the package, and its disposition. **No row may be blank.**

### A1. Merge candidates (8 delivered)

| id | what | disposition | tracked as |
|---|---|---|---|
| MC-01 | Ten-laws AST checker (9 of 10; law 6 = JUDGMENT) | script | **T-02** |
| MC-02 | Doctrine laws 11–16 + 2 judgment-boundary clauses | prose | **T-03** |
| MC-03 | 4 additive validator checks (bump-on-modify + 3 reporters) | script | **T-01** |
| MC-04 | Verdict dispatch self-declaration | script | **T-05** |
| MC-05 | Run-identity / state rotation (stale-evidence gate) | script | **T-04** |
| MC-06 | Readback-verified writes + newline-guarded appends | script | **T-06** |
| MC-07 | BUILT/WIRED/GATED vocabulary + decidable half of PD-2 | hybrid | **T-07** |
| MC-08 | src-layout import resolution (fills §Z10) | script | **T-08** |

### A2. Divergence flags (5 delivered, 1 MISSING)

| id | recommendation | disposition | tracked as |
|---|---|---|---|
| DF-01 | Context-as-Code vs scripts — **HOLD ours** | no action; confirms our architecture | **BL-M12** (record only) |
| DF-02 | Amendments they did NOT propose | informational; read before MC-02 grill | input to **T-03** |
| DF-03 | Tool-class taxonomy — HOLD; **§4 applies to us** | §4 conversion-fossil lesson | **BL-M13** |
| DF-04 | 4 places our validator is better — **KEEP all four** | no action; protects T-01 scope | constraint on **T-01** |
| DF-05 | 9 §Z gaps declined + 2 features withheld | informational; §3a measurement | **BL-M09** |
| **DF-06** | **NEVER DELIVERED** — referenced at `CLEAN-ROOM-ATTESTATION.md:116` as a **partial-scrub-risk** item | **BLOCKER** | **T-00** |

### A3. Their forward backlog (26 items — intelligence, not proposals)

Not proposals; none is built. Tracked as **BL-M01..BL-M08** where they name work we should
consider, and recorded wholesale as intelligence.

| BL | their item | our disposition |
|---|---|---|
| BL-026 | Packet-tracing smoke formalization | **BL-M01** — they name this the most worth ingesting; end-to-end transit fidelity is owned by nothing on either side |
| BL-005 / BL-013 / BL-017 | Specialist registry + injection + cadre | **BL-M02** — convergence: same as our parked specialist-injection seam; neither side built it |
| BL-025 | Skill evals + skill-quality assessment | **BL-M03** — we have ~49 skills and only structural checks; their research cite: curated skills +16pp, self-generated −1.3pp |
| BL-019 | Learning-loop deep dive — is it working? | **BL-M04** + Part D checklist |
| BL-022 | Handoff mechanism thorough review | **BL-M05** + Part D checklist |
| BL-020 | Code-graph oracle layer beyond parser floor | **BL-M06** — maps to our §Z10/graph work; MC-08 is the floor fix, not this |
| BL-021 | "Understand anything" comprehension tool | **BL-M07** — we have `kata-understand`; same honest-state question |
| BL-018 | Agent-roster deep review (coder / adversarial / evaluator rubrics) | **BL-M08** |
| BL-002 | Durable "the resolver actually ran" artifact | **BL-M10** — we have the same gap class (D59 relative routing leaves no trace on non-adaptive runs) |
| BL-011 | Good-code/bad-code ride-along context + quality verifier | **BL-M11** |
| BL-001, 003, 004, 006, 007, 008, 009, 010, 012, 014, 015, 016, 023, 024 | remainder | **recorded as intelligence only** — no KataHarness action; revisit if they build |

### A4. Report-level content (claims, not files)

| source | content | disposition |
|---|---|---|
| `alignment-report.md` §0 | **Premise correction: it is a conversion PORT, not a branch.** No merge base, no shared history, upstream pin `v0.3.0-11-gf40a973`, port date 2026-07-05 | **T-09** — correct our own records (README/STATE/HANDOFF call it a fork/branch) |
| `alignment-report.md` §1 | 14 "already aligned" subsystem claims | **Part D checklist** (the user's core ask) |
| `alignment-report.md` §3 | **"A fix does not travel; a checker does"** — 5 of our closed DET defects reappeared in their port | **rationale for T-02**; also **T-10** (ingest-direction risk) |
| `INDEX.md` §honesty | 7 disclosures incl. no live e2e run ever, 26 unwired call sites, 0-of-22 machine-JSON trailers | qualifies every MC; recorded per task |
| `INDEX.md` §own-defects | 4 self-disclosed defects in their shipped work | **BL-M14** — the `[::2]` under-count class is worth checking for in our own checkers |
| `CLEAN-ROOM-ATTESTATION.md` | 4-point scrub + 2 explicit non-claims | **T-00** (verified independently, see Part E) |
| `BACKLOG-FULL.md` §closing | 3 convergence observations | folded into BL-M01/M02/M03 |

### A5. Findings originated on OUR side during this review

| # | finding | tracked as |
|---|---|---|
| F-1 | **DF-06 referenced but never delivered** — a partial-scrub-risk item with no artifact | **T-00** |
| F-2 | Attestation cites DF-05 by a filename that does not match the delivered file | **T-00** (minor) |
| F-3 | `DF-05 §1` credits **MC-06** with the §Z10 fill; it is **MC-08** | **T-00** (minor) |
| F-4 | **MC-03's headline claim VERIFIED against our tree**: `STANDARDS.md:112` promises "validator-enforced"; `validate_skills.py:122` has only `SEMVER.match`, **no comparator anywhere** | **T-01** |
| F-5 | **MC-01 run against our `tools/`: 101 findings / 58 files** (law 5:59 · 8:19 · 1:7 · 2:6 · 10:5 · 3:3 · 7:2) | **T-02** |
| F-6 | **Law 5 is FP-dominated on our tree** — our doctrine carves out "builder dicts with fixed key order are safe"; their checker cannot see that distinction and flags every `json.dumps` | **T-02** (prerequisite) |
| F-7 | **Law 1's 7 findings look REAL** — `footprint.py:212`, `kata_restore.py:86,120,688,702`, `kata_trail.py:142` invoke git raw instead of routing through `kata_telemetry._run_git`; doctrine says "never re-derive the pin set per call-site" | **T-02** / **BL-M15** |
| F-8 | 168 test claim **verified exactly** (44+19+24+24+15+22+20) on our interpreter | evidence for all tasks |

---

## PART B — TASKS (the ingestion work, ordered)

Each task = one version-up. Gates: `tools/scripts/gauntlet.py` green + correctness adval +
**work-linkage adval** (§6). Branch → PR → merge-on-green.

### T-00 — Close the clean-room record · **BLOCKER, no code**
- **Request `DF-06`** from the fork. It is named at `CLEAN-ROOM-ATTESTATION.md:116` as one of two
  partial-scrub-risk items routed to divergence flags; only DF-05 arrived. Nothing leaked, but an
  item they flagged as carrying scrub risk has **no artifact the operator can see** — which is the
  entire purpose of routing it to a flag.
- Report back F-2 and F-3 (citation errors) in the same message.
- **Gate:** the clean-room gate does not close until DF-06 lands or the fork states it was withdrawn.
- **Does NOT block** T-01..T-08 code review; it blocks the *record*, not the candidates.

### T-01 — MC-03 validator additions · **grill: standard · FIRST**
- Best-evidenced item in the package; the only one citing our own source to prove a false guarantee.
- **Rider (mandatory):** `docs/STANDARDS.md:112` must either become true or be reworded. Today it
  claims "validator-enforced" for bump-on-modify with no comparator — the same stale-record class as
  the DET registry we just reconciled (PR #50).
- **Constraint (DF-04):** additive module only. Do NOT merge their validator. Our empty-tree guard,
  `REQUIRED_PROTOCOL["prime-directives.md"]`, `steering.md` registration, and `--only` are all
  absent from theirs.
- **Re-flag risk:** none by construction — an unmodified file is skipped.
- **Workflow change to accept explicitly:** a contributor editing a skill without bumping gets a red
  build.

### T-02 — MC-01 ten-laws checker · **grill: advanced · REPORT-ONLY on landing**
- Closes the named Target-1 gap (`AGENTS.md:102`, doctrine §Enforcement).
- **Prerequisite (F-6):** add a **law-5 builder-dict carve-out** before law 5 can ever gate. Our
  doctrine's own text exempts fixed-key-order builder dicts; their checker flags all 59.
- **Triage required (F-5):** 101 findings on our surface. Law 1's 7 look real (F-7).
- **Do not wire as a gate on day one** — `02` Target 2 rejects a merge that flips our tree red.
- Their measured FP rate on their own surface was 11/88 = 12.5%, and they explicitly do not claim
  the residual is zero.

### T-03 — MC-02 doctrine laws 11–16 · **grill: advanced · HIGHEST STAKES**
- This is doctrine **text** — a never-tiered structural document. Our own rules make text changes
  advanced-grill.
- **Their own honesty limits, which are the reason for caution:** batch-reviewed, **not**
  adversarially grilled as amendments; single-corpus evidence; derived from a Context-as-Code
  harness that is not ours; no live-run evidence anywhere behind it.
- **Their recommendation:** take **law 15 (scope honesty)** and **law 13 (recompute, don't
  shape-check)** first; **law 11 may describe a hole we do not have** since our detectors are
  already scripts.
- **Take a subset, not all six.** Read DF-02 first.
- Constraint: preserve the core rule verbatim; do not renumber or drop laws 1–10; do not blur
  "where judgment is allowed" (their 2 clauses claim to *narrow* it — verify that at grill).

### T-04 — MC-05 run-identity / state rotation · **grill: standard · HIGHEST BC RISK**
- The only candidate that **changes behavior on disk** (moves files; archives, never deletes).
- Real gap: `kata-evaluate` covers absent + malformed `RESULT.json`; **stale is present and
  well-formed**, so the gate credits it.
- Their status: **BUILT, NOT WIRED**; no live run has exercised it.
- Their stated limitation: assumes a single run per state directory at a time.

### T-05 — MC-04 verdict dispatch self-declaration · **grill: standard**
- Closes the other half of D33: our `check_evaluator_no_write` enforces the *structural* half; nothing
  validates that a consumed verdict actually came from such a dispatch.
- Their status: contract-wired, **never live-fired**; module is new code.
- **Their deny-list is a policy stub** naming one host-roster agent — must be re-authored for our roster.

### T-06 — MC-06 readback-verified writes + newline guard · **grill: standard**
- Two ~150-line primitives. Row-fusion corruption **actually happened twice** on their side — the
  best-evidenced claim in that MC.
- **They explicitly do not know whether we have this gap.** Verify against our `gate_emit.py`,
  `run_result.py`, board writer before accepting.

### T-07 — MC-07 BUILT/WIRED/GATED vocabulary · **grill: advanced**
- Directly answers `02` Target 3 (enforcement, not PD text).
- **The checker is the least-proven artifact in the package by their own admission** — the two rubric
  items it derives from are prose-only and have never fired.
- Vocabulary has real operating history; the checker does not. Consider taking the **vocabulary**
  (protocol doc) and grilling the checker separately.

### T-08 — MC-08 src-layout resolver · **grill: standard**
- Fills **§Z10**, which our own `01` §E named as a merge-back candidate.
- Their status: BUILT and exercised but **shipped with ZERO tests**; the 20 tests are new.
- **The PageRank improvement is unproven** — they can show edges resolve, not that ranking improved.
- Constraint: flat layout must stay byte-identical.

### T-09 — Correct the "fork/branch" premise in our own records · **no grill, docs-only**
- It is a **conversion port**, not a fork/branch: no shared git history, genesis commit, upstream pin
  `v0.3.0-11-gf40a973`, port date 2026-07-05, per-file conversion matrix.
- Wrong in: alignment package README, `.planning/STATE.md`, `.planning/HANDOFF-NEXT-SESSION.md` §6,
  and memory `project_kataharness`.
- Matters because "reverse-direction merge from a fork" and "ingest from an independently-diverged
  port with no merge base" are different risk models.

### T-10 — Ingest-direction defect-carry risk · **backlog-or-task, operator call**
- Their §3 proves defects travel **backwards** through an ingest: 5 of our closed DET defects live in
  their port because they forked one week before adoption.
- Our sanctioned KataHarness→fork flow has the same exposure in reverse.
- Concrete ask: when T-02 lands report-only, run it over **any** ingested surface, not just ours.

---

## PART C — BACKLOG ITEMS (not scheduled; promote when ready)

| id | item | source |
|---|---|---|
| **BL-M01** | Packet-tracing smoke formalization — end-to-end transit fidelity, owned by nothing today | their BL-026 (their top pick for us) |
| **BL-M02** | Specialist registry + injection points + cadre | their BL-005/013/017 ↔ our parked specialist-injection seam |
| **BL-M03** | Skill evals + skill-quality assessment (behavioral, not structural) | their BL-025 |
| **BL-M04** | **Learning-loop deep dive** — does improve actually change skills run-over-run? | their BL-019 + Part D |
| **BL-M05** | **Handoff mechanism thorough review** — does every path fire and reconstitute? | their BL-022 + Part D |
| **BL-M06** | Code-graph oracle layer beyond the parser floor (`call` edges, communities, blast-radius) | their BL-020 |
| **BL-M07** | `kata-understand` → first-class whole-repo comprehension | their BL-021 |
| **BL-M08** | Agent-roster deep review + explicit evaluator rubrics/scoring | their BL-018 |
| **BL-M09** | **Measure `kata-orchestrate`'s reference surface.** They measured theirs at **102,750 tokens = 51.4% of a 200k window before doing any work**; one-reference-per-phase cut it 54%. Take the *measurement method*, not the feature | DF-05 §3a |
| **BL-M10** | Durable "the model resolver actually ran" artifact per dispatch | their BL-002 |
| **BL-M11** | Good-code/bad-code ride-along context + a maintainability verifier | their BL-011 |
| **BL-M12** | Record DF-01: our scripts-first architecture is externally validated; do not adopt Context-as-Code | DF-01 |
| **BL-M13** | DF-03 §4 — the **conversion-fossil** class; check our own tree for the equivalent | DF-03 |
| **BL-M14** | Audit our own checkers for the `[::2]`-style silent under-count class they found in theirs | INDEX §own-defects |
| **BL-M15** | Route the 7 raw-git call sites through the shared pinning helper (F-7) | our finding |
| **BL-M16** | **M4 inline evaluator has never fired here** — 0 machine-JSON verdicts in all history, 0 artifacts in `.kata/`. Either fire it once (n=0→1) or re-label the M4 claims honestly. Same state as the producer's | D2-7 probe |

---

## PART D — VERIFICATION CHECKLIST: "already aligned" ⇒ is it actually working HERE?

`alignment-report.md` §1 asserts 14 subsystems are aligned on both sides. **An alignment claim is not
evidence our side works.** This is the checklist. Status vocabulary is MC-07's, used deliberately:
**BUILT** (code exists) · **WIRED** (reachable from a real surface) · **GATED/FIRED** (has executed).

### D1 — Probed this session (evidence in hand)

| subsystem | claim | our verified state |
|---|---|---|
| **Learning loop — EMIT half** | aligned | ✅ **FIRED.** 269 pages in `~/Kiban/Vault/second-brain/wiki/pages/synthesis/decision-patterns`; `log.md` shows emits through 2026-07-22 with dedup (`skipped_identical=167/207`) and `redactions=0`. The β redaction filter is real (`learn_feed.redact`, SB-L4 classes). |
| **Learning loop — LOOP half** | aligned | ⚠️ **UNVERIFIED — this is exactly their BL-019.** Emit ≠ loop. No evidence that lessons → `kata-improve` → changed skills → re-applied actually closes. **Also: every log line carries `parsed_open_skipped=1`** — a persistent skip nobody has explained. → **BL-M04**, and investigate the skip. |
| **Advisor (D167)** | "port of yours; hooks never fired on either side" | ✅ **BUILT + WIRED, UNFIRED** — confirms Z3. Engine `tools/kata_advisor.py` (11 fns), prose wiring in `kata-orchestrate`, `kata-design-doc`, all 3 plan tiers, `kata-initiate`; `protocol/advice.md` schema; `.kata/advisor-exercise-state.json` exists **from the operator-ordered pre-merge exercise, not a live consult**. |
| **Validator / conformance** | ours better in 4 places | ✅ **VERIFIED** — empty-tree guard at `validate_skills.py:497-504` with D136/D33 rationale, exactly as DF-04 credits. |
| **Per-skill semver + README index** | aligned; MC-03 makes bump enforced | ❌ **THE PROMISE IS FALSE HERE** (F-4). `STANDARDS.md:112` says validator-enforced; only `SEMVER.match` runs. → **T-01**. |

### D2 — Still to probe (each is a checklist item, not an assumption)

| # | subsystem | the question that settles it |
|---|---|---|
| D2-1 | **Spine + outer loop** | Does a real run traverse initiation → harness → closeout with the loop-back? Or is only the direct one-shot path exercised? |
| D2-2 | **Modes / tier families** | Does `standard`-as-fallback actually fire when `kata.config` is absent, or is it prose? |
| D2-3 | **D33 never-tiered invariants** | Is there a test proving a tier variant cannot weaken a structural invariant, or is it convention? |
| D2-4 | **Default-FAIL fresh-context evaluator** | `check_evaluator_no_write` covers frontmatter. Has a real evaluator dispatch ever been *verified as fresh-context* at runtime? (This is MC-04's gap.) |
| D2-5 | **RESULT.json / footprint / mutation evidence contract** | Is a stale `RESULT.json` currently creditable? (MC-05 says yes on both sides.) |
| D2-6 | **Contract edges / freeze-float M1** | Any run with a real `builds_against` edge? Our own note: **zero exist in any run today** — so the float is inert. |
| ~~D2-7~~ | **Inline evaluator M4** | ✅ **PROBED 2026-07-25 — SAME RESULT AS THEIRS.** Our history: 24 `Kata-Task:` trailers · 210 checkpoint/inline-eval references · **0 machine-JSON verdict payloads** · **0 inline-eval artifacts in `.kata/`**. Their measurement was 22 trailers / 0 machine JSON. **Our M4 chain has never fired either.** Both harnesses ship an inline evaluator; neither has produced machine-readable output from it. → **BL-M16** |
| D2-8 | **Restore-hardening / board-as-trail** | Tier-2-authoritative-for-DONE proven live, or only by the manual operator playbook? (Our record says the latter.) |
| D2-9 | **Second-brain recall (no embeddings)** | Does CONSULT/recall read back in a real run, or is it emit-only? |
| D2-10 | **Handoff family (all paths)** | Does self-handoff fire at threshold with zero task loss? Does boundary supersede a coincident self-handoff? Does staleness demote correctly? Can a cold agent resume from artifacts alone? → **BL-M05** |
| D2-11 | **Prime Directives** | `REQUIRED_PROTOCOL` is a **term-presence** check — it catches deletion, not rewording. Is there anything stronger? (MC-07 is the candidate.) |
| D2-12 | **Quota park sequence** | UNFIRED by our own label (Z4). Unchanged by this package — they have no quota subsystem at all. |
| D2-13 | **Graph / kata-understand** | Does `kata-understand` degrade to a diff map as documented, and has it ever run end-to-end? → **BL-M06/M07** |
| D2-14 | **Adaptive L2** | OFF on both sides. Confirm absent-block ⇒ byte-identical still holds. |

**The D2-7 probe is the single cheapest high-value check on this list** — it is a `git log` grep, and
it answers whether our M4 inline evaluator has ever actually produced machine-readable output or
whether we are in the same position they measured on their side.

---

## PART E — CLEAN-ROOM VERDICT (independent, not their attestation)

Scanned every file in the package myself:

- **0** AWS/corp identifiers (every `aws|lambda|s3` hit is the Python `lambda` keyword or `sorted(key=…)`)
- **0** URLs, emails, account ids, ARNs; `[A-Z]{2,}-[0-9]{3,}` hits are all `BL-NNN`
- Producer name: **4 occurrences, all in `CLEAN-ROOM-ATTESTATION.md`** as provenance framing —
  *fewer* places than they disclosed
- **0** new strings added to `.planning/`, as claimed
- **No git history, packfiles, or objects** — plain files only
- **168 tests verified passing** on our interpreter, exact match to their claim

**Verdict: PASSES on content.** The record is incomplete pending **DF-06** (T-00).

### E1 — ⚠ BINDING CONSTRAINT ON EVERY WORK-LINKAGE ADVAL: our IaC surface is FIRST-PARTY

**The scrub above scanned ONLY the inbound package** (`~/Downloads/kataharness-mergeback-v0.2.1/`).
Our repo was never in scope, so our IaC specialists could not have been false-flagged. But the §6
work-linkage adval **does** scan our tree, and it will grep for exactly the AWS vocabulary our own
shipped product legitimately contains.

**These are first-party KataHarness product features (public, Apache-2.0) — NOT work-linkage:**

| surface | AWS-vocabulary hits | what it is |
|---|---|---|
| `skills/execute/kata-iac-cloudformation/SKILL.md` | many | shipped IaC specialist skill |
| `skills/execute/kata-iac-terraform/SKILL.md` | many | shipped IaC specialist skill |
| `tools/iac_apply.py` | 15 | CFN/TF argv builders; `run_apply` is the deferred `NotImplementedError` seam |
| `protocol/iac-safety.md` | 8 | the IaC safety contract |
| `protocol/exec-safety.md` | 0 direct; 4 `run_apply` rows | the exec-safety registry |
| `tools/iac_detect.py`, `skills/execute/kata-lang-profile/` | some | stack detection / language profile |

**Any adversarial reviewer scanning for AWS/work-linkage MUST be briefed that these are product
features.** A reviewer who flags `kata-iac-cloudformation` as an AWS leak produces a false HOLD — and
worse, acting on it would scrub a shipped capability. The work-linkage question is *"does this
disclose the internal project, its shape, or the relationship?"* — **not** *"does the word AWS
appear?"* Naming a public cloud vendor whose IaC we deliberately support is neither.

**Inbound side, for completeness:** the package contains **exactly one** IaC reference —
`MC-05/PROPOSAL.md:53` lists `iac.json` among the `.kata/` state files that would receive
run-identity stamping. That is a reference to *our* artifact, read from our snapshots. **Zero AWS
content arrived.**

**Consequence for T-04 (MC-05):** it stamps run-identity across `.kata/*.json` **including
`iac.json`** — so MC-05 touches IaC state. Confirm no interaction with the creds-wall/approval
artifact contract at grill.

---

## OPEN DECISIONS FOR THE OPERATOR

1. **Work-linkage + correctness advals** — §6 requires both per item before merge. Both are subagent
   work; not spawned this session pending operator go-ahead.
2. **DF-06** — chase before T-01, or in parallel?
3. **MC-02 scope** — all six laws, or the subset (13 + 15) the producer themselves recommend?
4. **T-10** — task or backlog?
