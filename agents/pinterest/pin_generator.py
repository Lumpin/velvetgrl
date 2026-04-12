import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from agents.claude_client import get_claude_client, parse_json_response
from agents.pinterest.image_gen import generate_image_prompts, generate_images
from agents.config import DATA_DIR
from agents.db import get_connection

# Pin dimensions
PIN_WIDTH = 1000
PIN_HEIGHT = 1500
GRID_COLS = 2
GRID_ROWS = 2


def create_pin_collage(
    images: list[Image.Image],
    number: int,
    title_lines: list[str],
    highlight_word: str,
    accent_color: str = "#F4C2C2",
) -> Image.Image:
    """Create a Pinterest pin collage with text overlay."""
    canvas = Image.new("RGB", (PIN_WIDTH, PIN_HEIGHT), "white")

    # Place 4 images in 2x2 grid
    cell_w = PIN_WIDTH // GRID_COLS
    cell_h = PIN_HEIGHT // GRID_ROWS
    for i, img in enumerate(images[:4]):
        row, col = divmod(i, GRID_COLS)
        resized = img.resize((cell_w, cell_h), Image.LANCZOS)
        canvas.paste(resized, (col * cell_w, row * cell_h))

    draw = ImageDraw.Draw(canvas)

    # Darken center area for text
    overlay = Image.new("RGBA", (PIN_WIDTH, PIN_HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    center_y = PIN_HEIGHT // 2
    band_height = 400
    overlay_draw.rectangle(
        [0, center_y - band_height // 2, PIN_WIDTH, center_y + band_height // 2],
        fill=(0, 0, 0, 140),
    )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # Load fonts (fall back to default if custom not available)
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 72)
        font_number = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 96)
    except OSError:
        font_large = ImageFont.load_default()
        font_number = ImageFont.load_default()

    # Draw number badge
    badge_y = center_y - band_height // 2 + 20
    badge_x = PIN_WIDTH // 2
    badge_r = 55
    draw.ellipse(
        [badge_x - badge_r, badge_y - badge_r + 30, badge_x + badge_r, badge_y + badge_r + 30],
        fill=accent_color,
    )
    num_text = str(number)
    num_bbox = draw.textbbox((0, 0), num_text, font=font_number)
    num_w = num_bbox[2] - num_bbox[0]
    num_h = num_bbox[3] - num_bbox[1]
    draw.text(
        (badge_x - num_w // 2, badge_y - num_h // 2 + 30),
        num_text, fill="white", font=font_number,
    )

    # Draw title lines
    title_y = badge_y + badge_r + 50
    for line in title_lines:
        words = line.split()
        # Calculate total line width first
        line_bbox = draw.textbbox((0, 0), line, font=font_large)
        line_w = line_bbox[2] - line_bbox[0]
        x_start = (PIN_WIDTH - line_w) // 2

        # Draw word by word for highlight
        x = x_start
        for word in words:
            color = accent_color if word.upper() == highlight_word.upper() else "white"
            draw.text((x, title_y), word + " ", fill=color, font=font_large)
            word_bbox = draw.textbbox((0, 0), word + " ", font=font_large)
            x += word_bbox[2] - word_bbox[0]

        title_y += 80

    # Brand watermark
    try:
        font_small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
    except OSError:
        font_small = ImageFont.load_default()
    brand = "velvetgrl.com"
    brand_bbox = draw.textbbox((0, 0), brand, font=font_small)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text(
        ((PIN_WIDTH - brand_w) // 2, PIN_HEIGHT - 50),
        brand, fill="white", font=font_small,
    )

    return canvas


def generate_pin_title(post_title: str, category: str) -> dict:
    """Use Claude to generate a clickbait pin title with highlight word."""
    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Generate a Pinterest pin title for this blog post: "{post_title}"

The title should be:
- ALL CAPS
- Format: [number] [ADJECTIVE] [keyword] IDEAS/DESIGNS/LOOKS!
- Eye-catching and clickable
- The adjective should be emotional/visual (STUNNING, DREAMY, MAGICAL, GORGEOUS, etc.)

Also identify the single most emotional/visual word to highlight in a different color.
Split the title into 2 lines for the pin graphic.

Return JSON:
{{"line1": "17 MAGICAL CAT", "line2": "TATTOO IDEAS!", "highlight_word": "MAGICAL", "number": 17}}

Return ONLY JSON."""
        }]
    )
    return parse_json_response(response.content[0].text)


def generate_pins_for_post(slug: str, title: str, category: str, count: int = 3) -> list[Path]:
    """Generate multiple pin variations for a blog post."""
    pins_dir = DATA_DIR / "pins" / slug
    pins_dir.mkdir(parents=True, exist_ok=True)

    accent_colors = ["#F4C2C2", "#B2C9AB", "#C9A96E", "#A8C4D9", "#D4A5A5"]
    generated_pins = []

    for variation in range(count):
        # Generate title variation
        pin_title = generate_pin_title(title, category)

        # Generate AI images
        prompts = generate_image_prompts(title, category, count=4)
        image_dir = pins_dir / f"v{variation}"
        image_paths = generate_images(prompts, image_dir)

        if len(image_paths) < 4:
            continue

        # Create collage
        images = [Image.open(p) for p in image_paths]
        pin = create_pin_collage(
            images=images,
            number=pin_title["number"],
            title_lines=[pin_title["line1"], pin_title["line2"]],
            highlight_word=pin_title["highlight_word"],
            accent_color=accent_colors[variation % len(accent_colors)],
        )

        pin_path = pins_dir / f"pin_v{variation}.png"
        pin.save(pin_path, "PNG", quality=95)
        generated_pins.append(pin_path)

        # Clean up individual images
        for img in images:
            img.close()

    return generated_pins


def generate_pin_copy(title: str, keywords: list[str], category: str) -> dict:
    """Generate Pinterest pin title and description."""
    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Write Pinterest pin copy for: "{title}"
Keywords: {', '.join(keywords)}
Category: {category}

Return JSON:
{{"pin_title": "max 100 chars, keyword-rich, compelling", "pin_description": "max 500 chars, includes keywords naturally, ends with CTA to click through"}}

Return ONLY JSON."""
        }]
    )
    return parse_json_response(response.content[0].text)


def register_pins_in_db(slug: str, pin_paths: list[Path], title: str, keywords: list[str], category: str) -> None:
    """Register generated pins in DB for the browser agent to post."""
    from agents.config import load_boards
    boards_config = load_boards()

    # Find boards for this category
    category_boards = [b["name"] for b in boards_config.get("boards", []) if b["category"] == category]
    if not category_boards:
        category_boards = ["General"]

    conn = get_connection()
    for i, pin_path in enumerate(pin_paths):
        copy = generate_pin_copy(title, keywords, category)
        board = category_boards[i % len(category_boards)]

        conn.execute(
            """INSERT INTO pins (post_slug, image_path, title, description, board, status)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (slug, str(pin_path), copy["pin_title"], copy["pin_description"], board)
        )
    conn.commit()
    conn.close()
