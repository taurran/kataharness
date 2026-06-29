---
title: "Install / Onboarding Final Polish — FROZEN PLAN"
status: FROZEN (2026-06-29) — disjoint-file-ownership slices; TDD/mutation-proof where code; build comes later
spec: install-onboarding
feature: "Feature 2 — install/onboarding final polish (G1–G4)"
gate: pytest green · validate_skills 0-errors · Snyk medium+ 0 · E2E smoke · kata-evaluate PASS
invariant: ADDITIVE-ONLY. Disjoint file ownership per slice. The 18 working patterns stay untouched.
tags: [plan, frozen, install, onboarding, additive, tdd]
---

# Feature 2 — Install / Onboarding Final Polish · FROZEN PLAN

Six small, independently-testable slices with **disjoint file ownership**. Code slices are TDD +
mutation-proof; skill/prose slices are prose-verified against the design. Slices A–C are pure code (no
skill edits); D–E touch one working skill each (ADDITIVE step only); F is docs + scripts. No two slices own
the same file.

## Wave / dependency DAG

```
Wave 1 (parallel):  A (router tool)   B (install headless flags+exit codes)   D (intent schema field)
Wave 2 (parallel):  C (uninstall verb — needs A+B)     E (initiate step 2g — needs D)
                    G4-onboard (needs A)                G3 already in E
Wave 3 (serial):    F (scripts + README/SETUP — needs B+C)  →  INTEGRATION GATE + E2E SMOKE
Wave 4 (serial):    PART A kata-evaluate  →  PART B (D98) kata-review
```

Wave-1 slices share no files. Wave-2 slices depend only on wave-1 symbols, not on each other.

---

## Slice A — `tools/kata_router.py` (NEW) · marked router-stanza contract

**Owns:** `tools/kata_router.py`, `tools/tests/test_kata_router.py` (both NEW).

**TDD (red→green):**
1. `render_stanza(summary)` returns 12–15 pointer-style lines naming entrypoints (`kata-bootstrap`,
   `kata-validate`) + state locations (`.kata/`, `.planning/`, `INTENT.md`, `kata.config`).
2. `write_stanza` **creates** `AGENTS.md` with one `<!-- kata:begin -->…<!-- kata:end -->` block when absent.
3. `write_stanza` is **idempotent**: a second call replaces the block in place — exactly one block, content
   outside the markers untouched (assert the pre/post surrounding bytes are identical).
4. `write_stanza` appends (does not clobber) when `AGENTS.md` exists without a kata block.
5. `remove_stanza` removes exactly the block; surrounding content preserved; absent block ⇒ no-op (no raise).
6. `..`-traversal path is rejected (mirror `intent_scaffold._safe_path`).

**Mutation-proof:** mutate the marker-match (begin/end swap), the "replace-in-place vs append" branch, and
the no-op-on-absent guard — each must fail a test. (Idempotency + exact-removal are the load-bearing
invariants the uninstaller depends on.)

---

## Slice B — `tools/kata_install.py` headless surface (ADDITIVE) · flags + exit codes + `--json`

**Owns:** the `main()`/CLI region of `tools/kata_install.py` (`:331-367`) + NEW helpers
`_exit_code_for`, `_emit`, `_load_answers_json`; `tools/tests/test_install_cli_headless.py` (NEW).
**Does NOT touch** `install()`, `confirm_platform()`, `copy_project()`, `_flat_link_skills()`,
`_link_or_copy()` (the working engine — read-only here).

**TDD:**
1. New flags parse: `--non-interactive`/`--yes`, `--answers-json`, `--json`, `--uninstall` (uninstall wired
   in Slice C; here assert the arg parses + routes).
