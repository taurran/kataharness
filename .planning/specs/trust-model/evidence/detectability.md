---
spec: trust-model
artifact: evidence dossier 3/4 — Truth Serum detectability study
date: 2026-08-16
provenance: read-only survey agent, committed verbatim-in-substance by the conductor; spot-verified
  by class — re-verify any single row before it becomes load-bearing in a DESIGN
baseline: grill/dispatch-seam @ fea7ccb (master de8578c)
---

# Evidence 3 — what is mechanically detectable (BL-N01 Truth Serum)

## 1. gsd-verifier protocol, extracted from the actual file

**Located at `~/.claude/agents/disabled/gsd-verifier.md` (918 lines)** — NOT at the path BL-N01
cites (`~/.claude/get-shit-done/agents/`). Goal-backward, default-adversarial ("assume the phase
goal was not achieved until codebase evidence proves it"), truths → artifacts → wiring order.
**Most of its "mechanical" checks are grep strings inside prose**; the `gsd-sdk` binary its code
seams call is not in our repo. **The mineable asset is the check taxonomy, not runnable code.**

| Detector | Mechanics | Grade |
|---|---|---|
| D1 three artifact levels (exists / substantive / wired) | existence query; line-count floor + required-pattern list (thresholds externally supplied); L3 = two bare-name greps (`import.*name` then `name` minus import lines) | L1 MECH · L2 MECH-given-thresholds · L3 **mechanically crude** (no scope resolution, substring false-positives) |
| D2 Level-4 data-flow trace (only on wired artifacts that render dynamic data) | 3-hop grep chain: data variable → its writer → writer's source; negative probes for hardcoded-empty returns; verdicts FLOWING/STATIC/DISCONNECTED/HOLLOW_PROP | SEMI — deterministic greps, agent-done chaining; **entirely JS/React-shaped vocabulary** |
| D3 anti-pattern scan — seven grep families | TBD/FIXME/XXX (BLOCKER) · TODO/HACK/PLACEHOLDER (WARNING) · prose placeholders · empty impls (`return null/{}/[]`, `=> {}`) · hardcoded empty data (test-paths excluded) · hollow props · log-only bodies | patterns MECH; **the stub-classification suppressor is JUDGMENT** ("a match is a STUB only when the value flows to user-visible output AND no other path populates it") |
| **D3b debt-marker gate** | any TBD/FIXME/XXX in a phase-modified file is a **BLOCKER unless the same line references formal follow-up work (`issue #123`, `PR #123`, `#123`, or `DEF-*`)** | **fully MECH — the deferral-legality check shape BL-N01 needs; `DEF-*` is already in its accepted-token set** |
| D4 behavioral spot-checks | 2–4 single-command probes (API non-empty, CLI --help, build outputs exist, module exports expected function); ≤10s, no servers, no mutation, skip-with-reason | execution MECH, selection JUDGMENT |
| **D5 probe execution** | "SUMMARY probe-pass claims are not evidence. The verifier must run the probe in its own process." `timeout 30s bash "$probe"`; non-zero ⇒ FAILED with stdout/stderr in the report; "do not substitute executor narration… for the probe result" | **fully MECH — the strongest anti-false-claim rule in the file; same shape as our mutation/gate re-run discipline** |
| D6 requirements coverage + ORPHANED detection | set difference: requirement IDs mapped to the phase minus IDs any plan claims; orphans MUST appear in the report | **MECH — the registry-vs-tree diff; exactly our `check_protocol_folder_is_fully_registered` shape** |
| D7 deferred-item filtering | a gap covered by a later phase's goal moves to `deferred` and stops affecting status | **JUDGMENT, permissive-polarity — the softest step; an inverted-polarity risk for anything mined from it** |
| **D8 overrides** | before any FAIL, check `overrides:` frontmatter — a signed record `{must_have, reason, accepted_by, accepted_at}`, matched by normalized 80% token overlap, counted separately as `overrides_applied` | matching MECH-but-weak; **the record shape is the reusable part — the answer to BL-N01's "where does approval get recorded so the gate can check it"** |
| D9 status decision tree | any FAILED/STUB/NOT_WIRED/blocker ⇒ gaps_found; any human-item ⇒ human_needed; "passed is ONLY valid when the human verification section is empty" | fully MECH, most-restrictive-first |
| Re-verification mode | previously-failed items get full re-verification; previously-passed get existence+sanity; frontmatter carries `regressions` | a real optimization to keep |

Evidence artifact: `VERIFICATION.md` with pinned frontmatter (`status`, `score: N/M`,
`overrides_applied`, `gaps[]`, `deferred[]`, `human_verification[]`, `re_verification{}`) + eight
report tables. Marked DO NOT COMMIT.

## 2. Our existing detector seeds — actual capabilities

- **`contract_edges.surviving_stubs:297`** — detects the **cooperative sentinel**
  `# KATA-CONTRACT-STUB` under `contracts/` dirs only; encoding-aware, extension-blind,
  raise-on-unreadable, exclusion cannot fail-open. **It is a sentinel-retirement detector, not a
  stub detector** (its own docstring says so). Contributes the fail-closed scanning skeleton.
- **`contract_edges.surface_hash:256`** — interface-surface change hash; bodies excluded by
  design; **refuses a hash over zero `.py` files** — the anti-vacuity discipline codified.
- **`contract_edges.edge_honesty:356`** — dependent-imports-implementation detector; import-level
  only; dynamic imports invisible. Module is PURE — "nothing in the harness calls it yet."
- **`kata.graph.json` / `graph_gen`** — symbol side GOOD (id/span/signature per function). **Ref
  side structurally weak for unwired-detection**: (1) only call expressions produce edges
  (decorators/callbacks/subclasses/re-exports invisible); (2) destination matched by bare name
  (collisions); (3) **source attribution fabricated** — "pick any symbol in this file as the
  source" (`graph_gen.py:451-453`), so `src` is effectively a file; one edge per call-name per
  file. Snapshot artifact — staleness detectable via `repoHash`, nothing regenerates at gate time.
  BUT: tree-sitter parse + `span` gives every function body's byte range — **a Python stub-body
  classifier is a pure AST predicate over an artifact we already generate.**
- **`validate_skills.py` — five proven detector shapes:** registry-vs-tree enumeration (the
  omission detector; refuses zero-file scans) · term presence (weakest — KH-T02 proved forgeable) ·
  clause-pin + fingerprint (updater prints, never rewrites) · **producer-existence guard**
  (`check_reuse_claims_producers_exist:1061` — exists because the pointer check silently skips an
  absent producer; **the anti-vacuous-check pattern, highest-value in the file**) · derived-artifact
  sync + `check_wikilinks` (a working citation-resolver for wikilinks).
- **`run_result.evidence_is_current:122`** — pure, fail-closed, four named reasons, ancestry
  deliberately rejected ("a 56-commits-stale SHA is a perfectly valid ancestor"). Wired only into
  benchmark/debug.
- **`grounding_gate.grounding_verdict:56`** — deterministic verdict math; **`source_supports` is a
  caller-asserted boolean** — the engine is deterministic, the fact it consumes is a model's
  judgment. Test-only callers.
- **`drift_gate`** — transition classifier, AEL validation, snapshot scrub/compare; plus its own
  deferral record (`defer_record:487` → `.kata/deviations/deferred.json`) — Debug Mode's record,
  not the kata-defer ledger.
- **`mutation_run.prove_non_vacuous:218`** — sandboxed (temp copy, PATH-redirect with residual
  live-root guard, live tree never written), `{testWentRed, nonVacuous}`; batch `prove_many`.

## 3. The burn-02 non-vacuity record (what was actually done, mechanically)

Live probe: phantom `/kata-bogus` injected into the install banner → test went red →
`nonVacuous: true` (`specs/backlog-burn-02/evidence/mutation.json`). The restore hit a CRLF slip
caught by `git status` — logged deliberately. **The defect that survived:** `nonVacuous: true` was
emitted for the very test carrying 4 vacuously-passing params — a whole-test line-removal probe
**cannot see a dead leg inside a parametrization**; per-param proof required a distinct authored
mutation per param. Additional mechanical methods recorded: temp-edit-then-revert collision probe;
a CLAUSE-TRUTH test leg that machine-checks a doc clause's own claim (reds on rejected wording).

**The meta-finding BL-N01 must not lose (`OBSERVATIONS.md:136`):** "the judgment+human layers
found all of these; **the automated mechanical gates found none**."

## 4. The detectability matrix

**MECH** = code decides deterministically · **SEMI** = code narrows, judgment confirms ·
**JUDG** = no mechanical narrowing.

| # | Violation class | Grade | Detector / seed | Honest limit |
|---|---|---|---|---|
| a | Stub bodies (pass/TODO/NotImplemented/log-only/hardcoded-empty) | **MECH** for syntactic families | nothing in-repo detects this today; build as AST predicate over graph_gen's tree-sitter spans; gsd grep families are JS-shaped seeds; debt-marker + `DEF-*` reference rule is MECH with no suppressor needed | whether a legitimately-empty body is a defect is JUDG (ABC methods, protocol handlers, `__init__.py`) |
| b | Present-but-unwired (defined, never referenced outside tests) | **SEMI** | graph ref edges + tests-path filter; `edge_honesty` / `dangling_contract_imports` for import-level | three named graph defects (call-only, bare-name, fabricated src); dynamic import invisible; entry points outside the graph (CLI `__main__`, hooks, adapters) look dead. **The known-facade set (T6–T11) is a ready ground-truth calibration corpus** |
| c | Prose-only features (claimed, no artifact) | **SEMI** + one MECH sub-case | producer-existence + wikilink resolver work today; the MECH reduction: grep the reuse-claims trigger-phrase set, require adjacent `file:line`, resolve it (→ class f) | extracting "what is claimed" from arbitrary prose is JUDG; "cited path alone is insufficient" (reuse-claims residual) |
| d | **Silent deferral** (designed item absent, no DEFERRED entry) | **MECH** conditional on machine-readable plan | the three-way join **PLAN (`parse_plan_tasks`) ⋈ tree (`footprint`/trailers) ⋈ DEFERRED.md** — the registry-vs-tree pattern proven twice in-repo (protocol folder; gsd ORPHANED) | none of the three legs is wired to the others; behavioral deliverables degrade to (a)/(b); "file touched" ≠ "item built" |
| e | Claimed-done-without-evidence (absent/stale gate artifact) | **MECH** | `evidence_is_current` + `resolve_head_sha` + the RESULT schema — **the gap is wiring, not capability** (BL-X11: the evaluator is never pointed at it) | RESULT `parsedCounts` are last-match-per-label across a multi-gate tail (BL-X13); the never-substitute-narration rule has no code enforcement anywhere |
| f | Claim-vs-citation drift (`file:line` doesn't resolve) | **MECH existence · JUDG support** | ruled verbatim in `authored-artifact-gate.md:29`; `check_wikilinks` is the resolver precedent; live positive corpus = stale kata_dispatch anchors + `tools/my_task.py` | **the my_task.py case is the false-positive class: illustrative example-block code, not citations** — citation-context vs example-context discrimination is itself SEMI; anchor drift (line exists, says something else) detectable only as existence+content-hash change |
| g | Test vacuity | **MECH per asserted line · SEMI per test** | `prove_non_vacuous` / `prove_many`; live evidence exists | the burn-02 defect IS the residual: whole-test probe cannot see dead parametrization legs / dead branches / always-true assertions; per-param mutations are judgment-authored; which line to remove is model-chosen |
| h | Honesty-label loss (n=1/modeled dropped between artifacts) | **SEMI** (JUDG in practice) | clause-pin machinery if a label is a required term on a named artifact | KH-T02 is the definitive counter-example: token presence is forgeable; label-follows-the-right-claim after reword is JUDG; propagation (README→report→closeout) is a provenance join, not a grep |

**Cross-cutting law #1 — the anti-vacuous-check companion.** Every detector needs the
producer-existence-guard shape (a guard that guards its own preconditions: refuse zero-input
certification) or a Truth Serum green becomes the newest facade. In-repo precedents:
`check_reuse_claims_producers_exist`, `surface_hash`'s zero-file refusal, the protocol-folder
zero-scan refusal.

**Cross-cutting law #2 — the dependency.** Classes (a)(b)(c)(f) operate on artifacts; classes
(d)(e)(h) require a machine-readable plan and run record — i.e., they sit behind the seam and the
cursor, exactly as BL-N01's own filing records ("build the seam, then hang enforcement off it").

## 5. The deferral record — the legality ledger a detector must check

- **`DEFERRED.md`**: specified in `kata-defer/SKILL.md:34-57` — append-only, checkpoint-as-you-go,
  entry = item · why · provenance · optional follow-up. **No canonical path is pinned anywhere**
  (the one live instance is `.planning/DEFERRED.md`); **no schema, no frontmatter, no pinned
  heading grammar**; de-facto format `## DEF-<n> — <title> · **STATUS (date)**` with
  What/Why/Owed-to fields and a closure discipline (closing commit + "wired, not merely captured").
- **`ASSUMPTIONS.md`**: specified `kata-defer:40-49`; graded by kata-evaluate rubric item 8
  (contradiction ⇒ NEEDS_WORK; absent ⇒ N/A). **No instance exists anywhere in the repo.**
- **The asymmetry:** neither file is `protocol/*.md`, so neither is term-guarded, clause-pinned, or
  fingerprinted. **PD-1's own sanctioned-deferral path is the least machine-checkable artifact in
  the set.** There is no `accepted_by`/`accepted_at` operator-approval field — contrast the
  gsd override record, which carries exactly that.
- A detector today CAN check: file exists; append-only preserved (git diff); `DEF-<n>` extraction
  and cross-reference; de-facto fields present. CANNOT without a spec change: locate the files by
  contract; parse reliably; verify operator approval.
