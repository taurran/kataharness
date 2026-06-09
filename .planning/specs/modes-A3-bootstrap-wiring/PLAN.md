# Modes Spec A3 — Bootstrap + Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make the A2 tier families actually *dispatch* — build `kata-bootstrap` (the run-shape router +
composition ladder that writes `kata.config`), `kata-readiness` (the bootstrap-invoked health/target check),
and wire `kata-orchestrate` to read `kata.config`, resolve `[[kata-<verb>]]` family→tier, and fail closed on a
bad config. Bootstrap is version-up-aware from day one (writes a correct version-up config that A4 will execute).

**Architecture:** Two new single skills in `skills/coordinate/` (`kata-bootstrap`, `kata-readiness`) + a prose
wiring change to `skills/coordinate/kata-orchestrate/SKILL.md` + a `kata.config` schema extension
(`runShape`, `target`) in `protocol/config.md` enforced by the validator. Run-shapes are **presets** (data) over
the frozen mode axis (GB1), not a new axis. The version-up *execution* bundle (`kata-graph` + context-aware
planning/regression) is **A4, out of scope here** — A3 only makes version-up *selectable + correctly configured*.

**Tech Stack:** Markdown skills (schema-v2 frontmatter, STANDARDS §1); the `tools/` Python/uv validator
(extended `REQUIRED_PROTOCOL`); pytest. No runtime code — skills are prose contracts; machine-checkable parts
(config schema terms, new-skill frontmatter, README sync) are validator/pytest-gated, prose is gated by the
final adversarial `kata-review` (D15).

**Decisions this plan implements (LOCKED — quote, don't paraphrase):** GB1 (run-shapes = presets on the mode
axis), GB5 (A3/A4 cut; same orchestrator D24d; bootstrap re-entrant — one skill), GB11 (`kata-readiness` is a
separate light skill *invoked by* bootstrap), GB12 (config validation = **fail-closed load-guard in
`kata-orchestrate`, NOT a bootstrap phase**), GB13 (interview surfaces **only run-shape-relevant** fields).
D24c (composition ladder: default→go / add modules / cross-tier pick / external ingest), D25 (absent config ⇒
Standard), D26 (`tiers[family]` → `kata-<family>-<tier>`).

**Versioning (STANDARDS §3 pre-release hold, policy A, 2026-06-08):** new skills enter at `0.1.0`;
`kata-orchestrate` is modified but **NOT bumped** (held at `0.1.0`). Do not bump any `version` in this plan.

**Scope guards:** A3 does NOT build `kata-graph`, the version-up execution DAG, `kata-understand`, or
`kata-defer` (all A4/backlog). A3 does NOT bump skill versions. Bootstrap MUST reference `kata-graph` only in
**plain prose, never as `[[kata-graph]]`** — that skill does not exist yet and `check_wikilinks` fails on
dangling links.

---

## File Structure

| Path | Responsibility |
|---|---|
| `protocol/config.md` (modify) | add `runShape` + `target` fields to the schema table |
| `tools/validate_skills.py` (modify) | add `"runShape"`, `"target"` to `REQUIRED_PROTOCOL["config.md"]` |
| `tools/tests/test_validate_skills.py` (modify) | test: the two new terms are required + the real `config.md` documents them |
| `skills/coordinate/kata-readiness/SKILL.md` (create) | light health/target/re-entrant readiness check; no Write |
| `skills/coordinate/kata-bootstrap/SKILL.md` (create) | run-shape router + ladder + interview + readiness call + cost preview + write config |
| `skills/coordinate/kata-bootstrap/resources/run-shapes.md` (create) | the preset table (data): run-shape → mode + modules + target defaults |
| `skills/coordinate/kata-orchestrate/SKILL.md` (modify) | read `kata.config`; resolve family→tier; fail-closed load-guard; Standard fallback |
| `.planning/SKILL-COST-RATINGS.md` (modify) | add rows: `kata-bootstrap` = 2, `kata-readiness` = 1 |
| `README.md` (regenerate + hand-author Use cells) | index now lists 24 skills |
| `docs/TAXONOMY.md` (touch-up) | note bootstrap/readiness are spine; run-shape preset concept |
| `docs/DESIGN.md` (modify) | add `kata-bootstrap`, `kata-readiness` to the COORDINATE spine roster |
| `docs/MODES-DESIGN.md` (modify) | mark D24b/c implemented; note A3/A4 cut |
| `CONTEXT.md` (modify) | glossary: Run-shape, Preset, Readiness, Load-guard, `target` |
| `.planning/DECISIONS.md` (modify) | promote GB1–GB13 → D34–D46 |
| `.planning/specs/modes-A3-bootstrap-wiring/REVIEW.md` (create, T7) | adversarial review verdict |

