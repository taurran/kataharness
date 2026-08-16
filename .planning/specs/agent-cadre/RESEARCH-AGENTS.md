---
spec: agent-cadre
kind: field survey — how to build OUR agent definitions (AC-6, extended by AC-9)
produced: 2026-08-16 by a dispatched read-only research agent; evidence labels preserved
labels: RV file-verified (read at the cited absolute path on this machine) · DS doc-sourced
  (URL cited) · UA unverified assumption · UNKNOWN honestly unresolved
scope: agent DEFINITION shape only. Memory/skills-gating mechanics are covered by
  ../learning-graph/RESEARCH-HERMES-PI.md and are not re-covered here except where they
  constrain the definition format.
consumes: GRILL-LEDGER.md (AC-1..AC-9, roster draft v0)
---

# RESEARCH-AGENTS — surveying the field for the KataHarness agent cadre

> **Label discipline (PD-2).** Every claim below carries its evidence class. `RV` means I read
> the file at the cited path. `DS` means I read the vendor/repo documentation at the cited URL
> (fetched 2026-08-16). `UA` means I am reasoning past the evidence and saying so. `UNKNOWN`
> means I could not resolve it and refuse to guess. Where a source contradicts itself, I say so
> rather than picking the flattering reading.

---

## 1. Per-target findings

### 1.1 HERMES (Nous Research) — agent definition shape

**The headline, and it inverts an assumption in AC-4.** Hermes has **no persistent agent
definition files at all**. There is no `~/.hermes/agents/`, no per-role persona file, no
frontmatter schema for an agent. — DS
(hermes-agent.nousresearch.com/docs/user-guide/features/delegation;
.../docs/guides/delegation-patterns)

Specialization in Hermes is achieved by **three mechanisms, none of them a definition file**:

1. **Per-dispatch prompt fields.** `delegate_task(goal, context, role, max_iterations, tasks)`.
   `goal` and `context` are required and carry the entire specialization. Subagents start with
   a *completely fresh conversation* — "zero knowledge of the parent's conversation history";
   the only context is what the parent typed into those two fields. — DS (…/features/delegation)
2. **A two-value role enum**, not a roster: `role: "leaf"` (default, cannot delegate) or
   `role: "orchestrator"` (may spawn workers, and only when `delegation.max_spawn_depth` is
   raised above its default of 1). Tool restriction is attached to the enum, not to a named
   agent: leaves lose `delegate_task`, `clarify`, `memory`, `send_message`, `cronjob`; both
   roles keep `execute_code`. — DS (…/features/delegation, …/guides/delegation-patterns)
3. **Global config, not per-agent config.** `~/.hermes/config.yaml` `delegation:` block sets
   `max_iterations: 50`, `max_concurrent_children: 3`, `max_spawn_depth: 1`, `model`,
   `provider`, `worktree_isolation`, `orchestrator_enabled`, `child_timeout_seconds` — all
   **global per install**. Per-task model override via `delegate_task` is *not supported*
   (the docs route per-task model selection to the Kanban board instead). — DS
   (…/features/delegation)

**Identity is global, not per-role.** `SOUL.md` (`~/.hermes/SOUL.md` or `$HERMES_HOME/SOUL.md`)
is plain markdown with **no field structure**, injected verbatim into the first system-prompt
slot after a security scan and truncation. Personality presets (`helpful`, `concise`,
`technical`, …, plus custom entries under `agent.personalities` in config.yaml) switch tone via
`/personality <name>`. The docs describe **no per-role persona mechanism**. — DS
(…/features/personality)

**Mixture-of-Agents is a model-ensemble, not a role cast** — but it is the closest thing Hermes
has to a multi-seat design, and it is evidence for our Challenger row. MoA presets define
`moa.presets.<name>.reference_models[]` (each with its own `reasoning_effort`) and an
`aggregator` (also with its own `reasoning_effort`); the aggregator is the acting model that
writes the response and emits tool calls, references supply perspectives. Valid effort values:
`none, minimal, low, medium, high, xhigh, max, ultra`. The docs report a two-model preset
(claude-opus-4.8 aggregating over a gpt-5.5 reference) **outscoring either model alone by ~6
points**. — DS (hermes-agent.nousresearch.com/docs/user-guide/features/mixture-of-agents)

**The return contract is real and structured** — worth stealing. Only the final summary enters
the parent's context; alongside it Hermes returns `status`, `exit_reason`, `worktree` (path,
branch, commits, dirty flag) when isolation is on, `pending_steer` / `missed_steer` for
redirected children, and timeout metadata (`timeout_seconds`, `timed_out_after_seconds`,
`timeout_phase`). Per-task live transcripts land at
`~/.hermes/cache/delegation/live/<delegation_id>/task-<n>.log`. The delegation-patterns doc
explicitly says results **require verification by the parent rather than blind acceptance**. — DS

**Verdict for us.** Hermes is a *weak* source for definition shape (it has none) and a *strong*
source for (a) the fresh-context brief contract, (b) role-attached tool stripping, (c)
structured machine-readable return metadata, (d) live transcript durability, (e) the
mixture-of-models evidence. **AC-4's "aligned against Hermes/Quicksilver/Pi" cannot mean
"align the definition format against Hermes" — there is nothing there to align to.** (UA: the
grill should re-word AC-4 to name Pi as the format anchor and Hermes as the dispatch-contract
anchor.)

### 1.2 QUICKSILVER — identified, and it is not a third harness

**QUICKSILVER is the codename of Hermes Agent v0.19.0** (Nous Research), released 2026-07-20.
It is not a separate project. — DS (github.com/NousResearch/hermes-agent releases page,
fetched 2026-08-16; corroborated by aitoolsreview.co.uk/insights/hermes-agent-quicksilver and
medium.com/kd-agentic "Hermes 0.19 Quicksilver")

What v0.19 changed that touches agents: first-turn time-to-first-token down ~80% (~4.3s →
~0.9s) on every surface; **live subagent transcripts + durable background delegation** (a
ledger so background delegation results survive process restarts); "smart approvals" default,
where an LLM reviewer assesses flagged commands rather than every action needing manual
approval; and per-slot `reasoning_effort` controls in MoA presets plus a session-scoped
`/reasoning` command. — DS (same sources)

**Consequence for the roster: the three named inspirations are two harnesses.** The
"Hermes/Quicksilver/Pi" triad in AC-4 double-counts Nous Research. I found **no evidence of any
other agent harness named Quicksilver** in the searches run. If the operator meant a different
Quicksilver, that is UNKNOWN and should be re-asked rather than assumed.

### 1.3 PI — the strongest definition-format source in the survey

Pi core is deliberately minimal, but its subagent ecosystem carries **the richest agent
frontmatter schema I found anywhere**, and it is Claude-Code-shaped (YAML frontmatter + markdown
system prompt), which makes it directly comparable to our target render.

**Discovery precedence** (lowest → highest): builtin
`~/.pi/agent/extensions/subagent/agents/` → package (`package.json` `pi-subagents.agents`) →
user `~/.pi/agent/agents/**/*.md` → project `.pi/agents/**/*.md`. Higher scopes override lower
by canonical name; nested subdirectories are discovered recursively; the user dir is resolved
via `PI_CODING_AGENT_DIR`. — DS (github.com/nicobailon/pi-subagents `docs/agents.md`)

**Full frontmatter schema** — DS (same source). Grouped by what it buys:

| Group | Fields |
|---|---|
| identity | `name` (required), `package` (namespace prefix, e.g. `code-analysis.scout`), `aliases`, `description` |
| capability fence | `tools[]` (strict allowlist; **empty = no tools**), `extensions[]`, `subagentOnlyExtensions[]`, `maxSubagentDepth` |
| model | `model`, **`fallbackModels[]`** (ordered backups, triggered on quota/auth/timeout/unavailability — *not* on ordinary task failure), `thinking` (appended as a `:level` suffix at runtime) |
| context construction | `systemPromptMode: replace\|append`, `inheritProjectContext` (default true for builtins), `inheritSkills` (default **false**), `skills[]`, `skillPath[]`, `defaultContext: fresh\|fork`, `defaultReads[]` |
| budget | `timeoutMs` (default 30 min foreground), `toolTimeoutMs` (5 min for known builtins), `turnBudget: {maxTurns, graceTurns}` |
| output contract | `output` (default output file), `defaultProgress` (maintain `progress.md`), `async` |
| gating | **`acceptance`** (level, or `{level, reason}`), **`acceptanceRole: read-only\|writer`**, **`completionGuard`** (default true; skipped for non-implementation agents) |
| learning | `memory: {scope: project\|user, path}` |

Tool-allowlist syntax carries three shapes in one field: bare names (`read, grep, find`), MCP
entries (`mcp:chrome-devtools`, `mcp:github/search`), and **path-like entries treated as
tool-extension paths** rather than tool names. Model resolution order: explicit call value →
agent `model` → `subagents.agentOverrides.<name>.model` → `subagents.defaultModel` → Pi's
current default. — DS

Validation behaviour worth copying and worth *not* copying: unsafe `memory` paths (traversal,
symlinks) **silently skip rather than fail** (UA: for us that is the wrong default — a silently
skipped safety path is exactly the class of thing PD-2 exists to catch); missing `mcp:`
providers **fail at launch** if explicitly allowlisted (right default); agents holding only
read-only builtins skip completion guards automatically. — DS

**`baryonlabs/pi-agent-harness` — a cadre factory, and the closest prior art to what AC-3 asks
for.** It turns one domain sentence into a team: specialist agents (`.pi/agents`), their skills
(`.pi/skills`), and orchestration prompts (`.pi/prompts`). It ships **six team-architecture
patterns** mapped onto pi's three delegation modes — DS (github.com/baryonlabs/pi-agent-harness):

