from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ["username", "email", "trust_level", "is_banned", "is_deleted", "date_joined"]
    list_filter = ["trust_level", "is_banned", "is_deleted", "is_staff", "is_active"]
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Profile", {"fields": ["bio", "avatar"]}),
        ("Trust and moderation", {"fields": ["trust_level", "is_banned", "banned_until"]}),
        ("Deletion", {"fields": ["is_deleted"]}),
    )
