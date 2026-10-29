import io
import json
import urllib.error
import urllib.parse

from core import turnstile


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def fake_cloudflare(monkeypatch, result=None, error=None):
    """Replace the network call; returns a dict that records what was sent."""
    sent = {}

    def fake_urlopen(url, data, timeout):
        sent["url"] = url
        sent["fields"] = urllib.parse.parse_qs(data.decode())
        if error is not None:
            raise error
        return FakeResponse(json.dumps(result).encode())

    monkeypatch.setattr(turnstile.urllib.request, "urlopen", fake_urlopen)
    return sent


def test_valid_token_passes(monkeypatch, settings):
    settings.TURNSTILE_SECRET_KEY = "server-secret"
    sent = fake_cloudflare(monkeypatch, result={"success": True})

    assert turnstile.verify_token("browser-token", remote_ip="203.0.113.5")
    assert sent["url"] == turnstile.VERIFY_URL
    assert sent["fields"]["secret"] == ["server-secret"]
    assert sent["fields"]["response"] == ["browser-token"]
    assert sent["fields"]["remoteip"] == ["203.0.113.5"]


def test_rejected_token_fails(monkeypatch):
    fake_cloudflare(monkeypatch, result={"success": False, "error-codes": ["invalid-input"]})

    assert not turnstile.verify_token("browser-token")


def test_missing_token_fails_without_calling_cloudflare(monkeypatch):
    sent = fake_cloudflare(monkeypatch, result={"success": True})

    assert not turnstile.verify_token("")
    assert sent == {}


def test_network_error_fails_closed(monkeypatch):
    fake_cloudflare(monkeypatch, error=urllib.error.URLError("offline"))

    assert not turnstile.verify_token("browser-token")
