import json
from unittest.mock import patch, MagicMock
from agents.researcher.topic_selector import select_topics


def test_select_topics_returns_correct_count():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps([
        {"title": "23 Minimalist Tattoo Ideas", "category": "tattoo-ideas", "keywords": ["minimalist tattoo"], "target_items": 23},
        {"title": "15 Boho Kitchen Ideas", "category": "boho-decor", "keywords": ["boho kitchen"], "target_items": 15},
        {"title": "19 Sage Green Nail Designs", "category": "nail-art", "keywords": ["sage green nails"], "target_items": 19},
        {"title": "21 Tarot Spread Ideas", "category": "tarot-spirituality", "keywords": ["tarot spread"], "target_items": 21},
    ]))]

    with patch("agents.researcher.topic_selector.get_claude_client") as mock_client:
        mock_client.return_value.messages.create.return_value = mock_response
        topics = select_topics(count=4)

    assert len(topics) == 4
    assert topics[0]["category"] == "tattoo-ideas"
