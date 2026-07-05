---
spec: context-autonomy
phase: CA-P0
title: engine + config — gauge math, settings marker mechanics, premium resolver branch, preflight bundle engine, installer fix, telemetry v3
status: frozen-candidate (pending plan gate)
created: 2026-07-04
branch: feat/context-autonomy
baseline: 280d1d2 (DESIGN FROZEN; master 2c81beb = v0.2.0; pytest 2505/3 skip, validator 48/0/0, Snyk medium+ 0)
tags: [kata/spine, context-autonomy, plan, CA-P0, engine, config]
---

# CA-P0 — engine + config (all Python decision code + the `kata.config` schema deltas)

Implements the mechanical substrate of DESIGN.md (FROZEN 2026-07-04): every number, comparator, and
fail-closed guard the prose legs (P1 adapter, P2 policy) will consume. **Nothing in P0 changes any
run's behavior by itself** — the new functions are dormant until P1/P2 wire them (BC §4 rows 3–5,
10, 12, 13 hold structurally). All decision-code parsing is **fail-closed (D136)**: absent/unparseable
input RAISES a named exception, never a permissive default — the graceful-degradation legs (stale
gauge ⇒ fallback) are *explicit return values from successful parses*, never silent exception
swallowing. Stdlib-only throughout (§7: "Verified: NO new external dependencies").

Build mode: direct with dispatched workers (one agent per task, disjoint files, conductor integrates —
the D137-L8 pattern). **Dogfood mandate:** the run config carries `inlineEval: "telemetry"`; every
worker dispatch carries the M4 checkpoint-commit + trailer mandate. Build workers tier down per D131
(coding class); gates run at anchor.

## Ownership (disjoint) + DAG

```yaml
ownership:
  E1: [tools/kata_gauge.py, tools/tests/test_kata_gauge.py]
  E2: [tools/kata_settings.py, tools/tests/test_kata_settings.py]
  E3: [tools/kata_models.py, tools/tests/test_kata_models.py, .planning/specs/model-tiering/DESIGN.md]
  E4: [tools/kata_preflight.py, tools/tests/test_kata_preflight.py]
  E6: [tools/kata_telemetry.py, tools/tests/test_kata_telemetry.py]
  E5: [tools/kata_install.py, tools/tests/test_kata_install.py, tools/tests/test_install_update.py]
  E7: [protocol/config.md]
waves:
  wave1: [E1, E2, E3, E4, E6]
  wave2: [E5, E7]
depends_on:
  E5: [E2]
  E7: [E1, E3, E4]
tasks:
  E1: { estimate: 45, class: code }
  E2: { estimate: 35, class: code }
  E3: { estimate: 40, class: code }
  E4: { estimate: 40, class: code }
  E5: { estimate: 35, class: code }
  E6: { estimate: 25, class: code }
  E7: { estimate: 20, class: code }
```

E8 (conductor closeout, after integration): run the full gauntlet (pytest grown from 2505, validator
48+/0/0, Snyk medium+ 0 on every new/changed `tools/*.py`), record the mutation-proof list for the
D-record, commit on `feat/context-autonomy`. Skill bumps and CHANGELOG are P2 (single CHANGELOG owner).

**Module-home note (compilation choice, not a design decision):** the DESIGN names no module for the
gauge/threshold arithmetic; `tools/kata_gauge.py` is this plan's home for it (NEW file — the DESIGN §7
"new runtime pieces" clause; mirrors the M4-P0 choice of `tools/kata_telemetry.py`). Everything else
lands in the exact modules the DESIGN cites by line.

## E1 — `tools/kata_gauge.py` (NEW; pure/stdlib; TDD + mutation proofs)

read_first: DESIGN §1 Leg A (CA-L1..L6), CA-L7, CA-L9, CA-L16, §2 "Bridge file", §9 tunables table;
GROUNDING-CLAUDE.md G1/G3; closest analog `tools/kata_risk.py` (pure decision module, no subprocess).

