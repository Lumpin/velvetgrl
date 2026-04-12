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
    from agents.pinterest.api import check_token

    user = check_token()
    if user:
        console.print(f"[green]Connected as: {user.get('username', 'unknown')}[/green]")
    else:
        console.print("[red]Not authenticated. Run: python -m agents pin auth[/red]")


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


if __name__ == "__main__":
    cli()
