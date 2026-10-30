"""Server-side limits on posting. Views call posting_error() before saving anything."""

from datetime import timedelta

from django.utils import timezone

from accounts.models import User
from accounts.permissions import can_post, can_post_links, is_moderator

from .markdown import contains_link
from .models import Post

DAILY_POST_LIMITS = {
    User.TrustLevel.NEW: 5,
    User.TrustLevel.MEMBER: 50,
}
# Minimum gap between two posts from the same person, to stop accidental double posts and
# floods. Moderators are exempt from both limits.
MIN_SECONDS_BETWEEN_POSTS = 15


def content_error(user, *texts):
    """Checks that apply to new posts and edits alike. Returns a message or None.

    texts are the strings being submitted (a reply body, or a new thread's title and body).
    """
    if not can_post(user):
        return "Your account can't post right now."

    for text in texts:
        if contains_link(text) and not can_post_links(user):
            return (
                "New accounts can't post links yet. You can post links once your account "
                "is a week old and has a few posts."
            )

    return None


def posting_error(user, *texts):
    """content_error() plus the rate limits for new posts. Returns a message or None.

    Deleted posts still count toward the limits, so deleting doesn't reset them.
    """
    error = content_error(user, *texts)
    if error is not None:
        return error

    if is_moderator(user):
        return None

    now = timezone.now()
    recent_posts = Post.objects.filter(author=user)

    latest = recent_posts.order_by("-created_at").first()
    if latest is not None:
        seconds_since_last = (now - latest.created_at).total_seconds()
        if seconds_since_last < MIN_SECONDS_BETWEEN_POSTS:
            return "You're posting too quickly. Please wait a few seconds and try again."

    daily_limit = DAILY_POST_LIMITS.get(user.trust_level, DAILY_POST_LIMITS[User.TrustLevel.NEW])
    posts_today = recent_posts.filter(created_at__gte=now - timedelta(hours=24)).count()
    if posts_today >= daily_limit:
        return f"You've reached the limit of {daily_limit} posts in 24 hours. Please try later."

    return None


def can_edit_post(user, post):
    """Authors may edit for 24 hours after posting; moderators any time."""
    if post.is_deleted or not can_post(user):
        return False
    if is_moderator(user):
        return True
    if post.author_id != user.pk:
        return False
    return timezone.now() < post.edit_deadline


def can_delete_post(user, post):
    if post.is_deleted or not user.is_authenticated:
        return False
    if is_moderator(user):
        return True
    return post.author_id == user.pk
