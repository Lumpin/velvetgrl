import click
from rich.console import Console
from rich.table import Table

from agents.config import ensure_dirs, QUEUE_DIR
from agents.db import get_connection

console = Console()


@click.group()
def cli():
    """velvetgrl Autopilot — AI-powered content marketing pipeline."""
    ensure_dirs()


@cli.command("st")
def status():
    """Show system dashboard."""
    conn = get_connection()
    posts = conn.execute("SELECT status, COUNT(*) as cnt FROM posts GROUP BY status").fetchall()
    pins = conn.execute("SELECT status, COUNT(*) as cnt FROM pins GROUP BY status").fetchall()
    conn.close()

    table = Table(title="velvetgrl Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for row in posts:
        table.add_row(f"Posts ({row['status']})", str(row['cnt']))
    for row in pins:
        table.add_row(f"Pins ({row['status']})", str(row['cnt']))

    console.print(table)


@cli.group("rv")
def review():
    """Manage post review queue."""
    pass


@review.command("ls")
def review_list():
    """List posts waiting for review."""
    conn = get_connection()
    drafts = conn.execute(
        "SELECT slug, title, category, created_at FROM posts WHERE status = 'review' ORDER BY created_at"
    ).fetchall()
    conn.close()

    if not drafts:
        console.print("[dim]No posts waiting for review.[/dim]")
        return

    table = Table(title="Posts Awaiting Review")
    table.add_column("Slug", style="cyan")
    table.add_column("Title")
    table.add_column("Category", style="green")
    table.add_column("Created", style="dim")

    for d in drafts:
        table.add_row(d["slug"], d["title"], d["category"], d["created_at"])

    console.print(table)


@review.command("ok")
@click.argument("slug")
def review_approve(slug: str):
    """Approve a post for publishing."""
    conn = get_connection()
    result = conn.execute("UPDATE posts SET status = 'approved' WHERE slug = ? AND status = 'review'", (slug,))
    conn.commit()
    conn.close()

    if result.rowcount:
        console.print(f"[green]Approved:[/green] {slug}")
    else:
        console.print(f"[red]Not found or not in review:[/red] {slug}")


@review.command("ok-all")
def review_approve_all():
    """Approve all posts waiting for review."""
    conn = get_connection()
    result = conn.execute("UPDATE posts SET status = 'approved' WHERE status = 'review'")
    conn.commit()
    count = result.rowcount
    conn.close()

    if count:
        console.print(f"[green]Approved {count} post(s).[/green]")
    else:
        console.print("[dim]No posts waiting for review.[/dim]")


@review.command("no")
@click.argument("slug")
@click.option("--note", "-n", default="", help="Rejection reason")
def review_reject(slug: str, note: str):
    """Reject a post with optional feedback."""
    conn = get_connection()
    result = conn.execute("UPDATE posts SET status = 'rejected' WHERE slug = ? AND status = 'review'", (slug,))
    conn.commit()
    conn.close()

    if result.rowcount:
        console.print(f"[yellow]Rejected:[/yellow] {slug}")
        if note:
            console.print(f"[dim]Note: {note}[/dim]")
    else:
        console.print(f"[red]Not found or not in review:[/red] {slug}")


@cli.command("rpt")
def report():
    """Show weekly analytics report."""
    from agents.analytics.reporter import print_report
    print_report()


@cli.command("collect")
@click.option("--days", "-d", type=int, default=90, help="Pull metrics for the last N days (max 90)")
def collect(days: int):
    """Pull Pinterest analytics into the local DB."""
    from agents.analytics.collector import run_weekly_collection, backfill_pinterest_ids, collect_all_pin_metrics

    console.print("[cyan]Backfilling missing Pinterest pin IDs...[/cyan]")
    backfilled = backfill_pinterest_ids()
    console.print(f"  Backfilled: {backfilled}")

    console.print(f"[cyan]Fetching analytics (last {days} days)...[/cyan]")
    result = collect_all_pin_metrics(days=days)
    console.print(
        f"[green]Fetched {result['fetched']} pins, {result['errors']} errors.[/green]"
    )


@cli.command("insights")
def insights_cmd():
    """Show category performance + next-week slot allocation."""
    from agents.analytics.insights import category_performance, slot_allocation, top_pins

    perf = category_performance()
    table = Table(title="Category Performance")
    table.add_column("Category", style="cyan")
    table.add_column("Posts", justify="right")
    table.add_column("Impressions", justify="right")
    table.add_column("Clicks", justify="right")
    table.add_column("CTR", justify="right")
    table.add_column("Signal")
    for c in perf:
        table.add_row(
            c["category"], str(c["posts"]),
            f"{c['impressions']:,}", f"{c['clicks']:,}",
            f"{c['ctr']*100:.2f}%" if c["impressions"] else "—",
            c["signal"],
        )
    console.print(table)

    from agents.config import load_settings
    posts_per_week = (load_settings().get("schedule") or {}).get("posts_per_week", 4)
    alloc = slot_allocation(posts_per_week, perf)
    console.print(f"\n[bold]Next week's slot plan ({posts_per_week} posts):[/bold]")
    console.print(f"  Performer slots ({alloc['performer_slots']}): {alloc['top_categories'] or '—'}")
    console.print(f"  Exploration slots ({alloc['exploration_slots']}): {alloc['explore_categories'] or '—'}")

    pins = top_pins(limit=5)
    if pins and any(p["impressions"] for p in pins):
        console.print("\n[bold]Top pins so far:[/bold]")
        for p in pins:
            console.print(f"  [{p['board']}] {p['title'][:60]} — {p['impressions']:,} imp / {p['clicks']:,} clicks")


@cli.command("run")
@click.option("--once", is_flag=True, help="Run one cycle and exit")
def run(once: bool):
    """Start the full orchestrator (research → write → review → publish)."""
    from agents.orchestrator.pipeline import run_full_cycle
    from agents.orchestrator.scheduler import create_scheduler

    if once:
        console.print("[bold]Running single pipeline cycle...[/bold]")
        run_full_cycle()
    else:
        console.print("[bold]Starting velvetgrl Autopilot...[/bold]")
        scheduler = create_scheduler()
        try:
            scheduler.start()
        except KeyboardInterrupt:
            console.print("[yellow]Shutting down...[/yellow]")


@cli.command("pub")
def publish():
    """Publish all approved posts (no research/writing)."""
    from agents.orchestrator.pipeline import run_publish_phase
    run_publish_phase()


@cli.command()
def pins():
    """Generate and post pins for all published posts that don't have pins yet."""
    import json
    from agents.orchestrator.pipeline import run_pinterest_phase
    conn = get_connection()
    slugs = [r["slug"] for r in conn.execute(
        "SELECT slug FROM posts WHERE status = 'published' AND slug NOT IN (SELECT DISTINCT post_slug FROM pins)"
    ).fetchall()]
    conn.close()

    if not slugs:
        console.print("[dim]No published posts without pins.[/dim]")
        return

    console.print(f"Generating pins for {len(slugs)} post(s)...")
    run_pinterest_phase(slugs)


@cli.group("pin")
def pinterest():
    """Pinterest automation commands."""
    pass


@pinterest.command("auth")
def pinterest_auth():
    """Authenticate with Pinterest API (OAuth flow)."""
    from agents.pinterest.api import run_oauth_flow, check_token

    try:
        tokens = run_oauth_flow()
        user = check_token()
        username = user.get("username", "unknown") if user else "unknown"
        console.print(f"[green]Authenticated as: {username}[/green]")
    except Exception as e:
        console.print(f"[red]Auth failed: {e}[/red]")


@pinterest.command("test")
def pinterest_test():
    """Test Pinterest API connection."""
    from agents.pinterest.api import check_token, _load_tokens

    user = check_token()
    if user:
        username = user.get("username", "unknown")
        console.print(f"[green]Connected as:[/green] {username}")
        return

    if _load_tokens():
        console.print("[red]Token is invalid or expired.[/red] Re-authenticate: python -m agents pin auth")
    else:
        console.print("[red]No token found.[/red] Authenticate: python -m agents pin auth")


@pinterest.command("boards")
def pinterest_boards():
    """List all Pinterest boards."""
    from agents.pinterest.api import get_boards

    try:
        boards = get_boards()
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        return

    if not boards:
        console.print("[dim]No boards found.[/dim]")
        return

    table = Table(title="Pinterest Boards")
    table.add_column("Name", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Pins", style="green")

    for b in boards:
        table.add_row(b["name"], b["id"], str(b.get("pin_count", 0)))

    console.print(table)


@pinterest.command("post")
@click.argument("slug")
def pinterest_post(slug: str):
    """Manually post pins for a blog post."""
    from agents.pinterest.browser import post_pins_for_post
    posted = post_pins_for_post(slug)
    console.print(f"[green]Posted {posted} pins for {slug}[/green]")


@pinterest.command("refresh")
@click.option("--slug", "-s", default=None, help="Refresh pins for one slug only")
@click.option("--dry-run", is_flag=True, help="Show changes without calling Pinterest")
@click.option("--limit", "-n", type=int, default=None, help="Cap number of posts processed")
def pinterest_refresh(slug: str | None, dry_run: bool, limit: int | None):
    """Regenerate copy for already-posted pins and PATCH them on Pinterest.

    Note: PATCH requires the Pinterest pin_edit permission (app review). For
    accounts without it, use `pin recreate` instead, which deletes + reposts.
    """
    from agents.pinterest.refresh import refresh_all, refresh_post_pins
    if slug:
        out = refresh_post_pins(slug, dry_run=dry_run)
        console.print(f"[green]Refreshed {out['refreshed']} pin(s) for {slug}[/green]")
    else:
        out = refresh_all(dry_run=dry_run, limit=limit)
        console.print(f"[green]Refreshed {out['refreshed_pins']} pin(s) across {out['posts']} post(s)[/green]")


@pinterest.command("recreate")
@click.argument("slugs", nargs=-1)
@click.option("--dry-run", is_flag=True, help="Show what would change without touching Pinterest")
def pinterest_recreate(slugs: tuple[str, ...], dry_run: bool):
    """Delete + repost all pins for the given post slugs.

    Reuses existing background images on disk (no Flux regeneration). The new
    prompt produces 3 distinct angles per post. Pin IDs change; analytics reset.
    """
    from agents.pinterest.refresh import recreate_post_pins
    if not slugs:
        console.print("[red]Provide at least one slug.[/red]")
        return
    total = 0
    for slug in slugs:
        console.print(f"\n[cyan]Recreating: {slug}[/cyan]")
        out = recreate_post_pins(slug, dry_run=dry_run)
        if "error" in out:
            console.print(f"  [red]{out['error']}[/red]")
        else:
            console.print(f"  Recreated: {out.get('recreated', 0)}")
            total += out.get("recreated", 0)
    console.print(f"\n[green]Recreated {total} pin(s) total.[/green]")


@pinterest.command("post-all")
@click.option("--limit", "-n", type=int, default=None, help="Max pins to post across all posts")
@click.option("--dry-run", is_flag=True, help="Show what would be posted without actually posting")
def pinterest_post_all(limit: int | None, dry_run: bool):
    """Post all pending pins across every blog post via the Pinterest API."""
    from agents.pinterest.browser import post_pins_for_post
    conn = get_connection()
    rows = conn.execute(
        "SELECT post_slug, COUNT(*) AS n FROM pins WHERE status='pending' GROUP BY post_slug ORDER BY post_slug"
    ).fetchall()
    conn.close()

    if not rows:
        console.print("[dim]No pending pins.[/dim]")
        return

    table = Table(title="Pending Pins")
    table.add_column("Slug", style="cyan")
    table.add_column("Count", style="green")
    for r in rows:
        table.add_row(r["post_slug"], str(r["n"]))
    console.print(table)

    if dry_run:
        console.print("[yellow]Dry run — nothing posted.[/yellow]")
        return

    total_posted = 0
    for r in rows:
        if limit is not None and total_posted >= limit:
            break
        console.print(f"\n[cyan]Posting pins for: {r['post_slug']}[/cyan]")
        total_posted += post_pins_for_post(r["post_slug"])

    console.print(f"\n[green]Posted {total_posted} pin(s) total.[/green]")


if __name__ == "__main__":
    cli()
