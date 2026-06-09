---
date: 2026-06-08
spec: modes-A3-bootstrap-wiring
reviewer: fresh-context adversarial (kata-review advanced, D15) — Opus, read-only
verdict: SHIP
gate: pytest 12 passed · validator 24 skills / 0 errors
tags: [review, A3, modes, ship]
---

# A3 (bootstrap + wiring) — Adversarial Review (D15)

**VERDICT: SHIP.** Fresh-context, read-only adversarial pass over `git diff master...phase-2/modes-A3-bootstrap`
(6 build commits). Judged against the frozen contract (PLAN.md + GRILL-LEDGER GB1–GB13), STANDARDS §1/§3, and
the locked decisions D24c/D25/D26/GB12/D33. No blockers found on any of the five stress axes.

## Gate
- `uv run pytest -q` → **12 passed**
- `uv run python validate_skills.py` → **24 skills checked — 0 error(s), 0 warning(s)**, exit 0

## Stress-axis confirmations
1. **Load-guard fail-closed (GB12) — HOLDS.** `kata-orchestrate` precondition #0 draws the absent⇒Standard vs
   present-but-broken⇒STOP line unambiguously; the enumerated broken cases (malformed JSON, non-existent
   mode/effort, a `tiers[family]` with no skill, a module with no provider) all route to STOP/escalate. No
   wording permits a silent default over a *present* config. CONTEXT Load-guard glossary restates the split.
2. **Structural invariants (D33) — HOLDS.** Bootstrap "writes by construction, does not re-validate" opens no
   gap: the stale/hand-edited re-entrant-config risk is exactly what the orchestrate load-guard closes on read;
   both skills cross-reference the division of labor. No-self-certification / no-drift / default-FAIL /
   DRY-by-pointer all intact.
3. **No dependence on unbuilt A4 — HOLDS.** `kata-graph` appears only in plain prose (bootstrap SKILL +
   run-shapes.md table cell), never as `[[kata-graph]]` (validator's `check_wikilinks` = 0 errors). Version-up
   is honestly flagged "configurable now, executable in A4" in three places — valid config, not silently broken.
4. **Config schema coherence — HOLDS.** `runShape`/`target` defined identically across `protocol/config.md`,
   `run-shapes.md`, and the orchestrate consumer. Provenance-only contract holds end to end (orchestrate
   dispatches off mode/modules/tiers, not runShape). `target.baselineGate` producer (bootstrap) / consumer
   (orchestrate precondition #2) matched. No orphan fields.
5. **Frontmatter / STANDARDS §1 — HOLDS.** Both new skills: valid `kata-<verb>` names, all required keys,
   `kata/coordinate`+`kata/spine` tags, versions held at `0.1.0` (orchestrate not bumped — policy A).
   `kata-readiness` correctly omits Write (read-only, cost 1); `kata-bootstrap` legitimately has
   Write+AskUserQuestion (cost 2). Least-privilege respected. Registration consistent across README /
   SKILL-COST-RATINGS / TAXONOMY / DESIGN spine roster / D34–D46.

## Secondary observations (non-blocking — deferred, not fixed in A3)
1. **`tiers` key format not machine-enforced.** Docs consistently key `tiers` by family alias (`kata-grill`),
   but nothing validates bare-verb vs family-name. Low risk (prose is consistent). Closed by the
   already-backlogged `tools/` example-`kata.config` check (GB12). → tracked in BACKLOG.
2. **`kata-diagnose` in orchestrate's bare-family resolution mention** is forward-looking — orchestrate holds
   no live `[[kata-diagnose]]` dispatch in A3. Harmless generic rule statement.
3. **`kata-readiness` Scope 1 couples to the harness self-host layout** (`tools/` validator green). When the
   harness runs *on a target repo* (version-up, A4), "validator green" means the harness install, not the
   target. The two-scope split already separates harness-health from target-readiness; sharpen the wording in
   A4. → A4 note.

## Outcome
SHIP. A3 merges to `master`. Secondaries (1) and (3) carried to A4/backlog; none gate this merge.
