# STANDARDS.md — frontmatter, versioning, naming, file conventions

> The conventions that **permeate the project**. Every skill and durable artifact conforms. Aligns with
> the [agentskills.io](https://agentskills.io) open standard, the Claude Code skill/subagent schemas,
> and Obsidian frontmatter — chosen so the same files are valid across tools and render in a vault.

## 1. Skill frontmatter (canonical schema)

Every `skills/<category>/<name>/SKILL.md` opens with YAML frontmatter:

```yaml
---
name: kata-grill                # REQUIRED. agentskills.io id; matches dir; kebab-case; kata-<verb>
description: >-                  # REQUIRED. one line; the discovery trigger (what + when)
  Relentless, doc-grounded interrogation that resolves every decision branch and updates CONTEXT.md
version: 0.1.0                   # REQUIRED. semver, per-skill, independently bumped (see §3)
category: plan                   # REQUIRED. one of: plan|coordinate|execute|evaluate|handoff|meta|cognition
status: experimental             # REQUIRED. experimental | beta | stable | deprecated
agnostic: true                   # REQUIRED. true = no tool-specific deps in the skill body
allowed-tools: [Read, Grep, Glob, Write]   # OPTIONAL. least-privilege; evaluators are read-only
model: opus                      # OPTIONAL. only when the model is fixed for correctness
source: >-                       # OPTIONAL but REQUIRED when adapting external work (provenance)
  adapted-from mattpocock/skills@{grill-me, grill-with-docs, ubiquitous-language}
supersedes: []                   # OPTIONAL. skill names this replaces
tags: [planning, grilling, ddd]  # OPTIONAL. Obsidian tags
---
```

**Rules**
- `name` MUST equal the directory name and start with the `kata-` prefix.
- `description` is the *only* thing a host model sees when deciding to invoke — make it trigger-rich.
- `allowed-tools` enforces least privilege **structurally** (not by prose). Evaluator skills MUST omit
  Write/Edit. This is the Anthropic "fresh-context, no-write evaluator" made structural.
- `agnostic: false` is allowed only inside `adapters/<tool>/` skills; core `skills/**` MUST be `true`.
- `source:` is mandatory whenever a skill is derived from external work — we stand on shoulders *and
  attribute*.

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
- **Suite version** lives in `README.md` + a future `package`/`plugin.json`; it is *not* the sum of
  skill versions — it marks compatible bundles.
- **The README skill index is the source of truth** for which skills exist and at what version
  (§ README). A skill not listed in the index with a version is not "released."
- `status` lifecycle: `experimental → beta → stable`; retiring → `deprecated` + `supersedes` on the
  replacement; deprecated skills move to a `deprecated/` area, never silently deleted.

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
