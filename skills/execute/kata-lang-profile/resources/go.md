# Go profile — debug-mode overlay

A prose lens over `[[kata-tdd]]` (debug fix-loop) and `[[kata-diagnose]]` (diagnosis) for `.go` codebases.
Guidance only — it relaxes no gate. Detect the module layout (`go.mod`) and existing test style before
assuming conventions below.

## Idioms that matter when fixing without drift
- **Explicit error handling** — `if err != nil` is the contract. A fix that swallows, wraps differently
  (`fmt.Errorf("...: %w", err)` vs not), or changes the returned error changes caller behavior. Preserve
  error identity that callers check with `errors.Is` / `errors.As`.
- **Zero values** are meaningful — a `nil` map vs an empty map, a `nil` slice vs `[]T{}`, behave differently.
  Don't "tidy" one into the other.
- **`nil` interface gotcha** — a non-nil interface holding a nil pointer is `!= nil`. Classic bug source;
  preserve the exact return.
- **Value vs pointer receivers** and **slice aliasing** — slices share backing arrays; `append` may or may
  not mutate the caller's slice. A fix here is high-drift-risk.
- **`defer` ordering** and named-return interactions; goroutine/channel semantics.

## Test-runner conventions
- The standard toolchain: `go test`. Run focused: `go test ./pkg -run '^TestName$' -v`. Use `-run` regexes
  to scope. `-race` is a cheap, high-value objective signal — run it on the loop when concurrency is in play.
- `go vet` and a linter (`golangci-lint`) are objective signals distinct from tests; `go build ./...` catches
  compile breakage fast.
- For the **characterization suite**, use **table-driven tests** (the idiomatic `tests := []struct{...}`
  pattern) to pin many input→output cases; `testing.T` subtests (`t.Run`) for isolation. Golden-file testing
  (`-update` flag pattern) pins large outputs; `go-cmp` (`cmp.Diff`) for readable struct comparisons.

## Common failure modes (diagnosis hooks)
- **Data races** — caught by `go test -race`; the single most useful Go debugging flag.
- **Goroutine leaks / deadlocks** — blocked on a channel send/receive; unbuffered-channel misuse;
  forgotten `wg.Done()`.
- **`context` misuse** — cancellation/timeout not propagated; ignoring `ctx.Err()`.
- **Map iteration order is randomized** — code that relied on order is buggy and flaky.
- **Integer overflow / unsigned wraparound**; time/duration unit mistakes.
- **Error wrapping chains** — a fix that breaks `errors.Is` matching.

## Diagnosis loop (feedback-first)
A focused `go test -run -race` is the fastest signal. Use **delve** (`dlv test`, `dlv debug`) for stepping;
`runtime/pprof` and `go test -cpuprofile/-memprofile` for performance; `GODEBUG` knobs (e.g.
`GODEBUG=gctrace=1`) for runtime behavior; the race detector and `-count=1` (disable cache) to reproduce
flakiness deterministically.

## Characterization / drift hints
- Scrub timestamps, randomized map ordering (sort keys), and pointer addresses before snapshotting.
- Pin the **exported** contract (return values incl. the exact error, mutations of passed slices/maps) —
  not unexported internals — so a body-only fix keeps the suite green.
