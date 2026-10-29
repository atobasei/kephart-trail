"""Server-side check of Cloudflare Turnstile tokens.

The browser widget only produces a token; the token means nothing until the server asks
Cloudflare whether it's valid. See https://developers.cloudflare.com/turnstile/
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# The widget puts its token in a form field with this name.
TOKEN_FIELD_NAME = "cf-turnstile-response"


def verify_token(token, remote_ip=None):
    """Return True only if Cloudflare confirms the token. Fails closed on any error."""
    if not token:
        return False

    fields = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        fields["remoteip"] = remote_ip
    body = urllib.parse.urlencode(fields).encode()

    try:
        with urllib.request.urlopen(VERIFY_URL, data=body, timeout=5) as response:
            result = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        logger.warning("Turnstile verification failed: %s", error)
        return False

    return result.get("success") is True
