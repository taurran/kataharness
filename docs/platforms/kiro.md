# Kiro — recommended context-autonomy config

> **Docs-only in v0.2.1 — no non-Claude code legs (CA-L39).** This page states the recommended
> degradation posture for driving Kiro (AWS agentic IDE + Kiro CLI) under KataHarness. There is **no
> live Kiro leg** in v0.2.1: Claude Code is the only platform with shipped context-autonomy machinery.
> Everything below is a *build reference* for a future Kiro adapter, sourced verbatim from
> `RESEARCH-CROSS-PLATFORM.md`. Every load-bearing claim carries its citation and verification verdict;
> `UNVERIFIABLE` items stay flagged and ride the **Re-verify before build** section.

## The §5 degradation row (frozen)

| Field | Value |
|---|---|
| **Gauge for kata** | **NO** (interactive `/context show` + IDE meter only) |
| **Host knob** | CLI retention knobs only; **no trigger-threshold knob**; IDE ~80% fixed |
| **Resume primitive** | `/chat resume` (compaction spawns a new session) |
| **v0.2.1 kata policy** | **Deterministic-rotation-only.** Hook-enabled configs are higher-risk (issue #5527 auto-compact hard-fail loop, unconfirmed); headless compaction behavior docs-silent — flag in docs. |

## The knob to set

Kiro has **two distinct compaction surfaces** — one in the IDE chat panel, one in the CLI — with
different configurability.

- **IDE auto-summarization (chat panel).** Auto-summarizes prior messages once usage nears the model's
  context limit. **NO KNOB EXISTS** — not user-configurable per official docs; no setting, env var, or
  flag for the threshold or behavior. Trigger ~80% of the active model's context window (percent,
  model-dependent); context *files* are separately capped at 75% of the window, with excess
  auto-dropped. [official-docs — kiro.dev/docs/chat/summarization/ — **CONFIRMED**]
- **CLI conversation compaction.** Summarizes older turns while retaining recent ones; fires
  automatically on context-window overflow, or manually via `/compact`. Retention knobs:
  - `chat.disableAutoCompaction` — boolean; default presumed `false`/enabled (not published); set via
    `kiro-cli settings chat.disableAutoCompaction <value>` → writes `~/.kiro/settings/cli.json`.
  - `compaction.excludeMessages` — unit: message pairs; docs example value `2`;
    `kiro-cli settings compaction.excludeMessages <N>`.
  - `compaction.excludeContextWindowPercent` — unit: percent of context window; docs example value `2`;
    `kiro-cli settings compaction.excludeContextWindowPercent <N>`.
  - Both retention knobs are evaluated each run and "the more conservative (larger) value wins."
  - **FLAG (UNVERIFIABLE):** the `2`/`2` values are illustrative in the settings-command docs; no
    standalone `default:` label was stated — treat as presumptive, not certified. [official-docs —
    kiro.dev/docs/cli/reference/settings/ + kiro.dev/docs/cli/chat/context/]
  - **Session model:** compaction creates a **new** session (summary-seeded); the original
    pre-compaction session is preserved and reopened via `/chat resume`. [official-docs —
    kiro.dev/docs/cli/chat/context/ — **CONFIRMED**]

## The gauge channel (if any)

**Interactive/human-facing only — no machine-readable channel.**

- IDE chat-panel live context-usage percentage meter (passive display, not pollable). [official-docs —
  **CONFIRMED**]
- CLI `/context show` — prints a percentage breakdown by category plus glob patterns for bloated
  entries; interactive slash command only. [official-docs — kiro.dev/docs/cli/chat/context/ —
  **CONFIRMED**]
- **No statusline hook, no JSON/log artifact, no programmatic API** for a supervising process to read
  utilization out-of-band during a headless `--no-interactive` run — verified as an *absence* across the
  cited official pages. [**CONFIRMED**]

Consequence: an orchestrator driving Kiro headlessly **cannot observe approaching exhaustion out-of-band**
→ kata must **track its own approaching-context risk independently** (deterministic rotation /
token-accounting on its side).

## The resume primitive

`/chat resume` reopens the preserved pre-compaction session (compaction spawns a new summary-seeded
session, leaving the original intact). [official-docs — kiro.dev/docs/cli/chat/context/ — **CONFIRMED**]

Headless mode exists: `kiro-cli chat --no-interactive "<prompt>" --trust-all-tools`, auth via
`KIRO_API_KEY` (introduced CLI 2.0). Documented exit codes: 0 success / 1 general / 3 MCP-startup —
**none context/token-limit specific.** [official-docs — kiro.dev/docs/cli/headless/ — **CONFIRMED**]

## Must-guard risks

- **Hook-config auto-compact hard-fail loop.** With `agentSpawn`/`userPromptSubmit` hooks active in CLI
  v1.25.0, the auto-compaction trigger **fails to fire** near 100% context; Kiro sends an oversized
  request and gets `ValidationException: Improperly formed request`, and every subsequent message fails
  identically until a manual `/compact` — which is exactly what's unavailable unattended. [issue-tracker
  — github.com/kirodotdev/Kiro/issues/5527, label `pending-maintainer-response` — **CONFIRMED** as a
  faithful characterization of an open report]
- **Task-state loss across the session boundary.** Even when 80% auto-summarization fires correctly, the
  agent can mark a task complete before finishing its summary, so the new post-compaction session loses
  visibility into the prior task's true state and starts the next task on stale assumptions. [issue-tracker
  — github.com/kirodotdev/Kiro/issues/4976, Open — **CONFIRMED**]
- **Compaction is real but not a safety net for an 8-hr run.** Treat Kiro as
  **deterministic-rotation-only** (no live gauge), and treat hook-enabled configs as higher-risk /
  requiring proactive manual-compact scheduling around ~70–80% if kata can estimate usage.

## Re-verify before build

The RESEARCH doc's Confidence-Gap items for Kiro ride here as re-verify-before-build flags. Do **not**
hard-code any of these into kata logic without first confirming against a live install:

1. **Kiro CLI compaction defaults (`excludeMessages`/`excludeContextWindowPercent` = 2).** Docs show
   `2`/`2` only as illustrative example values; no standalone `default:` label. → Run `kiro-cli settings`
   on a live install to read actual defaults. [UNVERIFIABLE]
2. **Kiro headless compaction behavior.** The official headless-mode doc is entirely silent on
   whether/how compaction runs inside a single `--no-interactive` invocation, and whether one run can
   span multiple internal compactions. → Empirically drive a long headless Kiro run to observe.
   [docs-silent]
3. **#5527 severity for kata's hook usage.** Community-reported, not maintainer-confirmed. If kata
   registers `agentSpawn`/`userPromptSubmit` hooks, verify whether the auto-compact bypass reproduces on
   the current CLI version. [issue-tracker, unconfirmed by maintainer]

---

**Portable-architecture conclusion (SR-6):** 3 of 5 non-Claude platforms have no host knob and/or no
gauge, so **internal-threshold-primary is the only portable architecture** — kata's own threshold
tracking, not the host's compaction, is the load-bearing mechanism on Kiro.
