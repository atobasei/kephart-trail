import importlib

import pytest
from django.apps import apps
from django.core.management import call_command

from forum.models import Thread
from parks.models import Board, Park, Section, Trail


@pytest.fixture
def gsmnp():
    return Park.objects.get(slug="gsmnp")


@pytest.mark.django_db
def test_migration_creates_general_and_gsmnp_boards(gsmnp):
    assert Board.objects.filter(slug="general", park__isnull=True).exists()
    assert gsmnp.board.slug == "gsmnp"


@pytest.mark.django_db
def test_new_trail_gets_exactly_one_thread(gsmnp):
    trail = Trail.objects.create(park=gsmnp, name="Alum Cave Trail")
    trail.save()

    assert Thread.objects.filter(trail=trail).count() == 1
    assert trail.thread.title == "Alum Cave Trail"
    assert trail.thread.board == gsmnp.board
    assert trail.thread.get_absolute_url() == "/gsmnp/trails/alum-cave-trail/"


@pytest.mark.django_db
def test_renaming_a_trail_renames_its_thread(gsmnp):
    trail = Trail.objects.create(park=gsmnp, name="Clingmans Dome Trail")

    trail.name = "Kuwohi Trail"
    trail.save()

    trail.thread.refresh_from_db()
    assert trail.thread.title == "Kuwohi Trail"
    assert trail.thread.slug == "kuwohi-trail"


@pytest.mark.django_db
def test_new_park_gets_a_board():
    park = Park.objects.create(name="Frozen Head State Park", kind=Park.Kind.STATE)

    assert park.board.name == "Frozen Head State Park"


@pytest.mark.django_db
def test_import_trails_creates_threads(tmp_path):
    csv_path = tmp_path / "trails.csv"
    csv_path.write_text(
        "park,section,name,length_miles\n"
        "gsmnp,Cosby,Low Gap Trail,\n"
        "gsmnp,Cosby,Gabes Mountain Trail,\n"
    )

    call_command("import_trails", str(csv_path))

    assert Thread.objects.filter(trail__isnull=False).count() == 2


@pytest.mark.django_db
def test_backfill_migration_adds_threads_to_existing_trails(gsmnp):
    trail = Trail.objects.create(park=gsmnp, name="Ramsey Cascades Trail")
    trail.thread.delete()
    migration = importlib.import_module("forum.migrations.0002_create_boards_and_trail_threads")

    migration.create_boards_and_trail_threads(apps, None)
    migration.create_boards_and_trail_threads(apps, None)

    assert Thread.objects.filter(trail=trail).count() == 1


@pytest.mark.django_db
def test_new_is_a_reserved_section_slug(gsmnp):
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        Section(park=gsmnp, name="New", slug="new").full_clean()