| Pattern | Delegation mode |
|---|---|
| Pipeline | `chain` (sequential steps) |
| Fan-out / Fan-in | `parallel` (independent work, main integrates) |
| Expert Pool | `single` (selective expert dispatch) |
| **Producer-Reviewer** | `chain` (worker → reviewer → worker loop) |
| Supervisor | main agent's dynamic `parallel` loop |
| Hierarchical Delegation | 2-level delegation |

Modes: `single {agent, task}` · `parallel {tasks[]}` (≤8, 4 concurrent) · `chain {chain[]}` with
a `{previous}` substitution. Inter-agent handoff goes through `_workspace/` files, and
project-level agents are only discovered when `agentScope: "both"`. Per-agent model tiering is
demonstrated concretely: `claude-haiku-4-5` for recon, `claude-sonnet-4-5` for work. — DS

### 1.4 Claude Code native subagent format — the shape our adapter must render into

This is the render target for row 1–14, so I pinned it precisely. — DS
(code.claude.com/docs/en/sub-agents and /docs/en/plugins-reference, both fetched 2026-08-16)

**Locations and precedence** (1 = highest): managed settings (org-wide) → `--agents` CLI JSON
(session) → `.claude/agents/` (project) → `~/.claude/agents/` (user) → **plugin `agents/`
(lowest)**. Directories are scanned recursively; same-name collisions resolve to the
higher-priority location.

**Frontmatter schema.** Required: `name` (lowercase/numbers/hyphens; may not contain `:`, which
is reserved for plugin scoping; surfaces to hooks as `agent_type`), `description` (when Claude
should delegate). Optional: `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`,
`skills[]`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `color`,
`initialPrompt`.

Load-bearing details:
- `model`: `sonnet | opus | haiku | fable | <full model id> | inherit`. **Default is `inherit`.**
  Resolution order: `CLAUDE_CODE_SUBAGENT_MODEL` env → per-invocation `model` param → the
  definition's `model` → the main conversation's model. — DS
- `effort`: `low | medium | high | xhigh | max` (availability model-dependent).
- `tools` / `disallowedTools`: comma-string or array. **`disallowedTools` is applied first, then
  `tools` resolves against the remaining pool.** Omitting `tools` inherits everything available
  to subagents. Agent-spawn scoping is expressible: `tools: Agent(worker, researcher)`. MCP
  patterns: `mcp__<server>`, `mcp__<server>__*`, `mcp__*` (denylist only).
- Tool pool is filtered twice: always removed — `Agent` (at depth limit), `AskUserQuestion`,
  `EndConversation`, `EnterPlanMode`, `ExitPlanMode`, `ScheduleWakeup`, `TaskOutput`,
  `WaitForMcpServers`, `Workflow`; **background subagents** additionally lose everything except
  a named working set. **Forks skip both filters** and get the parent's exact pool. — DS
- `isolation: worktree` is the only valid value.
- `memory: user | project | local` — see §1.4a.
- `color`: `red|blue|green|yellow|purple|orange|pink|cyan`.

**Plugin-shipped agents are a restricted subset.** Supported: `name`, `description`, `model`,
`effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation`.
**"For security reasons, `hooks`, `mcpServers`, and `permissionMode` are not supported for
plugin-shipped agents."** Plugin agents @-mention as `my-plugin:code-reviewer`. `plugin.json`'s
`agents` field **replaces** the default directory scan — listing it there means `agents/` is no
longer scanned unless explicitly re-listed. — DS (plugins-reference)

**Anthropic's own written guidance for writing them** (short, and every line is a design rule
we should carry): "Design focused subagents — each subagent should excel at one specific task";
"Limit tool access: grant only necessary permissions for security and focus"; "Write a clear
description so Claude knows when to use it… include phrases like 'use proactively'"; "Check into
version control". — DS (sub-agents)

**#### 1.4a Native per-agent memory already exists — and it is partly broken**

`memory: user|project|local` gives the subagent a persistent directory
(`~/.claude/agent-memory/<name>/` for user scope, `.claude/agent-memory/<name>/` for project)
and **auto-injects the first 200 lines of `MEMORY.md` into the system prompt on each
invocation**; Read/Write/Edit are documented as auto-enabled so the agent can curate its own
notes. Introduced in v2.1.33 (Feb 2026). — DS (code.claude.com/docs/en/sub-agents field table;
corroborated by hindsight.vectorize.io/blog/2026/05/06/claude-code-subagents-shared-memory and
orchestrator.dev/blog/2026-04-06--claude-code-agent-memory-2026)

**But:** anthropics/claude-code issue **#57507** (reproduced on v2.1.137, **closed as
not-planned**, a re-report of #31294) documents that `memory:` does not reliably create or
update `MEMORY.md`. The reporter's 5-agent matrix shows agents *without* explicit `Write, Edit`
in `tools:` never producing a memory file — i.e. **the `tools:` allowlist appears to override
the documented auto-enable** — plus a second failure mode where an agent *with* proper tool
access still wrote nothing across 5+ invocations (suspected `Task()`-spawn activation gap). Root
cause is stated as unclear; the working workaround is to put `Write, Edit` explicitly in
`tools:` for every memory-enabled agent. — DS (github.com/anthropics/claude-code/issues/57507)

The 200-line injection cap is independent corroboration of Hermes' bounded-curation lesson
already adopted into BL-N16 ("append for audit, distill for load").

### 1.5 GitHub agent ecosystems — what a strong definition actually looks like

I mined five exemplar bodies rather than cataloguing collections. Sizes and shapes differ by
almost an order of magnitude, and the differences are informative.

**(a) `feature-dev:code-reviewer` — the compact-reviewer exemplar. 47 lines.** — RV
(`C:\Users\taurr_nvs748q\.claude\plugins\cache\claude-plugins-official\feature-dev\unknown\agents\code-reviewer.md`)
Frontmatter: `name`, `description`, `tools` (Glob, Grep, LS, Read, NotebookRead, WebFetch,
TodoWrite, WebSearch, KillShell, BashOutput — **no Edit, no Write**), `model: sonnet`,
`color: red`. Body: one role sentence, `## Review Scope` (defaults to `git diff` unstaged),
`## Core Review Responsibilities` (3 bolded lenses), `## Confidence Scoring`,
`## Output Guidance`. Its distinguishing move is a **calibrated 0–100 confidence rubric with
anchored descriptions at 0/25/50/75/100 and a hard reporting floor — "Only report issues with
confidence ≥ 80"** — plus "If no high-confidence issues exist, confirm the code meets standards."
That is a *false-positive* control, and it is the counterweight to the refute-posture our AV
briefs already carry.

**(b) `karpathy-reviewer` — the tool-restriction-discipline exemplar. ~14-line frontmatter.**
— RV (`…\claude-code-skills\engineering-advanced-skills\2.9.0\karpathy-coder\agents\karpathy-reviewer.md`)
```yaml
name: karpathy-reviewer
description: Reviews staged git changes against Karpathy's 4 coding principles. Runs
  complexity_checker on changed files, diff_surgeon on the diff, and produces a verdict with
  specific fix recommendations. Spawn before committing, when the user says "karpathy check", …
domain: engineering
model: sonnet
maxTurns: 30
tools: [Read, Grep, Glob, Bash(git diff *), Bash(git log *), Bash(git status *), Bash(python *)]
disallowedTools: [Bash(rm *), Bash(rmdir *), Bash(curl *), Bash(wget *), Bash(git push *),
  Bash(git reset --hard *)]
skills:
  - karpathy-coder:karpathy-coder
context: fork
```
Three transferable moves: **sub-command-scoped Bash allowlisting** (`Bash(git diff *)` — not a
blanket `Bash`); an **explicit destructive-command denylist** even though the allowlist already
excludes them (defence in depth against allowlist drift); and **deterministic tools invoked
from inside the definition** (`complexity_checker.py`, `diff_surgeon.py` run with `--json`)
so the judgment layer sits on top of machine evidence rather than replacing it. Note `domain:`
and `context: fork` are **not** in the documented Claude Code schema (§1.4) — unknown fields
appear to be tolerated; treat that as UA, not as licence.

**(c) VoltAgent `awesome-claude-code-subagents` — 158+ agents across 10 categories** (Core
Development, Language Specialists, Infrastructure, Quality & Security, Data & AI, Developer
Experience, Specialized Domains, Business & Product, Meta & Orchestration, Research & Analysis),
each category shipped as a plugin (`voltagent-lang`, `voltagent-infra`, …). Prescribed template:
frontmatter `name` (kebab-case), `description`, `tools`, `model`; body = role/expertise opening
paragraph → agent-specific checklists → `Communication Protocol` → `Development Workflow`. It
states a tool convention by purpose — reviewers `Read, Grep, Glob`; research
`Read, Grep, Glob, WebFetch, WebSearch`; code writers `Read, Write, Edit, Bash, Glob, Grep` —
and a stated principle of "minimal permissions". — DS (github.com/VoltAgent/awesome-claude-code-subagents)

**⚠ It violates its own rule, and this is the most useful negative finding in the survey.** The
actual `code-reviewer.md` ships `tools: Read, Write, Edit, Bash, Glob, Grep` and `model: inherit`
— a *reviewer with write access*, contradicting the collection's own read-only convention. Its
"Communication Protocol" is a JSON request blob (`requesting_agent`, `request_type`, `payload.query`)
asking for context it was never given, at ~170 lines / ~2,800 words. — DS (raw
githubusercontent VoltAgent/awesome-claude-code-subagents `categories/04-quality-security/code-reviewer.md`)
**Read: high-star collections are not evidence of discipline.** Tool restriction is the field
most often written as prose and least often enforced in the frontmatter.

