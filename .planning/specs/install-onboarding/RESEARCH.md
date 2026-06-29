---
title: "Install / Onboarding Final Polish — RESEARCH (grill-resolved, frozen approach)"
status: FROZEN (2026-06-29) — grill COMPLETE; every fork below is RESOLVED and LOCKED by the operator
spec: install-onboarding
feature: "Feature 2 — install/onboarding final polish"
builds-on: .planning/specs/install-portability/DESIGN.md (FROZEN 2026-06-26 — the engine this layer sits ON TOP of)
load-bearing-constraint: >-
  "We REALLY REALLY need to be sure we aren't changing anything that's already working.
  Only if there are drastic oversights." EVERY change is ADDITIVE / backward-compatible.
  Only G3 + G4 touch a working skill, and only as ADDITIVE STEPS — never rewrites.
tags: [research, install, onboarding, headless, additive, frozen]
---

# Feature 2 — Install / Onboarding Final Polish · RESEARCH

This research is **closed**. The grill is complete; the operator has LOCKED every decision. This file
records the resolved approach and ties it to the established transcript themes so the freeze-gate reviewer
can see *why* each fork landed where it did. It does **not** re-open anything.

## 0. The standing constraint (repeated, load-bearing)

> *"We REALLY REALLY need to be sure we aren't changing anything that's already working. Only if there are
> drastic oversights."*

