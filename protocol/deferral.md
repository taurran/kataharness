# protocol/deferral.md — the sanctioned-deferral ledger contract

A cross-skill contract fixing **where a deferral lives, what shape it has, how an operator approval is
recorded, and what closure means**. This is the canonical source of truth; responsible skills and the
conductor reference it by path (`protocol/deferral.md`), never by `[[wikilink]]`. Companion to
`protocol/prime-directives.md` (PD-1 names deferral as a sanctioned path) and to `skills/handoff/kata-defer`
(the skill that appends entries) — this file is the **schema those entries must satisfy**.

## Purpose

PD-1 permits exactly three ways around designed work, and one of them is deferral: *"parked items land in
`DEFERRED.md`, graded at the gate, surfaced at handoff — a deferral exists only if the operator can see
it."* Until this contract, "the operator can see it" rested on prose alone. Nothing pinned the ledger's
path, nothing fixed an entry's shape, nothing said where an operator's approval is written so a gate can
check it rather than take an agent's word for it, and nothing distinguished **captured** from **closed** —
so an entry could be filed, never built, and read as discharged. A gate cannot grade a ledger it cannot
parse, and an approval a gate cannot locate is an approval it must not credit.

## The contract (TM-D1 — verbatim contract text)

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

Everything below states that contract precisely enough to implement and to parse. It adds no permission the
paragraph above withholds.

## Canonical paths

| Ledger | Path | Holds |
|---|---|---|
| Deferral ledger | `.planning/DEFERRED.md` | Designed or discovered work deliberately **not** done now — the PD-1 sanctioned park. |
| Assumption ledger | `.planning/ASSUMPTIONS.md` | Every spec assumption the loop had to make **without a human grill** (D71 autonomous floor). |

Both are **append-only, checkpoint-as-you-go**: an entry is written the moment it arises, so an interrupted
run loses nothing. Append-only is a discipline about meaning, not bytes — an existing entry is never
rewritten to say something else; it is amended by adding to it (a status change, a closure record) with the
original text left standing as the record. Correcting a typo is not a rewrite; changing what an entry
claims happened is.

A ledger that is **absent** is a legal zero only where the consuming gate says so (`kata-evaluate` treats a
missing `ASSUMPTIONS.md` as N/A). A ledger that is **present but unparseable** is never a zero — see
*Parsing is mechanical*, below.

## Entry grammar

An entry is an **H2 heading** plus the field lines that follow it, up to the next H2 or end of file:

```
## DEF-<n> — <title> · <STATUS> (<ISO-date>)
```

Canonical heading pattern (applied to the heading line after normalisation):

```
^##\s+(?P<id>(?:DEF|ASM)-\d+)\s+—\s+(?P<title>.+?)\s+·\s+(?P<status>OPEN|ACCEPTED|CLOSED)\s+\((?P<date>\d{4}-\d{2}-\d{2})\)\s*$
```

- `<n>` is a positive integer, unique per ledger, never reused after closure.
- The separators are literal: an em dash `—` between id and title, a middle dot `·` before the status.
- `<ISO-date>` is `YYYY-MM-DD` — the date the entry reached its **current** status.
- **Normalisation before matching:** line endings, whitespace runs, and the markdown emphasis markers
  `*` and `` ` `` carry no meaning here and are flattened first. So `· **CLOSED (2026-08-04)**` and
  `· CLOSED (2026-08-04)` are the same entry. Reflow and bolding are free; the id, status, and date are
  not.
- **The underscore is NOT stripped**, and that is the one deliberate difference from
  `_normalize_protocol_text` (`tools/validate_skills.py:713`), which does strip `_` as an emphasis marker
  for protocol prose. This grammar's field names are snake_case — `accepted_by`, `accepted_at`,
  `closing_commit` — so stripping `_` would mangle exactly the fields a gate must read, and identifiers
  like `kata_preflight` in an entry title would silently lose a character. A ledger parser that reuses the
  protocol normaliser unchanged is wrong; this is stated here because the mistake is a quiet one.
- **Only H2 is an entry.** Deeper headings (`###`+) inside an entry are its body — a closure record or a
  preserved original filing nested under an entry is part of that entry, never a second one.

