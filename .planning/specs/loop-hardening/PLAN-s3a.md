---
date: 2026-06-21
spec: loop-hardening
sprint: S3a — grounding + research (the buildable half of S3)
status: FROZEN — partitions S3a into disjoint slices for an orchestrated foreground-parallel build
roadmapRef: ./ROADMAP.md · baseline: S2 green (b9d9af5)
closes: G5 (grounding gate / kata-research never fired) — the machine-readable, testable substrate
tags: [plan, loop-hardening, sprint-s3a, grounding, research, escalation, frozen]
note: S3b (the live loop-back, G6) is a SEPARATE operator-driven session — NOT in this plan.
---

# S3a — grounding + research substrate · frozen PLAN

`kata-research` + the grounding gate (`kata-evaluate` injected-knowledge mode) are fully documented but never
fired — there is **no machine-readable artifact or emitter** for the `research-needed` escalation, the research
findings, or the GROUND/REJECT/ESCALATE verdict (unlike `RESULT.json`/`mutation.json`). G5 closes the same way G3
did: add the testable artifacts + emitters, wire the two skills to them, so the mechanism is concrete, auditable,
and ready for the S3b loop-back to exercise live. Two disjoint slices, Sonnet workers in isolated worktrees →
integration gate → fresh-context `kata-evaluate`. **S3b (the live loop-back) is a separate operator-driven session.**

## LOCKED decisions (do NOT re-decide)
- **Escalation + findings are machine-readable, schema-pinned.** `tools/escalation.py` builds/validates the
  `protocol/escalation.md` payload and writes `.kata/escalations/<taskId>.json`; it also validates a research
  **finding** `{claim, source, confidence, groundsToPlan}` (the `kata-research` output shape). Required fields +
  enums are fail-closed (raise on missing/invalid). `..`-guard on `kata_dir` (CWE-23, mirror gate_emit).
- **The grounding verdict is derived deterministically + emitted.** `tools/grounding_gate.py` maps a finding to a
  verdict per the `kata-evaluate` injected-knowledge rules — **REJECT** if the source does not support the claim;
  **ESCALATE** if a LOCKED decision is in tension (`groundsToPlan == "NO"`) or it can't be grounded; **GROUND**
  only if source-supported AND no LOCKED conflict. It writes `.kata/grounding.json` `{verdicts, allGrounded}`.
  **Default-FAIL: nothing is GROUND until its source is asserted to support the claim** (the `source_supports`
  input is the human/gate judgment, never assumed True).
- **Skills are WIRED, not reimplemented.** `kata-research` keeps its no-write contract and now names the
  `tools/escalation.py` finding shape as its output schema. `kata-evaluate` injected-knowledge mode names
  `tools/grounding_gate.py` as the verdict emitter (the orchestrator runs it; the no-write skills never write).
  Neither skill imports the tools (prose reference); both stay structurally no-write.
