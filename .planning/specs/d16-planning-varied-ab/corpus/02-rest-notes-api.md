# Project 2 — Notes REST API  (v2, hardened post-pilot)

## SPEC (given identically to both arms)
Build an **in-memory REST API for "notes"** in Python with **FastAPI**. Several features **interact**
(filtering + pagination + ordering + timestamps) — plan them together.

- **Model:** a note = `{ id, title, body, created_at, updated_at }`. `created_at`/`updated_at` are ISO-8601
  UTC. `title` is **trimmed of surrounding whitespace**; empty after trim → invalid. `body` optional (default `""`).
- **Endpoints:**
  - `POST /notes` `{title, body?}` → **201** + the note. Missing/empty-after-trim title → **422**.
  - `GET /notes` → **200** + array, **in creation order**, supporting query params (all optional, combinable):
    - `q` — case-insensitive substring match against **title OR body**.
    - `limit` (int ≥ 0) and `offset` (int ≥ 0) — pagination applied **after** `q` filtering and ordering.
      `limit=0` → empty array; `offset` past the end → empty array (not an error); **negative limit/offset →
      422**.
  - `GET /notes/{id}` → **200** or **404**.
  - `PATCH /notes/{id}` `{title?, body?}` → **200** + updated note, or **404**. If `title` is present it must be
    non-empty after trim (else **422**). A successful PATCH updates `updated_at` only (not `created_at`) and
    does **not** change creation order.
  - `DELETE /notes/{id}` → **204** or **404**.
- **IDs:** server-assigned, unique, **never reused** after deletion (monotonic).
- **Storage:** in-memory only. App importable as e.g. `app.main:app`. Keep it small (≈4–7 files). Ship a
  `pytest` suite using `TestClient`; pass `ruff check .` clean.

## GATE (held out from the arms) — `pytest -q` ∧ `ruff check .`
1. Create → 201 with id, trimmed title, `created_at==updated_at`, body default `""` when omitted.
2. `title="  "` (whitespace) → 422; title omitted → 422.
3. List reflects creation order across ≥3 creates.
4. `q` filters case-insensitively on title OR body; non-matching excluded.
5. Pagination: `limit`/`offset` applied after `q`; `offset` past end → `[]`; `limit=0` → `[]`; `limit=-1` → 422.
6. `GET /notes/{id}` 200 / unknown 404.
7. `PATCH` updates only provided fields; `updated_at` changes, `created_at` unchanged, creation order unchanged;
   empty-after-trim title in PATCH → 422; unknown id → 404.
8. `DELETE` → 204 then `GET` → 404; deleting unknown → 404; a new create after a delete gets a **fresh id**
   (no reuse).

Lint: `ruff check .` → 0 findings. *(Executable held-out suite authored from these cases before project-2 runs.)*
