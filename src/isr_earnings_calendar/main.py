from __future__ import annotations

from fastapi import FastAPI

from .config import load_settings
from .db import connect, initialize_schema


def create_app() -> FastAPI:
    app = FastAPI(title="ISR Earnings Calendar")

    @app.on_event("startup")
    def startup() -> None:
        settings = load_settings()
        connection = connect(settings.db_path)
        try:
            initialize_schema(connection)
        finally:
            connection.close()

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
