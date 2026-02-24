from __future__ import annotations

from isr_earnings_calendar.db import (
    Event,
    connect,
    count_events,
    initialize_schema,
    upsert_event,
)


def test_upsert_event_inserts_new_event(tmp_path) -> None:
    db_path = tmp_path / "events.db"
    connection = connect(str(db_path))
    try:
        initialize_schema(connection)

        upsert_event(
            connection,
            Event(
                security_id="12345",
                company_name="Example Co",
                event_date="2026-03-01",
                event_type="earnings",
                source_url="https://maya.tase.co.il/company/12345",
            ),
        )

        row = connection.execute(
            """
            SELECT security_id, company_name, event_date, event_type, source_url
            FROM events
            WHERE security_id = ? AND event_date = ? AND event_type = ?
            """,
            ("12345", "2026-03-01", "earnings"),
        ).fetchone()

        assert row is not None
        assert row["security_id"] == "12345"
        assert row["company_name"] == "Example Co"
        assert row["event_date"] == "2026-03-01"
        assert row["event_type"] == "earnings"
        assert row["source_url"] == "https://maya.tase.co.il/company/12345"
        assert count_events(connection) == 1
    finally:
        connection.close()


def test_upsert_event_is_idempotent_for_exact_duplicate(tmp_path) -> None:
    db_path = tmp_path / "events.db"
    connection = connect(str(db_path))
    try:
        initialize_schema(connection)
        event = Event(
            security_id="12345",
            company_name="Example Co",
            event_date="2026-03-01",
            event_type="earnings",
            source_url="https://maya.tase.co.il/company/12345",
        )

        upsert_event(connection, event)
        upsert_event(connection, event)

        assert count_events(connection) == 1
    finally:
        connection.close()
