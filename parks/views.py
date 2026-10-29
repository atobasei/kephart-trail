from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from .models import FLAGSHIP_PARK_SLUG, Park, Section, Trail


def _redirect_if_not_canonical(request, obj):
    """Send /parks/gsmnp/... to /gsmnp/... (and vice versa) so each page has one URL."""
    canonical_url = obj.get_absolute_url()
    if request.path != canonical_url:
        return redirect(canonical_url, permanent=True)
    return None


def park_detail(request, park_slug=FLAGSHIP_PARK_SLUG):
    park = get_object_or_404(Park, slug=park_slug)
    redirect_response = _redirect_if_not_canonical(request, park)
    if redirect_response is not None:
        return redirect_response

    sections = []
    unsectioned_trails = []
    if park.uses_sections:
        trails_a_to_z = Prefetch("trails", queryset=Trail.objects.order_by("name"))
        sections = park.sections.prefetch_related(trails_a_to_z)
        unsectioned_trails = park.trails.filter(section__isnull=True).order_by("name")
    else:
        unsectioned_trails = park.trails.order_by("name")

    context = {
        "park": park,
        "sections": sections,
        "unsectioned_trails": unsectioned_trails,
    }
    return render(request, "parks/park_detail.html", context)


def section_detail(request, section_slug, park_slug=FLAGSHIP_PARK_SLUG):
    section = get_object_or_404(
        Section.objects.select_related("park"),
        park__slug=park_slug,
        slug=section_slug,
    )
    redirect_response = _redirect_if_not_canonical(request, section)
    if redirect_response is not None:
        return redirect_response

    context = {
        "park": section.park,
        "section": section,
        "trails": section.trails.order_by("name"),
    }
    return render(request, "parks/section_detail.html", context)


def trail_detail(request, trail_slug, park_slug=FLAGSHIP_PARK_SLUG):
    trail = get_object_or_404(
        Trail.objects.select_related("park", "section"),
        park__slug=park_slug,
        slug=trail_slug,
    )
    redirect_response = _redirect_if_not_canonical(request, trail)
    if redirect_response is not None:
        return redirect_response

    context = {
        "park": trail.park,
        "trail": trail,
    }
    return render(request, "parks/trail_detail.html", context)
