from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Our account pages first, then allauth's (login, signup, email, password).
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
    path("u/", include("profiles.urls")),
    path("", include("forum.urls")),
    path("", include("parks.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    # In production, uploaded files are served by R2 (Phase 6) or the web server, not Django.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
