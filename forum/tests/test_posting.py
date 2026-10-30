from datetime import timedelta

import pytest
from django.utils import timezone

from accounts.models import User
from accounts.tests.helpers import make_verified_user
from forum.models import Post, Thread
from parks.models import Board, Park, Trail


@pytest.fixture
def no_wait(monkeypatch):
    """Turn off the "posting too quickly" gap for tests that post several times in a row."""
    monkeypatch.setattr("forum.rules.MIN_SECONDS_BETWEEN_POSTS", 0)


@pytest.fixture
def hiker(client):
    user = make_verified_user()
    client.force_login(user)
    return user


@pytest.fixture
def trail():
    gsmnp = Park.objects.get(slug="gsmnp")
    return Trail.objects.create(park=gsmnp, name="Alum Cave Trail")


def general_board():
    return Board.objects.get(slug="general")


def make_thread(author, title="Road closures this weekend", body="Newfound Gap Road?", board=None):
    if board is None:
        board = general_board()
    thread = Thread.objects.create(board=board, title=title, author=author)
    Post.objects.create(thread=thread, author=author, body=body)
    thread.update_stats()
    return thread


# Starting threads


@pytest.mark.django_db
def test_start_a_general_thread(client, hiker):
    response = client.post(
        "/general/new/", {"title": "Best fall color week?", "body": "Planning a **trip**."}
    )

    thread = Thread.objects.get(title="Best fall color week?")
    assert response["Location"] == f"/general/t/{thread.pk}-best-fall-color-week/"
    assert thread.author == hiker
    assert thread.post_count == 1
    page = client.get(response["Location"])
    assert b"<strong>trip</strong>" in page.content


@pytest.mark.django_db
def test_start_a_gsmnp_thread(client, hiker):
    response = client.post("/gsmnp/new/", {"title": "Permit question", "body": "How far ahead?"})

    thread = Thread.objects.get(title="Permit question")
    assert thread.board.park.slug == "gsmnp"
    assert response["Location"] == f"/gsmnp/t/{thread.pk}-permit-question/"
    park_page = client.get("/gsmnp/")
    assert b"Permit question" in park_page.content


@pytest.mark.django_db
def test_logged_out_users_cannot_start_threads(client):
    response = client.post("/general/new/", {"title": "Hi", "body": "Spam"})

    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]
    assert not Thread.objects.filter(title="Hi").exists()


@pytest.mark.django_db
def test_board_lists_pinned_first_then_latest_activity(client):
    author = make_verified_user()
    older = make_thread(author, title="Older thread")
    newer = make_thread(author, title="Newer thread")
    pinned = make_thread(author, title="Read this first")
    pinned.is_pinned = True
    pinned.last_post_at = timezone.now() - timedelta(days=30)
    pinned.save()
    older.last_post_at = timezone.now() - timedelta(days=2)
    older.save()

    html = client.get("/general/").content.decode()

    assert html.index("Read this first") < html.index(newer.title) < html.index(older.title)


@pytest.mark.django_db
def test_thread_url_with_wrong_slug_redirects(client):
    thread = make_thread(make_verified_user())

    response = client.get(f"/general/t/{thread.pk}-old-title/")

    assert response.status_code == 301
    assert response["Location"] == thread.get_absolute_url()


# Replies, including on trail pages


@pytest.mark.django_db
def test_reply_on_a_trail_page(client, hiker, trail):
    response = client.post(
        "/gsmnp/trails/alum-cave-trail/", {"body": "Ice past Inspiration Point."}
    )

    post = Post.objects.get(body="Ice past Inspiration Point.")
    assert post.thread == trail.thread
    assert response["Location"] == f"/posts/{post.pk}/"
    landing = client.get(response["Location"])
    assert landing["Location"] == f"/gsmnp/trails/alum-cave-trail/#post-{post.pk}"
    trail.thread.refresh_from_db()
    assert trail.thread.post_count == 1


@pytest.mark.django_db
def test_trail_threads_stay_off_the_park_thread_list(client, hiker, trail):
    client.post("/gsmnp/trails/alum-cave-trail/", {"body": "Great hike."})

    park_page = client.get("/gsmnp/").content.decode()
    discussions = park_page[
        park_page.index('id="discussions"') : park_page.index("<h2>Trails</h2>")
    ]
    assert "Alum Cave Trail" not in discussions


@pytest.mark.django_db
def test_logged_out_reply_is_refused(client, trail):
    response = client.post("/gsmnp/trails/alum-cave-trail/", {"body": "drive-by"})

    assert response.status_code == 200
    assert not Post.objects.exists()