2. Non-TTY auto-skip: monkeypatch `sys.stdin.isatty()→False` ⇒ non-interactive implied.
3. `--answers-json <path>` loads `{parentDir, vaultDir, platform}` ⇒ `kata_settings.write_settings` called;
   `..`-guard on the path. **Headless traceback hole:** a non-existent `vaultDir`/`parentDir` makes
   `write_settings` raise `ValueError` (`kata_settings.py:125-128`) — assert `main()` catches it and returns
   **`3 NOT_FOUND`** (no traceback); malformed/missing-key JSON ⇒ **`2 USAGE`**.
4. Env fallback: `KATA_PARENT_DIR`/`KATA_VAULT_DIR` used when flags absent; explicit flag wins.
5. **Exit-code mapper** (`_exit_code_for`): ok⇒`0`; unknown platform (`install_generic` ok:false)⇒`3`;
   bad `--answers-json` path / non-existent settings dir⇒`3`; simulated PERMISSION (OSError)⇒`4`; non-kata
   collision (the `:118-122` ValueError)⇒`5`; confirm-not-confirmed⇒`1` (unchanged). `main()` wraps
   `install()` **and the settings-write** in try/except to map instead of tracebacking. *(The engine
   functions are not edited — the try/except lives entirely in the `main()` region.)*
6. **`--json` split:** stdout is parseable JSON only; notes go to stderr (capture both streams).
7. **BC regression (stdout untested-gap fix):** without any new flag, `main(["--platform","claude",…])` rc + a
   **`capsys` stdout golden** match today (re-run the existing assertions from `test_kata_install.py:132-156`
   **plus** a captured-stdout byte compare proving the default mixed-stdout path at `:360-362` is unchanged).

**Mutation-proof:** mutate each exit-code branch constant (3/4/5) and the stdout-vs-stderr routing — each
must fail a test. **Idempotent re-install ⇒ `0` (no-op, no traceback, valid links present)** is asserted
explicitly (CONFLICT is ONLY the non-kata case; no `changed` flag is asserted).

---

## Slice C — `tools/kata_install.py` uninstall verb (ADDITIVE) · NEW `uninstall(...)` + CLI route

**Owns:** the NEW `uninstall(platform, harness_home, host_dir)` function in `tools/kata_install.py` + the
`--uninstall` dispatch in `main()`; uninstall tests added to `test_install_cli_headless.py`.
**Depends on:** Slice A (`kata_router.remove_stanza`), Slice B (CLI plumbing). **Reuses** the non-clobber
signal at `:104`/`:115-123` — does not modify it.

**TDD:**
1. `uninstall` removes a kata symlink (target under harness home) and a `.kata-managed` copy dir.
2. `uninstall` **leaves a non-kata dir intact** and reports it (never deletes user data) — the mirror of
   `test_refuses_to_clobber_non_kata_dir` (`:79-87`).
3. CLI `--uninstall` also unlinks `.kata-settings.json` (via `kata_settings.settings_path`) and calls
   `kata_router.remove_stanza` on a supplied `--target-dir/AGENTS.md`.
4. **Re-run is a no-op** (all absent ⇒ exit `0`, no raise).
5. Plugin-manifest removal is flag-gated (default keep).

**Mutation-proof:** mutate the symlink-target-under-home check and the marker check — removing a non-kata
dir must fail test 2.

---

## Slice D — INTENT schema field (ADDITIVE) · `acceptanceCriteria`

**Owns:** `tools/intent_scaffold.py` (`build_intent` frontmatter assembly `:111-137`),
`protocol/intent.md` (schema doc), and additions to `tools/tests/test_intent_scaffold.py`.
**Disjoint from** Slices A–C (different files).

**TDD:**
1. `build_intent` with `answers["acceptanceCriteria"]=[…]` emits the field as a YAML block list.
2. **BC:** `build_intent` with the field ABSENT produces **byte-identical** output to today (golden compare)
   — the field is added only when non-empty.
3. Field is OPTIONAL: omitting it never raises (not in required-key validation `:71-106`).
4. `write_intent` round-trips it through YAML.
5. `protocol/intent.md` documents `acceptanceCriteria` as optional; `validate_skills`
   `check_protocol_schemas` stays green (term documented).

