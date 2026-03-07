from __future__ import annotations

from isr_earnings_calendar.db import (
    Event,
    connect,
    count_events,
    initialize_schema,
    smart_merge_event,
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


def test_smart_merge_event_updates_existing_event(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "events.db"
    monkeypatch.setenv("ISR_EARNINGS_DB_PATH", str(db_path))
    monkeypatch.setenv("ISR_EARNINGS_MAYA_BASE_URL", "https://maya.tase.co.il")

    connection = connect(str(db_path))
    try:
        initialize_schema(connection)
        upsert_event(
            connection,
            Event(
                security_id="12345",
                company_name="Example Co Ltd",
                event_date="2026-03-01T10:00:00",
                event_type="conference",
                description="Original agenda",
            ),
        )
    finally:
        connection.close()

    smart_merge_event(
        {
            "company_name": "Example Co",
            "event_date": "2026-03-01T10:00:00",
            "description": "Zoom link: https://example.com/room",
            "end_date": "2026-03-01T11:00:00",
        }
    )

    connection = connect(str(db_path))
    try:
        row = connection.execute(
            """
            SELECT company_name, description, end_date
            FROM events
            WHERE security_id = ?
            """,
            ("12345",),
        ).fetchone()

        assert row is not None
        assert row["company_name"] == "Example Co Ltd"
        assert "Original agenda" in row["description"]
        assert "Zoom link: https://example.com/room" in row["description"]
        assert row["end_date"] == "2026-03-01T11:00:00"
        assert count_events(connection) == 1
    finally:
        connection.close()


def test_smart_merge_event_inserts_new_event(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "events.db"
    monkeypatch.setenv("ISR_EARNINGS_DB_PATH", str(db_path))
    monkeypatch.setenv("ISR_EARNINGS_MAYA_BASE_URL", "https://maya.tase.co.il")

    smart_merge_event(
        {
            "company_name": "NewCo",
            "event_date": "2026-03-02T09:00:00",
            "event_type": "roadshow",
            "description": "Investor presentation",
            "source_url": "https://example.com/ir",
        }
    )

    connection = connect(str(db_path))
    try:
        row = connection.execute(
            """
            SELECT security_id, company_name, event_date, event_type, source_url
            FROM events
            WHERE company_name = ?
            """,
            ("NewCo",),
        ).fetchone()

        assert row is not None
        assert row["security_id"] == "IR_NewCo_2026-03-02"
        assert row["company_name"] == "NewCo"
        assert row["event_date"] == "2026-03-02T09:00:00"
        assert row["event_type"] == "roadshow"
        assert row["source_url"] == "https://example.com/ir"
        assert count_events(connection) == 1
    finally:
        connection.close()
