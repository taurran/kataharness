---
title: "SPIKE — local skill modification: in-place merge vs overlay/parameter-store vs hybrid"
status: SPIKE (read-only design investigation — NOT frozen, NOT a decision)
date: 2026-06-29
spec: install-update-polish
informs: Item 1 (one-command UPDATE path) — the "update never clobbers local change" guarantee
decision: TBD (assign a D-number at freeze; this spike only frames the choice + recommends)
tags:
  - kata/install
  - update
  - overlay
  - config-over-fork
  - skill-lifecycle
---

# SPIKE — when a user's install locally modifies a core skill, how do we reconcile on update?

> **Read-only design spike.** Grounds the (A) in-place + 3-way-merge / (B) overlay-parameter-store /
> (C) hybrid choice in codebase evidence. Patterns are framed **generically** (overlay, parameter store,
> config-over-fork, materialize-on-install). No external/proprietary system is named.

## The question (restated)

When a USER's installed harness locally modifies a **core skill** (`skills/**`), do we:
- **(A)** keep editing skill files **in place** and reconcile on update with a **3-way merge**;
- **(B)** abstract local modifications into an **overlay / parameter-store** layer so upstream files stay
  pristine and update is always a **clean overwrite**; or
- **(C)** a **hybrid**.

## What is already settled (given — not re-derived here)

- The **automatic learning loop** (validation-misses, recurrence-hardening **T2 drafts**, LEARN feed,
  agent-distilled candidates) **never touches upstream files**. It writes only to the **target project's**
  `.planning/*.jsonl` + `LESSONS-LEARNED.md` (relative to the working-branch root — `protocol/config.md:8`,
  `protocol/validation-misses.md:71,80`) and to **two external dirs** (`engram.learnFeed.dir`,
  `agentSkills.dir` — both "**Outside this repo's `skills/` tree**", `protocol/config.md:26-27`).
- The **only** collision is `kata-improve`'s human-invoked **"kata" mode**, which deliberately edits
  `skills/**`, `protocol/`, `docs/`, `README.md` **in place** and bumps semver.
- The home is a full git clone at `~/.kata-home`. Per-skill `version` is **HELD at 0.1.0** pre-release
  (non-discriminating — `STANDARDS.md:100-106`). **No install-level version stamp.** **No frontmatter marker
  for "locally edited / pinned."**

This spike therefore concerns exactly **one narrow surface**: a user who runs `kata-improve` (or hand-edits)
against their installed skill tree, and what `--update` (Item 1) does to those local edits.

---

## Finding 1 — `kata-improve`'s edit taxonomy (THE CRUX)

Read in full: `skills/meta/kata-improve/SKILL.md`. The governing discipline is stated up front:

> *"Next experiment — the smallest change to a skill/doc that moves toward the target. **One step, not a
> rewrite.**"* (`SKILL.md:42-43`)
> *"Edit the skill body; **bump its semver** (PATCH wording/fix, MINOR new capability, MAJOR contract
> change)."* (`SKILL.md:46`)

The kata is **biased by design toward small, additive, evidence-cited experiments**, not wholesale
rewrites. Categorizing the kinds of change it makes, with an overlay-fit verdict for each:

| # | Edit category | Evidence | Overlay-fit verdict |
|---|---|---|---|
| 1 | **Frontmatter knob** — `status`, `cost-weight`, `allowed-tools`, `version` bump | `SKILL.md:46` ("bump its semver"); the whole frontmatter schema is `STANDARDS.md §1` | **Parametric → clean overlay.** A frontmatter-override map materializes trivially. |
| 2 | **Appended guard / folded lesson / rubric item** — fold accumulated lessons; recurrence-hardening proposes "a **protocol contract clause + a mechanical test**" appended as a standing rule | `SKILL.md:3-6` ("fold accumulated LESSONS-LEARNED … into the SKILLS"), `:116-120` (proposed guard text + test sketch) | **Append-able → clean overlay** (a keyed prepend/append block). **This is the dominant kata shape.** |
| 3 | **Threshold / wording tweak inside body prose** — change a number or a sentence mid-body | implied by "PATCH wording/fix" (`:46`) | **Awkward middle.** Overlay can express it cleanly **only if** the body is refactored to read a *parameter*; otherwise it is a small fork (a line-level patch overlay cannot do without diff machinery). |
| 4 | **Deep prose-method rewrite / contract change (MAJOR)** | "MAJOR contract change" (`:46`) — but explicitly rare ("**one step, not a rewrite**", `:43`) | **Fork only.** Not expressible as overlay data. |
| 5 | **Whole new skill** → delegates to `kata-write-skill` | `SKILL.md:31,48` | **Orthogonal / additive.** No collision with any upstream file; lands as a new repo skill or an external toolkit candidate. Not an overlay concern at all. |
| 6 | **Deprecation / retire** → `deprecated/` + `supersedes` | `SKILL.md:48-49` | **Fork/supersede semantics** (see Finding 2). |

