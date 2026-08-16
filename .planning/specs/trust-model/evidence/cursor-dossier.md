---
spec: trust-model
artifact: evidence dossier 2/4 — the cursor (temporal run record) evidence base
date: 2026-08-16
provenance: read-only survey agent, committed verbatim-in-substance by the conductor; spot-verified
  by class — re-verify any single row before it becomes load-bearing in a DESIGN
baseline: grill/dispatch-seam @ fea7ccb (master de8578c)
---

# Evidence 2 — the cursor dossier

Durability legend: **(i)** session death · **(ii)** compaction · **(iii)** wiped `.kata/` ·
**(iv)** machine change (only committed-and-pushed git survives).

## Governing facts

- `.gitignore:9` — `.kata/` is gitignored; `observability.md:151-154` "can vanish with the session."
- **`.gitignore:10,19` — `/INTENT.md` and `kata.config` are ALSO gitignored**, contradicting
  `protocol/state.md:41` which lists tier-1 frozen provenance as `kata.config` **(git)**. Verified:
  `git ls-files` returns neither. Under (iv) a resumer loses the run's goal, mode, tiers, modules,
  roles, advisor grant, and delivery shape.
- `kata_trail.py:13-14` — the trail ref "NEVER writes to refs/heads/*" and "NEVER pushes" — so
  `refs/kata/trail` survives (i)(ii)(iii) but **not (iv)**.

## The two binding rulings any cursor must reconcile with (verbatim)

> **D81** — three-tier state; tier-3 `.kata/` cache is disposable, rebuilt from the git-committed
> trail. Tier 1 frozen provenance (`kata.config`) · tier 2 durable trail (reports + boundary
> handoffs + superseding decisions, git) · tier 3 progression cache (`.kata/`, single-writer,
> churns). Resume works in a new session/clone; git is the source of truth for "where are we?".
> — `DECISIONS.md:612-615`

> **D135** — board-is-the-trail; **no separate continuous-replay journal**. Building a second
> append-only log alongside the board doubles the write + parse + divergence surface for a
> capability that already exists: the board is *already* an append-only, worker-stamped event log.
> Its **only** deficiency for restore is that it lives in gitignored tier-3. So the feature is
> **durability of the board**, not a parallel journal. — `DECISIONS.md:1952-1965`

**Constraints these impose:** (a) the cursor's authority may not live in `.kata/`; (b) the cursor
may not be a second append-only event log; (c) therefore a cursor is either a **fold/view over
board + trailers + tier-2** or a **durability/semantics upgrade of the existing board** — never a
new journal. Third precedent: `protocol/state.md:53-61` refuses new state fields AND new board
TYPEs for thrash counters — recount-from-`DECISION`-lines is the established pattern.

## A. Event inventory — the load-bearing rows

(Full sweep covered ~106 events across initiation → grill/freeze → execution → debug → final gate
→ closeout → loop-back → sprint → burn. Retained here: every row whose durability profile shapes
the design.)

### Durably recorded today (the assets)

| Event | Record | Survives |
|---|---|---|
| PLAN freeze | `PLAN.md` frontmatter `status:` — the only closed-enum freeze marker in code (`kata_restore.plan_status:344-424`, absent⇒NOT frozen, unknown⇒raise) | (i)(ii)(iii)(iv) |
| Task INTEGRATED | `Kata-Task:` trailer on the integration commit — "Tier-2 is AUTHORITATIVE for DONE" (`kata_restore.py:22`), strict regex `:206` | (i)(ii)(iii)(iv) |
| Checkpoint | `Kata-Checkpoint: {json}` trailer, one per commit, second⇒RAISE (`observability.md:75-78`) | (iv) iff branch pushed |
| Contract supersede / invalidation | `Kata-Supersede:` / `Kata-Invalidated:` trailers (`kata_restore.py:212-221`), malformed⇒surfaced never swallowed | (i)(ii)(iii)(iv) |
| DESIGN/PLAN/ledgers/handoff/DEFERRED/lessons | `.planning/` committed docs | (iv) if committed |
| Validation misses + recurrence | `.planning/validation-misses.jsonl` / `recurrence-handled.jsonl` | (i)(ii)(iii)(iv) |
| Steering directives consumed | `STEERING.md` `## Consumed / delivered` | (i)(ii)(iii)(iv) |
| Board (latest snapshot) | `refs/kata/trail` via post-integration call + PreCompact hook (the hook is the one WIRED live writer) | (i)(ii)(iii), **not (iv)** |

