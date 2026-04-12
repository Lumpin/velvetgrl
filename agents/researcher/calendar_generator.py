import json
from datetime import datetime, timedelta
from agents.config import QUEUE_DIR, load_settings
from agents.db import get_connection


def generate_weekly_calendar(topics: list[dict]) -> dict:
    """Assign topics to publish dates for the week."""
    settings = load_settings()
    publish_days = settings.get("schedule", {}).get("publish_days", ["monday", "wednesday", "friday", "saturday"])

    today = datetime.now()
    # Find next Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0 and today.hour >= 12:
        days_until_monday = 7
    week_start = today + timedelta(days=days_until_monday)

    day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
    publish_dates = []
    for day_name in publish_days:
        offset = day_map[day_name]
        publish_dates.append(week_start + timedelta(days=offset))

    calendar = {
        "week": week_start.strftime("%Y-%m-%d"),
        "created_at": datetime.now().isoformat(),
        "posts": [],
    }

    for i, topic in enumerate(topics):
        date = publish_dates[i % len(publish_dates)]
        slug = topic["title"].lower()
        slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
        slug = slug.strip().replace(" ", "-")[:80]

        post = {
            **topic,
            "slug": slug,
            "publish_date": date.strftime("%Y-%m-%d"),
            "status": "draft",
        }
        calendar["posts"].append(post)

    # Save to queue
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    (QUEUE_DIR / "upcoming.json").write_text(json.dumps(calendar, indent=2))

    # Track in DB
    conn = get_connection()
    conn.execute(
        "INSERT INTO calendar (week, post_data) VALUES (?, ?)",
        (calendar["week"], json.dumps(calendar))
    )
    conn.commit()
    conn.close()

    return calendar
