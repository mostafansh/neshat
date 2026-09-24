"""Synthetic test radiographs, so the site can be built and tested without patient images.

Each image is drawn by code: no patient, no download. It shows a forearm-like shape with two
long bones and, when asked, a thin dark fracture line across one of them. Every image carries
the words "SYNTHETIC - NOT A PATIENT".
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 1024, 1280

# The two bones: (left, top, right, bottom) in image pixels.
LEFT_BONE = (350, 90, 470, 1200)
RIGHT_BONE = (545, 120, 650, 1180)


def make_phantom(path: Path, fracture: bool = True, variant: int = 0) -> list[int] | None:
    """Draw one test image and save it as an 8-bit greyscale PNG at `path`.

    `variant` moves the fracture to another bone and height, so a set of images differs.
    Returns the fracture's box [x, y, width, height] in image pixels, or None.
    """
    image = Image.new("L", (WIDTH, HEIGHT), 12)
    draw = ImageDraw.Draw(image)

    # Soft tissue: a long grey shape down the middle.
    draw.rounded_rectangle((250, 60, 780, 1240), radius=220, fill=70)

    # Two long bones (like radius and ulna), brighter than soft tissue, with darker marrow.
    draw.rounded_rectangle(LEFT_BONE, radius=60, fill=175)
    draw.rounded_rectangle(RIGHT_BONE, radius=55, fill=165)
    draw.rounded_rectangle((385, 140, 435, 1150), radius=25, fill=150)
    draw.rounded_rectangle((578, 170, 617, 1130), radius=20, fill=140)

    box = None
    if fracture:
        box = fracture_box(variant)
        x, y, w, h = box
        # A thin oblique dark line across the bone, inside the box.
        draw.line((x + 15, y + h - 25, x + w - 15, y + 25), fill=60, width=5)

    image = image.filter(ImageFilter.GaussianBlur(3))
    noise = Image.effect_noise((WIDTH, HEIGHT), 18)  # film-like grain
    image = Image.blend(image, noise, 0.12)
    ImageDraw.Draw(image).text((24, 24), "SYNTHETIC - NOT A PATIENT", fill=200, font_size=48)

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
    return box


def fracture_box(variant: int) -> list[int]:
    """Where the fracture of a given variant sits: [x, y, width, height] in image pixels."""
    left, _, right, _ = LEFT_BONE if variant % 2 == 0 else RIGHT_BONE
    y = 330 + (variant * 137) % 640
    return [left - 15, y, (right - left) + 30, 90]


def normal_area_box(variant: int) -> list[int]:
    """A box over a normal stretch of bone, used for a deliberately wrong AI 'fracture'."""
    x, y, w, h = fracture_box(variant + 1)
    return [x, (y + 300) % 900 + 150, w, h]
