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