**Cost-weights** (authority `.planning/SKILL-COST-RATINGS.md`): `kata-bootstrap` **2** (guided single pass,
no spawn/loop, invokes readiness), `kata-readiness` **1** (light checks, no amplification).

### `kata.config` schema additions (T1 — the exact fields)
```
| `runShape` | `"individual" \| "batch" \| "version-up" \| "advanced"` | The preset chosen at bootstrap (GB1) — provenance; presets pre-fill `mode`+`modules`. |
| `target`   | `{ kind: "greenfield" \| "existing", path?: string, baselineGate?: string }` | `greenfield` (default) or `existing` (version-up): `path` = existing repo, `baselineGate` = the command that must be green before + after (the regression baseline). |
```

---

## Task 1: Extend `kata.config` schema for run-shapes + version-up target

**Files:**
- Modify: `protocol/config.md`
- Modify: `tools/validate_skills.py:234-237` (the `REQUIRED_PROTOCOL` dict)
- Test: `tools/tests/test_validate_skills.py`

- [ ] **Step 1: Write the failing test**

Add to `tools/tests/test_validate_skills.py`:

```python
def test_config_schema_requires_runshape_and_target():
    from validate_skills import REQUIRED_PROTOCOL, check_protocol_schemas
    required = REQUIRED_PROTOCOL["config.md"]
    assert "runShape" in required and "target" in required
    # the real protocol/config.md must document them; check_protocol_schemas ignores its arg,
    # so pass []. Match on the stringified finding to avoid assuming the Finding field name.
    findings = check_protocol_schemas([])
    assert not any("config.md" in str(f) for f in findings), [str(f) for f in findings]
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd tools && uv run pytest tests/test_validate_skills.py::test_config_schema_requires_runshape_and_target -v`
Expected: FAIL — `"runShape" in required` is False (term not yet added).

- [ ] **Step 3: Add the two terms to `REQUIRED_PROTOCOL`**

In `tools/validate_skills.py`, change the `config.md` entry:

```python
REQUIRED_PROTOCOL = {
    "config.md": ["mode", "modules", "effort", "tiers", "preflight", "bakeoff", "skillVersions",
                  "runShape", "target"],
    "dependencies.md": ["classification", "scope", "verify", "install"],
}
```

- [ ] **Step 4: Document the two fields in `protocol/config.md`**

In the Schema table (after the `skillVersions` row), add the two rows from the "schema additions" block above.
Then add a short note under `## Notes`:

```
- `runShape` is provenance only: the bootstrap preset (GB1) pre-fills `mode`+`modules`; orchestrate dispatches
  off `mode`/`modules`/`tiers`, not off `runShape`. `target.kind: "existing"` (version-up) supplies the
  `baselineGate` that `kata-orchestrate` precondition #2 records as the regression baseline. The version-up
  *execution* path (kata-graph ingestion) is Spec A4; A3 only writes/validates the config.
```

- [ ] **Step 5: Run the test + full gate to verify green**

