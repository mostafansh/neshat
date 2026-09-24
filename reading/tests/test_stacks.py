"""Stacks of slices (MRI): the folder format, the stack file, the image address and rule 1."""

import csv
import hashlib
import io
import json
import shutil
import struct
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from reading.demo import make_phantom_stack
from reading.models import Case, ImageAccess, Study, User
from reading.studyfiles import STACK_COLUMNS, StudyFileError, load

DESIGN = {
    "key": "t-stack",
    "title": "Stack test",
    "question": "Cyst?",
    "choices": [
        {"value": "yes", "label": "Cyst"},
        {"value": "no", "label": "No cyst"},
        {"value": "unsure", "label": "Unsure"},
    ],
}
ROWS = [
    [1, "s1", "yes", "yes", 0.90, "1 1 4 4", "1 2"],
    [2, "s2", "no", "no", 0.85, "", ""],
    [3, "s3", "no", "yes", 0.88, "2 2 4 4", "0 1"],  # planted false alarm: same box size and span
    [4, "x.png", "no", "no", 0.86, "", ""],  # a single image in the same study
]
SLICE_SIZE = (12, 10)


def temporary_folder(test: TestCase) -> Path:
    folder = Path(tempfile.mkdtemp())
    test.addCleanup(shutil.rmtree, folder, ignore_errors=True)
    return folder


def split_stack(data: bytes) -> list[bytes]:
    """Split a stack file by the layout in docs/reading-api.md. Refuses any other byte."""
    if data[:4] != b"NSTK":
        raise ValueError("no NSTK at the start")
    (count,) = struct.unpack(">I", data[4:8])
    slices, offset = [], 8
    for _ in range(count):
        (length,) = struct.unpack(">I", data[offset : offset + 4])
        slices.append(data[offset + 4 : offset + 4 + length])
        offset += 4 + length
    if offset != len(data):
        raise ValueError("bytes left over after the last slice")
    return slices


