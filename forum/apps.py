from django.apps import AppConfig


class ForumConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "forum"

    def ready(self):
        # Connects the signal handlers that create boards and trail threads.
        from . import signals  # noqa: F401
