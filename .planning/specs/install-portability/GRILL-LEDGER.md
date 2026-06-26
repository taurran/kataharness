---
title: "Install & Portability — grill decision ledger"
status: GRILL DONE → DESIGN FROZEN → BUILT + REVIEWED (D98 SHIP-WITH-FIXES→fixed) 2026-06-26
spec: install-portability
build: tools/{project_find,kata_settings,kata_install}.py + tests · .claude-plugin/plugin.json · docs/SETUP.md · kata-initiate Phase 2d
gates: pytest 490 · validate_skills 36/0 · Snyk 0 medium+ · D98 adversarial review SHIP-WITH-FIXES (2 MAJOR + 2 MINOR fixed)
caveat: Claude verified end-to-end (36 skills link+discover); Codex/Kiro best-effort (not host-verifiable here); Windows install method=copy (symlink needs Developer Mode)
scope: FULL installer layer (D103) — workspace binding + 3 user paths + install contract + per-platform dispatch + docs/SETUP.md
grounding: scoping pass (Explore, file:line-cited) + protocol/config.md + modules/initiation/AGENTS.md + greater-loop/DESIGN.md §2/§8
note: selection UX is NOT in scope (already landed in kata-initiate Phase 2, the GL-R3c fold)
---

# Install & Portability — GRILL LEDGER

The running record of the grill (method: `skills/plan/kata-grill/RUBRIC.md`). One entry per resolved branch.
FREEZE (`kata-design-doc`) compiles this into the frozen DESIGN. LOCKED entries are drift if re-decided downstream.

## Phase 0 — decision tree (enumerated; ✔ = pre-resolved from docs/code, ◻ = open for the grill)

**A. The workspace-binding artifact (heaviest gap)**
- ◻ IP-A1 — Where does the binding physically live? (`~/.kata/` user-global · per-workspace dotfile · fold into kata.config · new top-level file)
- ◻ IP-A2 — Schema: which roots does it bind? (skills · planning · learn-feed · candidate-skills · state/.kata · vault)
- ◻ IP-A3 — Discovery: how does a run *find* it? (env var → cwd walk-up → ~/.kata → in-repo default; precedence)
- ◻ IP-A4 — Relationship to per-run `kata.config` (workspace-level WHERE vs run-level HOW; does binding seed config defaults?)
- ◻ IP-A5 — Versioning of the binding shape (so platform installers target a known contract version)

**B. The init flow / entry point**
- ◻ IP-B1 — Home for installer mechanics: new `kata-install` skill · extend `kata-bootstrap` Phase 0 · extend initiation module
- ◻ IP-B2 — Trigger + idempotency: first-run detection (no binding → install); re-run = reconfigure vs no-op
- ◻ IP-B3 — Interactive vs declarative (config-file-driven) vs both
- ◻ IP-B4 — Does install place files into the target, or only write a binding pointer? (copy/symlink/register)

