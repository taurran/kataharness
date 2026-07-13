# DESIGN — elevate-grill-ux (B1 + B2, one initiative)

**Status:** **FROZEN (D153); BUILT; ADVAL'D** — freeze-gate v1 HOLD (8 findings, folded) → re-gate
v2 SHIP-WITH-FIXES (8 findings, folded) → built → 2-reviewer fresh-context adval SHIP-WITH-FIXES ×2
(13 findings, all folded: A1-1 untracked operator config swept into the feat commit — removed from
the index; A1-2/3/4/5, A2-2, A2-6 RUBRIC recording-spec pins restored/hardened incl. per-ledger
sequential numbering + the status-vocab-in-title parser hazard; A2-1 HIGH kata-initiate Phase 5
Path A/B close-out contradiction fixed — Path B on-confirm now runs convergence → ELEVATE → record
→ emit, Path A explicitly forgoes with an evaluator-checkable bail ledger line (A2-4); A2-3
DECISION-LEDGER.md EV-{n} shape + Edges-exemption added; A2-5 decline-reveals-a-gap routed through
the scoped-check machinery; A2-7 depth-table gate wording fixed). kata-initiate bump raised
0.4.1 → **0.5.0** (the adval-driven Path A/B close-out prose is new capability, not wording).
Operator-directed
2026-07-12 (BACKLOG 2026-07-12b #1/#2); built 2026-07-12c in an operator-away autonomous session
(mid-session operator authorization: "I approve of all commits/pushes/merges this section … when I
am back we will do a full evaluation"). Provisional items are consolidated in §RATIFY below.
D-record: **D153** on freeze.

**Scope:** prose-only. Files:
- `skills/plan/kata-grill/RUBRIC.md` (ELEVATE section + Interaction-format amendment + emit
  cross-ref — **incl. the emit-section trigger sentence (v2-F7): "The moment the fresh pass
  returns SHIP and the ledger checkpoints its final entry…" becomes "…returns SHIP, the ELEVATE
  outcome is recorded, and the ledger checkpoints its final entry…"**)
- `skills/plan/kata-grill-{essential,standard,advanced}/SKILL.md` — MINOR 0.2.0 → 0.3.0
- `modules/initiation/kata-initiate/SKILL.md` — 0.4.0 → 0.5.0 (two named line targets F-5 + the
  adval A2-1 Phase 5 Path A/B close-out alignment + A2-7 depth-table wording)
- `skills/plan/kata-grill/resources/DECISION-LEDGER.md` — EV-{n} entry shape + Edges-exemption
  (adval A2-3)
- `protocol/engram.md` — new seam-registry row for the ELEVATE decision point + producer-line
  alignment (F-2; its own maintenance rule requires the row land in the same change)

No engine code. `tools/learn_feed.py` is byte-untouched (F-1 makes that true, see E5).

---

## Goal (operator's words, BACKLOG 2026-07-12b)

- **B1 (ELEVATE):** "at the END of every grill session — on EACH KataHarness execution — the harness
  uses its deep context + task understanding to make ONE brainstormed recommendation (more only if
  the user asks) that elevates the design and function of the output. Always-on, single by default.
  Natural home: a grill-close step after the convergence gate, beside the D151 learn-feed emit (and
  its recommendation is itself grill-ledger material → second-brain input)."
- **B2 (single-question UX):** "the doc-grounded grill must ask via Claude's single-question output
  (AskUserQuestion) ONE question at a time — never a multi-question dump ('throwing five out there
  isn't a good UX'). Applies to the grill tier skills' interactive flow on the Claude adapter;
  general design discussion stays conversational prose."

## Locked contract

### E1 — The ELEVATE step: position + bounds (LOCKED)

The grill-close sequence becomes, in order:

1. Convergence criteria all hold → fresh-context convergence pass returns **SHIP**
   (Advanced: the final of its two passes).
2. **ELEVATE** (new): pose exactly ONE elevate recommendation (E2–E4). **ELEVATE is posed at most
   ONCE per grill close** — no path re-enters this step (F-4). Operator-requested alternatives
   (E2/F-7 "give me another") occur WITHIN this single ELEVATE step; the once-bound forbids
   **harness-initiated** re-elevation, including after E5a (v2-F2).
3. Record the operator's decision as ledger checkpoint entries (E5). If an acceptance opened new
   branches, resolve them and run the scoped re-check (E5a) — then resume **here at step 3's
   recording, proceeding to step 4**, never back to step 2.
4. **Grill-close emit** (D151 `learn_feed.py`, byte-unchanged engine) — the elevate entries are in
   the ledger by then, so they ride the same emit into the second brain.
5. Handoff to FREEZE.

ELEVATE runs strictly AFTER the convergence SHIP (the tree is closed; elevate is value-add on top,
never a reopened survey) and strictly BEFORE the emit — the operator's stated anchor.

**Early exit (F-3, precised v2-F3):** a grill ended by the operator's Path-A hard bail ("execute"
typed mid-grill) never reaches a convergence SHIP and therefore **forgoes ELEVATE** — "stop all
remaining grill rounds immediately" means immediately; the emit follows the existing bail behavior
unchanged. **Path-B is NOT a bail** (kata-initiate: the grill self-proposes readiness and the
operator confirms — a normal close): a confirmed Path-B close runs the normal close-out sequence —
convergence pass → ELEVATE → record → emit — satisfying "at the END of every grill session."

### E2 — What the recommendation is (LOCKED)

ONE brainstormed recommendation that **elevates the design or function of the output** — a concrete
improvement the resolved design does not already contain. It MUST be grounded in THIS run's grill
context: cite the resolved branch(es), goal terms, or probed scenarios that motivate it. **Generic
advice is a violation** — if no grounded elevation exists, say so honestly in one line and record it
per E5's no-elevation shape; never invent filler (PD-2). More than one recommendation is offered
ONLY if the operator asks ("more only if the user asks").

### E3 — Always-on, a grill behavior (LOCKED; scope note in §RATIFY)

ELEVATE is part of the grill method (RUBRIC), not a config-gated module. It runs whenever a grill
runs (essential / standard / advanced). `skip`-depth runs no grill ⇒ no ELEVATE (nothing to ground
it in — an interpretive narrowing of "on EACH KataHarness execution"; listed in §RATIFY). It is NOT
tiered away — same D33-class posture as the convergence gate: a tier may scope the tree it grills,
not the close-out behaviors.

### E4 — FORK 1 (PROVISIONAL, §RATIFY): tier behavior = SAME at all tiers

Same structural behavior at every tier: exactly ONE recommendation, same grounding rule, same
recording rule. The grounding *richness* scales naturally with tier (a deeper grill has more
context to elevate from) — no added machinery, no per-tier variants (anti-cathedral).

### E5 — Recording the decision (LOCKED mechanics; FORK 3 in §RATIFY)

Every ELEVATE outcome is appended to the decision ledger as a normal checkpointed entry BEFORE the
emit, **always with a `· LOCKED` status token** so the SB-L1 ledger grammar
(`learn_feed._STATUS_RE`: only `LOCKED`/`resolved` emit; anything else is `parsed_open_skipped`)
carries it into the feed with a genuinely unchanged engine (F-1). **The entry heading MUST use the
ledger's normal anchor grammar (v2-F1): a dedicated `EV-{n}` anchor —
`### EV-{n} — Elevate: <short title> · LOCKED` — which satisfies `learn_feed._ANCHOR_RE` (digit /
dash-segment required); a heading without a valid anchor token is not an entry at all and silently
never emits (not even counted as skipped). `EV-{n}` numbering is per-ledger sequential, and the
anchor also names the emitted page (`<project>--EV-{n}.md`) — it must not collide with an existing
anchor in the same ledger.** The outcome lives in the entry's Decision field:

- **Accepted** ⇒ Decision = the recommendation (rationale = the operator's acceptance + the
  grounding). Compiled into the frozen DESIGN by FREEZE like any other resolution.
- **Declined** ⇒ Decision = "Declined — <operator's reason>" (the decision *not to adopt* IS the
  resolved decision; one line suffices). **A bare Decline with no free text records Decision =
  "Declined — no reason given"; the harness never poses a follow-up question to extract a reason
  (v2-F4).** **FORK 3 (PROVISIONAL): declines feed the second brain too** — a decline is
  preference signal.
- **No grounded elevation found** (E2) ⇒ Decision = "No grounded elevation beyond the resolved
  design" — recorded LOCKED so the honest null result is signal too.
- **Free-text outcomes (F-7):** "give me another" ⇒ recommendation #1 is recorded
  "Declined — superseded by request for an alternative (<reason if given>)" and the alternative
  becomes the (still single-at-a-time) next posed recommendation, recorded on its own `EV-{n}`
  decision; accept-with-modification ⇒ Decision = the operator's modified form, rationale notes it
  as an accepted-with-correction of the posed recommendation; **"tell me more" ⇒ in-step
  elaboration only — elaborate, then re-pose the SAME accept/decline question; no ledger entry of
  its own (v2-F6).**

**E5a — acceptance that opens new branches (F-4 bounds):** the recommendation must be posed
edge-defined, so this is the exception; when it happens, resolve the newly opened branches via the
normal Phase-1 loop, then run a **scoped** fresh-context convergence check over ONLY those branches
— **one pass regardless of tier** (it is scoped; Advanced's two passes gate the main tree, not
this). A scoped-check HOLD names the under-specified branch → back to Phase 1 for that branch,
then the scoped check RE-RUNS until SHIP — "one pass" means one pass per attempt, not once-ever
(v2-F8), per the RUBRIC backstop. On SHIP, resume at E1 step 3 (record, then emit) — never a
second ELEVATE.

### E6 — FORK 2 (PROVISIONAL, §RATIFY): interaction shape = the B2 single-question surface

The elevate recommendation is posed as ONE structured question through the same single-question
binding as the rest of the grill (Claude adapter: `AskUserQuestion`): the recommendation with its
grounding as the question, options **Accept (lock it in)** / **Decline**, free text always available
(decline reason, "tell me more", or "give me another" — handled per E5/F-7).

### U1 — B2: one question at a time (LOCKED; Claude-adapter binding per the directive)

The RUBRIC's Interaction format is amended: the grill asks **ONE question per interaction**. The
hard binding is the Claude adapter's, exactly as the operator scoped it (F-6): one
`AskUserQuestion` call containing exactly one question — never a multi-question call, never a
batch. Non-Claude hosts keep their existing prose questioning (per the orientation's recorded
recommendation), with one-question-at-a-time sequencing as guidance, not a new hard binding.
"Group tightly-related questions" is REPLACED by sequencing: related branches are asked in
consecutive single questions, dependency order preserved (an answer re-derives the tree before the
next question — which single-question pacing makes structurally natural). Everything else in the
format holds: 2–4 options, recommendation first, one-line trade-offs, free-text escape, provenance.

### U2 — Scope boundary (LOCKED)

U1 binds the GRILL's interactive flow. It does NOT extend to general design discussion outside the
grill, which stays conversational prose (the operator's standing preference).

**kata-initiate alignment (F-5) — exactly two named targets, both real edits:**
- the infer-then-confirm gate line "surface it explicitly via `AskUserQuestion`" (SKILL.md ~line
  382): add "one value per question, one question at a time" so plural unconfirmed values are never
  batched into one multi-question call;
- Phase 4 goal/details collection (~lines 426–427): add "asked one at a time — never a
  multi-question dump".
Phases 2b and 2e already comply (verified at freeze-gate) — no edit there. The 0.4.1 bump lands
WITH these two modifications (bump-on-modify satisfied by real diffs).

### S — protocol/engram.md (F-2)

Add the ELEVATE decision point as a seam row (a new human accept/decline decision surface whose
outcomes feed the learn-feed), and align the producer line describing the grill-close emit: it
fires at grill close AFTER the ELEVATE step, over resolved/LOCKED ledger entries which now include
the elevate outcome entries (accepted, declined-with-reason, or no-elevation — all LOCKED-status
per E5). **Seam-row pin (v2-F5):** next sequential seam number in the registry's existing column
format; Op = LEARN (latent CONSULT via recall read-back); Sev = MED; Backed-by = D153 / this
design. The builder matches the registry's exact column shape — the pin here is the content, not
a divergent format.

### V — Versioning

- `kata-grill-essential` / `-standard` / `-advanced`: 0.2.0 → **0.3.0** (new capability: ELEVATE
  step + single-question contract in their close-out sequence).
- `kata-grill/RUBRIC.md`: not independently versioned (method doc) — carries the new sections.
- `kata-initiate`: 0.4.0 → **0.4.1** (two real wording-alignment edits, F-5).

## §RATIFY — held for operator ratification at return (one list)

1. **FORK 1 (E4):** tier behavior = same at all tiers, grounding richness scales naturally.
2. **FORK 2 (E6):** elevate posed via the single-question AskUserQuestion surface.
3. **FORK 3 (E5):** declines (and the null "no grounded elevation" result) feed the second brain.
4. **Skip-depth narrowing (E3):** `skip` grill-depth ⇒ no ELEVATE (nothing run to ground it in).

## Acceptance

- Freeze-gated design (fresh-context default-FAIL review): v1 HOLD (8 findings) → folded → re-gate.
- Built: RUBRIC ELEVATE section + Interaction-format amendment + emit-section cross-ref; three tier
  SKILL.md close-out lines + bumps; kata-initiate two-line alignment + bump; engram.md seam row +
  producer alignment.
- Adval: 2 fresh-context reviewers SHIP.
- Validator 48/0/0 (`--write` for README regen); pytest unchanged-green.
- **Live smoke: DONE — LIVE-PROVEN n=1 (2026-07-12c, operator present).** A real essential-tier
  grill (subject: the D160 statusline decoupling) ran the full contract live: four one-question
  `AskUserQuestion` interactions (incl. an operator misclick correction handled in-flow) →
  fresh-context convergence gate SHIP (2 findings folded) → ONE grounded ELEVATE posed (shared
  kata-scope helper, grounded in the run's own D2 edge) → operator ACCEPTED →
  `EV-1 … · LOCKED` ledger entry → grill-close emit **into the real PokeVault**
  (`kataharness--ev-1.md` + 3 decision pages, written=4, idempotent re-run 0/4) → recall read-back
  surfaced all four as `source="second-brain"`. **Honest scope:** proven on a standalone
  essential-tier grill; the kata-initiate Phase-5 Path-A/Path-B close-out legs are not yet
  live-exercised (they ride the next real initiation run).
