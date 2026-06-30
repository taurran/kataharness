---
title: "install-update-polish — FROZEN DESIGN (hybrid update system: update · factory-reset · uninstall polish · overlay · fork)"
status: FROZEN (2026-06-29) — spike ADOPTED; every open question resolved; build comes via PLAN.md
spec: install-update-polish
adopts: SPIKE-learning-overlay.md (hybrid recommendation, in full)
builds-on: install-onboarding/DESIGN.md (the engine + the 18 working patterns + never-git guarantee)
sibling: FREEZE-write-settings-merge.md (item 3 — DISJOINT freeze; this design NEVER touches tools/kata_settings.py)
decision: TBD (assign a D-number at freeze-gate sign-off)
invariant: 5 engine fns COMPOSED never rewritten · kata_install NEVER git · additive-first/strict-BC · validate_skills 47/0 · Snyk medium+ 0
tags: [design, frozen, install, update, factory-reset, uninstall, overlay, supersedes, fork, immutable-base]
---

# install-update-polish — FROZEN DESIGN

The operator has chosen to build the **full hybrid update system now** (not defer the overlay to v0.2).
This design turns the ADOPTED spike into a buildable, frozen spec. It resolves every open question from the
spike and the requirement, honors all invariants, and is phased (PLAN.md) so the **core update path ships and
is testable first**, then the overlay layer, then the fork layer.

The governing architecture (ADOPTED from the spike, verbatim):

> **Upstream skills are IMMUTABLE from the user's side → update is a clean overwrite.**
> **Parametric / append-able local change → an overlay / parameter store.**
> **Deep behavioral divergence → a fork via the (currently dormant) `supersedes` / toolkit machinery.**
> **Factory-reset = drop the overlay back to the pristine baseline.**

`kata-improve` splits into two audiences: **dev-repo "authoring-upstream"** (edits `skills/**` in place, as
today) vs **user-install "local-adaptation"** (NEVER edits the installed base — emits an overlay entry or
scaffolds a fork).

---

## 0. Invariants (never relax) + the don't-break guarantee

These are carried forward verbatim from `install-onboarding/DESIGN.md §0` and the requirement's constraints.
Every one is re-affirmed; the compliance proof is §10.

1. **The 5 engine functions are COMPOSED, never rewritten.** `_flat_link_skills`, `_link_or_copy`,
   `install`, `copy_project`, `confirm_platform` are byte-for-byte untouched. All new behavior lives in (a)
   NEW pure modules under `tools/`, (b) NEW functions in `kata_install.py`'s post-D126 region, and (c) NEW
   branches in `main()` (which is **not** one of the 5 frozen fns — it was already extended additively in
   D126). No `changed` key is threaded through the engine; no signature changes.
2. **The 18 working patterns are DON'T-BREAK.** This design reads them; it never alters their behavior. The
   one working-pattern edit in the whole requirement — `write_settings` MERGE (item 3) — is a **separate,
   already-frozen** track (`FREEZE-write-settings-merge.md`) with its own freeze-gate and strict BC. **This
   design's file ownership is DISJOINT from it: nothing here touches `tools/kata_settings.py`.**
3. **`tools/kata_install.py` NEVER invokes git.** `copy_project` stays `shutil`-only. The uninstaller never
   runs git. **ALL git (fetch / checkout / reset / pull) lives in the bootstrap shells** (`update.sh` /
   `update.ps1`) or the existing clone path — NEVER in the Python engine or any new pure module. `kata_version`
   is git-FREE: the bootstrap computes the SHA and passes it in; the module only writes/reads what it is given.
4. **Additive-first / strict-BC.** Every new flag is `store_true`/optional with today's default ⇒ omitting it
   reproduces current behavior byte-for-byte. Existing install / uninstall / headless behavior is unchanged.
   Every existing `test_kata_install.py` test still passes (none pass the new flags).
5. **Non-clobber preserved + extended.** The `.kata-managed` marker (`kata_install.py:105`) and the
   "symlink→under-home OR `.kata-managed` dir, else leave intact" rule (`:115-123`, `uninstall:442-460`) are
   reused unchanged. Materialized slots carry **both** `.kata-managed` (so uninstall removes them) and a NEW
   `.kata-overlay-materialized` marker (so factory-reset knows to restore the pristine link). The orphaned-link
   sweep (§8) is **fail-closed**: it never removes a non-kata or unrelated link.
6. **Gates unchanged.** `validate_skills` stays **47/0** (forks live OUTSIDE the repo tree, never scanned; the
   shadowed upstream skill stays present and validated — §7.4). Snyk medium+ **0** on all new/changed Python.
7. **User-owned state survives every git operation.** The home (`~/.kata-home`) is a git clone; the update
   bootstrap runs `git` against its **tracked** tree. The overlay store, version stamp, manifest, and
   materialization record are **git-ignored** (§9) so a `git checkout`/`reset --hard` never sees, conflicts
   with, or deletes them. **Tracked base files are NOT git-ignored-protected** — their protection is the
   dirty-tree check (M2, §4.1): the update bootstrap runs `git status --porcelain` on the tracked tree
   **before** any checkout/reset and **aborts on a dirty tracked tree** unless `--discard-local` is passed, so
   a user's in-place base edits are never silently clobbered.

---

## 1. The home / host / store topology (the mental model)

