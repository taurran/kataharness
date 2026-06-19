# Project 1 — `wordfreq` CLI

## SPEC (given identically to both arms)
Build a Python command-line tool **`wordfreq`** that reads a UTF-8 text file and prints the most frequent words.

- **Usage:** `wordfreq <file> [--top N] [--min-length L] [--ignore-case]`
- **Output:** up to N lines, each `word<TAB>count`, sorted by **count descending, then word ascending**.
- **Defaults:** `--top 10`, `--min-length 1`, `--ignore-case` off.
- **Word definition:** maximal runs of `[A-Za-z0-9']`; everything else is a separator.
- **`--ignore-case`:** fold to lowercase before counting.
- **`--min-length L`:** ignore words shorter than L characters (after case-folding).
- **Errors:** missing/unreadable file → message on **stderr**, exit code **1**. Success → exit **0**.
- **Packaging:** runnable as `python -m wordfreq` (a `wordfreq/` package). Keep it small (≈3–6 files).
- **Quality:** ships with a `pytest` suite covering the behavior; passes `ruff check .` clean.

## GATE (experimenter acceptance — held out from the arms)
Run in the arm's output dir: **`pytest -q`** (the held-out suite below) **and** **`ruff check .`** → both must
pass on the first delivered build for **first-pass-green**.

Enumerated acceptance cases (the held-out suite encodes exactly these):
1. Input `"the cat sat on the mat the cat"` → top line `the\t3`, then `cat\t2`, then `mat/on/sat\t1` in
   **ascending word order** for ties.
2. `--top 2` on the same input → exactly 2 lines (`the\t3`, `cat\t2`).
3. `--ignore-case` with `"The the THE"` → `the\t3` (single bucket).
4. Without `--ignore-case`, `"The the"` → two buckets `The\t1`, `the\t1` (tie → `The` before `the`, ASCII order).
5. `--min-length 3` with `"a an ant"` → only `ant\t1` (a, an filtered).
6. Tokenisation: `"don't stop—now"` → words `don't`, `stop`, `now` (apostrophe kept, em-dash splits).
7. Missing file → nonzero exit (1) and a message on stderr; nothing on stdout.
8. Empty file → no output lines, exit 0.

Lint: `ruff check .` reports 0 findings.
