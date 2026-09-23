from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render

from .demo import make_phantom


def home(request):
    return render(request, "reading/home.html")


def demo_image(request):
    """Serve the synthetic test image. It is drawn on first use.

    Case images are never public static files. They come only through views like this one,
    so each request can be checked. Real cases (next milestone) will check that the image
    belongs to this reader's current, previous or next case.
    """
    path = settings.CASE_MEDIA_ROOT / "demo" / "phantom.png"
    if not path.exists():
        make_phantom(path)
    response = FileResponse(path.open("rb"), content_type="image/png")
    response["Cache-Control"] = "private, max-age=300"
    return response
