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
| wave 1 | BURN-A · B · C | **dispatched concurrently, 3 isolated worktrees** | all three returned green independently |
| wave 1 | integration | **MERGED CLEAN, 0 conflicts** | gauntlet 4/4 on the integrated tree; pytest 4411 → **4452** |
| wave 1 | BURN-C | confinement HELD | `_module_to_path`/`_node_text` byte-identical, proven by AST extraction |
| wave 1 | gate | **PASS** | conductor re-verified: 3-tuple wired, 3 surfacing sites, zero residual `.write_text` in all 6 writers |
| wave 2 | baseline | gauntlet 4/4 PASS re-run at `d3fb968` before dispatch | pytest 4452/3 skip · integration 2/2 · ruff clean · validator 49/0/0 |
| wave 2 | provisioning | host auto-worktree FAILED (case collision) + left 2 orphans at the WRONG base | see H6-repeat section; conductor provisioned manually at the pinned SHA |
| wave 2 | BURN-D · E | **dispatched concurrently, 2 manually-pinned worktrees** (2026-08-15) | briefs carry step-0 base verification + push-back instruction |
| wave 2 | BURN-E | returned green ~4.5 min, 56k subagent tokens, gauntlet 4/4 in worktree | gate: diff = exactly the owner set (2 files, +7); glob claim + no-count-pins re-verified by conductor's own probes |
| wave 2 | BURN-D | returned ~11 min, 134k subagent tokens, gauntlet **3/4** + ESCALATION | the red was the escalated pin, not the build; 33 new tests, non-vacuity 16/33 fail under neutralization |
| wave 2 | BURN-D | **signature delta, reported not substituted** | brief's 2-arg shape cannot support the modules check (no name convention module→provider); builder added `provided_modules` derived from `kata/module/*` tags + a bridge `available_from_skills` |
| wave 2 | integration | merged clean ×2, 0 conflicts; conductor fixed the escalated pin (floor ≥0.17.0, not exact) + README/AGENTS command rows | validator probed independently: 5 fresh cases incl. reproducing the config.md:14 doc-delta |
| wave 2 | gate | **PASS** — integrated gauntlet 4/4 (`53cecf8`) | pytest-unit green post-pin-fix · integration 2/2 · ruff clean · validator 49/0/0 |
| wave 3 | BURN-F | documented command IMPOSSIBLE: `--root ..` refused by `_safe_path` (kata-understand SKILL.md:47) | doc-vs-mechanism collision class again; ran with absolute paths instead |
| wave 3 | BURN-F | first rebuild CONTAMINATED: 43,064 nodes — six embedded worktrees counted the repo ~7× | graph_gen has no worktree exclusion; a MID-BURN graph rebuild is structurally garbage (mode-relevant) |
| wave 3 | BURN-F | **honest measurement after worktree cleanup: 25 files/450/532 → 157 files/5,560/6,629** | the July + BURN-C fixes plainly densified the map; old graph saw ~16% of the repo |

---

## H1 — RESULT: gating is the bottleneck, and by a wide margin

**Status: CONFIRMED.**

Three builders ran **concurrently** — wall-clock ≈ the slowest one (~16 min), not the sum. They
consumed ~345k subagent tokens between them, none of it from the conductor's context.

Gating them was **serial and entirely conductor-context**: read three reports, check branch bases and
diff scope, merge three branches, run one integrated gauntlet (~3 min), then independently re-verify
each builder's central claim rather than trust it.

**The asymmetry is the finding.** Builders scale out; the gate does not. A burn mode that adds
builders without changing the gate just moves the queue. **Design implication:** the mode needs either
parallel gating (independent gate agents per item, with the conductor adjudicating only conflicts), or
gates cheap enough to be mechanical — and note the repo already has the machinery for the latter
(`gauntlet.py`, the mutation pins, the residual-`write_text` style assertions the BURN-A builder wrote
itself). **The cheapest wins are gates the BUILDER writes and the conductor merely re-runs.**

---

## H6 — Worktree provisioning silently used the wrong base

**Status: CONFIRMED — reported independently by TWO of three builders, which is why it is credible.**

BURN-B and BURN-C both found their worktree checked out at `d4650fc`, one commit behind the pinned
base `3e10ce4`. Both noticed, both verified `d4650fc` was a direct ancestor whose only delta was two
`.planning/` docs, and both branched from `3e10ce4` as briefed.

**This time it was harmless — the source files were byte-identical. It would not always be.** A base
differing in *code* would have produced silent build-on-stale with every worktree green.

**Mode rule:** a burn must **verify each worktree's base SHA before the builder starts**, not trust the
provisioning. Cheap: one `git rev-parse` in the brief's preamble, reported back. Add it to the standing
rules.