Run: `cd tools && uv run pytest -q` → Expected: all pass (incl. the new test).
Run: `cd tools && uv run python validate_skills.py` → Expected: `22 skills checked — 0 error(s)`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add protocol/config.md tools/validate_skills.py tools/tests/test_validate_skills.py
git commit -m "feat(A3): kata.config schema — runShape + target (version-up), validator-enforced"
```

---

## Task 2: Author `kata-readiness` (light health/target check)

**Files:**
- Create: `skills/coordinate/kata-readiness/SKILL.md`

- [ ] **Step 1: Write the frontmatter + body**

```markdown
---
name: kata-readiness
description: >-
  Fast pre-run readiness check: is the kata harness healthy (validator green, skills present, required tools
  on PATH) and is the target ready (git repo + clean tree, AGENTS/CONTEXT present, deps installable, an
  existing kata.config = re-entrant run)? Invoke from kata-bootstrap before composing a run, or standalone as
  an "is my kata environment ready?" doctor.
license: Apache-2.0
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Bash]
source: >-
  new (KataHarness original); pattern echoes environment "doctor" checks (e.g. brew/flutter doctor) — abstract,
  no external code adapted
tags:
  - kata/coordinate
  - kata/spine
  - readiness
  - preflight
---
# kata-readiness — is the harness + target ready to run?

A **read-only** check (no Write — it returns a verdict to its caller, it does not author artifacts). Two scopes,
each a checklist; report PASS / WARN / BLOCK per item and an overall verdict.

## Scope 1 — harness health
- Skills tree present and the validator is green (`tools/` → `uv run python validate_skills.py`, exit 0).
- Required host tools on PATH for the chosen run (e.g. `git`, the test runner, `uv`/language toolchain).
- A subagent-capable host is available (orchestrate's dispatch binding).

## Scope 2 — target readiness
- Inside a git repo with a **clean working tree** (uncommitted churn ⇒ WARN — execution wants a clean fork).
- `AGENTS.md` (and `CONTEXT.md` if the run plans against one) present, or flag that grill must create them.
- Declared dependencies are installable from an allowed registry (defers the actual install to pre-flight, D29).
- **Re-entrant detection:** if a `kata.config` already exists at the branch root, report it (its `mode`,
  `runShape`, `modules`) so bootstrap offers "same as last / step up / change shape" rather than cold-start.

## Verdict
Return a compact structured verdict (overall PASS/WARN/BLOCK + the per-item findings + the re-entrant
`kata.config` summary if any). **BLOCK** = a hard stop bootstrap must resolve before composing a run; **WARN**
= surface to the user but allow proceed. The check never installs, never writes, never mutates the repo.
```

- [ ] **Step 2: Verify frontmatter conformance**

Run: `cd tools && uv run python validate_skills.py` → Expected: now `23 skills checked — 0 error(s)`, exit 0.
(Confirms name/regex, required keys, `kata/coordinate`+`kata/spine` tags, no dangling wikilinks, cost-weight 1.)

- [ ] **Step 3: Commit**

```bash
git add skills/coordinate/kata-readiness/SKILL.md
git commit -m "feat(A3): kata-readiness — light harness+target readiness check (GB11)"
```

---

## Task 3: Author `kata-bootstrap` (run-shape router + composition ladder)

**Files:**
- Create: `skills/coordinate/kata-bootstrap/SKILL.md`
- Create: `skills/coordinate/kata-bootstrap/resources/run-shapes.md`

**read_first:** `protocol/config.md` (the schema it writes), `skills/coordinate/kata-readiness/SKILL.md`
(invoked in step 1), `docs/MODES-DESIGN.md` D24c ladder, `.planning/SKILL-COST-RATINGS.md` (cost preview source).

- [ ] **Step 1: Write the preset table resource**

`skills/coordinate/kata-bootstrap/resources/run-shapes.md` — the **data** that makes run-shapes presets (GB1):

```markdown
# Run-shape presets (data — bootstrap pre-fills these, the user may then drill down)

| runShape | mode default | modules (default) | target.kind | notes |
|---|---|---|---|---|
| individual | standard | [] | greenfield | the D24c default→go floor; one one-shot |
| batch | standard | [bakeoff] | greenfield | best-of-N (Spec B); asks `bakeoff.n` |
| version-up | standard | [graph] | existing | feature-add to an existing repo; asks `target.path` + `baselineGate`. **Execution = A4** (kata-graph not built yet — bootstrap writes the config, flags execution as A4-pending) |
| advanced | advanced | [] | greenfield | top of the ladder; surfaces cross-tier picks + external ingest |

A preset only pre-fills capability that exists. `batch` (Spec B) and `version-up` (Spec A4) are
**configurable now, executable later** — readiness reports them as not-yet-wired; bootstrap still writes a
valid config so they light up when B/A4 land. (GB5)
```

- [ ] **Step 2: Write the skill**

```markdown
---
name: kata-bootstrap
description: >-
  Pre-loop configurator and on-ramp: evaluate readiness (via kata-readiness), route by run-shape
  (individual / batch / version-up / advanced — presets over the mode axis), compose mode+modules+tiers via
  the ladder, preview cost, then write kata.config and launch the loop. Re-entrant — reads an existing config
  to reconfigure. Invoke to start or reconfigure any kata run.
license: Apache-2.0
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Write, AskUserQuestion]
source: >-
  adapted-from GSD discuss-phase Q&A model + docs/MODES-DESIGN.md D24c composition ladder (KataHarness design)
