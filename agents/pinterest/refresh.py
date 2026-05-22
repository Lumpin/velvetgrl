"""Refresh existing pins.

Two strategies:
 - `refresh_post_pins` PATCHes the pin in place (needs Pinterest pin_edit perm)
 - `recreate_post_pins` deletes + reposts with the new prompt. Reuses existing
   background images on disk so no Flux image regeneration is needed.
"""

import json
from pathlib import Path

from PIL import Image

from agents.config import DATA_DIR, load_settings
from agents.db import get_connection
from agents.pinterest.api import delete_pin, update_pin
from agents.pinterest.browser import _build_description, create_pin as api_post_pin
from agents.pinterest.pin_generator import (
    create_pin_collage,
    generate_pin_copy,
    generate_pin_title,
)


def _category_for(slug: str, conn) -> str:
    row = conn.execute("SELECT category FROM posts WHERE slug = ?", (slug,)).fetchone()
    return row["category"] if row else ""


def _keywords_for(slug: str, conn) -> list[str]:
    row = conn.execute("SELECT keywords FROM posts WHERE slug = ?", (slug,)).fetchone()
    if not row or not row["keywords"]:
        return []
    raw = row["keywords"].replace("'", '"')
    try:
        return json.loads(raw)
    except Exception:
        return []


def refresh_post_pins(slug: str, dry_run: bool = False) -> dict:
    """Refresh all posted pins for one blog post. Each variation gets a distinct angle."""
    conn = get_connection()
    pins = conn.execute(
        """SELECT id, pinterest_pin_id, title, description, board
           FROM pins
           WHERE post_slug = ? AND status = 'posted' AND pinterest_pin_id IS NOT NULL
           ORDER BY id""",
        (slug,),
    ).fetchall()

    if not pins:
        conn.close()
        return {"slug": slug, "refreshed": 0, "skipped": 0}

    category = _category_for(slug, conn)
    keywords = _keywords_for(slug, conn)
    # Use blog post title (not pin title) as the source so each variation is generated fresh.
    post_row = conn.execute("SELECT title FROM posts WHERE slug = ?", (slug,)).fetchone()
    base_title = post_row["title"] if post_row else (pins[0]["title"] if pins else slug)

    refreshed = 0
    prior_copy: list[dict] = []
    for i, pin in enumerate(pins):
        copy = generate_pin_copy(
            base_title, keywords, category,
            variation_index=i,
            previous_copy=prior_copy,
        )
        prior_copy.append(copy)
        new_title = (copy.get("pin_title") or "")[:100]
        tags = copy.get("tags", [])
        new_desc = _build_description(copy.get("pin_description", ""), tags)

        if dry_run:
            print(f"  [dry] id={pin['id']} pin={pin['pinterest_pin_id']}")
            print(f"    old title: {pin['title']}")
            print(f"    new title: {new_title}")
            continue

        try:
            update_pin(pin["pinterest_pin_id"], title=new_title, description=new_desc)
        except Exception as e:
            print(f"  ! Pinterest update failed for {pin['pinterest_pin_id']}: {e}")
            continue

        conn.execute(
            "UPDATE pins SET title = ?, description = ?, tags = ? WHERE id = ?",
            (new_title, new_desc, json.dumps(tags), pin["id"]),
        )
        conn.commit()
        refreshed += 1

    conn.close()
    return {"slug": slug, "refreshed": refreshed}


