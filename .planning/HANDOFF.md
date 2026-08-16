---
date: 2026-08-16-overnight
kind: manual
trigger: overnight autonomous execution complete — operator asleep; morning re-anchor
branch: burn/backlog-burn-02 (stacked on burn/backlog-burn-01) · BOTH PUSHED · PR #54 open (burn-01 → master) · master untouched at d4650fc
green: closing gauntlet 4/4 on the integrated burn-02 tree — pytest 4493 / 3 pre-existing skip · integration 2/2 · ruff clean · validator 49/0/0
authored-by: the overnight session (operator-directed: "execute as far as you can without me")
---

# HANDOFF — 2026-08-16 OVERNIGHT

## 0. GROUND TRUTH — verify before trusting anything below

```
cd C:\Dev\projects\kataharness
git status --porcelain                          -> empty
git rev-parse --abbrev-ref HEAD                 -> burn/backlog-burn-02
git rev-list --count burn/backlog-burn-01..HEAD -> grows with remediation; 35 at the AV-2 audit (the branch NAME is the durable fact, not the count — AV-2 H3 caught the stale "~20")
cd tools && uv run python scripts/gauntlet.py   -> 4/4 PASS (pytest 4493)
```

## 1. WHAT THE OVERNIGHT SESSION DID — all operator-directed before sleep, none invented

1. **D171 executed:** pushed burn-01, opened **PR #54** to master, froze + ran the parallel small
   burn, opened the UX grill.
2. **backlog-burn-02 COMPLETE (5/5, two waves)** — the first burn run UNDER the BBM rules, all
   items dispatched to Opus-5 builders in pinned outside-the-root worktrees, hybrid-gated
   (self-gate re-run + fresh judge per item + one spot-audit + integrated gauntlets). Full
   evidence + the BBM-6 accuracy record: `specs/backlog-burn-02/OBSERVATIONS.md`. Headline
   (corrected per the final eval F3/F4): item content verified sound · 1 known test-quality
   defect shipped in wave-1 test code (vacuous params; fix dispatched) · net-new defects found
   by judges (3), a builder audit (1), and the OPERATOR (🔴 BL-M34, the loop bypass — the
   biggest) · 1 escalation (recorded plan amendment) · 1 gate rejection (fixed) · H1's
   serial-gate bottleneck did NOT reproduce · H6 wrong-base did NOT recur.
   **FINAL EVAL: round 1 NEEDS_WORK → targeted-fix round → round 2 PASS (2026-08-16).** The
   cycle honored the loop's SEMANTICS by hand — no mechanical run-level re-loop route exists
   (BL-N19); one run-level eval covered both waves (wave-per-loop ruled mid-remediation, NOT
   applied retroactively — recorded deviation, AV-2 M4). Durable gate evidence emitted (`specs/backlog-burn-02/
   evidence/` — RESULT/footprint/mutation, live non-vacuity probe, two evaluators re-derived it).
   F5 RULED (ride-along, one-time) · the vacuous-params fix MERGED and eval-probed · records
   corrected. PASS ≠ nothing left: 🔴 BL-M34 loop-bypass enforcement, BL-X08/09/10/11, BL-N18
   all filed and live; the run's shape stays recorded DRIFT under BBM-12 (wave-per-loop RULED).
3. **The UX system grilled + compiled + convergence-gated to FREEZE-CANDIDATE.** Rulings UX-28..32
   recorded live with the operator before sleep (wrapper-preferred entry + env provisioning ·
   committed grammar engine · glyph-first transcript from the probe-1 result · all-three
   wrappers · open preload seam + the third-party independence doctrine). Then: dispatched
   design-author → convergence R1 (HOLD 7H) → rev 2 → R2 (HOLD 3H) → rev 3 → conductor-verified
   clean. Every overnight conductor ruling carries the grep-able label
   `[author-proposed, conductor-ruled interim — operator confirms at freeze]`; §8.1 indexes them.
4. **Probe 1 RESOLVED with the operator** (ANSI stripped in the Claude transcript, glyphs clean)
   → UX-30 glyph-first ruling + PLATFORM-MATRIX updated.

## 2. 🔴 NEXT — the operator's morning list (present, do not pre-decide)

