import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
QUEUE_DIR = PROJECT_ROOT / "queue"
DATA_DIR = PROJECT_ROOT / "data"
WEBSITE_DIR = PROJECT_ROOT / "website"
BLOG_DIR = WEBSITE_DIR / "src" / "content" / "blog"
IMAGES_DIR = WEBSITE_DIR / "public" / "images" / "posts"

_ENV_LOADED = False


def _load_env_file() -> None:
    """Load .env into os.environ (idempotent, no dependency on python-dotenv)."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for raw in env_path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
    _ENV_LOADED = True


# Map of settings.json keys → environment variable names.
_ENV_OVERRIDES = {
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "flux_api_key": "FLUX_API_KEY",
    "unsplash_access_key": "UNSPLASH_ACCESS_KEY",
    "pexels_api_key": "PEXELS_API_KEY",
    "pinterest_app_id": "PINTEREST_APP_ID",
    "pinterest_app_secret": "PINTEREST_APP_SECRET",
    "pinterest_email": "PINTEREST_EMAIL",
    "pinterest_password": "PINTEREST_PASSWORD",
}

CATEGORIES = {
    "boho-decor": "Boho Decor & Home",
    "tattoo-ideas": "Tattoo Ideas",
    "nail-art": "Nail Art",
    "fashion": "Fashion & Outfits",
    "tarot-spirituality": "Tarot & Spirituality",
    "kitchen-recipes": "Kitchen & Recipes",
    "perfume-fragrance": "Perfume & Fragrance",
    "makeup-beauty": "Makeup & Beauty",
    "hair-hairstyles": "Hair & Hairstyles",
    "jewelry-accessories": "Jewelry & Accessories",
    "self-care-wellness": "Self-Care & Wellness",
    "wedding-bridal": "Wedding & Bridal",
}


def load_settings() -> dict:
    """Load settings from config/settings.json, overlayed with .env values.

    Environment variables (set directly or in .env) win over values in
    settings.json — this lets ops rotate secrets without editing the file.
    """
    _load_env_file()
    settings_path = CONFIG_DIR / "settings.json"
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}

    for setting_key, env_key in _ENV_OVERRIDES.items():
        env_value = os.environ.get(env_key)
        if env_value:
            settings[setting_key] = env_value

    return settings


def load_boards() -> dict:
    """Load Pinterest board mapping from config/boards.json."""
    boards_path = CONFIG_DIR / "boards.json"
    if boards_path.exists():
        return json.loads(boards_path.read_text())
    return {}


def load_categories() -> dict:
    """Load categories config from config/categories.json."""
    categories_path = CONFIG_DIR / "categories.json"
    if categories_path.exists():
        return json.loads(categories_path.read_text())
    return {}


def ensure_dirs() -> None:
    """Create all required directories."""
    for d in [CONFIG_DIR, QUEUE_DIR / "drafts", DATA_DIR / "pins", DATA_DIR / "keywords", BLOG_DIR, IMAGES_DIR]:
        d.mkdir(parents=True, exist_ok=True)
