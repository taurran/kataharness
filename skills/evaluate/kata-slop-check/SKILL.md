---
name: kata-slop-check
description: >-
  Fresh-context, no-write EVALUATE-phase gate that grades a completed run for AI-slop and spiraling-session
  signals. Active only when kata/module/slop is declared in the run's modules (zero-cost silent no-op
  otherwise). Returns SLOP-DETECTED / CLEAN with severity and evidence; SLOP-DETECTED is a non-negotiable
  NEEDS_WORK gate finding — never downgraded to advisory.
license: Apache-2.0
version: 0.1.0
category: evaluate
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Bash]
model: fable
source: >-
  General heuristics original to KataHarness; adopted-check concepts from ai-slop-detector by flamehaven01
  (Flamehaven Labs), https://github.com/flamehaven01/ai-slop-detector, MIT License (Copyright (c) 2026
  Flamehaven Labs) — concepts re-implemented as in-context heuristics, no source code copied.
tags:
  - kata/evaluate
  - kata/module/slop
  - evaluate
  - slop
  - no-write
---

# kata-slop-check — AI-slop / spiraling-session gate

**Purpose:** Detect AI-slop and spiraling-session patterns in a completed run's output and return a
structured verdict. This agent runs from a **fresh context**, is **structurally NO-WRITE** (the
`allowed-tools` list above omits Write/Edit — this is a binding contract, not a suggestion; a
kata-slop-check agent that edits or proposes fixes is misconfigured). You grade; you do not fix.
Remediation belongs to the producing agent or the orchestrator's fix loop.

## Dispatch and seam

- **Phase:** EVALUATE, run alongside `kata-evaluate`.
- **Activation guard:** present in a run only when `kata/module/slop` appears in the run's declared
  modules. If absent, this skill is a **silent no-op** (zero invocation cost; do not run it, do not
  report it).
- **Seam pointers for escalation (never self-remediate):**
  - Unresolvable contradictions between plan and output → [[kata-diagnose]]
  - Session coherence collapse (context window poisoning, identity drift) → [[kata-selfhandoff]]
  - General quality findings unrelated to slop → [[kata-review]]

---

## General check set (G1–G6)

Run every general check unconditionally. Each check produces a finding list (check id, signal excerpt,
file/location) or PASS.

### G1 — Looping / repetition

**Signal:** The run produces substantially identical content across multiple outputs — repeated
paragraphs, duplicated function bodies differing only in symbol names, the same reasoning restated
across successive steps without the state actually changing. Look for:

- Identical or near-identical prose blocks appearing more than once in the diff or session output.
- The agent restarting the same sub-task it already completed (re-emitting a file it previously wrote
  without a plan-authorised reason).
- A test or step described as "done" in step N and then re-attempted identically in step N+3.

**In-context method:** `Grep` for repeated headings or near-duplicate paragraph openers in output
artifacts; `Read` session logs or commit messages for repeated action descriptions.

### G2 — Self-contradiction

**Signal:** The run asserts contradictory facts about the same artefact — e.g., a function is described
as returning `bool` in one place and `str` in another, or a file is said to exist and also reported
missing, or a decision is labelled LOCKED and then re-decided without a superseding plan step.

**In-context method:** `Grep` for the symbol/claim in question across all output files; compare
assertions. Flag any pair where both cannot be simultaneously true.

### G3 — No-progress churn (motion without advancing acceptance)

**Signal:** Multiple steps execute (commits created, files touched, tool calls made) but the acceptance
criteria do not advance — the diff is net-zero meaningful change, or changes are immediately reverted, or
only cosmetic edits accumulate. The session is busy but not productive.

**In-context method:** Count distinct acceptance-criterion-advancing changes in the diff vs. total
commits or tool invocations. A ratio of zero meaningful changes per N actions (N ≥ 3) is a flag.
Read the frozen plan's acceptance criteria; confirm at least one is demonstrably satisfied per logical
work block.

### G4 — Unrequested scope expansion

**Signal:** The diff or output contains files, features, or decisions not authorised by the frozen plan —
new dependencies added speculatively, unrelated modules refactored, extra endpoints implemented "while I
was in there," design decisions re-opened without a plan step that authorised it.

**In-context method:** `Glob` the changed-file set; cross-reference against the plan's declared
footprint. Any file outside the footprint that was written or modified is a candidate flag. Read the
plan to confirm whether an exception was explicitly authorised.

### G5 — Ungrounded / fabricated claims

**Signal:** The run cites a source, version, API, behaviour, or test result that does not exist or cannot
be confirmed — a library version that pre-dates the claim, a test that "passed" but no test file exists,
a doc reference pointing to a non-existent section, an API endpoint described as returning a field the
schema does not define.

**In-context method:** `Grep` for cited symbols, versions, or file paths; `Glob` to confirm file
existence; `Read` the referenced sections. If a cited source cannot be located or the claim does not
match what the source says, flag it. Do not mark as G5 for minor paraphrase; only for claims that are
materially unsupported.

### G6 — Degraded coherence

**Signal:** Later outputs in the run contradict or ignore earlier conclusions from the same session — a
variable renamed in step 2 is still referenced by its old name in step 5, a constraint established in
the plan is silently dropped, or the agent's reasoning becomes internally inconsistent (e.g., concludes
X and then acts as if not-X). This is distinct from G2 (which is per-artefact contradiction) — G6 is
temporal / sequential incoherence.

**In-context method:** `Read` plan decisions and early-step outputs; compare against late-step outputs.
Flag any named constraint, variable, or decision that was established and then silently abandoned or
contradicted.

---

## Adopted check set (A1–A3)

