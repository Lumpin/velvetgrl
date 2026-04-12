from PIL import Image
from agents.pinterest.pin_generator import create_pin_collage


def test_create_pin_collage_correct_size():
    # Create 4 dummy images
    images = [Image.new("RGB", (500, 500), color) for color in ["red", "blue", "green", "yellow"]]
    result = create_pin_collage(
        images=images,
        number=17,
        title_lines=["MAGICAL CAT", "TATTOO IDEAS!"],
        highlight_word="CAT",
        accent_color="#F4C2C2",
    )
    assert result.size == (1000, 1500)
