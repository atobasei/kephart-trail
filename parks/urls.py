from django.urls import path

from . import views

app_name = "parks"

# "trails/" must come before "<section_slug>/" so it isn't read as a section.
urlpatterns = [
    # GSMNP, the flagship park, at /gsmnp/
    path("gsmnp/", views.park_detail, name="gsmnp"),
    path("gsmnp/trails/<slug:trail_slug>/", views.trail_detail, name="gsmnp_trail"),
    path("gsmnp/<slug:section_slug>/", views.section_detail, name="gsmnp_section"),
    # Every other park, at /parks/<park_slug>/
    path("parks/<slug:park_slug>/", views.park_detail, name="park_detail"),
    path(
        "parks/<slug:park_slug>/trails/<slug:trail_slug>/",
        views.trail_detail,
        name="trail_detail",
    ),
    path(
        "parks/<slug:park_slug>/<slug:section_slug>/",
        views.section_detail,
        name="section_detail",
    ),
]
