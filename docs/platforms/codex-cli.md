# Codex CLI — recommended context-autonomy config

> **Docs-only in v0.2.1 — no non-Claude code legs (CA-L39).** This page states the recommended
> degradation posture for driving OpenAI Codex CLI under KataHarness. There is **no live Codex leg** in
> v0.2.1: Claude Code is the only platform with shipped context-autonomy machinery. Everything below is a
> *build reference* for a future Codex adapter, sourced verbatim from `RESEARCH-CROSS-PLATFORM.md`. Every
> load-bearing claim carries its citation and verification verdict; `UNVERIFIABLE` items stay flagged and
> ride the **Re-verify before build** section.

## The §5 degradation row (frozen)

| Field | Value |
|---|---|
| **Gauge for kata** | **YES — best-in-class** (rollout JSONL `token_count` tailing; OTel `task.compact`) — reverse-engineered schema, parse defensively |
| **Host knob** | `model_auto_compact_token_limit` (tokens) |
| **Resume primitive** | `codex resume --last/<id>` |
| **v0.2.1 kata policy** | Full ladder: gauge → lowered limit / proactive `/compact` → resume-restart. Must-guard: 402-hang wall-clock watchdog; shared 5-hr quota on ChatGPT-plan auth (prefer API key unattended); non-convergent compaction ⇒ keep deterministic rotation as backstop. |

## The knob to set

**Automatic history/context compaction (pre-turn + server-side).** Codex checks accumulated token usage
before each turn; crossing the threshold calls a proprietary compaction endpoint returning an opaque,
encrypted "compaction item" (summary + up to ~20k tokens of most-recent user messages). Manual `/compact`
also available in the TUI. [official-docs — developers.openai.com/api/docs/guides/compaction +
/codex/cli/features]

- **Primary knob:** `model_auto_compact_token_limit` — integer **tokens**; default **unset → "uses model
  defaults"** (no fixed number published); set in `~/.codex/config.toml` as
  `model_auto_compact_token_limit = <tokens>`, or per-invocation
  `codex --config model_auto_compact_token_limit=<n>`. [official-docs —
  developers.openai.com/codex/config-reference — **CONFIRMED**]
