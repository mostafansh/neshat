from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from reading.studyfiles import StudyFileError, load


class Command(BaseCommand):
    help = "Load a study from a folder with study.json, cases.csv and the case images."

    def add_arguments(self, parser):
        parser.add_argument("folder", type=Path)
        parser.add_argument("--open", action="store_true", help="Open the study for readers now (freezes it).")

    def handle(self, folder, open, **options):
        try:
            study = load(folder, open_now=open)
        except StudyFileError as problem:
            raise CommandError(str(problem))

        self.stdout.write(f"Loaded '{study.key}': {study.title} ({study.state})")
        self.stdout.write("pos  code          truth  AI      conf  planted")
        for case in study.cases.order_by("position"):
            self.stdout.write(
                f"{case.position:>3}  {case.code:<12}  {case.truth:<5}  {case.ai_answer:<6}  "
                f"{case.ai_confidence:.2f}  {'PLANTED' if case.ai_planted else ''}"
            )
        planted = study.cases.filter(ai_planted=True).count()
        self.stdout.write(self.style.SUCCESS(f"{study.cases.count()} cases, {planted} planted."))
