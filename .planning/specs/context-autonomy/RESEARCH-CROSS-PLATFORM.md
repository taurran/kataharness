# KataHarness Cross-Platform Compaction Research

**Purpose:** Inform a design grill deciding how kata's context-autonomy feature degrades per platform, and serve as a future docs/recommended-config reference.

**Scope:** Five agent platforms — Kiro, OpenAI Codex CLI, GitHub Copilot, Cursor, Gemini CLI. For each: (a) compaction mechanism + configurable knob, (b) context observability for a running agent, (c) unattended-run behavior, (d) the kata degradation path implied.

**Verdict legend:** Each load-bearing claim carries a citation and a verification verdict. `CONFIRMED` = independently verified against the cited source. `UNVERIFIABLE` = stated in body but explicitly flagged as unconfirmed (docs silent, community-only, or inferred). `REFUTED` claims are excluded from the body and listed in the Corrections Footnote — **no claims were refuted in this dataset.**

**Confidence tiers on source material:** `official-docs` > `issue-tracker`/`changelog` > `community` (blogs, forum posts, reverse-engineered file formats). Tiers are noted inline where they affect trust.

---

## 1. Kiro (AWS agentic IDE + Kiro CLI)

### (a) Compaction mechanism + configurable knob

Kiro has **two distinct compaction surfaces** — one in the IDE chat panel, one in the CLI — with different configurability.

**IDE auto-summarization (chat panel).**
- *What:* The IDE chat agent auto-summarizes prior messages once usage nears the model's context limit, so the session continues instead of erroring.
- *Knob:* **NO KNOB EXISTS.** Not user-configurable per official docs — no setting, env var, or flag documented for the IDE summarization threshold or behavior. [official-docs — kiro.dev/docs/chat/summarization/ — **CONFIRMED**]
- *Trigger/units:* ~80% of the active model's context window (percent, model-dependent). Context *files* are separately capped at 75% of the window, with excess auto-dropped. [official-docs — **CONFIRMED** via kiro.dev/docs/chat/summarization/]

**CLI conversation compaction.**
- *What:* Summarizes older turns while retaining recent ones; fires automatically on context-window overflow, or manually via `/compact`.
- *Knob (name / units / default / how to set):*
  - `chat.disableAutoCompaction` — boolean; default presumed `false`/enabled (not published); set via `kiro-cli settings chat.disableAutoCompaction <value>` → writes `~/.kiro/settings/cli.json`.
  - `compaction.excludeMessages` — unit: message pairs; docs example value `2`; `kiro-cli settings compaction.excludeMessages <N>`.
  - `compaction.excludeContextWindowPercent` — unit: percent of context window; docs example value `2`; `kiro-cli settings compaction.excludeContextWindowPercent <N>`.
  - Both retention knobs are evaluated each run and "the more conservative (larger) value wins."
  - **FLAG (UNVERIFIABLE):** The example values `2`/`2` are illustrative in the settings-command docs; an explicit standalone `default:` label was **not** stated separately — treat as presumptive defaults, not certified. [official-docs — kiro.dev/docs/cli/reference/settings/ + kiro.dev/docs/cli/chat/context/]
- *Session model:* Compaction creates a **new** session (summary-seeded); the original pre-compaction session is preserved and reopened via `/chat resume`. [official-docs — kiro.dev/docs/cli/chat/context/ — **CONFIRMED**]

### (b) Context observability for a running agent