def recreate_post_pins(slug: str, dry_run: bool = False) -> dict:
    """Delete every posted pin for a slug, then re-render + repost using the new prompt.

    Reuses existing background images at data/pins/<slug>/v<i>/*.png so we don't
    pay for Flux regeneration. Loses Pinterest pin IDs (replaced with new ones).
    """
    conn = get_connection()
    pins = conn.execute(
        """SELECT id, pinterest_pin_id, board
           FROM pins
           WHERE post_slug = ? AND status = 'posted' AND pinterest_pin_id IS NOT NULL
           ORDER BY id""",
        (slug,),
    ).fetchall()
    if not pins:
        conn.close()
        return {"slug": slug, "recreated": 0}

    post = conn.execute("SELECT title, category FROM posts WHERE slug = ?", (slug,)).fetchone()
    if not post:
        conn.close()
        return {"slug": slug, "recreated": 0, "error": "no post row"}

    base_title = post["title"]
    category = post["category"]
    keywords = _keywords_for(slug, conn)
    settings = load_settings()
    site_url = settings.get("site_url", "https://velvetgrl.com")
    post_url = f"{site_url}/blog/{slug}/"

    pins_dir = DATA_DIR / "pins" / slug
    accent_colors = ["#F4C2C2", "#B2C9AB", "#C9A96E", "#A8C4D9", "#D4A5A5"]

    if dry_run:
        for i, pin in enumerate(pins):
            t = generate_pin_title(base_title, category, variation_index=i, previous_titles=[])
            print(f"  [dry] would replace {pin['pinterest_pin_id']} -> {t.get('line1')} {t.get('line2')}")
        conn.close()
        return {"slug": slug, "recreated": 0, "dry_run": True}

    # Step 1: delete the old pins on Pinterest, then drop the DB rows.
    for pin in pins:
        try:
            delete_pin(pin["pinterest_pin_id"])
        except Exception as e:
            print(f"  ! could not delete {pin['pinterest_pin_id']}: {e}")
    conn.execute(
        "DELETE FROM pins WHERE post_slug = ? AND status = 'posted'",
        (slug,),
    )
    conn.commit()

    # Step 2: re-render + repost each variation.
    used_titles: list[str] = []
    prior_copy: list[dict] = []
    recreated = 0
    for i, pin in enumerate(pins):
        variation_dir = pins_dir / f"v{i}"
        bg_files = sorted(variation_dir.glob("*.png"))[:4]
        if len(bg_files) < 4:
            print(f"  ! missing background images for variation {i} in {variation_dir}")
            continue

        title_info = generate_pin_title(
            base_title, category,
            variation_index=i, previous_titles=used_titles,
        )
        used_titles.append(f"{title_info.get('line1','')} {title_info.get('line2','')}".strip())

        images = [Image.open(p) for p in bg_files]
        collage = create_pin_collage(
            images=images,
            number=title_info["number"],
            title_lines=[title_info["line1"], title_info["line2"]],
            highlight_word=title_info["highlight_word"],
            accent_color=accent_colors[i % len(accent_colors)],
        )
        out_path = pins_dir / f"pin_v{i}.png"
        collage.save(out_path, "PNG", quality=95)
        for img in images:
            img.close()

        copy = generate_pin_copy(
            base_title, keywords, category,
            variation_index=i, previous_copy=prior_copy,
        )
        prior_copy.append(copy)
        new_title = (copy.get("pin_title") or "")[:100]
        tags = copy.get("tags", [])
        new_desc = _build_description(copy.get("pin_description", ""), tags)

        new_pin_id = api_post_pin(
            image_path=out_path,
            title=new_title,
            description=new_desc,
            board=pin["board"],
            url=post_url,
        )
        if not new_pin_id:
            print(f"  ! failed to repost variation {i}")
            continue

        conn.execute(
            """INSERT INTO pins
               (post_slug, image_path, title, description, board, tags, status, posted_at, pinterest_pin_id)
               VALUES (?, ?, ?, ?, ?, ?, 'posted', CURRENT_TIMESTAMP, ?)""",
            (slug, str(out_path), new_title, new_desc, pin["board"], json.dumps(tags), new_pin_id),
        )
        conn.commit()
        recreated += 1

    conn.close()
    return {"slug": slug, "recreated": recreated}


def refresh_all(dry_run: bool = False, limit: int | None = None) -> dict:
    """Refresh every posted pin grouped by post."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT DISTINCT post_slug
           FROM pins
           WHERE status='posted' AND pinterest_pin_id IS NOT NULL
           ORDER BY post_slug"""
    ).fetchall()
    conn.close()

    total = 0
    for i, r in enumerate(rows):
        if limit is not None and i >= limit:
            break
        print(f"[{r['post_slug']}]")
        out = refresh_post_pins(r["post_slug"], dry_run=dry_run)
        total += out["refreshed"]
    return {"posts": len(rows), "refreshed_pins": total}
