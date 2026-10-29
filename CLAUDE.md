# Kephart Trail

Open-source hiking forum for Great Smoky Mountains National Park. Built in phases (0–9); work on one phase at a time.

## Stack
- Django 5.2 + PostgreSQL 17, server-rendered templates (HTMX for small interactive bits, from Phase 4).
- Python 3.12, dependencies managed with uv (`pyproject.toml`, `uv.lock`).
- Docker Compose for local dev (`web` + `db`).

## Layout
- `kephart/` – project package. Settings split into `kephart/settings/base.py`, `dev.py`, `prod.py`. All secrets come from env vars via django-environ; `dev.py` supplies safe local defaults.
- Apps (top level): `accounts` (custom `User`, auth), `parks` (Park/Section/Trail/Board), `forum` (Thread/Post/Tag/votes), `profiles` (profile posts, images), `moderation` (reports, mod actions), `core` (home, static pages, shared helpers).
- `templates/` – project-level templates; `<app>/tests/` – pytest-django tests.
- `AUTH_USER_MODEL = "accounts.User"`. Never reference `django.contrib.auth.models.User` directly; use `get_user_model()` or `settings.AUTH_USER_MODEL`.

## Code style
- Prefer explicit `for` loops and spelled-out `if` statements over compressed one-liners and dense comprehensions. Readability for newer contributors matters more than brevity.
- Every limit (post length, image count, rate limits) is enforced on the server, never only in the browser.
- Store Markdown raw and render to sanitized HTML on save; never render user input unsafely.
- ruff handles lint and formatting (line length 100).

## Before finishing any change
```sh
uv run ruff check .
uv run ruff format .
uv run pytest
```
Tests need Postgres: `docker compose up -d db`. If models change, run `uv run python manage.py makemigrations` and commit the migration.
