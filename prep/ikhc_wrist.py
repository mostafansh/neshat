"""Prepare the IKHC hand/wrist study folder from downloaded DICOM (docs/tasks/ikhc-wrist-cases.md).

Run:  uv run --group prep python prep/ikhc_wrist.py

Reads and writes only in the dataset folder OUTSIDE this repo:

    raw/       DICOM, as downloaded by the ikhc_fetch skill (never copied anywhere else)
    private/   candidates.csv + manifest.csv (in), map.csv + owner_check.csv (out). NEVER in the repo.
    study/     case-NN.png, study.json, cases.csv, spares.csv: what load_study reads

For each case it takes one frontal (PA/AP) image, applies the image's own window, keeps
8-bit greyscale pixels only (no header, no text chunk) and trims blank borders. File names
are neutral and shuffled. Nothing here prints names, national codes or report text.

Burned-in text is NOT removed reliably by code. The owner opens every PNG and checks it by eye
before load_study runs (CLAUDE.md, data rules). To crop a case by hand after that check, fill
crop_left/top/right/bottom (pixels to cut) in private/crops.csv and run the script again.
"""

import csv
import json
import random
import re
from pathlib import Path

import numpy as np
import pydicom
from PIL import Image

ROOT = Path(r"C:\Users\Mahbod\Desktop\datasets\ikhc-wrist")
RAW, PRIVATE, STUDY = ROOT / "raw", ROOT / "private", ROOT / "study"
MAX_SIDE = 2560  # long side in pixels; plenty for a phone, and a smaller download
PER_CLASS = 8    # 4 cases + 4 spares with a fracture, the same without

FRONTAL = re.compile(r"\b(PA|AP)\b")
NOT_FRONTAL = re.compile(r"LAT|OBL|LL|RL", re.I)
PREFERRED_PART = {"wrist": re.compile(r"WRIST|FOREARM", re.I), "hand": re.compile(r"HAND|FINGER", re.I)}

# Positions 1-8: (truth, AI answer, AI confidence). As in make_synthetic_study: cases 1 and 2
# have correct AI; 4 is the planted miss and 7 the planted false alarm.
PLAN = [("yes", "yes", 0.91), ("no", "no", 0.88), ("yes", "yes", 0.86), ("yes", "no", 0.87),
        ("no", "no", 0.90), ("yes", "yes", 0.84), ("no", "yes", 0.89), ("no", "no", 0.85)]
DESIGN = {
    "key": "ikhc-wrist",
    "title": "Fracture on hand/wrist X-ray",
    "description": "Real hand and wrist X-rays, de-identified.",
    "question": "Fracture?",
    "choices": [
        {"value": "yes", "label": "Fracture"},
        {"value": "no", "label": "No fracture"},
        {"value": "unsure", "label": "Unsure"},
    ],
    "confidence_max": 5,
    "ai_source": "AI model (simulated)",
}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def choose_image(candidate, instances):
    """The frontal image of the right body part. Returns (instance row, header, view_uncertain)."""
    options = []
    for inst in instances:
        path = RAW / inst["study_key"] / inst["series_key"] / f"{inst['instance_key']}.dcm"
        header = pydicom.dcmread(path, stop_before_pixels=True)
        desc = inst["series_desc"].upper()
        view = str(header.get("ViewPosition", "")).upper()
        if NOT_FRONTAL.search(desc) or view in {"LAT", "LL", "RL"}:
            continue
        known = view in {"PA", "AP"} or bool(FRONTAL.search(desc))
        part = "wrist" if candidate["body_part"] == "wrist" else "hand"
        options.append((not known, not PREFERRED_PART[part].search(desc), int(header.get("InstanceNumber") or 0), inst, header))
    if not options:
        return None, None, True
    options.sort(key=lambda o: o[:3])
    uncertain, _, _, inst, header = options[0]
    return inst, header, uncertain


def to_8bit(ds):
    """Pixels -> 8-bit greyscale with the image's own window (1st-99th percentile if none)."""
    pixels = ds.pixel_array.astype(np.float64)
    pixels = pixels * float(ds.get("RescaleSlope", 1)) + float(ds.get("RescaleIntercept", 0))
    centre, width = ds.get("WindowCenter"), ds.get("WindowWidth")
    if isinstance(centre, pydicom.multival.MultiValue):
        centre, width = centre[0], width[0]
    if centre is not None and width is not None and float(width) > 1:
        low, high = float(centre) - float(width) / 2, float(centre) + float(width) / 2
    else:
        low, high = np.percentile(pixels, [1, 99])
    scaled = np.clip((pixels - low) / max(high - low, 1e-6), 0, 1) * 255
    if ds.get("PhotometricInterpretation") == "MONOCHROME1":
        scaled = 255 - scaled
    return scaled.astype(np.uint8)


def trim_blank_borders(pixels, spread=2.0):
    """Cut rows and columns at the edges that hold no image (almost one flat grey)."""
    rows = np.where(pixels.std(axis=1) > spread)[0]
    cols = np.where(pixels.std(axis=0) > spread)[0]
    if len(rows) == 0 or len(cols) == 0:
        return pixels, (0, 0, 0, 0)
    top, bottom, left, right = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
    box = (int(left), int(top), int(pixels.shape[1] - right), int(pixels.shape[0] - bottom))
    return pixels[top:bottom, left:right], box


