from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Site user.

    Created before the first migration so we never have to swap user models later.
    Profile and trust fields (bio, avatar, trust_level, ban fields) are added in Phase 2.
    """

    email = models.EmailField("email address", unique=True)

    def __str__(self):
        return self.username
