---
title: "install-update-polish — BUILD PLAN (phased, disjoint ownership, TDD)"
status: FROZEN PLAN (2026-06-29) — derived from DESIGN.md; build order is binding
spec: install-update-polish
design: DESIGN.md (this plan implements it)
sibling-track: FREEZE-write-settings-merge.md (item 3 — its OWN already-frozen track; builds independently)
phasing: Phase A (core update path — ship/test FIRST) → Phase B (overlay layer) → Phase C (fork layer)
parallelism: phases are SEQUENTIAL; tasks WITHIN a phase have DISJOINT file ownership for parallel subagents
tags: [plan, frozen, phased, tdd, disjoint-ownership]
---

# install-update-polish — BUILD PLAN

Three sequential phases. **Phase A is the operator's "install / update / test immediately" path** — version
surface + `--update` + factory-reset + uninstall polish — so a full test environment is reachable before any
overlay/fork machinery exists. Phase B adds the overlay layer; Phase C adds the fork layer.

**Sibling track (independent):** item 3 (`write_settings` MERGE) builds from `FREEZE-write-settings-merge.md`,
owning **only** `tools/kata_settings.py` + `tools/tests/test_kata_settings.py`. It is DISJOINT from every task
here and may run in parallel with any phase. Its only intersection is the Phase-A live proof step 4 (reconfigure
preserves `confirmedPlatforms`) — sequence item 3 to land before that live-proof step.

**Engine-edit discipline (all phases):** the 5 frozen fns (`_flat_link_skills`, `_link_or_copy`, `install`,
`copy_project`, `confirm_platform`) are **never edited**. Within a phase, **exactly one task** owns
`tools/kata_install.py` (the "engine wiring" task); module/test/docs tasks run in parallel against disjoint
files. Across phases the engine is edited by at most one task per phase (phases are sequential ⇒ no conflict).

**TDD for every task:** write the failing test first; default-FAIL; no task is done until its tests are green
and the phase gate passes.

---

## PHASE A — Core update path (SHIP + TEST FIRST)

Goal: a real install can be **updated and factory-reset in one command on both link modes**, the uninstall
leaves no orphaned links, and a version surface exists — with **zero overlay/fork machinery** yet.

### A1 — Version surface module  ·  OWNS: `tools/kata_version.py`, `tools/tests/test_kata_version.py`
- Implement the PURE, git-free `kata_version` API (DESIGN §5): `stamp_path`/`manifest_path`, `write_stamp`,
  `read_stamp`, `compute_manifest`, `write_manifest`/`read_manifest`, `is_pristine`, `suite_semver`.
- `..`-guard all paths (reuse the `_safe_abs` convention); fail-closed JSON reads (`{}` on corrupt).
- **TDD:** stamp round-trips; manifest hashes are stable + match `iter_skill_dirs` coverage; `is_pristine`
  true on a verbatim base, false after a content change; `write_stamp` never shells out (assert no subprocess /
  no git import). 
- **Gate:** unit tests green; Snyk clean; module imports nothing from `kata_install`'s private region.

### A2 — Engine wiring: install-stamp, `--update`, factory-reset, sweep, dry-run  ·  OWNS: `tools/kata_install.py`, `tools/tests/test_install_update.py`
- **M1 (load-bearing):** the EXISTING `main()` install branch (`kata_install.py:626-641`) gains an **additive**
  post-install step — after `install()` succeeds, call `kata_version.write_stamp`/`write_manifest`. When
  `--git-sha` is absent (plain `install.sh` path), record `gitSha:"unknown"` (schema permits). This makes a
  fresh install self-identify as an install so §6.2's `adaptation_context` rail is ON by default and §12 step-1
  passes. Stays git-free (engine never computes the SHA).
- Add `main()` branches + NEW post-D126 fns ONLY (DESIGN §4.2, §8, §9): `--update` (calls `install()` →
  re-link, then `kata_version.write_stamp`/`write_manifest` from `--git-sha`), `--factory-reset`/`--reinstall`
  (Phase-A form: re-link/re-copy pristine + re-stamp; `--hard` is a no-op-on-overlay passthrough here),
  `--dry-run`, `--git-sha`.
- **minor-a:** `--update` calls `kata_version.is_pristine` against the *previous* manifest before the engine
  re-link and surfaces a drift NOTE for any hand-edited tracked base (the live consumer for `is_pristine`).
