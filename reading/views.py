from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from . import flow
from .demo import make_phantom
from .forms import SignUpForm
from .models import Enrollment, Study


def home(request):
    return render(request, "reading/home.html")


def demo_image(request):
    """Serve the synthetic test image on the home page. It is drawn on first use.

    Only the pixels are sent: no file name, no file date, nothing that could hint at the
    source or the answer.
    """
    path = settings.CASE_MEDIA_ROOT / "demo" / "phantom-v3.png"
    if not path.exists():
        make_phantom(path)
    return HttpResponse(
        path.read_bytes(),
        content_type="image/png",
        headers={"Cache-Control": "private, max-age=300"},
    )


def sign_up(request):
    if request.user.is_authenticated:
        return redirect("projects")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        next_url = request.POST.get("next", "")
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect("projects")
    return render(request, "accounts/signup.html", {"form": form, "next": request.GET.get("next", "")})


def projects(request):
    studies = Study.objects.filter(state=Study.State.OPEN).order_by("opened_at")
    joined = {}
    if request.user.is_authenticated:
        joined = {e.study_id: e for e in Enrollment.objects.filter(user=request.user, study__in=studies)}
    rows = [{"study": s, "enrollment": joined.get(s.pk)} for s in studies]
    return render(request, "reading/projects.html", {"rows": rows})


def _open_study(key: str) -> Study:
    return get_object_or_404(Study, key=key, state=Study.State.OPEN)


def study_detail(request, key):
    """Study information and consent. "I agree" enrols the reader and starts reading."""
    study = _open_study(key)
    enrollment = None
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(user=request.user, study=study).first()
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{reverse('signin')}?next={request.path}")
        if request.POST.get("consent") != "yes":
            return render(request, "reading/study.html", {"study": study, "consent_missing": True})
        flow.enroll(request.user, study)
        return redirect("study_read", key=study.key)
    return render(request, "reading/study.html", {"study": study, "enrollment": enrollment})


@login_required
def read_page(request, key):
    study = _open_study(key)
    enrollment = Enrollment.objects.filter(user=request.user, study=study).first()
    if enrollment is None:
        return redirect("study_detail", key=study.key)
    if enrollment.completed_at:
        return redirect("study_done", key=study.key)
    api_base = reverse("api_current", args=[study.key]).removesuffix("current")
    return render(request, "reading/read.html", {"study": study, "api_base": api_base})


@login_required
def study_done(request, key):
    study = _open_study(key)
    enrollment = get_object_or_404(Enrollment, user=request.user, study=study)
    if enrollment.completed_at is None:
        return redirect("study_read", key=study.key)
    return render(request, "reading/done.html", {"study": study})
