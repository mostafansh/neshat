from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from reading.studyfiles import StudyFileError, load, prepare


class Command(BaseCommand):
    help = "Load a study from a folder with study.json, cases.csv and the case images or stack folders."

    def add_arguments(self, parser):
        parser.add_argument("folder", type=Path)
        parser.add_argument("--open", action="store_true", help="Open the study for readers now (freezes it).")
        parser.add_argument(
            "--check",
            action="store_true",
            help="Run every check and re-save the pixels in memory only. Writes nothing (no database, no files).",
        )

    def handle(self, folder, open, check, **options):
        if check and open:
            raise CommandError("--check writes nothing, so it cannot open the study. Use one or the other.")
        try:
            if check:
                design, prepared, _ = prepare(folder)
            else:
                study = load(folder, open_now=open)
        except StudyFileError as problem:
            raise CommandError(str(problem))

        if check:
            stacks = [case for case, *_ in prepared if case["slices"] > 1]
            slices = sum(case["slices"] for case in stacks)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Check passed for '{design['key']}': {len(prepared)} cases, {len(stacks)} stacks, "
                    f"{slices} slices in the stacks. Nothing was written."
                )
            )
            return

        self.stdout.write(f"Loaded '{study.key}': {study.title} ({study.state})")
        self.stdout.write("pos  code          slices  truth  AI      conf  planted")
        for case in study.cases.order_by("position"):
            self.stdout.write(
                f"{case.position:>3}  {case.code:<12}  {case.slices:>6}  {case.truth:<5}  {case.ai_answer:<6}  "
                f"{case.ai_confidence:.2f}  {'PLANTED' if case.ai_planted else ''}"
            )
        planted = study.cases.filter(ai_planted=True).count()
        self.stdout.write(self.style.SUCCESS(f"{study.cases.count()} cases, {planted} planted."))
