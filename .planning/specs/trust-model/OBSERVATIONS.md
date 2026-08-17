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
`C:\dev\projects\_kata_wt\trust-model\` (BBM-9), disjoint ownership per the frozen PLAN
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

## Wave-4 integration record (2026-08-17 — every fact below mechanically re-derived)

- **Four task branches merged no-ff with `Kata-Task:` trailers, each verified post-merge
  (G10.2):** `6a5ada3 tm-w4-coordinate-skills-migration` (tip 58fc17a incl. the close_run cure) ·
  `8fe656a tm-w4-cursor-rename-sweep` (G17 stacked task, f8e31d4) · `c16caeb
  tm-w4-orchestrate-seam-migration` (98a6021) · `59ac923 tm-w4-authoring-skills-migration`
  (10cb4e4 incl. the G16 follow-up).
- **Judge verdicts (fresh-context, default-FAIL, one per item, all captured on the cursor
  via the seam):** authoring PASS first round (F1 MEDIUM → ruling G16 → cure 10cb4e4
  conductor-verified; F2 LOW W5-owed) · orchestrate PASS first round, zero blocking findings
  (6/6 anchors, capture(kind=) + arm-scan verified real, all-plan governor reading verified
  against check_governor) · sweep PASS first round · coordinate NEEDS_WORK (close_run phantom
  at three new sites — the reuse-claims class, caught by the judge; builder and conductor both
  missed it) → cure 58fc17a (NOT-YET-BUILT qualifiers; Path-A step 3 parked, sequence stops)
  → re-verdict PASS. Conductor ruling on the builder's step-4 question: stop-at-step-3 stays
  as authored; sanctioning loop-back over an open predecessor is W7's ruling.
- **Conductor integration acts, each a distinct vetoable commit:** G3 cursor.md pin paste
  `0ccfc698…` (592672f; digest independently derived 3×: builder report, cure re-verify,
  integrated tree — exact match each; supersedes intermediate `7cf63a2b…`, D-19 precedent) ·
  G18 path-swaps in six un-owned protocol contracts (4949b11: advice ×3 / escalation ×1 /
  narration ×3 / steering ×1 / state `[[kata-cursor]]` ×1 / orientation skill-name ×1; heritage
  `.kata/board.md` kept; observability.md left for W9; prime-directives:110 stays as authored)
  + six fingerprint re-approvals (5bad9a7 advice · dcbb6d1 escalation+narration PAIRED in one
  commit, declared same-file-staging deviation · 509f6d0 orientation · 37c96d7 state ·
  522192f steering) · G2 README regeneration (8786489).
- **Integration gauntlet 4/4** (pytest-unit 0 · pytest-integration 0 · ruff 0 ·
  validate-skills 0; validator 49 skills, 0 errors, 0 warnings) + **G11 loop:**
  test_record_claim_is_atomic_single_use ×10 sequential fresh processes, 10/10 pass.
- **Spot-audit (ONE, live on the burn's own run records):** re-claim of consumed record
  run-20260817T034343Z-e3b50e43-1 → RecordClaimRefused (single-use, re-mint path named);
  body-embedded `VERDICT: PASS` → CaptureRefused (line-1 only, body never scanned). Both
  refusals fired on the LIVE seam, not fixtures.
- **Dogfood closure of the N1 label (conductor side):** this wave is the seam's first
  production use — run_start / mint ×6 / claim ×6 / phase / capture ×4 / refusal-driven DENY
  all exercised live by the conductor loop. Skills-side wiring landed in kata-orchestrate
  (46 LS sites) + the conductor spine. Enforcement remains Honor-system (nothing denies a
  bypass until W8) — stated.
- **Rulings issued this wave:** G16 (plan-tier evidence bullet follow-up, executed) · G17
  (rename-completion sweep as stacked task, executed) · G18 (protocol path-swap integration
  act + per-file re-approvals, executed). Operator veto surface: the G3 paste + six G18
  re-approvals, one revert each; the three rulings themselves vetoable by objection.
- **Carried to W5's brief:** convergence-reviewer role-token ladder row (named seam comment,
  kata_dispatch.py:456-467) · kata-evaluate `ASSUMPTIONS.md` bare-path fix (judge F2) ·
  kata-evaluate:186 stale `protocol/board.md` ref + retired wall-clock/`sec` concurrency
  schema row (superseded by the D-19 seq-space fold) · worker-report `VERDICT:` first-line
  contract coherence (orchestrate made it mandatory for workers; W5 owns judge enums) ·
  optional host-only restatement at LS-20/21 (judge R4).
- **Carried to W7's brief:** R3 (LOOP-BACK close vs the terminal-write refusal — close_run
  must close it or run-closed refuses) · lift the three NOT-YET-BUILT close_run qualifiers
  (protocol/cursor.md ~:201, kata-loop ~:72 and ~:196-205 step 3) when tools/kata_close.py
  lands · rule loop-back-over-open-predecessor semantics · the stale law-8 mutation_run
  example fold (D-20, standing).
- **Carried to W9's brief:** protocol/observability.md — 6 `protocol/board.md` path refs +
  5 stale line-number anchors into the renamed file (:110,112,114,127,150) — W9 owns the file.
- **Lessons (harness-fold candidates, kata-improve):** (1) E7 reuse-claim sweeps must include
  BARE-BACKTICKED identifiers, not only `module.symbol`/`symbol()` forms — the close_run
  phantom passed builder and conductor sweeps shaped the narrow way; judge R5 + builder
  root-cause agree. (2) `git merge -F -` does not read stdin (unlike git commit) — merge
  messages go via `-F <file>`; and a `cmd /c` wrapper under Git Bash swallows commands
  entirely (two G10 tooling nuances observed live this wave).
- **DEF-4..DEF-11 filed** (.planning/DEFERRED.md) from builder deferral candidates — none
  silently dropped.

## G19 — OPERATOR-DIRECTED RE-SCOPE (2026-08-17): waves 5–9 consolidate to FOUR loops, run back-to-back autonomously

Operator directive (verbatim-intent, given live in-session): *"Consolidate to four loops, and
don't wait between each. Run them back to back in an end to end burn, and then give me the
full post-loop report once it's all done. I'm going to go to bed and would like to wake up to
a completed end to end run."*

**What changes:** ONLY the wave grouping of the frozen PLAN's `waves:` map for waves 5–9.
Every task contract, ownership grant, dependency edge, evidence declaration, gate, and
recorded rationale stays frozen as authored. The consolidation was derived from the frozen
`depends_on:` map and verified against it:

- **Loop A** = judge-contract-rewrites (anchor) ∥ blocking-detectors ∥ signal-detectors ∥
  close-machinery ∥ doctrine-amendment (anchor). All five have every dependency landed
  (W1–W3) and disjoint ownership.
- **Loop B** = judge-tripwire-corpora ∥ grounding-agent ∥ ev1-badge-registry, with
  **gate-preconditions STACKED on the corpora branch** (the G8/G17 stacked-task precedent —
  its `depends_on` includes judge-tripwire-corpora).
- **Loop C** = hook-activation ALONE — the TM-H1 activate-LAST law and its own gate with the
  live deny-tripwire stay intact, exactly as frozen.
- **Loop D** = guardian-relabel-pass — the PLAN deviation-3 rationale (relabel must cite
  post-activation results) stays intact, exactly as frozen.

**Preserved orderings (load-bearing, unchanged):** corpora after judge contracts ·
gate-preconditions after corpora · hook after ALL migrations + judge contracts +
gate-preconditions · relabel after hook. The full loop runs per consolidated wave (builders →
conductor re-runs → fresh-context default-FAIL judges per item → cures → ONE spot-audit →
integration with trailers/G2/G3-class acts → gauntlet → push+CI → default-FAIL final eval).

**Blast-radius trade, declared:** a failed Loop-A final eval re-loops five tasks instead of
one wave's worth. Accepted by the operator's directive; per-task judge gates before
integration keep the cure surface per-task.

**Autonomy rider:** the operator's directive makes the remaining human-approval moments
(doctrine fingerprint re-approval; any further G3-class pastes) conductor-performed acts with
the FULL VETO SURFACE enumerated in the post-loop report — the G3 precedent extended by
explicit operator direction, recorded here. Outward-facing posture unchanged: pushes go only
to the existing origin burn branch; `cursor.pushTrail` stays default never-push; the BACKLOG
truth-status leg of W9 stays fence-parked unless the planning-window fence is verifiably
lifted (GATE-PLAN ruling 2) — it will be FILED via OBSERVATIONS instead.

**G20 — ownership amendment riding G19:** `close-machinery` (Loop A) additionally gains the
three W4 NOT-YET-BUILT `close_run` qualifier sites (`protocol/cursor.md` ~:201,
`skills/coordinate/kata-loop/SKILL.md` ~:72 and the parked Path-A step 3 at ~:196-205) — to
flip them true when `tools/kata_close.py` lands in the same loop — plus the W7-carried
rulings it must make in its own contract: R3 (LOOP-BACK close before the terminal write) and
the loop-back-over-open-predecessor semantics. The `protocol/cursor.md` touch re-triggers the
fingerprint two-step (conductor re-derives + pastes at Loop-A integration, one more veto line).

## Wave-4 FINAL EVAL round 1 — NEEDS_WORK (2026-08-17) + the cure (D-22 class, forward-only)

The fresh-context final eval re-derived legs 1–5, 7, 8 fully green (topology exact, zero
drift across 53 paths, gauntlet green under its own execution incl. full pytest 4927/3 and
the G11 ×10 loop, all four evidence nodes standalone, all four acceptance spot-checks, CI
re-verified) and FAILED the wave on leg 6: two claims in the integration record's "Dogfood
closure" bullet did not survive re-derivation. The conductor's record — again — is where the
gate bit (the D-22 precedent working as designed).

**ERRATUM (the original bullet stays as authored above; this correction is the record):**
- **F1 cure:** at the time the record was committed (7b257bc) the true counts were
  **mint ×9 / claim ×9** — seqs 1, 2, 3 (wave openers) · 6 (authoring judge) · 9 (G16
  follow-up) · 10 (orchestrate judge) · 11 (coordinate judge) · 12 (G17 sweep) · 15 (sweep
  judge) — not ×6. The bullet was drafted from the dispatch-time state and not refreshed;
  the eval's own dispatch (seq 20) later made it 10. `capture ×4` and `phase ×1` were exact.
- **F2 cure (the claim is WITHDRAWN):** "refusal-driven DENY … exercised live" was FALSE as
  written — the two spot-audit refusals raised typed exceptions (`RecordClaimRefused`,
  `CaptureRefused`) but **no cursor DENY event existed on this run at record time**
  (`deny()` is invoked on the mint/governor refusal path per §1.8, not by claim/capture
  refusals). Honest restatement: two refusal classes fired live without DENY lines; the
  DENY event class was UNEXERCISED on this run when the record was written.
- **Post-finding live exercise (recorded fact, not a retro-justification):** a deliberate
  unmet-governor mint (`governs="ledger"`, role `coder` — a plan-executing class with no
  ledger rung) was refused with the typed `MintRefused` naming the legal path, the task
  PARKED at `.kata/escalations/deny-probe-w4-cure.json`, and the seam wrote cursor DENY
  line **seq 21**. The §1.4 role-class fail-closed rung and the §1.8
  every-denial-is-a-cursor-event law are both now live-exercised on THIS run.
- **DEF-12 filed:** whether claim/capture refusals should ALSO write cursor DENY events
  (§1.8's "every denial is a cursor DENY event" vs the current mint-path-only behavior) is
  a real boundary question surfaced by this finding — filed, not silently absorbed.
- Judge note N2 acknowledged: `4949b11`'s `Kata-Task: tm-w4-cursor-rename-sweep` trailer on
  a G18 conductor act is loose attribution in service of the rename (the D-22
  integration-time-attribution nuance, tier-2 semantics) — recorded, not repeated.

## Wave-4 FINAL EVAL round 2 — NEEDS_WORK (F3) + the cure (the same class, one layer deeper)

Round 2 verified the F1/F2 cures closed (nine seqs exact; DENY seq 21 live; DEF-12 valid;
code state byte-identical to the green-lit tip) and found **F3**: the erratum's sentence
"the task PARKED at `.kata/escalations/deny-probe-w4-cure.json`" asserted an artifact that
did not exist. The conductor had copied the refusal message's ADVISORY narration ("an
unattended run PARKS the task at …") into the record as a performed fact — but parking is
the CALLER's act (`kata_dispatch._park_path` only computes the path so the refusal can name
it; `escalation.write_escalation` is the act), and the probe was run bare. The correction
delivering the do-not-assert-unexercised-machinery lesson itself asserted unperformed
machinery. Caught by the same judge on its second pass — the D-22 precedent applied twice
in one wave, both times against the conductor's own prose.

**CORRECTION OF RECORD:** at the time of the round-1 erratum, NO park had been performed;
the clause was false as written and is WITHDRAWN in that form.

**The park is now PERFORMED, as the caller's act:** `escalation.build_escalation(taskId=
"deny-probe-w4-cure", kind="human-required", …)` → `escalation.write_escalation(".kata", …)`
→ `.kata/escalations/deny-probe-w4-cure.json` written and verified present (recommendation:
retire the probe task — its purpose, the live §1.8 DENY exercise, is complete; surfaced on
the operator veto ledger with everything else).

**DEF-13 filed:** a refusal that NAMES a park path which nothing is obliged to create is
the same boundary family as DEF-12 — whether refuse-to-mint should itself write the park
artifact (or a caller contract should bind it) is a design ruling, filed not patched.

**Conductor lesson (kata-improve fold, joining R14):** a refusal/error message's narration
is a DESCRIPTION of the legal path, never evidence the path was taken. Records cite
artifacts (paths that exist, lines on the cursor), not message text.

## Loop-A integration record (2026-08-17 — the G19 consolidated wave: frozen W5 + W6-detectors + W7 close-machinery/doctrine; every fact mechanically re-derived)

- **Five task branches merged no-ff with `Kata-Task:` trailers, each verified post-merge
  (G10.2):** `1515338 tm-la-judge-contract-rewrites` (tip d268444) · `28bb512
  tm-la-blocking-detectors` (f49ac87) · `ccbac76 tm-la-signal-detectors` (74c00e7) ·
  `27ebb6e tm-la-close-machinery` (tip b92e34e) · `2f0b192 tm-la-doctrine-amendment`
  (tip bee2ed3).
- **Judge verdicts (fresh-context, default-FAIL, one per item, captured via the seam):**
  blocking-detectors PASS first round (the judge mutation-tested the no-exec-sinks tripwire;
  3 live stub findings in existing tools/ recorded) · signal-detectors PASS first round
  (E7 edge_honesty deviation UPHELD; `UNATTESTED` accepted as in-scope — both
  conductor-ratified) · judge-contract-rewrites NEEDS_WORK ×2 (F1 `allowed=`-wiring
  present-tense over-claim at five sites; F2 the F1-cure's reviewer site list wrong —
  LS-33/35 are evaluator sites, LS-39 omitted) → cures 68e03f2 + d268444 → PASS round 3 ·
  close-machinery NEEDS_WORK (the G25 LIFO ordering GLOSS inverted at six prose sites while
  the code was correct — INCLUDING in the ratified proposal text, the conductor's miss too)
  → cure b92e34e → PASS · doctrine-amendment: the ONE advanced grill NEEDS_WORK (B1 law-13
  vs law-9 contradiction · B2 DET-09 row · B3 numbering paragraph · B4 scope-honesty
  self-violation; N1–N7) → fold bee2ed3 → grill re-verdict PASS, constraints re-held
  byte-level (core rule + judgment boundary md5-identical), zero E5 escalations across both
  passes.
- **Rulings this loop:** **G21** (reviewer token carries the grill-phase ladder row —
  live-proven: reviewer mints at ledger:draft, critic/challenger refused) · **G22-extension**
  (DET-09 row + "ten laws" heading/Enforcement wording joined the doctrine fold) · **G23**
  (numbers stay 13/15 per D173's naming; the Numbering paragraph deleted; the
  never-a-gap-number sentence struck) · **G24** (the doctrine fingerprint pin ADDITION —
  no pin exists today — rides Loop B `ev1-badge-registry`, the validator-check owner) ·
  **G25 as RESTATED** (LOOP-BACK over an open predecessor is legal; `close_run` closes
  still-open phases LIFO — most-recently-opened FIRST, so LOOP-BACK closes FIRST — then
  writes `run-closed` with `loopBack=1`; the original ratified gloss said "last" and the
  judge's fixture falsified it — conductor accuracy note, same D-22 family) · **@overload
  suppressor promotion DECLINED** (E3: block-and-signal is the correct fail-safe posture;
  a new suppressor class needs its own escalation with evidence).
- **Conductor integration acts, each distinct and vetoable:** G3 cursor.md pin paste
  `efdaf047…` (digest derived by builder, judge, and conductor-on-integrated-tree — three
  independent exact matches; supersedes the never-pasted intermediates b9ae816…/0ccfc698…)
  · G9 guard-family rows for `kata_close._safe_path` + `truth_serum._guard_path`
  (invariants conductor-re-verified live; family test 71/71 after) · G9 exec-safety sink
  rows for `kata_close._pinned_git` + `kata_close.default_evidence_runner` (judge-verified
  against the real sinks; test_exec_safety 15/15 after) · G2 README regeneration.
- **Spot-audit (ONE, conductor, live):** (1) the merged B1 detector run over the INTEGRATED
  tools/ tree — BLOCK with exactly the 3 known findings (drift_gate.py:79,
  iac_apply.py:815, kata_web.py:620 — the latter two are deliberate n=0-live/quiet-override
  shapes) out of 947 candidates, matching the task judge's independent run; B1's production
  input is the task-modified set, so these block nothing today — they are W7
  gate-preconditions input-set evidence. (2) The G24 gap demonstrated live: one word of
  docs/DETERMINISM-DOCTRINE.md mutated (RETIRED→RETAINED), validator exit 0, mutation NOT
  caught, file restored byte-clean — priority evidence for the Loop-B pin addition.
- **Integration gauntlet 4/4** (pytest-unit 0 · pytest-integration 0 · ruff 0 · validate-skills 0; validator 49 skills, 0 errors, 0 warnings) + **G11:** the close race/interleaving set ×10 sequential fresh processes 40/40 pass, plus the seam atomic-claim node 1/1.
- **DEF-12/DEF-13 inputs:** close-machinery answered the §1.8 DENY boundary for ITS surface
  only (a close refusal is a recorded gate verdict, not a DENY-class act) and its analysis
  argues FOR DEF-12's change on the claim/capture surface — both DEFs stay OPEN as filed.
- **Carried to Loop B briefs:** corpora activate per-judge under the NEW W5 contracts (the
  first loop whose eval judges run under them) · grounding-agent reconciles the
  `v1-provisional` fact-table row shape shipped by truth_signals · ev1-badge-registry gains
  G24 (the doctrine pin addition + its check) and the S3↔badge-registry wiring ·
  gate-preconditions (stacked) reads B1's input-set question (the 3 live tree findings +
  truth_serum self-block DEF-16) and the per-judge tripwire activation per R-M6.
- **Operator veto surface this loop:** the cursor.md paste (one revert) · the two G9 row
  commits · rulings G21–G25 (vetoable by objection) · the doctrine amendment itself lands
  with NO mechanical pin until Loop B (stated, not hidden).
- **DEF-14..DEF-21 filed** from builder/judge deferral candidates — none silently dropped;
  BL-N24-class items (Ellipsis-only stubs, bare-name false-negative class, constant-level
  orphans) recorded here FOR THE PLANNING WINDOW rather than DEF-filed (backlog-fence).

## The G26 CI strand (2026-08-17) — two rounds, three defects, instances 4–6 of the platform/promise-divergence family

Loop-A integration went CI-red TWICE on the windows leg at
`test_kata_board.py::test_concurrent_rotations_never_clobber_an_archive` (a W2-era test on
code no Loop-A task touched) before going green. Ruling **G26**: a stacked
root-cause-before-fix task (`task/tm-la-rotation-liveness-fix`, the D-24/D-27 precedent),
two rounds, merges `c9e6b6a` (edb206a) + `4904922` (c2778ec), both trailered and verified.

- **D-28 · Round 1 (run 32003837572, red @ b880810): the Windows sharing-violation window.**
  `os.replace(board.md → archive)` needs DELETE access on its source; a concurrently held
  read handle (any racer inside `_read_cursor_bytes`, or AV/indexer) vetoes it —
  `PermissionError` winerror 32 (source held) / 5 (destination held), raw-OS probed. All
  four racers can lose a round this way; the test's "progress guaranteed by construction"
  docstring was POSIX reasoning (the D-25 shape). Forced-contention reproduction: pre-fix
  20/25 all-fail rounds; post-fix 0/25 with exactly one winner per round. Cure: a bounded
  7-attempt (~187 ms) retry on exactly the measured transient class; election semantics
  untouched; exhaustion still refuses loudly, now naming the OS error and the budget.
  20×/20 green locally pre-fix — contention-dependent, CI-runner-only; the conductor did
  NOT wave it through as a flake.
- **D-29 · Round 2 (run 32006013216, red @ c9e6b6a): two deeper defects the upgraded
  refusal diagnostics exposed.** (1) An `O_CREAT|O_EXCL` archive reservation is
  RE-ACQUIRABLE mid-`os.replace` (the destination is momentarily free during the replace —
  measured steal rate 1-in-20 000), letting two racers co-own one archive path, each one's
  cleanup wrecking the other's (the observed ENOENT + moved-0-observed-121 refusals).
  (2) 🔴 **The blank-cursor branch was an election violation with data loss:** a racer that
  read the cursor as absent (a real window between a winner's archive-move and publish)
  reached `path.unlink()` behind a *"harmless — no data is involved"* comment, DELETED the
  winner's published cursor (measured 98B→34B) and published its own header — **two runs
  each believing they owned the cursor**, the exact property D-25's election exists to
  prevent, asserted in a comment instead of enforced at the boundary (the D-26 shape,
  again). Cure: archive names are RUN-PRIVATE (`board.<stamp>.<run-token>.archive.md`,
  token derived from the already-minted run id — no new entropy sink, law 9; no consumer
  parses archive names, grep-verified) so name contention is REMOVED not narrowed; and
  blankness is PROVEN before any discard (move to the run's own private archive, inspect,
  restore-and-refuse if non-blank). Revert-proof: pre-fix the blank-branch test ends
  `DID NOT RAISE` — the racer silently became a second winner. Cascade probe 60 rounds
  0 all-fail; forced 25 rounds 25 wins; G11 10× 87/87 each; full gauntlet 5128/3 green.
- **Conductor scope ratifications:** the round-1 minimal-blast-radius call (retry only the
  measured syscall) and the round-2 in-grant correctness fix (defect 2 feeds the observed
  cascade) — both ratified; `archive_token` stays public (test-consumed).
- **Green CI citation (the strand's proof): run 32008635522 @ `4904922` — SUCCESS both
  legs.** Two superseded evaluator mints recorded honestly: records `…-50` (subject tip
  b880810, went red) and `…-52` (subject tip c9e6b6a, went red) were claimed but never
  launched; the Loop-A final eval runs under a fresh record at the true cured tip.
- **Family note for the lessons fold:** with D-25 (rename no-op), D-26 (docstring promise),
  D-27 (POSIX strands), this makes SIX instances of one meta-defect — a concurrency/
  platform property asserted in prose and falsified by measurement. The burn's detectors
  (D-26's boundary-enforcement thesis) and this strand's upgraded refusal diagnostics (the
  round-2 root cause was legible ONLY because round 1's cure put the diagnosis in the
  assertion) are the accumulating counter-machinery.

## Loop-A FINAL EVAL — PASS (2026-08-17, fresh-context default-FAIL judge @ efeae5b)

All eight legs re-derived under the judge's own execution: 7 trailered merges with
second-parents byte-exact · zero drift across 57 changed paths (G6/G20/G21/G26 + conductor
acts all traced) · gauntlet green incl. full pytest 5128/3 · all 7 declared evidence nodes
standalone · five per-task acceptance spot-checks (incl. an unplanned live anti-vacuity
demonstration when the judge's own scratch run grazed tools/.venv and B1 REFUSED) · the G26
shipped state verified (run-private archives, prove-before-discard, bounded class-gated
retry) with CI 32008635522 re-confirmed both legs · 14 record claims verified (the
`efdaf047…` pin now has FOUR independent derivations; the superseded evaluator mints -50/-52
confirmed claimed-never-launched) · PD-2 sweep clean. The judge's close: the two prior D-22
failures did not repeat — where the record had room to over-claim, it under-claimed.
Residuals R1–R8 carried (R1 spot-audit denominators must pin their input set — conductor
practice, adopted; R2 filed as DEF-22). **Loop B is unlocked.** Operator surface: rulings
G21–G26 (one veto line each) + the cursor.md paste + the two G9 commits.

## DEF-22 (filed via the Loop-A eval R2) — see .planning/DEFERRED.md

## Loop-B integration record (2026-08-17 — corpora ∥ grounding ∥ EV-1 with gate-preconditions STACKED + the G28 flip; every fact mechanically re-derived)

- **Five task branches merged no-ff with `Kata-Task:` trailers, each verified post-merge:**
  `314bb8a tm-lb-judge-tripwire-corpora` (tip 262f584 incl. the docstring cure) · `da2a618
  tm-lb-tripwire-clause-flip` (G28, d164294) · `022f0dd tm-lb-gate-preconditions` (45f9f8d,
  stacked on the corpora tip per G19) · `d3f1dea tm-lb-grounding-agent` (8fa2de3) ·
  `bf4ffbb tm-lb-ev1-badge-registry` (b402237).
- **Judge verdicts (fresh-context, default-FAIL, NEW W5 contracts, captured via the seam):**
  grounding PASS first round (its own tamper probes; residuals: parse recomputes the roll-up
  only — consumer-wave rec; DEF-17's premise REFUTED by E7: no public per-citation B5
  callable exists) · ev1 PASS first round (the scope-attack survived; F1 anchor-breadth
  closing assertion routed to the G27/W9 grant; the judge's trailer-present remark was
  contradicted by the conductor's mechanical check — noted) · corpora NEEDS_WORK (a FALSE
  observed-divergence claim in the line-ending rationale + two of three honest labels
  missing from the module's own docstrings) → cure 262f584 → PASS · gate-preconditions PASS
  first round (E8 falsified two ways and held; the DEF-16 ruling — task-modified input set,
  no self-exemption — endorsed; a mid-build wrong-SHA table-pairing bug found by the builder
  and pinned) · the G28 flip conductor-verified (six files, pins still green).
- **Conductor integration acts, each distinct and vetoable:** G9 guard rows
  (`gate_preconditions`, `tripwire_check`) + the fs_atomic nine-scoped-sites acknowledgment
  incl. the judge-F1 rename (ad7c142) · G9 `kata-grounding: economy` work-class row
  (5bb2997) · **G24 re-approval — the doctrine fingerprint pin pasted `47d6a52b…`, derived
  FOUR independent times; the Loop-A demonstrated mutation-passes-unseen gap is CLOSED**
  (9503b95) · the EV-1 registry reconciliation (1ff75b9, below) · G2 README (03d5ab8).
- **🏆 EV-1's FIRST LIVE CATCH, at its own integration:** the G28 clause-flip (one branch)
  reworded the six tripwire clauses while the badge registry (another branch) anchored the
  OLD wording — at merge, the validator fired 11 uncited-claim-term errors + 5 stale-anchor
  errors. Exactly the cross-branch drift class EV-1 was built for, caught the first time two
  concurrent branches could produce it. Reconciled as a conductor act on the growing
  registry: 5 re-anchors + 6 new `non_claims` rows (all negation/downgrade lines), validator
  back to 0/0 at 50 skills.
- **Spot-audit (ONE, conductor, live, cross-task):** the composition no single judge could
  run — a REAL truth_serum B1 report over two integrated files → `grounding_gate.
  detector_rows` → `build_fact_table` → render → parse round-trip (verdict GROUND), then the
  tampered roll-up REFUSED with the law-13 recompute message. The detector→table seam works
  across the two tasks' code on the integrated tree; the table→final_gate hop remains
  honestly unwired (the close/W8 wiring, stated).
- **Integration gauntlet 4/4** after TWO in-integration catches: (1) EV-1 (above); (2) the
  corpora completeness check fired on the sibling-branch `kata-grounding` skill
  (unclassified new evaluate-family member) — filed in `NON_JUDGE_EVALUATE_SKILLS` per its
  own contract's not-a-judge statement, a distinct conductor commit. Final: pytest-unit 0 ·
  pytest-integration 0 · ruff 0 · validate-skills 0 (50 skills, 0 errors). G11 regression:
  board suite ×3 (87/87 each incl. the G26 races), close race set 4/4, benchmark watchlist
  103/103 (the two environmental reds the grounding judge saw did NOT reproduce).
  **Conductor accuracy note (D-6a class, self-caught):** the first gauntlet invocation
  piped the runner into `tail` and echoed `$?` — the printed GAUNTLET_EXIT=0 was the
  pipe tail's, while pytest-unit had FAILED; the failure surfaced anyway in the summary
  table and was root-caused, but the rule is re-learned: never read a gate's exit through
  a pipe.
- **Rulings this loop:** G27 (badge_registry.json becomes a cross-wave shared file; W9/Loop-D
  gains a grant + the anchor-breadth closing assertion lands there) · G28 (the clause-flip,
  executed) · the R-M10 engine-stricter-than-contract reconciliation ruled
  no-text-change-needed (the kata-evaluate clause stays true until a grounding pass actually
  runs — first at the burn's own close) · the co-author-trailer question ruled non-material
  (G10.3 binds `Kata-Task:` only).
- **Carried to Loop C (hook-activation):** the exec-safety scan already reaches
  `adapters/claude/hooks/kata-seam-guard.py` (the ev1 fixture proves enforcement pre-landing)
  — the hook builder MUST register its sink row or the validator fails · DEF-15 (the
  `allowed=` wiring is the natural rider on the hook wave's kata-orchestrate adjacency —
  NOT granted yet, needs a ruling if ridden) · the fact-table→final_gate wiring question.
- **Carried to Loop D (relabel):** G27 grant · the two `pending_graduation` rows route
  through promise-audit finding 8 · every `BUILT—Verified` mark needs a registry row with a
  live check in the same commit (W9's registry work is proportional to its relabel work).
- **DEF-23..DEF-28 filed**; smaller nits (read_mutation_closure root-guard, the
  quote-paraphrase in limit 5, HOST_ONLY_ROLES attribution, stale mutation_run anchor ×2
  faithful-quote class, TestExecSafety ImportFrom gap, PlatformActivation citation-on-
  honor-system-rows cosmetic) recorded HERE as fold-candidates for any authorized touch.
- **Operator veto surface this loop:** the G24 paste (one revert) · the four other act
  commits · rulings G27/G28 (vetoable by objection).

## Loop-B FINAL EVAL — PASS (2026-08-17, fresh-context default-FAIL judge @ 000f2a6)

Hostile re-derivation under the judge's own execution: 5 trailered merges + 8 named conductor
acts (topology exact, zero substitution); zero drift across 38 paths; validator 50/0/0, ruff
clean, full pytest 5333 passed/3 skipped ZERO failures; all six evidence nodes standalone; the
five per-task acceptance spot-checks (corpora activation scratch-derived incl. the
identical-hash-on-restore, gate-preconditions E8 live linux+win32-active/darwin-honor,
grounding law-13 tamper refusal, EV-1 doctrine pin the FIFTH independent 47d6a52b derivation +
mutation-sensitive, the G28 landed-truth clauses). **Both in-integration catches reproduced
NUMERICALLY EXACTLY** — EV-1's 16 errors = 11 uncited + 5 stale-anchor (checked out the
pre-reconciliation registry against the current tree), and the corpora completeness catch
`['kata-grounding']` by name (revert-check). 12 record claims spot-verified, zero false; the
conductor's self-reported piped-exit-code defect verified as honest-against-interest (the judge
hit the same pipe class twice itself and re-ran every gate exit-direct). PD-2 sweep: every gap
disclosed, no overclaim. Residuals R1–R12 carried to Loop C — **R11 is a HARD gate: the ev1
exec-safety scan already reaches adapters/claude/hooks/, so the hook task MUST register its
sink row or the validator fails; R5/DEF-24 (preconditions not yet demanded at the gate call
sites) must not calcify; R10/DEF-15 (allowed= wiring) needs a ruling if ridden on the hook
wave.** **Loop C is unlocked.**

## Loop-C integration record (2026-08-17 — the LAST switch: Honor-system ends)

- **One task branch merged no-ff with its `Kata-Task:` trailer, verified post-merge:**
  `tm-lc-hook-activation` (tip 548cd68 = the hook 6dddf32 + the G30 badge graduation).
  8-file diff (7 grant + G30's badge test); README already in sync (no skill frontmatter
  changed); validator 50/0/0.
- **Judge verdict (fresh-context, default-FAIL, NEW W5, captured via the seam): PASS first
  round — and it is the burn's single most-verified gate.** The judge drove the REAL script
  end-to-end (deny/allow/replay/semantic-revalidation/non-kata-silence/internal-error) and
  **MUTATION-PROVED the enforcement claim**: a neutered validator AND a blanket-denier both
  derive `Dormant`; only the genuine hook derives `Verified (intercepting)`. A
  deny-everything hook cannot read as Verified — the RS-H4 fingerprint+tripwire are jointly
  necessary and neither inherits. Capture edge proven both paths (sync post-edge; async
  SubagentStop+agentId); O_CREAT|O_EXCL capture-guard raced; deny appends a cursor DENY line;
  hostile agent_id never reaches the FS; internal deadline 10s < settings timeout 20s pinned
  as a pair; settings digest matches the file.
- **Conductor spot-audit (ONE, live on the burn's OWN cursor):** the real hook, run against a
  record-less Agent call in the conductor's live kata scope, returned the PreToolUse
  deny-JSON (`permissionDecision: deny`, "a record-less launch is denied"). Enforcement is
  genuinely active on this tree, not just in fixtures.
- **Rulings this loop:** G29 (probe deny-tripwire → active + the pinning-assertion flip;
  executed by the builder) · **G30** (conductor act: graduate the ev1 badge test that pinned
  `declared-before-active` — the sibling task is closed; the flip is its downstream) · **G31**
  (the kata-orchestrate stop-pre-claiming + recordId-in-brief documentation is a
  post-activation truth-fix — ridden into Loop D, W9's doc-honesty domain) · **G32** (the G29
  cross-wave touch of probe_registry.json + test_evidence_grammar.py is SANCTIONED — the W2
  task deliberately seeded the probe `declared-before-active` and authored the flip
  instruction; a recorded cross-wave shared-file).
- **The honest post-activation posture, stated:** the hook is BUILT, tested, mutation-proven,
  and its settings.snippet.json carries the install digest — but the snippet is a committed
  TEMPLATE; it is NOT installed into any operator's live `~/.claude/settings.json`, and
  `~/.claude/settings.json` is unguardable by kata (§11 residual). So enforcement is
  **proven-live-via-the-tripwire-and-subprocess, install-gated** — the conductor's own
  dispatches this burn ran Honor-system (the hook was not intercepting THIS session), and
  every dispatch named its recordId anyway (the de-facto convention G31 documents). Guardian
  grade for the seam: **Verified (intercepting) WHERE INSTALLED**, with the install + the
  UNPROBED scopes (interactive/Kiro/Codex/nested-Agent/global-settings) as open operator
  Human Moments.
- **Gauntlet + G11 + live tripwire — with an honest flake note.** The FIRST integration
  gauntlet invocation reported `pytest-unit FAIL` (exit 1) while the summary's other three
  gates passed; the specific failing test was not captured (the gauntlet streams uncaptured).
  Under D-25/G11 discipline this was hunted, NOT waved through: the full `-m "not integration"`
  suite was re-run THREE times (once with `-p no:randomly`) — **5374 passed / 3 skipped, zero
  failures each** — and the new concurrency/subprocess-heavy surface (`test_seam_guard.py`)
  looped **15× standalone, 43/43 every time**. 18 subsequent clean runs; the red did not
  reproduce. Assessed as an unreproduced transient (most plausibly a subprocess-spawn
  resource/timing hiccup under the gauntlet's concurrent load on Windows — the class the
  seam-guard tests are most exposed to), recorded here rather than relabeled 4/4-first-try.
  The clean gauntlet 4/4 for the record is the re-run below; **CI on both platforms is the
  cross-platform arbiter** (unlike D-28, this occurrence is local-single, not CI-seen). G11
  seam-guard race set ×10 = 30/30; live tripwire denies end-to-end.
- **Carried to Loop D:** G27 (badge registry grant) · G31 (the kata-orchestrate fix) ·
  DEF-22 (observability.md stale refs) · the §10 closes citations · the BACKLOG truth-status
  table FILED not edited (fence, GATE-PLAN ruling 2).
- **DEF-29..DEF-31 filed** (capture-edge live probe for Verified-post-edge; the marker-loss
  fail-open residual channel; the global-settings install Human Moment).
