---
date: 2026-06-19
spec: install-portability
status: BRIEF — pre-grill, not frozen. A captured gap; the build needs its own grill → DESIGN → PLAN.
order: 1 of 3 (future-gap sequence — the foundation the other two lean on)
tags: [brief, future-gap, install, portability, config, modular, vault]
---

# Install & Portability — workspace config + modular per-platform install

> **ALIGNMENT (2026-06-20, [[greater-loop]] grill GL-R3c):** the **config layer** of this brief (interactive
> target/platform/vault selection + workspace binding) **folds into the `kata-initiate` initiation module** —
> configured interactively during initiation, not as a separate "build after." What remains HERE = the heavier
> **per-platform installer mechanics** (PokeVault link / bring-your-own-vault scaffold / aim-each-folder;
> the work host brings its own), sequenced to **Phase 5** of `greater-loop/ROADMAP.md` (external reach, after the
> self greater loop). See `greater-loop/DESIGN.md §8`.

> **Quick plan brief.** Captures scope + constraints so we can grill→freeze→build it cleanly later. Sequencing
> for *this* item is the one open call (see *Build timing* below): the user said "build it before we dogfood,"
> and also "come back to these after dogfooding" — to be confirmed.

## Why (the gap)
Today KataHarness operates **only inside its own repo**. To run against *any* user's vault or project directory
it needs (1) a way for the skills to be **discovered** by the host agent, and (2) a **one-time workspace-binding
config** that says where everything lives. The per-run `kata.config` has the *seeds* (`engram.learnFeed.dir`,
`agentSkills.dir`, `target.path` are path-configurable) but there is no init flow and the layout is PokeVault-
shaped. See [[BACKLOG]] "Install & portability layer".

## Scope / what it must do
- **Config into place.** A first-run **init flow** that writes a top-level **workspace binding** (distinct from
  per-run `kata.config`): the roots for where the **harness skills** live and where the **operable directories**
  (`.planning/`, the LEARN feed, candidate skills, `.kata/`) land relative to the user's workspace.
- **Three user paths, offered at init:**
  1. **Optional PokeVault integration** — offer to install/link [PokeVault] too (a pointer/link to install it);
     if accepted, bind the standard `toolkit/` layout automatically.
  2. **Bring-your-own vault** — point the harness at the user's existing vault **and scaffold a small
     functional vault** inside it (the minimal structure that supports the harness's functions) if one isn't
     present.
  3. **Aim-each-folder** — power-user path: let the user target **each defined folder individually** (skills
     dir · planning dir · learn-feed dir · candidate-skills dir · state/`.kata` dir).
- **Modular per-platform install components.** The install step is **pluggable**: PokeVault, **the work host**, and
  **work vault** each can ship their **own custom setup/install component**. the work host's ties into the
  **install/config agents in Quick** (so the work host brings its own installer; the core just defines the
  contract the installer satisfies). Core stays platform-agnostic; installers are adapters.
- **Doc cordoning (explicit requirement).** The setup/install material is **cordoned into its own document**
  (e.g. `docs/SETUP.md` / `INSTALL.md`), **not** mixed into the main README/AGENTS narrative. The main docs
  carry only **pointers** ("No vault yet? Start here →") so a vault-less user is routed to setup without
  cluttering the conceptual docs.

## Modularity / key constraints
- A **stable install contract** (what any installer must produce: discoverable skills + a valid workspace
  binding) so PokeVault / the work host / a plain dir each satisfy it differently. This is spine #3 (agnostic via
  adapters) applied to *install*, not just to runtime.
- Discovery is host-specific (Claude Code plugin or `.claude/skills/`; Quick/the work host via its own agents;
  Kiro/Codex via their adapters) — overlaps the deferred "Plugin packaging" backlog item.
- Never assume PokeVault. Absent any binding ⇒ the harness still runs in-repo (today's behavior, BC-style).

## Open questions (for the grill)
- One init skill (`kata-install`) vs. an extension of `kata-bootstrap`'s Phase 0?
- Where does the workspace binding physically live (a `~/.kata/` user config? a per-workspace dotfile?) and how
  does a run discover it?
- What is the *minimal functional vault* scaffold (folders + index files) for the bring-your-own-vault path?
- How does the install contract get versioned so platform installers can target a known shape?

## Dependencies & sequencing
- **Foundation for [[multi-model-orchestration]] and [[testing-model]]** — both need to know where things live.
- Reuses config seeds already shipped; pairs with the deferred "Plugin packaging" + v0.3 adapters.

## Build timing (DECISION NEEDED)
The user said both "**build it before we dogfood**" and "come back to these after dogfooding." Confirm: build
the install/portability layer **before** the self-dogfood, or **self-dogfood first** then build this? (The
self-dogfood does *not* require it — KataHarness's own repo is its workspace.)

## Out of scope (for now)
Full plugin-marketplace publishing; non-Obsidian vault formats; the work host installer internals (the work host
owns those — we own the contract).
