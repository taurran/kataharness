# NEXT-SESSION ORIENTATION — written 2026-08-02 (branch `grill/session-lifecycle`)

> **Copy the block below the rule.** It is plain text, no fences, so it pastes clean into a new
> session after `/clear`. Terminal step first, and ONLY if you are opening a new window:
>
> ```
> cd C:\Dev\projects\kataharness
> ```
>
> The authoritative state is `.planning/HANDOFF.md`; this file is the paste companion.

---

Read .planning/HANDOFF.md in full — it is the authoritative state. Then read
.planning/STATE.md's CURRENT block. Do not read STATE.md wholesale (1400+ lines).

VERIFY BEFORE ACTING. Stop and report on any mismatch:
  git status --porcelain                          -> empty
  git stash list                                  -> empty
  git rev-parse --short origin/master             -> a815c2b
  git rev-parse --abbrev-ref HEAD                 -> grill/session-lifecycle
  cd tools && uv run python scripts/gauntlet.py   -> 4/4 PASS
  (use `uv run` — the .venv python false-reds 2 integration tests offline)

WHERE THINGS STAND
The backlog queue that drove this branch is CLEAR. Seven items shipped, each
dispatched to a builder and gated default-FAIL by the conductor: the Prime
Directives hardened across all 13 protocol contracts, destructive crash recovery
fixed, stale gate evidence blocked, the thin-orchestrator doctrine made binding,
design/plan authoring turned into dispatched roles with a rubric to gate them, and
"frozen" made a recorded state that blocks dispatch.

One theme ran through all seven: rules that existed only as prose with nothing
enforcing them. Expect to keep finding that shape.

DO NOT INVENT A NEXT ITEM. Section 2 of the handoff lists real candidates; pick with
the operator. The only thing actually blocking is 8 unpushed commits and the PR
decisions.

THREE THINGS THAT WILL BITE YOU IF YOU SKIP THEM

1. The grill in .planning/specs/session-lifecycle/ is HELD after three convergence
   passes (9 -> 13 -> 12 HIGH). SL-1..SL-36 must NOT be compiled into a DESIGN.
   Several carry a "LOCKED" token and are still WRONG — that token records that a
   branch was decided, not that it survived review. CONVERGENCE-HOLD-{1,2,3}.md are
   authoritative wherever they disagree with the ledger.

2. READ .planning/DECISIONS.md — do not measure it. It is 2700+ lines of binding
   law. The held grill above failed three times for exactly one reason: it treated
   that file as a parse target. D135 forbids a second append-only journal; D133/D142
   scope the git carve-out to board-only; D74 makes redaction a hard pre-write gate;
   D81 makes .kata/ disposable. Any of those will silently invalidate a design.

3. protocol/prime-directives.md and 11 other protocol files are clause-pinned AND
   fingerprinted. Editing one turns the suite red until you review your own diff and
   re-approve via `uv run python validate_skills.py --update-protocol-fingerprint`.
   That is the machinery working, not a bug. The updater prints; it never writes.

HOW TO WORK HERE
protocol/orchestration.md is binding: "A well-behaved orchestrator does not do the
work itself." Dispatch builders against a tight frozen brief; gate what returns
default-FAIL using protocol/authored-artifact-gate.md's six rows. Verify, never
trust the worker's summary — read the diff, re-run the gate yourself, reproduce the
mutation evidence, confirm every flagged deviation, and reject anything that retires
a frozen invariant. That last row is what caught the one rejection on this branch,
where the fault was in the conductor's own brief.

Also binding, PD-2: "Done requires proof, not assertion." Cite gate numbers, paths
and SHAs — never confidence.

OPERATOR PREFERENCES
Never write a bare work-item code. Always pair KH-T02 / BL-F01 / DEF-2 with a plain
description of what it actually is. This has been asked for twice.

MindBridge is OUT OF SCOPE by operator direction. Pre-existing mentions in older
planning docs are history, not queue items.

OWED TO THE OPERATOR — surface these, do not silently carry them
  - Rotate the GitHub PAT: plaintext at settings.json -> env ->
    GITHUB_PERSONAL_ACCESS_TOKEN, exported into every spawned process.
  - 8 commits committed locally and NOT pushed.
  - PR #51 (MindBridge ingest, 26 commits) and PR #53 (stacked on it). WARNING:
    grill/session-lifecycle CONTAINS #51's commits, so merging this branch to master
    merges #51 as a side effect. That decision is the operator's, not a side effect.
  - DEF-2's undecided question: does the learn_feed emit block extend to all 19
    ledgers?

Section 3 DECISIONS in the handoff are settled; do not re-litigate. Start from
section 2 NEXT STEP, and pick the next item WITH the operator rather than assuming
one.
