from io import BytesIO

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from .helpers import PASSWORD, make_verified_user

SETTINGS_URL = "/accounts/settings/"
DELETE_URL = "/accounts/delete/"
GPS_IFD = 0x8825


def photo_with_gps(size=(1200, 800), image_format="JPEG"):
    """A test photo carrying GPS coordinates in its EXIF data, like a phone photo."""
    image = Image.new("RGB", size, (40, 120, 60))
    exif = Image.Exif()
    exif[0x010F] = "TestCam"  # camera make
    exif.get_ifd(GPS_IFD)[2] = (35.0, 39.0, 18.0)  # latitude
    output = BytesIO()
    image.save(output, format=image_format, exif=exif.tobytes())
    return SimpleUploadedFile("trail.jpg", output.getvalue(), content_type="image/jpeg")


@pytest.fixture
def logged_in(client):
    user = make_verified_user()
    client.force_login(user)
    return user


@pytest.mark.django_db
def test_settings_requires_login(client):
    response = client.get(SETTINGS_URL)

    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_update_bio(client, logged_in):
    response = client.post(SETTINGS_URL, {"bio": "Section hiker, LeConte regular."})

    assert response.status_code == 302
    logged_in.refresh_from_db()
    assert logged_in.bio == "Section hiker, LeConte regular."


@pytest.mark.django_db
def test_bio_over_500_characters_is_rejected(client, logged_in):
    response = client.post(SETTINGS_URL, {"bio": "x" * 501})

    assert response.status_code == 200
    logged_in.refresh_from_db()
    assert logged_in.bio == ""


@pytest.mark.django_db
def test_avatar_is_cropped_resized_and_stripped_of_location(client, logged_in):
    client.post(SETTINGS_URL, {"bio": "", "avatar": photo_with_gps()})

    logged_in.refresh_from_db()
    assert logged_in.avatar.name.startswith("avatars/")
    with logged_in.avatar.open("rb") as stored:
        saved = Image.open(stored)
        saved.load()
    assert saved.format == "JPEG"
    assert saved.size == (256, 256)
    exif = saved.getexif()
    assert len(exif) == 0
    assert len(exif.get_ifd(GPS_IFD)) == 0


@pytest.mark.django_db
def test_replacing_avatar_deletes_the_old_file(client, logged_in):
    client.post(SETTINGS_URL, {"bio": "", "avatar": photo_with_gps()})
    logged_in.refresh_from_db()
    old_name = logged_in.avatar.name
    storage = logged_in.avatar.storage

    client.post(SETTINGS_URL, {"bio": "", "avatar": photo_with_gps(size=(300, 900))})

    logged_in.refresh_from_db()
    assert logged_in.avatar.name != old_name
    assert not storage.exists(old_name)
    assert storage.exists(logged_in.avatar.name)


@pytest.mark.django_db
def test_non_image_upload_is_rejected(client, logged_in):
    fake = SimpleUploadedFile("me.jpg", b"#!/bin/sh\necho not an image", content_type="image/jpeg")

    response = client.post(SETTINGS_URL, {"bio": "", "avatar": fake})

    assert response.status_code == 200
    logged_in.refresh_from_db()
    assert not logged_in.avatar


@pytest.mark.django_db
def test_gif_is_rejected_even_though_pillow_can_read_it(client, logged_in):
    output = BytesIO()
    Image.new("RGB", (50, 50)).save(output, format="GIF")
    gif = SimpleUploadedFile("me.jpg", output.getvalue(), content_type="image/jpeg")

    response = client.post(SETTINGS_URL, {"bio": "", "avatar": gif})

    assert b"Upload a JPEG, PNG, or WebP image." in response.content


@pytest.mark.django_db
def test_delete_account_needs_the_right_password(client, logged_in):
    response = client.post(DELETE_URL, {"password": "wrong"})

    assert response.status_code == 200
    logged_in.refresh_from_db()
    assert not logged_in.is_deleted


@pytest.mark.django_db
def test_delete_account_wipes_personal_data_and_blocks_login(client, logged_in):
    client.post(SETTINGS_URL, {"bio": "about me", "avatar": photo_with_gps()})
    logged_in.refresh_from_db()
    avatar_name = logged_in.avatar.name
    storage = logged_in.avatar.storage

    response = client.post(DELETE_URL, {"password": PASSWORD})

    assert response.status_code == 302
    assert "_auth_user_id" not in client.session
    user = get_user_model().objects.get(pk=logged_in.pk)
    assert user.is_deleted
    assert not user.is_active
    assert user.username == f"deleted-{user.pk}"
    assert "hiker@example.com" not in user.email
    assert user.bio == ""
    assert not user.avatar
    assert not storage.exists(avatar_name)
    assert not user.has_usable_password()
    assert not EmailAddress.objects.filter(user=user).exists()
    assert user.display_name == "[deleted user]"

    # The old username and email can't log in any more.
    client.post("/accounts/login/", {"login": "hiker", "password": PASSWORD})
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_email_can_be_reused_after_account_deletion(client, logged_in, turnstile_passes):
    client.post(DELETE_URL, {"password": PASSWORD})

    client.post(
        "/accounts/signup/",
        {
            "username": "hiker2",
            "email": "hiker@example.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
        },
    )

    assert get_user_model().objects.filter(username="hiker2").exists()


@pytest.mark.django_db
def test_other_sessions_end_when_account_is_deleted(client, logged_in):
    from django.test import Client

    other_device = Client()
    other_device.force_login(logged_in)

    client.post(DELETE_URL, {"password": PASSWORD})

    response = other_device.get(SETTINGS_URL)
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]
