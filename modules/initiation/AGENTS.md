# modules/initiation/AGENTS.md

> **Nested-AGENTS rollup target.** This file composes under the root `AGENTS.md` via the standard
> nested-AGENTS.md vertical rollup (`kata-orient` assembles: root invariants → this file → task assignment).
> State only what **specializes** the module — do not restate the spine.

## Module responsibility (front half only)

The initiation module owns the **front half of the Kata Loop**:

```
user intent + design/brief
        │
        ▼
  [ kata-initiate ]
        │  ingest → classify kind
        │  interactive target/platform/vault config
        │  drive grill to readiness (dual control)
        │
        ▼
  frozen INTENT.md  ←─ the hand-off artifact
        │
        ▼
  harness (the built loop, unchanged)
```

**Single responsibility:** transform a raw user intent (system prompt and/or project-brief file) into a
frozen `INTENT.md` artifact that the harness can execute against — nothing more.

## Contract

| Direction | What |
|---|---|
| **Input** | User's design/brief (system prompt and/or a project-brief file) + any existing `AGENTS.md` / `CONTEXT.md` in the target repo |
| **Output** | A frozen `INTENT.md` (schema: `protocol/intent.md`) + the full session context handed to the harness |

The module **composes** existing skills (`kata-readiness`, `kata-grill`, `kata-bootstrap`,
`kata-context`). It **never reimplements** the spine, the grill machinery, or any gate. It **does not
gate** — gating remains `kata-evaluate`'s responsibility.

## Platform swap

A platform (e.g. MindBridge) may **replace this entire directory** with its own `modules/initiation/`
— its own `AGENTS.md` + installer. The conductor (`kata-loop`, planned) depends only on the
**contract** above (`INTENT.md` in → context out), not on this implementation. Spine #3
(agnostic-via-adapters) applies at module granularity.

Installer mechanics (how skills land in a target repo/vault) are deferred to Phase 5 — this module
covers the **config layer** only (which target, which vault, which platform).

## Backward-compatibility

`INTENT.md` absent ⇒ the harness reads the frozen DESIGN as today. The initiation module is
**additive**: skipping it leaves the direct one-shot harness run unchanged (BC, DESIGN §9).