**Interactive/human-facing only — no machine-readable channel.**
- IDE chat-panel live context-usage percentage meter (passive display, not pollable). [official-docs — **CONFIRMED**]
- CLI `/context show` — prints a percentage breakdown by category (context files, tools, Kiro responses, user prompts) plus glob patterns for bloated entries; interactive slash command only. [official-docs — kiro.dev/docs/cli/chat/context/ — **CONFIRMED**]
- **No statusline hook, no JSON/log artifact, no programmatic API** for a supervising process to read utilization out-of-band during a headless `--no-interactive` run. This is verified as an *absence* across the cited official pages. [**CONFIRMED** — claim #3]

### (c) Unattended-run behavior

- Headless mode exists: `kiro-cli chat --no-interactive "<prompt>" --trust-all-tools`, auth via `KIRO_API_KEY` (introduced CLI 2.0). Exit codes documented: 0 success / 1 general / 3 MCP-startup — **none context/token-limit specific.** [official-docs — kiro.dev/docs/cli/headless/ — **CONFIRMED**]
- The headless-mode doc is **silent** on whether/how compaction behaves inside a single `--no-interactive` invocation. [**CONFIRMED** — absence verified]
- **Known defect (issue-tracker, community-reported, not maintainer-confirmed):** With `agentSpawn`/`userPromptSubmit` hooks active in CLI v1.25.0, the auto-compaction trigger **fails to fire** near 100% context; Kiro sends an oversized request and gets `ValidationException: Improperly formed request`, and every subsequent message in the session fails identically until a manual `/compact`. Manual `/compact` still works. [issue-tracker — github.com/kirodotdev/Kiro/issues/5527, label `pending-maintainer-response` — **CONFIRMED** as a faithful characterization of an open report]
- **Known UX defect (issue-tracker):** Even when 80% auto-summarization fires correctly, the agent can mark a task complete before finishing its summary, so the new post-compaction session loses visibility into the prior task's true state (e.g., outstanding compile/test errors) and starts the next task on stale assumptions. [issue-tracker — github.com/kirodotdev/Kiro/issues/4976, Open — **CONFIRMED**]

### (d) Kata degradation path

- **Gauge available? NO.** No pollable API/file/statusline. An orchestrator driving Kiro headlessly cannot observe approaching exhaustion out-of-band → kata must **track its own approaching-context risk independently** (deterministic rotation / token-accounting on its side).
- Compaction infrastructure is real and marketed for autonomy, but **cannot be treated as "compaction always saves you"** for an 8-hr run — hook-heavy configs risk a silent hard-stop failure loop (#5527) with no self-recovery path (manual `/compact` is exactly what's unavailable unattended).
- **Recommendation for a kata degradation policy:** treat Kiro as **deterministic-rotation-only** (no live gauge), and treat hook-enabled configs as higher-risk / require proactive manual-compact scheduling around ~70–80% if kata can estimate usage.

---

## 2. OpenAI Codex CLI

### (a) Compaction mechanism + configurable knob

**Automatic history/context compaction (pre-turn + server-side).**
- *What:* Codex checks accumulated token usage before each turn; crossing the threshold calls a proprietary compaction endpoint returning an opaque, encrypted "compaction item" (summary + up to ~20k tokens of most-recent user messages). Manual `/compact` also available in the TUI. [official-docs — developers.openai.com/api/docs/guides/compaction + /codex/cli/features]
- *Primary knob (name / units / default / how to set):*
  - `model_auto_compact_token_limit` — integer **tokens**; default **unset → "uses model defaults"** (no fixed number published); set in `~/.codex/config.toml` as `model_auto_compact_token_limit = <tokens>`, or per-invocation `codex --config model_auto_compact_token_limit=<n>`. [official-docs — developers.openai.com/codex/config-reference — **CONFIRMED**]
- *Supporting knobs:*
  - `model_context_window` — integer tokens; the denominator for "% context left." Needed for custom/non-default models. **Known bug:** very large values (~1M) can be silently overridden (issue #19185, community-reported). [official-docs + github.com/openai/codex/issues/19185]
  - `compact_prompt` / `experimental_compact_prompt_file` — string / path; overrides the built-in compaction prompt to bias what survives (task state, decisions, file paths). Default: built-in prompt. [official-docs — config-reference]
  - `history.max_bytes` (bytes, default unset/no cap) + `history.persistence` (`save-all` default | `none`) — bounds on-disk `history.jsonl`, relevant to 8-hr log growth. [official-docs — config-advanced + config-reference]
- **FLAG (UNVERIFIABLE / community):** Community sources report an effective auto-compact trigger around **~95%** of the window when the limit is unset, and that raising the threshold much above **~90%** is silently clamped. Neither the numeric default nor the ~90% clamp is in official docs. **Re-verify against current `codex-rs` source before hard-coding.** [community]

### (b) Context observability for a running agent

**Three channels, ascending automatability — this is the strongest observability story of the five platforms.** [**CONFIRMED** — claims #1, #2]
1. **TUI status line** — `tui.status_line = ["model","context","limits",...]` (or `/statusline`) renders a live `CTX <bar> N%` indicator from `token_count` vs `model_context_window`. Human-facing. [official-docs — config-reference]
2. **Session rollout JSONL** — `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` persists periodic `token_count` events (input/cached/output/reasoning/total) + active `model_context_window`, tool calls, compaction events, approvals. On by default (`history.persistence=save-all`); skip with `codex exec --ephemeral`. **An external orchestrator CAN tail/parse this to compute live utilization** — the best bet for kata. **Caveat:** community-reverse-engineered format, **not a documented stable API contract.** [community — verified against issue #17618, discussions/3827; path/`--ephemeral`/`save-all` confirmed by official docs — **CONFIRMED**]
3. **OpenTelemetry export** — `otel.metrics_exporter` (`none|statsig|otlp-http|otlp-grpc`, default `statsig`) emits a `task.compact` counter ("number of compactions per type — remote/local, manual/auto") to an external collector for dashboard-level compaction-frequency observability. [official-docs — config-advanced — **CONFIRMED** verbatim]
- **No push hook fires on "context nearing threshold."** The generic `notify` command officially fires only on `agent-turn-complete` (`turn-id`/`input-messages`/`last-assistant-message`), no context-usage fields. [official-docs — **CONFIRMED**]

### (c) Unattended-run behavior

- `codex exec` (alias `codex e`) is the automation entry point: `--json`/`--experimental-json` (NDJSON events), `--output-last-message out.txt`, `--ephemeral`. Compaction is **not disabled** headless — the pre-turn check + `model_auto_compact_token_limit` still fire. (Note: "not disabled by exec" is an inference from absence of an exec override — flagged, but consistent with docs.) [official-docs — cli/features + cli/reference — **CONFIRMED**]
- **Session resume/handoff is first-class:** `codex resume --last | --all | <SESSION_ID>` reloads "the original transcript, plan history, and approvals" — kata's checkpoint-restart mechanism after crash/compaction failure. [official-docs — **CONFIRMED**]
- **Failure modes for long runs (issue-tracker):**
  - Compaction does **not always converge** on very long, tool-call-heavy threads — issue #19842 "runs out of context instead of compacting/resuming." [github.com/openai/codex/issues/19842 — **CONFIRMED**]
  - ChatGPT-plan auth (vs API key) shares **one 5-hour rolling usage window** across interactive + headless `exec` → a long unattended loop can silently exhaust quota. [help.openai.com/en/articles/11369540 — **CONFIRMED**]
  - Quota/insufficient-credit (HTTP 402) errors **not surfaced** — TUI hangs on "Processing request…" indefinitely, **no non-zero exit** (issue #6512). Real risk for a supervisor expecting clean exit codes. [github.com/openai/codex/issues/6512 — **CONFIRMED**]

### (d) Kata degradation path

- **Gauge available? YES (best-in-class), via rollout-JSONL tailing** — kata can compute live utilization turn-by-turn without the TUI, or subscribe to OTel `task.compact`. Caveat: rollout schema is reverse-engineered, so kata should defensively parse and tolerate format churn.
- **Full degradation ladder available:** live gauge → proactive `/compact` (or lowered `model_auto_compact_token_limit`) → `codex resume` checkpoint-restart on hard failure.
- **Must-guard risks kata should encode:** (1) the "hang on 402, no exit code" case → kata needs a wall-clock watchdog, not just exit-code monitoring; (2) shared 5-hr quota window for ChatGPT-plan auth → kata should prefer API-key auth for unattended runs or budget accordingly; (3) non-convergent compaction on tool-heavy threads → deterministic rotation as a backstop even with a gauge present.

---

## 3. GitHub Copilot (Copilot CLI + async cloud "coding agent")

### (a) Compaction mechanism + configurable knob

**Automatic context compaction (auto-compact).**
- *What:* Copilot CLI auto-summarizes running history in the background once the window fills, replacing older messages with a structured summary (goals, work done, key files, next steps). [official-docs — docs.github.com/en/copilot/concepts/agents/copilot-cli/context-management]
- *Knob:* **NO KNOB EXISTS.** No env var, CLI flag, or `settings.json` key to change the threshold or disable it. Two feature requests confirm the absence: #1761 (open, no maintainer response) requesting a `--compaction-threshold` flag / `config.json` setting, and #947 (closed, no visible explanation) requesting a `copilot config auto_compact false` toggle. Absence corroborated across docs + CLI reference + config help. [official-docs + github.com/github/copilot-cli/issues/1761 + /947 — **CONFIRMED** via absence-of-feature]
- *Trigger/units:* Starts compacting at **~80%** of context capacity (~20% working buffer); if usage hits **~95%** before the summary finishes, the CLI **pauses briefly** rather than crashing. (Jan-2026 changelog loosely says "approaching 95% of the token limit.") [official-docs — context-management + github.blog changelog 2026-01-14]
- *Manual:* `/compact` or `/compact [focus-instructions]` in-session; `Esc` cancels. Not exposed as a launch flag. [official-docs — CLI command reference]
- *PreCompact hook:* Fires immediately before any compaction (auto or manual); payload `trigger: "manual"|"auto"`, session id, cwd, `transcript_path`. Supported in CLI **and** the cloud agent (cloud = **auto trigger only**, no interactive session). Event trigger, no tunable units. [official-docs — docs.github.com/en/copilot/reference/hooks-reference — **CONFIRMED**]

### (b) Context observability for a running agent

**Two partial channels — no guaranteed-accurate live percentage.** [**CONFIRMED** — claim #2]
1. **Interactive-only (official):** `/context` (token/percentage breakdown by system prompt, custom instructions, tool defs, message history, free space, reserved buffer), `/usage` (session usage/cost), `/session checkpoints` (compaction history). **Not confirmed queryable from a single-shot `-p/--prompt` headless invocation** → an unattended orchestrator can't obviously poll them mid-run. [official-docs — context-management + CLI reference]
2. **Programmatic (experimental/community):** `statusLine.command` in `~/.copilot/settings.json` (`{"experimental": true, "statusLine": {"type":"command","command":"<path>"}}`) runs a script after every model turn, piping JSON on stdin — `current_context_used_percentage`, `displayed_context_limit`, `context_window_size`, cache stats, cost/credit, session id, `transcript_path`. **The only near-real-time machine-readable gauge found.** [community — tgrall blog + issues #2342/#2582/#1957 — **CONFIRMED**]
   - **FLAG (bug, must-heed):** Issue #1957 — the delivered `used_percentage` starts at 0% after resume, rises disproportionately, and maxes at 100% while `/context` reports a stable realistic figure. **Treat as approximate, NOT an authoritative session-total metric.** [github.com/github/copilot-cli/issues/1957 — **CONFIRMED**]
3. **On-disk forensics (official):** compaction writes numbered checkpoint files under `~/.copilot/session-state/{session-id}/checkpoints/` alongside the raw event log. After-the-fact observability of *when/what* was summarized, not a live "% full."
   - **FLAG (UNVERIFIABLE detail):** the specific filename `events.jsonl` for the raw log was **not** confirmed in the official docs checked (the `checkpoints/` dir under `session-state/` *is* confirmed) — non-load-bearing, uncontradicted. [official-docs — best-practices + context-management]

### (c) Unattended-run behavior

- Auto-compaction fires headless (background mechanism independent of interactive vs `-p/--prompt`); GitHub markets sessions as "infinite" **because** auto-compaction prevents hard exhaustion (compact ~80%, pause ~95%). [official-docs — context-management — **CONFIRMED**]
- Resume well-supported: `-r`/`--resume`, `--continue`, `--session-id`, `--connect` (remote/cloud). `-p/--prompt` one-shot; `--output-format=json` JSONL; `-s/--silent` for scripting. `--context TIER` opts into `long_context` vs `default` (changes window size, not compaction policy). [official-docs — CLI reference — **CONFIRMED**]
- **Community defect (must-heed):** issue #2755 — headless-mode **internal-state accumulation** causes progressive latency degradation (1st req ~1–3s → later ~17–30s), resolved only by killing the process. Real risk for an 8-hr run even though context itself is compacted. [github.com/github/copilot-cli/issues/2755 — **CONFIRMED**]
- **Cloud coding agent (separate surface):** async, PR-driven, runs in GitHub Actions. Its own **1-hour stuck-session timeout** (fixed, not configurable) with manual unassign/reassign recovery — **not** context-window-based, and no context-exhaustion crash behavior documented. `timeout-minutes` in the workflow only bounds env-setup, not the working session. Supports `PreCompact` (auto only) → implies it runs the same underlying auto-compaction. Community reports (not official) note a ~5–6 min internal command-exec timeout causing retry loops on long build scripts. [official-docs — troubleshoot-coding-agent + hooks-reference; community discussion 178998 — **CONFIRMED**]
- **FLAG (marketing claim to verify empirically):** No official source enumerates a hard "session dies at context exhaustion" mode; the "infinite sessions" / "auto-compaction prevents that outcome" framing is GitHub's own and should be validated during kata's own long-run testing. [flagged]

### (d) Kata degradation path

- **Gauge available? PARTIAL / UNTRUSTWORTHY.** The only machine-readable live gauge (`statusLine.command`) is experimental *and* numerically wrong per #1957. Interactive `/context` is accurate but not headless-pollable. → kata cannot rely on a trustworthy live percentage.
- **Best kata signal = PreCompact hook** as a coarse "compaction is about to happen" event (works CLI + cloud/auto), plus on-disk checkpoint forensics after the fact.
- **Recommended kata policy:** treat Copilot as **deterministic-rotation + PreCompact-event-driven**, not gauge-driven. Add a **latency watchdog** for the #2755 state-accumulation degradation (periodic process recycle on an 8-hr run). For the cloud coding agent, design around the fixed 1-hr timeout with unassign/reassign as the restart primitive.

---

## 4. Cursor (IDE Agent + Cursor CLI / cursor-agent, incl. Cloud/Background Agents)

### (a) Compaction mechanism + configurable knob

**Automatic context-window summarization ("self-summarization").**
- *What:* When an Agent/Composer session nears the window limit, Cursor pauses, generates a condensed summary, and resumes with the summary substituted for full history. Cursor's **only** built-in compaction mechanism. [official-docs — docs.cursor.com/context/management (now 308-redirects; verified via cache + corroborating official blog cursor.com/blog/self-summarization + cursor.com/learn/context)]
- *Knob:* **NO KNOB EXISTS.** Fires automatically and silently — no flag, env var, or `settings.json`/`cli-config.json` key. Only user control is reactive: manual `/summarize` (or `/compress`) to trigger it early. [official-docs — **CONFIRMED**]
- *Trigger/units:* **No documented numeric threshold** exposed to users. Cursor's engineering blog mentions internal training-time triggers (40k / 80k tokens) but these are **research parameters, not shipped runtime settings.** [official-docs / blog — flagged]
- *Configurable threshold:* **DOES NOT EXIST.** Full CLI parameter list and `cli-config.json` / `.cursor/cli.json` schema expose no context/compaction/summarization key. Absence corroborated by open community feature requests explicitly asking for an 80–85% tunable trigger. [official-docs — cursor.com/docs/cli/reference/parameters + /configuration; forum threads 148699/160865/149291 — **CONFIRMED** via absence]

### (b) Context observability for a running agent

**NO reliable mechanism. No documented API, file, or statusline schema exposes numeric context utilization to an external agent/hook/extension in either the IDE or CLI.** [**CONFIRMED** — claim #2]
- `/statusline` custom status bar (confirmed shipped, official changelog 04-14-26) surfaces "session and runtime signals — mode, branch, environment, active task hints, session metadata." **Undocumented as a formal schema.** [official-docs changelog — **CONFIRMED**]
  - **FLAG (UNVERIFIABLE):** Whether `/statusline` can surface a context-utilization percentage / token count is **NOT confirmed** in any official doc — one forum poster speculated it "looks compatible with Claude's implementation" (which exposes context %), but this is unverified community speculation. [community — forum 152287 — flagged]
- `cli-config.json` documents only `display.showStatusIndicators` (bool) and `display.showStatusLineRunningTime` (bool, elapsed time only) — neither is context usage. [official-docs — **CONFIRMED**]
- Cloud Agent API exposes transcripts/logs/setup-details for progress monitoring but **nothing about token/context accounting.** [official-docs — cursor.com/docs/cloud-agent — **CONFIRMED**]

### (c) Unattended-run behavior

- **Local headless CLI:** `cursor-agent -p`/`--print`, `--output-format json|stream-json` — single foreground process. **Official docs are silent on mid-run context exhaustion** (hard death vs forced summarization). Community bug reports describe headless processes hanging / not releasing the terminal — corroborating-but-not-authoritative that headless failure modes are rough/undocumented. [official-docs — parameters (silent); community — flagged UNVERIFIABLE]
- Session continuity: `cursor-agent --resume [chatId]`, `--continue` (alias `--resume=-1`), `agent ls` to list chat IDs — the practical handoff primitive for multi-hour runs. [official-docs — **CONFIRMED**]
- **Cloud/Background Agents = Cursor's purpose-built long-run product:** isolated cloud VMs, separate branches, deliberately small task scope. Documented running **25–52+ hours** unattended. Endurance is **architectural** (decompose into scoped isolated cloud-agent tasks), **not** a compaction/threshold knob; progress observed via transcripts/logs. [official-docs blog — cursor.com/blog/long-running-agents + cloud-agent-lessons ("days or even weeks," "moved from eternal workflows to multiple shorter ones that exit after a single task") — **CONFIRMED**]
- Only **one** platform-wide compaction mechanism (auto-summarization + manual `/summarize`); no evidence it's disabled or differs headless vs interactive — it's a context-length-triggered behavior regardless of surface. [official-docs — **CONFIRMED**]

### (d) Kata degradation path

- **Gauge available? NO.** No documented way to read live context utilization on any Cursor surface. → kata must run **deterministic-rotation-only** and cannot build a gauge-driven early-compaction loop on Cursor.
- **Two load-bearing open gaps kata must not assume away:** (1) whether headless context exhaustion is a **hard death** vs forced summarization is **undocumented** (only inferable from "auto-summarization exists to prevent complete failure"); (2) whether `/statusline` can surface context % is **unconfirmed.**
- **Recommended kata policy:** for local CLI, deterministic rotation + `--resume`/`--continue` checkpoint-restart as the sole degradation lever, with a hang watchdog for the undocumented-headless-failure risk. For genuinely long autonomy, prefer Cursor's **Cloud Agents architectural pattern** (kata orchestrates many scoped cloud-agent tasks) over relying on a single agent's context management.

---

## 5. Gemini CLI (google-gemini/gemini-cli)

### (a) Compaction mechanism + configurable knob

**Automatic Chat Compression (`ChatCompressionService`) — the most transparent/source-documented of the five.**
- *What:* Before each turn, if `lastPromptTokenCount >= threshold * tokenLimit(model)`, it (1) truncates oversized tool outputs (reverse token-budget, 50k-token function-response budget, oldest large outputs cut to ~last 30 lines, saved to a temp file), (2) sends older history to a summarizer persona producing an XML `<state_snapshot>` (goal, key knowledge, FS state, plan), (3) runs a second "critically evaluate" verification pass, (4) splices `[snapshot-as-user, ack-as-model]` + most-recent ~30% of history back in. If the result is **larger** than the original, compression aborts (`COMPRESSION_FAILED_INFLATED_TOKEN_COUNT`) and raw truncation is used. [official-docs / source — packages/core/src/context/chatCompressionService.ts — **CONFIRMED**]
- *Primary knob (name / units / default / how to set):*
  - `model.compressionThreshold` — **fraction 0–1** of the model's token limit; **default `0.5` (50%)**; set in `settings.json` or via `/settings`; `requiresRestart: true`. [official-docs / source — settingsSchema.ts, main branch commit f7af4e5 — **CONFIRMED**]
  - Manual trigger: `/compress` (force=true, bypasses threshold).
  - `PreCompress` hook fires (fire-and-forget, cannot block/modify) with `{trigger: 'auto'|'manual'}` for logging/observability. [official-docs — docs/hooks/reference.md — **CONFIRMED**]
- *Non-configurable internals:* preserve-fraction `COMPRESSION_PRESERVE_THRESHOLD = 0.3` (last 30% kept); `COMPRESSION_FUNCTION_RESPONSE_TOKEN_BUDGET = 50,000`. [source — **CONFIRMED**]
- *Separate hard cap:* `model.maxSessionTurns` — integer turns; **default `-1` (unlimited)**; a request-count runaway guard, **not** context-size-based; on hit emits `MaxSessionTurns` and stops. [official-docs — session-management.md + settings.schema.json — **CONFIRMED**]
- **FLAG (churn / re-verify):** A **deprecated** predecessor `model.chatCompression.contextPercentageThreshold` (reported default `0.7`) was renamed/re-tuned to `model.compressionThreshold` (default `0.5`). Subsystem has churned across recent releases — **verify against the installed CLI's `/settings` output before relying on the name/default in production.** [source vs third-party writeups — flagged]

### (b) Context observability for a running agent

**Fragmented across three surfaces; no first-class %-remaining API.** [**CONFIRMED** — claim #1]
1. **Headless JSON (best for kata):** `gemini -p "..." --output-format json` returns one object with `stats` (token counts: prompt, candidates, total, cached, thoughts, tool; turn + tool-call counts; duration). `--output-format stream-json` emits NDJSON events (init, message, tool_use, tool_result, error, result). Invocation-time flag only; default is plain text. **A wrapping orchestrator polls token growth turn-by-turn without the TUI.** [official-docs — geminicli.com/docs/cli/headless — **CONFIRMED**] (Minor: stream-json stats are aggregated in the final `result` event rather than strictly per-event.)
2. **TUI footer:** `ui.footer.hideContextPercentage` (boolean; **default `true` → HIDDEN**; set `false` to show "`<model> (X% context left)`"). Human-facing render, not a queryable API. [source — settingsSchema.ts — **CONFIRMED**]
   - **FLAG (source discrepancy):** a rendered docs-site fetch reported default `false`/shown; **direct source inspection said default `true`/hidden.** Trusting source over the summarizer, but flagged. [flagged]
3. **On-disk session files:** `~/.gemini/tmp/<project_hash>/chats/` persist full per-turn token-usage stats (input/output/cached, etc.) + reasoning summaries. A supervising process **could** tail/parse these as a side-channel even when not driving the process — **inferred from the session-management doc's description of recorded contents, not published as a stable public integration schema.** [official-docs — session-management.md — **CONFIRMED** contents; side-channel use flagged as inference]
- `PreCompress` hook = advisory pre-compression signal only; **cannot report usage %**, cannot block/alter. [**CONFIRMED**]

### (c) Unattended-run behavior

- Compaction fires the **same** headless as interactive — the per-turn threshold check runs regardless of TTY (the "regardless of TTY" point is a flagged inference, uncontradicted). An 8-hr `-p`/scripted run still auto-compresses at `model.compressionThreshold` (default 0.5). [**CONFIRMED**]
- **Two limit behaviors:**
  - `maxSessionTurns` (default `-1`) — if a finite cap is hit, **non-interactive exits with an error** (vs interactive which stops and waits), **exit code 53 "Turn limit exceeded."** This is the knob kata would tune. [official-docs — session-management.md + headless docs — **CONFIRMED**]
  - **True context exhaustion is best-effort, NOT guaranteed:** the underlying Gemini API throws a hard `input token count exceeds maximum` error when a single turn's payload (huge tool output, `--all-files` bulk load) blows past the limit faster than the threshold check, or when auto model-switching moves a long-history session onto a smaller-context model mid-session. Non-interactive **exits with an error, does not self-heal.** [issue-tracker — github.com/google-gemini/gemini-cli/issues/8132 (1,048,576 limit) + #9775 (5,911,388 > 1,048,576, manual restart required) — **CONFIRMED**]
- **Session resume/handoff:** `gemini --resume`/`-r` (most recent), `--resume <index|uuid>`, in-session `/resume` (Session Browser), named checkpoints `/resume save|list|resume <name>` (aliases `/chat …`), `--list-sessions`/`--delete-session`. Retention via `general.sessionRetention` (`enabled` default true, `maxAge` default `"30d"`, `maxCount` default unlimited, `minRetention` default `"1d"`). A killed/errored session is resumable → the practical handoff path for surviving a hard failure. [official-docs — session-management.md — **CONFIRMED**]

### (d) Kata degradation path

- **Gauge available? YES** — headless `--output-format json`/`stream-json` `stats` give real per-turn token counts (a documented, official channel — cleaner than Codex's reverse-engineered rollout, though Codex's is continuous-file vs Gemini's per-invocation). On-disk `chats/` files are a secondary side-channel.
- **Full degradation ladder available:** live token gauge (JSON stats) → tune `model.compressionThreshold` down for earlier/more-frequent compression → `/compress` proactively → `--resume` checkpoint-restart on the hard `input token count exceeds maximum` error.
- **Must-guard risk:** compression is best-effort — a single oversized turn (bulk tool output / `--all-files`) or mid-session model auto-switch can hard-fail past it. kata should **cap single-turn tool-output size** and pin the model, and treat exit code 53 / API token errors as **resume-and-continue** triggers, not terminal.

---

## Comparison Table

| Platform | Compaction knob (name / units / default) | Configurable threshold? | Live context gauge for orchestrator | Unattended-run posture |
|---|---|---|---|---|
| **Kiro** | CLI: `chat.disableAutoCompaction` (bool); `compaction.excludeMessages` (msg pairs, ~2); `compaction.excludeContextWindowPercent` (%, ~2). IDE: none | Retention tunable; **no trigger-threshold knob** (IDE fires ~80%, CLI on overflow) | **NO** (interactive `/context show` + IDE meter only; no API/file/statusline) | Headless mode exists (`--no-interactive`, `KIRO_API_KEY`); docs silent on headless compaction; **hook-config auto-compact can hard-fail loop (#5527)**; task-state loss across session boundary (#4976) |
| **Codex** | `model_auto_compact_token_limit` (tokens, unset→model default); `model_context_window`; `compact_prompt` | **YES** (token limit; community: >~90% clamped) | **YES — best** (rollout JSONL `token_count`, tailable; OTel `task.compact`; TUI `CTX N%`). Rollout schema reverse-engineered | `codex exec` + `resume --last/--all/<id>`; compaction fires headless; **hang-on-402 no exit (#6512)**; shared 5-hr quota window; non-convergent compaction on tool-heavy threads (#19842) |
| **Copilot** | Auto-compact — **NO KNOB** (~80% start, ~95% pause) | **NO** (2 rejected/stalled FRs: #1761 open, #947 closed) | **PARTIAL/UNTRUSTED** (`statusLine.command` JSON, but #1957 says % is wrong; `/context` accurate but interactive-only). PreCompact hook = coarse event | "Infinite sessions" via auto-compact; resume flags rich; **headless state-accumulation latency creep (#2755)**; cloud agent = fixed **1-hr** timeout, unassign/reassign |
| **Cursor** | Auto self-summarization — **NO KNOB** (manual `/summarize` only) | **NO** (open FRs confirm absence; internal 40k/80k are training params) | **NO** (`/statusline` shipped but no confirmed context-% field; cli-config only elapsed-time; Cloud API = no token accounting) | Headless `-p` single process, **docs silent on exhaustion**; `--resume`/`--continue`/`agent ls`; **Cloud Agents = architectural 25–52+ hr via scoped isolated VMs, not a compaction knob** |
| **Gemini** | `model.compressionThreshold` (fraction 0–1, **0.5**); `model.maxSessionTurns` (turns, **-1**) | **YES** (`compressionThreshold`; churned from deprecated 0.7 name) | **YES** (`--output-format json/stream-json` `stats` token counts — official; on-disk `chats/` side-channel; footer % hidden by default) | Compaction fires headless; `maxSessionTurns` hit → **exit 53**; **hard `input token count exceeds maximum` on oversized single turn (#8132/#9775), no self-heal**; `--resume` + 30-day retention |

---

## Confidence Gaps — What Needs Hands-On Verification

1. **Kiro CLI compaction defaults (`excludeMessages`/`excludeContextWindowPercent` = 2).** Docs show `2`/`2` only as illustrative example values; no standalone `default:` label. → Run `kiro-cli settings` on a live install to read actual defaults. [UNVERIFIABLE]
2. **Kiro headless compaction behavior.** Official headless-mode doc is entirely silent on whether/how compaction runs inside a single `--no-interactive` invocation, and whether one run can span multiple internal compactions. → Empirically drive a long headless Kiro run to observe. [docs-silent]
3. **Kiro #5527 severity for kata's hook usage.** Community-reported, not maintainer-confirmed; if kata registers `agentSpawn`/`userPromptSubmit` hooks, verify whether the auto-compact bypass reproduces on the current CLI version. [issue-tracker, unconfirmed by maintainer]
4. **Codex auto-compact default value + ~90% clamp.** Official docs say only "uses model defaults"; the ~95% effective trigger and ~90% silent clamp are community-sourced. → Re-verify against current `codex-rs` source / running-version behavior before hard-coding into kata logic. [community]
5. **Codex rollout-JSONL schema stability.** kata's best gauge relies on a reverse-engineered file format that is not a documented API contract. → Pin behavior to a Codex version and add defensive parsing; watch for format churn. [community]
6. **Codex `model_context_window` ~1M silent override (#19185).** Community-reported, not confirmed fixed. → Verify effective window when configuring large-context models. [issue-tracker]
7. **Copilot `statusLine.command` accuracy (#1957).** The only machine-readable live gauge reports a wrong percentage. → Do NOT trust for kata gating without empirically calibrating against `/context`; consider PreCompact-event-driven degradation instead. [confirmed-inaccurate]
8. **Copilot cloud coding agent compaction.** Its relationship to auto-compaction is *inferred* solely from the hooks-reference marking `PreCompact` "(auto only)"; troubleshooting docs never mention compaction. → Verify empirically. [inferred]
9. **Copilot "infinite sessions" marketing claim.** No official source enumerates a hard exhaustion-death mode; the "compaction prevents that" framing is GitHub's own. → Validate during kata's own 8-hr long-run testing. [marketing-claim]
10. **Cursor headless exhaustion = hard death vs forced summarization.** Undocumented; only inferable. → Empirically exhaust a `cursor-agent -p` run and observe exit behavior. [docs-silent]
11. **Cursor `/statusline` context-% capability.** Existence confirmed (changelog); field schema undocumented; context-% support is unverified community speculation. → Inspect `/statusline` payload on a live CLI. [UNVERIFIABLE]
12. **Cursor docs-reorg source degradation.** Several `docs.cursor.com` URLs now 308-redirect to a generic landing page; claims rest on cache + corroborating official blog. → Re-fetch canonical docs once the reorg settles. [degraded-source]
13. **Gemini `model.compressionThreshold` name/default churn.** Source (main, commit f7af4e5) says name `model.compressionThreshold`, default `0.5`; deprecated predecessor was `0.7`. → Verify against the *installed* CLI version's `/settings`. [version-churn]
14. **Gemini `ui.footer.hideContextPercentage` default.** Source says `true`/hidden; a docs-site summarizer said `false`/shown. → Confirm on a live install. [source-discrepancy]
15. **Gemini on-disk `chats/` as an integration surface.** Contents (per-turn token stats) confirmed by docs, but "treat the file as a pollable API" is an inference, not a documented contract. → Validate schema stability before kata depends on it. [inferred]

---

## Corrections Footnote (REFUTED claims)

**None.** Every claim carried in the verdict sets for all five platforms returned `CONFIRMED`. No claim in the input dataset was refuted and removed from the body. UNVERIFIABLE / flagged items remain in the body at their point of use, marked `FLAG` / `[flagged]` / `[UNVERIFIABLE]`.

---

*Security note (per user global instruction): this was a pure research/documentation task with no first-party code written or modified, so no Snyk scan was applicable or run.*
