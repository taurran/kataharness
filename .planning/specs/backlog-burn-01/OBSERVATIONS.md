---
spec: backlog-burn-01
kind: mode-design evidence
opened: 2026-08-04
purpose: evidence base for a new KataHarness "burn" operating mode (operator-directed)
---

# OBSERVATIONS — backlog burn #1

**Why this file exists.** The operator directed that the burn become a first-class KataHarness mode:
ingest a large item set (backlog, design issues, and later **external tickets/issues**), collect
context broadly, run **one comprehensive grill across the whole set**, then burn it in preplanned
waves with parallel agents — *throughput without losing accuracy*.

This run is the prototype. **Its second deliverable is evidence.** Recorded as it happens, not
reconstructed afterwards — a reconstructed account is exactly the kind of assertion-without-proof
`PD-2` forbids.

---

## H1 — The conductor's gating capacity is the throughput limit, not the builders

**Status: OPEN — the central hypothesis of the mode.**

Reasoning going in: builders parallelise freely, but every returned artifact must be gated
default-FAIL by one conductor, and gating means reading the diff, re-running the gate, and
reproducing the evidence *independently*. That is serial and context-expensive.

If confirmed, a burn mode cannot simply add more builders — it needs cheaper gates, parallel gating,
or gates placed differently. **Record: wall-clock and context cost of dispatch vs. gate, per item.**

---

## H2 — Items change materially under investigation, so triage must be mandatory

**Status: SUPPORTED before execution even began — 2 of 6 items changed.**

- **`T-06`** was filed as "read files back after writing". Investigation showed readback would **not**
  have caught the corruption this repo actually reproduced (a concurrent reader seeing a partial
  file — the writer's own readback succeeds and sees nothing), and that the wrong-PASS exposure it
  implied is already closed by `D136` fail-closed readers. The real gap was a different one: an
  atomic-write conversion that stopped short of six gate-critical writers.
- **`BL-M20`** was filed as "the loop component can't be started from any command", implying a dead
  component. It is referenced **23 times** across skill files; what is missing is a user entry point
  to the *full cycle* including closeout and the loop-back.

**If a third of a set is mis-filed, building straight from a backlog is building the wrong things.**
Provisional mode rule: **triage precedes the grill; the grill is written against findings, not
against filings.**

---

## H3 — A broad grill amortises understanding AND misunderstanding

**Status: OPEN — the named accuracy risk.**

The efficiency of one grill across many items is also its danger: a wrong assumption in a combined
contract propagates into every item built from it. In one session the conductor made **four**
assume-a-primitive-fits errors (`_run_git` for file content · git `-M` for rename detection ·
`contract-gate.json` cited as proven prior art when it has a writer and no reader · a probe reading
fields off the wrong dict level). At burn scale that class multiplies.

Standing rule #2 ("verify a primitive before reusing it; if it does not expose the surface, say so and
STOP") exists for this. **Whether builders actually honour it is itself a finding.**

---

---

## H4 — ★ THE BIGGEST MODE FINDING SO FAR: file-level disjointness is the WRONG safety property

**Status: CONFIRMED before a single builder was dispatched. This one is load-bearing for the mode.**

The wave plan proved that no file appeared in two owner sets, and called wave 1 safe. **That proof was
insufficient and the wave was not safe.**

`tools/contract_gate.py:33` — `from graph_gen import _module_to_path, _node_text`, called at `:335`.
BURN-A owned `contract_gate`; BURN-C owned `graph_gen`. A root-detection change altering that private
symbol's signature or candidate ordering would silently change `contract_gate`'s dangling-import scan.
**Both worktrees would have passed their own gauntlets. The break lands at integration** — the worst
possible place, because each builder can honestly report success.

Compounding it, **four test files import owned modules and belonged to no owner set**
(`test_contract_gate`, `test_debug_report`, `test_exec_safety`, `test_live_proof_battery`), plus two
repo-wide guard surfaces that AST-walk every `tools/*.py` and pin a `(module, guard)` registry.

**Mode rule this produces — do not re-derive it next time:**
> Wave partitioning MUST be computed over the **import graph**, not the file list. An owner set is
> the module **plus everything that imports it**, plus every test that imports any of those. Where
> full closure is impractical, the contract must **confine** the change to a named function and make
> touching anything else an escalation rather than a judgment call.

This repo has `tools/graph_gen.py` and a code map — **the machinery to compute that closure already
exists and was not used to plan the waves.** That is the concrete tooling gap the mode should close:
a burn should partition waves *from the graph*, automatically.

---

## H3 — CONFIRMED: the broad grill amortised a misunderstanding

Predicted above, and it happened, in the grill's own text. The conductor wrote an `fs_atomic`
import-direction warning that was **exactly backwards** — it flagged `drift_gate`/`deviation` as
possibly disqualified when both are stdlib-only leaves that qualify unconditionally, while the two
genuinely heavy modules were waved through. **A literal reading would have dropped 3 of 8 call
sites**, and the item would have shipped two-thirds done while reporting success.

That is the fifth assume-the-shape error of the session. In a single-item grill it costs one item; in
a combined contract it is a defect in a document six items are built from.

**Mode rule:** the convergence gate is **not optional** in a burn, and it must be given the wave plan
and the standing rules as explicit attack targets — not just the item specs. Every high-severity
finding here was in the *shared* half of the contract, not in any individual item.

---

## H5 — A contract can forbid the thing the gate requires

**Status: CONFIRMED.** Standing rule #5 told builders to bump a `SKILL.md` but never regenerate
`README.md`. But `check_readme_sync` ERRORs the moment a version drifts from the index, and that check
is gauntlet gate 4. **A wave-2 builder literally could not produce a green gauntlet** — the rule and
the default-FAIL gate were mutually exclusive, and the burn would have stalled on first contact.

**Mode rule:** every "the conductor owns this file" restriction must be checked against **what the
gate requires a builder to be able to run.** Shared-artifact ownership is safe only for artifacts that
are *regenerated* (recomputed, discard-and-re-derive) rather than *authored*. `README.md`'s index is
regenerated — so builders may regenerate it freely and the conductor simply re-derives once. The
hand-authored parts of the same file are a different matter and stay conductor-owned.

---

## Running log

*(appended as the burn proceeds — dispatch, gate outcome, deviations, collisions, surprises)*

| when | item | event | note |
|---|---|---|---|
| pre-flight | BURN-A | scope changed by triage | filed fix was wrong; real gap is 8 unconverted call sites |
| pre-flight | BURN-E | framing corrected | not orphaned — 23 references; missing a user entry point |
| pre-flight | BL-M25 | DROPPED | inert by documented deferral in 3 places; deleting it would be the PD-1 violation |

---

## Design questions the mode must answer (collect answers, do not guess)

1. **Where do gates go?** If H1 holds, is default-FAIL gating parallelisable without losing
   independence — or does it need a different shape entirely?
2. **What is the right wave size?** Three concurrent builders is this run's bet. Is the limit file
   disjointness, conductor context, or something else?
3. **How do external tickets enter?** The operator wants issues/tickets as backlog sources. What is
   the minimum an external item must carry to be grillable — and who triages it?
4. **Does the partition rule generalise?** "Builders own code + own tests + own SKILL.md; the
   conductor owns every shared surface" was derived here from a concrete README-regeneration
   collision hazard. Is that the general rule, or an artifact of this repo's shape?
5. **What is the honest accuracy cost?** If a burn ships faster but with a higher defect rate, the
   mode is a downgrade dressed as throughput. This run should produce a number, not a feeling.
