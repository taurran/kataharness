# modules/closeout/AGENTS.md

> **Nested-AGENTS rollup target.** This file composes under the root `AGENTS.md` via the standard
> nested-AGENTS.md vertical rollup (`kata-orient` assembles: root invariants → this file → task assignment).
> State only what **specializes** the module — do not restate the spine.

## Module responsibility (back half only)

The closeout module owns the **back half of the Kata Loop**:

```
  harness (the built loop — RESULT.json + .kata/ artifacts emitted)
        │
        ▼
  [ kata-closeout ]
        │  track .kata/{RESULT.json, footprint.json, mutation.json}
        │  compose kata-report over those artifacts
        │  offer kata-understand (opt-in, per run)
        │  human decision gate
        │
        ▼
  report + human decision
        │
        ├── satisfied? → commit / push / merge (git actions carried out)
        │
        └── run again (version-up) or build something else?
              │
              ▼
        handed to the conductor's loop-back
```

**Single responsibility:** transform the completed run's machine artifacts and the post-gate verdict into a
human-reviewable report, then capture the human's decision and hand it to the conductor — nothing more.

## Contract

| Direction | What |
|---|---|
| **Input** | The completed run + its `.kata/` artifacts (`.kata/RESULT.json`, `.kata/footprint.json`, `.kata/mutation.json`) + the post-gate verdict from `kata-evaluate` |
| **Output** | A durable report (via `kata-report`) + the human's decision: `{satisfied, git-actions, run-again \| build-new}` |

The module **composes** existing skills (`kata-report`, `kata-understand`, `kata-handoff`). It **never
reimplements** the spine, the gate, or any evaluation logic. It **does not gate** — the default-FAIL gate
is and stays `kata-evaluate`'s responsibility. Closeout runs **after** the gate and **reports**; it never
confers a pass/fail verdict.

## Composes, never gates

`kata-closeout` is additive. The never-gates property is structural, not a suggestion:
- `kata-evaluate` owns the default-FAIL gate (spine principle #4).
- `kata-closeout` reads and reports the gate's verdict; it does not re-derive or re-evaluate it.
- The human decision gate inside closeout is a **human** gate — it surfaces options; the agent carries out
  only what the human explicitly approves (commit/push/merge require explicit sign-off).

## Platform swap

A host platform may **replace this entire directory** with its own `modules/closeout/`
— its own `AGENTS.md` + skills. The conductor (planned; reference in prose only — not yet built) depends
only on the **contract** above (`.kata/` artifacts + post-gate verdict in → report + human decision out),
not on this implementation. Spine #3 (agnostic-via-adapters) applies at module granularity.

## Backward-compatibility

Closeout is additive. Absent the closeout module, the harness completes with the evaluate gate as today.
Running closeout never weakens the default-FAIL gate — a NEEDS_WORK verdict from `kata-evaluate` is
surfaced verbatim in the report; closeout does not override it (DESIGN §9, BC).
