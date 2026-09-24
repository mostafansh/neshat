"""The reading flow: CLAUDE.md rules 1, 2 and 4, the image window and the retry rule."""

import json
import tempfile
from pathlib import Path

from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from reading.models import AIExposure, Case, Enrollment, ImageAccess, Presentation, Read, Study, User

# Values that must never appear in anything the browser receives before the first read is locked.
SENTINEL_SOURCE = "SENTINEL-AI-SOURCE"
SENTINEL_CONFIDENCE = 0.8123
SENTINEL_BOX = [4321, 4322, 4323, 4324]
CHOICES = [
    {"value": "yes", "label": "Fracture"},
    {"value": "no", "label": "No fracture"},
    {"value": "unsure", "label": "Unsure"},
]


def make_study(media_root: Path, cases: int = 4, planted: tuple = (2,)) -> Study:
    study = Study.objects.create(
        key="t-study",
        title="Test study",
        question="Fracture?",
        choices=CHOICES,
        ai_source=SENTINEL_SOURCE,
        design_sha256="test",
        state=Study.State.OPEN,
    )
    (media_root / "t-study").mkdir(parents=True, exist_ok=True)
    for position in range(1, cases + 1):
        Image.new("L", (8, 8), position * 20).save(media_root / "t-study" / f"c{position}.png")
        truth = "yes" if position % 2 else "no"
        ai = truth if position not in planted else ("no" if truth == "yes" else "yes")
        Case.objects.create(
            study=study,
            position=position,
            image=f"t-study/c{position}.png",
            image_sha256="test",
            width=8,
            height=8,
            truth=truth,
            ai_answer=ai,
            ai_confidence=SENTINEL_CONFIDENCE,
            ai_box=SENTINEL_BOX if ai == "yes" else None,
            ai_planted=ai != truth,
        )
    return study


class ReadingTestCase(TestCase):
    def setUp(self):
        self.media = Path(tempfile.mkdtemp())
        self.override = override_settings(CASE_MEDIA_ROOT=self.media)
        self.override.enable()
        self.study = make_study(self.media)
        self.reader = User.objects.create_user("reader", password="a long test passphrase")
        self.client.force_login(self.reader)

    def tearDown(self):
        self.override.disable()

    def join(self):
        return self.client.post(reverse("study_detail", args=[self.study.key]), {"consent": "yes"})

    def current(self, client=None):
        response = (client or self.client).get(reverse("api_current", args=[self.study.key]))
        return response.json()

    def post(self, name, alias, body, client=None):
        return (client or self.client).post(
            reverse(name, args=[alias]), json.dumps(body), content_type="application/json"
        )

    def lock_first(self, answer="yes", confidence=4):
        state = self.current()
        body = {"submission_id": state["submission_id"], "answer": answer, "confidence": confidence, "elapsed_ms": 900}
        return state, self.post("api_first", state["presentation"], body)

    def finish_case(self):
        state, response = self.lock_first()
        body = {"submission_id": response.json()["submission_id"], "answer": "no", "confidence": 3}
        return self.post("api_final", state["presentation"], body)


class JoiningTests(ReadingTestCase):
    def test_joining_needs_consent(self):
        self.client.post(reverse("study_detail", args=[self.study.key]), {})
        self.assertFalse(Enrollment.objects.exists())

    def test_consent_creates_the_case_list_in_the_fixed_order(self):
        response = self.join()
        self.assertRedirects(response, reverse("study_read", args=[self.study.key]))
        positions = list(Presentation.objects.values_list("position", "case__position"))
        self.assertEqual(positions, [(1, 1), (2, 2), (3, 3), (4, 4)])


class NoAIBeforeTheLockTests(ReadingTestCase):
    """Rule 1: nothing the browser gets before the lock reveals the AI or the correct answer."""

    def test_read_page_and_current_case_hold_no_ai_and_no_truth(self):
        self.join()
        page = self.client.get(reverse("study_read", args=[self.study.key])).content.decode()
        state = self.current()
        raw = json.dumps(state)
        for text in (page, raw):
            self.assertNotIn(SENTINEL_SOURCE, text)
            self.assertNotIn("0.81", text)
            self.assertNotIn("4321", text)
            self.assertNotIn("truth", text)
            self.assertNotIn("planted", text)
        self.assertIsNone(state["ai"])
        self.assertEqual(state["stage"], "first")

    def test_the_lock_response_reveals_the_ai(self):
        self.join()
        _, response = self.lock_first()
        self.assertEqual(response.status_code, 200)
        ai = response.json()["ai"]
        self.assertEqual(ai["source"], SENTINEL_SOURCE)
        self.assertEqual(ai["confidence"], 0.81)
        self.assertEqual(AIExposure.objects.count(), 1)


