# CAPTCHA API

[![CI](https://github.com/DanieleBelfiore/captcha-api/actions/workflows/ci.yml/badge.svg)](https://github.com/DanieleBelfiore/captcha-api/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A small self-hosted HTTP service that generates and validates CAPTCHAs.

`GET /captcha` returns a challenge ID plus a base64-encoded PNG. Show the image
to the user, collect what they type, then `POST /captcha/validate` with the ID
and the text. The answer is stored server-side, expires after 5 minutes, and is
deleted the moment it is validated — so each challenge works exactly once.

![Example generated captcha](docs/captcha-example.png)

*Actual output of `generate_captcha_image` — read [Known limitations](#known-limitations)
before putting this in front of real traffic.*

## Why this exists

I wanted a CAPTCHA endpoint I could drop into side projects without wiring them
to reCAPTCHA or hCaptcha. Those services work well, but every one of them means
an external dependency on the critical path of my signup form, a third-party
script in the browser, and my visitors' IP addresses going somewhere I don't
control. For a hobby project that gets a handful of signups a week, that trade
never felt worth it.

So: one container, one Postgres table, no outbound calls, no client-side SDK.

The design choice worth naming is that this is **stateful**. The plaintext answer
lives in Postgres and the client only ever sees an integer ID. The alternative —
a signed, self-contained token (HMAC or JWT) carrying the answer — needs no
database at all and scales horizontally for free. I went with the database
because single-use enforcement is the whole point of a CAPTCHA, and deleting a
row is a much shorter path to "this challenge can never be replayed" than
building a revocation list for stateless tokens. The cost is a database
round-trip per request and a table that needs pruning.

## Setup

### Prerequisites

- Git
- Docker

### Local development with Docker

1. **Clone the repository**

    ```sh
    git clone https://github.com/DanieleBelfiore/captcha-api.git
    cd captcha-api
    ```

2. **Create a `.env` file** in the project root:

    ```env
    DATABASE_URL=postgresql://postgres:password@db:5432/captcha_api
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=password
    POSTGRES_DB=captcha_api
    ```

    `.env` is gitignored. Use a real password anywhere that isn't your laptop.

3. **Build and run**

    ```sh
    docker-compose up --build
    ```

4. **Open the API**

    Browse to `http://localhost:8000` — it redirects to the Swagger UI at
    `http://localhost:8000/swagger`.

## API

Interactive docs: `/swagger`. Both endpoints are rate limited (see
[Configuration](#configuration)) and answer `429` when the limit is exceeded.

### Generate a CAPTCHA

- **URL**: `/captcha`
- **Method**: `GET`
- **Response** `200`:

  ```json
  {
    "id": 1,
    "image": "<base64_png_data>"
  }
  ```

  Render it directly with `<img src="data:image/png;base64,{image}">`.

### Validate a CAPTCHA

- **URL**: `/captcha/validate`
- **Method**: `POST`
- **Request body**:

  ```json
  {
    "id": 1,
    "text": "aK7dQ2"
  }
  ```

- **Response** `200`: a bare JSON boolean, `true` or `false`.

  ```json
  true
  ```

  `false` covers every failure the same way — unknown ID, expired challenge,
  wrong text, or an ID that was already validated. The comparison is
  case-sensitive.

  A challenge is consumed on a successful validation *and* on any attempt made
  after it expired; in both cases the row is deleted. A wrong guess does **not**
  consume the challenge, so the user can retry until the TTL runs out or the rate
  limit kicks in.

### Errors

| Status | When |
| --- | --- |
| `422` | Request body failed validation (missing or non-integer `id`, missing `text`) |
| `429` | Rate limit exceeded for the caller's IP |

## Configuration

| Setting | Where | Default | Meaning |
| --- | --- | --- | --- |
| `DATABASE_URL` | env var | — | Postgres connection string. Required; the database is created on startup if missing |
| `CAPTCHA_TTL` | [app/captcha.py](app/captcha.py) | 5 minutes | How long a challenge stays valid |
| `MAX_REQUESTS` | [app/rate_limit.py](app/rate_limit.py) | 20 | Requests allowed per window, per IP |
| `WINDOW_SECONDS` | [app/rate_limit.py](app/rate_limit.py) | 60 | Length of the rate-limit window |

Only `DATABASE_URL` is read from the environment. The other three are module
constants — edit the file to change them.

## Running tests

Against the Docker Compose stack:

```sh
docker-compose run --rm test
```

Or locally, with a reachable Postgres and `DATABASE_URL` set:

```sh
pip install -r requirements.txt
pytest
```

The suite creates and drops its own database, named `${DATABASE_URL}_test`, so
the Postgres user needs `CREATEDB`.

## Continuous integration

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs the test suite on
every push and pull request against `main`, using a `postgres:18` service
container.

## Known limitations

This is a personal project. Some things are deliberately unfinished, and one of
them matters a lot:

- **The image offers no real protection.** It is plain text in the default PIL
  font on a white background — no noise, no distortion, no rotation, no
  overlapping glyphs. Any off-the-shelf OCR reads it on the first try. Treat it
  as a speed bump against naive scripts, not as bot defence.
- **The rate limiter is in-process.** Counters live in a Python dict
  ([app/rate_limit.py](app/rate_limit.py)), so every worker keeps its own tally
  and the real ceiling is `MAX_REQUESTS × workers`. Restarting the process
  resets it. A shared store such as Redis is the fix.
- **The rate limiter trusts `request.client.host`.** Behind a proxy that is the
  proxy's IP, and every caller shares one bucket. Behind no proxy it is
  spoofable at the network layer.
- **Expired rows are never swept.** A row is deleted when it is validated, or
  when someone tries to validate it after it expired. Challenges that are
  generated and then abandoned stay in the table forever. A periodic cleanup job
  is missing.
- **CORS is wide open** — `allow_origins=["*"]` in
  [app/main.py](app/main.py). Fine for a public read-only endpoint, worth
  narrowing anywhere else.
- **No auth, no per-key quotas, no metrics.**

## Project layout

```
app/
  main.py        FastAPI app, CORS, Swagger at /swagger
  routes.py      /captcha endpoints
  captcha.py     text and image generation, TTL, validation logic
  models.py      SQLAlchemy Captcha model
  schemas.py     Pydantic request/response models
  database.py    engine, session factory, auto-create database
  rate_limit.py  in-memory per-IP sliding window
tests/
  test_main.py   endpoint tests
```

## License

[MIT](LICENSE)
