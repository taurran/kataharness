# GitHub Copilot — recommended context-autonomy config

> **Docs-only in v0.2.1 — no non-Claude code legs (CA-L39).** This page states the recommended
> degradation posture for driving GitHub Copilot (Copilot CLI + async cloud "coding agent") under
> KataHarness. There is **no live Copilot leg** in v0.2.1: Claude Code is the only platform with shipped
> context-autonomy machinery. Everything below is a *build reference* for a future Copilot adapter,
> sourced verbatim from `RESEARCH-CROSS-PLATFORM.md`. Every load-bearing claim carries its citation and
> verification verdict; `UNVERIFIABLE` items stay flagged and ride the **Re-verify before build** section.

## The §5 degradation row (frozen)

| Field | Value |
|---|---|
| **Gauge for kata** | **PARTIAL/UNTRUSTED** (`statusLine.command` experimental; % wrong per #1957); PreCompact hook = coarse event |
| **Host knob** | **NO KNOB** (~80% auto, ~95% pause) |
| **Resume primitive** | `--resume`/`--continue`/`--session-id`; cloud = unassign/reassign (fixed 1-hr timeout) |
| **v0.2.1 kata policy** | **Deterministic-rotation + PreCompact-event-driven**, never gauge-driven. Latency watchdog for #2755 headless state creep (periodic process recycle on 8-hr runs). |

## The knob to set

**Automatic context compaction (auto-compact).** Copilot CLI auto-summarizes running history in the
background once the window fills, replacing older messages with a structured summary (goals, work done,
key files, next steps). [official-docs —
docs.github.com/en/copilot/concepts/agents/copilot-cli/context-management]

- **Knob:** **NO KNOB EXISTS.** No env var, CLI flag, or `settings.json` key to change the threshold or
  disable it. Two feature requests confirm the absence: #1761 (open, no maintainer response) requesting a
  `--compaction-threshold` flag / `config.json` setting, and #947 (closed, no visible explanation)
  requesting a `copilot config auto_compact false` toggle. [official-docs +
  github.com/github/copilot-cli/issues/1761 + /947 — **CONFIRMED** via absence-of-feature]
- **Trigger/units:** starts compacting at **~80%** of context capacity (~20% working buffer); if usage
  hits **~95%** before the summary finishes, the CLI **pauses briefly** rather than crashing. (Jan-2026
  changelog loosely says "approaching 95% of the token limit.") [official-docs — context-management +
  github.blog changelog 2026-01-14]
- **Manual:** `/compact` or `/compact [focus-instructions]` in-session; `Esc` cancels. Not exposed as a
  launch flag. [official-docs — CLI command reference]
- **PreCompact hook:** fires immediately before any compaction (auto or manual); payload
  `trigger: "manual"|"auto"`, session id, cwd, `transcript_path`. Supported in CLI **and** the cloud
  agent (cloud = **auto trigger only**, no interactive session). Event trigger, no tunable units.
  [official-docs — docs.github.com/en/copilot/reference/hooks-reference — **CONFIRMED**]

## The gauge channel (if any)

**Two partial channels — no guaranteed-accurate live percentage.** [**CONFIRMED**]

1. **Interactive-only (official):** `/context` (token/percentage breakdown), `/usage` (session
   usage/cost), `/session checkpoints` (compaction history). **Not confirmed queryable from a single-shot
   `-p/--prompt` headless invocation** → an unattended orchestrator can't obviously poll them mid-run.
   [official-docs — context-management + CLI reference]
2. **Programmatic (experimental/community):** `statusLine.command` in `~/.copilot/settings.json`
   (`{"experimental": true, "statusLine": {"type":"command","command":"<path>"}}`) runs a script after
   every model turn, piping JSON on stdin — `current_context_used_percentage`, `displayed_context_limit`,
   `context_window_size`, cache stats, cost/credit, session id, `transcript_path`. **The only
   near-real-time machine-readable gauge found.** [community — tgrall blog + issues #2342/#2582/#1957 —
   **CONFIRMED**]
   - **FLAG (bug, must-heed):** Issue #1957 — the delivered `used_percentage` starts at 0% after resume,
     rises disproportionately, and maxes at 100% while `/context` reports a stable realistic figure.
     **Treat as approximate, NOT an authoritative session-total metric.**
     [github.com/github/copilot-cli/issues/1957 — **CONFIRMED**]
3. **On-disk forensics (official):** compaction writes numbered checkpoint files under
   `~/.copilot/session-state/{session-id}/checkpoints/` alongside the raw event log. After-the-fact
   observability of *when/what* was summarized, not a live "% full."
   - **FLAG (UNVERIFIABLE detail):** the specific filename `events.jsonl` for the raw log was **not**
     confirmed in the official docs checked (the `checkpoints/` dir under `session-state/` *is*
     confirmed) — non-load-bearing, uncontradicted. [official-docs — best-practices + context-management]

## The resume primitive

Resume is well-supported: `-r`/`--resume`, `--continue`, `--session-id`, `--connect` (remote/cloud).
`-p/--prompt` one-shot; `--output-format=json` JSONL; `-s/--silent` for scripting. `--context TIER` opts
into `long_context` vs `default` (changes window size, not compaction policy). [official-docs — CLI
reference — **CONFIRMED**]

**Cloud coding agent (separate surface):** async, PR-driven, runs in GitHub Actions with its own **1-hour
stuck-session timeout** (fixed, not configurable) recovered via **manual unassign/reassign** — the
restart primitive. `timeout-minutes` in the workflow only bounds env-setup, not the working session.
[official-docs — troubleshoot-coding-agent + hooks-reference — **CONFIRMED**]

## Must-guard risks

- **The only machine-readable live gauge is untrustworthy.** `statusLine.command` is experimental *and*
  numerically wrong per #1957; interactive `/context` is accurate but not headless-pollable. → kata
  **cannot rely on a trustworthy live percentage.** Best kata signal = the **PreCompact hook** as a
  coarse "compaction is about to happen" event (works CLI + cloud/auto), plus on-disk checkpoint
  forensics after the fact.
- **Headless state-accumulation latency creep.** Issue #2755 — headless-mode internal-state accumulation
  causes progressive latency degradation (1st req ~1–3s → later ~17–30s), resolved only by killing the
  process. Add a **latency watchdog** (periodic process recycle on an 8-hr run) even though context
  itself is compacted. [github.com/github/copilot-cli/issues/2755 — **CONFIRMED**]
- **Cloud agent = fixed 1-hr timeout.** Design around it with unassign/reassign as the restart
  primitive. [official-docs — troubleshoot-coding-agent]
- **Recommended kata policy:** treat Copilot as **deterministic-rotation + PreCompact-event-driven**, not
  gauge-driven.

## Re-verify before build

The RESEARCH doc's Confidence-Gap items for Copilot ride here as re-verify-before-build flags. Do **not**
hard-code any of these into kata logic without first confirming empirically:

7. **Copilot `statusLine.command` accuracy (#1957).** The only machine-readable live gauge reports a wrong
   percentage. → Do NOT trust for kata gating without empirically calibrating against `/context`;
   consider PreCompact-event-driven degradation instead. [confirmed-inaccurate]
8. **Copilot cloud coding agent compaction.** Its relationship to auto-compaction is *inferred* solely
   from the hooks-reference marking `PreCompact` "(auto only)"; troubleshooting docs never mention
   compaction. → Verify empirically. [inferred]
9. **Copilot "infinite sessions" marketing claim.** No official source enumerates a hard exhaustion-death
   mode; the "compaction prevents that" framing is GitHub's own. → Validate during kata's own 8-hr
   long-run testing. [marketing-claim]

---

**Portable-architecture conclusion (SR-6):** 3 of 5 non-Claude platforms have no host knob and/or no
gauge, so **internal-threshold-primary is the only portable architecture** — kata's own threshold
tracking, not the host's compaction, is the load-bearing mechanism on Copilot.
