from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from parks.models import Park, Section, Trail

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def write_csv(tmp_path, text):
    csv_path = tmp_path / "trails.csv"
    csv_path.write_text(text, encoding="utf-8")
    return str(csv_path)


@pytest.mark.django_db
def test_import_creates_sections_and_trails(tmp_path):
    csv_path = write_csv(
        tmp_path,
        "park,section,name,length_miles\n"
        "gsmnp,Cosby,Snake Den Ridge Trail,5.3\n"
        "gsmnp,Cosby,Low Gap Trail,\n"
        "gsmnp,Greenbrier,Porters Creek Trail,3.7\n",
    )

    call_command("import_trails", csv_path)

    gsmnp = Park.objects.get(slug="gsmnp")
    assert gsmnp.sections.count() == 2
    snake_den = Trail.objects.get(name="Snake Den Ridge Trail")
    assert snake_den.section.name == "Cosby"
    assert str(snake_den.length_miles) == "5.3"
    assert Trail.objects.get(name="Low Gap Trail").length_miles is None


@pytest.mark.django_db
def test_import_twice_updates_instead_of_duplicating(tmp_path):
    first = write_csv(tmp_path, "park,section,name,length_miles\ngsmnp,Cosby,Low Gap Trail,\n")
    call_command("import_trails", first)
    cosby = Section.objects.get(name="Cosby")
    cosby.sort_order = 7
    cosby.save()

    second = write_csv(tmp_path, "park,section,name,length_miles\ngsmnp,Cosby,Low Gap Trail,2.9\n")
    call_command("import_trails", second)

    assert Trail.objects.filter(name="Low Gap Trail").count() == 1
    assert str(Trail.objects.get(name="Low Gap Trail").length_miles) == "2.9"
    # Sort order set in the admin survives a re-import.
    assert Section.objects.get(name="Cosby").sort_order == 7


@pytest.mark.django_db
def test_dry_run_saves_nothing(tmp_path):
    csv_path = write_csv(tmp_path, "park,section,name,length_miles\ngsmnp,Cosby,Low Gap Trail,\n")

    call_command("import_trails", csv_path, "--dry-run")

    assert not Trail.objects.exists()
    assert not Section.objects.exists()


@pytest.mark.django_db
def test_a_bad_row_rolls_back_the_whole_file(tmp_path):
    csv_path = write_csv(
        tmp_path,
        "park,section,name,length_miles\n"
        "gsmnp,Cosby,Low Gap Trail,\n"
        "gsmnp,Cosby,Gabes Mountain Trail,six\n",
    )

    with pytest.raises(CommandError, match="Line 3"):
        call_command("import_trails", csv_path)

    assert not Trail.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("csv_text", "message"),
    [
        ("park,section,name\ngsmnp,Cosby,Low Gap Trail\n", "Missing CSV columns: length_miles"),
        ("park,section,name,length_miles\nnowhere,Cosby,Low Gap Trail,\n", "no park"),
        ("park,section,name,length_miles\ngsmnp,Cosby,,\n", "name is empty"),
        ("park,section,name,length_miles\ngsmnp,Trails,Low Gap Trail,\n", "reserved"),
        (
            "park,section,name,length_miles\n"
            "gsmnp,Cosby,Low Gap Trail,\n"
            "gsmnp,Cosby,Low Gap Trail,\n",
            "more than once",
        ),
    ],
)
def test_import_rejects_bad_files(tmp_path, csv_text, message):
    csv_path = write_csv(tmp_path, csv_text)

    with pytest.raises(CommandError, match=message):
        call_command("import_trails", csv_path)


@pytest.mark.django_db
def test_the_gsmnp_csv_in_the_repo_imports_cleanly():
    call_command("import_trails", str(REPO_ROOT / "data" / "trails" / "gsmnp.csv"))

    gsmnp = Park.objects.get(slug="gsmnp")
    assert gsmnp.trails.count() > 100
    assert not gsmnp.trails.filter(section__isnull=True).exists()
