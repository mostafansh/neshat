"""Load a study from a folder: study.json + cases.csv + the case images.

The folder layout (it lives OUTSIDE the repo when images are real):

    study.json   {"key", "title", "description", "question", "choices", "confidence_max", "ai_source"}
    cases.csv    position,image,truth,ai_answer,ai_confidence,ai_box[,ai_slices]
    images...    the image files and stack folders named in the image column

The image column names one of two things:
- one image file, for example an X-ray; or
- a folder with one stack of slices, for example one MRI series: 000.png, 001.png, …
  numbered from 000, with no gaps and no other files. File-name order is display order: the
  prep script has already turned the slices the right way up. A stack has 2 to 64 slices.
  Every slice is already an 8-bit greyscale PNG (Pillow mode "L"), all slices have one size,
  and the long side is 1024 px at most.

ai_box is "x y width height" in image pixels (slice pixels for a stack), or empty.
ai_slices is "first last": the slices the box is drawn on, counted from 0, both included. A
stack case with an ai_box needs it. Single images and cases without a box leave it empty.
The ai_slices column may be left out, so older folders load as before.

Every check below refuses the whole study with a plain message; nothing is half-loaded.
Images are re-saved as bare 8-bit greyscale pixels under a random name, so no file name, no
DICOM header and no PNG/JPEG text travels into the site (CLAUDE.md rule 4). A single image is
stored as <code>.png; a stack is stored as one file, <code>.stk (see stack_bytes).
"""

import csv
import hashlib
import io
import itertools
import json
import re
import shutil
import struct
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from PIL import Image

from .models import Case, Study, new_case_code

STUDY_FIELDS = {"key", "title", "description", "question", "choices", "confidence_max", "ai_source"}
CASE_COLUMNS = ["position", "image", "truth", "ai_answer", "ai_confidence", "ai_box"]
STACK_COLUMNS = [*CASE_COLUMNS, "ai_slices"]
LONG_NUMBER = re.compile(r"\d{8,}")  # national codes, accession numbers, patient IDs
KEY = re.compile(r"^[a-z0-9-]{3,50}$")
MIN_SLICES, MAX_SLICES = 2, 64
MAX_SLICE_SIDE = 1024  # px
STACK_MAGIC = b"NSTK"  # the first 4 bytes of every stack file


class StudyFileError(Exception):
    pass


def _no_identifiers(label: str, text: str) -> None:
    if LONG_NUMBER.search(text):
        raise StudyFileError(f"{label} contains a long number ({text!r}). It could be a patient ID; remove it.")


