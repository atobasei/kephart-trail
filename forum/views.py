from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from parks.models import FLAGSHIP_PARK_SLUG, Board, Park

from .forms import PostForm, ThreadForm
from .helpers import (
    create_post,
    handle_reply,
    page_number_for_post,
    paginate_threads,
    thread_page_context,
    visible_threads,
)
from .models import Post, Thread
from .rules import can_delete_post, can_edit_post, content_error, posting_error

GENERAL_BOARD_SLUG = "general"


def general_board(request):
    board = get_object_or_404(Board, slug=GENERAL_BOARD_SLUG)
    context = {
        "board": board,
        "page_obj": paginate_threads(request, visible_threads(board)),
        "new_thread_url": "forum:general_new_thread",
    }
    return render(request, "forum/board.html", context)


def _new_thread(request, board, cancel_url):
    if request.method == "POST":
        form = ThreadForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            body = form.cleaned_data["body"]
            error = posting_error(request.user, title, body)
            if error is not None:
                form.add_error(None, error)
            else:
                with transaction.atomic():
                    thread = Thread.objects.create(board=board, title=title, author=request.user)
                    create_post(thread, request.user, body)
                return redirect(thread.get_absolute_url())
    else:
        form = ThreadForm()

    context = {"board": board, "form": form, "cancel_url": cancel_url}
    return render(request, "forum/new_thread.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def new_general_thread(request):
    board = get_object_or_404(Board, slug=GENERAL_BOARD_SLUG)
    return _new_thread(request, board, cancel_url=reverse("forum:general"))


@login_required
@require_http_methods(["GET", "POST"])
def new_park_thread(request, park_slug=FLAGSHIP_PARK_SLUG):
    park = get_object_or_404(Park, slug=park_slug)
    board = get_object_or_404(Board, park=park)
    return _new_thread(request, board, cancel_url=park.get_absolute_url())


@require_http_methods(["GET", "POST"])
def thread_detail(request, thread_id, slug, park_slug=None):
    thread = get_object_or_404(
        Thread.objects.select_related("board__park", "trail"),
        pk=thread_id,
        is_deleted=False,
    )
    # Fixes old slugs after a title edit, the wrong board in the URL, and trail threads
    # (which live on their trail page).
    canonical_url = thread.get_absolute_url()
    if request.path != canonical_url:
        return redirect(canonical_url, permanent=True)

    form, response = handle_reply(request, thread)
    if response is not None:
        return response

    context = thread_page_context(request, thread, form)
    context["board"] = thread.board
    return render(request, "forum/thread_detail.html", context)


def post_permalink(request, post_id):
    """/posts/<id>/ sends you to the right page of the thread, scrolled to the post."""
    post = get_object_or_404(Post.objects.select_related("thread"), pk=post_id)
    if post.thread.is_deleted:
        raise Http404
    page_number = page_number_for_post(post)
    url = post.thread.get_absolute_url()
    if page_number > 1:
        url += f"?page={page_number}"
    return redirect(f"{url}#post-{post.pk}")


@login_required
@require_http_methods(["GET", "POST"])
def edit_post(request, post_id):
    post = get_object_or_404(Post.objects.select_related("thread"), pk=post_id)
    if not can_edit_post(request.user, post):
        raise PermissionDenied

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            body = form.cleaned_data["body"]
            error = content_error(request.user, body)
            if error is not None:
                form.add_error(None, error)
            else:
                post.body = body
                post.edited_at = timezone.now()
                post.save()
                return redirect(post.get_absolute_url())
    else:
        form = PostForm(initial={"body": post.body})

    return render(request, "forum/edit_post.html", {"post": post, "form": form})


@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post.objects.select_related("thread"), pk=post_id)
    if not can_delete_post(request.user, post):
        raise PermissionDenied

    with transaction.atomic():
        post.is_deleted = True
        post.save(update_fields=["is_deleted"])
        post.thread.update_stats()
    messages.success(request, "Your post was deleted.")
    return redirect(post.get_absolute_url())
