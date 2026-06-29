---
name: kata-onboard
description: >-
  First-run on-ramp (LD13): detect a fresh KataHarness install, OFFER a Debug-Mode run on the user's
  repo, and — only on a successful, human-approved closeout — OFFER to convert the repo to the loop
  (kata.config + vault binding + committing the left-behind characterization suite + a minimal
  .planning/ scaffold) and a follow-on version-up/sprint. Composes built install-portability tools and
  the initiate/bootstrap/closeout/loop skills; reimplements nothing. Invoke on a fresh install when no
  kata.config / INTENT.md exists at the target.
license: Apache-2.0
version: 0.2.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Write, AskUserQuestion]
source: >-
  new (KataHarness original, Debug-Mode P3 / LD13 — DESIGN R6/LD13); a NEW composition of the BUILT
  install-portability surfaces (tools/kata_settings.py, tools/project_find.py, tools/kata_install.py,
  tools/intent_scaffold.py) + the initiate/bootstrap/closeout/loop spine skills. "convert-to-loop" and
  the ".planning/ scaffold" are NEW here (see "What is NEW", below), not a reused convert flow.
tags:
  - kata/coordinate
  - kata/spine
  - onboarding
---

# kata-onboard — first-run on-ramp (offer Debug Mode → offer convert-to-loop)

The dedicated **first-run path** (DESIGN R6 / LD13). A developer has just installed KataHarness and points
it at an existing repo. This skill is the on-ramp: it **detects** the fresh install, **offers** a
Debug-Mode run, and — only after that run reports success **with the human's approval** — **offers** to
convert the repo to the loop and bind a vault. It is a thin **coordinate wrapper**: every capability below
is delegated to a skill or tool that already exists. It **composes — never reimplements**.

Voice throughout: read `protocol/persona.md`. Plain-language, outcome-first, warm through clarity. Never
surface internal stage names. **Never overclaim** (see "Honesty — read before offering anything").

> **Not the only entry.** For a normal Kata Loop run start from the [[kata-loop]] conductor (or
> [[kata-initiate]] / [[kata-bootstrap]] directly). `kata-onboard` is purely the **first-run** convenience
> layer; it adds no capability those skills don't already own. Direct use of the spine skills stays valid
> and unchanged (BC: onboarding is optional).

---

## Honesty — read before offering anything (mandatory)

State these plainly to the user; never paper over them.

- **Debug Mode is OFFERED, never auto-run.** This skill proposes a debug run and waits for an explicit
  yes. It starts nothing on its own.
- **convert-to-loop is HUMAN-GATED, never autonomous.** Writing `kata.config`, binding the vault, and
  **committing the left-behind characterization suite** all happen only on explicit human approval. The
  suite commit rides [[kata-closeout]]'s existing **human-gated Decision 2** git actions — there is **no
  new git path** here, and nothing is committed, pushed, or merged autonomously.
- **The Claude install path is the verified one.** Per install-portability's build note, the Claude host
  is the path that has been exercised; **Codex / Kiro are best-effort and documented (IP-D)**, not a
  verified cross-host install. Say so; never imply a verified install on a non-Claude host.
- **n=0 live.** Debug Mode — and therefore this onboarding flow — **has never been exercised end-to-end on
  a real fresh install**. The path is proven only on seeded fixtures. Do not imply a real first-run
  conversion has happened.

## What is NEW here (not phantom reuse — `protocol/reuse-claims.md`)

Two pieces below are **NEW compositions/prose**, scoped honestly so they are not disguised as reuse:

- **`convert-to-loop`** is a **NEW composition** — there is **no single existing "convert flow" surface**.
  It is this skill orchestrating already-built surfaces (`kata_settings.*`, [[kata-bootstrap]],
  [[kata-closeout]], [[kata-loop]]) in a new sequence. Do not relabel it "reuses the existing convert flow."
- **The `.planning/` scaffold** is **NEW skill-prose** — no scaffolder tool exists (unlike
  `intent_scaffold.write_intent`, which scaffolds `INTENT.md`, not `.planning/`). The layout is created by
  this skill's own `Write` calls into the target tree (no subprocess, no new Python).

