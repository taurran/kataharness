---
date: 2026-07-26
kind: manual
trigger: operator-requested session refresh ("handoff to a new session")
branch: docs/mergeback-ingest-itemization @ pushed · master UNTOUCHED at fcb0338
green: pytest 4106 / 3 pre-existing skip · integration 2/2 · ruff clean · validator 49/0/0 · Snyk 0 med+
authored-by: the outgoing session, by hand
---

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
