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

Load the GSMNP sections and trails (safe to run again after editing the CSV):

```sh
docker compose exec web python manage.py import_trails data/trails/gsmnp.csv
```

Open http://localhost:8000/. To use the admin:

```sh
docker compose exec web python manage.py createsuperuser
```

## Trail data

Trails live in `data/trails/<park>.csv` with the columns `park,section,name,length_miles`, so corrections are reviewed like code. Fixing a trail name, section, or length is a good first contribution, no programming needed. Check changes against the [official NPS park map](https://www.nps.gov/grsm/planyourvisit/maps.htm) and run `import_trails --dry-run` first to catch mistakes.

In development, emails (signup confirmation, password reset) aren't sent; they're printed in the terminal running the server, so copy the link from there. The signup form's bot check uses Cloudflare's always-pass test keys.

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
