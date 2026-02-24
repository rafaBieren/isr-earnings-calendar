from __future__ import annotations

import sqlite3
from dataclasses import dataclass

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    event_date TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source_url TEXT,
    UNIQUE (security_id, event_date, event_type)
);
"""


@dataclass(frozen=True, slots=True)
class Event:
    security_id: str
    company_name: str
    event_date: str
    event_type: str
    source_url: str | None = None


def connect(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.execute(SCHEMA_SQL)
    connection.commit()


def upsert_event(connection: sqlite3.Connection, event: Event) -> None:
    connection.execute(
        """
        INSERT INTO events (
            security_id,
            company_name,
            event_date,
            event_type,
            source_url
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(security_id, event_date, event_type) DO NOTHING
        """,
        (
            event.security_id,
            event.company_name,
            event.event_date,
            event.event_type,
            event.source_url,
        ),
    )
    connection.commit()


def count_events(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) AS count FROM events").fetchone()
    return int(row["count"])