- **Conditional, not required.** Research/grounding fires **only on a `research-needed` escalation** — it is NOT a
  per-run requirement (unlike S2's code-bearing mutation rule). When it fires, only GROUND findings may fold, via a
  deliberate superseding re-plan (audited). BC: absent any escalation ⇒ no artifacts, no behavior change.

## Wave DAG
```
Wave 1 (parallel):  S3a-1 escalation + finding emitter (+ kata-research wire) ──┐
                    S3a-2 grounding-gate verdict emitter (+ kata-evaluate wire) ─┘  (disjoint files)
Integration:        octopus-merge → uv sync → pytest + validator 35/0 + Snyk → gate_emit RESULT.json
                    → fresh-context kata-evaluate (PASS). Demonstrable: a real .kata/escalations/<id>.json +
                    .kata/grounding.json produced by the emitters (GROUND + REJECT + ESCALATE each shown).
```

## Task S3a-1 — escalation + research-finding emitter
**Owns (disjoint):** `tools/escalation.py` (NEW), `tools/tests/test_escalation.py` (NEW),
`skills/plan/kata-research/SKILL.md` (EDIT).
**read_first:** `protocol/escalation.md` (the payload schema — authoritative), `skills/plan/kata-research/SKILL.md`
(the findings output shape), `tools/gate_emit.py` (`_safe_path` `..`-guard pattern), this PLAN's LOCKED section.
**action:**
- **`tools/escalation.py`** — stdlib only:
  - `build_escalation(taskId, kind, decisionNeeded, optionsConsidered, agentRecommendation, rationale, *,
    lockedDecisionInTension=None, costOfWaiting=None, costOfProceeding=None, status="open", resolution=None) ->
    dict`: validate REQUIRED fields present + `kind` ∈ {orchestrator-resolvable, research-needed, human-required}
    + `status` ∈ {open, resolved}; `optionsConsidered` a non-empty list; raise `ValueError` (fail-closed) otherwise.
    Return the dict exactly per `protocol/escalation.md`.
  - `write_escalation(kata_dir, payload) -> str`: `..`-guard kata_dir; `mkdir -p <kata_dir>/escalations`; write
    `<kata_dir>/escalations/<taskId>.json` (utf-8, indent=2); return the path.
  - `build_finding(claim, source, confidence, grounds_to_plan) -> dict`: validate `source` non-empty (an ungrounded
    claim is not a finding ⇒ raise), `confidence` ∈ {HIGH, MED, LOW}, `grounds_to_plan` ∈ {YES, NO, PARTIAL};
    return `{claim, source, confidence, groundsToPlan}`.
- **`skills/plan/kata-research/SKILL.md`** (EDIT): in the Output section, name `tools/escalation.py`'s
  `build_finding` shape `{claim, source, confidence, groundsToPlan}` as the canonical finding schema the orchestrator
  persists, and note the `research-needed` escalation is written via `write_escalation` (`.kata/escalations/<id>.json`).
  Keep the skill **no-write** (it returns findings; the orchestrator writes). Frontmatter unchanged/valid.
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_escalation.py -q` (TDD red→green). Cover:
`build_escalation` returns a full valid payload; missing a required field ⇒ ValueError; bad `kind`/`status` ⇒
ValueError; empty `optionsConsidered` ⇒ ValueError; `write_escalation` writes `.kata/escalations/<taskId>.json`
round-tripping as JSON + creates the dir; `build_finding` validates source/confidence/grounds_to_plan (each bad
value raises; empty source raises); `..`-guard rejects traversal. Full suite + validator 35/0 stay green.
**acceptance:** a `research-needed` escalation + a finding can be built and persisted to `.kata/` schema-valid.
**threat model:** writes only under operator-supplied `kata_dir` (`..`-guard); pure builders otherwise. New Python ⇒ Snyk.

## Task S3a-2 — grounding-gate verdict emitter
**Owns (disjoint):** `tools/grounding_gate.py` (NEW), `tools/tests/test_grounding_gate.py` (NEW),
`skills/evaluate/kata-evaluate/SKILL.md` (EDIT).
**read_first:** `skills/evaluate/kata-evaluate/SKILL.md` (the **Injected-knowledge grounding mode** section — the
GROUND/REJECT/ESCALATE rules), `protocol/escalation.md`, `tools/gate_emit.py` (`_safe_path`), this PLAN's LOCKED.
**action:**
- **`tools/grounding_gate.py`** — stdlib only:
  - `grounding_verdict(finding, source_supports: bool, locked_conflict: bool) -> str`: per the gate rules —
    `locked_conflict or finding["groundsToPlan"] == "NO"` ⇒ `"ESCALATE"`; elif `not source_supports` ⇒ `"REJECT"`;
    else `"GROUND"`. (Default-FAIL: caller must assert `source_supports` from reading the source — never assumed.)
  - `build_verdict(finding, source_supports, locked_conflict, evidence) -> dict`: `{finding, verdict, evidence}`.
  - `write_grounding(kata_dir, verdicts: list[dict]) -> str`: `..`-guard; write `<kata_dir>/grounding.json`
    `{"verdicts": verdicts, "allGrounded": all(v["verdict"] == "GROUND" for v in verdicts)}`; return the path.
- **`skills/evaluate/kata-evaluate/SKILL.md`** (EDIT): in the **Injected-knowledge grounding mode** section, name
  `tools/grounding_gate.py` as the deterministic verdict emitter (the orchestrator runs it post-evaluation to
  persist `.kata/grounding.json`); align the prose verdict rules with `grounding_verdict`. Do NOT touch rubric item
  1 (S2). Keep frontmatter **no-write** (`allowed-tools: [Read, Grep, Glob, Bash]` — no Write/Edit). Valid frontmatter.
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_grounding_gate.py -q` (red→green). Cover: GROUND
(source_supports True, no conflict, groundsToPlan YES); REJECT (source_supports False); ESCALATE (locked_conflict
True) AND ESCALATE (groundsToPlan == "NO" even if source_supports True); `write_grounding` writes `grounding.json`
with correct `allGrounded` (True only if every verdict GROUND); `..`-guard rejects traversal. Full suite + validator 35/0 green.
**acceptance:** the three verdicts are derived correctly and `.kata/grounding.json` is emitted; `allGrounded` is
True only when every finding GROUND.
**threat model:** writes only under operator-supplied `kata_dir` (`..`-guard); pure derivation otherwise. New Python ⇒ Snyk.

## Integration + gate (the boundary artifact)
1. Octopus-merge `s3a/escalation` + `s3a/grounding` off master → `s3a/integration`. `cd tools && uv sync` (no new deps).
2. Full gate: `uv run pytest -q` (367 + new) · `uv run python validate_skills.py` (35/0 — SKILL edits, no new skills) ·
   `mcp__Snyk__snyk_code_scan` on the new Python (`..`-guards = the controls; CWE-23 on operator args = documented FP).
   Emit `.kata/RESULT.json` via `tools/gate_emit.py` (gate_name `s3a-integration`).
3. **Demonstrable (close G5 for real):** drive the emitters once — build a `research-needed` escalation +
   `write_escalation`; build three findings and produce a **GROUND**, a **REJECT**, and an **ESCALATE** verdict +
   `write_grounding` → show `.kata/escalations/<id>.json` + `.kata/grounding.json`. (Like S2's real `mutation.json`.)
4. **Fresh-context `kata-evaluate`** — SEPARATE no-write Sonnet subagent, 8-rubric, default-FAIL, **no self-cert (L8)**.
   Must return PASS.
5. Merge to master, push, checkpoint STATE/HANDOFF/ROADMAP, clean up worktrees+branches. Backout: tag `pre-s3a`.
   **Then S3b** — the live loop-back (G6), an operator-driven session (the human "run again" decision can't be simulated).

## Ownership disjointness
| File | Owner |
|---|---|
| `tools/escalation.py`, `tools/tests/test_escalation.py`, `skills/plan/kata-research/SKILL.md` | S3a-1 |
| `tools/grounding_gate.py`, `tools/tests/test_grounding_gate.py`, `skills/evaluate/kata-evaluate/SKILL.md` | S3a-2 |
| integration RESULT.json + demo artifacts, STATE/HANDOFF/ROADMAP checkpoint | Integrator |
No file in two lanes. ✓
