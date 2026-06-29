---
title: "Install / Onboarding Final Polish — FROZEN DESIGN"
status: FROZEN (2026-06-29) — grill COMPLETE; decisions LOCKED; this is the freeze (build comes later)
spec: install-onboarding
feature: "Feature 2 — install/onboarding final polish (G1–G4)"
builds-on: install-portability/DESIGN.md (the engine), kata-initiate, kata-onboard
invariant: EVERY change is ADDITIVE / backward-compatible. The 18 working patterns stay untouched.
tags: [design, frozen, install, onboarding, additive]
---

# Feature 2 — Install / Onboarding Final Polish · FROZEN DESIGN

Four goals (G1–G4) layer ON TOP of the shipped install engine. **Nothing already working is rewritten.**
G1/G2 add NEW files + ADDITIVE flags to `tools/kata_install.py`. G3/G4 add **one ADDITIVE step each** to two
working skills (`kata-initiate`, `kata-onboard`) plus one OPTIONAL schema field and one NEW helper tool.

Every integration point below is cited `file:line` against the code read at freeze time. Line numbers are
anchors at freeze; the build cites by **stable symbol name** where the engine already prefers that discipline
(`kata-preflight/SKILL.md:56-57`).

---

## 0. Invariants (never relax) + the don't-break guarantee

1. **Additive-only.** No existing function signature changes. No existing code path changes behavior when the
   new flags/files are absent. Proof obligation per change is stated in §6.
