from agents.claude_client import get_claude_client, parse_json_response
from agents.config import CATEGORIES, load_categories
from agents.db import get_connection


def scrape_keyword_suggestions(category: str, seed_keywords: list[str]) -> list[dict]:
    """Use Claude to expand seed keywords into a list of Pinterest-worthy search terms."""
    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""You are a Pinterest keyword researcher for a women's lifestyle blog.

Category: {category}
Seed keywords: {', '.join(seed_keywords)}

Generate 20 high-volume Pinterest search terms for this category. For each keyword, estimate:
- search_volume: "high", "medium", or "low"
- competition: "high", "medium", or "low"
- ad_value: 1-10 score (how likely advertisers target this term)

Return as JSON array:
[{{"keyword": "...", "search_volume": "...", "competition": "...", "ad_value": 5}}]

Focus on specific, listicle-friendly terms (e.g., "minimalist wrist tattoo" not just "tattoo").
Return ONLY the JSON array, no other text."""
        }]
    )
    keywords = parse_json_response(response.content[0].text)
    return keywords


def update_keyword_database(category: str, keywords: list[dict]) -> None:
    """Store keywords in SQLite."""
    conn = get_connection()
    volume_map = {"high": 3, "medium": 2, "low": 1}
    for kw in keywords:
        conn.execute(
            """INSERT INTO keywords (keyword, category, search_volume_estimate, competition, ad_value_score)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(keyword) DO UPDATE SET
                 search_volume_estimate = excluded.search_volume_estimate,
                 competition = excluded.competition,
                 ad_value_score = excluded.ad_value_score,
                 last_updated = CURRENT_TIMESTAMP""",
            (kw["keyword"], category, volume_map.get(kw.get("search_volume", "low"), 1),
             kw.get("competition", "unknown"), kw.get("ad_value", 0))
        )
    conn.commit()
    conn.close()


def run_keyword_research() -> None:
    """Run keyword research for all categories."""
    categories = load_categories()
    for cat_slug, cat_data in categories.items():
        keywords = scrape_keyword_suggestions(cat_slug, cat_data["seed_keywords"])
        update_keyword_database(cat_slug, keywords)
