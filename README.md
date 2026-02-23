# ISR Earnings Calendar

Automated ICS feed generator for Israeli earnings events scraped from Maya.

## Phase 2 Scope
- Project scaffolding for Python + FastAPI + SQLite.
- Strict environment-based configuration.
- SQLite schema bootstrap and idempotent upsert primitive.
- Early tests for config and persistence behavior.

## Local Commands
- `python -m pytest`
- `black .`
- `flake8`

## Required Environment Variables
- `ISR_EARNINGS_DB_PATH`
- `ISR_EARNINGS_MAYA_BASE_URL`
