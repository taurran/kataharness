# Project 3 — Arithmetic expression evaluator

## SPEC (given identically to both arms)
Build a Python package **`expr_eval`** that parses and evaluates arithmetic expressions from a string.

- **Public API:** `evaluate(expr: str) -> float`.
- **Grammar:** binary `+ - * /`, **unary minus**, parentheses, integer and float literals. Standard
  precedence (`* /` over `+ -`) and left-associativity; whitespace-insensitive.
- **Errors:** malformed input (bad token, unbalanced parens, trailing/missing operand) → raise a defined
  **`ParseError`** (exported from the package). **Division by zero → raise `ParseError`** (pin this — do not
  leak a bare `ZeroDivisionError`).
- **CLI:** `python -m expr_eval "2+3*4"` prints the numeric result to stdout, exit 0; on a `ParseError`, message
  to stderr, exit 1.
- **Constraints:** hand-written tokenizer + parser (no `eval`, no external parser libs). Keep it small (≈3–6 files).
- **Quality:** ships with a `pytest` suite; passes `ruff check .` clean.

## GATE (experimenter acceptance — held out from the arms)
Run **`pytest -q`** (held-out suite) **and** **`ruff check .`** → both pass on first delivered build for
**first-pass-green**.

Enumerated acceptance cases (`evaluate(...)`):
1. `"2+3*4"` → `14`.
2. `"(2+3)*4"` → `20`.
3. `"-3+5"` → `2`; `"-(3+5)"` → `-8`.
4. `"10/4"` → `2.5`.
5. `"2*3+4*5"` → `26` (precedence); `"100-10-10"` → `80` (left-assoc).
6. `"  ( 1 + 2 ) * 3 "` → `9` (whitespace-insensitive).
7. `"2 +"` , `"(1+2"` , `"1 2"` , `""` → each raises `ParseError`.
8. `"1/0"` → raises `ParseError` (not bare `ZeroDivisionError`).
9. CLI: `python -m expr_eval "2+3*4"` → prints `14` (or `14.0`), exit 0; `python -m expr_eval "1/0"` → stderr + exit 1.

Lint: `ruff check .` reports 0 findings.
