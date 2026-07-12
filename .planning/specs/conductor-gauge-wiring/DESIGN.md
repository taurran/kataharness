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
  UserPromptSubmit hook.** Reads the hook stdin JSON (`session_id`), locates the kata bridge
  (`%TEMP%/kata-ctx-<session_id>.json`), calls `kata_gauge.read_bridge`/`resolve_gauge`/
  `trigger_crossed` (existing tested engine — finally wired). When crossed ⇒ emits
  `hookSpecificOutput.additionalContext`: a one-line `[KATA CONTEXT GAUGE]` directive telling
  the conductor its context fraction and to execute `kata-selfhandoff` at the next task
  boundary. Below threshold or any failure ⇒ silent exit 0 (fail-soft — never break the host;
  the gauge engine itself stays fail-closed internally per v0.2.1). This makes the conductor
  check MACHINERY on every user turn — session-shape-independent (fixes C-2: no dependence on
  the orchestrate wave loop), model-memory-independent (fixes C-1).
- **CG-L2 — Consent-gated deployment: `kata_install.py --install-hooks` (+
  `--uninstall-hooks`).** Renders `settings.snippet.json` with RESOLVED paths (no `<repo>`
  placeholders; python executable = the venv when present else `python`), then merges into
  `~/.claude/settings.json`: strict fail-closed read (unparseable ⇒ abort, never guess — D136);
  timestamped backup written first; atomic temp+replace write; idempotent (re-run ⇒ no-op).
  Hook entries APPEND (never remove/reorder existing hooks). statusLine: absent ⇒ set kata's;
  present+chain-eligible (statusline_chain.py pin) ⇒ wrap via the chain (`-- <user-command>`,
  user output byte-identical, CA-L1 never-clobber); present+ineligible ⇒ SKIP statusline,
  report it, still install hooks. `--uninstall-hooks` removes exactly kata's entries and
  unwraps the chain back to the user's original command. NEVER runs implicitly — explicit flag
  only, prints the settings diff, requires confirmation (`--yes` for headless). This is the
  executable "bootstrap slot 6" that was previously prose-only (fixes D-1/D-2).
- **CG-L3 — Snippet gains the gauge-check hook** (UserPromptSubmit) alongside the existing
  SessionStart/PreCompact entries, same `<repo>` templating, resolved by CG-L2.
- **CG-L4 — Router-stanza fixes (A2/A3).** `kata_router.render` takes the resolved harness
  home (default `~/.kata-home`) and templates the prime-directives back-pointer from it
  (fixes the hard-coded path under custom `KATA_HOME`); stanza start-verb becomes
  `/kata-start` (kata-initiate, the canonical front door) with kata-bootstrap named as the
  pre-loop configurator (fixes the entrypoint drift).
- **CG-L5 — Doc-truth (A4/F3).** STANDARDS §4: non-Claude adapter normalization marked
  *(planned — only `adapters/claude/` ships today)*. kata_settings docstring aligned with the
  now-real learnFeed seeding (SB-L7).
- **CG-L6 — Honest-claim reword.** Anywhere the docs state the conductor "watches its own
  gauge" as present-tense fact for arbitrary sessions, scope it to the deployed-chain
  condition (post `--install-hooks`); R6 (live host-fired compaction) stays a named-open leg
  until proven — this build makes it PROVABLE on this machine, it does not claim it proven.
- **CG-L7 — Smoke (this session).** (a) Unit+integration tests for the hook (arranged bridge
  file → crossed/not-crossed/absent/corrupt ⇒ correct additionalContext or silent-0). (b)
  Installer merge dry-run against a COPY of the operator's real settings.json proving: GSD
  statusline chain-wrapped byte-identical passthrough, hooks appended, idempotency, backup,
  uninstall round-trip. (c) LIVE install into the operator profile ONLY with explicit operator
  consent at the moment of execution (it edits their working settings.json).

## Out of scope (named)

PostToolUse-cadence gauge checks (UserPromptSubmit only in v1; noted as a follow-on if turn-
internal growth proves under-sampled); auto-compact window writes (backstop stays
recommend-only per C-4 — a separate decision); non-Claude platform hook parity; R6 attended
live-proof execution (enabled by this build, run when the operator chooses).
