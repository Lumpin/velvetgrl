import json
from rich.console import Console
from agents.researcher.keyword_scraper import run_keyword_research
from agents.researcher.topic_selector import select_topics
from agents.researcher.calendar_generator import generate_weekly_calendar
from agents.writer.blog_writer import generate_blog_post, extract_image_prompts
from agents.image_sourcer.stock_photos import source_images_for_post
from agents.publisher.publish import publish_all_approved
from agents.pinterest.pin_generator import generate_pins_for_post, register_pins_in_db
from agents.pinterest.browser import post_pins_for_post
from agents.config import QUEUE_DIR

console = Console()


def run_research_phase() -> dict:
    """Phase 1: Research keywords and generate content calendar."""
    console.print("[cyan]Phase 1: Running keyword research...[/cyan]")
    run_keyword_research()

    console.print("[cyan]Phase 1: Selecting topics...[/cyan]")
    topics = select_topics(count=4)

    console.print("[cyan]Phase 1: Generating calendar...[/cyan]")
    calendar = generate_weekly_calendar(topics)

    console.print(f"[green]Research complete — {len(topics)} topics planned[/green]")
    return calendar


def run_writing_phase() -> list[str]:
    """Phase 2: Write blog posts for all pending calendar items."""
    calendar_path = QUEUE_DIR / "upcoming.json"
    if not calendar_path.exists():
        console.print("[yellow]No calendar found. Run research phase first.[/yellow]")
        return []

    calendar = json.loads(calendar_path.read_text())
    written = []

    for post in calendar["posts"]:
        if post["status"] != "draft":
            continue
        console.print(f"[cyan]Writing: {post['title']}[/cyan]")
        markdown = generate_blog_post(post)

        # Extract image references from the post and generate each one
        image_entries = extract_image_prompts(markdown)
        console.print(f"[cyan]Generating {len(image_entries)} images for: {post['slug']}[/cyan]")
        source_images_for_post(post["slug"], image_entries)

        post["status"] = "review"
        written.append(post["slug"])

    # Update calendar
    calendar_path.write_text(json.dumps(calendar, indent=2))
    console.print(f"[green]Writing complete — {len(written)} posts ready for review[/green]")
    return written


def run_publish_phase() -> list[str]:
    """Publish all approved posts."""
    console.print("[cyan]Publishing approved posts...[/cyan]")
    published = publish_all_approved()
    console.print(f"[green]Published {len(published)} posts[/green]")
    return published


def run_pinterest_phase(slugs: list[str]) -> int:
    """Phase 3: Generate and post pins for published posts."""
    total_posted = 0
    for slug in slugs:
        console.print(f"[cyan]Generating pins for: {slug}[/cyan]")
        # Get post info from DB
        from agents.db import get_connection
        conn = get_connection()
        post = conn.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()
        conn.close()

        if not post:
            continue

        pin_paths = generate_pins_for_post(slug, post["title"], post["category"], count=3)
        keywords = json.loads(post["keywords"].replace("'", '"')) if post["keywords"] else []
        register_pins_in_db(slug, pin_paths, post["title"], keywords, post["category"])

        console.print(f"[cyan]Posting pins for: {slug}[/cyan]")
        posted = post_pins_for_post(slug)
        total_posted += posted

    console.print(f"[green]Pinterest complete — {total_posted} pins posted[/green]")
    return total_posted


def run_full_cycle() -> None:
    """Run one complete pipeline cycle."""
    console.print("[bold]Starting full pipeline cycle...[/bold]")
    run_research_phase()
    run_writing_phase()
    console.print("[yellow]Posts queued for review. Approve with: python -m agents review approve <slug>[/yellow]")
