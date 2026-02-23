from __future__ import annotations

from isr_earnings_calendar.db import (
    EarningsEvent,
    connect,
    count_events,
    initialize_schema,
    upsert_earnings_event,
)


def test_upsert_is_idempotent_on_security_id_and_event_date(tmp_path) -> None:
    db_path = tmp_path / "events.db"
    connection = connect(str(db_path))
    try:
        initialize_schema(connection)

        upsert_earnings_event(
            connection,
            EarningsEvent(
                security_id="12345",
                event_date="2026-03-01",
                title="Initial Earnings Call",
                source_url="https://maya.tase.co.il/company/12345",
            ),
        )

        upsert_earnings_event(
            connection,
            EarningsEvent(
                security_id="12345",
                event_date="2026-03-01",
                title="Updated Earnings Call",
                source_url="https://maya.tase.co.il/company/12345/new",
            ),
        )

        row = connection.execute(
            """
            SELECT security_id, event_date, title, source_url
            FROM earnings_events
            WHERE security_id = ? AND event_date = ?
            """,
            ("12345", "2026-03-01"),
        ).fetchone()

        assert count_events(connection) == 1
        assert row["security_id"] == "12345"
        assert row["event_date"] == "2026-03-01"
        assert row["title"] == "Updated Earnings Call"
        assert row["source_url"] == "https://maya.tase.co.il/company/12345/new"
    finally:
        connection.close()
