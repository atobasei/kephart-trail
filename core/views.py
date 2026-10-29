from django.http import HttpResponse
from django.shortcuts import render

from parks.models import Park


def home(request):
    context = {
        "parks": Park.objects.all(),
    }
    return render(request, "core/home.html", context)


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")
