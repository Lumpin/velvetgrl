from unittest.mock import patch, MagicMock
from agents.writer.blog_writer import generate_blog_post, extract_image_prompts


def test_generate_blog_post_creates_markdown():
    topic = {
        "title": "15 Boho Kitchen Ideas",
        "category": "boho-decor",
        "keywords": ["boho kitchen"],
        "target_items": 15,
        "slug": "15-boho-kitchen-ideas",
        "publish_date": "2026-04-14",
    }

    fake_markdown = """---
title: "15 Boho Kitchen Ideas"
description: "Transform your cooking space with these boho ideas."
category: "boho-decor"
tags: ["boho", "kitchen", "home decor"]
pinterest_title: "Boho Kitchen Ideas | velvetgrl"
date: 2026-04-14
draft: false
featured_image: "/images/posts/15-boho-kitchen-ideas/01.png"
---

Looking for boho kitchen inspiration?

## 1. Macrame Plant Hangers

![macrame plant hangers in boho kitchen](/images/posts/15-boho-kitchen-ideas/01.png)

Add some texture above your sink.

**Style tip:** Mix trailing pothos with upright herbs.
"""

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=fake_markdown)]

    with patch("agents.writer.blog_writer.get_claude_client") as mock_client:
        mock_client.return_value.messages.create.return_value = mock_response
        result = generate_blog_post(topic)

    assert "15 Boho Kitchen Ideas" in result
    assert "/images/posts/15-boho-kitchen-ideas/01.png" in result


def test_extract_image_prompts():
    md = """## 1. Macrame Plant Hangers

![macrame plant hangers in boho kitchen](/images/posts/test-slug/01.png)

Some text.

## 2. Open Wooden Shelving

![open wooden shelves with ceramics](/images/posts/test-slug/02.png)

More text."""

    entries = extract_image_prompts(md)
    assert len(entries) == 2
    assert entries[0]["alt"] == "macrame plant hangers in boho kitchen"
    assert entries[1]["path"] == "/images/posts/test-slug/02.png"
