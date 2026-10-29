import pytest

from accounts.tests.helpers import PASSWORD, make_verified_user


@pytest.mark.django_db
def test_profile_page_shows_username_bio_and_join_date(client):
    make_verified_user(username="SmokyHiker", bio="Hiked all 900 miles.")

    response = client.get("/u/SmokyHiker/")

    assert response.status_code == 200
    assert b"SmokyHiker" in response.content
    assert b"Hiked all 900 miles." in response.content
    assert b"Joined" in response.content


@pytest.mark.django_db
def test_profile_url_is_case_insensitive_and_redirects_to_one_spelling(client):
    make_verified_user(username="SmokyHiker")

    response = client.get("/u/smokyhiker/")

    assert response.status_code == 301
    assert response["Location"] == "/u/SmokyHiker/"


@pytest.mark.django_db
def test_bio_html_is_escaped(client):
    make_verified_user(username="sneaky", bio="<script>alert(1)</script>")

    response = client.get("/u/sneaky/")

    assert b"<script>alert(1)</script>" not in response.content
    assert b"&lt;script&gt;" in response.content


@pytest.mark.django_db
def test_unknown_and_deleted_profiles_are_404(client):
    make_verified_user(username="leaving")
    client.login(username="leaving", password=PASSWORD)
    client.post("/accounts/delete/", {"password": PASSWORD})

    assert client.get("/u/nobody/").status_code == 404
    assert client.get("/u/leaving/").status_code == 404


@pytest.mark.django_db
def test_header_shows_account_links(client):
    response = client.get("/")
    assert b"Log in" in response.content
    assert b"Sign up" in response.content

    user = make_verified_user()
    client.force_login(user)
    response = client.get("/")
    assert b'href="/u/hiker/"' in response.content
    assert b"Log out" in response.content
