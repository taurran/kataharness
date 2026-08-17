# orphan-corpus — the T6–T11 calibration ground truth for S1/S2/S3

**Standing humility (TM-D2, verbatim):** *"the judgment+human layers found all of these; the
automated mechanical gates found none."* Detectors ATTEST and NARROW; judges judge.

This is a miniature repo, scanned by the REAL `graph_gen.build_graph`, whose shapes mirror the six
**FACADE** rows of the trust ledger (`.planning/specs/trust-model/ASSESSMENT.md` §1, rows T6–T11).
It is ground truth, not a mock: the corpus is calibrated against the same defect shapes an operator
and a human reviewer found by hand in the live tree, and the live symbols each row mirrors were
re-verified to exist at build time.

## The T6–T11 rows this corpus mirrors

| Row | Ledger claim (ASSESSMENT.md §1) | Live symbol mirrored | Corpus file | Orphan shape |
|---|---|---|---|---|
| T6 | Nothing builds from a draft (D169) | `kata_restore.assert_frozen:557`, `kata_dispatch.build_brief:80` | `t6_dispatch.py` | caller is in the SAME file (graph_gen emits no self-file ref edge) and the caller itself has zero callers |
| T7 | Host-only roles never route off-host | `kata_roles.resolve_roles:99`, `kata_roles.HOST_ONLY_ROLES:55` | `t7_roles.py`, `t7_preflight.py` | the would-be caller (`run_preflight`) exists and is itself wired, but never calls `resolve_roles` |
| T8 | The contract gate ran | `contract_gate` producer | `t8_contract_gate.py` | producer-only: defines the writer, nothing calls it |
| T9 | Runs are accounted (telemetry) | `kata_telemetry` engine | `t9_telemetry.py` | whole engine, zero callers |
| T10 | Runs survive interruption | `kata_restore.detect_lost_run:76`, `kata_restore.fold_board:153` | `t10_restore.py` | three engine functions, zero callers |
| T11 | Research claims are grounded | `grounding_gate.grounding_verdict:56`, `grounding_gate.build_verdict:111` | `t11_grounding.py` + `tests/t11_grounding_check.py` | **test-only callers** — the tests-path filter is what turns this from "wired" into the orphan it is |

## Negative controls — a detector that flags everything is vacuous

- `wired_helper.helper_wired` — called from `wired_pipeline.py` (a non-test file) AND from
  `tests/wired_helper_check.py`. Must be reported CLEAR: a test caller neither creates nor destroys
  wiring.
- `t7_preflight.run_preflight` — called from `wired_pipeline.py`. Must be CLEAR. This is what makes
  the T7 finding sharp: the preflight is wired, it just never calls `resolve_roles`.

## The five honest limits, each with its own fixture

These are S1's stated limits carried VERBATIM from DESIGN §3.1. Each has a fixture here and a test
in `tools/tests/test_truth_signals.py` that DEMONSTRATES the wrong answer — the limits are pinned,
not merely prosed.

| Limit (verbatim) | Fixture | Wrong answer demonstrated |
|---|---|---|
| call-only edges | `limit_call_only.py`, `limit_call_only_consumer.py` | `used_as_value` is referenced as a value, never called ⇒ no ref edge ⇒ reported unwired (false positive) |
| bare-name matching | `limit_bare_name_a.py`, `limit_bare_name_b.py`, `limit_bare_name_caller.py` | the caller imports and calls `b`'s `shared_name`; name matching credits `a` (first sorted candidate) ⇒ the genuine orphan `a` looks wired (false negative) and the real target `b` looks unwired (false positive) |
| fabricated `src` attribution | `limit_fabricated_src.py`, `limit_fabricated_target.py` | the real caller is `zzz_actual_caller`; `graph_gen._extract_refs` attributes the edge to the file's alphabetically-first symbol, so provenance names `aaa_innocent` |
| dynamic imports invisible | `limit_dynamic_caller.py`, `limit_dynamic_target.py` | `getattr(importlib.import_module(...), "dynamic_only")()` produces neither an import edge nor a ref edge ⇒ reported unwired (false positive) |
| out-of-graph entry points look dead | `wired_pipeline.py`, `entrypoints/run.sh` | `run_pipeline` is invoked by a shell entry point graph_gen never scans (it globs `*.py` only) ⇒ reported unwired (false positive) |

## S2 / S3 fixtures

- `prose/` — reuse-claim trigger phrases with resolving, missing, and dangling `file:line`
  citations, plus the D-5 case: an anchor that RESOLVES and is still wrong (existence is not
  support).
- `labels/` — honesty-label clause-pin presence (`labelled-closeout.md`) and absence
  (`unlabelled-closeout.md`) on named artifacts.

## Deliberate corpus note

`t7_roles.HOST_ONLY_ROLES` is a module-level constant, faithful to the live code. `graph_gen`
extracts function and class definitions only, so a constant is not a symbol node and cannot appear
in an S1 finding. T7's corpus finding is `resolve_roles`. Constant-level orphan detection is not a
v1 capability and is not claimed as one.
