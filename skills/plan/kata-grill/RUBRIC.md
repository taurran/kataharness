# kata-grill — shared method (RUBRIC)

The tier-invariant grill method. The `kata-grill-<tier>` skills set only depth; they all obey this.

> **The grill is optional (D71 — Priming-and-Grill).** The grill-depth dial is `skip | light | standard | full`
> (→ `tiers["kata-grill"] = skip|essential|standard|advanced`; map in `protocol/config.md`). **`skip` runs none
> of this** — it freezes the priming prompt as-is and drops to the **autonomous-reliability floor** (default-FAIL
> + the RS research subagent + a `kata-defer` assumption log surfaced at the gate/handoff). Grill (up-front,
> with-human) and RS (in-loop, without-human) are **one ambiguity-resolution spectrum**; skipping the grill
> *shifts* resolution along it, it never removes it. When a grill *does* run (light/standard/full), it adds
> alignment certainty by construction and its decision ledger feeds the second brain at grill close via the
> `tools/learn_feed.py` emitter (D151 — see the grill-close emit step below).

---

## Purpose

The grill is the harness's highest-leverage phase: a frozen plan is only as good as the interrogation that
produced it. The goal is **a very specific design contract** — specific enough that downstream execution has
no room to re-decide (that is what makes [[kata-orchestrate]]'s no-drift line *possible*).

## The anti-pattern this method exists to prevent (read first)

**A one-pass list of "here are N decisions, each with my recommendation" is NOT a grill — it is a survey.**
It pre-answers for the user, stops at the first plausible option, and never stress-tests. (This is the exact
failure recorded in [[LESSONS-LEARNED]] L8/L9 from the Wizard-of-Oz run.) A real grill is **iterative,
demanding, and adversarial to ambiguity**: it walks the decision tree branch by branch, re-deriving the tree
after each answer, and does not stop until the convergence criteria below are met.

> **Not a contradiction with "recommendation-first / simplest-model" (below):** leading each branch with a plain
> recommended option is the *interaction format* + the *starting frame to attack* — the survey anti-pattern is
> emitting the whole list *once* and *stopping*. The plain-language discipline still requires you to probe each
> branch, re-derive the tree, and pass the convergence backstop. Recommendation-first ≠ resolve-on-first-answer.

## Interaction format (the GSD-style binding — L7/L8)

Ask **structured questions the user can either click an option for OR answer in free text.** Every question:
- offers 2–4 concrete options, **recommendation first** and labeled, each with its trade-off in one line;
- **always allows a free-text answer** — never a no-escape constrained picker (that is what [[LESSONS-LEARNED]]
  L7 forbids; offering options *with* an escape is encouraged, not banned);
- states the provenance: what in the spec/code/docs raised this branch.

**ONE question per interaction (D153/U1).** The grill asks **one question at a time — never a multi-question
dump** ("throwing five out there isn't a good UX" — operator, 2026-07-12). Related branches are asked in
consecutive single questions, dependency order preserved: an answer re-derives the tree before the next
question is posed (which single-question pacing makes structurally natural). *(Adapter binding: Claude → one
`AskUserQuestion` call containing exactly ONE question — the hard binding; never a multi-question call, never
a batch. Non-Claude hosts keep prose questioning — numbered options + a free-text prompt — with
one-question-at-a-time sequencing as guidance, not a new hard binding. The pattern is host-agnostic; the
rendering is the adapter's job.)* This binds the GRILL's interactive flow; general design discussion outside
the grill stays conversational prose (the operator's standing preference).

## Plain-language & simplest-model discipline — the PRIMARY grill style (memory `grill-in-plain-terms`)

This is how every grill is conducted, at every tier. It is a **presentation + scope** discipline layered on
top of the rigor below — it changes *how* you ask and *where you start*, and it **never** reduces coverage,
probing depth, or the convergence bar (see the fidelity invariant).

- **Plain human terms.** A moderate-non-expert operator must be able to follow every question without decoding
  internal jargon or unexplained machinery names. If a branch can only be stated in framework-speak, you have
  not understood it well enough to ask it — translate it to the concrete thing at stake. (Operator feedback,
  2026-06-26: *"If you're going to grill me, do it in human terms — I can't follow all this nonsense."*)
- **Lead with the simplest model that satisfies the goal.** The recommended (first) option is the **plainest
  design that actually meets the stated goal** — not the most general, not the most extensible. This is the
  **starting frame for the interrogation, not a shortcut past it:** you still walk the whole decision tree and
  stress-test it (Phase 1). Simplest-first means the *baseline you pressure-test from* is lean, so added
  complexity has to earn its place against a concrete need.
- **Short, concrete options.** 2–4 options, each a genuinely distinct choice in plain words with its one-line
  trade-off. No option whose meaning the operator must reverse-engineer.
- **Stop-and-simplify guard (the anti-cathedral rule).** If you catch yourself designing a config-resolution
  cathedral, a multi-layer binding/abstraction, or a taxonomy the goal never asked for — **halt, collapse to
  the plainest model that works, and ask whether the extra structure is genuinely needed before building it.**
  Over-engineering the design *is* a drift the grill must catch in itself (the operator course-corrected exactly
  this twice — see `grill-in-plain-terms`; e.g. the D104 install-portability reset).

### Fidelity invariant (D33-class — plain ≠ shallow; never tiered, never relaxed)

The plain-language style is **additive and presentation-level**. It does **NOT** weaken any of the rigor that
follows. All of these hold unchanged at every tier when a grill runs:
- the decision-tree enumeration (Phase 0.2) **at this tier's mandated depth** — every branch the tier covers is
  stated plainly and none is dropped *for being awkward to phrase* (a tier may scope which branches it walks —
  e.g. Essential's partial tree — but the plain style never shrinks that scope further);
- the iterative, adversarial-to-ambiguity probing (Phase 1) — *don't accept the first plausible answer*; the
  simplest model is the thing you attack, not a reason to stop;
- the convergence criteria (all boxes) and the **don't-grade-your-own-convergence** fresh-context backstop;
- doc-grounding, glossary canonicalization, decision-ledger checkpointing, contradiction surfacing.

*Test (the binding one, reused from convergence box 5):* **could two independent builders read this contract and
diverge?** If yes, keep grilling — regardless of how plainly the questions were posed. The only differences the
plain style introduces are human-readable questions and a lean starting design; it must reach the **same
specificity** the convergence bar demands. If "plain" ever produces a thinner contract, that is the failure —
plain is about clarity and right-sizing, never about asking less.

## Phase 0 — Ground before you ask

1. Read the spec / source docs in full, plus any existing `CONTEXT.md` / `CONTEXT-MAP.md`, ADRs
   (`docs/adr/` or the project's decision log), and the relevant code.
2. **Build the decision tree:** enumerate EVERY branch the spec leaves open or under-specified — data shape,
   classification/boundary calls, algorithm/magnitude choices, interface contracts, failure behavior,
   backward-compat, security surface. Missing branches are how vague specs ship bugs.
3. **Answer from the docs/code whatever you can** — if a question is resolvable by exploration, resolve it
   yourself and record it; do NOT spend the user's attention on what you can discover.
4. When `target.kind == existing` (version-up), invoke [[kata-graph]] FIRST to build/load the cached
   `kata.graph.json` and ingest its feature-seeded digest — interrogate the feature's design AGAINST the
   existing architecture and its blast radius, not greenfield. (kata-graph requires tree-sitter; kata-readiness
   BLOCKs version-up without it.)
5. **Enumerate external dependencies:** list every library, tool, MCP server, or runtime the build needs
   and record each per `protocol/dependencies.md` (the Dependency Manifest). This list travels with the
   decision ledger to FREEZE, where it is approved and written to `kata.dependencies.json`; the PRE-FLIGHT
   phase (D29) provisions the approved set before the loop launches.

## Phase 1 — Interrogate, dependency-ordered

For each still-open branch, in dependency order, run the loop:
- **Pose** the choice-or-text question (format above) with your recommendation + rationale.
- **Probe — don't accept the first plausible answer.** Push on second-order consequences, the failure mode,
  and "what would break this?" A branch is not resolved until its *edges* are defined.
- **Stress-test with concrete scenarios.** Invent specific cases that force precise boundaries ("what does
  the system do when X and Y at once?"). Vague relationships hide here.
- **Sharpen language.** Any fuzzy/overloaded term → propose the one canonical word; the rest go under
  `_Avoid_` in the glossary. Challenge terms that conflict with the existing `CONTEXT.md`.
- **Cross-reference code/docs.** If the user's statement contradicts the code or a prior decision, surface it
  immediately and resolve which is right.
- **Re-derive the tree.** After each resolution, recompute what is now open/closed before the next question.

## Doc-baking — inline, not batched ([[STANDARDS]] §5; formats from grill-with-docs)

As each branch resolves, capture it *then and there*:
- **Glossary** (`CONTEXT.md`, glossary-only — no implementation): one tight definition per resolved term,
  with `_Avoid_:` synonyms. Create the file lazily on the first resolved term. (See `kata-context`.)
- **ADR** — offer one ONLY when all three hold: hard to reverse · surprising without context · the result of
  a real trade-off. Otherwise skip it. Sequential `docs/adr/NNNN-slug.md`, 1–3 sentences.
- **Decision ledger** — append every resolved branch (chosen option, rejected alternatives, rationale,
  provenance) to the running ledger. This is the raw material the FREEZE phase ([[kata-design-doc]]) compiles
  into the contract. See `resources/DECISION-LEDGER.md`.
- **Checkpoint after EVERY resolved branch** (append to the ledger *before* posing the next question) so an
  interrupted grill loses nothing — the ledger is the durable recovery point (GSD discuss-phase checkpointing).
- **User-cited docs:** when the user points to a doc/source mid-grill, read it, add it to the canonical
  references, and let it answer open branches before you ask more.

## Convergence criteria — the grill is DONE only when ALL hold

- [ ] Every enumerated branch is resolved with a chosen option + rationale (none left "TBD").
- [ ] No fuzzy/overloaded terms remain; the glossary is canonical for this work.
- [ ] Every probed scenario / edge case has a defined behavior.
- [ ] No unresolved contradiction with the code, the glossary, or prior ADRs.
- [ ] The design is specific enough that a competent executor could not *reasonably* drift on it
      (the operational test: could two independent builders read this and diverge? If yes, keep grilling).

If any box is unchecked, you are not done — return to Phase 1. Stopping early is the failure mode.

## Don't grade your own convergence (the structural backstop)

The criteria above are necessary but **self-assessed** — and the griller shares the exact bias that triggered
[[LESSONS-LEARNED]] L8: stopping at the first plausible answer and *believing* it sufficed. So before
declaring the grill done, hand the decision ledger to a **fresh-context adversarial check** ([[kata-review]],
in its "could two independent builders still diverge here?" mode). This mirrors the no-write evaluator in
EXECUTE — the one who did the work does not certify it. Only when that fresh pass returns SHIP is the grill
complete; a HOLD names the under-specified branch → back to Phase 1.

## The ELEVATE step (D153) — one grounded recommendation at every grill close

When the fresh convergence pass returns SHIP (Advanced: the final of its two passes), and strictly BEFORE the
grill-close emit below, pose **exactly ONE brainstormed recommendation that elevates the design or function of
the output** — a concrete improvement the resolved design does not already contain, **grounded in THIS run's
grill context** (cite the resolved branch(es), goal terms, or probed scenarios that motivate it). Generic
advice is a violation: if no grounded elevation exists, say so honestly in one line and record that (below) —
never invent filler (PD-2). More than one recommendation is offered ONLY if the operator asks. ELEVATE is
**always-on wherever a grill runs, at every tier** (same D33-class posture as the convergence gate — a tier
may scope the tree it grills, not the close-out behaviors); a `skip`-depth run has no grill and therefore no
ELEVATE. A Path-A hard bail ("execute" typed mid-grill) forgoes ELEVATE — stop means stop; a confirmed Path-B
close (the grill self-proposes readiness) is a NORMAL close and runs the full sequence: convergence pass →
ELEVATE → record → emit.

- **Interaction:** posed as ONE structured question through the same single-question binding as the rest of
  the grill (Claude: one `AskUserQuestion`) — the recommendation with its grounding, options **Accept (lock it
  in)** / **Decline**, free text always available. "Tell me more" ⇒ elaborate in-step, then re-pose the SAME
  question (no ledger entry of its own). "Give me another" ⇒ record #1 with Decision
  "Declined — superseded by request for an alternative (<reason if given>)", then pose the alternative as the
  next single question, recorded on its own `EV-{n}` entry. **ELEVATE is posed at most ONCE per grill close** —
  operator-requested alternatives occur WITHIN the single step; harness-initiated re-elevation is forbidden.
- **Recording (before the emit, always):** every outcome is a normal checkpointed ledger entry with a
  **dedicated `EV-{n}` anchor and a `· LOCKED` status token** — `### EV-{n} — Elevate: <short title> · LOCKED`
  — so the SB-L1 grammar emits it (`learn_feed._ANCHOR_RE` requires a digit/dash-segment anchor; a heading
  without one is not an entry and silently never emits; the anchor also names the emitted page, so never
  collide with an existing anchor). `EV-{n}` numbering is **per-ledger sequential**. **Title safety:** the
  `<short title>` must NOT contain `·` or `—` followed by a status word (locked/resolved/open) — the parser
  takes the FIRST status token on the line, so a title like "keep it — open by default" silently parses as
  status *open* and never emits. Decision field by outcome: **Accepted** ⇒ the recommendation (rationale =
  the operator's acceptance + the grounding; compiled into the frozen DESIGN like any other resolution);
  **Declined** ⇒ "Declined — <operator's reason>", or "Declined — no reason given" on a bare decline (never
  pose a follow-up question to extract a reason); **no grounded elevation** ⇒ the entry is
  `### EV-{n} — Elevate: none found · LOCKED` with Decision "No grounded elevation beyond the resolved
  design"; **accept-with-modification** ⇒ the operator's modified form, rationale noting the correction.
  Declines and the null result feed the second brain too — a decline is preference signal. A **Path-A bail**
  (no ELEVATE) still checkpoints one plain ledger line — "grill ended via operator 'execute' — Path A;
  ELEVATE forgone" — so an evaluator can distinguish a legitimate bail from an ELEVATE omission. Entry format
  incl. the EV shape: `resources/DECISION-LEDGER.md`.
- **If an acceptance opens genuinely NEW branches** (the exception — pose recommendations edge-defined):
  resolve them via the normal Phase-1 loop, then run a **scoped** fresh-context convergence check over ONLY
  those branches — one pass per attempt regardless of tier, re-run until SHIP; a HOLD sends the named branch
  back to Phase 1. On SHIP, resume at recording → emit — never a second ELEVATE. A **decline that reveals a
  genuinely unresolved branch** ("decline — but this makes me realize X is undefined") routes through the SAME
  machinery: resolve the revealed branch via Phase 1, scoped re-check, then recording → emit.

## Grill-close emit — feed the second brain (D151/G1)

The moment the fresh pass returns SHIP (on the acceptance-opened-branches path: the scoped re-check's
SHIP), the ELEVATE outcome (D153, above) is recorded, and the ledger checkpoints its final entry, this
grill's resolutions become second-brain signal — each resolved branch, the human's choice, and the rationale. When
`engram.learnFeed.dir` is set (kata.config / `protocol/config.md`), run the LEARN-feed emitter over the run's
ledger before handing off:

```
python tools/learn_feed.py --ledger <the run's GRILL-LEDGER.md> --decisions .planning/DECISIONS.md \
    --feed-dir <engram.learnFeed.dir> --log-path <kata_settings.default_learn_log_path(settings)> \
    --project <the target repo/project name> --kind <the run kind>
```

Pass `--decisions .planning/DECISIONS.md` only when that file is present. `engram.learnFeed.dir` unset ⇒
**no-op** (BC1 — the feed is purely additive; a run without a configured second brain behaves exactly as
before). If the feed dir is set but the settings-derived log path is absent (`vaultDir` unset), ask the
operator for a log path or skip the emit with a surfaced note — **never derive the log path from the feed
dir** (freeze-gate F-2). The emit **never blocks the grill close** — an emitter failure is surfaced and the
close proceeds.
Surface the emit report to the operator as one line (pages written / skipped-identical / redactions /
open-skipped). This step is what makes the D151 claim above true: the ledger feeds the second brain via
`tools/learn_feed.py`, and future grills read it back through recall's config-gated second-brain source.

## Handoff to FREEZE

Output = the **decision ledger** + the updated **glossary** + any **ADRs**. These are consumed by
[[kata-design-doc]] and [[kata-plan]] to produce the frozen DESIGN + PLAN. The grill never freezes the plan
itself — it makes freezing *safe*.
