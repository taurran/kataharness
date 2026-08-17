# DEFERRED — parked designed work (kata-defer ledger)

> PD-1 sanctioned deferral path: every entry here is operator-visible, graded at the gate,
> and surfaced at handoff. An entry is closed by the run that builds it (link the record).
>
> **Schema: `protocol/deferral.md`** (the sanctioned-deferral ledger contract). Entries are H2:
> `## DEF-<n> — <title> · <STATUS> (<ISO-date>)`, STATUS ∈ `OPEN | ACCEPTED | CLOSED`, with the
> required **What / Why / Provenance / Owed-to** fields; `accepted_by` / `accepted_at` on an
> operator-approved park, `closing_commit` on a closure. Append-only.
>
> The entries below were retrofitted to that grammar on 2026-08-16
> (`tm-w1-deferral-contract`). Exactly what that changed, per entry, so the claim can be checked
> against the diff rather than taken on trust:
> - **DEF-1** — a field block was **added** under the H2. Its `What` and `Why` values are
>   reproduced from the original filing, which is preserved verbatim further down under its own
>   sub-heading, as is the closure record. Its `Provenance` line, and the final clause of its
>   `Owed-to` line ("discharged ahead of that owner by backlog-burn-01, item BURN-B"), are
>   **newly written** — the first summarising the filing's own audit note, the second restating
>   the closure record's "Closed by backlog-burn-01, item BURN-B".
> - **DEF-2** — **relabelled in place**: `Why deferred` → `Why`, `Owed to` → `Owed-to`. Its
>   `Provenance` line is **newly written**, summarising the filing's own account of where the
>   defect was found. Every other bullet, and the closure record, are untouched.
> - **Both** — a `closing_commit` field was added, each sha resolved against `git log` rather
>   than asserted.
>
> **No entry's substance was changed:** nothing was deleted, no status or date was moved, and no
> claim about what happened was altered. The lines named above are the only prose this retrofit
> authored.

## DEF-1 — kata_preflight._default_runner stderr widening · **CLOSED (2026-08-04)**

- **What:** `tools/kata_preflight.py:397-407` `_default_runner` returns `(returncode, stdout)`
  — same stderr-discard class as the kata_dispatch defect fixed by the dispatch-stderr-fix run.
  *(Verbatim from the original filing, preserved below.)*
- **Why:** the quota-resilience classifier (its own grilled run,
  `.planning/specs/quota-resilience/REQUIREMENT.md`) decides what preflight signal it consumes;
  widening now is scope creep on a surgical fix.
- **Provenance:** filed OPEN 2026-07-21 by the dispatch-stderr-fix run; grill record
  `.planning/specs/dispatch-stderr-fix/GRILL-LEDGER.md` D4 (operator-approved). Re-assigned
  2026-07-25 by the audit recorded in the original filing below.
- **Owed-to:** ~~the quota-resilience Tier 1+2 run~~ → re-assigned to **quota Tier 3**
  (2026-07-25); discharged ahead of that owner by **backlog-burn-01, item BURN-B**.
- **closing_commit:** `63bd65f` (*fix(preflight): stop swallowing the reason an install or verify
  failed (DEF-1)*, 2026-08-04; merged `fdf4be9`, closure recorded in `d3fb968`).

