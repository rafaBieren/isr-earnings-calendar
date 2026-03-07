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
    end_date TEXT,
    event_type TEXT NOT NULL,
    description TEXT,
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
        connection.execute("ALTER TABLE events ADD COLUMN end_date TEXT")
    except Exception:
        pass
    try:
        connection.execute("ALTER TABLE events ADD COLUMN report_url TEXT")
    except Exception:
        pass
    try:
        connection.execute("ALTER TABLE events ADD COLUMN description TEXT")
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


def save_events_to_db(events: list[dict[str, object]]) -> None:
    settings = load_settings()
    connection = connect(settings.db_path)
    try:
        initialize_schema(connection)
        for event in events:
            connection.execute(
                """
                INSERT OR REPLACE INTO events (
                    security_id,
                    company_name,
                    event_date,
                    end_date,
                    event_type,
                    description,
                    source_url,
                    report_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.get("security_id", ""),
                    event.get("company_name", ""),
                    event.get("event_date", ""),
                    event.get("end_date", ""),
                    event.get("event_type", ""),
                    event.get("description", ""),
                    event.get("source_url", ""),
                    event.get("report_url", ""),
                ),
            )
        connection.commit()
    finally:
        connection.close()


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


def smart_merge_event(event_data: dict[str, object]) -> None:
    """Professionally merges a new event or creates one if it doesn't exist."""
    settings = load_settings()
    connection = connect(settings.db_path)
    try:
        initialize_schema(connection)

        event_date_str = str(event_data.get("event_date", ""))
        date_prefix = event_date_str[:10] if event_date_str else ""
        company = str(event_data.get("company_name", "")).strip()

        if not date_prefix or not company:
            return

        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, description, end_date
            FROM events
            WHERE event_date LIKE ?
              AND (company_name LIKE ? OR ? LIKE '%' || company_name || '%')
            """,
            (f"{date_prefix}%", f"%{company}%", company),
        )
        row = cursor.fetchone()

        if row:
            event_id = int(row["id"])
            old_desc = row["description"]
            old_end = row["end_date"]
            new_desc = old_desc or ""
            added_info = str(event_data.get("description", ""))

            if added_info and added_info not in new_desc:
                marker = (
                    "\n\n-- \u05de\u05d9\u05d3\u05e2 \u05e0\u05d5\u05e1\u05e3 "
                    "\u05de\u05e7\u05e9\u05e8\u05d9 \u05de\u05e9\u05e7\u05d9\u05e2"
                    "\u05d9\u05dd --\n"
                )
                merged_desc = (
                    f"{new_desc}{marker}{added_info}" if new_desc else added_info
                )
                new_end = event_data.get("end_date") or old_end
                cursor.execute(
                    "UPDATE events SET description = ?, end_date = ? WHERE id = ?",
                    (merged_desc, new_end, event_id),
                )
        else:
            security_id = event_data.get("security_id") or f"IR_{company}_{date_prefix}"
            cursor.execute(
                """
                INSERT OR REPLACE INTO events (
                    security_id,
                    company_name,
                    event_date,
                    end_date,
                    event_type,
                    description,
                    source_url,
                    report_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(security_id),
                    company,
                    event_date_str,
                    event_data.get("end_date"),
                    event_data.get(
                        "event_type",
                        "\u05d0\u05d9\u05e8\u05d5\u05e2 \u05de\u05e9\u05e7\u05d9"
                        "\u05e2\u05d9\u05dd",
                    ),
                    event_data.get("description", ""),
                    event_data.get("source_url", ""),
                    "",
                ),
            )
        connection.commit()
    finally:
        connection.close()