class StackFolderTestCase(TestCase):
    def setUp(self):
        self.media = temporary_folder(self)
        self.override = override_settings(CASE_MEDIA_ROOT=self.media)
        self.override.enable()
        self.folder = self.good_folder()

    def tearDown(self):
        self.override.disable()

    def good_folder(self) -> Path:
        self.folder = temporary_folder(self)
        for name in ("s1", "s2", "s3"):
            self.write_stack(name)
        Image.new("L", SLICE_SIZE, 50).save(self.folder / "x.png")
        self.write()
        return self.folder

    def write_stack(self, name, count=4, size=SLICE_SIZE, mode="L"):
        """Slices whose grey value is 10, 20, 30 …, each with hidden text like a name left by some software."""
        info = PngInfo()
        info.add_text("PatientName", "Should Not Travel")
        stack = self.folder / name
        stack.mkdir(exist_ok=True)
        for index in range(count):
            Image.new(mode, size, 10 * (index + 1)).save(stack / f"{index:03d}.png", pnginfo=info)

    def write(self, rows=None, header=STACK_COLUMNS):
        (self.folder / "study.json").write_text(json.dumps(DESIGN), encoding="utf-8")
        with (self.folder / "cases.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows or ROWS)


class LoadStackTests(StackFolderTestCase):
    def test_a_stack_folder_becomes_one_stack_file_of_bare_slices(self):
        study = load(self.folder)
        case = study.cases.get(position=1)
        self.assertTrue(case.image.endswith(".stk"))
        self.assertNotIn("s1", case.image)
        self.assertEqual((case.slices, case.width, case.height), (4, *SLICE_SIZE))
        self.assertEqual((case.ai_box, case.ai_slices), ([1, 1, 4, 4], [1, 2]))

        data = (self.media / case.image).read_bytes()
        self.assertEqual(case.image_sha256, hashlib.sha256(data).hexdigest())
        self.assertNotIn(b"PatientName", data)
        slices = split_stack(data)
        self.assertEqual(len(slices), 4)
        for index, png in enumerate(slices):
            with Image.open(io.BytesIO(png)) as image:
                self.assertEqual((image.format, image.mode, image.size), ("PNG", "L", SLICE_SIZE))
                self.assertEqual(image.getextrema(), (10 * (index + 1),) * 2)  # never stretched

    def test_a_single_image_in_a_stack_study_stays_a_png(self):
        case = load(self.folder).cases.get(position=4)
        self.assertTrue(case.image.endswith(".png"))
        self.assertEqual((case.slices, case.ai_slices), (1, None))
        suffixes = sorted(path.suffix for path in (self.media / DESIGN["key"]).iterdir())
        self.assertEqual(suffixes, [".png", ".stk", ".stk", ".stk"])

    def test_old_six_column_folders_still_load(self):
        rows = [[1, "x.png", "yes", "yes", 0.9, "1 1 4 4"], [2, "x.png", "no", "no", 0.85, ""]]
        self.write(rows=rows, header=STACK_COLUMNS[:6])
        study = load(self.folder)
        self.assertEqual(list(study.cases.values_list("slices", "ai_slices")), [(1, None), (1, None)])

    def test_problems_refuse_the_whole_study(self):
        def rows_with(position, column, value):
            rows = [row[:] for row in ROWS]
            rows[position - 1][column] = value
            return rows

        problems = {
            "a 16-bit slice": lambda: self.write_stack("s2", mode="I;16"),
            "a colour slice": lambda: Image.new("RGB", SLICE_SIZE).save(self.folder / "s2" / "001.png"),
            "a JPEG named .png": lambda: Image.new("L", SLICE_SIZE).save(self.folder / "s2" / "001.png", "JPEG"),
            "slices of two sizes": lambda: Image.new("L", (12, 11)).save(self.folder / "s2" / "002.png"),
            "a folder with 1 slice": lambda: (shutil.rmtree(self.folder / "s2"), self.write_stack("s2", count=1)),
            "a folder with 65 slices": lambda: self.write_stack("s2", count=65, size=(2, 2)),
            "a gap in the slice names": lambda: (self.folder / "s2" / "003.png").rename(self.folder / "s2" / "004.png"),
            "another file in a stack folder": lambda: (self.folder / "s2" / "notes.txt").write_text("x"),
            "slices longer than 1024 px": lambda: (shutil.rmtree(self.folder / "s2"), self.write_stack("s2", size=(1025, 4))),
            "ai_slices past the last slice": lambda: self.write(rows_with(1, 6, "2 4")),
            "ai_slices backwards": lambda: self.write(rows_with(1, 6, "2 1")),
            "ai_slices that are not numbers": lambda: self.write(rows_with(1, 6, "a b")),
            "a stack box without ai_slices": lambda: self.write(rows_with(1, 6, "")),
            "ai_slices without a box": lambda: self.write(rows_with(2, 6, "0 1")),
            "ai_slices on a single image": lambda: self.write(rows_with(4, 6, "0 0")),
            "a box outside the slice": lambda: self.write(rows_with(1, 5, "10 1 4 4")),
            "a planted box wider than the correct ones": lambda: self.write(rows_with(3, 5, "2 2 6 4")),
            "a planted box shorter than the correct ones": lambda: self.write(rows_with(3, 5, "2 2 4 3")),
            "a planted box on more slices than the correct ones": lambda: self.write(rows_with(3, 6, "0 2")),
        }
        for problem, spoil in problems.items():
            with self.subTest(problem):
                self.good_folder()
                spoil()
                with self.assertRaises(StudyFileError):
                    load(self.folder)
                self.assertFalse(Study.objects.exists())
                self.assertFalse(any(self.media.iterdir()))

    def test_check_writes_nothing(self):
        call_command("load_study", self.folder, "--check", stdout=io.StringIO())
        self.assertFalse(Study.objects.exists())
        self.assertFalse(any(self.media.iterdir()))

    def test_slice_counts_that_sort_the_answers_are_refused(self):
        # Rule 1: two 'yes' stacks of 3 slices and two 'no' stacks of 5.
        for name, count in (("s1", 3), ("s4", 3), ("s2", 5), ("s3", 5)):
            shutil.rmtree(self.folder / name, ignore_errors=True)
            self.write_stack(name, count=count)
        self.write(ROWS + [[5, "s4", "yes", "yes", 0.87, "1 1 4 4", "0 1"]])
        with self.assertRaisesRegex(StudyFileError, "slice count"):
            load(self.folder)
        self.assertFalse(Study.objects.exists())
        # One 'yes' stack as long as the 'no' ones: the ranges overlap, so the study loads.
        shutil.rmtree(self.folder / "s4")
        self.write_stack("s4", count=5)
        self.assertEqual(load(self.folder).cases.count(), 5)

    def test_check_reports_a_problem_and_refuses_to_open(self):
        # On a good folder first, so only the --open guard can refuse.
        with self.assertRaises(CommandError):
            call_command("load_study", self.folder, "--check", "--open", stdout=io.StringIO())
        self.write_stack("s2", mode="I;16")
        with self.assertRaises(CommandError):
            call_command("load_study", self.folder, "--check", stdout=io.StringIO())
        self.assertFalse(Study.objects.exists())


class StackReadingTests(StackFolderTestCase):
    """The image address sends the stack file, and rule 1 holds for its AI box."""

    def setUp(self):
        super().setUp()
        self.study = load(self.folder, open_now=True)
        self.reader = User.objects.create_user("reader", password="a long test passphrase")
        self.client.force_login(self.reader)
        self.client.post(reverse("study_detail", args=[self.study.key]), {"consent": "yes"})

    def current(self):
        return self.client.get(reverse("api_current", args=[self.study.key])).json()

    def test_the_stack_file_is_sent_with_its_own_type_and_length_and_logged_once(self):
        response = self.client.get(self.current()["image"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.neshat.stack")
        self.assertEqual(int(response["Content-Length"]), len(response.content))
        self.assertIn("no-store", response["Cache-Control"])
        case = Case.objects.get(study=self.study, position=1)
        self.assertEqual(response.content, (self.media / case.image).read_bytes())
        self.assertEqual(len(split_stack(response.content)), 4)
        access = ImageAccess.objects.get()
        self.assertTrue(access.allowed)
        self.assertEqual(access.sha256, hashlib.sha256(response.content).hexdigest())

    def test_box_slices_arrive_only_with_the_lock(self):
        page = self.client.get(reverse("study_read", args=[self.study.key])).content.decode()
        state = self.current()
        self.assertIsNone(state["ai"])
        for text in (page, json.dumps(state)):
            self.assertNotIn("box_slices", text)

        body = {"submission_id": state["submission_id"], "answer": "no", "confidence": 3}
        response = self.client.post(
            reverse("api_first", args=[state["presentation"]]), json.dumps(body), content_type="application/json"
        )
        ai = response.json()["ai"]
        self.assertEqual((ai["box"], ai["box_slices"]), ([1, 1, 4, 4], [1, 2]))
        self.assertEqual(self.current()["ai"], ai)  # a reload after the lock shows the same


class SyntheticStackStudyTests(TestCase):
    def setUp(self):
        self.data = temporary_folder(self)
        self.override = override_settings(DATA_DIR=self.data, CASE_MEDIA_ROOT=self.data / "media")
        self.override.enable()

    def tearDown(self):
        self.override.disable()

    def test_the_practice_stack_study_loads_and_opens(self):
        call_command("make_synthetic_stack_study", stdout=io.StringIO())
        study = Study.objects.get(key="synthetic-pelvis-mri")
        self.assertEqual(study.state, Study.State.OPEN)
        cases = list(study.cases.order_by("position"))
        self.assertEqual([c.slices for c in cases], [24] * 8)
        self.assertEqual([c.position for c in cases if c.ai_planted], [4, 7])
        for case in cases:
            self.assertEqual(len(split_stack((self.data / "media" / case.image).read_bytes())), 24)
            self.assertEqual(case.ai_box is None, case.ai_slices is None)
            self.assertEqual(case.ai_box is None, case.ai_answer == "no")

        with self.assertRaises(CommandError):
            call_command("make_synthetic_stack_study", stdout=io.StringIO())
        call_command("make_synthetic_stack_study", "--replace", stdout=io.StringIO())
        self.assertEqual(Study.objects.get(key="synthetic-pelvis-mri").cases.count(), 8)

    def test_the_cyst_is_off_the_start_slice_and_inside_the_frame(self):
        box, (first, last) = make_phantom_stack(self.data / "stack", cyst=True, variant=1)
        self.assertEqual(last - first, 2)
        self.assertFalse(first <= (24 - 1) // 2 <= last)  # every case opens on the middle slice
        x, y, w, h = box
        self.assertTrue(0 <= x and 0 <= y and x + w <= 384 and y + h <= 384)
        self.assertIsNone(make_phantom_stack(self.data / "plain", cyst=False, variant=2))
        with Image.open(self.data / "plain" / "023.png") as image:
            self.assertEqual((image.mode, image.size), ("L", (384, 384)))
