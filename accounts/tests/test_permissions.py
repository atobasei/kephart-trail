from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from accounts.models import User
from accounts.permissions import can_post, can_post_links, can_upload_images, is_moderator

from .helpers import make_verified_user


@pytest.mark.django_db
def test_new_users_can_post_but_not_upload_images_or_links():
    user = make_verified_user()

    assert user.trust_level == User.TrustLevel.NEW
    assert can_post(user)
    assert not can_upload_images(user)
    assert not can_post_links(user)
    assert not is_moderator(user)


@pytest.mark.django_db
def test_members_can_upload_images():
    user = make_verified_user(trust_level=User.TrustLevel.MEMBER)

    assert can_upload_images(user)
    assert can_post_links(user)
    assert not is_moderator(user)


@pytest.mark.django_db
@pytest.mark.parametrize("level", [User.TrustLevel.MODERATOR, User.TrustLevel.ADMIN])
def test_moderators_and_admins(level):
    user = make_verified_user(trust_level=level)

    assert is_moderator(user)
    assert can_upload_images(user)


@pytest.mark.django_db
def test_superuser_is_a_moderator_even_at_new_trust_level():
    user = make_verified_user(is_superuser=True)

    assert is_moderator(user)


def test_anonymous_users_can_do_nothing():
    anonymous = AnonymousUser()

    assert not can_post(anonymous)
    assert not can_upload_images(anonymous)
    assert not is_moderator(anonymous)


@pytest.mark.django_db
def test_permanent_ban():
    user = make_verified_user(trust_level=User.TrustLevel.MEMBER, is_banned=True)

    assert user.is_currently_banned
    assert not can_post(user)
    assert not can_upload_images(user)


@pytest.mark.django_db
def test_temporary_ban_ends_on_its_own():
    user = make_verified_user(is_banned=True, banned_until=timezone.now() + timedelta(days=3))
    assert not can_post(user)

    user.banned_until = timezone.now() - timedelta(minutes=1)

    assert not user.is_currently_banned
    assert can_post(user)
