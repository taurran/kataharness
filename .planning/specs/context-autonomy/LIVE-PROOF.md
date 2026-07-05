---
spec: context-autonomy
task: C11 — the live-proof battery (CA-A1..A5 + CA-A8 row 1 + CA-A11 b/c + G4 empirics)
status: executed 2026-07-04
branch: feat/context-autonomy
baseline: 0fc4ba1344ad31863b474803d35db1980e9e008a (C1–C10 integrated)
host: Windows 11 · claude.exe v2.1.200 · CPython 3.14.3 (harness tools venv)
fixture-pin: every arranged run below carries `inlineEval: "telemetry"` in its fixture
  config unless the fixture line states otherwise (fold #4); the SMOKE rerun arm ran
  the seeded repo's `inlineEval: "on"` exactly as the baseline smoke did.
tags: [kata/spine, context-autonomy, live-proof, CA-A1, CA-A2, CA-A5, CA-A8, CA-A11]
---

# C11 LIVE-PROOF — pasted evidence, per battery item

Every block below is ACTUAL captured output (exit codes, tokens, file contents), not
assertion. Drivers + raw logs: session scratchpad `c11/` (`battery1.log`, `battery2.log`,
`battery3.log`, `statusline-capture` probe, `smoke-extraction.md`, `smoke-repo/`).
Scratchpad artifacts are session-local; everything a verdict rests on is restated HERE
(the CA-L22 durable-citation rule, applied to this doc itself).

## 1 — CA-A1/A2 mechanical leg: GAUGE + THRESHOLD crossing (PASS, mechanical)

Throwaway profile `settings.json = {"autoCompactWindow": 100000}` (the key floor);
fixture config `{"contextAutonomy": "on", "inlineEval": "telemetry", "contextTrigger": 0.30}`.
Each tick is a REAL subprocess through the shipped `adapters/claude/statusline_chain.py`
chaining a REAL user statusline child (byte-identical passthrough shown), then the gauge
read back through `kata_gauge.read_bridge` / `resolve_gauge` / `trigger_crossed`:

```
-- tick used=15.0% -- chain exit=0 passthrough stdout='USER-STATUSLINE used=15%'
kata bridge (superset) : {'session_id': 'c11-liveproof', 'remaining_percentage': 85.0,
                          'used_pct': 15.0, 'timestamp': 1783226022, 'total_tokens': 100000}
read_bridge -> mode=full stale=False   resolve_gauge source: kata
trigger_crossed(gauge, 0.3) = False
-- tick used=25.0% -- trigger_crossed = False
-- tick used=28.0% -- trigger_crossed = False
-- tick used=32.0% -- trigger_crossed(gauge, 0.3) = True        <- the crossing
```

%-only degrade (CA-L2) on the USER 4-field bridge (no `total_tokens`):
```
user bridge: {'session_id': 'c11-liveproof', 'remaining_percentage': 68.0, 'used_pct': 32.0,
              'timestamp': 1783226023}
read_bridge -> mode=percentage-only total_tokens=None
trigger_crossed(user_gauge, 0.3) = True
```
Reader priority: `resolve_gauge -> source=kata` (kata beats user; CA-L1).

`backstop_recommendation` (CA-L16) — actual clamped numbers:
```
fixture leg  target=30000  eff=100000 model_max=200000 -> {'recommend': 100000,
  'note': 'target+gap below the 100k key floor; recommend the 100k floor — deterministic
   rotation covers the remainder.', 'approximate': False}
realistic leg target=112000 burn=8000 handoff=3000 eff=160000 model_max=200000
  -> {'recommend': 128000, 'note': None, 'approximate': False}
ceiling leg  target=190000 eff=200000 model_max=200000 -> {'recommend': None,
  'note': 'target+gap ≥ model max; host default auto-compact suffices, recommend nothing.'}
```

**Live-host chain-eligibility catch (real, kept):** a user command containing the Windows
8.3 short path `TAURR_~1` was refused chaining (`is_chain_eligible=False` — `~` is in the
metachar set) and took the SKIP leg exactly as documented; re-pointing at the long path
chained cleanly. The gate behaved as shipped under a real-world Windows path.

## 2 — CA-A3/A4 mechanical cycle: SELF-HANDOFF + BRIDGE + RE-ANCHOR (PASS, mechanical)

**(a) handoff committed BEFORE any reset** — throwaway target repo, artifact durable in git:
```
30c4ce2 docs(handoff): self-handoff at trigger crossing (kind: self)
33bbf3d feat: wave 1 work (pre-threshold)
committed frontmatter: ['kind: self', 'written: 2026-07-04T22:30:00Z',
  'trigger: contextTrigger 0.30 crossed at used_pct 32.0 (gauge source: kata)']
```

**(b) chained statusline: kata bridge written, user bridge byte-untouched:**
```
chain exit=0 passthrough='USER-NOOP-LINE'
kata bridge after tick : {'session_id': 'c11-liveproof', 'remaining_percentage': 66.0,
                          'used_pct': 34.0, 'timestamp': 1783226089, 'total_tokens': 100000}
user bridge sha256 before: 6eda69d343c9b46f949c9763a65d7aa4053201fd320e93e29ad3cb0aaac2667e
user bridge sha256 after : 6eda69d343c9b46f949c9763a65d7aa4053201fd320e93e29ad3cb0aaac2667e
user bridge byte-unchanged: True
```

**(c) SessionStart(compact) hook — REAL subprocess, actual stdout JSON:**
```
stdin {'source': 'compact', 'cwd': <repo with HANDOFF.md>}  exit=0
stdout: {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
"KataHarness re-anchor (post-compaction / resumed session): before doing anything else,
re-anchor on the newest `.planning/HANDOFF.md` — read it in the Read-in order it prescribes
and confirm the green numbers. Then apply the handoff staleness rule (protocol/handoff.md):
if any board DONE/DECISION line is newer than the HANDOFF.md git commit, the handoff is
demoted from sole-anchor to context-input and the kata-orient 3-tier rebuild is
authoritative. Rebuild full context via kata-orient (3-tier). Orientation tiers consume it 1:1."}}
```
`source=resume` ⇒ identical injection. `source=startup` ⇒ exit 0, EMPTY stdout (clean
no-op). Absent HANDOFF.md ⇒ the degrade wording ("no `.planning/HANDOFF.md` was found …
kata-orient full 3-tier rebuild") — §4 row 8, shown live.

## 3 — CA-A5 NO-FIRE (PASS)

Four under-threshold ticks through the same real chain, then churn counters:
```
tick used=10.0% -> trigger_crossed=False     tick used=18.0% -> False
tick used=24.0% -> False                     tick used=29.0% -> False
handoff refreshes: 0   rotation events: 0
HEAD unchanged: True (30c4ce26)   HANDOFF.md mtime unchanged: True
```

## 4 — CA-A11 fixture rows + CA-A8 row 1 (PASS — 19/19 green)

`tools/tests/test_live_proof_battery.py` (new, this task): CA-A11(a) over-briefing WARN
0.32⇒warn/0.45⇒mandate with the R-31 brief-embedded numbers (budget 144 000 / cap 160 000
on a 200k frame); (b) continuation-report path (continue at 0.75≤0.80, return at 0.87>0.80,
unconditional at ≥cap; pt-N+1 index continuity + the F2 stated rule pinned in
protocol/observability.md); (c) report size contract (verdict+pointer inline, bulk at
`.kata/reports/<runId>-<taskId>-<agent>-<kind>.md`, durable-citation rule pinned);
(d) allowlist checklist WARN (covered⇒0; missing verify-command⇒exactly that one WARN;
empty⇒exactly the five frozen classes); (e) marker re-arm full lifecycle (absent⇒forced⇒
stamped⇒quiet⇒gitSha change re-arms⇒re-stamp quiets); **CA-A8 row 1** — a pre-v0.2.1
one-shot config (no `contextAutonomy` key) ⇒ rotation UNCONDITIONAL, the fixture NAMES
the **D147** departure at the shipped rule site, and proves the incremental path's
absent-at-load⇒OFF BC is preserved (plus malformed-key STOP, never silent off).
```
19 passed in 0.10s
```

## 5 — CA-A2: SMOKE-2/3 identical-protocol rerun (A/B) — PASS with stated caveats

Protocol: fresh-context, author-blind conductor (Opus — same as baseline), given ONLY
verbatim kata-orchestrate SKILL.md extractions + a seeded red-checkpoint micro-repo
(strutil clone: dispatch base 42dbbf0 4/4 green; checkpoint e41dcbf on task/T-F with real
T1-CLI trailer `{"v":1,"i":1,"verify":{"exit":1,"passed":3,"failed":1,"skipped":0},…}`),
same ≤30-line final-report dispatch contract as the baseline smoke.

| Metric (per task gated) | SMOKE-3 baseline (v0.2.0) | C11 rerun (v0.2.1 arm) | Delta |
|---|---|---|---|
| Conductor tokens (spawn-inclusive) | 94 489 | **72 347** | **−22 142 (−23.4%)** |
| Conductor tool calls | 25 | **14** | **−11 (−44%)** |
| Wall clock | 472 s | **335 s** | −137 s (−29%) |
| Final-report ingestion | ~30 lines (contract-capped) | 30 lines (contract-capped) | null |

**Identical run outcomes (the CA-A2 parity leg):** same posture resolve (`inlineEval:"on"`
via precondition-0), same trigger (score **0.60 > τ 0.50**, driver `verify_fail`, lane_drift
false, slack null), same evaluator resolution through the never-anchor gauntlet (anchor
sentinel "session"→opus; economy in standard→**haiku**, explicit ID passed), same verdict
(**reroll**), same reroll conformance (anchor = **dispatch base 42dbbf0** — no below-τ
checkpoint; new branch `task/T-F-attempt1`; kill/worktree legs correctly N/A'd; board
DECISION `@e41dcbf… score 0.6 verdict reroll -> anchor 42dbbf0e… new-attempt
task/T-F-attempt1` written to `.kata/board.md`). Durable artifacts verified post-run
(branch exists at anchor; DECISION line present).

**HONEST COMPARABILITY (read before crediting the delta):**
1. The baseline smoke ALREADY ran under a dispatch-imposed ≤30-line report contract
   (SMOKE-v0.2.0 caveat (a)); the rerun preserved that identically. So the final-report
   ingestion delta is **null by construction on this protocol** — what v0.2.1 changes is
   WHERE the discipline lives (shipped SKILL prose + `.kata/reports/` home for worker
   bulk), not the size of an already-contracted conductor report. No worker final report
   exists in this protocol (the only child is the no-write inline evaluator, whose verdict
   is inline by design), so the `.kata/reports/` leg is exercised by the CA-A11(c) fixture,
   not by this rerun.
2. The original baseline dispatch prompt text was not preserved; the rerun reconstructs
   the protocol from the SMOKE-v0.2.0.md record (same extraction ROLE-set: precondition-0,
   inlineEval load-guard, scheduler+ladder span, dispatch-time model selection) **plus
   exactly the shipped C3 block** (budget line + continuation + report contracts) — the
   deliberate arm delta. "Byte-identical" is therefore protocol-identical, not
   prompt-byte-identical.
3. The −23% tokens / −44% tool calls is n=1 vs n=1 — **directional, not statistics** —
   and cannot be surgically attributed between (i) the shipped budget/report riders and
   (ii) 0.8.0→0.10.0 prose evolution in the same spans. Stated plainly: the loop did not
   get slower under the added v0.2.1 prose (which rides in the SAME extraction the
   conductor must read), and outcome parity held exactly. The DROP threshold judgment is
   deliberately left to the operator merge gate (fold #7).
4. Token accounting: both arms report spawn-inclusive subagent totals from the same
   harness convention (baseline noted its haiku child inside the number; the rerun number
   is the subagent-tree total reported by the same Agent mechanism).

**Finding F2-R (reproduced prose gap, named):** the rerun conductor, author-blind to
protocol/observability.md, inferred the fresh attempt's checkpoint index as **i=1**
("anchor i=0 → k+1") where the baseline conductor inferred **--index 0** and the shipped
F2 stated rule (observability.md: "with `k` absent the fresh attempt indexes from 0")
pins 0. Both smokes prove the ladder-span sentence C3 deferred ("F2 sentence in the
frozen ladder span — deferred to the next M4-surface amendment") is still needed: the
doc-side home is not in a ladder-executor's minimal read set. Rides to the conductor.

## 6 — Green-path overhead datapoint (CALIBRATION-FINDINGS C-2 tie-in)

Retroactive scan of the REAL integrated v0.2.1 branch with the shipped scanner + scorer
(`kata_telemetry.scan_checkpoints` + `kata_risk.should_trigger`, task_class=code):
```
commits walked (feat/context-autonomy ^master) : 41
checkpoint trailers found                      : 31
scored 0.0 (green path, no trigger)            : 25
triggered (score > tau 0.50)                   : 6   (7537274b, 39a80dac, 1f9ed4c2,
                                                      68b36cf4, 5cfce050, 094b1160 — all
                                                      the C-1 suite-scoped verify_fail
                                                      false-positive class, score 0.60)
scan wall time (git walk + parse)              : 1173.2 ms
score wall time (31 checkpoints)               : 0.065 ms  (0.0021 ms/checkpoint)
LLM evaluator calls made by scorer             : 0 (pure decision code)
evaluator tokens spent on green path           : 0
```
**Measured bracket for the <1% cap (M4-L1), stated honestly:** on green checkpoints the
evaluator-call overhead is **exactly 0 LLM calls / 0 tokens** — trailer scoring is
~2 µs/checkpoint of pure Python. 25/31 integrated-branch checkpoints were green
(corroborating C-2's 44/57 over the full worker-branch set). This build ran
`inlineEval: "telemetry"`, so live evaluator spend was 0 by mode; HAD the ladder governed,
the 6 on-branch triggers (13/57 across all worker branches) would each have cost one
economy-tier evaluator call — every one a C-1 **false positive** (suite-scoped
verify signal), i.e. the residual overhead risk is the C-1 signal-definition fix, not τ
and not the green path. The <1% claim holds trivially on the green path (0%); the
non-green-path bound is conditional on C-1 and stays AT-RISK-until-C-1-fix — no stronger
claim is made here.

## 7 — Live host probes (G3/G4) — one VERIFIED-NEGATIVE datapoint + named residuals

**Probe (real `claude` v2.1.200, this host):** `claude -p "Reply with exactly: OK"
--model haiku --settings <throwaway settings.json>` where the settings set a capturing
`statusLine` command AND `autoCompactWindow: 100000`. Result:
```
stdout: OK    exit=0
capture file: ABSENT — the statusline command NEVER ran in headless -p mode
```
**G3's "statusline in headless runs: UNVERIFIED" is now VERIFIED-NEGATIVE on this host:**
headless (`-p`) sessions produce NO statusline ticks ⇒ NO bridge writes ⇒ the CA-L3
staleness fallback + CA-L4 deterministic N-wave rotation are MANDATORY for unattended
conductors, exactly as designed. (The user's real settings were untouched — the override
rode the `--settings` flag; never-clobber held on the live host too.)

**Named residual manual-verification steps (cannot be demonstrated from a subprocess on
this host — an ATTENDED interactive session in a throwaway profile is required):**
- R1: actual auto-compact firing margin below `autoCompactWindow` (G4.1).
- R2: PreCompact hook full input schema (G4.3 — log stdin in an attended session).
- R3: gauge `total_tokens` reflects `autoCompactWindow` capping (fold #6 / CA-L5
  post-cap grounding) — requires an interactive tick under the 100k profile.
- R4: bridge freshness cadence in an ATTENDED session (headless is now proven no-tick).
- R5: hook sync-time budget (CA-L17 UNVERIFIED item) under a real compaction event.
- R6: the full attended CA-A1 cycle (real compaction fires ⇒ SessionStart(compact)
  re-anchor ⇒ next task zero-loss + kata-orient 3-tier context-quality grade) — every
  durable artifact + hook I/O leg of that cycle is proven mechanically above (items 1–2);
  only the host-fired compaction link remains.
- R7: CA-A4's install-time chain-or-skip OFFER (interactive bootstrap); the mechanical
  never-clobber guarantee it rides on is proven at item 2(b).

## 8 — Staged telemetry-ledger row (calibration: true — for the operator's HUMAN-GATED append)

Built with `kata_telemetry.build_ledger_row` (schema v3) and round-tripped through the
strict `read_ledger` (parses: True). NOT appended by this worker — the ledger commit is
human-gated (D141(b)); the operator appends at the merge gate if wanted:
```
{"v":3,"utc":"2026-07-04T23:30:00Z","runId":"ca-c11-liveproof-2026-07-04","target":"scratch/c11 smoke-repo rerun + CA-A11 fixture battery (calibration exercise)","tasks":1,"checkpoints":1,"zeroCheckpointTasks":0,"firstPassAcceptanceByClassTier":{"code×haiku":0.0},"streaksByClass":{"code":[0]},"fixCycles":0,"gateRejections":0,"taskDurationsByClass":{"code":[5.6]},"wallClockS":335.3,"tokensIn":null,"tokensOut":72347,"effectiveModes":{"T-F":"on"},"perTask":{"T-F":{"tokensIn":null,"tokensOut":72347,"wallClockS":335.3}},"failureKinds":[{"taskId":"T-F","kind":"test-regression","at":"2026-07-04T23:25:00Z"}],"degraded":[],"parentTokens":{},"calibration":true}
```

## 9 — Notes for the conductor (files C11 does not own)

- **D147 tense:** DECISIONS.md D147 says the row-1 fixture is "run in the C11 live-proof
  battery" — as of this doc that is now TRUE (item 4); no edit needed, verify at closeout.
- **F2-R** (item 5): the deferred orchestrate-span F2 sentence remains needed —
  reproduced live by a second independent conductor.
- **Merge-gate packet inputs from this battery:** the CA-A2 judgment-grade table (item 5,
  with its four caveats), the G4 empirics + residuals (item 7), the VETO-FLAGs (CA-L22 /
  CA-L25 — surfaced by C10, unchanged here).
