# Project 1 — `wordfreq` CLI  (v2, hardened post-pilot)

## SPEC (given identically to both arms)
Build a Python CLI **`wordfreq`** (runnable as `python -m wordfreq`) that reads a UTF-8 text file and prints
word frequencies. The rules **interact — order of operations matters.**

- **Usage:** `wordfreq <file> [--top N] [--min-length L] [--ignore-case] [--stopwords FILE]`
- **Tokenize:** a word is a maximal run of Unicode alphanumerics plus the ASCII apostrophe `'`, with **leading
  and trailing apostrophes stripped** (`'tis'`→`tis`, `don't`→`don't`, a bare `''` yields nothing). Everything
  else separates.
- **Pipeline (apply in this exact order):** tokenize → (if `--ignore-case`: fold each token with
  `str.casefold()`) → **stopword removal** → **min-length filter** → count.
  - `--stopwords FILE`: one stopword per line; a token is removed if it **equals** a stopword. If
    `--ignore-case`, fold **both** token and stopword before comparing. (So stopwords are matched *after*
    folding, *before* min-length.)
  - `--min-length L` (default 1): drop tokens with fewer than L characters, measured **after** folding.
- **Ordering / output:** sort by **count descending, then word ascending (Unicode code-point order)**. Lines
  are `word<TAB>count`, `\n`-terminated, with a trailing newline. Empty result → no lines, exit 0.
- **`--top N` (default 10):** output the top N words — **but if the Nth and (N+1)th words share the same
  count, include the entire tied group** (output may exceed N; never split a count-group at the boundary).
- **Errors:** unreadable input file *or* unreadable `--stopwords` file → message on stderr, exit 1. Success exit 0.
- Keep it small (≈4–7 files). Ship a `pytest` suite; pass `ruff check .` clean.

## GATE (held out from the arms) — `pytest -q` ∧ `ruff check .`
1. `"the cat sat on the mat the cat"` → `the\t3`, `cat\t2`, then `mat\t1`,`on\t1`,`sat\t1` (ties ascending).
2. Apostrophe edges: `"'tis 'tis don't ''"` → `don't\t1`, `tis\t2` ordered `tis` then `don't`? No — count desc:
   `tis\t2`, `don't\t1` (the bare `''` contributes nothing).
3. `--ignore-case` casefold: `"groß GROSS"` → `gross\t2` (Python `casefold()` maps ß→ss).
4. Stopwords, case-sensitive: input `"the cat the dog"`, stopwords=`the` → `cat\t1`, `dog\t1`.
5. Stopwords + `--ignore-case`: input `"The the"`, stopwords=`the` → empty output (both fold to `the`, removed).
6. Order-of-ops: input `"a an the ant"`, stopwords=`the`, `--min-length 3` → only `ant\t1` (a/an dropped by
   length, the by stopword).
7. Top-N tie-group: input where words rank `5,3,3,3,1` by count with `--top 2` → output the count-5 word **and
   all three count-3 words** (4 lines), never 2 that split the tie group.
8. Missing input file → exit 1 + stderr; missing `--stopwords` file → exit 1 + stderr.
9. Empty file → exit 0, no output.

Lint: `ruff check .` → 0 findings.
