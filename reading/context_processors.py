from django.conf import settings


def site(request):
    """Values every template can use."""
    return {"site_name": settings.SITE_NAME, "site_mode": settings.SITE_MODE}