```
~/.kata-home/                         the harness HOME — a full git clone (bootstrap may git here)
  skills/<cat>/<name>/SKILL.md        IMMUTABLE base (tracked; clean-overwritten on update)
  modules/<cat>/<name>/SKILL.md       IMMUTABLE base (tracked)
  tools/kata_install.py               the engine (NEVER git)
  .kata-settings.json                 user-owned, git-ignored  (item-3 territory — NOT touched here)
  .kata-version                       NEW · user-owned, git-ignored · install/update stamp (§5)
  .kata-manifest.json                 NEW · user-owned, git-ignored · content-hash baseline (§5)
  .kata-overlay/                      NEW · user-owned, git-ignored · the overlay store (§2)
    overlay.json                        keyed by skill name (frontmatterOverrides/prepend/append/pin)
    materialized.json                   record of which host slots are materialized (§3)

~/.claude/skills/<name>/              the HOST slots (claude); codex/kiro → <host>/.agents/skills/<name>/
  └─ symlink → home/skills/...        DEFAULT: verbatim symlink (copy fallback on Win-no-DevMode)
  └─ OR concrete dir + composed SKILL.md   when overlaid/forked → MATERIALIZED (real dir, markers)

<agentSkills.dir>/                    the user's toolkit (protocol/config.md; OUTSIDE the repo)
  candidates/<name>/                  forks authored here (kata-write-skill), sandboxed
  skills/<cat>/<name>/                promoted forks (kata-promote gate) — may carry supersedes:
```

