# DETERMINISM DOCTRINE — KataHarness

**Status:** adopted 2026-07-12 (Fable 5 health review); **DET registry reconciled 2026-07-25 —
all 14 adoption-time stragglers RESOLVED and re-verified against code.**
Read with `docs/STANDARDS.md`.
**Scope:** every engine module in `tools/`, every adapter, and every skill-prose instruction
that produces a gated, scored, ordered, hashed, or committed artifact.

## The rule

**Anything that gates, scores, orders, hashes, compares, or writes a durable artifact MUST be
reproducible: same inputs ⇒ same bytes, on any machine, under any operator config.** LLM
judgment is reserved for questions no rule can decide — and even then the *decision record*
(verdict line, trail token, ledger row) is deterministic in form. Deterministic-first is not a
style preference; it is what makes gate verdicts auditable, evidence re-derivable, and drift
detectable. A nondeterministic gate is a gate that cannot be trusted twice.

## The ten laws

1. **One pinned git helper.** Every git call whose stdout is parsed goes through a shared
   helper pinning: `core.quotepath=off` · `--no-renames` (where file sets are compared) ·
   `log.follow=false` · `log.showSignature=false` · `color.ui=false`. Never re-derive the pin
   set per call-site. *(Model: `kata_telemetry._run_git`. Adoption-time stragglers DET-02..05
   RESOLVED: `contract_gate.py:150-152,185-186`, `kata_restore.py:493`, `footprint.py:226-228,161`.)*
2. **Sorted at every filesystem boundary.** No unsorted `rglob`/`iterdir`/`listdir`/`glob`
   result may drive artifact content, edge selection, or float accumulation order.
   *(Model: `contract_edges` sorted rglob. Straggler DET-01 RESOLVED: `graph_gen.py:419,506,
   508,607,614,655` — discovery, sets, AND lexicographic ref-target selection all pinned.)*
3. **Sets and dicts never drive output order.** `PYTHONHASHSEED` makes set iteration a
   per-process coin flip. `sorted()` before anything appends to an output.
   *(Model: `characterization_snapshot_verdict`. Straggler DET-07 RESOLVED:
   `drift_gate.py:185` `sorted(all_ids)`.)*
4. **Length-prefix every multi-item digest.** No hash over concatenated variable-length items
   without netstring/length prefixes — the D98 collision lesson, applied always.
   *(Models: `benchmark_control.content_hash`, `contract_edges._netstring_hash`.
   Straggler DET-10 RESOLVED: `kata_telemetry.evidence_digest` netstring-frames each entry,
   `kata_telemetry.py:449-465` — a digest-SCHEMA change, documented in place.)*
5. **`sort_keys=True` on any JSON that is committed, appended, or compared.** Builder dicts
   with fixed key order are safe; any pass-through map canonicalizes at the serialization
   boundary. *(Model: `contract_gate.write_contract_gate`. Straggler DET-08 RESOLVED:
   `build_ledger_row`, `kata_telemetry.py:1464-1470`.)*
6. **Timestamps live only where nothing compares them.** A wall-clock stamp may sit in an
   artifact only if the artifact is never byte-compared/hashed whole, or the comparator scrubs
   it (narrow patterns, never masking real values — the `drift_gate.scrub_nondeterminism`
   pattern). New comparators must state which.
7. **Injectable clocks for anything that decides.** Decision code takes `now` as a parameter
   (`kata_gauge.read_bridge`, `slack_ratio`); a raw `datetime.now()` is legal only in log
   stamps and documented hint-only fields (`recall._is_stale`).
8. **Gate subprocesses run in a declared environment.** Anything whose exit code feeds a gate
   or score strips env-injected nondeterminism (`PYTEST_ADDOPTS`) and records its invocation.
   **Prefer surgical over blanket:** on a known-pytest path (`mutation_check.run_named_test`,
   the scoring path) keep plugin autoload and block only the nondeterminism plugin by argv
   (`-p no:randomly`) — a blanket `PYTEST_DISABLE_PLUGIN_AUTOLOAD` would make a target's
   autoload-reliant tests (pytest-asyncio/mock/django) FAIL under the gate when they pass
   normally, *deflating* the score (adval R1). Reserve the blanket env-disable for the
   arbitrary-command path (`mutation_run._default_runner`) where argv can't be injected; there
   `shell=True` is retained because the `test_cmd` contract is a shell string (operator-trust,
   exec-safety-registered). Gate runners also carry timeouts — a hung gate is a
   nondeterministic outcome.
