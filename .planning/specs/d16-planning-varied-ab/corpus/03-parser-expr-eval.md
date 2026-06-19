# Project 3 — Arithmetic expression evaluator  (v2, hardened post-pilot)

## SPEC (given identically to both arms)
Build a Python package **`expr_eval`** that parses and evaluates arithmetic expressions. **Precedence and
associativity interact — design the grammar before coding.**

- **Public API:** `evaluate(expr: str) -> float`.
- **Operators & precedence (lowest → highest):**
  1. `+` `-` (binary, left-associative)
  2. `*` `/` `%` (left-associative; `/` is true division, `%` is Python-style modulo)
  3. unary `+` / unary `-`
  4. `**` (exponentiation, **right-associative**, binds tighter than unary on its left but a unary on the base
     applies first — i.e. `-2**2 == -4`, but `2**-2 == 0.25`)
- **Literals:** integers, floats incl. leading-dot (`.5`), trailing-dot (`5.`), and scientific (`1e3`, `2.5E-1`).
  Parentheses group. Whitespace-insensitive.
- **Errors:** any malformed input (bad token, unbalanced parens, missing/trailing operand) → raise an exported
  **`ParseError`**. **Division or modulo by zero → raise `ParseError`** (do not leak `ZeroDivisionError`).
- **CLI:** `python -m expr_eval "2+3*4"` prints the result (exit 0); on `ParseError` → stderr + exit 1.
- Hand-written tokenizer + parser (no `eval`, no parser libs). Keep it small (≈4–7 files). Ship a `pytest`
  suite; pass `ruff check .` clean.

## GATE (held out from the arms) — `pytest -q` ∧ `ruff check .`  (`evaluate(...)`)
1. Precedence: `"2+3*4"`→14; `"2*3+4*5"`→26; `"2+3%2"`→3 (`%` binds with `*`).
2. Left-assoc: `"100-10-10"`→80; `"8/4/2"`→1.0.
3. Exponent right-assoc: `"2**3**2"`→512; `"2**2**3"`→256.
4. Unary vs `**`: `"-2**2"`→-4; `"2**-2"`→0.25; `"-(3+5)"`→-8; `"+-3"`→-3.
5. True division & modulo: `"10/4"`→2.5; `"7%3"`→1; `"-7%3"`→2 (Python modulo sign).
6. Literals: `".5+.5"`→1.0; `"5.*2"`→10.0; `"1e3-1"`→999.0; `"2.5E-1*4"`→1.0.
7. Whitespace: `"  ( 1 + 2 ) ** 3 "`→27.
8. Malformed → `ParseError`: `"2 +"`, `"(1+2"`, `"1 2"`, `""`, `"*3"`, `"2**"`.
9. Zero: `"1/0"` and `"5%0"` → `ParseError` (not bare `ZeroDivisionError`).
10. CLI: `python -m expr_eval "2+3*4"` → prints `14`/`14.0`, exit 0; `"1/0"` → stderr, exit 1.

Lint: `ruff check .` → 0 findings. *(Executable held-out suite authored from these cases before project-3 runs.)*
