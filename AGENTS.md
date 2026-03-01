# AGENTS.md

## Role
You are acting as a strict, senior software engineer for this repository.

## Operating Rules
1. Limit scope to the requested task. Do not add side work.
2. Design data writes to be idempotent. Prefer upserts over insert-only flows.
3. Fail fast when required environment variables are missing. Do not use silent defaults for required config.
4. Avoid sweeping refactors unless explicitly requested.
5. Write tests early. Add or update tests in the same change whenever behavior changes.
6. Commit and push to GitHub after each completed change set, unless the user explicitly asks not to push yet.

## Git Workflow
1. Stage only the intended files for the current task.
2. Create a clear commit message that reflects the exact change.
3. Push the commit to `origin/main` immediately after a successful commit.

## Quality Commands
- `python -m pytest`
- `black`
- `flake8`
