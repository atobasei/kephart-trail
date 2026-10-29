from allauth.account.models import EmailAddress
from django.db import transaction


@transaction.atomic
def delete_account(user):
    """Remove a user's personal data but keep the row, so their posts can show "[deleted user]".

    The account can never log in again: the password is unusable and is_active is False,
    which also ends every other session the user has open on other devices.
    """
    if user.avatar:
        user.avatar.delete(save=False)

    EmailAddress.objects.filter(user=user).delete()

    user.username = f"deleted-{user.pk}"
    # Email must stay unique, so use an address that can never receive mail.
    user.email = f"deleted-{user.pk}@deleted.invalid"
    user.first_name = ""
    user.last_name = ""
    user.bio = ""
    user.avatar = ""
    user.set_unusable_password()
    user.is_active = False
    user.is_staff = False
    user.is_superuser = False
    user.is_deleted = True
    user.save()
