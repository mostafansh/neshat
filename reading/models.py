from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Our own user table. It starts identical to Django's, so fields can be added later
    (for example specialty or years in practice) without rebuilding the database."""
