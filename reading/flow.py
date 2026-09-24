"""The reading flow: which case is current, which images a reader may load, and how a read
is locked. The views stay thin; the rules live here.

CLAUDE.md rule 1: the AI suggestion leaves the server only in the response to the stored
first read (record_first), or later when the page is reloaded after that (current_state).
"""

import hashlib

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import AIExposure, Enrollment, ImageAccess, Presentation, Read, Study

MAX_ELAPSED_MS = 24 * 60 * 60 * 1000
PNG_TYPE = "image/png"  # one image
STACK_TYPE = "application/vnd.neshat.stack"  # one stack file (studyfiles.stack_bytes)


class FlowError(Exception):
    """A refused request. `message` is shown to the reader, so write it plainly."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def enroll(user, study: Study) -> Enrollment:
    """Join a study. The reader's case list is made once, in the study's fixed order."""
    with transaction.atomic():
        enrollment, created = Enrollment.objects.get_or_create(user=user, study=study)
        if created:
            Presentation.objects.bulk_create(
                Presentation(enrollment=enrollment, case=case, position=case.position)
                for case in study.cases.order_by("position")
            )
    return enrollment


def current_presentation(enrollment: Enrollment) -> Presentation | None:
    """The first case in the list that has no final read yet, or None when all are done."""
    return (
        enrollment.presentations.exclude(reads__stage=Read.Stage.FINAL)
        .select_related("case")
        .order_by("position")
        .first()
    )


def image_url(presentation: Presentation) -> str:
    return reverse("case_image", args=[presentation.alias])


def ai_payload(presentation: Presentation) -> dict:
    """What the reader sees of the AI suggestion. The same shape whether it is correct or
    planted: the page cannot tell them apart (rule 6). box_slices is [first, last] for a box
    on a stack, and None for a single image or no box."""
    case, study = presentation.case, presentation.enrollment.study
    return {
        "source": study.ai_source,
        "answer": case.ai_answer,
        "label": study.label_for(case.ai_answer),
        "confidence": round(case.ai_confidence, 2),
        "box": case.ai_box,
        "box_slices": case.ai_slices,
    }


def read_payload(read: Read) -> dict:
    study = read.presentation.enrollment.study
    return {"answer": read.answer, "label": study.label_for(read.answer), "confidence": read.confidence}


def current_state(enrollment: Enrollment) -> dict:
    """The data for GET <api>current (docs/reading-api.md)."""
    presentation = current_presentation(enrollment)
    if presentation is None:
        return {"state": "done"}

    if presentation.shown_at is None:
        presentation.shown_at = timezone.now()
        presentation.save(update_fields=["shown_at"])

    study = enrollment.study
    first = presentation.reads.filter(stage=Read.Stage.FIRST).first()
    following = enrollment.presentations.filter(position=presentation.position + 1).first()
    return {
        "state": "reading",
        "position": presentation.position,
        "total": enrollment.presentations.count(),
        "presentation": presentation.alias,
        "stage": "final" if first else "first",
        "image": image_url(presentation),
        "prefetch": [image_url(following)] if following else [],
        "question": study.question,
        "choices": study.choices,
        "confidence_max": study.confidence_max,
        "submission_id": presentation.final_submission_id if first else presentation.first_submission_id,
        "first_read": read_payload(first) if first else None,
        "ai": ai_payload(presentation) if first else None,
    }


def _clean_answer(study: Study, body: dict) -> tuple[str, int, int | None]:
    answer = body.get("answer")
    if not isinstance(answer, str) or answer not in study.choice_values():
        raise FlowError("Choose one of the answers.")
    confidence = body.get("confidence")
    if not isinstance(confidence, int) or isinstance(confidence, bool) or not 1 <= confidence <= study.confidence_max:
        raise FlowError(f"Choose a confidence from 1 to {study.confidence_max}.")
    elapsed = body.get("elapsed_ms")
    if not isinstance(elapsed, int) or isinstance(elapsed, bool) or not 0 <= elapsed <= MAX_ELAPSED_MS:
        elapsed = None  # the phone's timer is a help, not a rule
    return answer, confidence, elapsed


def _replayed(submission_id: str, presentation: Presentation, stage: str, body: dict) -> bool:
    """True when this exact answer was already stored (a retried send). Raises when the code
    belongs to another case, or when the stored answer differs (for example, a second tab)."""
    earlier = Read.objects.filter(client_submission_id=submission_id).first()
    if earlier is None:
        return False
    if earlier.presentation_id != presentation.pk or earlier.stage != stage:
        raise FlowError("This answer code belongs to another answer. Reload the page.", 409)
    if (earlier.answer, earlier.confidence) != (body.get("answer"), body.get("confidence")):
        raise FlowError("This case was already answered, maybe in another tab. Reload the page.", 409)
    return True


def record_first(presentation: Presentation, body: dict) -> dict:
    """Lock the unaided first read, then reveal the AI suggestion (rule 1)."""
    submission_id = body.get("submission_id")
    with transaction.atomic():
        if not _replayed(submission_id, presentation, Read.Stage.FIRST, body):
            if submission_id != presentation.first_submission_id:
                raise FlowError("This answer code is not valid for this case. Reload the page.", 409)
            current = current_presentation(presentation.enrollment)
            if current is None or current.pk != presentation.pk:
                raise FlowError("This is not your current case. Reload the page.", 409)
            answer, confidence, elapsed = _clean_answer(presentation.enrollment.study, body)
            Read.objects.create(
                presentation=presentation,
                stage=Read.Stage.FIRST,
                answer=answer,
                confidence=confidence,
                client_submission_id=submission_id,
                elapsed_ms=elapsed,
            )
            AIExposure.objects.create(presentation=presentation)
    return {"ai": ai_payload(presentation), "submission_id": presentation.final_submission_id}


def record_final(presentation: Presentation, body: dict) -> dict:
    """Lock the final read. Tells the page whether another case waits."""
    submission_id = body.get("submission_id")
    enrollment = presentation.enrollment
    with transaction.atomic():
        if not _replayed(submission_id, presentation, Read.Stage.FINAL, body):
            if submission_id != presentation.final_submission_id:
                raise FlowError("This answer code is not valid for this case. Reload the page.", 409)
            if not presentation.reads.filter(stage=Read.Stage.FIRST).exists():
                raise FlowError("Lock your first read before the final answer.", 409)
            answer, confidence, elapsed = _clean_answer(enrollment.study, body)
            Read.objects.create(
                presentation=presentation,
                stage=Read.Stage.FINAL,
                answer=answer,
                confidence=confidence,
                client_submission_id=submission_id,
                elapsed_ms=elapsed,
            )
        more = current_presentation(enrollment) is not None
        if not more and enrollment.completed_at is None:
            enrollment.completed_at = timezone.now()
            enrollment.save(update_fields=["completed_at"])
    return {"next": more}


def image_bytes(user, alias: str, remote_addr: str | None) -> tuple[bytes, str] | None:
    """The image file of one presentation and its content type, or None when refused. Every
    request is logged. The file is one PNG, or one stack file for a stack case.

    A reader gets only the images of their current case, the case before and the case after.
    The reading screen never asks for anything else, so any other request is a tripwire.
    """
    presentation = Presentation.objects.select_related("enrollment", "case").filter(alias=alias).first()

    def log(allowed: bool, reason: str = "", sha256: str = ""):
        ImageAccess.objects.create(
            user=user,
            alias=alias[:40],
            presentation=presentation if presentation and presentation.enrollment.user_id == user.pk else None,
            allowed=allowed,
            reason=reason,
            sha256=sha256,
            remote_addr=remote_addr,
        )

    if presentation is None:
        log(False, "unknown alias")
        return None
    if presentation.enrollment.user_id != user.pk:
        log(False, "another reader's case")
        return None
    current = current_presentation(presentation.enrollment)
    if current is None or abs(presentation.position - current.position) > 1:
        log(False, "outside the window")
        return None

    case = presentation.case
    data = (settings.CASE_MEDIA_ROOT / case.image).read_bytes()
    log(True, sha256=hashlib.sha256(data).hexdigest())
    return data, STACK_TYPE if case.slices > 1 else PNG_TYPE
