"""Validated decision extraction via a locally-running Ollama model."""
import json
from pathlib import Path

import requests

from . import config
from .schemas import ExtractionResult

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "extraction_prompt.md"
PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


def _extract_json(raw: str) -> dict:
    """Find a JSON object in model output without accepting malformed output."""
    decoder = json.JSONDecoder()
    for start, character in enumerate(raw):
        if character != "{":
            continue
        try:
            data, _ = decoder.raw_decode(raw[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    raise ValueError("Ollama response did not contain a valid JSON object")


def extract_decisions(transcript: str) -> dict:
    """Extract and validate decisions from transcript text using local Ollama."""
    prompt = PROMPT_TEMPLATE.replace("{transcript}", transcript)

    resp = requests.post(
        f"{config.OLLAMA_HOST}/api/generate",
        json={
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        },
        timeout=300,
    )
    resp.raise_for_status()
    response_data = resp.json()
    raw = response_data.get("response")
    if not isinstance(raw, str):
        raise ValueError("Ollama response is missing its text 'response' field")

    data = _extract_json(raw)
    return ExtractionResult.model_validate(data).model_dump()