**Mutation-proof:** mutate the "emit only when non-empty" guard ⇒ BC golden test (2) fails.

---

## Slice E — `kata-initiate` step 2g (ADDITIVE STEP) · acceptance-criteria in the mirror + gate

**Owns:** `modules/initiation/kata-initiate/SKILL.md` ONLY. **Depends on:** Slice D (the field exists).
**Prose-verified** (skill body, no code). Must PRESERVE `:152-287` mirror flow and `:310-380` S2 gate.

**Changes (additive prose):**
1. Insert sub-step **2g — enumerate + confirm acceptance/success criteria** **after 2e** (the sub-steps run
   2a → 2a-recall → 2b → 2c → 2d → 2e; there is no 2f, so 2g appends cleanly and does not interrupt the
   reference/find/routing sub-steps). Reflect checkable criteria back as a numbered list
   (start-with-the-end-in-mind).
2. Add criteria as load-bearing value **#9** (`:332-341`) + matching mirror-visibility and human-confirmation
   checklist items (`:346-374`), with the verbatim "blanket looks-good FAILS" rule retained.
3. **Confirmed-absent is valid (MAJOR-2 — no deadlock for empty/research runs).** Handle value #9 **exactly
   like conditional value #8** (single-host vs. multi-model) at `kata-initiate:341,360,370`: when there are no
   checkable criteria (research run, or the human opts out), an **explicit** "no acceptance criteria for this
   run" is a valid confirmation and the run PASSES with an **empty `acceptanceCriteria`**. The field stays
   OPTIONAL; the gate fails only on an un-itemized **unconfirmed** value — never on a legitimately empty one.
4. Add `acceptanceCriteria` to the Phase 4/6 `answers` dict (`:397-414`); `write_intent` stays sole writer;
   recall read-only invariant (`:143-149`) untouched.

**Verification:** a reviewer confirms (a) the existing mirror/infer-then-confirm text is unchanged except the
additions, (b) the S2 gate is strengthened not loosened **and accepts confirmed-absent** (an empty/research
run does not deadlock), (c) no other load-bearing value was altered.

---

## Slice G4-onboard — `kata-onboard` item 6 (ADDITIVE STEP) · offer the router stanza

**Owns:** `skills/coordinate/kata-onboard/SKILL.md` ONLY. **Depends on:** Slice A (`kata_router.write_stanza`).
**Prose-verified.** Must PRESERVE `:78-138` steps + `:46-61` honesty block.

**Changes (additive prose):**
1. Step 3 item **6 — offer the router stanza** (human-gated, after `.planning/` scaffold `:129`): OFFER to
   write the marked stanza into the target `AGENTS.md` by **invoking `kata_router.write_stanza` as executed
   Python** — the same convention as `intent_scaffold.write_intent` (`:130-135`) / `kata_settings.write_settings`
   (`:157-167`), so the no-duplicate / idempotent-upsert guarantee rides on the **tested** writer (Slice A),
   not a free-form skill `Write`. Declining leaves `AGENTS.md` untouched; note the uninstaller (Slice C)
   reverses exactly this block.
2. Add a `kata_router.write_stanza` row to the reuse map (`:153-167`) as **NEW** (honest provenance).
3. No `allowed-tools` change (existing `Write` grant covers it, `:16`).

**Verification:** reviewer confirms (a) the offer is opt-in under the existing human gate, (b) `CLAUDE.md`/this
repo's `AGENTS.md` are not touched (only the *target project's* `AGENTS.md`), (c) the step routes through the
executed `write_stanza` call. **Idempotency is proven where it runs** by the integration smoke step 5 (real
twice-write ⇒ exactly one block) — not by prose alone.

---

## Slice F — scripts + docs (NEW + ADDITIVE) · `install.sh`/`install.ps1`/uninstall + README/SETUP

