"""Prepare the "Nabothian cyst?" MRI stack study from the public UMD dataset.

Run:     uv run --group prep python prep/umd_stack.py
Slicer:  uv run --group prep python prep/umd_stack.py slicer case-03   (one case, for the owner's check)

Design notes: docs/research/2026-09-24-stack-viewer-and-slicer.md, sections 4 and 5.
Reads the local UMD copy on D: (never changes it) and writes only OUTSIDE this repo:

    study/     what load_study reads: study.json, cases.csv, spares.csv and one folder per case
               (case-01/000.png, 001.png, ...): one 8-bit greyscale slice per file, in display order
    private/   map.csv: case folder -> UMD case id, truth, AI details and the key point for Slicer
               contact-sheets/case-NN.png: all slices of a case, numbered as the phone numbers them,
               with the key slice, the AI box (yellow) and the largest expert cyst (green) marked
               NEVER in the repo or on the site: UMD ids are public, so they give the answer away.

Per volume: load the pixels and the affine (never the header's text fields); turn the axes so
rows run superior -> inferior, columns anterior -> posterior and slices patient right -> left
(sagittal, as a PACS shows it); window the whole volume with one percentile pair to 8 bits;
shrink each slice so its long side is at most 512 px.

Truth comes from the expert mask (label 4 = Nabothian cyst). The AI answer and box come from
the out-of-fold nnU-Net ensemble: each case was predicted by a model that never trained on it.
So every AI suggestion is the model's real answer. The two wrong ones (positions 4 and 7) are
real model errors, chosen on purpose; the site still treats them as planted (rule 5).
The shown confidences are fixed per position (PLAN), not the model's own.

The owner looks at every contact sheet before load_study runs (right label? any text?).
Claude never views them. Nothing here prints UMD ids or pixels, only counts.
"""

import csv
import itertools
import json
import math
import os
import random
import subprocess
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
from nibabel.orientations import apply_orientation, axcodes2ornt, inv_ornt_aff, io_orientation, ornt_transform
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

UMD = Path(r"D:\UMD")
IMAGES = UMD / r"data\nnUNet_raw\Dataset501_UMDMyoma\imagesTr"   # UMD_NNNN_0000.nii.gz: sagittal T2
MASKS = UMD / r"data\nnUNet_raw\Dataset501_UMDMyoma\labelsTr"    # UMD_NNNN.nii.gz: 1 wall, 2 cavity, 3 myoma, 4 cyst
ENSEMBLES = UMD / r"models\nnUNet_results\Dataset501_UMDMyoma\ensembles"  # one folder: the 2D + 3D ensemble
ROOT = Path(r"C:\Users\Mahbod\Desktop\datasets\umd-cyst")
STUDY, PRIVATE = ROOT / "study", ROOT / "private"
SLICER = Path(os.environ.get("SLICER") or Path(os.environ.get("LOCALAPPDATA", "")) / r"slicer.org\3D Slicer 5.12.4\Slicer.exe")

CYST = 4                    # the mask label of a Nabothian cyst
DISPLAY = ("I", "P", "L")   # array axes run toward inferior (rows), posterior (columns), patient left (slices)
PERCENTILES = (0.1, 99.9)   # one window per volume; Slicer's automatic window uses the same pair
MAX_SIDE = 512              # long side of a slice, in pixels
TRUTH_MIN_MM = 5.0          # truth "yes": the largest cyst is at least this wide (equivalent diameter)
AI_MIN_MM = 3.0             # AI "yes": the model found a cyst at least this wide
BOX_PAD, BOX_MIN = 4, 12    # AI box: pixels added on each side; smallest width and height
SEED = 20261103             # a fixed seed: re-running picks the same cases and the same names
SHEET_COLUMNS, SHEET_TILE, SHEET_GAP = 6, 320, 28  # contact sheet: tiles per row, tile size, gap for the number (px)
SHEET_AI, SHEET_TRUTH = "#ffff00", "#00ff00"       # contact sheet only: yellow AI box, green truth box

# Positions 1-8: (truth, AI answer, AI confidence), as in prep/ikhc_wrist.py: 4 is the missed
# cyst and 7 the false alarm. TP = true positive (both yes), TN = true negative (both no),
# FN = false negative (the model misses a cyst), FP = false positive (a cyst where none is drawn).
PLAN = [("yes", "yes", 0.91), ("no", "no", 0.88), ("yes", "yes", 0.86), ("yes", "no", 0.87),
        ("no", "no", 0.90), ("yes", "yes", 0.84), ("no", "yes", 0.89), ("no", "no", 0.85)]
