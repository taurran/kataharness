# protocol/authored-artifact-gate.md — the conductor-gates-what-it-did-not-author rubric (KH-B42)

A cross-skill contract enforcing the check the conductor applies to **any artifact it did not author itself**
and is about to write into the main tree. This is the canonical source of truth; responsible skills and the
conductor reference it by path (`protocol/authored-artifact-gate.md`), never by `[[wikilink]]`. Companion to
`protocol/reuse-claims.md` (LD3 verify-before-reuse) — this rubric is the sibling check for the artifact as a
whole, not just its reuse claims.

## Purpose

`protocol/orchestration.md` binds the conductor to a plan-guardian posture: *"you dispatch, gate, and route;
you do not author the code, tests, design doc, or plan under your own gate."* KH-T13 (`protocol/config.md`'s
`roles` schema, `design-author`/`plan-author`) makes that literal for the two documents that used to be
authored in the same session that later gates them: `DESIGN.md` and `PLAN.md`. The moment authoring is
dispatched, the conductor must gate an artifact it did not write — and this file is the rubric it applies
when doing so. It is written as a **six-row table**, following the `protocol/reuse-claims.md` shape (Purpose /
the guard / a table / producer sites) — same genre of document, same house style.

## The guard — six rows, applied to a returned `DESIGN.md` or `PLAN.md`

Each row states the check, the evidence that satisfies it, what a FAIL looks like, and whether it is
**mechanical** (a command or a grep either finds the defect or it does not) or **judgment** (a human-grade
reading call — see the honesty note below).

| # | Row | What is checked | Evidence that satisfies it | FAIL looks like | Kind |
|---|---|---|---|---|---|
| 1 | **SCOPE** | The author touched only its declared `owned_files` (one file: the returned `DESIGN.md` or `PLAN.md`) inside its own worktree. | `git diff --stat` (or worktree file listing) against the brief's `boundaries.ownedFiles` shows exactly the one file, nothing else. | The worktree diff includes a second file, a code file, or a change outside the worktree. | **Mechanical.** |
| 2 | **CLAIM vs ARTIFACT** | The conductor reads the returned **file itself** — never the dispatch payload's self-reported `verdict` as a substitute for reading it. | A record that the conductor opened the file at the returned path (`designPath`/`planPath`) before writing anything into the main tree. | The conductor writes the artifact into the main tree on the strength of the payload's `verdict` field alone, without having read the file. | **Mechanical to confirm the file was opened; judgment to assess what it says** (split row). |
| 3 | **CITATIONS RESOLVE** *(the design-document analogue of GATE RE-RUN)* | Every `file:line` citation in the artifact is independently re-opened by the conductor, not trusted because the author claims it checked. | The conductor re-greps/re-reads each cited `file:line` and confirms the cited text exists. | A citation points at a line that does not say what the artifact claims, or does not exist. | **Mechanical for existence** (grep resolves or it does not); **judgment for whether the cited text actually supports the claim.** |
| 4 | **NO UNCITED REUSE CLAIM** *(the design-document analogue of EVIDENCE VERIFIED, per `protocol/reuse-claims.md`)* | Every "reuses / composes / via the existing X" sentence carries a cited `file:line` exposing the exact surface assumed. | `protocol/reuse-claims.md`'s guard applied by the conductor: grep the phrase pattern, confirm each hit has an adjacent citation. | A reuse claim with no citation, or a citation that names a file but not the specific field/event/output/path assumed. | **Mechanical to detect an uncited claim; judgment to confirm a cited one actually substantiates it.** |
| 5 | **DEVIATIONS CONFIRMED** *(frozen decisions are cited and not contradicted)* | Every decision the artifact states as LOCKED is checked against the real ledger/`DECISIONS.md` entry it cites, and every deviation the author self-flagged (`deviations`) is independently checked against the ledger — never accepted at face value. | The conductor opens the cited ledger/`DECISIONS.md` entry for each LOCKED decision and each self-flagged deviation, and states whether it confirms or contradicts. | The artifact states a decision as LOCKED that the cited entry does not actually support, or a self-flagged deviation goes unchecked. | **Judgment** — comparing stated text to ledger semantics is not mechanically decidable. |
| 6 | **NO FROZEN INVARIANT RETIRED** *(every decision has defined edges; could two independent builders read this and diverge)* | The artifact does not silently weaken, retire, or leave ambiguous a Prime Directive, a `protocol/orchestration.md` clause, or a decision `DECISIONS.md` marks LOCKED — and every LOCKED decision it restates is specific enough that two independent readers could not diverge on it. | A read-back that (a) checks the artifact against the pinned/fingerprinted clauses in `protocol/prime-directives.md` and `protocol/orchestration.md`, and (b) asks, for each LOCKED decision restated, "could a second builder read this and build something different?" | An invariant is quietly narrowed ("stub it for now" reworded as a LOCKED decision), or a decision is restated vaguely enough that two builds could diverge. | **Judgment — explicitly not mechanically provable**, same posture as `protocol/orchestration.md`'s own honesty clause: *"no check can prove a conductor never touched the keyboard it shouldn't have."* |

## Applying the same six rows to a returned `PLAN.md`

The rubric is one table, not two — a `PLAN.md` gate re-reads the same six rows with plan-specific evidence:
row 1 (scope) still checks the one owned file; row 3 (citations resolve) covers every `owns:`/file-path the
plan names, confirming the file exists and the ownership does not collide with another task's; row 4 (no
uncited reuse) applies to the plan's own reuse claims about existing tooling; row 5 (deviations confirmed)
checks that every task's `depends_on`/wave placement matches the DESIGN it was built from; row 6 (no invariant
retired) checks that no task silently narrows an acceptance criterion the DESIGN stated. No new rows are
needed for `PLAN.md` — this is stated explicitly so a future reader does not invent a second rubric.

## Honesty note — do not overstate enforcement (PD-2)

Rows 1 and 3's existence-check half, and row 4's uncited-claim-detection half, are genuinely mechanical: a
`git diff` or a `grep` either finds the violation or it does not, and that half can be a real command a future
task could script. **Rows 2 (content), 3 (citation-supports-claim), 5, and 6 are judgment** — the same class
of check `protocol/orchestration.md` already names as binding but "NOT mechanically provable." This rubric
does not claim it makes gating a design doc as mechanical as re-running a test suite; it claims the six checks
are now **named, ordered, and traceable to the defects that motivated each one** — which is the improvement
PD-1/PD-2 ask for (never silently defer, never overstate what is proven).

## Provenance — the empirical basis (do not re-derive)

The six rows above are the checks that caught real defects while the conductor gated four dispatched builds
already merged on this branch (`KH-T02` — `4f16cbc`/`0a44bc2`; `T-04` — `bf163fd`; `BL-M21` — `2828040`;
`KH-T12` — `6d02f1e`, per this branch's own `git log`). This file is the rubric's durable home; the
provenance is recorded here, not re-derived from first principles at each site that references it.

## Producer sites

| Site | Skill / artifact | Role |
|---|---|---|
| **Conductor freeze gate** | `kata-orchestrate` (Integration & gate) | Applies the six rows to a returned `DESIGN.md`/`PLAN.md` before writing it into the main tree — the primary gating site. |
| **Design freeze dispatch** | `kata-design-doc` (Precondition/Output) | Names this file as the contract the `design-author` role's output will be gated against. |
| **Plan freeze dispatch** | `kata-plan-essential`/`-standard`/`-advanced` (Precondition) | Names this file as the contract the `plan-author` role's output will be gated against. |

`kata-grill` is explicitly **not** a site — it resolves decisions with the human; it does not author or gate
a frozen artifact.