> **Closed by backlog-burn-01, item BURN-B.** `RunnerType` is now
> `Callable[[list[str]], tuple[int, str, str]]` and `_default_runner` returns
> `(returncode, stdout, stderr)` **uncapped**. The 4000-char tail cap is applied at the **four
> consumer call sites**, not inside the runner — deliberately mirroring
> `kata_dispatch.py:194`'s choke-point property (*"injected runners cannot bypass it"*); putting
> the cap in the runner would have inverted it. `_stderr_tail` was **copied**, not imported:
> `kata_preflight` still imports nothing from `kata_dispatch`, pinned by a new AST test.
>
> **Wired, not merely captured** (the PD-1 risk in the brief): install failure and post-install
> re-verify failure append the tail to their `blockers` entry; a failing `target.baselineGate`
> probe appends to its degraded `warnings` entry. The **first** presence check deliberately does
> NOT surface — a non-zero there is the designed "dependency is absent" control signal routing to
> the install path, not a failure — and that asymmetry is pinned by its own test so it is not
> "fixed" by mistake later.
>
> **Proof:** integrated gauntlet 4/4 PASS, pytest 4452 passed / 3 skipped. Non-vacuity checked by
> neutralizing the install-path surfacing, which failed exactly 2 of the new tests, then reverting.
> Conductor verified independently: `RunnerType` at `kata_preflight.py:139`, `_default_runner` at
> `:399`, three surfacing sites at `:1354, :1385, :1433`.
>
> *(The original entry is preserved verbatim below — it is the record, and its "size when picked up"
> estimate is worth comparing against what the work actually took.)*

### Original entry — kata_preflight._default_runner stderr widening · OPEN (2026-07-21)
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

## DEF-2 — learn_feed drops entry bodies for the indented-sub-bullet ledger style · **CLOSED (2026-08-04)**
- **What:** `tools/learn_feed.py:511-518` renders `body` **only** when no recognized field is
  non-empty (`present = [k for k in _SECTION_ORDER …]; if present: … elif body_text:`). The house
  ledger style — `- **Decision:**` followed by indented sub-bullets — parses to an **empty**
  `decision` and orphans the content into `body`, which is then never rendered.
- **Measured:** running the shipped parser over
  `.planning/specs/session-lifecycle/GRILL-LEDGER.md` drops body content from **20 of 29** entries
  then measured — **19,153 characters**. Six repair entries parse with `decision=''`; the SL-19
  page renders with **no Decision section at all**.
- **Blast radius — NOT limited to one grill:** D151/G1 fires the emit at **every** grill close, and
  the same style is used across `.planning/specs/` (19 ledgers). Any of them emitting today
  publishes decision-less synthesis pages to the vault — a PD-2 violation written to a durable
  store.
- **Provenance:** filed OPEN 2026-07-27 out of convergence pass 2 of the session-lifecycle grill
  (which was itself HELD); the measurement above was taken by that pass against the shipped parser.
- **Why:** discovered by convergence pass 2 of the session-lifecycle grill (2026-07-27),
  which was itself HELD. The fix is a real design choice that belongs to its own grill, not to a
  repair pass: **either** extend `_FIELD_PREFIXES`/`render_page` to handle indented sub-bullets,
  **or** flatten ledger entries to single-paragraph fields (which changes the authoring convention
  for every future grill).
- **Interim posture:** the session-lifecycle grill-close emit is **NOT run**. Whether the block
  extends repo-wide to all 19 ledgers is **an open question this entry does not decide** — it is the
  first thing the owning run must settle.
- **Owed-to:** ~~unassigned~~ → **CLOSED by the `learn-feed-body-loss` run** (branch
  `fix/learn-feed-body-loss`), whose frozen contract is
  `.planning/specs/learn-feed-body-loss/GRILL-LEDGER.md` (LFB-1..LFB-4).
- **Evidence:** `.planning/specs/session-lifecycle/CONVERGENCE-HOLD-2.md` (NEW-7) and
  `CONVERGENCE-HOLD-3.md`.
- **closing_commit:** `0f8e5f4` (*fix(learn_feed): stop discarding the body of most ledger entries
  (DEF-2 + BL-M24)*, 2026-08-04; merged `d4650fc`). Closure evidence is the record below.

### Closure record — measured, not asserted (2026-08-04)

**What was built.** `render_page`'s `elif body_text:` became an independent `if`
(`tools/learn_feed.py`): parsed fields render as before, and the entry body now renders **in
addition** under a new `## Detail` section. The field-less path is untouched — with no field
parsed the body still renders under `## Decision` (the MM `· LOCKED` form), pinned by
`test_render_body_only_still_uses_decision_heading`. LFB-2 rode along: `_HEADING_LINE_RE`
narrowed `^#{1,6}` → `^#{2,6}` so a ledger's own H1 title is no longer parsed as an open entry.

