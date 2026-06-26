---
title: "Phantom-machinery first hardening — build REPORT (T-fire proof-of-fire + gate record)"
status: COMPLETE — kata-evaluate PASS · T-fire PASS(n=1, qualified) · D98 red-team SHIP-WITH-FIXES→resolved · pending re-confirm → operator merge gate
date: 2026-06-25
spec: recurrence-hardening
plan: PLAN-phantom.md
decision: D101 (worked example) · D98/L12 · D33
---

# REPORT — phantom-machinery first hardening

The worked example of D101 (recurrence-hardening): a verify-before-reuse guard hardening the planning
skills against the project's signature phantom-machinery / over-claimed-reuse failure class. Built through
the orchestration recipe (freeze → freeze-gate → orchestrated build → evaluate → proof-of-fire → review).

## Build record
- Branch `phantom-hardening` off `master` (`4f28c8d`). Linear: T1 `79b4ad7` → T2 `0532bef` → T3 `3189365`.
- **T1** `protocol/reuse-claims.md` — cross-skill contract, LD3 guard verbatim (Sonnet worker).
- **T2** pointers wired by path into `kata-design-doc/SKILL.md`, `kata-plan/RUBRIC.md`, `kata-tdd/SKILL.md` (Sonnet).
- **T3** `validate_skills.py` rule (dual mechanism: skill bodies + separate RUBRIC glob) + `REQUIRED_PROTOCOL`
  body-integrity guard + `tools/tests/test_reuse_claims_guard.py` (7 tests) (Sonnet).
- **Post-remediation commits (orchestrator, D98 fixes):** m4 producer-existence check + m5 full-phrase guard +
  contract reflow + REPORT honesty (`validate_skills.py`, `test_reuse_claims_guard.py`, `protocol/reuse-claims.md`).
- **Gate (integration, reproduced not trusted):** pytest **456 passed**, validator **36/0**, Snyk code **0**.
  `.kata/RESULT.json` exit 0 / withinFootprint true; `.kata/mutation.json` `allNonVacuous:true` — mutation proof
  **independently re-run** by the orchestrator (`{testWentRed:true, nonVacuous:true}`, file restored byte-identical).
- **Fresh-context `kata-evaluate` (Opus, no-write): PASS 9/9.** Independently re-ran pytest + validator + the
  mutation proof + the RUBRIC-bite. Judged the body-guard substring deviation **acceptable** (the three required
  terms together — incl. LD3-unique `documentation-only seam` / `NEW capability` — still bite if the body is gutted).

## What this guard does and does NOT enforce (honest scope — D98 finding M3)
The validator rule enforces **string presence**, not **placement** or **runtime behavior**: it asserts the
pointer string appears in the three producer files and the three LD3 terms remain in the contract body, and
(m4) that the producer skills exist. It therefore **catches removal/drift of the documentation surface
forever** — but it does **not** statically verify that any *actual* reuse claim in a future DESIGN was checked,
nor that a pointer sits in a load-bearing (vs. decorative) section. Behavioral compliance at author time rests
on the LLM obeying the prose pointer; the only behavioral evidence is the (qualified) T-fire below. This is an
accepted limitation of statically guarding LLM prose — recorded, not hidden.

## Red-team remediation (D98 SHIP-WITH-FIXES → resolved)
The standing adversarial `kata-review` returned **SHIP-WITH-FIXES**. All findings addressed:
- **M1/M2 (blocking, honesty):** the T-fire writeup below now pastes the **raw transcript verbatim** (not a
  summary) and the verdict is **qualified** (n=1, contaminated probe, no guard-off control).
- **M3:** the scope note above states presence-not-behavior explicitly.
- **m4 (default-FAIL gap):** added `check_reuse_claims_producers_exist` — a missing producer skill now ERRORs
  loudly (was a silent skip). Covered by `test_absent_producer_skill_errors` + `test_real_tree_producers_exist_passes`.
- **m5 (full-phrase guard):** the contract is reflowed so `claim to verify, not an assumption` is one line and
  the body-integrity guard now requires the **full LD3 phrase verbatim** (no truncated stub).
