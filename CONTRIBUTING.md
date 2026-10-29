# Contributing

Thanks for helping. Trail data corrections are a great first contribution, no programming needed.

## Setup
See the Quick start in [README.md](README.md). Develop against demo data; contributors never get the production database.

## Workflow
1. Open or pick an issue (look for `good first issue`).
2. Create a branch from `main`.
3. Make your change with tests.
4. Run `uv run ruff check .`, `uv run ruff format .`, and `uv run pytest`.
5. Open a pull request. CI must pass before review and merge.

`main` is always deployable.

## Code style
ruff is enforced in CI. Prefer explicit loops and spelled-out `if` statements over compressed one-liners.
