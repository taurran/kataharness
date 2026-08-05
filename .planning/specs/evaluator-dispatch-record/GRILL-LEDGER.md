---
spec: evaluator-dispatch-record
status: draft
opened: 2026-08-04
baseline: master `f4096e6` · gauntlet 4/4 PASS · working tree clean
tier: kata-grill-standard
---

# GRILL LEDGER — the gate never checks that its judge was independent

**In plain terms:** the rule is that finished work is judged by a fresh reviewer that cannot edit
files. We genuinely enforce the "cannot edit" half. We never check the "fresh" half — it is assumed
from how the reviewer is launched, and nothing anywhere records whether it actually was.

## Phase 0 — grounding (read, not measured)

### The gap, exactly — and it is sharper than the backlog description

`skills/evaluate/kata-evaluate/SKILL.md:27`:

> Run from a **fresh context**, as a separate subagent with **no Write/Edit** (enforced structurally by
> the frontmatter above — [[STANDARDS]] §1 / [[LESSONS-LEARNED]] L4).

**Two claims sit in one sentence and only one is true.** `no Write/Edit` *is* structurally enforced by
the skill frontmatter. `fresh context` has nothing behind it — no check, no record, no artifact. The
parenthetical *"(enforced structurally…)"* reads as though it covers both. A reader cannot tell the
machinery from the wish, which is the same failure mode as `KH-T02` (Prime Directives whose guard was
a substring count) and `STANDARDS §3` (a bump rule that said "validator-enforced" and was not).

### Measured facts (verified at `f4096e6`)

