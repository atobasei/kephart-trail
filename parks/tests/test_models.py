import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from parks.models import Park, Section, Trail
from parks.validators import validate_pdf


@pytest.fixture
def gsmnp():
    # Created by the 0002_create_gsmnp data migration.
    return Park.objects.get(slug="gsmnp")


@pytest.mark.django_db
def test_sections_sort_by_sort_order_then_name(gsmnp):
    Section.objects.create(park=gsmnp, name="Tremont", slug="tremont", sort_order=2)
    Section.objects.create(park=gsmnp, name="Cosby", slug="cosby", sort_order=2)
    Section.objects.create(park=gsmnp, name="Twentymile", slug="twentymile", sort_order=1)

    names = list(gsmnp.sections.values_list("name", flat=True))

    assert names == ["Twentymile", "Cosby", "Tremont"]


@pytest.mark.django_db
def test_sections_default_to_a_to_z(gsmnp):
    for name in ["Sugarlands", "Abrams Creek", "Elkmont"]:
        Section.objects.create(park=gsmnp, name=name, slug=name.lower().replace(" ", "-"))

    names = list(gsmnp.sections.values_list("name", flat=True))

    assert names == ["Abrams Creek", "Elkmont", "Sugarlands"]


@pytest.mark.django_db
def test_trails_sort_a_to_z_within_a_section(gsmnp):
    sugarlands = Section.objects.create(park=gsmnp, name="Sugarlands", slug="sugarlands")
    for name in ["Huskey Gap Trail", "Alum Cave Trail", "Chimney Tops Trail"]:
        Trail.objects.create(park=gsmnp, section=sugarlands, name=name)

    names = list(sugarlands.trails.values_list("name", flat=True))

    assert names == ["Alum Cave Trail", "Chimney Tops Trail", "Huskey Gap Trail"]


@pytest.mark.django_db
def test_slug_is_generated_from_name(gsmnp):
    trail = Trail.objects.create(
        park=gsmnp, name="Appalachian Trail: Newfound Gap to Charlies Bunion"
    )

    assert trail.slug == "appalachian-trail-newfound-gap-to-charlies-bunion"


@pytest.mark.django_db
def test_section_slug_cannot_collide_with_site_urls(gsmnp):
    section = Section(park=gsmnp, name="Trails", slug="trails")

    with pytest.raises(ValidationError):
        section.full_clean()


@pytest.mark.django_db
def test_trail_section_must_belong_to_the_same_park(gsmnp):
    other_park = Park.objects.create(name="Frozen Head State Park", kind=Park.Kind.STATE)
    section = Section.objects.create(park=gsmnp, name="Cosby", slug="cosby")
    trail = Trail(park=other_park, section=section, name="Chimney Top Trail", slug="chimney-top")

    with pytest.raises(ValidationError):
        trail.full_clean()


@pytest.mark.django_db
def test_absolute_urls_for_flagship_and_state_parks(gsmnp):
    section = Section.objects.create(park=gsmnp, name="Deep Creek", slug="deep-creek")
    trail = Trail.objects.create(park=gsmnp, section=section, name="Deep Creek Trail")
    state_park = Park.objects.create(
        name="Fall Creek Falls State Park", kind=Park.Kind.STATE, uses_sections=False
    )
    state_trail = Trail.objects.create(park=state_park, name="Woodland Trail")

    assert gsmnp.get_absolute_url() == "/gsmnp/"
    assert section.get_absolute_url() == "/gsmnp/deep-creek/"
    assert trail.get_absolute_url() == "/gsmnp/trails/deep-creek-trail/"
    assert state_park.get_absolute_url() == "/parks/fall-creek-falls-state-park/"
    assert (
        state_trail.get_absolute_url()
        == "/parks/fall-creek-falls-state-park/trails/woodland-trail/"
    )


def test_pdf_validator_accepts_a_real_pdf():
    pdf = SimpleUploadedFile("map.pdf", b"%PDF-1.7\n...", content_type="application/pdf")

    validate_pdf(pdf)


def test_pdf_validator_rejects_a_renamed_file():
    fake = SimpleUploadedFile("map.pdf", b"MZ\x90\x00 not a pdf", content_type="application/pdf")

    with pytest.raises(ValidationError):
        validate_pdf(fake)


def test_pdf_validator_rejects_oversized_files(monkeypatch):
    monkeypatch.setattr("parks.validators.MAX_MAP_PDF_BYTES", 10)
    pdf = SimpleUploadedFile("map.pdf", b"%PDF-1.7 and then a lot more bytes")

    with pytest.raises(ValidationError):
        validate_pdf(pdf)
