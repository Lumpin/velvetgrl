from rich.console import Console
from rich.table import Table
from agents.db import get_connection

console = Console()


def generate_weekly_report() -> str:
    """Generate a weekly performance report."""
    conn = get_connection()

    total_posts = conn.execute("SELECT COUNT(*) as cnt FROM posts WHERE status = 'published'").fetchone()["cnt"]
    total_pins = conn.execute("SELECT COUNT(*) as cnt FROM pins WHERE status = 'posted'").fetchone()["cnt"]
    total_views = conn.execute("SELECT COALESCE(SUM(pageviews), 0) as total FROM posts").fetchone()["total"]
    total_impressions = conn.execute("SELECT COALESCE(SUM(pinterest_impressions), 0) as total FROM posts").fetchone()["total"]

    top_posts = conn.execute(
        "SELECT slug, title, pageviews, pinterest_clicks FROM posts WHERE status = 'published' ORDER BY pageviews DESC LIMIT 5"
    ).fetchall()

    top_pins = conn.execute(
        "SELECT title, board, impressions, clicks FROM pins WHERE status = 'posted' ORDER BY impressions DESC LIMIT 5"
    ).fetchall()

    # Category performance
    categories = conn.execute(
        """SELECT category, COUNT(*) as posts, SUM(pageviews) as views, SUM(pinterest_clicks) as clicks
           FROM posts WHERE status = 'published' GROUP BY category ORDER BY views DESC"""
    ).fetchall()

    conn.close()

    # Build report
    report = f"""
=== velvetgrl Weekly Report ===

Published posts: {total_posts}
Total pins posted: {total_pins}
Total pageviews: {total_views:,}
Pinterest impressions: {total_impressions:,}

--- Top Posts ---
"""
    for p in top_posts:
        report += f"  {p['title']} — {p['pageviews']:,} views, {p['pinterest_clicks']:,} clicks\n"

    report += "\n--- Category Performance ---\n"
    for c in categories:
        report += f"  {c['category']}: {c['posts']} posts, {c['views'] or 0:,} views\n"

    # Recommendation
    if categories:
        top_cat = categories[0]["category"]
        report += f"\nRecommendation: Double down on {top_cat} content.\n"

    return report


def print_report() -> None:
    """Print the weekly report to console."""
    report = generate_weekly_report()
    console.print(report)
