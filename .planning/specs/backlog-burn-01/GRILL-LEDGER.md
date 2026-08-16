---
spec: backlog-burn-01
status: draft
opened: 2026-08-04
baseline: master `d4650fc` · gauntlet 4/4 PASS · working tree clean
tier: combined grill — six items, one contract, three waves
---

# GRILL LEDGER — backlog burn #1

**What this is:** one grill covering six backlog items, frozen as a single contract, executed in three
waves by parallel builders in isolated worktrees, each gated default-FAIL. The point is throughput
without losing accuracy — the loop as written, run wide instead of deep.

## Phase 0 — grounding (measured at `d4650fc`)

Two items were investigated by read-only triage agents; four by the conductor directly. **Two of the
six changed materially under investigation**, which is the argument for grounding before building.

### BURN-A — Atomic gate writes *(was `T-06`, "read files back after writing")*

**The filed item was the wrong fix.** Triage established:
- Nothing in the repo verifies a write. True — but readback would **not** have caught the corruption
  this repo actually reproduced. `tools/fs_atomic.py:4-15` records a live 2026-07-12c investigation
  that reproduced *"phantom IndentationError, empty reads, partial reads"* and proved same-dir tmp +
  `os.replace` gave zero corruption across **12,606 rewrites**. The failure mode is a **concurrent
  reader seeing a partial file** — the writer's own readback would succeed and see nothing.
- The wrong-PASS exposure the item implies **does not exist**: `D136` fail-closed readers already turn
  every realistic corruption into a loud FAIL (`benchmark.py:389-403` floor-FAILs a `RESULT.json`
  missing `failed`; `:443-447` treats a truncated `mutation.json` as vacuous; `kata_telemetry.py:590`
  raises on a malformed ledger row). A truncated JSON object is unparseable, so it lands in the
  fail-closed branch.
- **The real gap:** the atomic-write conversion shipped and then **stopped short of the six
  gate-critical writers.** `fs_atomic.py:21-24` names only five converted call sites.

**Scope:** convert 8 call sites to `fs_atomic.atomic_write_text` — `run_result.py:237`
(`RESULT.json`), `contract_gate.py:512` (`contract-gate.json`), `gate_emit.py:130` (`footprint.json`)
and `:144` (`mutation.json`), `grounding_gate.py:177` (`grounding.json`), `drift_gate.py:524,665`,
`deviation.py:538`. Output is byte-identical (`fs_atomic.py:17-19`), so no artifact changes.
**Watch the import direction** — `fs_atomic` is dependency-free by design and call sites must be leaf
modules; verify `drift_gate`/`deviation` qualify.

**Explicitly NOT built:** readback. Adopting it would contradict the recorded `D159` finding that the
proven fix was atomicity, not verification.

### BURN-B — `DEF-1`: the install check swallows the reason it failed

`tools/kata_preflight.py:397` `_default_runner` returns `(returncode, stdout)`; **4 call sites**
(`:1214, :1299, :1317, :1356`) all discard the second element as `_`, and `RunnerType` at `:949`
pins the shape. When a dependency install or verify fails, the operator sees *that* it failed and not
*why* — the error text is on stderr and is thrown away.

**Resolved without asking — mirror the existing precedent, do not invent.** The identical defect class
was fixed in `kata_dispatch`: `_stderr_tail` (`kata_dispatch.py:189-202`) caps at **4000 chars from
the TAIL** (provider error text — rate-limit/quota/auth — arrives at the *end*), prepends an explicit
truncation marker only when clipped, and decodes tolerantly because `TimeoutExpired.stderr` is bytes
on some platforms. BURN-B reuses that helper's approach so the two paths behave identically.

**Contract change, so it needs its own care:** `RunnerType` widens. All 4 call sites and the test stub
at `tools/tests/test_kata_preflight.py:36` update together.

### BURN-C — `T-08`: the code map is blind to a nested project layout

