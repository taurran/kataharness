# DETERMINISM DOCTRINE — KataHarness

**Status:** adopted 2026-07-12 (Fable 5 health review). Read with `docs/STANDARDS.md`.
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
   set per call-site. *(Model: `kata_telemetry._run_git`. Known stragglers at adoption:
   `contract_gate`, `kata_restore` fork-point, `footprint` — DET-02..05.)*
2. **Sorted at every filesystem boundary.** No unsorted `rglob`/`iterdir`/`listdir`/`glob`
   result may drive artifact content, edge selection, or float accumulation order.
   *(Model: `contract_edges` sorted rglob. Known straggler: `graph_gen.build_graph` — DET-01.)*
3. **Sets and dicts never drive output order.** `PYTHONHASHSEED` makes set iteration a
   per-process coin flip. `sorted()` before anything appends to an output.
   *(Model: `characterization_snapshot_verdict`. Straggler: `drift_verdict` — DET-07.)*
4. **Length-prefix every multi-item digest.** No hash over concatenated variable-length items
   without netstring/length prefixes — the D98 collision lesson, applied always.
   *(Models: `benchmark_control.content_hash`, `contract_edges._netstring_hash`.
   Straggler: `kata_telemetry.evidence_digest` — DET-10, fix at next digest-schema rev.)*
5. **`sort_keys=True` on any JSON that is committed, appended, or compared.** Builder dicts
   with fixed key order are safe; any pass-through map canonicalizes at the serialization
   boundary. *(Model: `contract_gate.write_contract_gate`. Straggler: `build_ledger_row` —
   DET-08.)*
6. **Timestamps live only where nothing compares them.** A wall-clock stamp may sit in an
   artifact only if the artifact is never byte-compared/hashed whole, or the comparator scrubs
   it (narrow patterns, never masking real values — the `drift_gate.scrub_nondeterminism`
   pattern). New comparators must state which.
7. **Injectable clocks for anything that decides.** Decision code takes `now` as a parameter
   (`kata_gauge.read_bridge`, `slack_ratio`); a raw `datetime.now()` is legal only in log
   stamps and documented hint-only fields (`recall._is_stale`).
8. **Gate subprocesses run in a declared environment, argv-only.** Anything whose exit code
   feeds a gate or score: no `shell=True`, explicit env handling (strip `PYTEST_ADDOPTS`,
   control plugin autoload where the target allows), and the invocation recorded in the
   artifact. *(Stragglers: `mutation_run._default_runner`, `mutation_check.run_named_test` —
   DET-09.)* Gate runners also carry timeouts — a hung gate is a nondeterministic outcome.
9. **Randomness mints identity only.** No randomness in sampling, tie-breaking, or scoring,
   ever. A minted id (`uuid4`) is persisted then compared as stored data; content-addressed
   ids are strictly stronger and preferred where the content hash already exists.
10. **Ties break on an explicit total order.** Every ranking sort ends its key tuple with a
    deterministic tie-break (id/label) — stated, not implied by sort stability.
    *(Model: `project_find.py` ranking. Stragglers: `benchmark` rank/max — DET-11.)*

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
- The straggler list above is the adoption-time debt registry; each fix cites its DET-id from
  `.planning/REVIEW-FABLE5-2026-07-12.md`.
- Repo conventions already load-bearing and kept: LF pinned via `.gitattributes` ("build/
  handoff sizes must be deterministic"), `encoding="utf-8"` on every read/write (verified
  zero gaps at adoption), pure-function engines with injected runners.