**Before → after**, same probe, re-run over the same 22 ledgers (drop decided by RENDERING each
entry and checking the body reached the page, so the probe is version-agnostic; it was
sanity-checked against the ORIGINAL code first and reproduced Phase 0 exactly):

| measure | before (HEAD `44118ae`) | after |
|---|---|---|
| entries whose body is dropped | **68** | **0** |
| characters lost | **46,427** | **0** |
| entries parsed | 218 | 207 (−11 phantom H1 titles) |
| phantom `GRILL-LEDGER` H1 entries | 8 | 0 |

DEF-2's own filed numbers were on `session-lifecycle` — **20 of 29 entries / 19,153 chars** when
filed; that ledger measured **25 of 37 / 23,363 chars** at closure and now drops **0**. The worst
four (`session-lifecycle` 25 · `ungated-protocol-files` 11 · `bump-on-modify` 7 ·
`evaluator-dispatch-record` 6) all go to 0. Visible instance: the `ungated-protocol-files` UPF-4
page rendered **1,133 chars** before (both `Rejected — …` alternatives and the follow-up silently
gone) and **2,000 chars** after.

**The interim block is LIFTED, not carried** (LFB-3): the block existed only because the blast
radius was unmeasured. It is measured and repaired at source, so the open question *"does the block
extend to all 19 ledgers?"* is closed by there being no block. `engram.learnFeed.dir` stays unset —
this run rendered in memory for proof only and emitted to no vault.

**Green:** `cd tools && uv run python scripts/gauntlet.py` → **4/4 PASS** (pytest-unit 4411 passed
/ 3 skipped / 2 deselected · pytest-integration 2 passed · ruff clean · validate-skills 49 skills,
0 errors, 0 warnings). Ten new tests in `tools/tests/test_learn_feed.py` (module 70 → 80), including
two that re-run the corpus measurement as assertions so a regression fails the gate rather than
publishing quietly.

**Not closed by this entry:** the option DEF-2 floated of extending `_FIELD_PREFIXES` to parse
indented sub-bullets *into* fields was rejected in the grill (LFB-1) — the tool was wrong, not the
writing, and no ledger's authoring style was changed.

## DEF-3 — test_exec_safety `_SHELL_TRUE_ALLOWLIST` still permits `mutation_run.py` · OPEN (2026-08-16)

- **What:** `tools/tests/test_exec_safety.py:33` `_SHELL_TRUE_ALLOWLIST` still lists
  `mutation_run.py`, though the module's `shell=True` sink was converted to structured argv by
  BL-X14 (`b996ee1`, merged `e484ce3`). The over-broad permit would silently re-allow a future
  `shell=True` in that module. Removal is proven green (empirically run by the
  `tm-w1-exec-safety-registration` follow-up: offenders `[]` with the reduced set; the doc
  assertion for `run_result` unaffected).
- **Why:** the test file is in no wave-1 task's ownership; editing it mid-wave would be an
  unowned-file lane violation. Risk is contained: `test_mutation_run.py`'s AST pin already
  fails any `shell=True` reappearing in `mutation_run.py`, so the allowlist entry is redundant
  permissive defense-in-depth, not a live hole.
- **Provenance:** flagged by the BL-X14 builder (out-of-scope discovery 2), removal proven by
  the exec-safety follow-up (`15dc23b` report), parked by the conductor at wave-1 integration.
