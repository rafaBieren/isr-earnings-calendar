from __future__ import annotations

import os
import sys

import uvicorn

# Bulletproof path injection for cloud environments
import pathlib

src_path = str(pathlib.Path(__file__).resolve().parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from isr_earnings_calendar.api import app  # noqa: E402
from isr_earnings_calendar.config import load_settings  # noqa: E402

if __name__ == "__main__":
    db_path = load_settings().db_path
    db_dir = os.path.dirname(db_path) or "."
    os.makedirs(db_dir, exist_ok=True)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