- **Supporting knobs:**
  - `model_context_window` — integer tokens; the denominator for "% context left." Needed for
    custom/non-default models. **Known bug:** very large values (~1M) can be silently overridden
    (issue #19185, community-reported). [official-docs + github.com/openai/codex/issues/19185]
  - `compact_prompt` / `experimental_compact_prompt_file` — string / path; overrides the built-in
    compaction prompt to bias what survives (task state, decisions, file paths). Default: built-in
    prompt. [official-docs — config-reference]
  - `history.max_bytes` (bytes, default unset/no cap) + `history.persistence` (`save-all` default |
    `none`) — bounds on-disk `history.jsonl`, relevant to 8-hr log growth. [official-docs —
    config-advanced + config-reference]
- **FLAG (UNVERIFIABLE / community):** community sources report an effective auto-compact trigger around
  **~95%** of the window when the limit is unset, and that raising the threshold much above **~90%** is
  silently clamped. Neither the numeric default nor the ~90% clamp is in official docs. **Re-verify
  against current `codex-rs` source before hard-coding.** [community]

## The gauge channel (if any)

**Three channels, ascending automatability — the strongest observability story of the five platforms.**
[**CONFIRMED**]

1. **TUI status line** — `tui.status_line = ["model","context","limits",...]` (or `/statusline`) renders
   a live `CTX <bar> N%` indicator from `token_count` vs `model_context_window`. Human-facing.
   [official-docs — config-reference]
2. **Session rollout JSONL** — `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` persists periodic
   `token_count` events (input/cached/output/reasoning/total) + active `model_context_window`, tool
   calls, compaction events, approvals. On by default (`history.persistence=save-all`); skip with
   `codex exec --ephemeral`. **An external orchestrator CAN tail/parse this to compute live
   utilization** — the best bet for kata. **Caveat:** community-reverse-engineered format, **not a
   documented stable API contract.** [community — verified against issue #17618, discussions/3827;
   path/`--ephemeral`/`save-all` confirmed by official docs — **CONFIRMED**]
3. **OpenTelemetry export** — `otel.metrics_exporter` (`none|statsig|otlp-http|otlp-grpc`, default
   `statsig`) emits a `task.compact` counter ("number of compactions per type — remote/local,
   manual/auto") to an external collector for dashboard-level compaction-frequency observability.
   [official-docs — config-advanced — **CONFIRMED** verbatim]

**No push hook fires on "context nearing threshold."** The generic `notify` command officially fires only
on `agent-turn-complete` (`turn-id`/`input-messages`/`last-assistant-message`), no context-usage fields.
[official-docs — **CONFIRMED**]

## The resume primitive

**Session resume/handoff is first-class:** `codex resume --last | --all | <SESSION_ID>` reloads "the
original transcript, plan history, and approvals" — kata's checkpoint-restart mechanism after
crash/compaction failure. [official-docs — **CONFIRMED**]

Automation entry point: `codex exec` (alias `codex e`) with `--json`/`--experimental-json` (NDJSON
events), `--output-last-message out.txt`, `--ephemeral`. Compaction is **not disabled** headless — the
pre-turn check + `model_auto_compact_token_limit` still fire. ("Not disabled by exec" is an inference from
absence of an exec override — flagged, but consistent with docs.) [official-docs — cli/features +
cli/reference — **CONFIRMED**]

## Must-guard risks

Full degradation ladder is available (live gauge → proactive `/compact` or lowered
`model_auto_compact_token_limit` → `codex resume` checkpoint-restart on hard failure). kata should still
encode:

- **Hang-on-402, no exit code.** Quota/insufficient-credit (HTTP 402) errors are **not surfaced** — the
  TUI hangs on "Processing request…" indefinitely with **no non-zero exit**. kata needs a **wall-clock
  watchdog**, not just exit-code monitoring. [github.com/openai/codex/issues/6512 — **CONFIRMED**]
- **Shared 5-hr quota window.** ChatGPT-plan auth (vs API key) shares **one 5-hour rolling usage window**
  across interactive + headless `exec` → a long unattended loop can silently exhaust quota. Prefer
  **API-key auth** for unattended runs or budget accordingly. [help.openai.com/en/articles/11369540 —
  **CONFIRMED**]
- **Non-convergent compaction on tool-heavy threads.** Compaction does **not always converge** on very
  long, tool-call-heavy threads — "runs out of context instead of compacting/resuming." Keep
  **deterministic rotation as a backstop** even with a gauge present.
  [github.com/openai/codex/issues/19842 — **CONFIRMED**]
- **Rollout schema is reverse-engineered** — kata should **defensively parse and tolerate format churn**.

## Re-verify before build

The RESEARCH doc's Confidence-Gap items for Codex ride here as re-verify-before-build flags. Do **not**
hard-code any of these into kata logic without first confirming against the running version:

4. **Codex auto-compact default value + ~90% clamp.** Official docs say only "uses model defaults"; the
   ~95% effective trigger and ~90% silent clamp are community-sourced. → Re-verify against current
   `codex-rs` source / running-version behavior before hard-coding into kata logic. [community]
5. **Codex rollout-JSONL schema stability.** kata's best gauge relies on a reverse-engineered file format
   that is not a documented API contract. → Pin behavior to a Codex version and add defensive parsing;
   watch for format churn. [community]
6. **Codex `model_context_window` ~1M silent override (#19185).** Community-reported, not confirmed
   fixed. → Verify the effective window when configuring large-context models. [issue-tracker]

---

**Portable-architecture conclusion (SR-6):** even though Codex has the best gauge and a full knob, 3 of 5
non-Claude platforms have no host knob and/or no gauge, so **internal-threshold-primary is the only
portable architecture** — kata's own threshold tracking, not the host's compaction, is the load-bearing
mechanism, with Codex's gauge and ladder as a favorable overlay.
