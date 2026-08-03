---
spec: ungated-protocol-files
status: frozen
opened: 2026-08-03
baseline: master `bb8c709` · gauntlet 4/4 PASS · working tree clean
tier: kata-grill-standard
---

# GRILL LEDGER — the eight unguarded protocol contracts

> **Not frozen.** No entry here is a design contract until the fresh-context convergence pass returns
> SHIP and the DESIGN is compiled by a dispatched `design-author`. Entries marked `· LOCKED` record
> that a branch was *decided*, not that it survived review — the `session-lifecycle` grill was HELD
> three times for exactly that conflation.

## Phase 0 — grounding (read, not measured)

The prior grill on this repo was HELD three times because Phase 0 **measured** `.planning/DECISIONS.md`
instead of reading it. Every decision below was opened and read in full.

### Measured facts (verified in code, this session, at `bb8c709`)

| fact | value | how verified |
|---|---|---|
| protocol files on disk | **23** | `Get-ChildItem protocol\*.md` |
| in `REQUIRED_PROTOCOL` (term check) | **15** | read `validate_skills.py:302-336` |
| in `PROTOCOL_PINNED_CLAUSES` | **15** | read `validate_skills.py:411-501` |
| in `PROTOCOL_FINGERPRINTS` | **14** (`config.md` exempt) | read `validate_skills.py:506-521` |
| ungated by every layer | **8** | 23 − 15 |

### ⚠️ P0-F1 — the documented counts are STALE, and they are wrong inside a fingerprinted contract

`protocol/prime-directives.md:95-96` states *"Clauses are pinned for all 13 `REQUIRED_PROTOCOL`
schemas; fingerprints cover 12."* `validate_skills.py:372-375` says the same. **The real numbers are 15
and 14.** `orchestration.md` (KH-T12) and `authored-artifact-gate.md` (KH-B42) were registered on this
branch and the prose was never updated. `CLAUDE.md` also says "all 13 protocol contracts".

This matters beyond tidiness: the wrong count sits **inside a clause-pinned, fingerprinted file**, so
correcting it requires a deliberate fingerprint re-approval. It is a live example of the exact disease
this spec addresses — a documented invariant with nothing checking it stays true.

### ⚠️ P0-F2 — THE ROOT CAUSE: nothing enumerates the protocol directory

Every use of `PROTOCOL_DIR` in the tree is `PROTOCOL_DIR / fname` — a lookup of a name the code was
already handed (`validate_skills.py:343, 528, 540, 714`). **No layer ever lists the directory.**

Consequence: the eight are not eight oversights. **A new protocol file is invisible to every guard,
silently and permanently, from the moment it is created.** `orchestration.md` and
`authored-artifact-gate.md` escaped for a while for this reason and were only caught because their
authors happened to register them by hand.

**This reframes the work.** Registering eight files fixes today's instance. It does not stop the ninth.

### Decisions read in full (not measured)

- **D74** — β LEARN feed. **Load-bearing precedent:** its `BP2` added `engram.md` to `REQUIRED_PROTOCOL`
  as an explicit, recorded decision ("default-FAIL floor on the schema"). Registering a protocol file is
  therefore an established, decision-worthy act with prior art — not a novel mechanism. Also: redaction
  is a HARD pre-write gate, fail-closed.
- **D81** — three tiers; tier-3 `.kata/` is disposable, rebuilt from the git-committed trail. Note the
  distinction this spec must not blur: the **board file** `.kata/board.md` is disposable tier-3; the
  **board contract** `protocol/board.md` is a durable doc. Gating the contract does not touch the
  file's disposability.
- **D133** — the git carve-out is narrow and **board-only**: a mechanical helper may commit
  `.kata/board.md` to `refs/kata/trail` only; never a branch, never pushes, board-only, self-pruning.
  Registering `board.md` in the validator does not touch this carve-out.
- **D134** — restore is task-granular re-dispatch; tier-2 is AUTHORITATIVE for DONE, the board
  CORROBORATES and never gates.
- **D135** — **board-is-the-trail; no second append-only journal.** The board is already the event log;
  its only deficiency was living in gitignored tier-3. Any design here that proposes a parallel record
  of protocol state violates this outright.
- **D142** — the M4 observability addition (relevant because `observability.md` is one of the eight):
  additive schema bump, every field has a NAMED consumer, no backfill.
- **Determinism Doctrine law 1** — one pinned git helper; never re-derive the pin set per call-site.
  Binding on any new engine code this spec produces.

