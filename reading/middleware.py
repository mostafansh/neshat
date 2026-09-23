from django.http import Http404

THIS_COMPUTER = {"127.0.0.1", "::1"}


def admin_only_from_this_computer(get_response):
    """Venue mode only: admin pages answer only the laptop itself.

    The workshop Wi-Fi is plain HTTP, so a password typed on a phone would cross the air
    unencrypted. The organizer uses http://127.0.0.1:8080/admin/ on the laptop instead.
    """

    def middleware(request):
        if request.path.startswith("/admin/") and request.META.get("REMOTE_ADDR") not in THIS_COMPUTER:
            raise Http404
        return get_response(request)

    return middleware