### The field block

An entry's required fields are read from its **field block**: the list items between the H2 heading and the
first sub-heading (or the next H2, whichever comes first). A field line is a list item whose leading label,
after normalisation, is the field name followed by a colon — `- **What:** …`. Content under a sub-heading
is preserved record — a closure record, an original filing, an audit trail — and is **never** read as a
second set of fields, which is what lets an entry keep its history verbatim without confusing a parser.

Additional labelled fields beyond the required set are **allowed** — `Measured`, `Evidence`, `Interim
posture` and their kin carry real weight and are what makes an entry worth reading. A parser checks that
the required fields are present; it never rejects an entry for saying more.

### `DEFERRED.md` — required fields

Each entry carries these four in its field block:

| Field | Required | Holds |
|---|---|---|
| `What` | always | The concrete thing not done — file, symbol, behavior, with a `file:line` where one exists. |
| `Why` | always | Why it was deferred rather than built. A reason a reader can disagree with, not "out of scope". |
| `Provenance` | always | Where the decision came from: the run/task that filed it, the grill or ledger entry that ruled on it, the discovery that surfaced it. |
| `Owed-to` | always | The named run, wave, or backlog item that will discharge it. `unassigned` is a legal value and an honest one; a wrong owner is not. |
| `accepted_by` / `accepted_at` | when operator-approved | See *The approval record*. |
| `closing_commit` | when `CLOSED` | See *Closure discipline*. |

### `ASSUMPTIONS.md` — required fields

Same heading grammar with the id `ASM-<n>`; the fields differ because the artifact does:

| Field | Required | Holds |
|---|---|---|
| `Assumption` | always | What the loop assumed, stated so a human can agree or contradict it. |
| `Provenance` | always | Which prompt gap, missing decision, or unavailable human forced it, and where (run/task id). |
| `Grilled` | always | `no` (the default, and why the assumption exists at all) or `yes — <where it was ruled on>`. An assumption recorded as grilled MUST cite the ruling. |
| `accepted_by` / `accepted_at` | when operator-approved | Same fields, same rule, as a deferral. |

## STATUS enum

`OPEN | ACCEPTED | CLOSED` — no other value is valid, and a heading carrying anything else does not parse.

| STATUS | Means | Requires |
|---|---|---|
| `OPEN` | Filed, unapproved, undischarged. The default on capture. | The four (or three) required fields. |
| `ACCEPTED` | The operator has approved the deferral itself — the item is legitimately parked. | `accepted_by` + `accepted_at`. |
| `CLOSED` | The owed work is built and merged. | `closing_commit`. |

`ACCEPTED` is approval of the **park**, never of the work; it is not a step on the way to `CLOSED` and is
not required before it. An item may go `OPEN → CLOSED` without ever being `ACCEPTED`.

## The approval record

An operator-approved deferral MUST carry, as field lines on the entry:

```
- **accepted_by:** <who>
- **accepted_at:** <ISO-utc>
```

**A gate may credit an approval ONLY from these fields.** Not from a commit message, not from a chat
transcript, not from an agent's report that the operator agreed, not from the entry's prose. This is the
whole point of the field existing: PD-1's "express operator permission" and PD-2's "or explicitly approved
by the operator" become checkable instead of assertable. An entry whose prose claims operator approval
while the fields are absent is **unapproved** as far as every gate is concerned, and the mismatch between
the two is itself a finding.

`accepted_by` names a human, not an agent. An agent approving its own deferral is the self-certification
D33 forbids.

## Closure discipline

**Closure requires the closing commit reference — captured is not closed.** An entry moves to `CLOSED`
only when the owed work is built, merged, and cited:

```
- **closing_commit:** <sha> (<subject>)
```

- The sha must resolve in this repository, and its content must be the work the entry described. A run that
  *decides* what to do, or *plans* to do it, has not closed anything.
