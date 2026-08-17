# DECISION-LEDGER format — the grill's output

The running record [[kata-grill]] appends to as each decision branch resolves. It is the raw material the
FREEZE phase ([[kata-design-doc]], [[kata-plan]]) compiles into the frozen contract. Keep it durable
(Obsidian-native frontmatter + wikilinks); one entry per resolved branch.

## Document frontmatter — REQUIRED, written when the ledger is CREATED

Every ledger opens with a YAML frontmatter block. **Write it at creation, not at close** — a ledger born
without one is a ledger nothing can govern, and the `status:` key is not a decoration: it is the machine
predicate of the `ledger` governor rung (`kata_dispatch.ledger_status`), so an absent key reads `absent`,
satisfies nothing, and silently denies every dispatch minted against this grill.

```yaml
---
spec: <the spec slug this grill serves — matches its .planning/specs/<slug>/ directory>
item: "<one line: what this grill is resolving>"          # optional but strongly recommended
status: draft                                             # draft | converged | frozen | absorbed
opened: <YYYY-MM-DD> (<what it supersedes or absorbs, if anything>)
tier: <the kata-grill tier this ran at>                   # optional
---
```

**The `status:` enum is CLOSED — four values, and no fifth:**

| Value | Means | Who writes it |
|---|---|---|
| `draft` | The grill is open. **The value at creation, always.** | Whoever creates the ledger. |
| `converged` | The final convergence pass SHIPped. | **ONLY the grill-close act** — see the tier skill's grill-close status write. |
| `frozen` | The ledger's decisions were compiled into a frozen DESIGN/PLAN. Satisfies anything `converged` satisfies. | The freeze act. |
| `absorbed` | This ledger was superseded by another, which now carries its branches. **Satisfies nothing** — it ROUTES a mint to the absorbing ledger. | The absorbing grill; name the absorber in the value's trailing prose. |

- **Parsed first-word-only, case-folded.** Trailing prose after the first word is legal and normal —
  `status: converged — 2026-08-16, pass 1 SHIP · pass 2 SHIP` reads as `converged`. Put the audit trail
  there; do not put a second status word first.
- **Fail-closed, never coerced.** An unrecognized first word RAISES rather than defaulting in either
  direction, and an empty value reads `absent`. There is no "roughly converged".
- Additional keys (`item`, `baseline`, `tier`, `target`, `converged:` with its date/detail) are free — a
  parser checks the ones it needs and never rejects a ledger for saying more.

## Per-entry shape

```md
### D{n} — {short branch title}  ·  {LOCKED | open}
- **Question:** the exact branch/ambiguity the spec left open.
- **Provenance:** what raised it (spec §, code path, doc, contradiction found).
- **Options considered:** A (chosen) · B · C — one line of trade-off each.
- **Decision:** the chosen option, stated specifically enough to execute.
- **Rationale:** why this over the alternatives (the real trade-off).
- **Edges/scenarios:** the concrete cases probed + the defined behavior for each.
- **Doc-baked:** glossary terms added ([[CONTEXT]]); ADR ref if one was warranted; backward-compat note.
```

## ELEVATE entries (D153)

The grill-close ELEVATE outcome uses a dedicated anchor family, same file, same grammar:

```md
### EV-{n} — Elevate: {short title}  ·  LOCKED
- **Recommendation:** the one grounded elevation posed (with its grounding: the resolved branches /
  goal terms / probed scenarios that motivate it).
- **Decision:** Accepted (the recommendation) · "Declined — <reason>" · "Declined — no reason given" ·
  "Declined — superseded by request for an alternative (<reason if given>)" · the operator's modified
  form (accept-with-modification) · "No grounded elevation beyond the resolved design" (title: `none found`).
- **Rationale:** the operator's acceptance/decline reasoning + the grounding.
```

- `EV-{n}` is per-ledger sequential; ALWAYS `· LOCKED` (any other status silently never emits).
- **Title safety:** no `·`/`—` followed by locked/resolved/open inside the short title — the parser takes
  the first status token on the line.
- **Edges-exemption:** EV entries are the ONLY entries exempt from the Edges/scenarios rule below — a
  declined or null elevation has no edges to define; an ACCEPTED elevation that opens new branches gets
  those edges in the normal `D{n}` entries the scoped re-check gates.
- A Path-A bail (no ELEVATE) checkpoints one plain line instead: "grill ended via operator 'execute' —
  Path A; ELEVATE forgone".

## Rules
- **The frontmatter block is written at creation** (above), `status: draft`, and the frontmatter — never the
  body prose — is the single source of truth for the ledger's status. Where stale body prose disagrees with a
  later recorded act, the act wins and the frontmatter carries it.
- **LOCKED** entries are frozen: re-deciding one downstream is drift ([[kata-orchestrate]] enforces this).
- An entry isn't done until **Edges/scenarios** is filled — a decision without defined edges is still fuzzy
  (EV entries exempt, above).
- The ledger is complete when it covers **every** branch enumerated in the grill's Phase-0 decision tree and
  the convergence criteria pass. A gap in the ledger is a gap the executor will fill by guessing.
- The two drift-magnets to record with extra care: **classification/boundary calls** and **magnitude/constant
  choices** — these are where sloppy specs ship wrong behavior (see [[LESSONS-LEARNED]] L10).
