from django.urls import path

from . import views

app_name = "forum"

# Included before parks.urls so "gsmnp/new/" isn't read as a section called "new".
urlpatterns = [
    path("general/", views.general_board, name="general"),
    path("general/new/", views.new_general_thread, name="general_new_thread"),
    path(
        "general/t/<int:thread_id>-<slug:slug>/",
        views.thread_detail,
        name="general_thread",
    ),
    path("gsmnp/new/", views.new_park_thread, name="gsmnp_new_thread"),
    path("gsmnp/t/<int:thread_id>-<slug:slug>/", views.thread_detail, name="gsmnp_thread"),
    path("parks/<slug:park_slug>/new/", views.new_park_thread, name="park_new_thread"),
    path(
        "parks/<slug:park_slug>/t/<int:thread_id>-<slug:slug>/",
        views.thread_detail,
        name="park_thread",
    ),
    path("posts/<int:post_id>/", views.post_permalink, name="post"),
    path("posts/<int:post_id>/edit/", views.edit_post, name="edit_post"),
    path("posts/<int:post_id>/delete/", views.delete_post, name="delete_post"),
]