2. **The 18 working patterns are untouched** (DESIGN don't-break list): flat-link install
   (`kata_install.py:107-159`), default-FAIL gates, frozen-plan/no-drift, two-way handoff, the 6 spine
   principles (`AGENTS.md:43-63`), readiness check, `project_find` determinism
   (`project_find.py:116-118`), persona/SOUL (`protocol/persona.md`), narration contract
   (`protocol/narration.md`), loop-init banner (`narration.md:125-148`), INTENT.md freeze
   (`protocol/intent.md:37-50`), grill-depth dial (`kata-bootstrap/SKILL.md:81-116`), the multi-model
   confirm-probe (`kata_install.py:265-323`, D121), settings+`project_find` UX, validator green, preflight
   structured-argv security (`kata-preflight/SKILL.md:33-48` — no freeform exec), worktree isolation, recall
   brief (`kata-initiate/SKILL.md:97-149`). Feature 2 reads these; it never edits their behavior.
3. **Never-git guarantee preserved.** The bootstrap shells MAY run `git clone` to *seed the harness home*
   (that is not a vault and not the user's project) — but `tools/kata_install.py` itself still NEVER invokes
   git (`kata_install.py:26-27`), and `copy_project` stays `shutil`-only. The uninstaller never runs git.
4. **Non-clobber preserved + extended.** Install refuses to overwrite a non-kata directory
   (`kata_install.py:115-123`, marker `.kata-managed` at `:104`). The NEW uninstall reuses the *same* signal:
   it removes a skills entry ONLY if it is a symlink whose real target is under the harness home, OR a dir
   carrying `.kata-managed`. Anything else is reported and **left intact** (never deleted).
5. **Headless = install + setup ONLY.** No new flag and no script grants the loop autonomy past setup. The
   loop's human gates (commit/merge/fix-approval) are out of scope and unchanged.

---

## 1. File-ownership map — NEW vs ADDITIVE vs NOT-TOUCHED

| Path | Disposition | What changes |
|---|---|---|
| `install.sh` (repo root) | **NEW** | POSIX bootstrap: locate/clone `$KATA_HOME` → invoke `tools/kata_install.py` with pass-through flags. Thin; no install logic. |
| `install.ps1` (repo root) | **NEW** | Windows parity of `install.sh` (`irm … \| iex`). Same contract, PowerShell idioms. |
| `uninstall.sh` / `uninstall.ps1` (repo root) | **NEW** | Thin wrappers → `tools/kata_install.py --uninstall …`. |
| `tools/kata_router.py` | **NEW** | Owns the marked router-stanza contract: `render_stanza`, `write_stanza`, `remove_stanza`. Used by G4 (write) + the uninstaller (remove). `..`-guarded, idempotent. |
| `tools/tests/test_kata_router.py` | **NEW** | TDD for the stanza contract. |
| `tools/tests/test_install_cli_headless.py` | **NEW** | TDD for the additive CLI surface (flags, exit codes, `--answers-json`, `--json`, uninstall). |
| `tools/kata_install.py` | **ADDITIVE** | NEW functions `uninstall(...)`, `_exit_code_for(result)`, `_emit(result, as_json)`; NEW argparse flags; NEW try/except mapping in `main()`. **Existing `install()`/`confirm_platform()`/`copy_project()`/`_flat_link_skills()` signatures + behavior UNCHANGED.** |
| `tools/intent_scaffold.py` | **ADDITIVE** | `build_intent` reads OPTIONAL `answers.get("acceptanceCriteria", [])`; emits the field only when non-empty (or always-as-`[]` — see §4). No required-key change ⇒ old call-sites unaffected. |
| `protocol/intent.md` | **ADDITIVE** | Document the NEW OPTIONAL `acceptanceCriteria: string[]` field. PINNED-schema note updated to record this additive amendment (additive ≠ fork). |
| `modules/initiation/kata-initiate/SKILL.md` | **ADDITIVE STEP** | Insert sub-step **2g — acceptance/success criteria** inside the existing Phase 2 mirror; add criteria to the load-bearing gate list + checklist; add the key to the Phase 4/6 `answers` dict. The existing mirror flow (`:152-287`) and the S2 gate (`:310-380`) are **preserved, not rewritten**. |
| `skills/coordinate/kata-onboard/SKILL.md` | **ADDITIVE STEP** | Add Step 3 item **6 — offer the router stanza** (human-gated) via `kata_router.write_stanza`; note the uninstaller reverses it. Existing steps (`:78-138`) preserved. |
| `README.md` | **ADDITIVE** | Add the one-liner install block + the honest `curl\|sh` / `irm\|iex` tradeoff note; point to `docs/SETUP.md`. |
| `docs/SETUP.md` | **ADDITIVE** | Add the one-liner paths, the uninstaller section (replacing the manual-removal note at `:78-83` with the shipped uninstaller — additive capability, the manual steps stay documented as the fallback). |
| `tools/kata_settings.py`, `tools/project_find.py` | **NOT TOUCHED** | Read by the new code; behavior unchanged. (`write_settings` + `confirmed_platforms` reused as-is.) |
| `kata-bootstrap`, `kata-readiness`, `kata-preflight`, `kata-loop`, all other skills | **NOT TOUCHED** | — |
| `protocol/persona.md`, `protocol/narration.md`, `AGENTS.md`, `CLAUDE.md` | **NOT TOUCHED** | `AGENTS.md` stays canonical; `CLAUDE.md` stays a pointer. G4 writes a stanza into the *target project's* `AGENTS.md`, never this repo's. |

---

## 2. G1 — Cross-platform one-command + GitHub install (NEW files)

### 2.1 Bootstrap script contract (`install.sh` / `install.ps1`)

Both scripts implement the **same 5-step contract**; the only difference is shell idiom (parity via §5).

1. **Resolve the harness home.** If `$KATA_HOME` is set and contains `tools/kata_install.py`, reuse it
   (idempotent — no re-clone). Else clone the repo to a default home (`~/.kata-home` POSIX /
   `$env:USERPROFILE\.kata-home` Windows), honoring `KATA_REF` (tag/sha **version-pin**) when set.
2. **No cruft.** The clone is the home itself; the bootstrap writes no temp files outside the home and
   removes any it creates. (The `.git` inside the cloned home is legitimate repo metadata, not cruft — it is
   what enables `update` via `git pull`; documented, not hidden.)
3. **Locate Python** (`uv run python` preferred, falling back to `python3`/`python`), per `docs/SETUP.md:19`.
4. **Invoke the engine** — `python tools/kata_install.py --platform <p> [pass-through flags]`. **All install
   logic stays in the engine** (no shell reimplementation). The script forwards `--platform`, `--parent-dir`,
   `--vault-dir`, `--host-dir`, `--yes/--non-interactive`, `--answers-json`, `--json`, `--confirm`, and the
   NEW `--uninstall` verb unchanged.
5. **Exit with the engine's exit code** (semantic codes propagate to the caller — §3.2).

**Security / honesty (README + script header):** the `curl … | sh` and `irm … | iex` forms are stated
**honestly** as "an unaudited remote script unless you read it first." Mitigations shipped: a **stable URL**,
**readable-before-run** (short script, printable), and a **`KATA_REF` version-pin**. **Checksum honesty
(minor fix):** a checksum protects the **download-THEN-run** path (fetch the script to a file, verify its
hash, then execute) — it does **NOT** protect the **piped** `curl … | sh` / `irm … | iex` form, where the
bytes are executed as they stream with nothing to hash first. The docs state this plainly and present
download-verify-run, the **git-clone path**, and **"Use this template"** as the audit-friendly alternatives
for users who want the checksum/inspection guarantee. (Folds RESEARCH §2.)

### 2.2 Uninstaller contract (`uninstall.sh` / `uninstall.ps1` → `kata_install.py --uninstall`)

Reverses **every change Feature 2 / the engine makes**, idempotently, never clobbering user data:

| Reverses | How | Guard |
|---|---|---|
| Flat-linked skills (`<host>/skills/<name>`, `.agents/skills/<name>`) | NEW `kata_install.uninstall(platform, harness_home, host_dir)` | Remove iff symlink→under-home OR dir carries `.kata-managed` (`:104`,`:115-123`). Else report + keep. |
| `.claude-plugin/plugin.json` | optional removal (flag-gated; default keep — it lives in the repo, not the host) | Only if explicitly requested. |
| `.kata-settings.json` | `kata_settings.settings_path(home)` unlink | Idempotent (absent ⇒ no-op). |
| **G4 router stanza** in the target `AGENTS.md` | `kata_router.remove_stanza(agents_md_path)` | Removes exactly the marked block; absent ⇒ no-op; never touches surrounding content. |

Re-running the uninstaller is a **no-op** (everything already absent). The uninstaller is the answer to the
most-cited "clean install" gap (RESEARCH §1).

**Scope honesty (minor fix) — router-stanza removal covers the SUPPLIED target only.** The host-level
artifacts (flat-linked skills, settings) are global and fully reversed. But the G4 router stanza is written
into *a project's* `AGENTS.md`, and **the harness keeps no registry of every project where a stanza was
written** (consistent with the deliberately simple, no-registry model of `install-portability` IP-A /
DESIGN §3 "Dropped: `~/.kata` registry"). So `--uninstall` removes the stanza **only from the `--target-dir`
the operator passes**; it does **not** crawl the filesystem hunting for other stanzas. Other projects'
`AGENTS.md` are the user's to clean (re-run `--uninstall --target-dir <that project>`). The "leaves no cruft"
claim is therefore scoped to the host artifacts + the supplied target — stated plainly, never overclaimed.

---

## 3. G2 — Agent-friendly / headless install+setup (ADDITIVE on `kata_install.py`)

Scope: **headless INSTALL + SETUP only.** Autonomous-loop mode is DEFERRED/off (Invariant 0.5).

### 3.1 Additive CLI flag surface (exact)

Existing flags (UNCHANGED): `--platform` (`:339`), `--home` (`:340`), `--host-dir` (`:341`),
`--parent-dir` (`:342`), `--vault-dir` (`:343`), `--confirm` (`:344-345`).

| NEW flag | Type | Behavior | BC |
|---|---|---|---|
| `--non-interactive` / `--yes` | store_true | Assert non-interactive; suppress any future prompt. Auto-enabled when `sys.stdin.isatty()` is False (non-TTY auto-skip). | Default off ⇒ today's behavior. The engine has no prompts today, so this is a forward-compat assertion + the bootstrap's contract. |
| `--answers-json <path>` | path | Load a JSON file of setup values (`{parentDir, vaultDir}`) and apply them (writes settings via `kata_settings.write_settings`). Supplies *all* setup up front for headless runs. `..`-guarded. | Absent ⇒ settings only written if `--parent-dir` given (today's path, `:348-352`). |
| `--json` | store_true | Machine JSON → **stdout**; human notes → **stderr**. | Absent ⇒ today's mixed-stdout (`:360-362`) unchanged. |
| `--uninstall` | store_true | Run the uninstall verb (§2.2) instead of install. | Absent ⇒ install (today's path). |

**Env-var config (additive fallbacks):** `KATA_HOME` already resolves the home
(`kata_settings.py:53`, `kata_install.py:49`). Add OPTIONAL `KATA_PARENT_DIR` / `KATA_VAULT_DIR` read as the
default for `--parent-dir`/`--vault-dir` when the flags are absent. Explicit flags win; env is fallback;
absent both ⇒ today's behavior.

**`--help` with real examples:** enrich the argparse `epilog` with copy-pasteable examples (claude install;
headless `--answers-json` install; uninstall; confirm-probe). Additive text only.

### 3.2 Semantic exit-code table (mapped in `main()` — ADDITIVE)

Today `main()` returns `0`/`1` (`:357`, `:363`). The build adds a pure `_exit_code_for(result, exc=None)`
mapper and a `try/except` around `install()`/`uninstall()` in `main()`. **Success stays `0`** (every existing
test asserting `rc == 0` still passes); argparse usage errors already exit `2` (unchanged).

| Code | Name | Meaning | Source |
|---|---|---|---|
| `0` | OK | Install ok, **idempotent re-install no-op**, confirm ok, or uninstall ok. | `result["ok"] is True`. Idempotent re-install of a kata-managed dir is a clean `0` no-op via the engine's existing unlink+relink (`:115-134`) — **no `changed` flag is added** (MAJOR-1; the engine result dict has no `changed` key and is not extended). |
| `1` | ERROR | Generic runtime failure / confirm-probe not confirmed (today's `:357`). | Preserved for the confirm path. |
| `2` | USAGE | Bad/missing args. | argparse default (unchanged). |
| `3` | NOT_FOUND | Harness home / target path / unknown-platform-with-no-install; **`--answers-json` path missing or a supplied `parentDir`/`vaultDir` is not an existing dir**. | `install_generic` `ok:false` (`:203-211`); missing `--answers-json` path; the `ValueError` from `kata_settings.write_settings` when `parentDir`/`vaultDir` does not exist (`kata_settings.py:125-128`), now caught + mapped. |
| `4` | PERMISSION | Host dir not writable; symlink AND copy both denied. | OSError from the link/copy fallback (`:128-134`). |
| `5` | CONFLICT | A **non-kata** dir occupies a skill slot (refuse-to-clobber). Distinct from idempotent re-install. | The `ValueError("…non-kata…")` at `:118-122`, now caught + mapped instead of tracebacking. |

**Settings-write failures are wrapped too (headless traceback hole):** `--answers-json` (and `--parent-dir`)
feed `kata_settings.write_settings`, which raises `ValueError` on a non-existent `parentDir`/`vaultDir`
(`kata_settings.py:125-128`). The same `main()` try/except catches it and maps it to **`3 NOT_FOUND`** (a bad
path), never an uncaught traceback. Malformed/unreadable `--answers-json` JSON or a missing required key maps
to **`2 USAGE`**.

**Engine functions are READ-ONLY in this feature (REAFFIRMED, MAJOR-1):** `_flat_link_skills`,
`_link_or_copy`, `install()`, `copy_project()`, and `confirm_platform()` are **not edited by any slice** —
no `changed` key is added, no idempotency flag is threaded through them. All new behavior (exit-code mapping,
`--json`, idempotency *observation*) lives in NEW `main()`-region code and NEW functions. Working pattern #1
(flat-link install) is therefore byte-for-byte preserved.

**CONFLICT semantics (the research's "CONFLICT=already-installed"):** an *already-installed kata-managed*
state is **not** an error — re-install is a clean `0` no-op (the engine's existing unlink+relink runs again
and yields valid links). **CONFLICT (`5`) is ONLY the non-kata-dir clobber** at `kata_install.py:118-122` — a
directory the harness did **not** create occupying a skill slot, needing human action. The build only maps
that existing refusal to a code instead of an uncaught traceback. This is additive: no existing test exercises
the traceback path.

### 3.3 `--json` channel split

`--json` ⇒ `json.dumps(result)` to **stdout** only; `result["notes"]` lines + human summary to **stderr**.
Without `--json`, the current behavior (`:360-362`, JSON + notes both on stdout) is byte-for-byte preserved.

---

## 4. G3 — Grill-for-goals: acceptance criteria (ADDITIVE step in `kata-initiate`)

### 4.1 Where it slots

A NEW sub-step **2g — enumerate + confirm acceptance/success criteria**, inserted inside the existing
**Phase 2 reflective goal mirror** (`kata-initiate/SKILL.md:152-287`), *after* 2b's conversational editing
and alongside the existing load-bearing values. It does **not** rewrite the mirror or the infer-then-confirm
flow — it adds one enumerated value-class to them (start-with-the-end-in-mind).

**Behavior:** infer candidate **checkable** success criteria from the goal + brief (e.g. "the CLI exits 0 on
a clean re-install", "uninstall leaves no `~/.claude/skills/kata-*`"), reflect them back in the mirror as a
numbered list, and require **per-criterion confirmation or correction** — exactly the S2 discipline. Frame
them as *how we'll know it's done*, not implementation.

### 4.2 S2 anti-drift STOP gate — PRESERVED (not weakened)

The infer-then-confirm gate (`:310-380`) is extended, not relaxed: acceptance criteria join the
**load-bearing values** list (`:332-341`) as item **9**, and the **gate checklist** (`:346-374`) gains a
matching pair of checks:

- *Mirror visibility:* "each acceptance criterion was individually named in the mirror (not only inferred);
  OR the human confirmed **'no acceptance criteria for this run'** by name."
- *Human confirmation:* "each criterion in `INTENT.md` traces to an explicit human approval or correction; OR
  a confirmed-absent decision is recorded (empty `acceptanceCriteria`)."

**Confirmed-absent is a valid confirmation, not a missing value (MAJOR-2 — no deadlock for empty/research
runs).** Value #9 is handled **exactly like conditional value #8** (single-host vs. multi-model routing) at
`kata-initiate:341,360,370`: when there are no checkable criteria (e.g. a `research` run, or the human opts
out), the human confirms that *explicitly* and the run PASSES with an **empty `acceptanceCriteria`** (the
field stays OPTIONAL — §4.3). The gate fails only on an **un-itemized, unconfirmed** value — never on a
legitimately empty one. The schema field is OPTIONAL and empty/research runs are first-class.

The standing rule holds verbatim: **a value inferred, not named in the mirror, and passed through with a
blanket approval FAILS the gate — even if correct** (`:372-374`). A blanket "looks good" over un-itemized
criteria does **not** confirm them; an **explicit** "no criteria for this run" **does**.

### 4.3 INTENT schema impact (minimal, additive, BC)

`protocol/intent.md` currently has **no** acceptance-criteria field; `readiness` (`:26`) is prose and
`features`/`fixes` (`:20-21`) are scope — neither is a checkable criteria list. The schema is PINNED
(`:5`) — slices may not *fork* it, but an **additive optional field is not a fork.** Add:

| Field | Type | Meaning |
|---|---|---|
| `acceptanceCriteria` | `string[]` (OPTIONAL) | Checkable success criteria captured in the mirror, start-with-the-end-in-mind. Absent ⇒ today's behavior (BC). |

- `tools/intent_scaffold.py` `build_intent` reads `answers.get("acceptanceCriteria", [])` and adds it to the
  frontmatter dict (`:127-137`) **only when non-empty** — so old answers dicts produce byte-identical INTENT
  output (BC proof). It is **not** added to the required-key validation (`:71-106`), so it can never fail an
  old call-site.
- `kata-initiate` Phase 4/6 `answers` dict (`:397-414`) gains the `acceptanceCriteria` key; `write_intent`
  stays the **sole** INTENT writer (recall's read-only invariant at `:143-149` is untouched).
- The validator's `check_protocol_schemas` (`intent.md:48-49`) documents the new term; since the field is
  optional, no existing INTENT.md is invalidated.

---

## 5. G4 — Project-router stanza at install (ADDITIVE step in `kata-onboard`)

### 5.1 The marker contract (`tools/kata_router.py` — NEW)

`AGENTS.md` is canonical (STANDARDS §4); the stanza is written into the **target project's** `AGENTS.md`,
never this repo's, and `CLAUDE.md` stays a pointer.

```
<!-- kata:begin -->
... ~12–15 pointer-style lines ...
<!-- kata:end -->
```

- `render_stanza(installed_summary) -> list[str]` — ~12–15 lines, pointer-style: **what's installed**
  (KataHarness skills) · **entrypoints** (`kata-bootstrap` to start a run, `kata-validate` to check) ·
  **where state lives** (`.kata/`, `.planning/`, `INTENT.md`, `kata.config`). Points to folders, not inline
  detail — respects the ~150–200-line instruction budget (RESEARCH §2).
- `write_stanza(agents_md_path, lines) -> dict` — **create** `AGENTS.md` with the marked block if absent;
  if present, **guarded idempotent upsert**: replace an existing `kata:begin..kata:end` block in place
  (never duplicate), else append the block. `..`-guarded path (mirrors `intent_scaffold._safe_path`).
- `remove_stanza(agents_md_path) -> dict` — remove exactly the marked block; absent ⇒ no-op; preserves all
  surrounding content; if the file was created solely for the stanza and is left empty, it MAY be removed
  (flag-gated; default leave). This is what the uninstaller calls (§2.2).

The marker pair is the idempotency primitive that replaces shell `grep -qF` — the guard lives in tested
Python so `install.sh`/`install.ps1` need no duplicated logic (parity, RESEARCH §4).

### 5.2 Where it slots in `kata-onboard`

`kata-onboard` Step 3 (`:113-138`) already offers human-gated conversion actions and scaffolds `.planning/`
(`:129`). Add **item 6 — offer the router stanza**: after `.planning/` scaffold, OFFER (never force) to write
the marked stanza into the target `AGENTS.md`. It is one more opt-in action under the existing human gate
(`:46-61` honesty block; `:113` "each confirmed before it happens"). Declining leaves `AGENTS.md` untouched.
The reuse map (`:153-167`) gains a `kata_router` row. The uninstaller (§2.2) removes exactly this block,
closing the loop.

**The no-duplicate / idempotent-upsert guarantee rides on EXECUTED Python, not prose (minor fix).** The step
**invokes `kata_router.write_stanza` as a Python call** — the same convention `kata-initiate` uses for
`intent_scaffold.write_intent` (`kata-initiate:383-414`, "`write_intent` is the only authorised writer") and
`kata-onboard` already uses for `intent_scaffold.write_intent` / `kata_settings.write_settings`
(`:130-135,:157-167`). The marker upsert is therefore enforced by the **tested** `write_stanza` (Slice A),
not by a free-form skill `Write`. `kata-onboard`'s `allowed-tools` already includes `Write` (`:16`); routing
the stanza through `write_stanza` adds no tool and changes no permission (additive within the existing grant)
while putting the idempotency guarantee where it is unit-tested.

---

## 6. How each change is proven additive / BC

| Change | Additive/BC proof |
|---|---|
| `install.sh`/`install.ps1`/uninstall scripts | NEW files; nothing imports/depends on them; absent ⇒ today's manual `python tools/kata_install.py` still works (`docs/SETUP.md:19`). |
| `kata_install.uninstall(...)` | NEW function; never called by `install()`; reuses the existing non-clobber signal (`:115-123`). |
| New CLI flags | All `store_true`/optional with today's defaults ⇒ omitting them reproduces current behavior; existing `test_kata_install.py` CLI tests (`:132-156`) still pass (they pass none of the new flags). |
| Exit-code mapper | Success path stays `0`; the only newly-reachable codes map *previously-uncaught exceptions* (CONFLICT/PERMISSION/NOT_FOUND) — no existing test asserts a traceback. |
| `--json` split | Gated entirely behind `--json`; default stdout output unchanged (`:360-362`). |
| `intent_scaffold` acceptanceCriteria | `answers.get(..., [])`; emitted only when non-empty ⇒ old answers ⇒ byte-identical INTENT (regression-asserted). Not a required key. |
| `protocol/intent.md` field | Documented as OPTIONAL; PINNED-schema amendment recorded as additive (not a fork); old INTENT.md stays valid. |
| `kata-initiate` step 2g | Additive prose inside Phase 2; the S2 gate is *strengthened* (one more confirmed value), never loosened; BC clause (`:485-488`) — INTENT absent ⇒ harness reads DESIGN as today — unchanged. |
| `kata-onboard` item 6 | Additive opt-in under the existing human gate; uses the existing `Write` grant; declining ⇒ no change. |
| `kata_router.py` | NEW; marker-scoped writes; `..`-guarded; idempotent upsert + no-op remove. |

---

## 7. Acceptance (default-FAIL, runnable)

- `kata_router` upsert is idempotent (write twice ⇒ one block); remove is exact + no-op when absent;
  `..`-guard rejects traversal.
- `kata_install` headless: `--answers-json` writes settings (bad path ⇒ exit `3`, malformed JSON ⇒ exit `2`);
  `--json` puts pure JSON on stdout + notes on stderr; **re-install of a kata-managed tree ⇒ exit `0`, no
  traceback, valid links present** (a `0` no-op — *not* CONFLICT, and no `changed` flag is asserted); non-kata
  collision ⇒ exit `5`; unknown platform ⇒ exit `3`; `--uninstall` removes links/settings/stanza and is a
  no-op on re-run.
- `intent_scaffold` round-trips `acceptanceCriteria` when present; absent ⇒ byte-identical to today.
- **End-to-end smoke (both shells):** clean install → re-install is a CONFLICT-free no-op (`0`) → uninstall
  leaves no cruft → headless `--answers-json` install. POSIX via Git Bash, Windows via PowerShell.
- Gate: pytest green · `validate_skills` 0 errors · Snyk medium+ 0 on new/modified Python ·
  `docs/SETUP.md` + README updated · the fresh-context `kata-evaluate` PASS.

## 8. Honest scope (carried to closeout)

- Codex/Kiro install stay **best-effort** ("verify in-host", `kata_install.py:12-14`) — unchanged, not a
  blocker.
- The live remote-fetch (`curl|sh` / `irm|iex`) network path is **exercised, not automatically proven** —
  CI smoke uses a local/fixture URL; the real CDN fetch is verified manually (persona.md honesty posture).
- Onboarding/Debug-Mode end-to-end remains **n=0 live** (`kata-onboard/SKILL.md:59-61`); G4 adds the stanza
  to that already-honest-scoped flow without changing its maturity claim.
