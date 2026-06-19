# Project 2 — Notes REST API

## SPEC (given identically to both arms)
Build a small **in-memory REST API for "notes"** in Python using **FastAPI**.

- **Endpoints:**
  - `POST /notes` — body `{ "title": str, "body": str }` → **201** + the created note
    `{ "id", "title", "body", "created_at" }` (`created_at` ISO-8601 UTC).
  - `GET /notes` — → **200** + a JSON array of all notes (creation order).
  - `GET /notes/{id}` — → **200** + the note, or **404** if absent.
  - `DELETE /notes/{id}` — → **204** if deleted, **404** if absent.
- **Validation:** `title` required and non-empty → **422** if missing/empty. `body` optional (defaults `""`).
- **IDs:** server-assigned, unique, stable for the process lifetime (monotonic int or uuid — arm's choice).
- **Storage:** in-memory only (no database, no file persistence).
- **Run:** `uvicorn` app object importable (e.g. `app.main:app`). Keep it small (≈3–6 files).
- **Quality:** ships with a `pytest` suite using FastAPI `TestClient`; passes `ruff check .` clean.

## GATE (experimenter acceptance — held out from the arms)
Run **`pytest -q`** (held-out TestClient suite) **and** **`ruff check .`** → both pass on first delivered build
for **first-pass-green**.

Enumerated acceptance cases:
1. `POST /notes {"title":"a","body":"b"}` → 201; response has `id`, `title=="a"`, `body=="b"`, an ISO `created_at`.
2. After two creates, `GET /notes` → 200 with a 2-element array in creation order.
3. `GET /notes/{id}` for a created id → 200 + that note; for an unknown id → 404.
4. `DELETE /notes/{id}` for a created id → 204; a subsequent `GET /notes/{id}` → 404.
5. `DELETE /notes/{unknown}` → 404.
6. `POST /notes {"body":"x"}` (no title) → 422; `POST /notes {"title":""}` (empty) → 422.
7. `body` omitted on create → note created with `body==""`.

Lint: `ruff check .` reports 0 findings.
