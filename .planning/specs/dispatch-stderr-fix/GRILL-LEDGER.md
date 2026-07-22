# GRILL-LEDGER — dispatch-stderr-fix (light tier, 2026-07-21, operator present)

> Subject: surgical fix of the kata_dispatch stderr-discard defect. `_subprocess_runner`
> (`tools/kata_dispatch.py:172-174`) runs `capture_output=True` but returns only `proc.stdout`;
> `dispatch()` (`:200-204`) builds the failure envelope with only `worker exited {code}` +
> `raw=stdout` — the provider error signal (rate-limit/quota/auth text on stderr from the
> codex/kiro CLIs) is destroyed. Prerequisite for the quota-resilience initiative
> (`.planning/specs/quota-resilience/REQUIREMENT.md`), whose scope is explicitly EXCLUDED here.
> Run: essential mode, version-up on self, fork point master `d765e93`. Operator ordered an
> explicit overcomplication check before acceptance; all four resolutions survived it.

### D1 — runner contract: hard 4-tuple, streams kept separate · LOCKED
- **Question:** widen the injectable runner contract to carry stderr, or merge streams
  (`stderr=STDOUT`) and keep the 3-tuple?
- **Provenance:** contract at `dispatch()` docstring (`kata_dispatch.py:180`); six in-repo stub
  runners at `tools/tests/test_kata_dispatch.py:124-208`; no external callers of the seam.
- **Decision:** **Hard 4-tuple `(exit_code, stdout, stderr, result_text)`.** Merging streams is
  the FALSE simplification: it would pollute `raw` on successful runs too (breaking the
  byte-unchanged success envelope, AC#4) and destroy stream provenance the future quota
  classifier needs. No dual-shape tolerance for legacy 3-tuples — silently accepting them would
  mask a stub that never carries stderr (D136 fail-closed spirit). All stubs updated in the same
  commit.
- **Edges:** injected runners that raise (e.g. `TimeoutExpired`) are unaffected — the contract
  change is return-shape only.

### D2 — stderr cap: deterministic tail, dispatch-side choke point · LOCKED
- **Question:** cap the carried stderr, and if so where?
- **Provenance:** RESULT envelopes land in durable records/ledgers; a crashing worker can dump
  megabytes; provider error text arrives at the END of stderr.
- **Decision:** **Deterministic tail cap — last 4,000 chars — applied in `dispatch()` via one
  `_stderr_tail()` helper, with a literal truncation marker prepended when clipped.** Capping at
  the dispatch side (not per-runner) makes one choke point injected stubs cannot bypass. Pure
  function of input — Determinism Doctrine compliant; boundary-tested.
- **Edges:** empty stderr ⇒ no key added (envelope stays minimal); exactly-4000 ⇒ no marker.

### D3 — where stderr rides: three failure paths; success byte-unchanged · LOCKED
- **Question:** does stderr ride failure envelopes only, or all envelopes?
- **Provenance:** `dispatch()` failure paths at `kata_dispatch.py:197-198` (timeout),
  `:200-204` (exit≠0), `:205-211` (unparseable result); `build_result` at `:216-223`.
- **Decision:** **Failure paths only, all three of them:** exit≠0 payload gains
  `"stderr": <tail>` alongside `"error"`; the timeout envelope carries captured-so-far stderr
  from `TimeoutExpired.stderr` (decode-if-bytes — the attribute is bytes on some platforms;
  test-pinned); the unparseable-result envelope (exit 0, garbage result file) carries it too —
  stderr may explain why. **The `completed` envelope is byte-unchanged** and `build_result`'s
  signature is untouched — stderr lives inside the payload dict.
- **Edges:** `raw` keeps its stdout-only semantics everywhere; injected stubs raising
  `TimeoutExpired` without `.stderr` ⇒ no key, never a crash.

### D4 — sibling kata_preflight runner: cross-ref hygiene now, widening DEFERRED · LOCKED
- **Question:** `kata_preflight._default_runner` (`kata_preflight.py:397-407`) has the same
  stderr-discard and its docstring cross-references `kata_dispatch.py:168-173` — lines this fix
  shifts. Fix it too?
- **Provenance:** grill-time grounding sweep (grep over `tools/` for runner seams).
- **Decision:** **Update the stale line-number cross-reference (mandatory hygiene, in-scope);
  DEFER the preflight stderr widening to the quota-resilience run** — that classifier decides
  what it consumes; widening preflight now is scope creep on a surgical fix. Recorded in
  `.planning/DEFERRED.md` (kata-defer path, operator-visible).
- **Edges:** none — behavior of preflight is untouched this run.

### Convergence pass · PASS
One refinement folded during convergence: the cap moved from runner-side to dispatch-side
(D2) so all runners — real and injected — pass one deterministic choke point. No contradictions
between D1–D4; the change is fully determined. Operator's explicit overcomplication audit:
merged-stream alternative rejected as false simplification (D1); cap is ~3 lines (D2);
timeout/unparseable legs are ~1-2 lines each (D3); deferral is the anti-overcomplication move
itself (D4).