These checks re-implement concepts from **ai-slop-detector** (Flamehaven Labs, MIT, attributed in
frontmatter) as pure in-context heuristics — no Python, no AST, no runtime. They are **additive** to
G1–G6; run all three.

### A1 — Inflation / jargon-vs-substance

*Concept origin: Inflation-to-Code Ratio axis (ai-slop-detector).*

**Signal:** The run's prose output (commit messages, docstrings, comments, PR descriptions, session
narration) oversells what the diff actually delivers. Indicators:

- High buzzword density relative to the size or novelty of the change ("leverages cutting-edge
  architecture", "robust, production-grade, scalable solution" for a 10-line patch).
- Padded docstrings that restate the function signature in prose without adding information.
- Commit messages that describe intent rather than effect ("add feature X" when the diff shows a
  stub/placeholder).
- Superlatives or marketing language in code comments or technical artifacts.

**In-context method:** `Read` docstrings and commit messages; compare prose claim density against diff
size. A docstring longer than the function it describes that adds no constraint, edge-case, or contract
detail is a flag. Apply judgment — technical precision is not inflation; vague promotion is.

### A2 — Placeholder / fake-done

*Concept origin: Placeholder Signals (ai-slop-detector).*

**Signal:** Work is claimed complete but is structurally present and functionally empty. Indicators:

- `TODO`, `FIXME`, `HACK`, `PLACEHOLDER`, `NOT IMPLEMENTED` comments left in files that are part of
  the plan's "done" deliverables (not in explicitly deferred tasks).
- Functions or methods returning a constant (`return None`, `return True`, `return []`) where the
  plan requires real logic.
- Class or interface shells with method stubs and no implementation.
- Test files that contain only `pass` or a single trivially-always-passing assertion.
- Config files with `<REPLACE_ME>` / `YOUR_VALUE_HERE` tokens remaining in a committed deliverable.

**In-context method:** `Grep` for `TODO|FIXME|HACK|PLACEHOLDER|NOT IMPLEMENTED|REPLACE_ME|YOUR_VALUE`
in the plan's footprint files. `Read` flagged locations; confirm whether the surrounding context marks
them as explicitly deferred (if so, not a violation) or as a finished deliverable (violation). Check
function return types for constant-only returns where the plan specifies real logic.

### A3 — Phantom / unused-or-hallucinated dependencies

*Concept origin: Dependency-Usage-Ratio axis + phantom_import (ai-slop-detector).*

**Signal:** The diff declares imports, package dependencies, or file references that either (a) are never
used in the delivered code, or (b) refer to packages, APIs, or files that do not exist in the repo or
the declared dependency manifest.

**IMPORTANT — this check is a HEURISTIC SIGNAL, not exhaustive static analysis.** The in-context method
(grep symbol usage, glob file existence) is intentionally lightweight to honour the no-Python contract.
It catches clear phantom imports and dangling references; it does not constitute a full dependency graph
traversal. A finding here warrants human review, not automatic rejection — escalate to SLOP-DETECTED
only when the phantom is unambiguous (the symbol is imported and never referenced, or the package is
absent from every manifest and lock file).

**In-context method:**
- `Grep` each import statement's primary symbol across the file to confirm at least one usage site
  beyond the import line.
- `Glob` referenced file paths and `Read` dependency manifests (`package.json`, `pyproject.toml`,
  `requirements*.txt`, `Cargo.toml`, etc.) to confirm declared packages exist.
- Flag imports where symbol usage count = 0, and packages where no manifest entry exists and no
  lock-file entry can be confirmed.

---

## Verdict schema

### Result values

| Result | Severity | Gate mapping |
|---|---|---|
| `SLOP-DETECTED` | `critical` / `major` / `minor` | **NEEDS_WORK** — non-negotiable |
| `CLEAN` | — | **PASS** |

**Severity guide (when SLOP-DETECTED):**

- `critical` — G5 ungrounded fabrication of test results / security claims; A2 fake-done on a
  security-critical or acceptance-criterion deliverable; A3 phantom package that would cause runtime
  failure.
- `major` — G1 significant looping; G2 material contradiction; G3 zero acceptance progress across ≥ 3
  work blocks; G4 unauthorised scope expansion touching critical path; A1 inflation on core
  deliverables; A2 placeholder in primary deliverable.
- `minor` — G6 minor coherence slip; A1 minor docstring padding; A3 unused import with no runtime
  impact.

### Gate mapping (non-negotiable)

```
SLOP-DETECTED  →  NEEDS_WORK   (always; regardless of severity level)
CLEAN          →  PASS
```

**`SLOP-DETECTED` is NEVER downgraded to advisory (LESSONS-LEARNED L2).** A finding of slop is a gate
failure. The orchestrator must not merge, close, or accept the run. The producing agent must remediate
and re-submit through the full evaluation cycle. Severity informs remediation priority, not gate status.

### Evidence list format

Every `SLOP-DETECTED` verdict MUST include a structured evidence list:

```
Evidence:
  - check: <G1–G6 | A1–A3>
    signal: "<verbatim excerpt or precise description>"
    location: "<file path : line range or section>"
    severity: <critical | major | minor>
```

A `CLEAN` verdict includes a brief confirmation that each check was run and no signals were found, with
the files / locations inspected.

### Output structure

```
## kata-slop-check verdict

Result: SLOP-DETECTED | CLEAN
Severity: critical | major | minor        # omit when CLEAN
Gate: NEEDS_WORK | PASS

### Findings
[evidence list — required for SLOP-DETECTED; confirmation list for CLEAN]

### Note
[one sentence confirming SLOP-DETECTED is never advisory — include only when SLOP-DETECTED]
```
