from pathlib import Path

from agents.config import IMAGES_DIR
from agents.image_sourcer.flux_client import generate_image_to_file


def generate_image(prompt: str, save_path: Path) -> Path:
    """Generate a single image and save it. Uses the shared rate-limited client."""
    return generate_image_to_file(prompt, save_path, width=768, height=1024)


def source_images_for_post(slug: str, image_entries: list[dict]) -> list[Path]:
    """Generate images for each item referenced in a blog post.

    image_entries: list of {"alt": "description", "path": "/images/posts/slug/01.png"}
    """
    saved = []

    for entry in image_entries:
        alt = entry["alt"]
        rel_path = entry["path"]
        filename = Path(rel_path).name
        save_dir = IMAGES_DIR / slug
        save_path = save_dir / filename

        if save_path.exists():
            saved.append(save_path)
            continue

        prompt = (
            f"Pinterest-aesthetic editorial photo: {alt}. High quality, warm natural lighting, "
            "stylish composition, lifestyle photography. No text or watermarks."
        )
        try:
            path = generate_image(prompt, save_path)
            saved.append(path)
            print(f"  Generated: {filename} — {alt[:60]}")
        except Exception as e:
            print(f"  Failed: {filename} — {e}")

    return saved
