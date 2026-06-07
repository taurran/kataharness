# FEEDBACK-LOOPS.md — ways to build the Phase-1 diagnosis signal

Loaded on demand by [[kata-diagnose]] Phase 1 (progressive disclosure — kept out of the skill body to keep
the loop context lean). "Build the right feedback loop and the bug is 90% fixed."

## Construct one — try in roughly this order
1. **Failing test** at whatever seam reaches the bug (unit / integration / e2e).
2. **Curl / HTTP script** against a running dev server.
3. **CLI invocation** with a fixture input, diffing stdout vs a known-good snapshot.
4. **Headless browser** (Playwright/Puppeteer) — drives UI, asserts DOM/console/network.
5. **Replay a captured trace** — save a real request/payload/event log, replay through the path in isolation.
6. **Throwaway harness** — minimal subset (one module, mocked deps) exercising the bug path in one call.
7. **Property / fuzz loop** — for "sometimes wrong output", run 1000 random inputs, look for the failure mode.
8. **Bisection harness** — if it appeared between two known states, automate "boot at X, check, repeat" for `git bisect run`.
9. **Differential loop** — same input through old vs new (or two configs), diff outputs.
10. **HITL script** — last resort; if a human must click, drive them with a structured loop so output still feeds back.

## Iterate on the loop itself (treat it as a product)
- Faster: cache setup, skip unrelated init, narrow scope.
- Sharper: assert the specific symptom, not "didn't crash".
- More deterministic: pin time, seed RNG, isolate FS, freeze network. A 2-second deterministic loop beats a
  30-second flaky one.

## Non-deterministic bugs
Goal is a higher reproduction *rate*, not a clean repro. Loop the trigger 100×, parallelise, add stress,
narrow timing windows, inject sleeps. 50%-flake is debuggable; 1% is not — raise the rate until it is.
