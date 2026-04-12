import re
from pathlib import Path
from agents.claude_client import get_claude_client
from agents.config import QUEUE_DIR, CATEGORIES
from agents.db import get_connection


def generate_blog_post(topic: dict) -> str:
    """Generate a complete Markdown blog post using Claude."""
    client = get_claude_client()
    category_label = CATEGORIES.get(topic["category"], topic["category"])
    slug = topic["slug"]
    n = topic["target_items"]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": f"""Write a complete Markdown blog post for velvetgrl, a women's lifestyle blog.

TOPIC: {topic['title']}
CATEGORY: {category_label}
TARGET KEYWORDS: {', '.join(topic['keywords'])}
NUMBER OF ITEMS: {n}

CRITICAL RULES — follow these exactly:

1. IMAGES: Every single item MUST have an image. Use this exact format:
   ![descriptive alt text](/images/posts/{slug}/01.png)
   Number them 01, 02, 03... up to {n:02d}. Place each image RIGHT AFTER the item heading.

2. LINKS: Reference real brands, products, shops, or tutorials. Link to them:
   - Product mentions → link to the brand website (e.g., [Fenty Beauty](https://fentybeauty.com))
   - Tutorials/techniques → link to relevant resources
   - Include 3-5 outbound links per post minimum
   - Use real, legitimate URLs for well-known brands

3. FORMAT:

---
title: "{topic['title']}"
description: "[Compelling 150-char meta description with main keyword]"
category: "{topic['category']}"
tags: [list of 3-5 relevant lowercase tags]
pinterest_title: "[Catchy Pinterest title] | velvetgrl"
date: {topic['publish_date']}
draft: false
featured_image: "/images/posts/{slug}/01.png"
---

[2-3 sentence intro. Warm, excited, conversational. Use the main keyword naturally.]

## 1. [Specific Item Name]

![descriptive alt text](/images/posts/{slug}/01.png)

[3-4 sentences describing this item. Be specific, visual, and helpful. Mention real brands or products where relevant and link to them.]

**Style tip:** [One actionable tip.]

## 2. [Specific Item Name]

![descriptive alt text](/images/posts/{slug}/02.png)

[3-4 sentences. Include a link to a relevant brand or resource.]

**Style tip:** [One actionable tip.]

[Continue this exact pattern for ALL {n} items. Every item gets an image and detailed description.]

## Final Thoughts

[2-3 sentences. Encourage readers to save/pin favorites. Mention velvetgrl.]

VOICE: Warm, aspirational, like a stylish friend. Not salesy.
Every item must be unique and specific — no generic filler.
EVERY item must have its own image tag.

Return ONLY the complete Markdown file. No other text."""
        }]
    )
    markdown = response.content[0].text.strip()

    # Strip markdown code fences if present
    if markdown.startswith("```"):
        markdown = re.sub(r'^```(?:markdown)?\s*\n?', '', markdown)
        markdown = re.sub(r'\n?```\s*$', '', markdown)

    # Save to queue
    draft_path = QUEUE_DIR / "drafts" / f"{slug}.md"
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(markdown)

    # Track in DB
    conn = get_connection()
    conn.execute(
        """INSERT INTO posts (slug, title, category, keywords, status)
           VALUES (?, ?, ?, ?, 'review')
           ON CONFLICT(slug) DO UPDATE SET status = 'review'""",
        (slug, topic["title"], topic["category"], str(topic["keywords"]))
    )
    conn.commit()
    conn.close()

    return markdown


def extract_image_prompts(markdown: str) -> list[dict]:
    """Extract image alt texts from markdown to use as generation prompts."""
    pattern = r'!\[([^\]]+)\]\((/images/posts/[^)]+)\)'
    matches = re.findall(pattern, markdown)
    return [{"alt": alt, "path": path} for alt, path in matches]
