import json
import re
import anthropic
from agents.config import load_settings


def get_claude_client() -> anthropic.Anthropic:
    """Get an Anthropic client using settings."""
    settings = load_settings()
    api_key = settings.get("anthropic_api_key") or None
    return anthropic.Anthropic(api_key=api_key)


def parse_json_response(text: str):
    """Parse JSON from Claude's response, stripping markdown code blocks if present."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ```
    match = re.search(r'```(?:json)?\s*\n?(.*?)```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return json.loads(text)
