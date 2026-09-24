"""Load a study from a folder: study.json + cases.csv + the case images.

The folder layout (it lives OUTSIDE the repo when images are real):

    study.json   {"key", "title", "description", "question", "choices", "confidence_max", "ai_source"}
    cases.csv    position,image,truth,ai_answer,ai_confidence,ai_box
    images...    the files named in the image column

Every check below refuses the whole study with a plain message; nothing is half-loaded.
Images are re-saved as bare 8-bit greyscale pixels under a random name, so no file name, no
DICOM header and no PNG/JPEG text travels into the site (CLAUDE.md rule 4).
"""

import csv
import hashlib
import io
import json
import re
import shutil
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from PIL import Image

from .models import Case, Study, new_case_code

STUDY_FIELDS = {"key", "title", "description", "question", "choices", "confidence_max", "ai_source"}
CASE_COLUMNS = ["position", "image", "truth", "ai_answer", "ai_confidence", "ai_box"]
LONG_NUMBER = re.compile(r"\d{8,}")  # national codes, accession numbers, patient IDs
KEY = re.compile(r"^[a-z0-9-]{3,50}$")


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
            if reader.fieldnames != CASE_COLUMNS:
                raise StudyFileError(f"cases.csv columns must be exactly: {','.join(CASE_COLUMNS)}")
            rows = list(reader)
    except FileNotFoundError:
        raise StudyFileError(f"No cases.csv in {folder}.")
    if not rows:
        raise StudyFileError("cases.csv has no cases.")
    return design, rows


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
        if folder.resolve() not in image.parents or not image.is_file():
            raise StudyFileError(f"{where}: image '{row['image']}' is not a file inside the study folder.")
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
                "source": image,
                "truth": row["truth"],
                "ai_answer": row["ai_answer"],
                "ai_confidence": confidence,
                "ai_box": box,
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


def load(folder: Path, open_now: bool = False) -> Study:
    folder = Path(folder)
    design, rows = read_design(folder)
    cases = check_cases(design, rows, folder)

    existing = Study.objects.filter(key=design["key"]).first()
    if existing and existing.state != Study.State.DRAFT:
        raise StudyFileError(f"Study '{design['key']}' is already open; its design is frozen (rule 3).")

    media_dir = settings.CASE_MEDIA_ROOT / design["key"]
    digest = hashlib.sha256(json.dumps(design, sort_keys=True).encode())
    prepared = []
    for case in cases:
        pixels = bare_pixels(case["source"])
        if case["ai_box"]:
            x, y, w, h = case["ai_box"]
            if x + w > pixels.width or y + h > pixels.height:
                raise StudyFileError(f"Case {case['position']}: ai_box reaches outside the image.")
        buffer = io.BytesIO()
        pixels.save(buffer, format="PNG", optimize=True)
        data = buffer.getvalue()
        sha = hashlib.sha256(data).hexdigest()
        digest.update(json.dumps({k: v for k, v in case.items() if k != "source"}, sort_keys=True).encode())
        digest.update(sha.encode())
        prepared.append((case, pixels.size, data, sha))

    with transaction.atomic():
        if existing:
            existing.delete()
        study = Study.objects.create(
            key=design["key"],
            title=design["title"],
            description=design.get("description") or "",
            question=design["question"],
            choices=design["choices"],
            confidence_max=int(design.get("confidence_max", 5)),
            ai_source=design.get("ai_source") or "AI model (simulated)",
            design_sha256=digest.hexdigest(),
        )
        if media_dir.exists():
            shutil.rmtree(media_dir)
        media_dir.mkdir(parents=True)
        for case, (width, height), data, sha in prepared:
            code = new_case_code()
            (media_dir / f"{code}.png").write_bytes(data)
            Case.objects.create(
                study=study,
                position=case["position"],
                code=code,
                image=f"{design['key']}/{code}.png",
                image_sha256=sha,
                width=width,
                height=height,
                truth=case["truth"],
                ai_answer=case["ai_answer"],
                ai_confidence=case["ai_confidence"],
                ai_box=case["ai_box"],
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
