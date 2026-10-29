"""Who may do what. Every view that changes data should check one of these on the server.

Later phases add rate limits (posts per day, votes per day) on top of these checks.
"""

from .models import User


def is_moderator(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.trust_level >= User.TrustLevel.MODERATOR


def can_post(user):
    """Start threads, reply, vote, and write profile posts."""
    if not user.is_authenticated:
        return False
    if not user.is_active:
        return False
    if user.is_currently_banned:
        return False
    return True


def can_upload_images(user):
    """New accounts can't upload images or post links until they're promoted to Member."""
    if not can_post(user):
        return False
    if is_moderator(user):
        return True
    return user.trust_level >= User.TrustLevel.MEMBER


def can_post_links(user):
    return can_upload_images(user)