@pytest.mark.django_db
def test_locked_thread_refuses_replies(client, hiker):
    thread = make_thread(make_verified_user(username="op", email="op@example.com"))
    thread.is_locked = True
    thread.save()

    client.post(thread.get_absolute_url(), {"body": "one more thing"})

    assert not Post.objects.filter(body="one more thing").exists()


@pytest.mark.django_db
def test_quote_reply_prefills_the_reply_box(client, hiker):
    op = make_verified_user(username="op", email="op@example.com")
    thread = make_thread(op, body="The bridge at mile 2 is out.")
    post = thread.posts.first()

    response = client.get(f"{thread.get_absolute_url()}?quote={post.pk}")

    assert b"&gt; **op wrote:**\n&gt; The bridge at mile 2 is out." in response.content


@pytest.mark.django_db
def test_posts_paginate_30_per_page_oldest_first(client, trail):
    author = make_verified_user()
    for number in range(31):
        Post.objects.create(thread=trail.thread, author=author, body=f"Report number {number}")
    last_post = trail.thread.posts.last()

    page_one = client.get("/gsmnp/trails/alum-cave-trail/").content.decode()
    page_two = client.get("/gsmnp/trails/alum-cave-trail/?page=2").content.decode()

    assert "Report number 0<" in page_one
    assert "Report number 29<" in page_one
    assert "Report number 30<" not in page_one
    assert "Report number 30<" in page_two
    assert "Jump to latest" in page_one
    landing = client.get(f"/posts/{last_post.pk}/")
    assert landing["Location"] == f"/gsmnp/trails/alum-cave-trail/?page=2#post-{last_post.pk}"


# No HTML injection


@pytest.mark.django_db
def test_script_and_javascript_links_never_reach_the_page(client, hiker, no_wait):
    client.post(
        "/general/new/",
        {"title": "<script>alert('title')</script>", "body": "<script>alert('body')</script>"},
    )
    thread = Thread.objects.get()
    client.post(thread.get_absolute_url(), {"body": "[click](javascript:alert('link'))"})

    html = client.get(thread.get_absolute_url()).content.decode()

    assert "<script>alert(" not in html
    assert "javascript:alert" not in html
    assert "&lt;script&gt;alert(&#x27;title&#x27;)" in html


# Limits enforced on the server


@pytest.mark.django_db
def test_post_body_over_10000_characters_is_rejected(client, hiker, trail):
    client.post("/gsmnp/trails/alum-cave-trail/", {"body": "x" * 10_001})

    assert not Post.objects.exists()


@pytest.mark.django_db
def test_new_accounts_are_limited_to_5_posts_a_day(client, hiker, trail):
    for hours_ago in range(1, 6):
        post = Post.objects.create(thread=trail.thread, author=hiker, body="earlier")
        post.created_at = timezone.now() - timedelta(hours=hours_ago)
        post.save()

    response = client.post("/gsmnp/trails/alum-cave-trail/", {"body": "sixth post"})

    assert b"limit of 5 posts in 24 hours" in response.content
    assert not Post.objects.filter(body="sixth post").exists()


@pytest.mark.django_db
def test_old_posts_do_not_count_toward_the_daily_limit(client, hiker, trail):
    for _number in range(5):
        post = Post.objects.create(thread=trail.thread, author=hiker, body="last week")
        post.created_at = timezone.now() - timedelta(days=7)
        post.save()

    client.post("/gsmnp/trails/alum-cave-trail/", {"body": "fresh post"})

    assert Post.objects.filter(body="fresh post").exists()


@pytest.mark.django_db
def test_posting_too_quickly_is_refused(client, hiker, trail):
    client.post("/gsmnp/trails/alum-cave-trail/", {"body": "first"})
    response = client.post("/gsmnp/trails/alum-cave-trail/", {"body": "second"})

    assert b"posting too quickly" in response.content
    assert not Post.objects.filter(body="second").exists()


@pytest.mark.django_db
@pytest.mark.parametrize("body", ["See [this](https://spam.example)", "go to www.spam.example"])
def test_new_accounts_cannot_post_links(client, hiker, trail, body):
    response = client.post("/gsmnp/trails/alum-cave-trail/", {"body": body})

    assert b"can&#x27;t post links yet" in response.content
    assert not Post.objects.exists()


@pytest.mark.django_db
def test_new_accounts_cannot_put_links_in_thread_titles(client, hiker):
    client.post("/general/new/", {"title": "cheap www.pills.example", "body": "hello"})

    assert not Thread.objects.exists()


@pytest.mark.django_db
def test_members_can_post_links(client, trail):
    member = make_verified_user(trust_level=User.TrustLevel.MEMBER)
    client.force_login(member)

    client.post("/gsmnp/trails/alum-cave-trail/", {"body": "[NPS alerts](https://www.nps.gov)"})

    assert Post.objects.filter(author=member).exists()


