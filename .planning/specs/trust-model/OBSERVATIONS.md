---
spec: trust-model
artifact: "burn observations — the execution window's discovery + evidence channel (two-window fence: discoveries land HERE + kata-defer, never in the planning window's files)"
---

# OBSERVATIONS — the Trust Model burn (execution window)

## Green-at-fork baseline (recorded as INPUT per DESIGN §2.4/R2-M6 — prose-era record; the machinery that formalizes this is this burn's own W2/W3 work)

- Burn branch `burn/trust-model-01` forked from `grill/dispatch-seam` tip `0bebb6c`.
- Frozen PLAN committed `08ce3da`; F1f amendment `0e54351`.
- **Local gauntlet at the fork (conductor worktree, Windows): 4/4 PASS** — pytest-unit 4518
  passed / 3 skipped · pytest-integration 2/2 · ruff clean · validate-skills 49 skills, 0
  errors, 0 warnings. (Run 2026-08-16, `uv run python scripts/gauntlet.py`.)
- **CI is RED** (BL-X14, Guardian: Broken) — the X14 acceptance is CI green by burn close.

## Wave-1 dispatch record (Guardian: Honor-system — pre-seam prose dispatches, stated)

Seven builders dispatched 2026-08-16 off base `08ce3da`, Opus tier (D131, Fable anchor −1),
manual pinned worktrees under `C:\dev\projects\_kata_wt\trust-model\` (BBM-9, outside repo
root), disjoint ownership per the frozen PLAN wave-1 map:
`fix-mutation-prover` (E2 reproduce-first; task-branch CI push authorized) ·
`fix-statusline-crash` · `fix-learn-feed-truth` (**phase A triage ONLY** — E1 fork proposal
owed to the conductor before any fix) · `deferral-contract` · `exec-safety-registration` ·
`stale-anchor-fixes` (economy class) · `hook-capability-probe` (research class).

Enforcement this wave: **Dormant** (hook lands LAST, W8). Capture: Honor-system
(engine-by-conductor does not exist yet — prose collection). Resilience: Honor-system (no
cursor machinery yet — trail snapshots are the pre-existing board-only shape).

## Wave-1 integration record (2026-08-16)

- Seven task branches merged no-ff with `Kata-Task:` trailers into `burn/trust-model-01`
  (e484ce3 · 75e215a · 1657f50 · 10e169d · 36907d4 · 806aa79 · bd21107) + the exec-safety
  row-retirement follow-up merge + G2 README regeneration (`be2e006`) + DEF-3 (`3f29947`).
- **Local integration gauntlet 4/4** on the merged tree (pytest-unit, pytest-integration,
  ruff, validate-skills — all exit 0; validator 49/0/0 with README in sync).
- **CI GREEN — the 12-day red streak is OVER (the X14 acceptance):** run 31979757460
  (workflow_dispatch, SHA `3f29947` = the integrated tip), gauntlet (ubuntu-latest) SUCCESS +
  gauntlet (windows-latest) SUCCESS.
  https://github.com/taurran/kataharness/actions/runs/31979757460
  **Guardian: the CI gauntlet moves Broken → Verified with exactly this citation** (§6.6).
- Judge verdicts: 5× PASS first-round (X15, exec-safety, stale-anchors, hook-probe, X14);
  2× NEEDS_WORK cured and conductor-verified (deferral B1 → `e4c4e66`; X12 closure residue
  → phase B `cd8723b`). Spot-audit (conductor): deferral clause-pin + fingerprint mutation
  probe — both fired, restored byte-clean.

## Wave-1 FINAL EVAL — PASS (2026-08-16, fresh-context default-FAIL judge)

Verdict PASS at HEAD `df7d073`. The judge re-derived: all 9 trailered merges + 2 conductor
acts; every one of the 23 changed paths traced to frozen ownership / recorded amendment /
conductor record (zero drift); validator + 245 targeted tests green under its own execution;
all three declared `evidence:` nodes pass standalone; CI run 31979757460 success on both
jobs at `3f29947` (ancestor; the 4 later commits are docs-only); the paper trail's claims
re-derived (emit 29+2=31 exact; 177/177 decisions parse with D168/D172/D173 recovered; the
exec-safety truth restoration; DEF/ASM grammar conformance); escalation discipline held.
Residual table carried in the verdict (DEF-3 · D-9 pin-count falsehood-in-waiting · D-1/D-15
planning-window writebacks · D-13 recall blindness · D-11 W4/W5 wiring · D-3 argv
reconciliation · D-8 on-ramp gap · D-7 · the declared 0e9ada9 converged-line edit · a
cosmetic deviation-list ordering). **Wave 2 is unlocked.**

## Conductor rulings G3/G4 (recorded before any wave-2 dispatch)

- **G3 — protocol fingerprint re-approvals are conductor INTEGRATION acts.** W2 has two
  tasks whose contracts require a fingerprint two-step (`protocol/board.md` rewrite;
  `protocol/intent.md` schema amendment), and the pin table lives in `tools/validate_skills.py`
  — un-owned by either task (the F1 class again) and a within-wave collision if granted to
  both. Ruling: builders edit their contract file, run the updater (prints, never rewrites),
  and REPORT the printed digest; the conductor — at integration, one writer — independently
  re-derives each digest, reviews the contract diff against the gated DESIGN clause it
  implements, pastes the pin, and commits each re-approval distinctly. **The human-review
  intent of the two-step is preserved as an operator veto line**: every re-approval is
  enumerated at the wave report + handoff, revertible one commit each. (Session context: the
  operator launched this window autonomously; parking waves 2–9 on each paste would
  dead-stop the chartered burn. Precedent: the charter's own conductor-performed freeze with
  veto standing; D-8's conductor-verified initial pin.)
- **G4 — ledger-status-normalization is FENCE-CONSTRAINED.** The frozen task owns
  `.planning/specs/*/GRILL-LEDGER.md` (status: line only), but every spec dir except
  `trust-model` is the planning window's per the two-window fence — including
  `backlog-burn-mode` (actively being written by that window right now). Ruling: the task
  normalizes ONLY fence-safe ledgers (trust-model — already `converged`, conformant),
  grep-enumerates the full live set, and FILES the fence-blocked remainder (file → current
  status → required enum value, incl. `dispatch-seam` → `absorbed`) in OBSERVATIONS for the
  planning window to fold. The W3 `ledger_status` predicate is fail-closed on unrecognized
  statuses, and the only governor ledger this burn mints against is trust-model's — the
  partial normalization is safe and DECLARED, not silent.

- **D-16 · Ledger-status normalization: the corpus is worse than the plan assumed, and the
  fix is filed, not forced.** Full 29-ledger table + conductor rulings R1–R5 durably at
  `evidence/ledger-status-table.md`. Headlines: 15/29 ledgers have NO `status:` key at all
  (the frozen acceptance grep passes vacuously on them — acceptance amended, R1);
  dispatch-seam already parses `absorbed` (off the fence list, R2) but its routing target is
  prose-only (W3 input, R2); three ledger-as-contract specs ruled `converged` conservatively
  (R3); root cause is the DECISION-LEDGER.md format doc prescribing no frontmatter — fixed
  authoring-side in W4 per ownership amendment G5 (R4). **FOR THE PLANNING WINDOW:** the 18
  fence-blocked normalizations in the table (3 free-prose + 15 key-absent), with required
  values pre-derived. Task tm-w2-ledger-status-normalization itself: complete at G4 scope,
  zero edits (trust-model verified conformant), validator green.

- **D-17 · cursor-durability landed with one git-forced erratum + three routings.**
  (1) **ERRATUM (recorded here; the gated DESIGN stays as authored):** DESIGN §2.5 /
  PLAN's `refs/kata/trail/<runId>` is UNCONSTRUCTIBLE while the legacy `refs/kata/trail`
  exists (git directory/file ref conflict, error text preserved in the module docstring) —
  per-run refs live at **`refs/kata/trails/<runId>`** (`RUN_TRAIL_REF_PREFIX`), legacy ref
  untouched; both DESIGN intents preserved. (2) `cursor.pushTrail` needs NO kata_config
  schema entry (additive keys legal by that validator's own contract) but DOES need a
  `protocol/config.md` registry row — no task owns that file: **ownership amendment G6:
  the row rides W7 `close-machinery`** (owner of the offer's machinery; builder-suggested
  row text preserved in the task report). (3) `protocol/exec-safety.md:61`'s
  `snapshot_board` row is now understated (new inputs: per-run ref from a regex-guarded
  runId, payload basenames, caller-supplied cursor basename) — routed to the exec-safety
  builder at W2 integration. Honest label carried: cadence + record mechanism are
  test-exercised but have NO production caller until W3's seam — by plan, stated.

- **D-18 · intent-freeze-field landed; ONE plan gap escalated and amended.** Gate re-run
  62/62; keyword-only `freeze=True` writer + fail-closed `intent_status` reader (mirrors
  `plan_status` posture); additive intent.md amendment with both pinned clauses surviving;
  digest `3a45250790721964fc3140420cedf5e2054551e438a90190568760b573245722` queued for the
  G3 integration paste (old pin `aaf46320…`). **ESCALATION accepted + ownership amendment
  G7:** the Phase-6 freeze CALL SITE (`modules/initiation/kata-initiate/SKILL.md:575`,
  `write_intent(path, answers)` — no `freeze=True`) is owned by NO task in the frozen plan,
  leaving `intent: frozen` unreachable in production (W3's rung would refuse every
  initiation-entered run). G7: **W4 `coordinate-skills-migration` gains
  `modules/initiation/kata-initiate/SKILL.md`** (the one-line Phase-6 call-site update +
  its phase-emission duties, which that task's contract already implies for the conductor
  spine). Builder's declared truth-repair of the acceptanceCriteria row (a knowingly-false
  byte-identical claim corrected to output-equivalence) ACCEPTED — reviewed in the diff.
  Interim honesty: the repo suite runs 6-red on the fingerprint mismatch until the G3
  paste — that is the two-step working, not a regression (named here so nobody "fixes" it).

- **D-19 · cursor-grammar landed; amendment G8 adds the consumer-migration task the plan
  missed.** Gate re-run 69/69; both pinned board.md clauses SURVIVE verbatim (only the
  digest changed — the two-step working as designed); digest
  `245fbbbc94ed950506c3b31b44018278590743c0e3f1505f4db2b312278c1f26` queued for the G3
  paste (old pin `30df4ea7…`). Compile decisions recorded by the builder (utc-compact
  format, kata-dir-relative payload token, seq-space concurrency.json with the clock-trust
  `sec` field retired, END-before-START tie-break). **G8:** DESIGN §2.2 requires all
  fold/parser updates in the SAME wave, but the frozen plan allocated only the K3 snippet —
  four surviving 5-field parsers (`kata_dash_model.parse_board` · `kata_restore.fold_board`
  · `kata_telemetry.parse_progress_events` · `kata_crew._latest_board_heartbeat`) would
  SILENTLY mis-read 6-field lines (seq as agent, agent as TYPE), and `kata_dash_demo` needs
  the legal `start_run` mint (14 loud test failures, correct refusals). New task
  **tm-w2-cursor-consumers** dispatched, STACKED on the cursor-grammar branch (3558da3);
  its `kata_restore.py` grant is the `fold_board` REGION ONLY (parse_plan_tasks stays the
  parallel evidence-grammar task's — within-wave disjointness held at region level,
  declared). W3 inputs flagged by the builder: the PHASE msg enum is the seam's to enforce;
  SPAWN/DOWN child-span placement is seam machinery.

- **D-20 · evidence-grammar landed; ruling G9 (path-guard registry acknowledgment at
  integration).** Gate re-run 139/139. Reflexive TM-F1 proven against the REAL frozen plan
  (all 28 declarations parse; all three forms exercised); D-3 reconciliation implemented as
  literal-DESIGN-argv + a named opt-in `uv_wrapped_argv` boundary, pinned by tests; the
  guard-grammar "reuse" honestly implemented as the repo's established fourth local copy
  (claims the checks, not the code); probe registry carries `status:
  declared-before-active` for the W8 deny-tripwire target (a test asserts the target is
  still absent and instructs W8 to flip it) + explicit per-probe `cwd`. **G9:**
  `tools/tests/test_path_guard_family.py::test_guard_family_membership_is_complete` fired
  exactly as designed on the new `_guard_path` — the un-owned one-line registry
  acknowledgment (`("evidence_grammar", "_guard_path")`) is a conductor INTEGRATION act
  (G3 class), distinct commit, after verifying both family invariants (builder verified;
  conductor re-verifies at the paste). **Third first-use registry with no on-ramp**
  (fingerprints D-8, guard family D-20) — pattern candidate for the backlog via the
  planning window. Also flagged: `docs/DETERMINISM-DOCTRINE.md:56-58`'s law-8 example
  still describes the retired mutation_run shell=True exception — owed to the W7
  doctrine-amendment task's fold (recorded here so it is folded, not rediscovered).

- **D-21 · cursor-consumers (G8) landed; per-consumer refusal rulings recorded; two
  follow-ons routed.** Gate re-run 422/422. Refusal semantics chosen deliberately per
  consumer and tested: dash renders UNREADABLE never idle · restore records
  `board-unparseable` in `degraded_reasons`, destroys nothing · telemetry PROPAGATES (gate
  parser, never-skip posture) · crew stays fail-soft per its F3 contract with the refusal
  logged. Legacy fixtures survive only inside refusal tests; fixtures now built through the
  canonical emitter. **Routed:** (1) the stale statusline golden fixture (legacy 5-field
  board literal, correctly refused ⇒ two ▰→▱ glyphs) → its wave-1 owner
  (tm-w1-fix-statusline-crash) as a stacked follow-up, in flight; (2) `fold_board` still
  selects by wall-clock — a deliberate non-change (parser migration ≠ semantic re-basing);
  the seq re-basing is a W3-adjacent decision, recorded here for the seam wave's brief; (3)
  latent naive/aware datetime mix in fold_board's min/max (pre-existing) — noted with (2).

## Wave-2 integration record (2026-08-16)

- Six task branches merged no-ff (cursor-grammar b946170 · cursor-consumers 96ee106 ·
  statusline-fixture ba1f91a · cursor-durability 2c6f835 · evidence-grammar 09fced4 (one
  mechanical import-collision resolution, recorded in the merge body) · intent-freeze-field
  22bb03a) + the exec-safety snapshot-row widening merge (9b37dc4).
  **CORRECTED per wave-gate finding F1/F2 (D-22): six of these seven merge messages carried
  NO `Kata-Task:` trailer** — a conductor tooling quoting defect swallowed the message
  bodies, and the original sentence here ("merged no-ff with trailers") was written from
  intent, not re-derivation: a false claim in the burn's own record, caught by the wave
  gate. Cure (forward-only, no history rewrite — rewriting would invalidate the cd5e2d5 CI
  citation): six integration-attestation commits (eb0a07d · de52bdd · 65f3438 · 9beeb42 ·
  865189e · e1c1ba5), each carrying its task's trailer, trailer presence mechanically
  verified post-commit. Only 09fced4 (the here-string-committed conflict resolution)
  carried its trailer natively.
- **Conductor integration acts, each a distinct vetoable commit:** G3 board.md pin
  `9faea138…` (8d61974) · G3 intent.md pin `3a45250…` (d04dce0) — both digests
  independently re-derived on the integrated tree, exact match · G9 guard-registry
  acknowledgment (d575c15, invariants conductor-re-verified) · ruff `--fix` on four I001
  import-sort findings in cursor-consumers test files (cd5e2d5, G2-class tool-generated
  fix; the wave gauntlet caught what task gates did not lint — task briefs gain a
  ruff-check line from W3 on).
- **Integration gauntlet 4/4** (pytest-unit, pytest-integration, ruff, validate-skills — 0
  errors after the pin pastes). **CI GREEN both platforms** at the tip: run 31984365831,
  SHA `cd5e2d5`. Judge verdicts: 3× PASS first-round (durability, evidence-grammar,
  consumers), 2× NEEDS_WORK cured + conductor-verified (cursor-grammar self-cycle →
  d6bb759; intent evidence-node rename + two mutation-proven pins → decfc1c).
  Spot-audit: mutated-PLAN probes both REFUSED by the new reflexive evidence check, real
  plan passes (control). Ledger-status task closed at G4 scope (table filed, D-16).
- Carried to W3's brief: fold_board seq re-basing decision + the naive/aware TypeError
  escape path + the stale "canonical K3" prose at kata_restore.py:150 (judge findings) ·
  kata_restore's `_TRAIL_REF` cannot read run-scoped snapshots · the prose-only
  `absorbed`-routing target (R2) · PHASE msg enum enforcement · SPAWN/DOWN child-span
  machinery.

- **D-22 · Conductor accuracy finding (BBM-6 class, symmetric with D-6):** the wave-2
  integration record claimed "merged with trailers" without re-deriving it; the wave-gate
  evaluator falsified the claim with one command. Root cause: `cmd /c` interpolation of
  PowerShell backtick-newlines silently produced subject-only merge messages; the sentence
  was then copied from wave 1's (true) record. **Ruling G10 (binding on all future waves):**
  (1) merge/commit messages are written ONLY via here-strings (the proven path), never via
  `cmd /c` string interpolation; (2) immediately after every merge, the conductor
  mechanically verifies trailer presence (`git log --format='%(trailers:...)'` or
  cat-file) — commit first, verify second, the same rule builders were already held to;
  (3) worker briefs from wave 3 on NO LONGER instruct workers to write `Kata-Task:`
  trailers (kata-tdd:162 marks it integration-only — waves 1–2 worker trailers were
  conductor-briefed, recorded here as a declared deviation, and are why DONE resolution
  still worked while the merge trailers were missing); integration commits alone carry it.
  **Attribution notes:** cd5e2d5 (ruff --fix) and 4616996 (row widening) carry task
  trailers but are conductor acts in service of those tasks — integration-time commits, so
  tier-2 semantics hold, with the nuance recorded here. **Two record patches flagged by
  the evaluator:** D-19's queued board.md digest `245fbbbc…` was legitimately superseded
  by `9faea138…` (the d6bb759 judge-cure re-edited board.md; the paste used the final
  value — delta now explained); D-20 addendum: `parse_plan_tasks(check_evidence=True)` is
  built-and-exercised-by-tests but has NO production caller until W7's gate wiring — the
  same honest label class as D-17's cadence note, now stated.

- **D-23 · 🔴 D-16 R2 was WRONG: the dispatch-seam ledger's frontmatter is NOT valid YAML.**
  `.planning/specs/dispatch-seam/GRILL-LEDGER.md:4`'s unquoted status value carries a second
  `": "` inside a plain scalar — `yaml.safe_load` refuses the whole frontmatter. R2's
  "already parses `absorbed`" was derived from FIRST-WORD INSPECTION, not a YAML parse; the
  new fail-closed `ledger_status` predicate correctly RAISES on the live file today, and a
  mint governed by it parks. Correction of record for the D-16 table + **FOR THE PLANNING
  WINDOW (fence)**: quote the value, or better add `absorbed-into:
  ../trust-model/GRILL-LEDGER.md` — the seam's routing rule prefers that explicit key over
  prose extraction. Until fixed, the routing rule is proven against the corpus SHAPE
  (quoted fixture with the identical prose), not the live bytes — stated by the builder,
  carried here.
- **D-24 · seam-engine landed (33 public functions, 187 tests); compile decisions +
  process findings.** (1) The durability record rides a seam-authored NOTE line with the
  record JSON as payload (no sixth cursor TYPE invented; NOTE is not a cadence trigger so
  no recursion) — `read_trail_records` makes `derive_resilience` a fold over recorded fact.
  (2) `EXECUTION(wave=<n>)` phase identity: per-wave open/close matching enforced. (3) The
  `ledger` rung is role-class-scoped fail-closed (an unlisted role-class row is unruled ⇒
  refused). (4) D-17's "no production caller" label for kata_trail's cadence CLOSES —
  `phase()`/`capture()` are that caller. (5) **Fourth first-use registry hit:**
  `kata_dispatch._safe_kata_dir` trips the guard-family tripwire — G9-class conductor act
  queued for integration (invariants builder-verified, conductor re-verifies at paste).
  (6) **G10.4 (tooling rule):** file appends go through Python with explicit UTF-8, never
  `Get-Content | Add-Content` (mojibake caught and reverted by the builder pre-commit).
  (7) **Conductor re-run caught an INTERMITTENT gate failure the builder's single-shot
  runs missed:** `test_record_claim_is_atomic_single_use` fails ~1-in-5 with TWO winners —
  the RS-H2 atomic-claim property itself in question on Windows; fix-loop dispatched with
  root-cause-before-fix orders (claim vs harness). Wave-3 gate blocked on it. Re-run
  practice upgraded: intermittency loops (≥10×) join the conductor re-run for
  concurrency-bearing tests.

- **D-25 · 🔴 DESIGN §1.5 ERRATUM (Windows) + the atomic-claim cure — the burn's deepest
  catch so far.** The "atomic claim by os.rename" premise is POSIX reasoning: on Windows,
  renaming a file to the path it already occupies is a DOCUMENTED NO-OP SUCCESS, so a
  rename-election silently degrades to everyone-wins (raw-OS probe, no kata code: 8/8
  claimants "won" every one of 200 rounds; the pre-fix `claim_record` produced multiple
  winners in 32/200). Sequential runs look perfect — which is why single-shot verification
  passed while the replay control was broken. **Cure (84ab704):** election by
  `O_CREAT|O_EXCL` exclusive create (probe: {1: 300/300}); retention move stays the §1.5
  rename (mark-consumed-and-retain preserved); loser denied with the re-mint path named;
  pinned by a deterministic forced-interleaving test + the declared node now runs the race
  25× in-process. **Same-class audit found a second defect, fixed (8c75e87):** two
  concurrent mints computing the same seq would silently clobber a record file — the path
  is now exclusively reserved; collision ⇒ refuse-to-mint ⇒ park. **Third instance routed:**
  `kata_board.start_run`'s archive-name TOCTOU (reported-not-touched, W2 owner; follow-up
  dispatched). **Standing practice (G11):** a concurrency-property test must run its race
  N times in-process AND pin the property by forced interleaving where injectable; the
  conductor re-run loops concurrency-bearing tests ≥10× (this discipline is what caught
  the 1-in-5 flake the builder's green single-shots missed). The gated DESIGN stays as
  authored; this erratum is the record.

- **D-26 · The wave-3 pattern, named (builder's lesson, adopted):** three seam defects
  shared one shape — **a property promised in a docstring but not enforced at the
  boundary** (rename-as-election · seam-seq uniqueness · park-path-on-refusal; the W2
  rotation TOCTOU is the same family). The cure each time: make the guarantee structural.
  This IS Truth Serum's thesis applied to our own code mid-burn — feeds the W6 detector
  rationale and the burn's lessons at close. Judge cures verified: seam-engine 05553dc
  (live-corpus mint now parks with a typed refusal + DENY; 194/194 + 10× declared-node
  loop clean under conductor re-run; the worker-NOTE resilience-lift hole closed with the
  seam-agent filter, systemic writer-class residual restated not silently closed);
  rotation fix 52dd729 merged (trailer verified). Wave-3 judges: evidence-identity PASS
  first round (4 non-blocking hardening notes recorded in its verdict); seam-engine
  NEEDS_WORK → cured. Non-blocking judge notes carried to W5: the convergence-reviewer
  role token needs its ladder row assigned at judge-contract-rewrites (named seam comment
  in code); evidence-identity's `\x7f`/DEL component char + the aspirational consumer
  list wording.

## Discoveries (append-only)

- **D-1 · The BL-X12 writeback gap (FOR THE PLANNING WINDOW to fold — fence-respecting
  handoff):** BL-X12 was fixed and conductor-gated CLOSED at `2a1b1cf` (2026-08-16 12:40,
  `specs/backlog-burn-02/OBSERVATIONS.md:84`), but `.planning/BACKLOG.md:562` still carries
  the 🔴 open marker — the closure was never written back. Consequence: the trust-model
  ASSESSMENT (T17 BROKEN), BURN-CHARTER item 4, both window orientations, and the frozen
  PLAN's `fix-learn-feed-truth` task were all authored off a ledger that lied about its
  state, and a wave-1 builder was dispatched against work already done (caught by the
  builder's H7 pushback, verified by conductor re-run: 105/105). **Planning window: mark
  BL-X12 closed at `2a1b1cf` in BACKLOG.md.** Stale references elsewhere (both orientations,
  BURN-CHARTER:22, ASSESSMENT:47/134, DESIGN.md:102's parenthetical, dispatch-seam
  ledger:112) are recorded here rather than edited — the gated/ruled artifacts stay as
  authored; this note is the correction of record. **Trust-model finding in its own right:**
  a closed defect whose ledger entry stays red re-schedules done work through an entire
  grill→design→plan→freeze pipeline; §6.6 truth-status marks + EV-1 cover the label side,
  but the WRITEBACK ACT at defect-closure has no owner — candidate binding input for BL-N11
  (backlog management).
- **D-2 · Retroactive trust-model grill emit RUN (2026-08-16):** written=29,
  parsed_open_skipped=2 (correct — the two genuinely open entries), redactions=0, to the
  Kiban vault feed (`.../wiki/pages/synthesis/decision-patterns/`, project slug
  `kataharness`, kind version-up). Ledger `converged:` line corrected (commit `0e9ada9`).
- **D-3 · `evidence:` `test:` argv-form reconciliation owed at W2:** DESIGN §3.5 pins
  compile-to `[python, -m, pytest, <id>]`, but every live sink uses `uv run pytest`
  (`mutation_check.run_named_test`, `scripts/gauntlet.py`); a bare `python -m pytest` misses
  the uv-managed venv. Conductor intent for the W2 `evidence-grammar` brief: grammar compiles
  per DESIGN; the EXECUTION environment may wrap the compiled argv in the uv runner as an
  environment detail, recorded in the module contract — divergence resolved visibly at build,
  not silently. (Exec-safety builder's finding 2.)
- **D-4 · Mutation-sink activation is now contractually BLOCKED on the argv conversion**
  (exec-safety builder's finding 1): the per-task verify command must never reach the
  still-`shell=True` mutation sink; `fix-mutation-prover` (in flight, W1) performs the
  conversion. W2/W6/W7 owners inherit the ordering constraint via the exec-safety watch-list.
- **D-5 · Citation-provenance data point (stale-anchor task):** `kata-validate/SKILL.md:276`'s
  `:13,151` anchor was BORN wrong (line 13 never contained the quoted sentence in any of the
  file's 9 revisions) — not drift but authoring-time fabrication; and line 369's reuse-table
  row had a symbol/range mismatch (anchor widened, label flagged for the W4/W5 rewrite).
  Feeds the B5/S2 detector rationale.
- **D-6 · Validator-evidence discrepancy (accuracy record, BBM-6 class):** the
  `stale-anchor-fixes` builder reported validate_skills green; the conductor re-run returned
  5 errors (STANDARDS §3 version bumps owed on all five changed skills). Fix-loop dispatched;
  builder's explanation pending — recorded whichever way it resolves.
- **D-6a · D-6 resolved:** the builder's accounting — its single validator run happened
  after editing but BEFORE committing, and the version-bump check reads committed blobs
  (`footprint.py:206` documents the ordering), so the green was real-but-invalid evidence
  for the claimed state; the stale claim is also baked into cc589e8's commit message
  (corrected on the record in a7e142b's). Ruled an accuracy finding, not fabrication.
  Corrected practice for all future briefs: **commit first, validate second, paste the raw
  exit code (no pipes — `$?` captures the pipe tail's status)**.
- **D-6b · Amendment G2:** README.md's generated skill index is owned by NO task; every
  SKILL.md version bump desyncs it. Ruled: regeneration is a per-wave integration-time
  conductor act (`validate_skills.py --write`, once, on the integration branch, before the
  wave-gate validator). Task gates for skill-touching tasks are green-except-README.
  Without this, W4's three concurrent skill tasks would have raced on the same generated
  block.
- **D-8 · deferral-contract landed with conductor-verified initial fingerprint pin:**
  the builder self-pasted the initial `deferral.md` pin (the updater cannot print a pin for
  a NEWLY registered file — it iterates the existing pin table, `validate_skills.py:1159`;
  no on-ramp exists). Conductor independently re-derived the digest via
  `--update-protocol-fingerprint`: exact match (`8f2cb080…`). Precedent `9af7c5e`.
  **Surfaced to the operator at the wave report** (an initial pin is a weaker act than a
  re-approval; the on-ramp gap is a small fix candidate for a later wave — recorded, not
  silently absorbed).
- **D-9 · Stale pin-count prose owed a human two-step:** `protocol/prime-directives.md:95-96`
  says 23 clause-pinned / 21 fingerprinted; with deferral.md the real numbers are 24 / 22
  (also echoed in `tools/tests/test_validate_prime_directives.py`). Correcting
  prime-directives.md requires its own fingerprint re-approval — **operator human moment,
  queued for the wave report**; leaving the numbers stale is recorded here so it is a known
  falsehood-in-waiting, not a silent one.
- **D-10 · `.planning/ASSUMPTIONS.md` never existed** despite four surfaces naming it
  canonical — created by deferral-contract with that provenance stated in-file; seeded with
  ASM-1 (the fingerprint-pin reasoning, ungrilled).
- **D-11 · kata-defer/kata-evaluate SKILL wiring to protocol/deferral.md deliberately NOT
  done in W1** (outside ownership) — owed to W4 `authoring-skills-migration` (kata-defer
  alignment is already in its task text) and W5 (kata-evaluate). Flagged so it is never
  assumed done.
- **D-12 · Hook probe (evidence/hook-probe.md, commit 95dae4c) — three findings wave 8 MUST
  absorb, all OBSERVED not assumed:** (1) **fail-open is the governing limit** — a PreToolUse
  hook that times out or crashes lets the call through; only a clean exit-2/deny-JSON blocks.
  The W8 hook must deny on internal error, and post-hoc verification is MANDATORY, not
  belt-and-braces (a broken hook is indistinguishable from an absent one in-session; the
  degrade table's no-result⇒Dormant clause is load-bearing in practice). (2) **Matcher
  naming trap:** the hook payload always carries tool_name "Agent" while result envelopes
  report "Task" — a hook asserting "Task" silently no-ops on every call. (3) **Capture needs
  BOTH edges:** PostToolUse sees the full return envelope on the sync path ONLY (background
  dispatch gets a handle ~4ms after launch); SubagentStop carries the verdict text on both
  paths but lacks the tool_use_id binding — R-H3 as written captures nothing on background
  dispatches without the second edge. Deny survives permission-skip flags (good for BBM-11);
  Bash leg sees the full pre-expansion command literal (Partially-verified residual confirmed
  as observed fact). Interactive sessions, Kiro/Codex, nested Agent-denies-Agent: UNPROBED,
  stated in the note.
- **D-15 · FOR THE PLANNING WINDOW (with D-1): BL-X14's BACKLOG diagnosis text (~line 486)
  records the FALSIFIED hypothesis** (sandbox import-path resolution). The observed mechanism
  is the cmd.exe `cd /d` prefix dying under `/bin/sh` with `shell=True` — both runs failed
  identically, mimicking vacuity (evidence: `evidence/x14-ci-green.md` + CI runs 31978174967
  red / 31979757460 green). When closing BL-X14 in the backlog, replace the diagnosis with
  the observed mechanism; also note stale `shell=True` prose at `.planning/DECISIONS.md:1211,
  1214` + `.planning/BACKLOG.md:840` (the latter is now done work).
- **D-13 · `tools/recall.py:607` carries the identical wrapped-bold-anchor blindness**
  (its own single-line `_BULLET_RE` copy): recall over DECISIONS.md still cannot see
  D168/D172/D173 and still returns D167/D171 with the swallowed text — the READ side of the
  loop phase B's fix only half-closes. Out of every wave-1 ownership; **for the planning
  window: file as a new backlog item** (pairs with the BL-X12 closure writeback, D-1).
- **D-14 · The wave-1 judge layer earned its cost (accuracy record):** of seven items, the
  fresh-context judges caught two real defects that builder self-gates AND conductor
  re-runs both missed — the deferral contract's self-staled citation inside its own
  fingerprinted commit (cured `e4c4e66`, pin re-derived and matched), and the overbroad
  X12 closure hiding a half-fixed sub-defect with neighbor-body corruption (cured
  `cd8723b`). Also: X14's judge found one unreproducible count in the evidence note (46 vs
  91 `testWentRed` occurrences in run 1 — understates pre-fix badness, correction owed at
  the note's zero-failure amend) and confirmed the E2 falsification escalation reached the
  conductor (it did — recorded).
- **D-7 · Minor: `statusline_chain.py` docstring's §security block claims its exec-safety
  row "lands at P2/C10 closeout" — stale: the row EXISTS (`protocol/exec-safety.md:68`).
  Docstring correction can ride any future statusline touch. X15's Snyk scan: one
  pre-existing Medium (CWE-78 class) on the registered operator-domain sink, unchanged by
  the fix (verified by revert-and-rescan); no `.snyk` entry added (outside task ownership) —
  surfaced here for the wave gate.

## Wave-2 FINAL EVAL — PASS on re-verdict (2026-08-16)

First round NEEDS_WORK (F1 six untrailered merges / F2 false record sentence — the
CONDUCTOR accuracy finding, D-22); cure re-verified by the same fresh-context evaluator:
attestation commits empty + trailered (cat-file), integration-time attribution resolves
from merges+attestations alone, full gauntlet re-run 4/4 at the cured HEAD, CI citation
cd5e2d5 intact. Residual table carried in the verdict. **Wave 3 unlocked.** Operator
surface: D-22 (the burn record carried a false claim for one gate cycle) + the two G3
re-approvals (one revert each).

## Wave-3 integration record (2026-08-16 -- cure of the wave-gate F1/F2 records findings; every fact below mechanically derived, not written from intent)

- **Five merges, trailers re-derived raw** (`git log --merges 5993402..HEAD --format=...`):
  `6bd7e7d tm-w2-cursor-grammar · 4ee15af tm-w3-seam-engine · d5fd1ee
  tm-w3-evidence-identity · 58732cb tm-w3-seam-engine · f4e962f tm-w2-cursor-grammar`.
  (G10.2 verification recorded for ALL five, curing the one-of-five gap.)
- **D-27 · The CI red strand D-26 predates (instances 2 and 3 of the D-25/D-26
  platform-divergence class):** run 31989512531 went RED on the ubuntu leg only, forcing
  two further fixes AFTER D-26 was written -- `2bb51ec` (the rename pin made
  platform-honest, PLUS its ordered sweep finding a REAL production defect: `claim_record`'s
  retention move would silently clobber a retained record on POSIX, returning a false win on
  Linux only -- now refused uniformly pre-rename, safe because the election serializes the
  window) and `451bf4b` (cursor publication made complete-or-absent + exclusive via
  temp+os.link, closing a POSIX strand where a zero-byte cursor was observable and two
  racers could both skip rotation -- falsified LOCALLY pre-fix 5/12 rounds, 0 post-fix).
  D-26's "cures verified" scope is hereby corrected: it was written before this strand.
- **Green CI citation (the wave's proof):** run 31990449823 @ `6bd7e7d` (== the wave tip,
  zero post-CI commits) -- SUCCESS on both jobs: gauntlet (windows-latest) 95272902603 ·
  gauntlet (ubuntu-latest) 95272902671.
- **NEW carried residual (lifted from the 451bf4b docstring per PD-2
  labels-travel-with-the-claim):** `_publish_cursor`'s fallback for filesystems without
  usable hardlinks reverts to exclusive-create-then-write, whose zero-byte window is a
  stated residual -- now operator-visible here, and a W4-brief input.
- **Post-W2-gate note for the next gate:** `52dd729` + `451bf4b` are post-W2-gate changes
  to W2-gated `kata_board` contracts, attributed `tm-w2-cursor-grammar` -- judge-ordered
  (rotation TOCTOU) and CI-forced (POSIX strand); NOT drift.
- **F2 cure -- D-25 operator-surface line:** the D-25 erratum REPLACES a mechanism named in
  the frozen gated DESIGN (S1.5 "atomic claim by os.rename" -> O_CREAT|O_EXCL election;
  retention rename unchanged). **Surfaced to the operator at the wave report + handoff as a
  vetoable-by-objection erratum** (the D-8/D-9 precedent), with the raw-OS measurements as
  its evidence.
- **N1 label (the D-22 precedent):** BOTH W3 surfaces have ZERO production callers today --
  the seam engine until W4 wires the ~52 launch sites (the dogfood rule), the evidence
  identity gate until W5/W7 wire consumers. Legitimate per the frozen PLAN, stated here so
  the record carries what the docstrings claim.
- D-23..D-26 physically sit under the Wave-2 heading (append-only discipline); this section
  is wave 3's record of them plus the strand above.

## Wave-4 dispatch record (2026-08-17 — THE FIRST ENGINE-MINTED DISPATCHES; Execution rule 4's dogfood rule now binding)

Three builders dispatched off base `5ed67a4` (the pushed tip; one handoff commit past the
orientation's `6a06b4b`), Opus tier (D131, Fable anchor −1), pinned worktrees under
`C:\dev\projects\_kata_wt	rust-model\` (BBM-9), disjoint ownership per the frozen PLAN
wave-4 map + recorded amendments G5/G7 and the rulings below.

**Dogfood (first live production use of the seam):** conductor ran `kata_dispatch.run_start`
in the conductor worktree (kata dir `.kata/`) — runId `run-20260817T034343Z-e3b50e43`, mode
new, declaration honestly derived: enforcement `Dormant (pre-activation)` · capture
`Honor-system (engine-by-conductor)` · resilience `Partially verified (local)`. Three mints
`governs=plan` against the frozen PLAN (state=frozen verified by the governor), each carrying
its full builder brief (briefHash recorded): seq 1 `tm-w4-orchestrate-seam-migration`
(brief 84b86009cb034581…) · seq 2 `tm-w4-coordinate-skills-migration` (b58b00bfb226b444…) ·
seq 3 `tm-w4-authoring-skills-migration` (69d594948da6a00b…). All three records CLAIMED at
launch (atomic single-use election; tokens + retained records in `.kata/dispatch/consumed/`).
`open EXECUTION wave=4` PHASE on the cursor; cadence snapshot committed
`501e8078421ae2700304cf429826c4bce5539f91` @ `refs/kata/trails/run-20260817T034343Z-e3b50e43`.
Enforcement remains Honor-system-DECLARED (nothing denies a bypass until W8) — stated.
Every brief carries the advisor channel, H7 pushback, G10 tooling rules, D-6a
commit-first-validate-second, and its task's `evidence:` node names VERBATIM from the PLAN.

**Conductor rulings at dispatch (binding, G-series):**
- **G12 — board→cursor rename cross-reference scope.** ~90 files reference
  `protocol/board.md`/`kata-board` (grep at dispatch). Builders migrate references ONLY
  inside their grants. The coordinate builder grep-enumerates the full surface and returns a
  three-class table: (a) historical/gated records — NEVER edited (the D-1
  records-stay-as-authored precedent; includes the fenced BACKLOG/DECISIONS); (b)
  other-W4-task-owned files — that task's duty (kata-orchestrate's own brief carries its
  board→cursor prose); (c) live un-owned surfaces — listed for conductor integration acts or
  a dispatched follow-up sweep (the G8 precedent). Out-of-grant dangling refs at the task
  gate are integration-owed, declared not silent.
- **G13 — ownership reconciliation (freeze-gate-fold class):** `protocol/board.md` joins
  `coordinate-skills-migration`'s edit set — the PLAN body text declares the rename as this
  task's; the frontmatter map omitted it. Cross-wave sequential share with W2 cursor-grammar,
  legal per the RUBRIC rule.
- **G14 — rename names pinned at dispatch (within-wave coherence):** `protocol/board.md` →
  `protocol/cursor.md`; `skills/coordinate/kata-board/` → `skills/coordinate/kata-cursor/`;
  `REQUIRED_PROTOCOL` key `board.md` → `cursor.md`. The runtime file `.kata/board.md` and
  module `tools/kata_board.py` KEEP heritage names — no code rename is in any frozen task
  text; prose states the heritage honestly.
- **G15 — evidence-node rename mapping:** the frozen node
  `artifact:skills/coordinate/kata-board/SKILL.md` names the pre-rename path; the conductor
  evaluates it at the task gate against the git-tracked rename successor and records the
  mapping here. The frozen PLAN stays as authored (D-17 erratum-of-record precedent).

Enforcement this wave: Dormant (hook is W8). Capture: Honor-system, engine-by-conductor —
the conductor invokes the capture/record legs by hand around Agent-tool dispatches, declared
per RS-M5.
