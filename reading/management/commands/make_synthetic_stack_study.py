"""Make and load a practice study of synthetic MRI-like stacks, for building and testing the
stack viewer.

No patient images: every slice is drawn by code (reading/demo.py). The plan is the same as
the practice X-ray study: 8 cases, "Nabothian cyst?", AI right on 6 and deliberately wrong on
2 (one missed cyst, one false alarm). The false alarm's box sits on a plausible spot, and its
size and slice span lie within those of the correct boxes (rule 6).
"""

import csv
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from reading.demo import cyst_box, make_phantom_stack
from reading.models import Enrollment, Study
from reading.studyfiles import STACK_COLUMNS, load

from .make_synthetic_study import PLAN

DESIGN = {
    "key": "synthetic-pelvis-mri",
    "title": "Practice: cyst on synthetic MRI stacks",
    "description": "A practice set of MRI-like stacks drawn by code. No patient images.",
    "question": "Nabothian cyst?",
    "choices": [
        {"value": "yes", "label": "Cyst"},
        {"value": "no", "label": "No cyst"},
        {"value": "unsure", "label": "Unsure"},
    ],
    "confidence_max": 5,
    "ai_source": "AI model (simulated)",
}


class Command(BaseCommand):
    help = "Draw 8 synthetic MRI-like stacks and load them as the practice study 'synthetic-pelvis-mri' (opened)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete the existing practice study and every answer given to it, then make it again.",
        )

    def handle(self, replace, **options):
        existing = Study.objects.filter(key=DESIGN["key"]).first()
        if existing:
            if not replace:
                raise CommandError(f"'{DESIGN['key']}' exists already. Add --replace to delete it and its answers.")
            Enrollment.objects.filter(study=existing).delete()
            existing.delete()

        folder = settings.DATA_DIR / "synthetic" / DESIGN["key"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "study.json").write_text(json.dumps(DESIGN, indent=2), encoding="utf-8")

        with (folder / "cases.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(STACK_COLUMNS)
            for position, (truth, ai_answer, confidence) in PLAN.items():
                name = f"case-{position}"  # a folder with 000.png … 023.png
                cyst = make_phantom_stack(folder / name, cyst=truth == "yes", variant=position)
                ai_box = ai_slices = ""
                if ai_answer == "yes":
                    box, (first, last) = cyst or cyst_box(position)
                    ai_box = " ".join(str(v) for v in box)
                    ai_slices = f"{first} {last}"
                writer.writerow([position, name, truth, ai_answer, confidence, ai_box, ai_slices])

        study = load(folder, open_now=True)
        self.stdout.write(self.style.SUCCESS(f"Opened '{study.key}' with {study.cases.count()} synthetic stacks."))
