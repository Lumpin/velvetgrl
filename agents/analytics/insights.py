"""Derive feedback signals from collected analytics.

Used by topic_selector to bias next week's content toward what works,
and by the weekly reporter to surface recommendations.
"""

from agents.config import CATEGORIES
from agents.db import get_connection

# A category must have at least this many total pin impressions before its CTR
# is treated as a reliable signal. Below it we treat the data as "thin".
MIN_IMPRESSIONS_FOR_SIGNAL = 200

# Share of next week's topics reserved for under-explored categories — the
# system never collapses to a single winner.
EXPLORATION_QUOTA = 0.20


def category_performance() -> list[dict]:
    """Per-category aggregates: posts, impressions, clicks, CTR, signal status."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT category,
                  COUNT(*) AS posts,
                  COALESCE(SUM(pinterest_impressions), 0) AS impressions,
                  COALESCE(SUM(pinterest_clicks), 0) AS clicks
           FROM posts
           WHERE status = 'published'
           GROUP BY category"""
    ).fetchall()
    conn.close()

    seen = set()
    out = []
    for r in rows:
        imps = int(r["impressions"] or 0)
        clicks = int(r["clicks"] or 0)
        ctr = (clicks / imps) if imps > 0 else 0.0
        out.append({
            "category": r["category"],
            "posts": int(r["posts"] or 0),
            "impressions": imps,
            "clicks": clicks,
            "ctr": ctr,
            "signal": "reliable" if imps >= MIN_IMPRESSIONS_FOR_SIGNAL else "thin",
        })
        seen.add(r["category"])

    # Include zero-data categories so the exploration policy can find them.
    for cat in CATEGORIES:
        if cat not in seen:
            out.append({
                "category": cat,
                "posts": 0,
                "impressions": 0,
                "clicks": 0,
                "ctr": 0.0,
                "signal": "thin",
            })

    return sorted(out, key=lambda r: (-r["ctr"], -r["impressions"]))


def exploration_categories(perf: list[dict] | None = None) -> list[str]:
    """Categories that need more data — bottom-tier by post count + impressions."""
    perf = perf or category_performance()
    # Lowest impressions first; tiebreak: fewer posts (we know least about them).
    ranked = sorted(perf, key=lambda r: (r["impressions"], r["posts"]))
    return [r["category"] for r in ranked]


def top_pins(limit: int = 5, category: str | None = None) -> list[dict]:
    """Pins with the highest impressions. Used as few-shot examples for the writer."""
    conn = get_connection()
    if category:
        rows = conn.execute(
            """SELECT p.title, p.board, p.impressions, p.clicks, po.category
               FROM pins p JOIN posts po ON po.slug = p.post_slug
               WHERE p.status = 'posted' AND po.category = ?
               ORDER BY p.impressions DESC LIMIT ?""",
            (category, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT p.title, p.board, p.impressions, p.clicks, po.category
               FROM pins p JOIN posts po ON po.slug = p.post_slug
               WHERE p.status = 'posted'
               ORDER BY p.impressions DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def slot_allocation(total_slots: int, perf: list[dict] | None = None) -> dict:
    """Split next week's topic slots between performers and exploration.

    Returns: {"performer_slots": int, "exploration_slots": int,
              "top_categories": [...], "explore_categories": [...]}
    """
    perf = perf or category_performance()
    explore_n = max(1, round(total_slots * EXPLORATION_QUOTA))
    performer_n = max(0, total_slots - explore_n)

    reliable = [p for p in perf if p["signal"] == "reliable"]
    # If we have no reliable data yet, treat the whole allocation as exploration.
    if not reliable:
        return {
            "performer_slots": 0,
            "exploration_slots": total_slots,
            "top_categories": [],
            "explore_categories": exploration_categories(perf)[:total_slots],
        }

    return {
        "performer_slots": performer_n,
        "exploration_slots": explore_n,
        "top_categories": [r["category"] for r in reliable[:performer_n]],
        "explore_categories": exploration_categories(perf)[:explore_n],
    }
