from django.http import HttpResponse
from django.shortcuts import render

from forum.helpers import visible_threads
from forum.models import Post
from parks.models import Board, Park

HOME_THREAD_COUNT = 5
HOME_LATEST_POST_COUNT = 10


def home(request):
    general_threads = []
    general_board = Board.objects.filter(slug="general").first()
    if general_board is not None:
        general_threads = visible_threads(general_board)[:HOME_THREAD_COUNT]

    latest_posts = (
        Post.objects.filter(is_deleted=False, thread__is_deleted=False)
        .select_related("author", "thread__trail__park", "thread__board__park")
        .order_by("-id")[:HOME_LATEST_POST_COUNT]
    )

    context = {
        "parks": Park.objects.all(),
        "general_threads": general_threads,
        "latest_posts": latest_posts,
    }
    return render(request, "core/home.html", context)


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")
