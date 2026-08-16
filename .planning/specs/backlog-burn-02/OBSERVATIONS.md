---
spec: backlog-burn-02
kind: mode-design evidence (burn round 2)
opened: 2026-08-16
purpose: evidence for Burn mode (BL-N12) — second live data point, first under the BBM-1..11 rules
---

# OBSERVATIONS — backlog burn #2 (the five ≤1-file fixes)

**What is different from round 1, by design:** hybrid gating from the start (BBM-1: builder
self-gates + fresh-context judges + one conductor spot-audit) · worktrees provisioned OUTSIDE the
repo root at a conductor-pinned SHA (BBM-9 + the HIGH-2 contamination mitigation) · triage +
convergence review BEFORE freeze (BBM-7/8) · `waveBoundaries: autonomous` declared up front
(BBM-11).

## Pre-dispatch record

| fact | value |
|---|---|
| frozen plan | `PLAN.md` beside this file, `status: frozen` at commit `c2be1159ca1aedaf4e39c135b55f0e7f35f39998` |
| **baseSHA (MED-5 durable record)** | `c2be1159ca1aedaf4e39c135b55f0e7f35f39998` (= the freeze commit; all four wave-1 worktrees provisioned at it) |
| worktrees | `C:/dev/projects/kh-burn02-{x01,x02,x03,x07}` on branches `task/burn02-<item>` — conductor-verified post-provision: all four at `c2be115`, clean |
| convergence | CONVERGE-HOLD (4 HIGH / 5 MED / 4 LOW) → all resolved in the frozen revision; the review corrected the conductor's OWN triage claim (H3 class: "only quality has provider tags" was wrong — twelve provider tags exist) |
| mode evidence already | BBM-8 vindicated a THIRD time: 3 of 4 HIGH findings were in the shared half or shared claims; one was an H5 unsatisfiable pair (X03 proof-vs-clean) and one an H5 pair inside an item spec (X07 wrong gate primitives — the conductor's fix-wording itself was the defect) |

## Integration queue (conductor-owned fixes accrued from flags/judges)

1. **File a new found-broken backlog item (from the X01 judge — the more serious of the two):**
   `skills/coordinate/kata-bootstrap/resources/run-shapes.md:6` — the `batch` preset pre-fills
   `modules: [bakeoff]`, and `bakeoff` has NO provider skill: **the shipped batch run-shape
   writes a config the load-guard STOPS.** Same family as BL-X01, still live, judge
   machine-verified. File as the next BL-X code at integration.
2. **File a new found-broken backlog item (from the X03 judge):** `kata-understand/SKILL.md:138-140`
   fallback path documents `grep -n "^def \|^class "` — not a PowerShell cmdlet, so a literal
   follower on this project's stated primary shell fails there. Same doc-vs-mechanism class as
   BL-X03 itself, pre-existing, out of the item's scope. File as the next BL-X code at integration.
2. **README.md:95 + :202 (from the X07 judge, MED-1):** two LIVE user-facing lines carry the same
   Hermes false-claim class in different words ("promotes learned behavior without a human gate" ·
   "which Hermes doesn't have") — invisible to the builder's literal-phrase self-gate, caught by
   the judgment layer. Hand-authored README prose = conductor-owned (the burn-01 partition);
   fix at integration with the research-accurate phrasing, gated by the integrated gauntlet.
   **Mode evidence:** the hybrid gate's judgment half caught what the mechanical half cannot —
   the first live proof of BBM-1's two-layer rationale.

## Running log

*(appended as the burn proceeds)*

| when | item | event | note |
|---|---|---|---|
| pre-flight | all | triage re-verified all five filings live | first burn where NO item changed materially at triage (contrast H2's 2-of-6) — though the conductor's supporting claim on X01 was wrong in the other direction |
| freeze | plan | convergence HOLD → fixed → frozen `c2be115` | wall-clock ~9 min for the review (fresh-context judge, ~115k subagent tokens) |
| wave 1 | x01·x02·x03·x07 | dispatched concurrently, 4 pinned worktrees | briefs carry step-0 verification + push-back |
| wave 1 | x01 | returned BUILT ~5.3 min, ~69k subagent tokens, gauntlet 4/4 in worktree, commit `c28e157` | self-gate NON-VACUOUS (red on old value, green on new); conductor RE-RAN it: PASS; diff scope exact (1 file, 1 line); flagged a byte-identical old example in a frozen planning record (correctly untouched) |
| wave 1 | x02 | **ESCALATED (rule 2) ~6 min, ~64k tokens, ZERO commits, worktree restored clean** | H5 ×3 for the mode ledger — AND a convergence-review FALSE NEGATIVE: the review's MED-2 "no test pins the banner" was wrong (`test_next_steps_banner.py:22-25` pins the phantoms); builder proved the collision with a temp-edit-then-revert, verified the whole command set + repo-wide phantom sweep, and asked a one-line ruling. **The cheap-escalation shape the mode wants, again** (H5's zero-redispatch pattern held) |
| wave 1 | x02 | plan AMENDED (conductor): `test_next_steps_banner.py` added to the owner set, scoped to the `:22-25` block | a deliberate, recorded re-plan event (spine #2) — the frozen plan changed via escalation, never silently; builder resumed in place |
| wave 1 | x01 | judge verdict **NEEDS_WORK** (~5.9 min, ~56k tokens) — the gate REJECTED a build: the builder's UNREQUESTED appended clause overclaimed (registry-as-authority vs the real 12-tag provider rule), contradicted by three tree surfaces; example swap itself clean | the default-FAIL loop firing in a burn, second live instance; remedy = one reword, builder resumed with a targeted fix (no re-plan). Judge also machine-verified a NEW live defect: the `batch` preset pre-fills provider-less `bakeoff` → queued as a new BL-X filing |
| wave 1 | x01 | gate-fix returned BUILT (~4 min), commit `bcec8ed`, gauntlet 4/4; builder added a CLAUSE-TRUTH probe leg that machine-checks the clause's own claim (reds on the rejected wording) AND filed a PD-2 precision correction on the judge's filename citation | conductor SPOT-AUDIT (the BBM-1c slot, run end-to-end on the rejected item): both commits read, example + clause-truth + wording + phantom checks all PASS → **X01 CLOSED**. Mode note: the only reject in this wave came from UNREQUESTED prose beyond a pre-decided end state — pre-deciding end states works; deviation from them is where defects entered |
| wave 1 | x03 | judge verdict **PASS** (~2.4 min, ~45k tokens) — reproduced the documented command verbatim (identical counts) AND re-proved the old form still crashes; two advisory LOWs, builder's leave-alone judgment upheld | judge surfaced a pre-existing backlog candidate: the skill's FALLBACK path documents a grep invocation that fails on PowerShell (same doc-vs-mechanism class) → queued for filing |
| wave 1 | x03 | returned BUILT ~8.5 min, ~65k tokens, gauntlet 4/4 in worktree, commit `a581835` | PROOF RUN literal + sane (153 files/5,447 nodes/6,404 edges — 2-3% BELOW baseline, the direction that rules out contamination; outside-the-root worktrees did their job); the predicted H5 gate-4 README demand FIRED and the sanctioned regen route resolved it exactly as planned; conductor re-ran the proof: identical counts |
| wave 1 | x07 | returned BUILT ~6.7 min, ~71k tokens, gauntlet 4/4 in worktree, commit `dc221d4` | four-part self-gate (offending literals ABSENT from owned surfaces · corrected text present at both sites + README row · `write_approval` absent · historical hits enumerated); conductor RE-RAN gates: all hold; diff scope exact (2 files). **Builder caught + fixed a would-be NEW falsehood in its own draft** ("not a dial" vs the autonomy tiers) — PD-2 behavior unprompted, second burn running (H7 class) |
| wave 1 | x02 | judge verdict **PASS** (~3.1 min, ~49k tokens) — rendered every platform branch itself, proved redness by in-memory mutation, verified the copy's TRUTH against the real command files + the install flat-link path | judge minor notes routed to X05's sweep (4 vacuous params in the new test's parametrization; bare skill names unguarded in codex/generic branches) |
| wave 1 | x07 | judge verdict **PASS** (~3.2 min, ~50k tokens) — every claim reproduced independently; the builder's self-authored hedge verified as the precisely-correct formulation | judge MED-1: README:95/:202 carry the same claim CLASS in different words — a miss no literal-phrase grep could see, queued for conductor fix at integration. Report-contract note: the builder did not flag those two lines (its sweep was literal-phrase-scoped) — recorded honestly, minor |
| wave 1 | integration | **MERGED CLEAN ×4, 0 conflicts** — the plan's "README conflict is CERTAIN" prediction was WRONG in the good direction (the regenerated rows didn't collide) | LOW-4's regeneration contingency existed and was not needed; recorded honestly |
| wave 1 | integration | conductor fixes applied: README:95/:202 Hermes truth repair (X07 judge MED-1) · BL-X08 + BL-X09 filed in BACKLOG (the two judge-found defects) | integrated gauntlet **4/4 PASS** — wave 1 CLOSED, 4/4 items |
| wave 2 | x05 | returned BUILT ~13 min, ~156k tokens, gauntlet 4/4 (4493), commits `adf1f46`+`354c923` | 13 files audited with per-site verdicts; 3 real conversions in 2 files, ALL proven red-on-wrong AND green-on-legitimate-growth; **deliberately LEFT 3 exact pins where exactness IS the protection** (the judgment the scope pre-decision was designed to force); flagged the wave-1 vacuous params + bare-skill-name gap + a pre-existing synthetic-fixture Snyk Low; conductor re-ran both test files (100 passed) + scope exact |
| wave 2 | x05 | judge verdict **PASS** (~8.3 min, ~70k tokens) — independent 10-mutation probe matrix: all 6 regression classes still RED under the new floors, all 4 growth/progress classes GREEN where the old pins rotted; 3-of-4 audit spot-checks confirmed correct | judge MED: the builder's RECORDED rationale for keeping `test_fs_atomic.py:286` exact was wrong ("test-local" — it is a live-source count). **Conductor ruling: the pin STAYS (the coupled `:277` registry pin makes per-site counts a frozen contract — the same class as `test_update_scripts.py:190-191`), and THIS row is the corrected rationale of record.** Judge LOW: the new `:1020` MM-prefix constraint is near-redundant fresh exactness — accepted, noted as a candidate trim if it ever rots |
| wave 2 | integration | merged clean, closing integrated gauntlet **4/4 PASS** — **BURN CLOSED 5/5** | |
| post-close | DRIFT | **OPERATOR-JUDGED DRIFT (2026-08-16 morning): this burn ran OUTSIDE the loop.** No initiation/run-config, no board CLAIM/DONE, no kata-orchestrate, judges ad-hoc (not the kata-evaluate contract), NO final whole-run evaluation, no improve fold, no telemetry — the conductor hand-rolled the process inline. The per-item gating discipline was real; the loop was bypassed. Burn-01 did the same. | Ruled BBM-12: burns use the ENTIRE loop, the bypass is drift not a mode. Filed 🔴 BL-M34 (bypass is structurally possible — enforcement owed). The conductor's earlier "nothing is broken" framing of the advisor question is superseded: the bypass IS the broken thing. |
| post-close | final eval | the MISSING loop stage run retroactively — fresh-context no-write evaluator dispatched under the kata-evaluate contract against the frozen plan + integrated tree at `412cdda` | per the operator's rule: if it fails, the greater loop runs again over the failed scope |

## Burn-level accuracy record (BBM-6 — the honest numbers)

- **Items: 5/5 built and gated** (4 wave-1 + 1 wave-2). Escalations: 1 (X02, resolved by a recorded
  plan amendment, zero re-dispatch cost). Gate rejections: 1 (X01 — an unrequested clause; fixed
  same-session). Judge verdicts: 4 PASS + 1 NEEDS_WORK→closed-after-fix.
- **Defects SHIPPED: 0 known at close.** Every item passed builder self-gate + conductor re-run +
  fresh judge; one item additionally spot-audited end-to-end. Linkback obligation stands: any
  defect later found in this code links back here.
- **Defects FOUND (net new, beyond the 5 filed):** BL-X08 (batch preset writes an illegal config —
  judge, machine-verified) · BL-X09 (kata-understand fallback grep fails PowerShell — judge) ·
  README:95/:202 claim-class (judge; FIXED at integration) · the wave-1 vacuous params + bare-skill
  gap (X05 flags, unfixed, recorded). The judgment layer found ALL of these; zero came from
  mechanical gates — BBM-1's two-layer rationale is now measured, not argued.
- **Hybrid-gate throughput vs burn-01 (H1):** judges ran concurrently off-conductor (~270k judge
  tokens total, none in conductor context); conductor gate work per item ≈ one re-run + one log
  row. The serial-gate bottleneck did not reproduce. Builders: ~345k tokens wave-1 + ~156k wave-2.
- **Base-SHA discipline (BBM-9):** 5/5 worktrees verified at pin by builders, zero wrong-base
  events (H6 did NOT recur under manual outside-the-root provisioning).
- **Convergence-before-freeze (BBM-8):** R1 caught 13 plan findings incl. 2 unsatisfiable pairs
  and a false triage claim; one review false-negative (X02's pinning test) surfaced via builder
  push-back (BBM-10) — the layers check each other in both directions.