- Extend `uninstall()` with `_sweep_managed_slots(skills_dst, home)` (sweep ALL host slots, fail-closed; prune
  nothing it didn't remove). `--dry-run` short-circuits before any mutation.
- **DO NOT** edit the 5 frozen fns. The materialize/shadow passes are stubbed as no-op hooks (`_materialize_pass`
  returns immediately when `kata_overlay` is absent) so B/C can wire in without re-touching the branch logic.
- **TDD:** plain install writes stamp+manifest with `gitSha:"unknown"` (M1) and `adaptation_context` then reads
  `"install"`; `--update` idempotency (re-run → identical links, identical stamp, exit 0); copy-mode re-copies
  vs symlink-mode tracks; factory-reset restores pristine; sweep removes an orphaned link after a simulated
  rename but leaves a non-kata dir intact; `--dry-run` changes nothing; exit-code table holds; every existing
  `test_kata_install.py` test still passes.
- **Gate:** pytest green; Snyk clean; frozen-fn bytes unchanged (assert via a diff check in review).

### A3 — Update/factory-reset bootstrap  ·  OWNS: `update.sh`, `update.ps1`
- Mirror the `install.sh`/`install.ps1` contract (DESIGN §4.1): resolve home (no clone), `git fetch`, determine
  ref, `--check` (report current/available, no mutation), clean ff/`reset --hard` to ref, capture SHA, invoke
  `kata_install.py --update --git-sha <sha>`, propagate exit. `--factory-reset [--hard]` passes through to the
  engine; `--hard` additionally permits the bootstrap `git reset --hard <ref>`.
- **M2 (operator-signed-off):** run `git status --porcelain` on the tracked tree **before** any checkout/reset.
  Dirty tracked base → **WARN + ABORT by default** (exit non-zero, no mutation), print dirty paths; proceed
  only with the explicit **`--discard-local`** flag. NEVER silently clobber local base edits (sole protection
  for tracked, non-git-ignored base files — DESIGN Invariant 7).
- **minor-c:** detect a non-git-clone home (no fetchable origin — copy/"Use this template") → emit
  `"this home is not a git clone — re-install to update"` and exit without mutating (such homes update via
  `install.sh`).
- Honest copy-vs-symlink messaging surfaced from the engine result.
- **TDD/proof:** offline smoke on both shells using a **local bare repo as origin** (minor-d: `git init --bare`,
  push, clone) so the ref-advance + dirty-guard + `--discard-local` paths are reproducible offline; `--check`
  exits without mutating; ALL git stays in these scripts (grep-assert no git token in any `tools/*.py`).
- **Gate:** offline smoke green on Git Bash + PowerShell, including the M2 abort-then-`--discard-local` path.

### A4 — Docs + gitignore  ·  OWNS: `.gitignore`, `docs/SETUP.md` (§4), `README.md`
- `.gitignore`: add `.kata-version`, `.kata-manifest.json`, `.kata-overlay/` (so home git ops never touch user
  state — DESIGN §9/Invariant 7).
- `docs/SETUP.md §4`: replace the manual `git pull` prose with the shipped `update.sh`/`--update` +
  factory-reset; keep the manual path as documented fallback (additive). `README.md`: one-liner update block.
- **Gate:** docs match shipped flags; no stale "re-run the installer manually" as the *only* path.

**PHASE A GATE (operator can now install/update/test):** pytest green (existing ≥1765 + A1/A2 new) ·
`validate_skills` 47/0 · Snyk medium+ 0 on new/changed Python · offline smoke both shells (origin = a **local
bare repo**, minor-d) · a **live install→update→factory-reset→uninstall** proof on a real `~/.kata-home`
(DESIGN §12 steps 1, 2, 5-Phase-A, 7), **including the M2 dirty-tree abort-then-`--discard-local` path** ·
fresh-context `kata-evaluate` PASS.

---

## PHASE B — Overlay layer (parametric / append local adaptation)

Goal: a user can locally adapt a skill **without ever editing the base** — an overlay entry materializes into a
concrete host slot; factory-reset drops it back to a link.

### B1 — Overlay store + materializer core  ·  OWNS: `tools/kata_overlay.py`, `tools/tests/test_kata_overlay.py`
- Implement the PURE `kata_overlay` API (DESIGN §2, §3, §6): `overlay_dir`, `read_overlay`, `validate_overlay`,
  `has_overlay`, `apply_overlay` (the base+overlay→SKILL.md composer), `write_overlay_entry` (read-merge-write
  ONE skill — never wholesale), `drop_overlay_entry`, `adaptation_context`, plus `materialized.json` I/O
  (`read_materialized`/`write_materialized`/`record_slot`/`drop_slot`).
- `apply_overlay` — pin the **M4 compose semantics exactly** (DESIGN §2): `frontmatterOverrides` = shallow
  per-key REPLACE (list-valued keys `tags`/`allowed-tools`/`aliases`/`supersedes` replaced WHOLESALE, never
  element-merged); `prepend`/`append` at a named heading-anchor = first/last content BENEATH that heading
  (`prepend` right after the heading line; `append` just before the next equal-or-higher heading); `anchor:null`
  = start/end of body (after frontmatter); multiple same-anchor blocks apply in array order. Fail-CLOSED
  `ValueError` on an unresolvable anchor (present base, bad anchor). Reuse `validate_skills.parse_frontmatter`
  (no new YAML parser).
- **TDD:** round-trip a frontmatter override (scalar + a list replaced wholesale — M4) + an append/prepend
  block at a named heading AND at null-anchor → valid SKILL.md with content in the exact positions; multiple
  same-anchor blocks ordered; unresolvable anchor raises (fail-closed); `write_overlay_entry` preserves other
  skills' entries (the item-3 lesson); `adaptation_context` returns `"install"` iff `.kata-version` present;
  corrupt store degrades to empty.
- **Gate:** unit tests green; Snyk clean; `validate_overlay` is fail-closed.

### B2 — Engine wiring: activate the materialize pass  ·  OWNS: `tools/kata_install.py`, `tools/tests/test_install_update.py` (extend)
- Flesh out `_materialize_pass(home, host_skills_dir, link_mode)` (DESIGN §3): after `_flat_link_skills`, for
  each `has_overlay` skill, replace the verbatim slot with a materialized concrete dir (copytree base →
  overwrite SKILL.md with `apply_overlay` → write `.kata-managed` + `.kata-overlay-materialized` markers →
  `record_slot`). Wire `--factory-reset` to drop materializations (read `materialized.json`, restore each slot
  to `baseMode`, clear record); wire `--hard` to also `drop`/empty the overlay store.
- **M3 (fail-soft):** an overlay entry whose base skill no longer exists in the updated tree → emit a NOTE and
  SKIP (never call `apply_overlay` with absent `base_text`; never crash); leave the stale entry in the store.
- Still **never** edits the 5 frozen fns; the pass runs strictly post-link.
- **TDD:** one overlaid skill materializes (concrete SKILL.md, both markers, recorded) while others stay
  symlink/copy; `--update` re-materializes from updated base; **M3:** an overlay for a removed base → NOTE +
  SKIP, no crash, entry retained; factory-reset restores the link + preserves the overlay store;
  `--factory-reset --hard` clears the store; idempotency holds.
- **Gate:** pytest green; frozen-fn bytes unchanged; Snyk clean.

### B3 — kata-improve local-adaptation mode  ·  OWNS: `skills/meta/kata-improve/SKILL.md`
- Add the local-adaptation mode section (DESIGN §6.2): `adaptation_context` detection, the install-context
  safety rail (kata mode refuses to edit `skills/**` in an install absent `improve.allowUpstreamEdit`), the
  edit-category→emission-target table, and the pinned writable footprint (overlay + toolkit candidates only).
  No new `allowed-tools`.
- **Gate:** `validate_skills` 47/0 (frontmatter unchanged shape); body conforms; pointer-style (no restatement
  of the schema); fresh-context `kata-review` of the skill passes.

### B4 — Docs (overlay model)  ·  OWNS: `docs/SETUP.md` (overlay/factory-reset subsections)
- Document the overlay store, the symlink→concrete promotion for overlaid slots (honest), and factory-reset's
  preserve-vs-`--hard` distinction.
- **Gate:** matches shipped behavior; honest about the one-skill "edits no longer live" tradeoff.

**PHASE B GATE:** pytest green · `validate_skills` 47/0 · Snyk medium+ 0 · the **overlay-materialize + reconfigure
+ factory-reset** live proof (DESIGN §12 steps 3, 4, 5-full) · `kata-evaluate` PASS.

---

## PHASE C — Fork layer (supersedes precedence + kata-promote gate)

Goal: a deep-divergence fork can **shadow** an upstream skill by name at install/update — but only after the
human `kata-promote` gate.

### C1 — Supersede resolver  ·  OWNS: `tools/kata_supersede.py`, `tools/tests/test_kata_supersede.py`
- Implement PURE `resolve_shadows(agentskills_dir) -> {upstream_name: fork_dir}` (scan promoted
  `<dir>/skills/**` for non-empty `supersedes`) and `validate_shadows(shadows, base_names)` (fail-closed:
  unknown supersede target = ERROR; two forks → same upstream = ERROR). No git.
- **TDD:** a promoted fork with `supersedes` resolves; a candidate in `candidates/` does NOT shadow; ambiguous
  double-supersede errors; an unknown target errors; absent `agentSkills.dir` → empty (no-op, BC).
- **Gate:** unit tests green; Snyk clean.

### C2 — Engine wiring: shadow precedence in the materialize pass  ·  OWNS: `tools/kata_install.py`, `tools/tests/test_install_update.py` (extend)
- In the `--update`/install orchestration, when `agentSkills.dir` is configured, call `resolve_shadows` +
  `validate_shadows`; the materialize pass installs the fork body (not the base) into each shadowed slot,
  marking `source: "fork"` in `materialized.json`. Precedence: fork > overlay > pristine (DESIGN §7.3).
- **minor-b:** when a skill has BOTH an overlay AND a winning fork, materialize the fork and emit a NOTE
  (`"overlay for <name> is dormant — a superseding fork shadows it"`); preserve the overlay entry (re-applies
  if the fork is later removed).
- The engine's in-repo dupe guard is untouched (forks are outside the repo set).
- **TDD:** a shadowed slot serves the fork body; precedence order holds when a skill has BOTH an overlay and a
  fork (fork wins) and the dormant-overlay NOTE is emitted (minor-b); `validate_shadows` failure → STOP +
  escalate (no partial shadow); `validate_skills` still 47/0.
- **Gate:** pytest green; frozen-fn bytes unchanged; 47/0; Snyk clean.

### C3 — kata-promote shadow binding  ·  OWNS: `skills/meta/kata-promote/SKILL.md`
- Add the note: a promoted toolkit skill carrying `supersedes: <name>` becomes **shadow-eligible at next
  install/update**; only `skills/`-promoted (not `candidates/`) forks shadow; the human gate is the precondition
  for shadowing. Existing promotion review flow preserved.
- **Gate:** `validate_skills` 47/0; `kata-review` of the skill passes.

### C4 — Standards note  ·  OWNS: `docs/STANDARDS.md`
- One additive line in §1/§3: `supersedes:` is now **wired** as install/update-time precedence (no schema
  change — the field already exists; this records that it is no longer dormant).
- **Gate:** validator unaffected (doc-only); cross-refs consistent.

**PHASE C GATE:** pytest green · `validate_skills` 47/0 · Snyk medium+ 0 · the **fork/shadow** live proof
(DESIGN §12 step 6) · `kata-evaluate` PASS.

---

## Cross-phase final gate (definition of done)

- All three phase gates passed; the **full DESIGN §12 live proof** captured end-to-end on **both shells**
  (install → update → overlay-materialize → reconfigure → factory-reset[`--hard`] → fork/shadow → uninstall).
- pytest green (≥1765 existing + all new) · `validate_skills` **47/0** · Snyk medium+ **0** on all new/changed
  Python · the 5 frozen engine fns byte-for-byte unchanged · `tools/kata_settings.py` **untouched** (item-3
  disjoint) · `docs/SETUP.md`/`README.md`/`STANDARDS.md` updated · fresh-context `kata-evaluate` PASS.
- Operator merge gate → checkpoint (new D-number; supersede-never-rewrite).

## Disjoint-ownership matrix (quick reference)

| File | A | B | C |
|---|---|---|---|
| `tools/kata_version.py` (+test) | A1 | — | — |
| `tools/kata_install.py` (+`test_install_update.py`) | A2 | B2 | C2 |
| `update.sh` / `update.ps1` | A3 | — | — |
| `.gitignore` / `README.md` | A4 | — | — |
| `docs/SETUP.md` | A4 (§4) | B4 (overlay) | — |
| `tools/kata_overlay.py` (+test) | — | B1 | — |
| `skills/meta/kata-improve/SKILL.md` | — | B3 | — |
| `tools/kata_supersede.py` (+test) | — | — | C1 |
| `skills/meta/kata-promote/SKILL.md` | — | — | C3 |
| `docs/STANDARDS.md` | — | — | C4 |
| `tools/kata_settings.py` (+test) | **sibling item-3 track only — never owned here** | | |

Within each phase, the engine task (A2/B2/C2) is the single owner of `kata_install.py`; all other tasks in that
phase own disjoint files and run in parallel.