1. **`read_bridge(path, *, now_utc) -> dict`** — parse one bridge JSON file. Kata superset schema
   (CA-L2): `{session_id, remaining_percentage, used_pct, timestamp, total_tokens}`; the 4-field user
   bridge (no `total_tokens`, GROUNDING G3) parses as `mode: "percentage-only"`. Absent file ⇒ RAISES
   `GaugeError` (caller falls to the next priority leg explicitly); unparseable JSON / missing required
   fields / non-numeric values ⇒ RAISES (fail-closed — never "assume fine"). Staleness (CA-L3, quoted):
   "Bridge timestamp older than **300 s** `[TUNABLE]` ⇒ stale ⇒ deterministic fallback leg" — returned
   as `stale: bool`, computed against `now_utc`; the constant is a module-level `STALENESS_S = 300`.
2. **`resolve_gauge(kata_bridge_path, user_bridge_path, *, now_utc) -> dict`** — CA-L1 reader priority
   verbatim: "(1) kata bridge → (2) user bridge (4-field, %-only triggering) → (3) deterministic
   fallback". Returns `{source: "kata"|"user"|"none", ...}`; stale or absent at both legs ⇒
   `source: "none"` (CA-L3: "Stale or absent ⇒ never 'assume fine'").
3. **`trigger_crossed(gauge, fraction) -> bool`** — CA-L7/CA-L5: trigger = `fraction ×` the
   "HOST-REPORTED effective window" = the gauge's `total_tokens` (post-cap); percentage-only gauge ⇒
   CA-L2 degrade: "the trigger runs **percentage-only** (0.70 by %)". `fraction` default `0.70`
   (`DEFAULT_TRIGGER_FRACTION`); out-of-range fraction (≤0 or ≥1) ⇒ RAISES.
4. **`fallback_waves(trigger_tokens, est_wave_burn) -> int`** — CA-L4 verbatim: "rotate every
   `N = max(1, floor(trigger_tokens ÷ est_wave_burn))` wave boundaries; `est_wave_burn` default **40k
   tokens** `[TUNABLE]`". Zero/negative inputs ⇒ RAISES.
