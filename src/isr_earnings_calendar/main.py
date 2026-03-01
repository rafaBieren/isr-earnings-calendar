from __future__ import annotations

import os

import uvicorn

from isr_earnings_calendar.api import app
from isr_earnings_calendar.config import load_settings

if __name__ == "__main__":
    db_path = load_settings().db_path
    db_dir = os.path.dirname(db_path) or "."
    os.makedirs(db_dir, exist_ok=True)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
