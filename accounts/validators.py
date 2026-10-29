from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, RegexValidator


def reject_reserved_prefix(username):
    # Deleted accounts are renamed to "deleted-<id>", so nobody else may take those names.
    if username.lower().startswith("deleted"):
        raise ValidationError("Usernames can't start with “deleted”.")


# Usernames appear in URLs (/u/<username>/), so keep them to letters, numbers, - and _.
username_validators = [
    RegexValidator(
        r"^[A-Za-z0-9_-]+$",
        "Use only letters, numbers, hyphens (-) and underscores (_).",
    ),
    MaxLengthValidator(30),
    reject_reserved_prefix,
]