CATEGORY = {("yes", "yes"): "TP", ("no", "no"): "TN", ("yes", "no"): "FN", ("no", "yes"): "FP"}
COLUMNS = ["position", "image", "truth", "ai_answer", "ai_confidence", "ai_box", "ai_slices"]
# The description is the CC BY credit readers see on the site. The figshare DOI
# (10.6084/m9.figshare.23541312.v3) is left out on purpose: its 8-digit run trips load_study's
# long-number check (studyfiles.LONG_NUMBER). The paper DOI links to the data, and the README
# carries the full credit. Do not loosen LONG_NUMBER for a citation.
DESIGN = {
    "key": "umd-cyst",
    "title": "Nabothian cyst on uterine MRI (public UMD data)",
    "description": "Public UMD dataset: Pan et al., Scientific Data 2024, doi:10.1038/s41597-024-03170-x; "
                   "data UMD.zip on figshare. Licence CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. "
                   "Modified: reoriented, windowed to 8 bits, downsized; answers derived from the masks.",
    "question": "Nabothian cyst?",
    "choices": [
        {"value": "yes", "label": "Cyst"},
        {"value": "no", "label": "No cyst"},
        {"value": "unsure", "label": "Unsure"},
    ],
    "confidence_max": 5,
    "ai_source": "AI model (research)",
}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def ensemble_folder():
    folders = [p for p in ENSEMBLES.iterdir() if p.is_dir()]
    if len(folders) != 1:
        raise SystemExit(f"Expected one ensemble folder in {ENSEMBLES}, found {len(folders)}.")
    return folders[0]


def to_display(path, image=None):
    """Load one NIfTI volume in display order. Returns (array, display affine).

    image: the case's T2 file, already opened; a mask or prediction must match its shape and affine.
    The display affine maps (row, column, slice) of the returned array to patient mm (RAS)."""
    nifti = nib.load(path)
    if len(nifti.shape) != 3:
        raise SystemExit(f"{path.name} is not one 3-D volume; refused.")
    if image is not None and (nifti.shape != image.shape or not np.allclose(nifti.affine, image.affine, atol=1e-3)):
        raise SystemExit(f"{path.name} does not have its image's shape and position; refused.")
    turn = ornt_transform(io_orientation(nifti.affine), axcodes2ornt(DISPLAY))
    array = apply_orientation(np.asanyarray(nifti.dataobj), turn)  # permutes and flips only, no resampling
    return array, nifti.affine @ inv_ornt_aff(turn, nifti.shape)


def final_size(rows, cols):
    """Slice size after shrinking: long side at most MAX_SIDE, same shape."""
    scale = min(1.0, MAX_SIDE / max(rows, cols))
    return round(rows * scale), round(cols * scale)


def cyst_parts(labels, mm):
    """Every 3-D piece of label 4, largest first, with its width in mm and its key point."""
    pieces, _ = ndimage.label(labels == CYST)
    parts = []
    for number, box in enumerate(ndimage.find_objects(pieces), start=1):
        piece = pieces[box] == number
        areas = piece.sum(axis=(0, 1))  # pixels on each slice
        k = int(areas.argmax())         # the piece's largest slice
        rows, cols = np.nonzero(piece[:, :, k])
        parts.append({
            "voxels": int(areas.sum()),
            "mm": 2 * math.sqrt(areas[k] * mm[0] * mm[1] / math.pi),  # equivalent diameter, native mm
            "box": box,
            "piece": piece,
            "key": (box[0].start + (rows.min() + rows.max()) / 2, box[1].start + (cols.min() + cols.max()) / 2,
                    box[2].start + k),
        })
    return sorted(parts, key=lambda p: -p["voxels"])


def ai_rect(box, shape):
    """The AI box in final slice pixels [x, y, w, h]: the piece's bounding box over all its slices,
    scaled exactly (no mask resampling, so a small piece cannot vanish), padded, at least
    BOX_MIN wide and high, clipped to the slice. One rule for every box (rule 6)."""
    edges = []
    for axis, size in enumerate(final_size(*shape[:2])):
        scale = size / shape[axis]
        low = math.floor(box[axis].start * scale) - BOX_PAD
        high = math.ceil(box[axis].stop * scale) + BOX_PAD
        if high - low < BOX_MIN:
            low -= (BOX_MIN - (high - low)) // 2
            high = low + BOX_MIN
        edges.append((max(low, 0), min(high, size)))
    (top, bottom), (left, right) = edges
    return [left, top, right - left, bottom - top]