**(d) `wshobson/agents` — 202 agents, 16 orchestrators**, organised as
`plugins/{plugin-name}/agents/` with auto-discovery. Its contribution is an explicit
**four-tier model policy**: Opus for architecture / security / code review / production-critical;
`inherit` for user-chosen backend/frontend/AI-ML; Sonnet for docs / testing / debugging / API
reference; Haiku for fast operational tasks. — DS (github.com/wshobson/agents). I could not
fetch an individual agent body (404 on the path I tried), so **its per-file structure and length
are UNKNOWN to me**; only the tier policy is DS.

**(e) GSD agent family — the "long agent" school, and the best researcher body I found.**
— RV (all files under `C:\Users\taurr_nvs748q\.claude\agents\disabled\`)
33 agents, **105 → 1,452 lines, 15,225 lines total, median ≈ 335**. Frontmatter is uniformly
minimal and *lags the platform*: `name`, `description`, `tools`, `color` — and nothing else. No
`model`, no `maxTurns`, no `memory`, no `disallowedTools` on any of the 33. Every file carries a
**commented-out `# hooks:` block** as a convention placeholder. Descriptions consistently end
with the dispatch provenance — "Spawned by /gsd:plan-phase orchestrator" — which is a cheap,
effective way to encode the call graph in the definition itself.

- `gsd-code-reviewer` 387 lines, `tools: Read, Write, Bash, Grep, Glob` (writes REVIEW.md).
- `gsd-verifier` 917 lines — a **7-step goal-backward verification protocol**: Step 0 check for
  previous verification → 1 load context → 2 establish must-haves → 3 verify *observable truths*
  → 3b verification overrides → 4 verify artifacts at **three levels** (exists / imported / used
  beyond imports) → 4b **data-flow trace (Level 4)** → 5 verify key links (wiring) → 6
  requirements coverage → 7 **scan for anti-patterns**: debt-marker comments, empty
  implementations, hardcoded empty data, props with hardcoded empty values, console.log-only
  implementations → 7b behavioral spot-checks → 7c probe execution.
  **This is a mechanised PD-1 "present-but-dead is not built" detector**, and we do not have one
  written down at this granularity.
- `gsd-phase-researcher` 927 lines, organised in **XML section tags** —
  `<downstream_consumer>`, `<philosophy>`, `<tool_strategy>`, `<source_hierarchy>`,
  `<verification_protocol>`, `<package_legitimacy_protocol>`. See §1.8.
- `gsd-codebase-mapper` 853 lines, `tools: Read, Bash, Grep, Glob, Write` — writes its analysis
  documents directly, with the stated reason "to reduce orchestrator context load", and carries
  full output templates (`STACK.md`, `INTEGRATIONS.md`, `ARCHITECTURE.md`) inline. It explicitly
  instructs "Config files (list only — **DO NOT read .env contents**)".
- `gsd-executor` 752 lines; `gsd-planner` 1,278; `gsd-debugger` 1,452.

**(f) superpowers — see §1.7. Its role definitions are the best-written of the lot and are not
agent files at all.**

### 1.6 Good-code / bad-code exemplar practice (AC-4 rule 4)

The strongest documented practice I found is superpowers' `writing-skills` skill — and it is
not merely "show a good and a bad example", it is a *typed* discipline. — RV
(`…\claude-plugins-official\superpowers\6.3.0\skills\writing-skills\SKILL.md`, 679 lines)

Four distinct exemplar forms, each used for a different failure:

1. **`<Bad>` / `<Good>` XML-tagged pairs wrapping fenced code**, used when the rule is about the
   *shape* of a written artifact. The pair is minimal and the Good side is the Bad side plus the
   closed loopholes — e.g. Bad: `Write code before test? Delete it.` / Good: the same line plus
   `**No exceptions:** — Don't keep it as "reference" · Don't "adapt" it while writing tests ·
   Don't look at it · Delete means delete`. — RV (lines 484–504)
2. **Inline `❌ BAD:` / `✅ GOOD:` comment pairs *inside* one code block**, used when the
   contrast is a single line of code and the reader must see them adjacent. In
   `writing-good-tests.md` the pairs are semantic, not stylistic:
   `// ❌ Mirror assertion: the same builder computes both sides — always true` vs
   `// ✅ Hand-derived literal`; `// ❌ Mock existence` vs `// ✅ Real behavior`;
   `// ❌ The mock swallows the config write that duplicate detection reads` vs
   `// ✅ Mock only the slow server startup; the config write stays real`.
   **Each bad exemplar states WHY it is wrong in the comment**, not just that it is. — RV
3. **`| Excuse | Reality |` rationalization tables**, harvested from baseline testing — "Every
   excuse agents make goes in the table" (e.g. *"Too simple to test"* → *"Simple code breaks.
   Test takes 30 seconds."*). — RV (lines 516–526)
4. **Red-flag lists and negative section headers** (`### ❌ Narrative Example`,
   `### ❌ Multi-Language Dilution`, `### ❌ Code in Flowcharts`, `### ❌ Generic Labels`). — RV

Three governing rules stated in the same file, all of which bind how we write AC-4's exemplar
pairs — RV:
- **"One excellent example beats many mediocre ones."** A good example is complete and runnable,
  commented explaining WHY, from a real scenario, ready to adapt — *not* a fill-in-the-blank
  template, *not* implemented in five languages, *not* contrived.
- **"Match the form to the failure."** For *discipline* failures (agent knows the rule, skips it
  under pressure), prohibition-style bulletproofing works. For *shaping* failures (wrong-shaped
  or omitted output), **prohibitions backfire**: in head-to-head wording tests on dispatch-prompt
  guidance, "the prohibition arm produced clearly more of the unwanted content than the recipe
  arm (fully separated distributions), and trended worse than even the no-guidance control."
  Give a recipe, not a "don't". — RV (line 470)
- **Two corollaries that read like bug reports from the field** — RV (lines 473–474): **"No
  nuance clauses"** ("Don't X unless it matters" reopens the negotiation; appending one nuance
  clause degraded a winning recipe from consistent to noisy) and **"Exemption clauses don't
  scope"** ("This limit doesn't apply to code blocks" still suppresses code blocks — restructure
  so the rule cannot reach the exempt part).

Supporting file `persuasion-principles.md` grounds the imperative register in cited research —
Meincke et al. (2025), N=28,000 AI conversations, persuasion techniques more than doubling
compliance (33% → 72%, p < .001) — and maps seven Cialdini principles to skill-writing moves
(Authority → "YOU MUST"/"No exceptions"; Commitment → forced announcements and explicit
choices). — RV. (UA: I have not verified the Meincke citation against the paper itself; I am
reporting that superpowers cites it.)

### 1.7 The superpowers plugin (AC-7) — precise shapes

Version inspected: **6.3.0**, at
`C:\Users\taurr_nvs748q\.claude\plugins\cache\claude-plugins-official\superpowers\6.3.0\`. — RV

**Finding that reshapes AC-7: superpowers ships NO `agents/` directory.** The plugin root
contains `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `gemini-extension.json`, `assets/`, `docs/`,
`hooks/`, `package.json`, `scripts/`, `skills/`, `tests/` — and no `agents/`. — RV (directory
listing). Every role in superpowers is expressed as **a prompt-template markdown file living
beside the skill that dispatches it**, targeted at a *generic* `Subagent (general-purpose)`.

**Skill frontmatter is two fields. That is the whole schema.** All 14 skills carry exactly
`name` and `description`; nothing else — no version, no model, no tools, no allowed-directories.
— RV (frontmatter of all 14 `skills/*/SKILL.md`). Skill body lengths: 63–679 lines (median
~170): `using-superpowers` 63 · `executing-plans` 64 · `requesting-code-review` 95 ·
`verification-before-completion` 120 · `dispatching-parallel-agents` 167 · `using-git-worktrees`
167 · `writing-plans` 171 · `receiving-code-review` 205 · `finishing-a-development-branch` 225 ·
`brainstorming` 250 · `systematic-debugging` 283 · `test-driven-development` 320 ·
`subagent-driven-development` 568 · `writing-skills` 679.