### Board-only (recount pattern; dies with `.kata/` unless a trail snapshot landed; never survives (iv))

CLAIM / PROGRESS / DONE / BLOCK / ESCALATE pointers / DECISION rulings · M4 ladder events
(`ladder: <task> trigger <n> @<sha> score <s> verdict <v>` — "the sha on each line is what makes
recovery sound", `kata-orchestrate:814-816`) · reroll DECISION naming the active attempt branch ·
adaptive `tier:` moves (durable recount trail, `observability.md:119-124`) · advisor spend
(`advisor:`-prefixed DECISION + `.kata/advice/*.json` ordinals) · fix-loop cycle counts
(`NEEDS_WORK fix: <area> cycle <n>` — the only trail; counters deliberately NOT persisted,
`protocol/state.md:53-61`).

**Four independent subsystems already recount from board DECISION lines — the board IS the cursor
for those four; it just isn't push-durable, phase-aware, or run-identified.**

### Recorded NOWHERE (the holes)

| Event | Consequence |
|---|---|
| **kata-evaluate PASS/NEEDS_WORK · kata-review SHIP/HOLD · slop verdict** | no-write judges by design ⇒ no verdict artifact exists anywhere. **Direct blocker for BL-N19's mechanical re-loop and BBM-12's per-wave re-loop.** A mid-gate resumer must re-run the whole gate |
| Phase (which loop stage the run is in) | "Phase is derived, never stored" (`session-lifecycle:28-30`); dash derives it only inside an active orchestrated run. Everything before wave-1 and after the final gate is phase-invisible; `detect_lost_run` is structurally blind mid-grill (no board, no trailer, no trail ⇒ "no-trail") |
| Convergence gate verdict (SHIP/HOLD, which round) | nowhere mechanical; BBM names it still open (`backlog-burn-mode:144-145`); Advanced's double-pass discipline leaves no trace two passes ran |
| Task gate PASS (per-task) | implicit only in the later integration commit |
| Gate rejection classification | in-context until the closeout ledger row; lost if the run dies first |
| Wave boundary | `wavesDone[]` exists only in never-written state.json; harmless today, **load-bearing under BBM-12 wave-per-loop** |
| Closeout Decisions 1–4 (satisfaction / git / loop disposition / backout) | D1/D3 prose in HANDOFF at best; **backout-approved-but-not-executed is recorded nowhere — the highest-stakes gap in the loop** |
| Loop-back event + 3 of its 4 payload elements | RESULT.json, understand.md, INTENT.md all gitignored; degrades to LESSONS-LEARNED only on (iii)/(iv) |
| Readiness verdict, orientation, dispatch-budget verdict, G1 sprint approval, kata-diagnose fix-problem verdict, mirror answers pre-freeze | in-context only |

## B. Fragment inventory — key rows

| Fragment | Writer → Reader | Tier |
|---|---|---|
| `.kata/state.json` (full schema at `protocol/state.md:10-24`) | code writer exists (`kata_board.write_state`); **no live writer; not present on disk** — readers are display-only | tier-3, de facto tier-∅ |
| `.kata/board.md` | workers via `kata_board.append_*` (prose-instructed), orchestrator DECISION | tier-3, snapshotted to trail |
| board archives ×4 | run-start rotation | **write-only — nothing reads archives**; the trail holds only the latest snapshot's board |
| `refs/kata/trail` | `kata_trail.snapshot_board` — plumbing-only, fail-soft, never pushes; call sites: post-integration prose + **PreCompact hook (wired)** | local-git durable |
| trailers (Task/Checkpoint/Invalidated/Supersede) | orchestrator/worker commits; strict regexes with malformed-surfacing | **git-durable — the only tier-2 execution record** |
| `.kata/dispatch.json` roster | conductor-only single-writer; display-only, "never gates, never kills" | tier-3 |
| telemetry ledger `.planning/telemetry-ledger.md` | closeout, human-gated commit (D141(b)); declined ⇒ `.kata/telemetry/ledger-row.pending.json` | git-durable after the gated commit |
| `HANDOFF.md` | **no code writes it** (session-lifecycle:9); hooks read presence-not-freshness; `kind:`/`trigger:` frontmatter **never read by any code** | tier-2 |
| PLAN frontmatter task maps (`ownership/waves/depends_on/builds_against`) | plan author; `parse_plan_tasks` authoritative — heading-scraping explicitly rejected | git-durable |
| `kata.config` / `INTENT.md` | bootstrap / `intent_scaffold.write_intent` | **claimed tier-1, actually gitignored** |

## C. Interruption-resume analysis — what restore actually does and where it is blind

`kata_restore.restore()` five steps: `detect_lost_run` (lost ⇔ trail present AND board
absent/empty) → `read_board_from_trail` + `fold_board` → `compute_redispatch_set` =
plan_task_ids − integrated_task_ids ("Re-dispatch set = PLAN-derived, never board-derived. Board
corroborates, never gates.") → `cleanup_stale_task` (worktree prune + salvage-rename, never
force-delete; skipped whole-cloth when degraded) → write board back without rotation.

- **Re-dispatch is (iv)-safe by construction** — it uses exactly the git-durable set (PLAN +
  trailers). **Every counter is not.**
- `detect_lost_run` is one-bit and trail-gated: conductor-death-with-board-present ⇒ "not lost";
  no-trail (nothing integrated yet, or hook not installed) ⇒ "not lost". Mid-grill, mid-freeze,
  mid-closeout are invisible to it.
- D134 (verbatim): "The task is the restart unit… restore re-dispatches from scratch… We do NOT
  record branch/worktree paths, do NOT build a mid-wave commit protocol, and do NOT re-attach a
  half-finished worktree." Partial-work loss is **by design, not a gap**.
- **The staleness comparator is fully specified (`protocol/handoff.md:53-58` — down to same-second
  tie-breaking) and implemented nowhere**; the only occurrences of "staleness" in code are inside
  nudge strings (session-lifecycle:14-15). SessionStart re-anchors on handoff **presence**, not
  freshness.
- Stale prose on the resume path: `kata-orient:108` still says cleanup "force-deletes" the task
  branch — the code salvage-renames (BL-M21); `observability.md:13,127-128` cites the trail call
  site at a stale line number.

## Cross-cutting conclusions (the dossier's synthesis)

1. **The board is already the cursor for four subsystems** (recount-from-DECISION-lines); its
   deficiencies are exactly three: no run identity, no phase awareness, no push durability.
2. **Every judgment verdict is undurable by construction** (no-write judges) — whoever persists a
   verdict must be the *dispatcher*, not the judge; this is the same EDR-1 principle (the
   dispatcher is the witness) arriving from the durability direction.
3. `refs/kata/trail` never pushes — all board-derived state is machine-local.
4. `kata.config`/`INTENT.md` gitignored vs. the tier-1 "(git)" claim is a **standing contradiction
   needing an operator ruling** (commit them? or re-tier them and fix state.md?).
5. Board archives are write-only; multi-rotation history is unread.
6. No phase marker exists anywhere; restore is structurally blind outside active execution.