- **Owed-to:** the next wave that owns `tools/tests/` guard files (W6 `judge-tripwire-corpora`
  or W7 `gate-preconditions` may absorb it as a one-line ride-along, conductor to assign at
  that wave's briefs; otherwise the burn closeout sweep).

## DEF-4 — no skill-to-role map exists; ROLE_GROUPS has no reporter role · OPEN (2026-08-17)

- **What:** `kata_roles.ROLE_GROUPS` is a closed enum but nothing maps a skill to a role.
  The W4 orchestrate migration authored the role column in its LS registry in-file and
  declared it authored-there; five picks are named contestable in the file, and
  `kata-benchmark-report` ⇒ `researcher` is the weakest fit (no reporter role exists).
- **Why:** widening the role enum is a cadre-grill decision (kata_roles.py:13 says so);
  inventing it mid-burn would be drift.
- **Provenance:** tm-w4-orchestrate-seam-migration builder deferral 1; judge residual R4.
- **Owed-to:** the cadre grill / planning-window backlog (role map + possible reporter role).

## DEF-5 — no engine helper enumerates arms / child runIds · OPEN (2026-08-17)

- **What:** exactly-once arm spawn is checked by scanning `dispatch_dir()` + `consumed/` for
  a record with `taskId == arm_label` (works because records are retained after consumption).
  The proper helper is named as a gap in kata-orchestrate/SKILL.md ~:235-238.
- **Why:** out of every W4 task's ownership (engine code); the workaround is correct on the
  shipped surface (judge-verified) but should not calcify.
- **Provenance:** tm-w4-orchestrate builder deferral 2 (a removed reuse over-claim).
- **Owed-to:** a W5+ engine fast-follow or the backlog.

## DEF-6 — phase boundaries are instructed, not mechanically checked · OPEN (2026-08-17)

- **What:** kata-orchestrate pins four phase boundaries, but no check asserts every
  `open EXECUTION wave=<n>` is eventually closed.
- **Why:** the natural home is close-machinery (W7) or a validator check — not W4 prose.
- **Provenance:** tm-w4-orchestrate builder deferral 3.
- **Owed-to:** W7 close-machinery adjacency, else the backlog.

## DEF-7 — skill renames have no registry-completeness check · OPEN (2026-08-17)

- **What:** three registries key on skill identity (kata_models.SKILL_WORK_CLASS, adapter
  command files, the generated README index) and only the README is validator-enforced. The
  board→cursor rename silently broke the first two until the G17 sweep; a SKILL_WORK_CLASS
  absence silently tiers a skill UP to critical/anchor (kata_models.py `.get(skill, "critical")`).
- **Why:** fifth first-use/keyed-registry-with-no-on-ramp instance (fingerprints D-8, guard
  family D-20, _safe_kata_dir D-24, ledger frontmatter D-16); the pattern deserves one fix.
- **Provenance:** tm-w4-coordinate builder deferral DEF-b; the G17 sweep is the evidence.
- **Owed-to:** planning-window backlog — a rename-completeness check.

## DEF-8 — CONTEXT.md:234 still illustrates the retired 5-field cursor grammar · OPEN (2026-08-17)

- **What:** the glossary's example shows the 5-field line the canonical parser now REFUSES
  (test_kata_board.py calls it a parse refusal). Path refs were fixed by the G17 sweep;
  the grammar example was deliberately left (content change, not a rename ref).
- **Why:** glossary content is kata-context's surface; rewriting it was outside the sweep's
  mechanical grant.
- **Provenance:** tm-w4-cursor-rename-sweep builder deferral 1.
- **Owed-to:** a kata-context glossary pass.

## DEF-9 — protocol/deferral.md has no mechanical conformance validator · OPEN (2026-08-17)

- **What:** kata-defer now emits the canonical grammar and the templates were proven
  parseable by a throwaway script, but nothing committed checks live DEFERRED/ASSUMPTIONS
  entries; conformance is Honor-system until W6 truth_serum lands B3 (and B3 covers the
  same-line BLOCKER rule, not a full entry-schema parse).
- **Why:** committing a parser tool is a deliberate Python-surface judgment call (operator
  preference: keep tools/ minimal); not decided mid-wave.
- **Provenance:** tm-w4-authoring builder deferral DC-1.
- **Owed-to:** W6 blocking-detectors brief notes the boundary; a parser tool = operator call.

## DEF-10 — grill convergence/status-write duties are triplicated across tier files · OPEN (2026-08-17)

- **What:** the convergence-pass record + grill-close status write live near-duplicated in
  the three grill tier SKILLs; `skills/plan/kata-grill/RUBRIC.md` is the tier-invariant home
  but was in no W4 grant, and its "Grill-close emit" section still omits the status write
  (a RUBRIC-only reader could close a grill without writing `status: converged`).
- **Why:** consolidating needed an un-granted file; duplication was the fence-respecting shape.
- **Provenance:** tm-w4-authoring builder deviation 2 + deferral DC-2.
- **Owed-to:** the next authorized touch of kata-grill/RUBRIC.md (kata-improve or a later wave).

## DEF-11 — deferral.md pins .planning/DEFERRED.md absolutely; wrong for non-.planning targets · OPEN (2026-08-17)

- **What:** the contract hardcodes `.planning/DEFERRED.md`/`.planning/ASSUMPTIONS.md`; a
  target repo with a different planning root has no defined ledger home. kata-defer now
  writes the pinned path (contract wins) without inventing a resolution rule.
- **Why:** resolving it is a protocol amendment (fingerprint two-step), not a W4 skill edit.
- **Provenance:** tm-w4-authoring builder deferral DC-3.
- **Owed-to:** a deferral.md amendment at a later wave / backlog.

## DEF-12 — claim/capture refusals raise typed exceptions but write no cursor DENY event · OPEN (2026-08-17)

- **What:** `kata_dispatch.deny()` (the §1.8 "every denial is a cursor DENY event" law) is
  invoked only on the mint/governor refusal path. `RecordClaimRefused` (replay/lost
  election) and `CaptureRefused` (no line-1 verdict) raise typed exceptions naming the
  legal path but append nothing to the cursor — a refusal a later reader of the cursor
  cannot see. The wave-4 final eval surfaced the boundary by falsifying a conductor record
  claim that conflated the two (F2, cured in the wave-4 erratum).
- **Why:** whether §1.8's law SHOULD extend to claim/capture refusals is a design ruling
  (cursor noise vs auditability trade), not a mid-burn patch; the current behavior is as
  built and tested in W3, not a defect against any frozen acceptance.
- **Provenance:** wave-4 FINAL EVAL round-1 finding F2 + its cure record.
- **Owed-to:** a DESIGN §1.8 boundary ruling — W7 close-machinery adjacency or the backlog.

## DEF-13 — refuse-to-mint names a park path nothing is obliged to create · OPEN (2026-08-17)

- **What:** `MintRefused` computes and names `.kata/escalations/<taskId>.json` as the legal
  path (TM-B5), but no code writes it — parking is left to the caller
  (`escalation.write_escalation`), and nothing binds the caller to do it. An unattended
  refusal can therefore die silently DESPITE the message promising a park, which is the
  exact silent-death TM-B5 exists to prevent. Sibling of DEF-12 (refusals that leave no
  cursor DENY): both are §1.8-adjacent "the message claims more than the machinery does"
  boundaries.
- **Why:** binding the park into the refusal path (or into a caller contract) is a design
  ruling with API consequences (who owns the escalation payload's required fields at
  refusal time?) — not a mid-burn patch.
- **Provenance:** wave-4 FINAL EVAL round-2 finding F3 + its cure record (the conductor
  itself ran the probe bare and copied the narration as fact).
- **Owed-to:** a DESIGN §1.8/TM-B5 boundary ruling — with DEF-12, W7 adjacency or the backlog.

## DEF-14 — post-G21 staleness: grill-tier residual paragraphs + engine docstring rows · OPEN (2026-08-17)

- **What:** kata-grill-standard/SKILL.md:61-65 and kata-grill-advanced/SKILL.md:70-74 still
  say the convergence-reviewer function has no role token (G21 assigned it to `reviewer`),
  and their kata_dispatch.py:458-468 anchor shifted with the comment rewrite;
  `check_governor`'s docstring ladder table (~:962) and `mint`'s (~:959) omit the reviewer
  token from the grill-phase row.
- **Why:** the grill tiers are W4-owned files (closed wave) and the docstring lines sit
  outside the G21 region grant — fixing either mid-loop would have been ownership drift.
- **Provenance:** tm-la-judge-contract-rewrites deferral 1+2; judge residual 1 (3 rounds).
- **Owed-to:** a small authorized sweep (Loop C/D window) or kata-improve.

## DEF-15 — the `allowed=` enum binding is wired at ONE of six judge dispatch sites · OPEN (2026-08-17)

- **What:** the W5 contracts pin per-judge closed enums, but only LS-31 passes
  `allowed={"PASS","NEEDS_WORK"}` at capture; the reviewer (LS-06/27/34/39), slop (LS-32)
  and inline-eval (LS-11/14) sites pass bare `capture(kind="verdict")`. The contracts now
  say DECLARED-not-yet-wired honestly (cure 68e03f2).
- **Why:** the wiring lives in kata-orchestrate/SKILL.md (W4-owned, closed); wiring it
  mid-Loop-A would have been drift.
- **Provenance:** judge-contract-rewrites judge F1 + residual 4.
- **Owed-to:** the next authorized kata-orchestrate touch (W8 hook wave is adjacent) or a
  dispatched mini-task; the honest label must not calcify.

## DEF-16 — truth_serum's B3 self-blocks the detector's own source · OPEN (2026-08-17)

- **What:** protocol/deferral.md:177-178 carves out the LEDGER from the same-line rule but
  not the detector module whose regexes/contract name the same markers; any future task
  modifying tools/truth_serum.py self-blocks with 12 findings.
- **Why:** adding a self-exemption is not in the frozen DESIGN; E3 forbids silent suppressors.
- **Provenance:** tm-la-blocking-detectors builder DC-1; conductor spot-audit corroborates
  the input-set question (W7 gate-preconditions chooses B3's inputs).
- **Owed-to:** gate-preconditions (Loop B, stacked) rules the input set; a deferral.md
  carve-out widening is the fallback (its own two-step).

## DEF-17 — swap S2's default resolver to truth_serum's B5 · OPEN (2026-08-17)

- **What:** truth_signals.prose_claim_signals ships a local existence-only resolver with an
  injectable seam proven load-bearing by test; now that truth_serum.resolve_citations is
  merged in the same tree, the swap is a one-call-site change.
- **Why:** both modules were built concurrently in disjoint grants; neither could import
  the other's unmerged branch.
- **Provenance:** tm-la-signal-detectors builder deferral 1.
- **Owed-to:** a Loop B/C fast-follow (grounding-agent is the natural consumer to drive it).

## DEF-18 — record a config-provenance digest at run_start · OPEN (2026-08-17)

- **What:** close_run's provenance check falls back to the working tree (labeled
  `source: "working-tree"`) because run_start records no config digest; an edit between
  the run's read and the close is invisible. `executed_provenance=` is the closure.
- **Why:** run_start is seam-engine surface (W3-gated), not close-machinery's grant.
- **Provenance:** tm-la-close-machinery builder DC-1; residual stated in every payload.
- **Owed-to:** the seam owner at a later authorized touch / backlog.

## DEF-19 — a dedicated plan-item binding field for deferral entries · OPEN (2026-08-17)

- **What:** the close's deferral binding is prose-derived (heading + What fields); an entry
  whose What merely mentions a task id over-binds. A `Defers:` field in protocol/deferral.md
  would make it structural.
- **Why:** deferral.md is clause-pinned + fingerprinted — its own two-step, not a mid-loop edit.
- **Provenance:** tm-la-close-machinery builder DC-2 (the defect-2 fix narrowed the rule and
  pinned the residual direction by test).
- **Owed-to:** a deferral.md amendment at a later wave / backlog.

## DEF-20 — migrate_machine_local has no caller in the loop · OPEN (2026-08-17)

- **What:** kata_config.split_machine_local + kata_settings work and are tested, but nothing
  invokes the migration; bootstrap/preflight is the natural once-per-operator home.
- **Why:** kata-bootstrap/kata-preflight are outside close-machinery's grant.
- **Provenance:** tm-la-close-machinery builder DC-4.
- **Owed-to:** a coordinate-skill touch at a later authorized window / backlog.

## DEF-21 — repo-root ruff scope/version drift makes the root invocation useless as a gate · OPEN (2026-08-17)

- **What:** unpinned `uvx ruff` (0.16.3 at last observation) over the REPO ROOT reports ~71
  errors, all in `.planning/specs/ux-rework/templates/*.py` and `adapters/claude/*.py`;
  the CI gate runs tools-scoped (working-directory: tools) and is green. Builders keep
  rediscovering the discrepancy (W4 orchestrate, Loop A close-machinery judge).
- **Why:** the offending trees are un-owned by any frozen task; pinning ruff's version or
  scoping the root config is a tooling decision.
- **Provenance:** W4 orchestrate deferral 4 (not DEF-filed then — filed now); Loop-A
  close-machinery judge residual.
- **Owed-to:** planning-window backlog (tooling hygiene).

## DEF-22 — six prose sites still describe the pre-G26 archive-name shape · OPEN (2026-08-17)

- **What:** G26 made archive names run-private (`board.<stamp>.<run-token>.archive.md`) but
  `protocol/cursor.md:170`, `protocol/observability.md:126`, `kata-readiness:132`,
  `kata-orient:113`, and `kata_restore.py:1026,1169` still describe `board.<utc>.archive.md`.
  No consumer PARSES archive names (grep-verified at the fix), so nothing breaks — but it is
  the burn's own prose/code-divergence meta-defect family.
- **Why:** the six sites span W2/W4/W9-owned files outside the G26 grant; fixing them
  mid-strand would have been ownership drift, and cursor.md re-triggers the fingerprint
  two-step.
- **Provenance:** Loop-A FINAL EVAL residual R2.
- **Owed-to:** W9 guardian-relabel (owns observability.md) + a small authorized sweep for
  the rest; the cursor.md leg pairs with any next fingerprint two-step.

## DEF-23 — the X14 closure record is human-authored markdown; activation parses its table shape · OPEN (2026-08-17)

- **What:** `gate_preconditions.mutation_activation` derives per-platform state by parsing
  the committed evidence note's run/SHA tables (block-bound after the builder's own
  wrong-pairing bug). The parse is only as strong as the note's shape; a structured
  machine-emitted closure artifact (or probe) would make it a fold over machine fact.