**Scope decision (frozen): the overlay store, version stamp, manifest, and materialization record are
PER-INSTALL (live in the home), not per-project.** Rationale: skills are flat-linked into a single host
location (`~/.claude/skills/`) and are therefore **shared across every project the user runs**. A per-project
overlay would have no host slot to materialize into. The home is the natural, already-git-ignored neighbor of
`.kata-settings.json` (the spike's recommendation, `SPIKE:164`).

---

## 2. The overlay store — location, format, scope, schema, module

**Location (frozen):** `<home>/.kata-overlay/overlay.json`. A **directory** (not a bare file) so the
materialization record and any future per-skill backups live alongside it. User-owned, **git-ignored** (§9).

**Format (frozen): JSON** — consistent with `.kata-settings.json`, `kata.config`, and `plugin.json`. (Not
YAML: the store is machine-coordination state that churns and is hand-edit-hostile — STANDARDS §5 keeps such
state in JSON, not vault frontmatter. The frontmatter it *overrides* is YAML, but the override values are
carried as JSON data and re-serialized to YAML only at materialize time.)

**Scope (frozen): per-install** (see §1).

**Schema (`overlay.json`):**

```json
{
  "schema": 1,
  "skills": {
    "<skill-name>": {
      "frontmatterOverrides": { "<field>": <value> },
      "prepend": [ { "anchor": "<heading-or-null>", "markdown": "<block>" } ],
      "append":  [ { "anchor": "<heading-or-null>", "markdown": "<block>" } ],
      "pin": "<semver>|null",
      "baseSha": "<sha256 of the base SKILL.md this entry was authored against>|null",
      "baseSuiteSemver": "<suite semver at authoring>|null"
    }
  }
}
```

- `frontmatterOverrides` — a field→value map merged over the base frontmatter (covers spike category 1).
- `prepend` / `append` — ordered blocks spliced at a named `anchor` heading (e.g. `"## Output"`), or at
  start/end of body when `anchor` is `null` (covers spike category 2, the dominant kata shape). A block whose
  `anchor` does not exist in the base body is a **validation error** (fail-closed — never silently dropped).
- `pin` — an optional advisory semver the user pinned against (informational while the pre-release hold holds
  per STANDARDS §3; becomes a real compat signal post-v0.1).
- `baseSha` / `baseSuiteSemver` (OPTIONAL) — the **staleness signal** (spike OQ6): the hash + suite version
  the entry was authored against. After an update, `kata_overlay` compares the live base hash (from the
  manifest, §5) to `baseSha`; a mismatch is surfaced as a **NOTE** ("the base skill changed since you authored
  this overlay — re-review") but **never blocks** the materialize (the base is immutable; the overlay still
  applies). This makes "is my overlay still compatible?" answerable without coupling to per-skill semver
  (which is frozen at 0.1.0, STANDARDS §3).

**Compose semantics — pinned exactly (M4, frozen).** `apply_overlay` is deterministic and unsurprising:
- **`frontmatterOverrides` = shallow, per-key REPLACE.** Each named key REPLACES the base key's value
  wholesale. **List-valued keys (`tags`, `allowed-tools`, `aliases`, `supersedes`) are replaced ENTIRELY, not
  element-merged** — to *extend* a list the overlay must restate the full intended list. (Keeps the rule a
  one-line mental model; no deep-merge ambiguity.) Keys absent from the override are left exactly as the base.
- **`prepend` / `append` at a named heading-anchor** insert as the **FIRST / LAST content BENEATH that
  heading** — `prepend` lands immediately after the heading line; `append` lands just before the next heading
  of equal-or-higher level (or end-of-section). **`anchor: null`** = start-of-body (`prepend`) / end-of-body
  (`append`), placed after the frontmatter block. Multiple blocks for the same anchor apply in array order.
- **Missing-base fail-soft (M3, frozen).** An overlay entry whose upstream base skill **no longer exists**
  (e.g. the skill was removed/renamed by an update) → `apply_overlay` is **never called with absent
  `base_text`**; the materialize pass (§3) emits a NOTE (`"overlay for <name>: base skill no longer exists —
  skipped"`) and **SKIPS** that entry. It never crashes, and the stale entry is left in the store for the user
  to clean (it re-activates if the skill returns). This is distinct from the unresolvable-anchor case (a
  present base with a bad anchor), which stays a fail-CLOSED `ValueError`.

**Module (frozen): `tools/kata_overlay.py` — PURE (no git, no network, stdlib-only).** Public API:

| Function | Contract |
|---|---|
| `overlay_dir(home) -> Path` | `<home>/.kata-overlay` (`..`-guarded via the engine's `_safe_abs` convention). |
| `read_overlay(home) -> dict` | Parse `overlay.json`; `{}`-equivalent (`{"schema":1,"skills":{}}`) when absent/corrupt (degrade to BC, mirrors `read_settings`). |
| `validate_overlay(data) -> list[str]` | Pure validator: schema int, per-skill key shapes, anchor-resolvability is checked at apply time; returns ERROR strings (empty = valid). Fail-closed. |
| `has_overlay(home, name) -> bool` | True iff a non-empty entry exists for `name`. |
| `apply_overlay(base_text, entry) -> str` | **The materializer core.** Parse base frontmatter+body, merge `frontmatterOverrides` (shallow per-key replace; lists replaced wholesale — M4), splice `prepend`/`append` at anchors (first/last-beneath-heading; null = start/end of body — M4), re-serialize to a valid SKILL.md string. Raises `ValueError` on an unresolvable anchor (fail-closed). **Caller guarantees `base_text` is present** — the missing-base case is handled fail-soft in the materialize pass (M3, §3), never here. Reuses the validator's `parse_frontmatter` shape (no new YAML parser). |
| `write_overlay_entry(home, name, entry) -> Path` | Read-merge-write a single skill entry (NEVER wholesale — preserves other skills' entries; the item-3 lesson applied to this store). |
| `drop_overlay_entry(home, name) -> bool` | Remove one skill's entry (factory-reset of one skill). |
| `adaptation_context(home) -> "dev-repo"\|"install"` | Context discriminator for `kata-improve` (§6). PURE: returns `"install"` iff `<home>/.kata-version` exists, else `"dev-repo"`. |

---

## 3. The materialize step — composing the frozen engine (the seam)

**The host reads a FLAT `SKILL.md` with NO runtime compose (spike Finding 3).** So an overlay/fork is purely an
install/update-time construct: effective skill = **base + overlay → one concrete materialized `SKILL.md`**.

**The seam (frozen): a POST-LINK MATERIALIZE PASS.** This composes the frozen engine — it does not rewrite it:

1. `--update` / install first runs the engine's normal link step **unchanged**: `_flat_link_skills` →
   `_link_or_copy` symlinks (or copies on Win-no-DevMode) **every** skill verbatim, exactly as today. The 5
   frozen fns do their whole job, untouched.
2. **Then** a NEW pass `_materialize_pass(home, host_skills_dir, link_mode)` (a NEW function in the engine's
   post-D126 region, callable only from the NEW `--update`/install-stamp path) iterates the skills that have an
   overlay entry OR are shadowed by a fork (§7), and **replaces that one verbatim slot with a materialized
   concrete directory**:
   - Remove the verbatim slot (symlink → `unlink`; copy → `rmtree`, guarded by `.kata-managed` exactly as
     `_link_or_copy:116-124`).
   - `shutil.copytree` the base skill dir into the slot (carries `resources/` etc.), then **overwrite the
     slot's `SKILL.md`** with `kata_overlay.apply_overlay(base_text, entry)` (or the fork's body for a shadow).
   - Write **two markers** into the slot: `.kata-managed` (uninstall removes it — reuses the existing signal)
     and `.kata-overlay-materialized` (factory-reset restores the link).
3. Skills WITHOUT an overlay/fork stay **symlink (or copy)** exactly as today — zero behavior change.

**Fail-soft + precedence NOTES the pass emits (M3 + minor-b, frozen):**
- **Missing base (M3):** an overlay entry whose base skill no longer exists in the updated tree → emit a NOTE
  and **SKIP** (never call `apply_overlay` with absent `base_text`; never crash). The stale entry stays in the
  store and re-activates if the skill returns.
- **Overlay shadowed by a fork (minor-b):** when a skill has BOTH an overlay entry AND a winning fork (§7.3,
  fork > overlay), the pass materializes the **fork** and emits a NOTE (`"overlay for <name> is dormant — a
  superseding fork shadows it"`) so the user knows their overlay is not in effect. The overlay entry is
  preserved (it re-applies if the fork is later removed).

**Why post-link, not a per-skill link-vs-materialize wrapper:** a wrapper would have to re-implement
`_flat_link_skills`'s dupe-guard + loop (a rewrite of a frozen fn). The post-link pass lets the frozen fns run
in full, then layers materialization on top of just the affected slots — strictly additive, strictly composing.
The cost is one extra filesystem write per overlaid slot (only when an overlay is actually exercised — the
spike's "not free, but bounded and only pays when used", Finding 3).

**The materialization record (frozen): `<home>/.kata-overlay/materialized.json`.** Records which host slots are
materialized so `--update` re-materializes them and `--factory-reset` restores them:

```json
{
  "schema": 1,
  "slots": {
    "<skill-name>": {
      "hostPath": "<abs path to the host slot>",
      "baseMode": "symlink|copy",          // what to RESTORE to on factory-reset
      "source": "overlay|fork",
      "appliedSha": "<sha256 of the composed SKILL.md>"
    }
  }
}
```

**Symlink-mode promotion (spike OQ3, frozen ACCEPTED):** materializing an overlaid skill **promotes its symlink
to a concrete file**, so for that one skill, edits to the repo no longer show up live. This is intrinsic to any
overlay on a flat-file host with no runtime compose; it is acceptable and explicit. `baseMode` records the
pre-materialize mode so factory-reset restores exactly it.

---

## 4. The update operation (`update.sh` / `update.ps1` + `--update`)

Two halves, split on the never-git line (Invariant 3):

### 4.1 Bootstrap half — `update.sh` / `update.ps1` (NEW; MAY git)

Extends the `install.sh`/`install.ps1` 5-step contract. Steps:

1. **Resolve the home** (identical resolution to `install.sh:48-64` — `KATA_SRC` → `KATA_HOME` → default home;
   error if absent — update never clones a missing home). **The home MUST be a git-clone origin** (have a
   `.git` with a fetchable remote); a copy/"Use this template" home (minor-c) has no origin to pull from →
   `update.sh` detects the missing remote, emits a clear NOTE (`"this home is not a git clone — re-install to
   update"`), and exits without mutating. Such homes update via **re-install** (`install.sh`), not `update.sh`.
2. **`git fetch`** the origin (honoring `KATA_REF`, default `master`).
3. **Dirty-tree guard (M2, frozen — runs BEFORE any checkout/reset).** Run `git status --porcelain` on the
   tracked tree. **If the tracked base is dirty → WARN and ABORT by default** (exit non-zero, change nothing),
   printing the dirty paths. Proceeding requires the explicit **`--discard-local`** flag, which acknowledges
   the local base edits will be discarded and only then performs step 5's reset. This is the sole protection
   for **tracked** base files (they are NOT git-ignored — Invariant 7); the harness NEVER silently clobbers a
   user's in-place base edits. (This also surfaces the kata-improve in-install base-edit anti-pattern: §6.2's
   rail steers users to the overlay/fork path instead of editing the base.)
4. **Determine the target ref** (`KATA_REF` or default). Compute `LOCAL=$(git rev-parse HEAD)` and
   `REMOTE=$(git rev-parse <ref>)`. **If equal → already current → still re-run the engine `--update`** (so a
   copy-mode install that was edited gets re-propagated and the stamp is refreshed) but report "already at
   `<sha>`".
5. **Clean fast-forward the tracked tree** (only after the step-3 guard passed or `--discard-local` was given).
   Because the base is **immutable-by-contract**, NO 3-way merge is needed (that is the whole point — spike
   Recommendation): `git checkout <ref>` then `git reset --hard <ref>` (or `git merge --ff-only`). The
   git-ignored user files (§9) are untouched by this.
6. **Capture the new SHA** (`git rev-parse HEAD`) and **invoke the engine**:
   `python tools/kata_install.py --update --platform <p> --git-sha <sha> [pass-through]`. (The SHA is passed in
   — the engine stays git-free.)
7. **Propagate the engine's exit code.**

### 4.2 Engine half — `kata_install.py --update` (NEW branch in `main()`; NO git)

`--update` performs the re-link / re-materialize / re-stamp half:

1. Call `install(platform, home, host_dir)` — the existing path, composing the 5 frozen fns, re-linking /
   re-copying every skill verbatim (idempotent: the engine's unlink+relink at `:116-134` yields valid links).
2. Run `_materialize_pass` (§3) — re-materialize every overlaid/forked slot from the (now-updated) base.
3. Write the version stamp + manifest (§5) via `kata_version` (consuming `--git-sha`).
4. **Idempotent:** an already-current install with no overlay re-links to identical targets and re-writes an
   identical stamp → effectively a `0` no-op. Re-running is always safe.

**Symlink vs copy on update (honest messaging — requirement item 1d):**
- **Symlink mode:** the symlinks already track the home, so step 4.1's checkout alone refreshes every
  non-overlaid skill; the `--update` re-run additionally re-materializes overlaid slots and re-stamps. Message:
  *"symlink mode: skills track the home; re-materialized N overlaid slots."*
- **Copy mode (Win-no-DevMode):** the copies are stale until re-copied; `--update` re-copies every skill (the
  exact UX gap the requirement calls out). Message: *"copy mode: re-copied all skills (copy-mode propagates
  only on update/reinstall)."*

`--update` is **additive**: absent ⇒ today's install path is byte-for-byte unchanged.

---

## 5. The version surface (`tools/kata_version.py` — PURE, git-free)

**`<home>/.kata-version` (JSON, git-ignored):**

```json
{
  "schema": 1,
  "gitSha": "<40-hex>|unknown",
  "suiteSemver": "0.1.0",
  "ref": "master",
  "installedAt": "<ISO-8601 UTC>",
  "linkMode": "symlink|copy|mixed",
  "platform": "claude"
}
```

The **git SHA is authoritative + free** (the bootstrap computes it and passes `--git-sha`); the **suite semver**
is the human/compat band (read from `README.md`, reusing the `_suite_version` heuristic — re-implemented in
`kata_version` to avoid importing the engine's private helper; `linkMode` comes from the install result's
`method`).

**Stamped on BOTH plain install AND update (M1, frozen — load-bearing).** The stamp + manifest are written at
the end of **every** successful install path, not only `--update`:
- The EXISTING `main()` install branch (`kata_install.py:626-641`) gains an **additive** post-install step:
  after `install()` succeeds, call `kata_version.write_stamp`/`write_manifest`. When `--git-sha` is absent
  (a plain install via `install.sh`, which does not pass a SHA), `gitSha` is recorded as **`"unknown"`** (the
  schema permits it) — the SHA is a "nice to have" for the bootstrap-driven path, not a correctness
  dependency.
- **Why this is load-bearing (not cosmetic):** without a first-install stamp, (1) §6.2's `adaptation_context`
  reads a real install as `"dev-repo"`, so the kata-improve base-mutation safety rail is **off by default** on
  a fresh install — exactly backwards; and (2) the §12 Phase-A live-proof step 1 ("`.kata-version` + manifest
  written on install") cannot pass. The stamp at plain-install time is what makes the install *self-identify*
  as an install.
- This stays **additive + git-free**: the stamp write is appended to the existing branch (not one of the 5
  frozen fns), and the engine never computes the SHA itself — `"unknown"` is the honest default when the
  bootstrap did not supply one.

**`<home>/.kata-manifest.json` (JSON, git-ignored)** — a content-hash of the shipped baseline, enabling drift /
overlay detection and "is this slot pristine?":

```json
{
  "schema": 1,
  "generatedAt": "<ISO-8601 UTC>",
  "gitSha": "<sha>",
  "skills": { "<name>": { "path": "skills/<cat>/<name>", "sha256": "<hash of SKILL.md>" } }
}
```

**Module `tools/kata_version.py` — PURE (NO git, stdlib + hashlib only):**

| Function | Contract |
|---|---|
| `stamp_path(home)` / `manifest_path(home)` | Resolve the two paths (`..`-guarded). |
| `write_stamp(home, *, git_sha, suite_semver, ref, link_mode, platform) -> Path` | Write `.kata-version` (the module writes what it is GIVEN — it never shells out to git). |
| `read_stamp(home) -> dict` | `{}` when absent/corrupt. |
| `compute_manifest(home) -> dict` | Hash every `skills/**/SKILL.md` + `modules/**/SKILL.md` (reuses `iter_skill_dirs` semantics; sha256). |
| `write_manifest(home, *, git_sha) -> Path` / `read_manifest(home) -> dict` | Persist / load. |
| `is_pristine(home, name) -> bool` | True iff the base SKILL.md hash matches the manifest (drift / "pristine slot" check). **Wired consumer (minor-a):** `--update` calls it before the checkout to compare each base hash against the *previous* manifest; a non-pristine base (the user hand-edited a tracked base file) is surfaced as a drift NOTE alongside the M2 dirty-tree guard. Not just a library primitive — it has a live call site. |
| `suite_semver(home) -> str` | README heuristic; defaults `0.1.0`. |

**"Newer available" check (requirement item 1e):** lives in the **bootstrap** (`git fetch` + compare local
HEAD vs `origin/<ref>`), because the module is git-free. `kata_version` provides only the *comparison
primitive* (sha equality / semver band); the network fetch is `update.sh`'s job. The check is **local-first and
opt-in** — `update.sh --check` reports "update available / current" and exits without mutating.

---

## 6. `kata-improve` — the contract split (dev-repo vs install)

**The contract change (frozen, ADOPTED from the spike):** `kata-improve` keeps its two audiences disjoint.

### 6.1 Authoring-upstream (dev repo) — UNCHANGED
The harness's own maintainers run `kata-improve`'s kata mode as today: edit `skills/**` / `protocol/` / `docs/`
in place, bump semver (per the pre-release hold), update the README index. This is where canonical improvement
lives. **No behavior change.**

### 6.2 Local-adaptation (user install) — NEW mode
In an install, `kata-improve` **MUST NOT edit `<home>/skills/**`**. It emits an overlay entry or scaffolds a
fork instead. The contract, precisely:

**Context detection (frozen):** the skill calls `kata_overlay.adaptation_context(home)`:
- `"install"` iff `<home>/.kata-version` exists. **Per M1 (§5) the stamp is written on EVERY install (plain or
  update)**, so any real install self-identifies as `"install"` and the safety rail below is **on by default**.
  The stamp is git-ignored, so a freshly cloned but never-installed canonical tree has no stamp.
- `"dev-repo"` otherwise (a canonical maintainer checkout that has never been installed into a host).

**Safety rail (frozen):** kata mode (in-place `skills/**` edits) **refuses to run when the context is
`"install"`** unless the operator passes an explicit acknowledgement (`improve.allowUpstreamEdit`), so the
default in an install is *never* a base mutation. The edge case (a maintainer who installed from their own dev
checkout, so the dev tree carries a stamp) is handled by that conscious override — failing toward
not-mutating-the-base.

**What local-adapt writes where (by spike edit category, Finding 1):**

| Change shape (spike category) | Emission target | Mechanism |
|---|---|---|
| 1 — frontmatter knob · 2 — appended guard/lesson/rubric (the ~60–70% bulk) | **Overlay entry** in `<home>/.kata-overlay/overlay.json` | `kata_overlay.write_overlay_entry(home, name, entry)` (read-merge-write one skill) |
| 3 — mid-body wording/threshold (the awkward middle) | Overlay **if** expressible as a frontmatter/append block; **else** route to fork | the skill states the choice explicitly + records why |
| 4 — deep prose/contract rewrite (the ~10–15% tail) | **Fork** authored to the toolkit, never the base | `kata-write-skill` → `<agentSkills.dir>/candidates/<name>/` carrying `supersedes: <upstream>` → `kata-promote` gate (§7) |
| 5 — whole new skill | Orthogonal (toolkit candidate) | existing `kata-write-skill` path — no collision |
| 6 — deprecate/retire | Fork/supersede semantics | §7 |

**Boundary (frozen):** local-adapt mode's writable footprint in an install is **exactly**: `overlay.json` (via
`write_overlay_entry`) and the toolkit `candidates/` tree (via `kata-write-skill`). It writes **nothing** under
`<home>/skills/`, `protocol/`, or `docs/`. This mirrors the existing pinned-footprint discipline kata-improve
already applies to its T2 sub-mode (`kata-improve:134-142`).

This is an **additive prose mode** in the existing skill body (no new `allowed-tools` — `Write`/`Edit` already
present); the kata-mode/local-adapt selection is a documented branch keyed on `adaptation_context`.

---

## 7. Supersedes / fork precedence binding (wiring the dormant field)

The `supersedes:` field is declared in STANDARDS §1 but wired NOWHERE (spike Finding 2). This activates it as
an **install/update-time precedence** mechanism.

### 7.1 The shadow rule
A **promoted toolkit skill** (under `<agentSkills.dir>/skills/<category>/<name>/`) carrying
`supersedes: <upstream-name>` **shadows** the upstream repo skill of that basename at install/update time: the
upstream base is suppressed from its host slot and the fork's `SKILL.md` is installed there instead.

### 7.2 The kata-promote gate (frozen — human-attended, audited)
A fork **cannot shadow until it has passed the existing `kata-promote` human gate** (`kata-promote/SKILL.md`).
The path is: `kata-write-skill` authors the fork into `<agentSkills.dir>/candidates/<name>/` (sandboxed,
`scope: agent`, never loaded) → grounding gate → **`kata-promote`** moves it to
`<agentSkills.dir>/skills/<category>/`. **Only skills under the toolkit's promoted `skills/` dir are eligible
to shadow** — a candidate in `candidates/` never shadows. This reuses the harness's existing audited,
human-attended persistence gate (no second persistence path is added — the spike's recommendation, OQ5).

### 7.3 Resolution order (frozen)
At the materialize pass (§3), per host slot the precedence is:

```
fork (promoted toolkit skill, supersedes: <name>)   >   overlay-materialized base   >   pristine base
```

A NEW pure module `tools/kata_supersede.py` resolves shadows:

| Function | Contract |
|---|---|
| `resolve_shadows(agentskills_dir) -> dict[str, Path]` | Scan `<agentskills_dir>/skills/**/SKILL.md`; return `{upstream_name: fork_dir}` for every promoted skill carrying a non-empty `supersedes`. PURE (no git). |
| `validate_shadows(shadows, base_names) -> list[str]` | Fail-closed checks: a `supersedes` target that is not an actual base skill is an ERROR; two forks superseding the same upstream is an ERROR (ambiguous precedence). |

The `--update`/install orchestration calls `resolve_shadows` (when `agentSkills.dir` is configured), then the
materialize pass installs the fork body (not the base) into each shadowed slot, marking the slot
`source: "fork"` in `materialized.json`. The engine's in-repo dupe guard (`_flat_link_skills:150-154`) is
unaffected — it only ever sees the repo's own skill set; the fork lives outside it, and precedence is resolved
by the new pass, not the frozen fn.

### 7.4 Validator implications (47/0 preserved — frozen)
- `validate_skills` scans **only** `skills/` + `modules/` (`*/*/SKILL.md`, confirmed `validate_skills.py:79-84`)
  → forks in `<agentSkills.dir>` are **never scanned**; the count stays **47/0**.
- A shadowed upstream skill **still exists in the repo and is still validated** — shadowing suppresses it from a
  *host slot*, it does not delete the base. So no repo skill leaves the validated set.
- **Decision (frozen): shadowed/forked skills are NOT validated by `validate_skills`** — their conformance is
  governed by `kata-promote` (stage 2) + the STANDARDS §1.3 agent-distilled discriminators, exactly as today's
  toolkit candidates are (STANDARDS §1.3, `:80-83`). `validate_shadows` (§7.2) adds the only new structural
  check, and it asserts *precedence integrity*, not frontmatter conformance.

---

## 8. Uninstall polish (orphaned-link sweep · dry-run · messaging)

The existing `uninstall()` (a D126 NEW function, not one of the 5 frozen fns — additively editable) iterates
`iter_skill_dirs(home)` = **current basenames**, so a renamed/removed skill leaves an orphaned host link
(requirement item 2a / spike PART-B Finding 5).

**The sweep (frozen):** add `_sweep_managed_slots(skills_dst, home) -> (removed, left_intact)` that enumerates
**every entry** in the host skills dir (not only current basenames) and removes an entry **iff**:
- it is a **symlink whose resolved target is under `home`** (an orphaned kata link), OR
- it is a **dir carrying `.kata-managed`** (a kata copy or a materialized slot).

**Fail-closed (frozen):** anything else — a non-kata dir, a symlink pointing outside the home, an unreadable
entry — is reported in `leftIntact` and **never removed**. This is the same signal the engine already trusts
(`:115-123`); the sweep just applies it to the whole directory instead of a basename list, so a rename/remove
can no longer orphan a link. The sweep also clears any materialized slots' markers and prunes
`materialized.json` entries it removed.

**Dry-run / `--list` (frozen):** a `--dry-run` flag computes the removal plan (what *would* be removed vs left
intact) and **changes nothing**, printing the plan (and `--json` emits it as data). Reuses the same
classification logic, short-circuiting before any `unlink`/`rmtree`.

**Messaging (frozen, consumption-grade):** uninstall reports counts, the explicit `leftIntact` list with the
reason ("not kata-managed"), and the scope honesty already shipped (router stanza covers the supplied target
only — `uninstall.sh:14-20`). No surprises, no overclaim.

---

## 9. Factory-reset (`--factory-reset` / `--reinstall`)

Restores the pristine baseline while keeping all user-owned data. **Confirm-gated** (reuses the existing
`--non-interactive`/`--yes` assertion; interactive runs require an explicit confirmation).

**`--factory-reset` (engine, NO git) does:**
1. Read `materialized.json`; for each materialized slot: remove the concrete materialized dir and **restore the
   pristine base** to its recorded `baseMode` (re-`_link_or_copy` for symlink/copy) — composing the frozen fn.
2. Clear the materialization record.
3. Re-write the version stamp + manifest.

**KEEPS (never deleted):** `.kata-settings.json`, `.kata/`, `.planning/*`, the vault, `agentSkills.dir` (forks),
**and the overlay store itself** — so factory-reset un-materializes but a subsequent `--update` re-applies the
preserved overlay. This is the key distinction from update: **update preserves overlay AND re-materializes;
factory-reset preserves overlay but drops materializations (back to pristine links).**

**`--hard` flag (frozen):** `--factory-reset --hard` ADDITIONALLY clears the overlay store
(`overlay.json` → emptied) so the next update yields a fully pristine tree with no overlay. The optional
`git reset --hard <ref>` of the tracked tree is the **bootstrap's** job (`update.sh --factory-reset --hard`),
never the engine's. Distinguish the three:

| Operation | Base tree | Overlay store | Materialized slots |
|---|---|---|---|
| `--update` | clean-overwrite (bootstrap git) | **preserved** | **re-materialized** |
| `--factory-reset` | re-linked pristine | **preserved** | **dropped → pristine links** |
| `--factory-reset --hard` | re-linked pristine (+ optional bootstrap `git reset --hard`) | **cleared** | **dropped → pristine links** |

In Phase A (before the overlay layer exists), `--factory-reset` degenerates cleanly to "re-link/re-copy
pristine + re-stamp (+ optional bootstrap `git reset --hard`)" — a coherent clean reinstall. Phase B extends it
to also drop materializations. This is additive layering.

---

## 10. New / changed file-ownership map

| Path | Disposition | What changes | Phase |
|---|---|---|---|
| `tools/kata_version.py` | **NEW** (pure, git-free) | stamp + manifest read/write/compute; `is_pristine`; `suite_semver` | A |
| `tools/tests/test_kata_version.py` | **NEW** | TDD for the version surface | A |
| `update.sh` / `update.ps1` (repo root) | **NEW** (bootstrap, MAY git) | fetch → ff/reset → `--update --git-sha` → propagate exit; `--check`; `--factory-reset[ --hard]` git passthrough | A |
| `tools/kata_install.py` | **ADDITIVE** | NEW `main()` branches: `--update`, `--factory-reset`/`--reinstall`, `--hard`, `--dry-run`, `--git-sha`; NEW fns `_materialize_pass`, `_factory_reset`, `_update`, `_sweep_managed_slots`; uninstall sweep extension. **5 frozen fns + existing branches UNCHANGED.** | A (update/reset/sweep), B (materialize wired), C (shadow wired) |
| `tools/tests/test_install_update.py` | **NEW** | TDD: `--update` idempotency, factory-reset restore, sweep, dry-run, exit codes | A |
| `tools/kata_overlay.py` | **NEW** (pure) | overlay read/validate/apply/write + `adaptation_context` + materialized-record I/O | B |
| `tools/tests/test_kata_overlay.py` | **NEW** | TDD for store + apply + context | B |
| `skills/meta/kata-improve/SKILL.md` | **ADDITIVE STEP** | NEW "local-adaptation mode" section (§6.2) + the dev-repo/install split + safety rail. Existing kata/T2/LEARN sub-modes preserved. | B |
| `tools/kata_supersede.py` | **NEW** (pure) | `resolve_shadows`, `validate_shadows` | C |
| `tools/tests/test_kata_supersede.py` | **NEW** | TDD for precedence + fail-closed | C |
| `skills/meta/kata-promote/SKILL.md` | **ADDITIVE STEP** | NEW note: a promoted fork carrying `supersedes:` becomes shadow-eligible at next install/update (the binding). Existing review flow preserved. | C |
| `.gitignore` | **ADDITIVE** | add `.kata-version`, `.kata-manifest.json`, `.kata-overlay/` | A |
| `docs/SETUP.md` | **ADDITIVE** | replace the §4 manual-update prose with the shipped `update.sh`/`--update`; add factory-reset + the overlay/fork model (honest) | A (update), B/C (overlay/fork) |
| `docs/STANDARDS.md` | **ADDITIVE** | one line: `supersedes:` is now wired at install/update precedence (no schema change) | C |
| `README.md` | **ADDITIVE** | one-liner update/factory-reset block | A |
| `tools/kata_settings.py` | **NOT TOUCHED** | item-3 territory — DISJOINT (sibling freeze owns it) | — |
| `_flat_link_skills`, `_link_or_copy`, `install`, `copy_project`, `confirm_platform` | **NOT TOUCHED** | composed only | — |

---

## 11. Invariant-compliance section (explicit)

| Invariant | How this design honors it |
|---|---|
| 5 engine fns composed, never rewritten | All new work is NEW modules + NEW `main()` branches + NEW post-D126 fns. The materialize pass runs **after** `_flat_link_skills`; factory-reset **re-uses** `_link_or_copy`. No frozen fn is edited. **Freeze-gate flag: none of the 5 require a change.** |
| kata_install NEVER git | All git (`fetch`/`checkout`/`reset`/`pull`) is in `update.sh`/`update.ps1`. The engine receives the SHA via `--git-sha`. `kata_version`/`kata_overlay`/`kata_supersede` are git-free. `copy_project` stays `shutil`-only; uninstall never gits. |
| Additive-first / strict BC | Every new flag defaults to today's behavior; absent ⇒ byte-for-byte unchanged install/uninstall/headless. Existing tests pass unchanged. |
| validate_skills 47/0 | Forks live outside the repo tree (never scanned); shadowed upstreams stay present + validated. The only new structural check (`validate_shadows`) is precedence integrity, separate from `validate_skills`. |
| Snyk medium+ 0 | All new Python is stdlib + hashlib + shutil; `..`-guarded paths (reuse `_safe_abs`); JSON parsing fail-closed; no subprocess in the pure modules. Scanned per task gate. |
| Item 3 disjoint | Nothing here touches `tools/kata_settings.py`. The overlay/version/manifest are SEPARATE files with SEPARATE modules; `write_settings` is never called by new code. |
| Non-clobber preserved | Materialized slots carry `.kata-managed`; the sweep + factory-reset reuse the existing symlink-under-home / `.kata-managed` signal; fail-closed on ambiguity. |
| User state survives git | overlay/version/manifest/materialized are git-ignored; `git reset --hard` in the home never touches them. |

---

## 12. The live-proof definition (D124 / L12 — NOT just unit tests)

The acceptance bar includes a **realistic live exercise on a real install**, on **both shells** (POSIX via Git
Bash, Windows via PowerShell), not only green unit tests.

**Origin fixture (minor-d, frozen): a LOCAL BARE REPO.** The proof clones the home from a **local bare git
repo** (`git init --bare <tmp>/kata-origin.git`, push the current tree to it), so the "advance a ref" step
(below) is a reproducible **offline** push to that bare repo on both shells — no network, no GitHub dependency,
deterministic on POSIX and Windows alike. The default-home clone points its origin at this bare repo for the
duration of the proof.

The live proof MUST exercise, in sequence, on a real `~/.kata-home`-style clone (origin = the local bare repo):

1. **Install** (one-command) → assert `.kata-version` + `.kata-manifest.json` written; host slots present;
   `linkMode` honest (symlink on DevMode/POSIX, copy on Win-no-DevMode).
2. **Live update** — advance a ref by pushing a commit to the **local bare origin**, run `update.sh`; assert
   the home fast-forwarded, the host slots refreshed (copy-mode re-copied; symlink-mode tracked), the stamp
   re-written to the new SHA, exit `0`; re-run `update.sh` → idempotent "already current" no-op. Also assert
   the **M2 dirty-tree guard**: dirty a tracked base file, run `update.sh` → it ABORTS without mutating; re-run
   with `--discard-local` → it proceeds.
3. **Overlay-materialize proof** — author an overlay entry (frontmatter override + an append block) for one
   skill via `kata-improve` local-adapt mode; run `--update`; assert that **one** host slot is now a concrete
   materialized `SKILL.md` (base + overlay), carries both markers, is recorded in `materialized.json`, while
   every other slot stays a symlink/copy; assert the composed SKILL.md is valid and contains the override +
   appended block.
4. **Reconfigure** — re-run install with `--parent-dir` and confirm (per the sibling item-3 freeze) that
   `confirmedPlatforms` is preserved AND the overlay/materialization survives the reconfigure.
5. **Factory-reset** — run `--factory-reset`; assert the materialized slot reverts to its pristine
   symlink/copy, the overlay store is **preserved**, user data (`.kata-settings.json`, `.planning/`) intact;
   then `--update` re-applies the overlay. Run `--factory-reset --hard`; assert the overlay store is now
   cleared and the tree is fully pristine.
6. **Fork/shadow proof** — promote a toolkit fork carrying `supersedes: <name>` via `kata-promote`; run
   `--update`; assert the shadowed host slot serves the fork body (not the base), `materialized.json` marks it
   `source: "fork"`, and `validate_skills` is still **47/0**.
7. **Uninstall** — run the uninstaller (after a skill rename in the home to force an orphan); assert **no
   orphaned kata-managed host link** remains, non-kata entries are left intact, `--dry-run` previewed the plan
   without changing anything, and re-running is a `0` no-op.

Gate: pytest green (≥1765 existing + new) · `validate_skills` 47/0 · Snyk medium+ 0 on new/changed Python ·
offline smoke on both shells · the above live proof captured · fresh-context `kata-evaluate` PASS.
