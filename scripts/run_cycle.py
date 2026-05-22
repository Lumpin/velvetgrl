"""Run a full pipeline cycle starting from the existing queue/upcoming.json.

Skips research (the calendar is already built). Steps:
  1. writing — Claude drafts each post + Flux generates images
  2. auto-approve — flip status from 'review' to 'approved'
  3. publish — copy MD into website/, git commit + push
  4. pinterest — generate 3 angle-aware pin variations per post and post via API
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rich.console import Console

from agents.config import QUEUE_DIR
from agents.db import get_connection
from agents.orchestrator.pipeline import (
    run_pinterest_phase,
    run_publish_phase,
    run_writing_phase,
)

console = Console()


def auto_approve() -> int:
    conn = get_connection()
    result = conn.execute("UPDATE posts SET status='approved' WHERE status='review'")
    conn.commit()
    n = result.rowcount
    conn.close()
    return n


def main() -> None:
    calendar_path = QUEUE_DIR / "upcoming.json"
    if not calendar_path.exists():
        console.print("[red]No calendar at queue/upcoming.json. Run select_topics first.[/red]")
        sys.exit(1)
    cal = json.loads(calendar_path.read_text())
    drafts = [p for p in cal["posts"] if p["status"] == "draft"]
    console.rule(f"[bold]Pipeline cycle: {len(drafts)} draft(s) to write")

    console.rule("[cyan]1/4 Writing")
    written = run_writing_phase()
    console.print(f"  Drafted: {len(written)} — {written}")

    console.rule("[cyan]2/4 Auto-approving")
    approved = auto_approve()
    console.print(f"  Approved: {approved}")

    console.rule("[cyan]3/4 Publishing + git push")
    published = run_publish_phase()
    console.print(f"  Published: {len(published)} — {published}")

    if published:
        console.rule("[cyan]4/4 Generating + posting pins")
        n = run_pinterest_phase(published)
        console.print(f"  Pins posted: {n}")
    else:
        console.print("[yellow]Nothing published — skipping Pinterest phase.[/yellow]")

    console.rule("[green]Cycle complete")


if __name__ == "__main__":
    main()
