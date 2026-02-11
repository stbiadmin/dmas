from __future__ import annotations

import os

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient


def get_model_client(model: str = "gpt-4.1-mini") -> OpenAIChatCompletionClient:
    """Create an OpenAI model client, loading the API key from .env if needed."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Create a .env file (see .env.example) or export the variable."
        )
    return OpenAIChatCompletionClient(model=model, api_key=api_key)
