from datetime import datetime
from agents.db import get_connection


def record_post_metrics(slug: str, pageviews: int, pinterest_impressions: int = 0, pinterest_clicks: int = 0) -> None:
    """Update post metrics in the database."""
    conn = get_connection()
    conn.execute(
        """UPDATE posts SET pageviews = ?, pinterest_impressions = ?, pinterest_clicks = ?
           WHERE slug = ?""",
        (pageviews, pinterest_impressions, pinterest_clicks, slug)
    )
    conn.commit()
    conn.close()


def record_pin_metrics(pin_id: int, impressions: int, saves: int, clicks: int) -> None:
    """Update pin metrics in the database."""
    conn = get_connection()
    conn.execute(
        "UPDATE pins SET impressions = ?, saves = ?, clicks = ? WHERE id = ?",
        (impressions, saves, clicks, pin_id)
    )
    conn.commit()
    conn.close()
