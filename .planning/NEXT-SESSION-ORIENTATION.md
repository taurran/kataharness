# NEXT-SESSION ORIENTATION — written 2026-08-04 (branch `master`)

> **Copy the block below the rule.** Plain text, no fences, so it pastes clean into a new session
> after `/clear`. Terminal step first, and ONLY if you are opening a new window:
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
  git rev-parse --abbrev-ref HEAD                 -> master
  git rev-parse --short origin/master             -> e0eebae   (or later)
  cd tools && uv run python scripts/gauntlet.py   -> 4/4 PASS
  (use `uv run` — the .venv python false-reds 2 integration tests offline)

WHERE THINGS STAND
EVERYTHING IS ON MASTER. No open PRs, no unpushed commits. The long-running
grill/session-lifecycle branch and the MindBridge ingest branch both merged on
2026-08-03. If you were told to expect a815c2b, an unpushed branch, or open PRs
#51/#53, that guidance is SUPERSEDED — it was true on 2026-08-02 and is not now.

Nine items have shipped. The last two, on 2026-08-04:
  - every protocol contract is now guarded, AND the protocol folder polices itself:
    a new file there must be registered or explicitly exempted, or the build fails.
    Eight contracts had NO protection at all, two of them safety contracts.
  - the version-bump rule is real: edit a skill without bumping it and the build
    fails naming it. CI needed fetch-depth: 0 or the check would have reported
    green while checking nothing.

ONE THEME RUNS THROUGH ALL NINE: a rule written in a document with nothing in code
enforcing it. Expect to keep finding that shape — it is the most reliable defect
generator in this repo.

DO NOT INVENT A NEXT ITEM. Section 2 of the handoff lists real candidates; pick with
the operator.

FOUR THINGS THAT WILL BITE YOU IF YOU SKIP THEM

1. The grill in .planning/specs/session-lifecycle/ is HELD after three convergence
   passes (9 -> 13 -> 12 HIGH). SL-1..SL-36 must NOT be compiled into a DESIGN.
   Several carry a "LOCKED" token and are still WRONG — that token records that a
   branch was decided, not that it survived review. CONVERGENCE-HOLD-{1,2,3}.md are
   authoritative wherever they disagree with the ledger.

2. READ .planning/DECISIONS.md — do not measure it. 2700+ lines of binding law. The
   held grill above failed three times for exactly one reason: it treated that file
   as a parse target. D135 forbids a second append-only journal; D133/D142 scope the
   git carve-out to board-only; D74 makes redaction a hard pre-write gate; D81 makes
   .kata/ disposable. Any of those will silently invalidate a design.

3. Protocol contracts are clause-pinned AND fingerprinted — 23 registered, 21
   fingerprinted. Editing one turns the suite red until you review your own diff and
   re-approve via `uv run python validate_skills.py --update-protocol-fingerprint`.
   That is the machinery working, not a bug. The updater prints; it never writes.
   TWO files are deliberately fingerprint-exempt because they are registries that
   must grow with the code: config.md and exec-safety.md. Both are still
   clause-pinned. Do not "fix" that asymmetry — it is load-bearing, and exec-safety's
   sink registry was resynced on 2026-08-04 at zero approval cost because of it.

4. NEVER use a PowerShell Get-Content/Set-Content round-trip to edit a repo file.
   It reads UTF-8 with the ANSI codepage and rewrites it double-encoded, corrupting
   every em-dash and adding a BOM. This happened on 2026-08-04 (repaired in faf2ede).
   Use the editor tooling. Same class: kata_telemetry._run_git uses text=True with
   no encoding, so it must NEVER be used to read file CONTENT — it mojibakes every
   non-ASCII file on Windows, and all 49 SKILL.md files are non-ASCII. Use
   footprint.blob_at_ref, which returns bytes.

HOW TO WORK HERE
protocol/orchestration.md is binding: "A well-behaved orchestrator does not do the
work itself." Dispatch builders against a tight frozen brief; gate what returns
default-FAIL using protocol/authored-artifact-gate.md's six rows. Verify, never
trust the worker's summary — read the diff, re-run the gate yourself, and reproduce
the evidence INDEPENDENTLY using different cases than the builder used.

That last point earned its place on 2026-08-04. A builder reported that the frozen
contract's rename-detection mechanism did not work and that it had substituted a
better one. Reproducing it confirmed the contract was wrong and the builder right —
git reported a moved-and-rewritten skill as plain delete+add, so it would have
laundered into "new and exempt". A conductor who accepted the summary, or who
insisted on the spec, would have shipped an open bypass either way.

ALSO BINDING, PD-2: "Done requires proof, not assertion." Cite gate numbers, paths
and SHAs — never confidence. The fresh-context convergence gate caught the conductor
asserting two things that were simply false: that CLAUDE.md contains a count it does
not contain, and that the validator ships with the skill suite when its own line 2
says it does not. RUN THAT GATE. Do not grade your own convergence.

OPERATOR PREFERENCES
Plain English, always. Never a bare work-item code — always pair KH-T02 / BL-F01 /
T-01 with a plain description of what it actually is. Asked for repeatedly, with
visible frustration. Do not over-complicate: prefer the smallest change that closes
the defect, and say plainly WHICH task is being delivered.

MindBridge is OUT OF SCOPE by operator direction. Pre-existing mentions in older
planning docs are history, not queue items. But NOTE: "out of scope" drops the
MindBridge chores, NOT the ingest documents — INGEST-EXECUTION-ORDER.md,
INGEST-PLAIN-ENGLISH.md and BACKLOG-FROM-MINDBRIDGE.md carry the live work queue.

OWED TO THE OPERATOR — surface these, do not silently carry them
  - Rotate the GitHub PAT: plaintext at settings.json -> env ->
    GITHUB_PERSONAL_ACCESS_TOKEN, exported into every spawned process.
    DEFERRED by the operator 2026-08-02. Deferred is not dropped.
  - DEF-2's undecided question, and it BLOCKS a cheap fix: learn_feed silently drops
    entry bodies (measured: 20 of 29 entries, 19,153 chars). The publish step fires
    at every grill close and 19 ledgers share the style. Does the block extend to all
    19? Until answered, NO grill-close emit runs. Its one-line sibling BL-M24 (the
    heading regex counts the ledger's own H1, still ^#{1,6}) is in the same file and
    should be fixed in the same run.
  - T-03 scope call: all six determinism laws, or the 13+15 subset.

Section 3 DECISIONS in the handoff are settled; do not re-litigate. Start from
section 2 NEXT STEP, and pick the next item WITH the operator rather than assuming
one.
