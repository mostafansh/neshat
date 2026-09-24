from django.contrib.auth.forms import UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    """A user name and a password, typed twice. Nothing else is asked for now."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)
