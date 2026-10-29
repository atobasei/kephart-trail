from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

PASSWORD = "correct-horse-battery"


def make_verified_user(username="hiker", email="hiker@example.com", **extra):
    """A user who has already confirmed their email, so they can log in."""
    User = get_user_model()
    user = User.objects.create_user(username=username, email=email, password=PASSWORD, **extra)
    EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    return user