`tools/graph_gen.py` root detection: a root is the parent of a top-level package, and there is a
`src/` fallback that fires **only when no roots are found at all** and only for a **top-level**
`src/`. The reported hole is that layout nested inside another directory.

**⚠️ Binding build requirement:** the builder must produce a **concrete failing case first** — an
actual directory shape whose roots resolve wrongly — before changing anything. **If no failing case
can be constructed, that is the finding and the item is closed as NOT REPRODUCIBLE.** This repo has
already shipped one fix for this area (2 July); a second speculative fix without a reproduction is
how duplicates get merged. `INGEST-EXECUTION-ORDER.md` warns exactly this: *"Do not merge a duplicate."*

### BURN-D — `BL-M17`: a load-guard that promises fail-closed validation and validates nothing

`skills/coordinate/kata-orchestrate/SKILL.md:38-43` says: *"fail closed (GB12): if it is malformed
JSON, or names a non-existent `mode`/`effort`, a `tiers[family]` that has no `kata-<family>-<tier>`
skill, or a `module` with no provider — STOP and escalate."* The **five bullets immediately after it**
each discharge their promise by naming a real validator — `kata_roles.resolve_roles`,
`kata_telemetry.validate_inline_eval`, `kata_risk.resolve_inline_eval_params`,
`kata_models.validate_advisor_block`, `kata_models.validate_anchor`. **This one names none.**

**The defect is precisely stated:** not that config is prose-owned — that is the design, and the
codebase draws the seam deliberately and repeatedly (`kata_adaptive.py:20-25` hands rung arithmetic to
the caller *by name*; no Python module opens `kata.config` at all). The defect is **a stated
mechanical guarantee with no mechanism**, in a paragraph that reads identically to five real ones.

**Scope:** a new pure `validate_core_config(config, available_skills)` in the style of
`kata_models.validate_advisor_block` — raise on `mode` ∉ {essential, standard, advanced}; `effort`
non-dict or `effort.reasoning` outside its enum; any `tiers[family]` with no matching
`kata-<family>-<tier>` skill on disk (with the `kata-grill: "skip"` legal-value carve-out); any
`modules[]` entry with no provider. Absent key ⇒ documented default (`mode` ⇒ `standard`, D25), so BC
holds. Then replace the un-owned clause with a named call, matching its five siblings.

**`BL-M25` is DROPPED, recorded:** `models.adaptive.l2` and `l2_base_rung` are inert **by documented
deferral** — stated in three independent places (`kata_adaptive.py:79-80`, the function docstring at
`:806-813`, `protocol/config.md:37`) with a named activation precondition (AT-L19, post-R6 ledger
volume). **Do not delete them** to make a dead-code metric go green; that is the exact PD-1/PD-2
posture the harness forbids.

### BURN-E — `BL-M20`: the full improvement cycle has no entry point

**The filed framing was wrong** and is corrected here: `kata-loop` is **not** orphaned — it is
referenced **23 times** across skill files. It is simply not reachable from a slash command.

What that costs, concretely: `/kata-start` reaches initiation → harness, i.e. **a build**. What has no
entry point is the **full cycle** — closeout, the comprehension map, and the context-carrying
**loop-back** that re-enters initiation on version-up. That loop-back is `kata-loop`'s distinctive job.

**Operator ruling 2026-08-04, after reading the skill:** add `/kata-loop`. One pointer command
matching the six that already exist. `kata-loop` is `allowed-tools: [Read, Grep, Glob]` — it composes
and cannot itself write, so the command adds a routing surface, not a drift surface.

### BURN-F — `BL-M26`: rebuild the 45-day-old code map and measure

`.kata/kata.graph.json` was built **21 June** — 45 days — with 450 nodes / 532 edges, and predates
the src-layout fix shipped 2 July. **Safe and repeatable:** `tree-sitter>=0.25.2` and
`tree-sitter-python>=0.25.0` are pinned dependencies, and `.kata/` is gitignored (D81 tier-3,
disposable). Nothing durable is at risk.

