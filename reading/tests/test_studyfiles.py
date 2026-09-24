"""Loading a study folder: every check refuses the whole study, and only pixels get through."""

import csv
import json
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from reading.models import Study
from reading.studyfiles import StudyFileError, load

DESIGN = {
    "key": "t-load",
    "title": "Load test",
    "question": "Fracture?",
    "choices": [
        {"value": "yes", "label": "Fracture"},
        {"value": "no", "label": "No fracture"},
        {"value": "unsure", "label": "Unsure"},
    ],
}
ROWS = [
    [1, "a.png", "yes", "yes", 0.90, "1 1 4 4"],
    [2, "b.png", "no", "no", 0.85, ""],
    [3, "c.png", "no", "yes", 0.88, "2 2 3 3"],  # planted false alarm
]


class LoadStudyTests(TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.media = Path(tempfile.mkdtemp())
        self.override = override_settings(CASE_MEDIA_ROOT=self.media)
        self.override.enable()
        # A source image that carries hidden text, like a name left in a PNG by some software.
        info = PngInfo()
        info.add_text("PatientName", "Should Not Travel")
        for name in ("a.png", "b.png", "c.png"):
            Image.new("RGB", (10, 12), (90, 90, 90)).save(self.folder / name, pnginfo=info)

    def tearDown(self):
        self.override.disable()

    def write(self, design=None, rows=None, header=None):
        (self.folder / "study.json").write_text(json.dumps(design or DESIGN), encoding="utf-8")
        with (self.folder / "cases.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header or ["position", "image", "truth", "ai_answer", "ai_confidence", "ai_box"])
            writer.writerows(rows or ROWS)

    def test_a_good_folder_loads_with_bare_pixels_and_random_names(self):
        self.write()
        study = load(self.folder, open_now=True)
        self.assertEqual(study.state, Study.State.OPEN)
        self.assertEqual([c.ai_planted for c in study.cases.order_by("position")], [False, False, True])
        for case in study.cases.all():
            self.assertNotIn(case.image, {"a.png", "b.png", "c.png"})
            with Image.open(self.media / case.image) as stored:
                self.assertEqual(stored.mode, "L")
                self.assertEqual(stored.size, (10, 12))
                self.assertNotIn("PatientName", stored.info)

    def test_sixteen_bit_images_become_eight_bit(self):
        Image.new("I;16", (10, 12), 3000).save(self.folder / "a.png")
        self.write()
        study = load(self.folder)
        with Image.open(self.media / study.cases.get(position=1).image) as stored:
            self.assertEqual(stored.mode, "L")

    def test_problems_refuse_the_whole_study(self):
        planted_too_confident = [row[:] for row in ROWS]
        planted_too_confident[2][4] = 0.97
        planted_without_box = [row[:] for row in ROWS]
        planted_without_box[2][5] = ""  # the correct 'yes' has a box, the planted 'yes' has none
        cases = {
            "an extra column": dict(header=["position", "image", "truth", "ai_answer", "ai_confidence", "ai_box", "patient_id"]),
            "an unknown answer": dict(rows=[[1, "a.png", "maybe", "yes", 0.9, ""]]),
            "a long number in the title": dict(design={**DESIGN, "title": "Cases 1234567890"}),
            "a gap in positions": dict(rows=[[1, "a.png", "yes", "yes", 0.9, ""], [3, "b.png", "no", "no", 0.9, ""]]),
            "an image outside the folder": dict(rows=[[1, "../x.png", "yes", "yes", 0.9, ""]]),
            "a box outside the image": dict(rows=[[1, "a.png", "yes", "yes", 0.9, "5 5 50 50"]]),
            "a box of zero size": dict(rows=[[1, "a.png", "yes", "yes", 0.9, "1 1 0 0"]]),
            "a planted confidence that stands out": dict(rows=planted_too_confident),
            "a planted suggestion that alone has no box": dict(rows=planted_without_box),
            "a confidence scale of 0": dict(design={**DESIGN, "confidence_max": 0}),
            "choices written as plain words": dict(design={**DESIGN, "choices": ["yes", "no"]}),
            "a row longer than the header": dict(rows=[[1, "a.png", "yes", "yes", 0.9, "", "extra"]]),
        }
        for problem, kwargs in cases.items():
            with self.subTest(problem):
                self.write(**kwargs)
                with self.assertRaises(StudyFileError):
                    load(self.folder)
                self.assertFalse(Study.objects.exists())

    def test_an_open_study_cannot_be_reloaded(self):
        self.write()
        load(self.folder, open_now=True)
        with self.assertRaises(StudyFileError):
            load(self.folder)

    def test_a_row_without_the_empty_last_field_loads(self):
        # "2,b.png,no,no,0.85" with no trailing comma: the empty ai_box is simply left out.
        self.write(rows=[ROWS[0], ROWS[1][:5], ROWS[2]])
        self.assertIsNone(load(self.folder).cases.get(position=2).ai_box)
