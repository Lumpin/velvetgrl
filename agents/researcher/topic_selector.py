import json
from agents.analytics.insights import category_performance, slot_allocation, top_pins
from agents.claude_client import get_claude_client, parse_json_response
from agents.db import get_connection


def select_topics(count: int = 4) -> list[dict]:
    """Pick the best topics for the week, biased by measured performance.

    Uses `slot_allocation` to split between top-performing categories and
    under-explored ones, so the system can't collapse to a single niche.
    """
    conn = get_connection()
    keywords = conn.execute(
        """SELECT keyword, category, search_volume_estimate, ad_value_score
           FROM keywords
           ORDER BY search_volume_estimate DESC, ad_value_score DESC
           LIMIT 80"""
    ).fetchall()
    # Already-published titles, grouped by category. Claude must avoid these.
    existing = conn.execute(
        "SELECT title, category FROM posts WHERE status IN ('published','approved','review')"
    ).fetchall()
    conn.close()

    perf = category_performance()
    allocation = slot_allocation(count, perf)
    winners = top_pins(limit=5)

    keyword_list = [dict(k) for k in keywords]
    existing_by_cat: dict[str, list[str]] = {}
    for row in existing:
        existing_by_cat.setdefault(row["category"], []).append(row["title"])

    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""You are a content strategist for velvetgrl, a women's lifestyle blog.

Pick {count} blog post topics for this week. Each should be a listicle.

== Available keywords (sorted by estimated search volume) ==
{json.dumps(keyword_list, indent=2)}

== Measured category performance ==
{json.dumps(perf, indent=2)}

== Slot allocation (this week) ==
- {allocation['performer_slots']} slots for top-performing categories: {allocation['top_categories']}
- {allocation['exploration_slots']} slots for under-explored categories (we need data): {allocation['explore_categories']}

== Top pins so far (use their patterns as inspiration) ==
{json.dumps(winners, indent=2)}

== ALREADY PUBLISHED — do NOT propose anything that overlaps with these ==
{json.dumps(existing_by_cat, indent=2)}

== Selection rules ==
1. Honor the slot allocation strictly: hit the performer / exploration counts.
2. Within performer slots, pick high-volume keywords from those categories.
3. Within exploration slots, pick the highest-volume keywords from those categories,
   even if the category has zero performance data yet (that's the point — we need data).
4. Listicle format: pick a specific number of items (13-31, odd numbers perform best).
5. **Topic uniqueness is critical.** Each new title must be clearly different from the
   ALREADY PUBLISHED list above — not just a swapped number or synonym. If a category
   only has near-duplicate options left, pick a *different sub-niche* of that category
   (e.g., if "blonde highlights on brown hair" exists, propose "money piece highlights"
   or "balayage for short hair" instead — different sub-topic, not a remix).

Return JSON array:
[{{"title": "23 Minimalist Tattoo Ideas for First-Timers", "category": "tattoo-ideas",
   "keywords": ["minimalist tattoo", "small tattoo"], "target_items": 23,
   "slot_type": "performer" | "exploration"}}]

Return ONLY the JSON array."""
        }]
    )
    topics = parse_json_response(response.content[0].text)
    return topics
