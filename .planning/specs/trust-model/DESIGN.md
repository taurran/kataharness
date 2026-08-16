---
status: draft
spec: trust-model
revision: 1
compiled-from: ".planning/specs/trust-model/GRILL-LEDGER.md — frontmatter `status: converged`
  (grill closed 2026-08-16: convergence pass 1 SHIP fifth run · pass 2 SHIP second run ·
  EV-1 ACCEPTED). 24 LOCKED branches (TM-A1..A3, B1..B5, C1..C7, D1..D5, E1..E2, F1..F2,
  G1..G3, H1..H4) + five amendment blocks (R-*, R2-*, R3-*, R4-*, RS-*; later supersedes
  earlier where they overlap) + 26 compile residuals (6 pass-1 SHIP, 5 at R4-H1, 15 pass-2
  SHIP) + EV-1."
date: 2026-08-16
author: design-author (KH-T13 dispatch; prose-era dispatch recorded honestly per the brief —
  Guardian Honor-system, stated)
---

# DESIGN — the Trust Model

**In plain terms:** the harness makes ~114 promises and machines keep only the document-layer
ones; execution runs on model obedience to prose, and both Backlog Burns proved obedience fails.
This contract moves trust from obedience to code: every agent launch becomes a code act (**the
seam**), every run event lands on one durable temporal record (**the cursor**), every completion
gate refuses work without attested facts (**Truth Serum** + gate preconditions), claims are
attested against ground truth before judges credit them (**the grounding agent**), every run
closes by grounding the output against the frozen plan (**the close**), and the user **sees** the
hard line working (**the presentation layer**). Operator goal, verbatim: *"TRUST in every
mechanism within the harness/loop, but also trust in the output itself… actually back trust with
fact/truth."* (ledger preamble + operator directives 1–9.)

**Standing rulings this DESIGN serves and must never contradict:** D172 (seam actions are engine
code under the Determinism Doctrine, fail-closed) · D169 (freeze blocks, never warns) · D81/D135
(the cursor is a board upgrade + fold, never a second journal; authority never lives in `.kata/`)
· EDR-7 (anything the judged agent can read off disk is forgeable — the dispatcher is the
witness) · D134 (tier-2 trailers authoritative for DONE) · BBM-11 (headless never blocks on a
human) · BBM-12 (burns run the entire loop, wave-per-loop) · thin-orchestrator (spine #8) ·
PD-1/PD-2 (the contract this program mechanizes). (Ledger "Binding rulings carried".)

**Reading rule:** every requirement row below cites its ledger anchor (`TM-x`, `R-x`, `R2-x`,
`R3-x`, `R4-H1`, `RS-x`, `EV-1`, or a named compile residual). A row without an anchor is drift;
a locked branch without a row is an omission. All trust claims use the Guardian scale (§6.2).
Where the ledger defers a detail to the frozen PLAN, this document says so explicitly and does
not invent it (§12).

---

## §1 The seam — every agent launch is a code act

### 1.1 Architecture: four attach points, layered — TM-B1

The seam composes ALL four authority attach points (SURFACE-MAP §5):

1. **The engine is the only door** — every dispatch is a function call that mints and validates
   run context, wiring the orphaned enforcement layer (freeze chokepoint, roles, models, cursor
   writer, roster) in one move. (TM-B1)
2. **A fail-closed host hook** intercepts bare dispatches at the host boundary (per-host
   capability, §1.7). (TM-B1, TM-B2)
3. **Post-hoc identity verification at every gate** audits the chain (host-independent). (TM-B1)
4. **The wrapper door defers to BL-N21** as the outermost layer, later. (TM-B1, TM-H3)

All four sit on the dispatcher's side — EDR-7 satisfied: the launched agent never echoes
anything; validation is wholly dispatcher-side, eliminating (not mitigating) the echo-forgery
class. (TM-B4)

### 1.2 Seam scope — TM-B3

- **Dispatch-gated (record required, hook denies without one):** every launch of another agent —
  workers, judges (evaluate/review/slop/inline), design/plan authors, the advisor, researchers,
  kata-validate critics, debug fix-workers, reroll/correct re-dispatches, grill convergence
  reviewers. (TM-B3; surfaces D1–D12 of SURFACE-MAP §1.)
- **Cursor-tracked, NOT gated:** in-session skill invocations (kata-loop → initiate → bootstrap →
  orchestrate sequencing) are the conductor reading its own instructions — they emit PHASE cursor
  events (§2.6), not dispatch records. (TM-B3)
- The advisor's seam record closes the burn-02 advisor-reach gap mechanically (the hook can
  positively confirm a consult happened). (TM-B3 sharpening)

### 1.3 Engine API surface