### Imperative density in the eight (a proxy for what is at stake, not a ranking)

`MUST|MUST NOT|NEVER|ALWAYS|never|invariant|forbidden|hard gate|fail-closed` occurrences:

| file | lines | hits |
|---|---|---|
| `iac-safety.md` | 337 | 27 |
| `observability.md` | 151 | 25 |
| `exec-safety.md` | 98 | 24 |
| `advice.md` | 133 | 23 |
| `validation-misses.md` | 141 | 17 |
| `narration.md` | 107 | 12 |
| `board.md` | 117 | 7 |
| `persona.md` | 68 | 4 |

`board.md`'s low count is misleading — its run-isolation rule is a single literal `MUST`
(`board.md:45-50`) on which the honesty of `concurrency.json` depends.

### ⚠️ P0-F3 — a live trap inside `board.md`

`board.md:47` permits the orchestrator to rotate a stale board **"(or truncate it)"**. Truncation
destroys the prior run's board. Pinning that sentence as a load-bearing clause would **freeze a
permissive branch into a tamper-evident contract**. Flagged by the 2026-07-28 handoff §5 and still
unresolved. This spec must decide whether to pin it, pin around it, or fix it first — pinning it as-is
is the one option that is actively wrong.

## The decision tree (Phase 0.2 — enumerated, dependency-ordered)

