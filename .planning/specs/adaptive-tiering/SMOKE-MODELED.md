---
spec: adaptive-tiering
artifact: SMOKE-MODELED — adaptive (v0.3.0) vs static (v0.2.1) tiering comparison
status: executed 2026-07-05, pre-merge (operator-directed, during the adval)
method: DETERMINISTIC REPLAY of the real v0.2.1 context-autonomy build's recorded dispatch/trigger
  mix through BOTH policies via the SHIPPED engine (kata_adaptive + kata_models — the real load
  guard, budget resolver, and spend gate executed, not simulated arithmetic). MODELED, NOT MEASURED
  (AT-L22): no live A/B arms were run; the live comparison is queued post-R6 with arms pinned.
tags: [kata/spine, adaptive-tiering, smoke, modeled, calibration]
---

# SMOKE-MODELED — adaptive vs static tiering (the operator's efficacy/efficiency question)

Every input below is a RECORDED number with its citation; every computation ran through the shipped
engine functions (`classify_premium_scope`, `resolve_budget`, `can_spend`, `record_spend`). The
driver is reproducible (session scratchpad `smoke_model.py`; all verdict-bearing numbers restated
here per the durable-citation rule).

## Inputs (real, cited)

| Input | Value | Source |
|---|---|---|
| Worker (coding) dispatches | 23 | CALIBRATION-FINDINGS.md:15 ("~23 tasks") |
| Critical dispatches (gates+grill+freeze/plan/final+re-gates) | 36 = 23+6+3+4 | D146 (6 convergence gates; freeze+plan-checker+final review); HANDOFF 2026-07-04 ("4 reworks") |
| Would-be triggers, pre-Amendment-#5 | 13/57, ALL false-positive | CALIBRATION-FINDINGS C-1 |
| True positives (post-fix expected class) | 0/57 | CALIBRATION-FINDINGS C-1 |
| One full task redispatch | 72,347 tokens | LIVE-PROOF.md item 5 (measured) |
| One economy evaluator call | ~2,500 tokens | SMOKE-2 arm record (order of magnitude) |
| Re-adjudication overturn on the FP flavor | 1/1 (sonnet overturned haiku's reroll) | CALIBRATION-FINDINGS C-3 (n=1 — the model's weakest assumption, stated) |

## Result 1 — premium-rung calls on the real v0.2.1 build shape (EFFICIENCY)

```
static class-scope : 59 premium calls (36 critical + 23 coding, run-long)
adaptive event-scope: 8 premium calls (of 10 hard-moment events; 2 denied at budget; N=10)
premium-call reduction: -86%
```

**−86% premium-rung calls.** The 51 dropped dispatches run at the anchor / their economy tier
instead — the D148 class-scope form would have elevated every gate AND every build worker for the
whole run; the D150 event scope elevates only the 10 hard moments the run actually had, and the
budget's 2-call freeze-gate reservation correctly denied the two lowest-priority rework reviews
(the engine's conservative direction, demonstrated live in the replay).

## Result 2 — evaluator economics on the PRE-fix trigger mix (EFFICACY + efficiency)

```
static ladder  : 13 wrongful kills -> 973,011 modeled tokens (13 redispatches)
adaptive ladder: 0 wrongful kills -> 65,000 modeled tokens (13 screens + 13 re-adjudications)
token reduction on the FP class: -93%   |   wrongful-kill efficacy: 13 -> 0
```

**Had the ladder governed the v0.2.1 build without Amendment #5,** the static policy kills and
redispatches 13 healthy tasks (every trigger was a false positive); the adaptive
cheap-then-escalate re-adjudication overturns them at one below-anchor call each — **−93% modeled
tokens on that population and 13→0 wrongful kills**, resting on the C-3 overturn observation
(n=1 — the honest caveat).

## Honest frame (read before quoting either number)

1. **MODELED, not measured.** The dispatch counts are reconstructed from the run record (±); the
   overturn rate is n=1; no live arms ran. These are DESIGN-BEHAVIOR demonstrations on real input
   shapes, not benchmark results.
2. **The two results measure different regimes.** Result 1 is the steady-state premium bill;
   Result 2 is the pre-fix pathological regime that Amendment #5 already designed away — on the
   POST-fix expected mix (TP 0 measured) both arms spend ~0 on the ladder, and the
   re-adjudication's residual role is insurance on TRUE kills only.
3. **What the live A/B must pin (queued post-R6, BACKLOG ★ item):** two arms on an identical
   seeded multi-task protocol, `models.adaptive` + `premium.scope` pinned per arm (AT-L22),
   measuring premium calls, evaluator calls, wrongful-kill count, wall clock, and tokens —
   the measured successors to both modeled numbers above.
