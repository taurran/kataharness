# Gemini CLI — recommended context-autonomy config

> **Docs-only in v0.2.1 — no non-Claude code legs (CA-L39).** This page states the recommended
> degradation posture for driving Gemini CLI (google-gemini/gemini-cli) under KataHarness. There is **no
> live Gemini leg** in v0.2.1: Claude Code is the only platform with shipped context-autonomy machinery.
> Everything below is a *build reference* for a future Gemini adapter, sourced verbatim from
> `RESEARCH-CROSS-PLATFORM.md`. Every load-bearing claim carries its citation and verification verdict;
> `UNVERIFIABLE` items stay flagged and ride the **Re-verify before build** section.

## The §5 degradation row (frozen)

| Field | Value |
|---|---|
| **Gauge for kata** | **YES** (official `--output-format json/stream-json` `stats` token counts; on-disk `chats/` side-channel) |
| **Host knob** | `model.compressionThreshold` (fraction, default 0.5 — verify installed version; name churned) |
| **Resume primitive** | `--resume` (+ 30-day retention), exit 53 on turn cap |
| **v0.2.1 kata policy** | Full ladder: JSON-stats gauge → tuned threshold → `/compress` → resume-and-continue on hard token errors (#8132/#9775). Must-guard: cap single-turn tool output; pin the model (auto-switch mid-session can hard-fail). |

## The knob to set

**Automatic Chat Compression (`ChatCompressionService`) — the most transparent/source-documented of the
five.** Before each turn, if `lastPromptTokenCount >= threshold * tokenLimit(model)`, it (1) truncates
oversized tool outputs (reverse token-budget, 50k-token function-response budget, oldest large outputs cut
to ~last 30 lines, saved to a temp file), (2) sends older history to a summarizer persona producing an XML
`<state_snapshot>` (goal, key knowledge, FS state, plan), (3) runs a second "critically evaluate"
verification pass, (4) splices `[snapshot-as-user, ack-as-model]` + most-recent ~30% of history back in.
If the result is **larger** than the original, compression aborts
(`COMPRESSION_FAILED_INFLATED_TOKEN_COUNT`) and raw truncation is used. [official-docs / source —
packages/core/src/context/chatCompressionService.ts — **CONFIRMED**]

- **Primary knob:** `model.compressionThreshold` — **fraction 0–1** of the model's token limit; **default
  `0.5` (50%)**; set in `settings.json` or via `/settings`; `requiresRestart: true`. [official-docs /
  source — settingsSchema.ts, main branch commit f7af4e5 — **CONFIRMED**]
- **Manual trigger:** `/compress` (force=true, bypasses threshold).
- **`PreCompress` hook** fires (fire-and-forget, cannot block/modify) with `{trigger: 'auto'|'manual'}`
  for logging/observability. [official-docs — docs/hooks/reference.md — **CONFIRMED**]
- **Non-configurable internals:** preserve-fraction `COMPRESSION_PRESERVE_THRESHOLD = 0.3` (last 30%
  kept); `COMPRESSION_FUNCTION_RESPONSE_TOKEN_BUDGET = 50,000`. [source — **CONFIRMED**]
- **Separate hard cap:** `model.maxSessionTurns` — integer turns; **default `-1` (unlimited)**; a
  request-count runaway guard, **not** context-size-based; on hit emits `MaxSessionTurns` and stops.
  [official-docs — session-management.md + settings.schema.json — **CONFIRMED**]
- **FLAG (churn / re-verify):** a **deprecated** predecessor
  `model.chatCompression.contextPercentageThreshold` (reported default `0.7`) was renamed/re-tuned to
  `model.compressionThreshold` (default `0.5`). The subsystem has churned across recent releases —
  **verify against the installed CLI's `/settings` output before relying on the name/default in
  production.** [source vs third-party writeups — flagged]

## The gauge channel (if any)

**Fragmented across three surfaces; no first-class %-remaining API.** [**CONFIRMED**]

1. **Headless JSON (best for kata):** `gemini -p "..." --output-format json` returns one object with
   `stats` (token counts: prompt, candidates, total, cached, thoughts, tool; turn + tool-call counts;
   duration). `--output-format stream-json` emits NDJSON events (init, message, tool_use, tool_result,
   error, result). Invocation-time flag only; default is plain text. **A wrapping orchestrator polls token
   growth turn-by-turn without the TUI.** [official-docs — geminicli.com/docs/cli/headless —
   **CONFIRMED**] (Minor: stream-json stats are aggregated in the final `result` event rather than
   strictly per-event.)
2. **TUI footer:** `ui.footer.hideContextPercentage` (boolean; **default `true` → HIDDEN**; set `false`
   to show "`<model> (X% context left)`"). Human-facing render, not a queryable API. [source —
   settingsSchema.ts — **CONFIRMED**]
   - **FLAG (source discrepancy):** a rendered docs-site fetch reported default `false`/shown; **direct
     source inspection said default `true`/hidden.** Trusting source over the summarizer, but flagged.
     [flagged]
3. **On-disk session files:** `~/.gemini/tmp/<project_hash>/chats/` persist full per-turn token-usage
   stats (input/output/cached, etc.) + reasoning summaries. A supervising process **could** tail/parse
   these as a side-channel even when not driving the process — **inferred from the session-management
   doc's description of recorded contents, not published as a stable public integration schema.**
   [official-docs — session-management.md — **CONFIRMED** contents; side-channel use flagged as
   inference]

`PreCompress` hook = advisory pre-compression signal only; **cannot report usage %**, cannot block/alter.
[**CONFIRMED**]

## The resume primitive

`gemini --resume`/`-r` (most recent), `--resume <index|uuid>`, in-session `/resume` (Session Browser),
named checkpoints `/resume save|list|resume <name>` (aliases `/chat …`), `--list-sessions`/`--delete-session`.
Retention via `general.sessionRetention` (`enabled` default true, `maxAge` default `"30d"`, `maxCount`
default unlimited, `minRetention` default `"1d"`). A killed/errored session is resumable → the practical
handoff path for surviving a hard failure. [official-docs — session-management.md — **CONFIRMED**]

## Must-guard risks

Full degradation ladder is available (live token gauge → tune `model.compressionThreshold` down →
`/compress` proactively → `--resume` checkpoint-restart on the hard `input token count exceeds maximum`
error). kata should still encode:

- **Compression is best-effort, not guaranteed.** The underlying Gemini API throws a hard
  `input token count exceeds maximum` error when a single turn's payload (huge tool output, `--all-files`
  bulk load) blows past the limit faster than the threshold check, or when auto model-switching moves a
  long-history session onto a smaller-context model mid-session. Non-interactive **exits with an error,
  does not self-heal.** kata should **cap single-turn tool-output size** and **pin the model**, and treat
  exit code 53 / API token errors as **resume-and-continue** triggers, not terminal. [issue-tracker —
  github.com/google-gemini/gemini-cli/issues/8132 (1,048,576 limit) + #9775 (5,911,388 > 1,048,576,
  manual restart required) — **CONFIRMED**]
