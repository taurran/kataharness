---
name: kata-context
description: >-
  Build and maintain the project's ubiquitous-language glossary (CONTEXT.md) so every skill, agent, and
  durable doc speaks the same precise vocabulary. Use during grilling/planning whenever a term is resolved,
  sharpened, or found to conflict — keep the glossary canonical and implementation-free.
license: Apache-2.0
version: 0.1.0
category: plan
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: adapted-from mattpocock/skills {ubiquitous-language, grill-with-docs CONTEXT-FORMAT}
tags:
  - kata/plan
  - kata/spine
  - ddd
  - ubiquitous-language
  - glossary
---

# kata-context — one canonical word per concept

Shared, precise language is what lets a frozen plan mean the same thing to every agent. `CONTEXT.md` is the
glossary and **nothing else** — not a spec, not a scratchpad, not a home for implementation decisions
(those are ADRs / the decision ledger).

## What it does
- Maintains `CONTEXT.md` at the repo root (single context) or per-context files indexed by `CONTEXT-MAP.md`
  (multi-context). Infers which applies; creates the file **lazily** on the first resolved term.
- Works hand-in-glove with [[kata-grill]]: when grilling resolves or sharpens a term, capture it here
  immediately (inline, not batched).

## Relationship to [[kata-grill]] (no duplication)
During a grill, [[kata-grill]] captures terms inline using *this* format and these rules. `kata-context` owns
**standalone glossary maintenance** and **multi-context maps** outside a grill (e.g. a later refactor that
renames a concept). One glossary, one format, two entry points — the rules live here; the grill references them.

## Rules (from grill-with-docs CONTEXT-FORMAT)
- **Be opinionated.** When several words mean one concept, pick the best; list the rest under `_Avoid_:`.
- **Tight definitions.** One or two sentences. Define what it IS, not what it does.
- **Context-specific terms only.** General programming concepts don't belong, even if heavily used.
- **Group under subheadings** when natural clusters emerge; a flat list is fine for a cohesive area.
- **Challenge conflicts.** If a new usage contradicts an existing entry, surface it and resolve which is right
  before writing — never let two definitions of one term coexist.

## Entry format
```md
**{Term}**:
{One or two sentence definition — what it IS.}
_Avoid_: {synonyms to stop using}
```

## Multi-context
If a `CONTEXT-MAP.md` exists, route the term to the right context and keep the map's relationships current.
If neither file exists yet, start a root `CONTEXT.md` on the first term.
