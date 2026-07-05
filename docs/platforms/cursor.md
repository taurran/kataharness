# Cursor — recommended context-autonomy config

> **Docs-only in v0.2.1 — no non-Claude code legs (CA-L39).** This page states the recommended
> degradation posture for driving Cursor (IDE Agent + Cursor CLI / cursor-agent, incl. Cloud/Background
> Agents) under KataHarness. There is **no live Cursor leg** in v0.2.1: Claude Code is the only platform
> with shipped context-autonomy machinery. Everything below is a *build reference* for a future Cursor
> adapter, sourced verbatim from `RESEARCH-CROSS-PLATFORM.md`. Every load-bearing claim carries its
> citation and verification verdict; `UNVERIFIABLE` items stay flagged and ride the **Re-verify before
> build** section.

## The §5 degradation row (frozen)

| Field | Value |
|---|---|
| **Gauge for kata** | **NO** (no documented context-% surface anywhere) |
| **Host knob** | **NO KNOB** (silent auto-summarize; manual `/summarize` only) |
| **Resume primitive** | `--resume`/`--continue`; Cloud Agents (architectural long-run) |
| **v0.2.1 kata policy** | **Deterministic-rotation-only** + resume checkpoint-restart + hang watchdog (headless exhaustion behavior undocumented). For real long autonomy, prefer the Cloud-Agents scoped-task pattern. |

## The knob to set

**Automatic context-window summarization ("self-summarization").** When an Agent/Composer session nears
the window limit, Cursor pauses, generates a condensed summary, and resumes with the summary substituted
for full history — Cursor's **only** built-in compaction mechanism. [official-docs —
docs.cursor.com/context/management (now 308-redirects; verified via cache + corroborating official blog
cursor.com/blog/self-summarization + cursor.com/learn/context)]

- **Knob:** **NO KNOB EXISTS.** Fires automatically and silently — no flag, env var, or
  `settings.json`/`cli-config.json` key. The only user control is reactive: manual `/summarize` (or
  `/compress`) to trigger it early. [official-docs — **CONFIRMED**]
- **Trigger/units:** **No documented numeric threshold** exposed to users. Cursor's engineering blog
  mentions internal training-time triggers (40k / 80k tokens) but these are **research parameters, not
  shipped runtime settings.** [official-docs / blog — flagged]
- **Configurable threshold:** **DOES NOT EXIST.** The full CLI parameter list and
  `cli-config.json` / `.cursor/cli.json` schema expose no context/compaction/summarization key. Absence
  corroborated by open community feature requests explicitly asking for an 80–85% tunable trigger.
  [official-docs — cursor.com/docs/cli/reference/parameters + /configuration; forum threads
  148699/160865/149291 — **CONFIRMED** via absence]

## The gauge channel (if any)

**NO reliable mechanism. No documented API, file, or statusline schema exposes numeric context
utilization to an external agent/hook/extension in either the IDE or CLI.** [**CONFIRMED**]

- `/statusline` custom status bar (confirmed shipped, official changelog 04-14-26) surfaces "session and
  runtime signals — mode, branch, environment, active task hints, session metadata." **Undocumented as a
  formal schema.** [official-docs changelog — **CONFIRMED**]
  - **FLAG (UNVERIFIABLE):** whether `/statusline` can surface a context-utilization percentage / token
    count is **NOT confirmed** in any official doc — one forum poster speculated it "looks compatible
    with Claude's implementation," but this is unverified community speculation. [community — forum
    152287 — flagged]
- `cli-config.json` documents only `display.showStatusIndicators` (bool) and
  `display.showStatusLineRunningTime` (bool, elapsed time only) — neither is context usage. [official-docs
  — **CONFIRMED**]
- Cloud Agent API exposes transcripts/logs/setup-details for progress monitoring but **nothing about
  token/context accounting.** [official-docs — cursor.com/docs/cloud-agent — **CONFIRMED**]

Consequence: kata must run **deterministic-rotation-only** and **cannot build a gauge-driven
early-compaction loop** on Cursor.

## The resume primitive

Session continuity: `cursor-agent --resume [chatId]`, `--continue` (alias `--resume=-1`), `agent ls` to
list chat IDs — the practical handoff primitive for multi-hour runs. [official-docs — **CONFIRMED**]

**Cloud/Background Agents = Cursor's purpose-built long-run product:** isolated cloud VMs, separate
branches, deliberately small task scope. Documented running **25–52+ hours** unattended. Endurance is
**architectural** (decompose into scoped isolated cloud-agent tasks), **not** a compaction/threshold knob;
progress observed via transcripts/logs. [official-docs blog — cursor.com/blog/long-running-agents +
cloud-agent-lessons — **CONFIRMED**]

## Must-guard risks

- **Two load-bearing open gaps kata must not assume away:** (1) whether headless context exhaustion is a
  **hard death** vs forced summarization is **undocumented** (only inferable from "auto-summarization
  exists to prevent complete failure"); (2) whether `/statusline` can surface context % is
  **unconfirmed.**
- **Headless failure modes are rough/undocumented.** Local headless CLI (`cursor-agent -p`/`--print`,
  `--output-format json|stream-json`) is a single foreground process; official docs are silent on mid-run
  context exhaustion, and community bug reports describe headless processes hanging / not releasing the
  terminal. Add a **hang watchdog**. [official-docs — parameters (silent); community — flagged
  UNVERIFIABLE]
- **Recommended kata policy:** for local CLI, deterministic rotation + `--resume`/`--continue`
  checkpoint-restart as the sole degradation lever, with the hang watchdog. For genuinely long autonomy,
  prefer Cursor's **Cloud Agents architectural pattern** (kata orchestrates many scoped cloud-agent
  tasks) over relying on a single agent's context management.

## Re-verify before build

The RESEARCH doc's Confidence-Gap items for Cursor ride here as re-verify-before-build flags. Do **not**
hard-code any of these into kata logic without first confirming against a live install:

10. **Cursor headless exhaustion = hard death vs forced summarization.** Undocumented; only inferable. →
    Empirically exhaust a `cursor-agent -p` run and observe exit behavior. [docs-silent]
11. **Cursor `/statusline` context-% capability.** Existence confirmed (changelog); field schema
    undocumented; context-% support is unverified community speculation. → Inspect `/statusline` payload
    on a live CLI. [UNVERIFIABLE]
12. **Cursor docs-reorg source degradation.** Several `docs.cursor.com` URLs now 308-redirect to a
    generic landing page; claims rest on cache + corroborating official blog. → Re-fetch canonical docs
    once the reorg settles. [degraded-source]

---

**Portable-architecture conclusion (SR-6):** 3 of 5 non-Claude platforms have no host knob and/or no
gauge, so **internal-threshold-primary is the only portable architecture** — kata's own threshold
tracking, not the host's compaction, is the load-bearing mechanism on Cursor.