Every **other** cited surface below resolves to a real symbol/skill (verified per `protocol/reuse-claims.md`).

---

## Step 1 — detect a fresh install

A fresh install is: **settings present** (the installer wrote them) but **no `kata.config` and no
`INTENT.md`** at the target.

- Read settings via **`kata_settings.read_settings`** (`tools/kata_settings.py`); locate the install root
  via **`kata_settings.harness_home`**; read the machine's confirmed hosts via
  **`kata_settings.confirmed_platforms`** (`tools/kata_settings.py`). An empty/absent settings dict means
  the installer hasn't run — surface that and stop (nothing to onboard yet).
- Check the target tree for an existing `kata.config` (branch root) and `INTENT.md`. **If either exists,
  this is not a fresh first run** — defer to [[kata-loop]] / [[kata-bootstrap]] (re-entrant config) and do
  not re-onboard.

If settings are present and both `kata.config` and `INTENT.md` are absent ⇒ proceed to Step 2.

## Step 2 — offer Debug Mode (offered, not auto-run)

Offer — don't start — a Debug-Mode run on the user's repo. On an explicit yes, route through the front door
**[[kata-initiate]]** (`modules/initiation/kata-initiate/SKILL.md`), which already owns:

- **classify kind + target/platform/vault configuration**;
- **project find → confirm** via **`project_find.find_projects`** (`tools/project_find.py`);
- **copy-mode** (import-a-copy for untrusted/large repos) via **`kata_install.copy_project`**
  (`tools/kata_install.py` — a plain `shutil` copy, **never git**); platform confirmation via
  **`kata_install.confirm_platform`**.

Steer `kind` / run-shape to **debug** so that, downstream, **[[kata-bootstrap]]**
(`skills/coordinate/kata-bootstrap/SKILL.md`, the Phase-3 config writer) writes `kata.config` from the
**debug preset** (`skills/coordinate/kata-bootstrap/resources/run-shapes.md`): `runShape: "debug"`,
`target.kind: "existing"`, and `modules` including **`kata/module/debug`** — the marker the entire debug
pipeline gates on. Bootstrap then launches the run via [[kata-orchestrate]]; this skill does **not** run
the debug pipeline itself.

> Onboarding does not fork initiate/bootstrap. It hands them the steered intent and lets them do their job.

## Step 3 — on success, offer convert-to-loop + vault setup (human-gated)

**Only after** the debug run's closeout reports success do you offer to convert the repo to the loop. This
whole step is **human-gated**; present it as a set of opt-in actions, each confirmed before it happens.

1. **`kata.config` for ongoing loop use** — written by **[[kata-bootstrap]]** (the config writer; re-entrant
   reconfigure path), now for a normal loop run rather than a one-off debug pass.
2. **Vault binding** — bind the user's vault by persisting the **`vaultDir`** setting via
   **`kata_settings.write_settings`** (validates `vaultDir` is an existing dir at the persistence boundary)
   / previewed with **`kata_settings.build_settings`** (`tools/kata_settings.py`; install-portability IP-A).
