"""Keep boards and trail threads in step with parks and trails.

Every park gets a board for park-wide discussion, and every trail owns exactly one thread.
These run whenever a Park or Trail is saved (admin, import_trails, or code). Existing rows
were backfilled by migration forum/0002.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from parks.models import Board, Park, Trail

from .models import Thread


def ensure_park_board(park):
    board, created = Board.objects.get_or_create(
        park=park,
        defaults={"name": park.name, "slug": park.slug},
    )
    return board


@receiver(post_save, sender=Park)
def create_board_for_park(sender, instance, **kwargs):
    ensure_park_board(instance)


@receiver(post_save, sender=Trail)
def sync_trail_thread(sender, instance, **kwargs):
    board = ensure_park_board(instance.park)
    thread = Thread.objects.filter(trail=instance).first()

    if thread is None:
        Thread.objects.create(board=board, trail=instance, title=instance.name)
        return

    # Keep the thread's title and board matching the trail after a rename or move.
    changed = False
    if thread.title != instance.name:
        thread.title = instance.name
        thread.slug = ""
        changed = True
    if thread.board_id != board.pk:
        thread.board = board
        changed = True
    if changed:
        thread.save()
