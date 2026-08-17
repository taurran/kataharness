# protocol/cursor.md — the CURSOR: one durable temporal record per run

Canonical grammar for the run's one log — the **cursor** — consumed by [[kata-cursor]] and
[[kata-orchestrate]]. Machine state — kept separate from durable Obsidian docs ([[STANDARDS]] §5).

**The concept is the CURSOR**: it marks where in the process the run is sitting and where it is
currently executing. This contract file and its skill completed the heritage rename
(`protocol/board.md` → `protocol/cursor.md`; `skills/coordinate/kata-board` → `kata-cursor`; the
`REQUIRED_PROTOCOL` registry key moved with them). **Two heritage names deliberately REMAIN, and
this is stated rather than tidied away:** the runtime file is still `.kata/board.md` and the engine
module is still `tools/kata_board.py`. No frozen task renames either one, and renaming a runtime
path or an importable module is a code change, not a doc change — so the names below are the true
ones, not aspirational. Everything here is the cursor contract.

- **Location:** `.kata/board.md` in the target repo's integration worktree (heritage filename; the
  cursor is what it holds).
- **Append-only:** agents append lines; no agent edits or deletes a prior line (no last-writer clobber —
  [[LESSONS-LEARNED]] L3).
- **One log per run.** No sidecar structured log, no second journal, no git-only cursor.
- **Engine:** `tools/kata_board.py` is the single writer and the single canonical parser (heritage
  module name, above). Nothing hand-rolls this grammar; a second parser is a second source of truth.
- **Seam-authored lines come from `tools/kata_dispatch.py`**, never from a hand-written append:
  `phase()` writes PHASE, `capture()` writes VERDICT/DOWN, `mint()` writes SPAWN, `deny()` writes
  DENY. Those five functions are the only legal authors of the seam TYPEs below.

## The grammar

```bnf
cursor        ::= run-header line*
run-header    ::= "RUN " run-id NL
                  ( "prev-run: "     run-id  NL )?     ; iteration chain (re-loop/loop-back)
                  ( "parent-run: "   run-id  NL )?     ; tree structure (child runs)
                  ( "prev-segment: " path    NL )?     ; chained segmenting (RESERVED NOW,
                                                       ;   built when a real cursor gets big)
run-id        ::= "run-" utc-compact "-" hex+          ; sortable, humane; randomness
                                                       ;   mints identity only (Determinism
                                                       ;   Doctrine)
line          ::= utc FS seq-field FS agent-id FS type FS task-id FS msg NL
FS            ::= " | "
seq-field     ::= seq ( "~" parent-seq )?              ; parent-seq = dispatch lineage: the seq
                                                       ;   of the SPAWN line this line descends
                                                       ;   from (worker-line lineage stamps)
seq           ::= digit+                               ; monotonic per run
type          ::= worker-type | orch-type | seam-type
worker-type   ::= "CLAIM" | "DONE" | "BLOCK" | "ESCALATE" | "NOTE" | "PROGRESS"
orch-type     ::= "DECISION"
seam-type     ::= "PHASE" | "VERDICT" | "SPAWN" | "DOWN" | "DENY"
msg           ::= one-line-text ( " payload=" path )?  ; pointed-to JSON payload (escalation
                                                       ;   idiom); REQUIRED for VERDICT
```

`utc-compact` is `%Y%m%dT%H%M%SZ` — the run id therefore sorts chronologically as a plain string.

**The old 5-field grammar parses NOWHERE.** A line of the pre-migration form
`<utc> | <agent> | <TYPE> | <task> | <msg>` is a parse **REFUSAL**, never a silent skip, and a
legacy line inside an otherwise valid cursor aborts the whole parse. This is deliberate: a silently
skipped row is an invisible hole in the audit trail, which is the failure class this contract exists
to remove.

