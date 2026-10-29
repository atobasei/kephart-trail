from django.conf import settings


def site(request):
    """Values every template needs. The site name lives in one setting until it's final."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        # Public key for the signup Turnstile widget. The secret key never leaves the server.
        "TURNSTILE_SITE_KEY": settings.TURNSTILE_SITE_KEY,
    }
