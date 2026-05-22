"""Re-encode any .png file whose bytes are actually JPEG into real PNG.

Together.ai's Flux endpoint returns JPEG content regardless of the requested
output format. Older runs saved that JPEG directly into a .png file, leaving
a content/extension mismatch that breaks strict image consumers (CDN MIME,
social scrapers, image optimisers).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image
from rich.console import Console

console = Console()
POSTS_DIR = ROOT / "website" / "public" / "images" / "posts"


def is_jpeg(path: Path) -> bool:
    with path.open("rb") as f:
        head = f.read(3)
    return head[:3] == b"\xff\xd8\xff"


def main() -> None:
    files = sorted(POSTS_DIR.rglob("*.png"))
    targets = [p for p in files if is_jpeg(p)]
    if not targets:
        console.print("[green]All .png files already have PNG content.[/green]")
        return

    console.rule(f"[bold]Re-encoding {len(targets)} JPEG-as-PNG file(s)")
    converted = failed = 0
    for i, p in enumerate(targets, 1):
        try:
            with Image.open(p) as im:
                im.load()
                im.save(p, format="PNG")
            converted += 1
            if i % 25 == 0 or i == len(targets):
                console.print(f"  [{i:3}/{len(targets)}] ok  {p.relative_to(ROOT)}")
        except Exception as e:
            failed += 1
            console.print(f"  [{i:3}/{len(targets)}] FAIL {p.relative_to(ROOT)} — {e}")

    console.rule(f"[green]Done: {converted} re-encoded, {failed} failed")


if __name__ == "__main__":
    main()