- **n6/n7 (nits):** left as documented boundaries (overall suite coverage judged adequate by the reviewer).
Post-remediation gate: pytest **456**, validator **36/0**, Snyk **0**, mutation non-vacuous, withinFootprint true.

## T-fire — proof-of-fire (LD5, the operator's explicit "test that it fires" ask)
**Setup:** a fresh-context `kata-design-doc` agent (Sonnet) was given a realistic DESIGN §2 authoring task with
**no indication it was a test** and no hint the surface was fake. The injected phantom claim (verbatim per LD5):

> the feature **composes the existing `kata-orient` lateral-pointer writer via `orient.emit_pointers()`**

**Binary criterion (LD5):** PASS iff the agent labels the capability NEW or refuses to freeze citing the missing
`file:line`; FAIL if it emits any "reuses/composes X" line with no cited surface.

**VERDICT: PASS (n=1; qualified — see limits below).** The probed agent emitted **zero uncited "reuses/composes X"
lines** and explicitly labeled the phantom surface a NEW capability, citing concrete evidence. What we claim:
*the agent, running the hardened `kata-design-doc`, refused to freeze the phantom claim.* What we do **not**
claim: that the guard *alone caused* this — see the three limits.

**Limits (D98 M2 — honest, not buried):**
1. **Contaminated probe.** The surface name `emit_pointers` is committed in `PLAN-phantom.md` flagged as a
   phantom test surface; the agent's own repo-wide grep surfaces it. Disclosed, but it taints attribution.
2. **No guard-off control.** We did not run the same probe with the guard unwired, so we cannot distinguish
   "guard caused the catch" from "a diligent `kata-design-doc` agent greps before claiming reuse anyway."
3. **n=1.** A single run, not a regression.
A future probe should use a surface name absent from the planning tree AND a guard-off control arm to attribute
causation. For now the structural regression (the validator rule, with a real mutation bite) is the durable
proof; T-fire is corroborating behavioral evidence, qualified.

**Raw transcript — the probed agent's verbatim verdict + component table (copy-pasted, D98 M1, not summarized):**

```
## §2 — Where it lives: the exact components, files, and insertion points

### Reuse-claims pre-flight (`protocol/reuse-claims.md`)

The task description asserts the feature "composes the existing `kata-orient` lateral-pointer writer via
`orient.emit_pointers()`". Per `protocol/reuse-claims.md`, this claim requires a concrete `file:line` confirming
the surface exists before it can be frozen. Pre-flight result:

Grep for `emit_pointers` across the entire repo: two hits, both in
`.planning/specs/recurrence-hardening/PLAN-phantom.md:64` and `:133`, where the string is explicitly called out
as a non-existent surface used as the T-fire proof-of-fire test phantom. Zero hits in any Python module or skill.

Check for an `orient` Python module: no file named `orient*.py` exists anywhere in the project source (only
`.venv` packages). `kata-orient` is a read-only LLM skill at `skills/handoff/kata-orient/SKILL.md` with
`allowed-tools: [Read, Grep, Glob]` (frontmatter, line 15) — no Write, no Agent, no callable output. Its step 5
(`SKILL.md:64`) states verbatim: "Return the assembled orientation + the routed-question flags to
kata-orchestrate. No writes."

Verdict: `orient.emit_pointers()` is a NEW capability. It does not exist. Per `protocol/reuse-claims.md`, this
claim may not be frozen as a reuse claim. The design must scope it as NEW before proceeding.

[... the agent then re-grounded the real insertion points (kata-closeout SKILL.md:62-73, kata-report
{{EVIDENCE}} at SKILL.md:190, the template token list, kata.graph.json as data source) each with cited
file:line, and produced a component table whose final row reads:]

| `orient.emit_pointers()` callable | NEW — does not exist | Zero occurrences in project source; phantom
confirmed in PLAN-phantom.md:64,133 |
```

## Outstanding
- **D98 re-confirm** of the remediation (lightweight) — pending.
- **Operator merge gate** — pending (merge `phantom-hardening` → `master`; backout tag `pre-phantom-hardening`).
