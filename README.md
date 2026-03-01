# ISR Earnings Calendar

Automated ICS feed generator for Israeli earnings events from Maya.

## Prerequisites
- Python 3.11+

## Setup
1. Install dependencies:
   `pip install -e .`
2. Set required environment variables:
   - `ISR_EARNINGS_DB_PATH`
   - `ISR_EARNINGS_MAYA_BASE_URL`

Example:
`ISR_EARNINGS_DB_PATH=./tmp/isr_earnings.db`
`ISR_EARNINGS_MAYA_BASE_URL=https://maya.tase.co.il`

## Run
Start the API server:
`python src/isr_earnings_calendar/main.py`

Server address:
`http://localhost:8000`

At startup, the app immediately runs `sync_maya_events()` and then starts the
daily scheduler.

Calendar endpoint:
`http://localhost:8000/calendar`

## Quality Gates
- `python -m black .`
- `python -m flake8`
- `python -m pytest`