3. **Commit the left-behind characterization suite** *(human-gated; never autonomous)* — the debug run
   leaves a generated characterization suite in the target repo (authored there by `kata-characterize` in
   P2b). Surface committing it through **[[kata-closeout]]**'s existing **human-gated Decision 2** git
   actions (`modules/closeout/kata-closeout/SKILL.md` — "Carry out git actions only on explicit human
   approval"). **No new git path** is introduced; the suite commit rides the same behavioral guard as
   commit/push/merge.
4. **Scaffold `.planning/`** *(NEW skill-prose — see "What is NEW")* — create the minimal `.planning/`
   layout in the target tree with this skill's own `Write` (no scaffolder tool exists; no subprocess). For
   `INTENT.md` itself, the existing **`intent_scaffold.write_intent`** (`tools/intent_scaffold.py`,
   `..`-guarded writer) is the surface — `.planning/` is the NEW part.
5. **Offer a follow-on version-up / sprint** — hand the follow-on disposition to the **[[kata-loop]]**
   conductor's **loop-back** (`skills/coordinate/kata-loop/SKILL.md`, Decision-3 path), matching LD12's
   offered handoff. **Offered, never auto-started.**
6. **Write a KataHarness router stanza into `AGENTS.md`** *(offered — never forced)* — offer, via
   `AskUserQuestion`, to write a compact marked block into the **target project's** `AGENTS.md`. State
   plainly to the user: "I can add a short KataHarness section to your project's AGENTS.md — it names
   what's installed, the two entrypoints (`kata-bootstrap`, `kata-validate`), and the four run-state
   locations. This writes only to your project's AGENTS.md, and only with your explicit yes." On an
   explicit yes, call **`kata_router.write_stanza(<target_path>/AGENTS.md)`** (`tools/kata_router.py`,
   `..`-guarded idempotent upsert — Slice A) as executed Python, the same convention as
   `intent_scaffold.write_intent` at item 4: creates the file if absent; upserts the
   `<!-- kata:begin -->…<!-- kata:end -->` block in place if present; re-running is a no-op (exactly one
   block, never duplicated). `CLAUDE.md` stays a pointer and is **never touched**. **On decline,
   no-op — `AGENTS.md` is left exactly as found.** The uninstaller
   (`kata_install --uninstall --target-dir <project>`) reverses exactly this block via
   `kata_router.remove_stanza` (DESIGN §2.2 / Slice C).

Each action is presented for explicit approval; declining any one leaves the rest untouched. If the debug
run did **not** succeed, do **not** offer conversion — report the outcome honestly and stop.

---

## What this skill does NOT do

- It **adds no execution sink** (`protocol/exec-safety.md`): it composes only **sink-free / registered /
  human-gated** surfaces — `kata_install.copy_project` (`shutil`, never git), `kata_settings.*` (pure
  builders + boundary-validated writers), `project_find.find_projects` (pure search),
  `intent_scaffold.write_intent` (`..`-guarded writer), `kata_router.write_stanza`
  (`..`-guarded, idempotent upsert), and the **already human-gated** git actions that live in
  [[kata-closeout]]. The `.planning/` scaffold is a skill `Write`, not a subprocess.
- It introduces **no new installer Python** and **no new run-shape** — it steers existing config writers.
- It **never gates** and never runs the debug pipeline — [[kata-evaluate]] owns the gate; the orchestrator
  owns the run.

## Reuse map (verified — cite by name, `protocol/reuse-claims.md`)

| Surface | Resolves at | Role here |
|---|---|---|
| `kata_settings.read_settings` / `harness_home` / `confirmed_platforms` | `tools/kata_settings.py` | detect fresh install |
| `kata_settings.write_settings` / `build_settings` (`vaultDir`) | `tools/kata_settings.py` | vault binding |
| `project_find.find_projects` | `tools/project_find.py` | project find→confirm (via initiate) |
| `kata_install.copy_project` / `confirm_platform` / `install` | `tools/kata_install.py` | copy-mode / platform confirm (via initiate) |
| `intent_scaffold.write_intent` | `tools/intent_scaffold.py` | `INTENT.md` scaffold |
| [[kata-initiate]] | `modules/initiation/kata-initiate/SKILL.md` | front door: kind/target/platform/vault + find + copy-mode |
| [[kata-bootstrap]] | `skills/coordinate/kata-bootstrap/SKILL.md` | writes `kata.config` (runShape/target/modules; debug preset) |
| [[kata-closeout]] | `modules/closeout/kata-closeout/SKILL.md` | human-gated Decision 2/3 git actions + suite commit |
| [[kata-loop]] | `skills/coordinate/kata-loop/SKILL.md` | loop-back / offered version-up |
| **`convert-to-loop`** | **NEW** (this skill) | composition, not a single existing surface |
| **`.planning/` scaffold** | **NEW** (this skill, `Write`) | skill-prose, no scaffolder tool |
| **`kata_router.write_stanza`** | **NEW** (`tools/kata_router.py`) | router stanza upsert into target `AGENTS.md` (item 6) |
