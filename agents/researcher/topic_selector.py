import json
from agents.claude_client import get_claude_client, parse_json_response
from agents.db import get_connection


def select_topics(count: int = 4) -> list[dict]:
    """Use Claude to pick the best topics for the week."""
    conn = get_connection()

    # Get top keywords not yet covered
    keywords = conn.execute(
        """SELECT keyword, category, search_volume_estimate, ad_value_score
           FROM keywords
           WHERE keyword NOT IN (SELECT title FROM posts)
           ORDER BY search_volume_estimate DESC, ad_value_score DESC
           LIMIT 50"""
    ).fetchall()

    # Get already published categories for balance
    published = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM posts WHERE status = 'published' GROUP BY category"
    ).fetchall()
    conn.close()

    keyword_list = [dict(k) for k in keywords]
    published_list = [dict(p) for p in published]

    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""You are a content strategist for velvetgrl, a women's lifestyle blog.

Pick {count} blog post topics for this week. Each should be a listicle.

Available keywords (sorted by search volume):
{json.dumps(keyword_list, indent=2)}

Already published post counts by category:
{json.dumps(published_list, indent=2)}

Selection criteria:
- High Pinterest search volume
- Mix of categories (don't repeat the same category unless it's clearly the top performer)
- Listicle-friendly (can be "N [adjective] [topic] ideas/designs/looks")
- Pick a specific number of items (between 13-31, odd numbers perform well)

Return JSON array:
[{{"title": "23 Minimalist Tattoo Ideas for First-Timers", "category": "tattoo-ideas", "keywords": ["minimalist tattoo", "small tattoo"], "target_items": 23}}]

Return ONLY the JSON array."""
        }]
    )
    topics = parse_json_response(response.content[0].text)
    return topics
