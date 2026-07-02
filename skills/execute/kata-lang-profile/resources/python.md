# Python profile — debug-mode overlay

A prose lens over `[[kata-tdd]]` (debug fix-loop) and `[[kata-diagnose]]` (diagnosis) for `.py` codebases.
Guidance only — it relaxes no gate. Detect the real test runner and project layout before assuming any of
the conventions below.

## Idioms that matter when fixing without drift
- Prefer the **smallest behavior-preserving edit**. Python's dynamism makes accidental drift easy: a changed
  default argument, a mutable default (`def f(x=[])`), or a reordered `**kwargs` merge silently changes
  behavior for callers you did not test.
- Respect **duck typing** at boundaries — a function may be called with more types than the annotations
  claim. Pin the *actual* observed types in characterization tests, not just the annotated ones.
- Watch **truthiness traps** (`0`, `""`, `[]`, `None` all falsy) and `is` vs `==` (identity vs equality,
  esp. for small-int / string interning). A fix that swaps one for the other is a classic regression.
- Exceptions are control flow: changing which exception type is raised (or swallowing one) is a behavioral
  change even if the happy path is identical.

## Test-runner conventions
- Default to **pytest**; fall back to `unittest` if that is what the repo uses. Detect via `pytest.ini`,
  `pyproject.toml` (`[tool.pytest.ini_options]`), `setup.cfg`, `tox.ini`, or existing `test_*.py` style.
- Run a focused node first: `pytest path/to/test_x.py::test_name -x -q`. Use `-x` to stop at first failure
  and `-q` for a fast loop. `-k` selects by expression.
- For the **characterization suite**, lean on `pytest` fixtures and **parametrize** to pin many input→output
  pairs cheaply. `pytest.approx` for floats. Snapshot libraries (`syrupy`) pin complex outputs.
- If the project uses `uv` / `poetry` / `hatch`, run tests through it (`uv run pytest`, `poetry run pytest`)
  so the right virtualenv and dependency set are used.

## Common failure modes (diagnosis hooks)
- **Import-time side effects** — module-level code that runs on import; ordering bugs surface only under a
  specific import sequence. Bisect by import order.
- **Mutable default arguments** and **shared class attributes** — state leaks across calls/instances.
- **Late binding in closures / comprehensions** (loop variable captured by reference).
- **`asyncio`** — unawaited coroutines, blocking calls inside the event loop, mixing sync and async I/O.
- **Floating-point and `Decimal`** mismatches; integer division (`/` vs `//`).
- **Encoding** — implicit `str`/`bytes` boundaries, default file encodings across platforms.
- **C-extension / native deps** (numpy, pandas, lxml) — behavior can hinge on the installed binary wheel.

## Diagnosis loop (feedback-first)
A failing `pytest -x` is the fastest pass/fail signal — build it before reading code. Reach for `pdb` /
`breakpoint()`, `python -X dev` (dev-mode warnings), `faulthandler` for hangs, and `pytest --pdb` to drop
into the debugger on failure. `python -m trace` or `sys.settrace` for execution paths. For nondeterminism,
fix the seed (`random.seed`, `PYTHONHASHSEED=0`) and pin the clock before snapshotting.

## Characterization / drift hints
- Scrub nondeterminism (timestamps, `repr` addresses, dict ordering pre-3.7 assumptions, set ordering,
  `uuid`) before snapshotting so the drift gate compares behavior, not noise.
- Pin the **public** contract (return values, raised exceptions, side effects on passed-in mutables), not
  private helper internals — that keeps the suite stable across a body-only fix.

## Greenfield src-layout seeding (BUILD context — F4; not debug)

Satisfies the orchestrator's generic **"the project's own package is importable before wave-1 dispatch"**
precondition for a new Python project. Skips the Kenjiri failure where `uv init --bare` wrote no
`[build-system]`, the package was not importable, and three workers independently added `sys.path` shims
to their test files before it was root-caused.

Before dispatching wave-1 on a greenfield Python **src-layout** project, the orchestrator (or the seeding
step it owns) ensures:
1. `uv init` (**not `--bare`** — bare omits the build backend), or otherwise author `pyproject.toml`.
2. A **`[build-system]`** table is present (e.g. `requires = ["setuptools>=61"]`,
   `build-backend = "setuptools.build_meta"`).
3. For src-layout, **`[tool.setuptools.packages.find]` with `where = ["src"]`** so the package under
   `src/<pkg>/` is discoverable.
4. **Verify importability**: `uv run python -c "import <pkg>"` exits 0 **before** any worker is dispatched.
   A non-zero exit is a seeding failure → fix the packaging at the orchestrator/root layer, never by a
   per-worker `sys.path` shim (that is cross-lane drift and masks the real gap).

Flat-layout projects (package at repo root) need only steps 1–2 + the import verify. Non-`uv` toolchains
(`poetry`, `hatch`) supply their own build backend — the invariant is the same: **the package imports
cleanly before wave-1**, however the toolchain gets there.
