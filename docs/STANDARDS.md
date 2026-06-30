# STANDARDS.md — frontmatter, versioning, naming, file conventions

> The conventions that **permeate the project**. Every skill and durable artifact conforms. Aligns with
> the [agentskills.io](https://agentskills.io) open standard, the Claude Code skill/subagent schemas,
> and Obsidian frontmatter — chosen so the same files are valid across tools and render in a vault.

## 1. Skill frontmatter (canonical schema)

Every `skills/<category>/<name>/SKILL.md` opens with YAML frontmatter:

Schema v2 (2026-06-07) — audited live against the agentskills.io open standard, Anthropic Agent Skills,
and Obsidian 1.9+ Properties. See `.planning/specs/modes-A1-foundations/FRONTMATTER-AUDIT.md` + decisions
D26/D31.

```yaml
---
name: kata-grill                # REQUIRED (spec). ==dir; ^[a-z0-9]+(-[a-z0-9]+)*$; ≤64; no leading/trailing/`--`
description: >-                  # REQUIRED (spec). non-empty; ≤1024; trigger-rich (what + when)
  Relentless, doc-grounded interrogation that resolves every decision branch and updates CONTEXT.md
license: Apache-2.0             # REQUIRED here (spec field; public-intended → every skill carries it) — D31c
version: 0.1.0                   # REQUIRED. semver, per-skill, independently bumped (see §3)
category: plan                   # REQUIRED. one of: plan|coordinate|execute|evaluate|handoff|meta|cognition
status: experimental             # REQUIRED. experimental | beta | stable | deprecated
agnostic: true                   # REQUIRED. true = no tool-specific deps in the skill body
cost-weight: 4                   # REQUIRED. 1–5 (authority: .planning/SKILL-COST-RATINGS.md) — D27
allowed-tools: [Read, Grep, Glob, Write]   # REQUIRED. non-empty YAML list (Claude v0.1); adapter normalizes to the open-standard space-separated string (D31b). Evaluators MUST omit Write/Edit. (REQUIRED + shape enforced — dogfood-selfup-1)
model: opus                      # OPTIONAL. only when the model is fixed for correctness
compatibility: >-               # OPTIONAL (spec; ≤500). env requirements; doubles as a human-readable pre-flight hint (D29)
  Requires git + a subagent-capable host
source: >-                       # OPTIONAL but REQUIRED when adapting external work (provenance)
  adapted-from mattpocock/skills@{grill-me, grill-with-docs, ubiquitous-language}
supersedes: []                   # OPTIONAL. skill names this replaces
aliases: []                      # OPTIONAL (Obsidian-reserved). renames / tier-family alias surface
tags:                            # OPTIONAL but RECOMMENDED. namespaced automation scaffold (§1.1)
  - kata/plan                    #   kata/<category>
  - kata/spine                   #   kata/spine | kata/module/<module>
  - grilling                     #   free domain tags
---
```

**Rules**
- `name` MUST equal the directory name and match `^[a-z0-9]+(-[a-z0-9]+)*$`, ≤64 chars, no leading/trailing
  hyphen, no `--` (agentskills.io spec — enforced by `tools/validate_skills.py`). The `kata-<verb>` /
  `kata-<verb>-<tier>` conventions (§2, D26) are *additional* to the spec regex.
- `description` MUST be non-empty and ≤1024 — it is the *only* thing a host model sees when deciding to
  invoke; make it trigger-rich.
- **Governance fields stay top-level (D31a)** — Obsidian-first: top-level properties are first-class in the
  core Properties UI and queryable. The spec's `metadata:` map is the *blessed* home for custom keys, but we
  keep them flat for vault visibility; the spec explicitly tolerates them ("agent-specific fields are safely
  ignored"). Do NOT mirror a field both top-level and under `metadata:` (drift).
- `allowed-tools` enforces least privilege **structurally** (not by prose). Evaluator skills MUST omit
  Write/Edit (the Anthropic fresh-context, no-write evaluator, made structural). Not a sandbox — `Bash` may
  remain for *running* gate commands; an evaluator never authors artifacts. Canonical form is the YAML list
  for the Claude v0.1 adapter; the adapter normalizes to the open standard's space-separated string (D31b).
- `agnostic: false` is allowed only inside `adapters/<tool>/` skills; core `skills/**` MUST be `true`.
- `source:` is mandatory whenever a skill is derived from external work — we stand on shoulders *and attribute*.
- **Obsidian:** only the *plural* reserved props exist — `tags` / `aliases` / `cssclasses` — and their values
  MUST be lists (1.9 removed the singular `tag`/`alias`/`cssclass`). Never use the singular forms.

### 1.1 Tag namespace (automation scaffold — D31)
`tags` is the future-automation surface. Use Obsidian nested tags (`/`) so automations can query slices:
- `kata/<category>` (always) · `kata/spine` OR `kata/module/<module>` (always) ·
  `kata/tier/<tier>` (tier skills only, A2) · free domain tags (`grilling`, `tdd`, `red-team`, …).

### 1.2 Reserved extension points (declared, not populated in v0.1)
- `hooks:` — event-driven automation triggers (the home for future automated actions). Reserved.
- `context: fork` (+`model`) — the **Claude-adapter binding** for our fresh-context, no-write evaluators
  (`kata-evaluate`, `kata-review`). The capability is abstract; this is the binding, documented in the
  Claude adapter, never depended on by the agnostic body.

### 1.3 Agent-distilled discriminators (managed learning — loop-cognition L5/D77)
A skill the **loop itself distilled** (not a human-authored core skill) carries extra discriminators so it is
**matched-but-marked** — same `kata-<verb>` name + category + v2 schema, *plus*:
- `provenance: agent-distilled` — distinguishes it from human-authored skills.
- `scope: agent | coding-agent | universal` — its reach. A **candidate** is `scope: agent` and **NOT loaded
  universally**; [[kata-promote]] bumps the scope on promotion.
- `summary: <≤60 chars>` — a one-line catalog blurb (tighter than `description`).
- tag `kata/origin/agent` — the automation slice for agent-made skills.

These live on skills in the **agent-skills toolkit** (`agentSkills.dir`, first-run-configured) — **outside this
repo's `skills/` tree**, so `tools/validate_skills.py` (which scans `skills/`) does not enforce them; they are
governed by [[kata-promote]] (stage 2) + the grounding gate (stage 1, [[kata-evaluate]] injected-knowledge mode,
D33). Core repo skills never carry these fields.

## 2. Naming convention (permeates everything)

- **Skills:** `kata-<verb>` — `kata-grill`, `kata-plan`, `kata-orchestrate`, `kata-board`,
  `kata-evaluate`, `kata-handoff`, `kata-write-skill`. Verb-first = action-oriented + collision-safe.
- **Categories (dirs)** = the loop phases: `plan/ coordinate/ execute/ evaluate/ handoff/ meta/ cognition/`.
- **Layout:** `skills/<category>/<name>/SKILL.md` (+ optional `resources/`, `CHANGELOG.md`).
- **Protocol files:** `protocol/<thing>.md` (schemas for `board`, `tasklist`, `state`, `handoff`).
- **Adapters:** `adapters/<tool>/` (`claude`, `codex`, `kiro`, `acp-quick`).
- **Durable artifacts:** `SCREAMING-KEBAB.md` at root/.planning (`DESIGN.md`, `DECISIONS.md`,
  `LESSONS-LEARNED.md`, `BACKLOG.md`, `STEERING.md`).

## 3. Versioning (per-skill + suite)

- **Per-skill semver** in frontmatter, bumped independently: MAJOR = breaking contract change,
  MINOR = new capability, PATCH = fix/wording. Optional `skills/**/CHANGELOG.md` for history.
- **Pre-release hold (current policy, 2026-06-08):** while the suite is pre-`v0.1` and every skill is
  `experimental`, **all skills are HELD at `0.1.0`** — the meaningful version number is the *suite* version
  (README / `v0.1`), and per-skill bumps below a first release are bookkeeping without a consumer. New skills
  enter at `0.1.0`; modifications do **not** bump. **The moment `v0.1` ships, this hold ends and bump-on-modify
  (the rule above) becomes mandatory** — flipping it is a v0.1 release-checklist item (`.planning/ROADMAP.md`).
  The frontmatter `version` field is still REQUIRED and validator-enforced throughout; only the *incrementing*
  is deferred.
- **Suite version** lives in `README.md` + a future `package`/`plugin.json`; it is *not* the sum of
  skill versions — it marks compatible bundles.
- **Per-skill frontmatter is the machine source of truth** (version/category/status/cost-weight — one
  place, can't drift). **The README skill index is the generated catalog + public landing page**: the
  `tools/` validator regenerates its mechanical columns from frontmatter, while the "Use" prose column and
  the suite-level version/status narrative are hand-authored. It is the human discovery surface and the repo
  front door — not the machine truth (D28; supersedes the earlier "README index is the source of truth"
  framing, a pre-spin-off legacy statement). A skill not present in the index is not "released."
- `status` lifecycle: `experimental → beta → stable`; retiring → `deprecated` + `supersedes` on the
  replacement; deprecated skills move to a `deprecated/` area, never silently deleted.
- `supersedes:` is now **wired as install/update-time precedence** (no longer dormant): a promoted toolkit
  skill carrying `supersedes: <name>` shadows that upstream skill by name at install/update time —
  precedence fork > overlay > pristine — gated by `kata-promote`; no schema change.

## 4. The AGENTS.md / CLAUDE.md dual standard

- `AGENTS.md` is **canonical** (cross-tool industry norm). `CLAUDE.md` is a **pointer** + Claude-only
  notes. Adapters for other tools map the canonical instructions to that tool's instruction file
  (e.g. `.cursorrules`, Kiro/Codex equivalents). One source of truth, many pointers.

## 5. Obsidian / durable-artifact compatibility

- Durable, human-facing artifacts (handoff, decisions, research, board-as-narrative) use **YAML
  frontmatter + `[[wikilinks]]` + `#tags`** so they render and link in an Obsidian vault — and stay
  consistent with the user's memory-file convention.
- Machine coordination state (live board, task-claim locks) is kept **separate** from durable docs
  and is **not** vault-managed (it churns and is hand-edit-hostile, per Anthropic's JSON-state guidance).
