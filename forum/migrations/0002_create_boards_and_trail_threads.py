from django.db import migrations
from django.utils import timezone
from django.utils.text import slugify


def create_boards_and_trail_threads(apps, schema_editor):
    """Create the General board, a board for each park, and a thread for each existing trail.

    New parks and trails get theirs from the signal handlers in forum/signals.py; this
    covers rows that existed before the forum app did.
    """
    Board = apps.get_model("parks", "Board")
    Park = apps.get_model("parks", "Park")
    Trail = apps.get_model("parks", "Trail")
    Thread = apps.get_model("forum", "Thread")

    Board.objects.get_or_create(
        slug="general",
        defaults={
            "name": "General",
            "description": "Anything Smokies-related that isn't about one trail.",
        },
    )

    boards_by_park_id = {}
    for park in Park.objects.all():
        board, created = Board.objects.get_or_create(
            park=park,
            defaults={"name": park.name, "slug": park.slug},
        )
        boards_by_park_id[park.pk] = board

    now = timezone.now()
    for trail in Trail.objects.all():
        if Thread.objects.filter(trail=trail).exists():
            continue
        Thread.objects.create(
            board=boards_by_park_id[trail.park_id],
            trail=trail,
            title=trail.name,
            slug=slugify(trail.name)[:80] or "thread",
            created_at=now,
            last_post_at=now,
        )


def remove_boards_and_trail_threads(apps, schema_editor):
    Thread = apps.get_model("forum", "Thread")
    Board = apps.get_model("parks", "Board")
    Thread.objects.filter(trail__isnull=False).delete()
    Board.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0001_initial"),
        ("parks", "0002_create_gsmnp"),
    ]

    operations = [
        migrations.RunPython(create_boards_and_trail_threads, remove_boards_and_trail_threads),
    ]
