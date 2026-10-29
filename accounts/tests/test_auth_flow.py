import re

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail

from .helpers import PASSWORD, make_verified_user

SIGNUP_URL = "/accounts/signup/"
LOGIN_URL = "/accounts/login/"


def signup(client, username="newhiker", email="new@example.com"):
    return client.post(
        SIGNUP_URL,
        {
            "username": username,
            "email": email,
            "password1": PASSWORD,
            "password2": PASSWORD,
            "cf-turnstile-response": "test-token",
        },
    )


def confirmation_link(message):
    match = re.search(r"(/accounts/confirm-email/[^/\s]+/)", message.body)
    assert match, message.body
    return match.group(1)


@pytest.mark.django_db
def test_signup_requires_email_confirmation_before_login(client, turnstile_passes):
    response = signup(client)

    assert response.status_code == 302
    user = get_user_model().objects.get(username="newhiker")
    assert not EmailAddress.objects.get(user=user).verified
    assert len(mail.outbox) == 1
    assert "new@example.com" in mail.outbox[0].to

    # Not verified yet, so logging in sends them to "check your email" instead.
    client.logout()
    response = client.post(LOGIN_URL, {"login": "newhiker", "password": PASSWORD})
    assert "_auth_user_id" not in client.session

    link = confirmation_link(mail.outbox[-1])
    response = client.post(link)

    assert response.status_code == 302
    assert EmailAddress.objects.get(user=user).verified
    assert client.session["_auth_user_id"] == str(user.pk)


@pytest.mark.django_db
def test_signup_rejected_when_turnstile_fails(client, turnstile_fails):
    response = signup(client)

    assert response.status_code == 200
    assert b"couldn&#x27;t confirm you&#x27;re a person" in response.content
    assert not get_user_model().objects.filter(username="newhiker").exists()


@pytest.mark.django_db
def test_signup_rejects_duplicate_email(client, turnstile_passes):
    make_verified_user(email="taken@example.com")

    signup(client, username="someoneelse", email="TAKEN@example.com")

    assert not get_user_model().objects.filter(username="someoneelse").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "username",
    ["has space", "dots.in.name", "a@b", "admin", "deleted-42", "Deleted_user", "ab", "x" * 31],
)
def test_signup_rejects_bad_usernames(client, turnstile_passes, username):
    signup(client, username=username)

    assert not get_user_model().objects.filter(username=username).exists()


@pytest.mark.django_db
def test_signup_rejects_username_that_differs_only_in_case(client, turnstile_passes):
    make_verified_user(username="SmokyHiker")

    signup(client, username="smokyhiker")

    assert get_user_model().objects.filter(username__iexact="smokyhiker").count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("login", ["hiker", "hiker@example.com"])
def test_login_with_username_or_email(client, login):
    user = make_verified_user()

    response = client.post(LOGIN_URL, {"login": login, "password": PASSWORD})

    assert response.status_code == 302
    assert client.session["_auth_user_id"] == str(user.pk)


@pytest.mark.django_db
def test_logout_requires_post(client):
    make_verified_user()
    client.post(LOGIN_URL, {"login": "hiker", "password": PASSWORD})

    client.post("/accounts/logout/")

    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_repeated_failed_logins_are_rate_limited(client):
    make_verified_user()

    for _attempt in range(5):
        client.post(LOGIN_URL, {"login": "hiker", "password": "wrong"})
    # The right password is refused too while the limit is in force.
    response = client.post(LOGIN_URL, {"login": "hiker", "password": PASSWORD})

    assert b"Too many failed login attempts" in response.content
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_password_reset_flow(client):
    make_verified_user()

    client.post("/accounts/password/reset/", {"email": "hiker@example.com"})

    assert len(mail.outbox) == 1
    match = re.search(r"(/accounts/password/reset/key/[^\s]+/)", mail.outbox[0].body)
    assert match, mail.outbox[0].body
    # The first visit swaps the key in the URL for a session token and redirects.
    response = client.get(match.group(1), follow=True)
    form_url = response.redirect_chain[-1][0]
    new_password = "a-brand-new-password"
    client.post(form_url, {"password1": new_password, "password2": new_password})

    user = get_user_model().objects.get(username="hiker")
    assert user.check_password(new_password)


@pytest.mark.django_db
def test_password_reset_for_unknown_email_sends_nothing_revealing(client):
    response = client.post("/accounts/password/reset/", {"email": "nobody@example.com"})

    # Same response as for a real account, so the form can't be used to find users.
    assert response.status_code == 302
    for message in mail.outbox:
        assert "/accounts/password/reset/key/" not in message.body
