"""The data the site stores. Words follow docs/reading-api.md.

Study      one project, e.g. "Fracture on hand/wrist X-ray"
Case       one image in a study, with the correct answer and the AI suggestion
Enrollment one reader taking part in one study
Presentation  one case shown to one reader, at one position, under a random alias
Read       one locked answer: the first (unaided) read or the final read
AIExposure the moment the AI suggestion was revealed to the reader
ImageAccess   every image request, allowed or refused (the access log)
"""

import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


def random_code(prefix: str) -> str:
    """A random, unguessable code such as 'p8Kq2mZt0bXa'. It says nothing about the case."""
    return prefix + secrets.token_urlsafe(9)[:11]


def new_case_code() -> str:
    return random_code("c")


def new_alias() -> str:
    return random_code("p")


def new_submission_id() -> str:
    return random_code("s")


class User(AbstractUser):
    """Our own user table. It starts identical to Django's, so fields can be added later
    (for example specialty or years in practice) without rebuilding the database."""


class Study(models.Model):
    class State(models.TextChoices):
        DRAFT = "draft"
        OPEN = "open"
        CLOSED = "closed"

    key = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    question = models.CharField(max_length=200)
    # [{"value": "yes", "label": "Fracture"}, ...]. "unsure" is a normal choice value.
    choices = models.JSONField()
    confidence_max = models.PositiveSmallIntegerField(default=5)
    ai_source = models.CharField(max_length=100, default="AI model (simulated)")
    state = models.CharField(max_length=10, choices=State.choices, default=State.DRAFT)
    design_sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "studies"

    def __str__(self):
        return self.title

    def label_for(self, value: str) -> str:
        return next((c["label"] for c in self.choices if c["value"] == value), value)

    def choice_values(self) -> set[str]:
        return {c["value"] for c in self.choices}


class Case(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="cases")
    position = models.PositiveIntegerField()  # fixed order, 1..N
    code = models.CharField(max_length=16, unique=True, default=new_case_code)
    image = models.CharField(max_length=200)  # path inside CASE_MEDIA_ROOT
    image_sha256 = models.CharField(max_length=64)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    truth = models.CharField(max_length=50)
    ai_answer = models.CharField(max_length=50)
    ai_confidence = models.FloatField()
    ai_box = models.JSONField(null=True, blank=True)  # [x, y, w, h] in image pixels, or null
    ai_planted = models.BooleanField()  # True when the AI answer is deliberately wrong

    class Meta:
        ordering = ["study", "position"]
        constraints = [
            models.UniqueConstraint(fields=["study", "position"], name="one_case_per_position"),
        ]

    def __str__(self):
        return f"{self.study.key} #{self.position} ({self.code})"


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="enrollments")
    consented_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "study"], name="one_enrollment_per_study"),
        ]

    def __str__(self):
        return f"{self.user} in {self.study.key}"


class Presentation(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="presentations")
    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    position = models.PositiveIntegerField()
    alias = models.CharField(max_length=16, unique=True, default=new_alias)
    # One-time codes for the two answers. A retried send with the same code is stored once.
    first_submission_id = models.CharField(max_length=16, unique=True, default=new_submission_id)
    final_submission_id = models.CharField(max_length=16, unique=True, default=new_submission_id)
    shown_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["enrollment", "position"]
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "position"], name="one_presentation_per_position"),
        ]

    def __str__(self):
        return f"{self.enrollment} #{self.position}"


class Read(models.Model):
    """A locked answer. Never edited: a database trigger refuses any UPDATE (rule 2)."""

    class Stage(models.TextChoices):
        FIRST = "first"
        FINAL = "final"

    presentation = models.ForeignKey(Presentation, on_delete=models.CASCADE, related_name="reads")
    stage = models.CharField(max_length=5, choices=Stage.choices)
    answer = models.CharField(max_length=50)
    confidence = models.PositiveSmallIntegerField()
    client_submission_id = models.CharField(max_length=16, unique=True)
    elapsed_ms = models.PositiveIntegerField(null=True, blank=True)  # as measured by the phone
    committed_at = models.DateTimeField(auto_now_add=True)  # as measured by the server

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["presentation", "stage"], name="one_read_per_stage"),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("A committed read is never edited.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.presentation} {self.stage}: {self.answer}"


class AIExposure(models.Model):
    presentation = models.OneToOneField(Presentation, on_delete=models.CASCADE, related_name="ai_exposure")
    revealed_at = models.DateTimeField(auto_now_add=True)


class ImageAccess(models.Model):
    """The access log: every image request, allowed or refused."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    alias = models.CharField(max_length=40)
    presentation = models.ForeignKey(Presentation, null=True, on_delete=models.SET_NULL)
    allowed = models.BooleanField()
    reason = models.CharField(max_length=40, blank=True)  # why a request was refused
    sha256 = models.CharField(max_length=64, blank=True)  # fingerprint of the bytes sent
    remote_addr = models.GenericIPAddressField(null=True, blank=True)
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "image accesses"