**C. The three user paths**
- ◻ IP-C1 — PokeVault-link mechanics (link to the PokeVault *template/product*, NOT git the user's local vault — never-git rule)
- ◻ IP-C2 — BYO-vault: the *minimal functional vault* scaffold (exact folders + index files)
- ◻ IP-C3 — aim-each-folder: which folders are individually targetable + validation
- ✔ IP-C4 — Absent-binding fallback = run in-repo (today's behavior). RESOLVED by BC1 (`config.md:8`).

**D. Skill discovery (host-specific)**
- ◻ IP-D1 — How skills are discovered per platform (Claude plugin/`.claude/skills/` · Quick agents · Kiro/Codex adapters)
- ◻ IP-D2 — copy vs symlink vs pointer, per platform
- ◻ IP-D3 — Overlap with deferred "Plugin packaging" backlog — in v1 or not

**E. The stable install contract**
- ◻ IP-E1 — Exact postconditions any installer must produce (discoverable skills + valid binding — specified)
- ◻ IP-E2 — Contract versioning (ties IP-A5)
- ◻ IP-E3 — Conformance verification (a readiness-style gate / new check)

**F. Per-platform installer dispatch (the "full layer" delta)**
- ◻ IP-F1 — Dispatch mechanism (registry · `adapters/<platform>/install.*` convention)
- ◻ IP-F2 — Installer interface each adapter implements (the operation set)
- ◻ IP-F3 — Which platforms get a real installer in v1 vs stubbed behind the contract
- ✔ IP-F4 — Work-host (Quick) brings its OWN installer; core defines only the contract. RESOLVED (`AGENTS.md:42–46`, BRIEF).

**G. Doc cordoning**
- ◻ IP-G1 — `docs/SETUP.md` name + structure (README carries pointers only)
- ◻ IP-G2 — Content matrix (3 user paths × per-platform)

**H. Security / safety**
- ✔ IP-H1 — PokeVault LOCAL-ONLY never-git: installer MUST NOT run git against a PokeVault path. HARD constraint (user memory).
- ✔ IP-H2 — New installer Python → Snyk SCA + CWE-23 `_safe_path` guards (process requirement, CLAUDE.md).
- ◻ IP-H3 — Out-of-repo writes (~/.kata, user vault): path-safety + approval policy

**I. Backward-compat & sequencing**
- ✔ IP-I1 — Absent binding ⇒ in-repo unchanged (BC). RESOLVED (= IP-C4).
- ⏸ IP-I2 — kata-preflight fold-vs-separate-grill — DECIDED AT FREEZE (D103), not in this grill's Phase 1.
- ◻ IP-I3 — Forward-fit for multi-model / testing-model (they need to know where things live) — does the binding anticipate them now?

---

## Course-correction (2026-06-26, operator-directed)
The grill drifted into the "well-lit area": six branches all resolved within **section A (the binding file)** —
its location, layering, discovery precedence, schema, version — while the **load-bearing** branches (per-host
skill discovery, install-contract postconditions, the 3 user paths, the vault scaffold) stayed untouched. Per
operator call ("Collapse section A, re-aim"), the section-A detail is **demoted to one defaulted decision (IP-A)**
and the grill re-aims at the installer mechanics. The over-engineered machine-layer `~/.kata/harness.json` +
4-level precedence chain are **dropped** as v1 requirements (self-locate makes them near-redundant).

## THE MODEL (plain terms — operator-specified, replaces the jargon-cathedral)
KataHarness lives in one central place and installs itself into the platform there. It **remembers two settings**
and, **each run**, finds the project to work on. That's the whole feature.

**Two remembered settings (in a small settings file at the central install):**
1. **Default parent project folder** (e.g. `C:\Dev\Projects`) — where your projects live. Overridable per run.
2. **Vault location** — where the **second brain** sits (the learning component reads/writes here). Optional but
   important: projects typically sit inside the vault, and the learn-feed/candidate-skills dirs live under it.

**Each run (launch + preflight):**
- Ask the **project name + rough location** → **search** under the parent folder → **show the match to confirm**.
- **Multiple matches** → show the list, user picks. **No match** → user types the full path.
- The confirmed folder = the codebase for this run.
- **Copy mode** (Debug Mode's import-a-copy, DG-10c) → also ask the **destination folder** first; work on the
  copy, leave the original untouched.

## Resolved branches (LOCKED ledger)

### IP-A — One central install + a small settings file (2 settings) · LOCKED
- **Decision:** KataHarness installs once, centrally, into the platform. A small settings file (at the central
  install) remembers (1) the default parent project folder and (2) the vault location. These **seed** the
  per-run `kata.config` path-fields (`target.path`, `engram.learnFeed.dir`, `agentSkills.dir` — `config.md:22/25/26`);
  a run may override. No binding present ⇒ in-repo behavior (BC1) unchanged.
- **Rationale:** Remembers where projects + the second brain live without inventing a config-resolution system.
- **Edges:** vault absent ⇒ no second-brain dirs (learning is a no-op, today's BC1). Parent overridable per run.
- **Dropped (do not resurrect at freeze):** two-layer machine+workspace binding; `~/.kata` registry; 4-level
  discovery precedence chain; version-scheme/relative-vs-absolute as user questions; the three-path vault installer
  (PokeVault-link / BYO-scaffold / aim-each-folder) → collapsed to "one vault-location setting."

### IP-B — Per-run project find = name + location → search → confirm · LOCKED
- **Decision:** Preflight prompts project name + rough location, searches under the default parent folder, and
  shows the match to confirm. Multiple matches → pick from a list; no match → type the full path. Confirmed folder
  is the run's codebase. Lives in the initiation/preflight flow (extends `kata-initiate`'s existing target step,
  not a separate skill).
- **Rationale:** The plain operator model; reuses the existing target-selection seam.
- **Edges:** ambiguous name (several matches) → list+pick · nothing found → manual path · path not a dir/no repo → re-prompt.

### IP-C — Copy mode asks a destination folder · LOCKED
- **Decision:** When the run is a copy (Debug Mode import-a-copy, DG-10c), preflight also asks the destination
  folder, copies the project there, and operates on the copy; the original is untouched.
- **Rationale:** Matches the operator model + Debug Mode LD11's opt-in import locus.
- **Edges:** destination exists/non-empty → confirm-overwrite or pick another · same-as-source → reject.

### IP-D — Multi-platform install, the SIMPLE way (needed today) · LOCKED
- **Decision:** Each supported platform has its **own small install script** under `adapters/<platform>/`
  (mirrors the existing `adapters/claude/` layout) that registers the skills with that host. The core picks the
  installer by the chosen/detected platform. **Claude is built + verified today** (the operator's platform);
  **Codex + Kiro get the same small install-script pattern** (best-effort, documented — see testability caveat);
  **Quick brings its own installer** (core defines only the contract — IP-F4, `AGENTS.md:42–46`).
- **Rationale:** "Multi-platform is the very next step, needed today before benchmarking." One small script per
  platform folder is the simple, honest mechanism — not an installer-interface taxonomy.
- **Testability caveat (honest):** Claude can be built + exercised here; Codex/Kiro install scripts can be
  written to the same pattern but **not fully verified** without those hosts → they ship documented best-effort.
- **Edges:** unknown platform → fall back to a generic "copy SKILL.md into the host's skills dir" + print manual steps.
