import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"
QUEUE_DIR = Path(__file__).parent.parent / "queue"
DATA_DIR = Path(__file__).parent.parent / "data"
WEBSITE_DIR = Path(__file__).parent.parent / "website"
BLOG_DIR = WEBSITE_DIR / "src" / "content" / "blog"
IMAGES_DIR = WEBSITE_DIR / "public" / "images" / "posts"

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
    """Load settings from config/settings.json."""
    settings_path = CONFIG_DIR / "settings.json"
    if settings_path.exists():
        return json.loads(settings_path.read_text())
    return {}


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
