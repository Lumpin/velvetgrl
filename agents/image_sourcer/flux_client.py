"""Shared Flux (Together.ai) image client with rate limiting and 429 backoff.

Together.ai's free tier throttles aggressively. This module enforces a
process-wide minimum interval between calls and retries with exponential
backoff on 429.
"""

import io
import threading
import time
from pathlib import Path

import httpx
from PIL import Image

from agents.config import load_settings

_LOCK = threading.Lock()
_LAST_CALL_TS = 0.0

# Minimum seconds between calls. Together free tier is ~6 req/min => 10s gap.
MIN_INTERVAL = 10.0
MAX_RETRIES = 5
INITIAL_BACKOFF = 20.0


def _wait_for_slot() -> None:
    """Block until at least MIN_INTERVAL seconds have passed since the last call."""
    global _LAST_CALL_TS
    with _LOCK:
        now = time.monotonic()
        delta = now - _LAST_CALL_TS
        if delta < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - delta)
        _LAST_CALL_TS = time.monotonic()


def generate_image_to_file(prompt: str, save_path: Path, *, width: int = 768, height: int = 1024) -> Path:
    """Generate one image and save it to `save_path`. Retries on 429.

    Raises the last httpx exception if every retry fails.
    """
    settings = load_settings()
    api_key = settings.get("flux_api_key", "")
    save_path.parent.mkdir(parents=True, exist_ok=True)

    backoff = INITIAL_BACKOFF
    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES):
        _wait_for_slot()
        try:
            r = httpx.post(
                "https://api.together.xyz/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "black-forest-labs/FLUX.1-schnell",
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "n": 1,
                },
                timeout=120,
            )
            if r.status_code == 429:
                last_exc = httpx.HTTPStatusError("429", request=r.request, response=r)
                print(f"  429 — backing off {backoff:.0f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(backoff)
                backoff = min(backoff * 2, 120.0)
                continue
            r.raise_for_status()
            image_url = r.json()["data"][0]["url"]
            img = httpx.get(image_url, follow_redirects=True, timeout=60)
            # Together.ai returns JPEG even when we name the file .png. Re-encode
            # so the bytes on disk actually match the extension.
            if save_path.suffix.lower() == ".png":
                with Image.open(io.BytesIO(img.content)) as im:
                    im.save(save_path, format="PNG")
            else:
                save_path.write_bytes(img.content)
            return save_path
        except httpx.HTTPError as e:
            last_exc = e
            # Non-429 errors: short retry then give up.
            if attempt < MAX_RETRIES - 1:
                time.sleep(5)
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("unreachable")