def read_design(folder: Path) -> tuple[dict, list[dict]]:
    try:
        design = json.loads((folder / "study.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise StudyFileError(f"No study.json in {folder}.")
    except ValueError as problem:
        raise StudyFileError(f"study.json is not valid JSON: {problem}")
    if not isinstance(design, dict):
        raise StudyFileError("study.json must be one object: { \"key\": ..., \"title\": ..., ... }.")
    unknown = set(design) - STUDY_FIELDS
    if unknown:
        raise StudyFileError(f"study.json has unknown fields: {', '.join(sorted(unknown))}.")
    for field in ("key", "title", "question", "choices"):
        if not design.get(field):
            raise StudyFileError(f"study.json needs '{field}'.")
    if not KEY.match(design["key"]):
        raise StudyFileError("The study key may use only a-z, 0-9 and '-' (3 to 50 characters).")
    for field in ("title", "description", "question", "ai_source"):
        _no_identifiers(f"study.json {field}", str(design.get(field, "")))
    choices = design["choices"]
    values = [c.get("value") for c in choices] if isinstance(choices, list) and all(isinstance(c, dict) for c in choices) else []
    if len(values) < 2 or len(set(values)) != len(values) or not all(c.get("label") for c in choices):
        raise StudyFileError("study.json 'choices' needs at least 2 entries, each with a unique value and a label.")
    scale = design.get("confidence_max", 5)
    if type(scale) is not int or not 2 <= scale <= 10:  # type(), because True counts as an int
        raise StudyFileError("study.json 'confidence_max' must be a whole number from 2 to 10.")

    try:
        with (folder / "cases.csv").open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, restval="")  # a short row gets empty fields, not None
            if reader.fieldnames not in (CASE_COLUMNS, STACK_COLUMNS):
                raise StudyFileError(
                    f"cases.csv columns must be exactly: {','.join(CASE_COLUMNS)} (optionally followed by ,ai_slices)"
                )
            rows = list(reader)
    except FileNotFoundError:
        raise StudyFileError(f"No cases.csv in {folder}.")
    if not rows:
        raise StudyFileError("cases.csv has no cases.")
    return design, rows


def stack_slices(where: str, stack: Path, folder: Path) -> list[Path]:
    """The slice files of one stack folder, in display order. Anything unexpected is refused."""
    names = sorted(entry.name for entry in stack.iterdir())
    for number, name in enumerate(names):
        if name != f"{number:03d}.png":
            raise StudyFileError(
                f"{where}: stack folder '{stack.name}' may hold only 000.png, 001.png, 002.png … numbered from "
                f"000, with no gaps and no other files. Found '{name}' where '{number:03d}.png' was expected."
            )
    if len(names) < MIN_SLICES:
        raise StudyFileError(
            f"{where}: a stack needs at least {MIN_SLICES} slices; '{stack.name}' has {len(names)}. "
            "For one image, name the PNG file itself."
        )
    if len(names) > MAX_SLICES:
        raise StudyFileError(f"{where}: a stack may have {MAX_SLICES} slices at most; '{stack.name}' has {len(names)}.")
    paths = [(stack / name).resolve() for name in names]
    if not all(folder.resolve() in path.parents and path.is_file() for path in paths):
        raise StudyFileError(f"{where}: every slice in '{stack.name}' must be a file inside the study folder.")
    return paths


def slice_range(where: str, text: str, slices: int, box: list[int] | None) -> list[int] | None:
    """The ai_slices column as [first, last], or None for a single image or a case without a box."""
    text = text.strip()
    if slices == 1 or box is None:
        if text:
            raise StudyFileError(f"{where}: ai_slices is only for a stack case with an ai_box. Leave it empty here.")
        return None
    try:
        span = [int(v) for v in text.split()]
    except ValueError:
        span = []
    if len(span) != 2 or not 0 <= span[0] <= span[1] < slices:
        raise StudyFileError(
            f"{where}: this stack case has an ai_box, so ai_slices must be 'first last': the slices the box "
            f"covers, counted from 0 (0 to {slices - 1} here), with first not after last."
        )
    return span


def check_cases(design: dict, rows: list[dict], folder: Path) -> list[dict]:
    """Turn the CSV rows into clean case data, or refuse with the first problem found."""
    answers = {c["value"] for c in design["choices"]} - {"unsure"}
    cases = []
    for number, row in enumerate(rows, start=2):  # line 1 is the header
        where = f"cases.csv line {number}"
        if None in row:
            raise StudyFileError(f"{where} has more fields than the header.")
        try:
            position = int(row["position"])
            confidence = float(row["ai_confidence"])
        except ValueError:
            raise StudyFileError(f"{where}: position must be a whole number and ai_confidence a number.")
        if row["truth"] not in answers or row["ai_answer"] not in answers:
            raise StudyFileError(f"{where}: truth and ai_answer must each be one of {sorted(answers)}.")
        if not 0.5 <= confidence <= 0.99:
            raise StudyFileError(f"{where}: ai_confidence must be between 0.5 and 0.99.")
        image = (folder / row["image"]).resolve()
        if folder.resolve() not in image.parents or not (image.is_file() or image.is_dir()):
            raise StudyFileError(
                f"{where}: image '{row['image']}' is not a file or a stack folder inside the study folder."
            )
        source = stack_slices(where, image, folder) if image.is_dir() else image
        slices = len(source) if image.is_dir() else 1
        box = None
        if row["ai_box"].strip():
            try:
                box = [int(v) for v in row["ai_box"].split()]
            except ValueError:
                box = []
            if len(box) != 4 or min(box) < 0 or min(box[2:]) == 0:
                raise StudyFileError(
                    f"{where}: ai_box must be four whole numbers 'x y width height' (width and height above 0), or empty."
                )
        cases.append(
            {
                "position": position,
                "source": source,  # one file, or the slice files of a stack
                "slices": slices,
                "truth": row["truth"],
                "ai_answer": row["ai_answer"],
                "ai_confidence": confidence,
                "ai_box": box,
                "ai_slices": slice_range(where, row.get("ai_slices", ""), slices, box),
                "ai_planted": row["ai_answer"] != row["truth"],
            }
        )

    positions = sorted(c["position"] for c in cases)
    if positions != list(range(1, len(cases) + 1)):
        raise StudyFileError("Positions in cases.csv must be 1, 2, 3 … with no gaps or repeats.")

    # Rule 6: the shown confidence must not give planted suggestions away.
    correct = [c["ai_confidence"] for c in cases if not c["ai_planted"]]
    for case in cases:
        if case["ai_planted"] and correct and not min(correct) <= case["ai_confidence"] <= max(correct):
            raise StudyFileError(
                f"Case {case['position']}: a planted suggestion's confidence ({case['ai_confidence']}) lies outside "
                f"the range of the correct ones ({min(correct)}-{max(correct)}). Readers could spot it."
            )
    # Rule 6: the AI box must not give planted suggestions away either. Every suggestion with
    # the same answer has a box, or none has.
    for answer in answers:
        if len({bool(c["ai_box"]) for c in cases if c["ai_answer"] == answer}) > 1:
            raise StudyFileError(
                f"Some '{answer}' AI suggestions have an ai_box and others do not. Readers could spot the "
                "planted ones. Give all of them a box, or none."
            )
    # Rule 6 for stacks: a planted box must not stand out by its size or by the number of
    # slices it covers. Each lies within the range of the correct boxes for the same answer.
    measures = {
        "width": lambda c: c["ai_box"][2],
        "height": lambda c: c["ai_box"][3],
        "slice span": lambda c: c["ai_slices"][1] - c["ai_slices"][0] + 1,
    }
    for answer in answers:
        boxed = [c for c in cases if c["ai_answer"] == answer and c["ai_slices"]]
        for name, measure in measures.items():
            values = [measure(c) for c in boxed if not c["ai_planted"]]
            for case in boxed:
                if case["ai_planted"] and values and not min(values) <= measure(case) <= max(values):
                    raise StudyFileError(
                        f"Case {case['position']}: a planted box's {name} ({measure(case)}) lies outside the range "
                        f"of the correct ones ({min(values)}-{max(values)}). Readers could spot it."
                    )
    # Rule 1: readers see the slice count before the lock, so it must not sort the answers.
    # With 2 or more stacks per answer, the slice-count ranges of two answers must overlap.
    counts = {}
    for case in cases:
        if case["slices"] > 1:
            counts.setdefault(case["truth"], []).append(case["slices"])
    groups = sorted((truth, min(v), max(v)) for truth, v in counts.items() if len(v) >= 2)
    for (a, a_low, a_high), (b, b_low, b_high) in itertools.combinations(groups, 2):
        if a_high < b_low or b_high < a_low:
            raise StudyFileError(
                f"Stacks with the answer '{a}' have {a_low}-{a_high} slices and stacks with '{b}' have "
                f"{b_low}-{b_high}. Readers could guess the answer from the slice count. Use the same slab "
                "rule for every case, or swap in a spare."
            )
    return sorted(cases, key=lambda c: c["position"])


def bare_pixels(source: Path) -> Image.Image:
    """Open an image and keep only its pixels, as 8-bit greyscale. Metadata is dropped."""
    with Image.open(source) as original:
        original.load()
        if original.mode in ("I;16", "I;16B", "I;16L", "I", "F"):
            # 16-bit or float pixels: stretch the full range to 0-255.
            original = original.convert("I")
            low, high = original.getextrema()
            scale = 255 / (high - low) if high > low else 0
            original = original.point(lambda v: v * scale - low * scale).convert("L")
        else:
            original = original.convert("L")
        return Image.frombytes("L", original.size, original.tobytes())


def slice_pixels(where: str, source: Path) -> Image.Image:
    """Open one stack slice and keep only its pixels. It must already be 8-bit greyscale:
    stretching each slice on its own (as bare_pixels does for one image) would make the
    brightness jump from slice to slice."""
    try:
        with Image.open(source) as original:
            if original.format != "PNG" or original.mode != "L":
                raise StudyFileError(
                    f"{where}: slice {source.name} is {original.format} mode {original.mode}, not an 8-bit greyscale "
                    "PNG (mode L). Window the whole volume to 8 bits before export; the site never stretches a slice."
                )
            original.load()
            return Image.frombytes("L", original.size, original.tobytes())
    except OSError:
        raise StudyFileError(f"{where}: slice {source.name} is not a readable PNG.")


def png_bytes(pixels: Image.Image) -> bytes:
    buffer = io.BytesIO()
    pixels.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def stack_bytes(slices: list[bytes]) -> bytes:
    """One stack file: "NSTK", the slice count, then for each slice its byte length and its
    PNG bytes. Count and lengths are 4-byte unsigned numbers, big-endian. Nothing else: no
    names, no positions, no metadata (rule 4). docs/reading-api.md describes the same layout."""
    parts = [STACK_MAGIC, struct.pack(">I", len(slices))]
    for data in slices:
        parts += [struct.pack(">I", len(data)), data]
    return b"".join(parts)


def stack_file(case: dict) -> tuple[tuple[int, int], bytes]:
    """Re-save every slice of one stack case and join them into one stack file."""
    where = f"Case {case['position']}"
    size, slices = None, []
    for source in case["source"]:
        pixels = slice_pixels(where, source)
        size = size or pixels.size
        if max(size) > MAX_SLICE_SIDE:
            raise StudyFileError(
                f"{where}: the slices are {size[0]} x {size[1]} px. The long side may be {MAX_SLICE_SIDE} px at most."
            )
        if pixels.size != size:
            raise StudyFileError(
                f"{where}: slice {source.name} is {pixels.width} x {pixels.height} px, but slice 000.png is "
                f"{size[0]} x {size[1]}. All slices of a stack need one size."
            )
        slices.append(png_bytes(pixels))
    return size, stack_bytes(slices)


def prepare(folder: Path) -> tuple[dict, list[tuple], str]:
    """Run every check and re-save every image in memory. Writes nothing to the database or
    the disk, so `load_study --check` uses it on its own. Returns the design, one
    (case, (width, height), file bytes, SHA-256) per case, and the design digest."""
    folder = Path(folder)
    design, rows = read_design(folder)
    cases = check_cases(design, rows, folder)

    existing = Study.objects.filter(key=design["key"]).first()
    if existing and existing.state != Study.State.DRAFT:
        raise StudyFileError(f"Study '{design['key']}' is already open; its design is frozen (rule 3).")

    digest = hashlib.sha256(json.dumps(design, sort_keys=True).encode())
    prepared = []
    for case in cases:
        if case["slices"] == 1:
            pixels = bare_pixels(case["source"])
            size, data = pixels.size, png_bytes(pixels)
        else:
            size, data = stack_file(case)
        if case["ai_box"]:
            x, y, w, h = case["ai_box"]
            if x + w > size[0] or y + h > size[1]:
                raise StudyFileError(f"Case {case['position']}: ai_box reaches outside the image.")
        sha = hashlib.sha256(data).hexdigest()
        # The digest covers every case field, including slices and ai_slices, and the pixels.
        digest.update(json.dumps({k: v for k, v in case.items() if k != "source"}, sort_keys=True).encode())
        digest.update(sha.encode())
        prepared.append((case, size, data, sha))
    return design, prepared, digest.hexdigest()


def load(folder: Path, open_now: bool = False) -> Study:
    design, prepared, digest = prepare(folder)
    media_dir = settings.CASE_MEDIA_ROOT / design["key"]
    with transaction.atomic():
        Study.objects.filter(key=design["key"]).delete()  # a draft only: prepare() refused an open one
        study = Study.objects.create(
            key=design["key"],
            title=design["title"],
            description=design.get("description") or "",
            question=design["question"],
            choices=design["choices"],
            confidence_max=int(design.get("confidence_max", 5)),
            ai_source=design.get("ai_source") or "AI model (simulated)",
            design_sha256=digest,
        )
        if media_dir.exists():
            shutil.rmtree(media_dir)
        media_dir.mkdir(parents=True)
        for case, (width, height), data, sha in prepared:
            code = new_case_code()
            name = f"{code}.stk" if case["slices"] > 1 else f"{code}.png"
            (media_dir / name).write_bytes(data)
            Case.objects.create(
                study=study,
                position=case["position"],
                code=code,
                image=f"{design['key']}/{name}",
                image_sha256=sha,
                width=width,
                height=height,
                slices=case["slices"],
                truth=case["truth"],
                ai_answer=case["ai_answer"],
                ai_confidence=case["ai_confidence"],
                ai_box=case["ai_box"],
                ai_slices=case["ai_slices"],
                ai_planted=case["ai_planted"],
            )
        if open_now:
            open_study(study)
    return study


def open_study(study: Study) -> None:
    """Open a study for readers. From now on its design and cases are frozen (rule 3)."""
    study.state = Study.State.OPEN
    study.opened_at = timezone.now()
    study.save(update_fields=["state", "opened_at"])
