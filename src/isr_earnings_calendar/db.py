from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .config import load_settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    event_date TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT,
    end_date TEXT,
    source_url TEXT,
    report_url TEXT,
    UNIQUE (security_id, event_date, event_type)
);
"""


@dataclass(frozen=True, slots=True)
class Event:
    security_id: str
    company_name: str
    event_date: str
    event_type: str
    description: str | None = None
    end_date: str | None = None
    source_url: str | None = None
    report_url: str | None = None


def connect(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.execute(SCHEMA_SQL)
    try:
        connection.execute("ALTER TABLE events ADD COLUMN report_url TEXT")
    except Exception:
        pass
    try:
        connection.execute("ALTER TABLE events ADD COLUMN description TEXT")
    except Exception:
        pass
    try:
        connection.execute("ALTER TABLE events ADD COLUMN end_date TEXT")
    except Exception:
        pass
    connection.commit()


def upsert_event(connection: sqlite3.Connection, event: Event) -> None:
    connection.execute(
        """
        INSERT INTO events (
            security_id,
            company_name,
            event_date,
            event_type,
            description,
            end_date,
            source_url,
            report_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(security_id, event_date, event_type) DO NOTHING
        """,
        (
            event.security_id,
            event.company_name,
            event.event_date,
            event.event_type,
            event.description,
            event.end_date,
            event.source_url,
            event.report_url,
        ),
    )
    connection.commit()


def count_events(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) AS count FROM events").fetchone()
    return int(row["count"])


def get_all_events() -> list[dict[str, object]]:
    settings = load_settings()
    connection = connect(settings.db_path)
    try:
        initialize_schema(connection)
        rows = connection.execute("""
            SELECT
                id,
                security_id,
                company_name,
                event_date,
                event_type,
                description,
                end_date,
                source_url,
                report_url
            FROM events
            ORDER BY event_date, security_id, event_type
            """).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
