---
date: 2026-07-02c (Milestone 1 MERGED to master · Freeze/Float M1 P0+P1 built + reviewed SHIP · HELD before M1-P2)
branch: freeze-float/m1-contract-edges (rebased onto merged master 8653faf; UNPUSHED; tip 46c7601)
green: validator 47/0 · pytest 2236 passed / 3 skip (-m "not integration") · Snyk medium+ 0  (at the freeze-float tip)
tags: kenjiri-lessons · D137 · freeze-float · contract-edges · M1-P0 · M1-P1 · D138 · sanctioned-M2 · handoff
authored-for: a fresh coding-agent window (sections map to the kata-orient tiers)
★ NEXT-SESSION START HERE: read `.planning/NEXT-SESSION-ORIENTATION.md` (self-contained, paste-ready). Milestone 1
  is MERGED. **Freeze/Float is the OPERATOR-DIRECTED Milestone 2 (D138) — do NOT re-question its legitimacy** (it is
  now recorded in ROADMAP/BACKLOG/STATE). M1-P0 (contract_edges engine) + M1-P1 (kata_restore durable substrate) are
  built + reviewed SHIP + committed (unpushed). Next is M1-P2 (the float) — HELD; it needs its own adversarial
  freeze-gate + operator go. First actions: confirm green → ask operator (push branch? open P2?) → do NOT shortcut P2's freeze-gate.
---

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
