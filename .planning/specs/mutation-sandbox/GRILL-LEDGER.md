# GRILL-LEDGER — mutation-sandbox (light tier, 2026-07-21, rolling runway)

> Subject: the D1 phantom-corruption fix. `tools/mutation_run.py:169` (pre-fix) writes mutated
> bytes to the REAL source file and restores at `:174` in `finally` — concurrent readers see
> corruption in the write→restore window; a hard kill persists the mutation on disk (the
> recurring IndentationError hauntings; root-caused 2026-07-14, D1). The vector fires on EVERY
> gauntlet: `test_benchmark.py::TestMutationProof` runs five REAL mutation proofs inside
> pytest-unit. The fix SHAPE was frozen in the operator-accepted execution plan (item D:
> "mutate a sandboxed copy — temp tree + path-redirected pytest invocation — never the live
> file"); this light grill resolved the five implementation branches inline under the
> operator's rolling runway (option 2, merge-on-green; stop only for escalations).

### D1 — copy scope: marker-derived project root, fail-closed; hygiene excludes · LOCKED
- **Question:** what gets copied into the sandbox, and how is the tree root found?
- **Provenance:** live callers embed `cd /d "<tools>"` + run named tests — the copy must carry
  the whole runnable project (source + tests + pyproject), not just the source file. `tools/`
  is ~3.5 MB minus `.venv`/caches (measured).
- **Decision:** **Copy the PROJECT ROOT: the first ancestor of the source file containing
  `pyproject.toml` or `.git`; no marker ⇒ RAISE (D136 — never guess a copy scope). An explicit
  `project_root=` parameter overrides derivation (same `..`-guard + the source must live under
  it). Excludes: `.git`, `.venv`, `.kata`, `__pycache__`, `.pytest_cache`, `.ruff_cache`,
  `node_modules`.** Per-call sandbox (prove_many shares nothing) — ~3.5 MB per proof is cheap;
  batch-sharing is premature optimization.
- **Edges:** unit tests using bare tmp_path sources now drop a `pyproject.toml` marker or pass
  `project_root` explicitly.

### D2 — runner contract widened to (cmd, cwd) · LOCKED
- **Question:** how do RELATIVE test_cmds (`cd tools && …`) reach the sandbox?
- **Provenance:** `_default_runner` (pre-fix) ran with inherited cwd; the injectable contract
  was `(cmd) -> bool`.
- **Decision:** **Hard contract widening to `(cmd, cwd) -> bool`** — the item-A precedent: no
  dual-shape tolerance; all in-repo stubs updated in the same commit. The real runner passes
  `cwd` to `subprocess.run`; relative cmds thereby execute inside the sandbox.
- **Edges:** injected stubs receive the sandbox root — which is itself a pin surface (tests
  observe the sandboxed copy through it).

### D3 — baseline AND mutated both run in the sandbox · LOCKED
- **Question:** does the baseline run stay on the live tree?
- **Provenance:** Determinism Doctrine law 8 — a gate comparison must differ ONLY by the
  mutation; splitting baseline (live) and mutated (sandbox) across trees would add a second
  variable (tree identity) to the Axis-Q boolean.
- **Decision:** **Both runs execute against the sandbox** — baseline on the pristine copy,
  mutated after the copy's source is rewritten. The live tree is read once (original bytes)
  and never written.
- **Edges:** the old restore-in-finally disappears; `finally` now removes the sandbox
  (`ignore_errors=True` — a leaked temp dir on a hard kill is harmless, unlike a mutated
  live file).

### D4 — redirect mechanics: literal root substitution + .venv lookahead · LOCKED
- **Question:** how do ABSOLUTE root references inside test_cmd reach the sandbox without
  breaking the interpreter path?
- **Provenance:** live caller cmd shape: `cd /d "<tools>" && <sys.executable> -m pytest …`
  where `sys.executable` = `<tools>\.venv\Scripts\python.exe` — a READ-ONLY reference into the
  live venv that MUST survive (the sandbox excludes `.venv`; uv would otherwise re-sync a
  fresh env per proof).
- **Decision:** **Substitute every literal occurrence of the resolved project root (both
  `str()` and `as_posix()` flavors) EXCEPT occurrences followed by `[\\/].venv` (negative
  lookahead).** Deterministic pure string transform of (cmd, root, sandbox).
- **Edges:** the venv python running with cwd=sandbox imports the SANDBOX module (sys.path[0]
  = cwd under `-m pytest`); an editable-install .pth cannot shadow it (cwd wins).

### D5 — residual live-root guard, Windows case-insensitive · LOCKED
- **Question:** what if a case-mismatched root reference survives substitution (Windows paths
  are case-insensitive; a `c:\dev\…` spelling would silently run the mutation against the
  LIVE tree — the exact corruption class this run kills)?
- **Provenance:** the D157 guard precedent — a guard that raises beats a silent wrong-target
  run (D136).
- **Decision:** **After substitution, scan the redirected cmd for any remaining slash-agnostic,
  case-insensitive (`os.name == "nt"` only) occurrence of the project root not followed by
  `.venv` — found ⇒ RAISE.** On POSIX the check is case-sensitive (a case-different path is a
  genuinely different path there; a case-folded check would false-positive).
- **Edges:** platform-conditional strictness is environmental honesty, documented in the
  docstring — the guard's OUTPUT is still deterministic per platform.

### ADDENDUM — adval folds (2026-07-21, fresh-context review SHIP-WITH-FIXES; supersede-don't-edit)
- **F1 (MEDIUM, confirmed) → folded:** D4's substitution pattern lacked a RIGHT boundary — a
  root that PREFIXES a sibling path (`C:\proj` vs `C:\proj2`, `<root>-backup`) was rewritten,
  and a case-mismatched sibling false-positived the D5 guard. The realized pattern now ends at
  `(?![A-Za-z0-9._~-])`. D4/D5 decisions STAND; this tightens their realization. Pinned.
- **F2 (LOW, confirmed) → folded:** the `.venv` lookahead now matches only a TRUE `.venv`
  component (`[\\/]+\.venv` + name-boundary): `<root>\.venv-old` substitutes loudly (it was the
  one silent live-reference escape), doubled separators still preserve. Pinned.
- **F3 (worker-facing doc drift) → folded:** `kata-tdd` SKILL taught the superseded mutate-live/
  restore design; prose + example updated to the sandbox contract with the interpreter-path
  cost note (0.4.0→0.4.1).
- **F4 (PD-2 count) → folded:** the preamble's "five/seven" understated blast radius — the whole
  fleet is ~60 real `prove_non_vacuous` call sites across 14 test modules, all sandbox-routed,
  all green. The error was in the safe direction; corrected in the CHANGELOG.
- **F5 (guard limits, theoretical) → documented:** alternate root SPELLINGS (8.3 short names,
  symlinks, UNC forms) are invisible to a literal pattern; accepted at test_cmd operator trust
  (commands are machine-built from resolved paths). Stated in `_root_pattern`'s docstring; D5's
  "any remaining occurrence" reads as any remaining LITERAL occurrence.

### Convergence pass · PASS
D1–D5 cohere: one sandbox per proof (D1) is what D3's both-runs-inside and D2's cwd landing
target; D4's lookahead is what makes D1's `.venv` exclusion viable; D5 closes the only silent
escape from D4. Overcomplication audit (standing, per the operator's item-A directive): the
alternative "atomic write + crash-safe restore" was REJECTED — it narrows but does not close
the concurrent-reader window and leaves the hard-kill persistence class open; the sandbox is
the minimal design that actually kills both.
