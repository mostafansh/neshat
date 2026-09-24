"""Make and load a practice study of synthetic X-rays, for building and testing the site.

No patient images: every picture is drawn by code (reading/demo.py). The design matches the
workshop's first study: 8 cases, "Fracture?", AI right on 6 and deliberately wrong on 2
(one missed fracture, one false alarm).
"""

import csv
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from reading.demo import make_phantom, normal_area_box
from reading.models import Enrollment, Study
from reading.studyfiles import load

# position: (truth, AI answer, AI confidence). Positions 4 and 7 are the planted errors.
PLAN = {
    1: ("yes", "yes", 0.91),
    2: ("no", "no", 0.88),
    3: ("yes", "yes", 0.86),
    4: ("yes", "no", 0.87),  # planted: the AI misses a fracture
    5: ("no", "no", 0.90),
    6: ("yes", "yes", 0.84),
    7: ("no", "yes", 0.89),  # planted: the AI calls a fracture that is not there
    8: ("no", "no", 0.85),
}

DESIGN = {
    "key": "synthetic-wrist",
    "title": "Practice: fracture on synthetic X-rays",
    "description": "A practice set drawn by code. No patient images.",
    "question": "Fracture?",
    "choices": [
        {"value": "yes", "label": "Fracture"},
        {"value": "no", "label": "No fracture"},
        {"value": "unsure", "label": "Unsure"},
    ],
    "confidence_max": 5,
    "ai_source": "AI model (simulated)",
}


class Command(BaseCommand):
    help = "Draw 8 synthetic X-rays and load them as the practice study 'synthetic-wrist' (opened)."

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
            writer.writerow(["position", "image", "truth", "ai_answer", "ai_confidence", "ai_box"])
            for position, (truth, ai_answer, confidence) in PLAN.items():
                name = f"image-{position}.png"
                fracture_box = make_phantom(folder / name, fracture=truth == "yes", variant=position)
                if ai_answer == "yes":
                    box = fracture_box or normal_area_box(position)
                    ai_box = " ".join(str(v) for v in box)
                else:
                    ai_box = ""
                writer.writerow([position, name, truth, ai_answer, confidence, ai_box])

        study = load(folder, open_now=True)
        self.stdout.write(self.style.SUCCESS(f"Opened '{study.key}' with {study.cases.count()} synthetic cases."))
