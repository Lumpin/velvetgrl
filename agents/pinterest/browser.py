"""Pinterest posting — uses the Pinterest API v5."""

import json
from pathlib import Path
from agents.pinterest.api import create_pin as api_create_pin, check_token
from agents.config import load_settings
from agents.db import get_connection


def _build_description(description: str, tags: list[str]) -> str:
    """Build the final pin description with hashtags appended."""
    hashtags = " ".join(f"#{t}" for t in tags) if tags else ""
    if hashtags and hashtags not in description:
        # Append hashtags if not already in the description
        combined = f"{description.rstrip()}\n\n{hashtags}"
        return combined[:500]
    return description[:500]


def create_pin(image_path: Path, title: str, description: str, board: str, url: str) -> str | None:
    """Create a single pin on Pinterest via the API. Returns the Pinterest pin ID."""
    try:
        result = api_create_pin(
            image_path=image_path,
            title=title,
            description=description,
            board_name=board,
            link=url,
        )
        pin_id = result.get("id")
        if pin_id:
            print(f"  Pin created: {pin_id}")
            return pin_id
        return None
    except Exception as e:
        print(f"  Failed to create pin: {e}")
        return None


def post_pins_for_post(slug: str) -> int:
    """Post all pending pins for a given blog post."""
    conn = get_connection()
    pins = conn.execute(
        "SELECT id, image_path, title, description, board, tags FROM pins WHERE post_slug = ? AND status = 'pending'",
        (slug,)
    ).fetchall()

    if not pins:
        conn.close()
        return 0

    settings = load_settings()
    site_url = settings.get("site_url", "https://velvetgrl.com")
    post_url = f"{site_url}/blog/{slug}/"
    posted = 0

    for pin in pins:
        tags = json.loads(pin["tags"]) if pin["tags"] else []
        full_description = _build_description(pin["description"], tags)

        pinterest_id = create_pin(
            image_path=Path(pin["image_path"]),
            title=pin["title"],
            description=full_description,
            board=pin["board"],
            url=post_url,
        )
        if pinterest_id:
            conn.execute(
                "UPDATE pins SET status = 'posted', posted_at = CURRENT_TIMESTAMP, pinterest_pin_id = ? WHERE id = ?",
                (pinterest_id, pin["id"]),
            )
            conn.commit()
            posted += 1

    conn.close()
    return posted


def login_test() -> bool:
    """Test Pinterest API token validity."""
    user = check_token()
    if user:
        username = user.get("username", "unknown")
        print(f"Authenticated as: {username}")
        return True
    return False