- **Wired, not merely captured** (PD-1): the closed work is reachable and exercised, not present-but-dead.
  A closure record states the evidence — the gate numbers, the test, the measurement — in the same breath
  as the claim (PD-2's done-requires-proof bar).
- A closure record **preserves the original entry** rather than replacing it. What was filed, and what it
  cost when it was finally picked up, is the record's value.
- An entry whose named owner (`Owed-to`) completes without discharging it is **not** closed by that
  completion. It is re-assigned, in writing, with the re-assignment's reason — leaving an `OPEN` entry
  pointing at a finished run is a silent deferral wearing a deferral's clothes.

## Debt markers — the same-line `DEF-*` rule

**A debt marker (TBD/FIXME/XXX) in gated work without a `DEF-*` reference on the same line is a BLOCKER.**
The reference must be on the marker's own line, because a marker whose follow-up lives in a nearby
paragraph is one refactor away from being an orphan. A `DEF-*` id in the marker line is a promise the
ledger can be checked against; anything else is a note to nobody.

"Gated work" is the task-modified file set the gate is grading — not the whole repository, and not this
ledger, whose entries name debt markers as their subject matter.

## Parsing is mechanical — a parse failure is a refusal

**Detectors parse this grammar mechanically; a parse failure is a refusal, never a skip.** A malformed
heading, a missing required field, a `CLOSED` entry with no `closing_commit`, an unreadable ledger: each is
a REFUSAL to certify, reported as such. The forbidden outcome is the silent one — a parser that shrugs at
what it cannot read and returns "no deferrals found" produces the exact false clean bill of health the
ledger exists to prevent.

This is the anti-vacuity companion law (TM-D3) applied to the ledger: a check that ran over nothing must
report that it ran over nothing. A ledger with **zero entries** is a valid zero and is reported as zero; a
ledger that could not be read is **not** a zero and must never be rendered as one.

## Honest residual — what is and is not wired today (PD-2)

At the moment this contract lands, **no mechanical detector consumes it yet.** The three-way silent-deferral
join (B2) and the debt-marker scan (B3) are specified in the trust-model DESIGN §3.1 and are built later in
that program (`tools/truth_serum.py`, the blocking-detectors task); until they run, conformance to this
schema is **Honor-system** — authored by agents, checked by human review and by the ledgers' own shape, not
by a gate. That is stated here rather than implied away, because a contract that reads as enforced while
nothing enforces it is precisely the documentation-only seam `protocol/reuse-claims.md` exists to stop.

What IS mechanical today: this file is a registered `REQUIRED_PROTOCOL` contract with pinned clauses and a
fingerprint (`tools/validate_skills.py`), so the rules above cannot be quietly weakened or deleted — the
guarantee is tamper-evidence of the contract, not yet enforcement of the ledgers.

## Producer / consumer sites

| Site | Skill / artifact | Role |
|---|---|---|
| **Capture** | `kata-defer` | Appends entries to both ledgers; this file is the schema its writes must satisfy. |
| **Worker escalation** | `kata-orchestrate` (escalate predicate) | Points a worker at the deferral path for an out-of-scope discovery instead of a silent drop or a scope-crept plan. |
| **Gate** | `kata-evaluate` | Grades the ledgers before PASS — the assumption log (rubric item 8) and, once B2 lands, the plan ⋈ tree ⋈ `DEFERRED.md` join. Credits an operator approval only from `accepted_by` / `accepted_at`. |
| **Handoff / closeout** | `kata-handoff`, `kata-report`, `kata-closeout` | Surface every parked item and every autonomous assumption at the boundary — the "operator can see it" half of PD-1. |
| **Detectors** | `tools/truth_serum.py` (trust-model program, DESIGN §3.1 B2/B3) | Parses this grammar; refuses on a parse failure. |

`kata-grill` is explicitly **not** a site — it resolves questions with the human, which is the alternative
to assuming; an assumption it rules on is recorded in its own decision ledger, and the `ASM-<n>` entry
citing that ruling is written by whoever made the assumption, not by the grill.