**Owns:** `install.sh`, `install.ps1`, `uninstall.sh`, `uninstall.ps1` (NEW, repo root); `README.md`
(install block + honest tradeoff), `docs/SETUP.md` (one-liner paths + uninstaller section). **Depends on:**
Slices B + C (the engine flags + uninstall verb exist).

**Build:**
1. `install.sh` / `install.ps1` per DESIGN §2.1 (resolve `$KATA_HOME` or clone w/ `KATA_REF` pin → locate
   python → invoke engine → propagate exit code). Thin; **no install logic in shell** (parity by
   construction).
2. `uninstall.sh` / `uninstall.ps1` → `python tools/kata_install.py --uninstall …`.
3. README: add the `curl … | sh` / `irm … | iex` one-liners + the **honest** unaudited-remote-script tradeoff
   + clone + "Use this template" alternatives; point to `docs/SETUP.md`.
4. `docs/SETUP.md`: add the one-liner paths and replace the manual uninstall note (`:78-83`) with the shipped
   uninstaller (keep manual steps as the documented fallback).

**Testability (cross-platform — Windows host w/ Git Bash + PowerShell):**
- Shell scripts are smoke-tested, not unit-tested. Idempotency/correctness lives in the Python they call
  (Slices A–C), which IS unit-tested. Scripts are linted for parity (no bash-ism in `.ps1`; no
  `NUL`/`%VAR%`; `$env:VAR`).
- **Static lint (minor fix):** `install.sh`/`uninstall.sh` pass **`shellcheck`**; `install.ps1`/`uninstall.ps1`
  pass **`PSScriptAnalyzer`** (the PS equivalent). Both must **quote every interpolated value** forwarded into
  `git clone` and the engine invocation — `"$KATA_REF"`, `"$KATA_HOME"`, and any path arg — to close the
  low-severity self-injection / word-splitting hole (PS: `& python tools/kata_install.py --platform $p` with
  quoted args). The lint is part of the gate, not optional.
- **Checksum honesty (minor fix):** the README/script docs state plainly that a checksum protects only the
  **download-then-run** path, **not** the piped `curl|sh`/`irm|iex` form (DESIGN §2.1) — no overclaim.
- The live `curl|sh`/`irm|iex` **network** fetch is smoke-tested against a local/`file://`/fixture URL; the
  real CDN fetch is **exercised, not automatically proven** (carried to closeout, DESIGN §8).

---

## Integration gate + explicit E2E smoke (after Slice F)

**Standing gate (default-FAIL):**
- `uv run python -m pytest tools/tests/` green (incl. all NEW tests + the BC regressions).
- `uv run python tools/validate_skills.py` ⇒ **0 errors** (skills + protocol schema docs).
- **Snyk medium+ = 0** on every new/modified Python (`kata_router.py`, `kata_install.py`,
  `intent_scaffold.py`) — `mcp__Snyk__snyk_code_scan` per the global security rule; fix-and-rescan until clean.

**Explicit end-to-end smoke (both shells, this host):**
1. **Clean install** → engine flat-links skills; settings written from `--answers-json`. Exit `0`.
2. **Re-install** → idempotent **CONFLICT-free no-op**: **exits `0`, emits no traceback, and valid links are
   present** (kata-managed dirs replaced cleanly). **No `changed` field is asserted** (MAJOR-1 — the engine
   result dict is not extended). *(A planted non-kata dir ⇒ exit `5`, asserted separately.)*
3. **Uninstall** → host skills + settings removed and the router stanza removed **from the supplied
   `--target-dir`**; **no cruft left** (host artifacts + supplied target); re-run uninstall ⇒ `0` no-op.
4. **Headless `--answers-json` install** → no prompts, settings applied, `--json` machine output parses.
   Run once via **Git Bash** (`install.sh`) and once via **PowerShell** (`install.ps1`) — PowerShell parity
   verified.
