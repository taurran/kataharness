---
name: kata-defer
description: >-
  Capture, don't drift. During a run, append out-of-scope-but-worth-keeping items to DEFERRED.md and any spec
  assumption made without a human grill to ASSUMPTIONS.md, instead of silently dropping them or scope-creeping
  the frozen plan. Both surface at the gate/handoff. Use as the grill-skip autonomous-floor safety net (D71) and
  as the in-loop deferral valve (D42). Invoke when a worker/orchestrator hits something off-plan but real.
license: Apache-2.0
version: 0.2.0
category: handoff
status: beta
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: >-
  new (KataHarness original, D42/D43 GB9) — the structural complement to the no-drift spine; assumption-log role
  added by D71 (Priming-and-Grill autonomous floor)
tags:
  - kata/handoff
  - kata/module/defer
  - defer
  - assumption-log
  - no-drift
---
# kata-defer — capture off-plan reality at the boundary, never drift

The **pressure-release valve** that makes one-shot = no-churn sustainable. The frozen plan does not drift
(spine #1/#2); but real, off-plan things surface mid-run — a worth-keeping idea, or an assumption the loop had
to make because no human grilled it. `kata-defer` gives both a durable home so they are **parked, not lost, and
not scope-crept into the frozen plan.** Optional module (`kata/module/defer`, D43) — additive, not spine.

## The schema you write to — `protocol/deferral.md` is canonical

**`protocol/deferral.md` is the contract; this skill is the writer that must satisfy it.** Where anything
below and that file disagree, that file wins — it is a registered `REQUIRED_PROTOCOL` contract with pinned
clauses and a fingerprint, so it cannot be quietly weakened, and detectors parse the grammar it fixes
**mechanically: a parse failure is a REFUSAL, never a skip.** An entry you write in the wrong shape is not a
soft note that gets read charitably — it is an entry that fails to parse and refuses the gate.

**Canonical paths (not "somewhere in the run's docs"):** `.planning/DEFERRED.md` and
`.planning/ASSUMPTIONS.md`.

## Two artifacts, two roles (both run-scoped, both surfaced at gate/handoff)

### 1. `.planning/DEFERRED.md` — out-of-scope parking (D42)
During a run, any out-of-scope-but-worth-keeping item (nice-to-have, post-processing candidate,
deferred-for-a-reason discovery a worker hit in-lane) is **appended** here rather than dropped or crept into the
frozen plan. This is the home the [[kata-orchestrate]] escalate predicate points workers to: *"record
out-of-scope discoveries as a deferral note and keep going."*

### 2. `.planning/ASSUMPTIONS.md` — the autonomous-floor safety net (D71)
The autonomous-reliability floor is on for **every** run, but it does the most work on a **grill-skip rung**
(`tiers["kata-grill"] == "skip"` — no grill ran, the priming prompt frozen as-is) or a low-grill run, where
ambiguity is resolved **in-loop without a human**. Every spec assumption the loop has to make to proceed is
**logged here with its provenance** (which prompt gap forced it, what was assumed, what the alternatives were). This is how the autonomous floor stays honest: misalignment with the designer's intent is
**caught at the boundary** (gate/handoff) without an up-front grill. It is the in-loop, without-human end of the
**grill ↔ RS ambiguity-resolution spectrum** (D71): the up-front-with-human grill and the in-loop RS research
subagent shore up alignment from the other ends; the assumption log makes whatever the loop *assumed* visible
for human review. (RS itself lands in the loop-cognition phase; the assumption log is the floor's available-now
backstop.)

## Entry grammar — the shape a detector can parse

An entry is an **H2 heading** plus the field lines that follow it, up to the next H2. The heading is literal:
an em dash `—` between id and title, a middle dot `·` before the STATUS, an ISO date in parens.

```
## DEF-<n> — <title> · <STATUS> (<YYYY-MM-DD>)
```

- `<n>` is a positive integer, unique per ledger, **never reused after closure**.
- `<STATUS>` is one of `OPEN | ACCEPTED | CLOSED` — no other value parses.
- The date is the date the entry reached its **current** status.
- Bolding and reflow are free (`· **CLOSED (2026-08-04)**` is the same entry); the id, status, and date are
  not. Underscores are NOT stripped — the field names are snake_case on purpose.
- **Only H2 is an entry.** `###`+ headings inside an entry are its body — a closure record nested under an
  entry is part of that entry, never a second one.

### `DEFERRED.md` — the entry template you emit

```md
## DEF-<n> — <short title> · OPEN (<YYYY-MM-DD>)
- **What:** the concrete thing not done — file, symbol, behavior, with a `file:line` where one exists.
- **Why:** why it was deferred rather than built. A reason a reader can disagree with, never "out of scope".
- **Provenance:** where it came from — the run/task that filed it, the ledger entry that ruled on it, the
  discovery that surfaced it.
- **Owed-to:** the named run, wave, or backlog item that will discharge it. `unassigned` is legal and
  honest; a wrong owner is not.
```

All four fields are **required** on every deferral, in the field block (the list items between the H2 and
the first sub-heading). Extra labelled fields — `Measured`, `Evidence`, `Interim posture` — are welcome and
are usually what makes an entry worth reading; a parser checks the required set and never rejects an entry
for saying more.

### `ASSUMPTIONS.md` — the entry template you emit

```md
## ASM-<n> — <short title> · OPEN (<YYYY-MM-DD>)
- **Assumption:** what the loop assumed, stated so a human can agree or contradict it.
- **Provenance:** which prompt gap, missing decision, or unavailable human forced it, and where (run/task id).
- **Grilled:** no — <why the assumption exists at all>   # or: yes — <the ruling it cites>
```

Same heading grammar, id `ASM-<n>`; these three are the required set. `Grilled: yes` **MUST** cite where it
was ruled on — an uncited "yes" is the claim the field exists to prevent.

## STATUS — and what each value costs you

| STATUS | Means | Requires |
|---|---|---|
| `OPEN` | Filed, unapproved, undischarged. **The default on capture — what you write.** | The required fields. |
| `ACCEPTED` | The operator approved **the park itself** — the item is legitimately parked. | `accepted_by` + `accepted_at`. |
| `CLOSED` | The owed work is built and merged. | `closing_commit`. |

`ACCEPTED` approves the park, never the work. It is **not** a step toward `CLOSED` and is not required
before it — `OPEN → CLOSED` is a normal life.

### The approval record — the only thing a gate may credit

```md
- **accepted_by:** <who>
- **accepted_at:** <ISO-utc>
```

**A gate may credit an operator approval ONLY from these two fields.** Not from a commit message, not from a
chat transcript, not from your report that the operator agreed, not from the entry's prose. An entry whose
prose claims approval while the fields are absent is **unapproved** to every gate — and the mismatch between
the two is itself a finding. `accepted_by` names a **human**: an agent approving its own deferral is the
self-certification D33 forbids, and you never write your own name there.

### Closure discipline — captured is not closed

```md
- **closing_commit:** <sha> (<subject>)
```

- The sha must resolve in this repo and its content must be the work the entry described. Deciding what to
  do, or planning to do it, closes nothing.
- **Wired, not merely captured** (PD-1): the closed work is reachable and exercised, not present-but-dead,
  and the closure record states its evidence — the gate numbers, the test, the measurement — in the same
  breath as the claim (PD-2).
- A closure record **preserves the original entry** rather than replacing it; nest it under a `###`
  sub-heading. What was filed, and what it cost when it was finally picked up, is the record's value.
- An entry whose `Owed-to` run completes **without** discharging it is not closed by that completion. It is
  re-assigned in writing, with the reason — an `OPEN` entry pointing at a finished run is a silent deferral
  wearing a deferral's clothes.

## The same-line `DEF-*` rule for debt markers

**A debt marker (TBD/FIXME/XXX) in gated work without a `DEF-*` reference on the same line is a BLOCKER.**
The reference goes on the marker's own line — a marker whose follow-up lives in a nearby paragraph is one
refactor away from being an orphan. So when you park something that leaves a marker behind, file the entry
FIRST and put its id in the marker:

```python
# FIXME(DEF-7): partition cache invalidation — parked, see .planning/DEFERRED.md
```

"Gated work" is the task-modified file set the gate is grading — not the whole repo, and not the ledger
itself, whose entries name debt markers as their subject matter.

## Append discipline
- **Append-only, checkpoint-as-you-go.** Write each entry the moment it arises (like the grill decision ledger)
  so an interrupted run loses nothing.
- **Append-only is about meaning, not bytes.** An existing entry is never rewritten to say something else; it
  is amended by adding to it — a status change, a closure record — with the original text left standing.
  Fixing a typo is not a rewrite; changing what an entry claims happened is.
- **Never edit the frozen plan from here.** Capturing an item is the *alternative* to drifting — if acting on it
  would require touching the frozen plan or an unowned file, it is escalate-or-defer, never silent edit.
- **A ledger with zero entries is a valid zero and reads as zero. A ledger that cannot be parsed is NOT a
  zero** — never write a shape that risks being read as "no deferrals found" when the truth is "unreadable".
- Both files are run-scoped artifacts (Obsidian-readable, git-committed with the run).

## Honest residual — what enforces this today (PD-2)

`protocol/deferral.md` states it plainly: at the time that contract landed, **no mechanical detector consumes
it yet**. The silent-deferral join and the debt-marker scan are later deliverables; until they run, conformance
to this schema is **Honor-system** — authored by agents, checked by human review and by the ledgers' own shape.
What IS mechanical is the contract's own tamper-evidence (clause pins + fingerprint in
`tools/validate_skills.py`). Write conformant entries anyway: the detectors land on this exact grammar, and an
entry written loosely today is an entry that refuses a gate tomorrow.

## Surfacing (the whole point)
- **At the gate:** [[kata-evaluate]] grades `.planning/ASSUMPTIONS.md` (its rubric item 8) before PASS — an
  assumption that contradicts the priming prompt / frozen spec is **NEEDS_WORK**, not a footnote (especially on
  a skip run). The orchestrate Final gate points the evaluator at it. *(This is wired, not asserted — the gate
  actually reads it.)* The gate credits an operator approval **only** from `accepted_by` / `accepted_at`, so an
  entry that needs to survive the gate as approved needs those fields, not a persuasive `Why`.
- **At handoff:** [[kata-handoff]] compiles both files into the handoff so the human/next session sees every
  parked item and every autonomous assumption. They feed the project backlog and [[kata-improve]].
