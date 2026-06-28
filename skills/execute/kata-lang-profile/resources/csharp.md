# C# / .NET profile — debug-mode overlay

A prose lens over `[[kata-tdd]]` (debug fix-loop) and `[[kata-diagnose]]` (diagnosis) for `.cs` codebases.
Guidance only — it relaxes no gate. Detect the target framework, solution/project layout, and test
framework before assuming conventions below.

## Idioms that matter when fixing without drift
- **Value vs reference types** — `struct` (value, copied) vs `class` (reference, shared). A fix that changes
  one to the other, or mutates a `struct` returned by a property, silently changes behavior.
- **Nullable reference types** (`?`, `!`, `#nullable`) are compile-time hints, not runtime guarantees.
  Preserve the actual null-handling; a `NullReferenceException` fix must not change the documented contract.
- **`==` overloading and `Equals`/`GetHashCode`** — reference equality vs value equality differs by type
  (and `record` types generate value equality). Don't swap them in a fix.
- **`async`/`await`** — `async void` (fire-and-forget, unobservable exceptions), missing `await`,
  `.Result`/`.Wait()` deadlocks on a sync context, and `ConfigureAwait(false)` semantics. High-drift area.
- **LINQ deferred execution** — a query is re-evaluated each enumeration; materializing (`.ToList()`) vs not
  changes side-effect timing and exception points.

## Test-runner conventions
- Detect the framework: **xUnit**, **NUnit**, or **MSTest** (check the `.csproj` `<PackageReference>` and
  test attributes — `[Fact]`/`[Theory]`, `[Test]`, `[TestMethod]`). **Moq**/**NSubstitute** for mocks,
  **FluentAssertions** for assertions.
- Run focused via the CLI: `dotnet test --filter "FullyQualifiedName~Namespace.Class.Method"`. Build first
  with `dotnet build` for a fast compile signal.
- For the **characterization suite**, xUnit `[Theory]` with `[InlineData]`/`[MemberData]` pins many cases;
  FluentAssertions' `BeEquivalentTo` pins object graphs; Verify (snapshot library) pins large outputs.

## Common failure modes (diagnosis hooks)
- **Async deadlocks** — blocking on async in a UI/ASP.NET sync context (`.Result`).
- **Disposal** — missing `using`/`Dispose`, `IDisposable` leaks; `IAsyncDisposable`.
- **Floating-point** vs `decimal` (money); `DateTime` vs `DateTimeOffset`, `Kind`/timezone bugs.
- **Boxing** of value types; mutable struct surprises in collections.
- **Culture-sensitive** string/number formatting (`CultureInfo.InvariantCulture` vs current culture).
- **Concurrency** — non-thread-safe collections; `ConfigureAwait` and context capture.
- **Reflection / serialization** mapping drift (System.Text.Json vs Newtonsoft behavior differences).

## Diagnosis loop (feedback-first)
A focused `dotnet test --filter` is the fastest signal. Use the debugger (`dotnet` + VS/VS Code/Rider,
conditional breakpoints, exception settings to break on throw), structured logging, and `dotnet-trace` /
`dotnet-dump` / `dotnet-counters` for performance and hangs. Enable first-chance-exception breaking to find
swallowed exceptions.

## Characterization / drift hints
- Scrub timestamps, GUIDs, and culture-dependent formatting before snapshotting; pin `InvariantCulture`.
- Pin the **public** contract (return values, thrown exception types, mutations of arguments) — not private
  fields — so a body-only fix keeps the suite green.
