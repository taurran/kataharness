---
title: "Multi-Model & Cross-Tool Orchestration — deep research + proposed architecture"
status: RESEARCH (2026-06-26) — grounds the eventual grill; NOT frozen
spec: multi-model-orchestration
method: 5 parallel cited research agents (Codex · Kiro · Copilot+Cursor · Anthropic/Hermes patterns · cross-framework routing)
relates: capability-aware-assignment (specialist axis) · install-portability (the install substrate, D104) · kata-orient (the handoff/orientation seam) · kata-orchestrate (the plan-guardian)
---

# Multi-Model & Cross-Tool Orchestration — RESEARCH + PROPOSED ARCHITECTURE

> **Operator vision (2026-06-26):** install KataHarness on the machine + on all the models; confirm; then
> **initialize and execute loop processes assigned to the various agents within the loop** — e.g. **Claude = coder,
> Codex = validator, Kiro = researcher.** Group subagents by **task type** behind an abstraction that binds a
> broad agent/skill group to a designated platform/model (validator group = grounding + anti-slop + red-team;
> coder group = TDD build; researcher group; orchestrator). The orchestrator stays the central source of truth;
> eventually orchestration itself can be delegated (Quick → Kiro/Codex).

---

## 0. The two headline findings (these change the design)

1. **The Agent-Skills `SKILL.md` standard is now SHARED across Claude, Codex, Kiro, Copilot, and Cursor.** All five
   auto-discover skills from `.agents/skills/` and/or `.claude/skills/` (Cursor + Copilot explicitly read
   `.claude/skills/` for cross-tool reuse; Codex/Kiro use the same open SKILL.md format). **One skill payload
   targets every platform** — KataHarness's existing SKILL.md files are already the lingua franca. The only
   adaptation is the **flat-link** (each `<name>/SKILL.md` flat in the discovery dir), which the install-portability
   installer (D104) *already does* — so it generalizes to all platforms by pointing at `.agents/skills/`.
2. **Every target platform is automatable headless today** (Kiro was the open risk — resolved). Each exposes a
   one-shot CLI that runs a task in a directory and returns output, so each can be a **single-role worker**:

| Platform | Skills install dir | Headless one-shot dispatch | Per-call model | Structured result | MCP / ACP |
|---|---|---|---|---|---|
| **Claude** (host) | `~/.claude/skills/` (flat) — D104 | Agent tool / SDK subagents (`model` field) | yes (`model`) | native (schema) | MCP client/server |
| **Codex** | `.agents/skills/` (⚠ legacy `~/.codex/skills`) | `codex exec --cd <wt> --sandbox <ro\|ww> --model M --output-schema v.json -o out` | yes (`--model`) | **yes** (`--output-schema`) ⚠ buggy w/ MCP active | MCP client **+ `codex mcp-server`**; no ACP |
| **Kiro** | `.kiro/skills/` or `~/.kiro/skills/` (SKILL.md) | `kiro-cli chat --no-interactive --agent <role> --trust-tools=…` | via agent JSON `model` | **gap** (plain stdout) → use **ACP** | MCP client **+ `kiro-cli acp`** (JSON-RPC/stdio) |
| **Copilot** | `.github/skills/` or `.claude/skills/` | `copilot -p "<role+task>" -s --allow-all-tools --no-ask-user --model M` | yes (`--model`) | text (cloud agent → PR) | MCP (3 schemas); cloud REST |
| **Cursor** | `.cursor/skills/` or `.claude/skills/` | `agent -p --force --output-format json --model M "<task>"` | yes (`--model`) | **yes** (`--output-format json`) | MCP (`.cursor/mcp.json`); cloud REST |

Caveats to verify before depending: Codex `.agents/skills` vs `~/.codex/skills` split + `--json/--output-schema`
silently dropped when MCP active (codex#15451); Kiro headless has **no documented JSON output** (route structured
results through `kiro-cli acp`); Kiro headless needs a **paid tier + `KIRO_API_KEY`** and pre-trusted tools; Cursor
CLI is **beta** (binary `agent` vs `cursor-agent`; `--model` flag) — all point-in-time June-2026 snapshots.

---

## 1. Per-platform detail (cited)

### Codex (best-fit worker)
- **Skills:** native Agent Skills (`<name>/SKILL.md`, `name`+`description` frontmatter). Discovery: repo `.agents/skills/`
  → `$HOME/.agents/skills` → `/etc/codex/skills` → built-in. ⚠ some installer versions still default to
  `~/.codex/skills`; install to both / verify CLI version. [developers.openai.com/codex/skills]