*(Credit where due: this was caught only because the briefs told builders to report anything that did
not match. A builder that silently "fixed" it would have hidden a real infrastructure defect.)*

---

## H7 — Builders caught things the grill missed, because they were told to push back

Standing rule #2 ("verify a primitive before reusing it; if it does not expose the surface, SAY SO AND
STOP") paid for itself three times in one wave:

- **BURN-A** refused to edit `fs_atomic.py:21-24` (stale docstring, out of owner set) and **flagged it
  instead** — correct, and the conductor fixed it at integration.
- **BURN-B** found that `protocol/exec-safety.md:53-55` records `_default_runner` *semantically*, so
  the fingerprinted file needed no edit — turning a predicted escalation into a non-event, with
  evidence.
- **BURN-C** found a **pre-existing** defect as a side effect (the old fallback returned `['src']` for
  a directory containing no Python at all) and pinned it with a test; and reported that two of its six
  new tests **passed vacuously at RED**, volunteering that they are regression guards rather than
  reproductions. That is PD-2 behaviour nobody asked for by name.

**Mode rule:** brief builders to push back explicitly. The instruction "if the brief is wrong, say so
and stop" is what converts a builder from a code-typist into a second reviewer — and it costs one
sentence.

---

## H5 — SECOND INSTANCE, wave 2: the brief mandated three things that cannot all hold

`test_validate_prime_directives.py:479` hard-pinned the literal `version: 0.17.0` against the real
kata-orchestrate SKILL.md (a KH-T12 TDD leftover). The BURN-D brief simultaneously required (a) the
0.18.0 bump, (b) a 4/4 gauntlet, and (c) never touching another test file. **All three could not
hold.** The builder chose correctly — kept the bump (also enforced by `check_bump_on_modify`, so
skipping it just reds a different gate), kept ownership discipline, and STOPPED on the gauntlet with
a precise escalation naming the one-line conductor-owned fix.

Two mode lessons, one new:
1. (H5 restated) every "green gate" demand must be checked against what the gate actually requires —
   this time the collision was **latent in the test suite**, not in the standing rules, so no contract
   review of the *brief* could have caught it; only building finds it.
2. **NEW: an exact-version pin against a living file is a time bomb.** The right assertion for
   "the doctrine landed at 0.17.0" is a FLOOR (`>= (0,17,0)`) plus the doctrine text — an exact string
   reds on every legitimate future bump and trains people to edit tests under pressure. Fixed at
   integration (floor + semver parse); grep for the same class before the next burn.

**Escalation cost, measured (H1 data):** the escalation round-trip cost zero builder re-dispatch —
the builder shipped everything it owned and handed the conductor a one-line fix with file:line and
two candidate shapes. That is the cheap-escalation shape the mode wants: STOP at the exact collision
point, not at the start of the item.

---

## H6 — REPEATED in wave 2, by a different provisioner (2026-08-15)

Wave 2 dispatch (a fresh session, eleven days later) hit the same class twice in one minute:

1. **The host's auto-worktree isolation refused to provision at all** on this repo — a Windows
   path-casing collision (`C:\dev\projects\KataHarness` cwd vs. git's canonical
   `C:/Dev/Projects/KataHarness`) that the isolation checker reads as a working-tree redirect.
   Fallback: the conductor provisioned worktrees manually via `git worktree add <path> -b <branch>
   <pinned-SHA>` and dispatched builders at explicit paths.
2. **The two half-created worktrees the failed attempts left behind sat at `d4650fc` — one commit
   behind the pinned base `3e10ce4`-lineage tip `d3fb968` — the exact H6 wrong-base failure, again,
   from different machinery.** Wave 1's provisioning and wave 2's host provisioning failed the same
   way independently.

**Mode rule, upgraded from H6:** wrong-base provisioning is not a one-off — two independent
provisioners produced it. The base-SHA verification MUST be structural (step 0 of every brief,
builder-verified and reported), and the conductor pinning the SHA into `git worktree add` itself is
strictly better than trusting any auto-provisioner. Manual provisioning at a pinned SHA costs one
command and removes the class.

---

## RETROACTIVE DRIFT RECORD (2026-08-16 — added per AV-2 M9; this run's record owed it too)

**This burn ran OUTSIDE the loop** — conductor-driven host dispatch, no initiation/run-config,
no board CLAIM/DONE, no kata-orchestrate, ad-hoc gating briefs, no final whole-run evaluation,
no improve fold, no telemetry rows. At the time it was framed as "the prototype"; the operator
ruled on 2026-08-16 (BBM-12) that burns use the ENTIRE loop and this shape is DRIFT, not a mode
— a ruling that indicts burn-01 equally (🔴 BL-M34: "the harness's own burns just did it
twice"). The evidence H1–H7 collected here remains valid AS evidence; the run's process does
not. Recorded retroactively so this file stops reading as a clean run.

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