- **`maxSessionTurns` on a finite cap** → non-interactive **exits with an error** (vs interactive which
  stops and waits), **exit code 53 "Turn limit exceeded."** This is the knob kata would tune.
  [official-docs — session-management.md + headless docs — **CONFIRMED**]
- Compaction fires the **same** headless as interactive — an 8-hr `-p`/scripted run still auto-compresses
  at `model.compressionThreshold` (default 0.5). ("Regardless of TTY" is a flagged inference,
  uncontradicted.) [**CONFIRMED**]

## Re-verify before build

The RESEARCH doc's Confidence-Gap items for Gemini ride here as re-verify-before-build flags. Do **not**
hard-code any of these into kata logic without first confirming against a live install:

13. **Gemini `model.compressionThreshold` name/default churn.** Source (main, commit f7af4e5) says name
    `model.compressionThreshold`, default `0.5`; deprecated predecessor was `0.7`. → Verify against the
    *installed* CLI version's `/settings`. [version-churn]
14. **Gemini `ui.footer.hideContextPercentage` default.** Source says `true`/hidden; a docs-site
    summarizer said `false`/shown. → Confirm on a live install. [source-discrepancy]
15. **Gemini on-disk `chats/` as an integration surface.** Contents (per-turn token stats) confirmed by
    docs, but "treat the file as a pollable API" is an inference, not a documented contract. → Validate
    schema stability before kata depends on it. [inferred]

---

**Portable-architecture conclusion (SR-6):** even though Gemini has an official gauge and a tunable
threshold, 3 of 5 non-Claude platforms have no host knob and/or no gauge, so
**internal-threshold-primary is the only portable architecture** — kata's own threshold tracking, not the
host's compaction, is the load-bearing mechanism, with Gemini's JSON-stats gauge and ladder as a
favorable overlay.
