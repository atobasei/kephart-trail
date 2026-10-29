import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxLengthValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

BIO_MAX_LENGTH = 500


def avatar_upload_path(user, filename):
    # Random names so avatar URLs can't be guessed or tied back to the original file.
    return f"avatars/{uuid.uuid4().hex}.jpg"


class User(AbstractUser):
    """Site user.

    Email verification status lives in allauth's EmailAddress table, not on this model.
    """

    class TrustLevel(models.IntegerChoices):
        # Integers so levels can be compared: trust_level >= TrustLevel.MEMBER
        NEW = 0, "New"
        MEMBER = 1, "Member"
        MODERATOR = 2, "Moderator"
        ADMIN = 3, "Admin"

    email = models.EmailField("email address", unique=True)
    bio = models.TextField(
        blank=True,
        max_length=BIO_MAX_LENGTH,
        validators=[MaxLengthValidator(BIO_MAX_LENGTH)],
    )
    avatar = models.ImageField("profile picture", upload_to=avatar_upload_path, blank=True)
    trust_level = models.PositiveSmallIntegerField(
        choices=TrustLevel.choices,
        default=TrustLevel.NEW,
    )
    is_banned = models.BooleanField(default=False)
    banned_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Leave empty for a permanent ban.",
    )
    # Set when the user deletes their account; personal data is wiped but the row stays
    # so their posts can show "[deleted user]".
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        if self.is_deleted:
            return "[deleted user]"
        return self.username

    def get_absolute_url(self):
        return reverse("profiles:profile", kwargs={"username": self.username})

    @property
    def is_currently_banned(self):
        """True while a ban is in force. Temporary bans end on their own at banned_until."""
        if not self.is_banned:
            return False
        if self.banned_until is None:
            return True
        return self.banned_until > timezone.now()
