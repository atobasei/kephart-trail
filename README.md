# Kephart Trail

An open-source, old-school hiking forum for Great Smoky Mountains National Park.
Plain, fast, text-first pages; one long-running thread per trail; dated condition reports.

Status: early development (Phase 0: repo and dev environment).

## Quick start

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```sh
git clone https://github.com/atobasei/kephart-trail.git
cd kephart-trail
docker compose up --build
```

Open http://localhost:8000/. To use the admin:

```sh
docker compose exec web python manage.py createsuperuser
```

No `.env` file is needed for local development. Copy `.env.example` to `.env` if you want to override anything.

## Running lint and tests natively

Install [uv](https://docs.astral.sh/uv/), then, with `docker compose up db` running:

```sh
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run pre-commit install   # run ruff on every commit
```

## Stack

Django 5.2, PostgreSQL 17, server-rendered templates (HTMX added later), Docker Compose.

## License

[AGPL-3.0](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md) to get involved.
