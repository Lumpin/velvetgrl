from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from rich.console import Console
from agents.config import load_settings
from agents.orchestrator.pipeline import (
    run_research_phase,
    run_writing_phase,
    run_publish_phase,
    run_pinterest_phase,
)

console = Console()


def create_scheduler() -> BlockingScheduler:
    """Create and configure the APScheduler instance."""
    settings = load_settings()
    schedule = settings.get("schedule", {})

    scheduler = BlockingScheduler()

    # Research: weekly on configured day
    researcher_day = schedule.get("researcher_day", "monday")
    researcher_hour = schedule.get("researcher_hour", 6)
    scheduler.add_job(
        run_research_phase,
        CronTrigger(day_of_week=_day_abbrev(researcher_day), hour=researcher_hour),
        id="research",
        name="Weekly Research",
    )

    # Writing: Mon-Sat at configured hour
    writer_hour = schedule.get("writer_hour", 7)
    scheduler.add_job(
        run_writing_phase,
        CronTrigger(day_of_week="mon-sat", hour=writer_hour),
        id="writing",
        name="Daily Writing",
    )

    # Publishing: check every 30 min for approved posts
    scheduler.add_job(
        _publish_and_pin,
        CronTrigger(minute="*/30"),
        id="publish_check",
        name="Publish Check",
    )

    # Analytics: weekly on Sunday
    analytics_day = schedule.get("analytics_day", "sunday")
    scheduler.add_job(
        _run_analytics,
        CronTrigger(day_of_week=_day_abbrev(analytics_day), hour=20),
        id="analytics",
        name="Weekly Analytics",
    )

    return scheduler


def _publish_and_pin() -> None:
    """Publish approved posts and trigger Pinterest."""
    published = run_publish_phase()
    if published:
        run_pinterest_phase(published)


def _run_analytics() -> None:
    """Run analytics collection (placeholder)."""
    console.print("[cyan]Analytics collection — not yet implemented[/cyan]")


def _day_abbrev(day: str) -> str:
    """Convert day name to APScheduler abbreviation."""
    mapping = {
        "monday": "mon", "tuesday": "tue", "wednesday": "wed",
        "thursday": "thu", "friday": "fri", "saturday": "sat", "sunday": "sun",
    }
    return mapping.get(day.lower(), day[:3].lower())