**Description style is a trigger clause, not a summary** — RV: they begin "Use when …" and name
the *moment*, e.g. `verification-before-completion`: "Use when about to claim work is complete,
fixed, or passing, before committing or creating PRs — requires running verification commands
and confirming output before making any success claims; evidence before assertions always."
`writing-skills` states the rule explicitly: descriptions carry **triggering conditions only, no
workflow summary** (❌ BAD: "Summarizes workflow — agents may follow this instead of reading
skill"), never first person, and name the technology only if the skill is technology-specific.

**The four role prompt-templates.** — RV
(`skills/requesting-code-review/code-reviewer.md`;
`skills/subagent-driven-development/{implementer,task-reviewer,re-review}-prompt.md`)

Every one of them opens with a fenced dispatch block naming the target
(`Subagent (general-purpose):`), a `description:`, and — for the three SDD ones —
`model: [MODEL — REQUIRED: choose per SKILL.md Model Selection; **an omitted model silently
inherits the session's most expensive one**]`. Each closes with an explicit
`**Placeholders:**` list marking which are REQUIRED, and a one-line
`**Reviewer returns:** …` contract.

Clauses worth lifting verbatim-in-spirit:

- **`## You Do Not Dispatch Subagents`** — present in *all four* templates, with the economic
  argument spelled out: "This process already provides every review seat the work gets; a
  reviewer you spawn duplicates one of them at full cost, and its verdict counts for nothing."
  The implementer version adds the pre-empted rationalization: "If you catch yourself thinking
  'an independent review would strengthen my report' — that review is already scheduled."
- **`## Do Not Trust the Report`** (task-reviewer) — "Treat the implementer's report as
  unverified claims about the code… Design rationales in the report are claims too: 'left it per
  YAGNI,' 'kept it simple deliberately,' or any other justification is the implementer grading
  their own work. **Judge the code on its merits — a stated rationale never downgrades a
  finding's severity.**" Paired with: "If the plan or brief explicitly mandates something this
  rubric calls a defect… that IS a finding — report it as Important, labeled plan-mandated. **The
  plan's authorship does not grade its own work; the human decides.**"
- **Context-budget discipline as a positive recipe** — "Read the diff file once… The diff's
  context lines ARE the changed files: do not Read a changed file separately unless a hunk you
  must judge is cut off mid-function — and say so in your report. Do not re-run git commands. Do
  not crawl the broader codebase. Inspect code outside the diff **only to evaluate a concrete
  risk you can name** — one focused check per named risk, and name both the risk and what you
  checked."
- **Test economy with an anti-false-negative counterweight** — "Do not re-run the suite to
  confirm their report… Run a test only when reading the code raises a specific doubt that no
  existing run answers." And then, crucially: **"Evidence you cannot see is not evidence that
  doesn't exist. If the report or its test evidence looks truncated… re-read the file at its
  stated path… Re-running the suite to regenerate what you failed to read is not verification;
  illegibility of the evidence is not invalidation of it."**
- **Escalation is pre-authorised, in the implementer** — "`## When You're in Over Your Head` —
  It is always OK to stop and say 'this is too hard for me.' **Bad work is worse than no work.
  You will not be penalized for escalating.**" followed by five observable STOP predicates
  (architectural decisions with multiple valid approaches · needing code beyond what was
  provided · uncertainty about approach · restructuring the plan didn't anticipate · reading
  file after file without progress).
- **A two-tier report contract.** Full detail to `[REPORT_FILE]` (what was implemented, what was
  tested, **explicit RED/GREEN TDD evidence — command, failing output, why the failure was
  expected, then command and passing output**, files changed, self-review findings, concerns);
  the returned message is **"ONLY (under 15 lines — the detail lives in the report file)"**:
  `**Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`, commits (short SHA +
  subject), a one-line test summary, concerns, report path. "Never silently produce work you're
  unsure about."
- **Verdict schemas are enumerated, and the enum has teeth.** Re-reviewer: per finding,
  `ADDRESSED | NOT ADDRESSED` with file:line — **"'Attempted' is not addressed: the specific
  defect must no longer exist."** Task reviewer: `✅ Spec compliant | ❌ Issues found |
  ⚠️ Cannot verify from diff` (the ⚠️ bucket exists precisely so the reviewer *doesn't* broaden
  its search), then Critical / Important / Minor, then `Task quality: Approved | Needs fixes`.
- **A scope fence with a capture valve** — `### Out-of-Scope Observations`: "Issues you noticed
  entirely outside the fix diff. Non-blocking; the controller ledgers these for the final
  review." (This is `kata-defer` by another name.)
- **No preamble** — "Your final message is the report itself: begin directly with the
  spec-compliance verdict. Every line is a verdict, a finding with file:line, or a check you ran
  — no preamble, no process narration, no closing summary."
- **Calibration against severity inflation** — "Important means this task cannot be trusted until
  it is fixed… 'Coverage could be broader' and polish suggestions are Minor" — plus a required
  Strengths section, justified instrumentally: "accurate praise helps the implementer trust the
  rest of the feedback."
- **A bounded fix loop with a named breaker.** Rounds cap at 5; at the cap the controller
  **adjudicates** each open finding into park-with-ruling (reviewer wrong / real-but-inert) or
  rule-the-smallest-unblocking-change, every adjudication a ledger line — "**Adjudicate only at
  the cap. Adjudicating earlier to end a loop is pre-judging with a different name.**" and "a
  silent discard is forbidden." Also: "Never fix findings yourself in the controller session —
  your context stays clean for coordination, and controller fixes skip review." — RV
  (`skills/subagent-driven-development/SKILL.md`)

The plugin also ships `docs/porting-to-a-new-harness.md` and per-harness tool references
(`skills/using-superpowers/references/{hermes,pi,codex,gemini,antigravity}-tools.md`) — RV — i.e.
the pack is deliberately harness-portable, which is the same instinct as our adapter seam.

### 1.8 Research-agent design (AC-9)

**(a) "Karpathy's auto research repo" — identified with high confidence.**
**`github.com/karpathy/autoresearch`** (MIT), released **2026-03-07**; "AI agents running
research on single-GPU nanochat training automatically". — DS (github.com/karpathy/autoresearch
README, fetched 2026-08-16; corroborated by datacamp.com/tutorial/guide-to-autoresearch,
datasciencedojo.com/blog/karpathy-autoresearch-explained,
thenewstack.io/karpathy-autonomous-experiment-loop). I found **no competing candidate** under
Karpathy's GitHub for "auto research"; the identification is DS, not a guess. *(Caveat, labeled:
secondary coverage disagrees on scale — one report says ~700 experiments / ~20 improvements over
two days, another says "50 experiments overnight" from a 630-line script. The loop design below
is from the README and is not affected.)*

Three files, and the split **is** the design — DS (README):
- **`prepare.py`** — fixed constants, one-time data prep, runtime utilities (dataloader,
  evaluation). **"Not modified."**
- **`train.py`** — "the single file the agent edits."
- **`program.md`** — the human-authored instruction contract; Karpathy calls it "essentially a
  super lightweight 'skill'". **Humans iterate on `program.md`; the agent iterates on `train.py`.**

Loop: modify `train.py` → train for exactly **5 minutes wall clock** → evaluate on **validation
bits-per-byte (val_bpb)** → improved? → keep, else discard → repeat. Two anti-gaming devices are
structural, not exhortative: the **fixed time budget** makes experiments comparable regardless of
what the agent changed (model size, batch size, architecture), and **val_bpb is
vocabulary-size-independent** so architectural changes compare fairly. The evaluator lives in the
file the agent may not touch. — DS

**A Claude-Code port of this loop exists locally and its role file is instructive** — RV
(`…\claude-code-skills\engineering-advanced-skills\2.9.0\autoresearch-agent\agents\experiment-runner.md`,
88 lines). Notably it has **no YAML frontmatter at all** — it is a prompt file in an `agents/`
directory (RV), which per §1.4 means it would not register as a Claude Code subagent; treat it
as a template, not a working definition. Its transferable content:
- A **state triple read at the top of every iteration**: `config.cfg` (what to optimize and how
  to measure) · `program.md` (what you can/cannot change, current approach) · `results.tsv`
  (every experiment ever run, with outcomes) — plus `git log --oneline -10`.
- **Evidence-driven strategy selection from the history**, bucketed by `status=keep` / `discard`
  / `crash`, and explicitly asking for trends ("plateauing? accelerating? oscillating?").
- **An escalation ladder indexed on experiment count**: runs 1–5 low-hanging fruit (low risk) ·
  6–15 systematic one-parameter-at-a-time (medium) · 16–30 structural/algorithm swaps (high) ·
  30+ radical (very high). "If no improvement in the last 20 runs… update the Strategy section of
  program.md and try something fundamentally different."
- **Scheduled self-improvement**: "After every 10th experiment, update program.md's Strategy
  section — which approaches consistently work? Double down. Which consistently fail? Stop
  trying." *(This is AC-2's learning channel, expressed as a cadence rule inside the definition.)*
- **Hard Rules** worth stealing wholesale: "**ONE change per experiment.** Multiple changes = you
  won't know what worked." · "**NEVER modify the evaluator.** evaluate.py is the ground truth.
  Modifying it invalidates all comparisons. If you catch yourself doing this, stop immediately."
  · "**5 consecutive crashes → stop.** Alert the user. Don't burn cycles on a broken setup." ·
  "**Simplicity criterion.** …Removing code that gets same results is the best outcome." · "No
  new dependencies." · "Never read or modify files outside the target file and program.md" ·
  "Never push to remote" · "Never skip the evaluation step — every change must be measured."

**(b) Other auto-research / deep-research systems.**

- **`SakanaAI/AI-Scientist-v2`** — a genuine multi-role cast with hard stage boundaries — DS
  (deepwiki.com/SakanaAI/AI-Scientist-v2; github.com/SakanaAI/AI-Scientist-v2): **Ideation
  Agent** (`perform_ideation_temp_free.py` → `ideas.json`) · **Experiment Manager Agent** (drives
  progressive agentic tree search / BFTS) · **Tree-Search Node Agents** (individual experimental
  paths; `bfts_config.yaml` sets `num_workers`, `steps`, `max_debug_depth`) · **Writeup Agent**
  (`perform_writeup.py`) · **Review/Reflection Agent** (`perform_llm_review.py` → `review.json`).
  Every stage boundary is **a named artifact file**, and runs are isolated in timestamped
  directories `experiments/<timestamp>_<ideaname>/`.
  **And the honest counterweight, which matters more than the architecture:** a 2026 evaluation
  (arxiv 2502.14297) found it "superficially automates the research process but fails to perform
  deep literature reviews, robust experiment validation, or quality manuscript production," with
  a **42% experimental failure rate** and manuscripts containing structural errors and misleading
  claims. — DS. **A self-reviewing research pipeline whose reviewer is another instance of itself
  does not produce trustworthy output.** That is direct evidence for keeping our Researcher
  strictly report-only and gating it externally.