- **Why:** the note's format predates the engine; changing it is an evidence-contract call.
- **Provenance:** tm-lb-gate-preconditions builder deferral 1; stated in-contract.
- **Owed-to:** the close/probe machinery at a later authorized touch / backlog.

## DEF-24 — gate_preconditions is not yet DEMANDED at the orchestrate/evaluate call sites · OPEN (2026-08-17)

- **What:** the engine + the gate_emit door exist and are exercised (refusal ⇒ exit 2, no
  RESULT), but kata-orchestrate/kata-evaluate contract text does not yet require the
  preconditions report at their gates — W4/W5-owned surfaces outside the Loop-B grants.
- **Why:** wiring them mid-loop would have been ownership drift.
- **Provenance:** tm-lb-gate-preconditions builder deferral 2; PD-2 label verified by its judge.
- **Owed-to:** Loop C/D adjacency (the hook wave touches kata-orchestrate context) or a
  dedicated follow-up; the honest label must not calcify.

## DEF-25 — final_gate checks fact-table PRESENCE, not schema · OPEN (2026-08-17)

- **What:** `final_gate` requires the attested fact table as a dict; now that
  grounding_gate's `kata.grounding.fact-table/v1` schema landed in the same loop, the check
  should validate shape (and treat `mutationAttestation: null` as a refusal — the grounding
  judge's parse-breadth recommendation joins here).
- **Why:** the two tasks built concurrently; neither could bind to the other's unmerged shape.
- **Provenance:** tm-lb-gate-preconditions builder deferral 3 + the grounding judge residual 1.
- **Owed-to:** a small follow-up on the integrated tree (both surfaces now exist).

## DEF-26 — a mutation-attestation record kind on the cursor · OPEN (2026-08-17)

- **What:** the R-M10 attestation is a caller-passed dict; recording it as a cursor fold
  (the tripwire corpus-hash pattern) would make it recorded fact rather than argument.
- **Why:** cursor record kinds are seam vocabulary — a deliberate addition, not a rider.
- **Provenance:** tm-lb-gate-preconditions builder deferral 4.
- **Owed-to:** seam-adjacent follow-up / backlog.

## DEF-27 — drop `v1-provisional` from truth_signals.ROW_SCHEMA · OPEN (2026-08-17)

- **What:** the consumer the marker awaited (grounding's fact table) landed and is a
  test-asserted strict superset; the producer-side constant rename is one line in
  truth_signals.py plus its schema-string tests.
- **Why:** truth_signals.py was a sibling task's grant during Loop B.
- **Provenance:** tm-lb-grounding-agent builder DC-2.
- **Owed-to:** any next authorized truth_signals touch (supersedes nothing in DEF-17, which
  stays open as amended: the B5 swap needs a public per-citation surface first).

## DEF-28 — a shared .snyk rationale for the CLI `_safe_path` python/PT LOW class · OPEN (2026-08-17)

- **What:** Snyk's taint engine does not credit the repo's hand-rolled `..`-component guard
  idiom, producing standing LOW findings on every CLI module using it (gate_emit
  un-suppressed today; grounding_gate + tripwire_check joined the class this burn). The
  honest options: one shared rationale entry covering the guard family (reason + expiry per
  the existing .snyk pattern), or a recorded decision to leave the class visible.
- **Why:** .snyk is a policy file outside every task grant; per-file entries would be
  inconsistent.
- **Provenance:** tm-lb-grounding-agent builder DC-3; corroborated by the corpora builder's
  scan (all-Low, same class).
- **Owed-to:** an operator security-policy call (surfaced on the veto ledger).

## DEF-29 — wire a live capture-edge probe so derive_capture can grade Verified (post-edge) · OPEN (2026-08-17)

- **What:** the capture edge is built and proven (both paths), but `run_start` grades capture
  from a `capture_edge_probe` the frozen W8 block never asked for, so it stays
  `Honor-system (engine-by-conductor)` at run start. The shape needed:
  `{"result": "probed", "captured": True}` from a real mint→claim→post-edge cycle.
- **Why:** inventing the probe was outside the frozen block (the builder's declared deviation 4).
- **Provenance:** tm-lc-hook-activation builder DC-2 + judge residual 2.
- **Owed-to:** a seam-adjacent follow-up / backlog.

## DEF-30 — the marker-loss / find_run_marker-OSError fail-open window · OPEN (2026-08-17)

- **What:** a run marker lost mid-run, or an OSError in `find_run_marker`, reads as non-kata
  ⇒ allow (RS-L5). The residual channel is the post-hoc cursor-lineage audit; the shadowing
  edge (an inner marker-less .kata hiding an outer live run) is in the same family.
- **Why:** fail-open here is the DESIGN's stated limit (a scope check cannot fail closed
  without denying every non-kata session on the host); closing it needs an ownership handle
  the hook deliberately does not take.
- **Provenance:** tm-lc-hook-activation stated residual (RS-L5) + the kata_scope shadowing note.
- **Owed-to:** the post-hoc lineage audit machinery / a DESIGN §11 boundary ruling.

## DEF-31 — the hook is a committed template, not installed; global-settings install is an operator Human Moment · OPEN (2026-08-17)

- **What:** `settings.snippet.json` carries the hook entries + install digest, but nothing
  installs them into an operator's live `~/.claude/settings.json` (which kata cannot guard,
  §11). Enforcement is proven-live-via-tripwire but install-gated; a real global-scope install
  + interactive-session confirmation are UNPROBED operator acts (probe Human Moments 1 & 3).
- **Why:** installing into the operator's global config is an outward act requiring explicit
  operator consent — never an autonomous conductor act.
- **Provenance:** tm-lc-hook-activation UNPROBED-scopes section + the honest post-activation
  posture note.
- **Owed-to:** operator Human Moment (surfaced on the veto/decision ledger in the post-loop report).
