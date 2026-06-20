---
name: kata-understand
description: >-
  Produce a graph-backed comprehension map of what changed and what was built in a completed harness run — opt-in,
  offered by the closeout stage; degrades gracefully to a git/diff map when the graph backend is unavailable;
  never blocks and never gates correctness.
license: Apache-2.0
version: 0.1.0
category: handoff
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Bash]
model: fable
source: >-
  new (KataHarness original, Phase 2 GL-R2c / DESIGN §3 / PLAN-phase2 Task C1) — comprehension-map half of the
  closeout back-half; backed by the F2 graph runtime (tools/graph_gen.py → kata.graph.json)
tags:
  - kata/handoff
  - kata/module/closeout
  - understand
  - graph-backed
  - opt-in
---

# kata-understand — graph-backed comprehension map of a completed run

An **opt-in** read-leaning skill offered by the closeout stage (via `kata-closeout` — referenced in prose only,
built in a parallel slice). It produces a **structured comprehension map** of what changed and what was built in a
completed harness run. It is **not** part of the default-FAIL gate, never blocks, and never re-evaluates
correctness — that stays with `kata-evaluate`. It maps; it does not judge.

> **Opt-in contract:** `kata-closeout` offers this skill per run. The human opts in. If the human declines,
> closeout proceeds without it. The understand-map is supplemental output — additive, never gating.

---

## Primary path — graph-backed map

**Precondition:** `kata.graph.json` exists (or can be (re)generated now).

### Step 1 — Run / refresh the F2 graph runtime

Invoke [[kata-graph]]'s `tools/graph_gen.py` to produce or refresh `kata.graph.json`:

```bash
cd <repo-root>/tools
uv run python graph_gen.py --root .. --out ../kata.graph.json
```

The generator walks `*.py` files via tree-sitter (AST-only, no `exec`/`eval`), emits `file` and `symbol` nodes
with PageRank `rank`, and resolves `def` + `import` edges (best-effort `ref`). It is content-hash incremental —
pass `--prev` if a prior graph exists to reuse unchanged files. Full schema: `protocol/graph.md`.

### Step 2 — Load `kata.graph.json` and the run footprint

Read:
- `kata.graph.json` — the structural map per `protocol/graph.md` (nodes: `file`/`symbol`; edges: `def`/`ref`/
  `import`; each node carries a `rank` float).
- `.kata/footprint.json` — the run's declared-touched files (F1 artifact from `kata-evaluate`).
- Optionally `.kata/mutation.json` — non-vacuity proof (confirms real changes occurred).
- Cross-check with `git diff --name-only HEAD~1..HEAD` (or the relevant range) to capture any files changed
  outside the declared footprint.

### Step 3 — Project the comprehension map

Intersect the run footprint / git-diff file set with graph nodes to project the map. Do not re-run or re-score
correctness. **Map only.**

#### Changed
Files that appear in BOTH the run footprint (or git diff) AND the graph's `file` nodes:
- List each by repo-relative path.
- Include its `rank` (structural importance in the repo graph).
- Note edge types present: `def` (defines symbols), `import` (imported by / imports), `ref` (referenced by).

For files NOT in the graph (e.g. pure markdown/YAML): list them as **untracked by graph** — they changed but
carry no structural role in the Python map.

#### Added
Symbols and files that are NEW in this run (present in the current graph, absent from the prior graph or not
present in any `--prev` graph node set):
- New `file` nodes: new source files introduced this run.
- New `symbol` nodes (`symKind: function|class|method`): new top-level functions, classes, or methods, with
  their `span` and `signature` if available.
- New skill/module paths (non-Python): discovered via `git diff --name-only --diff-filter=A`.

#### Structural role / blast context
For each changed file that appears in the graph:
- **Rank tier:** high (`rank > 0.05`), medium (`0.01–0.05`), low (`< 0.01`) — a proxy for how central the
  file is to the repo's call/import graph.
- **Incoming `ref`/`import` edges** (who depends on it): files or symbols that reference this node — these
  are the blast-radius neighbors. List up to 5; note if there are more.
- **Outgoing `import`/`ref` edges** (what it depends on): what this file imports or references — context for
  understanding its role.

This section is a **structural map, not a correctness judgment.** High rank + many inbound refs = high blast
potential; low rank + no inbound refs = isolated change. The human uses this to decide what to review next.

#### Open questions
Surface genuine ambiguities the map reveals but cannot resolve — for the human or the next run:
- Symbols changed with high inbound blast that were NOT covered by the plan's acceptance criteria (possible
  undeclared scope expansion).
- Files in the footprint with no graph node (markdown, config, YAML) whose role is structurally opaque.
- Any delta between the declared footprint (`.kata/footprint.json`) and the git diff (unreported changes).
- Mutation proof absent or vacuous (`.kata/mutation.json` missing or empty) — flag for the human.

---

## Light fallback — git/diff map (graph backend unavailable)

> **Note: graph backend unavailable.** `kata.graph.json` could not be generated or read (tree-sitter absent,
> greenfield repo with no `.py` files, or generator error). This map is derived from `git diff` only. Structural
> ranks and blast-radius context are NOT available. Treat this map as a file-level diff summary, not a structural
> analysis.

When the graph backend is unavailable, degrade to this lighter path — never hard-fail.

### Fallback: Changed
Run:
```bash
git diff --name-only HEAD~1..HEAD
```
List every changed file with its status (`M` modified, `A` added, `D` deleted, `R` renamed). No rank available.

### Fallback: Added
Run:
```bash
git diff --name-only --diff-filter=A HEAD~1..HEAD
```
List new files. For `.py` files, optionally grep for top-level `def` and `class` names as a lightweight symbol
summary (no AST — pattern only, may miss nested or decorated definitions):
```bash
grep -n "^def \|^class " <new_file.py>
```

### Fallback: Structural role / blast context
Not available without the graph. Note: "No structural rank or blast-radius available in fallback mode. Run
`tools/graph_gen.py` once tree-sitter is installed to unlock the full map."

### Fallback: Open questions
Flag: graph backend unavailable — install tree-sitter and rerun to get full structural context. List any
footprint / git-diff delta as above.

---

## Output shape — the understand-map artifact

Emit the map as a **human-readable Markdown block** (suitable for inline display or a handoff artifact). Sections
in order:

```
## Understand-map — <run-id or branch> (<date>)
> Backend: tree-sitter | fallback-git-diff

### Changed
...

### Added
...

### Structural role / Blast context
...

### Open questions
...
```

If the backend is the fallback, prepend the degradation note (verbatim from the Fallback section above) before
the `### Changed` heading.

---

## Discipline

- **Map, don't judge.** This skill reads and projects. It does not re-run tests, re-score correctness, or override
  `kata-evaluate`'s verdict. The default-FAIL gate is inviolable; this skill runs after it.
- **Never hard-fail.** If `kata.graph.json` cannot be generated, fall through to the git/diff fallback. If `git
  diff` also fails, emit what is known and flag the gap.
- **Read-only toward the codebase.** `Bash` is used only to run the existing graph generator and `git diff`
  commands. No writes to source files.
- **Graceful degradation chain:** graph-backed (tree-sitter) → fallback (git/diff) → partial (flag and continue).
- **Opt-in always.** If the human declines, return immediately with no output. Never auto-invoke.
