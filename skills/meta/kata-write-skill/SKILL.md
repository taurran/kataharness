---
name: kata-write-skill
description: >-
  Author a new kata-* skill to the project STANDARDS — correct frontmatter, least-privilege tools,
  provenance, semver, progressive disclosure, and registration in the README index. Use when a new skill is
  needed (typically invoked by kata-improve). Governs HOW to author well; kata-improve decides WHAT/WHEN.
license: Apache-2.0
version: 0.1.0
category: meta
status: beta
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: adapted-from mattpocock/skills productivity/write-a-skill
tags:
  - kata/meta
  - kata/module/meta
  - authoring
  - standards
  - skills
---

# kata-write-skill — make new skills the governed way

Authoring is a deliberate act, not freehand (the v0.1 review proved why: honesty/least-privilege/provenance
drift). This skill governs the *how*; [[kata-improve]] (or the human) decides the *what* and *when*.

## Conform to STANDARDS — point, don't restate
The frontmatter schema, naming (`kata-<verb>`), category enum, versioning, and durable-artifact conventions
live in `docs/STANDARDS.md` — **read it; do not duplicate it here** (DRY). This skill adds only the authoring
*procedure* on top of that schema.

## Procedure
1. **Requirements** — what task, what triggers, which loop phase, what it must NOT do (the boundary vs
   neighboring skills — name it explicitly so it can't compete). Take these from [[kata-improve]] if invoked
   by it.
2. **Draft** `skills/<category>/<name>/SKILL.md`:
   - Frontmatter per STANDARDS: `name`(==dir, `kata-<verb>`), trigger-rich one-line `description`, `version`
     `0.1.0`, `category`, `status: experimental`, `agnostic: true`, **least-privilege `allowed-tools`**
     (evaluators omit Write/Edit), `source:` provenance (must map to a real ADOPT row in `research/NOTES.md`).
   - **No `model:` field** (`docs/STANDARDS.md §1` / A1 guard `check_model_in_skill_frontmatter`):
     `model:` is **FORBIDDEN** in core SKILL.md frontmatter. Model is dispatch-resolved *relative to the
     operator's anchor at runtime* — never pinned in a skill body. Hard-baking a model ID force-switches
     the host model and silently breaks when that model is gated or unavailable (the **Fable-outage
     class** of failure). Rely on dispatch-time relative resolution instead. `adapters/**` may still pin
     a model (R8 carve-out); core `skills/**` must not. The validator raises a hard ERROR (not a warning)
     on any absolute `model:` key present here — see `docs/STANDARDS.md §1` and `AGENTS.md`
     (model-tiering D131).
   - Body: lean. **Context efficiency is a design constraint** — the body loads only when invoked, the
     `description` is the only always-resident cost, so make it tight and trigger-rich. Keep SKILL.md short
     (~100 lines); push depth into `resources/` (progressive disclosure, refs one level deep); reference
     canonical docs by pointer, never restate them.
3. **Register** in the README skill index (the source of truth — D6): name · version · category · status ·
   source · use. A skill not in the index isn't released.
4. **Provenance** — add/extend the `research/NOTES.md` adopt/drop/distort row for any external source.

## Authoring an agent-distilled CANDIDATE (stage 1 of managed learning — loop-cognition L5)
When the loop (not a human) distils a reusable pattern into a skill, author it as a **candidate**, not a core
skill:
- Write it to **`<agentSkills.dir>/candidates/<name>/SKILL.md`** (the toolkit, `protocol/config.md`) — **NOT**
  into this repo's `skills/` tree, and **not loaded universally**.
- Add the **agent-distilled discriminators** ([[STANDARDS]] §1.3): `provenance: agent-distilled`,
  `scope: agent`, `summary` (≤60 chars), tag `kata/origin/agent`. `status: experimental`, `version: 0.1.0`.
- The candidate then passes the **grounding gate** ([[kata-evaluate]] injected-knowledge mode, D33) for
  soundness, and waits for the **human promotion gate** ([[kata-promote]], stage 2) before it can persist or
  widen its `scope`. Authoring a candidate never makes it universal — that is [[kata-promote]]'s decision.

## Review checklist (before done)
- [ ] `name`==dir, `kata-<verb>`; category in enum; `agnostic: true` honest (no tool-specific deps in body —
      push tool bindings to an adapter note, like kata-grill/kata-orchestrate do)
- [ ] `description` trigger-rich, third person, "Use when …"
- [ ] `allowed-tools` least-privilege and justified
- [ ] No `model:` key in frontmatter — dispatch-resolved, never pinned in a skill body (A1 guard:
      `check_model_in_skill_frontmatter` hard-fails any absolute `model:` in core SKILL.md;
      see `docs/STANDARDS.md §1`, model-tiering D131)
- [ ] `source:` maps to a `research/NOTES.md` row; boundary vs neighbors stated (no overlap)
- [ ] SKILL.md lean; depth in `resources/`; pointers not restatements
- [ ] README index updated
- [ ] (D15) a fresh-context [[kata-review]] pass before it's called done
