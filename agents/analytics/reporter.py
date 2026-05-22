"""Weekly performance reporter.

Reads metrics that the collector has already populated. Surfaces:
 - aggregate counts
 - top posts and pins by impressions
 - per-category CTR with a 'thin data' marker
 - the recommended slot allocation for next week
"""

from rich.console import Console
from rich.table import Table

from agents.analytics.insights import (
    EXPLORATION_QUOTA,
    MIN_IMPRESSIONS_FOR_SIGNAL,
    category_performance,
    slot_allocation,
    top_pins,
)
from agents.config import load_settings
from agents.db import get_connection

console = Console()


def print_report() -> None:
    """Render the weekly report directly to the console."""
    conn = get_connection()
    totals = conn.execute(
        """SELECT
              (SELECT COUNT(*) FROM posts WHERE status='published')              AS posts,
              (SELECT COUNT(*) FROM pins  WHERE status='posted')                 AS pins,
              (SELECT COALESCE(SUM(pageviews), 0)              FROM posts)       AS views,
              (SELECT COALESCE(SUM(pinterest_impressions), 0)  FROM posts)       AS imps,
              (SELECT COALESCE(SUM(pinterest_clicks), 0)       FROM posts)       AS clicks"""
    ).fetchone()

    top_posts_rows = conn.execute(
        """SELECT title, category, pinterest_impressions, pinterest_clicks
           FROM posts WHERE status='published'
           ORDER BY pinterest_impressions DESC LIMIT 5"""
    ).fetchall()
    conn.close()

    settings = load_settings()
    posts_per_week = (settings.get("schedule") or {}).get("posts_per_week", 4)

    console.rule("[bold]velvetgrl weekly report")
    console.print(
        f"  Posts: {totals['posts']}   Pins: {totals['pins']}   "
        f"Pinterest impressions: {totals['imps']:,}   Outbound clicks: {totals['clicks']:,}"
    )

    perf = category_performance()
    cat_table = Table(title=f"Category performance (signal threshold: {MIN_IMPRESSIONS_FOR_SIGNAL:,} impressions)")
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Posts", justify="right")
    cat_table.add_column("Impressions", justify="right")
    cat_table.add_column("Clicks", justify="right")
    cat_table.add_column("CTR", justify="right")
    cat_table.add_column("Signal")
    for c in perf:
        signal_style = "green" if c["signal"] == "reliable" else "yellow"
        cat_table.add_row(
            c["category"],
            str(c["posts"]),
            f"{c['impressions']:,}",
            f"{c['clicks']:,}",
            f"{c['ctr']*100:.2f}%" if c["impressions"] else "—",
            f"[{signal_style}]{c['signal']}[/{signal_style}]",
        )
    console.print(cat_table)

    if top_posts_rows:
        post_table = Table(title="Top posts by Pinterest impressions")
        post_table.add_column("Title")
        post_table.add_column("Category", style="cyan")
        post_table.add_column("Impressions", justify="right")
        post_table.add_column("Clicks", justify="right")
        for p in top_posts_rows:
            post_table.add_row(
                p["title"][:60],
                p["category"],
                f"{p['pinterest_impressions']:,}",
                f"{p['pinterest_clicks']:,}",
            )
        console.print(post_table)

    pins_rows = top_pins(limit=5)
    if pins_rows and any(p["impressions"] for p in pins_rows):
        pin_table = Table(title="Top pins by impressions")
        pin_table.add_column("Title")
        pin_table.add_column("Board", style="cyan")
        pin_table.add_column("Impressions", justify="right")
        pin_table.add_column("Clicks", justify="right")
        for p in pins_rows:
            pin_table.add_row(p["title"][:60], p["board"], f"{p['impressions']:,}", f"{p['clicks']:,}")
        console.print(pin_table)

    alloc = slot_allocation(posts_per_week, perf)
    console.rule("[bold]Next week's plan")
    console.print(
        f"  {alloc['performer_slots']}/{posts_per_week} performer slots (categories with reliable data): "
        f"{', '.join(alloc['top_categories']) or '—'}"
    )
    console.print(
        f"  {alloc['exploration_slots']}/{posts_per_week} exploration slots "
        f"({int(EXPLORATION_QUOTA*100)}% reserved): {', '.join(alloc['explore_categories']) or '—'}"
    )
    if not alloc["top_categories"]:
        console.print("[dim]No reliable signal yet — running pure exploration until impressions accumulate.[/dim]")


def generate_weekly_report() -> str:
    """Legacy string-returning version. The CLI uses print_report directly."""
    from io import StringIO
    from rich.console import Console as _C

    buf = StringIO()
    c = _C(file=buf, force_terminal=False)
    global console
    real = console
    console = c
    try:
        print_report()
    finally:
        console = real
    return buf.getvalue()
