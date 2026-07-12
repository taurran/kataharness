# Context-autonomy grounding — Claude Code facts (session 2026-07-04)

Destined for `.planning/specs/context-autonomy/` when the grill opens a branch. Sources cited per claim.

## G1. CLAUDE_CODE_AUTO_COMPACT_WINDOW — VERIFIED EMPIRICALLY (installed binary, v2.1.200)

Official web docs do NOT document it (docs agent: settings page has no env-var entry for it; UNVERIFIED
from official docs — treat as undocumented/semi-internal, may change without notice → design must not
hard-depend on it). But the installed `claude.exe` v2.1.200 binary (string extraction, 2026-07-04) proves:

- **Exists**, parsed as numeric **tokens**, validated + floor-clamped, effective value = `min(setting, model max window)`.
- **Semantics = context-usage CEILING, not tail reserve.** In-binary help text verbatim:
  > "Auto-compact summarizes the conversation when context usage approaches this limit. The actual
  > threshold is the minimum of this setting and your model's maximum context window."
- **Settings.json equivalent exists**: `autoCompactWindow` — `int().min(1e5).max(1e6)`, described
  "Auto-compact window size". **Env var takes precedence** over settings; /config UI warns:
  "CLAUDE_CODE_AUTO_COMPACT_WINDOW is set and takes precedence. Unset it to change this setting here."
  → RECOMMENDATION VECTOR SHOULD BE settings.json, not the env var.
- **Default source = "auto"** — "The auto setting picks a window tuned for your model."
- **Auto-compact CAN be disabled** (`autoCompactEnabled`, "Auto-compact is currently disabled (see /config)").
  → GOTCHA: preflight MUST verify auto-compact is ENABLED or the host backstop doesn't exist at all.
- In-binary product tip (Pro subscribers, >200k models): `Set "autoCompactWindow": 200000 in settings.json`
  — "summarizes earlier so each turn stays cheaper without manual /compact." Precedent for kata's
  recommendation pattern (cap effective frame on huge windows).
- Exact pre-limit buffer/margin ("approaches") is minified; internal telemetry fields exist
  (`autoCompactThreshold`, `willRetriggerNextTurn`, "precomputed compact" arm fractions). → LIVE PROOF
  measures the actual firing point empirically in a throwaway profile.

### ⚠ CORRECTION to the initiative brief (L18 catch)
The brief's example values ("e.g. 300000 on a 1M window; 60000 on 200k" to fire at ~70%) assumed
**reserve** semantics. The binary proves **ceiling** semantics. Correct examples: fire at ~80% of a
200k frame ⇒ set ~160000; ~80% of 1M ⇒ ~800000. Floor is 100k (can't set lower).

## G1b. UserPromptSubmit hook — GROUNDED-BY-PATTERN (2026-07-12, D152/CG-L1; flip to CONFIRMED at the F-9 live smoke)

- **Stdin fields**: `session_id` + `cwd` present in the UserPromptSubmit payload — same envelope family as
  SessionStart/PreCompact (G2); mirrored from the established hook stdin-parsing pattern
  (`kata-sessionstart.py`), not yet re-verified against a live UserPromptSubmit payload for kata's OWN hook.
- **Context injection**: `hookSpecificOutput.additionalContext` — the SAME mechanism CONFIRMED for
  SessionStart (G2), and observed working live for UserPromptSubmit in this operator's environment (the
  kata-target-toggle UserPromptSubmit hook injects additionalContext every session start). Kata's
  `kata-gauge-check.py` reproduces the exact envelope with `hookEventName: "UserPromptSubmit"`.
- **Exit-code hazard**: UserPromptSubmit exit 2 BLOCKS AND ERASES the user's prompt — the gauge-check hook
  is structurally never-exit-2 (whole body under one try/except exiting 0; pinned by test).
- **CONFIRMED pending**: run the F-9 live smoke (install via `kata_install.py --install-hooks`, cross the
  threshold in a kata cwd, observe the injected directive), then flip this entry and the adapter README's
  GROUNDED-BY-PATTERN marker.

## G2. Hooks — VERIFIED from official docs (code.claude.com/docs/en/hooks.md)

- **SessionStart matchers**: `startup` | `resume` | `clear` | `compact` — a hook CAN fire specifically
  post-compaction (`source: "compact"`). ✔ L4(a) viable.
- **SessionStart context injection**: `hookSpecificOutput.additionalContext` injects text into model
  context. ✔ re-anchor instruction can be injected mechanically.
- **PreCompact matchers**: `manual` | `auto` (distinguishes trigger). Can block via exit 2 /
  `{"decision":"block"}`. Full input schema partially UNVERIFIED (docs truncated).
  → GRILL ITEM: blocking auto-compact near the limit is dangerous (no headroom left) — probably
  forbid block usage in kata's hook; observe-only + checkpoint guarantee.

## G3. Context-usage observability

- **Statusline input** receives `context_window.remaining_percentage`, `context_window.total_tokens`
  (docs + gsd-statusline.js reads them).
- **Bridge file** (operator's gsd-statusline.js): `%TEMP%/claude-ctx-<session_id>.json`, schema
  `{session_id, remaining_percentage, used_pct, timestamp}` (timestamp = Unix seconds).
  Kata's own bridge must match this schema (chain-don't-clobber).
- PostToolUse/other hooks receiving context data natively: UNVERIFIED — assume NOT; bridge file is the channel.
- **Statusline in headless (`claude -p`)/unattended runs: UNVERIFIED** → gauge-staleness fallback
  (timestamp freshness check + deterministic N-wave rotation) is MANDATORY, not optional.

## G4. Open items for grill/live-proof

1. Actual auto-compact firing margin below the window value (empirical, throwaway profile).
2. Statusline/bridge freshness in unattended sessions (empirical).
3. PreCompact full input schema (empirical: log stdin in a test hook).
4. autoCompactEnabled default state + where it persists.
5. Whether `autoCompactWindow` "auto" default differs on 1M-window models (cost/cache interaction —
   in-binary Pro tip suggests capping at 200k is sanctioned practice).

## SMOKE-1 result (same session, for the record)

PASS: tag v0.2.0 (+2 docs PRs = 8caabc7), pytest 2505/3 skip (75s), validator 48/0/0, ledger 4 rows
parse, failure_kinds_of per-version correct. FINDING: HANDOFF §7's "class_median returns None at
min_samples=5" expectation is STALE — non-calibration rows 2+3 hold 6 code samples ≥ 5, so 8.35 is
the CORRECT output and calibration exclusion HOLDS (all-rows median would be 3.8). Fix HANDOFF §7
line when docs are touched this session.
