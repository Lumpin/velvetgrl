from pathlib import Path

from agents.claude_client import get_claude_client, parse_json_response
from agents.config import DATA_DIR
from agents.image_sourcer.flux_client import generate_image_to_file


def generate_image_prompts(title: str, category: str, count: int = 4) -> list[str]:
    """Use Claude to generate detailed image prompts for pin graphics."""
    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": f"""Generate {count} detailed image prompts for AI image generation.
These will be used in a 2x2 collage for a Pinterest pin about: "{title}" (category: {category}).

Each prompt should describe a different, photorealistic scene related to the topic.
Make them visually diverse — different angles, settings, and compositions.
Style: Pinterest-aesthetic, high quality, editorial photography look.
Do NOT include any text in the images.

Return as JSON array of strings:
["prompt 1", "prompt 2", "prompt 3", "prompt 4"]

Return ONLY the JSON array."""
        }]
    )
    return parse_json_response(response.content[0].text)


def generate_images(prompts: list[str], output_dir: Path) -> list[Path]:
    """Generate images using the shared rate-limited Flux client."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, prompt in enumerate(prompts):
        path = output_dir / f"gen_{i}.png"
        try:
            generate_image_to_file(prompt, path, width=512, height=512)
            paths.append(path)
        except Exception as e:
            print(f"Image generation failed for prompt {i}: {e}")
    return paths