- **Role injection:** worktree `AGENTS.md` (auto-merged, closest-wins) + explicit `$skill` invocation.
- **Headless:** `codex exec` — `--output-schema` (JSON-Schema-constrained verdict), `-o` (final message to file),
  `--json` (event stream), `--cd`, `--sandbox read-only|workspace-write`, `--model`, `approval_policy="never"`,
  `--ephemeral`/`--ignore-user-config`/`--ignore-rules` (hermetic). SDK `@openai/codex-sdk` `thread.run(p,{outputSchema})`.
- **Drive from a non-Node orchestrator:** `codex mcp-server` exposes `codex`/`codex-reply` tools over stdio. No ACP.

### Kiro (CLI, NOT the IDE)
- **Skills:** native Agent Skills (`.kiro/skills/<name>/SKILL.md`); also steering (`.kiro/steering/*.md`, front-matter
  inclusion modes) + specs (`.kiro/specs/` requirements/design/tasks — near-1:1 with KataHarness's spec model). [kiro.dev/docs/cli/skills]
- **Custom agents = role definitions:** JSON in `.kiro/agents/<role>.json` — `prompt` (role system prompt, inline or
  `file://`), `model`, `tools`/`allowedTools`, `mcpServers`, `resources` (pull skills via `skill://…`, steering via `file://…`).
- **Headless:** `kiro-cli chat --no-interactive --agent <role> --trust-tools=read,grep "<task>"` → text on stdout, exit.
  **Structured-output gap → use `kiro-cli acp`** (JSON-RPC 2.0 over stdio) for parseable results/turn events.
- **Models:** Claude-only (Sonnet/Opus/Haiku + Auto), set in the agent JSON `model` (not a CLI flag).

### Copilot (bonus)
- **Skills:** Agent Skills (`.github/skills/` / `.claude/skills/` / `~/.copilot/skills/`), auto-loaded by description.
  Also `.github/copilot-instructions.md`, `AGENTS.md` (root=primary, nested), `.github/instructions/*.instructions.md` (`applyTo`).
- **Headless:** new agentic CLI `@github/copilot`: `copilot -p "<role+task>" -s --allow-all-tools --no-ask-user --model M`.
  Cloud coding agent: `POST /agents/repos/{o}/{r}/tasks` → opens a PR (needs user-to-server token; preview).

### Cursor (bonus)
- **Skills:** `.cursor/skills/<name>/SKILL.md` (+ reads `.claude/skills/`), `paths` scoping. Rules `.cursor/rules/*.mdc`.
- **Headless:** CLI (beta) `agent -p --force --output-format json --model M "<task>"` → structured JSON
  (`result`, `session_id`, `is_error`…). Cloud agents `POST /v1/agents` → PR.

---

## 2. Multi-model role-routing patterns (Anthropic · Hermes · frameworks)

**Anthropic — the conceptual + production blueprint**
- Four workflows map onto the vision: **orchestrator-workers** (lead decomposes, workers execute, lead synthesizes);
  **routing** (classify → specialized model; their example: Haiku for simple, Sonnet for complex = *the* role→model
  primitive); **evaluator-optimizer** (one model generates, *another* evaluates in a loop = the **validator role**);
  prompt-chaining (durable handoff). "Add multi-agent only when simpler fails."
- Multi-agent research system: **Opus lead + Sonnet subagents beat single-Opus by 90.2%.** Lessons: each subagent
  needs a **full task contract** (objective, output format, tool/source guidance, boundaries — nothing is inherited);
  **scale effort explicitly** (heuristics cap spawning); **context compression by isolation**; **plan saved to durable
  memory**; **artifact/filesystem handoff (pass pointers, not payloads)**; **LLM-as-judge with a 0-1 + pass/fail rubric**.
- ⚠ **Coding (interdependent) parallelizes badly** — keep the **coder a single sustained agent**; fan out the
  loosely-coupled roles (research, validation). Multi-agent ≈ **15× tokens**; spawn count dominates cost.
- **Claude Code/SDK subagents** already take a per-role `model` (`sonnet|opus|haiku|fable|<id>|inherit`), `tools`,
  `description` (routing key), `permissionMode`, `skills`, `memory`, `isolation: worktree`, resume-by-ID. **But native
  routing is Claude-only** → a non-Claude role must be bridged (MCP server / CLI / external process over the shared FS).

**Hermes (Nous Research) — validates KataHarness's own seams**
- **Three-tier prompt assembly `stable → context → volatile`** = *exactly* `kata-orient`'s three-tier orientation
  (stable identity/tools → project/caller context → memory/profile/timestamp), for the same reason: prefix-cache
  friendliness + deterministic, auditable priming. Delegated children get a **leaner** identity + the task contract.
- **Session lineage on compression** (branch a child session seeded by a summary; record parent→child) = an adoptable
  upgrade to handoff/compaction. Role→model routing in Hermes is **integrator-supplied**, not first-class (gap).

**Cross-framework (OpenAI Agents SDK · CrewAI · LangGraph · AutoGen/Magentic-One)**
- **Per-role model:** all bind a model at the role boundary via a LiteLLM-style adapter (OpenAI `LitellmModel`, CrewAI
  `LLM("provider/model")`, LangGraph per-node model, AutoGen per-agent `model_client`). Keep a **role→model map in config**.
- **Handoff-as-tool-call:** transfer is an explicit named action (`transfer_to_validator`, `create_handoff_tool`,
  CrewAI "delegate to coworker") with a **structured payload + input filter** (don't dump raw history).
- **Magentic-One dual ledger:** orchestrator keeps a **Task Ledger** (facts/plan/assumptions) + **Progress Ledger**
  (per-step status + next-owner); on stall, rewrite the Task Ledger and re-plan. Portable to a file board → resumable.
- **Supervisor/hierarchical routing** beats free-for-all group chat (cheaper, deterministic, auditable).

**Cross-tool transport (ACP vs MCP vs A2A vs filesystem)**
- **Filesystem/git = the authoritative cross-host substrate.** Durable, audit-trail, stateless restartable workers,
  spans hosts via shared FS / git remote with no always-on broker — **already KataHarness's model.** Weakness:
  concurrent writes → mitigate with single-writer-per-artifact + atomic rename + **worktree-per-worker**.
- **MCP = the uniform tool layer** (give every heterogeneous worker the same filesystem/tool access). NOT agent-to-agent.
- **ACP (Zed's Agent Client Protocol)** = the one protocol built for "orchestrator in tool A live-drives a worker
  agent in tool B's process" (stdio JSON-RPC: `session/new` w/ `cwd`+`mcpServers`, `session/prompt`, streamed
  `session/update`, `session/request_permission`). **Kiro speaks it** (`kiro-cli acp`). But it's **stdio/local + pre-1.0**
  → use locally, not as the cross-host backbone. **A2A** = cross-host peer delegation (heavier than needed now).

---

## 3. PROPOSED ARCHITECTURE for KataHarness (brainstorm, grounded)

**The strategy: KataHarness already has the hard parts.** The lift is a thin routing + dispatch layer over them, not
a new orchestrator. What we already own that this design leans on:
- **File-based board/state/handoff** = the blackboard substrate + cross-host rendezvous (the research's #1 recommendation).
- **`kata-orient` three-tier orientation** = the Hermes-validated priming bundle that makes a cross-model handoff lossless.
- **`kata-orchestrate` as plan-guardian** = the single source of truth (the supervisor/lead).
- **git worktrees per worker** = the isolation that fixes the blackboard's only weakness.
- **`kata-graph` + install-portability** = the detection substrate (for the capability-aware specialist axis).

### 3.1 The role-group abstraction (the operator's "categorize broad strokes into a platform")
Define a small set of **ROLE GROUPS** keyed to the existing loop-phase skill categories, each bound to a platform+model:

| Role group | Owns (skill categories / skills) | Default platform (example) |
|---|---|---|
| **coder** | `execute/` (kata-tdd), the build | Claude (single sustained agent — coding parallelizes poorly) |
| **validator** | `evaluate/` (kata-evaluate, kata-slop-check, kata-review/red-team) + grounding gate | Codex (cheap, structured `--output-schema` verdict) |
| **researcher** | `plan/kata-research`, comprehension | Kiro / Copilot / Cursor (fan-out friendly) |
| **orchestrator** | `coordinate/` (kata-orchestrate, kata-loop) | where init runs (Claude for v1; delegable later) |

This is a **`roles` registry** = `role → { platform, model, owns: [skill-categories] }`, living in the workspace
binding (`.kata-binding.json`) and/or `kata.config` as a `routing`/`roles` block. **Default = single-host** (today's
Claude-only path is the degenerate case: every role → Claude). Decouple `model`/`platform` from role logic so you can
re-pin without touching skills (Anthropic `CLAUDE_CODE_SUBAGENT_MODEL` + SDK-factory pattern).

### 3.2 The dispatch abstraction (the cross-model worker call)
Today `kata-orchestrate` dispatches a Claude subagent (`Agent(model: sonnet)`). Generalize dispatch to a
**per-platform adapter** with one contract:
`dispatch(role, taskContract, worktree) → structuredResult`, implemented per platform by its headless CLI:
- Claude → Agent tool / SDK subagent.
- Codex → `codex exec --cd <wt> --sandbox … --output-schema verdict.json -o out`.
- Kiro → `kiro-cli chat --no-interactive --agent <role>` (or `kiro-cli acp` for structured).
- Copilot → `copilot -p … --allow-all-tools`. Cursor → `agent -p --output-format json`.
The **task contract** = what `kata-orient` already assembles (objective + output format + tool/source guidance +
boundaries), written as a durable handoff doc into the worktree — the cross-model interop seam. Result comes back as a
structured artifact on the shared FS (each platform's structured-output flag, or ACP for Kiro). **This reuses the
existing handoff/board/worktree machinery; only the launch + result-capture per platform is new.**

### 3.3 Orchestrator-as-central (refine, don't replace)
The orchestrator stays the plan-guardian and never drifts (spine #1). Adopt the **dual-ledger** discipline
(Task Ledger = the frozen plan + assumptions; Progress Ledger = the board's per-task status + next-owner) so the
orchestrator can supervise heterogeneous workers it can't directly spawn by **polling the board** (the research's
cross-host pattern) rather than holding live handles. For the *later* "orchestrator runs in Quick/Kiro/Codex"
evolution: the orchestrator is itself a role group whose platform is configurable — but **v1 keeps it on the init
host** and routes only workers cross-platform (lower risk, still delivers the vision).

### 3.4 Install + confirm (extends D104)
- **Install on all platforms:** extend `kata_install.py` dispatch (already per-platform) to flat-link skills into each
  platform's discovery dir (`.agents/skills/` is the cross-tool standard; per-platform fallbacks per §1). Already 80% built.
- **Confirm step:** a per-platform **readiness probe** — install a tiny sentinel skill + run the platform's headless
  CLI to confirm it (a) discovered the skill and (b) returned a parseable result. This is the "once it's confirmed"
  gate before the orchestrator routes a role to that platform. (Ties to `kata-readiness` / `kata-preflight`.)

---

## 4. The lift (what's missing) + candidate build slices
1. **`roles` routing config** — schema in `.kata-binding.json`/`kata.config` (`role → {platform, model, owns}`); default single-host (BC).
2. **Per-platform dispatch adapters** — `dispatch(role, contract, worktree) → result` for Codex/Kiro/(Copilot/Cursor); Claude already exists.
3. **Task-contract handoff doc** — formalize what `kata-orient` writes for a cross-model dispatch (it largely exists; needs an output-format/result-schema field).
4. **Structured result capture** — per platform (`--output-schema`/`--output-format json`/ACP); a normalizer to one verdict/result shape.
5. **Confirm/readiness probe per platform** — the sentinel-skill check.
6. **Dual-ledger orchestrator refinement** — Progress Ledger = board; supervise-by-polling for non-spawnable workers.
7. **(Later) orchestrator-location config** — run the orchestrator role on a non-init host (Quick→Kiro/Codex).

## 5. Open decisions for the grill
- **Routing granularity:** role-group (coarse, recommended v1) vs per-skill vs per-task. How does it compose with
  `capability-aware-assignment` (the language-specialist axis)? — likely **two orthogonal layers** (platform/model ×
  specialist-profile) that multiply.
- **Where the `roles` block lives** — binding vs kata.config (durable identity vs per-run); how a run overrides.
- **Result transport per platform** — standardize on structured-output flags where they exist; **Kiro → ACP** (its
  headless lacks JSON). Is ACP worth a local adapter, or parse text + exit codes for v1?
- **Supervision of non-spawnable workers** — poll-the-board (FS, recommended) vs a live ACP control channel.
- **Determinism across heterogeneous models** — `skillVersions`/effort/seed capture; how to keep runs comparable
  (ties to `kata-loop-benchmark`, the keystone that measures whether routing pays off).
- **Failure/fallback** — a routed platform unavailable/unconfirmed → fall back to the host (Claude) for that role? (BC-safe default.)
- **Cost/effort governance** — Anthropic's 15× token warning + explicit effort-scaling heuristics in the orchestrator.

## 6. Honest caveats (carry into the grill)
- Cross-vendor routing is **native to no single tool** — KataHarness's FS-handoff substrate is the genuine enabler
  (a real strength), but each non-Claude worker call is a CLI/ACP bridge we own + must keep version-current.
- **Coding parallelizes poorly** (Anthropic) → the coder role stays one sustained agent; fan-out is for validation/research.
- Platform surfaces churn fast (Cursor CLI beta; Codex skills-dir split; Kiro JSON-output gap; Copilot rename
  `mode→agent`). Pin/verify per platform at build; the `confirm` probe is the standing guard.
- This is a **decent lift** (the operator's words) — sequence it: install+confirm-all-platforms first (extends D104),
  then the roles config + one non-Claude dispatch adapter (Codex validator = highest-value first), then generalize.