def main():
    candidates = [c for c in read_csv(PRIVATE / "candidates.csv") if c["study_key"]]
    manifest = read_csv(PRIVATE / "manifest.csv")
    crops_path = PRIVATE / "crops.csv"
    crops = {r["file"]: r for r in read_csv(crops_path)} if crops_path.exists() else {}
    STUDY.mkdir(exist_ok=True)

    prepared = []
    for candidate in candidates:
        instances = [i for i in manifest if i["study_key"] == candidate["study_key"]]
        inst, header, uncertain = choose_image(candidate, instances)
        if inst is None:
            continue
        prepared.append({"candidate": candidate, "inst": inst, "uncertain": uncertain,
                         "burned_in": str(header.get("BurnedInAnnotation", "")).upper() == "YES"})

    # Per class: known frontal views first, then no burned-in text flag, then the report order.
    chosen = []
    for truth in ("yes", "no"):
        pool = [p for p in prepared if p["candidate"]["truth"] == truth]
        pool.sort(key=lambda p: (p["uncertain"], p["burned_in"]))
        chosen += pool[:PER_CLASS]

    rng = random.Random(20261103)  # a fixed seed: re-running gives the same neutral names
    names = [f"case-{n:02d}.png" for n in range(1, len(chosen) + 1)]
    rng.shuffle(names)

    map_rows, check_rows = [], []
    for name, item in zip(names, chosen):
        c, inst = item["candidate"], item["inst"]
        ds = pydicom.dcmread(RAW / inst["study_key"] / inst["series_key"] / f"{inst['instance_key']}.dcm")
        pixels, box = trim_blank_borders(to_8bit(ds))
        manual = crops.get(name)
        if manual:
            l, t, r, b = (int(manual[k] or 0) for k in ("crop_left", "crop_top", "crop_right", "crop_bottom"))
            pixels = pixels[t:pixels.shape[0] - b, l:pixels.shape[1] - r]
        image = Image.fromarray(pixels)  # 2-D uint8 -> greyscale ("L")
        if max(image.size) > MAX_SIDE:
            image.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        image.save(STUDY / name, format="PNG", optimize=True)  # pixels only: no text chunks
        map_rows.append({"file": name, "truth": c["truth"], "body_part": c["body_part"], "paper_id": c["paper_id"],
                         "report_date": c["report_date"], "study_key": inst["study_key"], "series_key": inst["series_key"],
                         "instance_key": inst["instance_key"], "series_desc": inst["series_desc"],
                         "view_uncertain": item["uncertain"], "burned_in_flag": item["burned_in"],
                         "trimmed_ltrb": " ".join(map(str, box)), "size": f"{image.width}x{image.height}"})
        check_rows.append({"file": name, "look_closely": "YES (header says text is burned in)" if item["burned_in"] else "",
                           "view_to_check": "is this the frontal (PA/AP) view?" if item["uncertain"] else "",
                           "report_says": "fracture" if c["truth"] == "yes" else "no fracture", "body_part": c["body_part"],
                           "no_text_left (y/n)": "", "label_ok (y/n)": "", "notes": ""})

    map_rows.sort(key=lambda r: r["file"])
    check_rows.sort(key=lambda r: r["file"])
    write_csv(PRIVATE / "map.csv", map_rows, list(map_rows[0]))
    write_csv(PRIVATE / "owner_check.csv", check_rows, list(check_rows[0]))
    if not crops_path.exists():
        write_csv(crops_path, [{"file": r["file"], "crop_left": "", "crop_top": "", "crop_right": "", "crop_bottom": ""}
                               for r in map_rows], ["file", "crop_left", "crop_top", "crop_right", "crop_bottom"])

    # The 8 study cases follow PLAN; the rest are spares with the same columns.
    by_truth = {"yes": [r for r in map_rows if r["truth"] == "yes"], "no": [r for r in map_rows if r["truth"] == "no"]}
    columns = ["position", "image", "truth", "ai_answer", "ai_confidence", "ai_box"]
    cases = []
    for position, (truth, ai_answer, confidence) in enumerate(PLAN, start=1):
        row = by_truth[truth].pop(0)
        cases.append({"position": position, "image": row["file"], "truth": truth,
                      "ai_answer": ai_answer, "ai_confidence": confidence, "ai_box": ""})
    spares = [{"position": "", "image": r["file"], "truth": r["truth"], "ai_answer": "", "ai_confidence": "", "ai_box": ""}
              for r in by_truth["yes"] + by_truth["no"]]
    write_csv(STUDY / "cases.csv", cases, columns)
    write_csv(STUDY / "spares.csv", spares, columns)
    (STUDY / "study.json").write_text(json.dumps(DESIGN, indent=2), encoding="utf-8")

    print(f"prepared {len(chosen)} PNGs: {sum(r['truth'] == 'yes' for r in map_rows)} fracture, "
          f"{sum(r['truth'] == 'no' for r in map_rows)} no fracture")
    print(f"view to check by eye: {sum(r['view_uncertain'] for r in map_rows)}; "
          f"burned-in text flag: {sum(r['burned_in_flag'] for r in map_rows)}")
    print(f"cases.csv: 8 cases; spares.csv: {len(spares)} spares; checklist: {PRIVATE / 'owner_check.csv'}")


if __name__ == "__main__":
    main()
