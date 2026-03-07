from __future__ import annotations

import json
import os
import re

import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class IREvent(BaseModel):
    is_relevant: bool = Field(
        description=(
            "True if message is an investor event invitation "
            "(conference, zoom, tour)."
        )
    )
    company_name: str | None = Field(
        None, description="Company name without generic corporate suffixes"
    )
    event_type: str | None = Field(None, description="Event type")
    start_datetime: str | None = Field(
        None, description="Start datetime ISO 8601 format"
    )
    end_datetime: str | None = Field(
        None, description="End datetime ISO 8601 format if specified"
    )
    zoom_link: str | None = Field(None, description="Meeting link (Zoom, Teams, etc.)")
    password: str | None = Field(None, description="Meeting password")
    location: str | None = Field(None, description="Physical location")


def _scrape_url_text(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text(separator=" ", strip=True)[:2000]
    except Exception:
        return ""


def process_ir_message(text: str, image_bytes: bytes | None = None) -> IREvent | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing required env var: GEMINI_API_KEY")

    urls = re.findall(r"(https?://[^\s]+)", text)
    extra_context = ""
    for url in urls:
        scraped = _scrape_url_text(url)
        if scraped:
            extra_context += f"\n--- Content from {url} ---\n{scraped}\n"

    prompt = (
        "Analyze this PR message and extract event details. Output valid JSON.\n\n"
        f"Original Message:\n{text}\n{extra_context}"
    )

    contents: list[str | types.Part] = [prompt]
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "response_schema": IREvent,
                "temperature": 0.1,
            },
        )
        data = json.loads(response.text)
        return IREvent(**data)
    except Exception as exc:
        print(f"Agent Processing Error: {exc}")
        return None