The seam extends `tools/kata_dispatch.py` (live seeds: `build_brief:43`, `dispatch:219`,
`normalize:283`; `kata_restore.assert_frozen:426`). Module layout is a build detail; the
**surface is contract** (all engine code under the Determinism Doctrine's ten laws — D172):

| Function (contract name) | Act | Anchors |
|---|---|---|
| `run_start()` | New-run vs resume discrimination (§2.4); cursor rotation + run-header write + runId mint (new run only); orphan-record reaping; run-marker write (§8 RS-L5); hook fingerprint + deny-tripwire probes (§8 RS-H4/RS-M10); config-vs-settings consistency check (TM-H2); emits the minimal run-start declaration (§6.4) | TM-C2, R3-H1, R2-M3, TM-H2, RS-H4, RS-L5, R2-M1 |
| `mint(*, governs, role, …)` | Validates the governor predicate (§1.4), resolves role/platform/model (`kata_roles.resolve_roles`, `kata_models.resolve`), writes the pending dispatch record (§1.5), appends the seam-authored SPAWN line to the cursor (chained entry — a fabricated record without matching cursor lineage is post-hoc detectable) | TM-B4, R-H1, R3-M4, R-L4 |
| `dispatch(brief, worktree, …)` | The CLI-platform launch path (codex/kiro subprocess — the one live code path today) | TM-B2.2, SURFACE-MAP D6 |
| `capture(envelope, record_id)` | Parses the judge/arm return envelope with the ONE verdict parser (§1.6), appends the seam-authored VERDICT (judges) or DOWN (child runs) line + pointed-to JSON payload | TM-C4, R-H3, R2-H3, R4 residual 4, RS-M5 |
| `phase(event)` | Appends a seam-authored PHASE line (§2.6) | TM-C5, R-M2 |
| `deny(reason)` | Hook-side: appends the DENY line naming the legal path | TM-B5 |
| `close_run(…)` | The plan-grounding close (§5): refuses without required records, runs the three-way join + provenance drift check + redaction scrub, writes the terminal `run-closed` PHASE record | TM-F1/F2, TM-A2, RS-M7, R4 residual 3 |

The `governs` argument is **required, keyword-only, no default** — an omittable governor is the
D136 silent-permissive class (R3-M4, inheriting BL-F01's rule verbatim).

### 1.4 The governor ladder — per-role required states — R-H1 · R2-H1 · R3-H2 · R4-H1 · RS-H3

The dispatch record's `governs` field names WHICH artifact governs the dispatch. The vocabulary
is a **CLOSED enum with a mechanical predicate per entry** (no convention-only rung anywhere):

| Governor | Predicate (engine code) | Notes |
|---|---|---|
| `plan` | `assert_frozen(planPath)` — unchanged, exactly as D169 rules | R-H1, R2-H1 |
| `ledger` | new `ledger_status` predicate over grill-ledger frontmatter `status:` — closed four-value enum `draft \| converged \| frozen \| absorbed`, **first-word parse rule** (BL-F01); `converged` is written ONLY by the grill-close act after the final convergence SHIP, and that status write is **INDEPENDENT of the BL-X12-blocked `learn_feed` emit** (a blocked emit never blocks convergence status) | R2-H1, R3-M3, R4 residual 5, pass-1 SHIP residual 5 |
| `intent` | new `intent_status` predicate over `INTENT.md` frontmatter `status: draft \| frozen`; `intent_scaffold.write_intent` writes `frozen` at Phase 6 via a new explicit `freeze=True` argument (named, not inferred) — an explicit additive amendment to the pinned intent schema with its own two-step (the acceptanceCriteria precedent) | R2-H1, R3-L2 |
| `initiation` | an **open INITIATION or AUTHORING phase event on the live cursor** (checkable); the record additionally carries the priming-prompt hash as provenance | R3-H2, R4-H1 |

**Ordering over `ledger_status`** (per-role minimum-state comparisons): `draft < converged`;
`frozen` satisfies any requirement `converged` satisfies (a legitimate terminal state in live
use); **`absorbed` never satisfies a mint — it ROUTES the mint to the absorbing ledger** (pass-1
SHIP residual 2, R3-M3).

**Per-role minimum states:**

| Role class | Governor + minimum state | Guardian grade of the rung |
|---|---|---|
| Plan-executing roles — coder, task-scoped judges, anything dispatched against a plan task | `plan : frozen` (`assert_frozen` at mint) | Verified | 
| design-author / plan-author (run WITH a grill ledger) | `ledger : converged` | Verified |
| design-author / plan-author (run with NO grill ledger — D71 `skip`, or any bootstrap-entered authoring run) | `initiation` : open INITIATION/AUTHORING phase on the live cursor + priming-prompt hash | **Honor-system** (declared, never dressed as Verified) — R4-H1 |
| Grill-phase researchers / advisor / convergence reviewers | `ledger : present(draft)` | Verified (presence + status mechanical) |
| Bootstrap / harness-entry (runs that ENTERED via initiation/kata-loop) | `intent : frozen` | Verified |
| Initiation-phase mints | `initiation` (open-phase predicate) | **Honor-system** (the weakest rung, declared as such) — R3-H2 |

**BC laws (both binding):**

- A **direct one-shot harness run** (no initiation — the BC case `protocol/intent.md:11` pins)
  governs under `plan` exactly as today; `intent:frozen` binds only runs that entered via
  initiation/kata-loop. Deny-legal-runs eliminated. (R3-H2)
- R4-H1 compiles **ledger-presence-predicated, never tier-predicated**: a `light` grill DOES
  produce a ledger and therefore mints under `ledger` — the D71 parenthetical must not become
  the test. `ledger:converged` binds only runs that actually ran a grill; the grill remains the
  optional enrichment dial D71 froze — never a de-facto mandate at the seam. (R4-H1; pass-1 SHIP
  residual 3)
- **Initiation-rung exclusivity:** initiation-governed minting is REFUSED once the live run
  records a stronger governor (`plan:frozen` or `ledger:converged`) or once its
  INITIATION/AUTHORING phase has closed; re-opening INITIATION on a run with a frozen plan is a
  recorded DENY-class event. The predicate reads against the INITIATION **or AUTHORING** phase
  (pass-2 low 13). Honest residual: pre-freeze the rung is self-serviceable by the conductor —
  that is WHY it is graded Honor-system; cursor lineage is its detection channel, not a
  prevention (§11). (RS-H3)

Unknown governor or unmet state ⇒ **the engine refuses to mint** — no legal path ⇒ TM-B5 park
semantics apply. (R2-H1, TM-B5)

### 1.5 The dispatch record — schema + lifecycle — TM-B4 · R-L4 · R-M1 · R3-M1 · RS-H2 · RS-M12

**Fields (engine-minted, all required unless marked):**
`runId` · `taskId` · `role` · `platform` · resolved `model` + `effort` · `governs` (§1.4) +
governed-artifact ref (`planPath` with freeze VERIFIED at mint / ledger path / intent path /
priming-prompt hash) · `briefHash` · `mintedUtc` · `seq` (the mint's cursor line seq) ·
`agentDef` (slot RESERVED for BL-N20, unpopulated in v1). (TM-B4, R-H1)

**Storage:** records live under `.kata/dispatch/` — tier-3 is correct: the CURSOR chain entry is
the durable half, D81-consistent. The engine writes a pending-record pointer at mint; the hook
correlates the host `Agent` call to the pending record. (R-L4)

**Lifecycle (single-use, atomic claim, retained):**

1. Mint writes `.kata/dispatch/<runId>-<seq>.json` (pending) + the SPAWN cursor line.
2. **Consumption is an ATOMIC CLAIM:** the validating pre-hook consumes the record by
   `os.rename` of the record file into `.kata/dispatch/consumed/` (atomic within the volume).
   Two racing pre-hooks ⇒ one rename wins; the loser's validation fails ⇒ deny.
   Parallel-dispatch order-independence is ACHIEVED BY the atomic claim, never assumed.
   `fs_atomic`'s replace-only primitive is explicitly NOT the consume mechanism. (RS-H2)
3. **Mark-consumed-and-retain:** consumed records persist for lineage; a consumed record fails
   PRE-hook re-validation only. (R3-M1)
4. **Expiry:** `mintedUtc` bounds the MINT→LAUNCH window only and is **defense-in-depth ONLY** —
   the atomic single-use claim is THE replay control; wall-clock is never load-bearing (TM-C7
   reaffirmed). Return correlation is by the host's native tool-call pairing plus the record id
   stored at validation — a judge may legally return hours later. (R3-M1, RS-M12)
5. Crash mid-mint ⇒ orphan record without dispatch — detected and reaped at seam init (registry
   enumeration; the named actor is `run_start`'s orphan pass). (TM-H4 edge list, R2-M3)

**Hook validation is SEMANTIC, not existence:** the hook re-runs the engine validations against
the record (a stale or hand-copied record from an earlier dispatch fails — the T-04 staleness
class stays dead). (TM-B4)

### 1.6 Role vocabulary + verdict parsing

- **`ROLE_GROUPS` extends in the build** from today's verified set (`kata_roles.py:35` — coder,
  validator, researcher, orchestrator, evaluator, design-author, plan-author) with: `reviewer` ·
  `slop` · `inline-eval` · `advisor` · `critic` · `challenger` · `grounding`.
  `HOST_ONLY_ROLES` (`kata_roles.py:46` — orchestrator, evaluator) is UNCHANGED pending the
  cadre grill; tier mapping stays `SKILL_WORK_CLASS` (`kata_models.py:318`). (R-M5)
- **Every judge contract gains a pinned machine-parseable first line** (the kata-inline-eval
  pattern generalized): `VERDICT: <enum>` per judge type — the thing the capture edge parses.
  Part of the judge-contract rewrite wave. (R3-M2)
- **ONE verdict parser, two callers** (the post-hook and the conductor-invoked engine capture):
  strict fullmatch on **line 1 of the tool-result ENVELOPE** — never scanning the body, so repo
  content, advice payloads, and diff hunks cannot forge a verdict. The per-judge enum table is
  enumerated at the contract-rewrite wave. The conductor-invoked capture leg's input is
  conductor-supplied and says so (Honor-system). **No-match ⇒ the absent-records refusal path
  (§5.3), never a body-scan fallback** (pass-2 low 14). (R4 residual 4, RS-M5)

### 1.7 Per-host interception + the degrade table — TM-B2 · R-M7 · R2-H3 · TM-H2 · R3-M5

**Claude host (the reference adapter):**

- Workers stay on the in-process `Agent` path (host-native statusline, kill binding, background
  management). The engine mints FIRST; a new **PreToolUse-class hook fail-closes any `Agent`
  call lacking a valid record**. This deliberately breaks the all-hooks-fail-soft precedent
  (`kata-gauge-check.py:34-36`, anchor per R2-L4) — scope-gated to kata runs via the run marker
  (§8 RS-L5) so non-kata sessions are untouched. The hook capability probe is an explicit early
  task (UX-28 discipline: assess, never assume). (TM-B2.1)
- **The same hook layer also guards raw CLI worker launches through Bash** on a Claude conductor
  (match the dispatch command shapes of `codex exec` / `kiro-cli chat`, require the record). One
  interception surface, two guarded doors. **Honest residual:** the Bash leg is best-effort,
  evadable by indirection; its run-start declaration is **Partially verified**, never
  "intercepting" — the Agent-tool leg alone may claim interception. (TM-B2.2, R-M7)
- **Capture edge:** a **PostToolUse-class hook** appends the VERDICT/DOWN record mechanically
  when a seam-dispatched judge/arm returns, correlated via the dispatch record. The capability
  probe covers both edges in the same early task. (R-H3)

**Other hosts:** "dispatch interception" is an **abstract adapter capability**; each adapter
binds it natively (Kiro: its PreToolUse equivalent, risk-flagged per PLATFORM-MATRIX issue
#5527 — assess; Codex: assess). A host with NO interception primitive runs engine + post-hoc
verification only and **degrades LOUDLY** (the kill-binding precedent: surfaced, never silent).
(TM-B2.3)

**Hookless capture degrades to conductor-invoked ENGINE capture**, declared Honor-system: the
legal capture path is the seam's capture FUNCTION invoked by the conductor at verdict
collection — the run closes by doing the legal act, so the close's refusal (§5.3) binds only
when records are ABSENT, not when a hook is. Deny-the-bypass, never deny-everything. (R2-H3)

**The per-leg degrade table (Guardian grades are derived from probes, never asserted — §6.2):**

| Leg | Best mode | Degraded modes |
|---|---|---|
| Enforcement (deny edge) | Verified (intercepting) — deny-tripwire probe passed | Partially verified (bash-leg) · **Dormant (pre-activation, or deny-tripwire returns no result — never inheriting a prior declaration)** · Honor-system (detection-only host) |
| Capture edge | Verified (post-edge) | Honor-system (engine-by-conductor) |
| Resilience | Verified (full: **push receipt recorded on the cursor**, never the config flag) | Partially verified (local) · Honor-system (degraded / skips detected) |

(TM-B2.4, R2-H3, R3-M5, RS-H4 + pass-2 high 2.)

Degraded modes are **per-capability, never viral**; every degraded state is declared at
run-start; engine unavailable ⇒ the run cannot mint ⇒ no-legal-path park (§1.8), never a silent
prose fallback; settings drift is detected at seam init. (TM-H2)

### 1.8 Deny and park semantics — TM-B5

- A record-less launch is **DENIED by the hook** with a message naming the legal path (mint via
  the engine). Denial forces the legal path and needs no human ⇒ BBM-11-compatible in unattended
  shapes. (TM-B5)
- When the **engine itself refuses to mint** (plan not frozen, unknown role, unconfirmed
  platform, unmet governor state) there is no legal path: ESCALATE `human-required`; unattended
  runs **park the task** (the existing async-park pattern, `kata-orchestrate:884-885`), never
  die silently and never proceed. (TM-B5, R2-H1)
- **Every denial is a cursor DENY event and a visible refusal on the presentation layer** —
  the line being held is shown, not asserted. (TM-B5, TM-G1)
- A denial caused by a legitimate retry racing its own consumed record **names the re-mint path
  in the deny message** (retry-reads-as-replay, pass-2 low 11).
- Rejected shapes stay rejected: warn-first rollout (the D169 "warn as a soft status" class) and
  hard-fail-the-run. (TM-B5)

---

## §2 The cursor — one durable temporal record per run

### 2.1 What the cursor IS — TM-C1

The run's one log IS the cursor: the existing append-only board upgraded — a run-header block,
new seam-authored line TYPEs, structured payloads as pointed-to JSON files (the existing
escalation line+payload idiom, `protocol/escalation.md:3`). One log — D135's letter and spirit;
**the grammar change rides the pinned-clause deliberate two-step** (`protocol/board.md` is
clause-pinned). The concept is NAMED the **CURSOR** ("it marks where in the process we are
sitting and where it is currently executing" — operator verbatim; glossary entry live in
`CONTEXT.md`); file/skill heritage names (board → cursor) migrate under §7. Rejected and staying
rejected: a sidecar structured log (the second journal D135 forbids) and a git-only cursor.
(TM-C1)

### 2.2 The grammar migration — ONE migration, ONE pin re-approval — R-M3 · TM-C6

Everything below lands in the SAME build wave with ONE re-approval of the pinned clause:
appended-field line form, the full new TYPE enumeration, the run-header block, and the
fold/parser updates. (R-M3)

**The exact BNF** (compile specification under R-M3's explicit delegation — "Exact BNF in the
DESIGN"; delimiters and payload-path convention are compile decisions recorded here):

```bnf
cursor        ::= run-header line*
run-header    ::= "RUN " run-id NL
                  ( "prev-run: "     run-id  NL )?     ; iteration chain (re-loop/loop-back)
                  ( "parent-run: "   run-id  NL )?     ; tree structure (child runs)
                  ( "prev-segment: " path    NL )?     ; chained segmenting (reserved NOW,
                                                       ;   built when a real cursor gets big)
run-id        ::= "run-" utc-compact "-" hex+          ; TM-C2: sortable, humane; randomness
                                                       ;   mints identity only (Determinism
                                                       ;   Doctrine)
line          ::= utc FS seq-field FS agent-id FS type FS task-id FS msg NL
FS            ::= " | "
seq-field     ::= seq ( "~" parent-seq )?              ; parent-seq = dispatch lineage: the seq
                                                       ;   of the SPAWN line this line descends
                                                       ;   from (worker-line lineage stamps)
seq           ::= digit+                               ; monotonic per run
type          ::= worker-type | orch-type | seam-type
worker-type   ::= "CLAIM" | "DONE" | "BLOCK" | "ESCALATE" | "NOTE" | "PROGRESS"
orch-type     ::= "DECISION"
seam-type     ::= "PHASE" | "VERDICT" | "SPAWN" | "DOWN" | "DENY"
msg           ::= one-line-text ( " payload=" path )?  ; pointed-to JSON payload (escalation
                                                       ;   idiom); REQUIRED for VERDICT
```

- **Seq assignment:** the appending writer stamps `(observed max)+1`. Seam-authored lines come
  from the single seam writer and are therefore unique; concurrent worker appends may race —
  duplicate worker seqs are legal and ordered by file position. **Ordering of record =
  (runId, seq) + parent fold-order; wall-clock is never load-bearing** (closes the
  `board.md:52-55` clock-trust flag). Lineage references always target seam-authored (unique)
  seqs. (TM-C6 adoptions #3/#4, TM-C7)
- **Header semantics:** `prev-run:` walks history (iteration); `parent-run:` walks the tree
  (roll-up folds). Both pointers, distinct semantics, one ruling. A root-level re-loop has no
  parent by definition: `prev-run:` chain only. (R2-M2, R3-L1)
- Payloads live under `.kata/payloads/<runId>-<seq>.json` (tier-3 cache; durability is the
  snapshot's job, §2.5). VERDICT payload schema: `{verdict, evidencePointers[], judgeDispatchSeq,
  runId}`. (TM-C4)
- The old 5-field grammar (`protocol/board.md:9`) parses nowhere after the migration wave — the
  fold/parser updates (including the K3 concurrency snippet rewrite to a cross-cursor
  (runId, seq) fold) land in the same wave. Erratum carried: the fanout-survey's "K3" anchor for
  the schema is the **K5** schema (`protocol/board.md:57`). (R-M3, TM-C7 element 6, R-L2)

### 2.3 Writer classes — R-M2

PHASE / VERDICT / SPAWN / DOWN / DENY lines are **seam-authored** (engine mint/capture paths +
the hook), never worker-authored. "Orchestrator-only" is corrected: the conductor's
pre-orchestrator phase events are written by the seam functions it calls. Worker types
(CLAIM/DONE/BLOCK/ESCALATE/NOTE/PROGRESS) and orchestrator DECISION keep their existing authors
and invariants. Children NEVER write the parent's log: at abandon-with-rendezvous **the parent's
seam writes the DOWN record** by reading the child cursor's terminal state at the next parent
seam act; unrendezvoused orphans reap at seam init. (R-M2, R2-M3, TM-C7 element 3)

### 2.4 Run identity + the run-membership law — TM-C2 · R-H2 · R3-H1 · R2-M6

- The seam mints `runId` at run start (one seam act = cursor rotation + header write). It
  stamps: the cursor header · every dispatch record · every gate artifact (`RESULT.json` gains
  `runId`) · report filenames (making `observability.md:18`'s promise TRUE — it was a FALSE row)
  · a new **`Kata-Run: <runId>` trailer on integration commits** (run membership survives
  machine change via git — the only (iv)-durable tier). (TM-C2)
- **`evidence_is_current` is EXTENDED to run membership** (`run_result.py:122` seed): evidence
  is credited ONLY if the SHA is fresh AND the runId matches the live run — fail-closed on every
  old artifact (closes the July-artifact-read-raw class completely). (TM-C2, TM-D5)
- **The run-membership law, verbatim (R-H2):** gate evidence must carry the EXACT runId of the
  run being gated; ancestor/prior-run artifacts are legal as *inputs* but never as gate
  evidence; the sanctioned cross-run path is the parent consuming a child's recorded DOWN/VERDICT
  summary (which carries the child's runId) at fan-in/close. Each wave-loop's gate uses its own
  evidence; a re-loop pass re-emits its gates.
- **The green-at-fork baseline RESULT is an input, never gate evidence:** recorded in the
  consuming run's cursor as an input reference carrying its origin runId; the arm/re-loop's
  regression gate compares against it and emits ITS OWN result under its own runId. (R2-M6)
- **Crash-resume ADOPTS the runId; rotation happens only at run START.** Seam init
  distinguishes mechanically: **new run** (no live cursor, or the live cursor's run is closed)
  ⇒ rotate + mint; **resume** (live cursor with an unclosed run) ⇒ ADOPT the header's runId,
  reap orphan records, continue — pre-crash gate artifacts remain evidence (exact-runId rule
  satisfied), which is what makes the mid-gate-resume claim of §2.5 true. A resumed session
  never re-mints; a re-loop and a loop-back always do. (R3-H1)

### 2.5 Durability: snapshot cadence, per-run trail refs, offered push — TM-C3 · R-M4 · RS-L3 · R3-M5

- **Trail snapshot cadence fires on every PHASE and VERDICT append** (existing fail-soft
  `kata_trail` machinery) — mid-gate resume without re-running the gate. So that TM-C4's
  "durable at the moment they exist" claim is true, the snapshot content extends from board-only
  to the cursor file + its pointed-to payloads (compiled jointly from TM-C3 cadence + TM-C4
  durability; the snapshot is the mechanism that makes verdict persistence real). (TM-C3, TM-C4)
- **Per-run trail refs** — `refs/kata/trail/<runId>` — eliminate fan-out snapshot contention
  (per-arm cursors get per-arm durability); the legacy ref is unchanged for BC. Expected skip
  rate becomes a measured cursor metric at build. (RS-L3)
- **Trail push is OFFERED at the human push gate** (closeout Decision 2, alongside
  commit/push/merge; config-rememberable `cursor.pushTrail`) — presented AS the resilience
  option. Default stays never-push (BC, house guard; consent is the operator's). (TM-C3)
- **Resilience levels are DEFINED and DERIVED, never asserted:** **full** (trail push on +
  snapshots verified — the "full" claim requires a **push receipt recorded on the cursor**,
  never the config flag) · **local** (snapshots verified, no push) · **degraded** (skips
  detected). The snapshot skip sentinel becomes a recorded cursor event at the seam call site,
  so the declared level is a fold over recorded fact. (R-M4, R3-M5)
- The healthy default run declares `resilience: Partially verified (local)` — the run-start
  wording must read as honest state, not a defect report. (Pass-1 SHIP residual 6)

### 2.6 The phase model — the NAMED vocabulary — TM-C5 · pass-1 residuals 1 and 3

PHASE cursor events span the FULL Kata Loop. The phase vocabulary (closed enum; compile
specification under TM-C5's "exact phase vocabulary = design-doc detail" delegation):

```
INITIATION · GRILL · AUTHORING · FREEZE · EXECUTION (parameterized wave=<n>) ·
FINAL-GATE · CLOSEOUT · LOOP-BACK
```

PHASE msg grammar: `open <PHASE> [k=v …]` | `close <PHASE> [k=v …]` | `run-closed [k=v …]`.

- **INITIATION and AUTHORING are named phases** — the weakest governor rung's predicate reads
  the open INITIATION/AUTHORING event (§1.4). (Pass-1 residual 1, R3-H2, R4-H1)
- **"Run is closed" is a RECORDED terminal state, never convention** (the D169 class one layer
  down): the terminal `run-closed` PHASE line is written exactly once by `close_run`; nothing is
  legal on the cursor after it; `run_start`'s resume test reads it (§2.4). (R4 residual 3,
  pass-1 residual 1)
- The conductor and orchestrator are **phase-aware by contract**: they read position from the
  cursor, never re-derive it from context memory (feeds the BL-N20 agent definitions).
  **Closeout Decisions 1–4 land as structured cursor records** — including backout-approved,
  the highest-stakes previously-unrecorded event — and the loop-back event is recorded with the
  `prev-run:` chain pointer. (TM-C5)
- This closes the blind zones (mid-grill / mid-freeze / mid-closeout invisible to restore —
  cursor dossier §C). (TM-C5)

### 2.7 Tree-of-runs: fan-out, arm registry, close policies, reducers — TM-C7 · R-M8 · R2-M2/M3 · RS-L2

**The two-tier law:** in-wave tasks stay lines on the parent's cursor; bakeoff arms, Backlog
Burn wave-loops, and Kitchen bakes mint **child runs** (own runId + cursor + worktree,
`parent-run:` header). **D135 holds via arm = run** — ruled explicitly: one cursor per run stays
true at every tree node. (TM-C7)

All eight design elements are adopted (`evidence/fanout-survey.md`):

1. Two-tier fan-out law (written classification rule, above).
2. **Freeze-minted arm registry** — the frozen PLAN/benchmark_def carries the whole tree BEFORE
   dispatch: `arm_label → pre-minted child runId → worktree root → parent-close policy`; resume
   reads the registry (exactly-once spawn). Planning-agent alignment: the run structure is built
   before execution.
3. **Dispatcher-witnessed SPAWN / DOWN-with-reason on the parent cursor** — children never write
   the parent's log (DOWN actor per §2.3).
4. **Per-arm parent-close policy:** `cancel | park | abandon-with-rendezvous` — the last is
   MANDATORY across BBM-12 wave rollovers (the Continue-As-New hazard).
5. **Declared fold reducers; bounded child summaries only** — an undeclared concurrent merge is
   a fail-loud refusal.
6. **Ordering = (runId, seq) + parent fold-order** as order-of-record.
7. **Fan-in as merge-parents + trailers** — `Kata-Run:` + new `Kata-Arm:` trailer, fail-closed
   on conflict, **mechanical-only fan-in commits** (no evil merges — PD-2 in git history).
8. **Bakeoff selection as recorded supersede** — a DECISION records winner + losing runIds;
   `-s ours`-shaped, never content blending; human version-select per standing rule.

All seven named hazards carry their answering patterns per the survey. (TM-C7)

- **Re-loop of a wave = a sibling child:** `parent-run:` = the same parent (tree — roll-up folds
  walk this); `prev-run:` = the failed sibling (iteration — history walks this). (R2-M2)
- **Child runs NEVER rewrite the committed `kata.config`**; per-arm variation lives ONLY in the
  freeze-minted arm registry (committed with the plan). Fan-in cannot conflict on config by
  construction. (R-M8)
- **Abandoned-arm process disposition:** at parent close, arms are killed unless their close
  policy names a successor rendezvous; a closed run's arm commits are quarantined (never merged
  into graded results); the write-after-close residual is stated (§11). (RS-L2)
- **Rider 1 — learning rolls UP the tree:** child-run closeout learnings fold to the parent for
  in-loop learning or total-loop learning (the BL-N16 run-end session). The job-scoped/ephemeral
  vs substrate/durable learning-scope taxonomy is ASSESSED AT THE BL-N16 GRILL (seeded into its
  cross-doc note) — this DESIGN does not resolve it. (TM-C7 rider 1)
- **Rider 2 — overruns pre-assessed:** small result overruns are acceptable only when
  pre-assessed and optimized by the orchestrator — planned, declared overlap tolerance at
  partition/dispatch time; the fail-closed clobber protection stays for any UN-assessed overlap.
  Lands in the partition/plan rules (BBM-2 seam). (TM-C7 rider 2)

### 2.8 Projections + provenance — TM-C6

- The learning graph (BL-N16) **builds around the cursor** — the cursor is the truth component;
  graph projections are **folds** over it, and **every derived graph fact carries the
  (runId, seq) that produced it**, so a superseding DECISION invalidates downstream facts
  mechanically (Graphiti-derived, projection-layer only). Fold outputs are named **projections**
  (glossary term live in `CONTEXT.md`). (TM-C6)
- Hermes' distill-for-load binds: folds and context injections consume bounded distillations,
  never the raw log. (TM-C6)
- Fold-cache snapshots live in `.kata/` as pure cache (ES discipline; D81 licenses). Stated
  invariant: **"fold is pure; side effects only after fold completes."** (TM-C6)
- Views (rail, statistics/BL-N14) are folds, never second sources. (TM-C6, TM-H3)

---

## §3 Truth Serum v1 — detectors, the deferral ledger, gate preconditions

### 3.1 Detector set v1 — the 8-class matrix, MECH blocks / SEMI signals — TM-D2 · TM-D3

**Standing humility, stated wherever v1 is described (burn-02 meta-finding, verbatim):** *"the
judgment+human layers found all of these; the automated mechanical gates found none."*
Detectors ATTEST and NARROW; judges judge. (TM-D2, TM-E2)

**BLOCKING (gate-refusing) in v1:**

| # | Detector | Spec | Anti-vacuity companion (TM-D3) | Anchors |
|---|---|---|---|---|
| B1 | Stub-body AST scan | Pure AST predicate over `graph_gen`'s tree-sitter spans (an artifact already generated); syntactic families: `pass`-only / TODO-comment-only / `raise NotImplementedError` / log-only bodies / hardcoded-empty returns — in task-modified files; a match blocks unless the line carries a `DEF-*` reference (the D3b rule, §3.2). Mechanical suppressors for legitimately-empty classes (ABC/protocol-handler/`__init__.py` detection) are explicit predicates; residual legitimacy judgment routes to the signal channel, never silently suppresses | refuses to certify a scan over zero functions / an absent or stale graph artifact (`repoHash` check) | TM-D2, detectability class a, TM-D1 |
| B2 | Silent-deferral three-way join | PLAN (`parse_plan_tasks`, `kata_restore.py:235`) ⋈ tree (`footprint` / `Kata-Task:` trailers) ⋈ DEFERRED.md (hardened schema §3.2): every plan item resolves to built-and-exercised / recorded-deferral / **named drift** | refuses over an empty plan-task set or an unparseable DEFERRED.md | TM-D2, TM-D1, detectability class d |
| B3 | Debt-marker-without-`DEF-*` | Any TBD/FIXME/XXX in a task-modified file is a BLOCKER unless the same line references formal follow-up (`DEF-*` / issue ref) — the gsd D3b rule, adopted | refuses when the modified-file set is empty (nothing scanned ⇒ nothing certified) | TM-D1, TM-D2 |
| B4 | Stale/wrong-run evidence | The extended `evidence_is_current` (§2.4): SHA fresh AND runId exact | refuses when handed no artifact (absence ⇒ refusal, not pass) | TM-D2, TM-C2, TM-D5 |
| B5 | Citation-existence resolver | Every `file:line` / wikilink citation in a gated artifact resolves (the `check_wikilinks` precedent); existence MECH — "support" stays judgment routed to grounding (§4) | refuses to certify an artifact it could not read; zero-candidate artifacts are reported as zero-candidate, never as "all citations resolve" | TM-D2, detectability class f |
| B6 | Mutation-proof RE-RUN by the gate | NEVER the worker-reported union — the engine re-runs the claimed mutation set per task (§3.6) | the prover must itself be proven able to fail per platform (BL-X14 ordering, §3.6) — TM-D3 applied to the prover | TM-D2, R2-H2, R3-H3 |

**SIGNAL-ONLY in v1 (feeds judges via the attested fact table, never blocks):**

| # | Detector | Spec + honest limit | Anchors |
|---|---|---|---|
| S1 | Unwired-symbol detection | Graph ref edges + tests-path filter + `edge_honesty` import-level; **calibrated on the T6–T11 orphan corpus** (ready ground truth). Honest limits carried verbatim: call-only edges, bare-name matching, fabricated `src` attribution; dynamic imports invisible; entry points outside the graph look dead | TM-D2, detectability class b |
| S2 | Prose-claim narrowing | Reuse-claim trigger-phrase set + adjacent `file:line` requirement, resolved via B5; producer-existence guard (`check_reuse_claims_producers_exist` precedent). Extracting arbitrary claims from prose stays judgment | detectability class c |
| S3 | Honesty-label propagation | Clause-pin machinery where a label is a required term on a named artifact; token presence is forgeable (KH-T02) — the doc-layer half is owned by EV-1's badge registry (§9) | detectability class h, EV-1 |

**The anti-vacuity companion law (TM-D3):** every detector ships with its
anti-vacuous-check companion — it REFUSES to certify over zero inputs / absent preconditions
(the `check_reuse_claims_producers_exist` / `surface_hash`-zero-file / protocol-folder-zero-scan
pattern, now a stated design law).

**Judge tripwires (TM-D3 + R-M6):** the kata-validate tripwire generalizes to the judge stack —
every judge proves it can still fail against a known-bad corpus before its verdict is credited.
**Corpora activate PER JUDGE as they land** (the §7 activation-order pattern): a judge without a
corpus is declared **Honor-system**, never blocked; corpus ownership = the build wave wiring
that judge's precondition; home = per-judge fixtures on the kata-validate precedent; proof
cadence = per-build (CI) with the corpus hash on the cursor. Deny-everything dissolved. A
detector or judge that cannot demonstrate failure-capability is **Dormant, not Verified**.
(TM-D3, R-M6)

**Deferred blocks = BL-N24 (Truth Serum v2),** with per-item promotion criteria and the standing
rule: **a v1 scope cut lands in BL-N24 or it is a PD-1 silent deferral.** (TM-D2 rider)

### 3.2 The deferral ledger — hardened — TM-D1

- **Pinned canonical paths:** `.planning/DEFERRED.md` + `.planning/ASSUMPTIONS.md`.
- **Machine schema:** formalized heading grammar
  `## DEF-<n> — <title> · <STATUS> (<ISO-date>)` with required fields **What / Why /
  Provenance / Owed-to** and the closure discipline (closing commit; "wired, not merely
  captured"). ASSUMPTIONS.md gets the same treatment (entry id `ASM-<n>`, assumption /
  provenance / grilled-or-not).
- **Approval record on operator-approved deferrals:** `accepted_by` / `accepted_at` — the
  gsd-override shape — answering BL-N01's open question "where does approval get recorded so
  the gate can check it".
- **`protocol/deferral.md` is a NEW protocol contract**, registered in `REQUIRED_PROTOCOL` and
  clause-pinned, so the rules themselves are tamper-evident (never the pre-2026-08-03
  unguarded-protocol class). Draft contract text (to be landed verbatim-in-substance at build):

  > `protocol/deferral.md` — the sanctioned-deferral ledger contract. Canonical paths:
  > `.planning/DEFERRED.md`, `.planning/ASSUMPTIONS.md` (append-only, checkpoint-as-you-go).
  > Entry grammar: `## DEF-<n> — <title> · <STATUS> (<date>)` with required What / Why /
  > Provenance / Owed-to fields; ASSUMPTIONS entries `## ASM-<n>` likewise. STATUS enum:
  > `OPEN | ACCEPTED | CLOSED`. An operator-approved deferral MUST carry
  > `accepted_by: <who>` and `accepted_at: <ISO-utc>`; a gate may credit an approval ONLY from
  > these fields. Closure requires the closing commit reference — captured is not closed. A
  > debt marker (TBD/FIXME/XXX) in gated work without a `DEF-*` reference on the same line is
  > a BLOCKER. Detectors parse this grammar mechanically; a parse failure is a refusal, never
  > a skip.

  (TM-D1; the exact wording rides the authored-artifact gate at build like any contract text.)

### 3.3 The gate-precondition map — TM-D4 · R-M6 · pass-1 residual 4

ALL gates gain a truth-serum fact-artifact precondition (**refuse-not-warn**, the locked house
shape) in this program's build. Map over the gate inventory (`evidence/gate-inventory.md`; the
inventory's condensed rows stand for the ~40-gate sweep):

| Gate | Fact preconditions (refusals, not warnings) | NEW artifacts created |
|---|---|---|
| Freeze gate (D169) | DESIGN + PLAN present; governing-ledger `converged` record (§1.4); per-task `evidence:` declarations present and grammar-valid (§5.1, RS-H1); arm registry present for tree runs (§2.7); contract-edge freeze artifacts; **green-at-fork baseline RESULT recorded (as INPUT, §2.4)** | green-at-fork baseline RESULT |
| Task gate | per-task gate record: verify re-run output + lane check (`footprint`) + **engine mutation re-run record (§3.6)** + B1/B3 detector passes + B4 evidence identity | **per-task gate record** |
| Wave gate (BBM-12) | all member task-gate records + integration re-gate record + VERDICT records for the wave's judges | wave-gate record |
| Final gate — kata-evaluate | RESULT.json + `evidence_is_current` (the BL-X11 fix — §3.4) + the grounding-attested fact table (§4) + **grounding-attested mutation record set (R-M10)** + per-gate parsed counts (BL-X13 fix, §3.4); verdict persisted via capture (§1.6) | — |
| kata-review | attested fact table; regenerate-and-diff duty captured in the VERDICT payload evidence pointers | proof-it-ran evidence pointers |
| kata-slop-check / inline-eval | fact table; tripwire status per R-M6 (Honor-system until corpus lands) | — |
| Grill convergence | **convergence-pass record** — incl. proof the Advanced double-pass ran as two distinct dispatches, via seam records | **convergence-pass record** |
| Grounding gate | engine-attested comparisons only (§4) | attested fact table |
| Sprint stop-gate | consumes the PERSISTED evaluate VERDICT record with identity check (never a conversational value) | — |
| Closeout / close | §5.3's record requirements; Decision 1–4 cursor records; trail push receipt if `full` resilience is claimed | close verdict artifact |

- **Wave-phasing WITHIN the build is the frozen PLAN's job, not a scope cut**; any true scope
  cut lands in BL-N24 per the TM-D2 standing rule. (TM-D4)
- **The never-a-de-facto-mandate law carries into every per-gate fact-set:** no gate requires a
  grill artifact of a run that legally has none (D71 shapes). (Pass-1 residual 4)
- Per-judge tripwire preconditions activate per R-M6 (§3.1), and the mutation precondition
  activates per platform per §3.6 — activation ordering is part of the precondition itself,
  never a silent soft mode.

### 3.4 Evidence identity everywhere — TM-D5

Every evidence consumer routes through the extended `evidence_is_current` (SHA fresh AND runId
exact — §2.4): **kata-evaluate's machine-input step FIRST (the BL-X11 fix)**, then
review / debrief / closeout / sprint-stop. The RESULT parsed-counts cross-gate chimera
(**BL-X13**) is fixed in the same build (per-gate counts or the honesty flag, per its filing).
BL-X11 and BL-X13 fold into this build. (TM-D5)

### 3.5 The `evidence:` grammar — closed, exec-safety-registered — RS-H1 · pass-2 mediums 3–4

The per-task `evidence:` PLAN field (§5.1) is a NEW execution capability and gets the
exec-safety treatment — **a closed grammar, three forms only; a freeform command string is
REFUSED at the freeze gate:**

| Form | Semantics | Safety treatment |
|---|---|---|
| `artifact:<repo-relative-path>` | NEVER executed — existence/wiring checked | path guarded via the `_guard_path` pattern (CWE-23 traversal treatment — pass-2 medium 4; live precedents `benchmark_def.py:85`, `benchmark.py:82`) |
| `test:<pytest-node-id>` | fullmatch grammar on the node id, compiled to structured argv `[python, -m, pytest, <id>]`, no shell | **REUSES the `_guard_node_id` grammar** (pass-2 medium 4; live precedents `benchmark_def.py:805`, `benchmark.py:106`) |
| `probe:<registered-name>` | names an argv template from a committed probe registry — never a freeform command | registry committed with the repo; unknown name ⇒ refuse |

- The per-task verify command the mutation re-run uses gets the SAME treatment (trust domain:
  LLM-authored ⇒ compiles through the grammar or is refused). (RS-H1)
- **The mutation sink's `shell=True` conversion / re-domaining rides RS-H1** (pass-2 medium 3):
  the mutation runner's command execution converts to structured argv under the same grammar.
- The field + grammar + argv + trust domain are registered in `protocol/exec-safety.md` BEFORE
  build, per its own new-capability law. (RS-H1)

### 3.6 The mutation re-run — actor, cost basis, scope, sampling, activation — R2-H2 · R3-H3 · R-M10 · R4 residuals 1–2

- **Category + corrected cost premise (PD-2 correction carried):** the re-run is a deterministic
  ENGINE act — but `prove_non_vacuous` is **NOT milliseconds**: it copies the project tree to a
  sandbox and runs the test command twice per asserted line (`mutation_run.py:218-315`). TM-E1's
  agent-overhead ruling governs AGENT dispatches and is untouched. (R2-H2 as corrected by R3-H3)
- **Per-task:** the orchestrator triggers the engine re-run at each task gate using **the task's
  OWN verify command** (narrow by construction), re-running the worker's claimed mutation set
  with a declared cap: all lines when ≤ N (default **N=5**); beyond that the orchestrator
  samples N and **records the sampling on the cursor — no silent truncation**. Sampling uses a
  **stated deterministic sort key** (doctrine laws 9/10 — no randomness, explicit total order;
  compile specification: sort by `(file path, line number)` ascending, take the first N). (R3-H3;
  R4 residual 1)
- **Final gate:** the stack-head grounding pass re-runs a sampled subset against the gate
  command and **attests the whole set's records** (present + current + per-task complete) as the
  evaluator's precondition — the evaluator refuses without a grounding-run mutation record. The
  worker-union hole closes at a named seam. (R-M10, R2-H2)
- **Activation ordering (BL-X14):** the blocking mutation precondition ACTIVATES per platform
  only after 🔴 BL-X14 closes (the prover proven able to fail on that platform — TM-D3 applied
  to the prover itself); until then the precondition is declared **Honor-system** on that
  platform. **No Linux task gate fail-closes on a Broken prover.** (R3-H3; mid-close evidence
  event: CI-gauntlet Guardian status today = **Broken**; BL-X14/BL-X15 filed, fixes route
  through the loop per TM-A1.)
- **Honest residual, stated in-contract:** the re-run proves the worker's CLAIMED mutation set
  bites — **claimed-set completeness stays worker-asserted** (§11). (R4 residual 2)

---

## §4 Grounding — two-tier: engines everywhere, the agent at the stack head — TM-E1 · TM-E2 · R-M10

- **Tier 1 — engines at every gate, always** (near-free; §3.3). (TM-E1)
- **Tier 2 — the grounding AGENT stands FIRST in the validation stack** at the greater-loop
  level: ~3–5 bounded dispatches per run, economy-tiered under D131 (fact-orchestration, not
  judgment). (TM-E1)
- **Signal-triggered at other gates** — the agent fires only when an engine flags what it cannot
  attest alone. Trigger table: a reuse-claim phrase · an unattestable DONE claim · a research
  finding · a resolved-but-unread citation. (TM-E1)
- **Telemetry-informed promotion:** per-gate injection expands only where run data shows it
  cheap — tracked in BL-N24 per the TM-D2 standing rule. (TM-E1)
- **Overhead record (modeled, labeled as such):** per-task agent dispatches ≈ +15–30 serialized
  minutes on a mid-size run; stack-head-only ≈ +2–5 minutes per run; engines are milliseconds
  and token-free — EXCEPT the mutation re-run, whose real cost basis and caps are §3.6's.
  (TM-E1, corrected by R3-H3)
- **The charter:** the agent RUNS the engines and emits the attested fact table judges consume;
  **agent proposes, engine attests**; AC-10 execute-the-tooling is its standing law; scope
  boundary — grounding attests FACTS pre-judgment, the challenger attacks JUDGMENTS post-hoc.
  Roster placement + agentDef land via BL-N20 (§10). (TM-E1)
- **The mutation re-run seam:** the stack-head grounding pass is the attestor of the mutation
  record set (§3.6). (R-M10, R2-H2)
- **Judge-input contract (TM-E2):** every judge's brief carries the attested fact table for its
  target (detector outputs + grounding verdicts + evidence identity). Judge contracts are
  rewritten to (a) judge ON the facts — never re-derive what an engine attested, never accept a
  worker claim the table contradicts; (b) state residual-judgment surfaces explicitly (quality,
  design fidelity, threat reasoning — the legitimately-judgment set per the gate inventory);
  (c) carry the TM-D3 tripwire; (d) open with the pinned `VERDICT: <enum>` first line (R3-M2).
  The burn-02 meta-finding travels with every description. (TM-E2)

---

## §5 The close — plan-grounding, fail-closed

### 5.1 Evidence declared at freeze — TM-F1 · R-M9 · RS-H1

- **No plan item freezes without its completion-evidence declaration** — one line per item,
  authored by the plan-author, gated at the freeze gate. (TM-F1)
- **Mechanism:** a PLAN frontmatter **per-task `evidence:` field**; `parse_plan_tasks`, the
  plan-author skills, and the freeze gate extend to carry/check it — added to §7's migration
  scope explicitly. Grammar closed per §3.5. (R-M9, RS-H1)
- **Rider 1:** declarations and their resolution are **tracked in the cursor machinery** — item
  done-ness is a cursor fact, not a report-time derivation. (TM-F1)
- **Rider 2:** the join feeds the final report — **truth metrics at the final report**: items
  resolved, evidence per item, drift named, deferrals with approvals; **leftovers are always
  displayed, with the option to execute them in another run** (ties closeout Decision 3 /
  BL-N19's re-loop route). (TM-F1)

### 5.2 The three-way join — TM-F1 · TM-D1

The close join is TOTAL: **PLAN (`parse_plan_tasks`) ⋈ tree (`Kata-Task:` trailers /
`footprint`) ⋈ DEFERRED.md** — every item mechanically resolves to **built-and-exercised /
recorded-deferral / named drift**. Behavioral deliverables resolve through their declared
`evidence:` form (§3.5) rather than degrading to file-touch heuristics. (TM-F1, detectability
class d; the decisive seed — trailers and `parse_plan_tasks` both exist, nothing joins them
today — gate-inventory §C.)

### 5.3 Fail-closed close verdicts + re-loop routing — TM-F2 · R3-M6

- The close emits its verdict artifact (TM-C4 shape: VERDICT line + payload). A failing verdict
  leaves exactly TWO legal paths: **another loop pass** (BL-N19's mechanical route, wave-level
  per BBM-12) or **recorded operator acceptance** (the TM-D1 approval-record shape,
  `accepted_by`/`accepted_at`). **The seam refuses run-closure otherwise.** (TM-F2)
- TM-A1's remediation routing lands here: a Broken or Dormant-claimed-as-Verified finding is
  NEEDS_WORK-class and routes to re-loop — "if anything is false or facade it should be another
  loop pass" (operator verbatim). No out-of-band doc edits. (TM-A1)
- **D134 reconciliation, stated:** tier-2 integration trailers remain **AUTHORITATIVE for
  DONE**; the cursor gates ONLY fact classes for which it is the system of record (verdicts,
  phases, denials, spawns) — for DONE it corroborates, exactly as D134 rules. **The close's
  refusals bind per fact class to that class's system of record.** Absent-records refusal is the
  backstop for capture-edge loss of any kind (§1.6, RS-L1). (R3-M6)

### 5.4 Provenance drift check — TM-A2 · R-M8 · R-L1 · RS-M6 · RS-M7

- Machine-specific values (personal paths) migrate to `.kata-settings.json` (the existing
  machine-local home); `kata.config` and `INTENT.md` become clean, **committed run provenance**
  — completing the cursor's machine-change story. Erratum carried: `state.md:41`'s tier-1 claim
  covers `kata.config` (via the delivery row) and never claimed `INTENT.md` — committing
  INTENT.md is a NEW ruling under the resilience directive, not a restoration. (TM-A2, R-L1)
- **The drift check:** at branch close, if `kata.config`/`INTENT.md` as committed do not match
  what the run actually executed (per the cursor record), the close FAILS and the run routes
  per §5.3. **Tree semantics:** the drift check for a tree = committed config + arm registry vs
  EACH cursor's recorded execution; child runs never rewrite committed config (§2.7), so fan-in
  cannot conflict on config by construction. (TM-A2 rider, R-M8)
- **Consent:** committing `INTENT.md`/`kata.config` into a TARGET repo is an outward act with a
  **first-run consent moment** (per-target, remembered — stored machine-local in
  `.kata-settings.json`, pass-2 low 9); the harness's own repo consents by standing config.
  Redaction is not consent; both apply. (RS-M6)
- **Redaction at the commit act:** detected secret/key/PII classes fail closed **at the commit
  act** (branch close, not mint — closing the TOCTOU window); the scrub extends
  `learn_feed.redact`'s class table (one scrub, not two); undetected content is a stated
  residual (§11). Full two-point spec in §8 S4. (RS-M7, pass-2 high 1)

---

## §6 The presentation layer — trust shown, not asserted

### 6.1 The four surfaces — TM-G1+G3

1. **Run-start box:** in/NOT-in kata scope + enforcement level + resilience level + capture-edge
   grade (all seam-derived, §1.7/§2.5). (TM-B2.4, TM-C3, TM-G1)
2. **Per-gate receipts:** attested fact tables rendered as data-boxes; **visible REFUSALS with
   reasons** — every DENY and gate refusal is shown. (TM-G1, TM-B5)
3. **The final report's truth metrics:** per-item evidence, drift named, deferrals with
   approvals, leftovers with the run-again option (§5.1 rider 2). (TM-F1, TM-G1)
4. **The per-run trust ledger** as a user-facing artifact, Guardian-termed. (TM-G1)

Receipts must land where the operator looks — the CI-red-12-days event is the direct evidence
row for this surface (ledger mid-close evidence event). (TM-G1)

### 6.2 The Guardian scale — the ONLY user-facing trust vocabulary — TM-A1 · R2-M4 · R3-M5

**Verified · Partially verified · Honor-system · Dormant · Broken** — naming what is CHECKING,
not the code's condition. The internal audit categories (FACT/PARTIAL/PROSE/FACADE/FALSE) stay
as the diagnostic layer only. Baked into `CONTEXT.md`. (TM-A1)

**ONE trust vocabulary:** every user-facing trust claim is a Guardian term; mode words are
technical qualifiers in parentheses after the Guardian term, never standalone claims. **The
complete Guardian↔mode table (no builder invention):**

| Surface | Guardian (mode) values |
|---|---|
| enforcement | Verified (intercepting) · Partially verified (bash-leg) · Dormant (pre-activation) · Honor-system (detection-only host) |
| capture | Verified (post-edge) · Honor-system (engine-by-conductor) |
| resilience | Verified (full: push receipt recorded on the cursor, never the config flag) · Partially verified (local) · Honor-system (degraded/skips detected) |

(R2-M4, R3-M5; deny-tripwire no-result ⇒ enforcement falls to **Dormant**, never inheriting a
prior declaration — pass-2 high 2.)

### 6.3 The rendering law — TM-G2 · RS-M13 · pass-2 medium 8

- Every displayed fact carries its provenance: which check, which artifact, which runId/seq —
  the quote-verbatim-never-recompute discipline generalized. Machine facts render as data
  (boxes, per the UX grammar); judgment renders as prose (dividers). The presentation layer
  inherits PD-2 — an opinion in fact clothing is the facade one layer up. Detector humility
  ("no unattested fact enters a gate," never "no defect escapes") travels to every trust
  surface. (TM-G2)
- **ALL cursor-derived text rendered to any surface is control-character/ANSI-stripped** (the
  UX-30 glyph-first ruling applied as a security control) — a cursor line cannot repaint a fake
  receipt. **Glyph-mimicry is answered by provenance-fields rendering, not stripping alone**
  (the receipt's provenance fields are seam-derived, so a mimicking line cannot supply them).
  (RS-M13, pass-2 medium 8)

### 6.4 Minimal declaration ships in the seam wave — R2-M1

A MINIMAL run-start declaration (plain-text enforcement + resilience + capture-edge Guardian
line, seam-derived) ships **in the seam wave** — §7's interim honesty has its surface from day
one; the full UX-grammar box lands in the presentation wave. (R2-M1)

### 6.5 UX sequencing — TM-A3 correction · R-H4 · R2-L1/L2

Ground truth (corrected per PD-2, R-H4): the UX system is DESIGNED to freeze-candidate
(`DESIGN.md` rev 3, `status: DRAFT — freeze-candidate`); rounds R1 and R2 both returned
CONVERGE-HOLD (the round-2 record lives INSIDE `CONVERGENCE-R1.md` — R2-L1); rev 3 was
conductor-verified, NOT independently convergence-reviewed; **zero UX code is shipped**. The
trust surfaces **join the UX freeze-candidate as a pre-freeze addition**, extending the
operator's standing sign-off list by exactly this section (surfaced, not silent). **The combined
artifact (UX DESIGN revision 4 = rev 3 + the trust surfaces) receives a full fresh-context
convergence pass named round C1 before the operator's freeze sign-off.** The trust-model
program's **non-UX build does NOT block on the UX freeze** — only the presentation-layer build
wave does. (TM-G1+G3, R-H4, R2-L2)

### 6.6 Backlog truth status — TM-A3

Every backlog item carries a **truth-status mark**: lifecycle stage + Guardian verification —
`FILED · GRILLED · DESIGNED (freeze-candidate) · FROZEN · BUILT—Verified (with cited evidence) ·
CLOSED`. **"BUILT" is legal ONLY with the Verified evidence citation** (the §3 truth-serum
checks are what verify it) — an uncited BUILT is the PD-2 violation class itself. Immediate
correction already applied: BL-N06/N07 marked DESIGNED—freeze-candidate; the full retrofit of
existing items rides this build's loop passes (TM-A1 routing); the standing rule feeds BL-N11 as
a binding input. (TM-A3)

---

## §7 Migration + activation order — TM-H1 · R-M9 · R3-M3 · R3-L2

**Dependency order, binding:**

1. **Engine + cursor first** (seam API §1.3; grammar migration §2.2 with its ONE pin
   re-approval; minimal declaration §6.4 ships here).
2. **Skills in waves** — the ~52 launch sites in kata-orchestrate + the dispatched-skill inbound
   contracts rewrite to route through the seam; each wave is a loop pass per BBM-12. Judge
   contract rewrite (VERDICT first line, fact-table inputs, tripwires) rides these waves.
3. **The fail-closed hook is the LAST switch flipped**, activated only after every sanctioned
   path is migrated — a hook activated early would deny un-migrated legitimate prose sites, and
   a soft interim mode is the rejected warn-shape. Until activation, the run-start declaration
   honestly reports enforcement **Dormant** (Guardian terms make the interim truthful instead of
   soft). (TM-H1)

**Explicit migration-scope items (each named in the ledger, none optional):**

- Naming migration (board→cursor heritage: files, skills, prose) rides the same waves. (TM-H1)
- Stale `kata_dispatch` line anchors across five skills fix in wave 1 (already Broken rows).
  (TM-H1)
- **`ledger_status` live-corpus normalization:** the live free-prose ledger statuses
  (`GRILL COMPLETE…`, `GRILL DONE…`) normalize to the four-value enum — explicitly in scope.
  (R3-M3, R4 residual 5)
- **Plan-schema extension** (`evidence:` per-task field; `parse_plan_tasks` + plan-author
  skills + freeze gate). (R-M9)
- **INTENT schema amendment** (`status:` field + `freeze=True` argument) as an explicit
  additive amendment with its own two-step. (R3-L2)
- Per-platform mutation-precondition activation gated on BL-X14 (§3.6). (R3-H3)
- Per-judge tripwire activation per R-M6 (§3.1).
- The FALSE/FACADE promise rows become **work items in the build's first loop passes**,
  relabeled in Guardian terms with the mechanism cited when wiring lands — remediation routes
  THROUGH the loop, never out-of-band doc edits. (TM-A1)
- `protocol/exec-safety.md` registration of the `evidence:` capability happens BEFORE build
  (§3.5). (RS-H1)
- Wave composition and ordering details WITHIN this program are **deferred to the frozen PLAN**
  (§12) — this DESIGN fixes only the dependency order and the hook-LAST law. (TM-D4, TM-H1)

**Operator sequencing mandate (verbatim-intent, binding on the close):** *"As soon as this gets
frozen we will need to do a FULL DOCUMENTED handoff with agent orientation. That will have to
happen before we execute."* Sequence: grill close → design-author → plan-author → FREEZE (D169)
→ **full kata-handoff (STATE current-block rewrite + HANDOFF turnover block + the locked UX-15
agent-orientation format with its paste block) → THEN execution dispatches.** No build dispatch
before the handoff package is committed; a freeze without the handoff is an incomplete close.
(Ledger "Operator sequencing mandate".)

**Degradation honesty completes the interim (TM-H2):** hook absent/uninstalled ⇒ detection-only,
DECLARED at run-start (presence is live-probed at seam init — an uninstalled hook can never be
reported Verified); engine unavailable ⇒ no-legal-path park; settings drift detected at seam
init; `kata_scope` (via the run marker) guards everything — non-kata sessions untouched.

---

## §8 The security register — compiled as design constraints — TM-H4 + RS-* + the fifteen pass-2 residuals (absorbed in place)

**S1 — Forgery.** (TM-H4 S1, R2-M5, RS-M8)
- Dispatch-record fabrication: detected via cursor-lineage mismatch (TM-B4). Worker-line
  forgery: dispatch-lineage stamps (`~parent-seq`) mean a forged line must name a live
  seam-authored parent (TM-C6).
- VERDICT lines are **seam-authored** (wording per R2-M5) — but the conductor calls the seam,
  so the **adversarial-conductor residual stands and is stated**: detection at post-hoc
  verification, not prevention. The seam's prevention claim is scoped to drift, laziness, and
  prompt-obedience failure — the classes actually observed. (TM-B4, R2-M5)
- **Trust-boundary table for the record store + cursor:** writers enumerated per artifact
  (dispatch records: engine mint + hook claim; cursor seam-types: seam functions + hook;
  worker-types: workers; DECISION: orchestrator; payloads: seam). A worker CAN mint-and-launch
  and is caught post-hoc (stated). The register CLAIMS the strength it owns:
  **`refs/kata/trail` snapshots give git-object tamper-evidence for retro-edits of the cursor**
  — the post-hoc integrity anchor — and this tamper-evidence is **evidential-until-pushed**
  (machine-local until the operator opts into trail push; pass-2 low 10). (RS-M8)

**S2 — Injection.** (TM-H4 S2, RS-H1, RS-M13)
- Brief injection: advice/learning/facts are INLINED VERBATIM into briefs by ruling; **all
  inlined content is delimited as DATA** (the kata-validate payload-as-data discipline
  generalized to every brief assembly).
- Cursor-line injection: folds and any agent reading the cursor treat line content as data,
  never instructions; renderers escape + ANSI-strip (§6.3, RS-M13).
- Hook input parsing: structured, exec-safety-registered, never string-eval; the hook is a new
  sink and joins the exec-safety registry per its keep-in-sync rule. The exec-safety mechanical
  scan **extends to `adapters/**/hooks/*.py`** (or the hook's row is manual WITH that limitation
  stated — the scan-scope fact is recorded either way; preference: extend the scan — pass-2 low
  15). (RS-L4)
- The `evidence:` field + verify commands: closed grammar, structured argv, trust domains per
  §3.5 (RS-H1; sink re-domaining pass-2 medium 3; `_guard_node_id`/`_guard_path` reuse pass-2
  medium 4).
- Learning-substrate injection-persistence: already a BL-N16 ruling (security scan on
  self-written learning); cross-bound here.

**S3 — Hook trust.** (TM-H4 S3, RS-H4, RS-M10, R2-L3)
- The hook lives in user settings and can be absent/removed: seam init live-probes it and the
  declaration downgrades honestly — absence can never impersonate enforcement. (TM-H2)
- **Integrity is probed, never presumed (RS-H4):** the hook source carries a pinned FINGERPRINT
  (digest; updater prints, never rewrites — the protocol_fingerprint pattern; clause-pins cannot
  substitute for this on code). Seam init runs a **live deny-tripwire**: a self-test dispatch
  that MUST be denied; the Guardian enforcement declaration derives from that probe's result —
  file presence proves nothing (mid-session install reads present-but-inactive; a neutered hook
  reads present-and-green). TM-D3's failure-capability law explicitly covers the deny hook
  itself. **No-result posture: fail-closed to Dormant, never inheriting a prior declaration; the
  script tripwire + registration digest are jointly necessary** (pass-2 high 2).
- The settings entry records the **full expected command string + script digest at install**;
  seam init compares (the `/adapters/claude/` substring is identification, never verification).
  **`~/.claude/settings.json` itself is unguardable by kata — stated residual** (§11). (RS-M10)
- The hook's clause-pin and exec-safety registration cover BOTH edges (deny + capture). (R2-L3)
- The meta-residual (guards guarding guards — the validator's own source) is stated, not hidden.
  (TM-H4 S3, TM-H2)

**S4 — Redaction.** (TM-H4 S4, RS-M7, pass-2 high 1)
- Redaction is DETECTION, stated as such: detected secret/key/PII classes fail closed;
  undetected content is a stated residual. The scrub extends `learn_feed.redact`'s class table
  (ONE scrub, not two). The PAT lesson is the standing example.
- **The scrub compiles as TWO named points:** (1) committed run provenance at **branch close**
  (the commit act, closing the TOCTOU window — never at mint); (2) cursor/trail content at the
  **snapshot-or-push edge**. (RS-M7, pass-2 high 1)

**S5 — Consent.** (TM-H4 S5, RS-M6)
- Outward-facing acts stay human-gated: trail push opt-in only (§2.5); the hook never blocks
  non-kata work (scope marker); no auto-push anywhere.
- Target-repo provenance commits: first-run consent moment, per-target, remembered
  **machine-local in `.kata-settings.json`** (pass-2 low 9); redaction is not consent — both
  apply. (RS-M6)

**S6 — Availability.** (TM-H4 S6, RS-M11, RS-L5)
- Fail-closed must not become deny-everything: engine failure parks with a loud reason (TM-B5);
  degraded modes are per-capability, never viral; a wedged hook is detectable at seam init and
  reported. Hookless capture has its legal engine path (R2-H3).
- **The deny hook fails CLOSED in-run** — explicitly the opposite of the gauge hook's
  never-block precedent; that difference is stated in both files. Bounded runtime + payload cap:
  oversized/timeout ⇒ deny with reason, recorded. **The hook's internal timeout is pinned
  strictly below the host's** (pass-2 medium 7) — the host can never kill the hook into an
  ambiguous state. (RS-M11)
- **Scope check via run marker (RS-L5):** the deny hook reads a seam-init-written run marker
  (no live FS walk per call); marker present ⇒ kata scope ⇒ fail closed on errors; absent ⇒
  allow (non-kata sessions untouched). The transient-error window collapses to the marker read;
  the posture per edge is explicit. **Marker-loss edge (pass-2 medium 5), stated:** a deleted
  marker mid-run reads as non-kata — post-hoc detection (cursor-lineage audit at the next gate)
  is its residual channel.
- **Replay-prevention claims are host-scoped to intercepting hosts** (pass-2 medium 5-adjacent
  wording, recorded): on detection-only hosts the atomic-claim replay control has no enforcing
  edge to bind — the run's Guardian grade already says so. (Pass-2 medium: "replay-prevention
  scoped to intercepting hosts")

**Edge cases (each with named actor/pattern):** crash mid-mint ⇒ orphan record reaped at resume
(`run_start`, registry enumeration — the arm-registry anchor is TM-C7 **element 2**, per the R4
compile note) · rotation during live children ⇒ abandon-with-rendezvous (TM-C7) · same-second
ordering ⇒ seq (TM-C6) · parallel-dispatch hook races ⇒ **order-independence ACHIEVED BY the
atomic claim** (RS-H2) · fold purity ⇒ side effects only after fold completes (TM-C6) ·
**rotation is an atomic sequence** (archive rename, then header write; a torn rotation is
detected at seam init) and mid-capture loss is backstopped by the close's absent-records refusal
(RS-L1) · expiry wording: `mintedUtc` bounds MINT→LAUNCH only, defense-in-depth (RS-M12, pass-2
low 12).

---

## §9 EV-1 — the Trust Regression Suite · LOCKED

Every Guardian "Verified" badge and enforcement claim in the doc layer must cite a check id in a
**badge→check registry**; a `validate_skills` check (riding the existing gauntlet) fails an
uncited badge AND a cited-but-dead check, on every commit. The one-time promise audit becomes a
standing CI regression: **trust can only be claimed where a machine can re-derive the claim** —
facade regrowth becomes a validator failure, not a future hand-audit finding. Grounding: the
promise audit's distribution finding (honest labels live exactly where validate_skills runs);
TM-A1's Guardian vocabulary is the guardable term set; `check_reuse_claims_producers_exist` is
the working registry-vs-tree precedent. (EV-1)

Build shape: a committed registry file mapping `badge-site → check-id`; the validator check
walks both directions (registry-vs-tree: an uncited badge fails; a cited-but-dead check fails).
This suite is also where the T6–T11 facade rows graduate as wiring lands (TM-A1, TM-H3).

---

## §10 Backlog map — TM-H3 · R-L3 · TM-C7 commitment

**CLOSES when built + Verified:**
- 🔴 **BL-M33** — the seam (§1). (TM-H3)
- 🔴 **BL-M34** — the guard (TM-B5 + the hook, §1.7/§1.8). (TM-H3)
- 🔴 **BL-N01** — Truth Serum, **at v1 scope** (TM-D2); v2 = BL-N24 — stated per TM-A3's own
  uncited-claim rule. (TM-H3, R-L3)
- **BL-N19's missing mechanical route** — the persisted verdict artifact + re-loop routing
  (§1.6, §5.3). (TM-H3)
- **BL-X11 + BL-X13** — evidence identity + parsed counts (§3.4). (TM-H3)
- The T6–T11 facade rows as wiring lands (loop-routed per TM-A1). (TM-H3)

**FEEDS (binding input, does not close):**
- **BL-N16** learning graph — cursor substrate + roll-up + the learning-scope taxonomy
  assessment (§2.7 rider 1, §2.8). (TM-H3)
- **BL-N20** cadre — grounding agent roster row, phase-aware definitions, the `agentDef` record
  slot. (TM-H3)
- **BL-N08** Kitchen — tree-of-runs, close policies. (TM-H3)
- **BL-N14** statistics — projections (§2.8). (TM-H3)
- **BL-N21** always-loop — the wrapper as outermost layer. (TM-H3, TM-B1)
- **BL-N11** backlog management — the truth-status rule (§6.6). (TM-A3, TM-H3)
- **The UX freeze** — the four trust surfaces joined pre-freeze; round C1 (§6.5). (TM-G1+G3,
  R-H4)
- **BL-N24 (Truth Serum v2)** carries every deferred promotion: signal→block promotions,
  per-gate grounding-agent expansion (telemetry-informed), and any true v1 scope cut — per the
  TM-D2 standing rule. (TM-D2, TM-E1)
- 🔴 **BL-X14 / BL-X15** — the Linux vacuity-prover fix + statusline crash; §3.6's activation
  ordering depends on X14. (Mid-close evidence event)
- **Heavy cross-documentation commitment (owed):** the trust-model seams and behaviors get
  written INTO BL-N08 · N16 · N19 · N20 · N14 · N21 · the BBM ledger, so their future planning
  sessions execute with this work in mind — committed d785370; surface at handoff if any leg is
  unmet. (TM-C7 standing commitment)

---

## §11 Honest residuals — stated, EDR-5 house style

What this program does NOT claim, in the contract itself:

1. **Adversarial conductor — detection, not prevention.** A deliberately adversarial conductor
   holds the session and can fabricate files; the seam DETECTS fabrication (cursor-lineage
   mismatch at post-hoc verification). Prevention is scoped to drift, laziness, and
   prompt-obedience failure — the classes actually observed. (TM-B4, TM-H4 S1, R2-M5)
2. **The entry residual.** The seam's guarantees are scoped to runs that enter it; a session
   that never enters kata scope is untouched by design (consent law) and therefore unguarded by
   design. (TM-H2)
3. **The validator-source meta-layer.** The validator's own source (and the guards guarding
   guards generally) remains undefended and says so. (TM-H2, TM-H4 S3)
4. **The Bash leg is partial.** CLI-shape interception through Bash is best-effort, evadable by
   indirection — declared Partially verified, never "intercepting". (R-M7)
5. **Detector humility.** Burn-02 meta-finding, verbatim: *"the judgment+human layers found all
   of these; the automated mechanical gates found none."* The claim is "no unattested fact
   enters a gate," never "no defect escapes." (TM-D2, TM-E2, TM-G2)
6. **Claimed-mutation-set completeness.** The re-run proves the worker's CLAIMED mutation lines
   bite; the completeness of the claimed set stays worker-asserted. (R4 residual 2)
7. **The initiation rung is self-serviceable** pre-freeze by the conductor (it opens the phase
   it needs) — that is WHY it is graded Honor-system; cursor lineage is its detection channel,
   not a prevention. (RS-H3)
8. **`~/.claude/settings.json` is unguardable by kata** — the hook's registration site is
   outside the harness's authority; install-time digest comparison is the compensating control.
   (RS-M10)
9. **Trail tamper-evidence is evidential-until-pushed** — git-object integrity of
   `refs/kata/trail` is machine-local until the operator opts into trail push. (RS-M8, pass-2
   low 10)
10. **Redaction is detection** — undetected secret classes pass; stated at both scrub points.
    (RS-M7)
11. **Marker-loss edge** — a deleted run marker mid-run reads as non-kata to the hook; post-hoc
    lineage audit is the detection channel. (Pass-2 medium 5)
12. **Prose-era artifacts of this very program** (this DESIGN's own dispatch included) are
    Honor-system until the seam exists — recorded in the frontmatter, per the brief. (R-H1 mint
    note)

---

## §12 Deferred to the frozen PLAN (explicitly — not invented here)

Per the ledger's own delegations, the following are the plan-author's to fix, not this
document's:

- **Wave composition and ordering details** of the build (which launch-site groups migrate in
  which wave; which gate preconditions wire in which wave) — the dependency order and hook-LAST
  law of §7 are the only design-level constraints. (TM-D4, TM-H1)
- Per-wave task partitioning, ownership, and the per-task `evidence:` declarations for the
  build itself. (TM-F1 applied reflexively)
- The per-judge tripwire corpus build schedule (wave-bound per R-M6).
- The per-judge VERDICT enum table contents (enumerated at the contract-rewrite wave — R4
  residual 4).
- BL-X14/BL-X15 fix scheduling relative to the mutation-precondition activation (§3.6).

**Freeze path (recorded, binding):** this DESIGN is `status: draft` — the conductor gates it
(authored-artifact six-row rubric + the two-direction diff against every LOCKED branch), the
plan-author compiles the PLAN, the operator freezes per D169, and the full documented
handoff+orientation package lands BEFORE any execution dispatch (§7 operator mandate). The
freeze act is separate from this compile.
