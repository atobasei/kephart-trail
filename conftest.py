import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    # allauth keeps rate-limit counters in the cache; without this, tests would trip
    # each other's limits.
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def media_in_tmp(settings, tmp_path):
    # Uploaded files from tests go to a throwaway folder, never the real media/ directory.
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def turnstile_passes(monkeypatch):
    """Pretend Cloudflare accepted the signup form's Turnstile token."""
    monkeypatch.setattr("accounts.forms.verify_token", lambda token: True)


@pytest.fixture
def turnstile_fails(monkeypatch):
    monkeypatch.setattr("accounts.forms.verify_token", lambda token: False)
