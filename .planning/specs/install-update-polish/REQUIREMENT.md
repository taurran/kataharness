---
title: "install-update-polish — release-readiness for update / uninstall / settings"
status: REQUIREMENT (intake brief, pre-grill — NOT frozen)
date: 2026-06-29
spec: install-update-polish
follows: D126 (install/onboarding final polish), D121 (multi-model confirm state)
decision: TBD (assign a D-number at freeze)
tags:
  - kata/install
  - release-readiness
  - update
  - uninstall
  - settings
---

# install-update-polish — release-readiness for update / uninstall / settings

> **Intake brief, NOT frozen.** This is the requirement to bring into next session's **grill** → freeze → recipe build.
> It captures three release-polish work items the operator wants done **for the ACTUAL release**: once they are done,
> **the operator installs and runs a full test environment.** Nothing here is a LOCKED decision yet — the grill resolves
> the open knobs, then a freeze-gate adversarial review, then the orchestrated build. Two of the three items are
> ADDITIVE; **item 3 is the single item that edits a working pattern and therefore needs its own freeze-gate + strict BC.**

## Why (the problem)
D126 finished off the *install + onboarding* surface (one-command bootstrap, headless flags, grill-for-goals, router
stanza) — but it deliberately stopped at install. **Three release-grade gaps remain in the lifecycle AROUND install:**
there is **no functional UPDATE path** (re-running the curl one-liner does not actually update an install), the
**UNINSTALL** is built but has a couple of release-clean rough edges, and `write_settings` **clobbers** multi-model
confirm state on reconfigure. The operator will install + run a full test environment once these are polished, so they
must be release-honest, idempotent, and not lose state.

## Scope — three work items

### Item 1 — One-command UPDATE path *(the headline gap — there is NO functional update today)*
**Evidence (cite at grill):**
- `install.sh` clones the harness to `~/.kata-home` (a real git repo) but on re-run **REUSES it without pulling**
  (`install.sh:51-56`) — so re-running the `curl|sh` one-liner does **NOT** update.
- Symlink installs (mac/linux, win+DevMode) can update via `git pull` in the home (the symlinks track the home).
- **COPY installs** (Windows default, no DevMode) need `git pull` in the home **THEN re-run the engine to re-copy**
  (`docs/SETUP.md:78`) — two steps, manual today.
- There is **no `--update` flag, no version check, no update notification.** Skills carry per-skill semver in
  frontmatter, but there is **NO install-level version surface** today.

**Requirement:** a **single-command update** — a `--update` flag on `kata_install.py` and/or `update.sh` / `update.ps1`
bootstrap scripts — that:
1. **(a)** pulls/fetches the harness home to the target ref;
2. **(b)** re-links / re-copies skills in **one step**;
3. **(c)** works on **BOTH** link modes (symlink and copy);
4. **(d)** is **idempotent** + **honest about copy-vs-symlink** (state which mode it took, and that copy-mode propagates
   only on update/reinstall);
5. **(e)** *(optional, grill-decide)* an **install-level version stamp** + a **"newer version available"** check.

**Flags:** keep ADDITIVE; mirror the D126 G1/G2 pattern (bootstrap scripts wrap the existing engine; do NOT fork it).
**Constraint:** do **not** edit the **5 `kata_install.py` engine functions** (`_flat_link_skills`, `_link_or_copy`,
`install`, `copy_project`, `confirm_platform`) **unless freeze-gated** — they were byte-for-byte untouched in D126 and
none of the 18 working patterns were altered. An `--update` path should compose them, not rewrite them.

**Open knobs for the grill:** does `--update` live on the engine, the bootstrap scripts, or both? · what is the
"install-level version" surface (a `.kata-version` stamp? the git ref of the home?) · is the "newer available" check
opt-in/online, or purely local (compare home ref vs a pinned ref)? · does update re-run `--confirm` for platforms, or
strictly preserve existing confirm state (ties to item 3)?

### Item 2 — UNINSTALL polish *(mostly built — make it release-clean)*
**Already built + verified live (D126):** `kata_install --uninstall --target-dir` + `uninstall.{sh,ps1}` remove skills +
`.kata-settings.json` + the router stanza; scoped to the supplied target; idempotent; non-kata guard; verified live on
both shells.

**Polish items:**
- **(a) Orphaned host-link sweep — PART B Finding 5.** If a skill was **renamed or removed** between install and
  uninstall, its orphaned host link survives, because uninstall only removes the **basenames currently in the home**.
  Consider **sweeping all kata-managed slots** (every link the harness is responsible for) rather than only the
  currently-present basenames.
