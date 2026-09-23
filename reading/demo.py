"""A synthetic test radiograph, so the site can show an image before real cases exist.

It is drawn by code: no patient, no download. It shows a forearm-like shape with a thin
dark line across one bone, and the words "SYNTHETIC - NOT A PATIENT".
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 1024, 1280


def make_phantom(path: Path) -> None:
    """Draw the test image and save it as an 8-bit greyscale PNG at `path`."""
    image = Image.new("L", (WIDTH, HEIGHT), 12)
    draw = ImageDraw.Draw(image)

    # Soft tissue: a long grey shape down the middle.
    draw.rounded_rectangle((250, 60, 780, 1240), radius=220, fill=70)

    # Two long bones (like radius and ulna), brighter than soft tissue.
    draw.rounded_rectangle((350, 90, 470, 1200), radius=60, fill=175)
    draw.rounded_rectangle((545, 120, 650, 1180), radius=55, fill=165)
    # Bone marrow: slightly darker centre lines.
    draw.rounded_rectangle((385, 140, 435, 1150), radius=25, fill=150)
    draw.rounded_rectangle((578, 170, 617, 1130), radius=20, fill=140)

    # A thin oblique fracture line across the first bone.
    draw.line((340, 700, 480, 655), fill=60, width=5)

    image = image.filter(ImageFilter.GaussianBlur(3))

    # Film-like noise.
    noise = Image.effect_noise((WIDTH, HEIGHT), 18)
    image = Image.blend(image, noise, 0.12)

    ImageDraw.Draw(image).text((24, 24), "SYNTHETIC - NOT A PATIENT", fill=200, font_size=48)

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