5. **G4 stanza idempotency where it runs** → drive the `kata-onboard` router-stanza write (the executed
   `kata_router.write_stanza` call) **TWICE** against the same target `AGENTS.md`; assert **exactly one**
   `<!-- kata:begin -->…<!-- kata:end -->` block and that content outside the markers is unchanged. Then
   `--uninstall --target-dir <that project>` removes exactly that block.

---

## PART A — kata-evaluate (standing, default-FAIL)

Fresh-context, no-write `kata-evaluate` over the built feature: read the evidence (test output, validator,
Snyk, the smoke transcript) and return PASS/NEEDS_WORK. **Default-FAIL** — nothing is "done" until the
evaluator independently PASSes (`AGENTS.md:56-58`). Must specifically confirm: every change is additive (no
working-pattern behavior changed), the S2 gate is preserved in `kata-initiate`, and the uninstaller leaves no
residue.

## PART B — D98 kata-review (standing adversarial)

Standing `kata-review` (adversarial pre-done) red-teams the contract-bearing surfaces before merge:
- Try to make `write_stanza` duplicate or corrupt a user's `AGENTS.md`; try to make `uninstall` delete a
  non-kata dir; try to make a new exit-code path misreport success; try to make `--answers-json` traverse out
  of tree; try to make `acceptanceCriteria` break an old INTENT.md golden.
- Verify-before-reuse: confirm `kata_router` is labeled **NEW** (not "reuses existing convert flow") in
  `kata-onboard`'s reuse map.

---

## Residual risks (for the freeze-gate reviewer)

1. **Working-skill edits (G3/G4).** Slices E + G4-onboard are the only edits to working skills. Risk: an
   over-eager edit rewrites the mirror or the human gate. **Mitigation:** both are prose-only ADDITIVE
   inserts with explicit "preserve `:152-287`/`:310-380`/`:78-138`" guards and a reviewer diff check.
2. **S2 anti-drift gate.** Adding criteria as a load-bearing value must *strengthen* the gate, **without
   deadlocking empty/research runs** (MAJOR-2). **Mitigation:** Slice E retains the verbatim "blanket
   looks-good FAILS" rule AND treats value #9 like conditional value #8 — an explicit confirmed-absent
   ("no criteria for this run") PASSES with an empty `acceptanceCriteria`. PART A checks both the strengthen
   and the no-deadlock.
8. **Uninstall cross-project scope.** Router-stanza removal covers only the supplied `--target-dir` (no
   project registry, by design). **Mitigation:** stated plainly in DESIGN §2.2; the "no cruft" claim is scoped
   to host artifacts + the supplied target, never overclaimed.
3. **Exit-code BC.** Existing CLI tests assert `rc==0`; the mapper must keep success at `0`. Any reshuffle
   that moves success off `0` breaks them. **Mitigation:** Slice B test 7 re-runs the existing assertions.
4. **INTENT golden BC.** `acceptanceCriteria` must emit only when non-empty or old INTENT output drifts.
   **Mitigation:** Slice D test 2 is a byte-identical golden compare.
5. **PowerShell parity testability.** The live remote-fetch path can only be smoke-tested locally on CI; the
   real CDN `irm|iex` is *exercised, not proven*. **Mitigation:** all stateful logic is in unit-tested Python;
   scripts are thin + parity-linted; honest-scoped in closeout.
6. **PINNED INTENT schema.** Adding `acceptanceCriteria` is an additive amendment, not a fork — but a reviewer
   must confirm it is documented as OPTIONAL and no required-key check references it (else old INTENT.md
   fails). **Mitigation:** Slice D test 3 + the schema-doc note.
7. **Marker collision.** A target `AGENTS.md` that already contains literal `<!-- kata:begin -->` text would
   be matched. **Mitigation:** the upsert replaces in place (idempotent), so even a pre-existing marker is
   handled deterministically; documented in Slice A.