tags:
  - kata/coordinate
  - kata/spine
  - bootstrap
  - composition-ladder
---
# kata-bootstrap — compose a run, write kata.config, launch

The on-ramp. Turns a one-keystroke "default → go" into an expressive composition ladder, then writes the
frozen `kata.config` ([[protocol]]: `protocol/config.md`) that [[kata-orchestrate]] dispatches off. Interaction
uses **structured choice-or-text questions** (offer 2–4 options, recommendation first, always a free-text
escape) — *(adapter binding: Claude → `AskUserQuestion`; a plain CLI → numbered options + a free-text prompt)*.

## Phase 0 — readiness (always)
Invoke [[kata-readiness]]. On **BLOCK**, stop and surface the blocker (don't compose a run on a broken env). On
re-entrant detection (an existing `kata.config`), offer **same-as-last / step a family up a tier / change
run-shape** instead of cold-start. WARNs are surfaced, not blocking.

## Phase 1 — run-shape (the router, GB1)
Ask the run-shape: **individual / batch / version-up / advanced**. Each is a **preset** (see
`resources/run-shapes.md`) that pre-fills `mode` + `modules` + `target` — not a new axis. `batch` (Spec B) and
`version-up` (Spec A4) are configurable now but flagged **execution-pending** by readiness; bootstrap still
writes a valid config. For **version-up**, additionally collect `target.path` (the existing repo) and
`target.baselineGate` (the command that must be green before *and* after — the regression baseline). Describe
the version-up ingestion engine (kata-graph) in prose only; do **not** wikilink it (A4, unbuilt).

## Phase 2 — the composition ladder (D24c), interview = run-shape-relevant only (GB13)
1. **default → go** — accept the preset's recommended mode and launch. The floor is never punishing.
2. **add modules** — à-la-carte beyond the preset bundle (D20).
3. **cross-tier pick** — override a single family's tier (`tiers[family]`) without changing `mode`
   (e.g. pull `kata-grill-advanced` into a Standard run for one cycle).
4. **external/custom ingest** — name a skill + declare its slot (`needs`/`produces`/`slot`) → `ingested[]`.
Surface ONLY the `kata.config` fields the chosen run-shape needs (progressive disclosure) — the default→go path
stays one keystroke; advanced fields appear only when the path opens them.

## Phase 3 — cost preview
Sum the `cost-weight` of every skill the composed run will invoke (authority:
`.planning/SKILL-COST-RATINGS.md` / each skill's frontmatter). Show the total + the per-skill breakdown before
committing, so the user prices the run.

## Phase 4 — write kata.config + launch
Write `kata.config` (JSON, branch root) per `protocol/config.md`: `mode`, `modules`, `effort`, `tiers`,
`ingested`, `preflight`, `bakeoff`, `skillVersions`, **`runShape`**, **`target`**. Bootstrap writes the config
**by construction** — it does NOT re-validate it (that is [[kata-orchestrate]]'s fail-closed load-guard, GB12;
a second validation pass here would be redundant bloat). Then hand off to the loop ([[kata-orchestrate]]).
```

- [ ] **Step 3: Verify frontmatter + wikilinks**

Run: `cd tools && uv run python validate_skills.py`
Expected: `24 skills checked — 0 error(s)`, exit 0. (Confirms `[[kata-readiness]]`/`[[kata-orchestrate]]`
resolve and there is **no** `[[kata-graph]]`. If the validator reports README out-of-sync, that is expected —
Task 5 regenerates it; this step only needs the per-skill frontmatter/wikilink errors to be zero.)

- [ ] **Step 4: Commit**

```bash
git add skills/coordinate/kata-bootstrap/
git commit -m "feat(A3): kata-bootstrap — run-shape router + composition ladder, writes kata.config (D24c/GB1/GB13)"
```

---

## Task 4: Wire `kata-orchestrate` to read `kata.config` (resolve tiers + fail-closed load-guard)

**Files:**
- Modify: `skills/coordinate/kata-orchestrate/SKILL.md` (the Preconditions section, `:33-39`)

**action (LOCKED — GB12, D25, D26):** add config-reading to orchestrate's preconditions. Quote the locked rules
verbatim in the body: *"Absent `kata.config` ⇒ Standard (D25)"*; *"config validation is a fail-closed
load-guard here, NOT a bootstrap phase (GB12)."* Do **not** add a `version` bump (pre-release hold).

- [ ] **Step 1: Add a precondition #0 (config load + resolve + guard)**

Insert before the current precondition #1 in `## Preconditions`:

```markdown
0. **Load `kata.config`** (`protocol/config.md`). **Absent ⇒ assume Standard** (D25) and proceed. Present ⇒
   **fail closed (GB12):** if it is malformed JSON, or names a non-existent `mode`/`effort`, a `tiers[family]`
   that has no `kata-<family>-<tier>` skill, or a `module` with no provider — **STOP and escalate** (do not
   guess a default over a *present-but-broken* config; that is the drift the harness exists to prevent). This
   is the load-guard — bootstrap writes the config by construction, so the real risk is a stale / hand-edited /
   older-version config on a re-entrant run, which only this consumer-side check catches.
   - **Resolve tiers (D26):** for each bare family reference `[[kata-grill]]` / `[[kata-review]]` /
     `[[kata-plan]]` / `[[kata-diagnose]]`, dispatch the concrete `tiers[family]` skill (e.g.
     `kata-grill-standard`); a family absent from `tiers` ⇒ the mode's default tier.
   - **Version-up (`target.kind: "existing"`):** use `target.baselineGate` as the precondition-#2 baseline
     command. (The version-up ingestion DAG — kata-graph — is Spec A4; A3 only consumes the config fields.)
```

- [ ] **Step 2: Verify**

Run: `cd tools && uv run python validate_skills.py`
Expected: per-skill errors 0 (README-sync warning is fine until Task 5). `kata-orchestrate` still `version: 0.1.0`.

- [ ] **Step 3: Commit**

```bash
git add skills/coordinate/kata-orchestrate/SKILL.md
git commit -m "feat(A3): kata-orchestrate reads kata.config — tier resolution + fail-closed load-guard (D25/D26/GB12)"
```

---

## Task 5: Register cost-weights, regenerate README, touch up TAXONOMY

**Files:**
- Modify: `.planning/SKILL-COST-RATINGS.md`
- Modify (regenerate + hand-author Use cells): `README.md`
- Modify: `docs/TAXONOMY.md`

**depends_on:** T2, T3, T4 (all skills must exist for the README regen to pick them up).

- [ ] **Step 1: Add the cost-weight authority rows**

In `.planning/SKILL-COST-RATINGS.md`, add two rows to the main table:

```
| kata-bootstrap | coordinate | M | none (guided single pass; invokes readiness) | inline | low | 2 | pre-loop configurator; writes kata.config. |
| kata-readiness | coordinate | S | none | inline | low | 1 | read-only health/target check; bootstrap-invoked. |
```

- [ ] **Step 2: Regenerate the README index**

Run: `cd tools && uv run python validate_skills.py --write`
This rewrites the `<!-- SKILL-INDEX -->` block from frontmatter (now 24 rows). The two new skills land with
`Use` = `—` (no prior hand-authored cell).

- [ ] **Step 3: Hand-author the two new `Use` cells**

In `README.md`, edit only the `Use` (last) column for the two new rows (mechanical columns stay as regenerated,
so `check_readme_sync` still passes):
- `kata-bootstrap` → `Compose a run (run-shape + ladder), preview cost, write kata.config, launch`
- `kata-readiness` → `Pre-run harness+target readiness check (bootstrap-invoked or standalone doctor)`

- [ ] **Step 4: TAXONOMY touch-up**

In `docs/TAXONOMY.md`, under the spine-vs-module section, note that `kata-bootstrap` and `kata-readiness` are
**spine** (core, always-available; not optional feature modules), and add a one-line "Run-shape preset" entry
(a named bundle over the mode axis that bootstrap pre-fills — GB1). Keep the validator's required terms intact
(`kata-<verb>-<tier>`, `RUBRIC.md`, `Family alias`, `Spine vs module`).

- [ ] **Step 5: Verify**

Run: `cd tools && uv run python validate_skills.py`
Expected: `24 skills checked — 0 error(s)`, exit 0 (README now in sync).
Run: `cd tools && uv run pytest -q` → all pass.

- [ ] **Step 6: Commit**

```bash
git add .planning/SKILL-COST-RATINGS.md README.md docs/TAXONOMY.md
git commit -m "chore(A3): register bootstrap/readiness cost-weights + regenerate README index + TAXONOMY"
```

---

## Task 6: Promote decisions + update design docs + glossary

**Files:**
- Modify: `.planning/DECISIONS.md` (append D34–D46 = GB1–GB13)
- Modify: `docs/DESIGN.md` (COORDINATE spine roster: add `kata-bootstrap`, `kata-readiness`)
- Modify: `docs/MODES-DESIGN.md` (mark D24b/c implemented; record the A3/A4 cut)
- Modify: `CONTEXT.md` (glossary terms)

**depends_on:** T2, T3, T4 (so the docs describe what now exists). Disjoint from Task 5's files.

- [ ] **Step 1: Promote GB1–GB13 into the decision ledger**

In `.planning/DECISIONS.md`, append D34–D46, one per GB branch (titles + the chosen option + provenance),
sourced verbatim from `.planning/specs/modes-A3-bootstrap-wiring/GRILL-LEDGER.md`. Cross-reference the GB id.

- [ ] **Step 2: Add the two skills to the DESIGN spine roster**

In `docs/DESIGN.md`, the COORDINATE row of the spine table (`:51`), add `kata-bootstrap` and `kata-readiness`.

- [ ] **Step 3: Mark the modes design implemented**

In `docs/MODES-DESIGN.md`, under "Open / deferred", mark the `kata-bootstrap`/orchestrate-config items
**implemented (A3)** and note the A3/A4 cut (version-up execution = A4; kata-graph as its ingestion engine).

- [ ] **Step 4: Glossary**

In `CONTEXT.md`, add: **Run-shape** (a named preset over the mode axis: individual/batch/version-up/advanced —
GB1), **Preset** (the `(mode, modules, target)` bundle a run-shape pre-fills), **Readiness** (the
harness-health + target-readiness pre-run check), **Load-guard** (orchestrate's fail-closed `kata.config`
check on read — GB12), **`target`** (`greenfield` | `existing` — the version-up repo + baseline). One tight
definition each, `_Avoid_:` lines per the existing style.

- [ ] **Step 5: Verify + commit**

Run: `cd tools && uv run python validate_skills.py` → 24 skills, 0 errors (docs don't affect skill checks, but
confirm no wikilink regressions in CONTEXT/DESIGN).

```bash
git add .planning/DECISIONS.md docs/DESIGN.md docs/MODES-DESIGN.md CONTEXT.md
git commit -m "docs(A3): promote GB1-GB13 -> D34-D46; spine roster + glossary + modes-design status"
```

---

## Task 7: Adversarial review (D15) — the whole A3 diff

**Files:**
- Create: `.planning/specs/modes-A3-bootstrap-wiring/REVIEW.md`

**depends_on:** T1–T6.

- [ ] **Step 1: Dispatch a fresh-context `kata-review` (advanced tier) over the full A3 diff**

Use `kata-review` in "could two independent builders still diverge / what breaks this?" mode against
`git diff master...phase-2/modes-A3-bootstrap`. Specifically stress:
- Does the orchestrate load-guard actually fail closed on every malformed/stale-config case, or are there silent
  fallbacks that re-introduce drift?
- Is any structural invariant (no-self-certification, no-drift, default-FAIL, DRY) weakened by the new wiring? (D33)
- Does bootstrap leak a `[[kata-graph]]` wikilink or otherwise depend on unbuilt A4 machinery?
- Is the version-up config writable but *honestly flagged* execution-pending (not silently broken)?
- Bootstrap/readiness frontmatter + tags + cost-weights conform to STANDARDS §1; versions held at 0.1.0.

- [ ] **Step 2: Record the verdict + fix loop**

Write `REVIEW.md` (HOLD/SHIP + findings). For each blocker, dispatch a fix subagent against the owning task,
re-run the gate (`pytest -q` + `validate_skills.py` → 24 skills, 0 errors), re-review until SHIP.

- [ ] **Step 3: Final gate + commit**

Run: `cd tools && uv run pytest -q` (all pass) + `uv run python validate_skills.py` (`24 skills checked — 0
error(s)`, exit 0).

```bash
git add .planning/specs/modes-A3-bootstrap-wiring/REVIEW.md
git commit -m "docs(A3): adversarial review HOLD->SHIP (D15)"
```

Then merge to master `--no-ff` and update STATE/ROADMAP (A3 done).

---

## Plan frontmatter (for `kata-orchestrate`)

```yaml
ownership:
  T1: [protocol/config.md, tools/validate_skills.py, tools/tests/test_validate_skills.py]
  T2: [skills/coordinate/kata-readiness/SKILL.md]
  T3: [skills/coordinate/kata-bootstrap/SKILL.md, skills/coordinate/kata-bootstrap/resources/run-shapes.md]
  T4: [skills/coordinate/kata-orchestrate/SKILL.md]
  T5: [.planning/SKILL-COST-RATINGS.md, README.md, docs/TAXONOMY.md]
  T6: [.planning/DECISIONS.md, docs/DESIGN.md, docs/MODES-DESIGN.md, CONTEXT.md]
  T7: [.planning/specs/modes-A3-bootstrap-wiring/REVIEW.md]
waves:
  wave1: [T1]
  wave2: [T2, T4]      # disjoint files, both depend on T1
  wave3: [T3]          # depends on T2 (the [[kata-readiness]] wikilink target)
  wave4: [T5, T6]      # disjoint; both depend on the skills existing
  wave5: [T7]
depends_on:
  T2: [T1]
  T3: [T1, T2]
  T4: [T1]
  T5: [T2, T3, T4]
  T6: [T2, T3, T4]
  T7: [T1, T2, T3, T4, T5, T6]
```

**Disjoint-ownership check:** no file appears under two tasks. ✔
**DAG check:** acyclic; every task reachable from T1. ✔
