from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from parks.models import Board, Trail

from .markdown import render_markdown

THREAD_TITLE_MAX_LENGTH = 150
POST_BODY_MAX_LENGTH = 10_000
EDIT_WINDOW = timedelta(hours=24)


class Thread(models.Model):
    board = models.ForeignKey(Board, on_delete=models.PROTECT, related_name="threads")
    # Set only for a trail's single ongoing thread, which is created automatically.
    trail = models.OneToOneField(
        Trail,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="thread",
    )
    title = models.CharField(max_length=THREAD_TITLE_MAX_LENGTH)
    slug = models.SlugField(max_length=80)
    # Empty for trail threads, which nobody "starts".
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="threads",
    )
    created_at = models.DateTimeField(default=timezone.now)
    # Kept up to date by update_stats() so lists never count posts on the fly.
    last_post_at = models.DateTimeField(default=timezone.now, db_index=True)
    post_count = models.PositiveIntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_pinned", "-last_post_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:80] or "thread"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.trail_id is not None:
            return self.trail.get_absolute_url()

        park = self.board.park
        kwargs = {"thread_id": self.pk, "slug": self.slug}
        if park is None:
            return reverse("forum:general_thread", kwargs=kwargs)
        if park.is_flagship:
            return reverse("forum:gsmnp_thread", kwargs=kwargs)
        kwargs["park_slug"] = park.slug
        return reverse("forum:park_thread", kwargs=kwargs)

    def update_stats(self):
        """Recount visible posts and find the latest. Call after a post is added or removed."""
        visible_posts = self.posts.filter(is_deleted=False)
        self.post_count = visible_posts.count()
        latest = visible_posts.order_by("-created_at").first()
        if latest is not None:
            self.last_post_at = latest.created_at
        else:
            self.last_post_at = self.created_at
        self.save(update_fields=["post_count", "last_post_at"])


class Post(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts",
    )
    # Raw Markdown as typed. body_html is the sanitized version, rendered on save.
    body = models.TextField(validators=[MaxLengthValidator(POST_BODY_MAX_LENGTH)])
    body_html = models.TextField(editable=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        # Posts are never backdated, so id order is posting order and never changes.
        ordering = ["id"]

    def __str__(self):
        return f"Post {self.pk} in {self.thread}"

    def save(self, *args, **kwargs):
        self.body_html = render_markdown(self.body)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("forum:post", kwargs={"post_id": self.pk})

    @property
    def author_name(self):
        if self.author is None:
            return "[deleted user]"
        return self.author.display_name

    @property
    def edit_deadline(self):
        return self.created_at + EDIT_WINDOW
