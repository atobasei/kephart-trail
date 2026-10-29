from django.conf import settings


def site(request):
    """Values every template needs. The site name lives in one setting until it's final."""
    return {
        "SITE_NAME": settings.SITE_NAME,
    }