5. **`backstop_recommendation(target_tokens, worst_boundary_burn, handoff_write_cost, effective_window,
   model_max) -> dict`** — CA-L16 verbatim: "`gap = max(worst observed boundary burn + handoff write
   cost, 0.10 × effective window)` … `recommended autoCompactWindow = clamp(target_tokens + gap, 100k
   key floor, model max)`. `target+gap ≥ model max` ⇒ recommend NOTHING (default suffices). `target+gap
   < 100k` ⇒ recommend the 100k floor + note that rotation covers the remainder." Returns
   `{recommend: int|None, note: str|None, approximate: bool}`; the CA-L2 estimate degrade (no
   `total_tokens` ⇒ advertised-window estimate) sets `approximate: True` — "an explicit approximation
   flag in the recommendation text. Never silent." Nulls for telemetry terms fall to the fallback
   constant (CA-L40 consumers replace them later).
6. **`dispatch_budget(startup_fraction) -> dict`** — CA-L9 arithmetic verbatim: "Rotation point =
   **startup load + 40pp work quantum** `[TUNABLE]` … **hard cap 0.80** `[TUNABLE]` of the worker
   window (cap WINS: startup > 0.40 makes the quantum unsatisfiable ⇒ the dispatch is OVER-BRIEFED …
   a **mandate**, not a WARN); over-briefing **WARN at startup > 0.30**". Returns `{budget_fraction,
   cap_fraction: 0.80, warn: bool, over_briefed: bool}`; startup ≤ 0 or ≥ 1 ⇒ RAISES. This is the
   mechanical leg of CA-A11(a).
7. **`validate_context_autonomy(value) -> str`** — the load-guard mechanical leg (mirrors
   `kata_telemetry.validate_inline_eval`, kata_telemetry.py): `None` ⇒ `"off"` (§2: "Absent-at-load ⇒
   OFF on the key-consulted path (BC)"); exactly `"on"|"off"` ⇒ itself; anything else ⇒ RAISES
   ("Malformed ⇒ load-guard STOP + escalate (D45/GB12)"). Note in the docstring: one-shot shapes never
   call this (CA-L32/L33 — "the key is not consulted"; rotation unconditional is prose policy, P1/P2).

**Tests:** every RAISES clause named-tested; staleness boundary (299 s fresh / 301 s stale); priority
order (kata beats user; stale kata falls to fresh user; both stale ⇒ none); %-only trigger; N-wave
floor `max(1, …)`; backstop three legs (recommend / nothing / floor+note); budget WARN at 0.31, mandate
at 0.41, cap-wins identity; `validate_context_autonomy(None) == "off"` (CA-A8 row-2/3 mechanical pin).
**Mutation proofs ≥5** (staleness comparator, priority order, `max(1,…)` floor, clamp bounds, 0.30/0.40
thresholds): disable → named test RED → revert; listed for the D-record.

## E2 — `.kata-settings.json` new keys + marker mechanics + the fail-closed delete helper

read_first: DESIGN CA-L35..L37 + §2 settings table; kata_settings.py:96-112 (`add_confirmed_platform` —
the pattern C-4 FORBIDS copying), :120-144 (`_load_existing` — the pattern to copy), :147-185
(`write_settings` merge); kata_version.py:22-31 (stamp schema — `gitSha` + `suiteSemver`, NO `version`
field).

1. **Four additive keys** (§2 table verbatim): `firstRunCompletedAt` (ISO-8601 UTC), `firstRunVersion`
   (the stamp **`gitSha`** — CA-L36/R-43: "`suiteSemver` is EXPLICITLY REJECTED … the comparator reads
   **`gitSha`**"), `hostPosture {autoCompactChecked, recommendedWindowTokens, bridgeMode:
   "chained"|"user-only"|"none"}`, `acceptedDefaults` with the C-1 pinned value schema:
   `{ "<bundleItemId>": { "value": <json>, "v": "<harness semver>", "at": "<ISO-8601 UTC>" } }`.
2. **Writers** — `record_first_run(git_sha, home=None)`, `record_host_posture(posture, home=None)`,
   `record_accepted_defaults(entries, home=None)` — each copies the **fail-closed `_load_existing`
   pattern (kata_settings.py:120-144), NEVER the lenient `add_confirmed_platform` read-before-write
   (kata_settings.py:105-111)** (C-4, quoted from CA-L37). hostPosture/acceptedDefaults are
   "AUDIT-ONLY, last-write-wins, never consulted for suppression" (CA-L37) — docstring-pinned.
3. **NEW fail-closed delete helper** — `delete_settings_key(key, home=None) -> bool` (the CA-L36 named
   build item: "`write_settings` cannot delete a key (`{**existing, **owned}` preserves all keys,
   kata_settings.py:165/177) ⇒ the clear requires a small **NEW fail-closed delete helper**").
   Strict-loads via `_load_existing` (corrupt ⇒ ValueError, file untouched); absent key ⇒ False, no
   write; present ⇒ removed + rewritten, True.
4. **`first_run_required(home=None) -> dict`** — the CA-L36 comparator, verbatim: force "when the
   marker is **absent OR `firstRunVersion ≠` the `.kata-version` stamp's `gitSha`**"; "Stamp absent OR
   `gitSha == "unknown"` (the plain-install path, kata_install.py:1171) ⇒ the version clause is
   SKIPPED — marker absence alone forces." Returns `{required: bool, reason: "marker-absent"|
   "sha-mismatch"|None, clause_skipped: bool}`. Reads the stamp via `kata_version.read_stamp` (no
   duplicate parsing). **C-3 surface:** the marker READ is lenient (corrupt file reads absent ⇒ force)
   — but `record_first_run` on the same corrupt file fail-closes; the caller-facing contract
   (docstring + test) is CA-L37 verbatim: "bootstrap MUST detect the write failure, surface LOUDLY
   pointing at the corrupt file path, and stop; **never loop**."

**Tests (CA-A6 + CA-A11(e) mechanical legs):** delete on corrupt file RAISES, file byte-unchanged;
delete absent-key no-write; marker re-arm matrix — marker present + sha changed ⇒ required
(`sha-mismatch`); marker present + sha equal ⇒ not required; stamp absent ⇒ `clause_skipped` + marker
governs; `gitSha == "unknown"` ⇒ `clause_skipped`; corrupt settings ⇒ read-absent + write-raise pair
(the C-3 single-pass assertion); every existing kata_settings test untouched and green (additive BC,
§4 row 10). **Mutation proofs ≥3:** the `≠ gitSha` comparator (mutate to `suiteSemver` → RED), the
unknown-sha skip clause, the delete fail-closed guard.

## E3 — `kata_models` premium branch + the §3 gated amendment appended to the model-tiering DESIGN

read_first: DESIGN §1 Leg G (CA-L27..L31) + §3 (the amendment text — copy verbatim, it is frozen);
kata_models.py:300-407 (`resolve()` — the zero-step contract this amends), :29 (`_ANTHROPIC_LADDER =
["haiku","sonnet","opus","fable","mythos"]`); .planning/specs/model-tiering/DESIGN.md:25 (the
POST-FREEZE ADDENDUM precedent — append, never edit a frozen line).

1. **`resolve()` premium branch** — additive optional kwarg `premium: dict | None = None` (the
   `models.premium` block passed by the caller; `None` ⇒ byte-for-byte frozen behavior — §3 gating
   clause: "absent `models.premium`, the frozen spec governs byte-for-byte"). Fires iff **all four
   conjuncts** (CA-L29/§3.2 verbatim): "`models.premium.approved == true` ∧ `work-class ∈
   models.premium.scope` (critical | coding only — economy never, R-9) ∧ **the `offer` rung sits
   EXACTLY ONE rung strictly above the anchor in the family ladder** ∧ `mode == "advanced"`". The
   premium id is "**`models.premium.offer` itself** — never derived by ladder walk"; return the
   EXPLICIT id via ID_MAP (§3.2: "inherit would silently give the session model; explicit is
   mandatory"). "ANY other offer↔anchor relation ⇒ **NO FIRE + surfaced**" — mechanically: return the
   frozen-path result + a distinguishable surface signal (additive second channel, e.g. a
   `resolve_premium(...)` wrapper returning `{id, no_fire_reason}` so the frozen `resolve()` signature
   and every existing call stay byte-compatible; the board-NOTE prose is P2/C3). Malformed premium
   block (missing keys, wrong types) ⇒ RAISES (fail-closed, D136 — a present-but-broken approval is
   never silently ignored).
2. **The §3 amendment doc** — append the DESIGN §3 text (all six numbered clauses, verbatim, including
   both quoted frozen-spec excerpts) as a dated POST-FREEZE GATED AMENDMENT section at the END of
   `.planning/specs/model-tiering/DESIGN.md` (the line-25 precedent; supersede-never-rewrite — zero
   edits above the append point; D148 is recorded by P2/C10).
3. **Lapse/failure semantics boundary (stated, not built here):** run-lapse on dispatch failure
   (CA-L30) and the mode-change lapse executor (CA-L31, bootstrap) are PROSE consumers (P2/C1, C3);
   E3 ships only the conjunct evaluation + explicit-id return. The R2 401/403 premium carve-out is
   dispatch-time prose (P2/C3) — no code path in this module performs HTTP.

**Tests (CA-A7 verbatim):** "unit tests over all four conjuncts (each false ⇒ no premium id); premium
id EXPLICIT == `models.premium.offer` when all true"; the fold-#1 edge cases: "anchor=fable + approved
fable offer ⇒ NO FIRE (must NOT elevate to mythos); anchor=sonnet + approved fable offer (2 rungs
above) ⇒ NO FIRE + surfaced"; offer below anchor ⇒ NO FIRE; mode ≠ advanced ⇒ NO FIRE (the
"silent standard-mode +2-rung cost blowout" closure); "Absent `models.premium` ⇒ the existing
model-tiering suite passes byte-unchanged" (run the whole existing test_kata_models suite UNMODIFIED —
the §4 row 4/5 BC canary). Zero-step protection: premium never returns the anchor's own id.
**Mutation proofs ≥4:** each conjunct independently (negate → named NO-FIRE test RED).

## E4 — preflight bundle engine additions (`kata_preflight.py`)

read_first: DESIGN §1 Leg F (CA-L24..L26), CA-L15/L17, CA-L25; kata_preflight.py:526-539
(`_write_preflight` / `.kata/preflight.json`), :574 (`run_preflight`); protocol/config.md:41
(`approval_mode` reserved field — "Extension is additive alongside" it, CA-L24).

1. **`check_allowlist_coverage(allowlist_patterns, context) -> list[dict]`** — CA-L26: "a FIXED
   checklist, not an analyzer". The five frozen pattern classes verbatim: "(1) git plumbing the loop
   uses (commit / branch / worktree / merge on the target repo); (2) the run's verify command
   (`target.baselineGate` / the test runner); (3) dependency installs from the approved
   `preflight.allowed_registries` set; (4) writes to the bridge temp path (`%TEMP%/kata-ctx-*.json`)
   and to `.kata/**` + `.planning/**` in the target; (5) invocation of the harness tools
   (`python`/`uv run` on `<harness_home>/tools/*`)." Each uncovered class ⇒ one WARN entry naming the
   class. "Nothing else is checked; the list is the whole check" — the class list is a module constant
   frozenset; the function iterates it and only it.
2. **`stranding_verdict(walk_away, auto_compact_enabled, gauge_present, respawn_path) -> str`** —
   CA-L25 verbatim: "A walk-away-configured run (auto-continue boundary or unattended flag) with a
   missing leg that would STRAND it (auto-compact disabled AND no gauge AND no respawn path ⇒ session
   death at hard limit with no recovery) = **BLOCK** at preflight. Attended runs: **WARN** + proceed."
   Returns `"block"|"warn"|"ok"`; any input absent/None ⇒ RAISES (fail-closed on absent input to
   decision code — the adversarial-review discipline; callers must state what they know).
   [VETO-FLAG note carried in the docstring: CA-L25 stands locked-pending-veto.]
3. **Bundle audit event** — `run_preflight`'s `.kata/preflight.json` payload gains additive keys
   `bundle: {autoCompactChecked, backstopRecommendation, allowlistWarnings, premiumGate,
   hostSettingsWriteSlot}` (CA-L24: the host-settings write "is an explicit bundle slot approved like
   an install — never an implied side effect"; CA-L28: "`.kata/preflight.json` carries the audit event
   only" — kata.config stays authoritative). Existing preflight behavior (dependency installs,
   `gate_status`) byte-unchanged — every existing test green.

**Tests (CA-A11(d) + CA-A3(c) mechanical leg):** exactly-five-classes pin (adding a sixth entry to the
frozenset breaks a length test — the anti-cathedral guard); each class missing ⇒ exactly the enumerated
WARN; stranding matrix (walk-away + all three legs absent ⇒ block; any leg present ⇒ warn-or-ok;
attended ⇒ never block); absent-input RAISES; audit-event additive round-trip; existing suite green.
**Mutation proofs ≥3:** the AND-conjunction in stranding (flip to OR → RED), walk-away discriminator,
the five-class enumeration.

## E6 — telemetry ledger row v3 (`parentTokens`)

read_first: DESIGN CA-L40; kata_telemetry.py:888-920 (`build_ledger_row`, `"v": 2`), :490-540
(`read_ledger` version guard: known `{1, 2}`, unknown RAISES); the D142 precedent (M4-P0 §P0.1).

1. `build_ledger_row` emits `v: 3` + additive `parentTokens: {"<phase>": int|null}` — CA-L40 verbatim:
   "row schema **v2 → v3, additive, no backfill**, mirroring the D142 precedent exactly
   (absent-`v`⇒v1 unchanged; present-but-unknown version still RAISES)". "Nulls are honest absence,
   never zero."
2. `read_ledger` known-versions set becomes `{1, 2, 3}`; v1/v2 rows read unchanged; a documented
   accessor `parent_tokens_of(row)` maps v1/v2/absent → `{}`-with-nulls semantics (the
   `failure_kinds_of` pattern).
3. Named consumers documented in the docstring (CA-L40): "the CA-L16 gap formula's
   worst-observed-boundary-burn term; CA-L4's `est_wave_burn` replacement; OP-3's telemetry-derived
   gap" — consumption itself is future calibration (§8), not built here.

**Tests:** v3 round-trip; v1 + v2 fixture rows (the committed shapes verbatim) still parse; unknown-v4
RAISES; null-vs-zero honesty pin (a phase with no reading serializes `null`, never `0`); existing suite
green (§4 row 12). **Mutation proof ≥1:** the version-set guard.

## E5 — installer: shared-base-dir fix + factory-reset marker clear

read_first: DESIGN Leg K (CA-L42/L43) + CA-L36 clear clause; kata_install.py:58-67 (`iter_skill_dirs` —
return contract UNCHANGED), :112 (`_link_or_copy`), :274 (`_flat_link_skills` — the D104 pattern to
mirror), :361/:385/:427 (frozen fns), :1359-1439 (factory-reset branch); D128
(.planning/DECISIONS.md:1775-1776 — the frozen-five record); tier-family base dirs on disk:
`skills/plan/kata-plan/`, `skills/plan/kata-grill/` (RUBRIC.md + resources/), `skills/evaluate/
kata-review/`, `skills/execute/kata-diagnose/`.

1. **NEW enumeration helper** (CA-L42 fix shape, verbatim): "**ADDITIVE** — a new helper enumerating
   shared tier-family base dirs (a dir under `skills/` that contains no `SKILL.md` but is referenced by
   sibling tier skills' relative paths, or equivalently: the parent dirs of tier-family skills that
   carry non-SKILL payload) + an additive call in the Claude install path, following the D104
   install-portability pattern (SR-13: mirrors `_flat_link_skills`; Claude-only adapter surface)."
   `iter_skill_dirs` "keeps its exact current return contract — the new enumeration is a separate
   function." Never-git + stdlib-only hold (§7).
2. **The FROZEN FIVE stay byte-unchanged** (CA-L43): `install` (:361), `copy_project` (:385),
   `confirm_platform` (:427), `_flat_link_skills` (:274), `_link_or_copy` (:112) — verified by hash in
   the test (the STATE.md MD5 discipline). The `--update` and uninstall paths handle the new base-dir
   entries symmetrically (install/update add them; "uninstall removes only kata-managed entries",
   CA-A9).
3. **Factory-reset marker clear** (CA-L36): the factory-reset branch (:1359-1439) additionally calls
   E2's `delete_settings_key("firstRunCompletedAt")` (+ `firstRunVersion`) — "Factory-reset
   additionally CLEARS `firstRunCompletedAt` (it wipes install state; one forced pass after reset is
   correct)". Corrupt settings during the clear ⇒ the helper's ValueError surfaces via the existing
   factory-reset error path (loud, non-silent), reset otherwise proceeds — stated in the branch.

**Tests (CA-A9 verbatim):** "fresh install into a tmp host dir (symlink AND copy modes) ⇒ tier-family
base payloads (`kata-grill/RUBRIC.md` etc.) resolve from every installed tier skill; the frozen five
verified byte-identical (hash check, the STATE.md discipline); uninstall removes only kata-managed
entries." Plus: `iter_skill_dirs` output byte-identical pre/post (contract pin); factory-reset clears
both marker keys on a real tmp settings file; factory-reset on corrupt settings surfaces + does not
loop. **Mutation proofs ≥2:** the no-SKILL.md-but-payload discriminator; the kata-managed-only
uninstall guard.

## E7 — `protocol/config.md` schema rows (prose; after E1/E3/E4 semantics are landed)

read_first: DESIGN §2 kata.config table (copy the three rows verbatim), CA-L7/L8, §4 rows 1-5;
protocol/config.md:98-115 (Prime-frame sizing / D83 — the section that gains a POINTER, no rewrite).

1. Add the three rows to the schema table, content verbatim from DESIGN §2: `contextAutonomy`
   (`"on"|"off"`, incremental-only, one-shot never consults it, absent-at-load ⇒ OFF on the
   key-consulted path, malformed ⇒ load-guard STOP per D45/GB12 — validated mechanically by
   `kata_gauge.validate_context_autonomy`), `contextTrigger` (number 0–1, default 0.70 `[TUNABLE]`,
   advanced-drawer-only, never interactively asked; the key-NAME compilation-choice note carried),
   `models.premium` (`{offer, approved, scope, grantedMode}`, absent ⇒ resolver frozen behavior
   byte-for-byte, grantedMode lapse clause).
2. **CA-L8 (quoted):** "D83 is NOT edited … The prime-frame **0.40** fraction (protocol/config.md:
   98-115) remains the **sprint-sizing** fraction unchanged … config.md gains a pointer, no rewrite" —
   append one pointer sentence to the Prime-frame section naming this spec's trigger fraction as the
   B1 self-handoff threshold source; zero edits to the existing 0.40 text.
3. Document the §4 row-1 D147 departure at the `contextAutonomy` row ("The ONE departure in this
   initiative" — named, with the D147 pointer).

**Verify:** `git diff protocol/config.md` shows additive rows + one pointer sentence only; the D83
0.40 lines byte-unchanged (`git diff` hunk inspection); validator green.

## Phase verification (default-FAIL)

- `uv run --directory tools pytest` — full suite green, grown from 2505/3 skip; every new RAISES
  clause named-tested.
- `tools/validate_skills.py` 48/0/0 (no skill files owned in P0 — count unchanged).
- Snyk medium+ 0 on `tools/kata_gauge.py`, `kata_settings.py`, `kata_models.py`, `kata_preflight.py`,
  `kata_telemetry.py`, `kata_install.py` (CA-A10).
- Mutation-proof roster: ≥18 across E1–E6, each disable→RED→revert, listed for the D-record.
- BC canaries: existing test_kata_models / test_kata_settings / test_kata_preflight /
  test_kata_telemetry / test_kata_install suites pass UNMODIFIED (§4 rows 3-5, 10, 12, 13).
- Frozen-five hash check green (CA-L43).

## Threat register (STRIDE-lean; new attacker-reachable surface)

| Surface | Threat | Mitigation (task) |
|---|---|---|
| Bridge file in `%TEMP%` | Spoofing/Tampering — another local process writes a fake gauge to force/suppress rotation | E1: fail-closed parse; staleness bound; gauge only ever *schedules a handoff/rotation* (protective action, never destructive); worst case = deterministic-fallback behavior. No content is executed. |
| `.kata-settings.json` | Tampering/DoS — corrupt file loops the forced first run | E2: C-3 lenient-read/fail-closed-write + never-loop contract, test-pinned (CA-A6). |
| Installer base-dir enumeration | Tampering — path traversal / clobbering non-kata dirs | E5: `_safe_abs` guard (existing pattern); `_link_or_copy` never-clobber inherited; kata-managed-only uninstall test. |
| Premium block in kata.config | Elevation — hand-edited block escalates model spend | E3: four-conjunct AND + one-rung-exactly rule + NO-FIRE surfacing; malformed block RAISES. |

## Out of scope (P1/P2)

Bridge WRITER + chain wrapper + hooks (P1); all skill prose, bootstrap/preflight/orchestrate wiring,
report budgets, observability doc, platform docs, contract paragraph, glossary, riders, D-records,
CHANGELOG (P2); live proofs (P2/C11). Non-Claude code legs: none in v0.2.1 (§8).
