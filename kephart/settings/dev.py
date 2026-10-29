"""Local development settings. Safe defaults so a fresh clone runs without a .env file."""

import os

# Dev-only fallbacks, applied before base.py reads the environment.
os.environ.setdefault("SECRET_KEY", "dev-insecure-secret-key-do-not-use-in-production")
os.environ.setdefault("DATABASE_URL", "postgres://kephart:kephart@localhost:5432/kephart")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")

from .base import *  # noqa: E402, F403

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
