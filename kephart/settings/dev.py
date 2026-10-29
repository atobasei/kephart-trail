"""Local development settings. Safe defaults so a fresh clone runs without a .env file."""

import os
from pathlib import Path

import environ

# Read .env first so its values win over the fallbacks below.
environ.Env.read_env(Path(__file__).resolve().parent.parent.parent / ".env")

# Dev-only fallbacks for anything neither the environment nor .env sets.
os.environ.setdefault("SECRET_KEY", "dev-insecure-secret-key-do-not-use-in-production")
os.environ.setdefault("DATABASE_URL", "postgres://kephart:kephart@localhost:5432/kephart")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")

from .base import *  # noqa: E402, F403

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
