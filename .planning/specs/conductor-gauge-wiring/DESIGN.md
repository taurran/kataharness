---
spec: conductor-gauge-wiring
status: FROZEN 2026-07-12 (operator-directed G5: "BUILT and not deferred")
builds_on: v0.2.1 context-autonomy (D146-D149) — closes audit findings C-1/C-2/D-1/D-2
date: 2026-07-12
---

# DESIGN — mechanize the conductor gauge check + deploy the chain

## Problem (from the 2026-07-12 conductor self-handoff audit)

The 0.70 self-handoff never fired because (C-1/C-2) the conductor's gauge check is unenforced
prose that exists only inside kata-orchestrate's wave loop, and (D-1/D-2) the bridge/hook chain
is never deployed — the installer writes no host settings and the snippet has `<repo>`
placeholders. Live-confirmed: GSD owns the operator's statusLine, no PreCompact hook, no bridge
file ever written.

## LOCKED decisions

- **CG-L1 — Mechanical gauge check: NEW `adapters/claude/hooks/kata-gauge-check.py`, a
  UserPromptSubmit hook.** Reads the hook stdin JSON (`session_id`, `cwd`), locates the kata
  bridge `kata-ctx-<session_id>.json` under **`tempfile.gettempdir()`** (the writer's exact
  resolution, `kata_statusline.py:289` — freeze-gate F-8; never a raw `%TEMP%` env read), calls
  `kata_gauge.read_bridge`/`resolve_gauge`/`trigger_crossed` (existing tested engine — finally
  wired). **Kata-scope gate (freeze-gate F-3, mandatory):** inject ONLY when the stdin `cwd`
  shows kata-run evidence (a `.kata/` dir or `kata.config` file at or above cwd, bounded
  upward walk); otherwise silent exit 0 — a global hook must not push kata directives into
  non-kata sessions. **Once-per-crossing dedupe (F-3):** a sidecar marker
  `kata-gauge-notified-<session_id>.json` (same temp dir) records the last-notified fraction;
  re-inject only when the fraction has grown ≥ 0.05 since the last notification. When crossed
  ⇒ emits `hookSpecificOutput.additionalContext`: a one-line `[KATA CONTEXT GAUGE]` directive
  telling the conductor its context fraction and to execute `kata-selfhandoff` at the next task
  boundary. Below threshold or ANY failure ⇒ silent exit 0; the hook is structurally guaranteed
  to **never exit 2** (UserPromptSubmit exit 2 blocks and erases the user's prompt — F-8): the
  entire body runs under one try/except that exits 0. This makes the conductor check MACHINERY
  on every user turn — session-shape-independent (fixes C-2), model-memory-independent (fixes
  C-1). Grounding: a `UserPromptSubmit` stdin-fields + `additionalContext` entry is added to
  the adapter grounding registry and VERIFIED during smoke (freeze-gate F-9).
- **CG-L2 — Consent-gated deployment: `kata_install.py --install-hooks` (+
  `--uninstall-hooks`), merge engine in NEW `tools/kata_host_settings.py` (freeze-gate F-7):**
  pure, independently-testable `merge_host_settings(existing: dict, rendered: dict) -> dict` /
  `unmerge_host_settings(...)` / render helpers live in the new module; `kata_install.main`
  gains ONLY flag wiring. **The five frozen `kata_install.py` engine functions
  (`_flat_link_skills`, `_link_or_copy`, `install`, `copy_project`, `confirm_platform`) stay
  byte-identical** (the CA-L43 precedent pin, restated here). Renders `settings.snippet.json`
  with RESOLVED paths (no `<repo>` placeholders; python executable = the venv when present
  else `python`), then merges into `~/.claude/settings.json`: strict fail-closed read with
  `encoding="utf-8-sig"` (BOM-tolerant lossless read; unparseable ⇒ abort with a
  BOM-vs-corruption-distinguishing error, never guess — D136, freeze-gate F-11); timestamped
  backup written first (law-6-legal: never compared); atomic temp+replace write; idempotent
  (re-run ⇒ no-op). Hook entries APPEND (never remove/reorder existing hooks). statusLine:
  absent ⇒ set kata's; present+chain-eligible (statusline_chain.py pin) ⇒ wrap via the chain
  (`-- <user-command>`, user output byte-identical, CA-L1 never-clobber); present+ineligible
  (shell metacharacters incl. backslashes, or .bat/.cmd argv[0] — likely for Windows commands)
  ⇒ SKIP statusline, report it, still install hooks. `--uninstall-hooks` removes exactly kata's
  entries and unwraps the chain back to the user's original command. NEVER runs implicitly —
  explicit flag only, prints the settings diff, requires confirmation (`--yes` for headless).
  **The consent text explicitly discloses that these are GLOBAL hooks affecting every Claude
  Code session on the machine, with the F-3 kata-scope gate as the containment** (freeze-gate
  note). This is the executable "bootstrap slot 6" that was previously prose-only (fixes
  D-1/D-2).
- **CG-L3 — Snippet gains the gauge-check hook** (UserPromptSubmit) alongside the existing
  SessionStart/PreCompact entries, same `<repo>` templating, resolved by CG-L2.
- **CG-L4 — Router-stanza fixes (A2/A3).** `kata_router.render_stanza` / `write_stanza`
  (the actual API — freeze-gate F-9) gain an optional `home` param (default `~/.kata-home`)
  that templates the prime-directives back-pointer in `_STANZA_BODY` (fixes the hard-coded
  path under custom `KATA_HOME`); call sites updated; the orphan-marker data-loss guard and
  its pinned tests are untouched. Stanza start-verb becomes `/kata-start` (kata-initiate, the
  canonical front door) with kata-bootstrap named as the pre-loop configurator (fixes the
  entrypoint drift).
- **CG-L5 — Doc-truth (A4/F3).** STANDARDS §4: non-Claude adapter normalization marked
  *(planned — only `adapters/claude/` ships today)*. kata_settings docstring aligned with the
  now-real learnFeed seeding (SB-L7).
- **CG-L6 — Honest-claim reword.** Anywhere the docs state the conductor "watches its own
  gauge" as present-tense fact for arbitrary sessions, scope it to the deployed-chain
  condition (post `--install-hooks`); R6 (live host-fired compaction) stays a named-open leg
  until proven — this build makes it PROVABLE on this machine, it does not claim it proven.
- **CG-L7 — Smoke (this session).** (a) Unit+integration tests for the hook (arranged bridge
  file → crossed/not-crossed/absent/corrupt/non-kata-cwd/dedupe ⇒ correct additionalContext or
  silent-0; never-exit-2 proven). (b) Installer merge dry-run against a COPY of the operator's
  real settings.json proving: hooks appended, idempotency, backup, uninstall round-trip, and
  the statusLine outcome **conditional on `is_chain_eligible(actual GSD command)`** (freeze-gate
  F-6): eligible ⇒ chain-wrapped byte-identical passthrough; ineligible (expected for the
  Windows node+backslash command) ⇒ SKIP-reported + statusline untouched + hooks still
  installed. (c) LIVE install into the operator profile ONLY with explicit operator consent at
  the moment of execution (it edits their working settings.json).

## Out of scope (named)

PostToolUse-cadence gauge checks (UserPromptSubmit only in v1; noted as a follow-on if turn-
internal growth proves under-sampled); auto-compact window writes (backstop stays
recommend-only per C-4 — a separate decision); non-Claude platform hook parity; R6 attended
live-proof execution (enabled by this build, run when the operator chooses).
