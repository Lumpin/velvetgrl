"""Backfill missing post images using the rate-limited Flux client.

For each blog post markdown in website/src/content/blog/, find every
![alt](/images/posts/<slug>/NN.png) reference whose file is missing on disk,
and regenerate it (with 10s spacing + 429 retry).
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rich.console import Console

from agents.image_sourcer.flux_client import generate_image_to_file

console = Console()
BLOG_DIR = ROOT / "website" / "src" / "content" / "blog"
PUBLIC = ROOT / "website" / "public"

IMG_RE = re.compile(r"!\[([^\]]*)\]\((/images/posts/[^)]+)\)")


def find_missing() -> list[tuple[str, str, Path]]:
    """Return (alt, web_path, on_disk_path) for every missing image."""
    missing: list[tuple[str, str, Path]] = []
    for md in sorted(BLOG_DIR.glob("*.md")):
        for alt, web_path in IMG_RE.findall(md.read_text()):
            local = PUBLIC / web_path.lstrip("/")
            if not local.exists():
                missing.append((alt, web_path, local))
    return missing


def main() -> None:
    missing = find_missing()
    if not missing:
        console.print("[green]Nothing missing. Site is clean.[/green]")
        return

    console.rule(f"[bold]Backfilling {len(missing)} image(s)")
    eta_min = len(missing) * 10 / 60
    console.print(f"  ETA ~{eta_min:.0f} minutes at 10s/image with backoff on 429.")

    succeeded = failed = 0
    for i, (alt, web_path, on_disk) in enumerate(missing, 1):
        prompt = (
            f"Pinterest-aesthetic editorial photo: {alt}. High quality, warm natural "
            "lighting, stylish composition, lifestyle photography. No text or watermarks."
        )
        try:
            generate_image_to_file(prompt, on_disk, width=768, height=1024)
            succeeded += 1
            console.print(f"  [{i:3}/{len(missing)}] ok  {web_path}")
        except Exception as e:
            failed += 1
            console.print(f"  [{i:3}/{len(missing)}] FAIL {web_path} — {e}")

    console.rule(f"[green]Backfill done: {succeeded} succeeded, {failed} failed")


if __name__ == "__main__":
    main()
