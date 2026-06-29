---
title: "FREEZE — write_settings MERGE-fix (item 3 of install-update-polish)"
status: FROZEN MINI-SPEC (pre-build; awaits freeze-gate review)
date: 2026-06-29
spec: install-update-polish
item: 3 of 3 — the ONLY working-pattern edit
follows: D121 (multi-model confirm state), D126 (install/onboarding final polish)
decision: TBD (assign a D-number at freeze-gate sign-off)
class: EDITS A WORKING PATTERN (kata_settings.py — #14 of the 18 NOT-TOUCHED) → OWN freeze-gate + strict BC
file_ownership: tools/kata_settings.py + tools/tests/test_kata_settings.py ONLY (DISJOINT from items 1–2)
tags:
  - kata/settings
  - strict-bc
  - preserve-more-lose-less
---

# FREEZE — `write_settings` MERGE-fix

> **The single working-pattern edit in the whole requirement.** `tools/kata_settings.py` is one of the 18
> NOT-TOUCHED working patterns. This freeze is intentionally conservative: **preserve-more / lose-less, additive,
> strict backward-compatible.** The change must only PRESERVE keys `write_settings` does not own — it must NEVER
> alter the keys it does own, and EVERY existing test must pass byte-for-byte unchanged.

---

## 1. Problem

`write_settings` rebuilds the settings dict from scratch and writes it **wholesale**, so any key it does not
itself emit is silently dropped on every reconfigure.

Exact lines (`tools/kata_settings.py`):

```
114  def write_settings(parent_dir, vault_dir=None, home=None) -> Path:
...
125      if not Path(parent_dir).is_dir(): raise ValueError(...)
127      if vault_dir not in (None, "") and not Path(vault_dir).is_dir(): raise ValueError(...)
129      data = build_settings(parent_dir, vault_dir)     # <-- builds ONLY owned keys, from nothing
130      p = settings_path(home)
131      p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")   # <-- wholesale overwrite
132      return p
```

`build_settings` (lines 64–76) returns **only** `{settingsVersion, parentDir, vaultDir}`. It never reads the
existing file, so `confirmedPlatforms` — written by `add_confirmed_platform` (lines 90–106) and the D121
confirm-probe in `kata_install.confirm_platform` → `_record` (`kata_install.py:314-317`) — is absent from
`data` and is therefore erased by the line-131 write.

**Concrete failure:** a machine confirms `codex` (`confirmedPlatforms: ["codex"]` on disk). The operator later
re-runs install with `--parent-dir` (which calls `write_settings`). Line 129 rebuilds without `confirmedPlatforms`,
line 131 overwrites the file, and the confirm state is gone. The multi-model router
(`kata_roles.py:6,63`, which reads `confirmed_platforms()`) now refuses off-host roles until the operator
re-runs `--confirm`. Recoverable, but a release must not silently lose state (REQUIREMENT item 3, lines 82–88).

**Ownership of `confirmedPlatforms`:** written ONLY by `kata_settings.add_confirmed_platform` (called via
`kata_install._record`); read by `kata_settings.confirmed_platforms` and `tools/kata_roles.py`. `write_settings`
is **not** a writer of this key — it has no business touching it. That is precisely why erasing it is a bug.

---

## 2. Merge semantics (frozen)

Replace the "build-from-nothing → overwrite" body with **load-existing → overlay owned keys → write**:

1. **Validate** `parent_dir` / `vault_dir` exactly as today (lines 125–128 unchanged — same `ValueError`s,
   same messages, same order). Validation happens FIRST, before any read, so a bad arg still fails the same way.
2. **Load existing** settings from `settings_path(home)` if the file is present.
   - File absent → treat as empty `{}` (behaves exactly like today).
   - File present but unparseable → **fail-closed** (raise; see §4). Do NOT fall through to `{}` here — that
     would re-introduce the wholesale clobber this fix exists to prevent.
   - **Do NOT reuse `read_settings` for this load.** `read_settings` (lines 79–87) deliberately swallows
     corrupt/unreadable files and returns `{}` (a documented BC1 degrade for the *run* path). Using it here
     would turn a corrupt file into a silent clobber. The merge needs its own strict raw-load+parse. Leave
     `read_settings` itself untouched.
3. **Overlay the owned keys.** Compute the owned dict via the existing pure `build_settings(parent_dir,
   vault_dir)` and shallow-merge it ON TOP of the loaded dict: `merged = {**existing, **owned}`. Owned keys
   replace; every other present key is carried through verbatim.
   - **`vaultDir` wrinkle (the one place a naïve overlay would re-clobber).** `build_settings` always emits
     `vaultDir: None` when no vault is supplied, so `{**existing, **owned}` would overwrite a pre-existing
     `vaultDir` path with `None` — the exact clobber bug, just for the vault key. Therefore, **after** the
     overlay, apply the vault-preserve rule: **if `vault_dir` was NOT supplied** (`vault_dir in (None, "")`),
     set `merged["vaultDir"] = existing.get("vaultDir")` — i.e. preserve the prior on-disk value; fall back to
     `None` only when there is no prior. The key is ALWAYS present (never drops below today's "vaultDir always
     present" shape). When `vault_dir` IS supplied, the overlay's resolved path stands (owned-set wins).
     The prior value is preserved verbatim **without** re-validation (we did not validate an unsupplied vault;
     a stale prior path is the operator's existing state, not something this call asserts).
4. **Write** `json.dumps(merged, indent=2) + "\n"` to the same path (same serialization as line 131 and as
   `add_confirmed_platform` line 105 — trailing newline preserved).

### Key ownership (frozen list)

| Key | Class | write_settings behavior |
|---|---|---|
| `settingsVersion` | **OWNED** (set by `build_settings`) | always set to `SETTINGS_VERSION` (1) every call — unchanged from today |
| `parentDir` | **OWNED** | always set from the supplied `parent_dir` (resolved, `..`-guarded) — unchanged |
| `vaultDir` | **OWNED (set-when-supplied / preserve-prior-when-absent)** | supplied ⇒ resolved path (owned-set wins); NOT supplied ⇒ preserve the prior on-disk `vaultDir`, else `None`. Always present. **This is the deliberate "preserve-more" change folded in per operator Q2 — see §4.** |
| `confirmedPlatforms` | **PRESERVE** (owned by `add_confirmed_platform`) | carried through verbatim when present; never created, never modified |
| *any other / future key* | **PRESERVE by default** | carried through verbatim — the general rule below |

### General rule (so future keys are safe by default)

> `write_settings` owns exactly the keys `build_settings` emits (`settingsVersion`, `parentDir`, `vaultDir`).
> It REPLACES `settingsVersion` + `parentDir` on every call, and sets `vaultDir` when a vault is supplied
> (else preserves the prior). Every other key found on disk is PRESERVED untouched. A key added to
> `.kata-settings.json` in the future by some other writer is preserved automatically — no change to
> `write_settings` is required. Preservation is the default; ownership is the explicit, enumerated exception.

This is a denylist-of-owned / allowlist-everything-else design: the safe direction. There is no enumerated list
of "preserved" keys to keep in sync — anything not owned survives.

---

## 3. Strict BC contract (proof per existing test)

Every existing test in `tools/tests/test_kata_settings.py` must pass **unchanged**. The merge (now including the
folded-in vault-preserve rule) alters behavior in exactly two situations — (i) a pre-existing on-disk file
containing un-owned keys, and (ii) a second write WITHOUT a vault after a prior write WITH one — **and no existing
test exercises either.** Proof of identity with today's `data = owned`: whenever (a) the file does not pre-exist
(`existing == {}` → `merged == owned`, and the vault-preserve fallback yields `None` exactly as `build_settings`
would), or (b) only owned keys are present and no prior vault path exists (overlay overwrites them →
`merged == owned`). **vault-preserve only diverges from today when a prior `vaultDir` PATH is on disk AND the new
call supplies no vault — a sequence no existing test performs (verified below).**

| # | Test | What it locks | Why merge is identical |
|---|---|---|---|
| 1 | `test_build_settings_shape` | `build_settings` returns version+parentDir+vaultDir(None) | `build_settings` is NOT modified. Untouched. |
| 2 | `test_build_settings_with_vault` | vaultDir resolves to abs path | `build_settings` untouched. |
| 3 | `test_missing_parent_raises` | blank parent → ValueError | `build_settings` untouched; called after validation. |
| 4 | `test_traversal_rejected` | `..` path → ValueError | `_safe_abs`/`build_settings` untouched. |
| 5 | `test_write_read_roundtrip` | write→read returns parentDir; on-disk `settingsVersion==1` | **No pre-existing file** (fresh `tmp_path`), single write, **no vault supplied, no prior vault**. `existing=={}` → overlay gives `vaultDir:None`; vault-preserve fallback `existing.get("vaultDir")` → `None` (no prior) → **vaultDir stays `None`, byte-identical to today.** Re-verified for the folded-in rule. |
| 6 | `test_read_absent_returns_empty` | `read_settings` → `{}` when absent | `read_settings` untouched. |
| 7 | `test_write_rejects_nonexistent_parent` | bad parentDir → ValueError("parentDir") | Validation (lines 125–126) runs FIRST, unchanged, before any load. |
| 8 | `test_write_rejects_nonexistent_vault` | bad vaultDir → ValueError("vaultDir") | Validation (lines 127–128) runs FIRST, unchanged. |
| 9 | `test_confirmed_platforms_add_and_read` | add/read confirmedPlatforms via `add_confirmed_platform` | That function is NOT modified; does not call `write_settings`. |
| 10 | `test_add_confirmed_blank_rejected` | blank platform → ValueError | `add_confirmed_platform` untouched. |
| 11 | `test_harness_home_env_override` | `$KATA_HOME` honored | `harness_home` untouched. |
| 12 | `test_harness_home_self_locate` | self-locate to repo root | `harness_home` untouched. |
| 13 | `test_settings_path_location` | path = `<home>/.kata-settings.json` | `settings_path` untouched. |

Only test #5 calls `write_settings` successfully, and it does so against a fresh `tmp_path` with no pre-existing
file, no vault supplied, and no prior vault → the merge's load yields `{}`, the overlay sets `vaultDir:None`, and
the vault-preserve fallback also yields `None` → output is byte-identical to today. **No existing test sequences a
write-with-vault followed by a write-without-vault** (the only sequence vault-preserve changes): #7/#8 raise before
writing, #9/#10 use `add_confirmed_platform` (not `write_settings`), and every other test never calls
`write_settings`. **Therefore folding in vault-preserve breaks NONE of the 13 — BC holds.** The change is purely
additive: it preserves more, and alters none of the keys it owns relative to today's observable behavior.

---

## 4. Edge cases + recommended handling

| Edge case | Recommended handling | Justification |
|---|---|---|
| **File absent** | Load yields `{}`; `merged == owned`. Behaves exactly like today. | Strict BC; this is the common install case. |
| **File present, corrupt / unparseable JSON** | **FAIL-CLOSED: raise `ValueError` with a clear message** (e.g. `kata_settings: refusing to overwrite unparseable settings file: <path>`). Do NOT silently treat as `{}`, do NOT clobber. | The whole point of this fix is "do not silently lose state." Silently degrading a corrupt file to `{}` and then overwriting would erase whatever (possibly recoverable) data was there — the exact clobber bug, just triggered by corruption instead of reconfigure. Failing closed surfaces the problem and keeps the old file on disk for inspection. Mirrors `build_settings`/`_safe_abs` fail-closed posture (lines 43, 70, 126). NOTE: this DIVERGES from `read_settings`'s lenient `{}` degrade (lines 86–87) — that divergence is intentional: a *reader* feeding the run path may degrade to in-repo BC1, but a *writer* about to overwrite must not destroy data it cannot understand. |
| **Unknown / extra keys present** | **Preserve verbatim** via the `{**existing, **owned}` overlay. | The general rule (§2). Future-proof by default. |
| **Partial supplied args** (e.g. reconfigure with `--parent-dir` but no `--vault-dir`) | **PRESERVE the prior `vaultDir`** (deliberate "preserve-more", folded in per operator Q2). When `vault_dir` is not supplied, `merged["vaultDir"] = existing.get("vaultDir")` — keep the prior on-disk path; fall back to `None` only when no prior exists. The key is always present. | This is the same "lose-less" principle as `confirmedPlatforms`: a `--parent-dir`-only reconfigure should not silently drop the vault the operator already configured. It is BC-safe because **no existing test sequences write-with-vault → write-without-vault** (§3, re-verified). When there is no prior vault, the result is `None` — byte-identical to today, so fresh installs are unchanged. The prior path is preserved WITHOUT re-validation (an unsupplied vault is not asserted by this call; a stale prior is the operator's existing state). To explicitly *clear* a vault, a future caller would pass an explicit sentinel — out of scope here; not needed for the install/reconfigure path. |

---

## 5. Test plan (new tests — all in `tools/tests/test_kata_settings.py`)

All pure except `tmp_path` as a fake harness home (matches existing style).

1. **`test_write_preserves_confirmed_platforms`** — the headline. Seed the file via
   `add_confirmed_platform("codex", home=tmp_path)` (and `"kiro"`), then call
   `write_settings(proj, home=tmp_path)`. Assert `read_settings(home=tmp_path)["confirmedPlatforms"] == ["codex", "kiro"]`
   AND `parentDir` updated to `proj.resolve()`. Proves a `--parent-dir` reconfigure preserves prior confirm state.
2. **`test_write_updates_owned_keys`** — write once with `proj1`, then again with `proj2` (and once with a vault).
   Assert `parentDir`/`vaultDir`/`settingsVersion` reflect the latest supplied owned values each time (owned keys
   still replace correctly — preserve-more must not break update).
3. **`test_write_corrupt_file_fails_closed`** — write garbage (`"{not json"`) to `settings_path(home=tmp_path)`,
   call `write_settings(proj, home=tmp_path)`, assert it raises `ValueError`, and assert the garbage file is
   **unchanged** on disk (state not clobbered).
4. **`test_write_preserves_unknown_key`** — hand-write a file containing an un-owned key
   (e.g. `{"settingsVersion":1,"confirmedPlatforms":[],"futureKey":"keep-me"}`), call `write_settings`, assert
   `futureKey == "keep-me"` survives in the re-read result. Proves the general preserve-by-default rule.
5. **`test_write_preserves_vault_dir_when_absent`** — the folded-in vault rule (operator Q2). First
   `write_settings(proj, vault_dir=vault, home=tmp_path)` (vault is a real dir), then a second
   `write_settings(proj2, home=tmp_path)` with **no vault supplied**. Assert the re-read `vaultDir` still equals
   `vault.resolve()` (prior preserved) AND `parentDir` updated to `proj2.resolve()`. Proves a `--parent-dir`-only
   reconfigure does not drop a previously-configured vault.
6. **`test_write_updates_vault_when_supplied`** — first write with `vault1`, then a second write supplying
   `vault2`. Assert the re-read `vaultDir == vault2.resolve()` (owned-set wins when supplied; preserve does not
   block an explicit update). Pairs with #5 to lock both arms of the set-when-supplied / preserve-when-absent rule.
   Also assert that a first-ever write with no vault yields `vaultDir is None` (no-prior fallback = today's shape).
7. **Strict-BC regression check** — explicit gate step, not a new test body: run the FULL existing
   `test_kata_settings.py` (all 13) + `test_kata_install.py` (confirm-probe at `:180`) and confirm green,
   unchanged. (Documented in §6 Gates.)

---

## 6. File ownership (DISJOINT)

- **`tools/kata_settings.py`** — the `write_settings` body only (validation lines 125–128 unchanged; merge logic
  replaces lines 129–131). May add ONE small private parse helper for the strict raw-load (e.g. `_load_existing`).
  Do **not** touch `read_settings`, `build_settings`, `add_confirmed_platform`, `confirmed_platforms`,
  `harness_home`, `settings_path`, `_safe_abs`.
- **`tools/tests/test_kata_settings.py`** — append the 4 new tests above.

**Nothing else.** This freeze is DISJOINT from items 1 (`--update`) and 2 (uninstall polish) — no shared files.
`kata_install.py`, `kata_roles.py`, bootstrap scripts, skills, protocol/config are all OUT of scope here.

---

## 7. Gates

| Gate | Target | Notes |
|---|---|---|
| **pytest — existing** | all 13 `test_kata_settings.py` + `test_kata_install.py` green, unchanged | strict-BC proof (§3, §5.7) |
| **pytest — new** | 6 new tests green (§5.1–5.6) | preserve (confirmedPlatforms + vault + unknown) + update + fail-closed proof |
| **Full suite** | ≥1765 passed (REQUIREMENT acceptance) + new | no regression elsewhere; the flaky `test_benchmark.py::...test_importing_fixture_gives_q_one` is a known D124 env-sensitivity caveat, NOT a regression of this change |
| **validate_skills** | **47 / 0** | **no skill is touched by this item — expected unaffected.** Confirm it still reports 47/0 as a no-op sanity check (the edit is pure-Python in `tools/`, zero skill surface). |
| **Snyk** | medium+ **0** on the changed Python | re-scan `tools/kata_settings.py` after the edit per the global Snyk-at-inception rule; fix+rescan until clean |
| **Realistic reconfigure proof (D124 "reproduce, don't trust")** | live, not just unit | In a scratch home: write settings + `add_confirmed_platform` to seed `confirmedPlatforms: ["codex"]`, run a real reconfigure (`python kata_install.py ... --parent-dir <other>` or a direct `write_settings` against a real `~/.kata-settings.json` copy), then read the file back and SHOW `confirmedPlatforms` is still `["codex"]` AND `parentDir` changed. Capture the before/after file contents as the proof artifact. |

---

## 8. Open questions for the operator

1. **[RESOLVED — fail-closed.]** Corrupt-file policy: `write_settings` raises `ValueError` and leaves the old
   file untouched (no auto-backup, no silent `{}`-degrade). §4 stands as written. *(Operator-confirmed Q1.)*
2. **[RESOLVED — fold in vault-preserve now.]** A reconfigure without `--vault-dir` **PRESERVES** the prior
   on-disk `vaultDir` (falls back to `None` only when no prior exists). This is a deliberate "preserve-more"
   change, no longer deferred, incorporated into §2/§3/§4/§5. BC re-verified: it breaks none of the 13 existing
   tests because none sequence a write-with-vault followed by a write-without-vault. *(Operator-confirmed Q2.)*
3. **Merge depth.** `confirmedPlatforms` is a flat list and the overlay is a shallow merge — sufficient for every
   key that exists today. Confirm no nested-dict settings are anticipated that would need a deep merge (none exist
   now; shallow is correct and simpler).
4. **Helper vs inline.** Acceptable to add one small private `_load_existing` helper inside `kata_settings.py`
   (keeps the strict raw-load separate from the lenient `read_settings`)? Recommended; confirm it does not count
   as "touching another working-pattern function" for freeze-gate purposes (it is NEW, additive, private).