| # | branch | depends on | status |
|---|---|---|---|
| **B1** | **Instance or class?** Register the eight, or make the directory self-registering so a ninth cannot escape | — | **OPEN — asked first** |
| B2 | Which of the eight are contracts at all vs. reference material that should be explicitly exempt | B1 | OPEN |
| B3 | Which layers apply per file (terms / +clauses / +fingerprint), and does the `config.md` registry-exemption pattern generalise | B1, B2 | OPEN |
| B4 | Who selects the pinned clauses, and against what standard — this is the judgment-heavy half | B3 | OPEN |
| B5 | `board.md:47` "(or truncate it)" — pin as-is / pin around it / fix first | B4 | OPEN (see P0-F3) |
| B6 | The stale 13/12 counts (P0-F1) — same change or its own | B1 | OPEN |
| B7 | Does registration break the current green, and what is the migration if it does | B2, B3 | OPEN |
| B8 | Failure behavior: what happens to an unregistered-and-unexempted protocol file — hard fail or warn | B1 | OPEN |
| B9 | Authoring roles: DESIGN and PLAN are dispatched (KH-T13); conductor gates, never authors (spine #8) | all | OPEN |

## Resolved branches

### UPF-1 — The protocol folder becomes self-policing · LOCKED

- **Decision:** Every `protocol/*.md` must appear in **exactly one** of two places: `REQUIRED_PROTOCOL`
  (a guarded contract) or a new `PROTOCOL_EXEMPT` mapping (reference material, **with a written
  reason**). A file in neither **fails the validator by name**. The eight are then registered under
  that rule.
- **Rejected — register the eight by hand and stop:** it fixes today's instance and leaves the
  mechanism that produced it intact. The tenth protocol file escapes identically.
- **Rejected — add the rule but exempt all eight for now:** defers the whole risk-bearing half while
  claiming progress; the exempt list would ship pre-loaded with eight entries that nobody has a reason
  for, which is the dumping-ground failure mode built in on day one.
- **Rationale:** the defect is not eight missing entries, it is that **no layer can see the
  directory** (P0-F2). Registration-by-hand is exactly how `orchestration.md` and
  `authored-artifact-gate.md` came to be guarded — by someone remembering. A rule that depends on
  remembering is the disease, not the cure. The folder rule is also *less* code than eight hand-kept
  entries, so the anti-cathedral guard is satisfied: this is the plainest design that meets the goal,
  not an extra abstraction over it.
- **Provenance:** `validate_skills.py:343,528,540,714` (every `PROTOCOL_DIR` use is a lookup by a name
  already supplied; nothing enumerates) · `protocol/prime-directives.md:100-104` (names the eight and
  explicitly defers the decision) · operator ruling 2026-08-03.
- **Open edge carried to B8, not resolved here:** the exempt list is itself an escape hatch — a future
  agent could silence a guard by adding a file to it. Whether that residual is acceptable, and how it
  is made visible, is B8. It must be stated honestly in the contract rather than designed away
  (the `orchestration.md` "NOT mechanically provable" precedent).

### UPF-2 — All eight are contracts; `PROTOCOL_EXEMPT` ships EMPTY · LOCKED

- **Decision:** all eight register as guarded contracts. `PROTOCOL_EXEMPT` is built and wired but ships
  with **zero entries** — it exists as the declared path for a genuine future non-contract file (e.g. a
  `README.md` dropped into `protocol/`), not as a place to park work.
- **Rejected — exempt `observability.md`** (the one defensible candidate: it self-describes as
  documenting what exists rather than mandating behavior). Rejected because it still carries 25
  imperatives and names "gotchas that produce a silently-wrong read" — a wrong read of the
  observability contract corrupts evaluation, which is the gate. Exempting it would also establish on
  day one the precedent that *"this one is only descriptive"* — which is the reasoning that produced
  the hole in the first place.
- **Rejected — safety-critical three first, five parked:** would ship an exempt list pre-loaded with
  five entries whose reason is "not reviewed yet", i.e. the dumping ground, immediately.
- **Rationale / what they actually are** (read this session, not inferred): `exec-safety.md` is the
  RCE guard — *"the guard that stops the command/code-injection class from recurring"* (`:3-4`);
  `iac-safety.md` declares itself *"normative: a deviation is a contract violation, not a style
  preference"* (`:4-5`); `advice.md` is a machine payload schema of the **same kind** as
  `escalation.md` and `graph.md`, both already registered — leaving it out is an inconsistency, not a
  judgment; `persona.md` calls itself the *"single source of truth"* for voice. **Two safety contracts
  being unguarded is the sharpest fact in this spec.**
- **Provenance:** all eight read in Phase 0; operator ruling 2026-08-03.

### UPF-3 — All three layers apply to all eight; no fingerprint exemption qualifies · LOCKED

- **Decision:** each of the eight gets **term presence + pinned clauses + fingerprint** — the full
  treatment the other 14 fingerprinted contracts already carry. No registry-style exemption is granted.
- **Resolved by measurement, not by asking** (Phase 0.3): `config.md`'s exemption was earned on churn
  — 32 commits against 1–11 for every other protocol file, because essentially every feature adds a
  config key, so fingerprinting it would impose ~32 re-approvals and train blind re-approval. Commit
  counts for the eight, measured this session at `bb8c709`: `exec-safety` 12 · `board` 6 ·
  `observability` 5 · `iac-safety` 5 · `narration` 4 · `validation-misses` 3 · `advice` 2 ·
  `persona` 1. **Every one sits inside the 1–12 band**, and `engram.md` at 10 commits is already
  fingerprinted without complaint. The outlier criterion that justified the one exemption does not
  fire for any of the eight.
- **Consequence to state plainly in the DESIGN:** this adds 8 files × (clauses + fingerprint). Each
  future edit to any of them becomes a two-step act — change, then re-approve the fingerprint. That
  friction is the intended product, not a side effect (`prime-directives.md:92-93`).
- **Provenance:** `validate_skills.py:375-380` (the exemption and its stated criterion) · churn
  measured this session.

### UPF-4 — Pin board.md's run-isolation MUST; do NOT pin the truncation permission · LOCKED

- **Decision:** the pinned clause for `board.md` covers the run-isolation invariant — the board must
  contain only the current run's events, and a pre-existing board is rotated at run start before the
  first `CLAIM`. The **"(or truncate it)"** permission at `board.md:47` is deliberately **left outside
  the pinned set**.
- **Rejected — pin the sentence verbatim including truncation:** would make a permission that arguably
  contradicts `D135` *harder to remove than to keep*. A tamper-evident contract should protect the
  invariant, never the loophole.
- **Rejected — delete "(or truncate it)" first, then pin the corrected sentence:** the cleaner end
  state, but it is a **behavior change to a live contract smuggled inside a guarding change**. This
  spec's job is to make contracts tamper-evident; changing what they say is a separate act with its
  own review. Bundling them is precisely the "two things at once" the authored-artifact-gate rubric
  row 6 exists to catch.
- **Rationale:** truncation destroys the prior run's board. `D135` makes the board *the trail* — the
  whole reason no second journal was built — and `D133` carves out a git exception specifically so the
  board survives a crash. A contract clause that authorises deleting it sits in tension with both.
  Pinning the MUST while leaving the loophole editable gets the protection now and keeps the door open
  to removing the loophole cheaply later, with no fingerprint fight.
- **Follow-up filed, NOT built here:** *"should `(or truncate it)` be removed from `board.md`?"* — a
  standalone question for its own change, flagged by the 2026-07-28 handoff §5 and still open.
- **Provenance:** `board.md:45-50` · `D135` · `D133` (both read in Phase 0) · operator ruling
  2026-08-03.

### UPF-5 — Clause selection is DISPATCHED, against the standard already documented · LOCKED

- **Decision:** the conductor does **not** author the pinned clauses. Selecting load-bearing sentences
  for eight contracts is design work and is dispatched to a `design-author` role (`KH-T13`), then gated
  default-FAIL by the conductor against the six rows of `protocol/authored-artifact-gate.md`.
- **The standard is not invented here — it already exists** verbatim at `validate_skills.py:409-410`:
  clauses are *"chosen so that stating the OPPOSITE of the directive is impossible while the clause is
  still present."* That is the bar every returned clause is gated against. A clause that could survive
  an inversion of its own file's meaning is a rejected clause.
- **Rationale:** spine #8 — *"a well-behaved orchestrator does not do the work itself"* — and
  `protocol/orchestration.md`, which names authoring the design doc as doing the work rather than
  guarding it. Resolved without operator input because the routing is already binding law.
- **Provenance:** `AGENTS.md` spine #8 · `protocol/orchestration.md` · `protocol/authored-artifact-gate.md`.

### UPF-6 — The stale 13/12 counts are corrected in this change · LOCKED

- **Decision:** `protocol/prime-directives.md:95-96`, the `SCOPE` comment at
  `validate_skills.py:372-375`, and `CLAUDE.md`'s "all 13 protocol contracts" are corrected to the
  true post-change numbers in the same change that registers the eight.
- **Resolved without asking** — this is a factual error, not a design branch (P0-F1). The counts read
  13/12; the code says 15/14; after this change they become **23/22** (23 registered, 22 fingerprinted,
  `config.md` still the sole fingerprint exemption).
- **Consequence, stated because it is easy to trip over:** `prime-directives.md` is itself
  clause-pinned and fingerprinted, so correcting its own count **requires a deliberate fingerprint
  re-approval** via `--update-protocol-fingerprint`. The updater prints; it never writes. That is the
  machinery working, not a bug.
- **Rationale:** leaving a wrong count inside a tamper-evident contract, in the very change that
  widens tamper-evidence, would be the spec contradicting itself. It is also the disease in miniature
  — a documented number with nothing checking it stays true.

### UPF-7 — Green is proven by running the gate, never argued · LOCKED

- **Decision:** whether registration turns the suite red is **not** settled by inspection. The build
  runs the full gauntlet, and any term or clause that is not present verbatim in its file is a build
  finding to resolve — either the clause was chosen wrong, or the contract genuinely lacks the
  invariant it claims to carry. **The second case is a real finding and must be surfaced, not
  papered over by softening the clause until it matches.**
- **Rationale:** `PD-2` — done requires proof, not assertion. The prior session's `T-04` lesson is
  exactly this shape: a plausible argument that evidence was current, disproved by running the command.
- **Baseline to beat:** gauntlet 4/4 PASS at `bb8c709`, validator 49 skills / 0 errors / 0 warnings.

### UPF-8 — `PROTOCOL_EXEMPT`'s contents are pinned by a test · LOCKED

- **Decision:** a test asserts the **exact** contents of `PROTOCOL_EXEMPT` (today: empty). Adding an
  exemption fails that test **by name**, so it can never be a quiet one-line edit — it becomes a
  deliberate act that must be justified in the same change.
- **The attack this closes:** `validate_skills.py` is **not** itself fingerprinted. A future agent
  facing a failing clause check has two exits — fix the contract (intended), or add the file to
  `PROTOCOL_EXEMPT` (one line, silent, green). The second is faster and nothing notices. The test
  makes the cheap exit the loud one, leaving fixing the contract as the only quiet path.
- **Rejected — reason-string only:** relies on a human catching it in review. Review is exactly what
  failed to catch eight unguarded files for months.
- **Rejected — state the residual honestly and guard nothing:** honesty is necessary but not
  sufficient here; unlike `orchestration.md`'s genuinely non-mechanical residual, **this one IS
  mechanically checkable**, so declining to check it would be choosing prose over code — the precise
  failure this whole spec exists to correct.
- **Honest residual that remains** (state it in the DESIGN, do not design it away): the test itself
  can be edited. Nothing defends the validator's own source mechanically. The guard raises the cost
  and the visibility of switching a protection off; it does not make it impossible.
- **Provenance:** operator ruling 2026-08-03 · `orchestration.md`'s honest-residual precedent.

## Tree status — ALL BRANCHES CLOSED

| # | branch | resolution |
|---|---|---|
| B1 | instance vs class | UPF-1 — folder self-policing |
| B2 | which files | UPF-2 — all eight, exempt ships empty |
| B3 | which layers | UPF-3 — all three layers, no exemption qualifies |
| B4 | clause-selection standard + owner | UPF-5 — dispatched, against the documented standard |
| B5 | `board.md` truncation | UPF-4 — pin the MUST, not the loophole |
| B6 | stale 13/12 counts | UPF-6 — corrected in this change → 23/22 |
| B7 | green / migration | UPF-7 — proven by running the gate |
| B8 | exempt-list escape hatch | UPF-8 — contents pinned by a test |
| B9 | authoring roles | UPF-5 — DESIGN + PLAN dispatched, conductor gates |

## Convergence pass 1 — HOLD, and it was right

A fresh-context, structurally no-write reviewer returned **HOLD** with 9 findings. Every factual claim
it made was re-verified by the conductor before being acted on (agent output is not evidence). All
checked claims were correct. Corrections below **supersede** the entries they name.

### ⚠️ CORRECTION to UPF-6 — the conductor asserted a fact that was false

UPF-6 claimed `CLAUDE.md` contains *"all 13 protocol contracts"*. **It does not.** Verified:
`Select-String CLAUDE.md -Pattern '13|protocol contract|fingerprint'` → **no match**. The claim was
invented, and it is exactly the unverified-assertion class this repo's gates exist to catch (PD-2).

**The real sites are six, across three files** (verified at `bb8c709`):

| file:line | current text |
|---|---|
| `protocol/prime-directives.md:95` | "Clauses are pinned for all **13** `REQUIRED_PROTOCOL`" |
| `protocol/prime-directives.md:97` | "**31** times (against **1–11** for every other protocol file)" |
| `validate_skills.py:372` | "CLAUSES apply to ALL **13** REQUIRED_PROTOCOL files" |
| `validate_skills.py:375` | "FINGERPRINTS apply to **12** of the 13" |
| `validate_skills.py:376` | "changed **31** times (vs **1-11** …)" |
| `test_validate_prime_directives.py:13, 93, 156` | "all 13 files" · "31 commits vs 1-11" · "all 13 files" |

Both churn figures are **also stale**: measured at `bb8c709`, `config.md` is **32** (not 31) and the
band is **1–12** (not 1–11) because `exec-safety.md` has 12.

**Additionally in scope, and missed by the original UPF-6:** `prime-directives.md:100-104` and
`validate_skills.py:382-386` both carry a paragraph stating *"eight protocol files are not in
`REQUIRED_PROTOCOL` at all … Registering them newly gates them, so that is its own change."* **That
paragraph becomes false the moment this change lands** and must be rewritten to describe the folder
rule — otherwise the change ships a lie inside the contract it is protecting.

### ⚠️ CORRECTION to UPF-4 — the rationale was broken, the decision stands

UPF-4 argued that leaving `(or truncate it)` unpinned "keeps the door open to removing the loophole
cheaply later, **with no fingerprint fight**." **That is wrong.** Under UPF-3 `board.md` gets a
fingerprint, and `protocol_fingerprint` hashes the *whole normalised file*
(`validate_skills.py:402-406`) — the parenthetical is inside the digest. Removing it later costs a
re-approval either way.

**The decision does not change; only its reason does.** Pinning the invariant and not the loophole is
still right, because a pinned clause is the thing a future edit must *preserve verbatim* — pinning the
truncation permission would make the loophole load-bearing. That is the real argument.

**Implementation detail the reviewer forced out, and it is binding:** the two propositions are
physically separated by the parenthetical at `board.md:46-48`, and clause matching is a substring test
after normalisation, which does **not** strip parentheticals. So the pin **must be two short clauses**,
neither spanning the parenthetical:
- `"MUST contain only the current run's events"`
- `"rotates any pre-existing board at run start"`

### UPF-9 — `exec-safety.md` gets clauses but NO fingerprint · LOCKED

- **Decision:** `exec-safety.md` is registered with term presence + pinned clauses, and is **exempt
  from the fingerprint** — the second file to receive the `config.md` treatment.
- **Why (the reviewer's catch, and it was a real gap in UPF-3):** UPF-3 rejected every exemption on
  churn alone and never applied the *structural* half of the criterion. `exec-safety.md:45` is headed
  **"Sink registry (verify-before-add — keep in sync with the code)"** and `:48` requires that every
  new execution site **"must be added here"**. It is a list that grows with the codebase — structurally
  the same shape as `config.md`, and the most-edited of the eight at 12 commits. Fingerprinting it
  would make every new subprocess call site in `tools/` cost a manual re-approval, which is precisely
  the blind-re-approval training the `config.md` exemption exists to prevent.
- **The safety guarantee is NOT weakened:** its rules stay clause-pinned, so "structured-argv-only"
  cannot be inverted or deleted. Only the whole-file digest — the layer that fires on legitimate
  registry growth — is skipped.
- **Consequence:** final state is **23 registered / 21 fingerprinted**, with two declared fingerprint
  exemptions (`config.md`, `exec-safety.md`). *(This supersedes UPF-6's "23/22".)*
- **Provenance:** `exec-safety.md:45-48` · `validate_skills.py:375-380` · operator ruling 2026-08-03.

### UPF-10 — The term lists are dispatched too, against a stated bar · LOCKED

- **Decision:** UPF-5 covered pinned *clauses* but left `REQUIRED_PROTOCOL`'s **keyword lists** for the
  eight with no owner and no standard — the reviewer named this the single most likely place two
  builders diverge, and it was correct. Same dispatched author, same conductor gate, with an explicit
  bar: **each term must be a word whose deletion would remove a capability the file defines** (the
  existing lists run 2–11 entries; `validate_skills.py:302-336` are the worked examples).

### UPF-11 — The folder scan is specified verbatim · LOCKED

- **Decision:** `sorted(PROTOCOL_DIR.glob("*.md"))` — **sorted**, non-recursive, `.md` only. A
  `protocol/` directory containing **zero** files is an **ERROR**, never a vacuous pass. Findings are
  `Finding("ERROR", …)`; a warning would not gate, which would defeat the purpose.
- **Why sorted is not optional:** `docs/DETERMINISM-DOCTRINE.md:25-26` law 2 — *"Sorted at every
  filesystem boundary. No unsorted `rglob`/`iterdir`/`listdir`/`glob` result may drive artifact
  content."* The original UPF-1 cited law 1 (the git-helper law), which is the wrong law for a
  directory scan.
- **Why empty-is-an-error:** `validate_skills.py:727-734` already refuses to call "0 skills discovered"
  a green validator (D136 / D33), and `test_validate_prime_directives.py:246-251` monkeypatches an
  empty `PROTOCOL_DIR` and requires an ERROR. A naive scan would pass vacuously and contradict both.

### UPF-12 — UPF-8's test is widened to close two cheaper escapes · LOCKED

- **Decision:** the reviewer found the guard incomplete. Beyond pinning `PROTOCOL_EXEMPT`'s contents,
  the test must also assert **(a)** every registered file has a **non-empty** clause list, and
  **(b)** the fingerprint set equals `REQUIRED_PROTOCOL` minus the declared exemptions.
- **The escapes this closes:** `test_validate_prime_directives.py:85-86` asserts key presence only via
  a set difference — so setting `"board.md": []` passes the test, parametrises to zero cases, and turns
  the check green. Symmetrically, deleting a line from `PROTOCOL_FINGERPRINTS` is a silent green
  because `test_every_fingerprint_matches_its_file` parametrises over the dict itself.
- **Honest residual, unchanged:** the tests can themselves be edited. Nothing defends the validator's
  own source mechanically. This raises cost and visibility; it does not make tampering impossible.

## Status — CONTRACT FROZEN 2026-08-03

All branches resolved; the HOLD's findings are folded above. **Deliberate process deviation, recorded
rather than hidden:** DESIGN and PLAN are normally separate dispatched artifacts (`KH-T13`). For a
change this size — one new check, eight dictionary entries, two fingerprint exemptions, one widened
test — this ledger **is** the frozen contract and serves as the builder's brief. Operator-directed
2026-08-03 ("make sure you're not overcomplicating this"). The conductor still does not author the
change and still gates it default-FAIL.

## Blocked at close — do not forget

**The grill-close `learn_feed.py` emit is BLOCKED** by `DEF-2`: the emitter silently drops entry bodies
for this exact ledger style (measured: 20 of 29 entries, 19,153 chars on the `session-lifecycle`
ledger). Running the emit at close would publish decision-less pages to a durable store — a PD-2
violation written to the vault. **Do not run it until `DEF-2`'s repo-wide question is settled.**