- **`assafelovic/gpt-researcher`** — **planner / executor / publisher** split: the Planner
  generates the research questions, execution ("crawler") agents gather per question, the
  Publisher aggregates with source tracking. Deep Research adds a tree with configurable **depth
  and breadth**, explored concurrently. Its stated hallucination control is **multi-source
  corroboration** — scraping many sites per question and preferring the most frequent
  information — with per-resource source tracking across 20+ sources. — DS
  (github.com/assafelovic/gpt-researcher)
- **`langchain-ai/open_deep_research`** — the informative finding is that it **retreated from
  multi-agent**: the current implementation is a **single research agent** with four
  *task-specific model slots* (summarization / research / compression / final-report), and the
  supervisor-researcher multi-agent design plus the plan-and-execute workflow are preserved as
  **legacy alternatives**. — DS (github.com/langchain-ai/open_deep_research). **A team of
  research agents is not automatically better than one agent with tiered model slots** — evidence
  against over-splitting row 10.
- **`gsd-phase-researcher`** (927 lines) is the best *written* researcher role I read, and it is
  local. — RV. Its `<philosophy>` block is three named doctrines: **"Claude's Training as
  Hypothesis"** ("Training data is 6–18 months stale. Treat pre-existing knowledge as hypothesis,
  not fact… 'As of my training' is a warning flag"); **"Honest Reporting"** ("Research value
  comes from accuracy, not completeness theater. 'I couldn't find X' is valuable. 'This is LOW
  confidence' is valuable. 'Sources contradict' is valuable. **Avoid: padding findings, stating
  unverified claims as facts, hiding uncertainty behind confident language**"); and **"Research
  is Investigation, Not Confirmation"** ("Bad research: start with hypothesis, find evidence to
  support it").
  Its machinery: a **tool-priority table with a Trust Level column** (Context7 HIGH → WebFetch
  HIGH-MEDIUM → WebSearch "needs verification"); a **verification protocol that computes the
  label** (verifiable with Context7 → HIGH; with official docs → MEDIUM; multiple sources agree →
  raise one level; none of the above → stays LOW and is flagged) with "**Never present LOW
  confidence findings as authoritative**"; a **source hierarchy** mapping level to permitted
  speech act (HIGH "state as fact" / MEDIUM "state with attribution" / LOW "flag as needing
  validation"); four **Known Pitfalls** with named preventions — Configuration Scope Blindness,
  Deprecated Features, **Negative Claims Without Evidence** ("are you confusing 'didn't find it'
  with 'doesn't exist'?"), Single Source Reliance; a **Pre-Submission Checklist** including
  "Negative claims verified with official docs", "Publication dates checked", "Confidence levels
  assigned honestly", and **"'What might I have missed?' review completed"**; a fixed
  `RESEARCH.md` output skeleton with mandatory `## Assumptions Log`, `## Open Questions`,
  `## Sources`, `## Metadata`; a search-hygiene rule ("**Do not inject a year into queries** — it
  biases results toward stale dated content; check publication dates on the results you read
  instead"); and a **Package Legitimacy Gate** that runs `slopcheck` against every recommended
  package and routes `[SLOP]` → removed entirely, `[SUS]` → kept with an inline warning tag,
  `[OK]` → normal — **with graceful degradation that marks every package `[ASSUMED]` rather than
  `[VERIFIED]` when the tool is unavailable, "never a hard failure."** — RV

### 1.9 BMAD-METHOD — a compile step between source definition and platform format

Surveyed thinly (one search pass, no file reads), but it lands on the one architectural question
AC-1 raises and nothing else in this survey answers. — DS
(deepwiki.com/bmadcode/BMAD-METHOD/8.1-agent-architecture-and-lifecycle;
github.com/bmad-code-org/BMAD-METHOD `docs/agent-customization-guide.md`;
deepwiki.com/bmad-code-org/BMAD-METHOD, all fetched 2026-08-16)

- Agents are **YAML source files** — `src/modules/<module>/agents/<name>.agent.yaml` — carrying a
  `persona` section (role, identity, communication style, guiding principles) plus the agent's
  curated menu of invokable workflows.
- **They are compiled**: v6 agents are "defined in YAML source files (.agent.yaml) and compiled
  into markdown files (.md) for IDE consumption", installed to `_bmad/<module>/agents/`.
- Roles are org-shaped (Product Manager, Architect, Scrum Master, Developer, QA/Analyst), each
  with a workflow menu rather than free-form capability.

**Why it matters to us.** BMAD is the only surveyed system that keeps a **platform-neutral source
definition and renders it into the host's format** — which is exactly the shape AC-1 needs (ours,
rendered by the Claude adapter into `.claude/agents` frontmatter, §1.4) and exactly what
superpowers achieves by a different route (harness-portable prose + per-harness tool reference
files, §1.7). **Two viable architectures, and the choice is a real grill question:** compile
(BMAD — one source of truth, a build step, drift impossible) versus author-portable (superpowers
— no build step, portability by discipline). *(UA: I did not read a single BMAD `.agent.yaml`, so
the field-level schema is doc-sourced summary only — do not cite it as a schema.)*

---

## 2. PATTERNS — the transferable design rules

Twelve rules. Each is traced to the sources that support it; where the field disagrees, the
disagreement is stated rather than averaged away.

**P1 — Definition = frontmatter contract + prose role; the contract carries everything a
machine can enforce.** Pi's schema (§1.3) and Claude Code's (§1.4) converge on this: identity,
capability fence, model, budget, output, gating are *fields*, not sentences. GSD (§1.5e) proves
the failure mode — 33 agents, zero `model`, zero `maxTurns`, zero `disallowedTools`, with all
that discipline written as prose the agent may or may not honour. **Anything a field can enforce
must not be prose.** *(Sources: pi-subagents docs/agents.md DS · code.claude.com/docs/en/sub-agents DS · GSD RV)*

**P2 — Tool restriction is the highest-value and most-violated field. Fence it by role, at
sub-command granularity, and back the allowlist with a denylist.** `karpathy-reviewer` shows the
technique — `Bash(git diff *)`, `Bash(git log *)` not blanket `Bash`, plus an explicit
`disallowedTools` for `rm`/`curl`/`git push`/`git reset --hard` (§1.5b). VoltAgent shows the
anti-pattern: a stated read-only convention and a shipped reviewer with `Write, Edit` (§1.5c).
Hermes restricts by role enum rather than by name (§1.1). Claude Code applies `disallowedTools`
*before* `tools` — so the denylist genuinely wins (§1.4). **A read-only role that can write is
not a read-only role, and our validator must check the frontmatter, not the prose.**
*(Sources: RV karpathy-reviewer · DS VoltAgent · DS sub-agents · DS Hermes delegation)*

**P3 — Name the model tier, never leave it to inherit-by-default.** superpowers writes the
reason into every template: "an omitted model silently inherits the session's most expensive
one" (§1.7). Claude Code's documented default *is* `inherit` (§1.4). wshobson publishes a
four-tier policy (§1.5d); pi-agent-harness demonstrates it concretely (haiku recon / sonnet
work) (§1.3); Pi adds `fallbackModels[]` that fire on quota/auth/timeout **but not on ordinary
task failure** — exactly the distinction our D59 resolver needs so a hard task doesn't silently
tier down. **Our D59 relative-tier declaration is the right abstraction; give it a
fallback-on-unavailability list and forbid a bare omission.**
*(Sources: RV superpowers templates · DS sub-agents · DS wshobson · DS pi-subagents)*

**P4 — Two-tier reporting: a full report to a file, a ≤15-line machine-parseable status to the
caller.** superpowers' implementer contract (§1.7) and Hermes' structured return metadata (§1.1)
land on the same shape from opposite directions. GSD's codebase-mapper states the rationale
outright: the agent writes documents directly "to reduce orchestrator context load" (§1.5e).
**Status must be an enum** — `DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT` — and
DONE_WITH_CONCERNS is what makes "never silently produce work you're unsure about" actionable.
*(Sources: RV superpowers implementer-prompt · DS Hermes delegation · RV gsd-codebase-mapper)*

**P5 — Verdict schemas are enums with anti-hedging clauses attached.** `ADDRESSED | NOT
ADDRESSED` plus "'Attempted' is not addressed: the specific defect must no longer exist";
`✅ compliant | ❌ issues | ⚠️ cannot verify from diff`; severity calibrated with a written
definition of *Important* so it can't inflate (§1.7). feature-dev adds the other half: a
**0–100 confidence rubric with anchored descriptions and a hard ≥80 reporting floor**, which is
the only false-positive control I found in the whole survey (§1.5a). **Our per-finding schema
needs both — a refute-posture floor and a confidence floor.**
*(Sources: RV superpowers task-reviewer/re-review · RV feature-dev code-reviewer)*

**P6 — Distrust of the upstream report is a standing clause, and the rationale is that
self-grading is not evidence.** "Treat the implementer's report as unverified claims… a stated
rationale never downgrades a finding's severity"; "The plan's authorship does not grade its own
work"; Hermes: results "require verification by the parent rather than blind acceptance"
(§1.1, §1.7). **This is PD-2 written as a reviewer instruction, and it must be in-substrate, not
briefed.**
*(Sources: RV superpowers task-reviewer-prompt · DS Hermes delegation-patterns)*

**P7 — Context economy is a positive recipe with a named-risk escape hatch, never a bare
prohibition.** "Read the diff file once… do not crawl the broader codebase… inspect code outside
the diff **only to evaluate a concrete risk you can name** — one focused check per named risk,
and name both the risk and what you checked." Paired with the anti-false-negative counterweight:
"**Evidence you cannot see is not evidence that doesn't exist**… illegibility of the evidence is
not invalidation of it." (§1.7) This form is not stylistic: superpowers' own head-to-head wording
tests found the prohibition arm produced *more* unwanted content than the recipe arm and trended
worse than no guidance at all (§1.6).
*(Sources: RV superpowers task-reviewer-prompt + writing-skills line 470)*

**P8 — Write instructions in the form that matches the failure, and never soften a working
recipe.** Discipline failures (knows the rule, skips under pressure) → prohibitions, closed
loopholes, rationalization tables. Shaping failures (wrong-shaped or omitted output) → recipes.
**"No nuance clauses"** — one appended "unless it matters" degraded a consistent recipe to noisy.
**"Exemption clauses don't scope"** — restructure so the rule cannot reach the exempt part
(§1.6). *(Source: RV superpowers writing-skills)*

**P9 — Exemplar pairs are typed, minimal, and each bad side says WHY.** `<Bad>`/`<Good>` XML for
artifact shape; inline `❌`/`✅` comments *within one code block* for line-level contrasts, with
the failure named in the comment ("Mirror assertion: the same builder computes both sides —
always true"); `| Excuse | Reality |` tables for rationalizations; ❌-prefixed section headers
for anti-patterns. Governed by "one excellent example beats many mediocre ones" — complete,
runnable, commented for WHY, from a real scenario, never a fill-in-the-blank template (§1.6).
**AC-4's good/bad pairs should be built to this typology, and mined from our own live-run
failures rather than invented.** *(Source: RV superpowers writing-skills + writing-good-tests)*

**P10 — Escalation must be pre-authorised in the definition, with observable predicates.** "It is
always OK to stop and say 'this is too hard for me.' Bad work is worse than no work. **You will
not be penalized for escalating**" + five concrete STOP conditions (§1.7). The autoresearch
runner has the mechanical version: "5 consecutive crashes → stop. Alert the user. Don't burn
cycles on a broken setup" (§1.8a). Hermes exposes `max_iterations`, `child_timeout_seconds`; Pi
exposes `turnBudget {maxTurns, graceTurns}`, `timeoutMs`, `toolTimeoutMs`; Claude Code exposes
`maxTurns` (§1.1, §1.3, §1.4). **Pair the prose permission with the budget field — the permission
without the budget is a suggestion, the budget without the permission produces a silent
truncation reported as done (a PD-2 violation by construction).**
*(Sources: RV superpowers implementer-prompt · RV experiment-runner · DS Hermes/Pi/CC schemas)*

**P11 — Structural anti-gaming beats exhortation. Make the ground truth unreachable.** autoresearch
puts the evaluator in the file the agent may not edit and fixes the compute budget so results are
comparable no matter what changed (§1.8a); the ported runner still adds "NEVER modify the
evaluator… if you catch yourself doing this, stop immediately" as belt-and-braces. GSD's
`gsd-verifier` is the same instinct applied to build claims: **three artifact levels (exists /
imported / used-beyond-imports) plus a Level-4 data-flow trace plus an explicit stub scan** —
empty implementations, hardcoded empty data, props with hardcoded empty values, console.log-only
implementations (§1.5e). **That scan is a mechanised PD-1 detector and we should have one.**
*(Sources: DS karpathy/autoresearch README · RV experiment-runner · RV gsd-verifier)*

**P12 — The dispatch graph belongs inside the definition, and nested dispatch is denied by
default.** GSD encodes provenance in every `description` ("Spawned by /gsd:plan-phase
orchestrator") (§1.5e); Claude Code lets the fence be a field — `tools: Agent(worker, researcher)`
— and Hermes/Pi cap depth (`max_spawn_depth`, `maxSubagentDepth`) (§1.1, §1.3, §1.4). superpowers
argues the economics in prose in all four templates: a self-spawned reviewer "duplicates one of
[the review seats] at full cost, and its verdict counts for nothing" (§1.7). **Every non-conductor
agent in our cadre should carry an explicit spawn fence, expressed as a field where the platform
supports one.**
*(Sources: RV GSD descriptions · DS sub-agents · RV superpowers templates)*

**A thirteenth, stated as a warning rather than a rule — length has no consensus and we must
choose deliberately.** The field spans **47 lines** (feature-dev code-reviewer, RV) → **~88**
(experiment-runner, RV) → **~170** (VoltAgent, DS) → **median 335 / max 1,452** (GSD, RV) →
**568–679** for the two heaviest superpowers skills (RV). The compact ones win on maintainability
and on AC-4's "lightweight, never general-purpose blobs"; the long ones win by carrying *output
templates and executable protocols* inline. **The reconcilable reading (UA): keep the agent
definition compact and push protocol/template bulk into referenced skills — which is exactly what
superpowers does by keeping frontmatter to two fields and putting the substance in skills the
role loads.** Our `skills:` frontmatter field is the mechanism; the BL-N16 substrate cap is the
enforcement.

---

## 3. Per-roster-row recommendations

Format: **strongest inspiration (with why)** → **specific elevation the evidence supports**.
Only elevations I can trace to a labeled source are listed; where the draft's stated elevation
is already well-supported I say so instead of padding.

**1 · Conductor.** Strongest source: superpowers' controller discipline — "**Never fix findings
yourself in the controller session — your context stays clean for coordination, and controller
fixes skip review**", plus adjudicate-only-at-the-cap and "a silent discard is forbidden" (RV,
§1.7). Hermes' `role: leaf|orchestrator` shows the fence can be an enum rather than prose (DS).
**Elevations the evidence adds beyond the draft:** (a) make THIN mechanical — the conductor's
definition should carry an explicit *no-authoring, no-fixing* fence expressed in
`disallowedTools` (Edit/Write on gated artifact paths), not a graded-after aspiration; (b) adopt
the **adjudication ledger** — every ruling at a loop cap is a written line, silent discard
forbidden, which is the natural home for AC-1's "records rulings verbatim-with-provenance";
(c) borrow the **named breaker** shape (cap → adjudicate → park-with-ruling / rule-smallest-
unblocking-change) for the truth-serum register.

**2 · Orchestrator (chef/sous-chef).** Strongest source: `pi-agent-harness`'s **six team patterns
mapped onto three delegation modes** (DS, §1.3) — this is the vocabulary BL-N08's redesign needs,
and Producer-Reviewer + Fan-out/Fan-in + Supervisor are precisely our wave/bake shapes. Hermes
supplies the *config surface* a thin orchestrator should assume rather than re-implement:
`max_concurrent_children`, `max_spawn_depth`, `child_timeout_seconds`, `worktree_isolation`
(DS, §1.1). **Elevations:** (a) name the run's team pattern as a declared field on the run
(pipeline / fan-out / expert-pool / producer-reviewer / supervisor / hierarchical) so the
orchestrator definition selects a protocol rather than describing one — this is what makes
"code-seam-backed, never re-implemented in prose" (BL-M33) checkable; (b) take pi's
`_workspace/` **file-based handoff** as the model for board/bake artifacts — inter-agent state
in files, never in the orchestrator's context; (c) Hermes' **durable background delegation
ledger** (Quicksilver, DS §1.2) is the evidence that background dispatch must survive a restart —
our bake management should assume the same.

**3 · Coder.** Strongest source: superpowers `implementer-prompt.md` (RV, §1.7), which is the
single best coding-role definition I read; secondary `gsd-executor` (752 lines, atomic commits +
deviation handling + checkpoint protocol, RV). **Elevations:** (a) **RED/GREEN TDD evidence in
the report is a field, not a habit** — command, failing output, *why the failure was expected*,
then command and passing output; (b) the **status enum with DONE_WITH_CONCERNS** is what converts
"never silently produce work you're unsure about" into something the gate can read — adopt it
verbatim in shape; (c) the **pre-authorised escalation clause with five observable predicates**
plus a `maxTurns`/turn-budget field (P10) — our burn briefs' push-back clause is the same
instinct, and this is its in-substrate form; (d) **"You Do Not Dispatch Subagents"** as a
standing clause with the cost argument stated; (e) for AC-4's GOOD/BAD pairs, build them to the
P9 typology and **mine them from our own live-run failures** (the AC-8 corpus) — inline
❌/✅ pairs with the failure named in the comment beat any invented contrast.

**4 · Validator (adversarial).** Strongest source: superpowers `task-reviewer-prompt.md` (RV) for
posture and scope; `feature-dev:code-reviewer` (RV) for calibration. **Elevations:** (a) adopt
**"Do Not Trust the Report"** and **"the plan's authorship does not grade its own work"**
verbatim-in-spirit — the draft's "reproduce-don't-trust" is the same rule and this is its sharpest
written form; (b) add the **confidence rubric with anchored 0/25/50/75/100 descriptions and a
reporting floor** as the counterweight to refute-posture — the draft has no false-positive
control at all, and this is the gap; (c) make the draft's lens assignment a real **substrate
config field** and pair each lens with its tool fence (P2); (d) the **⚠️ "cannot verify from
diff" bucket** is what stops a scoped validator from crawling — it belongs beside the
confessed-thin-points section the draft already credits; (e) **"Evidence you cannot see is not
evidence that doesn't exist"** — the anti-false-negative clause; (f) tool fence must be
frontmatter-enforced read-only (VoltAgent's failure, §1.5c, is the cautionary tale).

**5 · Evaluator (the gate).** Strongest source: **`gsd-verifier`'s 7-step goal-backward protocol**
(RV, §1.5e) — and this is the row where the survey adds the most. **Elevations:** (a) adopt the
**three artifact levels — exists / imported / used-beyond-imports — plus the Level-4 data-flow
trace**; this is the mechanical form of PD-1's "present-in-the-tree but dead is NOT built" and we
currently assert it in prose only; (b) adopt the **anti-pattern scan** as a named step (empty
implementations, hardcoded empty data, props with hardcoded empty values, console.log-only,
debt-marker comments) — a stub-detector the gate runs rather than reasons about; (c) **Step 0
"check for previous verification"** is a cheap re-entrancy win for repeat gates; (d) keep
default-FAIL and no-write; superpowers corroborates the separation ("controller fixes skip
review").

**6 · Judge (per-item).** Strongest source: superpowers `re-review-prompt.md` (RV) — it *is* a
scoped per-item judge. **Elevations:** (a) the per-finding enum with **"'Attempted' is not
addressed: the specific defect must no longer exist"**; (b) the **Out-of-Scope Observations**
bucket — non-blocking, ledgered, "they never extend the loop" — which is `kata-defer` at
item scope and answers the open question of what a judge does with what it notices; (c) the
**explicit round cap with a breaker** so per-item loops terminate; (d) "Your final message is the
report itself… no preamble, no process narration" — the cheapest possible token discipline for a
"scoped-cheap, minutes" role.

**7 · Advisor.** Strongest source: Hermes' delegation contract (DS, §1.1) — fresh conversation,
"zero knowledge of the parent's history", specialization carried entirely by `goal` + `context`;
this is precisely D167's advisor-executor and it is the field-standard shape. **Elevations:**
(a) Hermes' **structured return metadata** (`status`, `exit_reason`, timeout phase) alongside the
prose answer, so the conductor can route on the machine fields; (b) Pi's `defaultContext:
fresh|fork` makes fresh-vs-fork a *field* — the advisor should declare `fresh` in-substrate
rather than depending on the dispatcher remembering; (c) Hermes' `child_timeout_seconds` +
`timeout_phase` give the burn-02 reach gap a concrete shape: an advisor that fires wherever the
loop runs needs a declared budget and a machine-readable timeout outcome.

**8 · ARBITER.** **No external equivalent found** — the draft's "no external equivalent known
yet (research to confirm)" is **confirmed** by this survey: no harness or collection I read has a
role that arbitrates against a durable decision history. Closest analogues, both partial:
`gsd-doc-synthesizer` (RV, 204 lines) applies **precedence rules, detects cross-ref cycles, and
enforces LOCKED-vs-LOCKED hard-blocks**, emitting three buckets — auto-resolved / competing-
variants / unresolved-blockers; and the gsd-researcher's **source hierarchy mapping evidence
level to permitted speech act** (§1.8b). **Elevations the evidence supports:** (a) adopt the
three-bucket conflict output — it is exactly the shape a vault-grounded arbitration needs; (b)
adopt **LOCKED-vs-LOCKED as a hard block** rather than a judgment call; (c) bind the citation
obligation to a **speech-act table** (cite-and-state-as-fact / state-with-attribution /
flag-as-needing-validation) so "vault-grounded verdict" has a testable form; (d) recency conflict
resolution should reuse the researcher's "prefer current sources, date your knowledge" doctrine.

**9 · Challenger.** Strongest *evidence* (not shape): Hermes MoA's finding that a two-model
preset **outscored either model alone by ~6 points** (DS, §1.1) — the closest thing to empirical
support for BL-N10's different-model ruling that I found; note it measures ensembling, not
cross-examination, so it is **suggestive, not proof** (UA). Shape source: `re-review-prompt.md`'s
per-finding verdicts (RV). **Elevations:** (a) Pi's **`fallbackModels[]`** is the mechanism that
makes "different model" survivable — a different-model default that silently collapses to the
same model when the other is unavailable is a PD-2 hazard, so the substrate needs an ordered
fallback *and* an honest report line when the intended model wasn't used; (b) the coverage attack
on held-lists has a precedent in the researcher's "**What might I have missed?**" mandatory
review step and in "Negative Claims Without Evidence — are you confusing 'didn't find it' with
'doesn't exist'?" (RV, §1.8b) — lift both as standing duties; (c) `CONFIRMED/REFUTED/RESCOPED`
should carry the "'Attempted' is not addressed" clause's equivalent: a REFUTED verdict must name
the specific evidence that refutes, not assert insufficiency.

**10 · Researcher — deepest treatment (AC-9).**

*Strongest sources, in order:* `gsd-phase-researcher` (RV, 927 lines — the best-written research
role in the survey) · `karpathy/autoresearch` + its ported `experiment-runner` (DS + RV — the
hypothesis→probe→record loop) · `gpt-researcher` (DS — planner/executor/publisher and
multi-source corroboration) · `open_deep_research` (DS — the *retreat* from multi-agent) ·
`AI-Scientist-v2` (DS — a full role cast **and** its 42%-failure evaluation).

*Recommended specialist split — 3 specialists + 1 shared substrate, not 4 peers.* The draft
candidates were doc/field · codebase · academic/experiment · triage-scoping. The evidence
supports **collapsing triage-scoping and promoting the shared discipline into a common
substrate**:

| Specialist | Why it splits (evidence) | Distinct fence |
|---|---|---|
| **doc/field researcher** (this report's role) | gsd-phase-researcher's tool-priority + trust-level table exists *because* external-source trust differs in kind from code trust (RV) | `WebSearch, WebFetch, Read, Grep, Glob` — **no Edit/Write outside its one output file**; must emit `## Sources` with URLs |
| **codebase researcher** | `gsd-codebase-mapper` / `gsd-pattern-mapper` are separate agents from `gsd-phase-researcher` in a 33-agent roster that otherwise merges freely (RV); tool fence genuinely differs (no web, plus graph/AST) | `Read, Grep, Glob, Bash(git log *)` + our graph runtime; **"list config files only — DO NOT read .env contents"** (RV, gsd-codebase-mapper) |
| **experiment researcher** (empirical, not "academic") | autoresearch's loop is a *different kind of work*: the evidence is generated, not found, and needs an untouchable evaluator + fixed budget (DS §1.8a) | may write only the target file + its strategy file; **may never modify the evaluator**; needs a results ledger |
| ~~triage-scoping~~ | **Fold in.** `open_deep_research` retreated from supervisor-researcher to one agent with tiered model slots (DS); gpt-researcher's Planner is a *phase* of the same agent, not a separate definition (DS). A fourth seat buys a hand-off cost for work each specialist must do anyway | scoping becomes a **mandatory first section of every research brief**, not an agent |

*Auto-research patterns worth adopting, each traced:*
1. **The three-file separation of powers** — instruction file (human-owned) / work file
   (agent-owned) / evaluator (nobody-owned). — DS (autoresearch README). For us: the brief is
   conductor-owned, the report is researcher-owned, the evidence-label rules are protocol-owned
   and unwritable by the researcher.
2. **One change per probe** — "Multiple changes = you won't know what worked." — RV
   (experiment-runner). For a doc researcher the analogue is one claim per evidence label; for
   the experiment researcher it is literal.
3. **The results ledger as the agent's first read** — `results.tsv` with `keep|discard|crash`
   status, read at the top of every iteration, with a mandated trend read ("plateauing?
   accelerating? oscillating?"). — RV. **This is the concrete form of AC-2's learning channel
   for row 10**, and it is cheaper than a prose learning log because it is tabular.
4. **Risk escalation indexed on attempt count** (1–5 low-hanging → 6–15 one-variable-at-a-time →
   16–30 structural → 30+ radical; no improvement in 20 → rewrite the strategy). — RV. Directly
   portable to a research agent's *search* strategy: cheap lookups first, then targeted fetches,
   then primary-source retrieval, then declare UNKNOWN.
5. **Scheduled self-improvement at a fixed cadence** ("after every 10th experiment, update the
   Strategy section: double down on what works, stop trying what fails"). — RV. This is AC-2's
   learning accrual with a *trigger*, which the draft lacks.
6. **Trust-level tooling + a label-computing verification protocol + a speech-act hierarchy**
   (HIGH state-as-fact / MEDIUM state-with-attribution / LOW flag-for-validation), with "Never
   present LOW confidence findings as authoritative." — RV (gsd-phase-researcher). **This maps
   1:1 onto our RV/DS/UA/UNKNOWN labels and gives them a computation rule rather than a
   convention.**
7. **The four Known Pitfalls with named preventions**, especially **Negative Claims Without
   Evidence** — "are you confusing 'didn't find it' with 'doesn't exist'?" — and the search
   hygiene rule "do not inject a year into queries; check publication dates instead." — RV.
8. **Multi-source corroboration as the hallucination control**, with per-resource source
   tracking. — DS (gpt-researcher). Cheap and directly compatible with our DS label.
9. **The Package Legitimacy Gate pattern, generalised** — run a machine check, route
   `[SLOP]`/`[SUS]`/`[OK]`, and on tool unavailability **downgrade every item to `[ASSUMED]`
   rather than failing**. — RV. The generalisation for us: *when the verification mechanism is
   unavailable, the label degrades — it never silently upgrades.*
10. **A mandatory Pre-Submission Checklist ending in "What might I have missed?"**, plus fixed
    `## Assumptions Log` / `## Open Questions` / `## Sources` sections. — RV. Our
    evidence-labeled reports already do the last part by convention; make it schema.

*The counterweight, and it must be in the definition:* AI-Scientist-v2 pairs a complete research
cast with a **42% experimental failure rate and misleading claims**, judged by an external
evaluation (DS §1.8b). Its reviewer was itself. **The elevation this demands: our Researcher's
"never rules, only reports" fence is not a modesty clause, it is the load-bearing control — and
research output must be gated by a role the researcher does not contain.**

**11 · Design-author / Plan-author.** Strongest sources: `gsd-planner` (1,278 lines) and
`gsd-plan-checker` (978) — note the field puts a **separate checker** on the planner's output,
which the draft does not (RV); `gsd-doc-verifier` (217 lines) "verifies factual claims in
generated docs against the live codebase" and returns structured JSON (RV); superpowers'
`plan-document-reviewer-prompt.md` / `spec-document-reviewer-prompt.md` (RV, present in the
tree). **Elevations:** (a) the draft's "ledger-fidelity self-check before returning" is good but
self-grading — the field's answer is a **separate verifier of factual claims against the tree**,
which is cheap and matches our verify-primitives-before-claiming-reuse lesson; (b) GSD's
`downstream_consumer` XML block, which states *who reads this artifact and what MUST be its first
section* — a strong pattern for artifacts with a fixed consumer; (c) the `[author-proposed]`
label discipline maps onto the speech-act hierarchy (P-rule from §1.8b) — make it computed, not
remembered.

**12 · Learning agent.** Strongest sources: Hermes' staged-write/diff/approve pipeline (already
held, DS) **plus the new native finding** — Claude Code's `memory: user|project|local` with
`~/.claude/agent-memory/<name>/MEMORY.md` and a **200-line injection cap** (DS, §1.4a).
**Elevations, and one is a warning:** (a) the 200-line cap independently corroborates BL-N16's
"append for audit, distill for load" — adopt a comparable explicit cap with a visible fill
percentage; (b) **do not build on the native `memory:` field**: issue #57507 (v2.1.137,
**closed as not-planned**) documents it failing to write when a `tools:` allowlist omits
Write/Edit — and every hardened agent we ship *will* have such an allowlist (P2). Our substrate
must own its own read/write path and treat the native field as, at most, an optional adapter
convenience — labeled UA until we test it ourselves; (c) the autoresearch **fixed-cadence
self-improvement trigger** (every 10th run) gives the learning agent a schedule rather than a
vibe; (d) Pi's `memory: {scope, path}` **silently skips unsafe paths (traversal, symlinks)** —
adopt the field shape, **reject the silent-skip semantics**; ours must fail loudly (PD-2).

**13 · Context-scanner.** Strongest source: `gsd-codebase-mapper` (RV, 853 lines) — and it
answers the draft's open agent-vs-function question with evidence: it is an **agent**, and the
stated reason is context economy — it "writes documents directly to reduce orchestrator context
load". **Elevations:** (a) carry the **output templates inline** (STACK / INTEGRATIONS /
ARCHITECTURE) so the scan produces a fixed schema rather than prose; (b) adopt the explicit
secret-hygiene fence — "config files: **list only — DO NOT read .env contents**" — which our
draft does not mention and which is a real exfiltration surface on an intake scan over an unknown
repo; (c) the draft's "budget exhaustion honesty, partial-map labeling" is well-supported — the
researcher's `[ASSUMED]`-on-degradation pattern (§1.8b item 9) is the mechanism; (d) GSD splits
scanning by **focus area** (tech / arch / quality / concerns) dispatched in parallel — a cheap
way to bound each scan's context, and a better answer to "large-codebase strategy" than one long
pass.

**14 · Cadre specialists + the extracted pack (AC-7).** **The finding that most affects this row:
superpowers 6.3.0 ships no `agents/` directory** (RV, §1.7) — its roles are prompt templates
beside the dispatching skill, aimed at a generic subagent, and its skill frontmatter is
**exactly `name` + `description`**. So "borrows the current superpowers' frontmatter shapes"
means borrowing a deliberately *minimal* schema plus a *trigger-clause* description style — not a
rich one. **Elevations:** (a) borrow the **description-as-trigger-clause** rule and its stated
prohibition (no workflow summary in the description, no first person) — it is what makes
progressive disclosure work; (b) borrow the **`**Placeholders:**` + `**Returns:**` contract block**
that closes every superpowers template — it is the cheapest possible interface documentation and
we should require it on every cadre role; (c) note superpowers is explicitly **harness-portable**
(`docs/porting-to-a-new-harness.md`, per-harness tool reference files for hermes/pi/codex/gemini/
antigravity) — our pack should carry the same shape, which also serves the adapter seam; (d)
vault-residency and the spin-off path have **no precedent in any source surveyed** — Pi's
`memory: {scope: project|user}` and Hermes' `~/.hermes` are the nearest, and neither survives a
reinstall in any documented way (UNKNOWN, carried from RESEARCH-HERMES-PI); (e) plugin-shipped
agents **cannot use `hooks`, `mcpServers`, or `permissionMode`** (DS, §1.4) — if the pack ships as
a plugin, those three enforcement levers are unavailable and the fence must live in
`tools`/`disallowedTools`.

---

## 4. What materially challenges the draft roster

1. **"Hermes / Quicksilver / Pi" is two harnesses, not three** (§1.2). AC-4's alignment triad
   double-counts Nous Research.
2. **Hermes has no agent definitions to align against** (§1.1). It aligns on *dispatch contract*
   and *return metadata*; **Pi is the format anchor**. AC-4's wording should change.
3. **superpowers has no `agents/` directory** (§1.7). AC-7's "borrows the current superpowers'
   frontmatter shapes" borrows a two-field schema and a prompt-template convention — the roster
   should say so, or the elevation reads as bigger than it is.
4. **Claude Code already ships per-agent memory — and it is documented-but-flaky** (§1.4a). BL-N16
   must own its own path; issue #57507 is closed as not-planned and the failure mode
   (allowlist suppresses the auto-enabled Write/Edit) hits precisely the hardened agents we intend
   to ship.
5. **The draft has no false-positive control anywhere in the Validator/Challenger/Judge rows.**
   Every adversarial elevation listed sharpens refute-posture; nothing bounds it. feature-dev's
   anchored confidence rubric with a ≥80 floor is the missing counterweight (§1.5a).
6. **Row 10's four-way split is probably one seat too many** (§3.10). `open_deep_research`
   retreated from multi-agent to a single agent with tiered model slots; gpt-researcher's planner
   is a phase, not an agent. Fold triage-scoping into a mandatory brief section.
7. **A research cast with a self-contained reviewer produced a 42% failure rate and misleading
   claims** (§1.8b). This is the strongest external evidence for our external-gate doctrine — and
   a warning against letting row 10 grow verdict powers.
8. **High-star agent collections are weak evidence of discipline** (§1.5c). VoltAgent publishes a
   read-only-reviewer convention and ships a reviewer with `Write, Edit`. Any "aligned against the
   ecosystem" claim in the roster should cite a *file we read*, not a repo's stated conventions.
9. **GSD is a strong content source and a weak schema source** (§1.5e): 33 agents, zero `model`,
   zero `maxTurns`, zero `disallowedTools`. Borrow its protocols; do not borrow its frontmatter.
10. **The roster has no length or budget policy**, and the field spans 47 → 1,452 lines with no
    consensus (§2, rule 13). AC-4's "lightweight" needs a number and a stated
    push-bulk-into-skills rule, or it will be graded by taste.
11. **The roster never decides whether our definitions are compiled or authored-portable**
    (§1.9). BMAD compiles YAML source → per-IDE markdown; superpowers ships portable prose plus
    per-harness tool references. The cross-cutting elevation says "loaded via the dispatch seam
    ONLY" — which is a *loading* rule and leaves the *authoring/rendering* question open. This is
    a prerequisite decision for AC-1, not a detail.

---

## 5. UNKNOWNS — honestly unresolved

- **Whether the operator's "Quicksilver" means Hermes v0.19.** I identified Quicksilver as the
  Hermes v0.19 codename with DS evidence and found no other harness by that name, but I cannot
  know the operator's referent. **Ask, don't assume.**
- **`wshobson/agents` per-file structure and length.** Only the four-tier model policy is DS; my
  attempt to fetch an individual agent body 404'd. The repo's frontmatter schema and body
  conventions are UNKNOWN to me.
- **Whether Claude Code tolerates unknown frontmatter keys.** `karpathy-reviewer` ships `domain:`
  and `context:` (RV) which are absent from the documented schema (DS). Whether these are ignored,
  warned, or silently meaningful is UNKNOWN — do not rely on custom keys without testing.
- **The real state of native `memory:`.** Issue #57507 is closed as not-planned with root cause
  "unclear" (DS). Whether it works on our current version, and whether the allowlist interaction
  is the real mechanism, is UNKNOWN until we test it ourselves.
- **Hermes per-subagent persistent memory** — still UNDOCUMENTED (carried unchanged from
  RESEARCH-HERMES-PI).
- **Reinstall/vault survival of agent definitions on every harness surveyed.** Hermes
  (`~/.hermes`), Pi (`~/.pi/agent`), Claude Code (`~/.claude/agents`) — none documents reinstall
  behaviour. Row 14's "persist across reinstalls" has **no prior art** to copy.
- **Whether any harness supports learning-derived specialist spin-off.** I found none. This
  remains genuinely novel (consistent with RESEARCH-HERMES-PI §4) — which also means **no external
  design to de-risk against**.
- **The Meincke et al. (2025) persuasion figures** (33% → 72%, N=28,000) are reported *as cited by
  superpowers* (RV). I did not verify them against the paper. UA.
- **autoresearch's experiment counts.** Secondary coverage disagrees (~700 experiments/~20
  improvements over two days vs. "50 overnight" from a 630-line script). The loop design is DS
  from the README; the throughput numbers are contested and should not be quoted as fact.
- **BMAD's actual field schema.** §1.9 is a single doc-sourced pass with **no file reads** — I
  know it uses `.agent.yaml` with a `persona` section and compiles to `.md`, and I do **not** know
  its field names, required/optional status, tool or model handling. Treat §1.9 as an
  architecture finding, not a schema.
- **Whether a compile step or author-portability is right for our cadre** (§1.9) — a genuine open
  design fork with one exemplar on each side and no evidence I found comparing them.