**This is a measurement, not a fix.** It must run **after** BURN-C, or it measures the wrong tree.
Report node/edge counts before and after; the value is knowing whether the July fix actually
densified the graph, which has never been checked.

## The wave plan — file ownership is the safety property

**The partition rule (binding on every builder):** a builder owns **its code files, its own test
files, and its own `SKILL.md`**. It owns **nothing shared**. The conductor owns every shared surface
and touches them only at integration.

**Conductor-owned, never builder-owned — and why each would break concurrency:**
- `README.md` — every `SKILL.md` edit requires a version bump, and every bump requires regenerating
  the skill index. Two builders regenerating it collide. **Regenerated ONCE per wave, by the conductor.**
- `.planning/**` (`DEFERRED.md`, `BACKLOG.md`, `STATE.md`, this ledger) — several items close entries
  in the same files.
- `CHANGELOG.md`.
- Protocol fingerprints — a fingerprint re-approval is a deliberate human-reviewed act, never a
  builder's.

| wave | items | why grouped | shared surface |
|---|---|---|---|
| **1** | BURN-A · BURN-B · BURN-C | pure `tools/` code, **provably disjoint file sets**, no `SKILL.md`, no `README` regen | none |
| **2** | BURN-D · BURN-E | both touch `SKILL.md` + adapter/protocol surfaces ⇒ need wave 1 integrated and one README regen | `README.md`, one regen by conductor |
| **3** | BURN-F | measurement; depends on BURN-C landing or it measures the wrong tree | `.kata/` only (disposable) |

**Wave 1 disjointness, verified:** BURN-A owns `contract_gate · run_result · gate_emit ·
grounding_gate · drift_gate · deviation · tests/test_fs_atomic`; BURN-B owns `kata_preflight ·
tests/test_kata_preflight`; BURN-C owns `graph_gen · tests/test_graph_gen`. **No file appears twice.**

**Wave 2 note:** `protocol/config.md` (BURN-D) is clause-pinned but **fingerprint-exempt** — decided
earlier today — so editing it costs no hash re-approval. That exemption is doing real work here.

## Standing rules for every builder in this burn

1. **PD-1 / PD-2 bind.** No silent stub, no "for now". Done requires proof with cited numbers.
2. **Verify a primitive before reusing it.** The conductor made this error **four times today**
   (`_run_git` for file content; git `-M` for rename detection; `contract-gate.json` as proven prior
   art; a probe reading fields off the wrong dict level). If a brief says "reuse X", confirm X exposes
   the surface — and if it does not, **say so and stop**, do not substitute silently.
3. **Never a PowerShell `Get-Content`/`Set-Content` round-trip on a repo file** — it double-encodes
   UTF-8 and adds a BOM. `.gitattributes` pins LF.
4. **Never `kata_telemetry._run_git` to read file CONTENT** — `text=True` with no `encoding=` mojibakes
   every non-ASCII file on Windows. Use `footprint.blob_at_ref` (bytes).
5. **`SKILL.md` edits require a version bump** (`check_bump_on_modify`, shipped today) — but **do not
   regenerate `README.md`**; the conductor does that once per wave.
6. Determinism Doctrine laws 1 (one pinned git helper) and 2 (sorted at every filesystem boundary).

## ★ THIS RUN IS A PROTOTYPE FOR A NEW OPERATING MODE (operator-directed 2026-08-04)

The operator's framing, recorded verbatim in substance: this is *"really the ultimate use of this."*
The burn is to become a **first-class KataHarness mode**:

1. Ingest a **large set** at once — brainstormed items, design issues, backlog entries — and
   explicitly **expand the sources to tickets, issues and other external backlog systems**, not just
   `.planning/BACKLOG.md`.
