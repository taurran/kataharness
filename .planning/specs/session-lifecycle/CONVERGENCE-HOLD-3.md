# CONVERGENCE GATE — PASS 3 · **HOLD** (2026-07-27)

> Fresh-context, no-write adversarial pass over the SL-29..SL-36 repairs.
> **VERDICT: HOLD — 12 HIGH remain open.** Eight repairs produced twelve new HIGH findings.
> **Third consecutive HOLD. The compounding ratio held all three times.**

## Verified TRUE (the repairs' grounding held where it was checked)

The canonical board reduce reads **only** `CLAIM`/`DONE` (`board.md:96-102`) — **SL-6's original
rejection of the board WAS factually wrong**, as SL-29 claimed · D135's quoted text is verbatim
(`DECISIONS.md:1952-1965`) · D74 is frozen as a HARD fail-closed pre-write gate (`:532`) ·
`engram.md:159-164` does scope D151/G4 to the loop feed only · `kata_telemetry._run_git:163` pins
only `core.quotepath=off` + `log.showSignature=false` — **not** `log.follow=false` ·
`learn_feed.py:74` is stdlib-only/no-subprocess · `learn_feed.py:511-518` does drop body ·
`HANDOFF.md` has 65 commits, no renames.

## Verified FALSE (premises the repairs were built on)

| claim | reality |
|---|---|
| FLOOR "carries no redaction surface by construction" (SL-30) | **FALSE.** `§1 POSITION` carries the **board tail** — which SL-29 just routed model narrative onto — and `§2` carries commit messages. Live `HANDOFF.md:26` `§0` holds an absolute host path plus free prose. |
| FLOOR "cannot be stubbed because generated" (SL-31) | **FALSE.** Live `§0` is hand-typed: **6** commands vs the template's 5, an absolute path, and a `uv run` warning with no template slot. |
| rotation archives, "nothing is lost" (SL-29) | **FALSE.** `board.md:47-48` and `kata-orchestrate:314-315` both read *"archive.md **(or truncate it)**"*. |
| "parked via `kata-defer` → `DEFERRED.md`" (SL-35) | **FALSE at the time of writing.** No entry existed. ✅ **Now corrected — `DEF-2` written 2026-07-27.** |
| "Corrected count: 29, not 18" (SL-36) | **FALSE.** `grep -c "^### SL-"` → **36**. A miscount inside the entry correcting miscounts. |

## The two that indict Phase 0 again

**N-10 — D67 was never cited by any of 36 entries.** `DECISIONS.md:459-463`, an explicit **D33-class
invariant**: the handoff carries the loop map (*"no ownerless edges"*) and a **never-summarized
invariant block** `{frozen-plan ref, goals, open decisions, open escalations}`. SL-21's eleven
sections have no home for *frozen-plan ref* or *goals*, and none is marked never-summarized.
Independently: `protocol/handoff.md` is 64 lines and **contains no loop map at all** — and it is the
file SL-21 rewrites.

**N-12 — the section contract was specified against a document shape the grill never measured.**
`.planning/HANDOFF.md:151` — *"↓ PRIOR HANDOFF BLOCKS — history, preserved per repo convention"*.
The file **accumulates** whole prior handoffs with old-scheme sections below. Nothing in
SL-21/SL-25/SL-31/SL-36 scopes the contract, the by-name cross-references, the citation gates, or
*"first-appearance order within the document"* to the newest block. `kata-handoff/SKILL.md:81` says
refresh *"overwrites"*, contradicting the file's own stated convention — an unresolved contradiction
in the artifact this grill read first.

## Remaining HIGH findings

**N-1 (SL-33)** the same-commit rule is a **new autonomous-git path** — `kata-loop/SKILL.md:138`
forbids autonomous git; D133 permits ref-only, board-only; **D142(b): "NO new autonomous-git path…
board→`refs/kata/trail` ONLY."** SL-33 stages and commits three source files to a branch — strictly
broader than the path SL-29 rejected one entry earlier, with no human turn at auto-compact ·
**N-2/N-3 (SL-30)** the floor *does* carry redaction surface, and a redaction HIT on **depth** has no
defined outcome; `engram.md:156` records §7 is *"a **prose contract** … 'fail-closed' is an
instruction, not an enforced guarantee"* — no scanner is named · **N-4 (SL-29)** rotation may
truncate, reversing SL-13(2)'s **verified** warning without argument · **N-5 (SL-29)**
`board.md:45-46` states a literal **MUST** (*"only the current run's events"*); SL-29 rebuts the
consequence, never the rule, and `concurrency.json`'s emitted provenance string becomes false ·
**N-6 (SL-29+SL-32)** CA-L19 keys staleness on `DONE`/`DECISION`; depth lands in `NOTE`, so **depth
NOTEs can never demote the handoff** — NEW-6 relocated from the left operand to the right ·
**N-7 (SL-34)** Doctrine law 1 is titled *"One pinned git helper"* and says *"**Never re-derive the
pin set per call-site**"*; the two cited sites are listed as *"adoption-time stragglers DET-02..05
RESOLVED"* — grandfathered, not the pattern. SL-34 adopts exactly what law 1 forbids, and law 1
names **five** pins where both sites inline three · **N-8 (SL-35)** the deferral did not exist, and
whether the emit block is repo-wide across all 19 ledgers is undecided · **N-9 (SL-32)** the
`depth:` operand is **undefined at bootstrap** (no commit carries it) and the entry calls the field
both *"never gates"* and the gating operand in one sentence · **N-11 (SL-31)** directly contradicts
SL-25 on whether `kata_handoff_break` renders `§0`; the live artifact refutes the generated claim ·
plus **N-13..N-17** (board line grammar cannot carry multi-paragraph depth and assigns `NOTE` to
workers; retrofit miscount + unnamed "subject-page builder"; tracked-but-modified sources; a
MANDATORY migration with no mechanism; D74's frozen `§7` anchor silently re-pointed under
supersede-never-rewrite).

---

## Verdict on the process, not just the artifact

Three passes. Three HOLDs. **9 HIGH → 13 HIGH → 12 HIGH.** Each repair round consumed the previous
round's findings and generated a comparable number of new ones, because each round specified against
premises that had not been measured — first `DECISIONS.md`, then the live `HANDOFF.md`'s actual file
shape, then the Doctrine's own law-1 text.

**The grill's QUESTIONS and the operator's RULINGS on them are sound and survive.** What does not
survive is this session's attempt to convert them into an executable contract. That work needs a
Phase 0 that reads `DECISIONS.md` (D67/D74/D81/D133/D135/D142/D151), `docs/DETERMINISM-DOCTRINE.md`
law 1, `protocol/board.md`'s MUST and rotation clauses, and the **actual shape** of
`.planning/HANDOFF.md` — before a single entry is written.