- **(b) Cross-project stanza tracking.** Router-stanza removal is scoped to the **SUPPLIED target only** — there is **no
  registry** of where stanzas were written across projects. Either **document this clearly** (uninstall only cleans the
  target you point it at) or add **light tracking** (a small registry of stanza-written targets).
- **(c) Preview.** Consider a `--list` / **dry-run** preview (show what uninstall would remove, change nothing).
- **(d) Messaging.** Confirm the uninstall messaging is **consumption-grade** (clear, honest about scope, no surprises).

**Constraint:** ADDITIVE; preserve the existing scoped/idempotent/non-kata-guard behavior. The sweep (a) must not remove
non-kata or unrelated links — fail-closed on ambiguity.

### Item 3 — `write_settings` MERGE-fix *(the one item that EDITS a working pattern — needs its OWN freeze-gate)*
**Evidence:** `kata_settings.write_settings` **OVERWRITES** `~/.kata-settings.json` **wholesale**, so an install with
`--parent-dir` **drops any `confirmedPlatforms`** (the D121 multi-model confirm state). Recoverable today via
re-`--confirm`, but a release should **not silently lose state**.

**Requirement:** make `write_settings` **MERGE** — preserve keys it does **not** own (especially **`confirmedPlatforms`**)
so install / reconfigure never clobbers multi-model confirm state. The change is **preserve-more / lose-less**.

**CAUTION — this is the single working-pattern edit in the whole requirement.** `kata_settings.py` is one of the **18
NOT-TOUCHED working patterns**. Therefore:
- it needs its **OWN freeze-gate** (separate from items 1–2, which are additive);
- **strict BC:** every existing `write_settings` test must **still pass** — the change only *preserves more*, never
  changes the keys it does own;
- add tests proving a `--parent-dir` reconfigure **preserves** a pre-existing `confirmedPlatforms`.

**Open knobs for the grill:** read-merge-write vs a structured merge helper · what counts as a key `write_settings`
"owns" vs "must preserve" · behavior when the on-disk file is corrupt/partial (fail-closed, keep the old file?).

## Honest non-blocking notes to carry into the grill (do not lose)
- **pyyaml lives only under `tools/`** — `build_intent` / `write_intent` must run from `tools/`. The **install path is
  stdlib-only** and unaffected. (Not a blocker for any of the three items.)
- **Windows copy-mode fallback** means harness skill updates need a **reinstall/update to propagate** — **item 1 directly
  addresses this UX.**
- The known **env-sensitive** test `test_benchmark.py::TestRunDualGateCwd::test_importing_fixture_gives_q_one` is **green
  canonically (1765 passed)** but flaky in some sandbox venvs — **NOT a regression** (D124 caveat); not in scope here.

## Additive-vs-working-pattern flags (for the freeze)
| Item | Class | Freeze handling |
|---|---|---|
| 1 — `--update` path | **ADDITIVE** (new flag + bootstrap scripts; compose the 5 engine fns, do not edit) | normal freeze-gate; engine functions stay untouched unless explicitly freeze-gated |
| 2 — uninstall polish | **ADDITIVE** (sweep + tracking + dry-run + messaging) | normal freeze-gate; preserve scoped/idempotent/non-kata-guard behavior |
| 3 — `write_settings` MERGE | **EDITS A WORKING PATTERN** (`kata_settings.py`, 1 of the 18) | **OWN freeze-gate + strict BC**; all existing tests pass; preserve-more/lose-less |

## Acceptance criteria (start-with-the-end-in-mind — refine at grill, G3 style)
- Re-running the one-command install/update on an existing install **actually updates** it (home pulled, skills
  re-linked/re-copied) on **both** link modes, idempotently, with honest copy-vs-symlink messaging.
- Uninstall leaves **no orphaned kata-managed host links**, even across a skill rename/remove; scope is documented or
  tracked; a dry-run preview exists; messaging is consumption-grade.
- An install with `--parent-dir` **preserves** a pre-existing `confirmedPlatforms`; every existing `write_settings` test
  still passes.
- Gates: pytest green (≥1765 + new tests), `validate_skills` 47/0, Snyk medium+ 0, offline smoke on both shells, and —
  per the D124 lesson — a **realistic live update/uninstall/reconfigure proof** (not just unit tests).

## Definition of done
All three items grilled → frozen → built through the recipe → gated → operator merge gate → checkpoint (new D-number,
supersede-never-rewrite). **Then the operator installs and runs a full test environment** (the trigger for this work).
