# GRILL-LEDGER — session lifecycle (standard tier, 2026-07-26)

> Subject: **KH-T01** (handoff-ready always) + **KH-T14** (project wiki as long-term memory) +
> read-back as the load-bearing half. **KH-B41** (kanban / unified task state) is an explicit input.
> Opened per `.planning/HANDOFF.md` §5 NEXT STEP (operator's stated next move). §3 DECISIONS of that
> handoff are settled and are treated as LOCKED inputs, not re-litigated here.
>
> **Phase-0 grounding (this session, verified by reading the code — not inherited from the handoff):**
> - **No code writes `.planning/HANDOFF.md`.** Every code reference to it is read-only (existence /
>   mtime) or a prose nudge. `adapters/claude/hooks/kata-precompact.py:116-129` commits the board to
>   `refs/kata/trail` (mechanical) then *nudges* the model; `adapters/claude/hooks/kata-gauge-check.py:195-212`
>   emits an `additionalContext` sentence at the 0.70 crossing. Both end in prose.
>   `tools/kata_handoff_break.py` renders the operator-facing **notice**, after a handoff already exists.
> - **The staleness comparator does not exist.** `protocol/handoff.md:53-64` specifies it down to
>   same-second tie-breaking; the only occurrences of "staleness" in code are inside those nudge *strings*.
> - **`kind:` / `trigger:` provenance fields are never read.** No code parses HANDOFF.md frontmatter.
> - **Read-back is dead.** `tools/recall.py` (37 KB) has no `__main__`, no argparse, no `main()`; its
>   sole importer repo-wide is `tools/tests/test_recall.py:42`.
> - **The wiki emitter has ONE hardcoded destination.** `tools/learn_feed.py:118` `_FEED_SUBDIR =
>   "decision-patterns"`. `concepts`/`entities`/`references`/`sources` are not unfed — they are
>   unimplemented. (Sharpens the handoff's "one emitter, one bucket".)
> - **The 269 synthesis pages are mostly OURS.** 256 `kataharness` / 13 `kagami`; newest 2026-07-22
>   (the quota-resilience grill). The write path works and fires on real runs; only the read path is dead.
>   (Corrects the implication that the vault is fed by other projects.)
> - **No per-project wiki home exists.** `Vault/projects/{kata-dojo,kenjiri}` (49 files) are *working
>   repos stored in the vault* — `.planning/`, `.pristine/`, `runs/` — not wiki pages. There is no
>   precedent to reuse; KH-T14's first question is genuinely open.
> - **Phase is derived, never stored.** `tools/kata_dash_model.py:211 _derive_phase(tasks, gate_raw)`
>   computes the ribbon phase from task status + gate *inside an active orchestrated run*. There is no
>   durable phase state and no representation of "between an ingest session and a grill".
> - **The position-carrying surfaces are stale and nothing detects it.** `.planning/STATE.md`
>   frontmatter `last_updated: "2026-07-22T00:00:00.000Z"` — four days and two sessions behind; its
>   CURRENT block still shows the overnight-run review as owed and knows nothing of the MindBridge
>   ingest, the 13 planning docs, T-11, or PR #51. `.kata/RESULT.json` is stamped `2026-07-20` against
>   `baselineSha 0922cf6`.
>
> **Tier note:** `kata.config` carries `tiers: {"kata-grill": "essential"}`; this grill runs at
> **standard** depth per the operator's invocation. Flagged, non-blocking.

---

### SL-1 — the handoff is the WRITER of position, not a reader of it · LOCKED

- **Question:** The operator requires the handoff to be phase-aware and positioned in the overall dev
  process, "informed by project, plan, backlog, etc." Where does that sense of position come from,
  given no durable phase state exists and the candidate source docs are stale?
- **Provenance:** Operator, this session: *"The handoff just needs to be context aware of what phase
  we are in and where in the overall dev process we are. The context that backs it up in project,
  plan, backlog, etc, inform it."* Raised against the Phase-0 measurements above —
  `kata_dash_model.py:211` (phase derived, run-scoped only), `.planning/STATE.md` frontmatter
  (`2026-07-22`, two sessions stale), `.kata/RESULT.json` (`2026-07-20`, `baselineSha 0922cf6`).
- **Options considered:**
  - **A (chosen)** — Handoff derives position from live session facts + git and **writes it down**,
    syncing `STATE.md` as a side effect rather than trusting it as a source.
  - **B** — Build KH-B41's durable task-row state machine first; the handoff becomes a render of it.
    Architecturally cleanest and kills the six-surface problem at the root, but blocks KH-T01 (the
    operator-flagged highest-value item) behind a larger, un-grilled build.
  - **C** — Keep reading the docs but build the missing staleness comparator and extend it to
    `STATE.md` / `RESULT.json`, failing loudly on a stale citation. Cheapest, also closes handoff
    finding #1 — but only makes the rot *visible*; a human still hand-fixes the surfaces.
- **Decision:** **The dependency inverts. The handoff is the authoritative, freshest position surface,
  and writing it is what brings the others current.** Position is derived from live session facts plus
  git (branch / HEAD / master / gate results / changed files / board tail), never read from a doc that
  may be stale. Writing the handoff **writes** phase and arc position, and syncs `STATE.md`'s CURRENT
  block, instead of reading either.
- **Rationale:** This matches observed reality rather than fighting it — the 2026-07-26 handoff is
  accurate and `STATE.md` is two sessions stale, because the handoff was written from the live
  conversation while `STATE.md` was written from nothing. Option B is the better end state but
  inverts the operator's own priority order. Option C detects rot without curing it, and a
  fail-loud on a stale surface at the *auto-compact* crossing has no turn left to fail into.
  Choosing A does not preclude B: making the handoff the single fresh surface is a step toward the
  durable-row store, not a competitor to it.
- **Edges/scenarios:** *(OPEN — to be defined in Phase 1 before this entry is complete)*
  - Two writers of `STATE.md` (an active orchestrated run vs. the handoff write) — arbitration
    under single-writer discipline.
  - What "position" contains when no run is active (this session's exact case: between an ingest
    and a grill, with no board, no frozen plan, PR open).
  - What happens when the handoff's derived position contradicts a non-stale `STATE.md`.
- **Doc-baked:** pending — glossary terms and the `protocol/handoff.md` amendment follow once the
  edges above are defined.

---

### SL-2 — the handoff does NOT point into the wiki · LOCKED

- **Question:** Should the handoff stay lean by pointing into the project wiki (KH-T14) for
  long-lived decisions and rationale, rather than re-narrating them?
- **Provenance:** Proposed by the griller this session as a way to reconcile "ephemeral/transactional"
  (the KH-T14 split, `TASKS-ARCHITECTURE-2026-07-26.md`) with the operator's requirement that the
  handoff be "precise and thorough". Operator response: *"I dont know if this is advisable or not.
  Reassess your recommendation based upon deep understanding and assessment."*
- **Options considered:**
  - **A (chosen)** — The handoff is self-contained and repo-local; the wiki is optional outbound
    enrichment with a different consumer.
  - **B** — The handoff references wiki pages for older decisions/rationale, staying lean.
- **Decision:** **Retracted and rejected.** The handoff never depends on, and never points into, the
  vault. **KH-T01 couples to KH-B41 (durable in-repo task state), NOT to KH-T14.**
- **Rationale:** Three reasons, in weight order. (1) It inverts a deliberate discipline —
  `kata-handoff/SKILL.md:41-43` records that this harness went durable/in-workspace/git *specifically
  as an inversion* of mattpocock's save-to-OS-temp handoff, so handoffs survive as audit artifacts;
  the vault lives outside the repo, outside git, is `engram.learnFeed.dir`-gated, and no-ops when
  unset (BC1, `protocol/recall.md`). Making the harness's most critical artifact depend on an
  optional subsystem is exactly the failure that inversion prevents. (2) The pointer would point at
  something unreadable — `recall.py` has no caller, so the reference would precede the reader; that
  is the same described-not-enforced disease this session's thesis names. (3) Every pointer is a
  promise the successor must redeem, and the handoff's value is that reading ONE file gets you
  running; `HANDOFF.md` §4 already lists 13 supporting docs and flags that as KH-B41 worsening.
- **Edges/scenarios:**
  - **Vault absent / `engram.learnFeed.dir` unset** ⇒ handoff quality is byte-unaffected. This is the
    binding test of the decision.
  - **Successor on a different machine** ⇒ the repo clone alone is sufficient to re-anchor.
  - **Wiki read-back** remains in scope for KH-T14, but its consumer is **the grill**
    (`protocol/recall.md` §6 — the `kata-initiate` Phase-2 mirror), not the handoff. The two
    "read-backs" the handoff §5 bundled are distinct problems with distinct consumers; conflating
    them was a griller error, corrected here.
- **Doc-baked:** glossary — pending (`handoff` vs `project wiki` boundary is already normative in
  `protocol/handoff.md:41-43`; this entry adds the *dependency-direction* rule).

---

### SL-3 — required structure is a FLOOR plus DEPTH, promoted from observed practice · LOCKED

- **Question:** What is the enforced section contract for a handoff? `protocol/handoff.md:8-16`
  mandates 7 sections; the handoff that demonstrably worked used 8 different ones.
- **Provenance:** Operator requirement, this session: *"handoff needs to be precise and thorough …
  It should be somewhat deterministic in its structure."* Measured against the schema/practice gap:
  the 2026-07-26 `HANDOFF.md` **added** §0 ground-truth-with-expected-values, §3 settled-decisions,
  and §7 things-I-got-wrong — none required by the schema — and **dropped** the schema's required
  "suggested next skills". Those three additions are what made it effective in live use this
  session: §0 permitted one-batch verification, §3 prevented re-litigation, §7 prevented the
  successor inheriting four false beliefs (all four were caught by adversarial review, not by the
  author). **The schema is behind the practice and has no way to know it.**
- **Options considered:**
  - **A (chosen)** — Promote observed practice into the schema AND split each section into a
    mechanical **FLOOR** (code-writable from git alone) and a **DEPTH** half (model-authored).
  - **B** — One flat mandatory list, all sections model-authored. Simpler and easier to review, but
    nothing is writable without a model turn, so the auto-compact crossing still yields nothing.
  - **C** — Keep the 7-section schema, add only a position block. BC-perfect and cheapest, but leaves
    the three sections that made today's handoff work permanently optional.
- **Decision:** **Two-part contract, both halves enforced present.**
  - **FLOOR — written by code from git/repo state, unconditionally, no model required:**
    `§0 ground truth` (branch / HEAD / master / gate results **with the verify commands and their
    expected values**), `§P position` (phase · arc · open PRs · board tail — per SL-1, derived and
    written, never read from a stale doc), `§S what shipped` (commits + paths, derived),
    `§R redaction` (scan result).
  - **DEPTH — authored by the model, checked non-hollow:** `§1 what this session did`,
    `§2 findings that reorder the queue`, `§3 decisions settled · do not re-litigate`,
    `§5 next step, in order`, `§6 owed to the operator`, `§7 what I got wrong`.
- **Rationale:** The floor/depth split is the only shape that survives the crossing that has never
  worked. At host auto-compact there may be no model turn at all; a flat contract (B) yields nothing,
  while the floor still yields a genuinely usable artifact — the position, the SHAs, and the verify
  commands are exactly the part a successor needs first, and they are all mechanically derivable.
  Depth remains where judgment genuinely lives. Option C was rejected because BC is not the binding
  constraint here: the schema's own required section ("suggested next skills") is one the best
  handoff in the repo silently omitted with no consequence, which is evidence the schema is not
  currently load-bearing on anything.
- **Edges/scenarios:** *(partially OPEN — see SL-4)*
  - **No model turn at all** (auto-compact) ⇒ FLOOR exists, DEPTH absent-and-marked-absent. An
    honestly-empty depth section is a *known* state, not a silent one (PD-2).
  - **`§R redaction` is only mechanically a SCAN**, never a judgment — the floor writes the scan
    result; a positive hit escalates rather than auto-redacting. *(To confirm in Phase 1.)*
  - **`§7 what I got wrong` with genuinely nothing to report** must be an explicit assertion, never
    an empty heading — otherwise the section is indistinguishable from a skipped one.
  - Hollow-depth detection is the load-bearing open branch → **SL-4**.
- **Doc-baked:** `protocol/handoff.md` §Required-sections rewrite + `kata-handoff` bump-on-modify —
  pending SL-4.

---

### SL-4 — hollowness is caught by citation and shape checks, never by vocabulary · LOCKED

- **Question:** SL-3's floor/depth contract rests on "a stubbed depth section is detectable." How is
  that made real without repeating the KH-T02 failure?
- **Provenance:** `OPERATOR-RULINGS-2026-07-26.md` ruling 12 / KH-T02 — the Prime Directives check
  greps **seven substrings**, so a reviewer rewrote both directives to say the *opposite*
  (*"stub it and move on, present-but-dead counts as built"*), kept the words, and **the validator
  passed green**. Operator: *"It is prime directive. It shouldn't have a workaround."* A naive
  non-empty or keyword check on a handoff section is the identical defect — `N/A` satisfies it.
- **Options considered:**
  - **A (chosen)** — Per-section **shape + citation** requirements, mechanically checked.
  - **B** — A fresh-context no-write evaluator reads the handoff cold and returns PASS/NEEDS_WORK.
    Catches fluent-but-empty prose no shape check can — but costs a model call, and the auto-compact
    crossing has no budget for one, so it cannot cover the crossing that has never worked.
  - **C** — Both, tiered by crossing: mechanical everywhere, evaluator where there is budget.
- **Decision:** **Mechanical checks over evidence SHAPE and resolvable CITATIONS — never over
  vocabulary.** Per section: `§0` requires ≥N lines of the form `<command> -> <expected value>`;
  every `§2` finding must cite a `path` / SHA / `file:line` **that resolves in the repo**; `§3` must
  be a table with ≥1 row; `§5` must be an ordered list with ≥1 item; `§7` must name a concrete
  correction **or** explicitly assert none *with a reason* — a bare empty section fails.
- **Rationale:** The KH-T02 defect is that the checked property (word presence) is orthogonal to the
  property that matters (the document says the right thing). Citation-resolution is not orthogonal:
  a fabricated `file:line` **fails the check mechanically**, and a *real* citation that does not
  support the claim is a PD-2 violation that leaves durable evidence for the reviewer — a loophole
  becomes an audit trail. `N/A` fails every one of these rules rather than satisfying them.
  Option B remains available as a later upgrade on the budgeted paths (see SL-3 edges) but is not
  load-bearing; the operator's recorded tiebreaker (*"take the proof"*) is satisfied by the
  mechanical half being the one that always runs.
- **Edges/scenarios:**
  - **Fabricated citation** ⇒ the resolve step fails ⇒ gate fails. Not a judgment call.
  - **Real citation, wrong claim** ⇒ passes the mechanical check; caught downstream by review, and
    the citation is the evidence. Accepted residual, recorded honestly rather than papered over.
  - **Genuinely nothing to report in §7** ⇒ explicit assertion + reason passes; a bare heading fails.
  - **`N`, the §0 minimum line count** ⇒ a magnitude choice, and a known drift-magnet
    (LESSONS-LEARNED L10). To be pinned in Phase 1, not left to the executor.
- **Doc-baked:** pending — the check belongs alongside `validate_skills.py`'s family; exact home
  deferred to the KH-T03 reproducibility-checker placement question (validator vs review vs gate).

---

### SL-5 — the FLOOR needs no trigger; "handoff-ready always" is a claim about DEPTH only · LOCKED

- **Question:** When and how often is the floor refreshed, so the handoff is "ready at every moment"?
- **Provenance:** KH-T01's refined target (`TASKS-ARCHITECTURE-2026-07-26.md`): *"handoff-ready at
  every moment, so the boundary costs nothing whoever triggers it."* Re-derived after SL-3.
- **Decision:** **The floor is computed on demand and is never pre-written, so it cannot go stale.**
  Every floor input (branch, HEAD, master SHA, gate results, board tail, open PRs, changed paths) is
  a pure function of repo state at the instant of the write. There is no refresh schedule, no
  pre-write, no staleness window, and therefore no trigger to design. **"Handoff-ready always"
  reduces entirely to keeping DEPTH current** — the half only a model can author, and precisely the
  half an unannounced compaction destroys.
- **Rationale:** Applying the anti-cathedral rule: the grill was about to design a refresh cadence
  (per-task-boundary / per-commit / per-crossing) for state that is already derivable at zero cost.
  Each candidate also carried a real defect — task/wave boundaries are **run-scoped** and would never
  fire in a session like this one (an architecture/grill session with no waves), and a per-commit
  hook writing `HANDOFF.md` would leave the tree dirty after every commit, breaking the
  `git status --porcelain -> empty` ground-truth tripwire the operator verifies against (D1).
  Removing the trigger removes both defects and a whole subsystem.
- **Edges/scenarios:**
  - **Uncommitted working-tree changes at write time** ⇒ the floor must state them, not silently
    describe HEAD as if it were the tree.
  - **Gate results are NOT pure git state** — they require a gauntlet run (~146 s). The floor either
    cites the last recorded run *with its SHA and staleness*, or re-runs. **Open → Phase 1.**
  - **No board present** (non-run session, this one) ⇒ the board-tail field is honestly absent.
- **Doc-baked:** pending.

---

### SL-6 — depth accrues incrementally; the board is NOT its store · LOCKED

- **Question:** Given SL-5, how does DEPTH stay current so a crossing costs nothing?
- **Provenance:** SL-5's re-derivation. Verified against `protocol/board.md` before claiming reuse.
- **Decision (store half only — the cadence question is SL-7):** Depth accrues into its **own
  durable append-only journal**, **not** `.kata/board.md`.
- **Rationale:** The board *looked* like the natural home — it is already append-only, durable, and
  carries `DECISION` / `NOTE` / `ESCALATE` types. It is not: `protocol/board.md:44-50` requires the
  board contain **only the current run's events** and rotates it at run start, because
  `concurrency.json` is computed over the whole file; session narrative appended there would
  contaminate the `maxInFlight` / `overlaps` evidence and falsify the `worker-clock` provenance
  claim. Reuse rejected on inspection rather than asserted — `protocol/reuse-claims.md`.
- **Edges/scenarios:** *(OPEN — SL-7)* cadence, format, who appends, and whether the journal is
  git-tracked or `.kata/`-local.
- **Doc-baked:** pending.

---

### SL-7 — depth is COLLECTED from artifacts that already accrue; only two sections need a journal · LOCKED

- **Question:** How does DEPTH stay current without relying on the model remembering to append —
  which would be prose enforcement again, the exact disease this grill exists to cure?
- **Provenance:** SL-5/SL-6. Grounded by inspecting each candidate source rather than assuming
  (`protocol/reuse-claims.md`; the recurring over-claim this project's red-team keeps catching).
- **Decision:** **Collect, don't re-author.** Six of the eight depth inputs already have durable,
  machine-written owners and are parsed at handoff time; a **thin append-only journal** is added
  **only** for the two with no existing owner.
  - **Collected:** `GRILL-LEDGER.md` + `DECISIONS.md` → `§3 decisions settled` ·
    `DEFERRED.md` + `.kata/escalations/*.json` → `§6 owed` · `git log` + board `DECISION` lines →
    `§1 what this session did`.
  - **Journaled (no existing owner):** `§2 findings that reorder the queue` · `§7 what I got wrong`.
- **Rationale:** The collected sections are current **by construction** — their sources are written
  by machinery (`kata-defer`, `escalation.write_escalation`, the grill's own mandatory ledger
  checkpoint, git) rather than by the model's memory. That removes the prose-enforcement dependency
  for six sections and leaves it for two, where the content genuinely originates in the model's
  judgment and nothing mechanical could produce it. It also avoids creating a seventh planning
  surface (the KH-B41 problem), which is why a single all-encompassing new journal was rejected.
- **🔑 Verified reuse — the collector's parser layer already exists, unused.** `tools/recall.py`
  ships `parse_lessons` / `parse_decisions` / `parse_intent` / `parse_understand` /
  `parse_synthesis_pages` (l.619-777), `_guard_path` (CWE-23), and tolerant I/O (absent ⇒ `[]`,
  never raises) — **37 KB, tested, with zero production callers.** `_parse_bullets` (l.602) already
  handles `DECISIONS.md`'s exact `- **D{n} — <title>.**` grammar, which is load-bearing: that file
  has **one heading in 2683 lines** and defeats any naive heading parser. Wiring the collector to
  these parsers gives `recall.py` its **first production caller**, closing the measured read-back
  gap as a structural consequence rather than as separate work.
- **Honest limits of that reuse (NOT over-claimed):**
  - `recall.py` covers **5** sources. It does **not** parse `DEFERRED.md`, `.kata/escalations/*.json`,
    `GRILL-LEDGER.md`, or `git log` — those need **new** parsers.
  - The collector reuses recall's **parse layer, NOT its selection layer.** `select_records` gates on
    query-token overlap for the grill's relevance question; the handoff wants *everything since the
    last handoff*, recency-scoped. Calling `recall_from_paths` would be the wrong contract.
  - Use stays within `protocol/recall.md` §5's **read-only invariant** — the collector reads and
    renders; it never decides, gates, or writes back through recall.
- **Edges/scenarios:**
  - **Three different anchor grammars** across the collected sources — `### D{n} … · LOCKED`
    (ledger), `## DEF-{n} … · OPEN (date)` (deferred), `- **D{n} — …**` (decisions). The collector
    needs three parsers **or** the grammars get unified. **Open → Phase 1** (unification would touch
    `learn_feed._ANCHOR_RE`, which requires a *heading* anchor and therefore already cannot emit
    `DECISIONS.md` bullets — a latent inconsistency worth resolving deliberately, not incidentally).
  - **Absent source** (no board, no escalations, no ledger — this very session) ⇒ section renders as
    honestly empty, never fabricated. recall's tolerant-I/O posture is the precedent.
  - **Journal location** — git-tracked vs `.kata/`-local. **Open → Phase 1.** Constraint from SL-5:
    a git-tracked journal written mid-session dirties the tree and breaks the
    `git status --porcelain -> empty` tripwire.
- **Doc-baked:** pending — `protocol/handoff.md` gains a "collected vs journaled" section-provenance
  table; `protocol/recall.md` gains the handoff collector as a named second consumer.

---

### SL-8 — a fresh handoff replaces orientation; kata-orient is the fallback · LOCKED

- **Question:** Operator-raised in KH-T01: *"Do we need orientation if it is automated, or is handoff
  good enough and orientation a waste of tokens?"* — with the recorded rider *"Measure both, don't
  argue it."*
- **Provenance:** `OPERATOR-RULINGS-2026-07-26.md` KH-T01. Live evidence from **this session**: the
  re-entry prompt came from `kata_handoff_break._REENTRY_TEMPLATE` (l.37-48) — ~10 lines, ~120
  tokens — and was sufficient: state verified in one batch, no settled decision reopened, work
  started at §5. The reason it sufficed is structural: the *"how to behave"* half of orientation is
  already delivered at launch by `CLAUDE.md` → `protocol/prime-directives.md` → `AGENTS.md`,
  independent of any handoff. What `kata-orient`'s 3-tier rebuild adds beyond that is a **context
  rollup** — which is what the handoff's read-in order already is.
- **Decision:** **A present, non-stale handoff IS the orientation on the resume path**, delivered via
  the short re-entry block. The full `kata-orient` 3-tier rebuild fires **only** when no handoff
  exists, or when the handoff is demoted stale. The operator's measurement runs as a **confirming
  instrument** on subsequent resumes, not as a gate blocking the build.
- **Rationale:** This formalizes behavior the code **already implements** —
  `adapters/claude/hooks/kata-sessionstart.py:63-75` branches on handoff presence today, pointing at
  the handoff when present and at a "kata-orient full 3-tier rebuild" when absent. The design change
  is to make that the *stated rule* and to base the branch on **fresh**, not merely *present*.
  Always-load-both was rejected as duplicating what the platform instruction file already injects.
- **⚠️ Dependency this creates:** the branch condition is *present **and fresh***, so the **staleness
  comparator becomes load-bearing.** `protocol/handoff.md:53-64` specifies it completely (newest board
  `DONE`/`DECISION` line vs the HANDOFF.md git commit timestamp, strict `>`, same-second ties favor
  the handoff) and **no code implements it** (Phase-0 finding). It is no longer optional polish —
  this decision cannot ship without it. **→ SL-9 must define what it compares**, since SL-1 inverted
  the handoff's role from reader to writer and the original comparator was specified for a reader.
- **Edges/scenarios:**
  - **Handoff present but stale** ⇒ full `kata-orient` rebuild becomes authoritative (existing rule).
  - **Handoff absent** ⇒ full rebuild; already the shipped behavior.
  - **No board present** (non-run session) ⇒ the comparator has no board lines to compare against;
    freshness must fall back to another signal. **Open → SL-9.**
- **Doc-baked:** `protocol/orientation.md` + `kata-orient` (bump-on-modify) + `protocol/handoff.md`
  — pending SL-9.

---

### SL-9 — the worker level needs a READER, not a new artifact; terminology stands · LOCKED

- **Question:** KH-T01 requires *"a worker that ends must leave a durable handoff"*, but
  `protocol/handoff.md:41-43` is **normative** that a handoff is the session-boundary artifact ONLY
  and that *"dispatch briefs, worker final reports, and escalation payloads are agent-exchange
  artifacts, never 'handoffs'."* Direct contradiction between an operator ruling and a frozen rule.
- **Provenance:** `OPERATOR-RULINGS-2026-07-26.md` KH-T01 §Required-scope level 1 vs
  `protocol/handoff.md` CA-L21(1). Surfaced per the grill method's cross-reference rule. Verified
  against code before posing: `tools/run_result.py:52-95 build_result` emits a durable
  machine-checkable gate record carrying `baselineSha` / `resultSha` / `utc`; workers additionally
  self-stamp board `CLAIM`/`DONE` with their own process clock (`protocol/board.md:13-14,21`),
  commit in their worktrees, and write `.kata/escalations/*.json` via
  `escalation.write_escalation`.
- **Decision:** **The normative terminology stands** — "handoff" continues to mean the
  session-boundary artifact only. The operator's requirement is satisfied without a new artifact and
  without a vocabulary change: **workers already leave durable state; what is missing is a reader.**
  Build (a) composition of those existing records into something a successor can actually read, and
  (b) the freshness check on them.
- **Rationale:** The requirement's intent — *nothing is lost when a worker ends* — is already met at
  the write side, four times over. What is absent is any consumer. Widening "handoff" to three
  levels was rejected because it dissolves the deliberate split between machine-coordination state
  (`.kata/`, rotated per run, feeds `concurrency.json`) and durable Obsidian docs (`.planning/`,
  git-committed) that `STANDARDS §5` rests on. Declaring the level already-done was rejected because
  *durable ≠ usable*: the records exist and nothing reads them, which is this session's thesis.
- **Edges/scenarios:**
  - **Free T-04 fix.** `RESULT.json` carries `resultSha`, so the floor can cite the last gate run
    **and** verify that SHA is an ancestor of HEAD. That is exactly handoff finding #1 (a stale
    `RESULT.json` fully creditable by the gate — ours names a SHA 37 commits behind). It falls out
    of this composition rather than needing a separate build. **Resolves SL-5's open gate-freshness
    edge.**
  - **Worker records are run-scoped and rotate** (`protocol/board.md:44-50`); the composer must read
    them before rotation or from the archived boards, never assume the live board spans the session.
- **Doc-baked:** `protocol/handoff.md` CA-L21(1) gains a clarifying note that the worker level is
  served by composition, not by a second handoff schema — additive, no rule change.

---

### SL-10 — staleness generalizes from board-only to any collected depth source · LOCKED · supersedes CA-L19

- **Question:** SL-8 makes the staleness comparator load-bearing. `protocol/handoff.md:53-64`
  specifies it completely and no code implements it — but it assumes a board exists.
- **Provenance:** SL-8's dependency. Counter-evidence from this session: **no active run, therefore
  no live board**, while five commits landed during the session. Under the specified rule nothing is
  ever newer, so the handoff would stay trusted indefinitely — blind in exactly the session shape
  where a manual handoff matters most.
- **Decision:** **Freshness = no collected depth source has an entry newer than the depth write.**
  Sources are SL-7's set: `git log` · `DECISIONS.md` · `DEFERRED.md` · `.kata/escalations/*.json` ·
  `GRILL-LEDGER.md` · board `DONE`/`DECISION`. Any newer entry ⇒ the handoff is demoted from
  sole-anchor to context-input and the `kata-orient` 3-tier rebuild becomes authoritative.
- **Rationale:** Strictly stronger than the board-only rule and degrades correctly — with no board,
  the other five sources still answer. It reuses the collector SL-7 already requires, so the
  comparator costs almost nothing additional. Git-only was rejected as demoting on commits that
  changed nothing reportable (a docs typo would force an unnecessary full rebuild); the collector
  set is the right granularity because those sources are, by construction, the things worth
  reporting. **Compare against the DEPTH write, not the file mtime** — SL-5 established the floor is
  computed on demand and therefore cannot be stale, so only depth can be.
- **Supersede lineage (C5 — supersede, never rewrite):** CA-L19 is **superseded, not deleted**. Its
  posture is **preserved verbatim** in the generalized rule: strict `>`, same-second ties favour the
  handoff, N=1 semantics, **no tunable**, trail-ref independent. Its **clock-skew note carries
  forward and widens** — the comparator now crosses more clock domains (worker process clocks on
  board lines, git committer clocks, filesystem mtimes on escalation JSON); the strict-`>`
  plus ties-favour-the-handoff convention remains the skew posture, and multi-machine runs revisit
  it with the board's own recorded revisit item.
- **Edges/scenarios:**
  - **No board** ⇒ five sources still answer. The failure this decision exists to fix.
  - **Source absent entirely** ⇒ contributes nothing; never an error (recall's tolerant-I/O posture).
  - **Same-second tie** ⇒ favours the handoff, unchanged from CA-L19.
  - **Clock domains disagree** ⇒ accepted single-host residual, recorded above rather than hidden.
- **Doc-baked:** `protocol/handoff.md` §Staleness-rule superseded-in-place with lineage; comparator
  ships as code — the single unimplemented rule this grill converts from prose to enforcement.

---

### SL-11 — the project wiki gets a per-project subdirectory plus a rollup · LOCKED

- **Question:** KH-T14 decision 1 — where does a project wiki live in the Vault?
- **Provenance:** `TASKS-ARCHITECTURE-2026-07-26.md` KH-T14. Measured: all 269 pages land flat in
  `second-brain/wiki/pages/synthesis/decision-patterns/` with the project encoded in the **filename**
  (`kataharness--quota-resilience--g-9.md`), because `tools/learn_feed.py:118` hardcodes
  `_FEED_SUBDIR = "decision-patterns"`. No rollup, no index. **Verified there is no home to reuse:**
  `Vault/projects/{kata-dojo,kenjiri}` (49 files) are *working repos stored in the vault*
  (`.planning/`, `.pristine/`, `runs/`), not wiki pages.
- **Decision:** **`synthesis/decision-patterns/<project>/` plus a per-project rollup `INDEX.md`.**
  `_FEED_SUBDIR` becomes a function of project rather than a constant.
- **Rationale:** Gives each project a real home and an entry point with a small, contained emitter
  change, without touching the vault's area structure and without overloading `projects/`, whose
  existing meaning is "working repo". Staying flat was rejected because one directory past 269 files
  keeps accreting and navigates poorly; a top-level area was rejected because it collides with that
  existing meaning **and** moves pages out from under the `second-brain` area that the promotion
  machinery (`research-promote`, `kiban-update`) targets.
- **Edges/scenarios:**
  - **Existing 269 pages** — migration is optional; new emissions land correctly either way. A
    migration is a rename-only operation, deterministic and reversible.
  - **Project slug** must be the same slug `learn_feed._slug` already produces, or old and new pages
    diverge into two homes for one project.
  - **Rollup regeneration** must be idempotent — same inputs, same bytes (Determinism Doctrine).
- **Doc-baked:** `protocol/engram.md` + `tools/learn_feed.py` (module constant → resolver).

---

### SL-12 — a temporal entry is a SUBJECT page keyed on the artifact changed, promoted at 2+ initiatives · LOCKED

- **Question:** KH-T14 decision 2 — what triggers a temporal entry and what does it contain?
- **Provenance:** `TASKS-ARCHITECTURE-2026-07-26.md` KH-T14 ("Per run? Per phase? Per decision
  cluster?"). **Operator reframing, this session (the decisive input):** *"Temporal should be aligned
  under basically a header with the same subject of entries that happen on a repeated basis … it
  should effectively be identified when something is changed, or repeated by nature. Things that
  change via iterations or via time."*
- **Decision:** A temporal entry is **not** an event log. It is a **subject page with a timeline**:
  the header is the subject, and entries accrue under it each time that subject is revisited.
  - **Subject identity = the durable artifact a decision changes**, taken from the ledger's
    `Doc-baked` field and corroborated by that file's git history. Mechanical; no semantic
    clustering, no embeddings (consistent with `protocol/recall.md` §2's hard stance).
  - **Promotion measure = the artifact is touched by decisions from ≥2 DISTINCT initiatives.**
- **Rationale:** The temporal dimension that matters is *how our thinking about a thing changed
  across iterations*, not when events occurred. Keying on the changed artifact makes "same subject"
  undeniable rather than inferred. The ≥2-distinct-initiatives bar is what encodes "repeated by
  nature": one spec revising its own document twice in an afternoon is iteration *within* a single
  act of work; the same artifact revisited months later by unrelated work is genuine recurrence.
  Token-overlap clustering was rejected because it requires a tuned threshold — a magnitude constant,
  and LESSONS-LEARNED **L10** names those as a drift magnet — and can group things that merely sound
  alike. Per-run and per-session triggers were both rejected as the *identity* rule (a session or run
  is a container, not a subject), though session close remains the natural *emit* moment.
- **Worked example from live data (the motivating case):** `protocol/handoff.md` — `CA-L21` (`kind:`
  provenance) and `CA-L19` (staleness) from **context-autonomy**, `G-1` (additive `trigger:` field)
  from **quota-resilience**, and `SL-1`–`SL-10` from **session-lifecycle**. Three distinct
  initiatives across two months ⇒ qualifies. Today those are unrelated atomic pages.
- **Edges/scenarios:**
  - **A decision touching several artifacts** ⇒ contributes an entry to each subject's timeline.
  - **A decision with no `Doc-baked` target** ⇒ contributes to no subject page; must not fabricate
    one. (This grill's SL-5 is such an entry — a de-scoping decision that changes nothing.)
  - **An artifact renamed** ⇒ subject identity must follow the rename (git `--follow`), or one
    subject silently forks into two.
  - **A subject that crosses files** (e.g. handoff spans `protocol/handoff.md` + `kata-handoff` +
    `kata-selfhandoff`) ⇒ accepted limitation: three subject pages, cross-linked, not merged. The
    alternative is the threshold-tuning this decision rejected. **Recorded honestly as a residual.**
- **Doc-baked:** `protocol/engram.md` + `tools/learn_feed.py`.

---

### SL-13 — four open edges resolved from constraint and precedent, not operator attention · LOCKED

Per the grill method's Phase-0.3 rule (*resolve from docs/code whatever is resolvable; do not spend
the operator's attention on it*), these SL-3/SL-7 edges are closed here with their grounds:

1. **`§0` minimum line count `N` — pinned to the five verify commands, not a free constant.**
   `kata_handoff_break._REENTRY_TEMPLATE` (l.37-48) already encodes exactly five commands with their
   expected values (`git status --porcelain` · `git stash list` · `origin/master` SHA · `HEAD`
   branch · the gauntlet), and that set was **sufficient in live use this session**. `N` is defined
   as *the template's command count*, so the constant has a single source and cannot drift
   independently — this deliberately avoids inventing a magnitude (L10).
2. **Depth-journal location — `.kata/`, not git-tracked.** **Verified:** `.gitignore:9` ignores
   `.kata/` and `git ls-files .kata` returns empty, so mid-session appends cannot dirty the tree or
   trip the `git status --porcelain -> empty` ground-truth check (SL-5's constraint). ⚠️ The journal
   must live **outside the board's rotation set** — `protocol/board.md:44-50` rotates
   `.kata/board.md` at run start, and a rotated journal would silently lose session narrative.
3. **Three anchor grammars — write three parsers; do NOT unify.** `### D{n} … · LOCKED` (ledger),
   `## DEF-{n} … · OPEN (date)` (deferred), `- **D{n} — …**` (decisions). Unification would have to
   rewrite `DECISIONS.md` (2683 lines, **one** heading) and touch `learn_feed._ANCHOR_RE`, which
   requires a *heading* anchor — a large, risky edit for cosmetic gain. `recall._parse_bullets`
   (l.602) already handles the third grammar, so only two parsers are genuinely new.
   *(Recorded latent inconsistency, deliberately not fixed here: `learn_feed`'s heading-anchor
   requirement means `DECISIONS.md` bullets can never emit to the second brain. Out of scope; named
   so it is not rediscovered as a surprise.)*
4. **Two writers of `STATE.md` — no conflict; the existing single-writer rule already decides it.**
   The conductor is sole main-tree git writer (`TASKS-ARCHITECTURE-2026-07-26.md` KH-T13 cost 4). The
   handoff's `STATE.md` sync (SL-1) therefore runs through that same writer; a dispatched agent never
   writes it. No new arbitration mechanism is required — this is a case where the anti-cathedral rule
   says stop.

---

### SL-14 — wiki scope stays inside synthesis; the other four kinds are not ours · LOCKED

- **Question:** KH-T14 — do we build emitters for `concepts` / `entities` / `references` / `sources`,
  the four page kinds recorded as having "never received a single page"?
- **Provenance:** `TASKS-ARCHITECTURE-2026-07-26.md` KH-T14 §"the measured state of our synthesis",
  which presents those four zeros as **our** gap. **Verified otherwise:** `kata.config`
  `engram.learnFeed.dir` = `…\wiki\pages\synthesis`, and the four kinds are **siblings** of
  `synthesis` — outside the configured feed dir entirely. `protocol/engram.md` §"Wiki-synthesis
  output schema" contracts **only** for synthesis pages (the Karpathy raw↔synthesis split). The four
  are the **vault's** taxonomy, fed by the vault-side skills the same document lists as unfed
  (`wiki-ingest`, `research-init`, `research-promote`).
- **Decision:** **Our territory is `wiki/pages/synthesis/**` only** — decision pages, SL-11 rollups,
  SL-12 subject pages. The documented framing is **corrected**: those four zeros are not a
  KataHarness gap, and the vault-side owner is named. Nothing is dismissed; the gap is reassigned,
  not erased.
- **Rationale:** Applies the recorded tiebreaker (*"take the proof"*) against the recorded ruling
  (*"worth building is ALL OF IT"*) where they genuinely conflict: building four emitters that write
  into another system's taxonomy, outside our configured feed dir, with no consumer, is capability
  without proof. Correcting a false claim is PD-2 work and costs nothing.
- **Edges/scenarios:**
  - **C5 derived-view carve-out is binding on SL-11 + SL-12.** `protocol/engram.md` C5 (D151/SB-L3):
    loop-emitted pages (`produced-by: loop`) are regenerable projections and may be overwritten
    idempotently; the emitter **refuses, fail-closed**, to touch any non-loop page
    (`produced-by: wiki | agent`, or missing/unparseable frontmatter). Rollups and subject pages
    **must** carry `produced-by: loop` or they can never be regenerated — and must never clobber a
    hand-curated page of the same name.
  - **Operator later wants the four fed** ⇒ that is a vault-side change plus a `learnFeed.dir` widen;
    this decision does not foreclose it, it assigns it.
- **Doc-baked:** correct `TASKS-ARCHITECTURE-2026-07-26.md` §KH-T14 and
  `SESSION-LIFECYCLE-AND-SYNTHESIS.md` §4 — both currently state the claim this entry corrects.

---

### SL-15 — recall.py gets a CLI; both read-back consumers wire · LOCKED

- **Question:** KH-T14 decision 4 — read-back, the operator's "load-bearing half". How far?
- **Provenance:** `modules/initiation/kata-initiate/SKILL.md:86-115` mandates the RECALL BRIEF
  **"always — cold start *and* loop-back"** and names `tools/recall.py` as the engine. **Verified:
  that engine has no CLI** (no `__main__`, no argparse, no `main`) — so the mandated step has **no
  runnable command**, and a compliant agent would have to author inline Python on every run. That is
  the mechanical reason a mandated step has never executed.
- **Decision:** Add a CLI (`_main`/argparse over the existing `recall_from_paths`) and wire **both**
  consumers: the SL-7 handoff collector imports the parsers directly; `kata-initiate` Phase 1b
  invokes the CLI as a command.
- **Rationale:** The engine, parsers, payload schema, path guard and tests already exist; the entire
  missing piece is an entry point. This is the highest reach-per-line change in the grill — it closes
  read-back on the handoff path *and* the planning path at once. Gating initiation on a produced
  brief was rejected as a hard stop that fires even on a fresh repo with nothing to recall; the
  no-workaround posture is better spent on KH-T02 where the operator directed it.
- **Edges/scenarios:**
  - **Read-only invariant preserved** (`protocol/recall.md` §5) — a CLI surfaces; it never decides,
    writes, or gates. **INTENT-never-written** (§6) is unaffected: the CLI has no INTENT write path.
  - **No vault** ⇒ works unchanged; the feed dir is the optional seventh source, six on-disk
    artifacts remain.
  - **Determinism** — `generated_ts` is the one impure field; the CLI must accept an injected
    timestamp for reproducibility (Doctrine law 7), as `run_result.build_result` already does.
- **Doc-baked:** `tools/recall.py` (+CLI) · `protocol/recall.md` (name the handoff collector as a
  second consumer) · `kata-initiate` Phase 1b (concrete invocation, bump-on-modify).

---

### SL-16 — promotion to personal/professional/work is vault-side; we emit promotion-READY pages · LOCKED

- **Question:** KH-T14 decision 3 — the promotion path to `personal` / `professional` / `work`
  (operator: *"tie it into decision making in the bigger picture"*).
- **Provenance:** `TASKS-ARCHITECTURE-2026-07-26.md` KH-T14 item 3; measured areas — `personal` 14,
  `professional` 10, `work` 4, `second-brain` 280. Resolved here from SL-14's boundary rather than by
  spending operator attention (Phase-0.3 rule).
- **Decision:** **Promotion is a vault-side act** (`research-promote`, `kiban-update` — the machinery
  the operator's own notes list as existing-but-unfed). **Our obligation is to emit
  promotion-READY pages**: every emitted page carries the `protocol/engram.md` page contract in full
  — `produced-by`, `source:`, `date:`, namespaced `tags:`, and crucially **`scope: project |
  universal`**, which is the field a promotion decision keys on (C3 project-scoping: a private
  project's synthesis must not leak into a public run).
- **Rationale:** Consistent with SL-14 — the boundary is the feed dir. Building a promoter would put
  KataHarness in charge of another system's areas. Emitting the metadata that makes promotion
  decidable is the part we own, and it is the part currently unverified.
- **Edges/scenarios:** a page missing `scope:` is **not promotable** and should fail our own emit
  checks rather than land un-promotable; `scope: universal` is the assertion that a page carries no
  project-private content, so it must pass the redaction gate (engram C3, same gate as handoff §7).
- **Doc-baked:** `tools/learn_feed.py` page-contract completeness check.

---

### SL-17 — KH-B41 stays out of this freeze; the design leaves it cheaper, not harder · LOCKED

- **Question:** KH-B41 (kanban / unified task state) was an explicit input to this grill. Does the
  frozen design include any of it?
- **Provenance:** `.planning/HANDOFF.md` §5 names KH-B41 an explicit input;
  `TASKS-ARCHITECTURE-2026-07-26.md` KH-B41 (six planning surfaces, no single view, no state
  machine; steal Hermes's state machine + one-durable-row-per-task + handoff-as-a-row; do **not**
  steal SQLite).
- **Decision:** **Out of scope for this freeze.** No durable row store, no state machine, no
  handoff-as-a-row is built here.
- **Rationale:** The one thing SL-1 genuinely needed from KH-B41 — **arc**, this session's position
  in a sequence — is **already free**: `git log --follow .planning/HANDOFF.md` yields **65 dated,
  captioned commits back to 2026-06-30**, a direct byproduct of CA-L21(4) (*"an over-threshold
  refresh overwrites HANDOFF.md and commits — history lives in git"*). Hermes's
  session-rotation-with-lineage borrowing (KH-T01 §Borrowings) is therefore **already satisfied**,
  and building handoff-as-a-row would be a second copy of existing data — additionally barred by
  CA-L21(6) (*no new artifact formats*). Folding in the full row store is the tradeoff SL-1 already
  rejected: it gates KH-T01, the operator-flagged highest-value item, behind a larger un-grilled
  build.
- **Forward coupling (recorded so the next grill inherits it):** SL-7's collector is precisely the
  **read layer** a durable row store would later feed. When KH-B41 is grilled, rows become a seventh
  collector source (or replace several), and **nothing in this design has to be undone** — the
  handoff still writes position (SL-1), the contract is unchanged (SL-3/SL-4), and the staleness
  comparator (SL-10) simply gains a source.
- **Edges/scenarios:**
  - **Arc across a repo with no handoff history** (fresh target) ⇒ arc is honestly "session 1 of
    this repo", never fabricated.
  - **`git log --follow` across a rename** ⇒ `--follow` is required, not optional; a plain `git log`
    truncates lineage silently at the rename.
- **Doc-baked:** none for KH-B41; the forward coupling above is recorded in this ledger for the
  future grill to consume.

---

### SL-18 — two residual branches closed from existing rules · LOCKED

Found by the Phase-1 convergence self-check against the Phase-0 tree; both resolve from precedent.

1. **`kind:` / `trigger:` stay purely additive and NEVER gate — but the floor now guarantees they
   are written.** Phase-0 measured that no code reads HANDOFF.md frontmatter, so neither field has
   ever gated anything, and `protocol/handoff.md:17-22` is explicit by design: *"absent ⇒ unknown
   kind; never gates"*, the same for `trigger:`. **Decision:** that rule is preserved unchanged (BC
   — a pre-existing handoff without them must keep reading clean). What changes is the **write**
   side: SL-3's floor emits `kind:` and `trigger:` mechanically, so the failure the Phase-0 probe
   found — *no real handoff has ever carried its provenance fields* — is closed by guaranteeing the
   write, **not** by adding a gate. Making them gate would break every one of the 65 historical
   handoffs on read, for no benefit the write guarantee does not already deliver.
2. **`§P position` when no run is active, and the STATE.md contradiction case.** `_derive_phase`
   (`kata_dash_model.py:211`) only yields a ribbon phase inside an active orchestrated run.
   **Decision:** when a run is active, `§P` carries the derived phase; when none is
   (an architecture / grill / review session — the shape of this one), `§P` states **"no active
   run"** explicitly and carries the arc instead: position in the `git log --follow HANDOFF.md`
   lineage, open PRs, and the current branch's relationship to master. An honestly-absent phase is
   never a fabricated one (PD-2). **There is no STATE.md contradiction case to arbitrate** — SL-1
   already made the handoff authoritative and the *writer* of `STATE.md`, so a disagreement is
   resolved by definition: the handoff's derived position wins and overwrites. This is the
   anti-cathedral stop — no reconciliation mechanism is needed.

   ⚠️ **SL-18(1) premise STRUCK by CONVERGENCE-HOLD-1 (MED).** The claim *"no real handoff has ever
   carried its provenance fields"* is **FALSE** — `.planning/HANDOFF.md:3-4` carries both
   `kind: manual` and `trigger:`, as do its last three commits. It was inherited from the handoff's
   prose while this ledger claimed its findings were code-verified. **The decision stands** (additive,
   never-gating, floor guarantees the write); only its justification is corrected.

---

# ═══ PHASE-1 RETURN — repairs to CONVERGENCE-HOLD-1 (2026-07-27) ═══

> Convergence pass 1 returned **HOLD, 18 findings (9 HIGH)**. Full review:
> `CONVERGENCE-HOLD-1.md`. Every finding is accepted as written; none is re-litigated. The entries
> below **supersede** the named parts of SL-1..SL-18 (supersede-never-rewrite, C5) — the originals
> stay readable so the lineage survives.

### SL-19 — comparator operands defined; undated sources resolved via git · LOCKED · repairs H1

- **Repairs:** H1 — the comparator had an undefined left operand and was uncomputable over
  `DECISIONS.md` and `GRILL-LEDGER.md`, which carry no frontmatter and no per-entry dates.
- **Decision:**
  - **Left operand = the `HANDOFF.md` git commit timestamp.** No new frontmatter field. Because
    depth is written *into* `HANDOFF.md` and committed (SL-3), the commit time **is** the depth-write
    time. This is CA-L19's original operand, preserved.
  - **Right operand, per source class — never per-entry text parsing:**
    - **Git-tracked sources** (`DECISIONS.md`, `GRILL-LEDGER.md`, `DEFERRED.md`, `LESSONS-LEARNED.md`):
      `git log -1 --format=%cI -- <path>`, routed through the pinned helper (Doctrine law 1).
      This **also repairs the `DEFERRED.md` MED finding** — the heading date `(2026-07-21)` misses
      the body's 2026-07-25 re-assignment; the file's commit time does not.
    - **Board**: the in-line ISO-8601 timestamp of the newest `DONE`/`DECISION` line
      (`protocol/board.md:9` grammar), unchanged from CA-L19.
    - **Escalations**: **file mtime only.** ⚠️ **Verified:** the payload built by
      `escalation.build_escalation` carries **no timestamp field** (checked the full `S1.json` and
      the builder), and `.kata/` is gitignored so there is no git time. On a fresh clone `.kata/`
      is absent ⇒ the source contributes nothing (tolerant-I/O). Honest limit, not hidden.
- **Rationale:** Per-file git timestamps on the *six named collector sources* is not the "git-only"
  rule SL-10 rejected — that rejected *any commit anywhere* demoting the handoff. A commit touching
  `DECISIONS.md` **is** a depth-worthy change; detecting it is the point.
- **Edges:** a whitespace-only edit to a collected source demotes the handoff. **Accepted residual**
  — demotion only triggers a rebuild (cheap), whereas a missed change is the dangerous direction.
  Fail-safe direction chosen deliberately.

### SL-20 — gate evidence is CITED WITH STALENESS, never re-run, never presented as green · LOCKED · repairs H2

- **Repairs:** H2 — and **retracts SL-9's "free T-04 fix"**, which the gate disproved by running it:
  `git merge-base --is-ancestor 159fc9b HEAD` → **yes**, so the stale artifact **passes** an ancestry
  check. Ancestry tests *validity*, not *freshness*.
- **Decision:** The floor **never re-runs the gauntlet** (146 s would block the auto-compact crossing
  SL-5 exists to survive). It **cites `.kata/RESULT.json` with a mandatory staleness verdict**:
  the `gateName` verbatim, `resultSha`, and the drift `git rev-list --count <resultSha>..HEAD`.
  When `resultSha != HEAD` the floor states **STALE** explicitly and **must not** present the
  recorded counts as current green.
  **The authoritative gate signal is the `§0` verify command the successor runs** — which is exactly
  how this session established green. `_REENTRY_TEMPLATE` already carries it.
- **Corrected measurements:** drift is **56** commits (`resultSha 159fc9b`) / **61**
  (`baselineSha 0922cf6`) — **not 37**, a figure carried from the handoff without measuring. And
  `gateName: advisor-executor-integration` runs three test files: **it is not the gauntlet**, so an
  uncorrected floor would report `537 passed` against a ground truth of `4/4 PASS`.
- **This is the real T-04 fix:** the stale artifact becomes **labelled stale** rather than silently
  creditable. SL-5's gate-freshness edge is now **closed**.

### SL-21 — the full section contract, contiguous, with Read-in order restored · LOCKED · repairs H3 + the §7 collision

- **Repairs:** H3 — `Read-in order` (required section 1 of the existing schema) had been silently
  dropped **while SL-8's entire rationale for demoting `kata-orient` depends on it**; `§4` vanished
  unstated; "suggested next skills" was neither deleted nor kept; numbering skipped 4 and 8.
- **Decision — eleven sections, `§0`–`§10`, contiguous, in read order:**

  | § | section | half |
  |---|---|---|
  | 0 | GROUND TRUTH (verify commands + expected values) | **FLOOR** |
  | 1 | POSITION (phase · arc · open PRs · board tail) | **FLOOR** |
  | 2 | WHAT SHIPPED (commits + paths, derived) | **FLOOR** |
  | 3 | WHAT THIS SESSION DID | DEPTH |
  | 4 | FINDINGS THAT REORDER THE QUEUE | DEPTH |
  | 5 | DECISIONS SETTLED · DO NOT RE-LITIGATE | DEPTH |
  | 6 | READ-IN ORDER | **FLOOR** |
  | 7 | NEXT STEP, IN ORDER | DEPTH |
  | 8 | OWED TO THE OPERATOR | DEPTH |
  | 9 | WHAT I GOT WRONG | DEPTH |
  | 10 | REDACTION | **FLOOR** |

  - **`READ-IN ORDER` is FLOOR** — it is the ordered list of paths the handoff cites, mechanically
    derivable. This restores SL-8's dependency.
  - **"Suggested next skills" is DELETED**, explicitly. Superseded by `§7` plus the re-entry block,
    which names the next action directly. The live 2026-07-26 handoff already omitted it with no
    consequence.
  - **🔑 Cross-references cite sections BY NAME, never by number.** This kills the `§7` collision
    (SL-3 made `§7` = "what I got wrong" while `protocol/engram.md:153-155` normatively references
    "the `kata-handoff` §7 redaction filter") and prevents the whole class recurring. `engram.md`'s
    reference is doc-baked to `§REDACTION`.
- **`§10 REDACTION` behavior (closes SL-3's unconfirmed edge):** the floor runs the **scan** and
  records its result. A positive hit **never blocks the floor write** and **never auto-scrubs**; it
  writes `REDACTION: HIT — <count> candidate(s), review before sharing` into `§10`. At the
  auto-compact crossing there is no turn to escalate into, so blocking would produce **no handoff at
  all** — the worst outcome. Consistent with D151's *scrub never blocks emit* posture.

### SL-22 — the depth journal is git-durable via an orphan ref; cadence is mechanical · LOCKED · repairs H4

- **Repairs:** H4 — no cadence, format, filename or writer; and **D81 makes tier-3 `.kata/` a
  disposable cache rebuilt from the git trail**, so a journal there holding the only copy of
  model-authored narrative is lost on rebuild. **SL-13(2) is superseded.**
- **Decision:**
  - **Location: an orphan git ref, written by plumbing only** — durable, survives a tier-3 rebuild,
    and **never touches the working tree or index**, so SL-5's `git status --porcelain -> empty`
    tripwire is preserved. This is the D133 recovery-ref carve-out's shape.
  - ⚠️ **Labelled honestly as an EXTENSION, not reuse** (`protocol/reuse-claims.md`):
    `kata_trail.snapshot_board()` snapshots **`.kata/board.md` only** and `_TRAIL_REF` is a module
    constant — verified. A generalized snapshot is **new code**.
  - **Cadence — mechanical events, not model memory:** a **gate/review verdict carrying findings**
    (a machine event — this session's own HOLD is the proof), an **escalation write**, and an
    explicit **operator-correction marker**. `§9 what I got wrong` is *generated by review verdicts*,
    which are files, not recollections.
  - **Format:** one append-only row — `<ISO-8601-UTC> | <class> | <citation> | <text>`, where class ∈
    `finding | correction | escalation`.
- **Honest residual:** a finding the model notices with **no** gate, review, or escalation behind it
  has no mechanical trigger and depends on the model appending. **Named, not hidden** — this is the
  irreducible prose-enforcement remainder, now confined to one row class instead of six sections.

### SL-23 — subject identity keys on a required structured Targets field · LOCKED · repairs H5

- **Repairs:** H5 — `Doc-baked` is read by **no** parser (`learn_feed._FIELD_PREFIXES` omits it; the
  code comment names this exact fall-through), its values are free prose, and it reads "pending" in
  **8 of 18** entries — so SL-12's "mechanical" identity was judgment, fixing a *durable artifact's
  identity* against the Determinism Doctrine.
- **Decision:**
  - The ledger entry format gains a **required `Targets:` field**: zero or more repo-relative paths,
    one per line, **and nothing else** — or the literal `(none)`. `Doc-baked` stays prose for humans.
  - **Subject identity keys on `Targets` only.** An entry with `(none)` contributes to no subject and
    is never inferred into one (PD-2).
  - **"Initiative" is defined operationally:** the spec-directory name of the ledger the entry lives
    in (`.planning/specs/<initiative>/GRILL-LEDGER.md`). `DECISIONS.md` entries belong to **no**
    initiative — they contribute to a subject's timeline but **never count toward the ≥2 bar**.
- **Migration:** this ledger's own 18 entries get `Targets:` retrofitted before any emit.

### SL-24 — collector and comparator scope to the HANDOFF WINDOW · LOCKED · repairs H6

- **Repairs:** H6 — `GRILL-LEDGER.md` was named by bare filename with **19** in `.planning/specs/`
  and no state recording which is current; same ambiguity for the live board vs **four**
  `board.*.archive.md` files.
- **Decision:** **Every collector and comparator source is scoped to the handoff window** — changed
  since the **previous `HANDOFF.md` commit**. Ledgers: those whose `git log -1` is after that commit.
  Boards: the live board plus any archive created after it. Deterministic, self-scoping, and it
  reuses the exact window SL-19's comparator already computes — **one concept, two uses.**
- **Edges:** first-ever handoff (no previous commit) ⇒ window opens at the repo root commit and the
  floor says so. A ledger edited for a typo enters the window — same accepted fail-safe residual as
  SL-19.

### SL-25 — the writer is tools/kata_handoff.py; citation checks gate DEPTH only · LOCKED · repairs H7

- **Repairs:** H7 — no module was named as the floor's writer (the central new build artifact was
  unowned), and SL-4 deferred *where the checks live* while its edges asserted *"gate fails"* —
  answering gate-vs-advisory both ways.
- **Decision:**
  - **Writer: a new `tools/kata_handoff.py`** — floor writer + depth collector + citation checks.
    `tools/kata_handoff_break.py` keeps its single job: rendering the operator-facing notice.
  - **The citation checks GATE.** `kata_handoff.py` refuses to write depth that fails them and exits
    nonzero. Not advisory-in-review; the operator's KH-T02 posture (*"it shouldn't have a
    workaround"*) decides it.
  - **The checks NEVER gate the FLOOR.** The floor writes unconditionally, always. A depth failure
    yields floor + an explicitly-marked absent depth — never no handoff.
  - **Not in `validate_skills.py`** — that validates skills; a handoff is not a skill.

### SL-26 — rollup contract defined; migration is MANDATORY and filenames are unchanged · LOCKED · repairs H8

- **Repairs:** H8 — the rollup `INDEX.md` had no content contract at all, and "migration is
  optional" contradicted `learn_feed.py:44-49`, which documents that a prior relpath change
  **orphaned** old pages because idempotency is per-filename, so re-emits write *beside*, not over.
- **Decision:**
  - **The filename is UNCHANGED.** Pages stay `<project>--<source>--<anchor>.md`; SL-11 adds **only a
    subdirectory** ⇒ `decision-patterns/<project>/<project>--<source>--<anchor>.md`. Migration is
    therefore a pure `git mv` whose destination **equals** the emitter's newly-computed relpath, so
    idempotency holds and **no page is orphaned.**
  - **Migration is MANDATORY, not optional** — SL-11's "optional" edge is **struck**. Leaving 269
    pages behind is precisely the documented failure.
  - **Rollup contract:** frontmatter `produced-by: loop` (required by C5 or it can never be
    regenerated), `date`, `scope`, sorted `tags`; body = a table of the project's decision pages
    sorted by `(source-slug, anchor-slug)` ascending, plus links to its subject pages. Regenerated
    idempotently — same inputs, same bytes.

### SL-27 — no --follow; arc is a NEW small capability, not free reuse · LOCKED · repairs H9

- **Repairs:** H9 — SL-12 and SL-17 made `git log --follow` load-bearing, but **Doctrine law 1 pins
  `log.follow=false`** in the shared helper (two live enforcement sites: `contract_gate.py:150`,
  `kata_restore.py:493`, plus a test), and `--follow` appears **nowhere** in the codebase. It is also
  rename-heuristic dependent, hence not reproducible.
- **Decision:** **Do not use `--follow`.** Arc is read with a plain single-pathspec `git log` through
  the pinned helper. **Verified this is sufficient:** `HANDOFF.md` has **never been renamed**
  (`git log --diff-filter=R` is empty) and plain `git log` yields the **same 65** commits. If a
  rename ever occurs, lineage truncates and the floor **says so** rather than silently shortening.
  SL-12's rename edge is superseded identically.
- **SL-17's "arc is already free" is RETRACTED** as an uncited reuse claim. Reading git history for
  arc is **new code** — small, but new, and labelled as such (`protocol/reuse-claims.md`).

### SL-28 — factual corrections to this ledger · LOCKED

- **`LESSONS-LEARNED L10` mis-cited twice.** L10 is *"A/B VERDICT: TIE…"*; the drift-magnet language
  is **L9** (`LESSONS-LEARNED.md:52`). Both SL-4 and SL-12 are corrected to cite **L9**. This is a
  real-citation/wrong-claim — the PD-2 class SL-4 itself defines — and it was the stated ground for
  SL-12's rejection of token-overlap clustering. **The rejection still stands** on its own reasoning
  (an unpinned threshold is not reproducible, Doctrine law 1), now cited correctly.
- **`DECISIONS.md` mis-measured.** It is **2734 lines with 2 headings** (`:1`, `:596`), not "2683
  lines, one heading" — this ledger's own `^#{2,3}` regex excluded the level-1 heading. **2 of its
  171 bullets use non-`D{n}` anchors** (`D-multisession`, `D-registry`) and there is a mid-file
  `### sprint-cadence` section. SL-13(3)'s conclusion (three parsers, do not unify) **stands**, but
  the bullet parser must handle `D-<word>` anchors and must not mis-scope the `sprint-cadence` block.
- **SL-2's citation corrected.** `protocol/handoff.md:41-43` is CA-L21(1) and concerns dispatch
  briefs / worker reports / escalation payloads — it says nothing about the wiki. SL-2's decision
  stands on its own three reasons; the mis-citation is struck.
- **SL-16 over-claimed a gap.** `learn_feed.render_page` **already** requires `scope`, hard-fails on
  an unknown value, and emits `produced-by`/`source`/`date`/`scope`/sorted `tags`. **No completeness
  check is needed** — SL-16 closes with zero lines changed. Its redaction edge is **struck**: it
  contradicts **D151** (`engram.md:160-165` — for the loop feed the scrub *never blocks emit*).
- **Emit-side title truncation (LOW).** `learn_feed._parse_heading_entry` cuts the title at the
  **first** status token, so `### SL-10 — … · LOCKED · supersedes CA-L19` would emit with
  "supersedes CA-L19" **silently discarded** — losing the C5 lineage SL-10 exists to preserve.
  **Mitigation adopted:** supersession is recorded in the entry **body** (`· supersedes` stays in the
  heading for human readers but is never the sole carrier). All Phase-1-return entries above follow
  this.
- **`· LOCKED` entries with open edges (MED).** SL-1's edges are closed by SL-13(4) and SL-18(2);
  SL-3's `§R` edge is closed by SL-21; SL-5's gate edge by SL-20; SL-6/SL-7's journal edges by
  SL-22. **Forward pointers are now explicit** so a top-down builder does not halt at SL-1.

---

# ═══ PHASE-1 RETURN #2 — repairs to CONVERGENCE-HOLD-2 (2026-07-27) ═══

> Pass 2 returned **HOLD, 13 HIGH**. Root cause named by the author: **Phase 0 never READ
> `.planning/DECISIONS.md`** — it was measured structurally and treated as a parse target rather
> than as binding law. **That is fixed first:** D74, D81, D133, D135, D142 and D151 have now been
> read in full and are cited below. Every entry here supersedes the named parts of SL-19..SL-28.

### SL-29 — the BOARD is the depth journal; D135 already decided this · LOCKED · supersedes SL-6 and SL-22 · repairs NEW-1, NEW-10, H4

- **Repairs:** NEW-1 — SL-22's orphan-ref journal is barred by **D135 (FROZEN)**, which this grill
  never cited, and would additionally be squashed at integration (**D133(d)**), forbidden as a new
  autonomous-git path (**D142(b)**), and lost on clone (`refs/kata/*` is not in
  `remote.origin.fetch`).
- **🔴 SL-6's rejection of the board was FACTUALLY WRONG — author-owned.** SL-6 claimed session
  narrative on the board "would contaminate the `maxInFlight`/`overlaps` evidence." **It cannot.**
  The canonical reduce at `protocol/board.md:96-102` pairs **only** `CLAIM` and `DONE`; every other
  TYPE is skipped. `NOTE` lines are inert to concurrency evidence, exactly as `PROGRESS` already is
  by explicit design (`board.md:23-31`). The stated ground for inventing a second log was false.
- **D135, read in full:** *"Building a second append-only log alongside the board doubles the write +
  parse + divergence surface for a capability that already exists: `protocol/board.md` is already an
  append-only, worker-stamped event log (`CLAIM/DONE/BLOCK/ESCALATE/NOTE/DECISION/PROGRESS`, one line
  each)… Its **only** deficiency for restore is that it lives in gitignored tier-3."*
- **Decision:** **Depth accrues as board `NOTE` lines** in the existing line grammar
  (`<ISO-8601-UTC> | <agent-id> | NOTE | <task-id> | <message>`), with the message prefixed
  `finding:` / `correction:` / `escalation:`. **No new artifact, no new ref, no new format** —
  satisfying D135, D133(c)(d), D142(b) and CA-L21(6) simultaneously.
- **Durability resolves by tier, not by a new mechanism (D81):** board rows are the **tier-3 accrual
  buffer**; `.planning/HANDOFF.md` — git-tracked and committed — is the **tier-2 durable record**.
  Nothing needs to survive a clone in `refs/kata/*`, so `restore-hardening/DESIGN.md:44`'s accepted
  worst case is not on the critical path. `kata-readiness` already rebuilds tier 3 from tier 2.
- **Rotation:** rotation archives to `.kata/board.<utc>.archive.md` (`board.md:44-50`) — nothing is
  lost, and SL-24's window reads live board **plus** archives.
- **Writer / reader / format — all pre-existing:** `tools/kata_board.py`, `protocol/board.md`
  grammar. H4's "no filename, no writer" and NEW-10 dissolve; there is no new subsystem to name.
- **Non-run session with no board** ⇒ appending a `NOTE` creates `.kata/board.md`; agent-id is the
  session's conductor id, task-id is `-` when no task is in flight.

### SL-30 — redaction stays FAIL-CLOSED per D74; the floor carries no redaction surface · LOCKED · supersedes SL-21's §REDACTION clause · repairs NEW-3

- **Repairs:** NEW-3 — SL-21 downgraded a fail-closed gate to advisory, justified by D151/G4, which
  `protocol/engram.md:160-165` scopes to **the loop feed only** while keeping agent-authored pages
  fail-closed. **D74 is frozen: redaction is a HARD pre-write gate.**
- **Decision:** **The D74 hard gate is preserved unchanged for DEPTH.** The apparent conflict with
  SL-3's never-no-handoff guarantee dissolves on inspection: **the FLOOR carries no redaction
  surface by construction** — its content is git identifiers (SHAs, branch names), repo-relative
  paths, gate counts and the fixed verify-command template. There is no free prose in the floor, so
  a positive hit is not reachable there. The gate therefore applies where prose lives (depth), and
  never blocks the floor.
- **Consequence:** at auto-compact with no model turn there is **no depth to gate**, so the hard gate
  and the never-no-handoff guarantee never actually collide. SL-21's "never blocks / never
  auto-scrubs" wording is **struck**; D151/G4's redact-and-mark posture applies **only** to the loop
  feed, as engram.md scopes it.
- **Doc-baked:** `protocol/engram.md`'s cross-reference is updated to `§REDACTION` **by name** (the
  SL-21 by-name rule), preserving the D74 semantics it points at.

### SL-31 — SL-4's checks restated BY NAME and scoped to DEPTH · LOCKED · repairs NEW-2, NEW-8

- **Repairs:** NEW-2 — SL-21 renumbered the sections but never remapped SL-4, whose checks still
  named `§3`/`§5`/`§7` in the old scheme, binding the anti-KH-T02 checks to the wrong sections.
  NEW-8 — `§0` is FLOOR and SL-25 says checks never gate FLOOR, so SL-4's first check could never
  fire.
- **Decision — the checks are restated by SECTION NAME and apply to DEPTH only:**
  - **FINDINGS THAT REORDER THE QUEUE** — every finding cites a `path` / SHA / `file:line` that
    **resolves in the repo**.
  - **DECISIONS SETTLED** — a table with ≥1 row.
  - **NEXT STEP, IN ORDER** — an ordered list with ≥1 item.
  - **WHAT I GOT WRONG** — names a concrete correction **or** explicitly asserts none *with a
    reason*; a bare empty section fails.
- **The FLOOR needs no checks, and this is not a gap.** Floor sections are **generated from a
  template with substituted values**, not authored — a generated section cannot be stubbed, so
  there is nothing for a stub-check to catch. Pass 1's MED (*"five well-formed fabricated lines
  pass"*) is therefore **moot by construction**: `§GROUND TRUTH` is emitted from
  `kata_handoff_break._REENTRY_TEMPLATE`, not typed. **SL-13(1)'s `N` pin is withdrawn as
  unnecessary** — there is no count to enforce against a template.

### SL-32 — freshness keys on an explicit depth marker, not the file commit · LOCKED · supersedes SL-19's left operand · repairs NEW-6

- **Repairs:** NEW-6 — SL-19 made the left operand the *file's* commit time, so a **floor-only**
  write (the auto-compact case SL-3 guarantees) resets the freshness clock, SL-8 suppresses the
  rebuild, and the successor gets ground truth with no depth and no rebuild. SL-10 had said
  *"compare against the DEPTH write, not the file mtime"*; SL-19 collapsed it by assertion.
- **Decision:** `HANDOFF.md` frontmatter gains one **additive** field, `depth: present | absent`,
  written by the floor — the same additive-provenance pattern `kind:`/`trigger:` already use
  (CA-L21(2); absent ⇒ unknown, never gates, BC preserved for all 65 historical handoffs).
  **The comparator's left operand is the commit time of the newest `HANDOFF.md` commit whose blob
  carries `depth: present`.** A floor-only emergency write therefore does **not** reset freshness,
  and SL-8 correctly falls through to the `kata-orient` rebuild.

### SL-33 — source timestamps do not depend on tracked status; the handoff commits its sources with it · LOCKED · repairs NEW-5, H1, H6

- **Repairs:** NEW-5/H1 — the live `GRILL-LEDGER.md` is **untracked** (18 of 19 tracked), and
  `DECISIONS.md` / `LESSONS-LEARNED.md` last committed `2026-07-19`, **7 days before** the last
  handoff — so the repaired collector would return **nothing** and this grill's 28 decisions would
  be invisible to the handoff meant to carry them. H6 — archive timestamps use two filename formats
  that disagree with mtime by up to 2 days.
- **Decision:**
  - **Per-source timestamp = `git log -1 --format=%cI -- <path>` when the path is tracked, else file
    mtime.** Tracked-status is detected, never assumed. This covers the untracked live ledger, the
    gitignored `.kata/` archives, and escalation JSON (verified to carry no timestamp field) under
    one rule.
  - **Never parse archive filenames** — two formats exist (`board.20260625T025924Z` vs
    `board.20260626172811`) and both disagree with mtime. Use mtime only.
  - **🔑 The handoff write commits its collected sources IN THE SAME COMMIT as `HANDOFF.md`.** This
    pins the commit-ordering ambiguity NEW-5 raised (commit the ledger after ⇒ stale at birth;
    before ⇒ never stale) and makes the window well-defined by construction: everything the handoff
    collected is, by definition, not newer than the handoff.
- **Edge:** a source that cannot be committed (gitignored `.kata/`) is exempt from the same-commit
  rule; its mtime is compared normally.

### SL-34 — no shared git helper exists; inline the pins per call site · LOCKED · repairs NEW-4

- **Repairs:** NEW-4 — *"routed through the pinned helper (Doctrine law 1)"* is a **phantom reuse
  claim**, committed twice, in the entry that retracts a phantom reuse claim.
- **🔴 Verified against the code, not asserted:** `log.follow=false` appears in exactly **two**
  production files and **both inline the flags at the call site** — `tools/contract_gate.py:150`,
  `tools/kata_restore.py:502`. The Doctrine's named model `kata_telemetry._run_git:139` pins
  `core.quotepath=off` and `log.showSignature=false` and **does NOT pin `log.follow=false`**.
- **Decision:** **There is no shared pinned helper. Follow the existing per-call-site pattern** —
  every `git log` in the new code inlines the Doctrine law-1 pins explicitly, as the two existing
  sites do. Calling `kata_telemetry._run_git` is **forbidden** for single-pathspec `log`: under an
  operator with `log.follow=true` in gitconfig it would activate rename-following — the exact
  nondeterminism SL-27 exists to remove (see `kata_restore.py:493-495`).

### SL-35 — the grill-close emit is BLOCKED and formally deferred · LOCKED · repairs NEW-7

- **Repairs:** NEW-7 — pass 2 **ran the shipped parser** over this ledger: `learn_feed.py:511-518`
  renders `body` only when no recognized field is non-empty, and this ledger's house style
  (`- **Decision:**` + indented sub-bullets) yields an empty `decision`, orphaning content into
  `body`. Measured: **20 of 29 entries lose body content — 19,153 characters.** SL-19's page renders
  with **no Decision at all**.
- **Decision:** **The D151/G1 grill-close emit does NOT run for this grill.** Emitting would publish
  synthesis pages missing their decisions — a PD-2 violation written to a durable store.
  The defect is parked via the **sanctioned PD-1 path** (`kata-defer` → `DEFERRED.md`), operator-
  visible and graded at the gate, with two candidate fixes named for the owning run: extend
  `_FIELD_PREFIXES`/`render_page` to handle indented sub-bullets, **or** flatten ledger entries to
  single-paragraph fields. **SL-28's "SL-16 closes with zero lines changed" stands** (that was about
  `render_page`'s page contract, verified correct); it does **not** extend to the parser.

### SL-36 — remaining corrections · LOCKED

- **The L9/L10 citation is DROPPED entirely** (NEW-9). L9 reports a *classification* drift-magnet
  honored in a zero-drift run; it says nothing about magnitude constants, so re-anchoring did not
  cure the PD-2 defect — it moved it. **SL-12's rejection of token-overlap clustering stands on
  Determinism Doctrine law 1 alone** (an unpinned threshold is not reproducible), which needs no
  lessons citation.
- **SL-2's "the vault lives outside git" is FALSE** (NEW-12) — `Vault\.git` exists, and SL-26
  depends on it for `git mv`. **The decision stands** on its other two grounds (the vault is outside
  *this repo*, config-gated and no-ops when unset; and the pointer would precede its reader); the
  false ground is struck.
- **Depth that fails its checks is MARKED, never discarded** (NEW-11). SL-25's "refuses to write
  depth" is amended: `kata_handoff.py` writes the depth under an explicit
  `UNVERIFIED — failed citation check: <which>` banner and exits nonzero. KH-T02's no-workaround
  posture is preserved because the failure is **loud and durable**; the never-no-handoff guarantee is
  preserved because nothing is thrown away at a crossing where it cannot be re-authored.
- **`READ-IN ORDER` ordering key defined** (H3): the floor emits every path the handoff cites, in
  **first-appearance order within the document**. Deterministic, and it preserves
  `protocol/handoff.md:9`'s "in sequence" intent without requiring the author to re-sequence.
- **`Targets:` is consumed by the subject-page builder, not by `learn_feed`** (H5) — so its absence
  from `_FIELD_PREFIXES` is not a defect, and no `learn_feed` change is implied. All 29 ledger
  entries get `Targets:` retrofitted before any subject-page build. Corrected count: **29, not 18.**
- **SL-26 gaps closed** (H8): the rollup's **generator** is the same emitter, its **trigger** is
  grill close, its **`scope:`** is `project`. The 269-page migration (256 `kataharness` + 13
  `kagami`) is a **one-time operator-run `git mv`**, explicitly **NOT** performed by `learn_feed`,
  which records a stdlib-only / no-subprocess posture (`learn_feed.py:74`).
