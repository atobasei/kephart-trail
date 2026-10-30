"""Thread-page logic shared by forum thread pages and trail pages (parks.views)."""

from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import redirect

from .forms import PostForm
from .models import Post
from .rules import posting_error

THREADS_PER_PAGE = 25
POSTS_PER_PAGE = 30
QUOTE_MAX_CHARACTERS = 1000


def visible_threads(board):
    """A board's thread list: not deleted, and not trail threads (those live on trail pages)."""
    threads = board.threads.filter(is_deleted=False, trail__isnull=True)
    return threads.select_related("author", "board__park")


def paginate_threads(request, threads):
    paginator = Paginator(threads, THREADS_PER_PAGE)
    return paginator.get_page(request.GET.get("page"))


def paginate_posts(request, thread):
    posts = thread.posts.select_related("author")
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    if page_number == "latest":
        page_number = paginator.num_pages
    return paginator.get_page(page_number)


def page_number_for_post(post):
    earlier_posts = post.thread.posts.filter(id__lt=post.id).count()
    return earlier_posts // POSTS_PER_PAGE + 1


def quote_text(post):
    """Markdown that quotes a post, for pre-filling the reply box."""
    body = post.body
    if len(body) > QUOTE_MAX_CHARACTERS:
        body = body[:QUOTE_MAX_CHARACTERS].rstrip() + " …"
    lines = [f"**{post.author_name} wrote:**"]
    for line in body.splitlines():
        lines.append(line)
    quoted = []
    for line in lines:
        quoted.append("> " + line)
    return "\n".join(quoted) + "\n\n"


def create_post(thread, author, body):
    with transaction.atomic():
        post = Post.objects.create(thread=thread, author=author, body=body)
        thread.update_stats()
    return post


def handle_reply(request, thread):
    """Build the reply form for a thread page, and save it on POST.

    Returns (form, response). response is a redirect after a successful reply, else None.
    """
    if request.method == "POST":
        form = PostForm(request.POST)
        if not request.user.is_authenticated:
            form.add_error(None, "Log in to reply.")
        elif thread.is_locked:
            form.add_error(None, "This thread is locked.")
        elif form.is_valid():
            body = form.cleaned_data["body"]
            error = posting_error(request.user, body)
            if error is not None:
                form.add_error(None, error)
            else:
                post = create_post(thread, request.user, body)
                return form, redirect(post.get_absolute_url())
        return form, None

    initial = {}
    quote_id = request.GET.get("quote")
    if quote_id and quote_id.isdigit():
        quoted_post = thread.posts.filter(pk=int(quote_id), is_deleted=False).first()
        if quoted_post is not None:
            initial["body"] = quote_text(quoted_post)
    return PostForm(initial=initial), None


def thread_page_context(request, thread, form):
    page_obj = paginate_posts(request, thread)
    return {
        "thread": thread,
        "page_obj": page_obj,
        "posts": page_obj.object_list,
        "reply_form": form,
    }
