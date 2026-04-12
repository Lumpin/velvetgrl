from pathlib import Path
from unittest.mock import patch, MagicMock
from agents.image_sourcer.stock_photos import generate_image


def test_generate_image_saves_file(tmp_path):
    mock_post_response = MagicMock()
    mock_post_response.json.return_value = {
        "data": [{"url": "https://example.com/generated.png"}]
    }

    mock_get_response = MagicMock()
    mock_get_response.content = b"fake-image-bytes"

    with patch("agents.image_sourcer.stock_photos.load_settings", return_value={"flux_api_key": "test-key"}), \
         patch("agents.image_sourcer.stock_photos.httpx.post", return_value=mock_post_response), \
         patch("agents.image_sourcer.stock_photos.httpx.get", return_value=mock_get_response):
        save_path = tmp_path / "test.png"
        result = generate_image("boho kitchen", save_path)

    assert result == save_path
    assert save_path.read_bytes() == b"fake-image-bytes"