**Rough proportion (judgment, anchored on the "one step, not a rewrite" discipline):**
- **~60–70%** of intended per-run edits are **categories 1–2 (parametric / append-able)** → cleanly carried
  by an overlay as **data**.
- **~15–25%** are **category 3 (mid-body wording/threshold)** → the boundary case; overlay-expressible only
  with a body refactor or a line-patch mechanism.
- **~10–15%** are **category 4 (deep rewrite / MAJOR contract change)** → genuinely fork-only, but rare by
  the kata's own discipline.
- Categories **5–6 are orthogonal** to the in-place-vs-overlay question.

**Conclusion:** an overlay / parameter-store **can carry the majority of real local change**. The genuine
fork cases are a deliberate minority. This is the single strongest piece of evidence, and it points at a
**hybrid**: overlay for the parametric/append bulk, fork for the rewrite tail.

---

## Finding 2 — the fork / supersede machinery is **declared but largely unwired (aspirational)**

- **`supersedes:`** is **declared** in the schema (`STANDARDS.md:32`) and in the lifecycle prose
  ("retiring → `deprecated` + `supersedes` on the replacement", `STANDARDS.md:116`). **It is wired
  nowhere.** Grep across `tools/**` and all skill bodies: **zero** functional references —
  `validate_skills.py` does not read it; `kata_install.py` does not read it; no skill frontmatter populates
  it. It is a **dormant field**.
- **The external-toolkit path IS real as an *authoring/persistence* mechanism:** `agentSkills.dir`
  (`protocol/config.md:27`) is a toolkit root **outside** `skills/`; `kata-write-skill` authors candidates
  into `<agentSkills.dir>/candidates/` (`kata-write-skill/SKILL.md:49-58`); `kata-promote` is the human gate
  that moves a cleared candidate into `<agentSkills.dir>/skills/<category>/`
  (`kata-promote/SKILL.md:36-49`). These pieces work and are governed.
- **But SHADOW-BY-NAME is unwired.** Nothing installs `agentSkills.dir` into the host at all — the installer
  only flat-links the repo's `skills/` + `modules/` (`kata_install.py:56-65, 138-160`). The flat-link keys on
  **dir basename** and runs **dupe-detection only WITHIN the repo's own skill set**
  (`kata_install.py:150-154`) — it raises on a repo-internal name collision but has **no notion of precedence
  resolution** between a repo skill and a toolkit skill of the same name. There is **no load-time mechanism by
  which a local toolkit skill overrides an upstream skill by name.**

**Verdict:** the conceptual scaffolding for "fork to a superseding skill" **exists and is governed**
(separate toolkit dir + authoring + human promotion gate), but the **binding that makes a fork actually
shadow an upstream skill by name is ASPIRATIONAL.** Activating the hybrid's fork-leg means **wiring the
dormant `supersedes` field into install-time precedence** — modest, additive work, not a from-scratch build.

---

## Finding 3 — host load model: flat file, **no runtime compose** → any overlay must **materialize**

Confirmed from `tools/kata_install.py` + `docs/SETUP.md`:

- An installed skill is a **flat `SKILL.md`** under `~/.claude/skills/<name>/` (claude) or
  `<host>/.agents/skills/<name>/` (codex/kiro) — `kata_install.py:138-160`, `SETUP.md:69-73`.
- The install mechanism is **symlink-first, copy-fallback** (`kata_install.py:108-135`; Windows-without-
  Developer-Mode falls back to copy, `SETUP.md:75-80`).
- **There is NO runtime compose/overlay layer.** The host model reads exactly the bytes in that flat file.

**Implication for design (load-bearing):** any overlay is **purely an install/update-time construct**. The
effective skill = **base + overlay → one materialized `SKILL.md`**, written at install/update time. Two modes
differ sharply:
- **Symlink mode** has **no materialization seam** — the host reads the live repo file directly. An overlaid
  skill must therefore be **promoted from a symlink to a concrete materialized file** (break the link, write
  base+overlay). **Factory-reset = drop the overlay → restore the symlink.**
