# DEFERRED — parked designed work (kata-defer ledger)

> PD-1 sanctioned deferral path: every entry here is operator-visible, graded at the gate,
> and surfaced at handoff. An entry is closed by the run that builds it (link the record).

## DEF-1 — kata_preflight._default_runner stderr widening · OPEN (2026-07-21)
- **What:** `tools/kata_preflight.py:397-407` `_default_runner` returns `(returncode, stdout)`
  — same stderr-discard class as the kata_dispatch defect fixed by the dispatch-stderr-fix run.
- **Why deferred:** the quota-resilience classifier (its own grilled run,
  `.planning/specs/quota-resilience/REQUIREMENT.md`) decides what preflight signal it consumes;
  widening now is scope creep on a surgical fix. Grill record:
  `.planning/specs/dispatch-stderr-fix/GRILL-LEDGER.md` D4 (operator-approved).
- **Owed to:** ~~the quota-resilience Tier 1+2 run~~ → **RE-ASSIGNED to quota Tier 3** (2026-07-25).
- **Why re-assigned (audit finding, 2026-07-25):** the Tier 1+2 run **shipped (PR #46, v0.4.0) without
  discharging or re-assigning this item** — its designated closer completed and DEF-1 was left OPEN
  pointing at a finished run. The audit re-verified the code: `tools/kata_preflight.py:397`
  still returns `tuple[int, str]` and still `return result.returncode, result.stdout`.
  Tier 1+2's grill answered the "what preflight signal does the classifier consume?" question
  implicitly as **none** — G-7 scoped classification to dispatch RESULT envelopes only, and
  `REQUIREMENT.md` touches preflight solely as a BLOCK-shape reference and as a **Tier 3** headroom
  check. So Tier 3 (which builds `preflight quota-headroom`) is the honest owner: it is the first run
  that actually needs the signal.
- **NOT closed:** the widening is still unbuilt. Kept OPEN so it stays operator-visible (PD-1).
- **Size when picked up:** 4 call sites, all already discarding the second element as `_`
  (`kata_preflight.py:1214,1299,1317,1356`), plus the `RunnerType` protocol and the test stub at
  `tools/tests/test_kata_preflight.py:36`. Mechanical, but a contract change — own branch + gauntlet + adval.