9. **Randomness mints identity only.** No randomness in sampling, tie-breaking, or scoring,
   ever. A minted id (`uuid4`) is persisted then compared as stored data; content-addressed
   ids are strictly stronger and preferred where the content hash already exists.
10. **Ties break on an explicit total order.** Every ranking sort ends its key tuple with a
    deterministic tie-break (id/label) — stated, not implied by sort stability.
    *(Model: `project_find.py` ranking. Straggler DET-11 RESOLVED: `benchmark.py:591-594`
    (pareto-best `min` over `(-composite, label)`) and `:779-782` (rank sort) — matched keys.)*

## Where judgment is allowed

LLM judgment decides only: grill resolutions, review verdicts/findings content, evaluator
NEEDS_WORK reasoning, research synthesis — places where no rule can decide. Even there:
- the **trigger** for judgment is rule-verifiable (the M4 doctrine: judge only after a
  deterministic signal trips);
- the **record** of judgment (DECISION lines, `tier:` trail tokens, verdict enums, ledger
  rows) is schema-pinned and deterministic in form, so the trail re-derives byte-stable.

## Enforcement

- New engine code: review against the ten laws; a violation in a gate/score/digest path is a
  gate-failing finding (class `nondeterminism`).
- **Skill-level enforcement** (a `nondeterminism`-class check wired into `kata-review` /
  `kata-evaluate`) is **NOT built** — it is a named open follow-up (`AGENTS.md` Conventions).
  Today the ten laws are enforced by human/agent review at the gate, not by a tool.

## The DET registry — adoption-time debt, ALL RESOLVED (reconciled 2026-07-25)

DET-01..14 were opened by the 2026-07-12 Fable 5 health review
(`.planning/REVIEW-FABLE5-2026-07-12.md`, the findings ledger) and closed in that review's
**Round 3** ("wire these up and fix ALL of these disconnects" — every named health-review
deferral was built). **Each id below was re-verified against the code on 2026-07-25**; ids are
retained, never deleted, so a downstream consumer can reconcile against them.

| DET | Was | Resolved at |
|---|---|---|
| DET-01 | `graph_gen` unsorted rglob + set iteration + first-candidate ref-target | `graph_gen.py:419,506,508,607,614,655` |
| DET-02 | single-pathspec `git log` without `log.follow=false` | `contract_gate.py:150`, `kata_restore.py:493` |
| DET-03 | no `log.showSignature=false` pin | `contract_gate.py:151,185`, `kata_telemetry` helper |
| DET-04 | `footprint.changed_in_task` missing `core.quotepath` | `footprint.py:226-228` |
| DET-05 | `footprint.changed_since` missing pins | `footprint.py:161` |
| DET-06 | `COLUMNS`-driven diffstat width | `footprint.py:294` (`--stat=200 --stat-graph-width=200`) |
| DET-07 | `drift_gate` set-union iteration order | `drift_gate.py:185` |
| DET-08 | `build_ledger_row` `json.dumps` without `sort_keys` | `kata_telemetry.py:1464-1470` |
| DET-09 | gate-runner inherited env / shell semantics | `mutation_check` / `mutation_run` env sanitization (see law 8 — `shell=True` deliberately RETAINED on the arbitrary-command path) |
| DET-10 | `evidence_digest` bare `"\n".join` | `kata_telemetry.py:449-465` (netstring) |
| DET-11 | benchmark float-tie rank by insertion order | `benchmark.py:591-594,779-782` |
| DET-12 | temp-path scrub missed `/var/folders`; node-id separators | `drift_gate.py:107-111,151` |
| DET-13 | `uuid4`+`now` benchmark identity later compared | `benchmark_def.py:340-372` (opt-in content-addressed `benchmark_ca_<hex>`) |
| DET-14 | wall-clock in durable graph artifacts | `graph_gen.py:489,713` (injectable `generated_at`; nothing hashes it) |

**There is no open determinism adoption debt.** A new violation opens a new DET id.
- Repo conventions already load-bearing and kept: LF pinned via `.gitattributes` ("build/
  handoff sizes must be deterministic"), `encoding="utf-8"` on every read/write (verified
  zero gaps at adoption), pure-function engines with injected runners.