2. **Collect context broadly** and run **ONE comprehensive grill across the whole set** before any
   execution — position the run for maximum success up front rather than grilling item by item.
3. **Burn the set** in preplanned waves, following the major loop as written, with parallel agents.
4. **Throughput without losing accuracy** is the stated goal.

**So this run has a second deliverable: evidence.** Successes, failures and friction are tracked
deliberately in `OBSERVATIONS.md` alongside this ledger, because the mode should be designed from what
actually happens here rather than from how it was imagined. An unrecorded burn teaches nothing.

### What to record, decided up front so it is not reconstructed afterwards

- **Did the wave partition hold?** Any file collision between concurrent builders is a partition
  design failure, not a builder failure — record which file and which rule missed it.
- **Where was the bottleneck?** Hypothesis to test: *the conductor's gating capacity is the throughput
  limit, not the builders.* If true, the mode must be designed around it (more parallel gating,
  cheaper gates, or a different gate placement).
- **What did the broad grill miss?** Every finding the convergence gate or a builder raises that the
  grill should have caught. This is the accuracy half of "throughput without losing accuracy."
- **Did any item change under investigation?** Two of six already did (`T-06` was the wrong fix;
  `BL-M20`'s framing was wrong). If that rate holds, **triage-before-build must be a mandatory mode
  step**, not an optional one.
- **Per item:** wall-clock, gate outcome (PASS / rejected / deviation-accepted), and whether the
  frozen brief turned out to be wrong.
- **Context cost** — the mode's real economics.

### Named risk this run must watch

A broad grill amortises understanding across many items, which is the point — **and it also
amortises any misunderstanding.** A wrong assumption in a combined contract propagates to every item
built from it. The conductor made four assume-a-primitive-fits errors in a single session today; at
burn scale that class multiplies. This is the specific reason standing rule #2 exists, and whether it
holds is itself a finding.

## Convergence pass 1 — HOLD, 10 findings. The wave plan was unsafe.

Fresh-context no-write reviewer. The decisive findings were re-verified by the conductor and **all
were true**. The amendments below **supersede** anything above that they contradict.

**The headline: the wave plan's safety property was wrong.** It proved *file-level* disjointness. The
property that actually matters is *dependency-level* disjointness, and wave 1 failed it.

### ⚠️ AMENDMENT 1 — Wave 1 is NOT disjoint; BURN-A and BURN-C are coupled

`tools/contract_gate.py:33` — `from graph_gen import _module_to_path, _node_text`, called at `:335`.
**BURN-A owns `contract_gate`; BURN-C owns `graph_gen`.** A root-detection change that alters
`_module_to_path`'s signature or candidate ordering silently changes `contract_gate`'s dangling-import
scan — **both worktrees green, breaking at integration.**

**Binding fix:** BURN-C is **confined to `_discover_source_roots`** (`graph_gen.py:264-300`). It MUST
NOT touch `_module_to_path` or `_node_text` — signature or semantics. If the fix appears to require
either, that is an **escalation, not a judgment call**: stop and report.

### ⚠️ AMENDMENT 2 — Unowned test files that import owned modules

None is in any owner set: `tools/tests/test_contract_gate.py` (imports contract_gate + graph_gen),
`test_debug_report.py:217` (drift_gate), `test_exec_safety.py:39` and `test_live_proof_battery.py:39`
(kata_preflight). Also repo-wide guard surfaces any builder could trip: `test_exec_safety.py:41,264`
AST-walks every `tools/*.py` and requires each subprocess sink registered in
`protocol/exec-safety.md`; `test_path_guard_family.py:24-55` pins a `(module, guard)` registry
including `graph_gen` and `kata_preflight`.

**Binding fix:** these are **conductor-owned, escalate-on-touch.** A builder that needs to modify one
STOPS and reports. *(Verified benign for BURN-B: `protocol/exec-safety.md:53-55` records
`_default_runner` semantically, not by signature, so widening its return type needs no registry edit —
and that file is fingerprinted, so this matters.)*

### ⚠️ AMENDMENT 3 — the `fs_atomic` import-direction warning was INVERTED

The original text warned that `drift_gate`/`deviation` might not qualify as leaf modules. **Backwards.**
Verified: `drift_gate.py:42-47` and `deviation.py:34-39` import **stdlib only** — they qualify
unconditionally. The heavy modules are `contract_gate.py:29-34` and `gate_emit.py:30-31`.

`fs_atomic`'s actual invariant is that **`fs_atomic` itself stays stdlib-only**; importing a
dependency-free leaf *from* a heavy module cannot invert any dependency. **All 8 call sites are
unconditionally in scope.** A literal reading of the original warning would have dropped 3 of them.

*(Verified clean and recorded so nobody re-checks: BURN-A changes **no observable bytes** —
`Path.write_text` and `fs_atomic.py:59` `os.fdopen(fd,"w",encoding=...)` both default `newline=None`
with utf-8. And there is **no import cycle**. There is **no `conftest.py`** anywhere in the repo.)*

### ⚠️ AMENDMENT 4 — Standing rule #5 made a green gauntlet impossible

Rule 5 said "bump the SKILL.md but do NOT regenerate README". But `check_readme_sync`
(`validate_skills.py:483,510-521`) renders the version into the index and ERRORs when it drifts, and
`validate_skills.py` is gauntlet gate 4 (`scripts/gauntlet.py:75`). **A builder who bumps a SKILL.md
could not produce a green gauntlet — i.e. could not prove its own work.** The rule and the default-FAIL
gate were mutually exclusive.

**Binding fix:** a builder editing a `SKILL.md` **DOES** run `uv run python validate_skills.py --write`
in its own worktree, so it can prove green. `README.md` is declared a **regenerated, never-merged**
artifact: the conductor discards builder README diffs and re-derives it with one `--write` after
integrating each wave. Regenerated output is not a merge conflict — it is recomputed.

### ⚠️ AMENDMENT 5 — BURN-C: the failing case EXISTS, so "close as not reproducible" is off the table

The reviewer produced it: `backend/src/pkg/mod.py` with **no `__init__.py` anywhere** (PEP-420
namespace, nested). `package_dirs` = ∅ ⇒ `roots` = ∅ ⇒ the fallback at `graph_gen.py:298` tests
`startswith("src/")`, **False** for `backend/src/...` ⇒ returns `[]` ⇒ `_module_to_path` gets no source
roots and **every import edge is dropped.** Second shape: when `roots` is non-empty the fallback is
never reached at all, so a top-level PEP-420 `src/` coexisting with one `__init__.py` package
elsewhere is equally blind.

**Acceptance bar, stated mechanically:** a new test in `tools/tests/test_graph_gen.py` asserting
`_discover_source_roots(...)` returns a demonstrably wrong list for a **synthetic path set**. A
synthetic set counts; a real-world repo is not required.

### ⚠️ AMENDMENT 6 — BURN-D: drop `effort.reasoning`, and pin what was under-determined

**`effort.reasoning` is REMOVED from scope.** `protocol/config.md:15` disclaims its own enum verbatim:
*"these values are indicative, **not an API contract**."* Validating it would contradict the source of
truth, and standing rule #2 obliges a builder to stop rather than invent one.

Pinned, because the reviewer showed two builders would ship different features:
- **Home module:** a **new `tools/kata_config.py`**. Not `kata_models.py` — that is pure and
  import-light, and a skills-on-disk inventory cannot live there.
- **`available_skills: set[str]`** — skill NAMES, not paths.
- **Producer:** `validate_skills.load_skills()` (`validate_skills.py:68`) is the only inventory helper
  in the tree. The SKILL.md call site names it explicitly.
- **In scope:** `mode` ∉ {essential, standard, advanced} · `tiers[family]` with no matching
  `kata-<family>-<tier>` skill (with the `kata-grill: "skip"` carve-out) · `modules[]` with no
  provider. Absent key ⇒ documented default (`mode` ⇒ `standard`, D25).

### ⚠️ AMENDMENT 7 — BURN-B: pin the shape, the cap placement, and the real test scope

- **Signature:** `tuple[int, str, str]` — `(returncode, stdout, stderr)`.
- **Cap placement:** at the **four consumer call sites**, NOT inside `_default_runner`. This mirrors
  the precedent exactly: `kata_dispatch.py:194` states the cap lives in `dispatch()` because it is
  *"the ONE dispatch-side choke point (injected runners cannot bypass it)"*. Putting it in the runner
  would invert that property.
- **`_stderr_tail`:** COPY the approach into `kata_preflight`; do not import a private name across
  modules. `kata_preflight.py:67-75` imports nothing from `kata_dispatch` today and that stays true.
- **Test scope is 66 sites, not "a stub":** `tools/tests/test_kata_preflight.py` has **27**
  `_TrackingRunner` constructions and **39** two-tuple literals, plus `default=(0,"ok")` at `:31`.
  **Decision: normalize short tuples inside `_TrackingRunner.__call__`** so the 39 literals stay
  unchanged. Smaller diff, and the literals stay readable.

### ⚠️ AMENDMENT 8 — BURN-E is not one file, and needs no `SKILL.md` bump

Five surfaces enumerate the command set: `adapters/claude/commands/kata.md:5-11` (the index),
`README.md:291`, `README.md:458-465` (**hand-authored**, outside the `SKILL-INDEX` splice markers, so
`--write` never touches it), `AGENTS.md:45-46`. Installation needs no manifest change —
`_flat_link_commands` globs `*.md`.

**Correction:** there are **five** pointer commands plus the `kata.md` index, not six.
**BURN-E bumps no `SKILL.md`** (`kata-loop` is only read), so it has **no README-regen dependency**.
**Builder owns:** the new command file + `adapters/claude/commands/kata.md`. **Conductor owns:**
`README.md:291`, `README.md:458-465`, `AGENTS.md:45-46`.

### ⚠️ AMENDMENT 9 — BURN-F must not write to the repo root

`modules/closeout/kata-understand/SKILL.md:47` documents
`graph_gen.py --root .. --out ../kata.graph.json` — the **repo root**, which is **NOT gitignored**
(`.gitignore:9` ignores `.kata/` only; `git check-ignore kata.graph.json` exits 1). Following the
documented command drops a ~344 KB untracked artifact at the root.

**Binding: `--out ../.kata/kata.graph.json`.** The repo root is out of bounds.
*(Verified clean: no gauntlet gate reads the graph — every reader is skill prose that degrades
gracefully. D81 disposability confirmed.)*

## Revised wave plan

| wave | items | owner sets |
|---|---|---|
| **1** | BURN-A · BURN-B · BURN-C | A: `contract_gate · run_result · gate_emit · grounding_gate · drift_gate · deviation · tests/test_fs_atomic` — B: `kata_preflight · tests/test_kata_preflight` — C: `graph_gen` **(`_discover_source_roots` ONLY)** · `tests/test_graph_gen` |
| **2** | BURN-D · BURN-E | D: new `kata_config.py` + its test · `kata-orchestrate/SKILL.md` · `protocol/config.md` — E: new command file · `commands/kata.md` |
| **3** | BURN-F | `.kata/` only, via `--out ../.kata/kata.graph.json` |

**Conductor-owned throughout:** `README.md` · `AGENTS.md` · `.planning/**` · `CHANGELOG.md` ·
protocol fingerprints · the four unowned test files in Amendment 2 (escalate-on-touch).

## Status — CONTRACT FROZEN 2026-08-04 (post-HOLD)

All ten findings folded. This ledger is the builders' brief.