def survey(case_id, ensemble):
    """Truth and AI answer of one case, from the two masks (the T2 pixels are not read here)."""
    image = nib.load(IMAGES / f"{case_id}_0000.nii.gz")  # the header only, for shape and affine
    if len(image.shape) != 3:
        raise SystemExit(f"{case_id}: the image is not one 3-D volume; refused.")
    truth_labels, affine = to_display(MASKS / f"{case_id}.nii.gz", image)
    ai_labels, _ = to_display(ensemble / f"{case_id}.nii.gz", image)
    mm = np.sqrt((affine[:3, :3] ** 2).sum(axis=0))  # voxel size along rows, columns and slices
    truth_parts = cyst_parts(truth_labels, mm)
    ai_parts = [p for p in cyst_parts(ai_labels, mm) if p["mm"] >= AI_MIN_MM]
    if not truth_parts:
        truth = "no"
    elif truth_parts[0]["mm"] >= TRUTH_MIN_MM:
        truth = "yes"
    else:
        truth = None  # only a small cyst: neither a clear yes nor a clear no, so not used
    shape = truth_labels.shape
    case = {"umd": case_id, "truth": truth, "ai": "yes" if ai_parts else "no",
            "cyst_mm": truth_parts[0]["mm"] if truth_parts else 0.0, "ai_mm": 0.0, "box": None, "slices": None,
            "on_cyst": False, "truth_box": None, "truth_slices": None}
    if truth_parts:  # the largest expert cyst, marked on the private contact sheet only
        largest_box = truth_parts[0]["box"]
        case.update(truth_box=ai_rect(largest_box, shape),
                    truth_slices=[largest_box[2].start, largest_box[2].stop - 1])
    if ai_parts:
        part = ai_parts[0]  # the largest piece the model found
        case.update(ai_mm=part["mm"], box=ai_rect(part["box"], shape),
                    slices=[part["box"][2].start, part["box"][2].stop - 1])
        if truth_parts:  # does the AI piece touch the largest truth cyst, the one that makes "yes"?
            largest = np.zeros(shape, bool)
            largest[truth_parts[0]["box"]] = truth_parts[0]["piece"]
            case["on_cyst"] = bool(largest[part["box"]][part["piece"]].any())
    # The key point: the truth cyst, else the AI's piece, else the middle of the start slice.
    parts = truth_parts or ai_parts
    point = parts[0]["key"] if parts else ((shape[0] - 1) / 2, (shape[1] - 1) / 2, (shape[2] - 1) // 2)
    case["key_slice"] = int(point[2])
    case["key_ras"] = (affine @ [*point, 1])[:3]
    return case


def extent(case):
    """AI box width, box height and slice span: what the loader compares for rule 6."""
    return case["box"][2], case["box"][3], case["slices"][1] - case["slices"][0] + 1


def fits(false_alarm, true_ones):
    """True when the false alarm's box extent lies inside the range of the true boxes."""
    ranges = list(zip(*map(extent, true_ones)))
    return all(min(r) <= value <= max(r) for value, r in zip(extent(false_alarm), ranges))


def choose(cases):
    """Per category: the study's cases and the spares (3 TP, 3 TN, 1 FN, 1 FP each)."""
    rng = random.Random(SEED)
    pools = {name: [] for name in ("TP", "TN", "FN", "FP")}
    for case in cases:
        category = CATEGORY.get((case["truth"], case["ai"]))
        if category == "TP" and not case["on_cyst"]:
            continue  # the model said yes, but its box is not on the largest cyst
        if category:
            pools[category].append(case)
    for pool in pools.values():
        rng.shuffle(pool)
    need = {"TP": 6, "TN": 6, "FN": 2, "FP": 2}
    for name, count in need.items():
        if len(pools[name]) < count:
            raise SystemExit(f"Only {len(pools[name])} {name} cases; {count} needed.")
    # Rule 6: both false alarms (study and spare) need boxes like the three true study boxes.
    for trio in itertools.combinations(pools["TP"], 3):
        alarms = [c for c in pools["FP"] if fits(c, trio)]
        if len(alarms) >= 2:
            break
    else:
        raise SystemExit("No three true AI boxes cover the size and slice span of two false alarms.")
    chosen = {c["umd"] for c in trio}
    true_ones = list(trio) + [c for c in pools["TP"] if c["umd"] not in chosen][:3]
    picks = {"TP": true_ones, "TN": pools["TN"][:6], "FN": pools["FN"][:2], "FP": alarms[:2]}
    per_case = {"TP": 3, "TN": 3, "FN": 1, "FP": 1}
    study = {name: picks[name][:n] for name, n in per_case.items()}
    spares = [c for name, n in per_case.items() for c in picks[name][n:]]
    return pools, study, spares


def write_stack(case, folder):
    """Window, turn and shrink one T2 volume; write its slices as 000.png, 001.png, ...
    Returns the slice images and their total size in bytes."""
    volume, _ = to_display(IMAGES / f"{case['umd']}_0000.nii.gz")
    volume = volume.astype(np.float32)
    low, high = np.percentile(volume, PERCENTILES)  # whole volume: never per slice
    scaled = np.clip((volume - low) / max(high - low, 1e-6), 0, 1) * 255
    rows, cols = final_size(*volume.shape[:2])
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("[0-9][0-9][0-9].png"):
        old.unlink()  # slices from an earlier run of this script
    slices, total = [], 0
    for k in range(volume.shape[2]):
        plane = Image.fromarray(np.ascontiguousarray(scaled[:, :, k]))  # float pixels ("F")
        if plane.size != (cols, rows):
            plane = plane.resize((cols, rows), Image.LANCZOS)
        pixels = np.clip(np.rint(np.asarray(plane)), 0, 255).astype(np.uint8)
        image = Image.fromarray(pixels)  # 2-D uint8 -> greyscale ("L"), pixels only
        path = folder / f"{k:03d}.png"
        image.save(path, format="PNG", optimize=True)
        slices.append(image)
        total += path.stat().st_size
    return slices, total


def contact_sheet(slices, path, case):
    """All slices of one case on one page, numbered as on the phone ("12 / 24"). The caption
    also says "key" on the key slice, "AI" on the AI box's slices and "truth" on the largest
    expert cyst's slices. Those tiles get a thin box just outside the region: yellow for the
    AI, green for the truth. The sheet is private, so the marks never reach a reader."""
    rows = math.ceil(len(slices) / SHEET_COLUMNS)
    pitch = SHEET_TILE + SHEET_GAP  # one tile plus the gap to its right and below it
    sheet = Image.new("RGB", (SHEET_COLUMNS * pitch, rows * pitch), "black")
    draw, font = ImageDraw.Draw(sheet), ImageFont.load_default(size=20)
    marks = (("AI", case["slices"], case["box"], SHEET_AI),
             ("truth", case["truth_slices"], case["truth_box"], SHEET_TRUTH))
    for index, image in enumerate(slices):
        tile = image.copy()
        tile.thumbnail((SHEET_TILE, SHEET_TILE), Image.LANCZOS)
        x, y = (index % SHEET_COLUMNS) * pitch, (index // SHEET_COLUMNS) * pitch
        sheet.paste(tile.convert("RGB"), (x, y))
        caption = f"{index + 1} / {len(slices)}" + (" key" if index == case["key_slice"] else "")
        scale = tile.width / image.width
        for name, span, box, colour in marks:
            if span and span[0] <= index <= span[1]:
                caption += f" {name}"
                bx, by, bw, bh = box
                draw.rectangle([x + bx * scale - 2, y + by * scale - 2, x + (bx + bw) * scale + 1,
                                y + (by + bh) * scale + 1], outline=colour)
        draw.text((x + 6, y + SHEET_TILE + 3), caption, fill="white", font=font)
    sheet.save(path, format="PNG", optimize=True)


def main():
    ensemble = ensemble_folder()
    ids = sorted(p.name.removesuffix("_0000.nii.gz") for p in IMAGES.glob("UMD_*_0000.nii.gz"))
    cases = [survey(case_id, ensemble) for case_id in ids]
    pools, study, spares = choose(cases)

    rows = []  # the 8 study cases in PLAN order, then the 8 spares
    for position, (truth, ai_answer, confidence) in enumerate(PLAN, start=1):
        rows.append((position, confidence, study[CATEGORY[(truth, ai_answer)]].pop(0)))
    rows += [("", "", case) for case in spares]
    rng = random.Random(SEED)
    names = [f"case-{n:02d}" for n in range(1, len(rows) + 1)]
    rng.shuffle(names)

    sheets = PRIVATE / "contact-sheets"
    sheets.mkdir(parents=True, exist_ok=True)
    table, map_rows, sizes, lengths = [], [], [], []
    for name, (position, confidence, case) in zip(names, rows):
        slices, size = write_stack(case, STUDY / name)
        contact_sheet(slices, sheets / f"{name}.png", case)
        box, span = case["box"], case["slices"]
        table.append({"position": position, "image": name, "truth": case["truth"], "ai_answer": case["ai"],
                      "ai_confidence": confidence, "ai_box": " ".join(map(str, box)) if box else "",
                      "ai_slices": " ".join(map(str, span)) if span else ""})
        map_rows.append({"folder": name, "position": position or "spare", "umd_case": case["umd"],
                         "category": CATEGORY[(case["truth"], case["ai"])], "truth": case["truth"], "ai_answer": case["ai"],
                         "cyst_mm": f"{case['cyst_mm']:.1f}", "ai_cyst_mm": f"{case['ai_mm']:.1f}",
                         "ai_box": table[-1]["ai_box"], "ai_slices_on_phone": f"{span[0] + 1}-{span[1] + 1}" if span else "",
                         "key_slice_on_phone": case["key_slice"] + 1, "slices": len(slices),
                         "key_point_ras": " ".join(f"{v:.1f}" for v in case["key_ras"]),
                         "size": f"{slices[0].width}x{slices[0].height}", "png_bytes": size})
        sizes.append(size)
        lengths.append(len(slices))

    write_csv(STUDY / "cases.csv", [r for r in table if r["position"] != ""], COLUMNS)
    write_csv(STUDY / "spares.csv", [r for r in table if r["position"] == ""], COLUMNS)
    (STUDY / "study.json").write_text(json.dumps(DESIGN, indent=2), encoding="utf-8")
    write_csv(PRIVATE / "map.csv", sorted(map_rows, key=lambda r: r["folder"]), list(map_rows[0]))

    counts = {"yes": 0, "no": 0, None: 0}
    for case in cases:
        counts[case["truth"]] += 1
    off_cyst = sum(1 for c in cases if (c["truth"], c["ai"]) == ("yes", "yes") and not c["on_cyst"])
    print(f"surveyed {len(cases)} volumes: {counts['yes']} with a cyst of {TRUTH_MIN_MM:g} mm or more, "
          f"{counts['no']} with no cyst label, {counts[None]} not used (only smaller cysts)")
    print("model answers: " + ", ".join(f"{name} {len(pool)}" for name, pool in pools.items())
          + f" (+{off_cyst} TP left out: the AI box is not on the largest cyst)")
    print("chosen: 8 study cases (TP 3, TN 3, FN 1, FP 1) + 8 spares (the same mix)")
    print(f"slices per case: {min(lengths)}-{max(lengths)}; PNG per case: min {min(sizes) / 1e6:.2f} MB, "
          f"median {float(np.median(sizes)) / 1e6:.2f} MB, max {max(sizes) / 1e6:.2f} MB")
    print(f"study folder: {STUDY}\nowner's eye check: every sheet in {sheets}, then load_study")


def open_in_slicer(folder):
    """Start 3D Slicer with prep/slicer_check.py on one prepared case (the owner's own Slicer)."""
    cases = {row["folder"]: row for row in read_csv(PRIVATE / "map.csv")}
    if folder not in cases:
        raise SystemExit(f"No case '{folder}' in {PRIVATE / 'map.csv'}. Use a folder name such as case-03.")
    row = cases[folder]
    env = dict(os.environ,
               NESHAT_T2=str(IMAGES / f"{row['umd_case']}_0000.nii.gz"),
               NESHAT_TRUTH=str(MASKS / f"{row['umd_case']}.nii.gz"),
               NESHAT_AI=str(ensemble_folder() / f"{row['umd_case']}.nii.gz"),
               NESHAT_POINT=row["key_point_ras"],
               NESHAT_PERCENTILES=" ".join(map(str, PERCENTILES)))
    if not SLICER.is_file():
        raise SystemExit(f"3D Slicer is not at {SLICER}. Set the SLICER environment variable to Slicer.exe.")
    subprocess.Popen([str(SLICER), "--python-script", str(Path(__file__).with_name("slicer_check.py"))], env=env)
    print(f"Opening {folder} in 3D Slicer: key slice {row['key_slice_on_phone']} of {row['slices']} on the phone.")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "slicer":
        open_in_slicer(sys.argv[2])
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("Use: umd_stack.py  (prepare the study)  or  umd_stack.py slicer case-NN")