A legacy row whose `msg` happened to contain ` | ` presents as six fields, so the field count alone
does not catch it. Two gates do the work: the digits-only `seq` field is the **primary**
discriminator (a legacy row's field 2 is an agent id, which is normally not all digits), and the
closed TYPE enumeration at field 4 is the **second** gate that fires when field 2 *is* numeric —
because the check then lands on what was the legacy task-id. **Honest residual:** a legacy row that
satisfies both — an all-digits agent id, a task-id that is literally one of the TYPE tokens, and a
` | ` inside its msg — would parse as a well-formed cursor line with shifted fields. No mechanical
check here closes that; the migration is what closes it, by leaving no legacy rows to read.

## TYPE vocabulary and writer classes

Three writer classes, disjoint. A writer never authors another class's TYPE.

| TYPE | Writer class | Meaning |
|---|---|---|
| `CLAIM` | worker | worker self-stamped start of a task — appended by the worker to the shared `.kata/board.md` at the integration/target-repo root (not the per-task worktree's `.kata/`) |
| `DONE` | worker | worker self-stamped end of a task — appended after task `<verify>` passes; signals ready for the orchestrator gate |
| `BLOCK` | worker | cannot proceed (environment/dependency) |
| `ESCALATE` | worker | the frozen plan is unclear/wrong — needs an orchestrator decision (never re-plan) |
| `NOTE` | worker | lateral info for peers |
| `PROGRESS` | worker | mandated liveness heartbeat (F3); `msg` carries `<modulesDone>/<modulesOwned> <label>` (e.g. `3/5 writing tests`) — the structured progress signal the liveness monitor and Freeze/Float M4 slack-timing read |
| `DECISION` | orchestrator only | a deliberate ruling resolving a BLOCK/ESCALATE |
| `PHASE` | seam only | a Kata-Loop phase event (open/close/run-closed) |
| `VERDICT` | seam only | a judge/arm verdict captured from a return envelope — **REQUIRES a payload pointer** |
| `SPAWN` | seam only | a dispatch was minted; the lineage anchor `~parent-seq` stamps point at |
| `DOWN` | seam only | a child run reached a terminal state, with reason |
| `DENY` | seam only | a launch was refused, naming the legal path |

- **Seam-authored types are written by the seam functions, never by a worker and never by hand.**
  "Orchestrator-only" is corrected for these five: the conductor's pre-orchestrator phase events are
  written by the seam functions it calls, not by the conductor's own hand.
- **Children NEVER write the parent's log.** At abandon-with-rendezvous the parent's seam writes the
  `DOWN` record by reading the child cursor's terminal state at the next parent seam act;
  unrendezvoused orphans reap at seam init.
- **Invariants:** workers never author `DECISION` or any seam type; every `BLOCK`/`ESCALATE` is
  answered by a `DECISION` before the task resumes; the cursor is the countable audit trail for the
  drift ledger.
- **PROGRESS is a mandated liveness heartbeat (F3)** — the worker emits one per owned-module completed
  AND at least once per `livenessDeadline`/2 of wall-clock (a long single module must not read as dark);
  a task with no countable modules heartbeats as `0/1 <label>`. Staleness is measured from the **most
  recent** CLAIM/PROGRESS line (a worker that heartbeats once then hangs is still detected). PROGRESS
  remains **excluded from the coordination logic and from concurrency evidence**: it is read by the
  dashboard, the orchestrator's **liveness monitor**, and (later) the Freeze/Float M4 slack-timing
  estimator. The DECISION/BLOCK/ESCALATE invariants are unchanged; a **missing** PROGRESS never gates a
  task — it only triggers the liveness monitor's staleness path (nudge → escalate → human-gated
  re-dispatch; never a blind kill).

## Seq assignment and the ordering of record

- The appending writer stamps `(observed max) + 1`. Seam-authored lines come from the single seam
  writer and are therefore unique; concurrent worker appends may race — **duplicate worker seqs are
  legal** and are ordered by file position.
- **Ordering of record = `(runId, seq)` + parent fold-order; wall-clock is NEVER load-bearing.**
  The `utc` field is recorded for humans and is informational only. File position is the explicit
  total-order tie-break a duplicate seq requires.
- **Parent fold-order:** runs walk the `parent-run:` tree, parents before their children; roots and
  runs whose parent is not in the fold sort by run id (which is chronological). A `parent-run:` cycle
  is a fail-loud refusal.
- Lineage references (`~parent-seq`) always target seam-authored — therefore unique — seqs.
- **This closes the clock-trust problem, it does not manage it.** The pre-migration board derived
  concurrency from worker process clocks and had to assume a synchronized clock, which cross-host
  skew would have invalidated. Ordering now lives in seq space, so the multi-machine / multi-model
  direction needs no skew-tolerant stamp for ordering to hold.

## Header semantics

- `prev-run:` walks **history** (iteration: a re-loop or a loop-back).
- `parent-run:` walks the **tree** (child runs; roll-up folds walk this edge).
- Both are pointers with distinct semantics; a root-level re-loop has no parent by definition and
  carries a `prev-run:` chain only. A re-loop of a wave is a sibling child: same `parent-run:`, with
  `prev-run:` naming the failed sibling.
- `prev-segment:` is **RESERVED**: it is parsed and round-tripped, and no segmenting machinery is
  built. It is written only when segmenting lands.
- **The reader is exactly as strict as the writer.** Header keys are read in the BNF's order
  (`prev-run:`, then `parent-run:`, then `prev-segment:`), each at most once; a permutation is a
  refusal. One header therefore has exactly one legal serialization, so two byte-different headers
  can never mean the same thing — the same write/read symmetry that makes a line's round trip exact.
- **A `parent-run:` cycle is a fail-loud refusal, and a run naming ITSELF as parent is a cycle.**
  Exempting the self-edge would accept the shortest cycle while refusing every longer one.

## Payloads

- A payload pointer is the `msg` suffix ` payload=<path>` — the escalation line+payload idiom
  (`protocol/escalation.md`), which keeps the cursor one line per event.
- The pointer is **kata-dir-relative** (`payloads/<runId>-<seq>.json`) so it resolves from the
  cursor's own location and survives rotation and worktree moves. The file therefore lives at
  `.kata/payloads/<runId>-<seq>.json` (tier-3 cache; durability is the trail snapshot's job).
- The pointer is path-guarded on **both write and parse**: relative only, no `..`, no whitespace, no
  field separator (CWE-23).
- `VERDICT` **requires** a payload. A VERDICT line without one is refused when written and refused
  when read. Its payload schema:

```json
{
  "verdict": "<verdict token>",
  "evidencePointers": ["<pointer>", "..."],
  "judgeDispatchSeq": 0,
  "runId": "run-<utc-compact>-<hex>"
}
```

- The payload is written **before** the line that points at it, so a pointer is never dangling.
- A line carries **at most one** payload pointer. A msg may not smuggle a bare ` payload=` token, so
  a two-token line is one this engine could never have emitted; it is refused on read rather than
  resolved to the last token, which would parse into a msg that cannot be re-emitted.

## Run isolation — required for the evidence to be honest

The fold computes over the whole cursor, so `.kata/board.md` MUST contain **only the current run's
events**. The seam therefore **rotates any pre-existing board at run start** — moving `.kata/board.md`
to `.kata/board.<utc-compact>.archive.md` before the header write — so prior-run `CLAIM`/`DONE` pairs
cannot contaminate this run's `maxInFlight`/`overlaps`. Without this, stale rows would be folded in
and this run's evidence would be false. Rotation happens only at run **start**: a crash-resume adopts
the existing header's `runId` and continues on the same cursor.

`kata_board.start_run()` performs the rotation and the header write; it never mints a run id
implicitly on an append, because the run id is minted by exactly one seam act at run start.

**Publication is complete-or-absent, with ONE stated residual.** `_publish_cursor` writes the
header bytes to a sibling temp file and `os.link`s them into place, so a concurrent reader sees the
whole cursor or no cursor — never a zero-byte file — and the link doubles as the exclusivity
election (exactly one run claims the cursor). **Residual, carried not hidden:** on a filesystem
with no usable hardlinks the publish falls back to exclusive-create-then-write, whose **zero-byte
window** is real. A reader landing in that window gets a loud parse refusal (`cursor has no
run-header block`), never a silently empty fold — the failure is visible, but the window is not
closed on that filesystem class.

## Phase events — the position of record

`PHASE` lines are how a run says where it is. The closed vocabulary (one enum, no free text):

```
INITIATION · GRILL · AUTHORING · FREEZE · EXECUTION (parameterized wave=<n>) ·
FINAL-GATE · CLOSEOUT · LOOP-BACK
```

- **msg grammar:** `open <PHASE> [k=v …]` | `close <PHASE> [k=v …]` | `run-closed [k=v …]`,
  enforced by `kata_dispatch.parse_phase_msg` — an unknown phase token or verb is a refusal.
- **Position is READ, never remembered.** Every phase-aware contract derives its position from the
  cursor (`kata_dispatch.phase_state(cursor)` → `{open, closed, runClosed}`), never from what an
  agent believes it just did. A conversational recollection is not a position.
- **`run-closed` is terminal and written exactly once**, by `close_run`
  (`tools/kata_close.py`). Nothing is legal on the cursor after it — `phase()` and `deny()` both
  refuse to append past it. Exactly-once is structural, not conventional: `close_run` elects one
  closer by `O_CREAT|O_EXCL` exclusive create before it writes, and the terminal line itself is
  what makes a second close refuse. A run that still holds phases open cannot be closed — the
  closer closes them **LIFO** (so a `LOOP-BACK` opened last is closed FIRST) and only then stamps
  the terminal line, or refuses and names that instruction. The READER half is live too:
  `run_start`'s resume test reads for the terminal line via `kata_dispatch.is_run_closed`.
- Re-opening a closed phase is a **DENY-class event**, recorded as a DENY line naming the legal
  path — not a silent no-op.

## Concurrency evidence (`.kata/concurrency.json`)

**Purpose.** Worker self-stamped `CLAIM`/`DONE` entries make concurrency provable from artifacts
alone. After every run the orchestrator emits `.kata/concurrency.json` — a machine-readable
concurrency evidence artifact the evaluator can read independently. The fold is a **cross-cursor
`(runId, seq)` fold**: a task's in-flight span runs from its earliest `CLAIM` seq to its latest `DONE`
seq (a re-dispatched task keeps its full span — a naive last-write `CLAIM` would erase a real overlap
and undercount concurrency), and the sweep is over seq space, so no clock enters the answer. At an
equal seq an END is processed before a START, so a hand-off is never inflated into an overlap.

**Fold is pure; side effects only after fold completes.** `fold_concurrency` performs no I/O, reads no
clock, and is deterministic; `emit_concurrency` reads, folds, and only then writes. A refusing fold
produces no artifact — an unreadable cursor is a refusal, never a silently emitted zero.

**Schema:**

```json
{
  "maxInFlight": 3,
  "genuinelyParallel": true,
  "workerCount": 4,
  "runs": ["<runId>", "..."],
  "workers": {
    "<runId>#<task-id>": {
      "runId": "<runId>", "task": "<task-id>", "agent": "<agent-id>",
      "startSeq": 1, "endSeq": 9, "spanSeqs": 8,
      "utcStart": "<iso>", "utcEnd": "<iso>"
    }
  },
  "overlaps": [ {"runId": "<runId>", "fromSeq": 2, "toSeq": 7} ],
  "ordering": "(runId, seq, file-position) + parent fold-order; wall-clock never load-bearing",
  "source": "cursor CLAIM/DONE seq spans (cross-cursor (runId, seq) fold); utc fields are informational only"
}
```

*Erratum carried forward:* the fan-out survey cites this schema as "K3". The K3 anchor was the
canonical **snippet**; the **schema** is K5. Both now live here.

**Canonical emit (single source of truth — the orchestrator runs this in-context at the gate):**

```python
import sys
import kata_board

# argv[1] = the run's .kata/ dir (integration root).
# Optional argv[2:] = additional cursor files (child-run arms) to fold across.
print(kata_board.emit_concurrency(sys.argv[1], extra_cursor_paths=sys.argv[2:]))
```

Run form (Windows; `python` not on PATH): `uv run --directory tools python - <abs-path-to-.kata> <<'PY' … PY`.

**Evidence, not a gate trigger (K6).** `concurrency.json` is parallelism evidence. A single-worker run
legitimately has `maxInFlight:1`/`genuinelyParallel:false` — that is **not** a failure. `kata-evaluate`
reads this artifact to corroborate rubric item 4 (ownership / conflict-free concurrent merges) when a run
claims parallel work; it is **never** a stand-alone default-FAIL trigger and is never tiered.
