"""Analytics collector — pulls Pinterest metrics into the DB and aggregates.

Runs weekly (Sunday morning) or on-demand via `python -m agents collect`.
"""

from datetime import datetime
from agents.analytics.pinterest_metrics import fetch_pin_analytics_bulk
from agents.db import get_connection


def record_post_metrics(slug: str, pageviews: int, pinterest_impressions: int = 0, pinterest_clicks: int = 0) -> None:
    """Update post metrics in the database (manual entry point — kept for back-compat)."""
    conn = get_connection()
    conn.execute(
        """UPDATE posts SET pageviews = ?, pinterest_impressions = ?, pinterest_clicks = ?
           WHERE slug = ?""",
        (pageviews, pinterest_impressions, pinterest_clicks, slug)
    )
    conn.commit()
    conn.close()


def record_pin_metrics(pin_id: int, impressions: int, saves: int, clicks: int) -> None:
    """Update pin metrics in the database (manual entry point — kept for back-compat)."""
    conn = get_connection()
    conn.execute(
        "UPDATE pins SET impressions = ?, saves = ?, clicks = ? WHERE id = ?",
        (impressions, saves, clicks, pin_id)
    )
    conn.commit()
    conn.close()


def backfill_pinterest_ids() -> int:
    """Match posted pins lacking pinterest_pin_id to live pins on the account.

    Two passes:
      1. Exact title match (only when the title is unique among live pins).
      2. Destination link + board, zipped in posting order — handles the case
         where one post produced multiple pins with near-identical titles to
         the same board.

    Returns the number of rows backfilled.
    """
    from agents.pinterest.api import list_pins
    from agents.config import load_settings

    conn = get_connection()
    missing = conn.execute(
        "SELECT id, title, board, post_slug FROM pins "
        "WHERE status='posted' AND pinterest_pin_id IS NULL ORDER BY id"
    ).fetchall()
    if not missing:
        conn.close()
        return 0

    claimed = {
        row["pinterest_pin_id"]
        for row in conn.execute(
            "SELECT pinterest_pin_id FROM pins WHERE pinterest_pin_id IS NOT NULL"
        )
    }
    live = [p for p in list_pins() if p.get("id") not in claimed]

    # Pass 1: unique-title match.
    by_title: dict[str, list[dict]] = {}
    for p in live:
        title = (p.get("title") or "").strip()
        if title:
            by_title.setdefault(title, []).append(p)

    matched = 0
    still_missing = []
    for row in missing:
        candidates = by_title.get((row["title"] or "").strip(), [])
        if len(candidates) == 1:
            pid = candidates[0]["id"]
            conn.execute(
                "UPDATE pins SET pinterest_pin_id = ? WHERE id = ?",
                (pid, row["id"]),
            )
            claimed.add(pid)
            matched += 1
        else:
            still_missing.append(row)

    # Pass 2: zip by destination link. Pinterest's /pins endpoint doesn't
    # return board.name by default, so we can't filter on it cheaply — but the
    # blog post link is unique enough to disambiguate.
    if still_missing:
        site_url = load_settings().get("site_url", "https://velvetgrl.com")
        bucket: dict[str, list[dict]] = {}
        for p in live:
            if p.get("id") in claimed:
                continue
            link = p.get("link") or ""
            if link:
                bucket.setdefault(link, []).append(p)
        for link, items in bucket.items():
            # Oldest first, so we zip in posting order against DB rows sorted by id.
            items.sort(key=lambda x: x.get("created_at") or "")

        for row in still_missing:
            expected_link = f"{site_url}/blog/{row['post_slug']}/"
            queue = bucket.get(expected_link) or []
            picked = next((p for p in queue if p["id"] not in claimed), None)
            if picked:
                conn.execute(
                    "UPDATE pins SET pinterest_pin_id = ? WHERE id = ?",
                    (picked["id"], row["id"]),
                )
                claimed.add(picked["id"])
                matched += 1

    conn.commit()
    conn.close()
    return matched


def collect_all_pin_metrics(days: int = 90) -> dict:
    """Pull analytics for every posted pin with a known pinterest_pin_id.

    Returns a summary dict with counts. Skips pins with no pinterest_pin_id
    (caller should run backfill_pinterest_ids first).
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, pinterest_pin_id FROM pins WHERE status='posted' AND pinterest_pin_id IS NOT NULL"
    ).fetchall()

    if not rows:
        conn.close()
        return {"fetched": 0, "errors": 0, "skipped": 0}

    pin_ids = [r["pinterest_pin_id"] for r in rows]
    metrics = fetch_pin_analytics_bulk(pin_ids, days=days)

    now = datetime.now().isoformat()
    fetched = errors = 0
    for row in rows:
        m = metrics.get(row["pinterest_pin_id"], {})
        if "error" in m:
            errors += 1
            continue
        conn.execute(
            """UPDATE pins SET impressions = ?, saves = ?, clicks = ?, metrics_updated_at = ?
               WHERE id = ?""",
            (m["impressions"], m["saves"], m["outbound_clicks"], now, row["id"]),
        )
        fetched += 1
    conn.commit()
    conn.close()

    aggregate_post_metrics()
    return {"fetched": fetched, "errors": errors, "skipped": 0}


def aggregate_post_metrics() -> None:
    """Roll pin-level metrics up to post-level totals."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT post_slug,
                  COALESCE(SUM(impressions), 0) AS imps,
                  COALESCE(SUM(clicks), 0) AS clicks
           FROM pins
           WHERE status = 'posted'
           GROUP BY post_slug"""
    ).fetchall()
    for r in rows:
        conn.execute(
            "UPDATE posts SET pinterest_impressions = ?, pinterest_clicks = ? WHERE slug = ?",
            (r["imps"], r["clicks"], r["post_slug"]),
        )
    conn.commit()
    conn.close()


def run_weekly_collection() -> dict:
    """The job the scheduler calls every Sunday morning."""
    backfilled = backfill_pinterest_ids()
    result = collect_all_pin_metrics()
    result["backfilled"] = backfilled
    return result