1. **UX freeze sign-off** — read `specs/ux-rework/CONVERGENCE-R1.md` "Owed to the operator at
   freeze": confirm/overrule the 6 interim rulings · reconcile the launch-template palette
   divergence (#B5894B/#c9d1d9/#61afef vs the generator tones — "lock A" is in tension) ·
   stat-box reconstruction approval · preload-seam config shape.
2. **Ship decisions:** PR #54 merge timing; whether burn-02 gets a stacked PR or waits.
3. **BL-X08 triage** — the batch run-shape preset writes a config the load-guard STOPS (live,
   judge-verified). Small but real.
4. 🔴 **PAT rotation** (deferred 2026-08-02 — deferred is not dropped) · **T-03 scope call** ·
   probes 2–6 when convenient (each minutes, none blocking).

## 3. SETTLED OVERNIGHT — do not re-litigate (but operator may overrule the interims)

D171 (planning depth) is a DECISIONS entry. UX-28..32 are ledger rulings made WITH the operator.
The convergence interim rulings are labeled AND indexed — they are proposals of record, not locks.
The burn-02 plan amendment (X02 owner set) is committed history.

## 4. WHERE EVERYTHING IS

`specs/backlog-burn-02/{PLAN,OBSERVATIONS,evidence/}` (the burn + its evidence) ·
`specs/ux-rework/{DESIGN,CONVERGENCE-R1,GRILL-LEDGER,PLATFORM-MATRIX}.md` (the freeze candidate +
its audit trail; rulings UX-28..33) · `DECISIONS.md` D171+D172 · `BACKLOG.md` (filed this
session: 🔴 BL-M34 · BL-X08/X09/X10/X11 · BL-N18/N19/N20/N21 · amendments to BL-N01 🔴 /N04/N10
/N16) · LESSONS-LEARNED 2026-08-16 block · PR #54. Prior handoff block below still binds for everything it covers.

---

# ↓ PRIOR HANDOFF BLOCK — 2026-08-16 morning (superseded above; retained per convention)

---
date: 2026-08-16
kind: manual
trigger: operator-directed handoff — deep context, session refresh; everything recorded in depth first
branch: burn/backlog-burn-01 · ~38 commits, NO remote branch, NOTHING pushed · master untouched at d4650fc
green: gauntlet 4/4 at fa03958 — pytest 4485 / 3 pre-existing skip · integration 2/2 · ruff clean · validator 49/0/0
authored-by: the outgoing session, by hand
---

# HANDOFF — 2026-08-16

## 0. GROUND TRUTH — verify before trusting anything below

```
cd C:\Dev\projects\kataharness
git status --porcelain                          -> empty
git stash list                                  -> empty
git rev-parse --abbrev-ref HEAD                 -> burn/backlog-burn-01
git rev-parse --short master                    -> d4650fc   (untouched all session)
git rev-list --count master..HEAD               -> ~38  (commits after this handoff add more)
cd tools && uv run python scripts/gauntlet.py   -> 4/4 PASS   (use uv run — .venv python false-reds 2 integration tests offline)
```

⚠️ **The branch has NO remote.** Nothing from two sessions of work is pushed. The push/PR decision
is the operator's and is OWED (§5).

## 1. WHAT THIS SESSION DID — four deliverables, all committed, none stubbed

1. **Finished backlog-burn-01 — 6/6 items closed.** Waves 2+3 built this session by dispatched
   builders, gated default-FAIL: the config load-guard is REAL (`tools/kata_config.py`,
   `validate_core_config` + `available_from_skills`, 33 tests / 16 proven non-vacuous,
   kata-orchestrate 0.18.0) · `/kata-loop` exists · the code map measured **25 → 157 files seen**.
   A builder escalated an internally-unsatisfiable brief (exact-version test pin vs mandated bump
   vs ownership) — the pin is now a semver floor. Evidence: `specs/backlog-burn-01/OBSERVATIONS.md`
   (H1 gating-bottleneck CONFIRMED · H5 contract-vs-gate collision ×2 · H6 wrong-base provisioning
   ×2 · H7 push-back paid 3× · CHANGELOG has the full three-wave entry).
2. **Filed the 2026-08-15 planning batch** — top of `BACKLOG.md`: **BL-N01..N17 + BL-X01..X07**,
   each with what-it-is / existing-machinery map / open questions. The deep ones: the Kitchen role
   model (conductor · thin orchestrator · advisor · evaluator · ARBITER · challenger) inside
   BL-N08; run statistics semantics (BL-N14: cumulative, counters are run STATE never config);
   handoff-on-demand (BL-N15); **the learning graph (BL-N16), operator-RULED**: dedicated learning
   agent + gate, confidence-thresholded additions, recency-resolved contradictions → the NEW
   learning-management component, Hermes-derived append-for-audit/distill-for-load + staged-diff
   approvals + security scan, Kiban as an additional gated destination; engram→learning scrub
   (BL-N17, BC-aliased).
3. **Designed Burn mode on paper** — `specs/backlog-burn-mode/GRILL-LEDGER.md` **BBM-1..11**
   (gate design, partition engine, intake, width, entry, accuracy metric, wave-boundary dial with
   per-shape defaults: burn=autonomous · wave-cadence=approve · version-up=asked).
4. **Designed the ENTIRE UX system** — `specs/ux-rework/`: **GRILL-LEDGER UX-1..27** (every ruling
   with its rejected alternatives) · **DESIGN.md** (draft; §6 lists exactly what is still open) ·
   **PLATFORM-MATRIX.md** (per-host capability, evidence-labeled, 6 cheap probes) ·
   **templates/** (the width-asserted Python generators + approved HTML finals — **the generators
   are the pixel-exact spec**; they lived only in session scratch until preserved this session) ·
   `../learning-graph/RESEARCH-HERMES-PI.md` (field alignment). Two research agents were dispatched
   and their reports committed verbatim with evidence labels.

## 2. 🔴 NEXT STEP — the operator SET this agenda; do not invent a different one

**"Determine the next planning items, and how far we need to plan before we decide to run our
coding execution."** Frame it as a decision the operator makes WITH you. The honest inputs:

- **Ready to grill now (design exists, needs grill→freeze):** the UX system (DESIGN.md draft +
  UX-1..27) · Burn mode (BBM-1..11) · the learning graph (BL-N16 ruled + field-researched).
- **Cheap unblockers before any build:** the six platform probes (PLATFORM-MATRIX §4 — minutes
  each; probe 1, ANSI-in-transcript, decides color-vs-glyph for the whole transcript grammar) ·
  the small fixes BL-X01/X02/X03/X05/X07 (each ≤1 file).
- **Big items needing full grills from scratch:** the Kitchen (BL-N08 — operator has unsaid
  details, wants a live grill) · Truth Serum (BL-N01, blocked-shaped by BL-M33's missing seam).
- **A candidate shape for execution:** a burn (mode-prototype round 2) over the BL-X fixes +
  probes, while the first big grill (UX or Kitchen) runs — but that is a CANDIDATE, not a
  decision. D169 binds: nothing dispatches without a frozen plan.

## 3. DECISIONS SETTLED THIS SESSION — do not re-litigate

| decision | where |
|---|---|
| "Wave" is the official term; never "sprint" | UX-16 |
| Internal codenames (Kitchen, engram…) never user-facing; **the vault is KIBAN** (verified on disk `~/Kiban/Vault`) | UX-24, memory |
| Boxes = data · dividers = prose · scissors = copy; rust chips = interruptions only; double border = human decision only | UX-15/18/19/20 |
| The ONE waveform (open swell, exact components), 64/72 measures, generator-asserted widths | UX-13, templates/ |
| Wave-boundary dial `waveBoundaries` per-shape defaults, declared highlighted in run-start | BBM-11 |
| Learning is PER-AGENT, gated, confidence-thresholded, recency-resolved; append-for-audit / distill-for-load | BL-N16 |
| Run-start = truth serum (incl. explicit NOT-in-this-run); closeout = mini-loop ending in [0] fresh-session | UX-16/19/20 |
| Loop-back onramp = initiate-with-carried-context + the D71 grill dial; no third path | UX-19 |

## 4. WHERE EVERYTHING IS

`BACKLOG.md` top (the batch) · `specs/ux-rework/{GRILL-LEDGER,DESIGN,PLATFORM-MATRIX,templates/}` ·
`specs/backlog-burn-mode/GRILL-LEDGER.md` · `specs/backlog-burn-01/OBSERVATIONS.md` ·
`specs/learning-graph/RESEARCH-HERMES-PI.md` · `CHANGELOG.md [Unreleased]` · memory: Kiban rename.
**Prior queues (session-lifecycle HELD grill, D-register, MindBridge scope rulings) are UNCHANGED
by this session — the 2026-08-02/03 blocks below still bind for them.**

## 5. OWED TO THE OPERATOR

1. **Push/PR decision** — ~38 unpushed commits, no remote branch. Backout = one branch delete.
2. 🔴 **Rotate the GitHub PAT** — deferred by the operator 2026-08-02. **Deferred is not dropped.**
3. **T-03 scope call** (all six determinism laws vs the 13+15 subset) — carried, still unanswered.
4. The next-session planning-depth decision (§2) is theirs to make.

## 6. WHAT I GOT WRONG THIS SESSION — so you don't inherit it as truth

- **Mocked "PokeVault" repeatedly** after the vault had been renamed Kiban — operator corrected;
  verified on disk; memory updated. Grep for PokeVault before shipping anything.
- **Let "the Kitchen" leak into user-facing mock copy** — internal analogy only; operator caught it.
- **Left the pixel-exact templates in session scratch** until the final wrap — they would have
  evaporated. Preserved at `specs/ux-rework/templates/` only because the operator demanded a
  no-stub recording pass.
- **The heredoc escape trap** (Bash-tool heredocs eat one backslash level) burned several
  regeneration cycles — use the Edit tool on generator files, not shell string surgery.
- The first wave-2 dispatch attempt used the host's auto-worktrees, which failed on path casing
  AND provisioned at a stale base (H6 again) — manual `git worktree add` at a pinned SHA is the
  standing rule (BBM-9).

## 7. REDACTION

No secrets, keys, or PII in any artifact. The PAT is referenced by location only. New code this
session: `tools/kata_config.py` (+tests) — Snyk-scanned clean by its builder; template generators
are .planning reference material, not shipped code.

---

# ↓ PRIOR HANDOFF BLOCK — 2026-08-02 (superseded above; retained per convention)

---
date: 2026-08-02
kind: manual
trigger: operator-directed handoff — context budget, queue clear
branch: grill/session-lifecycle · 8 commits AHEAD of the pushed remote · master at a815c2b
green: pytest 4301 / 3 pre-existing skip · integration 2/2 · ruff clean · validator 49/0/0 · Snyk 0 med+
authored-by: the outgoing session, by hand
---

# HANDOFF — 2026-08-02

## 0. GROUND TRUTH — verify before trusting anything below

```
cd C:\Dev\projects\kataharness
git status --porcelain                          -> empty
git stash list                                  -> empty
git rev-parse --short origin/master             -> a815c2b
git rev-parse --abbrev-ref HEAD                 -> grill/session-lifecycle
cd tools && uv run python scripts/gauntlet.py   -> 4/4 PASS
```

*(No HEAD SHA pinned, deliberately — committing this file moves HEAD, so a pin goes stale against its
own document. The branch NAME is the durable fact.)*

⚠️ **8 commits are local-only.** `git rev-list --count origin/grill/session-lifecycle..HEAD` → 8.

## 1. THE QUEUE IS CLEAR — seven items shipped, all gated

| item | plain description | commit |
|---|---|---|
| `KH-T02` | Prime Directives could be **inverted** and still pass a 7-substring check | `0a44bc2` |
| `KH-T02+` | Same protection widened to all 13 protocol contracts | `4f16cbc` |
| `BL-M21` | Crash recovery would force-delete all 6 live `task/*` branches | `2828040` |
| `T-04` | Gate credited a `RESULT.json` **56 commits stale** as current green | `bf163fd` |
| `KH-T12` | Thin-orchestrator doctrine landed as binding (spine #8) | `6d02f1e` |
| `KH-T13`+`KH-B42` | Design/plan authoring became dispatched roles + the gating rubric | `7dee6f7` |
| `BL-F01` | "Frozen" became a recorded state that **blocks** dispatch (D169) | `6b4e8db` |

**One theme:** every one was a rule that existed only as prose with nothing enforcing it.

**Method shift, and it held:** from `BL-M21` onward the conductor stopped writing code and **dispatched
builders, gating each default-FAIL.** The gate rejected one build — over a frozen invariant that the
conductor's *own brief* had broken. That is `protocol/orchestration.md` running on itself.

## 2. NEXT STEP — nothing is forced; pick with the operator

The backlog queue that drove this branch is **empty**. Do **not** invent a next item. Candidates:

1. **Push + PR decisions** (below) — the only thing actually blocking.
2. **`DEF-2`** — `learn_feed` silently drops ledger entry bodies (measured: 20 of 29 entries, 19,153
   chars). **Its first question is undecided:** does the emit block extend to all 19 ledgers?
3. **The eight ungated protocol files** — `board.md`, `exec-safety.md`, `observability.md`,
   `iac-safety.md`, `narration.md`, `validation-misses.md`, `advice.md`, `persona.md` are absent from
   `REQUIRED_PROTOCOL` entirely, so no layer protects them. `board.md` carries a literal run-isolation
   MUST. Registering them newly gates them — its own decision.
4. **Encode the context-boundary *cost comparison***. The 0.70 trigger and *"early exit is a risk equal
   to rot"* are already in `kata-selfhandoff`. What is NOT encoded is the reasoning that actually
   decides it: cold-start re-derivation cost vs. work remaining · is the work dispatchable (so cost
   lands in a builder's context, not the session's) · is the handoff already fresh enough that a
   mid-work boundary is cheap. Operator flagged this as wanted.

## 3. DECISIONS SETTLED — do not re-litigate

| decision | detail |
|---|---|
| **Protocol contracts are tamper-evident** | Clause-pinned + fingerprinted. `config.md` fingerprint-exempt on measurement (31 commits — a registry) |
| **"Done requires proof, not assertion"** | PD-2 clause: built AND (machine-confirmed with numbers OR operator-approved) |
| **Degraded scan ⇒ never destroy** | Salvage-rename to `kata-salvage/<id>-<sha>`, never `branch -D` |
| **Identity, not ancestry** | `merge-base --is-ancestor` returns TRUE for the stale SHA — proven |
| **Thin orchestrator is binding** | Behaviour *graded*, contract *tamper-evident*; the doc says so |
| **`KH-B42` rubric is empirical** | Six rows, each a check that caught a real defect on this branch |
| **Freeze BLOCKS, never warns** | D169. *"We don't want a model … executing because it sees warn as a soft status"* |
| **MindBridge out of scope** | `KH-T09` and `DF-06` dropped |

## 4. ⚠️ THE GRILL ON THIS BRANCH IS HELD — read before touching it

`.planning/specs/session-lifecycle/` holds a **36-entry ledger** and **three** convergence reviews, all
**HOLD** (9 → 13 → 12 HIGH). **`SL-1`…`SL-36` must NOT be compiled into a DESIGN** — several carry a
`· LOCKED` token and are still wrong; `CONVERGENCE-HOLD-{1,2,3}.md` are authoritative wherever they
disagree. Root cause recorded: Phase 0 *measured* `DECISIONS.md` instead of reading it, and designed
against four frozen decisions it never opened. **Its questions and the operator's rulings survive** —
that half is good; the conversion into an executable contract is what failed.

## 5. WHERE EVERYTHING IS

`.planning/STATE.md` CURRENT — the same picture, freshly rewritten (it had been stale since 07-22) ·
`.planning/BACKLOG.md` top — `BL-F01` marked built, with the assessment kept because the *reasoning* is
the reusable part · `protocol/orchestration.md` + `protocol/authored-artifact-gate.md` — the two new
binding contracts · `.planning/specs/dispatch-authoring/` — frozen DESIGN+PLAN for what shipped ·
`.planning/DECISIONS.md` D168–D169 · `CHANGELOG.md` `[Unreleased]`.

## 6. OWED TO THE OPERATOR

> **⚠️ Items 2, 3 and 5 were DISCHARGED on 2026-08-03 — see §9 below.** Kept here
> rather than deleted so the arc stays legible; struck text is done, not pending.

1. **🔴 Rotate the GitHub PAT.** Plaintext at `settings.json → env → GITHUB_PERSONAL_ACCESS_TOKEN`,
   exported into **every process Claude Code spawns**. *(Correction carried forward: earlier handoffs
   called this "mode 666 / world-readable" — **wrong**. The NTFS ACL grants only the user,
   Administrators, SYSTEM. Env-injection is the real exposure.)*
   **STILL OPEN — deferred by the operator 2026-08-02. Deferred is not dropped; keep surfacing it.**
2. ~~**8 unpushed commits.**~~ ✅ **PUSHED 2026-08-03** — and the count was wrong: it was **10**, not 8.
   The two extra were the handoff and orientation commits themselves, written *after* the count was
   taken. Same self-referential trap this file warns about twice for pinned `HEAD` SHAs.
3. ~~**PR #51** · **PR #53**~~ ✅ **BOTH MERGED 2026-08-03.** `#51` → `74efe98`; `#53` retargeted to
   `master` explicitly (GitHub does **not** auto-retarget while the old base branch still exists) and
   merged → **`cf2ee50`**. Merged tree verified byte-identical to the gated tree; gauntlet re-run on
   the mainline: **4/4 PASS**.
4. `DEF-1` · `DEF-2` (+ its undecided repo-wide-block question) — **STILL OPEN.** `DEF-2`'s question
   is the one thing blocking a cheap fix: **does the emit block extend to all 19 ledgers?** Its
   one-line sibling `BL-M24` (heading regex counts the ledger's own H1 — still `^#{1,6}`, verified
   2026-08-02) lives in the same file and should be fixed in the same run, not separately.
5. ~~`T-10` — still no description anywhere in the repo.~~ ✅ **CLOSED unbuilt 2026-08-02 (D170)**, with
   the description finally written down in `INGEST-PLAIN-ENGLISH.md` §9 before closing it. `T-00` closed
   by the same ruling; `T-09` verified moot.

## 7. WHAT I GOT WRONG

- **A brief of mine broke a frozen invariant** (`benchmark.py` must not spawn). The gate caught it; the
  resolver moved to `run_result.py`, which already spawns. Fault was the brief, not the worker.
- **Left `benchmark.py` mutated** during my own mutation check by mixing up the working directory.
  Caught next command, restored byte-identical, re-ran the full gate.
- **Repeated "mode 666" three times** from an inherited handoff without ever checking it.
- **Pinned a HEAD SHA** that a commit one day earlier had removed for exactly that reason.
- **Under-stated the freeze finding** as "no skill owns it" when the state did not exist at all.
- **Wrote a weakening-check that proved nothing** (grepped removed lines that were just old call
  signatures); redid it on assertion counts, which is the check that actually binds.

**The dispatch gate, the operator, and the convergence passes caught these. None was self-caught.**

## 8. REDACTION

No secrets, keys, or PII. The PAT is referenced by location only. Snyk code scan: **0 medium+**.

## 9. ADDENDUM — 2026-08-03: everything landed on master

**`master` = `cf2ee50`.** The enforcement sweep is no longer branch-local.

**What was done, in order, each step verified rather than assumed:**
1. **Pushed** `9619ebc..dde0c46`. The "8 unpushed commits" figure in §0 and §6 was **10** — recorded in
   §6 rather than silently corrected, because the cause is instructive.
2. **Merged `PR #51`** (MindBridge ingest, 26 commits) → `74efe98`.
3. **Retargeted `PR #53`** from `docs/mergeback-ingest-itemization` to `master` **explicitly.** GitHub
   auto-retargets a stacked PR only when the old base branch is *deleted*; the branch still existed, so
   the retarget would never have fired on its own. Waiting on that side effect would have stalled.
4. **Merged `PR #53`** → **`cf2ee50`**.
5. **Verified the merge**: merged-`master` tree is **byte-identical** to the tree gated at `dde0c46`
   (`git rev-parse HEAD^{tree}` equality), so the 4/4 gate transfers by *identity*, not inheritance.
   Re-ran the gauntlet on the merged mainline regardless: **4/4 PASS** (pytest-unit, pytest-integration,
   ruff, validate-skills).

**Branch topology, measured before merging — nothing was stranded:**
- `grill/session-lifecycle` **contained** all 26 of `#51`'s commits (`merge-base --is-ancestor`, true).
- `master` held exactly **one** commit the branch lacked: `#52`'s merge marker `a815c2b`. The *content*
  of `#52` (`8d477f3`) was already in the branch, so there was no content gap and no conflict.
- **Ten branches are fully contained in `master`** and safe to delete — `task/m4p1-W{1..4}`,
  `task/m4p2-X{1,2}`, `docs/m4-gap-audit`, `docs/post-m4-handoff`, `docs/readme-box-plainer`,
  `m4/inline-eval`. **Verified, NOT deleted** — deletion is outward-facing and was not authorized.
  *(The six `task/*` branches are the exact six `BL-M21`'s crash-recovery bug would have destroyed.)*

**⚠️ The scope ruling that must not be misread.** "MindBridge is out of scope" drops the MindBridge
**chores** — the return handoff (`KH-T09`), chasing `DF-06` (`T-00`). It does **not** discard the ingest
documents: `INGEST-EXECUTION-ORDER.md`, `INGEST-PLAIN-ENGLISH.md` and `BACKLOG-FROM-MINDBRIDGE.md` carry
**the live work queue**, and merging `#51` is what kept them on the mainline. Closing `#51` unmerged
would have written *"intake rejected"* into the record while its commits landed anyway via `#53` — the
queue would have looked discarded to the next session. That risk was to the **record**, never the code.

**Closed this session (`D170`):** `T-10` (ingest-direction defect-carry) **unbuilt** — the two projects
share no git history, so code only ever crossed by hand-copy, and a copy never carries fixes made after
it was taken; with no transfer channel left in either direction the guard protects nothing. **Kept**:
*hand-copied code silently loses the fixes made after the copy* — a property of copying without a merge
base, so it re-opens on any future vendor/port, not on this item. `T-00` closed by the same ruling.
`T-09` verified **moot** (no "fork of" claim survives in README/STATE/HANDOFF).

**Recorded honestly:** `T-10` was carried by three sessions as a bare code with no description anywhere
in the repo, so no session could evaluate it and each forwarded it. The description was written *before*
closing it. Deleting it quietly would have repeated the fault it represents.

**Still owed, unchanged:** 🔴 the **PAT rotation** — deferred by the operator 2026-08-02, **not dropped**.

---

# ↓ PRIOR HANDOFF BLOCK — 2026-08-01 (superseded above; retained per convention)

---
date: 2026-08-01
kind: manual
trigger: operator-directed handoff — context low, one assessed item queued
branch: grill/session-lifecycle · 6 commits AHEAD of the pushed remote · master at a815c2b
green: pytest 4291 / 3 pre-existing skip · integration 2/2 · ruff clean · validator 49/0/0 · Snyk 0 med+
authored-by: the outgoing session, by hand
---

# HANDOFF — 2026-08-01

## 0. GROUND TRUTH — verify before trusting anything below

```
cd C:\Dev\projects\kataharness
git status --porcelain                          -> empty
git stash list                                  -> empty
git rev-parse --short origin/master             -> a815c2b
git rev-parse --abbrev-ref HEAD                 -> grill/session-lifecycle
cd tools && uv run python scripts/gauntlet.py   -> 4/4 PASS
```

*(No HEAD SHA pinned — deliberately. Committing the handoff moves HEAD, so a pin goes stale against
its own file. The branch NAME is the durable fact.)*

⚠️ **6 commits are committed locally but NOT pushed** (`9619ebc..HEAD`). PR #53's remote is behind.

## 1. WHAT THIS SESSION DID — six queue items, all built and gated

| item | plain description | commit |
|---|---|---|
| `KH-T02` | Prime Directives could be inverted and still pass. Now clause-pinned + fingerprinted | `0a44bc2` |
| `KH-T02+` | Same protection widened to all 13 protocol contracts | `4f16cbc` |
| `BL-M21` | Crash recovery would force-delete all 6 live `task/*` branches | `2828040` |
| `T-04` | Gate credited a `RESULT.json` 56 commits stale as current green | `bf163fd` |
| `KH-T12` | Thin-orchestrator doctrine landed as binding (spine #8 + `protocol/orchestration.md`) | `6d02f1e` |
| `KH-T13`+`KH-B42` | Design/plan authoring became dispatched roles + the rubric for gating unauthored artifacts | `7dee6f7` |

**Method shift mid-session:** from `BL-M21` onward the work was **dispatched to builders and gated
default-FAIL here**, not written inline. The gate rejected one build (see §7). That is the harness
running on itself; each commit message records what was verified rather than trusted.

## 2. 🔴 NEXT STEP — `BL-F01`, already assessed, do not re-derive

**Full assessment is at the top of `.planning/BACKLOG.md`. Read it before designing anything.**

**Freeze is not a recorded state.** A plan is "frozen" by convention; nothing records or checks it.
**The evidence is in this repo:** `.planning/specs/dispatch-authoring/PLAN.md` still says
`status: DRAFT — awaiting freeze-gate` — it was gated, built across five tasks, and committed while
claiming to be a draft. Nothing noticed.

**Scope is deliberately small and was verified, not guessed:**
- **NOT a new skill.** Freeze is a fact, not a behavior; the authoring skills already do the act.
- **"Has execution started?" needs NOTHING built** — `Kata-Task:` trailers + board CLAIM lines +
  `detect_lost_run` already answer it durably.
- **Two changes:** (1) constrain the `status:` field that already exists to `draft | frozen`,
  validated in the frontmatter reader that already runs; (2) give `kata_dispatch.build_brief` the
  plan path and refuse a brief for a non-frozen plan — **because there is no code chokepoint today**
  (`build_brief` never sees the plan; `parse_plan_tasks` runs only in crash recovery).
- **Operator ruling 2026-08-01: it BLOCKS, never warns.** *"We don't want a model making assumptions
  and just executing because it sees warn as a soft status."*

**Then:** push the 6 local commits · PR #51 / #53 decisions · rotate the PAT.

## 3. DECISIONS SETTLED — do not re-litigate

Everything in the 2026-07-28 block below still stands. Added this session:

| decision | detail |
|---|---|
| **Protocol contracts are tamper-evident** | Clause-pinned + fingerprinted; `config.md` exempt from fingerprinting on measurement (31 commits — a registry, not a contract) |
| **"Done requires proof, not assertion"** | New PD-2 clause: built AND (machine-confirmed with cited numbers OR operator-approved) |
| **Degraded scan ⇒ never destroy** | Restore salvage-renames to `kata-salvage/<id>-<sha>`; it never force-deletes |
| **Gate evidence needs identity, not ancestry** | `merge-base --is-ancestor` returns TRUE for the stale SHA — proven |
| **Thin orchestrator is binding** | Spine #8; behaviour is *graded*, the contract is *tamper-evident* — the doc says so explicitly |
| **KH-B42 rubric is empirical** | Six rows, each one a check that caught a real defect while gating on this branch |
| **MindBridge is out of scope** | Operator-directed. `KH-T09` (return handoff) and `DF-06` dropped |

## 4. WHERE EVERYTHING IS

1. **`.planning/BACKLOG.md`** — top block is `BL-F01`, the assessed next item.
2. `protocol/orchestration.md` · `protocol/authored-artifact-gate.md` — the two new binding contracts.
3. `.planning/specs/dispatch-authoring/{DESIGN,PLAN}.md` — the frozen spec for what shipped.
4. `.planning/specs/session-lifecycle/` — the HELD grill + 3 convergence reviews. **Still HELD; `SL-1`…`SL-36` must NOT be compiled into a DESIGN.**

## 5. OWED TO THE OPERATOR

1. **🔴 Rotate the GitHub PAT.** Plaintext at `settings.json → env → GITHUB_PERSONAL_ACCESS_TOKEN`, so
   it is exported into **every process Claude Code spawns**. *(Correction: earlier handoffs called
   this "mode 666 / world-readable". That was wrong on Windows — the NTFS ACL grants only you,
   Administrators and SYSTEM. The env-injection is the real exposure.)*
2. **6 unpushed commits.**
3. **PR #51** (MindBridge ingest, 26 commits) and **PR #53** (stacked on it) — both still yours.
4. `DEF-1` · `DEF-2` (learn_feed drops ledger bodies — does the emit block extend to all 19 ledgers?)
5. `T-10` — I still do not know what this is; no description exists in anything I read.

## 6. WHAT I GOT WRONG THIS SESSION

- **My brief broke a frozen invariant.** I told a builder to make `benchmark.py` shell out, forcing it
  to delete a test reading *"zero new exec sink is a frozen invariant."* The gate caught it; the
  resolver moved to `run_result.py`, which already spawns. **The fault was the brief, not the worker.**
- **Left `benchmark.py` mutated** during my own mutation check by mixing up the working directory.
  Caught on the next command, restored byte-identical, re-ran the full gate rather than assuming.
- **Repeated "mode 666" three times** from a prior handoff without ever checking it. It was wrong.
- **Pinned a HEAD SHA** in the last handoff that `d0498b8` had removed one day earlier for exactly
  that reason.
- **Under-stated the freeze finding** as "no skill owns the freeze stage" when the truth is the state
  does not exist at all.

**The dispatched-build gate caught the invariant breach; the operator caught the MindBridge bleed and
the over-complication risk on `BL-F01`. Neither was self-caught.**

## 7. REDACTION

No secrets, keys, or PII. The PAT is referenced by location only. Snyk code scan: **0 medium+**.

---

# ↓ PRIOR HANDOFF BLOCK — 2026-07-28 (superseded above; retained per convention)

---
date: 2026-07-28
kind: manual
trigger: operator-directed close-out after three convergence HOLDs
branch: grill/session-lifecycle · pushed · PR #53 (stacked on #51) · master at a815c2b
green: pytest 4126 / 3 pre-existing skip · integration 2/2 · ruff clean · validator 49/0/0 · Snyk 0 med+
authored-by: the outgoing session, by hand
---

# HANDOFF — 2026-07-28

## 0. GROUND TRUTH — verify before trusting anything below

```
cd C:\Dev\projects\kataharness
git status --porcelain                          -> empty
git stash list                                  -> empty
git rev-parse --short origin/master             -> a815c2b
git rev-parse --abbrev-ref HEAD                 -> grill/session-lifecycle
cd tools && uv run python scripts/gauntlet.py   -> 4/4 PASS
```

*(No HEAD SHA is pinned here, deliberately. `d0498b8` removed one from the last handoff for exactly
this reason — committing the handoff itself moves HEAD, so a pinned SHA goes stale against its own
file and halts the next session on a false alarm. The branch NAME is the durable fact. I re-made this
mistake while writing this block and caught it on the commit; it is recorded in §7.)*

- ⚠️ **Use `uv run`, never `.venv/Scripts/python.exe -m pytest`** — the latter false-reds 2 integration
  tests offline.
- **Branch / PR state (all pushed 2026-07-28):**
  - `grill/session-lifecycle` **(you are here)** — **PR #53, OPEN.** ⚠️ **Stacked on #51**, base is
    `docs/mergeback-ingest-itemization`, NOT master — this branch **contains all 26 of #51's commits**,
    so merging it to master would merge #51 as a side effect. GitHub retargets #53 to master
    automatically once #51 merges.
  - `fix/install-probe-host-coupling` — **PR #52, MERGED** to master (`a815c2b`); branch deleted.
    master moved off `fcb0338` for the first time in three sessions, by this one commit only.
  - `docs/mergeback-ingest-itemization` @ `d0498b8` — **PR #51, still OPEN and unmerged.**
    Deliberately not merged: the operator's review-and-merge decision on it is still owed.

## 1. WHAT THIS SESSION DID

Opened the grill §5 called for (`KH-T01` handoff-ready-always + `KH-T14` project wiki + read-back,
with `KH-B41` as input). The operator resolved **17 branches**; the ledger reached **36 entries**.

**A fresh-context convergence gate was then run three times and HELD every time: 9 → 13 → 12 HIGH.**

Also fixed a genuinely red gate discovered at close-out (§7 of this file is not the only place I was
wrong — see there).

## 2. 🔴 READ THIS BEFORE TOUCHING THE LEDGER

**The grill is HELD. `SL-1`…`SL-36` are NOT frozen and MUST NOT be compiled into a DESIGN.**
Several entries are marked `· LOCKED` and are nonetheless *wrong* — the token records that a branch
was decided, not that it survived review. `CONVERGENCE-HOLD-{1,2,3}.md` are authoritative over the
ledger wherever they disagree.

**What survives, and it is the valuable half:** every branch the operator ruled on held up under all
three passes. The questions were right; converting them into an executable contract is what failed.

**Findings that outlive the design — act on these regardless of what happens to the grill:**
1. `tools/recall.py` is **37 KB with no CLI and no production caller** (only its own test imports it).
   `kata-initiate` Phase 1b mandates a recall brief *"always"* and names that engine — so the mandated
   step **has no runnable command.** That is the mechanical reason it has never run.
2. `learn_feed` **silently drops entry bodies** — 20 of 29 entries, 19,153 characters, measured by
   running the shipped parser. Filed as **`DEF-2`**. D151/G1 fires the emit at *every* grill close and
   19 ledgers share the style, so the blast radius may be repo-wide. **Do not run a grill-close emit
   until this is settled.**
3. The **staleness comparator** is specified to same-second tie-breaking (`protocol/handoff.md:53-64`)
   and **implemented nowhere.**
4. `.kata/RESULT.json` is **56 commits stale** and an ancestry check does **not** catch it (verified:
   `git merge-base --is-ancestor 159fc9b HEAD` returns true). It also names
   `gateName: advisor-executor-integration` — **not the gauntlet** — so anything citing it as "last
   gate run" reports `537 passed` against a ground truth of `4/4`.
5. `.planning/STATE.md` frontmatter still reads `last_updated: 2026-07-22` — **now six days and three
   sessions stale**, and nothing detects it.
6. `protocol/handoff.md` **lacks the loop map `D67` mandates**, and `D67`'s never-summarized invariant
   block (`frozen-plan ref, goals, open decisions, open escalations`) exists nowhere.

## 3. DECISIONS SETTLED — do not re-litigate

Everything in §3 of the **2026-07-26** block below still stands. This session adds the operator's
rulings, all of which survived three adversarial passes:

| decision | detail |
|---|---|
| **Handoff is the WRITER of position, not a reader** | The planning surfaces are stale; the handoff derives position from live facts + git and writes it down |
| **Handoff must NOT depend on the wiki** | `KH-T01` couples to **`KH-B41`**, not `KH-T14`. The vault is optional, config-gated, and outside this repo |
| **Structure = enforced FLOOR + DEPTH** | Mechanical floor, model-authored depth, both required present |
| **Hollowness is caught by citations, never vocabulary** | A resolvable `file:line`, not a keyword — the `KH-T02` lesson applied |
| **Temporal entries are SUBJECT pages keyed on the artifact changed** | Promoted when ≥2 *distinct initiatives* touch it. Operator's framing: *"identified when something is changed, or repeated by nature"* |
| **Wiki scope = `synthesis/**` only** | `concepts`/`entities`/`references`/`sources` sit outside our feed dir and were never ours — the planning docs' framing was wrong |
| **A fresh handoff replaces orientation** | `kata-orient`'s full rebuild is the fallback for absent-or-stale only |
| **`KH-B41` stays out** | Arc comes free from `HANDOFF.md`'s git lineage (65 commits, never renamed) |

## 4. WHERE EVERYTHING IS

1. **`.planning/specs/session-lifecycle/CONVERGENCE-HOLD-3.md`** — start here. Most recent, and it
   names the root cause.
2. `CONVERGENCE-HOLD-1.md` / `CONVERGENCE-HOLD-2.md` — the earlier passes; still-live findings.
3. `GRILL-LEDGER.md` — 36 entries. **Read only alongside the HOLDs.**
4. `.planning/DEFERRED.md` — **`DEF-2`** is new.

Prior-session material (`TASKS-ARCHITECTURE-2026-07-26.md`, `INGEST-PLAIN-ENGLISH.md`,
`BACKLOG-FROM-MINDBRIDGE.md`, `OPERATOR-RULINGS-2026-07-26.md`) is unchanged and still accurate —
**except** `TASKS-ARCHITECTURE` §KH-T14 and `SESSION-LIFECYCLE-AND-SYNTHESIS.md` §4, which state the
four-empty-page-kinds claim this session disproved.

## 5. NEXT STEP

**Do NOT open a fourth repair pass on the existing ledger.** Three rounds each consumed the prior
round's findings and produced a comparable number of new ones.

**Re-open Phase 0 first, and read — not measure — these, before writing a single entry:**
1. `.planning/DECISIONS.md` — **D67 · D74 · D81 · D133 · D135 · D142 · D151**. 2734 lines of binding
   law. This session treated it as a parse target and that is the root cause of all three HOLDs.
2. `docs/DETERMINISM-DOCTRINE.md` **law 1** — titled *"One pinned git helper"*, and it says
   *"Never re-derive the pin set per call-site."*
3. `protocol/board.md` — the `MUST` at `:45-46` and the *"(or truncate it)"* at `:47-48`.
4. **The actual shape of `.planning/HANDOFF.md`** — it *accumulates* prior blocks (`:151`). Any
   section contract must scope itself to the newest block. `kata-handoff/SKILL.md:81` says refresh
   *"overwrites"*, which contradicts the file's own convention — **that contradiction is unresolved.**

**Then, in order:** `KH-T02` (harden the Prime Directives — operator called it top of queue) ·
`BL-M21` (destructive restore default) · `T-04` (stale-evidence gate — §2 item 4 gives you the
measured case) · `KH-T13` (dispatch design/plan).

## 6. OWED TO THE OPERATOR

1. **🔴 Rotate the GitHub PAT** — plaintext in `~/.claude/settings.json`, mode 666, injected into every
   spawned process. Not git-tracked, so nothing leaked. **Still not done; carried from 2026-07-26.**
2. **PR #51** — review and merge decision. **Still open**, and still yours. It was deliberately not
   merged despite blanket push/merge authorization, because `grill/session-lifecycle` contains its
   26 commits and merging that branch would have merged #51 silently as a side effect.
3. **PR #53** — review and merge decision on this session's grill artifacts. Merges into #51's
   branch as stacked, so it is gated behind the #51 call above.
4. **`DEF-2`'s first question:** does the emit block extend repo-wide to all 19 ledgers?
5. **`DF-06`** (withheld partial-scrub-risk note, never sent) · **`T-10`** (task or backlog?)
6. Carried: overnight-delegation confirmation · **two in-absentia ELEVATEs (both default DECLINED)** ·
   F3 quota classifier-precision call · v0.4.0 tag veto window.

## 7. THINGS I GOT WRONG THIS SESSION — so you don't inherit them as truth

- **Claimed a "free `T-04` fix."** An ancestry check does not detect a stale `RESULT.json`. The gate
  disproved it by *running the command*.
- **Mis-cited `LESSONS-LEARNED` L10 twice** as load-bearing rationale; re-anchored to L9, which does
  not support the claim either. Citation now dropped entirely.
- **Claimed "no real handoff has ever carried its provenance fields"** — the live one carries both. I
  inherited that from prose while asserting I had verified it from code.
- **Said a deferral "is parked"** when I had not written it. That is the exact PD-2 class the entry
  was repairing. `DEF-2` now exists.
- **Mis-measured `DECISIONS.md`** (2734 lines / 2 headings, not 2683 / 1) — my own regex excluded the
  level-1 heading. And miscounted the ledger as 29 entries when it was 36, *inside the entry
  correcting miscounts*.
- **Designed against four frozen decisions I never read**, and against a `HANDOFF.md` file shape I had
  read that morning and still ignored.
- **Pinned a `HEAD` SHA in §0 of this very file** — which `d0498b8` had removed from the previous
  handoff, with the reason written in its commit message, one day earlier. Committing the handoff
  moved `HEAD` and the pin was stale before anyone read it. Caught on the commit, not before.

**Every one was caught by the fresh-context gate, not by me** — which is the argument for keeping the
discipline, and the reason three HOLDs is a good outcome rather than a failed session.

## 8. REDACTION

No secrets, keys, or PII. The GitHub PAT is referenced **by location only**, never its value. Snyk
code scan on the modified files: **0 medium+**.

---

# ↓ PRIOR HANDOFF BLOCK — 2026-07-26 (superseded above; retained per convention)

> ## ⚠️ THIS IS A MANUAL HANDOFF — the automated machinery did NOT fire
>
> **Do not read this as evidence that self-handoff works.** It does not. This session *proved* it
> doesn't: the 0.70 trigger has **never fired** in any real session (peak observed across 22 recorded
> sessions: **69%**), `boundary`-supersedes-`self` is prose with **zero code**, the staleness
> comparator **does not exist**, and **no real handoff has ever carried its `kind:`/`trigger:` fields**
> (this one carries them because I typed them).
>
> Fixing that is **`KH-T01`**, and it is the highest-value item in the queue.

---

# HANDOFF — 2026-07-26

## 0. GROUND TRUTH — verify before trusting anything below

```
cd C:\Dev\Projects\KataHarness
git status                 # expect: clean
git stash list             # expect: EMPTY  ← D1 tripwire; if not, STOP
git rev-parse --short origin/master        # expect: fcb0338  (UNTOUCHED)
git rev-parse --abbrev-ref HEAD            # expect: docs/mergeback-ingest-itemization
cd tools && uv run python scripts/gauntlet.py    # expect 4/4 PASS
```

- **PR #51 is OPEN and unmerged.** Nothing from this work is on master.
- ⚠️ **Run the gauntlet via `uv run`, never `.venv/Scripts/python.exe -m pytest` directly** — the
  latter fails 2 integration tests in an offline sandbox and produces a **false red**. Cost me a
  false alarm this session.

## 1. WHAT THIS SESSION DID

Ingested the MindBridge merge-back, verified our own tree against its claims, fixed one live defect,
and — in the last third — made a set of **architecture decisions that are more valuable than the
code**.

**Shipped:** T-11 model-tier currency fix (semantic tier recognition, currency guard **wired**,
Bedrock/Vertex normalization, +34 tests, **two fresh-context advals folded**).

**Also shipped, late:** `tools/kata_handoff_break.py` (+16 tests) — the SESSION BREAK
notice. First concrete piece of `KH-T01`: it gives the *operator-facing* half of the
session boundary a deterministic owner. It does NOT close KH-T01 — the write half
(PreCompact actually writing a handoff rather than nudging) is still open.

**Everything else is decisions, itemized and unbuilt.**

## 2. 🔴 READ THESE FIVE FINDINGS FIRST — they reorder everything

1. **A stale `RESULT.json` is fully creditable by the gate.** Ours names a SHA **37 commits** behind
   HEAD and would be accepted today as proof the build passed. Confirms MC-05; raises `T-04`.
2. **The Prime Directives can be inverted and still pass.** The check is 7 substrings. A reviewer
   rewrote both directives to say the *opposite* — *"stub it and move on, present-but-dead counts as
   built"* — kept the words, **and the validator passed green.** → `KH-T02`, operator-flagged top of queue.
3. **Crash recovery would `git branch -D` six live `task/*` branches.** `kata_restore` defaults to an
   `integration` branch that doesn't exist here. Never run for real, so never noticed. → `BL-M21`.
4. **Our second brain is one bucket of five, never read back.** 269 pages in
   `synthesis/decision-patterns`; `concepts`/`entities`/`references`/`sources` = **0 each**. → `KH-T14`.
5. **We are, on some hosts, a wrapper around the host's agents.** Operator sees Kiro's `Forge`/`Momus`
   during our runs. We don't construct agents — we write prompts. → `KH-T10`, `KH-B43`.

**The unifying pattern, and the thesis of the whole session:**
> **The rule is written in a document for the AI to follow. Nothing in code enforces it.** Every
> subsystem with a real code owner came back working. Every invariant living only in a `SKILL.md`
> sentence came back unverifiable or quietly broken.

## 3. DECISIONS MADE — these are settled, do not re-litigate

| decision | detail |
|---|---|
| **Prose-first, scripts-when-optimal** | ⚠️ **CORRECTION.** We are **NOT** "scripts-first" — the old `CONTEXT.md` term was wrong and **went outbound to MindBridge.** Corrected. Prose is the default; a script is an optimization with a burden of justification |
| **Prose-first is NOT disproven** | Our prose broke because it was **ungoverned**, not because prose fails. All **ten** confirmed breaks map onto their proposed laws 11–16. That *raises* MC-02's value — but confirming the disease ≠ confirming the cure |
| **Thin orchestrator** | *"A well-behaved orchestrator does not do the work itself."* Adopted. Three teams reached it independently |
| **Orchestrator stays in the ROOT session** | Near-unanimous industry practice; Claude Code enforces it structurally. `LD11` is **not** a compromise to outgrow. `KH-T06` resolved |
| **Our single-writer discipline exceeds the field** | Nobody else arbitrates writes mechanically. Keep it |
| **Grill stays in-session; design + plan get dispatched** | `D70`: a grill with no human to interrogate isn't a grill. Design/plan authoring has no human channel → dispatch them |
| **Wrong model ⇒ BLOCK at readiness, tell them to `/model`** | Operator's own answer. Don't over-engineer it |
| **Project wiki, NOT saved chats** | Handoff = ephemeral/transactional. Wiki = long-lived decisions on tap |
| **Tiebreaker** | *"Strength is validation and determinism, not fast and loose execution."* Where the choice is more capability vs. proving what we claim — **take the proof** |

## 4. WHERE EVERYTHING IS

**Start here, in this order:**
1. **`.planning/TASKS-ARCHITECTURE-2026-07-26.md`** — every architecture decision, itemized with costs
   and open questions. **The most important file.**
2. **`.planning/INGEST-PLAIN-ENGLISH.md`** — the whole queue in plain language.
3. **`.planning/BACKLOG-FROM-MINDBRIDGE.md`** — all 26 of their items as ours (`KH-B01`–`KH-B26`) plus
   our own findings (`KH-B27`–`KH-B43`).
4. **`.planning/OPERATOR-RULINGS-2026-07-26.md`** — operator decisions, recorded in-repo deliberately
   so no grill has to cite a transcript.

**Supporting (read when the relevant task comes up):** `INGEST-EXECUTION-ORDER.md` (ordered queue +
a coverage audit that found four gaps in my own plan) · `D2-VERIFICATION-RESULTS.md` (18 probes with
evidence) · `MERGEBACK-INGEST.md` (coverage matrix, clean-room verdict) ·
`ORCHESTRATOR-PLACEMENT-RESEARCH.md` (cited survey) · `PROSE-FIRST-REASSESSMENT.md` ·
`THIN-ORCHESTRATOR-DOCTRINE.md` · `SESSION-LIFECYCLE-AND-SYNTHESIS.md` ·
`PHASE1-DISPATCH-ASSESSMENT.md` · `ARCHITECTURE-CORRECTION-2026-07-26.md`.

⚠️ **This session produced 13 planning documents.** That is itself the `KH-B41` problem (six surfaces,
no single view) made worse. Recorded honestly rather than hidden.

## 5. NEXT STEP

**The operator's stated next move: open the grill on the session lifecycle** — handoff-ready-always
(`KH-T01`), the project wiki as long-term memory (`KH-T14`), and read-back as what makes either real.
Kanban (`KH-B41`) is an explicit input.

**Then, in order:** `KH-T02` (harden the Prime Directives — operator called it top of queue) ·
`BL-M21` (the destructive restore default) · `T-04` (stale-evidence gate) · `KH-T13` (dispatch
design/plan).

## 6. OWED TO THE OPERATOR

1. **🔴 Rotate the GitHub PAT** — plaintext in `~/.claude/settings.json`, mode 666, injected into every
   spawned process. **Not** git-tracked, so nothing leaked. I did not rotate it; that is their account.
2. **PR #51** — review and merge decision.
3. **DF-06** — the fork named a withheld partial-scrub-risk item and never sent the note. Chase or accept.
4. **`T-10`** — task or backlog?
5. Carried from before this ingest: overnight-delegation confirmation · **two in-absentia ELEVATEs
   (both default DECLINED)** · F3 quota classifier-precision call · v0.4.0 tag veto window.

## 7. THINGS I GOT WRONG THIS SESSION — so you don't inherit them as truth

- Claimed **"BC preserved byte-for-byte"** and **"future emit-side bumps are safe."** Both **false** —
  I had silently widened a spend gate and broken `fallback_chain` with my own bump. Caught by adval.
- Claimed **"+18 tests."** It was 13.
- Wrote a **vacuous test** that couldn't fail; the break-probe caught it; my first *rewrite* was
  **still** half-vacuous and the second adval caught that too.
- Called our architecture **"scripts-first"** and **shipped it outbound to MindBridge.**
- Filed **14 of their 26 backlog items as "intelligence only"** — a dodge the operator called out.
- Framed *"prose-only invariants are broken"* as *"prose-first is broken."* Materially different.

**Every one was caught by adversarial review, a break-probe, or the operator — not by me.** That is
the argument for the discipline, and the reason to keep running it.

## 8. REDACTION

No secrets, keys, or PII in this handoff. The GitHub PAT is **referenced by location only** — never
its value.

---

# ↓ PRIOR HANDOFF BLOCKS — history, preserved per repo convention

*(The 2026-07-25 pointer block and the 2026-07-01/07-02 handoff below are superseded by the sections
above, but retained: this file's convention is prepend-and-keep, never replace. The v0.4.0-era detail
lives in `.planning/HANDOFF-NEXT-SESSION.md`, which remains accurate for the MindBridge import
protocol §6/§6a/§6b.)*

date: 2026-07-25 (v0.4.0 TAGGED; A/B/C/D execution plan COMPLETE; next = MindBridge feature import + quota Tier 3)
branch: master `8e6096f` (clean; tag v0.4.0; all session branches deleted local+remote after merge)
green: pytest 4072 passed / 3 skip (-m "not integration") · integration 2/2 · ruff clean · validator 49/0/0 · Snyk medium+ 0
tags: v0.4.0 · advisor-executor · quota-resilience · D1-fix · reliability-quartet · mindbridge-import-next · handoff
authored-for: a fresh Opus 5 session (operator updating Claude Code; sections map to the kata-orient tiers)
★ NEXT-SESSION START HERE — read **`.planning/HANDOFF-NEXT-SESSION.md`** (the detailed re-entry brief:
  ground truth + the Opus-5/Windows update gotcha, what shipped this session PRs #41–#47, item C
  quota-resilience in full, the prioritized backlog, the STANDING ORDERS, and — §6 — the **MindBridge
  feature-import clean-room scrub protocol** the operator directed 2026-07-25). Then `.planning/STATE.md`
  CURRENT block. v0.4.0 = advisor-executor (D167) + quota-resilience Tier 1+2 + the reliability quartet
  (bootstrap/dispatch stderr fixes, advisor deferral pins, the D1 phantom-corruption sandbox fix). The
  whole A/B/C/D plan is DONE; nothing is mid-flight; tree clean; stash empty.

*(Historical M4-era pointer below is superseded; kept as history — the M1/M4 work shipped as v0.2.0.)*


> **★ 2026-07-02e (Fable 5 session — M1 COMPLETE + MERGED):** Executed the full ADVAL→P2 plan end-to-end.
> **(1) D139 integrated adval:** 9 fresh-context reviewers over 653f501..8902fb0 → 9× SHIP-WITH-FIXES, 0 HOLD;
> 5 HIGHs (supersede-parser fail-open, edge_honesty relative-import blindness, surviving_stubs *.py-only,
> liveness self-approving escalation kind, lane-check rename blindness) + ~15 MEDs folded, 13 guards
> mutation-proven; L19 recorded (unit-reviewed ≠ integration-reviewed — the HIGHs lived at seams).
> **(2) D140 M1-P2 THE FLOAT built** via the dogfooded loop: PLAN-p2-float.md frozen only after THREE
> adversarial freeze-gates (v1 HOLD 18 findings — route-time-trailer rule + DESIGN Amendment #2; v2 HOLD 10 —
> NUL-delimited commit scan + base-module dangler semantics; v3 SHIP-WITH-FIXES 7 — freeze-commit scan bound);
> 5 build workers (T1 `contract_gate.py` 33 tests · T2 kata-plan RUBRIC schema · T3 kata-orchestrate 0.5.0 ·
> T4 kata-review surface 7 · T5 kata-evaluate 0.3.0), each conductor-gated; ONE gated deviation (exec-safety
> registry row, recorded in D140); 2 built-work sweeps (code + prose) both SHIP-WITH-FIXES, all folded
> (bare-`contracts` namespace exemption; R3 pin-revert mutation-pinned; declared-but-empty edges evaluator
> wedge; review-tier hardcoded surface counts made count-free → -standard/-advanced/-essential 0.1.1).
> **(3) MERGED:** PR #5 → master `0c82bc4` (merge commit, SHAs preserved); branch deleted local+remote.
> **Seven adversarial gates caught real unsoundness on this initiative — the discipline's strongest showing.**
> BC: every float surface no-ops absent a `builds_against` edge (zero exist in any run today).
> *(Prior blocks are history.)*

> **★ 2026-07-02c (Milestone 1 MERGED; Freeze/Float sanctioned + reconciled; M1-P1 built + reviewed SHIP):**
> On "just proceed": **merged PR #4** (Milestone 1) to master `8653faf` (merge commit — SHAs preserved),
> **rebased** `freeze-float/m1-contract-edges` onto master (clean), deleted the hardening branch. **Recorded
> Freeze/Float as the operator-directed Milestone 2 (D138)** in ROADMAP/BACKLOG/STATE.milestone + memory —
> closing the loop where a fresh/compacted context kept re-deriving "unsanctioned" from stale tracked docs.
> **Reconciled the M1 DESIGN** (the last `.kata/invalidated.json` residue → git-durable trailers; edge_honesty
> signature + set-based-subtract semantics documented) and **closed the two P0 `OSError` fail-opens** (M1-L9).
> **Built M1-P1** — the `kata_restore` durable-trailer substrate (`builds_against` union, `Kata-Invalidated:`
> subtract, `parse_supersede_trailers`), all trailer parsing in `kata_restore.py` (avoiding the `kata_supersede.py`
> name collision); +10 tests, mutation-proven; fresh-context adversarial review **SHIP** (one LOW folded).
> **Also corrected a v0.1.0 honesty over-claim:** the benchmark "n=0→n=1 live on a real control fixture" was
> actually a SYNTHETIC control (benchmark-D5 real-fixture still deferred) — fixed in CHANGELOG/ROADMAP/BACKLOG/STATE.
> Green: pytest **2236 / 3 skip**, validate 47/0, Snyk 0. Commits `81c8dd0` (reconcile) + `46c7601` (P1), UNPUSHED.
> **HELD before M1-P2 (the float)** — it needs its own freeze-gate + operator go. *(Prior blocks are history.)*

> **★ 2026-07-02 (Milestone 1 SHIPPED to PR; Freeze/Float M1-P0 built + reviewed):** This session (a) built +
> shipped **Milestone 1 — Release Hardening** (F1–F6 from the Kenjiri one-shot + a tool-agnostic security gate),
> **PR #4 OPEN** on `hardening/kenjiri-lessons` — every code fix mutation-proven, WS-A/WS-D adversarially reviewed
> (D137, LOCKED L1–L10); and (b) opened **Milestone 2 — Freeze/Float**, taking sub-milestone **M1 (contract edges)**
> from doctrine → 3-investigator grounding → **two adversarial freeze-gates** (both HOLD; the second caught that a
> `.kata/` durability fix would be lost on a crash → moved to git-durable commit trailers) → a **phased split
> P0/P1/P2** → the **P0 engine `tools/contract_edges.py` built (5 fns, 36 tests, all mutation-proven, Snyk 0) +
> adversarially reviewed (SHIP-WITH-FIXES → fixed: async false-negative, whitespace false-positive)**. The two
> freeze-gates stopping an unsound architecture *before any code* is the headline — the discipline paying for
> itself on the project's own hardest feature. **HELD at P0 by operator.** No forced next build; see §2/§4.

> **★ 2026-07-01 (restore-hardening SHIPPED):** This session designed (3-pass adversarial freeze-gate), built
> (Increments A + B), and MERGED the D132 Option-2 restore-hardening initiative to master (**PR #1**, `0bc2a0e`),
> then shipped a recurrence-hardening guard (**D136**) and a salesy README refresh (**PR #2**, `16007f7`).
> Everything is committed, pushed, and green. The loop caught + fixed **4 silent-under-dispatch bugs** across the
> build that the passing tests had blessed — all via fresh-context adversarial sweeps (the D124/D136 discipline
> proving itself live). No next initiative is chosen.

# HANDOFF — KataHarness — 2026-07-01 (restore-hardening SHIPPED · pick next initiative)

## 1. Read-in order  *(orientation: CONTEXT)*
**★ Context-lean rule: do NOT inline-read STATE.md (1000+ lines) or AGENTS.md wholesale.** Resume from:
1. `.planning/NEXT-SESSION-ORIENTATION.md` — paste-ready self-contained brief (current state + the open options).
2. `.planning/BACKLOG.md` — the candidate next-work list (v0.1.x deferrals #6–#13, restore follow-ups #14–#16,
   scheduled builds). This is where the next initiative comes from.
3. `.planning/DECISIONS.md` — skim the tail (D131 model-tiering → D136 silent-permissive-default). D133/D134/D135
   are the restore-hardening rulings; **D136** is the new never-tiered guard every future build must obey.
4. `.planning/specs/restore-hardening/{DESIGN,PLAN}.md` — the frozen spec, if touching restore code.
- If deeper context is genuinely needed: `AGENTS.md` (the spine + conventions), `protocol/state.md` (three-tier
  state D81), `README.md` (the just-refreshed landing page — honest-maturity claims; do not re-inflate them).
- ⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated). Follow `AGENTS.md` + repo `CLAUDE.md` only.

## 2. State  *(orientation: VOLATILE)*
- Branch `master`, tip **`16007f7`** (merge of PR #2). **Everything pushed, working tree CLEAN.** Tag `v0.1.0`
  stands at `365c7f1`.
- **Green: pytest 2170 passed / 3 skip / 0 fail · validate 47 skills / 0 errors · Snyk medium+ 0.**
  - ⚠️ **2 tests are `@pytest.mark.integration` and FAIL in an offline sandbox** (`test_benchmark.py::TestRunDualGateCwd::test_importing_fixture_gives_q_one` + `::TestDurableF2PProof::test_f2p_zero_to_one_transition`). Root cause: they spawn `uv run pytest` over a temp clone, which cannot build an ephemeral env offline. They PASS with network/uv available. Run the honest gate with `-m "not integration"`. NOT a regression.
  - Pre-existing `kata_install.py` LOW CWE-23 (operator-supplies-own-path) stays below the medium+ gate (`.snyk`).
- **Run tests via the repo venv:** `tools/.venv/Scripts/python.exe -m pytest tools/tests -q -m "not integration"`
  (bare `python` / `uv run` are NOT reliable offline here). Validator: `... -m validate_skills` (add `--write` to regen the README index).
- **Bump-on-modify is ACTIVE** (STANDARDS §3): every SKILL.md edit needs a semver bump. Editing a shared
  `RUBRIC.md` needs NO peer bump (verified: the validator does not flag it). New skills enter at 0.1.0.
- **★ D136 is now a LOAD-BEARING build rule** (see §4 hard rules).

## 3. What shipped  *(orientation: VOLATILE — recent history)*
**PR #1 (`0bc2a0e`) — restore-hardening (D132 Option 2, lean scope):**
- Increment A (`8a020e2`): 6 pointer-only `/kata` slash-commands (`adapters/claude/commands/`) + additive
  `_flat_link_commands`/`_link_or_copy_file` installer (5 frozen `kata_install.py` engine fns byte-identical;
  `.kata-commands.json` manifest; never clobbers a user's own command file).
- Increment B (`0e160c2`): `tools/kata_trail.py` (durable board → orphan ref `refs/kata/trail`, git-plumbing only,
  fail-soft) · `kata-orchestrate` step-5 integration-cadence checkpoint + `Kata-Task:<id>` trailer (→0.3.0) ·
  `tools/kata_restore.py` task-granular restore (re-dispatch = frozen-PLAN-ownership MINUS integration-committed;
  tier-2 authoritative for DONE; board corroborates, never gates) · `kata-orient`/`kata-readiness` restore prose
  (→0.2.0) · PreCompact auto-checkpoint hook (`adapters/claude/hooks/kata-precompact.py`).
- Decisions D133 (recovery-ref git carve-out), D134 (task-granular re-dispatch), D135 (board-is-the-trail).

**`70542a0` — D136 silent-permissive-default guard** (D33 never-tiered family): prose guards in `kata-tdd`
(→0.1.1) + `kata-review` RUBRIC. Baked from the session's dominant error pattern.

**PR #2 (`16007f7`) — README salesy refresh:** landing-page rewrite (standout features + explicit per-platform
install/update/factory-reset/wipe/uninstall lifecycle). A fresh-context accuracy pass caught + fixed 3 over-claims.

## 4. NEXT STEP — in order  *(VOLATILE — act on this)*
**There is NO forced next build. The restore-hardening initiative is complete + merged.**
1. **Re-anchor** — read this file + `NEXT-SESSION-ORIENTATION.md`. Confirm green (`-m "not integration"`).
2. **Pick the next initiative WITH the operator** — do NOT assume one. Present the §6 options and let the operator
   steer. The strongest candidates (operator's call): (a) **live-proof #2** — verify the PreCompact hook actually
   fires in a real Claude session (the one unproven seam; only confirmable live); (b) **restore follow-ups
   #14–#16** (safe-direction polish); (c) a **v0.1.x deferral** (#6–#13, e.g. Debug Mode live run, benchmark→improve
   hook); (d) the **wiring-completeness full build** (scheduled) or the **second-brain-learning** spec (D99).
3. **When a build is chosen** — run the full loop: grill → freeze DESIGN → adversarial freeze-gate (HOLD→SHIP) →
   PLAN → subagent build (disjoint ownership, TDD, LIVE PROOF) → fresh-context adversarial sweep → operator merge
   gate. **Drive via subagents** (Sonnet build / Opus judgment); the fresh-context sweep is non-negotiable.

## 5. Suggested next skills  *(orientation: CONTEXT)*
- `kata-orient` — re-anchor from HANDOFF + ORIENTATION on resume.
- `kata-grill-standard` / `-advanced` — to open a design loop once the next initiative is chosen.
- `kata-design-doc` → `kata-review` (freeze-gate) → `kata-plan-*` → `kata-orchestrate` — the build spine.
- `/kata-resume` (or `kata-orient`) — if a run was interrupted, this now restores it (the feature just shipped).

## 6. Open decisions for the human
**The only open decision is: what to build next.** Candidates (from BACKLOG; none is forced):
1. **Live-proof #2 (recommended first):** confirm the PreCompact hook fires synchronously with a usable budget in
   a real Claude Code session. This is the single unproven seam of the shipped restore feature; if it does NOT
   fire as assumed, Gaps 2/3 still close via the integration-cadence checkpoint (so it degrades safely), but the
   compaction-window floor of Gap 1 would need a different trigger. Only confirmable live.
2. **Restore follow-ups #14–#16:** fork-point same-commit edge; nested-`waves` value guard; restore degraded-mode
   structured signal. All safe-direction (over-dispatch / observability), small.
3. **v0.1.x deferrals #6–#13:** benchmark→improve hook; planning↔delivery-mode alignment audit; Debug Mode live
   run (n=0→1); AO module-rollup test seam; recurrence-hardening promote-gate + T3; β redaction filter; validator
   deeper checks; A3 carry-overs.
4. **Scheduled larger builds:** wiring-completeness full build (produced-vs-consumed sweep gate); second-brain-
   learning spec (D99, the Recall contract); v0.2 milestone proper (self-handoff + concurrency).

## 7. Redaction
No secrets / keys / PII in any artifact this session. Repo is PRIVATE. Working tree clean. Nothing to redact.