Feature 2 is a **polish/portability layer that sits ON TOP of the shipped install engine**
(`install-portability`, FROZEN 2026-06-26). The engine — `tools/kata_install.py`,
`tools/kata_settings.py`, `tools/project_find.py` — is **not rewritten**. New files (`install.sh`,
`install.ps1`, the uninstaller, `tools/kata_router.py`) and **additive-only** extensions (new CLI flags,
new exit-code mapping, an optional INTENT field, two additive skill steps) layer on. The 18 working
patterns (DESIGN §don't-break) stay byte-untouched on their existing code paths.

## 1. The grill forks — all RESOLVED

| Fork | Options weighed | RESOLVED (LOCKED) |
|---|---|---|
| **Install delivery** | curl\|sh one-liner · npm/pipx/uv · git-clone · "Use this template" | **BOTH** one-liners (POSIX `install.sh` via `curl … \| sh`, Windows `install.ps1` via `irm … \| iex`) **AND** a documented git-clone path **AND** "Use this template". Not either/or — the one-liners *wrap* clone+engine. |
| **Where install logic lives** | reimplement in shell · keep in Python | **Keep in Python.** The shells are thin bootstraps that clone/seed then invoke the EXISTING `tools/kata_install.py`. No install logic is duplicated in bash/PowerShell (this is also what makes PS parity cheap — see §4). |
| **Clean install** | "just works" · idempotent + uninstallable | **Idempotent + UNINSTALLABLE.** Idempotent (re-run = same state; guarded appends), version-pinnable, no cruft, **and ship an uninstaller** that reverses every change including the G4 router stanza. The uninstaller is the single most-cited gap in the research; it is now in scope. |
| **Headless scope** | install+setup only · full autonomous loop | **Install + SETUP ONLY.** Headless covers install and the 2-setting setup. The build loop's human gates (commit/merge/fix-approval) STAY human. A true autonomous-loop mode is **explicitly DEFERRED / off-by-default**. |
| **Exit codes** | 0/1 only (today) · semantic set | **Semantic exit codes**, additively mapped in `main()` (0 success/idempotent-no-op · 2 usage · 3 not-found · 4 permission · 5 conflict). Idempotent re-install = exit 0 no-op; a non-kata-dir collision = exit 5 CONFLICT. |
| **Machine output** | mixed stdout (today) · `--json` channel split | **`--json`**: machine JSON to **stdout**, human notes to **stderr**. Default (no `--json`) keeps today's mixed-stdout behavior (BC). |
| **Grill-for-goals (G3)** | rewrite the mirror · add a step | **ADD a step** inside the existing reflective mirror: enumerate + confirm checkable ACCEPTANCE/SUCCESS criteria. The S2 anti-drift STOP gate is **preserved** (each criterion individually confirmed; blanket "looks good" fails). |
| **Acceptance criteria storage** | overload `readiness`/`features` · new field | **New OPTIONAL `acceptanceCriteria: string[]`** on the INTENT schema — additive, BC (absent ⇒ today's behavior). `readiness` is prose and `features`/`fixes` are scope; neither is a checkable criteria list, so a minimal additive field is the honest fit. |
| **Router stanza (G4)** | force-write · offer · skip | **OFFER** (human-gated, never forced) a small, marked, idempotent, opt-in stanza into the target project's `AGENTS.md`. `CLAUDE.md` stays a pointer. The uninstaller removes exactly the marked block. |

## 2. Synthesis tied to the transcript themes (established, folded in)

- **One-command install tradeoffs** — `curl|sh` optics = an unaudited remote script. **Mitigations adopted:**
  a **stable URL**, **readable-before-run** (the script is short, pinned, and printed/inspectable),
  **version-pin** (`KATA_REF` env / `--ref`), and a documented **checksum** path. README states the tradeoff
  **honestly** (it does not pretend `curl|sh` is risk-free). npm/pipx/uv/clone are *also* offered as the
  audit-friendly alternatives for users who decline the one-liner.
- **"Clean install" = idempotent + no cruft + UNINSTALLABLE.** Idempotent via `mkdir -p`-style creation and
  a **`grep -qF` guard before any append** (here realized as a marked-block write in `kata_router`, so the
  guard lives in tested Python, not duplicated shell). No cruft = no stray `.git`/temp left behind by the
  bootstrap. UNINSTALLABLE = the shipped uninstaller reverses skill links, the plugin manifest, the settings
  file, and the marked router stanza. *Honoring the most-cited gap.*
- **GitHub seeding** — clone / degit / **"Use this template"** all documented; the one-liner uses clone (or
  reuses an existing `$KATA_HOME`) then hands off to the engine.
- **Agent-friendly headless** — **non-TTY auto-skip** (when `stdin` is not a TTY, behave non-interactively) +
  explicit **`--yes` / `--non-interactive`** + **`--answers-json <path>`** to supply all setup values up front
  + **SEMANTIC EXIT CODES** (incl. CONFLICT=already-installed semantics) + **`--json` to stdout (human to
  stderr)** + **env-var config** (`KATA_HOME` exists; add `KATA_PARENT_DIR`/`KATA_VAULT_DIR` fallbacks) +
  **idempotent declarative verbs** (install / uninstall) + **`--help` with real examples**. Scope is INSTALL+
  SETUP; the loop's human gates are untouched.
- **Goal-elicitation = semi-structured** — openers → a coverage checklist → capture explicit **success /
  acceptance criteria** → reflective confirm-or-edit. This is exactly the additive G3 step: the existing
  mirror already does openers + reflect-and-edit; we add the **explicit acceptance-criteria enumeration +
  per-criterion confirmation**, start-with-the-end-in-mind.
- **Router file IS the per-project system prompt AND a router; `AGENTS.md` is the portable standard;
  instruction budget ~150–200 reliably-followed lines** — therefore the G4 stanza is **~12–15 lines,
  pointer-style** (what's installed · entrypoints · where state lives), **points to folders, not inline
  detail**, and `AGENTS.md` is canonical while `CLAUDE.md` stays a thin pointer (STANDARDS §4).
  The "system prompt" concept is **ALREADY SOUND** (assessed) — G4 adds only the marked stanza.

## 3. Transcript themes honored (the spine of *why*)

- **router-as-system-prompt** → G4 writes the project router stanza (marked, minimal, opt-in).
- **tool-agnostic files+folders** → the stanza + state-locations are file/folder pointers; `AGENTS.md`
  canonical, portable across hosts.
- **start-with-the-end-in-mind** → G3 captures acceptance criteria *before* the build, frozen into INTENT.
- **grill-for-goals** → G3 strengthens the goal mirror with checkable success criteria, S2 gate preserved.
- **simplest-level-that-fits** → install logic stays in one Python engine; shells are thin; the stanza is tiny;
  the schema gains exactly one optional field. No taxonomy, no installer-interface cathedral (consistent with
  `install-portability` IP-D "keep it simple").
- **routing-is-make-or-break** → the headless surface uses semantic exit codes + `--json` so an orchestrating
  agent can branch correctly; the project router stanza makes a fresh agent find the harness in any repo.

## 4. Cross-platform / PowerShell-parity research (Windows host)

This is a Windows 11 host with **Git Bash + PowerShell** both available — so both bootstrap scripts are
testable here. The parity strategy: **all stateful + idempotent logic lives in Python** (the engine,
`kata_router`, the uninstall verb); the shells only (a) locate/clone the home and (b) invoke the engine with
pass-through flags. This eliminates bash-isms-vs-PowerShell drift by construction — there is no second
implementation to keep in sync. PowerShell rules observed in the design: no `NUL`/`%VAR%` (use `$env:VAR`),
no here-string column-0 traps, `irm | iex` documented with the same honesty caveat as `curl | sh`. Residual
parity risk (carried to the reviewer): a true `curl|sh` / `irm|iex` *network* fetch can only be smoke-tested
against a local file:// or fixture URL in CI — the live remote-fetch path is **exercised, not automatically
proven** (persona.md honesty posture). See PLAN smoke gate.

## 5. What is explicitly NOT in scope (deferred / off)

- **Autonomous-loop mode** (headless past setup, through commit/merge/fix) — DEFERRED, off-by-default.
- **Codex/Kiro verified install** — stays **best-effort / honest-scoped** ("verify in-host"), as already
  shipped (`kata_install.py:12-14`, `docs/SETUP.md:26-27`). Not a blocker for Feature 2.
- **Full plugin-marketplace publishing**, non-Obsidian vault formats — out of scope (inherited from
  `install-portability/BRIEF.md` "Out of scope").
