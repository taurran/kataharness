# HANDOFF — Trust Model burn, EXECUTION window #2, mid-burn self-handoff (2026-08-17)

> **Written by the running conductor at the kata context gauge's 70% trigger** (kata-selfhandoff,
> task boundary = Loop-B integration). Supersedes the window-#1 handoff. Re-entry: read
> `protocol/prime-directives.md` → `.planning/ORIENTATION-EXECUTION-2.md` → the frozen
> `specs/trust-model/PLAN.md` → `specs/trust-model/OBSERVATIONS.md` IN FULL (it carries every
> ruling G1–G28, D-1..D-29, and all wave/loop records) → this file.

## Ground truth at handoff

- Conduct from `C:\dev\projects\_kata_wt\trust-model\conductor` (branch `burn/trust-model-01`).
  The main checkout may be a LIVE planning window — the two-window fence stands (OBSERVATIONS
  frontmatter). Shell cwd RESETS between commands — cd explicitly, always.
- **G19 (operator, recorded): waves 5–9 consolidated into FOUR back-to-back loops, run
  autonomously overnight; veto surface accumulates to the post-loop report.** Loop A =
  W5+detectors+close-machinery+doctrine · Loop B = corpora∥grounding∥EV-1 + stacked
  gate-preconditions · Loop C = hook-activation ALONE · Loop D = guardian-relabel. Hook LAST
  and relabel-after-hook stay frozen.
- **Waves 1–4 and Loop A: CLOSED, each with a fresh-context default-FAIL FINAL EVAL PASS**
  (records + the G26 CI strand D-28/D-29 in OBSERVATIONS). **Loop B: all five tasks
  judge-PASSED** (corpora cured 262f584; others first-round), five trailered merges +
  six conductor act commits in, validator 50 skills 0/0, spot-audit (the detector→fact-table
  composition + tamper refusal) PASSED live.
- **The live seam run:** runId `run-20260817T034343Z-e3b50e43`, kata dir `.kata/` in the
  conductor worktree. EVERY dispatch is minted+claimed through `kata_dispatch` (dogfood,
  Execution rule 4); judge verdicts captured via `capture()`; phases open/close per loop
  (`EXECUTION wave=6` is OPEN = Loop B). Enforcement remains **Honor-system — stated** until
  the Loop-C hook lands.

## Exactly where the loop stands (resume HERE)

1. **IN FLIGHT at handoff:** the re-run gauntlet on the Loop-B integrated tree (background)
   after the second tripwire catch (kata-grounding classified into
   `NON_JUDGE_EVALUATE_SKILLS`, commit on the branch). On 4/4 green:
2. Append the staged Loop-B record + DEF-23..28 (scratchpad files `loop-b-record.md`,
   `defs-loop-b.md` — re-create from OBSERVATIONS context if lost) with the gauntlet figures,
   commit, push.
3. `gh workflow run gauntlet --ref burn/trust-model-01` + watch (the G26 precedent: a red CI
   is root-caused via a stacked fix task, never waved through).
4. Loop-B FINAL EVAL: fresh-context default-FAIL judge (Explore agent, anchor model), minted
   through the seam, over the whole loop; on PASS close `EXECUTION wave=6`, open wave=7.
5. **Loop C — hook-activation ALONE** (frozen W8 block + `evidence/hook-probe.md` OBSERVED
   facts binding: deny-on-internal-error, matcher says "Agent" never "Task", capture needs
   PostToolUse+SubagentStop BOTH, run-marker scope, settings digest, timeout below host's).
   Builder Opus, worktree off the Loop-B-final tip. Its sink row MUST land in
   protocol/exec-safety.md (the ev1 scan already reaches adapters/**/hooks/ — a missing row
   fails the validator). Gate includes the live `probe:deny-tripwire`; run-start declaration
   flips per probe results ONLY. Wave gate = final eval including the live tripwire result.
6. **Loop D — guardian-relabel** (frozen W9 block + ruling G27: it gains
   `tools/badge_registry.json`; every BUILT—Verified mark needs a registry row with a live
   check in the same commit; the two pending_graduation rows route through promise-audit
   finding 8; observability.md's 6 stale board.md refs + 5 stale anchors are its DEF-22 leg).
   **BACKLOG.md leg: the planning-window fence has NOT been verified lifted — file the
   truth-status table via OBSERVATIONS + park that leg (GATE-PLAN ruling 2).**
7. **Program close:** `kata_close.close_run` over the burn's own cursor (Honor-system-declared
   conductor capture legs; consent PARKS if prompted unattended — expected, surface it).
   Close still-open phases LIFO (G25: most-recently-opened FIRST).
8. **The post-loop report to the operator** (they are asleep; they want the full story on
   waking): lead plain-language what-changed-and-why; the complete VETO LEDGER (all G3-class
   pastes incl. cursor.md `efdaf047…` and doctrine `47d6a52b…`, G18 six re-approvals, rulings
   G12–G28, the D-25/§1.5 erratum + D-8/D-9 standing items, DEF-1..28 dispositions, the open
   `deny-probe-w4-cure` escalation); the honest labels (what is wired vs built-but-unwired:
   DEF-15 allowed= wiring, DEF-24 gate wiring, fact-table consumer); CI citations per loop;
   the lessons list (R14 narration-is-not-evidence, E7 bare-backticks, registry-tables-not-
   prose, the six-instance divergence family D-25..D-29). Then STATE.md + orientation #3 (or
   closeout) per the window's report contract.

## Standing rules the resumer must not re-derive

Judges: fresh-context Explore agents, no-write, default-FAIL, `VERDICT:` first line
(PASS|NEEDS_WORK), minted as role=evaluator; cures go back to the SAME builder agent
(SendMessage), re-verdict by the SAME judge. Builders: Opus (anchor for dispatch_class
critical), briefs staged as scratchpad files passed by path, R14 rider + E7-bare-backticks +
registry-tables-not-prose in every brief. Integration: merges via `-F <file>` (never `-F -`),
`Kata-Task:` trailer integration-only + verified post-merge; G2 README `--write` once per
loop; fingerprint pastes re-derived on the integrated tree first; G9 registry rows conductor-
pasted after invariant re-verification. G11: concurrency suites ≥10× (fresh processes).
`$?` after a pipe is the TAIL's exit — never pipe a gate then echo `$?` (bitten live this
loop). Windows: `uv run --project tools python` (bare python is the Store stub).

## Agent roster at handoff (SendMessage ids, may be stale after reset)

corpora builder+judge, grounding builder+judge, ev1 builder+judge, gate-preconditions
builder+judge: all task-complete/verdict-delivered. The judge-contracts builder (also served
G16/G28 flips) and the rotation-fix builder are idle-complete. If a resumed session lacks
these ids, dispatch fresh agents — all durable state is in git + OBSERVATIONS + `.kata/`.
