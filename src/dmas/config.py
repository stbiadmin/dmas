from __future__ import annotations

import os

from dotenv import load_dotenv


def load_env() -> None:
    """Load environment variables from .env file."""
    load_dotenv()


def get_api_key() -> str:
    """Load env and return the OpenAI API key, or raise RuntimeError."""
    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Create a .env file (see .env.example) or export the variable."
        )
    return api_key
