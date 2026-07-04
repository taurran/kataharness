# HANDOFF — post-M4 session orientation (written 2026-07-04, at v0.2.0)

> Paste-companion for the next fresh session. Ground truth: master `8c68cd5`, tag `v0.2.0` pushed
> (PR #8, 38 commits). Gauntlet ON THE MERGED SHA: pytest 2505/3 skip · validator 48/0/0 · Snyk
> medium+ 0. D-records D141–D145. ⚠️ IGNORE C:\Dev\CLAUDE.md (unrelated Mise project).

## 1. WHAT SHIPPED (M4 — the inline evaluator/reroll, DSpark-informed; one operator-directed pass)

DESIGN + 3 PLANs all double-gated (9 adversarial gates this milestone; every one caught real
defects; all folded — full gate histories live IN the spec files, `specs/inline-eval-m4/`):
- **P0 telemetry:** `tools/kata_telemetry.py` (Kata-Checkpoint commit trailers, git-blob evidence
  digests, slack substrate, the committed ledger `.planning/telemetry-ledger.md`), worker
  checkpoint cadence (kata-tdd 0.2.x), orchestrate telemetry steps, calibration run #1.
- **P0.1 (operator scope addition, routing branch 3, D142):** ledger schema v2 — perTask cost
  (explicit nulls), failureKinds enum (orchestrator-classified, D33), structured degraded signal
  (kata_restore `_ex`/`restore()` keys — BACKLOG #16 folded).
- **P1 code-class mechanism (D143):** `tools/kata_risk.py` (one-dial capped-sum score, STRICT `>`
  τ), `kata-inline-eval` (48th skill, fresh-context no-write chunk evaluator), orchestrate
  scheduler + corrective-action ladder (trigger → inline eval at strictly-below-anchor via D131
  with BOTH never-anchor carve-outs → correct/reroll = one kill-and-restart primitive on attempt
  branches → grounding pass → human-required), adapter contract (`adapters/ADAPTER-CONTRACT-M4.md`).
  L19 cross-seam sweep: 0 HIGH, all folded. D141 = partial D134 supersede (checkpoint commits
  load-bearing) + ledger commit authority.
- **P2 (D144):** per-class τ leashes LIVE (0.45 research/debug vs 0.50 code) on the universal hard
  trio; class EXTRAS (coverage/scope/hypothesis) DATA'd at A1-Q4 weights with **named-deferred
  producers** (the gate caught the originally claimed sources not existing — honest shrink).
- **LIVE PROOF (D145):** ladder fired live (arranged fault: 0.60 > 0.50 → sonnet inline eval →
  diff-cited `correct` verdict → redispatch-with-NOTE → green, index continuity); float n=0→1
  (real `builds_against` edge: pin MATCH, stubs 0, danglers 0); A/B: on-arm 0 gate rejections vs
  control 1 rejection + 1 fix cycle; happy path = ZERO LLM calls (4 green checkpoints, score 0.0).

## 2. DEPLOYMENT-STATE TRUTH TABLE (is everything fully employed?)

| Surface | State |
|---|---|
| `inlineEval` off/telemetry/on (string + object forms) | **WIRED + LIVE** (BC: absent ⇒ off) |
| Bootstrap default `telemetry`; offer-`on` threshold (≥3 ledger runs) | **MET** (4 rows) — bootstrap may now OFFER `on` |
| Code-class ladder | **LIVE, proven once** (n=1 mechanism proof, not a statistical base) |
| Research/debug leashes (τ 0.45, base trio + slack) | **LIVE** |
| Research/debug class EXTRAS | **DATA'd only — producers NAMED-DEFERRED** (durable hypothesis records; scope/coverage comparators — each needs its own gated amendment) |
| <1% green-run overhead cap (M4-L1) | **AT-RISK** at owned-module chunking (measured bracket ~0.4–1.9% run-level); remediation NAMED: coarsen chunk unit `[TUNABLE]`; re-measure on the first real-scale `on` run |
| LD7 host-fallback × M4 topology | **DEFERRED** (named in the adapter contract; treat as reroll-equivalent or degrade) |
| ACP/Quick live leg | **DEFERRED** (contract-conformance only, per DESIGN acceptance 4) |
| Slack per-attempt re-scoping | **BACKLOG** (L19 LOW-8 caveat in the slack_ratio docstring) |
| τ/weights calibration from ledger | **NOT STARTED** (needs more real rows; rows 1+4 are calibration-flagged toys) |

## 3. NEXT STEPS (deployment path, in order)

1. **THE OPERATOR'S ONE-LAST-FIX (before launch):** the operator holds a prompt for **parent-session
   context minimization** — this session is the motivating incident (conductor context exhausted by
   gate reports, build reports, and telemetry all flowing through the parent). Expect it to touch:
   conductor narration/report compaction, subagent-report size contracts, kata-selfhandoff
   thresholds, and possibly a conductor-side "gate results as artifacts, not prose" discipline.
   Run it through the full loop (grill → freeze-gate → build → gates) like everything else.
2. **Launch/deploy:** install v0.2.0 into the PokeVault vault (D58 path); the operator ingests
   v0.2.0 into MindBridge (the sanctioned KataHarness → PokeVault → MindBridge direction, D30).
3. **First real full kata run with `inlineEval: on`** (Kenjiri resume is PAUSED as a candidate; or
   a new project one-shot): gives the real-scale <1% measurement, real calibration rows, and the
   first non-arranged ladder statistics. STOP-criteria: if real-scale overhead misses the cap,
   apply the named remediation (coarsen chunk), never a silent cap change.
4. **Freeze/Float ship order continues:** M2 (shadow tasks) → M3 (runtime re-partition, behind its
   own review) per L9/D138.
5. **Backlog (each via its own gated amendment):** class-extra producers; LD7×M4; ACP live leg;
   slack re-scoping; a learned scorer (M4.1) once the ledger is deep.

## 4. WHERE EVERYTHING LIVES

`specs/inline-eval-m4/{DESIGN,PLAN-p0-telemetry,PLAN-p1-code-class,PLAN-p2-adapters}.md` (gate
histories inline) · DECISIONS **D141–D145** (+ addenda) · `.planning/telemetry-ledger.md` (4 rows)
· CHANGELOG `[0.2.0]` · `adapters/ADAPTER-CONTRACT-M4.md` · STATE.md CURRENT block (2026-07-04) ·
the HANDOFF-M4-INLINE-EVAL.md brief is now HISTORICAL (superseded banners inline).

## 5. SESSION LESSONS FOR THE NEXT CONDUCTOR (uncommitted wisdom)

- The gates were the milestone's engine: 9 gates, ~60 real findings, including three catches that
  would have shipped broken invariants (the resolver-None never-anchor hole resurfaced FOUR times
  across layers — check it in anything touching dispatch). Never skip the re-gate after a HOLD.
- Conductor context is the scarce resource (the operator's next fix). Until it lands: dispatch
  workers with strict FINAL-REPORT size contracts, prefer artifacts over prose reports, and
  self-handoff at task boundaries rather than pushing through.
- Post-merge telemetry scans need FORK REFS (rev-list task ^integration is vacuous after merge) —
  the orchestrate text mandates gate-time scans; honor it.

## 6. HONEST GAP AUDIT — what is NOT fully closed in the M4 push (operator-requested, 2026-07-04)

Nothing here blocks the tag — but each is a truth the next session must not rediscover:

1. **The D16-machinery A/B was NOT used.** The handoff recipe named "Benchmark A/B (D16 machinery)";
   the live proof's A/B was run MANUALLY (honest numbers in D145, but no `benchmark.def.json` /
   scorecard artifacts). The evidence exists; the FORM deviates. If MindBridge ingest wants scorecard
   artifacts, re-run the A/B through the benchmark module.
2. **The <1% green-run cap is UNPROVEN — acceptance criterion 1 is PARTIALLY met.** Outer-loop
   reduction: proven (0 vs 1+1, arranged). Green overhead <1%: bracketed ~0.4–1.9% run-level,
   AT-RISK at owned-module chunking, remediation named (coarsen chunk `[TUNABLE]`). The first
   real-scale `on` run is the decisive measurement.
3. **`kata-inline-eval` has never been loaded AS an installed skill.** The live proof dispatched a
   general-purpose agent with the skill's content inlined. The SKILL.md validates (48/0/0) but the
   skill-file → dispatch path is unexercised (smoke item).
4. **The shipped PROSE has never driven a fresh conductor.** M4's scheduler/ladder is orchestrator
   prose; the one live firing was executed by the AUTHORING session (which knew the design). Whether
   a fresh conductor following ONLY orchestrate 0.8.0's text reproduces the behavior is untested —
   the single most valuable smoke check (the D137 sprint-blind-test spirit).
5. **Bootstrap's offer-`on` rule is prose-only.** Nothing mechanically reads the ledger row count at
   bootstrap; a bootstrap session must check `.planning/telemetry-ledger.md` manually (4 rows ⇒ MAY
   offer `on`). Acceptable-by-design; stated so it isn't assumed mechanical.
6. **Board DECISION durability**: the M4 session's D141(b) approval + ladder DECISION lines live in
   the harness repo's gitignored `.kata/board.md`; `kata_trail.snapshot_board` was never run. The
   approvals ALSO live in commit messages + D-records (audit trail survives), but the board lines
   are session-local. Snapshot or accept.
7. **Cross-model checklist row is PARTIAL**: durable-artifact readability is proven by the AC-4
   round-trip test + live cross-session scans; no DEDICATED test exercises an LD6
   background-subprocess writer. Deferred with the multi-model live leg.
8. **Ledger row 4's `at` timestamp is conductor-approximate** (21:45:00Z, minted at record time,
   not event time) — fine for calibration, noted for audit precision.
9. **kata-evaluate does not read `.kata/telemetry/`** — deliberate (M4-L8: gate unchanged;
   evidence re-validation deferred and flagged in A1-Q2). Stated so its absence reads as design.

## 7. SMOKE-CHECK PROTOCOL (the next session's opener — adval-style, fresh-context)

**Do we need it? YES** — gaps 3+4 above are exactly smoke-shaped: the product is prose + tools,
and the prose has never run without its author. **Can we? YES — cheaply** (the P0 T5 pattern).

- **SMOKE-1 (read-path, ~5 min, conductor-inline):** `git describe` == v0.2.0 on master; gauntlet
  (pytest 2505/3, validator 48/0/0); `read_ledger` parses 4 rows + `failure_kinds_of` on each +
  `class_median` returns None at min_samples=5 (calibration exclusion holds).
- **SMOKE-2 (prose-executability — THE critical one):** prepare a micro repo with a pre-seeded red
  checkpoint commit (reuse the T5/live-proof pattern); dispatch a FRESH-CONTEXT conductor agent
  given ONLY the orchestrate 0.8.0 scheduler+ladder sections + the repo path; PASS = it scans,
  scores 0.60, triggers, dispatches kata-inline-eval BY SKILL FILE (closes gap 3), acts on the
  verdict per A1-Q1, writes the @sha DECISION line — from the shipped text alone. FAIL modes feed
  a targeted prose fix, not a redesign.
- **SMOKE-3 (efficiency BASELINE for the operator's context-minimization fix):** during SMOKE-2,
  measure the CONDUCTOR's own cost: tokens consumed, tool calls, report bytes ingested per worker
  gated, and context-% at closeout. Record as the PRE-FIX baseline row. After the operator's fix
  lands (through the full loop), RE-RUN the same smoke — the fix's own A/B: conductor
  context-per-task-gated must DROP with identical gate outcomes. That is the "loop is more
  efficient" proof, measured, not asserted.