| fact | value | how |
|---|---|---|
| evaluator is host-only | `HOST_ONLY_ROLES = frozenset({"orchestrator", "evaluator"})` | `tools/kata_roles.py:46` |
| no-write enforcement | skill frontmatter (`no-write` in the skill's declared tools) | `kata-evaluate/SKILL.md:22,27` |
| freshness enforcement | **none found** | no `evaluator`-dispatch record in `tools/*.py`; `run_result.py` carries `gateName`/`command`/`exitCode`, no dispatch provenance |
| existing durable-artifact precedent | `contract-gate.json` | `tools/contract_gate.py:498-513` |

### Prior art, read before designing (this repo's recorded blind spot is assuming a primitive fits)

- **`contract_gate.write_contract_gate`** (`:498-505`) emits `<kata_dir>/contract-gate.json`, described
  as *"the durable artifact the evaluator's independence leg reads (F4; **its ABSENCE is the
  evaluator's signal that the gate was skipped**)"*. **This is the pattern to reuse:** a producer-stamped
  JSON artifact whose absence is meaningful. It proves the *contract gate* ran; it says nothing about
  the evaluator's own freshness, so it does **not** already close this gap — checked, not assumed.
- **`T-04`** established the governing principle: gate evidence is credited by **identity**, not by
  plausibility. An ancestry check returned TRUE for a `RESULT.json` 56 commits stale. The same logic
  applies here — a verdict must be tied to *this* dispatch, not merely look like a verdict.
- **`D81`** — tier-3 `.kata/` is **disposable**, rebuilt from the git-committed trail.
- **`D135`** — the board is the trail; **no second append-only journal.** A per-run JSON artifact is
  not a journal (`contract-gate.json` is the existing proof of that distinction), but any design that
  proposed an accumulating log of evaluator dispatches would violate this outright.
- **`D136`** — absent/unparseable decision input must hard-fail, never fall through permissively.

## The decision tree

| # | branch | status |
|---|---|---|
| **B1** | Prove freshness, record the dispatch, or just fix the sentence | **RESOLVED — EDR-1** |
| B2 | What ties a verdict to its dispatch record | RESOLVED — EDR-2 |
| B3 | Where the record lives, given `.kata/` is disposable (D81) | RESOLVED — EDR-3 |
| B4 | Behavior when the record is absent | RESOLVED — EDR-4 |
| B5 | The honest residual — what this does NOT prove, stated in the contract | RESOLVED — EDR-5 |
| B6 | Does `kata-evaluate:27`'s sentence change regardless | RESOLVED — EDR-6 |

## Resolved branches

### EDR-1 — The dispatcher is the witness; the judge never certifies itself · LOCKED

- **Decision:** the **conductor** writes a dispatch record when it dispatches the evaluator. The
  evaluator does **not** self-declare its own freshness.
- **Rejected — evaluator self-declaration** (the original `T-05` framing, "verdict dispatch
  self-declaration"): a stale evaluator asked *"were you fresh?"* answers **yes** exactly as
  convincingly as a fresh one. Asking the thing under check to certify itself is precisely how the
  Prime Directives guard was fooled (`KH-T02`). Rejecting the backlog item's own proposed mechanism is
  deliberate and recorded.
- **Rejected — reword the sentence and build nothing:** legitimate and honest, but it leaves a real
  gap in the project's *only* structural defence against a self-approving gate.
- **Provenance:** operator ruling 2026-08-04.

### EDR-2 — A run-scoped token, issued at dispatch, echoed in the verdict · LOCKED

- **Decision:** the dispatch record carries a **run-scoped token** plus the **target SHA**. The token
  travels in the evaluator's brief. A verdict is creditable only if it cites the token AND the record's
  target SHA matches the SHA actually being graded.
- **What this genuinely proves:** the verdict came from an agent that **received this dispatch brief**
  — not from a recycled verdict, a hand-written one, or a re-used earlier run's output.
- **What it does NOT prove:** that the agent's context was empty. See EDR-5. The token is a
  *provenance* binding, not a freshness proof, and must never be described as the latter.
- **Rejected — match on target SHA + a timestamp window only:** no brief change needed, but any agent
  could produce a matching verdict without ever having been dispatched; it re-admits exactly the
  plausibility-over-identity failure `T-04` closed.

### EDR-3 — The record lives in `.kata/`, and its disposability is correct · LOCKED

- **Decision:** `<kata_dir>/evaluator-dispatch.json`, alongside `contract-gate.json`, same producer
  pattern. **Not** git-committed, **not** an accumulating log — one record per dispatch, overwritten.
- **On `D81`:** `.kata/` is disposable and this record is deliberately disposable with it. That is the
  right semantics, not a weakness: the gate and the dispatch belong to the **same run**, so a wiped
  `.kata/` means there is no current verdict to credit and the gate is simply re-run. Stated so nobody
  later "fixes" it by making the record durable — that would drift toward the second journal `D135`
  forbids.

### EDR-4 — Absent or unreadable record ⇒ the verdict is NOT creditable · LOCKED

- **Decision:** no record, unparseable record, token mismatch, or SHA mismatch ⇒ the verdict cannot be
  credited as a PASS. This is `D136` fail-closed and the existing default-FAIL posture; it is **not** a
  new severity or a warning.
- **Deliberately mirrors** `contract_gate.py:500` — *"its ABSENCE is the evaluator's signal that the
  gate was skipped."* Same idiom, so the codebase has one meaning for a missing gate artifact.

### EDR-5 — The residual is stated in the contract, never designed away · LOCKED

- **Decision:** the contract must say plainly that this records **how the evaluator was dispatched**
  and does **not** prove its context was empty; an operator who dispatches the evaluator inside a dirty
  context defeats it, and no in-band mechanism can detect that.
- **Precedent:** `protocol/orchestration.md` already carries a pinned clause admitting its own
  property *"is NOT mechanically provable."* An honest, pinned limitation is the house style; a claim
  that over-reads its mechanism is the thing this whole spec exists to remove. **Shipping a freshness
  guarantee we cannot deliver would recreate the defect one level up.**

### EDR-6 — `kata-evaluate:27` is rewritten regardless of what is built · LOCKED

- **Decision:** the sentence is split so the two claims stop sharing one parenthetical — no-write is
  structurally enforced by frontmatter; freshness is a dispatch property, recorded and bound by the
  dispatch record, not proven.
- **Rationale:** the sentence is the defect. Even a perfect implementation leaves a reader unable to
  tell which half is machinery unless the prose separates them.

## Convergence pass 1 — HOLD, and it killed the design. Correctly.

A fresh-context no-write reviewer returned **HOLD** with 10 findings. The three decisive ones were
re-verified by the conductor and **all three were true**. `EDR-1`…`EDR-6` are **SUPERSEDED** by
`EDR-7` below — they are kept as the record of a design that was wrong, not as a contract.

### ⚠️ The design was forgeable — it re-created the exact failure it cited

`EDR-2` put a token in `.kata/evaluator-dispatch.json` for the evaluator to echo back. But
`kata-evaluate/SKILL.md:14` grants `allowed-tools: [Read, Grep, Glob, Bash]`, and
`kata-orchestrate/SKILL.md:1429` says *"Point it at `.kata/` so it reads the emitted artifacts
directly."* **A stale evaluator could `cat` the token and echo it.** Verified both lines directly.
That is not a weaker guarantee — it is **no guarantee wearing the costume of one**, which is strictly
worse than the honest gap, and it is the `KH-T02` self-certification shape the ledger opened by citing.

### ⚠️ There is no code seam to hold enforcement — conductor→evaluator is prose end-to-end

`build_brief` has **no non-test caller**: verified, every reference is either its own definition in
`kata_dispatch.py` or prose inside a `SKILL.md`. `_COMMAND_BUILDERS` covers `codex` and `kiro` only —
the evaluator is `HOST_ONLY` (`kata_roles.py:46`), i.e. the in-process host Agent path, which
`kata_dispatch` explicitly does not handle. So whatever comparison this spec specified, **the
comparator would also be prose** — a rule with nothing enforcing it, which is the disease being treated.

### ⚠️ The reused pattern was never wired — the conductor's third instance of this blind spot

`EDR-3` claimed `contract-gate.json` as proven prior art. Verified: **only the writer exists in
Python** (`contract_gate.py:499,511`); **no Python reads it.** Its consumer is prose, and
`.planning/D2-VERIFICATION-RESULTS.md` records that zero `contract-gate.json` files have ever been
written in a real run. **A pattern with a producer and no consumer is not a proven pattern.** This is
the same *assume-a-primitive-fits* error made twice earlier the same day (`_run_git` for file content;
git's `-M` for rename detection). Recorded, not smoothed over.

### EDR-7 — Fix the false sentence now; file the seam as its own item · LOCKED (SUPERSEDES EDR-1…EDR-6)

- **Decision:** build **no** dispatch record. Rewrite the sentence in **both** judge skills so the
  claim stops over-reading its mechanism, and file the missing code seam separately.
- **What shipped:** `kata-evaluate/SKILL.md` (0.3.1 → **0.3.2**) and `kata-inline-eval/SKILL.md`
  (0.1.0 → **0.1.1**) now state the two halves separately — `no Write/Edit` is **enforced
  structurally** by `allowed-tools`; `fresh context` is a **dispatch convention, NOT verified and NOT
  recorded**. `kata-inline-eval` additionally notes that it holds **kill authority** over a running
  task while economy-tiered, so its unverified freshness carries more weight, not less.
- **Why the second file:** the reviewer found the identical sentence at `kata-inline-eval:26`. Fixing
  only `kata-evaluate` would have left the same lie in a skill that can terminate work.
- **Why not build the hash version:** storing `sha256(nonce)` genuinely closes the forgery hole, but
  the comparison step is still prose. It would buy better hygiene while still *reading* as enforcement
  — and the whole point of this item is that a reader cannot currently tell machinery from convention.
- **Filed, not built:** `BL-M33` — a real dispatch seam for host-only roles. Until it exists, evaluator
  freshness is not mechanically checkable by anything, and both skills now say so.
- **Version bump note (dogfooding):** these edits required version bumps because `check_bump_on_modify`
  shipped hours earlier the same day. The rule caught its own authors, as intended.

## Status — CLOSED as "sentence fixed, gap filed"

This ledger is **not** a build contract. `EDR-1`…`EDR-6` are superseded and must not be compiled into
a DESIGN. The item's honest outcome is recorded in `EDR-7`.

## Blocked at close — do not forget

Grill-close `learn_feed.py` emit stays **BLOCKED** by `DEF-2` (it silently drops entry bodies for this
ledger style). Same posture as the two grills before it.
