# FRONTMATTER-AUDIT — our skill frontmatter vs Obsidian + agentskills.io + Claude skills

> Deep evaluation requested before A1 execution (the A1 validator enforces this schema, so lock it first).
> Live sources checked 2026-06: the agentskills.io **open standard**, Anthropic Agent Skills (platform docs +
> `anthropics/skills`), **Obsidian Properties** (1.9+), and a Claude-Code SKILL.md field reference.
> Verdict + decisions at the bottom.

## 1. Spec-standard fields (agentskills.io) — our standing

| Field | Spec | Ours today | Action |
|---|---|---|---|
| `name` | **required**; ≤64; `^[a-z0-9]+(-[a-z0-9]+)*$` (no leading/trailing/`--`); **==dir** | have (dir match only) | **ADD** regex + length checks to validator |
| `description` | **required**; non-empty; ≤1024 | have | **ADD** ≤1024 + non-empty check |
| `license` | optional | **MISSING** | **ADD** (public-intended → every skill should carry it) |
| `compatibility` | optional; ≤500; env requirements (product, packages, network) | **MISSING** | **ADD** on skills with env needs — doubles as a human-readable pre-flight hint (D29) |
| `metadata` | optional; arbitrary key→value catch-all; **spec's recommended home for custom fields** (its own example nests `version` here) | unused | decision below (governance home) |
| `allowed-tools` | optional; **space-separated string**; *experimental* | have as a **YAML list** | format decision below |

## 2. Our custom "kata-governance" fields — where they should live

We carry these top-level today: `version`, `category`, `status`, `agnostic`, `cost-weight`, `source`,
`supersedes`, `model`, `tags`.

- **Spec stance:** custom fields are "safely ignored by agents that don't support them" at top level; the
  *recommended* home is `metadata:`. So top-level is **tolerated, not blessed**.
- **Obsidian stance:** flat **top-level** properties are first-class — editable in the core Properties UI and
  directly queryable. Fields nested under `metadata:` are valid YAML and Dataview-queryable (`metadata.version`)
  but **do not appear in Obsidian's core Properties UI**.
- **The tension:** Obsidian-first ⇒ keep them top-level; strict-spec ⇒ move them under `metadata:`. The user
  ranked **Obsidian compatibility #1**, and the spec explicitly tolerates top-level custom keys → **recommend
  top-level**, documented as "spec-tolerated, agent-ignored extensions."

## 3. Obsidian compatibility — clean, with notes

- **Reserved plural list-props:** `tags`, `aliases`, `cssclasses`. Obsidian 1.9 **removed** the singular
  `tag`/`alias`/`cssclass`; values **must be lists**. Our `tags: [list]` ✓. (Never use singular forms.)
- **Property types:** text · number · checkbox · date · datetime · list · links. Our mappings are all valid:
  `version`→text (quote it; `0.1.0` is not a valid number so YAML reads it as string anyway), `cost-weight`→
  number, `agnostic`→checkbox, `supersedes`/`tags`→list.
- **`aliases`** (reserved, available): reserve for renames + the tier-family alias concept (D26).
- **No reserved-key collisions:** `name`/`description`/`status`/`category`/`model`/`license` are all safe.

## 4. Claude-Code recognized extensions (agent-specific; safely ignored by other tools)

Beyond the open standard, the Claude adapter recognizes: `model` (we use it), `effort: low|medium|high`,
`context: fork` (+`model`), `hooks`, `disable-model-invocation`, `argument-hint`. Relevance to us:

- **`context: fork`** is the **native Claude binding for our fresh-context, no-write evaluators**
  (`kata-evaluate`, `kata-review`). Worth noting in the Claude adapter as the binding for the abstract
  "run this in a fresh subagent context" capability — we don't depend on it in the agnostic body.
- **`effort`** maps to our D19 effort overlay — set at the bootstrap/`kata.config`, **not** baked per-skill
  (keeps effort orthogonal). Good that the field exists; we don't hard-code it.
- **`hooks`** is the event-driven-automation surface — the natural home for the user's #3 (future automation
  actions). We **reserve** it now (document it as the extension point); we don't populate it in A1.

## 5. Tagging scaffold for future automation (user #3)

Restructure `tags` from flat keywords into a **namespaced hierarchy** (Obsidian supports nested tags via `/`),
so future automation can query/filter slices of the suite deterministically:

```
tags:
  - kata/<category>          # kata/plan, kata/coordinate, ...   (mirrors the loop phase)
  - kata/spine               # OR kata/module/<module>           (spine-vs-module, D20)
  - kata/tier/<tier>         # A2 only: kata/tier/standard, ...
  - kata/<domain>            # grilling, tdd, red-team, doc-baking, ...
```

This scaffolds automations like "run/lint all `kata/spine` skills," "price every `kata/tier/advanced`,"
"surface all `kata/module/design`." Pairs with the reserved `hooks:` field for when an automation needs an
event trigger rather than a query. Low cost now, high option-value later.

## 6. Recommended schema v2 (the delta to apply in A1)

**Top-level** (spec-standard + Obsidian-reserved + spec-tolerated governance):
`name` · `description` · `license` *(NEW)* · `compatibility` *(NEW, where needed)* · `allowed-tools` ·
`model` · `version` · `category` · `status` · `agnostic` · `cost-weight` · `source` · `supersedes` ·
`tags` *(restructured §5)* · `aliases` *(optional)*.

**Validator additions (A1 / Task 1–2):**
- `name`: `^[a-z0-9]+(-[a-z0-9]+)*$`, ≤64, ==dir (spec-compliance by construction).
- `description`: non-empty, ≤1024.
- `license`: required (value per decision-c).
- `tags`: every entry under the `kata/...` namespace (lint), at least `kata/<category>` + spine/module present.
- *(A2)* tier skills: `tags` carry `kata/tier/<tier>`; family rubric folders documented.

**Reserved, not populated in A1:** `hooks` (automation), `context: fork` (Claude-adapter evaluator binding).

## Decisions for the human
- **(a) Governance fields home** — *top-level* (Obsidian-first; spec-tolerated) **[recommended]** vs nested
  under `metadata:` (strict-spec; loses core-UI visibility).
- **(b) `allowed-tools` format** — keep the **YAML list** for the Claude v0.1 adapter (the adapter normalizes
  to the open-standard space-separated string) **[recommended]** vs switch to the space-string now.
- **(c) `license` value** — pick an OSS license now (public-intended): **Apache-2.0** (patent grant — sensible
  for a framework) **[recommended]** vs MIT (simplest) vs `license: see LICENSE` (defer the choice, add field).
- **(d) Adopt `context: fork` as the Claude-adapter evaluator binding + reserve `hooks`** for future
  automation — **[recommended yes]**; documentation-only, no behavior change in A1.
