# Contributing

Thanks for helping improve Cosmos Intelligence. The current application is a local development build. Please keep changes aligned with the implemented behavior and record planned work separately from completed features.

## Development setup

The recommended workflow uses Docker Compose and requires Docker Engine/Desktop with the Compose plugin:

```sh
docker compose up --build -d
```

The dashboard is served at `http://localhost:8080`. Optional local variables belong in an ignored `.env` copied from `.env.example`. Never commit credentials, local database contents, or generated build/cache files. The default Compose stack enables development-only identity and disables scheduled ingestion; neither setting is production-ready.

For host-based checks, use Python 3.12 and Node.js 22.22.2:

```sh
python -m pip install -e ".[dev]"
cd frontend && npm ci
```

## Before opening a change

Run the checks relevant to the change:

```sh
ruff check .
mypy app
python -m pytest -q
cd frontend
npm run check
npm test -- --run
npm run build
```

PostgreSQL integration tests require a dedicated disposable database configured with `COSMOS_TEST_DATABASE_URL`; migrate that database first. Do not use the Compose development database or any production database for test data. The CI workflow provisions its own disposable PostgreSQL service and applies migrations before testing.

For infrastructure or migration changes, also run:

```sh
alembic -c alembic/alembic.ini upgrade head
alembic -c alembic/alembic.ini check
docker compose config --quiet
git diff --check
```

## Change expectations

- Keep NASA/JPL credentials server-side and out of logs, URLs, fixtures, and browser bundles.
- Preserve source provenance and original units; distinguish upstream facts from derived values and estimates.
- Add or adjust focused tests for behavior changes. Keep live third-party APIs out of ordinary automated tests.
- Update the relevant integration, operations, status, or roadmap documentation when behavior or operational requirements change.
- Keep AI generation disabled unless the documented NASA policy gate is satisfied and the implementation has the required evidence and safety checks.
- Use clear commit messages and describe checks actually run. CI must pass before treating a change as release-ready.

## Project status and limitations

AI response generation, browser OIDC/PKCE sign-in, production secret mounts, deployment, backups, and public tile-provider approval remain incomplete. See [project status](PROJECT_STATUS.md), [implementation progress](docs/IMPLEMENTATION_PROGRESS.md), [technical debt](TECHNICAL_DEBT.md), and [roadmap](ROADMAP.md).
