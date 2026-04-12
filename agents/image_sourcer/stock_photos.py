import httpx
from pathlib import Path
from agents.config import load_settings, IMAGES_DIR


def generate_image(prompt: str, save_path: Path) -> Path:
    """Generate a single image using Flux API and save to disk."""
    settings = load_settings()
    api_key = settings.get("flux_api_key", "")

    save_path.parent.mkdir(parents=True, exist_ok=True)

    response = httpx.post(
        "https://api.together.xyz/v1/images/generations",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": prompt,
            "width": 768,
            "height": 1024,
            "n": 1,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    image_url = data["data"][0]["url"]
    img_response = httpx.get(image_url, follow_redirects=True)
    save_path.write_bytes(img_response.content)
    return save_path


def source_images_for_post(slug: str, image_entries: list[dict]) -> list[Path]:
    """Generate images for each item referenced in a blog post.

    image_entries: list of {"alt": "description", "path": "/images/posts/slug/01.png"}
    """
    saved = []

    for entry in image_entries:
        alt = entry["alt"]
        rel_path = entry["path"]  # e.g. /images/posts/slug/01.png
        filename = Path(rel_path).name
        save_dir = IMAGES_DIR / slug
        save_path = save_dir / filename

        if save_path.exists():
            saved.append(save_path)
            continue

        prompt = f"Pinterest-aesthetic editorial photo: {alt}. High quality, warm natural lighting, stylish composition, lifestyle photography. No text or watermarks."
        try:
            path = generate_image(prompt, save_path)
            saved.append(path)
            print(f"  Generated: {filename} — {alt[:60]}")
        except Exception as e:
            print(f"  Failed: {filename} — {e}")

    return saved
