"""Environment-based configuration for BharatAir-Nowcasting."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def get_openaq_api_key() -> str:
    """Return the OpenAQ API key or raise a helpful configuration error."""
    api_key = os.getenv("OPENAQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAQ_API_KEY is not configured. Copy .env.example to .env "
            "and add your OpenAQ API key."
        )
    return api_key