- **Copy mode** materializes naturally (a copy is already a write; write base+overlay instead of a verbatim
  copy). The existing `.kata-managed` marker (`kata_install.py:105,132`) already distinguishes
  harness-written files from user files — the natural place to also record "this slot is materialized-with-
  overlay."

This is the mechanism cost of option (B)/(C): a **materialize step** keyed per-skill, plus symlink→concrete
promotion for overlaid skills. It is bounded and additive, but it is **not free**, and it only pays off if an
overlay is actually exercised.

---

## Finding 4 — mapping the overlay / parameter-store pattern onto the flat-file reality

**What an overlay schema realistically covers (the 60–70% from Finding 1):**
- `frontmatter-overrides: { <field>: <value> }` — keyed per skill name; applied over base frontmatter at
  materialize time (covers category 1).
- `prepend-blocks` / `append-blocks: [ { anchor?, markdown } ]` — structured guidance blocks merged into the
  body at a named anchor or at end-of-body (covers category 2 — the dominant append shape, and the
  recurrence-hardening "append a standing guard clause" shape).

**Where it breaks down:**
- **Category 3 (mid-body wording/threshold)** — an overlay of *blocks* cannot retarget an arbitrary mid-body
  sentence or number without either (a) the base body reading a **named parameter** the overlay supplies, or
  (b) a **line/diff patch** sub-mechanism (which re-introduces 3-way-merge fragility — the very thing option
  B is trying to avoid).
- **Category 4 (deep rewrite)** — out of scope for overlay by construction; this is the **fork** leg.

**The materialize step (base + overlay → effective `SKILL.md`):**
1. At install/update, for each skill: if an overlay entry exists for `<name>`, read base `SKILL.md`, apply
   `frontmatter-overrides`, splice `prepend/append-blocks`, write the result as a **concrete** file (and mark
   the slot materialized); else **symlink/copy verbatim** as today.
2. A fork (`supersedes: <upstream-name>`) suppresses materialization of the named upstream skill entirely and
   installs the fork in its slot — this is the dormant-machinery activation from Finding 2.
3. **Factory-reset** = delete the overlay/fork entry → next materialize reverts that skill to a clean
   verbatim base (symlink restored).

The overlay store is a **single user-owned file outside the skill tree** (natural home alongside
`.kata-settings.json`, which is already git-ignored — `.gitignore:13`), so a `git pull` of the home never
sees it and **update is always a clean overwrite of the base**.

---

## Recommendation — **(C) Hybrid, phased**, with a contract split

Adopt the conductor's framing, which the evidence supports cleanly:

> **Upstream skills are IMMUTABLE from the user's side** → update is always a **clean overwrite**.
> **Parametric / append-able** local change → **overlay / parameter store**.
> **Deep behavioral divergence** → **fork to a superseding toolkit skill** (reuse the dormant
> `supersedes` + `agentSkills.dir` + `kata-promote` machinery).
> **Factory-reset** = drop the overlay → clean base restored.

**Why hybrid over (A) or (B):**
- **Reject (A) in-place + 3-way merge.** A 3-way merge engine over prose `SKILL.md` files is the *most*
  machinery for the *least* exercised path (~1 user, version held at 0.1.0). It re-introduces conflict
  resolution — exactly the fragility we can avoid because the **base files have a single authoritative
  source** (the repo). YAGNI-violating.
- **Reject pure (B).** An overlay alone cannot express the category-4 deep-rewrite tail without degenerating
  into a line-patch (≈ option A). It needs the fork escape hatch — which already exists in dormant form.
- **(C) matches the data:** overlay carries the 60–70% parametric/append bulk; fork carries the 10–15%
  rewrite tail; the awkward category-3 middle is pushed toward "parameterize the body" or "if you must
  rewrite a sentence, fork the skill."

