# Rust profile — debug-mode overlay

A prose lens over `[[kata-tdd]]` (debug fix-loop) and `[[kata-diagnose]]` (diagnosis) for `.rs` codebases.
Guidance only — it relaxes no gate. Detect the crate/workspace layout (`Cargo.toml`) and test style before
assuming conventions below.

## Idioms that matter when fixing without drift
- **Ownership / borrowing** — the compiler enforces a lot, but a fix that clones to "make it compile" can
  change behavior (a deep copy where the caller expected shared mutation, or vice versa). Prefer the minimal
  borrow change.
- **`Result` / `Option` and the `?` operator** — error propagation is explicit. A fix that swaps `?` for
  `.unwrap()`/`.expect()` turns a recoverable error into a panic — a behavioral change and a regression risk.
  Preserve the returned error type (and any `From` conversions callers rely on).
- **`panic!` vs returned error** — changing which one a function does changes the caller contract.
- **Integer overflow** — panics in debug builds, wraps in release builds. A fix must account for both; use
  `checked_`/`wrapping_`/`saturating_` deliberately, matching existing intent.
- **Trait coherence and `impl` selection** — changing a trait bound or a generic can silently pick a
  different impl. **Iterators are lazy** — `map`/`filter` do nothing until consumed (`collect`, `for`).

## Test-runner conventions
- The standard toolchain: `cargo test`. Run focused: `cargo test test_name -- --nocapture` (substring
  match on the test name; `--nocapture` shows `println!`). `cargo test --doc` runs doctests.
- `cargo check` is the fastest compile signal; `cargo clippy` is a high-value objective lint signal;
  `cargo build` for the full compile.
- For the **characterization suite**, use `#[test]` functions with table-style `Vec` of cases; `assert_eq!`
  / `assert!`; the **insta** crate for snapshot testing of complex outputs; `proptest`/`quickcheck` for
  property tests that pin invariants.

## Common failure modes (diagnosis hooks)
- **`unwrap`/`expect` panics** and **index-out-of-bounds** — the most common runtime failures.
- **Integer overflow** behavior differing between debug and release profiles.
- **`unsafe` blocks** — undefined behavior, aliasing violations; run under **Miri** (`cargo +nightly miri
  test`) to catch UB, and **ASan/TSan** for memory/thread issues.
- **Concurrency** — `Arc`/`Mutex` poisoning, deadlocks, `Send`/`Sync` boundary mistakes.
- **Float vs integer** and unit/precision mistakes; `as` casts that truncate.
- **Lifetime/borrow "fixes"** that change sharing semantics.

## Diagnosis loop (feedback-first)
A focused `cargo test name -- --nocapture` is the fastest signal. Set `RUST_BACKTRACE=1` (or `full`) for
panic backtraces. Use `dbg!(x)` for quick inspection, `rust-gdb`/`rust-lldb` for stepping, `cargo clippy`
to surface logic smells, and **Miri** for UB in `unsafe` code. Reproduce overflow bugs by testing the
release profile (`cargo test --release`) too when behavior diverges.

## Characterization / drift hints
- Scrub timestamps, addresses (`{:p}`), and `HashMap` ordering (use `BTreeMap` or sort) before snapshotting.
- Pin the **public** contract (return values incl. the exact `Result`/error variant, panics, mutations of
  `&mut` args) — not private internals — so a body-only fix keeps the suite green.
