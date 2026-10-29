import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError

from accounts.models import User


@pytest.mark.django_db
def test_home_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Kephart Trail" in response.content


def test_healthz(client):
    response = client.get("/healthz/")
    assert response.status_code == 200
    assert response.content == b"ok"


def test_custom_user_model_is_active():
    assert get_user_model() is User


@pytest.mark.django_db
def test_duplicate_email_is_rejected():
    User.objects.create_user(username="first", email="hiker@example.com", password="x")
    with pytest.raises(IntegrityError):
        User.objects.create_user(username="second", email="hiker@example.com", password="x")


@pytest.mark.django_db
def test_no_missing_migrations():
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)
