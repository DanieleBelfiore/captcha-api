# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run tests (needs reachable Postgres via `DATABASE_URL`; the suite creates/drops its own `${DATABASE_URL}_test` db, so the user needs `CREATEDB`):

```sh
pip install -r requirements.txt
pytest
```

Single test:

```sh
pytest tests/test_main.py::test_name -v
```

Via Docker Compose (no local Postgres needed):

```sh
docker-compose run --rm test
```

Run the API locally:

```sh
docker-compose up --build
```

Swagger UI at `http://localhost:8000/swagger` (root `/` redirects there).

## Architecture

FastAPI service, single router, one Postgres table (`app/models.py: Captcha` — id, text, created_at). No ORM migrations; `Base.metadata.create_all` runs at import time in `app/models.py`, and `app/database.py` auto-creates the database itself via `sqlalchemy_utils.create_database` if it doesn't exist.

Request flow: `app/routes.py` (`GET /captcha`, `POST /captcha/validate`) → `app/captcha.py` (text/image generation, TTL and validation logic) → `Captcha` model. Both routes share the `rate_limiter` dependency from `app/rate_limit.py`.

Key design point (see README "Why this exists"): this is intentionally **stateful**, not token-based. The plaintext answer lives in Postgres; the client only ever sees an integer id. A challenge is deleted on successful validation *and* on any validation attempt after expiry — a wrong guess before expiry does not consume it.

Module-level constants (not env vars — edit the file to change):
- `CAPTCHA_TTL` in [app/captcha.py](app/captcha.py) — default 5 minutes
- `MAX_REQUESTS` / `WINDOW_SECONDS` in [app/rate_limit.py](app/rate_limit.py) — default 20 req/60s per IP

Only `DATABASE_URL` is read from the environment (`.env`, loaded via `python-dotenv`).

`app/rate_limit.py` is an in-process sliding-window limiter keyed on `request.client.host` — per-worker state (real ceiling is `MAX_REQUESTS × workers`), resets on restart, and trusts the client IP as seen (spoofable with no proxy in front, shared bucket behind one). This is a known, accepted limitation, not a bug to silently "fix" — see README "Known limitations" before changing it.

Tests (`tests/test_main.py`) override `get_db` to point at a separate test database created/dropped per session, and share the same `TestClient` app instance as production code — no mocking of the DB layer.

## Known limitations (deliberate, see README for full list)

- CAPTCHA image has no anti-OCR protection (plain PIL text, no noise/distortion).
- No cleanup job for expired-but-never-validated rows.
- `CORS allow_origins=["*"]` in [app/main.py](app/main.py).
- No auth, no per-key quotas, no metrics.

Don't "fix" these opportunistically — they're documented trade-offs for a hobby-scale project, not oversights.
