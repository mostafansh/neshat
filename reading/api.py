"""The data calls of the reading screen (docs/reading-api.md) and the case-image address."""

import json
from functools import wraps

from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from . import flow
from .models import Enrollment, Presentation, Study


def error(message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


def signed_in(view):
    """Like login_required, but answers the page with JSON instead of a redirect."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error("Please sign in again.", 403)
        return view(request, *args, **kwargs)

    return wrapper


def own_presentation(request, alias: str) -> Presentation | None:
    return (
        Presentation.objects.select_related("enrollment__study", "case")
        .filter(alias=alias, enrollment__user=request.user, enrollment__study__state=Study.State.OPEN)
        .first()
    )


def json_body(request) -> dict:
    try:
        body = json.loads(request.body)
    except (ValueError, RecursionError):  # RecursionError: a body nested thousands deep
        raise flow.FlowError("The answer could not be read. Reload the page.")
    if not isinstance(body, dict):
        raise flow.FlowError("The answer could not be read. Reload the page.")
    return body


@require_GET
@signed_in
def current(request, key):
    enrollment = (
        Enrollment.objects.select_related("study")
        .filter(user=request.user, study__key=key, study__state=Study.State.OPEN)
        .first()
    )
    if enrollment is None:
        return error("You have not joined this study.", 404)
    return JsonResponse(flow.current_state(enrollment))


def _answer(request, alias, record):
    presentation = own_presentation(request, alias)
    if presentation is None:
        return error("This case does not exist.", 404)
    try:
        return JsonResponse(record(presentation, json_body(request)))
    except flow.FlowError as refused:
        return error(refused.message, refused.status)


@require_POST
@signed_in
def first_read(request, alias):
    return _answer(request, alias, flow.record_first)


@require_POST
@signed_in
def final_read(request, alias):
    return _answer(request, alias, flow.record_final)


@require_GET
def case_image(request, alias):
    """Pixels only: no file name, no date, and not kept in the browser's disk cache.
    Content-Length lets the page show "1.2 of 2.9 MB" while a large stack loads."""
    if not request.user.is_authenticated:
        raise Http404
    found = flow.image_bytes(request.user, alias, request.META.get("REMOTE_ADDR"))
    if found is None:
        raise Http404
    data, content_type = found
    headers = {"Cache-Control": "private, no-store", "Content-Length": str(len(data))}
    return HttpResponse(data, content_type=content_type, headers=headers)


def csrf_failure(request, reason=""):
    """An expired form. The reading screen gets JSON; ordinary pages get the plain page."""
    if request.path.startswith("/api/"):
        return error("This page expired. Reload the page.", 403)
    return render(request, "403_csrf.html", status=403)
