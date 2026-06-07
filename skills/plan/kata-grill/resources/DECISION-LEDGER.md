# DECISION-LEDGER format — the grill's output

The running record [[kata-grill]] appends to as each decision branch resolves. It is the raw material the
FREEZE phase ([[kata-design-doc]], [[kata-plan]]) compiles into the frozen contract. Keep it durable
(Obsidian-native frontmatter + wikilinks); one entry per resolved branch.

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

## Rules
- **LOCKED** entries are frozen: re-deciding one downstream is drift ([[kata-orchestrate]] enforces this).
- An entry isn't done until **Edges/scenarios** is filled — a decision without defined edges is still fuzzy.
- The ledger is complete when it covers **every** branch enumerated in the grill's Phase-0 decision tree and
  the convergence criteria pass. A gap in the ledger is a gap the executor will fill by guessing.
- The two drift-magnets to record with extra care: **classification/boundary calls** and **magnitude/constant
  choices** — these are where sloppy specs ship wrong behavior (see [[LESSONS-LEARNED]] L10).
