"""Synthetic test images, so the site can be built and tested without patient images.

Each image is drawn by code: no patient, no download. Every image carries the words
"SYNTHETIC - NOT A PATIENT".
- make_phantom: an X-ray-like forearm with two long bones and, when asked, a thin dark
  fracture line across one of them.
- make_phantom_stack: an MRI-like stack of slices through a pelvis and, when asked, a small
  bright round "cyst" on 3 neighbouring slices.
"""

import math
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


# The cyst sits this many slices from the middle slice, where every case opens, so the reader
# must scroll to find it.
CYST_OFFSETS = (-7, -4, 3, 5)
CYST_PAD = 3  # px of margin around the cyst inside its box


def make_phantom_stack(folder: Path, cyst: bool, variant: int, slices: int = 24, size: int = 384):
    """Draw one MRI-like stack in `folder`: 000.png, 001.png … as 8-bit greyscale PNGs.

    It looks a little like a sagittal T2 pelvis, front of the body on the left: an oval body,
    a bright bladder and a uterus-like ellipse. Bladder and uterus grow toward the middle
    slices and shrink again, like a series across the midline. With `cyst`, a small bright
    round "cyst" sits in the cervix on 3 neighbouring slices, never on the middle slice.
    `variant` shifts the anatomy and moves the cyst, so a set of stacks differs.
    Returns (box [x, y, width, height], (first, last)) for the cyst, or None.
    """
    found = cyst_box(variant, slices, size) if cyst else None
    folder.mkdir(parents=True, exist_ok=True)
    for index in range(slices):
        image = _pelvis_slice(index, slices, size, variant)
        if found and found[1][0] <= index <= found[1][1]:
            _draw_cyst(image, variant, index, found[1], slices, size)
        image = image.filter(ImageFilter.GaussianBlur(1.2))
        noise = Image.effect_noise((size, size), 30)  # scanner-like grain
        image = Image.blend(image, noise, 0.1)
        ImageDraw.Draw(image).text((8, 6), "SYNTHETIC - NOT A PATIENT", fill=220, font_size=max(12, size // 26))
        image.save(folder / f"{index:03d}.png", format="PNG")
    return found


def cyst_box(variant: int, slices: int = 24, size: int = 384) -> tuple[list[int], tuple[int, int]]:
    """Where the cyst of a given variant sits: (box [x, y, width, height], (first, last) slice).

    Also used for a deliberately wrong AI "cyst" on a stack without one: the same plausible
    spot in the cervix, with the same box sizes and the same 3-slice span (rule 6).
    """
    middle = (slices - 1) // 2  # the start slice of every case
    first = max(0, min(middle + CYST_OFFSETS[variant % 4], slices - 3))
    span = (first, first + 2)
    x, y = _cyst_centre(variant, span, slices, size)
    side = 2 * (_cyst_radius(variant) + CYST_PAD)
    return [round(x) - side // 2, round(y) - side // 2, side, side], span


def _cyst_radius(variant: int) -> int:
    return 6 + variant % 4  # px


def _grow(index: int, slices: int) -> float:
    """How big a midline organ is on one slice: small at both ends of the stack, full in the middle."""
    return 0.35 + 0.65 * math.sin(math.pi * (index + 0.5) / slices)


def _uterus(variant: int, index: int, slices: int, size: int) -> tuple[float, ...]:
    """The uterus-like ellipse on one slice: centre x and y, long and short half-axes, tilt.
    The tilt points the top (fundus) forward over the bladder and the cervix down and back."""
    grow = _grow(index, slices)
    x = size * (0.52 + 0.03 * (variant % 3 - 1))
    y = size * (0.44 + 0.03 * (variant % 2))
    return x, y, 0.25 * size * grow, 0.12 * size * grow, math.radians(28 + 8 * (variant % 3))


def _ellipse(x: float, y: float, a: float, b: float, tilt: float, steps: int = 72) -> list[tuple[float, float]]:
    """The outline of a tilted ellipse, as points for ImageDraw.polygon."""
    cos, sin = math.cos(tilt), math.sin(tilt)
    points = []
    for step in range(steps):
        angle = 2 * math.pi * step / steps
        u, v = a * math.cos(angle), b * math.sin(angle)
        points.append((x + u * cos - v * sin, y + u * sin + v * cos))
    return points


def _pelvis_slice(index: int, slices: int, size: int, variant: int) -> Image.Image:
    """One slice without grain or text."""
    s = size
    image = Image.new("L", (s, s), 8)
    draw = ImageDraw.Draw(image)
    # Body: bright fat under the skin around darker muscle and soft tissue; sacrum at the back.
    draw.ellipse((0.05 * s, 0.1 * s, 0.95 * s, 0.93 * s), fill=105)
    draw.ellipse((0.1 * s, 0.15 * s, 0.9 * s, 0.88 * s), fill=58)
    draw.ellipse((0.8 * s, 0.2 * s, 0.88 * s, 0.76 * s), fill=88)
    grow = _grow(index, slices)
    # Bladder in front, very bright on T2 like all fluid; rectum behind, dark.
    draw.polygon(_ellipse(0.3 * s, 0.67 * s, 0.12 * s * grow, 0.08 * s * grow, 0.2), fill=210)
    draw.polygon(_ellipse(0.7 * s, 0.63 * s, 0.05 * s * grow, 0.07 * s * grow, 0.0), fill=38)
    # Uterus: intermediate wall, a dark inner band and a bright lining in the middle.
    x, y, a, b, tilt = _uterus(variant, index, slices, size)
    draw.polygon(_ellipse(x, y, a, b, tilt), fill=112)
    draw.polygon(_ellipse(x, y, a * 0.72, b * 0.55, tilt), fill=62)
    draw.polygon(_ellipse(x, y, a * 0.6, b * 0.28, tilt), fill=185)
    return image


def _cyst_centre(variant: int, span: tuple[int, int], slices: int, size: int) -> tuple[float, float]:
    """A spot in the cervix that lies inside the uterus on every slice of `span`."""
    x, y, a, b, tilt = min((_uterus(variant, i, slices, size) for i in range(span[0], span[1] + 1)), key=lambda u: u[2])
    along, across = 0.78 * a, 0.2 * b
    return x + along * math.cos(tilt) - across * math.sin(tilt), y + along * math.sin(tilt) + across * math.cos(tilt)


def _draw_cyst(image: Image.Image, variant: int, index: int, span: tuple[int, int], slices: int, size: int) -> None:
    """The cyst is largest and brightest on its middle slice, smaller on the two outer ones."""
    x, y = _cyst_centre(variant, span, slices, size)
    middle = index == span[0] + 1
    r = _cyst_radius(variant) - (0 if middle else 2)
    ImageDraw.Draw(image).ellipse((x - r, y - r, x + r, y + r), fill=215 if middle else 180)
