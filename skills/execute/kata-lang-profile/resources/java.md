# Java profile — debug-mode overlay

A prose lens over `[[kata-tdd]]` (debug fix-loop) and `[[kata-diagnose]]` (diagnosis) for `.java` codebases.
Guidance only — it relaxes no gate. Detect the build tool (Maven vs Gradle) and the test framework before
assuming the conventions below.

## Idioms that matter when fixing without drift
- **`equals` / `hashCode` contract** — changing one without the other silently breaks `HashMap`/`HashSet`
  membership for existing callers. A fix touching either is high-drift-risk.
- **`null` handling and `NullPointerException`** — preserve the exact nullability a caller depends on;
  prefer `Optional` only where the codebase already does.
- **Autoboxing** — `Integer` caching (`-128..127`) makes `==` on boxed values deceptive; use `.equals`.
  A fix that swaps `==`/`equals` on boxed types is a behavioral change.
- **Checked vs unchecked exceptions** — changing the thrown type, or wrapping/unwrapping, alters the
  caller's contract. Preserve the declared `throws`.
- **Mutability and visibility** — `final`, defensive copies, and the Java Memory Model (a missing
  `volatile`/`synchronized` is a real concurrency bug, not style).

## Test-runner conventions
- Detect **Maven** (`pom.xml`) vs **Gradle** (`build.gradle[.kts]`). Test framework is usually **JUnit 5**
  (Jupiter), sometimes JUnit 4 or TestNG; **Mockito** for mocks, **AssertJ**/**Hamcrest** for assertions.
- Run a focused test fast:
  - Maven: `mvn -q -Dtest=ClassName#method test`
  - Gradle: `./gradlew test --tests 'pkg.ClassName.method'`
- Honor the wrapper (`./mvnw` / `./gradlew`) if present, so the pinned toolchain version is used.
- For the **characterization suite**, JUnit 5 `@ParameterizedTest` (with `@CsvSource` / `@MethodSource`)
  pins many input→output pairs; AssertJ's recursive comparison pins object graphs; approval-testing
  libraries pin large outputs.

## Common failure modes (diagnosis hooks)
- **Concurrency** — visibility/ordering bugs under the JMM; non-thread-safe collections shared across
  threads; `SimpleDateFormat` not being thread-safe.
- **Floating-point** vs `BigDecimal` (money), and integer overflow.
- **Classpath / version skew** — the wrong transitive dependency version on the classpath; shading issues.
- **Resource leaks** — unclosed streams/connections (use try-with-resources); these surface as flakiness.
- **Serialization** — `serialVersionUID` drift, Jackson/Gson field-mapping changes.
- **Locale / timezone / charset** defaults differing across environments.

## Diagnosis loop (feedback-first)
A focused failing JUnit test is the fastest signal. Use the JVM debugger (JDWP, `--debug-jvm` on Gradle,
`mvnDebug`), conditional breakpoints, and remote-attach for server processes. Read full stack traces
including `Caused by:` chains. `jstack` for hangs/deadlocks, `jmap`/heap dumps for leaks, JFR for
performance. Enable assertions (`-ea`) when running.

## Characterization / drift hints
- Scrub timestamps, identity hash codes (`Object.toString` default), and unstable map/set ordering before
  snapshotting; sort or use ordered collections.
- Pin the **public/API** contract (return values, thrown exceptions incl. type, mutations of arguments) —
  not private fields — so a body-only fix keeps the suite green.
