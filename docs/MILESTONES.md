# Milestones

## Milestone 1: Maya Scraper & DB Integration
Fetch a single day/page of Maya data, extract earnings events, and safely upsert
to SQLite with idempotency enforced by `security_id` (and event date keying in
the table schema).

## Milestone 2: ICS Feed API
Implement a FastAPI endpoint that reads normalized earnings data from SQLite and
returns a valid `.ics` feed.

## Milestone 3: Automation & Orchestration
Implement daily automated execution of the scraper via background task or cron so
the data store remains current without manual intervention.
