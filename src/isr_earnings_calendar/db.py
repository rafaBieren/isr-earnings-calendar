from __future__ import annotations

import sqlite3
from dataclasses import dataclass

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS earnings_events (
    security_id TEXT NOT NULL,
    event_date TEXT NOT NULL,
    title TEXT NOT NULL,
    source_url TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (security_id, event_date)
);
"""


@dataclass(frozen=True, slots=True)
class EarningsEvent:
    security_id: str
    event_date: str
    title: str
    source_url: str | None = None


def connect(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.execute(SCHEMA_SQL)
    connection.commit()


def upsert_earnings_event(connection: sqlite3.Connection, event: EarningsEvent) -> None:
    connection.execute(
        """
        INSERT INTO earnings_events (security_id, event_date, title, source_url)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(security_id, event_date) DO UPDATE SET
            title = excluded.title,
            source_url = excluded.source_url,
            updated_at = CURRENT_TIMESTAMP
        """,
        (event.security_id, event.event_date, event.title, event.source_url),
    )
    connection.commit()


def count_events(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) AS count FROM earnings_events").fetchone()
    return int(row["count"])
