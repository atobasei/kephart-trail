from django.urls import path

from . import views

app_name = "accounts"

# Login, signup, email and password pages come from allauth under the same /accounts/ prefix.
urlpatterns = [
    path("settings/", views.account_settings, name="settings"),
    path("delete/", views.delete_account_view, name="delete"),
]
