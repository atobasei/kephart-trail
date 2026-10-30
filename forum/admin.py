from django.contrib import admin

from .models import Post, Thread


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ["title", "board", "author", "post_count", "last_post_at", "is_pinned"]
    list_filter = ["board", "is_pinned", "is_locked", "is_deleted"]
    list_select_related = ["board", "author"]
    search_fields = ["title"]
    raw_id_fields = ["author", "trail"]
    readonly_fields = ["post_count", "last_post_at"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["__str__", "author", "created_at", "edited_at", "is_deleted"]
    list_filter = ["is_deleted"]
    list_select_related = ["thread", "author"]
    search_fields = ["body", "author__username"]
    raw_id_fields = ["thread", "author"]
    readonly_fields = ["body_html"]