class LockingTests(ReadingTestCase):
    def test_a_retried_lock_is_stored_once_and_answered_the_same(self):
        self.join()
        state, first = self.lock_first()
        body = {"submission_id": state["submission_id"], "answer": "yes", "confidence": 4}
        again = self.post("api_first", state["presentation"], body)
        self.assertEqual(again.json(), first.json())
        self.assertEqual(Read.objects.filter(stage="first").count(), 1)

    def test_reload_after_the_lock_goes_to_the_final_answer(self):
        self.join()
        _, response = self.lock_first(answer="no", confidence=2)
        state = self.current()
        self.assertEqual(state["stage"], "final")
        self.assertEqual(state["first_read"], {"answer": "no", "label": "No fracture", "confidence": 2})
        self.assertEqual(state["ai"], response.json()["ai"])
        self.assertEqual(state["submission_id"], response.json()["submission_id"])

    def test_the_final_answer_moves_to_the_next_case(self):
        self.join()
        response = self.finish_case()
        self.assertEqual(response.json(), {"next": True})
        state = self.current()
        self.assertEqual((state["position"], state["stage"]), (2, "first"))

    def test_a_later_case_cannot_be_answered_first(self):
        self.join()
        later = Presentation.objects.get(position=2)
        body = {"submission_id": later.first_submission_id, "answer": "yes", "confidence": 3}
        self.assertEqual(self.post("api_first", later.alias, body).status_code, 409)

    def test_the_final_answer_needs_a_locked_first_read(self):
        self.join()
        state = self.current()
        presentation = Presentation.objects.get(alias=state["presentation"])
        body = {"submission_id": presentation.final_submission_id, "answer": "yes", "confidence": 3}
        self.assertEqual(self.post("api_final", presentation.alias, body).status_code, 409)

    def test_answers_outside_the_choices_are_refused(self):
        self.join()
        state = self.current()
        for answer, confidence in [("maybe", 3), ("yes", 0), ("yes", 6), ("yes", "3"), ("yes", True)]:
            body = {"submission_id": state["submission_id"], "answer": answer, "confidence": confidence}
            response = self.post("api_first", state["presentation"], body)
            self.assertEqual(response.status_code, 400, (answer, confidence))
        self.assertFalse(Read.objects.exists())

    def test_finishing_every_case_completes_the_study(self):
        self.join()
        for _ in range(3):
            self.assertEqual(self.finish_case().json(), {"next": True})
        self.assertEqual(self.finish_case().json(), {"next": False})
        self.assertEqual(self.current(), {"state": "done"})
        self.assertIsNotNone(Enrollment.objects.get().completed_at)
        self.assertRedirects(
            self.client.get(reverse("study_read", args=[self.study.key])),
            reverse("study_done", args=[self.study.key]),
        )


class NeverEditedTests(ReadingTestCase):
    """Rule 2: a committed read is never edited, not by the model and not by the database."""

    def test_the_model_refuses_to_save_a_read_again(self):
        self.join()
        self.lock_first()
        read = Read.objects.get()
        read.answer = "no"
        with self.assertRaises(ValueError):
            read.save()

    def test_the_database_refuses_any_update(self):
        self.join()
        self.lock_first()
        with self.assertRaises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("UPDATE reading_read SET answer = 'no'")
        self.assertEqual(Read.objects.get().answer, "yes")


class ImageWindowTests(ReadingTestCase):
    """A reader gets images only for the current case, the one before and the one after."""

    def image(self, position, client=None):
        alias = Presentation.objects.get(enrollment__user=self.reader, position=position).alias
        return (client or self.client).get(reverse("case_image", args=[alias]))

    def test_current_and_next_images_load(self):
        self.join()
        self.assertEqual(self.image(1).status_code, 200)
        self.assertEqual(self.image(2).status_code, 200)

    def test_an_image_outside_the_window_is_refused_and_logged(self):
        self.join()
        self.assertEqual(self.image(3).status_code, 404)
        refused = ImageAccess.objects.get(allowed=False)
        self.assertEqual(refused.reason, "outside the window")

    def test_the_window_moves_with_the_reader(self):
        self.join()
        self.finish_case()
        self.assertEqual(self.image(1).status_code, 200)  # the case before
        self.assertEqual(self.image(3).status_code, 200)  # the case after
        self.assertEqual(self.image(4).status_code, 404)

    def test_images_are_pixels_only_not_cached_and_fingerprinted(self):
        self.join()
        response = self.image(1)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertNotIn("Content-Disposition", response.headers)
        self.assertEqual(len(ImageAccess.objects.get(allowed=True).sha256), 64)


class OtherReadersTests(ReadingTestCase):
    def test_another_reader_cannot_load_or_answer_my_case(self):
        self.join()
        state = self.current()
        other = User.objects.create_user("other", password="another long passphrase")
        client = Client()
        client.force_login(other)
        self.assertEqual(client.get(state["image"]).status_code, 404)
        body = {"submission_id": state["submission_id"], "answer": "yes", "confidence": 3}
        self.assertEqual(self.post("api_first", state["presentation"], body, client=client).status_code, 404)
        self.assertEqual(ImageAccess.objects.get(allowed=False).reason, "another reader's case")


class SignedOutTests(ReadingTestCase):
    def test_signed_out_requests_are_refused(self):
        self.join()
        state = self.current()
        self.client.logout()
        self.assertEqual(self.client.get(reverse("api_current", args=[self.study.key])).status_code, 403)
        self.assertEqual(self.client.get(state["image"]).status_code, 404)
        response = self.client.get(reverse("study_read", args=[self.study.key]))
        self.assertTrue(response["Location"].startswith(reverse("signin")))


class CsrfTests(ReadingTestCase):
    def test_answers_need_the_page_token(self):
        self.join()
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.reader)
        state = self.current(client)
        body = {"submission_id": state["submission_id"], "answer": "yes", "confidence": 3}
        refused = self.post("api_first", state["presentation"], body, client=client)
        self.assertEqual(refused.status_code, 403)
        self.assertIn("error", refused.json())

        client.get(reverse("study_read", args=[self.study.key]))  # sets the csrftoken cookie
        token = client.cookies["csrftoken"].value
        accepted = client.post(
            reverse("api_first", args=[state["presentation"]]),
            json.dumps(body),
            content_type="application/json",
            headers={"X-CSRFToken": token},
        )
        self.assertEqual(accepted.status_code, 200)
