---
title: "Install & Portability — FROZEN DESIGN (the simple model)"
status: FROZEN (2026-06-26) — compiled from GRILL-LEDGER.md after operator simplification
spec: install-portability
scope: central install + 2-setting config + per-run project search + copy mode + simple per-platform install (Claude verified; Codex/Kiro best-effort; Quick = own installer)
supersedes: the jargon-cathedral binding/contract framing in early GRILL-LEDGER (course-corrected 2026-06-26)
---

# Install & Portability — FROZEN DESIGN

> Plain model (operator-specified): KataHarness lives in one central place and installs into the platform there.
> It remembers **two settings** and, **each run**, finds the project to work on. That is the whole feature.

## 1. Requirements
- **R1** One central install; installs into the platform from there (multi-platform — needed before benchmarking).
- **R2** Remember **two settings**: default parent project folder (overridable per run) + vault location (second brain).
- **R3** Each run: ask project **name + rough location** → **search** under the parent → **confirm** the match → use it.
- **R4** **Copy mode** (Debug Mode import-a-copy): also ask a destination folder; work on the copy, leave original alone.
- **R5** Absent settings ⇒ in-repo behavior unchanged (BC1).
- **R6** Keep it simple — no config-resolution system, no installer-interface taxonomy.

## 2. Components (NEW, this build)
- **`tools/kata_settings.py`** — read/write the central settings file; self-locate harness home (`$KATA_HOME` override).
  Settings = `{ settingsVersion: 1, parentDir, vaultDir }`. Pure builders + thin `_safe_path`-guarded writers.
- **`tools/project_find.py`** — given (name, parentDir, optional rough-location), return ranked candidate dirs.
  Pure search (glob/walk under parent, case-insensitive name match, prefer exact); returns a list (0/1/N) for the
  skill to confirm. No prompts in the tool (the skill drives confirm).
- **`tools/kata_install.py`** — the installer. `install(platform, harness_home, host_dir=None)`: registers the skills
  with the host per platform. (Settings are recorded by the CLI when `--parent-dir` is passed, else by `kata-initiate`
  on first run — `install()` itself does not write settings.) Dispatch by platform: `claude` (real),
  `codex`/`kiro` (best-effort, documented), `quick` (no-op — brings its own installer), unknown (generic: print
  manual steps + copy SKILL.md location). Per-platform logic lives in `adapters/<platform>/` (mirrors existing layout).
- **`.claude-plugin/plugin.json`** — Claude plugin manifest at repo root (name `kata`, description, version) so the
  harness entry is discoverable; the Claude installer links the repo into `~/.claude/` (symlink, copy fallback on Windows).
- **`docs/SETUP.md`** — cordoned setup doc (the three install paths + per-platform + `$KATA_HOME`); README carries a pointer only.
- **`kata-initiate` SKILL.md** — prose: the per-run name+location→search→confirm step + copy-mode destination prompt
  (extends the existing target step; reuses `project_find`). The settings seed `kata.config` path-fields (config.md:22/25/26).

## 3. LOCKED decisions (from the ledger)
- **IP-A** One central install + a small settings file (2 settings: parentDir, vaultDir); seeds kata.config; absent ⇒ in-repo (BC1).
- **IP-B** Per-run project find = name + location → search under parent → confirm; multiple→list, none→type path. Extends kata-initiate.
- **IP-C** Copy mode asks a destination folder; operates on the copy; original untouched.
- **IP-D** Multi-platform = one small install script per platform under `adapters/<platform>/`; Claude built+verified,
  Codex/Kiro best-effort (testability caveat: not verifiable without those hosts), Quick brings its own.
- **Dropped (do not resurrect):** two-layer machine+workspace binding · `~/.kata` registry · 4-level discovery chain ·
  version-scheme/path-encoding as questions · the three-path vault installer (→ one vaultDir setting).

## 4. Edges (resolved)
- Search: N matches → return the list (skill lists, user picks) · 0 → return empty (skill asks for full path) ·
  path-not-a-dir → reject/re-prompt.
- Copy: destination exists/non-empty → confirm-overwrite or pick another · destination == source → reject.
- Settings absent → in-repo defaults (BC1). Vault absent → learning is a no-op (today's BC).
- Windows symlink denied (no Developer Mode/admin) → fall back to copy; print a note.
- Unknown platform → generic manual-steps fallback.

## 5. Security (CLAUDE.md + project rules)
- New installer Python → **Snyk SCA scan**; operator-supplied paths are `..`-guarded (CWE-23) at every fs sink.
  **Scope note:** the `..`-guard rejects *traversal*, not destructive overwrite of a named absolute dir — so the
  destructive paths carry their own guards: skill-linking **refuses to clobber a non-kata directory** (a
  `.kata-managed` marker gates replacement), and `copy_project(overwrite=True)` is an **explicit opt-in**.
- **PokeVault is LOCAL-ONLY — the installer NEVER runs git** (structural: no `subprocess`/git import anywhere), so
  it can never git-touch a vault.
- Out-of-repo writes (`~/.claude/`, settings file): explicit, path-guarded, idempotent, non-clobbering.

## 6. Acceptance (default-FAIL, runnable)
- `kata_settings` round-trips the 2-setting file; self-locate finds harness home; `$KATA_HOME` overrides.
- `project_find` returns exact-match-first ranked candidates on a fixture tree; empty on no match; handles N matches.
- `kata_install` (claude) creates a valid `.claude-plugin/plugin.json` + links the harness discoverably (verified here);
  unknown platform prints manual steps; quick is a no-op; NO git invoked against any vault path (asserted).
- pytest green · validate_skills 36/0 · Snyk medium+ 0 on new Python · docs/SETUP.md exists + README points to it.

## 7. Testability seams
- `project_find` + `kata_settings` builders are pure → unit-testable on `tmp_path` fixtures.
- `kata_install` takes injectable `harness_home`/target dirs → testable against tmp dirs without touching real `~/.claude`.
- Per-platform dispatch testable by asserting the right adapter routine is selected + its dry-run plan.

## Build note (today)
Streamlined ceremony (operator time-pressure): TDD build directly, then the real gates (pytest · validate_skills ·
Snyk on new Python · fresh-context kata-evaluate). Claude path exercised end-to-end; Codex/Kiro ship documented
best-effort. Honest scope surfaced in the closeout.
