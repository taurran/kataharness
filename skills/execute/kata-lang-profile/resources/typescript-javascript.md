# TypeScript / JavaScript profile — debug-mode overlay

A prose lens over `[[kata-tdd]]` (debug fix-loop) and `[[kata-diagnose]]` (diagnosis) for
`.ts` / `.tsx` / `.js` / `.jsx` / `.mjs` / `.cjs` codebases. Guidance only — it relaxes no gate. Detect the
runner, module system (ESM vs CJS), and whether types are checked before assuming conventions below.

## Idioms that matter when fixing without drift
- **`==` vs `===`** — coercion bugs are endemic. A fix that changes equality strictness is a behavioral
  change. Same for truthiness (`0`, `""`, `NaN`, `null`, `undefined` all falsy).
- **`null` vs `undefined`** are distinct; optional chaining (`?.`) and nullish coalescing (`??`) differ from
  `||`. Preserve the exact null-handling a caller relies on.
- **Reference vs value** — objects/arrays are shared; a fix that mutates an argument in place changes caller
  behavior. Spread/clone deliberately.
- TypeScript types are **erased at runtime** — they do not enforce anything at the boundary. Untyped JSON,
  `any`, and `as` casts let wrong shapes flow through. Pin runtime behavior, not just the type.
- **Async** — a forgotten `await`, an unhandled promise rejection, or floating promises change ordering and
  error propagation. `Promise.all` vs sequential `await` differ in failure semantics.

## Test-runner conventions
- Detect the runner: **Vitest**, **Jest**, **Mocha**, **node:test**, or framework runners (e.g. Playwright,
  `@testing-library`). Check `package.json` `scripts.test`, config files (`vitest.config`, `jest.config`),
  and the package manager (`npm` / `pnpm` / `yarn` / `bun`).
- Run through the project's package manager so the right toolchain is used: `npm test`, `pnpm test`,
  `yarn test`, or `npx vitest run path -t "name"`. Use the runner's focus flag (`-t`/`--testNamePattern`,
  `.only`) for a tight loop, but never commit a stray `.only`.
- For TS, a separate **typecheck** pass (`tsc --noEmit`) is a cheap objective signal distinct from tests.
- For the **characterization suite**, snapshot testing (`toMatchSnapshot` / `toMatchInlineSnapshot`) pins
  complex output well; `it.each` / `test.each` parametrizes input→output pairs.

## Common failure modes (diagnosis hooks)
- **`this` binding** — lost in callbacks, differs between arrow and function expressions.
- **Floating-point** (`0.1 + 0.2`), and `Number` vs `BigInt`.
- **Event-loop ordering** — microtasks (promises) vs macrotasks (`setTimeout`); race conditions.
- **Module-system mismatch** — ESM/CJS interop (`require` vs `import`, default-export shape, `__dirname`
  absent in ESM); `package.json` `"type"` and `exports` map.
- **Mutable shared state** across imported singletons.
- **Date/timezone** handling; locale-sensitive string ops; `JSON.stringify` dropping `undefined`/functions.
- **Bundler/transpile** differences — behavior under the dev server vs the production build.

## Diagnosis loop (feedback-first)
A focused failing test is the fastest signal. Use `node --inspect` / the runner's `--inspect-brk` with
DevTools, `debugger` statements, source maps for stack traces, and `console.dir(x, { depth: null })` for
deep inspection. For browser/DOM bugs, a headless run (Playwright) gives a deterministic loop. Pin
`Date.now` / `Math.random` (fake timers, seeded RNG) before snapshotting nondeterministic output.

## Characterization / drift hints
- Scrub timestamps, generated ids, and unstable key ordering before snapshotting.
- Pin the **exported** contract (return shape, thrown errors, mutations of passed objects) — not internal
  helper structure — so the suite survives a body-only fix.