@pytest.mark.django_db
def test_moderators_skip_the_rate_limits(client, trail):
    moderator = make_verified_user(trust_level=User.TrustLevel.MODERATOR)
    client.force_login(moderator)

    for number in range(7):
        client.post("/gsmnp/trails/alum-cave-trail/", {"body": f"cleanup note {number}"})

    assert Post.objects.filter(author=moderator).count() == 7


@pytest.mark.django_db
def test_banned_users_cannot_post(client, trail):
    banned = make_verified_user(is_banned=True)
    client.force_login(banned)

    client.post("/gsmnp/trails/alum-cave-trail/", {"body": "let me in"})

    assert not Post.objects.exists()


# Editing and deleting


@pytest.mark.django_db
def test_author_can_edit_within_24_hours(client, hiker):
    thread = make_thread(hiker, body="Original text")
    post = thread.posts.get()

    client.post(f"/posts/{post.pk}/edit/", {"body": "Corrected text"})

    post.refresh_from_db()
    assert post.body == "Corrected text"
    assert post.edited_at is not None
    assert b"(edited)" in client.get(thread.get_absolute_url()).content


@pytest.mark.django_db
def test_author_cannot_edit_after_24_hours(client, hiker):
    thread = make_thread(hiker, body="Original text")
    post = thread.posts.get()
    post.created_at = timezone.now() - timedelta(hours=25)
    post.save()

    response = client.post(f"/posts/{post.pk}/edit/", {"body": "Sneaky change"})

    assert response.status_code == 403
    post.refresh_from_db()
    assert post.body == "Original text"


@pytest.mark.django_db
def test_editing_cannot_sneak_in_a_link(client, hiker):
    thread = make_thread(hiker, body="Original text")
    post = thread.posts.get()

    client.post(f"/posts/{post.pk}/edit/", {"body": "now with https://spam.example"})

    post.refresh_from_db()
    assert post.body == "Original text"


@pytest.mark.django_db
def test_others_cannot_edit_or_delete_your_post(client, hiker):
    other = make_verified_user(username="other", email="other@example.com")
    post = make_thread(other).posts.get()

    assert client.post(f"/posts/{post.pk}/edit/", {"body": "vandalized"}).status_code == 403
    assert client.post(f"/posts/{post.pk}/delete/").status_code == 403
    post.refresh_from_db()
    assert not post.is_deleted


@pytest.mark.django_db
def test_moderator_can_edit_old_posts(client):
    author = make_verified_user(username="author", email="author@example.com")
    post = make_thread(author).posts.get()
    post.created_at = timezone.now() - timedelta(days=30)
    post.save()
    client.force_login(make_verified_user(trust_level=User.TrustLevel.MODERATOR))

    client.post(f"/posts/{post.pk}/edit/", {"body": "Removed personal info."})

    post.refresh_from_db()
    assert post.body == "Removed personal info."


@pytest.mark.django_db
def test_author_soft_deletes_a_reply(client, hiker, no_wait):
    thread = make_thread(hiker, body="Opening post")
    client.post(thread.get_absolute_url(), {"body": "Oops, wrong thread"})
    reply = Post.objects.get(body="Oops, wrong thread")
    thread.refresh_from_db()
    assert thread.post_count == 2

    page = client.get(thread.get_absolute_url()).content.decode()
    assert 'data-confirm="Are you sure you want to delete this post?' in page
    assert client.get(f"/posts/{reply.pk}/delete/").status_code == 405
    client.post(f"/posts/{reply.pk}/delete/")

    reply.refresh_from_db()
    thread.refresh_from_db()
    assert reply.is_deleted
    assert thread.post_count == 1
    assert thread.last_post_at == thread.posts.get(body="Opening post").created_at
    html = client.get(thread.get_absolute_url()).content.decode()
    assert "[This post was deleted.]" in html
    assert "Oops, wrong thread" not in html


@pytest.mark.django_db
def test_deleting_does_not_reset_the_daily_limit(client, hiker, trail):
    for hours_ago in range(1, 6):
        post = Post.objects.create(thread=trail.thread, author=hiker, body="x", is_deleted=True)
        post.created_at = timezone.now() - timedelta(hours=hours_ago)
        post.save()

    client.post("/gsmnp/trails/alum-cave-trail/", {"body": "sixth"})

    assert not Post.objects.filter(body="sixth").exists()


@pytest.mark.django_db
def test_home_shows_latest_posts(client, hiker, trail):
    client.post("/gsmnp/trails/alum-cave-trail/", {"body": "Clear and dry today."})

    html = client.get("/").content.decode()

    assert "Clear and dry today." in html
    assert "Alum Cave Trail" in html