**The `kata-improve` CONTRACT CHANGE this implies (state it explicitly):** split the skill's two audiences.
- **Authoring-upstream** (the **dev repo**, the harness's own maintainers): `kata-improve` "kata" mode keeps
  editing `skills/**` **in place** and bumping semver — unchanged. This is where canonical improvement lives.
- **Local adaptation** (a **user's install**): `kata-improve` (or a thin local mode) **MUST NOT edit the
  installed base file**; it **emits an overlay entry** (parametric/append) or **authors a superseding fork**
  to the toolkit. Same skill, two emission targets, selected by "am I running in the dev repo or against an
  install?"

### YAGNI / v0.1 lens — the MINIMUM that guarantees "update never clobbers learning"

**The strongest finding for v0.1 is that the guarantee is *already mostly true for free*:** the learning
artifacts live in the **target project's** `.planning/` and two **external** dirs (Finding evidence:
`protocol/config.md:8,26-27`), and the updater touches **only** the home's `skills/` + `modules/`
(`kata_install.py:56-65`). A `git pull` on the home plus a re-link **cannot reach** the learning loop's
outputs. **The automatic loop is structurally safe today — no overlay needed to protect it.**

So the **v0.1 minimum (do this now):**
1. **Declare upstream skills immutable from the install side.** Document that `--update` (Item 1) performs a
   **clean overwrite** of the installed skill base — and that the installed base is **not a user-edit
   surface**. This is a one-paragraph contract statement + the `kata-improve` audience split above. **No
   engine code.**
2. **Land `--update` as a clean overwrite** (re-link/re-copy from the pulled home), per Item 1's additive
   plan — composing the five untouched engine functions, not editing them. Honest copy-vs-symlink messaging.
3. **Route any user who wants local divergence to the existing toolkit path** (`kata-write-skill` →
   `agentSkills.dir` → `kata-promote`), which the installer already leaves pristine. In v0.1 this needs **no
   shadow wiring**: the user's toolkit skill simply carries a **different name** (no collision), or they
   decline to install the upstream skill they are replacing.

This guarantees "update never clobbers learning" **with essentially zero new machinery** — because the only
clobber-risk surface (in-place edits to installed skills) is closed by **contract**, not by an engine.

### The clean v0.2 evolution path (build only when a user actually hits the wall)

1. **Overlay / parameter store** — a single user-owned file (alongside `.kata-settings.json`) with
   `frontmatter-overrides` + `prepend/append-blocks`, plus the **materialize step** of Finding 4 (and the
   symlink→concrete promotion for overlaid slots). Carries the parametric/append bulk. Factory-reset = drop
   the file.
2. **Wire `supersedes`** into install-time precedence so a named toolkit fork **shadows** an upstream skill
   by name — activating the dormant field (Finding 2) for the deep-rewrite tail.

Do **not** build a merge/overlay engine in v0.1. With ~1 user and per-skill versions frozen, an overlay
materializer would be **un-exercised code** carrying real maintenance + test surface.

---

## Open questions the operator must answer to freeze

1. **Contract split — does `kata-improve` get a real "local-adaptation" mode in v0.1, or is local
   modification simply declared OUT OF SCOPE for installs until v0.2?** (The cheapest v0.1 is: out of scope +
   documented; emit-overlay mode is v0.2.) This is the single biggest scoping decision.
2. **Does the spike's recommendation belong in *this* spec (install-update-polish) at all, or only the
   "update = clean overwrite + immutable-base contract" half**, deferring the overlay/fork machinery to its
   own later spec? (Recommended: only the clean-overwrite half + the contract statement land here; overlay is
   a separate v0.2 spec.)
3. **Symlink-mode materialization:** when (v0.2) a skill gets an overlay, are we comfortable **promoting that
   skill's symlink to a concrete materialized file** (losing the "edits to the repo show up immediately"
   property for *that one skill*)? Confirm this is acceptable, since it is intrinsic to any overlay on a
   flat-file host with no runtime compose.
4. **Overlay store location + format:** alongside `.kata-settings.json` (git-ignored, machine-local) as
   recommended? JSON to match settings, or YAML to match frontmatter? Per-install or per-project scope?
5. **`supersedes` activation:** is wiring install-time name-precedence in-scope for v0.2, and does a fork
   require going through `kata-promote` (human gate) before it can shadow an upstream skill — or may a user
   hand-place a fork? (Recommended: reuse the `kata-promote` gate; do not add a second persistence path.)
6. **Install-level version stamp (ties to Item 1e):** a hybrid's "is my overlay still compatible with the
   updated base?" question only becomes answerable once an install-level version surface exists. Decide
   whether the v0.2 overlay records the base version it was authored against (a staleness signal), or stays
   version-agnostic for v0.1.

## Invariants honored by this spike

- **Read-only** except this single artifact. No other file modified.
- The **18 working patterns** and the **5 `kata_install.py` engine functions** are untouched; the v0.1
  recommendation is **additive** (`--update` composes them) and closes the clobber surface **by contract**.
- `tools/kata_install.py` **NEVER invokes git** — unaffected; the home-pull stays in the bootstrap scripts
  (Item 1's stated design), not the engine.
- All patterns named **generically** (overlay, parameter store, config-over-fork, materialize-on-install).
